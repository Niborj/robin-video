---
name: robin-video
description: Robin-Video turns a document (PDF, PowerPoint, Word, text, Markdown, HTML, CSV or images) into a short, engaging, animated social video for LinkedIn and other feeds, on-brand for Cato Networks: scroll-stopping hooks, kinetic type, motion graphics, animated stats and diagrams, real pages from the source, music, optional narration with captions, a poster frame and ready-to-paste post copy. Built on the /brag workflow and HyperFrames. Use when someone says "/robin-video", "Robin-Video", "make a LinkedIn video from this", "turn this PDF/deck/report/doc into a social video", "animate this for social", or wants a Cato-branded social clip from a file.
---

# Robin-Video

Documents in, scroll-stopping Cato social video out.

`/brag` makes launch videos from a codebase. Robin-Video applies the same machinery (plan → storyboard → HyperFrames →
check → render → poster → share copy) to **documents**, aimed at **social feeds**, and locked to the **Cato brand**.

## What it does

1. **Ingests** the upload (PDF, PPTX, DOCX, TXT, MD, HTML, CSV, images): text in reading order, candidate stats and
   quotes with source locations, native chart data, tables, embedded images, rendered pages, and clearance flags.
2. **Plans** a social story (hook → value → proof → resolve) and writes `storyboard.json`: scenes, archetypes and copy.
3. **Builds** a first cut automatically: every scene becomes a Cato-branded HyperFrames sub-composition (ring
   super-graphics, Archivo/Inter type, Highlight Green accents, masked word reveals, drawn rings, count-ups, ring-iris
   transitions), with music (15 beds in distinct styles, 10 of them original and royalty-free), SFX and optional
   narration.
4. **Art-directs** it: makes the key moments specific and alive with bespoke motion and real visuals from the document.
5. **Gates** it: HyperFrames `check` (layout, motion, WCAG contrast) and the Cato brand check (palette, fonts, official
   logos, product names, voice, privacy).
6. **Delivers** `video.mp4` (poster baked as frame 0), `video.jpg`, captions `.srt` when narrated, and `post.md`.

## Invocation

```
/robin-video report.pdf
/robin-video deck.pptx --format vertical --duration 20
/robin-video brief.docx --story threat-research --voice
/robin-video notes.md --angle "calm myth-busting, three myths" --count 3
```

| Option | Values | Default |
|---|---|---|
| `--format` | `portrait` (1080×1350, 4:5 feed), `square` (1080×1080), `vertical` (1080×1920, 9:16), `landscape` (1920×1080) | `portrait` |
| `--duration` | seconds | auto, 20–40 |
| `--story` | `threat-research`, `data-story`, `executive-pov`, `product-launch`, `customer-story`, `event`, `explainer`, `employer-brand` | inferred |
| `--angle` | freeform creative direction | inferred |
| `--count` | number of distinct videos (a series from one document) | 1 |
| `--platform` | `linkedin`, `instagram`, `tiktok`, `youtube`, `x` | `linkedin` |
| `--voice` | narration with burned-in captions (local Kokoro; `--engine say` for macOS voices; `--engine elevenlabs` with a voice ID, only on request) | off |
| `--cta`, `--url` | end-card call to action and URL | inferred / `catonetworks.com` |
| `--music` | a bed key from `kit.py music` (`pulse`, `minimal`, `focus`, `cinematic`, `ambient`, `piano`, `lofi`, `mallets`, `uplift`, `deep`, or a /brag `vol-*` bed), or an audio file path | picked for the story (`references/audio.md`) |
| `--no-music`, `--no-sfx` | flags | music and SFX on |

Files can be attached, dropped in the working directory, or given as paths. If the user gives no file, ask for one.
Map a freeform request to these options; keep the user's words as the creative direction.

## Skill directory and tools

`<skill-dir>` is the folder containing this file (Claude Code prints it as "Base directory for this skill"). Resolve it;
never assume an install path. Scripts:

| Script | Runs with | Does |
|---|---|---|
| `scripts/ingest.py` | `uv run --project <skill-dir>/scripts python …` | documents → `source/content.md`, `content.json`, `pages/`, `images/` |
| `scripts/kit.py` | `python3` | `storyboard.json` → HyperFrames project with the Cato kit (`build`), media, icons, music |
| `scripts/brand_check.py` | `python3` | the Cato brand gate |
| `scripts/voice.py` | `python3` | narration, timing fit, captions (only with `--voice`) |
| `scripts/deliver.py` | `python3` | brand gate, render, verify, poster, social encode, delivery.json |
| `scripts/compose_music.py` | `uv run --with numpy --with scipy python …` | new original music variations with cue files (optional) |
| `scripts/hf` | shell | pinned HyperFrames CLI (`hf check`, `hf snapshot`, `hf preview`, `hf render`) with a safe npm cache |

Requirements: Node 22+, ffmpeg/ffprobe, `uv`. Narration also needs `scripts/setup_voice.sh` run once.

## Output directory

`robin-video-output/<slug>/` in the working directory. `<slug>` is the main file's name, lowercased with hyphens
(`ingest.py` prints it as `slug`); add `-YYYYMMDD-HHmmss` if the folder exists. With `--count N`, one folder per video:
`<slug>-1`, `<slug>-2`, …

```
robin-video-output/<slug>/
  source/            content.md, content.json, pages/, images/        (Step 1)
  plan.md            angle, hooks, story spine, claims table           (Step 2)
  storyboard.json    the contract: scenes, archetypes, copy, timing    (Step 2)
  composition/       HyperFrames project (index.html + compositions/)  (Step 3)
  timing.json, brand-report.md                                         (Step 3)
  video.mp4, video.jpg, video.srt*, post.md, delivery.json             (Step 4)
```

