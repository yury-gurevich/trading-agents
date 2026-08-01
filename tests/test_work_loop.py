"""Tests for kernel.work_loop progress and sleep behavior."""

from __future__ import annotations

from kernel.work_loop import run_once, work_loop
from kernel.work_loop_policy import WorkLoopPolicy


class FakeClock:
    """Tiny test clock that advances when the loop sleeps."""

    def __init__(self) -> None:
        self.current = 0.0
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.current += seconds


def _policy(
    *,
    poll: float = 1.0,
    base: float = 1.0,
    ceiling: float = 4.0,
    attempts: int = 5,
) -> WorkLoopPolicy:
    return WorkLoopPolicy(
        poll_interval_seconds=poll,
        backoff_base_seconds=base,
        backoff_multiplier=2.0,
        backoff_ceiling_seconds=ceiling,
        max_attempts_before_quarantine=attempts,
    )


def test_run_once_processes_every_pending_item() -> None:
    """DL-08: a productive pass reports advanced work, not merely found work."""
    processed: list[int] = []
    pending = [1, 2, 3]

    def process(item: int) -> None:
        processed.append(item)
        pending.remove(item)

    result = run_once(lambda: list(pending), process)

    assert processed == [1, 2, 3]
    assert result.found == 3
    assert result.advanced == 3


def test_run_once_returns_zero_when_no_pending() -> None:
    """DL-08: an empty graph-pull pass remains idle."""
    processed: list[int] = []
    result = run_once(list, processed.append)

    assert processed == []
    assert result.found == 0
    assert result.advanced == 0


def test_work_loop_sleeps_after_no_progress_pass() -> None:
    """DL-79 / DRIFT-030: found-but-not-advanced work sleeps before retry."""
    pending = ["poison"]
    attempts: list[str] = []
    clock = FakeClock()

    results = work_loop(
        lambda: list(pending),
        attempts.append,
        policy=_policy(poll=1.0, base=3.0),
        sleep=clock.sleep,
        clock=clock.now,
        max_iterations=1,
    )

    assert attempts == ["poison"]
    assert clock.sleeps == [1.0]
    assert results[0].found == 1
    assert results[0].advanced == 0
    assert results[0].no_progress == 1


def test_work_loop_sleeps_after_empty_pass() -> None:
    """DL-08: empty-pass sleep behaviour is unchanged."""
    clock = FakeClock()

    results = work_loop(
        list,
        lambda item: None,
        policy=_policy(poll=1.0),
        sleep=clock.sleep,
        clock=clock.now,
        max_iterations=1,
    )

    assert clock.sleeps == [1.0]
    assert results[0].found == 0
    assert results[0].advanced == 0


def test_work_loop_does_not_sleep_after_productive_pass() -> None:
    """DL-08: productive graph-pull passes continue without idle sleep."""
    pending = ["ready"]
    clock = FakeClock()

    def process(item: str) -> None:
        pending.remove(item)

    results = work_loop(
        lambda: list(pending),
        process,
        policy=_policy(poll=1.0),
        sleep=clock.sleep,
        clock=clock.now,
        max_iterations=1,
    )

    assert clock.sleeps == []
    assert results[0].advanced == 1


def test_run_once_contains_exception_and_continues_siblings() -> None:
    """DRIFT-030: one raised item is contained and sibling work still advances."""
    pending = ["poison", "healthy"]

    def process(item: str) -> None:
        if item == "poison":
            raise RuntimeError("boom")
        pending.remove(item)

    result = run_once(lambda: list(pending), process, policy=_policy(base=3.0))

    assert result.failed == 1
    assert result.advanced == 1
    assert result.next_retry_delay == 3.0
    assert pending == ["poison"]


def test_exception_can_quarantine_without_retry_delay() -> None:
    """DRIFT-030: an exception at the attempt cap becomes quarantine, not retry."""

    def process(item: str) -> None:
        raise RuntimeError(f"{item} failed")

    result = run_once(
        lambda: ["poison"],
        process,
        policy=_policy(attempts=1),
    )

    assert result.failed == 1
    assert result.quarantined == 1
    assert result.next_retry_delay is None


def test_work_loop_poll_interval_override_uses_resolved_policy() -> None:
    """DRIFT-030: explicit caller poll intervals still override the tunable default."""
    clock = FakeClock()

    work_loop(
        list,
        lambda item: None,
        policy=_policy(poll=99.0),
        poll_interval=2.0,
        sleep=clock.sleep,
        clock=clock.now,
        max_iterations=1,
    )

    assert clock.sleeps == [2.0]
