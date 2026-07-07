# Architecture

This document is the engineering companion to `docs/PRD.md`. It describes how the
system is structured and why, and it is the reference for where new code goes.

## The one rule

Trading knowledge lives only in agents. **No agent imports another agent.** Agents
communicate through typed messages over a bus and share a single vocabulary of
message types. Everything else exists to make that rule safe and cheap to keep.

## Layers and dependency direction

```text
kernel/        Plumbing only. NO trading knowledge.
contracts/     Shared vocabulary: typed payloads + one AgentContract per agent.
agents/        The trading system. One package per agent, fully self-contained.
orchestration/ Dispatcher + distributed-bus app. Routes; makes no decisions.
surfaces/      Consumers, not agents: dashboard, CLI. Read the system; never drive it.
```

Dependencies flow one way: `kernel ← contracts ← agents`. Orchestration and
surfaces sit on top of all three. This is enforced by `.importlinter` in CI, with
contracts that make four guarantees:

- agents are mutually independent (`independence`);
- agents may not reach into orchestration or surfaces (`forbidden`);
- the kernel imports nothing from contracts, agents, orchestration, or surfaces;
- contracts import only the kernel — never an agent.

## Anatomy of an agent

```text
agents/<name>/
  mission.md     Human charter: mission, owns, boundary, data, external I/O, never.
  __init__.py    Package marker. Imports only kernel + contracts.
  agent.py       The handler: consume a typed request, produce a typed response.
  domain/        The agent's private logic (indicators, sizing, exit rules, ...).
  store.py       The agent's OWNED data: its graph nodes/edges (and RAG vectors).
  mcp.py         Optional: bind this agent's capabilities as tools (from the contract).
  config.py      Agent-local configuration.
  tests/
    test_contract.py  Feed a typed request; assert the typed response shape.
    test_unit.py      The agent's private logic.
```

The machine-readable boundary for each agent is `contracts/<name>.py`, which
declares its capabilities (typed request → typed response), the messages it emits,
the tables and graph labels it owns, the external systems only it may touch, the
agents it depends on (by name, reached only via messages), the capabilities it
exposes as tools, and the things it must never do.

## Contracts as the boundary

A capability is a typed request model and a typed response model. Because both
models live in `contracts/`, a downstream agent can reference an upstream agent's
output type **without importing the upstream agent's code**. For example, the
analyst's `analyze` capability declares its request as the scanner's
`CandidateSet` — a real, type-checked reference across the boundary, with zero
coupling to scanner internals.

This is the whole isolation story: the contract is the interface; the agent is the
implementation; the two never leak into each other.

## Communication

Every inter-agent message is an `AgentMessage` envelope (`kernel/envelope.py`)
carrying a serialized typed payload. The bus has two interchangeable backends:

- **In-process** — synchronous, no broker. Every unit, contract, and integration
  test uses it, so tests are fast and deterministic.
- **Distributed** — a task queue over a message broker. Each agent is a worker that
  consumes its queue and is otherwise idle. This is what makes the system
  event-driven: no message, no work — no always-on conveyor.

The contract is transport-agnostic, so the same boundary binds to the in-process
bus, the distributed bus, and the tool interface without redefinition.

## Data: one store, three jobs (PostgreSQL)

A single PostgreSQL graph spine, reached through the kernel `GraphStore` adapter,
does three jobs — see `docs/decisions/0014-postgresql-system-of-record.md`.
Neo4j remains only as an ad-hoc, out-of-bounds analysis workbench.

| Job | Holds | Ownership |
| --- | --- | --- |
| Transactional truth (ACID, append-only) | orders, positions, approvals, audits, config — as nodes | each agent owns its own node/edge labels — no shared label |
| Provenance + analysis | every artifact and message as a node; edges for derivation and routing | written by the owning agent; read widely |
| Retrieval (RAG) | embeddings/vector retrieval when built on the Postgres spine | the producing agent writes; read widely |

