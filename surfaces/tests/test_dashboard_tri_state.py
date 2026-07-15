"""Dashboard warning-class tri-state truth-table tests.

Agent: surfaces
Role: prove unverified is not an outage and behind does not add a light color.
External I/O: none; all read-model inputs are plain mappings.
"""

from __future__ import annotations

from typing import cast

import surfaces.dashboard.projections_verdict as projection
from surfaces.tests.test_dashboard_verdict import _acceptance, _stages, _vitals


def test_unverified_bus_and_deploy_are_warnings_but_unreachable_bus_is_red() -> None:
    vitals = _vitals(fault=False, warning=False)
    vitals["bus"] = {"status": "unverified"}
    vitals["deploy_currency"] = {"status": "unverified"}
    unverified = projection.project_verdict(
        _acceptance("PASS", warning=False), _stages(), vitals, {"escalations": []}
    )
    assert unverified["light"] == "GREEN"
    warnings = cast("list[dict[str, str]]", unverified["warnings"])
    assert {row["code"] for row in warnings} == {
        "bus_unverified",
        "deploy_unverified",
    }
    vitals["bus"] = {"status": "unreachable"}
    unreachable = projection.project_verdict(
        _acceptance("PASS", warning=False), _stages(), vitals, {"escalations": []}
    )
    assert unreachable["light"] == "RED"
    vitals["bus"] = {"status": "reachable"}
    vitals["deploy_currency"] = {"status": "behind"}
    behind = projection.project_verdict(
        _acceptance("PASS", warning=False), _stages(), vitals, {"escalations": []}
    )
    assert behind["warnings"] == [
        {"code": "deploy_behind", "message": "Fleet deploy currency is behind"}
    ]
