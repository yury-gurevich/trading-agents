# Project State

**Last updated:** 2026-11-18 14:30 AEDT · **Version:** **0.131.07 on `main`** (`f1665f6e`, tag `v0.131.07`, GATE PROVEN) · **[S290](sprints/sprint-290-a-full-up-keeps-three-debates-at-once.md) is merged and deployed by a full `up` as `s290` (rollback `s289a`): every app reads back as it was, the three debate settings included; work-queue 113 is closed. First run on `s290`: `sched-2026-11-18`. The edge search's next test is the operator's call.**

**How to read.** *Now* = active · *Next* = queued · *Recent* = last few shipped (older detail lives in
each `docs/sprints/sprint-NN-*.md` + [`state-archive/`](state-archive/INDEX.md) `STATE-01…24.md` + git). **LAW-02:** an item is "shipped" only when
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

- **The fleet is on `s290`** = `0.131.07` (`f1665f6e`), a full `up` 2026-11-18 02:55 to 03:19 UTC
  (`DeployRecord` 03:20:30 UTC). Rollback: `s289a`. Every app's env values, scale rules, resources,
  ingress and secret names read back equal to the snapshot taken before it. A rollback below `s262` must also put the hand-made eight-probe pack back on the master in the
  same step (an older image ignores the declared provider and would run Anthropic's probes).
- **The debate runs on OpenAI (`gpt-5.5`)**, declared in `orchestration/packs/trading_llm.json` and
  kept by a full `up` since `s262` ([DL-282](design-log.md)); the master runs and counts OpenAI's
  probes alone. The Anthropic account is out of credit until 2026-10-11. **The operator's dashboard
  chat is on OpenAI since 2026-10-09 22:57 AEDT** (the operator: *"yes, you can switch my .env"*): the main checkout's `.env` holds
  `OPERATOR_LLM_PROVIDER=openai` and no model or effort, so the chat asks `gpt-5.5` at `xhigh`
  ([S263](sprints/sprint-263-the-operators-chat-makes-its-tool-call-on-openai.md)). To go back, set the value to `anthropic`. It is a local setting: the
  fleet's operator container binds the fake client.
- **The manager's wait is 240 seconds and debates run three at once**, live since October and in the
  pack since `0.131.07` ([S290](sprints/sprint-290-a-full-up-keeps-three-debates-at-once.md)), so a
  full `up` keeps both (F1 2026-11-18, and the full `up` to `s290` the same day read back 20 of 20);
  a rollback to `s255` or older must set the wait to 120 first. **F2's last limb is owed:** the first
  night on `s290` with more than one debated buy shows no order failed open and no orphaned reply.
- **The five-minute message lock is live only** on the two debater subscriptions; a re-created
  subscription reverts to one minute.
- **The fidelity count restarts at `sched-2026-10-20` on `s284`**; read 2026-10-26 through `sched-2026-10-23`: INSUFFICIENT, PM 8 of 10 judged recommendations, all else met; **read 2026-10-27 through `sched-2026-10-26`: PASS** (5 of 5 clean, scanner 125 / 125, analyst 193 / 193, PM 16 / 16 against 10, 0 unexplained); no session was missed (every trading day from 10-01 has its `sched-` run), and re-firing a past day cannot add to the count, ruled out 2026-10-26: the export takes `sched-YYYY-MM-DD` runs only (`scripts/fidelity_exporter.py`), and a re-run would decide on today's book and place paper orders (replay from a worktree pinned at
  `v0.128.06`; S284 changed the analyst; before it `sched-2026-10-16` on `s280`, pinned `v0.128.03`). Four clean sessions and ten judged PM recommendations are needed before EXP-014 or the
  exit experiment may start ([DL-237](design-log.md)); a deploy that changes a decision path restarts
  it. The 10-08 to 10-15 window read **INSUFFICIENT on 9 of 10** PM recommendations, 100 % agreement,
  0 unexplained ([DL-304](design-log.md)); `s279` had changed `contracts/`.
