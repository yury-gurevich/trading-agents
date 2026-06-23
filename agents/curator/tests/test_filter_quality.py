"""Filter-quality scorecard tests (DL-09 measurement side).

Agent: curator
Role: cover score_filters (per-filter confusion matrix + keep quality vs injected
      outcomes) and collect_verdicts (reading recorded verdicts off ScanRun nodes).
External I/O: none (InMemoryGraphStore).
"""

from __future__ import annotations

from agents.curator.domain.filter_quality import (
    collect_verdicts,
    score_filters,
)
from contracts.common import Explanation, Provenance
from contracts.scanner import CandidateSet, FilterTrace, FilterVerdict
from kernel import InMemoryGraphStore

_VERDICTS = (
    FilterVerdict(ticker="WIN", decision="survived"),  # rose -> good keep
    FilterVerdict(ticker="LOSEKEEP", decision="survived"),  # fell -> wrong keep
    FilterVerdict(
        ticker="GOODDROP", decision="dropped", filter_fired="min_relative_strength"
    ),
    FilterVerdict(
        ticker="MISSED",
        decision="dropped",
        filter_fired="min_relative_strength",
        bypassed=True,  # bypassed drop that rose -> a now-visible missed winner
    ),
    FilterVerdict(ticker="BETADROP", decision="dropped", filter_fired="max_beta"),
    FilterVerdict(
        ticker="NOFILTER", decision="dropped"
    ),  # filter_fired None -> skipped
    FilterVerdict(ticker="NOOUTCOME", decision="survived"),  # no outcome -> skipped
)
_OUTCOMES = {
    "WIN": 0.10,
    "LOSEKEEP": -0.05,
    "GOODDROP": -0.08,
    "MISSED": 0.20,
    "BETADROP": -0.03,
    "NOFILTER": 0.01,
}


def test_score_filters_confusion_matrix_and_precision() -> None:
    card = score_filters(_VERDICTS, _OUTCOMES)
    scores = {s.filter_name: s for s in card.by_filter}

    # min_relative_strength dropped two: one fell (good), one rose (missed winner).
    mrs = scores["min_relative_strength"]
    assert (mrs.dropped, mrs.good_drops, mrs.missed_winners) == (2, 1, 1)
    assert mrs.precision == 0.5
    # max_beta dropped one that fell -> perfect precision.
    assert scores["max_beta"].precision == 1.0
    # NOFILTER (no filter_fired) is not attributed to any filter.
    assert set(scores) == {"max_beta", "min_relative_strength"}


def test_score_filters_keep_quality_and_skips_unknown_outcomes() -> None:
    card = score_filters(_VERDICTS, _OUTCOMES)
    # WIN rose (good keep), LOSEKEEP fell (wrong keep); NOOUTCOME has no outcome.
    assert (card.kept, card.good_keeps, card.wrong_keeps) == (2, 1, 1)
    assert card.keep_precision == 0.5


def test_score_filters_empty_is_zeroed() -> None:
    card = score_filters((), {})
    assert card.by_filter == ()
    assert card.kept == 0
    assert card.keep_precision == 0.0


def test_collect_verdicts_reads_scan_run_nodes() -> None:
    graph = InMemoryGraphStore()
    candidate_set = CandidateSet(
        run_id="r1",
        candidates=(),
        filter_trace=FilterTrace(
            universe_size=2,
            evaluated=2,
            verdicts=(
                FilterVerdict(ticker="A", decision="survived"),
                FilterVerdict(ticker="B", decision="dropped", filter_fired="min_price"),
            ),
        ),
        explanation=Explanation(summary="scan"),
        provenance=Provenance(run_id="r1", source_agent="scanner"),
    )
    graph.merge_node(
        "ScanRun", "scan:r1", {"candidate_set": candidate_set.model_dump(mode="json")}
    )
    graph.merge_node("ScanRun", "scan:empty", {})  # no candidate_set -> skipped

    verdicts = collect_verdicts(graph)
    assert {v.ticker for v in verdicts} == {"A", "B"}
