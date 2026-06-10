"""Analyst agent contract — candidates into scored recommendations.

Agent: analyst
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: none.
"""

from __future__ import annotations

from pydantic import Field

from contracts.common import Action, Explanation, Provenance, Ticker, _Frozen
from contracts.scanner import CandidateSet
from kernel.contract import AgentContract, Capability


# ── Outbound payloads ───────────────────────────────────────────────────────
class Recommendation(_Frozen):
    ticker: Ticker
    action: Action
    confidence: float = Field(ge=0.0, le=1.0)
    """0..1. Must clear the regime's base_min_confidence to be actionable."""
    technical_score: float
    sentiment_score: float | None = None
    fundamental_score: float | None = None
    suggested_stop_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    suggested_target_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    rationale: Explanation


class Rejection(_Frozen):
    ticker: Ticker
    reason: str


class RecommendationSet(_Frozen):
    run_id: str
    recommendations: tuple[Recommendation, ...]
    rejections: tuple[Rejection, ...]
    explanation: Explanation
    """Run-level: why these, or why none today (explainable silence)."""
    provenance: Provenance


CONTRACT = AgentContract(
    name="analyst",
    version="0.1.0",
    mission=(
        "Turn candidates into scored, evidence-backed trade recommendations with a "
        "confidence and a rationale — or explain clearly why none qualify."
    ),
    consumes=(
        Capability(
            "analyze",
            "Score candidates against the current regime into recommendations.",
            request=CandidateSet,
            response=RecommendationSet,
            mcp=True,
        ),
        Capability(
            "explain_recommendation",
            "Explain how a recommendation's confidence and rationale were derived.",
            request=CandidateSet,
            response=Explanation,
            mcp=True,
        ),
    ),
    emits=("analysis_completed",),
    owns_graph=("AnalystRun", "Recommendation"),
    external_io=(),
    depends_on=("scanner", "provider"),
    mcp_tools=("analyze", "explain_recommendation"),
    never=(
        "size positions or compute order quantities",
        "approve, reject for portfolio reasons, or submit orders",
        "call a market-data API directly (request it from provider)",
        "import portfolio_manager sizing (the old leak this rebuild removes)",
    ),
)
