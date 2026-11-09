"""Synthesize the BGM (dark phonk @150 BPM) + sound design, mixed against the picture cues.

usage: python3 make_audio.py <workdir>   -> <workdir>/mix.wav
"""
import os
import sys
import wave

import numpy as np
from scipy import signal

import timeline as TL

SR = 48000
DUR = TL.DURATION
N = int(SR * DUR)
rng = np.random.default_rng(7)


# ----------------------------------------------------------------- helpers ----
def tt(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rng.standard_normal(int(d * SR))


def sos(btype, f, order=2):
    return signal.butter(order, f, btype=btype, fs=SR, output="sos")


def filt(x, btype, f, order=2):
    return signal.sosfilt(sos(btype, f, order), x, axis=0)


def tv_filter(x, btype, fn, block=256, order=2):
    """time-varying butterworth; fn(t_seconds_array_start) -> cutoff (or (lo, hi))."""
    x = np.asarray(x, dtype=np.float64)
    out = np.zeros_like(x)
    zi = None
    for s in range(0, len(x), block):
        c = fn(s / SR)
        c = np.clip(c, 20, SR / 2 - 200)
        ss = sos(btype, c, order)
        if zi is None or zi.shape[0] != ss.shape[0]:
            zi = np.zeros((ss.shape[0], 2) + x.shape[1:])
        out[s:s + block], zi = signal.sosfilt(ss, x[s:s + block], axis=0, zi=zi)
    return out


def env_ad(t, a, d):
    return np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-np.maximum(t - a, 0) / d)


def pan2(x, p=0.0):
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1) * np.sqrt(2)


def place(bus, x, t, gain=1.0, pan=0.0):
    if x.ndim == 1:
        x = pan2(x, pan)
    i = int(round(t * SR))
    if i < 0:
        x = x[-i:]
        i = 0
    j = min(N, i + len(x))
    if j > i:
        bus[i:j] += x[:j - i] * gain


def normalize(x, peak=1.0):
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 0 else x


def make_ir(rt60, predelay=0.012, bright=0.5, length=None):
    length = length or rt60 * 1.3
    t = tt(length)
    ir = np.zeros((len(t), 2))
    for ch in range(2):
        n1 = rng.standard_normal(len(t)) * np.exp(-6.9 * t / (rt60 * 0.55))
        n2 = filt(rng.standard_normal(len(t)), "lowpass", 2500) * np.exp(-6.9 * t / rt60)
        ir[:, ch] = bright * n1 + (1 - bright) * n2 * 2.0
    pd = int(predelay * SR)
    ir = np.concatenate([np.zeros((pd, 2)), ir])
    # a few early reflections
    for k, (dt, g) in enumerate([(0.007, 0.5), (0.013, 0.35), (0.021, 0.3), (0.029, 0.2)]):
        ir[int(dt * SR), k % 2] += g * 8
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def reverb(x, ir, wet=1.0):
    if x.ndim == 1:
        x = pan2(x)
    y = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], axis=1)
    return y * wet


def pad_to(x, n):
    if len(x) >= n:
        return x[:n]
    pad = np.zeros((n - len(x),) + x.shape[1:])
    return np.concatenate([x, pad])


def square_bl(freq, t, fmax=14000):
    y = np.zeros_like(t)
    k = 1
    while k * freq < fmax:
        y += np.sin(2 * np.pi * k * freq * t) / k
        k += 2
    return y * 4 / np.pi


def saw(freq_t, t):
    ph = np.cumsum(np.broadcast_to(freq_t, t.shape)) / SR
    return 2 * (ph % 1.0) - 1


# ------------------------------------------------------------ instruments ----
def kick(punch=1.0):
    t = tt(0.5)
    f = 46 + 120 * np.exp(-t / 0.032) + 320 * np.exp(-t / 0.004)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t / 0.26) * np.minimum(t / 0.0015, 1)
    click = filt(noise(0.5), "highpass", 1800) * np.exp(-t / 0.003) * 0.6 * punch
    return np.tanh(2.2 * (body + click)) * 0.9


