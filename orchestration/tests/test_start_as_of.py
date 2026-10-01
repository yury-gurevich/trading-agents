"""The RunRequest's writer and the provider agree on where the run's as-of lives (S249).

Agent: orchestration
Role: place a RunRequest for a past session and ingest the node it wrote, proving
      the as-of crosses the graph under the contract's name and the provider serves it.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from agents.provider import ProviderAgent
from agents.provider.poll import ingest_run_node
from agents.provider.sources import FakeDataSource
from contracts.provider import MARKET_DATA_LABEL, RUN_REQUEST_REQUESTED_AT_PROP
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.start import place_run_request


def test_the_provider_serves_the_as_of_the_dispatcher_wrote() -> None:
    """PROV-TRG-05: a RunRequest placed for 2026-09-30 is ingested for 2026-09-30.

    The property keeps the value 81 live nodes and the surfaces' readers use.
    """
    graph = InMemoryGraphStore()
    node = place_run_request(
        graph, run_id="r9", tickers=("AAPL",), as_of=date(2026, 9, 30)
    )
    agent = ProviderAgent(InProcessBus(), graph=graph, source=FakeDataSource())
    ingest_run_node(node, agent=agent)

    assert RUN_REQUEST_REQUESTED_AT_PROP == "requested_at"
    assert node.props[RUN_REQUEST_REQUESTED_AT_PROP] == "2026-09-30"
    market = graph.get_node(MARKET_DATA_LABEL, "market-data:r9")
    assert market is not None
    assert market.props["window_end"] == "2026-09-30"
