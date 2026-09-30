"""The guided debate turn as a DSPy program, for offline use only.

Agent: tooling
Role: define the DebateTurn signature and the ChainOfThought program whose
      rendering and parsing the runtime reproduces without DSPy (S246, DL-252).
External I/O: imports the offline `dspy` package lazily, as
      `kernel/dspy_optimizer.py` does; no LLM call is made here.

No image installs `dspy` (DL-184) and CI syncs without the `optimizer` extra, so
the module is built on an injected DSPy (the S119 pattern): tests hand it a fake,
and the golden writer hands it nothing, which imports the real one.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from kernel.deliberation_guided import GuidedReasoning

if TYPE_CHECKING:
    from types import ModuleType


def load_dspy(dspy_module: ModuleType | None = None) -> ModuleType:
    """Return the injected DSPy module, importing the real one only if none is."""
    if dspy_module is not None:
        return dspy_module
    return importlib.import_module("dspy")


def debate_turn_signature(dspy: ModuleType) -> type:
    """Return the DebateTurn signature, built on the given DSPy module."""

    class DebateTurn(dspy.Signature):  # type: ignore[name-defined, misc]
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

    return DebateTurn


def guided_program(instructions: str, dspy_module: ModuleType | None = None) -> object:
    """Return the ChainOfThought program for one role prompt."""
    dspy = load_dspy(dspy_module)
    signature = debate_turn_signature(dspy).with_instructions(instructions)  # type: ignore[attr-defined]
    return dspy.ChainOfThought(signature, rationale_field_type=GuidedReasoning)
