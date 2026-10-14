<!-- Agent: planning | Role: sprint handover -->
# Sprint 274 — a full `up` keeps the master's 22:00 wake, and the dashboard shows the wake the fleet has

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-274-a-full-up-keeps-the-masters-live-start`
**Status:** MERGED 2026-10-14 — `0.125.10`, fast-forwarded to `17655eea`, tag `v0.125.10`, GATE PROVEN `17655eea` (CI, CodeQL, Security Findings); F1 passed at no cost; no deploy
**Version:** PATCH: `0.125.10`
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

- [x] Every row of the Test plan is a passing test, under the name given.
- [x] `git hash-object` prints, on LF bytes, `c6ce85287bfa5f2c17ac5b303cdf9c535c5d1e43` for `infra/deploy-agents.ps1` and `0b26950dd75eeddfdf72b5c8e5c03edc6d25311d` for `surfaces/dashboard/settings.py`, or each difference is explained.
- [x] The original two existing tests changed as named, plus the planner-authorized third comparison in `tests/test_check_version_scheme.py` (quoted below); no other existing test changed. The test diff has four files: one new and three existing.
- [x] Law cycle done, every item: the `PARAM` row as given, `LOCKED v1.8`, the Changelog entry, the surfaces' row in `INDEX.md` and in `ledger.md`; `check_param_law_sync.py` exits 0.
- [x] Every guard planted, watched to fail on the test named for it, restored, stated per guard.
- [x] Every touched module under 200 lines.
- [x] `make ci` exit 0, sixteen steps, 100.00 % coverage.

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
| Dashboard setting and surfaces PARAM amendment | `surfaces/laws/laws.md` and `surfaces/laws/test-plan.md`, whole; `docs/laws/conventions.md` and `docs/laws/drift-register.md` (read 2026-10-14) | `PARAM`; conventions §§2–4, 7 and 7a; `SRF-DEP-01` / `SRF-DEP-02` and `SRF-NEV-01` / `SRF-NEV-02` / `SRF-NEV-03` reviewed | No. The wake hour is a declared parameter, not a new functional guarantee. No clause or law test-plan row changes. |
| Script's master wake default and comment | `surfaces/laws/laws.md`, whole; `docs/deployment.md`; `docs/laws/conventions.md` and `docs/laws/drift-register.md` | `PARAM`; `SRF-DEP-*` / `SRF-NEV-*` reviewed; no clause fixes the wake hour | No. Apply only Appendix 1's two lines; do not run the script or Azure commands. |
| New wake-window tests and two named existing test edits | `orchestration/laws/dispatcher/laws.md` and `agents/master/laws/laws.md`, whole; surfaces laws and test-plan above | `DSP-IN-03` (freshness), `DSP-TRG-01` (placing ticks); dispatcher `PARAM` (`preflight_max_age_minutes`); master `PARAM` (`fleet_preflight_interval_minutes`) | No. Read the existing settings with `_env_file=None`; no master clause fixes the wake hour. M3's proof comes from restored breaks, not red-first failure. |
| Third existing-test edit, authorized by the planner on 2026-10-14 | `CLAUDE.md` version-scheme and proof rules re-read before this edit; this spec and the planner authorization below | Version scheme `MAJOR.MMM.PP`; `LAW-02` | Yes. Replace only the authorized version comparison, with no import or test-name change; normalized lock agreement replaces the old string-inequality assumption. No additional law amendment is owed. |
| Law rollups and sprint handback | `docs/laws/INDEX.md`; `docs/laws/conventions.md`; `CLAUDE.md`; this spec, whole | Conventions §§3–4; `LAW-02` proof discipline | No. Keep 31 / 38, update both surfaces version labels, and record evidence here. `docs/STATE.md` is excluded by this handover. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. Done: the exact surfaces PARAM row, LOCKED v1.8, its Changelog entry, and both surfaces rollup rows at v1.8; counts remain 31 / 38. The PARAM/settings and law-coverage checks exited 0. The reading above was recorded before any code change; no clause or contracts file changed.

**Contradictions found between a law and this spec:** none.

**Laws found silent where a decision was needed:** No clause fixes the wake hour. DL-300 already decides this deployment/settings parameter choice; no new decision or drift row is needed.

**Clauses that were ⬜ and are now proven:** none; the counts stay 31 / 38.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| M1 | `test_script_defaults_are_the_live_wake_window` | `tests/test_master_wake_window.py` | PASS (50-case focused run and full CI) | none: deployment/PARAM guard, DL-300 |
| M2 | `test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick` | `tests/test_master_wake_window.py` | PASS (50-case focused run and full CI) | `DSP-IN-03` / `DSP-TRG-01` |
| M3 | `test_every_placing_tick_finds_a_fresh_check` | `tests/test_master_wake_window.py` | PASS (50-case focused run and full CI; not red-first) | `DSP-IN-03` / `DSP-TRG-01` |
| V1 (planner-authorized existing test) | `test_real_pyproject_passes_despite_normalized_lockfile` | `tests/test_check_version_scheme.py` | PASS (50-case focused run and full CI) | repository version-scheme rule; no agent clause |

**Tests added beyond the plan:** none. Three existing tests were edited: the two named in the original plan and the planner-authorized V1 comparison below.

---

## Closeout — evidence

**Status:** MERGED — the build proof is the builder's, below; the remote gate, the breaks and F1 are in the planner's review at the merge.

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s274`, branch `sprint-274-a-full-up-keeps-the-masters-live-start`, `.env` absent. Red, green and guard proofs ran on base `c5e54c360ba21cf2274686347945512acab22a41` plus this work. Before full CI, this branch fast-forwarded to the already-merged S273 at `25a0129dd600464d2dfb964cf623eea12acd6faa`; no work was performed on `main`. Both Appendix blobs stayed exact.

