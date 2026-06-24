# Project State

**Last updated:** 2026-06-25 01:02 AEST

**DIRECTION PIVOTED (DL-19). The goal is now to perfect the trading-agents bundle so it becomes
*etalon v0.1* — the hand-crafted reference the platform will one day reproduce (`ops/agent-genesis.md`).
Governance scaffolding shipped this session (v0.24.00→0.29.00): ADR-0013 continuous-improvement
system + P16/CI-1..CI-6 specs; Experimentation, Housekeeping & Deliberation charters; `librarian` +
`tuner` subagents + a deliberation harness (LLM defend/attack/judge) + an **eval harness** that scores a
debate against a manufactured answer key (0.29.00); the etalon. Pipeline: Alpaca primary OHLCV + chunked
ingest. **The bundle now TRADES** — the validate-once fix (0.28.01) yielded a clean 99/99 batch that
opened 5 positions (2026-06-24). Next: it trades *cleanly but not yet wisely* — the 5 names are
correlated tech, a concentration/risk gap (quant-methods Part 2/3). DSPy's first job is now framed as a
**model-drift firewall** (DL-24): a model swap is a *gated* change that must pass the eval. Meta-machinery
(CI-1..CI-6, the generator) waits behind a perfect etalon (etalon-first).**

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* = exists but
inactive. *Recent sprints* = the last ~8 shipped; older history is archived (see Archive).

**Update protocol — LAW-02 (success is proven, never assumed):** log each item as
**INTENT** (what + its *verifiable success factors* / definition-of-done) → **perform** → then report
the **PROVEN RESULT** — the checks that actually passed (tests, `make ci`, the named postcondition) —
**never restate the intent as if it were the outcome**. An item moves to *Recent sprints / shipped*
**only when its success factors are verified**. Update at every transition. Stamp "Last updated" with
Melbourne local time.

---

## Recent sprints (most recent first)

- **Session 2026-06-24/25 — deliberation eval harness + model-drift gate (0.28.01→0.29.00).** *Proven
  results (merged to main, GitHub CI green both pushes):* (1) **Eval harness** (0.29.00) —
  `kernel/deliberation_eval.py` (`EvalCase`/`EvalScore`/`score_debate`/`run_eval`/`pass_rate`, kernel-pure)
  scores a debate against a manufactured answer key *without* trade outcomes (DL-23 Path B); trading cases
  live caller-side (`scripts/deliberation_eval.py`, pack wall). **1093 tests, 100% coverage.** (2) **EXP-003**
  records the build + an honest finding: gpt-5.5 catches *textbook* flaws blind, so grounding's measurable
  ROI is **Class-1** (our-implementation facts), not Class-2 — known *before* investing in DSPy. (3) **DL-24
  + Deliberation charter v0.2:** DSPy's first job reframed as a **model-drift firewall**; `model` is now a
  **GATED** parameter (a downgrade/side-grade must pass the eval — no silent report drift). *Next experiment
  queued: Class-1 case library + a sharper (LLM-judge) scorer to arm the firewall.*
- **Session 2026-06-24 — pipeline + governance + housekeeping (0.24.00→0.27.00).** *Proven results
  (all merged to main, CI green):* (1) **Alpaca primary OHLCV** (0.26.00) — batch, no per-symbol
  throttle. (2) **Chunked ingest** (0.27.00) — paced sub-batches reassembled into one batch; **1080
  tests, 100% coverage**. (3) **ADR-0013** continuous-improvement system (all state on the graph) +
  **P16 / S90–S95** specs. (4) **Experimentation** & **Housekeeping** charters (`ops/departments/…`)
  - **`librarian`** & **`tuner`** subagents (`.claude/agents/…`) + the **etalon** (`ops/agent-genesis.md`).
  (5) **Housekeeping:** research docs → folder-per-topic; CodeQL → self-contained `codeql/` tool; root
  swept; **~1.3 GB reclaimed** (2.0 G→719 M); merged branches pruned both ends (local 89→4, remote 51→9). (6)
  **Dependabot** auto-merge fixed (Actions can't approve PRs) — all 6 PRs merged, image-build green.
  *Captured: DL-15…DL-20.* *Not done (verified failing): a real trade — DL-17 run 3 = INCONCLUSIVE.*
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

**INTENT: perfect the trading-agents bundle until it is *etalon v0.1* (DL-19, `ops/agent-genesis.md`).**
On `main`, no active sprint branch. Success factors (the verifiable definition-of-done — each must be
*proven*, not asserted):

- **A real trade — ✅ DONE (proven 2026-06-24 21:09 AEST).** A clean 99-ticker batch
  (`quality ok returned=99/99`) flowed provider→scanner→analyst→PM→execution and **opened 5 positions**
  (C, QCOM, CSCO, AMD, INTC). Unblocked by the **validate-once fix** (0.28.01 — chunked ingest
  re-validates the reassembled batch once) + `sigma=8.0` + BK dropped + conservative pacing (chunk 10 /
  delay 70). *New finding:* the 5 names are 4 semis + 1 bank — **correlated concentration** the pipeline
  has no penalty for (the gap [quant-methods](research/quant-methods/quant-methods.md) Part 2/3 flags;
  what a Deliberation Challenger would attack). So: *trades cleanly, not yet wisely.*
- **Laws green.** Remaining gray law clauses → green with cited tests (ledger: provider 23/43, scanner
  18/39, PM 23/43, analyst 24/43, …).
- **No cages.** Each charter audited for the "a NEVER quietly became the solution" problem (DL-19) —
  rules out the unsafe without prescribing the answer.
- **CI green throughout** (`make ci` + GitHub) at every step.

**Architecture (DL-08): graph-as-queue / pull model.** Provider writes all data to Neo4j; other agents
poll the graph for unprocessed work. Full detail in `docs/design-log.md`.

## Next

*The "finish the bundle" backlog — what perfection still needs:*

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
- **DEFERRED behind a perfect etalon (etalon-first, DL-19):** CI-1..CI-6 (ADR-0013 machinery, S90–S95)
  · the bundle **generator** · the **Research & Solution-Design** bundle (DL-20). Do not start these
  until the bundle is demonstrably perfect — a copier of an imperfect reference only reproduces gaps.

## Workflow

Each sprint/chore on its own branch (`sprint-NN-<slug>`); merge to `main` is the deploy trigger. This
cycle the operator implements sprints end-to-end (code+tests+CI+commit). See `docs/sprints/README.md`.

## Parked

- 3 unmerged local branches (not in `main`; review or delete): `sprint-56-analyst-lm-master-dictionary`,
  `sprint-57-forecaster-sentiment-scorecard`, `sprint-69-provider-law-cycle`. Their features show
  complete, so likely stale leftovers — verify before deleting.

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
