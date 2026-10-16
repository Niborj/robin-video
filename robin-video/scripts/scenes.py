"""Scene archetypes for Robin-Video: storyboard copy in, Cato-branded HyperFrames sub-composition out.

Each archetype is a function (scene, ctx) -> inner HTML for the scene's .cs-frame. `wrap` turns that into a complete
sub-composition file (bare <template>, styles and scripts inside, background on a clip layer, one paused timeline).
Copy markup: [square brackets] mark the key words shown in Highlight Green. Missing copy renders as TODO so the
brand gate catches it.
"""
from __future__ import annotations

import html
import json
import math
import re
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / 'assets'
ICONS = json.loads((ASSETS / 'brand/icons.json').read_text(encoding='utf-8'))
LOGO_WHITE = 'assets/cato/logos/cato_logo_rgb_white_art_101.svg'
LOGO_COLOR = 'assets/cato/logos/cato_logo_rgb_color_art_101.svg'
LIGHT_BGS = {'white', 'pale'}
DEFAULT_BG = {'hook': 'pine', 'statement': 'green', 'stat': 'green', 'cards': 'dark', 'compare': 'pine', 'list': 'forest',
              'quote': 'white', 'doc': 'pine', 'flow': 'green', 'end': 'green', 'custom': 'pine'}
ARCHETYPES = ('hook', 'statement', 'stat', 'cards', 'compare', 'list', 'quote', 'doc', 'flow', 'end', 'custom')

# Ring super-graphic placements (size and offsets as fractions of the frame width/height). Rotated per scene so
# consecutive scenes never repeat the same backdrop.
PLACEMENTS = [
    ('concentric', 1.40, {'left': -0.36, 'top': -0.42}),
    ('open', 1.10, {'right': -0.42, 'bottom': -0.30}),
    ('double', 0.95, {'right': -0.45, 'top': -0.30}),
    ('concentric', 1.25, {'left': -0.55, 'bottom': -0.40}),
    ('open', 0.85, {'left': -0.30, 'top': -0.28}),
]


def esc(text):
    return html.escape(str(text), quote=True)


def rich(text, fallback='TODO'):
    """Escape copy and turn [key words] into Highlight Green spans."""
    if not text:
        return esc(fallback)
    out = esc(text)
    return re.sub(r'\[([^\]]+)\]', r'<span class="hl">\1</span>', out)


def plain(text):
    return re.sub(r'[\[\]]', '', str(text or ''))


def icon(name, cls='icon'):
    body = ICONS.get(name or '', ICONS['sparkles'])
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>')


def ring_super(ctx, form=None, k=None):
    w, h = ctx['w'], ctx['h']
    pf, size, pos = PLACEMENTS[(ctx['index'] if k is None else k) % len(PLACEMENTS)]
    form = form or pf
    side = round(max(w, h) * size * (0.8 if w > h else 1))
    css = '; '.join(f'{k}: {round(v * (w if k in ("left", "right") else h))}px' for k, v in pos.items())
    return f'<svg class="ring ring--super" data-ring="{form}" data-layout-ignore style="width: {side}px; height: {side}px; {css}"></svg>'


def logo(ctx):
    src = LOGO_COLOR if ctx['bg'] in LIGHT_BGS else LOGO_WHITE
    return f'<img class="logo" src="{src}" alt="Cato Networks" />'


def eyebrow(s):
    return f'<p class="eyebrow">{rich(s["eyebrow"])}</p>\n<div class="gap-s"></div>' if s.get('eyebrow') else ''


def size_class(text, big='is-hero', mid='', small='is-h2'):
    n = len(plain(text).split())
    return big if n <= 6 else (mid if n <= 10 else small)


CHAR_EM = 0.51   # average advance of Archivo Medium per character (spaces included), in em, with margin; measured ~0.48


