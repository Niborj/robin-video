/* CatoMotion — seek-safe Cato motion language for HyperFrames compositions (GSAP 3).
 *
 * Brand intent (Cato Visual Style R101): Reveal what matters → Connect ideas → Resolve with clarity.
 * Motion is calm, decisive and precise: masked rises, drawn rings and paths, clean settles.
 * No bounce, elastic, shake, glitch, flash, 3D spins or particle bursts.
 *
 * Every function adds tweens to a paused GSAP timeline at an absolute time and returns the time at which
 * its elements are settled (fully in), so callers can chain beats and hold text long enough to read.
 * Nothing here reads clocks, randomness or input, so any frame renders identically when seeked.
 *
 * Typical use inside a scene sub-composition (kit.py build writes this for you):
 *   const root = document.querySelector('[data-composition-id="stat"]');
 *   const tl = gsap.timeline({ paused: true });
 *   CatoMotion.scene(tl, root);                 // transition in, enter every brand element, fade copy out in the tail
 *   // bespoke tweens for this scene go here (local time, seconds)
 *   window.__timelines["stat"] = tl;
 */
(function (global) {
  'use strict';
  const EASE = { in: 'power3.out', strong: 'expo.out', move: 'power2.inOut', out: 'power2.in', soft: 'sine.inOut', none: 'none' };
  const NS = 'http://www.w3.org/2000/svg';
  const q = (sel, root) => (typeof sel === 'string' ? (root || document).querySelector(sel) : sel);
  const qa = (sel, root) => {
    if (!sel) return [];
    if (typeof sel === 'string') return Array.from((root || document).querySelectorAll(sel));
    if (sel instanceof Element) return [sel];
    return Array.from(sel);
  };
  const num = (v, d) => (v === undefined || v === null || v === '' || isNaN(+v) ? d : +v);
  const words = (el) => (el.textContent || '').trim().split(/\s+/).filter(Boolean).length;

  // ------------------------------------------------------------------ the Ring
  // Proportions measured from the official Ring family (solid disc, open ring, double ring, concentric rings),
  // in a 200×200 viewBox with outer radius 100. Flat 2D only.
  const RING = {
    disc: [{ r: 100, disc: true }],
    open: [{ r: 79, w: 42 }],
    double: [{ r: 93.15, w: 13.7 }, { r: 65.1, w: 14.2 }],
    concentric: [{ r: 96.15, w: 7.7 }, { r: 78.8, w: 7.6 }, { r: 61.8, w: 7.6 }],
    thin: [{ r: 96, w: 8 }],
    track: [{ r: 93, w: 14 }],
  };

  /** Fill every <svg data-ring="open|double|concentric|disc|thin|track"> with exact ring geometry. */
  function rings(root) {
    qa('svg[data-ring]', root || document).forEach((svg) => {
      if (svg.dataset.ringReady) return;
      const form = RING[svg.dataset.ring] || RING.open;
      svg.setAttribute('viewBox', '0 0 200 200');
      svg.setAttribute('aria-hidden', 'true');
      form.forEach((c) => {
        const el = document.createElementNS(NS, 'circle');
        el.setAttribute('cx', '100'); el.setAttribute('cy', '100'); el.setAttribute('r', String(c.r));
        if (c.disc) { el.setAttribute('class', 'ring-disc'); } else {
          el.setAttribute('stroke', 'currentColor'); el.setAttribute('stroke-width', String(c.w));
          el.setAttribute('pathLength', '1'); el.setAttribute('transform', 'rotate(-90 100 100)');
          el.style.strokeDasharray = '1 0';
        }
        svg.appendChild(el);
      });
      svg.dataset.ringReady = '1';
    });
  }

  // ------------------------------------------------------------------ text
  /** A word mask. Its padding (cato.css .w) reaches 0.02em past the word on purpose, so glyph edges and descenders
   *  are never clipped mid-rise: marked as intentional overflow for the HyperFrames layout check. */
  function mask() {
    const w = document.createElement('span'); w.className = 'w'; w.setAttribute('data-layout-allow-overflow', '');
    return w;
  }

  /** Wrap each word in a mask (.w > i) so it can rise from below. Keeps inline children such as .hl. */
  function split(target) {
    const out = [];
    qa(target).forEach((el) => {
      if (el.dataset.split) { out.push(...el.querySelectorAll('.w > i')); return; }
      const walk = (node) => {
        Array.from(node.childNodes).forEach((n) => {
          if (n.nodeType === 3) {
            const parts = n.textContent.split(/(\s+)/);
            if (!n.textContent.trim()) return;
            const frag = document.createDocumentFragment();
            parts.forEach((p) => {
              if (!p) return;
              if (/^\s+$/.test(p)) { frag.appendChild(document.createTextNode(' ')); return; }
              const w = mask();
              const i = document.createElement('i'); i.textContent = p; w.appendChild(i); frag.appendChild(w);
            });
            node.replaceChild(frag, n);
          } else if (n.nodeType === 1 && n.hasAttribute('data-count')) {
            // A counting number rises as one unit (its text is rewritten while it counts).
            const w = mask();
            const i = document.createElement('i');
            node.replaceChild(w, n); i.appendChild(n); w.appendChild(i);
          } else if (n.nodeType === 1 && !n.classList.contains('w') && !/^(svg|img|br)$/i.test(n.tagName)) {
            walk(n);
          }
        });
      };
      walk(el);
      el.dataset.split = '1';
      out.push(...el.querySelectorAll('.w > i'));
    });
    return out;
  }

  /** Masked rise, word by word. The signature Cato headline reveal. */
  function rise(tl, target, at, o = {}) {
    const inner = split(target);
    if (!inner.length) return at;
    const dur = num(o.dur, 0.75), stagger = num(o.stagger, Math.max(0.025, Math.min(0.07, 0.6 / inner.length)));
    tl.fromTo(inner, { yPercent: 115 }, { yPercent: 0, duration: dur, ease: o.ease || EASE.in, stagger }, at);
    return at + dur + stagger * (inner.length - 1);
  }

  /** Accent words (.hl) shift from the line color to Highlight Green (or Cato Green on light) as they land. */
  function highlight(tl, target, at, o = {}) {
    const els = qa(target).flatMap((el) => (el.classList && el.classList.contains('hl') ? [el] : qa('.hl', el)));
    els.forEach((el, k) => {
      const to = getComputedStyle(el).color;
      const from = getComputedStyle(el.parentElement).color;
      if (to === from) return;
      tl.fromTo(el, { color: from }, { color: to, duration: num(o.dur, 0.5), ease: EASE.move }, at + k * 0.12);
    });
    return at + 0.5;
  }

  function fadeUp(tl, target, at, o = {}) {
    const els = qa(target); if (!els.length) return at;
    const dur = num(o.dur, 0.6), stagger = num(o.stagger, 0.1);
    tl.fromTo(els, { opacity: 0, y: num(o.y, 36) }, { opacity: num(o.to, 1), y: 0, duration: dur, ease: o.ease || EASE.in, stagger }, at);
    return at + dur + stagger * (els.length - 1);
  }

  function fadeIn(tl, target, at, o = {}) {
    const els = qa(target); if (!els.length) return at;
    const dur = num(o.dur, 0.6);
    tl.fromTo(els, { opacity: 0 }, { opacity: num(o.to, 1), duration: dur, ease: o.ease || EASE.soft, stagger: num(o.stagger, 0) }, at);
    return at + dur;
  }

  function settleIn(tl, target, at, o = {}) {
    const els = qa(target); if (!els.length) return at;
    const dur = num(o.dur, 0.8), stagger = num(o.stagger, 0.12);
    tl.fromTo(els, { opacity: 0, scale: num(o.from, 0.92), y: num(o.y, 24) }, { opacity: 1, scale: 1, y: 0, duration: dur, ease: o.ease || EASE.strong, stagger }, at);
    return at + dur * 0.7 + stagger * (els.length - 1);
  }

  /** Reveal characters one at a time (for a typed question or prompt). cps = characters per second. */
  function typeOn(tl, target, at, o = {}) {
    const el = q(target); if (!el) return at;
    if (!el.dataset.typed) {
      const text = el.textContent; el.textContent = '';
      for (const ch of text) { const s = document.createElement('span'); s.textContent = ch; s.className = 'ch'; el.appendChild(s); }
      el.dataset.typed = '1';
    }
    const chars = qa('.ch', el), step = 1 / num(o.cps, 30);
    tl.fromTo(chars, { opacity: 0 }, { opacity: 1, duration: 0.01, ease: EASE.none, stagger: step }, at);
    return at + step * chars.length;
  }

  /** Count a number up. Put the number alone in its element (prefix and suffix in siblings), e.g.
   *  <span class="stat"><span data-count>30,254</span><span class="unit">%</span></span>.
   *  Reads the target, decimals and thousands separators from the element text unless given. */
  function countUp(tl, target, at, o = {}) {
    const els = qa(target);
    els.forEach((el, k) => {
      const raw = (el.dataset.countTo || el.textContent).trim();
      const to = num(o.to, parseFloat(raw.replace(/[^0-9.-]/g, '')));
      if (isNaN(to)) return;
      const decimals = o.decimals !== undefined ? o.decimals : ((raw.split('.')[1] || '').replace(/\D/g, '').length);
      const commas = o.commas !== undefined ? o.commas : /\d,\d{3}/.test(raw) || to >= 10000;
      const from = num(o.from, num(el.dataset.countFrom, 0));
      const fmt = (v) => { const s = v.toFixed(decimals); return commas ? s.replace(/\B(?=(\d{3})+(?!\d))/g, ',') : s; };
      el.dataset.countTo = raw;
      el.textContent = fmt(from);
      const state = { v: from };
      tl.to(state, { v: to, duration: num(o.dur, 1.4), ease: o.ease || 'power2.out', onUpdate: () => { el.textContent = fmt(state.v); } }, at + k * num(o.stagger, 0.18));
    });
    return at + num(o.dur, 1.4) + num(o.stagger, 0.18) * Math.max(0, els.length - 1);
  }

  // ------------------------------------------------------------------ rings and lines
  /** Draw ring strokes (pathLength 1). o.to = 0..1 portion (a progress ring), o.stagger for concentric forms. */
  function ringDraw(tl, target, at, o = {}) {
    rings();
    const circles = qa(target).flatMap((s) => (s.tagName.toLowerCase() === 'circle' ? [s] : qa('circle:not(.ring-disc)', s)));
    if (!circles.length) return at;
    const dur = num(o.dur, 1.1), stagger = num(o.stagger, 0.12), to = num(o.to, 1);
    tl.fromTo(circles, { strokeDasharray: '0 1' }, { strokeDasharray: `${to} ${1 - to + 0.0001}`, duration: dur, ease: o.ease || EASE.move, stagger }, at);
    return at + dur + stagger * (circles.length - 1);
  }

  /** Bring a ring super graphic in (scale and fade to its CSS opacity) and let it drift slowly for `hold` seconds. */
  function ringIn(tl, target, at, o = {}) {
    rings();
    qa(target).forEach((svg, k) => {
      const opacity = parseFloat(getComputedStyle(svg).opacity) || 1;
      const t = at + k * 0.15, inDur = o.settled ? 0 : num(o.dur, 1.6);
      if (!o.settled) tl.fromTo(svg, { opacity: 0, scale: num(o.from, 0.82) }, { opacity, scale: 1, duration: inDur, ease: EASE.strong }, t);
      if (o.hold) tl.fromTo(svg, { scale: 1, x: 0, y: 0 }, { scale: 1 + num(o.breathe, 0.05), x: num(o.dx, (k % 2 ? -1 : 1) * 24), y: num(o.dy, -18), duration: o.hold, ease: EASE.soft, immediateRender: false }, t + inDur);
    });
    return at + 0.6;
  }

  /** Draw SVG paths or lines (connections between ideas). Paths get pathLength 1 automatically. */
  function drawPath(tl, target, at, o = {}) {
    const paths = qa(target); if (!paths.length) return at;
    paths.forEach((p) => p.setAttribute('pathLength', '1'));
    const dur = num(o.dur, 0.8), stagger = num(o.stagger, 0.25);
    // Hidden until each path starts drawing, so round caps never show as a dot ahead of the line.
    paths.forEach((p, k) => tl.fromTo(p, { opacity: 0 }, { opacity: 1, duration: 0.05, ease: EASE.none }, at + k * stagger));
    tl.fromTo(paths, { strokeDasharray: '0 1' }, { strokeDasharray: '1 0', duration: dur, ease: o.ease || EASE.move, stagger }, at);
    return at + dur + stagger * (paths.length - 1);
  }

  // ------------------------------------------------------------------ media
  /** Slow push on an image (a document page, a screenshot, a photo). */
  function kenBurns(tl, target, at, dur, o = {}) {
    const el = q(target); if (!el) return at;
    tl.fromTo(el, { scale: num(o.from, 1), x: 0, y: 0, transformOrigin: o.origin || '50% 30%' },
      { scale: num(o.to, 1.12), x: num(o.x, 0), y: num(o.y, 0), duration: dur, ease: o.ease || EASE.soft }, at);
    return at + dur;
  }

  /** Frame what matters on a page: the focus box settles onto its target, then its tag appears. */
  function focus(tl, target, at, o = {}) {
    const el = q(target); if (!el) return at;
    tl.fromTo(el, { opacity: 0, scale: 1.18 }, { opacity: 1, scale: 1, duration: 0.7, ease: EASE.strong }, at);
    return at + 0.6;
  }

  // ------------------------------------------------------------------ transitions
  function stageSize() {
    const r = document.querySelector('[data-composition-id]');
    return [num(r && r.dataset.width, 1080), num(r && r.dataset.height, 1080)];
  }

  /** Run fn with the scene laid out, even if the runtime has hidden it; restores inline styles after. */
  function measured(scene, fn) {
    const s = q(scene); if (!s) return fn();
    const saved = [s.style.display, s.style.visibility];
    if (getComputedStyle(s).display === 'none') s.style.display = 'block';
    try { return fn(); } finally { s.style.display = saved[0]; s.style.visibility = saved[1]; }
  }

  function frameOf(scene) { const s = q(scene); return s ? (s.querySelector(':scope > .cs-frame') || s) : null; }

  /** The Ring as a transition: the next scene opens through an expanding circle, edged by a Highlight Green ring. */
  function iris(tl, scene, at, o = {}) {
    const frame = frameOf(scene); if (!frame) return at;
    const x = o.x || '50%', y = o.y || '50%', dur = num(o.dur, 0.85);
    tl.fromTo(frame, { clipPath: `circle(0% at ${x} ${y})` }, { clipPath: `circle(150% at ${x} ${y})`, duration: dur, ease: o.ease || 'power3.inOut' }, at);
    tl.set(frame, { clipPath: 'none' }, at + dur);
    if (o.edge !== false) {
      const host = q(scene);
      let edge = host.querySelector(':scope > .cs-iris-edge');
      if (!edge) {
        edge = document.createElementNS(NS, 'svg'); edge.setAttribute('class', 'cs-iris-edge'); edge.setAttribute('viewBox', '-100 -100 200 200');
        const [w, h] = stageSize(), R = Math.hypot(w, h) * 1.5 / Math.SQRT2;
        Object.assign(edge.style, { position: 'absolute', left: `calc(${x} - ${R}px)`, top: `calc(${y} - ${R}px)`, width: `${2 * R}px`, height: `${2 * R}px`, overflow: 'visible', pointerEvents: 'none', zIndex: 50 });
        const c = document.createElementNS(NS, 'circle'); c.setAttribute('r', '100'); c.setAttribute('fill', 'none');
        c.setAttribute('stroke', o.edgeColor || '#00FFCC'); c.setAttribute('stroke-width', String(num(o.edgeWidth, 10))); c.setAttribute('vector-effect', 'non-scaling-stroke');
        edge.appendChild(c); host.appendChild(edge);
      }
      tl.fromTo(edge, { scale: 0, opacity: 1 }, { scale: 1, duration: dur, ease: o.ease || 'power3.inOut' }, at);
      tl.to(edge, { opacity: 0, duration: 0.3, ease: EASE.out }, at + dur * 0.55);
    }
    return at + dur * 0.45;
  }

  function fadeThrough(tl, scene, at, o = {}) {
    const frame = frameOf(scene); if (!frame) return at;
    tl.fromTo(frame, { opacity: 0 }, { opacity: 1, duration: num(o.dur, 0.5), ease: EASE.soft }, at);
    return at + 0.2;
  }

  function pushUp(tl, scene, at, o = {}) {
    const frame = frameOf(scene); if (!frame) return at;
    tl.fromTo(frame, { yPercent: 100 }, { yPercent: 0, duration: num(o.dur, 0.7), ease: 'power3.inOut' }, at);
    return at + 0.35;
  }

  function wipe(tl, scene, at, o = {}) {
    const frame = frameOf(scene); if (!frame) return at;
    tl.fromTo(frame, { clipPath: 'inset(0% 100% 0% 0%)' }, { clipPath: 'inset(0% 0% 0% 0%)', duration: num(o.dur, 0.7), ease: 'power3.inOut' }, at);
    tl.set(frame, { clipPath: 'none' }, at + num(o.dur, 0.7));
    return at + 0.3;
  }

  const TRANSITIONS = { iris, fade: fadeThrough, push: pushUp, wipe, cut: (tl, s, at) => at };

  // ------------------------------------------------------------------ archetype choreography
  const BEATS = ['.ring--super', '.logo', '.logo-inline', '.eyebrow', '.headline', '.stat-ring', '.stat', '.cards', '.compare', '.list', '.quote-mark',
    '.quote-text', '.ring-photo', '.attrib-name', '.attrib-role', '.doc-card', '.doc-stage', '.flow', '.lead', '.body', '.small', '.cta', '.url', '[data-enter]'];
  const OWNERS = '.stat-ring, .cards, .compare, .list, .doc-stage, .flow, .cta';

  /** Animate every brand element in a scene in reading order, starting at `at`. Returns the settled time.
   *  Per element: data-enter="none" skips it, data-delay="0.3" shifts it, data-hold="1.2" adds reading time after it. */
  function enter(tl, scene, at, o = {}) {
    const root = q(scene); if (!root) return at;
    rings(root);
    const sceneDur = num(root.dataset.duration, 6);
    const seen = new Set();
    const els = qa(BEATS.join(','), root).filter((el) => {
      if (seen.has(el)) return false; seen.add(el);
      const owner = el.parentElement && el.parentElement.closest(OWNERS);
      return !(owner && root.contains(owner) && owner !== el);
    });
    let cursor = at + num(o.lead, o.settled ? 0.04 : 0.1), settled = at;
    for (const el of els) {
      const mode = el.dataset.enter;
      if (mode === 'none') continue;
      const t = cursor + num(el.dataset.delay, 0);
      let end = t, advance = 0.15;
      const c = el.classList;
      // On a cut (the opener, hard cuts) the frame's chrome is already there on frame 1; only the message moves.
      if (c.contains('ring--super')) { ringIn(tl, el, at, { hold: Math.max(1, sceneDur - (o.settled ? 0.2 : 1.6)), settled: o.settled }); continue; }
      if (c.contains('logo')) { if (!o.settled) fadeIn(tl, el, at + 0.15, { dur: 0.8 }); continue; }
      if (o.settled && c.contains('eyebrow') && mode !== 'rise') { continue; }
      if (c.contains('logo-inline')) { settleIn(tl, el, t, { from: 0.9, y: 0, dur: 0.9 }); cursor = t + 0.35; settled = Math.max(settled, t + 0.7); continue; }
      if (mode === 'rise' || c.contains('headline') || c.contains('quote-text')) {
        end = rise(tl, el, t, c.contains('quote-text') ? { stagger: 0.03, dur: 0.6 } : {});
        highlight(tl, el, Math.min(end, t + 0.5));
        advance = Math.min(1.1, 0.25 + words(el) * 0.05);
      } else if (c.contains('stat-ring')) {
        const svgs = qa('svg[data-ring]', el);
        const track = svgs.find((s) => s.dataset.role === 'track'), prog = svgs.find((s) => s.dataset.role !== 'track');
        if (track) ringDraw(tl, track, t, { dur: 0.9 });
        if (prog) ringDraw(tl, prog, t + 0.15, { to: num(prog.dataset.to, 1), dur: 1.5 });
        settleIn(tl, qa('.stat', el), t + 0.2, { from: 0.85 });
        end = countUp(tl, qa('[data-count]', el), t + 0.25, { dur: 1.5 });
        fadeUp(tl, qa('.small, .body, .lead, .eyebrow', el), t + 0.7);
        advance = 0.9;
      } else if (c.contains('stat')) {
        settleIn(tl, el, t, { from: 0.86 });
        end = countUp(tl, qa('[data-count]', el), t + 0.05, { dur: 1.3 });
        advance = 0.7;
      } else if (c.contains('cards')) {
        const cards = qa('.card', el);
        settleIn(tl, cards, t, { stagger: 0.22, from: 0.94 });
        cards.forEach((card, k) => countUp(tl, qa('[data-count]', card), t + 0.2 + k * 0.22, { dur: 1.2 }));
        end = t + 1.2 + 0.22 * (cards.length - 1);
        advance = 0.5 + cards.length * 0.25;
      } else if (c.contains('compare')) {
        const sides = qa('.side', el);
        const vertical = getComputedStyle(el).flexDirection === 'column';
        sides.forEach((s, k) => tl.fromTo(s, { opacity: 0, [vertical ? 'y' : 'x']: (k ? 1 : -1) * 60 }, { opacity: 1, [vertical ? 'y' : 'x']: 0, duration: 0.7, ease: EASE.in }, t + k * 0.35));
        const rows = sides.map((s) => qa('.row', s));
        const n = Math.max(0, ...rows.map((r) => r.length));
        for (let i = 0; i < n; i++) rows.forEach((r, k) => r[i] && fadeUp(tl, r[i], t + 0.5 + i * 0.32 + k * 0.12, { y: 18, dur: 0.45 }));
        end = t + 0.5 + n * 0.32 + 0.5;
        advance = 0.6 + n * 0.32;
      } else if (c.contains('list')) {
        const items = qa('.item', el), rail = q('.rail', el), step = num(el.dataset.step, 0.55);
        if (rail) tl.fromTo(rail, { scaleY: 0 }, { scaleY: 1, duration: step * items.length, ease: EASE.none }, t);
        items.forEach((it, k) => {
          const ti = t + k * step;
          ringDraw(tl, qa('svg[data-ring]', it), ti, { dur: 0.6 });
          const text = qa('span, p, div', it).filter((x) => !x.closest('svg'));
          rise(tl, text.length ? text : it, ti + 0.1, { dur: 0.6 });
        });
        end = t + step * items.length + 0.4;
        advance = step * items.length + 0.2;
      } else if (c.contains('quote-mark')) {
        tl.fromTo(el, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.6, ease: EASE.in }, t);
        end = t + 0.4; advance = 0.25;
      } else if (c.contains('ring-photo')) {
        tl.fromTo(el, { clipPath: 'circle(0% at 50% 50%)' }, { clipPath: 'circle(50% at 50% 50%)', duration: 0.9, ease: 'power3.inOut' }, t);
        end = t + 0.9; advance = 0.2;
      } else if (c.contains('doc-stage') || c.contains('doc-card')) {
        const card = c.contains('doc-card') ? el : q('.doc-card', el);
        settleIn(tl, card, t, { from: 0.9, y: 40, dur: 0.9 });
        const img = card && (q('.doc-page', card) || q('img', card));
        if (img && el.dataset.kenburns !== 'off') kenBurns(tl, img, t, Math.max(2, sceneDur - (t - at) + 0.5), { to: num(el.dataset.zoom, 1.08), origin: el.dataset.origin || '50% 40%' });
        let ft = t + 0.9;
        qa('.doc-focus', el).forEach((f) => { focus(tl, f, ft); ft += 0.5; });
        qa('.doc-tag', el).forEach((g) => { settleIn(tl, g, ft - 0.2, { from: 0.8, y: 10, dur: 0.5 }); ft += 0.3; });
        end = ft; advance = ft - t + 0.2;
      } else if (c.contains('flow')) {
        end = measured(root, () => flow(tl, el, t)); advance = end - t;
      } else if (c.contains('cta')) {
        settleIn(tl, el, t, { from: 0.88, y: 10 }); end = t + 0.6; advance = 0.3;
      } else if (mode === 'type') {
        end = typeOn(tl, el, t, { cps: num(el.dataset.cps, 30) }); advance = end - t;
      } else if (mode === 'count') {
        end = countUp(tl, el, t); advance = 0.4;
      } else if (mode === 'ring') {
        end = ringDraw(tl, el, t, { to: num(el.dataset.to, 1) }); advance = 0.3;
      } else if (mode === 'fade') {
        end = fadeIn(tl, el, t); advance = 0.2;
      } else {
        end = fadeUp(tl, el, t); advance = c.contains('eyebrow') ? 0.2 : 0.18;
      }
      cursor = t + advance + num(el.dataset.hold, 0);
      settled = Math.max(settled, end);
    }
    return settled;
  }

  /** Connect diagram: nodes appear in DOM order; path i (in .links) draws after node i.
   *  Author nodes with absolute left/top inside .flow; give paths data-from / data-to node ids to auto-route. */
  function flow(tl, el, at) {
    const nodes = qa('.node', el), links = qa('svg.links path', el), step = num(el.dataset.step, 0.6);
    const center = (n) => { const r = q('.node-ring', n) || n; return [n.offsetLeft + r.offsetLeft + r.offsetWidth / 2, n.offsetTop + r.offsetTop + r.offsetHeight / 2, r.offsetWidth / 2]; };
    links.forEach((p) => {
      if (p.getAttribute('d') || !p.dataset.from) return;
      const a = q('#' + p.dataset.from, el), b = q('#' + p.dataset.to, el); if (!a || !b) return;
      const [x1, y1, r1] = center(a), [x2, y2, r2] = center(b), len = Math.hypot(x2 - x1, y2 - y1) || 1;
      const ux = (x2 - x1) / len, uy = (y2 - y1) / len, g = 14;
      p.setAttribute('d', `M ${x1 + ux * (r1 + g)} ${y1 + uy * (r1 + g)} L ${x2 - ux * (r2 + g)} ${y2 - uy * (r2 + g)}`);
    });
    let t = at;
    nodes.forEach((n, k) => {
      ringDraw(tl, qa('svg[data-ring]', n), t, { dur: 0.7 });
      fadeIn(tl, qa('.icon', n), t + 0.2, { dur: 0.4 });
      fadeUp(tl, qa('.node-label', n), t + 0.25, { y: 14, dur: 0.45 });
      if (links[k]) drawPath(tl, links[k], t + 0.45, { dur: step });
      t += step;
    });
    return t + 0.5;
  }

  /** One scene, in its own sub-composition timeline (local time 0 = scene start).
   *  Runs the scene's data-transition (iris | fade | push | wipe | cut) at 0 and enters its elements. data-tail is the
   *  time it stays under the next scene's transition; its copy (.cs-safe) clears in the first 0.22 s of it
   *  (data-tail-fade="false" keeps it).
   *  Returns the settled time. Add bespoke tweens after calling it. */
  function scene(tl, root, o = {}) {
    const r = q(root); if (!r) return 0;
    const s = r.classList && r.classList.contains('cs-scene') ? r : (r.querySelector('.cs-scene') || r);
    rings(s);
    const kind = o.transition || s.dataset.transition || 'cut';
    const t = (TRANSITIONS[kind] || iris)(tl, s, 0, {});
    const settled = enter(tl, s, kind === 'cut' ? num(o.lead, 0) : Math.max(0.15, t - 0.2), { settled: kind === 'cut', ...o });
    const dur = num(s.dataset.duration, 0), tail = num(s.dataset.tail, 0);
    if (dur && tail && o.tailFade !== false && s.dataset.tailFade !== 'false') {
      // Clear this scene's copy as the next transition opens, so old and new text never share the frame.
      const copy = qa('.cs-safe, .ring-photo, .cs-copy', s);
      if (copy.length) tl.to(copy, { opacity: 0, duration: 0.22, ease: EASE.out }, dur - tail);
    }
    return settled;
  }

  /** Enter every .cs-scene at its data-start and run its data-transition (iris | fade | push | wipe | cut; default
   *  iris, first scene none). Scenes must overlap the previous one by the transition length (~0.85 s for iris). */
  function auto(tl, root, o = {}) {
    const scenes = qa('.cs-scene', q(root || '#root') || document);
    const settled = {};
    scenes.forEach((s, k) => {
      const start = num(s.dataset.start, 0);
      const kind = s.dataset.transition || (k === 0 ? 'cut' : (o.transition || 'iris'));
      const t = (TRANSITIONS[kind] || iris)(tl, s, start, {});
      settled[s.id || k] = enter(tl, s, k === 0 ? start : Math.max(start + 0.15, t - 0.2));
    });
    const bar = q('.progress', q(root || '#root'));
    if (bar) { const total = num((q(root || '#root') || {}).dataset && q(root || '#root').dataset.duration, 20); tl.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: total, ease: EASE.none }, 0); }
    return settled;
  }

  /** Burned-in captions with the spoken word in Highlight Green. cues: [{start, end, text}] (seconds). */
  function captions(tl, container, cues, o = {}) {
    const box = q(container); if (!box) return;
    cues.forEach((cue, k) => {
      const cap = document.createElement('div'); cap.className = 'cap';
      const ws = cue.text.split(/\s+/).filter(Boolean);
      ws.forEach((w, i) => { const s = document.createElement('span'); s.textContent = w; cap.appendChild(s); if (i < ws.length - 1) cap.appendChild(document.createTextNode(' ')); });
      box.appendChild(cap);
      tl.set(cap, { opacity: 1 }, cue.start);
      tl.set(cap, { opacity: 0 }, cue.end);
      if (o.karaoke !== false) {
        const spans = qa('span', cap), per = (cue.end - cue.start) / Math.max(1, spans.length);
        const on = o.onColor || '#00FFCC', off = o.offColor || '#FFFFFF';
        spans.forEach((s, i) => { tl.set(s, { color: on }, cue.start + i * per); tl.set(s, { color: off }, cue.start + (i + 1) * per); });
      }
    });
  }

  global.CatoMotion = { EASE, RING, rings, split, rise, highlight, fadeUp, fadeIn, settleIn, typeOn, countUp, ringDraw, ringIn, drawPath,
    kenBurns, focus, iris, fade: fadeThrough, push: pushUp, wipe, enter, flow, scene, auto, captions, measured };
})(window);
