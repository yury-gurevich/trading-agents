# `Deliberator` -- Laws

**Prefix:** `DLIB` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Adversarially review PM-approved orders with a bounded proponent/opponent debate
> and a manager verdict before execution, subtracting unsafe orders only when the
> recorded verdict says so.

Each clause has a stable ID (`DLIB-CAT-NN`). IDs are append-only (conventions §2).
A clause is green only when a functional test cites its ID (conventions §3). Tests
+ status live in `test-plan.md`. S153 declares this capability from DL-80 and
ADR-0020; declaring is not proving, so every clause starts gray.

## Identity & Purpose (`IDN`)

- **DLIB-IDN-01** -- The deliberator's single job is adversarial review of
  PM-approved live orders between portfolio management and execution.
- **DLIB-IDN-02** -- The deliberator writes `DeliberationRun` as its owned graph
  label and may write shared substrate `LLMCall` audit nodes under ADR-0020.
- **DLIB-IDN-03** -- The deliberator is one image with three bounded identities:
  `deliberator-manager`, `deliberator-proponent`, and `deliberator-opponent`.

## Inputs (`IN`)

- **DLIB-IN-01** -- The manager accepts `PMRun` graph nodes carrying an
  `OrderIntentSet`.
- **DLIB-IN-02** -- Peers accept `DebateTurnRequest` payloads only from
  `deliberator-manager`.
- **DLIB-IN-03** -- The manager verdict path accepts `VerdictRequest` payloads
  only from `deliberator-manager`.
- **DLIB-IN-04** -- Malformed input records a fault and never produces an
  execution-stage mutation.

## Triggers (`TRG`)

- **DLIB-TRG-01** -- The manager is graph-pull: it processes `PMRun` nodes with
  no outgoing `DELIBERATED_BY` edge.
- **DLIB-TRG-02** -- The proponent and opponent are served request/reply
  instances.
- **DLIB-TRG-03** -- The deliberator never self-triggers and never polls external
  feeds.

## Outputs (`OUT`)

- **DLIB-OUT-01** -- Each processed `PMRun` gets exactly one append-only
  `DeliberationRun` linked by `PMRun -DELIBERATED_BY-> DeliberationRun`.
- **DLIB-OUT-02** -- Each `DeliberationRun` records verdicts, vetoed tickers,
  per-ticker debate turns, role models, narrative, and creation time.
- **DLIB-OUT-03** -- Each LLM call writes a shared `LLMCall` with
  `calling_agent`, model, hashes, rough token counts, latency, and timestamp.
- **DLIB-OUT-04** -- Non-uphold verdicts may only subtract existing PM-approved
  orders; uphold verdicts leave the order set unchanged.

## Prohibitions (`NEV`)

- **DLIB-NEV-01** -- Never originates an order.
- **DLIB-NEV-02** -- Never resizes an order.
- **DLIB-NEV-03** -- Never talks to the broker.
- **DLIB-NEV-04** -- Never fetches market data directly.
- **DLIB-NEV-05** -- Never imports another agent or `orchestration`.
- **DLIB-NEV-06** -- Never hides a failed debate or peer call as a clean veto.

## State & Effects (`STA`)

- **DLIB-STA-01** -- The manager is stateless between polls; graph state is the
  source of work truth.
- **DLIB-STA-02** -- Graph effects are append-only and idempotent by PM run id.
- **DLIB-STA-03** -- Peer instances write only their shared `LLMCall` audit node
  for a served turn.

## Determinism & Idempotency (`IDM`)

- **DLIB-IDM-01** -- Re-processing an already-deliberated `PMRun` is a no-op.
- **DLIB-IDM-02** -- LLM outputs are non-deterministic but bounded by role,
  model, max rounds, prompt hashes, response hashes, and timestamps.
- **DLIB-IDM-03** -- Manager writes use the PM run id as the deliberation id.

## Ordering & Concurrency (`ORD`)

- **DLIB-ORD-01** -- Within an order, the manager asks defender then challenger
  each round, preserving the running transcript.
- **DLIB-ORD-02** -- Independent `PMRun` nodes may be processed independently.
- **DLIB-ORD-03** -- Duplicate peer replies are ignored by idempotent manager
  write semantics.

