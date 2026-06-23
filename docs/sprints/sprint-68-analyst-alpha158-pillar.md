<!-- Agent: planning | Role: sprint handover -->
# Sprint 68 — Analyst: Alpha158 feature pillar (Qlib Phase Q2)

**Status:** planned · **Branch:** `sprint-68-analyst-alpha158-pillar`
**Build phase:** qlib Phase Q2 · **Effort: M (3–5 days)**
**Prerequisite:** S59 shipped (Q1 proven; LightGBM behind agent boundary established).

## Goal

Add a **fifth scoring pillar** to the analyst — an Alpha158-derived composite built from
multi-horizon momentum, volatility, and range features over OHLCV history. The pillar is
**deterministic, pure-Python, no pyqlib** (pyqlib is uninstallable on Python 3.13 — same
constraint as Q1). Governed by a tunable weight defaulting to 0.00 (off); operator enables
after 20-day IC comparison against the existing technical pillar.

The invariants from [R001 §"For Coding Agents"](../research/qlib-integration/qlib-integration.md) bind verbatim:

- Alpha158 logic lives inside `agents/analyst/domain/` only; no symbol crosses the boundary.
- No new contract type; `ScoreBreakdown` gains `alpha158_score: float | None = None`.
- Default weight 0.00 — existing tests and coverage are unaffected when weight is 0.

## Context

- Alpha158 formulas are published (arxiv 2009.11189); they are reproducible from OHLCV without
  pyqlib. This sprint implements the time-series subset (20 features); cross-sectional rank
  features (QTLU, QTLD) are deferred to Q2-follow-on once the per-ticker path proves stable.
- Existing analyst pillars: technical (RSI, MACD, Bollinger, ATR, EMA), fundamental, sentiment,
  relative strength within technical. This pillar is additive.
- `contracts/analyst.py` is unchanged; `ScoreBreakdown` is internal to the agent, not a contract.
- The `_composite` function in `scoring.py` renormalises present weights; Alpha158 follows the
  same pattern as the existing optional fundamental and sentiment pillars.

## Parts

### A — `agents/analyst/domain/alpha_features.py`

```python
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.provider import OHLCVBar


@dataclass(frozen=True)
class AlphaFeatureRow:
    """Computed Alpha158 subset for one ticker window."""
    # Rate-of-change at four horizons
    roc_5: float; roc_10: float; roc_20: float; roc_60: float
    # Return volatility (std of daily returns) at four horizons
    std_5: float; std_10: float; std_20: float; std_60: float
    # Max daily return in window (norm by current close)
    max_5: float; max_10: float; max_20: float; max_60: float
    # Min daily return in window (norm by current close)
    min_5: float; min_10: float; min_20: float; min_60: float
    # Days-since-max (recency of local high), normalised by window length
    imax_10: float; imax_20: float; imax_60: float
    # Days-since-min (recency of local low), normalised by window length
    imin_10: float; imin_20: float; imin_60: float


_WINDOWS = (5, 10, 20, 60)


def compute_alpha_features(bars: tuple[OHLCVBar, ...]) -> AlphaFeatureRow | None:
    """Compute Alpha158 subset from date-sorted OHLCV bars.

    Returns None when fewer than 62 bars are available (need 60-bar window + 2 for
    return computation).
    """
    if len(bars) < 62:
        return None
    closes = [b.close for b in bars]
    n = len(closes)
    daily_returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, n)]

    def roc(w: int) -> float:
        return (closes[-1] - closes[-1 - w]) / closes[-1 - w]

    def std(w: int) -> float:
        rets = daily_returns[-w:]
        mean = sum(rets) / w
        variance = sum((r - mean) ** 2 for r in rets) / w
        return math.sqrt(variance)

    def max_ret(w: int) -> float:
        return max(daily_returns[-w:])

    def min_ret(w: int) -> float:
        return min(daily_returns[-w:])

    def imax(w: int) -> float:
        window = closes[-w - 1:]          # w+1 closes → w returns
        idx = window.index(max(window))   # 0 = oldest, w = most recent
        return 1.0 - idx / w             # 1 = max is most recent, 0 = oldest

    def imin(w: int) -> float:
        window = closes[-w - 1:]
        idx = window.index(min(window))
        return 1.0 - idx / w

    return AlphaFeatureRow(
        roc_5=roc(5), roc_10=roc(10), roc_20=roc(20), roc_60=roc(60),
        std_5=std(5), std_10=std(10), std_20=std(20), std_60=std(60),
        max_5=max_ret(5), max_10=max_ret(10), max_20=max_ret(20), max_60=max_ret(60),
        min_5=min_ret(5), min_10=min_ret(10), min_20=min_ret(20), min_60=min_ret(60),
        imax_10=imax(10), imax_20=imax(20), imax_60=imax(60),
        imin_10=imin(10), imin_20=imin(20), imin_60=imin(60),
    )
```

Tests: `agents/analyst/tests/test_analyst_alpha_features.py`

