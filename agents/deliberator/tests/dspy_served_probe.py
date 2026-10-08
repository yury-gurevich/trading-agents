"""Serve every main request in a separate interpreter (S254 A1).

Agent: deliberator
Role: observe that serving really executes DSPy's ChainOfThought program.
External I/O: reads the main-record fixture and writes stdout; canned client only.
"""

from __future__ import annotations

import json
import sys
from importlib import import_module
from pathlib import Path
from typing import Any

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.settings import DeliberatorSettings
from contracts.deliberator import DebateTurnRequest
from kernel import InMemoryGraphStore, InProcessBus


class Client:
    """Record the system and user strings delivered to the vendor boundary."""

    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        assert tool_schema == {}
        self.calls.append((system, user))
        return self.answer


def main() -> None:
    """Execute six served requests and compare actual calls with main's fixture."""
    assert "dspy" in sys.modules, "a served deliberator must load DSPy"
    dspy = import_module("dspy")

    original = dspy.ChainOfThought.forward
    executed: list[object] = []

    def observed(program: object, **inputs: Any) -> Any:
        executed.append(program)
        return original(program, **inputs)

    dspy.ChainOfThought.forward = observed
    fixture = json.loads(
        Path("tests/fixtures/guided_turn_main_records.json").read_text("utf-8")
    )
    for case in fixture["requests"]:
        client = Client(fixture["answers"][0]["completion"])
        agent = DeliberatorAgent(
            InProcessBus(),
            graph=InMemoryGraphStore(),
            llm=client,
            settings=DeliberatorSettings(
                role="proponent" if case["role"] == "defender" else "opponent"
            ),
        )
        reply = agent.debate_turn(DebateTurnRequest.model_validate(case["request"]))
        assert reply.turn.reasoning is not None
        assert client.calls == [(fixture["systems"][case["role"]], case["user"])]
    assert len(executed) == 6
    print("served DSPy turns 6; identical single calls 6")


if __name__ == "__main__":
    main()
