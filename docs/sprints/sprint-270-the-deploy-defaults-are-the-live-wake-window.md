<!-- Agent: planning | Role: sprint handover -->
# Sprint 270 — the deploy script's defaults are the live wake window, and the dashboard knows its weekdays

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-270-the-deploy-defaults-are-the-live-wake-window`
**Status:** MERGED 2026-10-12 — `0.125.08`, fast-forwarded to `5d242a8e`, tag `v0.125.08`, GATE PROVEN `5d242a8e` (CI, CodeQL, Security Findings); F1 passed at no cost; deploy owed
**Version:** `0.125.08` (PATCH)
**Effort:** S
**Decisions:** [DL-295](../design-log.md) (this sprint's five decisions, made and measured) · [DL-294](../design-log.md) (the operator's window, applied to the live fleet) · [work-queue 131](../work-queue.md) part (e)

> **Why this bump kind.** No new capability: the fleet already wakes on weekdays from 22:30 to
> 23:30 UTC. The deploy script and the dashboard still describe the window it had before, so a
> full `up` would put the old one back and the dashboard promises a check on a day nothing wakes.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `surfaces/laws/laws.md` | The surfaces' **locked constitution** (v1.6) | **LOCKED.** This sprint changes two rows of its `PARAM` table and no clause |
| `surfaces/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read only. No row changes: no clause governs the wake window |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `INDEX.md` and `ledger.md`: the surfaces' row reads v1.7 |

Binding sections here: **`PARAM`** (the table), **`SRF-DEP`**, **`SRF-NEV`**.

### The rule

1. **Before writing code**, read `surfaces/laws/laws.md` and its `test-plan.md`, whole.
2. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
3. **Write the Law reading record** (bottom of this file) **before** your first code change.
4. **If a law contradicts this spec, STOP and report.**
5. A test for behaviour a clause governs cites the clause ID in its docstring. *[read 2026-10-11]*
   no clause of the surfaces' law governs the wake window; if your reading finds one, cite it and
   say so in the Return notes.

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No file in `contracts/` changes and no clause is added or reworded.** The `PARAM` table follows
the settings, as the parameter gate requires. The cycle owed, every item of it:

- In `surfaces/laws/laws.md` the `window_end_utc` row is replaced and a `window_days_utc` row is
  added directly under it, with exactly this text:

  ```text
  | `window_end_utc` | `"23:30"` | `str` | YES | Matches `$ScaleEnd` in `infra/deploy-agents.ps1` and is test-pinned. |
  | `window_days_utc` | `"1-5"` | `str` | YES | The weekday field of the three scale windows in `infra/deploy-agents.ps1`, read as cron reads it, and is test-pinned. |
  ```

- The version goes to v1.7 and the Changelog gains one entry, in the form of the entries above it:
  `v1.7 — S270 / DL-295 (2026-10-11): PARAM only. window_end_utc is 23:30 and the new
  window_days_utc is 1-5, the operator's wake window (DL-294). No clause changes.`
- `docs/laws/INDEX.md` and `docs/laws/ledger.md`: the surfaces' row reads v1.7 and says what this
  sprint did, in the form the row already uses for S267. 🪤 **The law gate does not check this
  label**: it compares the counts only. Change both rows by hand.
- The counts stay 31 / 38. Let the gate say.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `surfaces/dashboard/settings.py`, `surfaces/dashboard/time_windows.py` | surfaces `laws.md` + `test-plan.md` | the `PARAM` table must match the settings fields (`check_param_law_sync.py`) |
| `infra/deploy-agents.ps1` | surfaces `laws.md` (`SRF-DEP`), `docs/deployment.md` | the three parameters are what a full `up` applies to the live fleet |

---

## Goal

A full `up` with no window parameters applies the window the operator chose (weekdays, the master
from 20:25 and the agents from 22:30 until 23:30 UTC), and the dashboard's next check and latest
window fall only on a day the fleet wakes.

## Why (context)

On 2026-10-11 the operator shortened the wake window and restricted it to weekdays
([DL-294](../design-log.md)). It was applied to the 16 live apps by hand. The deploy script's
defaults still hold the old window, so the next full `up` reverts it silently, and the dashboard
copies its window from those defaults.

### Measured, 2026-10-11 — read these before designing

Every row was measured on `main` at `01254b04` unless it says otherwise.

| Claim | Value | How it was measured |
| --- | --- | --- |
| The live window | master `25 20 * * 1-5`, agents `30 22 * * 1-5`, end `30 23 * * 1-5`, UTC | *[measured]* `az containerapp show` on each of the 16 apps after the change: 16 of 16 |
| The script's defaults | `25 20 * * *`, `30 22 * * *`, `30 00 * * *` | *[read]* `infra/deploy-agents.ps1:21-23`; every app's create and update passes them (`Get-CronScaleArgs`) |
| The dashboard copies three times of day from the script | `master_window_start_utc`, `agent_window_start_utc`, `window_end_utc` | *[read]* `surfaces/tests/test_dashboard_schedule.py::test_schedule_defaults_are_the_deployed_schedule` reads minute and hour only (`cron.split()[:2]`), so a weekday field does not break it |
| The dashboard has no notion of a weekday for a window | `next_master_wake` adds one day; `latest_window` steps back one day | *[read]* `surfaces/dashboard/time_windows.py`, whole file. On a Saturday it promises the next check on Saturday at 20:25 |
| `next_fire` already skips weekends | by the dispatcher's own calendar | *[read]* same file; not changed here |
| Existing tests that break on the prototype | 1: `tests/test_deploy_script_invariants.py::test_master_scale_window_starts_before_the_two_pre_dispatch_retries`, which pins the old literal | *[measured]* full suite in the sprint worktree |
| Existing tests that read the default end time | none: the tests' shared `_settings()` passes `window_end_utc="00:30"` itself | *[read]* `surfaces/tests/test_dashboard_costs.py:47`; *[measured]* they pass on the prototype unchanged |
| The prototype's tests on the unchanged code | 21 failed, 20 passed, over the new file and the invariants file | *[measured]* production files restored to `main`'s, tests kept |
| The prototype's full suite | 4,777 passed, 8 skipped, 100.00 % coverage (29 new cases) | *[measured]* `uv run pytest` in the sprint worktree, exit 0 |
| The prototype's guards can fail | 15 planted breaks, 15 red | *[measured]* one at a time on `surfaces/tests` and the invariants file, each restored, green after |
| Sizes after the change | `time_windows.py` 152 lines (121 before), `settings.py` 178 (174), `test_deploy_script_invariants.py` 194 (192) | *[measured]* on the prototype's bytes, LF |
| The script still parses | 0 parse errors | *[measured]* PowerShell's parser on the prototype's file |
| How long a failed fleet check stays shown | one day (`LAST_CHECK_HORIZON_MINUTES = 1440`), and its comment names the old window | *[read]* `surfaces/queries/fleet_check.py:25-28`. What the dashboard should show from Saturday to Monday is *[ASSUMED — not measured]* and not this sprint's |

---

## Scope — and what is deliberately NOT here

