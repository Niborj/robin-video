"""Robin-Video brand gate: check a composition (and optional post copy) against the Cato brand.

  python3 brand_check.py <output-dir>/composition [--copy <output-dir>/post.md] [--strict] [--json]

Checks
  B-COLOR       every color in the composition is a Cato palette color (alpha variants allowed)
  B-FONT        only Archivo (headlines) and Inter (body) are used
  B-LOGO        logos are the official, unmodified files (SHA-256), not stretched, present in the end card
  B-PLACEHOLDER no TODO / lorem / bracketed placeholders left on screen
  B-NAME…       approved product names, no alarm or hype words, calm punctuation, U.S. spelling (Cato voice)
  B-DENSITY     on-screen text stays short enough to read on a phone
  B-PRIVACY     no email addresses, internal hosts or phone numbers on screen
  B-MOTION      no bounce/elastic eases, 3D ring treatments or flashing
  B-NETWORK     no remote assets at render time
Writes brand-report.md and brand-report.json next to the composition folder. Exit code 1 when errors remain.
A line containing `brand-ok` (for example `/* brand-ok: partner logo color */`) is exempt from B-COLOR.
"""
from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
BRAND = json.loads((SKILL / 'assets/brand/cato-brand.json').read_text(encoding='utf-8'))

UK_STEMS = 'organ recogn optim priorit util minim maxim custom author standard central visual summar emphas real special normal final categor character critic apolog synchron initial modern'.split()
UK_WORDS = {'colour': 'color', 'colours': 'colors', 'behaviour': 'behavior', 'behaviours': 'behaviors', 'favour': 'favor', 'favourite': 'favorite',
            'honour': 'honor', 'labour': 'labor', 'neighbour': 'neighbor', 'humour': 'humor', 'centre': 'center', 'centres': 'centers', 'centred': 'centered',
            'metre': 'meter', 'fibre': 'fiber', 'theatre': 'theater', 'catalogue': 'catalog', 'programme': 'program', 'programmes': 'programs',
            'defence': 'defense', 'offence': 'offense', 'licence': 'license', 'travelled': 'traveled', 'modelling': 'modeling', 'labelled': 'labeled',
            'cancelled': 'canceled', 'enrolment': 'enrollment', 'judgement': 'judgment', 'ageing': 'aging', 'artefact': 'artifact', 'whilst': 'while',
            'amongst': 'among', 'towards': 'toward', 'learnt': 'learned', 'focussed': 'focused', 'analyse': 'analyze', 'analysed': 'analyzed',
            'analysing': 'analyzing', 'recognisable': 'recognizable', 'behaviours': 'behaviors'}
LEGACY_NAMES = [('Virtual Socket', 'Cato vSocket'), ('Cato SASE Cloud', 'Cato SASE Platform'), ('Cato SDP Client', 'Cato Client'), ('SDP Client', 'Cato Client'), ('ZTNA Client', 'Cato Client')]
SOCIAL_HYPE = ['excited to announce', 'thrilled to announce', 'excited to share', 'thrilled to share', 'unleash', 'supercharge', 'skyrocket', 'mind-blowing',
               'insane', 'crushing it', 'disrupt', 'disruptive', 'killer', 'hack your', 'secret sauce', 'world-leading', 'industry-leading', 'unparalleled']
# Names that appear in Cato's own brand materials but are not product names on the Brand Hub list.
KNOWN_NAMES = ['Cato Networks', 'Cato AI Security', 'Cato CTRL', 'Cato Green', 'Cato Grey', 'Cato Ring', 'Cato Socket SD-WAN']
NAME_RUN = re.compile(r'\bCato(?:[ \u00a0]+(?:[A-Z][\w/-]*|AI|SD-WAN|\d+))+')
PLACEHOLDER = re.compile(r'\b(TODO|TBD|FIXME|XXX|lorem|ipsum|placeholder|replace (?:me|this|with))\b|\[[^\]]{2,40}\]|\{\{[^}]*\}\}', re.I)
EMAIL = re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.]+\b')
HOST = re.compile(r'https?://[^\s"\']+|\b(?:api|internal|intranet|staging|dev|corp)\.[\w-]+\.[\w.]+\b', re.I)
PHONE = re.compile(r'(?<![\d.])(?:\+\d{1,3}[\s.-])?(?:\(\d{2,4}\)\s?)?\d{3,4}[\s.-]\d{3,4}[\s.-]\d{2,4}(?![\d.])')
COLOR = re.compile(r'#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b|rgba?\([^)]*\)|hsla?\([^)]*\)')
NAMED_COLORS = re.compile(r'(?<![-\w])(red|blue|green|yellow|orange|purple|pink|cyan|magenta|teal|navy|gray|grey|silver|gold|lime|aqua|maroon|olive)(?![-\w])', re.I)
# Bouncy or jittery eases as code (GSAP 3 "bounce.out", "elastic.out(1, 0.3)", "rough({...})", GSAP 2 "Bounce.easeOut",
# CustomBounce/CustomWiggle), not the words in copy: narration such as "through one policy" must not match "rough".
BOUNCY = re.compile(r'\b(?:bounce|elastic|rough|wiggle)(?:\.\w+|\()|\bcustom(?:bounce|wiggle)\b', re.I)


