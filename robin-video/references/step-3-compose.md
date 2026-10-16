# Step 3 · Build, art-direct and check

## 1. Build the first cut

```bash
python3 <skill-dir>/scripts/kit.py build <out>
```

This writes `<out>/composition/`, a standard HyperFrames project:

- `index.html`: the host. Scene slots at computed starts (each scene overlaps the next by `overlap` so the ring iris
  opens over it), the music bed with fade-in/out automation, SFX, voiceover and captions when present. **Generated:**
  change timing, order, music or SFX in `storyboard.json` and re-run `build`.
- `compositions/<id>.html`: one sub-composition per scene, generated once from its archetype. **Yours to edit.** `build`
  keeps your edits and only re-syncs their timing attributes; `--force-scenes id1,id2` (or `all`) regenerates.
- `assets/cato/`: fonts, verified logos, icons, `cato.css`, `cato-motion.js`; `assets/vendor/gsap.min.js` (local, no
  CDN at render time); `assets/music/`, `assets/sfx/`, `assets/source/` (pages and images from the document).
- `<out>/timing.json`: every scene's start and end, for SFX, cue alignment, poster choice and snapshots.

The HyperFrames CLI runs through the wrapper (pinned version, safe npm cache): `<skill-dir>/scripts/hf <command>` from
inside `composition/`. Below, `hf` means that wrapper.

## 2. Look at it

```bash
cd <out>/composition && <skill-dir>/scripts/hf snapshot --at <t1>,<t2>,…
```

Take one settled time per scene (end − 0.4 s, from `timing.json`) plus the hook at 1.0 s, and read the contact sheet
(`contact-sheet.jpg`, or `contact-sheet-1.jpg`, `-2.jpg`… beyond nine frames). The `hf` wrapper passes
`--describe false` to snapshots so frames of internal documents are never sent to a vision service; pass `--describe`
yourself only for cleared content and with the user's agreement.
Check: the hook is legible by ~1 s; nothing overlaps or clips; no `TODO`; numbers and labels make sense together; the
document page in a `doc` scene is framed on the right region; contrast reads at phone size.

## 3. Art-direction pass (where the video gets good)

The archetypes give a correct, on-brand first cut. Your job is to make this video **specific** to this document and
audience. Spend your effort on the hook, the single strongest proof moment, and the end. Work in the scene files.

1. **The hook's one bespoke move** (see `hooks.md`). It should be impossible to reuse for another document.
2. **Show the source.** Prefer native chart data (rebuild as cards, stat rings, or a simple bar build with `.card`
   containers) over screenshots; use a `doc` scene with a precise `focus` for pages that carry credibility (cover,
   methodology, the chart page). Look at the page image before setting `focus`.
3. **Connect the parts.** Where the argument has a relationship (cause → effect, user → Cato → app, before → after),
   show it with `flow`, `compare` or drawn paths, not with more text.
4. **Rhythm and music.** Read the cue file (`assets/music/cues/*.music-cues.md`). Nudge the hook payoff, the key stat
   and the end card toward strong cues (±0.15 s) by adjusting scene durations in `storyboard.json` (then `build`) or
   tween times inside a scene. Sequential reveals may snap to beats only if each item still gets its reading time.
5. **SFX, sparingly.** 2–5 cues per video, motion-matched: a soft drop or click as a stat or card lands, a gentle bell
   on the end card. Add them to the scene's `sfx` list (times relative to the scene start) and re-run `build`. Choose
   files with low high-frequency risk from `assets/sfx/sfx-analysis.md` (see `audio.md`).
6. **Hold the end card** at least 2.5 s with the logo, one line, the CTA and the URL.

Gates do not judge taste: line breaks, crowding, tiny details and empty areas only show up when you look. Snapshot
again after every change that matters.

Bespoke work follows the HyperFrames contract (`hyperframes-core`): everything inside `<template>`, root styled by
`#root`, one paused timeline per scene registered at `window.__timelines["<id>"]`, `fromTo` entrances, deterministic
timing, no CSS transform on a tweened element, no `<br>` in body text. Keep colors to palette tokens.

## 4. Voice (only with `--voice`)

Add a `say` line (or list) to the scenes that need narration: write for the ear, short sentences, complementing the
screen rather than reading it. Then:

```bash
python3 <skill-dir>/scripts/voice.py <out> [--voice af_heart] [--speed 1.0] [--engine say]
ELEVENLABS_API_KEY=… python3 <skill-dir>/scripts/voice.py <out> --engine elevenlabs --voice <voice ID> [--speed 0.95]
```

Split a scene's narration into several `say` lines when on-screen beats should land with specific words: each line is
placed separately and `voice-timing.json` records every line's start and end (global and scene-local), so bespoke tweens
can hit the exact moment a number or phrase is spoken.

It voices each line locally, lengthens scenes that need more time (keeping `plannedDuration`), mixes
`assets/audio/voiceover.wav`, ducks the music, writes `captions.srt` and burned-in captions (`compositions/captions.html`,
spoken word in Highlight Green, scene content lifted clear of the caption band), checks the narration against the voice
rules, and rebuilds. Listen for "Cato" and product terms; add `pronunciations` to `storyboard.json` if needed (Kokoro
voices: `af_heart` default, `af_nova`, `am_michael`, `am_adam`, `bf_emma`, `bm_george`). First time only:
`<skill-dir>/scripts/setup_voice.sh`. ElevenLabs (only when the user asks, see `audio.md`): speed range 0.7–1.2; its
voices often read faster than Kokoro, so check `wpm` in `voice-report.json` and re-sync any tween timed to a word
(`voice-timing.json`, or `ffmpeg … silencedetect` on `assets/audio/lines/<scene>-01.wav` for phrase breaks).
`voice.py` only lengthens scenes: before re-voicing, set each `duration` back to its `plannedDuration`.

## 5. Gates

```bash
cd <out>/composition && <skill-dir>/scripts/hf check
python3 <skill-dir>/scripts/brand_check.py <out>/composition
```

- `hf check` must report **0 errors**; fix every contrast failure (each carries a suggested color: pick the nearest
  palette color that passes). Layout findings during transitions are informational; persistent ones are not.
- The brand gate must **PASS**. Warnings need a reason in `plan.md` if kept.
- If `check` reports a sub-composition timeline not registering, the host `data-composition-id` and the scene's
  `window.__timelines` key differ: keep them identical to the scene id.

## Self-review checklist

- [ ] Hook legible by ~1 s, at hero size, promise paid off by the second beat.
- [ ] One idea; every scene earns its place (delete test from `step-2-plan.md`).
- [ ] At least one real element from the source (page, chart data, quote, number with location).
- [ ] Every claim traced in the claims table; nothing invented; sample data labeled.
- [ ] Reading floor met everywhere; no paragraph on screen.
- [ ] Palette, type, Ring, logo per `cato-brand.md`; flat 2D; calm motion.
- [ ] Music bed under control (≈ −25 dB mean without voice, ducked under narration); SFX sparse and on the motion.
      `deliver.py` normalizes the final mix (−16 LUFS narrated, −20 LUFS music only).
- [ ] `hf check` 0 errors; brand gate PASS; you have looked at every scene's settled frame.
