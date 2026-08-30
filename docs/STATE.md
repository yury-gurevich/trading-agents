# Project State

**Last updated:** 2026-08-30 14:55 AEST · **Version:** 0.92.02 · **🚨 THE FLEET IS 3 SPRINTS BEHIND `main`: all 16 apps + the dispatcher job run `s184`, while S185, S186 and S187 are merged. Item 6b cannot be done until that changes — the deployed code has no posture switch to flip.**

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

- **Three diagnoses, one pattern, no code changed (docs only, no bump, 2026-08-24).** Measured against
  the live spine and the broker while S186/S187 waited on handover. **Item 12's "202-fill backlog" is
  27** ([DL-129](design-log.md)) — `Fill.status` is a submit-time fact never mutated; truth is
  `broker_status` + 3,725 `BrokerOrderStatus` nodes, and the sweep skips every terminal one. **Item 20's
  228 faults are 13 objects** ([DL-130](design-log.md)) — `broker_stop` asks *is this of type stop* and
  never reads status, `graph_stop` asks *is it active*, so every cancelled stop mismatches forever; the
  broker **agrees** on all 13. **New item 32** ([DL-131](design-log.md)) — a stop that *fires* is never
  reconciled: WFC filled at Alpaca 08-21T17:00:44, still active in the graph, because `cancelled_at is
  None` is a stop's only lifecycle. 🟩 **Item 27's symptom is gone**: 24 positions / 24 stops, **1:1,
  zero unprotected** (was 22/19 and $2,147.76 on 08-19) — but its live proof is still owed, all 24 read
  `stop_pct_source=position`, so S182's fallback has never fired. 🪤 Two of the three rows were
  **counting a field that never moves** — the retracted-DL-73 class, twice more.

## Now

🚨 **MEASURED 2026-08-30 — THE FLEET RUNS `s184`; THREE MERGED SPRINTS ARE INERT.** `az containerapp
list` shows **all 16 apps** and `dispatcher-cron` on `…:s184`, while `main` is `0.92.02` carrying **S185**
(merged 08-22), **S186** and **S187** (today) — **47 commits** since the last recorded deploy.
🟩 **Corroborated at runtime, not just from tags:** `sched-2026-08-28`'s `ExecutionRun` carries **no
`deliberation_posture` property**, which S185 guarantees on every run, so the running code demonstrably
predates S185. 🚨 **Item 6b is therefore unexecutable as written** — the posture cannot be flipped to
`binding` when the deployed code has no switch; **deploy is a prerequisite, not a follow-up.** S186's `1/n`
weighting likewise is not affecting live ranking (S187 is a CI gate, so it loses nothing by waiting).
🪤 **The `DeployRecord` trail cannot catch this:** newest is `2fc0672` (S182, 08-20) and **every record
has `tag=None`, `app_count=None`** — work-queue item 21, measured. 🟠 **Target ready:** `7d36771` images
exist at `:latest` and the full SHA, one tag covering S185+S186+S187.

🚨 **The deliberator had NOT recovered as of the last run** *[measured 2026-08-30]*: `sched-2026-08-28`
still failed open on `HTTP 400`, and `real_debate_count` is **0 on every run 08-21 → 08-28**. Today is the
operator's stated restore date; nothing has verified it. 08-27 shows `failed_open_count=0` only because it
had nothing to debate.

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
every run, and unbaselined drift fails the gate. 🟠 **Not deployed** — retag owed for S186+S187 together.


🚨 **The follow-up S185 leaves behind, and it is not a defect in the sprint.** The default is `advisory` and **nothing flips it to `binding` when credit returns on 2026-08-30**. The posture DL-116 and DL-119 fought for would then be a *declared* default rather than an arithmetic accident — better, but still not binding. **Flipping it must be a decision someone makes, not something that quietly never happens.** Queued as work-queue item 6b.

**PROVEN RESULT — [S186](sprints/sprint-186-a-headline-about-twenty-companies-is-not-news-about-one.md) merged `81b82ee` (`0.92.01`), 2026-08-30** (built by Codex on 08-24, verified and merged today). The analyst computes exact-headline duplicate weights over the whole `MarketData.news` batch — a new 24-line `sentiment_weights.py` rather than growing `scoring.py` — and exposes `sentiment_batch_weighted_articles` as the batch-scoped denominator. **`GATE PROVEN` for `81b82ee`** (CI + Security Findings), re-run by me from the worktree holding it, because Codex's own proof named `4b0daaf` and the docs commit on top would otherwise have merged unproven. `make ci` re-run **today**: exit 0, **2384 passed / 4 skipped / 100.00 %**. A1-A6 planted red first; the DL-70 violation (all weights forced to 1.0) failed A1 at `50.0 == 66.67`. Law cycle: analyst laws **v1.2**, `ANLZ-OBS-04` 🟩, ledger *and* INDEX **24 / 47**. [DL-132](design-log.md) records four decisions with alternatives, and decision 2 is **measured** — exact, whitespace-collapsed, casefolded and mojibake-normalised matching all give identical counts, so no normalisation was added on instinct. 🪤 It also **corrected my spec**: `DUK/GILD/MET/TGT` are news-only in the fixture, so their *stored confidence* could not be asserted; it proved weighted-vs-unweighted identity on their real headlines instead. 🟠 **Not deployed, and no live post-merge read yet** — image-only retag is owed, and 5 scheduled runs (08-24…08-28) have happened since the measurement.

