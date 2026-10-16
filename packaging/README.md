# Robin-Video

A Claude Code skill that turns a document into a short, animated, Cato-branded social video.

Give it a PDF, PowerPoint, Word document, text or Markdown file, HTML page, CSV or images, and it makes a
LinkedIn-ready MP4: a scroll-stopping hook, kinetic type, motion graphics (Cato rings, count-ups, data cards,
before/after splits, diagrams, real pages from your document), music, optional narration with captions, a poster
frame and ready-to-paste post copy. Every video passes a Cato brand check (palette, Archivo/Inter, official logos,
approved product names, Cato voice) before it renders.

Version 1.1 · October 2026 · built on the `/brag` workflow and HyperFrames.

**New in 1.1:** 15 music beds in distinct styles. Ten are original tracks composed for Robin-Video (tech pulse,
minimal data, calm suspense, cinematic rise, ambient, hopeful piano, lo-fi, playful mallets, bright corporate, deep
house), owned and royalty-free, with beat and section cues. Claude picks one to fit the story, or you can name one.

## Install (macOS, about 2 minutes)

1. Unzip this folder anywhere.
2. In Terminal, run:

   ```bash
   sh install.sh
   ```

   It copies the skill to `~/.claude/skills/robin-video` and checks the prerequisites below.
3. Restart Claude Code (or start a new session) so it picks up the skill.

### Prerequisites

| Tool | Why | Install |
|---|---|---|
| Claude Code | runs the skill | https://claude.com/claude-code |
| Node.js 22 or newer | HyperFrames renders the video | `brew install node` |
| ffmpeg | audio, posters, final encode | `brew install ffmpeg` |
| uv | reads PDFs, decks and Word files | `brew install uv` |

The first video downloads the HyperFrames renderer (pinned version, via `npx`), so the first run needs internet and
takes a little longer.

**Optional narration:** for `--voice`, run once:

```bash
~/.claude/skills/robin-video/scripts/setup_voice.sh
```

This sets up a local Kokoro voice (offline after a one-time model download; scripts never leave your machine). Without
it, use the built-in macOS voices with `--engine say`.

## Use

In Claude Code, from the folder where you want the output:

```
/robin-video report.pdf
/robin-video deck.pptx --format vertical --duration 20
/robin-video brief.docx --story threat-research --voice
/robin-video notes.md --angle "three myths, calmly busted" --count 3
```

| Option | Values | Default |
|---|---|---|
| `--format` | `portrait` (4:5, LinkedIn feed), `square`, `vertical` (9:16), `landscape` (16:9) | `portrait` |
| `--duration` | seconds | 20–40 s, automatic |
| `--story` | `threat-research`, `data-story`, `executive-pov`, `product-launch`, `customer-story`, `event`, `explainer`, `employer-brand` | inferred |
| `--angle` | any creative direction in your own words | inferred |
| `--count` | several distinct videos from one document | 1 |
| `--voice` | narration with burned-in captions | off |
| `--cta`, `--url` | end-card call to action and link | inferred / catonetworks.com |
| `--music` | `pulse`, `minimal`, `focus`, `cinematic`, `ambient`, `piano`, `lofi`, `mallets`, `uplift`, `deep` (or a /brag bed) | picked for the story |
| `--no-music`, `--no-sfx` | turn audio layers off | on |

You can also just ask: "Make a LinkedIn video from this report, vertical, with narration."

Results land in `robin-video-output/<document-name>/`:

- `video.mp4`: the video (its first frame is the poster, so thumbnails look right everywhere)
- `video.jpg`: the poster, also handy as a custom thumbnail
- `video.srt`: captions for upload (narrated videos)
- `post.md`: LinkedIn post copy, hashtags and alt text
- `plan.md`, `storyboard.json`, `composition/`: the plan and an editable HyperFrames project. To review or tweak it in
  HyperFrames Studio, run `~/.claude/skills/robin-video/scripts/hf preview` from inside `composition/`.

## Good to know

- **Internal documents:** if a document looks internal (Confidential, Draft, written for employees, customer data),
  Claude stops and asks whether the content is cleared for public social media, and anonymizes names. Only post what
  the owner has cleared.
- **Product names:** only approved Cato product names pass the brand check; anything else is flagged for you to confirm
  with Product Marketing.
- **Music:** the ten `robin-*` tracks are original and royalty-free, so use them anywhere. The five
  "Happy Beats / Business Moves" tracks (`vol-*`, ende.app) come from the `/brag` skill: confirm their license before
  publishing externally. Run `python3 ~/.claude/skills/robin-video/scripts/kit.py music` to list every bed, and
  `scripts/compose_music.py --style <name> --seed <n>` (with `uv run --with numpy --with scipy`) for new variations.
- **Slide images:** PowerPoint slides are rebuilt in motion from their text, charts and images. To show slides as
  pictures, also give it a PDF export of the deck (or install LibreOffice).
- **npm permission errors (EACCES):** the skill's `hf` wrapper switches to a private npm cache automatically. The
  permanent fix is `sudo chown -R $(id -u):$(id -g) ~/.npm`.
- **Updating:** unzip a newer version and run `sh install.sh` again; it replaces the installed copy.
- **Self-test:** `uv run --project ~/.claude/skills/robin-video/scripts python ~/.claude/skills/robin-video/scripts/test_robin_video.py`

## What's inside

```
install.sh              installs to ~/.claude/skills/robin-video
robin-video/
  SKILL.md              the workflow Claude follows
  references/           ingest, planning, hooks, scene types, Cato brand, compose, deliver, platforms, audio
  scripts/              ingest.py, kit.py, scenes.py, brand_check.py, voice.py, deliver.py, compose_music.py, hf, tests
  assets/brand/         Cato brand tokens, official logos, Archivo and Inter fonts (SIL OFL), outline icons
  assets/kit/           cato.css and cato-motion.js (the Cato motion language)
  assets/music/         15 music beds with beat and section cues (10 original, royalty-free)
  assets/sfx/           CC0 sound effects
  assets/vendor/        GSAP (local, so renders need no CDN)
  examples/             a sample (illustrative) source document and a storyboard showing every scene type
```

For Cato internal use. Brand sources: Cato Brand Hub tokens and the Cato Visual Style R101 guidelines.