**Result:** The script retains the master's live `0 22 * * 1-5` wake by default and the dashboard defaults to `22:00`; both production blobs match the Appendix hashes. The three wake tests and the third authorized existing-test comparison pass in the 50-case focused run and full CI. All 17 planted breaks went red and were restored byte for byte. The surfaces PARAM amendment and both v1.8 rollups pass their checks, with 31 / 38 unchanged. PATCH `0.125.10` resolved offline; full `make ci` exited 0 over all 16 steps with 4,834 passed, 8 skipped and 100.00 % coverage. Audit and both secret scans passed.

**Files changed:** `docs/laws/INDEX.md`, `docs/laws/ledger.md`, `docs/sprints/README.md`, `docs/sprints/sprint-274-a-full-up-keeps-the-masters-live-start.md`, `infra/deploy-agents.ps1`, `pyproject.toml`, `surfaces/dashboard/settings.py`, `surfaces/laws/laws.md`, `surfaces/tests/test_dashboard_window_days.py`, `tests/test_check_version_scheme.py`, `tests/test_deploy_script_invariants.py`, `tests/test_master_wake_window.py`, `uv.lock`.

**Planner authorization — 2026-10-14 (quoted; third authorized existing-test edit):**

> Authorized (planner): one more edit to an existing test, beyond the two the spec names.
>
> File: tests/test_check_version_scheme.py, test_real_pyproject_passes_despite_normalized_lockfile.
> Replace line 60:
>
> ```python
>     assert project_version != lock_version
> ```
>
> with:
>
> ```python
>     assert [int(part) for part in project_version.split(".")] == [
>         int(part) for part in lock_version.split(".")
>     ]
> ```
>
> Keep the test's name, add no import, and change nothing else in the file.
>
> Why: the old line held only while the patch group began with 0 (0.125.09 locks as 0.125.9).
> At 0.125.10 both strings match, and that is correct. The new line checks that the lock
> agrees with pyproject once normalized, so it also fails on a stale lock.
>
> Then resume: rerun the focused suite (49 tests plus this one) after the S273
> fast-forward and your import-order fix, run the full `make ci` redirected to a file,
> and finish the remaining steps as specced (coverage, audit, secrets, BUILT status, commit).
> In the closeout, list this as a third authorized existing-test edit and quote this
> authorization. Do not merge main in; the planner does that at review.

**Existing-test edits — three, all authorized:** remove `test_master_scale_window_starts_before_the_two_pre_dispatch_retries`; change only the named start assertion in `test_defaults_are_the_deployed_windows`; apply exactly the planner's three-line normalization comparison in `test_real_pyproject_passes_despite_normalized_lockfile`. The third test keeps its name and imports; every other byte of that file is unchanged.

