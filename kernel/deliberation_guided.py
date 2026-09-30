"""The guided debate turn: its typed reasoning, its messages and its parser.

Agent: kernel
Role: define the reasoning a defender or challenger writes before its argument,
      render DSPy's ChainOfThought messages for it without importing DSPy, and
      parse a completion back into that reasoning, strictly (DL-252).
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from pydantic.config import JsonDict

    from kernel.deliberation import Turn


def _no_description(schema: JsonDict) -> None:
    """Keep a class docstring out of the schema the model reads."""
    schema.pop("description", None)


# Frozen like every recorded payload; that leaves the rendered schema unchanged.
# Unknown keys are dropped, as DSPy's own pydantic call drops them (DL-252 D6).
_RECORD = ConfigDict(frozen=True, json_schema_extra=_no_description)

#: The reasoning's schema description, rendered to the model. Set through
#: `json_schema_extra` because the sentence is longer than a docstring line.
READ_FIRST = (
    "Read before you argue: each later step may use only what the earlier "
    "steps established."
)


class EvidenceReading(BaseModel):
    """One value the turn relies on, read from the packet before it argues."""

    model_config = _RECORD

    metric: str = Field(
        description="the exact name as it appears in the evidence packet"
    )
    value: str = Field(description="the value copied exactly as the packet writes it")
    meaning_here: str = Field(
        description=(
            "one clause: what this measures in THIS system, not in general finance"
        )
    )
    bears_on: Literal["supports", "against", "neutral"] = Field(
        description="how it bears on the decision under test"
    )


class GuidedReasoning(BaseModel):
    """The reasoning a turn writes before its argument; described by `READ_FIRST`."""

    model_config = ConfigDict(
        frozen=True, json_schema_extra={"description": READ_FIRST}
    )

    readings: list[EvidenceReading] = Field(
        description="step 1: every value your argument relies on, read from the packet"
    )
    gaps: list[str] = Field(
        description=(
            "step 2: evidence the packet lacks, marks unavailable, "
            "or leaves unit/scope unknown"
        )
    )


@dataclass(frozen=True)
class GuidedTurn:
    """A parsed completion: the reasoning and argument, or why it could not be read."""

    reasoning: GuidedReasoning | None
    argument: str | None
    error: str | None = None


def guided_system(role_prompt: str) -> str:
    """Return DSPy's system message for this signature around one role prompt."""
    raise NotImplementedError


def guided_user(decision: str, context: str, transcript: str) -> str:
    """Return DSPy's user message for one turn's three inputs."""
    raise NotImplementedError


def render_transcript(transcript: tuple[Turn, ...]) -> str:
    """Return the debate so far as the guided message's transcript input."""
    raise NotImplementedError


def parse_guided_turn(completion: str) -> GuidedTurn:
    """Parse a completion as DSPy's ChatAdapter does, with strict JSON."""
    raise NotImplementedError


def render_guided_text(reasoning: GuidedReasoning, argument: str) -> str:
    """Return the turn text the next speaker and the judge read."""
    raise NotImplementedError
