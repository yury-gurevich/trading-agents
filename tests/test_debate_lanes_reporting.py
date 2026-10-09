"""Reply identity observation and the independently falsifiable clean rule.

Agent: tooling
Role: prove DL-279 A5 and each of A6's seven terms.
External I/O: none.
"""

from __future__ import annotations

import threading

import pytest
from scripts.debate_lanes_observers import CheckingPeerClient
from scripts.debate_lanes_report import is_clean, observations
from tests.deliberator_correlated_peer_helpers import turn_request

from contracts.deliberator import DebateTurnRecord, DebateTurnReply


def clean_report(transport="memory"):
    return {
        "transport": transport,
        "orders": 4,
        "real_debate_count": 4,
        "failed_open_count": 0,
        "replies_nobody_took": 0,
        "mismatched_replies": 0,
        "turns_served_twice": 0,
        "errors": [],
        "production_unchanged": True,
    }


class WrongReply:
    orphaned_reply_count = 0

    def debate_turn(self, recipient, request):
        return DebateTurnReply(
            request_id="another request",
            turn=DebateTurnRecord(role="defender", round=1, text="A."),
        )


def test_another_requests_reply_is_counted():
    """DL-279 A5 / DLIB-NEV-06: an observed id mismatch cannot read clean."""
    calls = []
    observer = CheckingPeerClient(WrongReply(), calls, threading.Lock())
    reply = observer.debate_turn("peer", turn_request())
    assert reply.request_id == "another request"
    assert calls[0]["request_id"] == turn_request().request_id
    assert calls[0]["call"] <= calls[0]["return"]
    assert observations(calls)["mismatched_replies"] == 1
    report = {**clean_report(), **observations(calls)}
    assert is_clean(report) is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("failed_open_count", 1),
        ("real_debate_count", 3),
        ("replies_nobody_took", 1),
        ("mismatched_replies", 1),
        ("turns_served_twice", 1),
        ("errors", ["one replica raised"]),
        ("production_unchanged", False),
    ],
)
def test_each_rule_term_alone_makes_the_report_not_clean(field, value):
    """DL-279 A6 / DLIB-FAIL-01 / DLIB-OBS-04: each failure falsifies clean."""
    report = clean_report("live")
    assert is_clean(report) is True
    assert is_clean({**report, field: value}) is False


def test_memory_rule_needs_no_production_subscription_field():
    """DL-279 D3: the fleet subscription comparison belongs only to live."""
    report = clean_report()
    del report["production_unchanged"]
    assert is_clean(report) is True
