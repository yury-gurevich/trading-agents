"""Deliberation stage observatory view.

Agent: orchestration
Role: render the declared LLM veto stage as a first-class acceptance artifact.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from orchestration.observatory import Check, StageView

if TYPE_CHECKING:
    from kernel import GraphStore, Node

DELIBERATED_EDGE = "DELIBERATED_BY"
EXECUTED_EDGE = "EXECUTED_BY"
ADVISORY_STATUSES = frozenset({"applied", "applied_failed_open", "proceeded_unvetoed"})


def deliberation(graph: GraphStore, node: Node) -> StageView:
    """Render the manager's debate artifact without re-running the LLM."""
    verdicts = node.props.get("verdicts")
    vetoed = node.props.get("vetoed_tickers")
    debates = node.props.get("debates")
    reviewed = len(verdicts) if isinstance(verdicts, Mapping) else 0
    vetoed_count = len(vetoed) if isinstance(vetoed, tuple | list) else 0
    real_debate_count = _count(node.props.get("real_debate_count"))
    failed_open_count = _count(node.props.get("failed_open_count"))
    failed_open_tickers = _tickers(node.props.get("failed_open_tickers"))
    failed_open_reason = str(node.props.get("failed_open_reason") or "")
    execution = _linked_execution(graph, node)
    posture = _prop(execution, "deliberation_posture")
    status = _prop(execution, "deliberation_status")
    coverage = _coverage(real_debate_count, reviewed)
    outputs: tuple[str, ...] = (
        f"reviewed={reviewed}  vetoed={vetoed_count}",
        f"real_debates={_display(real_debate_count)}  "
        f"failed_open={_display(failed_open_count)}",
    )
    if posture is not None or status is not None:
        outputs += (f"posture={posture or 'missing'}  status={status or 'missing'}",)
    if failed_open_tickers:
        outputs += (f"failed_open_tickers={', '.join(failed_open_tickers)}",)
    narrative = node.props.get("narrative")
    if narrative:
        outputs += (f"narrative {str(narrative)[:120]}",)
    observed: dict[str, object] = {
        "reviewed": reviewed,
        "debates": len(debates) if isinstance(debates, Mapping) else 0,
        "debate_coverage": coverage,
        "failed_open_count": failed_open_count,
        "deliberation_posture": posture,
        "advisory_attribution": _advisory_attribution(
            posture, status, failed_open_count, failed_open_reason
        ),
    }
    checks = [
        Check("reviewed", "required"),
        Check("debates", "required"),
        Check("deliberation_posture", "oneof", ("advisory", "binding")),
    ]
    if posture == "binding":
        checks.extend(
            (
                Check("debate_coverage", "floor", 1.0),
                Check("failed_open_count", "ceiling", 0.0),
            )
        )
    else:
        checks.append(Check("advisory_attribution", "oneof", ("ok",)))
    return StageView(
        "deliberation",
        "PMRun(pm)",
        observed,
        reached=True,
        checks=tuple(checks),
        outputs=outputs,
    )


def _count(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _coverage(real_debate_count: int | None, reviewed: int) -> float | None:
    if real_debate_count is None:
        return None
    if reviewed == 0:
        return 1.0
    return real_debate_count / reviewed


def _tickers(value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple | list):
        return ()
    return tuple(str(ticker) for ticker in value)


def _display(value: int | None) -> str:
    return "n/a" if value is None else str(value)


def _linked_execution(graph: GraphStore, node: Node) -> Node | None:
    pm_run = next(
        iter(graph.ancestors(node, max_depth=1, edge_types={DELIBERATED_EDGE})), None
    )
    if pm_run is None:
        return None
    return next(
        iter(graph.descendants(pm_run, max_depth=1, edge_types={EXECUTED_EDGE})), None
    )


def _prop(node: Node | None, name: str) -> str | None:
    if node is None:
        return None
    value = node.props.get(name)
    return value if isinstance(value, str) else None


def _advisory_attribution(
    posture: str | None,
    status: str | None,
    failed_open_count: int | None,
    failed_open_reason: str,
) -> str:
    if posture != "advisory":
        return "missing"
    if status not in ADVISORY_STATUSES:
        return "missing"
    if failed_open_count and not failed_open_reason:
        return "missing"
    return "ok"
