---
type: Architecture Decision
status: accepted
closes: "What is the system of record after DL-43? What is Neo4j for now?"
tags: [postgres, neo4j, storage, graphstore, dl-43]
supersedes: ADR-0001
---

# ADR 0014 — PostgreSQL is the system of record; Neo4j is an ad-hoc analysis workbench

**Status:** Accepted · **Date:** 2026-07-07 · **Decider:** Yury Gurevich (product owner)

## Context

ADR-0001 chose Neo4j to avoid relational migration churn while the system was still finding its shape.
DL-43 reversed that trade after the graph port had settled: the project now needs a cheaper,
ordinary, migration-governed system of record that still preserves the `GraphStore` abstraction.

Sprint 116 proved the technical bridge: `PostgresGraphStore` implements the same six-method graph port,
the schema lives in `infra/migrations/`, `POSTGRES_DSN` wins in `build_graph_from_env`, and `NEO4J_URI`
continues to work when Postgres is unset. The placement plan in
`docs/research/db-placement/postgres-migration-plan.md` selected Neon free Sydney as the current host,
with Azure Database for PostgreSQL as the paid fallback when economics justify it.

## Decision

**PostgreSQL is the system of record for the trading-agents fleet.** Agents continue to write through
the kernel `GraphStore` port; the physical persistence layer is the Alembic-managed PostgreSQL
`nodes`/`edges` spine.

**Neo4j is no longer primary infrastructure.** Until S118 removes it from runtime composition, Neo4j is
kept only as an ad-hoc, out-of-bounds analysis workbench and as a rollback backend.

Rollback before S118 is configuration-only: unset `POSTGRES_DSN`, set `NEO4J_URI` plus its credentials,
and redeploy. No agent contract changes are involved.

## Rationale

- **Cost and operations.** Neon free Sydney is enough for the current single-operator spine; the paid
  Azure PostgreSQL path remains available later.
- **Ordinary durability.** PostgreSQL gives mature constraints, SQL inspection, managed backups, and
  standard operator tooling while keeping graph semantics behind the port.
- **Migration discipline.** Schema changes are deliberate Alembic revisions, never ad-hoc DDL.
- **Rollback remains cheap.** The S116 selector keeps the Neo4j adapter available during the
  two-backend window, so S117 can flip defaults without an irreversible cutover.

## Consequences

- `.env.example`, deploy scripts, Container Apps manifests, and probes default to `POSTGRES_DSN`.
- `alembic upgrade head` is the pre-start deploy step for the graph spine.
- `DEP-POSTGRES` is the run-gating store dependency; `DEP-NEO4J` is rollback/analysis-only.
- ADR-0001 is superseded by this decision.
- ADR-0008 remains only as the Neo4j workbench/rollback hosting note until S118.
- pgvector and any RAG/vector schema are explicitly out of scope for this ADR and S117.

## Links

- `docs/research/db-placement/postgres-migration-plan.md` — DL-43 plan, host decision, target schema.
- `docs/sprints/sprint-116-postgres-graphstore.md` — adapter/schema parity proof.
- `docs/sprints/sprint-117-postgres-fleet-swap.md` — fleet default flip and live closeout.
