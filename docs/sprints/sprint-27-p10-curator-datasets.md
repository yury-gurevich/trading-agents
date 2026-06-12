<!-- Agent: planning | Role: sprint handover -->
# Sprint 27 — P10 curator: dataset assembly by provenance traversal (P10 begins)

**Status:** planned · **Branch:** `sprint-27-p10-curator-datasets` · **Build phase:** P10 · **Effort: M–L**

## Goal

Implement the curator agent's two `consumes` capabilities — `build_dataset` and
`describe_corpus` — assembling clean, labelled, **versioned** training datasets from the
provenance graph by **read-only traversal**, splitting them train/validation/test, writing
`Dataset` + `TrainingExample` nodes and persisting the payload through a `dataset_store`
boundary. Prove P10's core invariant from day one: **the curator never influences or mutates
a trading decision** — running `build_dataset` leaves every non-curator node byte-for-byte
unchanged and writes only curator-owned nodes.

This sprint **begins** P10. It does **not** close it: the training trigger and predictor
registry (advisory → load-bearing promotion gate) are Sprint 28 (P10 exit).

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails); `docs/architecture.md`;
  `docs/build-plan.md` P10 ("dataset assembly by provenance-graph traversal … clean,
  labelled, versioned, with train/validation/test splits") and the cross-cutting
  **Training-data curation** workstream; `agents/curator/mission.md`.
- **Contract is already fully declared** — do **not** edit it unless §A flags it:
  `contracts/curator.py` — `build_dataset(DatasetRequest) -> DatasetManifest`,
  `describe_corpus(DatasetRequest) -> Explanation`; `owns_graph=("Dataset",
  "TrainingExample")`; `external_io=("dataset_store",)`; `depends_on=("reporter",
  "supervisor")`; `emits=("dataset_published",)`.
  - `DatasetRequest`: `purpose: str`, `lookback_days: int = 365`,
    `train_val_test: tuple[float, float, float] = (0.8, 0.1, 0.1)`.
  - `DatasetManifest`: `dataset_id`, `version`, `purpose`, `example_count`,
    `splits: tuple[DatasetSplit, ...]`, `schema_ref`, `explanation: Explanation`,
    `provenance: Provenance`.
  - `DatasetSplit`: `name: Literal["train","validation","test"]`, `example_count: int`.
- `agents/curator/__init__.py` is a stub — full implementation this sprint. The package
  imports **only** `kernel` and `contracts`, never another agent (import-linter enforces).
- **Training-example source = the provenance graph the other agents already wrote.** The
  natural corpus unit is reporter's `TradeNarrative` node (one completed scan→exit story per
  position). See `agents/reporter/store.py`:
  - `TradeNarrative` — key `f"narrative:{position_id}"`, props `{run_id, position_id,
    summary}`, edge `TradeNarrative -[:NARRATES]-> Position`.
  - `Snapshot` — key `f"snapshot:{run_id}"`, props `{run_id, metrics, headline_summary}`.
  The curator reads these with `graph.list_nodes("TradeNarrative")` /
  `list_nodes("Snapshot")` — graph reads are always permitted, no bus call, no import.
- **Graph API** (`kernel/graph.py`, `GraphStore` Protocol): `merge_node(label, key, props)`,
  `add_edge(parent, child, edge_type)`, `get_node(label, key)`, `list_nodes(label)`,
  `ancestors(node, *, max_depth, edge_types=None)`, `descendants(node, *, max_depth,
  edge_types=None)`. All writes are append-only; props on an existing `(label, key)` may not
  be overwritten with a conflicting value.
- **`emits` is declarative-only.** There is no runtime event bus — the bus is request/
  response (`bus.request`). `dataset_published` stays a contract declaration; do **not** try
  to publish a runtime event. "Publishing" a dataset = writing the `Dataset` node +
  `dataset_store` payload + returning the manifest.
