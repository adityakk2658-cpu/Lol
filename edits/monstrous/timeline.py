"""Shared edit timeline: music grid, picture cuts/retimes, camera moves and FX cues.

Everything is in OUTPUT seconds unless a name says `src`.
Tempo 150 BPM -> beat 0.4 s, 16th 0.1 s, bar 1.6 s.
"""
import math

BPM = 150
BEAT = 60.0 / BPM          # 0.4
STEP = BEAT / 4            # 0.1  (16th note)
BAR = BEAT * 4             # 1.6
FPS = 60
OUT_W, OUT_H = 1080, 1920
DURATION = 14.8

# --- key moments in the source clip (synced to the video track) ---------------
SRC_TAP1 = 1.40
SRC_TAP2 = 2.355
SRC_PRE_CRACK = 5.999      # last frame before the lid breaks
SRC_POST_CRACK = 6.066     # first frame with the can open
SRC_END = 9.35
# where the original sounds live in the synced original audio (seconds)
ORIG_TAP1 = 1.398
ORIG_TAP2 = 2.383
ORIG_CRACK = 6.142         # peak of the "pssht" crack

# --- section markers (output time) ---------------------------------------------
T_TAP1, T_TAP2, T_TAP3 = 1.6, 2.4, 2.8
T_GROOVE = 3.2
T_BUILD = 4.8
T_GAP = 6.0
T_DROP = 6.4
T_CRACK2, T_CRACK3 = 6.8, 7.2
T_VELO = 8.0
T_CUTS = 9.6
T_CUT_CRACK = 10.8
T_HERO = 11.2
T_BREAK_END = 12.0
T_END_HIT = 12.8
T_OUTRO_TEXT = 13.2

# Focus point of interest in the source (relative coords) over source time.
FOCUS_KEYS = [
    (0.0, 0.50, 0.37), (2.6, 0.50, 0.37), (3.0, 0.47, 0.35), (3.6, 0.40, 0.32),
    (4.2, 0.45, 0.30), (4.6, 0.36, 0.29), (5.0, 0.49, 0.35), (5.4, 0.60, 0.32),
    (5.7, 0.69, 0.36), (5.95, 0.72, 0.39), (6.07, 0.58, 0.42), (6.6, 0.62, 0.43),
    (7.5, 0.37, 0.50), (8.2, 0.37, 0.50), (9.5, 0.36, 0.50),
]
EMITTER_SRC = (0.60, 0.41)   # mouth of the can at the moment it cracks


def focus_at(ts):
    k = FOCUS_KEYS
    if ts <= k[0][0]:
        return k[0][1], k[0][2]
    for (t0, x0, y0), (t1, x1, y1) in zip(k, k[1:]):
        if ts <= t1:
            u = (ts - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)
            return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    return k[-1][1], k[-1][2]


# --- easing -------------------------------------------------------------------
def lerp(a, b, u):
    return a + (b - a) * u


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def ease_in(u, p=2.0):
    return min(max(u, 0.0), 1.0) ** p


def ease_out(u, p=2.0):
    return 1 - (1 - min(max(u, 0.0), 1.0)) ** p


def velocity(u, cycles, k=0.75):
    """Speed-ramp map: speed peaks at every cycle start (on the beat), slow-mo between.
    Monotonic for k < 1."""
    return u + k * math.sin(2 * math.pi * cycles * u) / (2 * math.pi * cycles)


def keys(u, pts):
    """piecewise smooth interpolation through [(u, value), ...]"""
    if u <= pts[0][0]:
        return pts[0][1]
    for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
        if u <= u1:
            return lerp(v0, v1, smooth((u - u0) / (u1 - u0)))
    return pts[-1][1]


