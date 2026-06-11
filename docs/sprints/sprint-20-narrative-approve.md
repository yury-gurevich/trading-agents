<!-- Agent: planning | Role: sprint handover -->
# Sprint 20 — Trade narrative display + approve command (P6 continues)

**Status:** shipped · **Branch:** `sprint-20-narrative-approve` · **Build phase:** P6 (surfaces) · **Effort: M**

## Goal

Two deliverables: (1) add a `cli narrative <run_id>` command that renders the per-trade story
for every position from a completed run; (2) wire the `approve` intent family end-to-end —
flip it to available in the capability matrix, resolve the matching human-review flag inline
in the gate, and add a `cli approve <subject>` command.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/architecture.md`;
  `agents/reporter/store.py` (`write_trade_narrative` — node key is `f"narrative:{position_id}"`;
  props are `run_id`, `position_id`, `summary`; edge is `TradeNarrative -[:NARRATES]-> Position`);
  `surfaces/queries/lifecycle.py` (`PositionLifecycle.narrative_text` + `_linked` helper already
  reads `summary` prop — confirms the prop name);
  `agents/supervisor/domain/gate.py` (**read carefully** — gate already writes/resolves
  confirmation flags inline; approve resolution follows the same pattern);
  `agents/supervisor/domain/matrix.py` (`approve` is currently `RouteSpec(None, None, False)` +
  listed in `BUILD_PHASES` — both must change);
  `agents/supervisor/store.py` (has `resolve_flag` + `_flag_key` + `_resolution_key` — add
  `resolve_flag_by_subject` here);
  `surfaces/cli_commands.py` (**currently 142L** — warning at 150, hard cap at 200; see
  extraction note below);
  `surfaces/render.py` (**currently 134L** — same warning applies);
  `agents/supervisor/tests/test_supervisor_gate.py` (has a test asserting `approve` returns
  `accepted=False`/not-available — must update it).

- **No new bus capability needed for approve.** `gate.dispatch_intent` IS the execution path
  — it makes direct graph writes (confirmation flags, Message nodes) without going through the
  bus. Approve resolution follows the same pattern: inline graph write before returning
  `DispatchResult`. `agent._dispatch_intent` just calls gate and returns the result unchanged;
  no routing loop is needed.

- **Line-count budget** — additions in this sprint will push `cli_commands.py` past 150L and
  `render.py` past 150L (both will be in the 150–200 warning band). Stay under 200L hard cap.
  If either file would exceed 175L after the full sprint, extract the new additions to
  `surfaces/cli_extras.py` and `surfaces/render_extras.py` respectively, imported back in the
  originals. Do not split until you know the real line counts.

## Part A — Trade narrative query + CLI

### A1. `surfaces/queries/lifecycle.py` — add `RunNarrative` + `narratives_for_run`

Append to the existing file (currently 97L; target ≤ 125L after addition):

```python
@dataclass(frozen=True)
class RunNarrative:
    position_id: str
    ticker: str
    summary: str

def narratives_for_run(graph: GraphStore, run_id: str) -> tuple[RunNarrative, ...]:
    """Return all trade narratives for a completed dispatcher run, sorted by position_id."""
    results: list[RunNarrative] = []
    for node in graph.list_nodes("TradeNarrative"):
        if str(node.props.get("run_id", "")) != run_id:
            continue
        position_id = str(node.props.get("position_id", ""))
        position = graph.get_node("Position", position_id)
        ticker = str(position.props.get("ticker", "")) if position is not None else ""
        results.append(RunNarrative(
            position_id=position_id,
            ticker=ticker,
            summary=str(node.props.get("summary", "")),
        ))
    return tuple(sorted(results, key=lambda r: r.position_id))
```

### A2. `surfaces/queries/__init__.py` — export new symbols

Add `RunNarrative` and `narratives_for_run` to the module exports.

### A3. `surfaces/render.py` — add `render_narratives`

Add a rendering helper (keep render.py ≤ 175L; extract if needed):

```python
def render_narratives(narratives: tuple[RunNarrative, ...], run_id: str, out) -> None:
    if not narratives:
        print(f"no narratives for run {run_id}", file=out)
        return
    print(f"Trade narratives — {run_id} ({len(narratives)} position(s))", file=out)
    for n in narratives:
        print(f"\n  {n.ticker}  [{n.position_id}]", file=out)
        for line in n.summary.splitlines():
            print(f"    {line}", file=out)
