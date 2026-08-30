# Project State

**Last updated:** 2026-08-30 20:02 AEST · **Version:** 0.93.00 · **🟢 [S188](sprints/sprint-188-a-credential-is-tested-before-it-is-handed-over.md) is built and branch-gate proven: master credential tests now reach activation as pack data, required failures refuse handover, and local/remote gates are green; merge, deploy, and live proof remain pending.**

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
`pwsh infra/deploy-agents.ps1 up -Tag s187` exit 0. **Verified independently of its own output:** **16/16**
apps on `s187`, **16/16** `Succeeded`, **16/16** KEDA `min=0 max=1, 1 rule` — *identical to the baseline
captured before deploying* — and `dispatcher-cron` on `s187`, cron `30 22 * * 1-5`. `DeployRecord` carries
the **build run's** head SHA `7d2339bc5a4f`, read from the run not handed in (item 21's defect).
🚨 **`up` was required, not an image-only retag:** S185's `e370f88` moved the vocabulary pack
(`8777b907…` → `93dab2e6…`), and a retag against a stale pack hits the fail-closed write guard mid-cascade
(S148 stall, DL-85). 🪤 **The first attempt failed and changed nothing** — the S169 guard threw at
Service Bus route prep *before* the first app create. Cause was local — a corrupt `azure-core` (dist-info
with no `RECORD` file) that still looked installed; preflight never imports the deps its own steps need, so
it surfaced *after* alembic ran. Full account in **item 34**.
🟠 **Not yet proven at runtime:** Monday's run (2026-08-31, 22:30 UTC) must show
`deliberation_posture` on its `ExecutionRun` — its absence on `sched-2026-08-28` is what proved the fleet
was behind.

🟩 **PROVEN RESULT — BOTH PROVIDERS VERIFIED BY DIRECT API CALL, 2026-08-30 17:00 AEST.** `claude-opus-5`
and `gpt-5.5` each returned **HTTP 200** with content; the outage that began 2026-08-19 ([DL-125](design-log.md))
is **over**. 🪤 **The Anthropic half was not a credit problem** — `HTTP 400 invalid_request_error`, *"your
**specified** API usage limits"*, is an **operator-set** spend limit, distinct from the tier cap (`429` +
`enforced_spend_limit_reached`). Raising it in Console → Billing restored access at once; the `2026-09-01` in
the message was only the month reset. 🚨 **Verified from this machine, not the fleet** — the deliberator
takes credentials via master/Key Vault, untested since the outage. Monday's run (08-31, 22:30 UTC) proves that
*and* the deploy: expect `real_debate_count > 0` **and** `deliberation_posture` on the `ExecutionRun`.
🟢 **Unblocks** item 6b (a real veto now, not a halt) and item 3 (K=4 needs real debates).

🟩 **PROVEN RESULT — [S187](sprints/sprint-187-a-parameter-is-declared-once.md) merged `7d36771` (`0.92.02`), 2026-08-30.**
`scanner.benchmark_ticker` is a registered `tunable()` (default `"SPY"` unchanged); provider laws
**v1.1** declare `alpaca_data_feed` and `ingest_ohlcv_only` `NO (mode selector)`; execution laws
**v1.3** declare `deliberation_grace_seconds`, which **closes DRIFT-049** — the row S185 left open for
this audit. `make ci` gained a **12th step**, PARAM/settings sync, with a `gate_selftest` probe proving
it can fail. **`GATE PROVEN` for `7d36771`**; `make ci` re-run by me: exit 0, **2390 passed / 4 skipped /
100.00 %**. 🚨 **The audit found 20× what the sprint was scoped for** — **60** PARAM/settings presence
divergences across nine agents; 3 fixed, **57 baselined** as warning-only so a small sprint did not
become a nine-agent law cleanup ([DL-133](design-log.md) decision 3, with a retire trigger;
**DRIFT-052** open; now ranked as work-queue item 33). The 57 print as `[WARN]` with `file:line` on
every run, and unbaselined drift fails the gate. 🟩 **Deployed** in `s187`.