def clap():
    t = tt(0.6)
    n = filt(noise(0.6), "bandpass", [900, 6000])
    e = np.zeros_like(t)
    for d in (0.0, 0.009, 0.018, 0.027):
        e += np.where(t >= d, np.exp(-(t - d) / 0.0045), 0)
    e += np.where(t >= 0.03, np.exp(-(t - 0.03) / 0.13), 0) * 0.9
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05) * 0.6
    return np.tanh(1.5 * (n * e * 0.6 + body))


def snare(pitch=1.0, dec=0.09):
    t = tt(0.3)
    n = filt(noise(0.3), "bandpass", [1200, 9000]) * np.exp(-t / dec)
    body = np.sin(2 * np.pi * 210 * pitch * t * (1 + 0.4 * np.exp(-t / 0.01))) * np.exp(-t / 0.06)
    return np.tanh(1.4 * (0.7 * n + 0.7 * body))


HAT_FREQS = np.array([205.3, 304.4, 369.6, 522.7, 540.0, 800.0]) * 1.7


def hat(open_=False):
    d = 0.35 if open_ else 0.06
    t = tt(d)
    m = sum(np.sign(np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))) for f in HAT_FREQS)
    x = 0.5 * m / 6 + 0.8 * noise(d)
    x = filt(x, "highpass", 7000, 4)
    return x * np.exp(-t / (0.11 if open_ else 0.018))


def cowbell(freq, dur=0.32, bright=1.0):
    t = tt(dur)
    x = square_bl(freq, t) + 0.85 * square_bl(freq * 1.4815, t)
    x = filt(x, "bandpass", [450, 4200 * bright])
    e = 0.65 * np.exp(-t / 0.028) + 0.35 * np.exp(-t / 0.16)
    e *= np.minimum(t / 0.0008, 1)
    return np.tanh(2.4 * x * e) * 0.8


def boom(f0=58, f1=28, d=1.4):
    t = tt(d)
    f = f1 + (f0 - f1) * np.exp(-t / 0.25)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / (d * 0.35)) * np.minimum(t / 0.004, 1)
    thud = filt(noise(d), "lowpass", 220) * np.exp(-t / 0.06) * 1.5
    return np.tanh(1.6 * (y + thud))


def crash(d=2.2):
    t = tt(d)
    m = sum(np.sign(np.sin(2 * np.pi * f * 2.3 * t)) for f in HAT_FREQS)
    x = filt(0.4 * m / 6 + noise(d), "highpass", 3200, 2)
    return x * np.exp(-t / (d * 0.3)) * np.minimum(t / 0.002, 1)


def whoosh(d=0.45, f_lo=300, f_hi=5000, up=True):
    t = tt(d)
    u = t / d
    e = np.sin(np.pi * u) ** 2
    def fc(s):
        v = s / d
        v = v if up else 1 - v
        c = f_lo * (f_hi / f_lo) ** v
        return [c * 0.6, c * 1.6]
    x = tv_filter(noise(d), "bandpass", fc, block=128)
    x = x * e
    return np.stack([x * (1 - u) * 1.4, x * u * 1.4], axis=1)


def riser(d):
    t = tt(d)
    u = t / d
    def fc(s):
        c = 350 * (9000 / 350) ** (s / d)
        return [c * 0.7, c * 1.5]
    nz = tv_filter(noise(d), "bandpass", fc, block=128) * (u ** 2.2) * 1.3
    f = 140 * (1500 / 140) ** (u ** 1.3)
    vib = 1 + 0.012 * np.sin(2 * np.pi * (4 + 14 * u) * t)
    tone = saw(f * vib, t) * 0.25 + np.sin(2 * np.pi * np.cumsum(f * 1.5 * vib) / SR) * 0.3
    tone = filt(tone, "lowpass", 5000) * (u ** 2.5)
    x = nz + tone
    return np.stack([x * (1 + 0.15 * np.sin(9 * t)), x * (1 - 0.15 * np.sin(9 * t))], axis=1)


def reverse_swell(d=1.0):
    return crash(d * 1.4)[::-1][-int(d * SR):] * np.linspace(0.3, 1, int(d * SR)) ** 1.5