```

### A4. `surfaces/cli_commands.py` — add `cmd_narrative`

Add a new handler (keep cli_commands.py ≤ 175L; extract if needed):

```python
def cmd_narrative(args: argparse.Namespace, ctx: SurfaceContext, out) -> None:
    run_id = str(args.run_id)
    narratives = narratives_for_run(ctx.graph, run_id)
    render_narratives(narratives, run_id, out)
```

Update `cli.py` `_parser()`: add `narrative` subparser with `run_id` positional argument.
Update `cli.py` `_dispatch()`: call `cmd_narrative(args, ctx, out)`.

### A5. Tests

**`surfaces/tests/test_lifecycle_flags.py`** — extend:

- `narratives_for_run` on a graph with two `TradeNarrative` nodes for the same `run_id` →
  returns 2 `RunNarrative` items sorted by `position_id`; ticker is populated from the
  linked `Position` node.
- `narratives_for_run` on a graph with no `TradeNarrative` nodes → empty tuple, no crash.
- `narratives_for_run` with a different `run_id` filter → returns only matching narratives.

**`surfaces/tests/test_cli.py`** — extend:

- `cli narrative <run_id>` on a graph with a seeded `TradeNarrative` → output contains
  the ticker name and the summary text.
- `cli narrative <missing_run_id>` → output contains `"no narratives for run"`.

## Part B — Approve command

### B1. `agents/supervisor/domain/matrix.py` — enable approve

Change the `approve` entry:

```python
# before
"approve": RouteSpec(None, None, False),

# after
"approve": RouteSpec("supervisor", "resolve_flag", True),
```

Remove `"approve"` from `BUILD_PHASES` (it now ships in P6).

### B2. `agents/supervisor/store.py` — add `resolve_flag_by_subject`

```python
def resolve_flag_by_subject(graph: GraphStore, subject_ref: str) -> bool:
    """Find and resolve the first unresolved Flag matching subject_ref. Returns True if resolved."""
    for flag in graph.list_nodes("Flag"):
        if flag.props.get("subject_ref") != subject_ref:
            continue
        severity = str(flag.props.get("severity", "critical"))
        resolution_key = f"resolution:{_flag_key(subject_ref, severity)}"
        if graph.get_node("FlagResolution", resolution_key) is None:
            resolve_flag(graph, subject_ref, severity)
            return True
    return False
```

(`_flag_key` is already defined in store.py — use it directly.)

### B3. `agents/supervisor/domain/gate.py` — inline approve resolution

In `dispatch_intent`, after the capability availability check and before writing the Message
node, add approve resolution:

```python
# after: if not spec.available: return rejected(...)
# before: node = write_message(...)

if intent.family == "approve":
    store.resolve_flag_by_subject(graph, intent.subject or "")
```

Import `resolve_flag_by_subject` from `agents.supervisor.store` (already imports `store`
members). Gate.py is currently 58L — this stays well under 80L.

**Note on confirmation handling**: `approve` requires confirmation per `grammar.py`. When
`cli approve` sends `confirmed=true` on the first call, the gate's existing
`if intent.parameters.get("confirmed") == "true": resolve_flag(...)` path runs first —
this is safe even if no confirmation flag exists (the call is idempotent). Then approve
resolution runs. No change to the confirmation logic needed.

### B4. `surfaces/cli_commands.py` — add `cmd_approve`

```python
def cmd_approve(args: argparse.Namespace, ctx: SurfaceContext, out) -> None:
    """Approve a pending human-review flag. Auto-confirms (cli approve is the confirmation)."""
    subject = str(args.subject)
    # Interpret the approve command text.
    command_result = _operator_interpret(ctx, f"approve {subject}")
    if command_result is None or command_result.intent is None:
        print(f"could not interpret approve command for: {subject}", file=out)
        return
    # Inject confirmed=true — the user typing cli approve IS the confirmation.
    intent = command_result.intent.model_copy(
        update={"parameters": {**command_result.intent.parameters, "confirmed": "true"}}
    )
    dispatch_result = _supervisor_dispatch(ctx, intent)
    render_approve(dispatch_result, subject, out)
```

Where `_operator_interpret` and `_supervisor_dispatch` are existing helpers in
`cli_commands.py` (or inline them if no such helpers exist — follow the pattern of
`cmd_command`). The key step is injecting `confirmed: "true"` before dispatching.

Update `cli.py` `_parser()`: add `approve` subparser with `subject` positional argument
(the flag subject_ref to approve).
Update `cli.py` `_dispatch()`: call `cmd_approve(args, ctx, out)`.

### B5. `surfaces/render.py` — add `render_approve`

```python
def render_approve(result: DispatchResult, subject: str, out) -> None:
    if result.accepted:
        print(f"approved: {subject}", file=out)
        if result.routed_to:
            print(f"  routed_to: {result.routed_to}", file=out)
    else:
        print(f"approve refused: {subject}", file=out)
        if result.reason:
            print(f"  reason: {result.reason}", file=out)
