"""US equities S&P 500 market pack.

Agent: orchestration
Role: declare the default universe, exchange, and readiness policy.
External I/O: none.
"""

from __future__ import annotations


class USEquitiesSP500Pack:
    """Default paper-stage pack for S&P 500 equities via Stooq."""

    name = "us_equities_sp500"
    exchange = "NYSE/NASDAQ"
    universe_name = "sp500"
    data_source_key = "stooq"
    max_stage = "paper"

    def is_ready(self) -> tuple[bool, str]:
        """Return default paper-stage readiness."""
        return True, "default pack; always ready for paper stage"
