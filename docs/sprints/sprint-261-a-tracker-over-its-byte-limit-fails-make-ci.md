<!-- Agent: planning | Role: sprint handover -->
# Sprint 261 — a live tracker over its byte limit fails `make ci`

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-261-a-tracker-over-its-byte-limit-fails-make-ci` (worktree `../ta-s261`, prepared)
**Status:** MERGED 2026-10-11 — no version bump, fast-forwarded to `be7594cb`, GATE PROVEN `be7594cb` (CI, CodeQL, Security Findings); no deploy; F1 passed at no cost
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

- [x] `uv run python scripts/check_tracker_size.py` exits 0 on the branch and prints seven lines.
- [x] The thirteen tests pass, and each was seen red before the script existed.
- [x] `scripts/check_tracker_size.py` is the Appendix's text byte for byte, and `scripts/` holds no
      limit as a number.
- [x] `make ci` runs 16 steps, the new one directly after sprint status; `ci.yml` has the same step in
      the same place.
- [x] `uv run python scripts/gate_selftest.py` exits 0 and prints `PASS  can-fail: tracker-size` and
      the two `tracker-size-gate-wired` invariants.
- [x] No tracker, law book, contract or agent file is edited; `git diff --stat main` lists only the
      files of the Blast radius row and this document and its README row.
- [x] Every planted break of the Traps list went red and was restored — stated per break.
- [x] Every touched module < 200 lines; `gate_selftest_cases.py` still 346.
- [x] `make ci` exit 0, 100.00 % coverage. No version bump.

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
| Checker and thirteen tests | `ops/departments/housekeeping/charter.md` (whole); this spec (whole) | G-SIZE and OPS-TRIM: seven charter limits, decimal KB, git-stored LF bytes, over-limit failure | No: implement the Appendix exactly; use isolated planted charters and trackers. |
| Self-test case, runner and invariants | `scripts/module_size_baseline.py` (whole); `CLAUDE.md`, Module size | Hard block at 200 lines; `gate_selftest_cases.py` is frozen at 346 and may only shrink | No: put the new case in the Appendix's separate module; split test fixtures into a helper. |
| Makefile and CI workflow | `CLAUDE.md`, CI gate | Run every step, redirect to a file, read its exit and output; keep both command lists aligned | No: add tracker size directly after sprint status in both lists. |
| CLAUDE.md, AGENTS.md and charter | This spec's Appendix; both rule files (whole); charter (whole) | Exact step-count and G-SIZE wording changes; no limit or table-row changes | No: apply the supplied diff without extending scope. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No: no contracts or agents change; the checker enforces the existing G-SIZE guarantee.

**Contradictions found between the charter and this spec:** none. OPS-TRIM already says a tracker over its limit fails once the gate exists; the Appendix updates that wording and makes equality explicit. Reading recorded before any code change in `../ta-s261`, branch `sprint-261-a-tracker-over-its-byte-limit-fails-make-ci`; initial tree clean, checker absent, `.env` absent, HEAD `28d77906cc347cee0f8970cc4dbb67c2190c92d3`.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status |
| --- | --- | --- | --- |
| T1 | `test_under_limit_reports_exact_size` | `tests/test_check_tracker_size.py` | PASS |
| T2 | `test_one_byte_over_fails_and_exact_limit_still_reported` | `tests/test_check_tracker_size.py` | PASS |
| T3 | `test_crlf_counts_git_stored_bytes` | `tests/test_check_tracker_size.py` | PASS |
| T4 | `test_utf8_counts_bytes_not_characters` | `tests/test_check_tracker_size.py` | PASS |
| T5 | `test_missing_tracker_fails` | `tests/test_check_tracker_size.py` | PASS |
| T6 | `test_ninety_percent_warns_without_failing` | `tests/test_check_tracker_size.py` | PASS |
| T7 | `test_unreadable_rows_fail_without_partial_reports` | `tests/test_check_tracker_size.py` | PASS |
| T8 | `test_absent_ambiguous_empty_or_duplicate_table_fails` | `tests/test_check_tracker_size.py` | PASS |
| T9 | `test_missing_unreadable_or_duplicate_sections_fail` | `tests/test_check_tracker_size.py` | PASS |
| T10 | `test_padded_cells_and_aligned_rule_rows_read` | `tests/test_check_tracker_size.py` | PASS |
| T11 | `test_only_ops_trim_limit_table_is_read` | `tests/test_check_tracker_size.py` | PASS |
| T12 | `test_repository_charter_tracks_seven_existing_files` | `tests/test_check_tracker_size.py` | PASS |
| T13 | `test_no_argument_uses_working_directory` | `tests/test_check_tracker_size.py` | PASS |

**Tests added beyond the plan:** none. Thirteen test functions; T7 loops over all eight malformed rows, T8 over all five bad table shapes, and T9 over the two file failures and duplicate sections.

---

## Closeout — evidence

**Status:** MERGED

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s261`, branch `sprint-261-a-tracker-over-its-byte-limit-fails-make-ci`; `.env` no. Initial HEAD `28d77906cc347cee0f8970cc4dbb67c2190c92d3`; all proof commands ran from this worktree's root.

