"""Resolution-aware flag views — resolved flags stop reading as pending.

Agent: surfaces
Role: prove run_flags and the vitals count honour FlagResolution records.
External I/O: none; graph is in-memory.
"""

from __future__ import annotations

from datetime import date

import surfaces.dashboard.projections_state as state
from kernel import InMemoryGraphStore
from orchestration.start import place_run_request

DAY = date(2026, 7, 9)


def test_resolved_flags_show_on_their_day_and_stop_riding() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="r1", tickers=("AAPL",), as_of=DAY)
    for key, created in (
        ("f-day", f"{DAY.isoformat()}T22:33:00+00:00"),
        ("f-old", "2026-07-01T00:00:00+00:00"),
    ):
        graph.merge_node(
            "Flag",
            key,
            {
                "severity": "critical",
                "reason": "divergence",
                "status": "pending",
                "created_at": created,
                "subject_ref": key,
            },
        )
    for key in ("f-day", "f-old"):
        graph.merge_node(
            "FlagResolution",
            f"res-{key}",
            {"subject_ref": key, "severity": "critical"},
        )

    rows = {r["key"]: r for r in state.run_flags(graph, "r1")}

    assert set(rows) == {"f-day"}
    assert rows["f-day"]["status"] == "resolved"
