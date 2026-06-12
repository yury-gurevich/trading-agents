"""CLI stage-promotion tests.

Agent: surfaces
Role: verify operator stage promotion goes through supervisor and execution.
External I/O: none.
"""

from __future__ import annotations

from io import StringIO

from kernel import InMemoryGraphStore
from surfaces.cli import main
from surfaces.context import test_context as build_context


def test_cli_stage_promote_refuses_without_evidence() -> None:
    graph = InMemoryGraphStore()
    output = StringIO()

    main(
        ["stage", "promote", "broker_shadow"],
        context=build_context(graph),
        stdout=output,
    )

    assert "refused: need 10 runs" in output.getvalue()
    assert graph.list_nodes("StageTransition") == ()


def test_cli_stage_promote_requests_confirmation_with_evidence() -> None:
    graph = InMemoryGraphStore()
    _seed_snapshots(graph)
    output = StringIO()

    main(
        ["stage", "promote", "broker_shadow"],
        context=build_context(graph),
        stdout=output,
    )

    assert "refused: confirmation required" in output.getvalue()
    flag = graph.get_node("Flag", "flag:stage_promote:broker_shadow:info")
    assert flag is not None
    assert graph.list_nodes("StageTransition") == ()


def test_cli_stage_promote_confirmed_writes_transition() -> None:
    graph = InMemoryGraphStore()
    _seed_snapshots(graph)
    first = StringIO()
    confirmed = StringIO()
    ctx = build_context(graph)

    main(["stage", "promote", "broker_shadow"], context=ctx, stdout=first)
    _resolve_stage_flag(graph, "broker_shadow")
    main(
        ["stage", "promote", "broker_shadow", "--confirmed"],
        context=ctx,
        stdout=confirmed,
    )

    assert (
        "stage promotion dispatched to execution.promote_stage" in confirmed.getvalue()
    )
    assert graph.list_nodes("StageTransition")[0].props["to_stage"] == "broker_shadow"


def _seed_snapshots(graph: InMemoryGraphStore) -> None:
    for index in range(10):
        graph.merge_node(
            "Snapshot",
            f"snapshot:stage-{index}",
            {"metrics": {"portfolio": {"approval_rate": 0.80}}},
        )


def _resolve_stage_flag(graph: InMemoryGraphStore, target_stage: str) -> None:
    graph.merge_node(
        "FlagResolution",
        f"resolution:flag:stage_promote:{target_stage}:info",
        {"subject_ref": f"stage_promote:{target_stage}", "severity": "info"},
    )
