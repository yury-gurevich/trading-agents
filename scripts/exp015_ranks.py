"""EXP-015's cross-sectional ranks and per-session Spearman rank IC (S289).

Agent: tooling
Role: rank a value within each group to [0, 1] (ties averaged; NaN or alone 0.5),
      build the twenty ranked features of a universe, and give each session's rank IC.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scripts.exp015_spec import LINE_FEATURES, MIN_NAMES, RETURN_FEATURES

if TYPE_CHECKING:
    from scripts.exp015_store import Panel


def group_ranks(values: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """Average rank within each group, scaled to [0, 1]; NaN and singletons 0.5."""
    out = np.full(len(values), 0.5)
    finite = np.flatnonzero(np.isfinite(values))
    if not len(finite):
        return out
    codes = np.unique(groups[finite], return_inverse=True)[1]
    vals = values[finite]
    order = np.lexsort((vals, codes))
    s_codes, s_vals = codes[order], vals[order]
    group_start = np.r_[True, s_codes[1:] != s_codes[:-1]]
    gid = np.cumsum(group_start) - 1
    starts = np.flatnonzero(group_start)
    sizes = np.diff(np.r_[starts, len(order)])
    position = np.arange(len(order)) - starts[gid]
    tie_start = group_start | np.r_[True, s_vals[1:] != s_vals[:-1]]
    tid = np.cumsum(tie_start) - 1
    average = (np.bincount(tid, weights=position) / np.bincount(tid))[tid]
    size = sizes[gid]
    out[finite[order]] = np.where(size > 1, average / np.maximum(size - 1, 1), 0.5)
    return out


def ranked_features(panel: Panel) -> np.ndarray:
    """rows x FEATURES: line features ranked per session, returns per sector."""
    columns = [
        group_ranks(panel.features[:, k], panel.sessions)
        for k in range(len(LINE_FEATURES))
    ]
    sector_groups = np.char.add(np.char.add(panel.sessions, "|"), panel.sectors)
    no_sector = panel.sectors == ""
    for name in RETURN_FEATURES:
        ranked = group_ranks(
            panel.features[:, LINE_FEATURES.index(name)], sector_groups
        )
        ranked[no_sector] = 0.5
        columns.append(ranked)
    return np.column_stack(columns)


def session_ic(
    prediction: np.ndarray, target: np.ndarray, sessions: np.ndarray
) -> dict[str, float]:
    """Spearman IC per session; at least MIN_NAMES rows with both values, not flat."""
    usable = np.isfinite(prediction) & np.isfinite(target)
    days = sessions[usable]
    if not len(days):
        return {}
    x = group_ranks(prediction[usable], days)
    y = group_ranks(target[usable], days)
    keys, codes = np.unique(days, return_inverse=True)

    def total(values: np.ndarray) -> np.ndarray:
        return np.bincount(codes, weights=values, minlength=len(keys))

    n = np.bincount(codes, minlength=len(keys)).astype(float)
    sx, sy = total(x), total(y)
    cov = total(x * y) - sx * sy / n
    vx = total(x * x) - sx * sx / n
    vy = total(y * y) - sy * sy / n
    out: dict[str, float] = {}
    for k, key in enumerate(keys):
        if n[k] >= MIN_NAMES and vx[k] > 1e-12 and vy[k] > 1e-12:
            out[str(key)] = float(cov[k] / np.sqrt(vx[k] * vy[k]))
    return out
