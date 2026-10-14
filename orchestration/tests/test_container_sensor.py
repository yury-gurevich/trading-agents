"""A14-A17 and A19: windows, records, telling and row deduplication.

Agent: orchestration
Role: prove overlapping bounded reads and graph facts through the real sensor.
External I/O: none; graph, reader and alarm port are in memory.
"""

from __future__ import annotations

from datetime import timedelta

from kernel import InMemoryGraphStore
from orchestration.container_events import classify
from orchestration.container_sensor import sense_containers
from orchestration.container_sensor_graph import (
    last_read_until,
    read_key,
    untold_alarms,
)
from orchestration.tests.container_sensor_helpers import (
    IGNORED,
    MEASURED,
    NOW,
    SETTINGS,
    FakeAlarm,
    FakeReader,
    row,
)


def test_a14_first_read_then_overlapping_fire() -> None:
    """DSP-TRG-04: first read is 24 hours; next starts ten minutes before its end."""
    graph, reader, port = InMemoryGraphStore(), FakeReader(), FakeAlarm()
    sense_containers(graph, reader, port, now=NOW, settings=SETTINGS)
    sense_containers(
        graph, reader, port, now=NOW + timedelta(minutes=10), settings=SETTINGS
    )
    assert reader.windows == [
        (NOW - timedelta(hours=24), NOW),
        (NOW - timedelta(minutes=10), NOW + timedelta(minutes=10)),
    ]
    assert last_read_until(graph) == NOW + timedelta(minutes=10)
    assert port.alarms == []


def test_a15_long_gap_caps_window_and_message() -> None:
    """DSP-TRG-04 / DSP-OUT-07: a nine-day gap reads only 168 hours and says so."""
    graph, port = InMemoryGraphStore(), FakeAlarm()
    sense_containers(
        graph, FakeReader(), port, now=NOW - timedelta(days=9), settings=SETTINGS
    )
    reader = FakeReader([MEASURED["killed"]])
    result = sense_containers(graph, reader, port, now=NOW, settings=SETTINGS)
    assert reader.windows == [(NOW - timedelta(hours=168), NOW)]
    read = graph.get_node("ContainerSensorRead", result.read_key)
    assert read is not None
    assert read.props["capped"] is True
    assert port.alarms[0].endswith(
        "Read only the last 168 hours; anything earlier is not read."
    )


def test_a16_records_every_kept_row_and_tells_seven_alarms() -> None:
    """DSP-OUT-07 / DSP-OBS-03: twelve rows yield eight events and seven told alarms."""
    graph, port = InMemoryGraphStore(), FakeAlarm()
    result = sense_containers(
        graph,
        FakeReader([*MEASURED.values(), *IGNORED]),
        port,
        now=NOW,
        settings=SETTINGS,
    )
    assert (
        result.rows,
        result.recorded,
        result.alarms,
        result.told,
        result.send_error,
    ) == (12, 8, 7, 7, "")
    read = graph.get_node("ContainerSensorRead", result.read_key)
    assert read is not None
    assert dict(read.props) == {
        "read_from": "2026-10-13T22:30:00+00:00",
        "read_until": NOW.isoformat(),
        "outcome": "read",
        "rows": 12,
        "recorded": 8,
        "alarms": 7,
        "reports": 1,
        "told": 7,
        "capped": False,
        "truncated": False,
        "created_at": NOW.isoformat(),
        "message_id": 301,
    }
    events = graph.list_nodes("ContainerEvent")
    assert len(events) == 8
    assert len(port.alarms) == 1
    assert len(tuple(graph.descendants(read, max_depth=1, edge_types={"TOLD"}))) == 7
    assert all(
        node.props["alarm"] is True
        for node in tuple(graph.descendants(read, max_depth=1, edge_types={"TOLD"}))
    )
    event = classify(MEASURED["killed"])
    assert event is not None
    killed = graph.get_node("ContainerEvent", event.key)
    assert killed is not None
    assert dict(killed.props) == {
        "app": "master",
        "revision": "master--0000174",
        "replica": "",
        "kind": "killed",
        "alarm": True,
        "reason": "Error",
        "message": "Container 'master' was terminated with exit code '137'",
        "times": 1,
        "occurred_at": NOW.isoformat(),
        "error_line": "",
        "read_key": result.read_key,
        "created_at": NOW.isoformat(),
        "exit_code": 137,
    }
    assert untold_alarms(graph, NOW - timedelta(days=7)) == []


def test_a17_same_row_in_two_reads_is_never_remerged() -> None:
    """DSP-IDM-04: duplicates within and across reads keep one original event and
    tell.
    """
    graph, port = InMemoryGraphStore(), FakeAlarm()
    reader = FakeReader([MEASURED["killed"], dict(MEASURED["killed"])])
    first = sense_containers(graph, reader, port, now=NOW, settings=SETTINGS)
    original = dict(graph.list_nodes("ContainerEvent")[0].props)
    second = sense_containers(
        graph, reader, port, now=NOW + timedelta(minutes=10), settings=SETTINGS
    )
    assert (first.recorded, first.told, second.recorded, second.told) == (1, 1, 0, 0)
    assert len(graph.list_nodes("ContainerEvent")) == 1
    assert dict(graph.list_nodes("ContainerEvent")[0].props) == original
    assert len(port.alarms) == 1
    assert (
        len(
            tuple(
                graph.descendants(
                    graph.list_nodes("ContainerSensorRead")[0],
                    max_depth=1,
                    edge_types={"TOLD"},
                )
            )
        )
        == 1
    )


def test_a19_report_only_and_row_limit() -> None:
    """DSP-OUT-07: reports never send; a 5000-row response records its truncation."""
    graph, port = InMemoryGraphStore(), FakeAlarm()
    result = sense_containers(
        graph,
        FakeReader([MEASURED["preempted"]] * 5000),
        port,
        now=NOW,
        settings=SETTINGS,
    )
    assert (result.rows, result.recorded, result.alarms, result.told) == (5000, 1, 0, 0)
    assert port.alarms == []
    read = graph.get_node("ContainerSensorRead", read_key(NOW))
    assert read is not None
    assert (read.props["reports"], read.props["truncated"]) == (1, True)


def test_recording_age_controls_pending_alarms() -> None:
    """DSP-IDM-04: late old events are retried by recording age; expired records
    are not.
    """
    graph, port = InMemoryGraphStore(), FakeAlarm(sent=False)
    ancient = row("OOMKilled", time_t=(NOW - timedelta(days=30)).isoformat())
    sense_containers(graph, FakeReader([ancient]), port, now=NOW, settings=SETTINGS)
    sent = FakeAlarm()
    outcome = sense_containers(
        graph, FakeReader(), sent, now=NOW + timedelta(hours=1), settings=SETTINGS
    )
    assert outcome.told == 1
    assert len(sent.alarms) == 1
    expired = InMemoryGraphStore()
    sense_containers(
        expired,
        FakeReader([ancient]),
        FakeAlarm(sent=False),
        now=NOW - timedelta(days=8),
        settings=SETTINGS,
    )
    assert (
        sense_containers(
            expired, FakeReader(), FakeAlarm(), now=NOW, settings=SETTINGS
        ).told
        == 0
    )