def _tokens(text):
    """Words with their highlight flag; [brackets] may span several words."""
    out, hl = [], False
    for raw in str(text).split():
        start_hl = hl or raw.startswith('[')
        word = raw.replace('[', '').replace(']', '')
        if raw.startswith('['):
            hl = True
        out.append((word, start_hl or hl))
        if raw.endswith(']') or (']' in raw):
            hl = False
    return [(w, h) for w, h in out if w]


def _render_line(tokens):
    parts, run = [], []
    def flush():
        if run:
            parts.append('<span class="hl">' + ' '.join(esc(w) for w in run) + '</span>')
            run.clear()
    for w, h in tokens:
        if h:
            run.append(w)
        else:
            flush()
            parts.append(esc(w))
    flush()
    return ' '.join(parts)


def _balanced(tokens, n):
    """Split tokens into n lines minimizing the longest line (character count)."""
    lens = [len(w) for w, _ in tokens]
    best = None
    def rec(i, k, acc, longest):
        nonlocal best
        if k == 1:
            line = sum(lens[i:]) + max(0, len(lens) - i - 1)
            m = max(longest, line)
            if best is None or m < best[0]:
                best = (m, acc + [tokens[i:]])
            return
        for j in range(i + 1, len(tokens) - k + 2):
            line = sum(lens[i:j]) + (j - i - 1)
            if best is not None and max(longest, line) >= best[0]:
                continue
            rec(j, k - 1, acc + [tokens[i:j]], max(longest, line))
    if n >= len(tokens):
        return [[t] for t in tokens]
    rec(0, n, [], 0)
    return best[1]


def _mixes_sentences(lines):
    """True when a sentence ends inside a line (not at its end)."""
    return any(re.search(r'[.!?:;]$', w) for line in lines for w, _ in line[:-1])


def _sentence_lines(sentences, max_lines):
    """Each sentence on its own line(s): spread up to max_lines over the sentences so the longest line is shortest."""
    longest = lambda ls: max(sum(len(w) for w, _ in l) + len(l) - 1 for l in ls)
    best = None
    def rec(i, left, acc):
        nonlocal best
        if i == len(sentences):
            if best is None or longest(acc) < longest(best):
                best = acc
            return
        for k in range(1, min(left - (len(sentences) - i - 1), len(sentences[i])) + 1):
            rec(i + 1, left - k, acc + _balanced(sentences[i], k))
    if len(sentences) <= max_lines:
        rec(0, max_lines, [])
    return best


def fit_headline(text, width, max_px, min_px=64, max_lines=3):
    """Pick line breaks and a font size so a headline is as large as it can be without awkward wraps.
    A '|' in the copy forces a break. Otherwise one sentence per line wins when it stays reasonably large; else the
    fewest balanced lines (up to max_lines) unless one more line buys a clearly larger size. Returns (html, px)."""
    text = str(text or 'TODO')
    size_for = lambda lines: min(max_px, int(width / (CHAR_EM * max(1, max(sum(len(w) for w, _ in l) + len(l) - 1 for l in lines)))))
    if '|' in text:
        lines = [_tokens(part) for part in text.split('|') if part.strip()]
    else:
        toks = _tokens(text)
        sentences = [part for part in re.split(r'(?<=[.!?:;])\s+', text.strip()) if part]
        lines = None
        if 1 < len(sentences) <= max_lines:
            cand = [_tokens(part) for part in sentences]
            if size_for(cand) >= 0.6 * max_px:
                lines = cand
        if lines is None:
            lines = _balanced(toks, 1)
            for n in range(2, min(max_lines, len(toks)) + 1):
                more = _balanced(toks, n)
                if size_for(more) > size_for(lines) / 0.78:   # another line only for a clearly bigger size
                    lines = more
            if len(sentences) > 1 and _mixes_sentences(lines):
                # A line that ends one sentence and starts the next reads badly: break at every sentence end instead
                # (one extra line allowed) when that keeps the size within 10%.
                kept = _sentence_lines([_tokens(part) for part in sentences], min(max_lines + 1, 4))
                if kept and size_for(kept) >= 0.9 * size_for(lines):
                    lines = kept
    size = max(min_px, size_for(lines))
    return ''.join(f'<span class="line">{_render_line(l)}</span>' for l in lines), size


