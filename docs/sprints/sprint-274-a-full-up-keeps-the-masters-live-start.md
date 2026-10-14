<!-- Agent: planning | Role: sprint handover -->
# Sprint 274 — a full `up` keeps the master's 22:00 wake, and the dashboard shows the wake the fleet has

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-274-a-full-up-keeps-the-masters-live-start`
**Status:** SPEC
**Version:** PATCH (the next free one at merge; do not pin the digits here)
**Effort:** S
**Decisions:** [DL-300](../design-log.md) (this sprint's five decisions, made and measured) · [DL-294](../design-log.md) amendment 1 (the operator's 22:00 wake, applied to the live master) · [work-queue 131](../work-queue.md) part (f)

> **Why this bump kind.** No new capability: the master already wakes at 22:00 UTC on weekdays.
> The deploy script and the dashboard still say 20:25, so a full `up` would put the old wake back
> and the dashboard reads the master as awake for an hour and a half in which it sleeps. The
> dashboard's default is package behaviour, so the version moves by a PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `surfaces/laws/laws.md` | The surfaces' **locked constitution** (v1.7) | **LOCKED.** This sprint changes one row of its `PARAM` table and no clause |
| `surfaces/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read only. No row changes: no clause governs the wake window |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `INDEX.md` and `ledger.md`: the surfaces' row reads v1.8 |

Binding sections here: **`PARAM`** (the table), **`SRF-DEP`**, **`SRF-NEV`**.

### The rule

1. **Before writing code**, read `surfaces/laws/laws.md` and its `test-plan.md`, whole.
2. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
3. **Write the Law reading record** (bottom of this file) **before** your first code change.
4. **If a law contradicts this spec, STOP and report.**
5. A test for behaviour a clause governs cites the clause ID in its docstring. *[read 2026-10-14]*
   no clause of the surfaces' law, the master's or the dispatcher's governs the hour the master
   wakes; if your reading finds one, cite it and say so in the Return notes.

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No file in `contracts/` changes and no clause is added or reworded.** The `PARAM` table follows
the settings, as the parameter gate requires. The cycle owed, every item of it:

- In `surfaces/laws/laws.md` the `master_window_start_utc` row becomes exactly this:

  ```text
  | `master_window_start_utc` | `"22:00"` | `str` | YES | Matches `$MasterScaleStart` in `infra/deploy-agents.ps1` and is test-pinned. |
  ```

- The status line at the top of the file reads `LOCKED v1.8`, and the Changelog gains one entry
  above the v1.7 one, in the form of the entries below it:
  `v1.8 — S274 / DL-300 (2026-10-14): PARAM only. master_window_start_utc is 22:00, the master's
  live wake (DL-294 amendment 1). No clause changes.`
- `docs/laws/INDEX.md` and `docs/laws/ledger.md`: the surfaces' row reads v1.8 and says what this
  sprint did, in the form the row already uses for S270. 🪤 **The law gate does not check this
  label**: it compares the counts only. Change both rows by hand.
- The counts stay 31 / 38. Let the gate say.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `surfaces/dashboard/settings.py` | surfaces `laws.md` + `test-plan.md` | the `PARAM` table must match the settings fields (`check_param_law_sync.py`) |
| `infra/deploy-agents.ps1` | surfaces `laws.md` (`SRF-DEP`), `docs/deployment.md` | the parameter is what a full `up` applies to the live master |
| `tests/test_master_wake_window.py` (new) | `orchestration/laws/dispatcher/laws.md` (`PARAM`: `preflight_max_age_minutes`), `agents/master/laws/laws.md` (`PARAM`: `fleet_preflight_interval_minutes`) | the new tests read both values; neither changes |

---

## Goal

A full `up` with no window parameter gives the master the wake it has on the live fleet
(weekdays, 22:00 UTC), the dashboard reads the master as awake only from that hour, and a test
fails when the wake no longer leaves one fresh fleet check for the 22:30 run.

## Why (context)

On 2026-10-12 the operator moved the master's wake from 20:25 to 22:00 UTC (*"wake master at
9:00 not at 7:30"*, Melbourne time; [DL-294](../design-log.md) amendment 1). It was applied to
the live master by hand. The deploy script's default, the test that pins it and the dashboard
still say 20:25. The same gap for the rest of the window was closed by
[S270](sprint-270-the-deploy-defaults-are-the-live-wake-window.md); this is its last part.

