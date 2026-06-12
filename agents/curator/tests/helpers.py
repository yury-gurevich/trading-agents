"""Curator test helpers.

Agent: curator
Role: seed TradeNarrative lineage fixtures and build dataset request messages.
External I/O: none.
"""

from __future__ import annotations

from contracts.curator import DatasetRequest
from kernel import AgentMessage, InMemoryGraphStore


def seed_narratives(
    graph: InMemoryGraphStore, count: int, *, trigger: str | None = "target"
) -> None:
    """Seed ``count`` TradeNarrative nodes plus Position/CloseDecision lineage."""
    for index in range(count):
        position_id = f"run-{index}:TICK{index}"
        position = graph.merge_node(
            "Position",
            position_id,
            {"run_id": f"run-{index}", "ticker": f"TICK{index}"},
        )
        narrative = graph.merge_node(
            "TradeNarrative",
            f"narrative:{position_id}",
            {
                "run_id": f"run-{index}",
                "position_id": position_id,
                "summary": f"story {index}",
            },
        )
        graph.add_edge(narrative, position, "NARRATES")
        if trigger is not None:
            close = graph.merge_node(
                "CloseDecision",
                f"monitor-{index}:{position_id}:close",
                {"position_id": position_id, "trigger": trigger},
            )
            graph.add_edge(close, position, "CLOSES")


def build_dataset_message(purpose: str = "exit-timing") -> AgentMessage:
    """Build a build_dataset request message for the curator."""
    return _message("build_dataset", purpose)


def describe_corpus_message(purpose: str = "exit-timing") -> AgentMessage:
    """Build a describe_corpus request message for the curator."""
    return _message("describe_corpus", purpose)


def _message(capability: str, purpose: str) -> AgentMessage:
    return AgentMessage(
        sender="test",
        recipient="curator",
        message_type="request",
        capability=capability,
        payload=DatasetRequest(purpose=purpose).model_dump(mode="json"),
    )
