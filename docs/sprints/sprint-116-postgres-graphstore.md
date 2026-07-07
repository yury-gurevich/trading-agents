<!-- Agent: planning | Role: sprint handover -->
# Sprint 116 — PostgresGraphStore: adapter + alembic schema + backend parity (DL-43 step 1)

**Phase:** DL-43 Postgres migration (step 1 of 3: adapter → S117 fleet swap → S118 rip-out)
**Branch:** `sprint-116-postgres-graphstore`
**Status:** ready for handover — from `main` (S115 merged `ab66caf`, 0.58.00)
**Effort:** M

---

## Codex kickoff (paste this)

> Execute **Sprint 116 — PostgresGraphStore** exactly as specified in this file
> (`docs/sprints/sprint-116-postgres-graphstore.md`). It is a complete, self-contained handover.
> Read `docs/research/db-placement/postgres-migration-plan.md` first — it is the design and holds the
> target schema + the operation parity map.
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-116-postgres-graphstore` (delete any
>   stale local branch first). Read every file under *Read first* before writing anything.
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage**, modules **≤ 200 lines**,
>   `Agent:`/`Role:` headers. Bump `pyproject.toml` **0.58.00 → 0.59.00** (feat) + `uv lock`.
> - **The whole job:** a `PostgresGraphStore` adapter (psycopg 3) implementing the six-method
>   `kernel/graph.py::GraphStore` protocol with behavior **identical** to the other backends, its
>   schema owned by **alembic migrations** (operator directive), and the existing parity/rigor suites
>   extended to run against it. **Dual-backend period:** `NEO4J_URI` keeps working unchanged;
>   `POSTGRES_DSN` selects Postgres — instant rollback is the design.
> - **Parity is the definition of done:** the behaviors pinned by `tests/test_graph.py` +
>   `tests/test_graph_backend_rigor.py` (idempotent merge, **append-only props** — existing values
>   never overwritten, only new keys added; edge identity ignoring replayed props; depth-capped +
>   edge-type-filtered traversal with converging-path dedup; nested-props round-trip; ORDER BY key;
>   schema_version guard; **no destructive ops on the port**; one-fault-then-reraise) must pass on
>   Postgres via the same tests, not copies.
> - **Alembic, not ad-hoc DDL:** schema lives in versioned migrations (`infra/migrations/` — alembic
>   `env.py` + one initial revision creating `nodes`/`edges` per the plan's schema). `alembic upgrade
>   head` is how the schema reaches ANY Postgres. The unit gate must NOT need a live PG or alembic run
>   (fakes/InMemory as today); live-backend tests stay env-gated (`POSTGRES_TEST_DSN`, mirroring
>   `NEO4J_TEST_URI` skips).
> - **Live check target is the provisioned Neon instance** (free plan, Sydney — probed PASS
>   2026-07-06; `POSTGRES_DSN` already in `.env`). No local Docker Postgres needed. **Never print the
>   DSN**; load `.env` by explicit path.
> - **Boundaries:** adapter files are `Agent: kernel`; no imports from `contracts`/`agents`. Split
>   like the Neo4j adapter did (`graph_postgres.py` + `graph_postgres_queries.py` + …) to stay under
>   200 lines/file. Do not modify the Neo4j adapter or any agent.
> - **Teardown tooling:** functionality checks need a delete path outside the port — add a small
>   `scripts/pg_teardown.py` (FK-ordered: edges then nodes, by key-prefix stamp), mirroring how Aura
>   checks use DETACH DELETE. Script-only; the port stays append-only.
> - **Real-environment check** (sprint-close rule): `alembic upgrade head` against Neon → run the
>   env-gated backend suite against `POSTGRES_TEST_DSN` (Neon) → drive one **pipeline slice** on
>   Postgres via `build_graph_from_env` (e.g. the S114 veto-context walk: stamped PMRun lineage →
>   `build_veto_context` renders gates — proves merge/edge/traversal on the real spine) → assert
>   `isinstance(graph, PostgresGraphStore)` (the recorded harness lesson) → teardown via
>   `scripts/pg_teardown.py` to zero stamped rows. Record in `docs/laws/functionality-checks.md`;
>   no data files committed.
> - **Do NOT merge or push to `main`** — commit on the branch only, then stop for operator review.
> - When done, append a **Closeout evidence** block to this file.

---

## Read first

- `docs/research/db-placement/postgres-migration-plan.md` — design, target schema (copy it exactly),
  operation parity map, why-now facts.
- `kernel/graph.py` — the 6-method protocol + `Node`/`Edge` (frozen, `_frozen_props`).
- `kernel/graph_memory.py` — the reference semantics (smallest adapter; read fully).
- `kernel/graph_neo4j.py` + `graph_neo4j_queries.py` + `graph_cypher.py` + `graph_support.py` — the
  split pattern, `_append_props`/`_new_props` append-only semantics, fault-boundary wrapping,
  `schema_version` handling. Mirror the *behavior*; JSONB makes the nested-props encode/decode layer
  unnecessary (store `props` as one JSONB document).
- `kernel/graph_env.py` — extend: `POSTGRES_DSN` → `PostgresGraphStore`; precedence when both env
  vars set: **Postgres wins** (the migration direction), `NEO4J_URI` alone unchanged. Update
  `tests/test_graph_env.py`.
- `tests/test_graph.py`, `tests/test_graph_backend_rigor.py`, `tests/test_graph_neo4j.py`
  (+ `graph_neo4j_fakes.py`) — the suites to parameterize/extend; note the env-gated skip pattern.
- `kernel/startup.py` — the auth-retry-storm guard around graph connect; give Postgres the same
  fail-fast courtesy.

## Build

1. **Deps:** `psycopg[binary]>=3.2` joins the `runtime` extra (beside `neo4j`); `alembic>=1.13` in a
   new `postgres` extra (migration tooling, not agent hot path) and in the dev group so CI
   type-checks it. `uv lock`.
2. **Migrations:** `infra/migrations/` — `alembic.ini` (scriptless config ok), `env.py` reading
   `POSTGRES_DSN`, revision `0001_spine` = the plan's `nodes`/`edges` DDL + `edges_child` index.
3. **Adapter:** `kernel/graph_postgres.py` (+ `_queries.py` as needed): connection kept per-store,
   `merge_node` = `INSERT … ON CONFLICT DO UPDATE SET props = EXCLUDED.props || nodes.props,
   schema_version = …guarded…` (append-only: existing keys win; new keys added; schema_version
   change rules identical to the other backends), `add_edge` = `ON CONFLICT DO NOTHING` (+ verify
   both nodes exist → same error type as other backends when missing), `get_node`, `list_nodes`
   (`ORDER BY key`), `ancestors`/`descendants` = recursive CTE (depth counter, `edge_type = ANY(…)`
   filter, visited-dedup, yields `Node`s). Wrap failures with the same fault-boundary pattern the
   Neo4j adapter uses.
4. **Selector:** `graph_env.py` + startup guard + tests.
5. **Teardown script:** `scripts/pg_teardown.py` (`Agent: tooling`) — delete by key prefix,
   edges-first, prints counts; refuses to run without an explicit `--prefix`.
6. **Tests:** parameterize the backend-rigor suite over the new adapter with fakes for unit coverage
   (mirror `graph_neo4j_fakes.py` — a fake cursor/connection is fine for 100 % unit coverage);
   env-gated `POSTGRES_TEST_DSN` live tests mirror `test_graph_neo4j.py`.

## Out of scope (flag, don't build)

Fleet env flip, Key Vault seeding, ADR-0001 supersede (all S117); Neo4j removal, `aura.ps1`/script
retirement (S118); any pgvector table (future RAG sprint); any agent or contracts change.

## Session gotchas

- **Append-only props is the subtle one.** `EXCLUDED.props || nodes.props` puts existing props on
  the winning side — new keys land, existing values never change. Get the rigor test to prove it.
- **Traversal yields nodes, not rows.** Depth-1 is the hot path (veto walks, poll) — don't build a
  clever generic walker that breaks the simple case; the CTE with `depth <= max_depth` is enough.
- **Edge identity:** the PK is (parent, child, type). Replayed `add_edge` with different props is a
  no-op — same as Neo4j `MERGE … ON CREATE SET`.
- **Neon quirks:** TLS terminates at Neon's proxy (`SHOW ssl` reads off — client TLS is what
  matters); scale-to-zero means the FIRST connection after idle takes ~0.5 s — don't let a
  connect_timeout under ~10 s flake the live tests. Direct (non-pooler) host is in the DSN.
- **`make ci` stays 9 steps.** Alembic is exercised by the live check and S117 deploy, not a new
  gate step. Unit tests must pass with no `POSTGRES_DSN` set at all.
- **Never print the DSN.** detect-secrets is watching too.

---

## Closeout evidence

<!-- Coding agent: fill in on handback. Files changed, coverage %, the functionality-check row,
     the parity-suite result on Neon, any decisions/deviations, exact make ci summary. Do not merge. -->