**PROVEN RESULT — [S186](sprints/sprint-186-a-headline-about-twenty-companies-is-not-news-about-one.md) merged `81b82ee` (`0.92.01`), 2026-08-30** (built by Codex on 08-24, verified and merged today). The analyst computes exact-headline duplicate weights over the whole `MarketData.news` batch — a new 24-line `sentiment_weights.py` rather than growing `scoring.py` — and exposes `sentiment_batch_weighted_articles` as the batch-scoped denominator. **`GATE PROVEN` for `81b82ee`** (CI + Security Findings), re-run by me from the worktree holding it, because Codex's own proof named `4b0daaf` and the docs commit on top would otherwise have merged unproven. `make ci` re-run **today**: exit 0, **2384 passed / 4 skipped / 100.00 %**. A1-A6 planted red first; the DL-70 violation (all weights forced to 1.0) failed A1 at `50.0 == 66.67`. Law cycle: analyst laws **v1.2**, `ANLZ-OBS-04` 🟩, ledger *and* INDEX **24 / 47**. [DL-132](design-log.md) records four decisions with alternatives, and decision 2 is **measured** — exact, whitespace-collapsed, casefolded and mojibake-normalised matching all give identical counts, so no normalisation was added on instinct. 🪤 It also **corrected my spec**: `DUK/GILD/MET/TGT` are news-only in the fixture, so their *stored confidence* could not be asserted; it proved weighted-vs-unweighted identity on their real headlines instead. 🟩 **Deployed** in `s187`; the live post-merge read is Monday's run.

🟩 **PROVEN LIVE — ADR-0023's PM half, unattended, first time.** GOOG passed sizing at
`existing_issuer_value_usd=0.00` → 0.998 %; GOOGL then **failed** at `1025.19` → 1.67 % > 1 %. 🚨 Pre-S184
both would have passed and the run would have opened **two positions in one company** ([DL-122](design-log.md)).

🚨 **NOT PROVEN — ADR-0023's falsifiable test** (the 73 % veto rate falls materially). **Zero real-debate data**
on `s184` code; the 40 % and 0 % readings from 08-20/08-21 are raw rates diluted by orders never reviewed, so
**73 % stands as the last honest figure** ([DL-119](design-log.md) amendment). 🟢 Monday can finally supply data.

🚨 **NOT PROVEN — S182 live.** 2026-08-21 was checked and did not supply it: the stops INTC/NEE/XOM got carry
`stop_pct_source=position`, written eight minutes before execution ran, so the Fill+OrderIntent fallback never
fired. 🪤 **Do not re-check it this way** — run-start reconciliation now closes the very window S182 was built for.

🟢 **BUILT + BRANCH-GATE PROVEN — [S188](sprints/sprint-188-a-credential-is-tested-before-it-is-handed-over.md), credential
tested before handover** (`0.93.00`, 2026-08-30). Credential tests now load via
`MASTER_CREDENTIAL_TESTS_B64` / path fallback, stay pack data, and run inside master activation without importing
`orchestration/` or provider SDK code. Required credential rejection refuses activation before `AgentInstance`;
transport failure faults without blocking or caching; optional failure records without blocking; successful activation
records declared/tested/pass/cache/failure evidence. Local `make ci` exit 0: **2410 passed / 4 skipped / 100.00 %**.
Remote `make gate-ran`: **GATE PROVEN** for `33b0cd5571e5ea5a1c7b307744b4f6560e9559be`. 🟠 Merge, full `up`,
and live declaration-only refusal proof remain pending; sequencing still says do not deploy before Monday's scheduled
run proves the current `s187` fleet.

🟢 **[S172](sprints/sprint-172-independent-debates-run-independently.md) is UNBLOCKED, 2026-08-30** — built and
gate-proven at `5bf72c9` (checked: CI + Security Findings + image build all `success` on the tip, not just on
`a7e7ad1`), unmerged. 🎯 **Its K=4 measurement is scheduled 2026-09-01, after Monday's run** ([DL-135](design-log.md)):
it needs `s172` images and peer `maxReplicas=4` on the fleet, and deploying that first would spend the only
instrument that proves the `s187` deploy and the credential path. Rollback is a retag to **`s187`**, not `s182`.
🟩 **Monday's unknown is now one link, not three** — the fleet reads `DELIBERATOR_LLM_PROVIDER=anthropic` on all three
deliberator apps, and `trading-agents-kv/anthropic-api-key` is byte-identical to the `.env` key that returned `HTTP 200`
(SHA-256, never printed). Untested is only whether **master hands that secret over** — see S188 below.

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