**Design decisions:** recorded as [DL-300](../design-log.md); none added by the build.

**Proof — the red run first:**

```text
============================= test session starts =============================
collected 49 items

tests\test_master_wake_window.py FF.                                     [  6%]
tests\test_deploy_script_invariants.py ..........                        [ 26%]
surfaces\tests\test_dashboard_window_days.py ........................... [ 81%]
.F                                                                       [ 85%]
surfaces\tests\test_dashboard_schedule.py .......                        [100%]

================================== FAILURES ===================================
________________ test_script_defaults_are_the_live_wake_window ________________
tests\test_master_wake_window.py:32: in test_script_defaults_are_the_live_wake_window
    assert (
E   assert b"  # DL-294 amendment 1: one readiness check, at the wake, before the 22:30 UTC dispatch.\n  [string]$MasterScaleStart = '0 22 * * 1-5',\n" in b'# deploy-agents.ps1 \xe2\x80\x94 One-command fleet deploy/teardown for Azure Container Apps.\n#\n#   pwsh infra/depl... }\n  \'postgres-flip\' { Flip-PostgresRoles }\n  \'servicebus-flip\' { Flip-ServiceBusSas }\n  \'down\' { Down }\n}\n'
_____ test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick ______
tests\test_master_wake_window.py:48: in test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick
    assert timedelta(minutes=5) <= lead <= timedelta(minutes=limit)
E   assert datetime.timedelta(seconds=7500) <= datetime.timedelta(seconds=4200)
E    +  where datetime.timedelta(seconds=4200) = timedelta(minutes=70)
___________________ test_defaults_are_the_deployed_windows ____________________
surfaces\tests\test_dashboard_window_days.py:120: in test_defaults_are_the_deployed_windows
    assert start == datetime(2026, 9, 25, 22, 0, tzinfo=UTC)
E   assert datetime.datetime(2026, 9, 25, 20, 25, tzinfo=datetime.timezone.utc) == datetime.datetime(2026, 9, 25, 22, 0, tzinfo=datetime.timezone.utc)
E    +  where datetime.datetime(2026, 9, 25, 22, 0, tzinfo=datetime.timezone.utc) = datetime(2026, 9, 25, 22, 0, tzinfo=datetime.timezone.utc)
=========================== short test summary info ===========================
FAILED tests/test_master_wake_window.py::test_script_defaults_are_the_live_wake_window
FAILED tests/test_master_wake_window.py::test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick
FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
======================== 3 failed, 46 passed in 5.51s =========================
RED_EXIT=1
```

**Proof — the green run (after the S273 fast-forward, import-order fix and third authorized existing-test edit):**

```text
============================= test session starts =============================
collected 50 items

tests\test_master_wake_window.py ...                                     [  6%]
tests\test_deploy_script_invariants.py ..........                        [ 26%]
surfaces\tests\test_dashboard_window_days.py ........................... [ 80%]
..                                                                       [ 84%]
surfaces\tests\test_dashboard_schedule.py .......                        [ 98%]
tests\test_check_version_scheme.py .                                     [100%]

============================= 50 passed in 3.81s ==============================
RESUMED_FOCUSED_EXIT=0
```

**Guards planted:** all 17, each alone. The output below names every failing test and confirms byte-for-byte restoration before the next plant. Daily-field plants fail M1 and the deployed-windows test; hour plants fail M1 and the schedule-equality test. M3 passed on the unchanged production code by design and went red for G14, G15 and G17.

