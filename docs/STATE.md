# Project State

**Last updated:** 2026-10-09 20:35 AEDT · **Version:** **0.125.00 deployed** (`s262`, image-only retag from `d01b71b3`, rollback `s259a` with the master's eight-probe pack) · **[S262](sprints/sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it.md) is deployed: the fleet's LLM vendor is declared in one file, a full `up` keeps it, and the command applied and proved it on the fleet; the dashboard chat on OpenAI is verified failing (work-queue 121); debates run three at once, as a live setting.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + [`state-archive/`](state-archive/INDEX.md) `STATE-01…18.md` + git). **LAW-02:** an item is "shipped" only when
its success factors are *proven* (tests, `make ci`, the named live check) — never restate intent as outcome.
**Size rules**, after this file reached 574 lines with a **112 KB header line**, and then 76 KB inside
200 lines: keep it **under 40 KB** ([housekeeping charter](../ops/departments/housekeeping/charter.md), G-SIZE) and under 200 lines,
and keep the header above to **three clauses — stamp, version, one headline**. Replace that headline
each session; never append a fourth. A *Now* entry on which nothing is owed leaves for the archive; a
condition that stays true lives under *Standing conditions*, never in the header.

---

## Current focus

**The bar, set by the operator 2026-08-20.** The etalon is done when **the pack trades unattended
for a sustained stretch and the evidence discipline catches its own defects without the operator in
the loop.** Not "trading is finished" — but far above where it is. 🚨 **Consequence for ranking:**
whatever currently prevents unattended operation *is* etalon work, not a detour from it. 🪤
**Generality is a separate unproven axis:** ADR-0012's platform/pack wall stays *de jure* until a
second pack exists, and clearing this bar does not close that.

Since P14 the project runs as **etalon-first continuous improvement** (DL-19).
**The platform is self-driving in paper mode**: the DEPLOYED, STANDING fleet (16 Container Apps +
`dispatcher-cron` job, KEDA scale-to-zero windows, idle ≈ $0) places a calendar-gated `RunRequest`
at 22:30 UTC daily, runs graph-pull + served-over-Service-Bus on the Neon Postgres spine (ADR-0014),
reconciles holdings against the broker (DL-44), debates vetoes under compiled prompts (DL-42), and
proves `ACCEPTANCE PASS`. Pausing = disable the job + zero the scale windows (`docs/deployment.md`).
Completed arcs live in their sprint docs + archives: fleet (DL-35), credentials (DL-36), Postgres
migration (DL-43), deliberation quality (DL-41/42). Layer-3 acceptance 🟩 at the full S&P-500;
Layer-2 choreography 🟩 on a distributed run (S102).

### Standing conditions — live, each with what lifts it

