"""Robin-Video delivery: render, pick and bake the poster, make a social-ready MP4, and package the post.

  python3 deliver.py <output-dir> [--render] [--quality draft|standard|high] [--poster <seconds>] [--name <file-stem>] [--force]

Steps
  1. Brand gate: brand_check.py on the composition (and post.md when present). Stops on errors unless --force.
  2. Render (with --render, or when no video exists yet): HyperFrames via scripts/hf into <output-dir>/<name>.mp4.
  3. Verify: duration matches timing.json, dimensions match the format, audio present when music/voice was planned.
  4. Poster: the frame at --poster seconds (default: the hook's settled moment) → <name>.jpg. It is frame 0 of the
     delivered file (so every feed and chat app shows a meaningful thumbnail) and dissolves into the live video over
     the first 0.3 s, so autoplay never flashes the poster and cuts to an unbuilt frame.
  5. Social encode: H.264 High, yuv420p, 30 fps, AAC 48 kHz, loudness-normalized (-16 LUFS with narration, -20
     music only), +faststart (LinkedIn, Instagram, YouTube, X ready). The raw render stays in composition/renders/.
  6. Captions: copies captions.srt (voice mode) next to the video for upload as a closed-caption file.
  7. Writes delivery.json with everything the human needs to post it.
Requires ffmpeg and ffprobe.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORMATS = {'portrait': (1080, 1350), 'square': (1080, 1080), 'vertical': (1080, 1920), 'landscape': (1920, 1080)}
QUALITY = {'draft': 'draft', 'standard': 'standard', 'high': 'delivery'}


def run(cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def probe(path: Path):
    out = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate',
               '-of', 'json', str(path)]).stdout
    return json.loads(out)


def loudnorm(src: Path, target: float):
    """Two-pass loudness normalization: measure the render, then apply one linear gain to reach `target` LUFS.
    Single-pass loudnorm (dynamic mode) lands 1-2 LU off the target on 20-40 s clips."""
    flt = f'loudnorm=I={target}:TP=-1.5:LRA=11'
    r = run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(src), '-vn', '-af', f'{flt}:print_format=json', '-f', 'null', '-'], check=False)
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr)
    if r.returncode != 0 or not m:
        return flt
    j = json.loads(m.group(0))
    if j['input_i'] in ('-inf', 'inf'):   # silent track: nothing to normalize
        return flt
    return (f"{flt}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}"
            f":measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('output_dir', type=Path)
    ap.add_argument('--render', action='store_true', help='render even if the video already exists')
    ap.add_argument('--quality', choices=QUALITY, default='high')
    ap.add_argument('--poster', type=float, help='poster time in seconds (a settled, readable frame)')
    ap.add_argument('--name', default='video')
    ap.add_argument('--force', action='store_true', help='continue even if the brand gate fails')
    a = ap.parse_args(argv)
    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            sys.exit(f'{tool} is required (brew install ffmpeg).')
    out = a.output_dir.resolve()
    comp = out / 'composition'
    sb = json.loads((out / 'storyboard.json').read_text(encoding='utf-8'))
    timing = json.loads((out / 'timing.json').read_text(encoding='utf-8'))
    fmt = sb.get('format', 'portrait')
    w, h = FORMATS[fmt]
    report = {'video': None, 'poster': None, 'captions': None, 'post': None, 'gates': {}, 'issues': [], 'format': fmt, 'size': f'{w}x{h}'}

    # 1. brand gate
    cmd = [sys.executable, str(HERE / 'brand_check.py'), str(comp)]
    if (out / 'post.md').is_file():
        cmd += ['--copy', str(out / 'post.md')]
    gate = run(cmd, check=False)
    report['gates']['brand'] = {'result': 'pass' if gate.returncode == 0 else 'fail', 'report': str(out / 'brand-report.md')}
    print(gate.stdout.strip().splitlines()[-1] if gate.stdout.strip() else 'brand check: no output', flush=True)
    if gate.returncode != 0 and not a.force:
        sys.exit('Brand gate failed. Fix the findings in brand-report.md (or pass --force to deliver anyway, and say so to the user).')

    # 2. render
    raw = comp / 'renders' / f'{a.name}.render.mp4'   # the untouched render, kept so re-delivery never re-encodes twice
    raw.parent.mkdir(parents=True, exist_ok=True)
    final = out / f'{a.name}.mp4'
    if a.render or not raw.exists():
        print(f'Rendering ({a.quality})…', flush=True)
        r = subprocess.run([str(HERE / 'hf'), 'render', '--quality', QUALITY[a.quality], '--output', str(raw)], cwd=comp)
        if r.returncode != 0 or not raw.exists():
            sys.exit('Render failed; see the HyperFrames output above.')

    # 3. verify
    info = probe(raw)
    dur = float(info['format']['duration'])
    v = next((s for s in info['streams'] if s['codec_type'] == 'video'), {})
    has_audio = any(s['codec_type'] == 'audio' for s in info['streams'])
    if abs(dur - timing['duration']) > 0.5:
        report['issues'].append(f'duration: {dur:.2f}s rendered vs {timing["duration"]}s planned')
    if (v.get('width'), v.get('height')) != (w, h):
        report['issues'].append(f'dimensions: {v.get("width")}x{v.get("height")} rendered vs {w}x{h} planned')
    if (sb.get('music') not in (None, 'none') or (comp / 'assets/audio/voiceover.wav').exists()) and not has_audio:
        report['issues'].append('audio: no audio stream although music or voice was planned')

    # 4. poster
    if a.poster is None:
        first = timing['scenes'][0]
        a.poster = round(min(first['end'] - 0.35, first['start'] + 3.2), 2)
    poster = out / f'{a.name}.jpg'
    run(['ffmpeg', '-y', '-v', 'error', '-ss', str(a.poster), '-i', str(raw), '-frames:v', '1', '-q:v', '2', str(poster)])

    # 5. bake poster as frame 0 + social encode in one pass
    voiced = (comp / 'assets/audio/voiceover.wav').exists()
    # Loudness for feeds: narration at -16 LUFS; a music-only bed sits lower at -20 LUFS.
    audio_args = ['-af', loudnorm(raw, -16 if voiced else -20), '-c:a', 'aac', '-b:a', '192k', '-ar', '48000'] if has_audio else []
    fade = 0.3
    run(['ffmpeg', '-y', '-v', 'error', '-i', str(raw), '-loop', '1', '-framerate', '30', '-t', str(fade), '-i', str(poster),
         '-filter_complex', f"[1:v]scale={w}:{h},format=rgba,fade=t=out:st=0:d={fade}:alpha=1[p];"
                            f"[0:v][p]overlay=0:0:eof_action=pass,format=yuv420p,fps=30[v]",
         '-map', '[v]', '-map', '0:a?', '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'slow', '-crf', '18',
         *audio_args, '-movflags', '+faststart', str(final)])
    finfo = probe(final)
    size_mb = int(finfo['format']['size']) / 1e6
    report['video'] = {'path': str(final), 'duration': round(float(finfo['format']['duration']), 2), 'sizeMB': round(size_mb, 1), 'audio': has_audio}
    report['poster'] = {'path': str(poster), 'at': a.poster}
    if size_mb > 200:
        report['issues'].append(f'size: {size_mb:.0f} MB is above 200 MB; re-run with --quality standard for faster uploads')

    # 6. captions
    srt = out / 'captions.srt'
    if srt.exists():
        shutil.copy2(srt, out / f'{a.name}.srt')
        report['captions'] = str(out / f'{a.name}.srt')
    if (out / 'post.md').exists():
        report['post'] = str(out / 'post.md')

    (out / 'delivery.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
