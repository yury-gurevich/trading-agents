# Project State

**Last updated:** 2026-09-01 11:47 AEST · **Version:** 0.94.02 · **🟩 Fleet deployed to `s190` — S190, S189, S188 and item 34's preflight fix reached the fleet in one full `up`; three live proofs now ride on tonight's run.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + [`state-archive/`](state-archive/INDEX.md) `STATE-01…07.md` + git). **LAW-02:** an item is "shipped" only when
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

## Now

🟩 **PROVEN RESULT — FLEET DEPLOYED TO `s190`, 2026-09-01** (was `s187`). Verified independently of the tool's own
output: **16/16** apps on `s190`, **16/16** `Succeeded`, scale config **diffed** against the pre-deploy baseline (not
sampled) — zero drift; `dispatcher-cron` on `s190` with cron **`30 22 * * 1-5`** intact. `DeployRecord`
`deploy:2026-09-01T01:32:41…` carries the **build run's** head SHA `b0185e76…` read back from the workflow (item 21's
defect, hand-avoided a third time). 🚨 **S190 could not travel alone:** the vocabulary pack moved (`93dab2e6…` →
`9b57a997…`), so an image-only retag would have met the fail-closed write guard mid-cascade (S148/[DL-85](design-log.md));
the full `up` carried **S190 + S189 + S188 + item 34's preflight fix** together. `alembic upgrade head` was a **no-op**
(already `0001_spine`) and **`ENV PRESERVATION` 16/16**, so no DL-100 revert. 🪤 **Two Dependabot merges had reached
`main` ungated and the images were built from them** — auto-merge pushes via `GITHUB_TOKEN`, which by design triggers
no workflow; **PR #82's merge commit differed from its gated head by 475 lines of `uv.lock`**, a union never gated as a
unit. CI + Security Findings were dispatched and `GATE PROVEN` re-read for `b0185e76…` *before* the fleet moved.

🟩 **PROVEN RESULT — [S190](sprints/sprint-190-one-liveness-question-one-answer.md) MERGED `193e71b`
(`0.94.02`), 2026-08-31.** `contracts/broker_lifecycle.py` is the single place execution broker-fact liveness is
asked. A `BrokerStopOrder` whose sibling `Fill` reached a terminal broker state is no longer returned by
`active_broker_stop_orders`, so **a fired stop stops being counted as protection**; a resting-stop `Fill` is no longer
an open order; and the stale-order sweep compares **live broker stop to live graph stop** instead of type-to-lifecycle.
Six scattered status vocabularies collapse into one module — and `partial` stayed non-terminal, so S176 is intact.
Execution laws **v1.4** (`EXEC-OBS-05`), rollup **35 / 61**, `DRIFT-055` **CORRECTED**, `DL-139` amended.
🟩 **Verified independently of the handback:** `GATE PROVEN` for `c682907…` from a worktree at that commit,
security baseline untouched, PATCH bump correct, both modules still under 200. 🪤 `EXEC-STA-05` went ⬜ → 🟩 by
**re-citation** — the tests already asserted it, filed under `EXEC-IDM-01`.
🟢 **DEPLOYED `s190` 2026-09-01; live proof owed** — tonight must show **zero new `BrokerStopIdentityMismatch`
faults** (17 fired this morning on `s187`, plus a `cancel_stop` 422) and `active_broker_stop_orders` = the broker's count.

🟩 **PROVEN RESULT — WORK-QUEUE ITEM 34 IS CLOSED, merged `6b4463c` (`0.94.01`), 2026-08-31.** `up`'s preflight now
runs the *same* import route prep runs. **Measured both ways** (real → exit 0, missing module → exit 1) and
**observed in place**: `[OK] Service Bus route-prep imports (azure extra)`, green in a worktree where every credential
row was red — it reports a corrupt *local environment*, not a missing secret. The invariant test pins **both sides**.
Full cycle despite being PowerShell: `GATE PROVEN` for `a234c28…`, post-merge CodeQL **success**. 🎯 This is the
failure that stopped the `s187` deploy *after* `alembic upgrade head` had run.

