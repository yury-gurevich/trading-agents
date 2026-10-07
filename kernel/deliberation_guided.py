"""The guided debate turn: its typed reasoning, its messages and its parser.

Agent: kernel
Role: define the reasoning a defender or challenger writes before its argument,
      render its recorded text and parse a completion strictly (DL-252).
External I/O: none.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from kernel.deliberation_guided_render import render_guided_text as render_guided_text
from kernel.deliberation_guided_render import render_transcript as render_transcript

if TYPE_CHECKING:
    from pydantic.config import JsonDict


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


#: DSPy's section header (`dspy/adapters/chat_adapter.py`), matched at the start
#: of each stripped line.
HEADER = re.compile(r"\[\[ ## (\w+) ## \]\]")
_OUTPUTS = ("reasoning", "argument")
#: The precedent is `failed_open_reason`'s cap (DL-252 D3).
_ERROR_LIMIT = 500


@dataclass(frozen=True)
class GuidedTurn:
    """A parsed completion: the reasoning and argument, or why it could not be read."""

    reasoning: GuidedReasoning | None
    argument: str | None
    error: str | None = None


def parse_guided_turn(completion: str) -> GuidedTurn:
    """Parse a completion as DSPy's `ChatAdapter.parse` does, with strict JSON.

    The one named deviation (DL-252 D6): the reasoning is read with `json.loads`,
    where DSPy would first repair it with `json_repair`. A repaired reading is
    not the one the model wrote, so it is refused by name instead.
    """
    sections = _sections(completion)
    missing = [name for name in _OUTPUTS if name not in sections]
    if missing:
        return unreadable("missing field: " + ", ".join(missing))
    try:
        payload = json.loads(sections["reasoning"])
    except json.JSONDecodeError as exc:
        return unreadable(f"invalid JSON in reasoning: {exc}")
    try:
        reasoning = GuidedReasoning.model_validate(payload)
    except ValidationError as exc:
        return unreadable(_schema_error(exc))
    return GuidedTurn(reasoning, sections["argument"])


def unreadable(reason: str) -> GuidedTurn:
    """Return a turn whose reasoning could not be read, with a bounded reason."""
    if len(reason) > _ERROR_LIMIT:
        reason = reason[: _ERROR_LIMIT - 3] + "..."
    return GuidedTurn(None, None, reason)


def _sections(completion: str) -> dict[str, str]:
    """Split on DSPy's headers; the first section of each name wins, as in DSPy."""
    found: dict[str, str] = {}
    name: str | None = None
    lines: list[str] = []
    for line in completion.splitlines():
        match = HEADER.match(line.strip())
        if match is None:
            lines.append(line)
            continue
        if name is not None:
            found.setdefault(name, "\n".join(lines).strip())
        name = match.group(1)
        # DSPy slices the *unstripped* line at the stripped match's end; kept so
        # an indented header parses as it does there.
        rest = line[match.end() :].strip()
        lines = [rest] if rest else []
    if name is not None:
        found.setdefault(name, "\n".join(lines).strip())
    return found


def _schema_error(exc: ValidationError) -> str:
    errors = exc.errors()
    first = errors[0]
    where = ".".join(str(part) for part in first["loc"]) or "(root)"
    more = f" (+{len(errors) - 1} more)" if len(errors) > 1 else ""
    return f"schema: {where}: {first['msg']}{more}"
