---
type: Architecture Decision
status: accepted
closes: "Why is the graph a hand-rolled nodes/edges spine in plain SQL rather than a Postgres graph extension such as Apache AGE? Future work — RAG, data collection and caching, shortest-path and other graph algorithms — sounds like it wants a standard graph engine. Is adopting one too expensive to schedule?"
tags: [postgres, graphstore, apache-age, pgvector, neon, rag, graph-algorithms, adr-0014, dl-43]
amends: ADR-0014
---

# ADR 0024 — The graph stays plain SQL until a named workload needs Cypher

**Status:** Accepted · **Date:** 2026-08-22 · **Decider:** planning agent under delegated authority
(operator: *"is this TOO expensive to schedule Apache AGE"*, 2026-08-22)

## Context

[ADR-0014](0014-postgresql-system-of-record.md) made PostgreSQL the system of record and left the
graph as an Alembic-managed `nodes`/`edges` spine: two tables, with every domain property inside a
JSONB column, behind the six-method kernel `GraphStore` port.

**ADR-0014 never addressed how the graph is represented *inside* Postgres.** It settled Postgres vs
Neo4j and stopped there. The graph-extension question was raised by the operator on 2026-07-07 and
recorded only as a *"noted, not scheduled"* paragraph in
[`docs/research/db-placement/postgres-migration-plan.md`](../research/db-placement/postgres-migration-plan.md) —
a research doc, not a decision. 🚨 **It has since resurfaced twice**, most recently on 2026-08-22 with
a forward-looking framing: *future development (RAG, data collection and caching, shortest-path
algorithms) would require a standard approach — is Apache AGE too expensive to schedule?*

A question that returns because the answer is unfindable is a defect in the decision record, not in
the questioner. This ADR moves the reasoning where `INDEX.md` can answer it, and replaces the
2026-07-07 assertions with measurements taken 2026-08-22 against the live spine.

## Decision

**The runtime graph stays the plain-SQL `nodes`/`edges` spine.** No graph extension is adopted now,
and none is scheduled on anticipation.

**A graph engine is adopted only when a named workload needs it** — not when one is expected to. The
revisit trigger is recorded below, and it is a workload, not a date.

**The `GraphStore` port is the commitment being protected.** Any future adoption must keep agents on
the six-method port; an extension that requires agents to know it exists is refused on ADR-0012
grounds (a graph engine is substrate, and trading agents must not see it).

## Rationale

### 1 · Two of the three stated drivers do not need a graph engine

| Stated need | What it actually requires | Status, measured 2026-08-22 |
| --- | --- | --- |
| **RAG** | `pgvector` | ✅ **Already available on the live host** — `vector` 0.8.6 offered by Neon. AGE is irrelevant to this |
| **Data collection & caching** | ordinary tables / JSONB | No graph engine involved at any point |
| **Shortest-path & graph algorithms** | a real graph engine | 🎯 **The only genuine driver** |

Costing an adoption against all three overstates the case by two thirds. Only the third survives.

### 2 · The blocker is the host, not the technology — and not the version

- 🪤 **Version was checked first, because it would have settled the question regardless of budget.**
  Apache AGE **does** support PostgreSQL 18; master targets it and the 2026 release process runs PG18
  down to PG14. **Not a blocker.** The live spine is **PostgreSQL 18.6**, squarely inside support.
  (PostgreSQL 19 was in Beta 3 on 2026-08-13, GA expected ~Sept/Oct 2026; nothing here runs it.)
- **The host is the blocker.** The live Neon instance offers **93 extensions and `age` is not among
  them.** `pg_graphql` (1.5.12) and `pgrouting` (3.8.0) are offered and sound adjacent, but neither
  substitutes: one is a GraphQL API layer, the other is geospatial routing over PostGIS geometry.
- Adopting AGE therefore means leaving Neon free for **Azure Flexible Server (~US$24/mo)**, ADR-0014's
  documented paid fallback, plus a host-migration sprint.

### 3 · The real cost is a second source of truth, not the $24

🚨 **The 2026-07-07 note's reassurance — *"the S116 adapter would not change; AGE would sit
alongside"* — is only true if AGE holds a _copy_ for analysis.** That buys two representations of one
graph and a synchronisation obligation. This project has already been damaged by exactly that shape:
two documents both tracking status drifted until `docs/build-plan.md` went stale, which is why
`docs/STATE.md` is now the single live tracker by rule. A second graph would be the same failure at a
worse layer, and it sits directly against DL-44's *broker = truth for holdings, graph = truth for
lineage* discipline, which works because each fact has exactly one home.

If instead AGE becomes the **runtime** store, the adapter *does* change, and the sprint is materially
larger than the note implies. **Either way the note understates it.**