**Result:** The checker reports all seven real trackers within their charter limits and exits 0. The thirteen tests pass, including one-byte overflow, exact-limit equality, LF byte counting, missing trackers and fail-closed charter parsing. All twelve prescribed breaks made those tests red and were restored to green. Both gate lists run tracker size directly after sprint status; the self-test rejected its planted overflow and passed both wiring invariants. Local `make ci` completed all sixteen commands with exit 0 and 100.00 % coverage; the gate self-test passed 34/34.

**Files changed:** new `scripts/check_tracker_size.py`, `scripts/gate_selftest_docs_cases.py`, `tests/test_check_tracker_size.py`, `tests/tracker_size_fixtures.py`; edited `scripts/gate_selftest.py`, `scripts/gate_selftest_invariants.py`, `Makefile`, `.github/workflows/ci.yml`, `CLAUDE.md`, `AGENTS.md`, `ops/departments/housekeeping/charter.md`, this sprint document and only the Sprint 261 status token in `docs/sprints/README.md`.

**Preflight:** the Appendix checker was executed in memory before its file existed, against the untouched branch's trackers: exit 0. `git apply --check` on the Appendix diff: exit 0. No charter/spec contradiction. No tracker trim or limit change was needed.

**Proof — the red run first:**

Ran `uv run pytest tests/test_check_tracker_size.py --no-cov -q` before the checker existed; exit 1. Redirected to `C:/Users/yury_/Downloads/project/ta-s261-evidence/2026-10-11/red-tests.txt`.