### Measured, 2026-10-14 — read these before designing

Every row was measured on `main` at `8b27dfcd` unless it says otherwise.

| Claim | Value | How it was measured |
| --- | --- | --- |
| The live master's scale rule | one rule, start `0 22 * * 1-5`, end `30 23 * * 1-5`, UTC | *[measured]* `az containerapp show` on the live app, read-only |
| The 16 live rules | the master as above; the 15 agents start `30 22 * * 1-5`; every end `30 23 * * 1-5`; one rule each | *[measured]* `az containerapp list`, read-only |
| The script's default | `25 20 * * 1-5`, under a comment that names two hourly retries | *[read]* `infra/deploy-agents.ps1:20-21` |
| What a full `up` with no window parameter gives each app | 16 rules. On `main` 15 equal the live rules and the master's start is `25 20 * * 1-5`. On the prototype 16 of 16 equal them | *[measured]* the script's own `Up`, every `az` call and every credential a stand-in, no network |
| What the dashboard says of the master today | its window reads 07:25-10:30 Melbourne; at 20:30 and at 21:30 UTC on a weekday it reads the master as awake, and the live master is asleep until 22:00 | *[measured]* `next_master_wake` and `window_label` on `DashboardSettings(_env_file=None)`. With `22:00` they read 09:00-10:30 Melbourne and name 22:00 as the next wake. The main checkout's `.env` sets no window key |
| How soon after a wake the first check is readable | 29 to 50 seconds, on eight nights (six wakes at 20:25, two at 22:00) | *[measured]* `FleetPreflight.checked_at` on the live graph, 2026-10-05 to 2026-10-13 |
| The nights at the new wake | two: on 2026-10-12 the checks are 22:00:50 and 23:01:05 and the run was placed; on 2026-10-13 the first is 22:00:45, read before that night's run. All passed | *[measured]* the same read. No check has failed at the new wake, so nothing here is measured about one that does |
| The values the wake has to fit | the first placing tick 22:30 and the last 23:20, one every ten minutes; the dispatcher takes a check up to 70 minutes old; the master repeats its check every 60 minutes | *[read]* `_ACTION_START` and `_ACT_BY` in `orchestration/scheduled_dispatch_actions.py`; `preflight_max_age_minutes` in `orchestration/settings.py`; `fleet_preflight_interval_minutes` in `agents/master/settings.py` |
| A later check that passes releases a held run, and the run is placed | yes | *[read]* `orchestration/scheduled_dispatch_gate.py::hold_unready_run`, `DSP-STA-01`, and the passing test `orchestration/tests/test_scheduled_dispatch_readiness.py::test_recovery_releases_hold_and_places_run`. *[measured]* the live graph holds 0 `RunHold`: no run has ever been held on the fleet, so the release is proven by the test alone |
| Existing tests that break on the prototype | 2: `tests/test_deploy_script_invariants.py::test_master_scale_window_starts_before_the_two_pre_dispatch_retries`, which pins the old literal and the old comment, and `surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows`, which pins 20:25 as the default window's start | *[measured]* the full suite in the sprint worktree |
| Existing tests that read `20:25` and do not break | the tests' shared `_settings()` passes `master_window_start_utc="20:25"` itself | *[read]* `surfaces/tests/test_dashboard_costs.py:45`; *[measured]* they pass on the prototype unchanged |
| The prototype's tests on the unchanged code | 3 failed, 46 passed, over the four files of the focused run | *[measured]* production files restored to `main`'s, tests kept |
| The prototype's full gate | `make ci` exit 0 in one run, 16 steps, 4,824 passed, 8 skipped, 100.00 % | *[measured]* `make ci` in the sprint worktree, redirected to a file |
| The prototype's guards can fail | 17 planted breaks, 17 red, each on the test named for it | *[measured]* one at a time on the focused run, each restored, green after |
| Sizes after the change | `tests/test_master_wake_window.py` 81 lines (new); `tests/test_deploy_script_invariants.py` 169 (178 before); `surfaces/dashboard/settings.py` 178 (unchanged) | *[measured]* on the prototype's bytes, LF |
| The script still parses | 0 parse errors | *[measured]* PowerShell's parser on the prototype's file |

