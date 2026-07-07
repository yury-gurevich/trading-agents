<!-- Agent: planning | Role: sprint handover -->
# Sprint 117 — Postgres fleet swap: seed, flip, prove, supersede (DL-43 step 2)

**Phase:** DL-43 Postgres migration (step 2 of 3: S116 adapter ✅ → **swap** → S118 rip-out)
**Branch:** `sprint-117-postgres-fleet-swap`
**Status:** ready for handover — from `main` (S116 merged `5f11b93`, 0.59.00)
**Effort:** S/M

---

## Codex kickoff (paste this)

> Execute **Sprint 117 — Postgres fleet swap** exactly as specified in this file
> (`docs/sprints/sprint-117-postgres-fleet-swap.md`). Read
> `docs/research/db-placement/postgres-migration-plan.md` first (design + host decision), then the
> S116 closeout in `docs/sprints/sprint-116-postgres-graphstore.md` (what already works).
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-117-postgres-fleet-swap` (delete any
>   stale local branch first). **Hard gate:** `make ci` green, 100 % coverage, ≤200-line modules,
>   headers. Bump `pyproject.toml` **0.59.00 → 0.60.00** (feat) + `uv lock`.
> - **The job — make Postgres the store the system actually runs on:**
>   1. **Secret into Key Vault, tested-before-insert (DL-36/S108).** Trace how the Neo4j credentials
>      reach the vault + master secret map today (S108 seeder manifest + `agents/master` secret
>      naming) and mirror that path exactly for `POSTGRES_DSN`. The S108 seeder must **probe the DSN
>      live** (connect + `SELECT 1`) before writing; fail-closed. Dry-run first, then `--apply`
>      (operator-approved by this handover), read-back equality proven.
>   2. **Default the composition to Postgres.** `.env.example` + deployment/config docs +
>      `infra/` container env (wherever `NEO4J_URI` is injected today) point the fleet at
>      `POSTGRES_DSN`. `NEO4J_URI` vars stay **supported** (S116 selector: Postgres wins) — rollback
>      is unsetting one env var. Do not delete any Neo4j code/config (that is S118).
>   3. **Deploy step:** document + wire `alembic upgrade head` as the schema step before the fleet
>      starts (deployment doc + wherever bootstrap/startup docs live). Startup fail-fast guard
>      already exists from S116.
>   4. **Probes:** extend `probes/checks.py` with a `DEP-POSTGRES` credential probe (connect +
>      SELECT 1, DSN from env/vault), mirroring the existing DEP probes.
>   5. **ADR supersede (the decision record):** new ADR at the next free number in
>      `docs/decisions/` — "PostgreSQL is the system of record; Neo4j is an ad-hoc, out-of-bounds
>      analysis workbench" — YAML frontmatter per the house pattern (`type/status/closes/tags`,
>      `supersedes: ADR-0001`), citing DL-43 + the migration plan. Mark ADR-0001 superseded (banner +
>      INDEX row), amend ADR-0008 to analysis-only scope (dated amendment block, ADR-0006 style).
>      Update `docs/decisions/INDEX.md` rows. Sweep `docs/laws/{stack,dependencies}.md` +
>      `docs/architecture.md` wording (Postgres spine; Neo4j analysis-only) — surgical edits, no
>      rewrite.
> - **Real-environment check** (sprint-close rule): with `POSTGRES_DSN` set and **no** `NEO4J_URI`
>   in the process env — (a) seeder `--apply` proof: vault read-back equals `.env`, probe log shows
>   tested-before-insert; (b) an S99-style in-process fleet slice (serve_loop agents) writing durable
>   artifacts to **Neon**, `isinstance(graph, PostgresGraphStore)` asserted, artifacts verified from
>   a **separate raw connection**, teardown via `scripts/pg_teardown.py` to 0 stamped rows;
>   (c) `DEP-POSTGRES` probe green. Record in `docs/laws/functionality-checks.md`. **Never print the
>   DSN.** No data files committed.
> - **Out of scope — flag, don't build:** deleting Neo4j adapter/deps/scripts, retiring
>   `infra/aura.ps1`, Aura teardown (all S118); pgvector tables; any agent contract change.
> - **Do NOT merge or push to `main`** — commit on the branch only; append **Closeout evidence** here.

---

## Notes for the coding agent

- The Key Vault is `trading-agents-kv` (RG `trading-agents`); the S108 seeder is the only sanctioned
  write path and it must remain fail-closed. The production vault is intentionally not torn down —
  the new `POSTGRES_DSN` secret stays after the check (it is production config, like the S108 row).
- Neon quirks (from S116): scale-to-zero cold start ~0.5 s — keep connect timeouts ≥ 10 s; client
  TLS is what matters (`sslmode=require`); direct (non-pooler) host.
- Rollback story to state in the ADR: set `NEO4J_URI` (+ unset `POSTGRES_DSN`) and redeploy — the
  S116 selector restores Aura with zero code changes, until S118 removes it.
- If the master's secret-naming/entitlement code needs a new entry for the graph DSN, keep it
  additive and mirror the existing naming convention exactly.

---

## Closeout evidence

<!-- Coding agent: fill in on handback. Files changed, coverage %, seeder proof, fleet-slice proof,
     ADR numbers touched, the functionality-check row, exact make ci summary. Do not merge. -->
