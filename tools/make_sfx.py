#!/usr/bin/env python3
"""Gera os efeitos sonoros da interface.

Sons próprios, sintetizados: não há dependência externa nem questão de
licenciamento. WAV PCM 16 bits mono a 48 kHz, que é exactamente o que o
QSoundEffect prefere (pré-carrega e toca com latência baixa).

Regenerar:  python3 tools/make_sfx.py
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

RATE = 48_000
OUT = Path(__file__).resolve().parent.parent / "assets" / "sfx"


def envelope(index: int, total: int, attack_ms: float, decay: float) -> float:
    t = index / RATE
    attack_samples = max(1, int(RATE * attack_ms / 1000))
    rise = min(1.0, index / attack_samples)
    return rise * math.exp(-decay * t)


def tone(freq: float, duration: float, decay: float, amp: float,
         attack_ms: float = 4.0, harmonic: float = 0.18, start: float = 0.0):
    """Seno com um harmónico suave por cima -- mais 'corpo' sem ficar agressivo."""
    total = int(RATE * duration)
    offset = int(RATE * start)
    for i in range(total):
        t = i / RATE
        env = envelope(i, total, attack_ms, decay)
        value = math.sin(2 * math.pi * freq * t)
        value += harmonic * math.sin(4 * math.pi * freq * t)
        yield offset + i, amp * env * value / (1 + harmonic)


def mix(length_seconds: float, *generators) -> bytes:
    buffer = [0.0] * int(RATE * length_seconds)
    for generator in generators:
        for index, value in generator:
            if 0 <= index < len(buffer):
                buffer[index] += value

    peak = max((abs(v) for v in buffer), default=0.0) or 1.0
    frames = bytearray()
    for value in buffer:
        sample = value / peak * 0.82           # margem para não saturar
        frames += struct.pack("<h", int(max(-1.0, min(1.0, sample)) * 32767))
    return bytes(frames)


def write(name: str, data: bytes) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.wav"
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(data)
    return path


def build() -> list[Path]:
    written = []

    # click: tique curto e seco, mal se dá por ele
    written.append(write("click", mix(
        0.055,
        tone(1_180, 0.05, 90, 0.55, attack_ms=1.5),
        tone(2_360, 0.03, 140, 0.16, attack_ms=1.0),
    )))

    # nav: dois tons a subir, para mudança de aba/modo
    written.append(write("nav", mix(
        0.13,
        tone(740, 0.06, 55, 0.5, attack_ms=2.0),
        tone(1_108, 0.08, 45, 0.45, attack_ms=2.0, start=0.035),
    )))

    # success: tríade ascendente, discreta
    written.append(write("success", mix(
        0.55,
        tone(523.25, 0.30, 11, 0.42, attack_ms=6.0),
        tone(659.25, 0.32, 10, 0.40, attack_ms=6.0, start=0.085),
        tone(783.99, 0.40, 8, 0.44, attack_ms=6.0, start=0.170),
    )))

    # error: dois tons graves a descer, sem estridência
    written.append(write("error", mix(
        0.42,
        tone(392.00, 0.22, 14, 0.46, attack_ms=5.0, harmonic=0.10),
        tone(311.13, 0.30, 11, 0.44, attack_ms=5.0, start=0.110, harmonic=0.10),
    )))

    return written


if __name__ == "__main__":
    for path in build():
        with wave.open(str(path)) as handle:
            ms = handle.getnframes() / handle.getframerate() * 1000
        print(f"{path.name:12} {path.stat().st_size:>7} bytes  {ms:6.0f} ms")
