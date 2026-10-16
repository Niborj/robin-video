# Robin-Video

A Claude Code skill that turns a document into a short, animated, Cato-branded social video.

Upload a PDF, PowerPoint, Word document, text/Markdown file, HTML page, CSV or images and say `/robin-video`. You get
a LinkedIn-ready MP4 with a scroll-stopping hook, kinetic type, motion graphics (drawn Cato rings, count-ups, data
cards, before/after splits, connect diagrams, real pages from your document), ring-iris transitions, music and SFX,
optional narration with burned-in captions, a poster frame, and the post copy. It is the `/brag` workflow (plan →
storyboard → HyperFrames → check → render → poster → share copy) re-aimed from codebases at documents and social feeds,
and locked to the Cato brand.

## Use it

```
/robin-video report.pdf
/robin-video deck.pptx --format vertical --duration 20
/robin-video brief.docx --story threat-research --voice
/robin-video notes.md --angle "three myths, calmly busted" --count 3
```

Formats: `portrait` 1080×1350 (LinkedIn feed default), `square`, `vertical` 9:16, `landscape` 16:9. Output lands in
`robin-video-output/<slug>/`: `video.mp4`, `video.jpg`, `video.srt` (narrated), `post.md`, plus the plan, storyboard and
the editable HyperFrames project (open it in HyperFrames Studio with `scripts/hf preview`).

## What keeps it on brand

- **Cato kit** (`robin-video/assets/kit/`): palette tokens, Archivo/Inter (bundled), the Ring family drawn with the
  official proportions, official logos (SHA-256 verified), outline icons, and `cato-motion.js`, a seek-safe motion
  language: masked word rises, drawn rings, count-ups, focus frames, the ring-iris transition.
- **Scene archetypes** modeled on Cato's own social and presentation examples (Visual Style R101): hook, statement,
  stat ring, dark data cards, compare split, ring-bullet list, quote card, document window, connect diagram, end card.
- **Brand gate** (`scripts/brand_check.py`): rejects off-palette colors, other fonts, modified/stretched logos,
  placeholders, unapproved product names, alarm words, personal data and remote assets; warns on hype, exclamation
  marks, UK spelling, shouting capitals, dense text and 3D/bouncy motion. Runs on the video and the post copy.
- **HyperFrames `check`**: layout, motion and WCAG AA contrast on every frame.

## Install or update

```bash
./install.sh
```

Copies `robin-video/` to `~/.claude/skills/robin-video` (personal install, every folder). Needs Node 22+, ffmpeg and [uv](https://docs.astral.sh/uv/).

This folder also has a project install: `.claude/skills/robin-video` is a link to `robin-video/`, so the skill travels
with the folder and always matches the source. When both exist, Claude Code uses the personal copy (same name), so
after editing `robin-video/` run `./install.sh` to refresh it.
For narration, run once: `~/.claude/skills/robin-video/scripts/setup_voice.sh` (local Kokoro voice; scripts never leave
the machine). If `~/.npm` has root-owned files, the `hf` wrapper uses a private npm cache automatically (or fix it with
`sudo chown -R $(id -u):$(id -g) ~/.npm`).

## Layout

```
robin-video/
  SKILL.md                 the workflow Claude follows
  references/              ingest, planning, hooks, archetypes, brand, compose, deliver, platforms, audio
  scripts/                 ingest.py, kit.py (+ scenes.py), brand_check.py, voice.py, deliver.py, hf, tests
  assets/brand/            cato-brand.json, logos, fonts, icons
  assets/kit/              cato.css, cato-motion.js
  assets/music/            15 beds with beat/section cues: 10 original (compose_music.py), 5 from /brag
  assets/sfx/              CC0 SFX (from /brag)
  assets/vendor/           GSAP (local, no CDN at render time)
  examples/                sample source document and the archetype gallery storyboard
test-runs/                 end-to-end test outputs (local only)
```

Tests: `uv run --project robin-video/scripts python robin-video/scripts/test_robin_video.py`

## Notes

- Brand sources: Cato Brand Hub tokens (15 Oct 2026) and the Cato Visual Style R101 deck (Aug 2026). When the brand
  updates, change `assets/brand/cato-brand.json`, `assets/kit/cato.css` and `references/cato-brand.md` together.
- Music: ten original tracks are composed in code by `scripts/compose_music.py` (owned, royalty-free; regenerate with
  `uv run --with numpy --with scipy python robin-video/scripts/compose_music.py --out robin-video/assets/music`). The
  five `vol-*` tracks come from `/brag` ("Happy Beats / Business Moves", ende.app); confirm their license before
  publishing externally.
- Videos made from internal documents stop at a clearance gate: Claude confirms the content is cleared for public
  social media and anonymizes customer and personal data.