- Known price sequence → verify every field numerically (ROC, STD, MAX, MIN, IMAX, IMIN).
- `None` returned when fewer than 62 bars.
- All 20 fields present and finite.

### B — `agents/analyst/domain/alpha_pillar.py`

```python
from __future__ import annotations
import dataclasses, math

from agents.analyst.domain.alpha_features import AlphaFeatureRow


def score_alpha158(
    features: AlphaFeatureRow,
    universe: tuple[AlphaFeatureRow, ...],
) -> float:
    """Return a 0–100 score via equal-weighted cross-sectional z-score aggregation.

    Each of the 20 features is z-normalised across the universe of candidate feature
    rows, then averaged; the mean z-score is mapped to [0, 100] via the logistic
    function centred at 0 (z=0 → 50, one-sigma above → ~73, two-sigma → ~88).
    """
    fields = [f.name for f in dataclasses.fields(AlphaFeatureRow)]
    rows = list(universe) if features in universe else [*universe, features]

    z_scores: list[float] = []
    for field in fields:
        vals = [getattr(r, field) for r in rows]
        mean = sum(vals) / len(vals)
        std = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
        z = (getattr(features, field) - mean) / std if std > 1e-9 else 0.0
        z_scores.append(z)

    mean_z = sum(z_scores) / len(z_scores)
    return 100.0 / (1.0 + math.exp(-mean_z))      # logistic → (0, 100)
```

Tests: `agents/analyst/tests/test_analyst_alpha_pillar.py`

- Single-element universe → score == 50.0 (z = 0 for every field).
- Known two-element universe where one ticker dominates on all features → score > 60.
- Features from a lower-performing ticker → score < 50.

### C — Integration: `scoring.py`, `agent.py`, `settings.py`

**`agents/analyst/settings.py`** — add one tunable:

```python
alpha158_pillar_weight: float = tunable(
    0.00,
    why=(
        "Fifth scoring pillar weight for the Alpha158 multi-horizon momentum/volatility "
        "composite. Default 0.00 = off; operator enables after 20-day shadow IC comparison "
        "against the existing technical pillar shows non-trivial incremental information "
        "(target: Δ IC ≥ 0.02 on the held-out window)."
    ),
    ge=0.0,
    le=1.0,
)
```

**`agents/analyst/domain/scoring.py`** — `score_candidate` gains `alpha_score`:

```python
def score_candidate(
    candidate,
    bars, fundamentals, benchmark_bars, news,
    settings,
    *,
    alpha_score: float | None = None,   # pre-computed; None when weight == 0.00
) -> ScoreBreakdown:
```

`_composite` gains an `alpha` argument following the `fundamental` / `sentiment` pattern:
all present weights are renormalised over the active set before blending.

`ScoreBreakdown` gains `alpha158_score: float | None = None`.

**`agents/analyst/agent.py`** — in `_analyze`, before the per-candidate loop:

```python
from agents.analyst.domain.alpha_features import compute_alpha_features
from agents.analyst.domain.alpha_pillar import score_alpha158

alpha_scores: dict[str, float] = {}
if self._settings.alpha158_pillar_weight > 0.0:
    feature_rows = {
        ticker: compute_alpha_features(tuple(bars.get(ticker, ())))
        for ticker in {c.ticker for c in candidate_set.candidates}
        if (bars := _bars_by_ticker(market.bars))
    }
    universe = tuple(v for v in feature_rows.values() if v is not None)
    for ticker, row in feature_rows.items():
        if row is not None:
            alpha_scores[ticker] = score_alpha158(row, universe)
```

Then pass `alpha_score=alpha_scores.get(candidate.ticker)` to each `score_candidate` call.

Tests: the existing `test_analyst_pubsub.py` exercises the `weight == 0.00` path unchanged.
Add `test_analyst_alpha_integration.py` to wire a 3-candidate universe with 70 bars each and
`alpha158_pillar_weight=0.20`; assert `ScoreBreakdown.alpha158_score is not None` for all
candidates with sufficient history, and score is in [0, 100].

## Exit criteria

- [ ] `ruff check .` — no violations
- [ ] `uv run pytest` — 863+ tests, 100.00% coverage
- [ ] `score_candidate` with default settings (weight 0.00) returns same ScoreBreakdown shape
      as before (alpha158_score is None)
- [ ] `compute_alpha_features` returns None when bars < 62
- [ ] `score_alpha158` maps single-element universe to ≈ 50.0
- [ ] `ScoreBreakdown.alpha158_score` is populated and in [0, 100] when weight > 0 and
      the ticker has ≥ 62 bars
- [ ] `alpha158_pillar_weight` documented in `settings.py` with `tunable()` justification

## Deferred

- Cross-sectional rank features (QTLU, QTLD, RANK) — need full market universe in a single
  call; worth a separate mini-sprint once the time-series path validates.
- Promoting weight above 0.00 — operator decision after 20+ trading days of scorecard data.
- CI secret / env injection for `ANALYST_ALPHA158_PILLAR_WEIGHT` in the Azure deployment —
  deferred to the law-backfill sprint (S69) which wires CAP+PARAM sections for all agents.