HERO_PX = {'portrait': 148, 'square': 136, 'vertical': 156, 'landscape': 148}   # hook ceiling; square matches --t-hero


def text_width(ctx):
    return min(ctx['w'] - 2 * ctx['pad_x'], 1250)


def a_hook(s, ctx):
    lines, px = fit_headline(s.get('headline'), text_width(ctx), HERO_PX[ctx['fmt']])
    sub = f'<div class="gap-m"></div>\n<p class="lead measure">{rich(s["sub"])}</p>' if s.get('sub') else ''
    return f'''{ring_super(ctx, s.get('ring'))}
{logo(ctx)}
<div class="cs-safe is-bottom">
  {eyebrow(s)}
  <h1 class="headline is-hero is-fit" style="font-size: {px}px">{lines}</h1>
  {sub}
</div>'''


def a_statement(s, ctx):
    lines, px = fit_headline(s.get('headline'), text_width(ctx), 132, max_lines=4)
    sub = f'<div class="gap-m"></div>\n<p class="lead measure">{rich(s["sub"])}</p>' if s.get('sub') else ''
    align = 'is-center' if s.get('align') != 'bottom' else 'is-bottom'
    return f'''{ring_super(ctx, s.get('ring'))}
{logo(ctx)}
<div class="cs-safe {align}">
  {eyebrow(s)}
  <h2 class="headline is-hero is-fit" style="font-size: {px}px">{lines}</h2>
  {sub}
</div>'''


def split_value(value):
    """'$5.02M' -> ('$', '5.02', 'M'); '71%' -> ('', '71', '%'); '3x' -> ('', '3', '×')."""
    m = re.match(r'^\s*([^\d\-]*?)(-?[\d,]*\.?\d+)\s*(.*)$', str(value))
    if not m:
        return '', str(value), ''
    pre, number, post = m.groups()
    if post.lower() == 'x':
        post = '×'
    return pre, number, post


def stat_markup(value, cls='stat', size=None):
    pre, number, post = split_value(value)
    style = f' style="--fs: {size}px"' if size else ''   # cato.css scales --fs per format (stat ring, cards)
    pre_html = f'<span class="unit">{esc(pre)}</span>' if pre else ''
    post_html = f'<span class="unit">{esc(post)}</span>' if post else ''
    return f'<p class="{cls}"{style}>{pre_html}<span data-count>{esc(number)}</span>{post_html}</p>'


def a_stat(s, ctx):
    value = s.get('value') or 'TODO'
    pre, number, post = split_value(value)
    digits = len(re.sub(r'\D', '', number)) + len(pre) + len(post)
    size = 260 if digits <= 3 else 210 if digits <= 4 else 170 if digits <= 5 else 140 if digits <= 6 else 115
    to = ''
    try:
        if post.strip() == '%':
            to = f' data-to="{max(0.02, min(1, float(number.replace(",", "")) / 100)):.3f}"'
    except ValueError:
        pass
    label = f'<div class="gap-m"></div>\n  <p class="lead measure">{rich(s.get("label"))}</p>'
    source = f'<div class="gap-s"></div>\n  <p class="small">{rich(s["source"])}</p>' if s.get('source') else ''
    track_color = 'rgba(255, 255, 255, 0.16)' if ctx['bg'] not in LIGHT_BGS else 'rgba(18, 132, 97, 0.14)'
    accent = 'ring--accent' if ctx['bg'] not in LIGHT_BGS else 'ring--green'
    return f'''{logo(ctx)}
<div class="cs-safe is-center is-center-x">
  {eyebrow(s)}
  <div class="stat-ring">
    <svg class="ring" data-ring="track" data-role="track" style="color: {track_color}"></svg>
    <svg class="ring {accent}" data-ring="track"{to}></svg>
    {stat_markup(value, size=size)}
  </div>
  {label}
  {source}
</div>'''


