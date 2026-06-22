"""Batch trace — per-stage metrics for one graph-pull pipeline run.

Agent: orchestration
Role: walk the provenance chain for a given run_id and print structured numbers for
      every stage (provider -> reporter). A batch is one RunRequest: one universe,
      one download, processed end-to-end. Reads only; never writes.
External I/O: none (delegates to the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore, Node

_CHAIN = (
    ("INGESTED_BY", "MarketData"),
    ("SCANNED_BY", "ScanRun"),
    ("ANALYZED_BY", "AnalystRun"),
    ("EVALUATED_BY", "PMRun"),
    ("EXECUTED_BY", "ExecutionRun"),
    ("MONITORED_BY", "MonitorRun"),
    ("REPORTED_BY", "Snapshot"),
)


def walk_chain(graph: GraphStore, run_id: str) -> dict[str, Node]:
    """Walk the provenance chain and return all found nodes keyed by label."""
    run_request = graph.get_node("RunRequest", f"run-request:{run_id}")
    if run_request is None:
        return {}
    nodes: dict[str, Node] = {"RunRequest": run_request}
    current: Node = run_request
    for edge, label in _CHAIN:
        child = next(
            iter(graph.descendants(current, max_depth=1, edge_types={edge})), None
        )
        if child is None:
            break
        nodes[label] = child
        current = child
    return nodes


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
            f"regime-context:{market_node.props.get('window_end', '')}",
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
            print(f"  {rej.ticker:<6} SKIP  {rej.reason}")
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
            pf = pm_metrics.get("profit_factor")
            exp = pm_metrics.get("expectancy_cents")
            pf_str = f"  profit_factor={pf:.2f}" if pf is not None else ""
            exp_str = f"  expectancy_cents={exp:.0f}" if exp is not None else ""
            print(
                f"  open={pm_metrics.get('positions_opened', '?')}"
                f"  closed={pm_metrics.get('positions_closed', '?')}"
                f"{pf_str}{exp_str}"
            )
        if headline:  # pragma: no branch
            print(f"  summary   {headline[:80]}")
        print()

    complete = sum(1 for lbl in (lbl for _, lbl in _CHAIN) if lbl in nodes)
    status = "OK batch processed" if complete == len(_CHAIN) else "INCOMPLETE"
    print(f"RESULT  {complete}/{len(_CHAIN)} stages complete  {status}")
    return complete
