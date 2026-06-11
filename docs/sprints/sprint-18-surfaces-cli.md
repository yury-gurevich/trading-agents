# Sprint 18 — Surfaces foundation + CLI (P6 begins)

**Status:** planned · **Branch:** `sprint-18-surfaces-cli` · **Build phase:** P6 (surfaces) · **Effort: M**

## Goal

Two deliverables: (1) fix the P5 deferred `resolve_flag` append-only violation before it reaches
production; (2) build the surfaces foundation — graph query projections and a minimal CLI that
lets an operator inspect pipeline runs, system health, and dispatch commands — proving the
surfaces layer is wired and the operator can interact end-to-end from the terminal.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/architecture.md` (surfaces layer: imports allowed,
  import direction, never-drive constraint); `.importlinter` (surfaces currently not in any
  contract — confirm after sprint that import-linter still passes); `agents/supervisor/store.py`
  (the `_replace_node` function to be replaced); `agents/supervisor/domain/gate.py` (calls
  `resolve_flag` — must be updated); `agents/supervisor/domain/health.py` (counts `Flag` nodes
  — must account for resolutions); `contracts/supervisor.py` (`owns_graph` needs `FlagResolution`
  added); `orchestration/bindings.py` (how to bind all agents for the CLI context);
  `kernel/graph.py` (the `GraphStore` protocol — traversal API, `get_node`, `ancestors`, etc.);
  `contracts/reporter.py` (`RunSnapshot`) + `contracts/supervisor.py` (`MasterReport`) — the
  main DTOs already available via bus.
- Surfaces sit above all other layers (agents, orchestration, contracts, kernel). They may
  import any of these. They must never be imported by agents or orchestration (the existing
  `forbidden` import-linter contract enforces the latter).
- The CLI is the first usable product surface. Its tests must be infra-free (graph + bus
  injected; `FakeDataSource` + `PaperBroker`; no Neo4j, no Celery, no Anthropic key needed).

## Part A — Fix `resolve_flag` (P6 obligation from P5)

The current `resolve_flag` implementation in `agents/supervisor/store.py` directly mutates
`InMemoryGraphStore._nodes`, bypassing the append-only `GraphStore` protocol. This raises
`RuntimeError` against the Neo4j backend.

### A1. Add `FlagResolution` label — `contracts/supervisor.py`

Add `"FlagResolution"` to `owns_graph`. No other contract changes.

### A2. Replace `_replace_node` with an append — `agents/supervisor/store.py`

```python
def resolve_flag(graph: GraphStore, subject_ref: str, severity: str) -> None:
    """Append a FlagResolution node linked to the existing Flag, if present."""
    flag_node = graph.get_node("Flag", _flag_key(subject_ref, severity))
    if flag_node is None:
        return
    key = f"resolution:{_flag_key(subject_ref, severity)}"
    if graph.get_node("FlagResolution", key) is not None:
        return  # idempotent — already resolved
    resolution = graph.merge_node(
        "FlagResolution", key,
        {"subject_ref": subject_ref, "severity": severity,
         "resolved_at": datetime.now(tz=UTC).isoformat()}
    )
    graph.add_edge(resolution, flag_node, "RESOLVES")
```

Delete `_replace_node` entirely.

### A3. Update `agents/supervisor/domain/health.py`

`compute_health` currently counts `Flag` nodes by status prop. Replace with: a `Flag` is open
if no `FlagResolution` node with key `f"resolution:{_flag_key(...)}"` exists for it. Since
`health.py` doesn't know the flag keys, the simplest approach: count all `FlagResolution` nodes
and subtract from total `Flag` count (or: iterate `Flag` nodes and check for a linked resolution
via `descendants(flag_node, {"RESOLVES"}, max_depth=1)`). Keep ≤ 80 lines.

### A4. Update `agents/supervisor/domain/gate.py`

`dispatch_intent` calls `resolve_flag(graph, subject_ref, severity)`. This call stays the same —
only the implementation in store.py changes. But the confirmation-pending check must also be
updated: currently it might read `flag.props["status"]` — change it to check for the absence of
a `FlagResolution` node instead. Extract a helper:

```python
def _flag_is_pending(graph: GraphStore, subject_ref: str, severity: str) -> bool:
    flag = graph.get_node("Flag", _flag_key(subject_ref, severity))
    if flag is None:
        return False
    resolution_key = f"resolution:{_flag_key(subject_ref, severity)}"
    return graph.get_node("FlagResolution", resolution_key) is None
