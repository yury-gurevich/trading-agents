<!-- Agent: planning | Role: sprint handover -->
# Sprint 118 — Neo4j runtime rip-out: one store, one truth (DL-43 step 3, closes the migration)

**Phase:** DL-43 Postgres migration (step 3 of 3; S116 adapter ✅ · S117 swap + ADR-0014 ✅)
**Branch:** `sprint-118-neo4j-ripout`
**Status:** ready for handover — from `main` (S117 merged `d6776ec`, 0.60.00)
**Effort:** S

---

## Codex kickoff (paste this)

> Execute **Sprint 118 — Neo4j runtime rip-out** exactly as specified in this file
> (`docs/sprints/sprint-118-neo4j-ripout.md`). Read ADR-0014 and
> `docs/research/db-placement/postgres-migration-plan.md` (§S118) first.
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-118-neo4j-ripout` (delete any stale
>   local branch first). **Hard gate:** `make ci` green, 100 % coverage, ≤200-line modules, headers.
>   Bump `pyproject.toml` **0.60.00 → 0.60.01** (fix/refactor → PATCH) + `uv lock`.
> - **The job — Neo4j leaves the runtime entirely (ADR-0014's end state):**
>   1. **Delete the runtime adapter:** `kernel/graph_neo4j.py`, `graph_neo4j_queries.py`,
>      `graph_neo4j_config.py`, `graph_cypher.py`; their exports from `kernel/__init__.py`; the
>      Neo4j branch of `kernel/graph_env.py` (an env with only `NEO4J_URI` now gets a **clear
>      startup error naming ADR-0014**, not a silent InMemory fallback); the Neo4j startup-guard
>      branch in `kernel/startup.py`. Keep anything `graph_support.py` provides that Postgres/memory
>      still use.
>   2. **Tests:** delete `tests/test_graph_neo4j.py` + `tests/graph_neo4j_fakes.py`; strip Neo4j
>      parameterizations from `test_graph_backend_rigor.py`/`test_graph.py`/`test_graph_env.py`
>      (InMemory + Postgres remain). Coverage stays 100 %.
>   3. **Deps:** remove `neo4j` from the `runtime` extra; `uv lock`. Nothing in
>      `kernel/agents/orchestration/surfaces` may import `neo4j` afterwards — prove with a grep in
>      the closeout.
>   4. **Ops surface:** retire `infra/aura.ps1`, `scripts/compare_aura.py`, `scripts/neo4j_crud.py`
>      (delete; git history is the archive). Remove the Neo4j DEP probe from `probes/checks.py`
>      (S117 already made it optional) and any `NEO4J_*` handling from `scripts/test-api-keys.ps1`,
>      `.env.example`, `docker-compose.yml` **except**: keep a `workbench` compose **profile** with
>      the Neo4j service (ADR-0008's analysis-only scope) that never starts by default.
>   5. **Docs/laws sweep (surgical):** `docs/laws/{dependencies,stack}.md`, `docs/architecture.md`,
>      `docs/deployment.md`, master mission "operational registry" wording — Postgres only;
>      Neo4j mentioned solely as the out-of-bounds workbench. Add a drift-register entry if any law
>      text contradicted reality. Update `docs/research/db-placement/postgres-migration-plan.md`
>      §S118 status.
>   6. **Aura retirement runbook — do NOT delete Aura in this sprint:** append an operator checklist
>      to this file (grace window: 7 days read-only from merge date → operator deletes instance
>      `bce05bd6` via console/`aura.ps1`-equivalent → confirm billing stop). Deletion is an operator
>      action; the sprint only documents it.
> - **Rollback story changes — state it in the closeout:** after this sprint there is no env-var
>   rollback; rollback = `git revert` + redeploy (previous images still exist in GHCR).
> - **Real-environment check** (sprint-close rule): fresh env sync **without** the neo4j package →
>   `make ci` green → grep proves zero `neo4j` imports outside the workbench compose profile →
>   `POSTGRES_DSN`-only fleet slice on Neon still green (S117 pattern, small: assert
>   `PostgresGraphStore`, one durable write verified from a raw connection, `pg_teardown.py` to 0)
>   → `NEO4J_URI`-only env produces the clear ADR-0014 startup error. Record in
>   `docs/laws/functionality-checks.md`. Never print the DSN.
> - **Out of scope — flag, don't build:** pgvector/RAG tables; the PG→Neo4j workbench snapshot
>   loader (YAGNI-parked in the plan); Apache AGE; any agent contract change; deleting the Aura
>   instance itself.
> - **Do NOT merge or push to `main`** — commit on the branch only; fill **Closeout evidence** here.

---

## Closeout evidence

<!-- Coding agent: fill in on handback. Files deleted/changed, coverage %, the zero-neo4j-import
     grep output, the functionality-check row, the Aura retirement checklist, exact make ci summary.
     Do not merge. -->
