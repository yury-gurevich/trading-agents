"""The runtime renders and parses what DSPy renders and parses (S246 B1, B2).

Agent: kernel
Role: prove DSPy's current rendering byte-identical to the recorded golden,
      with strict JSON as the one named deviation (DL-252 D1, D6).
External I/O: reads tests/fixtures/deliberation_guided_golden.json.
"""

from __future__ import annotations

import json
from pathlib import Path

import dspy
import pytest

from kernel.deliberation_guided import parse_guided_turn
from kernel.deliberation_program import ADAPTER, guided_program

GOLDEN = json.loads(
    (Path(__file__).parent / "fixtures" / "deliberation_guided_golden.json").read_text(
        encoding="utf-8"
    )
)
#: Where DSPy's `json_repair` accepts what strict `json.loads` refuses: the one
#: named deviation (a trailing comma is the spec's row, a fence the same class).
DEVIATIONS = frozenset({"malformed_json_trailing_comma", "fenced_json"})
_SPEC_ROWS = {
    "valid",
    "no_completed_marker",
    "preamble",
    "empty_readings",
    "bears_on_outside_enum",
    "missing_argument",
    "malformed_json_trailing_comma",
}


def _cases(section: str) -> list[dict[str, object]]:
    return list(GOLDEN[section])


def _named(cases: list[dict[str, object]]) -> list[object]:
    return [pytest.param(case, id=str(case["name"])) for case in cases]


def test_the_golden_was_written_by_dspy_and_covers_the_spec_table() -> None:
    """A hand-made golden proves nothing: it names its generator and its rows."""
    assert GOLDEN["generator"] == "scripts/render_guided_turn_golden.py"
    assert GOLDEN["dspy_version"] == dspy.__version__
    assert {case["name"] for case in _cases("parse")} >= _SPEC_ROWS
    assert {case["name"] for case in _cases("parse")} >= DEVIATIONS


def test_the_frozen_prefix_and_requirements_are_dspys() -> None:
    """DLIB-OUT-06: the field-description, structure and reminder text are DSPy's."""
    signature = guided_program("Argue.").predict.signature
    assert GOLDEN["prefix"] == (
        ADAPTER.format_field_description(signature)
        + "\n"
        + ADAPTER.format_field_structure(signature)
        + "\n"
    )
    assert GOLDEN["requirements"] == ADAPTER.user_message_output_requirements(signature)


@pytest.mark.parametrize("case", _named(_cases("system")))
def test_the_system_message_is_byte_identical_to_dspys(case: dict[str, str]) -> None:
    """DLIB-OUT-06 / DLIB-OBS-06: one frozen system string per role prompt, DSPy's."""
    signature = guided_program(case["instructions"]).predict.signature
    assert ADAPTER.format_system_message(signature) == case["rendered"]


@pytest.mark.parametrize("case", _named(_cases("user")))
def test_the_user_message_is_byte_identical_to_dspys(case: dict[str, object]) -> None:
    """DLIB-OUT-06: the turn is asked for in DSPy's own words and sections."""
    inputs = case["inputs"]
    assert isinstance(inputs, dict)
    signature = guided_program("Argue.").predict.signature
    assert (
        ADAPTER.format_user_message_content(signature, inputs, main_request=True)
        == case["rendered"]
    )


@pytest.mark.parametrize(
    "case", _named([c for c in _cases("parse") if c["name"] not in DEVIATIONS])
)
def test_the_runtime_parses_what_dspy_parses(case: dict[str, object]) -> None:
    """DLIB-OUT-06: every row DSPy reads, the runtime reads identically."""
    expected = case["dspy"]
    assert isinstance(expected, dict)
    turn = parse_guided_turn(str(case["completion"]))
    if expected["parsed"]:
        assert turn.error is None
        assert turn.reasoning is not None
        assert turn.reasoning.model_dump(mode="json") == expected["reasoning"]
        assert turn.argument == expected["argument"]
    else:
        assert (turn.reasoning, turn.argument) == (None, None)
        assert turn.error


@pytest.mark.parametrize(
    "case", _named([c for c in _cases("parse") if c["name"] in DEVIATIONS])
)
def test_the_named_deviation_records_an_error_where_dspy_repairs(
    case: dict[str, object],
) -> None:
    """DLIB-OUT-06: a repaired reading is not the one the model wrote.

    🪤 The row exists so "we parse everything" cannot come from silently
    repairing JSON: DSPy parsed it, and the runtime must refuse it by name.
    """
    expected = case["dspy"]
    assert isinstance(expected, dict)
    assert expected["parsed"] is True
    turn = parse_guided_turn(str(case["completion"]))
    assert (turn.reasoning, turn.argument) == (None, None)
    assert str(turn.error).startswith("invalid JSON in reasoning: ")
