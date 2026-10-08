"""Plain peer threads retain their own clients and packets (S254 A7).

Agent: deliberator
Role: exercise shared programs with four overlapping served calls.
External I/O: none; a barrier coordinates canned clients.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

from agents.deliberator.tests.dspy_fixtures import (
    MAIN,
    Client,
    answer_for,
    request_for,
    served,
)


def test_concurrent_turns_keep_their_own_client_and_packet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DLIB-ORD-01 / DLIB-OUT-06: plain threads share programs, never LM context."""
    from importlib import import_module

    def forbidden(**kwargs: object) -> None:
        raise AssertionError("global LM configuration is forbidden")

    monkeypatch.setattr(import_module("dspy"), "configure", forbidden)
    barrier = Barrier(4)

    class WaitingClient(Client):
        def complete(
            self, *, system: str, user: str, tool_schema: dict[str, object]
        ) -> str:
            barrier.wait(timeout=15)
            return super().complete(system=system, user=user, tool_schema=tool_schema)

    def run(index: int) -> None:
        role = "defender" if index % 2 == 0 else "challenger"
        marker = f"unique packet {index}"
        answer = str(answer_for("valid")).replace("\nA.", f"\n{marker}")
        client = WaitingClient(answer)
        agent, graph = served(role, client)
        request = request_for(next(c for c in MAIN["requests"] if c["role"] == role))
        request = request.model_copy(
            update={
                "request_id": f"thread-{index}",
                "proposition": request.proposition.model_copy(
                    update={"context": marker}
                ),
            }
        )
        turn = agent.debate_turn(request).turn
        assert turn.reasoning is not None
        assert turn.text.endswith(f"Argument: {marker}")
        assert len(client.calls) == len(graph.list_nodes("LLMCall")) == 1
        assert marker in client.calls[0][1]
        assert all(
            f"unique packet {other}" not in client.calls[0][1]
            for other in range(4)
            if other != index
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(run, range(4)))