1. **`infra/deploy-agents.ps1`:** the three defaults become the live window, with one comment line.
2. **`surfaces/dashboard/settings.py`:** `window_end_utc` defaults to `23:30`; a new tunable
   `window_days_utc` defaults to `1-5`.
3. **`surfaces/dashboard/time_windows.py`:** `latest_window` and `next_master_wake` skip a day the
   window does not open on; two private helpers read the weekday field.
4. **Tests**, per the Test plan: one new file, and one existing test whose pinned literal changes.
5. **The law cycle** as answered above.

Replace the production text with **exactly** what the Appendix gives.

### Out of scope (do NOT build this sprint)

- **No other function of `time_windows.py` changes**: `run_window`, `next_fire`,
  `scheduled_execution`, `window_label` and `_time` stay byte for byte.
- **`surfaces/queries/fleet_check.py` does not change**, comment included.
- **The dispatcher, `orchestration/`, `contracts/` and every agent do not change.** The answer
  deadline of a held run (23:20 UTC) is ten minutes before the new end; that is work-queue 131 (b).
- **The tests' shared `_settings()` does not change**: it keeps `00:30`, and the existing tests
  keep proving a window that crosses midnight.
- **No deploy, no `az` call, no run of the script.** You have no network.
- **Winding the fleet down when a run completes** is work-queue 131 (a), not this.

### The road not taken (LAW-06)

- **Leave the defaults and pass the parameters at every `up`.** Rejected: the value then lives in
  the operator's memory and a document; the first `up` that forgets it reverts the fleet silently.
- **Hard-code Monday to Friday in the dashboard.** Rejected: the dashboard's window is a copy of
  the script's, pinned by a test; a second weekday rule not read from the same place drifts.
- **Have the dashboard read the live rules from Azure.** Rejected: right in the end, but a new
  read path and its failure modes for a one-field change.
- **Move the fleet's weekday rule into the pack's tunables.** Rejected: the scale windows are the
  deploy script's parameters today; moving them is its own sprint.

---

## The design decisions — made, and recorded in DL-295

They are recorded with their rejected alternatives. **Do not add a design-log entry.**

1. The script's defaults are the live window, so a full `up` with no window parameter keeps it.
2. The dashboard gains one setting, `window_days_utc`, a cron weekday field, default `1-5`.
3. One weekday field serves the three windows; a test fails when the script's three differ or
   differ from the dashboard's.
4. The field is read as cron reads it: `*`, a number, a range, a list; 0 and 7 are both Sunday.
   A field that cannot be read is an error, never "every day".
5. The weekday belongs to the day a window starts on. The window no longer crosses midnight, and
   a setting that makes it cross still works: the day counted is the start's.

---

## Blast radius — measured 2026-10-11

| What | Detail |
| --- | --- |
| Files changed | `infra/deploy-agents.ps1`; `surfaces/dashboard/settings.py` (174 → 178); `surfaces/dashboard/time_windows.py` (121 → 152); one new test file; `tests/test_deploy_script_invariants.py` (192 → 194); surfaces `laws.md`; `docs/laws/INDEX.md`, `ledger.md` |
| Agents affected | none; surfaces only |
| Contract change? | No |
| Graph vocabulary change? | No |
| New env keys / tunables | `DASHBOARD_WINDOW_DAYS_UTC` (optional; default `1-5`) |
| Deploy implication | The dashboard runs from the main checkout and shows the new window on its next start. The script's defaults matter at the next full `up`; a retag does not touch scale rules |
| Rollback | Revert the commit. The live window does not move either way; `az` set it, and the rules it had before are saved outside the repo |

---

## Steps, in order

1. **Read the laws** and write the Law reading record.
2. **Plant the failing tests first** (Test plan) and watch them fail on the unchanged code. Paste the red output.
3. **Apply the Appendix** to the three production files, exactly.
4. **Law cycle** as answered above, every item.
5. **Prove the guards can fail (DL-70):** at least the breaks listed under Traps, one at a time, each red, each restored.
6. **`make ci` green**, every step of the `ci:` target (sixteen; count them from the `Makefile`), **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

New file `surfaces/tests/test_dashboard_window_days.py`. Build settings with the existing helper
`surfaces.tests.test_dashboard_costs._settings()` and `model_copy(update=...)`; the week used
below is the one of Monday 2026-09-21, whose 26th is a Saturday. All times UTC.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| W1 | 🎯 the next wake is the next weekday's start | parametrised `now`: Fri 00:45, Fri 12:00, Sat 00:45, Sat 12:00, Sat 21:00, Sun 21:00, Mon 12:00 | `next_master_wake` returns Fri 20:25 for the first two and Mon 2026-09-28 20:25 for the other five |
| W2 | the master is awake only inside a weekday window | Fri 21:00; Sat 00:10 (inside Friday's window, which the helper's settings end at 00:30); Sat 21:00 | `None`, `None`, and not `None` |
| W3 | 🪤 the latest window is the latest weekday one | Fri 21:00, Sat 12:00, Sun 23:00, Mon 10:00, Mon 21:00 | `latest_window(...)[0]` is on Fri 25th for the first four and Mon 28th for the last |
| W4 | a `*` opens the window every day | `window_days_utc="*"` | next wake from Sat 12:00 is Sat 20:25; latest window at Sun 23:00 starts Sun 27th |
| W5 | the field is read as cron reads it | from Sat 12:00: `6` → Sat 26th; `0` → Sun 27th; `7` → Sun 27th; `1,3` → Mon 28th; `2-4,6` → Sat 26th; `3` → Wed 30th | the next wake's date, each at 20:25 |
| W6 | a field that cannot be read is an error | `""`, `8`, `5-1`, `mon`, `1-9`, `1,`, `-1`, `1-` | `ValueError` matching `expected cron days 0-7`, from `next_master_wake` and from `latest_window` |
| W7 | the defaults are the deployed windows | the script's three parameters read with the regex `test_dashboard_schedule.py` uses; `DashboardSettings(_env_file=None)` | the three weekday fields are one value, equal to the default `window_days_utc`, equal to `1-5`; `window_end_utc` is `23:30`; `run_window("2026-09-25", defaults)` is 20:25 to 23:30 on the same day |

Existing test to edit: **one.**
`tests/test_deploy_script_invariants.py::test_master_scale_window_starts_before_the_two_pre_dispatch_retries`
asserts the three new literals in place of the one old one:

```python
    assert "[string]$MasterScaleStart = '25 20 * * 1-5'" in text
    assert "[string]$AgentScaleStart = '30 22 * * 1-5'" in text
    assert "[string]$ScaleEnd = '30 23 * * 1-5'" in text
```

If any other existing test fails, stop and report.

---

## Success factors

