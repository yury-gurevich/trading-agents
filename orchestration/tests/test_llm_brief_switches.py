"""A19-A22: the brief carries activation choices before the run's switches.

Agent: orchestration
Role: prove exact switch text and real-fire forwarding with no network.
External I/O: none.
"""

import pytest

from kernel import InMemoryGraphStore
from orchestration.llm_brief import llm_line
from orchestration.tests.daily_brief_fixtures import at, fire
from orchestration.tests.daily_brief_scenarios import seed_pair
from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram

FIRST = "openai/gpt-5.5/high"
SECOND = "anthropic/claude-opus-5/max"
SWITCH = (
    f"deliberator-opponent switched to claude-opus-5 (passed over {FIRST}: http_429)"
)
OTHER = f"deliberator-manager switched to claude-opus-5 (passed over {FIRST}: http_400)"
NOW = at(22, 50)


def test_a19_brief_names_each_switch_in_run_order() -> None:
    """DSP-OUT-09: each switch is followed by during-the-run wording in row order."""
    graph = InMemoryGraphStore()
    run = graph.merge_node(
        "DeliberationRun", "switches", {"llm_switches": [SWITCH, OTHER]}
    )
    assert llm_line(graph, now=NOW, deliberation=run) == (
        f"LLM: {SWITCH} during the run · {OTHER} during the run"
    )


def test_a20_activation_parts_precede_run_switches() -> None:
    """DSP-OUT-09: activation parts lead; without the run they remain unchanged."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "AgentInstance",
        "activation",
        {
            "agent_type": "deliberator-proponent",
            "started_at": NOW.isoformat(),
            "llm_candidate": SECOND,
            "llm_passed_over": [f"{FIRST}: unrecoverable:http_429"],
        },
    )
    run = graph.merge_node("DeliberationRun", "run", {"llm_switches": [SWITCH]})
    activation = (
        f"LLM: deliberator-proponent on {SECOND} "
        f"(passed over {FIRST}: unrecoverable:http_429)"
    )
    assert (
        llm_line(graph, now=NOW, deliberation=run)
        == f"{activation} · {SWITCH} during the run"
    )
    assert llm_line(graph, now=NOW) == activation


@pytest.mark.parametrize("switches", [[], (), None, "wrong shape"])
def test_a21_no_switch_means_no_line(switches: object) -> None:
    """DSP-OUT-09: absent, empty and malformed switches produce no LLM line."""
    graph = InMemoryGraphStore()
    run = graph.merge_node("DeliberationRun", "quiet", {"llm_switches": switches})
    assert llm_line(graph, now=NOW, deliberation=run) is None
    assert llm_line(graph, now=NOW) is None


def test_a22_real_fire_carries_the_runs_switch() -> None:
    """DSP-OUT-09: the public fire reads the run's switch into the sent brief."""
    graph, telegram = InMemoryGraphStore(), FakeTelegram()
    seed_pair(graph)
    for run in graph.list_nodes("DeliberationRun"):
        graph.merge_node("DeliberationRun", run.key, {"llm_switches": [SWITCH]})
    fire(graph, telegram, NOW)
    assert len(telegram.briefs) == 1
    assert telegram.briefs[0].splitlines()[-2] == f"LLM: {SWITCH} during the run"
