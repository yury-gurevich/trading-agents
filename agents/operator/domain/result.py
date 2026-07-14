"""Operator LLM result parsing helpers.

Agent: operator
Role: normalize model output into typed command results and intent provenance.
External I/O: none.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Literal

from agents.operator.domain.grammar import apply_confirmation_policy
from contracts.common import Explanation, Provenance
from contracts.operator import CommandResult, TypedIntent

if TYPE_CHECKING:
    from kernel import Node

Outcome = Literal["intent", "refused", "needs_clarification"]


def parse_json(raw: str) -> dict[str, object]:
    """Parse model JSON, normalizing malformed output to a refusal."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"outcome": "refused", "reason": "model returned malformed JSON"}
    return data if isinstance(data, dict) else {"outcome": "refused"}


def outcome(data: dict[str, object]) -> Outcome:
    """Return a contract-valid command outcome."""
    raw = data.get("outcome")
    if raw in ("intent", "refused", "needs_clarification"):
        return raw
    return "refused"


def intent_from_data(
    data: dict[str, object], correlation_id: str
) -> TypedIntent | None:
    """Build a TypedIntent and apply grammar-owned confirmation policy."""
    try:
        intent = TypedIntent(
            family=str(data.get("family", "status")),  # type: ignore[arg-type]
            parameters=_params(data.get("parameters", {})),
            requires_confirmation=False,
            provenance=Provenance(run_id=correlation_id, source_agent="operator"),
        )
        return apply_confirmation_policy(intent.family, intent)
    except ValueError:
        return None


def message(data: dict[str, object]) -> Explanation:
    """Build a non-empty operator-facing explanation."""
    return Explanation(summary=str(data.get("reason") or "Command refused."))


def refused(reason: str) -> CommandResult:
    """Build a refused CommandResult with a concrete reason."""
    return CommandResult(outcome="refused", message=Explanation(summary=reason))


def with_graph(intent: TypedIntent, node: Node) -> TypedIntent:
    """Attach graph provenance after the Intent node has been written."""
    return intent.model_copy(
        update={
            "provenance": Provenance(
                run_id=intent.provenance.run_id,
                source_agent="operator",
                graph_node_id=f"{node.label}:{node.key}",
            )
        }
    )


def correlation_id(*parts: str) -> str:
    """Return a stable command correlation id."""
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:16]


def request_correlation(request_id: str | None, *parts: str) -> str:
    """Keep legacy idempotence unless a surface identifies a distinct request."""
    return correlation_id(*parts, request_id) if request_id else correlation_id(*parts)


def _params(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}