- **[EXP-019](research/experiments/EXP-019-do-the-debaters-know-what-an-order-hinges-on.md) is
  interrupted** at 31 of 52 calls; $2.80 is approved for the rest, on Opus, after 2026-10-11.

## Now

⬜ **2026-11-18 — nothing in flight.** Coding candidates, none specced (each needs a prototype and a line here first): 136, 120, 118, 110 and 98, 105, 142, and 109's pack edit. Owed on `sched-2026-11-18` (fires 09:30 AEDT 11-19), the first run on `s290`: 8 / 8 and the fleet check; S290's last F2 limb waits for a night with more than one debated buy. The fidelity count restarts at `s290` (the pack is a decision path), though no live value changed. The edge search continues beside the paper test bed ([ADR-0033](decisions/0033-the-fleet-is-a-paper-test-bed.md)); the open lead is EXP-036's confirmation, the operator's call.

## Recent (most recent first — detail in each sprint doc)

🟩 **2026-11-18 — [S290](sprints/sprint-290-a-full-up-keeps-three-debates-at-once.md) (work-queue 113, [DL-325](design-log.md)) merged as `0.131.07` (`f1665f6e`, tag `v0.131.07`); work-queue 113 closed.** INTENT: the tunables pack declares three debates at once and the manager's wait of 240 seconds, the values the fleet has run live since October; success = the pack's blob equals the prototype's, six tests under the spec's names pass with four seen red first, fifteen planted breaks red against the builder's tests, GATE PROVEN for the merged SHA, and F1: the deploy script's own `Up` prints what the live apps hold. PROVEN RESULT: built by Codex; the three production blobs equal the prototype's; the builder's red run 4 failed / 2 passed, then 6 passed; the planner's tests pass in place of the builder's (96 with the two existing files); 15 of 15 breaks red against the builder's tests alone; the builder's `make ci` exit 0 (5,333 passed, 100.00 %); **GATE PROVEN `f1665f6e`** (CI, CodeQL, Security Findings, attempt 1); CodeQL 137 = 137 against `main`; **F1 passed**: 20 of 20 lines equal, both read 2026-11-18 02:38 UTC. **Deployed** on the operator's *"go for it"*: images `s290` built from `v0.131.07` (15 / 15), a stand-in `Up` over all 16 apps differed from live only in its stand-ins, then the full `up` (every step `[OK]`); read back, all 16 apps and the job on `s290`, `Succeeded`, `Running`, and equal to the snapshot before it in env values, scale, resources, ingress and secret names; the three deliberator apps equal F1 on 20 of 20 lines (F2's first limb); `DeployRecord` written. Owed: F2's last limb on a night with more than one debated buy ([functionality-checks](laws/functionality-checks.md)).

🟥 **2026-11-16 — [EXP-041](research/experiments/EXP-041-do-mid-and-small-companies-rise-after-a-sharp-fall-or-a-strong-results-reaction.md) ([DL-324](design-log.md)): no short-horizon buy signal in mid and small companies.** INTENT: on the operator's yes to a buy-side test at one to two weeks, measure at $0 whether a company ranked 501–2000 by dollar volume beats its peers over the ten sessions after a 10 % five-session fall (all, without and with a results release) or a strong results reaction; success = a universe that keeps delisted companies, pre-registration before any return is read, one scored run, verdict by R012's funnel. PROVEN RESULT: 7,092 companies built from SEC insider filings and Alpaca's free bars (four build defects found and fixed before any return was read: Appendix R); pre-registered `ff107361`; self-test finds a planted effect and none where none is planted; one `score` run read **NONE**: no cell of eight passes discovery (smallest p 0.51), every mean excess within ±0.7 %, all below zero net of 50 bps; about half the trades end up. One vendor bad print (AQB) found after the run, in no barred cell. No code change. Not done: companies listed after 2021 (the SEC's file host needs a contact address).

