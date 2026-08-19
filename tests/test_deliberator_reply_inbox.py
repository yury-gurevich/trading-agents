"""Deliberator shared reply-inbox routing tests.

Agent: deliberator
Role: prove concurrent manager reply waits keep sibling replies correlated.
External I/O: none.
"""

from __future__ import annotations

import threading
import time

import pytest
from tests.bus_azure_receiver_helpers import FakeReceiver, RawMessage
from tests.deliberator_correlated_peer_helpers import raw_ready

from agents.deliberator.servicebus_reply_inbox import (
    REPLY_RECEIVE_SLICE_SECONDS,
    ServiceBusReplyInbox,
)
from kernel.bus_azure_ready import (
    ORPHANED_READY_EVENT_REASON,
    CorrelatedReadyEvent,
    CorrelatedReadyEventTimeoutError,
)


def test_reply_inbox_stashes_pending_sibling_without_dead_letter() -> None:
    """DLIB-DEP-02 / DLIB-NEV-06: sibling replies are not stale orphans."""
    inbox = ServiceBusReplyInbox()
    sibling = raw_ready("reply-b", "request-b")
    mine = raw_ready("reply-a", "request-a")
    receiver = FakeReceiver([sibling, mine])

    with inbox.expecting("request-a"), inbox.expecting("request-b"):
        result_a = inbox.receive(
            receiver,
            correlation_id="request-a",
            deadline=1.0,
            now=lambda: 0.0,
        )
        result_b = inbox.receive(
            receiver,
            correlation_id="request-b",
            deadline=1.0,
            now=lambda: 0.0,
        )

    assert result_a.event["ref"] == "reply-a"
    assert result_b.event["ref"] == "reply-b"
    assert result_a.orphan_count == 0
    assert result_b.orphan_count == 0
    assert receiver.completed == [sibling, mine]
    assert receiver.dead_lettered == []


def test_reply_inbox_poll_slice_observes_late_stashed_sibling() -> None:
    """DLIB-DEP-02 / DLIB-PERF-02: blocked waiters re-check stashed replies."""
    inbox = ServiceBusReplyInbox()
    blocked_receiver = _BlockingEmptyReceiver()
    reply_a = raw_ready("reply-a", "request-a")
    reply_b = raw_ready("reply-b", "request-b")
    sibling_receiver = FakeReceiver([reply_a, reply_b])
    result_a: list[CorrelatedReadyEvent] = []
    errors: list[BaseException] = []

    with inbox.expecting("request-a"), inbox.expecting("request-b"):

        def wait_for_a() -> None:
            try:
                result_a.append(
                    inbox.receive(
                        blocked_receiver,
                        correlation_id="request-a",
                        deadline=time.monotonic() + 5.0,
                    )
                )
            except BaseException as exc:
                errors.append(exc)

        waiter = threading.Thread(target=wait_for_a)
        waiter.start()
        assert blocked_receiver.entered.wait(timeout=1.0)

        result_b = inbox.receive(
            sibling_receiver,
            correlation_id="request-b",
            deadline=time.monotonic() + 5.0,
        )
        blocked_receiver.release.set()
        waiter.join(timeout=1.0)

    assert not waiter.is_alive()
    assert errors == []
    assert result_a[0].event["ref"] == "reply-a"
    assert result_b.event["ref"] == "reply-b"
    assert blocked_receiver.max_wait_times == [REPLY_RECEIVE_SLICE_SECONDS]
    assert sibling_receiver.completed == [reply_a, reply_b]
    assert sibling_receiver.dead_lettered == []


def test_reply_inbox_deadline_expires_before_receive() -> None:
    """DLIB-PERF-02: expired peer reply waits fail without bus mutation."""
    inbox = ServiceBusReplyInbox()
    receiver = FakeReceiver([])

    with (
        inbox.expecting("request-a"),
        pytest.raises(CorrelatedReadyEventTimeoutError),
    ):
        inbox.receive(
            receiver,
            correlation_id="request-a",
            deadline=0.0,
            now=lambda: 1.0,
        )

    assert receiver.completed == []
    assert receiver.dead_lettered == []


def test_reply_inbox_dead_letters_malformed_then_times_out() -> None:
    """DLIB-DEP-02 / DLIB-NEV-06: malformed ready events are orphaned."""
    inbox = ServiceBusReplyInbox()
    malformed = RawMessage("not-json")
    receiver = FakeReceiver([malformed])

    with (
        inbox.expecting("request-a"),
        pytest.raises(CorrelatedReadyEventTimeoutError) as err,
    ):
        inbox.receive(
            receiver,
            correlation_id="request-a",
            deadline=1.0,
            now=lambda: 0.0,
        )

    assert err.value.orphan_count == 1
    assert receiver.completed == []
    assert receiver.dead_lettered == [(malformed, ORPHANED_READY_EVENT_REASON)]


class _BlockingEmptyReceiver:
    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()
        self.max_wait_times: list[float] = []

    def receive_messages(
        self, *, max_message_count: int, max_wait_time: float
    ) -> list[RawMessage]:
        assert max_message_count == 1
        self.max_wait_times.append(max_wait_time)
        self.entered.set()
        self.release.wait(timeout=max_wait_time)
        return []

    def complete_message(self, message: RawMessage) -> None:
        del message

    def dead_letter_message(self, message: RawMessage, *, reason: str) -> None:
        del message, reason
