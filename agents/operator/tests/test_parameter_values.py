"""Operator parameter values through interpretation and graph storage.

Agent: operator
Role: prove non-values are omitted while scalar and blank text behavior stays.
External I/O: none; canned model replies and an in-memory graph.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from agents.operator.agent import OperatorAgent
from agents.operator.domain.result import missing_parameters_reply
from agents.operator.settings import OperatorSettings
from contracts.operator import HumanCommand
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from contracts.operator import CommandResult, IntentFamily


@pytest.mark.parametrize(
    ("family", "parameters", "missing"),
    [
        ("approve", {"target": None}, ("target",)),
        ("approve", {"target": []}, ("target",)),
        ("approve", {"target": {}}, ("target",)),
        ("approve", {"target": ["flag:case-1"]}, ("target",)),
        ("approve", {"target": {"id": "flag:case-1"}}, ("target",)),
        ("reject", {"target": None, "subject": None}, ("target",)),
        ("modify", {"name": "limit", "value": None}, ("value",)),
        ("modify", {"name": None, "value": 8}, ("name",)),
        ("mode", {"mode": None}, ("mode",)),
        ("stage", {"stage": None, "target": []}, ("stage",)),
        ("resume", {"stage": None, "run_id": "run-1"}, ("stage",)),
    ],
    ids=[
        "approve-null",
        "approve-empty-list",
        "approve-empty-object",
        "approve-list",
        "approve-object",
        "reject-null-aliases",
        "modify-null-value",
        "modify-null-name",
        "mode-null",
        "stage-nonvalue-aliases",
        "resume-null-stage",
    ],
)
def test_b1_required_parameter_without_value_is_refused(
    family: IntentFamily, parameters: dict[str, object], missing: tuple[str, ...]
) -> None:
    """OPR-FAIL-02: required non-values refuse with the existing sentence and audit."""
    result, graph = _interpret(family, parameters)
    _assert_refused(result, graph, family, missing)


@pytest.mark.parametrize(
    ("family", "parameters", "expected"),
    [
        (
            "approve",
            {"target": None, "subject": "flag:case-1"},
            {"subject": "flag:case-1"},
        ),
        (
            "approve",
            {"subject": [], "target": "flag:case-1"},
            {"target": "flag:case-1"},
        ),
        ("stage", {"stage": None, "target": "paper"}, {"target": "paper"}),
        ("resume", {"stage": {}, "from_stage": "analyst"}, {"from_stage": "analyst"}),
        ("explain", {"subject": None}, {}),
        ("run", {"stage": None}, {}),
        ("run", {"stage": ["live"]}, {}),
        ("status", {"unknown_null": None, "unknown_object": {"id": "case-1"}}, {}),
    ],
    ids=[
        "approve-keeps-subject",
        "approve-keeps-target",
        "stage-keeps-target",
        "resume-keeps-from-stage",
        "explain-null-subject",
        "run-null-stage",
        "run-list-stage",
        "status-unknown-nonvalues",
    ],
)
def test_b2_parameter_without_value_is_omitted(
    family: IntentFamily, parameters: dict[str, object], expected: dict[str, str]
) -> None:
    """OPR-FAIL-02: required aliases and optional parameters omit non-values."""
    result, graph = _interpret(family, parameters)
    _assert_intent(result, graph, family, expected)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("8", "8"), (8, "8"), (0, "0"), (0.5, "0.5"), (False, "False"), (True, "True")],
    ids=["text", "integer", "zero", "float", "false", "true"],
)
def test_b3_scalar_parameter_is_kept(value: object, expected: str) -> None:
    """OPR-FAIL-02: text, numbers and booleans retain their existing Python text."""
    result, graph = _interpret("modify", {"name": "limit", "value": value})
    _assert_intent(result, graph, "modify", {"name": "limit", "value": expected})


def test_b4_blank_text_keeps_existing_behavior() -> None:
    """OPR-FAIL-02: required blank text refuses; optional empty text is carried."""
    result, graph = _interpret("approve", {"target": " \t\n"})
    _assert_refused(result, graph, "approve", ("target",))
    result, graph = _interpret("run", {"stage": ""})
    _assert_intent(result, graph, "run", {"stage": ""})


def _interpret(
    family: IntentFamily, parameters: dict[str, object]
) -> tuple[CommandResult, InMemoryGraphStore]:
    text = "s269-neutral-parameter-probe"
    graph = InMemoryGraphStore()
    agent = OperatorAgent(
        InProcessBus(),
        graph=graph,
        llm=FakeLLMClient(
            {
                text: json.dumps(
                    {"outcome": "intent", "family": family, "parameters": parameters}
                )
            }
        ),
        settings=OperatorSettings(_env_file=None),
    )
    return agent._interpret(
        HumanCommand(text=text, actor="yury", channel="dashboard")
    ), graph


def _assert_refused(
    result: CommandResult,
    graph: InMemoryGraphStore,
    family: IntentFamily,
    missing: tuple[str, ...],
) -> None:
    assert result.outcome == "refused"
    assert result.intent is None
    assert result.message.summary == missing_parameters_reply(family, missing)
    _audit(graph, "refused")
    assert graph.list_nodes("Intent") == ()


def _assert_intent(
    result: CommandResult,
    graph: InMemoryGraphStore,
    family: IntentFamily,
    expected: dict[str, str],
) -> None:
    assert result.outcome == "intent"
    assert result.intent is not None
    assert result.intent.family == family
    assert result.intent.parameters == expected
    _audit(graph, "intent")
    (stored,) = graph.list_nodes("Intent")
    assert json.loads(str(stored.props["parameters"])) == expected


def _audit(graph: InMemoryGraphStore, outcome: str) -> None:
    (audit,) = graph.list_nodes("CommandAudit")
    assert audit.props["outcome"] == outcome
    assert len(graph.list_nodes("LLMCall")) == 1
