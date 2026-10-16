# Step 4 · Render and deliver

## 1. Write the post copy

Write `<out>/post.md`, the text that goes with the video. It passes through the same brand gate as the on-screen copy.

```markdown
# LinkedIn post

<Line 1: a hook that works on its own, ≤ 140 characters (what shows before "…see more"). Not the video's exact hook;
complement it.>

<2–4 short lines of value: what the viewer learns, the strongest proof with its source, why it matters to them.>

<One clear call to action, with the URL if there is one.>

#Hashtag #Hashtag #Hashtag

# Alt text
<One or two sentences describing the video for screen readers.>

# Variants
- Short (X/Threads, ≤ 280 characters): …
- First comment (optional, for the link if the user prefers links out of the post body): …
```

Rules: 1–3 short paragraphs, 900–1,300 characters at most for LinkedIn; three to five relevant hashtags (#AISecurity,
#SASE, #CyberSecurity, #ZeroTrust, #NetworkSecurity…); no "excited to announce", no emoji walls (one or two at most, or
none for executive content); Cato voice and approved product names; the same claims as the video, nothing new.

## 2. Preview (when the user wants to review)

```bash
cd <out>/composition && <skill-dir>/scripts/hf preview --background
```

Give the user the Studio URL. They can scrub, comment and edit in HyperFrames Studio. Keep the server alive while they
review; render after they approve. If they asked for a finished video without review, go straight to delivery.

## 3. Deliver

```bash
python3 <skill-dir>/scripts/deliver.py <out> --render --poster <seconds> [--quality high|standard|draft]
```

- Runs the brand gate on the composition and `post.md`; stops on errors.
- Renders through HyperFrames (`high` = HyperFrames `delivery` quality; `draft` for quick looks).
- Verifies duration against `timing.json`, dimensions against the format, and that planned audio exists.
- **Poster:** pass the time of the strongest settled frame (usually the hook, fully revealed, around `hook end − 0.4 s`;
  sometimes the key stat). Not a transition, not mid-reveal, ideally between caption cues. It becomes `video.jpg` and
  **frame 0** of the delivered file, then dissolves into the live video over the first 0.3 s, so every feed, chat app
  and player shows it as the idle thumbnail and autoplay never flashes it. Also upload `video.jpg` as the custom
  thumbnail where the platform allows it (LinkedIn's post editor, YouTube, Instagram).
- Encodes for feeds: H.264 High, yuv420p, 30 fps, AAC 48 kHz, loudness-normalized (−16 LUFS with narration, −20 LUFS
  music only), faststart. Copies `captions.srt` to `video.srt`. The untouched render stays in
  `composition/renders/video.render.mp4`; re-running `deliver.py` without `--render` (for example with a different
  `--poster`) reuses it.
- Writes `delivery.json`: `gates` (the brand gate result) and `issues` (duration, dimensions, audio or size problems).
  An empty `issues` list means delivery is clean; anything listed needs fixing or explaining to the user.

Look at `video.jpg` before you hand over: it must be postable on its own.

## 4. Tell the user

- Where the video, poster, captions and post copy are (paths), the format and length.
- One sentence on the creative angle and the hook.
- The claims used and their sources, and anything anonymized or flagged at the clearance gate.
- Anything not done or not verified (for example "narration pronunciation of product names not reviewed by ear").
- Offer: another format (re-run `build` with a different `format` into a new folder; layouts adapt), a teaser cut, a
  different hook, or the next video in a series.

## Multiple formats

Make each format its own output folder (copy `storyboard.json`, change `format`, run `build`, art-direct, check,
deliver). Layouts adapt automatically, but always snapshot: a headline that fits 4:5 can wrap differently in 9:16 or
16:9, and `doc` focus areas need re-checking.