```text
G01 old master wake 20:25: exit 1; 3 failed in 5.31s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_script_defaults_are_the_live_wake_window
  FAILED tests/test_master_wake_window.py::test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick
  FAILED surfaces/tests/test_dashboard_schedule.py::test_schedule_defaults_are_the_deployed_schedule
G02 old retries comment above new wake: exit 1; 1 failed in 1.51s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_script_defaults_are_the_live_wake_window
G03 master wake 22:28: exit 1; 1 failed in 1.41s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick
G04 master wake 21:15: exit 1; 1 failed in 1.38s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick
G05 master wake 22:45: exit 1; 1 failed in 1.40s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick
G06 master days daily: exit 1; 2 failed in 2.09s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_script_defaults_are_the_live_wake_window
  FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
G07 master hour 21:00: exit 1; 3 failed in 5.33s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_script_defaults_are_the_live_wake_window
  FAILED tests/test_master_wake_window.py::test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick
  FAILED surfaces/tests/test_dashboard_schedule.py::test_schedule_defaults_are_the_deployed_schedule
G08 agent days daily: exit 1; 2 failed in 2.09s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_script_defaults_are_the_live_wake_window
  FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
G09 agent hour 21:30: exit 1; 2 failed in 5.16s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_script_defaults_are_the_live_wake_window
  FAILED surfaces/tests/test_dashboard_schedule.py::test_schedule_defaults_are_the_deployed_schedule
G10 end days daily: exit 1; 2 failed in 2.14s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_script_defaults_are_the_live_wake_window
  FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
G11 end hour 00:30: exit 1; 2 failed in 5.28s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_script_defaults_are_the_live_wake_window
  FAILED surfaces/tests/test_dashboard_schedule.py::test_schedule_defaults_are_the_deployed_schedule
G12 dashboard wake 20:25: exit 1; 2 failed in 13.84s; RESTORED byte-for-byte
  FAILED surfaces/tests/test_dashboard_schedule.py::test_schedule_defaults_are_the_deployed_schedule
  FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
G13 preflight limit 25 minutes: exit 1; 1 failed in 1.89s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick
G14 preflight limit 50 minutes: exit 1; 1 failed in 1.73s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_every_placing_tick_finds_a_fresh_check
G15 master interval 120 minutes: exit 1; 1 failed in 1.77s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_every_placing_tick_finds_a_fresh_check
G16 first placing tick 22:02: exit 1; 1 failed in 1.95s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick
G17 last placing tick 23:50: exit 1; 1 failed in 1.87s; RESTORED byte-for-byte
  FAILED tests/test_master_wake_window.py::test_every_placing_tick_finds_a_fresh_check
GUARDS_PROVEN=17/17; ALL_MUTATED_FILES_RESTORED byte-for-byte
```

**Module line counts:** `tests/test_master_wake_window.py` **68**, `tests/test_deploy_script_invariants.py` **169**, `surfaces/tests/test_dashboard_window_days.py` **122**, `tests/test_check_version_scheme.py` **64**, `surfaces/dashboard/settings.py` **178**; all under 200, all LF. No `noqa` added.

**`make ci`:** redirected to `C:\Users\yury_\AppData\Local\Temp\ta-s274-evidence-20261014\ci-resumed.txt`; the complete file was read and its proof lines extracted below. Exit code **0**, all **16** commands counted from `Makefile`; **4,834 passed, 8 skipped**, coverage **100.00 %**. Dependency audit: **no unaccepted vulnerabilities; one accepted advisory re-checked** (`PYSEC-2026-2447`, diskcache 5.6.3). detect-secrets: **Passed**. Untracked-secrets check: **no untracked files to scan**, exit 0.

**Proof — resumed full gate (actual log lines and captured exit):**

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
uv run lint-imports
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
uv run python scripts/check_tracker_size.py
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
uv run python scripts/check_dependency_audit.py
uv run pre-commit run detect-secrets --all-files
uv run python scripts/check_untracked_secrets.py
Success: no issues found in 1205 source files
Contracts: 5 kept, 0 broken.
TOTAL                                                           20473      0   4358      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 4834 passed, 8 skipped, 2470 warnings in 444.87s (0:07:24) ==========
accepted: PYSEC-2026-2447 (diskcache 5.6.3) - reachable only via the 'optimizer' extra, installed by 1 of 15 Dockerfiles; each installing command excludes diskcache by name; the dev group carries it too, and every sync passes --no-dev or excludes it by name; no fix release exists; every deployed optimizer installation excludes diskcache by name (S254, DL-266, ADR-0032) [DL-184] - retire when diskcache publishes a fixed release, or the optimizer extra is dropped
No unaccepted vulnerabilities; 1 accepted advisory re-checked
Detect secrets...........................................................Passed
detect-secrets (untracked): no untracked files to scan
CI_EXIT=0
```

**Prior CI attempts — retained evidence:** attempt 1 exited 2 at ruff I001 in the new test; only import ordering was fixed. Attempt 2 passed the first 12 steps and stopped during pytest at the existing version-string inequality; that failure was reproduced without editing it, and the planner then authorized the exact third existing-test replacement quoted above. The resumed 50-case focused run and full gate both pass after that replacement.

**Proof — redirected CI attempt 1 (actual output):**

```text
uv run ruff check . --output-format=github
::error title=ruff (I001),file=C:\Users\yury_\Downloads\project\ta-s274\tests\test_master_wake_window.py,line=8,endLine=16::tests\test_master_wake_window.py:8:1: I001 Import block is un-sorted or un-formatted%0A  help: Organize imports
make: *** [Makefile:47: ci] Error 1
```

**Proof — CI commands reached before the stop (actual log lines):**

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
uv run lint-imports
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
uv run python scripts/check_tracker_size.py
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
```

