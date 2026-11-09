"""Frame-by-frame renderer: retime + optical-flow slow-mo + virtual camera + grade + FX + type.

usage:
  python3 render.py <workdir> video            -> <workdir>/video.mp4 (60 fps, no audio)
  python3 render.py <workdir> stills t1,t2,... -> <workdir>/stills/*.jpg
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import fxcues as FX
import timeline as TL

cv2.setNumThreads(1)
W, H = TL.OUT_W, TL.OUT_H
FPS = TL.FPS
NFRAMES = int(round(TL.DURATION * FPS))
FONT_BLACK_IT = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_MED = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
NEON = np.array([0.42, 1.0, 0.30], np.float32)

G = {}  # per-process globals


# ------------------------------------------------------------------ setup ----
def init(work):
    meta = json.load(open(os.path.join(work, "frames.json")))
    G["SW"], G["SH"], G["NF"] = meta["w"], meta["h"], meta["n"]
    G["PTS"] = np.array(meta["pts"])
    G["FD"] = meta["flow_div"]
    G["frames"] = np.memmap(os.path.join(work, "frames.rgb"), dtype=np.uint8, mode="r").reshape(
        G["NF"], G["SH"], G["SW"], 3)
    G["fwd"] = np.load(os.path.join(work, "flow_fwd.npy"), mmap_mode="r")
    G["bwd"] = np.load(os.path.join(work, "flow_bwd.npy"), mmap_mode="r")
    # no interpolation across the lid-break (dropped frame + huge motion)
    G["cut_pairs"] = {int(np.argmin(np.abs(G["PTS"] - TL.SRC_PRE_CRACK)))}
    xs = np.arange(W, dtype=np.float32) - W / 2 + 0.5
    ys = np.arange(H, dtype=np.float32) - H / 2 + 0.5
    G["X"], G["Y"] = np.meshgrid(xs, ys)
    G["PX"], G["PY"] = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    r = np.sqrt((G["X"] / (W * 0.62)) ** 2 + (G["Y"] / (H * 0.6)) ** 2)
    G["vig"] = np.clip(1 - r ** 2.4 * 0.85, 0, 1).astype(np.float32)
    rng = np.random.default_rng(3)
    grains = []
    for _ in range(8):
        g = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
        g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
        g += 0.5 * rng.standard_normal((H, W)).astype(np.float32)
        grains.append(g)
    G["grain"] = grains
    G["texts"] = build_texts()
    G["particles"] = {b[0]: make_particles(b[1], b[2]) for b in FX.BURSTS}


# ------------------------------------------------------------- time/camera ----
def env_decay(t, t0, decay):
    if t < t0:
        return 0.0
    return math.exp(-(t - t0) / decay)


def punch(t):
    z = 1.0
    for t0, amt, dec in FX.PUNCHES:
        if t0 - 0.03 <= t < t0 + 1.0:
            if t < t0:  # tiny anticipation pull-back
                z *= 1 - amt * 0.25 * (1 - (t0 - t) / 0.03)
            else:
                z *= 1 + amt * math.exp(-(t - t0) / dec)
    return z


def noise1(t, seed):
    return (math.sin(t * 1.0 + seed) * 0.5 + math.sin(t * 2.31 + seed * 1.7) * 0.3
            + math.sin(t * 4.79 + seed * 2.9) * 0.2)


def shake(t):
    dx = dy = dr = 0.0
    for t0, amp, dec, freq in FX.SHAKES:
        if t0 <= t < t0 + dec * 5:
            e = amp * math.exp(-(t - t0) / dec)
            w = 2 * math.pi * freq * (t - t0)
            dx += e * noise1(w, t0 * 13)
            dy += e * noise1(w, t0 * 29 + 4)
            dr += e * 0.05 * noise1(w * 0.8, t0 * 7 + 9)
    ra = FX.rumble_amp(t)
    if ra:
        w = 2 * math.pi * 23 * t
        dx += ra * noise1(w, 1.1)
        dy += ra * noise1(w, 5.3)
        dr += ra * 0.03 * noise1(w, 8.8)
    return dx, dy, dr


def camera(t):
    seg = TL.segment_at(t)
    span = max(seg["t1"] - seg["t0"], 1e-6)
    u = min(max((t - seg["t0"]) / span, 0.0), 1.0)
    s = seg["curve"](u)
    ts = seg["s0"] + (seg["s1"] - seg["s0"]) * s
    z = TL.keys(u, seg["zoom"]) * punch(t)
    rot = TL.keys(u, seg["rot"])
    dx, dy, dr = shake(t)
    fx, fy = seg["focus"] or TL.focus_at(ts)
    return dict(seg=seg, u=u, ts=ts, z=z, rot=rot + dr, sx=dx, sy=dy, fx=fx, fy=fy,
                mirror=seg["mirror"])


def affine(cam):
    """2x3 matrix mapping output pixel -> source pixel."""
    SW, SH = G["SW"], G["SH"]
    k = (SW / cam["z"]) / W
    hw, hh = k * W / 2, k * H / 2
    cx = min(max(cam["fx"] * SW, hw), SW - hw)
    cy = min(max(cam["fy"] * SH, hh), SH - hh)
    th = math.radians(cam["rot"])
    c, s = math.cos(th) * k, math.sin(th) * k
    m = -1.0 if cam["mirror"] else 1.0
    # q = p - center + shake ; src = R*S*(mirror*q) + C
    ox, oy = -W / 2 + cam["sx"], -H / 2 + cam["sy"]
    A = np.array([[c * m, -s, c * m * ox - s * oy + cx],
                  [s * m, c, s * m * ox + c * oy + cy]], np.float64)
    return A


def to_out(A, px, py):
    Ai = cv2.invertAffineTransform(A)
    return Ai[0, 0] * px + Ai[0, 1] * py + Ai[0, 2], Ai[1, 0] * px + Ai[1, 1] * py + Ai[1, 2]


def locate(ts):
    P = G["PTS"]
    i = int(np.searchsorted(P, ts, side="right") - 1)
    i = min(max(i, 0), G["NF"] - 2)
    a = (ts - P[i]) / (P[i + 1] - P[i])
    return i, float(min(max(a, 0.0), 1.0))


def sample(ts, A, interp=True):
    i, a = locate(ts)
    PX, PY = G["PX"], G["PY"]
    mx = (A[0, 0] * PX + A[0, 1] * PY + A[0, 2]).astype(np.float32)
    my = (A[1, 0] * PX + A[1, 1] * PY + A[1, 2]).astype(np.float32)
    fr = G["frames"]
    if not interp or a < 0.04 or a > 0.96 or i in G["cut_pairs"]:
        j = i if a < 0.5 else i + 1
        return cv2.remap(np.asarray(fr[j]), mx, my, cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_REFLECT101).astype(np.float32)
    FD = G["FD"]
    fxm, fym = mx / FD, my / FD
    F = cv2.remap(np.asarray(G["fwd"][i], dtype=np.float32), fxm, fym, cv2.INTER_LINEAR,
                  borderMode=cv2.BORDER_REPLICATE) * FD
    B = cv2.remap(np.asarray(G["bwd"][i], dtype=np.float32), fxm, fym, cv2.INTER_LINEAR,
                  borderMode=cv2.BORDER_REPLICATE) * FD
    I0 = cv2.remap(np.asarray(fr[i]), mx - a * F[..., 0], my - a * F[..., 1], cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_REFLECT101).astype(np.float32)
    I1 = cv2.remap(np.asarray(fr[i + 1]), mx - (1 - a) * B[..., 0], my - (1 - a) * B[..., 1],
                   cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101).astype(np.float32)
    return I0 * (1 - a) + I1 * a


def render_plate(t):
    cam = camera(t)
    seg = cam["seg"]
    n, sh = seg["nsub"], seg["shutter"]
    if n <= 1 or sh <= 0:
        A = affine(cam)
        return sample(cam["ts"], A, seg["interp"]) / 255.0, cam, A
    acc = None
    lo, hi = seg["t0"], seg["t1"] - 1e-4
    for k in range(n):
        tk = t + (k / (n - 1) - 0.5) * sh / FPS
        tk = min(max(tk, lo), hi)
        ck = camera(tk)
        img = sample(ck["ts"], affine(ck), seg["interp"])
        acc = img if acc is None else acc + img
    return acc / (n * 255.0), cam, affine(cam)


# ------------------------------------------------------------------- grade ----
LOOKS = {
    #        exp   con   sat   spot  vig   bloom  shadow tint            highlight tint
    "intro": (0.78, 1.55, 0.50, 0.70, 0.80, 0.30, (-0.030, 0.010, 0.050), (0.00, 0.010, 0.030)),
    "cold": (0.86, 1.50, 0.62, 0.60, 0.70, 0.30, (-0.030, 0.012, 0.050), (0.00, 0.010, 0.025)),
    "main": (0.92, 1.45, 0.88, 0.50, 0.60, 0.30, (-0.030, 0.018, 0.035), (0.025, 0.010, -0.010)),
    "build": (0.88, 1.50, 0.80, 0.60, 0.70, 0.35, (-0.030, 0.018, 0.045), (0.010, 0.010, 0.000)),
    "gap": (0.80, 1.70, 0.40, 0.75, 0.90, 0.40, (-0.030, 0.020, 0.050), (0.00, 0.010, 0.020)),
    "drop": (0.95, 1.55, 1.05, 0.50, 0.62, 0.45, (-0.035, 0.030, 0.025), (0.020, 0.010, -0.005)),
    "hero": (0.90, 1.50, 0.92, 0.68, 0.75, 0.45, (-0.030, 0.018, 0.050), (0.010, 0.015, 0.025)),
    "outro": (0.90, 1.50, 0.92, 0.68, 0.75, 0.45, (-0.030, 0.018, 0.050), (0.010, 0.015, 0.025)),
}


def look_params(t, cam):
    seg = cam["seg"]
    name = seg["look"].get("grade", "main")
    p = list(LOOKS[name])
    u = cam["u"]
    if name == "build":   # drain colour and close in as tension rises
        p[0] *= 1 - 0.12 * u
        p[2] *= 1 - 0.45 * u
        p[1] *= 1 + 0.12 * u
        p[4] = p[4] + 0.2 * u
    if name == "outro":
        k = TL.smooth((t - TL.T_END_HIT - 0.15) / 0.5)
        p[2] *= 1 - k
        p[0] *= 1 - 0.78 * k
        if t > TL.DURATION - 1.0:
            p[0] *= max(0.0, (TL.DURATION - 0.25 - t) / 0.75)
    return p


def aces(x):
    return np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0, 1)


def scurve(x, g):
    x = np.clip(x, 1e-4, 1 - 1e-4)
    a = np.power(x, g)
    return a / (a + np.power(1 - x, g))


def grade(img, t, cam, A):
    exp_, con, sat, spot, vig, bloom, sh_t, hi_t = look_params(t, cam)
    seg = cam["seg"]
    img = scurve(img * exp_, con).astype(np.float32)
    lum = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722
    img = lum[..., None] + (img - lum[..., None]) * sat
    l2 = lum[..., None]
    img = img + (1 - l2) ** 2 * np.array(sh_t, np.float32) + l2 ** 2 * np.array(hi_t, np.float32)
    # spotlight relight: keep the subject, sink the room into shadow
    fxo, fyo = to_out(A, cam["fx"] * G["SW"], cam["fy"] * G["SH"])
    sw, shh = W // 8, H // 8
    xs = (np.arange(sw, dtype=np.float32) + 0.5) * 8 - fxo
    ys = (np.arange(shh, dtype=np.float32) + 0.5) * 8 - fyo
    m = np.exp(-(xs[None, :] ** 2 / (2 * 460 ** 2) + ys[:, None] ** 2 / (2 * 640 ** 2)))
    m = cv2.resize(m.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    img = img * (1 - spot * (1 - m) * 0.9 + 0.06 * spot * m)[..., None]
    img = np.clip(img, 0, None)
    if seg["look"].get("bw"):
        l3 = img[..., 0] * 0.3 + img[..., 1] * 0.59 + img[..., 2] * 0.11
        l3 = scurve(np.clip(l3, 0, 1), 1.35)
        img = np.repeat(l3[..., None], 3, axis=2) * np.array([0.97, 1.0, 1.03], np.float32)
    return img.astype(np.float32), vig, bloom, (fxo, fyo)


# -------------------------------------------------------------- particles ----
def make_particles(seed, n):
    r = np.random.default_rng(seed)
    ang = -math.pi / 2 + r.normal(0, 0.75, n) + 0.25
    spd = r.uniform(400, 2300, n) * (0.4 + 0.6 * r.random(n) ** 0.5)
    life = r.uniform(0.25, 0.85, n)
    size = r.uniform(2.5, 7.5, n)
    bri = r.uniform(0.5, 1.0, n)
    delay = r.uniform(0, 0.06, n)
    return dict(vx=np.cos(ang) * spd, vy=np.sin(ang) * spd, life=life, size=size, bri=bri,
                delay=delay)


def draw_particles(t, emit_xy, z):
    layer = None
    if t >= TL.T_HERO:
        return None
    for t0, seed, n in FX.BURSTS:
        age0 = t - t0
        if not (0 <= age0 < 1.0):
            continue
        P = G["particles"][t0]
        if layer is None:
            layer = np.zeros((H, W), np.uint8)
        k = z / 1.4
        ex, ey = emit_xy
        for i in range(n):
            age = age0 - P["delay"][i]
            if age <= 0 or age > P["life"][i]:
                continue
            fade = (1 - age / P["life"][i]) ** 1.2
            def pos(a):
                return (ex + k * (P["vx"][i] * a), ey + k * (P["vy"][i] * a + 0.5 * 2600 * a * a))
            x1, y1 = pos(age)
            x0, y0 = pos(max(age - 0.022, 0))
            c = int(255 * P["bri"][i] * fade)
            th = max(1, int(round(P["size"][i] * k * (0.6 + 0.4 * fade))))
            cv2.line(layer, (int(x0 * 16), int(y0 * 16)), (int(x1 * 16), int(y1 * 16)), c, th,
                     cv2.LINE_AA, shift=4)
        # spray mist puff
        mist_r = int(60 + 900 * age0 ** 0.6)
        mist_a = int(28 * math.exp(-age0 / 0.15))
        if mist_a > 2:
            cv2.circle(layer, (int(ex), int(ey - mist_r * 0.35)), mist_r, mist_a, -1, cv2.LINE_AA)
    if layer is None:
        return None
    f = layer.astype(np.float32) / 255.0
    glow = cv2.GaussianBlur(f, (0, 0), 6)
    soft = cv2.GaussianBlur(f, (0, 0), 1.2)
    return np.clip(soft * 1.5 + glow * 2.2, 0, 2.5)


# ---------------------------------------------------------------- lighting ----
def light_fx(img, t, emit_xy, lum):
    add = np.zeros_like(img)
    X, Y = G["PX"], G["PY"]
    # anamorphic flare at the crack
    for t0, s in FX.FLARES:
        a = t - t0
        if 0 <= a < 0.6:
            e = 0.7 * s * math.exp(-a / 0.12)
            ex, ey = emit_xy
            dx, dy = X - ex, Y - ey
            streak = np.exp(-(dy / 7) ** 2) * np.exp(-np.abs(dx) / 420)
            core = np.exp(-(dx ** 2 + dy ** 2) / (2 * 40 ** 2)) + 0.12 * np.exp(
                -(dx ** 2 + dy ** 2) / (2 * 200 ** 2))
            add += (streak * 1.4)[..., None] * np.array([0.55, 0.85, 1.0], np.float32) * e
            add += core[..., None] * np.array([0.8, 1.0, 0.85], np.float32) * e
            # ghosts mirrored through the frame centre
            for gk, gr, gc in [(0.6, 70, (0.3, 1.0, 0.4)), (1.3, 40, (0.4, 0.7, 1.0)),
                               (1.8, 110, (0.6, 1.0, 0.6))]:
                gx = W / 2 + (W / 2 - ex) * gk
                gy = H / 2 + (H / 2 - ey) * gk
                gd = np.exp(-((X - gx) ** 2 + (Y - gy) ** 2) / (2 * gr ** 2))
                add += gd[..., None] * np.array(gc, np.float32) * 0.18 * e
    # specular sweep in the hero shot
    a = (t - FX.SWEEP_T0) / FX.SWEEP_DUR
    if 0 <= a <= 1:
        ang = math.radians(62)
        d = X * math.cos(ang) + Y * math.sin(ang)
        dmax = W * math.cos(ang) + H * math.sin(ang)
        pos = -250 + (dmax + 500) * TL.smooth(a)
        band = np.exp(-((d - pos) / 70) ** 2) + 0.35 * np.exp(-((d - pos) / 260) ** 2)
        w = np.clip(lum - 0.42, 0, 1) ** 1.3 * 2.2
        add += (band * w)[..., None] * np.array([0.92, 0.98, 1.0], np.float32) * 0.95
    img = img + add
    # light leaks (screen)
    for t0, dur, col, side in FX.LEAKS:
        a = (t - t0) / dur
        if 0 <= a <= 1:
            e = math.sin(math.pi * a) ** 1.5 * 0.38
            cx = W / 2 + side * (W * 0.85 - W * 0.7 * a)
            cy = H * (0.25 + 0.3 * a)
            sw, shh = W // 8, H // 8
            xs = (np.arange(sw, dtype=np.float32) + 0.5) * 8 - cx
            ys = (np.arange(shh, dtype=np.float32) + 0.5) * 8 - cy
            m = np.exp(-(xs[None, :] ** 2 / (2 * 330 ** 2) + ys[:, None] ** 2 / (2 * 600 ** 2))).astype(np.float32)
            m = cv2.resize(m, (W, H))
            leak = m[..., None] * np.array(col, np.float32) * e
            img = 1 - (1 - np.clip(img, 0, 1)) * (1 - leak)
    return img


def bloom(img, strength):
    if strength <= 0:
        return img
    br = np.clip(img - 0.8, 0, None)
    s1 = cv2.resize(br, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    b1 = cv2.GaussianBlur(s1, (0, 0), 6)
    s2 = cv2.resize(s1, (W // 16, H // 16), interpolation=cv2.INTER_AREA)
    b2 = cv2.GaussianBlur(s2, (0, 0), 4)
    b = cv2.resize(b1, (W, H)) + 1.5 * cv2.resize(b2, (W, H))
    return img + b * strength * np.array([0.92, 1.0, 1.02], np.float32)


def shockwave(img, t, emit_xy):
    for t0, s in FX.SHOCKWAVES:
        a = t - t0
        if 0 <= a < 0.45:
            R = 1500 * a ** 0.75
            amp = 36 * s * (1 - a / 0.45) ** 2
            X, Y = G["PX"], G["PY"]
            dx, dy = X - emit_xy[0], Y - emit_xy[1]
            d = np.sqrt(dx * dx + dy * dy) + 1e-3
            disp = amp * np.exp(-((d - R) / 70) ** 2)
            img = cv2.remap(img, (X - disp * dx / d).astype(np.float32),
                            (Y - disp * dy / d).astype(np.float32), cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_REFLECT101)
            ring = np.exp(-((d - R) / 18) ** 2) * 0.25 * s * (1 - a / 0.45)
            img = img + ring[..., None] * np.array([0.7, 1.0, 0.8], np.float32)
    return img


# --------------------------------------------------------------- 2D post ----
def split_rgb(img, px, radial=0.0):
    if px < 0.3 and radial <= 0:
        return img
    out = img.copy()
    for ch, sgn in ((0, 1), (2, -1)):
        sc = 1 + sgn * radial
        M = np.array([[sc, 0, (1 - sc) * W / 2 + sgn * px],
                      [0, sc, (1 - sc) * H / 2]], np.float32)
        out[..., ch] = cv2.warpAffine(np.ascontiguousarray(img[..., ch]), M, (W, H),
                                      flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101)
    return out


def glitch(img, t, inten, fidx):
    r = np.random.default_rng(fidx * 7919 + 13)
    out = img.copy()
    for _ in range(int(6 + 10 * inten)):
        y0 = int(r.integers(0, H - 20))
        h = int(r.integers(6, 160))
        dx = int(r.normal(0, 70 * inten))
        sl = slice(y0, min(H, y0 + h))
        if r.random() < 0.5:
            out[sl] = np.roll(out[sl], dx, axis=1)
        else:
            ch = int(r.integers(0, 3))
            out[sl, :, ch] = np.roll(out[sl, :, ch], dx, axis=1)
        if r.random() < 0.15:
            out[sl] = out[sl] * np.array([0.3, 1.2, 0.5], np.float32)
    out[::3] *= 0.85
    return out


# ------------------------------------------------------------------- text ----
def fit_font(path, text, max_w, start=400, tracking=0):
    size = start
    while size > 20:
        f = ImageFont.truetype(path, size)
        w = text_width(f, text, tracking)
        if w <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(path, size)


def text_width(f, text, tracking):
    return sum(f.getlength(c) for c in text) + tracking * (len(text) - 1)


def draw_line(draw, f, text, cx, y, tracking, fill, stroke=0, stroke_fill=None):
    w = text_width(f, text, tracking)
    x = cx - w / 2
    for c in text:
        draw.text((x, y), c, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        x += f.getlength(c) + tracking


def make_layer(lines, glow_col=(1, 1, 1), glow=0.8, glow_r=22, shadow=0.55, size=(1400, 1000)):
    """lines: list of dict(text, font, y, tracking, fill(rgba), stroke, stroke_fill)
    returns premultiplied float RGBA (h, w, 4) centred at canvas centre."""
    cw, ch = size
    im = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for L in lines:
        draw_line(d, L["font"], L["text"], cw / 2, L["y"], L.get("tracking", 0), L["fill"],
                  L.get("stroke", 0), L.get("stroke_fill"))
    a = np.asarray(im).astype(np.float32) / 255.0
    rgb, al = a[..., :3], a[..., 3:4]
    pre = rgb * al
    al_img = Image.fromarray((al[..., 0] * 255).astype(np.uint8))
    g = np.asarray(al_img.filter(ImageFilter.GaussianBlur(glow_r))).astype(np.float32) / 255.0
    g2 = np.asarray(al_img.filter(ImageFilter.GaussianBlur(glow_r * 3))).astype(np.float32) / 255.0
    sh = np.asarray(al_img.filter(ImageFilter.GaussianBlur(14))).astype(np.float32) / 255.0
    sh = np.maximum(sh, np.asarray(al_img.filter(ImageFilter.GaussianBlur(40))).astype(np.float32) / 255.0 * 1.6)
    sh = np.clip(sh, 0, 1)
    sh = np.roll(np.roll(sh, 10, axis=0), 6, axis=1)
    return dict(pre=pre, a=al[..., 0], glow=(g * 1.0 + g2 * 0.7) * glow,
                glow_col=np.array(glow_col, np.float32), shadow=sh * shadow)


def build_texts():
    T = {}
    big = fit_font(FONT_BLACK_IT, "ZERO", 900, 360)
    sub = fit_font(FONT_BLACK_IT, "SUGAR.", 780, 300, tracking=6)
    T["zero_sugar"] = make_layer([
        dict(text="ZERO", font=big, y=150, fill=(255, 255, 255, 255)),
        dict(text="SUGAR.", font=sub, y=150 + big.size * 0.92, tracking=6,
             fill=(255, 255, 255, 255))], glow=0.45)
    sub2 = fit_font(FONT_BLACK_IT, "MERCY.", 820, 300, tracking=6)
    T["zero_mercy"] = make_layer([
        dict(text="ZERO", font=big, y=150, fill=(255, 255, 255, 255)),
        dict(text="MERCY.", font=sub2, y=150 + big.size * 0.92, tracking=6,
             fill=(110, 255, 80, 255))], glow_col=(0.42, 1.0, 0.3), glow=0.9)
    mf = fit_font(FONT_BLACK_IT, "MONSTROUS", 1000, 260, tracking=-4)
    my = 500 - mf.size * 0.62
    T["monstrous_fill"] = make_layer([dict(text="MONSTROUS", font=mf, y=my, tracking=-4,
                                           fill=(255, 255, 255, 255))],
                                     glow_col=(0.42, 1.0, 0.3), glow=1.1, glow_r=26, shadow=0.95)
    T["monstrous_outline"] = make_layer([dict(text="MONSTROUS", font=mf, y=my, tracking=-4,
                                              fill=(0, 0, 0, 0), stroke=8,
                                              stroke_fill=(255, 255, 255, 255))],
                                        glow_col=(0.6, 1.0, 0.6), glow=0.9, glow_r=14, shadow=0.6)
    T["monstrous_green"] = make_layer([dict(text="MONSTROUS", font=mf, y=my, tracking=-4,
                                            fill=(110, 255, 80, 255), stroke=4,
                                            stroke_fill=(255, 255, 255, 255))],
                                      glow_col=(0.42, 1.0, 0.3), glow=1.2, glow_r=30, shadow=0.95)
    cap = ImageFont.truetype(FONT_MED, 34)
    T["caption"] = make_layer([dict(text="ULTRA  /  ZERO SUGAR  /  FULL CHARGE", font=cap, y=480,
                                    tracking=7, fill=(235, 245, 255, 255))],
                              glow=0.35, glow_r=10, shadow=0.7)
    stay = ImageFont.truetype(FONT_BLACK, 60)
    T["stay"] = make_layer([dict(text="STAY", font=stay, y=330, tracking=34,
                                 fill=(255, 255, 255, 255))], glow=0.5, glow_r=12)
    T["stay_letters"] = []
    ms = fit_font(FONT_BLACK_IT, "MONSTROUS.", 960, 220, tracking=-2)
    full_w = text_width(ms, "MONSTROUS.", -2)
    x = 700 - full_w / 2
    for i, c in enumerate("MONSTROUS."):
        lay = make_layer([dict(text=c, font=ms, y=430, fill=(255, 255, 255, 255))],
                         glow_col=(0.42, 1.0, 0.3), glow=0.9, glow_r=22)
        T["stay_letters"].append((lay, x + ms.getlength(c) / 2 - 700))
        x += ms.getlength(c) - 2
    return T


def place_layer(img, lay, cx, cy, scale=1.0, rot=0.0, alpha=1.0, dx=0.0, rgb_split=0.0):
    h, w = lay["a"].shape
    th = math.radians(rot)
    c, s = math.cos(th) * scale, math.sin(th) * scale
    M = np.array([[c, -s, cx + dx - (c * w / 2 - s * h / 2)],
                  [s, c, cy - (s * w / 2 + c * h / 2)]], np.float32)
    def warp(x, ch=None):
        return cv2.warpAffine(np.ascontiguousarray(x), M, (W, H), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    shadow = warp(lay["shadow"]) * alpha
    img = img * (1 - shadow[..., None] * 0.85)
    glow = warp(lay["glow"]) * alpha
    img = img + glow[..., None] * lay["glow_col"] * 0.9
    a = warp(lay["a"]) * alpha
    pre = warp(lay["pre"]) * alpha
    if rgb_split > 0.5:
        Mr = np.array([[1, 0, rgb_split], [0, 1, 0]], np.float32)
        Mb = np.array([[1, 0, -rgb_split], [0, 1, 0]], np.float32)
        pr = cv2.warpAffine(pre[..., 0], Mr, (W, H))
        pb = cv2.warpAffine(pre[..., 2], Mb, (W, H))
        ar = cv2.warpAffine(a, Mr, (W, H))
        ab = cv2.warpAffine(a, Mb, (W, H))
        img[..., 0] = img[..., 0] * (1 - ar) + pr
        img[..., 1] = img[..., 1] * (1 - a) + pre[..., 1]
        img[..., 2] = img[..., 2] * (1 - ab) + pb
        return img
    return img * (1 - a[..., None]) + pre


def ease_back(u, k=2.2):
    u = min(max(u, 0.0), 1.0) - 1
    return 1 + u * u * ((k + 1) * u + k)


def texts(img, t, fidx):
    T = G["texts"]
    dx, dy, dr = shake(t)
    for t0, t1, key in FX.TEXTS:
        if not (t0 <= t < t1):
            continue
        a = t - t0
        if key in ("zero_sugar", "zero_mercy"):
            sc = 1.45 - 0.45 * ease_back(a / 0.13) + 0.05 * a
            split = 22 * math.exp(-a / 0.08)
            alpha = 1.0
            jitter = 0
            if key == "zero_mercy" and t1 - t < 0.16:
                alpha = 1.0 if (fidx % 3) else 0.0
                jitter = (fidx % 5 - 2) * 18
            img = place_layer(img, T[key], W / 2 + dx * 0.4 + jitter, 900 + dy * 0.4,
                              sc, dr * 0.3, alpha, rgb_split=split + (12 if jitter else 0))
        elif key.startswith("monstrous"):
            if key == "monstrous_fill":
                sc = 1.9 - 0.9 * ease_back(a / 0.11, 1.8)
                rot = -3
            elif key == "monstrous_outline":
                sc = 1.12 - 0.08 * TL.ease_out(a / 0.4)
                rot = -6
            else:
                sc = 1.25 - 0.2 * ease_back(a / 0.1)
                rot = 4
            alpha = 1.0 if t1 - t > 0.04 else 0.0
            split = 26 * math.exp(-a / 0.1) + 3
            img = place_layer(img, T[key], W / 2 + dx * 0.7, 980 + dy * 0.7, sc, rot + dr, alpha,
                              rgb_split=split)
        elif key == "caption":
            fin = TL.smooth(a / 0.35) * TL.smooth((t1 - t) / 0.2)
            img = place_layer(img, T[key], W / 2, 1650, 1.0 + 0.04 * a, 0, fin)
        elif key == "stay_monstrous":
            fout = TL.smooth((TL.DURATION - 0.1 - t) / 0.5)
            st = TL.smooth(a / 0.3) * fout
            img = place_layer(img, T["stay"], W / 2, 850 - 8 * (1 - TL.smooth(a / 0.4)), 1.0, 0, st)
            for i, (lay, off) in enumerate(T["stay_letters"]):
                la = (a - 0.12 - i * 0.045) / 0.18
                if la <= 0:
                    continue
                e = TL.smooth(la)
                sc = 1.0 + 0.35 * (1 - ease_back(la, 1.5))
                img = place_layer(img, lay, W / 2 + off * (1.0 + 0.02 * a), 960 + 40 * (1 - e),
                                  sc, 0, e * fout, rgb_split=10 * (1 - e))
    return img


# ------------------------------------------------------------------- frame ----
def frame(fidx):
    t = fidx / FPS
    img, cam, A = render_plate(t)
    seg = cam["seg"]
    ex_src, ey_src = TL.EMITTER_SRC
    emit = to_out(A, ex_src * G["SW"], ey_src * G["SH"])

    img = shockwave(img, t, emit)
    img, vig, blm, focus = grade(img, t, cam, A)
    lum = img[..., 0] * 0.2126 + img[..., 1] * 0.7152 + img[..., 2] * 0.0722

    p = draw_particles(t, emit, cam["z"])
    if p is not None:
        img = img + p[..., None] * np.array([0.85, 0.97, 1.0], np.float32)
    img = light_fx(img, t, emit, lum)
    img = bloom(img, blm)

    # sharpen a touch
    bl = cv2.GaussianBlur(img, (0, 0), 1.3)
    img = img + 0.35 * (img - bl)

    # chroma burst + constant mild lens CA
    px = sum(px_ * env_decay(t, t0, dec) for t0, px_, dec in FX.CHROMA)
    img = split_rgb(img, px, radial=0.0015 + px * 0.0004)
    for g0, g1, inten in FX.GLITCH:
        if g0 <= t < g1:
            img = glitch(img, t, inten, fidx)

    inv = seg["look"].get("invert_frames", 0)
    if (inv and t - seg["t0"] < inv / 30) or (TL.T_CRACK3 <= t < TL.T_CRACK3 + 0.05):
        img = 1 - np.clip(img, 0, 1)
    # flashes
    for t0, s, dec, col in FX.FLASHES:
        e = env_decay(t, t0, dec)
        if e > 0.002:
            img = img + s * e * np.array(col, np.float32)

    # intro flicker reveal
    if t < 0.6:
        img = img * FX.flicker(t)

    img = img * (vig ** 1.0 * G["vig"] + (1 - vig))[..., None]
    img = texts(img, t, fidx)
    img = img + G["grain"][fidx % 8][..., None] * 0.022
    img = np.clip(img, 0, 1)
    return (img * 255 + 0.5).astype(np.uint8)


def _worker_init(work):
    init(work)


def _render(fidx):
    return fidx, frame(fidx).tobytes()


def main():
    work, mode = sys.argv[1], sys.argv[2]
    if mode == "stills":
        init(work)
        os.makedirs(os.path.join(work, "stills"), exist_ok=True)
        for ts in sys.argv[3].split(","):
            t = float(ts)
            fi = int(round(t * FPS))
            out = frame(fi)
            cv2.imwrite(os.path.join(work, "stills", f"{t:06.3f}.jpg"),
                        cv2.cvtColor(out, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
            print("still", t, flush=True)
        return
    lo = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    hi = int(sys.argv[4]) if len(sys.argv) > 4 else NFRAMES
    out = os.path.join(work, "video.mp4" if (lo, hi) == (0, NFRAMES) else f"video_{lo}_{hi}.mp4")
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-vf", "scale=out_color_matrix=bt709:out_range=tv",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
         "-profile:v", "high", "-colorspace", "bt709", "-color_primaries", "bt709",
         "-color_trc", "bt709", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    with Pool(int(os.environ.get("JOBS", "4")), initializer=_worker_init, initargs=(work,)) as pool:
        for k, (fi, buf) in enumerate(pool.imap(_render, range(lo, hi), chunksize=2)):
            enc.stdin.write(buf)
            if k % 60 == 0:
                print(f"frame {fi}/{hi}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
