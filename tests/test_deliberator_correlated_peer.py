"""Deliberator Service Bus reply-correlation tests.

Agent: deliberator
Role: prove a served-peer reply answers the manager request being resolved.
External I/O: none.
"""

from __future__ import annotations

import uuid

import pytest
from tests.deliberator_correlated_peer_helpers import (
    DEFAULT_REQUEST_ID,
    ReplyReceiver,
    client,
    store_reply,
    turn_request,
)

from kernel import (
    CollectingFaultSink,
    GraphFaultSink,
    InMemoryGraphStore,
)
from kernel.bus_azure_ready import ORPHANED_READY_EVENT_REASON


def test_debate_turn_skips_stale_ahead_of_genuine_reply_and_faults() -> None:
    """DLIB-DEP-02 / DLIB-NEV-06 / DLIB-OBS-04: stale replies stay loud."""
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
