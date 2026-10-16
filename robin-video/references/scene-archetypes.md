# Scene archetypes and the Cato motion kit

`kit.py build` turns each storyboard scene into `composition/compositions/<id>.html`: a HyperFrames sub-composition
with the Cato kit, laid out for the format, animated by `CatoMotion.scene()`. The archetypes are modeled on Cato's own
social and presentation examples (Visual Style R101): solid-green and gradient backgrounds with ring super-graphics,
dark-mode data cards, the human-era/agentic-era comparison, customer quote cards.

`[Brackets]` in any copy field mark Highlight Green key words. Missing copy renders as `TODO`, which the brand gate
rejects, so nothing half-written ships.

## Catalog

### `hook` — the opener (Reveal)
Ring super-graphic, corner logo, eyebrow, hero headline anchored low (like Cato's "Ready. Set. Defend." post).
Fields: `headline` (3–9 words; `|` forces a line break), `eyebrow`, `sub` (one short line), `ring`.
The headline is fitted: line breaks and size are chosen for the longest line (sentence per line when possible; a
line never ends one sentence and starts the next when a sentence-aligned layout is nearly as large).
Motion: as the opener (a cut), ring, logo and eyebrow are there from frame 1 and drift; the words rise masked one by
one straight away; the highlight turns Highlight Green. As a later scene, the ring and logo enter with the iris.
```json
{"id": "hook", "archetype": "hook", "duration": 4, "eyebrow": "Threat research", "headline": "AI changed the attack surface. [Security has to change with it.]"}
```

### `statement` — one big line (Reveal / Resolve)
Centered or bottom-anchored headline with optional sub; for "so what", myths, takeaways, transitions in the argument.
Fields: `headline` (fitted like the hook; `|` forces a break), `sub`, `eyebrow`, `align` (`center` | `bottom`), `ring`.

### `stat` — one number that matters (Connect)
The number counts up inside a ring; for percentages the Highlight Green ring draws to the same value over a faint track.
Fields: `value` ("71%", "30,254", "$5.02M", "3x", "1 in 3"), `label` (≤ 14 words), `source`, `eyebrow`.
Font size adapts to the number's length.

### `cards` — 2–4 numbers side by side (Connect)
Dark-mode containers (thin outlines, big Highlight Green numbers, white labels), from Cato's dark presentation style.
Stacked in portrait/vertical and in square with 2 cards, a 2-column grid in square with 3–4, in a row in landscape.
Numbers count up as each card lands.
Fields: `headline`, `eyebrow`, `cards: [{value, label, note, accent}]`.

### `compare` — before / after (Connect)
Light panel ("before", Pale Grey) against a deep green panel ("after", Highlight Green rows), with outline icons; rows
reveal in pairs so the contrast reads line by line. Stacked in portrait/vertical, side by side in square/landscape
(in square the two sides share row tracks, so a title or row that wraps on one side keeps both sides level).
Fields: `headline`, `before: {title, rows: [{icon, text}]}`, `after: {...}` (2–4 rows each).

### `list` — 3–5 points (Connect / Resolve)
Open-ring bullets that draw in sequence along a rail; each item rises as its ring closes.
Fields: `headline`, `eyebrow`, `items` (≤ 6 words each), `step` (seconds per item, default 0.55).

### `quote` — a real voice (Connect)
White card style from Cato's customer stories: Cato Green quote mark, Inter Bold quote, uppercase name, role; optional
headshot framed in the Ring. Fields: `quote` (≤ 30 words), `name`, `role`, `photo` (path; cleared images only).

### `doc` — show the source (Connect)
A window onto a real page: the page fills the card width, tall pages are cropped around the focus area, a slow push
settles on it, a Highlight Green frame lands on the key region and a tag names the takeaway.
Fields: `image` (e.g. `source/pages/p-02.png`), `focus: [x, y, w, h]` as fractions of the page (look at the page to set
it), `tag` (≤ 6 words), `headline`, `zoom` (default 1.08), `crop: [x, y, w, h]` (optional).
Framing is automatic: `build` crops the page to its content box measured at ingest (no empty margins), and when the
result would be a short strip (a dashboard row, a wide slide) it zooms in around the `focus` so the key numbers stay
legible on a phone. When the page is taller than the window, the window becomes a band around the focus whose edges
sit in blank space between lines (measured at ingest), from the first frame to the end of the push, with room for
the tag above or below the focus, wherever that slot is blank on the page. Square uses the full width. The window
keeps its proportions and scales down when the stage is shorter (burned-in captions), so it never slices text.
Set `crop` to override, or `"crop": [0, 0, 1, 1]` to show the whole page.

### `flow` — how it connects (Connect)
Open-ring nodes with outline icons, joined by paths that draw in order; mark the Cato node `hub: true` for a double ring
(inner ring: the customer's network, outer ring: Cato's protection). Up to 3 nodes in portrait/square/vertical (stacked
in a column with labels beside the rings in vertical), 5 in landscape. Fields: `headline`, `eyebrow`,
`nodes: [{label, icon, hub}]`.

### `end` — resolve and act (Resolve)
Centered logo lockup, one line, the CTA pill, the URL, over the green gradient. Hold ≥ 2.5 s.
Fields: `line`, `cta` (verb first: "Read the report", "Register now"), `url`.

### `custom` — your own scene
Brand chrome (background, ring, logo) and a headline, for a bespoke visual you build by hand in the scene file.

## Icons

`python3 <skill-dir>/scripts/kit.py icons` lists the Cato outline icons (24 px grid, 2 px stroke). Use them by name in
`compare` rows and `flow` nodes, or print inline SVG with `kit.py icon <name>`. Icons are conceptual: never use one as
a product mark or as evidence of a specific capability.

## Editing a generated scene

Scene files are yours once generated: `build` never overwrites them (it only re-syncs their timing attributes) unless
you pass `--force-scenes <id>` or `all`. Edit freely, keeping the contract:

- Everything lives inside `<template>`; style the scene root by `#root`; ids prefixed with the scene id.
- Animate `.cs-frame` and its children, never the `.clip` element itself.
- Colors from palette tokens (`var(--cato-green)`, `var(--highlight)`, `var(--pine)`, …); type via the classes below.
- Add bespoke tweens in the scene script **after** `CatoMotion.scene(tl, root)`, at local times (0 = scene start).
- Opt an element out of automatic entrance with `data-enter="none"` and animate it yourself; shift one with
  `data-delay="0.4"`; give it extra reading time with `data-hold="1"`.
- Use `fromTo` (not `from`) for entrances; no `Math.random`, clocks or network; no CSS `transform` on an element you
  also tween with x/y/scale.

## CSS classes (cato.css)

Layout: `.cs-safe` (+ `.is-bottom`, `.is-center`, `.is-center-x`, `.is-top`), `.measure`, `.gap-xs|s|m|l`.
Backgrounds: `.bg-pine`, `.bg-forest`, `.bg-grass`, `.bg-green` (gradient), `.bg-cato`, `.bg-dark` (gradient),
`.bg-white`, `.bg-pale`. Type: `.eyebrow`, `.headline` (+ `.is-hero`, `.is-h2`, `.is-h3`), `.lead`, `.body`, `.small`,
`.hl`, `.strong`. Data: `.stat`, `.stat-ring`, `.cards`/`.card`/`.card-value`/`.card-label`/`.card-note`. Others:
`.compare`, `.list`, `.quote-mark`, `.quote-text`, `.attrib-name`, `.attrib-role`, `.ring-photo`, `.doc-*`, `.flow`,
`.node`, `.cta`, `.url`, `.logo`, `.logo-inline`, `.progress`, `.captions`.
Rings: `<svg class="ring ring--super" data-ring="open|double|concentric|disc|thin|track">` (geometry is filled in by
`CatoMotion.rings()` from the official Ring family proportions). Colors: `.ring--accent`, `.ring--green`, `.ring--white`.

## CatoMotion API (cato-motion.js)

All functions take the timeline, a target and a start time, and return the time the elements are settled.

| Function | Use |
|---|---|
| `scene(tl, root, o)` | the default: transition in, `enter()` everything, clear copy in the tail |
| `enter(tl, scene, at)` | reading-order choreography of every brand element in a scene |
| `rise(tl, el, at, {dur, stagger})` | masked word-by-word rise (headlines) |
| `highlight(tl, el, at)` | `.hl` words turn Highlight Green |
| `fadeUp`, `fadeIn`, `settleIn` | small entrances (y offset, fade, scale-settle) |
| `typeOn(tl, el, at, {cps})` | type a line character by character |
| `countUp(tl, el, at, {to, dur, decimals})` | count a `[data-count]` number up |
| `ringDraw(tl, svg, at, {to, dur})` | draw ring strokes (a progress ring with `to`) |
| `ringIn(tl, svg, at, {hold})` | bring a super-graphic in and let it drift |
| `drawPath(tl, path, at, {dur})` | draw connector paths |
| `kenBurns(tl, img, at, dur, {to, origin})` | slow push on an image or page |
| `focus(tl, el, at)` | land a focus frame |
| `iris`, `fade`, `push`, `wipe` | scene transitions (iris is the Ring opening, edged in Highlight Green) |
| `captions(tl, el, cues)` | burned-in captions with the spoken word highlighted |
| `EASE` | `in` power3.out · `strong` expo.out · `move` power2.inOut · `soft` sine.inOut |

## Bespoke motion recipes

```js
// The number and the ring land together on a strong music cue at 1.8 s (local time)
tl.fromTo(root.querySelector(".stat"), { scale: 0.96 }, { scale: 1, duration: 0.5, ease: CatoMotion.EASE.strong }, 1.8);

// Contrast pair: the first sentence dims as the highlighted turn lands
const [first, turn] = root.querySelectorAll(".headline .line");
tl.to(first, { opacity: 0.45, duration: 0.5, ease: "power2.inOut" }, 1.6);

// A real page sits blurred behind the hook, then sharpens
tl.fromTo(root.querySelector(".hook-page"), { filter: "blur(18px)", opacity: 0 }, { filter: "blur(0px)", opacity: 0.25, duration: 1.2 }, 0.2);

// Draw a custom connector between two elements you placed by hand
CatoMotion.drawPath(tl, root.querySelector("#flow-link-a"), 1.1, { dur: 0.7 });
```

For anything beyond these (camera moves, masks, morphs, data charts), load `hyperframes-animation` and
`hyperframes-keyframes` and follow their rules; keep the Cato motion character: calm, decisive, no bounce.