**Proof — the prior existing-test stop, before planner authorization:**

```text
============================= test session starts =============================
collected 1 item

tests\test_check_version_scheme.py F                                     [100%]

================================== FAILURES ===================================
___________ test_real_pyproject_passes_despite_normalized_lockfile ____________
tests\test_check_version_scheme.py:60: in test_real_pyproject_passes_despite_normalized_lockfile
    assert project_version != lock_version
E   AssertionError: assert '0.125.10' != '0.125.10'
=========================== short test summary info ===========================
FAILED tests/test_check_version_scheme.py::test_real_pyproject_passes_despite_normalized_lockfile
============================== 1 failed in 1.36s ==============================
EXISTING_FAILURE_EXIT=1
```

**Proof — Appendix hashes, parsing, scope and lock:**

```text
c6ce85287bfa5f2c17ac5b303cdf9c535c5d1e43
0b26950dd75eeddfdf72b5c8e5c03edc6d25311d
i/lf    w/lf    attr/text=auto eol=lf infra/deploy-agents.ps1
i/lf    w/lf    attr/text=auto eol=lf surfaces/dashboard/settings.py
POWERSHELL_PARSE_ERRORS=0
Resolved 180 packages in 1.84s
Updated trading-agents v0.125.9 -> v0.125.10
UV_LOCK_OFFLINE_EXIT=0
 surfaces/tests/test_dashboard_window_days.py |  2 +-
 tests/test_deploy_script_invariants.py       |  9 ----
 tests/test_master_wake_window.py             | 68 ++++++++++++++++++++++++++++
 3 files changed, 69 insertions(+), 10 deletions(-)
```

`uv lock --offline` changed only the root package version from `0.125.9` to `0.125.10`; no dependency changed. `uv.lock` was staged with the PATCH bump. Repository git writes work. The final focused run above was performed after the already-completed S273 fast-forward and import-order fix. No further merge of `main` was made after the planner's resume instruction.

**`make gate-ran`:** not done; the planner's from the proving worktree. Push, remote proof, merge, deploy and live proof are not done.

**Not met / verified failing:** none among the local build success factors. The prior version-test failure is resolved by the exact planner-authorized edit. Push, remote gate, merge, deploy and live proof are **not done** and belong to review/follow-up; no script execution or Azure command ran.

---

## Return notes

- Scope held: both Appendix blobs are exact. The original two existing-test edits and the planner-authorized third edit are listed and quoted above; no other existing test changed. All transient orchestration/master breaks were restored byte for byte. `docs/STATE.md`, the design log, shared `_settings()`, excluded surfaces files and all contracts are unchanged. No deploy script or Azure command ran.
- No law/spec contradiction was found. The old version test assumed project and lock strings always differ; at PATCH `0.125.10` they correctly match. The planner authorized the exact numeric-component comparison, which retains the format gate and catches a stale lock. No import or test name changed.
- S273 was already brought into this branch in the earlier turn at `25a0129dd600464d2dfb964cf623eea12acd6faa`. The resumed focused and full gates ran on that tree plus S274. No further merge of `main` was made; the planner handles it at review. The full-suite count includes S273, explaining the difference from the prototype's 4,824 passes.
- M3 passes before the production change by design. Its proof is the red/restored limit, interval and final-tick plants. Neither a failed check at the new wake nor hold recovery was measured live here. Historical log windows before 2026-10-12 still start at the new 22:00 default, as the spec warns.
- The surfaces law test-plan header still names v1.6, predating the PARAM-only v1.7/v1.8 amendments; it was read and left unchanged as required. The clauses and 31 / 38 count are unchanged. Final handback/status edits are checked separately before commit.

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

