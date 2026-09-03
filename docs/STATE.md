# Project State

**Last updated:** 2026-09-03 18:33 AEST · **Version:** 0.94.07 · **🟩 S180 tag-identity deploy guard merged and gate-proven at `5359667`.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + [`state-archive/`](state-archive/INDEX.md) `STATE-01…08.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.
**Size rules**, after this file reached 574 lines with a **112 KB header line**: keep it **under 200
lines**, and keep the header above to **three clauses — stamp, version, one headline**. Replace that
headline each session; never append a fourth. Oldest *Recent* entries split to the archive.

---

## Current focus

**The bar, set by the operator 2026-08-20.** The etalon is done when **the pack trades unattended
for a sustained stretch and the evidence discipline catches its own defects without the operator in
the loop.** Not "trading is finished" — but far above where it is. 🚨 **Consequence for ranking:**
whatever currently prevents unattended operation *is* etalon work, not a detour from it. **Until
2026-08-22 that was the 73 % veto rate** ([DL-119](design-log.md)). It is now one level up: the
referee cannot run at all until **2026-08-30**, so the pack trades unvetoed behind a gate that is red
nightly for a non-defect ([DL-125](design-log.md)). 🚨 **A discipline that cries wolf for six
straight nights fails the second half of the bar as surely as not trading fails the first** — which
is why work-queue **item 6** (a declared advisory posture) is now ranked first. 🪤 **Generality is a separate
unproven axis:** ADR-0012's platform/pack wall stays *de jure* until a second pack exists, and
clearing this bar does not close that.

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

🟩 **PROVEN RESULT — [S194](sprints/sprint-194-a-number-nobody-records-is-a-number-nobody-has.md) MERGED `e0a144f` (`0.94.05`) **AND DEPLOYED `s194`**, 2026-09-02.** `DeliberationRun` records `orphaned_reply_count` as a
**per-run delta**; the two-runs-one-client trap earned its place — the naive cumulative write failed `assert 3 == 1`. 🟩 **Verified independently:** `GATE PROVEN` for `e7699af` with the printed SHA checked
against `HEAD`, delta at `poll.py:63/94`, `DLIB-OBS-04` present. 🟩 **Deployed by full `up` (never a retag — the pack moved):** `ENV PRESERVATION` **16/16**, alembic OK, **16/16 on `s194`**, **16/16 `Succeeded`**,
cron `30 22 * * 1-5` intact, and scale/KEDA **diffed identical to the pre-deploy baseline apart from the tag**. 🎯 **The check that matters for a pack move:** the *deployed* `GRAPH_VOCABULARY_B64` decodes to
**`d47e88b1…`, byte-identical to the repo pack**, with `orphaned_reply_count` declared — image and pack travelled together, so the fail-closed guard will accept the write. `DeployRecord` on the build run's own SHA.
🟩 **It has now recorded:** `sched-2026-09-02` wrote **`orphaned_reply_count=0`** — the first datapoint S172's criterion has ever had (*Now*). 🚨 Two hazards stand from verifying, neither
in the code ([DL-148](design-log.md)): a **CRLF regression was reported as a fix** (three evidence docs, converted back) and **two different `v1.2` deliberator law versions** now exist, S194's on `main` and S172's on its
branch — git may merge them **without a conflict**, so whoever merges S172 renumbers it to v1.3.

## Now

🟩 **PROVEN RESULT — [S180](sprints/sprint-180-a-deploy-record-must-name-the-commit-that-was-built.md) MERGED `5359667` (`0.94.07`), 2026-09-03.** `record_deploy` now wires the existing `GitHubActionsReader` into `record_verified_deploy()`; the writer refuses unless the supplied SHA is the head of a successful `build-images.yml` run that produced the tag being recorded. The required `s194` / `e0a144fc08b1d5fd8bc219f4ed48fef74fa8d120` case is accepted even though newer successful builds existed, closing the old SHA-only gap: `verify_build_sha()` / `sha_has_successful_build()` proved only *"this SHA was built"*, so recording `s193` against the commit that built `s194` would still have passed. GitHub unreadable or absent tag evidence fails closed; no asserted `sha_verified=False` record is emitted. `DL-149` is corrected below `DL-150` and its same-day correction. 🟩 **Proven in order:** branch CI `33732844209` success for `5359667`, `main` fast-forwarded and pushed, then `make gate-ran` from `C:/Users/yury_/AppData/Local/Temp/wt-main` printed `GATE PROVEN for 53596676460a36782a99d4a3bf71dfc0bc9d293b`; that matches `git rev-parse HEAD`.

🎯 **Next:** 🚨 *(the line here read “plan S181” — S181 shipped weeks ago; corrected.)* **[DL-150](design-log.md) re-measured the per-order debate cost at 72.5–84.3 s, not the 124 s work-queue item 3 rests on**, so serial deliberation now fits the deployed 1,800 s grace to **21** orders and breaches at **22**. Recent nights approved **2, 2, 9, 7**. **S172's own trigger is therefore met only if the target funnel width is ≥22 — an operator decision, open.** Next work: **item 9 / S173**, the verdict-quality gate, which is the instrument for the `effort` and `max_rounds` question and the only way to read the **56 %** self-agreement.

🎯 **PROVEN RESULT — THE FIRST `s194` NIGHT PASSED CLEAN, AND THE INSTRUMENT WROTE ITS FIRST VALUE.** `sched-2026-09-02` fired on schedule: **8/8 stages, `ACCEPTANCE PASS`**, provider
`quality ok 98/99` with **no `*_degraded` notes**. 🟩 **The number S172's criterion could never be falsified without now exists:** `DeliberationRun pm-run-c31f4806…` (22:44:09 UTC) carries
**`orphaned_reply_count=0`** beside `real_debate_count=2` and `failed_open_count=0` — **every earlier run on the spine reads `<ABSENT>`**, so this is the first datapoint, and it is the quiet-night `0`
[S194](sprints/sprint-194-a-number-nobody-records-is-a-number-nobody-has.md) predicted. 🟩 **The veto bound for a second night:** PM approved **2 buys** (AMD, USB) of 30 scored, the deliberator ran
**2 real debates** and **vetoed both** (`revise`), execution recorded `deliberation_status=`**`applied`** and **submitted 0**; the fleet returned to rest on its own, **16/16 on `s194` at `minReplicas=0`**.
🪤 **`deliberation_posture=advisory` with `blocked_count=0` in that record is not a veto being ignored** — `drop_vetoed` strips vetoed tickers **before** posture is consulted
(`agents/execution/pm_execution.py:57-63`); posture governs only the no-artifact branch, so an advisory posture and a binding veto are not in contradiction. 🟩 **[DL-147](design-log.md)'s prediction held,
and item 32's success factor is met on this run:** **zero** new faults of any kind — the newest on the spine are still the two `BrokerStopIdentityMismatch` warnings at `2026-09-01T22:30:42/47`. No stop
fired (0 submitted), so the transient 16-second staleness warning did not recur, exactly as the corrected reading said it would not. 🟠 Item **42** still stands: the check compares a type against a lifecycle.

🟩 **PROVEN RESULT — [S191](sprints/sprint-191-a-quiet-night-gets-the-same-verdict-twice.md) MERGED `97e9fb5`
(`0.94.03`), 2026-09-01.** The acceptance view derives the approved-**buy** count from the linked
`PMRun.order_intent_set`, so quiet zero-order *and* sell-only `not_required` runs pass, while a `not_required`
beside an approved buy still breaches as `buy_veto_missing` and an unreadable PM payload fails closed.
🟩 **Verified independently:** claimed SHA **is** the tip, `GATE PROVEN` incl. post-merge **CodeQL**, PATCH correct.
🎯 **The real proof is live, not a fixture:** `sched-2026-08-31` — which returned `ACCEPTANCE FAIL` this morning —
now re-runs **`ACCEPTANCE PASS`**. 🟩 **DEPLOYED `s191`** by image-only retag: **16/16** on `s191`, **16/16**
`Succeeded`, scale **diffed identical**, cron intact, `DeployRecord` on the build run's `1f0b6a0…`. 🟩 **LIVE-PROVEN, AND NO CASCADE WAS NEEDED:** the view is imported only by `accept.py` and the
dashboard, and the fleet is **16 apps with no dashboard among them** — so it was proven over **all 55 runs on the spine**
rather than one run. Both race branches are covered by real runs; `sched-2026-08-31` **PASSes**.

🟩 **PROVEN RESULT — FLEET DEPLOYED `s190` THEN `s191`, 2026-09-01** (from `s187`). 16/16 on tag, scale **diffed** to zero drift, cron intact, `DeployRecord` on the
build run's own SHA. 🚨 **S190 could not travel alone** — the vocabulary pack had moved, so a retag would have met the fail-closed write guard mid-cascade
(S148/[DL-85](design-log.md)); the full `up` carried **S190 + S189 + S188 + item 34**, alembic a **no-op**, **`ENV PRESERVATION` 16/16**. 🪤 Two Dependabot merges
had reached `main` ungated and the images came from them — now closed as item 39.

🟩 **PROVEN RESULT — [S190](sprints/sprint-190-one-liveness-question-one-answer.md) MERGED `193e71b`
(`0.94.02`), 2026-08-31.** `contracts/broker_lifecycle.py` is the single place execution broker-fact liveness is
asked: a fired stop stops being counted as protection, a resting-stop `Fill` is no longer an open order, and the
stale-order sweep compares **live broker stop to live graph stop**. Six status vocabularies collapse into one, and
`partial` stayed non-terminal so S176 is intact. Execution laws **v1.4**, rollup **35 / 61**, `DRIFT-055` CORRECTED.
🟩 **Verified independently:** `GATE PROVEN` for `c682907…` from a worktree at that commit, baseline untouched,
PATCH bump correct. 🪤 `EXEC-STA-05` went ⬜ → 🟩 by **re-citation**, already asserted under `EXEC-IDM-01`.
🟩 **PROVEN LIVE, 2026-09-01.** One cascade (`verify-2026-09-01-s190-stops`) ran **8/8 with zero faults** where
`s187` raised **17** mismatch warnings and a `cancel_stop` 422 nine hours earlier; broker **identical before and
after** (28/28, same order IDs). Torn down with `pg_teardown --run-id` — **item 12's delete path, first live use**.

🎯 **DECIDED — ITEM 6b: THE POSTURE STAYS `advisory` THROUGH MONDAY** ([DL-134](design-log.md), 2026-08-30).
🪤 **The row's premise was wrong, read in the code.** `drop_vetoed` runs **before** `apply_deliberation_posture`
(`agents/execution/pm_execution.py:59`), so an **arrived veto binds identically under both postures**. `binding`
bites only on `proceeded_unvetoed` — *no `DeliberationRun` at all* after the grace — and on acceptance, where it
adds `debate_coverage >= 1.0` and `failed_open_count <= 0`. **Every degraded night of the outage was
`applied_failed_open`**, so `binding` would have blocked **zero** orders on any of them; it would only have made
acceptance red. DL-116's grace is what made the veto bind, on 2026-08-19, and this switch does not move DL-119's 73 %.
🟠 **FLIP CONDITION 1 of 3 on `sched-2026-08-31`** — the posture landed, but `real_debate_count` was **0** and
`failed_open_count == 0` only vacuously; PM approved nothing, so no debate ran. 🟩 **Its real purpose is now met
another way:** S188's in-fleet tests show all three deliberators passing `anthropic` through master's Key Vault, so
the credential path is proven and only **debate mechanics** still need item 3's K=4 run. Posture stays `advisory`.

🟩 **PROVEN LIVE — ADR-0023's PM half, unattended, first time.** GOOG sized at 0.998 %; GOOGL then **failed** at
1.67 % > 1 %. 🚨 Pre-S184 both passed, opening **two positions in one company** ([DL-122](design-log.md)).

🚨 **NOT PROVEN — ADR-0023's falsifiable test** (the 73 % veto rate falls materially). **73 % stands as the last
honest figure** ([DL-119](design-log.md) amendment). 🪤 `sched-2026-08-31` supplied **no** data — zero debates.

🚨 **NOT PROVEN — S182 live.** 2026-08-21's stops carry `stop_pct_source=position`, written eight minutes before
execution ran, so the fallback never fired. 🪤 **Do not re-check it that way** — run-start reconciliation closes it.

🟩 **PROVEN RESULT — [S193](sprints/sprint-193-a-shim-that-never-runs-is-not-a-shim.md) MERGED `a9603d7` (`0.94.04`), 2026-09-02** — work-queue **item 40 closed**. `_accept_historical_passed` now accepts any
`Mapping`, so S184's shim runs against the type the store actually returns; the tests round-trip through a real `GraphStore`, which is what nothing had ever done. 🟩 **Verified independently, not accepted:**
`GATE PROVEN` for `72e063b` with the printed SHA checked against `HEAD`, PATCH bump correct, and **the sweep re-run here: 56 runs, `0 ERROR`, 54 `FAIL`, 2 `PASS`.** 🪤 The handback moved `FAIL` 16 → 54
without explaining it; it accounts for exactly — the **38** formerly-unreadable runs are now readable and legitimately red on old data (16 + 38 = 54), and `PASS` 1 → 2 is the overnight run arriving.

🟩 **PROVEN RESULT — [S188](sprints/sprint-188-a-credential-is-tested-before-it-is-handed-over.md) merged `108475c`
(`0.93.00`), 2026-08-30.** Master refuses activation on a rejected required credential, separates transport failure
so a DNS blip cannot halt the fleet, records sanitized evidence on `AgentInstance`; laws **v1.2**, `GATE PROVEN` for
the merged SHA, post-merge CodeQL clean. 🚨 A merge-review correction flipped the *primary* OHLCV credential to
required ([DL-136](design-log.md) amendment). 🟩 **PROVEN IN THE FLEET 2026-09-01:** 15/15 agents `active` and the
tests **ran** — provider 4/4, execution 1/1, operator 1/1, each deliberator 2/2; 0 failed, 0 `Escalation`.
🟩 **AND THE REFUSAL HALF, 2026-09-01** ([DL-144](design-log.md)) — a broken credential refuses, a control arm activates. **Item 36 is closed.**

🚨 **[S172](sprints/sprint-172-independent-debates-run-independently.md) MEASURED, THEN RE-MEASURED THE SAME DAY, AND THE PREMISE MOVED** ([DL-140](design-log.md), [DL-145](design-log.md)). Same image, same K=4, five hours apart:
**15/15 debated, 0 fail-opens** where the first run had 13 and 2 — the correctness failure is **intermittent and did not reproduce**. But the speed miss did, **1.78x of a possible 4x**, which
**separates the two symptoms and falsifies DL-140's guess** that they were one defect. 🚨 **The 2026-09-01 orphan count remains UNKNOWN, not zero:** pre-S194 rows/logs cannot re-derive it. 🟩 **S194 now records the per-run count on every future `DeliberationRun`, so S192 can diagnose from measured data instead of first building the instrument.**

**Shipped and deployed, detail in the sprint docs and design log.** **S184** merged `18c41b1` (`0.91.00`), `GATE PROVEN` at `8613d72`, PM rows `PM-NEV-07/08/09` 🟩, DRIFT-042..046 `CORRECTED`, deployed `s184` with `ENV PRESERVATION` 16/16 and zero drift. Two defects the merge exposed are fixed on `chore-gate-outcome-refuses-ambiguity`: `GateOutcome.passed` re-collapsed the states S184 had just separated and now raises; CodeQL **#187** was `py/mismatched-multiple-assignment`, **the same rule and package as #177 four days earlier**, because `codeql.yml` runs only on `main` (queue item 31). 🟢 **That trap did not fire this time** — `main` at `19dc2b2` is `GATE PROVEN` on CI, Security Findings **and CodeQL**, with **0** open error-level alerts. **S182** merged `2fc0672` (`0.90.16`), deployed `s182`. 🪤 A `verify-2026-08-20-s184-a` teardown reported false success because `ScanRun` is uuid-keyed and the verification query reused the teardown's own filter ([DL-124](design-log.md)); a second pass removed 24 nodes + 25 edges and the pollers' own predicates now read **0 pending** at every stage, 22 positions intact.

🪤 **One live residue, not urgent:** **2 NFLX shares** from the S172 test harness, never vetoed (selling is a real trade). The `cancel_stop` `HTTP 422` half is **closed**.

## Next

**Ranked queue of record: [work-queue.md](work-queue.md)** — this section is the narrative around it, not a second ranking.

🎯 **Re-ranked 2026-09-01, after the `s190` proof and the K=4 measurement.** **(1)** item 3's newly-named defect —
peer replies dead-lettered under concurrency, which blocks the veto's verdict and is now a code fix, not a
measurement; **(2)** item 38, measured as a **race** (identical inputs, opposite acceptance verdicts), specced as
[S191](sprints/sprint-191-a-quiet-night-gets-the-same-verdict-twice.md); **(3)** item 39, the Dependabot gate hole.

**Ahead of the numbered list — three questions raised and not yet answered.**

**The latency levers, and why S172 got built anyway.** DL-105's ordering was: sweep `effort` down first (free),
then `max_rounds` 2 → 1 only if needed — 🚨 and that second one is **cutting the artefact under test to buy wall
clock**, a recorded decision, not a knob. The first point is **done** (`effort` `max` → `high`, live 2026-08-12);
it cost three fail-opens until `request_timeout_seconds` went 30 → 60, which then read **0 fail-opens** on
2026-08-18/19 — a figure the outage has since made unreadable. Both levers are **coupled** (more effort lengthens
the peer-call tail into a fixed timeout): measure them together or not at all. Arithmetic in
[DL-105](design-log.md)'s amendment.

**Undecided, recorded so they are not re-derived** — raised 2026-08-11. **(i)** amend S172 and **(ii)** collapse to one ranked queue are both **DONE 2026-08-19** (detail in the queue's own header). **(iii)** stop pinning version numbers in sprint specs (*"next available PATCH/MINOR at merge"*) — after three renumberings in one day — **still open**.

1. 🪤 **WITHDRAWN 2026-08-22 — retracted twice, on a raw-prop count both times.** `pending_human_flags`
   is **0**; `Flag.status` stays `pending` by design, like `Position.status` staying `open`. What pins
   `healthy=false` is `open_incidents`. The retracted-DL-73 class again — audit on the predicate.
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
   rationale asserting an input without checking it exists. Same class as item 5. 🚨 **Cited again 2026-08-19** — NEE vetoed because *"the cited technical support is contradicted by a 0.463 technical score with bearish MACD/EMA/golden-cross inputs and a bottom-tier scanner rank"*: the rationale reads as confirmation while the score underneath it is bearish.
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
