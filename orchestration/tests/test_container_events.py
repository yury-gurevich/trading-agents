"""A1-A7: platform rows become the specified events or nothing.

Agent: orchestration
Role: prove classification, row identity, repeats and the ingestion-time query.
External I/O: none.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from orchestration.container_events import SENSED_REASONS, classify, event_key
from orchestration.container_queries import events_query
from orchestration.tests.container_sensor_helpers import IGNORED, MEASURED, NOW, row


@pytest.mark.parametrize(
    ("name", "kind", "app", "code", "alarm"),
    [
        ("exit-error", "exit-error", "provider", 1, True),
        ("killed", "killed", "master", 137, True),
        ("memory-kill", "memory-kill", "analyst", None, True),
        ("start-failed", "start-failed", "scanner", None, True),
        ("scale-up-failed", "start-failed", "forecaster", None, True),
        ("scaler-failed", "scaler-failed", "dispatcher-cron", None, True),
        ("provision-failed", "provision-failed", "researcher", None, True),
        ("preempted", "preempted", "reporter", None, False),
    ],
)
def test_a1_measured_kinds(
    name: str, kind: str, app: str, code: int | None, alarm: bool
) -> None:
    """DSP-IN-05: every measured kind retains its app, exit code and alarm status."""
    event = classify(MEASURED[name])
    assert event is not None
    assert (event.kind, event.app, event.exit_code, event.alarm) == (
        kind,
        app,
        code,
        alarm,
    )


@pytest.mark.parametrize("platform_row", IGNORED)
def test_a2_noise_and_clean_exit_are_nothing(platform_row: dict[str, object]) -> None:
    """DSP-IN-05: readiness noise, stopping and an exit with zero are ignored."""
    assert classify(platform_row) is None


@pytest.mark.parametrize(
    ("platform_row", "kind"),
    [
        (row("NewReason", Level="Error"), "platform-error"),
        (row("Error", Log_s="exit unreadable"), "exit-error"),
    ],
)
def test_a3_unknown_error_and_unreadable_exit(
    platform_row: dict[str, object], kind: str
) -> None:
    """DSP-IN-05: unknown platform errors and unreadable exit codes still alarm."""
    event = classify(platform_row)
    assert event is not None
    assert (event.kind, event.exit_code, event.alarm) == (kind, None, True)


@pytest.mark.parametrize(
    ("platform_row", "app"),
    [
        (row("OOMKilled", app="", JobName_s="dispatcher-cron"), "dispatcher-cron"),
        (row("OOMKilled", app="", RevisionName_s=None), "unknown"),
        (row("ScaleDown", app="monitor", JobName_s="ignored"), "monitor"),
    ],
)
def test_a4_app_precedence_and_unknown(
    platform_row: dict[str, object], app: str
) -> None:
    """DSP-IN-05: app precedes job and revision, and no name is explicitly unknown."""
    event = classify(platform_row)
    assert event is not None
    assert event.app == app
    if platform_row["Reason_s"] == "ScaleDown":
        assert (event.kind, event.alarm) == ("preempted", False)


@pytest.mark.parametrize(
    ("count", "expected"),
    [(12.0, 12), ("3", 3), (None, 1), (0.0, 1), ("x", 1), (float("inf"), 1)],
)
def test_a5_repeat_count(count: object, expected: int) -> None:
    """DSP-OUT-07: missing or unusable repeat counts conservatively become one."""
    event = classify(row("OOMKilled", Count_d=count))
    assert event is not None
    assert event.times == expected


def test_a6_key_is_the_row_and_message_is_bounded() -> None:
    """DSP-IDM-04: identical rows share a digest; a changed count is a new row."""
    original = row("OOMKilled", Log_s="word " * 100)
    event = classify(original)
    assert event is not None
    assert event.key == event_key(dict(original))
    assert event.key != event_key(original | {"Count_d": 2.0})
    assert event.message == str(original["Log_s"])[:300]
    assert event.occurred_at == NOW.isoformat()
    fallback = classify(original | {"time_t": None, "TimeGenerated": 7})
    assert fallback is not None
    assert fallback.occurred_at == "7"


def test_a7_query_matches_classifier_and_ingestion_window() -> None:
    """DSP-IN-05: the query selects every sensed reason and errors by ingestion time."""
    query = events_query(NOW - timedelta(hours=24), NOW)
    assert all(f"'{reason}'" in query for reason in SENSED_REASONS)
    assert "Level =~ 'error'" in query
    assert (
        "| where ingestion_time() > datetime(2026-10-13T22:30:00.000000Z) "
        "and ingestion_time() <= datetime(2026-10-14T22:30:00.000000Z)" in query
    )
    assert "| order by TimeGenerated asc\n| take 5000" in query
