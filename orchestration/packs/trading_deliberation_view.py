"""Deliberation stage observatory view.

Agent: orchestration
Role: render the declared LLM veto stage as a first-class acceptance artifact.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from contracts.portfolio_manager import OrderIntentSet
from orchestration.observatory import Check, StageView

if TYPE_CHECKING:
    from kernel import GraphStore, Node

DELIBERATED_EDGE = "DELIBERATED_BY"
EXECUTED_EDGE = "EXECUTED_BY"
ADVISORY_STATUSES = frozenset({"applied", "applied_failed_open", "proceeded_unvetoed"})
NOT_REQUIRED_STATUS = "not_required"
BUY_VETO_MISSING = "buy_veto_missing"


def deliberation(graph: GraphStore, node: Node) -> StageView:
    """Render the manager's debate artifact without re-running the LLM."""
    verdicts = node.props.get("verdicts")
    vetoed = node.props.get("vetoed_tickers")
    debates = node.props.get("debates")
    reviewed = len(verdicts) if isinstance(verdicts, Mapping) else 0
    vetoed_count = len(vetoed) if isinstance(vetoed, tuple | list) else 0
    real_debate_count = _count(node.props.get("real_debate_count"))
    failed_open_count = _count(node.props.get("failed_open_count"))
    orphaned_reply_count = _count(node.props.get("orphaned_reply_count"))
    failed_open_tickers = _tickers(node.props.get("failed_open_tickers"))
    failed_open_reason = str(node.props.get("failed_open_reason") or "")
    pm_run, execution = _linked_pm_and_execution(graph, node)
    posture = _prop(execution, "deliberation_posture")
    status = _prop(execution, "deliberation_status")
    approved_buy_count = _approved_buy_count(pm_run)
    coverage = _coverage(real_debate_count, reviewed)
    outputs: tuple[str, ...] = (
        f"reviewed={reviewed}  vetoed={vetoed_count}",
        f"real_debates={_display(real_debate_count)}  "
        f"failed_open={_display(failed_open_count)}  "
        f"orphaned_replies={_display(orphaned_reply_count)}",
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
        "orphaned_reply_count": orphaned_reply_count,
        "deliberation_posture": posture,
        "advisory_attribution": _advisory_attribution(
            posture,
            status,
            failed_open_count,
            failed_open_reason,
            approved_buy_count,
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


def _linked_pm_and_execution(
    graph: GraphStore, node: Node
) -> tuple[Node | None, Node | None]:
    pm_run = next(
        iter(graph.ancestors(node, max_depth=1, edge_types={DELIBERATED_EDGE})), None
    )
    if pm_run is None:
        return None, None
    execution = next(
        iter(graph.descendants(pm_run, max_depth=1, edge_types={EXECUTED_EDGE})), None
    )
    return pm_run, execution


def _approved_buy_count(node: Node | None) -> int | None:
    if node is None:
        return None
    raw = node.props.get("order_intent_set")
    if raw is None:
        return None
    try:
        order_set = OrderIntentSet.model_validate(raw)
    except ValueError:
        return None
    return sum(1 for intent in order_set.approved if intent.action == "buy")


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
    approved_buy_count: int | None,
) -> str:
    if posture != "advisory":
        return "missing"
    if status == NOT_REQUIRED_STATUS:
        if approved_buy_count == 0:
            return "ok"
        if approved_buy_count is not None:
            return BUY_VETO_MISSING
        return "missing"
    if status not in ADVISORY_STATUSES:
        return "missing"
    if failed_open_count and not failed_open_reason:
        return "missing"
    return "ok"
