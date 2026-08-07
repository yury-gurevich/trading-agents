"""Batch trace — per-stage metrics for one graph-pull pipeline run.

Agent: orchestration
Role: walk the provenance chain for a given run_id and print structured numbers for
      every stage (position sync -> reporter). A batch is one RunRequest: one
      universe, one download, processed end-to-end. Reads only; never writes.
External I/O: none (delegates to the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.batch_chain import CHAIN, POSITION_SYNC_KEY
from orchestration.batch_chain import walk_chain as walk_chain
from orchestration.pm_rejections import format_pm_rejection
from orchestration.trace_format import metric_text as mt

if TYPE_CHECKING:
    from kernel import GraphStore

_COMPLETE_KEYS = (POSITION_SYNC_KEY, *(label for _, label in CHAIN))


def print_trace(graph: GraphStore, run_id: str) -> int:
    """Print per-stage batch metrics. Returns number of completed stages (max 7)."""
    from contracts.provider import REGIME_CONTEXT_LABEL, MarketData, RegimeContext

    nodes = walk_chain(graph, run_id)
    if not nodes:
        print(f"  RunRequest not found for run-id={run_id!r}")
        return 0

    run_request = nodes["RunRequest"]
    as_of = run_request.props.get("requested_at", "unknown")
    print(f"\nBATCH TRACE  run-id={run_id}  as-of={as_of}")
    print("-" * 56)

    sync_node = nodes.get(POSITION_SYNC_KEY)
    if sync_node:
        print("[position_sync]")
        print(
            f"  status={sync_node.props.get('position_book_status', '?')}"
            f"  snapshot={sync_node.props.get('snapshot_key', '?')}"
        )
        reason = sync_node.props.get("position_book_stale_reason")
        if reason:
            print(f"  stale_reason={reason}")
        print()

    market_node = nodes.get("MarketData")
    if market_node:
        market = MarketData.model_validate(market_node.props["snapshot"])
        tickers: list[str] = list(market_node.props["tickers"])
        bars: dict[str, int] = {}
        for bar in market.bars:
            bars[bar.ticker] = bars.get(bar.ticker, 0) + 1
        news_counts = {t: len(h) for t, h in market.news.items() if h}
        regime_node = graph.get_node(
            REGIME_CONTEXT_LABEL,
            f"regime-context:{market_node.props.get('run_id', '')}",
        )
        regime = (
            RegimeContext.model_validate(regime_node.props["snapshot"])
            if regime_node
            else None
        )
        q = market.quality
        print("[provider]")
        print(f"  tickers   {len(tickers)}  ->  {' '.join(tickers)}")
        bars_str = "  ".join(f"{t}:{n}" for t, n in sorted(bars.items()))
        print(f"  bars      {bars_str}  ({sum(bars.values())} total)")
        if news_counts:
            news_str = "  ".join(f"{t}:{n}" for t, n in sorted(news_counts.items()))
            print(f"  news      {news_str}  ({sum(news_counts.values())} headlines)")
        if regime:  # pragma: no branch
            vix = f"  vix={regime.vix:.1f}" if regime.vix is not None else ""
            print(f"  regime    {regime.label}{vix}")
        flag = "DEGRADED" if q.used_fallback else "ok"
        print(f"  quality   {flag}  returned={q.returned}/{q.requested}")
        if q.stale_tickers:
            print(f"  stale     {' '.join(q.stale_tickers)}")
        if q.notes:
            print(f"  notes     {' '.join(q.notes)}")
        print()

    scan_node = nodes.get("ScanRun")
    if scan_node:
        from contracts.scanner import CandidateSet

        cs = CandidateSet.model_validate(scan_node.props["candidate_set"])
        ft = cs.filter_trace
        print("[scanner]")
        print(
            f"  universe={ft.universe_size}"
            f"  evaluated={ft.evaluated}"
            f"  survived={len(cs.candidates)}"
        )
        if ft.dropped_by_filter:
            drops = "  ".join(f"{f}:{n}" for f, n in ft.dropped_by_filter.items())
            print(f"  dropped   {drops}")
        if cs.candidates:  # pragma: no branch
            scores = "  ".join(
                f"{c.ticker}:{c.score:.1f}"
                for c in sorted(cs.candidates, key=lambda c: -c.score)
            )
            print(f"  scores    {scores}")
        print()

    analyst_node = nodes.get("AnalystRun")
    if analyst_node:
        from contracts.analyst import RecommendationSet

        rs = RecommendationSet.model_validate(analyst_node.props["recommendation_set"])
        print("[analyst]")
        print(f"  scored={len(rs.recommendations)}  rejected={len(rs.rejections)}")
        for r in sorted(rs.recommendations, key=lambda r: -r.confidence):
            senti = (
                f"  senti={r.sentiment_score:.1f}"
                if r.sentiment_score is not None
                else ""
            )
            line = (
                f"  {r.ticker:<6} {r.action!s:<4}"
                f"  conf={r.confidence:.2f}  tech={r.technical_score:.1f}{senti}"
            )
            print(line)
        for arej in rs.rejections:
            print(f"  {arej.ticker:<6} REJECT  {arej.reason}")
        print()

    pm_node = nodes.get("PMRun")
    if pm_node:
        from contracts.portfolio_manager import OrderIntentSet

        ois = OrderIntentSet.model_validate(pm_node.props["order_intent_set"])
        print("[pm]")
        print(f"  approved={len(ois.approved)}  rejected={len(ois.rejected)}")
        for o in ois.approved:
            print(
                f"  {o.ticker:<6} {o.action!s:<4}"
                f"  qty={o.quantity}  est=${o.est_price.amount:.2f}"
            )
        for rej in ois.rejected:
            print(f"  {format_pm_rejection(rej)}")
        print()

    exec_node = nodes.get("ExecutionRun")
    if exec_node:
        submitted = exec_node.props.get("submitted", "?")
        rejected = exec_node.props.get("rejected", "?")
        print("[execution]")
        print(f"  submitted={submitted}  rejected={rejected}")
        print()

    monitor_node = nodes.get("MonitorRun")
    if monitor_node:
        print("[monitor]")
        print(
            f"  checked={monitor_node.props.get('positions_checked', '?')}"
            f"  closes={monitor_node.props.get('closes', '?')}"
            f"  holds={monitor_node.props.get('holds', '?')}"
        )
        print()

    snapshot_node = nodes.get("Snapshot")
    if snapshot_node:
        metrics = snapshot_node.props.get("metrics") or {}
        pm_raw = metrics.get("portfolio") if hasattr(metrics, "get") else None
        pm_metrics = pm_raw or {}
        headline: str = str(snapshot_node.props.get("headline_summary", ""))
        print("[reporter]")
        if pm_metrics:  # pragma: no branch
            print(
                f"  open={pm_metrics.get('positions_opened', '?')}"
                f"  closed={pm_metrics.get('positions_closed', '?')}"
                f"  profit_factor={mt(pm_metrics.get('profit_factor'), '.2f')}"
                f"  expectancy_cents={mt(pm_metrics.get('expectancy_cents'), '.0f')}"
            )
        if headline:  # pragma: no branch
            print(f"  summary   {headline[:80]}")
        print()

    complete = sum(1 for key in _COMPLETE_KEYS if key in nodes)
    total = len(_COMPLETE_KEYS)
    status = "OK batch processed" if complete == total else "INCOMPLETE"
    print(f"RESULT  {complete}/{total} stages complete  {status}")
    return complete
