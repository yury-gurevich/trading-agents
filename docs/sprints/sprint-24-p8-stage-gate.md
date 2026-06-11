<!-- Agent: planning | Role: sprint handover -->
# Sprint 24 — P8 stage gate machinery (P8 begins)

**Status:** planned · **Branch:** `sprint-24-p8-stage-gate` · **Build phase:** P8 · **Effort: M**

## Goal

Build the evidence-based stage gate machinery for execution stage transitions
(paper → broker_shadow → live_manual). The current stage is read from a settings env-var;
after this sprint it is graph-authoritative (`StageTransition` nodes) and promotions require
provable positive evidence. The CLI surface gains a read-only `cli stage` command. Write
actions (the `cli stage promote` operator command) are wired in Sprint 25.

**Note:** This is P8 Part 1 of 2. Sprint 25 adds the operator grammar + supervisor routing
for `stage_promote`, the `MarketPack` abstraction, and the P8 exit test.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/architecture.md`; `docs/build-plan.md`
  (P8 exit: "a new market pack can be added without core control-plane changes (G6)";
  stage gates are the prerequisite for safely using non-paper stages);
  `contracts/execution.py` (`ExecutionStage = Literal["paper", "broker_shadow",
  "live_manual", "live_autopilot"]`; `stage_transitioned` already in `emits`;
  `owns_graph=("Fill", "Reconciliation")` — **must add "StageTransition"** this sprint);
  `agents/execution/agent.py` (**166L — warn band; must extract before adding
  `_promote_stage`; see Part A0**);
  `agents/execution/domain/orders.py` (100L) and `domain/reconcile.py` (47L) — domain/
  already exists, extend it;
  `agents/execution/settings.py` (`stage: ExecutionStageValue = "paper"` — the static env
  default; after this sprint the graph is authoritative, settings is the fallback);
  `agents/reporter/domain/metrics.py` (metric keys: `portfolio.approval_rate`,
  `signal.avg_confidence` — the same keys the researcher mines; reuse the pattern from
  `agents/researcher/domain/evidence.py`);
  `agents/execution/store.py` — already has `write_fills`; add `write_stage_transition`.

- **Stage ordering.** The promotion sequence is strictly ordered:
  `paper → broker_shadow → live_manual → live_autopilot`. Demotion is always allowed
  (any stage can step back one or more stages immediately, no evidence required).
  Promotion requires evidence AND a `FlagResolution` approval (see below).
  `live_autopilot` promotion is explicitly out of scope for P8 — its evidence bar is set
  in P9/P10 when calibration curves and scorecards exist.

- **Evidence gate.** Before promotion is allowed, check `Snapshot` nodes in the graph
  (same source the researcher uses):
  - At least `min_promotion_runs` Snapshot nodes must exist.
  - The average `approval_rate` over those runs ≥ `min_approval_rate`.
  - No `Fault` nodes with `severity="critical"` exist in the graph (any unresolved critical
    fault blocks promotion; the operator must investigate first).
  If evidence is insufficient, `execution.promote_stage` returns `accepted=False` with a
  `reason` explaining which gate failed; nothing is written.

- **Approval mechanism.** When evidence IS sufficient, `execution.promote_stage` does NOT
  write the `StageTransition` immediately. Instead it writes a `Flag(subject_ref=
  "stage_promote:<target_stage>", severity="info")` and returns `accepted=False` with
  `reason="confirmation required — approve stage:promote:<target_stage> to proceed"`.
  The operator then calls `cli approve stage:promote:<target_stage>` → FlagResolution
  written → `execution.promote_stage` is called again with `confirmed=True` in parameters
  → StageTransition node written, stage becomes graph-authoritative.

  The second call path: when `parameters.get("confirmed") == "true"` AND a FlagResolution
  exists for `stage_promote:<target>`, skip the evidence check and write the transition.
  This mirrors exactly how the existing confirmation pattern works in `gate.dispatch_intent`
  (see `agents/supervisor/domain/gate.py` — the `confirmed` parameter check and flag
  resolution pattern).

- **Graph-authoritative stage.** After a `StageTransition` node is written, the current
  stage is the `to_stage` of the most recent `StageTransition` node (by `transitioned_at`).
  `execution.stage_status` must be updated to read this from the graph, falling back to
  `settings.stage` when no `StageTransition` nodes exist. `_submit()` must also consult the
  graph-authoritative stage, not settings, before accepting submissions at live-adjacent stages.

- **This sprint has no CLI write command for stage promotion.** The `promote_stage` capability
  is accessible via the bus (and tested via direct bus calls) but not yet wired into the
  operator grammar or supervisor matrix. `cli stage` is read-only: `cli stage status` and
  `cli stage history`. Sprint 25 adds `cli stage promote <target>` via the operator/supervisor
  command path.

## Part A0 — Prerequisite: free `execution/agent.py` headroom (zero-behaviour refactor)

`execution/agent.py` is 166L. Adding `_promote_stage` (~30L) and updating `_submit` (~5L)
would reach ~200L — exactly at the hard cap. **Before any other changes**, extract the
submission helpers:

### A0.1 New file: `agents/execution/domain/submit.py` — ≤ 60L

Move `_submit_order`, `_remember` (and any helpers used only by them — check the actual
agent.py source) from `agent.py` to this module. Keep the same logic; no behaviour change.

```python
"""Order submission helpers — broker call, fill caching, fault wrap.

Agent: execution
Role: wrap broker submission under fault_boundary; maintain in-memory fill dedup cache.
External I/O: Broker port calls.
"""
```

### A0.2 Update `execution/agent.py`

Import the extracted helpers and delete the moved code. `agent.py` should reach ~125L.

**Run `make ci` after A0** — must be green (zero behaviour change) before continuing.

## Part A — Contract and settings update

### A1. `contracts/execution.py`

Add three items:

```python
class PromoteStageRequest(_Frozen):
    target_stage: ExecutionStage
    reason: str
    confirmed: bool = False

