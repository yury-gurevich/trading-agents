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
    real_debate_count = _count(node.props.get("real_debate_count"))
    failed_open_count = _count(node.props.get("failed_open_count"))
    failed_open_tickers = _tickers(node.props.get("failed_open_tickers"))
    coverage = _coverage(real_debate_count, reviewed)
    outputs: tuple[str, ...] = (
        f"reviewed={reviewed}  vetoed={vetoed_count}",
        f"real_debates={_display(real_debate_count)}  "
        f"failed_open={_display(failed_open_count)}",
    )
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
    }
    checks = (
        Check("reviewed", "required"),
        Check("debates", "required"),
        Check("debate_coverage", "floor", 1.0),
        Check("failed_open_count", "ceiling", 0.0),
    )
    return StageView(
        "deliberation",
        "PMRun(pm)",
        observed,
        reached=True,
        checks=checks,
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
