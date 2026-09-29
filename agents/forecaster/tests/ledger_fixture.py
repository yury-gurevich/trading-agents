"""A fixture ledger for the S241 barrier_scorecard tests.

Agent: forecaster
Role: write claims through the forecaster's own claim store and their settlements
      through its own settlement store (no bars: the scorecard is scored alone),
      and ask the bound forecaster for barrier_scorecard over the bus.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from agents.forecaster import ForecasterAgent
from agents.forecaster.domain.barrier_settlement import (
    CORPORATE_ACTION,
    VOID,
    Settlement,
)
from agents.forecaster.settlement_store import write_settlement
from agents.forecaster.tests.settlement_helpers import seed_claim
from contracts.forecaster import BarrierScorecardRequest, Scorecard
from kernel import AgentMessage, InProcessBus

if TYPE_CHECKING:
    from kernel import GraphStore

MODEL = "barrier-garch-v1"
CLIMATOLOGY = (0.287, 0.477, 0.236)  # EXP-018 Appendix R, primary set
DATES = tuple(date(2026, 9, 28) + timedelta(days=d) for d in range(4))
Row = tuple[str, int, tuple[float, float, float], str]
#: (ticker, date index, declared stop / target / neither, outcome), in the
#: scorecard's order: as_of, then claim key. 3 stop, 5 target, 2 neither.
LEDGER: tuple[Row, ...] = (
    ("AAPL", 0, (0.30, 0.50, 0.20), "target"),
    ("MSFT", 0, (0.25, 0.45, 0.30), "stop"),
    ("NVDA", 0, (0.35, 0.40, 0.25), "neither"),
    ("AAPL", 1, (0.28, 0.52, 0.20), "target"),
    ("MSFT", 1, (0.31, 0.44, 0.25), "target"),
    ("NVDA", 1, (0.20, 0.55, 0.25), "stop"),
    ("AAPL", 2, (0.33, 0.47, 0.20), "neither"),
    ("MSFT", 2, (0.27, 0.49, 0.24), "target"),
    ("NVDA", 2, (0.30, 0.46, 0.24), "stop"),
    ("AAPL", 3, (0.26, 0.51, 0.23), "target"),
)


def settle_row(graph: GraphStore, row: Row) -> None:
    """Write one claim and its settlement (a void is a corporate action)."""
    ticker, index, probabilities, outcome = row
    day = DATES[index]
    claim = seed_claim(graph, ticker=ticker, as_of=day, probabilities=probabilities)
    reason = CORPORATE_ACTION if outcome == VOID else None
    write_settlement(
        graph,
        claim,
        Settlement(outcome, reason, day + timedelta(days=14), 100.0, 1.0),
        settling_ref=f"market-data:{day.isoformat()}",
    )


def write_ledger(graph: GraphStore, rows: tuple[Row, ...] = LEDGER) -> None:
    """Write every row."""
    for row in rows:
        settle_row(graph, row)


def card(graph: GraphStore, model_id: str = MODEL) -> Scorecard:
    """The bound forecaster's barrier_scorecard for ``model_id``, over the bus."""
    bus = InProcessBus()
    ForecasterAgent(bus, graph=graph).bind()
    reply = bus.request(
        AgentMessage(
            sender="tester",
            recipient="forecaster",
            message_type="request",
            capability="barrier_scorecard",
            payload=BarrierScorecardRequest(model_id=model_id).model_dump(mode="json"),
        )
    )
    return Scorecard.model_validate(reply.payload)
