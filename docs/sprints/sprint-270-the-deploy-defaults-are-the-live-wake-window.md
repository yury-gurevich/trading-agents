<!-- Agent: planning | Role: sprint handover -->
# Sprint 270 — the deploy script's defaults are the live wake window, and the dashboard knows its weekdays

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-270-the-deploy-defaults-are-the-live-wake-window`
**Status:** SPEC
**Version:** *next available PATCH at merge*
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

- [ ] Every row of the Test plan is a passing test.
- [ ] `git hash-object` prints, on LF bytes, `cde71d801d1ca08d168fcccc63c5ebf102e7dd8c` for `infra/deploy-agents.ps1`, `32883a5789410d44bd8baf265a4dfc9c5ee18d86` for `surfaces/dashboard/settings.py` and `f26cca6c76a853c53e2981c397d71fc4805fe637` for `surfaces/dashboard/time_windows.py`, or each difference is explained.
- [ ] One existing test changed and no other (`git diff --stat main -- '*test_*.py'` shows the new file and the invariants file).
- [ ] Law cycle done, every item: the two `PARAM` rows as given, v1.7, Changelog, the surfaces' row in `INDEX.md` and in `ledger.md`; `check_param_law_sync.py` exits 0.
- [ ] Every guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module under 200 lines.
- [ ] `make ci` exit 0, sixteen steps, 100.00 % coverage.

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
| | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**

**Contradictions found between a law and this spec:**

**Laws found silent where a decision was needed:**

**Clauses that were ⬜ and are now proven:**

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Status:** SPEC

**Tree the proofs ran in (and `.env` present?):**

**Result:**

**Files changed:**

**Design decisions:** recorded as [DL-295](../design-log.md); none added by the build.

**Proof — the red run first:**

**Proof — the green run:**

**Guards planted:**

**Module line counts:**

**`make ci`:**

**`make gate-ran`:** not the builder's: the planner runs it for the exact commit that merges.

**Not met / verified failing:**

---

## Return notes

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
