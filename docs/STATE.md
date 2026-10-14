# Project State

**Last updated:** 2026-10-14 11:40 AEDT · **Version:** **0.125.09 on `main` and on the fleet: `s272`, deployed 2026-10-14** (image-only retag from `497293b8`, 17 of 17 targets, rollback `s270`; `main` is `ccc2bf94` plus docs, nothing since `497293b8` ships in an image) · **[S273](sprints/sprint-273-the-secrets-scan-reads-every-file-as-utf-8.md) is merged with no version bump: the commit hook's secrets scan reads every text file, and a self-test run that leaves a probe path now fails (work-queue 132 and 130 closed). [S272](sprints/sprint-272-a-container-ends-cleanly-on-the-stop-signal.md)'s read after the first nightly window's end passed: all 16 containers ended by themselves, exit 0 (work-queue 116 closed). [S274](sprints/sprint-274-a-full-up-keeps-the-masters-live-start.md) is specced for Codex (work-queue 131 part f, [DL-300](design-log.md)); until it is merged a full `up` must still pass `-MasterScaleStart '0 22 * * 1-5'`. Debates run three at once, as a live setting.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + [`state-archive/`](state-archive/INDEX.md) `STATE-01…20.md` + git). **LAW-02:** an item is "shipped" only when
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

