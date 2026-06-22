# Project State

**Last updated:** 2026-06-22 22:14 AEST

**S77–S85 SHIPPED. S77–S83 (graph-pull pipeline) + batch-trace + live-Neo4j hardening merged to
main (0.23.00). S84+S85 closed BOTH platform/pack leaks in the master (DL-12): the grant policy
(S84, 0.23.01) and the secret map (S85, 0.23.02) now live in pack data files
(`orchestration/packs/trading_*.json`), loaded by path and injected — the master substrate names
zero trading concepts. S84 merged to main + GitHub CI green; S85 on its branch, green locally.
Next: S86 — deploy wiring (ship the pack JSONs into the master image + set the two MASTER_*_PATH
env vars), then DL-10 staleness fix / DL-09 filter source.**

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* = exists but
inactive. *Recent sprints* = the last ~8 shipped; older history is archived (see Archive). Update
at every transition. Stamp "Last updated" with Melbourne local time.

---

## Recent sprints (most recent first)

- **S85 — secret map out of the substrate (DL-12 leak #2; 0.23.01→0.23.02, PATCH).** `AGENT_SECRETS`
  deleted from `agents/master`; the `(kv_name, env_name)` table moved to
  `orchestration/packs/trading_secrets.json`, loaded via `MasterSettings.secret_map_path`
  (`load_secret_map`) and injected; `resolve_config(agent_type, store, secret_map)` takes the map as a
  param. The master substrate now names zero trading concepts. **1054 tests**, 100% coverage. On branch
  `sprint-85-platform-pack-secret-map`, green locally (not yet merged).
- **S84 — grant policy out of the substrate (DL-12 leak #1; 0.23.00→0.23.01, PATCH).** `DEFAULT_GRANTS`
  deleted; the 12-agent grant table moved to `orchestration/packs/trading_grants.json`, loaded via
  `MasterSettings.grant_policy_path` (`load_grant_policy`) and injected — read by path, never imported,
  so the `agents↛orchestration` boundary holds. Merged to main, GitHub CI green.
- **post-S83 (on the sprint-83 branch; 0.22.00→0.23.00) — batch-trace + live-Neo4j hardening.**
  `orchestration/batch_trace.py` + `scripts/trace_run.py` + `run_local.py --real/--trace` walk the
  provenance chain and print per-stage numbers (incl. the provider `quality` block and per-ticker analyst
  REJECT reasons). First **live Aura run** found + fixed **2 real Neo4j bugs the in-memory store hid**:
  nested-map node properties (JSON-encode at the store boundary, `kernel/graph_support.py`) and a
  list/tuple idempotency mismatch in `_append_props`. Backup/restore proven via a sentinel node. Captured
  DL-09 (filter training source), DL-10 (staleness gate counts calendar days but means trading sessions),
  DL-11 (Aura ops). Merged to main.
- **S83 — graph-pull orchestration trigger + e2e demonstrator (0.22.00).** Dispatcher writes one
  `RunRequest`; the provider is now graph-pull on it; every downstream agent wakes off its prerequisite
  gate. `orchestration/start.py` (`preflight` + `place_run_request`), `local_pipeline.cascade_once`,
  `scripts/run_local.py`, `test_graph_pull_e2e.py`. Closes DL-08's explicit-start gap.
- **S82 — execution+monitor+reporter graph-pull (0.21.00).** Final three agents move bus→graph data path;
  **closes DL-08 end-to-end** (provider→…→reporter all graph-pull).
- **S81 — analyst→PM graph-pull (0.20.00).** PM reads the `RecommendationSet` + market from the graph.
- **S80 — scanner→analyst graph-pull (0.19.00).** Provider persists full `RegimeContext`; scanner persists
  full `CandidateSet`; analyst reads all three from the graph. Scoring core extracted to
  `agents/analyst/run.py` shared by the bus + graph paths.
- **S79 — provider→scanner vertical slice + `work_loop` (0.18.00, DL-08b).** Provider persists the full
  `MarketData` payload; scanner reads market data from the graph (`agents/scanner/poll.py`), not bus RPC;
  reusable `kernel/work_loop.py`.
- **S78 — provider standalone graph-ingestor (0.17.00).** `kernel/graph_env.build_graph_from_env`;
  `agents/provider/ingest.py` (`universe_from_env`/`ingest_once`/`ingest_loop`); provider entrypoint
  replaces `idle_loop` with real ingest.
- **S77 — credential-naming reconciliation (0.16.1, PATCH).** `secret_map.py` emits
  `PROVIDER_TIINGO_API_KEY` (not bare); aligned the three entitled agents' env-var names; Neo4j integration
  test skips gracefully when Aura is smart-paused.

---

## Now

Platform/pack separation: **both master leaks closed.** With S84+S85 the master substrate is
domain-agnostic — grants and secrets are pack-supplied data loaded by path, not hardcoded. The
graph-pull pipeline (S77–S83) runs end-to-end and has been exercised on real Aura. S85 is on its branch,
green locally, awaiting a merge decision.

**Architecture (DL-08, 2026-06-21): graph-as-queue / pull model.** Provider writes all data to Neo4j;
other agents poll the graph for unprocessed work — no Service Bus needed for correctness. P14 pub/sub
remains an optional fast-path notification. Full detail in `docs/design-log.md`.

## Next

- **S86 — deploy wiring (the necessary follow-up to S84+S85; NOT CI-tested).** Ship
  `trading_grants.json` + `trading_secrets.json` into the master Docker image and set
  `MASTER_GRANT_POLICY_PATH` + `MASTER_SECRET_MAP_PATH` in `infra/deploy-agents.ps1` / the master
  Dockerfile. **Without this, a deployed master loads empty policies and rejects every agent** — must land
  before the next fleet deploy.
- **DL-10 staleness fix** — count trading sessions, not calendar days (market-calendar aware). OPEN.
- **DL-09 filter training source** — per-ticker verdict + bypass + dual labels → curator dataset.
- **Permanent graph store** — self-host Neo4j on a small Azure VM for the fleet to run durably (Enterprise
  if the dev licence lands, else Community).
- **Fleet run-through on real store** — full `provider→reporter` cascade against the permanent store.
- **Dispatcher cron** — schedule the daily `RunRequest` so the fleet runs hands-off.
- **Forecaster + control-plane agents** (operator/supervisor/curator/researcher) work loops — the last
  `idle_loop()` holders.
- **P12/P13 DSPy harness** — queued after agents actually run (news runway needed).
- **`contracts/` substrate/pack split** — the remaining ADR-0012 mix; deferred until a 2nd pack.

## Workflow

Each sprint/chore on its own branch (`sprint-NN-<slug>`); merge to `main` is the deploy trigger. This
cycle the operator implements sprints end-to-end (code+tests+CI+commit). See `docs/sprints/README.md`.

## Parked

- (none)

## Archive

> Older shipped history is split out to keep this file short:
> **Sprints 37–76** (P11 → P15 master-bootstrap arc) → [STATE-02.md](STATE-02.md).
> **Sprint 36 → P0** + retired-components log → [STATE-01.md](STATE-01.md).
> Keep only the most recent ~8 sprints here; move older entries down as this list grows.

---

## Pointers

- Product intent: `docs/PRD.md`
- Structure & rules: `docs/architecture.md`
- Sequenced plan: `docs/build-plan.md`
- Configuration governance: `docs/configuration.md`
- Error handling: `docs/error-handling.md`
- Observability & historical data: `docs/observability.md`
- Hardening backlog (deferred security/quality, with unblock triggers): `docs/hardening-backlog.md`
- Per-agent charters: `agents/<name>/mission.md`
- Machine boundaries: `contracts/<name>.py`
