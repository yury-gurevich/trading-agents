# Design log — in-flight discussions, options, and what we ruled out

<!-- markdownlint-configure-file {"MD024":{"siblings_only":true},"MD026":false,"MD029":false,"MD037":false} -->

The home for design reasoning **before** it hardens into an ADR. Captures the question, the
options weighed (including the ones rejected and *why*), and the current status. This is the
LAW-05 ("every choice has a recorded why") and LAW-01 ("everything is a proposal") record for
threads that are discussed but not yet decided. When an entry resolves, it graduates to an ADR
and is marked CLOSED here.

---

**Older entries are in [design-log-archive/](design-log-archive/INDEX.md)** (tracker trim, [housekeeping charter](../ops/departments/housekeeping/charter.md), OPS-TRIM): this file keeps the newest forty entries and every older entry that the work queue or STATE links.

## DL-290 - an intent is passed on only when its family is known and every parameter that family cannot do without is given under a name its readers take; the model is told the names - status: MEASURED and DECIDED (planner, 2026-10-11 14:15 AEDT); specced as [S268](sprints/sprint-268-an-intent-that-lacks-what-its-family-needs-is-refused.md); work-queue 126

**Why.** DRIFT-109 (DL-286): `OPR-FAIL-02` says an intent with missing required fields is refused, and an `approve` with no target, a `modify` with no name or value and a reply with no family at all are passed on. Work-queue 126 left open whether to refuse or to reword the clause.

**Measured (2026-10-11, no vendor call).** Refusing on the grammar as it stands would refuse commands that work. *[measured]* The grammar's `params` are read by no code. *[read]* The system prompt lists each family with its description alone and the tool schema's `parameters` is a bare object, so the model is told no parameter name. *[read]* The readers take other names: the supervisor reads an `approve` as `subject` or `target`, a `stage` as `stage` or `target`, a `resume`'s stage as `from_stage` or `stage`; the chat surface falls back to the typed text for an `explain` with no `subject` and adds the selected run's id to a `resume`; no reader takes a `run`'s `stage` except the hard-NO for `live`. *[read]* An unknown family is refused today with its audit reading `intent`. *[measured, prototype in the sprint worktree]* Three existing tests break and no other of 4,675; with them edited and the new tests added 4,710 pass; 19 planted breaks, 19 red. *[not measured]* Which names each real model returns per family, and what the unattended scorecard counts for such a refusal.

**Decided.**

- **D1 - required:** `approve` and `reject` a `target` (or `subject`); `modify` a `name` and a `value`; `mode` a `mode`; `stage` a `stage` (or `target`); `resume` a `stage` (or `from_stage`). The grammar holds, for each, the names its readers take; the first is the one told to the model and named in a refusal.
- **D2 - not required:** `explain`'s `subject` (the surface has the typed text), `run`'s `stage` (no reader takes it), `resume`'s `run_id` (the surface supplies it).
- **D3 - a blank value is a missing one; a `parameters` that is not an object is no parameters.**
- **D4 - no family, a family that is not a string, or an unknown one is refused with one fixed sentence.** A reply with no family is no longer a `status` intent, and the model's own reason is not shown for it.
- **D5 - the check runs after the explicit command grammar and only on an `intent`.**
- **D6 - the audit of a refused intent reads `refused`.** For an unknown family it read `intent` with no `Intent` written.
- **D7 - the system prompt states each family's parameter names** and tells the model to ask for clarification when the command does not give one the intent cannot do without. The operator's prompt recipe hash changes.

**Ruled out.**

- *Reword the clause to what the code does* - an `approve` that names nothing asks the operator to confirm nothing.
- *Refuse on the grammar's list as it stands* - see Measured.
- *One name per parameter in the supervisor* - a second agent's law cycle for no gain.
- *Per-family parameter properties in the tool schema* - not measured on either vendor.

**Named, not built.** A `run` whose reply carries no `stage` passes the supervisor's hard-NO for `live`, as before. No value is validated by the operator: a `stage` of an unknown name is the supervisor's to refuse. A deployment that sets its own operator system prompt does not get the parameter names.

---

## DL-289 - an LLM role runs on the first working entry of a declared, ordered list of vendor, model and effort; it does not refuse to start, and it does not fail its orders open, while another entry can do the job - status: DIRECTION SET (operator, 2026-10-11 12:41 AEDT), design PROPOSED by the planner, not specced; work-queue 123 widened to it

**Why.** Work-queue 123 asked the operator what a debater does when its vendor refuses its configured effort or model: refuse to start (no debate record, so under the binding posture every buy of the night is dropped) or fail each order open (the buys go undebated). The operator took neither: *"Refuse to start when another LLM can do the job and miss a day's run is not a best Idea. Let's create a list of LLM that can replace currently not working one ... we can switch Andropic with OpenAI or make a list of LLM+Effort combinations."* Before that, the operator asked whether the error can be recognised at run time: *"Does a return code tell you it is a 'effort mismatch'?"*

**Measured (2026-10-11, three requests `gpt-5.5` refused before generation, no cost).** The HTTP status does not name the cause; the error body does.

| Request | HTTP | `code` | `param` |
| --- | --- | --- | --- |
| effort `max`, Chat Completions | 400 | `unsupported_value` | `reasoning_effort` |
| effort `max`, Responses API | 400 | `unsupported_value` | `reasoning.effort` |
| model `claude-opus-5-5` | 404 | `model_not_found` | none |

Each body's `type` is `invalid_request_error`, and the effort message lists the accepted values (`none`, `low`, `medium`, `high`, `xhigh`). *[read]* The master's LLM probes in `trading_credential_tests.json` send a model and no effort, so a refused effort passes activation today and is met on the first debate turn. *[read]* Since S262 the master runs the declared vendor's probes alone and hands over that vendor's key alone (`agents/master/credential_selection.py`); `build_llm`'s docstring says *"never silently switch vendors"*. *[not measured]* What Anthropic answers to an effort or a model it does not take; the Anthropic error bodies already in this log carry a `type` and a message and no `code` or `param`.

**Proposed.**

- **P1 - the declaration is an ordered list.** `orchestration/packs/trading_llm.json` holds candidates, each a vendor, a model and an effort, the preferred one first. The proposed first list: `openai` / `gpt-5.5` / `high`, then `anthropic` / `claude-opus-5` / `max` (the operator keeps the debate on OpenAI while the DSPy work is plumbed: operator, 2026-10-07, work-queue 110). The effort belongs to its entry, so the default mismatch of work-queue 123 cannot be declared by accident.
- **P2 - the choice is made at activation, before the night's work.** The master probes each candidate with its own model and effort, in order, and an agent runs on the first that passes. This covers an empty account, a bad key, a refused effort and a missing model. A candidate that fails is recorded and told to the operator; it does not make the run degraded. An agent is refused only when no candidate passes.
- **P3 - a switch during the night.** A turn whose request the vendor refuses before generation is retried once on the next candidate, and the process stays on that candidate. Each ledger row already names the model that answered; the debate record says which candidate ran and why an earlier one was passed over, and the morning brief says so.

**What it costs, to be stated in the spec.** An LLM agent holds the key of every candidate that passed, which reverses S262's rule that only the selected vendor's key is handed over (DL-282). `build_llm`'s rule becomes: never switch to a vendor that is not declared, and never without a record. A debate may hold turns from two vendors after a switch in the night. A fallback spends the other vendor's account.

**Ruled out.**

- *Refuse to start* - a night's buys are lost while another model could have debated them (operator, 2026-10-11).
- *Fail every order open, as today* - the buys go undebated, with no attempt on the other vendor.
- *A retry inside the same vendor alone* (the planner's proposal earlier the same day: retry once at the vendor's default effort or model) - it mends the effort and the model name and does nothing for an empty account, which is the failure the fleet has met (2026-10-06, DL-265).
- *Every vendor's probe required at activation*, as before S262 - one empty account made the run degraded and held every buy (work-queue 109).

**Open, for the spec.** Whether a time-out moves to the next candidate: the manager waits 240 seconds for a turn and execution 1,800 for the record, so a second attempt costs debate time (work-queue 113). Whether the change restarts the fidelity count (DL-237): the list lives outside the tunables pack, the deliberator's code changes. Whether the operator's chat follows the same list. Anthropic's two refusals, measured the way OpenAI's were.

**Size.** A feature, in two sprints: the list and the choice at activation (P1, P2), then the switch during the night (P3). Work-queue 123's two fixes are inside the first.

---

## DL-288 - a tag is proven from any attempt of its build: the reader reads the latest log archive first and then each earlier attempt's - status: MEASURED and DECIDED (planner, 2026-10-11 10:21 AEDT); specced as [S267](sprints/sprint-267-a-tag-is-proven-from-any-attempt-of-its-build.md); work-queue 115; MERGED as S267 `0.125.05` (`475dba3c`), F1 passed at no cost (amendment 1); work-queue 115 closed

**Why.** DL-278 met the defect on 2026-10-08: a build in which one failed job was re-run read `success`, and `scripts/record_deploy.py` refused to record the deploy made from it. The reader's fix was left as work-queue 115, behind a rule in the deploy skill (*never re-run a failed job*). The operator asked for another sprint (2026-10-11) while S266 was being built; this was the next row that could be specced.

**Measured (2026-10-11, read-only on GitHub).** Run `37767377219` (commit `49146e40`, tag `s259`) reads `run_attempt` 2 and `success`. `/actions/runs/{id}/logs`, the path `surfaces/dashboard/github_tag_builds.py` reads, serves the latest attempt's archive: 25,420 bytes, the scanner job alone, no mention of `trading-agents-master:s259`. `/actions/runs/{id}/attempts/1/logs` serves 434,794 bytes over 30 entries and names the tag five times as a complete tag; `/attempts/3/logs` answers HTTP 404. The run rows the reader already lists carry `run_attempt`: on 100 of the last 100 successful runs, 99 of them with one attempt. Through the repo's own reader: on `main` the tag `s259` has no build for the commit; on the prototype it has that run, after two reads, and `record_verified_deploy` on an in-memory graph records it. DL-278's sizes for the same archives (953 KB, 56 KB, ten mentions) were not reproduced three days on; the finding stands.

**Decided.**

- **D1 - every attempt of a successful run is evidence.** The reader lists only runs whose latest attempt concluded `success`; a job that was not re-run succeeded in the attempt whose log names it; a re-run builds the same commit with the same inputs.
- **D2 - the latest archive first, at today's path, then each earlier attempt, newest first, stopping at the first that names the tag.** A run of one attempt costs the one read it costs today, and no existing test's fake changes.
- **D3 - the attempt count is the run row's `run_attempt`.** Absent, one attempt; present and not an integer of one or more (a boolean included), the reader's incomplete-response error before any archive is read.
- **D4 - an earlier archive that cannot be read is an error**, the same sanitised errors the latest archive raises.
- **D5 - one new clause, `SRF-DEP-04`**, states the whole rule for proving a tag (the complete tag, every attempt, `main`'s history, unreadable is not absent). The surfaces' law had none; DRIFT-111.
- **D6 - the change stays in `github_tag_builds.py`** (94 lines, 115 in the prototype): a fourth parameter on `run_log_mentions_tag`, defaulting to 1.

**Ruled out.**

- *Prove the tag from the registry* - a second credential scope and a second source for which commit a tag was built from.
- *Read the first attempt first, or every attempt always* - 99 of 100 runs have one attempt; their one read and its path would change under every existing test.
- *Read each job's log through the jobs API* - more calls for the same text.
- *Take an earlier archive that cannot be read for an absent tag* - unreadable evidence and absent evidence must not look alike.
- *Cap the attempts read* - no number to justify; each read is bounded by the timeout.
- *Keep the skill's rule and close the row* - it costs a second build and a second tag each time one job flakes.

**Named consequences.** After the merge and its check the deploy skill's rule can change: a failed job may be re-run before the fleet is retagged. The rule that a tag the fleet has pulled is never pushed again stands. A run of the same commit with more than one attempt that does not name the tag costs one more download for each earlier attempt.

**Seen and left.** When no run of the commit names the tag, `record_verified_deploy` asks again without the commit and the reader downloads the archive of each of the last 100 successful `main` runs: on `main` the record step for `s259` did not finish in 280 seconds. It is the path that refuses, and it refuses correctly.

**Prototype (measured, then removed from `../ta-s267`).** No existing test breaks (the 39 of the five related files pass unedited). Twelve of the fifteen planned tests fail on the unchanged code on behaviour; the three that pass state what does not change. Fifteen planted breaks, fifteen red.

**Not claimed.** A real deploy recorded on the live graph from a build with a re-run job: that waits for the next job that fails.

Evidence outside the repo: OneDrive `trading-agents-data/wq115-2026-10-11/`.

🔁 **Amendment 1, 2026-10-11 11:42 AEDT (planner) — built as decided and merged; what the check showed; one gap in the spec's own test plan.** Built by Codex with no amendment to the six decisions; the reader is the prototype in every line of code (the module docstring's `Role:` line alone differs, 114 lines for 115). Merged as `0.125.05` (`475dba3c`, GATE PROVEN). *F1*, on the merged `main`, at no cost and read-only on GitHub: for `s259` and commit `49146e40` the reader returns run `37767377219` after reading its latest archive (25,420 bytes) and then `/attempts/1/logs` (434,794 bytes); `s259a` returns run `37770503860` and `s25` none, as before; `record_verified_deploy` records `s259` on an in-memory graph; 4 of 4, the prototype's output line for line. *The gap:* D5's clause says an archive, a comparison or an attempt count that cannot be read is an error, and the plan's eight tests planted the archive and the count, never the comparison; that limb was covered only by an older test that cites no clause. The planner added a ninth test on the branch (a comparison GitHub refuses, one with no `ahead_by`, one whose `ahead_by` is a boolean: the reader's error, no host in it, no archive read) and broke the comparison five ways against it alone, five red. *Ruled out at the review:* citing the older test in the row instead (it lives in a file at 198 of 200 lines and asserts nothing about what was read). The deploy skill's rule is changed: a failed job may be re-run before the retag. *Still not claimed:* a real deploy recorded on the live graph from a build with a re-run job.

## DL-287 - a run's barrier history ends on the run's as-of, read through the run's lineage; the other eight wall-clock date reads S249 left stay as they are - status: MEASURED and DECIDED (planner, 2026-10-11 07:52 AEDT); specced as [S266](sprints/sprint-266-a-runs-barrier-history-ends-on-its-as-of.md); work-queue 103 part two; MERGED as S266 `0.125.04` (`b1580076`), F1a and F1b passed at no cost (amendment 1); work-queue 103 closed

🔁 **Amendment 1, 2026-10-11 11:22 AEDT (planner) — built as decided and merged; what the checks showed; one fault in the spec's own test recipe.** Built by Codex with no amendment to the six decisions; the two production files are the prototype byte for byte. Merged as `0.125.04` (`b1580076`, GATE PROVEN). *F1a*, on the merged `main` at no cost: this entry's measurement prints, on both graph-pull paths, the history's end, its newest bar and each claim's `as_of` and `entry_close` on the run's as-of, and every other line as before the change. *F1b*, at no cost, the first time the built path read the live market source: given `sched-2026-10-08`'s two buys on 2026-10-11, the provider wrote a history whose window is the scheduled run's own (2023-09-09 to 2026-10-08) and whose 760 bars a name equal, bar for bar, what that run stored on the live graph; a control with no lineage ended on 2026-10-11 and read 2026-10-09's bar, so a later bar was there to take (7 of 7 checks; 4 of them fail on the code before the merge). *The fault in the recipe:* the spec told the builder to fix the as-of when the test module is imported and to move `entry_bars()` back three days, but `entry_bars()` dates its bars at the call, so a suite that straddled 00:00 UTC put the run's newest bar a day after its as-of, no buy came out and the three end-to-end tests failed (3 of 9 cases with every import-time date moved a day back). The planner's change on the branch dates the run's bars from the as-of (0 of 9); no production file and no assertion changed. *Looked for in the whole suite:* with the clock moved one day forward once collection had finished, 4,654 tests passed and 1 failed, and that one measures a 900-second grace from a time fixed at import, which a run crossing midnight does not break. *Ruled out:* returning the handback for it (the recipe was the planner's, and the change is eight lines in one test helper); reading the clock once at the call and handing the dates to each test (it changes the shape of all three tests for the same effect). *Not proven:* a past-dated run or an analyst-stage resume on the deployed fleet, which runs the earlier code until the next retag.

**Why.** S249 (DL-255, DL-256) made a run's ingest follow the run's as-of and left nine wall-clock date reads as work-queue 103's second part, with *"which of them run inside a graph-pull run is not measured"*. The operator asked for the next sprint (2026-10-11); the queue's first row was this one.

