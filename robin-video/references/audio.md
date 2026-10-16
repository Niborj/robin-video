# Audio

Social video is watched muted first, so sound is a reward, not a dependency: a tasteful bed, a few motion-matched
accents, and narration only when asked for (`--voice`). Music and SFX are on by default unless the user passes
`--no-music` or `--no-sfx`.

## Music beds: 15 bundled, 10 of them original

`python3 <skill-dir>/scripts/kit.py music` lists them. Pick by story and energy, and vary the bed across a series.

**Original tracks** (composed for Robin-Video by `scripts/compose_music.py`: no samples or third-party recordings, so
they are owned and royalty-free, safe for corporate posts and for sharing the skill):

| Key | Style | Tempo | Best for |
|---|---|---|---|
| `pulse` | Tech pulse: driving kick, plucked arpeggios, minor key | 118 | product launches, announcements, data stories |
| `minimal` | Minimal data: ticks, rimshots, rolling bass, short stabs | 124 | threat research, data stories |
| `focus` | Calm suspense: ticking clock, low drone, sparse piano (never alarming) | 100 | threat research, problem statements |
| `cinematic` | Cinematic rise: strings, ostinato, big low hits | 92 | reveals, research findings, launch hooks |
| `ambient` | Ambient glow: no drums, evolving pads and bells | 72 | thought leadership, executive POV, reflective openers |
| `piano` | Hopeful piano: arpeggios over soft strings, light pulse | 96 | customer stories, people stories |
| `lofi` | Lo-fi focus: swung beat, electric piano, vinyl texture | 84 | explainers, how-tos, employer brand |
| `mallets` | Playful mallets: marimba, shaker, light drums | 108 | explainers, employer brand, light news |
| `uplift` | Bright corporate: strummed guitar, claps, bells | 112 | events, partner news, wins |
| `deep` | Deep house: warm filtered chords, rolling bass | 120 | events, culture, energetic teasers |

Each original track is 48–60 s with sections (intro → build/main → lift → outro), mastered to the tonal balance of
produced library music at −14.5 LUFS. Its cue file lists exact beats and the **section starts**, where the arrangement
lifts: the best places to land the hook payoff, the key stat or the end card.

**From /brag** ("Happy Beats / Business Moves" by ende.app; confirm the license before publishing externally):
`vol-12` steady and clean (110 BPM, the default when `music` is not set) · `vol-11` warm, business-like · `vol-1` most
energetic · `vol-9` mid-energy, laid back · `vol-10` compact, punchy loop.

**By story type** (first choice, alternative):

| Story | Music |
|---|---|
| `threat-research` | `minimal`, `focus` |
| `data-story` | `pulse`, `minimal` |
| `executive-pov` | `ambient`, `cinematic` |
| `product-launch` | `cinematic` (reveal), `pulse` |
| `customer-story` | `piano`, `uplift` |
| `event` | `deep`, `uplift` |
| `explainer` | `lofi`, `mallets` |
| `employer-brand` | `mallets`, `lofi` |

Set `music` in `storyboard.json` to a key, to `none`, or to a path to your own audio file (relative to the output
folder; a `cues/<file stem>.music-cues.json` next to it is copied too). `build` copies the track and its cue file and
writes the bed with a 0.6 s fade-in and a fade-out over the last ~2 s. Level: `musicVolume` 0.25–0.35 without voice
(about −25 dB mean); 0.12–0.16 under narration (automatic). Never above 0.5.

**More variety on demand.** `compose_music.py` makes new variations of any style (a different seed changes the patterns,
voicings and sound details while keeping the style), with cue files:

```bash
uv run --with numpy --with scipy python <skill-dir>/scripts/compose_music.py --out <out>/music --style pulse --seed 12
```

Then set `"music": "music/robin-pulse-s12.mp3"`.

## Beat and cue alignment

Read the cue file `build` copied next to the track: `composition/assets/music/cues/<track file name>.music-cues.md`
(for example `happy-beats-business-moves-vol-12-by-ende-dot-app.music-cues.md`). The `.md` summarizes the first 25 s;
for longer videos read `beats` and `strongCues` from the `.json` beside it. Use cues as hints, not rules:

- Move the hook payoff, the key stat and the end-card landing toward a strong cue (within ±0.15 s) by adjusting scene
  durations in `storyboard.json` or tween times in a scene.
- Sequential reveals (cards, list items) may snap to consecutive beats (±0.10 s) only if each item still gets its
  reading time; otherwise every other beat.
- Ignore cues that hurt readability or the story.

## SFX (CC0, Kenney and OpenGameArt, bundled from /brag)

Add per scene in `storyboard.json`: `"sfx": [{"file": "interface/drop_001.ogg", "at": 0.4, "volume": 0.55}]` (`at` is
seconds from the scene start, aligned to the start of the motion it accents). `build` copies the files, places them
and sizes each slot to the sound's real length. Short UI sounds (0.1–0.2 s) are quiet under a bed: use 0.55–0.7 volume
for them, and listen to the render.
Read `assets/sfx/sfx-analysis.md` and prefer files with low high-frequency risk.

Cato's sound is calm and precise: 2–5 cues per video, volume 0.45–0.7.

| Moment | Good files |
|---|---|
| A stat or card lands | `interface/drop_001.ogg`, `interface/drop_002.ogg`, `ui/click3.ogg` |
| List items or nodes appearing | `interface/click_002.ogg`, `ui/switch2.ogg` (accent first and last only) |
| Ring iris on a key transition | `impact/impactSoft_medium_001.ogg` (soft, at the transition start) |
| End card / logo | `impact/impactBell_heavy_000.ogg` at 0.45–0.55, or `interface/bong_001.ogg` |
| Typed question | `keyboard/keypress-0NN.wav`, randomized, sparse |

Avoid for Cato: glitch, error buzzes, punches, metal clangs, casino sounds; nothing that signals alarm.

## Narration (`--voice`)

Local Kokoro TTS through HyperFrames (offline; scripts never leave the machine). Cloud voices only with the user's
explicit approval and for content cleared for external processing: `--engine elevenlabs --voice <voice ID>` sends each
narration line to ElevenLabs (model `eleven_multilingual_v2` unless `--model`), uses the voice's stored settings and
trims edge silence. The key comes only from `ELEVENLABS_API_KEY` in the environment of that one command: never write it
to a file, the storyboard or memory, and never echo it. Write lines for the ear (short sentences, under ~20
words, contractions), complement the screen rather than read it, ~140–165 words per minute. `voice.py` does the rest.