# --- picture segments ---------------------------------------------------------
# Each segment: out [t0, t1), source range [s0, s1] with a remap curve,
# a zoom curve, rotation, optional mirror / look tweaks and motion-blur shutter.
def seg(t0, t1, s0, s1, curve=None, zoom=((0, 1.1), (1, 1.1)), rot=((0, 0), (1, 0)),
        shutter=0.0, nsub=1, look=None, mirror=False, focus=None, interp=True):
    return dict(t0=t0, t1=t1, s0=s0, s1=s1, curve=curve or (lambda u: u), zoom=zoom,
                rot=rot, shutter=shutter, nsub=nsub, look=look or {}, mirror=mirror,
                focus=focus, interp=interp)


SEGMENTS = [
    # INTRO: moody slow push on the fist resting on the can
    seg(0.0, 1.6, 0.25, SRC_TAP1, zoom=((0, 1.12), (1, 1.32)), rot=((0, -1.5), (1, 0.5)),
        look=dict(grade="intro")),
    # TAP 1 -> TAP 2
    seg(1.6, 2.4, SRC_TAP1, SRC_TAP2, zoom=((0, 1.38), (1, 1.30)), look=dict(grade="cold")),
    # TAP 2 aftermath, then a double-take re-cut to land tap 3
    seg(2.4, 2.6, SRC_TAP2, SRC_TAP2 + 0.15, zoom=((0, 1.55), (1, 1.5)), rot=((0, 2), (1, 2)),
        look=dict(grade="cold")),
    seg(2.6, 2.8, SRC_TAP2 - 0.2, SRC_TAP2, zoom=((0, 1.85), (1, 1.95)), rot=((0, -3), (1, -3)),
        look=dict(grade="cold")),
    # WHIP: fast-forward into the grab, heavy motion blur
    seg(2.8, 3.2, SRC_TAP2, 3.5, curve=lambda u: ease_in(u, 2.2),
        zoom=((0, 1.4), (0.75, 1.15), (1, 1.12)), rot=((0, 0), (0.7, 3), (1, 0)),
        shutter=1.6, nsub=7, look=dict(grade="main")),
    # GROOVE: velocity ramps on every beat
    seg(3.2, 4.8, 3.5, 5.05, curve=lambda u: velocity(u, 4, 0.7),
        zoom=((0, 1.16), (0.5, 1.26), (1, 1.3)), rot=((0, 0), (1, -1)),
        shutter=0.9, nsub=4, look=dict(grade="main")),
    # BUILD: ramp into slow-mo while pushing into the tab
    seg(4.8, 6.0, 5.05, 5.955, curve=lambda u: ease_out(u, 1.8),
        zoom=((0, 1.32), (1, 2.05)), rot=((0, -1), (1, 1.5)), look=dict(grade="build")),
    # GAP: near freeze, maximum tension
    seg(6.0, 6.4, 5.955, SRC_PRE_CRACK, curve=lambda u: ease_out(u, 1.5),
        zoom=((0, 2.05), (1, 2.45)), rot=((0, 1.5), (1, 2.5)), look=dict(grade="gap")),
    # DROP: triple crack replay wide -> mid -> extreme close
    seg(6.4, 6.8, SRC_POST_CRACK, 6.27, curve=lambda u: ease_out(u, 1.4),
        zoom=((0, 1.22), (1, 1.32)), look=dict(grade="drop"), interp=True),
    seg(6.8, 7.2, SRC_POST_CRACK, 6.27, curve=lambda u: ease_out(u, 1.4),
        zoom=((0, 1.75), (1, 1.9)), rot=((0, -4), (1, -5)), look=dict(grade="drop")),
    seg(7.2, 7.6, SRC_POST_CRACK, 6.27, curve=lambda u: ease_out(u, 1.4),
        zoom=((0, 2.45), (1, 2.65)), rot=((0, 5), (1, 6)), look=dict(grade="drop")),
    # WHIP OUT
    seg(7.6, 8.0, 6.27, 6.75, curve=lambda u: ease_in(u, 1.6),
        zoom=((0, 2.6), (1, 1.18)), rot=((0, 6), (1, 0)), shutter=1.4, nsub=7,
        look=dict(grade="drop")),
    # VELOCITY: beat-locked speed ramps on the open can
    seg(8.0, 9.6, 6.75, 8.15, curve=lambda u: velocity(u, 4, 0.8),
        zoom=((0, 1.2), (1, 1.32)), shutter=0.9, nsub=4, look=dict(grade="drop")),
]

