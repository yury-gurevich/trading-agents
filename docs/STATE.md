# Project State

**Last updated:** 2026-08-30 21:05 AEST · **Version:** 0.93.00 · **🟩 S188 merged (master refuses activation on a dead credential) and [S189](sprints/sprint-189-an-empty-answer-says-why-it-is-empty.md) is packaged — measured: 135 empty LLM completions, and the defect is in the *primary* adapter, not the fallback item 35 blamed.**

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

- **Three diagnoses, one pattern, no code changed (docs only, 2026-08-24).** All three were execution's
  graph facts denormalising lifecycle differently, with only `Position` having a predicate to hide it:
  item 12's "202-fill backlog" is **27** ([DL-129](design-log.md)); item 20's 228 faults are **13 objects**
  the broker agrees are cancelled ([DL-130](design-log.md)); a stop that *fires* is never reconciled
  ([DL-131](design-log.md), item 32). 🟩 Item 27's symptom is gone — 24 positions / 24 stops, 1:1, zero
  unprotected — but its live proof is still owed. 🪤 Measured 08-24; six runs have happened since.

## Now

🎯 **DECIDED — ITEM 6b: THE POSTURE STAYS `advisory` THROUGH MONDAY** ([DL-134](design-log.md), 2026-08-30).
🪤 **The row's premise was wrong, read in the code.** `drop_vetoed` runs **before** `apply_deliberation_posture`
(`agents/execution/pm_execution.py:59`), so an **arrived veto binds identically under both postures**. `binding`
bites only on `proceeded_unvetoed` — *no `DeliberationRun` at all* after the grace — and on acceptance, where it
adds `debate_coverage >= 1.0` and `failed_open_count <= 0`. **Every degraded night of the outage was
`applied_failed_open`**, so `binding` would have blocked **zero** orders on any of them; it would only have made
acceptance red. DL-116's grace is what made the veto bind, on 2026-08-19, and this switch does not move DL-119's 73 %.
🎯 **Flip condition, checkable not judged:** `sched-2026-08-31` shows `deliberation_posture` on its `ExecutionRun`,
`real_debate_count > 0` **and** `failed_open_count == 0` — the third is what proves the master/Key Vault path,
untested since 2026-08-19. 🚨 Flipping today would stake the acceptance gate on that untested path and make a red
Tuesday unreadable between *the referee bound* and *the fleet cannot reach a provider* — DL-125 repeated on purpose.
🟠 **Advisory is not the destination**, only a one-run delay against a named unknown.