### 4 · Deferring is free, because the port already paid the premium

Measured 2026-08-22 — every file containing `psycopg` or raw SQL:

```text
kernel/graph_postgres.py                     the adapter
kernel/graph_postgres_queries.py             the adapter
orchestration/packs/trading_vault_postgres.py    vault/credential provisioning, not graph
orchestration/packs/trading_vault_probes.py      vault probes, not graph
orchestration/tests/test_trading_vault_postgres.py
scripts/pg_provision_roles.py · pg_role_plan.py · pg_teardown.py · pg_teardown_targets.py
scripts/cred_audit_azure.py · scripts/train_lgbm_return.py
```

🟢 **Zero files under `agents/`.** Every agent reaches the graph through `merge_node`, `add_edge`,
`get_node`, `list_nodes`, `ancestors`, `descendants` — and nothing else. Swapping the physical store
is a **kernel-local** change.

**This is the decisive argument for "not now":** waiting accrues no lock-in, so a later adoption costs
no more than an earlier one. The usual reason to buy an abstraction early — that retrofitting gets
dearer — does not apply, because the abstraction is already built and already enforced.

### 5 · An unverified assumption that must not be inherited

🪤 **AGE gives openCypher; it does not give Neo4j GDS.** Its graph-*algorithm* library is
substantially thinner. If the driver is shortest-path or community detection, **AGE may not deliver
what the phrase "standard approach" implies**, while the Neo4j analysis workbench — already the
documented path under ADR-0014, loaded on demand from a Postgres snapshot — carries GDS.

**This is recorded as unverified.** It must be measured in the spike below before any adoption, and
must not be quoted from this ADR as established fact.

## Consequences

- The runtime store, `kernel/graph_postgres.py`, and the `GraphStore` port are unchanged.
- **RAG is unblocked without this decision** — `pgvector` 0.8.6 is available on the current host
  whenever DL-38's agent-memory work is scheduled. It must not wait on a graph engine.
- Neon free remains the host; the Azure Flexible Server fallback stays documented and unexercised.
- Neo4j remains the ad-hoc analysis workbench (ADR-0014), and is the answer for graph algorithms
  today.
- 🚨 **New standing rule:** no agent may acquire a graph-engine-specific dependency. If a sprint needs
  something the six-method port cannot express, that is a signal to revisit this ADR — **not** a
  licence to reach past the port.

### Revisit trigger — a workload, not a date

Reopen this ADR when **a named investigation needs multi-hop Cypher over live data**, where the
snapshot-to-Neo4j workbench is genuinely insufficient. The nearest concrete candidate today is
[ADR-0023](0023-concentration-is-issuer-and-correlation-not-a-vendor-label.md)'s correlated-cluster
detection: currently computed in Python from the 203 bars already on the graph, but if it grows into
community detection over a persisted issuer-correlation graph, that is the trigger.

On reopening, the first unit of work is a **research spike, not an adoption**: confirm AGE's actual
algorithm coverage (§5), decide copy-vs-runtime-store (§3), and cost the host migration.

## Alternatives considered

- **Adopt Apache AGE now, alongside the spine.** Rejected: a second representation with a sync
  obligation (§3), bought for a driver that is one-third as large as stated (§1), on a host that does
  not offer it (§2), when deferring is free (§4).
- **Adopt AGE as the runtime store.** Rejected for now: changes the adapter, the host, and the ops
  floor simultaneously, on anticipation rather than a measured need.
- **Use `pg_graphql` or `pgrouting`**, both already offered by Neon. Rejected: neither is a property-
  graph engine. `pg_graphql` exposes a GraphQL API over relational tables; `pgrouting` solves
  geospatial routing. Recorded because their names invite exactly this confusion.
- **Move to Azure Flexible Server pre-emptively** to keep the option open. Rejected: pays ~US$24/mo
  and a migration sprint for an option the port already preserves at zero cost.
- **Wait for SQL/PGQ** (the SQL:2023 property-graph query standard) to land in core PostgreSQL, which
  would make this question moot without any extension. **Not relied upon** — its core-PostgreSQL
  status is unverified here, and a decision must not rest on an unmeasured roadmap. Noted so the spike
  checks it.

## Links

- [ADR-0014](0014-postgresql-system-of-record.md) — the system-of-record decision this amends.
- [`docs/research/db-placement/postgres-migration-plan.md`](../research/db-placement/postgres-migration-plan.md) —
  the 2026-07-07 *"noted, not scheduled"* paragraph this ADR supersedes as the authority.
- [Apache AGE release notes](https://age.apache.org/release-notes/) · [AGE 2026 roadmap / PG18](https://github.com/apache/age/discussions/2305)