The provenance graph is the data-collection-and-analysis layer. A trade's full
story — `Candidate → Recommendation → OrderIntent → Fill → CloseDecision →
Outcome`, plus the message lineage that produced each step — is a graph traversal,
not a log scrape. The physical schema is the Alembic-managed `nodes`/`edges` spine;
properties stay JSONB-flexible, money is stored as integer minor units, and
append-only is enforced by the GraphStore adapter plus database constraints.

## Validated dependency graph (the process flow)

```text
provider → (root; external data + regime)
scanner → provider
analyst → scanner, provider
forecaster → provider                         (advisory / shadow only)
portfolio_manager → analyst, provider, forecaster
execution → portfolio_manager, monitor        (only broker boundary)
monitor → forecaster, execution
reporter → reads the whole provenance graph
researcher → reporter                          (proposes only, never applies)
curator → reporter                             (out-of-band dataset prep; never gates)
operator → supervisor                          (tool host bridge)
supervisor → all                               (router + capability gate + fault sink)
```

## Enforced invariants

`tests/test_boundary_map.py` reads every contract and fails CI if the design drifts:

- every capability is a typed request → typed response;
- every declared dependency names a real agent;
- **single writer per node/edge label** — no two agents own the same label;
- **exclusive external I/O** — no external system is touched by two agents;
- every agent states a mission, hard boundaries, and the data it owns.

## Deployment architecture (container-per-agent)

Each agent ships as its own Docker image with a tailored dependency group. Images are pushed to
DockerHub and run on **Azure Container Apps** (scale-to-zero per container). A **master agent**
bootstraps the fleet: it is the first container to start, the sole Azure Key Vault accessor, and the
only agent that assigns identities and distributes minimum-necessary secrets to other agents.

Agents start in a `PRE_FLIGHT` state — no identity, no capabilities, no secrets — and transition to
`ACTIVE` only after receiving a cryptographically signed `ACTIVATE` message from master. This
enforces least-privilege at the process level: a compromised container has access only to what it
was explicitly granted.

The fleet registry (live instances, session recovery state, queued messages) lives in PostgreSQL
alongside the provenance graph. See `docs/decisions/0007-container-per-agent-master-bootstrap.md` for
the full design, risk assessment, and mitigations.

> **Note:** The current `Dockerfile` and `docker-compose.yml` deploy a single monolithic container.
> That is an interim shortcut, superseded by ADR-0007. The per-agent split is tracked under P14.

## Configuration, faults, and observability

- **Configuration** — every processing/forecast constant is a justified,
  env-overridable tunable (`kernel.tunable` + `AgentSettings`), introspectable into
  a central catalogue. No bare magic numbers. See `docs/configuration.md`.
- **Faults** — every exception becomes a provenance-carrying `AgentFault`
  (`kernel.errors`) redirected to the supervisor's central channel and acted upon.
  See `docs/error-handling.md`.
- **Observability** — a kernel metrics adapter feeds Prometheus + Grafana for live
  health; the Postgres provenance graph holds the durable, exportable
  decision history. See `docs/observability.md`.

## Conventions

- **One responsibility per file, under 200 lines** (warn at 150), enforced by
  `scripts/check_module_size.py`.
- **A coding-agent header on every module** — the docstring declares `Agent:` and
  `Role:` (plus `External I/O:` where relevant), enforced by
  `scripts/check_module_header.py`, so a coding agent can read a file's purpose and
  ownership without parsing it.
- **Justify values in code** — a constant's chosen value carries its rationale via
  the mandatory `why=` on `kernel.tunable`.

## Testing model

| Scope | Lives in | Runs when |
| --- | --- | --- |
| Agent private logic | `agents/<name>/tests/test_unit.py` | that agent's internals change |
| Agent contract conformance | `agents/<name>/tests/test_contract.py` | that agent's contract or handler changes |
| Cross-agent flow | `tests/integration/` (in-process bus) | a cross-agent interaction changes |
| Boundary map | `tests/test_boundary_map.py` | any contract changes |

Changing one agent's internals runs that agent's tests, full stop. The CI
toolchain (lint, format, types, import boundaries, coverage ratchet, secret scan,
dependency audit, module-size guard) matches the conventions documented in
`docs/build-plan.md`.
