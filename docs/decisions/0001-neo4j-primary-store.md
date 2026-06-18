---
type: Architecture Decision
status: accepted
closes: "What database do we use for the graph, provenance, and RAG store?"
tags: [neo4j, storage]
---

# ADR 0001 — Neo4j as the single primary store

**Status:** Accepted · **Date:** 2026-06-06 · **Decider:** Yury Gurevich (product owner)

> **Hosting** (where Neo4j runs) is decided separately in
> [ADR-0008](0008-neo4j-hosting-local-docker.md): a single **local Docker container**, Community
> edition. This ADR is unchanged by that — it is about *what* Neo4j is for, not *where* it runs.

## Context

The system needs a durable store for three things at once: **relationships**
(provenance lineage: candidate → recommendation → order → fill → outcome, plus
message lineage), **retrieval-augmented generation** (embeddings + similarity search
for evidence-grounded operator/narration answers), and **flexible, evolving data**
without the migration churn that a relational schema imposes. The product owner's
priority is explicit: *end ongoing schema migrations and the migration CI job.*

An earlier sketch split storage — relational (transactional truth) + a graph for
provenance. That split has a fatal seam: an artifact row (relational) and its
provenance node (graph) cannot commit in one transaction across two engines, so
"every artifact has a node, no orphans" (acquisition-grade traceability) would
require 2-phase commit or an outbox worker. Both add exactly the always-running
machinery the project set out to remove.

## Decision

**Neo4j is the single primary store** for everything: transactional records,
provenance graph, documents, and RAG vectors. There is **no relational store** and
**no Alembic**. Agents reach storage through a kernel **`GraphStore` protocol**
(mirroring how the bus is a `MessageBus` protocol) so the backend stays swappable;
`Neo4jGraphStore` is the implementation.

## Rationale

- **Schema-flexible** — properties are added to nodes without a migration; the
  `migration` CI lane disappears. This is the primary goal.
- **ACID within one store** — artifact + provenance nodes/edges commit in one Neo4j
  transaction; the cross-store orphan problem evaporates because there is no second
  store.
- **Relationships are native** — provenance lineage *is* the graph.
- **RAG is native** — Neo4j vector index (5.11+) holds embeddings as node properties
  with kNN retrieval, so documents, their embeddings, and their relationships live in
  one store; a RAG query and a provenance walk hit the same graph.
- **No relational island needed** — see the analysis below; the money-critical
  guarantees are either available in Neo4j, enforced at the typed-contract boundary
  this system already has, or replaced by a known pattern.

### Why no relational island (the money question)

| Claimed relational need | How it is met without relational |
| --- | --- |
| ACID | Neo4j is ACID. |
| Idempotency / uniqueness | Neo4j unique node-property constraint (Community). |
| Referential integrity | Graph edges require existing endpoints — dangling refs impossible. |
| Required fields / ranges | Pydantic contract validation at the `AgentBase` boundary. |
| Aggregation | Cypher aggregation at single-operator scale. |

Genuinely relational-only, with adopted mitigations:

1. **Exact-decimal money.** Neo4j has no Decimal type → **store money as integer
   minor units (cents), never float.**
2. **DB-level append-only / CHECK / conditional-unique.** Not declarable in Neo4j
   Community → **append-only by convention + `schema_version` versioned nodes +
   uniqueness constraints + code review**; "one active position per ticker" via a
   `MERGE` pattern in the portfolio_manager.

This keeps invariant-enforcement at the typed boundary + agent code — consistent with
the system's existing philosophy, not a regression.

## Consequences

- **Supersedes Sprint 02.** The relational persistence adapter (`kernel/persistence.py`)
  and the Alembic harness (`alembic/`, `alembic.ini`) are retired. Cheapest possible
  moment — only P0–P1 done.
- **Dependencies:** drop `sqlalchemy` + `alembic`; promote `neo4j` to a default
  dependency. Drop the `migration` CI job.
- **Test/CI:** the `GraphStore` protocol gets an **in-memory backend** (like the bus's
  `InProcessBus`), so the **unit gate stays deterministic and infra-free**; the real
  `Neo4jGraphStore` is covered by an `integration`-marked test that runs against a Neo4j
  service in CI and skips locally when none is configured. Net: drop the `migration` job;
  add a Neo4j-backed integration lane (the default unit run keeps the no-infra property).
- **Invariant rename:** "single writer per **table**" → "single writer per **node/edge
  label**" in the boundary meta-test and contracts (the graph-label concept already
  exists on `AgentContract`).
- **`PersistenceSettings.database_url`** → Neo4j connection settings (`NEO4J_URI` etc.,
  already stubbed in `.env.example`).

### Propagation checklist (docs flipped here; code in the storage-adapter sprint)

- Docs updated with this ADR: `PRD.md` §4.3/§4.6/§4.7/§5/§8.3, `architecture.md`
  (data section, invariants, layout), `build-plan.md` (P1, P6, cross-cutting, CI,
  status), `STATE.md`, `observability.md` §2, `README.md`. (`error-handling.md` was
  already store-neutral.)
- Code (storage-adapter sprint, a coding agent): retire `kernel/persistence.py` +
  `alembic/` + `alembic.ini`; add `kernel/graph.py` (`GraphStore` protocol +
  `Neo4jGraphStore`); drop `sqlalchemy`/`alembic` and promote `neo4j` in
  `pyproject.toml` + mypy overrides; swap `DATABASE_URL` → `NEO4J_*` in `.env.example` and
  `PersistenceSettings`; change the boundary meta-test from single-writer-per-table
  to single-writer-per-label. (The "Neo4j" references already in `kernel/contract.py`
  and the curator are correct and need no change.)

## Alternatives considered

- **Relational provenance DAG (Postgres `decision_node`/`decision_edge`).** Atomic and
  no new server, but keeps Alembic/migrations (fails the primary goal) and graph
  ergonomics are recursive-CTE rather than native.
- **Hybrid (relational truth + Neo4j graph).** Reintroduces Alembic for the relational
  island *and* the cross-store atomicity seam — worst of both for the stated goals.

## Optionality

Agents write through the `GraphStore` protocol, never raw Cypher in domain code, so a
different backend could be substituted later without touching agents — the same
two-backend discipline the bus uses.
