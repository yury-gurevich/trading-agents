<!-- Agent: planning | Role: sprint handover -->
# Sprint 29 — P10 curator: predictor registry + promotion gate (closes P10)

**Status:** planned · **Branch:** `sprint-29-p10-predictor-registry` · **Build phase:** P10 (exit) · **Effort: M**

## Goal

Add the **predictor registry**: a `promote_predictor` capability that gates an advisory
`Predictor` from **advisory → load-bearing** on **frozen evidence** plus **operator approval**,
and records an append-only **promotion audit** (`PredictorPromotion`). Promotion is a registry
*state*, written through the existing supervisor flag/approve flow — it does **not** wire the
predictor into any decision. **This closes P10.**

The design mirrors the Sprint 24 stage-promotion gate (evidence gate → operator approval →
append-only transition node → graph-authoritative status), applied to predictors.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/build-plan.md` P10 ("a predictor registry that
  gates advisory → load-bearing promotion with frozen evidence … strictly out of band — never
  gating a trading decision") and its **Exit**: "a versioned dataset can be built … a target
  can be trained on command and a predictor promoted through the registry."
- **Closest precedent — read it (Sprint 24 stage gate):** `agents/execution/domain/stage_gate.py`
  (`collect_stage_evidence` + `check_promotion_allowed(evidence, settings) -> (bool, reason)` —
  the evidence-gate shape to mirror), and how stage status is graph-authoritative via append-only
  transition nodes. Your registry is the same pattern for predictors.
- **The approve flow to reuse — read it:** `agents/supervisor/store.py`:
  - `write_flag(graph, *, subject_ref, severity, reason)` — keys `flag:{subject_ref}:{severity}`.
  - `resolve_flag_by_subject(graph, subject_ref)` + `_resolution_key` = `resolution:flag:{subject_ref}:{severity}`.
  - The **curator cannot write `Flag` directly** (Flag is supervisor-owned, single-writer). It
    calls **`supervisor.flag_for_human` over the bus** — exactly as the researcher does. Read
    `agents/researcher/agent.py` for the precedent: `self.<bus>.request(AgentMessage(sender=…,
    recipient="supervisor", capability="flag_for_human", payload=FlagRequest(...).model_dump(
    mode="json")))`. Read `contracts/supervisor.py` for the exact `FlagRequest` fields and confirm
    the `flag_for_human` capability name.
  - The operator approves with the **existing** `cli approve <subject>` command — it resolves any
    flag by `subject_ref` (generic; `resolve_flag_by_subject`). `subject_ref` = `predictor:<id>`.
    No change to the approve command; just confirm it handles a `predictor:` subject (add a test).
- **What S28 already wrote** (`agents/curator/store.py::write_predictor`): a `Predictor` node,
  key `predictor:{purpose}:{target}:v{version}`, props `{purpose, target, strategy, accuracy,
  train_size, test_size, sample_size, advisory: True, promotion_eligible: False, dataset_id,
  trained_at}`, edge `Predictor -[:TRAINED_ON]-> Dataset`. **The frozen evidence is `accuracy` +
  `sample_size` in those props** — the gate reads them; it does not re-train.
- **Graph is append-only.** You cannot flip `advisory`/`promotion_eligible` on the existing
  Predictor node. Promotion **state is derived** from the latest `PredictorPromotion` record —
  the same way stage status derives from transition nodes and a flag's resolved-ness from
  `FlagResolution`. Do not try to mutate the Predictor node.
- **Curator already declares `depends_on=("reporter","supervisor")`** — the supervisor bus call
  is now genuinely used (no contract dep change needed; this resolves the S27 declared-but-unused
  note). The curator must **not import** `agents.supervisor` — bus call + `contracts.supervisor`
  import only.
- **`emits` declarative-only**; nothing to publish.

## Part A — Contract: add the promotion capability

`contracts/curator.py` — add payloads + capability + owned label. Bump `version="0.2.0"` →
`"0.3.0"`.

```python
# ── Inbound ──
class PromoteRequest(_Frozen):
    predictor_id: str