```

Update `_needs_confirmation` to use `_flag_is_pending` if you want to short-circuit repeated
confirmation prompts (optional for P6; the current behaviour — always write a new flag if
`requires_confirmation=True` and no `confirmed=true` param — is still correct because
`write_flag` is idempotent). The key fix is that `resolve_flag` no longer mutates internals.

### A5. Update tests in `agents/supervisor/tests/`

All tests that previously asserted `flag.props["status"] == "resolved"` must now assert that
a `FlagResolution` node exists (or use `node_count(graph, "FlagResolution") == 1`). Make sure
the confirmation-gate tests still pass end-to-end.

## Part B — Surfaces foundation and CLI

### B1. `surfaces/queries/` — graph projection functions

Pure functions over `GraphStore` — no bus, no agents. Return typed dataclasses (not graph
`Node` objects). Keep each file ≤ 100 lines.

**`surfaces/queries/runs.py`**:

```python
@dataclass(frozen=True)
class StepRecord:
    name: str
    status: str  # "completed" | "attempted"

@dataclass(frozen=True)
class RunSummary:
    run_id: str
    steps: tuple[StepRecord, ...]
    completed: bool
    message_count: int
    snapshot_available: bool

def recent_runs(graph: GraphStore, limit: int = 10) -> tuple[RunSummary, ...]:
    """Return the most recent dispatcher runs from Message nodes, newest first."""
    # Group Message nodes by run_id; for each run_id, collect steps.
    # A run is completed if it has a "narrative" step record.
    # snapshot_available = get_node("Snapshot", f"snapshot:{run_id}") is not None
    ...
```

**`surfaces/queries/health.py`**:

```python
@dataclass(frozen=True)
class HealthSummary:
    healthy: bool
    open_faults: int
    pending_flags: int
    last_run_id: str | None

def system_health(graph: GraphStore) -> HealthSummary:
    """Project graph state into a health summary without calling the bus."""
    ...
```

**`surfaces/queries/positions.py`**:

```python
@dataclass(frozen=True)
class PositionView:
    position_id: str
    ticker: str
    quantity: int
    opened_price_cents: int
    status: str   # "open" | "closed"
    close_trigger: str | None

def open_positions(graph: GraphStore) -> tuple[PositionView, ...]:
    """Return all Position nodes that have no linked CloseDecision."""
    ...

def positions_for_run(graph: GraphStore, run_id: str) -> tuple[PositionView, ...]:
    """Return Position nodes opened by a specific PM run."""
    ...
```

### B2. `surfaces/context.py` — injectable context for CLI and tests

```python
@dataclass
class SurfaceContext:
    graph: GraphStore
    bus: MessageBus

def paper_context(source=None, broker=None) -> SurfaceContext:
    """Build a production-ready context with Neo4j + InProcessBus + all agents bound."""
    from orchestration.bindings import bind_paper_loop_agents
    ...

def test_context(graph=None, source=None, broker=None) -> SurfaceContext:
    """Build an infra-free context with InMemoryGraphStore + InProcessBus."""
    ...
