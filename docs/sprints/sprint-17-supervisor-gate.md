# Sprint 17 — Supervisor capability gate (P5 exit)

**Status:** planned · **Branch:** `sprint-17-supervisor-gate` · **Build phase:** P5 (operator + supervisor safety) · **Effort: M**

## Goal

Complete the supervisor with its three remaining P5 capabilities: `dispatch_intent` (validate a
`TypedIntent` against the capability matrix and the hard-NO surface, then accept or refuse),
`system_status` (health report from graph state), and `flag_for_human` (raise an anomaly into
the review queue). The **P5 exit test** chains `OperatorAgent.interpret` → `SupervisorAgent.dispatch_intent`
end-to-end: a parsed command produces a `DispatchResult` with a full audit trail and zero
unsafe bypasses. Sprint 17 depends on Sprint 16 — branch off `sprint-16-operator`.

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails + gate); `docs/architecture.md` (layers,
  the one rule, supervisor role); `contracts/supervisor.py` (full contract — three capabilities
  are unimplemented; do not change the contract this sprint); `agents/supervisor/agent.py`
  (currently 112 lines — will grow into the warn-band; keep it < 200);
  `agents/supervisor/store.py` (add `write_flag` here); `contracts/operator.py`
  (`TypedIntent` — the input to `dispatch_intent`); `agents/operator/agent.py` +
  `agents/operator/domain/grammar.py` (the confirmation policy — **must match** the matrix);
  `contracts/reporter.py` + `contracts/portfolio_manager.py` (routing targets for status/explain).
- The supervisor is a **gate and router, not an executor.** `dispatch_intent` returns a
  `DispatchResult` with `routed_to` set — it does NOT make follow-up bus calls on behalf of the
  caller. Execution is triggered by the caller (P6 surface) after receiving the approved result.
  Exception: `system_status` queries the graph directly and returns `MasterReport` — this is the
  supervisor's own read capability, not routing.
- P5 exit criterion: "the allowed command families execute safely with full audit and zero unsafe
  bypasses."

## Key design constraints (do not break)

- **The supervisor never makes a domain decision.** `dispatch_intent` gates; it does not trade,
  approve orders, or modify parameters. The `routed_to` field names the next hop; the caller acts
  on it.
- **Hard-NO is checked before confirmation.** A hard-NO intent is refused unconditionally —
  confirmation does not unlock it, ever. Order: (1) hard-NO check → refuse; (2) confirmation
  check → flag and refuse; (3) matrix lookup → route or "not available."
- **Confirmation gate writes a Flag node.** When `TypedIntent.requires_confirmation` is `True`
  and the intent is not yet confirmed (no `"confirmed": "true"` in `parameters`), write a `Flag`
  node (`severity="warn"`, `reason="awaiting confirmation"`, `subject_ref=intent provenance run_id`)
  and return `DispatchResult(accepted=False, rejection="confirmation required — resubmit with confirmed=true")`.
  This is the P5 confirmation UX. The dashboard (P6) will render pending `Flag` nodes.
- **Confirmation token is in `parameters`.** To confirm a pending intent, the caller resubmits
  the same `TypedIntent` with `parameters["confirmed"] = "true"`. The supervisor clears the Flag
  node (mark `status="resolved"`) and proceeds to route.
- **`MasterReport.healthy` is derived, never cached.** Query live graph state on every
  `system_status` call. Do not cache.
- **The one rule.** `agents/supervisor/` imports `kernel` + `contracts` only.
- **No contract changes this sprint.** `contracts/supervisor.py` already has all five
  capabilities declared. Only add `Flag`-write functions to `store.py` and the three handlers
  to `agent.py`.

## Capability matrix (bake into `agents/supervisor/domain/matrix.py`)

```python
@dataclass(frozen=True)
class RouteSpec:
    agent: str | None        # None = not yet available
    capability: str | None   # capability name on the target agent's bus endpoint
    available: bool          # False → DispatchResult(accepted=True, routed_to=None, rejection="not available in current build phase")
```

