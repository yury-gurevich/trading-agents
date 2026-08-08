"""PM rejection rendering tests.

Agent: orchestration
Role: prove trace surfaces reveal secondary rejected-order gate failures.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.execution.paper_broker import PaperBroker
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.common import Explanation, Provenance
from contracts.portfolio_manager import GateOutcome, OrderIntentSet, RejectedOrder
from kernel import InMemoryGraphStore, InProcessBus, Node
from orchestration.batch_trace import print_trace
from orchestration.local_pipeline import cascade_once
from orchestration.packs.trading_observatory_chain import pm
from orchestration.start import place_run_request
from orchestration.tests.helpers import bar

if TYPE_CHECKING:
    import pytest


def test_batch_trace_renders_secondary_failed_rejection_gates(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """PM-OBS-01 / LAW-02: batch_trace shows a second failed PM gate."""
    graph = _cascade(
        "trace-two-fail",
        PortfolioManagerSettings(
            starting_cash=Decimal("1500.00"),
            max_position_pct=Decimal("0.80"),
            max_positions=1,
        ),
    )

    assert print_trace(graph, "trace-two-fail") == 8
    out = capsys.readouterr().out
    assert "MSFT   SKIP  max_positions (also failed: cash_available)" in out


def test_batch_trace_stays_quiet_on_one_rejection_gate(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """PM-OBS-01 / LAW-02: a single failed PM gate keeps the old trace shape."""
    graph = _cascade(
        "trace-one-fail",
        PortfolioManagerSettings(
            starting_cash=Decimal("10000.00"),
            max_position_pct=Decimal("0.10"),
            max_positions=1,
        ),
    )

    assert print_trace(graph, "trace-one-fail") == 8
    out = capsys.readouterr().out
    assert "MSFT   SKIP  max_positions" in out
    assert "also failed" not in out


def test_observatory_pm_view_matches_trace_rejection_suffix() -> None:
    """PM-OBS-01 / LAW-02: observatory view names the same secondary PM gates."""
    view = pm(
        InMemoryGraphStore(),
        Node(
            "PMRun",
            "pm-run-render",
            {
                "order_intent_set": _order_set(
                    RejectedOrder(
                        ticker="MSFT",
                        reason="max_positions",
                        gate_report=(
                            _gate("max_positions", passed=False),
                            _gate("cash_available", passed=False),
                        ),
                    )
                ).model_dump(mode="json")
            },
        ),
    )

    assert view.outputs[-1] == (
        "MSFT   SKIP  max_positions (also failed: cash_available)"
    )


def _cascade(run_id: str, pm_settings: PortfolioManagerSettings) -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    provider = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=FakeDataSource(
            bars=(
                bar("AAPL", 4, 100.0),
                bar("AAPL", 0, 116.0),
                bar("MSFT", 4, 100.0),
                bar("MSFT", 0, 116.0),
            ),
            vix=12.0,
        ),
        settings=ProviderSettings(max_staleness_days=7),
    )
    place_run_request(graph, run_id=run_id, tickers=("AAPL", "MSFT"))
    list(
        cascade_once(
            graph,
            provider_agent=provider,
            broker=PaperBroker(),
            pm_settings=pm_settings,
        )
    )
    return graph


def _order_set(rejection: RejectedOrder) -> OrderIntentSet:
    return OrderIntentSet(
        run_id="pm-run-render",
        approved=(),
        rejected=(rejection,),
        explanation=Explanation(summary="fixture"),
        provenance=Provenance(run_id="pm-run-render", source_agent="portfolio_manager"),
    )


def _gate(name: str, *, passed: bool) -> GateOutcome:
    return GateOutcome(
        name=name,
        value=1.0,
        threshold=1.0,
        passed=passed,
        detail="fixture",
    )