🟩 **PROVEN LIVE — ADR-0023's PM half, unattended, first time.** GOOG and GOOGL landed in the same
batch — the exact case the ADR was written for. GOOG passed sizing at `issuer=alphabet;
existing_issuer_value_usd=0.00` → **0.998 %**; GOOGL then **failed** at `existing_issuer_value_usd=1025.19`
→ **1.67 % > 1 %, `outcome=failed`**. 🚨 **Pre-S184 both would have passed** (1.00 % and 0.67 % sized
alone) and the run would have opened **two positions in one company**. Also visible in the same gate
report: issuer-level `max_positions`, `max_sector_pct` counting `held_sector_value_usd=1092.36`, and a
three-state `correlated_cluster_pct` ([DL-122](design-log.md) amendment).

🚨 **NOT PROVEN, and now un-measurable until 2026-08-30 — ADR-0023's falsifiable test.** The
prediction is that the deliberator's exposure objections vanish and the **73 % veto rate falls
materially**. It has **zero real-debate data on `s184` code**. 🪤 **Neither of the two runs since
counts, and both look like they might:** `sched-2026-08-20` reads 40 % and `sched-2026-08-21` reads
0 %, but both are raw rates diluted by orders never reviewed — of the 2 orders actually debated on
08-20, **2 were vetoed**. A veto rate over unreviewed orders is not a veto rate. The 73 % stands as
the last honest figure ([DL-119](design-log.md) amendment).

🚨 **NOT PROVEN, and 2026-08-21 was checked and did not supply it — S182 live.** INTC/NEE/XOM
filled between runs, raised `missing_graph_position` flags, and got stops — but each stop carries
`stop_pct_source=position`, from a `Position` `position_sync` had written at 22:31:52, **eight minutes
before execution ran**, so the Fill+OrderIntent fallback never fired. 🪤 **Do not re-check it this
way:** run-start reconciliation now closes the very window S182 was built for.

**PROVEN RESULT — S183 accepted and merged, `0.91.02`, 2026-08-22** ([spec](sprints/sprint-183-a-gate-that-did-not-run-says-so.md)). A scanner gate that could not run now says so: `Candidate`/`FilterVerdict` carry `skipped_filters`, no-earnings-date is attested, a *known past* date is an evaluated pass, thin beta is attested, and the packet renders the stop's basis. **All 9 success factors met; `GATE PROVEN` for `27fa3f5`** (SHA checked against the worktree HEAD). 🪤 **The mid-build correction held.** 🚨 **Three merge-time defects were mine, not Codex's:** a DL number that collided with `main`'s DL-121 (→ **DL-126**); a bump `0.90.17` that would have *lowered* `0.91.01`; and **a spec that never asked for a law cycle** although the sprint changed `contracts/scanner.py` under a LOCKED law book, one day after S184 did exactly that cycle. Closed, not filed: `SCAN-OUT-06`/`SCAN-OUT-07` (laws **v1.1**), rollup **18 / 41** 🪤 *the gate corrected my 19 — two clauses proven by three rows is +2*, and `DRIFT-047` for the `SCAN-TYP-01` clause the change slipped under (item 30's class). **The omission is now a required section in [`_TEMPLATE.md`](sprints/_TEMPLATE.md).**
- 🪤 **[S172](sprints/sprint-172-independent-debates-run-independently.md) is RE-BLOCKED** — built and
  gate-proven at `5bf72c9`, unmerged. Its 15-order K=4 measurement needs real debates, so it cannot
  merge before **2026-08-30**. The "unblocked 2026-08-19" note is withdrawn in the queue.

