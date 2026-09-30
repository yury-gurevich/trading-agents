"""Serve one guided turn, then print which DSPy modules got loaded (S246 B8).

Agent: kernel
Role: a separate interpreter for `test_no_dspy_at_runtime.py`, so nothing the
      test run already imported can hide or fake what the deliberator loads.
External I/O: stdout.
"""

from __future__ import annotations

import importlib
import sys

from agents.deliberator.guided_turn import guided_turn
from contracts.deliberator import DebateProposition, DebateTurnRequest

_COMPLETION = (
    '[[ ## reasoning ## ]]\n{"readings": [], "gaps": []}\n[[ ## argument ## ]]\nA.'
)


class _LLM:
    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        return _COMPLETION


def main() -> int:
    """Load the whole agent, serve a turn, and list any DSPy module loaded."""
    importlib.import_module("agents.deliberator.entrypoint")
    turn = guided_turn(
        _LLM(),
        DebateTurnRequest(
            request_id="r",
            proposition=DebateProposition(decision="d", context="c"),
            role="defender",
            round_number=1,
        ),
    )
    loaded = sorted(
        name
        for name in sys.modules
        if name.split(".")[0] == "dspy" or name == "kernel.dspy_optimizer"
    )
    print(f"reasoning={turn.reasoning is not None} loaded={loaded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
