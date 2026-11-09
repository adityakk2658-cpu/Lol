"""Visual FX cue sheet (shared with the audio so every hit has a sound)."""
import timeline as TL

# fluorescent-tube flicker reveal in the intro: (time, brightness) step function
FLICKER = [(0.0, 0.0), (0.06, 0.85), (0.10, 0.08), (0.17, 0.0), (0.24, 1.0), (0.28, 0.3),
           (0.31, 0.0), (0.40, 0.8), (0.44, 0.15), (0.47, 1.0)]
FLICKER_ON = [(0.06, 0.04), (0.24, 0.05), (0.40, 0.05), (0.47, 0.09)]


def flicker(t):
    v = FLICKER[0][1]
    for t0, b in FLICKER:
        if t >= t0:
            v = b
    return v


# zoom punches (time, amount, decay)  -- every kick and clap gets one
PUNCHES = []
for kt in TL.kick_times():
    if TL.T_HERO <= kt < TL.T_BREAK_END:
        continue
    PUNCHES.append((kt, 0.07, 0.11))
for ct in TL.clap_times():
    PUNCHES.append((ct, 0.045, 0.09))
for t in (TL.T_TAP1, TL.T_TAP2, TL.T_TAP3):
    PUNCHES.append((t, 0.12, 0.14))
for i, t in enumerate(TL.CRACK_TIMES):
    PUNCHES.append((t, 0.18 if i == 0 else 0.1, 0.18))
for k in range(8):
    PUNCHES.append((TL.T_CUTS + 0.2 * k, 0.06, 0.08))
PUNCHES.append((TL.T_END_HIT, 0.12, 0.25))

# camera shakes (time, amplitude px, decay s, frequency Hz)
SHAKES = [(t, 26, 0.16, 18) for t in (TL.T_TAP1, TL.T_TAP2, TL.T_TAP3)]
SHAKES += [(TL.T_DROP, 70, 0.45, 16), (TL.T_CRACK2, 40, 0.3, 18), (TL.T_CRACK3, 45, 0.3, 20)]
SHAKES += [(t, 14, 0.12, 20) for t in TL.clap_times() if t >= TL.T_GROOVE]
SHAKES += [(TL.T_CUT_CRACK, 30, 0.2, 20), (TL.T_END_HIT, 40, 0.35, 14)]
SHAKES += [(0.0, 18, 0.2, 14), (0.8, 18, 0.2, 14)]


def rumble_amp(t):
    """continuous build-up shake"""
    if TL.T_BUILD <= t < TL.T_DROP:
        u = (t - TL.T_BUILD) / (TL.T_DROP - TL.T_BUILD)
        return 2 + 14 * u ** 2
    return 0.0


# flashes: (time, strength, decay, (r, g, b))
WHITE = (1.0, 1.0, 1.0)
GREEN = (0.45, 1.0, 0.35)
ICE = (0.75, 0.92, 1.0)
FLASHES = [(TL.T_TAP1, 0.45, 0.05, WHITE), (TL.T_TAP2, 0.35, 0.045, WHITE),
           (TL.T_TAP3, 0.5, 0.05, ICE),
           (TL.T_GROOVE, 0.3, 0.05, WHITE),
           (TL.T_DROP, 1.1, 0.06, WHITE), (TL.T_CRACK2, 0.55, 0.05, GREEN),
           (TL.T_CRACK3, 0.7, 0.05, WHITE), (TL.T_VELO, 0.4, 0.05, ICE),
           (TL.T_CUT_CRACK, 0.7, 0.05, WHITE), (TL.T_HERO, 0.5, 0.07, ICE),
           (TL.T_END_HIT, 0.9, 0.09, WHITE)]
FLASHES += [(t, 0.16, 0.035, WHITE) for t in TL.clap_times() if TL.T_VELO <= t < TL.T_CUTS]
FLASHES += [(TL.T_CUTS + 0.2 * k, 0.18, 0.03, WHITE) for k in range(8) if k != 6]

# chromatic split bursts: (time, px, decay)
CHROMA = [(t, 14, 0.12) for t in (TL.T_TAP1, TL.T_TAP2, TL.T_TAP3)]
CHROMA += [(TL.T_DROP, 26, 0.16), (TL.T_CRACK2, 14, 0.12), (TL.T_CRACK3, 20, 0.12),
           (TL.T_CUT_CRACK, 18, 0.1), (TL.T_END_HIT, 22, 0.2), (0.0, 18, 0.2), (0.8, 22, 0.2)]
CHROMA += [(TL.T_CUTS + 0.2 * k, 10, 0.06) for k in range(8)]

# glitch windows: (t0, t1, intensity)
GLITCH = [(0.8, 0.92, 1.0), (1.3, 1.45, 0.8), (TL.T_CRACK3, TL.T_CRACK3 + 0.12, 1.0),
          (TL.T_CUTS + 1.4, TL.T_CUTS + 1.5, 0.8), (TL.T_END_HIT + 0.02, TL.T_END_HIT + 0.2, 0.9),
          (2.6, 2.64, 0.6)]

# particle bursts from the can mouth: (time, seed, count)
BURSTS = [(TL.T_DROP, 1, 340), (TL.T_CRACK2, 2, 180), (TL.T_CRACK3, 3, 200),
          (TL.T_CUT_CRACK, 4, 150)]
SHOCKWAVES = [(TL.T_DROP, 1.0), (TL.T_CRACK3, 0.6), (TL.T_END_HIT, 0.5)]
FLARES = [(TL.T_DROP, 1.0), (TL.T_CRACK2, 0.6), (TL.T_CRACK3, 0.7), (TL.T_CUT_CRACK, 0.6)]

# specular light sweep across the can in the hero shot
SWEEP_T0 = TL.T_HERO + 0.35
SWEEP_DUR = 0.75

# light leaks: (t0, dur, color, side)
LEAKS = [(TL.T_TAP1 - 0.1, 0.5, (1.0, 0.55, 0.2), 1), (TL.T_VELO - 0.1, 0.5, (0.35, 1.0, 0.5), -1),
         (TL.T_HERO - 0.1, 0.9, (0.3, 0.7, 1.0), 1), (TL.T_END_HIT, 0.8, (1.0, 0.95, 0.85), -1)]

# texts: (t0, t1, id)
TEXTS = [(0.0, 0.8, "zero_sugar"), (0.8, 1.48, "zero_mercy"),
         (TL.T_DROP, TL.T_CRACK2, "monstrous_fill"), (TL.T_CRACK2, TL.T_CRACK3, "monstrous_outline"),
         (TL.T_CRACK3, TL.T_CRACK3 + 0.4, "monstrous_green"),
         (TL.T_HERO + 0.3, TL.T_END_HIT - 0.05, "caption"),
         (TL.T_OUTRO_TEXT, TL.DURATION, "stay_monstrous")]
