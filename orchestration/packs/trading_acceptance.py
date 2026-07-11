"""Layer-3 acceptance gate for the trading pipeline (pack, not substrate).

Agent: orchestration
Role: turn the observatory into a PASS/NO_TRADE/FAIL verdict on a run — every per-stage
      invariant AND the cross-stage CONSERVATION boundaries: no agent fabricates or
      exceeds its mandate, so each stage's output count is bounded by its input. This
      is the trading content of the Layer-3 "each agent's job + boundaries asserted"
      acceptance row. The verdict mechanism is substrate (observatory.accept); the
      conservation invariants are the trading pack (ADR-0012).
External I/O: none (reads the injected GraphStore via observe_run).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from orchestration.batch_trace import walk_chain
from orchestration.observatory import Breach, CrossCheck, StageView, accept
from orchestration.packs.trading_observatory import observe_run

if TYPE_CHECKING:
    from kernel import GraphStore

AcceptanceVerdict = Literal["PASS", "NO_TRADE", "FAIL"]


@dataclass(frozen=True)
class TradingAcceptanceResult:
    """Pack verdict; NO_TRADE is pass-equivalent without hiding its label."""

    verdict: AcceptanceVerdict
    breaches: tuple[Breach, ...]

    @property
    def passed(self) -> bool:
        """Whether the CLI should exit successfully."""
        return self.verdict != "FAIL"


def _conserves(child: str, child_key: str, parent: str, parent_key: str) -> CrossCheck:
    """No fabrication: a stage's output count cannot exceed its input count."""

    def check(observed: dict[str, dict[str, object]]) -> Breach | None:
        out = observed.get(child, {}).get(child_key)
        src = observed.get(parent, {}).get(parent_key)
        if not isinstance(out, int) or not isinstance(src, int):
            return None
        if out > src:
            return Breach(
                child, child_key, f"{out} > {parent}.{parent_key}={src} (fabricated)"
            )
        return None

    return check


# Each agent's output is bounded by its input — the boundaries asserted (EXEC-NEV-01:
# "never decides what to trade"; the scanner/analyst/PM cannot invent names).
_CONSERVATION: tuple[CrossCheck, ...] = (
    _conserves("scanner", "survived", "provider", "returned"),
    _conserves("analyst", "scored", "scanner", "survived"),
    _conserves("pm", "approved", "analyst", "scored"),
    _conserves("execution", "submitted", "pm", "approved"),
)

_NO_TRADE_BREACHES = frozenset({("analyst", "scored"), ("pm", "evaluated")})
_REJECTION_EVIDENCE = re.compile(
    r"confidence (?P<confidence>\d+(?:\.\d+)?) below regime floor "
    r"(?P<floor>\d+(?:\.\d+)?)"
)


def accept_run(graph: GraphStore, run_id: str) -> TradingAcceptanceResult:
    """The Layer-3 acceptance verdict over one persisted run."""
    stages = observe_run(graph, run_id)
    return evaluate_stages(stages, _has_rejection_evidence(graph, run_id))


def evaluate_stages(
    stages: tuple[StageView, ...], rejection_evidence: bool
) -> TradingAcceptanceResult:
    """Classify observed stages; exposed for the acceptance truth table."""
    result = accept(stages, _CONSERVATION)
    if result.passed:
        verdict: AcceptanceVerdict = "PASS"
    elif _is_no_trade(stages, result.breaches, rejection_evidence):
        verdict = "NO_TRADE"
    else:
        verdict = "FAIL"
    return TradingAcceptanceResult(verdict=verdict, breaches=result.breaches)


def _is_no_trade(
    stages: tuple[StageView, ...],
    all_breaches: tuple[Breach, ...],
    rejection_evidence: bool,
) -> bool:
    """Require a complete, zero-scored run explained by confidence evidence."""
    complete = bool(stages) and all(stage.reached for stage in stages)
    if not rejection_evidence or not complete:
        return False
    analyst = next((stage for stage in stages if stage.name == "analyst"), None)
    if analyst is None or analyst.observed.get("scored") != 0:
        return False
    blocking = {
        (breach.stage, breach.key)
        for breach in all_breaches
        if breach.severity == "fail"
    }
    return bool(blocking) and blocking <= _NO_TRADE_BREACHES


def _has_rejection_evidence(graph: GraphStore, run_id: str) -> bool:
    """Every analyst rejection states confidence and the regime floor it missed."""
    analyst = walk_chain(graph, run_id).get("AnalystRun")
    payload = analyst.props.get("recommendation_set") if analyst else None
    rejections = payload.get("rejections") if isinstance(payload, Mapping) else None
    return (
        bool(rejections)
        and isinstance(rejections, (list, tuple))
        and all(_explains_floor(rejection) for rejection in rejections)
    )


def _explains_floor(rejection: object) -> bool:
    """Validate one persisted low-confidence rejection explanation."""
    if not isinstance(rejection, Mapping):
        return False
    reason = rejection.get("reason")
    match = _REJECTION_EVIDENCE.fullmatch(reason) if isinstance(reason, str) else None
    if match is None:
        return False
    return float(match["confidence"]) < float(match["floor"])


def render_acceptance(result: TradingAcceptanceResult) -> str:
    """Human-readable verdict — one line per genuine failure breach."""
    if result.verdict == "PASS":
        return "ACCEPTANCE  PASS - every stage did its job within its boundaries"
    if result.verdict == "NO_TRADE":
        return (
            "ACCEPTANCE  NO_TRADE - completed; no candidates cleared "
            "the confidence floor"
        )
    lines = [f"  FAIL  {b.stage}.{b.key}: {b.detail}" for b in result.breaches]
    return "ACCEPTANCE  FAIL\n" + "\n".join(lines)
