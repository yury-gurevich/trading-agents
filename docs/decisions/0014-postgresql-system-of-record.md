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
the schema lives in `infra/migrations/`, and `POSTGRES_DSN` wins in `build_graph_from_env`. Sprint 117
flipped the fleet default, and Sprint 118 removed the Neo4j runtime adapter/driver/probes. `NEO4J_URI`
now raises an ADR-0014 startup error when it is the only graph-store env. The placement plan in
`docs/research/db-placement/postgres-migration-plan.md` selected Neon free Sydney as the current host,
with Azure Database for PostgreSQL as the paid fallback when economics justify it.

## Decision

**PostgreSQL is the system of record for the trading-agents fleet.** Agents continue to write through
the kernel `GraphStore` port; the physical persistence layer is the Alembic-managed PostgreSQL
`nodes`/`edges` spine.

**Neo4j is no longer runtime infrastructure.** It is kept only as an ad-hoc, out-of-bounds analysis
workbench. It is not a fleet dependency, not a probe target, and not used for rollback.

Rollback after S118 is code rollback: `git revert` the rip-out and redeploy. Previous GHCR images
remain available for image-level rollback; no environment variable re-enables Neo4j.

## Rationale

- **Cost and operations.** Neon free Sydney is enough for the current single-operator spine; the paid
  Azure PostgreSQL path remains available later.
- **Ordinary durability.** PostgreSQL gives mature constraints, SQL inspection, managed backups, and
  standard operator tooling while keeping graph semantics behind the port.
- **Migration discipline.** Schema changes are deliberate Alembic revisions, never ad-hoc DDL.
- **Clean rollback boundary.** The temporary S116/S117 two-backend window closed in S118. Reversal is
  now an explicit code revert + redeploy, which is visible in review and CI.

## Consequences

- `.env.example`, deploy scripts, Container Apps manifests, and probes default to `POSTGRES_DSN`.
- `alembic upgrade head` is the pre-start deploy step for the graph spine.
- `DEP-POSTGRES` is the run-gating store dependency; there is no `DEP-NEO4J` runtime dependency.
- ADR-0001 is superseded by this decision.
- ADR-0008 remains only as the Neo4j analysis-workbench hosting note.
- pgvector and any RAG/vector schema are explicitly out of scope for this ADR and S117.

## Links

- `docs/research/db-placement/postgres-migration-plan.md` — DL-43 plan, host decision, target schema.
- `docs/sprints/sprint-116-postgres-graphstore.md` — adapter/schema parity proof.
- `docs/sprints/sprint-117-postgres-fleet-swap.md` — fleet default flip and live closeout.
- `docs/sprints/sprint-118-neo4j-ripout.md` — runtime rip-out and Aura retirement runbook.