- **The fleet is on `s272`** = `0.125.09` (`497293b8`), since 2026-10-14. Rollback: `s270`. A
  rollback below `s262` must also put the hand-made eight-probe pack back on the master in the
  same step (an older image ignores the declared provider and would run Anthropic's probes).
- **The debate runs on OpenAI (`gpt-5.5`)**, declared in `orchestration/packs/trading_llm.json` and
  kept by a full `up` since `s262` ([DL-282](design-log.md)); the master runs and counts OpenAI's
  probes alone. The Anthropic account is out of credit until 2026-10-11. **The operator's dashboard
  chat is on OpenAI since 2026-10-09 22:57 AEDT** (the operator: *"yes, you can switch my .env"*): the main checkout's `.env` holds
  `OPERATOR_LLM_PROVIDER=openai` and no model or effort, so the chat asks `gpt-5.5` at `xhigh`
  ([S263](sprints/sprint-263-the-operators-chat-makes-its-tool-call-on-openai.md)). To go back, set the value to `anthropic`. It is a local setting: the
  fleet's operator container binds the fake client.
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

📦 **SPECCED 2026-10-14 — [S274](sprints/sprint-274-a-full-up-keeps-the-masters-live-start.md) (work-queue 131 part f, [DL-300](design-log.md)), for Codex, PATCH; worktree `../ta-s274`; not yet handed over.** INTENT: a full `up` with no window parameter gives the master the wake it has on the live fleet, weekdays at 22:00 UTC; the dashboard reads the master as awake only from that hour; a test fails when the wake no longer leaves one fresh fleet check for the 22:30 run. SUCCESS FACTORS: the two production files are the prototype's blobs; the three new tests pass under their given names and the two existing tests change as named; the planner's 17 breaks go red on the built tree; surfaces law v1.8, `PARAM` only; `make ci`, 16 steps; GATE PROVEN for the merged SHA; then F1 at no cost: the script's own `Up`, every call a stand-in, gives 16 rules equal to the 16 live ones, and the dashboard names 22:00 UTC as the master's next wake. MEASURED BEFORE THE BUILD: on `main` 15 of the 16 rules equal the live ones and the master's is `25 20 * * 1-5`; on the prototype `make ci` exit 0 in one run, 16 steps, 4,824 passed, 8 skipped, 100.00 %.

🟩 **MERGED 2026-10-14 — [S273](sprints/sprint-273-the-secrets-scan-reads-every-file-as-utf-8.md) (work-queue 132 and 130, [DL-299](design-log.md)), no version bump, fast-forwarded to `25a0129d`, GATE PROVEN; then the planner's follow-up, `ccc2bf94`, GATE PROVEN; no deploy (nothing here ships in an image).** INTENT: the secrets scan reads every text file in UTF-8 on any machine, at a commit as in `make ci`; the gate's self-test plants a credential in a file cp1252 and ASCII cannot decode and fails unless the scan reports it; a self-test run leaves no probe folder. PROVEN: built by Codex, the four files the planner's prototype byte for byte and its ten test cases its own; the planner's ten cases pass beside them; the planner broke it 19 ways against the builder's tests alone and 19 went red, each on the test meant for it; remote CI, CodeQL and Security Findings green for the merged commit, and the new case's first Linux run reads `PASS` in the remote job's log; one new CodeQL alert, a note. F1 ([functionality checks](laws/functionality-checks.md)), at no cost: with no variable set a real `git commit` of a page holding the plant is refused by the hook, naming the credential, where the commit before the merge passes the same page; the page was never committed. 🔴 NOT met on the merged commit, verified failing: in the main checkout the self-test read 40 of 40 and left the probe folder dated 2026-08-30, because 437 of that checkout's 444 folders carry Windows' read-only attribute and the removal cannot take such a folder and says nothing; the prototype was never run there. PUT RIGHT the same day by the planner (`ccc2bf94`): the owner's rights are given back before a probe folder is removed, and every run ends on one more check that fails it when a probe path is left; five tests, four red on the unchanged code; nine breaks, nine red; Windows `make ci` exit 0, sixteen steps (4,836 passed, 9 skipped, 100.00 %); in the main checkout the self-test then read 41 of 41 and the folder was gone. 🔴 The planner's break script first read 8 of 19: it judged by the prototype's test names, which the spec had left to the builder; re-run in the builder's names, 19 of 19. NOT RE-RUN by the planner: the local `make ci` on the builder's commit (its pass reads 4,832 passed, 8 skipped, 100.00 %; the remote gate is the proof). Nothing is owed.

🟩 **MERGED 2026-10-14 — [S272](sprints/sprint-272-a-container-ends-cleanly-on-the-stop-signal.md) (work-queue 116, [DL-297](design-log.md)), `0.125.09`, fast-forwarded to `497293b8`, tag `v0.125.09`, GATE PROVEN; deployed as `s272` 2026-10-14 on the operator's word (*"go for it"*); F2 passed at the retag and again after the first nightly window's end.** INTENT: a container told to stop ends by itself inside the grace: it takes no new work, finishes the item or request in hand, closes what it holds, writes one line and exits 0; the master also lets the activations in hand finish and writes `ended_at` on its `Session`. PROVEN: built by Codex, the 17 production files the planner's prototype byte for byte and its 38 tests its own; no decision path changes (the scope command prints nothing), so the fidelity count stands; the planner broke it 51 ways against the builder's tests alone and 51 went red; each of the 38 tests the four clauses' rows cite resolved by hand; master law v1.10, 30 / 55, DRIFT-113 corrected; Windows `make ci` exit 0, sixteen steps (4,822 passed, 8 skipped, 100.00 %); 129 open CodeQL alerts, one new, a note. Three lines changed by the planner in two commits, a fault in the planner's own prototype: an error-level CodeQL alert on the closing line, raised on the branch while all three remote workflows were green, found by the comparison with the last merged branch; the first rewrite did not clear it, the second did, and the same line is written. F1 ([functionality checks](laws/functionality-checks.md)), at no cost, on the merged commit: five process shapes print what the prototype printed (exit 0 after flushing and closing; the item in hand finished; exit 1 where the graph refused to close; the master's `Session` ended), and on Linux a Python that is process 1 ignored the signal for the 6.0 seconds watched with no handler and exited 0 in 0.2 seconds on the merged code. NAMED, NOT BUILT: a stop that arrives while a container is still starting or activating; work in hand longer than the 30-second grace. DEPLOYED 2026-10-14 03:15 to 03:22 AEDT: image-only, 15 images built from `v0.125.09`, 17 of 17 targets, nothing but the image differing from the snapshot before, `DeployRecord` written, rollback `s270`. F2 AT THE RETAG, PASSED: 16 of 16 apps were stopped by the scaler within eleven minutes of the retag (the master twice), each left its signal line and a closing line ending `exit 0` in its console log, and the platform's event log holds no exit code 137 and no exit line at all for them; the master's two sessions on the new image hold `ended_at` and `shutdown_reason` `SIGTERM`; 15 of 15 agent types activated; 0 escalations, faults or flags. MEASURED there for the first time: the platform logs nothing for a clean exit. READ AFTER THE FIRST NIGHTLY WINDOW'S END, 2026-10-14 11:00 AEDT, PASSED: the scaler stopped all 16 apps between 23:34:31 and 23:35:00 UTC, each left a closing line ending `exit 0`, the event log holds no exit code 137, and the master's session of the night holds `ended_at` and `shutdown_reason` `SIGTERM`. NOT exercised: a stop with a debate in hand. Nothing is owed; work-queue 116 closed.

🟩 **MERGED 2026-10-13 — [S271](sprints/sprint-271-a-full-up-creates-the-master-with-its-probes.md) (work-queue 122, [DL-296](design-log.md)), no version bump, fast-forwarded to `9eb1325f`, GATE PROVEN; no deploy; F2 owed at the next full `up`.** INTENT: a full `up` makes two calls for the master, the create carrying the probe pack with the secret map and the provider, so no revision of the master refuses to start. PROVEN: built by Codex, the script the prototype's blob (`d9447b63`); the planner's eight cases pass beside the builder's and the planner's 14 breaks went red on the built tree, 14 of 14; remote CI, CodeQL and Security Findings green for the merged commit; 128 open CodeQL alerts, none new; F1 at no cost on merged `main`: the script's own `Up`, every call a stand-in, makes two master calls where it made three, the create at most 17,279 characters of the 32,767 allowed. NOT RE-RUN by the planner: the local `make ci` (the builder's pass reads 4,784 passed, 8 skipped, 100.00 %; the remote gate is the proof). NOT PROVEN, owed at the next full `up` (F2): that Azure accepts the longer create call and that neither new revision of the master logs a refusal.

## Recent (most recent first — detail in each sprint doc)

🟩 **2026-10-14 — `sched-2026-10-13`, the first scheduled run on `s272`: 8 / 8, and [S272](sprints/sprint-272-a-container-ends-cleanly-on-the-stop-signal.md)'s read after the window's end passed** ([functionality-checks](laws/functionality-checks.md)). The analyst scored 33 names and the portfolio manager approved one buy (CAT, 1 share; GOOGL skipped on sizing); it was debated, ruled `revise` and submitted for the open, so acceptance reads `UNPROVEN` until the broker fills it. No `Fault`, no `Escalation`; one name's fundamentals timed out (LRCX); two warn-level divergence flags at the run's start (CAT and JNJ held on the graph and not at the broker), and the reporter counts two positions closed. After the window's end all 16 containers ended by themselves, exit 0. Not read: the fill at the open.

🟩 **2026-10-10 — `sched-2026-10-09`, the first scheduled run on `s262`: 8 / 8, `ACCEPTANCE PASS`, and [S262](sprints/sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it.md)'s F2 passed** ([functionality-checks](laws/functionality-checks.md)). The fleet check passed over 15 agent types; the operator, the manager and three replicas of each debater activated with OpenAI's probe passed and Anthropic's not declared; 0 Escalations, 0 Faults. No buy was approved (GOOGL skipped on sizing, 33 holds), so nothing was debated and no order was placed. In the session TMO's re-buy filled at $657.50 and T and VZ were stopped out; the broker and the graph agree on 33 names, each with its stop; equity $101,703.15. Read 25 minutes into the window; its end is not read. 🔴 **[S252](sprints/sprint-252-every-finder-fetches-only-its-pending-work.md)'s F2, read the same morning on `sched-2026-10-08`, is NOT fully met:** the forecaster and the deliberator-manager read 7.7 and 7.6 MB where they read 2,295 and 1,021, and execution and the monitor read 154.0 and 20.6 MB where they read 403 and 143, short of tenfold. Execution's idle polls fell to 0.18 MB in five minutes; 135 MB arrives in its first five minutes, not diagnosed (work-queue 101, about half a cent a night). Work-queue 106 closed.

🟩 **2026-10-09 15:54–16:01 AEDT — debates side by side proven once on the fleet at three at once (work-queue 113, [DL-277](design-log.md) amendment 1; operator: *"yes, it can. go ahead"*).** INTENT: six synthetic buys are debated by the deployed manager and debaters at three at once with no reply lost, no order can reach the broker, and everything changed is put back. PROVEN: 6 of 6 really debated, 0 failed open, 0 orphaned replies, 0 Faults; 30 calls on `gpt-5.5`, all ended on `stop`, $3.72 against a ceiling of $5.50; three replicas of each debater ran and activated; the record landed 6.9 minutes after the seed (2.26 lanes); execution and the portfolio manager at 0 replicas throughout; the synthetic run deleted from the graph and the four apps equal to their snapshot ([functionality-checks](laws/functionality-checks.md)). NOT proven: a night-sized batch, execution reading the record, and absence of an intermittent failure (one run).

🟩 **2026-10-09 — [S260](sprints/sprint-260-debates-at-once-lose-no-reply-and-the-repo-can-show-it.md) merged as `0.124.00` (`19239d25`, tag `v0.124.00`, GATE PROVEN, no deploy), and F1 passed.** INTENT: the repository holds a command that runs the production debate manager and debaters at one to four debates at once with a canned model, and tests that go red if a reply is lost at one request a pass or if the September setting stops failing. PROVEN: built by Codex, complete against its checklist; the planner put the kernel's old default of ten back and the four-at-once test failed; `make ci` exit 0 (4,436 passed, 100.00 %); on disposable topics of the live namespace, on the merged `main`, one to four at once are all clean (8 orders, 32 turns of 20 s: 713, 356, 269 and 181 s) and ten requests a pass fails 2 of 4 orders open; every topic deleted, the fleet's subscriptions unchanged ([functionality-checks](laws/functionality-checks.md)). NOT proven: anything on the fleet (Postgres, replicas scaling out, the vendor's rate limit). The dial stays at 1; the paid proof at three at once is the operator's call (work-queue 113).

🟩 **2026-10-09 — `sched-2026-10-08`, the first scheduled run on `s259a`: 8 / 8, the first buy debated on OpenAI on a scheduled run, and the F2s of [S253](sprints/sprint-253-a-runs-snapshot-counts-what-the-broker-filled.md), [S254](sprints/sprint-254-each-debater-turn-is-run-by-dspy-and-the-prompt-does-not-change.md), [S255](sprints/sprint-255-the-packet-states-the-score-arithmetic.md), [S256](sprints/sprint-256-a-served-request-is-settled-when-it-is-taken.md) and [S257](sprints/sprint-257-a-debaters-turn-may-write-16384-output-tokens.md) passed** ([functionality-checks](laws/functionality-checks.md)). One buy (TMO, 1 share) was debated in 222 seconds on `gpt-5.5`, ruled `revise` and submitted for the open: five calls, none cut, none failed open, $0.76. No `Fault`; the broker and the graph agree on 34 names, each with its stop; equity $101,560.84. Work-queue 111 and 112 closed. TMO and DE were stopped out in the session and the run re-bought TMO ([DL-240](design-log.md) amendment). The five entries are in [STATE-18.md](state-archive/STATE-18.md).

🟩 **2026-10-08 — [S259](sprints/sprint-259-the-eight-excused-law-rows-state-the-codes-bounds.md) merged as `0.123.04` and deployed `s259a` before the fidelity count's first session; work-queue 114 closed.** [S258](sprints/sprint-258-a-law-rows-numbers-are-compared-with-the-code.md) merged the same day as `0.123.03`, no deploy: the parameter step of `make ci` compares every law row's default and bounds with the code, and no row is excused.

🧹 **2026-10-08 21:50 AEDT — three frozen scripts left the size baseline (15 → 12): [chore-three-scripts-leave-the-size-baseline](sprints/chore-three-scripts-leave-the-size-baseline.md), merged with no bump, fast-forwarded to `7bbf8737`.** INTENT: `check_worktrees.py`, `retrain_return_model_helpers.py` and `remediation_gate.py` each fit the 200-line block with no behaviour change, and their entries leave the frozen list. Built by a Claude cloud session on 2026-10-03 and left unmerged until now. PROVEN: the planner's own re-measure (46 of 47 definitions identical as syntax trees and none missing, the 47th gained one import line; both runnable scripts print the same bytes before and after; a deleted entry put back, and a split module grown to 209 lines, each fail the size step); Windows `make ci` exit 0 (**4,392 passed, 8 skipped, 100.00 %**); **`GATE PROVEN` for `7bbf8737`**; open CodeQL alerts 127, the same as `main`'s. No deploy: the scripts ship in no image.

🗄️ **Older shipped results are in [state-archive/](state-archive/INDEX.md); the newest file is [STATE-20.md](state-archive/STATE-20.md).**

## Next

**Ranked queue of record: [work-queue.md](work-queue.md).** This section is the narrative around it, not a
second ranking.

1. **Small fixes off the fidelity
   decision paths:** **The debaters' effort and model checks (work-queue 123) are widened
   by the operator, 2026-10-11, to a declared list of fallback models** ([DL-289](design-log.md)):
   proposed, not specced, a feature in two sprints.
2. **F2 of three debates at once** (work-queue 113, [DL-277](design-log.md) amendment 2), on the first
   scheduled night with more than one debated buy; then the pack edit, once the fidelity count allows it.
3. Codex-sized and off the fidelity decision paths: what execution still downloads in its first five minutes
   (work-queue 101).
   **The container sensor** (work-queue 119), now that the shutdown path is deployed and proven
   ([S272](sprints/sprint-272-a-container-ends-cleanly-on-the-stop-signal.md), work-queue 116 closed 2026-10-14;
   [DL-283](design-log.md); operator, 2026-10-09): every container ends by itself on the stop
   signal, and nothing yet tells the operator when one fails to start or is killed. Until the
   sensor exists the fleet check reads the platform's event log by hand.
4. **The fidelity count:** four clean sessions and ten judged PM recommendations from
   `sched-2026-10-08`, read from a worktree pinned at `v0.123.04` (`v0.125.00` holds the same
   decision code); on PASS,
   [EXP-014](research/experiments/EXP-014-does-the-price-only-pipeline-beat-spy-held-at-the-same-exposure.md),
   which is also S250's F2.
5. **Anthropic's account accepts paid calls again** (measured 2026-10-11: one call of one output
   token answered HTTP 200; S264's F1b on Anthropic passed the same day, *Now*): EXP-019's
   remainder on Opus, then the debate workflow in the order of
   [DL-264](design-log.md) amendment 5: the other two pieces of step 2 (work-queue 98, and the risk
   figures), the debaters' typed turn, the judge's typed ruling, the loop in shadow.
   [DL-280](design-log.md) proposes the judge's contract before the typed turn: every ruling since
   2026-09-17 is `revise`, and `revise` changes no order (work-queue 118).
6. **From about 2026-10-12:** S241's F4, the first barrier claims settling
   ([S241](sprints/sprint-241-each-barrier-claim-is-settled-and-scored.md)).
7. **Not while the fidelity count runs** (each touches a decision path): work-queue 105 and 108.
   Work-queue 103 part two left this list on 2026-10-11: measured, its one live read is the
   barrier history's, a side branch no decision reads ([DL-287](design-log.md)).

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
