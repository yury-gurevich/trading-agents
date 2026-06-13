<!-- Agent: planning | Role: sprint handover -->
# Sprint 23 — P7 researcher: propose bounded parameter changes (P7 begins)

**Status:** planned · **Branch:** `sprint-23-p7-researcher` · **Build phase:** P7 · **Effort: M**

## Goal

Implement the researcher agent (`propose` + `evidence` capabilities), write proposals into
the graph, flag them for human review via the existing supervisor Flag mechanism, surface
proposals in the CLI (`cli proposals`), and prove P7's core invariant: the researcher
proposes bounded parameter changes but never applies them.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/architecture.md`; `docs/build-plan.md`
  (P7 exit: "a measured proposal can be reviewed and approved through the operator with
  full provenance"); `contracts/researcher.py` (full contract already declared;
  `depends_on=("reporter",)` — **must add "supervisor" this sprint**; owns `Experiment` +
  `ParamChange` nodes; capabilities: `propose`, `evidence`);
  `agents/researcher/__init__.py` (stub only — full implementation this sprint);
  `agents/reporter/domain/metrics.py` (exact keys: `portfolio.approval_rate`,
  `signal.avg_confidence`, `signal.rejection_count` — these are the metrics the researcher
  mines from `Snapshot` nodes);
  `agents/reporter/store.py` (`write_snapshot` stores `metrics_blob` in node prop `"metrics"`
  as `{"portfolio": {...}, "signal": {...}, "regime": {...}}` — researcher reads
  `node.props["metrics"]`);
  `agents/supervisor/store.py` (`write_flag` — researcher calls this via bus to queue a
  proposal for human review; subject_ref `proposal:<proposal_id>`);
  `surfaces/cli_commands.py` (169L — cmd_proposals adds ~15L → ~184L; in warn band, ok);
  `surfaces/render.py` (**187L — must extract before adding render_proposals; see Part A0**).

- **Evidence model.** The researcher reads `Snapshot` nodes (reporter-owned) directly from
  the graph using `list_nodes("Snapshot")`. No bus call to reporter is needed — graph reads
  are always permitted. It filters to the lookback window using `node.props["run_id"]`
  timestamps or simply takes all Snapshot nodes if provenance is opaque (P7 simplification:
  take all Snapshot nodes, up to `lookback_days` worth by count order).

- **Proposal heuristic (P7 scope).** One target parameter: `analyst.confidence_floor`.
  Derive direction from `avg_confidence` across the evidence window:
  - If `avg_confidence < CONFIDENCE_LOW_WATER` (default 0.40) over ≥ `min_sample_runs`
    snapshots → raise floor by `confidence_step` (default 0.05): fewer but stronger signals.
  - If `avg_confidence > CONFIDENCE_HIGH_WATER` (default 0.70) over ≥ `min_sample_runs`
    snapshots → lower floor by `confidence_step`: accept more candidates.
  - Otherwise → degrade gracefully: return a proposal with zero changes and an explanation
    that the evidence does not yet warrant a change.
  All tunables; all bounds enforced. The current reference value for `confidence_floor` is
  declared in `ResearcherSettings.confidence_floor_reference` (default 0.30, matching the
  analyst agent's tunable default). The researcher CANNOT import from `agents/analyst/` —
  it uses its own reference constant.

- **Forbidden combinations (P7 scope).** Reject a proposal if:
  - `len(changes) > settings.max_changes_per_proposal` (default 2).
  - `evidence_window_days < settings.min_evidence_window_days` (default 30).
  - Any `proposed_value` is outside the declared bounds for that parameter (hardcode
    bounds for `confidence_floor`: ge=0.0, le=1.0 — from the analyst contract).
  If validation fails, return a `ParameterChangeProposal` with `changes=()` and a rationale
  explaining which constraint was violated.

- **Approval flow.** After writing `Experiment` + `ParamChange` graph nodes, the researcher
  calls `supervisor.flag_for_human` via bus with:
  `subject_ref=f"proposal:{proposal.proposal_id}", severity="info",
  reason=f"Researcher proposes {len(changes)} parameter change(s)"`.
  This writes a `Flag` node (supervisor-owned). The operator approves via the existing
  `cli approve proposal:<proposal_id>` command → `FlagResolution` written. The `cli proposals`
  surface shows approval status by checking `FlagResolution` existence.

- **"Never applies" invariant.** The researcher writes ONLY `Experiment` + `ParamChange`
  nodes. It never modifies `.env`, never calls `os.environ.__setitem__`, never re-instantiates
  any `AgentSettings` subclass with overridden values. The boundary test proves this by
  asserting `AnalystSettings().confidence_floor` equals the original default before and after
  the full propose+approve flow.

## Part A0 — Prerequisite: free `render.py` headroom (zero-behaviour refactor)

`render.py` is at 187L. Adding `render_proposals` (~12L) would reach 199L — one line from
the hard cap. **Before any other code**, extract the Sprint 21 additions to a companion file:

### A0.1 New file: `surfaces/render_extras.py`, ≤ 50L

```python
"""Extended render helpers (incidents and explain) extracted from render.py.

Agent: surfaces
Role: render incident and narrative-explain CLI output.
External I/O: none.
"""
```

Move `render_incidents` and `render_explain` (and any imports used only by them) from
`render.py` into this file.

### A0.2 Update callers

In `surfaces/cli_commands.py`, update:

```python
from surfaces.render import render_incidents, render_explain
```

to:

```python
from surfaces.render_extras import render_incidents, render_explain
```

`render.py` shrinks by ~28L to ~159L. **Run `make ci` — must be green** (zero behaviour
change) before touching any other file.

## Part A — Contract update

### A1. `contracts/researcher.py` — add `"supervisor"` to `depends_on`

```python
depends_on=("reporter", "supervisor"),
```

One line. The researcher legitimately calls `supervisor.flag_for_human` via bus to queue
proposals for human review. This is a bus call, not a Python import — import-linter is
unaffected.

## Part B — Researcher agent

### B1. `agents/researcher/settings.py` — ≤ 60L

```python
"""Researcher agent settings and evidence/proposal tunables.

Agent: researcher
Role: own defaults for evidence window, proposal bounds, and parameter reference values.
External I/O: process environment and the .env file.
"""

