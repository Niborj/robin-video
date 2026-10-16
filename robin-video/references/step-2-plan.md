# Step 2 · Plan the social story

Write two files in `<out>/`: `plan.md` (the creative north star, for humans) and `storyboard.json` (the contract that
`kit.py build` turns into a video). Plan before you build: a change here costs seconds, after the build it costs minutes.

## The story spine: Reveal → Connect → Resolve

Cato's design principles (Visibility → Reveal, Context → Connect, Control → Resolve) are also the best social structure:

| Phase | Job | Share of time | Typical archetypes |
|---|---|---|---|
| **Reveal** (hook + value) | Stop the scroll, say why it matters | first 15–25% | `hook`, `stat`, `statement` |
| **Connect** (proof) | Show the evidence and how the parts relate | middle 50–60% | `stat`, `cards`, `compare`, `list`, `flow`, `doc`, `quote` |
| **Resolve** (takeaway + CTA) | Leave one clear takeaway and an action | last 20–25% | `statement`, `list`, `end` |

Self-check: delete the proof scenes and the remaining scenes must still state the value. Delete the value scenes and the
video should stop making sense (otherwise it was a document tour, not a story).

## Story types → shape

| Type | Scenes | Shape (archetypes) | Length |
|---|---|---|---|
| `threat-research` | 5–7 | hook (finding) → stat → cards or doc → statement (what it means) → list (what to do) → end | 25–40 s |
| `data-story` | 5–6 | stat (hook) → cards → doc (the chart page) → statement → end | 20–35 s |
| `executive-pov` | 4–6 | hook (reframe) → statement → compare → statement (takeaway) → end | 20–35 s |
| `product-launch` | 5–7 | hook (what changed) → statement (why) → flow or compare (how) → list (capabilities) → end (availability) | 20–35 s |
| `customer-story` | 5–6 | hook (challenge) → statement (approach) → stat (outcome) → quote → end | 25–40 s |
| `event` | 4–5 | hook → list (what you'll learn) → statement (who/when/where) → end (register) | 15–25 s |
| `explainer` | 5–8 | hook (question) → flow (the model, step by step) → list → statement → end | 30–45 s |
| `employer-brand` | 4–6 | hook (human) → quote → list (values) → end (join us) | 20–30 s |

Vertical (9:16) runs shorter (15–30 s). A teaser cut is 10–15 s: hook → one proof → end.

## Pacing and reading time

Pace comes from motion and cuts, never from pulling text before it can be read.

- **Reading floor:** a label or number holds ~0.8 s settled; a headline or sentence ~0.3 s per word (minimum 1.2 s).
  The hook gets the most.
- **Entrances take ~0.6–1.2 s** with the archetype motion (rise, ring draw, count-up). So a scene's duration ≈ entrance
  + reading floor + ~0.8 s of hold. Typical durations: hook 3.5–4.5 s, statement 3–4 s, stat 4–5 s, cards 4.5–5.5 s,
  compare 5–6 s, list 4.5–6 s (0.55 s per item), quote 5–6 s, doc 4.5–5.5 s, flow 4.5–5.5 s, end 3–3.5 s.
- **Too much copy for the time?** Cut copy or split the scene. Never shorten the hold.
- **Rhythm:** alternate dense and simple scenes; alternate backgrounds (the generator rotates ring placements).

## Copy rules for on-screen text

- Headlines 3–12 words, sentence case, no full stop unless it is two sentences. Hook and statement headlines are
  fitted automatically (size and line breaks); `|` forces a line break.
- `[Brackets]` mark the key words shown in Highlight Green. One highlight per headline; it carries the turn or the value.
- Stats: the number alone in `value` ("71%", "30,254", "$5.02M", "3x"); the meaning in `label` (≤ 14 words).
- Labels on cards, rows, list items and nodes: ≤ 6 words.
- Approved Cato product names only (see `cato-brand.md`); U.S. spelling; no exclamation marks; no hype or fear words.
- Third-party data gets a `source` line. Sample or illustrative data says so on screen.

## plan.md template

```markdown
# Robin-Video plan: <title>

## Ingest rubric
1–10 from step-1-ingest.md.

## The angle
<One paragraph: the creative premise and why it suits this audience. Story type and why.>

## Hook options
1. "<hook A>" — formula, why
2. "<hook B>" — formula, why
3. "<hook C>" — formula, why
**Pick:** <n>, because <reason>.

## Story spine
- Reveal: <what the viewer learns first and why it matters>
- Connect: <the proof beats>
- Resolve: <takeaway + CTA>

## Storyboard (summary of storyboard.json)
| # | Scene id | Archetype | Duration | On screen | Source |
|---|---|---|---|---|---|

## Claims table
| Claim on screen | Exact source wording | Location | Notes |

## Format and length
<format, size, target seconds, platform>

## Audio
- Music: <track key> because <mood and story type> (see the story table in audio.md); cue notes (land the hook payoff
  and the end card near section starts from the track's cue file)
- SFX: <moments and families>
- Voice: <off | on: voice, tone, pronunciation notes>

## Art direction
<The one bespoke move for the hook; which real pages/charts appear; anything to customize beyond the archetypes.>

## Post copy (draft)
<first line hook for the post, 2–3 lines of value, CTA, 3 hashtags>

## Clearance
<cleared / anonymized items / internal only>
```

## storyboard.json

The contract between the plan and the composition. `kit.py build` reads it; `voice.py` writes timing back into it.

```json
{
  "title": "AI adoption is outpacing the controls around it",
  "format": "portrait",
  "music": "minimal",
  "musicVolume": 0.3,
  "transition": "iris",
  "overlap": 0.85,
  "progress": false,
  "scenes": [
    {"id": "hook", "archetype": "hook", "duration": 4,
     "eyebrow": "Field notes · AI security", "headline": "AI moves fast. [Security has to see first.]"},
    {"id": "proof", "archetype": "stat", "duration": 4.6, "value": "71%",
     "label": "of employees used an AI tool that IT had not approved", "source": "Cato field notes, 2026",
     "sfx": [{"file": "interface/drop_001.ogg", "at": 0.4, "volume": 0.5}]},
    {"id": "end", "archetype": "end", "duration": 3.4,
     "line": "See what your AI traffic is doing", "cta": "Read the report", "url": "catonetworks.com"}
  ]
}
```

Top level:

| Field | Meaning | Default |
|---|---|---|
| `title` | video title (metadata, poster alt) | — |
| `format` | `portrait` · `square` · `vertical` · `landscape` | `portrait` |
| `music` | an original bed (`pulse` · `minimal` · `focus` · `cinematic` · `ambient` · `piano` · `lofi` · `mallets` · `uplift` · `deep`), a /brag bed (`vol-12` · `vol-11` · `vol-1` · `vol-9` · `vol-10`), `none`, or a path to your own audio file (see `audio.md`) | `vol-12` |
| `musicVolume` | bed level 0–0.5 (auto-lowered to 0.14 under narration) | 0.3 |
| `transition` | default scene transition: `iris` (the Ring) · `fade` · `push` · `wipe` · `cut` | `iris` |
| `overlap` | seconds each scene stays under the next one's transition | 0.85 |
| `progress` | thin Highlight Green progress bar along the bottom | false |
| `pronunciations` | `{ "written": "spoken" }` for narration only | — |

Per scene: `id` (lowercase, unique), `archetype`, `duration` (seconds of its own time; starts are the running sum),
optional `transition`, `bg` (`pine` · `forest` · `grass` · `green` · `cato` · `dark` · `white` · `pale`), `ring`
(`concentric` · `open` · `double` · `disc`), `say` (narration line or list, used only with `--voice`), `sfx` (list of
`{file, at, volume}`; each slot is sized to the sound's real length), `note`,
plus the archetype's copy fields from [scene-archetypes.md](scene-archetypes.md).

Media paths (`image`, `photo`) may point into `source/` (for example `"source/pages/p-02.png"`); `build` copies them
into the composition.

## Series (`--count N`)

Plan N distinct angles from the same document (for example: the headline finding, the "what to do" list, the customer
quote). Each video gets its own folder, plan and storyboard; share the look so the series feels like one set, and use
related beds (the same bed, or `compose_music.py --seed` variations of one style) so the music feels like one family.
Vary the hook formula across the series.
