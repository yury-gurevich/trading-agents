# Product Requirements

**Product:** An operator-controlled, single-user, self-managed stock-trading
system built as a set of self-contained agents that communicate through typed
messages.
**Status:** Active — foundational (boundary map defined; runtime being built).
**Product owner:** Yury Gurevich.

---

## 1. Executive summary

This is a single-user, self-managed stock-trading application designed to do one
narrow job extremely well: help one operator run a disciplined trading process
with strong automation, full visibility, local control, and minimal day-to-day
friction.

The system must feel quiet, trustworthy, and under control. It talks to the user
as little as possible and exposes state, decisions, risks, and exceptions through
controlled channels rather than constant conversation.

It starts with US equities and an S&P 500 universe because trust is earned on a
narrow universe before it is widened. The architecture must allow broader US
equities and then additional exchange packs without rewriting the control plane.

What makes this system distinct is **how it is built**: every responsibility lives
inside an independent agent with a published mission and a typed contract. Agents
never reach into one another; they exchange messages over a bus and record their
work as provenance. A change to one agent is testable in isolation, and the flow
of the whole system is readable from the contracts alone.

The operator command layer is an agent like any other. It is not a chatty
companion: it translates a small, bounded set of human requests into typed,
policy-checked actions, explains what the system did in plain language grounded in
stored evidence, and refuses anything ambiguous or unsafe.

The operator has only two meaningful product surfaces:

1. **Dashboard** — the high-visibility forensic and manual-control surface.
2. **Phone app** — the eventual primary daily interface, introduced only after
   trust is earned.

Everything else is infrastructure, not product surface.

---

## 2. Product thesis

Build a local-first, single-user trading application that manages itself
conservatively, recovers safely, explains itself clearly, and eventually accepts
well-formed human instructions in everyday language through a tightly controlled
command channel.

The product wins if it simultaneously:

- runs mostly on its own without becoming opaque;
- makes conservative decisions and exposes why they happened;
- fails loudly when trust would otherwise be damaged;
- gives the operator only the controls that matter, through bounded surfaces;
- keeps meaning local — command interpretation, risk policy, and execution
  validation stay under the operator's control;
- expands market scope only after the original control loop is trustworthy.

---

## 3. Non-negotiable principles

1. **Single-user first.** One operator. Not a team platform, not multi-tenant,
   not a social product.
2. **Quiet by default.** Silence is the healthy state. The system does not
   narrate itself or demand attention.
3. **Controlled channels only.** Interaction happens through bounded artifacts:
   approval cards, alerts, summaries, evidence views, and typed commands.
4. **Local control of meaning.** Command interpretation, operating mode,
   execution stage, and decision validation stay locally controlled, auditable,
   and reversible.
5. **Evidence before automation.** A capability may run automatically only after
   the system can explain it, measure it, and roll it back.
6. **Agent-native.** Every responsibility is an independent agent with a published
   mission and a typed contract. Agents communicate only through messages.
7. **Deterministic by default.** Prefer code, simulation, statistics, and rules.
   Reach for a language model only where verbal reasoning is the actual value, and
   keep ML advisory until measured scorecards earn promotion.
8. **Acquisition-grade traceability.** Build the audit surface as if the system
   could be acquired tomorrow: append-only history, user actions audited, silence
   that filters but never erases, exportable evidence bundles.
9. **Expansion is architectural, not ad hoc.** New markets arrive through
   market-pack abstractions, never code forks.
10. **Local first.** Cloud is a scaling path taken after local limits are reached,
    not a starting requirement.

---

## 4. Architecture principles

The architecture is a product requirement, not an implementation detail — it is
what makes the system trustworthy, explainable, and changeable one piece at a time.

### 4.1 Three tiers, one rule

- **Agents** hold all domain knowledge. Each owns its logic, its data, its tests,
  and its contract.
- **Kernel** is pure plumbing shared by every agent: the message envelope, the bus,
  contract descriptors, persistence and graph adapters, observability, and the MCP
  binding. It contains no trading knowledge.
- **Contracts** are the shared vocabulary — typed message payloads and one contract
  per agent. Agents import message types from here, never from each other.

**The one rule:** an agent may depend on the kernel and the shared contracts and
nothing else in the system. No agent imports another agent. This is enforced
mechanically in continuous integration, so the boundary cannot quietly erode.

### 4.2 Agent-to-agent communication