def glitch(d=0.25):
    t = tt(d)
    y = np.zeros_like(t)
    s = 0
    while s < len(t):
        L = min(int(rng.uniform(0.012, 0.04) * SR), len(t) - s)
        f = rng.choice([180, 360, 720, 1440, 2880, 95])
        seg = np.sign(np.sin(2 * np.pi * f * t[:L]))
        if rng.random() < 0.4:
            seg = rng.standard_normal(L)
        hold = int(rng.integers(4, 30))
        seg = np.repeat(seg[::hold], hold)[:L]
        y[s:s + len(seg)] = seg * rng.uniform(0.4, 1.0)
        s += L
    y = np.round(y * 6) / 6
    return filt(y, "highpass", 120) * 0.6


def zap(d=0.08):
    t = tt(d)
    buzz = square_bl(100, t, 6000) * 0.6 + noise(d) * 0.35
    buzz = filt(buzz, "bandpass", [80, 6000])
    return buzz * np.minimum(t / 0.002, 1) * np.exp(-t / (d * 0.7))


def shimmer(d=1.6):
    t = tt(d)
    y = np.zeros_like(t)
    for f, a in [(2637, 1.0), (3951, 0.7), (5274, 0.5), (7040, 0.35), (1318.5, 0.5)]:
        y += a * np.sin(2 * np.pi * f * t * (1 + 0.002 * np.sin(2 * np.pi * 5 * t)))
    y *= np.minimum(t / 0.004, 1) * np.exp(-t / 0.45)
    sweep = whoosh(0.35, 2000, 12000)[:, 0] * 0.5
    y[:len(sweep)] += sweep
    return y * 0.35


def heartbeat():
    t = tt(0.35)
    def thump(f):
        return np.sin(2 * np.pi * f * t * (1 + 0.5 * np.exp(-t / 0.02))) * np.exp(-t / 0.07)
    y = np.zeros(int(0.5 * SR))
    y[:len(t)] += thump(55)
    o = int(0.14 * SR)
    y[o:o + len(t)] += 0.7 * thump(50)[: len(y) - o]
    return np.tanh(2 * y)


def vinyl(d):
    t = tt(d)
    pops = (rng.random(len(t)) < 9 / SR) * rng.uniform(0.3, 1, len(t))
    pops = filt(pops, "bandpass", [800, 6000]) * 6
    hiss = filt(noise(d), "bandpass", [2000, 9000]) * 0.03
    return pops + hiss + 0.0 * t


# --------------------------------------------------------- original audio ----
def load_orig(work):
    a = np.fromfile(os.path.join(work, "orig_audio.f32"), dtype=np.float32).reshape(-1, 2)
    return a.astype(np.float64)


def snippet(orig, t_peak, pre, post):
    i0 = int((t_peak - pre) * SR)
    x = orig[i0:i0 + int((pre + post) * SR)].mean(axis=1)
    x = filt(x, "highpass", 90)
    n = len(x)
    fade = np.ones(n)
    fi = int(0.002 * SR)
    fo = int(0.06 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo)
    # downward expander to kill room noise
    env = np.sqrt(signal.lfilter([0.01], [1, -0.99], x ** 2) + 1e-12)
    thr = 0.12 * env.max()
    g = np.clip(env / thr, 0, 1) ** 1.5
    return normalize(x * fade * g)


def tap_hit(orig, t_peak):
    x = snippet(orig, t_peak, 0.02, 0.28)
    t = tt(len(x) / SR)
    clank = sum(a * np.sin(2 * np.pi * f * t) for f, a in
                [(1180, 1), (2870, .7), (4310, .5), (6120, .35), (8800, .2)])
    clank *= np.exp(-t / 0.09) * np.minimum(t / 0.001, 1)
    thud = np.sin(2 * np.pi * 72 * t * (1 + 0.6 * np.exp(-t / 0.01))) * np.exp(-t / 0.11)
    return np.tanh(1.3 * (0.9 * x + 0.35 * clank + 0.9 * thud))


