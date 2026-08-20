# Project State

**Last updated:** 2026-08-21 00:20 AEST · **Version:** 0.91.01 · **Fleet `s184`, asleep.** · **S184 is deployed and drift-free; the 71 % veto rate it must move is measured tonight, unattended.**

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

🟢 **DEPLOYED `s184` and put back to sleep, 2026-08-21.** Full `up` (not a retag — S184 adds the
issuer-map pack, `PORTFOLIO_MANAGER_ISSUER_MAP_B64` and four tunables). `ENV PRESERVATION` **16/16**,
so the DL-100 guard confirmed the `up` would drop no live env key. **16/16 apps on `s184`; scale *and*
KEDA-rule metadata diffed to zero drift** against the recorded baseline; `dispatcher-cron` `s184`,
cron `30 22 * * 1-5`. PM env carries all five S184 keys, each verified PRESENT. 🪤 `curator` failed once on an
Azure `InternalServerError`, was left cleanly on `s182` (`Succeeded`, not broken) and took a targeted
image retry — it carries no pack tunables, so only the image differed. 🪤 The `min-replicas 1` bump used
to run off-window was **restored to 0 and re-diffed**; that leftover was the S182 deploy's defect.

🚨 **A test run was abandoned, and the first teardown reported false success** ([DL-124](design-log.md)).
`verify-2026-08-20-s184-a` read `MarketData=0` at 14:05 — taken for *"nothing happened"* when it meant
*"nothing yet"*: the paced ingest was in flight. The provider finished at ~14:09 and the scanner
consumed it (99 evaluated, **23 candidates**) whose `AnalystRun` was missing, i.e. **live pending work that
would have run a second cascade tonight**. 🪤 The teardown could not see it: `ScanRun` is keyed
`scanner-run-<uuid>` with `run_id=None`, and **the verification query used the same filter**, so it
confirmed the teardown instead of testing it. A second pass on the uuid removed **24 nodes + 25 edges**.
Now proven with the pollers' own predicates: **provider 0 / scanner 0 / analyst 0 / pm 0 pending**, 22 positions intact. 🪤 A watcher caught this after the point check said clean.

🚨 **The measurement is tonight's 22:30 UTC scheduled run — unattended, on the production path**, which
is a better test than the one abandoned: no operator in the loop is the actual bar.

🚨 **NOT PROVEN — ADR-0023's falsifiable test.** The prediction is that the deliberator's
exposure-aggregation objections disappear and the **73 % veto rate falls materially**. Unit fixtures
cannot show that; only a live run can. **If the objections persist now that the PM aggregates
properly, the finding moves to the referee** — the separation the ADR was written to make possible.

- **S183 is with Codex** ([spec](sprints/sprint-183-a-gate-that-did-not-run-says-so.md)) — scanner
  attestation. 🪤 **Corrected mid-build** (`d859746`): it told Codex to register `stop_target_mode` as
  a `tunable()`, which the locked analyst law forbids on purpose. **My spec was wrong; the law was
  right.** Confirm the correction was picked up before accepting a handback.
- **[S172](sprints/sprint-172-independent-debates-run-independently.md) is unblocked** — built,
  gate-proven at `5bf72c9`, unmerged; only the 15-order K=4 measurement remains.

**PROVEN RESULT — S182 merged `2fc0672` (`0.90.16`) and deployed `s182`, 2026-08-20.** Execution
derives a protective stop from `Fill` + `OrderIntent` lineage when the monitor has not yet written the
`Position`; `contracts/position_refs.py` makes the no-double-place guarantee structural. 🪤 **Two traps
a glance would miss:** the working directory was left on Codex's branch, so the first `git merge` said
*"Already up to date"* — merging the branch into itself; and the post-deploy scale diff showed
`minReplicas=1` on all 16, my own leftover. **Both caught by diffing against a recorded baseline.**

**NOT PROVEN: S182 live.** The defect needs a position filled *between* runs, so no synthetic fixture
can exhibit it — proof waits on a **new** entry filling. Opportunistic.

**Test residue cleared, 2026-08-20.** Codex's 13 synthetic 1-share S172 orders cancelled. 🪤 Two
earlier attempts already filled, so the book carries **2 NFLX shares created by a test harness**,
never vetoed, still held — selling is a real trade and needs a decision.

**S172 handed back unmerged, 2026-08-20 — correctly.** Bounded `debate_concurrency=4`, deterministic
PM-order reassembly, per-order fail-open isolation. Tip `5bf72c9`, **`GATE PROVEN`**. Unmerged because
the live K=4 measurement could not run (OpenAI `429`). **Now unblocked** (queue item 3).

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