def a_cards(s, ctx):
    cards = (s.get('cards') or [{'value': 'TODO', 'label': 'TODO'}])[:4]
    grid = ctx['fmt'] == 'square' and len(cards) >= 3
    column = ctx['fmt'] != 'landscape' and not grid
    value_size = 110 if grid else 130 if not column else (150 if len(cards) <= 2 else 120)
    items = []
    for c in cards:
        note = f'<p class="card-note">{rich(c["note"])}</p>' if c.get('note') else ''
        items.append(f'''    <div class="card{' is-accent' if c.get('accent') else ''}">
      <p class="card-label">{rich(c.get('label'))}</p>
      {stat_markup(c.get('value') or 'TODO', 'card-value', value_size)}
      {note}
    </div>''')
    head = f'<h2 class="headline is-h2 measure">{rich(s["headline"])}</h2>\n  <div class="gap-m"></div>' if s.get('headline') else ''
    return f'''{ring_super(ctx, s.get('ring'))}
{logo(ctx)}
<div class="cs-safe is-bottom">
  {eyebrow(s)}
  {head}
  <div class="cards{' is-column' if column else ''}{' is-grid' if grid else ''}">
{chr(10).join(items)}
  </div>
</div>'''


def a_compare(s, ctx):
    def side(d, cls, fallback):
        d = d or {}
        rows = d.get('rows') or [{'text': 'TODO'}]
        r = '\n'.join(f'      <div class="row">{icon(x.get("icon") if isinstance(x, dict) else None)}<span>{rich(x.get("text") if isinstance(x, dict) else x)}</span></div>' for x in rows[:4])
        return f'''    <div class="side {cls}">
      <p class="side-title">{rich(d.get('title') or fallback)}</p>
{r}
    </div>'''
    head = f'<h2 class="headline is-h2 measure">{rich(s["headline"])}</h2>\n  <div class="gap-m"></div>' if s.get('headline') else ''
    rows = 1 + max(min(4, len((s.get(k) or {}).get('rows') or [1])) for k in ('before', 'after'))
    return f'''{logo(ctx)}
<div class="cs-safe is-bottom">
  {eyebrow(s)}
  {head}
  <div class="compare" style="--rows: {rows}">
{side(s.get('before'), 'is-before', 'Before')}
{side(s.get('after'), 'is-after', 'With Cato')}
  </div>
</div>'''


def a_list(s, ctx):
    items = s.get('items') or ['TODO']
    rows = '\n'.join(f'    <div class="item"><svg class="ring" data-ring="open"></svg><span>{rich(i)}</span></div>' for i in items[:5])
    return f'''{ring_super(ctx, s.get('ring') or 'double')}
{logo(ctx)}
<div class="cs-safe is-center">
  {eyebrow(s)}
  <h2 class="headline is-h2 measure">{rich(s.get('headline'))}</h2>
  <div class="gap-l"></div>
  <div class="list"{f' data-step="{s["step"]}"' if s.get('step') else ''}>
    <div class="rail"></div>
{rows}
  </div>
</div>'''


def a_quote(s, ctx):
    photo = ''
    if s.get('photo'):
        d = 300
        photo = (f'<div class="ring-photo" style="width: {d}px; height: {d}px; right: var(--pad-x); bottom: var(--pad-bottom)">'
                 f'<img src="{esc(s["photo"])}" alt="{esc(plain(s.get("name", "")))}" /></div>')
    role = f'<p class="attrib-role">{rich(s["role"])}</p>' if s.get('role') else ''
    return f'''{ring_super(ctx, s.get('ring') or 'open')}
{logo(ctx)}
<div class="cs-safe is-center">
  <p class="quote-mark">“</p>
  <p class="quote-text measure">{rich(s.get('quote'))}</p>
  <div class="gap-m"></div>
  <p class="attrib-name">{rich(s.get('name'))}</p>
  {role}
</div>
{photo}'''


