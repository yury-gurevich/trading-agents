"""Alpaca daily-bars page query, built whole and pure.

Agent: provider
Role: build the exact query one Alpaca bars page request sends, including the
end rule that keeps a SIP request out of the plan's recent-data window
(PROV-OUT-07, DL-239). The caller supplies the time; nothing here reads a clock.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.common import Window

SIP_FEED = "sip"
# Alpaca's market-data plan refuses a SIP request whose end falls inside the
# most recent 15 minutes (measured 403 "subscription does not permit querying
# recent SIP data", DL-233 amendment). The entitlement is Alpaca's, not a policy
# of ours, so this is a named constant and never a tunable or settings field.
SIP_RECENT_DATA_DELAY = timedelta(minutes=15)
# The wall is exact: an end 900 s back is served and 899 s is refused (measured
# 2026-09-28, three of three each). Sending exactly 900 s leaves only the clocks'
# agreement as headroom, so a host a second ahead would lose every SIP fetch.
SIP_CLOCK_MARGIN = timedelta(minutes=1)
_TIMEFRAME = "1Day"
_PAGE_LIMIT = "10000"  # Alpaca's maximum bars per page.


def bars_page_query(
    tickers: tuple[str, ...],
    window: Window,
    feed: str,
    page_token: str | None,
    now: datetime,
) -> dict[str, str]:
    """Return the query one bars page request sends, in the order it is sent.

    ``now`` is an aware UTC time. A SIP ``end`` is RFC 3339 with ``Z``; any other
    feed sends ``window.end`` as a bare date, exactly as the source always did.
    """
    query = {
        "symbols": ",".join(tickers),
        "timeframe": _TIMEFRAME,
        "start": window.start.isoformat(),
        "end": _end(window, feed, now),
        "feed": feed,
        "limit": _PAGE_LIMIT,
    }
    if page_token:
        query["page_token"] = page_token
    return query


def _end(window: Window, feed: str, now: datetime) -> str:
    """End a SIP request at the midnight after the window, or clear of the wall.

    Midnight *after* ``window.end``, never ``window.end`` at 00:00: daily bars are
    stamped 04:00Z or 05:00Z, so an end at the window day's midnight drops that
    day's bar. Seconds are truncated, never rounded up past the wall.
    """
    if feed != SIP_FEED:
        return window.end.isoformat()
    after_window = datetime.combine(window.end + timedelta(days=1), time(), UTC)
    wall = now.astimezone(UTC) - SIP_RECENT_DATA_DELAY - SIP_CLOCK_MARGIN
    end = min(after_window, wall)
    return end.strftime("%Y-%m-%dT%H:%M:%SZ")
