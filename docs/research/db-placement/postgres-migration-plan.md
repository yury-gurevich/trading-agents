# R002 — PostgreSQL migration plan: Postgres spine, Neo4j demoted to analysis workbench

**Status:** Plan complete — awaiting operator go · **Date:** 2026-07-06 · **Author:** planning agent
**Audience:** Product owner, planning agents, coding agents
**Companion:** [db-placement.md](db-placement.md) (the substrate-vs-pack placement research this executes)

Operator directive (2026-07-06): *"see how we can move from Neo4j to PostgreSQL as soon as
possible"*, refined in the same session: *"we will still use Neo4j but for investigations and graph
analysis, ad-hoc and out of bounds"* — i.e. Neo4j leaves the runtime entirely; PostgreSQL becomes
the system of record.

---

## Why the migration is unusually cheap right now (measured, not estimated)

1. **The port is six methods.** `kernel/graph.py::GraphStore` — `merge_node`, `add_edge`, `get_node`,
   `list_nodes`, `ancestors`, `descendants`. Append-only, `(label, key)` identity, typed directed
   edges, bounded-depth traversal. No agent imports Neo4j; import-linter enforces it.
2. **The whole Neo4j surface is ~480 lines** in 4 kernel files (`graph_neo4j*.py`, `graph_cypher.py`)
   plus the env selector. Driver imports: `kernel/graph_neo4j.py`, `probes/checks.py`,
   `scripts/compare_aura.py`, `tests/test_graph_neo4j.py`. Cypher: `kernel/graph_cypher.py`,
   `scripts/compare_aura.py`, `scripts/neo4j_crud.py`. That is the entire blast radius.
3. **Production data volume is zero.** Every functionality check tears down to "Aura baseline 0";
   the fleet does not run distributed yet (S100–103 pending). **There is no data migration** — this
   is an adapter swap plus provisioning.
4. **S101 ("provision the permanent spine") has not executed.** Swap the provisioning target from
   Neo4j to Postgres and the "migration" never happens at all.
5. **A parity rig already exists** — `tests/test_graph_backend_rigor.py` + `tests/test_graph.py` pin
   adapter behavior; a new backend joins the same suite.

## Feature audit — what the graph actually uses

Keyed idempotent merge; typed edges; `ancestors`/`descendants` with `max_depth` (almost always 1:
veto context walks, execution poll, graph-pull loops) and `edge_types` filters; `list_nodes(label)`.
No unbounded traversals, no graph algorithms, no Cypher outside the adapter and two ops scripts.

## Target schema (PostgreSQL)

```sql
CREATE TABLE nodes (
  label          text NOT NULL,
  key            text NOT NULL,
  props          jsonb NOT NULL DEFAULT '{}',
  schema_version int  NOT NULL DEFAULT 1,
  PRIMARY KEY (label, key)
);
CREATE TABLE edges (
  parent_label text NOT NULL, parent_key text NOT NULL,
  child_label  text NOT NULL, child_key  text NOT NULL,
  edge_type    text NOT NULL,
  props        jsonb NOT NULL DEFAULT '{}',
  PRIMARY KEY (parent_label, parent_key, child_label, child_key, edge_type),
  FOREIGN KEY (parent_label, parent_key) REFERENCES nodes,
  FOREIGN KEY (child_label,  child_key)  REFERENCES nodes
);
CREATE INDEX edges_child ON edges (child_label, child_key, edge_type);
```

- `merge_node` → `INSERT … ON CONFLICT (label,key) DO UPDATE` (atomic; strictly better than Cypher
  `MERGE` race behavior).
- `ancestors`/`descendants` → recursive CTE with a depth counter, `edge_type` filter, and a visited
  guard; depth-1 (the dominant case) is a single join.
- Driver: psycopg 3 (lighter than the neo4j driver).

## The trade, with the operator's refinement

**Gain:** no node caps (the original pain); genuinely cheap/free hosting; **pgvector in the same
engine** for the DL-38 RAG/agent-memory candidate; a proper tabular home for ADR-0013 CI-2
`RunMetrics`; boring ops (backups/PITR); atomic merges.
**Lose:** nothing operationally — the one real loss (Cypher browser / visual graph exploration) is
resolved by the refinement: **Neo4j remains as an ad-hoc, out-of-bounds analysis workbench** — local
Docker (ADR-0008's hosting mode), loaded on demand from a Postgres snapshot, with **zero runtime, CI,
law, or cloud dependency**. Build the PG→Neo4j loader script only when the first investigation needs
it (YAGNI; noted, not scheduled).

**Noted, not scheduled — Apache AGE (operator-flagged 2026-07-07).** If in-database Cypher over the
*live* spine is ever wanted (no export step), **Apache AGE** adds a property-graph model + openCypher
inside Postgres, joinable with plain SQL. Requires a C extension the host must allow: **not on
Neon's allowlist**; **available on Azure Flexible Server** (our documented ~US$24/mo fallback) and
any self-hosted PG. The S116 adapter would not change — AGE would sit alongside for analysis.
Trigger to revisit: an investigation that needs live-data Cypher rather than the local-Neo4j
workbench + snapshot loader. Until then: runtime = plain SQL (shipped), analysis = Neo4j workbench,
RAG = pgvector (available on Neon today, v0.8.1 probed).

## Sprint sequence

- **S116 — `PostgresGraphStore` adapter + parity rig** (kernel-only; zero infra risk).
  psycopg adapter + idempotent DDL bootstrap; the backend-rigor suite parameterized over
  InMemory/Neo4j/Postgres (live backends env-gated); `build_graph_from_env` extended —
  `POSTGRES_DSN` selects PG, `NEO4J_URI` keeps working (dual-backend period = instant rollback).
  Live check runs against the **provisioned Neon instance** (see Host DECIDED below) — no local
  Docker Postgres needed.
- **S117 — fleet swap (absorbs S101's intent).** Host already provisioned (**Neon free, Sydney** —
  see Host DECIDED below; Azure B1MS is the paid fallback); `POSTGRES_DSN` enters Key Vault via the
  S108 **tested-before-insert** seeder; fleet env flip; live distributed-slice check on cloud PG.
  **The superseding ADR is written here** (ADR-0001 → "PostgreSQL as the system of record; Neo4j =
  offline analysis workbench"; ADR-0008 amended to analysis-only scope). DL-38's S101 reframe
  ("provision the permanent *spine*") lands on Postgres.
- **S118 — runtime rip-out.** Neo4j adapter + driver out of the runtime path and default deps
  (analysis-only optional extra or deletion — decide at the sprint); `probes/checks.py` DEP probe
  re-pointed; `infra/aura.ps1` + `scripts/compare_aura.py`/`neo4j_crud.py` retired; docs/laws sweep
  (master "operational registry" wording, stack/dependencies law files); drift-register entry; Aura
  instance deleted after a grace window.

**Pace:** S116 hands over when S115 lands (no file overlap, but the shared working dir forces
sequential Codex execution). At current velocity the Postgres spine can be live within days.

## Prior decisions this touches (surfaced per LAW-06)

- **ADR-0001 (Neo4j single primary store, Accepted)** — superseded at S117, not before.
- **ADR-0008 (Neo4j local Docker hosting)** — amended to analysis-workbench scope at S117.
- **DL-38's ruled-out note** ("wholesale migration… pointless when the spine can simply be
  re-hosted") — reversed by operator directive with changed facts: RAG/pgvector (raised by DL-38
  itself), the zero-data window, S101 still queued, Aura economics. DL-38's *architecture* (spine
  shrinks; memory is bundle-declared) is unchanged — Postgres is simply where the spine lives.
