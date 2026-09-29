"""ActivationReplay's in-flight and failure paths (S244, DL-249 D3).

Agent: master
Role: prove a refusal is never remembered, a waiter on a failed first attempt
      tries afresh, and another type is refused while the first is in flight.
External I/O: none (threads and events only).
"""

from __future__ import annotations

import threading

import pytest

from agents.master.activation_replay import ActivationReplay, ReplayConflictError


def test_a_refusal_is_never_remembered() -> None:
    """MST-IDM-03: a failed activation leaves nothing, so the resend is decided anew."""
    replay = ActivationReplay(300.0)

    def refuse() -> dict[str, object]:
        raise ValueError("credential test(s) failed")

    with pytest.raises(ValueError, match="credential"):
        replay.answer("boot-1", "scanner", refuse)

    assert replay.answer("boot-1", "scanner", lambda: {"instance_id": "i-2"}) == {
        "instance_id": "i-2"
    }


def test_a_waiter_on_a_failed_first_attempt_mints_its_own() -> None:
    """MST-IDM-03: a concurrent duplicate never inherits the first attempt's refusal."""
    replay = ActivationReplay(300.0)
    first_started = threading.Event()
    release_first = threading.Event()
    outcomes: dict[str, object] = {}

    def failing() -> dict[str, object]:
        first_started.set()
        release_first.wait(timeout=5)
        raise ValueError("graph unavailable")

    def first() -> None:
        try:
            replay.answer("boot-1", "scanner", failing)
        except ValueError as exc:
            outcomes["first"] = str(exc)

    def second() -> None:
        outcomes["second"] = replay.answer("boot-1", "scanner", lambda: {"id": "i-2"})

    one = threading.Thread(target=first)
    one.start()
    assert first_started.wait(timeout=5)
    two = threading.Thread(target=second)
    two.start()
    release_first.set()
    one.join(timeout=5)
    two.join(timeout=5)

    assert outcomes == {"first": "graph unavailable", "second": {"id": "i-2"}}


def test_another_type_is_refused_while_the_first_is_in_flight() -> None:
    """MST-IDM-03 / MST-NEV-02: an in-flight boot id is already bound to its type."""
    replay = ActivationReplay(300.0)
    started = threading.Event()
    release = threading.Event()

    def slow() -> dict[str, object]:
        started.set()
        release.wait(timeout=5)
        return {"instance_id": "scanner:1"}

    worker = threading.Thread(target=lambda: replay.answer("boot-1", "scanner", slow))
    worker.start()
    assert started.wait(timeout=5)
    try:
        with pytest.raises(ReplayConflictError, match="another agent type"):
            replay.answer("boot-1", "analyst", lambda: {"instance_id": "analyst:1"})
    finally:
        release.set()
        worker.join(timeout=5)


def test_a_replayed_answer_is_a_copy() -> None:
    """MST-IDM-03: a caller mutating its answer cannot change what the next gets."""
    replay = ActivationReplay(300.0)
    first = replay.answer("boot-1", "scanner", lambda: {"config": {"K": "v"}})
    first["config"] = {}

    assert replay.answer("boot-1", "scanner", dict) == {"config": {"K": "v"}}