def crack_hit(orig):
    x = snippet(orig, TL.ORIG_CRACK, 0.03, 0.65)
    t = tt(len(x) / SR)
    snap = filt(noise(len(x) / SR), "highpass", 2500) * np.exp(-t / 0.004) * 0.9
    fz = filt(noise(len(x) / SR), "bandpass", [2600, 11000])
    crackle = filt((rng.random(len(t)) < 900 / SR).astype(float), "lowpass", 3000) * 30
    fizz = fz * (0.6 + crackle) * np.minimum(t / 0.006, 1) * np.exp(-t / 0.28) * 0.5
    snap = np.roll(snap, int(0.025 * SR))
    fizz = np.roll(fizz, int(0.025 * SR))
    return np.tanh(1.2 * (1.0 * x + snap + fizz))


# ------------------------------------------------------------------- music ----
FS = 46.249  # F#1
ROOT_CB = 739.99  # F#5 (cowbell)

MEL_A = [(0, 0), (3, 0), (6, 3), (8, 0), (10, 7), (11, 5), (14, 3)]
MEL_B = [(0, 0), (3, 0), (6, 3), (8, 8), (10, 7), (12, 5), (14, 1)]
BASS_A = [(0, 0, 6), (6, 0, 4), (10, 3, 6)]
BASS_B = [(0, 8, 8), (8, 7, 4), (12, 3, 4)]


def semi(f, s):
    return f * 2 ** (s / 12)


def build_808(events):
    """events: list of (t_start, semitone, dur, glide_from_prev)"""
    freq = np.full(N, semi(FS, 0))
    amp = np.zeros(N)
    prev_f = None
    for (t0, s, d, glide) in events:
        i0, i1 = int(t0 * SR), min(N, int((t0 + d) * SR))
        f = semi(FS, s)
        L = i1 - i0
        tl = np.arange(L) / SR
        if glide and prev_f is not None:
            fr = f + (prev_f - f) * np.exp(-tl / 0.035)
        else:
            fr = f * (1 + 0.35 * np.exp(-tl / 0.012))
        freq[i0:i1] = fr
        a = np.minimum(tl / 0.003, 1) * np.where(tl > d - 0.05, np.clip((d - tl) / 0.05, 0, 1), 1)
        a *= 0.85 + 0.15 * np.exp(-tl / 0.3)
        amp[i0:i1] = np.maximum(amp[i0:i1], a)
        prev_f = f
    ph = 2 * np.pi * np.cumsum(freq) / SR
    x = np.sin(ph)
    y = np.tanh(3.2 * x) * 0.75 + 0.35 * np.tanh(9 * np.sin(2 * ph)) * 0.25 + 0.4 * x
    y = filt(y, "lowpass", 2600)
    return y * amp