- **The fleet is on `s262`** = `0.125.00` (`d01b71b3`), since 2026-10-09 20:16 AEDT. Rollback: `s259a`,
  with the hand-made eight-probe pack put back on the master in the same step (the older image
  ignores the declared provider and would run Anthropic's probes).
- **The debate runs on OpenAI (`gpt-5.5`)**, declared in `orchestration/packs/trading_llm.json` and
  kept by a full `up` since `s262` ([DL-282](design-log.md)); the master runs and counts OpenAI's
  probes alone. The Anthropic account is out of credit until 2026-10-11. **The operator's dashboard
  chat stays dark:** it is on Anthropic, and it cannot run on OpenAI until work-queue 121 is fixed.
- **The manager's wait is 240 seconds, live only** on `deliberator-manager`; the pack says 120. A full
  `up` puts 120 back, and a rollback to `s255` or older must set 120 first.
- **The five-minute message lock is live only** on the two debater subscriptions; a re-created
  subscription reverts to one minute.
- **The fidelity count restarted at `sched-2026-10-08`.** Four clean sessions and ten judged PM
  recommendations are needed before EXP-014 may start ([DL-237](design-log.md)). A deploy that changes a
  decision path restarts it; the retag to `s262` changed none.
- **Debates run three at once, live only** (operator, 2026-10-09; [DL-277](design-log.md) amendment 2):
  the manager's `DELIBERATOR_DEBATE_CONCURRENCY` is 3 and each debater app has three replicas in the
  nightly window. The pack says 1, so a full `up` puts 1 back on all three. F2 is owed on the first
  scheduled night with more than one debated buy (work-queue 113).
- **[EXP-019](research/experiments/EXP-019-do-the-debaters-know-what-an-order-hinges-on.md) is
  interrupted** at 31 of 52 calls; $2.80 is approved for the rest, on Opus, after 2026-10-11.

## Now

🧹 **IN PROGRESS — the first tracker trim, 2026-10-09 ([housekeeping charter](../ops/departments/housekeeping/charter.md) v0.2: OPS-TRIM and gate G-SIZE; operator: *"yes, please"* to a maintenance schedule for the frequently edited files).** INTENT: each of the seven most-edited trackers is under its size limit in bytes, everything removed from one is in the place the charter names, every link resolves, and the limits become a step of `make ci`. Success factors: the seven sizes against their limits; for each move, the count before equals live plus archived; `check_markdown_links.py` and `check_sprint_status.py` exit 0. PROVEN so far: this file, 76 KB → 28 KB against a limit of 40; its header, 24 *Now* entries on which nothing was owed, 12 lines of *Recent* and the September narrative under *Next* moved verbatim to [state-archive/STATE-18.md](state-archive/STATE-18.md). **Merged 2026-10-09 16:47 AEDT (`4a88282e`), the Librarian's pass over three trackers, re-measured by the planner on top of the day's commits:** the work queue 251 KB → 48 KB (limit 64), the sprints README 178 KB → 87 KB (limit 96), the sprints INDEX 121 KB → 24 KB (limit 48); all 115 queue ids are in the live table (23) or the archive (92), every live row equals its text before the trim, all 265 README rows are present, and the link check and the sprint-status check exit 0 with the same count line as before. Two closed rows (111, 112) stay in the queue until the next trim. NOT yet met: the design log (1,249 KB against 512) and the functionality-check register (264 KB against 160), which the Librarian left because moving design-log entries would leave 12 links dead and the register is two tables in two orders; the gate step (sprint 261 and work-queue 117 are reserved for it, not specced).

🚀 **DEPLOYED `s262` 2026-10-09 20:09 to 20:31 AEDT (09:08 to 09:31 UTC), image-only retag, on the operator's word (*"ok for both"*) — [S262](sprints/sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it.md) (work-queue 109, [DL-282](design-log.md)), `0.125.00`, fast-forwarded to `d01b71b3`, tag `v0.125.00`, GATE PROVEN.** INTENT: one pack file declares the fleet's LLM vendor; the master runs and counts only that vendor's probes and hands over only its key; a full `up` keeps it; one command applies it to the live apps and reads the proof from the graph; the operator's dashboard chat follows it. PROVEN (F1a, [functionality checks](laws/functionality-checks.md)): build 15 of 15 in one attempt from the release tag; 16 of 16 apps and the job on `s262`, 0 of 16 differing from the before-snapshot image aside; 15 of 15 agent types activated, 0 Escalations, Faults or Flags; the master given its vendor and two packs in one update, and its fleet check **passed over 15 agent types** on the full 13-probe pack; the command reported the operator as the one app differing, applied it, found nothing else moved, and read a passed fleet check and the operator active on OpenAI's probe alone, inside 90 seconds; `DeployRecord` written; no decision path differs from `v0.123.04`, so the fidelity count stands. 🔴 **NOT met, verified failing (F1b):** the dashboard chat on OpenAI. `gpt-5.5` refuses the adapter's call with HTTP 400, first for the effort `max`, then for any reasoning effort with a function tool on that endpoint; nothing was spent; work-queue 121. 🔴 The spec's order for the master (provider, then packs) would have stopped it at start; measured offline before acting. NOT exercised live: the command changing the master or more than one app; the return to Anthropic. **Owed:** **F2** on the first scheduled run (8 / 8; each deliberator and the operator activated with OpenAI's probe passed and Anthropic's not declared; no `Escalation`).

🟩 **MERGED — [S252](sprints/sprint-252-every-finder-fetches-only-its-pending-work.md) (work-queue 101 and 106, DRIFT-097 / DRIFT-100, [DL-261](design-log.md)), `0.121.03`, fast-forwarded to `dd22b348` so the merged SHA is the gated SHA, tag `v0.121.03`, 2026-10-02; **deployed `s255` 2026-10-08**, F2 owed on the first scheduled run.** INTENT: all thirteen pending-work finders find their work by key and edge and fetch props only for it. Built by Codex in `../ta-s252`, complete against the checklist: the forecaster's two finders, the deliberator's, execution's two and the monitor's position sync use `kernel.graph_pending`; the monitor finds its sync work from the `RunRequest` side; a guard reads the source and fails on a finder with no payload case; forecaster laws v1.10, deliberator v1.12 (27 / 59), execution v1.12 (40 / 66, new `EXEC-TRG-08`), monitor v1.3. PROVEN: Windows `make ci` exit 0 (**3,966 passed, 8 skipped, 100.00 %**), including the dependency audit the builder's sandbox could not run; **`GATE PROVEN` for `dd22b348`**, measured from the proving worktree; CodeQL 131 = 131; `uv lock` changed only the version line. **F1 PASS** ([functionality-checks](laws/functionality-checks.md)): `main`'s finders and the branch's on the live graph, 44 comparisons, every pending set equal and in the same order; one idle poll reads 12.47 MB (forecaster), 4.72 MB (deliberator), 1.08 MB (execution) and 0.42 MB (monitor) before, and a key query after. Planner's review: 🔴 the handback's `mypy` PASS did not reproduce (one error in the test clock, on the handback's own commit); fixed at merge, two lines in a test helper. Rebased over S253, the shared law and sprint tables merged row by row. NOT yet met: the fleet's received bytes. **Owed:** **F2** (the first scheduled run on `s255`: 8 / 8, and `RxBytes` for the four apps down at least tenfold from 2,295, 1,021, 403 and 143 MB).

