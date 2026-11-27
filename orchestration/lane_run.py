"""Test-lane run — place one lane run and drive its stages until nothing moves.

Agent: orchestration
Role: start a test-lane run (DL-328): refuse a graph that holds any run but a lane
      run, place a ``lane-`` RunRequest for the last closed NYSE session, run every
      stage once per round until a round advances nothing, and read the run's
      acceptance verdict the way the fleet's runs are read.
External I/O: none (the injected graph and stages do the I/O).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from agents.provider.domain.market_calendar import is_trading_session
from contracts.provider import RUN_REQUEST_LABEL
from kernel.work_loop import run_once
from kernel.work_loop_state import WorkLoopState
from orchestration.lane_guard import LaneRefusedError
from orchestration.packs.trading_acceptance import accept_run
from orchestration.start import place_run_request

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date

    from kernel import GraphStore
    from orchestration.lane_stages import LaneStage
    from orchestration.packs.trading_acceptance import TradingAcceptanceResult

LANE_RUN_PREFIX = "lane-"
NEW_YORK = ZoneInfo("America/New_York")
SESSION_SETTLED = time(17, 0)
"""A session counts as closed one hour after the 16:00 bell, once its bars settle."""


@dataclass(frozen=True)
class RoundReport:
    """What each stage advanced and failed in one round."""

    number: int
    advanced: dict[str, int]
    failed: dict[str, int]


@dataclass(frozen=True)
class LaneRunResult:
    """A lane run's id, its rounds and its acceptance verdict."""

    run_id: str
    rounds: tuple[RoundReport, ...]
    acceptance: TradingAcceptanceResult


def lane_run_id(now: datetime) -> str:
    """Return the run id for a lane run started at *now* (UTC, to the second)."""
    return f"{LANE_RUN_PREFIX}{now.astimezone(UTC):%Y%m%d-%H%M%S}"


def last_closed_session(
    now: datetime, *, is_session: Callable[[date], bool] = is_trading_session
) -> date:
    """Return the latest NYSE session whose bars have settled by *now*."""
    local = now.astimezone(NEW_YORK)
    day = local.date()
    if local.time() < SESSION_SETTLED:
        day -= timedelta(days=1)
    for _ in range(10):
        if is_session(day):
            return day
        day -= timedelta(days=1)
    raise LaneRefusedError(f"no NYSE session in the ten days before {local.date()}")


def refuse_foreign_runs(graph: GraphStore) -> None:
    """Refuse a graph holding any run that is not a lane run (a copy of the fleet's)."""
    foreign = sorted(
        str(node.props.get("run_id", node.key))
        for node in graph.list_nodes(RUN_REQUEST_LABEL)
        if not str(node.props.get("run_id", "")).startswith(LANE_RUN_PREFIX)
    )
    if foreign:
        raise LaneRefusedError(
            f"the lane graph holds {len(foreign)} run(s) that are not lane runs, "
            f"first {foreign[0]!r}: it is not the lane's own graph"
        )


def run_rounds(
    stages: tuple[LaneStage, ...], *, max_rounds: int
) -> tuple[RoundReport, ...]:
    """Run every stage once per round until a round advances nothing."""
    states = {stage.name: WorkLoopState() for stage in stages}
    reports: list[RoundReport] = []
    for number in range(1, max_rounds + 1):
        advanced: dict[str, int] = {}
        failed: dict[str, int] = {}
        for stage in stages:
            result = run_once(stage.find, stage.process, state=states[stage.name])
            stage.flush()
            advanced[stage.name] = result.advanced
            failed[stage.name] = result.failed
        reports.append(RoundReport(number, advanced, failed))
        if not any(advanced.values()):
            break
    return tuple(reports)


def run_lane(
    graph: GraphStore,
    stages: tuple[LaneStage, ...],
    *,
    tickers: tuple[str, ...],
    run_id: str,
    as_of: date,
    max_rounds: int,
) -> LaneRunResult:
    """Place one lane run on the lane graph, drive it, and read its verdict."""
    if not run_id.startswith(LANE_RUN_PREFIX):
        raise LaneRefusedError(f"a lane run id starts with {LANE_RUN_PREFIX!r}")
    refuse_foreign_runs(graph)
    place_run_request(graph, run_id=run_id, tickers=tickers, as_of=as_of)
    rounds = run_rounds(stages, max_rounds=max_rounds)
    return LaneRunResult(run_id, rounds, accept_run(graph, run_id))
