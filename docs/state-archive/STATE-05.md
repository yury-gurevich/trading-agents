# Project State — Archive (STATE-05)

**Continuation of [STATE.md](../STATE.md).** This file holds the detail for **Sprints 102–126** — the
fleet arc's last two steps (S102 distributed 13-container run-through, S103 dispatcher cron that
made the platform self-driving), the DL-42 deliberation-prompt arc (S119 compile, S121 first
promotion), DL-44 broker reconciliation (S120), and the **DL-47 operations-dashboard arc in full**
(S123 fleet + infra, S124 glance-first verdict, S125 operator chat, S126 resume-from-stage +
deploy-currency judgement). Split out on **2026-07-22**, when STATE.md was trimmed back to a lean
live dashboard and the S128–S134 hardening run was promoted out of the header blob into Recent.
Earlier history: **S99–S118 + chores** → [STATE-04.md](STATE-04.md); **S77–96** →
[STATE-03.md](STATE-03.md); **S37–76** → [STATE-02.md](STATE-02.md); **S36 → P0** →
[STATE-01.md](STATE-01.md).

> *Entries below are verbatim from STATE.md's Recent section at the time of the trim (2026-07-22).*

---

- **S126 (DL-47 slice 5 FINAL, 0.69.00→0.70.00) — RUNS RESUME FROM A STAGE; DEPLOY CURRENCY IS
  JUDGED.** Resume is supersession, never deletion: a child
  `RunRequest` with a `RESUMES` edge links upstream artifacts (`LINKED_FROM`) and re-derives only
  the stages from the chosen point; operator-gated end-to-end (interpret → validate → primitive)
  with `CommandAudit` and a broker-consequence double-confirm for stages ≤ execution; dashboard
  stage cards carry "Resume from" controls posting the bounded command. `/deploy-fleet` now
  appends an append-only `DeployRecord`, and the dashboard judges deploy currency
  `current/behind/unverified` against observed fleet tags + the newest successful main image
  build (`GITHUB_TOKEN` absent → honest `unverified`). Bus health is tri-state — an unavailable
  Azure read renders `unverified`, never `unreachable`, and never flips the light. DL-46 recorded
  DECIDED ("C shipped in S126; A remains the end state"). Live proof: child of `sched-2026-07-13`
  reached 7/7 with only monitor/reporter re-derived and 0 broker orders; currency read **behind**
  (fleet `:s121`; main moved again to `a5bbb5f` during closeout and the judgement tracked it);
  bus `unverified` with credentials unset. Evidence + screenshots in
  `docs/reports/sprint-126-resume-and-tripwire/`; `make ci` 1566 passed / 5 skipped / 100%
  (planning-agent re-run on the exact tree). Codex-built; handback evidence completed and
  re-verified by the planning agent (see the sprint doc's Return notes). The merge integrated
  fixpack chores 0.69.01–0.69.05 (below): `public_message` carried into the split-out
  `projections_azure.py`, loud port bind + `ts()` timestamps kept alongside the github wiring
  and deploy-currency chip; `make ci` on the merge result 1569 passed / 5 skipped / 100%.
  **Merged `297354b`** (GitHub CI + image build + CodeQL all green). **DL-47 arc complete.**

- **Chore (0.69.04→0.69.05) — FLAG VIEWS HONOUR RESOLUTIONS.** Flag views join
  `FlagResolution`; resolved flags stop reading pending across the dashboard (`412dd82`,
  merged `a5bbb5f`). Recorded here at the S126 merge — the chore's own session predated this
  STATE entry.

- **Chores (0.69.02→0.69.04) — FIXPACK ITEMS 2, 7, 8 SHIPPED.**
  0.69.03: dead `compactSummary` client shim deleted — the hero renders server wording
  verbatim (one wording source). 0.69.04: shared `ts()` renders `yyyy-MM-dd HH:mm UTC`
  (decision: UTC, labeled) in the containers table, job card, vitals + hero next-fire, and
  log drawer; Alpaca login link (new tab, `noopener`) in the Positions panel header.
  PROVEN: `make ci` green each; live screenshot shows the readable stamps + the link.
  Backlog rows 2/7/8 closed; row 9 added (live bus test fails instead of skipping without
  the azure extra — importorskip guard needed).

- **Chore (0.69.01→0.69.02) — LOG DRAWER FOLLOWS THE SELECTED RUN (DRIFT-022 CORRECTED).**
  `/api/containers/<name>/logs` accepts `run=<id>`, resolves the day from the RunRequest,
  and queries that day's fleet window (`run_window`); unscoped or unresolvable falls back to
  the latest window and the payload says which via `scope`. The drawer sends the selected run
  and titles the window it shows. PROVEN: unit truth-table (run-scoped window bounds, bad-day
  fallback, unknown-run fallback) + `make ci` green + live Neon/Azure check (07-10 run returns
  the 07-10 22:25→00:30 window).

- **Chore (0.69.00→0.69.01) — FIXPACK 5+6 EARLY: SECURITY GATE UN-SILENCED; PORT BINDS LOUDLY.**
  The five error-level CodeQL alerts that failed the Security Findings gate on every PR are
  fixed at the source: dashboard statics serve from an import-time allowlist dict (request
  paths are only dict keys — no user input reaches a filesystem path or response header,
  closing 3× `py/path-injection` + `py/http-response-splitting`); Azure degradation messages
  render `AzureReadError.public_message` (a structured attribute), never `str(exc)`
  (closing `py/stack-trace-exposure`). `_ThreadingWSGIServer` sets `allow_reuse_address=False`
  plus a clear taken-port error, so a stale instance can never silently keep answering the
  browser (fixpack item 5's split-brain). PROVEN: `make ci` green; live checks — traversal
  paths 404, second instance on the same port exits loudly; gate-green proof lands with the
  next PR's Security Findings run after CodeQL rescans main.

- **S125 (DL-47 slice 4, 0.68.02→0.69.00) — THE OPERATOR IS AVAILABLE IN THE DASHBOARD.**
  `POST /api/chat` exposes only the existing bounded operator dispatch with dashboard-channel
  audit, selected-run grounding, explicit confirmation for gated commands, and deterministic
  quick asks. The dock has transcript and working states but becomes an honest read-only
  “chat is not connected” panel when graph/key binding is absent. Live Neon + Anthropic proof
  answered “how did we go last night” for `sched-2026-07-10`, and the cost ledger priced the
  final two-call exchange at A$0.008530 with zero untracked models. Evidence and retained audit-node
  inventory are in `docs/laws/functionality-checks.md` and
  `docs/reports/sprint-125-operator-chat/`; `make ci` 1531 passed / 6 skipped / 100%.

- **Chore (0.68.02→0.68.03) — COMPACT HERO WORDING + RESPONSIVE STAGE GRID.**
  Operator-directed UI pass landed from the shared working tree: the deterministic server-side
  hero summary is now terse operator language ("3 orders, 3 candidates" · "5 candidates below
  confidence bar (0.6)" — the floor value extracted from analyst rejection evidence into a new
  `confidence_bar` verdict field · "Attention needed: …" on faults); the hero names the selected
  **Run day** beside Next fire (closes the 07-12 "dates do not match" confusion); stage flow is
  a responsive wrapping grid; cache-busted assets. Tests updated with the wording.
  PROVEN: `make ci` all 9 steps green on the exact tree.

- **Chore (0.68.01→0.68.02) — WARNINGS DRILL-DOWN IS VISIBLE; DRIFT-021 RECORDED.**
  The verdict hero's "N warnings" dropdown opened invisibly: `.verdict-hero { overflow:hidden }`
  (needed to contain the stripe layer) clipped the absolutely-positioned list at the card's bottom
  edge. Fixed by dropping the hero's `overflow:hidden` and clipping the `::before` stripes with
  `border-radius:inherit` instead. PROVEN: headless-Edge screenshot of the open drill-down shows
  both warning rows fully readable below the card edge, stripes still inside the rounded corners;
  live server re-served the fixed CSS; `make ci` 1511 passed / 5 skipped / 100%. Same session's
  `/diagnose-feeds` on `sched-2026-07-10` root-caused the chronic all-four `*_degraded` notes
  (Finnhub free-tier rate limit × whole-feed fault boundary; key/vault/activation ruled out;
  provider faults invisible in Log Analytics after scale-to-zero) → **DRIFT-021 (OPEN)** in
  `docs/laws/drift-register.md` with the candidate fixes to package.
  Second fix, same branch: the local dashboard died after Neon dropped its idle Postgres
  connection — `PostgresGraphStore` held one connection forever, so every API 500'd
  (`psycopg.OperationalError: the connection is closed`) until restart. `_run` now retries a
  failed statement once on a fresh connection (owned connections only; single autocommit
  statements, so the retry is safe; injected test connections never replaced). PROVEN:
  `tests/test_graph_postgres_reconnect.py` (reconnect-once, replacement-also-dead raises,
  injected-never-replaced) + `make ci` green.
  Third fix, same branch: the dashboard served over single-threaded `wsgiref` — one hung Azure
  REST read (`/api/fleet`, stuck ≥30 min despite the urllib timeout; token acquisition has none)
  wedged the whole server, and past the listen backlog Windows refuses connections, so the run
  selector "did nothing". `__main__` now serves thread-per-request (`ThreadingMixIn`,
  daemon threads); shared state is safe (psycopg3 conns + MSAL are thread-safe, projections are
  pure reads). PROVEN: 6 parallel API hits all answered; headless screenshot of
  `?run=sched-2026-07-07` renders RUN PASSED / 1 order submitted (vs 07-10's NO_TRADE) —
  selector demonstrably changes the display.
  Fourth fix, same branch (operator-reported "why is it yellow"): transient Azure management-API
  failures no longer masquerade as warnings — the REST reader retries each read once
  (`_send_retry`), `AzureReadError` detail passes through to the infra `message`, the rail
  separates "couldn't verify — retrying" (idle, with a 45 s self-heal refetch) from genuine
  "attention" (warn), and a Failed dispatcher night on the control-plane card reads warn instead
  of idle; grant count labeled "to date". PROVEN: 16 targeted dashboard tests green (incl. new
  `test_dashboard_azure_retry.py` retry-once/raise-after table) + full `make ci` exit 0.

- **S124 (DL-47 slice 3, 0.67.00→0.68.00) — THE DASHBOARD ANSWERS AT A GLANCE.**
  A dominant binary RED/GREEN hero now follows the selected run with a deterministic sentence,
  next fire, and warning drill-down. Acceptance has a first-class pass-equivalent `NO_TRADE`
  verdict only for complete, fully evidenced confidence-floor rejection runs; genuine missing
  stages and unexplained silence remain FAIL. `/api/verdict?run=<id>` and `/bundle` share the pure
  projection; static/API jargon guards keep internal ids off the surface. Live proof:
  `sched-2026-07-10` = NO_TRADE/GREEN; absent-run diagnostic = RED before provider. Screenshots
  under `docs/reports/sprint-124-dashboard-verdict/`; `make ci` 1511 passed / 5 skipped / 100%
  (re-verified by the planning agent before merge, live NO_TRADE flip included). Merged `b9ed20e`.

- **S123 (DL-47 slice 2, 0.66.00→0.67.00) — FLEET + INFRASTRUCTURE ARE LEGIBLE.**
  One injectable Azure REST read port now projects all 13 Container Apps, `dispatcher-cron`,
  current replicas, real Log Analytics excerpts, and Cost Management service rows; graph-first
  Section II projects the six-stage nightly lifecycle, latest per-agent activation state, and the
  DL-36 ladder. `/api/vitals` drives all status-line facts and `/bundle` now carries bounded
  per-container logs + image tags. Hardware and ledger/model prices render in A$; USD LLM prices
  use the committed Commonwealth Bank Send-IMT snapshot (`1 USD=A$1.39450565`). Live Neon/Azure
  evidence: 13 apps + job all`:s121`, execution log drawer opened, A$0.001062 hardware MTD,
  2 pending Flags, broker↔graph in sync. Screenshots under
  `docs/reports/sprint-123-dashboard-fleet-infra/`;`make ci` 1489 passed / 5 skipped / 100%.
  Merged `2ad656e`.

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
