<!-- Agent: planning | Role: sprint handover -->
# Sprint 118 — Neo4j runtime rip-out: one store, one truth (DL-43 step 3, closes the migration)

**Phase:** DL-43 Postgres migration (step 3 of 3; S116 adapter ✅ · S117 swap + ADR-0014 ✅)
**Branch:** `sprint-118-neo4j-ripout`
**Status:** closed on branch — not merged/pushed (S117 merged `d6776ec`, 0.60.00)
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

Coding agent closeout (2026-07-07, branch `sprint-118-neo4j-ripout`; not merged, not pushed):

- Version/deps: bumped `0.60.00` -> `0.60.01`; `uv lock` refreshed (`uv.lock` normalizes the root
  package as `0.60.1`). `neo4j` was removed from the `runtime` extra and dev dependency surface.
- Deleted runtime adapter/test files: `kernel/graph_neo4j.py`, `kernel/graph_neo4j_queries.py`,
  `kernel/graph_neo4j_config.py`, `kernel/graph_cypher.py`, `tests/test_graph_neo4j.py`, and
  `tests/graph_neo4j_fakes.py`. `kernel/__init__.py` no longer exports Neo4j types.
- Deleted retired ops/runtime scripts: `infra/aura.ps1`, `scripts/compare_aura.py`,
  `scripts/neo4j_crud.py`, plus stale driver-importing helpers (`infra/fleet-graph.ps1`,
  `tools/scripts/aura.ps1`, `codeql/scripts/sync_codeql_to_neo4j.py`) so runtime/import grep stays
  clean. Git history is the archive.
- Runtime behavior: `POSTGRES_DSN` selects `PostgresGraphStore`; no graph env still uses
  `InMemoryGraphStore` for local dev/CI; `NEO4J_URI` without `POSTGRES_DSN` raises a clear
  ADR-0014 error. There is no silent InMemory fallback and no env-var rollback backend.
- Workbench scope: root `docker-compose.yml` keeps Neo4j only behind the `workbench` profile, and
  `infra/neo4j/` is documented as ADR-0008 analysis-only. It never starts by default.
- Docs/laws sweep: dependencies, stack, architecture, deployment, technology stack, law flow,
  law ledger, drift register, agent dependency clauses, master wording, CodeQL docs, probes,
  `.env.example`, and deployment scripts now describe PostgreSQL as the only runtime store.
- Fresh sync proof: `uv sync --extra runtime --extra postgres` completed and explicitly uninstalled
  `neo4j==6.2.0`; `uv pip show neo4j` returned package not found; `importlib.util.find_spec("neo4j")`
  returned absent.
- Zero-import proof: `rg -n "from neo4j|import neo4j|graph_neo4j|graph_cypher|Neo4jGraphStore" kernel agents orchestration surfaces scripts probes tests pyproject.toml uv.lock`
  produced no matches. Fixed-string package greps for `name = "neo4j"`, `neo4j>=`, and `neo4j==`
  in `pyproject.toml`/`uv.lock` also produced no matches.
- Gate: `make ci` green. Summary: Ruff check + format check green; mypy green (`545 source files`);
  import-linter `4 kept, 0 broken`; module-size guard emitted warnings only, no file over 200 lines;
  pytest `1374 passed, 5 skipped`; coverage `100.00%`; detect-secrets passed; pip-audit reported
  no known vulnerabilities.
- Real Neon check (DSN never printed): stamped `s118-livecheck-20260707T205942`; process forced to
  `POSTGRES_DSN`-only; asserted `PostgresGraphStore`; wrote one `S118LiveCheck` node; raw SQL verified
  `durable_count=1`; `uv run python scripts/pg_teardown.py --prefix s118-livecheck-20260707T205942 --env-file .env`
  deleted `0` edges / `1` node; follow-up raw SQL verified `post_teardown_nodes=0` and
  `post_teardown_edges=0`.
- Negative env check: with `POSTGRES_DSN` unset and only `NEO4J_URI=bolt://example.invalid:7687`,
  `build_graph_from_env()` raised:
  `NEO4J_URI is no longer a runtime backend after ADR-0014. Set POSTGRES_DSN for the PostgreSQL system of record, or unset NEO4J_URI for local in-memory development.`
- Functionality-check register: added S118 row to `docs/laws/functionality-checks.md`.
- Rollback story after this branch: rollback is `git revert` + redeploy. Previous GHCR images persist
  for image-level rollback; there is no `NEO4J_URI` env-var rollback.

## Aura retirement runbook (operator action; do not delete in this sprint)

1. Start the read-only grace window on the date S118 is merged/deployed.
2. For 7 days, keep Aura instance `bce05bd6` paused or read-only. Do not write new runtime data to
   Aura; the runtime no longer has a Neo4j adapter.
3. During the grace window, rollback is `git revert` + redeploy to the previous GHCR image. Do not
   re-enable Aura by environment variable; that path is retired.
4. On day 7 or later, the operator confirms production has run on PostgreSQL and no S118 rollback is
   pending.
5. The operator deletes Aura instance `bce05bd6` from the Neo4j Aura console or an Aura API/CLI
   equivalent. The retired `infra/aura.ps1` script is intentionally not restored for this.
6. Confirm the Aura instance is gone and billing has stopped, then record the deletion in the
   operations audit trail.