# FLASH-CUT montage: 8 cuts on 8th notes recapping the whole clip
_CUTS = [
    # src start, zoom, rot, mirror, look
    (0.30, 1.7, -2, False, dict(grade="drop", bw=True)),
    (SRC_TAP1 - 0.08, 1.45, 3, False, dict(grade="drop")),
    (3.55, 1.6, -4, True, dict(grade="drop", bw=True)),
    (4.45, 1.55, 2, False, dict(grade="drop")),
    (5.15, 1.9, -3, True, dict(grade="drop", bw=True)),
    (5.62, 2.2, 4, False, dict(grade="drop")),
    (SRC_POST_CRACK, 1.35, 0, False, dict(grade="drop", invert_frames=3)),
    (6.30, 1.8, -5, True, dict(grade="drop", bw=True)),
]
for _i, (_s, _z, _r, _m, _look) in enumerate(_CUTS):
    _t0 = T_CUTS + _i * 0.2
    SEGMENTS.append(seg(_t0, _t0 + 0.2, _s, _s + 0.2, zoom=((0, _z * 1.06), (1, _z)),
                        rot=((0, _r), (1, _r)), mirror=_m, look=_look))

SEGMENTS += [
    # HERO: slow push on the opened can, light sweep
    seg(T_HERO, T_END_HIT, 8.15, SRC_END, zoom=((0, 1.55), (1, 1.85)), rot=((0, -1), (1, 1)),
        look=dict(grade="hero"), focus=(0.39, 0.58)),
    # OUTRO: freeze and fade
    seg(T_END_HIT, DURATION + 0.01, SRC_END, SRC_END, zoom=((0, 1.85), (1, 1.6)),
        rot=((0, 1), (1, 0)), look=dict(grade="outro"), focus=(0.39, 0.58)),
]


def segment_at(t):
    for s in SEGMENTS:
        if s["t0"] <= t < s["t1"]:
            return s
    return SEGMENTS[-1]


# --- drum grid (shared with audio so picture hits land on drum hits) ------------
def bar_start(i):
    return i * BAR


KICK_A = [0, 6, 10]
KICK_B = [0, 8, 12]
CLAP = [4, 12]

DRUM_BARS = {
    # bar index: (kick steps, clap steps, hats style)
    2: (KICK_A, CLAP, "8ths"),
    4: (KICK_A, CLAP, "8ths+"),
    5: (KICK_B, CLAP, "rolls"),
    6: (KICK_A, CLAP, "16ths"),
}


def kick_times():
    ts = [T_TAP1, T_TAP2, T_TAP3]
    for b, (ks, _, _) in DRUM_BARS.items():
        ts += [bar_start(b) + k * STEP for k in ks]
    # build bar: four-on-the-floor for the first half
    ts += [T_BUILD + i * BEAT for i in range(2)]
    # hero bar second half + end hit
    ts += [T_BREAK_END, T_BREAK_END + 0.6, T_END_HIT]
    return sorted(set(round(t, 4) for t in ts))


def clap_times():
    ts = [T_TAP3]
    for b, (_, cs, _) in DRUM_BARS.items():
        ts += [bar_start(b) + c * STEP for c in cs]
    ts += [T_BREAK_END + 0.4]
    return sorted(set(round(t, 4) for t in ts))


CRACK_TIMES = [T_DROP, T_CRACK2, T_CRACK3, T_CUT_CRACK]
TEXT_SLAMS = [0.0, 0.8]