Every inter-agent message is a typed envelope carrying a typed payload. The bus
has two interchangeable backends:

- an in-process backend used by every unit and contract test (deterministic, no
  broker), and
- a distributed backend (a task queue with a message broker) used by the running
  system, where an agent is a worker that consumes its queue and is otherwise idle.

Because the contract is transport-agnostic, the same boundary is bound to the
in-process bus, the distributed bus, and the operator's tool interface without
duplicating definitions.

### 4.3 Two databases, two jobs

- **Relational store — transactional truth.** Orders, positions, approvals, and
  audits live in a relational database with ACID guarantees and append-only
  semantics. Each agent owns its own tables; there is no shared schema that every
  agent writes.
- **Graph store — provenance and analysis.** Every artifact and every message is a
  node in a provenance graph; edges record derivation
  (candidate → recommendation → order → fill → outcome) and message lineage. This
  is the data-collection-and-analysis layer and the substrate for explanation,
  audit, and research.

### 4.4 Tool interface

Each agent's capabilities can be exposed as tools to an external model context
through the kernel's binding, generated from the same contract that drives the
internal bus. The operator command agent is the bounded host that lets an external
model drive the system through the allowed command grammar; other agents opt in.

### 4.5 Configuration and constants governance

Every value that influences processing or a forecast is a justified, env-overridable
tunable, never a bare literal. Each is declared with a mandatory rationale and safe
bounds, namespaced per agent, and introspectable into a central catalogue the
operator can see and control. Secrets are provided out-of-band and read only by the
owning agent. Details: `docs/configuration.md`.

### 4.6 Fault handling

Errors are never merely logged where they occur. Every exception is captured as a
fault carrying its origin — which agent and module produced it — redirected to one
central channel, and acted upon by the supervisor (the central agent for faults),
which opens incidents, flags for human review, or retries. Faults are append-only
in the relational store and the provenance graph. Details: `docs/error-handling.md`.

### 4.7 Observability and historical data

The system is loud inward, quiet outward. Live metrics and traces flow through a
kernel adapter to Prometheus and are visualized in Grafana (system health, agent
throughput and latency, fault rates, trust indicators). The durable record of what
the system did and why lives in the provenance graph (Neo4j) and the append-only
relational store, queryable and exportable for any date range. Grafana is an
internal forensic surface beside — not replacing — the product dashboard. Details:
`docs/observability.md`.

### 4.8 Out-of-band data engineering

Data preparation for later LLM training is a separate concern from trading. The
curator agent reads the collected provenance graph and produces clean, labelled,
versioned datasets, running alongside the trading loop and never gating a decision.

---

## 5. The agents

Each agent has a full charter in `agents/<name>/mission.md` and a machine-readable
boundary in `contracts/<name>.py`.

| Agent | Mission (one line) | Owns the boundary to |
| --- | --- | --- |
| **provider** | Single boundary to external market data + regime; turns raw feeds into clean, cached facts. | all market-data APIs |
| **scanner** | Reduce the universe to a ranked candidate set, explaining every filter. | — |
| **analyst** | Turn candidates into scored, evidence-backed recommendations. | — |
| **forecaster** | Advisory shadow-ML signals, never binding until scorecards earn it. | — |
| **portfolio_manager** | Decide which recommendations become sized, risk-checked orders. | — |
| **execution** | The single idempotent broker boundary: submit, fill, reconcile, stage-gate. | the broker |
| **monitor** | Watch open positions, decide exits, explain every hold and close. | — |
| **reporter** | Stitch runs and trades into durable narrative + metrics. | — |
| **researcher** | Propose bounded, measurable parameter changes — never apply them. | — |
| **curator** | Curate collected graph data into versioned datasets for later LLM training, out of band. | the dataset store |
| **operator** | Translate operator language into typed, policy-bound intents; explain state. | the language model |
| **supervisor** | Route messages, enforce the capability matrix, flag for human, master report. | — |

Two invariants hold across the roster and are enforced as tests:

- **single writer per table** — no shared schema; every table has one owning agent;
- **exclusive external I/O** — exactly one agent holds the credentials and code path
  to each external system (data APIs → provider, broker → execution, model → operator).

### 5.1 Capability safety surface

The supervisor enforces a capability matrix: which agents may invoke which
capabilities, and a hard-NO set of capabilities that may never be enabled at all
(for example: committing code, approving a trade without the operator, bypassing
the approval queue, mutating the capability matrix at runtime, or disabling audit).

