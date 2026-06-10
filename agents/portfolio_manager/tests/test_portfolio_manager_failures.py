"""Portfolio Manager failure and explainable-silence tests.

Agent: portfolio_manager
Role: verify provider and evaluation failures become honest PM rejections.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import agents.portfolio_manager.agent as pm_agent_module
from agents.portfolio_manager import PortfolioManagerAgent
from agents.portfolio_manager.tests.helpers import (
    bar,
    evaluate_message,
    recommendation,
    recommendation_set,
    wire_pm,
)
from contracts.portfolio_manager import OrderIntentSet
from kernel import InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    import pytest


def test_empty_recommendations_return_explainable_empty_result() -> None:
    payload = recommendation_set()
    bus, _, _ = wire_pm()

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert result.rejected == ()
    assert (
        result.explanation.summary == "No orders approved; 0 recommendations rejected."
    )


def test_provider_unavailable_rejects_without_crashing() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    PortfolioManagerAgent(bus, graph=graph).bind()
    payload = recommendation_set(recommendation("AAPL"))

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert [(item.ticker, item.reason) for item in result.rejected] == [
        ("AAPL", "provider_unavailable")
    ]


def test_degraded_regime_rejects_honestly_and_records_fault() -> None:
    payload = recommendation_set(recommendation("AAPL"))
    bus, _, sink = wire_pm(source_bars=(bar("AAPL", 0, 100.0),), fail_regime=True)

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert [(item.ticker, item.reason) for item in result.rejected] == [
        ("AAPL", "provider_degraded")
    ]
    assert sink.faults[-1].message == "provider returned degraded regime data"


def test_evaluation_fault_rejects_all_recommendations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(pm_agent_module, "evaluate_recommendations", boom)
    payload = recommendation_set(recommendation("AAPL"))
    bus, _, sink = wire_pm(source_bars=(bar("AAPL", 0, 100.0),))

    response = bus.request(evaluate_message(payload))

    result = OrderIntentSet.model_validate(response.payload)
    assert result.approved == ()
    assert [(item.ticker, item.reason) for item in result.rejected] == [
        ("AAPL", "portfolio_evaluation_failed")
    ]
    assert sink.faults[-1].message == "boom"