class ResearcherSettings(AgentSettings):
    model_config = SettingsConfigDict(env_prefix="RESEARCHER_", frozen=True)

    lookback_days: int = tunable(90, why="...", ge=30, le=365, unit="days")
    min_sample_runs: int = tunable(5, why="...", ge=3, le=100, unit="runs")
    min_evidence_window_days: int = tunable(30, why="...", ge=7, le=365, unit="days")
    max_changes_per_proposal: int = tunable(2, why="...", ge=1, le=5)
    confidence_floor_reference: float = tunable(
        0.30,
        why=(
            "Reference baseline for analyst.confidence_floor when proposing changes. "
            "Matches the analyst agent's default; declared here so the researcher "
            "does not import from agents/."
        ),
        ge=0.0, le=1.0,
    )
    confidence_step: float = tunable(
        0.05,
        why="Incremental adjustment per proposal cycle; small to keep changes reviewable.",
        ge=0.01, le=0.20,
    )
    confidence_low_water: float = tunable(
        0.40,
        why="Below this avg_confidence the researcher proposes raising the floor.",
        ge=0.0, le=1.0,
    )
    confidence_high_water: float = tunable(
        0.70,
        why="Above this avg_confidence the researcher proposes lowering the floor.",
        ge=0.0, le=1.0,
    )
```

Justify each `why` properly — no placeholder strings.

### B2. `agents/researcher/domain/evidence.py` — ≤ 70L

```python
"""Evidence collection from the provenance graph.

Agent: researcher
Role: read Snapshot nodes from the graph and reduce them to evidence statistics.
External I/O: GraphStore reads (never writes).
"""

@dataclass(frozen=True)
class RunEvidence:
    snapshot_count: int
    avg_confidence: float
    avg_approval_rate: float
    avg_rejection_count: float

