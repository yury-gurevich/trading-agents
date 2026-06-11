<!-- Agent: planning | Role: sprint handover -->
# Sprint 19 — GraphStore `list_nodes` + position lifecycle (P6 continues)

**Status:** shipped · **Branch:** `sprint-19-list-nodes-lifecycle` · **Build phase:** P6 (surfaces) · **Effort: M**

## Goal

Two deliverables: (1) close the Neo4j compatibility gap in the surfaces layer by adding
`list_nodes(label)` to the `GraphStore` protocol and both backends, then removing every
`._nodes` internal access across the codebase; (2) extend the CLI and surfaces layer
with position lifecycle detail (entry → exit chain with trade narrative) and a pending-flags
view (approval queue stub).

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/architecture.md` (layer order, import rules);
  `kernel/graph.py` (`GraphStore` Protocol + `InMemoryGraphStore` — note that `_nodes` is a
  flat `dict[str, Node]` keyed by `f"{label}:{key}"` or similar; read the actual structure);
  `kernel/graph_neo4j.py` (`Neo4jGraphStore` — read the label-quoting pattern already present
  in other Cypher methods; replicate it for `list_nodes`);
  `surfaces/queries/_graph.py` (the `nodes_by_label` helper — currently accesses `._nodes`);
  `agents/supervisor/domain/health.py` (has its own private `_nodes(graph, label)` helper
  that also accesses `._nodes` — this is in `agents/`, cannot import from `surfaces/`);
  `surfaces/cli.py` (**already at 150L, the hard cap**; before adding any commands, extract
  per-command dispatch logic into `surfaces/cli_commands.py` to free up headroom);
  `surfaces/render.py` (100L rendering helpers; extend for new output formats);
  `orchestration/lineage.py` (canonical traversal example — confirms edge directions and
  `ancestors`/`descendants` convention).

- **Edge direction convention** (confirm by reading `lineage.py` and tests before coding):
  `ancestors(node, edge_types)` follows **incoming** edges — returns nodes that have an edge
  of the given type **pointing to** `node`. `descendants(node, edge_types)` follows **outgoing**
  edges — returns nodes that `node` points to. Confirmed edges:
  `OrderIntent -[:EMITTED_BY]-> PMRun`,
  `Fill -[:EXECUTES]-> OrderIntent`,
  `Fill -[:OPENS]-> Position`,
  `CloseDecision -[:CLOSES]-> Position`,
  `TradeNarrative -[:NARRATES]-> Position`,
  `OrderIntent -[:APPROVES]-> Recommendation`.

- Part A is a prerequisite for Neo4j production use of all surface queries. It is a pure
  protocol/backend change — no new behaviour, no new graph nodes. All existing tests must
  still pass after Part A.

- `agents/supervisor/domain/health.py` is in the `agents/` layer. It may not import from
  `surfaces/`. After Part A, replace its private `_nodes` helper with direct calls to
  `graph.list_nodes(label)` (the protocol method is now available on `GraphStore` directly).

## Part A — `list_nodes` protocol method

### A1. `kernel/graph.py` — add to `GraphStore` Protocol and `InMemoryGraphStore`

Add to the `GraphStore` Protocol:

```python
def list_nodes(self, label: str) -> tuple[Node, ...]:
    """Return all nodes with the given label."""
    ...
```

Implement in `InMemoryGraphStore`:

```python
def list_nodes(self, label: str) -> tuple[Node, ...]:
    return tuple(n for n in self._nodes.values() if n.label == label)
```

(Read the actual `_nodes` structure first — adjust if it is a dict-of-dicts. The iteration
pattern must match however `_nodes` is organised.)

### A2. `kernel/graph_neo4j.py` — implement in `Neo4jGraphStore`

Use the same backtick label-quoting pattern already present in the module:

```python
def list_nodes(self, label: str) -> tuple[Node, ...]:
    label_q = label.replace("`", "``")
    result = self._session.run(f"MATCH (n:`{label_q}`) RETURN n")
    return tuple(self._to_node(record["n"]) for record in result)
```

(`_to_node` or equivalent — use whatever helper the module already has for mapping
Neo4j records to `Node` objects.)

### A3. `surfaces/queries/_graph.py` — remove `._nodes` access

Replace the body of `nodes_by_label`:

```python
def nodes_by_label(graph: GraphStore, label: str) -> tuple[Node, ...]:
    return graph.list_nodes(label)
