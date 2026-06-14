"""Pure-Python geometric chart-pattern detection (swing points -> patterns).

Agent: analyst
Role: find swing highs/lows and classify double/H&S/triangle patterns; no pandas.
External I/O: none.
"""

from __future__ import annotations

_SWING_MIN_BARS = 5
_PATTERN_MIN_BARS = 20
_PATTERN_MIN_SWINGS = 3
_MIN_INDEX_GAP = 5
_DOUBLE_CONF_CAP = 0.85
_SHOULDER_CONF = 0.70
_TRIANGLE_CONF = 0.65

_Swing = tuple[int, float, str]


def find_swing_points(
    closes: list[float], highs: list[float], lows: list[float], min_swing_pct: float
) -> list[_Swing]:
    """Local swing highs/lows kept only when far enough from the last close."""
    if len(closes) < _SWING_MIN_BARS:
        return []
    swings: list[_Swing] = []
    for index in range(2, len(closes) - 2):
        neighbours = (index - 2, index - 1, index + 1, index + 2)
        if all(highs[index] > highs[j] for j in neighbours):
            swings.append((index, highs[index], "high"))
        elif all(lows[index] < lows[j] for j in neighbours):
            swings.append((index, lows[index], "low"))
    last = closes[-1]
    if not swings or last == 0:
        return swings
    threshold = min_swing_pct * 0.5
    return [s for s in swings if abs(s[1] - last) / last * 100 >= threshold]


def geometric_patterns(
    closes: list[float],
    highs: list[float],
    lows: list[float],
    lookback: int,
    min_swing_pct: float,
) -> tuple[str, float] | None:
    """First matching geometric pattern over the last ``lookback`` bars, or ``None``."""
    n = min(lookback, len(closes))
    if n < _PATTERN_MIN_BARS:
        return None
    close_w, high_w, low_w = closes[-n:], highs[-n:], lows[-n:]
    swings = find_swing_points(close_w, high_w, low_w, min_swing_pct)
    if len(swings) < _PATTERN_MIN_SWINGS:
        return None
    tolerance = min_swing_pct / 100.0
    last = close_w[-1]
    highs_s = [(i, p) for i, p, kind in swings if kind == "high"]
    lows_s = [(i, p) for i, p, kind in swings if kind == "low"]
    return (
        _double_pattern(highs_s, lows_s, last, tolerance)
        or _shoulder_pattern(highs_s, lows_s, last, tolerance)
        or _triangle_pattern(highs_s, lows_s, tolerance)
    )


def _matching_swings(a: float, b: float, tolerance: float) -> bool:
    """Two swing prices match when within ``tolerance`` of each other."""
    return abs(a - b) / a < tolerance


def _double_pattern(
    highs_s: list[tuple[int, float]],
    lows_s: list[tuple[int, float]],
    last: float,
    tolerance: float,
) -> tuple[str, float] | None:
    """Double top (two matched highs) or double bottom (two matched lows)."""
    if len(highs_s) >= 2:
        (i1, a), (i2, b) = highs_s[-2], highs_s[-1]
        gap = i2 - i1 >= _MIN_INDEX_GAP
        if _matching_swings(a, b, tolerance) and gap and last < b * (1 - tolerance):
            conf = round(min(1 - abs(a - b) / a / tolerance, _DOUBLE_CONF_CAP), 2)
            return "double_top", conf
    if len(lows_s) >= 2:
        (i1, a), (i2, b) = lows_s[-2], lows_s[-1]
        gap = i2 - i1 >= _MIN_INDEX_GAP
        if _matching_swings(a, b, tolerance) and gap and last > b * (1 + tolerance):
            conf = round(min(1 - abs(a - b) / a / tolerance, _DOUBLE_CONF_CAP), 2)
            return "double_bottom", conf
    return None


def _shoulder_pattern(
    highs_s: list[tuple[int, float]],
    lows_s: list[tuple[int, float]],
    last: float,
    tolerance: float,
) -> tuple[str, float] | None:
    """Head-and-shoulders (three highs) or its inverse (three lows)."""
    if len(highs_s) >= 3:
        s1, head, s2 = highs_s[-3][1], highs_s[-2][1], highs_s[-1][1]
        shoulders = _matching_swings(s1, s2, tolerance)
        if head > s1 and head > s2 and shoulders and last < min(s1, s2):
            return "head_and_shoulders", _SHOULDER_CONF
    if len(lows_s) >= 3:
        s1, head, s2 = lows_s[-3][1], lows_s[-2][1], lows_s[-1][1]
        shoulders = _matching_swings(s1, s2, tolerance)
        if head < s1 and head < s2 and shoulders and last > max(s1, s2):
            return "inverse_head_and_shoulders", _SHOULDER_CONF
    return None


def _triangle_pattern(
    highs_s: list[tuple[int, float]],
    lows_s: list[tuple[int, float]],
    tolerance: float,
) -> tuple[str, float] | None:
    """Ascending (flat highs, rising lows) or descending (flat lows, falling highs)."""
    if len(highs_s) < 2 or len(lows_s) < 2:
        return None
    high1, high2 = highs_s[-2][1], highs_s[-1][1]
    low1, low2 = lows_s[-2][1], lows_s[-1][1]
    half = tolerance * 0.5
    if _matching_swings(high1, high2, tolerance) and low2 > low1 * (1 + half):
        return "ascending_triangle", _TRIANGLE_CONF
    if _matching_swings(low1, low2, tolerance) and high2 < high1 * (1 - half):
        return "descending_triangle", _TRIANGLE_CONF
    return None