class PromoteStageResult(_Frozen):
    accepted: bool
    previous_stage: ExecutionStage
    current_stage: ExecutionStage
    reason: str
    provenance: Provenance
```

Add to `CONTRACT`:
```python
Capability(
    "promote_stage",
    "Request evidence-based promotion to the next execution stage.",
    request=PromoteStageRequest,
    response=PromoteStageResult,
),
```

Add `"StageTransition"` to `owns_graph`:
```python
owns_graph=("Fill", "Reconciliation", "StageTransition"),
```

Keep `stage_transitioned` in `emits` (already declared).

### A2. `agents/execution/settings.py`

Add three tunables:

```python
min_promotion_runs: int = tunable(
    10,
    why="Require at least ten completed runs before stage promotion.",
    ge=3, le=200, unit="runs",
)
min_approval_rate: float = tunable(
    0.70,
    why="Seventy-percent approval rate as evidence the strategy is performing.",
    ge=0.0, le=1.0,
)
```

## Part B — Stage gate domain logic

### B1. `agents/execution/domain/stage_gate.py` — ≤ 80L

```python
"""Stage gate — evidence collection and promotion eligibility check.

Agent: execution
Role: determine whether evidence supports stage promotion; never write to the graph.
External I/O: GraphStore reads.
"""

STAGE_ORDER: tuple[ExecutionStage, ...] = (
    "paper", "broker_shadow", "live_manual", "live_autopilot"
)

@dataclass(frozen=True)
class StageEvidence:
    snapshot_count: int
    avg_approval_rate: float
    critical_fault_count: int

def collect_stage_evidence(graph: GraphStore) -> StageEvidence:
    """Reduce Snapshot + Fault nodes into stage promotion evidence."""
    snapshots = graph.list_nodes("Snapshot")
    faults = [
        f for f in graph.list_nodes("Fault")
        if f.props.get("severity") == "critical"
    ]
    ...

