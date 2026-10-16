"""Robin-Video narration (opt-in, --voice): voice each scene's `say` lines, fit scene timing to the speech, and make
captions (burned in for muted autoplay, plus an .srt for upload).

  python3 voice.py <output-dir> [--engine kokoro|say|elevenlabs] [--voice af_heart] [--speed 1.0] [--model …] [--no-burn]

Reads storyboard.json scenes' "say" (a string or a list of lines). For each line it synthesizes a clip locally
(Kokoro via HyperFrames, or macOS `say`), so internal scripts never leave the machine; or, only when the user asks for
it, with ElevenLabs (cloud: the narration text is sent to ElevenLabs; `--voice` is the ElevenLabs voice ID and the key
comes from ELEVENLABS_API_KEY in the environment, never from a file or the storyboard). Then it:
  - lengthens any scene whose narration does not fit (keeping "plannedDuration"), and saves storyboard.json
  - mixes composition/assets/audio/voiceover.wav with every line at its exact place on the timeline
  - writes captions.srt (for the LinkedIn caption upload) and, unless --no-burn, compositions/captions.html
    (burned-in captions with the spoken word in Highlight Green, kept clear of scene content)
  - writes voice-timing.json (every line's start and end, global and scene-local) for syncing bespoke motion
  - checks narration against the Cato voice rules and writes voice-report.json
  - re-runs kit.py build so the host picks up the voice, captions and new timing.
Kokoro needs Python packages kokoro-onnx and soundfile: run scripts/setup_voice.sh once (isolated venv).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kit  # noqa: E402
import brand_check  # noqa: E402

RATE = 24000
VOICE_VENV = Path.home() / '.cache/robin-video/voice-venv/bin/python'
# Spoken forms for TTS only (captions keep the written form). Confirm "Cato" and product terms by ear.
SPOKEN = {'SASE': 'sassy', 'SSE': 'S S E', 'CMA': 'C M A', 'SD-WAN': 'S D WAN', 'ZTNA': 'Z T N A', 'PoPs': 'pops', 'PoP': 'pop',
          'vSocket': 'V Socket', 'XDR': 'X D R', 'CASB': 'cas bee', 'DLP': 'D L P', 'RBI': 'R B I', 'FWaaS': 'firewall as a service',
          'SWG': 'S W G', 'IPS': 'I P S', 'DEM': 'D E M', 'TLSi': 'T L S inspection', 'EPP': 'E P P', 'IoT/OT': 'I O T and O T',
          'SaaS': 'sass', 'MPLS': 'M P L S', 'VPN': 'V P N', 'CISO': 'see-so', 'CISOs': 'see-sos', 'GenAI': 'gen A I', 'LLM': 'L L M', 'LLMs': 'L L Ms'}
DEFAULT_VOICE = {'kokoro': 'af_heart', 'say': 'Samantha'}   # elevenlabs: no default, pass the voice ID
ELEVEN_API = 'https://api.elevenlabs.io/v1'
ELEVEN_MODEL = 'eleven_multilingual_v2'
ELEVEN = {'settings': {}, 'model': ELEVEN_MODEL}  # the voice's stored settings, read once in check_voice
CAP_WORDS = 7        # words per burned-in caption cue
LEAD_FIRST, LEAD, GAP, TAIL = 0.3, 0.6, 0.22, 0.5


def spoken(text, extra):
    text = re.sub(r'[\[\]]', '', text).replace('&', ' and ').replace('→', ', then ')
    table = {**SPOKEN, **(extra or {})}
    pattern = re.compile(r'(?<![\w-])(' + '|'.join(re.escape(w) for w in sorted(table, key=len, reverse=True)) + r')(?![\w-])')
    return pattern.sub(lambda m: table[m.group(1)], text)


def run(cmd, env=None):
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(f'{" ".join(cmd[:3])}… failed:\n{r.stdout[-800:]}\n{r.stderr[-800:]}')
    return r


def say_voices():
    """Installed macOS voices as {name: locale} (from `say -v ?`)."""
    out = subprocess.run(['say', '-v', '?'], capture_output=True, text=True).stdout
    return {m.group(1): m.group(2) for m in (re.match(r'^(.+?)\s+([a-z]{2,3}[_-]\w+)\s+#', line) for line in out.splitlines()) if m}


def eleven_key():
    key = os.environ.get('ELEVENLABS_API_KEY', '').strip()
    if not key:
        sys.exit('The elevenlabs engine needs ELEVENLABS_API_KEY in the environment (Robin-Video never stores it).')
    return key


def eleven_request(path, body=None, accept='application/json', retries=4, fatal=True):
    """One ElevenLabs API call (retries rate limits and server errors). Never prints or saves the key."""
    import time
    import urllib.error
    import urllib.request
    data = json.dumps(body).encode('utf-8') if body is not None else None
    headers = {'xi-api-key': eleven_key(), 'Accept': accept}
    if data:
        headers['Content-Type'] = 'application/json'
    for attempt in range(retries):
        try:
            req = urllib.request.Request(ELEVEN_API + path, data=data, headers=headers, method='POST' if data else 'GET')
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode('utf-8', 'replace')[:300]
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 * 2 ** attempt)
                continue
            if not fatal:
                return None
            sys.exit(f'ElevenLabs returned {e.code} for {path.split("?")[0]}: {detail}')
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(2 * 2 ** attempt)
                continue
            sys.exit(f'Could not reach ElevenLabs: {e.reason}')


def check_voice(engine, voice):
    """`say -v <unknown>` silently falls back to the system voice, so check the name first. For ElevenLabs, confirm the
    voice ID and read its stored settings (stability, similarity…) so narration sounds as the voice was tuned."""
    if engine == 'elevenlabs':
        if not voice:
            sys.exit('The elevenlabs engine needs --voice <ElevenLabs voice ID>.')
        raw = eleven_request(f'/voices/{voice}', fatal=False)
        if raw:
            print(f'ElevenLabs voice: {json.loads(raw).get("name", voice)}')
        settings = eleven_request(f'/voices/{voice}/settings', fatal=False)
        ELEVEN['settings'] = json.loads(settings) if settings else {}
        return
    if engine != 'say':
        return
    if not shutil.which('say'):
        sys.exit('The say engine needs macOS.')
    voices = say_voices()
    if voice not in voices:
        english = sorted(n for n, loc in voices.items() if loc.startswith('en'))
        sys.exit(f'macOS voice {voice!r} is not installed. English voices: {", ".join(english) or "none"}. '
                 'Add more in System Settings > Accessibility > Spoken Content > System voice > Manage Voices.')


def synthesize(text, out_wav: Path, engine, voice, speed):
    tmp = out_wav.with_suffix('.raw.aiff' if engine == 'say' else '.raw.wav')
    trim = []
    if engine == 'elevenlabs':
        settings = {k: v for k, v in ELEVEN['settings'].items() if v is not None}
        settings['speed'] = max(0.7, min(1.2, speed))     # the API accepts 0.7–1.2
        pcm = eleven_request(f'/text-to-speech/{voice}?output_format=pcm_{RATE}', accept='audio/pcm',
                             body={'text': text, 'model_id': ELEVEN['model'], 'voice_settings': settings})
        with wave.open(str(tmp), 'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm)
        # Cloud clips carry a little silence at each end; trim it so the timing fit uses the speech itself.
        trim = ['-af', 'silenceremove=start_periods=1:start_threshold=-50dB,areverse,'
                       'silenceremove=start_periods=1:start_threshold=-50dB,areverse']
    elif engine == 'kokoro':
        env = os.environ.copy()
        if 'HYPERFRAMES_PYTHON' not in env and VOICE_VENV.exists():
            env['HYPERFRAMES_PYTHON'] = str(VOICE_VENV)
        run([str(HERE / 'hf'), 'tts', text, '--voice', voice, '--speed', str(speed), '-o', str(tmp)], env=env)
    else:
        if not shutil.which('say'):
            sys.exit('The say engine needs macOS.')
        run(['say', '-v', voice, '-r', str(int(180 * speed)), '-o', str(tmp), text])
    run(['ffmpeg', '-y', '-v', 'error', '-i', str(tmp), *trim, '-ac', '1', '-ar', str(RATE), '-sample_fmt', 's16', str(out_wav)])
    tmp.unlink(missing_ok=True)
    with wave.open(str(out_wav)) as w:
        return w.getnframes() / w.getframerate()


def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def cues_for(text, start, end):
    words = re.sub(r'[\[\]]', '', text).split()
    n = max(1, -(-len(words) // CAP_WORDS))
    size = -(-len(words) // n)
    chunks = [' '.join(words[i:i + size]) for i in range(0, len(words), size)]
    total = sum(len(c.split()) for c in chunks)
    out, t = [], start
    for c in chunks:
        d = (end - start) * len(c.split()) / total
        out.append({'start': round(t, 3), 'end': round(t + d, 3), 'text': c})
        t += d
    return out


def captions_html(cues, w, h, total):
    return f'''<template id="captions-template">
  <div id="root" data-composition-id="captions" data-width="{w}" data-height="{h}" data-duration="{total}">
    <!-- Burned-in captions generated by voice.py. LinkedIn and most feeds autoplay muted: these carry the narration. -->
    <link rel="stylesheet" href="assets/cato/cato.css" />
    <style>
      @font-face {{ font-family: Inter; src: url("assets/cato/fonts/Inter-Bold.woff") format("woff"); font-weight: 700; }}
      #root {{ position: absolute; inset: 0; pointer-events: none; }}
    </style>
    <div id="captions-layer" class="clip captions" data-start="0" data-duration="{total}" data-track-index="0"></div>
    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/cato/cato-motion.js"></script>
    <script>
      (function () {{
        const root = document.querySelector('[data-composition-id="captions"]');
        const tl = gsap.timeline({{ paused: true }});
        CatoMotion.captions(tl, root.querySelector(".captions"), {json.dumps(cues)});
        window.__timelines["captions"] = tl;
      }})();
    </script>
  </div>
</template>
'''


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('output_dir', type=Path)
    ap.add_argument('--engine', choices=('kokoro', 'say', 'elevenlabs'))
    ap.add_argument('--voice', help='Kokoro voice, macOS voice name, or ElevenLabs voice ID')
    ap.add_argument('--model', help=f'ElevenLabs model (default {ELEVEN_MODEL})')
    ap.add_argument('--speed', type=float)
    ap.add_argument('--no-burn', action='store_true', help='SRT only; no burned-in captions')
    a = ap.parse_args(argv)
    out = a.output_dir.resolve()
    sbp = out / 'storyboard.json'
    sb = kit.validate(json.loads(sbp.read_text(encoding='utf-8')))
    v = sb.setdefault('voice', {})
    engine = a.engine or v.get('engine', 'kokoro')
    # A voice saved by the other engine (af_heart for Kokoro, Samantha for say) does not carry over.
    voice = a.voice or (v.get('voice') if v.get('engine', 'kokoro') == engine else None) or DEFAULT_VOICE.get(engine)
    if engine == 'elevenlabs':
        ELEVEN['model'] = a.model or v.get('model') or ELEVEN_MODEL
    check_voice(engine, voice)
    speed = a.speed or float(v.get('speed', 1.0))
    v.update({'enabled': True, 'engine': engine, 'voice': voice, 'speed': speed})
    if engine == 'elevenlabs':
        v['model'] = ELEVEN['model']
    else:
        v.pop('model', None)
    comp = out / 'composition'
    lines_dir = comp / 'assets/audio/lines'
    lines_dir.mkdir(parents=True, exist_ok=True)
    clips = {}
    for k, s in enumerate(sb['scenes']):
        says = s.get('say') or []
        says = [says] if isinstance(says, str) else says
        if not says:
            continue
        durs = []
        for i, line in enumerate(says):
            path = lines_dir / f'{s["id"]}-{i + 1:02d}.wav'
            durs.append(synthesize(spoken(line, sb.get('pronunciations')), path, engine, voice, speed))
            clips[(s['id'], i)] = (path, line, durs[-1])
        need = (LEAD_FIRST if k == 0 else LEAD) + sum(durs) + GAP * (len(durs) - 1) + TAIL
        if need > float(s['duration']) + 0.01:
            s.setdefault('plannedDuration', s['duration'])
            s['duration'] = round(need, 2)
    if not clips:
        sys.exit('No scene has "say" lines. Add narration to storyboard.json first.')
    sbp.write_text(json.dumps(sb, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    rows, total = kit.layout(sb)
    bed = bytearray(int(total * RATE) * 2)
    cues, placed = [], []
    for k, r in enumerate(rows):
        s = r['scene']
        t = r['start'] + (LEAD_FIRST if k == 0 else LEAD)
        i = 0
        while (s['id'], i) in clips:
            path, line, d = clips[(s['id'], i)]
            with wave.open(str(path)) as w:
                data = w.readframes(w.getnframes())
            at = int(t * RATE) * 2
            bed[at:at + len(data)] = data[:max(0, len(bed) - at)]
            cues += cues_for(line, t, t + d)
            placed.append({'scene': s['id'], 'line': i + 1, 'text': line, 'start': round(t, 3), 'end': round(t + d, 3),
                           'localStart': round(t - r['start'], 3), 'localEnd': round(t + d - r['start'], 3)})
            t += d + GAP
            i += 1
    with wave.open(str(comp / 'assets/audio/voiceover.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(bytes(bed))
    # Per-line timing (global and scene-local seconds): sync bespoke motion to the spoken words with it.
    (out / 'voice-timing.json').write_text(json.dumps({'duration': total, 'lines': placed}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    (out / 'captions.srt').write_text(''.join(f'{n}\n{srt_time(c["start"])} --> {srt_time(c["end"])}\n{c["text"]}\n\n' for n, c in enumerate(cues, 1)), encoding='utf-8')
    fw, fh = kit.FORMATS[sb.get('format', 'portrait')]
    cap_file = comp / 'compositions/captions.html'
    if a.no_burn:
        sb['captions'] = False
        cap_file.unlink(missing_ok=True)
    else:
        sb['captions'] = True
        cap_file.write_text(captions_html(cues, fw, fh, total), encoding='utf-8')
    sbp.write_text(json.dumps(sb, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    findings = []
    add = lambda rule, sev, where, msg, fix='': findings.append({'rule': rule, 'severity': sev, 'where': where, 'message': msg, 'fix': fix})
    for (sid, i), (_, line, _) in clips.items():
        brand_check.copy_rules(f'narration {sid}:{i + 1}', line, add, on_screen=False)
    speech = sum(d for _, _, d in clips.values())
    wpm = round(sum(len(l.split()) for _, l, _ in clips.values()) / max(1, speech) * 60)
    if wpm > 175:
        findings.append({'rule': 'V-PACE', 'severity': 'warn', 'where': 'narration', 'message': f'{wpm} words per minute is rushed.', 'fix': 'Cut words or lower --speed.'})
    report = {'engine': engine, 'voice': voice, 'speed': speed, 'duration': total, 'wpm': wpm, 'lines': len(clips), 'cues': len(cues),
              'stretched': [s['id'] for s in sb['scenes'] if 'plannedDuration' in s and s['plannedDuration'] != s['duration']], 'findings': findings}
    (out / 'voice-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    subprocess.run([sys.executable, str(HERE / 'kit.py'), 'build', str(out)], check=True)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
