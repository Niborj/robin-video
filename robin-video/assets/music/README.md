# Music

## Original tracks (owned, royalty-free)

Composed and synthesized for Robin-Video by `scripts/compose_music.py`: no samples, loops or third-party recordings.
They can be used in published videos and redistributed with the skill.

| File | Style | Tempo | Length |
|---|---|---|---|
| `robin-pulse.mp3` | Tech pulse | 118 | 0:57 |
| `robin-minimal.mp3` | Minimal data | 124 | 0:54 |
| `robin-focus.mp3` | Calm suspense | 100 | 0:58 |
| `robin-cinematic.mp3` | Cinematic rise | 92 | 0:52 |
| `robin-ambient.mp3` | Ambient glow | 72 | 0:53 |
| `robin-piano.mp3` | Hopeful piano | 96 | 1:00 |
| `robin-lofi.mp3` | Lo-fi focus | 84 | 0:57 |
| `robin-mallets.mp3` | Playful mallets | 108 | 0:53 |
| `robin-uplift.mp3` | Bright corporate | 112 | 0:51 |
| `robin-deep.mp3` | Deep house | 120 | 0:48 |

Regenerate or make variations: `uv run --with numpy --with scipy python scripts/compose_music.py --out <dir> --style all [--seed N]`
(seed 7 reproduces these files).

## From ende.app

- `happy-beats-business-moves-vol-1-by-ende-dot-app.mp3` (2:44)
- `happy-beats-business-moves-vol-9-by-ende-dot-app.mp3` (1:54)
- `happy-beats-business-moves-vol-10-by-ende-dot-app.mp3` (1:00)
- `happy-beats-business-moves-vol-11-by-ende-dot-app.mp3` (1:28)
- `happy-beats-business-moves-vol-12-by-ende-dot-app.mp3` (1:58)

Source: [ende.app](https://ende.app/en) "Happy Beats / Business Moves" series. Verify the exact license terms before
publishing externally.

## Cue files

`cues/<track-stem>.music-cues.json` and `.md`: tempo, the beat grid and strong cues (for the original tracks: exact
beats from the composition grid, section starts and 4-bar phrase starts). Read them when aligning reveals to the music.
