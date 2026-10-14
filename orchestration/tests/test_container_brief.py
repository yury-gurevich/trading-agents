"""A22-A23: the brief's container line and its placement.

Agent: orchestration
Role: prove sensor health and recording-age summaries in full and RED briefs.
External I/O: none; the graph and operator port are in memory.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from kernel import InMemoryGraphStore
from orchestration.container_brief import container_line
from orchestration.daily_brief_text import BriefFacts, compose_brief
from orchestration.tests.container_sensor_helpers import NOW, fact
from orchestration.tests.daily_brief_fixtures import at, fire
from orchestration.tests.daily_brief_scenarios import seed_pair
from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram


def test_a22_first_failed_stale_and_quiet_read() -> None:
    """DSP-OUT-08: no line before a read; failed, stale and quiet states say which."""
    graph = InMemoryGraphStore()

    def line() -> str | None:
        return container_line(graph, now=NOW, timezone="UTC")

    assert line() is None
    graph.merge_node("ContainerSensorRead", "invalid", {"read_until": "bad"})
    assert line() is None
    graph.merge_node(
        "ContainerSensorRead",
        "stale",
        {"read_until": (NOW - timedelta(hours=25)).isoformat(), "outcome": "read"},
    )
    assert line() == "Containers: the sensor has not read since Tue 13 Oct 21:30"
    graph.merge_node(
        "ContainerSensorRead",
        "failed",
        {
            "read_until": (NOW - timedelta(minutes=1)).isoformat(),
            "outcome": "failed",
            "error": "ContainerLogReadError (403)",
        },
    )
    assert (
        line()
        == "Containers: the sensor's last read failed (ContainerLogReadError (403)) "
        "at Wed 14 Oct 22:29"
    )
    graph.merge_node(
        "ContainerSensorRead",
        "quiet",
        {"read_until": NOW.isoformat(), "outcome": "read"},
    )
    assert line() == "Containers: no alarm in 24 hours"


def test_a22_recording_window_counts_repeat_peaks() -> None:
    """DSP-OUT-08: count recorded alarms in 24 hours, with repeats and singular
    words.
    """
    graph = InMemoryGraphStore()
    graph.merge_node(
        "ContainerSensorRead",
        "read",
        {"read_until": NOW.isoformat(), "outcome": "read"},
    )
    graph.merge_node(
        "ContainerEvent",
        "old",
        fact("memory-kill", created_at=(NOW - timedelta(hours=25)).isoformat()),
    )
    graph.merge_node("ContainerEvent", "undated", fact("memory-kill", created_at="bad"))
    graph.merge_node("ContainerEvent", "report", fact("preempted", alarm=False))
    assert (
        container_line(graph, now=NOW, timezone="UTC")
        == "Containers: no alarm in 24 hours"
    )
    graph.merge_node("ContainerEvent", "first", fact("memory-kill"))
    assert (
        container_line(graph, now=NOW, timezone="UTC")
        == "Containers: 1 alarm in 24 hours: killed for memory (provider)"
    )
    graph.merge_node("ContainerEvent", "repeat", fact("memory-kill", times=3))
    graph.merge_node("ContainerEvent", "second", fact("scaler-failed", app="master"))
    text = container_line(graph, now=NOW, timezone="UTC")
    assert text is not None
    assert text.startswith("Containers: 4 alarms in 24 hours:")
    assert "killed for memory" in text
    assert "scale rule refused (master)" in text


@pytest.mark.parametrize("verdict", ["PASS", "NOT_FINISHED"])
def test_a23_container_line_is_just_before_needs_you(verdict: str) -> None:
    """DSP-OUT-08: full and RED messages insert one container line before needs-you."""
    line = "Containers: no alarm in 24 hours"
    facts = BriefFacts(
        verdict=verdict, run_id="sched-2026-10-14", stamp="fixture", containers=line
    )
    lines = compose_brief(facts).splitlines()
    assert lines[-2] == line
    assert lines[-1].startswith("Needs you:")
    without = compose_brief(
        BriefFacts(verdict=verdict, run_id=facts.run_id, stamp="fixture")
    )
    assert without == "\n".join(part for part in lines if part != line)


def test_a23_real_brief_facts_include_the_sensor_line() -> None:
    """DSP-OUT-08 / DSP-IDN-05: the public fire carries the new line from graph
    facts.
    """
    graph, port = InMemoryGraphStore(), FakeTelegram()
    seed_pair(graph)
    graph.merge_node(
        "ContainerSensorRead",
        "fixture",
        {"read_until": at(22, 40).isoformat(), "outcome": "read"},
    )
    fire(graph, port, at(22, 50))
    assert port.briefs[0].splitlines()[-2] == "Containers: no alarm in 24 hours"
