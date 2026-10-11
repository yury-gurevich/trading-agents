<!-- Agent: planning | Role: sprint handover -->
# Sprint 261 — a live tracker over its byte limit fails `make ci`

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-261-a-tracker-over-its-byte-limit-fails-make-ci` (worktree `../ta-s261`, prepared)
**Status:** SPEC
**Version:** *no bump*
**Effort:** S
**Decisions:** [DL-291](../design-log.md) the gate reads its limits from the charter · work-queue 117 · [housekeeping charter](../../ops/departments/housekeeping/charter.md) G-SIZE, OPS-TRIM

> **Why no bump.** The change is one read-only script, its tests and its wiring into the gate. It ships
> in no image and changes no package behaviour, so the version does not move
> ([chore-three-scripts-leave-the-size-baseline](chore-three-scripts-leave-the-size-baseline.md) is the
> precedent). It still takes the full cycle (branch, `make ci`, remote gate), because it adds Python.

---

## 🔴 MUST RULE — read the rules for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until the reading record is filled.**

No agent law book binds this sprint: it touches `scripts/`, `tests/`, the gate's wiring and three
documents. What binds it is the housekeeping charter, which states the limits this script enforces.

1. Read [`ops/departments/housekeeping/charter.md`](../../ops/departments/housekeeping/charter.md), whole.
   The table under `## OPS-TRIM` is the script's only source of numbers.
2. Read [`scripts/module_size_baseline.py`](../../scripts/module_size_baseline.py): it is why the new
   self-test case cannot go into `gate_selftest_cases.py`.
3. Read `CLAUDE.md`, *CI gate* and *Module size*.
4. **Write the Law reading record** (bottom of this file) **before** your first code change.
5. **If the charter contradicts this spec, STOP and report.**

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No.** No contract, no agent, no law book. The charter's gate G-SIZE already states the guarantee; this
sprint makes `make ci` check it. The charter's wording is brought up to date (version 0.4, the exact
text is in the Appendix). No clause ID is cited in a test docstring, because G-SIZE is a charter gate
and not a clause of an agent's law book.

### Element → rule map

| Element you will touch | Read first | Why it binds |
| --- | --- | --- |
| `scripts/check_tracker_size.py` (new) | the charter, G-SIZE and OPS-TRIM | the limits, what a KB is, and that a tracker over its limit fails the gate |
| `scripts/gate_selftest_docs_cases.py` (new), `scripts/gate_selftest.py`, `scripts/gate_selftest_invariants.py` | `scripts/module_size_baseline.py`; `CLAUDE.md`, *Module size* | `gate_selftest_cases.py` is frozen at 346 lines and may only shrink |
| `Makefile`, `.github/workflows/ci.yml` | `CLAUDE.md`, *CI gate* | the two lists of steps are kept by hand and must both gain the step |
| `CLAUDE.md`, `AGENTS.md`, the charter | this spec's Appendix | each states the step count or the hand-measured limits |

⚠️ **The script holds no limit of its own.** If you find yourself typing `40` or `512` into
`scripts/`, stop: the number belongs to the charter's table and is read from there.

---

## Goal

At merge, `make ci` and the remote `CI` workflow both run `scripts/check_tracker_size.py`, which reads
the limit of each live tracker from the table under `## OPS-TRIM` in the housekeeping charter and exits
1 when a tracker is over its limit, when a tracker the table names is missing, or when a row of the
table cannot be read. The gate self-test plants an over-limit tracker and requires the step to reject it.

## Why (context)

The charter set byte limits for the seven most-edited trackers on 2026-10-09 and said the limits would
become a step of `make ci`. Until today they were measured by hand, and two of the seven sat far over:
the design log at 1,324 KB against 512 and the functionality-check register at 285 KB against 160. Both
were trimmed on 2026-10-11 (commit `20597d82`), so every tracker is now within its limit and the gate
can start with no exemption list. Without the gate the next growth is found by hand again, or not at all.

