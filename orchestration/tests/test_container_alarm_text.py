"""A21: the alarm's exact text and repeat grouping.

Agent: orchestration
Role: prove the operator-facing message with literal expectations.
External I/O: none.
"""

from __future__ import annotations

from datetime import timedelta

from orchestration.container_alarm_text import TIMES, alarm_message, group_events
from orchestration.tests.container_sensor_helpers import NOW, fact


def test_a21_message_exactly_groups_kinds_across_apps() -> None:
    """DSP-OUT-07: newest kind first, repeat peaks, latest why and Melbourne plus
    UTC.
    """
    facts = [
        fact(
            "exit-error",
            exit_code=1,
            occurred_at=(NOW - timedelta(minutes=10)).isoformat(),
            error_line="ValueError: earlier",
        ),
        fact(
            "killed",
            app="master",
            exit_code=137,
            occurred_at=(NOW - timedelta(minutes=5)).isoformat(),
        ),
        fact(
            "killed",
            exit_code=137,
            times=1,
            occurred_at=(NOW - timedelta(minutes=1)).isoformat(),
            error_line="ValueError: old",
        ),
        fact("killed", exit_code=137, times=2, error_line="HTTPError: latest"),
    ]
    groups = group_events(facts)
    assert len(groups) == 2
    assert (groups[0].kind, groups[0].apps, groups[0].times, groups[0].why_app) == (
        "killed",
        ("master", "provider"),
        3,
        "provider",
    )
    assert alarm_message(groups, timezone="Australia/Melbourne", limit=8) == (
        "Container alarm: 2 apps, 2 kinds of failure\n"
        f"killed (exit code 137) {TIMES}3: master, provider · "
        "Thu 15 Oct 09:30 (22:30 UTC)\n"
        "  why (provider): HTTPError: latest\n"
        "exited with code 1: provider · Thu 15 Oct 09:20 (22:20 UTC)\n"
        "  why (provider): ValueError: earlier"
    )
    assert alarm_message(
        groups, timezone="Missing/Zone", limit=1, capped_hours=168
    ) == (
        "Container alarm: 2 apps, 2 kinds of failure\n"
        f"killed (exit code 137) {TIMES}3: master, provider · Wed 14 Oct 22:30 UTC\n"
        "  why (provider): HTTPError: latest\n"
        "and 1 more kind of failure\n"
        "Read only the last 168 hours; anything earlier is not read."
    )


def test_a21_five_apps_name_four_and_count_the_rest() -> None:
    """DSP-OUT-07: five apps of one kind name the first four and count the fifth."""
    groups = group_events(
        fact("memory-kill", app=app) for app in ("e", "d", "c", "b", "a")
    )
    assert alarm_message(groups, timezone="UTC", limit=8) == (
        "Container alarm: 5 apps, 1 kind of failure\n"
        f"killed for memory {TIMES}5: a, b, c, d and 1 more · "
        "Wed 14 Oct 22:30 (22:30 UTC)"
    )