## Failure, Recovery & Rollback (`FAIL`)

- **DLIB-FAIL-01** -- Any LLM or peer-call failure is fail-open for the affected
  order and records an uphold verdict with a failure rationale.
- **DLIB-FAIL-02** -- A graph-write failure records a fault; no compensating
  delete is attempted.
- **DLIB-FAIL-03** -- After a crash, the manager retries any `PMRun` that still
  lacks a `DELIBERATED_BY` edge.

## Type Alignment (`TYP`)

- **DLIB-TYP-01** -- Bus payloads match `contracts/deliberator.py` exactly.
- **DLIB-TYP-02** -- PM input is validated as `contracts.portfolio_manager.OrderIntentSet`.
- **DLIB-TYP-03** -- Verdict rulings are limited to `uphold`, `overturn`, or
  `revise`.

## Security & Privilege (`SEC`)

- **DLIB-SEC-01** -- Holds only its scoped graph, bus, and LLM credentials.
- **DLIB-SEC-02** -- The Anthropic API key is never logged, stored in graph props,
  or returned in bus responses.
- **DLIB-SEC-03** -- Peer capabilities accept only `deliberator-manager`.
- **DLIB-SEC-04** -- Revoking the deliberator must leave trading fail-open rather
  than broker-blocked.

## Dependencies (`DEP`)

- **DLIB-DEP-01** -- `DEP-POSTGRES` for reading PM lineage and writing audit
  graph nodes.
- **DLIB-DEP-02** -- `DEP-BUS` for manager-to-peer request/reply.
- **DLIB-DEP-03** -- `DEP-LLM` for external model calls and fail-open behaviour.
- **DLIB-DEP-04** -- `DEP-CONFIG` for role, round, model, and credential settings.

## Observability & Audit (`OBS`)

- **DLIB-OBS-01** -- The debate narrative and transcript are reconstructable from
  `DeliberationRun` alone.
- **DLIB-OBS-02** -- LLM spend is attributable per calling agent through
  `LLMCall.calling_agent`.
- **DLIB-OBS-03** -- Fail-open outcomes are visible in the recorded rationale.

## Performance Envelope (`PERF`)

- **DLIB-PERF-01** -- `max_rounds` bounds peer turns before execution.
- **DLIB-PERF-02** -- Peer wait time is bounded by `request_timeout_seconds`.

## Capability Declaration (`CAP`)

```json
{
  "graph": {
    "operations": ["append_write", "read"],
    "labels_owned": ["DeliberationRun"],
    "labels_shared": ["LLMCall"],
    "labels_read": ["PMRun"]
  },
  "messaging": {
    "operations": ["request", "serve"],
    "peers": ["deliberator-manager", "deliberator-proponent", "deliberator-opponent"]
  },
  "llm": {
    "operations": ["complete"],
    "audit_label": "LLMCall"
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `role` | `manager` | enum | YES | Selects one of the three image identities |
| `instance_name` | empty | string | YES | Allows an explicit fleet app identity |
| `max_rounds` | `2` | int >= 1 <= 5 | YES | More than one live round while bounded |
| `defender_model` | `claude-opus-5` | string | YES | Proponent role model |
| `challenger_model` | `claude-opus-5` | string | YES | Opponent role model |
| `judge_model` | `claude-opus-5` | string | YES | Manager verdict model |
| `effort` | `max` | enum | YES | Anthropic reasoning effort |
| `max_tokens` | `4096` | int >= 64 <= 4096 | YES | Per-call response cap |
| `request_timeout_seconds` | `30.0` | float >= 1 <= 120 | YES | Bounds peer RPC wait |
| `poll_interval_seconds` | `60` | int >= 1 <= 300 | YES | Bounds manager idle polling |
| `proponent_identity` | `deliberator-proponent` | string | YES | Manager peer target |
| `opponent_identity` | `deliberator-opponent` | string | YES | Manager peer target |

## Divergence Register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| -- | -- | -- | no known drift |

## Changelog

- v1 -- S153 created from `docs/laws/_TEMPLATE.md`, declaring the DL-80/ADR-0020
  deliberator capability. All clauses start gray.
