"""The held-run notice names its deadline in the operator's own time.

Agent: orchestration
Role: prove the act-by text is local-first, DST-aware, and safe without zone data.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime

from kernel import InMemoryGraphStore
from orchestration.scheduled_dispatch_actions import act_by_text
from orchestration.tests.scheduled_dispatch_human_helpers import (
    FakeTelegram,
    dispatch,
    preflight,
)


def test_act_by_reads_melbourne_first_and_follows_daylight_saving() -> None:
    standard = datetime(2026, 9, 24, 22, 30, tzinfo=UTC)
    daylight = datetime(2026, 10, 5, 22, 30, tzinfo=UTC)

    assert act_by_text(standard, "Australia/Melbourne") == "09:20 Melbourne (23:20 UTC)"
    assert act_by_text(daylight, "Australia/Melbourne") == "10:20 Melbourne (23:20 UTC)"


def test_act_by_falls_back_to_utc_without_usable_zone_data() -> None:
    now = datetime(2026, 9, 24, 22, 30, tzinfo=UTC)

    assert act_by_text(now, "Nowhere/Atlantis") == "23:20 UTC"
    assert act_by_text(now, "../etc") == "23:20 UTC"


def test_a_new_hold_notice_carries_the_local_deadline() -> None:
    graph = InMemoryGraphStore()
    preflight(graph, passed=False, failures=("unrecoverable:provider:credential",))
    telegram = FakeTelegram()

    dispatch(graph, telegram)

    assert telegram.sent[0]["act_by"] == "09:20 Melbourne (23:20 UTC)"
