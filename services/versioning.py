"""Comparação de versões.

O código antigo comparava strings: `"1.10.0" > "1.9.0"` é False, por isso a
partir da v1.9 o updater deixaria de ver versões novas.
"""

from __future__ import annotations

import re

_NUM = re.compile(r"\d+")


def parse(version: str) -> tuple[int, ...]:
    cleaned = (version or "").strip().lower().lstrip("v")
    cleaned = cleaned.split("-")[0].split("+")[0]
    parts = tuple(int(n) for n in _NUM.findall(cleaned)[:4])
    return parts or (0,)


def is_newer(candidate: str, current: str) -> bool:
    left, right = parse(candidate), parse(current)
    size = max(len(left), len(right))
    left += (0,) * (size - len(left))
    right += (0,) * (size - len(right))
    return left > right


def normalize(version: str) -> str:
    return ".".join(str(n) for n in parse(version))
