"""The guided turn's recorded text, its error vocabulary and its frozen schema.

Agent: kernel
Role: prove the turn text rendering (S246 B3's table), the bounded
      `reasoning_error` vocabulary (DL-252 D3), and that the frozen prefix states
      the kernel model's own schema (DL-252 D1).
External I/O: none.
"""

from __future__ import annotations

import json

import pytest
from pydantic import TypeAdapter

from kernel.deliberation import Turn
from kernel.deliberation_guided import (
    READ_FIRST,
    GuidedReasoning,
    parse_guided_turn,
    unreadable,
)
from kernel.deliberation_guided_render import render_guided_text, render_transcript
from kernel.deliberation_program import ADAPTER, guided_program

_READINGS = [
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
]


def _completion(reasoning: str, argument: str = "A.") -> str:
    return f"[[ ## reasoning ## ]]\n{reasoning}\n\n[[ ## argument ## ]]\n{argument}"


def test_the_turn_text_follows_the_rendering_table() -> None:
    """DLIB-OUT-06: readings, then gaps, then the argument, values verbatim."""
    reasoning = GuidedReasoning.model_validate(
        {"readings": _READINGS, "gaps": ["no holdings context"]}
    )

    assert render_guided_text(reasoning, "A.") == (
        "Readings:\n"
        "- pe = 30: 0-100 banded sub-score of P/E (against)\n"
        "- atr_pct = 2.935: 14-day ATR as percent of close (neutral)\n"
        "Gaps:\n"
        "- no holdings context\n"
        "Argument: A."
    )
    assert render_guided_text(GuidedReasoning(readings=[], gaps=[]), "A.") == (
        "Readings: none\nGaps: none\nArgument: A."
    )


def test_a_value_is_printed_exactly_as_the_model_copied_it() -> None:
    """DLIB-OUT-06: no number formatting; `5.87%` and `2.9350` stay as written."""
    readings = [
        {**_READINGS[0], "value": "5.87%"},
        {**_READINGS[1], "value": "2.9350"},
    ]
    text = render_guided_text(
        GuidedReasoning.model_validate({"readings": readings, "gaps": []}), "A."
    )

    assert "- pe = 5.87%: " in text
    assert "- atr_pct = 2.9350: " in text


def test_the_transcript_input_is_one_line_per_turn() -> None:
    """DL-252 D5: `[role rN] text` per turn, or `(none yet)`."""
    assert render_transcript(()) == "(none yet)"
    assert render_transcript(
        (Turn("defender", 1, "A.\nB."), Turn("challenger", 1, "C."))
    ) == ("[defender r1] A.\nB.\n[challenger r1] C.")


@pytest.mark.parametrize(
    ("completion", "error"),
    [
        (
            _completion(json.dumps({"readings": _READINGS})),
            "schema: gaps: Field required",
        ),
        (
            _completion(json.dumps({"readings": [{**_READINGS[0], "value": 30}]})),
            "schema: readings.0.value: Input should be a valid string (+1 more)",
        ),
        (
            _completion("[1, 2]"),
            "schema: (root): Input should be a valid dictionary or instance of "
            "GuidedReasoning",
        ),
        ("[[ ## reasoning ## ]]\n{}", "missing field: argument"),
        ("I uphold.", "missing field: reasoning, argument"),
    ],
)
def test_every_unreadable_reasoning_is_named_in_the_vocabulary(
    completion: str, error: str
) -> None:
    """DLIB-OUT-06: why a reasoning could not be read is short and specific."""
    turn = parse_guided_turn(completion)

    assert (turn.reasoning, turn.argument, turn.error) == (None, None, error)


def test_malformed_json_is_named_with_where_it_broke() -> None:
    """DLIB-OUT-06: the named deviation says where; the wording is Python's own."""
    turn = parse_guided_turn(_completion('{"readings": [], "gaps": [],}'))

    assert (turn.reasoning, turn.argument) == (None, None)
    assert str(turn.error).startswith("invalid JSON in reasoning: ")
    assert "line 1 column 28" in str(turn.error)


def test_a_reason_is_bounded_like_the_fail_open_reason() -> None:
    """DL-252 D3: 500 characters at most, the `failed_open_reason` precedent."""
    reason = unreadable("x" * 900).error

    assert reason is not None
    assert len(reason) == 500
    assert reason.endswith("...")
    assert unreadable("short").error == "short"


def test_the_frozen_prefix_states_the_models_own_schema() -> None:
    """DLIB-OUT-06: editing a field description without regenerating fails here.

    Rendered the way DSPy renders it (`type` first, keys sorted, non-ASCII kept),
    from the kernel model the runtime validates against.
    """

    def type_first(node: object) -> object:
        if isinstance(node, dict):
            items = sorted(node.items(), key=lambda kv: (kv[0] != "type", kv[0]))
            return {key: type_first(value) for key, value in items}
        if isinstance(node, list):
            return [type_first(item) for item in node]
        return node

    schema = type_first(TypeAdapter(GuidedReasoning).json_schema())
    rendered = json.dumps(schema, ensure_ascii=False)

    signature = guided_program("Argue.").predict.signature
    assert (
        f"must adhere to the JSON schema: {rendered}\n"
        in ADAPTER.format_system_message(signature)
    )
    assert json.dumps(READ_FIRST) in rendered
