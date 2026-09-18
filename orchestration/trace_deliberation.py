"""Deliberation trace rendering helpers.

Agent: orchestration
Role: format recorded DeliberationRun and ExecutionRun facts for operator traces.
External I/O: none.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from typing import TYPE_CHECKING

from contracts.portfolio_manager import OrderIntentSet

if TYPE_CHECKING:
    from kernel import Node


def format_deliberation_trace(
    pm_node: Node | None, deliberation_node: Node, execution_node: Node | None
) -> tuple[str, ...]:
    """Return trace lines for a recorded deliberation stage."""
    verdicts = deliberation_node.props.get("verdicts")
    vetoed_raw = deliberation_node.props.get("vetoed_tickers")
    reviewed = str(len(verdicts)) if isinstance(verdicts, Mapping) else "?"
    revised = _revised_count(verdicts)
    vetoed = str(len(vetoed_raw)) if isinstance(vetoed_raw, tuple | list) else "?"
    status = _str_prop(execution_node, "deliberation_status") or "?"
    lines: tuple[str, ...] = (
        f"reviewed={reviewed}  revised={revised}  vetoed={vetoed}  status={status}",
    )
    vetoed_tickers = _tickers(vetoed_raw)
    if vetoed_tickers:
        lines += (f"tickers={','.join(vetoed_tickers)}",)
    withheld = _withheld_count(pm_node, vetoed_tickers, execution_node)
    if withheld is not None:
        lines += (f"withheld={withheld} by deliberation veto",)
    return lines


def _tickers(value: object) -> tuple[str, ...]:
    if not isinstance(value, tuple | list):
        return ()
    return tuple(str(ticker) for ticker in value)


def _revised_count(value: object) -> str:
    if not isinstance(value, Mapping):
        return "?"
    return str(sum(1 for verdict in value.values() if str(verdict).lower() == "revise"))


def _withheld_count(
    pm_node: Node | None, vetoed_tickers: tuple[str, ...], execution_node: Node | None
) -> int | None:
    if not vetoed_tickers or execution_node is None:
        return None
    submitted = execution_node.props.get("submitted")
    if not isinstance(submitted, int):
        return None
    approved_buys = _approved_buy_tickers(pm_node)
    if approved_buys is None:
        return None
    gap = len(approved_buys) - submitted
    if gap <= 0 or gap != len(vetoed_tickers):
        return None
    if Counter(vetoed_tickers) - Counter(approved_buys):
        return None
    return gap


def _approved_buy_tickers(pm_node: Node | None) -> tuple[str, ...] | None:
    if pm_node is None:
        return None
    raw = pm_node.props.get("order_intent_set")
    if raw is None:
        return None
    try:
        order_set = OrderIntentSet.model_validate(raw)
    except ValueError:
        return None
    return tuple(
        intent.ticker for intent in order_set.approved if str(intent.action) == "buy"
    )


def _str_prop(node: Node | None, name: str) -> str | None:
    if node is None:
        return None
    value = node.props.get(name)
    return value if isinstance(value, str) else None
