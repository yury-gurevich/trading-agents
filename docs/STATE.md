# Project State

**Last updated:** 2026-07-08 17:20 AEST · **Version:** 0.65.01 · **S121 merged — the compiled judge + challenger are the live deliberation champions.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + `STATE-01/02/03.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.

---

## Current focus

Since P14 the project runs as **etalon-first continuous improvement** (DL-19).
**The platform is self-driving in paper mode**: the DEPLOYED, STANDING fleet (13 Container Apps +
`dispatcher-cron` job, KEDA scale-to-zero windows, idle ≈ $0) places a calendar-gated `RunRequest`
at 22:30 UTC daily, runs graph-pull + served-over-Service-Bus on the Neon Postgres spine (ADR-0014),
reconciles holdings against the broker (DL-44), debates vetoes under compiled prompts (DL-42), and
proves `ACCEPTANCE PASS`. Pausing = disable the job + zero the scale windows (`docs/deployment.md`).
Completed arcs live in their sprint docs + archives: fleet (DL-35), credentials (DL-36), Postgres
migration (DL-43), deliberation quality (DL-41/42). Layer-3 acceptance 🟩 at the full S&P-500;
Layer-2 choreography 🟩 on a distributed run (S102).

## Recent (most recent first — detail in each sprint doc)

- **S121 (DL-42 resolution, 0.65.00→0.65.01) — FIRST ADR-0010 PROMPT PROMOTIONS ARE LIVE.**
  Compiled judge artifact `2026-07-08-s119-v4` promoted into `JUDGE_SYSTEM` and the challenger-only
  v5 recompile (`2026-07-08-s121-v5`) beat the promoted-judge champion (`100%/100%` vs `94%/94%`,
  stability 100%, firewall PASS) and was promoted into `CHALLENGER_SYSTEM`; prompts split into
  `kernel/deliberation_prompts.py` with artifact citations; **golden re-frozen 4→5 robust cases**
  (gained `fixed-fraction-size`); live default-prompt deliberation (no env opt-in) returned REVISE;
  final-default firewall PASS (gained `name-correlation`). Defender untouched — the hand-written
  prompt remains its champion. Evidence + transcripts in
  `docs/reports/sprint-121-judge-promotion-challenger-recompile/`. Codex-built, reviewed,
  `make ci` re-verified (1439 passed, 100%). Merged `5c5dd1c`. **The live veto path now debates
  under measured, compiled prompts.**

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

Older sprints — S99–S118 + chores → [STATE-04.md](STATE-04.md) · S77–96 → [STATE-03.md](STATE-03.md) ·
S37–76 → [STATE-02.md](STATE-02.md) · S36→P0 → [STATE-01.md](STATE-01.md); full index `docs/sprints/README.md`.

## Now

On `main` at 0.65.01, no active sprint branch and the packaged queue is empty (S119/S120/S121
all shipped 2026-07-08 on top of the self-driving fleet). Operational watch: the 22:30 UTC run is
the first with broker reconciliation + compiled deliberation prompts live — expect the pending
89-share CSCO fill and a qty-mismatch divergence Flag (the reconciliation working, not a defect).
The etalon north-star holds (DL-19):
remaining gray law clauses → green with cited tests; **every sprint ends with a real-environment
functionality check** (`docs/laws/functionality-checks.md`) + teardown. Each sprint/chore on its own
`sprint-NN-<slug>` branch; merge to `main` is the deploy trigger (rebuilds + pushes agent images).

## Next

- **DL-42 — SHIPPED (S119 0.64.00 + S121 0.65.01).** Compiled judge + challenger are the live
  champions; defender stays hand-written; golden re-frozen to 5 robust cases. Next layer when
  prioritized: EvoPrompt/TextGrad bake-off behind the same port (R003).
- **Deliberation as a reasoning/competence source (DL-39, DIRECTION)** — the transcript's *why*, not
  the verdict, is the asset: grade whether the expert model reasons at senior-analyst level and learn
  which parameters carry the decision. Assembles DL-31 (`--score`) + DL-09 + ADR-0010/CI-2; needs a
  research item + a live runway before packaging. Companion **DL-40 (parked)**: literacy-tiered verdict
  explanations (low/mid/high) as a `surfaces/` renderer, ruling single-sourced.
- **Remaining DL-36 hardening** — destructive executors (`rotate-credential`/`recreate-instance`) stay
  human-manual until a provider-specific write path + approval UI land; the diskcache CVE from the
  offline DSPy extra → hardening-backlog (not in runtime/images).
- **Deferred behind a perfect etalon (DL-19):** CI-1..CI-6 (ADR-0013, S90–S95) · the bundle **generator** ·
  ADR-0010 reusable predictor registry/promotion (first instance landed in S107) · P12 scorecard-run (needs
  a live news runway) · P13 cross-asset graph · `contracts/` substrate/pack split.

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