**Shipped and deployed, detail in the sprint docs and design log.** **S184** merged `18c41b1` (`0.91.00`), `GATE PROVEN` at `8613d72`, PM rows `PM-NEV-07/08/09` 🟩, DRIFT-042..046 `CORRECTED`, deployed `s184` with `ENV PRESERVATION` 16/16 and zero drift. Two defects the merge exposed are fixed on `chore-gate-outcome-refuses-ambiguity`: `GateOutcome.passed` re-collapsed the states S184 had just separated and now raises; CodeQL **#187** was `py/mismatched-multiple-assignment`, **the same rule and package as #177 four days earlier**, because `codeql.yml` runs only on `main` (queue item 31). 🟢 **That trap did not fire this time** — `main` at `19dc2b2` is `GATE PROVEN` on CI, Security Findings **and CodeQL**, with **0** open error-level alerts. **S182** merged `2fc0672` (`0.90.16`), deployed `s182`. 🪤 A `verify-2026-08-20-s184-a` teardown reported false success because `ScanRun` is uuid-keyed and the verification query reused the teardown's own filter ([DL-124](design-log.md)); a second pass removed 24 nodes + 25 edges and the pollers' own predicates now read **0 pending** at every stage, 22 positions intact.

🪤 **Two live residues to decide, neither urgent.** **2 NFLX shares created by the S172 test
harness**, never vetoed — selling is a real trade; and one `cancel_stop` `HTTP 422`, the run's only
non-billing error incident.

## Next

**Ranked queue of record: [work-queue.md](work-queue.md)** — this section is the narrative around it, not a second ranking.

🚨 **Re-ranked 2026-08-22: work-queue item 6 is first** — a declared advisory/binding posture, the
only queued item that changes what the next ~6 unvetoed nights *mean*, and the only one that needs no
LLM to build or prove. Item 3 (S172) drops to second **because it is blocked, not because it shrank**;
item 9 (S173) is provider-blocked too. **Items 28, 29, 26, 12, 20, 21, 22, 30, 31 and 11 are not, and
they are what these six sessions can actually ship.**

**Ahead of the numbered list — three questions raised and not yet answered.**

**The measurement that reorders everything below it.** `0.90.02` made the `effort` tunable reach the
wire, so the two free latency levers are measurable for the first time. Sweep **`effort` down from
`max` first** — it is the only lever that costs nothing. Then `max_rounds` 2 → 1 **only if that is
not enough**: 🚨 its own `why` says *"debate must show more than one round in live proof"*, so one
round is **cutting the artefact under test to buy wall clock**, a recorded decision rather than a
knob. Build [S172](sprints/sprint-172-independent-debates-run-independently.md) **only if both
together still miss** — full ordering and the arithmetic in [DL-105](design-log.md)'s amendment.
The sweep's first point is **done** — `effort` `max` → `high`, live since 2026-08-12 — and it
cost three fail-opens before `request_timeout_seconds` went 30 → 60, **which then proved out at 0
fail-opens** on the runs of 2026-08-18/19 — a figure the billing outage has since made unreadable,
since every debate now fails open for an unrelated reason. The two levers are
**coupled**: raising effort lengthens the peer-call tail into a fixed timeout. Measure both
together or not at all.

**Undecided, recorded so they are not re-derived** — all raised 2026-08-11, none actioned:
**(i)** ~~amend S172~~ **DONE 2026-08-19** — the unsound `max_rounds` reason is replaced (a 1-round debate is a different artefact, not a faster one), the build-trigger is now **measured** and in the spec (**15 orders breaches the 1800 s grace**), the stale `effort`/S169 traps are corrected, and a Codex handover block is written;
**(ii)** ~~collapse to one ranked queue~~ **DONE 2026-08-19** — the out-of-repo `debt.md` was **deleted**, not reconciled: it was a 2026-08-14 ancestor of `work-queue.md` and all 8 of its unique references were fragments of closed items. The queue was pruned 255 → 99 lines (11 closed rows removed, 2 folded into parents, every carried number re-measured); **(iii)** stop pinning version numbers in sprint
specs (*"next available PATCH/MINOR at merge"*) — after three renumberings in one day.

1. 🪤 **WITHDRAWN 2026-08-22 — the premise is dead, measured on the contract predicate.** This item
   read: *"47 unresolved critical Flags pin `healthy=false` and `pending_human_flags=47` forever."*
   `compute_health` returns **`pending_human_flags=0`**: all **60** Flags carry a `FlagResolution`
   (S178/S179 closed this). `Flag.status` stays `pending` **by design** — the resolution is a separate
   node, exactly like `Position.status` staying `open`. **I ranked this #1 on a raw-prop count for a
   second time.** What actually pins `healthy=false` is `open_incidents`, today **5** — 3 of them the
   billing outage, which clears itself on 2026-08-30. 🪤 This item had *already* been retracted once
   (2026-08-15, the AVGO `overturn` false premise); it is now retracted on its remaining half too.
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
