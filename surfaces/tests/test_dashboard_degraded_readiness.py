"""Dashboard degraded-readiness tests for S227.

Agent: surfaces
Role: prove degraded fleet checks render no-new-buys wording instead of holds.
External I/O: reads the static dashboard bundle from the worktree.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, cast

from surfaces.dashboard import build_app
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.test_dashboard_app import invoke
from surfaces.tests.test_dashboard_costs import _settings
from surfaces.tests.test_dashboard_projections import cascade_graph
from surfaces.tests.test_dashboard_readiness import _NOW, _payload

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore


def _degraded_graph() -> InMemoryGraphStore:
    graph = cascade_graph("app-run")
    checked_at = (_NOW - timedelta(minutes=30)).isoformat(timespec="seconds")
    graph.merge_node(
        "FleetPreflight",
        f"preflight:{checked_at}",
        {
            "checked_at": checked_at,
            "passed": False,
            "failures": [
                f"unrecoverable:{agent}:anthropic:unrecoverable:http_400"
                for agent in (
                    "deliberator-manager",
                    "deliberator-opponent",
                    "deliberator-proponent",
                    "operator",
                )
            ],
        },
    )
    return graph


def test_degraded_preflight_says_no_new_buys_without_holding() -> None:
    baseline = _payload(cascade_graph("app-run"))
    payload = _payload(_degraded_graph())

    assert payload["light"] == baseline["light"]
    assert payload["summary"] == baseline["summary"]
    readiness = cast("dict[str, object]", payload["readiness"])
    assert readiness["state"] == "degraded"
    assert readiness["headline"] == (
        "Tonight's run will place no new buys unless the next fleet check passes"
    )
    assert readiness["problems"] == [
        "anthropic answered HTTP 400 — 4 agents can't start: "
        "deliberator-manager, deliberator-opponent, deliberator-proponent, operator"
    ]
    app = build_app(_degraded_graph(), FakeAzureReader(), _settings(), now=_NOW)
    vitals = json.loads(invoke(app, "/api/vitals?run=app-run")[2])
    assert vitals["next_fire_held"] is False
    script = Path("surfaces/dashboard/static/verdict.js").read_text(encoding="utf-8")
    assert "— no new buys" in script
