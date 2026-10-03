"""The synthetic scenarios: named market situations an expert should recognise.

`expert_view` is the planner's draft of what a competent reader should conclude. It is a
hypothesis for the operator to approve or correct (DL-264, decision 3), not ground truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field

GOOD_FUND = {
    "peBasicExclExtraTTM": 19.0,
    "roeTTM": 22.0,
    "netProfitMarginTTM": 18.0,
    "currentRatioQuarterly": 1.7,
    "pbQuarterly": 3.5,
    "totalDebt/totalEquityQuarterly": 0.6,
    "epsGrowthTTMYoy": 14.0,
    "revenueGrowthTTMYoy": 9.0,
}
RICH_FUND = {**GOOD_FUND, "peBasicExclExtraTTM": 48.0, "pbQuarterly": 11.0}
TRAP_FUND = {
    "peBasicExclExtraTTM": 7.5,
    "roeTTM": 6.0,
    "netProfitMarginTTM": 4.0,
    "currentRatioQuarterly": 1.1,
    "pbQuarterly": 0.9,
    "totalDebt/totalEquityQuarterly": 1.8,
    "epsGrowthTTMYoy": -22.0,
    "revenueGrowthTTMYoy": -9.0,
}
NEUTRAL_NEWS = ("Company presents at industry conference", "Analyst maintains rating")


@dataclass(frozen=True)
class Scenario:
    name: str
    ticker: str
    sector: str
    segments: list[tuple[int, float]]
    fundamentals: dict[str, float]
    expert_view: str
    news: tuple[str, ...] = NEUTRAL_NEWS
    provider_sentiment: float = 0.1
    earnings_in_days: int = 40
    regime: str = "neutral"
    vix: float = 16.5
    holdings: dict[str, list[tuple[int, float]]] = field(default_factory=dict)  # held ticker -> its segments
    held_sector: dict[str, str] = field(default_factory=dict)
    wiggle: float = 0.006
    phase: float = 1.3


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        "extended_leader",
        "LEAD",
        "Technology",
        [(240, 0.0012), (60, 0.0045)],
        RICH_FUND,
        "Strong, extended momentum leader: overbought, far above its 200-day average, expensive. "
        "The risk is a pullback; the overbought reading is a timing caution, not a reason to reject alone.",
    ),
    Scenario(
        "steady_compounder",
        "QUAL",
        "Industrials",
        [(300, 0.0011)],
        GOOD_FUND,
        "Quality at a reasonable price in a steady uptrend: valuation, growth and trend agree. "
        "A clean buy unless risk or portfolio facts say otherwise.",
    ),
    Scenario(
        "falling_knife",
        "KNIF",
        "Consumer Discretionary",
        [(230, 0.0040), (70, -0.0060)],
        GOOD_FUND,
        "A big run-up that has broken sharply in the last three months: falling, oversold, negative MACD, but "
        "the 1-year return still clears the scanner. Oversold sub-scores prop up the technical score; they do "
        "not support a buy while the trend is down.",
        wiggle=0.014,
    ),
    Scenario(
        "value_trap",
        "TRAP",
        "Materials",
        [(300, 0.0009)],
        TRAP_FUND,
        "Cheap on valuation sub-scores, but earnings and revenue are shrinking and debt is high. "
        "Valuation alone does not support the buy.",
    ),
    Scenario(
        "pillars_in_conflict",
        "CONF",
        "Technology",
        [(240, 0.0010), (60, 0.0030)],
        GOOD_FUND,
        "Strong technicals against strongly negative news. The conflict must be resolved explicitly.",
        news=(
            "Regulator opens probe into company accounting",
            "Lawsuit alleges misleading investors",
            "Company beats estimates and raises guidance",
        ),
        provider_sentiment=-0.7,
    ),
    Scenario(
        "earnings_inside_hold",
        "EARN",
        "Health Care",
        [(300, 0.0012)],
        GOOD_FUND,
        "A sound buy whose next earnings report lands inside the expected holding period (after the "
        "scanner's 5-day exclusion). Event risk must be weighed.",
        earnings_in_days=8,
    ),
    Scenario(
        "correlated_with_holding",
        "TWIN",
        "Energy",
        [(300, 0.0012)],
        GOOD_FUND,
        "A sound name that moves almost exactly like an existing holding: adding it doubles one exposure.",
        holdings={"HELD": [(300, 0.0012)]},
        held_sector={"HELD": "Energy"},
    ),
    Scenario(
        "risk_off_high_beta",
        "BETA",
        "Technology",
        [(300, 0.0016)],
        GOOD_FUND,
        "A volatile name bought into a risk-off market with a high VIX: a stronger case is needed.",
        regime="risk_off",
        vix=31.0,
        wiggle=0.016,
        phase=0.0,
    ),
)
