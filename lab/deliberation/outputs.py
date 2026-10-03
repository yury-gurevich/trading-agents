"""The typed outputs the three seats must produce. Typed so that code can check understanding."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Scale = Literal[
    "sub_score_0_100",
    "fraction_0_1",
    "fraction",
    "percent",
    "percentage_points",
    "ratio",
    "raw_indicator",
    "count",
    "usd",
    "shares",
    "flag_0_1",
    "days",
    "position_0_1",
    "index_points",
    "enum",
    "weight_sum",
    "compound",
    "provider_scale_undeclared",
]


class Reading(BaseModel):
    metric: str = Field(
        description="the exact key as written in the packet, e.g. rsi_score (no prose, no block name)"
    )
    value: str = Field(description="the value copied exactly as the packet writes it, no rounding")
    scale: Scale = Field(description="what kind of number this is, per the dictionary")
    meaning_here: str = Field(description="one clause: what this value means for THIS stock in THIS system")
    direction: Literal["favourable", "unfavourable", "neutral"] = Field(
        description="how this value bears on buying this stock now"
    )
    weight: Literal["high", "medium", "low"] = Field(description="how much it matters to your position")


class Brief(BaseModel):
    readings: list[Reading] = Field(
        description="EVERY number in the packet, one reading each, read before "
        "arguing (house rule H12); a number that does not matter still gets weight low"
    )
    gaps: list[str] = Field(description="evidence that is missing and would change the case")
    case: str = Field(description="your argument, built only on the readings above")


class Ruling(BaseModel):
    own_readings: list[Reading] = Field(
        description="your own reading of EVERY number in the packet, one each, before weighing the cases "
        "(house rule H12)"
    )
    decisive: list[str] = Field(description="the metric keys (from own_readings) the ruling rests on")
    market_conditions: str = Field(
        description="regime, VIX and its date, sector, earnings horizon as they bear here"
    )
    accepted: list[str] = Field(description="claims from either case you accept, each with its reason")
    rejected: list[str] = Field(
        description="claims from either case you reject, each with its reason; "
        "always answer the losing side's strongest claim"
    )
    ruling: Literal["uphold", "revise", "overturn"]
    rationale: str = Field(description="why THIS combination of data and conditions leads to THIS ruling")
