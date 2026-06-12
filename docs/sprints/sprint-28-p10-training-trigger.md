<!-- Agent: planning | Role: sprint handover -->
# Sprint 28 — P10 curator: training trigger (advisory predictor + frozen evidence)

**Status:** planned · **Branch:** `sprint-28-p10-training-trigger` · **Build phase:** P10 · **Effort: M**

## Goal

Give the curator a **training trigger**: a `train_predictor` capability that selects a
curator-built dataset, "runs a chosen target" with a **deterministic** baseline trainer, and
writes an **advisory** `Predictor` artifact carrying **frozen evidence** (metrics measured on
the dataset's held-out test split). Everything stays out of band and advisory — the predictor
is never promoted, never load-bearing, never read by any trading-decision agent.

This is the **training half** of P10's exit. It does **not** add a registry or any promotion
— that is Sprint 29 (predictor registry + promotion gate + audit), which **closes P10**.

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails); `docs/build-plan.md` P10 ("a training
  trigger that selects data and runs a chosen target") and the **Advisory before binding**
  principle ("ML … ships shadow first, behind a scorecard, before it can influence a
  decision"); `docs/PRD.md` §7 ("keep ML advisory until measured scorecards earn promotion").
- **This sprint builds on Sprint 27 (shipped).** The curator already assembles versioned
  datasets. Exact node shapes the trainer reads (from `agents/curator/store.py` +
  `agents/curator/domain/manifest.py`):
  - `Dataset` — key `f"dataset:{purpose}:v{version}"`, props `{purpose, version,
    example_count, schema_ref, train_count, validation_count, test_count, created_at}`.
  - `TrainingExample` — key `f"{dataset_id}:{example_id}"` where `example_id =
    f"{purpose}:{position_id}"`; props `{purpose, split, content, label, source_ref,
    run_id, position_id, ticker?}`. `split ∈ {"train","validation","test"}`; `label` is the
    exit trigger (`"stop"|"target"|"time"|"unlabelled"`).
  - Edges: `Dataset -[:CONTAINS]-> TrainingExample`, `TrainingExample -[:DERIVED_FROM]->
    TradeNarrative`.
- **Existing curator code to extend** (read all): `agents/curator/agent.py` (the handler
  pattern + `fault_boundary` degraded-result pattern — `_build_dataset` returns a degraded
  manifest on fault, never raises; mirror it for `_train_predictor`), `agents/curator/
  settings.py`, `agents/curator/store.py` (the graph write path you extend with
  `write_predictor`), `agents/curator/domain/manifest.py` (the `next_version` per-purpose
  counting pattern — mirror it for predictor versioning).
- **The trainer is a deterministic baseline, not real ML.** There is no ML stack in this
  codebase and none is in scope. "Run a chosen target" = fit a **majority-class baseline** on
  the train split and measure it on the test split. This is deterministic, explainable, and
  fully testable — exactly the kind of advisory artifact that a later registry (S29) can gate.
- **Forecaster contract is the conceptual cousin, NOT a dependency.** `contracts/
  forecaster.py` models `ShadowPrediction`/`Scorecard`/`promotion_eligible` for the *runtime*
  advisory-ML path (unimplemented, future phase). Do **not** implement or import the
  forecaster. The curator's `Predictor` is a distinct, out-of-band trained artifact. (S29 will
  decide whether the *registry/promotion* is curator- or forecaster-owned; S28 only produces
  the advisory artifact, which does not foreclose that choice.)
- **`emits` is declarative-only** (no runtime event bus). Nothing to publish.
- **Graph API** (`kernel/graph.py`): `merge_node`, `add_edge`, `get_node`, `list_nodes`,
  `ancestors`/`descendants(node, *, max_depth, edge_types)`. Append-only — props on an
  existing `(label,key)` cannot be overwritten with a conflicting value.
- **Surface pattern**: mirror `surfaces/queries/datasets.py` + `cmd_datasets` (S27) for the
  read-only `cli predictors` view.

## Part A — Contract: add the training capability

`contracts/curator.py` — add the capability, payloads, and owned label. Bump
`version="0.1.0"` → `"0.2.0"` (a capability was added).

```python
# ── Inbound ──
class TrainRequest(_Frozen):
    purpose: str
    version: int | None = None       # None → latest dataset version for this purpose
    target: str = "exit_trigger"     # the label column to predict

# ── Outbound ──
class PredictorManifest(_Frozen):
    predictor_id: str
    dataset_id: str
    purpose: str
    target: str
    strategy: str                    # e.g. "majority_class"
    metrics: dict[str, float]        # frozen evidence: {"accuracy", "train_size", "test_size"}
    sample_size: int                 # test-split size the metrics were measured on
    advisory: bool = True            # ALWAYS True this sprint — never load-bearing
    promotion_eligible: bool = False # ALWAYS False this sprint — promotion is S29
    explanation: Explanation
    provenance: Provenance
```

Add to `consumes`:

```python
Capability(
    "train_predictor",
    "Train an advisory baseline predictor from a curated dataset and freeze its evidence.",
    request=TrainRequest,
    response=PredictorManifest,
    mcp=True,
),
```

Add `"Predictor"` to `owns_graph` → `owns_graph=("Dataset", "TrainingExample", "Predictor")`.

Leave `never`, `depends_on`, `external_io` unchanged. (MCP binding of the new tool is **out of
scope** — Sprint 22's MCP server has a fixed tool list; `mcp=True` is declarative.)

## Part B — Deterministic trainer

### B1. `agents/curator/settings.py` — add two tunables (stays ≤ 60L)

```python
min_train_examples: int = tunable(
    2, why="Below this the train split cannot establish a majority class; training degrades.",
    ge=1, le=10_000, unit="examples",
)
predictor_strategy: str = "majority_class"   # identity, not a knob — plain constant
```

### B2. `agents/curator/domain/training.py` — ≤ 80L

```python
"""Deterministic baseline training over a curated dataset.

Agent: curator
Role: fit a majority-class baseline on the train split and score it on the test split.
External I/O: GraphStore reads (never writes).
"""

@dataclass(frozen=True)
class TrainingResult:
    strategy: str
    prediction: str            # the majority label chosen on train
    metrics: Mapping[str, float]   # {"accuracy", "train_size", "test_size"}
    sample_size: int           # test-split size

def select_dataset(graph: GraphStore, purpose: str, version: int | None) -> Node | None:
    """Return the Dataset node for (purpose, version); latest version when version is None."""

def train_baseline(graph: GraphStore, dataset: Node) -> TrainingResult | None:
    """Fit majority-class on the train split, score on test; None if train split is empty."""
```

Rules (deterministic, read-only):

- `select_dataset`: filter `list_nodes("Dataset")` by `props["purpose"] == purpose`; if
  `version` is given, match `props["version"]`; else pick `max` by `props["version"]`. Return
  `None` if no match.
- Read the dataset's examples: `list_nodes("TrainingExample")` filtered by
  `node.key.startswith(f"{dataset.key}:")`. Partition by `props["split"]`.
- **Majority class**: count `label` values in the **train** split; choose the most frequent,
  tie-broken **alphabetically** (deterministic). If the train split is empty → return `None`.
- **Accuracy**: fraction of **test**-split examples whose `label == prediction`. If the test
  split is empty, `accuracy = 0.0` and `test_size = 0` (degraded but valid — note it in the
  explanation, do not crash).
- `metrics = {"accuracy": <float>, "train_size": float(n_train), "test_size": float(n_test)}`.
  Keep all metric values `float` (the contract's `metrics: dict[str, float]`).

### B3. `agents/curator/store.py` — add `write_predictor` (check size; ~77L → ~100L, ok)

```python
def write_predictor(
    graph: GraphStore, *, manifest: PredictorManifest, dataset: Node
) -> None:
    """Write the Predictor node (frozen evidence in props) and link it to its Dataset."""
```

- `Predictor` node: key = `manifest.predictor_id`, props `{purpose, target, strategy,
  accuracy, train_size, test_size, sample_size, advisory: True, promotion_eligible: False,
  dataset_id, trained_at}` (ISO `trained_at`). The metrics in props **are** the frozen
  evidence (graph props are immutable/append-only).
- Edge: `Predictor -[:TRAINED_ON]-> Dataset` (points into the existing Dataset; does not
  mutate it).

If `write_predictor` pushes `store.py` near the 150L warn band, move it to a new
`agents/curator/predictor_store.py` instead — your call based on the measured count.

### B4. `agents/curator/domain/manifest.py` — add `next_predictor_version` + `build_predictor_manifest` (or a new `predictor_manifest.py` if size demands)

- `next_predictor_version(graph, purpose, target)`: `len([p for p in list_nodes("Predictor")
  if p.props.get("purpose")==purpose and p.props.get("target")==target]) + 1`.
- `predictor_id = f"predictor:{purpose}:{target}:v{version}"`.
- `build_predictor_manifest(...)` assembles `PredictorManifest` from a `TrainingResult`:
  - `explanation = Explanation(summary=f"{strategy} predictor for {target} on {dataset_id}: "
    f"accuracy {accuracy:.2f} over {test_size} test examples (advisory; not promoted).")`.
  - `provenance = Provenance(run_id=predictor_id, source_agent="curator",
    graph_node_id=f"Predictor:{predictor_id}")`.
  - `advisory=True`, `promotion_eligible=False` (hard-coded this sprint).

Keep modules ≤ 150L; split a new `predictor_manifest.py` if `manifest.py` would exceed it.

### B5. `agents/curator/agent.py` — add `_train_predictor` (stays ≤ 150L)

- Register `"train_predictor": self._train_predictor` in `self.handlers`.
- `_train_predictor(request) -> PredictorManifest`, mirroring `_build_dataset`'s
  `fault_boundary` + degraded-fallback pattern (never raises):
  1. `model = TrainRequest.model_validate(request)`.
  2. `dataset = select_dataset(graph, model.purpose, model.version)`.
     If `None` → return a **degraded** `PredictorManifest` (empty metrics, `sample_size=0`,
     advisory, explanation "no dataset found for <purpose>"). Do not write a Predictor node
     when there is no dataset.
  3. `result = train_baseline(graph, dataset)`. If `None` (empty train split) → degraded
     manifest explaining the train split was too small; still no Predictor node written.
  4. `version = next_predictor_version(...)`, `predictor_id = …`.
  5. `manifest = build_predictor_manifest(...)`; `write_predictor(graph, manifest=…,
     dataset=dataset)`.
  6. Return `manifest`.
- If `min_train_examples` is not met, treat as the empty-train degraded path (step 3).

`PredictorManifest` and the new domain imports stay within the curator package — no new
external dependency, no agent import.

## Part C — Predictors surface

### C1. `surfaces/queries/predictors.py` — ≤ 50L

```python
@dataclass(frozen=True)
class PredictorView:
    predictor_id: str
    purpose: str
    target: str
    strategy: str
    accuracy: float
    sample_size: int
    advisory: bool        # always True this sprint

def all_predictors(graph: GraphStore) -> tuple[PredictorView, ...]:
    """Return all predictors, newest first (by purpose, target, version desc)."""
```

### C2. `surfaces/render_extras.py` — add `render_predictors` (render.py stays untouched at 175L)

```python
def render_predictors(views: tuple[PredictorView, ...]) -> str:
    if not views:
        return "no predictors trained"
    lines = [f"Predictors: {len(views)}"]
    for v in views:
        lines.append(
            f"  [{v.predictor_id}] {v.strategy} acc={v.accuracy:.2f} "
            f"n={v.sample_size} (advisory)"
        )
    return "\n".join(lines)
```

Match the sibling renderers' return-string convention (confirm against `render_datasets`).

### C3. `surfaces/cli_commands_queries.py` — add `cmd_predictors`; `surfaces/cli.py` — add the `predictors` subcommand

Mirror `cmd_datasets` / the `datasets` subparser + dispatch line from S27.

**Note:** `cli predictors` is read-only. Triggering training from the operator command layer
(operator grammar → supervisor → curator) is **out of scope** — the trigger this sprint is the
`train_predictor` bus capability, invoked by tests (and later a scheduler/MCP). Surfaces read;
they do not drive the curator directly.

## Part D — Tests

### D1. `agents/curator/tests/test_training.py` — ≤ 80L

Seed a `Dataset` + `TrainingExample` nodes directly (or reuse the S27 helper to
`build_dataset` from seeded narratives, then train). Cover:

- Train split labels `["target","target","stop"]`, test `["target"]` → majority `"target"`,
  `accuracy == 1.0`, `train_size==3`, `test_size==1`.
- Tie in train (`["stop","target"]`) → alphabetical tie-break picks `"stop"`.
- Empty test split → `accuracy == 0.0`, `test_size == 0`, still a valid `TrainingResult`.
- Empty train split → `train_baseline` returns `None`.
- `select_dataset`: latest-version selection when `version is None`; exact match when given;
  `None` for an unknown purpose.

### D2. `agents/curator/tests/test_train_predictor.py` — ≤ 90L

Bind a `CuratorAgent` on `InMemoryGraphStore`; seed narratives → `build_dataset` →
`train_predictor` over the bus:

- Response validates as `PredictorManifest`; `advisory is True`; `promotion_eligible is
  False`; `metrics["accuracy"]` present; `sample_size == test_count`.
- Graph: exactly one `Predictor` node; `Predictor -[:TRAINED_ON]-> Dataset` edge present;
  props carry the frozen metrics.
- A **second** `train_predictor` for the same `(purpose, target)` → `version` increments
  (`predictor:…:v2`).
- `train_predictor` with a `purpose` that has **no dataset** → degraded manifest
  (`sample_size == 0`, empty/zero metrics), and **no** `Predictor` node written.

### D3. `agents/curator/tests/test_p10_training_boundary.py` — ≤ 60L

Extend the P10 invariant to training: `train_predictor` writes only the curator's `Predictor`
node and is read-only over everything else (including its source `Dataset`/`TrainingExample`).

```python
def test_train_predictor_mutates_no_prior_node() -> None:
    # Seed narratives → build_dataset. Snapshot ALL nodes except {"Predictor"} → (label,key)->props.
    # Run train_predictor. Re-snapshot. Assert after == before; assert a Predictor node exists.
```

Snapshot every label the test created **except** `Predictor` (so `Dataset`, `TrainingExample`,
`Position`, `TradeNarrative`, `CloseDecision` are all proven untouched). The `TRAINED_ON` edge
appends from the `Predictor` side only.

### D4. `surfaces/tests/test_predictors_surface.py` — ≤ 55L

- `all_predictors` empty → `()`; with one `Predictor` node → one `PredictorView` with right
  fields.
- `cli predictors` empty → `"no predictors trained"`; populated → output contains the
  `predictor_id` and `acc=`.

## Steps

1. Branch `sprint-28-p10-training-trigger` off `main`.
2. **Part A** contract change; run the boundary meta-test + mypy. `make ci`.
3. **Part B** settings → training → store → manifest → agent. `make ci` after the agent.
4. **Part C** predictors query → render → cli_commands_queries → cli.
5. **Part D** all tests; `make ci` final — fully green.
6. **Line-count check**: `wc -l agents/curator/agent.py agents/curator/store.py
   agents/curator/domain/*.py surfaces/queries/predictors.py`. All < 200L; none over the warn
   band without reason.
7. Push; hand back.

## Acceptance criteria

- `curator.train_predictor` on a dataset with a non-empty train split writes one `Predictor`
  node with a `TRAINED_ON` edge to its `Dataset`, frozen metrics in props, and returns a valid
  `PredictorManifest` with `advisory is True`, `promotion_eligible is False`.
- The baseline is deterministic: same dataset → same prediction, accuracy, and metrics; ties
  broken alphabetically.
- Re-training the same `(purpose, target)` increments the predictor version.
- `train_predictor` with no matching dataset (or too-small train split) → degraded manifest,
  no crash, **no** `Predictor` node written.
- **`test_p10_training_boundary.py` green:** every non-`Predictor` node is identical before/
  after training.
- `cli predictors` empty → "no predictors trained"; populated → shows predictor_id + accuracy.
- Import-linter 4/4 kept (curator imports only `kernel` + `contracts`; forecaster NOT
  imported or implemented).
- `make ci` green at/above the coverage floor (100.00); raise it only if measured coverage
  climbs.

## Out of scope (do NOT build this sprint)

- **The predictor registry, any promotion (advisory → load-bearing), promotion audit, or
  operator approval of a predictor** — all of that is **Sprint 29 (P10 exit)**.
- Implementing or importing the **forecaster** agent / its runtime `forecast` path.
- Real ML (any model beyond the deterministic majority-class baseline).
- A real file/blob predictor store (the Predictor lives in the graph; persisting model
  binaries is build-when-needed).
- Operator-command-layer training trigger (`cli predictors` is read-only this sprint).
- MCP binding of `train_predictor`.

## P10 status after this sprint (planning agent updates on review)

Still **active** (not complete). After S28, P10 has: versioned datasets (S27) + an advisory
trained predictor with frozen evidence (S28). The exit ("a predictor promoted through the
registry") still needs **Sprint 29** — the registry + promotion gate + promotion-audit test.

## Handback report (paste into PR / reply)

- Confirm the contract change (capability + payloads + `owns_graph` + version bump) and that
  the boundary meta-test stayed green.
- Whether `write_predictor` / the predictor manifest helpers stayed in `store.py`/`manifest.py`
  or needed new modules (and the resulting line counts).
- The majority-class tie-break behaviour as implemented (confirm alphabetical, deterministic).
- `test_p10_training_boundary.py` result (confirm before/after node-snapshot equality).
- Final line counts: agent.py, training.py, store.py, manifest.py.
- New coverage % and floor; total test count.

The planning agent reviews, merges to `main`, keeps P10 active, and plans **Sprint 29**
(predictor registry + promotion gate + audit — closes P10; decides registry ownership
curator vs forecaster at that point).
