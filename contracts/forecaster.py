"""Forecaster agent contract — advisory shadow-ML signals only.

Agent: forecaster
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: none.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from contracts.common import Provenance, _Frozen
from kernel.contract import AgentContract, Capability


# ── Inbound payloads ────────────────────────────────────────────────────────
class ForecastRequest(_Frozen):
    subject_kind: Literal["recommendation", "position"]
    subject_ref: str
    features: dict[str, float]
    history_ref: str | None = None
    """forecast_barrier only: the provider's BarrierHistory key to read bars from."""


class ScorecardRequest(_Frozen):
    model_id: str


class SentimentScorecardRequest(_Frozen):
    model_id: str
    forward_returns: dict[str, float]
    """Realized forward returns keyed by '{analyst_run_id}:{ticker}'.

    Injected (offline harness): forward returns are never a runtime dependency, so
    the caller supplies the realized returns for the observations it wants scored.
    """


class ReturnScorecardRequest(_Frozen):
    model_id: str
    forward_returns: dict[str, float]
    """Realized forward returns keyed by subject_ref (ticker); injected offline."""


class BarrierScorecardRequest(_Frozen):
    model_id: str
    """The barrier model whose settled claims to score (e.g. ``barrier-garch-v1``)."""


# ── Outbound payloads ───────────────────────────────────────────────────────
class ShadowPrediction(_Frozen):
    model_id: str
    subject_ref: str
    value: float
    confidence: float
    shadow: bool = True
    """Always True until a scorecard earns promotion. Never gates a decision."""
    provenance: Provenance


class Scorecard(_Frozen):
    model_id: str
    metrics: dict[str, float]
    sample_size: int
    fresh_as_of: datetime
    promotion_eligible: bool = False


CONTRACT = AgentContract(
    name="forecaster",
    version="0.7.0",
    mission=(
        "Provide advisory ML forecasts (exit timing, news impact, ...) as clearly "
        "labelled shadow signals that never gate a decision until scorecards prove "
        "they deserve promotion."
    ),
    consumes=(
        Capability(
            "forecast",
            "Produce an advisory shadow prediction for a recommendation or position.",
            request=ForecastRequest,
            response=ShadowPrediction,
            mcp=True,
        ),
        Capability(
            "scorecard",
            "Report a shadow model's measured accuracy and promotion eligibility.",
            request=ScorecardRequest,
            response=Scorecard,
            mcp=True,
        ),
        Capability(
            "sentiment_scorecard",
            "Compare the lexicon/provider/finbert sentiment scorers against "
            "injected forward returns; advisory, never promotion-eligible.",
            request=SentimentScorecardRequest,
            response=Scorecard,
        ),
        Capability(
            "forecast_return",
            "Produce an advisory shadow price/return prediction for a subject.",
            request=ForecastRequest,
            response=ShadowPrediction,
        ),
        Capability(
            "forecast_factor",
            "Produce an advisory shadow prediction for an operator-enabled factor.",
            request=ForecastRequest,
            response=ShadowPrediction,
        ),
        Capability(
            "forecast_barrier",
            "State P(stop first), P(target first), P(neither) within 10 sessions "
            "for a buy's stop and target (features stop_pct, target_pct) and record "
            "them as an advisory BarrierForecast claim; value = P(target first).",
            request=ForecastRequest,
            response=ShadowPrediction,
        ),
        Capability(
            "return_scorecard",
            "Compare the LightGBM return model's shadow predictions against injected "
            "forward returns; advisory, never promotion-eligible.",
            request=ReturnScorecardRequest,
            response=Scorecard,
        ),
        Capability(
            "barrier_scorecard",
            "Report whether one barrier model's claims come true: settled, void and "
            "open counts, Brier and skill over EXP-018's fixed climatology with a "
            "date-bootstrap interval; advisory, never promotion-eligible.",
            request=BarrierScorecardRequest,
            response=Scorecard,
        ),
    ),
    emits=("scorecard_refreshed",),
    owns_graph=(
        "ShadowPrediction",
        "Model",
        "ForecasterRun",
        "BarrierForecast",
        "BarrierSettlement",
        "BarrierSettlementPass",
    ),
    external_io=(),
    depends_on=("provider",),
    mcp_tools=("forecast", "scorecard"),
    never=(
        "emit a binding (non-shadow) signal",
        "gate or veto a recommendation, sizing, or exit",
        "self-promote a model without an operator-facing scorecard",
    ),
)