🟥 **2026-11-16 — [EXP-040](research/experiments/EXP-040-does-selling-what-the-analyst-would-not-buy-today-beat-the-stop-alone.md) ([DL-323](design-log.md)): selling what the analyst would not buy today earns less than the stop alone.** INTENT: on the operator's *"would i buy it today? … If not then we have to sell to minimise loss"*, run the rule at $0 as a replay arm (the thesis exit's floor raised from 0.50 to the buy floor 0.60) against EXP-022's sealed stops arm; success = pre-registration committed before the arms ran, the control reproduces the sealed arm, one scored run, verdict by the frozen rule. PROVEN RESULT: pre-registered `e33e5108`; four ten-year arms ran clean in 4 h 26 min and were sealed (`878d1b0f…`); the control's `equity.csv` equals the sealed one byte for byte; one `score` run, no defect, read **BEHIND**: +1.17 % a year against +10.64 %, dR −9.47 pts [−17.31, −2.14], halves −7.28 / −11.69 (floor 0.55: −6.17; 10 bps: −8.43). The rule sold winners, not losers: 71 % of its 2,781 sales were at a gain (+4.18 % after 5 sessions), while stops tripled (1,802 against 604) at the same −5.85 % and the same worst trip. The floor stays 0.50; no code change. Also found: DL-240 had the floor as 0, it is 0.50 (corrected there).

🟥 **2026-11-16 — [EXP-039](research/experiments/EXP-039-does-a-trend-regime-make-the-barrier-forecast-more-accurate.md) ([DL-322](design-log.md)): a trend regime does not make the barrier forecast more accurate.** INTENT: on the operator's *"how about introduction of a regime"*, test at $0 whether a sticky SPY bull / sideways / bear label, as a per-regime correction of GARCH-756's probabilities, beats the same correction pooled; success = pre-registration committed before the scored run, one run, verdict by the frozen rule. PROVEN RESULT: pre-registered `48344da7`; one formatting defect crashed the first `score` before any output and was fixed by one line (Appendix R); the run read **H0**, R1 over R0 −0.20 % [−0.97, +0.48], halves −0.90 % / +0.37 %; raw GARCH over climatology +2.64 % [+1.81, +3.53], and a pooled shift alone costs −0.26 %. Also read from the live ledger (work-queue 92): held claims' return bias +0.08 % [−0.27, +0.46] meets step 5's gate, buy claims' skill −7.1 % [−15.1, −1.1] and bias +3.26 % do not.

🟩 **2026-11-13 — `sched-2026-11-12`, the first run on `s289a`: 8 / 8, and the forecaster image chore's F2 passed; S283's last limb passed on `sched-2026-11-10`; work-queue 134 closed** ([functionality-checks](laws/functionality-checks.md)). INTENT: (a) on the slim image the forecaster writes its barrier claims and settlements as before, with no `error` fault; (b) the first old stop the broker ends is settled and its position carries a stop again by the next run. PROVEN RESULT: (a) `ACCEPTANCE PASS`, brief PASS 22:50 UTC, no order (LLY below the minimum quantity, 42 holds); 41 barrier claims at 22:40:51 UTC and 39 settlements; the forecaster's only faults are two designed refusals at `warning` (CL, UNH); equity $102,605.24 (−$243.37 on the day). (b) Alpaca ended the four stops of 2026-08-12 (AAPL, KO, MDT, DIS) at 2026-11-10 21:05:30 UTC; the run that night settled each `Fill` `rejected` and placed each again as `<stop key>#1` at the same quantity and price; 42 positions, 42 open stops. Measured against the spec: the broker reports the 90-day end as `canceled`, not `expired`, and four stops ended, not five ([DL-306](design-log.md) amendment 1). Also read: one `error` fault, the dispatcher's container sensor (`ContainerLogReadError`, transport, 23:10 UTC), which read again at 23:20; its one alarm is Azure's `FailedKillPod` on the supervisor at scale-down, after the window. Main's CI, CodeQL and Security Findings green on `7f2f1ed9`. DRIFT-117 is work-queue 142. Weekly trim done: STATE to [STATE-24](state-archive/STATE-24.md), nine closed queue rows and the design log's unlinked older entries to their archives.