def image_size(path):
    """(width, height) of a PNG, JPEG, GIF or WebP file using only the standard library; None if unknown."""
    import struct
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return struct.unpack('>II', data[16:24])
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return struct.unpack('<HH', data[6:10])
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        if data[12:16] == b'VP8X':
            return (int.from_bytes(data[24:27], 'little') + 1, int.from_bytes(data[27:30], 'little') + 1)
        if data[12:16] == b'VP8 ':
            w, h = struct.unpack('<HH', data[26:30]); return (w & 0x3fff, h & 0x3fff)
    if data[:2] == b'\xff\xd8':
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1; continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack('>HH', data[i + 5:i + 9]); return (w, h)
            i += 2 + struct.unpack('>H', data[i + 2:i + 4])[0]
    return None


# Safe area per format, mirroring cato.css (--pad-top, --pad-bottom, --logo-w): how tall a doc window can be.
SAFE = {'portrait': (88, 96, 210), 'square': (80, 84, 210), 'vertical': (250, 430, 230), 'landscape': (90, 96, 220)}


def stage_height(s, ctx):
    """Estimated height (px) left for the doc window under the corner logo, eyebrow and headline, without captions."""
    top, bottom, logo_w = SAFE[ctx['fmt']]
    h = ctx['h'] - top - bottom - (logo_w * 0.4 + 72)
    if s.get('eyebrow'):
        h -= 28 * 1.2 + 28
    if s.get('headline'):
        measure = 1250 if ctx['fmt'] == 'landscape' else min(900, ctx['w'] - 2 * ctx['pad_x'])
        h -= math.ceil(len(plain(s['headline'])) * 0.5 * 60 / measure) * 60 * 1.08 + 48
    return max(200, h)


def snap_window(cy, ch, need, m, gaps, origin=None, zoom=1.0):
    """The visible band (y, h, fits) in page fractions inside the content [cy, cy + ch] that contains `need` (the
    focus with its frame margin and tag slot), with both edges in blank bands so no line of text is sliced from the
    first frame to the end of the slow push (`zoom` around `origin` draws the edges toward the origin). Wider gaps
    are better edges (they separate sections, not lines); content edges count as the widest. Prefers bands at most m
    tall (fits); then the shortest band up to m / 0.75 (the window scales down to fit); None if neither exists."""
    lo, hi = cy, cy + ch
    o = (need[0] + need[1]) / 2 if origin is None else origin
    k = 1 / max(1.0, zoom)
    tops, bottoms = [], []
    for a, b in gaps:
        if not lo < (a + b) / 2 < hi:
            continue
        # Top edge t: at rest at or below a (the line above stays out); after the push at o - (o - t) * k, still
        # above b (the line below is not cut). Aim to end 20% of the gap above b.
        upper = min(o - (o - b) / k, need[0])
        if upper >= a:
            tops.append((min(max(o - (o - (b - 0.2 * (b - a))) / k, a), upper), b - a))
        # Bottom edge, mirrored: at rest at or above b, after the push still below a.
        lower = max(o + (a - o) / k, need[1])
        if lower <= b:
            bottoms.append((max(min(o + (a + 0.2 * (b - a) - o) / k, b), lower), b - a))
    edge = max([g for _, g in tops + bottoms] or [0.02])
    tops.append((lo, edge))
    bottoms.append((hi, edge))
    pairs = [(t, b, gt + gb) for t, gt in tops for b, gb in bottoms if t <= need[0] and b >= need[1]]
    fits = [p for p in pairs if p[1] - p[0] <= m + 1e-9]
    if fits:
        t, b, _ = max(fits, key=lambda p: (p[2], p[1] - p[0]))
    else:
        near = [p for p in pairs if p[1] - p[0] <= m / 0.75]
        if not near:
            return None
        t, b, _ = min(near, key=lambda p: (p[1] - p[0], -p[2]))
    return round(t, 4), round(b - t, 4), bool(fits)


