"""A21-A24: the brief discloses a recent passed-over LLM candidate.

Agent: orchestration
Role: prove quiet, grouped, time-bounded wording and real-fire integration.
External I/O: none; in-memory graph and injected operator port.
"""

from datetime import timedelta

import pytest

from kernel import InMemoryGraphStore
from orchestration.daily_brief_text import BriefFacts, compose_brief
from orchestration.llm_brief import llm_line
from orchestration.tests.daily_brief_fixtures import at, fire
from orchestration.tests.daily_brief_scenarios import seed_pair
from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram

FIRST = "openai/gpt-5.5/high"
SECOND = "anthropic/claude-opus-5/max"
OVER = f"{FIRST}: unrecoverable:http_429"
NOW = at(22, 50)


def activation(
    graph: InMemoryGraphStore, key: str, agent_type: str, **props: object
) -> None:
    graph.merge_node(
        "AgentInstance",
        key,
        {
            "agent_type": agent_type,
            "started_at": NOW.isoformat(),
            "llm_candidate": SECOND,
            "llm_passed_over": [OVER],
            **props,
        },
    )


def test_a21_quiet_night_has_no_llm_line() -> None:
    """DSP-OUT-09: absent, empty and non-LLM activations stay silent."""
    graph = InMemoryGraphStore()
    graph.merge_node("AgentInstance", "legacy", {"agent_type": "deliberator-manager"})
    activation(graph, "quiet", "deliberator-opponent", llm_passed_over=[])
    graph.merge_node(
        "AgentInstance",
        "scanner",
        {"agent_type": "scanner", "started_at": NOW.isoformat()},
    )
    assert llm_line(graph, now=NOW) is None


def test_a22_llm_line_groups_replicas_and_filters_old_or_undated() -> None:
    """DSP-OUT-09 / DSP-DEP-01: tuple-backed lists, sorted groups and the last 24h."""
    graph = InMemoryGraphStore()
    activation(graph, "opponent-1", "deliberator-opponent")
    activation(graph, "opponent-2", "deliberator-opponent")
    activation(graph, "manager", "deliberator-manager")
    activation(
        graph, "old", "old-role", started_at=(NOW - timedelta(hours=25)).isoformat()
    )
    activation(graph, "undated", "undated-role", started_at=None)
    expected = (
        f"LLM: deliberator-manager, deliberator-opponent on {SECOND} "
        f"(passed over {OVER})"
    )
    assert llm_line(graph, now=NOW) == expected
    activation(
        graph,
        "second-choice",
        "deliberator-proponent",
        llm_candidate=FIRST,
        llm_passed_over=[f"{SECOND}: http_503", "another: TimeoutError"],
    )
    assert llm_line(graph, now=NOW) == (
        expected + f" · deliberator-proponent on {FIRST} "
        f"(passed over {SECOND}: http_503; another: TimeoutError)"
    )
    boundary = InMemoryGraphStore()
    activation(
        boundary, "boundary", "role", started_at=(NOW - timedelta(hours=24)).isoformat()
    )
    assert llm_line(boundary, now=NOW) == f"LLM: role on {SECOND} (passed over {OVER})"


@pytest.mark.parametrize("verdict", ["PASS", "NOT_FINISHED"])
def test_a23_llm_line_follows_container_before_needs_you(verdict: str) -> None:
    """DSP-OUT-09: full and RED briefs put containers, LLM, then needs-you."""
    facts = BriefFacts(
        verdict=verdict,
        run_id="fixture",
        stamp="fixture",
        containers="Containers: no alarm in 24 hours",
        llm="LLM: fixture choice",
    )
    lines = compose_brief(facts).splitlines()
    assert lines[-3:-1] == [facts.containers, facts.llm]
    assert lines[-1].startswith("Needs you:")


def test_a24_real_fire_carries_the_candidate_line() -> None:
    """DSP-OUT-09 / DSP-DEP-01: the public fire reads the activation into its brief."""
    graph, telegram = InMemoryGraphStore(), FakeTelegram()
    seed_pair(graph)
    activation(graph, "manager", "deliberator-manager")
    fire(graph, telegram, NOW)
    assert len(telegram.briefs) == 1
    assert telegram.briefs[0].splitlines()[-2] == (
        f"LLM: deliberator-manager on {SECOND} (passed over {OVER})"
    )
