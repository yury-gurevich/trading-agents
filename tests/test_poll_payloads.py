"""No graph-pull poll downloads payloads to find its work (S242 A4/A8, DL-246).

Agent: tooling
Role: run every find_pending in scope on a store that fails when the poll lists its
      own label with props or walks its processed edge per node, and pin which of
      its label's nodes it then fetches: the ones without that edge, never the rest.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

import ast
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from tests.poll_payload_fixtures import CASES as ORIGINAL_CASES
from tests.poll_payload_fixtures import NOW
from tests.poll_payload_remaining import REMAINING_CASES
from tests.poll_payload_support import FrozenDatetime, PayloadSpy

from agents.analyst import poll as analyst_poll
from agents.deliberator.store import find_pending as find_pending_deliberation
from agents.execution import poll as execution_poll
from agents.forecaster import poll as forecaster_poll
from agents.forecaster.settlement_pass import find_pending_settlement
from agents.monitor import poll as monitor_poll
from agents.monitor.position_sync import find_pending_position_sync
from agents.portfolio_manager import poll as pm_poll
from agents.provider import poll as provider_poll
from agents.provider.barrier_history import find_pending_barrier_history
from agents.reporter import poll as reporter_poll
from agents.scanner import poll as scanner_poll

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.poll_payload_fixtures import PollCase

    from kernel import GraphStore, Node

CASES = (*ORIGINAL_CASES, *REMAINING_CASES)
FINDERS: dict[str, Callable[[GraphStore], list[Node]]] = {
    "provider": provider_poll.find_pending,
    "scanner": scanner_poll.find_pending,
    "analyst": analyst_poll.find_pending,
    "portfolio_manager": pm_poll.find_pending,
    "monitor": monitor_poll.find_pending,
    "reporter": reporter_poll.find_pending,
    "barrier_history": partial(find_pending_barrier_history, now=NOW),
    "forecaster": partial(forecaster_poll.find_pending, now=NOW),
    "settlement": partial(find_pending_settlement, now=NOW),
    "deliberator": find_pending_deliberation,
    "execution": execution_poll.find_pending,
    "execution_sync": execution_poll.find_pending_position_sync,
    "monitor_sync": find_pending_position_sync,
}


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_no_poll_downloads_a_payload_to_find_its_work(
    case: PollCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PROV-TRG-02 / PROV-TRG-04 / SCAN-TRG-02 / ANLZ-TRG-02 / PM-TRG-02 / MON-TRG-02 /
    RPT-TRG-02 / FORE-TRG-01 / DLIB-TRG-01 / EXEC-TRG-07 / EXEC-TRG-08
    (DL-246, DL-261): a poll finds its pending work by key and edge; it
    fetches only the nodes that lack its processed edge, in list order. (Also cited
    before S251 as SCAN-TRG-03 / ANLZ-TRG-03 / PM-TRG-03 / MON-TRG-04 / RPT-TRG-04.)"""
    graph = PayloadSpy()
    case.seed(graph)
    graph.arm(case.label, case.edge)
    monkeypatch.setattr(execution_poll, "datetime", FrozenDatetime)

    found = FINDERS[case.name](graph)

    assert tuple(node.key for node in found) == case.pending
    assert tuple(graph.fetched) == case.candidates


def test_the_barrier_backlog_is_never_fetched() -> None:
    """PROV-TRG-04 / PROV-TRG-02 (DL-241 D11, DL-246 D2): 71 stale runs with no
    BarrierHistory and one current run: only the current run's node is ever read."""
    case = next(case for case in CASES if case.name == "barrier_history")
    graph = PayloadSpy()
    case.seed(graph)
    graph.arm(case.label, case.edge)

    found = find_pending_barrier_history(graph, now=NOW)

    assert [node.key for node in found] == ["current"]
    assert graph.fetched == ["current"]


def _finder_functions(root: Path) -> set[tuple[str, str]]:
    """Read module-level finders; work aggregators, methods and nested defs are
    excluded.
    """
    return {
        (".".join(path.relative_to(root.parent).with_suffix("").parts), item.name)
        for path in root.rglob("*.py")
        for item in ast.parse(path.read_text(encoding="utf-8")).body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and (item.name == "find_pending" or item.name.startswith("find_pending_"))
        and item.name != "find_pending_work"
    }


def _assert_finder_cases(discovered: set[tuple[str, str]]) -> None:
    """Require one executable payload case for every discovered function identity."""
    names = [case.name for case in CASES]
    assert len(names) == len(set(names)), "duplicate payload cases"
    assert set(names) == set(FINDERS), "payload cases and callables disagree"
    covered = set()
    for name in names:
        finder = FINDERS[name]
        target = finder.func if isinstance(finder, partial) else finder
        covered.add((target.__module__, target.__name__))
    assert len(covered) == len(names), "duplicate finder identities"
    assert discovered == covered, (
        f"finders missing cases: {sorted(discovered - covered)}"
    )


def test_the_payload_cases_cover_every_finder() -> None:
    """FORE-TRG-01 / DLIB-TRG-01 / EXEC-TRG-07 / EXEC-TRG-08 / MON-TRG-02:
    S252 A8: every module-level pending finder has one executable payload case.
    """
    _assert_finder_cases(
        _finder_functions(Path(__file__).resolve().parents[1] / "agents")
    )


def test_an_uncovered_fourteenth_finder_is_rejected(tmp_path: Path) -> None:
    """FORE-TRG-01 / DLIB-TRG-01 / EXEC-TRG-08 / MON-TRG-02: a new uncased finder
    is red.
    """
    root = tmp_path / "agents"
    root.mkdir()
    (root / "uncovered.py").write_text(
        "def find_pending_extra(graph):\n    return []\n"
    )
    discovered = _finder_functions(Path(__file__).resolve().parents[1] / "agents")
    with pytest.raises(AssertionError, match=r"agents\.uncovered.*find_pending_extra"):
        _assert_finder_cases(discovered | _finder_functions(root))


def test_discovery_excludes_methods_nested_functions_and_work_aggregators(
    tmp_path: Path,
) -> None:
    """FORE-TRG-01 / EXEC-TRG-08 / MON-TRG-02: source discovery follows the
    declared rule.
    """
    root = tmp_path / "agents"
    root.mkdir()
    (root / "sample.py").write_text(
        "def find_pending(graph):\n    def find_pending_nested(): pass\n"
        "async def find_pending_sync(graph): pass\n"
        "def find_pending_work(graph): pass\n"
        "class Worker:\n    def find_pending(self): pass\n"
    )
    assert _finder_functions(root) == {
        ("agents.sample", "find_pending"),
        ("agents.sample", "find_pending_sync"),
    }
