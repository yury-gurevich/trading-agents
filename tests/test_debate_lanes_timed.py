"""Production debate lanes with real threads and real waits.

Agent: tooling
Role: hold the four DL-279 counts, including September's lost replies.
External I/O: none; only the memory transport.
"""

from __future__ import annotations


def test_four_debates_lose_no_reply():
    """DL-279 A1 / DLIB-IDM-04 / DLIB-OBS-04: the default loses nothing."""
    from scripts.debate_lanes_scene import run

    report = run(
        concurrency=4,
        replicas=4,
        orders=4,
        rounds=1,
        turn_seconds=1.0,
        wait_seconds=2.5,
        replica_start_delay=0.3,
    )
    assert report["clean"] is True
    assert report["real_debate_count"] == 4
    for field in (
        "failed_open_count",
        "replies_nobody_took",
        "mismatched_replies",
        "turns_served_twice",
    ):
        assert report[field] == 0
    assert report["first_wave_replicas"] == 4
    assert report["requests_a_pass"] == 1


def test_september_setting_loses_replies():
    """DL-279 A2 / DLIB-FAIL-01 / DLIB-NEV-06 / DLIB-OBS-04: loss is loud."""
    from scripts.debate_lanes_scene import run

    report = run(
        concurrency=4,
        replicas=4,
        orders=4,
        rounds=1,
        turn_seconds=1.0,
        wait_seconds=2.5,
        replica_start_delay=0.3,
        requests_a_pass=10,
    )
    assert report["clean"] is False
    assert report["first_wave_replicas"] == 1
    assert report["requests_a_pass"] == 10
    assert report["failed_open_count"] >= 2
    assert "no deliberator peer reply received" in report["failed_open_reason"]
    assert report["replies_nobody_took"] >= 2
    assert report["turns_started_after_caller_gave_up"] >= 1


def test_four_lanes_need_four_replicas():
    """DL-279 A3 / DLIB-FAIL-01: one replica fails independent orders open."""
    from scripts.debate_lanes_scene import run

    report = run(
        concurrency=4,
        replicas=1,
        orders=4,
        rounds=1,
        turn_seconds=1.0,
        wait_seconds=2.5,
    )
    assert report["clean"] is False
    assert report["failed_open_count"] >= 2
    assert report["first_wave_replicas"] == 1


def test_one_debate_at_a_time():
    """DL-279 A4 / DLIB-DEP-02 / DLIB-OBS-04: serial replies are picked up."""
    from scripts.debate_lanes_scene import run

    report = run(
        concurrency=1,
        replicas=1,
        orders=4,
        rounds=1,
        turn_seconds=1.0,
        wait_seconds=2.5,
    )
    assert report["clean"] is True
    assert 0.8 <= report["effective_lanes"] <= 1.1
    assert report["reply_pickup_seconds"][1] < 0.5