- **Port pattern** to mirror: `agents/provider/sources.py` (`DataSource` Protocol +
  `FakeDataSource`). The `dataset_store` boundary follows the same shape.
- **Surface pattern** to mirror: `surfaces/queries/proposals.py` + `cmd_proposals` in
  `surfaces/cli_commands_queries.py` + the `proposals` subparser/dispatch in
  `surfaces/cli.py` (lines 50, 83). `cli datasets` is the read-only analogue.

## Part A — Contract dependency reconciliation (verify first, edit only if needed)

`contracts/curator.py` declares `depends_on=("reporter", "supervisor")`. This sprint's
curator reads reporter-owned nodes **via the graph** (not a bus call) and makes **no
supervisor call**. Run the boundary meta-test early (`uv run pytest -k boundary` or the
meta-test that checks contract `depends_on`) and determine its rule:

- If the meta-test requires declared deps to be **exercised** (a real bus call): drop
  `"supervisor"` (and `"reporter"`, since graph reads aren't bus calls) so
  `depends_on=()` — the curator depends on no agent at runtime. **Justify in the PR.**
- If the meta-test only requires that *used* deps are *declared* (the more likely rule):
  leave the contract untouched.

Make the minimal change that keeps the gate green and **state which rule applied** in the
handback. Do not add a gratuitous supervisor call just to satisfy a declaration.

## Part B — Curator agent

### B1. `agents/curator/settings.py` — ≤ 60L

```python
"""Curator agent settings and dataset-assembly tunables.

Agent: curator
Role: own defaults for corpus selection, minimum dataset size, and the example schema ref.
External I/O: process environment and the .env file.
"""

class CuratorSettings(AgentSettings):
    model_config = SettingsConfigDict(env_prefix="CURATOR_", frozen=True)

    max_examples: int = tunable(
        5000, why="Cap a single dataset build so out-of-band work never starves trading.",
        ge=1, le=100_000, unit="examples",
    )
    min_examples_for_split: int = tunable(
        3, why="Below this, a 3-way split cannot place ≥1 example per split; build is degraded.",
        ge=3, le=1000, unit="examples",
    )
    schema_ref: str = "curator.training_example.v1"
```

`schema_ref` is a plain versioned string constant, not a tunable (it is an identity, not a
bounded knob). Justify each `why` properly — no placeholders.

### B2. `agents/curator/dataset_store.py` — ≤ 60L

The `external_io=("dataset_store",)` boundary, mirroring `provider/sources.py`.

```python
"""Curator dataset-store ports and a deterministic in-memory store.

Agent: curator
Role: isolate curated-dataset writes behind a DatasetStore boundary.
External I/O: writes curated dataset payloads to the configured store.
"""

class DatasetStore(Protocol):
    def write(self, dataset_id: str, payload: Mapping[str, Any]) -> None:
        """Persist one curated dataset payload, keyed by dataset_id."""
        ...  # pragma: no cover - protocol declaration only.

class FakeDatasetStore:
    """In-memory store used by the unit gate; payloads inspectable via .written."""
    def __init__(self) -> None:
        self.written: dict[str, Mapping[str, Any]] = {}
    def write(self, dataset_id: str, payload: Mapping[str, Any]) -> None:
        self.written[dataset_id] = payload
```

A real (file-based) store is **out of scope** — deferred build-when-needed. The agent
defaults to `FakeDatasetStore()` when none is injected (so binding stays a one-liner).

### B3. `agents/curator/domain/assembly.py` — ≤ 90L

Read-only provenance traversal → ordered training-example records.

```python
"""Training-example assembly by provenance-graph traversal.

Agent: curator
Role: reduce completed TradeNarrative lineage into ordered, labelled example records.
External I/O: GraphStore reads (never writes).
"""

@dataclass(frozen=True)
class ExampleRecord:
    example_id: str          # f"{purpose}:{position_id}"
    content: str             # the narrative summary (the SFT/training text)
    label: str               # supervised target; see below
    source_ref: str          # source node id: f"TradeNarrative:{narrative.key}"
    metadata: Mapping[str, str]   # assembled context: run_id, position_id, ticker, trigger

def assemble_examples(
    graph: GraphStore, *, purpose: str, max_examples: int
) -> tuple[ExampleRecord, ...]:
    """Assemble examples from all TradeNarrative nodes, deterministically ordered."""
```

Rules (deterministic, no I/O):

- Source corpus = `graph.list_nodes("TradeNarrative")`.
- **Deterministic order:** sort by `node.key` ascending, then truncate to `max_examples`.
  (Reproducible ordering is what makes versioned splits stable.)
- For each narrative:
  - `content` = `props["summary"]`.
  - `source_ref` = `f"TradeNarrative:{node.key}"`.
  - **Label** = the realized exit trigger. Reach it by traversing
    `descendants(narrative, max_depth=2, edge_types={"NARRATES", "CLOSES"})` to find the
    `CloseDecision` reachable through the Position, and read its `props["trigger"]`
    (`"stop" | "target" | "time"`). If none is reachable, label = `"unlabelled"`.
    *(Confirm the actual edge from Position to CloseDecision by reading
    `agents/monitor/store.py` / `agents/reporter/domain/lineage.py`; the reporter lineage
    module already traverses `CLOSES` — reuse the same edge-type name. Do NOT import the
    reporter module; just match the edge string.)*
  - `metadata` = `{"run_id": props["run_id"], "position_id": props["position_id"]}` plus any
    cheaply reachable fields (ticker from the Position node if present). Keep values as
    strings (graph props for examples are simple/serialisable).
- Lookback filtering is a **P10-begins simplification**: take all narratives up to
  `max_examples` (timestamp filtering deferred — note it as out of scope). Do not invent a
  date field that isn't on the node.

### B4. `agents/curator/domain/split.py` — ≤ 60L

Deterministic train/validation/test partition.

```python
"""Deterministic dataset splitting.

Agent: curator
Role: partition ordered example records into train/validation/test by ratio.
External I/O: none.
"""

@dataclass(frozen=True)
class SplitAssignment:
    train: tuple[ExampleRecord, ...]
    validation: tuple[ExampleRecord, ...]
    test: tuple[ExampleRecord, ...]

def split_examples(
    records: tuple[ExampleRecord, ...], ratios: tuple[float, float, float]
) -> SplitAssignment:
    """Partition records by cumulative ratio over their stable order."""
```

Rules:

- Validate `ratios`: each ≥ 0, `abs(sum(ratios) - 1.0) < 1e-9`. On violation raise
  `ValueError` (caught by the agent's `fault_boundary` → a degraded outcome, not a crash).
- Partition by **index over the already-stable order** (records arrive pre-sorted from
  assembly): `n_train = int(len(records) * ratios[0])`, `n_val = int(len(records) *
  ratios[1])`, test = remainder. Index-based partitioning on a stable order is reproducible
  across builds → identical inputs yield identical splits (versioning integrity).
- This is deterministic and needs no tunable (ratios come from the request).

### B5. `agents/curator/domain/manifest.py` — ≤ 70L

Versioning + manifest construction.

```python
"""Dataset manifest assembly and version numbering.

Agent: curator
Role: compute the next dataset version and build the DatasetManifest payload.
External I/O: GraphStore reads (version lookup).
"""

def next_version(graph: GraphStore, purpose: str) -> int:
    """Next 1-based version for this purpose = count of existing Dataset nodes + 1."""

def build_manifest(
    *, graph, purpose, schema_ref, split, dataset_id, version
) -> DatasetManifest:
    """Assemble the DatasetManifest from a SplitAssignment."""
```

Rules:

- `next_version`: `len([d for d in graph.list_nodes("Dataset")
  if d.props.get("purpose") == purpose]) + 1`. First build of a purpose → version 1.
- `dataset_id` = `f"dataset:{purpose}:v{version}"`.
- `splits` = three `DatasetSplit` entries with counts from the `SplitAssignment`.
- `example_count` = total across splits.
- `explanation` = `Explanation(summary=f"{example_count} examples for {purpose} (v{version}):
  {n_train}/{n_val}/{n_test} train/val/test", evidence_refs=(source_refs…))` — keep
  `evidence_refs` bounded (e.g. first ≤ 10 source_refs) so the payload stays small.
- `provenance` = `Provenance(run_id=dataset_id, source_agent="curator",
  graph_node_id=f"Dataset:{dataset_id}")`.

### B6. `agents/curator/store.py` — ≤ 80L

Graph write path (curator-owned nodes only; source provenance is referenced, never mutated).

```python
"""Curator graph write path.

Agent: curator
Role: write Dataset and TrainingExample nodes and link them to source provenance.
External I/O: GraphStore writes via the injected backend.
"""

def write_dataset(
    graph: GraphStore, *, manifest: DatasetManifest, split: SplitAssignment
) -> None:
    """Write the Dataset node, one TrainingExample per record, and provenance edges."""
```

Rules:

- `Dataset` node: key = `manifest.dataset_id`, props `{purpose, version, example_count,
  schema_ref, train_count, validation_count, test_count, created_at}` (ISO `created_at`).
- For each record in each split: `TrainingExample` node, key =
  `f"{manifest.dataset_id}:{record.example_id}"`, props `{purpose, split, content, label,
  source_ref, **metadata}`.
- Edges:
  - `Dataset -[:CONTAINS]-> TrainingExample` (curator-internal).
  - `TrainingExample -[:DERIVED_FROM]-> <source TradeNarrative node>` — look the source up
    with `graph.get_node("TradeNarrative", source_key)` and add the edge **only if present**.
    `DERIVED_FROM` points *into* existing provenance; it appends an edge, it does **not**
    modify the source node. This is the read-only-over-source guarantee made concrete.

### B7. `agents/curator/agent.py` — ≤ 110L

```python
"""Curator agent — assemble versioned training datasets from the provenance graph.

Agent: curator
Role: out-of-band data engineering; build/describe datasets, never touch the decision loop.
External I/O: MessageBus binding; dataset_store writes.
"""
```

- Ctor: `CuratorAgent(bus, *, graph, dataset_store=None, settings=None, sink=None)`.
  Default `dataset_store` to `FakeDatasetStore()`, `settings` to `CuratorSettings()`,
  `sink` to `CollectingFaultSink()` when not injected (match the other agents).
- `bind()` registers `build_dataset` and `describe_corpus`.
- `_build_dataset(request: DatasetRequest) -> DatasetManifest`, wrapped in `fault_boundary`:
  1. `records = assemble_examples(graph, purpose=req.purpose, max_examples=settings.max_examples)`.
  2. If `len(records) < settings.min_examples_for_split`: return a **degraded manifest** —
     `version = next_version(...)`, `example_count = len(records)`, empty/partial splits, and
     an `Explanation` stating the corpus is too small. Do **not** raise. (Still write the
     Dataset node so the attempt is auditable, with whatever examples exist.)
  3. `split = split_examples(records, req.train_val_test)`.
  4. `version = next_version(graph, req.purpose)`; `dataset_id = f"dataset:{purpose}:v{version}"`.
  5. `manifest = build_manifest(...)`.
  6. `write_dataset(graph, manifest=manifest, split=split)`.
  7. `dataset_store.write(dataset_id, payload)` — `payload` = a serialisable dict of the
     splits (example_id → {content, label, split, source_ref}). Route through `fault_boundary`
     so a store failure degrades, not crashes.
  8. Return `manifest`.
- `_describe_corpus(request: DatasetRequest) -> Explanation`:
  - Count `list_nodes("TradeNarrative")`, `list_nodes("Snapshot")`, and existing
    `list_nodes("Dataset")` for this purpose. Return
    `Explanation(summary=f"{n_narratives} completed-trade narratives and {n_snapshots} run
    snapshots available; {n_existing} prior {purpose} dataset(s).", evidence_refs=…)`.
  - If the corpus is empty: `Explanation(summary="no training corpus collected yet", …)`.

### B8. Bind the curator

In `orchestration/bindings.py`, add one line at the end of `bind_paper_loop_agents`:

```python
CuratorAgent(bus, graph=graph, sink=sink).bind()
```

**Out-of-band note:** binding only *registers handlers*; it does **not** put the curator in
the dispatcher's scan→…→report run sequence (the dispatcher never calls `build_dataset`). The
curator is invoked only by an explicit `build_dataset`/`describe_corpus` request (the P10
exit test, the CLI, later MCP/scheduler). Registering its handlers in the shared context is
what lets `cli datasets` and the tests reach it; it stays out of the trading loop.

`surfaces/context.py` needs **no signature change** — the curator self-defaults its
`dataset_store`. (Tests that want to inspect the store can construct a `CuratorAgent` with an
injected `FakeDatasetStore` directly.)

## Part C — Datasets surface

### C1. `surfaces/queries/datasets.py` — ≤ 55L

```python
"""Dataset query projections.

Agent: surfaces
Role: read Dataset nodes and project dataset views, newest first.
External I/O: GraphStore reads.
"""

@dataclass(frozen=True)
class DatasetView:
    dataset_id: str
    purpose: str
    version: int
    example_count: int
    train_count: int
    validation_count: int
    test_count: int

def all_datasets(graph: GraphStore) -> tuple[DatasetView, ...]:
    """Return all datasets, newest first (by purpose then version desc)."""
```

### C2. `surfaces/render.py` — `render_datasets` (check headroom first)

`render.py` was ~159–165L after the Sprint 23 `render_extras` extraction. **Check its current
line count.** If adding `render_datasets` (~12L) would exceed ~185L, first move the dataset/
pack-style renderers into `surfaces/render_extras.py` (zero-behaviour refactor; run `make ci`
green before continuing) — mirror Sprint 23 Part A0. Otherwise add `render_datasets` inline:

```python
def render_datasets(views: tuple[DatasetView, ...]) -> str:
    if not views:
        return "no datasets built"
    lines = [f"Datasets: {len(views)}"]
    for v in views:
        lines.append(
            f"  [{v.dataset_id}] {v.example_count} examples "
            f"({v.train_count}/{v.validation_count}/{v.test_count})"
        )
    return "\n".join(lines)
```

Match the **return-string** convention of the other `cmd_*`/`render_*` in this codebase
(the CLI `_dispatch` returns a string that `main` writes — see `surfaces/cli.py`). Confirm
whether sibling renderers return a string or print to `out`, and match exactly.

### C3. `surfaces/cli_commands_queries.py` — add `cmd_datasets`

```python
def cmd_datasets(args: argparse.Namespace, ctx: SurfaceContext) -> str:
    del args
    return render_datasets(all_datasets(ctx.graph))
```

### C4. `surfaces/cli.py` — add the `datasets` subcommand

- Add `sub.add_parser("datasets")` beside `proposals`/`packs` (line ~50).
- Add to `_dispatch`: `if args.command == "datasets": return
  cli_commands_queries.cmd_datasets(args, ctx)` (beside line ~84).

## Part D — Tests

### D1. `agents/curator/tests/__init__.py` — empty marker

### D2. `agents/curator/tests/helpers.py` — ≤ 60L

A small builder that seeds N `TradeNarrative` nodes (and their `Position` + `CloseDecision`
lineage with a known `trigger`) into an `InMemoryGraphStore`, plus a `build_dataset_message`
factory. Mirror `agents/researcher/tests/helpers.py`.

### D3. `agents/curator/tests/test_assembly.py` — ≤ 70L

- Empty graph → `assemble_examples` returns `()`.
- 5 narratives with reachable `CloseDecision{trigger="target"}` → 5 records, each
  `label == "target"`, ordered by key, `content == summary`.
- A narrative with no reachable CloseDecision → `label == "unlabelled"`.
- `max_examples=2` over 5 narratives → exactly 2 records (first two by key order).

### D4. `agents/curator/tests/test_split.py` — ≤ 60L

- 10 records, ratios `(0.8, 0.1, 0.1)` → counts `8/1/1`; partition is contiguous over input
  order; same input twice → identical assignment (determinism).
- ratios summing to ≠ 1.0 → `ValueError`.
- 3 records, `(0.8,0.1,0.1)` → `2/0/1` (document the int-floor behaviour; it is deterministic).

### D5. `agents/curator/tests/test_manifest.py` — ≤ 50L

- `next_version` on empty graph for purpose "x" → 1; after one `Dataset{purpose:"x"}` → 2;
  a different purpose stays at 1 (per-purpose versioning).
- `build_manifest` → `dataset_id == "dataset:x:v1"`, `example_count` = sum of split counts,
  three `DatasetSplit` entries, non-empty `explanation.summary`.

### D6. `agents/curator/tests/test_build_dataset.py` — ≤ 90L

Bind a `CuratorAgent` on an `InMemoryGraphStore` with an injected `FakeDatasetStore`; seed
6 narratives. Drive `build_dataset` over the bus:

- Response validates as `DatasetManifest`; `version == 1`; `example_count == 6`.
- Graph: exactly one `Dataset` node; six `TrainingExample` nodes;
  `Dataset -[:CONTAINS]-> TrainingExample` edges present; each `TrainingExample
  -[:DERIVED_FROM]-> TradeNarrative` edge present.
- `FakeDatasetStore.written` has one entry keyed by `dataset_id`.
- A **second** `build_dataset` for the same purpose → `version == 2` (versioning works).
- `build_dataset` on an empty corpus → degraded manifest (`example_count == 0`), no crash.
- `describe_corpus` → `Explanation` with a non-empty summary reflecting the corpus counts.

### D7. `agents/curator/tests/test_p10_boundary.py` — ≤ 70L  *(the P10 invariant)*

The boundary proof: **the curator never influences or mutates a trading decision.**

```python
def test_curator_build_dataset_mutates_no_decision_node() -> None:
    """build_dataset writes only curator nodes; every pre-existing node is unchanged."""
    # Seed a realistic decision graph (use surfaces.context.build_test_context and/or the
    # helper that seeds Recommendation/OrderIntent/Fill/Position/CloseDecision/TradeNarrative).
    # Snapshot BEFORE: for every label except Dataset/TrainingExample, capture
    # {(label, key): node.props} via list_nodes.
    before = _snapshot_non_curator_nodes(graph)

    # Run build_dataset.
    ctx.bus.request(build_dataset_message(purpose="exit-timing"))

    after = _snapshot_non_curator_nodes(graph)
    assert after == before          # no decision/source node added, removed, or mutated
    assert graph.list_nodes("Dataset")          # curator DID write its own nodes
    assert graph.list_nodes("TrainingExample")
```

`_snapshot_non_curator_nodes` iterates every label the test seeded **except** `Dataset` and
`TrainingExample` and records `(label, key) -> props`. Equality before/after proves the
curator is purely additive over its own labels and read-only over everyone else's. Append the
`DERIVED_FROM` edges only from `TrainingExample`, so source nodes are untouched.

### D8. `surfaces/tests/test_datasets_surface.py` — ≤ 60L

- `all_datasets` on empty graph → `()`.
- After one `Dataset` node → one `DatasetView` with the right counts.
- `cli datasets` empty → `"no datasets built"`; with a dataset → output contains the
  `dataset_id` and the `8/1/1`-style split counts.

## Steps

1. Branch `sprint-27-p10-curator-datasets` off `main`.
2. **Part A**: run the boundary meta-test; reconcile `depends_on` minimally; `make ci`.
3. **Part B**: settings → dataset_store → assembly → split → manifest → store → agent →
   bind. Run `make ci` after the agent + bind (or sooner — shortest loop wins).
4. **Part C**: datasets query → render (check headroom) → cli_commands_queries → cli.
5. **Part D**: all test files; `make ci` final — fully green.
6. **Line-count check:** `wc -l agents/curator/*.py agents/curator/domain/*.py
   surfaces/render.py surfaces/queries/datasets.py`. All < 200L; none should exceed the 150L
   warn band without reason.
7. Push; hand back.

## Acceptance criteria

- `curator.build_dataset` with ≥ `min_examples_for_split` seeded `TradeNarrative` nodes
  writes one `Dataset` node, one `TrainingExample` per example, `CONTAINS` + `DERIVED_FROM`
  edges, and one `FakeDatasetStore` payload; the response is a valid `DatasetManifest`.
- Re-running `build_dataset` for the same `purpose` yields `version == previous + 1`;
  a different purpose starts at `version == 1`.
- `split_examples` is deterministic and contiguous; ratios not summing to 1.0 raise
  `ValueError` (degraded, not crash, through the agent).
- `build_dataset` on an empty/too-small corpus returns a degraded manifest with no crash and
  no Flag.
- `describe_corpus` returns an `Explanation` with a non-empty, corpus-accurate summary.
- **`test_p10_boundary.py` green:** every non-curator node is identical before/after a
  `build_dataset`, while `Dataset` + `TrainingExample` nodes are created.
- `cli datasets` empty → "no datasets built"; populated → shows dataset_id + split counts.
- Import-linter 4/4 kept (curator imports only `kernel` + `contracts`; reads reporter data
  via the graph, never an import).
- `make ci` green at/above the coverage floor (100.00); raise the floor only if measured
  coverage climbs.

## Out of scope (do NOT build this sprint)

- **Training trigger + predictor registry** (advisory → load-bearing promotion gate, frozen
  evidence, promotion-audit) — that is **Sprint 28 (P10 exit)**.
- A real file/blob `DatasetStore` backend (FakeDatasetStore only this sprint; real store is
  build-when-needed).
- Timestamp/lookback filtering of the corpus (P10-begins takes all up to `max_examples`).
- Richer per-purpose example schemas (one generic `ExampleRecord` schema this sprint; the
  `schema_ref` string is the version hook for later schemas).
- MCP binding of curator tools (Sprint 22's MCP server has a fixed tool list; updating it is
  deferred).
- Any change to a trading-decision agent (the whole point is that the curator touches none).

## P10 status after this sprint (planning agent updates on review)

This sprint **begins** P10 and delivers the dataset half of the exit criterion
("a versioned dataset can be built from collected data and described to the operator with
full provenance"). P10 **exit** also needs the training trigger + predictor registry
(Sprint 28). After merge, mark P10 **active** (begun) — not complete.

## Handback report (paste into PR / reply)

- Which `depends_on` rule the boundary meta-test enforced, and the resulting contract state.
- The edge name used from Position → CloseDecision for the label (confirm it matches the
  reporter/monitor edge string; note where you read it).
- Whether `render.py` needed an A0-style extraction (final line counts of render.py /
  render_extras.py).
- Final line counts: agent.py, assembly.py, split.py, manifest.py, store.py.
- `test_p10_boundary.py` result — confirm the before/after node-snapshot equality held.
- New coverage % and floor; total test count.

The planning agent reviews, merges to `main`, marks P10 active (begun) in STATE +
build-plan, and plans **Sprint 28** (training trigger + predictor registry; P10 exit).