def collect_evidence(
    graph: GraphStore,
    min_sample_runs: int,
) -> RunEvidence | None:
    """Return evidence reduced from all Snapshot nodes, or None if too few samples."""
    snapshots = graph.list_nodes("Snapshot")
    if len(snapshots) < min_sample_runs:
        return None
    # Each Snapshot stores metrics_blob in props["metrics"] as
    # {"portfolio": {...}, "signal": {...}}. Use .get() with 0.0 fallback for safety.
    ...
    return RunEvidence(...)
```

Read `node.props.get("metrics", {})` → `metrics.get("signal", {})` → `"avg_confidence"`.
Read `node.props.get("metrics", {})` → `metrics.get("portfolio", {})` → `"approval_rate"`.

### B3. `agents/researcher/domain/proposal.py` — ≤ 80L

```python
"""Proposal builder — turns evidence into bounded parameter-change proposals.

Agent: researcher
Role: apply evidence-window and forbidden-combination rules; produce ProposedChange list.
External I/O: none.
"""

def build_proposal(
    evidence: RunEvidence,
    settings: ResearcherSettings,
    proposal_id: str,
) -> ParameterChangeProposal:
    """Build a ParameterChangeProposal from evidence, or a zero-change proposal if none warranted."""
```

Rules:

- `evidence_window_days = len(snapshots)` — if `< settings.min_evidence_window_days`,
  return a zero-change proposal explaining the gap.
- Determine direction: avg_confidence < low_water → UP; > high_water → DOWN; else → NEUTRAL.
- NEUTRAL → zero-change proposal; reason: "evidence does not yet warrant a change."
- UP: `proposed_value = min(settings.confidence_floor_reference + settings.confidence_step, 1.0)`
- DOWN: `proposed_value = max(settings.confidence_floor_reference - settings.confidence_step, 0.0)`
- If proposed equals current (already at bound) → zero-change proposal.
- Wrap in `ParameterChangeProposal(proposal_id, changes=(...,), rationale=Explanation(...))`.

Forbidden-combination check: if `len(changes) > settings.max_changes_per_proposal`,
zero-change proposal with rationale explaining the constraint. (P7 only proposes one change
at a time so this is a defensive assertion, not a likely path.)

### B4. `agents/researcher/store.py` — ≤ 60L

```python
"""Researcher graph write path.

Agent: researcher
Role: write Experiment and ParamChange graph artifacts.
External I/O: GraphStore writes via the injected backend.
"""

def write_proposal(graph: GraphStore, proposal: ParameterChangeProposal) -> None:
    """Write Experiment + ParamChange nodes; link them; idempotent on proposal_id."""
    exp_key = f"experiment:{proposal.proposal_id}"
    exp_node = graph.merge_node("Experiment", exp_key, {
        "proposal_id": proposal.proposal_id,
        "change_count": len(proposal.changes),
        "rationale_summary": proposal.rationale.summary,
        "created_at": datetime.now(tz=UTC).isoformat(),
    })
    for change in proposal.changes:
        change_key = f"param-change:{proposal.proposal_id}:{change.parameter}"
        change_node = graph.merge_node("ParamChange", change_key, {
            "proposal_id": proposal.proposal_id,
            "parameter": change.parameter,
            "current_value": change.current_value,
            "proposed_value": change.proposed_value,
            "evidence_window_days": change.evidence_window_days,
            "effect_summary": change.expected_effect.summary,
        })
        graph.add_edge(exp_node, change_node, "PROPOSES")
