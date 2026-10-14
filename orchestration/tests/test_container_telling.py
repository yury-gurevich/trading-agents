"""A18 and A20: retry unsent alarms and retain their replica's why.

Agent: orchestration
Role: prove TOLD edges depend on success and explain only newly recorded alarms.
External I/O: none; injected reader and alarm port only.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from kernel import InMemoryGraphStore
from orchestration.container_sensor import sense_containers
from orchestration.container_sensor_graph import untold_alarms
from orchestration.tests.container_sensor_helpers import (
    MEASURED,
    NOW,
    SETTINGS,
    FakeAlarm,
    FakeReader,
)


def test_a18_unsent_then_raised_then_sent() -> None:
    """DSP-IDM-04 / DSP-FAIL-04: failed sends add no TOLD edge and are retried later."""
    graph = InMemoryGraphStore()
    port = FakeAlarm(sent=False, last_error="telegram_response_invalid")
    reader = FakeReader([MEASURED["killed"]])
    first = sense_containers(graph, reader, port, now=NOW, settings=SETTINGS)
    assert (first.told, first.send_error) == (0, "telegram_response_invalid")
    assert len(untold_alarms(graph, NOW - timedelta(days=7))) == 1
    port.failure = ValueError("synthetic body")
    second = sense_containers(
        graph, reader, port, now=NOW + timedelta(minutes=10), settings=SETTINGS
    )
    assert (second.told, second.send_error) == (0, "ValueError")
    assert all(
        not tuple(graph.descendants(read, max_depth=1, edge_types={"TOLD"}))
        for read in graph.list_nodes("ContainerSensorRead")
    )
    port.failure, port.sent = None, True
    third = sense_containers(
        graph, reader, port, now=NOW + timedelta(minutes=20), settings=SETTINGS
    )
    assert (third.recorded, third.told, third.send_error) == (0, 1, "")
    assert untold_alarms(graph, NOW - timedelta(days=7)) == []
    assert len(port.alarms) == 3
    assert [
        read.props.get("send_error") for read in graph.list_nodes("ContainerSensorRead")
    ] == ["telegram_response_invalid", "ValueError", None]


@pytest.mark.parametrize("error", ["", "refused body", "token=synthetic"])
def test_refused_port_error_is_a_safe_word(error: str) -> None:
    """DSP-FAIL-04 / DSP-SEC-03: an empty or unsafe port error is no message id."""
    outcome = sense_containers(
        InMemoryGraphStore(),
        FakeReader([MEASURED["killed"]]),
        FakeAlarm(sent=False, last_error=error),
        now=NOW,
        settings=SETTINGS,
    )
    assert (outcome.told, outcome.send_error) == (0, "no message id")


def test_a20_replica_line_reaches_graph_and_message() -> None:
    """DSP-IN-05 / DSP-OUT-07: read one replica's window and carry its safe why."""
    graph, port = InMemoryGraphStore(), FakeAlarm()
    exit_row = MEASURED["exit-error"] | {"ReplicaName_s": "provider-abc"}
    lines: list[dict[str, object]] = [
        {
            "TimeGenerated": NOW.isoformat(),
            "ContainerGroupName_s": "provider-abc",
            "Log_s": "ValueError: credential test declaration is required",
        },
        {
            "TimeGenerated": "not a time",
            "ContainerGroupName_s": "provider-abc",
            "Log_s": "ValueError: ignored",
        },
    ]
    reader = FakeReader([exit_row, MEASURED["scaler-failed"]], lines)
    sense_containers(graph, reader, port, now=NOW, settings=SETTINGS)
    assert reader.line_windows == [
        (("provider-abc",), NOW - timedelta(minutes=15), NOW)
    ]
    why = "ValueError: credential test declaration is required"
    assert (
        next(
            node
            for node in graph.list_nodes("ContainerEvent")
            if node.props["app"] == "provider"
        ).props["error_line"]
        == why
    )
    assert f"  why (provider): {why}" in port.alarms[0]
    assert all(
        node.props["error_line"] == ""
        for node in graph.list_nodes("ContainerEvent")
        if node.props["app"] != "provider"
    )


@pytest.mark.parametrize(
    "properties",
    [
        {"ReplicaName_s": ""},
        {"ReplicaName_s": "provider-abc", "time_t": "bad", "TimeGenerated": "bad"},
    ],
)
def test_unexplained_alarm_queries_no_lines(properties: dict[str, object]) -> None:
    """DSP-IN-05 / DSP-OUT-07: a replica-less or undated alarm has no guessed why."""
    graph = InMemoryGraphStore()
    reader = FakeReader([MEASURED["exit-error"] | properties])
    sense_containers(graph, reader, FakeAlarm(), now=NOW, settings=SETTINGS)
    assert reader.line_windows == []
    assert graph.list_nodes("ContainerEvent")[0].props["error_line"] == ""
