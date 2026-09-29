"""Provider graph-poll work source (DL-08).

Agent: provider
Role: find RunRequest nodes the dispatcher has placed that the provider has not
      ingested yet, and ingest their universe straight from the graph — so the
      provider is graph-pull like every other agent and the dispatcher's RunRequest
      is the single trigger that starts a run. A second work kind writes the barrier
      history an AnalystRun's qualifying buys need (DL-241 D10).
External I/O: delegates to ProviderAgent which calls the injected DataSource.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Literal

from agents.provider.barrier_history import (
    find_pending_barrier_history,
    write_barrier_history,
)
from agents.provider.domain.market_calendar import trading_sessions_between
from agents.provider.ingest import ingest_once
from contracts.positions import open_position_tickers
from contracts.provider import (
    MARKET_DATA_LABEL,
    RUN_REQUEST_BENCHMARK_TICKER_PROP,
    RUN_REQUEST_LABEL,
    RUN_REQUEST_LOOKBACK_DAYS_PROP,
    RUN_REQUEST_REQUIRED_HISTORY_BARS_PROP,
)
from kernel.graph_pending import pending_nodes

if TYPE_CHECKING:
    from agents.provider.agent import ProviderAgent
    from kernel import GraphStore, Node

INGESTED_EDGE = "INGESTED_BY"


@dataclass(frozen=True)
class ProviderWorkItem:
    """One provider poll item: a RunRequest, or an AnalystRun needing history.

    ``barrier_history`` items are AnalystRuns whose qualifying buys need their
    BarrierHistory written (DL-241 D10).
    """

    kind: Literal["ingest", "barrier_history"]
    node: Node


def find_pending_work(
    graph: GraphStore, *, now: datetime | None = None
) -> list[ProviderWorkItem]:
    """Return run ingests before barrier histories, as one work list.

    ``now`` limits barrier histories to current runs (the deployed loop, D11).
    """
    return [
        *(ProviderWorkItem("ingest", node) for node in find_pending(graph)),
        *(
            ProviderWorkItem("barrier_history", node)
            for node in find_pending_barrier_history(graph, now=now)
        ),
    ]


def find_current_work(graph: GraphStore) -> list[ProviderWorkItem]:
    """The deployed loop's work list: barrier histories for current runs only (D11)."""
    return find_pending_work(graph, now=datetime.now(tz=UTC))


def process_work_item(item: ProviderWorkItem, *, agent: ProviderAgent) -> None:
    """Dispatch one provider work item without widening the work_loop."""
    if item.kind == "ingest":
        ingest_run_node(item.node, agent=agent)
    else:
        write_barrier_history(item.node, agent=agent)


def find_pending(graph: GraphStore) -> list[Node]:
    """Return RunRequest nodes with no downstream MarketData (uningested work).

    Found by key and edge alone; only the pending RunRequests are fetched (DL-246).
    """
    return pending_nodes(graph, RUN_REQUEST_LABEL, INGESTED_EDGE)


def ingest_run_node(node: Node, *, agent: ProviderAgent) -> None:
    """Ingest one RunRequest's universe and link the MarketData back to it."""
    tickers = tuple(str(ticker) for ticker in node.props["tickers"])
    market_key = ingest_once(
        agent,
        _union(tickers, open_position_tickers(agent._graph)),
        run_id=str(node.props["run_id"]),
        lookback_days=_lookback_days(node),
        benchmark_ticker=_benchmark_ticker(node),
    )
    assert market_key is not None  # the dispatcher always places a non-empty universe
    market_node = agent._graph.get_node(MARKET_DATA_LABEL, market_key)
    assert market_node is not None  # just written by ingest_once
    agent._graph.add_edge(node, market_node, INGESTED_EDGE)


def _union(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*left, *right)))


def _benchmark_ticker(node: Node) -> str | None:
    """The beta benchmark this run declared, or None when it named none.

    The ticker is the scanner's to own (it is the denominator of its beta cap);
    the dispatcher stamps it on the RunRequest so the provider can ingest the
    series without importing another agent's settings. Absent or blank means the
    run asked for no benchmark, which costs the beta cap and nothing else.
    """
    raw = node.props.get(RUN_REQUEST_BENCHMARK_TICKER_PROP)
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip().upper()


def _lookback_days(node: Node) -> int:
    raw = node.props.get(RUN_REQUEST_LOOKBACK_DAYS_PROP)
    required = node.props.get(RUN_REQUEST_REQUIRED_HISTORY_BARS_PROP)
    if (
        not isinstance(raw, int)
        or raw < 1
        or not isinstance(required, int)
        or required < 1
    ):
        raise ValueError(
            "RunRequest.lookback_days and required_history_bars must be positive "
            "integers"
        )
    if _covered_sessions(raw) < required:
        raise ValueError("RunRequest.lookback_days does not cover required history")
    return raw


def _covered_sessions(lookback_days: int) -> int:
    end = datetime.now(tz=UTC).date()
    start = end - timedelta(days=lookback_days)
    return trading_sessions_between(start - timedelta(days=1), end)