def check_promotion_allowed(
    evidence: StageEvidence,
    settings: ExecutionSettings,
) -> tuple[bool, str]:
    """Return (allowed, reason). Reason is operator-readable on rejection."""
    if evidence.snapshot_count < settings.min_promotion_runs:
        return False, f"need {settings.min_promotion_runs} runs; have {evidence.snapshot_count}"
    if evidence.avg_approval_rate < settings.min_approval_rate:
        return False, f"approval_rate {evidence.avg_approval_rate:.2f} below {settings.min_approval_rate}"
    if evidence.critical_fault_count > 0:
        return False, f"{evidence.critical_fault_count} critical fault(s) must be resolved first"
    return True, "evidence gate passed"

def is_valid_promotion(from_stage: ExecutionStage, to_stage: ExecutionStage) -> bool:
    """Return True only if to_stage is exactly one step above from_stage."""
    try:
        return STAGE_ORDER.index(to_stage) == STAGE_ORDER.index(from_stage) + 1
    except ValueError:
        return False

def is_valid_demotion(from_stage: ExecutionStage, to_stage: ExecutionStage) -> bool:
    """Return True if to_stage is any earlier stage (demotion always allowed)."""
    try:
        return STAGE_ORDER.index(to_stage) < STAGE_ORDER.index(from_stage)
    except ValueError:
        return False
```

### B2. `agents/execution/store.py` — add `write_stage_transition`

```python
def write_stage_transition(
    graph: GraphStore,
    *,
    from_stage: str,
    to_stage: str,
    reason: str,
) -> Node:
    """Append one immutable StageTransition node."""
    key = f"stage:{to_stage}:{datetime.now(tz=UTC).isoformat()}"
    return graph.merge_node("StageTransition", key, {
        "from_stage": from_stage,
        "to_stage": to_stage,
        "reason": reason,
        "transitioned_at": datetime.now(tz=UTC).isoformat(),
    })

def current_stage_from_graph(
    graph: GraphStore, default: str
) -> str:
    """Return the most recent StageTransition.to_stage, or default if none exist."""
    transitions = graph.list_nodes("StageTransition")
    if not transitions:
        return default
    latest = max(transitions, key=lambda n: str(n.props.get("transitioned_at", "")))
    return str(latest.props.get("to_stage", default))
```

### B3. `agents/execution/agent.py` — add `_promote_stage`, update `_stage_status` and `_submit`

`_promote_stage(request: PromoteStageRequest) → PromoteStageResult`:

```python
def _promote_stage(self, request: BaseModel) -> PromoteStageResult:
    req = PromoteStageRequest.model_validate(request)
    current = current_stage_from_graph(self._graph, self._settings.stage)

    # Demotion: immediate, no evidence required.
    if is_valid_demotion(current, req.target_stage):
        node = write_stage_transition(self._graph, from_stage=current, to_stage=req.target_stage, reason=req.reason)
        return PromoteStageResult(accepted=True, previous_stage=current, current_stage=req.target_stage, reason="demotion applied immediately", provenance=_prov(node))

    if not is_valid_promotion(current, req.target_stage):
        return PromoteStageResult(accepted=False, previous_stage=current, current_stage=current, reason=f"invalid transition {current} → {req.target_stage}", provenance=_empty_prov())

    # Confirmed path: FlagResolution exists + confirmed flag.
    flag_key = f"stage_promote:{req.target_stage}"
    if req.confirmed and _flag_resolved(self._graph, flag_key):
        node = write_stage_transition(self._graph, from_stage=current, to_stage=req.target_stage, reason=req.reason)
        return PromoteStageResult(accepted=True, previous_stage=current, current_stage=req.target_stage, reason="promotion confirmed and applied", provenance=_prov(node))

    # Evidence gate.
    evidence = collect_stage_evidence(self._graph)
    allowed, reason = check_promotion_allowed(evidence, self._settings)
    if not allowed:
        return PromoteStageResult(accepted=False, previous_stage=current, current_stage=current, reason=reason, provenance=_empty_prov())

    # Evidence passed: write Flag and ask for confirmation.
    write_flag(self._graph, subject_ref=flag_key, severity="info", reason=f"Promote execution stage {current} → {req.target_stage}")
    return PromoteStageResult(accepted=False, previous_stage=current, current_stage=current, reason=f"confirmation required — approve stage:promote:{req.target_stage} to proceed", provenance=_empty_prov())