```text
FFFFFFFFFFFFF                                                            [100%]
================================== FAILURES ===================================
_____________________ test_under_limit_reports_exact_size _____________________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:25: in test_under_limit_reports_exact_size
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
___________ test_one_byte_over_fails_and_exact_limit_still_reported ___________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:33: in test_one_byte_over_fails_and_exact_limit_still_reported
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
______________________ test_crlf_counts_git_stored_bytes ______________________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:48: in test_crlf_counts_git_stored_bytes
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
____________________ test_utf8_counts_bytes_not_characters ____________________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:59: in test_utf8_counts_bytes_not_characters
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
_________________________ test_missing_tracker_fails __________________________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:67: in test_missing_tracker_fails
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
__________________ test_ninety_percent_warns_without_failing __________________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:75: in test_ninety_percent_warns_without_failing
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
______________ test_unreadable_rows_fail_without_partial_reports ______________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:90: in test_unreadable_rows_fail_without_partial_reports
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
____________ test_absent_ambiguous_empty_or_duplicate_table_fails _____________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:101: in test_absent_ambiguous_empty_or_duplicate_table_fails
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
_____________ test_missing_unreadable_or_duplicate_sections_fail ______________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:110: in test_missing_unreadable_or_duplicate_sections_fail
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
________________ test_padded_cells_and_aligned_rule_rows_read _________________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:124: in test_padded_cells_and_aligned_rule_rows_read
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
___________________ test_only_ops_trim_limit_table_is_read ____________________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:137: in test_only_ops_trim_limit_table_is_read
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
_____________ test_repository_charter_tracks_seven_existing_files _____________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:144: in test_repository_charter_tracks_seven_existing_files
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
___________________ test_no_argument_uses_working_directory ___________________
tests\tracker_size_fixtures.py:29: in load_checker
    return importlib.import_module("scripts.check_tracker_size")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'scripts.check_tracker_size'

During handling of the above exception, another exception occurred:
tests\test_check_tracker_size.py:161: in test_no_argument_uses_working_directory
    checker = load_checker()
              ^^^^^^^^^^^^^^
tests\tracker_size_fixtures.py:31: in load_checker
    pytest.fail(f"tracker size checker is missing: {exc}")
E   Failed: tracker size checker is missing: No module named 'scripts.check_tracker_size'
=========================== short test summary info ===========================
FAILED tests/test_check_tracker_size.py::test_under_limit_reports_exact_size
FAILED tests/test_check_tracker_size.py::test_one_byte_over_fails_and_exact_limit_still_reported
FAILED tests/test_check_tracker_size.py::test_crlf_counts_git_stored_bytes - ...
FAILED tests/test_check_tracker_size.py::test_utf8_counts_bytes_not_characters
FAILED tests/test_check_tracker_size.py::test_missing_tracker_fails - Failed:...
FAILED tests/test_check_tracker_size.py::test_ninety_percent_warns_without_failing
FAILED tests/test_check_tracker_size.py::test_unreadable_rows_fail_without_partial_reports
FAILED tests/test_check_tracker_size.py::test_absent_ambiguous_empty_or_duplicate_table_fails
FAILED tests/test_check_tracker_size.py::test_missing_unreadable_or_duplicate_sections_fail
FAILED tests/test_check_tracker_size.py::test_padded_cells_and_aligned_rule_rows_read
FAILED tests/test_check_tracker_size.py::test_only_ops_trim_limit_table_is_read
FAILED tests/test_check_tracker_size.py::test_repository_charter_tracks_seven_existing_files
FAILED tests/test_check_tracker_size.py::test_no_argument_uses_working_directory
13 failed in 4.24s
```

**Proof — the green run:**

`uv run pytest tests/test_check_tracker_size.py --no-cov -q`, exit 0; redirected to `C:/Users/yury_/Downloads/project/ta-s261-evidence/2026-10-11/green-tests.txt`.

```text
.............                                                            [100%]
13 passed in 1.35s
```

`uv run python scripts/check_tracker_size.py`, exit 0 after the README status change; redirected to `C:/Users/yury_/Downloads/project/ta-s261-evidence/2026-10-11/tracker-size-final.txt`.

```text
[WARN] docs/STATE.md: 36,320 of 40,000 bytes (90 %)
[OK] docs/work-queue.md: 55,865 of 64,000 bytes (87 %)
[WARN] docs/sprints/README.md: 91,745 of 96,000 bytes (95 %)
[OK] docs/sprints/INDEX.md: 23,863 of 48,000 bytes (49 %)
[OK] docs/design-log.md: 334,004 of 512,000 bytes (65 %)
[OK] docs/laws/functionality-checks.md: 96,790 of 160,000 bytes (60 %)
[OK] docs/laws/drift-register.md: 130,343 of 160,000 bytes (81 %)
```

