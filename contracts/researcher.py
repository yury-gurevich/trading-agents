"""Researcher agent contract — evidence into bounded parameter-change proposals.

Agent: researcher
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: none.
"""

from __future__ import annotations

from contracts.common import Explanation, Provenance, _Frozen
from kernel.contract import AgentContract, Capability


# ── Inbound payloads ────────────────────────────────────────────────────────
class ResearchRequest(_Frozen):
    lookback_days: int = 90
    focus: str | None = None
    """Optional parameter family to study (sizing, stops, confidence floor, ...)."""


# ── Outbound payloads ───────────────────────────────────────────────────────
class ProposedChange(_Frozen):
    parameter: str
    current_value: float
    proposed_value: float
    evidence_window_days: int
    expected_effect: Explanation


class BacktestEvidence(_Frozen):
    sharpe: float
    ic_mean: float
    max_drawdown: float
    turnover: float
    n_days: int
    window_start: str
    window_end: str
    holdout_sharpe: float | None
    holdout_ic_mean: float | None
    slippage_bps: float
    engine: str = "walkforward-v1"


class ParameterChangeProposal(_Frozen):
    """Lands in the human-review queue. The researcher never applies it itself."""

    proposal_id: str
    changes: tuple[ProposedChange, ...]
    rationale: Explanation
    provenance: Provenance
    backtest: BacktestEvidence | None = None


CONTRACT = AgentContract(
    name="researcher",
    version="0.2.0",
    mission=(
        "Mine accumulated evidence for parameter and strategy improvements and "
        "propose bounded, measurable changes into the human-review queue — never "
        "apply them itself."
    ),
    consumes=(
        Capability(
            "propose",
            "Study evidence over a window and propose bounded parameter changes.",
            request=ResearchRequest,
            response=ParameterChangeProposal,
            mcp=True,
        ),
        Capability(
            "evidence",
            "Return the evidence behind a proposal for operator inspection.",
            request=ResearchRequest,
            response=Explanation,
            mcp=True,
        ),
    ),
    emits=("proposal_queued",),
    owns_graph=("Experiment", "ParamChange"),
    external_io=(),
    depends_on=("reporter", "supervisor"),
    mcp_tools=("propose", "evidence"),
    never=(
        "apply a parameter change (proposes into the review queue only)",
        "bypass the evidence-window requirement",
        "propose a forbidden parameter combination",
    ),
)
