"""Terminal-native ASCII/Unicode visualizations for the cos home.

Pure functions — no Textual dependency — so they are trivially unit-testable
and reusable by the brief generator. Every function clamps its inputs and
returns a fixed-width string suitable for dropping into Rich markup.
"""

from __future__ import annotations

from typing import Sequence

_SPARK = "▁▂▃▄▅▆▇█"


def sparkline(values: Sequence[float]) -> str:
    """Render a unicode sparkline. Empty input → empty string.

    A flat series renders as the lowest block. Output length == number of
    non-None values.
    """
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    span = hi - lo
    out = []
    for v in vals:
        idx = 0 if span == 0 else round((v - lo) / span * (len(_SPARK) - 1))
        out.append(_SPARK[idx])
    return "".join(out)


def gauge(value: float, maximum: float, width: int = 9, filled: str = "█", empty: str = "░") -> str:
    """A proportional gauge of fixed `width`. Clamps to [0, maximum]."""
    width = max(1, int(width))
    if maximum <= 0:
        return empty * width
    frac = max(0.0, min(1.0, value / maximum))
    n = round(frac * width)
    return filled * n + empty * (width - n)


def bar(pct: float, width: int = 10, filled: str = "▰", empty: str = "▱") -> str:
    """A percentage bar (0–100) of fixed `width`."""
    width = max(1, int(width))
    frac = max(0.0, min(1.0, (pct or 0) / 100.0))
    n = round(frac * width)
    return filled * n + empty * (width - n)


def blocks(n: int, char: str = "▮", max_blocks: int = 12) -> str:
    """`n` discrete blocks, capped at `max_blocks` (for small counts/queues)."""
    n = max(0, min(int(n or 0), max_blocks))
    return char * n