---

## Scope — and what is deliberately NOT here

1. **`infra/deploy-agents.ps1`:** the master's default wake and the comment above it, two lines.
2. **`surfaces/dashboard/settings.py`:** `master_window_start_utc` defaults to `22:00`, one line.
3. **Tests**, per the Test plan: one new file, one existing test removed, one existing line changed.
4. **The law cycle** as answered above.

Replace the production text with **exactly** what the Appendix gives.

### Out of scope (do NOT build this sprint)

- **No other parameter of the script changes**, and nothing below its `param(...)` block.
- **`surfaces/dashboard/time_windows.py` does not change**: it reads the setting.
- **`surfaces/queries/fleet_check.py` does not change**, its comment that names `20:25-00:30`
  included, and neither does the `why` of `readiness_failure_max_age_minutes`. How long a failed
  check stays shown across a weekend is not measured ([DL-295](../design-log.md)).
- **`orchestration/`, `agents/`, `kernel/` and `contracts/` do not change.** The new tests read
  three of their values; none of the three moves.
- **The tests' shared `_settings()` does not change**: it keeps `20:25`.
- **The rest of work-queue 131 is not here**: winding the fleet down when the run completes (a),
  the answer deadline of a held run (b), the dispatcher's line on a fire that places nothing (d).
- **No deploy, no `az` call, no run of the script.** You have no network.

### The road not taken (LAW-06)

- **Leave the default and pass `-MasterScaleStart` at every `up`.** Rejected, as in DL-295: the
  value then lives in a document, and the first `up` that forgets it moves the master's wake.
- **Put 20:25 back on the live master, so the fleet follows the script.** Rejected: the operator
  chose 22:00 on 2026-10-12 and has not reopened it.
- **Wake at 22:25, five minutes before the run.** It would save 25 minutes of the master a
  night. Rejected here: the operator named 9:00 Melbourne; not this sprint's to change.
- **Have the dashboard read the live rule from Azure.** Rejected, as in DL-295: a new read path
  and its failure modes for one value.
- **Change `preflight_max_age_minutes` or the master's interval.** Not needed: with the wake at
  22:00 every placing tick finds a check inside the limit (test M3).

---

## The design decisions — made, and recorded in DL-300

They are recorded with their rejected alternatives. **Do not add a design-log entry.**

1. The script's default is the live wake, `0 22 * * 1-5`, and its comment names the decision
   and the one check, so a full `up` with no window parameter keeps it.
2. The dashboard's `master_window_start_utc` defaults to `22:00`. The existing test
   `test_schedule_defaults_are_the_deployed_schedule` keeps it equal to the script's.
3. The test named for two retries is removed and its job taken by one that says what the wake
   is for: the check made at the wake is readable at least 5 minutes before the first placing
   tick and is no older than the dispatcher's limit at that tick. Five minutes is six times the
   slowest landing measured (50 seconds).
4. A second test holds the master's interval, the dispatcher's limit and the wake against each
   other: at each of the six placing ticks the newest readable check is inside the limit,
   counting a check as readable two minutes after it starts. It changes no value.
5. The law changes in its `PARAM` table only, v1.8.

---

## Blast radius — measured 2026-10-14

| What | Detail |
| --- | --- |
| Files changed | `infra/deploy-agents.ps1` (2 lines); `surfaces/dashboard/settings.py` (1 line); `tests/test_master_wake_window.py` (new, about 80 lines); `tests/test_deploy_script_invariants.py` (178 → 169); `surfaces/tests/test_dashboard_window_days.py` (1 line); surfaces `laws.md`; `docs/laws/INDEX.md`, `ledger.md`; `pyproject.toml`, `uv.lock` |
| Agents affected | none; surfaces only |
| Contract change? | No |
| Graph vocabulary change? | No |
| New env keys / tunables | none (`DASHBOARD_MASTER_WINDOW_START_UTC` exists and is unset) |
| Deploy implication | none. The dashboard runs from the main checkout and shows the new wake at its next start. The script's default matters at the next full `up`; a retag does not touch scale rules |
| Rollback | Revert the commit. The live wake does not move either way: `az` set it |

