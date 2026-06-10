"""Reporter narrative composition.

Agent: reporter
Role: compose deterministic scan-to-exit trade stories from graph nodes.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kernel import Node

UNAVAILABLE = "(data unavailable)"
CENTS_PER_DOLLAR = 100


def compose_story(
    position: Node | None,
    fill: Node | None,
    order_intent: Node | None,
    recommendation: Node | None,
    candidate: Node | None,
    scan_run: Node | None,
    close_decision: Node | None,
) -> str:
    """Compose one deterministic position story, tolerating missing graph legs."""
    ticker = _text(_first_prop("ticker", position, fill, order_intent, recommendation))
    return (
        f"{ticker} scanned [{_text(_prop(scan_run, 'created_at'))}] as candidate "
        f"rank {_text(_prop(candidate, 'rank'))} "
        f"(score {_number(_prop(candidate, 'score'), '.2f')}). "
        f"Technical score {_number(_prop(recommendation, 'technical_score'), '.2f')}, "
        f"confidence {_percent(_prop(recommendation, 'confidence'))} -> "
        f"{_text(_prop(order_intent, 'action'))}. "
        f"{_text(_prop(order_intent, 'quantity'))} shares approved, est. "
        f"{_money(_prop(order_intent, 'est_price_cents'))}, stop "
        f"{_percent(_prop(order_intent, 'stop_pct'))} / target "
        f"{_percent(_prop(order_intent, 'target_pct'))}. "
        f"Position opened at {_money(_prop(position, 'opened_price_cents'))}. "
        f"{_exit_text(close_decision)}"
    )


def _exit_text(close_decision: Node | None) -> str:
    if close_decision is None:
        return "Position still open."
    trigger = _text(_prop(close_decision, "trigger"))
    rationale = _text(_prop(close_decision, "rationale"))
    return f"Exit: {trigger} - {rationale}."


def _first_prop(prop: str, *nodes: Node | None) -> Any:  # noqa: ANN401
    for node in nodes:
        value = _prop(node, prop)
        if value is not None:
            return value
    return None


def _prop(node: Node | None, prop: str) -> Any:  # noqa: ANN401
    return None if node is None else node.props.get(prop)


def _text(value: Any) -> str:  # noqa: ANN401
    return UNAVAILABLE if value is None else str(value)


def _number(value: Any, spec: str) -> str:  # noqa: ANN401
    if value is None:
        return UNAVAILABLE
    try:
        return format(float(value), spec)
    except (TypeError, ValueError):
        return UNAVAILABLE


def _percent(value: Any) -> str:  # noqa: ANN401
    if value is None:
        return UNAVAILABLE
    try:
        return f"{float(value):.0%}"
    except (TypeError, ValueError):
        return UNAVAILABLE


def _money(value: Any) -> str:  # noqa: ANN401
    if value is None:
        return UNAVAILABLE
    try:
        return f"{float(value) / CENTS_PER_DOLLAR:.2f}"
    except (TypeError, ValueError):
        return UNAVAILABLE