- [x] Every row of the Test plan is a passing test.
- [x] `git hash-object` prints, on LF bytes, `cde71d801d1ca08d168fcccc63c5ebf102e7dd8c` for `infra/deploy-agents.ps1`, `32883a5789410d44bd8baf265a4dfc9c5ee18d86` for `surfaces/dashboard/settings.py` and `f26cca6c76a853c53e2981c397d71fc4805fe637` for `surfaces/dashboard/time_windows.py`, or each difference is explained.
- [ ] One existing test changed and no other (`git diff --stat main -- '*test_*.py'` shows the new file and the invariants file).
- [x] Law cycle done, every item: the two `PARAM` rows as given, v1.7, Changelog, the surfaces' row in `INDEX.md` and in `ledger.md`; `check_param_law_sync.py` exits 0.
- [x] Every guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module under 200 lines.
- [x] `make ci` exit 0, sixteen steps, 100.00 % coverage.

---

## Traps

🪤 **Cron counts Sunday as 0 and also as 7; Python's `weekday()` counts Monday as 0.** The helper
uses `isoweekday() % 7`.
🪤 **A window open at 00:10 on Saturday started on Friday.** `latest_window` decides the day
first and only then looks at its weekday. W2 plants it.
🪤 **A field that yields no day would loop forever** in `next_master_wake`. The reader raises
before a loop can start: every accepted part adds at least one day.
🪤 **`"1-"` is not day 1.** `partition` returns an empty end; W6 plants it.
🪤 **`tests/test_deploy_script_invariants.py` is at 192 lines** and the block is 200. Add two
lines, no more.
🪤 **`_settings()` in the tests ends the window at 00:30**; `DashboardSettings(_env_file=None)`
gives the real defaults. W7 needs the second.
🪤 **The script is PowerShell: the gate cannot read it.** The invariants test and W7 read its
text; do not run it.

Breaks to plant, at the least: the latest window ignores the weekday; the next wake ignores it;
Monday counted as day 0; a 7 not read as Sunday; a `*` not read; a day above 7 accepted; a
backward range accepted; a range with no end accepted; the latest window stepping forward; the
dashboard's end still `00:30`; the dashboard's days `*`; the script's end `30 00 * * *`; the
script's agents daily; the script's master daily; the script's end on other days than its starts.

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
2. The planner re-measures: the three blobs against the Appendix, the planner's own test file and
   break script run on the built tree, the open CodeQL alerts set-diffed against the last merged
   branch's.
3. **F1**, at no cost and read-only: on the merged `main`, the script's three defaults compared
   with the 16 live rules (`az containerapp show`); the dashboard's verdict for a Saturday, a
   Sunday and a Monday morning names Monday 20:25 UTC as the next check.
4. **Deploy** (the operator, 2026-10-11: *"and yeah deploy"*): an image retag of `main`. A retag
   does not touch scale rules; the live window is checked again after it.

---

## Handover — paste this to Codex

```text
You are building Sprint 270 in the worktree ../ta-s270, on the branch
sprint-270-the-deploy-defaults-are-the-live-wake-window. Never work on main.

Read docs/sprints/sprint-270-the-deploy-defaults-are-the-live-wake-window.md, whole, before
anything else. It is the spec, and its bottom sections are your handback.

In order:
1. Read surfaces/laws/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any code.
2. Write the tests of the Test plan in surfaces/tests/test_dashboard_window_days.py and change
   the one assertion in tests/test_deploy_script_invariants.py. Run them on the unchanged code
   and paste the red output into the Closeout.
3. Apply the Appendix to infra/deploy-agents.ps1, surfaces/dashboard/settings.py and
   surfaces/dashboard/time_windows.py, exactly. Change nothing else in production code.
4. Do the law cycle the spec answers, every item: the two PARAM rows as given, laws.md to v1.7
   with a Changelog entry, the surfaces' row in docs/laws/INDEX.md and docs/laws/ledger.md
   (v1.7; the gate does not check it).
5. Plant the breaks listed under Traps one at a time; each must go red; restore.
6. Bump the version (PATCH) and stage uv.lock. Run make ci redirected to a file and read the file.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md.

DO NOT: run infra/deploy-agents.ps1 or any az command; change any other function of
time_windows.py, surfaces/queries/fleet_check.py, the tests' shared _settings(), orchestration/,
contracts/ or any agent; change any existing test but the one named; add a design-log entry; add
or reword a law clause; use noqa; let any module reach 200 lines; measure make ci through a pipe.

Traps: cron's Sunday is 0 and 7 while Python's weekday() starts at Monday; a window open just
after midnight started the day before; "1-" is not day 1; _settings() in the tests ends the
window at 00:30 and DashboardSettings(_env_file=None) gives the real defaults;
tests/test_deploy_script_invariants.py may grow by two lines only.

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
| Dashboard settings and window helpers | `surfaces/laws/laws.md` and `surfaces/laws/test-plan.md`, whole, before code (2026-10-11) | `PARAM` must follow settings; `SRF-DEP-01/02` and `SRF-NEV-01/02/03` preserve dependency, confirmation and product-language boundaries. No clause governs the wake window. | No: apply the Appendix exactly; window tests cite no unrelated clause and move no gray row. |
| Deploy defaults | Same surfaces books; `docs/deployment.md` | `SRF-DEP` and `SRF-NEV` reviewed as boundaries; no clause specifies the scale-window calendar. | No: read and parse the script only; do not execute it or call Azure. |
| PARAM amendment and law rollups | `docs/laws/INDEX.md`, `docs/laws/conventions.md`, `docs/laws/drift-register.md` | Conventions sections 2-4, 7-7a and 9; locked clause IDs/text and proof counts stay unchanged. | No: the spec authorizes PARAM only, v1.7 and its Changelog plus both rollup labels; the law test-plan stays read-only. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**

No. No contract file or clause changes. The cycle is the two specified PARAM rows, v1.7,
its Changelog entry and the surfaces row in both law rollups; counts remain 31 / 38.

**Contradictions found between a law and this spec:**

None in the governing surfaces clauses. The spec explicitly settles the PARAM-only cycle.

**Laws found silent where a decision was needed:**

The wake-window weekdays, cron parsing and start-day attribution have no surfaces clause.
DL-295 already settles those decisions; no new design-log entry or clause is owed by this build.

**Clauses that were ⬜ and are now proven:**

None; no clause-level proof status changes in this sprint.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| W1 | `test_next_wake_is_the_next_weekdays_start` | `surfaces/tests/test_dashboard_window_days.py` | PASS (7 cases) | None: no clause governs the wake window. |
| W2 | `test_master_is_awake_only_inside_a_weekday_window` | `surfaces/tests/test_dashboard_window_days.py` | PASS (1 case, all three times) | None: no clause governs the wake window. |
| W3 | `test_latest_window_is_the_latest_weekday_one` | `surfaces/tests/test_dashboard_window_days.py` | PASS (5 cases) | None: no clause governs the wake window. |
| W4 | `test_star_opens_the_window_every_day` | `surfaces/tests/test_dashboard_window_days.py` | PASS (1 case) | None: no clause governs the wake window. |
| W5 | `test_weekday_field_is_read_as_cron_reads_it` | `surfaces/tests/test_dashboard_window_days.py` | PASS (6 cases) | None: no clause governs the wake window. |
| W6 | `test_unreadable_weekday_field_is_an_error` | `surfaces/tests/test_dashboard_window_days.py` | PASS (8 cases, both entry points) | None: no clause governs the wake window. |
| W7 | `test_defaults_are_the_deployed_windows` | `surfaces/tests/test_dashboard_window_days.py` | PASS (1 case, real defaults) | None: no clause governs the wake window. |
| Existing | `test_master_scale_window_starts_before_the_two_pre_dispatch_retries` | `tests/test_deploy_script_invariants.py` | PASS; only the specified assertion block changed, net +2 lines. | No new clause citation. |

**Tests added beyond the plan:**

None. W1-W7 are 29 new collected cases; the existing invariants file still collects 12 cases.

---

## Closeout — evidence

**Status:** MERGED

**Tree the proofs ran in (and `.env` present?):**

`C:\Users\yury_\Downloads\project\ta-s270`, branch `sprint-270-the-deploy-defaults-are-the-live-wake-window`, based on `d80cb1c8ec1d3705205c030f580dc450fa41aaa2`. `.env` absent. No deploy script execution or Azure command.

**Result:**

BUILT. All seven test-plan rows pass. The three production blobs exactly match the Appendix. The PARAM-only law cycle is complete at v1.7, with 31 / 38 unchanged. All fifteen required breaks went red and were restored. `make ci` exited 0, all sixteen commands ran, and the full suite passed at 100.00% coverage. Version is 0.125.08; `uv lock` succeeded and its lockfile is staged. No source change followed this CI run.

**Files changed:**

- `infra/deploy-agents.ps1`
- `surfaces/dashboard/settings.py`
- `surfaces/dashboard/time_windows.py`
- `surfaces/tests/test_dashboard_window_days.py`
- `tests/test_deploy_script_invariants.py`
- `surfaces/laws/laws.md`
- `docs/laws/INDEX.md`
- `docs/laws/ledger.md`
- `docs/sprints/sprint-270-the-deploy-defaults-are-the-live-wake-window.md`
- `docs/sprints/README.md`
- `pyproject.toml`
- `uv.lock`

**Design decisions:** recorded as [DL-295](../design-log.md); none added by the build.

**Proof — the red run first:**

Production diff was empty before this run. Command: `uv run pytest surfaces/tests/test_dashboard_window_days.py tests/test_deploy_script_invariants.py --no-cov`; exit 1. Trailing spaces on pytest's empty diff rows are omitted.

```text
============================= test session starts =============================
collected 41 items

