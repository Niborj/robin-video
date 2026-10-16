# Platforms

| Platform | Best format | Length sweet spot | Notes |
|---|---|---|---|
| **LinkedIn feed** | `portrait` 1080×1350 (4:5) | 20–40 s | Autoplays muted; 4:5 takes the most feed space on mobile. Upload the poster as the thumbnail and `video.srt` as captions when narrated. Videos 3 s–15 min, up to 5 GB; keep under ~200 MB. |
| LinkedIn (desktop-first, events, webinars) | `landscape` 1920×1080 or `square` | 20–60 s | Square is the safe all-rounder. |
| LinkedIn vertical video / Instagram Reels / TikTok / YouTube Shorts | `vertical` 1080×1920 (9:16) | 15–30 s | The platform UI covers the top ~250 px, bottom ~420 px and right edge: the kit's vertical safe area already keeps content clear. |
| Instagram feed | `portrait` 4:5 | 15–30 s | |
| YouTube / website / event screens | `landscape` 16:9 | 30–90 s | Narration usually expected. |
| X | `square` or `landscape` | 15–30 s | Short post copy variant (≤ 280 characters). |

All formats are 1080 px on their short side, so the type scale is shared. Safe areas per format live in `cato.css`
(`--pad-x`, `--pad-top`, `--pad-bottom`), and burned-in captions move content up automatically (`.has-captions`).
Square is the tightest with captions (750 px above the caption band), so it also switches to a compact type scale and
a smaller stat ring; centered square scenes center below the corner logo.

## Captions and accessibility

- Muted autoplay is the default: on-screen text tells the story without sound.
- With narration: burned-in captions (default) for the feed, plus `video.srt` for the platform's caption upload.
- Contrast: every text element passes WCAG AA (enforced by `hf check`).
- No flashing more than three times per second; no strobing transitions.
- Provide alt text in `post.md`.
