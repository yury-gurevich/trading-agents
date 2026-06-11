"""CLI surface tests.

Agent: surfaces
Role: verify terminal commands render graph and bus state.
External I/O: none.
"""

from __future__ import annotations

import json
from io import StringIO
from typing import TYPE_CHECKING

from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus
from surfaces.cli import main
from surfaces.context import SurfaceContext
from surfaces.context import test_context as build_context

if TYPE_CHECKING:
    import pytest


def test_cli_status_renders_health(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["status"], context=build_context()) == 0
    assert "healthy" in capsys.readouterr().out


def test_cli_runs_renders_seeded_run_and_empty_table() -> None:
    graph = InMemoryGraphStore()
    _seed_message(graph, "cli-run", "scan")
    output = StringIO()

    main(["runs"], context=build_context(graph=graph), stdout=output)
    empty = StringIO()
    main(["runs"], context=build_context(), stdout=empty)

    assert "cli-run" in output.getvalue()
    assert "no runs" in empty.getvalue()


def test_cli_run_reports_snapshot_or_missing_run() -> None:
    graph = InMemoryGraphStore()
    _seed_message(graph, "needs-report", "scan")
    output = StringIO()
    main(["run", "needs-report"], context=build_context(graph=graph), stdout=output)
    missing = StringIO()
    main(["run", "absent"], context=build_context(graph=graph), stdout=missing)

    assert "No PMRun found for needs-report." in output.getvalue()
    assert "run absent not found" in missing.getvalue()


def test_cli_run_handles_reporter_error() -> None:
    graph = InMemoryGraphStore()
    _seed_message(graph, "unbound", "scan")
    output = StringIO()
    context = SurfaceContext(graph, InProcessBus())
    main(["run", "unbound"], context=context, stdout=output)
    assert "snapshot unavailable" in output.getvalue()


def test_cli_positions_renders_empty_and_open_position() -> None:
    empty = StringIO()
    main(["positions"], context=build_context(), stdout=empty)
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Position",
        "run-a:AAPL",
        {
            "run_id": "run-a",
            "ticker": "AAPL",
            "quantity": 4,
            "opened_price_cents": 10000,
            "status": "open",
        },
    )
    output = StringIO()
    main(["positions"], context=build_context(graph=graph), stdout=output)

    assert "no open positions" in empty.getvalue()
    assert "run-a:AAPL" in output.getvalue()


def test_cli_position_renders_lifecycle_or_missing_message() -> None:
    graph = InMemoryGraphStore()
    _seed_position(graph)
    output = StringIO()
    missing = StringIO()

    main(["position", "run-a:AAPL"], context=build_context(graph=graph), stdout=output)
    main(["position", "missing"], context=build_context(graph=graph), stdout=missing)

    assert "ticker          AAPL" in output.getvalue()
    assert "position not found: missing" in missing.getvalue()


def test_cli_flags_renders_pending_flags_or_empty_message() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "Flag",
        "flag:approval:warn",
        {"subject_ref": "approval", "severity": "warn", "created_at": "now"},
    )
    output = StringIO()
    empty = StringIO()

    main(["flags"], context=build_context(graph=graph), stdout=output)
    main(["flags"], context=build_context(), stdout=empty)

    assert "approval" in output.getvalue()
    assert "approve <subject>" in output.getvalue()
    assert "no pending flags" in empty.getvalue()


def test_cli_command_reaches_supervisor_dispatch() -> None:
    llm = FakeLLMClient(
        {
            "run": json.dumps(
                {
                    "outcome": "intent",
                    "family": "run",
                    "parameters": {"confirmed": "true"},
                }
            )
        }
    )
    output = StringIO()

    main(
        ["command", "run the daily scan"],
        context=build_context(llm=llm),
        stdout=output,
    )

    assert "routed_to       orchestration.execute_run" in output.getvalue()


def test_cli_command_refusal_skips_supervisor_dispatch() -> None:
    llm = FakeLLMClient(
        {"refuse": json.dumps({"outcome": "refused", "reason": "unsafe"})}
    )
    output = StringIO()

    main(["command", "refuse this"], context=build_context(llm=llm), stdout=output)

    assert "outcome         refused" in output.getvalue()
    assert "accepted" not in output.getvalue()


def _seed_message(graph: InMemoryGraphStore, run_id: str, step: str) -> None:
    graph.merge_node(
        "Message",
        f"{run_id}:{step}",
        {
            "run_id": run_id,
            "step": step,
            "status": "attempted",
            "created_at": "2026-06-11T00:00:00+00:00",
        },
    )


def _seed_position(graph: InMemoryGraphStore) -> None:
    graph.merge_node(
        "Position",
        "run-a:AAPL",
        {
            "run_id": "run-a",
            "ticker": "AAPL",
            "quantity": 4,
            "opened_price_cents": 10000,
            "status": "open",
        },
    )