**Named consequences, not built (the operator has been told):**

- A check that fails at the wake has no retry before 22:30. The run is held and the operator is
  told on Telegram. The master's repeat lands at about 23:01; if it passes, the 23:10 tick
  releases the hold and places the run, 20 minutes before the window's end. A night with one
  debate took 10 to 14 minutes (DL-294); a longer night is not measured. Work-queue 131 (b).
- For a run day before 2026-10-12 the dashboard's log window will start at 22:00 and leave out
  the master's lines from 20:25 of that day.

---

## Steps, in order

1. **Read the laws** and write the Law reading record.
2. **Plant the failing tests first** (Test plan) and watch them fail on the unchanged code. Paste the red output.
3. **Apply the Appendix** to the two production files, exactly.
4. **Law cycle** as answered above, every item.
5. **Prove the guards can fail (DL-70):** at least the breaks listed under Traps, one at a time, each red on the test named for it, each restored.
6. **`make ci` green**, every step of the `ci:` target (sixteen; count them from the `Makefile`), **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

New file `tests/test_master_wake_window.py`, module docstring with `Agent: tooling`. **Name the
three tests exactly as given**: the planner's break script looks for these names. Read the
script's parameters with the regex `surfaces/tests/test_dashboard_schedule.py` uses; build both
settings with `_env_file=None`. All times UTC, on any one fixed weekday.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| M1 | `test_script_defaults_are_the_live_wake_window` | the script's text | the two lines of Appendix 1 are in it, one directly above the other, byte for byte; `[string]$AgentScaleStart = '30 22 * * 1-5'` and `[string]$ScaleEnd = '30 23 * * 1-5'` are in it; the words `preflight retries` are nowhere in it |
| M2 | 🎯 `test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick` | the wake: the minute and hour of the script's `MasterScaleStart`; the tick: `_ACTION_START`; the limit: `OrchestratorSettings(_env_file=None).preflight_max_age_minutes` | `timedelta(minutes=5) <= tick - wake <= timedelta(minutes=limit)`. On the unchanged code it fails: 125 minutes against 70 |
| M3 | `test_every_placing_tick_finds_a_fresh_check` | checks readable at wake + 2 minutes + k × `MasterSettings(_env_file=None).fleet_preflight_interval_minutes`, k = 0 to 3; ticks every ten minutes from `_ACTION_START` to `_ACT_BY`, both included | there are six ticks, and at each the newest check readable at or before it is no older than the limit. 🪤 It passes on the unchanged code too: it guards three values against each other, and the breaks below prove it can fail |

Existing tests changed: **two, and no other.**

- `tests/test_deploy_script_invariants.py::test_master_scale_window_starts_before_the_two_pre_dispatch_retries`
  is **removed**, whole. M1 takes its job. Nothing else in that file changes.
- `surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows`: the one
  line `assert start == datetime(2026, 9, 25, 20, 25, tzinfo=UTC)` becomes
  `assert start == datetime(2026, 9, 25, 22, 0, tzinfo=UTC)`.

If any other existing test fails, stop and report.

---

## Success factors

- [ ] Every row of the Test plan is a passing test, under the name given.
- [ ] `git hash-object` prints, on LF bytes, `c6ce85287bfa5f2c17ac5b303cdf9c535c5d1e43` for `infra/deploy-agents.ps1` and `0b26950dd75eeddfdf72b5c8e5c03edc6d25311d` for `surfaces/dashboard/settings.py`, or each difference is explained.
- [ ] Two existing tests changed as named and no other (`git diff --stat main -- '*test_*.py'` shows the new file, the invariants file and the window-days file).
- [ ] Law cycle done, every item: the `PARAM` row as given, `LOCKED v1.8`, the Changelog entry, the surfaces' row in `INDEX.md` and in `ledger.md`; `check_param_law_sync.py` exits 0.
- [ ] Every guard planted, watched to fail on the test named for it, restored, stated per guard.
- [ ] Every touched module under 200 lines.
- [ ] `make ci` exit 0, sixteen steps, 100.00 % coverage.

---

## Traps

