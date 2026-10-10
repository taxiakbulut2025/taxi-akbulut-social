"""Eigene Musikspur für Reels, komplett synthetisch erzeugt (keine Lizenzfragen).
Aufruf: python3 generator/music.py musik.wav --dur 9 --bpm 112 --seed 7 --pops 2.0,3.5 --chime 5.8 [--plane]
Unterschiedliche --seed/--bpm ergeben Varianten."""
import argparse
import numpy as np
import wave

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--dur", type=float, default=9.0)
ap.add_argument("--bpm", type=float, default=112)
ap.add_argument("--seed", type=int, default=7)
ap.add_argument("--pops", default="2.0,3.5", help="Zeitpunkte für Nachrichten-Töne (s), leer = keine")
ap.add_argument("--chime", type=float, default=5.8, help="Zeitpunkt Abschluss-Klang (s), <0 = keiner")
ap.add_argument("--plane", action="store_true", help="Flugzeug-Rauschen am Anfang")
ARGS = ap.parse_args()

SR = 44100
DUR = ARGS.dur
BPM = ARGS.bpm
BEAT = 60 / BPM
N = int(SR * DUR)
t_all = np.arange(N) / SR
mix = np.zeros((N, 2))
rng = np.random.default_rng(ARGS.seed)


def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[: N - i] * gain
    mix[i:i + len(sig), 0] += sig * (1 - max(pan, 0))
    mix[i:i + len(sig), 1] += sig * (1 + min(pan, 0))


def env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * np.exp(-t / r)
    return e


def note(freq, length, kind="saw", a=0.01, r=0.3):
    n = int(length * SR)
    t = np.arange(n) / SR
    if kind == "saw":
        s = sum(np.sin(2 * np.pi * freq * k * t) / k for k in range(1, 8))
    elif kind == "tri":
        s = sum(((-1) ** ((k - 1) // 2)) * np.sin(2 * np.pi * freq * k * t) / k**2 for k in range(1, 9, 2))
    else:
        s = np.sin(2 * np.pi * freq * t)
    return s * env(n, a, r)


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 50 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def hat(open_=False):
    n = int((0.12 if open_ else 0.04) * SR)
    s = rng.standard_normal(n)
    s = np.diff(np.concatenate([[0], s]))  # Hochpass-Charakter
    return s * env(n, 0.001, 0.05 if open_ else 0.012) * 0.25


def clap():
    n = int(0.18 * SR)
    s = rng.standard_normal(n)
    return s * env(n, 0.002, 0.05) * 0.35


def mtof(m):
    return 440 * 2 ** ((m - 69) / 12)


# Akkorde: C – G – Am – F (je ein Takt), danach C
chords = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60], [60, 64, 67]]
bass = [36, 31, 33, 29, 36]
bar = 4 * BEAT
for b, (ch, bs) in enumerate(zip(chords, bass)):
    t0 = b * bar
    if t0 >= DUR:
        break
    for beat in range(4):
        tb = t0 + beat * BEAT
        if tb < 0.9:  # Intro: nur Flächen, Beat setzt mit der Überschrift ein
            continue
        add(kick(), tb, gain=0.9)
        if beat in (1, 3):
            add(clap(), tb, gain=0.6)
        add(hat(), tb + BEAT / 2, pan=0.3)
        add(note(mtof(bs), BEAT * 0.9, "tri", 0.005, 0.25), tb, gain=0.55)
        add(note(mtof(bs + 12), BEAT * 0.4, "tri", 0.005, 0.1), tb + BEAT / 2, gain=0.3)
    # Akkord-Stabs (Offbeat) + weiche Fläche
    for k in range(8):
        ts = t0 + k * BEAT / 2 + BEAT / 2
        if k % 2 == 0 and ts > 0.9:
            for m in ch:
                add(note(mtof(m + 12), 0.25, "saw", 0.003, 0.08), ts, pan=-0.2, gain=0.06)
    for m in ch:
        add(note(mtof(m), bar, "sine", 0.4, 1.6), t0, gain=0.12)

# Soundeffekte passend zur Animation
# Flugzeug: gefiltertes Rauschen, das an- und abschwillt (0,2–2,6 s)
if ARGS.plane:
    n = int(2.4 * SR)
    w = rng.standard_normal(n)
    k = np.ones(40) / 40
    w = np.convolve(w, k, mode="same")
    w *= np.sin(np.linspace(0, np.pi, n)) ** 2 * 0.5
    pan = np.linspace(-0.8, 0.8, n)
    i0 = int(0.2 * SR)
    mix[i0:i0 + n, 0] += w * (1 - np.clip(pan, 0, 1))
    mix[i0:i0 + n, 1] += w * (1 + np.clip(pan, -1, 0))


def pop(f1, f2):
    a = note(mtof(f1), 0.15, "sine", 0.002, 0.06)
    b = note(mtof(f2), 0.2, "sine", 0.002, 0.08)
    out = np.zeros(int(0.3 * SR))
    out[: len(a)] += a
    out[int(0.07 * SR):int(0.07 * SR) + len(b)] += b
    return out


for j, tp in enumerate([float(x) for x in ARGS.pops.split(",") if x.strip()]):
    add(pop(84 + 4 * (j % 2), 88 + 3 * (j % 2)), tp, pan=-0.3 if j % 2 == 0 else 0.3, gain=0.45)
if ARGS.chime >= 0:                            # Abschluss-Klang bei „Online buchen"
    for j, m in enumerate([72, 76, 79, 84]):
        add(note(mtof(m), 1.2, "sine", 0.005, 0.6), ARGS.chime + j * 0.06, gain=0.18)

# Mastering: Ein-/Ausblenden, Normalisieren, sanfte Sättigung
fade = np.ones(N)
fi, fo = int(0.15 * SR), int(1.2 * SR)
fade[:fi] = np.linspace(0, 1, fi)
fade[-fo:] = np.linspace(1, 0, fo)
mix *= fade[:, None]
mix /= np.max(np.abs(mix)) + 1e-9
mix = np.tanh(mix * 1.4) / np.tanh(1.4) * 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open(ARGS.out, "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes(pcm.tobytes())
print(ARGS.out, DUR, "s")
