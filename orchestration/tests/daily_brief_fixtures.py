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
from contracts.analyst import RecommendationSet
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent, OrderIntentSet, RejectedOrder
from contracts.position_sync import POSITION_SYNC_EDGE, POSITION_SYNC_PHASE
from contracts.provider import RUN_REQUEST_LABEL, DataQualityTrace, MarketData
from contracts.run_posture import RUN_POSTURE_DEGRADED
from contracts.scanner import Candidate, CandidateSet, FilterTrace
from orchestration.scheduled_dispatch_human import dispatch_with_human_answer
from orchestration.start import place_run_request
from orchestration.tests.shadow_book_helpers import bar, recommendation

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore, Node
    from orchestration.scheduled_dispatch import ScheduledDispatchResult
    from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram

DAY = date(2026, 9, 25)
PREVIOUS_DAY = date(2026, 9, 24)
# sched-2026-09-25's reporter clause, as measured (spec row 8).
CLAUSE = "vs SPY: -0.43 pts over 33 sessions at 21% invested"
# The chain in the order walk_chain reads it; the head sync marker is a MonitorRun.
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
TICKER = "AAPL"


def at(hour: int, minute: int, day: date = DAY) -> datetime:
    """Return a UTC fire time on the given day."""
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=UTC)


def pm_key(day: date) -> str:
    """Return the fixture PMRun key for a scheduled day."""
    return f"pm-run-{day:%Y%m%d}"


def performance(equity_cents: float, *, sessions: float = 33.0) -> dict[str, float]:
    """Return a performance group with the keys the reporter writes."""
    return {
        "portfolio_return_pct": 1.98,
        "benchmark_return_pct": 3.1,
        "exposure_matched_return_pct": 2.41,
        "excess_return_pct": -0.43,
        "average_exposure_pct": 21.0,
        "max_drawdown_pct": -1.2,
        "rolling_portfolio_return_pct": 0.5,
        "rolling_exposure_matched_return_pct": 0.9,
        "rolling_excess_return_pct": -0.4,
        "performance_sessions": sessions,
        "performance_gap_sessions": 0.0,
        "equity_cents": equity_cents,
    }


def metrics_with(group: object) -> dict[str, object]:
    """Return a Snapshot metrics blob carrying ``group`` as its performance."""
    blob: dict[str, object] = {
        "portfolio": {"positions_opened": 0.0, "positions_closed": 0.0},
        "signal": {"recommendation_count": 1.0},
        "regime": {},
    }
    if group is not None:
        blob["performance"] = group
    return blob


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
) -> Node:
    """Place one scheduled run and write its chain up to ``through``."""
    run_id = f"sched-{day.isoformat()}"
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
    blob = metrics_with(performance(10_197_632.0)) if metrics is None else metrics
    names = [name for name, _, _ in STAGES]
    parent = request
    for name, label, edge in STAGES[: names.index(through) + 1]:
        key, props = _stage(name, run_id, day, approved)
        if name == "PMRun":
            props["created_at"] = pm_created
        if name == "Snapshot":
            props = {
                "run_id": pm_key(day),
                "metrics": blob,
                "headline_summary": "0 positions opened; 0 closed; "
                f"1 recommendations stitched. {clause}",
            }
        node = graph.merge_node(label, key, props)
        graph.add_edge(request if name == "PositionSync" else parent, node, edge)
        if name == "PMRun" and not degraded:
            _deliberation(graph, node, approved)
        if name != "PositionSync":
            parent = node
    return request


def fire(
    graph: InMemoryGraphStore,
    telegram: FakeTelegram,
    now: datetime,
    *,
    day: date = DAY,
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


def _stage(
    name: str, run_id: str, day: date, approved: tuple[OrderIntent, ...]
) -> tuple[str, dict[str, object]]:
    key = pm_key(day) if name == "PMRun" else f"{name.lower()}:{run_id}"
    if name == "Snapshot":
        key = f"snapshot:{pm_key(day)}"
    return key, _PROPS[name](run_id, day, approved)


def _deliberation(
    graph: InMemoryGraphStore, pm_run: Node, approved: tuple[OrderIntent, ...]
) -> None:
    node = graph.merge_node(
        "DeliberationRun",
        f"deliberation:{pm_run.key}",
        {
            "verdicts": {item.ticker: "uphold" for item in approved},
            "debates": {item.ticker: "fixture" for item in approved},
            "vetoed_tickers": [],
        },
    )
    graph.add_edge(pm_run, node, "DELIBERATED_BY")


def _provenance(run_id: str, agent: str) -> Provenance:
    return Provenance(run_id=run_id, source_agent=agent)


def _sync(run_id: str, day: date, approved: tuple[OrderIntent, ...]) -> dict:
    del run_id, day, approved
    return {"phase": POSITION_SYNC_PHASE, "position_book_status": "fresh"}


def _market(run_id: str, day: date, approved: tuple[OrderIntent, ...]) -> dict:
    del approved
    market = MarketData(
        bars=(bar(TICKER, day, 100.0),),
        quality=DataQualityTrace(requested=1, returned=1),
        provenance=_provenance(run_id, "provider"),
    )
    return {"snapshot": market.model_dump(mode="json"), "tickers": [TICKER]}


def _scan(run_id: str, day: date, approved: tuple[OrderIntent, ...]) -> dict:
    del day, approved
    candidates = CandidateSet(
        run_id=run_id,
        candidates=(Candidate(ticker=TICKER, rank=1, score=1.0, survived_filters=()),),
        filter_trace=FilterTrace(universe_size=1, evaluated=1),
        explanation=Explanation(summary="fixture scan"),
        provenance=_provenance(run_id, "scanner"),
    )
    return {"candidate_set": candidates.model_dump(mode="json")}


def _analyst(run_id: str, day: date, approved: tuple[OrderIntent, ...]) -> dict:
    del day, approved
    recommendations = RecommendationSet(
        run_id=run_id,
        recommendations=(recommendation(TICKER),),
        rejections=(),
        explanation=Explanation(summary="fixture analyst"),
        provenance=_provenance(run_id, "analyst"),
    )
    return {"recommendation_set": recommendations.model_dump(mode="json")}


def _pm(run_id: str, day: date, approved: tuple[OrderIntent, ...]) -> dict:
    del run_id
    rejected = () if approved else (RejectedOrder(ticker=TICKER, reason="full"),)
    intents = OrderIntentSet(
        run_id=pm_key(day),
        approved=approved,
        rejected=rejected,
        explanation=Explanation(summary="fixture pm"),
        provenance=_provenance(pm_key(day), "portfolio_manager"),
    )
    return {"order_intent_set": intents.model_dump(mode="json")}


def _execution(run_id: str, day: date, approved: tuple[OrderIntent, ...]) -> dict:
    del run_id, day
    return {
        "submitted": len(approved),
        "rejected": 0,
        "deliberation_posture": "advisory",
        "deliberation_status": "applied" if approved else "not_required",
    }


def _monitor(run_id: str, day: date, approved: tuple[OrderIntent, ...]) -> dict:
    del run_id, day, approved
    return {"positions_checked": 10, "closes": 0, "holds": 10}


def _snapshot(run_id: str, day: date, approved: tuple[OrderIntent, ...]) -> dict:
    del run_id, day, approved
    return {}


_PROPS = {
    "PositionSync": _sync,
    "MarketData": _market,
    "ScanRun": _scan,
    "AnalystRun": _analyst,
    "PMRun": _pm,
    "ExecutionRun": _execution,
    "MonitorRun": _monitor,
    "Snapshot": _snapshot,
}
