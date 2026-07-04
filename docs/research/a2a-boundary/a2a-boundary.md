# Research: A2A (Agent2Agent) — interop standard, adopted at the boundary only

**Status:** Research complete · **Date:** 2026-07-04 · **Author:** Claude (planning agent)
**Audience:** Product owner, planning agents, coding agents
**Source:** [a2aproject on GitHub](https://github.com/a2aproject/) ·
[Linux Foundation press, first-year adoption](https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year)

---

## TL;DR

A2A is the Google-originated, Linux-Foundation-governed open protocol for agent↔agent
interoperability across vendors and frameworks (HTTP + JSON-RPC 2.0 + SSE; Agent Cards for
discovery; a task lifecycle; v1.0 production-grade since early 2026, v1.2 adds signed Agent
Cards; 150+ organizations in production including Microsoft, AWS, Salesforce, SAP, ServiceNow).

**Verdict: do not adopt internally — ever, on current architecture. Adopt at the boundary when
an external agent appears.** This platform independently converged on A2A's principles (opaque
agents, declared capabilities, task lifecycle, message-only communication) with *stronger*
enforcement than the spec asks. Internal adoption would trade compile-time typed contracts and
brokered-bus guarantees for runtime negotiation and peer-to-peer HTTP — a strict downgrade
inside one codebase. The right integration is an **A2A front door at the surfaces layer**,
exactly parallel to the existing MCP surface: MCP covers agent↔tool, A2A covers agent↔agent.
No trigger has fired yet, so nothing is built.

---

## What A2A is

| Concept | Spec meaning |
| --- | --- |
| Agent Card | JSON capability/auth declaration at a well-known URL; cryptographically signed since v1.2 |
| Task | Stateful unit of work: submitted → working → input-required → completed / canceled / failed |
| Message / Parts | Text, file, and structured-data parts; modality negotiated at runtime |
| Artifact | Task output, streamed via SSE or delivered by push notification |
| Transport | HTTP(S) + JSON-RPC 2.0 + Server-Sent Events; standard web auth (OAuth2/OIDC/API keys) declared in the card |
| Governance | Contributed to the Linux Foundation 2025-06; Apache 2.0; v1.0 early 2026 |

A2A **complements MCP** rather than competing with it: MCP standardizes an agent calling tools;
A2A standardizes agents delegating work to each other while staying opaque.

## Scorecard — this platform vs A2A best practice

**Convergent (independently arrived at, enforced harder than the spec):**

| A2A best practice | This platform's equivalent | Enforcement |
| --- | --- | --- |
| Opaque agents, no shared internals | Agents are islands; typed messages only | import-linter (CI-fatal) |
| Declared capabilities (Agent Card) | CAPABILITY DECLARATION in law files; `owns_graph` in contracts; master-issued `CapabilityGrant` | boundary meta-test + supervisor gate |
| Task lifecycle | RunRequest → graph-pull spine (DL-08) with per-transition provenance nodes | graph, auditable end-to-end |
| Declared auth per agent | DL-36 arc: tested credentials, min-privilege handover, fail-closed vault seeding | live-checked (S104–S108) |

**Divergent (deliberate; defensible for a closed fleet):**

| Axis | A2A | Here | Why ours is right internally |
| --- | --- | --- | --- |
| Transport | Peer-to-peer HTTP/JSON-RPC/SSE | Brokered bus (Azure Service Bus, ADR-0005) + claim-check | Delivery guarantees, backpressure, replay |
| Discovery | Self-published Agent Cards | Master assigns identity + capabilities at ACTIVATE | Auditable, no trust-establishment problem in a fleet we define |
| Schemas | Runtime content negotiation | Compile-time Pydantic contracts | mypy + tests catch drift before deploy |

## Where A2A enters this platform

**The boundary, as a surface.** When an external agent must interact with the fleet (a client's
agent submitting a run request; a third-party agent consuming reports), build an **A2A server
adapter in `surfaces/`** exposing the operator agent: a signed Agent Card declaring the
operator-facing capabilities, A2A task lifecycle mapped onto RunRequest lineage, artifacts
mapped onto reporter outputs. Internals unchanged — same pattern as `surfaces/mcp_server`.
Per ADR-0012 this is a **substrate surface** concern (domain-agnostic, sellable with any pack).

## What NOT to do

| Option | Why not |
| --- | --- |
| Adopt A2A as the internal bus | Loses typed contracts, broker guarantees, boundary enforcement; solves interop we don't need between agents we own |
| Replace master ACTIVATE with Agent-Card discovery | Dynamic discovery solves an open-world trust problem; ours is a closed world with a stronger (granted, audited) model |
| Build the front door now | No external agent exists; unexercised integration code rots; violates etalon-first (DL-19) |

## Revisit triggers

1. **A concrete external-agent integration request** — a real counterparty wanting to submit
   work or consume outputs agent-to-agent. → Build the surfaces adapter (research → sprint).
2. **The multi-org scaling intent becomes concrete** (platform sold/operated across
   organizations) — A2A is then the expected lingua franca; the front door becomes a product
   feature, not plumbing.
3. **MCP↔A2A convergence** — if the two specs merge or bridge officially, re-evaluate whether
   one surface covers both directions.

Until a trigger fires, this question is **closed** — cite this document instead of re-deriving.

## Relation to existing decisions

- **ADR-0012 (substrate/pack wall):** the A2A adapter is substrate surface; Agent Card content
  per deployment is pack/operator configuration.
- **DL-38 (memory in the agent definition):** unaffected — A2A says nothing about storage;
  opaque memory is exactly what both designs assume.
- **ADR-0005 (Service Bus):** unchanged; A2A never replaces the internal bus.
- **MCP surface (`surfaces/mcp_server`):** the architectural template for the future adapter.