🟥 **2026-11-09 — [EXP-038](research/experiments/EXP-038-do-published-stock-predictors-still-earn-after-publication-outside-micro-caps.md) ([DL-321](design-log.md)): the 212 published stock predictors after publication, outside micro caps; none confirms, nothing is built.** INTENT: answer the operator's QuantConnect question for the whole academic set at once, through R012's funnel; success = the pre-registration committed before the run (`451280f8`), the frozen script run once, a verdict by code. PROVEN RESULT: OSAP 2026.10, ex-micro long-shorts: 25 of 194 pass Benjamini–Hochberg on post-publication months through 2015, 0 confirm under Holm on 2016–2025 (smallest p `Mom6m` 0.014 against 0.002); the median falls +0.40 → +0.17 → +0.14 % a month (papers' samples → after publication → 2016–2025); `ShareVol` −0.05 % a month since 1998; the original methods with micro caps confirm none either. Secondary lead only: `AnnouncementReturn` in value-weighted deciles (+0.75 % a month, t 2.49). Kit OneDrive `exp038-2026-11-09/`, `exp038.json` `42321087`.

🟩 **2026-11-09 — chore `0.131.05`: litellm 1.103.9 and msgpack 1.2.4 for two advisories.** INTENT: clear GHSA-g5ff-637f-6q2m (litellm 1.90.7, fixed in 1.95.0) and CVE-2026-114613 (msgpack 1.2.2, fixed in 1.2.3), which failed the dependency audit on all four Dependabot branches since 2026-10-30 and would have failed `main`'s next push; success = audit clean, `make ci` exit 0, GATE PROVEN, nothing new in CodeQL. litellm stays on its 1.103 line: 1.104.0 to 1.108.2 cap filelock below 4 (back to 3.32.7, 13 OSV advisories, undoing `0.131.03`) and 1.108.3 was two days old. PROVEN RESULT: Windows `make ci` exit 0 (5,323 passed, 8 skipped, 100.00 %, audit clean but the accepted diskcache row); GATE PROVEN `b7b4a75e` (CI, CodeQL, Security Findings, attempt 1); CodeQL open alerts by rule and path equal the baseline branch's (137, 0 errors); `main` fast-forwarded, tag `v0.131.05`. Not deployed: msgpack reaches the fleet with the next image build, and the deliberator image will then also carry litellm's new dependencies (boto3, botocore, s3transfer, jmespath, h2, hpack, hyperframe), unimported, since only litellm itself is left out by name.

🟩 **2026-10-23 — [EXP-024](research/experiments/EXP-024-does-news-sentiment-rank-the-scanners-survivors.md) (work-queue 138, [DL-316](design-log.md)): news sentiment on Alpaca's historical news, 2017–2026; nothing carries, nothing changes.** INTENT: test the lexicon champion and the FinBERT challenger, each read as the fleet reads it, on EXP-015's survivors and 10-session target, with Holm across three; pre-registered in `410a79c1` before any news was fetched, Amendment 1 (`095cf8e7`) before the pilot: the symbol each line's news carried that day (renames), FinBERT's check at 1e-5. PROVEN RESULT: the fetch (1,998,632 items, 2016-10 → 2026-10-23, 40,037 calls); the pilot passed every stop; scripts frozen with their SHA-256 in `5424467d` before the scored run; one scored run from `095cf8e7`, 696,537 rows, 327,012 headlines scored, check 8.9e-8. **Lexicon IC +0.0022 [−0.0101, +0.0206], FinBERT −0.0050 [−0.0168, +0.0108], FinBERT minus lexicon −0.0091 [−0.0289, +0.0030]; none carries.** Reported: Alpaca carries 13.7 % of Finnhub's headlines for the fleet's names, so the live feed is not certified empty. $0. **The operator, 2026-10-24: no change** (the pillar keeps 0.20, FinBERT stays challenger, sentiment no longer an edge line); FinBERT's revision pin is work-queue 139, after GitHub unlocks.

🟩 **2026-10-23 — [EXP-023](research/experiments/EXP-023-which-of-the-technical-scores-rules-carry-its-rank-ic.md) (work-queue 137, [DL-314](design-log.md)): the technical score taken apart; nothing carries, nothing changes.** INTENT: test each of the score's 16 components (15 banded rules and relative strength) on EXP-015's survivors and window, with Holm across the 16, and whether the scanner's filter picks names that beat the ones it turns away; pre-registered in `8afc707c` before any component was scored. PROVEN RESULT: one scored run from `8afc707c`, 715,852 rows, 0 mismatches against EXP-015's panel, the score's own IC reproduced (−0.0099); **no component carries** (smallest p 0.017 against Holm's 0.003); the selection +0.06 % over 10 sessions, CI [−0.13 %, +0.31 %], does not carry. Below the bar the weakness rules lean positive and the trend rules negative. Whether the price-only score keeps ranking is the operator's call after EXP-014 scores.

