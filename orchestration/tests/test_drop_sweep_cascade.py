"""Drop-sweep outage containment through the graph-pull cascade.

Agent: orchestration
Role: prove a poisoned cleanup path no longer stalls downstream stages.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import agents.execution.poll as execution_poll
from agents.execution.paper_broker import PaperBroker
from agents.execution.tests.drop_sweep_helpers import broker_order, seed_fill_lineage
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.packs.trading_acceptance import accept_run
from orchestration.start import place_run_request
from orchestration.tests.helpers import source

if TYPE_CHECKING:
    import pytest

    from agents.execution.broker import BrokerFill


class SeededDropBroker(PaperBroker):
    """Paper broker with one historical stale order already visible."""

    def __init__(self, order: BrokerFill) -> None:
        super().__init__()
        self._fills[order.idempotency_key] = order


def _provider(graph: InMemoryGraphStore) -> ProviderAgent:
    return ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )


def _deliberation_llm() -> FakeLLMClient:
    return FakeLLMClient(
        {"DECISION UNDER TEST": '{"ruling": "uphold", "rationale": "ok"}'}
    )


def test_poisoned_drop_sweep_still_reaches_reporter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EXEC-FAIL-02 / DL-79: planted sweep failure still reaches 9/9."""
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="s151-poisoned", tickers=("AAPL", "MSFT"))

    def poison_sweep(*_: object, **__: object) -> int:
        raise RuntimeError("sweep poisoned")

    monkeypatch.setattr(execution_poll, "sweep_unfilled_orders", poison_sweep)

    results = cascade_once(
        graph,
        provider_agent=_provider(graph),
        broker=PaperBroker(),
        deliberation_llm=_deliberation_llm(),
    )
    acceptance = accept_run(graph, "s151-poisoned")

    assert {result.name: result.processed for result in results} == {
        "position_sync": 1,
        "provider": 1,
        "scanner": 1,
        "analyst": 1,
        "forecaster": 1,
        "portfolio_manager": 1,
        "deliberation": 1,
        "execution": 1,
        "monitor": 1,
        "reporter": 1,
    }
    assert acceptance.verdict == "PASS"
    assert any(
        "sweep poisoned" in fault.props["message"]
        for fault in graph.list_nodes("Fault")
    )


def test_legacy_colliding_fill_runs_end_to_end_and_records_drop() -> None:
    """EXEC-STA-03 / EXEC-OBS-02: production-shaped stale fill reaches reporter."""
    graph = InMemoryGraphStore()
    key = "old-run:ABT:buy"
    seed_fill_lineage(graph, "old-run", key, "ABT")
    graph.merge_node("Fill", key, {"broker_status": "rejected"})
    stale = broker_order(key, "ABT", status="rejected", reason="canceled")
    place_run_request(graph, run_id="s151-legacy", tickers=("AAPL", "MSFT"))

    cascade_once(
        graph,
        provider_agent=_provider(graph),
        broker=SeededDropBroker(stale),
        deliberation_llm=_deliberation_llm(),
    )
    acceptance = accept_run(graph, "s151-legacy")

    fill = graph.get_node("Fill", key)
    assert acceptance.verdict == "PASS"
    assert fill is not None
    assert fill.props["broker_status"] == "rejected"
    assert fill.props["drop_reason"] == "unfilled at session end"
    drop_statuses = [
        node
        for node in graph.list_nodes("BrokerOrderStatus")
        if node.props.get("fill_key") == key
        and node.props.get("reason") == "unfilled at session end"
    ]
    assert len(drop_statuses) == 1
    assert drop_statuses[0].props["status"] == "canceled"