🎯 **DECIDED — ITEM 6b: THE POSTURE STAYS `advisory` THROUGH MONDAY** ([DL-134](design-log.md), 2026-08-30).
🪤 **The row's premise was wrong, read in the code.** `drop_vetoed` runs **before** `apply_deliberation_posture`
(`agents/execution/pm_execution.py:59`), so an **arrived veto binds identically under both postures**. `binding`
bites only on `proceeded_unvetoed` — *no `DeliberationRun` at all* after the grace — and on acceptance, where it
adds `debate_coverage >= 1.0` and `failed_open_count <= 0`. **Every degraded night of the outage was
`applied_failed_open`**, so `binding` would have blocked **zero** orders on any of them; it would only have made
acceptance red. DL-116's grace is what made the veto bind, on 2026-08-19, and this switch does not move DL-119's 73 %.
🟠 **FLIP CONDITION NOT MET — 1 of 3, measured 2026-09-01.** `sched-2026-08-31` carried `deliberation_posture=advisory`
✅, but `real_debate_count` was **0** and `failed_open_count == 0` only **vacuously**: PM approved nothing (28 holds;
GOOGL, the lone buy, failed sizing), so no debate ran and the master/Key Vault path is *still* untested. **Posture
stays `advisory`** — for want of evidence, not by choice. 🚨 **That run also went `ACCEPTANCE FAIL` for a non-defect:**
`not_required` is declared (`agents/execution/deliberation_gate.py:38`) but missing from `ADVISORY_STATUSES`
(`orchestration/packs/trading_deliberation_view.py:20`), so **a no-trade day cannot pass the advisory gate**.

🟩 **SUPERSEDED BY `s190` — the fleet was deployed to `s187` on 2026-08-30**, 16/16 verified, and
`sched-2026-08-31` did carry `deliberation_posture=advisory` on its `ExecutionRun`, so that half of its proof landed.

🟩 **PROVEN — BOTH PROVIDERS RETURN HTTP 200, 2026-08-30**; the [DL-125](design-log.md) outage is **over** (the
Anthropic half was an **operator-set** spend limit, not credit). 🚨 **From this machine, not the fleet** — and
`sched-2026-08-31` ran no debates, so the fleet's own path is still unproven.

🟩 **SHIPPED AND DEPLOYED IN `s187`, both 2026-08-30** — detail in their sprint docs.
**[S187](sprints/sprint-187-a-parameter-is-declared-once.md)** `7d36771` (`0.92.02`): `make ci` gained a **12th step**,
PARAM/settings sync. 🚨 Its audit found **20× its scope** — 60 divergences across nine agents, 3 fixed and **57
baselined warning-only** ([DL-133](design-log.md) decision 3, DRIFT-052, work-queue item 33).
**[S186](sprints/sprint-186-a-headline-about-twenty-companies-is-not-news-about-one.md)** `81b82ee` (`0.92.01`):
batch-scoped duplicate-headline weighting, analyst laws **v1.2**, ledger + INDEX **24 / 47** ([DL-132](design-log.md)).
🪤 Its gate proof named `4b0daaf` and I re-ran it on the tip — the docs-commit-on-top trap, which S188 nearly repeated.

🟩 **PROVEN LIVE — ADR-0023's PM half, unattended, first time.** GOOG sized at 0.998 %; GOOGL then **failed** at
1.67 % > 1 %. 🚨 Pre-S184 both passed, opening **two positions in one company** ([DL-122](design-log.md)).

🚨 **NOT PROVEN — ADR-0023's falsifiable test** (the 73 % veto rate falls materially). **73 % stands as the last
honest figure** ([DL-119](design-log.md) amendment). 🪤 `sched-2026-08-31` supplied **no** data — zero debates.

🚨 **NOT PROVEN — S182 live.** 2026-08-21's stops carry `stop_pct_source=position`, written eight minutes before
execution ran, so the fallback never fired. 🪤 **Do not re-check it that way** — run-start reconciliation closes it.