def doc_frame(s, ctx):
    """How a page sits in the doc window: page size and window size in px (at the card's design width), the visible
    region in page fractions, and where the tag goes. The page fills the card width; content taller than the stage is
    cropped to a band around the focus (frame and tag included) whose edges fall in blank space (ingest measures the
    bands). The tag goes above or below the focus, wherever its slot is blank on the page. When no band fits the stage,
    a band up to a third taller is shown scaled down; past that, the band is centered on the focus."""
    size = ctx.get('img_size') or (1600, 2263)
    card_w = 1180 if ctx['fmt'] == 'landscape' else ctx['w'] - 2 * ctx['pad_x']
    explicit = s.get('crop') is not None
    cx, cy, cw, ch = ctx.get('crop') or s.get('crop') or [0, 0, 1, 1]   # frame the page's content, not its empty margins
    page_w = card_w / cw
    page_h = page_w * size[1] / size[0]
    f = s.get('focus') if s.get('focus') and len(s['focus']) == 4 else None
    if f and not explicit and page_h * ch < ctx['h'] * 0.42:
        # Wide, short content (a dashboard row, a slide) would render small: zoom the window in around the focus.
        zw = min(cw, max(f[2] + 0.08, cw / 2))
        cx = min(max(f[0] + f[2] / 2 - zw / 2, cx), cx + cw - zw)
        cw = zw
        page_w = card_w / cw
        page_h = page_w * size[1] / size[0]
    y, h, tag = cy, ch, 'auto'
    limit = stage_height(s, ctx)
    if not explicit and page_h * ch > limit:
        f0, f1 = (f[1], f[1] + f[3]) if f else (cy + ch * 0.3, cy + ch * 0.3)
        gaps = ctx.get('gaps') or []
        pad, slot = 24 / page_h, 72 / page_h          # frame margin (border and push-in), tag height plus spacing
        blank = lambda a, b: any(g0 <= a and b <= g1 for g0, g1 in gaps)
        options = []
        if f and s.get('tag'):
            options += [('above', (f0 - pad - slot, f1 + pad), blank(f0 - 66 / page_h, f0 - 12 / page_h)),
                        ('below', (f0 - pad, f1 + pad + slot), blank(f1 + 14 / page_h, f1 + 68 / page_h))]
        options.append(('auto', (f0 - pad, f1 + pad), False))
        best = None
        for n, (where, need, clean) in enumerate(options):
            found = snap_window(cy, ch, need, limit / page_h, gaps, (f0 + f1) / 2, float(s.get('zoom', 1.08)))
            if found and (best is None or (not clean, not found[2], n) < best[0]):
                best = ((not clean, not found[2], n), found[0], found[1], where)
        if best:
            _, y, h, tag = best
        else:
            h = limit / page_h
            y = min(max((f0 + f1) / 2 - h / 2, cy), cy + ch - h)
    if tag == 'auto':
        tag = 'above' if f and (f[1] - y) * page_h > 80 else 'below'
    return {'card_w': card_w, 'page_w': round(page_w), 'page_h': round(page_h), 'window_h': round(page_h * h),
            'x': round(cx, 4), 'y': round(y, 4), 'h': round(h, 4), 'focus': f, 'tag': tag}


