# Project State

**Last updated:** 2026-07-05 14:56 AEST · **Version:** 0.55.01 · **`make ci` + GHCR image build green on `main`.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + `STATE-01/02/03.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.

---

## Current focus

Since P14 the project runs as **etalon-first continuous improvement** (DL-19). Two active arcs (DL-35
reverses the etalon pause for the fleet workstream only):

- **Fleet-serve transport (DL-35)** — give the control-plane agents a real serve/consume path so the
  distributed fleet can run. **S97–S99 shipped — zero `idle_loop()` remains; the in-process fleet is
  functionally complete.** S100–S103 remain (Service Bus receiver is next; refresh its pre-S104 draft first).
- **Credential-security + bounded self-healing (DL-36) — ARC COMPLETE.** The master tests every
  credential before handover; failure → refuse + `Escalation` → LLM plans a bounded remediation →
  eval-gated auto-execute (one shot) → human. **A/B/C/D shipped (S104/S105/S106/S107)**; **S108** seeds
  Key Vault tested-before-insert (fail-closed) — the credential lifecycle is now closed at the source.

Layer-3 acceptance is 🟩 at the full S&P-500 (proven live 2026-06-26). The trade spine runs graph-pull
(DL-08). The fleet does **not** run distributed yet (S99–S103).

## Recent (most recent first — detail in each sprint doc)

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
S36→P0 → [STATE-01.md](STATE-01.md); full index `docs/sprints/README.md`.

## Now

On `main`, no active sprint branch (S112 reviewed and merged). The etalon north-star holds (DL-19):
remaining gray law clauses → green with cited tests; **every sprint ends with a real-environment
functionality check** (`docs/laws/functionality-checks.md`) + teardown. Each sprint/chore on its own
`sprint-NN-<slug>` branch; merge to `main` is the deploy trigger (rebuilds + pushes agent images).

## Next

- **🔴 PRIORITY — S114 complete the deliberation evidence (DL-41).** Money is spent on the veto's
  output, so its evidence must be complete. Live `orchestration/veto_context.py` already renders
  confidence + `base_min_confidence` + regime/scanner/market lineage, but (1) gate **outcomes** are
  implicit (values shown, pass/fail not stated) and (2) **PM risk gates are absent** — `max_sector_pct`
  concentration, sizing basis, held-position context are computed but not rendered (needs the PM to
  emit gate outcomes as an additive `OrderIntentSet` field). Fix: render every gate as value+outcome,
  thread PM gate results, explicit stop-vs-ATR; split `veto_context.py` (195/200); add a completeness
  test. **Package S114 and execute before S113.** DL-41 holds the spec.
- **Qlib Q5 part A — S113 governed factor proposal — PACKAGED, ready for Codex** (now behind S114). Handover written
  (`docs/sprints/sprint-113-governed-factor-proposal.md`): bounded factor catalogue + LLM proposes an
  in-catalogue factor (enum-guarded, fail-open, LLM only in composition root) → S112 walk-forward scores
  it → `FactorProposal` + `BacktestEvidence` into the review queue. LLM never drives; researcher
  `external_io=()` intact. Version 0.55.01 → **0.56.00** (feat). **S114 (part B, later):** approved
  factor → live shadow signal → scorecard → promote/kill (P10 registry). R001 addendum + DL-39 hold why.
- **Deliberation as a reasoning/competence source (DL-39, DIRECTION)** — the transcript's *why*, not
  the verdict, is the asset: grade whether the expert model reasons at senior-analyst level and learn
  which parameters carry the decision. Assembles DL-31 (`--score`) + DL-09 + ADR-0010/CI-2; needs a
  research item + a live runway before packaging. Companion **DL-40 (parked)**: literacy-tiered verdict
  explanations (low/mid/high) as a `surfaces/` renderer, ruling single-sourced.
- **Remaining DL-36 hardening** — destructive executors (`rotate-credential`/`recreate-instance`) stay
  human-manual until an Azure/Aura write path + rollback + approval UI land; the diskcache CVE from the
  offline DSPy extra → hardening-backlog (not in runtime/images).
- **Fleet arc S100–S103** — **S100 Service Bus receiver: handover Codex-ready + namespace `trading-agents-bus`
  provisioned & live-verified (`infra/servicebus.bicep`); unblocked to build** (implement the receive half of
  `bus_azure.py` behind the `RequestConsumer` protocol) · permanent graph store (S101 — **reframed by
  DL-38 to "provision the permanent *spine*"**: agent memory becomes a bundle-declared concern, the shared
  store shrinks to lineage + work-state; fold into the S101 refresh) · 13-container run-through +
  distributed acceptance (S102) · dispatcher cron (S103). Refresh the S101–103 pre-S104 drafts before executing.
- **Deferred behind a perfect etalon (DL-19):** CI-1..CI-6 (ADR-0013, S90–S95) · the bundle **generator** ·
  ADR-0010 reusable predictor registry/promotion (first instance landed in S107) · P12 scorecard-run (needs
  a live news runway) · P13 cross-asset graph · `contracts/` substrate/pack split.

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