def main(work):
    orig = load_orig(work)
    music = np.zeros((N, 2))
    drums = np.zeros((N, 2))
    sfx = np.zeros((N, 2))
    verb_send = np.zeros((N, 2))
    big_send = np.zeros((N, 2))

    B, S = TL.BAR, TL.STEP

    # ---- cowbell melody (bars 0..7) ----
    cb = np.zeros((N, 2))
    for bar in range(8):
        mel = MEL_A if bar % 2 == 0 else MEL_B
        for step, s in mel:
            t0 = bar * B + step * S
            if TL.T_GAP <= t0 < TL.T_DROP:
                continue
            if TL.T_HERO <= t0 < TL.T_BREAK_END and step not in (0, 8):
                continue
            f = semi(ROOT_CB, s)
            note = cowbell(f)
            pan = -0.25 if step % 4 == 0 else 0.25
            place(cb, note, t0, 0.55, pan)
            if bar >= 4:  # octave doubling on the drop for weight
                place(cb, cowbell(f / 2, bright=0.6), t0, 0.28, -pan)
    # ping-pong delay (dotted 8th)
    dly = int(0.3 * SR)
    cbd = np.zeros_like(cb)
    fb = cb.copy()
    for k in range(1, 4):
        sh = np.zeros_like(cb)
        sh[dly * k:] = fb[:-dly * k] * (0.33 ** k)
        sh = sh[:, ::-1] if k % 2 else sh
        cbd += sh
    cb = cb + filt(cbd, "lowpass", 3500)
    # filter automation: underwater intro, opening on taps, high-pass build
    def cb_lp(t):
        if t < TL.T_TAP1:
            return 650
        if t < TL.T_GROOVE:
            return 650 * (12000 / 650) ** ((t - TL.T_TAP1) / (TL.T_GROOVE - TL.T_TAP1))
        if TL.T_HERO <= t < TL.T_BREAK_END:
            return 1800
        return 15000
    cb = tv_filter(cb, "lowpass", cb_lp)
    def cb_hp(t):
        if TL.T_BUILD <= t < TL.T_GAP:
            return 40 * (900 / 40) ** ((t - TL.T_BUILD) / (TL.T_GAP - TL.T_BUILD))
        return 30
    cb = tv_filter(cb, "highpass", cb_hp)
    music += cb * 0.9
    verb_send += cb * 0.25

    # ---- pad (F#m) ----
    t = np.arange(N) / SR
    pad = np.zeros(N)
    for f in [semi(FS * 2, 0), semi(FS * 2, 7), semi(FS * 4, 0), semi(FS * 4, 3), semi(FS * 4, 7)]:
        for dt in (-0.12, -0.05, 0.0, 0.06, 0.11):
            pad += saw(f * 2 ** (dt / 12), t)
    pad = filt(pad, "lowpass", 1100) / 25
    pad_env = np.interp(t, [0, 0.5, 4.6, 5.6, TL.T_DROP, TL.T_HERO, TL.T_HERO + 0.3, TL.T_BREAK_END,
                            TL.T_END_HIT, TL.T_END_HIT + 0.05],
                        [0, 1, 0.8, 0, 0, 0.25, 0.9, 0.5, 0.4, 0])
    pad = pad * pad_env
    music += np.stack([pad * 0.9, np.roll(pad, 480) * 0.9], axis=1) * 0.55
    verb_send += pan2(pad) * 0.2

    # ---- clean sub on the groove, distorted 808 on the drop ----
    sub_ev, ev808 = [], []
    for bar in (2, 3):
        pat = BASS_A if bar % 2 == 0 else BASS_B
        for step, s, d in pat:
            t0 = bar * B + step * S
            if t0 >= TL.T_GAP:
                continue
            sub_ev.append((t0, s, min(d * S, TL.T_GAP - t0), False))
    for bar in range(4, 8):
        pat = BASS_A if bar % 2 == 0 else BASS_B
        for step, s, d in pat:
            t0 = bar * B + step * S
            ev808.append((t0, s, d * S, step != 0))
    ev808.append((TL.T_END_HIT, 0, 1.4, False))
    sub = build_808(sub_ev)
    sub = filt(sub, "lowpass", 160) * 0.55
    b808 = build_808(ev808)
    music += pan2(sub) * 0.8 + pan2(b808) * 0.62

    # ---- drums ----
    kicks = TL.kick_times()
    for kt in kicks:
        if kt in (TL.T_TAP1, TL.T_TAP2, TL.T_TAP3):
            place(drums, kick(0.6), kt, 0.75)
        else:
            place(drums, kick(), kt, 0.95)
    for ct in TL.clap_times():
        c = clap()
        place(drums, c, ct, 0.5)
        place(verb_send, c, ct, 0.22)
    # hats
    def hats(t0, t1, every, gain=0.22, roll_at=None):
        tt_ = t0
        k = 0
        while tt_ < t1 - 1e-6:
            g = gain * (1.0 if k % 2 == 0 else 0.65)
            place(drums, hat(), tt_, g, 0.3 if k % 2 else -0.15)
            tt_ += every
            k += 1
    hats(TL.T_TAP1, TL.T_GROOVE, 0.2, 0.12)
    hats(TL.T_GROOVE, TL.T_GROOVE + B, 0.2, 0.2)
    hats(TL.T_BUILD, TL.T_BUILD + 0.8, 0.2, 0.18)
    hats(TL.T_DROP, TL.T_DROP + B - 0.2, 0.2, 0.22)
    # triplet roll into bar 5
    for k in range(6):
        place(drums, hat(), TL.T_VELO - 0.2 + k * (0.2 / 6), 0.14 + 0.02 * k, 0.4)
    hats(TL.T_VELO, TL.T_VELO + B - 0.4, 0.2, 0.22)
    for k in range(8):
        place(drums, hat(), TL.T_VELO + B - 0.4 + k * 0.05, 0.12 + 0.015 * k, -0.3 + 0.08 * k)
    hats(TL.T_CUTS, TL.T_HERO, 0.1, 0.17)
    hats(TL.T_BREAK_END, TL.T_END_HIT - 0.4, 0.1, 0.17)
    for k in range(8):
        place(drums, hat(), TL.T_END_HIT - 0.4 + k * 0.05, 0.13 + 0.02 * k, 0.0)
    for ot in [TL.T_DROP + 1.4, TL.T_VELO + 0.6, TL.T_VELO + 1.4, TL.T_CUTS + 0.6, TL.T_CUTS + 1.4]:
        place(drums, hat(True), ot, 0.16, 0.35)
    # snare build roll
    roll = [(TL.T_BUILD, 0.4), (TL.T_BUILD + 0.4, 0.2), (TL.T_BUILD + 0.8, 0.1),
            (TL.T_BUILD + 1.0, 0.05)]
    k = 0
    for (rs, step) in roll:
        end = rs + (0.4 if step == 0.4 else (0.4 if step == 0.2 else 0.2))
        tt_ = rs
        while tt_ < end - 1e-6 and tt_ < TL.T_GAP:
            u = (tt_ - TL.T_BUILD) / (TL.T_GAP - TL.T_BUILD)
            sn = snare(1 + 0.6 * u)
            place(drums, sn, tt_, 0.18 + 0.4 * u ** 1.5, rng.uniform(-0.2, 0.2))
            place(verb_send, sn, tt_, 0.1 + 0.2 * u)
            tt_ += step
            k += 1
    # break fill before the end hit
    for k in range(4):
        place(drums, snare(1.2 + 0.1 * k), TL.T_END_HIT - 0.4 + k * 0.1, 0.3 + 0.08 * k)

    # sidechain duck for music on every kick
    duck = np.ones(N)
    for kt in kicks:
        i = int(kt * SR)
        L = int(0.35 * SR)
        tl = np.arange(L) / SR
        g = 1 - 0.55 * np.exp(-tl / 0.09) * np.minimum(tl / 0.004, 1)
        j = min(N, i + L)
        duck[i:j] = np.minimum(duck[i:j], g[:j - i])
    music *= duck[:, None]

    music += drums

    # ---- build automation on the music bus: high-pass sweep, then hard mute for the gap ----
    def bus_hp(t):
        if TL.T_BUILD <= t < TL.T_GAP:
            return 25 * (450 / 25) ** ((t - TL.T_BUILD) / (TL.T_GAP - TL.T_BUILD))
        return 20
    music = tv_filter(music, "highpass", bus_hp)
    gate = np.ones(N)
    i0, i1 = int(TL.T_GAP * SR), int(TL.T_DROP * SR)
    gate[i0:i1] = 0
    gate[i0 - 240:i0] = np.linspace(1, 0, 240)
    music *= gate[:, None]

    # ---- intro low-pass on the whole music bus ("underwater" until the taps) ----
    def intro_lp(t):
        if t < TL.T_TAP1 - 0.05:
            return 900
        if t < TL.T_GROOVE:
            return 900 * (18000 / 900) ** ((t - TL.T_TAP1 + 0.05) / (TL.T_GROOVE - TL.T_TAP1 + 0.05))
        return 20000
    music = tv_filter(music, "lowpass", intro_lp)

    # ----------------------------------------------------- sound design -----
    # intro: flicker zaps, text slams, vinyl, reverse swell into the taps
    from fxcues import FLICKER_ON
    for t0, d in FLICKER_ON:
        place(sfx, zap(max(d, 0.04)), t0, 0.22, rng.uniform(-0.3, 0.3))
    place(sfx, pan2(vinyl(TL.T_GROOVE)), 0.0, 0.5)
    for i, ts in enumerate(TL.TEXT_SLAMS):
        place(sfx, boom(62, 30, 1.6), ts, 0.95)
        place(big_send, boom(62, 30, 0.5), ts, 0.3)
        place(sfx, clap(), ts, 0.25)
        place(big_send, clap(), ts, 0.5)
    place(sfx, glitch(0.22), TL.TEXT_SLAMS[1], 0.4)
    place(sfx, glitch(0.18), 1.3, 0.25)
    rs = reverse_swell(0.75)
    place(sfx, pan2(rs), TL.T_TAP1 - 0.75, 0.35)

    # taps
    for tt_, src in [(TL.T_TAP1, TL.ORIG_TAP1), (TL.T_TAP2, TL.ORIG_TAP2), (TL.T_TAP3, TL.ORIG_TAP2)]:
        h = tap_hit(orig, src)
        place(sfx, h, tt_ - 0.02, 0.85)
        place(big_send, h, tt_ - 0.02, 0.35)
        place(sfx, boom(70, 35, 0.6), tt_, 0.5)
    place(sfx, whoosh(0.42, 250, 7000), TL.T_TAP3 + 0.02, 0.6)
    place(sfx, whoosh(0.3, 400, 6000, up=False), TL.T_GROOVE - 0.05, 0.3)

    # build: riser + rumble, gap: heartbeat + reverse crack
    place(sfx, riser(TL.T_GAP - TL.T_BUILD + 0.05), TL.T_BUILD, 0.42)
    t_r = tt(TL.T_DROP - TL.T_BUILD)
    rumble = filt(noise(len(t_r) / SR), "lowpass", 90) * (t_r / t_r[-1]) ** 2 * 1.8
    place(sfx, pan2(rumble), TL.T_BUILD, 0.6)
    place(sfx, pan2(heartbeat()), TL.T_GAP + 0.01, 0.8)
    ch = crack_hit(orig)
    rev_ir = make_ir(1.8, bright=0.6)
    crack_tail = reverb(pad_to(ch, len(ch) + int(1.6 * SR)), rev_ir)
    rev = crack_tail[::-1]
    rev = rev[-int(0.75 * SR):]
    rev = rev * np.linspace(0, 1, len(rev))[:, None] ** 2
    place(sfx, rev, TL.T_DROP - len(rev) / SR, 0.55)
    place(sfx, pan2(reverse_swell(0.4)), TL.T_DROP - 0.4, 0.3)

    # drop: crack x3 + flash-cut crack
    for i, ct in enumerate(TL.CRACK_TIMES):
        g = [1.0, 0.85, 0.85, 0.7][i]
        place(sfx, ch, ct - 0.03, g)
        place(big_send, ch, ct - 0.03, 0.45 * g)
        place(sfx, boom(60, 26, 1.6 if i == 0 else 0.8), ct, [1.0, 0.6, 0.65, 0.5][i])
        if i == 0:
            place(sfx, crash(2.6), ct, 0.35)
            place(big_send, crash(1.5), ct, 0.25)
    place(sfx, glitch(0.2), TL.T_CRACK3, 0.35)
    place(sfx, whoosh(0.45, 6000, 300, up=False), TL.T_CRACK3 + 0.35, 0.55)
    place(sfx, whoosh(0.35, 300, 6000), TL.T_VELO - 0.3, 0.3)

    # flash cuts: alternating swishes + shutter ticks
    for k in range(8):
        tc = TL.T_CUTS + 0.2 * k
        sw = whoosh(0.12, 1500, 9000)
        if k % 2:
            sw = sw[:, ::-1]
        place(sfx, sw, tc - 0.04, 0.35)
        tick = filt(noise(0.01), "highpass", 4000) * np.exp(-tt(0.01) / 0.002)
        place(sfx, tick, tc, 0.4, -0.4 if k % 2 else 0.4)
    place(sfx, glitch(0.15), TL.T_CUTS + 1.4, 0.3)

    # hero: big whoosh in, glint shimmer on the light sweep
    place(sfx, whoosh(0.5, 200, 4000, up=False), TL.T_HERO - 0.1, 0.5)
    place(sfx, boom(55, 30, 1.2), TL.T_HERO, 0.55)
    from fxcues import SWEEP_T0
    sh = shimmer()
    place(sfx, sh, SWEEP_T0 + 0.12, 0.85, -0.3)
    place(big_send, sh, SWEEP_T0 + 0.12, 0.5)

    # end hit + outro
    place(sfx, boom(64, 24, 2.4), TL.T_END_HIT, 1.0)
    place(sfx, crash(3.0), TL.T_END_HIT, 0.4)
    place(big_send, crash(2.0), TL.T_END_HIT, 0.25)
    place(sfx, glitch(0.25), TL.T_END_HIT + 0.02, 0.25)
    place(sfx, pan2(reverse_swell(0.5)), TL.T_OUTRO_TEXT - 0.5, 0.3)
    place(sfx, boom(50, 28, 2.0), TL.T_OUTRO_TEXT, 0.6)
    place(sfx, sh, TL.T_OUTRO_TEXT + 0.05, 0.5, 0.3)
    place(big_send, sh, TL.T_OUTRO_TEXT + 0.05, 0.6)

    # ---- tape stop on the music bus at the end ----
    ts0, ts1 = TL.T_END_HIT + 0.18, TL.T_END_HIT + 1.0
    i0, i1 = int(ts0 * SR), int(ts1 * SR)
    u = np.linspace(0, 1, i1 - i0)
    rate = (1 - u) ** 1.6
    pos = i0 + np.cumsum(rate)
    stopped = np.stack([np.interp(pos, np.arange(N), music[:, c]) for c in range(2)], axis=1)
    stopped *= np.linspace(1, 0.0, len(u))[:, None] ** 0.5
    music[i0:i1] = stopped
    music[i1:] = 0

    # ---- reverbs ----
    room = make_ir(1.1, bright=0.55)
    hall = make_ir(2.6, predelay=0.02, bright=0.45)
    wet = reverb(verb_send, room) * 0.35 + reverb(big_send, hall) * 0.5
    wet = filt(wet, "highpass", 150)
    # music reverb stops with the tape stop, sfx reverb tails ring out
    mix = music + sfx + wet

    # ---- master: glue comp -> soft clip -> limiter ----
    mix = filt(mix, "highpass", 25)
    mono = np.abs(mix).max(axis=1)
    env = np.sqrt(signal.lfilter([1 - 0.9993], [1, -0.9993], mono ** 2) + 1e-9)
    thr = 0.25
    gr = np.where(env > thr, (env / thr) ** (1 / 2.5 - 1), 1.0)
    mix *= gr[:, None]
    # loudness: aim the drop around -9 dBFS RMS before the limiter
    d0, d1 = int(TL.T_DROP * SR), int(TL.T_HERO * SR)
    rms = np.sqrt(np.mean(mix[d0:d1] ** 2))
    mix *= 10 ** (-8.5 / 20) / rms
    mix = np.tanh(mix * 1.05) / 1.05 * 1.0
    ceiling = 10 ** (-1.0 / 20)
    peak = np.abs(mix).max(axis=1)
    from scipy.ndimage import maximum_filter1d
    la = int(0.002 * SR)
    pk = maximum_filter1d(peak, size=2 * la + 1)
    g = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    g = signal.lfilter([1 - 0.995], [1, -0.995], np.r_[g[:1].repeat(1), g])[1:]
    g = np.minimum(g, np.minimum(1.0, ceiling / np.maximum(pk, 1e-9)) * 1.0 + 0.0)
    mix *= g[:, None]
    mix = np.clip(mix, -ceiling, ceiling)
    # fade at the very end
    fo = int(0.6 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2

    out = os.path.join(work, "mix.wav")
    pcm = (mix * 32767).astype("<i2")
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", out, f"peak={np.abs(mix).max():.3f}",
          f"drop rms={20*np.log10(np.sqrt(np.mean(mix[d0:d1]**2))):.1f} dBFS")


if __name__ == "__main__":
    main(sys.argv[1])
