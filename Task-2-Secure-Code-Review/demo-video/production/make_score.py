#!/usr/bin/env python3
"""Original 56 s score + sound design for the landscape Secure Code Review demo.

Synthesized locally. No third-party music. UI accents are CC0 samples from the
Brag asset library (Kenney), used at low level.
"""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, lfilter

SR = 48_000
DUR = 56.0
N = int(SR * DUR)
T = np.arange(N) / SR
RNG = np.random.default_rng(0x5EC0DE26)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "openfilm" / "assets" / "audio"
OUT.mkdir(parents=True, exist_ok=True)

L = np.zeros(N)
R = np.zeros(N)


def add(sig: np.ndarray, start: float, gain: float = 1.0, pan: float = 0.0) -> None:
    i = int(round(start * SR))
    if i >= N:
        return
    sig = np.asarray(sig, dtype=np.float64)
    j = min(N, i + len(sig))
    if j <= i:
        return
    a = (pan + 1.0) * np.pi / 4.0
    L[i:j] += sig[: j - i] * gain * np.cos(a)
    R[i:j] += sig[: j - i] * gain * np.sin(a)


def smoothstep(x, a: float, b: float):
    p = np.clip((np.asarray(x) - a) / (b - a), 0, 1)
    return p * p * (3 - 2 * p)


def lowpass(x: np.ndarray, cutoff: float, order: int = 2) -> np.ndarray:
    b, a = butter(order, cutoff / (SR / 2), btype="low")
    return lfilter(b, a, x)


def highpass(x: np.ndarray, cutoff: float, order: int = 2) -> np.ndarray:
    b, a = butter(order, cutoff / (SR / 2), btype="high")
    return lfilter(b, a, x)


