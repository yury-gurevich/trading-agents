<!-- Copy this file to agents/<name>/laws/laws.md and fill every section. -->
<!-- Author in IDEAL-DESIGN mode (intent, not code). See docs/laws/conventions.md. -->

# `<Agent>` — Laws

**Prefix:** `<XXXX>` · **status:** DRAFT v0 · **Owner:** Yury Gurevich

> One-sentence statement of this agent's single responsibility.

Each clause below has a stable ID (`<XXXX>-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- What is its *one* job? Why does it exist (what does it feed, so that what becomes possible)?
- What does it own **exclusively** (graph labels; credentials)?

## Inputs (`IN`)

- Each accepted request/message: its **type/schema**, field constraints/units, and the **provenance
  role** it expects (a type, never a named agent).
- Behaviour on malformed/invalid input.
- Inputs it must never accept or act on.

## Triggers (`TRG`)

- What invokes each capability; pull (request/response) or push (event).
- Precondition to act vs. no-op. Can it ever self-trigger? (state the answer.)

## Outputs (`OUT`)

- Each capability's **output type/schema** and destination (response / graph node / event).
- The **total output space**: success, explained rejection, degraded, fault — and the condition for
  each.
- Provenance and append-only guarantees.

## Prohibitions (`NEV`)

- The exhaustive list of what it must **never** do / touch / decide. ("Performs its function *only*.")

## State & effects (`STA`)

- Stateless between calls? Side effects (writes, bus calls, external I/O)? Append-only? Single-writer?

## Determinism & idempotency (`IDM`)

- Same input → same output? Invoking twice == once? Idempotency key? How are non-deterministic inputs
  (time, feeds, models) bounded and stamped?

## Ordering & concurrency (`ORD`)

- Does input order matter? Safe under concurrency? Behaviour on duplicate / late / out-of-order
  messages?

## Failure, recovery & rollback (`FAIL`)

- What *is* failure here (fault vs. degrade)? Partial failure — atomic? Safe to re-process/retry?
  Can effects be rolled back, or only compensated (append-only)? Recoverable after a mid-operation
  crash — how? Behaviour when a dependency is unhealthy.

## Type alignment (`TYP`)

- I/O types match the contracts it choreographs with (no drift). Units explicit (money exact, not
  lossy). Contract versioned; behaviour on version mismatch.

## Security & privilege (`SEC`)

- **Is it root/admin? (target: no.)** What is the *least* privilege it needs — is every authority
  justified by its function?
- Credentials held (and sole holder?); never logged/returned. Can it escalate? (must not.)
- **Blast radius** if compromised. Confused-deputy guard. Egress restricted to declared endpoints.
  Who may invoke it (authorization). Is it revocable / quarantinable without breaking the system?

## Dependencies (`DEP`)

- Each Layer-0 component it relies on, pointing at its `DEP-*` IDs. (These must be green first.)

## Observability & audit (`OBS`)

- Is every output reconstructable from the graph alone? What metrics/faults does it emit? Is
  degradation observable, not buried?

## Performance envelope (`PERF`)

- Timeouts on external calls. Expected latency/throughput budget.

## Capability declaration (`CAP`)

*What this agent needs from the runtime to perform its function. Describes interfaces, not products.
This section is the design-time source of truth; the EHLO payload sent to the master agent at
startup is derived from it. See `docs/decisions/0007-container-per-agent-master-bootstrap.md`.*

```json
{
  "messaging": {
    "operations": ["publish", "subscribe"],
    "delivery": "at_least_once",
    "schema_version": "1.0"
  }
}
```

- List every interface the agent needs (messaging, graph, data API, broker, …).
- For each: required operations, minimum access level, schema/protocol version.
- Never name a product ("Azure Service Bus") — describe the functional contract.

## Parameters (`PARAM`)

*Every constant used in agent code — both env-overridable tunables and hard-coded values — must be
documented here with schema, rationale, and tunable/non-tunable classification.
See `docs/decisions/0007-container-per-agent-master-bootstrap.md`.*

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `EXAMPLE_CONSTANT` | `42` | `int ≥ 1` | YES | Replace with real name, value, and rationale |

- **Tunable** — can be changed for operational experiments without altering the agent's semantic
  contract; candidate for master to expose at runtime.
- **Non-tunable** — structural constant; changing the value changes what the agent *means*.
- Every `tunable()` in `settings.py` has a `why=` kwarg; non-tunable constants must be documented
  here with equal rigour.

## Divergence register

| ID | Law says | PRD / mission / code says | Decision needed |
| --- | --- | --- | --- |
| … | … | … | confirm law / correct law |

## Changelog

- v0 — drafted (ideal-design). Not yet locked.
