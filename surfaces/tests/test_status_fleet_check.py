"""Status and error wording tests for the operator's quick answers.

Agent: surfaces
Role: prove status names a failing fleet check and vendor errors read as a sentence.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from kernel import InMemoryGraphStore
from surfaces import mcp_tools
from surfaces.context import test_context as build_context
from surfaces.mcp_tools import dispatch_tool
from surfaces.plain_errors import plain_error

if TYPE_CHECKING:
    import pytest

_DRAINED = (
    "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', "
    "'message': 'Your credit balance is too low to access the Anthropic API.'}, "
    "'request_id': 'req_011'}"
)


def _failing_graph() -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    checked_at = (datetime.now(tz=UTC) - timedelta(minutes=10)).isoformat()
    graph.merge_node(
        "FleetPreflight",
        f"preflight:{checked_at}",
        {
            "checked_at": checked_at,
            "passed": False,
            "failures": [
                *(
                    f"unrecoverable:{agent}:anthropic:unrecoverable:http_400"
                    for agent in ("deliberator-manager", "operator")
                ),
                "unrecoverable:provider:fmp:unrecoverable:http_402",
            ],
        },
    )
    return graph


def _degraded_graph() -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    checked_at = (datetime.now(tz=UTC) - timedelta(minutes=10)).isoformat()
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


def test_status_names_a_failing_fleet_check_above_the_health_line() -> None:
    status = dispatch_tool(build_context(graph=_failing_graph()), "status", {})

    assert status["fleet_check"] == "failing"
    first, second = str(status["summary"]).split("\n")
    assert first == (
        "Tonight's run will be held unless the next fleet check passes: "
        "anthropic answered HTTP 400 — 2 agents can't start: "
        "deliberator-manager, operator."
    )
    assert second == "System health is green."


def test_status_without_a_failing_check_is_unchanged() -> None:
    status = dispatch_tool(build_context(graph=InMemoryGraphStore()), "status", {})

    assert status["fleet_check"] == "passing"
    assert status["summary"] == "System health is green."


def test_status_names_degraded_fleet_check_as_no_new_buys() -> None:
    status = dispatch_tool(build_context(graph=_degraded_graph()), "status", {})

    assert status["fleet_check"] == "degraded"
    first, second = str(status["summary"]).split("\n")
    assert first == (
        "Tonight's run will place no new buys unless the next fleet check passes: "
        "anthropic answered HTTP 400 — 4 agents can't start: "
        "deliberator-manager, deliberator-opponent, deliberator-proponent, operator."
    )
    assert second == "System health is green."


def test_vendor_status_error_reads_as_one_sentence() -> None:
    assert plain_error(_DRAINED) == (
        "The language model refused the request (HTTP 400): "
        "Your credit balance is too low to access the Anthropic API."
    )
    assert plain_error('Error code: 429 - {"message": "slow down"}') == (
        "The language model refused the request (HTTP 429): slow down"
    )


def test_other_errors_pass_through_unchanged() -> None:
    assert plain_error("unknown tool: nope") == "unknown tool: nope"
    assert plain_error("Error code: 400 - no body") == "Error code: 400 - no body"


def test_dispatch_rewrites_raised_and_returned_vendor_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raises(ctx: object, args: object) -> dict[str, object]:
        raise RuntimeError(_DRAINED)

    def returns(ctx: object, args: object) -> dict[str, object]:
        return {"error": _DRAINED, "run_id": "r1"}

    ctx = build_context(graph=InMemoryGraphStore())
    monkeypatch.setattr(mcp_tools, "_cmd_runs", raises)
    raised = dispatch_tool(ctx, "runs", {})
    monkeypatch.setattr(mcp_tools, "_cmd_runs", returns)
    returned = dispatch_tool(ctx, "runs", {})

    assert str(raised["error"]).startswith("The language model refused the request")
    assert str(returned["error"]).startswith("The language model refused the request")
    assert returned["run_id"] == "r1"


def test_status_keeps_a_failed_check_until_the_next_one_replaces_it() -> None:
    """The master sleeps outside its window, so a five-hour-old failure stands."""
    graph = InMemoryGraphStore()
    checked_at = (datetime.now(tz=UTC) - timedelta(hours=5)).isoformat()
    graph.merge_node(
        "FleetPreflight",
        f"preflight:{checked_at}",
        {"checked_at": checked_at, "passed": False, "failures": ["x:y:z:http_400"]},
    )

    status = dispatch_tool(build_context(graph=graph), "status", {})

    assert status["fleet_check"] == "failing"