---

## 6. Product surfaces and contact model

### 6.1 Surfaces

| Surface | Purpose | Allowed actions | Must not become |
| --- | --- | --- | --- |
| Dashboard | Full visibility, forensics, trust-building, manual runs | Inspect every run and trade, approve/reject/modify, change mode/stage, run diagnostics, read reports | A noisy general chat UI |
| Phone app | Fast daily control with concise status and safe commands | Approvals, pause/resume, concise explanations, mode toggles, urgent alerts | A replacement for deep investigation |

### 6.2 Notifications are transport, not a surface

Notifications exist only to bring the operator back to a surface. Notify for
forced-manual, approval-expiry risk, pipeline failure, severe incident, or
stage/policy escalation. Never notify for routine healthy runs. Group low-urgency
information into scheduled summaries.

### 6.3 Dashboard requirements

The dashboard is the truth surface. It must expose pipeline status and run history;
recommendation evidence and rejection reasons; the approval queue and execution
review; position lifecycle and post-trade narrative; shadow-ML status and
scorecards; control-plane state (operating mode, execution stage, forced-manual
reason); incident, recovery, and dependency-health views; an always-visible active
incidents pane; and manual run triggers with operator-safe recovery actions. It
must never hide a material decision behind logs alone.

### 6.4 Phone app requirements

Intentionally narrow: a compact daily status view, pending approvals and urgent
exceptions, pause/resume/switch-to-manual controls, one-step access to "why did
this happen" summaries, safe command entry, and bounded report views. It must not
ship full admin workflows or observability trees — those stay in the dashboard.

---

## 7. Operator command layer

The operator agent is the command-and-validation layer. It exists to make the
system easier to control without making it less safe.

**Responsibilities:** translate approved human-language commands into typed
intents; produce concise explanations grounded in stored evidence; validate intent
against policy and current state; refuse or escalate ambiguous or unsafe requests;
help summarize incidents and unusual outcomes.

**Hard boundaries.** The operator agent must not invent trades outside the policy
and data path; bypass approval or stage gates; submit broker actions directly;
mutate strategy parameters outside the approval and audit flow; or become a
free-form conversational trading advisor.

**Requirements.**

- **CMD-01** Provider-neutral command processing (hosted default, local interface).
- **CMD-02** A defined intent grammar — only a named command set may execute.
- **CMD-03** A validated typed schema for every accepted command.
- **CMD-04** Safe failure on ambiguity — refuse or ask one bounded clarification.
- **CMD-05** Evidence-grounded explanations that cite stored decision evidence.
- **CMD-06** Explicit confirmation for mode changes, stage changes, approvals, runs.
- **CMD-07** A durable audit per accepted command (raw request, parsed intent,
  validation result, actor, outcome) plus a call ledger for every model call.
- **CMD-08** Policy parity — a command issued here obeys the same rules as one from
  the dashboard.

**Initial command families** (kept small): `status`, `explain`, `approve` /
`reject` / `modify`, `run`, `mode`, `stage`, `pause` / `resume`. Anything beyond
this must be added to the grammar explicitly.

---

## 8. Core capability requirements

### 8.1 Trading engine and execution

Start with US equities and an S&P 500 universe. Preserve paper-first foundations
and staged promotion through paper, broker-shadow, live-manual, and live-autopilot.
Keep shadow ML advisory until scorecards earn promotion. Support multiple
portfolios for one operator with explicit, auditable policy boundaries.

### 8.2 Control plane

Persist requested and effective operating mode and execution stage. Support
forced-manual behavior when observability or policy demands it. Keep the approval
lifecycle durable, inspectable, and reversible. Ensure broker submission is
idempotent before live-adjacent stages become normal. Make stage promotion and
demotion evidence-based, and keep every transition attributable to a user, policy,
or recovery action.

### 8.3 Observability and trust

Every recommendation and every non-action must be explainable (why no
recommendation, no entry, no exit, no promotion). Every incident and recovery must
be durably visible. Every trade must have a stitched narrative from scan to exit.
Advisory ML must publish operator-facing scorecards before influencing hard
decisions. Prefer concise summaries over raw logs, with deeper drill-down in the
dashboard. Every surfaced artifact carries an explain-on-demand affordance that
invokes the operator agent to produce a plain-language explanation. The
user-facing voice is reassuring and explanatory, framing disruptions as technical
incidents outside the operator's control, with safety-critical reassurance copy
hard-coded rather than model-generated, and always offering dismissal. Live system health is exposed
through an internal Prometheus + Grafana stack, while the durable decision history
lives in the provenance graph and the relational store, queryable and exportable
for any date range (see `docs/observability.md`).

