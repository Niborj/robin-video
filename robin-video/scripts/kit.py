"""Robin-Video kit: build a Cato-branded HyperFrames project from storyboard.json.

Python standard library only. Commands (run with python3 from anywhere):

  kit.py init  <output-dir> [--format portrait|square|vertical|landscape] [--title "..."] [--music <key>|none|<file>]
      Writes a starter <output-dir>/storyboard.json (hook + end card) unless one exists, then runs build.

  kit.py build <output-dir> [--force-scenes id,id|all] [--refresh-kit]
      Reads <output-dir>/storyboard.json and writes <output-dir>/composition/:
        assets/cato/      fonts, verified official logos, icons, cato.css, cato-motion.js
        assets/vendor/    local GSAP
        assets/music/     the chosen bed (+ cue file); assets/sfx/ for any SFX the storyboard names
        compositions/     one sub-composition per scene, generated from its archetype (never overwritten unless forced)
        index.html        the host: scene slots with computed starts and overlaps, music, SFX, voiceover, captions
      Re-run it whenever storyboard.json timing, order, music or SFX change. Scene files you edited are kept.

  kit.py media <output-dir> <file> [...]   Copy source pages/images into composition/assets/source/ (prints paths).
  kit.py icon <name> [...]                 Inline SVG for Cato outline icons.   kit.py icons   Lists icon names.
  kit.py music                             The 15 bundled music beds (10 original) with mood, tempo and best use.

storyboard.json (the contract between the plan and the composition):
  {
    "title": "...", "format": "portrait", "music": "vol-12", "musicVolume": 0.3,
    "transition": "iris", "overlap": 0.85, "progress": false,
    "scenes": [
      {"id": "hook", "archetype": "hook", "duration": 3.6, "eyebrow": "...", "headline": "AI moves fast. [Security sees first.]"},
      {"id": "proof", "archetype": "stat", "duration": 4.5, "value": "71%", "label": "...", "source": "...",
       "sfx": [{"file": "interface/drop_001.ogg", "at": 0.3, "volume": 0.6}]},
      {"id": "end", "archetype": "end", "duration": 3.4, "line": "...", "cta": "...", "url": "catonetworks.com"}
    ]
  }
  Scene starts are the running sum of durations; every scene except the last also stays up for `overlap` seconds
  so the next scene's transition (ring iris by default) opens over it. Archetypes and their fields: references/scene-archetypes.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scenes as S  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
ASSETS = SKILL / 'assets'
FORMATS = {'portrait': (1080, 1350), 'square': (1080, 1080), 'vertical': (1080, 1920), 'landscape': (1920, 1080)}
PAD_X = {'portrait': 84, 'square': 80, 'vertical': 96, 'landscape': 120}
TRANSITIONS = ('iris', 'fade', 'push', 'wipe', 'cut')
# Music beds: key -> (file, mood and best use, source). "original" tracks were composed for Robin-Video by
# compose_music.py (owned, royalty-free); "brag" tracks come from the /brag skill (confirm license before external use).
MUSIC = {
    'pulse': ('robin-pulse.mp3', 'Tech pulse, 118 BPM: driving, plucked arpeggios, minor key. Product launches, announcements.', 'original'),
    'ambient': ('robin-ambient.mp3', 'Ambient glow, 72 BPM: no drums, evolving pads and bells. Thought leadership, executive POV.', 'original'),
    'cinematic': ('robin-cinematic.mp3', 'Cinematic rise, 92 BPM: strings, ostinato, big low hits. Reveals, research findings, launch hooks.', 'original'),
    'lofi': ('robin-lofi.mp3', 'Lo-fi focus, 84 BPM: swung beat, electric piano, vinyl. Explainers, how-tos, employer brand.', 'original'),
    'piano': ('robin-piano.mp3', 'Hopeful piano, 96 BPM: piano arpeggios over soft strings. Customer stories, people stories.', 'original'),
    'minimal': ('robin-minimal.mp3', 'Minimal data, 124 BPM: ticks, rimshots, rolling bass. Threat research, data stories.', 'original'),
    'uplift': ('robin-uplift.mp3', 'Bright corporate, 112 BPM: strummed guitar, claps, bells. Events, partner news, wins.', 'original'),
    'deep': ('robin-deep.mp3', 'Deep house, 120 BPM: warm filtered chords, rolling bass. Events, culture, energetic teasers.', 'original'),
    'focus': ('robin-focus.mp3', 'Calm suspense, 100 BPM: ticking clock, low drone, sparse piano. Threat research, problem statements.', 'original'),
    'mallets': ('robin-mallets.mp3', 'Playful mallets, 108 BPM: marimba, shaker, light drums. Explainers, employer brand, light news.', 'original'),
    'vol-12': ('happy-beats-business-moves-vol-12-by-ende-dot-app.mp3', 'Steady and clean, 110 BPM. Thought leadership, threat research, analyst news.', 'brag'),
    'vol-11': ('happy-beats-business-moves-vol-11-by-ende-dot-app.mp3', 'Warm and business-like, 115 BPM. Customer stories, executive POV.', 'brag'),
    'vol-1': ('happy-beats-business-moves-vol-1-by-ende-dot-app.mp3', 'Most energetic, 120 BPM. Product launches and announcements.', 'brag'),
    'vol-9': ('happy-beats-business-moves-vol-9-by-ende-dot-app.mp3', 'Mid-energy, laid-back, 115 BPM. Explainers and how-tos.', 'brag'),
    'vol-10': ('happy-beats-business-moves-vol-10-by-ende-dot-app.mp3', 'Compact, punchy loop, 110 BPM. Event promos and short teasers.', 'brag'),
}
AUDIO_EXT = ('.mp3', '.wav', '.m4a', '.ogg')


def is_custom_music(value):
    return isinstance(value, str) and value.lower().endswith(AUDIO_EXT)


def place_music(out: Path, comp: Path, music):
    """Copy the bed (bundled key or custom file path) and its cue files into the composition; return its file name."""
    if not music or music == 'none':
        return None
    if music in MUSIC:
        src = ASSETS / 'music' / MUSIC[music][0]
    else:
        src = next((c for c in (Path(music), out / music, out / 'source' / music) if c.is_file()), None)
        if src is None:
            die(f'music file not found: {music}')
    (comp / 'assets/music/cues').mkdir(parents=True, exist_ok=True)
    if not (comp / 'assets/music' / src.name).exists():
        shutil.copy2(src, comp / 'assets/music' / src.name)
    for ext in ('json', 'md'):
        for cue in (src.parent / 'cues' / f'{src.stem}.music-cues.{ext}', ASSETS / 'music/cues' / f'{src.stem}.music-cues.{ext}'):
            if cue.exists():
                shutil.copy2(cue, comp / 'assets/music/cues' / cue.name)
                break
    return src.name


def die(msg):
    sys.exit(f'kit.py: {msg}')


def brand():
    return json.loads((ASSETS / 'brand/cato-brand.json').read_text(encoding='utf-8'))


def copy_kit(comp: Path, refresh=False):
    cato = comp / 'assets/cato'
    if (cato / 'cato-motion.js').exists() and not refresh:
        return
    (cato / 'fonts').mkdir(parents=True, exist_ok=True)
    for f in (ASSETS / 'brand/fonts').iterdir():
        shutil.copy2(f, cato / 'fonts' / f.name)
    (cato / 'logos').mkdir(parents=True, exist_ok=True)
    for key, info in brand()['logos']['files'].items():
        src = ASSETS / 'brand' / info['path']
        if hashlib.sha256(src.read_bytes()).hexdigest() != info['sha256']:
            die(f'{src.name} does not match the official Cato logo hash. Restore the original file.')
        shutil.copy2(src, cato / 'logos' / src.name)
    shutil.copytree(ASSETS / 'brand/icons', cato / 'icons', dirs_exist_ok=True)
    for f in ('icons.json', 'cato-brand.json'):
        shutil.copy2(ASSETS / 'brand' / f, cato / f)
    for f in ('cato.css', 'cato-motion.js'):
        shutil.copy2(ASSETS / 'kit' / f, cato / f)
    (comp / 'assets/vendor').mkdir(parents=True, exist_ok=True)
    shutil.copy2(ASSETS / 'vendor/gsap.min.js', comp / 'assets/vendor/gsap.min.js')
    (comp / 'hyperframes.json').write_text(json.dumps({
        '$schema': 'https://hyperframes.heygen.com/schema/hyperframes.json',
        'registry': 'https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry',
        'paths': {'blocks': 'compositions', 'components': 'compositions/components', 'assets': 'assets'},
        'media': {'autoProxy': True}}, indent=2) + '\n', encoding='utf-8')


def place_media(out: Path, comp: Path, ref: str, sid: str):
    """Resolve a storyboard image path (relative to the output dir, the source/ folder, or the composition) and copy it
    into composition/assets/source/. Returns the composition-relative path the scene HTML uses."""
    if ref.startswith('assets/') and (comp / ref).is_file():
        return ref
    for cand in (Path(ref), out / ref, out / 'source' / ref, comp / ref):
        if cand.is_file():
            dest = comp / 'assets/source' / cand.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if cand.resolve() != dest.resolve():
                shutil.copy2(cand, dest)
            return f'assets/source/{cand.name}'
    die(f'scene {sid}: media file not found: {ref}')


def page_record(out: Path, name: str):
    """What ingest.py measured for a rendered page (contentBox, blank bands), if this image is one."""
    cj = out / 'source/content.json'
    if not cj.is_file():
        return {}
    for page in json.loads(cj.read_text(encoding='utf-8')).get('pages', []):
        if Path(page.get('image', '')).name == name:
            return page
    return {}


def validate(sb):
    if sb.get('format', 'portrait') not in FORMATS:
        die(f'format must be one of {", ".join(FORMATS)}')
    scenes = sb.get('scenes')
    if not isinstance(scenes, list) or not scenes:
        die('storyboard.json needs a non-empty "scenes" list')
    ids = set()
    for k, s in enumerate(scenes):
        sid = s.get('id')
        if not sid or not re.fullmatch(r'[a-z][a-z0-9-]{0,30}', sid):
            die(f'scene {k + 1}: id must be lowercase letters, digits and hyphens, starting with a letter (got {sid!r})')
        if sid in ids or sid in ('main', 'root', 'captions'):
            die(f'scene id {sid!r} is duplicated or reserved')
        ids.add(sid)
        if s.get('archetype') not in S.ARCHETYPES:
            die(f'scene {sid}: archetype must be one of {", ".join(S.ARCHETYPES)}')
        try:
            if float(s.get('duration', 0)) <= 0:
                raise ValueError
        except (TypeError, ValueError):
            die(f'scene {sid}: duration must be a positive number of seconds')
        if s.get('transition') and s['transition'] not in TRANSITIONS:
            die(f'scene {sid}: transition must be one of {", ".join(TRANSITIONS)}')
    if sb.get('music') not in (None, 'none', *MUSIC) and not is_custom_music(sb.get('music')):
        die(f'music must be one of {", ".join(MUSIC)}, none, or a path to an audio file ({", ".join(AUDIO_EXT)})')
    return sb


def layout(sb):
    """Scene starts, slot lengths (duration + overlap tail) and the total running time."""
    overlap = float(sb.get('overlap', 0.85))
    default_tr = sb.get('transition', 'iris')
    t, rows = 0.0, []
    scenes = sb['scenes']
    for k, s in enumerate(scenes):
        tr = 'cut' if k == 0 else (s.get('transition') or default_tr)
        nxt = scenes[k + 1] if k + 1 < len(scenes) else None
        next_tr = (nxt.get('transition') or default_tr) if nxt else None
        tail = overlap if nxt and next_tr != 'cut' else 0.0
        d = float(s['duration'])
        rows.append({'scene': s, 'start': round(t, 3), 'duration': d, 'slot': round(d + tail, 3), 'tail': round(tail, 3), 'transition': tr})
        t += d
    return rows, round(t, 3)


def media_duration(path: Path, fallback=1.5):
    """Length of an audio file in seconds (ffprobe), so SFX slots match their sound exactly."""
    import subprocess
    try:
        out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        return round(float(out), 3)
    except (OSError, ValueError, subprocess.SubprocessError):
        return fallback


def host_html(sb, rows, total, comp: Path, music_file=None):
    fmt = sb.get('format', 'portrait')
    w, h = FORMATS[fmt]
    slots = []
    for k, r in enumerate(rows):
        sid = r['scene']['id']
        slots.append(f'''      <div id="slot-{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html"
        data-start="{r['start']}" data-duration="{r['slot']}" data-track-index="{1 + k % 2}" data-width="{w}" data-height="{h}"></div>''')
    audio = []
    voice = comp / 'assets/audio/voiceover.wav'
    has_voice = voice.exists() and sb.get('voice', {}).get('enabled', True) is not False
    if music_file:
        name = music_file
        vol = float(sb.get('musicVolume', 0.3))
        if has_voice:
            vol = min(vol, 0.14)  # duck the bed under narration
        fade_out = max(0.5, min(2.0, total * 0.08))
        # The volume lane sets the absolute level (it replaces data-volume while it runs), so it carries the bed level.
        lane = {'version': 1, 'lanes': [{'target': 'volume', 'points': [
            {'t': 0, 'v': 0}, {'t': 0.6, 'v': vol}, {'t': round(total - fade_out, 3), 'v': vol}, {'t': total, 'v': 0}]}]}
        audio.append(f'''      <audio id="music-bed" data-start="0" data-duration="{total}" data-track-index="10" data-volume="{vol}"
        data-automation='{json.dumps(lane, separators=(",", ":"))}' src="assets/music/{name}"></audio>''')
    if has_voice:
        audio.append(f'      <audio id="voiceover" data-start="0" data-duration="{total}" data-track-index="9" data-volume="1" src="assets/audio/voiceover.wav"></audio>')
    n = 0
    for r in rows:
        for fx in r['scene'].get('sfx', []) or []:
            n += 1
            at = round(r['start'] + float(fx.get('at', 0)), 3)
            vol = float(fx.get('volume', 0.6))
            length = min(float(fx['duration']) if fx.get('duration') else media_duration(comp / 'assets/sfx' / fx['file']), round(total - at, 3))
            audio.append(f'      <audio id="sfx-{n}" data-start="{at}" data-duration="{length}" data-track-index="{10 + n}" '
                         f'data-volume="{vol}" src="assets/sfx/{fx["file"]}"></audio>')
    captions = ''
    if (comp / 'compositions/captions.html').exists() and sb.get('captions', True):
        captions = f'''      <div id="slot-captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-track-kind="captions"
        data-start="0" data-duration="{total}" data-track-index="8" data-width="{w}" data-height="{h}"></div>'''
    progress = ''
    if sb.get('progress'):
        progress = f'      <div id="progress-bar" class="clip progress" data-start="0" data-duration="{total}" data-track-index="7"></div>'
    progress_js = (f'\n      tl.fromTo("#progress-bar", {{ scaleX: 0 }}, {{ scaleX: 1, duration: {total}, ease: "none" }}, 0);' if progress else '')
    title = S.esc(sb.get('title') or 'Cato social video')
    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <title>{title}</title>
    <!-- Generated by Robin-Video kit.py build from storyboard.json. Edit the storyboard (timing, order, music, SFX)
         and re-run build; edit scene look and motion in compositions/<scene>.html. -->
    <link rel="stylesheet" href="assets/cato/cato.css" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: Archivo; src: url("assets/cato/fonts/Archivo-Latin.woff2") format("woff2"); font-weight: 100 900; }}
      @font-face {{ font-family: Inter; src: url("assets/cato/fonts/Inter-Regular.woff") format("woff"); font-weight: 400; }}
      @font-face {{ font-family: Inter; src: url("assets/cato/fonts/Inter-Bold.woff") format("woff"); font-weight: 700; }}
      html, body {{ width: {w}px; height: {h}px; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; }}
      #root > div[data-composition-src] {{ position: absolute; inset: 0; }}
    </style>
  </head>
  <body>
    <div id="root" class="cs-root fmt-{fmt}{' has-captions' if captions else ''}" data-composition-id="main" data-start="0" data-width="{w}" data-height="{h}" data-duration="{total}">
{chr(10).join(slots)}
{captions}
{progress}
{chr(10).join(audio)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});{progress_js}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''


def cmd_build(a):
    out = Path(a.output_dir).resolve()
    sbp = out / 'storyboard.json'
    if not sbp.is_file():
        die(f'{sbp} not found. Write the storyboard (Step 2) or run kit.py init.')
    sb = validate(json.loads(sbp.read_text(encoding='utf-8')))
    comp = out / 'composition'
    (comp / 'compositions').mkdir(parents=True, exist_ok=True)
    copy_kit(comp, a.refresh_kit)
    fmt = sb.get('format', 'portrait')
    w, h = FORMATS[fmt]
    rows, total = layout(sb)
    force = set((a.force_scenes or '').split(',')) - {''}
    written, kept = [], []
    for k, r in enumerate(rows):
        s = dict(r['scene'])
        bg = s.get('bg') or S.DEFAULT_BG[s['archetype']]
        ctx = {'id': s['id'], 'index': k, 'fmt': fmt, 'w': w, 'h': h, 'pad_x': PAD_X[fmt], 'bg': bg, 'slot': r['slot'],
               'tail': r['tail'], 'transition': r['transition']}
        for field in ('image', 'photo'):
            if s.get(field):
                s[field] = place_media(out, comp, s[field], s['id'])
                if field == 'image':
                    ctx['img_size'] = S.image_size(comp / s[field])
                    page = page_record(out, Path(s[field]).name)
                    ctx['crop'] = s.get('crop') if s.get('crop') is not None else page.get('contentBox')
                    ctx['gaps'] = page.get('gaps') or []
        path = comp / 'compositions' / f'{s["id"]}.html'
        if path.exists() and not ('all' in force or s['id'] in force):
            text = path.read_text(encoding='utf-8')
            # Keep the author's scene but sync its timing attributes with the storyboard.
            text = re.sub(r'(<div id="root" data-composition-id="[^"]+" data-width="\d+" data-height="\d+" data-duration=")[\d.]+(")', rf'\g<1>{r["slot"]}\2', text, count=1)
            text = re.sub(r'(class="clip cs-scene" data-start="0" data-duration=")[\d.]+(")', rf'\g<1>{r["slot"]}\2', text, count=1)
            text = re.sub(r'data-transition="[a-z]+"', f'data-transition="{r["transition"]}"', text, count=1)
            text = re.sub(r' data-tail="[\d.]+"', '', text, count=1)
            if r['tail']:
                text = text.replace(f'data-transition="{r["transition"]}"', f'data-transition="{r["transition"]}" data-tail="{r["tail"]}"', 1)
            path.write_text(text, encoding='utf-8')
            kept.append(s['id'])
        else:
            path.write_text(S.render_scene(s, ctx), encoding='utf-8')
            written.append(s['id'])
    music_file = place_music(out, comp, sb.get('music', 'vol-12'))
    for r in rows:
        for fx in r['scene'].get('sfx', []) or []:
            src = ASSETS / 'sfx' / fx['file']
            if not src.is_file():
                die(f'scene {r["scene"]["id"]}: unknown SFX {fx["file"]} (see assets/sfx/sfx-analysis.md)')
            dest = comp / 'assets/sfx' / fx['file']
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    (comp / 'index.html').write_text(host_html(sb, rows, total, comp, music_file), encoding='utf-8')
    (comp / 'meta.json').write_text(json.dumps({'id': out.name, 'name': sb.get('title') or out.name, 'createdBy': 'robin-video'}, indent=2) + '\n', encoding='utf-8')
    timing = {'format': fmt, 'width': w, 'height': h, 'duration': total,
              'scenes': [{'id': r['scene']['id'], 'archetype': r['scene']['archetype'], 'start': r['start'], 'end': round(r['start'] + r['duration'], 3),
                          'slot': r['slot'], 'transition': r['transition']} for r in rows]}
    (out / 'timing.json').write_text(json.dumps(timing, indent=2) + '\n', encoding='utf-8')
    print(f'Built {comp} — {fmt} {w}x{h}, {total}s, {len(rows)} scenes (new: {", ".join(written) or "none"}; kept: {", ".join(kept) or "none"})')
    for r in rows:
        print(f'  {r["start"]:6.2f}s  {r["scene"]["id"]:<14} {r["scene"]["archetype"]:<10} {r["duration"]:>5.2f}s  in: {r["transition"]}')
    if not 15 <= total <= 60:
        print(f'  note: {total}s is outside the 15–60 s range that suits most LinkedIn feed videos.')


def cmd_init(a):
    out = Path(a.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    sbp = out / 'storyboard.json'
    if not sbp.exists():
        sb = {'title': a.title or 'Cato social video', 'format': a.format, 'music': a.music, 'transition': 'iris', 'overlap': 0.85,
              'scenes': [
                  {'id': 'hook', 'archetype': 'hook', 'duration': 4, 'eyebrow': '', 'headline': ''},
                  {'id': 'end', 'archetype': 'end', 'duration': 3.5, 'line': '', 'cta': '', 'url': 'catonetworks.com'}]}
        sbp.write_text(json.dumps(sb, indent=2) + '\n', encoding='utf-8')
    a.force_scenes, a.refresh_kit = None, False
    cmd_build(a)


def cmd_media(a):
    out = Path(a.output_dir).resolve()
    dest = out / 'composition/assets/source'
    dest.mkdir(parents=True, exist_ok=True)
    for f in a.files:
        src = Path(f)
        if not src.is_absolute():
            src = (out / f) if (out / f).exists() else (out / 'source' / f)
        if not src.is_file():
            die(f'not found: {f}')
        shutil.copy2(src, dest / src.name)
        print(f'assets/source/{src.name}')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('init'); p.add_argument('output_dir'); p.add_argument('--format', choices=FORMATS, default='portrait')
    p.add_argument('--title'); p.add_argument('--music', default='vol-12', help=f'one of {", ".join(MUSIC)}, none, or an audio file path')
    p = sub.add_parser('build'); p.add_argument('output_dir'); p.add_argument('--force-scenes', help='comma-separated scene ids to regenerate, or all')
    p.add_argument('--refresh-kit', action='store_true', help='recopy cato.css, cato-motion.js, fonts and logos from the skill')
    p = sub.add_parser('media'); p.add_argument('output_dir'); p.add_argument('files', nargs='+')
    p = sub.add_parser('icon'); p.add_argument('names', nargs='+'); p.add_argument('--cls', default='icon')
    sub.add_parser('icons'); sub.add_parser('music')
    a = ap.parse_args(argv)
    if a.cmd == 'init':
        cmd_init(a)
    elif a.cmd == 'build':
        cmd_build(a)
    elif a.cmd == 'media':
        cmd_media(a)
    elif a.cmd == 'icon':
        for n in a.names:
            if n not in S.ICONS:
                die(f'unknown icon {n}; run kit.py icons')
            print(S.icon(n, a.cls))
    elif a.cmd == 'icons':
        print(' '.join(sorted(S.ICONS)))
    elif a.cmd == 'music':
        print('Original tracks (composed for Robin-Video; owned and royalty-free):')
        for k, (f, mood, src) in MUSIC.items():
            if src == 'original':
                print(f'  {k:10} {mood}')
        print('From /brag ("Happy Beats / Business Moves", ende.app; confirm the license before external use):')
        for k, (f, mood, src) in MUSIC.items():
            if src != 'original':
                print(f'  {k:10} {mood}')
        print('Custom: set "music" to an audio file path (e.g. a compose_music.py --seed variation); its cues/ file is copied too.')


if __name__ == '__main__':
    main()