- **DL-15** (registry writes are audit-only) and **DL-37** (Tiingo raw-history lineage) unaffected.

## Host investigation (2026-07-06, operator-requested): does free Azure satisfy our needs?

**Verdict: NO — there is no applicable free Azure Postgres offering for this project.**

1. **The only free Azure Postgres deal is the new-free-account bundle** — 750 h/mo Burstable B1MS +
   32 GB for **12 months**, available exclusively to a *new Azure free account*. All three project
   subscriptions are **pay-as-you-go** (`payg-@Live`, `payg`, `payg-@Office`) — **not eligible**.
   Creating a new free account for it would mean a separate tenant/directory cut off from the
   existing RG/Key-Vault/Container-Apps rails, for a benefit that dies in 12 months. Not worth it.
2. **No always-free Postgres tier exists on Azure** (verified 2026-07-06; the always-free list has
   Cosmos DB/Functions/App Service — not Flexible Server). The catalog row in
   `../cloud-free-tiers/microsoft-free-forever.md` was imprecise and is corrected with this finding.
   Cosmos DB's lifetime free tier is not Postgres (no pgvector, different API) — rejected.
3. **Real Azure cost (retail API, australiaeast, 2026-07-06):** B1MS Flexible Server =
   **US$0.0260/h → ≈ US$19/mo** compute (730 h) + 32 GB × $0.138 ≈ **$4.4/mo** storage ≈
   **~US$24/mo (~A$36)**. Cheaper than Aura Professional (~US$65/mo) but not free. Stop/start
   scheduling could cut compute ~80 % at the cost of orchestration complexity (server auto-restarts
   after 7 days; ad-hoc checks would find it down) — not recommended initially.
4. **If free is the requirement: Neon free plan fits the measured workload.** 100 CU-h/mo compute
   (our bursty daily-run profile ≈ 10–20 CU-h at 0.25 CU with 5-min autosuspend), **0.5 GB storage**
   (spine is near-zero today; will bind when CI-2 RunMetrics land → upgrade or move), **pgvector on
   free**, 5 GB egress/mo, AWS Sydney region per Neon's region list (**confirm at provisioning**;
   cross-cloud latency Azure australiaeast ↔ AWS Sydney is single-digit ms). Trades: second vendor,
   ~0.5 s cold start after suspend, the 0.5 GB cap.

**Recommendation:** start S117 on **Neon free (Sydney)** — genuinely $0, serverless matches the
bursty fleet, pgvector included; the `GraphStore` port makes the host a DSN swap, so **Azure B1MS
(~US$24/mo) stays the one-command fallback** when storage/latency/vendor-consolidation argues for it.
Decision confirmed by the operator at S117 kickoff.

## Host DECIDED + provisioned (2026-07-06)

**Neon free (AWS ap-southeast-2 Sydney), project `trading-agents`, PostgreSQL 18** — provisioned by
the operator 2026-07-06. Credential probe (DL-36 tested-before-use, secret in `.env` as
`POSTGRES_DSN`, never printed): connect PASS · PostgreSQL 18.4 · db `neondb` · **pgvector 0.8.1
available** · client TLS **in use** (`sslmode=require`; Neon terminates TLS at its proxy, so
server-side `SHOW ssl` reads off — expected). Direct (non-pooler) host in the DSN, per plan.
Azure B1MS (~US$24/mo, australiaeast) remains the one-command paid fallback via the port.

**S116 consequence:** the real-environment check runs against this live Neon instance (it is empty
and *is* the future spine) — no local Docker Postgres needed.

## Open items for the operator at S117

1. ~~Confirm host~~ — **decided: Neon free (Sydney), provisioned + probed 2026-07-06.**
2. Aura grace window before deletion (suggest: after S118's live check, keep 7 days read-only).
3. `POSTGRES_DSN` enters Key Vault via the S108 tested-before-insert seeder at S117.
