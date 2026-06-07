# Sprint 03 — Neo4j GraphStore: retire the relational adapter, stand up the graph spine

**Status:** shipped (merged to `main` @ `ba2f42c`) · **Branch:** `sprint-03-neo4j-store` · **Build phase:** P1 (storage pivot)

## Goal

Replace the relational persistence adapter with a **Neo4j-backed `GraphStore` behind a
kernel protocol**, implementing `docs/decisions/0001-neo4j-primary-store.md`. Mirror the
bus's two-backend shape: an **in-memory backend** keeps the unit gate deterministic and
infra-free; a **Neo4j backend** is exercised under an `integration` marker. Reconcile the
boundary map to **single-writer-per-label**. No relational store, no Alembic, no migration
job remains.

## Why (context)

- ADR-0001 settled the store: one schema-flexible Neo4j graph for transactional records,
  provenance, and RAG. This **supersedes Sprint 02's relational adapter**.
- The runtime spine already follows a protocol + swappable-backend pattern — the bus is a
  `MessageBus` Protocol with `InProcessBus` for tests. The graph store mirrors it exactly:
  a `GraphStore` Protocol with an in-memory backend for tests and `Neo4jGraphStore` for
  runtime.
- Read first: `docs/sprints/README.md` (the non-negotiable guardrails + the exact
  quality-gate commands); `docs/decisions/0001-neo4j-primary-store.md`; `kernel/bus.py` (the
  Protocol + backend pattern to copy, incl. `fault_boundary` usage); `kernel/persistence.py`
  (what you are deleting); `kernel/config.py` (`AgentSettings` + `tunable`); `kernel/contract.py`
  (`owns_tables` / `owns_graph`); `tests/test_boundary_map.py`; `tests/test_persistence.py`
  (retire); `.env.example` (the `NEO4J_*` block).

## Key design constraints (do not break)

- **Mirror the bus.** A `GraphStore` Protocol + two backends: `InMemoryGraphStore` (the
  graph analogue of `InProcessBus` — dict-backed, deterministic, the default test backend)
  and `Neo4jGraphStore` (the real driver). Kernel and agents talk to the **protocol**, never
  the `neo4j` driver directly.
