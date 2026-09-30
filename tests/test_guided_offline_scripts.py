"""The guided turn's offline scripts run without DSPy installed (S246 B11).

Agent: tooling
Role: prove the golden writer produces the golden's shape through an injected
      fake `dspy`, that the committed golden was rendered from today's cases, and
      that the live-check instrument prints one line per turn with a fake LLM.
External I/O: writes one JSON file under tmp_path.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING

from scripts.deliberation_guided_program import guided_program, load_dspy
from scripts.guided_turn_golden_cases import PARSE_CASES, SYSTEM_CASES, USER_CASES
from scripts.guided_turn_replay import latest_subjects, replay, summary
from scripts.render_guided_turn_golden import build_golden, write_golden
from tests.veto_context_fixtures import intent, linked_graph, order_set

from kernel import InMemoryGraphStore
from kernel.deliberation_guided import GuidedReasoning

if TYPE_CHECKING:
    from kernel.llm import LLMClient
    from orchestration.replay_types import ReplaySubject

GOLDEN = json.loads(
    (Path(__file__).parent / "fixtures" / "deliberation_guided_golden.json").read_text(
        encoding="utf-8"
    )
)


class _Field:
    def __init__(self, *, desc: str) -> None:
        self.desc = desc


class _Signature:
    instructions = ""

    @classmethod
    def with_instructions(cls, text: str) -> type:
        return type(cls.__name__, (cls,), {"instructions": text})


class _ChainOfThought:
    def __init__(self, signature: type, rationale_field_type: type) -> None:
        self.predict = SimpleNamespace(signature=(signature, rationale_field_type))


class _Adapter:
    def format_field_description(self, signature: object) -> str:
        return "D"

    def format_field_structure(self, signature: object) -> str:
        return "S"

    def format_system_message(self, signature: tuple[type, type]) -> str:
        return f"SYS:{signature[0].instructions}"  # type: ignore[attr-defined]

    def user_message_output_requirements(self, signature: object) -> str:
        return "REQ"

    def format_user_message_content(
        self, signature: object, inputs: dict[str, str], main_request: bool
    ) -> str:
        return f"USER:{inputs['decision']}:{main_request}"

    def parse(self, signature: object, completion: str) -> dict[str, object]:
        if "[[ ## argument ## ]]" not in completion:
            raise ValueError("no argument section")
        return {"reasoning": GuidedReasoning(readings=[], gaps=[]), "argument": "A."}


def _fake_dspy() -> ModuleType:
    dspy = ModuleType("dspy")
    dspy.Signature = _Signature  # type: ignore[attr-defined]
    dspy.InputField = _Field  # type: ignore[attr-defined]
    dspy.OutputField = _Field  # type: ignore[attr-defined]
    dspy.ChainOfThought = _ChainOfThought  # type: ignore[attr-defined]
    dspy.ChatAdapter = _Adapter  # type: ignore[attr-defined]
    dspy.__version__ = "fake"  # type: ignore[attr-defined]
    return dspy


def test_the_program_is_the_spec_signature_with_the_typed_reasoning() -> None:
    """The program asks for GuidedReasoning before the argument, on the role prompt."""
    dspy = _fake_dspy()
    program = guided_program("Argue.", dspy)
    signature, rationale = program.predict.signature  # type: ignore[attr-defined]

    assert load_dspy(dspy) is dspy
    assert rationale is GuidedReasoning
    assert signature.instructions == "Argue."
    assert signature.argument.desc.startswith("step 3: your turn")
    assert [signature.decision.desc, signature.transcript.desc] == [
        "the decision under test",
        "the debate so far",
    ]


def test_the_golden_writer_produces_the_goldens_shape(tmp_path: Path) -> None:
    """Every case is rendered or parsed, and a refusal is recorded by its type."""
    written = json.loads(
        write_golden(tmp_path / "golden.json", _fake_dspy()).read_text("utf-8")
    )

    assert written == build_golden(_fake_dspy())
    assert list(written) == list(GOLDEN)
    assert (written["prefix"], written["requirements"]) == ("D\nS\n", "REQ")
    assert [case["rendered"] for case in written["system"]] == [
        f"SYS:{text}" for _, text in SYSTEM_CASES
    ]
    assert written["user"][0]["rendered"] == "USER:buy AAPL (qty 12):True"
    by_name = {case["name"]: case["dspy"] for case in written["parse"]}
    assert by_name["valid"]["parsed"] is True
    assert by_name["no_sections"] == {"parsed": False, "error": "ValueError"}


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