def bandpass(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    b, a = butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band")
    return lfilter(b, a, x)


# ------------------------------------------------------------------- harmony
# Chord changes sit exactly on the picture cuts.
#   0 hook | 5 reveal | 12 architecture | 19 scan | 29 classification
#   38 tests | 48 outro
CHORDS = [
    (0.0, 5.2, [55.00, 110.00, 164.81, 220.00, 261.63]),
    (5.2, 12.2, [43.65, 87.31, 130.81, 174.61, 220.00]),
    (12.2, 19.2, [65.41, 98.00, 130.81, 164.81, 196.00]),
    (19.2, 29.2, [49.00, 98.00, 146.83, 196.00, 246.94]),
    (29.2, 38.2, [55.00, 110.00, 164.81, 220.00, 261.63]),
    (38.2, 48.2, [43.65, 87.31, 130.81, 174.61, 220.00]),
    (48.2, 56.0, [55.00, 110.00, 164.81, 220.00, 277.18]),
]

for start, end, notes in CHORDS:
    i0, i1 = int(start * SR), min(N, int(end * SR))
    n = i1 - i0
    if n <= 0:
        continue
    tt = np.arange(n) / SR
    fade = np.minimum(
        smoothstep(tt, 0, 0.9),
        1 - smoothstep(tt, max(0.0, n / SR - 0.9), n / SR),
    )
    for k, freq in enumerate(notes):
        amp = [0.19, 0.15, 0.10, 0.072, 0.048][k]
        det = 1.0 + (0.0011 if k % 2 else -0.0011)
        phase = 2 * np.pi * freq * det * tt
        sig = (
            np.sin(phase)
            + 0.24 * np.sin(2 * phase + 0.4)
            + 0.08 * np.sin(3 * phase + 1.1)
        )
        add(sig * fade * amp, start, 1.0, pan=(-0.35 + 0.18 * k))

# Sub drone, breathing slowly under everything.
sub_env = smoothstep(T, 0.0, 2.0) * (1 - smoothstep(T, 54.2, 56.0))
sub = np.sin(2 * np.pi * 55.0 * T + 0.5 * np.sin(2 * np.pi * 0.037 * T))
add(sub * sub_env, 0.0, 0.095, 0.0)
add(np.sin(2 * np.pi * 27.5 * T) * sub_env, 0.0, 0.070, 0.0)

# Air / room tone.
air = highpass(lowpass(RNG.standard_normal(N), 1800, 2), 160, 1)
air_env = smoothstep(T, 0.4, 5.0) * (0.40 + 0.60 * smoothstep(T, 38.0, 48.0)) * (1 - smoothstep(T, 54.0, 56.0))
add(air * air_env, 0.0, 0.018, -0.25)
add(np.roll(air, 1201) * air_env, 0.0, 0.015, 0.28)


# --------------------------------------------------------------------- pulse
def kick(dur: float = 0.32, f0: float = 92.0, f1: float = 34.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = f1 + (f0 - f1) * np.exp(-t * 22.0)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    body = np.sin(phase) * np.exp(-t * 10.5)
    click = highpass(RNG.standard_normal(n), 2400, 1) * np.exp(-t * 220.0) * 0.10
    return body + click


def hat(dur: float = 0.07, level: float = 0.5) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    return highpass(RNG.standard_normal(n), 5200, 2) * np.exp(-t * 90.0) * level


def pluck(freq: float, dur: float = 0.34) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = (
        np.sin(2 * np.pi * freq * t)
        + 0.34 * np.sin(2 * np.pi * freq * 2.005 * t + 0.2)
        + 0.12 * np.sin(2 * np.pi * freq * 3.01 * t + 1.0)
    )
    sig *= np.exp(-t * 9.0) * np.clip(t / 0.006, 0, 1)
    return lowpass(sig, 2600, 2)


def bass(freq: float, dur: float = 0.5) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.sin(2 * np.pi * freq * t) + 0.18 * np.sin(2 * np.pi * freq * 2 * t)
    sig *= np.exp(-t * 4.2) * np.clip(t / 0.008, 0, 1)
    return lowpass(sig, 420, 2)


beat = 0.6  # 100 BPM
for k in range(0, 90):
    at = 5.2 + k * beat
    if at >= 48.2:
        break
    if at < 12.2:
        if k % 2:
            continue
        add(kick(0.38, 84, 32), at, 0.060, 0.0)
    elif at < 19.2:
        add(kick(), at, 0.080, 0.0)
        add(hat(), at + beat / 2, 0.010, 0.12)
    elif at < 38.2:
        add(kick(), at, 0.100, 0.0)
        add(hat(), at + beat / 2, 0.014, -0.15 if k % 2 else 0.15)
        add(bass([65.41, 65.41, 98.00, 65.41][k % 4]), at, 0.043, 0.0)
    else:
        add(kick(0.30, 96, 36), at, 0.090, 0.0)
        add(hat(0.05, 0.55), at + beat / 2, 0.014, 0.15)
        add(bass([43.65, 43.65, 87.31, 65.41][k % 4]), at, 0.046, 0.0)

# Filtered arpeggio over the evidence and verification sections.
arp_windows = [
    (19.2, 29.2, [130.81, 164.81, 196.00, 261.63]),
    (29.2, 38.2, [130.81, 164.81, 196.00, 261.63]),
    (38.2, 48.2, [87.31, 130.81, 174.61, 220.00]),
]
for start, end, notes in arp_windows:
    for k in range(int((end - start) / beat)):
        at = start + k * beat
        f = notes[k % len(notes)] * 2
        add(pluck(f), at, 0.030 if start < 38.2 else 0.026, -0.28 if k % 2 else 0.28)

# Sonar pings in the hook.
def ping(freq: float = 1040.0, dur: float = 1.3) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.sin(2 * np.pi * freq * t) * np.exp(-t * 5.4)
    sig += 0.30 * np.sin(2 * np.pi * freq * 1.501 * t) * np.exp(-t * 7.2)
    sig += 0.12 * np.sin(2 * np.pi * freq * 0.5 * t) * np.exp(-t * 3.6)
    return sig


for at, pan, gain in [(0.12, -0.55, 0.040), (0.72, 0.45, 0.030), (1.35, -0.15, 0.034)]:
    add(ping(), at, gain, pan)

# Shimmer for the final resolve.
shimmer = [523.25, 659.26, 783.99, 1046.50, 1318.51]
env = smoothstep(T, 48.0, 50.0) * (1 - smoothstep(T, 54.0, 56.0))
for i, f in enumerate(shimmer):
    vib = 1.0 + 0.0016 * np.sin(2 * np.pi * (0.19 + 0.02 * i) * T)
    sig = np.sin(2 * np.pi * f * vib * T + i * 0.8)
    sig *= 0.62 + 0.38 * np.sin(2 * np.pi * (0.11 + 0.017 * i) * T + i)
    add(sig * env, 0.0, 0.012, -0.65 + i * 0.33)


# --------------------------------------------------------------- transition fx
def riser(dur: float, f0: float, f1: float) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = np.clip(t / dur, 0, 1)
    freq = f0 * (f1 / f0) ** (p ** 1.5)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    sweep = np.sin(phase) * 0.5 + np.sin(2.01 * phase) * 0.18
    noise = bandpass(RNG.standard_normal(n), 700, 6000)
    return (sweep * 0.45 + noise * 0.55) * (p ** 2.2)


def sub_hit(dur: float = 1.8, f0: float = 74.0, f1: float = 27.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = f1 + (f0 - f1) * np.exp(-t * 4.0)
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return np.sin(phase) * np.exp(-t * 2.6)


def whoosh(dur: float = 0.7) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = np.clip(t / dur, 0, 1)
    noise = bandpass(RNG.standard_normal(n), 300, 4200)
    return noise * (np.sin(np.pi * p) ** 2)


def bell(dur: float = 3.0, base: float = 220.0) -> np.ndarray:
    n = int(dur * SR)
    t = np.arange(n) / SR
    parts = [(1.0, 0.50), (2.01, 0.22), (3.01, 0.10), (4.17, 0.06), (5.43, 0.035)]
    sig = np.zeros(n)
    for mult, amp in parts:
        sig += amp * np.sin(2 * np.pi * base * mult * t) * np.exp(-t * (2.2 + mult * 0.4))
    return sig * np.clip(t / 0.004, 0, 1)


add(sub_hit(), 0.02, 0.22, 0.0)
add(riser(3.4, 70, 500), 0.6, 0.050, -0.1)
add(bell(2.6, 261.63), 3.9, 0.050, 0.15)

for at in (5.2, 12.2, 19.2, 29.2, 38.2, 48.2):
    add(whoosh(0.55), at - 0.28, 0.070, -0.2)
    add(sub_hit(1.2), at, 0.085, 0.0)

add(riser(2.2, 110, 900), 8.0, 0.040, 0.1)
add(riser(2.0, 120, 1000), 16.0, 0.045, -0.15)
add(riser(1.8, 140, 1200), 36.2, 0.045, 0.1)

add(bell(3.6, 220.0), 5.2, 0.090, 0.0)
add(bell(4.2, 220.0), 48.2, 0.110, 0.0)
add(sub_hit(2.4), 48.2, 0.140, 0.0)
add(bell(3.0, 329.63), 52.0, 0.050, 0.2)


# -------------------------------------------------------------------- reverb
def stereo_delay(sig: np.ndarray, delay: float, feedback: float, mix: float) -> np.ndarray:
    out = sig.copy()
    d = int(delay * SR)
    for k in range(1, 4):
        shifted = np.zeros_like(sig)
        shifted[d * k :] = sig[: N - d * k]
        out += shifted * (feedback ** k) * mix
    return out


L = stereo_delay(L, 0.233, 0.30, 0.15)
R = stereo_delay(R, 0.297, 0.28, 0.15)

# Gentle bus glue and fades.
L = lowpass(L, 11500, 1)
R = lowpass(R, 11500, 1)
L = np.tanh(L * 1.18) / np.tanh(1.18)
R = np.tanh(R * 1.18) / np.tanh(1.18)
L *= smoothstep(T, 0.0, 0.8) * (1 - smoothstep(T, 54.6, 56.0))
R *= smoothstep(T, 0.0, 0.8) * (1 - smoothstep(T, 54.6, 56.0))

peak = max(np.max(np.abs(L)), np.max(np.abs(R)), 1e-9)
L = L / peak * 0.82
R = R / peak * 0.82


def write_wav(path: Path, left: np.ndarray, right: np.ndarray, peak_norm: float = 0.95) -> None:
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    m = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-9)
    left = np.clip(left / m * peak_norm, -1, 1)
    right = np.clip(right / m * peak_norm, -1, 1)
    data = np.stack([left, right], axis=1)
    pcm = (data * 32767).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SR)
        handle.writeframes(pcm.tobytes())
    print(f"{path.name}: {len(left)/SR:.2f}s peak {peak_norm:.2f}")


write_wav(OUT / "score.wav", L, R, 0.92)

# --------------------------------------------------------------- accent sounds
fx = {
    "sub-hit.wav": (sub_hit(), 0.90),
    "whoosh.wav": (whoosh(), 0.70),
    "confirm.wav": (
        np.concatenate([bell(0.9, 659.26)[: int(0.9 * SR)], bell(1.5, 987.77)]),
        0.62,
    ),
    "title-bell.wav": (bell(4.0, 220.0), 0.72),
    "tick.wav": (
        highpass(RNG.standard_normal(int(0.06 * SR)), 3000, 1)
        * np.exp(-np.arange(int(0.06 * SR)) / (0.008 * SR))
        * 0.5,
        0.55,
    ),
}
for name, (mono, level) in fx.items():
    write_wav(OUT / name, mono, np.roll(mono, 37), level)
