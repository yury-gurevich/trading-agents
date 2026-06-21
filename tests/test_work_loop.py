"""Tests for kernel.work_loop.run_once (the testable single pass)."""

from __future__ import annotations

from kernel.work_loop import run_once


def test_run_once_processes_every_pending_item() -> None:
    processed: list[int] = []
    count = run_once(lambda: [1, 2, 3], processed.append)
    assert processed == [1, 2, 3]
    assert count == 3


def test_run_once_returns_zero_when_no_pending() -> None:
    processed: list[int] = []
    count = run_once(list, processed.append)
    assert processed == []
    assert count == 0
