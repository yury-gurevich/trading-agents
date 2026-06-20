# `Curator` — Laws

**Prefix:** `CUR` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Curate the collected provenance graph into clean, labelled, versioned datasets ready
> for later LLM training — running out of band, alongside trading, never touching the
> live decision loop.

Each clause has a stable ID (`CUR-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **CUR-IDN-01** — The curator's single job is out-of-band data engineering: traverse the
  provenance graph, assemble versioned training datasets, train advisory predictors, and gate
  their promotion. It runs alongside trading and has zero influence over the live decision loop.
- **CUR-IDN-02** — The curator exclusively writes these graph labels (single-writer rule):
  `Dataset`, `TrainingExample`, `Predictor`, `PredictorPromotion`.

## Inputs (`IN`)

- **CUR-IN-01** — `build_dataset` accepts `DatasetRequest { purpose, lookback_days=365,
  train_val_test=(0.8,0.1,0.1) }`.
- **CUR-IN-02** — `describe_corpus` accepts `DatasetRequest` (same schema).
- **CUR-IN-03** — `train_predictor` accepts `TrainRequest { purpose, version: int|None,
  target="exit_trigger" }`.
- **CUR-IN-04** — `promote_predictor` accepts `PromoteRequest { predictor_id: str }`.
- **CUR-IN-05** — Malformed input → degraded manifest or `PromotionResult(status="rejected", ...)`
  returned; fault recorded; never raises to bus.

## Triggers (`TRG`)

- **CUR-TRG-01** — All capabilities triggered by RPC request from the operator (via surfaces) or
  the dispatcher.
- **CUR-TRG-02** — No event subscription; the curator never self-triggers.
- **CUR-TRG-03** — Out-of-band operation: `build_dataset` and `train_predictor` may be invoked
  manually at any time without pipeline dependency.

## Outputs (`OUT`)

- **CUR-OUT-01** — `build_dataset` returns `DatasetManifest { dataset_id, version, purpose,
  example_count, splits, schema_ref, explanation, provenance }`.
- **CUR-OUT-02** — `describe_corpus` returns `Explanation` describing available narratives,
  snapshots, and prior datasets for the requested purpose.
- **CUR-OUT-03** — `train_predictor` returns `PredictorManifest { predictor_id, dataset_id,
  purpose, target, strategy, metrics, sample_size, advisory=True, promotion_eligible=False,
  explanation, provenance }`.
- **CUR-OUT-04** — `advisory=True` and `promotion_eligible=False` are structural on every
  `PredictorManifest`; no code path changes them at train time.
- **CUR-OUT-05** — `promote_predictor` returns `PromotionResult { predictor_id, status, state,
  reason, explanation, provenance }`. Status is one of `"promoted"`, `"pending_approval"`,
  `"rejected"`, `"already_promoted"`, `"not_found"`.
- **CUR-OUT-06** — `Dataset`, `TrainingExample`, `Predictor`, and `PredictorPromotion` nodes are
  written to the graph as part of their respective capability calls.

## Prohibitions (`NEV`)

- **CUR-NEV-01** — Never influences or gates a live trading decision. No write path to
  `OrderIntent`, `Recommendation`, or `CloseDecision`.
- **CUR-NEV-02** — Never feeds a trained model into the live loop without a promotion gate.
  A predictor is advisory until `promote_predictor` passes the frozen-evidence + operator-approval
  gate.
- **CUR-NEV-03** — Never mutates source provenance written by other agents. All reads of
  `Snapshot`, `TradeNarrative`, `Recommendation`, etc. are read-only.
- **CUR-NEV-04** — Never writes a model artefact to the graph or the dataset store without first
  computing frozen evidence metrics (accuracy, sample_size); degraded paths skip storage entirely.

## State & effects (`STA`)

- **CUR-STA-01** — Stateless between calls. No in-memory dataset cache survives across
  invocations.
- **CUR-STA-02** — Graph writes are append-only. `Dataset` and `Predictor` nodes accumulate per
  version; none are overwritten.
- **CUR-STA-03** — The external `dataset_store` is write-only from the curator's perspective;
  it never reads back from the store to affect decision logic.

## Determinism & idempotency (`IDM`)

- **CUR-IDM-01** — Given the same graph state, `build_dataset(purpose)` produces the same
  `DatasetManifest` structure (same example count, same split sizes). Version numbering is
  deterministic (`next_version` reads existing nodes).
- **CUR-IDM-02** — Not globally idempotent: re-running `build_dataset` with the same purpose
  increments the version and writes a new `Dataset` node.
- **CUR-IDM-03** — `train_predictor` with the same `dataset_id` produces a new `Predictor` node
  with frozen evidence; re-training is safe but not free.

## Ordering & concurrency (`ORD`)

- **CUR-ORD-01** — `build_dataset` must precede `train_predictor` for the same purpose (the
  train request references a dataset version).
- **CUR-ORD-02** — `train_predictor` must precede `promote_predictor` for the same
  `predictor_id`.
- **CUR-ORD-03** — Concurrent `build_dataset` calls for the same purpose may produce duplicate
  version numbers; callers are responsible for serialising builds.

## Failure, recovery & rollback (`FAIL`)

- **CUR-FAIL-01** — `build_dataset` assembly error: `fault_boundary` captures; `degraded_manifest`
  returned; fault emitted; no `Dataset` node written.
- **CUR-FAIL-02** — Dataset store write failure: second `fault_boundary` captures; manifest is
  still returned (in-graph write succeeded); only external store write is lost.
- **CUR-FAIL-03** — `train_predictor` failure: `degraded_predictor_manifest` returned; fault
  emitted; no `Predictor` node written.
- **CUR-FAIL-04** — `promote_predictor` failure or evidence gate rejection:
  `PromotionResult(status="rejected", ...)` returned; fault emitted.
- **CUR-FAIL-05** — Insufficient examples (`len < min_examples_for_split`): `build_dataset`
  returns a manifest with all examples in the train split (degenerate split); no failure.

## Type alignment (`TYP`)

- **CUR-TYP-01** — `DatasetManifest`, `PredictorManifest`, and `PromotionResult` match
  `contracts/curator.py` exactly.
- **CUR-TYP-02** — `metrics` in `PredictorManifest` is `dict[str, float]`; `accuracy` and
  `train_size`/`test_size` are always present after a successful train.
- **CUR-TYP-03** — `train_val_test` split fractions sum to 1.0 (validated by `DatasetRequest`);
  the curator does not re-validate.

## Security & privilege (`SEC`)

- **CUR-SEC-01** — Holds no credentials. Dataset store access is through the injected
  `DatasetStore` port; the curator has no direct file-system or cloud-storage authority.
- **CUR-SEC-02** — Never logs training data or predictor weights to external systems.
- **CUR-SEC-03** — `promote_predictor` requires operator approval (gated by the supervisor's
  dispatch path); the curator cannot self-approve a promotion.

## Dependencies (`DEP`)

- **CUR-DEP-01** — `DEP-NEO4J` — reads `Snapshot`, `TradeNarrative`, and related nodes for
  dataset assembly; writes `Dataset`, `Predictor`, `PredictorPromotion`.
- **CUR-DEP-02** — `DEP-BUS` — routes `promote_predictor` through the supervisor approval gate.

## Observability & audit (`OBS`)

- **CUR-OBS-01** — A `Dataset` node is written per `build_dataset` call; version history is
  reconstructable from the graph.
- **CUR-OBS-02** — A `Predictor` node with frozen evidence metrics is written per
  `train_predictor`; `PredictorPromotion` nodes record the promotion audit trail.
- **CUR-OBS-03** — Degraded paths emit faults to the sink; never buried.

## Performance envelope (`PERF`)

- **CUR-PERF-01** — `max_examples=5000` caps a single dataset build; prevents unbounded graph
  traversal during a build run.
- **CUR-PERF-02** — `min_examples_for_split=3` degenerate threshold ensures build completes on
  thin corpora without error.

## Capability declaration (`CAP`)

```json
{
  "graph": {
    "operations": ["append_write", "read"],
    "labels_owned": [
      "Dataset", "TrainingExample", "Predictor", "PredictorPromotion"
    ],
    "labels_read": ["Snapshot", "TradeNarrative", "Recommendation"]
  },
  "dataset_store": {
    "operations": ["write"],
    "format": "application/json"
  },
  "messaging": {
    "operations": ["request"],
    "peers": ["supervisor"]
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `max_examples` | `5000` | `int ≥ 1 ≤ 100000` | YES | Cap dataset build so out-of-band work never starves trading |
| `min_examples_for_split` | `3` | `int ≥ 3 ≤ 1000` | YES | Below this a 3-way split cannot fill each split; build degrades |
| `schema_ref` | `"curator.training_example.v1"` | `str` | NO | Structural identity of the example schema; non-tunable |
| `min_train_examples` | `2` | `int ≥ 1 ≤ 10000` | YES | Below this the train split cannot establish a majority class |
| `predictor_strategy` | `"majority_class"` | `str` | NO | Training algorithm identity; structural |
| `min_promotion_accuracy` | `0.55` | `float ≥ 0.0 ≤ 1.0` | YES | Frozen-evidence floor for promotable predictors |
| `min_promotion_sample_size` | `5` | `int ≥ 1 ≤ 100000` | YES | Minimum test-split size to trust the accuracy figure |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| — | — | — | no known drift |

## Changelog

- v1 — authored S71 and locked immediately (full first-principles cycle).