🟩 **2026-10-23 — [S289](sprints/sprint-289-exp-015-has-the-tooling-its-pre-registration-fixes.md) (work-queue 90, [DL-313](design-log.md)) merged at `1c91c21e` (no bump, GATE PROVEN, no deploy), and [EXP-015](research/experiments/EXP-015-price-only-ensemble-vs-technical-score.md) run to its verdict: FAIL, nothing built.** INTENT: the three stages EXP-015's pre-registration fixes exist as tested scripts, then run from a clean tree, the walk-forward recorded before the holdout is touched once. PROVEN RESULT: the review (kit OneDrive `wq90-2026-10-22/`): 13 of 13 blobs, the planner's 24 tests pass on the built tree, 36 of 36 breaks red against the builder's tests alone, F1 byte for byte, CodeQL 0 errors (its one new warning fixed in `1c91c21e`), `make ci` exit 0 (5,321 passed, 100.00 %). The run from `1c91c21e`: `panel` 1,209,946 rows; the walk-forward recorded in EXP-015 (`3eac394d`) before the holdout: IC difference +0.0123, CI [−0.0219, +0.0313], 3 of 7 folds, control passed, so bars 1 and 2 fail; the holdout, once: bar 3 holds (+0.0345; net top decile +28.6 % against −3.1 %); verdict **FAIL**. Reported, not barred: the technical score's own rank IC is −0.0099 over 2018–2024 and −0.0070 on the holdout.

🗄️ **Older shipped results are in [state-archive/](state-archive/INDEX.md); the newest file is [STATE-24.md](state-archive/STATE-24.md).**

## Next

**Ranked queue of record: [work-queue.md](work-queue.md).** This section is the narrative around it, not a
second ranking.

1. **F2 of three debates at once** (work-queue 113, [DL-277](design-log.md) amendment 2): **PASSED 2026-10-21** on
   `sched-2026-10-20`: CL and SBUX debated at once on three replicas of each debater, 0 failed open, 0 orphaned.
   The pack edit is merged as `0.131.07` (S290, 2026-11-18); left: its F2 at the next full `up`.
2. **Anthropic's account accepts paid calls again** (measured 2026-10-11: one call of one output
   token answered HTTP 200; S264's F1b on Anthropic passed the same day, *Now*): EXP-019's
   remainder on Opus, then the debate workflow in the order of
   [DL-264](design-log.md) amendment 5: the other two pieces of step 2 (work-queue 98, and the risk
   figures), the debaters' typed turn, the judge's typed ruling, the loop in shadow.
   [DL-280](design-log.md) proposes the judge's contract before the typed turn: every ruling since
   2026-09-17 is `revise`, and `revise` changes no order (work-queue 118).

## Pointers

Product `docs/PRD.md` · architecture `docs/architecture.md` · phases `docs/build-plan.md` · closed
decisions `docs/decisions/INDEX.md` · open threads `docs/design-log.md` · "does it work"
`docs/laws/{ledger,drift-register,functionality-checks}.md` · per-agent `agents/<name>/mission.md`.
