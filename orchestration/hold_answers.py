"""Append-only RunHoldAnswer facts and deterministic answer precedence.

Agent: orchestration
Role: record human hold answers without mutating prior decisions.
External I/O: reads and writes the injected GraphStore.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from datetime import date, datetime

    from kernel import GraphStore

Answer = Literal["run_now", "skip_today"]
Source = Literal["telegram", "dashboard"]
_ANSWERS = frozenset(("run_now", "skip_today"))


def record_answer(
    graph: GraphStore,
    *,
    run_id: str,
    as_of: date,
    answer: Answer,
    source: Source,
    answered_at: datetime,
    update_id: int,
) -> bool:
    """Append one answer unless a Telegram update was already recorded."""
    answers = tuple(graph.list_nodes("RunHoldAnswer"))
    if update_id and any(node.props.get("update_id") == update_id for node in answers):
        return False
    ordinal = 1 + sum(
        node.props.get("run_id") == run_id and node.props.get("source") == source
        for node in answers
    )
    graph.merge_node(
        "RunHoldAnswer",
        f"answer:{run_id}:{source}:{ordinal}",
        {
            "run_id": run_id,
            "as_of": as_of.isoformat(),
            "answer": answer,
            "source": source,
            "answered_at": answered_at.isoformat(timespec="seconds"),
            "update_id": update_id,
        },
    )
    return True


def effective_answer(graph: GraphStore, *, run_id: str) -> Answer | None:
    """Return the earliest valid answer fact for one scheduled run."""
    answers = [
        node
        for node in graph.list_nodes("RunHoldAnswer")
        if node.props.get("run_id") == run_id and node.props.get("answer") in _ANSWERS
    ]
    if not answers:
        return None
    first = min(answers, key=lambda node: str(node.props.get("answered_at", "")))
    return cast("Answer", first.props["answer"])
