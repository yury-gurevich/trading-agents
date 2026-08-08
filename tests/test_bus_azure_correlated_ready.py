"""Correlated Azure Service Bus ready-event tests.

Agent: kernel
Role: prove reply-ready events answer the request being resolved.
External I/O: none.
"""

from __future__ import annotations

import json

import pytest
from tests.bus_azure_receiver_helpers import FakeReceiver, RawMessage

from kernel.bus_azure_ready import (
    ORPHANED_READY_EVENT_REASON,
    CorrelatedReadyEventTimeoutError,
    receive_correlated_ready_event,
)


def _raw(ref: str, run_id: str) -> RawMessage:
    event = {
        "topic": "deliberator-manager.reply",
        "label": "AgentMessage",
        "ref": ref,
        "run_id": run_id,
    }
    return RawMessage(json.dumps(event))


def test_correlated_ready_event_dead_letters_orphan_then_completes_match() -> None:
    stale = _raw("reply-stale", "request-old")
    fresh = _raw("reply-fresh", "request-new")
    receiver = FakeReceiver([stale, fresh])

    result = receive_correlated_ready_event(
        receiver,
        correlation_id="request-new",
        deadline=1.0,
        now=lambda: 0.0,
    )

    assert result.event["ref"] == "reply-fresh"
    assert result.orphan_count == 1
    assert receiver.dead_lettered == [(stale, ORPHANED_READY_EVENT_REASON)]
    assert receiver.completed == [fresh]


def test_correlated_ready_event_timeout_reports_skipped_orphans() -> None:
    stale = _raw("reply-stale", "request-old")
    receiver = FakeReceiver([stale])

    with pytest.raises(CorrelatedReadyEventTimeoutError) as err:
        receive_correlated_ready_event(
            receiver,
            correlation_id="request-new",
            deadline=1.0,
            now=lambda: 0.0,
        )

    assert err.value.orphan_count == 1
    assert receiver.dead_lettered == [(stale, ORPHANED_READY_EVENT_REASON)]
    assert receiver.completed == []


def test_correlated_ready_event_honors_expired_deadline_without_receive() -> None:
    receiver = FakeReceiver([])

    with pytest.raises(CorrelatedReadyEventTimeoutError):
        receive_correlated_ready_event(
            receiver,
            correlation_id="request-new",
            deadline=0.0,
            now=lambda: 1.0,
        )

    assert receiver.dead_lettered == []
    assert receiver.completed == []


def test_correlated_ready_event_dead_letters_malformed_ready_event() -> None:
    malformed = RawMessage("not-json")
    fresh = _raw("reply-fresh", "request-new")
    receiver = FakeReceiver([malformed, fresh])

    result = receive_correlated_ready_event(
        receiver,
        correlation_id="request-new",
        deadline=1.0,
        now=lambda: 0.0,
    )

    assert result.event["ref"] == "reply-fresh"
    assert result.orphan_count == 1
    assert receiver.dead_lettered == [(malformed, ORPHANED_READY_EVENT_REASON)]