### 8.4 Self-management

Keep deterministic self-improvement as the first layer. Route parameter changes
through a human-review queue. Prevent cumulative drift and forbidden parameter
combinations. Require a measurable evidence window before any strategy adjustment
is promoted. Self-management is a controlled subsystem (the researcher proposes;
the operator approves), never a hidden optimizer.

### 8.5 Market and exchange expansion

Separate market-universe selection from core trading logic; separate exchange
calendars from agent orchestration; allow provider mapping and risk/execution
policy by market pack; require a trust pass on each new pack. Desired sequence:
S&P 500 pack → broader US-equity pack → additional exchange packs.

---

## 9. Data, provenance, and audit

- **Append-only history.** Incidents, diagnostics, approvals, stage transitions,
  command audits, narrations, and parameter-change queues are append-only. State
  transitions are new rows or new fields, never destructive overwrites. Deletion is
  not a supported operation on audit-bearing tables.
- **User actions are audited, not just persisted.** Dismissing a card, silencing a
  tag, confirming a high-risk intent, or accepting a parameter change each produces
  a timestamped, user-attributed audit row.
- **Silence does not erase.** Dismissal and silence are display filters only; the
  underlying records persist in full fidelity.
- **Provenance travels.** Every decision produced during a degraded-dependency
  window carries a pointer to the open incident; the provenance graph answers "what
  did this rely on?" deterministically.
- **Exportable bundle.** The audit surface is exportable as a machine-parseable
  bundle for any date range, with a declared schema.
- **No silent retention.** Retention windows, if any, are declared in configuration
  and produce their own audit rows when they trim.

---

## 10. Success measures

| ID | Goal | Measure |
| --- | --- | --- |
| G1 | Trustworthy autonomy | ≥95% of scheduled cycles complete without silent failure over a rolling 30 days |
| G2 | Explainable silence | 100% of "no trade / no action" outcomes answerable from controlled surfaces without reading raw logs |
| G3 | Quiet operations | After stabilization, intervention needed on fewer than 20% of healthy trading days |
| G4 | Safe command control | ≥95% of accepted commands map to correct intent with 0 unsafe bypasses |
| G5 | Controlled execution | All live-adjacent actions are stage-gated, idempotent, reversible, auditable |
| G6 | Change isolation | A change to one agent is validated by that agent's tests plus the contract suite, without touching others; a new market pack adds no core-control-plane changes |

---

## 11. Maturity and progress framework

| Level | Meaning |
| --- | --- |
| 0 | Not started |
| 1 | Foundations exist in code |
| 2 | Observable and testable |
| 3 | Trustworthy under operator scrutiny |
| 4 | Controlled autonomy |
| 5 | Expandable and stable |

Per-agent and per-capability maturity is tracked in the build plan
(`docs/build-plan.md`), refreshed at each closeout against this rubric.

---

## 12. Product roadmap

The engineering sequencing lives in `docs/build-plan.md`. The product phases are:

- **Phase A — Trust foundation.** Market-data reliability, fail-loud scheduling and
  recovery, why-no-action visibility, trade-lifecycle narrative, shadow-forecast
  proof loop, broker idempotency and audited stage transitions.
- **Phase B — Quiet command layer.** Operator command grammar, typed intent schemas,
  command audit and rehearsal, evidence-grounded explanations, dashboard parity for
  every command outcome.
- **Phase C — Phone-first operator control.** Mobile/PWA approvals and status,
  concise daily brief and exception digest, safe pause/resume/mode changes, one-tap
  "why" summaries, strict notification budget.
- **Phase D — Market-pack expansion.** Formal market-pack and exchange-calendar
  abstractions, provider configuration by market, market-specific policy overlays,
  a readiness checklist per pack.

---

## 13. Non-goals

Out of scope unless explicitly reopened: multi-user accounts; social or
collaborative trading; a chat-first assistant experience; uncontrolled free-form
broker actions; options, crypto, or broad derivatives in the first trust-building
wave; expansion to many exchanges before the original loop is trustworthy; and
cloud-first operation as a product requirement.
