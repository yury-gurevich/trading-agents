"""Filter-quality scorecard — score scanner drops against realized outcomes (DL-09).

Agent: curator
Role: turn recorded per-ticker FilterVerdicts into a per-filter confusion matrix
      (good drops vs missed winners, precision) and an overall keep quality, scored
      against injected forward-return outcomes.
External I/O: GraphStore reads (collect_verdicts). Outcomes are injected, never fetched.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from contracts.scanner import CandidateSet, FilterVerdict

if TYPE_CHECKING:
    from collections.abc import Mapping

    from kernel import GraphStore

_SCAN_RUN_LABEL = "ScanRun"


@dataclass(frozen=True)
class FilterScore:
    """How one filter's drops fared against realized outcomes."""

    filter_name: str
    dropped: int  # drops by this filter that have a known outcome
    good_drops: int  # dropped and fell — the filter was right to drop
    missed_winners: int  # dropped and rose — the filter threw away a winner
    precision: float  # good_drops / dropped (0.0 when dropped == 0)


@dataclass(frozen=True)
class FilterScorecard:
    """Per-filter drop quality plus the scanner's overall keep quality."""

    by_filter: tuple[FilterScore, ...]
    kept: int  # survived tickers with a known outcome
    good_keeps: int  # survived and rose
    wrong_keeps: int  # survived and fell
    keep_precision: float  # good_keeps / kept (0.0 when kept == 0)


def collect_verdicts(graph: GraphStore) -> tuple[FilterVerdict, ...]:
    """Read every recorded FilterVerdict off the graph's ScanRun nodes."""
    verdicts: list[FilterVerdict] = []
    for node in graph.list_nodes(_SCAN_RUN_LABEL):
        snapshot = node.props.get("candidate_set")
        if snapshot is None:
            continue
        verdicts.extend(CandidateSet.model_validate(snapshot).filter_trace.verdicts)
    return tuple(verdicts)


def score_filters(
    verdicts: tuple[FilterVerdict, ...], outcomes: Mapping[str, float]
) -> FilterScorecard:
    """Score drops + keeps against injected outcomes (return > 0 = the ticker rose).

    Outcomes — a fixed-horizon forward return per ticker — are injected, never fetched
    (same discipline as the forecaster scorecards). Tickers absent from ``outcomes``
    are skipped (no ground truth). Bypassed drops carry a real outcome, so a drop that
    rose is finally visible as a missed winner — the DL-09 counterfactual.
    """
    # filter name -> [good_drops, missed_winners]
    drops: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    kept = good_keeps = wrong_keeps = 0
    for verdict in verdicts:
        outcome = outcomes.get(verdict.ticker)
        if outcome is None:
            continue
        rose = outcome > 0
        if verdict.decision == "survived":
            kept += 1
            good_keeps += 1 if rose else 0
            wrong_keeps += 0 if rose else 1
        elif verdict.filter_fired is not None:
            tally = drops[verdict.filter_fired]
            tally[1 if rose else 0] += 1  # rose -> missed winner; fell -> good drop
    by_filter = tuple(
        FilterScore(
            filter_name=name,
            dropped=good + missed,
            good_drops=good,
            missed_winners=missed,
            precision=good / (good + missed) if (good + missed) else 0.0,
        )
        for name, (good, missed) in sorted(drops.items())
    )
    return FilterScorecard(
        by_filter=by_filter,
        kept=kept,
        good_keeps=good_keeps,
        wrong_keeps=wrong_keeps,
        keep_precision=good_keeps / kept if kept else 0.0,
    )
