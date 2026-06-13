"""Curator agent — assemble versioned training datasets from the provenance graph.

Agent: curator
Role: out-of-band data engineering; build/describe datasets, never the decision loop.
External I/O: MessageBus binding; dataset_store writes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.curator.agent_support import dataset_payload, degraded_manifest
from agents.curator.dataset_store import FakeDatasetStore
from agents.curator.domain.assembly import assemble_examples
from agents.curator.domain.manifest import (
    build_manifest,
    degraded_predictor_manifest,
    next_version,
)
from agents.curator.domain.split import SplitAssignment, split_examples
from agents.curator.predictor import run_training
from agents.curator.promotion import run_promotion
from agents.curator.settings import CuratorSettings
from agents.curator.store import write_dataset
from contracts.common import Explanation, Provenance
from contracts.curator import (
    CONTRACT,
    DatasetManifest,
    DatasetRequest,
    PredictorManifest,
    PromoteRequest,
    PromotionResult,
    TrainRequest,
)
from kernel import AgentBase, CollectingFaultSink, FaultSink, GraphStore
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from pydantic import BaseModel

    from agents.curator.dataset_store import DatasetStore
    from kernel import MessageBus


class CuratorAgent(AgentBase):
    """Curator boundary agent."""

    def __init__(
        self,
        bus: MessageBus,
        *,
        graph: GraphStore,
        dataset_store: DatasetStore | None = None,
        settings: CuratorSettings | None = None,
        sink: FaultSink | None = None,
    ) -> None:
        """Create curator with injected bus, graph, store, settings, and sink."""
        super().__init__(CONTRACT, bus)
        self._graph = graph
        self._store = dataset_store if dataset_store is not None else FakeDatasetStore()
        self._settings = settings or CuratorSettings()
        self.sink = sink if sink is not None else CollectingFaultSink()
        self.handlers = {
            "build_dataset": self._build_dataset,
            "describe_corpus": self._describe_corpus,
            "train_predictor": self._train_predictor,
            "promote_predictor": self._promote_predictor,
        }

    def _build_dataset(self, request: BaseModel) -> DatasetManifest:
        model = DatasetRequest.model_validate(request)
        result = degraded_manifest(model.purpose, f"dataset:{model.purpose}:v1", 1)
        with fault_boundary(
            self.sink,
            agent="curator",
            module="agents.curator.agent",
            capability="build_dataset",
            reraise=False,
        ) as capture:
            result = self._assemble(model)
        if capture.fault is not None:
            return degraded_manifest(model.purpose, f"dataset:{model.purpose}:v1", 1)
        return result

    def _assemble(self, request: DatasetRequest) -> DatasetManifest:
        version = next_version(self._graph, request.purpose)
        dataset_id = f"dataset:{request.purpose}:v{version}"
        records = assemble_examples(
            self._graph,
            purpose=request.purpose,
            max_examples=self._settings.max_examples,
        )
        if len(records) < self._settings.min_examples_for_split:
            split = SplitAssignment(records, (), ())
        else:
            split = split_examples(records, request.train_val_test)
        manifest = build_manifest(
            purpose=request.purpose,
            schema_ref=self._settings.schema_ref,
            split=split,
            dataset_id=dataset_id,
            version=version,
        )
        write_dataset(self._graph, manifest=manifest, split=split)
        self._persist(dataset_id, split)
        return manifest

    def _persist(self, dataset_id: str, split: SplitAssignment) -> None:
        with fault_boundary(
            self.sink,
            agent="curator",
            module="agents.curator.agent",
            capability="build_dataset.store",
            reraise=False,
        ):
            self._store.write(dataset_id, dataset_payload(split))

    def _describe_corpus(self, request: BaseModel) -> Explanation:
        model = DatasetRequest.model_validate(request)
        narratives = self._graph.list_nodes("TradeNarrative")
        snapshots = self._graph.list_nodes("Snapshot")
        existing = [
            node
            for node in self._graph.list_nodes("Dataset")
            if node.props.get("purpose") == model.purpose
        ]
        if not narratives and not snapshots:
            return Explanation(summary="no training corpus collected yet")
        return Explanation(
            summary=(
                f"{len(narratives)} completed-trade narratives and {len(snapshots)} "
                f"run snapshots available; {len(existing)} prior {model.purpose} "
                f"dataset(s)."
            )
        )

    def _train_predictor(self, request: BaseModel) -> PredictorManifest:
        model = TrainRequest.model_validate(request)
        result = self._faulted_predictor(model)
        with fault_boundary(
            self.sink,
            agent="curator",
            module="agents.curator.agent",
            capability="train_predictor",
            reraise=False,
        ) as capture:
            result = run_training(self._graph, model, settings=self._settings)
        if capture.fault is not None:
            return self._faulted_predictor(model)
        return result

    def _faulted_predictor(self, model: TrainRequest) -> PredictorManifest:
        return degraded_predictor_manifest(
            purpose=model.purpose,
            target=model.target,
            strategy=self._settings.predictor_strategy,
            reason=f"training faulted for {model.purpose}",
        )

    def _promote_predictor(self, request: BaseModel) -> PromotionResult:
        model = PromoteRequest.model_validate(request)
        result = _promotion_fault(model.predictor_id)
        with fault_boundary(
            self.sink,
            agent="curator",
            module="agents.curator.agent",
            capability="promote_predictor",
            reraise=False,
        ) as capture:
            result = run_promotion(
                graph=self._graph,
                bus=self.bus,
                settings=self._settings,
                predictor_id=model.predictor_id,
            )
        if capture.fault is not None:
            return _promotion_fault(model.predictor_id)
        return result


def _promotion_fault(predictor_id: str) -> PromotionResult:
    return PromotionResult(
        predictor_id=predictor_id,
        status="rejected",
        state="advisory",
        reason="promotion fault",
        explanation=Explanation(summary="promotion faulted"),
        provenance=Provenance(
            run_id=f"promotion:{predictor_id}", source_agent="curator"
        ),
    )
