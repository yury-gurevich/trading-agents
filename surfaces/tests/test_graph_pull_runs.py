"""The CLI and MCP run views read graph-pull runs, the ones the dashboard lists.

Agent: surfaces
Role: prove `runs`, `run` and the last-run health field name real runs (DL-225).
External I/O: none; graph is in-memory and the bus refuses every call.
"""

from __future__ import annotations

from io import StringIO
from typing import cast

from kernel import InMemoryGraphStore, MessageBus
from surfaces.cli import main
from surfaces.context import SurfaceContext
from surfaces.mcp_tools import dispatch_tool
from surfaces.queries import recent_runs, run_detail, system_health
from surfaces.tests.performance_fixtures import HEADLINE, MEASURED, seed_run


class _RefusingBus:
    def request(self, message: object) -> object:
        raise AssertionError(f"a read may not ask an agent: {message!r}")


def _graph() -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    seed_run(
        graph,
        "sched-a",
        performance=dict(MEASURED),
        requested_at="2026-09-23T22:30:00+00:00",
    )
    seed_run(
        graph,
        "sched-b",
        performance=dict(MEASURED),
        requested_at="2026-09-24T22:30:00+00:00",
    )
    seed_run(
        graph, "held-c", requested_at="2026-09-25T22:30:00+00:00", with_snapshot=False
    )
    # Supervisor intents are Message nodes; on graph-pull runs they are never runs.
    graph.merge_node(
        "Message",
        "flag-resolve:x:approve",
        {"run_id": "flag-resolve:x", "step": "approve"},
    )
    return graph


def test_recent_runs_are_the_dashboards_runs_newest_first() -> None:
    """SRF-ORD-01: the MCP/CLI run list is the dashboard's, newest requested first."""
    runs = recent_runs(_graph())

    assert [run.run_id for run in runs] == ["held-c", "sched-b", "sched-a"]
    assert runs[0].completed is False
    assert runs[1].completed is True
    assert runs[1].steps[-1].name == "Snapshot"
    assert len(runs[1].steps) == 7
    assert runs[1].headline == HEADLINE
    assert recent_runs(_graph(), limit=1)[0].run_id == "held-c"
    assert recent_runs(_graph(), limit=-3) == ()


def test_run_detail_walks_the_chain_and_misses_intent_ids() -> None:
    """SRF-IN-01: a run id resolves through its RunRequest; an intent id does not."""
    graph = _graph()

    assert run_detail(graph, "sched-b") == recent_runs(graph)[1]
    assert run_detail(graph, "flag-resolve:x") is None
    assert run_detail(graph, "") is None


def test_the_mcp_runs_tool_lists_real_runs() -> None:
    """SRF-TYP-01 / SRF-ORD-01: the tool returns graph-pull runs as JSON dicts."""
    ctx = SurfaceContext(_graph(), cast("MessageBus", _RefusingBus()))

    result = dispatch_tool(ctx, "runs", {"limit": 2})

    assert result["runs"] == [
        {"run_id": "held-c", "completed": False, "steps": 6},
        {"run_id": "sched-b", "completed": True, "steps": 7},
    ]


def test_the_cli_run_prints_the_snapshot_headline_without_asking_an_agent() -> None:
    """SRF-IDN-02: a CLI read renders stored evidence and never requests a report."""
    ctx = SurfaceContext(_graph(), cast("MessageBus", _RefusingBus()))
    reported, held, missing, table = StringIO(), StringIO(), StringIO(), StringIO()

    main(["run", "sched-b"], context=ctx, stdout=reported)
    main(["run", "held-c"], context=ctx, stdout=held)
    main(["run", "flag-resolve:x"], context=ctx, stdout=missing)
    main(["runs", "--limit", "3"], context=ctx, stdout=table)

    assert "vs SPY: -0.28 pts over 32 sessions" in reported.getvalue()
    assert "7/7" in reported.getvalue()
    assert "snapshot unavailable" in held.getvalue()
    assert "run flag-resolve:x not found" in missing.getvalue()
    assert "flag-resolve" not in table.getvalue()
    assert "sched-a" in table.getvalue()


def test_the_last_run_is_the_newest_reported_one() -> None:
    """SRF-OUT-01: health names the newest run whose chain reached a Snapshot."""
    graph = _graph()
    graph.merge_node(
        "Snapshot", "snapshot:zzz-old-verify", {"run_id": "zzz-old-verify"}
    )

    assert system_health(graph).last_run_id == "sched-b"
    assert system_health(InMemoryGraphStore()).last_run_id is None
