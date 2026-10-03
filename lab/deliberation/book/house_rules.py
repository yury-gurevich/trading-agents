"""Book Part III, house rules: how this system works and what the deliberators must not assume.

Each rule cites where it is decided. `falsifiers` are regexes for statements that contradict the
rule; DEC-FORM-06 flags any output text that matches one (the S245 class of error).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: str
    text: str
    cites: str
    falsifiers: tuple[str, ...] = ()


RULES: tuple[Rule, ...] = (
    Rule(
        "H1",
        "Only `overturn` blocks the order. `revise` is a recorded finding: the order still trades unchanged. "
        "`uphold` lets it trade.",
        "ADR-0029",
        (r"\brevise\b[^.]{0,40}\b(blocks?|cancels?|stops?|prevents?)\b",),
    ),
    Rule(
        "H2",
        "Data staleness is counted in NYSE trading sessions, never calendar days.",
        "DL-10; provider settings",
        (r"calendar[- ]days?[^.]{0,60}stale", r"stale[^.]{0,60}calendar[- ]days?"),
    ),
    Rule(
        "H3",
        "The scanner already drops any name whose next earnings report is within 5 calendar days. Earnings "
        "later than that can still fall inside the holding period.",
        "scanner earnings_exclusion_days=5",
    ),
    Rule(
        "H4",
        "A decision must rest on market evidence (technical, fundamental, relative-strength, sentiment, "
        "volatility or regime readings) used as an expert would. Process facts (a gate passed, sizing, an "
        "attestation) may support a case but are never its basis.",
        "operator policy, DL-264 decision 2",
    ),
    Rule(
        "H5",
        "A PM gate reading NOT-EVALUATED did not look (deployment is below its floor). It is not a pass.",
        "portfolio_manager deployment_floor",
        (r"NOT-EVALUATED[^.]{0,40}\bpass(ed|es)?\b",),
    ),
    Rule(
        "H6",
        "The reward_risk gate is disclosure-only at threshold 0: a target smaller than the stop still PASSES. "
        "Judge the ratio yourself.",
        "PM min_reward_risk_ratio=0.0; comparison=DISCLOSURE_ONLY",
    ),
    Rule(
        "H7",
        "Contrarian sub-scores (RSI, RSI-2, stochastic, Williams %R, Bollinger, NW deviation) score oversold "
        "as bullish. Read them together with the trend readings (SMA-200 distance, EMA spread, MACD, golden "
        "cross, relative strength); oversold in a downtrend is not support.",
        "analyst technical_rules",
    ),
    Rule(
        "H8",
        "The packet carries no holdings, open positions or sibling orders beyond what the PM gate lines state. "
        "Do not infer them.",
        "agents/deliberator/context.py _PORTFOLIO_BATCH_BOUNDARY",
    ),
    Rule(
        "H9",
        "Today the only exit that fires is the protective stop. Nothing sells at the target or after "
        "base_max_holding_days.",
        "work-queue 92 / DL-240",
    ),
    Rule(
        "H10",
        "Sentiment 'n/a' means no headline carried a lexicon word: no signal, not neutral.",
        "analyst sentiment_rules",
    ),
    Rule(
        "H11",
        "`pe`, `pb`, `roe`, `net_margin`, `current_ratio`, `debt_equity`, `eps_growth`, `revenue_growth` in "
        "quant_metrics are 0-100 SUB-SCORES. The raw ratios appear under vendor names in the Fundamentals line.",
        "analyst fundamental_rules",
    ),
    Rule(
        "H12",
        "Every number in the packet is presented to you and must be read: copied exactly, its scale named, what it "
        "means here, whether it is favourable for this buy, and how much it weighs. The judge reads EVERY number. "
        "The pro and con read every number of evidence and may skip bookkeeping (the dictionary marks each "
        "entry). A number that does not matter is still read, with weight low and the reason.",
        "operator rule 2026-10-03; tiers decided in DL-264 amendment 8",
    ),
    Rule(
        "H13",
        "A number marked UNPROVEN in the dictionary (a model output whose skill is not yet shown live, such as the "
        "barrier forecast) is read and weighed like any other, but it may never carry a decision on its own: at "
        "least one PROVEN market reading must. When its skill is proven the mark is removed and nothing else "
        "changes.",
        "DL-264 amendment 8 (replaces hiding the forecast until proven, work-queue 99)",
    ),
)


def render() -> str:
    return "\n".join(["# House rules (book Part III)", ""] + [f"- {r.id}: {r.text}" for r in RULES])
