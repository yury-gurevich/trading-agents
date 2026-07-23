"""Execution stage view — what the broker actually did with the run's orders (pack).

Agent: orchestration
Role: count a run's fills by their real broker outcome and build the execution
      StageView from them. Submitting an order is not trading; the gate must read
      the outcome, not the intent.
External I/O: none (reads the injected GraphStore).

DL-59: acceptance scored stage completion, so a run whose every order was rejected at
the open still read PASS. `submitted` is an intent count and can never show that. The
distinction that matters is three-way — filled, resolved-unfilled, and not-yet-known —
because an after-hours run legitimately has no outcome yet, and calling that PASS is
the same sin as calling a rejected run PASS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from orchestration.observatory import Check, StageView

if TYPE_CHECKING:
    from kernel import GraphStore, Node

_FILLED = frozenset({"filled", "partial"})
_RESOLVED_UNFILLED = frozenset({"rejected", "canceled", "cancelled", "expired"})
_PM_EDGE = "EXECUTED_BY"
_ORDER_EDGE = "EMITTED_BY"


@dataclass(frozen=True)
class FillOutcomes:
    """One run's orders, split by what the broker did with them."""

    filled: int = 0
    unfilled: int = 0
    unresolved: int = 0
    statuses: tuple[str, ...] = ()

    @property
    def submitted(self) -> int:
        """Orders this run put to the broker."""
        return self.filled + self.unfilled + self.unresolved


def fill_outcomes(graph: GraphStore, execution_run: Node) -> FillOutcomes:
    """Classify every Fill reachable from one ExecutionRun by its broker outcome."""
    filled = unfilled = unresolved = 0
    seen: list[str] = []
    for fill in _run_fills(graph, execution_run):
        status = _effective_status(fill)
        seen.append(status)
        if status in _FILLED:
            filled += 1
        elif status in _RESOLVED_UNFILLED:
            unfilled += 1
        else:
            unresolved += 1
    return FillOutcomes(filled, unfilled, unresolved, tuple(sorted(set(seen))))


def execution_view(graph: GraphStore, node: Node) -> StageView:
    """Build the execution StageView, including the broker outcome of its orders."""
    submitted = node.props.get("submitted")
    outcomes = fill_outcomes(graph, node)
    outputs = (
        f"submitted={submitted}  rejected={node.props.get('rejected')}",
        f"outcome   filled={outcomes.filled}  unfilled={outcomes.unfilled}"
        f"  unresolved={outcomes.unresolved}"
        + (f"  [{', '.join(outcomes.statuses)}]" if outcomes.statuses else ""),
    )
    observed: dict[str, object] = {
        "submitted": submitted,
        "orders": outcomes.submitted,
        "filled": outcomes.filled,
        "unfilled": outcomes.unfilled,
        "statuses": ", ".join(outcomes.statuses),
    }
    checks = (Check("submitted", "required"),)
    return StageView(
        "execution",
        "OrderIntentSet(pm)",
        observed,
        reached=True,
        checks=checks,
        outputs=outputs,
    )


def _run_fills(graph: GraphStore, execution_run: Node) -> tuple[Node, ...]:
    """Return the Fill nodes for the PM run this ExecutionRun executed."""
    pm_run = next(
        iter(graph.ancestors(execution_run, max_depth=1, edge_types={_PM_EDGE})), None
    )
    if pm_run is None:
        return ()
    source = str(pm_run.props.get("linked_from_key", pm_run.key))
    fills: list[Node] = []
    for order in graph.ancestors(pm_run, max_depth=1, edge_types={_ORDER_EDGE}):
        ticker = order.props.get("ticker")
        action = order.props.get("action")
        fill = graph.get_node("Fill", f"{source}:{ticker}:{action}")
        if fill is not None:
            fills.append(fill)
    return tuple(fills)


def _effective_status(fill: Node) -> str:
    """Broker evidence wins over the status recorded at submit time."""
    status = fill.props.get("broker_status") or fill.props.get("status")
    return str(status or "unknown")
