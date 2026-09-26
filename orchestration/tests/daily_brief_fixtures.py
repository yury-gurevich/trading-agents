"""Graph fixtures for the S234 daily-brief tests.

Agent: orchestration
Role: seed scheduled runs shaped like the live facts S234 measured, stage by stage.
External I/O: none.

Every payload is a real contract model, so the pack's `accept_run` scores these runs
itself: a fixture that faked the verdict would prove nothing about the brief's.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.scanner.universe import FakeUniverse
from contracts.common import Explanation, Money
from contracts.portfolio_manager import OrderIntent
from contracts.position_sync import POSITION_SYNC_EDGE
from contracts.provider import RUN_REQUEST_LABEL
from contracts.run_posture import RUN_POSTURE_DEGRADED
from orchestration.scheduled_dispatch_human import dispatch_with_human_answer
from orchestration.start import place_run_request
from orchestration.tests.daily_brief_payloads import TICKER, stage_payloads

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore, Node
    from orchestration.scheduled_dispatch import ScheduledDispatchResult
    from orchestration.telegram_port import TelegramPort

DAY = date(2026, 9, 25)
PREVIOUS_DAY = date(2026, 9, 24)
# sched-2026-09-25's reporter clause, as measured (spec row 8).
CLAUSE = "vs SPY: -0.43 pts over 33 sessions at 21% invested"
# The chain in walk_chain's order; the head position-sync marker is a MonitorRun.
STAGES = (
    ("PositionSync", "MonitorRun", POSITION_SYNC_EDGE),
    ("MarketData", "MarketData", "INGESTED_BY"),
    ("ScanRun", "ScanRun", "SCANNED_BY"),
    ("AnalystRun", "AnalystRun", "ANALYZED_BY"),
    ("PMRun", "PMRun", "EVALUATED_BY"),
    ("ExecutionRun", "ExecutionRun", "EXECUTED_BY"),
    ("MonitorRun", "MonitorRun", "MONITORED_BY"),
    ("Snapshot", "Snapshot", "REPORTED_BY"),
)


def at(hour: int, minute: int, day: date = DAY) -> datetime:
    """Return a UTC fire time on the given day."""
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=UTC)


def pm_key(day: date, prefix: str = "sched") -> str:
    """Return the fixture PMRun key for one run of a day."""
    return f"pm-run-{prefix}-{day:%Y%m%d}"


def performance(equity_cents: float, *, sessions: float = 33.0) -> dict[str, float]:
    """Return a performance group with every key the reporter writes."""
    names = [
        "portfolio_return_pct",
        "benchmark_return_pct",
        "exposure_matched_return_pct",
        "excess_return_pct",
        "average_exposure_pct",
        "max_drawdown_pct",
        "rolling_portfolio_return_pct",
        "rolling_exposure_matched_return_pct",
        "rolling_excess_return_pct",
        "performance_gap_sessions",
    ]
    group = dict.fromkeys(names, 0.0)
    return group | {"performance_sessions": sessions, "equity_cents": equity_cents}


def metrics_with(group: object) -> dict[str, object]:
    """Return a Snapshot metrics blob carrying ``group`` as its performance."""
    blob: dict[str, object] = {
        "portfolio": {"positions_opened": 0.0, "positions_closed": 0.0},
        "signal": {"recommendation_count": 1.0},
    }
    return blob if group is None else blob | {"performance": group}


def seed_run(
    graph: InMemoryGraphStore,
    day: date = DAY,
    *,
    pm_created: str,
    through: str = "Snapshot",
    metrics: object = None,
    clause: str = CLAUSE,
    approved: tuple[OrderIntent, ...] = (),
    degraded: bool = False,
    briefed: bool = False,
    prefix: str = "sched",
) -> Node:
    """Place one run (scheduled by default) and write its chain up to ``through``."""
    run_id = f"{prefix}-{day.isoformat()}"
    pm = pm_key(day, prefix)
    request = place_run_request(graph, run_id=run_id, tickers=(TICKER,), as_of=day)
    marks: dict[str, object] = {}
    if degraded:
        marks |= {"run_posture": RUN_POSTURE_DEGRADED, "degraded_by": ["llm:x"]}
    if briefed:
        marks |= {
            "brief_sent_at": f"{day.isoformat()}T22:50:00+00:00",
            "brief_message_id": 7,
            "brief_verdict": "PASS",
        }
    if marks:
        request = graph.merge_node(RUN_REQUEST_LABEL, request.key, marks)
    payloads = stage_payloads(run_id, pm, day, approved, pm_created)
    payloads["Snapshot"] = {
        "run_id": pm,
        "metrics": metrics_with(performance(10_197_632.0))
        if metrics is None
        else metrics,
        "headline_summary": f"0 positions opened; 0 closed; 1 recommendations "
        f"stitched. {clause}",
    }
    names = [name for name, _, _ in STAGES]
    parent = request
    for name, label, edge in STAGES[: names.index(through) + 1]:
        key = {"PMRun": pm, "Snapshot": f"snapshot:{pm}"}.get(
            name, f"{name.lower()}:{run_id}"
        )
        node = graph.merge_node(label, key, payloads[name])
        graph.add_edge(request if name == "PositionSync" else parent, node, edge)
        if name == "PMRun" and not degraded:
            verdicts = {item.ticker: "uphold" for item in approved}
            deliberation = graph.merge_node(
                "DeliberationRun",
                f"deliberation:{node.key}",
                {"verdicts": verdicts, "debates": verdicts, "vetoed_tickers": []},
            )
            graph.add_edge(node, deliberation, "DELIBERATED_BY")
        parent = request if name == "PositionSync" else node
    return request


def fire(
    graph: InMemoryGraphStore, telegram: TelegramPort, now: datetime, *, day: date = DAY
) -> ScheduledDispatchResult:
    """Run one dispatcher fire for ``day`` at ``now`` through the public seam."""
    return dispatch_with_human_answer(
        graph,
        as_of=day,
        now=now,
        telegram=telegram,
        universe_source=FakeUniverse({"sp500": (TICKER,)}),
    )


def order(ticker: str, quantity: int, price: str) -> OrderIntent:
    """Build one approved buy intent."""
    return OrderIntent(
        ticker=ticker,
        action="buy",
        quantity=quantity,
        est_price=Money(amount=Decimal(price)),
        rationale=Explanation(summary=f"fixture {ticker}"),
    )