```

(`DispatchResult` has `accepted`, `routed_to`, and `reason` — verify field names in
`contracts/supervisor.py`.)

### B6. Tests

**`agents/supervisor/tests/test_supervisor_gate.py`** — update approve test:

The existing test that asserts `dispatch_intent(approve_intent).accepted == False` must change:

- With a pending `Flag` in the graph and an `approve` intent (`confirmed=true`):
  `dispatch_intent` returns `accepted=True`, `routed_to="supervisor.resolve_flag"`, and a
  `FlagResolution` node exists in the graph.
- Without a matching `Flag` in the graph: returns `accepted=True` (gate does not refuse
  a no-op approve — it's already been routed and the flag was just absent).

**New test** (add to `test_supervisor_gate.py` or `test_supervisor_health_flags.py`):

- `resolve_flag_by_subject` with a matching unresolved flag → returns `True`, `FlagResolution`
  node exists.
- `resolve_flag_by_subject` with no matching flag → returns `False`, no crash.
- `resolve_flag_by_subject` with an already-resolved flag → returns `False` (idempotent).

**`surfaces/tests/test_cli.py`** — extend:

- Seed a `Flag` node in the test graph. Run `cli approve "<subject_ref>"`. Verify output
  contains `"approved:"` and a `FlagResolution` node exists in the graph.
- `cli approve "<unknown>"` (no matching flag) → output contains `"approved:"` (accepted
  even for no-op; the approve went through).

**`surfaces/tests/test_lifecycle_flags.py`** or `test_approve_flow.py` — integration:

- Full path: seed a `Flag(critical, subject_ref="run/test-123")`; build `test_context`;
  call `cmd_approve` with `subject="run/test-123"`; assert `FlagResolution` exists.

## Steps

1. Branch `sprint-20-narrative-approve` off `main`.
2. **Part A first**: `lifecycle.py` → `queries/__init__.py` → `render.py` → `cli_commands.py`
   → `cli.py` → query/CLI tests. Run `make ci`. Green before Part B.
3. **Part B**: `matrix.py` → `store.py` → `gate.py` → `cli_commands.py` → `render.py` →
   `cli.py` → supervisor gate tests → CLI/integration tests.
4. **Line count check**: before final `make ci`, run
   `wc -l surfaces/cli_commands.py surfaces/render.py agents/supervisor/domain/gate.py`.
   If `cli_commands.py` > 175L or `render.py` > 175L, extract new additions to `_extras.py`
   companions before pushing.
5. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- `cli narrative <run_id>` renders each `TradeNarrative` node's ticker and summary text;
  `"no narratives"` output for an unknown run_id.
- `approve` entry in `CAPABILITY_MATRIX` is `available=True` with `routed_to="supervisor.resolve_flag"`.
- `resolve_flag_by_subject` resolves the matching Flag by appending a `FlagResolution` node.
- `cli approve <subject>` with a seeded Flag → `FlagResolution` exists in graph after the call.
- Updated supervisor gate test: `approve` intent with `confirmed=true` returns `accepted=True`.
- `cli_commands.py` < 200L; `render.py` < 200L; all other modules < 200L.
- Import-linter 4/4 kept.
- `make ci` green at/above coverage floor (100.00).

## Out of scope (do NOT build this sprint)

Reject/modify intents (P7); stage/mode/pause/resume commands (P8); narrative quality scoring
or calibration (P7); MCP tool-binding (separate sprint); rich/textual formatting; approval
of multiple flags in one command (single-flag per command is the target). Flag anything that
feels needed earlier.

## Handback report (paste into PR / reply)

- Confirm `grep "resolve_flag_by_subject" agents/supervisor/domain/gate.py` shows the call.
- Confirm `approve` in `matrix.py` is `available=True`.
- Final line counts for `cli_commands.py` and `render.py` (were extraction companions needed?).
- Whether `TypedIntent.model_copy` with updated `parameters` worked cleanly (no frozen-model
  issues) — if it failed, describe the workaround.
- New coverage % and floor; any design note for Sprint 21.

The planning agent will review, merge to `main`, update docs, and plan Sprint 21
(remaining P6 surfaces or MCP tool-binding — TBD based on Sprint 20 outcome).
