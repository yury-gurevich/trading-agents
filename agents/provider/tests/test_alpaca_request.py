"""Alpaca bars query builder tests: the SIP end clamp.

Agent: provider
Role: verify the pure page-query builder ends a SIP request at the midnight
after its window, or fifteen minutes before now when that is earlier.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from agents.provider.alpaca_request import SIP_RECENT_DATA_DELAY, bars_page_query
from contracts.common import Window

_WINDOW = Window(start=date(2026, 9, 1), end=date(2026, 9, 28))
_NEXT_PAGE = "next-page"


@pytest.mark.parametrize(
    ("now", "end"),
    [
        (datetime(2026, 10, 2, 12, 0, tzinfo=UTC), "2026-09-29T00:00:00Z"),
        (datetime(2026, 9, 29, 0, 5, tzinfo=UTC), "2026-09-28T23:50:00Z"),
        (datetime(2026, 9, 29, 0, 15, tzinfo=UTC), "2026-09-29T00:00:00Z"),
    ],
)
def test_sip_past_window_ends_at_the_midnight_after_it(now: datetime, end: str) -> None:
    """PROV-OUT-07: a past SIP window ends at the midnight after it - never at
    its own day's 00:00, which drops that day's bar - unless that midnight is
    inside the last 15 minutes, where the clamp wins."""
    query = bars_page_query(("LLY",), _WINDOW, "sip", None, now)
    assert query["end"] == end
    assert query["feed"] == "sip"
    assert "page_token" not in query


def test_sip_end_is_whole_seconds_and_never_later_than_the_wall() -> None:
    """PROV-OUT-07: sub-second time is dropped, never rounded up past the wall."""
    now = datetime(2026, 9, 28, 22, 30, 0, 999_999, tzinfo=UTC)
    query = bars_page_query(("LLY",), _WINDOW, "sip", _NEXT_PAGE, now)
    assert query["end"] == "2026-09-28T22:15:00Z"
    assert query["page_token"] == _NEXT_PAGE
    sent = datetime.fromisoformat(query["end"].replace("Z", "+00:00"))
    assert sent <= now - SIP_RECENT_DATA_DELAY
    assert timedelta(minutes=15) == SIP_RECENT_DATA_DELAY
