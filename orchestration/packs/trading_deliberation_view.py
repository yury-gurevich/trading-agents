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


def deliberation(graph: GraphStore, node: Node) -> StageView:
    """Render the manager's debate artifact without re-running the LLM."""
    del graph
    verdicts = node.props.get("verdicts")
    vetoed = node.props.get("vetoed_tickers")
    debates = node.props.get("debates")
    reviewed = len(verdicts) if isinstance(verdicts, Mapping) else 0
    vetoed_count = len(vetoed) if isinstance(vetoed, tuple | list) else 0
    outputs: tuple[str, ...] = (f"reviewed={reviewed}  vetoed={vetoed_count}",)
    narrative = node.props.get("narrative")
    if narrative:
        outputs += (f"narrative {str(narrative)[:120]}",)
    observed: dict[str, object] = {
        "reviewed": reviewed,
        "debates": len(debates) if isinstance(debates, Mapping) else 0,
    }
    checks = (Check("reviewed", "required"), Check("debates", "required"))
    return StageView(
        "deliberation",
        "PMRun(pm)",
        observed,
        reached=True,
        checks=checks,
        outputs=outputs,
    )
