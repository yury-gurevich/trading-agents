"""Deliberator Service Bus reply-correlation tests.

Agent: deliberator
Role: prove a served-peer reply answers the manager request being resolved.
External I/O: none.
"""

from __future__ import annotations

import uuid

import pytest
from tests.bus_azure_receiver_helpers import FakeReceiver, RawMessage
from tests.deliberator_correlated_peer_helpers import (
    DEFAULT_REQUEST_ID,
    ReplyReceiver,
    client,
    raw_ready,
    store_reply,
    turn_request,
)

from agents.deliberator.servicebus_reply_inbox import ServiceBusReplyInbox
from kernel import (
    CollectingFaultSink,
    GraphFaultSink,
    InMemoryGraphStore,
)
from kernel.bus_azure_ready import (
    ORPHANED_READY_EVENT_REASON,
    CorrelatedReadyEventTimeoutError,
)


def test_debate_turn_skips_stale_ahead_of_genuine_reply_and_faults() -> None:
    """DLIB-DEP-02 / DLIB-NEV-06: stale replies are not clean debate turns."""
    graph = InMemoryGraphStore()
    inner = CollectingFaultSink()
    stale = store_reply(
        graph,
        "reply-stale",
        request_id="pm-old:MSFT:defender:r1",
        text="stale MSFT reply",
        correlation_id=uuid.uuid4(),
    )
    receiver = ReplyReceiver(graph, [stale], fresh_ref="reply-fresh")
    peer = client(graph, receiver, GraphFaultSink(graph, inner))

    result = peer.debate_turn("deliberator-proponent", turn_request())

    assert result.request_id == DEFAULT_REQUEST_ID
    assert result.turn.text == "fresh AAPL reply"
    assert receiver.dead_lettered == [(stale, ORPHANED_READY_EVENT_REASON)]
    assert len(receiver.completed) == 1
    assert peer.orphaned_reply_count == 1
    (fault,) = graph.list_nodes("Fault")
    assert fault.props["error_type"] == "OrphanedPeerReply"
    assert "dead-lettered 1 orphaned peer reply" in fault.props["message"]
    assert inner.faults[0].context["orphan_count"] == 1


def test_stale_success_for_different_ticker_is_not_accepted() -> None:
    """DLIB-DEP-02 / DLIB-NEV-06: stale success cannot answer another ticker."""
    graph = InMemoryGraphStore()
    stale = store_reply(
        graph,
        "reply-stale",
        request_id="pm-old:MSFT:defender:r1",
        text="stale success for MSFT",
        correlation_id=uuid.uuid4(),
    )
    receiver = ReplyReceiver(graph, [stale])
    peer = client(graph, receiver, GraphFaultSink(graph, CollectingFaultSink()))

    with pytest.raises(RuntimeError, match="no deliberator peer reply received"):
        peer.debate_turn("deliberator-proponent", turn_request())

    assert receiver.completed == []
    assert receiver.dead_lettered == [(stale, ORPHANED_READY_EVENT_REASON)]
    assert peer.orphaned_reply_count == 1


def test_prompt_peer_reply_is_one_receive_no_dead_letter() -> None:
    """DLIB-DEP-02 / DLIB-PERF-02: normal peer reply path stays unchanged."""
    graph = InMemoryGraphStore()
    receiver = ReplyReceiver(graph, [], fresh_ref="reply-fresh")
    peer = client(graph, receiver, GraphFaultSink(graph, CollectingFaultSink()))

    result = peer.debate_turn("deliberator-proponent", turn_request())

    assert result.turn.text == "fresh AAPL reply"
    assert receiver.receive_calls == 1
    assert receiver.dead_lettered == []
    assert len(receiver.completed) == 1
    assert peer.orphaned_reply_count == 0
    assert graph.list_nodes("Fault") == ()


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


def test_no_matching_reply_still_raises_for_manager_fail_open() -> None:
    """DLIB-FAIL-01 / DLIB-PERF-02: no matching reply remains fail-open input."""
    graph = InMemoryGraphStore()
    receiver = ReplyReceiver(graph, [])
    peer = client(graph, receiver, GraphFaultSink(graph, CollectingFaultSink()))

    with pytest.raises(RuntimeError, match="no deliberator peer reply received"):
        peer.debate_turn("deliberator-proponent", turn_request())

    assert receiver.receive_calls == 1
    assert receiver.dead_lettered == []
    assert receiver.completed == []
    assert peer.orphaned_reply_count == 0
