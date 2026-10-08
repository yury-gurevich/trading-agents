"""Command report fields and the three specified exit states.

Agent: tooling
Role: prove DL-279 A8 on the real memory scene.
External I/O: none.
"""

from __future__ import annotations

import json

import pytest
from scripts import debate_lanes
from scripts.debate_lanes import main, parser

REPORT_FIELDS = {
    "transport",
    "concurrency",
    "replicas",
    "orders",
    "rounds",
    "turn_seconds",
    "wait_seconds",
    "replica_start_delay_seconds",
    "requests_a_pass",
    "real_debate_count",
    "failed_open_count",
    "failed_open_reason",
    "orphaned_reply_count",
    "replies_nobody_took",
    "mismatched_replies",
    "turns_asked",
    "turns_served",
    "turns_served_twice",
    "turns_answered_for_nobody",
    "turns_started_after_caller_gave_up",
    "first_wave_replicas",
    "by_replica",
    "span_seconds",
    "served_work_seconds",
    "effective_lanes",
    "request_wait_seconds",
    "reply_pickup_seconds",
    "subscriptions",
    "errors",
    "faults",
    "clean",
}


@pytest.mark.parametrize("loses_replies", [False, True])
def test_command_reports_and_returns_the_counted_result(loses_replies, capsys):
    """DL-279 A8 / DLIB-FAIL-01 / DLIB-OBS-04: counted loss determines exit."""
    args = (
        "--concurrency 4 --orders 4 --rounds 1 --turn-seconds 1 --wait-seconds 2.5 "
        "--replica-start-delay 0.3 --requests-a-pass 10"
        if loses_replies
        else "--concurrency 1 2 --orders 1 --rounds 1 --turn-seconds 0 --wait-seconds 1"
    )
    assert main(args.split()) == (1 if loses_replies else 0)
    output = capsys.readouterr()
    lines = output.out.splitlines()
    assert output.err == ""
    assert len(lines) == (2 if loses_replies else 3)
    reports = [json.loads(line) for line in lines[:-1]]
    for report in reports:
        assert report.keys() >= REPORT_FIELDS
        assert report["clean"] is not loses_replies
        assert report["requests_a_pass"] == (10 if loses_replies else 1)
        assert report["transport"] == "memory"
    assert lines[-1] == ("LANES NOT CLEAN: 4" if loses_replies else "LANES CLEAN")


@pytest.mark.parametrize(
    "args",
    [
        "--unknown",
        "--concurrency 0",
        "--concurrency 26",
        "--rounds 6",
        "--replicas 0",
        "--orders -1",
        "--turn-seconds -1",
        "--turn-seconds nan",
        "--wait-seconds 0",
        "--replica-start-delay -1",
        "--requests-a-pass 101",
    ],
)
def test_bad_argument_returns_two_without_a_report(args, capsys, monkeypatch):
    """DL-279 A8: an unusable argument is a could-not-run exit."""
    calls = []

    def unexpected_run(**kwargs):
        calls.append(kwargs)
        raise AssertionError("an invalid configuration reached scene construction")

    monkeypatch.setattr(debate_lanes, "run", unexpected_run)
    assert main(args.split()) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err.startswith("LANES COULD NOT RUN:")
    assert calls == []


def test_command_defaults_are_the_recorded_scene():
    """DL-279 D9 / DL-281: the bare command compares one through four."""
    args = parser().parse_args([])
    assert vars(args) == {
        "transport": "memory",
        "concurrency": [1, 2, 3, 4],
        "replicas": None,
        "orders": 8,
        "rounds": 2,
        "turn_seconds": 0.5,
        "wait_seconds": 5.0,
        "replica_start_delay": 0.0,
        "requests_a_pass": None,
    }
