# Project State

**Last updated:** 2026-07-10 18:48 AEST · **Version:** 0.67.00 · **S123 COMPLETE ON BRANCH — live fleet/infra/log/cost dashboard evidence captured; pending merge.**

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

- **S123 (DL-47 slice 2, 0.66.00→0.67.00) — FLEET + INFRASTRUCTURE ARE LEGIBLE.**
  One injectable Azure REST read port now projects all 13 Container Apps, `dispatcher-cron`,
  current replicas, real Log Analytics excerpts, and Cost Management service rows; graph-first
  Section II projects the six-stage nightly lifecycle, latest per-agent activation state, and the
  DL-36 ladder. `/api/vitals` drives all status-line facts and `/bundle` now carries bounded
  per-container logs + image tags. Hardware and ledger/model prices render in A$; USD LLM prices
  use the committed Commonwealth Bank Send-IMT snapshot (`1 USD=A$1.39450565`). Live Neon/Azure
  evidence: 13 apps + job all `:s121`, execution log drawer opened, A$0.001062 hardware MTD,
  2 pending Flags, broker↔graph in sync. Screenshots under
  `docs/reports/sprint-123-dashboard-fleet-infra/`; `make ci` 1489 passed / 5 skipped / 100%.
  Branch complete, pending operator merge.

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

On `sprint-123-dashboard-fleet-infra` at 0.67.00; **S123 is complete and live-proven on its branch**
(Sections I/II, real per-container logs, A$ hardware/LLM cost meters, `/api/vitals`, bundle
logs/images) and awaits operator merge. **S122 remains shipped** (`820b8c9`). The
07-08 deploy-gap incident + same-day repair (fleet → `:s121`, stray CSCO order cancelled) is
recorded in design-log **DL-46**; the 07-09 run outcome (reconciliation proven; no-trade
`ACCEPTANCE FAIL`) is under Watch outcome in Next.
The etalon north-star holds (DL-19):
remaining gray law clauses → green with cited tests; **every sprint ends with a real-environment
functionality check** (`docs/laws/functionality-checks.md`) + teardown. Each sprint/chore on its own
`sprint-NN-<slug>` branch; merge to `main` is the deploy trigger (rebuilds + pushes agent images).

## Next

- **DL-47 — operations dashboard (ACTIVE ARC).** **S122 SHIPPED 2026-07-10 (0.66.00, merged `820b8c9`)** — Section III run view. **S123 COMPLETE ON BRANCH (0.67.00)** — Sections I/II, Azure REST read port, real logs/images, A$ costs, and live vitals; LAW-02 row + screenshots captured. Next: S124
  (resume-from-stage — Airflow clear+downstream over graph-pull artifacts — + the DL-46 tripwire),
  S125 (two-tier chat: bounded operator agent + **repair agent** with repo access consuming the
  `/bundle` context — investigates via the **pre-defined skill catalogue** (7 skills shipped
  2026-07-10 at `.claude/skills/`: diagnose-run/-feeds, check-/deploy-fleet, reconcile-broker,
  resume-run, audit-costs — usable in any Claude Code session today), prepares a fix as branch+PR
  only, rebuilds containers via the DL-46 deploy machinery; DL-47 req. 11–12). Design spec committed:
  `docs/design/dashboard-mockup.html` (interactive; built from the real 07-08/07-09 runs).
- **Watch outcome (2026-07-09 22:30 UTC run, verified 2026-07-10):** cron fired (3/3 nights),
  7/7 stages on `:s121`; **S120 reconciliation proven live** — critical divergence Flag raised
  exactly as predicted (CSCO 88→177 + missing BAC/WFC), monitor adopted broker truth (graph now
  matches broker, 6 positions), pending-fill refresh stamped all 4 stale Fills. **But
  `ACCEPTANCE FAIL`** — a legitimate no-trade day (all 5 candidates below the 0.600 regime floor)
  trips the hard `analyst.scored ≥ 1` / `pm.evaluated ≥ 1` floors: gate semantics need a no-trade
  verdict (candidate drift item, operator to prioritize). Contributing: all four enrichment feeds
  (fundamentals/news/sectors/earnings) ran degraded in-fleet — investigate why (secrets? rate
  limits at 22:30?). The pending critical Flag awaits operator ack.
- **DL-46 — deploy gap (OPEN, needs operator decision):** merge-to-main rebuilds images but the
  tag-pinned fleet doesn't move; pick CI-deploy step vs `:latest` pinning vs a fleet-behind
  tripwire (leaning tripwire now, CI-deploy as end state; the tripwire lands naturally on the
  S124 dashboard slice). See design-log DL-46.
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
