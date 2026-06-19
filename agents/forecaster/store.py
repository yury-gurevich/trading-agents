"""Forecaster graph write path.

Agent: forecaster
Role: persist shadow predictions and their model, linked into the provenance graph.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from contracts.common import Provenance

if TYPE_CHECKING:
    from agents.forecaster.domain.sentiment import ModelReading
    from kernel import GraphStore, Node

#: subject_kind -> the graph label whose node a prediction advises.
_SUBJECT_LABELS = {"recommendation": "Recommendation", "position": "Position"}


def write_forecast(
    graph: GraphStore,
    *,
    model_id: str,
    model_ref: str,
    subject_kind: str,
    subject_ref: str,
    reading: ModelReading,
    model_kind: str = "sentiment",
) -> Provenance:
    """Persist a Model + its ShadowPrediction, linked to the subject when present."""
    run_id = f"forecaster-run-{uuid.uuid4().hex}"
    # Model is keyed by the stable model_id, so it is merged idempotently across
    # runs — its props must not change (the graph rejects prop overwrites).
    model = graph.merge_node("Model", model_id, {"ref": model_ref, "kind": model_kind})
    prediction = graph.merge_node(
        "ShadowPrediction",
        f"{model_id}:{subject_ref}:{run_id}",
        {
            "subject_ref": subject_ref,
            "model_id": model_id,
            "value": reading.value,
            "confidence": reading.confidence,
            "shadow": True,
            "source_run_id": run_id,
        },
    )
    graph.add_edge(model, prediction, "PREDICTED")
    _advise_subject(graph, prediction, subject_kind, subject_ref)
    return Provenance(
        run_id=run_id,
        source_agent="forecaster",
        graph_node_id=f"{prediction.label}:{prediction.key}",
    )


def _advise_subject(
    graph: GraphStore, prediction: Node, subject_kind: str, subject_ref: str
) -> None:
    """Link the prediction to the recommendation/position it advises, if present."""
    label = _SUBJECT_LABELS.get(subject_kind)
    if label is None:
        return
    subject = graph.get_node(label, subject_ref)
    if subject is not None:
        graph.add_edge(prediction, subject, "ADVISES")


def read_predictions(graph: GraphStore, model_id: str) -> tuple[Node, ...]:
    """Return all ShadowPredictions produced by one model."""
    return tuple(
        node
        for node in graph.list_nodes("ShadowPrediction")
        if node.props.get("model_id") == model_id
    )
