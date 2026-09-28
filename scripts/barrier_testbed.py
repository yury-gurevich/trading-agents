"""Barrier test bed: decisions, outcomes and baselines behind EXP-011 and EXP-016-018.

Agent: tooling
Role: rebuild EXP-011's decision set from daily bars (S211's barriers, the
      low-before-high outcome) with the yearly climatology and the plain bootstrap
      as baselines. Models live in `barrier_testbed_models`; scoring in
      `barrier_testbed_score`.
External I/O: none, except `main`, which reads the replay cache
              (`scripts/replay_dataset.py`).

    uv run python scripts/barrier_testbed.py --reproduce  # EXP-011's set, else exit 1
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if TYPE_CHECKING:
    Row = tuple[str, float, float, float, float]  # date, open, high, low, close
    Bars = dict[str, list[Row]]

H = 10  # sessions a decision is followed for
LOOKBACK = 120  # settled windows behind the target
ATR_N = 14
STEP = 5  # a decision every 5th session
MIN_HISTORY = 251  # prior bars a decision needs
FIRST_DECISION = "2017-01-03"
STOP_FLOOR, STOP_CAP = 0.025, 0.08
OUTCOMES = ("stop_first", "target_first", "neither")
EXP011 = (47485, (0.285, 0.480, 0.235))


@dataclass(frozen=True)
class Decision:
    """One decision at the close of bar ``t`` of stock ``sym``."""

    sym: str
    day: str
    t: int
    stop: float
    target: float
    outcome: int  # index into OUTCOMES
    regime: int


def regime_label(vix: float) -> int:
    """The provider's live thresholds: risk_on, neutral, risk_off, high_vol, extreme."""
    if vix >= 35:
        return 4
    if vix >= 25:
        return 3
    if vix >= 20:
        return 2
    return 0 if vix <= 15 else 1


def barriers(
    hi: np.ndarray, lo: np.ndarray, cl: np.ndarray, t: int
) -> tuple[float, float]:
    """S211's stop (clamped 2 x ATR14 %) and target (median 10-session best rise)."""
    tr = np.maximum.reduce(
        [hi[1:] - lo[1:], abs(hi[1:] - cl[:-1]), abs(lo[1:] - cl[:-1])]
    )
    atr_pct = tr[t - ATR_N : t].mean() / cl[t]
    stop = min(max(2 * atr_pct, STOP_FLOOR), STOP_CAP)
    anchors = range(t - H - LOOKBACK + 1, t - H + 1)
    rises = [max(hi[a + 1 : a + 1 + H].max() / cl[a] - 1, 0.0) for a in anchors]
    return float(stop), min(float(np.median(rises)), 1.0)


def outcome(
    hi: np.ndarray, lo: np.ndarray, cl: np.ndarray, t: int, stop: float, target: float
) -> int:
    """0 stop first, 1 target first, 2 neither; touching both counts as the stop."""
    for k in range(t + 1, t + H + 1):
        if lo[k] <= cl[t] * (1 - stop):
            return 0
        if hi[k] >= cl[t] * (1 + target):
            return 1
    return 2


def decision_days(bars: Bars) -> set[str]:
    """Every 5th session of the union calendar, from the first on/after 2017-01-03."""
    calendar = sorted({row[0] for rows in bars.values() for row in rows})
    start = next(i for i, day in enumerate(calendar) if day >= FIRST_DECISION)
    return set(calendar[start::STEP])


def build_decisions(bars: Bars, vix: dict[str, float]) -> list[Decision]:
    """EXP-011's decisions: history before, a full horizon after, a VIX close."""
    days = decision_days(bars)
    out: list[Decision] = []
    for sym, rows in sorted(bars.items()):
        hi, lo, cl = (np.array([row[k] for row in rows]) for k in (2, 3, 4))
        for t, row in enumerate(rows):
            day = row[0]
            if (
                day not in days
                or t < MIN_HISTORY
                or t + H >= len(rows)
                or day not in vix
            ):
                continue
            stop, target = barriers(hi, lo, cl, t)
            result = outcome(hi, lo, cl, t, stop, target)
            out.append(
                Decision(sym, day, t, stop, target, result, regime_label(vix[day]))
            )
    return out


def climatology(decisions: list[Decision]) -> np.ndarray:
    """Outcome shares of all earlier years; the first year uses the first 500 cases."""
    y = np.eye(3)[[d.outcome for d in decisions]]
    years = np.array([int(d.day[:4]) for d in decisions])
    clim = np.zeros_like(y)
    for i, year in enumerate(years):
        prior = years < year
        clim[i] = y[prior].mean(0) if prior.sum() > 500 else y[:500].mean(0)
    return clim


def _load_cache() -> tuple[dict[str, float], Bars]:  # pragma: no cover - reads OneDrive
    from scripts.replay_dataset import load

    return load()


def main(argv: list[str]) -> int:
    """`--reproduce`: rebuild from the replay cache and compare with EXP-011."""
    parser = argparse.ArgumentParser(
        description="Barrier test bed (EXP-011 decisions)."
    )
    parser.add_argument("--reproduce", action="store_true", help="check EXP-011's set")
    parser.parse_args(argv)
    vix, bars = _load_cache()
    decisions = build_decisions(bars, vix)
    shares = tuple(
        round(float(v), 3) for v in np.eye(3)[[d.outcome for d in decisions]].mean(0)
    )
    names = len({d.sym for d in decisions})
    print(
        f"decisions {len(decisions)} ({len({d.day for d in decisions})} dates x "
        f"{names} names)"
    )
    print(f"realised stop / target / neither {shares}")
    ok = (len(decisions), shares) == EXP011
    print("reproduces EXP-011" if ok else f"MISMATCH: EXP-011 has {EXP011}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
