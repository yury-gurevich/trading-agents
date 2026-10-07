"""The guided debate signature and strict DSPy adapter.

Agent: kernel
Role: let DSPy render and execute the measured turn while preserving strict JSON.
External I/O: none; programs receive their LM through the caller's context.
"""

from __future__ import annotations

from typing import Any

import dspy  # type: ignore[import-untyped]

from kernel.deliberation_guided import GuidedReasoning, parse_guided_turn, unreadable


class DebateTurn(dspy.Signature):  # type: ignore[misc]
    """A debating role reads the packet before making its argument."""

    decision: str = dspy.InputField(desc="the decision under test")
    context: str = dspy.InputField(
        desc=(
            "the evidence packet for this decision; "
            "every value you read comes from here"
        )
    )
    transcript: str = dspy.InputField(desc="the debate so far")
    argument: str = dspy.OutputField(
        desc=(
            "step 3: your turn, at most ~5 sentences, "
            "built only from your readings and gaps"
        )
    )


class UnreadableTurnError(Exception):
    """Retain the unreadable completion and the strict parser's reason."""

    def __init__(self, reason: str, completion: str) -> None:
        """Keep both the raw text and its refusal reason."""
        super().__init__(reason)
        self.reason, self.completion = reason, completion


class StrictGuidedAdapter(dspy.ChatAdapter):  # type: ignore[misc]
    """Use DSPy's chat format with the existing strict parser (DL-252 D6)."""

    def __init__(self) -> None:
        """Disable the JSON adapter's additional call and repair behavior."""
        super().__init__(use_json_adapter_fallback=False)

    def parse(self, signature: type[dspy.Signature], completion: str) -> dict[str, Any]:
        """An unreadable or argument-free turn never triggers another call."""
        del signature  # The strict parser validates the frozen GuidedReasoning schema.
        turn = parse_guided_turn(completion)
        if turn.error is None and not turn.argument:
            turn = unreadable("empty field: argument")
        if turn.reasoning is None:
            raise UnreadableTurnError(turn.error or "unreadable", completion)
        return {"reasoning": turn.reasoning, "argument": turn.argument}


ADAPTER = StrictGuidedAdapter()


def guided_program(instructions: str) -> dspy.ChainOfThought:
    """Build one role's ChainOfThought with the unchanged reasoning schema."""
    return dspy.ChainOfThought(
        DebateTurn.with_instructions(instructions), rationale_field_type=GuidedReasoning
    )
