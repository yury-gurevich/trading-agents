# Project State

**Last updated:** 2026-07-08 16:20 AEST · **Version:** 0.65.00 · **S120 merged — holdings reconciliation live; next: S121 (judge promotion + challenger recompile).**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + `STATE-01/02/03.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.

---

## Current focus

Since P14 the project runs as **etalon-first continuous improvement** (DL-19). Two active arcs (DL-35
reverses the etalon pause for the fleet workstream only):

- **Fleet-serve transport (DL-35) — ARC COMPLETE (S97–S100, S102, S103; S101 absorbed by
  S116–S118).** The DL-35 full-activation end state is reached and live: a Container Apps Job
  places a calendar-gated day-keyed `RunRequest` at 22:30 UTC, the 13-container fleet wakes on
  KEDA cron windows, runs graph-pull + served-over-Service-Bus on the Neon Postgres spine, proves
  `ACCEPTANCE PASS`, and scales back to zero. **The fleet + dispatcher-cron job are DEPLOYED and
  STANDING** (idle ≈ $0) — pausing = disable the job + zero the scale windows (runbook in
  `docs/deployment.md`).
- **Credential-security + bounded self-healing (DL-36) — ARC COMPLETE.** The master tests every
  credential before handover; failure → refuse + `Escalation` → LLM plans a bounded remediation →
  eval-gated auto-execute (one shot) → human. **A/B/C/D shipped (S104/S105/S106/S107)**; **S108** seeds
  Key Vault tested-before-insert (fail-closed) — the credential lifecycle is now closed at the source.

Layer-3 acceptance is 🟩 at the full S&P-500 (proven live 2026-06-26). The trade spine runs graph-pull
(DL-08). The fleet does **not** run distributed yet (S99–S103).

## Recent (most recent first — detail in each sprint doc)

- **S120 (DL-44, 0.64.00→0.65.00) — BROKER RECONCILIATION IS THE HOLDINGS REPAIR.**
  Broker port now exposes read-only holdings; execution run-start appends `BrokerPositionSnapshot`,
  refreshes pending broker-order status evidence, and raises loud supervisor-path `Flag`s on
  graph-vs-broker divergence; monitor adopts the latest fresh snapshot into
  `reconciled-from-broker` Positions; PM max-position/sector gates seed from active graph
  Positions. Live Neon/Alpaca check was read-only and branch-only: the production graph already
  held repaired AMD/CSCO/HPE/MRVL Positions from an earlier stale S120 live repair, so current-branch
  first/second passes wrote fresh snapshots with no new divergence Flag; the retained prior Flag
  states missing graph Positions for AMD/CSCO/HPE/MRVL, and raw verification found CSCO held at 88
  shares. The S103 CSCO broker id `632f0604-d36a-4f82-9c19-d621f19710ad` still reports `pending`,
  so `BrokerOrderStatus` evidence was appended and no terminal status was fabricated. Codex-built,
  `make ci` re-verified (1436 passed, 5 skipped, 100%). Reviewed and merged `6c0c0e9`; DRIFT-020 closes the CSCO double-buy.

- **S119 (DL-42, 0.63.00→0.64.00) — DELIBERATION ROLE PROMPTS ARE NOW COMPILED PREDICTORS.**
  Second real `PromptOptimizer` instance (ADR-0010): kernel `DeliberationPrompts` override
  (default byte-identical to the hand-written champions — pinned by test), kernel-pure artifact
  loader (`deliberation_prompt_artifacts.py`), DSPy compile pipeline + champion-vs-challenger
  comparison scripts, env opt-in in `scripts/deliberate.py`, per-role artifacts committed.
  Live report (72 debate + 72 scorer calls, GPT-5.5 debaters / Opus judge; transcripts under
  `docs/reports/sprint-119-deliberation-roles/`): **judge artifact improves** (94%/94% pass vs
  78%/83%, stability 100% vs 75%), defender flat, **challenger artifact regresses** (61%) — the
  per-role gating decision earned its keep. All four firewall checks PASS, `regressed: none`.
  **No default flipped — promotion operator-held; operator directed resolution "sooner rather
  than later" → S121 packaged** (promote judge, recompile challenger, golden re-freeze).
  Codex-built, reviewed, `make ci` re-verified (1421 passed, 100%). Merged `353d983`.

- **S103 (fleet arc FINAL, 0.62.00→0.63.00) — THE PLATFORM IS SELF-DRIVING (paper mode).**
  Dispatcher cron shipped: pure calendar-gated decision core
  (`orchestration/scheduled_dispatch.py` — provider NYSE calendar via a small port, day-keyed
  `sched-YYYY-MM-DD` run_id, `CalendarWindowExceededError` past the 2027 holiday table instead of
  silent weekday fallback), thin fail-loud job entrypoint (`scripts/dispatch_scheduled_run.py`,
  as_of = UTC today, DSN never printed), universe = committed sp100 file via the shared
  `load_universe_file()` (run_local now uses it too). Infra: `dispatcher-cron` Container Apps Job
  (`30 22 * * *` UTC) + KEDA cron scale windows on all 13 apps (master 22:25, agents 22:30, close
  00:30 UTC). Live (evidence in the sprint doc + `functionality-checks.md`): manual fire placed
  `sched-2026-07-08` → distributed chain to Snapshot → **`ACCEPTANCE PASS`** (99/99 tickers, 1
  CSCO paper buy filled); second fire merged to `run_request_count=1`; injected 2026-07-04 →
  clean skip, 0 RunRequests; all 13 apps at 0 replicas after the window; teardown to
  `remaining_sched_nodes=0/edges=0` with fleet/job/registry/topics standing. Codex-built,
  reviewed, `make ci` re-verified (1404 passed, 100%). Merged `6caa2f6`. **DL-35 end state
  reached: cron fires → fleet wakes → runs → proves acceptance → sleeps.**

- **S102 (fleet arc, 0.61.00→0.62.00) — THE FLEET IS PROVEN DISTRIBUTED.** Part A: env-selected
  serve transport (`kernel/serve_transport.py::consumer_from_env` — Service Bus consumer when a
  connection string is configured, `LocalRequestConsumer` otherwise; all five served entrypoints
  compose through it), `deploy-agents.ps1 -Tag`, manual-tag image builds, separate-process
  claim-check request script. Part B (live, evidence in the sprint doc +
  `functionality-checks.md`): 13 Container Apps on `:s102` GHCR images, **all 12 agents activated**
  with grants in Postgres, one `RunRequest` (`s102-dist-20260707T1530Z`) ran
  provider→…→Snapshot **across containers** with 3 real Alpaca-paper orders, `OBSERVATORY OK` +
  **`ACCEPTANCE PASS`** on the distributed run, five control-plane round-trips over Service Bus
  into separate containers. Ledger **Layer 2 (choreography) 🟩**. Four live-only defects fixed with
  cited tests (DRIFT-016..019 — incl. execution entrypoint hard-coding `PaperBroker`; Alpaca paper
  had never run in-container before). Teardown: graph swept to `remaining_s102_artifacts={}` (33
  edges/58 nodes), disposable reply topics gone, **all 13 Container Apps deleted** (cost stop);
  activation registry rows + served request topics stay as production config. Codex-built,
  reviewed, `make ci` re-verified (1393 passed, 100%). Merged `3049955`. **Fleet arc remaining:
  S103 (dispatcher cron) only.**

- **S100 (fleet arc, 0.60.01→0.61.00)** — Azure Service Bus **receive half** shipped:
  `kernel/bus_azure_receiver.py` behind the `RequestConsumer` protocol, claim-check request
  resolution + claim-checked replies, complete/abandon/dead-letter semantics, optional SDK imports,
  `AzureServiceBusBus.request_consumer(...)` factory. Codex-built, reviewed, `make ci` re-verified
  (1385 passed, 100%). Live smoke against `trading-agents-bus`; teardown `remaining_s100_topics=[]`.
  Merged `2e50a3d`. **Fleet arc remaining: S102 (13-container run-through — refresh draft first, now
  on Postgres) → S103 (dispatcher cron).**

- **S118 (DL-43 step 3, 0.60.00→0.60.01) — MIGRATION COMPLETE: one store, one truth.** Neo4j is out
  of the runtime: kernel adapter/tests/`neo4j` dep deleted (fresh sync uninstalls it;
  zero-import grep clean), `NEO4J_URI`-only env raises the explicit ADR-0014 error (no silent
  fallback), `aura.ps1`/`compare_aura.py`/`neo4j_crud.py`/stale helpers retired, Neo4j survives only
  as the opt-in `workbench` compose profile (ADR-0008 analysis scope). Docs/laws swept to
  Postgres-only. Live: `POSTGRES_DSN`-only slice on Neon asserted `PostgresGraphStore`, durable write
  verified raw, teardown 0/0; negative check proved the ADR-0014 error. **Aura `bce05bd6` DELETED by operator 2026-07-07 (waived grace window) — DL-43 fully closed, zero cloud Neo4j remains.** `make ci` re-verified (1374
  passed, 100%). Merged `ce53230`. **Rollback = git revert + redeploy (GHCR images persist).**

- **S117 (DL-43 step 2, 0.59.00→0.60.00) — POSTGRES IS THE SYSTEM OF RECORD (ADR-0014 supersedes
  ADR-0001).** `postgres-dsn` seeded to `trading-agents-kv` via the S108 tested-before-insert path
  (probe passed, read-back equal, DSN never printed); composition + container defaults flipped to
  `POSTGRES_DSN` (the temporary `NEO4J_URI` rollback was removed by S118); `deploy-agents.ps1` runs `alembic
  upgrade head` before fleet start; `DEP-POSTGRES-01` probe green; ADR-0008 amended to
  analysis scope; laws/architecture swept. Live: S99-style served slice on **Neon** asserted
  `PostgresGraphStore`, durable rows verified from a separate raw connection (36 nodes/26 edges),
  teardown to 0/0. `make ci` re-verified (1383 passed, 100%). Merged `d6776ec`.

- **S116 (DL-43 step 1, 0.58.00→0.59.00)** — `PostgresGraphStore` shipped: psycopg 3 adapter over the
  6-method port with **alembic-owned schema** (`infra/migrations/0001_spine`), append-only JSONB merge
  (`EXCLUDED.props || nodes.props` + schema_version guard), recursive-CTE traversal, `POSTGRES_DSN`
  selector (Postgres wins; temporary Neo4j fallback later removed by S118), fake-psycopg unit suite + env-gated Neon tests +
  `scripts/pg_teardown.py`. Codex-built, reviewed, `make ci` re-verified (1379 passed, 100%). Live
  check on **Neon free (Sydney)**: alembic `0001_spine` applied, backend suite 7 passed, pipeline
  slice asserted `PostgresGraphStore` + rendered veto-context lineage, teardown to nodes=0/edges=0,
  DSN never printed. Merged `5f11b93`. **The spine can now run on Postgres; S117 closes the fleet
  default flip on its branch.**

- **S115 (qlib Q5 part B, 0.57.00→0.58.00) — THE Q5 LOOP IS CLOSED.** Factor shadow signal: additive
  `forecast_factor` capability (forecaster contract 0.5.0), factor math duplicated island-clean with a
  **parity test pinning it to S113 catalogue values**, no-lookahead fence, OFF by default (empty
  `factor_name` → clean disabled response, zero graph writes), generic `model_id` scorecard covers
  factor predictions (`promotion_eligible=False`), locked laws untouched (FORE-NEV-02 cited). Live
  check: real Tiingo bars (AAPL, MSFT) → 2 `ShadowPrediction`s under `factor-s115-live-momentum-60` on
  Aura, scorecard `sample_size=2`, default-off wrote 0 nodes, teardown to baseline 0. `make ci`
  re-verified locally (1370 passed, 100%). Merged `ab66caf`. Every Q5 stage now exists and is governed:
  propose (S113) → approve (operator) → shadow (S115) → scorecard → promote/kill (operator on P10
  rails). **Moonshot #3 concrete; LLM's only power remains nomination.** (Merge also carried R002
  Postgres migration plan + DL-43 + Neon host decision — committed on-branch by shared-dir accident.)
- **S113 (qlib Q5 part A, 0.56.00→0.57.00)** — governed factor proposal: pure researcher factor
  catalogue (`momentum`/`mean_reversion`/`volatility_rank`, `tunable`-bounded), strict
  `validate_selection` enum guardrail (reject-not-clamp, fail-open `None`), additive `ProposedFactor` +
  `FactorProposal` (researcher contract 0.3.0), LLM selection **only** in `scripts/mine_factors.py`
  (`external_io=()` intact), S112 harness reused unchanged, no-lookahead fence test. Codex-built,
  reviewed, `make ci` re-verified locally (1358 passed, 100%). Live check: 100-ticker Tiingo export
  (DL-37), GPT-5.5 selected in-catalogue `momentum lookback=60`, evidence populated +
  `FactorProposal.model_validate` round-trip; forced `invented_factor` failed open (no output). Merged
  `3ec2d9e` (CI/CodeQL/image-build green, incl. Dependabot #29–31 bumps). **The LLM now nominates
  factors under a hard catalogue guardrail; part B (S115: approved factor → shadow → scorecard →
  promote/kill) closes the Q5 loop.**
- **S114 (DL-41, 0.55.01→0.56.00)** — complete deliberation evidence: additive `GateOutcome` +
  `OrderIntent.gate_report` (PM contract 0.2.0); PM emits sizing / min-order / max-positions / cash /
  sector-concentration / names-per-sector / reward-risk outcomes; `veto_context.py` split
  (`veto_context_pm.py`) and the veto context now renders **every enforced gate as value + explicit
  PASSED/FAILED**, incl. confidence-floor and stop-vs-regime/ATR, degrading to stated "unavailable"
  lines (fail-open intact). Completeness test fences regressions. Codex-built, reviewed, `make ci`
  re-verified locally (1346 passed, 100%). Live check: seeded PMRun through the real veto stage on Aura
  — every gate rendered with explicit outcome incl. `max_sector_pct`; 6 nodes torn down to baseline 0.
  Merged `6d9e9d0`. **The challenger-veto now debates complete evidence (DL-41 closed); DL-42 (DSPy on
  the reasoning) is the next layer.**
- **S109 re-run (0.55.00→0.55.01, `chore-s109-opus-refreeze`)** — cleared the deferred S109 proofs with a
  funded Anthropic key: live check with the **real Opus judge** (`claude-opus-4-8`) → `VERDICT: REVISE`;
  **golden re-frozen** with the Opus judge (robust-passing `{alpha158-weight-zero, calendar-staleness,
  lightgbm-shadow, pooled-sigma}`, n=3); **firewall** `--check gpt-5.4` → `PASS` (no false trip). Found +
  fixed a harness bug: `gpt-5` challenger turns came back **empty** — reproduced as `finish_reason=length`,
  2000/2000 tokens on hidden reasoning (need 2560); the OpenAI adapter shared one `max_completion_tokens`
  pool and ignored the budget it was handed. Fix: adapter honours `max_tokens`; debaters 8000, judge 2000.
  Proof it mattered: at the fixed budget `gpt-5`'s homogeneous verdict **flipped UPHOLD→REVISE** (the muted
  challenger had been changing the outcome). `make ci` 100% (1339 passed). Drift-firewall baseline is now
  the real-Opus one. **S109 fully closed.**
- **S112 (qlib Q3, 0.54.01→0.55.00)** — researcher backtest evidence: additive
  `BacktestEvidence` contract field (researcher contract 0.2.0), pure no-lookahead walk-forward
  harness in `agents/researcher/domain/` (next-close fills, turnover slippage, ≥30% holdout), three
  bounded researcher backtest tunables, and `scripts/backtest_proposal.py` with a two-entry analyst
  signal catalogue (`analyst.rsi_period`, `analyst.bollinger_window`) that fails open for unsupported
  parameters. Codex-built on branch, `make ci` 100%. Live check: DL-37 Tiingo export via the S111
  exporter using the fixed S110 100-ticker list (100,400 rows; zero duplicate `(ticker,date)` keys);
  `analyst.rsi_period` 14→21 produced populated full/holdout evidence and the proposed JSON
  round-tripped through `BacktestEvidence.model_validate`. Reviewed and merged `feb7f87`
  (CI/CodeQL/image-build green). **Qlib Q3 complete — Q5 (governed factor mining) is the last
  workflow phase and is now unblocked.** (Also in this window: torch pinned to CPU wheels, PR #28
  0.54.01 — forecaster image build 4.6–8.1 min → 1.6 min, deploy wall ~1m35s.)
- **S111 (qlib Q1c, 0.53.01→0.54.00)** — rolling retrain + IC-decay trigger: committed
  `scripts/export_tiingo_bars.py` (paced/resumable Tiingo DL-37 raw-history export, bounded sync
  backoff for transient 5xx/timeouts), pure `retrain_policy` (fail-safe decay +
  champion-vs-challenger verdict), `scripts/retrain_return_model.py` (dry-run default; `--force`
  trains challenger; `--apply` archives incumbent then installs challenger only on a positive
  verdict). Codex-built, reviewed, `make ci` 100 %. Live check: 100 Tiingo tickers × 1,004 bars,
  fresh incumbent, dry-run verdict `swap=False`, scratch apply proof `swap=True` with archive hash
  intact. Notes: Alpaca is the primary runtime/batch OHLCV path; Tiingo is the cheap fallback +
  DL-37 raw-history lineage source (ADR-0006 amendment queued). **The self-improvement loop is now
  mechanical: decay measured → retrain on evidence → operator holds `--apply`.**
- **chore-enforce-security-gate (PR #27)** — Security Findings gate flipped **report-only →
  ENFORCING**: a NEW error-severity code-scanning finding now fails the PR
  (`--fail-on-code-scanning-error`). Baseline refreshed post-clearance (81 lines → 1 entry: the
  operator-accepted diskcache Dependabot advisory; policy embedded). PROVEN: toolset run locally —
  clean state exit 0, synthetic new error exit 1; PR #27's own `gate` check passed enforcing in CI.
  Accept-a-finding path documented in the workflow header (dismiss-with-reason preferred).
- **chore-codeql-fixes (0.53.00→0.53.01, PR #26 `b61aff4`)** — CodeQL security report cleared to
  **0 open alerts**: the 3 error-severity `py/unsafe-cyclic-import` alerts fixed structurally
  (`RemediationAttempt` → new cycle-free `agents/master/remediation_records.py`; CodeQL re-scan marks
  them `fixed`); the other 68 triaged as false positives / intentional idioms (fault_boundary
  sentinels, attribute docstrings, string-form casts, pytest.raises flows, deliberate lazy imports)
  and **dismissed with per-family recorded reasons** — not "fixed" by deleting working idioms.
  `make ci` 100 % + CI/CodeQL/image-build green on `main`. Unblocks enforcing the security-findings
  gate (was report-only pending these 3 errors — operator decision).
- **S110 (qlib Q1b, 0.52.00→0.53.00)** — forecaster **signal evaluation battery**: rank IC (Spearman),
  quantile group returns + top-bottom spread + monotonicity, per-date cross-sectional IC mean/std/IR,
  rank-autocorrelation stability; OOS-only multi-horizon CLI (`scripts/evaluate_return_model.py`).
  Codex-built, reviewed, `make ci` 100 % + **live Tiingo check** (DL-37 re-scope proven: 100 tickers ×
  877 bars; booster retrained Tiingo-sourced). Honest weak-signal baseline, best at h=20 (IC 0.017,
  rank-IC 0.023, IC-IR 0.27) — the Q1c retrain-trigger baseline. Also: live-discovered LightGBM
  NumPy-input fix + `docs/laws/tiingo-usage-limits.md` preflight law. Merged `0818679`.
- **S109 (ADR-0010, 0.51.00→0.52.00)** — heterogeneous deliberation: GPT-5.5 debaters + a separate **Opus**
  debate judge (`DELIBERATION_JUDGE_*` env); veto now debates a **grounded** proposition (fixes S96).
  `make ci` 100%. **⚠ Functional via a temporary gpt-5 judge; real-Opus check + golden re-freeze DEFERRED
  (billing, operator-accepted) — re-run Sun 2026-07-05.** Merged `81c3922`.
- **S99 (fleet arc, 0.50.00→0.51.00)** — forecaster/curator/researcher served over `serve_loop` (S98
  pattern); `idle_loop` deleted from `kernel/bootstrap.py` + guard test; clause-cited serving tests
  (`FORE-TRG-02` etc.). Codex-built, reviewed, `make ci` 100% + live Aura check (durable artifacts from a
  separate connection; trade spine untouched; 35 nodes torn down to 0). **In-process fleet functionally
  complete.** Merged `f68457b`.
- **S108 (DL-36 family, 0.49.00→0.50.00)** — `.env`→Key Vault seeder, **tested-before-insert**: a secret
  enters the vault only after a live working-check passes; failing/empty/unverifiable creds are rejected
  (fail-closed), dry-run by default. Also fixed a latent secret-map bug (provider Alpaca-secret env var).
  Codex-built, reviewed, `make ci` 100% + **live check** on vault `trading-agents-kv`. Merged `bfd7cf8`.
- **S107 (DL-36 D, 0.47.00→0.49.00)** — eval-gated auto-remediation execution: DSPy behind ADR-0010's
  `PromptOptimizer` port gates the selector; safe executors run the `test→execute→production→documentation`
  loop (one automatic shot then human); + thread-safe activation IDs + composition-root wiring. Codex-built,
  reviewed, `make ci` 100% + **live GPT-5.5** check on Aura (selector 5/5, gate trips, refetch heals). Merged `f980965`.
- **S106 (DL-36 C, 0.47.00)** — bounded-catalogue LLM remediation planner (enum guardrail, fail-open,
  configurable `auto_remediation_scope`); plans + gates, never executes. Live GPT-5.5 check. Merged `8f74bfa`.

Older sprints — DL-36 A/B (S104/S105) in the arc above; S77–96 → [STATE-03.md](STATE-03.md) · S37–76 →
[STATE-02.md](STATE-02.md) · S36→P0 → [STATE-01.md](STATE-01.md); full index `docs/sprints/README.md`.

## Now

On `main` at 0.63.00, no active sprint branch (S103 reviewed and merged — **the fleet arc is
complete; the platform runs itself daily in paper mode**). The etalon north-star holds (DL-19):
remaining gray law clauses → green with cited tests; **every sprint ends with a real-environment
functionality check** (`docs/laws/functionality-checks.md`) + teardown. Each sprint/chore on its own
`sprint-NN-<slug>` branch; merge to `main` is the deploy trigger (rebuilds + pushes agent images).

## Next

- **DL-42 — DSPy-compile the deliberation roles: S119 handover packaged 2026-07-08, Codex-ready**
  (`docs/sprints/sprint-119-dspy-deliberation-roles.md`). Decisions recorded in the doc (LAW-06):
  compile all three roles but gate/promote each independently (judge scored objectively on known
  verdicts); runtime never imports DSPy (artifact-file opt-in via env, byte-identical default);
  metric = Class-1 pass-rate + `score_understanding` + n=3 verdict stability, golden firewall as
  hard veto; **promotion stays operator-held** — the sprint ships artifacts + the
  champion-vs-challenger report only. Version 0.63.00 → **0.64.00** (feat).
- **Deliberation as a reasoning/competence source (DL-39, DIRECTION)** — the transcript's *why*, not
  the verdict, is the asset: grade whether the expert model reasons at senior-analyst level and learn
  which parameters carry the decision. Assembles DL-31 (`--score`) + DL-09 + ADR-0010/CI-2; needs a
  research item + a live runway before packaging. Companion **DL-40 (parked)**: literacy-tiered verdict
  explanations (low/mid/high) as a `surfaces/` renderer, ruling single-sourced.
- **Remaining DL-36 hardening** — destructive executors (`rotate-credential`/`recreate-instance`) stay
  human-manual until a provider-specific write path + approval UI land; the diskcache CVE from the
  offline DSPy extra → hardening-backlog (not in runtime/images).
- **S121 — judge promotion + challenger recompile (S119 resolution): branch closeout complete;
  awaiting operator review/merge** (`docs/sprints/sprint-121-judge-promotion-challenger-recompile.md`).
  Compiled Judge artifact `2026-07-08-s119-v4` is now default `JUDGE_SYSTEM`; the golden was
  re-frozen from 4 to 5 robust cases; one challenger-only recompile produced
  `2026-07-08-s121-v5`, which beat the promoted-judge champion (`100%/100%` vs `94%/94%`,
  stability `100%` vs `100%`, firewall PASS) and was promoted into `CHALLENGER_SYSTEM`.
  Defender untouched. Version **0.65.01**. Not merged.
- **S120 — broker reconciliation (DL-44): shipped on main**
  (`docs/sprints/sprint-120-broker-reconciliation.md`, operator: "straight away after the previous
  work"). **The first unattended fire HAPPENED (2026-07-07 22:30 UTC) and worked** — full lineage
  to Snapshot on Neon, CSCO buy 89 accepted at 22:34 — **and exposed DL-44**: teardowns had
  deleted the Position/Fill rows for holdings the paper account still has, so the solo run
  re-bought CSCO on top of 88 held shares, and after-hours `Fill`s stay `pending` forever. Policy
  (DL-44): broker = truth for holdings, graph = truth for lineage; execution-owned run-start
  reconciliation (`BrokerPositionSnapshot`, loud divergence Flag), monitor adopts broker truth,
  teardown discipline amended. The S120 branch live check proved the repaired graph idempotent and
  retained production Positions/account holdings. Version **0.65.00**. Paper account during the
  check: 4 positions (AMD/CSCO/HPE/MRVL); CSCO broker order `632f0604...` still reported pending.
- **Deferred behind a perfect etalon (DL-19):** CI-1..CI-6 (ADR-0013, S90–S95) · the bundle **generator** ·
  ADR-0010 reusable predictor registry/promotion (first instance landed in S107) · P12 scorecard-run (needs
  a live news runway) · P13 cross-asset graph · `contracts/` substrate/pack split.

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
