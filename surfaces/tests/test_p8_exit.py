"""P8 exit criterion: G6 market-pack registration without core changes.

Agent: surfaces
Role: prove a new pack can be added in test scope and surfaced by the CLI.
External I/O: none.
"""

from __future__ import annotations

from io import StringIO

from kernel import InMemoryGraphStore, MarketPackRegistry
from orchestration.packs import USEquitiesSP500Pack
from surfaces.cli import main
from surfaces.context import test_context as build_context
from surfaces.queries.packs import all_packs
from surfaces.render import render_packs


class EuropeStocksTestPack:
    """Fictitious second pack defined entirely in test scope."""

    name = "europe_stocks_test"
    exchange = "LSE"
    universe_name = "lse_100"
    data_source_key = "test"
    max_stage = "paper"

    def is_ready(self) -> tuple[bool, str]:
        """Return test readiness."""
        return False, "test pack not production-ready"


def test_p8_register_second_pack_no_core_changes() -> None:
    registry = _registry_with_two_packs()

    assert registry.get("us_equities_sp500") is not None
    assert registry.get("missing") is None
    assert {pack.name for pack in registry.all_packs()} == {
        "us_equities_sp500",
        "europe_stocks_test",
    }


def test_p8_pack_readiness_and_empty_render() -> None:
    views = all_packs(_registry_with_two_packs())
    by_name = {view.name: view for view in views}

    assert by_name["us_equities_sp500"].ready is True
    assert by_name["europe_stocks_test"].ready is False
    assert render_packs(()) == "no market packs registered"


def test_p8_cli_packs_shows_both_registered_packs() -> None:
    ctx = build_context(pack_registry=_registry_with_two_packs())
    output = StringIO()

    main(["packs"], context=ctx, stdout=output)

    text = output.getvalue()
    assert "Market packs: 2" in text
    assert "us_equities_sp500" in text
    assert "europe_stocks_test" in text
    assert "not ready: test pack not production-ready" in text


def test_p8_stage_promote_end_to_end() -> None:
    graph = InMemoryGraphStore()
    ctx = build_context(graph=graph)
    _seed_snapshots(graph)
    _resolve_stage_flag(graph, "broker_shadow")
    output = StringIO()

    main(
        ["stage", "promote", "broker_shadow", "--confirmed"], context=ctx, stdout=output
    )

    assert "stage promotion dispatched to execution.promote_stage" in output.getvalue()
    assert graph.list_nodes("StageTransition")[0].props["to_stage"] == "broker_shadow"


def _registry_with_two_packs() -> MarketPackRegistry:
    registry = MarketPackRegistry()
    registry.register(USEquitiesSP500Pack())
    registry.register(EuropeStocksTestPack())
    return registry


def _seed_snapshots(graph: InMemoryGraphStore) -> None:
    for index in range(10):
        graph.merge_node(
            "Snapshot",
            f"snapshot:p8-{index}",
            {"metrics": {"portfolio": {"approval_rate": 0.80}}},
        )


def _resolve_stage_flag(graph: InMemoryGraphStore, target_stage: str) -> None:
    graph.merge_node(
        "FlagResolution",
        f"resolution:flag:stage_promote:{target_stage}:info",
        {"subject_ref": f"stage_promote:{target_stage}", "severity": "info"},
    )
