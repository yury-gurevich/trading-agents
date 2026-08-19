# Project State

**Last updated:** 2026-08-19 19:50 AEST · **Version:** 0.90.15 · **Fleet: `s181`** · **ONE CLEAN RUN: `verify-2026-08-19-clean-2` returned 9/9 real debates, 0 fail-opens and `deliberation_status=applied` — the veto bound fully for the first time. S181 closed and proven.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + [`state-archive/`](state-archive/INDEX.md) `STATE-01…07.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.
**Size rules**, after this file reached 574 lines with a **112 KB header line**: keep it **under 200
lines**, and keep the header above to **three clauses — stamp, version, one headline**. Replace that
headline each session; never append a fourth. Oldest *Recent* entries split to the archive.

---

## Current focus

Since P14 the project runs as **etalon-first continuous improvement** (DL-19).
**The platform is self-driving in paper mode**: the DEPLOYED, STANDING fleet (16 Container Apps +
`dispatcher-cron` job, KEDA scale-to-zero windows, idle ≈ $0) places a calendar-gated `RunRequest`
at 22:30 UTC daily, runs graph-pull + served-over-Service-Bus on the Neon Postgres spine (ADR-0014),
reconciles holdings against the broker (DL-44), debates vetoes under compiled prompts (DL-42), and
proves `ACCEPTANCE PASS`. Pausing = disable the job + zero the scale windows (`docs/deployment.md`).
Completed arcs live in their sprint docs + archives: fleet (DL-35), credentials (DL-36), Postgres
migration (DL-43), deliberation quality (DL-41/42). Layer-3 acceptance 🟩 at the full S&P-500;
Layer-2 choreography 🟩 on a distributed run (S102).

## Recent (most recent first — detail in each sprint doc)

- **The gate was red for two days over one test line (fix, no bump, 2026-08-17 —
  [DL-110](design-log.md)).** Four straight `Security Findings` runs failed — three on docs-only
  commits — on CodeQL `py/mismatched-multiple-assignment` **#177**, the only error-level alert of 76
  open: a PM test unpacked `SectorBook.outcomes()` into two names, and that call returns `()` when
  the ticker has no sector. Length now asserted, then indexed. `make ci` **2302 passed / 100.00 %**;
  #177 reads `fixed`; `GATE PROVEN` for `21a5e81`. 🪤 **A branch cannot clear an alert raised on
  `main`** — `codeql.yml` runs only there, so the fix branch failed its own gate on the same alert;
  merge-then-verify was the only exit. 🪤 **The step prints nothing on failure** (report → summary).

## Now

**PROVEN RESULT — one clean run, 2026-08-19 (the goal that was set).** After the operator restored
OpenAI credits, `verify-2026-08-19-clean-2` on the deployed `s181` fleet:
**8/8 stages · `real_debate_count` 9 of 9 (`debate_coverage` = 1.0) · `failed_open_count` **0** ·
`deliberation_status` = **`applied`**, plain — not `applied_failed_open`, not `proceeded_unvetoed` ·
`ACCEPTANCE UNPROVEN` with **no breach lines**, the only missing element being the 13:30 UTC open.**
Verdicts: **6 vetoed** (AMZN, GOOGL, GOOG, XOM, INTC, NEE), **3 upheld and submitted** (MO, CSCO,
MDLZ) — every one genuinely debated. 45 `LLMCall` rows = exactly 9 x 5. Cost **$0.46**.
🪤 **The timeout raise was load-bearing after all, for a different reason than it was made for:**
this run logged **68.4 s and 61.6 s** calls, both of which the old 60 s ceiling would have cut.
DL-116's amendment stands — the fail-opens were `HTTP 429`s — but 120 s was genuinely needed.
🚨 **The blocker was real and is now lifted only by the operator's $5 top-up**: OpenAI reads
`HTTP 200`; **Anthropic is still capped until 2026-09-01**, so there is no working fallback provider
and a second credit exhaustion stops the fleet again — now a **standing operational note** in the
work queue rather than a work item, because it is an outage condition, not something to build.

🚨🚨 **BLOCKER, since LIFTED — the deliberator had no working LLM provider.** Probed directly
2026-08-19: OpenAI **`HTTP 429` "You have no credits remaining"**; Anthropic **`HTTP 400` "You have
reached your specified API usage limits. You will regain access on 2026-09-01"**. Every debate fails
open, and `failed_open_count > 0` fails acceptance on its own, so **no run can come back clean until
credits are added or 1 September**. 🟢 Nothing else is broken: the pipeline runs 8/8 and the veto now
binds. **Operator action, not a code fix.**

**PROVEN RESULT — S181 closed, fully proven on the fleet.** Sweep #1 (06:37:57) wrote the ack and one
fault; **sweep #2 (07:45:33) wrote neither** — `UntrackedOpenOrder` **13 → 13**, acks **1 → 1**.
Twelve consecutive runs had each raised that fault. Retired with **one targeted** `FaultResolution`
(`Fault` 6178 → 6178 unchanged, resolutions 2 → 3, live incidents 5 → 4, all statuses still
`pending`). 🪤 Deliberately **not** the blanket sweep — the other four live incidents are the LLM
outage and retiring them would mark a live failure resolved.

**PROVEN RESULT — the veto binds, first time (DL-116).** Grace 900 → 1800 and per-call timeout
60 → 120, in the tunables pack as well as live env (DL-100). `verify-2026-08-19-clean` returned
`deliberation_status=applied_failed_open`, **not** `proceeded_unvetoed`: 6 of 9 orders blocked, **3
submitted instead of 9**. 🚨 **This is a posture change made by arithmetic** — DL-104 set the grace to
900 precisely to keep the veto advisory. Work-queue **item 6** (a real advisory/binding switch)
stays open; the posture is now held by two numbers a busier night could overturn.

🪤 **I got half the diagnosis wrong and it cost a run.** The fail-opens were read as a 60 s timeout
because the latency tail sat exactly at that ceiling. They were `HTTP 429`s. The reason string was
in `DeliberationRun.failed_open_reason` the whole time. Third instance of taking a number that
*correlates* with the boundary as the cause — after the `record_deploy` SHA and the module-size
counts. **Read the reason field before the metrics.**

**Both test runs torn down.** 9 + 3 orders cancelled; book at **19 open orders, all protective stops,
0 non-stop**, cash unchanged `$83,776.22`, 19 positions, equity `$102,694.96`. Fleet at
`minReplicas 0`, scale config diffs identical to the pre-test snapshot. 🪤 `sched-2026-08-19` was
consumed by the first test, so tonight's job no-ops; the next scheduled run is `sched-2026-08-20`.

**PROVEN RESULT — S181 deployed `s181`, 2026-08-19.** Image-only retag was the right path: the
vocabulary pack hash is identical (`8777b907…`) between the deployed `s179` commit and `bcf3a2b`.
16/16 apps + `dispatcher-cron` on `s181`, all `Succeeded`, tag count == inventory count, cron still
`30 22 * * 1-5`, KEDA rules unchanged. `GATE PROVEN` for `bcf3a2b` (CI, Security Findings, CodeQL,
image build) with the printed SHA checked against `git rev-parse HEAD`. `DeployRecord` written with
the **build's own head SHA**, not a live `git rev-parse` — the S180 defect is unbuilt, so that trap
was avoided by hand.

**S179 (`0.90.14`) shipped 2026-08-18 and is deployed** — `open_incidents` is a live incident
count scoped to the latest graph-run day, with append-only `FaultResolution` retirement. Detail in
its sprint doc and [STATE-08.md](state-archive/STATE-08.md).

**PROVEN RESULT — `sched-2026-08-18`, read 2026-08-19.** The run completed **8/8**: 99 tickers at **203
bars** each, 20 scanner survivors, 28 scored, **7 PM approvals**, **7 real debates with 0 fail-opens**,
**5 vetoed** (GOOG, GOOGL, AVGO, XOM, CSCO) and **2 submitted** (AMZN 3, MO 15) — both `accepted` at the
broker. 🪤 **Neither reached the open** — both were cancelled by the 2026-08-19 test run's head-of-run
sweep (ADR-0018), so this run never resolved past `UNPROVEN`. Equity
**$102,680.53** (last_equity $102,572.78), 19 positions, **+$351.23 unrealized**. 🚨 **No DL-104-class
defect in any verdict this time** — all five cite real gaps in what the PM aggregates (dual-class
GOOG/GOOGL as independent names, no sector-correlation penalty, market-order sizing against an
estimated price). Two nights running, the theme is **exposure aggregation the PM does not do**; that is
a candidate, not a defect, and it is adjacent to work-queue item 18.

## Next

**Ranked queue of record: [work-queue.md](work-queue.md)** — this section is the narrative around it, not a second ranking.

**Ahead of the numbered list — one measurement now unblocked, and three questions raised and not yet
answered.**

**The measurement that reorders everything below it.** `0.90.02` made the `effort` tunable reach the
wire, so the two free latency levers are measurable for the first time. Sweep **`effort` down from
`max` first** — it is the only lever that costs nothing. Then `max_rounds` 2 → 1 **only if that is
not enough**: 🚨 its own `why` says *"debate must show more than one round in live proof"*, so one
round is **cutting the artefact under test to buy wall clock**, a recorded decision rather than a
knob. Build [S172](sprints/sprint-172-independent-debates-run-independently.md) **only if both
together still miss** — full ordering and the arithmetic in [DL-105](design-log.md)'s amendment.
The sweep's first point is **done** — `effort` `max` → `high`, live since 2026-08-12 — and it
cost three fail-opens before `request_timeout_seconds` went 30 → 60, **now proven at 0 fail-opens**
(table under *Now*). The two levers are
**coupled**: raising effort lengthens the peer-call tail into a fixed timeout. Measure both
together or not at all.

**Undecided, recorded so they are not re-derived** — all raised 2026-08-11, none actioned:
**(i)** ~~amend S172~~ **DONE 2026-08-19** — the unsound `max_rounds` reason is replaced (a 1-round debate is a different artefact, not a faster one), the build-trigger is now **measured** and in the spec (**15 orders breaches the 1800 s grace**), the stale `effort`/S169 traps are corrected, and a Codex handover block is written;
**(ii)** ~~collapse to one ranked queue~~ **DONE 2026-08-19** — the out-of-repo `debt.md` was **deleted**, not reconciled: it was a 2026-08-14 ancestor of `work-queue.md` and all 8 of its unique references were fragments of closed items. The queue was pruned 255 → 99 lines (11 closed rows removed, 2 folded into parents, every carried number re-measured); **(iii)** stop pinning version numbers in sprint
specs (*"next available PATCH/MINOR at merge"*) — after three renumberings in one day.

1. 🚨 **Close the loop on `critical` Flags, so `healthy` can mean something again.** A **fix**.
   47 unresolved critical Flags since 2026-07-08 pin `healthy=false` and `pending_human_flags=47`
   forever. A divergence that reconciliation has already adopted should resolve its own Flag; the
   backlog needs a one-off sweep behind that. 🪤 **Retracted, 2026-08-15:** this item previously
   claimed the graph had the book wrong and ranked #1 for that reason. It did not — graph and broker
   matched 19/19. The AVGO `overturn` was a **false premise**, not a data defect (see item 2).
2. 🪤 **Sweep the debate context for the same class — now FOUR instances, packaged as [S177](sprints/sprint-177-every-number-names-its-unit.md)** (2026-08-15). The fourth
   is `max_sector_pct`'s `deployed`: `SectorBook.__init__` seeds `_names` from held positions but
   **never seeds `_deployed`**, so `deployed` counts only *this batch* (GOOGL's `deployed=687.05` is
   exactly GOOG's `order_cost` moments earlier). `deployed=0.00` beside `existing_sector_names=2`
   is correct and unreadable, and it cost the AVGO overturn. 🚨 **Same code is also a latent gate
   defect** — the dollar sector cap never sees held positions, so across days sector exposure can
   pass 30 % unnoticed; masked today only because `max_names_per_sector=3` binds first. Every value rendered into the packet should be
   checkable against what the reader will assume it means: right unit, right period, right scope.
   **Not yet a spec.** This is the highest-value item once the divergence is settled.
3. **~~DL-104 (a) — the invented ATR fragment~~ — DONE.** S175, `0.90.08`, **deployed `s176a`
   2026-08-15**. `_atr_pct`/`_atr_fragment` deleted. Cost, measured before the fix landed: the AMZN
   and MDLZ vetoes on `sched-2026-08-14`.
4. **~~DL-104 (b) — batch/portfolio absence~~ — DONE.** S175, same deploy. Cost, measured: the AVGO
   `overturn` plus the CSCO and GOOGL `revise`s on `sched-2026-08-14`.
5. **~~DL-112 — sentiment counts name their unit~~ — DONE.** `0.90.11`, **deployed `s176b`**.
   Cost, measured: the XOM veto and part of AMZN's.
6. **DL-104 (c) — the analyst's hardcoded SMA-200 rationale.** The summary string always names
   SMA-200 while `indicators.sma_distance` returns `None` below its period. 🪤 **The bars gap
   underneath it is CLOSED** — S174 ships 203 bars, so SMA-200 now computes; what survives is the
   rationale asserting an input without checking it exists. Same class as item 5. ð¨ **Cited again 2026-08-19** â NEE vetoed because *"the cited technical support is contradicted by a 0.463 technical score with bearish MACD/EMA/golden-cross inputs and a bottom-tier scanner rank"*: the rationale reads as confirmation while the score underneath it is bearish.
7. **DL-104 (d) — a real advisory/binding switch**, so *advisory* is a declared posture rather than a
   grace that happens to expire. Every run writes a truthful but uninformative `error` fault, which
   trains the operator to read a real fault as noise.
8. **S170 — one LLM adapter in `kernel/`**
   ([sprint-170](sprints/sprint-170-one-llm-adapter-in-the-plumbing.md)). Capability, not repair, so
   it ranks below the fixes — but it gives the operator the same provider switch the deliberator has,
   while the Anthropic key is usage-limited to 2026-09-01.
9. **Remaining hardening rows: N, O, R.** **N** — delegated coding agents default to
   `danger-full-access` with no approval prompt; the protection is the operator remembering a CLI
   flag. **O** — S157's 101 missing law-clause test-plan rows, then flip assertion E in
   `scripts/check_law_coverage.py` to hard fail. **R** — three guards covered only by CI lacking the
   extras. 🪤 **Row P is closed** (S176, deployed); **row Q is closed** (the `s176a` full `up`
   returned `[OK]` on all 16 env-preservation checks after refusing once — see Recent).

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
