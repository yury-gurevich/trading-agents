"""Guided-turn fixtures for deliberator tests.

Agent: deliberator
Role: provide guided completions, their expected turn text, and an LLM that
      records the messages it was sent (S246).
External I/O: none.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

REASONING: dict[str, object] = {
    "readings": [
        {
            "metric": "pe",
            "value": "30",
            "meaning_here": "0-100 banded sub-score of P/E",
            "bears_on": "against",
        },
        {
            "metric": "atr_pct",
            "value": "2.935",
            "meaning_here": "14-day ATR as percent of close",
            "bears_on": "neutral",
        },
    ],
    "gaps": ["no holdings context"],
}
EMPTY_REASONING: dict[str, object] = {"readings": [], "gaps": []}


def completion(reasoning: dict[str, object], argument: str = "A.") -> str:
    """Return a guided completion in DSPy's ChatAdapter sections."""
    return (
        "[[ ## reasoning ## ]]\n"
        f"{json.dumps(reasoning)}\n\n"
        "[[ ## argument ## ]]\n"
        f"{argument}\n\n"
        "[[ ## completed ## ]]"
    )


VALID = completion(REASONING)
#: The spec's rendering table, row 1 (B3).
EXPECTED_TEXT = (
    "Readings:\n"
    "- pe = 30: 0-100 banded sub-score of P/E (against)\n"
    "- atr_pct = 2.935: 14-day ATR as percent of close (neutral)\n"
    "Gaps:\n"
    "- no holdings context\n"
    "Argument: A."
)
#: The spec's rendering table, row 2 (B3).
EXPECTED_EMPTY_TEXT = "Readings: none\nGaps: none\nArgument: A."

#: The parse table's error rows, each a completion the runtime cannot read (B4).
UNREADABLE: dict[str, str] = {
    "bears_on_outside_enum": VALID.replace('"against"', '"support"'),
    "missing_argument": VALID.split("\n\n[[ ## argument ## ]]")[0],
    "malformed_json_trailing_comma": VALID.replace(
        '["no holdings context"]}', '["no holdings context"],}'
    ),
    "no_sections": "I uphold the decision, it clears every gate.",
    "empty_argument": completion(REASONING, argument=""),
}


class RecordingLLM:
    """An LLM that answers by role and records every message pair it is sent."""

    def __init__(self, answer: str, *, judge_answer: str = "") -> None:
        self.answer = answer
        self.judge_answer = judge_answer
        self.calls: list[tuple[str, str]] = []

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del tool_schema
        self.calls.append((system, user))
        if user.startswith("DECISION UNDER TEST"):
            return self.judge_answer
        return self.answer


def without_packets(props: Mapping[str, object]) -> str:
    """Render a DeliberationRun's props with each order's recorded packet removed."""
    debates = props.get("debates")
    assert isinstance(debates, Mapping)
    return repr(
        {
            **props,
            "debates": {
                ticker: {
                    key: value for key, value in record.items() if key != "context"
                }
                for ticker, record in debates.items()
            },
        }
    )