🪤 **Change the script's default and not the dashboard's, or the other way, and one existing test
goes red**: `test_schedule_defaults_are_the_deployed_schedule` keeps the two equal. That is the
guard working; change both.
🪤 **The old comment holds a `§`.** Replace the whole line with the Appendix's; the file is UTF-8
with LF endings and must stay so. Check with `git diff --stat`: two lines changed in the script.
🪤 **`_settings()` in the tests passes `20:25` itself**; `DashboardSettings(_env_file=None)` and
the two other settings built with `_env_file=None` give the real defaults. A setting built
without it reads a `.env` if one is there.
🪤 **M3 passes before the change.** Do not report it as a red-first test. Its proof is the breaks.
🪤 **A wake after the tick leaves M3 with no check to read**; M2 is the test that says so. Do not
make M3 swallow the empty case.
🪤 **`tests/` counts for the 200-line block**, and `tests/test_deploy_script_invariants.py` only
shrinks here.
🪤 **The script is PowerShell: the gate cannot read it.** The tests read its text; do not run it.

Breaks to plant, at the least, each alone: the script's master start `25 20 * * 1-5` again (M1,
M2 and the existing schedule test go red); the old comment left above the new value (M1); the
master's start `28 22`, `15 21` and `45 22` (M2 each time); the script's master, agents or end
on other days or hours (M1, and `test_defaults_are_the_deployed_windows`); the dashboard's
default `20:25` again (the schedule test and `test_defaults_are_the_deployed_windows`);
`preflight_max_age_minutes` 25 (M2) and 50 (M3); the master's interval 120 (M3);
`_ACTION_START` at 22:02 (M2); `_ACT_BY` at 23:50 (M3). The last five are planted in files this
sprint does not change: restore each before the next.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module under 200 lines. Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- Faults, not silent failure.
- `make ci` every step green, 100.00 % coverage floor, **never measured through a pipe**.
- PATCH bump, `uv.lock` staged with it. If `uv lock` cannot resolve in your sandbox, say so and
  say exactly how `uv.lock` was touched.
- Secrets never through the worktree. The worktree has no `.env`; nothing here needs one.

---

## Sequencing after merge (the planner's)

1. `make gate-ran` from the proving worktree, the printed SHA checked against `git rev-parse HEAD`.
2. The planner re-measures: the two blobs against the Appendix, the planner's own test file run
   beside the builder's, the break script on the built tree (17 breaks), the open CodeQL alerts
   set-diffed against the last merged branch's.
3. **F1**, at no cost and read-only: on the merged `main`, the script's own `Up` with every call
   a stand-in gives 16 rules equal to the 16 live rules read the same hour; the dashboard names
   22:00 UTC as the next wake at 20:30 and at 21:30 UTC on a weekday and labels the master's
   window 09:00-10:30 Melbourne.
4. No deploy. `docs/deployment.md` and STATE lose the line that says a full `up` must pass
   `-MasterScaleStart`.

[S273](sprint-273-the-secrets-scan-reads-every-file-as-utf-8.md) is with its builder and changes
no file this sprint changes; the two meet only in the sprint list. Whichever is reviewed second
takes `main` in first.

---

## Handover — paste this to Codex

