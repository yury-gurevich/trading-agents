"""Curator agent contract — collected graph data into training-ready datasets.

Agent: curator
Role: contract — typed boundary for the out-of-band data-engineering agent that
      prepares Neo4j-collected data for later LLM training.
External I/O: dataset_store
"""

from __future__ import annotations

from typing import Literal

from contracts.common import Explanation, Provenance, _Frozen
from kernel.contract import AgentContract, Capability


# ── Inbound payloads ────────────────────────────────────────────────────────
class DatasetRequest(_Frozen):
    purpose: str
    """e.g. 'exit-timing-finetune', 'narration-sft', 'rejection-explanations'."""
    lookback_days: int = 365
    train_val_test: tuple[float, float, float] = (0.8, 0.1, 0.1)


class TrainRequest(_Frozen):
    purpose: str
    version: int | None = None  # None → latest dataset version for this purpose
    target: str = "exit_trigger"  # the label column to predict


class PromoteRequest(_Frozen):
    predictor_id: str


# ── Outbound payloads ───────────────────────────────────────────────────────
PromotionStatus = Literal[
    "promoted", "pending_approval", "rejected", "already_promoted", "not_found"
]


class PromotionResult(_Frozen):
    predictor_id: str
    status: PromotionStatus
    state: Literal["advisory", "load_bearing"]  # registry state AFTER this call
    reason: str
    explanation: Explanation
    provenance: Provenance


class DatasetSplit(_Frozen):
    name: Literal["train", "validation", "test"]
    example_count: int


class PredictorManifest(_Frozen):
    predictor_id: str
    dataset_id: str
    purpose: str
    target: str
    strategy: str  # e.g. "majority_class"
    metrics: dict[str, float]  # frozen evidence: accuracy, train_size, test_size
    sample_size: int  # test-split size the metrics were measured on
    advisory: bool = True  # ALWAYS True this sprint — never load-bearing
    promotion_eligible: bool = False  # ALWAYS False this sprint — promotion is S29
    explanation: Explanation
    provenance: Provenance


class DatasetManifest(_Frozen):
    dataset_id: str
    version: int
    purpose: str
    example_count: int
    splits: tuple[DatasetSplit, ...]
    schema_ref: str
    explanation: Explanation
    provenance: Provenance


CONTRACT = AgentContract(
    name="curator",
    version="0.3.0",
    mission=(
        "Curate the collected provenance graph into clean, labelled, versioned "
        "datasets ready for later LLM training — running out of band, alongside "
        "trading, never touching the live decision loop."
    ),
    consumes=(
        Capability(
            "build_dataset",
            "Assemble a versioned, split training dataset from the provenance graph.",
            request=DatasetRequest,
            response=DatasetManifest,
            mcp=True,
        ),
        Capability(
            "describe_corpus",
            "Summarize what collected data is available to train on.",
            request=DatasetRequest,
            response=Explanation,
            mcp=True,
        ),
        Capability(
            "train_predictor",
            "Train an advisory baseline predictor from a curated dataset and "
            "freeze its evidence.",
            request=TrainRequest,
            response=PredictorManifest,
            mcp=True,
        ),
        Capability(
            "promote_predictor",
            "Gate an advisory predictor to load-bearing on frozen evidence + "
            "operator approval.",
            request=PromoteRequest,
            response=PromotionResult,
            mcp=True,
        ),
    ),
    emits=("dataset_published",),
    owns_graph=("Dataset", "TrainingExample", "Predictor", "PredictorPromotion"),
    external_io=("dataset_store",),
    depends_on=("reporter", "supervisor"),
    mcp_tools=("build_dataset", "describe_corpus"),
    never=(
        "influence or gate a trading decision",
        "feed a trained model into the live loop without a promotion gate",
        "mutate source provenance written by other agents (read-only over the graph)",
    ),
)
