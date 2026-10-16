"""Robin-Video composer: original, royalty-free background music for Cato social videos.

Every track is composed and synthesized here from code (no samples, no third-party recordings), so the music is
owned outright and safe for corporate posts and for sharing the skill. Ten styles cover the story types:

  pulse      tech pulse, 118 BPM        product launches, announcements
  ambient    ambient glow, 72 BPM       thought leadership, executive POV, reflective openers
  cinematic  cinematic rise, 92 BPM     reveals, research findings, launch hooks
  lofi       lo-fi focus, 84 BPM        explainers, how-tos, employer brand
  piano      hopeful piano, 96 BPM      customer stories, human stories
  minimal    minimal data, 124 BPM      threat research, data stories
  uplift     bright corporate, 112 BPM  events, partner news, wins
  deep       deep house, 120 BPM        events, culture, energetic teasers
  focus      calm suspense, 100 BPM     threat research without alarm, problem statements
  mallets    playful mallets, 108 BPM   explainers, employer brand, light news

Usage (numpy and scipy via uv, nothing else):
  uv run --with numpy --with scipy python compose_music.py --out <dir> [--style all|pulse,lofi,...] [--seed 7] [--bars N]
Writes <dir>/robin-<style>.mp3 plus cues/robin-<style>.music-cues.json and .md (beats, strong cues, sections) in the
same schema as the /brag cue presets, so kit.py and the composition step can align motion to the music.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from scipy import signal

SR = 44100
NOTE = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
        'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
QUALITY = {'': [0, 4, 7], 'm': [0, 3, 7], 'maj7': [0, 4, 7, 11], 'm7': [0, 3, 7, 10], '7': [0, 4, 7, 10], 'sus2': [0, 2, 7],
           'sus4': [0, 5, 7], 'add9': [0, 4, 7, 14], 'm9': [0, 3, 7, 10, 14], 'maj9': [0, 4, 7, 11, 14], '6': [0, 4, 7, 9],
           'm11': [0, 3, 7, 10, 17]}


# ---------------------------------------------------------------- theory

def midi_of(name):
    """'A3' -> 57."""
    n, octv = (name[:-1], int(name[-1]))
    return NOTE[n] + 12 * (octv + 1)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def chord(sym):
    """'Am7' -> (root pitch class, intervals)."""
    root = sym[:2] if len(sym) > 1 and sym[1] in '#b' else sym[:1]
    return NOTE[root], QUALITY[sym[len(root):]]


def voicing(sym, prev=None, lo=52, hi=74):
    """Close voicing of a chord in [lo, hi], led smoothly from the previous voicing."""
    pc, iv = chord(sym)
    best, best_cost = None, None
    for base in range(lo - 12, hi):
        if base % 12 != pc:
            continue
        for inv in range(len(iv)):
            notes = sorted(base + i + (12 if k < inv else 0) for k, i in enumerate(iv))
            if notes[0] < lo or notes[-1] > hi:
                continue
            cost = abs(np.mean(notes) - (np.mean(prev) if prev else (lo + hi) / 2)) + (0 if prev is None else 0.1 * sum(min(abs(a - b) for b in prev) for a in notes))
            if best_cost is None or cost < best_cost:
                best, best_cost = notes, cost
    return best or [pc + 60 + i for i in iv]


# ---------------------------------------------------------------- DSP

def tvec(n):
    return np.arange(n) / SR


def exp_env(n, decay, attack=0.002):
    t = tvec(n)
    env = np.exp(-t / max(decay, 1e-4))
    a = int(attack * SR)
    if a > 1:
        env[:a] *= np.linspace(0, 1, a)
    return env


def adsr(n, a, d, s, r):
    env = np.full(n, s, dtype=float)
    ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    ai = min(ai, n); env[:ai] = np.linspace(0, 1, ai, endpoint=False) if ai else env[:ai]
    d_end = min(n, ai + di)
    if d_end > ai:
        env[ai:d_end] = np.linspace(1, s, d_end - ai)
    if ri and n > ri:
        env[-ri:] *= np.linspace(1, 0, ri) ** 1.5
    return env


def saw(freq, n, phase=0.0):
    """Band-limited sawtooth (PolyBLEP)."""
    dt = freq / SR
    ph = (phase + dt * np.arange(n)) % 1.0
    y = 2 * ph - 1
    m = ph < dt
    t = ph[m] / dt
    y[m] -= t + t - t * t - 1
    m = ph > 1 - dt
    t = (ph[m] - 1) / dt
    y[m] -= t * t + t + t + 1
    return y


def sine(freq, n, phase=0.0):
    return np.sin(2 * np.pi * freq * tvec(n) + phase)


def lp(x, cutoff, order=2):
    sos = signal.butter(order, min(cutoff, SR * 0.45), 'low', fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def hp(x, cutoff, order=2):
    sos = signal.butter(order, cutoff, 'high', fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, min(hi, SR * 0.45)], 'band', fs=SR, output='sos')
    return signal.sosfilt(sos, x)


def noise(n, rng):
    return rng.uniform(-1, 1, n)


# ---------------------------------------------------------------- instruments (mono, return np.ndarray)

def kick(rng, punch=1.0, n=None):
    n = n or int(0.45 * SR)
    t = tvec(n)
    f = 46 + (130 * punch) * np.exp(-t / 0.045)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * exp_env(n, 0.28)
    click = hp(noise(int(0.004 * SR), rng), 2500) * 0.25
    body[:len(click)] += click
    return np.tanh(body * 1.6) * 0.9


def snare(rng, tone=190):
    n = int(0.28 * SR)
    return bp(noise(n, rng), 1200, 7000) * exp_env(n, 0.09) * 0.7 + sine(tone, n) * exp_env(n, 0.05) * 0.45


def clap(rng):
    n = int(0.32 * SR)
    x = np.zeros(n)
    for k, off in enumerate((0, 0.011, 0.022)):
        s = int(off * SR); m = int(0.012 * SR)
        x[s:s + m] += noise(m, rng) * (0.8 - 0.15 * k)
    tail = noise(n, rng) * exp_env(n, 0.11)
    tail[:int(0.03 * SR)] = 0
    return bp(x + tail * 0.6, 900, 3800) * 1.4


def hat(rng, open_=False, tone=7500):
    n = int((0.32 if open_ else 0.06) * SR)
    return hp(noise(n, rng), tone, 4) * exp_env(n, 0.12 if open_ else 0.022) * 0.35


def shaker(rng):
    n = int(0.12 * SR)
    return bp(noise(n, rng), 4500, 11000) * adsr(n, 0.012, 0.03, 0.4, 0.06) * 0.22


def rim(rng):
    n = int(0.08 * SR)
    return (bp(noise(n, rng), 1800, 3500) * 0.5 + sine(820, n) * 0.4) * exp_env(n, 0.018)


def tick(rng):
    n = int(0.05 * SR)
    return bp(noise(n, rng), 3000, 9000, 4) * exp_env(n, 0.01) * 0.35


def sub_bass(freq, dur, rng, cutoff=420, pluck=False):
    n = int(dur * SR)
    x = 0.65 * sine(freq, n) + 0.35 * lp(saw(freq, n), cutoff)
    env = exp_env(n, dur * 0.45, 0.004) if pluck else adsr(n, 0.006, 0.08, 0.85, min(0.08, dur * 0.3))
    return np.tanh(x * env * 1.3) * 0.8


def pad(freqs, dur, rng, cutoff=1800, attack=0.6, release=1.2, detune=0.08, bright=1.0):
    n = int((dur + release) * SR)
    x = np.zeros(n)
    for f in freqs:
        for d in (-detune, 0, detune):
            ff = f * 2 ** (d / 12)
            x += saw(ff, n, rng.uniform()) * (0.6 if d else 0.8)
    x = lp(x / (len(freqs) * 2.2), cutoff * bright)
    return x * adsr(n, attack, 0.4, 0.8, release)


def string_pad(freqs, dur, rng, cutoff=1400):
    n = int((dur + 1.4) * SR)
    vib = 1 + 0.0025 * np.sin(2 * np.pi * 5.2 * tvec(n))
    x = np.zeros(n)
    for f in freqs:
        for d in (-0.06, 0.05):
            ph = np.cumsum(f * 2 ** (d / 12) * vib) / SR
            p = ph % 1.0
            x += 2 * p - 1
    return lp(x / (len(freqs) * 2), cutoff) * adsr(n, 1.1, 0.5, 0.85, 1.4)


def pluck(freq, dur, rng, bright=0.5, decay=0.996):
    """Karplus-Strong string, run as an IIR filter (a two-tap averaging loop of the excitation burst)."""
    n = int((dur + 0.6) * SR)
    N = max(2, int(round(SR / freq - 0.5)))
    burst = lp(noise(N, rng), 1500 + 5000 * bright)
    excite = np.zeros(n); excite[:N] = burst
    a = np.zeros(N + 2); a[0] = 1.0; a[N] = -0.5 * decay; a[N + 1] = -0.5 * decay
    y = signal.lfilter([1.0], a, excite)
    return lp(y, 2500 + 4000 * bright) * exp_env(n, dur * 0.9 + 0.25, 0.001) * 0.6


def epiano(freq, dur, rng, bright=1.0):
    """FM electric piano (Rhodes-like)."""
    n = int((dur + 0.8) * SR)
    t = tvec(n)
    idx = (1.8 * bright) * np.exp(-t / 0.35) + 0.25
    mod = np.sin(2 * np.pi * freq * t)
    tone = np.sin(2 * np.pi * freq * t + idx * mod)
    tine = np.sin(2 * np.pi * freq * 14.0 * t) * np.exp(-t / 0.02) * 0.12
    return (tone + tine) * exp_env(n, 1.6, 0.003) * adsr(n, 0.001, 0.0, 1.0, 0.25) * 0.5


def piano(freq, dur, rng, vel=1.0):
    """Additive piano: inharmonic partials with frequency-dependent decay, two detuned strings and hammer noise."""
    n = int((dur + 1.6) * SR)
    t = tvec(n)
    B = 0.00035
    x = np.zeros(n)
    for k in range(1, 13):
        fk = k * freq * np.sqrt(1 + B * k * k)
        if fk > SR * 0.42:
            break
        amp = vel / k ** 1.15 * (1.0 if k > 1 else 1.2)
        dec = 2.8 / (1 + 0.35 * k) * (220 / max(freq, 60)) ** 0.35
        for det in (-0.6, 0.6):
            x += amp * np.sin(2 * np.pi * (fk + det * 0.1 * k) * t) * np.exp(-t / dec)
    hammer = lp(noise(int(0.01 * SR), rng), 3000) * 0.2 * vel
    x[:len(hammer)] += hammer
    damp = adsr(n, 0.001, 0, 1, 0.35)
    return lp(x * damp, 5000) * 0.22


def bell(freq, dur, rng, ratio=3.5):
    n = int((dur + 1.5) * SR)
    t = tvec(n)
    idx = 2.2 * np.exp(-t / 0.6)
    return np.sin(2 * np.pi * freq * t + idx * np.sin(2 * np.pi * freq * ratio * t)) * exp_env(n, 1.4, 0.002) * 0.3


def marimba(freq, dur, rng):
    n = int((dur + 0.6) * SR)
    t = tvec(n)
    parts = [(1.0, 1.0, 0.55), (3.93, 0.28, 0.12), (9.2, 0.08, 0.04)]
    x = sum(a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t / d) for r, a, d in parts)
    return x * adsr(n, 0.003, 0, 1, 0.05) * 0.45


def riser(dur, rng):
    n = int(dur * SR)
    x = noise(n, rng)
    out = np.zeros(n)
    blocks = 32
    for b in range(blocks):
        s, e = b * n // blocks, (b + 1) * n // blocks
        out[s:e] = bp(x[s:e], 500 + 7000 * (b / blocks) ** 2, 9000 + 4000 * b / blocks)
    return out * np.linspace(0, 1, n) ** 2 * 0.25


def boom(rng):
    n = int(2.2 * SR)
    t = tvec(n)
    f = 38 + 50 * np.exp(-t / 0.08)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * exp_env(n, 0.9) * 0.9 + lp(noise(n, rng), 600) * exp_env(n, 0.35) * 0.4)


# ---------------------------------------------------------------- mixing

class Mix:
    def __init__(self, seconds, rng):
        self.n = int(seconds * SR) + SR * 4
        self.rng = rng
        self.buses = {}
        self.kicks = []

    def add(self, bus, x, at, gain=1.0, pan=0.0):
        L, R = self.buses.setdefault(bus, (np.zeros(self.n), np.zeros(self.n)))
        s = int(at * SR)
        if s >= self.n:
            return
        e = min(self.n, s + len(x))
        gl, gr = gain * np.sqrt(0.5 * (1 - pan)), gain * np.sqrt(0.5 * (1 + pan))
        L[s:e] += x[:e - s] * gl
        R[s:e] += x[:e - s] * gr

    def sidechain(self, bus, depth=0.55, release=0.22):
        if bus not in self.buses or not self.kicks:
            return
        env = np.ones(self.n)
        r = int(release * SR)
        curve = 1 - depth * (1 - np.linspace(0, 1, r)) ** 2
        for k in self.kicks:
            s = int(k * SR)
            e = min(self.n, s + r)
            env[s:e] = np.minimum(env[s:e], curve[:e - s])
        L, R = self.buses[bus]
        self.buses[bus] = (L * env, R * env)


def reverb_ir(seconds, rng, damp=4500, width=1.0):
    n = int(seconds * SR)
    t = tvec(n)
    env = np.exp(-t / (seconds / 6.5))
    pre = int(0.018 * SR)
    irs = []
    for _ in range(2):
        x = lp(noise(n, rng), damp) * env
        x[:pre] = 0
        irs.append(x / np.sqrt(np.sum(x * x)))
    l, r = irs
    return l, l * (1 - width) + r * width


def apply_reverb(L, R, ir, wet):
    il, ir_ = ir
    wl = signal.fftconvolve(L, il)[:len(L)]
    wr = signal.fftconvolve(R, ir_)[:len(R)]
    return L * (1 - wet * 0.35) + wl * wet, R * (1 - wet * 0.35) + wr * wet


def delay(L, R, time, fb=0.35, mix=0.25, taps=4):
    d = int(time * SR)
    outL, outR = L.copy(), R.copy()
    for k in range(1, taps + 1):
        g = mix * fb ** (k - 1)
        sl, sr = (R, L) if k % 2 else (L, R)   # ping-pong
        outL[d * k:] += lp(sl[:-d * k], 3500) * g
        outR[d * k:] += lp(sr[:-d * k], 3500) * g
    return outL, outR


# ---------------------------------------------------------------- styles

STYLES = {}


def style(fn):
    STYLES[fn.__name__] = fn
    return fn


def grid(bpm):
    beat = 60.0 / bpm
    return beat, beat * 4


def sections_of(spec, bar):
    out, t = [], 0.0
    for name, bars, layers in spec:
        out.append({'name': name, 'start': round(t, 3), 'bars': bars, 'layers': set(layers)})
        t += bars * bar
    return out, t


def drums(m, sec, bar, beat, kick_steps, snare_steps=(), hat_steps=(), clap_steps=(), open_steps=(), shake_steps=(),
          swing=0.0, layer='drums', kick_gain=0.95, punch=1.0):
    rng = m.rng
    for b in range(sec['bars']):
        t0 = sec['start'] + b * bar
        for step in range(16):
            st = t0 + step * beat / 4 + (swing * beat / 4 if step % 2 else 0)
            if 'kick' in sec['layers'] and step in kick_steps:
                m.add(layer, kick(rng, punch), st, kick_gain); m.kicks.append(st)
            if 'snare' in sec['layers'] and step in snare_steps:
                m.add(layer, snare(rng), st, 0.55, 0.05)
            if 'clap' in sec['layers'] and step in clap_steps:
                m.add(layer, clap(rng), st, 0.5, -0.05)
            if 'hat' in sec['layers'] and step in hat_steps:
                m.add(layer, hat(rng), st, 0.55 + 0.15 * (step % 4 == 2), 0.25)
            if 'open' in sec['layers'] and step in open_steps:
                m.add(layer, hat(rng, True), st, 0.4, 0.3)
            if 'shaker' in sec['layers'] and step in shake_steps:
                m.add(layer, shaker(rng), st, 0.6 + 0.25 * (step % 4 == 0), -0.3)


def chords_track(m, sec, bar, prog, inst, bus='music', gain=0.5, lo=52, hi=74, per_bar=1, **kw):
    prev = None
    for b in range(sec['bars']):
        for h in range(per_bar):
            sym = prog[(b * per_bar + h) % len(prog)]
            v = voicing(sym, prev, lo, hi); prev = v
            t = sec['start'] + b * bar + h * bar / per_bar
            m.add(bus, inst([hz(x) for x in v], bar / per_bar, m.rng, **kw), t, gain)


def bass_track(m, sec, bar, beat, prog, steps, octave=2, gain=0.6, pluck=False, cutoff=420, per_bar=1, lengths=None):
    for b in range(sec['bars']):
        for h in range(per_bar):
            pc, _ = chord(prog[(b * per_bar + h) % len(prog)])
            root = pc + 12 * (octave + 1)
            for i, st in enumerate(steps):
                if st // (16 // per_bar) != h:
                    continue
                dur = (lengths[i] if lengths else 1) * beat / 4 * 0.95
                m.add('bass', sub_bass(hz(root), dur, m.rng, cutoff, pluck), sec['start'] + b * bar + st * beat / 4, gain)


def arp_track(m, sec, bar, beat, prog, inst, pattern, gain=0.3, octave_shift=12, per_bar=1, rate=4, pan_spread=0.4, **kw):
    prev = None
    for b in range(sec['bars']):
        for h in range(per_bar):
            v = voicing(prog[(b * per_bar + h) % len(prog)], prev, 55, 72); prev = v
            notes = v + [x + 12 for x in v]
            steps_per = 16 // per_bar
            for i in range(steps_per * rate // 4):
                idx = pattern[i % len(pattern)]
                if idx is None:
                    continue
                f = hz(notes[idx % len(notes)] + octave_shift)
                st = sec['start'] + b * bar + h * bar / per_bar + i * beat / rate
                pan = pan_spread * np.sin(i * 1.7)
                m.add('music', inst(f, beat / rate * 1.5, m.rng, **kw), st, gain, pan)


def melody_track(m, sec, bar, beat, notes, inst, gain=0.3, bus='lead', **kw):
    """notes: list of (beat_offset_in_section, midi, beats) repeated every len_bars bars."""
    for off, midi, length in notes:
        t = sec['start'] + off * beat
        if t >= sec['start'] + sec['bars'] * bar:
            continue
        m.add(bus, inst(hz(midi), length * beat, m.rng, **kw), t, gain)


@style
def pulse(m, rng):
    bpm = 118; beat, bar = grid(bpm)
    prog = ['Am', 'F', 'C', 'G']
    secs, total = sections_of([('intro', 4, ['arp', 'pad']), ('build', 4, ['arp', 'pad', 'kick', 'hat', 'bass']),
                               ('main', 8, ['arp', 'pad', 'kick', 'hat', 'bass', 'clap', 'open']),
                               ('lift', 8, ['arp', 'pad', 'kick', 'hat', 'bass', 'clap', 'open', 'lead']),
                               ('outro', 4, ['arp', 'pad', 'kick', 'hat'])], bar)
    for s in secs:
        drums(m, s, bar, beat, kick_steps={0, 4, 8, 12}, hat_steps={2, 6, 10, 14}, clap_steps={4, 12}, open_steps={14})
        if 'pad' in s['layers']:
            chords_track(m, s, bar, prog, pad, gain=0.32, cutoff=1500 if s['name'] == 'intro' else 2200, attack=0.4)
        if 'bass' in s['layers']:
            bass_track(m, s, bar, beat, prog, steps=[0, 3, 6, 8, 11, 14], gain=0.55, pluck=True, cutoff=600)
        if 'arp' in s['layers']:
            arp_track(m, s, bar, beat, prog, pluck, [0, 2, 1, 3, 2, 4, 3, 1], gain=0.26, bright=0.55)
        if 'lead' in s['layers']:
            motif = [(0, 76, 1.5), (2, 74, 0.5), (3, 72, 1), (4, 76, 2), (8, 79, 1.5), (10, 77, 0.5), (11, 76, 1), (12, 72, 3)]
            for rep in range(s['bars'] // 4):
                melody_track(m, s, bar, beat, [(o + rep * 16, n, l) for o, n, l in motif], bell, gain=0.16, ratio=2.0)
    m.sidechain('music', 0.28); m.sidechain('bass', 0.25)
    return {'bpm': bpm, 'sections': secs, 'total': total, 'reverb': (1.8, 0.22), 'delay': beat * 0.75}


@style
def ambient(m, rng):
    bpm = 72; beat, bar = grid(bpm)
    prog = ['Dmaj9', 'Bm9', 'Gmaj9', 'Asus4']
    secs, total = sections_of([('intro', 2, ['pad']), ('main', 6, ['pad', 'bells', 'sub']), ('lift', 6, ['pad', 'bells', 'sub', 'strings']),
                               ('outro', 2, ['pad', 'bells'])], bar)
    for s in secs:
        if 'pad' in s['layers']:
            chords_track(m, s, bar, prog, pad, gain=0.42, cutoff=1300, attack=1.4, release=2.5, detune=0.1)
        if 'strings' in s['layers']:
            chords_track(m, s, bar, prog, string_pad, gain=0.25, lo=62, hi=81, cutoff=2200)
        if 'sub' in s['layers']:
            bass_track(m, s, bar, beat, prog, steps=[0, 8], gain=0.42, cutoff=220, lengths=[8, 8])
        if 'bells' in s['layers']:
            arp_track(m, s, bar, beat, prog, bell, [0, None, 3, None, 2, None, None, 4], gain=0.13, rate=2, octave_shift=12, ratio=3.5)
    return {'bpm': bpm, 'sections': secs, 'total': total, 'reverb': (4.5, 0.5), 'delay': beat * 0.75}


@style
def cinematic(m, rng):
    bpm = 92; beat, bar = grid(bpm)
    prog = ['Dm', 'Bb', 'F', 'C']
    secs, total = sections_of([('intro', 4, ['strings', 'pulse']), ('build', 4, ['strings', 'pulse', 'perc', 'riser']),
                               ('main', 8, ['strings', 'pulse', 'perc', 'boom', 'brass', 'kick']),
                               ('outro', 4, ['strings', 'pulse'])], bar)
    for s in secs:
        if 'strings' in s['layers']:
            chords_track(m, s, bar, prog, string_pad, gain=0.42 if s['name'] != 'main' else 0.5, lo=50, hi=72, cutoff=1300 if s['name'] == 'intro' else 2400)
        if 'pulse' in s['layers']:
            bass_track(m, s, bar, beat, prog, steps=list(range(0, 16, 2)), gain=0.42, pluck=True, cutoff=900, octave=2)
        if 'perc' in s['layers']:
            drums(m, s, bar, beat, kick_steps=set(), snare_steps={12}, hat_steps={2, 6, 10, 14})
        if 'kick' in s['layers']:
            drums(m, {**s, 'layers': {'kick'}}, bar, beat, kick_steps={0, 10}, punch=0.7, kick_gain=1.0)
        if 'brass' in s['layers']:
            chords_track(m, s, bar, prog, pad, bus='lead', gain=0.2, lo=60, hi=79, cutoff=2600, attack=0.25)
        if 'riser' in s['layers']:
            m.add('fx', riser(s['bars'] * bar, rng), s['start'], 0.8)
        if 'boom' in s['layers']:
            for b in range(0, s['bars'], 4):
                m.add('fx', boom(rng), s['start'] + b * bar, 0.7)
    return {'bpm': bpm, 'sections': secs, 'total': total, 'reverb': (3.2, 0.38), 'delay': None}


@style
def lofi(m, rng):
    bpm = 84; beat, bar = grid(bpm)
    prog = ['Dm9', 'G7', 'Cmaj9', 'Am7']
    secs, total = sections_of([('intro', 2, ['keys', 'vinyl']), ('main', 8, ['keys', 'vinyl', 'kick', 'snare', 'hat', 'bass']),
                               ('lift', 8, ['keys', 'vinyl', 'kick', 'snare', 'hat', 'bass', 'lead']), ('outro', 2, ['keys', 'vinyl'])], bar)
    for s in secs:
        drums(m, s, bar, beat, kick_steps={0, 7, 10}, snare_steps={4, 12}, hat_steps={0, 2, 4, 6, 8, 10, 12, 14}, swing=0.28)
        if 'keys' in s['layers']:
            for b in range(s['bars']):
                v = voicing(prog[b % len(prog)], None, 53, 72)
                for k, x in enumerate(v):
                    m.add('music', epiano(hz(x), bar * 0.9, rng, bright=0.8), s['start'] + b * bar + k * 0.018, 0.2, -0.2 + 0.1 * k)
        if 'bass' in s['layers']:
            bass_track(m, s, bar, beat, prog, steps=[0, 7, 10], gain=0.5, cutoff=300, lengths=[6, 3, 5])
        if 'vinyl' in s['layers']:
            n = int(s['bars'] * bar * SR)
            crackle = (rng.uniform(size=n) > 0.9993) * rng.uniform(-1, 1, n)
            m.add('fx', hp(lp(crackle, 6000), 800) * 0.35 + lp(noise(n, rng), 1200) * 0.006, s['start'], 1.0)
        if 'lead' in s['layers']:
            motif = [(0, 74, 1), (1.5, 72, 0.5), (2, 69, 2), (8, 72, 1), (9.5, 71, 0.5), (10, 67, 2.5)]
            for rep in range(s['bars'] // 4):
                melody_track(m, s, bar, beat, [(o + rep * 16, n, l) for o, n, l in motif], epiano, gain=0.16, bright=1.2)
    m.buses['music'] = tuple(lp(x, 4200) for x in m.buses['music'])
    return {'bpm': bpm, 'sections': secs, 'total': total, 'reverb': (1.6, 0.22), 'delay': None}


@style
def piano_(m, rng):
    bpm = 96; beat, bar = grid(bpm)
    prog = ['C', 'G', 'Am', 'F']
    secs, total = sections_of([('intro', 4, ['piano']), ('main', 8, ['piano', 'pad', 'bass', 'shaker']),
                               ('lift', 8, ['piano', 'pad', 'bass', 'shaker', 'kick', 'melody']), ('outro', 4, ['piano', 'pad'])], bar)
    for s in secs:
        drums(m, s, bar, beat, kick_steps={0, 8}, shake_steps={2, 6, 10, 14}, punch=0.6, kick_gain=0.7)
        if 'piano' in s['layers']:
            arp_track(m, s, bar, beat, prog, piano, [0, 2, 4, 2, 1, 3, 5, 3], gain=0.42, rate=4, octave_shift=0, pan_spread=0.15)
        if 'pad' in s['layers']:
            chords_track(m, s, bar, prog, string_pad, gain=0.22, cutoff=1600)
        if 'bass' in s['layers']:
            bass_track(m, s, bar, beat, prog, steps=[0, 10], gain=0.45, cutoff=300, lengths=[10, 6])
        if 'melody' in s['layers']:
            motif = [(0, 79, 1.5), (1.5, 77, 0.5), (2, 76, 2), (4, 74, 1.5), (5.5, 72, 0.5), (6, 74, 2), (8, 76, 3), (12, 72, 4)]
            for rep in range(s['bars'] // 4):
                melody_track(m, s, bar, beat, [(o + rep * 16, n, l) for o, n, l in motif], piano, gain=0.3, vel=1.1)
    m.sidechain('music', 0.15)
    return {'bpm': bpm, 'sections': secs, 'total': total, 'reverb': (2.6, 0.32), 'delay': None}


STYLES['piano'] = STYLES.pop('piano_')


@style
def minimal(m, rng):
    bpm = 124; beat, bar = grid(bpm)
    prog = ['Fm', 'Fm', 'Db', 'Eb']
    secs, total = sections_of([('intro', 4, ['kick', 'tick']), ('build', 4, ['kick', 'tick', 'hat', 'bass']),
                               ('main', 8, ['kick', 'tick', 'hat', 'bass', 'stab', 'clap', 'rim']),
                               ('lift', 8, ['kick', 'tick', 'hat', 'bass', 'stab', 'clap', 'rim', 'open', 'blip']),
                               ('outro', 4, ['kick', 'tick', 'hat'])], bar)
    for s in secs:
        drums(m, s, bar, beat, kick_steps={0, 4, 8, 12}, hat_steps={2, 6, 10, 14}, clap_steps={4, 12}, open_steps={14}, punch=1.1)
        for b in range(s['bars']):
            t0 = s['start'] + b * bar
            if 'tick' in s['layers']:
                for st in range(0, 16, 1):
                    if st % 4 != 0:
                        m.add('drums', tick(rng), t0 + st * beat / 4, 0.25 + 0.2 * (st % 2), 0.4 * np.sin(st))
            if 'rim' in s['layers']:
                for st in (3, 11, 13):
                    m.add('drums', rim(rng), t0 + st * beat / 4, 0.3, -0.35)
        if 'bass' in s['layers']:
            bass_track(m, s, bar, beat, prog, steps=[2, 6, 10, 14], gain=0.55, pluck=True, cutoff=700, octave=1)
        if 'stab' in s['layers']:
            for b in range(s['bars']):
                v = voicing(prog[b % len(prog)], None, 55, 70)
                for st in (3, 10):
                    m.add('music', pad([hz(x) for x in v], beat / 4, rng, cutoff=2400, attack=0.005, release=0.25), s['start'] + b * bar + st * beat / 4, 0.3)
        if 'blip' in s['layers']:
            arp_track(m, s, bar, beat, prog, bell, [0, None, None, 2, None, 4, None, None], gain=0.12, rate=4, octave_shift=24, ratio=1.0)
    m.sidechain('music', 0.3); m.sidechain('bass', 0.3)
    return {'bpm': bpm, 'sections': secs, 'total': total, 'reverb': (1.4, 0.2), 'delay': beat * 0.75}


@style
def uplift(m, rng):
    bpm = 112; beat, bar = grid(bpm)
    prog = ['Gadd9', 'D', 'Em7', 'C']
    secs, total = sections_of([('intro', 4, ['guitar', 'shaker', 'pad']), ('main', 8, ['guitar', 'shaker', 'kick', 'clap', 'bass', 'pad']),
                               ('lift', 8, ['guitar', 'shaker', 'kick', 'clap', 'bass', 'pad', 'bells', 'hat']),
                               ('outro', 4, ['guitar', 'shaker', 'pad'])], bar)
    for s in secs:
        drums(m, s, bar, beat, kick_steps={0, 6, 8}, clap_steps={4, 12}, hat_steps={2, 6, 10, 14}, shake_steps=set(range(0, 16, 2)))
        if 'guitar' in s['layers']:
            prev = None
            for b in range(s['bars']):
                v = voicing(prog[b % len(prog)], prev, 52, 71); prev = v
                for st in (0, 3, 6, 8, 10, 12, 14):
                    for k, x in enumerate(v + [v[0] + 12]):
                        m.add('music', pluck(hz(x), beat * 0.6, rng, bright=0.6, decay=0.994), s['start'] + b * bar + st * beat / 4 + k * 0.009, 0.2 * (1.0 if st in (0, 8) else 0.7), -0.3 + 0.15 * k)
        if 'pad' in s['layers']:
            chords_track(m, s, bar, prog, pad, gain=0.2, cutoff=2000, attack=0.5)
        if 'bass' in s['layers']:
            bass_track(m, s, bar, beat, prog, steps=[0, 6, 8, 12], gain=0.5, cutoff=500, lengths=[5, 2, 4, 4])
        if 'bells' in s['layers']:
            motif = [(0, 79, 1), (1, 81, 1), (2, 83, 2), (4, 81, 1), (5, 79, 1), (6, 78, 2), (8, 79, 1), (9, 76, 1), (10, 74, 4)]
            for rep in range(s['bars'] // 4):
                melody_track(m, s, bar, beat, [(o + rep * 16, n, l) for o, n, l in motif], bell, gain=0.13, ratio=2.0)
    m.sidechain('music', 0.18)
    return {'bpm': bpm, 'sections': secs, 'total': total, 'reverb': (1.8, 0.25), 'delay': None}


@style
def deep(m, rng):
    bpm = 120; beat, bar = grid(bpm)
    prog = ['Am9', 'Am9', 'Fmaj9', 'G6']
    secs, total = sections_of([('intro', 4, ['kick', 'hat', 'chords']), ('main', 8, ['kick', 'hat', 'chords', 'bass', 'clap', 'shaker']),
                               ('lift', 8, ['kick', 'hat', 'chords', 'bass', 'clap', 'shaker', 'open', 'keys']),
                               ('outro', 4, ['kick', 'hat', 'chords'])], bar)
    for s in secs:
        drums(m, s, bar, beat, kick_steps={0, 4, 8, 12}, hat_steps={2, 6, 10, 14}, clap_steps={4, 12}, open_steps={2, 10},
              shake_steps={1, 3, 5, 7, 9, 11, 13, 15}, punch=0.9)
        if 'chords' in s['layers']:
            for b in range(s['bars']):
                v = voicing(prog[b % len(prog)], None, 55, 74)
                cut = 900 + 1600 * (0.5 + 0.5 * np.sin(2 * np.pi * b / 8))
                for st in (3, 6, 11, 14):
                    m.add('music', pad([hz(x) for x in v], beat / 2, rng, cutoff=cut, attack=0.01, release=0.35), s['start'] + b * bar + st * beat / 4, 0.32)
        if 'bass' in s['layers']:
            bass_track(m, s, bar, beat, prog, steps=[0, 3, 7, 10, 14], gain=0.6, cutoff=380, lengths=[2, 3, 2, 3, 2], octave=1)
        if 'keys' in s['layers']:
            arp_track(m, s, bar, beat, prog, epiano, [4, None, 2, None, None, 3, None, 1], gain=0.12, rate=4, octave_shift=12)
    m.sidechain('music', 0.32); m.sidechain('bass', 0.3)
    return {'bpm': bpm, 'sections': secs, 'total': total, 'reverb': (2.0, 0.26), 'delay': beat * 0.75}


@style
def focus(m, rng):
    bpm = 100; beat, bar = grid(bpm)
    prog = ['Em', 'Em', 'Cmaj7', 'Bsus4']
    secs, total = sections_of([('intro', 4, ['drone', 'clock']), ('build', 4, ['drone', 'clock', 'pulse']),
                               ('main', 8, ['drone', 'clock', 'pulse', 'kick', 'piano']),
                               ('lift', 4, ['drone', 'clock', 'pulse', 'kick', 'piano', 'strings']), ('outro', 4, ['drone', 'clock'])], bar)
    for s in secs:
        if 'drone' in s['layers']:
            chords_track(m, s, bar, prog, pad, gain=0.3, lo=40, hi=60, cutoff=700, attack=1.5, release=2.0)
        if 'clock' in s['layers']:
            for b in range(s['bars']):
                for st in range(0, 16, 2):
                    m.add('drums', tick(rng), s['start'] + b * bar + st * beat / 4, 0.32 if st % 4 == 0 else 0.18, 0.5 if st % 4 else -0.5)
        if 'pulse' in s['layers']:
            bass_track(m, s, bar, beat, prog, steps=list(range(0, 16, 2)), gain=0.32, pluck=True, cutoff=500, octave=1)
        if 'kick' in s['layers']:
            drums(m, {**s, 'layers': {'kick'}}, bar, beat, kick_steps={0, 6, 8}, punch=0.6, kick_gain=0.8)
        if 'piano' in s['layers']:
            motif = [(0, 71, 2), (3, 67, 1), (4, 69, 2), (8, 71, 2), (11, 74, 1), (12, 72, 4)]
            for rep in range(s['bars'] // 4):
                melody_track(m, s, bar, beat, [(o + rep * 16, n, l) for o, n, l in motif], piano, gain=0.32, bus='music', vel=0.8)
        if 'strings' in s['layers']:
            chords_track(m, s, bar, prog, string_pad, gain=0.22, lo=59, hi=79, cutoff=1800)
    return {'bpm': bpm, 'sections': secs, 'total': total, 'reverb': (3.0, 0.36), 'delay': beat * 0.75}


@style
def mallets(m, rng):
    bpm = 108; beat, bar = grid(bpm)
    prog = ['F', 'C', 'Dm', 'Bb']
    secs, total = sections_of([('intro', 4, ['mallets', 'shaker']), ('main', 8, ['mallets', 'shaker', 'kick', 'snare', 'bass']),
                               ('lift', 8, ['mallets', 'shaker', 'kick', 'snare', 'bass', 'lead', 'pad']),
                               ('outro', 4, ['mallets', 'shaker'])], bar)
    for s in secs:
        drums(m, s, bar, beat, kick_steps={0, 10}, snare_steps={4, 12}, shake_steps=set(range(16)), swing=0.12, punch=0.7, kick_gain=0.8)
        if 'mallets' in s['layers']:
            arp_track(m, s, bar, beat, prog, marimba, [0, 2, 1, 3, 2, None, 4, 2], gain=0.42, rate=4, octave_shift=12, pan_spread=0.5)
        if 'bass' in s['layers']:
            bass_track(m, s, bar, beat, prog, steps=[0, 3, 8, 11], gain=0.45, pluck=True, cutoff=450, lengths=[3, 3, 3, 3])
        if 'pad' in s['layers']:
            chords_track(m, s, bar, prog, pad, gain=0.16, cutoff=1500, attack=0.6)
        if 'lead' in s['layers']:
            motif = [(0, 81, 0.5), (0.5, 84, 0.5), (1, 81, 1), (3, 77, 1), (4, 79, 2), (8, 77, 0.5), (8.5, 81, 0.5), (9, 79, 1), (11, 74, 1), (12, 77, 3)]
            for rep in range(s['bars'] // 4):
                melody_track(m, s, bar, beat, [(o + rep * 16, n, l) for o, n, l in motif], bell, gain=0.12, ratio=4.0)
    return {'bpm': bpm, 'sections': secs, 'total': total, 'reverb': (1.6, 0.24), 'delay': None}


DESCRIPTIONS = {
    'pulse': ('Tech pulse', 'Driving four-on-the-floor, plucked arpeggios, minor key. Confident and modern.', 'product launches, announcements'),
    'ambient': ('Ambient glow', 'No drums: evolving pads, soft bells, deep sub. Calm and spacious.', 'thought leadership, executive POV, reflective openers'),
    'cinematic': ('Cinematic rise', 'Strings and a pulsing ostinato that build to big low hits.', 'reveals, research findings, launch hooks'),
    'lofi': ('Lo-fi focus', 'Swung beat, warm electric piano, vinyl texture. Relaxed and human.', 'explainers, how-tos, employer brand'),
    'piano': ('Hopeful piano', 'Flowing piano arpeggios over soft strings and a light pulse.', 'customer stories, people stories'),
    'minimal': ('Minimal data', 'Tight minimal techno: ticks, rimshots, rolling bass, short stabs.', 'threat research, data stories'),
    'uplift': ('Bright corporate', 'Strummed plucked guitar, claps, bells. Positive without being cheesy.', 'events, partner news, wins'),
    'deep': ('Deep house', 'Warm filtered chords, rolling bass, shuffling hats.', 'events, culture, energetic teasers'),
    'focus': ('Calm suspense', 'Ticking clock, low drone and a sparse piano motif. Focused, never alarming.', 'threat research, problem statements'),
    'mallets': ('Playful mallets', 'Marimba patterns, shaker and light drums. Curious and friendly.', 'explainers, employer brand, light news'),
}


# ---------------------------------------------------------------- render, master, cues

# Tonal balance of professionally mastered commercial beds (low <150 Hz, mid 150-1k, high-mid 1k-5k, air >5k), in dB
# relative to the full mix. Measured on five produced library tracks; every render is steered toward it, plus a small
# per-style character offset, so synthesized arrangements land with the weight and clarity of produced music.
TARGET_BANDS = [-2.9, -5.9, -15.2, -24.3]
CHARACTER = {'ambient': [0, 0, -1, -4], 'lofi': [0, 0.5, -2, -5], 'piano': [-2, 0, 0, -2], 'deep': [1, 0, -1, 0],
             'minimal': [0.5, -1, 0, 1], 'cinematic': [1, 0, -1, -2], 'focus': [0, 0, -1, -2]}
CROSSOVERS = (150, 1000, 5000)


def _split(x):
    out, r = [], x.copy()
    for f in CROSSOVERS:   # zero-phase low-pass and subtraction: the bands sum back to the input exactly
        b = signal.sosfiltfilt(signal.butter(2, f, 'low', fs=SR, output='sos'), r)
        out.append(b); r = r - b
    out.append(r)
    return out


def _band_db(bands, total):
    return [20 * np.log10(np.sqrt(np.mean(b * b)) / total + 1e-12) for b in bands]


def level_sections(L, R, ratio=0.55, max_boost_db=7.0, window=2.0):
    """Slow macro leveler: lifts quiet passages (sparse intros) toward the body of the track so a bed never jumps
    when the full arrangement enters. Gain follows a ~2 s loudness envelope; never cuts, boosts at most max_boost_db."""
    mid = 0.5 * (L + R)
    w = int(window * SR)
    power = signal.fftconvolve(mid * mid, np.ones(w) / w, mode='same')
    rms = np.sqrt(np.maximum(power, 1e-12))
    ref = np.percentile(rms[rms > 1e-6], 75)
    gain_db = np.clip(20 * np.log10(ref / rms) * (1 - ratio), 0, max_boost_db)
    gain = 10 ** (signal.fftconvolve(gain_db, np.ones(w) / w, mode='same') / 20)
    return L * gain, R * gain


def master_balance(L, R, name, passes=2, limit=10.0):
    target = np.array(TARGET_BANDS) + np.array(CHARACTER.get(name, [0, 0, 0, 0]))
    for _ in range(passes):
        mid = 0.5 * (L + R)
        total = np.sqrt(np.mean(mid * mid)) or 1e-9
        gains = np.clip(target - np.array(_band_db(_split(mid), total)), -limit, limit)
        lin = 10 ** (gains / 20)
        L = sum(g * b for g, b in zip(lin, _split(L)))
        R = sum(g * b for g, b in zip(lin, _split(R)))
    return L, R

def render(name, seed=7):
    rng = np.random.default_rng(seed + sum(map(ord, name)))
    m = Mix(110, rng)
    meta = STYLES[name](m, rng)
    total = meta['total']
    n = int((total + 0.05) * SR)
    rev = reverb_ir(meta['reverb'][0], rng)
    sends = {'drums': 0.25, 'bass': 0.0, 'music': 1.0, 'lead': 1.0, 'fx': 0.6}
    L = np.zeros(m.n); R = np.zeros(m.n)
    for bus, (bl, br) in m.buses.items():
        if bus == 'bass':
            bl, br = hp(bl, 30), hp(br, 30)
        else:
            bl, br = hp(bl, 140 if bus in ('music', 'lead') else 35), hp(br, 140 if bus in ('music', 'lead') else 35)
        if bus in ('music', 'lead') and meta.get('delay'):
            bl, br = delay(bl, br, meta['delay'], mix=0.18 if bus == 'lead' else 0.1)
        wet = meta['reverb'][1] * sends.get(bus, 0.5)
        if wet:
            bl, br = apply_reverb(bl, br, rev, wet)
        L += bl; R += br
    L, R = L[:n], R[:n]
    # fade the last bar so the track ends cleanly, steer the tonal balance last, then leave level to the encoder's
    # loudness normalization and true-peak limiter (no clipping stage that would add harsh harmonics)
    fade = int(min(2.0, 60 / meta['bpm'] * 4) * SR)
    for ch in (L, R):
        ch[-fade:] *= np.linspace(1, 0, fade) ** 2
    L, R = level_sections(L, R)
    for ch in (L, R):   # keep the final fade a fade after leveling
        ch[-fade:] *= np.linspace(1, 0, fade) ** 0.5
    L, R = master_balance(L, R, name)
    peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-9)
    return np.stack([L, R], axis=1) / peak * 0.89, meta


def write_mp3(audio, path: Path, target_lufs=-14.5):
    """Encode at a consistent loudness with a static gain and a true-peak limiter. (Single-pass dynamic loudnorm
    rides the gain on wide-range tracks and audibly brightens them, so it is not used.)"""
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'mix.wav'
        pcm = (np.clip(audio, -1, 1) * 32767).astype('<i2')
        with wave.open(str(wav), 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
        meter = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(wav), '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'],
                               capture_output=True, text=True).stderr
        lufs = float(meter.split('Integrated loudness:')[1].split('I:')[1].split('LUFS')[0])
        gain = target_lufs - lufs
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(wav),
                        '-af', f'volume={gain:.2f}dB,alimiter=limit=0.84:attack=3:release=60:level=false', '-ar', '48000',
                        '-c:a', 'libmp3lame', '-b:a', '192k', '-metadata', 'artist=Robin-Video composer',
                        '-metadata', 'comment=Original royalty-free music generated by Robin-Video', str(path)], check=True)


def cues(audio, meta, stem, filename, name):
    bpm, total = meta['bpm'], meta['total']
    beat = 60 / bpm
    mono = audio.mean(axis=1)
    win = int(0.09 * SR)
    def energy(t):
        s = int(t * SR); seg = mono[s:s + win]
        return float(np.sqrt(np.mean(seg * seg))) if len(seg) else 0.0
    times = np.arange(0, total - 0.01, beat)
    raw = np.array([energy(t) for t in times])
    norm = raw / (np.percentile(raw, 98) or 1)
    section_starts = {round(s['start'], 3) for s in meta['sections']}
    beats = []
    for i, (t, e) in enumerate(zip(times, norm)):
        boost = 0.2 if i % 4 == 0 else 0.0
        beats.append({'time': round(float(t), 4), 'intensity': round(float(min(1.0, e * 0.8 + boost)), 4)})
    # Strong cues are musical, not guessed: every section start (the arrangement changes there) and every 4-bar phrase
    # start inside a section (a natural place for the next reveal).
    strong = []
    bar = beat * 4
    for s in meta['sections']:
        if s['start'] > 0:
            strong.append({'time': round(s['start'], 4), 'intensity': 1.0, 'kind': 'strong_beat', 'section': s['name']})
        for k in range(4, s['bars'], 4):
            t = s['start'] + k * bar
            strong.append({'time': round(t, 4), 'intensity': round(min(0.95, 0.75 + 0.2 * energy(t) / (np.percentile(raw, 98) or 1)), 4),
                           'kind': 'phrase', 'section': s['name']})
    strong.sort(key=lambda c: c['time'])
    doc = {'schemaVersion': 1, 'source': {'filename': filename, 'trackStem': stem, 'generator': 'robin-video compose_music.py'},
           'duration': round(total, 3), 'tempo': float(bpm),
           'analysis': {'method': 'exact composition grid', 'sampleRate': SR},
           'scoring': {'intensityFormula': '0.8*normalized_rms_after_beat + 0.2*downbeat',
                       'note': 'strongCues = section starts (kind strong_beat, intensity 1.0) and 4-bar phrase starts (kind phrase).'},
           'sections': [{'name': s['name'], 'start': round(s['start'], 3), 'bars': s['bars']} for s in meta['sections']],
           'beats': beats, 'strongCues': strong}
    title, desc, use = DESCRIPTIONS[name]
    early = [f'{b["time"]:.2f}' for b in beats if b['time'] <= 25]
    md = [f'# Music Cues: {stem}', '', f'- Track: `{filename}` ({title}: {desc})', f'- Best for: {use}',
          f'- Duration: {total:.2f}s', f'- Tempo: {bpm} BPM (exact; the track was composed on this grid)', '- Planning window: 0.00-25.00s', '',
          '## Sections', '', *[f'- {s["name"]}: {s["start"]:.2f}s ({s["bars"]} bars)' for s in meta['sections']], '',
          '## Useful Beat Grid', '', ', '.join(early), '', '## Strong Cues', '',
          *[f'- {c["time"]:.2f}s — {"section start: " + c["section"] if c["kind"] == "strong_beat" else "phrase in " + c["section"]}' for c in strong], '',
          '## Use Policy', '',
          'Section starts are where the arrangement lifts: land the hook payoff, the key stat or the end card near one (within ~0.15s). '
          'Snap sequential reveals to the beat grid only when each item keeps its reading time.', '']
    return doc, '\n'.join(md)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--style', default='all', help='comma-separated styles or "all"')
    ap.add_argument('--seed', type=int, default=7, help='change for a different variation of the same style')
    a = ap.parse_args(argv)
    names = list(STYLES) if a.style == 'all' else [s.strip() for s in a.style.split(',')]
    (a.out / 'cues').mkdir(parents=True, exist_ok=True)
    for name in names:
        if name not in STYLES:
            raise SystemExit(f'Unknown style {name}. Choose from: {", ".join(STYLES)}')
        audio, meta = render(name, a.seed)
        stem = f'robin-{name}' if a.seed == 7 else f'robin-{name}-s{a.seed}'
        mp3 = a.out / f'{stem}.mp3'
        write_mp3(audio, mp3)
        doc, md = cues(audio, meta, stem, mp3.name, name)
        (a.out / 'cues' / f'{stem}.music-cues.json').write_text(json.dumps(doc, indent=1) + '\n', encoding='utf-8')
        (a.out / 'cues' / f'{stem}.music-cues.md').write_text(md, encoding='utf-8')
        print(f'{mp3.name}: {meta["total"]:.1f}s at {meta["bpm"]} BPM, {len(meta["sections"])} sections')


if __name__ == '__main__':
    main()