```

### B5. `agents/researcher/agent.py` — ≤ 100L

```python
"""Researcher agent — evidence into bounded parameter-change proposals.

Agent: researcher
Role: mine accumulated graph evidence and propose bounded changes for operator review.
External I/O: MessageBus calls to supervisor.flag_for_human.
"""
```

Bind `propose` and `evidence` capabilities.

`_propose(request: ResearchRequest) → ParameterChangeProposal`:

1. `evidence = collect_evidence(self._graph, self._settings.min_sample_runs)`
2. If evidence is None: return a zero-change proposal with rationale "insufficient data".
3. `proposal = build_proposal(evidence, self._settings, proposal_id=_new_id())`
4. `write_proposal(self._graph, proposal)`
5. If `proposal.changes`:  call `supervisor.flag_for_human` via bus:

   ```python
   self._bus.request(AgentMessage(
       sender="researcher",
       recipient="supervisor",
       message_type="request",
       capability="flag_for_human",
       payload=FlagRequest(
           subject_ref=f"proposal:{proposal.proposal_id}",
           severity="info",
           reason=f"Researcher proposes {len(proposal.changes)} change(s)",
       ).model_dump(mode="json"),
   ))
   ```

6. Return `proposal`.

`_evidence(request: ResearchRequest) → Explanation`:

- `collect_evidence(...)` → format as Explanation with available metric values.
- If no evidence: Explanation(summary="insufficient data for evidence window", ...).

`_new_id()`: `uuid4().hex[:12]` — short, unique, graph-key-safe.

Wrap both handlers in `fault_boundary`.

## Part C — Proposals surface

### C1. `surfaces/queries/proposals.py` — ≤ 60L

```python
"""Proposal query projections.

Agent: surfaces
Role: read Experiment and ParamChange nodes and project proposal views.
External I/O: GraphStore reads.
"""

@dataclass(frozen=True)
class ProposalView:
    proposal_id: str
    change_count: int
    rationale: str
    created_at: str
    approved: bool     # True if FlagResolution(proposal:<proposal_id>) exists

def all_proposals(graph: GraphStore) -> tuple[ProposalView, ...]:
    """Return all proposals, newest first."""
    ...
```

`approved` check: for each experiment node, check if
`graph.get_node("FlagResolution", _resolution_key(f"proposal:{proposal_id}", "info"))` is
not None. Use the same key convention as `supervisor/store.py`'s `_resolution_key` — do NOT
import from `agents/supervisor/`. Replicate the key formula: read the source of
`_resolution_key` in `agents/supervisor/store.py` and hardcode the same formula in
`proposals.py` with a comment pointing to the supervisor store.

### C2. `surfaces/render.py` — add `render_proposals`, ≤ 170L total after A0

```python
def render_proposals(proposals: tuple[ProposalView, ...], out) -> None:
    if not proposals:
        print("no proposals pending review", file=out)
        return
    print(f"Proposals: {len(proposals)}", file=out)
    for p in proposals:
        status = "approved" if p.approved else "pending"
        print(f"\n  [{p.proposal_id}] {status} — {p.change_count} change(s)", file=out)
        print(f"  {p.rationale}", file=out)
        print(f"  created: {p.created_at}", file=out)
```

### C3. `surfaces/cli_commands.py` — add `cmd_proposals`

```python
from surfaces.queries.proposals import all_proposals
from surfaces.render import render_proposals

def cmd_proposals(args: argparse.Namespace, ctx: SurfaceContext, out) -> None:
    del args
    render_proposals(all_proposals(ctx.graph), out)
