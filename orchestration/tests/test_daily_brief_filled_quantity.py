"""Daily brief fill sizes for partial and legacy executions.

Agent: orchestration
Role: prove a fill line reports shares executed from stored evidence.
External I/O: none.
"""

from datetime import UTC, datetime

from kernel import InMemoryGraphStore
from orchestration.daily_brief_fills import fills_between


def test_a_fill_line_counts_the_shares_the_broker_filled() -> None:
    """DSP-OUT-06 / EXEC-TYP-04: the brief reads filled size, else legacy size."""
    graph = InMemoryGraphStore()
    for key, extra, expected in [
        ("partial", {"broker_filled_quantity": 1}, 1),
        ("legacy", {}, 2),
    ]:
        fill = graph.merge_node(
            "Fill",
            key,
            {
                "ticker": "UNH",
                "side": "buy",
                "quantity": 2,
                "broker_status": "filled",
                "broker_price_cents": 40111,
                "broker_status_refreshed_at": "2026-10-15T22:32:00+00:00",
                **extra,
            },
        )
        lines = fills_between(
            (fill,),
            datetime(2026, 10, 14, tzinfo=UTC),
            datetime(2026, 10, 16, tzinfo=UTC),
        )
        assert len(lines) == 1
        assert lines[0].quantity == expected