```

The `test_context` helper is what CLI tests use. Both functions bind the full agent roster
(including `OperatorAgent` + `SupervisorAgent`) to the bus.

### B3. `surfaces/cli.py` — terminal interface

Minimal `argparse` CLI. Entry point: `python -m surfaces.cli <command> [args]`.

| Command | What it does |
| --- | --- |
| `status` | Calls `supervisor.system_status` via bus; renders `MasterReport` fields |
| `runs [--limit N]` | Calls `recent_runs(graph)`; renders run table (run_id, steps, completed) |
| `run <run_id>` | Shows steps and snapshot for one run; calls `reporter.report` if snapshot missing |
| `positions` | Calls `open_positions(graph)`; renders position table |
| `command "<text>"` | Calls `operator.interpret` then `supervisor.dispatch_intent`; renders outcome |

Output is plain text (no colour libraries, no rich/click — just `print`). Format: one value per
line with a fixed-width label, or a simple table with `str.ljust`. The CLI is a developer tool
at this stage; aesthetics are secondary to correctness.

**`surfaces/cli.py`** ≤ 150 lines. Extract rendering helpers to `surfaces/render.py` if needed.

**`surfaces/__init__.py`** — export `SurfaceContext`, `paper_context`, `test_context`.

**`surfaces/__main__.py`** — `if __name__ == "__main__": main()` entry point.

### B4. Tests — `surfaces/tests/`

**`test_queries.py`**:
- `recent_runs` on a graph with two completed run records → returns 2 `RunSummary` items,
  newest first; `completed=True`; `steps` contains all step names.
- `recent_runs` on empty graph → returns empty tuple, no crash.
- `open_positions` returns only `Position` nodes with no linked `CloseDecision`.
- `positions_for_run` returns only positions for the given PM run_id.
- `system_health` on graph with one `Fault` node → `open_faults=1`, `healthy=False`.

**`test_cli.py`** (use `test_context` + `capsys` or capture prints):
- `cli status` renders a line containing `"healthy"`.
- `cli runs` renders the run_id of a run that was seeded in the test graph.
- `cli positions` renders "no open positions" when graph is empty.
- `cli command "run the daily scan"` → renders `routed_to: orchestration.execute_run` (using
  `FakeLLMClient` with a `run` keyword response).

**Coverage floor** — ratchet from 100.00; surfaces is new, must be fully covered.

## Steps

1. Branch `sprint-18-surfaces-cli` off `main`.
2. **Fix first**: `contracts/supervisor.py` → `agents/supervisor/store.py` → `health.py` →
   `gate.py` → supervisor tests. Run `make ci` before touching surfaces.
3. `surfaces/queries/runs.py`; `surfaces/queries/health.py`; `surfaces/queries/positions.py`.
4. `surfaces/context.py`; `surfaces/cli.py`; `surfaces/__init__.py`; `surfaces/__main__.py`.
5. Query tests, then CLI tests.
6. Run the gate. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- `_replace_node` is gone from `supervisor/store.py`; `resolve_flag` appends a `FlagResolution`
  node; no direct access to `._nodes`; `FlagResolution` added to `contracts/supervisor.py`
  `owns_graph`; all Sprint 17 confirmation-gate tests still pass.
- `recent_runs`, `open_positions`, `positions_for_run`, `system_health` return typed dataclasses
  from graph state; no crashes on empty graph.
- `cli status` / `cli runs` / `cli positions` / `cli command` all produce non-empty output;
  `cli command` reaches the supervisor's `dispatch_intent` and renders `routed_to`.
- `surfaces/cli.py` ≤ 150 lines; all modules headered, < 200 lines.
- Import-linter 4/4 kept (surfaces imports agents/contracts/kernel; agents do NOT import surfaces).
- `make ci` green at/above coverage floor.

## Out of scope (do NOT build this sprint)

Web dashboard (later P6 sprint); approval queue UI (later P6 sprint); scorecards and calibration
surfaces (P7/P9); position P&L arithmetic (P6 later — needs sell-price fills from execution
close path); `rich` or `textual` for terminal formatting (defer until the CLI is validated).
Flag anything that feels needed earlier.

## Handback report (paste into the PR / reply)

- Files changed, line counts; confirm `_replace_node` is gone and `FlagResolution` exists.
- How `recent_runs` groups `Message` nodes by run_id (iteration approach, any edge cases).
- How `open_positions` determines open vs closed (presence of `CloseDecision` node, or edge).
- Whether `cli command` required any agent binding changes in `test_context`.
- New coverage % and floor; any design note for the next P6 sprint.

The planning agent will review, merge to `main`, update docs, and plan Sprint 19 (position
lifecycle + trade narrative display + approval queue stub).
