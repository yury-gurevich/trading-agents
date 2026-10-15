"""Deliberator review record helpers.

Agent: deliberator
Role: shape per-order debate outcomes into durable DeliberationRun fields.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from agents.deliberator.settings import DeliberatorSettings
    from contracts.deliberator import DebateProposition, DebateTurnRecord
    from kernel import GraphStore

_FAILED_OPEN_REASON_LIMIT = 500
_UNKNOWN_FAIL_OPEN_REASON = "UnknownError: reason unavailable"


@dataclass(frozen=True)
class OrderReview:
    """One order's recorded debate outcome."""

    verdict: str
    rationale: str
    turns: tuple[DebateTurnRecord, ...]
    llm_call_keys: tuple[str, ...]
    failed_open: bool = False
    failed_open_reason: str = ""
    #: The packet the roles were given; None only when building it failed.
    proposition: DebateProposition | None = None


def failed_open_reason(error_type: str, message: str) -> str:
    """Return the queryable fail-open cause stamped on DeliberationRun."""
    reason = f"{error_type}: {message}"
    if len(reason) <= _FAILED_OPEN_REASON_LIMIT:
        return reason
    return reason[: _FAILED_OPEN_REASON_LIMIT - 3] + "..."


def fail_open_review(
    reason: str | None = None, proposition: DebateProposition | None = None
) -> OrderReview:
    """Return the lawful fail-open review marker for one affected order."""
    recorded_reason = reason or _UNKNOWN_FAIL_OPEN_REASON
    return OrderReview(
        "uphold",
        f"fail-open: {recorded_reason}",
        (),
        (),
        failed_open=True,
        failed_open_reason=recorded_reason,
        proposition=proposition,
    )


def debate_record(review: OrderReview) -> dict[str, object]:
    """Return the per-ticker debate payload stored on DeliberationRun.

    The decision and packet are stored once per order, since every turn of the
    order read the same one (DLIB-OUT-07, DL-252 D4).
    """
    proposition = review.proposition
    return {
        "verdict": review.verdict,
        "rationale": review.rationale,
        "failed_open": review.failed_open,
        "failed_open_reason": review.failed_open_reason,
        "turns": [
            {"role": turn.role, "round": turn.round, "text": turn.text}
            for turn in review.turns
        ],
        "decision": proposition.decision if proposition is not None else None,
        "context": proposition.context if proposition is not None else None,
    }


def transcript_records(
    ticker: str, turns: tuple[DebateTurnRecord, ...]
) -> list[dict[str, object]]:
    """Return transcript rows stamped with the order ticker (DLIB-OUT-06).

    Each row keeps the guided reasoning exactly as parsed, or why it could not
    be read; a turn recorded before S246 has neither and reads as ``None``.
    """
    return [
        {
            "ticker": ticker,
            "role": turn.role,
            "round": turn.round,
            "text": turn.text,
            "reasoning": (
                turn.reasoning.model_dump(mode="json")
                if turn.reasoning is not None
                else None
            ),
            "reasoning_error": turn.reasoning_error,
        }
        for turn in turns
    ]


def narrative(debates: dict[str, object]) -> str:
    """Render the human-readable deliberation summary."""
    if not debates:
        return "No PM-approved orders required deliberation."
    return "; ".join(
        f"{ticker}: {record['verdict']} - {record['rationale']}"
        for ticker, record in sorted(debates.items())
        if isinstance(record, dict)
    )


def role_models(
    settings: DeliberatorSettings,
    graph: GraphStore | None = None,
    llm_call_keys: tuple[str, ...] | list[str] = (),
) -> dict[str, str]:
    """Return the three models stamped on a DeliberationRun: the ones that answered.

    Each role's entry is read from the run's own `LLMCall` rows by the identity
    that served it, because every replica chooses its LLM at activation (DL-289)
    and two replicas of one role may run on different models; several models
    are joined, sorted. A role with no row falls back to `model_for_role`: never
    the empty sentinel, never the other vendor's name (DL-100).
    """
    answered: dict[str, set[str]] = {}
    for key in llm_call_keys:
        node = graph.get_node("LLMCall", key) if graph is not None else None
        if node is not None and isinstance(node.props.get("model"), str):
            agent = str(node.props.get("calling_agent", ""))
            answered.setdefault(agent, set()).add(str(node.props["model"]))
    served: tuple[tuple[Literal["defender", "challenger", "judge"], str], ...] = (
        ("defender", settings.proponent_identity),
        ("challenger", settings.opponent_identity),
        ("judge", settings.identity),
    )
    return {
        role: ", ".join(sorted(answered.get(identity, ())))
        or settings.model_for_role(role)
        for role, identity in served
    }


def llm_switches(
    graph: GraphStore | None, llm_call_keys: tuple[str, ...] | list[str]
) -> list[str]:
    """Return each role that answered on a later candidate, and what refused first.

    Read from the run's own `LLMCall` rows: a row whose request a candidate refused
    before it names them under `llm_passed_over` (DLIB-FAIL-05). One line per role,
    model and refusals, in the order the rows were written.
    """
    lines: list[str] = []
    for key in llm_call_keys:
        node = graph.get_node("LLMCall", key) if graph is not None else None
        over = node.props.get("llm_passed_over") if node is not None else None
        if node is None or not isinstance(over, (list, tuple)) or not over:
            continue
        line = (
            f"{node.props.get('calling_agent', '')} switched to "
            f"{node.props.get('model', '')} (passed over {'; '.join(map(str, over))})"
        )
        if line not in lines:
            lines.append(line)
    return lines
