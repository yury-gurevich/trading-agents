"""A31-A37: platform failures are alarms with the platform's own safe why.

Agent: orchestration
Role: prove Sprint 278 classification, query, identity and operator wording.
External I/O: none; in-memory graph and injected log/alarm ports only.
"""

from __future__ import annotations

from datetime import timedelta

from kernel import InMemoryGraphStore
from orchestration.container_alarm_text import TIMES, group_events, kind_words
from orchestration.container_events import classify, event_key
from orchestration.container_lines import LINE_LIMIT
from orchestration.container_queries import events_query
from orchestration.container_sensor import sense_containers
from orchestration.tests.container_sensor_helpers import (
    NOW,
    SETTINGS,
    FakeAlarm,
    FakeReader,
    fact,
    row,
)

WEBHOOK = 'failed calling webhook "mapp.kb.io": no endpoints available for service'


def warning(
    reason: str, *, app: str = "provider", **props: object
) -> dict[str, object]:
    """Mark a synthetic row as the measured platform failures are marked."""
    return row(reason, app=app, Type_s="Warning", Level="info") | props


def test_a31_platform_failures_alarm() -> None:
    """DSP-IN-05: named platform failures alarm even without a warning marker."""
    rows = [
        (warning("RevisionFailure", Log_s=WEBHOOK), "revision-failed"),
        (warning("FailedGetScale", Log_s="forbidden"), "autoscaler-failed"),
        (
            warning("FailedUpdateStatus", Log_s="server unable to handle the request"),
            "autoscaler-failed",
        ),
        (row("FailedGetScale", Level="info"), "autoscaler-failed"),
    ]
    for source, kind in rows:
        event = classify(source)
        assert event is not None
        assert (event.kind, event.alarm) == (kind, True)


def test_a32_revision_gone_is_nothing() -> None:
    """DSP-IN-05: only an autoscaler message ending ' not found' is nothing."""
    for reason in ("FailedGetScale", "FailedUpdateStatus"):
        assert classify(warning(reason, Log_s="revision old not found")) is None
        event = classify(warning(reason, Log_s="revision old not found; forbidden"))
        assert event is not None
        assert (event.kind, event.alarm) == ("autoscaler-failed", True)
    revision = classify(warning("RevisionFailure", Log_s="webhook not found"))
    assert revision is not None
    assert (revision.kind, revision.alarm) == ("revision-failed", True)


def test_a33_measured_warnings_are_nothing() -> None:
    """DSP-IN-05: the five measured deploy/wake by-products are nothing."""
    for reason in (
        "AssigningReplicaFailed",
        "Completed",
        "ReplicaUnhealthy",
        "ScaledObjectCheckFailed",
        "ScaledObjectDeleted",
    ):
        assert classify(warning(reason)) is None


def test_a34_unknown_warning_alarms_and_unmarked_unknown_does_not() -> None:
    """DSP-IN-05: catch unknown warnings without overriding known row meanings."""
    event = classify(warning("FailedMount"))
    assert event is not None
    assert (event.kind, event.reason, event.alarm) == (
        "platform-warning",
        "FailedMount",
        True,
    )
    assert classify(row("FailedMount", Type_s="Normal", Level="info")) is None
    assert classify(row("FailedMount", Level="info")) is None
    moved = classify(warning("ScaleDown"))
    assert moved is not None
    assert (moved.kind, moved.alarm) == ("preempted", False)
    assert classify(warning("Error", Log_s="terminated with exit code '0'")) is None


def test_a35_query_asks_for_unknown_warnings_not_measured_ones() -> None:
    """DSP-IN-05 / DSP-IDM-04: query warnings, but never key the marker."""
    query = events_query(NOW - timedelta(hours=1), NOW)
    assert (
        "or (Type_s == 'Warning' and Reason_s !in ('AssigningReplicaFailed', "
        "'Completed', 'ReplicaUnhealthy', 'ScaledObjectCheckFailed', "
        "'ScaledObjectDeleted'))"
    ) in query
    assert "Reason_s, Type_s, Level," in query
    source = row("FailedMount", Level="info")
    assert event_key(source) == event_key(source | {"Type_s": "Warning"})


def test_a36_platform_why_is_its_own_words() -> None:
    """DSP-IN-05 / DSP-OUT-07: store safe platform words and tell the latest why."""
    graph, port = InMemoryGraphStore(), FakeAlarm()
    reader = FakeReader(
        [
            warning(
                "RevisionFailure",
                app="analyst",
                Log_s="webhook unavailable",
                time_t=(NOW - timedelta(minutes=2)).isoformat(),
            ),
            warning(
                "RevisionFailure",
                Log_s=WEBHOOK + " webhook unavailable" * 40,
                time_t=(NOW - timedelta(minutes=1)).isoformat(),
            ),
            warning("FailedGetScale", app="master", Log_s="forbidden token=abc123"),
            row("Error", app="scanner", Log_s="terminated with exit code '1'"),
        ]
    )
    result = sense_containers(graph, reader, port, now=NOW, settings=SETTINGS)
    assert (result.recorded, result.alarms, result.told) == (4, 4, 4)
    whys = {
        str(node.props["app"]): str(node.props["error_line"])
        for node in graph.list_nodes("ContainerEvent")
    }
    assert whys["analyst"] == "RevisionFailure: webhook unavailable"
    assert whys["provider"].startswith(f"RevisionFailure: {WEBHOOK}")
    assert len(whys["provider"]) == LINE_LIMIT
    assert whys["provider"].endswith("…")
    assert whys["master"] == "FailedGetScale: forbidden token=***"
    assert whys["scanner"] == ""
    assert reader.line_windows == []
    (message,) = port.alarms
    assert f"revision update failed {TIMES}2: analyst, provider · " in message
    assert f"  why (provider): {whys['provider']}" in message
    assert "  why (analyst):" not in message
    assert "the platform's autoscaler failed: master · " in message
    assert "  why (master): FailedGetScale: forbidden token=***" in message
    assert "abc123" not in message


def test_a37_platform_kinds_in_the_operators_words() -> None:
    """DSP-OUT-07: say whose failure each of the three platform kinds is."""
    for kind, words in (
        ("revision-failed", "revision update failed"),
        ("autoscaler-failed", "the platform's autoscaler failed"),
        ("platform-warning", "platform warning"),
    ):
        (group,) = group_events([fact(kind)])
        assert kind_words(group) == words
