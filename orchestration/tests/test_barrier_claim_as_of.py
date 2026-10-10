"""A past run's barrier history and claim use the run's own as-of (S266).

Agent: orchestration
Role: prove the local cascade and deployed provider work list read the run's
      last bar, with a source that can also serve later bars.
External I/O: none (in-memory graph, fake source, fake GARCH fitter).
"""

from __future__ import annotations

from agents.execution.paper_broker import PaperBroker
from agents.forecaster import ForecasterAgent
from agents.forecaster.barrier_fit import FakeGarchFitter
from agents.forecaster.tests.barrier_helpers import ACCEPTED
from contracts.barrier_history import BarrierHistory
from orchestration.local_pipeline import cascade_once
from orchestration.resume import resume_run
from orchestration.tests.barrier_as_of_helpers import (
    AS_OF,
    TODAY,
    analyze_pending,
    history_once,
    past_run,
    upstream_once,
)


def test_a_past_runs_claim_is_stated_on_its_own_last_bar() -> None:
    """PROV-OUT-08 / FORE-OUT-07: A1, the local pass claims on the run's last bar."""
    graph, provider, source = past_run()
    forecaster = ForecasterAgent(
        provider.bus, graph=graph, barrier_fitter=FakeGarchFitter(ACCEPTED)
    )

    cascade_once(
        graph,
        provider_agent=provider,
        broker=PaperBroker(),
        forecaster_agent=forecaster,
    )

    [market] = graph.list_nodes("MarketData")
    assert market.props["window_end"] == AS_OF.isoformat()
    [node] = graph.list_nodes("BarrierHistory")
    history = BarrierHistory.model_validate(dict(node.props))
    end = history.window_end
    assert end == AS_OF
    assert history.histories
    assert all(
        rows.bars[-1][0] == AS_OF.isoformat() for rows in history.histories.values()
    )
    claims = graph.list_nodes("BarrierForecast")
    assert claims
    assert len(claims) == len(history.histories)
    for claim in claims:
        ticker = claim.props["ticker"]
        own_bar = next(
            bar for bar in source.long if bar.ticker == ticker and bar.bar_date == AS_OF
        )
        assert claim.props["as_of"] == AS_OF.isoformat()
        assert claim.props["entry_close"] == own_bar.close
        assert claim.props["history_ref"] == node.key
    assert max(bar.bar_date for bar in source.long) == TODAY > AS_OF


def test_a_resumed_analysis_uses_its_source_runs_as_of() -> None:
    """PROV-OUT-08: A3, an analyst-stage resume keeps the copied source as-of."""
    graph, provider, _ = past_run()
    upstream_once(graph, provider)
    history_once(graph, provider)
    placement = resume_run(graph, source_run_id="past-barrier", resume_from="analyst")
    assert placement.created
    analyze_pending(graph)
    history_once(graph, provider)

    assert len(graph.list_nodes("AnalystRun")) == 2
    histories = graph.list_nodes("BarrierHistory")
    assert len(histories) == 2
    assert {node.props["window_end"] for node in histories} == {AS_OF.isoformat()}


def test_the_deployed_work_list_serves_the_runs_as_of() -> None:
    """PROV-OUT-08 / PROV-TRG-04: A2, a current run keeps its earlier as-of."""
    graph, provider, source = past_run()
    upstream_once(graph, provider)
    history_once(graph, provider)

    [market] = graph.list_nodes("MarketData")
    assert market.props["window_end"] == AS_OF.isoformat()
    [node] = graph.list_nodes("BarrierHistory")
    history = BarrierHistory.model_validate(dict(node.props))
    end = history.window_end
    assert end == AS_OF
    assert history.histories
    assert all(
        rows.bars[-1][0] == AS_OF.isoformat() for rows in history.histories.values()
    )
    assert max(bar.bar_date for bar in source.long) == TODAY > AS_OF