```

### C4. `surfaces/cli.py` — add `proposals` subcommand

Add `sub.add_parser("proposals")` and dispatch to `cmd_proposals`.

## Part D — Tests

### D1. `agents/researcher/tests/__init__.py` — empty (module marker)

### D2. `agents/researcher/tests/test_evidence.py` — ≤ 60L

- Empty graph → `collect_evidence(..., min_sample_runs=5)` returns None.
- Graph with 4 Snapshot nodes → still returns None (below min_sample_runs).
- Graph with 5 Snapshot nodes (avg_confidence=0.35) → returns `RunEvidence(snapshot_count=5,
  avg_confidence≈0.35, ...)`.

Seed Snapshot nodes with:

```python
graph.merge_node("Snapshot", f"snapshot:run-{i}", {
    "run_id": f"run-{i}",
    "metrics": {
        "portfolio": {"approval_rate": 0.8, ...},
        "signal": {"avg_confidence": 0.35, "rejection_count": 1.0},
    },
    "headline_summary": "test run",
})
```

### D3. `agents/researcher/tests/test_proposal.py` — ≤ 70L

- Evidence with `avg_confidence=0.35` (below 0.40 low-water) → proposal proposes raising
  `confidence_floor` from 0.30 to 0.35; `changes` has 1 entry.
- Evidence with `avg_confidence=0.50` (between 0.40 and 0.70) → zero-change proposal.
- Evidence with `avg_confidence=0.75` (above 0.70 high-water) → proposal proposes lowering.
- Evidence at floor=0.00 + low-water trigger → clamped; proposed_value=0.0 (already at bound)
  → zero-change proposal (no change to make).

### D4. `agents/researcher/tests/test_propose.py` — ≤ 80L

Use `test_context()` (from `surfaces/context.py`). Seed 6 Snapshot nodes with
`avg_confidence=0.35`.

```python
def test_propose_writes_graph_nodes(ctx):
    response = ctx.bus.request(AgentMessage(
        sender="test",
        recipient="researcher",
        message_type="request",
        capability="propose",
        payload=ResearchRequest().model_dump(mode="json"),
    ))
    proposal = ParameterChangeProposal.model_validate(response.payload)
    assert proposal.changes  # non-empty — evidence warrants a change
    # Graph artifacts
    experiments = ctx.graph.list_nodes("Experiment")
    assert len(experiments) == 1
    changes = ctx.graph.list_nodes("ParamChange")
    assert len(changes) == 1
    # Flag written by supervisor
    flags = ctx.graph.list_nodes("Flag")
    assert any("proposal:" in str(f.props.get("subject_ref", "")) for f in flags)

def test_propose_insufficient_evidence(ctx):
    # No snapshots seeded → zero-change proposal, no Flag written
    response = ctx.bus.request(...)
    proposal = ParameterChangeProposal.model_validate(response.payload)
    assert not proposal.changes
    assert not ctx.graph.list_nodes("Flag")
```

### D5. `agents/researcher/tests/test_p7_boundary.py` — ≤ 50L

```python
def test_researcher_never_applies_proposed_change(ctx, snapshots):
    """Researcher proposes but does not apply: AnalystSettings remains at default."""
    from agents.analyst.settings import AnalystSettings
    original = AnalystSettings().confidence_floor

    # Run full propose + approve flow
    ctx.bus.request(...)  # researcher.propose
    # Approve the proposal via supervisor flag resolution
    ctx.bus.request(...)  # supervisor.dispatch_intent with approve

    # Verify: analyst setting is unchanged
    assert AnalystSettings().confidence_floor == original
    # Verify: Experiment node exists (proposal IS written)
    assert ctx.graph.list_nodes("Experiment")
```

**Important:** this test imports from `agents.analyst.settings` — this is allowed in tests.
Only agent modules themselves are restricted by import-linter; test files are not in the
linter's source set.

### D6. `surfaces/tests/test_proposals_surface.py` — ≤ 70L

- `all_proposals` on empty graph → empty tuple.
- `all_proposals` with one `Experiment` node and no `FlagResolution` → one ProposalView
  with `approved=False`.
- `all_proposals` with matching `FlagResolution` → `approved=True`.
- `cli proposals` on empty graph → `"no proposals pending review"`.
- `cli proposals` with a pending proposal → output contains proposal_id and "pending".

### D7. `surfaces/tests/test_p7_exit.py` — ≤ 100L

End-to-end proof of the P7 exit criterion using `test_context()`:

```python
def test_p7_propose(ctx, snapshots):
    """Proposal created with Experiment + ParamChange nodes and a Flag."""

def test_p7_approve_proposal(ctx, snapshots):
    """Approving the proposal writes a FlagResolution; ProposalView shows approved=True."""

def test_p7_never_applies(ctx, snapshots):
    """After propose + approve, AnalystSettings.confidence_floor is still the default."""

def test_p7_evidence_query(ctx, snapshots):
    """researcher.evidence returns a non-empty Explanation."""
