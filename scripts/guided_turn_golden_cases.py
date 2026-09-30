"""The inputs the guided turn's golden is rendered and parsed from.

Agent: tooling
Role: hold the fixture role prompts, turn inputs and completions (S246's parse
      table, one row per case class, plus the edges DL-252 D6 names) that
      `render_guided_turn_golden.py` hands to real DSPy.
External I/O: none.

The tests read these back from the golden, never from here, so the golden stays
the whole definition: what DSPy was asked and what it answered, side by side.
"""

from __future__ import annotations

import json

# 🪤 DSPy dedents the role prompt, then indents *every* line, blank ones too, and
# drops a trailing newline. The champion prompts carry blank lines and a literal
# backslash-n inside their examples, so each of those is here.
SYSTEM_CASES: tuple[tuple[str, str], ...] = (
    (
        "blank_line_and_paragraph",
        "You are the CHALLENGER in a decision review.\n"
        "\n"
        "Attack the decision: find its weakest assumption,\n"
        "cite the value you read (e.g. 5.87% or 'Semiconductors'),\n"
        "and say what would change your mind.\n"
        "Example: a stop of 3% reads 'stop_pct=0.03\\nbasis=atr'.\n"
        "Max ~5 sentences — no more.",
    ),
    (
        "common_indent_and_trailing_newline",
        "  Two spaces lead every line.\n"
        "\n"
        "    This one leads with four.\n"
        "   \n"
        "  Back to two.\n",
    ),
    ("single_line", "Argue from the packet only. Max ~5 sentences."),
)

USER_CASES: tuple[tuple[str, dict[str, str]], ...] = (
    (
        "first_turn",
        {
            "decision": "buy AAPL (qty 12)",
            "context": (
                "confidence: 0.71 (floor 0.60, analyst)\n"
                "pe: 30\n"
                "atr_pct: 2.935\n"
                "sector: Semiconductors"
            ),
            "transcript": "(none yet)",
        },
    ),
    (
        "later_turn_with_edges",
        {
            "decision": "buy MSFT (qty 3)",
            "context": "\n  relative_strength: 5.87%\nearnings: 2026-10-19\n",
            "transcript": (
                "[defender r1] Readings:\n"
                "- pe = 30: 0-100 banded sub-score of P/E (against)\n"
                "Gaps: none\n"
                "Argument: A.\n"
                "[challenger r1] The stop is inside one ATR."
            ),
        },
    ),
    (
        "empty_transcript",
        {"decision": "sell X (qty 1)", "context": "c", "transcript": ""},
    ),
)

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
_VALID = json.dumps({"readings": _READINGS, "gaps": ["no holdings context"]})
_EMPTY = json.dumps({"readings": [], "gaps": []})
_SUPPORT = _VALID.replace('"against"', '"support"')
_NUMBER = _VALID.replace('"value": "30"', '"value": 30')
_TRAILING_COMMA = _VALID[:-1] + ",}"
_R = "[[ ## reasoning ## ]]\n"
_A = "\n\n[[ ## argument ## ]]\n"
_DONE = "\n\n[[ ## completed ## ]]"

PARSE_CASES: tuple[tuple[str, str], ...] = (
    # The spec's table (B2), one row per case class.
    ("valid", _R + _VALID + _A + "A." + _DONE),
    ("no_completed_marker", _R + _VALID + _A + "A."),
    ("preamble", "Let me read the packet first.\n\n" + _R + _VALID + _A + "A." + _DONE),
    ("empty_readings", _R + _EMPTY + _A + "A." + _DONE),
    ("bears_on_outside_enum", _R + _SUPPORT + _A + "A." + _DONE),
    ("missing_argument", _R + _VALID + _DONE),
    ("malformed_json_trailing_comma", _R + _TRAILING_COMMA + _A + "A." + _DONE),
    # Edges DL-252 D6 names, so the parity covers them too.
    ("fenced_json", _R + "```json\n" + _VALID + "\n```" + _A + "A." + _DONE),
    ("header_with_inline_content", _R + _VALID + "\n\n[[ ## argument ## ]] A." + _DONE),
    ("first_section_wins", _R + _VALID + _A + "A." + _A + "B." + _DONE),
    ("unknown_header_between", _R + _VALID + "\n\n[[ ## notes ## ]]\nN." + _A + "A."),
    ("multi_line_argument", _R + _VALID + _A + "  A.\nB.\n\n  " + _DONE),
    ("empty_argument", _R + _VALID + _A + _DONE),
    ("value_as_number", _R + _NUMBER + _A + "A." + _DONE),
    ("reasoning_not_an_object", _R + "[1, 2]" + _A + "A." + _DONE),
    ("no_sections", "I uphold the decision."),
)
