"""S237 Layer 2: the same code chained, live inputs swapped for the cache's in order.

Agent: tooling
Role: run scanner -> analyst -> PM per cumulative swap step on the live regime,
      sectors and book, and say what each swap moved (an attribution by sequence).
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scripts.replay_fidelity_cache import cache_bars, lines_for, sip_volume
from scripts.replay_fidelity_stages import replay_analyst, replay_pm, replay_scanner

if TYPE_CHECKING:
    from scripts.replay_fidelity_cache import CacheContext
    from scripts.replay_fidelity_inputs import SessionInputs
    from scripts.replay_settings import ReplaySettings

    from contracts.provider import MarketData

# The fixed order DL-237 and the spec set, so every report reads the same way.
STEPS = (
    "0_live",
    "1_sip_volume",
    "2_no_fundamentals",
    "3_no_news",
    "4_no_earnings",
    "5_cache_bars",
)
_JUDGED = frozenset({"buy", "sell"})
Decided = tuple[frozenset[str], frozenset[str], frozenset[str]]


def layer2_rows(
    inputs: SessionInputs, settings: ReplaySettings, context: CacheContext
) -> list[dict[str, Any]]:
    """Return one row per step, or none when the session cannot be replayed."""
    if (
        inputs.market is None
        or inputs.window_end is None
        or inputs.regime is None
        or not inputs.tickers
    ):
        return []
    session = inputs.window_end
    lines = lines_for(context, inputs.tickers, session)
    live = inputs.market
    volume, unswapped = sip_volume(context, live, lines)
    fundamentals = volume.model_copy(update={"fundamentals": {}})
    news = fundamentals.model_copy(update={"news": {}})
    earnings = news.model_copy(update={"earnings": {}, "earnings_horizon_days": None})
    markets = (
        live,
        volume,
        fundamentals,
        news,
        earnings,
        cache_bars(context, earnings, lines, session, settings),
    )
    decided = [_chain(inputs, settings, market) for market in markets]
    rows: list[dict[str, Any]] = []
    for index, step in enumerate(STEPS):
        now, before = decided[index], decided[max(index - 1, 0)]
        rows.append(
            {
                "session": inputs.session,
                "step": step,
                "candidates": _join(now[0]),
                "recommendations": _join(now[1]),
                "approvals": _join(now[2]),
                "candidates_jaccard": _jaccard(decided[0][0], now[0]),
                "approvals_jaccard": _jaccard(decided[0][2], now[2]),
                "candidates_entered": _join(now[0] - before[0]),
                "candidates_left": _join(before[0] - now[0]),
                "approvals_entered": _join(now[2] - before[2]),
                "approvals_left": _join(before[2] - now[2]),
                "unswapped_volume_bars": unswapped if step == STEPS[1] else "",
            }
        )
    return rows


def _chain(
    inputs: SessionInputs, settings: ReplaySettings, market: MarketData
) -> Decided:
    """Scanner -> analyst -> PM, each fed the step's own upstream output."""
    candidates = replay_scanner(inputs, settings, market)
    assert candidates is not None  # snapshot, tickers and as-of checked by the caller
    recommendations = replay_analyst(inputs, settings, candidates, market)
    assert recommendations is not None  # the regime is checked by the caller
    approvals = replay_pm(inputs, settings, recommendations, market)
    assert approvals is not None
    return (
        frozenset(item.ticker for item in candidates.candidates),
        frozenset(
            item.ticker
            for item in recommendations.recommendations
            if item.action in _JUDGED
        ),
        frozenset(item.ticker for item in approvals.approved),
    )


def _jaccard(first: frozenset[str], other: frozenset[str]) -> float:
    union = first | other
    return len(first & other) / len(union) if union else 1.0


def _join(tickers: frozenset[str]) -> str:
    return " ".join(sorted(tickers))
