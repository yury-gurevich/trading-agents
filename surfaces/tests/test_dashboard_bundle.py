"""Dashboard bundle projection tests — the LLM context bundle (DL-47 req. 11).

Agent: surfaces
Role: verify the bundle aggregates every projection with stable keys.
External I/O: none.
"""

from __future__ import annotations

from typing import Any, cast

import surfaces.dashboard.projections_state as state
from kernel import InMemoryGraphStore
from surfaces.tests.test_dashboard_projections import cascade_graph


def test_bundle_shape_over_real_cascade() -> None:
    graph = cascade_graph("dash-bundle")
    bundle = state.run_bundle(graph, "dash-bundle")
    assert set(bundle) >= {
        "run_id",
        "generated_at",
        "meta",
        "verdict",
        "stages",
        "flags",
        "positions",
        "recovery",
        "logs",
        "images",
    }
    assert cast("dict[str, Any]", bundle["logs"])["available"] is False
    assert cast("dict[str, Any]", bundle["images"])["available"] is False
    meta = cast("dict[str, Any]", bundle["meta"])
    assert meta["ticker_count"] == 2
    assert "dash-bundle" in meta["known_runs"]
    verdict = cast("dict[str, Any]", bundle["verdict"])
    assert verdict["passed"] is True


def test_bundle_meta_for_unknown_run() -> None:
    graph = InMemoryGraphStore()
    bundle = state.run_bundle(graph, "ghost")
    meta = cast("dict[str, Any]", bundle["meta"])
    assert meta["ticker_count"] == 0
    assert meta["requested_at"] == ""