def palette():
    cols = set()
    def walk(v):
        if isinstance(v, dict):
            for x in v.values(): walk(x)
        elif isinstance(v, list):
            for x in v: walk(x)
        elif isinstance(v, str):
            for m in re.findall(r'#[0-9A-Fa-f]{6}', v):
                cols.add(m.upper())
    walk(BRAND['colors'])
    cols.update({'#00392F', '#474747'})  # official gradient stops
    return cols


PALETTE = palette()


def to_hex(token):
    t = token.strip()
    if t.startswith('#'):
        h = t[1:]
        if len(h) in (3, 4):
            h = ''.join(c * 2 for c in h[:3])
        return '#' + h[:6].upper()
    m = re.match(r'rgba?\(([^)]*)\)', t)
    if m:
        parts = re.split(r'[\s,/]+', m.group(1).strip())
        try:
            r, g, b = (int(round(float(p.rstrip('%')) * (2.55 if p.endswith('%') else 1))) for p in parts[:3])
            return f'#{r:02X}{g:02X}{b:02X}'
        except ValueError:
            return None
    return None


class TextExtractor(html.parser.HTMLParser):
    """Visible text per element, skipping script/style/svg and HTML comments."""
    SKIP = {'script', 'style', 'svg', 'head', 'title', 'noscript'}
    BLOCK = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'span', 'section', 'blockquote', 'figcaption', 'td', 'th', 'a', 'button'}

    def __init__(self, scene=None):
        super().__init__()
        self.stack, self.skip, self.items, self.imgs, self.buf, self.scene = [], 0, [], [], [], scene

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.SKIP:
            self.skip += 1
        if tag in ('section', 'div') and 'cs-scene' in (a.get('class') or '').split() and not self.scene:
            self.scene = a.get('id') or f'scene@{self.getpos()[0]}'
        if tag == 'img':
            self.imgs.append({**a, '_line': self.getpos()[0], '_scene': self.scene})
        if tag in self.BLOCK and not self.skip:
            self.flush()
            self.stack.append((tag, a.get('class', ''), self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        if tag in self.BLOCK and not self.skip:
            self.flush()
            if self.stack:
                self.stack.pop()

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.buf.append(data)

    def flush(self):
        text = re.sub(r'\s+', ' ', ''.join(self.buf)).strip()
        self.buf = []
        if text:
            tag, cls, line = self.stack[-1] if self.stack else ('body', '', 0)
            self.items.append({'text': text, 'tag': tag, 'class': cls, 'line': line, 'scene': self.scene})


def element_text(items):
    """Merge inline fragments back into one string per block-level element (headline spans stay together)."""
    merged = []
    for it in items:
        if merged and merged[-1]['line'] == it['line'] and merged[-1]['scene'] == it['scene']:
            merged[-1]['text'] += ' ' + it['text']
        else:
            merged.append(dict(it))
    return merged


def copy_rules(where, s, add, on_screen=True):
    names = [(bad, n['correct']) for n in BRAND.get('productNames', []) for bad in n.get('incorrect', [])]
    for bad, good in names:
        if re.search(r'\b' + re.escape(bad) + r'\b', s, re.I):
            add('B-NAME', 'error', where, f'Product name “{bad}” is not approved.', f'Use “{good}”.')
    for bad, good in LEGACY_NAMES:
        if re.search(r'\b' + re.escape(bad) + r'\b', s, re.I):
            add('B-NAME', 'warn', where, f'“{bad}” looks like an older or informal product name.', f'Prefer “{good}”; confirm with Product Marketing.')
    approved = [n['correct'] for n in BRAND.get('productNames', [])]
    approved += [re.sub(r'\s*\([^)]*\)', '', a) for a in approved] + KNOWN_NAMES
    for m in NAME_RUN.finditer(s):
        name = m.group(0).replace('\u00a0', ' ').rstrip('.')
        if name == 'Cato SASE' or any(name == a or name.startswith(a + ' ') or a.startswith(name) for a in approved):
            continue
        if any(name.lower() == bad.lower() for bad, _ in names):
            continue
        add('B-NAME-UNKNOWN', 'warn', where, f'“{name}” is not on the approved product-name list.', 'Confirm the current name with Product Marketing (or the user) before it ships.')
    if re.search(r'\bCato SASE\b(?! Platform)', s):
        add('B-NAME-SASE', 'warn', where, '“Cato SASE” alone is listed as incorrect when the platform is meant.', 'Use “Cato SASE Platform”.')
    for w in BRAND['voice']['avoidAlarm']:
        if re.search(r'\b' + re.escape(w) + r'\b', s, re.I):
            add('B-ALARM', 'error' if on_screen else 'warn', where, f'“{w}” adds fear or drama.', 'Calmly confident: state the risk plainly and say what people can do next.')
    for w in BRAND['voice']['avoidHype'] + SOCIAL_HYPE:
        if re.search(r'\b' + re.escape(w) + r'\b', s, re.I):
            add('B-HYPE', 'warn', where, f'“{w}” is hype rather than a clear point.', 'Smart and decisive: say what it means and what to do next.')
    if s.count('!') > 1:
        add('B-EXCLAIM', 'warn', where, 'Several exclamation marks.', 'Keep the voice calm; let the content carry the energy.')
    elif '!' in s:
        add('B-EXCLAIM', 'info', where, 'Exclamation mark.', 'Calm confidence rarely needs one.')
    for token in re.findall(r"[A-Za-z]+", s):
        low = token.lower()
        if low in UK_WORDS:
            add('B-SPELL-US', 'warn', where, f'“{token}” is not U.S. spelling.', f'Use “{UK_WORDS[low]}”.')
        m = re.fullmatch(r'(' + '|'.join(UK_STEMS) + r')is(e|es|ed|ing|ation|ations|er|ers)', low)
        if m:
            add('B-SPELL-US', 'warn', where, f'“{token}” is not U.S. spelling.', f'Use “{m.group(1)}iz{m.group(2)}”.')
        if on_screen and len(token) >= 6 and token.isupper() and token not in ('NETWORKS',):
            add('B-CAPS', 'warn', where, f'“{token}” in capitals reads as shouting.', 'Use sentence case; emphasize with Highlight Green instead (eyebrows are styled uppercase by CSS).')
    if re.search(r'\bclick here\b', s, re.I):
        add('B-LINK', 'warn', where, '“click here” does not describe the destination.', 'Name the destination.')
    for m in EMAIL.finditer(s):
        add('B-PRIVACY', 'error', where, f'Email address on screen: {m.group(0)}', 'Remove it or replace with a fictional, clearly generic address.')
    for m in HOST.finditer(s):
        if on_screen and re.search(r'api\.|internal|intranet|staging|dev\.|corp\.', m.group(0), re.I):
            add('B-PRIVACY', 'error', where, f'Internal host or API URL on screen: {m.group(0)}', 'Never show internal endpoints.')
    if on_screen and PHONE.search(s):
        add('B-PRIVACY', 'warn', where, 'Looks like a phone number.', 'Remove personal contact details.')


def check(comp: Path, copy_file: Path | None):
    findings = []

    def add(rule, severity, where, message, fix=''):
        findings.append({'rule': rule, 'severity': severity, 'where': where, 'message': message, 'fix': fix})

    index = comp / 'index.html'
    if not index.is_file():
        sys.exit(f'No index.html in {comp}')
    html_text = index.read_text(encoding='utf-8')
    sources = [(index, html_text)] + [(p, p.read_text(encoding='utf-8')) for p in comp.rglob('*.css') if 'node_modules' not in p.parts and p.name != 'cato.css'] \
        + [(p, p.read_text(encoding='utf-8')) for p in comp.rglob('*.html') if p != index and '.hyperframes' not in p.parts and 'node_modules' not in p.parts]

    # ---- colors and fonts (CSS, inline styles, inline scripts)
    for path, text in sources:
        rel = path.relative_to(comp)
        for n, line in enumerate(text.splitlines(), 1):
            if 'brand-ok' in line or re.search(r'<(svg|path|circle)\b[^>]*data-brand-ok', line):
                continue
            code = re.sub(r'<!--.*?-->|/\*.*?\*/', '', line)
            for m in COLOR.finditer(code):
                hx = to_hex(m.group(0))
                if hx is None:
                    add('B-COLOR', 'warn', f'{rel}:{n}', f'Could not read color {m.group(0)}.', 'Use a palette token from cato.css.')
                elif hx not in PALETTE:
                    add('B-COLOR', 'error', f'{rel}:{n}', f'{m.group(0)} is not a Cato palette color.', 'Use var(--cato-green), var(--highlight), var(--pine)… (alpha variants of palette colors are fine).')
            if re.search(r'(color|background|fill|stroke|border)[^;:{]*:\s*[^;]*', code):
                for m in NAMED_COLORS.finditer(re.sub(r'var\([^)]*\)|url\([^)]*\)|class="[^"]*"', '', code.split(':', 1)[-1] if ':' in code else '')):
                    add('B-COLOR', 'warn', f'{rel}:{n}', f'Named color “{m.group(1)}”.', 'Use palette tokens.')
            for m in re.finditer(r'font-family\s*:\s*([^;"}]+)', code):
                fams = [f.strip().strip('"\'') for f in m.group(1).split(',')]
                first = fams[0]
                if not re.match(r'^(Archivo|Inter|var\(--(display|body)\)|inherit)$', first, re.I):
                    add('B-FONT', 'error', f'{rel}:{n}', f'font-family starts with “{first}”.', 'Use var(--display) (Archivo Medium) for headlines and var(--body) (Inter) for everything else.')
            if re.search(r'rotate[XY]\s*\(|rotationX|rotationY|perspective\s*[:(]|preserve-3d', code):
                add('B-MOTION', 'warn', f'{rel}:{n}', '3D transform found.', 'The Ring and brand graphics are flat 2D; keep motion planar.')
            if BOUNCY.search(code) and path.suffix in ('.html', '.js'):
                add('B-MOTION', 'warn', f'{rel}:{n}', 'Bouncy or jittery ease.', 'Cato motion is calm and decisive: power3.out / expo.out / power2.inOut.')
            if re.search(r'(src|href)\s*=\s*["\']https?://', code) or re.search(r'url\(\s*["\']?https?://', code):
                add('B-NETWORK', 'error', f'{rel}:{n}', 'Remote asset at render time.', 'Copy the file into composition/assets/ and reference it relatively.')

    # ---- visible copy, logos, density
    # Scenes are sub-compositions mounted by index.html (kit.py build); read them in timeline order.
    mounted = re.findall(r'data-composition-src="([^"]+)"', html_text)
    texts, imgs, scenes = [], [], []
    for path, scene in [(index, None)] + [(comp / m, Path(m).stem) for m in mounted]:
        if not path.is_file():
            add('B-STRUCTURE', 'error', scene or 'index.html', f'Mounted file {path.name} is missing.', 'Run kit.py build.')
            continue
        ex = TextExtractor(scene)
        ex.feed(path.read_text(encoding='utf-8'))
        ex.flush()
        texts += element_text(ex.items)
        imgs += ex.imgs
        if scene and scene != 'captions':
            scenes.append(scene)
    if not mounted:
        scenes = sorted({t['scene'] for t in texts if t['scene']} | {i['_scene'] for i in imgs if i['_scene']})
    for t in texts:
        where = f'{t["scene"] or "root"} · line {t["line"]}'
        if PLACEHOLDER.search(t['text']):
            add('B-PLACEHOLDER', 'error', where, f'Placeholder text on screen: “{t["text"][:60]}”.', 'Replace with planned copy.')
        copy_rules(where, t['text'], add)
        n = len(t['text'].split())
        if 'headline' in t['class'] and n > 14:
            add('B-DENSITY', 'warn', where, f'Headline has {n} words.', 'Social hooks and headlines land at 3–12 words. Split it across beats.')
        elif n > 32:
            add('B-DENSITY', 'warn', where, f'{n} words in one on-screen block.', 'Nobody reads a paragraph in a feed. Cut to the point or split into beats.')
    official = {info['sha256']: name for name, info in BRAND['logos']['files'].items()}
    logo_scenes = set()
    for img in imgs:
        src = img.get('src', '')
        if 'logo' not in src.lower():
            continue
        f = (comp / src).resolve()
        where = f'{img["_scene"] or "root"} · line {img["_line"]}'
        if not f.is_file():
            add('B-LOGO', 'error', where, f'Logo file missing: {src}', 'Use the files kit.py copied into assets/cato/logos/.')
            continue
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        if 'cato' in src.lower() and digest not in official:
            add('B-LOGO', 'error', where, f'{src} is not an official, unmodified Cato logo.', 'Restore the official file; never redraw or recolor the logo.')
        else:
            logo_scenes.add(img['_scene'])
        style = img.get('style', '')
        if re.search(r'\bwidth\s*:', style) and re.search(r'\bheight\s*:\s*(?!auto)', style):
            add('B-LOGO', 'warn', where, 'Logo has both width and height set.', 'Set only the width (height: auto) so the logo is never distorted.')
        if re.search(r'filter|rotate|skew|opacity\s*:\s*0\.[0-4]', style):
            add('B-LOGO', 'error', where, 'Logo is filtered, rotated, skewed or faded.', 'Show the official mark as-is with clear space.')
    if not logo_scenes:
        add('B-LOGO', 'error', 'composition', 'No official Cato logo on screen.', 'Use the white logo on dark/green scenes and the color logo on light scenes; always in the end card.')
    elif scenes and scenes[-1] not in logo_scenes:
        add('B-LOGO', 'warn', scenes[-1], 'The final scene has no logo.', 'End on the logo lockup with the call to action.')
    dur = re.search(r'data-composition-id="[^"]+"[^>]*data-duration="([\d.]+)"|data-duration="([\d.]+)"[^>]*data-composition-id', html_text)
    if dur:
        d = float(dur.group(1) or dur.group(2))
        if d > 90:
            add('B-LENGTH', 'warn', 'root', f'{d:.0f} s is long for a feed video.', 'LinkedIn feed videos perform best at 15–45 s; cut or split into a series.')
        if d < 6:
            add('B-LENGTH', 'warn', 'root', f'{d:.1f} s is very short.', 'Give the hook and the end card time to read.')

    if copy_file and copy_file.is_file():
        body = copy_file.read_text(encoding='utf-8')
        for n, para in enumerate([p for p in re.split(r'\n\s*\n', body) if p.strip()], 1):
            if para.lstrip().startswith('#'):
                continue
            copy_rules(f'{copy_file.name} ¶{n}', para, add, on_screen=False)
            if PLACEHOLDER.search(para):
                add('B-PLACEHOLDER', 'error', f'{copy_file.name} ¶{n}', 'Placeholder in post copy.', 'Finish the copy.')
        tags = re.findall(r'(?<!\w)#\w+', body)
        if len(tags) > 5:
            add('B-POST', 'warn', copy_file.name, f'{len(tags)} hashtags.', 'Use three to five relevant hashtags on LinkedIn.')
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('composition', type=Path)
    ap.add_argument('--copy', type=Path, help='post copy (post.md) to check with the same voice rules')
    ap.add_argument('--strict', action='store_true', help='treat warnings as errors')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    comp = a.composition.resolve()
    findings = check(comp, a.copy)
    order = {'error': 0, 'warn': 1, 'info': 2}
    findings.sort(key=lambda f: (order[f['severity']], f['rule'], f['where']))
    errors = [f for f in findings if f['severity'] == 'error' or (a.strict and f['severity'] == 'warn')]
    report = {'composition': str(comp), 'errors': len([f for f in findings if f['severity'] == 'error']),
              'warnings': len([f for f in findings if f['severity'] == 'warn']), 'info': len([f for f in findings if f['severity'] == 'info']),
              'passed': not errors, 'findings': findings}
    out = comp.parent
    (out / 'brand-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    md = [f'# Brand report', '', f'- Composition: `{comp.name}`', f'- Result: **{"PASS" if report["passed"] else "FAIL"}** — {report["errors"]} error(s), {report["warnings"]} warning(s), {report["info"]} note(s)', '']
    for f in findings:
        md.append(f'- **{f["severity"].upper()} {f["rule"]}** `{f["where"]}` — {f["message"]}{" Fix: " + f["fix"] if f["fix"] else ""}')
    (out / 'brand-report.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    if a.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for f in findings:
            print(f'{f["severity"].upper():5} {f["rule"]:13} {f["where"]}: {f["message"]}' + (f'\n      fix: {f["fix"]}' if f['fix'] else ''))
        print(f'\nBrand check {"PASSED" if report["passed"] else "FAILED"}: {report["errors"]} error(s), {report["warnings"]} warning(s), {report["info"]} note(s). Report: {out / "brand-report.md"}')
    sys.exit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
