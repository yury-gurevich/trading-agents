<!-- Agent: planning | Role: sprint handover -->
# Sprint 117 — Postgres fleet swap: seed, flip, prove, supersede (DL-43 step 2)

**Phase:** DL-43 Postgres migration (step 2 of 3: S116 adapter ✅ → **swap** → S118 rip-out)
**Branch:** `sprint-117-postgres-fleet-swap`
**Status:** closed on branch — not merged/pushed (S116 merged `5f11b93`, 0.60.00)
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

Coding agent closeout (2026-07-07, branch `sprint-117-postgres-fleet-swap`; not merged, not pushed):

- Files changed: added `orchestration/packs/trading_vault_postgres.py`,
  `orchestration/tests/test_trading_vault_postgres.py`, and
  `docs/decisions/0014-postgresql-system-of-record.md`; updated the S108 vault seed manifest/probes,
  `agents/master/entrypoint.py`, `probes/checks.py`, `infra/deploy-agents.ps1`, `infra/main.bicep`,
  `.env.example`, `docker-compose.yml`, deployment/architecture/law/ADR docs, `scripts/pg_teardown.py`,
  `scripts/test-api-keys.ps1`, `pyproject.toml`, and `uv.lock`.
- Version/deps: bumped `0.59.00` → `0.60.00`; `uv lock` refreshed (`uv.lock` normalizes the root
  package version to `0.60.0`).
- Key Vault: mirrored the S108 tested-before-insert seeder path for `postgres-dsn`. Dry-run
  `uv run --extra azure --extra runtime python scripts/seed_key_vault.py --only postgres-dsn`
  reported `postgres probe passed`; operator-approved `--apply` reported `postgres-dsn seeded postgres
  probe passed`; separate read-back from `trading-agents-kv` proved the value was present and equal to
  `.env`. The DSN was never printed.
- Composition/deploy: default graph selection now runs through the shared env selector (`POSTGRES_DSN`
  wins; `NEO4J_URI` still works as rollback when Postgres is absent). Container defaults and deployment
  docs now inject `POSTGRES_DSN`; `infra/deploy-agents.ps1` loads `.env` without printing secrets,
  probes Postgres with a ≥10 s timeout, runs `alembic -c infra/migrations/alembic.ini upgrade head`
  before starting the fleet, and preserves the Neo4j rollback branch.
- Probe/laws: `probes/checks.py` adds `DEP-POSTGRES-01` (`SELECT 1`) and treats Neo4j as optional
  rollback/workbench when Postgres is active. `docs/laws/dependencies.md`, `docs/laws/ledger.md`, and
  `docs/laws/functionality-checks.md` now make Postgres the default dependency truth.
- ADRs: added ADR-0014, "PostgreSQL is the system of record; Neo4j is an ad-hoc analysis workbench,"
  with frontmatter `supersedes: ADR-0001`; marked ADR-0001 superseded; amended ADR-0008 to
  analysis/rollback scope; updated `docs/decisions/INDEX.md`.
- Live Neon evidence: with `.env` loaded by explicit path and `NEO4J_URI` removed from the process,
  `alembic upgrade head` completed against Neon; `DEP-CONFIG-01` and `DEP-POSTGRES-01` were green.
  The S99-style served slice stamped `s117-livecheck-20260707T194720`, asserted
  `isinstance(graph, PostgresGraphStore)`, served forecaster/researcher/curator, and a separate raw
  connection verified durable nodes (`CloseDecision:6`, `Dataset:1`, `Experiment:1`, `Flag:1`,
  `Model:1`, `ParamChange:1`, `Position:6`, `ShadowPrediction:1`, `Snapshot:6`,
  `TradeNarrative:6`, `TrainingExample:6`) plus **26** edges.
- Teardown/functionality register: `uv run python scripts/pg_teardown.py --prefix
  s117-livecheck-20260707T194720 --contains --env-file .env` deleted **26 edges / 36 nodes**;
  follow-up raw query verified **post_teardown_nodes=0, post_teardown_edges=0**. Evidence appended to
  `docs/laws/functionality-checks.md`.
- Final `make ci`: green. Ruff check + format kept; mypy green for **549 source files**;
  import-linter **4 kept / 0 broken**; module-size guard had warnings only (new modules under the
  200-line hard cap); pytest **1383 passed, 6 skipped, 100.00% coverage**; `pip-audit` reported no
  known vulnerabilities (torch skipped because the CPU wheel is not on PyPI); detect-secrets passed.