def a_doc(s, ctx):
    """A window onto a real page from the source. The page fills the card width and the window shows a band of it
    around the focus (whole lines only); a slow push settles on it while the focus frame and tag land. The window
    keeps its proportions and scales down when the stage is shorter (burned-in captions), so it never slices text."""
    img = s.get('image') or 'TODO.png'
    d = doc_frame(s, ctx)
    card_w, pw, ph, wh, f = d['card_w'], d['page_w'], d['page_h'], d['window_h'], d['focus']
    focus = ''
    if f:
        x, y, w, h = f
        focus = f'<div class="doc-focus" style="left: {x * 100:.1f}%; top: {y * 100:.1f}%; width: {w * 100:.1f}%; height: {h * 100:.1f}%"></div>'
        if s.get('tag'):
            above = d['tag'] == 'above'
            pos = f'top: calc({y * 100:.1f}% - 66px)' if above else f'top: calc({(y + h) * 100:.1f}% + 14px)'
            focus += f'\n          <div class="doc-tag" style="left: {x * 100:.1f}%; {pos}">{rich(s["tag"])}</div>'
    fy = (f[1] + f[3] / 2) if f else d['y'] + d['h'] / 2
    origin = f'{(f[0] + f[2] / 2) * 100 if f else 50:.0f}% {fy * 100:.0f}%'
    head = f'<h2 class="headline is-h3 measure">{rich(s["headline"])}</h2>\n  <div class="gap-m"></div>' if s.get('headline') else ''
    return f'''{logo(ctx)}
<div class="cs-safe is-top">
  {eyebrow(s)}
  {head}
  <div class="doc-stage" data-zoom="{s.get('zoom', 1.08)}" data-origin="{origin}">
    <div class="doc-card" style="height: min(100%, {wh}px); aspect-ratio: {card_w} / {wh}">
      <div class="doc-page" data-layout-allow-overflow style="width: {pw / card_w * 100:.2f}%; height: {ph / wh * 100:.2f}%; left: {-d['x'] * pw / card_w * 100:.2f}%; top: {-d['y'] * ph / wh * 100:.2f}%">
        <img src="{esc(img)}" alt="{esc(plain(s.get('alt') or s.get('headline') or 'Source page'))}" />
        {focus}
      </div>
    </div>
  </div>
</div>'''


def a_flow(s, ctx):
    nodes = (s.get('nodes') or [{'label': 'TODO'}])[: (5 if ctx['fmt'] == 'landscape' else 3)]
    inner_w = ctx['w'] - 2 * ctx['pad_x']
    n = len(nodes)
    slot = inner_w / n
    parts, links = [], []
    sid = ctx['id']
    column = ctx['fmt'] == 'vertical'   # 9:16 has height to spare: stack the nodes so the diagram reads large
    for k, node in enumerate(nodes):
        hub = node.get('hub')
        width = 260 if hub else 200
        if column:
            width = 560
            left = round(inner_w * 0.16) + (0 if hub else 40)   # ring centers share one vertical line
            top = k * 330 + (0 if hub else 40)
        else:
            left = round(slot * k + slot / 2 - width / 2)
            top = 0 if hub else 40
        nid = f'{sid}-n{k + 1}'
        parts.append(f'''    <div class="node{' is-hub' if hub else ''}{' is-row' if column else ''}" id="{nid}" style="left: {left}px; top: {top}px; width: {width}px">
      <div class="node-ring"><svg class="ring" data-ring="{'double' if hub else 'open'}"></svg>{icon(node.get('icon'))}</div>
      <p class="node-label">{rich(node.get('label'))}</p>
    </div>''')
        if k:
            links.append(f'<path data-from="{sid}-n{k}" data-to="{nid}"></path>')
    return f'''{logo(ctx)}
<div class="cs-safe is-center">
  {eyebrow(s)}
  <h2 class="headline is-h2 measure">{rich(s.get('headline'))}</h2>
  <div class="gap-l"></div>
  <div class="flow" style="height: {330 * n if column else 360}px; flex: none">
    <svg class="links">{''.join(links)}</svg>
{chr(10).join(parts)}
  </div>
</div>'''