🟩 **PROVEN RESULT — FLEET DEPLOYED TO `s187`, 2026-08-30** (was `s184`, three sprints behind).
`pwsh infra/deploy-agents.ps1 up -Tag s187` exit 0. **Verified independently of its own output:** **16/16** apps on
`s187`, **16/16** `Succeeded`, **16/16** KEDA `min=0 max=1, 1 rule` — identical to the pre-deploy baseline — and
`dispatcher-cron` on `s187`, cron `30 22 * * 1-5`. `DeployRecord` carries the **build run's** head SHA `7d2339bc5a4f`,
read from the run not handed in (item 21's defect). 🚨 **`up` was required, not a retag:** S185's `e370f88` moved the
vocabulary pack, and a retag against a stale pack hits the fail-closed write guard mid-cascade (S148 stall, DL-85).
🪤 **The first attempt failed and changed nothing** — a corrupt local `azure-core` (dist-info with no `RECORD`) that
still looked installed; preflight never imports the deps its own steps need, so it surfaced after alembic ran
(item 34). 🟠 **Not yet proven at runtime:** Monday's run must show `deliberation_posture` on its `ExecutionRun`.

🟩 **PROVEN RESULT — BOTH PROVIDERS VERIFIED BY DIRECT API CALL, 2026-08-30 17:00 AEST.** `claude-opus-5` and
`gpt-5.5` each returned **HTTP 200**; the outage that began 2026-08-19 ([DL-125](design-log.md)) is **over**.
🪤 **The Anthropic half was never a credit problem** — `HTTP 400`, *"your **specified** API usage limits"*, is an
**operator-set** spend limit, distinct from the tier cap (`429` + `enforced_spend_limit_reached`); raising it in
Console → Billing restored access at once, and the `2026-09-01` in the message was only the month reset.
🚨 **Verified from this machine, not the fleet.** Monday's run (08-31, 22:30 UTC) proves that path *and* the deploy.

🟩 **SHIPPED AND DEPLOYED IN `s187`, both 2026-08-30** — detail in their sprint docs.
**[S187](sprints/sprint-187-a-parameter-is-declared-once.md)** `7d36771` (`0.92.02`): `make ci` gained a **12th step**,
PARAM/settings sync. 🚨 Its audit found **20× its scope** — 60 divergences across nine agents, 3 fixed and **57
baselined warning-only** ([DL-133](design-log.md) decision 3, DRIFT-052, work-queue item 33).
**[S186](sprints/sprint-186-a-headline-about-twenty-companies-is-not-news-about-one.md)** `81b82ee` (`0.92.01`):
batch-scoped duplicate-headline weighting, analyst laws **v1.2**, ledger + INDEX **24 / 47** ([DL-132](design-log.md)).
🪤 Its gate proof named `4b0daaf` and I re-ran it on the tip — the docs-commit-on-top trap, which S188 nearly repeated.

🟩 **PROVEN LIVE — ADR-0023's PM half, unattended, first time.** GOOG sized at `existing_issuer_value_usd=0.00` →
0.998 %; GOOGL then **failed** at `1025.19` → 1.67 % > 1 %. 🚨 Pre-S184 both passed, opening **two positions in one
company** ([DL-122](design-log.md)).

🚨 **NOT PROVEN — ADR-0023's falsifiable test** (the 73 % veto rate falls materially). **Zero real-debate data** on
`s184` code; 08-20/08-21's 40 % and 0 % are raw rates diluted by orders never reviewed, so **73 % stands as the last
honest figure** ([DL-119](design-log.md) amendment). 🟢 Monday can finally supply data. 🪤 **And S189 found a second
way that number could be wrong** — an empty judge answer becomes a forced `revise`, which *counts as a veto*; 11 judge
calls returned empty, and whether any fell inside DL-119's four binding runs is S189's first task.

🚨 **NOT PROVEN — S182 live.** 2026-08-21 was checked and did not supply it: the stops INTC/NEE/XOM got carry
`stop_pct_source=position`, written eight minutes before execution ran, so the Fill+OrderIntent fallback never
fired. 🪤 **Do not re-check it this way** — run-start reconciliation now closes the very window S182 was built for.

🎯 **PACKAGED — [S189](sprints/sprint-189-an-empty-answer-says-why-it-is-empty.md), an empty answer says why it is
empty** (work-queue item 35, 2026-08-30). Neither LLM adapter reads `stop_reason`/`finish_reason`, so a **truncation**,
a **refusal** (Anthropic returns `HTTP 200` for those) and a genuinely empty answer are one recorded value.
🚨 **Item 35's framing was wrong and is corrected:** it filed this as OpenAI-fallback-only and "not currently biting".
**Measured on the live spine: 135 of 1,037 `LLMCall` rows are empty** (two agreeing signals), and **112 are
`claude-opus-5` — the primary** — against 22 for `gpt-5.5`. 🪤 **98 of the 135 are 2026-08-08 alone**, a known outage
day, so the honest steady-state figure is **~3 %** on days with no outage; quoting 13 % would repeat DL-119's own
diluted-denominator mistake. 🚨 **The worst case has no fail-safe** — `debate_turn` emits `Turn(role, n, "")` unguarded, so a
truncated argument becomes a hole in the transcript the judge rules on, and the verdict looks legitimate (proponent
**16.0 %** empty, opponent **13.5 %**). 🎯 Ready for Codex; deploy is a full `up` behind S172 and S188.

🟩 **PROVEN RESULT — [S188](sprints/sprint-188-a-credential-is-tested-before-it-is-handed-over.md) merged `108475c`
(`0.93.00`), 2026-08-30.** Master loads pack-declared credential probes, **refuses activation** when a required
credential is rejected, classifies transport failure separately so a DNS blip cannot halt the fleet, and records
sanitized evidence on `AgentInstance`. Master laws **v1.2**. `make ci` re-run by me: **2410 passed / 100.00 %**;
`GATE PROVEN` for the **merged** SHA; post-merge **CodeQL success, 0 open error-level alerts**; image build green on
re-run after a transient `403` on one of 15 jobs.
🚨 **One merge-review correction:** the sprint gated the *fallback* OHLCV credential and left the *primary* optional,
reasoning from a sentence ADR-0006's own amendment supersedes — flipped, verified against the secret map and the
vault, pinned by a test ([DL-136](design-log.md) amendment). 🪤 `credential_failure_statuses` is **inert**, recorded
with both options rather than patched.
🟠 **NOT DEPLOYED** — full `up`, and it must not land before `sched-2026-08-31`. **The live activation-refusal proof
is owed:** S188 is a code fact, not yet a fleet fact.

🟢 **[S172](sprints/sprint-172-independent-debates-run-independently.md) is UNBLOCKED, 2026-08-30** — built and
gate-proven at `5bf72c9` (checked on the tip, not just `a7e7ad1`), unmerged. 🎯 **Its K=4 measurement is scheduled
2026-09-01, after Monday's run** ([DL-135](design-log.md)): it needs `s172` images and peer `maxReplicas=4` on the
fleet, and deploying that first spends the only instrument proving the `s187` deploy and the credential path. Rollback
is a retag to **`s187`**, not `s182`. 🟩 **Monday's unknown is one link, not three** — the fleet reads
`DELIBERATOR_LLM_PROVIDER=anthropic` on all three deliberators and the vault key is byte-identical to the verified one;
untested is only whether **master hands it over**.

**Shipped and deployed, detail in the sprint docs and design log.** **S184** merged `18c41b1` (`0.91.00`), `GATE PROVEN` at `8613d72`, PM rows `PM-NEV-07/08/09` 🟩, DRIFT-042..046 `CORRECTED`, deployed `s184` with `ENV PRESERVATION` 16/16 and zero drift. Two defects the merge exposed are fixed on `chore-gate-outcome-refuses-ambiguity`: `GateOutcome.passed` re-collapsed the states S184 had just separated and now raises; CodeQL **#187** was `py/mismatched-multiple-assignment`, **the same rule and package as #177 four days earlier**, because `codeql.yml` runs only on `main` (queue item 31). 🟢 **That trap did not fire this time** — `main` at `19dc2b2` is `GATE PROVEN` on CI, Security Findings **and CodeQL**, with **0** open error-level alerts. **S182** merged `2fc0672` (`0.90.16`), deployed `s182`. 🪤 A `verify-2026-08-20-s184-a` teardown reported false success because `ScanRun` is uuid-keyed and the verification query reused the teardown's own filter ([DL-124](design-log.md)); a second pass removed 24 nodes + 25 edges and the pollers' own predicates now read **0 pending** at every stage, 22 positions intact.

🪤 **Two live residues to decide, neither urgent.** **2 NFLX shares** from the S172 test harness, never vetoed
(selling is a real trade); and one `cancel_stop` `HTTP 422`, the run's only non-billing error incident.

## Next

**Ranked queue of record: [work-queue.md](work-queue.md)** — this section is the narrative around it, not a second ranking.

🎯 **Order set by the operator, 2026-08-30.** **(1)** item 6b — *decided today, no flip* ([DL-134](design-log.md));
**(2)** item 3, S172's K=4 measurement, unblocked and first buildable; **(3)** Monday's `sched-2026-08-31` as the
proof of today's deploy — `deliberation_posture` on the `ExecutionRun` **and** `real_debate_count > 0`.

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