---

## Step 1 · Ingest and understand

**Read:** [references/step-1-ingest.md](references/step-1-ingest.md)

Run `ingest.py` on every file, then read `source/content.md` **in full**. Answer the ingest rubric (audience, the one
idea, the strongest proof, visual assets, clearance).

**Clearance gate.** If `content.md` lists clearance flags (confidential/internal/draft markers, customer or user names,
emails, internal hosts), tell the user what you found and confirm the content is cleared for public social media
before making anything public-facing. Never put personal data, customer names (unless the source is a published case
study), internal URLs or unreleased claims on screen. If the document's product names are not on the approved list,
ask the user rather than silently dropping or using them.

**Gate:** you can state the one idea in one sentence, and every number you plan to use is traced to a location (`[p3]`).

## Step 2 · Plan the social story

**Read:** [references/step-2-plan.md](references/step-2-plan.md) and [references/hooks.md](references/hooks.md)

Write `plan.md` (angle, three hook options and the pick, the story spine, claims table, audio, post-copy draft), then
`storyboard.json` (scenes with archetypes and on-screen copy). The archetype catalog and every field:
[references/scene-archetypes.md](references/scene-archetypes.md).

**Gate:** `storyboard.json` exists; the hook lands in the first 2 seconds; durations sum to the target; every scene's
copy fits its reading time; the end card has a call to action.

## Step 3 · Build, art-direct and check

**Read:** [references/step-3-compose.md](references/step-3-compose.md), [references/cato-brand.md](references/cato-brand.md),
[references/audio.md](references/audio.md). For bespoke motion, the HyperFrames domain skills: `hyperframes-core`,
`hyperframes-animation`, `hyperframes-keyframes` (and `hyperframes-creative`, `hyperframes-cli` as needed). Robin-Video
is its own workflow: do not enter the `hyperframes` entry-point interview or its generic promo workflows.

1. `python3 <skill-dir>/scripts/kit.py build <out>` → a complete, on-brand first cut.
2. Snapshot it (`hf snapshot --at <scene midpoints>`) and look at every scene.
3. **Art-direction pass:** make it specific to this document. Use real pages and charts, add bespoke motion to the
   hook and the proof moment, tune timing to the music cues, pick SFX. Edit `compositions/<scene>.html` directly.
4. With `--voice`: `python3 <skill-dir>/scripts/voice.py <out>` (fits timing, adds captions, rebuilds).
5. Gates: `hf check` in `composition/` → 0 errors (contrast included); `brand_check.py <out>/composition` → PASS.

**Gate:** both checks pass, and you have looked at a settled frame of every scene.

## Step 4 · Render and deliver

**Read:** [references/step-4-deliver.md](references/step-4-deliver.md) and [references/platforms.md](references/platforms.md)

Write `post.md` (the LinkedIn post), then `python3 <skill-dir>/scripts/deliver.py <out> --render --poster <t>`.
It re-runs the brand gate (including the post), renders, verifies, bakes the poster as frame 0, encodes for feeds and
writes `delivery.json`. Offer `hf preview` before the final render when the user wants to review in HyperFrames Studio.

**Gate:** `video.mp4` and `video.jpg` exist, `delivery.json` has no unresolved checks, `post.md` passes the brand gate.

---

## Creative laws

**Hook in 2 seconds.** Most feed viewers decide in the first two seconds, on mute. The first frame already carries
the hook in big type; never open on a logo sting, a blank gradient or a slow fade.

**Built for mute.** On-screen text carries the story. With `--voice`, captions are burned in.

**One idea.** A social video makes one point and proves it. A second idea is a second video (`--count`).

**Value before evidence.** The viewer learns why it matters by the second beat; data, pages and diagrams then prove it.

**Show the source.** At least one scene uses something real from the document: a page, a chart's data, a quote, a
diagram, a number with its location. Never invent statistics, quotes or customer names.

**Readable at phone size.** Fast in, then hold: a label holds 0.8 s settled, a sentence 0.3 s per word. Headlines 3–12
words; no on-screen paragraphs. Minimum on-screen text 28 px at 1080 wide.

**Calmly confident (the Cato voice).** Clear, not complicated; confidence without alarm; no hype, fear words,
exclamation marks or shouting capitals. Key words in Highlight Green carry the emphasis.

**Unmistakably Cato.** Reveal what matters → Connect ideas → Resolve with clarity. Palette, Archivo and Inter, the flat
Ring, official logos only. Motion is calm and decisive: masked rises, drawn rings, clean settles; no bounce, glitch,
shake, 3D or cyber clichés.

**Short.** 20–40 s is the feed sweet spot (LinkedIn), 15–30 s for vertical; a teaser can be 10–15 s.

## Story types

| Type | Use for | Shape |
|---|---|---|
| `threat-research` | research findings, telemetry reports | Finding hook → the number → what it means → what to do → CTA |
| `data-story` | surveys, benchmarks, metrics | Stat hook → 2–3 proof stats → so what → CTA |
| `executive-pov` | analyst reports, POV papers, blogs | Contrarian or reframe hook → argument in 3 beats → takeaway |
| `product-launch` | announcements, release notes, decks | What changed → why it matters → how it works → availability |
| `customer-story` | case studies (published) | Customer challenge → approach → outcome stat → quote |
| `event` | webinars, booths, keynotes | Hook → what you'll learn → who/when/where → register |
| `explainer` | how-tos, concepts, training decks | Question hook → model built step by step → takeaway |
| `employer-brand` | culture, hiring, people stories | Human hook → story → values → join us |

Full guidance, pacing and scene counts: [references/step-2-plan.md](references/step-2-plan.md).