### Measured, 2026-10-11 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Every tracker is within its limit on `main` | 7 of 7; the largest share is `docs/sprints/README.md` at 94 % | *[measured]* the prototype step in `../ta-s261` on `20597d82`: exit 0, six `[OK]` lines and one `[WARN]` |
| The step fails on the tree as it stood before the trim | exit 1, two `[FAIL]` lines (`over by 811,742`, `over by 125,316`) | *[measured]* the prototype on the seven files of `b8f112af` |
| The step fails one byte over a limit | exit 1, `40,001 of 40,000 bytes, over by 1` | *[measured]* 4,107 bytes appended to a copy of `docs/STATE.md` |
| The step fails on a limit it cannot read | exit 1, `cannot read the limit row`, no `[OK]` line printed | *[measured]* `64 KB` changed to `64KB` in a copy of the charter |
| The prototype breaks no existing test | none of 4,674: `make ci` exit 0 over all 16 steps, 4,698 passed (the 4,674 of `main` and the planner's 24), 8 skipped, 100.00 % | *[measured]* `make ci` in `../ta-s261` on the prototype, redirected to a file |
| The prototype's guards can fail | 36 breaks, 36 red | *[measured]* one break at a time against the planner's 24 tests, the script restored and green after |
| The self-test case rejects its planted tracker | exit 0, 34 of 34; `PASS  can-fail: tracker-size — rejected (exit 1)` and both `tracker-size-gate-wired` invariants | *[measured]* `scripts/gate_selftest.py` on the prototype |
| Sizes on the prototype | `check_tracker_size.py` 115 lines, `gate_selftest_docs_cases.py` 45, `gate_selftest.py` 155 → 156, `gate_selftest_invariants.py` 168 → 186 | *[measured]* `wc -l` |
| A working file with CRLF line ends reads larger on disk than git stores it | 1,200 bytes on disk, 1,000 stored, for 200 five-byte lines | *[measured]* the planner's test T3 |
| How long the step takes | under one second | *[measured]* on the seven real trackers (1.9 MB before the trim) |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first.** `tests/test_check_tracker_size.py`, the thirteen tests of the Test plan,
   written before the script exists and watched to fail.
2. **`scripts/check_tracker_size.py`**, exactly as the Appendix gives it.
3. **The gate self-test:** `scripts/gate_selftest_docs_cases.py` as the Appendix gives it, read by the
   runner beside the first case table; two invariants that keep the step wired in the `Makefile` and in
   `ci.yml`.
4. **The wiring:** one line in the `Makefile`'s `ci:` target and one step in `ci.yml`, each directly
   after the sprint-status step.
5. **The three documents:** `CLAUDE.md` and `AGENTS.md` say 16 steps and name the new one; the charter
   says the gate checks the limits (version 0.4). The Appendix holds the exact text.

### Out of scope (do NOT build this sprint)

- **No trim.** Do not move, shorten or archive anything in a tracker. If the step is red on your
  branch, a tracker grew on `main` after this spec was written: STOP and report.
- **No change to a limit**, and no new row in the charter's table.
- **No exemption list.** Nothing like `module_size_baseline.py` for trackers.
- **No size check for any other file** (an archive file, a sprint document, a law book).
- **No design-log entry.** DL-291 is already written. Do not edit `docs/design-log.md`,
  `docs/work-queue.md`, `docs/STATE.md` or `docs/laws/functionality-checks.md` at all: they are four of
  the trackers the step measures.
- **No version bump, no `uv.lock` change, no law-book edit.**

### The road not taken (LAW-06)

Recorded in full in [DL-291](../design-log.md); the short form:

- **The limits as constants in the script, with a test comparing them to the charter.** Rejected: two
  lists and a comparison that is the same parse; a limit raised in code would not show in the rule the
  operator reads.
- **A frozen list for trackers over their limit.** Rejected: none is over since the trim, and a frozen
  design log would stop its own next entry while an unfrozen one is a warning that passes.
- **Counting bytes on disk.** Rejected: a working file saved with CRLF reads up to a few percent
  larger than what git stores, so the step would fail on one machine and pass on the remote.
- **Failing at 90 %.** Rejected: the sprint table sits at 94 % directly after a trim.
- **Skipping a row that cannot be read.** Rejected: a typo in a limit would silently take that tracker
  out of the gate.

---

## The design decisions — made, and recorded in DL-291

1. The script reads the limits from the charter's table and holds none.
2. A KB is 1,000 bytes; a file is measured as git stores it (CRLF counted as LF).
3. A tracker exactly at its limit passes; one byte over fails.
4. A missing tracker, a missing or unreadable charter, a second `## OPS-TRIM` section, a second
   `Tracker | Limit` table in the section, an empty table, a tracker listed twice and a row whose first
   two cells are not a backticked path and `<whole number> KB` each fail the whole check.
5. From 90 % of its limit a tracker is reported `[WARN]` and passes.
6. Every tracker is reported even after one has failed.
7. The root is the first argument, or the working directory when there is none, as
   `check_sprint_status.py` does; the self-test relies on it.

---

## Blast radius — measured 2026-10-11

| What | Detail |
| --- | --- |
| Files changed | new: `scripts/check_tracker_size.py` (115), `scripts/gate_selftest_docs_cases.py` (45), `tests/test_check_tracker_size.py`, optionally a helper module under `tests/`; edited: `scripts/gate_selftest.py` (155 → 156), `scripts/gate_selftest_invariants.py` (168 → 186), `Makefile`, `.github/workflows/ci.yml`, `CLAUDE.md`, `AGENTS.md`, `ops/departments/housekeeping/charter.md` |
| Agents affected | none |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | none: nothing here is in an image |
| Rollback | `git revert` of the merge; nothing outside the repository changes |

**Named consequences, as designed.** A commit to `main` that takes a tracker over its limit turns
`main`'s `CI` red, and every branch that then merges `main` with it. A docs commit goes to `main`
without the gate, so whoever writes one runs the step first. The sprint table is at 94 % of its limit
with twelve full rows, so it will need its trim again within a few sprints.

---

## Steps, in order

1. **Read** the charter and the two files of the MUST RULE; fill the Law reading record.
2. **Write the tests** of the Test plan and watch them fail on the tree without the script. Paste the
   red output into the Closeout.
3. **Add `scripts/check_tracker_size.py`** from the Appendix, byte for byte.
4. **Add the self-test case and the two invariants**, and make the runner read both case tables.
5. **Wire the step** into the `Makefile` and `ci.yml`.
6. **Edit the three documents** with the Appendix's text.
7. **Prove the guards can fail:** plant each break listed under Traps, one at a time, run the test
   file, see it red, restore.
8. **`make ci`**, every step, redirected to a file; then `uv run python scripts/gate_selftest.py`,
   redirected to a file.
9. **Fill the handback sections**; set Status to `BUILT` here and in this sprint's row of
   `docs/sprints/README.md`.

---

## Test plan

All in `tests/test_check_tracker_size.py`, each on a charter and trackers planted under `tmp_path`
(T12 alone reads the repository). The planted charter holds a `Tracker | Limit` table in a section
before `## OPS-TRIM`, another in a section after it, and a table of another shape inside the section
after the limit table: none of the three may be read.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| T1 | 🎯 a tracker under its limit passes and says its size | 500 bytes against `2 KB` | exit 0; the output is exactly `[OK] docs/a.md: 500 of 2,000 bytes (25 %)` and a line end |
| T2 | 🎯 one byte over fails, the limit itself passes | 1,001 bytes, listed first, and 1,000 bytes, each against `1 KB` | exit 1; `[FAIL] docs/over.md: 1,001 of 1,000 bytes, over by 1.` and `do not raise the limit`; the second tracker is still reported, `[WARN] docs/at.md: 1,000 of 1,000 bytes (100 %)` |
| T3 | CRLF line ends are counted as git stores them | `b"line\r\n" * 200` against `1 KB` | 1,200 bytes on disk, `stored_size` 1,000, exit 0 |
| T4 | bytes are counted, not characters | 501 times `é` against `1 KB` | exit 1 |
| T5 | 🪤 a tracker the charter names and the tree lacks fails | a row and no file | exit 1; `[FAIL] docs/gone.md: named in` |
| T6 | 90 % warns and passes | 899 and 900 bytes against `1 KB` | exit 0; `[OK] ... (89 %)` and `[WARN] ... (90 %)` |
| T7 | 🪤 a row that cannot be read fails the whole check | after one good row, each of: `40 kB`, `0.5 MB`, `about 40 KB`, `0 KB`, an empty limit cell, a path without backticks, two paths in one cell, a row of one cell | exit 1; `cannot read the limit row`; no `[OK]` line at all |
| T8 | 🪤 a charter without one readable table fails | each of: no `## OPS-TRIM` heading; no table headed `Tracker`, `Limit`; two such tables in the section; a table with no rows; a tracker listed twice | exit 1, with `section, found 0`, `table, found 0`, `table, found 2`, `has no rows`, `is listed twice` |
| T9 | 🪤 no charter, an unreadable one, or two sections fail | no charter file; a charter of the bytes `ff fe`; a text with two `## OPS-TRIM` headings | exit 1 and a `[FAIL] ops/departments/housekeeping/charter.md: ` line for each of the first two; `CharterError` matching `section, found 2` |
| T10 | a table the editor padded reads the same | cells padded with spaces, a rule row of `:---`, `---:`, `:---:` | the two limits, in bytes |
| T11 | only the table under OPS-TRIM is read, and it ends at its last row | the planted charter as described above | exactly the one planted limit |
| T12 | the repository's own charter names seven trackers that exist | nothing | `read_limits` returns the seven paths with 40,000, 64,000, 96,000, 48,000, 512,000, 160,000 and 160,000; each file exists |
| T13 | with no argument the working directory is the root | `monkeypatch.chdir` to a planted root | exit 0; `[OK] docs/a.md` |

🪤 Keep each test module under 200 lines. The planner's own file is 150 lines with its planted charter
in a 63-line helper module, `tests/tracker_size_fixtures.py`; one file of both would be over.

---

## Success factors

- [ ] `uv run python scripts/check_tracker_size.py` exits 0 on the branch and prints seven lines.
- [ ] The thirteen tests pass, and each was seen red before the script existed.
- [ ] `scripts/check_tracker_size.py` is the Appendix's text byte for byte, and `scripts/` holds no
      limit as a number.
- [ ] `make ci` runs 16 steps, the new one directly after sprint status; `ci.yml` has the same step in
      the same place.
- [ ] `uv run python scripts/gate_selftest.py` exits 0 and prints `PASS  can-fail: tracker-size` and
      the two `tracker-size-gate-wired` invariants.
- [ ] No tracker, law book, contract or agent file is edited; `git diff --stat main` lists only the
      files of the Blast radius row and this document and its README row.
- [ ] Every planted break of the Traps list went red and was restored — stated per break.
- [ ] Every touched module < 200 lines; `gate_selftest_cases.py` still 346.
- [ ] `make ci` exit 0, 100.00 % coverage. No version bump.

---

## Traps

🪤 **A backslash in a string you paste through a shell heredoc arrives as a real line break.** The
planner's first copy of `gate_selftest_docs_cases.py` was a syntax error for that reason. Create files
with your editor, and compare `scripts/check_tracker_size.py` with the Appendix afterwards.

🪤 **`gate_selftest_cases.py` may not grow by one line.** The new case goes in the new module.

🪤 **A green self-test proves nothing if the case never ran.** Read the output for the line
`can-fail: tracker-size`.

🪤 **The step reads the working directory.** Run it from the worktree's root.

**The breaks to plant** (in `scripts/check_tracker_size.py`, one at a time, run
`uv run pytest tests/test_check_tracker_size.py --no-cov -q`, expect red, restore):

1. `if size > limit:` → `if size >= limit:`
2. drop `.replace(b"\r\n", b"\n")` from `stored_size`
3. `WARN_PERCENT = 90` → `91`
4. `BYTES_PER_KB = 1000` → `1024`
5. `_LIMIT_CELL.fullmatch(cells[1])` → `_LIMIT_CELL.search(cells[1])`
6. the `raise CharterError(f"cannot read the limit row: ...")` → `continue`
7. `if len(heads) != 1:` → `if not heads:`
8. `return body[: ends[0]] if ends else body` → `return body`
9. in the row loop, `break` → `continue`
10. `return 1 if failed else 0` → `return 0`
11. the missing-file branch `return True` → `return False`
12. `Path.cwd().resolve()` → `Path(__file__).resolve().parents[1]`

The planner runs 36 breaks on the built tree at the review.

---

## Guardrails (every sprint)

- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` beyond the `E402` on the
  runner's new import, which matches the two beside it.
- Module docstring declares `Agent:` / `Role:` / `External I/O:` (the header step reads `scripts/`).
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Secrets never through the worktree. A worktree has no `.env`; nothing here needs one. **State which
  tree you ran in.**
- Leave working files with LF line ends (`git ls-files --eol`).

---

## Sequencing after merge (the planner's)

1. Run the planner's 24 tests and 36 breaks on the built tree
   (`OneDrive/trading-agents-data/s261-2026-10-11/`); compare the script with the prototype.
2. Merge `main` into the branch if `main` has moved; the step must still exit 0.
3. Push, `make gate-ran` from `../ta-s261`, check the printed SHA, merge, push. No tag: no bump.
4. **F1, at no cost:** on merged `main`, the step exits 0; on a scratch copy with one tracker taken one
   byte over, it exits 1; the remote `CI` run of the merged commit shows the step *Tracker size limits*.
5. Close work-queue 117; STATE; the functionality-check row.

---

## Handover — paste this to Codex

```text
You are building Sprint 261 in the worktree ../ta-s261, on the branch
sprint-261-a-tracker-over-its-byte-limit-fails-make-ci. Never work on main.

Read docs/sprints/sprint-261-a-tracker-over-its-byte-limit-fails-make-ci.md, whole, before
anything else. It is the spec, and its bottom sections are your handback.

In order:
1. Read ops/departments/housekeeping/charter.md (whole), scripts/module_size_baseline.py and the
   "CI gate" and "Module size" sections of CLAUDE.md. Fill the Law reading record in the spec
   BEFORE any code.
2. Write the thirteen tests of the Test plan in tests/test_check_tracker_size.py (a helper module
   under tests/ is allowed). Run them before the script exists and paste the red output into the
   Closeout.
3. Create scripts/check_tracker_size.py and scripts/gate_selftest_docs_cases.py from the spec's
   Appendix, byte for byte.
4. Apply the Appendix's diff: scripts/gate_selftest.py, scripts/gate_selftest_invariants.py,
   Makefile, .github/workflows/ci.yml, CLAUDE.md, AGENTS.md, the housekeeping charter.
5. Plant the twelve breaks listed under Traps, one at a time; each must turn the test file red;
   restore after each.
6. Run make ci redirected to a file and read the file. Run uv run python scripts/gate_selftest.py
   redirected to a file and find the line "can-fail: tracker-size".
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT in the spec and in the
   sprint's row of docs/sprints/README.md.

DO NOT: bump the version or touch uv.lock; edit docs/design-log.md, docs/work-queue.md,
docs/STATE.md, docs/laws/functionality-checks.md or any other tracker beyond the one README row;
trim, move or shorten anything in a tracker; change a limit; add an exemption list; put a limit
as a number into scripts/; add a line to scripts/gate_selftest_cases.py; edit a law book; use
noqa beyond the one E402 the Appendix shows; let any module reach 200 lines; measure make ci
through a pipe.

Traps: a backslash pasted through a shell heredoc becomes a real line break, so create files
with the editor and compare with the Appendix; the step reads the working directory, so run it
from the worktree's root; leave files with LF line ends.

If the step is red on the untouched branch, if the Appendix's diff does not apply cleanly, or if
the charter contradicts the spec, STOP and report. State anything not done as "not done" or
"verified failing". Never write a Result for work you have not done.
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

| Element | Rule file(s) read | What binds it | Did reading change your approach? |
| --- | --- | --- | --- |
| <element> | <files> | <the gate or section> | <Yes/No + what changed> |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** <Yes/No + why>

**Contradictions found between the charter and this spec:** <none | what, and what you did>

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status |
| --- | --- | --- | --- |
| T1 | <name> | <file> | PASS/FAIL |

**Tests added beyond the plan:** <none | what and why>

---

## Closeout — evidence

**Status:** <BUILT | MERGED>

**Tree the proofs ran in (and `.env` present?):** <path, branch, .env yes/no>

**Result:** <what is now true, in the artefact's own words — not the intent restated>

**Files changed:** <list>

**Proof — the red run first:**

```text
<the failing test output, before the script existed>
```

**Proof — the green run:**

```text
<the passing output, and the step's seven lines>
```

**Guards planted:** <per break of the Traps list: that it failed, that it was restored>

**Gate self-test:** redirected to `<path>`. Exit code <n>. <the `can-fail: tracker-size` line and the two invariant lines>

**Module line counts:** <file **n**, file **n**>

**`make ci`:** redirected to `<path>`. Exit code <n>. `<N passed, M skipped>`, coverage `<100.00 %>`.
dependency audit `<result>`. detect-secrets `<result>`.

**Not met / verified failing:** <plainly, or "none">

---

## Return notes

- <Scope held / where it moved and why.>
- <What you disagreed with in the spec after reading the charter.>
- <What the next sprint should know that is not obvious from the diff.>

---

## Appendix — the code, measured on the planner's prototype

### `scripts/check_tracker_size.py` (new, whole file)

```python
"""Check that every live tracker is within the byte limit its charter declares.

Agent: tooling
Role: fail the gate when a tracker named under OPS-TRIM is over its limit.
External I/O: reads the housekeeping charter and the trackers it names; writes
reports to stdout.

The limits live in one place, the table under `## OPS-TRIM` in the housekeeping
charter. This script reads that table and holds no number of its own, so the
rule the operator reads and the rule the gate enforces cannot drift apart. A
table it cannot read in full is a failure, never an empty pass.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CHARTER = "ops/departments/housekeeping/charter.md"
SECTION = "## OPS-TRIM"
BYTES_PER_KB = 1000
WARN_PERCENT = 90

_PATH_CELL = re.compile(r"`([^`]+)`")
_LIMIT_CELL = re.compile(r"(\d+) KB")
_RULE_CELL = re.compile(r":?-+:?")


class CharterError(ValueError):
    """The charter's limit table is absent or holds a row that cannot be read."""


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _section(text: str) -> list[str]:
    lines = text.splitlines()
    starts = [n for n, line in enumerate(lines) if line.startswith(SECTION)]
    if len(starts) != 1:
        raise CharterError(f"expected one '{SECTION}' section, found {len(starts)}")
    body = lines[starts[0] + 1 :]
    ends = [n for n, line in enumerate(body) if line.startswith("## ")]
    return body[: ends[0]] if ends else body


def read_limits(text: str) -> dict[str, int]:
    """Return tracker path -> limit in bytes, from the table under OPS-TRIM."""
    body = _section(text)
    heads = [
        n
        for n, line in enumerate(body)
        if line.startswith("|") and _cells(line)[:2] == ["Tracker", "Limit"]
    ]
    if len(heads) != 1:
        raise CharterError(f"expected one Tracker | Limit table, found {len(heads)}")
    limits: dict[str, int] = {}
    for line in body[heads[0] + 1 :]:
        if not line.startswith("|"):
            break
        cells = _cells(line)
        if all(_RULE_CELL.fullmatch(cell) for cell in cells):
            continue
        path = _PATH_CELL.fullmatch(cells[0])
        limit = _LIMIT_CELL.fullmatch(cells[1]) if len(cells) > 1 else None
        if path is None or limit is None or int(limit.group(1)) == 0:
            raise CharterError(f"cannot read the limit row: {line.strip()[:80]}")
        if path.group(1) in limits:
            raise CharterError(f"{path.group(1)} is listed twice")
        limits[path.group(1)] = int(limit.group(1)) * BYTES_PER_KB
    if not limits:
        raise CharterError("the Tracker | Limit table has no rows")
    return limits


def stored_size(path: Path) -> int:
    """Count the bytes git stores for the file: line ends as LF."""
    return len(path.read_bytes().replace(b"\r\n", b"\n"))


def _report(root: Path, name: str, limit: int) -> bool:
    """Print one tracker's verdict and return whether it fails the gate."""
    path = root / name
    if not path.is_file():
        sys.stdout.write(f"[FAIL] {name}: named in {CHARTER} and not found.\n")
        return True
    size = stored_size(path)
    if size > limit:
        sys.stdout.write(
            f"[FAIL] {name}: {size:,} of {limit:,} bytes, over by {size - limit:,}. "
            f"Run the tracker trim ({CHARTER}, OPS-TRIM); do not raise the limit.\n"
        )
        return True
    percent = size * 100 // limit
    label = "WARN" if percent >= WARN_PERCENT else "OK"
    sys.stdout.write(f"[{label}] {name}: {size:,} of {limit:,} bytes ({percent} %)\n")
    return False


def main(argv: list[str]) -> int:
    """Check the trackers under the given root, or the working directory."""
    root = Path(argv[0]).resolve() if argv else Path.cwd().resolve()
    charter = root / CHARTER
    try:
        limits = read_limits(charter.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, CharterError) as exc:
        sys.stdout.write(f"[FAIL] {CHARTER}: {exc}\n")
        return 1
    failed = [name for name, limit in limits.items() if _report(root, name, limit)]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

### `scripts/gate_selftest_docs_cases.py` (new, whole file)

```python
"""Planted violations for the gates that read the repo's documents.

Agent: tooling
Role: hold the can-fail cases that do not fit the frozen first case table.
External I/O: none; exports an immutable case table.

`gate_selftest_cases.py` is frozen at its measured size (`module_size_baseline.py`)
and may only shrink, so a new case lives here and the runner reads both tables.
"""

from __future__ import annotations

from scripts.gate_selftest_types import PROBE_PREFIX, FailureCase

_TRACKER_ROOT = f"scripts/{PROBE_PREFIX}_tracker_size"
_TRACKER_CHARTER = """## OPS-TRIM

| Tracker | Limit |
| --- | --- |
| `docs/STATE.md` | 1 KB |
"""

DOCS_FAILURE_CASES: tuple[FailureCase, ...] = (
    FailureCase(
        name="tracker-size",
        why=(
            "S261: a tracker over the byte limit its charter declares must fail "
            "the gate; by hand, two of seven sat over their limit for weeks"
        ),
        files={
            f"{_TRACKER_ROOT}/ops/departments/housekeeping/charter.md": (
                _TRACKER_CHARTER
            ),
            f"{_TRACKER_ROOT}/docs/STATE.md": "x" * 1001,
        },
        command=[
            "uv",
            "run",
            "python",
            "scripts/check_tracker_size.py",
            _TRACKER_ROOT,
        ],
        must_output=("[FAIL] docs/STATE.md: 1,001 of 1,000 bytes", "over by 1"),
    ),
)
```

### The wiring and the three documents (a diff against `20597d82`)

```diff
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index a3fcd712..59a83aa3 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -52,2 +52,4 @@ jobs:
         run: uv run python scripts/check_sprint_status.py
+      - name: Tracker size limits
+        run: uv run python scripts/check_tracker_size.py
       - name: Markdown link integrity
diff --git a/AGENTS.md b/AGENTS.md
index 8b7b6c19..475fd4b2 100644
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -17,4 +17,4 @@ were given.

-2. **`make ci` must pass — all 15 steps.** ruff, format, mypy, import-linter, module size, module
-   header, law coverage, PARAM/settings sync, sprint status, markdown links, version scheme, pytest at a
+2. **`make ci` must pass — all 16 steps.** ruff, format, mypy, import-linter, module size, module
+   header, law coverage, PARAM/settings sync, sprint status, tracker size, markdown links, version scheme, pytest at a
    **100.00 % coverage floor**, pip-audit, detect-secrets, untracked secrets. Never lower the floor. Never declare work green without running
diff --git a/CLAUDE.md b/CLAUDE.md
index 34f50f08..3aed773e 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -26,3 +26,3 @@ check `agents/<name>/laws/laws.md` if a law question is involved.

-## CI gate — always run all 15 steps
+## CI gate — always run all 16 steps

@@ -35,10 +35,10 @@ Never declare a change "green" on the strength of intent. **Run `make ci` locall
 push your own work** — it keeps a broken push off the remote — and confirm the remote gate afterwards.
-The gate has 15 steps: ruff, format, mypy, import-linter, module size, module header,
-law coverage, PARAM/settings sync, sprint status, markdown links, version scheme,
+The gate has 16 steps: ruff, format, mypy, import-linter, module size, module header,
+law coverage, PARAM/settings sync, sprint status, tracker size, markdown links, version scheme,
 pytest (100 % coverage floor), dependency audit, detect-secrets, untracked secrets.
 *(The count read 12 before S221, and this sentence said 14 while the target already ran 15 — it had
-missed S224's sprint-status step. **Re-count from the `ci:` target, never from this sentence.**)*
+missed S224's sprint-status step; S261 added the tracker-size step, the sixteenth. **Re-count from the `ci:` target, never from this sentence.**)*

 **Verifying someone else's handback is the exception: `make gate-ran` is the proof, not a local
-re-run** (operator, 2026-08-31). Remote CI runs the same 15 steps on clean infrastructure with **no
+re-run** (operator, 2026-08-31). Remote CI runs the same 16 steps on clean infrastructure with **no
 `.env`**, so a green gate for the merged SHA is a *stronger* signal than a local pass, and repeating
diff --git a/Makefile b/Makefile
index d079794b..c303d7af 100644
--- a/Makefile
+++ b/Makefile
@@ -55,2 +55,3 @@ ci:             ## Simulate the GitHub CI quality/security lane locally
 	uv run python scripts/check_sprint_status.py
+	uv run python scripts/check_tracker_size.py
 	uv run python scripts/check_markdown_links.py
diff --git a/ops/departments/housekeeping/charter.md b/ops/departments/housekeeping/charter.md
index bfd06ee1..278ed505 100644
--- a/ops/departments/housekeeping/charter.md
+++ b/ops/departments/housekeeping/charter.md
@@ -5,3 +5,3 @@ owner: operator + AI housekeeping loop  (→ candidate "Librarian" agent)
 status: draft
-version: 0.3
+version: 0.4
 implements_with: [.gitignore, ops/maintenance/ledger.md, "del-folder convention (../trading-agent-del/)"]
@@ -62,3 +62,3 @@ file, docs that lie about reality. **Blast radius is comprehension, not runtime.
 | G-DOC | README/INDEX reflect the current structure | current | refresh in the same change |
-| G-SIZE | each live tracker is under its size limit, counted in bytes | the table under OPS-TRIM | run the tracker trim |
+| G-SIZE | each live tracker is at or under its size limit, counted in bytes | `scripts/check_tracker_size.py`, a step of `make ci`, reading the table under OPS-TRIM | run the tracker trim |

@@ -106,4 +106,6 @@ entry on which something is still owed.
 limit. `STATE.md` is trimmed by whoever is writing it that session, because deciding what is still
-owed there is not housekeeping. Until `make ci` checks the limits the trim measures them by hand;
-the gate step is a chore of its own, and once it exists a tracker over its limit fails the gate.
+owed there is not housekeeping. `make ci` checks the limits (`scripts/check_tracker_size.py`, S261). It reads the table above and holds
+no number of its own: a tracker over its limit fails the gate, and so does a row of that table it
+cannot read. A row is read as the tracker's path in backticks in its first cell and a whole number
+of KB in its second; from 90 % of its limit a tracker is reported as due for the next trim.

@@ -172,2 +174,3 @@ become a specific agent.")
 | 0.1 | 2026-06-24 | initial draft — registers the root / INDEX / README / git-size housekeeping process; names the future Librarian agent |
+| 0.4 | 2026-10-11 | G-SIZE is checked by `make ci` (S261): the gate reads the limits from the table under OPS-TRIM |
 | 0.3 | 2026-10-11 | first trim of the design log and the functionality-check register, and what it taught the two rules: an older design-log entry that the work queue or STATE links stays live; the register's operations table and harness lesson stay; a KB is 1,000 bytes on the file as git stores it |
diff --git a/scripts/gate_selftest.py b/scripts/gate_selftest.py
index 4a0b54c3..5e5aff9e 100644
--- a/scripts/gate_selftest.py
+++ b/scripts/gate_selftest.py
@@ -28,2 +28,3 @@ if str(_ROOT) not in sys.path:
 from scripts.gate_selftest_cases import FAILURE_CASES  # noqa: E402
+from scripts.gate_selftest_docs_cases import DOCS_FAILURE_CASES  # noqa: E402
 from scripts.gate_selftest_invariants import INVARIANTS  # noqa: E402
@@ -127,3 +128,3 @@ def main() -> int:
     results: list[tuple[str, bool, str]] = []
-    for case in FAILURE_CASES:
+    for case in (*FAILURE_CASES, *DOCS_FAILURE_CASES):
         ok, detail = run_failure_case(case, root)
diff --git a/scripts/gate_selftest_invariants.py b/scripts/gate_selftest_invariants.py
index acf2ec5f..5e34fd3f 100644
--- a/scripts/gate_selftest_invariants.py
+++ b/scripts/gate_selftest_invariants.py
@@ -65,2 +65,20 @@ INVARIANTS: tuple[Invariant, ...] = (
     ),
+    Invariant(
+        name="tracker-size-gate-wired-locally",
+        why=(
+            "S261: a tracker limit that make ci does not run is measured by hand, "
+            "which is how the design log reached 1.3 MB against 512 KB"
+        ),
+        path="Makefile",
+        must_contain=("scripts/check_tracker_size.py",),
+    ),
+    Invariant(
+        name="tracker-size-gate-wired-in-ci",
+        why=(
+            "S261: CI enumerates quality commands independently from the "
+            "Makefile, so both paths must retain the tracker size check"
+        ),
+        path=".github/workflows/ci.yml",
+        must_contain=("scripts/check_tracker_size.py",),
+    ),
     Invariant(
```