**Guards planted:** each prescribed break was planted alone, ran `uv run pytest tests/test_check_tracker_size.py --no-cov -q`, failed, and was restored before the next break. Pasted test summaries follow; logs are `guard-NN-red.txt` and `guard-NN-restored.txt` under `C:/Users/yury_/Downloads/project/ta-s261-evidence/2026-10-11/` (break 6's final restoration is `guard-06-restored-final.txt`).

| Break | Guard | Planted result | Restoration result |
| --- | --- | --- | --- |
| 1 | equality is allowed | `2 failed, 11 passed in 1.81s`; exit 1 | restored; `13 passed in 1.26s`; exit 0 |
| 2 | CRLF normalization | `1 failed, 12 passed in 1.44s`; exit 1 | restored; `13 passed in 1.22s`; exit 0 |
| 3 | warning boundary | `1 failed, 12 passed in 1.47s`; exit 1 | restored; `13 passed in 1.22s`; exit 0 |
| 4 | decimal KB | `8 failed, 5 passed in 1.52s`; exit 1 | restored; `13 passed in 1.24s`; exit 0 |
| 5 | whole limit cell | `1 failed, 12 passed in 1.53s`; exit 1 | restored; `13 passed in 1.44s`; exit 0 |
| 6 | unreadable row rejection | `1 failed, 12 passed in 1.90s`; exit 1 | restored; `13 passed in 1.27s`; exit 0 |
| 7 | unique table | `1 failed, 12 passed in 1.46s`; exit 1 | restored; `13 passed in 1.27s`; exit 0 |
| 8 | section end | `11 failed, 2 passed in 1.49s`; exit 1 | restored; `13 passed in 1.25s`; exit 0 |
| 9 | table end | `10 failed, 3 passed in 1.53s`; exit 1 | restored; `13 passed in 1.29s`; exit 0 |
| 10 | failure exit | `3 failed, 10 passed in 1.49s`; exit 1 | restored; `13 passed in 1.26s`; exit 0 |
| 11 | missing tracker failure | `1 failed, 12 passed in 1.70s`; exit 1 | restored; `13 passed in 1.42s`; exit 0 |
| 12 | working directory root | `1 failed, 12 passed in 1.77s`; exit 1 | restored; `13 passed in 1.62s`; exit 0 |

Break 6's first restoration patch matched the separator-row `continue` rather than the malformed-row branch; that intermediate restoration was verified failing (`11 failed, 2 passed in 1.79s`, exit 1). Both branches were corrected, the checker was compared byte for byte to the Appendix, and the final restoration passed before break 7.

**Gate self-test:** `uv run python scripts/gate_selftest.py`, redirected to `C:/Users/yury_/Downloads/project/ta-s261-evidence/2026-10-11/gate-selftest.txt`. Exit code **0**. The complete file was read; actual output:

```text
PASS  can-fail: ruff — rejected (exit 1)
PASS  can-fail: module-size — rejected (exit 1)
PASS  can-fail: module-size-reads-scripts — rejected (exit 1)
PASS  can-fail: module-header — rejected (exit 1)
PASS  can-fail: law-coverage — rejected (exit 1)
PASS  can-fail: param-law-sync — rejected (exit 1)
PASS  can-fail: sprint-status — rejected (exit 1)
PASS  can-fail: markdown-links — rejected (exit 1)
PASS  can-fail: version-scheme — rejected (exit 1)
PASS  can-fail: untracked-secrets — rejected (exit 1)
PASS  can-fail: pip-audit-cve — rejected (exit 1)
PASS  can-fail: accepted-advisory-re-check — rejected (exit 1)
PASS  can-fail: gate-ran-rejects-abbreviated-sha — rejected (exit 1)
PASS  can-fail: gate-ran-rejects-zero-runs — rejected (exit 1)
PASS  can-fail: gate-ran-judges-the-newest-attempt-not-the-first — rejected (exit 1)
PASS  can-fail: tracker-size — rejected (exit 1)
PASS  invariant: merge-procedure-asserts-a-run-exists — present
PASS  invariant: gate-ran-target-exists — present
PASS  invariant: security-gate-runs-on-push — present
PASS  invariant: ci-runs-on-push — present
PASS  invariant: sprint-status-gate-wired-locally — present
PASS  invariant: sprint-status-gate-wired-in-ci — present
PASS  invariant: tracker-size-gate-wired-locally — present
PASS  invariant: tracker-size-gate-wired-in-ci — present
PASS  invariant: untracked-scan-wired-into-ci — present
PASS  invariant: dependency-audit-not-ignored-by-ci — present
PASS  invariant: dependency-audit-wired-in-ci — present
PASS  invariant: size-block-reads-scripts-locally — present
PASS  invariant: size-block-reads-scripts-in-ci — present
PASS  invariant: dependabot-pins-python-to-3-13 — present
PASS  invariant: graph-vocabulary-guard-wired — present
PASS  invariant: graph-vocabulary-injected-at-deploy — present
PASS  invariant: codeql-custom-query-referenced — present
PASS  invariant: codeql-config-queries-not-overridden — present

gate self-test: 34/34 passed
```

**Module line counts:** `scripts/check_tracker_size.py` **115**, `scripts/gate_selftest_docs_cases.py` **45**, `scripts/gate_selftest.py` **156**, `scripts/gate_selftest_invariants.py` **186**, `tests/test_check_tracker_size.py` **165**, `tests/tracker_size_fixtures.py` **71**. All touched Python modules are below 200; untouched `scripts/gate_selftest_cases.py` remains **346**. Both new scripts match the Appendix byte for byte, and the seven diffed files match its target git blob hashes.

**`make ci`:** redirected to `C:/Users/yury_/Downloads/project/ta-s261-evidence/2026-10-11/make-ci.txt`, with no pipe. Exit code **0** (`MAKE_CI_EXIT=0`). The complete 2,157-line file was read and its sixteen commands compared with the expanded `ci:` target in order. **4,687 passed, 8 skipped**, coverage **100.00 %**. Dependency audit passed: no unaccepted vulnerabilities, one existing accepted advisory re-checked. detect-secrets passed for both tracked files and all four new files. Actual final output:

```text
TOTAL                                                           20252      0   4292      0  100.00%
Coverage HTML written to dir htmlcov
Required test coverage of 100.0% reached. Total coverage: 100.00%
=========================== short test summary info ===========================
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 4687 passed, 8 skipped, 2470 warnings in 573.26s (0:09:33) ==========
uv run python scripts/check_dependency_audit.py
accepted: PYSEC-2026-2447 (diskcache 5.6.3) - reachable only via the 'optimizer' extra, installed by 1 of 15 Dockerfiles; each installing command excludes diskcache by name; the dev group carries it too, and every sync passes --no-dev or excludes it by name; no fix release exists; every deployed optimizer installation excludes diskcache by name (S254, DL-266, ADR-0032) [DL-184] - retire when diskcache publishes a fixed release, or the optimizer extra is dropped
No unaccepted vulnerabilities; 1 accepted advisory re-checked
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 4 new file(s)
```

**Not met / verified failing:** no unresolved failure in the build scope. Eight conditional tests are not done (skipped: local `.env`/Service Bus/Celery/Postgres proof, optional SciPy oracle and provider network probes; exact reasons above). Commit, push, remote gates, the planner's 24 tests and 36 breaks, merge, F1 and the later tracker closeouts are **not done**; they belong to the planner's subsequent sequence. No version bump; `uv.lock` untouched.

---

**Final documentation and scope checks:** after filling the handback and setting both statuses to BUILT, the sprint-status, Markdown-link and documentation secret checks passed. Logs are `final-sprint-status.txt`, `final-markdown-links.txt` and `final-docs-secrets.txt` in the same external evidence directory. The final scope check compared both new scripts with the Appendix, all seven diffed files with its target blobs, the README byte change with HEAD and all excluded files with HEAD; it checked all thirteen changed/new files for LF and every touched Python module for the line block. Actual output:

```text
SPRINT_STATUS_EXIT=0
docs_seen=273 SPEC=11 BUILT=1 MERGED=261 UNMAPPED=0 MISSING=0
MARKDOWN_LINKS_EXIT=0
DOCS_SECRETS_EXIT=0
Detect secrets...........................................................Passed
SCOPE: all 13 files allowed; LF; BUILT; handback filled; correct branch; no .env; no script probe residue
FINAL SCOPE PROOF: PASS
```

---

## Return notes

- Scope held: all thirteen changed/new files are in the specified blast radius or handback. No tracker was trimmed, moved or shortened; the only tracker edit changes the Sprint 261 README status token from SPEC to BUILT, adding one byte. No agent, contract, law book, limit, exemption, version, lockfile, frozen case table or excluded tracker changed. Working files have LF line ends. Changes remain uncommitted and unpushed on the requested branch.
- No disagreement with the spec after reading the charter. The initial branch passed the Appendix checker in memory, and the supplied diff applied cleanly; both new scripts are byte-for-byte Appendix copies and all seven diffed files match the Appendix's target blob hashes. Use branch-specific context when restoring repeated `continue` statements: the corrected break 6 restoration and its extra red evidence are recorded above.
- The current branch emits two passing size warnings: `docs/STATE.md` at 90 % and `docs/sprints/README.md` at 95 %. The README was 91,744 bytes before the status change and is 91,745 after it; no size limit moved. The planner's review, push/exact-SHA remote proof, merge, F1 and later work-queue/STATE/functionality-register closeouts are not done. The completed status and evidence edits passed the affected documentation checks recorded above.
- The existing PARAM self-test leaves an ignored 676-byte `settings.cpython-313.pyc` under its probe root, preventing the empty-directory cleanup. The generated bytecode was removed by its verified literal path, then the existing empty-directory sweep removed the probe directories. The final scope check confirms no script probe residue. A runner cleanup change is not done: the runner stays exactly at the Appendix's version.
- Existing workflow parity gap, outside this Appendix: `ci.yml` has no standalone normal-tree `check_param_law_sync.py` or `check_untracked_secrets.py` command, while the local sixteen-command target does. Its gate self-test exercises the planted cases. The specified tracker-size step is wired in both places; extending unrelated remote steps is not done because this sprint requires the exact Appendix diff. Remote gate execution remains not done.

---

## Planner's review at the merge — 2026-10-11

Re-measured by the planner in `../ta-s261` on the builder's tree, which was handed back uncommitted
on `28d77906`; the planner committed it as `6782ba22`. Nothing here is taken from the handback.

- **The code is the measured prototype byte for byte.** Every production file has the prototype's
  blob id, read by applying the prototype's patch to `28d77906` in a scratch index: the new step
  (`d2fc19a7`), the self-test runner, its invariants and its new case table, the `Makefile`, the
  workflow, the charter, `CLAUDE.md` and `AGENTS.md`. The builder's two test files are its own.
- **Guards.** The planner's 36 breaks of `scripts/check_tracker_size.py`, one at a time against
  the builder's tests alone, each restored: **36 went red, none survived, none failed to apply.**
- **The planner's own tests** (24 cases, written for the prototype) were placed beside the
  builder's with their own fixtures and run on the built code: all passed. They are not committed.
- **The step on the real tree.** After `main` was merged in it exits 0 and warns twice:
  `docs/STATE.md` at 95 % and `docs/sprints/README.md` at 92 % of their limits.
- **`main` moved during the build:** S268's merge and its records, and the S269 spec. They were
  merged into this branch (`954a9a29`); the two met in one file, `docs/sprints/README.md`,
  resolved row by row (every row but this sprint's is `main`'s, byte for byte).
- **One working file was CRLF** (`scripts/check_tracker_size.py`; the committed bytes are LF).
- **No version bump**, by the spec: the step ships no package behaviour.
- **Two things the builder named, neither built here.** The parameter self-test leaves a compiled
  file under its probe root that the empty-folder sweep cannot remove. And the workflow runs
  neither `check_param_law_sync.py` nor `check_untracked_secrets.py` on the normal tree, although
  `make ci` does: the remote gate is two steps short of the local one. Both go to the work queue.

**The gate and the merge.** Windows `make ci` exit 0 on the branch at `be7594cb`: all sixteen steps,
4,722 passed, 8 skipped, 100.00 % coverage. `GATE PROVEN` for `be7594cb`, run from `../ta-s261`, the
printed SHA equal to its `HEAD`: CI, CodeQL and Security Findings each `success`. Open CodeQL
alerts on the branch: 128, one more than on the last merged branch, a note (`py/mixed-returns`) in
`tests/tracker_size_fixtures.py` where a helper ends in `pytest.fail`; none at error level.
`main` fast-forwarded to that commit. No tag: no bump.

**After the merge, 2026-10-11 ([functionality checks](../laws/functionality-checks.md)).**
*F1 passed*, at no cost: on the merged `main` the step exits 0 and warns for two trackers; on a
scratch copy of the charter and the seven trackers it exits 0 untouched, passes with `STATE.md`
padded to exactly 40,000 bytes, and exits 1 at 40,001 naming the file and the overshoot; the
remote CI run of the commit shows the step *Tracker size limits* green. STATE was trimmed in the
merge record's own commit, from 95 % of its limit.

**Written at the merge, before the gate — what was still owed then:** the planner's Windows
`make ci`, the remote gate and the CodeQL set-diff for the commit that holds this block; then F1
at no cost.

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