🚀 **DEPLOYED `s259a` 2026-10-08 22:34–22:41 AEDT (11:34–11:41 UTC), image-only retag (operator: *"tonight"*); rollback `s257`.** INTENT: put S259's three rewritten law books on the fleet before the night's run, so the fidelity count starts on them; the runtime code is the code of `s257`. PROVEN: the three injected packs hash the same at `b0831f64` and `49146e40`, no file under `infra/`, the packs, the workflows or a Dockerfile moved, and outside `docs/`, `scripts/` and `tests/` only four law books and the version line differ; build `37770503860` **15 / 15** in one attempt from the gated `49146e40`, dispatched on the release tag; done outside the nightly window; **16 / 16** apps and `dispatcher-cron` on `s259a`, all `Succeeded`, latest = ready; 0 of 16 apps differ from the pre-retag snapshot in container, scale, secrets, ingress, registries or identity, image aside, and the job differs in its image alone; the three deliberators still read `openai` and the manager's wait is still 240 seconds; `DeployRecord` written; **15 of 15** agent types activated on the new images (11:35–11:41 UTC) with their credentials passed; 0 Escalations, 0 Faults, 0 Flags; every app back at 0 replicas; both debater request subscriptions still hold the five-minute lock. The master's outgoing replica was killed after its 30-second stop grace at each retag (exit code 137), as at both earlier retags of the day: the replica being scaled down, not a serving one (work-queue 116). 🔴 **It took two retags.** The first, to `s259` at 22:09 AEDT, was verified the same way and then could not be recorded: one job of its build had been re-run after the vulnerability scanner failed to download its database, and the record script cannot prove a build whose log archive holds the re-run job alone ([DL-278](design-log.md), work-queue 115). A tag the fleet has pulled is not pushed again, so the same commit was built afresh as `s259a`. 🪤 The 240 seconds is live only: a full `up` puts back the pack's 120. **The first scheduled run on this tag, `sched-2026-10-08`, read 8 / 8 on 2026-10-09**, and the F2s of S253 to S257 passed on it (*Recent*). **Owed:** S252's F2 (`RxBytes` for the four apps, readable once that run's window has closed at 00:30 UTC) and, at the same scale-down, how the master's container ended (work-queue 116). The fidelity count's first session is that run; its worktree is to be pinned at `v0.123.04`. ([functionality-checks](laws/functionality-checks.md))

## Recent (most recent first — detail in each sprint doc)

🟩 **2026-10-09 15:54–16:01 AEDT — debates side by side proven once on the fleet at three at once (work-queue 113, [DL-277](design-log.md) amendment 1; operator: *"yes, it can. go ahead"*).** INTENT: six synthetic buys are debated by the deployed manager and debaters at three at once with no reply lost, no order can reach the broker, and everything changed is put back. PROVEN: 6 of 6 really debated, 0 failed open, 0 orphaned replies, 0 Faults; 30 calls on `gpt-5.5`, all ended on `stop`, $3.72 against a ceiling of $5.50; three replicas of each debater ran and activated; the record landed 6.9 minutes after the seed (2.26 lanes); execution and the portfolio manager at 0 replicas throughout; the synthetic run deleted from the graph and the four apps equal to their snapshot ([functionality-checks](laws/functionality-checks.md)). NOT proven: a night-sized batch, execution reading the record, and absence of an intermittent failure (one run).

🟩 **2026-10-09 — [S260](sprints/sprint-260-debates-at-once-lose-no-reply-and-the-repo-can-show-it.md) merged as `0.124.00` (`19239d25`, tag `v0.124.00`, GATE PROVEN, no deploy), and F1 passed.** INTENT: the repository holds a command that runs the production debate manager and debaters at one to four debates at once with a canned model, and tests that go red if a reply is lost at one request a pass or if the September setting stops failing. PROVEN: built by Codex, complete against its checklist; the planner put the kernel's old default of ten back and the four-at-once test failed; `make ci` exit 0 (4,436 passed, 100.00 %); on disposable topics of the live namespace, on the merged `main`, one to four at once are all clean (8 orders, 32 turns of 20 s: 713, 356, 269 and 181 s) and ten requests a pass fails 2 of 4 orders open; every topic deleted, the fleet's subscriptions unchanged ([functionality-checks](laws/functionality-checks.md)). NOT proven: anything on the fleet (Postgres, replicas scaling out, the vendor's rate limit). The dial stays at 1; the paid proof at three at once is the operator's call (work-queue 113).

🟩 **2026-10-09 — `sched-2026-10-08`, the first scheduled run on `s259a`: 8 / 8, the first buy debated on OpenAI on a scheduled run, and the F2s of [S253](sprints/sprint-253-a-runs-snapshot-counts-what-the-broker-filled.md), [S254](sprints/sprint-254-each-debater-turn-is-run-by-dspy-and-the-prompt-does-not-change.md), [S255](sprints/sprint-255-the-packet-states-the-score-arithmetic.md), [S256](sprints/sprint-256-a-served-request-is-settled-when-it-is-taken.md) and [S257](sprints/sprint-257-a-debaters-turn-may-write-16384-output-tokens.md) passed** ([functionality-checks](laws/functionality-checks.md)). One buy (TMO, 1 share) was debated in 222 seconds on `gpt-5.5`, ruled `revise` and submitted for the open: five calls, none cut, none failed open, $0.76. No `Fault`; the broker and the graph agree on 34 names, each with its stop; equity $101,560.84. Work-queue 111 and 112 closed. TMO and DE were stopped out in the session and the run re-bought TMO ([DL-240](design-log.md) amendment). The five entries are in [STATE-18.md](state-archive/STATE-18.md).

🟩 **2026-10-08 — [S259](sprints/sprint-259-the-eight-excused-law-rows-state-the-codes-bounds.md) merged as `0.123.04` and deployed `s259a` before the fidelity count's first session; work-queue 114 closed.** [S258](sprints/sprint-258-a-law-rows-numbers-are-compared-with-the-code.md) merged the same day as `0.123.03`, no deploy: the parameter step of `make ci` compares every law row's default and bounds with the code, and no row is excused.

🧹 **2026-10-08 21:50 AEDT — three frozen scripts left the size baseline (15 → 12): [chore-three-scripts-leave-the-size-baseline](sprints/chore-three-scripts-leave-the-size-baseline.md), merged with no bump, fast-forwarded to `7bbf8737`.** INTENT: `check_worktrees.py`, `retrain_return_model_helpers.py` and `remediation_gate.py` each fit the 200-line block with no behaviour change, and their entries leave the frozen list. Built by a Claude cloud session on 2026-10-03 and left unmerged until now. PROVEN: the planner's own re-measure (46 of 47 definitions identical as syntax trees and none missing, the 47th gained one import line; both runnable scripts print the same bytes before and after; a deleted entry put back, and a split module grown to 209 lines, each fail the size step); Windows `make ci` exit 0 (**4,392 passed, 8 skipped, 100.00 %**); **`GATE PROVEN` for `7bbf8737`**; open CodeQL alerts 127, the same as `main`'s. No deploy: the scripts ship in no image.

🗄️ **Older shipped results are in [state-archive/](state-archive/INDEX.md); the newest file is [STATE-18.md](state-archive/STATE-18.md).**

## Next

**Ranked queue of record: [work-queue.md](work-queue.md).** This section is the narrative around it, not a
second ranking.

1. **Today:** S252's F2 on `sched-2026-10-08` (the four apps' received bytes) and how the master's container ended at
   the scale-down (work-queue 116); both are readable once the run's window has closed at 00:30 UTC.
2. **F2 of three debates at once** (work-queue 113, [DL-277](design-log.md) amendment 2), on the first
   scheduled night with more than one debated buy; then the pack edit, once the fidelity count allows it.
3. **S262's F2** on tonight's run (*Now*), and **the chat adapter's fix** (work-queue 121), a small
   sprint for Codex once its choices are measured against the vendor.
   **The tracker trim's two remaining files** (*Now*), then the size limits as a step of `make ci`
   (sprint 261, reserved). Also Codex-sized and off the fidelity decision paths: work-queue 115.
   **Then the shutdown path and the container sensor** (work-queue 116, then 119;
   [DL-283](design-log.md); operator, 2026-10-09): no container in the fleet shuts down on the stop
   signal, and nothing tells the operator when one fails to start or is killed. Until the sensor
   exists the fleet check reads the platform's event log by hand.
4. **The fidelity count:** four clean sessions and ten judged PM recommendations from
   `sched-2026-10-08`, read from a worktree pinned at `v0.123.04` (`v0.125.00` holds the same
   decision code); on PASS,
   [EXP-014](research/experiments/EXP-014-does-the-price-only-pipeline-beat-spy-held-at-the-same-exposure.md),
   which is also S250's F2.
5. **After 2026-10-11:** EXP-019's remainder on Opus, then the debate workflow in the order of
   [DL-264](design-log.md) amendment 5: the other two pieces of step 2 (work-queue 98, and the risk
   figures), the debaters' typed turn, the judge's typed ruling, the loop in shadow.
   [DL-280](design-log.md) proposes the judge's contract before the typed turn: every ruling since
   2026-09-17 is `revise`, and `revise` changes no order (work-queue 118).
6. **From about 2026-10-12:** S241's F4, the first barrier claims settling
   ([S241](sprints/sprint-241-each-barrier-claim-is-settled-and-scored.md)).
7. **Not while the fidelity count runs** (each touches a decision path): work-queue 103 part two, 105
   and 108.

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
