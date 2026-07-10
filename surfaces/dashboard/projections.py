"""Dashboard run projections — runs, verdict, and per-stage logical views.

Agent: surfaces
Role: project one run's observatory + acceptance facts into JSON-ready dicts.
      Verdicts are computed by the orchestration pack (one source of truth,
      the same numbers `scripts/accept.py` prints) — never re-derived here.
External I/O: none (reads the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.provider import RUN_REQUEST_LABEL
from orchestration.batch_trace import walk_chain
from orchestration.observatory import breaches
from orchestration.packs.trading_acceptance import accept_run
from orchestration.packs.trading_observatory import observe_run

if TYPE_CHECKING:
    from kernel import GraphStore, Node
    from orchestration.observatory import Breach, StageView

# The two acceptance floors that a legitimate no-trade day trips (see STATE
# 2026-07-10 watch outcome): every candidate rejected below the regime
# confidence floor leaves nothing to score or evaluate.
_NO_TRADE_BREACHES = frozenset({("analyst", "scored"), ("pm", "evaluated")})

_NO_TRADE_ANNOTATION = (
    "Every agent did its job: all {rejected} candidates were rejected below the "
    "regime confidence floor, so there was nothing to score or evaluate — a "
    "legitimate no-trade day. The gate requires at least one scored "
    "recommendation, so it reads FAIL (gate-policy finding, not a runtime fault)."
)


def run_request_node(graph: GraphStore, run_id: str) -> Node | None:
    """Return the RunRequest node for a run id, if the run exists."""
    return graph.get_node(RUN_REQUEST_LABEL, f"run-request:{run_id}")


def list_runs(graph: GraphStore) -> list[dict[str, object]]:
    """All known runs, newest first — the run-selector feed."""
    rows: list[dict[str, object]] = [
        {
            "run_id": str(node.props.get("run_id", "")),
            "requested_at": str(node.props.get("requested_at", "")),
        }
        for node in graph.list_nodes(RUN_REQUEST_LABEL)
    ]
    rows.sort(key=lambda r: (str(r["requested_at"]), str(r["run_id"])), reverse=True)
    return rows


def run_verdict(graph: GraphStore, run_id: str) -> dict[str, object]:
    """Acceptance PASS/FAIL + breaches + the no-trade-day annotation."""
    result = accept_run(graph, run_id)
    rejected = _rejection_count(graph, run_id)
    no_trade = _is_no_trade_day(result.passed, result.breaches, rejected)
    return {
        "run_id": run_id,
        "passed": result.passed,
        "breaches": [
            {
                "stage": b.stage,
                "key": b.key,
                "detail": b.detail,
                "severity": b.severity,
            }
            for b in result.breaches
        ],
        "no_trade_day": no_trade,
        "annotation": (
            _NO_TRADE_ANNOTATION.format(rejected=rejected) if no_trade else None
        ),
    }


def run_stages(graph: GraphStore, run_id: str) -> list[dict[str, object]]:
    """Per-stage logical views: observed values, outputs, and check outcomes."""
    return [_stage_dict(view) for view in observe_run(graph, run_id)]


def _stage_dict(view: StageView) -> dict[str, object]:
    failed = {b.key: b for b in breaches(view)}
    checks = [
        {
            "key": check.key,
            "kind": check.kind,
            "severity": check.severity,
            "ok": check.key not in failed,
            "detail": failed[check.key].detail if check.key in failed else None,
        }
        for check in view.checks
    ]
    return {
        "name": view.name,
        "trigger": view.trigger,
        "reached": view.reached,
        "observed": dict(view.observed),
        "outputs": list(view.outputs),
        "checks": checks,
    }


def _rejection_count(graph: GraphStore, run_id: str) -> int:
    """How many candidates the analyst explicitly rejected on this run."""
    from collections.abc import Mapping

    node = walk_chain(graph, run_id).get("AnalystRun")
    rec_set = node.props.get("recommendation_set") if node else None
    if not isinstance(rec_set, Mapping):
        return 0
    rejections = rec_set.get("rejections")
    return len(rejections) if isinstance(rejections, (list, tuple)) else 0


def _is_no_trade_day(
    passed: bool, all_breaches: tuple[Breach, ...], rejected: int
) -> bool:
    """FAIL caused only by the scored/evaluated floors, with real rejections."""
    if passed or rejected == 0:
        return False
    blocking = {(b.stage, b.key) for b in all_breaches if b.severity == "fail"}
    return bool(blocking) and blocking <= _NO_TRADE_BREACHES
