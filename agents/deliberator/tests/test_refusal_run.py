"""A10-A11: real review records and readers disclose the run's switches.

Agent: deliberator
Role: exercise two rounds over the bus and empty, repeated or malformed metadata.
External I/O: none.
"""

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.peer_client import BusPeerClient
from agents.deliberator.poll import review_pm_node
from agents.deliberator.review_record import llm_switches
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.tests.refusal_testkit import (
    FIRST,
    SWITCH,
    Client,
    StatusError,
    chain,
)
from agents.deliberator.tests.test_deliberator_agent import _pm_node
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus, Node


def review(*, refused: bool) -> tuple[InMemoryGraphStore, Node]:
    """Run two peer rounds and a judge on an order with a possible refusal."""
    graph, bus = InMemoryGraphStore(), InProcessBus()
    pm = _pm_node(graph)
    opponent = (
        chain(Client(StatusError(429)), Client("evidence challenge"))
        if refused
        else Client("evidence challenge")
    )
    DeliberatorAgent(
        bus,
        graph=graph,
        llm=FakeLLMClient({"DECISION UNDER TEST": "evidence defense"}),
        settings=DeliberatorSettings(
            _env_file=None, role="proponent", llm_provider="openai"
        ),
    ).bind()
    DeliberatorAgent(
        bus,
        graph=graph,
        llm=opponent,
        settings=DeliberatorSettings(
            _env_file=None, role="opponent", llm_provider="openai"
        ),
    ).bind()
    settings = DeliberatorSettings(
        _env_file=None, role="manager", llm_provider="openai"
    )
    manager = DeliberatorAgent(
        bus,
        graph=graph,
        settings=settings,
        llm=FakeLLMClient(
            {"DECISION UNDER TEST": '{"ruling":"uphold","rationale":"clears"}'}
        ),
    )
    review_pm_node(
        pm,
        graph=graph,
        manager=manager,
        peer_client=BusPeerClient(bus, sender=settings.identity),
        settings=settings,
    )
    (run,) = graph.list_nodes("DeliberationRun")
    return graph, run


def test_a10_real_review_records_answered_model_and_switch() -> None:
    """DLIB-OUT-02 / DLIB-FAIL-05: a refused turn is answered, audited and upheld."""
    graph, run = review(refused=True)
    assert run.props["failed_open_count"] == 0
    assert run.props["real_debate_count"] == 1
    assert run.props["role_models"]["challenger"] == "claude-opus-5"
    assert list(run.props["llm_switches"]) == [SWITCH]
    rows = [
        row
        for row in graph.list_nodes("LLMCall")
        if row.props["calling_agent"] == "deliberator-opponent"
    ]
    assert len(rows) == 3
    assert [row.props["model"] for row in rows] == [
        "gpt-5.5",
        "claude-opus-5",
        "claude-opus-5",
    ]
    assert rows[0].props["stop_reason"] == "unknown"
    assert list(rows[1].props["llm_passed_over"]) == [f"{FIRST}: http_429"]
    assert "llm_passed_over" not in rows[2].props


def test_a11_run_always_writes_empty_switches() -> None:
    """DLIB-OUT-02: a quiet real run writes an explicit empty switch list."""
    _, run = review(refused=False)
    assert run.props["failed_open_count"] == 0
    assert list(run.props["llm_switches"]) == []


def test_a11_switch_reader_skips_bad_rows_and_deduplicates_in_row_order() -> None:
    """DLIB-OUT-02: tuple-backed refusals read once, in the run's supplied order."""
    graph = InMemoryGraphStore()
    for key, props in (
        ("absent", {}),
        ("empty", {"llm_passed_over": []}),
        ("scalar", {"llm_passed_over": "wrong shape"}),
    ):
        graph.merge_node("LLMCall", key, props)
    quiet = ["missing", "absent", "empty", "scalar"]
    assert llm_switches(graph, quiet) == []
    assert llm_switches(None, quiet) == []
    switch_props = {
        "calling_agent": "deliberator-opponent",
        "model": "claude-opus-5",
        "llm_passed_over": [f"{FIRST}: http_429"],
    }
    graph.merge_node("LLMCall", "a", switch_props)
    graph.merge_node("LLMCall", "duplicate", switch_props)
    graph.merge_node(
        "LLMCall",
        "b",
        {
            "calling_agent": "deliberator-manager",
            "model": "other",
            "llm_passed_over": ["first: http_400", "second: http_503"],
        },
    )
    other = (
        "deliberator-manager switched to other "
        "(passed over first: http_400; second: http_503)"
    )
    assert llm_switches(graph, ["b", *quiet, "a", "duplicate"]) == [other, SWITCH]
