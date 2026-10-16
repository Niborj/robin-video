# Step 1 · Ingest and understand

## Run the ingester

Create the output folder `robin-video-output/<slug>/` (slug = the main file's name, lowercased with hyphens, as
`ingest.py` prints it; add a timestamp if the folder exists), then ingest every source file into its `source/` folder:

```bash
uv run --project <skill-dir>/scripts python <skill-dir>/scripts/ingest.py "<file1>" ["<file2>" …] --out <out>/source
```

`uv` provisions PyMuPDF, python-pptx and python-docx on first run. Useful flags: `--max-pages 40` (page renders per
document), `--page-width 1600`, `--min-image 160` (skip tiny embedded images).

| Input | What you get |
|---|---|
| PDF | text in reading order with heading levels, bullets, every page rendered to `pages/p-NN.png`, embedded images, visual-page flags |
| PowerPoint (.pptx) | slide titles, body bullets, speaker notes, tables, **native chart data** (categories and series values), pictures; slide renders only if LibreOffice is installed |
| Word (.docx) | headings, paragraphs, bullets, quotes, tables (layout tables are read as content), text boxes, images |
| Text / Markdown / HTML | headings, paragraphs, bullets, quotes, tables |
| CSV | the table (an animated stat or chart source) |
| Images (PNG, JPG, SVG…) | copied to `images/` as assets (logos of partners, headshots, screenshots) |
| .ppt, .doc, .key, .pages, .odp, .rtf | converted with LibreOffice when installed; otherwise ask the user for a PDF or .pptx/.docx export |

For a deck without slide renders, ask whether the user can also export it to PDF (ingest both: the PPTX gives clean
text and chart data, the PDF gives page images). Do not block on it: slides are usually better rebuilt in motion anyway.

## Read the digest

Read `source/content.md` in full (in parts if long). It contains, in order:

- **Clearance flags**: confidentiality labels (Confidential, Internal use only, DRAFT… where they act as labels, headers
  or footers), internal-audience signals (employees, bootcamp, enablement, QBR…), emails, internal hosts. Handle
  before anything else (below).
- **Candidate stats**: figures stated in sentences, with location tags like `[p3]` or `[slide 4]`. Table fragments are
  listed separately as weak; read the page render before using one.
- **Candidate quotes** with attribution. Unattributed quoted passages are only counted (they are usually examples or
  prompts, not quotes) and stay in the full text and `content.json`.
- **Charts** with their native data (animate these, never screenshot a chart you can rebuild).
- **Page renders** and **extracted images**, with "visual" flags for chart- and image-heavy pages, each page's content
  area (used to crop empty margins), and small square images flagged as likely stock icons (prefer Cato's icons).
- **Full text** in reading order with locations.

Look at the page renders that matter (cover, the chart page, the key diagram) with the Read tool: you need to know what
they look like to use them in a `doc` scene, and to set the focus box.

## Clearance gate

Social posts are public. If the digest shows clearance flags, or the content is plainly internal (assessments with
customer data, internal proposals, roadmaps, pricing, unreleased features, anything marked Confidential/Internal/Draft):

1. Tell the user, in one short message, what you found (quote the marker and where).
2. Ask whether it is cleared for public social media, and whether to anonymize (for example "a global retailer").
3. Continue once they confirm. If they say it is for internal social channels only, note that in `plan.md` and keep
   going, still without personal data.

Always, cleared or not: no personal data (names of private individuals, emails, phone numbers, user names), no
internal hostnames, API URLs or account IDs, no customer names unless the source is a published case study, no claims
that the document marks as forward-looking or unapproved. Replace with neutral stand-ins and say so in the plan.

## The ingest rubric

Answer all ten in `plan.md` before planning scenes.

```
1. What is this document?            One sentence: type, author/owner, audience.
2. Who is the social audience?       e.g. CISOs and network leaders on LinkedIn; partners; candidates.
3. What is the one idea?             The single thing a viewer should remember. One sentence, no "and".
4. Why should they care?             The outcome or risk in the viewer's language (not the document's headings).
5. What is the strongest proof?      The best number, chart, quote or before/after, with its location.
6. What can we show from the source? Pages, charts (native data), images, diagrams, quotes worth putting on screen.
7. What story type fits?             threat-research | data-story | executive-pov | product-launch | customer-story |
                                     event | explainer | employer-brand (or the user's --story).
8. What is the call to action?       Read the report, register, visit, talk to us; plus the URL if the document has one.
9. Which Cato names and terms appear? Check them against the approved product names (cato-brand.md).
10. Clearance:                       cleared / anonymize X / internal only. List anything that must not appear.
```

## Claims table

Every number, quote and factual claim that will appear on screen or in the post goes into a table in `plan.md`:

| Claim on screen | Exact source wording | Location | Notes |
|---|---|---|---|
| 71% of employees used an unapproved AI tool | "71% of employees used at least one AI tool that IT had not approved" | [p2] | sample data: label it |

Rules: never round in a way that changes meaning ("71%" may become "7 in 10", not "most"); keep the qualifier when it
matters ("in this sample", "in 30 days"); attribute third-party data ("Source: Gartner, 2026") on screen in `.small`.
