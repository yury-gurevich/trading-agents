"""Required operator intent parameters and prompt declarations.

Agent: operator
Role: prove missing family requirements are refused before an intent is written.
External I/O: none; canned model replies and an in-memory graph.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from agents.operator.agent import OperatorAgent
from agents.operator.domain import grammar
from agents.operator.domain import result as replies
from agents.operator.domain.prompts import build_interpret_system
from agents.operator.settings import OperatorSettings
from contracts.operator import HumanCommand
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from contracts.operator import CommandResult, IntentFamily


@pytest.mark.parametrize(
    ("family", "parameters", "missing"),
    [
        ("approve", {}, ("target",)),
        ("reject", {}, ("target",)),
        ("modify", {}, ("name", "value")),
        ("modify", {"name": "limit"}, ("value",)),
        ("modify", {"value": "0"}, ("name",)),
        ("mode", {}, ("mode",)),
        ("stage", {}, ("stage",)),
        ("resume", {"run_id": "run-1"}, ("stage",)),
        ("approve", {"target": " \t\n"}, ("target",)),
        ("approve", "not an object", ("target",)),
        ("stage", {"Stage": "paper"}, ("stage",)),
    ],
)
def test_a1_missing_required_parameter_is_refused(
    family: IntentFamily, parameters: object, missing: tuple[str, ...]
) -> None:
    """OPR-FAIL-02: incomplete intents refuse with one audit/call and no intent."""
    result, graph = _interpret(
        {"outcome": "intent", "family": family, "parameters": parameters}
    )
    assert result.outcome == "refused"
    assert result.intent is None
    assert result.message.summary == replies.missing_parameters_reply(family, missing)
    _audit(graph, "refused")
    assert graph.list_nodes("Intent") == ()


@pytest.mark.parametrize(
    ("family", "parameters"),
    [
        ("status", {}),
        ("pause", {}),
        ("explain", {}),
        ("run", {}),
        ("run", "not an object"),
        ("approve", {"target": "flag:case-1"}),
        ("approve", {"subject": "flag:case-1"}),
        ("reject", {"subject": "flag:case-1"}),
        ("modify", {"name": "limit", "value": "0"}),
        ("mode", {"mode": "paper"}),
        ("stage", {"stage": "paper"}),
        ("stage", {"target": "paper"}),
        ("resume", {"stage": "analyst"}),
        ("resume", {"from_stage": "analyst"}),
    ],
)
def test_a2_complete_family_parameters_are_passed_on(
    family: IntentFamily, parameters: object
) -> None:
    """OPR-FAIL-02: accepted names pass unchanged; optional parameters may be absent."""
    result, graph = _interpret(
        {"outcome": "intent", "family": family, "parameters": parameters}
    )
    assert result.outcome == "intent"
    assert result.intent is not None
    assert result.intent.family == family
    assert result.intent.parameters == (
        parameters if isinstance(parameters, dict) else {}
    )
    _audit(graph, "intent")
    assert len(graph.list_nodes("Intent")) == 1


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"family": "bogus", "reason": "model invented reason"},
        {"family": ["status"]},
        {"family": None, "parameters": {"target": "flag:case-1"}},
        {"family": "Status"},
    ],
)
def test_a3_unknown_family_is_refused(data: dict[str, object]) -> None:
    """OPR-FAIL-02: absent, malformed and unknown families use one fixed refusal."""
    result, graph = _interpret({**data, "outcome": "intent"})
    assert result.outcome == "refused"
    assert result.intent is None
    _audit(graph, "refused")
    assert result.message.summary == replies.UNKNOWN_FAMILY_REPLY
    assert graph.list_nodes("Intent") == ()


@pytest.mark.parametrize("outcome", ["refused", "needs_clarification"])
def test_a4_non_intent_reply_is_not_checked(outcome: str) -> None:
    """OPR-FAIL-02: a model refusal or question keeps its own outcome and reason."""
    result, graph = _interpret(
        {"outcome": outcome, "family": "approve", "reason": "which pending item?"}
    )
    assert result.outcome == outcome
    assert result.message.summary == "which pending item?"
    assert result.intent is None
    _audit(graph, outcome)
    assert graph.list_nodes("Intent") == ()


def test_a5_explicit_approve_supplies_target_before_check() -> None:
    """OPR-FAIL-02: the explicit approve grammar fills a model's omitted target."""
    result, graph = _interpret(
        {"outcome": "intent", "family": "approve", "parameters": {}},
        text="approve flag:case-1",
    )
    assert result.outcome == "intent"
    assert result.intent is not None
    assert result.intent.family == "approve"
    assert result.intent.parameters == {"target": "flag:case-1"}
    _audit(graph, "intent")
    assert len(graph.list_nodes("Intent")) == 1


def test_a6_missing_names_and_refusal_sentences_are_pinned() -> None:
    """OPR-FAIL-02: report first accepted names in order and pin both sentences."""
    assert grammar.missing_parameters("modify", {}) == ("name", "value")
    assert grammar.missing_parameters("resume", {"from_stage": " "}) == ("stage",)
    assert (
        grammar.missing_parameters("resume", {"from_stage": "analyst", "stage": ""})
        == ()
    )
    assert replies.UNKNOWN_FAMILY_REPLY == (
        "The model's reply named no command this system has, so nothing was done."
    )
    assert replies.missing_parameters_reply("modify", ("name", "value")) == (
        "The modify command needs its name and value, and the model's "
        "reply gave none, so nothing was done. Say it again and name it."
    )
    assert replies.missing_parameters_reply("approve", ("target",)).startswith(
        "The approve command needs its target, "
    )


def test_a7_grammar_requirements_and_prompt_parameters_are_declared() -> None:
    """OPR-FAIL-02: six families need parameters; the prompt names every parameter."""
    assert {
        name for name, spec in grammar.INTENT_FAMILIES.items() if spec.required
    } == {"approve", "reject", "modify", "mode", "stage", "resume"}
    prompt = build_interpret_system()
    for family, spec in grammar.INTENT_FAMILIES.items():
        assert all(names[0] in spec.params for names in spec.required)
        declaration = f"{family}: {spec.description}"
        if spec.params:
            assert f"{declaration} (parameters: {', '.join(spec.params)})" in prompt
        else:
            assert declaration in prompt
            assert f"{declaration} (" not in prompt
    assert "under exactly the name listed" in prompt
    assert "ask for clarification; never guess it." in prompt


def _interpret(
    data: dict[str, object], *, text: str = "s268-neutral-parameter-probe"
) -> tuple[CommandResult, InMemoryGraphStore]:
    graph = InMemoryGraphStore()
    agent = OperatorAgent(
        InProcessBus(),
        graph=graph,
        llm=FakeLLMClient({text: json.dumps(data)}),
        settings=OperatorSettings(_env_file=None),
    )
    return agent._interpret(
        HumanCommand(text=text, actor="yury", channel="dashboard")
    ), graph


def _audit(graph: InMemoryGraphStore, outcome: str) -> None:
    (audit,) = graph.list_nodes("CommandAudit")
    assert audit.props["outcome"] == outcome
    assert len(graph.list_nodes("LLMCall")) == 1
