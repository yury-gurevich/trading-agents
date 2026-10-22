"""Score one EXP-015 fold: fit on its train sessions, measure its test (S289).

Agent: tooling
Role: a fold's per-session rank ICs (ensemble, baseline, components, decay at 5 and
      20), its decile spreads, its net long-only top deciles, LightGBM's importances.
External I/O: none.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from scripts.exp015_models import Trainer, fit
from scripts.exp015_ranks import session_ic
from scripts.exp015_spec import (
    COST_BPS,
    DECILES,
    HORIZON,
    HORIZONS,
    MIN_NAMES,
    STEP_SESSIONS,
)

if TYPE_CHECKING:
    from scripts.exp015_folds import Fold
    from scripts.exp015_store import Panel

_BARRED = HORIZONS.index(HORIZON)


def score_fold(
    panel: Panel, x: np.ndarray, fold: Fold, trainer: Trainer
) -> dict[str, object]:
    """One fold's record; `x` is the universe's ranked features, row for row."""
    train = np.isin(panel.sessions, fold.train)
    test = np.isin(panel.sessions, fold.test)
    excess = panel.excess
    fitted = fit(x[train], excess[train, _BARRED], panel.sessions[train], trainer)
    days, lines = panel.sessions[test], panel.lines[test]
    scores = fitted.predict(x[test], days) | {"baseline": panel.baseline[test]}
    target = excess[test, _BARRED]
    ic = {name: session_ic(value, target, days) for name, value in scores.items()}
    decay = {
        f"{name}_h{h}": session_ic(scores[name], excess[test, k], days)
        for name in ("ensemble", "baseline")
        for k, h in enumerate(HORIZONS)
        if h != HORIZON
    }
    rebalances = tuple(sorted(set(days.tolist())))[::STEP_SESSIONS]
    raw = panel.returns[test, _BARRED]
    return {
        **fold.record(),
        "rows_train": int(train.sum()),
        "rows_test": int(test.sum()),
        "ic": ic,
        "decay": decay,
        "decile_spread": {
            name: decile_spread(scores[name], target, days)
            for name in ("ensemble", "baseline")
        },
        "top_decile": {
            name: top_decile(scores[name], raw, days, lines, rebalances)
            for name in ("ensemble", "baseline")
        },
        "importances": fitted.importances(),
    }


def decile_spread(
    prediction: np.ndarray, target: np.ndarray, days: np.ndarray
) -> float:
    """Mean over sessions of the top decile's mean target minus the bottom decile's."""
    spreads = []
    for day in sorted(set(days.tolist())):
        rows = np.flatnonzero(
            (days == day) & np.isfinite(prediction) & np.isfinite(target)
        )
        if len(rows) < MIN_NAMES:
            continue
        k = math.ceil(len(rows) / DECILES)
        ordered = rows[np.argsort(-prediction[rows], kind="stable")]
        spreads.append(float(target[ordered[:k]].mean() - target[ordered[-k:]].mean()))
    return float(np.mean(spreads)) if spreads else math.nan


def top_decile(
    prediction: np.ndarray,
    raw: np.ndarray,
    days: np.ndarray,
    lines: np.ndarray,
    rebalances: tuple[str, ...],
) -> dict[str, float]:
    """Equal weight in the top decile at each rebalance, COST_BPS a side."""
    weights: dict[str, float] = {}
    value, gross_value, periods = 1.0, 1.0, 0
    for day in rebalances:
        rows = np.flatnonzero(
            (days == day) & np.isfinite(prediction) & np.isfinite(raw)
        )
        if len(rows) < MIN_NAMES:
            continue
        k = math.ceil(len(rows) / DECILES)
        top = rows[np.argsort(-prediction[rows], kind="stable")[:k]]
        new = {str(line): 1.0 / k for line in lines[top]}
        traded = sum(
            abs(new.get(n, 0.0) - weights.get(n, 0.0)) for n in set(new) | set(weights)
        )
        gross = float(raw[top].mean())
        value *= 1.0 + gross - traded * COST_BPS / 10_000
        gross_value *= 1.0 + gross
        weights, periods = new, periods + 1
    return {
        "net_return": value - 1.0,
        "gross_return": gross_value - 1.0,
        "periods": periods,
    }
