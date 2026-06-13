"""Training-trigger orchestration: select, fit, version, and write a predictor.

Agent: curator
Role: turn a TrainRequest into an advisory PredictorManifest, writing one
      Predictor node on success and a degraded manifest (no node) otherwise.
External I/O: GraphStore reads and the Predictor write path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.curator.domain.manifest import (
    build_predictor_manifest,
    degraded_predictor_manifest,
    next_predictor_version,
)
from agents.curator.domain.training import select_dataset, train_baseline
from agents.curator.store import write_predictor

if TYPE_CHECKING:
    from agents.curator.settings import CuratorSettings
    from contracts.curator import PredictorManifest, TrainRequest
    from kernel import GraphStore


def run_training(
    graph: GraphStore, model: TrainRequest, *, settings: CuratorSettings
) -> PredictorManifest:
    """Select a dataset, fit the baseline, and write/return a PredictorManifest."""
    strategy = settings.predictor_strategy
    dataset = select_dataset(graph, model.purpose, model.version)
    if dataset is None:
        return _degraded(model, strategy, f"no dataset found for {model.purpose}")
    result = train_baseline(graph, dataset, strategy=strategy)
    if result is None or result.metrics["train_size"] < settings.min_train_examples:
        return _degraded(model, strategy, f"train split too small for {model.purpose}")
    version = next_predictor_version(graph, model.purpose, model.target)
    manifest = build_predictor_manifest(
        purpose=model.purpose,
        target=model.target,
        dataset_id=str(dataset.key),
        version=version,
        result=result,
    )
    write_predictor(graph, manifest=manifest, dataset=dataset)
    return manifest


def _degraded(model: TrainRequest, strategy: str, reason: str) -> PredictorManifest:
    return degraded_predictor_manifest(
        purpose=model.purpose,
        target=model.target,
        strategy=strategy,
        reason=reason,
    )