```

The function signature and all call sites are unchanged.

### A4. `agents/supervisor/domain/health.py` — remove private `_nodes` helper

Delete the `_nodes(graph, label)` private helper. Replace every call site
`_nodes(graph, "Fault")` / `_nodes(graph, "Flag")` / `_nodes(graph, "FlagResolution")` /
`_nodes(graph, "Snapshot")` with `graph.list_nodes("Fault")` etc. directly.
Keep ≤ 80 lines.

### A5. Tests for `list_nodes`

Add to an existing `tests/kernel/` file (or a new `tests/kernel/test_list_nodes.py`):

- `InMemoryGraphStore.list_nodes("X")` on an empty store → empty tuple, no crash.
- After writing one `Foo` node and one `Bar` node, `list_nodes("Foo")` returns the
  `Foo` node only; `list_nodes("Bar")` returns the `Bar` node only.
- A fake `GraphStore` that has **no `_nodes` attribute** but implements `list_nodes`
  correctly can be passed to `nodes_by_label(graph, "X")` without crashing — proves the
  helper no longer touches internals.
- Neo4j live test (skip unless `NEO4J_TEST_URI` is set): write a node, `list_nodes`
  returns it.

**Run `make ci` after Part A before touching Part B.**

## Part B — Position lifecycle detail + pending-flags view

### B0. Prerequisite: free up `cli.py` headroom

`cli.py` is at **150L (hard cap)**. Before adding any commands, extract the per-command
handler bodies from `_dispatch()` into a new `surfaces/cli_commands.py`:

```python
# surfaces/cli_commands.py
"""CLI command handler implementations.

Agent: surfaces
Role: implement each CLI sub-command; called from cli._dispatch.
External I/O: MessageBus calls (operator, supervisor, reporter); GraphStore reads.
"""

def cmd_status(args, ctx, out): ...
def cmd_runs(args, ctx, out): ...
def cmd_run(args, ctx, out): ...
def cmd_positions(args, ctx, out): ...
def cmd_command(args, ctx, out): ...
```

Leave `cli.py` as thin argument-parsing glue that calls into `cli_commands`. Both files
must stay < 200L; aim for `cli.py` ≤ 80L after extraction, `cli_commands.py` ≤ 150L.

### B1. `surfaces/queries/lifecycle.py` — position lifecycle query

New file, ≤ 100L:

```python
@dataclass(frozen=True)
class PositionLifecycle:
    position_id: str
    ticker: str
    quantity: int
    opened_price_cents: int
    status: str               # "open" | "closed"
    close_trigger: str | None
    run_id: str | None
    recommendation_confidence: float | None
    narrative_text: str | None

def position_lifecycle(
    graph: GraphStore, position_id: str
) -> PositionLifecycle | None:
    """Traverse the full entry-to-exit chain for one position. None if not found."""
    ...
```

**Traversal from `position` node (verify directions against `orchestration/lineage.py`):**

| Step | Call | Gets |
| ---- | ---- | ---- |
| opening fill | `ancestors(position, {"OPENS"}, max_depth=1)` | Fill |
| order intent | `descendants(fill, {"EXECUTES"}, max_depth=1)` | OrderIntent |
| pm run id | `descendants(order, {"EMITTED_BY"}, max_depth=1)` | PMRun (read `.key`) |
| recommendation | `descendants(order, {"APPROVES"}, max_depth=1)` | Recommendation |
| close decision | `ancestors(position, {"CLOSES"}, max_depth=1)` | CloseDecision or empty |
| narrative | `ancestors(position, {"NARRATES"}, max_depth=1)` | TradeNarrative or empty |

Take only the first element from each result (positions have one opening fill, one order,
etc.). Return `None` for any step that has no result rather than crashing.

Also add:

```python
def all_position_lifecycles(graph: GraphStore) -> tuple[PositionLifecycle, ...]:
    """Return lifecycle for all Position nodes in the graph."""
    return tuple(
        lc
        for pos in nodes_by_label(graph, "Position")
        if (lc := position_lifecycle(graph, pos.key)) is not None
    )
```

### B2. `surfaces/queries/flags.py` — pending-flags query

New file, ≤ 50L:

```python
@dataclass(frozen=True)
class FlagView:
    subject_ref: str
    severity: str
    created_at: str

def pending_flags(graph: GraphStore) -> tuple[FlagView, ...]:
    """Return Flag nodes that have no linked FlagResolution."""
    flags = nodes_by_label(graph, "Flag")
    resolutions = nodes_by_label(graph, "FlagResolution")
    resolved = {
        (str(r.props.get("subject_ref")), str(r.props.get("severity")))
        for r in resolutions
    }
    return tuple(
        FlagView(
            subject_ref=str(n.props.get("subject_ref", "")),
            severity=str(n.props.get("severity", "")),
            created_at=str(n.props.get("created_at", "")),
        )
        for n in flags
        if (str(n.props.get("subject_ref")), str(n.props.get("severity")))
        not in resolved
    )