```

`_flag_resolved`: helper that checks if `FlagResolution(resolution:flag:stage_promote:<target>:info)` exists in the graph. Read the key formula from `agents/supervisor/store.py` — do NOT import from supervisor; replicate the formula with a comment.

Update `_stage_status` to call `current_stage_from_graph(self._graph, self._settings.stage)`.

Update `_submit` to verify the current stage allows the submission:
```python
stage = current_stage_from_graph(self._graph, self._settings.stage)
if stage not in ("paper", "broker_shadow"):
    # live stages require explicit gating — reject rather than silently skip.
    return _live_gate_rejected(order_set)
```

## Part C — Stage surface (read-only)

### C1. `surfaces/queries/stage.py` — ≤ 50L

```python
"""Stage query projections.

Agent: surfaces
Role: read StageTransition nodes and project stage history views.
External I/O: GraphStore reads.
"""

@dataclass(frozen=True)
class StageView:
    from_stage: str
    to_stage: str
    reason: str
    transitioned_at: str

def stage_history(graph: GraphStore) -> tuple[StageView, ...]:
    """Return all StageTransition nodes, oldest first."""

def current_stage(graph: GraphStore, *, default: str = "paper") -> str:
    """Return the current execution stage (most recent transition, or default)."""
```

### C2. `surfaces/render.py` — add `render_stage` (≤ 175L total)

```python
def render_stage(stage: str, history: tuple[StageView, ...], out) -> None:
    print(f"Execution stage: {stage}", file=out)
    if history:
        print(f"  ({len(history)} transition(s) in history)", file=out)
    for s in history[-3:]:   # show last 3 transitions
        print(f"  {s.from_stage} → {s.to_stage}  {s.transitioned_at[:10]}", file=out)
        print(f"    {s.reason}", file=out)
```

### C3. `surfaces/cli_commands.py` — add `cmd_stage` (≤ 190L total)

```python
def cmd_stage(args: argparse.Namespace, ctx: SurfaceContext, out) -> None:
    del args
    from surfaces.queries.stage import current_stage, stage_history
    from surfaces.render import render_stage
    render_stage(current_stage(ctx.graph), stage_history(ctx.graph), out)
```

### C4. `surfaces/cli.py` — add `stage` subcommand

Add `sub.add_parser("stage")` and dispatch to `cmd_stage`.

## Part D — Tests

### D1. `agents/execution/tests/test_stage_gate.py` — ≤ 80L

- `check_promotion_allowed` with 0 snapshots → not allowed ("need N runs").
- `check_promotion_allowed` with 10 snapshots at approval_rate=0.50 → not allowed.
- `check_promotion_allowed` with 10 snapshots at approval_rate=0.80 → allowed.
- `check_promotion_allowed` with critical Fault present → not allowed.
- `is_valid_promotion("paper", "broker_shadow")` → True.
- `is_valid_promotion("paper", "live_manual")` → False (skips a stage).
- `is_valid_demotion("broker_shadow", "paper")` → True.
- `current_stage_from_graph` on empty graph → returns default.
- `current_stage_from_graph` with one StageTransition → returns its `to_stage`.

### D2. `agents/execution/tests/test_promote_stage.py` — ≤ 90L

Use `test_context()`. Seed Snapshot nodes with `approval_rate=0.80`.

```python
def test_promote_stage_blocked_without_evidence(ctx):
    """Promotion without evidence returns accepted=False."""
    result = _promote(ctx, "broker_shadow")
    assert not result.accepted
    assert "need" in result.reason  # evidence gate message

def test_promote_stage_writes_flag_when_evidence_passes(ctx, snapshots_ok):
    """Sufficient evidence writes Flag for approval, not a StageTransition."""
    result = _promote(ctx, "broker_shadow")
    assert not result.accepted
    assert "confirmation required" in result.reason
    assert ctx.graph.list_nodes("Flag")
    assert not ctx.graph.list_nodes("StageTransition")

