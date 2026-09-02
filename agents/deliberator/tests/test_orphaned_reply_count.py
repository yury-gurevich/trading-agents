"""Deliberator orphaned peer-reply count tests.

Agent: deliberator
Role: prove late peer-reply counts are recorded per DeliberationRun.
External I/O: none.
"""

from __future__ import annotations

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.poll import review_pm_node
from agents.deliberator.store import DELIBERATION_RUN_LABEL
from agents.deliberator.tests.test_deliberator_agent import (
    _UPHOLD,
    _pm_node,
    _settings,
)
from contracts.deliberator import DebateTurnRecord, DebateTurnReply, DebateTurnRequest
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus


class _CountingPeerClient:
    def __init__(self, orphan_deltas: dict[str, int]) -> None:
        self._orphan_deltas = orphan_deltas
        self._counted_runs: set[str] = set()
        self.orphaned_reply_count = 0

    def preflight(self, recipients: tuple[str, ...]) -> None:
        del recipients

    def debate_turn(
        self, recipient: str, request: DebateTurnRequest
    ) -> DebateTurnReply:
        run_id = request.request_id.split(":", maxsplit=1)[0]
        if run_id not in self._counted_runs:
            self.orphaned_reply_count += self._orphan_deltas.get(run_id, 0)
            self._counted_runs.add(run_id)
        return DebateTurnReply(
            request_id=request.request_id,
            turn=DebateTurnRecord(
                role=request.role,
                round=request.round_number,
                text=f"{recipient} addressed",
            ),
        )


def test_manager_records_orphaned_reply_count_per_run_delta() -> None:
    """DLIB-OBS-04 / DLIB-NEV-06: late peer replies are counted per PM run."""
    graph = InMemoryGraphStore()
    first_pm = _pm_node(graph, "pm-1")
    second_pm = _pm_node(graph, "pm-2")
    manager_settings = _settings("manager", rounds=1)
    manager = DeliberatorAgent(
        InProcessBus(),
        graph=graph,
        llm=FakeLLMClient({"DECISION UNDER TEST": _UPHOLD}),
        settings=manager_settings,
    )
    peer = _CountingPeerClient({"pm-1": 2, "pm-2": 1})

    review_pm_node(
        first_pm,
        graph=graph,
        manager=manager,
        peer_client=peer,
        settings=manager_settings,
    )
    review_pm_node(
        second_pm,
        graph=graph,
        manager=manager,
        peer_client=peer,
        settings=manager_settings,
    )

    runs = {node.key: node for node in graph.list_nodes(DELIBERATION_RUN_LABEL)}
    assert runs["pm-1"].props["orphaned_reply_count"] == 2
    assert runs["pm-2"].props["orphaned_reply_count"] == 1
    assert peer.orphaned_reply_count == 3
