"""Align persisted sentiment readings into scorecard observations.

Agent: forecaster
Role: read the three scorers' readings from the graph (lexicon + provider
      SentimentReadings, finbert ShadowPredictions) and join injected forward
      returns into complete-case observations for the scorecard.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.forecaster.domain.scorecard import Observation

if TYPE_CHECKING:
    from kernel import GraphStore

_LEXICON = "lexicon"
_PROVIDER = "provider"


def build_observations(
    graph: GraphStore, model_id: str, forward_returns: dict[str, float]
) -> list[Observation]:
    """Complete-case observations keyed by '{analyst_run_id}:{ticker}'.

    A ref contributes only when all three scorers and a forward return are present
    (an inner join); refs missing any leg are skipped.
    """
    readings = _readings_by_ref(graph)
    finbert = _finbert_by_ref(graph, model_id)
    observations: list[Observation] = []
    for ref, forward_return in forward_returns.items():
        scorers = readings.get(ref, {})
        lexicon = scorers.get(_LEXICON)
        provider = scorers.get(_PROVIDER)
        fin = finbert.get(ref)
        if lexicon is None or provider is None or fin is None:
            continue
        observations.append(
            Observation(
                ref=ref,
                lexicon=lexicon,
                provider=provider,
                finbert=fin,
                forward_return=forward_return,
            )
        )
    return observations


def _readings_by_ref(graph: GraphStore) -> dict[str, dict[str, float]]:
    """SentimentReading scores grouped by ref, then by scorer."""
    out: dict[str, dict[str, float]] = {}
    for node in graph.list_nodes("SentimentReading"):
        ref = f"{node.props.get('source_run_id')}:{node.props.get('ticker')}"
        scorer = str(node.props.get("scorer"))
        out.setdefault(ref, {})[scorer] = float(node.props.get("score", 0.0))
    return out


def _finbert_by_ref(graph: GraphStore, model_id: str) -> dict[str, float]:
    """ShadowPrediction values for one model, keyed by their subject ref."""
    out: dict[str, float] = {}
    for node in graph.list_nodes("ShadowPrediction"):
        if node.props.get("model_id") != model_id:
            continue
        out[str(node.props.get("subject_ref"))] = float(node.props.get("value", 0.0))
    return out
