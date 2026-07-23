"""Provider graph-poll work source (DL-08).

Agent: provider
Role: find RunRequest nodes the dispatcher has placed that the provider has not
      ingested yet, and ingest their universe straight from the graph — so the
      provider is graph-pull like every other agent and the dispatcher's RunRequest
      is the single trigger that starts a run.
External I/O: delegates to ProviderAgent which calls the injected DataSource.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.provider.ingest import ingest_once
from contracts.positions import open_position_tickers
from contracts.provider import MARKET_DATA_LABEL, RUN_REQUEST_LABEL

if TYPE_CHECKING:
    from agents.provider.agent import ProviderAgent
    from kernel import GraphStore, Node

INGESTED_EDGE = "INGESTED_BY"


def find_pending(graph: GraphStore) -> list[Node]:
    """Return RunRequest nodes with no downstream MarketData (uningested work)."""
    pending: list[Node] = []
    for node in graph.list_nodes(RUN_REQUEST_LABEL):
        ingested = list(
            graph.descendants(node, max_depth=1, edge_types={INGESTED_EDGE})
        )
        if not ingested:
            pending.append(node)
    return pending


def ingest_run_node(node: Node, *, agent: ProviderAgent) -> None:
    """Ingest one RunRequest's universe and link the MarketData back to it."""
    tickers = tuple(str(ticker) for ticker in node.props["tickers"])
    market_key = ingest_once(
        agent,
        _union(tickers, open_position_tickers(agent._graph)),
        run_id=str(node.props["run_id"]),
    )
    assert market_key is not None  # the dispatcher always places a non-empty universe
    market_node = agent._graph.get_node(MARKET_DATA_LABEL, market_key)
    assert market_node is not None  # just written by ingest_once
    agent._graph.add_edge(node, market_node, INGESTED_EDGE)


def _union(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*left, *right)))