def test_promote_stage_confirmed_writes_transition(ctx, snapshots_ok, flag_resolved):
    """Confirmed call after FlagResolution writes StageTransition."""
    result = _promote(ctx, "broker_shadow", confirmed=True)
    assert result.accepted
    assert result.current_stage == "broker_shadow"
    transitions = ctx.graph.list_nodes("StageTransition")
    assert len(transitions) == 1

def test_demotion_is_immediate_no_evidence(ctx):
    """Demotion from broker_shadow to paper requires no evidence."""
    # First promote (with confirmed path)
    ...
    result = _promote(ctx, "paper")  # demotion
    assert result.accepted
    assert result.current_stage == "paper"
```

### D3. `surfaces/tests/test_stage_surface.py` — ≤ 60L

- `current_stage(graph)` on empty graph → `"paper"` (default).
- `stage_history(graph)` on empty graph → empty tuple.
- `stage_history(graph)` with two StageTransition nodes → two StageView entries, oldest first.
- `cli stage` on empty graph → "Execution stage: paper".
- `cli stage` with a transition → shows the transition in output.

## Steps

1. Branch `sprint-24-p8-stage-gate` off `main`.
2. **A0 first** (extract to `domain/submit.py`). `make ci` must be green — zero behaviour
   change — before continuing. `execution/agent.py` should reach ~125L.
3. **Part A**: contract + settings update. `make ci`.
4. **Part B**: `stage_gate.py` → `store.py` additions → `agent.py` additions. `make ci`.
5. **Part C**: surface queries → render → cli_commands → cli. `make ci`.
6. **Part D**: all test files. `make ci` final.
7. **Line count check**: `wc -l agents/execution/agent.py agents/execution/domain/*.py
   surfaces/render.py surfaces/cli_commands.py`. All < 200L.
8. Push; hand back. Do not wire `stage_promote` into operator grammar — that is Sprint 25.

## Acceptance criteria

- `execution.promote_stage("broker_shadow")` with fewer than `min_promotion_runs` Snapshot
  nodes returns `accepted=False` with a `reason` explaining the gap.
- `execution.promote_stage("broker_shadow")` with sufficient evidence writes a `Flag` and
  returns `"confirmation required"`.
- `execution.promote_stage("broker_shadow", confirmed=True)` after a `FlagResolution`
  writes a `StageTransition` node and returns `accepted=True, current_stage="broker_shadow"`.
- Demotion (any stage → paper) returns `accepted=True` with no Flag requirement.
- `execution.stage_status` returns the graph-authoritative stage (from `StageTransition`
  nodes), falling back to `settings.stage` when no transitions exist.
- `cli stage` on empty graph → "Execution stage: paper".
- `cli stage` with a seeded `StageTransition` → shows the transition.
- `execution/agent.py` < 150L (after A0 extraction). All other new modules < 200L.
- Import-linter 4/4 kept.
- `make ci` green at/above coverage floor (100.00).

## Out of scope (do NOT build this sprint)

`cli stage promote <target>` operator command (operator grammar + supervisor matrix routing
— Sprint 25); `live_autopilot` promotion gate (needs P9 calibration curves); `MarketPack`
abstraction (Sprint 25); P8 exit test (Sprint 25); Alpaca broker client (P8 hardening,
requires live credentials); proposal range validation in supervisor gate (Sprint 25).

## Handback report (paste into PR / reply)

- Confirm A0 extraction: `execution/agent.py` final line count; `domain/submit.py` line count.
- Confirm `_flag_resolved` helper key formula matches supervisor/store.py (paste the formula).
- Confirm `stage_status` now reads from graph when StageTransition nodes exist.
- Final line counts: `agent.py`, `domain/stage_gate.py`, `store.py`, `domain/submit.py`.
- Whether `_submit` stage check was straightforward or needed adjustment.
- New coverage % and floor; total test count.

The planning agent will review, merge to `main`, and plan Sprint 25 (P8 Part 2: operator
grammar for stage_promote + MarketPack abstraction + P8 exit test).
