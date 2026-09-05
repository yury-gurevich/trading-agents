"""Recorded-verdict source tests.

Agent: tooling
Role: prove a fail-open never leaves the graph reader as if it were a ruling.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from orchestration.verdict_sources import (
    real_verdicts,
    recorded_as_repeats,
    recorded_verdicts,
)


def test_a_fail_open_uphold_is_subtracted_from_a_recorded_run() -> None:
    """fail_open_review records 'uphold'; counting it would measure the outage."""
    props = {
        "verdicts": {"USB": "uphold", "AVGO": "revise"},
        "failed_open_tickers": ["USB"],
    }

    assert real_verdicts(props) == {"AVGO": "revise"}


def test_a_run_with_no_readable_verdict_map_contributes_nothing() -> None:
    """A malformed row must not become an empty agreement claim."""
    assert real_verdicts({}) == {}
    assert real_verdicts({"verdicts": "not a map"}) == {}
    assert real_verdicts({"verdicts": {"USB": "revise"}, "failed_open_tickers": 3}) == {
        "USB": "revise"
    }


def test_the_recorded_verdicts_are_keyed_by_run_and_ticker() -> None:
    """One ticker can be judged differently on different nights."""
    graph = InMemoryGraphStore()
    graph.merge_node(
        "DeliberationRun",
        "pm-run-1",
        {"verdicts": {"USB": "revise", "C": "uphold"}, "failed_open_tickers": ["C"]},
    )
    graph.merge_node("DeliberationRun", "pm-run-2", {"verdicts": {"USB": "uphold"}})

    assert recorded_verdicts(graph) == {
        ("pm-run-1", "USB"): "revise",
        ("pm-run-2", "USB"): "uphold",
    }


def test_two_recorded_runs_become_repeats_of_one_ticker_decision() -> None:
    """DL-104 compared two nights by ticker; the metric must be able to."""
    graph = InMemoryGraphStore()
    graph.merge_node("DeliberationRun", "run-a", {"verdicts": {"USB": "revise"}})
    graph.merge_node(
        "DeliberationRun",
        "run-b",
        {"verdicts": {"USB": "uphold", "C": "uphold"}, "failed_open_tickers": ["C"]},
    )

    repeats = recorded_as_repeats(graph, ["run-a", "run-b"])

    assert [(item.ticker, item.repeat, item.ruling) for item in repeats] == [
        ("USB", 1, "revise"),
        ("USB", 2, "uphold"),
    ]
    assert {item.pm_run for item in repeats} == {"cross-run"}


def test_a_run_id_that_does_not_exist_contributes_no_repeats() -> None:
    """A typo in a run id must not quietly halve the comparison."""
    assert recorded_as_repeats(InMemoryGraphStore(), ["nope"]) == ()
