"""EXP-013: does scaling position size by the regime label pay on this system?

Agent: tooling
Role: replay regime-weighted sizing against flat notional sizing and report the delta.
External I/O: reads the replay cache (scripts/replay_dataset.py); prints tables.

Reads the cache rather than the network, so it re-runs in seconds at zero cost.
Thresholds and the stop rule are the deployed ones, read from the code they live
in rather than restated here.

    uv run python scripts/replay_dataset.py          # once, to build the cache
    uv run python scripts/exp013_regime_sizing.py
"""

from __future__ import annotations

import collections
import random
import statistics
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.replay_dataset import load  # noqa: E402

from agents.analyst.settings import AnalystSettings  # noqa: E402
from agents.provider.domain.regime import classify_regime  # noqa: E402
from agents.provider.settings import ProviderSettings  # noqa: E402
from agents.provider.sources import RegimeInputs  # noqa: E402

HORIZON = 10
GRID = 5
ATR_WINDOW = 14
FIRST = "2017-01-03"
ORDER = ("risk_on", "neutral", "risk_off", "high_volatility", "extreme_volatility")

# "Less risk when the market is dangerous" - the ADR-0031 direction, two strengths.
# The inverted arm is not a proposal; it prices the gradient's direction.
ARMS = {
    "mild     (1.1/1.0/0.9/0.8/0.6)": (1.1, 1.0, 0.9, 0.8, 0.6),
    "strong   (1.2/1.0/0.8/0.6/0.4)": (1.2, 1.0, 0.8, 0.6, 0.4),
    "INVERTED (0.8/1.0/1.2/1.4/1.6)": (0.8, 1.0, 1.2, 1.4, 1.6),
}


def _stop_pct(atr: float, close: float, settings: AnalystSettings) -> float:
    """The deployed ADR-0013 scaled stop: clamp(mult x ATR/close, floor, ceiling)."""
    raw = settings.scaled_stop_atr_multiplier * atr / close
    return min(
        max(raw, settings.scaled_stop_floor_pct), settings.scaled_stop_ceiling_pct
    )


def decisions() -> list[tuple[str, float, float, str]]:
    """Return one tuple per grid decision: regime, returns, ticker."""
    provider, stops = ProviderSettings(), AnalystSettings()
    vix, bars = load()
    out: list[tuple[str, float, float, str]] = []
    for ticker, rows in bars.items():
        rows = sorted(rows)
        dates = [r[0] for r in rows]
        high = [r[2] for r in rows]
        low = [r[3] for r in rows]
        close = [r[4] for r in rows]
        true_range = [0.0] * len(rows)
        for i in range(1, len(rows)):
            true_range[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1]),
            )
        start = next((i for i, day in enumerate(dates) if day >= FIRST), None)
        if start is None:
            continue
        for i in range(max(start, ATR_WINDOW + 1), len(rows) - HORIZON, GRID):
            level = vix.get(dates[i])
            if level is None or close[i] <= 0:
                continue
            label = classify_regime(RegimeInputs(vix=level, as_of=dates[i]), provider)
            atr = sum(true_range[i - ATR_WINDOW + 1 : i + 1]) / ATR_WINDOW
            stop = _stop_pct(atr, close[i], stops)
            raw = (close[i + HORIZON] / close[i] - 1.0) * 100.0
            floor_price = close[i] * (1 - stop)
            stopped = any(low[j] <= floor_price for j in range(i + 1, i + 1 + HORIZON))
            out.append((label, raw, -stop * 100.0 if stopped else raw, ticker))
    return out


def _table(rows: list[tuple[str, float, float, str]], column: int, title: str) -> None:
    grouped: dict[str, list[float]] = collections.defaultdict(list)
    for record in rows:
        grouped[record[0]].append(record[column])
    print(f"\n{title}")
    head = f"{'regime':<20} {'n':>7} {'mean %':>8} {'stdev':>8}"
    print(f"{head} {'mean/sd':>8} {'win %':>7}")
    for label in ORDER:
        values = grouped.get(label, [])
        if not values:
            continue
        deviation = statistics.pstdev(values)
        wins = sum(1 for v in values if v > 0) / len(values) * 100
        print(
            f"{label:<20} {len(values):>7} {statistics.mean(values):>8.3f} "
            f"{deviation:>8.3f} "
            f"{statistics.mean(values) / deviation:>8.4f} {wins:>7.1f}"
        )


def _arms(rows: list[tuple[str, float, float, str]], column: int, title: str) -> None:
    print(f"\n{title}")
    champion = sum(record[column] for record in rows)
    print(f"  {'champion (flat 1.0 weight)':<34} {champion:>12,.0f}")
    for name, weights in ARMS.items():
        weight = dict(zip(ORDER, weights, strict=True))
        total = sum(record[column] * weight[record[0]] for record in rows)
        print(f"  {name:<34} {total:>12,.0f}   delta {total - champion:>+9,.0f}")


def _bootstrap(
    rows: list[tuple[str, float, float, str]], column: int, draws: int
) -> None:
    weight = dict(zip(ORDER, ARMS["strong   (1.2/1.0/0.8/0.6/0.4)"], strict=True))
    per_ticker: dict[str, float] = collections.defaultdict(float)
    for record in rows:
        per_ticker[record[3]] += record[column] * weight[record[0]] - record[column]
    names = list(per_ticker)
    rng = random.Random(20260922)  # noqa: S311 - resampling, not cryptography.
    totals = sorted(
        sum(per_ticker[rng.choice(names)] for _ in names) for _ in range(draws)
    )
    negative = sum(1 for total in totals if total < 0) / len(totals) * 100
    print(
        f"\nticker-cluster bootstrap, strong arm, {draws} resamples, "
        f"{len(names)} names:"
        f"\n  95% CI [{totals[draws // 40]:,.0f}, "
        f"{totals[-draws // 40]:,.0f}] pct-points, {negative:.1f}% negative"
    )


def main(argv: list[str]) -> int:
    del argv
    rows = decisions()
    print(f"decisions: {len(rows):,}")
    _table(rows, 1, "Forward 10-session return, no bracket")
    _table(rows, 2, "Forward 10-session return, deployed stop bracket + timeout")
    _arms(rows, 1, "Summed weighted return, no bracket (pct-points)")
    _arms(rows, 2, "Summed weighted return, deployed stop bracket (pct-points)")
    _bootstrap(rows, 2, 2000)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