# ── Outbound ──
PromotionStatus = Literal[
    "promoted", "pending_approval", "rejected", "already_promoted", "not_found"
]

class PromotionResult(_Frozen):
    predictor_id: str
    status: PromotionStatus
    state: Literal["advisory", "load_bearing"]   # registry state AFTER this call
    reason: str
    explanation: Explanation
    provenance: Provenance
```

Add to `consumes`:

```python
Capability(
    "promote_predictor",
    "Gate an advisory predictor to load-bearing on frozen evidence + operator approval.",
    request=PromoteRequest,
    response=PromotionResult,
    mcp=True,
),
```

Add `"PredictorPromotion"` to `owns_graph` →
`owns_graph=("Dataset", "TrainingExample", "Predictor", "PredictorPromotion")`.

Leave `never`, `depends_on`, `external_io` unchanged. (`mcp=True` is declarative — no MCP server
change this sprint.)

## Part B — Registry domain + store

### B1. `agents/curator/settings.py` — add two tunables

```python
min_promotion_accuracy: float = tunable(
    0.55, why="Frozen-evidence floor: a predictor below this accuracy is not promotable.",
    ge=0.0, le=1.0,
)
min_promotion_sample_size: int = tunable(
    5, why="Minimum test-split size behind the accuracy figure for it to be trustworthy.",
    ge=1, le=100_000, unit="examples",
)
```

### B2. `agents/curator/domain/registry.py` — ≤ 70L

```python
"""Predictor-registry evidence gate and promotion-status derivation.

Agent: curator
Role: decide promotion eligibility from frozen evidence; derive promotion status.
External I/O: GraphStore reads.
"""

def check_promotion_evidence(predictor: Node, settings: CuratorSettings) -> tuple[bool, str]:
    """Return (ok, reason) from the predictor's frozen accuracy + sample_size."""

def is_promoted(graph: GraphStore, predictor_id: str) -> bool:
    """True iff a PredictorPromotion(to_state='load_bearing') exists for this predictor."""

def promotion_status(graph: GraphStore, predictor_id: str) -> str:
    """Derive 'load_bearing' | 'pending_approval' | 'advisory' for a predictor."""
```

Rules:

- `check_promotion_evidence`: read `predictor.props`; reject if `accuracy < min_promotion_accuracy`
  (`reason=f"accuracy {a:.2f} below {floor:.2f}"`) or `sample_size < min_promotion_sample_size`
  (`reason=f"sample_size {n} below {min}"`); else `(True, "evidence gate passed")`.
- `is_promoted`: `graph.get_node("PredictorPromotion", f"promotion:{predictor_id}") is not None`
  (one promotion record per predictor; advisory→load_bearing is one-way this sprint).
- `promotion_status`: `load_bearing` if `is_promoted`; else `pending_approval` if a
  `Flag(subject_ref=f"predictor:{predictor_id}")` exists without its `FlagResolution`; else
  `advisory`. Replicate the supervisor key formulas (`flag:{subject}:{severity}`,
  `resolution:flag:{subject}:{severity}`) with a comment pointing at `agents/supervisor/store.py`
  — do **not** import the supervisor module. Use `severity="info"` (matches the flag you raise).

### B3. `agents/curator/store.py` — add `write_promotion` (size check: ~101L → ~125L, ok)

```python
def write_promotion(
    graph: GraphStore, *, predictor: Node, approval_ref: str
) -> Node:
    """Append the PredictorPromotion audit node and link it to its Predictor."""