```text
You are building Sprint 274 in the worktree ../ta-s274, on the branch
sprint-274-a-full-up-keeps-the-masters-live-start. Never work on main.

Read docs/sprints/sprint-274-a-full-up-keeps-the-masters-live-start.md, whole, before anything
else. It is the spec, and its bottom sections are your handback.

In order:
1. Read surfaces/laws/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any code.
2. Write the three tests of the Test plan in the new file tests/test_master_wake_window.py,
   under the names given. Remove the one test named from tests/test_deploy_script_invariants.py
   and change the one line named in surfaces/tests/test_dashboard_window_days.py. Run
   uv run pytest tests/test_master_wake_window.py tests/test_deploy_script_invariants.py
   surfaces/tests/test_dashboard_window_days.py surfaces/tests/test_dashboard_schedule.py --no-cov
   on the unchanged code and paste the red output into the Closeout (3 failed, 46 passed on the
   planner's prototype; M3 passes before the change, by design).
3. Apply the Appendix to infra/deploy-agents.ps1 and surfaces/dashboard/settings.py, exactly.
   Change nothing else in production code.
4. Do the law cycle the spec answers, every item: the PARAM row as given, the status line to
   LOCKED v1.8, a Changelog entry, the surfaces' row in docs/laws/INDEX.md and
   docs/laws/ledger.md (v1.8; the gate does not check it).
5. Plant the breaks listed under Traps one at a time; each must go red on the test named;
   restore each before the next.
6. Bump the version (PATCH) and stage uv.lock. Run make ci redirected to a file and read the file.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md.

DO NOT: run infra/deploy-agents.ps1 or any az command; change any other parameter of the script
or anything below its param block; change surfaces/dashboard/time_windows.py,
surfaces/queries/fleet_check.py, the tests' shared _settings(), orchestration/, agents/, kernel/
or contracts/ (the breaks of step 5 are restored, never kept); change any existing test but the
two named; add a design-log entry; add or reword a law clause; use noqa; let any module reach 200
lines; measure make ci through a pipe.

Traps: the dashboard's default and the script's are held equal by an existing test, so change
both; the script is UTF-8 with LF endings and its old comment holds a section sign; _settings()
in the tests passes 20:25 itself and a setting built without _env_file=None can read a .env; M3
is not a red-first test.

If a law contradicts the spec, or any other existing test fails, STOP and report. State anything
not done as "not done" or "verified failing". Never write a Result for work you have not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| <element> | <files> | <clause IDs> | <Yes/No + what changed> |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** <Yes/No + what it owed and what was done>

**Contradictions found between a law and this spec:** <none | what, and what you did>

**Laws found silent where a decision was needed:** <none | what, and the drift row filed>

**Clauses that were ⬜ and are now proven:** <IDs, and the rollup in ledger.md + INDEX.md>

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| M1 | <name> | <file> | PASS/FAIL | <clause IDs> |

**Tests added beyond the plan:** <none | what and why>

---

## Closeout — evidence

**Status:** <BUILT | MERGED>

**Tree the proofs ran in (and `.env` present?):** <path, branch, .env yes/no>

**Result:** <what is now true, in the artefact's own words — not the intent restated>

**Files changed:** <list>

**Design decisions:** recorded as [DL-300](../design-log.md); none added by the build.

**Proof — the red run first:**

```text
<the failing test output, before the implementation>
```

**Proof — the green run:**

```text
<the passing output>
```

**Guards planted:** <per guard: what was planted, the test that failed, that it was restored>

**Module line counts:** <file **n**, file **n**>

**`make ci`:** redirected to `<path>`. Exit code <n>. `<N passed, M skipped>`, coverage `<100.00 %>`.
dependency audit `<result>`. detect-secrets `<result>`.

**`make gate-ran`:** the planner's, from the proving worktree.

**Not met / verified failing:** <plainly, or "none">

---

## Return notes

- <Scope held / where it moved and why.>
- <What you disagreed with in the spec after reading the laws.>
- <What the next sprint should know that is not obvious from the diff.>

---

## Appendix — the change, measured on the planner's prototype

### 1. `infra/deploy-agents.ps1` — lines 20 and 21 become these two

The line above them (`[string]$Tag = 'latest',`) and the line below (the `# DL-294: weekdays
only` comment) stay as they are. Two spaces of indent, no trailing space.

```text
  # DL-294 amendment 1: one readiness check, at the wake, before the 22:30 UTC dispatch.
  [string]$MasterScaleStart = '0 22 * * 1-5',
```

### 2. `surfaces/dashboard/settings.py` — the default of `master_window_start_utc`

The field becomes this; only the first argument changes.

```python
    master_window_start_utc: str = tunable(
        "22:00",
        why="Matches $MasterScaleStart in infra/deploy-agents.ps1 (test-pinned).",
    )
```

### 3. The numbers the new tests use, and where each comes from

| Number | Value | Basis |
| --- | --- | --- |
| The least lead of the wake over the first placing tick | 5 minutes | six times the slowest landing measured: 50 seconds after a wake, over eight nights |
| How long after it starts a check counts as readable | 2 minutes | the same eight nights: 29 to 50 seconds; a repeat follows 60 minutes and 9 to 24 seconds later |
| The spacing of the placing ticks | 10 minutes | the dispatcher's cron in `orchestration/packs/trading_tunables.json` (`*/10 22-23 * * 1-5`) |
| The number of placing ticks | 6 | 22:30 to 23:20, both included |