```

## Steps

1. Branch `sprint-23-p7-researcher` off `main`.
2. **A0 first** (extract render_extras.py). `make ci` must be green before continuing.
3. **A1**: update `contracts/researcher.py` `depends_on`.
4. **Part B**: settings → evidence → proposal → store → agent. After each sub-step run
   `make ci` (or at minimum after B5). Shortest feedback loop wins.
5. **Part C**: proposals query → render → cli_commands → cli. `make ci`.
6. **Part D**: all test files. `make ci` final — must be fully green.
7. **Line count check**: `wc -l surfaces/render.py surfaces/render_extras.py
   surfaces/cli_commands.py agents/researcher/agent.py agents/researcher/domain/*.py`.
   All < 200L.
8. Push; hand back.

## Acceptance criteria

- `researcher.propose` with 5+ seeded Snapshot nodes writes an `Experiment` node, at least
  one `ParamChange` node, and a `Flag(subject_ref="proposal:...")` to the graph.
- `researcher.propose` with fewer than `min_sample_runs` Snapshot nodes returns a
  zero-change proposal and writes no Flag.
- `researcher.evidence` returns an `Explanation` with a non-empty `summary`.
- Evidence below `confidence_low_water` → proposes raising `confidence_floor`; above
  `confidence_high_water` → proposes lowering; between thresholds → zero changes.
- `cli proposals` on empty graph → "no proposals pending review".
- `cli proposals` with a pending proposal → shows proposal_id and "pending".
- `cli proposals` after approval → shows "approved".
- `test_p7_boundary.py` green: `AnalystSettings().confidence_floor == original` after
  the full propose+approve flow.
- `test_p7_exit.py` green: all four assertions pass.
- `render.py` ≤ 170L (after A0 extraction); `render_extras.py` ≤ 50L; all other new
  modules ≤ 150L.
- Import-linter 4/4 kept (researcher calls supervisor via bus, not Python import).
- `make ci` green at/above coverage floor (100.00).

## Out of scope (do NOT build this sprint)

Multi-parameter proposals (P7 can propose more; deferred to a hardening sprint); MCP
binding of researcher tools (Sprint 22's MCP server has a fixed tool list; updating it is
deferred); automated scheduling of research runs (researcher is triggered by the P7 exit
test and later by the dispatcher in P8); applying an approved proposal (P8+; this sprint
proves it is NEVER done); confidence floor calibration curves (P7/P9 workstream).

## P7 exit evaluation (planning agent performs after merge)

P7 exit criterion: "a measured proposal can be reviewed and approved through the operator,
with full provenance."

| Capability | Entry point | Sprint |
| --- | --- | --- |
| Propose bounded change | `researcher.propose` bus call | S23 |
| Evidence for proposal | `researcher.evidence` bus call | S23 |
| Human review flag queued | `Flag(proposal:X)` in graph | S23 |
| Operator reviews proposals | `cli proposals` | S23 |
| Operator approves | `cli approve proposal:X` (existing) | S20 |
| FlagResolution written | Graph node | S20 |
| Never applies | `test_p7_boundary.py` green | S23 |

If all rows green and `test_p7_exit.py` passes, close P7 in STATE.md + build-plan.md.
Plan Sprint 24 to begin P8 (hardening: stage-promotion gates, range validation, market-pack
readiness checklist).

## Handback report (paste into PR / reply)

- Confirm A0 extraction: render.py final line count; render_extras.py line count.
- Confirm `depends_on` updated in `contracts/researcher.py`.
- Whether evidence heuristic needed any adjustment from plan (note any divergence).
- Whether `FlagResolution` key formula was copied correctly from supervisor/store.py (note
  the formula used in proposals.py).
- Final line counts: agent.py, evidence.py, proposal.py, store.py.
- `test_p7_boundary.py` result — specifically whether `AnalystSettings().confidence_floor`
  assertion passed without mocking.
- New coverage % and floor; total test count.

The planning agent will review, merge to `main`, close P7 if the exit test passes, and
plan Sprint 24 (P8 hardening).