```

- `PredictorPromotion` node: key `f"promotion:{predictor.key}"`, props `{predictor_id,
  from_state: "advisory", to_state: "load_bearing", accuracy, sample_size, approval_ref,
  promoted_at}` (snapshot `accuracy`/`sample_size` from `predictor.props` — frozen at promotion
  time). `approval_ref` = the resolution key `resolution:flag:predictor:{id}:info`.
- Edge: `PredictorPromotion -[:PROMOTES]-> Predictor`.

If `store.py` nears the 150L warn band, spill `write_promotion` into a new
`agents/curator/promotion_store.py` — your call from the measured count.

## Part C — Promotion orchestration + agent

### C1. `agents/curator/promotion.py` — ≤ 80L (mirror S28's `predictor.py`)

The full promote flow, so the agent handler stays thin.

```python
"""Predictor promotion orchestration.

Agent: curator
Role: run the evidence-gate → operator-approval → audit promotion flow.
External I/O: MessageBus call to supervisor.flag_for_human.
"""

def run_promotion(
    *, graph: GraphStore, bus: MessageBus, settings: CuratorSettings, predictor_id: str
) -> PromotionResult:
    """Evidence-gate, then raise-flag-or-promote depending on approval state."""
```

Flow (idempotent — approval state drives it; no explicit confirm flag):

1. `predictor = graph.get_node("Predictor", predictor_id)`. If `None` →
   `PromotionResult(status="not_found", state="advisory", reason="unknown predictor", …)`.
2. If `is_promoted(graph, predictor_id)` →
   `PromotionResult(status="already_promoted", state="load_bearing", …)`.
3. `ok, reason = check_promotion_evidence(predictor, settings)`. If not ok →
   `PromotionResult(status="rejected", state="advisory", reason=reason, …)`. **No flag raised**
   — insufficient evidence is a hard stop, not a review request.
4. Approval check: `resolution = graph.get_node("FlagResolution",
   f"resolution:flag:predictor:{predictor_id}:info")`.
   - If `resolution is None`:
     - If no `Flag` yet (`graph.get_node("Flag", f"flag:predictor:{predictor_id}:info") is None`),
       call `supervisor.flag_for_human` over the bus (subject_ref=`predictor:{predictor_id}`,
       severity=`info`, reason=`"predictor {id} passed evidence gate; awaiting approval"`).
     - Return `PromotionResult(status="pending_approval", state="advisory",
       reason="operator approval required", …)`.
   - If `resolution is not None`: `write_promotion(graph, predictor=predictor,
     approval_ref=resolution.key)`; return `PromotionResult(status="promoted",
     state="load_bearing", reason="evidence gate passed; operator approved", …)`.

`explanation` carries the accuracy + sample_size + outcome; `provenance` =
`Provenance(run_id=f"promotion:{predictor_id}", source_agent="curator",
graph_node_id=f"Predictor:{predictor_id}")`.

Use the AgentBase bus attribute for the supervisor call (confirm the name — `self.bus` vs
`self._bus` — against `agents/researcher/agent.py`). Wrap the bus call so a supervisor fault
degrades to `pending_approval`, never crashes the handler.

### C2. `agents/curator/agent.py` — add a **thin** `_promote_predictor` handler

**Headroom warning:** `agent.py` is at **180L**. Keep the handler to ~5 lines — validate
`PromoteRequest`, wrap `run_promotion(...)` in `fault_boundary` with a degraded fallback
(`PromotionResult(status="rejected", state="advisory", reason="promotion fault", …)`), return.
Register `"promote_predictor": self._promote_predictor` in `self.handlers`.

If adding the handler pushes `agent.py` over ~195L, first move the module-level helpers
(`_degraded_manifest`, `_payload`) into a small `agents/curator/agent_support.py` (zero-behaviour
refactor; `make ci` green before continuing) to buy headroom. Do not let `agent.py` reach 200.

## Part D — Registry surface

### D1. `surfaces/queries/predictors.py` — add `promotion_status` to `PredictorView`

Extend the S28 `PredictorView` with `promotion_status: str` and populate it via
`registry.promotion_status(graph, predictor_id)` (or replicate the derivation locally over
`PredictorPromotion`/`Flag`/`FlagResolution` nodes — surfaces already read the graph directly).
Keep the file ≤ 70L (currently ~53L).

### D2. `surfaces/render_extras.py` — show status in `render_predictors`

Append the status to each line, e.g. `… (advisory)` → `… [{v.promotion_status}]`.

(No new CLI subcommand needed — `cli predictors` now shows promotion status. Triggering
`promote_predictor` from the operator command layer is **out of scope**; the trigger is the bus
capability, exercised by the exit test and `cli approve` for the human step.)

## Part E — Tests

### E1. `agents/curator/tests/test_registry.py` — ≤ 70L

- `check_promotion_evidence`: accuracy below floor → `(False, …)`; sample_size below min →
  `(False, …)`; both pass → `(True, …)`.
- `is_promoted` / `promotion_status` over seeded `Predictor` + optional `PredictorPromotion` /
  `Flag` / `FlagResolution` nodes → `advisory` / `pending_approval` / `load_bearing`.

### E2. `agents/curator/tests/test_promote_predictor.py` — ≤ 100L

Bind a `CuratorAgent` (with a real `InProcessBus` so the supervisor handler is reachable — use
`build_test_context`/`bind_paper_loop_agents` so `supervisor` is bound, OR bind a SupervisorAgent
alongside the curator). Seed narratives → `build_dataset` → `train_predictor` first.

- **Low accuracy** (force a predictor whose `accuracy < min_promotion_accuracy`) →
  `promote_predictor` → `status="rejected"`, no `Flag`, no `PredictorPromotion`.
- **Passing evidence, first call** → `status="pending_approval"`, a `Flag(subject_ref=
  "predictor:…")` exists, no `PredictorPromotion`.
- **After `cli approve predictor:<id>`** (or a direct `supervisor` resolve over the bus) →
  second `promote_predictor` → `status="promoted"`, `state="load_bearing"`, one
  `PredictorPromotion` node with `PROMOTES` edge and frozen `accuracy`/`sample_size` props.
- **Idempotent:** a third `promote_predictor` → `status="already_promoted"` (no second record).
- **Unknown id** → `status="not_found"`.

### E3. `surfaces/tests/test_registry_surface.py` — ≤ 60L

- `cli predictors` shows `advisory` for a fresh predictor, `pending_approval` after a flag, and
  `load_bearing` after a promotion record.

### E4. `agents/curator/tests/test_p10_exit.py` — ≤ 110L  *(the P10 exit proof)*

End-to-end, using a context where `curator` + `supervisor` are both bound:

```python
def test_p10_exit_dataset_train_promote_with_provenance() -> None:
    """P10 exit: build -> train -> promote through the registry, full provenance."""
    # 1. build_dataset, 2. train_predictor (ensure evidence passes the gate),
    # 3. promote_predictor -> pending, 4. approve the flag, 5. promote_predictor -> promoted.
    # Assert the full provenance chain exists:
    #   PredictorPromotion -[:PROMOTES]-> Predictor -[:TRAINED_ON]-> Dataset
    #     -[:CONTAINS]-> TrainingExample -[:DERIVED_FROM]-> TradeNarrative
    # Assert PromotionResult(status="promoted", state="load_bearing").