```

### B3. `surfaces/cli_commands.py` additions (after B0 extraction)

Add two new command handlers to the extracted module:

**`cmd_lifecycle(args, ctx, out)`** — for `cli position <pos_id>`:

- Call `position_lifecycle(ctx.graph, args.pos_id)`; if `None`, print `"position not found: {pos_id}"`.
- Render with a new `render.render_lifecycle` helper.

**`cmd_flags(args, ctx, out)`** — for `cli flags`:

- Call `pending_flags(ctx.graph)`.
- If empty, print `"no pending flags"`.
- Render each flag: `subject_ref`, `severity`, `created_at`.
- Append a hint line: `Hint: cli command "approve <subject>" to resolve.`

Update `cli.py` / `_parser()` with two new subparsers:

```text
position <pos_id>   Show full lifecycle for one position (entry → exit → narrative)
flags               List pending human-review flags (approval queue stub)
```

### B4. `surfaces/render.py` additions

Add `render_lifecycle(lifecycle: PositionLifecycle, out)` and `render_flags(flags, out)`
helpers. `render.py` is at 100L; it may grow up to 150L (warn band) — aim to stay ≤ 130L.
Split into `render_positions.py` / `render_system.py` only if the file exceeds 150L.

### B5. Export updates

`surfaces/queries/__init__.py` — add `PositionLifecycle`, `position_lifecycle`,
`all_position_lifecycles`, `FlagView`, `pending_flags`.

`surfaces/__init__.py` — no change needed (context factories stay the same).

### B6. Tests — `surfaces/tests/`

**`test_queries.py`** additions:

- `position_lifecycle` on a graph with a full chain (Position ← Fill ← OrderIntent,
  CloseDecision, TradeNarrative all present) → returns `PositionLifecycle` with all
  non-None fields; `status == "closed"`.
- `position_lifecycle` on a graph with only an open position (no CloseDecision, no
  narrative) → returns `PositionLifecycle` with `close_trigger=None`, `narrative_text=None`,
  `status == "open"`.
- `position_lifecycle(graph, "missing")` → `None`, no crash.
- `all_position_lifecycles` on a graph with two positions → returns 2 results.
- `pending_flags` with one Flag and one FlagResolution (same subject/severity) → empty.
- `pending_flags` with two Flags and one resolution → one pending flag returned.

**`test_cli.py`** additions:

- `cli position <valid_id>` renders the ticker name from a seeded lifecycle.
- `cli position <missing_id>` renders `"position not found"`.
- `cli flags` with a seeded pending flag renders the subject_ref.
- `cli flags` on empty graph renders `"no pending flags"`.

**Coverage floor** — ratchet from 100.00; all new code must be covered.

## Steps

1. Branch `sprint-19-list-nodes-lifecycle` off `main`.
2. **Part A first:** `kernel/graph.py` → `kernel/graph_neo4j.py` → `surfaces/queries/_graph.py`
   → `agents/supervisor/domain/health.py` → add `list_nodes` tests. Run `make ci`. Do not
   proceed to Part B until the gate is green.
3. **Part B — B0 first:** extract `cli_commands.py` from `cli.py`. Run `make ci` to confirm
   the extraction is a no-op (same behaviour, just reorganised).
4. `surfaces/queries/lifecycle.py`; `surfaces/queries/flags.py`.
5. Add `cmd_lifecycle` + `cmd_flags` to `cli_commands.py`; add subparsers to `cli.py`.
6. Rendering helpers in `render.py`.
7. Export updates.
8. Query tests, then CLI tests.
9. Run the gate. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- `GraphStore` Protocol has `list_nodes(label: str) → tuple[Node, ...]`; both
  `InMemoryGraphStore` and `Neo4jGraphStore` implement it.
- No `getattr(graph, "_nodes"` or `._nodes` access anywhere in the codebase
  (confirm with `grep -r "_nodes" kernel contracts agents orchestration surfaces`).
- All existing Sprint 17 + Sprint 18 tests still pass unchanged.
- `position_lifecycle` returns a fully populated `PositionLifecycle` for a position
  with a complete chain; `None` for a missing position; partial fields for incomplete chains.
- `pending_flags` returns only unresolved flags; empty tuple if none.
- `cli position <pos_id>` and `cli flags` produce non-empty output.
- `cli.py` ≤ 150L; `cli_commands.py` < 200L; all other modules < 200L.
- Import-linter 4/4 kept.
- `make ci` green at/above coverage floor (100.00).

## Out of scope (do NOT build this sprint)

P&L arithmetic on positions (needs sell-price fills from execution close path — deferred);
approval queue resolution via CLI (already works through `cli command "approve ..."`; no
extra surface needed); scorecards and calibration surfaces (P7/P9); rich/textual formatting
(defer until CLI is validated); MCP tool-binding (separate sprint). Flag anything that feels
needed earlier.

## Handback report (paste into PR / reply)

- Confirm `grep -r "_nodes"` returns zero results outside of `InMemoryGraphStore`'s own impl.
- How `position_lifecycle` handles a position with no opening fill (e.g., an orphaned node).
- Whether `render.py` stayed under 150L or required a split.
- Whether `cli.py` headroom was recovered cleanly after B0 extraction.
- New coverage % and floor; any design note for the next P6 sprint.

The planning agent will review, merge to `main`, update docs, and plan Sprint 20
(trade narrative detail, scorecard stub, or MCP tool-binding — TBD based on Sprint 19 outcome).
