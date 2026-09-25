"""S227 degraded-readiness scheduled dispatcher tests.

Agent: orchestration
Role: prove only fresh pack-declared LLM outages place degraded runs.
External I/O: none.
"""

from __future__ import annotations

from datetime import timedelta
from importlib import import_module
from typing import TYPE_CHECKING

from agents.scanner.universe import FakeUniverse
from contracts.provider import RUN_REQUEST_LABEL
from kernel import InMemoryGraphStore
from orchestration.fleet_readiness import is_active_run_hold
from orchestration.scheduled_dispatch import place_scheduled_run
from orchestration.tests.test_scheduled_dispatch_readiness import (
    _AS_OF,
    _NOW,
    _place,
    _preflight,
)

if TYPE_CHECKING:
    import pytest

_LLM_ONLY_FAILURES = (
    "unrecoverable:deliberator-manager:anthropic:unrecoverable:http_400",
    "unrecoverable:deliberator-opponent:anthropic:unrecoverable:http_400",
    "unrecoverable:deliberator-proponent:anthropic:unrecoverable:http_400",
    "unrecoverable:operator:anthropic:unrecoverable:http_400",
)


def test_llm_only_failing_check_places_degraded_run_and_releases_hold() -> None:
    """MST-OUT-04/MST-FAIL-05/DSP-IN-03/DSP-OUT-04: LLM-only outage degrades."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "RunHold",
        "hold:sched-2026-07-08",
        {
            "run_id": "sched-2026-07-08",
            "as_of": _AS_OF.isoformat(),
            "held_at": (_NOW - timedelta(minutes=30)).isoformat(timespec="seconds"),
            "state": "held",
            "readiness_state": "failing",
            "failures": ["old"],
        },
    )
    _preflight(
        graph,
        checked_at=_NOW - timedelta(minutes=5),
        passed=False,
        failures=_LLM_ONLY_FAILURES,
    )

    result = _place(graph)

    assert result.action == "placed"
    assert result.failures == _LLM_ONLY_FAILURES
    run = graph.get_node(RUN_REQUEST_LABEL, "run-request:sched-2026-07-08")
    assert run is not None
    assert run.props["run_posture"] == "degraded"
    assert tuple(run.props["degraded_by"]) == _LLM_ONLY_FAILURES
    (hold,) = graph.list_nodes("RunHold")
    assert "released_at" in hold.props
    assert is_active_run_hold(hold) is False


def test_non_degradable_failure_keeps_llm_outage_held() -> None:
    """MST-FAIL-05 / DSP-IN-03: one undeclared failure is still a hard hold."""
    graph = InMemoryGraphStore()
    failures = (
        *_LLM_ONLY_FAILURES,
        "unrecoverable:provider:fmp:unrecoverable:http_402",
    )
    _preflight(
        graph, checked_at=_NOW - timedelta(minutes=5), passed=False, failures=failures
    )

    result = _place(graph)

    assert result.action == "held"
    assert result.readiness_state == "failing"
    assert result.failures == failures
    assert graph.list_nodes(RUN_REQUEST_LABEL) == ()


def test_unparseable_master_stale_and_missing_checks_still_hold() -> None:
    """MST-OUT-04 / MST-FAIL-05 / DSP-IN-03: only fresh declared failures degrade."""
    cases = (
        (("not-structured",), _NOW - timedelta(minutes=5), "failing"),
        (
            ("transient:master:vault:TimeoutError",),
            _NOW - timedelta(minutes=5),
            "failing",
        ),
        (_LLM_ONLY_FAILURES, _NOW - timedelta(minutes=71), "unknown"),
    )
    for failures, checked_at, expected_state in cases:
        graph = InMemoryGraphStore()
        _preflight(graph, checked_at=checked_at, passed=False, failures=failures)

        result = _place(graph)

        assert result.action == "held"
        assert result.readiness_state == expected_state
        assert graph.list_nodes(RUN_REQUEST_LABEL) == ()

    graph = InMemoryGraphStore()
    missing = _place(graph)
    assert missing.action == "held"
    assert missing.readiness_state == "unknown"
    assert graph.list_nodes(RUN_REQUEST_LABEL) == ()


def test_passing_check_places_normal_run_without_posture_property() -> None:
    """DSP-OUT-01 / DSP-OUT-04: normal scheduled placement stays byte-identical."""
    graph = InMemoryGraphStore()
    _preflight(graph, checked_at=_NOW - timedelta(minutes=5), passed=True)

    result = _place(graph)

    assert result.action == "placed"
    assert result.run_posture == "normal"
    run = graph.get_node(RUN_REQUEST_LABEL, "run-request:sched-2026-07-08")
    assert run is not None
    assert "run_posture" not in run.props
    assert "degraded_by" not in run.props


def test_degradable_set_comes_from_the_pack_declaration() -> None:
    """DSP-IN-03: omitted pack agents are not degraded by code defaults."""
    graph = InMemoryGraphStore()
    _preflight(
        graph,
        checked_at=_NOW - timedelta(minutes=5),
        passed=False,
        failures=("unrecoverable:operator:anthropic:unrecoverable:http_400",),
    )

    result = place_scheduled_run(
        graph,
        as_of=_AS_OF,
        now=_NOW,
        universe_source=FakeUniverse({"sp500": ("AAPL",)}),
        degradable_agents=frozenset({"deliberator-manager"}),
    )

    assert result.action == "held"
    assert graph.list_nodes(RUN_REQUEST_LABEL) == ()


def test_malformed_posture_pack_degrades_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DRIFT-068: malformed posture-pack rows fail closed."""
    module = import_module("orchestration.packs.trading_run_postures")

    class Resource:
        def joinpath(self, _name: str) -> Resource:
            return self

        def read_text(self) -> str:
            return '{"postures":{"degraded":{"degradable_agents":{}}}}'

    monkeypatch.setattr(module.resources, "files", lambda _package: Resource())

    assert module.degradable_agent_types() == frozenset()
