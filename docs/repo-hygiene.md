# Repo hygiene

How we keep this repo clean without losing work. The cleanup runs as a **multipass**: each
pass identifies stale files/components, **moves** (never hard-deletes) them to a staging
folder, and records what happened here. Nothing is destroyed until a human confirms a batch
is truly dead.

## Principles

1. **Move, don't delete.** Stale files go to the sibling staging folder
   `../trading-agent-del/` (outside the git repo), preserving their original relative path so
   they can be restored with a single `mv`. Each pass appends a row to
   `trading-agent-del/RESTORE.md`.
2. **Never break the build to tidy up.** The repo enforces `--cov-fail-under=100.00`,
   import-linter contracts, mypy strict, and ruff. A file is only "stale" if removing it keeps
   all of these green. Source that is imported by live code or tests is **load-bearing**, not
   stale — retiring it is a coordinated change (code + tests + deps + CI + infra together),
   not a file move.
3. **Respect the keep-list.** Do not touch: `*.db` files, `desktop.ini`, the operator's
   `.env.bak`, or any in-progress work (currently: all CodeQL artifacts).
4. **Record retirements** in [`STATE-01.md`](state-archive/STATE-01.md) → *Retired components*, and update
   `RESTORE.md`.

## Staging folder

`c:\Users\yury_\Downloads\project\trading-agent-del\` — a sibling of `trading-agents/`, so
moved files leave the working tree (tracked files show as deletions in `git status`;
gitignored files just disappear from the tree). Restore with, e.g.:

```bash
# from c:/Users/yury_/Downloads/project
mv trading-agent-del/infra/neo4j/docker-compose.yml trading-agents/infra/neo4j/docker-compose.yml
```

## Pass 1 — 2026-06-18

**Neo4j consolidation + env.** The graph store is now a single source of truth: local Neo4j
**Enterprise** in Docker (`infra/neo4j/local/`, APOC + GDS, default db `traiding-agents`).

- `.env` + `.env.example`: active local block uncommented; **all other Neo4j connection
  combinations commented out** (Aura `02812797`, prior Desktop `trading-agent`). The two files
  are kept in sync; `.env.example` carries no secrets.
- `infra/neo4j/README.md` repointed to `local/`.

**Moved to `trading-agent-del/`** (see `RESTORE.md` for the table):

| Item | Why |
| --- | --- |
| `alembic/` | Relational store + Alembic dropped in Sprint 03 (ADR-0001); only an empty `versions/` remained. |
| `data/` | Orphaned gitignored local append/WAL store (Sprint-02 persistence era), superseded by Neo4j; no source references it. |
| `infra/neo4j/docker-compose.yml` + `.env` + `.env.example` | Superseded Neo4j instance (named-volume, no plugins, `neo4j` db); replaced by `infra/neo4j/local/`. |

**STATE.md** split: the older shipped ledger (**Sprint 36 → P0**) moved to
[`STATE-01.md`](state-archive/STATE-01.md) with a continuation note left in `STATE.md`; STATE.md dropped from
583 → ~290 lines.

**Deliberately kept** (not moved): `*.db`, `desktop.ini`, `folderico-favorites.ico` (folder
icon paired with `desktop.ini`), `.env.bak`, regeneratable caches
(`.mypy_cache/ .pytest_cache/ .ruff_cache/ .import_linter_cache/ htmlcov/ .coverage`), and all
CodeQL artifacts (`.codeql-db/ .tools/ codeql/ .github/codeql/ run_codeql_ast.ps1
scripts/*codeql*`) — active in-progress work.

## `pyproject.toml` component audit

Every declared dependency is **imported by live code or the toolchain** — nothing is safely
removable today without reddening the 100 % gate. The components flagged for review are whole
subsystems; each needs an operator decision and a coordinated retirement, not a file move.

| Component | Dep(s) | Used by | Verdict |
| --- | --- | --- | --- |
| Pydantic | `pydantic`, `pydantic-settings` | Everything (contracts, settings) | **Keep** — foundation. |
| Neo4j | `neo4j` | `kernel/graph_neo4j*.py` (primary store) | **Keep** — primary store (ADR-0001). |
| MCP | `mcp` | `surfaces/mcp_server.py`, `mcp_tools.py` | **Keep** — live surface. |
| FinBERT | `torch`, `transformers` | forecaster (S49, lazy) | **Keep** — advisory ML, lazily imported. |
| Toolchain | pytest/ruff/mypy/import-linter/pip-audit/detect-secrets/pre-commit | CI gates | **Keep**. |
| **Celery bus** | `celery`, `redis` | `kernel/bus_celery*.py` (`CeleryBus`), `test_bus_celery.py`, `test_p4_celery_parity.py` | **Decision** — working distributed bus. **Recommend: retire as part of P14** (inter-agent comms re-architecture → event-driven pub/sub → Azure Service Bus), not as ad-hoc hygiene. `redis` is Celery's broker — it lives/dies with Celery. |
| **Prometheus / Grafana** | `prometheus-client` | `kernel/metrics_prometheus.py`, `surfaces/metrics_server.py`; infra: root `docker-compose.yml` sidecar, `infra/prometheus/`, `infra/grafana/` | **Split decision** — the in-code `Metrics` adapter is small, vendor-neutral, and feeds Azure Monitor remote-write → **keep**. The **local Prometheus/Grafana infra** may be superseded by Azure Monitor; retire only if you've abandoned the local metrics UI. |
| **Postgres probe** | `psycopg2-binary` | `probes/checks.py` (`probe_neo4j` neighbour: Postgres raw-OHLCV probe); `.env` `DATABASE_URL`/`PG*` | **Decision** — documented raw-OHLCV **backtest** source (ADR-0006, raw-data-only). Lightly used (a probe). **Keep** unless the Postgres backtest path is abandoned; if so, retire probe + `psycopg2` + `.env` creds together. |

> **Alembic** is already retired (no longer in `pyproject.toml`; the empty `alembic/` dir was
> moved in pass 1).

## Pass 2 — 2026-06-19

**Azure-native stack ratification (ADR-0009).** The tech-stack charter (`docs/laws/stack.md`)
was written and accepted. All infrastructure must be Azure-managed; Neo4j is the explicit
graph-store exception; external SaaS vendors are a separate category.

`DEP-BUS` in `docs/laws/dependencies.md` corrected: "RabbitMQ / ADR-0004" → "Azure Service Bus /
ADR-0005; transitional CeleryBus retires at P14." `docs/laws/ledger.md` corrected:
`DEP-NEO4J` updated from Aura to local Enterprise Docker; `DEP-TELE` updated to reference
Azure Monitor/Managed Prometheus.

**Moved to `trading-agent-del/`** (see `RESTORE.md`):

| Item | Why |
| --- | --- |
| `infra/prometheus/` (prometheus.yml, Dockerfile, prometheus.compose.yml) | Local Prometheus server retired; metrics go via prometheus-client → Azure Managed Prometheus remote-write (ADR-0009). |
| `infra/grafana/dashboards/trading-agents.json` | Local Grafana dashboard retired; superseded by Azure Monitor (never opened in normal operation). |
| `infra/setup-prometheus-auth.ps1` | Setup script for the retired local Prometheus sidecar; Azure credentials it produced are already in `.env`. |
| `infra/setup-grafana-datasource.ps1` | Setup script for the retired local Grafana. |

**`docker-compose.yml` updated:** `prometheus` service, `observability` network, and
`prometheus_config` configs entry removed. File now only runs the `app` service locally.

**Deliberately kept:**

- `prometheus-client` Python library — the in-code SDK that generates metrics and remote-writes
  to Azure Managed Prometheus. Not a local server; not retired.
- `infra/setup-azure.ps1`, `infra/setup-container-apps.ps1`, `infra/*.bicep` — Azure IaC; active.

## Pass 3 — 2026-06-19

**Postgres raw-OHLCV fallback retired.** Tiingo (primary, S44, probed green) + Alpaca
(failover, S45, probed green) cover the OHLCV need; the Postgres backtest fallback is no
longer required.

**Removed from the codebase** (no file move needed — nothing was git-tracked for Postgres
except config and the probe function):

| Item | Change |
| --- | --- |
| `probes/checks.py` — `_postgres_ohlcv` function | Deleted |
| `probes/checks.py` — `probe_feed_ohlcv` call + docstring | Updated to Tiingo + FMP only |
| `probes/checks.py` — `probe_config` `DATABASE_URL` check | Removed |
| `probes/__init__.py` + `probes/__main__.py` docstrings | Removed Postgres mention |
| `pyproject.toml` — `probes = ["psycopg2-binary>=2.9"]` optional group | Deleted |
| `.env` — `DATABASE_URL`, `PG*`, `TEST_DATABASE_URL` | Commented out with retirement note |
| `.env.example` — Postgres section | Commented out with retirement note |
| `docs/laws/dependencies.md` — DEP-FEED | Postgres noted as retired 2026-06-19 |
| `docs/laws/ledger.md` — DEP-FEED + harness command | Postgres probe removed; `--extra probes` flag dropped |
| `docs/laws/stack.md` — vendor table | Postgres row removed |
| `infra/neo4j/README.md` — verify command | `--extra probes` flag dropped |

**Probe harness command** updated everywhere from
`uv run --extra runtime --extra probes python -m probes` →
`uv run --extra runtime python -m probes`.

## Open decisions (pass 4)

1. **Celery/Redis** — deferred to P14 (ratified). Retires when `ServiceBusBus` ships. No further hygiene decisions pending.

## Local dev tools

Tools installed on the dev machine (outside `pyproject.toml`) and approved for Claude Code so
they run without a permission prompt:

| Tool | Install | Approved via | Used for |
| --- | --- | --- | --- |
| `jq` 1.8.2 | `winget install jqlang.jq` (user scope) | `.claude/settings.json` → `permissions.allow` `Bash(jq:*)` | JSON processing in bash (e.g. filtering `gh run list --json` output). Note: `gh`'s built-in `--jq` flag also works without the external binary. |

## Follow-ups (not blocking)

- `kernel/graph_neo4j_config.py` still defaults `neo4j_database="neo4j"`. The runtime `.env`
  override (`traiding-agents`) wins, so this is cosmetic; align the code default in a future
  change if/when tests that pin it are updated (touches the 100 % gate).
- ~~Once Aura is deleted, drop the commented Aura recovery lines from `.env`.~~ Done 2026-06-19:
  Aura instance deleted; `.env` Aura block collapsed to a one-line tombstone.
