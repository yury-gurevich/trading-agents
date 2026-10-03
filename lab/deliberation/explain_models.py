"""Iteration 1, step 2: what a deliberator must produce to prove it understands the data.

(a) one Interpretation per number: what kind of financial indicator it is, its unit, what it means here,
    which way it points for this buy, and, for a raw indicator our code scores, the sub-score it maps to;
(b) the numbers in combination: how the system's aggregates derive from the parts (Derivation), what each
    pillar says (PillarView), which numbers confirm, contradict or qualify one another (Interaction), and
    what situation the whole picture describes.
Typed throughout, so code can grade it against what the fleet's code computes.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .outputs import Scale

Concept = Literal[
    "momentum_oscillator",
    "trend",
    "volatility",
    "mean_reversion",
    "volume_flow",
    "relative_strength",
    "valuation",
    "profitability",
    "growth",
    "balance_sheet",
    "sentiment",
    "composite_score",
    "risk_management",
    "market_regime",
    "event_risk",
    "systematic_risk",
    "liquidity",
    "concentration",
    "position_sizing",
    "forecast",
    "pattern",
    "price_level",
    "data_quality",
    "bookkeeping",
]

DERIVATIONS = Literal[
    "technical_score",
    "fundamental_score",
    "composite_score",
    "confidence_score",
    "applied_stop_pct",
    "reward_risk_ratio",
]
PILLARS = Literal["technical", "relative_strength", "fundamental", "sentiment", "risk", "regime", "portfolio"]


class Interpretation(BaseModel):
    metric: str = Field(description="the exact key as written in the packet")
    value: str = Field(description="the value copied exactly as the packet writes it")
    scale: Scale = Field(description="what kind of number this is, per the dictionary")
    concept: Concept = Field(description="the family of financial indicator this number belongs to")
    meaning_here: str = Field(description="one clause: what this value says about THIS stock in THIS system")
    direction: Literal["favourable", "unfavourable", "neutral"] = Field(
        description="how this value bears on buying this stock now"
    )
    implied_sub_score: float | None = Field(
        description="for a RAW indicator that our code scores (rsi, atr_pct, sma_distance_pct, a vendor "
        "fundamental such as peBasicExclExtraTTM, ...): the 0-100 sub-score our scoring bands assign to this "
        "value; null for anything else"
    )


class Derivation(BaseModel):
    name: DERIVATIONS = Field(description="which aggregate you are reproducing")
    inputs: list[str] = Field(description="the packet keys it is computed from")
    rule: str = Field(description="the rule, in words or a formula")
    computed: float = Field(description="your result, computed from the packet's values")


class PillarView(BaseModel):
    pillar: PILLARS
    verdict: Literal["favourable", "unfavourable", "mixed", "absent"]
    because: list[str] = Field(description="the keys that decide this verdict")


class Interaction(BaseModel):
    keys_a: list[str] = Field(description="one group of keys")
    keys_b: list[str] = Field(description="the group they interact with")
    relation: Literal["confirms", "contradicts", "qualifies"]
    meaning: str = Field(description="what the two groups mean TOGETHER for this stock")


class Explanation(BaseModel):
    interpretations: list[Interpretation] = Field(
        description="one per number you must read (house rule H12), each read on its own, except contrarian oscillators, which are read with the trend (house rule H7)"
    )
    derivations: list[Derivation] = Field(
        description="reproduce EACH named aggregate from its parts using the packet's own numbers"
    )
    pillars: list[PillarView] = Field(description="one verdict per pillar")
    interactions: list[Interaction] = Field(
        description="every place where numbers confirm, contradict or qualify each other"
    )
    situation: str = Field(
        description="in two or three sentences: what market situation this whole picture describes"
    )
    overall: Literal["favourable", "unfavourable", "mixed"]
