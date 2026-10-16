"""Position draft quantities from refreshed and legacy fills.

Agent: monitor
Role: prove the draft reads execution's recorded filled size when present.
External I/O: none.
"""

from agents.monitor.domain.positions import position_from_fill
from kernel import InMemoryGraphStore


def test_the_draft_holds_the_filled_quantity_where_the_broker_gave_one() -> None:
    """EXEC-TYP-04: one executed share is one held share; legacy keeps two."""
    graph = InMemoryGraphStore()
    for key, extra, expected in [
        ("partial", {"broker_filled_quantity": 1}, 1),
        ("legacy", {}, 2),
    ]:
        fill = graph.merge_node(
            "Fill",
            key,
            {"ticker": "UNH", "quantity": 2, "price_cents": 40111, **extra},
        )
        draft = position_from_fill(
            graph,
            run_id="run",
            fill=fill,
            default_stop_pct=0.05,
            default_target_pct=0.10,
            default_horizon_days=14,
        )
        assert draft.quantity == expected
