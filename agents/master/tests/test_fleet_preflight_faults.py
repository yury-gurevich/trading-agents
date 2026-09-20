"""Aggregate fleet-preflight fault tests.

Agent: master
Role: prove failed fleet checks emit aggregate critical evidence.
External I/O: none.
"""

from __future__ import annotations

from agents.master.credential_result import credential_failed
from agents.master.credential_test import CredentialTest
from agents.master.tests.test_fleet_preflight import _run_preflight


def test_many_failed_probes_emit_one_fleet_preflight_fault() -> None:
    """MST-OUT-04 / MST-FAIL-05: one failed check emits one aggregate fault."""
    tests = tuple(
        CredentialTest(
            name=f"key-{number}",
            run=lambda _config: credential_failed("unrecoverable:http_402"),
            agent_types=("alpha",),
        )
        for number in range(3)
    )

    graph, sink, result = _run_preflight(tests)

    (node,) = graph.list_nodes("FleetPreflight")
    assert result.passed is False
    assert len(sink.faults) == 1
    assert sink.faults[0].severity == "critical"
    assert "failure_count=3" in sink.faults[0].message
    assert sink.faults[0].context["failures"] == list(node.props["failures"])