def a_end(s, ctx):
    line = f'<p class="headline is-h2 measure">{rich(s.get("line"))}</p>\n  <div class="gap-m"></div>'
    cta = f'<div class="cta">{rich(s.get("cta"))}</div>\n  <div class="gap-s"></div>' if s.get('cta', True) else ''
    url = f'<p class="url">{esc(s.get("url") or "catonetworks.com")}</p>'
    src = LOGO_COLOR if ctx['bg'] in LIGHT_BGS else LOGO_WHITE
    return f'''{ring_super(ctx, s.get('ring') or 'open', 1)}
<div class="cs-safe is-center is-center-x">
  <img class="logo-inline" src="{src}" alt="Cato Networks" />
  <div class="gap-m"></div>
  {line}
  {cta}
  {url}
</div>'''


def a_custom(s, ctx):
    return f'''{ring_super(ctx, s.get('ring'))}
{logo(ctx)}
<div class="cs-safe is-center">
  <!-- Custom scene: build the bespoke visual for this beat here, from cato.css classes and palette tokens. -->
  <h2 class="headline is-h2 measure">{rich(s.get('headline'))}</h2>
</div>'''


RENDER = {'hook': a_hook, 'statement': a_statement, 'stat': a_stat, 'cards': a_cards, 'compare': a_compare, 'list': a_list,
          'quote': a_quote, 'doc': a_doc, 'flow': a_flow, 'end': a_end, 'custom': a_custom}


def wrap(s, ctx, inner):
    sid, dur = ctx['id'], ctx['slot']
    tail = f' data-tail="{ctx["tail"]}"' if ctx['tail'] else ''
    inner = '\n'.join('        ' + line if line.strip() else '' for line in inner.splitlines())
    return f'''<template id="{sid}-template">
  <div id="root" data-composition-id="{sid}" data-width="{ctx['w']}" data-height="{ctx['h']}" data-duration="{dur}">
    <!-- Robin-Video scene "{sid}" · archetype: {s['archetype']} · {dur}s ({s.get('note', '').strip() or 'see storyboard.json'})
         Generated by kit.py build; edit freely (kit.py build never overwrites an existing scene file without --force-scenes). -->
    <link rel="stylesheet" href="assets/cato/cato.css" />
    <style>
      @font-face {{ font-family: Archivo; src: url("assets/cato/fonts/Archivo-Latin.woff2") format("woff2"); font-weight: 100 900; }}
      @font-face {{ font-family: Inter; src: url("assets/cato/fonts/Inter-Regular.woff") format("woff"); font-weight: 400; }}
      @font-face {{ font-family: Inter; src: url("assets/cato/fonts/Inter-Bold.woff") format("woff"); font-weight: 700; }}
      #root {{ position: absolute; inset: 0; overflow: hidden; }}
      /* Scene-specific layout: palette tokens only (var(--cato-green), var(--highlight), var(--pine)…). */
    </style>

    <div id="{sid}-scene" class="clip cs-scene" data-start="0" data-duration="{dur}" data-track-index="0" data-transition="{ctx['transition']}"{tail}>
      <div class="cs-frame bg-{ctx['bg']}">
{inner}
      </div>
    </div>

    <script src="assets/vendor/gsap.min.js"></script>
    <script src="assets/cato/cato-motion.js"></script>
    <script>
      (function () {{
        const root = document.querySelector('[data-composition-id="{sid}"]');
        const tl = gsap.timeline({{ paused: true }});
        CatoMotion.scene(tl, root);
        // Bespoke motion for this scene goes here, in local seconds, e.g.
        // tl.fromTo(root.querySelector(".headline .hl"), {{ scale: 1 }}, {{ scale: 1.04, duration: 0.6, ease: "power2.inOut" }}, 2.2);
        window.__timelines["{sid}"] = tl;
      }})();
    </script>
  </div>
</template>
'''


def render_scene(s, ctx):
    if s['archetype'] not in RENDER:
        raise ValueError(f'Unknown archetype {s["archetype"]} in scene {s.get("id")}. Use one of: {", ".join(ARCHETYPES)}')
    return wrap(s, ctx, RENDER[s['archetype']](s, ctx))
