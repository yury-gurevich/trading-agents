# `Supervisor` — Laws

**Prefix:** `SUP` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Route messages between agents, enforce the capability matrix and hard-NO safety surface,
> flag anomalies for human review, and produce the master health/decision report.

Each clause has a stable ID (`SUP-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **SUP-IDN-01** — The supervisor's single job is governance: validate every typed intent against
  the capability matrix, route permitted intents, block and explain refused ones, record faults,
  raise flags, and report system health. It governs flow and safety; it never decides what to
  trade.
- **SUP-IDN-02** — The supervisor exclusively writes these graph labels (single-writer rule):
  `Message`, `Agent`, `Flag`, `Fault`, `FlagResolution`.

## Inputs (`IN`)

- **SUP-IN-01** — `dispatch_intent` accepts `TypedIntent { family, parameters,
  requires_confirmation, provenance }` from the operator.
- **SUP-IN-02** — `system_status` accepts `StatusRequest { run_id: str | None }`.
- **SUP-IN-03** — `flag_for_human` accepts `FlagRequest { subject_ref, severity, reason }`.
- **SUP-IN-04** — `record_dispatch_run` accepts `DispatchRunRecord { run_id, steps_attempted,
  completed, reason, faults }`.
- **SUP-IN-05** — `report_fault` accepts `AgentFault` (redirected from any agent's fault sink).
- **SUP-IN-06** — Malformed input → `DispatchResult(accepted=False, ...)` returned; fault
  recorded; never raises to bus.

## Triggers (`TRG`)

- **SUP-TRG-01** — `dispatch_intent` triggered by RPC from the operator (via surfaces).
- **SUP-TRG-02** — `system_status` triggered by RPC from the CLI surface or MCP tool.
- **SUP-TRG-03** — `flag_for_human` triggered by RPC from any agent that detects an anomaly.
- **SUP-TRG-04** — `record_dispatch_run` triggered by the dispatcher at the end of each run.
- **SUP-TRG-05** — `report_fault` triggered by the fault sink infrastructure when an agent
  redirects a fault to the supervisor.
- **SUP-TRG-06** — No event subscription; the supervisor never self-triggers.

## Outputs (`OUT`)

- **SUP-OUT-01** — `dispatch_intent` returns `DispatchResult { accepted, routed_to, rejection,
  provenance }`.
- **SUP-OUT-02** — `system_status` returns `MasterReport { healthy, open_incidents,
  pending_human_flags, last_successful_run, summary, provenance }`.
- **SUP-OUT-03** — `flag_for_human` returns `DispatchResult`; a `Flag` graph node is written.
- **SUP-OUT-04** — `record_dispatch_run` returns `DispatchResult`; a `Message`-lineage node is
  written for each step.
- **SUP-OUT-05** — `report_fault` returns `DispatchResult`; a `Fault` graph node is written.
- **SUP-OUT-06** — Every refused `dispatch_intent` is explained via `DispatchResult.rejection`;
  never silent.

## Prohibitions (`NEV`)

- **SUP-NEV-01** — Never makes a domain trading decision. The supervisor routes and governs; it
  has no write path to OrderIntent, Recommendation, or CloseDecision.
- **SUP-NEV-02** — Never enables a hard-NO capability, even if explicitly asked. Hard-NO intents
  are blocked by the capability matrix; no override path exists.
- **SUP-NEV-03** — Never routes a capability to a caller the matrix forbids.
- **SUP-NEV-04** — Never swallows a fault. Every `report_fault` call writes a `Fault` node; every
  `record_dispatch_run` call with faults persists them.

## State & effects (`STA`)

- **SUP-STA-01** — Stateless between calls. All system-state knowledge comes from the graph;
  no in-memory health cache between `system_status` calls.
- **SUP-STA-02** — All graph writes are append-only. `Flag`, `Fault`, and `Message` nodes
  accumulate; none are overwritten.

## Determinism & idempotency (`IDM`)

- **SUP-IDM-01** — `system_status` is deterministic given the same graph state at call time.
  Re-invoking returns the same `MasterReport` if no graph changes have occurred.
- **SUP-IDM-02** — `dispatch_intent`, `flag_for_human`, `record_dispatch_run`, and
  `report_fault` are not idempotent: each invocation writes a new graph node.

## Ordering & concurrency (`ORD`)

- **SUP-ORD-01** — `dispatch_intent` calls are independent; no ordering dependency.
- **SUP-ORD-02** — Concurrent `flag_for_human` calls are safe; each writes an independent `Flag`
  node. No deduplication of flags at the supervisor level.

## Failure, recovery & rollback (`FAIL`)

- **SUP-FAIL-01** — `dispatch_intent` internal error: `fault_boundary` captures; `rejected()`
  result returned; fault emitted. The intent is not dispatched.
- **SUP-FAIL-02** — `system_status` traversal failure: `failed_health()` returned with
  `healthy=False`; fault emitted.
- **SUP-FAIL-03** — `record_dispatch_run` graph write failure: `rejected()` returned; fault
  emitted. The run record is not preserved but the pipeline continues.
- **SUP-FAIL-04** — `report_fault` write failure: a second `DispatchResult(accepted=False)`
  is returned; fault is emitted to the sink (distinct from the original fault being reported).

## Type alignment (`TYP`)

- **SUP-TYP-01** — `DispatchResult`, `MasterReport`, `TypedIntent`, and `FlagRequest` match
  `contracts/supervisor.py` exactly.
- **SUP-TYP-02** — `DispatchResult.accepted: bool` is always present; never None.
- **SUP-TYP-03** — `MasterReport.healthy: bool` is derived from the graph health check; a
  graph traversal failure always yields `healthy=False`.

## Security & privilege (`SEC`)

- **SUP-SEC-01** — Holds no credentials. The supervisor enforces the capability matrix but
  holds no keys to act on intents directly.
- **SUP-SEC-02** — Capability matrix is a hard-coded policy, not a runtime-configurable table.
  It cannot be modified without a code change and a new CI gate pass.
- **SUP-SEC-03** — `max_fault_message_chars=500` bounds the fault message stored in the graph;
  prevents unbounded data from an untrusted agent fault from bloating the graph.
- **SUP-SEC-04** — Revocable without breaking the system; if the supervisor is down, faults are
  collected locally by each agent's sink and trading continues.

## Dependencies (`DEP`)

- **SUP-DEP-01** — `DEP-POSTGRES` — graph for `Flag`, `Fault`, `Message`, `FlagResolution` writes
  and health-check traversal.
- **SUP-DEP-02** — `DEP-BUS` — receives RPC from operator and dispatcher; routes permitted
  intents to target agents.

## Observability & audit (`OBS`)

- **SUP-OBS-01** — Every `dispatch_intent` call writes a node; the routing decision (accepted /
  refused + reason) is reconstructable from the graph.
- **SUP-OBS-02** — `Flag` nodes are the alert queue for the human-review surface; `open_incidents`
  and `pending_human_flags` in `MasterReport` are derived from them.
- **SUP-OBS-03** — `Fault` nodes from `report_fault` are the canonical fault log; queryable via
  the CLI `incidents` command.

## Performance envelope (`PERF`)

- **SUP-PERF-01** — `max_fault_message_chars=500` keeps `Fault` nodes compact and health-check
  traversals fast.
- **SUP-PERF-02** — The supervisor holds no open connections between calls.

## Capability declaration (`CAP`)

```json
{
  "messaging": {
    "operations": ["register", "request"],
    "role": "router"
  },
  "graph": {
    "operations": ["append_write", "read"],
    "labels_owned": ["Message", "Agent", "Flag", "Fault", "FlagResolution"],
    "labels_read": ["all"]
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `max_fault_message_chars` | `500` | `int ≥ 80 ≤ 2000` | YES | Fault nodes stay scannable; enough text for triage |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| — | — | — | no known drift |

## Changelog

- v1 — authored S71 and locked immediately (full first-principles cycle).