**Measured (2026-10-11).** A spy on each of the nine reads, and a run placed for an as-of three days back, in memory with a fake source and no `.env`, down the three paths a run can take (the planner's `wq103b_clock_reads.py`):

- *Fleet-shaped* (each container entrypoint's own find/process pair; the forecaster on its own bus with the deployed legs): **two** of the nine are reached. `agents/provider/barrier_history.py:94` (`barrier_window`) returns today. `agents/forecaster/settlement_pass.py::_pass_date` returns the run's creation date, read from its `created_at` stamp; it reads the clock only for a run with no readable stamp (DL-243 D3).
- *The in-process pass* (`cascade_once`): the same two, plus the forecaster's news window (`agent.py:164`) and return window (`price_signal.py:79`), both returning today. The factor window (`factor_signal.py:78`) is not reached: no factor is enabled by default.
- *The served agents on a `run.trigger` event*: the scanner's, the analyst's, the portfolio manager's and the monitor's (`agent.py:182`, `:128`, `:119`, `provider_client.py:63`). The event carries a run id and a universe and no as-of. Nothing outside tests constructs `Dispatcher` or sends a request to those four agents; `SCAN-STA-03` says the scanner's served window is calculated from the clock.

What the one live read does: for that run `MarketData.window_end` and `RegimeContext.window_end` are the as-of, `BarrierHistory.window_end` and its newest bar are today's, and each `BarrierForecast` carries today as `as_of` and today's close as `entry_close` (101.7538 where the as-of's close is 101.7995), for a stop and a target the analyst computed on the as-of's bars. The same on both graph-pull paths. A run resumed from the analyst stage on a later day does the same: its `AnalystRun` is new, so the 24-hour rule (DL-241 D11) counts it. `PROV-OUT-08` already assumes otherwise: *"its newest session is the one the daily request judged"*.

On the live graph (read-only, `neon_barrier_ledger.py`): **0 of 8** `BarrierHistory` nodes end off their run's as-of, 0 hold a bar after it, 0 lack a `MarketData` lineage; **0 of 28** claims are dated after their run's as-of (one is dated a day before: TGT of `verify-2026-10-01-s248-a`, whose `MarketData` window followed the clock before S249). So nothing in the ledger is misdated yet; the first claims settle from about 2026-10-12.

**Decided.**

- **D1 - the as-of is the `window_end` of the `MarketData` the run was scanned from**, found by edge: the run's `ANALYZED_BY` ancestor, then that node's `DERIVED_FROM` descendant. The walk the portfolio manager and the forecaster's settlement already make, and the one a resume clone keeps (`orchestration/resume.py:110-111`, `:126`).
- **D2 - a run with no such lineage has no as-of, and its window ends on the UTC date of the fetch**, as an ingest no run triggered does under `PROV-TRG-05`. Only a hand-built run can be one: the graph-pull analyst recommends nothing without a `MarketData`.
- **D3 - a `MarketData` whose `window_end` is absent or not a date fails the work before any fetch** (`KeyError`, `ValueError`); no node is written and it is not served today. The scanner raises on the same node, so no pipeline run reaches this.
- **D4 - one new module, `agents/provider/barrier_window.py`**, holds the lineage read and the window helper with its two constants; `barrier_history.py` goes from 191 lines to 179.
- **D5 - the other eight reads stay.** The four served windows answer a request that carries no as-of, in decision-path agents, with no caller outside tests. The settlement pass's date is the run's creation date on purpose. The forecaster's three advisory windows are fired by the in-process pass and an RPC caller only, their request (`FORE-IN-01`, `FORE-IN-02`) carries no as-of, and nothing outside tests places a past as-of on that pass (`scripts/run_local.py` has no `--as-of`). **Named:** before any of the three legs is deployed, or run for a past as-of, its window must take the run's as-of, which is a field on `ForecastRequest` and a forecaster law cycle.
- **D6 - `PROV-OUT-08` is amended, no clause is added**; DRIFT-110 records the gap. No contract, graph property, env key or tunable changes; no forecaster file changes.

**Ruled out.**

- *Stamp the as-of on the `AnalystRun`* - it changes the analyst's write path while the fidelity count runs and adds a graph property (a full `up`); the 88 runs already written would not carry it.
- *Read the run id out of a key and fetch the small `RegimeContext` or `RunRequest` by it* - a resume clone's `MarketData` is keyed `resume-link:...`, so the parse fails on the runs this is for.
- *A props-light read in the graph port* - a port change, for about 1.9 MB a night.
- *Refuse a run with no lineage with a failed node* - `BarrierHistory` requires its window's two dates, so the node would need an invented window or a contract change, for a case only a hand-built run can produce.
- *Skip a run reached after its as-of* - the claim on the run's own bars is the honest one, and a re-run for a past session that states the scheduled run's claim again merges into it.
- *Fix all nine reads in one sprint* - seven are not reached by a fleet run, four of those sit in decision-path agents, and three need a contract field for legs nothing deployed fires.

**Named consequences.** A run reached after its as-of now states its claim under the as-of's date: it merges into the scheduled run's claim for that ticker when the barriers agree, and is refused with a fault when they differ, the first standing (`FORE-IDM-04`, unchanged). A claim stated for an as-of ten or more sessions back can settle on the next run's pass, and the barrier scorecard does not tell it from a forward claim. The provider reads one `ScanRun` (mean 46 KB) and one `MarketData` (mean 1.85 MB, largest 2.78 MB, over 88 live nodes) more for each run that holds a qualifying buy; that the read costs exactly those two nodes on Postgres is assumed, not measured.

**A correction to the tracker.** STATE's *Next* held work-queue 103 part two back *"while the fidelity count runs (each touches a decision path)"*. That was written of the eight reads in five agents before any was measured. The one change this sprint makes is in the provider's barrier history, a side branch only the forecaster's shadow claim reads (`FORE-NEV-02`); no decision path changes, and the spec's scope command says so file by file.

**Prototype (measured, then removed from `../ta-s266`).** On the prototype the same run stores the as-of for the history's end, its newest bar and each claim, with `entry_close` 101.7995, and nothing else in the measurement's output differs. One of 4,646 existing tests breaks (a clock pin that patches a name that moved); with its two lines edited and nine planned tests, the full suite reads 4,655 passed, 8 skipped, 100.00 %. Three end-to-end tests are red on the unchanged code on behaviour. Fourteen planted breaks, fourteen red.

**Not claimed.** Point-in-time replay. A past-dated run on the deployed fleet. Anything about a run whose as-of is today, placed while the session is open (its ingest reads that day's unfinished bar, here and before).

Evidence outside the repo: OneDrive `trading-agents-data/wq103b-2026-10-11/`.

## DL-286 - a model request that fails in the operator's chat is a fault inside the operator's own boundary, is audited on both capabilities, and is answered with one message that says why - status: MEASURED and DECIDED (planner, 2026-10-10 10:47 AEDT); specced as [S265](sprints/sprint-265-a-failed-chat-request-is-audited-and-says-why.md); work-queue 125; DRIFT-107 and DRIFT-108; MERGED as S265 `0.125.03` (`c32398fc`), F1a and F1b passed at no cost (amendment 1); work-queue 125 closed

🔁 **Amendment 1, 2026-10-11 07:28 AEDT (planner) — built as decided and merged; what the checks showed.** Built by Codex with no amendment to the seven decisions; the five production files are the prototype byte for byte. Merged as `0.125.03` (`c32398fc`, GATE PROVEN). *F1a*, on the merged `main` at no cost: this entry's measurement prints, on both vendors, the message, the linked audits and one fault for each of the 16 failed-request turns, and the eight control turns as before. *F1b*, at no cost, the first time a real vendor's refusal went through the built path: each real adapter on the real SDK with a key that is not a key. Both vendors answered HTTP 401, and on the quick ask and on a typed question the chat showed the lead sentence, the status and the vendor's own message, with the audit written and one fault (40 of 40 checks; 14 of them fail on the code before the merge). *Changed at the merge:* nothing; the clause is as this entry gave it. *Still not produced by a vendor through this path:* a time-out, a dropped connection, an account with no credit (HTTP 400), a rate limit (HTTP 429).

**The question.** Work-queue 125, found while measuring DL-285: when the operator's model request
itself fails, no `CommandAudit` is written and a typed question hides the reason. Two things were
left to decide: what a typed question says, and what the audit of a failed call reads, given that
the unattended scorecard counts an audit with no intent and an outcome other than `explain` as a
human action. This entry measures today's behaviour again, with more cases, and decides.

**Measured** *[2026-10-10, 10:05 to 10:45 AEDT; in the sprint's worktree, which has no `.env`, on
`main` at `f3e37421`; no call to a vendor except where a line says so. Each real operator adapter
was built by the factory on a fake SDK and bound into the surfaces' context, and each turn went
through the dashboard's chat handler. Scripts, outputs and the prototype's diff are outside the
repository, `trading-agents-data/wq125-2026-10-10/`]*. Both vendors read alike in every row.

| The request fails | Today | On the prototype |
| --- | --- | --- |
| the quick ask *explain this run*, a time-out | chat: *"Request timed out."*; **no `CommandAudit`**; a fault recorded by the bus | the message; audit `explain`, linked to the row; one fault from the operator's boundary |
| the quick ask, the vendor answers HTTP 400 | chat: *"The language model refused the request (HTTP 400): ..."*; no audit | the message, with the status and the vendor's words |
| the quick ask, an error with no text | chat: **an empty message**; no audit | the message, naming the error's type |
| a typed question, any of the three | chat: *"Operator could not parse the command."*, the reason nowhere; no audit; a fault from the agent | the same message as the quick ask; audit `refused`, linked; one fault |
| a typed question parsed, then its answer's request fails | audit `intent` only; the explain call has none | audits `intent` and `explain` |
| an explicit `approve flag-12` | refused, *"Operator could not parse the command."* | refused, the message |
| the unattended scorecard | counts nothing (there is no audit) | a failed typed question counts as one `command`; a failed explain counts as reading |

- The row of a failed call is unchanged: `unknown`, 0 output tokens, `estimated`, and the outage
  check reads it silent, as it should.
- Four control cases a vendor (a cut-off and a good reply, on the quick ask and on a typed
  question) print the same lines before and after the prototype.
- *What the SDKs really render* (one request a vendor from the main checkout with a key that is not
  a key: answered HTTP 401, nothing billed). OpenAI 2.49.0: `Error code: 401 - {'error':
  {'message': 'Incorrect API key provided: not-a-ke***q125. ...', 'type': 'invalid_request_error',
  ...}}`. Anthropic 0.120.2: `Error code: 401 - {'type': 'error', 'error': {'type':
  'authentication_error', 'message': 'invalid x-api-key'}, 'request_id': ...}`. The pattern in
  `surfaces/plain_errors.py` reads the status and the message from both. OpenAI's message repeats
  the key masked to its first eight and last four characters. A time-out reads *"Request timed
  out."* on OpenAI and a longer plain sentence on Anthropic.
- Only the operator's store, the contract and `surfaces/queries/scorecard_actions.py` read a
  `CommandAudit`; only `surfaces/operator_tools.py` and the command line (which binds the fake
  client) ask the operator to `interpret` or `explain`.
- *A prototype of the whole change*, five files, 129 lines added and 48 removed. Of the 4,588
  existing tests it breaks exactly three functions, the three that pin today's behaviour. 48
  prototype test cases pass on it. Broken 32 ways, one at a time, 32 went red (a first run of 30
  read 29: one break changed nothing and was replaced). `ruff`, `mypy` and the import contracts
  are clean.
- The law gate was run on a planted citation: a test that does not exist, added to a green row
  beside two live ones, leaves the gate at exit 0. It checks that a green row has one live test
  naming the clause, not each citation.
- A model reply that is not valid JSON emits no fault (three shapes planted), although
  `OPR-FAIL-01` lists *malformed JSON* among the failures that do: DRIFT-108.

**Decided.**

1. **The model call sits in its own fault boundary.** One helper,
   `agents/operator/ledger.py::recorded_completion`, opens the ledger capture outside and the
   caller's boundary inside, around the completion alone, and hands back the row, the reply and
   the fault. A request that fails is a fault and not a raise. A ledger write that fails is not a
   failed request and propagates as today.
2. **One message, built in the operator's domain:** *"The request to the language model failed, so
   there is no answer."*, then the error's own reason in plain words: *"The vendor answered HTTP
   400: ..."* for a status error, the error's text for any other, the error's type when it has no
   text.
3. **The pattern that reads an SDK's status-error text moves to the kernel**, unchanged
   (`kernel/llm_error_text.py`), so the agent and the surface read one pattern. The surface's
   `plain_error` keeps its sentence and its behaviour.
4. **`explain`** writes its audit with outcome `explain` on every path and returns the message for
   a failed request. It no longer raises to the bus for it.
5. **`interpret`** reads a failed request as a refusal whose reason is the message, and does not
   pass it through the explicit grammar. The existing flow writes the audit, `refused`. Any other
   fault inside `interpret` keeps *"Operator could not parse the command."*
6. **The audits keep today's vocabulary.** A failed explain is `explain` (reading on the
   scorecard); a failed interpret is `refused`, which the scorecard counts as a command, as it
   counts every interpret call that produced no intent and as a cut-off one is counted since S264.
7. **Nothing else moves**: a reply that came back, the adapters, the bus, the scorecard, the chat
   page, the debaters.

One law cycle follows, with no new clause: `OPR-FAIL-01` is reworded to say all of this for both
capabilities, and to stop listing a reply that is not JSON as a fault.

**Ruled out, and why.**

- *Keep the old division (the operator relays the error's text, the surface words it): `explain`
  keeps raising to the bus with its audit written first, and the surface rewords a refusal's
  message.* The smallest change, and it keeps the turn's outcome word `refused`. Rejected: one
  event would keep two idioms and two fault sources; a bare *"Request timed out."* or *"Connection
  error."* in a chat does not say what failed; an error with no text shows an empty message; and
  the sentence that says the model request failed can only be written by the agent, the one place
  that knows it was the model call. It is also the shape S264 chose for a cut-off.
- *Relay the text of every fault inside `interpret`.* A graph failure is not a model failure; only
  the measured case changes.
- *Apply the explicit grammar to a failed request, as to a cut-off*, so that `approve flag-12`
  typed during an outage asks for confirmation (the grammar needs no model). Rejected for this
  sprint: the law says a failed call is refused, and whether a command should act while the model
  is unreachable is a decision about commands during an outage, not about what the chat says. It
  can be asked for on its own.
- *A new audit outcome (`failed`) that the scorecard skips.* Nothing shows whether the words were a
  question or a command; an approval typed during an outage would leave the count; the rule is
  DL-235's.
- *Audit a failed `explain` as `refused`.* The scorecard would count a question as a human action.
- *Write the error's text or type on the `CommandAudit`.* `OPR-NEV-06` and `OPR-SEC-02` keep
  credentials and raw text out of the graph, and a vendor's 401 repeats the key masked. It would
  also be a new graph property. The linked row reads silent; the fault holds the type and text.
- *Copy the pattern into the operator's domain.* Two patterns for one vendor format. Importing the
  surface's is not possible: an agent may not import a surface.
- *Have the adapters raise a typed error carrying the status and the message.* Four adapters, the
  debate's two among them, for a text the SDKs already render one way.
- *Retry once.* An empty account or a refused key does not heal, and a paid call would be doubled
  with no evidence that it ends differently.
- *Shorten a long error text.* No measured case; a bound would be a number with no evidence.

**Named consequences.** The turn's outcome word for a failed quick ask goes from `refused` to
`answer`, because an `Explanation` carries no outcome of its own (the cut-off reads `answer` since
S264, and the chat page shows the message alone). An MCP client that calls `explain` gets the
message as an accepted answer instead of an `error` key. A failed typed question counts as one
`command` on the unattended scorecard where it counted as nothing.

**Found while reading the law, and not decided here.** `OPR-FAIL-02` says an intent with missing
required fields is refused. Measured: an unknown family is refused, but `approve` with no target,
`modify` with no name or value and `run` whose parameters are not an object each come back as an
intent with empty parameters, and a reply with no family comes back as a `status` intent.
DRIFT-109, work-queue 126.

**Not measured.** A failure met in the dashboard itself: the live ledger holds no failed operator
call. What a vendor sends for an empty account on OpenAI. A status error whose body is not JSON:
the SDK then uses the response's raw text, which this sprint shows as it is.

---

## DL-285 - a reply cut off at the cap is the port's stopped completion on both vendors; the operator records its stop reason and its tokens on both paths and writes the audit, and the chat says one sentence - status: MEASURED and DECIDED (planner, 2026-10-10 00:15 AEDT); specced as [S264](sprints/sprint-264-a-cut-off-reply-is-recorded-and-the-chat-says-so.md); work-queue 124; the failed request is work-queue 125; OpenAI's real cut-off read 2026-10-10 (amendment 1); MERGED as S264 `0.125.02` (`cc050bba`), F1a and F1b on OpenAI passed (amendment 2); work-queue 124 closed

🔁 **Amendment 3, 2026-10-11 08:09 AEDT (planner) — Anthropic's cut-off reply produced and read; a cut tool block does carry a partial input.** On the operator's word (*"go for it"*), one paid call on `main` at `035f07dc`: `claude-opus-5` at `max` with the cap at 64, one typed question through the dashboard's chat handler on an in-memory graph. The vendor answered `stop_reason: max_tokens`, 860 input and 64 output tokens, no thinking tokens, and one `tool_use` block for `parse_intent` with the input `{"outcome": "intent", "family": "explain"}`. That settles what *Not measured* below assumed: the SDK hands back the cut block with whatever fields were complete, and here they parse as an object that names a family and nothing else. Only the stop reason tells it from a whole call, so D1 (the adapter raises on the stop reason and the block is never read) is what keeps a half-written intent out. The chat showed the one sentence; the row reads `max_tokens`, 860 and 64, `vendor`, not silent; the audit reads `refused`; no fault. Cost **$0.0059** at the pack's rates, where the planner had quoted the operator about a third of a cent: the estimate counted the request body with `tiktoken` (331 tokens) and the vendor counted 860 for a forced tool call. *Ruled out after the fact: quoting a vendor's price from another vendor's tokenizer.* The vendor's own token count costs nothing to ask for. Not produced: a cut inside a string of the tool's input, and a cut at the real cap of 4,096. S264 owes nothing more ([functionality checks](laws/functionality-checks.md)).

🔁 **Amendment 2, 2026-10-10 02:03 AEDT (planner) — built as decided and merged; what the checks showed; one wording change to the law.** Built by Codex with no amendment to the six decisions; the production code is the prototype line for line. Merged as `0.125.02` (`cc050bba`, GATE PROVEN). *F1a*, on the merged `main` at no cost: this entry's measurement prints, on both vendors, the sentence for every cut-off question, the vendor's counts and stop word on the row, the audits and no fault; the failed-request cases read as before. *F1b on OpenAI*, one paid call ($0.0033; with amendment 1's, $0.0066 for the sprint): the call of amendment 1 on the built code. The chat showed the sentence, the row holds 278 in and 64 out with `max_output_tokens`, the audit reads `refused`, no fault. *Changed at the merge:* the builder's `OPR-FAIL-04` quoted the sentence inside the law; the law now says what the sentence must be and leaves its letters to the test that pins them, so the text exists once. *Owed:* F1b on Anthropic after 2026-10-11. *Still not produced by a vendor:* a cut at the real cap of 4,096; a reply cut inside a function call's arguments or a tool block.

🔁 **Amendment 1, 2026-10-10 00:28 AEDT (planner) — OpenAI's cut-off reply produced and read; it is the shape the adapter reads.** On the operator's word (*"yes, you may spend a tihrd of a cent"*), one paid call at 00:27 AEDT: `gpt-5.5` at `xhigh` with the cap at 64, a typed question through the chat handler on an in-memory graph, on `main` at `ad741063`. The vendor answered `status: incomplete`, `incomplete_details.reason: max_output_tokens`; `output` held one `reasoning` item and no function call; usage 278 in, 64 out (all reasoning), 0 cached; $0.0033 at the price pack's rates. On that code the chat said *"Operator could not parse the command."*, the row read `unknown`, 13 in, 0 out, `estimated`, no `CommandAudit` was written and a fault was recorded: what the table below shows for a fake reply, now for a real one. The call is not on the live ledger (the graph was in memory); this paragraph is its record. No decision changes. Still not produced: a reply cut inside the function call's arguments, and any cut-off on Anthropic.

**The question.** S263's paid check found that the operator's ledger rows carry no stop reason, and
reading the caller showed a cut-off reply is recorded differently on the two vendors (DL-284,
amendments 1 and 2). Work-queue 124 carried one decision: what the chat says when a reply is cut
off, the same on both vendors. This entry measures today's behaviour end to end and decides.

**Measured** *[2026-10-09 23:21 to 23:37 AEDT; in the sprint's worktree, which has no `.env`, on
`main` at `2ce40c30`; no call to a vendor. Each real operator adapter was built by the factory on a
fake SDK and bound into the surfaces' context, and each turn went through the dashboard's chat
handler. Scripts, outputs and the prototype's diff are outside the repository,
`trading-agents-data/wq124-2026-10-09/`]*. The fake cut-off reply carries 21,133 input and 4,096
output tokens.

| A reply cut off at the cap | OpenAI today | Anthropic today | Both, on the prototype |
| --- | --- | --- | --- |
| the quick ask *explain this run* | chat: *"openai completion stopped: stop_reason=max_output_tokens"*; row `unknown`, 0 out, `estimated`; **no `CommandAudit`**; a fault from the bus | chat: *"No explanation returned."*; row `unknown`, 4,096 out, `vendor`; audit `explain`; no fault | the sentence; row with the vendor's own stop word, 21,133 in, 4,096 out, `vendor`; audit `explain`; no fault |
| a typed question, its parse cut | chat: *"Operator could not parse the command."*; row as above; **no `CommandAudit`**; a fault from the agent | chat: *"model returned no tool result"*; audit `refused` | the sentence; audit `refused`; no fault |
| the reply cut inside the tool block | the adapter raises before it reads the output | the half sentence is shown as the answer *(on an assumed reply shape: a partial `input`)* | the sentence, and nothing of the cut reply |
| an explicit `approve flag-12`, its parse cut | refused, *"Operator could not parse the command."* | asks for confirmation: the grammar pins the intent over whatever the model returned | asks for confirmation |
| the outage check on the row (`is_silent_call`) | silent | silent for the explain | not silent |

- No operator row carries a stop reason: 23 of the 23 rows the measurement wrote on `main` read
  `unknown`, the good replies included. On the prototype a good reply reads `completed` or
  `tool_use`, a filtered one `content_filter` or `refusal`.
- The chat page shows only a turn's message; its outcome changes nothing on screen except for the
  three outcomes that carry a control (`renderTurn` and `send` in `chat.js`, read whole).
- The unattended scorecard counts a `CommandAudit` with no `Intent` and an outcome other than
  `explain` as a human action (`surfaces/queries/scorecard_actions.py::_acts`, read whole).
- The live ledger, read at 23:37 AEDT: 1,456 `LLMCall` rows, **none from any agent** recorded as cut
  at the cap (`max_tokens`, `length`, `max_output_tokens`). The operator has nine rows, all
  `unknown`, the largest reply 703 output tokens.
- *A prototype of the whole change*, four files, 58 lines added and 14 removed. The 857 existing
  tests over the operator, the debate, the surfaces and the adapters pass with it, and passed
  without it: none guards any of this. 25 prototype test cases pass on it. Broken 23 ways, one at a
  time, 23 went red. `mypy`, the import contracts, the size and header checks are clean.
- The law gate was run on a planted clause: it refuses a clause with no test-plan row, a green row
  whose test does not exist, a test whose docstring names no clause, and a rollup that disagrees
  with the derived 20 / 51. It does not read the test plan's own footer.

**Decided.**

1. **Anthropic's operator client raises on a cut-off, as OpenAI's does.** It keeps the reply's
   `stop_reason` as `last_stop_reason` (the port's `unknown` after construction and at the start of
   each call) and on `max_tokens` raises the port's stopped-completion error, after the stop reason
   and the usage are set. The port's docstring already asks this of every adapter; the operator's
   Anthropic client was the one that did neither. Every other stop reason returns as today.
2. **One helper records a completion on both paths.** `agents/operator/ledger.py::complete_recorded`
   sets the stop reason and the usage whether the reply came back or the vendor stopped it, and
   returns `None` for a cut-off. Any other exception passes through untouched.
3. **The chat says one fixed sentence:** *"The model's reply was cut off at its output limit before
   it finished, so there is no answer. Ask again, or ask something narrower."* No vendor, model,
   number or the word *token*.
4. **`explain`** writes its audit with outcome `explain`, as for an answer, then returns the
   sentence. No fault.
5. **`interpret`** reads a cut-off as a refusal whose reason is the sentence, through the same
   normaliser as any reply: an explicit `approve <target>` keeps its grammar, everything else is
   refused with the sentence, and the existing flow writes the audit. No fault.
6. **Nothing else moves**: a request that fails, a reply the vendor filtered or refused, the cap of
   4,096, every file of the surfaces, the debate's client.

One law cycle follows: `OPR-STA-03` reworded (the row carries the vendor's stop reason and counts on
both paths) and a new `OPR-FAIL-04` (a cut-off is neither a fault nor an answer).

**Ruled out, and why.**

- *Show the part of the reply that arrived, marked as cut.* OpenAI returns no usable part, so the
  vendors would differ again; and half a sentence about the book reads as a statement.
- *Leave Anthropic's client as it is and let the agent compare stop reasons.* The agent would need
  each vendor's vocabulary; the port assigns that to the adapter.
- *Raise from `explain` and let the bus report it*, which is what happens on OpenAI today. It skips
  the audit, records a fault for a call that completed and was billed, and shows a field name.
- *Reword the error at the surface*, in `surfaces/plain_errors.py`, where a vendor's status error is
  already reworded. It would change the words on one path of one vendor and leave the row's tokens,
  the missing audit, the fault and Anthropic's unexplained answer as they are.
- *Audit a cut-off `explain` as `refused`.* The scorecard would count a question as a human action.
- *Record a fault for a cut-off.* On Anthropic it never was one; the row and the audit are the
  record; on the dashboard the fault sink is in memory and nobody reads it.
- *Name the cap or the vendor in the sentence.* The agent is handed a client and does not know its
  cap; the vendor's word is on the row.
- *Raise on a vendor's refusal too*, as the port's docstring also allows. The OpenAI adapter returns
  the refusal dictionary on `content_filter` (S263, test A5), so raising on Anthropic's `refusal`
  would make the vendors differ; neither has been seen; the row now names the reason.
- *Retry once, or raise the cap.* The cap's bound is the law's; a retry doubles a paid call with no
  evidence that it ends differently.

**Found while measuring, and not decided here.** When the request itself fails (a time-out, the
vendor answering HTTP 400), on both vendors alike: no `CommandAudit` is written for either
capability, although `OPR-OUT-06` says every call has one; the quick ask shows the error's text,
which the surface already rewords for a status error; a typed question says *"Operator could not
parse the command."* and the reason is shown nowhere. The prototype leaves these eight cases exactly
as they are. Work-queue 125, DRIFT-107: it needs its own decision (what a typed question says, and
what the audit of a failed call reads, given the scorecard's rule), and it touches the same two call
sites, so it follows S264.

**Not measured.** A cut-off produced by a vendor: both adapters read it from the SDK's types, and
whether Anthropic returns a partial tool input is assumed. The check after merge produces one on
each vendor with the cap at 64, under one cent each, on the operator's word.

---

## DL-284 - on OpenAI the operator's forced function goes through the Responses API, its effort resolves from the provider as its model does, and an explicit model of another vendor refuses the chat's binding - status: MEASURED and DECIDED (planner, 2026-10-09 21:11 AEDT); MERGED as [S263](sprints/sprint-263-the-operators-chat-makes-its-tool-call-on-openai.md) `0.125.01` (`9df7dacd`), F1a and F1b passed 2026-10-09; work-queue 121 closed, 124 opened

🔁 **Amendment 2, 2026-10-09 23:06 AEDT (planner) — amendment 1 overstated the ledger defect; corrected by measuring through each real adapter.** Amendment 1 said a cut-off call's row holds 0 output tokens *on either vendor*. That was inferred from a stand-in client that raises, and it is true on OpenAI only. Measured offline on the merged code, each real operator adapter on a fake SDK, one cut-off explain each: on OpenAI the adapter raises and the row holds 0 output tokens stamped `estimated`; on Anthropic the operator's adapter does not raise, the row holds the vendor's 21,133 and 4,096, and the chat answers *"No explanation returned."* Missing on both: the stop reason, which the agent never passes on and which Anthropic's operator client does not expose. The token loss dates from S262's OpenAI adapter, which raised the same way, and S263 kept that. Work-queue 124 is restated, with one decision added: what the chat says on a cut-off, the same on both vendors.

🔁 **Amendment 1, 2026-10-09 22:49 AEDT (planner) — built as decided and merged; what the paid check confirmed and what it found.**

- **Confirmed (F1b, three calls, $0.27).** Through the dashboard binding on the merged code `gpt-5.5` answered an
  explain and an interpret at `xhigh`: 797, 233 and 716 output tokens of 4,096, none cut, 12.2 and 13.8 seconds a
  turn. With the measurement's two that is five replies at `xhigh`, the largest 811.
- **Decision 3 holds in the adapter and not in the operator's ledger.** The adapter keeps the vendor's word and, on
  a cut-off, the usage before it raises. The operator agent passes neither on: its ledger rows read `unknown` for
  every call, on either vendor, and a cut-off call's row holds 0 output tokens stamped `estimated` (measured
  offline on the merged code). This entry wrote *recorded* as if the adapter's two fields were the record, and
  S263's Goal repeats it: the adapter and the port were read, the caller was not. Not caused by the sprint;
  work-queue 124.
- **Still not observed:** a cached input token (0 on all eleven accepted calls; the two explain prompts differ
  from their first line, so nothing repeats), a reply the vendor cut off, the return to Anthropic.

**The question.** S262's paid check found the dashboard chat cannot run on OpenAI (DL-282,
amendment 2): `gpt-5.5` refuses the effort `max`, refuses a function tool with any reasoning effort on
Chat Completions, and the operator's `.env` would send it an Anthropic model name. DL-282's decision 5
was made unmeasured. This entry measures each choice against the vendor first.

**Measured** *[2026-10-09; scripts, prompts, wire requests and replies are kept outside the repository, `trading-agents-data/wq121-2026-10-09/`]*.

*At no cost.* The Responses API was read in the installed SDK (`openai` 2.49.0,
`types/responses/`): the request fields `instructions`, `input`, `max_output_tokens`,
`reasoning.effort`, `tools`, `tool_choice`, `store`; the reply's `status`, `incomplete_details.reason`,
`output` items of type `function_call` carrying `arguments`, and `usage.input_tokens`,
`usage.input_tokens_details.cached_tokens`, `usage.output_tokens`. The chat's two real prompts were
captured from the live graph with a fake model: the explain prompt for `sched-2026-10-08` is 21,049
tokens (the 3,958 in S262's record was a word count), the interpret prompt about 290.

*Nine calls to the vendor, $0.38 at the price pack's rates, one at a time under a stop rule of $0.60.*

| Road | Effort | Prompt | Vendor's answer | Seconds | Output tokens of 4,096 | Of them reasoning |
| --- | --- | --- | --- | --- | --- | --- |
| Responses | `max` | interpret | HTTP 400, `'max' is not supported with the 'gpt-5.5' model. Supported values are: 'none', 'low', 'medium', 'high', and 'xhigh'.` | 2.2 | none, nothing billed | |
| Responses | `xhigh` | interpret | the function call | 4.6 | 187 | 121 |
| Responses | `high` | interpret | the function call | 2.9 | 60 | 0 |
| Responses | `medium` | interpret | the function call | 2.9 | 58 | 0 |
| Responses | `none` | interpret | the function call | 3.1 | 65 | 0 |
| Chat Completions | `none` | interpret | the function call | 3.4 | 60 | 0 |
| Responses | `xhigh` | explain | the function call | 9.4 | 811 | 516 |
| Responses | `high` | explain | the function call | 5.8 | 293 | 0 |
| Chat Completions | `none` | explain | the function call | 6.6 | 307 | 0 |

- Every accepted call returned usable arguments: the same intent on the interpret prompt, and on the
  explain prompt a paragraph with the same verdict and numbers. One sample each: this is not a
  comparison of answer quality.
- With a forced function the model reasoned at `xhigh` only. At `high` and `medium` it wrote no
  reasoning token on either prompt.
- A completed reply reads `status: completed`; its `output` holds a `reasoning` item, when the model
  reasoned, and then the `function_call`. Chat Completions ends a forced call on `tool_calls`.
- No reply reported a cached token, so the reading of `cached_tokens` as a part of `input_tokens`
  rests on the SDK's wording (*"a detailed breakdown of the input tokens"*), not on an observed value.
- A cut-off reply was not produced by the vendor: no call came near the cap.

*A prototype of the whole change* (five code files and one law row, kept as a diff outside the
repository): the six accepted Responses replies, replayed through the real SDK on a fake transport,
give back what the paid calls returned, with the same stop reason and usage, and the request the SDK
sends equals the request captured on the wire, also in a process where DSPy has registered its lazy
`openai` module first. The parameter step of `make ci` goes red on the changed default and green once
the law row follows. Eight existing test cases in three files fail (five test functions: they pin
the old endpoint's shape or the old default). `mypy`, the import contracts and the size check pass.

**Decided.**

1. **The OpenAI operator adapter calls the Responses API.** System text as `instructions`, user text
   as `input`, one function tool with `strict: false`, `tool_choice` naming it, the operator's cap as
   `max_output_tokens`, the effort as `reasoning.effort`. The arguments are read from the first
   `output` item of type `function_call`; a reply without one is the same refusal as today.
2. **`store: false`.** The explain prompt carries the book; nothing reads a stored reply.
3. **The stop reason recorded is the vendor's own word**: the incomplete reason when there is one
   (`max_output_tokens`, `content_filter`), else the status (`completed`). A reply cut on
   `max_output_tokens` raises the port's stopped-completion error after its usage is recorded.
4. **Usage is read as on Chat Completions**: input minus cached is the uncached input, cached is the
   cache read. `cache_write_tokens`, a field the reply also carries (0 on all nine), is not carried:
   whether `input_tokens` includes it is not known.
5. **The operator's effort resolves from the provider, as its model does.** The setting's default
   becomes empty; empty resolves `max` on Anthropic and `xhigh` on OpenAI. An explicit value is sent
   as set. The setting accepts both vendors' words, so `none` joins the list.
6. **An explicit model whose name starts with another provider's family prefix is refused** when the
   operator's client is built (`claude-` is Anthropic's; `gpt-`, `chatgpt-`, `o1`, `o3`, `o4` are
   OpenAI's). The chat binding returns disconnected and writes the reason on the dashboard's start-up
   output. A name that starts with none of them is left to the selected vendor.
7. **The cap stays 4,096.** The largest reply used 811.
8. **`.env.example` stops planting the trap**: it no longer sets `OPERATOR_MODEL`.
9. **Rider, found while measuring.** `agents/deliberator/tests/test_llm_openai_adapter.py` fails when
   run alone on `main` (`ImportError`, a circular import): importing the deliberator loads DSPy, DSPy
   registers `openai` as a lazy module, and the test's first use of the SDK is a submodule import.
   Reading an attribute of the package first loads it; one line. Its comment that CI does not
   install the SDK is also stale: the SDK arrives with DSPy in the dev group.

**Ruled out, and why.**

- *Stay on Chat Completions and send effort `none`*: measured to work, and it is a one-value change.
  But on that endpoint every other effort is refused with a function tool, so the operator's effort
  setting would mean nothing on this vendor, and the vendor's own message names Responses as the way
  to keep both.
- *Translate `max` to `xhigh` inside the adapter*: an explicit value the model refuses should be
  seen, not rewritten (the operator law's row; DL-282). Resolving an unset value is not a translation.
- *Default to `high` on OpenAI, as the debaters run*: with a forced function `high` reasoned nothing,
  so it is `none` under another name here; `xhigh` is the one value that reasoned, and it used a
  fifth of the cap on the largest real prompt.
- *Check the effort against a ladder for each vendor at the binding*: the ladder is the model's, not
  the vendor's (the SDK's type lists `max` and `minimal`; the vendor's message for `gpt-5.5` lists
  neither), so a table here would be wrong for the next model. The vendor's refusal costs nothing and names the
  supported values, and the chat shows it.
- *Record the cut-off as `length`, Chat's word*: the ledger keeps each vendor's own word already
  (`max_tokens`, `length`). A translated word would claim a field the reply did not carry. The cost:
  a query for cut-off calls must know a third word.
- *`strict: true`*: not tried. The intent schema has an open `parameters` object and optional fields;
  the operator's parser already refuses what it cannot read.
- *Refuse every model name not known here*: a new family or a fine-tuned name is not this code's to
  judge.
- *Stop the dashboard when the model belongs to another vendor*: the dashboard is the status board
  and the chat is one panel of it; it stays up and says why the chat is dark.
- *Give the debaters the same two rules in this sprint*: their default effort is `max` too, and an
  explicit role model of another vendor would be sent as is. On the fleet the tunables pack sets
  `high` on all three apps and leaves the models empty, and a full `up` re-applies both, so nothing
  is live. What a debater should do at start with another vendor's model is its own decision: a
  refusal to start means no debate record, and under the binding posture that drops every buy.
  Work-queue 123.

**Not measured, each named in the spec.** A reply cut off by the vendor (the adapter's reading of it
rests on the SDK's types; the cap was never approached). A non-zero `cached_tokens`. The effort
`low`. The return to Anthropic, whose account is empty until 2026-10-11. S263's paid check, one
explain and one interpret through the binding on the merged code, reads the second and gives two more
samples at `xhigh`.

## DL-283 - a sensor for containers that do not start or stop cleanly: the platform's event log already holds when and why, nothing reads it, and no container in the fleet has a shutdown path - status: DECIDED as a direction (planner, 2026-10-09 17:39 AEDT); the sensor is work-queue 119 and the shutdown path is work-queue 116; neither is specced

**The operator's words, 2026-10-09.** *"remind me untill we resolve it: container restarts and
unexpected falure tracker"*; asked what was meant, *"tracker as in sensor. I want to know when and wht
containers do not start cleanly"*; and then *"does master properly shutts down (closing onnections,
logging shutdown)?"*

**Measured** *[2026-10-09, read-only; the raw rows are kept outside the repository, `trading-agents-data/container-starts-2026-10-09/`]*.

- The log workspace `trading-agents-logs` keeps 30 days of the platform's container events
  (`ContainerAppSystemLogs_CL`). An event reaches it a median 4 seconds after it happens (95 % within
  7 seconds, the worst 43, over 5,343 events of seven days).
- In those 30 days it holds **456 crash, kill and failed-start events on 21 days**. None reached the
  operator, except where a session happened to read the log by hand.

| What the platform recorded | Events | Days | Apps | Last |
| --- | --- | --- | --- | --- |
| `Persistent Failure to start container` | 255 | 13 | 16 | 2026-09-29 |
| Terminated with exit code 1 | 102 | 3 | 13 | 2026-09-25 |
| The master terminated with exit code 137 | 52 | 16 | 1 | 2026-10-08 |
| Killed for memory | 38 | 1 | 2 (scanner, reporter) | 2026-09-28 |
| Another app terminated with exit code 137 | 9 | 5 | 6 | 2026-09-27 |

- 104 of the 456 fell inside a nightly window (22:00 to 00:30 UTC), on six nights, the last
  2026-09-28. Since 2026-10-03 the only events are the master's five kills of the retag day.
- 80 of the exits with code 1 came in seven minutes on 2026-09-25 (00:32 to 00:39 UTC) on 13 apps. The
  one console read (the scanner's) shows its first call to the master failing. Not traced further here.
- **Noise that must not raise an alarm:** `Waiting for infrastructure to be ready` (744, on every one
  of the 30 days, all 17 targets), the master's start-up probe refused while it boots (929, every day)
  and the scaler's messages at a revision change (3,182).
- 🪤 `first`, `last`, `day` and `kind` are reserved in the query language: a query that names a column
  so fails with a bare syntax error.

**Shutdown: read in the code, and measured where the platform logs it.**

- No module under `agents/`, `kernel/`, `orchestration/` or `surfaces/` installs a signal handler or
  an exit hook (searched: none). Every image starts Python directly as the container's command. The
  master's `serve` runs *"until the process ends"*. Nothing writes `Session.ended_at`, which
  `MST-OUT-03` names as the mark of a stop that was not a crash. The app sets no stop grace, so it has
  the platform's 30 seconds.
- Every stop of the master that the platform logged ended 31 or 32 seconds after `Stopping container`
  with exit code 137: **52 of 52, and no clean exit on record.** Each is on a new revision (a deploy, a
  retag, an env update).
- **So the master does not shut down.** It does not react to the stop signal, logs nothing, closes
  neither its graph connection nor its socket, never marks its session ended, and is killed. Read from
  the code, the same holds for the fifteen agents.
- *Not measured:* the platform logs no exit at an ordinary nightly scale-down, for any app, so
  whether those also end in a kill is not known from the log; and whether a kill has ever landed
  between two graph writes of one activation. A single write cannot be torn: the database rolls an
  unfinished statement back.

**Decided.**

1. **The sensor reads the platform's event log.** It is the only place that holds the reason (exit
   code, memory kill, start failure). The why is completed by the last error line of that replica's
   console log.
2. **It runs in the dispatcher job**, which already ticks every ten minutes through the nightly window,
   already sends Telegram messages and already writes the morning brief. Each tick reads the events
   since its last read, so the first tick of a night also covers the day's deploys.
3. **The operator is told three ways:** a Telegram message at once when a tick finds one (which app,
   when, why); one line in the morning brief; a record in the graph, so the dashboard and the health
   signal see it.
4. **It alarms on** a failed start, a termination with a non-zero exit code and a memory kill. It
   reports a preemption without alarming. It ignores the three kinds of noise above.
5. **The shutdown path is a separate fix, built first** (work-queue 116, widened to every container):
   on the stop signal a process stops taking work, closes what it holds, records the end of its
   session, logs one line and exits 0 inside the grace. Built in the kernel's serving code and the
   master's server, so no file under a fidelity decision path changes. It follows S262, which edits
   the same master entrypoint.

**Ruled out, and why.**

- *An Azure Monitor alert rule that emails the operator.* It works even when the whole fleet is down,
  but it is a second channel beside Telegram, a monthly charge, and leaves nothing in the graph. Kept
  as a possible later watchdog for the case the sensor cannot see: the dispatcher itself not starting.
- *The master as the reader.* It is awake only around the run, and it is the app most often affected.
- *The dashboard alone.* It shows what is asked for; it does not tell anyone.
- *Inferring from the graph.* Activations show that a container started twice, never why, and a
  container that never started leaves nothing at all.

**Needed, to be measured when the sprints are specced.** The dispatcher job has no identity today
(`identity: None`); reading the workspace needs one, with read access to it. The shape of the graph
record and where the sensor keeps the time of its last read.

**Until the sensor exists** the fleet check reads the event log by hand (the `check-fleet` skill,
step 7).

## DL-282 - the fleet's LLM vendor becomes one declared value that the deliberators, the operator, its chat and the master's probes follow, with one command to apply and prove it - status: DECIDED (planner, 2026-10-09 17:25 AEDT); the build is [S262](sprints/sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it.md), work-queue 109

🔁 **Amendment 2, 2026-10-09 20:35 AEDT (planner) — deployed as `s262`; what the live checks confirmed and what they refuted.**

- **Confirmed on the fleet (F1a).** With the provider declared and the full 13-probe pack on the master, its fleet check passed over 15 agent types; the command reported, applied and proved the operator's value; the operator activated with OpenAI's probe as the only one declared. An env-only update on an app at 0 replicas starts a replica, and that agent's first call wakes the master: the proof was read inside 90 seconds of the start instant.
- **My order for the master was wrong, and was caught before acting.** The spec said: the provider first, then the packs. Run offline with the merged code against the four combinations: the provider with the old, untagged pack stops the master at start (*granted openai key without its probe*, decision 2's own refusal), and the new pack without the provider runs Anthropic's probes. So the three values went to the master in one update. *Ruled out:* either value alone, in either order. The same hazard sits in a full `up`, which sets them in separate calls: work-queue 122.
- **Decision 5 is refuted by the vendor (F1b, verified failing).** `gpt-5.5` answers HTTP 400 to the operator's default effort: *"'reasoning_effort' does not support 'max' with this model. Supported values are: 'none', 'low', 'medium', 'high', and 'xhigh'."* and, with an accepted effort, HTTP 400 again: *"Function tools with reasoning_effort are not supported for gpt-5.5 in /v1/chat/completions. To use function tools, use /v1/responses or set reasoning_effort to 'none'."* Two things this entry ruled out were wrong: *translate the effort* (the SDK's type lists `max`; the model does not accept it) and staying on Chat Completions for the tool call. Nothing was spent: each call was refused before generation. The fix is work-queue 121, and each of its choices is measured against the vendor before it is specced.
- **Found on the way.** The operator's `.env` carries an explicit `OPERATOR_MODEL`, which wins over the provider's default: declaring the provider alone would send an Anthropic model name to OpenAI. Decision 4 copied the deliberator's rule (an explicit value wins) without asking what an explicit value of the other vendor should do; work-queue 121 answers it.
- **Residue, unchanged:** the three provider lines in the tunables pack; the return to Anthropic unproven; a rollback below `s262` needs the eight-probe pack put back on the master.

**The question** (operator, 2026-10-06, DL-265): switching the vendor *"SHOULD be a configurational change and a
trigger"*. By hand it took five live changes on four apps and a hand-edited copy of the master's
credential-test pack, and any full `up` reverts it.

**Measured before deciding** *[2026-10-09; the prototype's diff and outputs are outside the repository, `trading-agents-data/wq109-2026-10-09/`]*.

- The operator **container** calls no vendor: its entrypoint binds the fake client. Its Anthropic
  probe guards a key that only the dashboard chat uses, and that chat is the operator agent's one
  real LLM use (`surfaces/dashboard/chat_binding.py`, Anthropic only).
- A prototype of the selection, the packs, the operator's setting, an OpenAI operator adapter and the
  chat binding changes 11 files and adds 2, touches **no** fidelity decision path, and breaks exactly
  four existing tests (two pin 12 probes, two patch a name the chat binding no longer imports).
- The parameter step of `make ci` goes red on the new settings field until its law row exists, and
  green after: the S258 gate covers this change by itself.
- `properties.runningStatus` reads `Running` on an app with 0 replicas (three apps, 06:14 UTC), so a
  "nothing is running" guard must count replicas.
- Not measured, each named in the spec with the check that settles it: whether `gpt-5.5` accepts the
  operator's effort `max` with a forced function inside 4,096 completion tokens (a paid call, F1b);
  whether an env-only update on an app at 0 replicas starts a replica (F1a).

**Decided.**

1. **The value lives in a new pack file, `orchestration/packs/trading_llm.json`**: the provider, and
   for each of five apps the environment variable that app reads. At merge it says `openai`, which is
   what the fleet runs on the operator's word of 2026-10-07.
2. **The master selects once, where it loads its packs.** A probe may carry its vendor; with a
   declared provider the master keeps that vendor's probes and key and drops the other's. An empty
   setting is today's behaviour. It refuses to start on an unknown provider, an unknown tag, or a
   granted vendor key with no probe.
3. **The unselected vendor's key is withheld**, not handed over untested (DL-36).
4. **The operator's settings gain `llm_provider`**, and its model resolves from the provider, as the
   deliberator's does since DL-100. The container keeps the fake client.
5. **The dashboard chat follows the operator's provider** through a kernel factory and a new OpenAI
   adapter with one forced function call.
6. **The deploy script reads the pack**, so a full `up` keeps the value; it wins over the tunables
   pack's line for the same key.
7. **The command is Python** (`scripts/switch_llm_provider.py`) with the `az` runner injected: report,
   apply to the apps that differ, check nothing else on them moved, read the proof from the graph.
8. **The tunables pack is not edited.** Its three provider lines stay until the fidelity count allows
   a pack edit; work-queue 109 stays open until then.

**Ruled out, and why.**

- *Filter the credential pack in the deploy tooling* (the hand method): the filter would sit in
  PowerShell, unread by the gate, and the master would run a pack the repository does not hold.
- *The command takes the vendor as an argument*: a live-only state, which a full `up` reverts. It
  applies what the pack declares.
- *Hand both keys over and test one*: against DL-36.
- *Select on every call inside the credential report*: prototyped first; it threads an argument
  through two near-full modules and withholds no key.
- *Record the provider on `FleetPreflight`*: a new property on a property-enforced label moves the
  vocabulary pack and turns an image-only retag into a full `up`.
- *The command wakes unchanged apps to re-prove their activation*: temporary scale rules on live
  apps; the fleet check already tests every agent type's credentials, and the command says which
  activations it did not re-prove.
- *A vendor per role*: one provider for all; a second would need the master's selection per agent
  type.
- *Carry the manager's wait and the debate concurrency in the same file*: both would also survive a
  full `up`, but they are not this row; they stay live-only.

**Residue named now.** The return to Anthropic cannot be proven live before its account is funded
(2026-10-11). The operator container still binds the fake client. A rollback below this sprint's
image needs the hand-made eight-probe pack put back on the master.

**S262 build amendment (2026-10-09): proof retry scope.** `--prove-since` alone has no record of
which apps the previous apply changed: D8 forbids adding graph properties, and unchanged apps must
not require fresh activations. Reusing `--evidence-dir` recovers the changed set from the original
before snapshots; without evidence the retry names its conservative scope and requires all
non-master pack targets. Ruled out: infer the changed set from missing activations (that would erase
the very failure being checked), or write a new graph property. No D1-D10 decision is reversed.

## DL-281 - S260's command defaults to the four measured concurrencies - status: DECIDED (builder, 2026-10-09)

D9 lists every argument default except the concurrency list. The Goal says the bare command runs
several debates at once, and the required command compares one through four. Default `--concurrency`
to `1 2 3 4`, keeping an explicit list authoritative. Requiring the flag or choosing only four was
ruled out: either would make the bare command miss the stated comparison. This is a tooling default;
no production setting or pack changes. All other choices implement D1-D9, including real first-poll
startup, without changing the Appendix's production calls.

**Proof constraint found during the build.** Main advanced independently after the sprint tree was
cut from `10770f91`, including STATE trimming and tracker updates. The requested two-tip
`git diff main --stat` therefore includes reverse STATE changes even though this branch never edits
STATE. Retain that actual output and assess this sprint's protected-path edits against its original
base and merge base, naming the literal empty-output check as failing. Rebasing solely to make that
check print nothing was ruled out: it would import unrelated history into the proving tree without
changing the harness. Do not alter STATE or main to manufacture an empty result. The sprint's Return
notes record the measured refs and all three comparisons.

---

## DL-280 - the judge has ruled `revise` on every order since the reward-to-risk floor went to 0, and `revise` changes no order; the causes are in the packet and in the judge's prompt - status: MEASURED; fix PROPOSED (planner, 2026-10-09 10:20 AEDT), told to the operator, not yet confirmed

**The question.** On `sched-2026-10-08` the judge ruled `revise` on TMO because *"the live reward-risk gate
is effectively disabled at threshold 0"*. That floor is a recorded decision
([ADR-0027](decisions/0027-reward-risk-compares-measured-upside-against-measured-downside.md), Correction 2).
Is this one ruling or a pattern, and why does it happen?

**Measured 2026-10-09, no LLM call.** Every `DeliberationRun` with a real debate, and the recorded packet and
turns of TMO's (scripts and outputs: OneDrive `trading-agents-data/f2-sched-2026-10-08/`, `analysis_a.py`).

| Rulings | All | `revise` | `uphold` | `overturn` | Rationale names reward-to-risk |
| --- | --- | --- | --- | --- | --- |
| Before 2026-09-17 | 209 | 161 | 26 | 22 | 29 |
| From 2026-09-17, the floor at 0 (S211) | 35 | 35 | 0 | 0 | 32 |

- 34 of the 35 are Opus's and one is `gpt-5.5`'s, so it is not one vendor's habit.
- **`revise` has no reader.** Execution drops an order only when its ticker is in `vetoed_tickers`
  (`agents/execution/deliberation_gate.py::drop_vetoed`). None of the 35 orders was vetoed or changed.
- **The packet prints the ratio as a gate that passed.** TMO's line: `PM gate outcome: name=reward_risk
  value_reward_risk_ratio=1.004 threshold_reward_risk_ratio=0 -> PASSED (… comparison=DISCLOSURE_ONLY)`. It
  has the form of the eight real gates beside it. Nothing says the ratio is printed and not enforced, or why.
- **The judge's prompt** (`kernel/deliberation_prompts.py::JUDGE_SYSTEM`, version
  `2026-09-30-s245-v6-judge-claude-opus-5`) says *"If the Challenger catches a grounded
  implementation-specific flaw from the evidence, do not uphold the decision"*, and all six of its examples
  rule `revise`. One of them (`alpha158-weight-zero`) rules `revise` because a weight of 0.00 *"is a disabled
  signal"*, which is the shape of the argument made about the floor.
- 🪰 The last column counts rationales that name the theme, by a keyword pattern; a rationale can name several.
- *[not measured]* Whether the judge's earlier prompt versions held the same six examples (77 % `revise`
  before 2026-09-17 suggests so); what the 35 debates cost.

**Reading.** Three causes that add. The packet shows a disclosed number as a passed gate and does not state
the decision behind it. The judge may not uphold once an implementation flaw is named, and this one is on
every order. Every example it was given rules `revise`. So the judge rules on the system's design, which is
the same for every order, and the ruling cannot tell one order from another. The ruling it then gives is
read by nothing.

**Consequence for [DL-264](design-log.md)'s order.** Amendment 6's loop gives `revise` an effect: a smaller
quantity or no order. With this judge it would shrink or drop every order. The judge's contract therefore
comes before the loop, and before the debaters' typed turn, whose worth is read through the judge.

**Proposed (work-queue 118).**

1. **The packet, deliberator only, so no fidelity decision path moves.** A gate whose detail says
   `comparison=DISCLOSURE_ONLY` is not rendered as `PM gate outcome … -> PASSED`. One line, in the manner of
   S255's *rule for every order*, states that the ratio is printed and not enforced, by ADR-0027's decision
   and on its evidence. The same sprint states that the name's previous lot was stopped out that session
   ([DL-240](design-log.md) amendment 2; work-queue 98's *past fills in the ticker*).
2. **The judge's contract**, ahead of the debaters' typed turn: rule on what distinguishes this order from
   the others; a property shared by every order is recorded as a design note and cannot decide the ruling;
   the examples include an `uphold` and an `overturn`. It changes a prompt, so ADR-0010's gate and a paid
   replay apply.
3. **`revise`** takes its effect from amendment 6's loop, in shadow first.

**Proof before either ships:** the ten stored packets replayed on `gpt-5.5`, about $8, on the operator's
word. The bar: the rulings are not all the same, and none rests on the floor.

**Ruled out.** *Raising the floor so the gate can fail:* Correction 2 measured that the ratio does not
predict returns (+0.03 % per trade, 95 % CI −0.17 % to +0.23 %, 47,485 decisions) and that a floor of 0.80
rejects between 0 % and 99 % of a night's book. *Removing the line from the packet:* the debaters would lose
the stop and target geometry, and withholding is what work-queue 98 exists to end. *Dropping `revise` from
the judge's choices now:* under the instruction not to uphold, the rulings may all move to `overturn` and no
buy would be placed; not measured, so not done blind. *The packet line alone:* the same rationales also name
fixed-fraction sizing (a distinction the prompt teaches) and the stop's gap risk on most orders, so the
ruling would probably stay `revise` for another reason shared by every order (not measured).

---

## DL-279 - the production manager and debaters, run together at four debates at once with a canned model, lose no reply at one request a pass and fail two orders of four open at ten; the harness is specced as S260 - status: MEASURED and DECIDED (planner, 2026-10-09 09:18 AEDT); MERGED as [S260](sprints/sprint-260-debates-at-once-lose-no-reply-and-the-repo-can-show-it.md) `0.124.00` (`19239d25`), F1 passed 2026-10-09; work-queue 113

**The question.** [DL-277](design-log.md) measured the request side alone: four consumers on one
subscription and a handler that sleeps. Step 1 of its plan is a committed harness on the production
manager and debaters together. What must it be, and does DL-277's result hold with the manager in it?

**Measured 2026-10-09, no LLM call.** A prototype on no branch (S260's Appendix; the file and its outputs
are in OneDrive `trading-agents-data/s260-2026-10-09/`). Between a transport and a canned model that
sleeps, everything is the repository's code as the fleet calls it: `review_pm_node`,
`ServiceBusPeerClient` and its reply inbox, `AzureServiceBusRequestConsumer`, `serve_once`,
`DeliberatorAgent`. Two transports: a stand-in bus in the process, and three disposable topics on the
live namespace, run before that morning's scheduled run began and deleted after each configuration.

| Run | Stand-in bus | Disposable live topics |
| --- | --- | --- |
| Four at once, four replicas up late, 1 request a pass | 10 runs of 10: 4 of 4 debated, nothing lost, four replicas served the first four turns | the same counts (turns of 8 s, a wait of 20 s) |
| The same, 10 requests a pass | 10 of 10: 2 of 4 failed open, 2 replies nobody took (1 dead-lettered, 1 unread), one replica served all four | the same counts |
| Four at once, one replica | 10 of 10: 2 of 4 failed open | not run |
| One at a time against four at once, 16 turns | lanes 1.00 against 2.30 at turns of 0.5 s | 186.6 s against 48.8 s at turns of 10 s: 3.8 times faster, both clean |
| 1,600 turns at four at once | 25 runs of 25 clean, no exception from the shared in-memory graph | not run |

The fleet's three debate subscriptions read the same before and after every live configuration.

**Decided (D1 to D9 of S260).** The harness lives under `scripts/` and ships in no image. The manager's
peer client gains one optional argument, the bus it publishes on, as its reply receiver can already be
supplied; nothing else in shipped code changes. A run is clean when every order was really debated, none
failed open, no reply went untaken, none answered another request, no turn was served twice and no
replica raised. Lanes are reported and not judged. The live transport makes its three topics from a
random run id, refuses a fleet topic's name, counts the fleet's subscriptions before and after, and
deletes what it made. Four timed tests hold the result on the stand-in bus, with the September setting
as the planted failure.

**Ruled out.** Scripts kept outside the repository: the September apparatus was lost twice
([DL-145](design-log.md)). A harness that runs only live: the builder has no network and CI could not
hold the result. Stand-in manager or debaters: they bypass the inbox and the consumer, where the replies
were lost. A process for each replica: it needs Postgres as the shared graph, so writes to the production
spine. A harness manager under another name: a debater admits `deliberator-manager` alone, and that list
is in `contracts/`, a fidelity decision path; the reply topic is made disposable through the settings'
suffix instead. Judging lanes: at a canned turn of a second the pickup below dominates.

**Found on the way. Nothing decided, nothing changed.**

- A reply taken by a sibling's receive call reaches its owner when the owner's own call returns: up to
  one second (`REPLY_RECEIVE_SLICE_SECONDS`), about half a second a turn at four at once. Against turns of
  40 to 230 seconds that is under 2 %.
- At ten a pass one turn of four started after its caller had given up. A request has no time to live
  (already in work-queue 113's row); the harness counts such turns.
- The first guided turn in a fresh process takes 2.4 seconds, the import of DSPy. A debater replica pays
  it once after each start.
- The fleet's reply subscription `deliberator-manager.reply` holds 7 dead-lettered messages (read
  2026-10-09 22:08 UTC). Not read further.

**Not shown.** Anything on the fleet: Postgres as the claim-check store, replicas scaling out, the
vendor's rate limit with several calls in flight. Step 2 of DL-277's plan, one paid proof at three at
once, stands and is the operator's call. The dial stays at 1.

---

## DL-278 - a build with a re-run job cannot be proven to the deploy record, and a tag the fleet has pulled is not pushed again - status: DECIDED (planner, 2026-10-08 22:50 AEDT); the reader's fix is work-queue 115

**What happened.** The `s259` build (run `37767377219`) pushed fifteen images and failed one job: the
scanner image's vulnerability scan could not download its database, so the image was never scanned or
smoke-tested. I re-ran that one job (`gh run rerun --failed`); it passed and the run read `success`, 15 of
15. The fleet was retagged to `s259` and verified. Then `scripts/record_deploy.py` refused: "GitHub build
evidence is required before recording a deploy".

**Measured.** `surfaces/dashboard/github_tag_builds.py` proves that a run published a tag by finding
`trading-agents-master:<tag>` in the run's log archive. GitHub's archive for a run is the latest attempt's.
Attempt 1's archive is 953 KB over 15 jobs and names the master image ten times. The latest is 56 KB, the
scanner job alone, with no mention. A read-only call of the same reader gave 0 qualifying builds for `s259`.

**Why the record could not be skipped.** `scripts/fidelity_export_helpers.py` takes a session's deployed
commit from the `DeployRecord` in force when its scan ran. With no record for this deploy every session
would be compared against `s257`'s commit, and the three law books S259 rewrote would make each one
unclean. The deploy existed to prevent exactly that.

**Decided.** A fresh build of the same commit in one attempt, under a new tag, `s259a` (run `37770503860`,
15 of 15; the reader finds it), and a second retag onto it, verified and recorded. `s259` was live from
11:09 UTC until that retag, with no record.

**Ruled out.** Re-running every job of the first run, or a fresh build under `s259`: either pushes fifteen
images again under a tag the fleet had already pulled, so what was verified would no longer be what runs.
Recording by assertion: the skill forbids it, and the record's worth is that it is not asserted. Leaving
the deploy unrecorded: above.

**Changed.** The deploy-fleet skill says to dispatch a fresh run when a job fails and never to re-run it.
The reader is unchanged; reading every attempt's archive is work-queue 115.

**Not decided.** Whether `s259a` is the right name. The convention suffixes a chore to the sprint it
follows; this is a second build of the same sprint. The `DeployRecord`'s commit is what is authoritative.

---

## DL-277 - parallel debates were built in September and left off because one replica took the whole queue; S256 removed that, measured at no cost - status: MEASURED (planner, 2026-10-08 19:33 AEDT); one clean fleet run at three at once on 2026-10-09 (amendment 1); **three at once is LIVE on the fleet since 2026-10-09 (amendment 2, operator)**; work-queue 113

**The question.** DL-274 lists three ways out of a night's capacity. The third, more than one debate at a
time, is said there to need peers that serve in parallel. Is that built?

**It is built, and switched off on purpose.** *[measured, read]* [S172](sprints/sprint-172-independent-debates-run-independently.md) gave the manager
`debate_concurrency`: a thread for each order, replies routed among the waits by correlation id.
`infra/deploy-agents.ps1` gives each debater as many replicas as the pack's
`DELIBERATOR_DEBATE_CONCURRENCY`. The pack says 1 ([DL-153](design-log.md)). At K=4 one fleet run lost
six replies and failed two of fifteen orders open ([DL-140](design-log.md)); a second run of the same
build was clean; both reached 1.5 to 1.8 lanes of a possible four ([DL-145](design-log.md)). The cause
was not found, and [S192](sprints/sprint-192-a-reply-that-arrives-late-is-still-an-answer.md), written to find it, is still a spec. DL-153 left the dial at 1 because
serial debates then fitted 21 orders into execution's wait. Today they fit about 7 (DL-274's amendment).

**Measured 2026-10-08, no LLM call.** The repo's own request consumer and `serve_once` on disposable
topics of the live namespace, four consumers on one subscription as four replicas would be, a handler
that sleeps five seconds as a turn would. Each configuration run twice, with the same result.

| The requests | Taking 10 a pass (the default before S256) | Taking 1 a pass (the default since S256) |
| --- | --- | --- |
| Eight already queued when the four consumers start | one consumer took all eight and served them in turn, three served none; the last began after 44 s; 0.8 lanes | two each; the last began after 6.9 s; 3.35 lanes |
| Four at a time, arriving at idle consumers, three waves | one each | one each |

So a debater that found requests waiting used to take up to ten of them and serve them one after another
while the other replicas idled. A request at the back waited several turns, longer than the manager's
wait, and its reply arrived for nobody: the orphaned replies and the fail-opens of DL-140. When requests
met idle replicas it did not happen: the clean run of DL-145. Fewer lanes than replicas fits both.
[S256](sprints/sprint-256-a-served-request-is-settled-when-it-is-taken.md) changed the number taken a pass from ten to one for another reason (a taken request is
settled at once, so nothing is gained by holding more), and that has been on the fleet since `s257`.

**Not shown.** That K above 1 is correct on the fleet today. Not measured here: the manager's reply
routing with real debates in flight, whether the debater apps scale to K replicas (never measured:
DL-145's watcher failed), and the vendor's rate limit with K calls in flight.

**Plan (planner). Nothing changes on the fleet without the operator's word.**

1. A harness that runs the production manager and the production peers over disposable topics with a
   canned model, and reports lanes, orphaned replies and fail-opens at K = 1 to 4, at no cost. Committed
   this time: DL-145 records that the apparatus was lost twice. The next sprint for Codex after S258.
2. Then one fleet proof at K=3, on a seeded run with execution and the portfolio manager held at zero.
   Its debates are paid, so it is the operator's call.
3. K=3 would take a night on `gpt-5.5` from about 7 debated buys to at most about 21; the largest night on
   record approved 18. The value lives in the tunables pack, a fidelity decision path, so until the count
   allows a pack edit it would be a live setting on three apps.

**Amendment 1 — step 2 is done: one fleet proof at three debates at once, clean (measured 2026-10-09
15:54–16:01 AEDT, 04:54–05:01 UTC; operator: *"yes, it can. go ahead"* to about $5.30).** Six synthetic
buys (`verify-2026-10-09-s260-k3-a`: GOOGL, TMO, TXN, CSCO, GOOG, UNP, one share each) seeded under
`sched-2026-10-08`'s real AnalystRun, on the fleet's own images (`s259a`). Live for the run only: the
manager's `DELIBERATOR_DEBATE_CONCURRENCY` 3, each debater app at three replicas, and a temporary window on
the master and the three deliberator apps. Execution and the portfolio manager stayed at 0 replicas.

| Read | Value |
| --- | --- |
| Orders really debated | **6 of 6**; 0 failed open; **0 orphaned replies** |
| Model calls | **30** (12, 12 and 6), all `gpt-5.5`, all ended on `stop`; **$3.72** |
| Replicas | 3 of each debater running at three samples; **7 activations** (the manager and three instances of each debater), credentials passed; **3 calls in flight at once** on each debater |
| Time | the record landed 6.9 minutes after the seed; model span 361.8 s for 819.3 s of model time: **2.26 lanes**, about 60 s an order against 188 to 231 s one at a time |
| Faults | 0 |
| The vendor's rate limit | not met at three calls in flight for each debater |

The slowest call took 62.3 s and the largest turn wrote 7,569 output tokens. The judge ruled `overturn` on
four and `revise` on two; the rulings are about orders priced at a placeholder $100.00 and are not evidence
for [DL-280](design-log.md).

**Torn down and restored.** `pg_teardown --prefix` deleted the PMRun, its DeliberationRun and 32 edges; the
AnalystRun has its one PM run again, no PM run awaits deliberation or execution, and the 30 `LLMCall` rows
stay as the record of the spend. The four apps' scale, env, image, resources, ingress and secret names
equal the snapshot taken before; execution and the portfolio manager were not touched. Scripts, snapshots
and outputs: OneDrive `trading-agents-data/k3-fleet-proof-2026-10-09/`.

**What it does and does not show.** The debater apps scale to three replicas and each activates; the
manager's reply routing holds with real debates in flight; nothing was lost. It is **one** run of two waves.
September's failure appeared in one run of two, so this does not prove absence; its named cause (ten
requests a pass) is gone and is held red by [S260](sprints/sprint-260-debates-at-once-lose-no-reply-and-the-repo-can-show-it.md)'s tests. Not measured: a night-sized batch (the
largest on record approved 18), and execution reading the record. **Step 3 is the operator's decision:**
three at once as a live setting on three apps (the pack is a fidelity decision path), or leave the dial at 1.

**Amendment 2 — step 3 is decided: three debates at once, as a live setting (operator, 2026-10-09 16:25
AEDT: *"three at once"*).** Set 2026-10-09 16:27 AEDT on three apps and nowhere else: `deliberator-manager`'s
`DELIBERATOR_DEBATE_CONCURRENCY` is 3 (was 1); `deliberator-proponent` and `deliberator-opponent` have
`maxReplicas` 3 and `desiredReplicas` 3 in the nightly window rule, whose hours are unchanged. Compared with
the morning's snapshot, those are the only differences on the three apps; the master, execution and the
portfolio manager differ in nothing. **The pack still says 1**, because the pack is a fidelity decision path
and an edit would restart the clean-session count: a full `up` puts 1 back on all three, and the pack edit is
owed once the count allows it. **Rollback:** the manager's value back to 1 and the two debaters back to one
replica. **F2, owed on the first scheduled night with more than one debated buy:** the record's
`real_debate_count` equals the approved buys, `failed_open_count` 0, `orphaned_reply_count` 0, three replicas
of each debater activated, and the record lands inside execution's 1,800 seconds. **Ruled out:** four at
once, never run on the fleet since September's failure; waiting for more fleet runs first, since a night
with more than about 7 debated buys places none today and the proof run cost $3.72 a time.

**Ruled out for now.** Turning the dial for tonight's run: six F2s are owed on it and K above 1 is
unproven on the fleet. A longer wait alone: the brief's last tick caps it near 3,000 seconds, about 12
buys. A verdict applied per order as it lands stays open: it is the half that degrades gracefully when a
night still does not fit.

---

## DL-276 - a law row's default and bounds are compared with the code; twelve rows state bounds the code does not enforce, and eight of them cannot be rewritten yet - status: DECIDED (planner, 2026-10-08 19:16 AEDT); BUILT and MERGED as [S258](sprints/sprint-258-a-law-rows-numbers-are-compared-with-the-code.md) `0.123.03` (2026-10-08); the eight rows rewritten as [S259](sprints/sprint-259-the-eight-excused-law-rows-state-the-codes-bounds.md) `0.123.04` and deployed `s259a` the same night; work-queue 114 closed

**The question.** DL-275 found that the parameter step of `make ci` compares a `PARAM` row's name and
its Tunable cell and nothing else. What should it compare, and what does it find when it does?

**Measured (2026-10-08, `main` `60a19e29`, a worktree with no `.env`; a prototype on no branch).** The
step covers 16 books and 235 rows that have a settings field. Value cells are written four ways (177 in
backticks, 45 in backticks and double quotes, 9 a dash for a secret, 4 the bare word `empty`), and all 235
agree with the code's default once each form is read. Bounds are written four ways: `≥` and `≤`, `>=` and
`<=`, `>` and `<`, and intervals such as `[0.0, 1.0]` and `(0, 1]`. 164 rows have a bound in code. 152
state the same bounds. **12 do not:** 8 state a different number or strictness, 3 state one side where the
code has two, 1 states none. Four are in the execution book (`slippage_bps`, `min_promotion_runs`,
`min_approval_rate`, `alpaca_timeout`), six in the portfolio manager's (`starting_cash`,
`max_position_pct`, `max_positions`, `cash_buffer_pct`, `min_order_quantity`, `price_lookback_days`), one
in the scanner's (`min_average_volume`) and one in the analyst's (`scaled_stop_atr_multiplier`). The
prototype exits 1 on today's books naming exactly the four execution rows, exits 0 once they are
rewritten, and exits 1 on each of six planted wrong rows, the first of them the row S257's builder
planted. Against the whole suite it fails exactly one existing test, which pins the number of warnings;
the gate self-test passes 31 of 31. Printing a law's `≥` raises `UnicodeEncodeError` on this machine when
stdout is redirected (`cp1252`), which is how `make ci` is always run.

**Correction of my amendment to DL-275.** I wrote there that 23 rows state a numeric bound, 41 bounds in
all, that all 41 equal the code's, and that a widened step would pass as the books stand. The script
behind it read one notation of the four. It reported no disagreement because it could not read the rows
that disagree. The Value half of that amendment stands.

**Decisions.**

- **D1.** The Value cell is compared with the field's default for every row with a settings field, by
  reading rules that cover every form in use. A cell that cannot be read is a failure, not a skip.
- **D2.** The Type cell's bounds are compared with the field's, in every notation in use. The set of
  bounds stated must be the set the field has, each number equal.
- **D3.** For the twelve rows the law follows the code. No settings file changes. The four execution
  rows are rewritten by S258.
- **D4.** The other eight are excused by a recorded list: a row's Type cell exactly as written today. An
  entry excuses a bounds disagreement only while the cell equals the record, and an entry that is no
  longer needed fails the gate. They are rewritten, and the entries deleted, at the first deploy that
  restarts the fidelity count or after [DL-237](design-log.md)'s verdict.
- **D5.** A failure names the row, what the law states and what the code has, and no line may raise on a
  console that cannot encode a law's symbols.
- **D6.** Work-queue 114 stays open until the eight rows are rewritten.

**Why eight rows wait.** The fidelity check calls a session clean only when no file differs under its
decision paths between the deployed commit and the replayed one, and it counts every file under
`agents/portfolio_manager/`, `agents/scanner/` and `agents/analyst/`, a law book included
(`scripts/replay_fidelity_git.py`). The count restarted on 2026-10-08 and needs four clean sessions and
ten judged recommendations. A row of text is not worth that.

**Ruled out.** Rewriting all twelve now (above). Teaching the fidelity check to ignore law books: it
narrows a rule fixed before its result was known. Changing the code's bounds to match the books: it
changes what a setting may be set to, on no evidence. Comparing only the bounds a row states: three rows
state one side of two. A warning that leaves the gate green: work-queue 33 removed a baseline of 57
divergences for that reason. A case in the gate self-test: its file is frozen at its size.

**Not measured.** Whether each code bound is the intended rail. The tunables' `why` texts do not say. A
rail that looks wrong is a drift-register row and its own decision, not part of this.

**Built as decided (2026-10-08 20:55 AEDT, S258 merged as `0.123.03`).** D1 to D5 were built with no
departure, and the planner's own count over the built reader gives the numbers above. Three limits of
the reader are accepted, and no row meets any of them today: a rail enforced by a validator function
is not seen; a Type cell that states the same side twice is read by its last statement; and two
numbers written with no space after the comma read as one grouped number, which fails against a field
that has bounds and would pass against a field that has none.

**Amendment (2026-10-08 21:35 AEDT): the eight rows are rewritten the same night, as
[S259](sprints/sprint-259-the-eight-excused-law-rows-state-the-codes-bounds.md).** D6 left them for
the first deploy that restarts the fidelity count. The operator asked what clearing them takes and
chose "tonight". The count's first session is `sched-2026-10-08`, which had not run: a session is
clean when no decision path differs between the deployed commit and the commit the replay runs from
(`scripts/replay_fidelity_git.py`, read whole), so a deploy before that run spends nothing, and the
rewritten books are part of the code the count starts on. **Ruled out.** Waiting for the next deploy
that restarts the count, or for the verdict: one to three weeks, and each night adds a session a later
rewrite would discard. Merging without deploying: the next retag, whatever it carried, would then
restart the count. Removing the excusing mechanism: its tests still prove it and the repository test
now holds the list empty, so an entry cannot arrive quietly. **Not decided.** Whether the code's
limits are the right ones. The books now state them (up to 500 positions, a cash buffer up to 0.95, a
single-name cap from 0); tightening one is a change to decision code and its own decision.

---

## DL-275 - S257's numeric PARAM proof belongs to its literal tests; the shared gate checks names and tunable declarations - status: MEASURED and DECIDED (builder, 2026-10-08); confirmed by the planner, the gap measured and filed as work-queue 114

**Found while planting guards.** S257 says the PARAM gate fails until the two numeric rows follow the
settings. With the implemented settings unchanged, reverting only the `max_tokens` row to default
8,192 and upper bound 8,192 made A1 fail, but `python scripts/check_param_law_sync.py` still exited 0.
The mutation was restored byte for byte. Evidence: `.tools/s257/guards.txt` from the initial run
(preserved as `.tools/s257/guards-initial.txt`), G07. Read `scripts/param_law_sync_sources.py`:
`ParamRow` stores the name and Tunable cell, not Value or Type; `scripts/param_law_sync.py` compares
name presence and the tunable family, with separate default/envelope warnings.

**Decision.** Keep the gate unchanged. A1 and A4 pin the two complete numeric row prefixes, and their
plants must fail on old values; B2 still runs the shared checker and plants a tunable-declaration
mismatch that the checker actually enforces. Record the spec correction in Return notes. This changes
no guarantee and needs no law clause or contract change.

**Ruled out.** Widening the repository-wide checker to compare numeric defaults and bounds would
change proof for every agent, discover unrelated old-row divergences and exceed S257's settings-only
scope. Treating its exit 0 as numeric proof would hide the observed survivor. The scoped literal tests
already supply that proof without changing a production decision.

**Amendment (planner, 2026-10-08 16:27 AEDT): confirmed, and the gap is measured.** The same plant
on the built tree: with the cap's law row back at 8,192, `scripts/check_param_law_sync.py` exits 0. The
claim in S257's spec was the planner's, and it was never run in its failing direction: the prototype ran
the step only with the rows already changed. Then every cell the step skips was read on `main`
(`7309b858`), in all 16 law books it covers. Of 235 `PARAM` rows that have a settings field, the Value
cell equals the code's default in 220; the other 15 are written in a form a number comparison cannot read
(four `Decimal`s, one `Decimal(...)` literal, one date, nine secrets shown as a dash) and each equals the
code when read by eye. 23 rows state a numeric bound in the Type cell, 41 bounds in all, and all 41 equal
the code's. So the second reason above for leaving the step alone, that widening it would find old
disagreements, is not borne out: there is none today, and a widened step would pass as the books stand.
The first reason holds: it is a change to a shared gate and was not S257's to make. Filed as work-queue
114.

🩹 **Corrected the same evening (DL-276).** The count of bounds above read one notation of the four the
books use. Read in all of them, twelve rows state bounds the code does not enforce. The conclusion that a
widened step would pass as the books stand is withdrawn; the builder's second reason was right.

---

## DL-274 - the output cap, the manager's wait and execution's grace are one chain; the cap goes to 16,384, and a night with more debated buys than fit in the grace places none of them - status: DECIDED for the cap and the wait (planner, 2026-10-08 14:09 AEDT); BUILT and MERGED as [S257](sprints/sprint-257-a-debaters-turn-may-write-16384-output-tokens.md) `0.123.02` (`b0831f64`, 2026-10-08), F1a and F1b passed, deployed `s257` 2026-10-08 with the manager's wait at 240 seconds, work-queue 111; MEASURED and open for the grace (work-queue 113)

**The question.** Work-queue 111 offered two fixes for the output cap on `gpt-5.5`: raise the cap, or lower
the effort. Sizing the first one means asking what a longer turn meets next. DL-271 answered for the
message lock. This entry answers for the two bounds after it.

**Measured, 2026-10-08, no LLM call.**

- **A turn's time follows its output.** Over the 49 typed first turns kept from EXP-020 and EXP-021
  (`gpt-5.5`, effort `high`) the speed is 86 to 117 output tokens a second, median 109. The defender's
  turns: median 6,726 tokens, largest 11,556, 5 of 25 over 8,192. The challenger's: largest 7,320, none
  over. So a turn that used a whole cap would take up to 96 seconds at 8,192, 143 at 12,288 and 191 at
  16,384.
- **What Anthropic's client accepts.** Version 0.120.2 refuses a non-streaming request above 21,333
  output tokens, for every model (measured offline: 21,333 allowed, 21,334 refused). The adapter does not
  stream. A bound above that would let a setting fail every Opus turn.
- **Where the numbers live.** No app sets the cap, so the code's default is the fleet's. The wait (120
  seconds) comes from the tunables pack, and the pack is fidelity decision code: an edit starts the count
  again.
- **A prototype of the two bounds and the default:** on a prototype of the two bounds and the default, the parameter step passes and exactly two existing tests fail, both because they pin the old cap (4,301 pass).
- **A debated order, in seconds of model time.** Opus with guided turns, since 2026-09-30: median 146,
  largest 160 (9 orders in 4 runs). `gpt-5.5`: 188, one order, S254's F1. The record lands about 60
  seconds later than the model time alone (49 to 69 over the four runs).

**Decided, for the cap and the wait (S257).**

| # | Decision | Ruled out, and why |
| --- | --- | --- |
| D1 | The cap's default and upper bound go to 16,384 | **Lowering the effort to `medium`:** it changes what the debaters write to work around a number, and needs a paid measurement. **12,288:** 6 % above the largest turn already measured. **A higher bound or none:** Anthropic's client refuses it. **Raising the bound and leaving the default:** the fleet reads the default |
| D2 | The reason for the ceiling is a named constant in the Anthropic adapter, held by a test | **Calling the vendor's client in a test:** it is installed only in the `llm` extra, not where CI runs |
| D3 | The wait's upper bound goes to 300 seconds | **Leaving it at 120:** a turn at the new cap can take 191 seconds, so the failure would move from the cap to the wait |
| D4 | The fleet's wait goes to 240 seconds on the manager's live app at the deploy, on the operator's word. The pack is not edited | **Editing the pack:** it starts the fidelity count again, and a full `up` would also undo the week's vendor switch (DL-265) |

**Found: the night has a capacity, and past it no buy is placed (work-queue 113).** *[the whole mechanism
read]* The manager debates one order at a time and writes one `DeliberationRun` for the whole batch, at
the end. Execution holds a buy-carrying run for 1,800 seconds from the PM run. Its posture is `binding`
(the default; no app sets it), so when the grace ends with no record, every buy is dropped and only the
sells go. At the measured times that is about **11 debated buys a night on Opus and 9 on `gpt-5.5`**
(1,740 seconds over 146 and over 188; the second from one order). The typed turn of step 3 would make it
about 7 on `gpt-5.5`, and the loop of step 5 adds calls to each order. *[measured, the live graph]* Of 90
PM runs, 15 approved nine or more buys: five nights (2026-08-08, -10, -14, -19 and 2026-09-28, with 18,
18, 9, 9 and 12) and four undated runs of 15. The last 25 runs approved 0 to 4, except the 12. The 12 of
2026-09-28 were debated on the shorter turns of the time; the same night today would end with none
placed, on either vendor. The three grace faults on record are from August, under a 900-second grace.

**Ways out of the capacity, not decided.**

- **A longer grace.** The bound allows 3,600 seconds and the agents' scale window runs to 00:30 UTC, so
  there is room. The value lives in the tunables pack (the fidelity count again), and the daily brief's
  last tick is at 23:50 UTC: a night that used the whole hour would end after it. Not measured.
- **A verdict applied per order as it lands**, so a night that runs out of time keeps the reviews it has.
- **More than one debate at a time.** Raising the manager's fan-out does nothing while each peer serves
  one turn at a time; it needs peers that serve in parallel. After S256 a request is settled when taken,
  so two replicas on one subscription cannot serve the same turn.

**Also moved here from work-queue 111:** a request message has no time to live (DL-272). A request whose
caller stopped waiting is served when a peer next takes it, and it is served ahead of the live ones.

**Not measured.** A production turn on `gpt-5.5` with S255's longer packet: the first debated buy will show
it. Whether a larger cap changes what Opus writes: its largest turn is 4,846 tokens, and the account is
empty until 2026-10-11.

**Amendment (planner, 2026-10-08 18:31 AEDT): F1b, one real debate at the new cap.** The merged code
on `gpt-5.5` at `high` effort, the cap at 16,384 and the wait at 240 seconds, on GILD's recorded packet of
`sched-2026-10-05` (the packet S254's F1 used; it predates S255's three lines). The defender's first turn
wrote 10,658 output tokens in 93.8 seconds, 114 tokens a second. The cap of 8,192 would have cut it and
failed the order open, and it ran longer than the 60-second lock that S256 stopped depending on. The other
calls: the challenger's 5,630 tokens in 52.8 s, the defender's 4,828 in 42.0 s, the challenger's 3,714 in
34.8 s, the judge's 574 in 7.1 s. Every call ended on `stop`; the ruling was `revise`, as on the night.
The order took 231 seconds from the first request to the ruling, against 188 seconds on 2026-10-07 with
the same packet. That is the number work-queue 113 divides execution's 1,800-second wait by: 7 debated
buys a night on this vendor where 188 seconds gave 9. One measurement. $0.88.

**Amendment (planner, 2026-10-08 18:52 AEDT): D4 applied.** The fleet was retagged to `s257` between
07:35 and 07:42 UTC, and `DELIBERATOR_REQUEST_TIMEOUT_SECONDS` went from 120 to 240 on
`deliberator-manager` between 07:44 and 07:45 UTC: the one field that differs between the app's two
snapshots. The manager activated on that revision; the code before S257 refuses a value above 120 at
start-up. The value is live only. The tunables pack still says 120, so a full `up` puts 120 back, and a
rollback to an older image must set 120 first. The two debaters keep 120: the setting bounds the manager's
wait for a served reply.

---

## DL-272 - a served request is settled when it is taken, one at a time, and a second completion is its own ledger row - status: DECIDED (planner, 2026-10-08 13:11 AEDT); BUILT and MERGED as [S256](sprints/sprint-256-a-served-request-is-settled-when-it-is-taken.md) `0.123.01` (`b3f1ee1f`, 2026-10-08), F1 passed, deployed `s257` 2026-10-08; work-queue 112

**The question.** DL-271 measured the defect and listed four parts of a fix without
choosing between them: an explicit lock, a renewal or an early settlement, a caught lost lock, a visible
repeat. This entry chooses.

**Measured, 2026-10-08, no LLM call.**

- **The whole mechanism, read.** `serve_once` polls, runs the handler, then replies; `reply` publishes and
  only then completes the message. One poll takes up to ten requests, all locked from the moment they are
  received and handled one after another, so the third has waited two turns before it starts. A reply that
  cannot be published abandons the request, which is then delivered and served again. `write_llm_call`
  returns the first row for a key that exists.
- **A reproduction with no network** (the Appendix of the spec) prints all five of these on `main`.
- **A prototype of the decisions below, on the live namespace:** disposable topics, the default one-minute
  lock, a 70-second handler. The request is served once, with no error and one reply, and a second
  consumer is given nothing. `main`'s code on the same check raised `MessageLockLostError` and served the
  request twice (DL-271).
- **The prototype against the whole suite:** five existing tests fail and 4,298 pass. The five assert the
  behaviour being removed.
- **Who is served.** Only the deliberator's manager sends to a request topic, to its two peers. The
  supervisor, the operator, the researcher and the forecaster run the same loop and receive nothing.
- **The record.** 4 of 1,130 debater calls took more than 60 seconds, all on 2026-08-19 on `gpt-5.5`. The
  manager has recorded no reply that nobody was waiting for, in 90 runs.

**Decided.**

| # | Decision | Ruled out, and why |
| --- | --- | --- |
| D1 | A served request is settled when it is taken, before its handler runs. `reply` only publishes | **Renewing the lock** (the vendor's `AutoLockRenewer`): a second thread on a synchronous receiver's connection, provable only on the live service, and it keeps the redelivery that makes the second paid call. **An explicit five-minute lock alone:** the vendor's maximum, not applied to a subscription that exists, and a batch still ages under it. **Catching the lost lock:** the request is still served again |
| D2 | One request a pass: `receive_max_messages` defaults to 1 | **Settling each request just before its own handler:** a third method on the consumer protocol, for a batch that buys nothing when requests are handled in turn. **Deleting the tunable:** more surface for no gain |
| D3 | A reply that cannot be published is a `Fault`, and the loop serves the next request. The two debater peers pass a graph sink; the other served agents keep the in-memory one | **Letting the error end the process:** the next request waits for a restart. **Swallowing it, as today:** silent |
| D4 | A completion under a ledger key that exists is its own row, under that key plus `:repeat-N`. No new property | **One row with a repeat count and summed tokens:** rewrites an audit row and loses the second call's hash and latency. **Keying by the bus message's id:** changes every key and reader. **A `repeat_of` property:** new graph vocabulary for what the key already says |
| D5 | Nothing changes on any subscription. The five-minute lock set by hand on 2026-10-08 stays | **Setting it back:** it costs nothing where it is, and it protects the older code after a rollback |
| D6 | `OPR-IDM-02` is rewritten to what the code does: duplicate commands share one `CommandAudit` and one `Intent`, and each model call is its own `LLMCall` row | **Leaving it:** the clause said two of each, the code has always written one, and the test that proves `OPR-IDM-03` counted one `LLMCall` for two paid calls |

**What D1 gives up.** The bus no longer serves a turn again after its peer stopped mid-call or its reply
could not be published. That order fails open when the manager's wait ends, as a timed-out turn does
today. With the five-minute lock on the live subscriptions a redelivery already arrives after the
manager's 120-second wait, so the fleet as it stands gives up nothing. *[ASSUMED, from the vendor's
documentation, not measured]* A locked message is not freed when its receiver disconnects; nothing above
depends on it.

**Found on the way, not fixed here.** A request message has no time to live: the manager sets none and the
subscriptions keep a message forever. A request whose caller has stopped waiting is served whenever a peer
next takes it, a paid call with no reader. No instance is recorded. It is noted on work-queue 111, which
changes the wait.

**Not decided.** Whether the other four served agents should record their failed replies: nothing sends to
them today.

---

## DL-271 - a debater turn slower than the 60-second message lock crashes its peer and is served again, and the ledger cannot show the second call - status: MEASURED (planner, 2026-10-07 21:58 AEDT); the five-minute lock APPLIED live 2026-10-08 08:52 AEDT; the fix is work-queue 112

**How it was found.** Sizing work-queue 111 (the output cap on `gpt-5.5`), the planner looked at what a
longer turn meets on its way back. A served peer receives its request under a message lock, runs the model
call, publishes the reply, and only then completes the message.

**Measured, no LLM call.**

- The two request subscriptions the debaters serve from, `deliberator-proponent.requests` and
  `deliberator-opponent.requests`, have a lock of **one minute**. Nothing sets it: `create_subscription` is
  called with the vendor's default. No code renews a lock, and no code catches a lost one.
- The repo's own receiver and `serve_once`, on disposable topics on the live namespace with that default
  lock and a handler that takes 70 seconds: the reply is published, then `serve_once` raises
  `MessageLockLostError`. `serve_loop` catches nothing, so in a container the peer's process ends. A
  second consumer, as a restarted process would be, receives the same request again: the handler runs a
  **second** time and a second reply is published. The topics were deleted afterwards.
- The same check with a five-minute lock: served once, no error, one reply, nothing redelivered.
- The ledger keys a call by agent and correlation id and returns the first record when the key exists
  (`kernel/llm_ledger.py`). So a turn served twice is one `LLMCall`: the second, paid call is not recorded.
  The planner's first reading, *"1,387 calls, no id served twice"*, therefore proved nothing and is
  withdrawn.
- How long turns take: on Opus the debaters' calls average 41 to 51 seconds. On `gpt-5.5` the defender's
  production turn took 58.1 and 59.8 seconds in the one debate measured, and its typed turn averages 66
  seconds with a slowest of 118. In the live records 4 served turns passed 60 seconds, all on 2026-08-19,
  all `gpt-5.5`.

**What it means.** On Opus the lock is rarely reached. On `gpt-5.5` about half of the defender's turns
reach it. Each one that does: the debate gets its reply, the peer then dies, restarts and makes the same
call again, unrecorded; its second reply is an orphan; and the manager's next request to that peer waits
behind the repeat, against a 120-second wait, so that order can fail open. Raising the output cap
(work-queue 111) makes turns longer, so this comes first.

**Options.**

- **Live, now:** set the lock of the two request subscriptions to five minutes, the vendor's maximum. One
  setting on each, reversible, measured above to remove the failure for any turn under five minutes. It
  changes production infrastructure, so it is the operator's to approve.
- **The fix (work-queue 112):** subscriptions are created with an explicit lock; a served peer renews its
  lock while the handler runs, or settles the message before a long handler and relies on the claim check;
  a lost lock is caught and recorded as a fault instead of ending the process; and the ledger records a
  repeat instead of hiding it. Which of these, and in what order, is for the sprint's spec.

**Applied live, 2026-10-08 08:52 AEDT (21:52 UTC, 38 minutes before the scheduled run).** The operator, asked whether to apply it: *"not sure. make decision"*. The planner applied it: the failure and the remedy were both measured, the change is one setting on each of two subscriptions, and it is undone by setting it back. `lockDuration` is `PT5M` on `deliberator-proponent.requests` and `deliberator-opponent.requests` (subscription `agent`). Read before and after: of each subscription's 24 fields, two differ, `lockDuration` and `updatedAt`. The three debater apps were at 0 replicas and both subscriptions held 0 messages. Live only: no code, no image and no deploy record; a subscription created again would have the default again. To undo: `az servicebus topic subscription update -g trading-agents --namespace-name trading-agents-bus --topic-name <topic> -n agent --lock-duration PT1M`. Snapshots are in OneDrive `trading-agents-data/wq112-2026-10-07/`.

**Not taken.** Lowering the model's effort so that turns finish sooner: it changes what the debaters write,
to work around a transport setting. Catching the error alone: the turn would still be served twice.

---

## DL-270 - S255's frozen sentence includes normalized pillar metrics in its 0-100 claim - status: STOP (builder, 2026-10-07 17:49 AEDT)

**Constraint found while pinning the text, no network or LLM call.** The Appendix's first line says
"inside quant_metrics each key ending in _score, and each fundamental sub-score, is a 0-100 band
score in which 50 is neutral". The analyst's [scoring code](../agents/analyst/domain/scoring.py)
also writes its normalized `technical_score`, `fundamental_score` and `sentiment_score` into
`metrics`, and the recommendation retains them as `quant_metrics`.

**Measured on the planner's TGT fixture:** `fundamental_score=0.5125`,
`sentiment_score=0.4943820224719101`, `technical_score=0.5228571428571429`; each equals its normalized
recommendation pillar. The analyst's neutral band of 50 is divided by 100 to produce the neutral
pillar of 0.50. The sentence's universal claim cannot be pinned to that code under `DLIB-NEV-09`.
The Appendix still prints 9/9 equal blocks and 9/9 reproduced records; A1's prototype renders
9 of 9 orders equal. Numerical parity does not prove this sentence's units.

**Decision under the handover's explicit stop rule:** stop further implementation, law amendments,
guard plants and CI; retain status SPEC and record the partial prototype. `DRIFT-103` names the
defect. The planner must resolve the frozen wording and its experimental status before the build
can resume. No new text has been substituted.

**Corrected, 20:35 AEDT (planner).** The defect was the planner's: the sentence was written for EXP-019's arm B
and carried into the spec as frozen text without being checked against the keys. Measured over 1,765
recorded recommendations: 20 distinct keys end in `_score`, and exactly four are on a 0-1 scale
(`technical_score`, `fundamental_score`, `sentiment_score`, `composite_score`; the builder named three, the
composite is the fourth). The first line gains one clause that excepts them. The second and third lines
are unchanged. *Not taken:* removing the scale claim altogether, because the model needs it to read the
sub-scores; and leaving the line as measured, because it is false. The corrected line is not the line
the two experiments measured: measuring it again before the merge is the operator's decision. The stop
rule is narrowed to a sentence that is false in the code.

**Roads not taken.** Do not exclude the pillar keys from `quant_metrics`: that would change an
existing packet line and stored evidence outside scope. Do not rescale them: that would change
scores. Do not silently narrow the pin to indicator sub-scores: the sentence says every key.
Do not reword the three lines: EXP-019's text is frozen and the sprint expressly forbids it.

---

## DL-269 - the analyst and the provider record the constants they used, and the packet states the score arithmetic only when it reproduces the record - status: DECIDED (planner, 2026-10-07 18:19 AEDT); SPEC as [S255](sprints/sprint-255-the-packet-states-the-score-arithmetic.md), work-queue 107

**The question.** Step 2 of DL-264 amendment 5 puts the score arithmetic in the packet. EXP-019's arm B is
that text. How does production print it?

**Measured, no LLM call.** The weights, the floor and the span are the analyst's tunables, and the VIX
thresholds are the provider's. No contract field and no run record carries any of them, and an agent may
not import another. Built from the recorded recommendations, the lines equal arm B's for 9 of 9 orders. The
stated rule reproduces the recorded confidence and `technical_score` for 1,765 of 1,765 recommendations that
carry quant metrics (largest difference 1.1e-16). EXP-019's nine orders all have three pillars and a
relative-strength score. The analyst's code has branches they do not exercise: no `rs_score` (946 of 1,765,
none since 2026-09-04), an absent pillar (33), and a fourth pillar that a setting can switch on (0).

**Decided.**

- **D1.** The analyst records on each recommendation the seven constants it used and the names of the
  sub-scores it averaged into the technical and the fundamental score (`Recommendation.score_arithmetic`).
- **D2.** The provider records on the regime context the four VIX thresholds its label was selected with.
- **D3.** The deliberator ends the packet with arm B's three lines, built from those two records.
- **D4.** The lines are printed only when the stated rule reproduces this order's recorded confidence.
  Otherwise one line says why they are withheld. The branches the experiment did not measure are withheld,
  not stated. A record that predates the fields adds no line, so a rebuilt old packet is unchanged.
- **D5.** "Reproduces" is within 1e-9 on the confidence and on `technical_score`.
- **D6.** Both fields are optional. A reader on older code ignores a field it does not know (measured).
- **D7.** The new module joins the deliberator's recipe digest.

**Rejected.**

- *The weights and the sub-score lists hard-coded in the deliberator*, as the experiment's script has them.
  A deploy that changes a weight would make the packet state a false rule, and a new indicator would fall
  out of a list kept in another agent.
- *The weights as extra `quant_metrics` entries.* It changes a line the model already reads.
- *The regime line without its thresholds.* It is not the text that was measured.
- *A rule stated for the unmeasured branches now.* It would be text no experiment has read.
- *All of step 2 as one sprint.* The withheld facts (work-queue 98) need their inventory re-measured and
  their definitions written; the risk figures are not measured at all. Each is its own sprint.

**The gate.** A change to the evidence a model reads is within ADR-0010. The merge waits for EXP-019's
verdict (operator, 2026-10-07). The build needs no model call, so it does not wait.

---

## DL-268 - DSPy in the dev group opens a second route to `diskcache`, so the audit's premise covers it - status: DECIDED and built (planner, 2026-10-07 15:51 AEDT), on S254's branch

**What D2 changed.** DL-266's decision D2 puts `dspy` in the `dev` group so that CI can run the tests
that execute it. From that commit `diskcache` is reachable through the group as well as through the
`optimizer` extra. The acceptance's premise (DL-184, DL-199) named only the extra.

**Measured.** All 15 tracked Dockerfiles pass `--no-dev` on their one `uv sync` line. Nothing checked
it. A Dockerfile that dropped the flag would have installed DSPy, LiteLLM and `diskcache`, and the gate
would still have printed the acceptance as holding.

**Decision.** `AcceptedAdvisory` gains `also_in_dev_group`, set on the `diskcache` entry. A sync command
that names the extra, or that does not pass `--no-dev`, must leave the package out by name. Otherwise
the acceptance is void and the Dockerfile is named. The accepted note in the gate's output says so.
Test B4 also asserts `--no-dev` on every tracked Dockerfile. Watched to fail: the rule change turned two
of the builder's B5 cases red, because their second Dockerfile was a bare `uv sync`; the cases were then
corrected, and four voiding cases were added.

**Rejected.**

- *Keep `dev` free of DSPy and have CI sync with `--extra optimizer`.* The premise would stay true as
  written. But a bare `uv sync` in any worktree would remove DSPy and the suite would fail on import,
  and the workflow and the `Makefile` would each have to name the extra.
- *Leave the rule alone because every Dockerfile passes `--no-dev` today.* That is the state DL-199 was
  written against: a premise that holds and that nobody re-measures.

---

## DL-267 - S254 removal command matches its own specification - status: CORRECTED (planner, 2026-10-07 14:31 AEDT); found and recorded by the builder; the build resumes

**Measured in `../ta-s254`, no `.env`, no network.** Both unmodified S254 Appendix runs give 132/132 identical outcomes and single vendor calls at installed DSPy 3.4.0, with zero disk-cache files and zero global history; A1 is red before implementation. Main's behavior is frozen in `tests/fixtures/guided_turn_main_records.json`.

**Constraint.** S254 checklist 8 requires an unqualified `git grep` for the retired helper/prefix identifiers to be empty. The sprint document itself, DL-252 and the historical S246 handover contain those identifiers: the command returned 28 lines, exit 0, including its own checklist. Runtime source removals cannot satisfy it.

**Roads not taken.** Deleting historical records or rewriting the handed-over requirement is outside scope. Silently narrowing the grep would claim a different proof. The handover explicitly requires a stop if the spec is wrong, so implementation is not done and S254 remains SPEC.

**Proposed correction, not applied:** scope the removal grep to `kernel agents scripts tests`. The planner must correct the handover before the build resumes; D1-D7 are unchanged.

**Corrected, 14:31 AEDT (planner).** The defect was the spec's: the planner wrote the removal command without
running it on the tree. Checklist item 8 is now scoped to `kernel contracts agents orchestration surfaces scripts tests`. Three more
wordings that a literal reading could trip on were fixed in the same pass: item 9 (the golden's one changed
value), test B3 (the fourteen things it imports), and the stop rule, under which a wrong command with a plain
intent is corrected and recorded, not stopped on. The first pass stands: the law reading, the two Appendix
outputs, `main`'s frozen records and A1's red run.

---

## DL-266 - DSPy runs at run time: the offline placement is reversed, and the first build changes no prompt - status: DECIDED (operator, 2026-10-07 12:05 AEDT; [ADR-0032](decisions/0032-dspy-runs-the-llm-roles-at-run-time.md)); first build SPEC as [S254](sprints/sprint-254-each-debater-turn-is-run-by-dspy-and-the-prompt-does-not-change.md), work-queue 110

**The direction.** The operator, on reading that the runtime is DSPy-free by design: *"May have been an
experiment, i do not know but from the very beginning i intended it to be an active participant. Revert
this decision and let's put dspy back where it belongs."*

**How the offline placement came about** (read from the record, 2026-10-07). No step was the operator's
decision about where DSPy runs.

1. **2026-06-20, ADR-0010.** DSPy adopted, with optimisation *"offline, behind a `PromptOptimizer`
   port"*. The reason given was that the evaluation gate must not depend on the tool.
2. **2026-07-02 (`33eb1cd5`).** `dspy` landed in an optional `optimizer` extra that no Dockerfile
   installs.
3. **2026-09-20, DL-184.** A new advisory against `diskcache`, which arrives only through `dspy`, was
   accepted by the planner on the premise that no container installs it.
4. **2026-09-30, DL-250 and S246 (DL-252).** The operator asked for the guided chain of thought to be
   recorded. DL-250 left the placement open between (a) DSPy in the image and (b) DSPy offline with a
   parity-tested runtime parser. The S246 spec chose (b) for three reasons: the advisory, LiteLLM on
   the live call path, and a DSPy upgrade silently changing a live prompt.

**The operator's question the same hour:** *"there was a security issue with dspy. maybe decision to
pause was because of it?"* Partly. The offline placement is three months older than the advisory. The
advisory then became the first of the three reasons in step 4. It is against `diskcache`, not DSPy's
own code, and it is still unfixed: 5.6.3, the affected release, is the latest on PyPI today.

**Measured before deciding how** *[2026-10-07; DSPy 3.4.0, the lock's version; no LLM call, no
network; `main` at `02e4f865`]*. A guided turn was run by `dspy.ChainOfThought` through an engine that
wraps our own `LLMClient`, and compared with `main`'s `guided_turn`. The script is in S254's Appendix
and runs in a worktree with no `.env`.

| What | Measured |
| --- | --- |
| The new turn against `main`'s, over both roles × 3 user cases × (17 parse cases, 2 blank completions, a stopped call, a transport error, a timeout) | **132 of 132** give the same `DebateTurnRecord` or raise the same exception |
| What the vendor client receives | 132 of 132: exactly one call, with `main`'s system and user text |
| The same with `litellm` and `diskcache` unimportable | 132 of 132; neither is loaded even when importable |
| Files written to DSPy's cache directory, disk cache off | 0 |
| Calls DSPy keeps in memory with `disable_history=True` | 0 |
| A failure of our client | arrives as `LMUnexpectedError` with our exception as `__cause__`; the client is called once |
| A reasoning with a trailing comma | DSPy's own parse repairs it; `parse_guided_turn` refuses it (DL-252 D6) |
| Four plain threads sharing one program, each in its own `dspy.context` | 4 of 4 correct |
| Loading DSPy beside the deliberator (planner's Windows machine) | import + 0.9 to 1.4 s; 58 → 83 MB at import, about 120 MB after a turn; first turn + 2.3 s once, later turns + 7 ms. The container has 1.0 Gi |
| Packages the `optimizer` extra adds to the deliberator image's 56 | 41 |
| Packages `uv.lock` reaches only through LiteLLM or `diskcache` | 33, of which **8 are loaded by DSPy anyway** (`attrs`, `jsonschema`, `jsonschema-specifications`, `referencing`, `rpds-py`, `pygments`, `pyyaml`, `rich`) |
| `uv sync --no-install-package` in the Dockerfiles' `uv==0.4.29` | present |
| CI's environment | no DSPy: `uv sync` with no extra |

**Measured again at 12:24 AEDT, after the spec, with the two packages not installed at all.** The rows above
made them unimportable inside an environment that had them. In a fresh environment holding the deliberator
image's package set less `litellm` and `diskcache` (96 requirement lines from the lock, installed without
dependency resolution), the same script gives 132 of 132, and the deliberator's entrypoint imports beside
DSPy. *[not measured]* The Linux image itself: the local Docker daemon did not answer, so the first proof
of the built image is the build workflow's entrypoint smoke after the merge.

So the three reasons of 2026-09-30 are each met with DSPy in the image: the image leaves `diskcache`
out, the call goes through our client and never through LiteLLM, and the golden pins the wire text.

**The planner's decisions under the operator's direction** (delegated technical decisions; S254 builds
D1 and D3 to D7, the planner does D2 at merge).

- **D1 — the engine and the program live in `kernel/`**, in modules `kernel/__init__.py` never
  imports. *Rejected:* `agents/deliberator/`, because the judge and later roles would need them moved.
- **D2 — `dspy` goes in the `dev` group, so CI has it, and stays in the `optimizer` extra the one
  Dockerfile names.** *Rejected:* a base dependency (fourteen images would carry a library they never
  run); a renamed extra (churn in every recorded command for no behaviour).
- **D3 — strict JSON is kept: a `ChatAdapter` subclass, JSON fallback off, whose `parse` is
  `parse_guided_turn`.** *Rejected for this sprint:* DSPy's own parse. It repairs JSON, and
  `DLIB-OUT-06` records the reasoning *"exactly as the model wrote it"*. Whether to accept a repair
  and record that it happened is a later decision.
- **D4 — the image leaves out exactly `diskcache` and `litellm`.** *Rejected:* the extra whole
  (against DL-184); a list computed from the lock (8 of its 33 are loaded, so `import dspy` would
  break); a list of what one probe never loaded (not proof). The unused remainder is a later chore.
- **D5 — the caller sees the client's own exception.** The one function that runs a program re-raises
  `LMUnexpectedError.__cause__`, and a blank completion raises `empty_debate_turn` inside the engine.
  *Rejected:* letting DSPy's wrapper reach `fault_boundary`, which would name DSPy's class as the
  fail-open reason.
- **D6 — the prompt-recipe digest covers the installed DSPy version.** *Rejected:* hashing DSPy's
  source tree.
- **D7 — DSPy is imported and the programs built when the agent module is imported; each turn builds
  its own `dspy.LM` around its own client (`cache=False`, `num_retries=0`) and enters `dspy.context`
  with the history off in the serving thread.** *Rejected:* a lazy import, which lets a broken image
  start, activate and fail its first debate at night.

**What the first build is, and is not.** S254 changes who renders and who calls. The model reads the
same bytes and the graph records the same fields, and that is its proof. The judge, `dspy.History`,
`dspy.Refine`, typed weights (work-queue 107) and a loaded optimised program each follow as their own
change; a changed prompt still passes ADR-0010's gate.

**The operator's prototype, read against this.** The operator, the same hour: *"there is a prototype of
code suggested to me. Can you take it into consideration"*. The only prototype on file is
[R010](research/debate-pipeline-prototype/INDEX.md), so this reading is of that one. Its shape is three
callable roles, each returning typed JSON, composed by a plain loop in which the judge's directives feed
the next round. That is the shape of a DSPy program: three predictors and a `forward()`. With DSPy in
the runtime the same three predictors serve twice. In production each runs in its own container and the
manager's `_debate` is the loop, as today. Offline they compose into one `dspy.Module` whose `forward()`
is that loop, which is what `Evaluate` and GEPA run. So R010 sets the order of work after S254: the
judge's ruling becomes typed and carries directives, then a later-round turn takes the other side's
points and those directives as a typed input and must answer them (DL-264, goals a and b). What R010's
reading ruled out stays ruled out: a model that writes the plan, a judge inside the loop it rules on,
and risk figures computed by a model.

**Not decided.** Whether a repaired reasoning is accepted. When the operator agent's prompts move.
Whether LiteLLM's unused dependencies are trimmed from the image.

**The planner's miss.** DL-250 asked the placement question and S246's spec answered it inside a
"road not taken" paragraph. It reversed nothing the operator had said, but it settled something the
operator cared about without putting it to them. A choice about where a framework the operator named
runs is a direction, not a build detail.

---

## DL-265 - the Anthropic account is empty until Sunday 2026-10-11, so the debate runs on OpenAI for the week; the switch took five live changes where it should take one - status: DONE live (operator, 2026-10-06); the one-switch fix is work-queue 109

🔁 **2026-10-07 17:18 AEDT, a second measured debate (S254's F1).** The same GILD packet through the merged code, `gpt-5.5`, the fleet's settings:
**$0.79** against $0.66 the day before, so a debated buy costs $0.66 to $0.79 and three a night about $2.40. All of the
difference is output: 22,195 output tokens. **Discovered constraint:** the defender's two turns wrote 6,363 and 7,738
output tokens against a cap of 8,192, and on this vendor the model's reasoning tokens count against the cap. A turn over
it stops with `length` and fails its order open. Opus peaked near 3,000. The cap is bounded at 8,192 in the settings, so
raising it is a code change: work-queue 111. *Not taken:* lowering the effort to `medium` live tonight. It would change
what the debaters write on a vendor whose rulings are already not pooled with Opus's, on one observation.

🔁 **2026-10-07 12:20 AEDT (operator): *"Keep it on OpenAi whilst we are plumbing."*** The debate stays on
`gpt-5.5` while the DSPy runtime and the debate workflow are built (ADR-0032; DL-264 amendments 5 and 6), not
only until the top-up of 2026-10-11. The restore steps below are kept for the day the operator calls for
them, and are not run before. The live-only state therefore lasts longer than this entry assumed: a full
`up` still reverts it, which is what work-queue 109 fixes.

**What the operator decided, in order.** Asked to top up the Anthropic account after EXP-019 emptied it
(DL-264 amendment 3): *"No, no funds until coming Sunday"*. Then: *"re-wire for Chat GPT and get the
pipeline going"*. And, watching it being done: *"that SHOULD be a configurational change and a trigger"*.

**What stood in the way** *[measured 2026-10-06, read in the code and on the fleet]*.

- **Each deliberator must pass both vendors' probes.** The credential-test pack lists `anthropic` and
  `openai` for all three, and the fleet check counts every failing probe, required or not
  (`agents/master/credential_test.py`, `fleet_preflight.py`). Setting the provider alone would have left
  them refused.
- **The operator agent has no provider setting** and its only probe is `anthropic`. One refused agent
  makes the run degraded, and a degraded run holds its buys whoever is missing.
- **The tunables pack is a fidelity decision path** (`scripts/replay_fidelity_git.py`). Changing the
  provider there and recording a deploy would have reset the clean-session count two days before the
  verdict of 2026-10-08.
- **Without the switch:** the September drain's four recorded failures read `degraded` under today's
  code (4 of 4), and no degraded run has ever been placed (0 of 84 `RunRequest`s), so four nights would
  have run a path proven only by unit tests, with no buys.

**What was changed, live only, 12:30 to 12:50 UTC.**

| App | Change | Everything else |
| --- | --- | --- |
| `master` | `MASTER_CREDENTIAL_TESTS_B64` = the repo pack without the four `anthropic` probes (8 of 12 tests remain) | image `s251`, resources, scale, secrets, ingress and identity equal the snapshot |
| `deliberator-manager`, `-proponent`, `-opponent` | `DELIBERATOR_LLM_PROVIDER=openai`; the models resolve to `gpt-5.5` | the same |

No code moved and no `DeployRecord` was written: the fleet's deployed commit is still `d526faf4`. The
snapshots and the temporary declaration are in OneDrive `trading-agents-data/rewire-2026-10-06/`.

**Proven.**

- **The vendor.** The fleet's own probes, run with the fleet's keys: `openai` passed, `anthropic` failed.
- **The debate, offline.** One full debate on `gpt-5.5` through the production functions, on GILD's
  recorded packet: 4 of 4 guided turns read, the slowest call 54 s against the 120 s limit, the judge's
  JSON read (`revise`). **$0.66 for the order.**
- **The fleet, live.** The master and the three deliberators were woken under their own rule names. The
  fleet check **passed twice with 0 failures over all 15 agent types**; each deliberator reached
  `state active` with `openai` declared, tested and passed; 0 escalations, 0 faults, no run and no
  debate written. The four wake windows were restored and equal their snapshots.

**What it means for the week.**

- **A debated buy costs about $0.66**, so three buys a night are about $2 and twelve about $8, on the
  OpenAI account, whose balance the planner cannot read.
- **The model change is ungated.** DL-24's gate needs an Anthropic judge, which has no credit. `gpt-5.5`
  ruled on 136 orders in August and September. This week's rulings are its own and are not to be pooled
  with `claude-opus-5`'s.
- **The operator agent activates unchecked** and its chat fails on use until the account is funded.
- 🪤 **The state is live only.** The pack still says `anthropic`, so any full `up` puts both changes back.
- **EXP-019 does not move.** It is pre-registered on `claude-opus-5`; another model is another experiment.

**To restore, after the top-up and a fresh probe of the Anthropic key:** set
`DELIBERATOR_LLM_PROVIDER=anthropic` on the three deliberators and the master's
`MASTER_CREDENTIAL_TESTS_B64` from the repo pack, then compare each app with its snapshot.

**Ruled out.**

- *Change the pack and run a full `up`.* It resets the fidelity count, and the state is temporary.
- *Mark the probes not required.* The fleet check counts them anyway.
- *Leave the operator agent's probe.* The run would be degraded and the buys held.
- *Fire a test run now.* It would decide today's as-of again with three orders already queued for the open.

**Owed.** The morning check of `sched-2026-10-06`, the first run on OpenAI: a normal posture, the run's
`role_models`, buys submitted, the night's cost. The restore after Sunday. Work-queue **109**.

---

## DL-264 - the debaters answer each other only by habit, and the judge has given every debate since 2026-09-17 the same ruling on the same closed grounds - status: MEASURED (planner, 2026-10-06 21:50 AEDT); direction DECIDED (operator, 2026-10-06: the debaters first, and whether they can weigh the evidence; work-queue 107)

**The operator's focus (2026-10-06).** *"How our trio of experts can be made to produce a) discussion
b) qualified answer to the debate issues."* This entry measures where the three roles stand on both. It
adds to DL-250 (do the roles understand the evidence), work-queue 75 (one-sided examples) and
[ADR-0029](decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md) (what a ruling binds). It
re-opens none of them.

**Measured.** *[2026-10-06, read-only, no LLM call]* All 88 `DeliberationRun`s. The denominator is every
order with recorded turns that did not fail open: **243 orders in 42 runs**. 🪰 The "names the other
side" and "concedes" rows are word matches, so they are upper bounds on engagement, not proof of it.

| What | Measured |
| --- | --- |
| Rulings since 2026-09-17 | **34 of 34 `revise`**, over 11 runs (one is the planner-fired test run of 2026-10-01). Last `uphold` 2026-09-15, last `overturn` 2026-09-01 |
| What those 34 rationales rest on | `reward_risk` or its zero threshold **30**, sizing **19**, correlation **10**, sentiment or news **2** |
| The judge's rationale | median **230** characters (49 to 740); names the defender in **14 of 243** (6 %), and in 2 of the last 34 |
| Who speaks last | the challenger, in **73 of 73** debates since 2026-09-01 |
| Round 2 names the other side | defender 136 of 235 (58 %), challenger 100 of 243 (41 %) |
| Round 2 concedes something | defender 63 of 235 (27 %), challenger 53 of 243 (22 %) |
| Guided turns whose reasoning could not be read | 1 of 36 (a challenger round 2 wrote its `argument` inside the reasoning JSON) |

Forty older records (2026-08-07 and 08-08) list their turns out of order. Not investigated; every
record since 2026-09-01 is in order.

**One debate read in full: GILD, `sched-2026-10-05`** (4 turns, each about 4,000 characters).

- **There is an exchange.** The defender's round 2 opens on the challenger's claim (*"the only risk
  check with a non-zero threshold is the one it barely cleared"*), answers it with four gates from the
  packet, answers the sizing and the confidence points, and concedes one gap (no fill-price re-check).
  The challenger's round 2 answers the defender's "scaled beats flat" with the packet's own numbers
  (the target is the same in both modes; the stop is 2.00 ATR against a 1.73 ATR target).
- **The last turn adds a point nobody can answer:** the confidence floor rejected 0 of 37 candidates.
- **The ruling restates the challenger's last turn.** It names `reward_risk`, the skew, the sizing
  headroom and the sector slot, and addresses none of the defender's three answers.
- **The contested points are about the gates and the bracket.** The stock's own evidence
  (fundamentals, sentiment 0.750, beta) is read in round 1 and the sentiment is never contested.
- **Every demand is a change to the system** (*"set threshold_reward_risk_ratio above 0"*,
  *"re-check sizing at fill"*). No one acting on one order can make it.

**Why, read in the code.**

1. **Nothing asks for a reply.** A guided turn is `readings`, `gaps`, `argument`
   (`kernel/deliberation_guided.py`), and the role prompts say *argue for* and *attack*
   (`kernel/deliberation_prompts.py`). Answering the other side is the model's habit. It is not a
   recorded step, so it cannot be scored, and it is absent from about half of round-2 turns.
2. **The challenger closes.** `_debate` (`agents/deliberator/poll.py`) asks the defender, then the
   challenger, in each round, and the judge reads the transcript straight after the challenger's
   last turn.
3. **The judge is asked for one line and has been shown one ruling.** `JUDGE_SYSTEM` asks for
   `{"ruling", "rationale": "<one line>"}`. All six of its examples rule `revise`. It is told not to
   uphold when the challenger "catches a grounded implementation-specific flaw", and the challenger is
   told to find one and to say why it forces REVISE or OVERTURN. The ruling has no place to list the
   contested points, say who prevailed on each and on which reading, or say what would have to change.
4. **The issues are about the system, and they are closed.** The floor of 0 on `reward_risk` (ADR-0027
   Correction 2, EXP-011), fixed-fraction sizing (EXP-012) and the correlation cutoff (EXP-008) are
   each measured and decided. No role is told so. ADR-0029's decisions 2, 3 and 4 (a block names a
   fact about this order; the judge is told what each ruling does; a `revise` lands in a register,
   deduplicated by ground) were sequenced after S214, are not built, and are not in the work queue.
   Since S214 a `revise` does not block. **So for three weeks the debate has changed no order, and
   its finding has had no reader.**

**What the two goals need, as far as the measurement shows.** Not decided; the direction is the
operator's.

- **(a) A discussion** needs replying to be a recorded step: a turn after the first lists the other
  side's points and answers each (concede, rebut with a reading, or name it as a matter for the
  system, not this order). The last word must not open a new point, or the defender gets a closing
  reply.
- **(b) A qualified answer** needs the ruling to be built from the issues: each contested issue, both
  positions, the judge's finding, the reading it rests on, and whether the issue is about this order
  or about every order. An issue about every order goes to ADR-0029's register with its standing
  answer, and that answer is given to all three roles as a definition (DL-250's rule: true of every
  order, the same for every role).

**Not measured.** Whether a reply answers the point it names (it needs a typed record or a reader);
what a closing turn would cost; whether ADR-0029's tests 1 to 5 were ever read as a set (test 3 feared
`overturn` above 20 %; it reads 0 of 34).

🧭 **AMENDMENT, 2026-10-06 22:24 AEDT — the operator's direction: the debaters first, and whether they can weigh the
evidence.**

**The direction.** *"I would start with deliberators. Why? They are the source of data for the rest of
the process. … If the source is bad then the rest of the data is a 'fruit of a poison tree'."* And
what to concentrate on: *"Can we make LLM understand and assign 'weights' to the quant values we send
them. … Can they be made to understand not only the value, but general significance of an indicator in
relation of other indicators. … I want to make sure the decisions are made based on facts."* The
planner had proposed starting with the judge. The order is now the defender and the challenger, then
the judge, and the first question is significance, ahead of the reply step and the issue-built ruling
above.

**Measured the same day** ([rounds-and-weights](research/dspy/rounds-and-weights.md); no LLM call).

- **The system has weights, and no role is shown them.** Confidence = 0.30 + 0.60 × (0.50 × technical
  + 0.30 × fundamental + 0.20 × sentiment). The VIX is not in the score: it selects the regime, which
  sets the floor and the base stop and target. The packet prints the scores with no weight and no
  formula.
- **GILD cleared its floor only on the sentiment score** (0.628 against 0.600; 0.598 with sentiment at
  a neutral 0.50). The debate spent two rounds on *"an undisclosed mapping"* between two numbers that
  one line of code relates, and named the sentiment score once.
- **Nine debates store their packet.** The code's weights reproduce the confidence in 9 of 9. Five
  would fail the floor with one pillar set to neutral. In the three that hinge on sentiment, the
  judge's ruling mentions sentiment in none.

**DSPy, read at 3.4.0 and probed offline** (the operator: *"Read it and tell me what you think"*). The
site has no example of roles arguing. `dspy.History` carries rounds as real message pairs, where we
paste one text block. The experimental decision types (`Score`, `Choice`, `Noul`) with `ReAnchor` make
a stated weight a typed number that can be compared and calibrated, and they work beside S246's guided
reasoning, as top-level fields only. They record a weight. They do not make it right.

**The planner's answer to the question.** A model will state a weight for anything, so a stated weight
proves nothing by itself. It can be checked against two references that exist today at no cost: the
code's arithmetic (which pillar this order hinges on), and a changed input (do the weight and the
argument follow it). Whether the code's own weights are right is a third question that only outcomes
answer, and fundamentals and sentiment have no history in the replay cache (DL-232).

**Next step, proposed (not approved: it spends money).** One pre-registered experiment on recorded
packets before any production change, EXP-019: the two debaters' first turns with typed weights, on
today's packet and on the packet plus the arithmetic, each with the hinge value moved. The call count
and the dollar budget are stated in the pre-registration. After it, the packet states the arithmetic
(with work-queue 98) and the turn records its weights. Work-queue **107**.

**Finance models from Hugging Face** (the operator: *"may be relevant or not"*).

- **Not for the three roles' reasoning.** No model knows what our keys mean in this system, which is
  the measured defect. *[assumed, not measured]* A smaller model is also weaker at the strict typed
  output the harness depends on.
- **Relevant in one place this entry measured.** The sentiment score decided 3 of 9 orders. It is a
  word count over headlines, and GILD's list includes headlines about other companies. Scoring it with
  a finance-tuned model is the existing champion–challenger track.
- **A later arm, not a first step.** All three roles run one model (`claude-opus-5`, read from the run
  record), so they may share blind spots. A second model family as one debater can be an arm of the
  same experiment.

🪰 The last section is the planner's knowledge of those models, not a survey made today.

🩹 **CORRECTION and AMENDMENT 2, 2026-10-06 22:57 AEDT — the VIX sets nothing; the experiment is approved and
pre-registered.**

**Correction.** The amendment above says the VIX *"selects the regime, which sets the floor and the base stop
and target"*. That is what the packet's `Regime:` line suggests, and it is wrong. *[measured 2026-10-06, the
whole mechanism read]* `classify_regime` turns the VIX into a label. The provider then builds every
`RegimeContext` from four settings constants (`agents/provider/agent.py`), the same under every label. The
label is read only to be printed: the analyst's summary sentences, the packet and the trace. **In today's code a
large VIX changes no score, no floor, no stop and no target.** On the operator's own example (*"a large VIX or
great company data?"*) the code gives the VIX no weight at all, so any weight a debater puts on it is the
debater's own. EXP-013 measured that scaling risk down under stress loses; nothing tells the debaters so.

**Approved.** Operator, 2026-10-06: *"go ahead"*, on *"OK to spend up to $10 on it?"*.
[EXP-019](research/experiments/EXP-019-do-the-debaters-know-what-an-order-hinges-on.md) is pre-registered: nine
recorded packets and four with the relative-strength band moved; today's packet against the packet plus the
arithmetic; each debater answers, with a probability, whether the order hinges on each pillar; the bars are set
before the run. Estimate $7.70; no call starts after $9.00.

**Not decided.** Whether the packet's `Regime:` line should stop presenting four constants as the regime's. It
belongs with work-queue 107's packet change.

🔴 **AMENDMENT 3, 2026-10-06 23:14 AEDT — EXP-019 was stopped by an empty LLM account, and it is the fleet's account too.**

**What happened.** After 31 of the 52 planned calls ($3.91) the vendor refused the next four: *"Your credit
balance is too low to access the Anthropic API"*. The fleet's `anthropic-api-key` is the same key as the
planner's (compared by hash), so the three deliberators and the operator agent have no credit either.
*[by S227's design, not tested tonight]* A run whose only failing checks are the LLM agents proceeds with its
buys held.

**The planner's miss.** The spend was approved; the balance was never asked about, and the planner cannot read
it. A paid experiment draws on the same balance as the nightly debate. The planner's standing rule from now:
ask what the balance can carry before a paid run, and count the fleet's night first.

**Interim, not a verdict** ([EXP-019](research/experiments/EXP-019-do-the-debaters-know-what-an-order-hinges-on.md), Appendix R; phase 2 has not run). With the arithmetic in the
packet, 45 of the 45 answers given are right. On today's packet 34 of 45 are, and all 11 errors are false
alarms: a debater today names more pillars as decisive than are.

**Found by an arm-B turn, and checked against the packet: MRK was approved on a rival's good news.** MRK's
order on `sched-2026-10-05` cleared its floor only on its sentiment score (0.7167; neutral gives 0.5918). 7 of
its 20 headlines are about Vaxcyte's pneumococcal vaccine trial win, two of them *"Takes Aim at Pfizer and
Merck"*, and the word count reads *spikes*, *soars*, *win* and *success* as good news for Merck. The live debate
that night ruled `revise` on the `reward_risk` gate and never raised it. The challenger given the arithmetic
found it in one turn. Filed as work-queue **108**.

**Owed by the operator:** the top-up, before the fleet check that precedes `sched-2026-10-06` (22:30 UTC).
**Owed by the planner after it:** the remaining 21 calls (about $2.80), on the operator's word that the balance
can carry them.

📎 **AMENDMENT 4, 2026-10-07 00:00 AEDT — the operator's prototype is filed as R010, and two of its ideas feed the two goals.**

The operator supplied a generic debate-pipeline prototype (a proponent, an opponent, a judge that computes risk
and issues directives, and a revision loop) and asked for it to be filed as research:
[R010](research/debate-pipeline-prototype/INDEX.md). The planner's reading, not a decision:

- **For goal (b), a ruling needs a reader.** The prototype's judge issues directives that the next round must
  answer. Here the reader cannot be a model that rewrites the order (ADR-0017, ADR-0022). It is ADR-0029's
  register for a point about the system, and the other debater's next turn for a point about this order.
- **For decisions that rest on facts, risk figures belong in the packet.** The prototype has the judge compute
  VaR and expected shortfall. Computed in code and defined, they are evidence (work-queue 98). Computed by a
  model, they are not.
- **Not taken:** a model that writes the trading plan, a judge inside the loop it rules on, and the generic
  parameter list.

🧭 **AMENDMENT 5, 2026-10-07 12:15 AEDT — the prototype is the shape to build, adapted; amendment 4's "not taken" was the wrong reading.**

**The direction.** The operator, on the prototype of amendment 4: *"it does not have to be implemented
VERBATUM. It can bee adpted to our needs."* Amendment 4 sorted its parts into taken and not taken. Read as
a shape to adapt, each part has a form here. The part-by-part table is in
[R010](research/debate-pipeline-prototype/INDEX.md).

**What the adapted debate is.** Three typed roles and a loop. The defender argues for the order the
pipeline wrote. Each of the challenger's points carries a reading, a severity, and whether it is about
this order or about every order. The judge returns a ruling built point by point, with directives. After
round 1 the judge states what is still open, round 2 must answer each point, and the judge rules. Risk
figures are computed in code and shown to all three. This is goals (a) and (b) of this entry in one
design: the directive is what makes a reply a recorded step, and the point-by-point ruling is the
qualified answer.

**The one part not carried over, on purpose.** In the prototype the loop revises the plan. Here a ruling
can stop a buy and change nothing else (ADR-0029 decision 1: the model may subtract, never add). So the
loop improves the debate and the ruling, not the order. Letting a ruling shrink an order is a
capital-risk decision, and it stays the operator's to reopen.

**The order of work.** Each step is its own change, and a changed prompt passes ADR-0010's gate with its
budget stated first.

1. **DSPy in the deliberator's process**, with no prompt changed: [S254](sprints/sprint-254-each-debater-turn-is-run-by-dspy-and-the-prompt-does-not-change.md), specced
   ([ADR-0032](decisions/0032-dspy-runs-the-llm-roles-at-run-time.md), DL-266).
2. **Facts in the packet**, all computed in code: the score arithmetic (work-queue 107), the withheld
   facts (work-queue 98), risk figures for the order and for the book, each with a definition
   (work-queue 97 c). Building it needs no model call. Its paid check is EXP-019's arm B.
3. **The debaters' typed turn:** what the order hinges on, and for the challenger a severity and a scope
   on each point. After EXP-019's verdict.
4. **The judge's typed ruling**, point by point, with directives and a probability for each ruling. The
   judge is told what each ruling does (ADR-0029 decisions 2 and 3).
5. **The loop:** the judge's open points after round 1, an answer to each in round 2, and an early end
   when none is open. *[ASSUMED, not measured]* an order with no open point then costs 3 calls where it
   costs 5 today, and one with open points costs 6.
6. **The register** for directives about the system (ADR-0029 decision 4).
7. **One offline program** composing the three predictors, for evaluation and GEPA (work-queue 97 d).

Steps 2 and 3 keep the operator's order of 2026-10-06: the debaters first. Step 1 does not wait for the
Anthropic account. Steps 3 to 5 each need a paid replay.

**Not decided.** How many points a ruling may hold. Whether the judge's statement of open points is its
own call or part of its ruling. Which risk figures the book supports today: nothing is measured.

🧭 **AMENDMENT 6, 2026-10-07 12:20 AEDT — the loop that revises the plan is the workflow, and it is carried; amendment 5's exclusion is withdrawn. The debate stays on OpenAI while this is plumbed.**

**The direction.** Amendment 5 said the prototype's loop *revises the plan*, and left that part out. The
operator: *"the workflow is what we are after."* The planner reads this as: the cycle itself is the thing
to build. A proposal is critiqued, the judge sends it back with directives, the proposal is revised, and it
goes round until the judge accepts or the rounds run out. A loop in which only the arguments change is not
that workflow. 🪰 If the operator meant the process without a changed order, the revision step below is
dropped and the rest stands.

**What a revision can be here.** The model may subtract, never add: the founding constraint is kept. So a
revised order is the same ticker and side with a smaller quantity, or no order. Nothing else about an order
is a model's to move: the stop and the target are measured from volatility (ADR-0019, ADR-0031), and the
entry is the session's (ADR-0018). The judge's directive is typed. The revised order is checked in code
against those bounds and run again through the PM's own gates, and the next round debates the revised
order.

**Shadow first.** While the workflow is being built, the revised order is recorded beside the original and
the original is what executes. `revise` therefore still changes no order, ADR-0029 stands as written, and
the plumbing reverses no law clause. Each revision is scored against what the unrevised order went on to
do. Making a revision binding is a capital-risk decision: it needs that ledger, an ADR that amends
ADR-0029, and a law cycle (`DLIB-NEV-02`, `DLIB-OUT-04`). It is the operator's, and it is not part of the
plumbing. *Why not binding at once:* 34 of the last 34 rulings are `revise`, 19 of them on sizing, which
EXP-012 measured and closed. A binding revision today would shrink every order on a ground already
answered.

**The order of work, changed in two places.** Step 5, the loop, now includes the revision, in shadow:
directives, a revised order, the code's re-check, the next round, the judge's acceptance. A new last step
is added: the revision becomes binding, on the operator's decision.

**Vendor.** The operator, in the same message: *"Keep it on OpenAi whilst we are plumbing."* See DL-265's
note. Every live check and replay of the plumbing runs on `gpt-5.5`. *[the planner's reading]* A judgement
of prompt quality (EXP-019, a GEPA run) is not plumbing, and stays on the model production is meant to run.

**Not decided.** Who writes the revised quantity: the defender, inside the bounds, or code from a typed
directive. How many rounds the cycle may take, against what each costs.

🧭 **AMENDMENT 7, 2026-10-07 18:19 AEDT — step 2 is three pieces and the arithmetic goes first; the quality checks are to be read on both vendors.**

**Step 2, split.** Read against the code, "facts in the packet" is three pieces at different stages. The
score arithmetic is measured and prototyped, and is packaged as
[S255](sprints/sprint-255-the-packet-states-the-score-arithmetic.md) (DL-269). The withheld facts (work-queue 98) rest on an inventory of 30
September and have no definitions written. The risk figures have no measurement. The last two follow as
their own sprints, each after its measuring.

**The operator, on EXP-019's remainder:** *"$2.80 is ok."* The run resumes on Opus when that account is
funded (2026-10-11).

**The operator, the same hour:** *"maybe we should continue testing on OpenAI to get confidence tat if we
HAVE TO swap from anthropic to openai again it will give up comparable results."* Amendment 6 recorded the
planner's reading that a judgement of prompt quality stays on the model production is meant to run. That
reading is too narrow. The fleet debates on `gpt-5.5` this week, a forced swap can happen again, and the
first real debate on it already showed one difference: the defender writes 2.7 times the output it writes
on Opus for the same order (6,363 and 7,738 tokens against 2,334 and 2,853) and reaches 94 % of the cap
(work-queue 111). **Direction:** a check of what the roles understand is run on both vendors, on the same
frozen cases, and compared answer by answer.

**Run, 19:10 AEDT ([EXP-020](research/experiments/EXP-020-on-the-same-cases-does-gpt-5-5-know-the-hinge-as-opus-does.md), $6.52, the operator approved $7).** With the arithmetic `gpt-5.5`
answers 54 of 54 hinge questions right and is on Opus's side of 0.5 in 45 of 45 answers both gave. On today's
packet the two guess, and differently (5 of 36 on opposite sides). So the arithmetic is also what makes a
vendor swap safe on this question. `gpt-5.5`'s defender writes twice Opus's output, and the fleet's cap would
have cut 5 of its 16 typed turns: work-queue 111 now has a measured frequency and comes before step 3.

**Found the same evening, 20:37 AEDT: the measured text has a false clause.** S255's builder stopped while
pinning the first line: arm B's first line says that inside `quant_metrics` *each key ending in `_score`* is a 0-100 band score. Four such keys are on a 0-1 scale: `technical_score`, `fundamental_score`, `sentiment_score` and `composite_score` (measured over 1,765 recorded recommendations: 20 distinct keys end in `_score`, and these four never exceed 1.0).
The planner wrote that sentence for EXP-019 and carried it into S255's spec as frozen text without checking it
against the keys. Corrected on S255's branch: one clause excepts the four keys, and the other two lines are
unchanged. **What it does to the gate:** EXP-019 and EXP-020 measured the uncorrected line, and every answer
was right with it. The corrected line is not measured. *Decided by the operator ("run it") and done,
20:59 AEDT ([EXP-021](research/experiments/EXP-021-does-the-corrected-first-line-read-as-well-as-the-measured-one.md), $3.29):* with the corrected line `gpt-5.5` answers 54 of 54
right, and all 54 are on the side they were on with the uncorrected line. The corrected text is measured on
`gpt-5.5`. It is not measured on Opus, and EXP-019's remaining calls will measure the uncorrected line there.

**As it was proposed, before the run.** EXP-019's frozen cases on `gpt-5.5`, with the runner's vendor as the only
change. *[estimated, not measured]* On Opus a call cost $0.126 (31 calls, $3.91). The one debate measured on
both vendors cost 1.6 times as much on `gpt-5.5`, so about $0.20 a call: about $7 for the 36 calls that
answer H1, about $10.50 for all 52. It can run now, because that account is funded. A stop at the output cap
counts as an unread answer, as the pre-registration already says.

---

## DL-263 - the window is computed in one pure reporter module over one listing of each label, a count that cannot be computed is absent, and positions_held reuses RPT-OUT-07's snapshot selection - status: DECIDED (builder, 2026-10-02; S253, under DL-262)

**Question.** DL-262 decided what the book metrics read. How is it built so `result.py` (154) and
`domain/lineage.py` (179) stay under 200, what happens when the reported run has no `created_at`, how
is the snapshot selection shared, and which analyst clause takes DRIFT-096?

**Decided.**

- **D1, two new modules, lineage untouched.** `agents/reporter/domain/book_window.py` is pure: it
  parses an instant, finds the window's start among `PMRun`s, places filled `Fill`s by
  `broker_status_refreshed_at`, and counts. `agents/reporter/book_inputs.py` lists `Fill` and `PMRun`
  **once each** per report and runs the pure functions inside a `fault_boundary`
  (`capability="report.book"`), so a failure there leaves the book keys absent, records a fault and
  keeps the rest of the snapshot (as `RPT-FAIL-04` does for performance). `domain/lineage.py` is not
  changed: the lineage still supplies recommendations, rejections, the market lineage and the
  `CloseDecision`s that `close_trigger_target` / `close_trigger_time` read.
- **D2, the window.** Upper bound inclusive at the **reported** `PMRun.created_at` (the instant
  `RPT-IDM-03` already uses; a resumed run's `linked_from_key` source is not consulted). Lower bound
  exclusive at the latest other `PMRun.created_at` strictly before it; a `PMRun` whose `created_at`
  does not parse is never a boundary; no earlier run, no lower bound. A fill counts only if its
  lower-cased `broker_status` is in `FILLED_BROKER_STATUSES` and its `broker_status_refreshed_at`
  parses (a naive instant is UTC, as the brief reads it). `status` and `submitted_at` are never read.
- **D3, a reported run with no readable `created_at`.** The window and the inception span are
  undefined, so `positions_opened`, `positions_closed`, `close_trigger_stop`,
  `closed_trades_with_pnl`, `profit_factor` and `expectancy_cents` are **absent**, and the headline
  prints `?` in the two count slots (the `?` `orchestration/batch_trace.py` already prints for an
  absent key). No second fault is recorded: the performance read already faults on the same missing
  `created_at`. `RPT-NEV-03` is amended to say so.
- **D4, `positions_held`.** `performance_inputs.py`'s selection now returns the chosen
  `BrokerPositionSnapshot` nodes (latest fresh per UTC date, at or before `PMRun.created_at`, on or
  after the inception, with integer equity) and the points are built from them; `positions_held` is
  the length of the last chosen node's `holdings`. One listing serves both. With none chosen, or when
  the performance read faults, the key is absent.
- **D5, the outcomes.** Filled sells refreshed in [00:00 UTC of `performance_inception`,
  `PMRun.created_at`] go through the unchanged `collect_trade_outcomes`, so `_pnl_cents`'s exclusions
  stand. `CloseDecision.pnl_cents` is no longer an input to the run snapshot (the function still
  accepts it, for its own tests).
- **D6, the degraded snapshot** keeps its counts at 0.0 (`book_counts(())`) and
  `closed_trades_with_pnl` 0.0, with a headline that says why; it has no `positions_held`.
- **D7, DRIFT-096 is a new clause, `ANLZ-IN-05`.** It is about what the analyst accepts as a scoreable
  input, so it sits with `IN`; amending `ANLZ-OUT-03` (the regime gate) or `ANLZ-FAIL-03` (a scoring
  exception) would have stretched clauses that say something else. Proven by two tests in one file,
  `test_analyst_domain.py`: the 1-bar rejection and the 40-bar scored candidate (its confidence is
  the blended one, so it was not rejected), which gains one assertion (`sma_distance_pct_missing_bars`
  160) and folds its arithmetic comment into the citing docstring, because the file sat at 199 lines
  and the block is at 200. No analyst code changes.

**Road not taken.**

- *Put the window in `domain/lineage.py` or `result.py`.* Both would cross 200 (179 + ~45, 154 + ~40).
- *Report 0.0 for the counts of a run with no `created_at`.* A zero that cannot be true is the thing
  this sprint removes; the omission is what `trade_outcomes.py` already does for an undefined ratio.
- *A new headline sentence explaining the missing counts.* The spec forbids new wording; `?` is the
  number becoming true, and the performance clause beside it already names the unavailable input.
- *Raise inside the book read for a missing `created_at`, so the boundary records a fault.* Two
  faults for one cause; the performance read already records it.
- *A second `BrokerPositionSnapshot` listing for `positions_held`.* The spec says reuse; a copy could
  drift from `RPT-OUT-07`'s rule (as work-queue 88's earliest-per-date bug did).
- *Count `partial` fills.* `FILLED_BROKER_STATUSES` is the brief's and the contract's set; a
  partial is not yet a position opened.

**Planner's note at merge (2026-10-02).** *[measured on the live graph]* A resumed run's `PMRun` is
a clone: `orchestration/resume.py::_linked_props` copies its source's props, `created_at` included.
The one on the graph, `resume-link:sched-2026-07-13-resume-monitor:pmrun`, shares
`2026-07-13T22:33:14Z` with the `PMRun` it resumes. So D2's instant of the reported run is its
source's: the two report the same window, and "strictly before" keeps either from being the
other's start. The handback's law reading took a resumed run to have its own `created_at`; that was
assumed, not read. `RPT-IDM-04` now says what happens, and
`test_book_window_edges.py::test_a_resumed_run_reports_its_sources_window` holds it (planted: the
start made inclusive, `assert (0.0, 0.0) == (1.0, 3.0)`, red, restored). No filled fill on the graph
sits in that shared window, so F1 counted none twice (129 of 129 in exactly one window).
*Ruled out:* giving the clone an empty window (it would report 0 opened on the run the operator
resumed, the number this sprint exists to remove) and consulting `linked_from_key` for the instant
(the same value by construction, and a second read path).

---

## DL-262 - a run's book metrics are read from the broker's fills in the run's window, not from the PM run's lineage - status: DECIDED (planner, 2026-10-02; work-queue 106, DRIFT-099, built as S253)

**Question.** The reporter's snapshot has never counted an opened or closed position. What should its
book metrics read, so that they are true when the snapshot is written and stay true when an old run
is re-reported?

**Measured before deciding (2026-10-02, on Neon).**

- **0 of 86** `Snapshot`s carry a `positions_opened`, `positions_closed` or `execution_count` above
  zero. The reporter reads its own PM run's lineage minutes after that run's orders are submitted
  for the next open, so nothing in the lineage has filled. Exits are resting broker stops, in no PM
  run's lineage; the monitor has written no `CloseDecision` since July (7, all July).
- 129 `Fill`s read `broker_status` `filled` (85 buys, 31 resting-stop sells, 13 other sells). All 129
  carry a readable `broker_status_refreshed_at`, and all 129 read `status: pending`.
- Placed by that time into (previous `PMRun.created_at`, this `PMRun.created_at`], each of the 129
  falls in exactly one run's window. The last four runs read 12 / 3, 1 / 1, 0 / 0 and 1 / 3.
- Since `performance_inception` (2026-08-10): 31 exits, all stops, all losses, −146,279 cents.
- `positions_held`, `execution_count`, `approval_execution_gap` and `dropped_decision_count` are read
  by nothing outside the reporter and its tests.

**Decided.**

- **D1, the window.** A filled `Fill` belongs to the run whose window holds its
  `broker_status_refreshed_at`: after the previous `PMRun`'s `created_at`, up to and including the
  reported one's. It is the daily brief's rule for a fill's time (S234), bounded by upstream facts
  only, so `RPT-ORD-01` holds and an old run re-reports identically.
- **D2, the counts.** Opened = buy fills in the window; closed = sell fills in it; stops = those
  `contracts.broker_lifecycle.is_resting_stop_fill` accepts.
- **D3, held.** The holdings of the run's as-of position snapshot, the one `RPT-OUT-07` already reads.
- **D4, the outcomes.** Profit factor, expectancy and the closed-trade count are cumulative, over
  every exit fill with realised P&L from the inception to the run. A one-night profit factor over
  three trades says nothing; the span matches the benchmark figures beside it.
- **D5, three keys removed.** `execution_count`, `approval_execution_gap` and
  `dropped_decision_count` describe the run's own orders, which cannot have filled when the snapshot
  is written. Nothing reads them.

**Road not taken.**

- *Re-report a run once its orders resolve.* A `Snapshot` is append-only (`RPT-STA-02`), the stops
  would still be in no lineage, and the count would arrive a day late.
- *Start the window at the reporter's previous `Snapshot`.* `RPT-ORD-01` forbids depending on the
  reporter's own output, and a `Snapshot` carries no time.
- *Import the brief's `fills_between`.* An agent imports nothing from `orchestration`.
- *Re-point the three keys at the previous run.* A fair metric and a new one; not this fix.
- *Keep them and document the zero.* A number that can only be zero misleads the reader who does not
  open the law book (work-queue 56).

**Cost named.** One report lists `Fill` (0.35 MB) and `PMRun` (0.86 MB), once per run and only when
a `MonitorRun` is pending. The poll that finds that work is already key-and-edge (DL-246).

**Not decided here.** `close_trigger_target` and `close_trigger_time` still come from the lineage's
`CloseDecision`s and stay 0 until an exit other than the stop exists (work-queue 92).

---

## DL-261 - every remaining pending-work finder fetches only its candidates - status: DECIDED (builder, 2026-10-02; S252)

**Scope and evidence.** Clean worktree `../ta-s252`, branch
`sprint-252-every-finder-fetches-only-its-pending-work`, based on local `main` and
`origin/main` at `ae54cf3591bc3312d6f7056cfd79a4a888675613`. The whole four law books,
their test plans, conventions and drift register were read before code. The planner's
live measurements in S252 are context, not measurements made by this builder.
All builder proof is offline unit proof; no `.env`, push, version/lock edit, gate,
merge, deploy or live check is authorised.

**D1 - both forecaster finders.** Use `pending_nodes` on `AnalystRun` with the
respective `FORECAST_BY` or `BARRIER_SETTLEMENT_BY` edge and
`created_at_from=None if now is None else now - CLAIM_RUN_MAX_AGE`. Keep
`is_current_run` and forecast's history-readiness check on candidates only.
Missing/non-string creation stamps are excluded by a bounded key query; malformed
or zone-less strings it over-includes are still rejected by `is_current_run`.
Without `now`, there is no recency bound. The accepted timestamp-format limit is
DL-246 D2: fleet writers stamp UTC, and arbitrary negative offsets are not a new
supported query format. Rejected: only filter fetched props (downloads the stale
backlog), new SQL casts (one malformed stamp can break a poll), or a new tunable.

**D2 - pending PM runs.** Deliberator uses `DELIBERATED_BY`, execution submit uses
`EXECUTED_BY`; retain presence of `order_intent_set` and the existing `is_waiting`
predicate respectively. Accept fetching an orderless PM run on each idle poll,
and fetching one waiting through its bounded grace. Tests pin both accepted costs.
Rejected: adding a property query/filter to the kernel port, or changing review,
posture, grace, submission or exit policy. The processed-edge check must never walk
to a completed deliberation's transcript.

**D3 - monitor sync.** Find `RunRequest`s without `POSITION_SYNCED_BY`, then read
each request's one `linked_snapshot`; return snapshot nodes in request order. A
request awaiting its snapshot returns nothing. The only decided set differences
are: do not adopt a second snapshot for an already-synced request; do reselect a
snapshot whose own marker edge exists but whose request edge is missing. The
unchanged marker-exists branch completes both edges with the same one marker.
Rejected: start at snapshots (106 PM-keyed snapshots in the planner's measurement
never receive a sync marker), or put a 24 h window on them (loses delayed adoption).
The old snapshot-side suggestion in DRIFT-097 is superseded by this decision.

**D4 - execution sync.** Use `pending_nodes` on `RunRequest` with `REFRESHES`.
The request-side edge is the completed-snapshot fact. Rejected: walking each
request's edge just to discover completion, or widening any graph vocabulary.

**D5 - payload fixture split.** Move the unchanged PayloadSpy and PollCase into a
small support module, retain the seven seeders/cases, and put the six new seeders
and cases in a separate module. Share only synthetic fixture construction.
Rejected: weaken the spy, grow the existing 166-line module past 200, or raise a
module-size baseline. Each case pins fetched and returned keys in order.
Full-CI refinement, recorded before the fixture correction: S242's same-work
oracle also consumes the original `CASES` export. Keep that seven-case export
stable and join the six S252 cases in the payload suite only. Rejected: add new
cases to the old seven-case oracle or edit its expected values; monitor's decided
set differences require their own proofs, and all thirteen payload cases remain.

**D6 - completeness.** Read `agents/**/*.py` with AST and collect module-level
sync/async functions named `find_pending` or `find_pending_*`, except
`find_pending_work` aggregators. Compare exact `(module, function)` identities to
the case-to-callable registry, including wrapped forecaster calls, and require each
case once. Prove omission and an uncovered fourteenth finder fail. Rejected:
import every module (side effects and optional dependencies), a bare count (an
omission and duplicate can cancel), or a manually fixed discovery list.

**Law cycle.** Amend the four named trigger clauses and add `EXEC-TRG-08` after the
whole execution book confirms its silence. DRIFT-100 records that missing trigger;
`EXEC-TRG-02`'s stale primary-path qualifier is reported and left untouched. No
other clause changes. Dependencies in the ledger are historical context; this
builder does not refresh them. `DLIB-TRG-03` and `DLIB-IDM-01` remain gray.

**Proof owed.** Red A1/A4/A8 before implementation, A1-A8 green, four red-and-restored
DL-70 plants, redirected `make ci` with every unavailable step named. PATCH bump,
re-lock, remote gate/CodeQL, F1, retag after the fidelity verdict, and F2 stay with
the planner. No byte saving is inferred from the in-memory spy.

**Builder proof result.** A1-A8 and all four plants proven; 43 final focused checks
(including 14 unchanged S242 comparisons) pass. Final full pytest: 3,953 passed,
8 skipped, 100.00 %; `make ci` exits 2 only because the offline guard refuses the
advisory lookup. Dependency audit NOT RUN to completion; the other fourteen
checks pass, with secret checks run separately. No release or live claim.
Main advanced independently through S253 to `d8949a32` (`0.121.02`); this proof
stays on the declared `ae54cf35` base. Planner integration must preserve that parallel work.

---

## DL-260 - each ruled drift row becomes a clause the code already keeps, proven where a test can hold it, and what the code does less of the clause says less of - status: DECIDED (builder, 2026-10-01; S251, under DL-259)

**Question.** DL-259 ruled the 23 rows. What does each amended clause say, which test proves it, and
which clauses stay ⬜?

**Measured before writing (2026-10-01).**

- The coverage gate reads `agents/*/laws`, `orchestration/laws/*` and `surfaces/laws` only
  (`law_coverage_docs._law_book_paths`). It **never reads `docs/laws/dependencies.md`**. Every
  clause-shaped ID in a book counts as that book's own clause, so no book may name another book's IDs.
- `owns_graph` has no runtime reader: only `kernel/contract.py` declares it, and only tests read it.
  One test, `tests/test_boundary_map.py::test_each_graph_label_has_one_writer`, fails on any label
  that two contracts own.
- The only live OHLCV source is `AlpacaDataSource` (`composite.market_source_from_settings`).
  `alpaca_request.bars_page_query` sends `symbols, timeframe, start, end, feed, limit` and never an
  `adjustment`. Alpaca's default is `raw`.
- The monitor's end-of-run poll uses `kernel.graph_pending`. Its position-sync poll
  (`position_sync.find_pending_position_sync`) lists every `BrokerPositionSnapshot` with props.
- The pytest guard (`conftest.py`) replaces `AzureServiceBusBus._azure_send` only. It blocks a send;
  a receive is not guarded.
- `PMRun` carries `order_intent_set` = `run_id, approved, rejected, explanation, provenance`.
  `PM-OUT-01` and `PM-TYP-03` also list `portfolio_state_snapshot`, and the contract has no such field.

**Decisions.**

1. **Graph-pull triggers (DRIFT-082, 085, 086).** Each book names its own work in its `TRG-02`: the
   label, the edge whose absence makes an item pending, and any wait condition. Then one sentence
   states the bound: pending work is found by key and edge, and props are fetched only for nodes that
   lack the edge. `PROV-TRG-01` is widened to the three recorded needs. Proof: each agent's poll tests
   (find, process, marked) plus `tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work`,
   whose docstring now names every amended `TRG-02`. New `agents/provider/tests/test_graph_pull_trigger.py`
   is D4: a `RunRequest` with no bus event is ingested, and an empty graph is never fetched.
   *Rejected:* a new `TRG` clause per book, which would leave the false "primary production trigger
   path" in place; and putting the bound in a system book, which DL-259 already ruled out.
2. **The monitor's bound covers `ExecutionRun` work only.** The sync poll does not meet it, so the
   clause does not claim it does. That poll is filed as DRIFT-097 (code gap, OPEN). *Rejected:* fixing
   the sync poll here, which is a behaviour change, and stating the bound for "every poll", which would
   be false.
3. **Raw bars (DRIFT-084) go into `PROV-OUT-07`**, the clause that already describes a bar. Proof:
   new `test_alpaca_raw_bars.py`, which checks that the source's own request names no adjustment.
   *Rejected:* a new `OUT` clause, which splits the one bar description in two.
4. **`PROV-OUT-04` (DRIFT-040)** now promises a recorded `MarketSnapshot` with `created_at` and
   `used_fallback`, mirrored in `market_data_degraded`. It says outright that it records neither the
   source nor a transformation (work-queue 105). It turns 🟩 on a new test of exactly that.
   *Rejected:* staying ⬜ "for safety". The narrowed clause is fully provable, so leaving it gray
   would under-report.
5. **The analyst's held-stop check (DRIFT-074) is `ANLZ-OUT-09`.** Its inputs come from the shared
   stop-width resolver. A held ticker whose latest close is at or below
   `opened_price_cents × (1 − stop_pct)` is a `sell` with `exit_trigger="stop"`, whatever its
   confidence. A position whose broker stop is live is left to that stop. A book whose stop inputs
   cannot be read is a fault and an empty result, never a guessed stop. Proof: new
   `tests/test_analyst_held_stop.py` (D6), placed in `tests/` because it uses execution's stop
   fixtures, plus the four ADR-0017 tests in `test_exit_authority.py` and the shared-resolver test.
   *Rejected:* an `OBS` clause, because the check produces an output and not only evidence.
6. **The divergence exception (DRIFT-094)** is declared by the family it covers: `subject_ref`
   beginning `broker-position-divergence:`. `SUP-IDN-02` says its single-writer rule has that one
   exception, written by the broker boundary's run-start reconciliation, and it names no agent
   (conventions §5). New `EXEC-IDN-04` says execution writes that family and no other `Flag` or
   `FlagResolution`. `owns_graph` and the CAP list gain both labels. `test_each_graph_label_has_one_writer`
   now allows exactly that pair, shared by exactly those two contracts. Proof (D7): new
   `agents/execution/tests/test_divergence_flag_ownership.py` records every label the writer touches
   and every subject it writes. *Rejected:* letting the boundary-map test skip shared labels, which
   would let any future share pass silently.
7. **Execution's output clauses (DRIFT-061)** name the contract's fields. `EXEC-OUT-01` drops
   `pm_run_id` and adds `dropped`/`skipped`. `EXEC-OUT-02` keeps the six `Fill` fields and says that
   `client_order_id` is the broker call's key, not a `Fill` field. `EXEC-OUT-04` drops `run_id`.
   `EXEC-OUT-05` names `accepted, previous_stage, current_stage, reason, provenance`, and says a
   dry run is `confirmed=False` with nothing written. The already-green rows stay green on
   `tests/test_contract_required_payload_fields.py::test_execution_payload_fields_required_by_law`, and
   the gray ones stay gray. *Rejected:* adding the old fields to the contract, a behaviour change.
8. **Contract version (DRIFT-060).** `SCAN-TYP-01`, `EXEC-TYP-03` and `PM-TYP-03` say that
   `CONTRACT.version` names the current schema, and that no clause promises the version moves when a
   field is added, removed or renamed. No gate is added.
9. **PM (DRIFT-037, 039, 065).** `PM-OUT-03` uses the emitted reason strings. `PM-OBS-04` is per
   evaluated candidate. `PM-OBS-01`, `PM-OUT-06` and `PM-STA-04` claim only what `PMRun.order_intent_set`
   carries, and name execution's `BrokerPositionSnapshot` (by label, not by agent) as the record of the
   pre-trade book. `PM-OUT-06` and `PM-STA-04` stay ⬜, because nothing tests that the PM reads no live
   broker. `PM-OUT-01` and `PM-TYP-03`, which carry the same false field, are not named by the row
   table. They are filed as DRIFT-098 and **not reworded**.
10. **Supervisor `SUP-OBS-02` (DRIFT-076)** turns 🟩. `open_incidents` counts live `Fault` incidents and
    never a `Flag`; `pending_human_flags` counts unresolved `critical` Flags. Proof: a new test that
    keeps the two sources apart, plus the existing health tests.
11. **Forecaster (DRIFT-081, 083).** `FORE-IDN-01` names the four legs. `FORE-OBS-01` names the recorded
    node per leg. `FORE-IDM-03` covers the three shadow scorecards. All three stay ⬜: no test covers the
    return leg's node, and `IDN-01` is a whole-purpose statement. The partials are named in their rows.
12. **Master (DRIFT-059)** gets `MST-FAIL-07`, the start-up refusal, proven by
    `test_remediation_posture.py`. A plain paragraph (no clause) states that attempting remediation is
    outside the constitution until DL-36 Pieces C and D are built. The `remediation_mode` `PARAM`
    rationale now says that `automatic` is refused today. *Rejected:* writing remediation clauses now
    (DL-259).
13. **`DEP-BUS-05` (DRIFT-032)** reads: a local test run never **sends** to the production Service Bus.
    No test-plan row exists, because the gate does not read the charter and no charter test-plan
    exists. The guard's three tests cite the clause, and the ledger's Layer-0 `DEP-BUS` row is
    recounted (it said 3 clauses; there are 5). *Rejected:* a charter test-plan file, which would be a
    new layout that no gate reads.
14. **Surfaces `SRF-OUT-03` (DRIFT-078).** An answer the model composes is grounded and audited. The
    four graph-read quick asks write no audit fact and make no model call; `status`, `incidents` and
    `scorecard` are not scoped by the selected run. Proof: a new test of the four quick asks, plus the
    existing audited-answer test.
15. **Rows with no file change (DRIFT-030, 031, 034)** become `DECIDED` with the feature they wait for.

**Ruled out, generally.** Writing a clause for something the code does not do; making a gray clause
green on a partial test (§7a); creating a charter test-plan or a kernel book.

**Not claimed.** Live proof of any amended clause (the planner's F1), or that the books are complete.

## DL-259 - the 23 open drift rows are ruled in one pass: the law follows the code, a claim the code does not meet is narrowed, and a row that waits for a feature says which - status: DECIDED (planner, 2026-10-01; work-queue 104, S251)

**Question.** The drift register holds 22 `OPEN` rows and one `PARTLY CORRECTED`, the oldest from
2026-08-06. Each needs a forced decision. What is it, for each, and is it one sprint?

**Measured (2026-10-01).** Every row was read; the stale-prone ones were re-measured:
`portfolio_state_snapshot` and `RecommendationOutcome` still have 0 hits in the code; the PM still
emits `sector_concentration` and `reward_risk_below_min`; `contracts/execution.py` still lacks the
fields four `EXEC-OUT` clauses name; four test-plan layouts still exist, and the gate has parsed all
of them since S204. Two ledger versions lag their books (reporter v1.3, supervisor v1.2).

**The rule applied.** No row is closed by changing behaviour. Where the code is right and the clause
is old, the clause is amended. Where a clause promises what was never built, it is narrowed to what
is true, and if the missing thing still matters it becomes a queue item instead of a silent
promise. Where a row waits for a feature that does not exist, it becomes `DECIDED` with the feature
named, because `OPEN` means a decision is owed.

**Rulings.**

- **Amend to the code (14):** DRIFT-082, 084, 085, 086, 077, 087, 076, 081, 037, 074, 061, 094, 059, 032.
- **Narrow (6):** 078 (`SRF-OUT-03` covers operator-mediated answers), 083 (`FORE-IDM-03`'s subject),
  065 (`PM-OBS-04` is per candidate), 039 (the PM claims what `PMRun` carries), 060 (a contract
  version is the current schema's identity), 040 (`PROV-OUT-04` promises fetch time and the fallback
  flag).
- **Decided, waits (3):** 031 (the four layouts stay), 030 (owed when a substrate law book is
  authored, next-leg E20.3), 034 (`RecommendationOutcome`'s builder owns its cycle).

**Ruled out, per row where it was a real choice.**

- *DRIFT-094: route execution's flag writes through a supervisor capability.* Run-start
  reconciliation would wait on another agent, and `EXEC-TRG-07` says nothing alongside the snapshot may
  prevent it. Declared as an exception instead.
- *DRIFT-039: build the PM's pre and post snapshot.* Execution's `BrokerPositionSnapshot` already
  records the pre-trade book each run; a second copy on the PM's node is a feature nobody has asked for.
- *DRIFT-040: record the serving vendor now.* It is a real gap (ADR-0006 has three possible OHLCV
  sources and the graph cannot say which answered), and it is a behaviour change: a contract field and
  a write. Filed as work-queue 105 so it is ranked, and the clause stops promising it meanwhile.
- *DRIFT-060: add a contract shape and version gate.* A new CI gate, against the next leg's process
  freeze, for a failure that has not happened.
- *DRIFT-059: write remediation clauses now.* DL-36 Pieces C and D are not built; a clause for them
  would be unfalsifiable. One clause states the refusal that exists.
- *DRIFT-086: put the poll's download bound in a system book.* No such book exists (DRIFT-030); the
  bound goes in each agent's trigger clause, where its test already is.
- *DRIFT-030: author a kernel law book here.* A full law cycle from the template, and E20.3 needs it
  shaped by the second pack.
- *DRIFT-031: one layout for all fourteen test-plans.* Churn with no proof gained.
- *One sprint per book, or per kind of ruling.* Thirteen gate cycles for text. One sprint, one commit
  a book, rows independent so a blocked one does not hold the rest.

**Not claimed.** That the amended books are now complete. This closes the rows that were filed.

## DL-258 - the history rule filters in its own module and counts only when on; the scorer rebuilds each resample in integer cents and draws one stationary index stream for every arm - status: DECIDED (builder, 2026-10-01; S250)

**Why.** DL-257 (below) fixed what EXP-014 scores and by what rule (its Appendix P is frozen). S250's spec left six
implementation decisions to the builder. Each is recorded here before the code, with what was
ruled out.

**D1 - where the history rule lives.** A new `scripts/replay_history.py` holds both the window
(`visible_window`, moved verbatim out of `replay_session.py`'s `_visible_bars`) and the filter
(`offer_lines`): it counts each member's bars inside the declared window, keeps a line that is held
or holds at least `required_history_bars(settings.analyst)` bars, and returns the kept members, their
bars and the number removed. `replay_session.py` gains one keyword (`require_history`) and one call;
moving the 13-line helper out pays for it, so the file shrinks. *Ruled out:* the filter inside
`replay_series.py` (its helpers are settings-free, and the filter needs the analyst's settings and
the book); inline in `replay_session.py` (190 lines; it crosses 200); filtering in the day runner
(`replay_day.py` would then be told what "held" means twice, and the session row's `members` count
would disagree with what the pipeline saw).

**D2 - the counter exists only when the rule is on.** `replay_runner.run` adds
`member_sessions_below_required_history: 0` to the absent-input set only when `require_history` is
true. *Ruled out:* always present (0 when off). No existing test asserts the whole dict, so the
constraint alone would allow it, but F1 requires the rule-off run to write byte-identical files to
the commit before; a new key in `summary.json` breaks that. The key's presence is therefore itself a
statement that the rule ran, and `arm.json` records the rule's state explicitly beside it.

**D3 - the bootstrap's draw algorithm and percentiles.** One `random.Random(seed)` drives every
draw. A resample of `n` session-pair indices: the first index is `rng.randrange(n)`; each next index
is a fresh `rng.randrange(n)` when `rng.random() < 1 / mean_block`, else the previous index plus 1,
modulo `n` (wrapping, Politis and Romano's stationary bootstrap). Resamples are drawn one at a time
and each is applied to **every arm and the control before the next is drawn**, so the index stream
does not depend on how many arms there are and is never held in memory whole (10,000 x 2,445 Python
ints would be about a gigabyte). Percentiles by order statistics with integer arithmetic: sort the
`B` draws ascending, `k = B * 25 // 1000`; the 2.5th percentile is `v[k]` and the 97.5th is
`v[B - 1 - k]`. At `B` = 10,000 that is `v[250]` and `v[9749]`: exactly 250 draws lie below the lower
bound and 250 above the upper. *Ruled out:* a fixed block length (the moving-block bootstrap; its
resamples are not stationary, and Appendix P names the stationary one); interpolated percentiles
(numpy's default; a float index, and nothing gained at 10,000 draws); drawing all indices up front
(the memory); one generator per arm (the arms would no longer be compared on the same days, which
Appendix P forbids, and plant (d) proves C9 catches it).

**D4 - what `arm.json` records and what makes arms refusable.** `arm.json` holds the arm's name,
slippage and overrides, the start, the first and last session and their count (read back from the
`equity.csv` the replay wrote), `require_history`, the repo commit (`git rev-parse HEAD`), `dirty`
(`git status --porcelain --untracked-files=no` non-empty) and a 12-hex SHA-256 prefix of each cache
file the harness reads (`sp500_sessions`, `_membership`, `_bars`, `_benchmark`, `_vix`, `_sectors`
`.csv.gz` and `sp500_coverage.json`; a missing optional file is recorded as `absent`). The arms
command also writes `benchmark.csv` (date, SPY close) for the arm's sessions, so the scorer needs no
cache and can check every arm scored against the same closes. `arm.json` is written last, so an
interrupted replay leaves no `arm.json` and is refused as missing. **A dirty worktree refuses to start
an arm** (an 84-minute run on code no commit names is not evidence), and the scorer refuses a
`dirty: true` arm anyway. The scorer refuses, naming the arm and the reason, when: an arm directory
or file is missing; an arm's name, slippage, overrides, start or rule state differ from the manifest;
arms differ in commit, cache checksums, sessions (dates, not only counts) or benchmark closes;
`equity.csv` disagrees with `arm.json`'s sessions; an arm has a gap session
(`performance_gap_sessions > 0`); or the control fails. *Ruled out:* trusting a dirty run with its
diff recorded (the scorer cannot replay a diff); checksumming the whole cache folder (other files
there are not inputs); the scorer re-reading the cache for SPY (it would tie the scorer to the
licensed folder and still not prove the arms used those closes).

**D5 - how a resampled series is rebuilt.** Each arm's pairs are read once as
`(E_prev, E_cur, L_prev, S_prev, S_cur)`. A resample is rebuilt on consecutive synthetic dates
(ordinal day 1, 2, ...) starting at **10^14 integer cents**: each step's equity is
`round(E' x E_cur / E_prev)` and its invested value `round(E' x L_prev / E_prev)`, both in integer
arithmetic (round half up), and SPY starts at 1.0 and steps by `S_cur / S_prev`. The rebuilt points
and closes go through `calculate_performance`, which alone yields `P`, `E` and `n`. The control's
replica is built the same way from `base-25`'s pairs with its equity step replaced by
`E_prev + L_prev x (S_cur / S_prev - 1)`: SPY earned at `base-25`'s exposure. It passes when `|A|` and
both interval bounds are at most `1e-6` points (the rebuild's rounding is about 1e-14 a step).
*Ruled out:* rebuilding from the original equity's scale (10^7 cents rounds to 1e-7 a step and
drifts); float equity (the reporter types points as integer cents); real calendar dates (a resample
has no calendar; `calculate_performance` only orders and pairs them).

**D6 - the layout of `verdict.md`.** One page, in this order: the verdict and its reading in the
title line; `base-25`'s `A` and interval with `n`, resamples, block and seed; the arms table
(slippage, `A`, interval, portfolio, exposure-matched, SPY, average exposure, max drawdown); the
paired differences from `base-25`; the control; the yearly `A` table (partial years marked, then the
count of years with positive excess per arm); the two halves; provenance (commit, sessions, rule,
cache checksums, the history rule's removed member-sessions). A refusal writes the same two files
with `NO VERDICT` and the refusals in place of the tables, and the command exits 2. Numbers are
rounded to 6 decimals in `verdict.json` (sorted keys, `-0.0` normalised) and to 2 in `verdict.md`.
*Ruled out:* per-year intervals (ten more bootstraps of a partial year answer nothing Appendix P
asks); a plot (not byte-stable without a pinned renderer, and the gate has none).

**Found while building: the rule withholds every unheld line before 2024 (BLOCKS F1 and F2).**
`declared_lookback_days` counts sessions with `agents/provider/domain/market_calendar.py`, whose
holiday table covers **2024-2027 only** and treats every earlier weekday as a session. Before 2024
the window it returns therefore holds 203 *weekdays*, of which 6-9 are NYSE closures the cache has
no bar for. *[measured 2026-10-01, the builder's container, with NYSE's 2016-2023 closures written
out and checked against EXP-014's own counts: 2,698 sessions from 2016-01-04 and 2,446 from
2017-01-03 both reproduce once 2025-01-09, a closure the provider's table also lacks, is removed]*
a line with a bar on every session holds **194-198 bars** in its window on **every** session from
2017-01-03 to 2023-12-29 (1,760 of 1,760) and on 74 sessions of 2024; from 2025 on, 203. So with
the rule on as specified, no unheld line clears `required_history_bars` (200) before 2024: EXP-014's
arms would buy nothing for seven years. The same arithmetic means every replay so far, rule off,
gave the analyst at most 198 bars before 2024, so SMA-200 distance was absent from every pre-2024
replayed decision, the smoke run's included. The code does what the spec says and is proven on
synthetic caches whose sessions follow the provider's calendar; the hazard is pinned by
`tests/test_replay_history_calendar.py` (a 2019 cache that skips 2019's real closures: 197 bars on
2019-12-31, withheld), which flips when the calendar is fixed. *Not done here, deliberately:* the
repair is the provider's holiday table (an `agents/` file, out of S250's scope by the spec's own
stop rule), or a harness window cut from the cache's sessions instead of the calendar (a change to
what the analyst sees, with the rule off too, so F1's byte-identity fails by design). Both are the
planner's call; the builder recommends the first, back to 2016 and with 2025-01-09 added, because
it also gives the rule-off replay the 203 bars the fleet is given.

**Found while deciding (recorded, not acted on).** EXP-014 section 2 states H1 as *"`A > 0` and the
lower bound … above 0"*; Appendix P states EDGE as the lower bound alone. They differ only if the
point estimate falls below its own interval's lower bound. The code follows Appendix P, as the spec
binds it, and `verdict.json` records the point estimate beside the interval so a reader sees that
case if it ever occurs.

**Amendment, S250 return 1 (builder, 2026-10-01; the planner ruled repair (a)).** The provider's
holiday table (`agents/provider/domain/market_calendar.py`) now lists NYSE's full-day closures from
2016: the 74 dates of 2016-2023 and 2025-01-09, as measured in Return 1's table against the cache
(2016-01-01 from the public record). No existing date changed, and `calendar_window_end()` still
returns 2027-12-31. Sessions a year now count 252, 251, 251, 252, 253, 252, 251, 250, 252, 250 for
2016-2025. On every one of the 2,446 sessions from 2017-01-03 to 2026-09-25, the window
`declared_lookback_days` gives holds exactly 203 sessions, the analyst's 200 plus the 3-session
staleness buffer (`tests/test_replay_history_calendar.py`, flipped from pinning the gap to asserting
the repair; `agents/provider/tests/test_market_calendar_history.py`). Fleet effect: the declared
lookback differs from the old table only for an as-of between 2025-01-09 and 2025-10-29 (measured
over 2025-2027), so no run the fleet places today reads a different window. *Rejected:* **(b)**,
cutting the harness window from the cache's own sessions. It leaves the calendar wrong for every
pre-2024 replay that counts sessions with it, and makes the harness stop calling the fleet's own
`declared_lookback_days`. It would also change rule-off output by design, so F1's byte-identity
check would fail for a reason the repair does not need. The rule's threshold and Appendix P are
unchanged. Not claimed: F1, F2 or GATE PROVEN.

---

## DL-257 - EXP-014 scores five replays from 2017 with a block bootstrap through the reporter's own metric, and the harness holds a line back until it has the history the fleet's analyst is given - status: DECIDED (planner, 2026-10-01; work-queue 82, S250)

**Question.** E17.5 owes a verdict on the price-only pipeline (DL-232): edge, no edge, or edge in one
pillar. What exactly is scored, by what rule, and what must the harness stop doing first?

**Measured (2026-10-01).**

- **The one ten-year replay decides on history the fleet never has.** The cache's first bar is
  2016-01-04 and the replay starts there, so **113 of its 552 buys** were decided on fewer than 200
  bars: 103 in 2016, 10 on lines that had just joined the index, 57 on fewer than 50, the least on 11.
  The analyst's own floor is `min_history_bars` = 2 (bounded at 60); `required_history_bars` is 200,
  and a fleet run's names arrive with 203 bars.
- **187 of 721 lines** have their first bar after 2016: the cache holds a line's bars from the day it
  joined, not before.
- Stocks and SPY both carry `adjustment=all`, so both sides are total return.
- The drop-one ablation is one analyst setting: `relative_strength_weight` 0.0 or 1.0 (live 0.20).
- A series rebuilt from resampled session pairs and passed through `calculate_performance` reproduces
  the original to 3 × 10⁻¹⁴; one call over ten years costs 3.2 ms, so 10,000 resamples of five arms is
  under three minutes without numpy, which the gate's environment does not have.

**Decision.**

1. **A history rule in the harness, off by default.** With it on, a line that is not held is offered
   to the pipeline only when its visible window holds `required_history_bars(settings.analyst)` bars.
   Held lines stay visible. The member-sessions removed are counted.
2. **The scored window is 2017-01-03 → the cache's last session** (2,446 sessions). 2016 is history
   only, so every line present since the cache began has 252 bars on the first scored day.
3. **One statistic:** annualised excess over exposure-matched SPY, computed from
   `calculate_performance`'s outputs.
4. **One interval:** a stationary block bootstrap over session pairs (mean block 20, 10,000
   resamples, seed 0), the same draws for every arm, each resampled series scored by
   `calculate_performance`.
5. **Calendar years are evaluation blocks.** Nothing is fitted, so there is no training window and
   nothing to purge. The plan's phrase "purged, non-overlapping test windows" was written for a fitted
   model; EXP-015 is the one that fits.
6. **Five arms:** the fleet's settings at 5, 10 and 25 bps, and the two ablations at 25 bps.
7. **The verdict is the plan's rule** (lower bound above 0 at 25 bps). An ablation counts only if it
   also beats the full pipeline on the same resampled days.
8. **The run waits for E17.4's PASS.** The tooling does not.
9. **The split.** A cloud session builds the rule, the arms command and the scorer against synthetic
   series ([S250](sprints/sprint-250-a-replays-excess-return-comes-with-an-interval-and-a-verdict.md)). The planner runs
   [EXP-014](research/experiments/EXP-014-does-the-price-only-pipeline-beat-spy-held-at-the-same-exposure.md) on the licensed cache and writes the result.

**Ruled out.**

- *Fetch each late line's earlier bars.* The right repair, and the only one that keeps a joiner in the
  universe from its first day. It is a cache rebuild over the network in a file at 199 lines. Holding
  the line back and counting it gives a valid verdict now; revisit if the count is large.
- *Raise `ANALYST_MIN_HISTORY_BARS`.* Bounded at 60, and a setting the fleet does not run.
- *Start the replay on 2016-01-04 with the rule on.* Ten months of cash inside the scored window.
- *Chain the daily ratios inside the bootstrap.* A second definition of return, the thing the plan's
  one-metric rule forbids.
- *An i.i.d. bootstrap.* Daily excess returns of a book that carries positions are not independent.
- *A fresh replay per year.* Each starts in cash and spends weeks deploying; that is another strategy.
- *A t-test on the ten yearly numbers.* Ten observations, the last one partial.
- *Ablation arms at 10 bps too.* The bar is at 25; two more 84-minute runs would decide nothing.
- *Score the existing smoke replay.* It predates five merged fixes and contains the short-history buys.
- *Hold out the last two years.* No setting is chosen inside this experiment, so a holdout has nothing
  to protect. The honest limit is stated instead: the pack's settings were chosen with this decade in
  view, which biases toward finding an edge.

**Not claimed.** Anything about the full pipeline (fundamentals, sentiment, the deliberator), or about
the fleet's 99-name book at 22 % invested.

**Amendment (planner, 2026-10-01, at S250's first return).** Decision 1 was written against a window
the planner assumed held about 203 sessions and never measured by year. The builder measured it: the
provider's holiday table covered 2024–2027 only, so before 2024 every weekday counted as a session
and the declared lookback came out about a week short. *[verified on the cache]* The window held
194–198 sessions on all 1,760 sessions of 2017–2023, so the rule as specified would have kept every
arm in cash until 2024, and every earlier replay on this harness (S235's smoke run included) gave the
analyst at most 198 bars before 2024, with no 200-day average. **Repair:** the table now holds every
NYSE closure from 2016 and 2025-01-09 (DL-258's amendment); the calendar equals the cache's sessions
on every day from 2016-01-04 to 2026-09-25, and the window holds 203 on all 2,446 scored sessions.
*Ruled out:* cutting the harness window from the cache's own sessions, which leaves the calendar
wrong and stops the harness calling the fleet's own function. The live fleet's lookback is unchanged
for any as-of after 2025-10-29. Appendix P is untouched: it says only that the rule is on.

## DL-256 - a run's ingest reads its as-of once, as an exact ISO date no later than today, and one helper builds the window from it - status: DECIDED (builder, 2026-10-01; S249)

**Why.** DL-255 (below) measured the defect and set the direction: the provider reads the
`RunRequest`'s as-of and builds the window from it.
[S249](sprints/sprint-249-a-runs-market-window-ends-on-its-as-of.md) left four decisions to the
builder. The planner's recommendation was taken for D1; D2–D4 are the builder's. All four are stated
in `PROV-TRG-05` (provider laws v1.7).

**D1 — a `RunRequest` with no as-of, or one that does not parse, is refused with a `ValueError`
before any fetch.** The same shape `_lookback_days` already uses for a bad lookback, and what
`PROV-TRG-03` asks (an invalid request is refused, nothing fetched). All 81 live requests carry one
(DL-255). The lookback's own checks run first, so an existing test that omits both still meets the
lookback error it expects. Cost: the request helper in `test_provider_poll.py` and the short-lookback
test add the as-of, and so does the benchmark test's helper.

- *Ruled out: fall back to today.* That is the defect, made silent.
- *Ruled out: fall back to the node's creation time.* A second date source for one fact, and a resume
  child is created later than its source's as-of, so it would read the wrong day again.
- *Ruled out: record a fault and skip the request.* The `INGESTED_BY` edge is the processed mark; a
  skip without it is re-polled anyway, and with it the run is lost quietly.

**D2 — only the exact ISO calendar date the dispatcher writes parses**: a string `s` with
`date.fromisoformat(s).isoformat() == s`, i.e. `YYYY-MM-DD`. A full datetime, a non-string, the compact
`20260930` and the week form `2026-W40-3` are refused (B7 proves each).

- *Ruled out: accept a datetime and take its date.* Which date depends on the zone: a 22:30 UTC
  placement written with a `+10:00` offset reads as the next day. The surfaces already read a naive
  `requested_at` as UTC; the provider would be a second interpreter of the same field, and nobody
  writes a datetime there today.
- *Ruled out: accept whatever `date.fromisoformat` accepts.* On Python 3.11+ that includes the compact
  and ISO-week forms. The writer never produces them, so a typed `--as-of` override in one of them is a
  mistake to refuse, not a date to guess.

**D3 — the as-of travels as a parameter, `as_of: date | None = None`, on `ingest_once` and
`ingest_chunked`, and one helper in `ingest.py`, `_run_window(lookback_days, as_of)`, builds the
window for both paths** (`as_of − lookback … as_of`; `_today_window` when `as_of` is `None`).
`_today_window` stays as it is: the standalone path still calls it, and two test files import it.

- *Ruled out: build the `Window` in `poll.py` and pass it down.* `ingest_once` would then take a
  lookback *and* a window, two copies of one fact free to disagree, and the chunked dispatch would carry
  both.
- *Ruled out: give `_today_window` an as-of argument.* Its name would then lie, and its two importing
  tests (at 175 and 198 lines) would need edits for no behaviour change.

**D4 — an as-of later than the UTC date the provider reaches the request on is refused**
(`ValueError`, before any fetch). The dispatcher never writes one (its as-of is the UTC date it runs,
DL-255), so only a mistyped `--as-of` override can, and the operator should hear about it.

- *Ruled out: serve up to today.* The stored `window_end` would differ from the request's as-of: the
  shape of the defect this sprint removes, made silent.
- *Ruled out: serve the future window as asked.* The stored `window_end` would claim a session that
  has not closed, and the regime would be read as of a day with no `^VIX` bar; the SIP end rule caps the
  bars anyway, so what is stored could not match what it claims (`PROV-STA-04`).

**The coverage check** (`_covered_sessions`) counts sessions from the lookback's start up to the
as-of, the same date `declared_lookback_days` declared the lookback against
(`orchestration/start.py`). For a scheduled run this is the date it used before.

**Not changed.** The barrier history window (`barrier_history.py:94`) and the eight wall-clock reads
in five other agents (DL-255, out of scope); the value `"requested_at"`; `surfaces/` and
`orchestration/resume.py`.

**Accepted by the planner at merge (2026-10-01).** D2 and D4 are stricter than the spec asked and stand: a refusal is loud (the work loop records the failure and backs off), and the dispatcher writes neither form. One consequence: the as-of is a UTC date, so a test run placed from Melbourne before 10:00 AEST (11:00 AEDT) with the local date is refused as after today.

Two things found at merge and left alone:

- *The `uv lock` diff is 52 lines.* Dependabot's uv (`5b44d973`) had dropped dependency markers and ten `greenlet` wheel entries that uv 0.8.14 writes back. The package set is identical, 180 = 180. Ruled out: hand-editing the version line to keep the diff small; the lock is uv's file.
- *CodeQL filed the `ingest` and `ingest_chunked` pairing again, as alert 279 (note).* The import statement changed by one name; alert 61 dismissed the same pairing on 2026-07-04. Left open beside ten identical notes on `main`. Ruled out: dismissing it, the step the operator overturned on alert 263; removing the pairing here, a module split outside a merged sprint. `ingest.py` is at 191 lines, so its next change forces that split.

## DL-255 - the provider builds a run's window from the clock, not from the run's as-of - status: DECIDED (planner, 2026-10-01; work-queue 103, built as S249, DL-256)

**Why.** The fleet test run `verify-2026-10-01-s248-a` was placed for as-of 2026-09-30, the session `sched-2026-09-30` had run on that morning. It read 202 bars a name where the scheduled run read 203, and bought TGT (0.61) where the scheduled run had rejected it (0.587).

**Measured (2026-10-01).** `agents/provider/ingest.py:72-75` (`_today_window`) returns `today − lookback … today`; `ingest_once` (`:167`) and `ingest_chunked` (`ingest_chunked.py:136`) use it; `agents/provider/poll.py:90-99` never reads the request's as-of (`requested_at`). The regime is read as of `window.end`, and news and earnings anchor on `window.end` (`fundamentals.py:98`, `:139`), so all four follow the clock. Reproduced on `InMemoryGraphStore` with `FakeDataSource` and no `.env`: a request for 2026-09-30 ingested on 2026-10-01 writes `window_end` 2026-10-01 (script in the [S249 spec](sprints/sprint-249-a-runs-market-window-ends-on-its-as-of.md)). On Neon: all 81 `RunRequest`s carry `requested_at` as a 10-character date; **0 of 60** scheduled runs have a `window_end` different from their as-of, and **8 of 21** other runs do, each by one day. The two runs for 2026-09-30 hold the same newest bar and close; the test run's window slid one day and dropped the oldest bar. How much of the changed decision came from the bar shift and how much from five hours of newer headlines was not measured.

**Direction (planner).** The provider reads the as-of from the `RunRequest` and builds the window from it; the coverage check uses the same date; an ingest with no run keeps today. The property gets a name in `contracts/provider.py`. New clause `PROV-TRG-05`, DRIFT-095. A fix, PATCH, image-only retag, built by a cloud session. Scheduled runs do not change.

**Ruled out.**

- *Derive the as-of from the run id* - test runs and resumes carry no date in their id, and they are the runs this hits.
- *Have the dispatcher write the window on the request* - the lookback and the as-of are already there; a third field is a second copy of the same fact.
- *Forbid past-as-of runs* - 8 of 21 non-scheduled runs already are, and a scheduled run the provider reaches after 00:00 UTC is one too.
- *Fix every wall-clock date read at once* - 8 more sit in five other agents with five law books, and which of them run inside a graph-pull run is not measured. They stay in work-queue 103 as its second part.
- *Move the barrier history window too* (`barrier_history.py:94`) - DL-241 and DL-243 tie a barrier claim to the run's creation date on purpose; whether a past-as-of run should make a claim at all is a separate design question.

**Not claimed.** Point-in-time replay. Fundamentals and sectors come from sources that serve the latest value only, so a past-as-of run still reads today's.

**Built and merged as S249 (`0.120.03`); F1 passed.** The merged provider on the live sources, given a request for 2026-09-30 a day late, reads `sched-2026-09-30`'s window exactly: 203 bars a name, 10 of 10 names identical. The second part stays open in work-queue 103.

## DL-254 - a divergence flag names its episode by the snapshot that first saw it, and severity is read from the open episode - status: DECIDED (builder, 2026-10-01; S248)

**Why.** DL-253 (below) measured the defect and set the direction (the episode goes into the subject; readers unchanged).
[S248](sprints/sprint-248-a-divergence-is-critical-only-when-it-survived-a-run.md) left four decisions
to the builder; two more came up while building. The planner's recommendations were taken for D1, D3
and D4.

**D1 — the episode token is the key of the `BrokerPositionSnapshot` that first saw the divergence.**
It is unique per run-start reconciliation (`broker-position-snapshot:{run_id}:{created_at}`), already
in hand when the flags are written, the same on every read of that snapshot, and it ties the flag to
the snapshot that raised it. *Rejected:* (a) **the run id** — a resumed or re-fired run repeats it, so
two episodes could share a subject; (b) **a clock or a uuid** — not reproducible, so no test could pin
a subject and A8 would mean nothing (the `created_at` *inside* the snapshot key is fine: it is read
from the node, never from `datetime.now` at flag time); (c) **a per-ticker counter** — a
read-modify-write across runs, and the count is history the subject does not need.

**D2 — the subject is `broker-position-divergence:{kind}:{ticker}:{snapshot key}`.** The family
prefix stays first and the kind and ticker stay in front, so the legacy test
(`startswith("broker-position-divergence:broker-position-snapshot:")`) can never match a new subject
(no kind is named `broker-position-snapshot`), and `scripts/sweep_divergence_flags.py` never sees one.
`:` is the separator the family already uses; kind and ticker contain none, so `(kind, ticker)` is
the first two fields after the prefix whatever the token holds (the snapshot key has colons of its
own). Today's suffix-less subject parses to the same `(kind, ticker)` with no token. *Rejected:* (a)
**a distinct separator such as `@`** — buys nothing a fixed field order does not, and gives the family
two grammars; (b) **the token first** (`…:{token}:{kind}:{ticker}`) — the token starts with
`broker-position-snapshot:`, so the subject would start with the legacy prefix and the sweep would
retire live flags; (c) **a hash of the snapshot key** — shorter, but a reader could no longer go from
a flag to the snapshot that raised it.

**D3 — the open episode is found in memory, from one read of `Flag` and one of `FlagResolution`.**
A Flag is open when no `FlagResolution` carries its `(subject_ref, severity)`, the join every reader
uses (`agents/supervisor/domain/health.py`, `surfaces/queries/flags.py`). Open family Flags are grouped
by `(kind, ticker)`. Per live divergence: none open → a new episode at `warn` under this snapshot's
subject; an open `critical` → nothing (an open `warn` beside it, which only a crash between the two
writes could leave, is resolved "superseded by critical"); an open `warn` → `critical` on that
episode's subject and the `warn` resolved "superseded by critical" — **unless this snapshot is the one
that opened the episode**, because a second call for the same run-start reconciliation is not a
survived run. Every open family Flag whose `(kind, ticker)` is not live gets one resolution,
"divergence no longer present". The writer never writes a key it has already read (`EXEC-STA-03`).
*Rejected:* (a) **a `get_node` per divergence and severity** (today's shape) — it cannot find an
episode it does not already know the subject of, and N divergences cost 2N+ round trips; (b) **a
query on a `subject_ref` prefix** — a new kernel port for ~112 nodes and about two a night; (c)
**escalate on any open `warn`** (the spec's rule taken literally) — a repeated call with one snapshot
would read as a survived run.

**D4 — an open suffix-less Flag is the open episode.** It escalates on its own (suffix-less) subject
or retires exactly as it would have before this change, so a deploy landing between two runs neither
loses nor downgrades anything. All 112 live Flags are resolved today, so this path is for safety.
*Rejected:* **retire it and open a new-format episode** — a real `critical` would drop to `warn` for a
night, and a `warn` that survived the deploy would restart its clock. **Accepted limit:** a
suffix-less `warn` whose `critical` key is already spent (only two crashes in a row could leave that)
is not escalated, because the writer refuses a spent key; it stays the one open `warn` of its
divergence and is retired when the divergence goes.

**D5 — proceed although `SUP-IDN-02` makes the supervisor the single writer of `Flag` and
`FlagResolution`.** Execution has written both since S120/S178 and its CAP says
`write_own_labels_only`; nothing recorded it. This sprint adds no writer, label or kind of write, so
the contradiction is the same size after it as before. Recorded as DRIFT-094 (OPEN) with the forced
decision. *Rejected:* **stop the sprint** (the spec's MUST RULE step 6, read literally) — the measured
defect stays live while an independent ownership question waits; the planner can still return it.
*Rejected:* **route the writes through the supervisor's `flag_for_human`** — a cross-agent change,
out of scope, and `FlagResolution` has no supervisor capability to route to.

**D6 — the sweep test changes by one argument.** `test_reconciliation_flag_sweep.py` asserts that a
run's own `warn` survives the legacy sweep, and finds it by `subject_ref_for(_PFE)`, the suffix-less
subject. A subject that names its episode cannot be computed from the divergence alone, so that call
becomes `subject_ref_for(_PFE, "s1")`; the assertion and every other line are unchanged. The spec's
A10 ("passes with no edit") is therefore **not met as written**; the edit-free run's failure is in the
handback. *Rejected:* **keep `subject_ref_for(divergence)` returning the suffix-less subject and use it
for a ticker's first episode** — two subject grammars for new flags, and A8's "different first-sight
snapshots give different subjects" would be false.

**Measured while building — a correction to DL-253's first road not taken.** `merge_node` to a spent
key does not silently rewrite the old Flag. On Postgres the `ON CONFLICT … DO UPDATE` carries a
`WHERE NOT EXISTS` that skips the update when any incoming prop differs from the stored one, and
`_raise_merge_conflict` then raises `ValueError: property '…' cannot be overwritten`
(`kernel/graph_postgres.py:99`, `kernel/graph_support.py:87`); `InMemoryGraphStore` raises the same.
A new Flag always differs (`created_at`, and `reason` names the snapshot), so the one-line fix would
have **raised inside `reconcile_run_start` after the snapshot was written**: the run's flags lost, not
an invisible `warn`. Still rejected, for a different reason. The writer's spent-key guard (D3) keeps
that raise unreachable.

## DL-253 - a broker divergence's flag key has no episode, so a repeat ticker's first sighting is critical and its third is silent - status: DECIDED (planner, 2026-10-01; work-queue 100, built as S248, DL-254)

**Why.** On `sched-2026-09-30` the run flagged `extra_graph_position:MDLZ` as `critical`, "Divergence survived a full run without adoption", at 22:32:22 UTC and resolved it at 22:39 as "divergence no longer present". It was a first sighting: the position had left the broker since the previous run, and the same run retired it. `extra_graph_position:BAC` did the same on `sched-2026-09-29`.

**Measured (2026-10-01).** `agents/execution/reconciliation_flags.py:48` asks whether a `warn` Flag exists for the subject, not whether one is open. Flags are append-only (`EXEC-STA-03`) and keyed `flag:{subject_ref}:{severity}`; the subject is `broker-position-divergence:{kind}:{ticker}`, so each key is spent once per ticker. On Neon: 53 run-stable subjects, **40** with a spent `warn` (their next divergence is `critical` on sight) and **12** with both keys spent. For those 12 the code writes nothing: reproduced on `InMemoryGraphStore` with no `.env`, a third episode raises no Flag even after surviving two runs (the script and its output are in the [S248 spec](sprints/sprint-248-a-divergence-is-critical-only-when-it-survived-a-run.md)). All 112 divergence Flags have resolutions. Of the 10 `critical` divergence Flags since 09-01, 3 were checked and all 3 were first sightings; the other 7 were not checked. The behaviour S178 built is in no law clause: its tests cite `EXEC-TRG-07`, which covers only the snapshot.

**Direction (planner).** Put the episode into the subject: kind, ticker, and a token from the snapshot that first saw the divergence. Severity then comes from the open episode's unresolved Flag. The readers (`agents/supervisor/domain/health.py`, `surfaces/queries/flags.py`) join on the props `(subject_ref, severity)` and need no change. New clause `EXEC-OBS-07`, DRIFT-093. A fix, PATCH, image-only retag, built by a cloud session.

**Ruled out.**

- *Change line 48 to "no unresolved `warn`"* - the key is spent: `merge_node` rewrites the old Flag (`ON CONFLICT (label, key) DO UPDATE`, `kernel/graph_postgres_queries.py:21`), which breaks `EXEC-STA-03`, and the old resolution still matches `(subject_ref, severity)`, so the new flag reads as already resolved. A false `critical` would become an invisible `warn`.
- *Delete or supersede the old `FlagResolution` to re-open the flag* - deletion breaks append-only and loses history; a resolution of a resolution needs every reader changed.
- *Put the episode in the resolution key and keep the subject stable* - readers in the supervisor and in `surfaces/` join on `(subject_ref, severity)`, so an execution defect would need changes in two other components.
- *Drop `critical`, flag every divergence `warn`* - removes the one signal S178 built, that adoption failed.
- *The planner builds it in-session* - the builder and the checker would be the same agent; the live replay on Neon is the planner's either way.

**Correction (2026-10-01, measured by the S248 builder, DL-254).** The first item under *Ruled out* is rejected for a wrong reason. `merge_node` to a spent key does not rewrite the Flag: the `ON CONFLICT … DO UPDATE` carries a `WHERE NOT EXISTS` guard and the store raises `property '…' cannot be overwritten` (`kernel/graph_postgres.py:99`). The planner read line 21 of the SQL and not the guard under it. The one-line fix would have raised inside `reconcile_run_start` after the snapshot was written. It stays rejected. Also: of the 53 subjects, 52 are kind-and-ticker subjects and 1 is an old hash-keyed `critical`. **Built and merged as S248 (`0.120.02`); F1 passed.**

**Open, for the builder (next free DL).** The episode token (recommended: the first-sight snapshot's key; not the run id, a clock, a uuid or a counter), the subject's exact format, how the open episode is found, and how an unresolved suffix-less Flag is treated at upgrade (recommended: as the open episode).

## DL-252 - each debater turn is a DSPy-rendered guided turn, reproduced without DSPy, parsed strictly, and recorded with its packet - status: DECIDED (builder, 2026-09-30; S246)

🔁 **Reversed in part, 2026-10-07 ([ADR-0032](decisions/0032-dspy-runs-the-llm-roles-at-run-time.md), DL-266).** DSPy now runs in the deliberator's
process. D1's frozen literals are retired by S254. D2, D3, D5, D6, D7 and D8 stand.

**Why.** DL-250's amendment (the operator, 2026-09-30) asks for the *guided* reasoning, the structure
`dspy.ChainOfThought(..., rationale_field_type=GuidedReasoning)` imposes, recorded so it can be scored
later for completeness and truth (S247).
[S246](sprints/sprint-246-every-debate-turn-records-how-it-read-the-evidence.md) settles DL-250's open
runtime placement as option (b): DSPy renders and parses offline into a golden fixture, and the runtime
reproduces both without importing it. These are the builder's decisions inside it; the planner's
recommendations were taken for D1 and D4.

**Measured before deciding (DSPy 3.3.1, read in source and run).** `ChatAdapter.format_system_message`
is the field-description block, `\n`, the structure block, `\n`, then the task description, which is
`textwrap.dedent(instructions)` split with `str.splitlines()` and each line prefixed with `\n` plus 8
spaces: blank lines are indented too, a trailing newline disappears, and common indentation is
removed. The user message is the three input sections and one output-requirements sentence joined by
a blank line, then stripped. `parse` splits `completion.splitlines()` on `\[\[ ## (\w+) ## \]\]`
matched at the start of each stripped line (the rest of that line is content), keeps the **first**
section of each name, ignores a preamble and unknown headers, strips each section, and never needs
`[[ ## completed ## ]]`. A typed field goes through `json_repair.loads`, then `ast.literal_eval`, then
pydantic. `ConfigDict(frozen=True)` leaves the rendered JSON schema byte-identical; `extra="forbid"`
or `"allow"` adds `additionalProperties` to it.

**D1 — the frozen text lives in `kernel/deliberation_guided_format.py`; a CI test proves it equals the
golden.** Three literals: `GUIDED_TURN_PREFIX` (DSPy's field-description and structure blocks, with the
`\n` that follows each), the objective lead (*"In adhering to this structure, your objective is: "*)
and the user message's output-requirements sentence. Newlines are written as `\n` escapes, so the
trailing spaces DSPy emits stay inside string literals. B1 compares all three, and whole rendered
messages, with `tests/fixtures/deliberation_guided_golden.json`, which only
`scripts/render_guided_turn_golden.py` writes. A second test recomputes `GuidedReasoning`'s JSON schema
with pydantic the way DSPy does (type key first, `ensure_ascii=False`) and requires it inside the
prefix, so editing a field description without regenerating the golden fails CI. *Rejected:* (a)
**render the schema at import from pydantic.** A pydantic upgrade would then change a live prompt with
no diff in our code, and DSPy's field-description block cannot be derived without DSPy anyway. (b)
**the runtime reads the golden.** `tests/` is in no image, and a runtime reading a test fixture inverts
the tree. (c) **the literals inside `kernel/deliberation_guided.py`.** ~35 literal lines beside the
models and the parser crowd the 200-line block, and a separate module lets `PROMPT_MODULES` name
exactly the text the model reads.

**D2 — the turn `text`: readings, gaps, argument, every value verbatim.**
`Readings:` then one `- <metric> = <value>: <meaning_here> (<bears_on>)` line each (or
`Readings: none`), `Gaps:` then one `- <gap>` line each (or `Gaps: none`), then `Argument: <argument>`.
No number formatting: `value` is the string the model copied, printed as written. Rounding or
normalising it would show the opponent and the judge a value the model never wrote, and S247 compares
the string with the packet. *Rejected:* (a) **argument only.** The judge loses the definitions it reads
today inside the free text (the spec's road not taken). (b) **the reasoning as JSON in `text`.** The
opponent and the judge read prose, and it roughly doubles the transcript's tokens. (c) **the raw
completion with its `[[ ## … ## ]]` markers.** It puts DSPy's field headers into the next speaker's
transcript section. It remains the fallback when the reasoning cannot be read, because then there is
nothing typed to render.

**D3 — the `reasoning_error` vocabulary, bounded at 500 characters like `failed_open_reason`.**
`missing field: <names>` (a required section is absent, names in signature order);
`invalid JSON in reasoning: <json error>` (the named deviation: DSPy would repair it);
`schema: <location>: <message>` plus `(+N more)` (valid JSON that is not a `GuidedReasoning`, first
pydantic error; `(root)` when the location is empty); and, at the turn level,
`empty field: argument` (the argument section is present but blank). The parser returns exactly what
DSPy returns there (an empty string); the turn does not render it, because `Argument: ` with nothing
after it is an empty turn dressed as a readable one (`DLIB-NEV-07`), so the raw text is kept and the
reason named. The completion is never copied into the error: it is already the turn's `text`.
*Rejected:* (a) **exception class names** (`AdapterParseError` says nothing a reader can act on); (b)
**pydantic's full error list** (unbounded, and some messages echo input values); (c) **a numeric
code** (unreadable in the graph).

**D4 — the packet is stored once per order, at `debates[ticker]["decision"]` and `["context"]`.** Every
turn of an order reads the same packet, so one copy per order suffices; four copies per transcript row
would quadruple the largest string on the node. It is recorded whenever the proposition was built,
including a fail-open after that point, because the roles were given it; it is `None` only when
building it failed. Not on `LLMCall`: `DLIB-OUT-05` forbids prompt text there. *Rejected:* per
transcript row (4× the bytes); a separate label (a vocabulary change and a full `up` for no reader).

**D5 — how the guided user message renders the transcript.** One `[<role> r<round>] <text>` line per
turn, joined by `\n`, or `(none yet)`: `render_debate_prompt`'s line shape without its two-space
indent, which only existed to sit under a `DEBATE SO FAR:` heading that the `[[ ## transcript ## ]]`
section replaces. *Rejected:* `render_debate_prompt` whole (it repeats the decision and packet the
message already carries as sections, doubling the largest input); JSON turns.

**D6 — parse parity, and what stays as today.** `parse_guided_turn` mirrors `ChatAdapter.parse` line
for line (same regex, stripped-line match, first section wins, preamble and unknown headers ignored,
marker optional) and differs only in `json.loads` + pydantic, where DSPy runs `json_repair` and
`ast.literal_eval` first. A fenced reasoning (```` ```json ````) is the same deviation class and is in
the golden so F1 can see it if it happens. Unknown keys are dropped exactly as DSPy's pydantic does;
forbidding them would add `additionalProperties: false` to the rendered schema and turn a harmless
extra key into an unreadable turn. An empty completion still raises `empty_debate_turn`
(`DLIB-NEV-07`); a stopped or failed call still fails the order open (`DLIB-FAIL-01`); an unreadable
reasoning does neither (`DLIB-OUT-06`).

**D7 — the replay and eval harnesses keep the free-text path, and that is a known divergence.**
`kernel.deliberate`, `orchestration/deliberation_replay.py` and `scripts/deliberation_eval.py` still
render `render_debate_prompt`, so `scripts/deliberation_reproducibility.py` will count every
post-S246 `defender:r1` turn as `mismatched`. The new `prompt_recipe_hash` on those rows is what says
the renderer changed (`DLIB-OBS-07`); S247 owns moving the harnesses.

**D8 — `max_tokens` 4,096 → 8,192.** Challenger max 3,026 output tokens and p95 2,720 since
2026-09-01 (0 stopped at the cap); the readings add an estimated 400–700 per turn. 8,192 is the
tunable's own ceiling, and billing is per generated token, so an unused cap costs nothing.

---

## DL-251 - the referee's champion prompts are rebuilt from pack-side sources, and every fact they state about our code has a named pin - status: DECIDED (builder, 2026-09-30; S245)

**Why.** DL-250 measured the defect: `CHALLENGER_SYSTEM` and `JUDGE_SYSTEM` tell the model the staleness
gate counts calendar days (false since S87), carry a stale name-correlation case, and the compile
pipeline starts from those promoted constants, so a re-run doubles them (13,023 vs 6,764 chars).
[S245](sprints/sprint-245-every-fact-the-referee-is-told-is-pinned-to-the-code.md) removes both cases
and pins the rest (`DLIB-NEV-09`). These are the builder's decisions inside it; the planner's
recommendations were taken for D1–D3.

**D1 — the bases and the calibration live in `scripts/deliberation_prompt_sources.py` (`Agent: tooling`).**
It holds the challenger and judge bases (the champion text before *" Compiled calibration from the
existing Class-1 library"*, which matches the hand-written prompts `kernel/deliberation.py` held before
the S121 promotion, `14aa9278^`), the judge's pipeline sentence (*" If the Challenger catches …"*), the
Class-1 calibration and the challenger calibration. `_ROLE_INSTRUCTIONS` starts from them. The kernel
keeps only the promoted literals the runtime reads, and the runtime never imports `scripts/` or `dspy`.
The defender's base stays `kernel.DEFENDER_SYSTEM`: it has never been promoted (DL-186), so its
champion *is* its base. *Rejected:* (a) **kernel constants.** ADR-0012's S232 correction already lists
`kernel/deliberation_prompts.py` as trading residue in the substrate, and the module is in
`PROMPT_MODULES`: compile-only text there would move `PROMPT_RECIPE_HASH` on edits no role ever reads,
so `DLIB-OBS-07` would report a new renderer for an unchanged prompt. (b) **Inside
`compile_deliberation_prompts.py`.** It is 185 lines, so the bases would push it past 200, and the facts
tests would import a CLI to read prompt text. (c) **Cutting each base out of the kernel constant at
import.** A `scripts/` module reading `CHALLENGER_SYSTEM` is the doubling trap again, and A2 would be
true by construction. (d) **A second copy of the defender base in the sources module.** That is two
copies of one hand-written text, one of them the runtime's, with no rebuild check between them. The
doubling guard in D5 covers a future defender promotion instead.

**D2 — the pin registry is two dictionaries in `tests/test_deliberation_prompt_facts.py`.**
`DISTINCTION_PINS` maps each distinction sentence, verbatim, to its pin test; `CASE_PINS` maps each
Class-1 case name to its pin test. The values are the test functions themselves, so an entry cannot
name a check pytest never runs (A7 asserts each is a `test_*` function of that module). A7 parses the
distinctions from the champion constants, not from the sources, because the constant is what the model
reads. It compares sets for **equality**, both ways, so a pin left behind for a removed fact fails too
and the registry cannot turn into a list of facts no longer told. The parse runs from *"Preserve these
distinctions:"* to the first sentence-ending period (a `.` followed by whitespace). The spec's *"first
`.`"* would stop inside *"Alpha158 weight 0.00"*. *Rejected:* (a) **the registry in `scripts/`** beside
the sources. The checks are tests and belong where pytest runs them; `scripts/` importing `tests/`
inverts the tree. (b) **Pins discovered by a docstring tag or a decorator.** That is implicit: a
mistyped tag unpins a fact without a sound. (c) **String-match pins** (the spec's road not taken). A pin
must fail when the code changes. (d) **Parsing the distinctions from the sources.** That proves the
sources are pinned, not what ships. A2 ties the two, but the check belongs on the shipped text.

**D3 — the golden is edited and the edit recorded; it is not re-frozen.** Both names leave `passing`
and `fractions`, and a `corrected` key says what was removed, when and why. The four surviving
fractions are the 2026-07-08 freeze's, untouched; `deliberation_gate.py` reads only `passing`,
`fractions`, `model`, `judge` and `date`. *Rejected:* (a) **Re-freeze.** It is paid, and the golden's
models (`gpt-5.5` debaters, `claude-opus-4-8` judge) are not production's (`claude-opus-5`): item 97.
(b) **Leave it.** `check_robust` computes `regressed = golden_passing − candidate`, so
`calendar-staleness` would read as regressed on every future check; A8 pins that the golden names only
live cases. (c) **Drop `fractions`.** That loses the only recorded evidence for the four live cases.

**D4 — regeneration runs through the injected fake `dspy_module`.** `DSPyPromptOptimizer.compile_prompt`
imports `dspy` only to prove it is installed and then joins strings (`kernel/dspy_optimizer.py:33`), so
the fake gives the bytes the real module would. `dspy` is in the `optimizer` extra, which this container
does not install, and the CLI has no switch for the fake, so the regeneration calls
`compile_artifacts(..., dspy_module=types.SimpleNamespace())` from Python with `claude-opus-5` for both
model stamps and version `2026-09-30-s245-v6` (S121's promotion was `v5`). Only `CHALLENGER_SYSTEM` and
`JUDGE_SYSTEM` are re-promoted, in the same 80-character literal chunks as before.

**D5 — the reach of `DLIB-NEV-09`, and what A2 guards.** (a) Every role prompt, the defender's
included, names three example *"system parameter[s]"* (`max_daily_move_sigma`, `base_min_confidence`,
`max_sector_pct`). Those are existence claims about this system, so each is pinned to its live settings
field; no prompt text changes. (b) A2 compares all three rebuilt artifacts with the committed ones
(system prompt and examples), and the challenger and judge with the kernel constants. It also requires
*"Compiled calibration"* and *"Examples:"* exactly once in every rebuilt prompt, which is the doubling
guard for a future defender promotion. (c) A static check: no module in `scripts/` imports
`CHALLENGER_SYSTEM` or `JUDGE_SYSTEM`. `compare_deliberation_prompts.py` and `deliberation_gate.py`
still read `DEFAULT_DELIBERATION_PROMPTS`, to *evaluate* the champion, never to build an instruction;
that stays. (d) A4 is pinned twice: on `size_quantity` (20; the floor; exactly three parameters) and
at PM level through `evaluate_recommendations`, since an existing helper builds a buy in a few lines
(beta 0.5 vs 2.5, `atr_pct` 1.0 vs 6.0, the same price: the same quantity). *Rejected:* widening A7 to
the defender's artifact (never promoted, never read by the fleet) or to the Class-2 examples
(hypotheticals, item 75).

**Measured while pinning (A3).** The pooled-sigma example says *"one 9% name does not trip it"*. On a
99-name session at ±1.5 % the +9 % mover is **5.11σ** and passes; on a calm ±0.5 % session the same
move is **8.66σ** and is excluded. The distinction (*"pooled cross-sectional sigma is not per-name
volatility"*) holds either way; the example sentence holds only on an ordinary day. Rewording a case is
a new eval case with an unmeasured effect (item 75/97), so the text is unchanged and this is reported.

**Planner, at merge (2026-09-30): the ADR-0010 firewall.** The 20-call challenger replay stands in for `deliberation_gate.py --check` for S245. The golden is frozen on `gpt-5.5` debaters and a `claude-opus-4-8` judge, and production runs `claude-opus-5` for every role, so a `--check` would test models production does not use against a baseline measured under the old prompts. The replay measures the change's purpose directly: the old champion asserted calendar-day counting in **8 of 10** recorded propositions, the new one in **0 of 10** ($1.45). *Rejected:* (a) running `--check` anyway, ≈ $6–12 for a signal about the wrong models; (b) re-freezing the golden on `claude-opus-5` inside this merge, a paid baseline design that belongs to work-queue 97.

---

## DL-250 - the referee reads ~60 quants with no definitions, and one of its six hard-coded facts has been false since before it was compiled - status: MEASURED; direction DECIDED (operator, 2026-09-30; work-queue 96, 97)

**The operator's question.** How does quant data reach the first deliberator call and what does the model
start out knowing? How do we make the debate use our parameters and read them the way *this* system
means them? And does DSPy (3.3.1 installed; the operator's "2.x" was a typo) give us that foundation?
DL-186 answered the first half on 2026-09-20. This entry re-measures it on a real packet, reads DSPy's
source for the mechanism, and proposes the build.

**(a) What the first call receives, rendered from the spine** (`pm-run-d622b85f…`, 2026-09-29, first
approved order, via `orchestration/replay_corpus.py`'s own path, read-only). The defender's round-1 call
gets `DEFENDER_SYSTEM` (**434 chars**: role, "define each parameter first", "max ~5 sentences") and one user
message: `DECISION UNDER TEST: buy TXN (qty 3)` plus **9,587 bytes** of `name=value` lines. **What it
knows about this system: its pretraining, plus whatever the names suggest.** Around 60 metrics arrive
stamped `source-owned-units-scope-unknown{…}`. Four traps sit in that one packet, each checked in code:

| In the packet | What it looks like | What our code computes |
| --- | --- | --- |
| `pe=30`, `pb=20`, `current_ratio=70`, `debt_equity=65` | the P/E is 30 | 0–100 banded **sub-scores** (`fundamental_rules.py`). P/E 41.92 misses both bands and gets the default 30 |
| scanner `relative_strength=0.5247` vs analyst `relative_strength=8.091` | one metric | two metrics: the scanner's is the ticker's **raw total return** as a fraction, not relative to anything (`scanner/domain/filters.py:112`); the analyst's is **ticker minus benchmark**, in percentage points (`relative_strength.py:36`) |
| `atr_pct=2.935`, `favorable_excursion_pct=0.06321`, `atr_pct=2.93%` | one `_pct` convention | three scales: percent points, fraction, pre-formatted percent |
| `stochastic_k=95.66 → stochastic_k_score=20`, `rsi2=100 → rsi2_score=20` | overbought = strong | the bands are **contrarian** by design: overbought scores bearish (`technical_rules_range.py:40`, `technical_rules_event.py:41`); nothing in the packet says so |

The `reward_risk` gate also renders `threshold=0 -> PASSED` with `comparison=DISCLOSURE_ONLY`: a gate
that cannot fail, reported as passing.

🚨 **A false fact is live in the referee.** `CHALLENGER_SYSTEM` and `JUDGE_SYSTEM`
(`kernel/deliberation_prompts.py`) state that *"our staleness gate counts CALENDAR days, not trading
sessions"*. The challenger is also told to argue that exact flaw ("that is the decision flaw under
test"). **The code has counted trading sessions since S87** (`d00739e0`, DL-10;
`agents/provider/settings.py:53`). The Class-1 case library predates that fix. S119's compile of
2026-07-08 copied the case into both prompts, and nothing connects a prompt sentence to the code it
describes. A second example is **stale by omission**: *"four semis each pass the sector cap, so add a
fifth"* now meets `correlated_cluster_pct` (S210 / ADR-0030), which the same TXN packet shows running.
The other four distinctions still hold today (pooled sigma, fixed-fraction `size_quantity`,
`alpha158_pillar_weight=0.00`, LightGBM only in the forecaster). They are still one refactor away from
the same rot.

**What "DSPy" does today: nothing at run time or at compile time.**
`DSPyPromptOptimizer.compile_prompt` (`kernel/dspy_optimizer.py:33`) imports `dspy` only to prove it is
installed. It then joins the instruction and examples with `"\n".join`. No `Signature`, adapter or
optimizer has ever run. That is why S119's report shows **understanding 17 % for champion and
compiled prompts alike**: a string concatenation cannot move it.

**DSPy 3.3.1, read in its source and confirmed by rendering a probe signature through `ChatAdapter` and
`JSONAdapter`.** These mechanics decide the design:

1. **An input field's `desc` goes into the system message** ("Your input fields are: 1. `x` (type): desc"). Pydantic bounds `ge`/`le` render as a `Constraints:` line. The signature docstring becomes
   the `objective`.
2. 🪤 **A Pydantic model used as an *input* type loses its field descriptions.**
   `translate_field_type` returns an empty note for input fields, so the model sees only
   `dict[str, Metric]` and a JSON dump of the values. A glossary written as `Field(description=…)`
   inside the input model **never reaches the LLM**. Meaning has to travel in a top-level `desc`, in a
   dedicated glossary field, or inside the value itself.
3. **An *output* Pydantic model renders its full JSON schema, descriptions included.** `Literal`
   outputs render as *"must exactly match one of"*. The output side is where a grounding contract can be
   enforced.
4. **`prefix`, `format` and `parser` are deprecated no-ops.** `dspy.Assert`/`Suggest` are gone;
   `dspy.Refine` and `BestOfN` take a reward function. `dspy.History` carries multi-turn transcripts.
5. **GEPA rewrites only each predictor's instructions** (`signature.with_instructions`). It never
   changes field descriptions. Its metric may return `(score, feedback)` per predictor
   (`GEPAFeedbackMetric`), so the answer key can explain *why* a reading was wrong in words.
   MIPROv2 searches instructions plus demos.
6. **`program.save()` / `dump_state()` serialise instructions and demos as JSON.** Loading them needs
   `dspy`, and no Dockerfile installs it (DL-184, the diskcache advisory).

**The resolution of DL-186's open trade-off (better definitions are also hints).** Separate
**definitions** from **findings**:

- A **definition** says what our code computes. It is true of every order, generated from code, and
  given **identically to all three roles**. Example: *"`sizing` = portfolio_value × max_position_pct ÷
  price; stop distance and volatility do not enter it."*
- A **finding** says what is wrong with *this* order. It must be argued from the packet and must never
  appear in a prompt.

The circularity DL-186 found (the AMZN veto repeating a sentence we wrote) came from putting findings
in the challenger's prompt alone, phrased as things to attack. Symmetric definitions give the defender
the same knowledge, so they point neither side at a verdict. **Test for any sentence in a prompt: if it
is not true of every order, or cannot be regenerated from code, it does not belong there.**

**Proposed build, in order** (fix first, per the standing rule):

1. **Fix (work-queue 96, PATCH).** Remove the false staleness distinction and its example from the
   challenger and judge prompts. Re-state or remove the stale correlation example. Pin each surviving
   fact to the code it describes with a test that reads the code's own value (e.g. `unit="sessions"`
   on `max_staleness_days`), so the next rot fails `make ci`.
2. **Names that cannot be misread (work-queue 97a).** Rename at the render boundary:
   `pe` → `pe_subscore_0_100`, scanner `relative_strength` → `trailing_return_frac`, and one `_pct`
   convention. Deterministic, costs nothing, and removes the traps above before any glossary exists.
3. **A generated glossary, the same for all roles (97b).** Thresholds come from `tunable(why=, unit=,
   ge=, le=)`, which already exists. Metrics come from a new pack-side registry owned by the rule tables
   that compute them (the band table *is* the definition). Render only the keys present in the packet.
   Place it in the system message, where it is stable across orders and cacheable. Add its source to
   `PROMPT_MODULES` so the recipe hash tracks it.
4. **A grounding contract on the output (97c).** Model each turn and the ruling as DSPy signatures with
   typed outputs: `citations: list[Citation(metric, value, meaning_in_this_system, bears_on)]`, then
   `argument`, and for the judge `ruling: Literal[...]` plus `decisive_citation`. A deterministic check
   runs after every live call: the metric exists in the packet, the value matches, and the stated
   meaning passes `score_understanding` (`kernel/deliberation_understanding.py`, which already exists
   but only runs in eval). A misread is recorded on the `DeliberationRun`, not discovered months later.
5. **Real optimisation, offline (97d).** GEPA over each role, with feedback text taken from the answer
   key (*"you read `pe=30` as a P/E of 30; here it is a 0–100 sub-score and the P/E is 41.92"*). Train
   on a **balanced** set drawn from the replay corpus (upholds, revises and overturns; item 75), not
   the flaw-only Class-1 library. Export the adapter's rendered system and demo messages as the
   `PromptArtifact`. A parity test pins the runtime renderer to `ChatAdapter.format` on a fixture.
   **State a call and dollar budget before running**: S173 Part B stopped at $58.05 for one round.

**Rejected.** (a) **Install DSPy in the deliberator image and call `dspy.Predict` live.** It re-imports
the advisory DL-184 kept out of every image, and adds litellm to the hot path to render text we can
render ourselves. (b) **Descriptions on a nested input Pydantic model**, the shape of the operator's
snippet applied to inputs: measured above, they never reach the model. (c) **A meaning string inline on
every value.** It reaches the model, but it repeats ~60 definitions per turn per round, where a glossary
states each once in a cacheable prefix. (d) **Keep hand-written "distinctions".** One of six was false
at the moment it was compiled, and nothing could have caught it. (e) **Persona.** Still rejected;
DL-186's reasons stand.

🪰 **Denominator.** One packet, the first approved order of one run. The traps are properties of the
renderer and the rule tables, so they recur on every packet carrying those keys. How often the model
actually *misreads* them is not measured here: that is what 97c's contract measures on every live
debate.

🚨 **AMENDMENT, same day — the operator's direction: record the *guided* reasoning; and what the model
already does unseen.**

**Correction.** The rendered packet above is from **`sched-2026-09-28`** (the PM run was created
2026-09-28 22:40 UTC), not "2026-09-29".

**The direction (operator, 2026-09-30).** *"Record thoughts to be able to assess them for completeness
of quant data and truth"*, and then: *"not the LLM thought notes. This is also gold, but the GUIDED
thought process of the DSPy when it is processing chain of thought."* The recorded artifact is the
reasoning the model writes, **before its answer, into a structure we define**:
`dspy.ChainOfThought(signature, rationale_field_type=<typed model>)`. Measured in 3.3.1 by rendering
and parsing a probe, with no LLM call:

- The output order is `['reasoning', 'ruling']`: the guided reasoning is produced first.
- Each step's description reaches the model through the JSON schema (*"step 1: read every quant you
  rely on; define before using"*).
- `ChatAdapter.parse` returns a typed object ready to store, for example
  `readings[0] = {metric: "pe", value: 30.0, meaning_here: "0-100 banded sub-score…"}`.

The assessment runs on that record, in code rather than with an LLM judge:

- **Completeness:** the readings cover the packet's *material* quants (failed and near-threshold
  gates, warnings, the stop basis), which is a set computed deterministically from the packet.
- **Truth:** every `value` equals the packet, and every `meaning_here` passes the answer key
  (`score_understanding`).

The failures, stated in words, become GEPA's feedback.

**What this changes in work-queue 97's order.** Guided reasoning and its recording come **first**, on
today's packet, so the baseline misread rate is measured before anything changes the packet. Then
names, then the glossary, then GEPA, each measured against that recorded baseline.

**The model's own thinking ("also gold").** Measured, not assumed:

- All three roles run **`claude-opus-5`** (`LLMCall.model` since 2026-09-20).
- On Opus 5, omitting `thinking` means adaptive thinking **is on**, and the thinking text comes back
  empty by default. `kernel/llm_anthropic_responses.py:49-53` keeps only `text` blocks anyway.
- `sched-2026-09-28`: 60 calls, **73,635** output tokens billed. The visible turns average ≈ 305
  words, about 20,000 tokens in total (estimated at 1.3 tokens per word). **≈ 73 % of billed output
  is reasoning we never see.**
- `thinking: {"type": "adaptive", "display": "summarized"}` returns a summary at the same token cost.
  The raw chain of thought is not returned by any model, and nothing here should try to obtain it.
- A summary can show a misread but cannot prove an omission, because it may leave out a quant the
  model used. So the guided reasoning is the primary record and the summary a secondary one.

**Runtime placement: open, decided when 97 is packaged.** No image installs `dspy`, and DL-184's
accepted diskcache advisory rests on "installed by 0 of 15 Dockerfiles". The two options:

- **(a)** The deliberator image installs `dspy` and uses its adapter to format and parse. The call
  still goes through our `LLMClient`, so the ledger, stop reasons and outage handling stay. This
  changes an accepted advisory's premise.
- **(b)** DSPy renders offline, and a runtime parser is pinned to `ChatAdapter` by a parity test.
  This keeps a second parser in sync.

**Also measured today, and handed to [S245](sprints/sprint-245-every-fact-the-referee-is-told-is-pinned-to-the-code.md).**

- **The false fact is used, not just carried.** 180 of 936 recorded turns mention calendar-day
  staleness; **150 assert it, 0 state session counting**; challenger 169, defender 11; 18 of 38 runs,
  2026-08-07 → 2026-09-29. The challenger quotes the planted sentence nearly verbatim.
- **The compile pipeline is not idempotent.** It starts from the *promoted* constants, so a re-run
  doubles the prompt (challenger **13,023** vs **6,764** chars).
- **The golden firewall no longer tests production's models.** It was frozen on `gpt-5.5` debaters and
  a `claude-opus-4-8` judge, while production runs `claude-opus-5` for every role. Re-freezing it is
  paid, and belongs to 97.

🚨 **AMENDMENT 2, 2026-09-30 15:22 AEST — terms are defined in the prompt; no debate role gets
internet access** (the operator's question; the planner's decision, delegated).

**The question.** *"I see a lot of numbers in the prompt, I do not see discussion citing numbers. We
either give the LLM access to internet, or explain what terms mean in the initial message/prompt."*

**Measured first: the debaters cite numbers; they do not understand them.** *[measured 2026-09-30,
read-only, no LLM call]* 772 recorded turns from 35 real `DeliberationRun`s, each matched to its own
packet through `source_pm_run_id` and `orchestration/replay_corpus.py` (synthetic `verify-*` runs
excluded). **759 of 772 (98.3 %) quote at least one packet number verbatim.** A turn quotes on
average **7.2** packet numbers and names **9.0** packet metrics (defender 9.4 / 10.8, challenger
5.1 / 7.2). A number counts only if it has a decimal point or at least 4 digits, so *"5 sentences"*
never matches. The page the operator read showed the round-1 *input*, whose transcript is empty,
which is why no discussion appeared on it. The defect is comprehension: S119 read understanding at
**17 %**, and 150 turns asserted the false calendar-day fact while quoting numbers correctly.
**0 of 772** turns carry a typed reasoning, because S246 is merged and not deployed.

**Decision: define the terms in the prompt.** These are steps 2 and 3 above, work-queue 97 (b) and
(c), unchanged: names that cannot be misread, then one glossary generated from code and given to all
three roles in the cacheable system message.

**Rejected: internet access for any debate role.**

- **The web cannot know what our code computes.** No search says that `pe=30` in our packet is a
  0–100 sub-score while the P/E sits in the same packet as `peTTM=35.84`. It cannot say that the
  scanner's and the analyst's `relative_strength` are two different metrics, or that our oscillator
  bands are contrarian. A web definition pulls the model toward the general-finance meaning, which
  is the misreading this entry measured. `meaning_here`'s own schema rules it out: *"in THIS
  system, not in general finance"*.
- **Replays would stop being replays.** A recorded debate re-run later would read a different web,
  which breaks the replay corpus and the golden firewall.
- **Fetched pages would enter the prompt of a system that places orders.** That is an injection
  surface.
- **It adds cost and latency to every turn** against a tight LLM budget.

**Glossary denominator.** *[measured, same pass]* **73** distinct source-owned keys across 371
packets. This is the finite set that step 3's registry must define.

**Sequence (proposed).** Retag S246 first, so live turns record `meaning_here` against today's
packet: that is the baseline. The records persist on `DeliberationRun`, so S247's scorer can grade
the baseline after the fact. The names-and-glossary sprint therefore waits only for baseline runs to
exist, not for S247's code.

🚨 **AMENDMENT 3, 2026-09-30 17:55 AEST — all of it, with explicit meanings, for all three roles**
(operator direction; planner inventory).

**The direction.** *"Whatever can be calculated about a trade should be given to deliberators. ALL OF
IT. What we need is to determine if the agents understand fully what they are discussing. The
instructions should be explicit."* It widens the packet boundary that `build_veto_context` states today
(*"this packet contains no holdings, open positions, sibling orders, or dual-class exposure facts"*), and
makes three things the target: complete facts, an explicit meaning for each, and proof of understanding
for the defender, the challenger **and the judge**.

**Measured the same day** ([R009](research/dspy/INDEX.md)). Over 229 debated orders the judge names a
quant metric in 40.2 % of rulings and rests 38.0 % on process facts alone, and S246 guides only the two
debaters. The inventory ([packet-inventory](research/dspy/packet-inventory.md)) lists what is computed
before the debate but never shown: the barrier forecast (`p_stop_first`, `p_target_first`, `p_neither`;
present for 10 of the 12 orders debated on 2026-09-28), the forecaster's settled track record, current
holdings and cash, the other orders in the batch, past fills in the ticker, the VIX's staleness, and the
order's own `decision_atr_pct` and `position_ref`.

**Blocked by a law, for the operator.** The deliberation veto is `binding` on every recent run, so a
barrier forecast shown to the deliberators would take part in gating. `FORE-NEV-02` forbids that (*"Never
gates, vetoes, or blocks a recommendation, sizing, or exit"*). Including forecasts needs the operator's
decision and a forecaster law cycle. Every other missing row is a renderer omission.

✅ **AMENDMENT 4, 2026-09-30 18:40 AEST — decided: the barrier forecast waits for its own track record; every other fact goes in** (the operator agreed the planner's recommendation).

**Decision.** `FORE-NEV-02` is **not** amended now. The deliberators decide from the facts about the trade, which all go
into the packet (work-queue **98**). The barrier forecast joins them only when the live `barrier_scorecard` reports
`skill_lo > 0`, and then always beside its scorecard (work-queue **99**, parked with that trigger).

**Why.** *[measured 2026-09-30]* The forecaster has stated 15 live claims since 2026-09-28 and **none is settled**; each
needs 10 sessions. DL-240's rule is that nothing acts on a probability until a ledger shows it comes true, and
`FORE-NEV-02` is pinned green by two tests that keep every other module from reading the ledger. The goal set in
amendment 2 is to prove the deliberators *understand* the evidence: a crisp, unproven probability in front of a binding
veto invites them to defer to it, and a deferring ruling would look evidence-based while measuring nothing.

**Rejected: amend `FORE-NEV-02` now** (the operator's first instruction, withdrawn the same hour). It also could not land
as a text edit: §5 of the conventions forbids the forecaster's book to name the reader, so the conditions (*shown with its
track record*, *never decides alone*) belong in the deliberator's book, and the two green isolation tests would have to be
widened in the same change. **Rejected: never show it.** The debaters ask for exactly this (18 of 19 guided turns name a
missing stop-out probability or similar), and a forecast that beats climatology live is evidence like any other.

---

## DL-240 - the book is managed as a distribution: short holding periods on stocks we buy, and exits that take profit - status: DIRECTION (operator, 2026-09-28); design open, work-queue 92

**The operator, 2026-09-28:** *"we need to think about how we manage stocks. We need to be able to
determine if a ticker needs to be dropped/upped/lowered in volume … accommodate short term investment
strategies, like two week, like over the weekend … We need to sell at profit."* Asked whether "short"
meant short selling: **no — short holding periods on stocks we buy.** Then: *"we need to treat the
portfolio as a distribution."*

**Why now.** S238 (deployed `s238` the same day) ends the scanner's starvation: approvals were measured
to rise from a median 2 to 13 a session and the book (~24 % invested) to fill within days. Once it is
full, what the book sells decides what it can buy.

**What the fleet does today** *[read from the code, 2026-09-28]*:

- The only exit that fires is the **protective stop** (the broker's resting GTC stop, 3.9–7.3 % below
  entry; the analyst also sells a held name on `stop_breached`).
- The **thesis exit** never fires: `recommend.py` sells a held name only when confidence falls below
  `exit_confidence_floor`, which is 0 (ADR-0027 Correction 2).
- **Targets are computed, never acted on:** every buy carries `target_pct`; the monitor has
  `default_target_pct` 0.10 and `default_horizon_days` 14, but `exit_rules.evaluate_position` observes
  only the stop, and nothing places a take-profit order or a time exit.
- **A sell is always a full exit** (`portfolio_manager/domain/exits.py`); nothing trims or adds.

So losses are realised automatically and gains never are.

**"The portfolio as a distribution" — the planner's reading, to be confirmed:**

1. **Each position is a distribution** over its outcome by its horizon: the chance it reaches its target
   first, its stop first, or neither, and the return in each case.
2. **The book is the aggregate** of those distributions: an expected return and a left tail at the
   horizon. Drop, trim, add and take-profit are chosen by how they move that aggregate, not name by name.
3. **The book is a mix of holding profiles** (for example a Friday-to-Monday hold, a ~10-session swing,
   a longer hold), each position carrying its own exit plan from entry, so capital recycles as the short
   slots close.

**Link to work-queue 71 (parked regime-probability track).** Reading 1 is exactly EXP-011's barrier
probability, and EXP-011 already measured where to begin: a ledger of declared against realised
probabilities, starting with S211's own claim that the median target is reached within 10 sessions about
half the time (**50.2 %** historically). *Proposed, not decided:* item 71's step (1) becomes a step of
this track rather than staying parked. The operator parked 71 "until the debt settles and we are ready";
that is theirs to lift.

**Sequence (planner, delegated):**

1. **Item 91 first.** Trim, add and take-profit decisions need each holding's current value; the PM still
   values held names at their adoption-day mark (DRIFT-079).
2. **Measure the book as it stands** (read-only, $0): how positions have closed, and how many sit above
   their target now.
3. **Pre-register an exit experiment on the replay cache** (as EXP-015 was; $0 LLM): stops only (today,
   the champion) against take-profit at the PM's target, a time exit at ~10 sessions, a trailing stop, and a
   Friday-to-Monday hold. The first ten-year smoke (stops only) read +217.9 % against exposure-matched SPY
   +232.2 %.
4. **Build the winner in increments.** The likely first: the target becomes a resting sell beside the
   stop (a bracket / one-cancels-other). Then holding profiles recorded on the `OrderIntent`. Trimming and
   adding last, with their own law cycle.

**Ruled out:**

- **Short selling.** The operator: short holding periods on stocks we buy. Short selling would be a
  separate capability with its own capital-risk policy.
- **Intraday strategies.** The fleet decides once a day after the close and trades at the next open;
  weekend and two-week holds fit that cadence, intraday does not.
- **Installing ABIDES** (operator, 2026-09-28: *"install ABIDES if we need it"*; planner: not needed). It
  simulates an exchange's order book tick by tick (order flow, queue position, intraday impact). The
  outcomes here are daily paths over 1–10 sessions, which daily-bar models answer; ABIDES would earn a
  place only for intraday execution or market-impact questions, which this book's size does not raise.

**Stays the operator's:** the mix of holding profiles and any cap on it is capital-risk policy.

**Amendment — the operator, 2026-09-28: the meaning is moonshot #1.** Answering "the portfolio as a
distribution", the operator pointed to [moonshot #1](moonshots.md): the analyst stops shipping one score per
candidate and emits a distribution (`P(profit > 0)`, `E[drawdown]`, `tail_loss_p99`, `time_to_target`), and
the PM optimises the book over distributions (Kelly fractions, a CVaR budget). Readings 1 and 2 above are
that moonshot; reading 3, the holding profiles, is its time axis. The same object, re-read each day for a
held name, is what decides drop, trim, add and take-profit.

What this repo's evidence changes about the moonshot (planner):

- **Daily return paths, not microstructure.** The moonshot proposed ABIDES (order flow, queue position).
  Nothing of it exists here (checked 2026-09-28), and the fleet decides once a day and fills at the next
  open, so a position's outcome over 1–10 sessions is a question of daily paths. The model runs over daily
  bars: EXP-011's barrier simulation, then a block bootstrap or GARCH, which keep volatility clustering.
- **Calibrated before anything sizes on it.** EXP-011's first model added only ~1 % Brier skill over base
  rates and over-dispersed `P(stop first)`. A miscalibrated probability fed to Kelly over-bets. So the first
  build is the **ledger**: every declared probability recorded at decision time and checked against what
  happened, and every model is a challenger to the base rate.
- **Deterministic**, as the moonshots' own cross-cutting preference asks: simulation and statistics, no
  LLM in the path.
- **Homes.** The forecaster produces the distribution (advisory until its scorecard promotes it, as
  EXP-011 placed it); the PM consumes it; the daily re-read of held names feeds the exits.
- **Kelly / CVaR sizing is capital-risk policy**: the operator's, and the last step.

**Measured 2026-09-28 — [EXP-016](research/experiments/EXP-016-jev-barrier-probabilities.md): Jev is not a
forecaster here** (operator: *"I want to try JEV AI on it"*). On 5,862 of EXP-011's decisions its Brier is
0.84–0.85 against climatology 0.616 and the bootstrap 0.606; alone its probabilities point the wrong way, and
given the bootstrap's estimate it copies the likeliest outcome at ~0.96. The ledger's challengers are
simulation models. Jev's typed-text use (ideas.md) is untouched by this.

**Measured 2026-09-28 — [EXP-017](research/experiments/EXP-017-block-bootstrap-and-garch-barrier-probabilities.md):
GARCH is the model, not yet the ledger.** On 42,456 decisions GARCH(1,1) filtered historical simulation is the only
model with skill on the fleet's 203 bars (+1.47 % over climatology; +2.26 % on full history); the plain bootstrap
has none on 203 bars (−0.49 %), and the block bootstrap is worse than the plain one. The formal GARCH verdict is
INSUFFICIENT (6.2 % fits fell back against a 2 % limit, almost all on the α + β = 1 boundary), and nothing clears
the 2 % bar on production's history. Next: EXP-018, boundary fits accepted, at 203 / 756 / full bars, plus the cost
of a 756-bar SIP request (possible since S238). The build waits on it.

**Measured 2026-09-28 — [EXP-018](research/experiments/EXP-018-garch-history-depth.md): the model is GARCH(1,1)
on ~3 years of history.** With boundary fits accepted (persistence capped at 0.999), its skill over climatology
is **+2.67 %** [+1.88, +3.48] at 756 bars, with 0.39 % failed fits: the first model to clear the pre-registered
bar. At 203 bars +1.57 % (short); full history +2.35 % (three years beats ten). A live 756-bar SIP fetch costs 8
pages and 19 s. **Decided (planner, delegated): the live ledger is built on it**, as a forecaster shadow model
with its own 760-session history request, leaving the scanner / analyst window (a decision path) untouched.
Order: the test-bed chore, sprint A (the forecaster states barrier probabilities for approved buys, a new
append-only record, full `up`), sprint B (settlement ten sessions later and a scorecard). No trading behaviour
changes until an exit experiment on these probabilities passes; sizing on them stays the operator's.

**Done 2026-09-28 — the test bed is repo code** (chore-barrier-testbed, `v0.117.04`): `scripts/barrier_testbed.py`
(`--reproduce` gives EXP-011's 47,485 decisions exactly), `barrier_testbed_models.py`, `barrier_testbed_score.py`;
numpy joins the dev group. *Decided (planner):* **GARCH is not in the test bed.** It becomes forecaster code in
[S239](sprints/sprint-239-the-forecaster-states-how-likely-a-buy-reaches-its-target.md), and the test bed takes any
model function, so one implementation serves production and the parity check (S239's F1). *Rejected:* a second
GARCH in `scripts/`, which would let the experiment and production drift apart. **Specced 2026-09-28: S239**
(sprint A, for a Claude cloud session).

**Work-queue 71 folds into 92** (planner, on the operator's pointer; reversible): its three measured steps
(the ledger, the sticky regime label, barrier simulation only where a decision needs it) become this
track's evidence base. Revised sequence: item 91 → measure the book → **the ledger** (starting with the
claim the system already makes: the median target within 10 sessions, 50.2 % historically) → a
distribution model on the replay cache, pre-registered and calibrated out of sample against the base rate
→ exits and holding profiles chosen by that distribution in replay → build in increments → PM sizing over
distributions last.

**Amendment — a name stopped out is often bought again the same night (measured 2026-10-02).** On
`sched-2026-10-01` the stops on JNJ, C and DE had filled in the session (−$107.05 realised), and the
same run approved and submitted a buy for each at the same quantity. Over the record, **11 of 31**
filled stops were followed by a buy order for the same name in the run that first saw the stop (the
stop `Fill`'s `broker_status_refreshed_at` date equal to the buy's `submitted_at` date). Of the 8
before tonight, 6 filled and are still held with no second stop, and 2 expired unfilled. Nothing in
the scanner, the analyst or the PM reads a recent stop-out, so this is the pipeline behaving as
written, not a defect, and the six that held say it has not cost money so far. It belongs to this
entry's question (what the book does with a name after an exit). The replay harness runs the same
code, so EXP-014's arms include the behaviour. **No decision taken:** a re-entry rule is trading
policy, the operator's to set, and the place to test one is the exit experiment this entry plans.

**Amendment 2 — the same reading on the broker's own orders, with what each second lot did (measured
2026-10-09).** On `sched-2026-10-08` the stops on TMO and DE had filled in the session, and the run bought
TMO again: a limit of $661.63 against a stop fill of $645.43. From Alpaca's closed orders, by fill time:
**14 of 37** filled stops were followed by a buy order for the same name before the next session opened. Two
of those orders expired, one is pending and 11 filled: 6 are up and 5 down, **+$252.34** in total, of which
INTC alone is +$216.01. **3 of the 11 were stopped out a second time** (SCHW, BMY, DE: −$129.81), so a stop
limits the loss on a lot and not on a name (DE: −4.63 % and then −4.89 % within a week). The second lot was
bought above the stop's fill in 6 of 11, by +0.51 % on average. **14 of the 37 stops filled in the first 15
minutes of a session**; TMO's did, at 13:36 UTC, on a day whose low was $635.30 and whose close was $652.00.
Why the run buys again: the stop is tied to the old lot's entry price, the analyst scores the name afresh at
the close, and nothing between them carries the stop-out; the debate's packet does not carry it either.
*[not measured]* how often a stopped name closed back above its stop the same day; any rule on the ten-year
replay. **Proposed, told to the operator (the rule is theirs):** no cool-down on this evidence, because it
would have cost this record $252, INTC's recovery; the packet states the stop-out (the packet sprint of
[DL-280](design-log.md)); *no re-entry for 1, 3 or 5 sessions* becomes an arm of the exit experiment on the
replay, after the fidelity verdict. The first amendment read the graph's refresh dates and counted 11 of 31
a week earlier; script `analysis_b.py`, OneDrive `trading-agents-data/f2-sched-2026-10-08/`.

## DL-237 - E17.4's fidelity bar is re-cut: the harness is judged on the fleet's own inputs, and the data gap is measured, not barred - status: DECIDED (planner, 2026-09-27; S237)

**Question.** The plan's E17.4 bar is *≥ 90 % approved-order membership, replay against live, every
difference explained*. Can that bar tell whether the S235 harness reproduces the pipeline?

**Measured, 2026-09-27 (live spine).** Every scheduled run since `sched-2026-07-07` (**56**) stores
its full `MarketData` snapshot: bars with IEX volume, fundamentals, news, sectors, earnings dates,
and SPY from `09-04`. Every stage stores its output (candidate set, recommendation set with pillar
scores, intents, rejections with reasons, vetoes, fills), and every run stores its broker book. The
fleet was redeployed about **35** times in the window. Only since `s225` (deployed 2026-09-22) is the
scanner, analyst and PM code equal to `main`, apart from 11 `contracts/` files. The PM approves
**0–4** names per session and rejects 21–27. Live PM passes each holding's market value to its caps;
the replay passes none (`scripts/replay_day.py`).

**Decision.** The bar applies to the harness, on the inputs the fleet actually saw. The data gap is
measured and explained, but carries no bar.

1. **Layer 1, harness fidelity (the bar).** Each stage (scanner, analyst, PM) is replayed on that
   stage's **live** inputs and compared per ticker with the live output. The pre-registered bar,
   pooled over **clean sessions** (the deployed decision code equals the replayed code):
   - agreement **≥ 90 %** at each of the three stages (candidate membership and rank; recommendation
     action and confidence within 1e-9; PM decision and reason);
   - **zero `unexplained`** differences. Each difference names `code_changed:<file>`,
     `not_persisted:<field>`, or a `harness:` defect that is fixed before the verdict;
   - a denominator of at least **100** analyst ticker-decisions, else the verdict is `INSUFFICIENT`,
     not `PASS`. Four clean sessions give ~104 *[measured]*, so the export runs after
     `sched-2026-09-28` to add margin.

   `FAIL` stops P17, as the plan says: the named causes become the work.
2. **Layer 2, input attribution (measured, no bar).** The same code chained over the same session.
   One input at a time, cumulatively, in a fixed order: SIP volume, then no fundamentals, no news, no
   earnings dates, and cache bars. This quantifies what DL-232 (price-only) and DL-233 (IEX volume)
   change about the decisions. EXP-014's verdict already speaks only for the price-only pipeline;
   this says how far that pipeline is from the live one.
3. **Layer 3, approval to fill (counted, no bar).** From the live record: approvals, deliberator
   overturns, execution drops and rejections, fills and expiries. It accounts for the absent
   deliberator without replaying it.

**Ruled out.** *The plan's bar as written:* it would fail on two causes already decided (price-only,
IEX volume) and could not tell a harness defect from either. *Chained comparison only:* one early
difference cascades, and nothing says which stage diverged. *Replaying under each night's deployed
code:* ~35 deploys and harness modules that did not exist then, answering a question P17 does not
ask. *A P&L bar against the live account:* the two books diverge from the first different fill; the
number is reported as context only.

**Amendment — planner review of S237's first handback, 2026-09-27: the clean set and the PM denominator.**
Two claims above did not survive the live export. (1) *"Four clean sessions give ~104"* assumed the
11 `contracts/` diffs since s225 were decision-neutral; the rule this entry asks for (the deployed
decision paths equal the replayed code's) marks s225, s227 and s228b non-clean, because the analyst
imports those files. **The clean set starts at `sched-2026-09-28` (s232, 0 files).** Four sessions reach
the analyst floor, so the first verdict is due after `sched-2026-10-01` at the earliest. Non-clean
sessions are still replayed and reported: a non-clean session that matches is evidence, not the bar.
(2) The PM's rows are mostly passthroughs: on `sched-2026-09-25`, 25 of 26 were `hold_recommendation`,
which the PM rejects mechanically. Pooling them would measure the analyst's action field twice. **PM
agreement is taken over judged recommendations (`buy`, `sell`) with its own floor of 10**; passthroughs
are counted beside it. The per-stage rules and floors are in S237's returned item R5. *Rejected:* a
hand-kept allow-list of decision-neutral `contracts/` files (a judgement the tool cannot check);
lowering the analyst floor to keep the earlier date.

**Amendment — the re-run after `sched-2026-10-01` reads INSUFFICIENT, and the plan for four clean sessions was never measured (planner, 2026-10-02).**
The status below said the verdict would be re-run *"when four clean sessions exist"*, and the review
above put the first of them at `sched-2026-09-28`. That assumed the fleet's decision code would stand
still for four sessions. It did not, and I did not check a deploy against the decision paths before
making it.

*Measured 2026-10-02* (export of 60 sessions, replay from `main` at `684441d7`; outputs in OneDrive
`fidelity/live-2026-10-02/`):

- Verdict INSUFFICIENT, **0 clean sessions**, 0 unexplained differences.
- Layer 1 agrees on every judged row of the ten latest sessions (09-18 → 10-01). On the four since
  09-28: scanner 100 / 100, analyst 468 / 468, PM 88 / 88.
- Decision-path files that differ between a session's deployed commit and the deployed `f3956bac`
  (`s249`): 09-28 **7** (S242's three polls, S243's `integrity.py`, three `contracts/` modules), 09-29
  **2**, 09-30 **1** (`contracts/provider.py`, S249), 10-01 **0**.
- Against `main` every session differs by 18 or more: S250 changed
  `agents/provider/domain/market_calendar.py`, S251 changed `contracts/execution.py`, and the rule counts
  each agent's `laws/` and `tests/` folders, which S251 touched.

So one session is clean today, and only when the replay runs from the deployed commit.

**Decided.** (1) The rule stands as written (DL-238 D7). It is not narrowed to make this run pass: the
agreement above is evidence, and the bar EXP-014's frozen Appendix P names is a PASS. (2) The replay
runs from a worktree pinned at the fleet's deployed commit, so a merge to `main` no longer resets the
count. (3) The fleet's decision code is held still for four sessions, and EXP-014 runs from the same
pinned commit, so the code the gate certifies is the code the experiment runs. (4) Before any deploy
inside that window, diff it against the decision paths first.

**Road not taken.** *Count the four matching sessions as clean.* A bar that admits a session because
it matched passes by construction. *Drop `laws/` and `tests/` from the decision paths.* Neither can
move a decision, so the change is fair, but made today it would be a rule edited after reading its
result, and it would not give a PASS: `market_calendar.py` and `contracts/` still differ. Left for a
sprint that touches the tool. *Replay each session from its own deployed commit.* Four runs of one
session each, and none can meet a four-session floor.

**Open, the operator's call: which commit the four sessions run on.** Staying on `s249` gives a verdict
after `sched-2026-10-06` (three more sessions) and certifies `f3956bac`; EXP-014 would then run on a
commit that differs from it in two decision-path code files. Retagging to `main` first gives a verdict
after `sched-2026-10-07` (four sessions) and certifies exactly the commit EXP-014 runs from.
Recommended: the retag.

**Resolved, 2026-10-02 10:38 AEST: the operator chose the retag** (*"retag"*). The fleet runs
`s251`, built from `d526faf4` (`v0.121.01`), since 00:38 UTC. The four sessions are
`sched-2026-10-02`, `-10-05`, `-10-06` and `-10-07`; the verdict is read on the morning of
2026-10-08 from a worktree pinned at `d526faf4`, and EXP-014 runs from the same worktree. Until
then there is no retag unless a live defect forces one, and any build is diffed against the
decision paths first. At the retag `main` differed from `d526faf4` in 0 decision-path files.

**Read, 2026-10-08 10:32 AEDT: INSUFFICIENT again, and for a different reason.** The replay ran from a
worktree pinned at `d526faf4` over an export of 64 sessions. The four sessions on the fleet's unchanged
decision code are clean, as planned: `sched-2026-10-02`, `-10-05`, `-10-06`, `-10-07`. On them the replay
agrees with the fleet on every row: scanner 100 of 100, analyst 148 of 148, PM 4 of 4, and 143 of 143 PM
hold passthroughs, which are counted beside the verdict and never pooled. Unexplained differences: 0. The
scanner's floor is met (4 of 4 clean sessions) and the analyst's (148 of 100 tickers). **The PM's is not:
4 judged recommendations against a floor of 10.** The four sessions held four buys in all (one on 10-02,
three on 10-05), and the last two nights placed none because every name the scanner passed was already
held. Outputs: OneDrive `trading-agents-data/fidelity/2026-10-08/`.

**What it means.** EXP-014's frozen gate asks for a PASS, so no arm starts. The rule is not narrowed
after reading its result (decision 1 above). A PASS needs six more judged recommendations on the same
decision code. *[estimated, not measured]* at one buy a session or fewer, with the book at 36 names, that
is one to three more weeks.

**Open, the operator's call: hold the fleet still, or deploy and restart the count.** Four merged sprints
wait for a retag (S252 to S255), and two of them change decision paths (S253 scores a short-history
candidate differently; S255 adds fields in `contracts/`). So a retag starts the count again on the new
code: four clean sessions and ten judged recommendations from zero. Holding keeps the four recommendations
already counted and keeps four sprints, and every later decision-path change, off the fleet until the
floor is reached. Recommended: the retag. The PM's floor is slow to reach on any code while the book is
this full, so holding buys about a week of the experiment's start at the price of every deploy in
between.

**Resolved, 2026-10-08 11:34 AEDT: the operator chose the retag** (*"go for it"*). The fleet runs `s255`, built from `fec365a1` (`v0.123.00`), since 00:40 UTC. The fidelity count starts again on that code: four clean sessions, the first of them `sched-2026-10-08`, and ten judged PM recommendations. It is read from a worktree pinned at `fec365a1`, and EXP-014 runs from the same worktree. *Given up:* the four recommendations already counted on `d526faf4`. Until the next read, any build is diffed against the decision paths before it is deployed.

**Status 2026-09-27 — S237 merged (`v0.117.00`), first live run.** Verdict **INSUFFICIENT** (0 clean sessions). On the six latest sessions the replay agrees with live on every row, four of them the `contracts/`-only sessions; over 56 sessions, 0 differences are unexplained. The verdict is re-run after `sched-2026-10-01`, when four clean sessions exist.

---

## DL-236 - a price-only ensemble is measured on the replay cache now, and built only if it wins - status: DECIDED (operator, 2026-09-27)

**Question.** With ten years of the point-in-time index cached (S235), should shadow-prediction
ensembles start now, or wait for P18A.3 after the G-EDGE decision, where the plan put new signals?

**Decision (operator: "I like your recommendations and would like to follow it").** Pull it forward **as a measurement,
not a build**: **EXP-015**, offline on the replay cache, $0 LLM. Does a small price-and-volume
ensemble beat the analyst's current technical score out of sample: rank IC, decile spread and decay,
purged walk-forward windows, a final holdout, and 25 bps costs? The hypothesis and the pass bar are
written before any model is fitted. It runs alongside E17.4. Only a clear win enters the forecaster's
existing shadow loop (`shadow=True`, never gates; promotion through the registry, ADR-0010). A loss
costs one experiment and builds nothing.

**Why now.** The harness that can say no exists (S235). The forecaster already owns shadow models,
return labels and a return scorecard. The measurement touches no live path.

**Bounds.** Price and volume only (DL-232: no point-in-time fundamentals or news). Sector labels are
today's (a mild look-ahead; 13 % of symbols have none). The SIP bars stay out of the repo; models and
scores may not embed them. Item 89 (the live scanner reads IEX volume) must be fixed before any
shadow model is fed by the live pipeline, or it will see the wrong universe.

**Ruled out.** *Build a shadow ensemble now:* many fitted variants over ~2,700 sessions will find
something by chance; the experiment's pre-registered bar is the guard. *Wait for G-EDGE:* the
measurement is free and informs the verdict. *Train on the live graph's history:* six weeks, one
configuration, IEX volume.

## DL-230 - the daily brief may carry P&L amounts to the operator's Telegram chat - status: DECIDED (operator, 2026-09-26)

**Question.** E19.1's daily brief goes out over Telegram, a vendor channel. `RPT-SEC-02` says the
reporter never logs trade details, P&L or position data to external systems. May the brief carry P&L,
and in what form? DL-220 moved this question from E16.2 to E19.1 as the operator's.

**Decision (operator: *"Yes, with amounts"*).** The brief may carry dollar amounts (equity, the change
since the previous brief, the orders placed and filled) and the vs-SPY scoreboard, sent only to the
operator's configured Telegram chat, only by the scheduled dispatcher, once per scheduled run.

**Where the law lands.** The sender is the dispatcher, so the guarantee and its boundary go into the
`DSP` book (S234's law cycle: the brief, its one-per-run idempotency, and the channel it may use).
`RPT-SEC-02` is **not** amended: its subject is the reporter, which still sends nothing, so the clause
stays true, and conventions §4 forbids amending a law for its wording.

**Ruled out.** *Percentages and the vs-SPY line only*: offered, and declined by the operator.
*No P&L at all*: offered, and declined. *The reporter sends the brief*: it would contradict
`RPT-SEC-02`, and the reporter cannot see the acceptance verdict, which lives in the pack's
orchestration layer.

**Accepted risk.** Telegram's servers see the amounts. The account is a paper account, and the operator
accepted the channel. A live account would reopen this question.

## DL-228 · S232 moves the substrate's handshake vocabulary into the kernel and the served roster into pack data · status: DECIDED (S232, 2026-09-26)

**Question.** ADR-0012 declared the substrate/pack wall *de jure* in June 2026 and named two leaks.
Measured 2026-09-25: one leak is already closed (DL-12, S84–S86), one is real and small (10 import
lines, `agents.master* → contracts.master`), and there is a third the ADR never named (9 pack
agent-type string literals in `kernel/serve_transport.py`). Where does the substrate's handshake
vocabulary live, and how does the served roster stop being a kernel constant, without moving anything
that is genuinely pack content?

**Decision 1 — the substrate vocabulary moves into the kernel.** Confirmed by the operator at the
planner review (2026-09-26); technical calls are delegated to the planner. The kernel already hosts
`AgentContract`, `Capability`, `AgentFault` and `Envelope` (substrate vocabulary with no trading
content), so `_Frozen`, `Provenance`, `Explanation`, `AgentState`, `EHLOMessage`, `ACTIVATEMessage`,
`DRAINMessage` and the master `CONTRACT` join them there. **Rejected:** a `contracts/platform/`
subpackage (the substrate would still live inside the pack's package, and the master image would
still need a partial `COPY`); a new top-level `substrate/` package (a sixth root package and a `COPY`
line in 15 Dockerfiles, for vocabulary the kernel can already hold); leaving the vocabulary in
`contracts/` and moving the *trading* modules out instead (rewrites 829 statements in 467 files and
touches all 15 Dockerfiles, only to relocate the side that is not moving).

**Decision 2 — module names.** `kernel/payload.py` (new: `_Frozen`, `Provenance`, `Explanation`,
moved verbatim from `contracts/common.py`, docstrings included) and `kernel/handshake.py` (new, via
`git mv contracts/master.py`: `AgentState`, `EHLOMessage`, `ACTIVATEMessage`, `DRAINMessage`, the
master `CONTRACT`). No reviewer rename requested.

**Decision 3 — the re-export.** One base class, not two. `contracts/common.py` imports `_Frozen`,
`Provenance`, `Explanation` from `kernel.payload` and re-exports them with explicit `X as X` aliases
(mypy strict disables implicit re-export). `_Frozen` keeps its private name at the new path so `D101`
does not require a docstring. **Rejected:** rewriting all 134 import statements in 133 files to import
from `kernel.payload` directly — 40 of them would split into two import statements (one substrate, one
trading), and the deliberator's context modules are among them, which would move `PROMPT_RECIPE_HASH`
(out of scope, and a live-audit-breaking side effect for zero benefit). **Rejected:** keeping a second,
separately-defined `_Frozen` in `contracts/common.py` — two frozen bases would make
`issubclass(x, _Frozen)` answer differently depending on which module a test imports from (the trap
this sprint's spec names explicitly).

**Decision 4 — the wall's contract text.** `.importlinter` gains one new forbidden contract,
`substrate-imports-no-pack` (`source_modules`: `kernel`, `agents.master`; `forbidden_modules`:
`contracts`, the 13 other `agents.*` packages, `orchestration`, `surfaces`), alongside the existing
kernel contract, which stays unchanged — it costs nothing to keep and already proves a related but
narrower property. `agents-are-islands` widens from 12 to 14 modules, adding `agents.deliberator` and
`agents.master` (measured: 0 violations on today's tree with both added).

**Decision 5 — the roster file and its loader.** `orchestration/packs/trading_served_agents.json`
holds `served_agent_types`, `deliberator_peer_agent_types`, `deliberator_manager_type`,
`deliberator_reply_agent_types`, and `image_dir_by_agent_type` (an explicit map, not a naming
convention — the pack states which directory serves each type, so no loader logic has to guess that
the three deliberator roles share one image). A new loader, `scripts/served_agent_roster.py`, reads
this JSON **by path** (`parse_served_agent_roster(text)` / `load_served_agent_roster(path)`, mirroring
`agents/master/grants.py`'s `parse_grant_policy`/`load_grant_policy` pattern) and exposes the same
constants `kernel/serve_transport.py` used to export, so `sb_sas_plan.py`, `servicebus_prepare_routes.py`
and `tests/test_served_agent_images.py` swap one import line for another. `kernel/serve_transport.py`
keeps `request_topic`, `reply_topic` and `consumer_from_env` — those three are genuinely generic string
formatting and transport selection, not roster data. **How two packs' rosters would combine (not
built):** a second pack's roster would be its own JSON file; a multi-pack loader would take a list of
paths and merge their `agent_type` keys with a collision check (two packs claiming the same served
type would be a build-time error, not a silent override) — deferred until a second served pack exists.
**Rejected:** a Python module in `orchestration/packs/` (the deploy script would then need to import
pack Python under `uv run --extra azure`, and `orchestration/packs/__init__.py` imports
`us_equities_sp500` — DL-218's failure shape); leaving the roster for E20.3 to find (ADR-0012 already
names "the agent roster" as a leak shape, so leaving a known instance in place would make E20.3's count
of substrate edits dishonest). The full reasoning for keeping it in this sprint is Decision 8.

**Decision 6 — the amended master wording.** `MST-NEV-01`'s subject becomes "the grant policy the pack
supplies" (its guarantee — never activate an unknown type — is unchanged; `DEFAULT_GRANTS` was deleted
in S84, three months before this sprint). `MST-SEC-03` is rewritten to assert only what code can
falsify: *"the pack's grant policy is the only privilege table, the master image ships none, and
master reads it once, when it starts."* It drops the *"cannot be changed by runtime config"* claim
entirely — the same book's own `PARAM` table marks `grant_policy_b64`/`grant_policy_path` `Tunable
YES`, so that claim was already false and nothing enforces it (DRIFT-058's lesson: a clause whose
check cannot fail proves only that the oracle ran, never fails). `MST-DEP-03`'s subject becomes "the
pack data injected at start-up (grant policy, secret map, credential tests) plus the `AgentDefinition`
graph nodes" — the guarantee (no dependency on trading-agent code) is unchanged; only the store the
knowledge lives in is named accurately (it names three pack-data sources now, not one deleted
constant). `MST-TYP-01` names `kernel/handshake.py` in place of `contracts/master.py`. New
**`MST-DEP-05`**: master imports only the substrate (`kernel` and its own package) and never a pack
module — the guarantee this sprint actually adds, proven by A1 (a fresh interpreter's import closure
holds no `contracts*`, no other `agents.*`, no `orchestration*`, no `surfaces*`).

**Decision 7 — the pack-neutral `CONTRACT` text.** The mission changes "every trading-system agent
container" to "every pack agent container." The `never` list's *"perform trading logic or place
orders"* becomes *"perform any pack agent's business logic or act on its behalf"* — the same
prohibition (master does no domain work), stated without naming a domain. Nothing else in `CONTRACT`
changes; `name="master"` and `version="0.1.0"` are the master's own identity, not trading vocabulary.

**Decision 8 — the served roster is fixed in E20.2, not left for E20.3.** The operator delegated this
one (2026-09-26: *"Do not know enough to comment. make a rational and document it"*); the builder
decided it on the evidence below. The question: the roster (`SERVED_AGENT_TYPES` and the three
deliberator role constants, 9 literals in `kernel/serve_transport.py`) is a leak ADR-0012 did not list,
found while measuring E20.2. Fix it here, or leave it for E20.3 to find while building the second pack?

- **For fixing it here.** (1) ADR-0012's decision text forbids exactly this: *"the agent roster … is
  pack-provided input to the substrate, never hardcoded in it"*. It has the shape of `DEFAULT_GRANTS`,
  and DL-12 already chose the fix for that shape (pack JSON read by path), so no new design was needed.
  (2) P20's exit is zero substrate edits after E20.2, and E20.3 is where that count is taken. A leak
  known before E20.3 starts, left in place and then "found", would make the count measure what we
  chose to leave rather than what we failed to see. (3) It is small and provable on fixtures: one
  kernel module (72 → 51 lines), three readers (two deploy scripts and one test), a JSON file and a
  62-line loader. The Service Bus route list and the SAS-grant plan built from the pack file equal
  those built from the old constants (A6, four tests), and `sb_sas_plan.py` shrank, 212 → 211.
  (4) It lets the name-level wall test (A3) run with no exemption list; an exemption would be a declared
  leak inside the guard meant to catch leaks. (5) Every image rebuilds anyway, because `kernel/`
  changes, so it adds no deploy of its own.
- **Against.** (1) It goes beyond the plan's wording for E20.2, which named only the grants, `contracts/`
  and the wall. (2) It touches deploy tooling. `servicebus_prepare_routes.py` runs during
  `deploy-agents.ps1 up`, and `sb_sas_plan.py` plans the Service Bus SAS grants; an image-only retag
  exercises neither, so a defect would stay hidden until the next full `up`. (3) Whether the
  repo-steward pack serves any agent over Service Bus is unknown until E20.3 designs it. If it serves
  none, the move buys the P20 exit nothing beyond ADR-0012 cleanliness.
- **Why "for" wins.** Risk (2) is controlled rather than accepted blind. A6 pins both plans to today's
  literal values, so the next `up` prepares the same topics, subscriptions and grants. The loader reads
  JSON by path, never importing `orchestration` under `--extra azure` (DL-218's failure shape). A
  failure is loud: `Prepare-ServiceBusRoutes` throws *"Service Bus route preparation failed"* and stops
  the deploy. (1) is a scope addition inside the plan's own intent: "fix the named leaks", where the
  ADR names rosters. (3) cuts both ways. If the second pack serves an agent, deferring costs a kernel
  edit in E20.3, which is exactly what the exit forbids; fixing it now costs one small, proven
  relocation either way.
- **What would reverse it.** Either of two findings: a topic, subscription or grant that differs at the
  first full `up` after merge (the functionality check compares them with today's), or a reader of the
  roster beyond the three measured (A6's own test aside). A fourth reader would mean the measured blast
  radius was wrong: stop and re-scope.
- **Rejected: defer to E20.3.** This keeps E20.2 to the plan's words and leaves deploy tooling untouched
  until a second pack exists. But it ships a known ADR-0012 violation past the sprint that declares the
  wall enforced, it needs A3 to carry an exemption, and it pre-loads E20.3's count of substrate edits.

**Ruled out, sprint-wide.** A gate step that checks every 🧱 test-plan row names a contract that lists
its agent — rejected under the process freeze (next-leg-plan §5); the two known rows (`MST-NEV-05`,
`MST-DEP-03`) are corrected by hand this sprint, and A2 is the proof they are not vacuous. Declaring
the wall with module lists alone and moving no code — rejected because `contracts/common.py` mixes
both sides name-by-name and import-linter reasons about whole modules. Moving `Window` into the kernel
alongside the other three — rejected; it is a date-range DTO the substrate never uses (ADR-0012 §3, no
speculative generality). Moving `kernel/deliberation_prompts.py` or `kernel/market_pack.py` (both hold
trading content already inside the kernel) — rejected for this sprint: the former is hashed into every
`LLMCall`'s prompt-recipe digest (`kernel/prompt_recipe.py` hashes `__name__`), so moving it would
break comparability with every already-recorded debate; the latter is read only by the trading
dashboard. Both are recorded here as known residue, not silently left; a pack that is not a market
registers nothing against `market_pack.py`, and no second pack deliberates yet, so neither leak has a
consumer today that this sprint's DL-70 guards would need to defend against.

**Discovered in the build environment. This applies to any sprint built in a claude.ai cloud
session, not only this one.** Two gate steps cannot finish there. (1) `make gate-ran` shells out to
`gh`, which the cloud container does not have (`FileNotFoundError: 'gh'`, measured twice, 2026-09-25
and 2026-09-26). The session can read the run conclusions through the GitHub connector, but that is
an observation, not the gate, so the planner runs `make gate-ran` before merging. (2) `uv lock`
cannot complete, because the session's egress policy blocks `download.pytorch.org`, the `forecaster`
extra's pinned index. A version bump then leaves `uv.lock` stale, and every `uv run` tries to re-lock
and fails. This sprint's builder hand-edited only `uv.lock`'s own version line
(`0.113.0` → `0.113.1`) and flagged it, so the planner owes a real `uv lock` before merge. Either
limit is removed by giving cloud sessions `gh` or allowing that host, and each is the operator's call.
Until then, a cloud handback names both steps as owed.

---

## DL-186 - the referee is given every quant's value and almost none of its meaning, and its sharpest argument was one we wrote for it - status: MEASURED (2026-09-20, operator question)

**The question, from the operator:** a freshly started LLM conversation has no history, so how does
the deliberator know (a) that this project's quants exist and what they mean *here*, and (b) what
their values are? Read in the code rather than answered from memory.

**(b) Values: yes, and there is nothing magical about it.** Each turn's user message carries a
rendered CONTEXT/EVIDENCE block built by string interpolation in `agents/deliberator/context_pm.py`:
analyst scores, `quant_metrics`, every PM gate outcome as `value`/`threshold`/outcome, and
`Regime: label=...; vix_index=...`. `agents/deliberator/prompt_recipe.py` hashes the exact module set
that produced the text, so the rendering is auditable.

**(a) Meaning: largely NO, and the renderer says so out loud.** `context_values.py:81` emits
`source-owned-units-scope-unknown{atr_pct=2.35, beta=1.383}`, and an unregistered gate renders
`value_units_scope_unknown`. **There is no glossary of what a metric means in this system.** The model
gets a name, a number, and an explicit declaration that nobody has stated the units or scope.

Two things partly stand in, and neither is a substitute for a definition:

- `_DEFINE_THEN_JUSTIFY` (`kernel/deliberation_prompts.py:8`) forces the model to define each parameter
  it invokes before reasoning from it. That is an **honesty device, not a knowledge device**: it makes
  a wrong assumption visible rather than preventing it.
- A hand-written *"Preserve these distinctions"* list of six project-specific facts.

🚨 **The asymmetry nobody had measured.** Champion system prompts:

| Role | Size | Distinctions list | Compiled examples |
| --- | --- | --- | --- |
| Defender | **434 chars** | no | no |
| Challenger | **6,764 chars** | yes | yes |
| Judge | **6,341 chars** | yes | yes |

The judge is additionally instructed: *"If the Challenger catches a grounded implementation-specific
flaw from the evidence, do not uphold the decision."* So a meaningful part of the **78.9 % veto rate
is designed in**, not discovered. That is a more likely driver than anything about model temperament.

🪰 **The circularity, which matters for how past evidence is read.** The challenger's prompt
contains the literal distinction *"fixed-fraction sizing is not volatility-adjusted"*. The
`sched-2026-09-15` AMZN veto then argued *"sizing is a fixed-fraction notional cap, not
volatility-adjusted for a beta-1.383/ATR-2.35 % name"*, and
[ADR-0025](decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md)
Decision B quoted that veto as the referee being **right**. 🎯 **The flaw is real** - re-read
2026-09-20, `size_quantity` (`agents/portfolio_manager/domain/sizing.py:25`) is
`(portfolio_value * max_position_pct) // est_price`, a pure notional fraction with no stop distance in
it. **But the argument was not independent discovery: we told it to preserve that distinction, it did,
and we counted it as evidence.** ADR-0025 and [ADR-0031](decisions/0031-regime-scales-the-risk-budget-atr-keeps-the-stop.md)
stand on the code reading, not on the veto; this records that the veto should never have been cited as
a second, separate witness.

**DSPy is not in the runtime.** `kernel/dspy_optimizer.py` lazily imports `dspy`, which lives in the
optional `optimizer` extra that **zero Dockerfiles install**. The champion prompts are frozen Python
string literals in `kernel/deliberation_prompts.py`, carrying their own birth certificate
(*"Promoted from PromptArtifact task=deliberation.challenger,
version=2026-07-08-s121-v5-challenger-gpt-5.5"*). `deliberation_prompt_artifacts.py` parses artifacts
for that promotion pipeline; it does not load prompts at run time. So the semantics are a paragraph
compiled once in July and pasted in, while the values are `name=number` stamped *scope unknown*.

**On persona (operator's hypothesis, answered).** A domain persona - *"senior financial analyst at a
trading firm covering the S&P 500"* - conditions the output distribution: register, vocabulary, which
known things surface. It **adds no knowledge**, so it cannot supply the missing `atr_pct` definition;
it makes a confident guess sound more authoritative. 🪤 **And in this system it may work
against us:** the challenger prompt spends words on *"address that exact flaw **before generic finance
caution**"*, which is precisely the prior a finance persona raises. **Rejected as a default**, kept as
a testable hypothesis - work-queue item **75**.

🚨 **AMENDMENT, same day — the few-shot examples are the stronger steer, and they are
one-sided.** The operator asked whether the *“for example”* narrative guides the model in the
right direction. Measured, not eyeballed:

| Role | Examples | What they demonstrate |
| --- | --- | --- |
| Defender | **0** | nothing |
| Challenger | **8** | 8 objections; no case where the decision is sound |
| Judge | **8** | 🚨 **`revise` × 8 — 100 %. Zero `uphold`, zero `overturn`.** |

**The judge has never been shown a correct `uphold`.** Its only demonstrated ruling is `revise`, and
few-shot examples steer harder than any instruction in a prompt.

Against the live spine — **353 rulings across 64 `DeliberationRun`s carrying verdicts**:
`revise` **168 (47.6 %)**, `uphold` **163 (46.2 %)**, `overturn` **22 (6.2 %)**, a **revise/overturn
ratio of 7.6×** that reproduces the 7.5× [ADR-0029](decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md)
was written to address. *(Different denominator from item 59's 223 reviewed over 29 real-debate runs;
both stand, they count different populations.)*

🎯 **The cause is traceable and is not malice — it is a sampling artifact.** The examples were
compiled from the **Class-1 case library**, which [EXP-004](research/experiments/EXP-004-class1-cases-llm-judge.md)
built *by construction* as a library of flaws: *“each flaw must be invisible from finance
world-knowledge and revealed only by our implementation”*. A flaw library contains no sound
decisions, so examples drawn from it can only ever demonstrate objecting. Nobody chose to bias the
judge; the corpus had one class in it.

🪤 **This re-frames ADR-0029 rather than contradicting it.** Narrowing the block to `overturn`
was correct and remains correct. But it treated `revise` over-production as a *property of the
referee*, when `revise` may be inflated because **it is the only ruling ever demonstrated**. If so,
some share of those 168 findings is the model reproducing the examples, which makes the *finding
count* a weaker signal than it reads as.

🪰 **Measuring this cost me a false zero.** The first pass reported **0 rulings** with complete
confidence: `verdicts` is a `mappingproxy`, `isinstance(x, dict)` is **False** for it, so the filter
silently matched nothing. Corrected with `collections.abc.Mapping`. That is
[[audit-with-contracts-predicates]] / DL-73 again — an audit on a raw type assumption, producing a
clean, confident, wrong number.

**The road not taken, recorded now so it is not re-derived.** Richer field descriptions (the DSPy
signature shape the operator proposed) would close the semantics gap - and would also be *hints*. The
distinctions list demonstrates how hard a sentence in the system prompt steers the verdict, so better
definitions would improve grounding and deepen the told-it-what-to-find problem **at the same time**.
That trade-off is the real design question and is not settled here.

---

## DL-160 - the sweep's price was wrong by 3.2x, and work-queue item 43 is exactly why - status: DECIDED (2026-09-05 — stop, spend nothing more)

🚨 **[DL-158](design-log-archive/DL-141-to-175.md#dl-158---part-b-is-five-dependent-batch-rounds-not-one-batch-of-debates---and-it-has-a-price---status-decided-2026-09-05) priced an order-replay at `$0.0305` for five calls — `$0.0061` per call. Measured on the real thing: `$0.0196` per call.** Round 1 of the funded sweep (2,961 requests, 2,957 succeeded / 4 errored) cost **$58.05**, read from the Batch API's own `usage` rather than from anything this repo records:

| Measured, round 1 (`msgbatch_01NtHf…`) | Value |
| --- | --- |
| input tokens | **8,865,925** — mean **2,998** per call |
| output tokens | **2,870,907** — mean **970** per call |
| cache read / write | **0 / 0** — no prompt caching anywhere |
| cost at batch rates ($2.50 / $12.50 per MTok) | **$58.05**, i.e. **$0.0196 per call** |

**Why the estimate was low, precisely — and it is not a modelling nicety.** DL-158 built its figure from `LLMCall.tokens_in`/`tokens_out`, which **work-queue item 43 had already established are word counts, not tokens, and exclude the system prompt entirely** (`kernel/llm_ledger.py:114`, `agents/deliberator/agent.py:139` passing `prompt=user`). Two errors compounded:

1. **The per-order figure was treated as covering all five calls.** It does not: every call re-sends the whole context, so ~3,000 input tokens are paid **five times per order**, not once.
2. 🚨 **"Excludes the system prompt" is the dominant term here, because the system prompts are wildly unequal.** Measured: **`DEFENDER_SYSTEM` 434 chars · `CHALLENGER_SYSTEM` 6,764 · `JUDGE_SYSTEM` 6,341.** The challenger's is **15.6x** the defender's. Round 1 is the *only* round that speaks with the small one, so calibrating anything on round 1 — as DL-158 effectively did — understates every round after it.

**Output is half the remaining bill.** At 970 output tokens per arguing turn and $12.50/MTok, output alone is ~$0.0121 of each $0.0196 call. No amount of input trimming touches that.

### The corrected table, projected from round 1's measured usage

Characters-per-token calibrated at **2.14** on round 1's real figures — low for prose, but the veto context is numbers and `snake_case` identifiers, which tokenize badly. Round 1 is paid and free in every row.

| Option | Calls left | Debates | Remaining | With system-prompt caching |
| --- | --- | --- | --- | --- |
| **A** three arms x 3 repeats *(what was funded)* | 9,854 | 2,961 | **$274** | $218 |
| **B** three arms x 2 repeats | 6,564 | 1,974 | **$182** | $145 |
| **C** control arm only x 3 repeats | 3,944 | 987 | **$112** | $91 |
| **D** control arm only x 2 repeats | 2,628 | 658 | **$75** | $61 |

Full design A therefore lands near **$331** against the **~$90** quoted. The operator authorised $90; that authorisation does not stretch to $331, so the sweep is **stopped after round 1** pending a fresh decision.

🪤 **Round 1 alone yields nothing measurable.** A verdict needs all five rounds, so the $58 buys zero verdicts unless some configuration is finished. That is an argument for completing *one* usable arm, not for completing all three.

### DECISION (operator, 2026-09-05): stop. Spend nothing more.

**Part B does not run.** Put the corrected table above, the operator chose to bank the $58 rather than
buy any of the four options — including the $75 one. **This is a decision, not a deferral:** the
effort/`max_rounds` question stays answered by assumption, and that is now a recorded choice made
against a known price rather than an omission.

**What the $58 bought, stated honestly: no verdicts.** A verdict needs all five rounds, so round 1's
2,957 answers produce nothing measurable on their own. They sit at
`…/scratchpad/sweep-1/round-01.json` (6 MB) and stay reusable indefinitely on disk — the Batch API's
own 29-day results window does not apply to a file already written. If the sweep is ever funded,
that round is not re-bought.

**What it did buy is this entry.** The pricing error was 3.2x and would have been discovered either
by spending $331 or by spending $58; it was discovered by spending $58. Everything S173 Part A ships
— the harness, the metrics, the gate, the re-derived DL-104 baseline — is unaffected and cost nothing.

### Two things worth doing regardless of which option is chosen

🟩 **Prompt caching is unclaimed money, and not only for this sweep.** `cache_read = 0` across all 2,957 calls. The challenger and judge system prompts are identical across every request in a round, so `cache_control` on the system block cuts them to 10% of the input rate — **~20% off the sweep** (table above), and it applies to the **nightly fleet** too, where every debate in a run shares those same two prompts inside the cache TTL. This is a code change to the adapters, not to the harness.

🚨 **This is the second time item 43 has cost a real decision, and the first time it cost money.** The item's own text predicted it: *"it is urgent for decisions, because the effort/cost sweep in S173 Part B is one of them."* It was ranked and not done, and the sweep was then priced off the numbers it warns about. The honest source is the API's own `usage`, which both adapters currently discard — and which this entry had to fetch by hand.

---