- **Kernel stays domain-pure.** The store provides generic node/edge mechanics; it defines
  **no domain labels** and contains no trading logic. Labels/keys are passed in by callers
  (agents, from their contracts' `owns_graph`). `import-linter` "Kernel is pure plumbing"
  must stay KEPT.
- **Append-only by construction.** Expose `merge_node` / `add_edge` / read / traversal —
  and **no destructive operation** (no node delete, no property overwrite that drops
  history). Every node carries a `schema_version`. This is the audit guarantee from ADR-0001
  (money is integer minor units; append-only by convention + `schema_version` + uniqueness).
- **Faults, not silent failure.** Every store operation runs inside
  `fault_boundary(sink, agent="kernel", module="kernel.graph", reraise=True)`.
- **No relational store, no Alembic, no migration job.**
- **Small files.** < 200 lines each (split the backends across modules if needed — e.g.
  `kernel/graph.py` for types + Protocol + `InMemoryGraphStore`, `kernel/graph_neo4j.py` for
  `Neo4jGraphStore` + `GraphSettings`). Coding-agent headers; justified tunables; no magic numbers.

## Deliverables

1. **`kernel/graph.py`** — types + protocol + in-memory backend:
   - `Node` (label, key, props, `schema_version`) and `Edge` (parent key, child key,
     edge_type, props) — frozen/typed value objects.
   - `GraphStore` (Protocol): `merge_node(label, key, props, *, schema_version=1) -> Node`
     (idempotent upsert by `(label, key)`); `add_edge(parent, child, edge_type, props=None)
     -> None`; `get_node(label, key) -> Node | None`; `ancestors(node, *, max_depth,
     edge_types=None) -> Iterator[Node]`; `descendants(...)`. Keep the surface minimal but
     useful for provenance walks. No delete.
   - `InMemoryGraphStore(GraphStore)`: dict-backed, deterministic; default test backend.
     Constructor takes an optional `FaultSink` (default `CollectingFaultSink`), like
     `InProcessBus`.

2. **`kernel/graph_neo4j.py`** — `Neo4jGraphStore(GraphStore)` + `GraphSettings`:
   - `GraphSettings(AgentSettings)` reading `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD`
     (no env_prefix — infrastructure config, same pattern the retired `PersistenceSettings`
     used). Any pool/timeout knob via `tunable(..., why=...)`.
   - `Neo4jGraphStore`: wraps `neo4j.GraphDatabase`; `MERGE` for nodes (idempotent on
     `(label, key)`), `CREATE`/`MERGE` for edges (endpoints must already exist), variable-length
     `MATCH` for `ancestors`/`descendants`. Operations inside `fault_boundary`. Keep it thin;
     use `# pragma: no cover` (with a one-line reason) only on lines that genuinely require a
     live DB and cannot be covered by the integration test.

3. **`kernel/__init__.py`** — remove `Base`, `Database`, `PersistenceSettings` (and any
   persistence mention in the module docstring); export `GraphStore`, `InMemoryGraphStore`,
   `Neo4jGraphStore`, `GraphSettings`, `Node`, `Edge`.

4. **Retire the relational layer** — delete `kernel/persistence.py`, `alembic/`,
   `alembic.ini`, and `tests/test_persistence.py` (replaced by `tests/test_graph.py`).

5. **Dependencies & CI config:**
   - `pyproject.toml`: remove `sqlalchemy` + `alembic` from **both** the `runtime` extra
     (≈ lines 17–18) **and** the `dev` group (≈ lines 33–34); add `neo4j>=5.20` to the
     `dev` group so `uv sync` installs it for the gate (it stays in the `runtime` extra
     too); drop `alembic` / `alembic.*` from `[[tool.mypy.overrides]]` (keep `neo4j`).
     `celery`/`redis` stay in the `runtime` extra for the later distributed bus.
   - `.github/workflows/ci.yml`: the `migration` job is only a **dormant comment** —
     remove/reword it; there is no active job to delete. No other CI change is needed (the
     `test` job already runs `integration` tests, and the Neo4j integration test skips
     without `NEO4J_TEST_URI`, so CI stays green). Wiring a real Neo4j service into the
     `test` job to actually exercise the integration test is an optional later follow-up.

6. **`.env.example`** — remove the `DATABASE_URL` block; document `NEO4J_URI` /
   `NEO4J_USER` / `NEO4J_PASSWORD` (already stubbed) plus `NEO4J_TEST_URI` for the
   integration test.

7. **Boundary map → single-writer-per-label:**
   - Remove `owns_tables` from `AgentContract` (`kernel/contract.py`) and from all **12**
     contracts.
   - `tests/test_boundary_map.py`: delete `test_each_table_has_one_writer`; change
     `test_every_agent_states_its_boundaries` to assert `c.owns_graph` (drop the
     `owns_tables` alternative).
   - **Do not** re-model the dropped tables into new labels in this sprint — each agent's
     `owns_graph` already declares its core labels; more are added as agents are built (P2+).

8. **`tests/test_graph.py`:**
   - `InMemoryGraphStore` unit tests (the gate): `merge_node` is idempotent on
     `(label, key)`; `add_edge` between existing nodes; `ancestors`/`descendants` return the
     right chain at depth; a forced failure records exactly one fault
     (`source_module == "kernel.graph"`) and re-raises; there is no destructive operation on
     the protocol (append-only).
   - `Neo4jGraphStore` integration test, `@pytest.mark.integration`: read `NEO4J_TEST_URI`
     (+ creds), **skip if unset** so the default gate stays green and infra-free; round-trip
     a node + edge + a traversal against real Neo4j; clean up after.

## Steps

1. Branch `sprint-03-neo4j-store` off `main`.
2. Write `kernel/graph.py` + `kernel/graph_neo4j.py`; update `kernel/__init__.py` exports.
3. Delete the relational layer (deliverable 4) and swap deps + `.env.example`.
4. Apply the contract + boundary-test changes (deliverable 7).
5. Write `tests/test_graph.py`.
6. Run the gate (the integration test skips without `NEO4J_TEST_URI`, so the default run
   stays green and infra-free). Re-measure coverage and set the floor in `pyproject.toml`
   (`--cov-fail-under` + `[tool.coverage.report] fail_under`) to the new real value — never
   below the meaningful floor.
7. Push the branch and hand back the report. Do not merge to `main`.

## Acceptance criteria

- `GraphStore` Protocol + `InMemoryGraphStore` + `Neo4jGraphStore` exist, each module
  headered and < 200 lines.
- `import-linter` reports "Kernel is pure plumbing" **KEPT**; the graph modules import
  nothing from `contracts`/`agents`.
- No relational store, Alembic, or `migration` job remain; `pyproject.toml` has no
  `sqlalchemy`/`alembic`.
- The boundary meta-test passes with the per-label-only invariant; `owns_tables` is gone
  from the contract and all 12 contracts.
- The unit gate is green with **no external infrastructure** (in-memory backend); the Neo4j
  integration test passes when `NEO4J_TEST_URI` is set and **skips cleanly** otherwise.
- `make ci` (or the individual `uv run` gate commands) green; coverage at or above the
  retuned floor.
- No agent/domain logic added; the kernel stays pure.

## Out of scope (do NOT build this sprint)

The **RAG vector index + `vector_search`** (its own fast-follow — keep this sprint to
nodes/edges/traversal); provenance mirror-write helpers in agents (P2); the distributed
(Celery) bus; the observability/metrics adapter; any real agent. Flag if you think the
vector/RAG slice is needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed/deleted and final line counts.
- New total coverage % and the floor you set.
- The `GraphStore` protocol surface + the backend-split decision; how append-only is
  enforced; whether `neo4j` moved to `dev` or stayed in the `runtime` extra; the
  integration-test skip behaviour.
- Anything that felt out of scope or worth recording.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`.
