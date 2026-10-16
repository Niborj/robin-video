# The Cato brand in social video

Sources: the Cato Brand Hub tokens (`assets/brand/cato-brand.json`, retrieved 15 October 2026) and the Cato Visual
Style R101 deck (August 2026): brand platform, color, typography, the Ring, data and illustration style, photography,
social and presentation examples, tone of voice. The hub stays canonical; when it changes, update `cato-brand.json`,
`assets/kit/cato.css` and this file together.

## Platform in one breath

Brand promise: **Effortless command over network security.** What customers should remember: **Visibility. Context.
Control.** Personality: calmly brilliant, deeply secure, decisive by design. Expression: commanding, intelligent,
adaptive, human. In video that means: the important thing is revealed clearly, ideas visibly connect, and every piece
resolves into a calm, confident takeaway.

Design checklist (from R101), applied to every video before delivery:
- **Reveal:** Is the message immediately clear? Is there a clear hierarchy that reveals what matters most?
- **Connect:** Do the elements tell one cohesive story? Is it clear how the information relates and why it matters?
  Do the visuals add meaning rather than decoration?
- **Resolve:** Does it feel structured, intentional and precise? Does it guide toward a clear takeaway or action?
  Does it feel confident and unmistakably Cato?

## Color

| Role | Colors |
|---|---|
| Primary | Cato Green `#128461`, Highlight Green `#00FFCC`, White, Black (Cato Grey `#7D7D7D` / Medium Grey `#646464`) |
| Greens | Moss `#006F53`, Grass `#005543`, Forest `#003E34`, Dark Pine `#002C28` |
| Secondary (support only) | Coral `#FF3749`, Sunflower `#FFC820`, Light Moss `#7BCF91`, Sky `#00D8E0`, Plum `#561E9B`, Fuchsia `#BF00CC` |
| Neutrals | White, Pale Grey `#F0F0F0`, Light Grey `#C8C8C8`, Grey `#969696`, Medium Grey `#646464`, Dark Grey `#464646`, Black |
| Gradients (125°) | Green `#128461 → #00392F`; Dark `#474747 → #000000` |
| Solid backgrounds | `#128461`, `#006F53`, `#005543`, `#000000` (plus Forest and Dark Pine in the social examples) |

Rules in video:
- Greens lead. Backgrounds: Dark Pine, Forest, Grass, Cato Green, the green gradient; the dark gradient for data
  scenes; White or Pale Grey for quote cards and documents.
- **Highlight Green is for emphasis on dark surfaces**: key words, key numbers, rings, focus frames, the CTA pill.
  Use it selectively (one highlight per headline). It is never small text on white (1.3:1).
- On light backgrounds, emphasis is Cato Green (large type) or Moss (small text).
- Secondary colors only carry meaning (Coral for a threat or error, Sunflower for caution), never decoration, never
  competing with the greens.
- Alpha variants of palette colors are fine (`rgba(18, 132, 97, 0.14)`). Everything else is off-brand and the brand
  gate rejects it. A deliberate exception (a partner logo color) carries a `brand-ok` comment on its line.

## Typography

- **Archivo Medium** for the primary message: hooks, headlines, stats, side titles.
- **Inter Bold** for supporting hierarchy: eyebrows (uppercase, 0.12em tracking), labels, quotes, CTA.
- **Inter Regular** for body and leads.
- Sentence case for headlines. No shouting capitals in copy (eyebrows are uppercased by CSS).
- Fonts ship locally in the kit (Archivo under the SIL OFL). Do not substitute; HyperFrames' generic "banned fonts"
  advice does not apply because these are the brand typefaces.

## The Ring

The flat 2D Ring family is Cato's foundational graphic: **solid disc** (boldest focal point), **open ring** (the
foundational form: connection, continuity), **double ring** (inner ring the customer's network, outer ring Cato's
protection), **concentric rings** (movement, energy, scale; each ring a pillar). The kit draws them with the official
proportions (`data-ring="disc|open|double|concentric"`).

- Use it as a super-graphic backdrop (large, cropped, tone-on-tone), a frame for imagery or photography, a focal point,
  a progress ring, bullets and diagram nodes, and as the transition (the iris).
- **Flat 2D only.** The dimensional 3D ring is retired: no bevels, radial-gradient rings, perspective, glow or spin.
- Restraint: one or two ring forms per scene.
- Most recognizable in Cato Green; tone-on-tone on green and pine backgrounds.

## Logo

- Official files only (`assets/cato/logos/`, SHA-256 verified by `kit.py` and the brand gate): white on dark, green and
  imagery; color on white and light neutrals; black only when color is unavailable.
