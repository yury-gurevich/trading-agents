"""S241 C8: the in-process cascade runs the forecaster's settlement pass too.

Agent: orchestration
Role: prove the local pipeline settles an older barrier claim from the run's own
      MarketData (read through the run's lineage), once, and that the pass never
      touches the trade path.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.paper_broker import PaperBroker
from agents.forecaster.tests.settlement_helpers import seed_claim
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import entry_bars, node_count, source


def _cascade(graph: InMemoryGraphStore) -> dict[str, int]:
    provider = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )
    results = cascade_once(graph, provider_agent=provider, broker=PaperBroker())
    return {result.name: result.processed for result in results}


def test_the_local_pipeline_settles_an_older_claim() -> None:
    """FORE-TRG-01 / FORE-OUT-08: a claim on the fixture's first AAPL bar (close
    100, stop 5 %, target 7 %) settles on the cascade's run: its MarketData holds
    ten sessions after that bar, and session 1's high of 111 reaches the target.
    A second cascade settles nothing again; the trade path completes as before."""
    graph = InMemoryGraphStore()
    first = min(
        (bar for bar in entry_bars() if bar.ticker == "AAPL"),
        key=lambda bar: bar.bar_date,
    )
    seed_claim(graph, as_of=first.bar_date, entry_close=first.close)
    place_run_request(graph, run_id="fc-settle", tickers=("AAPL", "MSFT"))

    processed = _cascade(graph)
    again = _cascade(graph)

    assert processed["forecaster_settlement"] == 1
    assert again["forecaster_settlement"] == 0
    [settlement] = graph.list_nodes("BarrierSettlement")
    assert settlement.props["outcome"] == "target"
    assert settlement.props["settling_ref"] == "market-data:fc-settle"
    assert settlement.props["entry_ratio"] == 1.0
    assert node_count(graph, "BarrierSettlementPass") == 1
    assert node_count(graph, "PMRun") == 1
    assert node_count(graph, "ExecutionRun") == 1
