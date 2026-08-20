# Project State

**Last updated:** 2026-08-21 00:05 AEST · **Version:** 0.91.01 · **Fleet still `s182`; `s184` images built and waiting.** · **PAUSED mid-deploy — main is gate-proven, the next action is `up -Tag s184`.**

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
whatever currently prevents unattended operation *is* etalon work, not a detour from it. Today that
is the **73 % veto rate** ([DL-119](design-log.md)) — a system that rejects its own orders and trades
nothing cannot demonstrate that the method produces working systems. 🪤 **Generality is a separate
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

- **The gate was red for two days over one test line (fix, no bump, 2026-08-17 —
  [DL-110](design-log.md)).** Four straight `Security Findings` failures — three on docs-only commits
  — on CodeQL #177, the only error-level alert of 76: a PM test unpacked `SectorBook.outcomes()` into
  two names, and that call returns `()` with no sector. `GATE PROVEN` for `21a5e81`. 🪤 **A branch
  cannot clear an alert raised on `main`** (`codeql.yml` runs only there), and 🪤 **the step prints
  nothing on failure** — read the report, not the log.

## Now

**PROVEN RESULT — S184 merged `18c41b1` (`0.91.00`), 2026-08-20.** ADR-0023 shipped. The PM now
aggregates concentration by **issuer** (GOOG + GOOGL = Alphabet), rejects **measured** correlated
clusters against the held book, emits `not_evaluated` for a missing sector label or too-short
history, counts held dollars in `max_sector_pct`, and carries `GateOutcome.outcome` as
`passed | failed | not_evaluated`. **Verified independently before merge:** `GATE PROVEN` for
`8613d72` from a worktree at that SHA; `make ci` reproduced at exit 0, **2360 passed / 100.00 %**;
all five `.passed` readers migrated; rollups **28 / 47** in `ledger.md` *and* `INDEX.md`;
DRIFT-042..046 `CORRECTED`. Measured behaviour change: the same GOOG/AMZN set went from both
approved to `GOOG:sizing` + `AMZN:correlated_cluster_concentration`, with **0** added provider
requests. PM law rows `PM-NEV-07/08/09` are 🟩.

🚨 **Two defects the merge exposed, both fixed on `chore-gate-outcome-refuses-ambiguity`.**
**(1)** S184 kept `GateOutcome.passed` as a two-state view that **re-collapsed the states it had just
separated** — `not_evaluated` read as *"the gate found a breach"* when the truth is *"it never ran"*.
No production reader used it; the hazard was the next one. It now raises (DL-122 amendment).
**(2)** CodeQL **#187** `py/mismatched-multiple-assignment` — **the same rule, same package, as #177
four days earlier** ([DL-123](design-log.md)). 🪤 **A green branch gate does not mean CodeQL-clean:**
`codeql.yml` runs only on `main`, so the scan that finds this class had not run when S184's branch
went green. Merge-then-verify is again the only exit — a trap that fires twice in four days is a
missing check, filed as queue item 31.

⏸️ **PAUSED 2026-08-21 00:05 AEST, deliberately between steps.** Nothing is half-applied: `main`
is `7af1583`, **`GATE PROVEN`** (CI + Security Findings + CodeQL + Build images all success, SHA
checked against `HEAD`), tree clean, `s184` images **built and pushed to GHCR**, fleet **still on
`s182`** and untouched. **Resume at step 1.**

1. `pwsh infra/deploy-agents.ps1 up -Tag s184` — 🚨 a **full `up`**, not an image retag: S184 adds
   the `trading_issuer_map.json` pack, a new `PORTFOLIO_MANAGER_ISSUER_MAP_B64` env var, and four
   tunables. 🪤 A full `up` **replaces each app's env set** (DL-100), so anything set by hand is
   reverted — the pack carries the tunables and the cron (`30 22 * * 1-5`), so this is safe.