| IntentFamily | agent | capability | available | Notes |
| --- | --- | --- | --- | --- |
| `status` | `reporter` | `report` | True | Read-only; no confirmation required |
| `explain` | `reporter` | `narrative` | True | Read-only; no confirmation required |
| `run` | `orchestration` | `execute_run` | True | Caller triggers `Dispatcher.execute_run` |
| `approve` | `None` | `None` | False | P7 — researcher proposals queue |
| `reject` | `None` | `None` | False | P7 |
| `modify` | `None` | `None` | False | P7 — parameter change flow |
| `mode` | `None` | `None` | False | P8 — operating mode switch |
| `stage` | `None` | `None` | False | P8 — stage promotion gate |
| `pause` | `None` | `None` | False | P8 — scheduler control |
| `resume` | `None` | `None` | False | P8 — scheduler control |

The `available=True` entries return `DispatchResult(accepted=True, routed_to=f"{agent}.{capability}")`.
The `available=False` entries return `DispatchResult(accepted=False, rejection="not available in current build phase: {family} requires P7/P8")`.

## Hard-NO surface (`agents/supervisor/domain/hard_no.py`)

```python
def is_hard_no(intent: TypedIntent) -> tuple[bool, str]:
    """Return (True, reason) if the intent triggers the hard-NO surface."""
    params = intent.parameters
    if params.get("stage") == "live" and intent.family == "run":
        return True, "live-stage trading is not enabled in this build phase"
    if params.get("bypass_gate") == "true":
        return True, "bypassing the capability gate is permanently forbidden"
    if params.get("disable_supervisor") == "true":
        return True, "disabling the supervisor is permanently forbidden"
    return False, ""
```

Hard-NO reasons appear verbatim in `DispatchResult.rejection`. They must be specific enough
to explain to an operator why their command was permanently refused (not just "not allowed").

## Deliverables

### 1. `agents/supervisor/store.py` — add flag writes

```python
def write_flag(
    graph: GraphStore,
    *,
    subject_ref: str,
    severity: str,
    reason: str,
    status: str = "pending",
) -> Node:
    key = f"flag:{subject_ref}:{severity}"
    ...
    return graph.merge_node("Flag", key, {...})

def resolve_flag(graph: GraphStore, subject_ref: str, severity: str) -> None:
    """Mark the matching Flag node status='resolved' if it exists."""
    node = graph.get_node("Flag", f"flag:{subject_ref}:{severity}")
    if node is not None:
        graph.merge_node("Flag", node.key, {"status": "resolved"})
```

### 2. `agents/supervisor/domain/matrix.py`

Define `CAPABILITY_MATRIX: dict[str, RouteSpec]` with all 10 families per the table above.
`RouteSpec` is a frozen dataclass. No magic strings outside this file — `agent` and `capability`
fields are the canonical routing identifiers; the supervisor never assembles bus capability
strings anywhere else.

### 3. `agents/supervisor/domain/hard_no.py`

`is_hard_no(intent: TypedIntent) -> tuple[bool, str]` as specified above. Keep the file ≤ 60
lines — every condition must have a comment explaining the invariant it protects.

### 4. `agents/supervisor/domain/health.py`

```python
def compute_health(graph: GraphStore, run_id: str | None) -> dict:
    """Return raw health fields for MasterReport."""
    # Count Fault nodes with no "resolved" status → open_incidents
    # Count Flag nodes with status="pending" → pending_human_flags
    # Find most recent Snapshot node → last_successful_run (node key)
    # healthy = open_incidents == 0 and pending_human_flags with severity="critical" == 0
```

Keep ≤ 80 lines. Graceful on empty graph — return zeros and `healthy=True` when no nodes exist
(a fresh system with no history is not unhealthy).

### 5. `agents/supervisor/agent.py` — add three capabilities

Extend `SupervisorAgent` with:

**`_dispatch_intent` handler:**
1. Validate `TypedIntent` from request.
2. `is_hard_no(intent)` → if True: return `DispatchResult(accepted=False, rejection=reason)`.
3. Look up `CAPABILITY_MATRIX[intent.family]`.
4. If `spec.available is False`: return `DispatchResult(accepted=False, rejection="not available...")`.
5. If `intent.requires_confirmation` and `intent.parameters.get("confirmed") != "true"`:
   write `Flag` node; return `DispatchResult(accepted=False, rejection="confirmation required...")`.
6. If pending Flag exists for this intent: call `resolve_flag(...)`.
7. Write a `Message` node (`run_id=intent.provenance.run_id`, `step=intent.family`, `status="dispatched"`).
8. Return `DispatchResult(accepted=True, routed_to=f"{spec.agent}.{spec.capability}")`.
9. Wrap in `fault_boundary(reraise=False)`.

**`_system_status` handler:**
1. Validate `StatusRequest`.
2. Call `compute_health(graph, request.run_id)`.
3. Compose `MasterReport(healthy=..., open_incidents=..., pending_human_flags=..., last_successful_run=..., summary=Explanation(...), provenance=...)`.
4. Wrap in `fault_boundary(reraise=False)`.

**`_flag_for_human` handler:**
1. Validate `FlagRequest`.
2. Call `write_flag(graph, subject_ref=..., severity=..., reason=...)`.
3. Return `DispatchResult(accepted=True, provenance=...)`.
4. Wrap in `fault_boundary(reraise=False)`.

**`bind()` update:** register `dispatch_intent`, `system_status`, `flag_for_human` alongside
the existing two P4 capabilities.

Expected line count after additions: ~165–175 lines — warn-band but under the 200 hard block.
Add a comment `# P5 additions below` to mark the boundary for future splitting.

### 6. Tests — `agents/supervisor/tests/test_supervisor_gate.py`

Infra-free, `InProcessBus` + `InMemoryGraphStore`:

**Hard-NO tests:**
- `dispatch_intent` with `family="run", parameters={"stage": "live"}` → `accepted=False`,
  rejection contains "live-stage".
- `dispatch_intent` with `parameters={"bypass_gate": "true"}` → `accepted=False`,
  rejection contains "bypassing the capability gate".

**Capability matrix tests:**
- `family="status"` → `accepted=True`, `routed_to="reporter.report"`.
- `family="run"`, confirmed → `accepted=True`, `routed_to="orchestration.execute_run"`.
- `family="approve"` (not available) → `accepted=False`, rejection contains "P7".
- `family="stage"` (not available) → `accepted=False`, rejection contains "P8".

**Confirmation gate tests:**
- `family="run"`, `requires_confirmation=True`, no `"confirmed"` param → `accepted=False`,
  rejection contains "confirmation required"; `Flag` node written to graph.
- Same intent re-sent with `parameters={"confirmed": "true"}` → `accepted=True`; `Flag` node
  resolved in graph.
- `family="status"`, `requires_confirmation=False` → proceeds without Flag, no confirmation needed.

**System status tests:**
- Empty graph → `MasterReport(healthy=True, open_incidents=0, pending_human_flags=0)`.
- Graph with one `Fault` node → `open_incidents=1`, `healthy=False`.
- Graph with one `Flag(status="pending", severity="critical")` → `pending_human_flags=1`, `healthy=False`.
- Graph with one `Snapshot` node → `last_successful_run` is its key.

**Flag tests:**
- `flag_for_human` writes a `Flag` node with `status="pending"`.
- Calling `flag_for_human` twice with same `subject_ref` and `severity` → idempotent (one node).

### 7. P5 exit test — `agents/supervisor/tests/test_p5_exit.py`

End-to-end: `OperatorAgent` (Sprint 16) + `SupervisorAgent` (Sprint 17) on one `InProcessBus`:

```python
def test_p5_operator_to_supervisor_run_intent():
    # Wire operator + supervisor on one bus + graph
    # Call operator.interpret(HumanCommand("run the daily scan", actor="admin", channel="dashboard"))
    # Extract TypedIntent from CommandResult (outcome == "intent")
    # Call supervisor.dispatch_intent(intent)
    # Assert: DispatchResult.accepted == True, routed_to == "orchestration.execute_run"
    # Assert: CommandAudit node in graph (written by operator in Sprint 16)
    # Assert: Message node in graph with step=intent.family (written by supervisor)

def test_p5_hard_no_blocks_unconditionally():
    # Same setup
    # Interpret a command that maps to run + stage=live parameter
    # dispatch_intent → accepted=False regardless of confirmation
    # Assert no Message node written (hard-NO should not write routing record)

def test_p5_policy_parity_dashboard_vs_mcp():
    # Interpret "run the daily scan" from channel="dashboard"
    # Interpret "run the daily scan" from channel="mcp"
    # Both TypedIntents have same family, same requires_confirmation
    # Both DispatchResults have same accepted + routed_to
    # This is the policy-parity test.
```

### 8. Coverage floor

Ratchet from 100.00. All new domain files must be covered. `health.py` and `hard_no.py` are
small and must be 100% covered.

## Steps

1. Branch `sprint-17-supervisor-gate` off `sprint-16-operator` (or off `main` if Sprint 16 has
   merged — check first).
2. Read `agents/supervisor/agent.py` (current 112 lines) + `store.py` fully before touching them.
3. `store.py` — add `write_flag` + `resolve_flag`.
4. `domain/matrix.py`; `domain/hard_no.py` (≤ 60 lines); `domain/health.py` (≤ 80 lines).
5. `agent.py` — add three handlers + update `bind()`; aim for < 180 lines.
6. Unit tests (`test_supervisor_gate.py`) first; P5 exit test last.
7. Run the gate. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- `dispatch_intent` enforces hard-NO → confirmation gate → matrix, in that order.
- Hard-NO intents refused with specific reasons; confirmation gate writes + resolves Flag nodes.
- Available families (`status`, `explain`, `run`) return correct `routed_to`; unavailable families
  return `accepted=False` with a build-phase explanation.
- `system_status` returns a `MasterReport` that accurately reflects live graph state.
- `flag_for_human` writes `Flag` nodes idempotently.
- P5 exit test green: `operator.interpret` → `TypedIntent` → `supervisor.dispatch_intent` →
  `DispatchResult(accepted=True)` with `CommandAudit` + `Message` provenance in graph.
- Policy-parity test green: same command via dashboard and mcp channels yields identical
  `DispatchResult`.
- `agent.py` < 200 lines; all new domain files ≤ 80 lines; modules headered; tunables justified.
- `make ci` green at/above the coverage floor; import-linter 4/4 kept.

## Out of scope (do NOT build this sprint)

The MCP tool binding for `interpret` + `dispatch_intent` (that is the surfaces sprint, P6);
any bus call from supervisor to other agents (supervisor gates, it doesn't execute);
confirmation UX in a dashboard (P6); `Agent` graph label writes (the supervisor contract lists
`Agent` in `owns_graph` — that label is for the supervisor's own agent-registry in P6, not
needed here); `message_dead_lettered` + `fault_received` emits (wiring these on the bus is
P6 pub/sub work). Flag anything that feels needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts (confirm `agent.py` < 200, domain files ≤ 80).
- Whether the confirmation flow (Flag write → re-submit with confirmed=true → Flag resolved)
  worked cleanly, or needed a design change.
- How `compute_health` counts Fault/Flag nodes — by iterating all nodes of that label, or a
  dedicated graph query.
- P5 exit test result: CommandAudit + Message nodes confirmed in graph after the full chain.
- New coverage % and floor.

The planning agent will review, confirm P5 exit criterion met, merge to `main`, and update
`docs/STATE.md` + `docs/build-plan.md`. After this sprint, P5 is complete and P6 begins.
