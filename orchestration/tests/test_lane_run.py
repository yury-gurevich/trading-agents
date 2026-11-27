"""Lane ids, sessions, graph refusal and round termination.

Agent: orchestration
Role: prove DL-328 D4 and D5 with memory stores and counting work pairs.
External I/O: none.
"""

from datetime import UTC, date, datetime

import pytest

from kernel import InMemoryGraphStore
from orchestration.lane_guard import LaneRefusedError
from orchestration.lane_run import (
    lane_run_id,
    last_closed_session,
    refuse_foreign_runs,
    run_lane,
    run_rounds,
)
from orchestration.lane_stages import LaneStage


def test_a_lane_run_id_is_its_start_in_utc_to_the_second() -> None:
    """DL-328 D4: run ids identify the UTC start to the second."""
    assert (
        lane_run_id(datetime(2026, 11, 27, 14, 5, 9, tzinfo=UTC))
        == "lane-20261127-140509"
    )


@pytest.mark.parametrize(
    ("instant", "expected"),
    [
        ("2026-11-25T21:59:00+00:00", "2026-11-24"),
        ("2026-11-25T22:00:00+00:00", "2026-11-25"),
        ("2026-11-27T03:00:00+00:00", "2026-11-25"),
        ("2026-11-29T03:00:00+00:00", "2026-11-27"),
        ("2026-12-01T03:00:00+00:00", "2026-11-30"),
    ],
)
def test_the_session_is_the_last_one_settled_in_new_york(
    instant: str, expected: str
) -> None:
    """DL-328 D4: settlement at 17:00 NY observes holidays and weekends."""
    assert last_closed_session(datetime.fromisoformat(instant)) == date.fromisoformat(
        expected
    )


def test_no_session_in_ten_days_is_refused() -> None:
    """DL-328 D4: a calendar with no recent session fails explicitly."""
    with pytest.raises(LaneRefusedError, match="no NYSE session"):
        last_closed_session(
            datetime(2026, 11, 27, tzinfo=UTC), is_session=lambda _: False
        )


def test_a_graph_holding_a_fleet_run_is_refused() -> None:
    """DL-328 D4: missing and scheduled ids are both foreign graph evidence."""
    graph = InMemoryGraphStore()
    graph.merge_node("RunRequest", "run-request:lane-1", {"run_id": "lane-1"})
    refuse_foreign_runs(graph)
    graph.merge_node("RunRequest", "run-request:x", {})
    graph.merge_node("RunRequest", "run-request:sched", {"run_id": "sched-2026-11-25"})
    with pytest.raises(LaneRefusedError, match=r"2 run\(s\).*first 'run-request:x'"):
        refuse_foreign_runs(graph)


def test_a_run_id_without_the_lane_prefix_is_refused() -> None:
    """DL-328 D4: reject foreign ids before placing work."""
    graph = InMemoryGraphStore()
    with pytest.raises(LaneRefusedError, match="starts with 'lane-'"):
        run_lane(
            graph,
            (),
            tickers=("AAPL",),
            run_id="sched-2026-11-25",
            as_of=date(2026, 11, 25),
            max_rounds=1,
        )
    assert graph.list_nodes("RunRequest") == ()


class CountingStage:
    """Offer one item at a time so progress is measured independently per round."""

    def __init__(self, name: str, count: int, *, raises: bool = False) -> None:
        self.name, self.remaining, self.raises = name, count, raises
        self.flushes = 0

    def find(self) -> list[int]:
        return [self.remaining] if self.remaining else []

    def process(self, item: int) -> None:
        if self.raises:
            raise ValueError("planted work failure")
        assert item == self.remaining
        self.remaining -= 1

    def flush(self) -> None:
        self.flushes += 1

    def stage(self) -> LaneStage:
        return LaneStage(self.name, self.find, self.process, self.flush)


def test_rounds_run_until_one_advances_nothing() -> None:
    """DL-328 D5: retain retries, flush each round, stop on no progress."""
    counters = (
        CountingStage("three", 3),
        CountingStage("one", 1),
        CountingStage("raising", 1, raises=True),
    )
    rounds = run_rounds(tuple(c.stage() for c in counters), max_rounds=12)
    assert [r.number for r in rounds] == [1, 2, 3, 4]
    assert [r.advanced for r in rounds] == [
        {"three": 1, "one": 1, "raising": 0},
        {"three": 1, "one": 0, "raising": 0},
        {"three": 1, "one": 0, "raising": 0},
        {"three": 0, "one": 0, "raising": 0},
    ]
    assert rounds[0].failed == {"three": 0, "one": 0, "raising": 1}
    assert [c.flushes for c in counters] == [4, 4, 4]


def test_rounds_stop_at_the_round_limit() -> None:
    """DL-328 D5: perpetual available work cannot exceed the caller's limit."""
    stage = CountingStage("many", 1000)
    rounds = run_rounds((stage.stage(),), max_rounds=2)
    assert [r.advanced for r in rounds] == [{"many": 1}, {"many": 1}]
    assert stage.remaining == 998
    assert stage.flushes == 2
