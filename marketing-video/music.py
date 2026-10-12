"""Synthesizes a 30s 120 BPM soundtrack with transition whooshes, written to music.wav."""
import wave

import numpy as np

SR = 44100
DUR = 30.0
BPM = 120
BEAT = 60 / BPM
DROP = 4.4
TRANSITIONS = [4.4, 8.2, 12.2, 16.2, 20.8, 24.6, 27.4]

n = int(SR * DUR)
t = np.arange(n) / SR
mix = np.zeros((n, 2))
rng = np.random.default_rng(7)


def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= n:
        return
    sig = sig[: n - i] * gain
    mix[i : i + len(sig), 0] += sig * (1 - pan) ** 0.5
    mix[i : i + len(sig), 1] += sig * (1 + pan) ** 0.5


def env(length, a=0.005, d=0.2):
    tt = np.arange(int(length * SR)) / SR
    return np.minimum(tt / a, 1) * np.exp(-tt / d)


def kick():
    tt = np.arange(int(0.45 * SR)) / SR
    freq = 50 + 110 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-tt * 7)


def hat(length=0.06):
    noise = rng.standard_normal(int(length * SR))
    noise = np.diff(noise, prepend=0)
    return noise * env(length, 0.001, 0.015)


def clap():
    noise = rng.standard_normal(int(0.25 * SR))
    return noise * env(0.25, 0.002, 0.06) * 0.6


def saw(freq, length):
    tt = np.arange(int(length * SR)) / SR
    return 2 * ((tt * freq) % 1) - 1


def lowpass(x, alpha):
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def note(midi):
    return 440 * 2 ** ((midi - 69) / 12)


# Am - F - C - G, one chord per bar (2s)
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
ROOTS = [45, 41, 36, 43]

bar = 4 * BEAT
for b in range(int(DUR / bar) + 1):
    start = b * bar
    chord = CHORDS[b % 4]
    pad = sum(saw(note(m) * d, bar) for m in chord for d in (0.997, 1.003))
    pad = lowpass(pad, 0.04 if start < DROP else 0.08)
    fade = np.minimum(1, np.arange(len(pad)) / (0.3 * SR)) * np.minimum(1, (len(pad) - np.arange(len(pad))) / (0.3 * SR))
    add(pad * fade, start, 0.035 if start >= DROP else 0.05)

    if start + bar <= DROP:
        continue
    for e in range(8):
        tb = start + e * BEAT / 2
        if tb < DROP:
            continue
        f = note(ROOTS[b % 4] - 12 + (12 if e % 2 else 0))
        bass = lowpass(saw(f, BEAT / 2 * 0.9), 0.12) * env(BEAT / 2 * 0.9, 0.003, 0.18)
        add(bass, tb, 0.35)
    for q in range(4):
        tb = start + q * BEAT
        if tb >= DROP:
            add(kick(), tb, 0.9)
            add(hat(), tb + BEAT / 2, 0.25, pan=0.3)
            if q % 2 == 1:
                add(clap(), tb, 0.35, pan=-0.2)

# Intro: ticking clock + tension riser into the drop
for k in range(int(DROP / BEAT)):
    add(hat(0.03), k * BEAT, 0.35)
riser_len = 1.6
tt = np.arange(int(riser_len * SR)) / SR
riser = rng.standard_normal(len(tt)) * (tt / riser_len) ** 2
riser = lowpass(riser, 0.05) + np.sin(2 * np.pi * np.cumsum(200 + 900 * tt / riser_len) / SR) * (tt / riser_len) ** 2 * 0.3
add(riser, DROP - riser_len, 0.35)

# Notification pings in the hook scene
for tp in (1.5, 2.2):
    tt = np.arange(int(0.4 * SR)) / SR
    ping = (np.sin(2 * np.pi * 1318 * tt) + 0.5 * np.sin(2 * np.pi * 1760 * tt)) * np.exp(-tt * 9)
    add(ping, tp, 0.25)

# Whoosh on every scene change
for tr in TRANSITIONS:
    length = 0.5
    tt = np.arange(int(length * SR)) / SR
    shape = np.sin(np.pi * tt / length) ** 2
    w = lowpass(rng.standard_normal(len(tt)), 0.15) * shape
    add(w, tr - 0.3, 0.6)

# Impact on the drop and on the CTA
for ti in (DROP, 27.4):
    tt = np.arange(int(1.2 * SR)) / SR
    boom = np.sin(2 * np.pi * np.cumsum(40 + 80 * np.exp(-tt * 12)) / SR) * np.exp(-tt * 3)
    add(boom, ti, 0.8)

fade = np.ones(n)
fo = int(1.5 * SR)
fade[-fo:] = np.linspace(1, 0, fo)
mix *= fade[:, None]
mix = np.tanh(mix * 1.2)
mix /= np.max(np.abs(mix)) * 1.05

with wave.open("music.wav", "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes((mix * 32767).astype(np.int16).tobytes())
print("music.wav written")