surfaces\tests\test_dashboard_window_days.py ..FFFF.F..FF...FFF.FFFFFFFF [ 65%]
FF                                                                       [ 70%]
tests\test_deploy_script_invariants.py ...........F                      [100%]

================================== FAILURES ===================================
_ test_next_wake_is_the_next_weekdays_start[2026-09-26T00:45:00+00:00-2026-09-28] _
surfaces\tests\test_dashboard_window_days.py:36: in test_next_wake_is_the_next_weekdays_start
    assert next_master_wake(settings, datetime.fromisoformat(now)) == (
E   AssertionError: assert '2026-09-26T20:25:00+00:00' == '2026-09-28T20:25:00+00:00'
E
E     - 2026-09-28T20:25:00+00:00
E     ?          ^
E     + 2026-09-26T20:25:00+00:00
E     ?          ^
_ test_next_wake_is_the_next_weekdays_start[2026-09-26T12:00:00+00:00-2026-09-28] _
surfaces\tests\test_dashboard_window_days.py:36: in test_next_wake_is_the_next_weekdays_start
    assert next_master_wake(settings, datetime.fromisoformat(now)) == (
E   AssertionError: assert '2026-09-26T20:25:00+00:00' == '2026-09-28T20:25:00+00:00'
E
E     - 2026-09-28T20:25:00+00:00
E     ?          ^
E     + 2026-09-26T20:25:00+00:00
E     ?          ^
_ test_next_wake_is_the_next_weekdays_start[2026-09-26T21:00:00+00:00-2026-09-28] _
surfaces\tests\test_dashboard_window_days.py:36: in test_next_wake_is_the_next_weekdays_start
    assert next_master_wake(settings, datetime.fromisoformat(now)) == (
E   AssertionError: assert None == '2026-09-28T20:25:00+00:00'
E    +  where None = next_master_wake(DashboardSettings(dispatcher_fire_utc='22:30', scorecard_window_days=30, scorecard_g1_target=0.95, scorecard_g3_target... operator_timezone='Australia/Melbourne', readiness_failure_max_age_minutes=1440, performance_behind_threshold_pts=1.0), datetime.datetime(2026, 9, 26, 21, 0, tzinfo=datetime.timezone.utc))
E    +    where datetime.datetime(2026, 9, 26, 21, 0, tzinfo=datetime.timezone.utc) = <built-in method fromisoformat of type object at 0x00007FFDF1CD5760>('2026-09-26T21:00:00+00:00')
E    +      where <built-in method fromisoformat of type object at 0x00007FFDF1CD5760> = datetime.fromisoformat
_ test_next_wake_is_the_next_weekdays_start[2026-09-27T21:00:00+00:00-2026-09-28] _
surfaces\tests\test_dashboard_window_days.py:36: in test_next_wake_is_the_next_weekdays_start
    assert next_master_wake(settings, datetime.fromisoformat(now)) == (
E   AssertionError: assert None == '2026-09-28T20:25:00+00:00'
E    +  where None = next_master_wake(DashboardSettings(dispatcher_fire_utc='22:30', scorecard_window_days=30, scorecard_g1_target=0.95, scorecard_g3_target... operator_timezone='Australia/Melbourne', readiness_failure_max_age_minutes=1440, performance_behind_threshold_pts=1.0), datetime.datetime(2026, 9, 27, 21, 0, tzinfo=datetime.timezone.utc))
E    +    where datetime.datetime(2026, 9, 27, 21, 0, tzinfo=datetime.timezone.utc) = <built-in method fromisoformat of type object at 0x00007FFDF1CD5760>('2026-09-27T21:00:00+00:00')
E    +      where <built-in method fromisoformat of type object at 0x00007FFDF1CD5760> = datetime.fromisoformat
______________ test_master_is_awake_only_inside_a_weekday_window ______________
surfaces\tests\test_dashboard_window_days.py:46: in test_master_is_awake_only_inside_a_weekday_window
    assert next_master_wake(settings, datetime(2026, 9, 26, 21, tzinfo=UTC)) is not None
E   AssertionError: assert None is not None
E    +  where None = next_master_wake(DashboardSettings(dispatcher_fire_utc='22:30', scorecard_window_days=30, scorecard_g1_target=0.95, scorecard_g3_target... operator_timezone='Australia/Melbourne', readiness_failure_max_age_minutes=1440, performance_behind_threshold_pts=1.0), datetime.datetime(2026, 9, 26, 21, 0, tzinfo=datetime.timezone.utc))
E    +    where datetime.datetime(2026, 9, 26, 21, 0, tzinfo=datetime.timezone.utc) = datetime(2026, 9, 26, 21, tzinfo=datetime.timezone.utc)
_ test_latest_window_is_the_latest_weekday_one[2026-09-27T23:00:00+00:00-2026-09-25] _
surfaces\tests\test_dashboard_window_days.py:63: in test_latest_window_is_the_latest_weekday_one
    assert start == datetime.fromisoformat(f"{expected_day}T20:25:00+00:00")
E   AssertionError: assert datetime.datetime(2026, 9, 27, 20, 25, tzinfo=datetime.timezone.utc) == datetime.datetime(2026, 9, 25, 20, 25, tzinfo=datetime.timezone.utc)
E    +  where datetime.datetime(2026, 9, 25, 20, 25, tzinfo=datetime.timezone.utc) = <built-in method fromisoformat of type object at 0x00007FFDF1CD5760>('2026-09-25T20:25:00+00:00')
E    +    where <built-in method fromisoformat of type object at 0x00007FFDF1CD5760> = datetime.fromisoformat
_ test_latest_window_is_the_latest_weekday_one[2026-09-28T10:00:00+00:00-2026-09-25] _
surfaces\tests\test_dashboard_window_days.py:63: in test_latest_window_is_the_latest_weekday_one
    assert start == datetime.fromisoformat(f"{expected_day}T20:25:00+00:00")
E   AssertionError: assert datetime.datetime(2026, 9, 27, 20, 25, tzinfo=datetime.timezone.utc) == datetime.datetime(2026, 9, 25, 20, 25, tzinfo=datetime.timezone.utc)
E    +  where datetime.datetime(2026, 9, 25, 20, 25, tzinfo=datetime.timezone.utc) = <built-in method fromisoformat of type object at 0x00007FFDF1CD5760>('2026-09-25T20:25:00+00:00')
E    +    where <built-in method fromisoformat of type object at 0x00007FFDF1CD5760> = datetime.fromisoformat
__________ test_weekday_field_is_read_as_cron_reads_it[0-2026-09-27] __________
surfaces\tests\test_dashboard_window_days.py:90: in test_weekday_field_is_read_as_cron_reads_it
    assert next_master_wake(settings, datetime(2026, 9, 26, 12, tzinfo=UTC)) == (
E   AssertionError: assert '2026-09-26T20:25:00+00:00' == '2026-09-27T20:25:00+00:00'
E
E     - 2026-09-27T20:25:00+00:00
E     ?          ^
E     + 2026-09-26T20:25:00+00:00
E     ?          ^
__________ test_weekday_field_is_read_as_cron_reads_it[7-2026-09-27] __________
surfaces\tests\test_dashboard_window_days.py:90: in test_weekday_field_is_read_as_cron_reads_it
    assert next_master_wake(settings, datetime(2026, 9, 26, 12, tzinfo=UTC)) == (
E   AssertionError: assert '2026-09-26T20:25:00+00:00' == '2026-09-27T20:25:00+00:00'
E
E     - 2026-09-27T20:25:00+00:00
E     ?          ^
E     + 2026-09-26T20:25:00+00:00
E     ?          ^
_________ test_weekday_field_is_read_as_cron_reads_it[1,3-2026-09-28] _________
surfaces\tests\test_dashboard_window_days.py:90: in test_weekday_field_is_read_as_cron_reads_it
    assert next_master_wake(settings, datetime(2026, 9, 26, 12, tzinfo=UTC)) == (
E   AssertionError: assert '2026-09-26T20:25:00+00:00' == '2026-09-28T20:25:00+00:00'
E
E     - 2026-09-28T20:25:00+00:00
E     ?          ^
E     + 2026-09-26T20:25:00+00:00
E     ?          ^
__________ test_weekday_field_is_read_as_cron_reads_it[3-2026-09-30] __________
surfaces\tests\test_dashboard_window_days.py:90: in test_weekday_field_is_read_as_cron_reads_it
    assert next_master_wake(settings, datetime(2026, 9, 26, 12, tzinfo=UTC)) == (
E   AssertionError: assert '2026-09-26T20:25:00+00:00' == '2026-09-30T20:25:00+00:00'
E
E     - 2026-09-30T20:25:00+00:00
E     ?         ^^
E     + 2026-09-26T20:25:00+00:00
E     ?         ^^
_________________ test_unreadable_weekday_field_is_an_error[] _________________
surfaces\tests\test_dashboard_window_days.py:100: in test_unreadable_weekday_field_is_an_error
    with pytest.raises(ValueError, match="expected cron days 0-7"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
________________ test_unreadable_weekday_field_is_an_error[8] _________________
surfaces\tests\test_dashboard_window_days.py:100: in test_unreadable_weekday_field_is_an_error
    with pytest.raises(ValueError, match="expected cron days 0-7"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
_______________ test_unreadable_weekday_field_is_an_error[5-1] ________________
surfaces\tests\test_dashboard_window_days.py:100: in test_unreadable_weekday_field_is_an_error
    with pytest.raises(ValueError, match="expected cron days 0-7"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
_______________ test_unreadable_weekday_field_is_an_error[mon] ________________
surfaces\tests\test_dashboard_window_days.py:100: in test_unreadable_weekday_field_is_an_error
    with pytest.raises(ValueError, match="expected cron days 0-7"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
_______________ test_unreadable_weekday_field_is_an_error[1-9] ________________
surfaces\tests\test_dashboard_window_days.py:100: in test_unreadable_weekday_field_is_an_error
    with pytest.raises(ValueError, match="expected cron days 0-7"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
________________ test_unreadable_weekday_field_is_an_error[1,] ________________
surfaces\tests\test_dashboard_window_days.py:100: in test_unreadable_weekday_field_is_an_error
    with pytest.raises(ValueError, match="expected cron days 0-7"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
________________ test_unreadable_weekday_field_is_an_error[-1] ________________
surfaces\tests\test_dashboard_window_days.py:100: in test_unreadable_weekday_field_is_an_error
    with pytest.raises(ValueError, match="expected cron days 0-7"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
________________ test_unreadable_weekday_field_is_an_error[1-] ________________
surfaces\tests\test_dashboard_window_days.py:100: in test_unreadable_weekday_field_is_an_error
    with pytest.raises(ValueError, match="expected cron days 0-7"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
___________________ test_defaults_are_the_deployed_windows ____________________
surfaces\tests\test_dashboard_window_days.py:117: in test_defaults_are_the_deployed_windows
    assert weekdays == {defaults.window_days_utc} == {"1-5"}
                        ^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\pydantic\main.py:1042: in __getattr__
    raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E   AttributeError: 'DashboardSettings' object has no attribute 'window_days_utc'. Did you mean: 'window_end_utc'?
_____ test_master_scale_window_starts_before_the_two_pre_dispatch_retries _____
tests\test_deploy_script_invariants.py:191: in test_master_scale_window_starts_before_the_two_pre_dispatch_retries
    assert "[string]$MasterScaleStart = '25 20 * * 1-5'" in text
E   assert "[string]$MasterScaleStart = '25 20 * * 1-5'" in "# deploy-agents.ps1 — One-command fleet deploy/teardown for Azure Container Apps.\n#\n#   pwsh infra/deploy-agents.ps...' { Up }\n  'postgres-flip' { Flip-PostgresRoles }\n  'servicebus-flip' { Flip-ServiceBusSas }\n  'down' { Down }\n}\n"
=========================== short test summary info ===========================
FAILED surfaces/tests/test_dashboard_window_days.py::test_next_wake_is_the_next_weekdays_start[2026-09-26T00:45:00+00:00-2026-09-28]
FAILED surfaces/tests/test_dashboard_window_days.py::test_next_wake_is_the_next_weekdays_start[2026-09-26T12:00:00+00:00-2026-09-28]
FAILED surfaces/tests/test_dashboard_window_days.py::test_next_wake_is_the_next_weekdays_start[2026-09-26T21:00:00+00:00-2026-09-28]
FAILED surfaces/tests/test_dashboard_window_days.py::test_next_wake_is_the_next_weekdays_start[2026-09-27T21:00:00+00:00-2026-09-28]
FAILED surfaces/tests/test_dashboard_window_days.py::test_master_is_awake_only_inside_a_weekday_window
FAILED surfaces/tests/test_dashboard_window_days.py::test_latest_window_is_the_latest_weekday_one[2026-09-27T23:00:00+00:00-2026-09-25]
FAILED surfaces/tests/test_dashboard_window_days.py::test_latest_window_is_the_latest_weekday_one[2026-09-28T10:00:00+00:00-2026-09-25]
FAILED surfaces/tests/test_dashboard_window_days.py::test_weekday_field_is_read_as_cron_reads_it[0-2026-09-27]
FAILED surfaces/tests/test_dashboard_window_days.py::test_weekday_field_is_read_as_cron_reads_it[7-2026-09-27]
FAILED surfaces/tests/test_dashboard_window_days.py::test_weekday_field_is_read_as_cron_reads_it[1,3-2026-09-28]
FAILED surfaces/tests/test_dashboard_window_days.py::test_weekday_field_is_read_as_cron_reads_it[3-2026-09-30]
FAILED surfaces/tests/test_dashboard_window_days.py::test_unreadable_weekday_field_is_an_error[]
FAILED surfaces/tests/test_dashboard_window_days.py::test_unreadable_weekday_field_is_an_error[8]
FAILED surfaces/tests/test_dashboard_window_days.py::test_unreadable_weekday_field_is_an_error[5-1]
FAILED surfaces/tests/test_dashboard_window_days.py::test_unreadable_weekday_field_is_an_error[mon]
FAILED surfaces/tests/test_dashboard_window_days.py::test_unreadable_weekday_field_is_an_error[1-9]
FAILED surfaces/tests/test_dashboard_window_days.py::test_unreadable_weekday_field_is_an_error[1,]
FAILED surfaces/tests/test_dashboard_window_days.py::test_unreadable_weekday_field_is_an_error[-1]
FAILED surfaces/tests/test_dashboard_window_days.py::test_unreadable_weekday_field_is_an_error[1-]
FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
FAILED tests/test_deploy_script_invariants.py::test_master_scale_window_starts_before_the_two_pre_dispatch_retries
======================== 21 failed, 20 passed in 4.06s ========================
```

**Proof — the green run:**

`uv run pytest surfaces/tests/test_dashboard_window_days.py tests/test_deploy_script_invariants.py --no-cov`; exit 0.

```text
============================= test session starts =============================
collected 41 items

surfaces\tests\test_dashboard_window_days.py ........................... [ 65%]
..                                                                       [ 70%]
tests\test_deploy_script_invariants.py ............                      [100%]

============================= 41 passed in 3.58s ==============================
```

Same focused run after all guards were restored; exit 0:

```text
============================= test session starts =============================
collected 41 items

surfaces\tests\test_dashboard_window_days.py ........................... [ 65%]
..                                                                       [ 70%]
tests\test_deploy_script_invariants.py ............                      [100%]

============================= 41 passed in 2.98s ==============================
```

`git hash-object infra/deploy-agents.ps1 surfaces/dashboard/settings.py surfaces/dashboard/time_windows.py` on LF files, in that order:

```text
cde71d801d1ca08d168fcccc63c5ebf102e7dd8c
32883a5789410d44bd8baf265a4dfc9c5ee18d86
f26cca6c76a853c53e2981c397d71fc4805fe637
POWERSHELL_PARSE_ERRORS=0
PARAM_EXIT=0
LAW_EXIT=0
```

The two specified PARAM rows, v1.7 and its Changelog are present; both surfaces rollup labels read v1.7. The law coverage and PARAM gates each exited 0. The law test-plan and every clause remain unchanged.

Version resolution and staging:

```text
UV_LOCK_EXIT=0
Resolved 180 packages in 2.72s
Updated trading-agents v0.125.7 -> v0.125.8
LOCK_STAGE_EXIT=0
```

`uv.lock` changed only the local project package version, normalized from `0.125.7` to `0.125.8`; no dependency changed.

Scope check output (source-segment comparison against the pre-build HEAD; protected files compared as bytes):

```text
UNCHANGED FUNCTION: run_window
UNCHANGED FUNCTION: next_fire
UNCHANGED FUNCTION: scheduled_execution
UNCHANGED FUNCTION: window_label
UNCHANGED FUNCTION: _time
UNCHANGED: every surfaces clause and CAP declaration
UNCHANGED FILE: surfaces/laws/test-plan.md
UNCHANGED FILE: surfaces/queries/fleet_check.py
UNCHANGED FILE: surfaces/tests/test_dashboard_costs.py
UNCHANGED FILE: docs/STATE.md
UNCHANGED FILE: docs/design-log.md
SCOPE PASS; .env absent
```

`git diff --stat main -- '*test_*.py'` after the new file was staged:

```text
 surfaces/tests/test_dashboard_window_days.py | 122 +++++++++++++++++++++++++++
 tests/test_deploy_script_invariants.py       |   4 +-
 2 files changed, 125 insertions(+), 1 deletion(-)
```

**Guards planted:**

Each break was planted alone in one production file, the same 41 focused cases ran, exit 1 and a named failing assertion were required, and a `finally` restored the original bytes before the next break. G04 deliberately misread 7 as Saturday; G07 normalized a backward range so acceptance was falsified without an empty-set loop. The helper and per-guard logs are outside the repo in `%TEMP%/ta-s270-*`. Raw per-guard evidence follows:

```text
G01 latest window ignores weekdays: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_next_wake_is_the_next_weekdays_start[2026-09-26T21:00:00+00:00-2026-09-28]
======================== 5 failed, 36 passed in 3.65s =========================
RESTORED f26cca6c76a853c53e2981c397d71fc4805fe637

G02 next wake ignores weekdays: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_next_wake_is_the_next_weekdays_start[2026-09-26T00:45:00+00:00-2026-09-28]
======================== 7 failed, 34 passed in 4.11s =========================
RESTORED f26cca6c76a853c53e2981c397d71fc4805fe637

G03 Monday counted as day 0: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_next_wake_is_the_next_weekdays_start[2026-09-26T00:45:00+00:00-2026-09-28]
======================== 15 failed, 26 passed in 3.56s ========================
RESTORED f26cca6c76a853c53e2981c397d71fc4805fe637

G04 7 treated as Saturday: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_weekday_field_is_read_as_cron_reads_it[7-2026-09-27]
======================== 1 failed, 40 passed in 3.39s =========================
RESTORED f26cca6c76a853c53e2981c397d71fc4805fe637

G05 star not read: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_star_opens_the_window_every_day
======================== 1 failed, 40 passed in 3.43s =========================
RESTORED f26cca6c76a853c53e2981c397d71fc4805fe637

G06 day above 7 accepted: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_unreadable_weekday_field_is_an_error[8]
======================== 2 failed, 39 passed in 3.61s =========================
RESTORED f26cca6c76a853c53e2981c397d71fc4805fe637

G07 backward range accepted: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_unreadable_weekday_field_is_an_error[5-1]
======================== 1 failed, 40 passed in 3.36s =========================
RESTORED f26cca6c76a853c53e2981c397d71fc4805fe637

G08 range with no end accepted: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_unreadable_weekday_field_is_an_error[1-]
======================== 1 failed, 40 passed in 3.33s =========================
RESTORED f26cca6c76a853c53e2981c397d71fc4805fe637

G09 latest window steps forward: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_latest_window_is_the_latest_weekday_one[2026-09-27T23:00:00+00:00-2026-09-25]
======================== 2 failed, 39 passed in 3.54s =========================
RESTORED f26cca6c76a853c53e2981c397d71fc4805fe637

G10 dashboard end still 00:30: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
======================== 1 failed, 40 passed in 4.50s =========================
RESTORED 32883a5789410d44bd8baf265a4dfc9c5ee18d86

G11 dashboard days daily: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
======================== 1 failed, 40 passed in 3.39s =========================
RESTORED 32883a5789410d44bd8baf265a4dfc9c5ee18d86

G12 script end old daily midnight: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
======================== 2 failed, 39 passed in 4.12s =========================
RESTORED cde71d801d1ca08d168fcccc63c5ebf102e7dd8c

G13 script agents daily: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
======================== 2 failed, 39 passed in 2.74s =========================
RESTORED cde71d801d1ca08d168fcccc63c5ebf102e7dd8c

G14 script master daily: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
======================== 2 failed, 39 passed in 3.82s =========================
RESTORED cde71d801d1ca08d168fcccc63c5ebf102e7dd8c

G15 script end on different days: exit 1
FAILED surfaces/tests/test_dashboard_window_days.py::test_defaults_are_the_deployed_windows
======================== 2 failed, 39 passed in 3.70s =========================
RESTORED cde71d801d1ca08d168fcccc63c5ebf102e7dd8c

FINAL RESTORED RUN: exit 0
============================= test session starts =============================
collected 41 items

surfaces\tests\test_dashboard_window_days.py ........................... [ 65%]
..                                                                       [ 70%]
tests\test_deploy_script_invariants.py ............                      [100%]

============================= 41 passed in 2.98s ==============================
```

**Module line counts:**

Measured before CI; the module-size gate also passed.

```text
surfaces/dashboard/settings.py: 178 lines
surfaces/dashboard/time_windows.py: 152 lines
surfaces/tests/test_dashboard_window_days.py: 122 lines
tests/test_deploy_script_invariants.py: 194 lines
```

**`make ci`:**

Command: `make ci > "$env:TEMP\ta-s270-ci.txt" 2>&1`; `$LASTEXITCODE` was 0. The complete redirected file was read (2,168 lines). The `ci:` target was counted from the Makefile: sixteen commands. Raw excerpts below retain every command line, aggregate results, all skips and the security tail; unchanged module warnings, individual test progress and coverage rows are omitted. This run preceded handback status updates; the document gates are rechecked below.

```text
MAKE_CI_EXIT=0
uv run ruff check . --output-format=github
uv run ruff format --check .
1676 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 1197 source files
uv run lint-imports
Contracts: 5 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
docs_seen=275 SPEC=11 BUILT=0 MERGED=264 UNMAPPED=0 MISSING=0
uv run python scripts/check_tracker_size.py
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
TOTAL                                                           20288      0   4306      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 4777 passed, 8 skipped, 2470 warnings in 809.46s (0:13:29) ==========
uv run python scripts/check_dependency_audit.py
accepted: PYSEC-2026-2447 (diskcache 5.6.3) - reachable only via the 'optimizer' extra, installed by 1 of 15 Dockerfiles; each installing command excludes diskcache by name; the dev group carries it too, and every sync passes --no-dev or excludes it by name; no fix release exists; every deployed optimizer installation excludes diskcache by name (S254, DL-266, ADR-0032) [DL-184] - retire when diskcache publishes a fixed release, or the optimizer extra is dropped
No unaccepted vulnerabilities; 1 accepted advisory re-checked
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
```

**`make gate-ran`:** not the builder's: the planner runs it for the exact commit that merges.

**Not met / verified failing:**

Verified failing: the final current-main comparison now shows a third path, `scripts/gate_selftest_parity_invariants.py`, because `main` advanced to `ff10da34213527888dc36ab67057051e9d0d9067` while this branch remained based on `d80cb1c8ec1d3705205c030f580dc450fa41aaa2`. That path was added by main's separate DL-293/work-queue 129 chore; the builder did not edit or remove it. The pinned-base comparison proves exactly the two planned test paths, and the builder delta contains exactly the twelve scoped files. Integration of the newer main is not done; the planner must integrate it and re-prove the resulting exact SHA before merge. No existing test failed. Eight existing tests were skipped for the prerequisites printed above; those cases are not done. Push and remote gate, merge, planner F1/live measurements, image retag/deploy and post-deploy proof are not done; they belong to the planner/operator sequence. No live window change is claimed.

---

## Return notes

- DL-295's five decisions were applied without amendment; no design-log entry was added.
- The Appendix's three blobs match exactly, with no difference to explain. Only the specified existing assertion block changed; the shared `_settings()` still ends at 00:30.
- Cron Sunday aliases, start-day attribution across midnight, malformed fields and all fifteen required guard breaks are proven locally. W7 uses `DashboardSettings(_env_file=None)`, not the shared helper.
- Law cycle: both exact PARAM rows, v1.7, Changelog and both rollup labels are complete; counts stay 31 / 38. `surfaces/laws/test-plan.md` remains read-only as specified; no gray clause moved to green.
- The full source/tests/laws/version tree passed `make ci` before this handback fill. Final document and secret checks are recorded below. The builder's final action is the requested branch commit; no push, merge, deploy, Azure command or live proof is part of this build.
- `docs/STATE.md`, `docs/design-log.md`, fleet-check code, protected time-window functions, orchestration, contracts and agents were not changed.
- Pre-existing process-document discrepancies, reported without edits: `AGENTS.md` requires merge permission while `CLAUDE.md` retires it; `docs/sprint-loop.md` still names a 76% floor and retired `trading_v2` paths. The binding spec/CLAUDE rules were followed: branch-only build, sixteen CI steps and a 100.00% floor.

**Main advanced during the build:** observed after the builder commit `e8650614`. The earlier pasted main-relative scope output remains the actual output at that point; the final comparison below differs because the shared main ref moved. No main change was incorporated into this sprint branch. The success-factor checkbox for the current main-relative command is left unfulfilled explicitly; the pinned-base builder scope passes. Main remains at package version 0.125.07, so the branch's PATCH 0.125.08 is still available.

Current-main comparison:

```text
 scripts/gate_selftest_parity_invariants.py   |  56 ------------
 surfaces/tests/test_dashboard_window_days.py | 122 +++++++++++++++++++++++++++
 tests/test_deploy_script_invariants.py       |   4 +-
 3 files changed, 125 insertions(+), 57 deletions(-)
```

Pinned-base comparison (`git diff --stat d80cb1c8ec1d3705205c030f580dc450fa41aaa2 HEAD -- '*test_*.py'`):

```text
 surfaces/tests/test_dashboard_window_days.py | 122 +++++++++++++++++++++++++++
 tests/test_deploy_script_invariants.py       |   4 +-
 2 files changed, 125 insertions(+), 1 deletion(-)
```

**Final handback checks:** the status, tracker-size and markdown-link gates, plus both secret checks, were rerun after filling the handback and changing the README status. All exited 0. Pasted output:

```text
docs/sprints/sprint-270-the-deploy-defaults-are-the-live-wake-window.md: BUILT | **Status:** BUILT
docs_seen=275 SPEC=10 BUILT=1 MERGED=264 UNMAPPED=0 MISSING=0
SPRINT_STATUS_EXIT=0
[WARN] docs/sprints/README.md: 90,689 of 96,000 bytes (94 %)
TRACKER_SIZE_EXIT=0
MARKDOWN_LINKS_EXIT=0
Detect secrets...........................................................Passed
DETECT_SECRETS_EXIT=0
detect-secrets (untracked): no untracked files to scan
UNTRACKED_SECRETS_EXIT=0
```

---

## Planner's review at the merge — 2026-10-12

Re-measured by the planner in `../ta-s270` on the builder's commits `e8650614` and `92cc2165`.
Nothing here is taken from the handback.

- **The code is the measured prototype byte for byte.** The three production files have the
  Appendix's blob ids (`cde71d80`, `32883a57`, `f26cca6c`). Against the spec's commit the branch
  changes the twelve files the spec names and no other; one existing test is edited, the one named.
- **Guards.** The planner's 15 breaks, one at a time against `surfaces/tests` and the invariants
  file, each restored: **15 went red, none survived, none failed to apply**; the restored tree is
  green.
- **The planner's own tests** (29 cases, written for the prototype) were placed beside the
  builder's and run on the built code with the builder's file and the invariants file: 70 passed.
  They are not committed.
- **The law cycle, read by hand where the gate does not look.** The two `PARAM` rows are the
  given text, the law reads v1.7 and the Changelog has its entry; the surfaces' row reads v1.7 in
  `docs/laws/INDEX.md` and in `docs/laws/ledger.md`; the counts stand at 31 / 38.
- **`main` moved during the build:** the planner's own mend of work-queue 129 (`ff10da34`: the
  remote gate's header folders, a new self-test table) and its records. Merged into this branch
  (`d8889161`) with no conflict. The builder's scope check against the newer `main` named that
  mend's new file and said so plainly; against the spec's commit the scope holds.
- **PATCH bump to `0.125.08`**; the change to `uv.lock` is the one version line.

**Written at the merge, before the gate — what was still owed then:** the planner's Windows
`make ci`, all sixteen steps, the remote gate and the CodeQL set-diff for the commit that holds
this block; then F1 at no cost, and the deploy the operator asked for.

**The gate and the merge.** Windows `make ci` exit 0 on the branch at `5d242a8e`: all sixteen steps,
4,777 passed, 8 skipped, 100.00 % coverage. `GATE PROVEN` for `5d242a8e`, run from `../ta-s270`, the
printed SHA equal to its `HEAD`: CI, CodeQL and Security Findings each `success`. Open CodeQL
alerts on the branch: 128, the same 128 as on the last merged branch; none at error level. `main`
fast-forwarded to that commit, tag `v0.125.08`.

**After the merge, 2026-10-12 ([functionality checks](../laws/functionality-checks.md)).**
*F1 passed*, at no cost and read-only: on the merged `main` the script's three defaults equal the
scale rule of each of the 16 live apps; the dashboard's settings give the window cards as
07:25-10:30 and 09:30-10:30 Melbourne, and name Monday 20:25 UTC as the next check from a
Saturday noon, a Sunday evening and a Monday morning, and none while Monday's window is open.
The deploy is not done.

---

## Appendix — the code, measured on the planner's prototype

### `infra/deploy-agents.ps1` — lines 21 to 23 become these four

Blob after the change: `cde71d801d1ca08d168fcccc63c5ebf102e7dd8c`.

```powershell
  [string]$MasterScaleStart = '25 20 * * 1-5',
  # DL-294: weekdays only, one hour. The dispatcher places no run on a weekend.
  [string]$AgentScaleStart = '30 22 * * 1-5',
  [string]$ScaleEnd = '30 23 * * 1-5',
```

### `surfaces/dashboard/settings.py` — the `window_end_utc` field becomes these two

Blob after the change: `32883a5789410d44bd8baf265a4dfc9c5ee18d86`.

```python
    window_end_utc: str = tunable(
        "23:30", why="Matches $ScaleEnd in infra/deploy-agents.ps1 (test-pinned)."
    )
    window_days_utc: str = tunable(
        "1-5",
        why="The scale windows' weekday field in deploy-agents.ps1 (test-pinned).",
    )
```

### `surfaces/dashboard/time_windows.py` — three places

Blob after the change: `f26cca6c76a853c53e2981c397d71fc4805fe637`; 152 lines.

In `latest_window`, between the assignment of `day` and the `return`:

```python
    days = _days(settings.window_days_utc)
    while _cron_day(day) not in days:
        day -= timedelta(days=1)
    return run_window(day.isoformat(), settings)
```

In `next_master_wake`, between `wake += timedelta(days=1)` and the `return`:

```python
    days = _days(settings.window_days_utc)
    while _cron_day(wake.date()) not in days:
        wake += timedelta(days=1)
    return wake.isoformat()
```

Directly above `def _time(`, two blank lines between functions:

```python
def _cron_day(day: date) -> int:
    """Return the day's number as cron counts it: Sunday is 0, Saturday 6."""
    return day.isoweekday() % 7


def _days(value: str) -> frozenset[int]:
    """Read a cron weekday field (`*`, `1-5`, `1,3,5`) as the days a window opens on."""
    if value == "*":
        return frozenset(range(7))
    days: set[int] = set()
    try:
        for part in value.split(","):
            low, dash, high = part.partition("-")
            first = int(low)
            last = int(high) if dash else first
            if not 0 <= first <= last <= 7:
                raise ValueError(part)
            days.update(day % 7 for day in range(first, last + 1))
    except ValueError:
        raise ValueError(
            f"invalid weekday field {value!r}; expected cron days 0-7"
        ) from None
    return frozenset(days)
```