🟩 **PROVEN RESULT — [S189](sprints/sprint-189-an-empty-answer-says-why-it-is-empty.md) merged `934ffb5`
(`0.94.00`), 2026-08-31.** A vendor-declared truncation or refusal is now a sanitized stop error, not an empty
string: empty debate turns cannot enter transcripts, a stopped judge keeps fail-safe `revise` with an honest
reason, every `LLMCall` carries `stop_reason`, and `max_tokens` gains `le=8192` (4096 had been both default
*and* ceiling). **DL-119 contamination settled** — one empty judge call inside its four binding runs, an
asterisk not a retraction. Deliberator laws **v1.1**, rollup **9 / 51**, [DL-137](design-log.md), DRIFT-054;
`GATE PROVEN` for the merged SHA, post-merge CodeQL success. 🟩 Its temporary CodeQL baseline is already
pruned **4 keys → 1**, **0 open error-level**, closure verified *first* ([DL-138](design-log.md)).
🟢 **Deployed `s190` 2026-09-01** — its `stop_reason` pack move is part of what forced the full `up`.

🟩 **PROVEN RESULT — [S188](sprints/sprint-188-a-credential-is-tested-before-it-is-handed-over.md) merged `108475c`
(`0.93.00`), 2026-08-30.** Master refuses activation on a rejected required credential, separates transport failure
so a DNS blip cannot halt the fleet, records sanitized evidence on `AgentInstance`; laws **v1.2**, `GATE PROVEN` for
the merged SHA, post-merge CodeQL clean. 🚨 A merge-review correction flipped the *primary* OHLCV credential to
required ([DL-136](design-log.md) amendment). 🟢 **DEPLOYED `s190` 2026-09-01**, every `required=True` credential
probed green first. **The activation-refusal proof is still owed** — a fleet fact only after tonight's run.

🟢 **[S172](sprints/sprint-172-independent-debates-run-independently.md) is UNBLOCKED** — built and gate-proven at
`5bf72c9`, unmerged. 🎯 **The K=4 measurement is now next** ([DL-135](design-log.md)): it needs `s172` images and peer
`maxReplicas=4`. 🪤 **Rollback is now a retag to `s190`, not `s187`**, and `s172` needs rebuilding on top of `s190`.

**Shipped and deployed, detail in the sprint docs and design log.** **S184** merged `18c41b1` (`0.91.00`), `GATE PROVEN` at `8613d72`, PM rows `PM-NEV-07/08/09` 🟩, DRIFT-042..046 `CORRECTED`, deployed `s184` with `ENV PRESERVATION` 16/16 and zero drift. Two defects the merge exposed are fixed on `chore-gate-outcome-refuses-ambiguity`: `GateOutcome.passed` re-collapsed the states S184 had just separated and now raises; CodeQL **#187** was `py/mismatched-multiple-assignment`, **the same rule and package as #177 four days earlier**, because `codeql.yml` runs only on `main` (queue item 31). 🟢 **That trap did not fire this time** — `main` at `19dc2b2` is `GATE PROVEN` on CI, Security Findings **and CodeQL**, with **0** open error-level alerts. **S182** merged `2fc0672` (`0.90.16`), deployed `s182`. 🪤 A `verify-2026-08-20-s184-a` teardown reported false success because `ScanRun` is uuid-keyed and the verification query reused the teardown's own filter ([DL-124](design-log.md)); a second pass removed 24 nodes + 25 edges and the pollers' own predicates now read **0 pending** at every stage, 22 positions intact.

🪤 **Two live residues to decide, neither urgent.** **2 NFLX shares** from the S172 test harness, never vetoed
(selling is a real trade); and `cancel_stop` `HTTP 422`, which **recurred on `sched-2026-08-31`** — S190 should end it.

## Next

**Ranked queue of record: [work-queue.md](work-queue.md)** — this section is the narrative around it, not a second ranking.

🎯 **Re-ranked 2026-09-01, after the `s190` deploy.** **(1)** the advisory-gate no-trade defect — it reds the gate
for a non-defect and would make tonight unreadable; **(2)** item 3, S172's K=4 measurement; **(3)** the Dependabot
auto-merge gate hole (merge commits reach `main` ungated), with PR #83 open and failing CI merged-with-main.

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
