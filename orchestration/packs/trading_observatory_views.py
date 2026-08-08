"""Trading-pack stage view extractors for the graph observatory.

Agent: orchestration
Role: extract the head/tail trading stages and assemble the pack's stage SPEC.
External I/O: none.

The scanner -> analyst -> PM decision chain lives in `trading_observatory_chain`,
and the shared reached-StageView builder in `trading_stage_view`, so no module here
approaches the 200-line hard block.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from orchestration.batch_chain import POSITION_SYNC_KEY
from orchestration.observatory import Check
from orchestration.packs.trading_deliberation_view import deliberation
from orchestration.packs.trading_fill_outcomes import execution_view
from orchestration.packs.trading_observatory_chain import analyst, pm, scanner
from orchestration.packs.trading_stage_view import view

if TYPE_CHECKING:
    from kernel import GraphStore, Node
    from orchestration.observatory import StageView


def position_sync(graph: GraphStore, node: Node) -> StageView:
    """Render the head-of-run broker-book sync marker."""
    del graph
    status = str(node.props.get("position_book_status", "unknown"))
    outputs: tuple[str, ...] = (
        f"status={status}  snapshot={node.props.get('snapshot_key', '?')}",
    )
    reason = node.props.get("position_book_stale_reason")
    if reason:
        outputs += (f"stale_reason={reason}",)
    return view(
        "position_sync",
        "RunRequest",
        {"synced": int(status in {"fresh", "stale"}), "status": status},
        (Check("synced", "required"),),
        outputs,
    )


def provider(graph: GraphStore, node: Node) -> StageView:
    """Render provider market data quality."""
    del graph
    from contracts.provider import MarketData

    market = MarketData.model_validate(node.props["snapshot"])
    quality = market.quality
    ratio = round(quality.returned / max(quality.requested, 1), 3)
    bars: dict[str, int] = {}
    for one in market.bars:
        bars[one.ticker] = bars.get(one.ticker, 0) + 1
    flag = "DEGRADED" if quality.used_fallback else "ok"
    sectors_n = len(market.sectors)
    outputs: tuple[str, ...] = (
        f"tickers   {' '.join(node.props['tickers'])}",
        "bars      " + "  ".join(f"{t}:{n}" for t, n in sorted(bars.items())),
        f"quality   {flag}  returned={quality.returned}/{quality.requested}",
        f"sectors   {sectors_n}/{quality.requested} classified"
        f"  (0 = PM concentration caps INACTIVE, DRIFT-013)",
    )
    if quality.stale_tickers:
        outputs += (f"stale     {' '.join(quality.stale_tickers)}",)
    if quality.anomalous_tickers:
        excluded = " ".join(quality.anomalous_tickers)
        outputs += (f"anomalous {excluded}  (>sigma excluded, DRIFT-014)",)
    observed: dict[str, object] = {
        "returned": quality.returned,
        "return_ratio": ratio,
        "sector_coverage": sectors_n,
    }
    checks = (
        Check("returned", "floor", 1.0),
        Check("return_ratio", "floor", 0.9),
        Check("sector_coverage", "floor", 1.0, severity="warn"),
    )
    return view("provider", "RunRequest", observed, checks, outputs)


def monitor(graph: GraphStore, node: Node) -> StageView:
    """Render tail monitor position checks."""
    del graph
    checked = node.props.get("positions_checked")
    outputs = (
        f"checked={checked}  closes={node.props.get('closes')}"
        f"  holds={node.props.get('holds')}",
    )
    observed: dict[str, object] = {"checked": checked}
    checks = (Check("checked", "required"),)
    return view("monitor", "ExecutionRun(execution)", observed, checks, outputs)


def reporter(graph: GraphStore, node: Node) -> StageView:
    """Render final report summary."""
    del graph
    metrics = cast("dict[str, object]", node.props.get("metrics") or {})
    portfolio = cast("dict[str, object]", metrics.get("portfolio") or {})
    summary = node.props.get("headline_summary")
    outputs = (
        f"open={portfolio.get('positions_opened')}"
        f"  closed={portfolio.get('positions_closed')}",
        f"summary   {summary}",
    )
    observed: dict[str, object] = {"summary": summary}
    checks = (Check("summary", "required"),)
    return view("reporter", "MonitorRun(monitor)", observed, checks, outputs)


SPEC = (
    ("position_sync", POSITION_SYNC_KEY, "RunRequest", position_sync),
    ("provider", "MarketData", "RunRequest", provider),
    ("scanner", "ScanRun", "MarketData(provider)", scanner),
    ("analyst", "AnalystRun", "CandidateSet(scanner)", analyst),
    ("pm", "PMRun", "RecommendationSet(analyst)", pm),
    ("deliberation", "DeliberationRun", "PMRun(pm)", deliberation),
    ("execution", "ExecutionRun", "OrderIntentSet(pm)", execution_view),
    ("monitor", "MonitorRun", "ExecutionRun(execution)", monitor),
    ("reporter", "Snapshot", "MonitorRun(monitor)", reporter),
)