2. Diff the result against the recorded baseline —
   `scratchpad/fleet-baseline-pre-s184.json` + `job-baseline-pre-s184.json`: **16 apps + job, all
   `s182`, min 0 / max 1, cron `30 22 * * 1-5`.** 🪤 Both previous deploys hid a scale-config drift
   that only a baseline diff caught.
3. Fire a **test run now** rather than waiting for 22:30 UTC (pre-prod; widen the KEDA window, then
   restore it). No CLI exists for a custom `verify-*` id — `orchestration/start.py::place_run_request`
   is the library call; write a scratch script with the refuse-on-in-memory guard.
4. Measure with `scratchpad/measure_veto.py`. **The "before" is already recorded** in
   `scratchpad/veto-baseline-pre-s184.txt`: **25 of 35 vetoed = 71 %** across five real binding runs,
   and **every one** carries an exposure-aggregation objection.

🚨 **NOT PROVEN — ADR-0023's falsifiable test.** The prediction is that the deliberator's
exposure-aggregation objections disappear and the **73 % veto rate falls materially**. Unit fixtures
cannot show that; only a live run can. **If the objections persist now that the PM aggregates
properly, the finding moves to the referee** — the separation the ADR was written to make possible.

- **S183 is with Codex** ([spec](sprints/sprint-183-a-gate-that-did-not-run-says-so.md)) — scanner
  attestation. 🪤 **Corrected mid-build** (`d859746`): it told Codex to register `stop_target_mode` as a
  `tunable()`, which the locked analyst law forbids on purpose. **My spec was wrong; the law was right.**
  Confirm the correction was picked up before accepting a handback.
- **[S172](sprints/sprint-172-independent-debates-run-independently.md) is unblocked** — built,
  gate-proven at `5bf72c9`, unmerged; only the 15-order K=4 measurement remains.

**PROVEN RESULT — S182 merged `2fc0672` (`0.90.16`) and deployed `s182`, 2026-08-20.** Execution
derives a protective stop from **`Fill` + `OrderIntent` lineage** when the monitor has not yet written
the `Position`; monitor keeps ownership, and the shared `contracts/position_refs.py` makes the
no-double-place guarantee structural. `make ci` **2331 passed / 100.00 %**; `GATE PROVEN` for
`2fc0672`. 🪤 **Two traps a glance would miss:** the working directory was left on Codex's branch so
the first `git merge` said *"Already up to date"* — merging the branch into itself; and the
post-deploy scale diff showed `minReplicas=1` on all 16, my own leftover. **Both caught by diffing
against a recorded baseline, not by reading output.**

**NOT PROVEN: S182 live.** The defect needs a position filled *between* runs, so no synthetic fixture
can exhibit it — proof waits on a **new** entry filling. Opportunistic.

**Test residue cleared, 2026-08-20.** Codex's 13 synthetic 1-share S172 orders cancelled; book back
to all-protective-stops, 0 non-stop. 🪤 **Two earlier attempts already filled** — the book carries
**2 NFLX shares created by a test harness**, never vetoed, still held: selling is a real trade and
needs a decision. MO and CSCO also filled and are legitimate (the clean run's upheld orders).

**S172 handed back unmerged, 2026-08-20 — correctly.** Bounded `debate_concurrency=4`, deterministic
PM-order reassembly, per-order fail-open isolation, shared correlated reply inbox, peer
`maxReplicas=4`. Tip `5bf72c9`, `make ci` **2336 / 100.00 %**, **`GATE PROVEN`** on all three
workflows (verified independently). Unmerged because the live K=4 measurement could not run — the
synthetic attempt wrote `LLMCall=0` on an OpenAI `429`. 🟢 Service Bus clean throughout, so S171's
correlation guarantee is not implicated. **Now unblocked** (queue item 3).

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

**S179 (`0.90.14`) shipped 2026-08-18 and is deployed** — `open_incidents` is a live incident
count scoped to the latest graph-run day, with append-only `FaultResolution` retirement. Detail in
its sprint doc and [STATE-08.md](state-archive/STATE-08.md).

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
