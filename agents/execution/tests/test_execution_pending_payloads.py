"""S252 A6/A7: execution fetches unexecuted candidates while retaining its grace wait.

Agent: execution
Role: pin pending submission and run-start sync payload costs without any broker work.
External I/O: none (in-memory graph).
"""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING

from tests.poll_payload_remaining import seed_execution, seed_execution_sync
from tests.poll_payload_support import NOW, FrozenDatetime, PayloadSpy

from agents.execution import poll
from agents.execution.settings import ExecutionSettings

if TYPE_CHECKING:
    import pytest


def test_a_waiting_pm_run_is_fetched_until_its_grace_expires(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EXEC-TRG-08 / EXEC-NEV-06: buys wait inside grace, return after it;
    executed b is never fetched.
    """
    graph = PayloadSpy()
    seed_execution(graph)
    graph.arm("PMRun", "EXECUTED_BY")
    settings = ExecutionSettings()
    monkeypatch.setattr(poll, "datetime", FrozenDatetime)

    assert [node.key for node in poll.find_pending(graph, settings=settings)] == [
        "c",
        "a",
    ]
    assert graph.fetched == ["c", "a", "waiting"]
    graph.fetched.clear()
    after = NOW + timedelta(seconds=settings.deliberation_grace_seconds)
    monkeypatch.setattr(poll, "datetime", SimpleNamespace(now=lambda **_: after))

    assert [node.key for node in poll.find_pending(graph, settings=settings)] == [
        "c",
        "a",
        "waiting",
    ]
    assert graph.fetched == ["c", "a", "waiting"]


def test_position_sync_fetches_only_requests_without_a_snapshot_edge() -> None:
    """EXEC-TRG-07: the REFRESHES edge excludes a completed request before its
    props are read.
    """
    graph = PayloadSpy()
    seed_execution_sync(graph)
    graph.arm("RunRequest", "REFRESHES")

    assert [node.key for node in poll.find_pending_position_sync(graph)] == ["c", "a"]
    assert graph.fetched == ["c", "a"]
