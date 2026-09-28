"""Barrier test bed models: simulated paths and their stop / target / neither shares.

Agent: tooling
Role: the plain bootstrap baseline (EXP-011's `all_history`) and the path scorer every
      simulation model shares. A model is any function of a stock's rows, the decision
      index and the barriers that returns (P stop first, P target first, P neither).
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scripts.barrier_testbed import H

if TYPE_CHECKING:
    from scripts.barrier_testbed import Row


def bootstrap_probs(
    rows: list[Row],
    t: int,
    stop: float,
    target: float,
    rng: np.random.Generator,
    n_paths: int = 1000,
    lo: int = 0,
) -> tuple[float, float, float]:
    """EXP-011's plain bootstrap: each simulated day an independent past day."""
    hi, low, cl = (np.array([row[k] for row in rows]) for k in (2, 3, 4))
    rh, rl, rc = hi[1:] / cl[:-1], low[1:] / cl[:-1], cl[1:] / cl[:-1]
    idx = rng.integers(lo, t, (n_paths, H))
    level = np.cumprod(rc[idx], axis=1)
    prev = np.concatenate([np.ones((n_paths, 1)), level[:, :-1]], axis=1)
    return path_probs(prev, rh[idx], rl[idx], stop, target)


def path_probs(
    prev: np.ndarray,
    rel_high: np.ndarray,
    rel_low: np.ndarray,
    stop: float,
    target: float,
) -> tuple[float, float, float]:
    """Shares of simulated paths ending stop / target / neither (low before high)."""
    hit_stop = prev * rel_low <= 1 - stop
    hit_target = prev * rel_high >= 1 + target
    first_stop = np.where(hit_stop.any(1), hit_stop.argmax(1), H)
    first_target = np.where(hit_target.any(1), hit_target.argmax(1), H)
    p_stop = float(np.mean((first_stop < H) & (first_stop <= first_target)))
    p_target = float(np.mean((first_target < H) & (first_target < first_stop)))
    return (p_stop, p_target, 1 - p_stop - p_target)
