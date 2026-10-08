"""The guided turn's offline instruments use real DSPy and canned completions.

Agent: tooling
Role: prove the real golden writer matches the committed cases and bytes, and
      that the live-check instrument prints one line per turn with a fake LLM.
External I/O: writes one JSON file under tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.guided_turn_golden_cases import PARSE_CASES, SYSTEM_CASES, USER_CASES
from scripts.guided_turn_replay import latest_subjects, replay, summary
from scripts.render_guided_turn_golden import build_golden, write_golden
from tests.veto_context_fixtures import intent, linked_graph, order_set

from kernel import InMemoryGraphStore
from kernel.deliberation_guided import GuidedReasoning
from kernel.deliberation_program import guided_program

if TYPE_CHECKING:
    from kernel.llm import LLMClient
    from orchestration.replay_types import ReplaySubject

GOLDEN = json.loads(
    (Path(__file__).parent / "fixtures" / "deliberation_guided_golden.json").read_text(
        encoding="utf-8"
    )
)


def test_the_program_is_the_spec_signature_with_the_typed_reasoning() -> None:
    """DLIB-OUT-06: real DSPy asks for the unchanged typed reasoning first."""
    signature = guided_program("Argue.").predict.signature
    assert signature.instructions == "Argue."
    assert signature.output_fields["reasoning"].annotation is GuidedReasoning
    assert (
        signature.fields["argument"]
        .json_schema_extra["desc"]
        .startswith("step 3: your turn")
    )
    assert [
        signature.fields[n].json_schema_extra["desc"]
        for n in ("decision", "transcript")
    ] == [
        "the decision under test",
        "the debate so far",
    ]


def test_the_golden_writer_produces_the_goldens_shape(tmp_path: Path) -> None:
    """DLIB-OUT-06: real DSPy reproduces every golden byte, without an LLM."""
    path = write_golden(tmp_path / "golden.json")
    assert json.loads(path.read_text("utf-8")) == build_golden() == GOLDEN
    assert (
        path.read_bytes()
        == (
            Path(__file__).parent / "fixtures" / "deliberation_guided_golden.json"
        ).read_bytes()
    )


def test_the_committed_golden_was_rendered_from_todays_cases() -> None:
    """Editing a case without regenerating the golden fails here, not silently."""
    assert [(c["name"], c["instructions"]) for c in GOLDEN["system"]] == list(
        SYSTEM_CASES
    )
    assert [(c["name"], c["inputs"]) for c in GOLDEN["user"]] == list(USER_CASES)
    assert [(c["name"], c["completion"]) for c in GOLDEN["parse"]] == list(PARSE_CASES)


class _LLM:
    """Answers the defender with a reading and the challenger with prose."""

    def __init__(self, answer: str, *, fail: bool = False) -> None:
        self.answer = answer
        self.fail = fail
        self.last_stop_reason = "end_turn"

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        if self.fail:
            raise RuntimeError("provider down")
        return self.answer


_READ = (
    '[[ ## reasoning ## ]]\n{"readings": [], "gaps": ["x"]}\n[[ ## argument ## ]]\nA.'
)


def _subject() -> ReplaySubject:
    graph = InMemoryGraphStore()
    linked_graph(graph, full=True)
    graph.merge_node(
        "PMRun", "pm", {"order_intent_set": order_set(intent()).model_dump(mode="json")}
    )
    (subject,) = latest_subjects(graph, 10)
    assert latest_subjects(graph, 0) == ()
    return subject


def test_the_replay_instrument_prints_one_line_per_turn() -> None:
    """The planner's live check: parse, readings, latency, tokens, stop, per turn."""
    llms: dict[str, LLMClient] = {
        "defender": _LLM(_READ),
        "challenger": _LLM("I object."),
    }
    reports = replay(llms, (_subject(),))  # type: ignore[arg-type]

    assert [(r.subject, r.role, r.parse, r.readings) for r in reports] == [
        ("pm:AAPL", "defender", "ok", 0),
        ("pm:AAPL", "challenger", "missing field: reasoning, argument", 0),
    ]
    line = reports[0].line()
    assert line.startswith("pm:AAPL\tdefender\treadings=0\tlatency_s=")
    assert line.endswith("\ttokens_out=?\tstop=end_turn\tparse=ok")
    assert summary(reports).startswith("parsed 1 of 2; max_tokens stops 0; ")


def test_a_failed_call_is_a_row_and_ends_that_subject() -> None:
    """A provider failure is reported, not raised, and skips that challenger."""
    reports = replay(
        {"defender": _LLM("", fail=True), "challenger": _LLM(_READ)},  # type: ignore[dict-item]
        (_subject(),),
    )

    assert [(r.role, r.parse) for r in reports] == [
        ("defender", "call failed: RuntimeError: provider down")
    ]
    assert (
        summary([]) == "parsed 0 of 0; max_tokens stops 0; challenger max latency_s n/a"
    )
