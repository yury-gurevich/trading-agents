# Project State — Archive (STATE-04)

**Continuation of [STATE.md](../STATE.md).** This file holds the detail for **Sprints 99–118 (and the
S109 re-run + security chores)** — the fleet-serve arc's receive half (S99/S100), the qlib workflow
adoption (S110–S113, S115: evaluation battery, rolling retrain, backtest evidence, governed factor
mining), the DL-41 complete-deliberation-evidence fix (S114), the DL-36 credential arc close
(S106–S108), and the DL-43 Postgres migration trilogy (S116–S118) that made PostgreSQL the system
of record and deleted cloud Neo4j. Split out on 2026-07-08 when STATE.md was trimmed back to a lean
live dashboard. Earlier history: **S77–96** → [STATE-03.md](STATE-03.md); **S37–76** →
[STATE-02.md](STATE-02.md); **S36 → P0** → [STATE-01.md](STATE-01.md).

> *Entries below are verbatim from STATE.md's Recent section at the time of the trim (2026-07-08
> 17:20 AEST). "Fleet arc remaining" notes inside entries are historical — the arc completed with
> S102/S103 (see STATE.md Recent).*

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