- Never redraw, recolor, stretch, rotate, separate, filter, fade below full strength, or animate the logo's parts.
  A simple fade or settle of the whole mark is fine.
- Placement: small in the top-left corner of each scene (as in Cato's social posts) and as the centered lockup in the
  end card. Clear space around it; never on busy imagery without a solid field.
- Partner co-branding (`CATO / Partner`) only with the partner's official logo and approval; keep the slash lockup
  from the customer-story examples.

## Icons, data and illustration

- Outline icons are the standard (24 px grid, 2 px round stroke); a solid icon only to give one idea more weight.
- Data: emphasize key numbers in larger, higher-contrast containers; keep container radius, padding and spacing uniform.
- Isometric illustration only for systems and relationships, never as the default.
- Icons are conceptual: not product marks or evidence of a feature.

## Imagery

Authentic, human, contemporary; selective focus and a clear focal point; perspective that suggests clarity; abstract
movement (connectivity, light, data) instead of cyber clichés. Industry imagery may be framed in the Ring.
**Never:** hooded hackers, padlocks, binary rain, glowing shields, skulls, red alert screens, stock handshakes.
Do not generate imagery of real people. Use photos only when the user provides cleared images.

## Voice

Clear, confident and human: clarity without simplification, intelligence without ego, confidence without alarm,
authority without corporate stiffness.

| Principle | On screen | Instead of |
|---|---|---|
| Clear, not complicated | "One policy, every path." | "A unified, holistic, end-to-end policy paradigm." |
| Calmly confident | "Stay ahead without chasing every threat." | "Hackers are coming for you!" |
| Smart and decisive | "See every AI app. Decide. Enforce." | "There are several approaches you might consider." |
| Human and conversational | "You can't secure what you can't see." | "Visibility enables security outcomes." |

Standards: U.S. English, The Chicago Manual of Style, Merriam-Webster; Cato conventions first. Banned in copy (the gate
flags them): alarm words (catastrophic, devastating, nightmare, terrifying, panic, doom, lurking, cripple…), hype
(game-changer, revolutionary, best-in-class, world-class, cutting-edge, next-gen, synergy, unleash, supercharge,
"excited to announce"…), exclamation marks, "click here", UK spellings.

## Product names

Use approved names: Cato SASE Platform (not "Cato SASE Cloud Platform" or bare "Cato SASE" for the platform), Cato SSE
360, Cato Socket, Cato Client (not ZTNA/SDP client), Cato XDR, Cato Network Stories for XDR, Cato FWaaS, Cato PoPs,
Cato SWG, Cato IPS, Cato NGAM, Cato DNS Security, Cato RBI, Cato CASB, Cato DLP, Cato Management Application (CMA), Cato
Endpoint Protection (EPP), Cato vSocket, Cato Single Pass Cloud Engine (SPACE), Cloud Interconnect (not Cross Connect),
Cato Edge SD-WAN, Cato DEM, Cato IoT/OT Security, Cato Safe TLSi. Expand an acronym the first time it appears on screen
unless the audience certainly knows it (SASE, AI). Validate new or changed names with Product Marketing before external
use.

## Brand gate (scripts/brand_check.py)

```bash
python3 <skill-dir>/scripts/brand_check.py <out>/composition [--copy <out>/post.md] [--strict]
```

| Rule | Checks | Fix |
|---|---|---|
| B-COLOR | every hex/rgb color is a palette color (alpha ok) | use tokens; `brand-ok` only for approved exceptions |
| B-FONT | font-family starts with Archivo/Inter/var(--display/--body) | use the type classes |
| B-LOGO | official, unmodified logo files; not stretched/filtered; present (and in the last scene) | restore files, set width only |
| B-PLACEHOLDER | TODO/lorem/brackets left in copy | finish the copy |
| B-NAME, B-NAME-SASE | product names marked incorrect | use approved names |
| B-NAME-UNKNOWN | a "Cato …" name that is not on the approved list (warning) | confirm with the user / Product Marketing |
| B-ALARM, B-HYPE, B-EXCLAIM, B-CAPS, B-SPELL-US, B-LINK | voice rules | rewrite calmly and plainly |
| B-DENSITY | headline > 14 words, any block > 32 words | split into beats |
| B-PRIVACY | emails, internal hosts, phone numbers | remove or anonymize |
| B-MOTION | 3D transforms, bounce/elastic eases | planar, calm eases |
| B-NETWORK | remote assets at render time | copy into composition/assets |
| B-LENGTH | < 6 s or > 90 s | cut, or split into a series |

Errors block delivery. Warnings need a reason in `plan.md` if you keep them.
