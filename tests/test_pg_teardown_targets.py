"""A run-scoped teardown collects every artifact and proves none survived (DL-94).

Agent: tooling
Role: pin the label split, the container-owned pass the edge walk cannot perform, and
      the non-zero exit that stops a silent under-delete reading as success.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scripts.pg_teardown import _run_id_teardown
from scripts.pg_teardown_targets import (
    PROTECTED_LABELS,
    RUN_ARTIFACT_LABELS,
    RUN_CONTAINER_LABELS,
    collect,
    protected_neighbours,
    survivors,
)

if TYPE_CHECKING:
    import pytest

RUN_ID = "sched-2026-08-07"
MONITOR_RUN = ("MonitorRun", "monitor-run-fddb027fd2e24664a0caeea2f3972428")
POSITION_CHECK = ("PositionCheck", f"{MONITOR_RUN[1]}:broker:WFC:348:8639:check")


class FakeCursor:
    """Scripted psycopg cursor that records every statement it is given."""

    def __init__(
        self,
        fetchall: list[list[tuple[str, str]]] | None = None,
        fetchone: list[tuple[int]] | None = None,
        rowcounts: dict[str, int] | None = None,
    ) -> None:
        self._fetchall = list(fetchall or [])
        self._fetchone = list(fetchone or [])
        self._rowcounts = dict(rowcounts or {})
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.rowcount = 0

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((query, params))
        if "DELETE FROM edges" in query:
            self.rowcount = self._rowcounts.get("edges", 0)
        elif "DELETE FROM nodes" in query:
            self.rowcount = self._rowcounts.get("nodes", 0)

    def executemany(self, query: str, params: Any) -> None:
        self.calls.append((query, tuple(params)))

    def fetchall(self) -> list[tuple[str, str]]:
        return self._fetchall.pop(0) if self._fetchall else []

    def fetchone(self) -> tuple[int]:
        return self._fetchone.pop(0) if self._fetchone else (0,)


def _walk_params(cursor: FakeCursor) -> tuple[Any, ...]:
    return next(p for q, p in cursor.calls if "WITH RECURSIVE target" in q)


def test_broker_state_is_never_a_run_artifact() -> None:
    """DL-94: the label list doubles as a traversal barrier, so the sets stay disjoint.

    `BrokerStopOrder` reads exactly like a run artifact and is the bridge
    `Fill -> BrokerStopOrder -> Position`. Listing it deletes the live book.
    """
    assert set(PROTECTED_LABELS).isdisjoint(RUN_ARTIFACT_LABELS)
    for label in ("Position", "Fill", "BrokerStopOrder", "BrokerOrderStatus"):
        assert label in PROTECTED_LABELS
        assert label not in RUN_ARTIFACT_LABELS


def test_labels_dl94_found_orphaned_are_collectable() -> None:
    """DL-94: the five labels the pipeline writes that the old list never named."""
    for label in (
        "Rejection",
        "SentimentReading",
        "PositionCheck",
        "DeliberationRun",
        "BrokerPositionSnapshot",
    ):
        assert label in RUN_ARTIFACT_LABELS


def test_run_containers_are_themselves_artifacts() -> None:
    """A container whose children are collected must itself be deletable."""
    assert set(RUN_CONTAINER_LABELS) <= set(RUN_ARTIFACT_LABELS)


def test_walk_never_seeds_or_traverses_protected_labels() -> None:
    """The barrier is explicit in the SQL, not incidental to the edge topology."""
    cursor = FakeCursor(fetchall=[[]])
    collect(cursor, RUN_ID)
    params = _walk_params(cursor)
    assert list(PROTECTED_LABELS) in params
    traversable = params[-1]
    assert all(label not in traversable for label in PROTECTED_LABELS)


def test_collect_gathers_rows_the_walk_cannot_reach() -> None:
    """A `PositionCheck`'s only edge is to `Position`, so only the key prefix finds it.

    Measured on the live spine: `PositionCheck -> Position` is its sole edge type, so
    widening the walk's label list — DL-94's proposed fix — reaches none of them.
    """
    cursor = FakeCursor(fetchall=[[MONITOR_RUN], [POSITION_CHECK]])
    found = collect(cursor, RUN_ID)
    assert POSITION_CHECK in found
    owned_query, owned_params = cursor.calls[-1]
    assert "LIKE ANY" in owned_query
    assert f"{MONITOR_RUN[1]}:%" in owned_params[-1]


def test_collect_skips_the_owned_pass_when_no_container_was_reached() -> None:
    """No container means no `<key>:%` pattern, and no second query to run."""
    cursor = FakeCursor(fetchall=[[("Snapshot", "snapshot:x")]])
    assert collect(cursor, RUN_ID) == [("Snapshot", "snapshot:x")]
    assert len(cursor.calls) == 1


def test_survivors_reports_stamped_rows_that_outlived_the_delete() -> None:
    cursor = FakeCursor(fetchall=[[POSITION_CHECK]])
    assert survivors(cursor, RUN_ID, [MONITOR_RUN]) == [POSITION_CHECK]


def test_protected_neighbours_counts_spared_rows_the_stamp_cannot_see() -> None:
    """A spared `Fill` is keyed `exit:<ref>:WFC:sell` and carries no run stamp.

    Counting by stamp reports 0 while ten broker rows were deliberately kept —
    measured on the live spine for `sched-2026-08-07`.
    """
    cursor = FakeCursor(fetchone=[(10,)])
    assert protected_neighbours(cursor, [MONITOR_RUN]) == 10
    query, params = cursor.calls[0]
    assert "unnest" in query
    assert list(PROTECTED_LABELS) in params


def test_protected_neighbours_of_nothing_queries_nothing() -> None:
    cursor = FakeCursor()
    assert protected_neighbours(cursor, []) == 0
    assert cursor.calls == []


def test_teardown_exits_non_zero_and_names_every_orphan(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DL-94's actual defect: a count printed, exit 0, and 41 rows still stamped."""
    cursor = FakeCursor(
        fetchall=[[MONITOR_RUN], [], [POSITION_CHECK]],
        fetchone=[(0,)],
        rowcounts={"edges": 3, "nodes": 1},
    )
    assert _run_id_teardown(cursor, RUN_ID) == 1
    out = capsys.readouterr().out
    assert "ORPHANS REMAIN" in out
    assert POSITION_CHECK[1] in out


def test_teardown_exits_zero_and_reports_what_it_deliberately_kept(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Protected rows are kept loudly, so `deleted_nodes` is never the whole story."""
    cursor = FakeCursor(
        fetchall=[[MONITOR_RUN], [POSITION_CHECK], []],
        fetchone=[(7,)],
        rowcounts={"edges": 5, "nodes": 2},
    )
    assert _run_id_teardown(cursor, RUN_ID) == 0
    out = capsys.readouterr().out
    assert "deleted_edges=5 deleted_nodes=2 protected_kept=7" in out
    assert "ORPHANS REMAIN" not in out


def test_teardown_of_an_unmatched_run_deletes_nothing() -> None:
    cursor = FakeCursor(fetchall=[[], []], fetchone=[(0,)])
    assert _run_id_teardown(cursor, RUN_ID) == 0
    assert not any("DELETE FROM nodes" in q for q, _ in cursor.calls)