## Planner's review at the merge — 2026-10-14

Re-measured by the planner in `../ta-s274` on the builder's commit `ae57a478` and on the merge
commit `17655eea`. Nothing here is taken from the handback.

- **The two production files are the measured prototype byte for byte.**
  `infra/deploy-agents.ps1` is `c6ce8528` and `surfaces/dashboard/settings.py` is `0b26950d`, the
  Appendix's blob ids. Against the spec's commit the branch changes the files the spec names, the
  version pair and the one test the planner authorized during the build, and no other.
- **The builder's new test file is its own** (`tests/test_master_wake_window.py`, 68 lines): the
  three functions under the names the spec fixed, M2 and M3 citing `DSP-IN-03` / `DSP-TRG-01`.
  The two existing-test edits the spec names are the prototype's blobs (`aeaa6fba`, `95360dd9`).
- **One stop during the build, the planner's miss.** The PATCH bump to `0.125.10` failed
  `tests/test_check_version_scheme.py::test_real_pyproject_passes_despite_normalized_lockfile`,
  which asserted that `uv.lock` spells the version differently from `pyproject.toml`. That held
  only while the last group began with 0 (`0.125.09` is locked as `0.125.9`); no tag since the
  test was written (S221, `39c28c72`) had a patch of 10 or more. The prototype's `make ci` ran at
  the old version, never with the bump applied. The builder stopped as the spec told it to; the
  planner authorized a third existing-test edit, the two versions compared as numbers, which
  passes on `main` and on this branch and fails on a stale lock (measured before the
  authorization). The builder applied it exactly ([DL-300](../design-log.md) amendment 1).
- **The planner's own tests** (written for the prototype) were placed beside the builder's and run
  with the focused suite: 58 passed. They are not committed.
- **Guards.** The planner's 17 breaks, one at a time, each restored: **17 went red, each on the
  test named**, five of them planted in `orchestration/` and `agents/master/`; the tree was clean
  afterwards.
- **Law rows.** The surfaces' row reads v1.8 and 31 / 38 in `docs/laws/INDEX.md` and in
  `docs/laws/ledger.md`; the law gate checks the counts, not the label.
- **`main` was merged into the branch** (S273's follow-up and its record had landed): one
  conflict, the sprint list's rows 273 and 274, resolved with 273 from `main` and 274 from the
  branch.
- **Not re-run by the planner:** the local `make ci` on the builder's commit. The builder's
  sixteen-step pass (4,834 passed, 8 skipped, 100.00 %) is the builder's statement; the proof is
  the remote gate on the merge commit.
- **Gate.** `GATE PROVEN` for `17655eea`, run from `../ta-s274`, whose `HEAD` it is; `main` was
  fast-forwarded to that commit, so the proven commit is the merged one.
- **CodeQL.** 130 open alerts on the branch, 0 of them errors (116 notes, 14 warnings): the same 130, by number, as on the `chore-a-read-only-probe-folder-is-removed` branch, none new and none gone.
- **F1, at no cost, on the merged commit: passed.** The script's own `Up`, every `az` call and
  credential a stand-in (`up_scale_rules.ps1`), gives 16 scale rules, each equal to the live
  app's rule read with `az containerapp list` at 04:46 UTC the same day: 16 of 16, where `main`
  before gave 15 of 16 (the master's `25 20 * * 1-5`). The dashboard's default
  `master_window_start_utc` is 22:00, its label 09:00-10:30 Melbourne, and from 20:00 to 21:30
  UTC it names 22:00 as the master's next wake where it read the master as awake.
- **No deploy.** Neither file ships in an image: the deploy script runs from the operator's
  machine and the dashboard runs locally (a running dashboard keeps the old default until it is
  restarted). The fleet stays on `s272`.

Evidence outside the repo: OneDrive `trading-agents-data/wq131f-2026-10-14/`
(`breaks_on_built_17655eea.txt`, `s274-branch-runs.txt`, `s274-gate-ran.txt`,
`f1_up_rules_17655eea.txt`, `f1_rules_compare_17655eea.txt`, `f1_dashboard_17655eea.txt`,
`s274_merge_docs.py`).
