"""Sprint 286 A1-A4: plans from the synthetic held book.

Agent: forecaster
Role: pin lineage targets, dollar prices, lot ambiguity and stop lifecycle.
External I/O: none.
"""

from agents.forecaster.tests.held_helpers import COP_WIDTH, lineage, position, stop
from kernel import InMemoryGraphStore


def test_a_held_name_carries_its_live_stop_and_declared_target() -> None:
    """FORE-OUT-09: adopted COP reads its exact buy, not its own fallback target."""
    from agents.forecaster.held_plan import held_requests

    graph = InMemoryGraphStore()
    assert held_requests(graph) == ()
    lot = position(graph)
    lineage(graph, lot)
    stop(graph, lot)

    assert held_requests(graph) == (
        (
            "COP",
            {
                "stop_price": 117.08,
                "target_price": round(124.41 * (1 + COP_WIDTH), 4),
                "target_pct": COP_WIDTH,
            },
        ),
    )


def test_a_pm_lineage_position_declares_its_own_target() -> None:
    """FORE-OUT-09: a PM-lineage KO lot declares its own target from entry."""
    from agents.forecaster.held_plan import held_requests

    graph = InMemoryGraphStore()
    lot = position(graph, "KO", entry=8692, adopted=False, target=0.1)
    stop(graph, lot, 8257)

    assert held_requests(graph) == (
        ("KO", {"stop_price": 82.57, "target_price": 95.612, "target_pct": 0.1}),
    )


def test_a_target_the_lineage_does_not_declare_is_left_out() -> None:
    """FORE-OUT-09 / FORE-FAIL-04: absent lineage and multiple lots invent nothing."""
    from agents.forecaster.held_plan import held_requests

    graph = InMemoryGraphStore()
    cop = position(graph)
    stop(graph, cop)
    unh = position(graph, "UNH")
    lineage(graph, unh, None)
    stop(graph, unh)
    mo = position(graph, "MO", key="mo-first")
    lineage(graph, mo)
    position(graph, "MO", key="mo-second")
    position(graph, "META", absent=True)

    assert held_requests(graph) == (
        ("COP", {"stop_price": 117.08}),
        ("MO", {}),
        ("UNH", {"stop_price": 117.08}),
    )
    for target in (True, "0.1", 0.0, -0.1):
        invalid = InMemoryGraphStore()
        lot = position(invalid)
        lineage(invalid, lot, target)
        assert held_requests(invalid) == (("COP", {}),)


def test_the_newest_live_placement_is_the_stop() -> None:
    """FORE-OUT-09: the newest placement owns the stop; ended ones own none."""
    from agents.forecaster.held_plan import held_requests

    graph = InMemoryGraphStore()
    cop = position(graph)
    stop(graph, cop, 11000, ended="replaced_at")
    stop(graph, cop, suffix="#1", placed="2026-10-04T22:30:00+00:00")
    ko = position(graph, "KO")
    stop(graph, ko, ended="cancelled_at")

    assert held_requests(graph) == (("COP", {"stop_price": 117.08}), ("KO", {}))

    late_old = InMemoryGraphStore()
    lot = position(late_old)
    stop(late_old, lot, suffix="#1", placed="2026-10-04T22:30:00+00:00")
    stop(late_old, lot, 11000, ended="replaced_at")
    assert held_requests(late_old) == (("COP", {"stop_price": 117.08}),)