def test_p10_exit_promotion_mutates_no_decision_node() -> None:
    """The whole curator flow (build/train/promote) writes only curator+Flag nodes."""
    # Snapshot every label EXCEPT {Dataset, TrainingExample, Predictor, PredictorPromotion,
    # Flag, FlagResolution} before the full flow; assert identical after.
    # Proves a load-bearing predictor is a registry record, never a decision input.
```

The second test is the **"never influences a decision" invariant at P10 exit** — promotion adds
only curator-owned + supervisor approval nodes; no `Recommendation`/`OrderIntent`/`Fill`/
`Position`/`CloseDecision` is created or changed.

## Steps

1. Branch `sprint-29-p10-predictor-registry` off `main`.
2. **Part A** contract; boundary meta-test + mypy; `make ci`.
3. **Part B** settings → registry → store. `make ci`.
4. **Part C** promotion orchestration → thin agent handler (mind the 180L headroom; refactor
   to `agent_support.py` if needed, green before continuing).
5. **Part D** surface.
6. **Part E** tests; `make ci` final — fully green.
7. **Line-count check:** `wc -l agents/curator/agent.py agents/curator/promotion.py
   agents/curator/store.py agents/curator/domain/registry.py`. All < 200L.
8. Push; hand back.

## Acceptance criteria

- `promote_predictor` on a predictor below the evidence floor → `status="rejected"`, no flag,
  no promotion record.
- `promote_predictor` on a passing predictor with no approval → `status="pending_approval"` and
  a supervisor `Flag(subject_ref="predictor:<id>")` written via the bus.
- After `cli approve predictor:<id>` → `promote_predictor` → `status="promoted"`,
  `state="load_bearing"`, one append-only `PredictorPromotion` node with a `PROMOTES` edge and
  frozen `accuracy`/`sample_size`.
- Re-promotion is idempotent → `status="already_promoted"`; unknown id → `status="not_found"`.
- `cli predictors` shows `advisory` / `pending_approval` / `load_bearing` correctly.
- **`test_p10_exit.py` green:** the full build→train→promote provenance chain exists, AND the
  flow mutates no trading-decision node.
- Import-linter 4/4 kept (curator calls supervisor via bus; imports only `kernel` + `contracts`;
  no `agents.supervisor` import; forecaster untouched).
- `make ci` green at/above the coverage floor (100.00); raise it only if measured coverage climbs.

## Out of scope (do NOT build this sprint)

- Wiring a load-bearing predictor into any decision agent (a future runtime/forecaster phase;
  P10 is strictly out of band — promotion is a registry record only).
- Demotion / re-promotion versioning (one-way advisory→load_bearing this sprint).
- Implementing or importing the forecaster.
- Operator-command-layer `promote` grammar (the bus capability + `cli approve` are the path).
- MCP binding of `promote_predictor`; real predictor/model binary store.

## P10 exit evaluation (planning agent performs after merge)

P10 exit (build-plan): "a versioned dataset can be built from collected data and described to
the operator with full provenance; a target can be trained on command and a predictor promoted
through the registry."

| Capability | Entry point | Sprint |
| --- | --- | --- |
| Versioned dataset built + described | `curator.build_dataset` / `describe_corpus` | S27 |
| Target trained on command | `curator.train_predictor` (advisory + frozen evidence) | S28 |
| Predictor promoted through registry | `curator.promote_predictor` + `cli approve` | S29 |
| Promotion audit (append-only) | `PredictorPromotion` node | S29 |
| Never influences a decision | `test_p10_exit.py` (boundary half) | S27–S29 |

If all rows green and `test_p10_exit.py` passes, **close P10** in STATE + build-plan. The next
queued work is **P11 — Decision-logic depth** (the deterministic analyst/PM/scanner/reporter
deepening already tracked in build-plan).

## Handback report (paste into PR / reply)

- Contract change confirmed (payloads + capability + `owns_graph` + version bump) and boundary
  meta-test green.
- The bus attribute name used for the `supervisor.flag_for_human` call (and confirmation the
  `cli approve predictor:<id>` path resolved the flag without changes).
- Whether `write_promotion` / the agent handler needed module spills (`promotion_store.py` /
  `agent_support.py`) and the resulting line counts.
- `test_p10_exit.py` result — confirm the full provenance chain and the no-decision-node
  boundary both held.
- Final line counts: agent.py, promotion.py, registry.py, store.py.
- New coverage % and floor; total test count.

The planning agent reviews, merges to `main`, **closes P10** if the exit test passes, and plans
the first **P11** sprint (analyst decision-logic depth).
