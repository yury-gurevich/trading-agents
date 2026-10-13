<!-- Agent: planning | Role: sprint handover -->
# Sprint 273 — the secrets scan reads every text file whatever the machine's default encoding, and the gate's self-test leaves nothing behind

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-273-the-secrets-scan-reads-every-file-as-utf-8`
**Status:** SPEC
**Version:** *no bump*
**Effort:** S
**Decisions:** [DL-299](../design-log.md) (this sprint's six decisions, made and measured) · [DL-298](../design-log.md) (where the defect was found) · [work-queue 132 and 130](../work-queue.md)

> **Why no bump.** The change is in `.pre-commit-config.yaml`, in `scripts/` and in tests. None of
> them ships in an image or in the Python package, so the package's behaviour is the same and the
> version stays. The branch and the remote gate are still owed: Python files change.

---

## 🔴 MUST RULE — read the rules for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until the reading record is filled.**

No agent law book binds this sprint: it touches the commit hooks' configuration, `scripts/` and
`tests/`. What binds it:

1. Read [`scripts/module_size_baseline.py`](../../scripts/module_size_baseline.py): it is why the new
   case cannot go into `gate_selftest_cases.py`.
2. Read `CLAUDE.md`, *CI gate*, *Module size* and *Secrets*.
3. Read `scripts/gate_selftest.py`, `scripts/gate_selftest_types.py` and
   `scripts/gate_selftest_docs_cases.py`, whole. They are short.
4. **Write the Law reading record** (bottom of this file) **before** your first change.
5. **If one of them contradicts this spec, STOP and report.**

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No.** No contract, no agent, no law book. No clause ID is cited in a test docstring, because no
clause of any law book governs the commit hooks or the gate's self-test.

### Element → rule map

| Element you will touch | Read first | Why it binds |
| --- | --- | --- |
| `.pre-commit-config.yaml` | `CLAUDE.md`, *Secrets* | the secrets scan is the last line before a push to a public repository |
| `scripts/gate_selftest_encoding_cases.py` (new) | `scripts/module_size_baseline.py`; `CLAUDE.md`, *Module size* | `gate_selftest_cases.py` is frozen at 346 lines and may only shrink |
| `scripts/gate_selftest.py`, `scripts/gate_selftest_types.py` | the two files, whole | the runner is at 157 lines, warns at 150 and blocks at 200; the Appendix leaves it at 153 |
| `tests/test_gate_selftest_runner.py` (new) | `CLAUDE.md`, *Module size* | `tests/` counts for the 200-line block |

⚠️ **No file you leave in the tree may hold a line shaped like a credential.** The plant is
assembled from parts at run time and exists on disk only while its case runs. If the secrets scan
stops your `make ci`, reshape the line. Never add an entry to `.secrets.baseline` and never add an
allowlist comment.

---

## Goal

After this sprint the secrets scan reads every text file in UTF-8 on any machine: at a commit, in
`make ci`, in a hand run of `scripts/check_untracked_secrets.py` and on the remote. The gate's
self-test plants a credential in a file that neither cp1252 nor ASCII can decode, runs the scan in
the environment that used to skip such a file, and fails unless the scan reports the credential.
The self-test also removes each probe folder with whatever a gate wrote into it, so a run leaves
nothing behind.

## Why (context)

`detect-secrets` opens a file with the platform's default encoding and treats a file it cannot
decode as a binary one: it passes over it without a word. On this Windows machine the default is
cp1252. On 2026-10-13 a docs commit with a credential-shaped line passed the commit hook and
failed the remote scan, after the push, in a public repository ([DL-298](../design-log.md)). The
line was an example in a spec; a real secret would have taken the same path.

A docs commit takes the light path: no branch, no `make ci`. Its only local scan is the commit
hook, the one that skips.

Work-queue 130 sits in the same runner: the self-test's parameter case imports a planted
`settings.py`, Python writes a compiled file beside it, and the runner removes only empty probe
folders. The folder stays behind after every local run.

### Measured, 2026-10-14 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| How the library reads a file | `open(filename)` with no encoding; a `UnicodeDecodeError` returns no lines, under the comment *"We flat out ignore binary files"* | *[read]* `detect_secrets/core/scan.py`, `_get_lines_from_file`, release 1.5.0, the one the hook pins |
| Tracked text files cp1252 cannot decode | **184** of 2,408 (169 under `docs/`); 989 are not ASCII; 15 are not UTF-8 text at all | *[measured]* every tracked file decoded three ways |
| The hook today, Windows, on a page with a made-up credential and one character outside cp1252 | no variable set: **passed, exit 0**; `PYTHONUTF8=1`: failed, exit 1, the credential reported; `PYTHONUTF8=0`: passed | *[measured]* `measure_scan.sh` in a clean worktree at `38b35852` |
| The same, Linux | passed, exit 0, only with UTF-8 mode off and the C locale; failed (correctly) otherwise | *[measured]* in WSL on a clone of `38b35852`, pre-commit 4.6.2 from its released archive, by hand |
| With the hook's entry spelled `python -X utf8 -m detect_secrets.pre_commit_hook` | failed, exit 1, the credential reported, in all four environments on Windows and all four on Linux | *[measured]* the same script, both machines |
| Which interpreter that entry runs | the hook environment's own (`…\.cache\pre-commit\…\py_env-python3\Scripts\python.EXE`), in UTF-8 mode with `PYTHONUTF8=0` set | *[measured]* a one-line probe entry |
| The whole tree with that entry and no variable set | passed, exit 0, `.secrets.baseline` untouched: no commit is newly refused on today's tree | *[measured]* `pre-commit run detect-secrets --all-files` |
| `scripts/check_untracked_secrets.py` | runs `pre-commit run detect-secrets --files …`: the same hook. By hand, no variable set, on an untracked page with the plant: exit 0 today, exit 1 with the entry | *[read and measured]* the script, whole; `untracked_script_by_hand.txt` |
| What the self-test leaves behind today | `scripts/_gate_selftest_probe_param_law_sync/agents/probe/__pycache__/settings.cpython-313.pyc`, after a run that reads 38 of 38 passed | *[measured]* a run in a clean worktree. The main checkout holds one dated 2026-08-30 |
| The self-test on the prototype | **40 of 40** passed, the new case and the new invariant among them; no probe path left | *[measured]* Windows, no variable set |
| The new case with the entry weakened | fails: *"gate exited 0 on a planted violation"*, also when the caller exports `PYTHONUTF8=1` as `make gate-selftest` does | *[measured]* breaks 01 and 02 below |
| The tests of the Test plan | on the unchanged tree 8 of 10 cases fail (T2 and T3 pass); on the prototype 10 pass | *[measured]* |
| Breaks | 19 planted, **19 red** | *[measured]* `break_s273.py` on the prototype |
| `make ci` on the prototype | thirteen steps passed in one run (pytest 4,832 passed, 8 skipped, 100.00 %, the ten new cases among them); that run then stopped at the dependency audit on a time-out reaching pypi.org; the audit and the two secrets steps, run alone straight after, each exit 0 | *[measured]* redirected to a file; sixteen steps passed, not in one clean run |
| Our own Python that opens a file without naming an encoding | 4 places, none of them a gate step | *[measured]* ruff's `PLW1514` over the seven folders |
| The self-test's new case on Linux | not run | *[NOT measured]* WSL has no `uv`. The hook was run there by hand with the case's own environment. The remote `quality` job on the branch's first push is the case's first Linux run |
| The builder's sandbox | not measured | *[NOT measured]* its default encoding is not known; with the entry in place it does not matter |

Evidence outside the repo: OneDrive `trading-agents-data/wq132-2026-10-14/`.

---

## Scope — and what is deliberately NOT here

1. **The tests first.** `tests/test_gate_selftest_runner.py`, new, with the eight tests of the Test
   plan. On the unchanged tree T2 and T3 pass and the other six fail.
2. **The hook's entry.** One line and a four-line comment in `.pre-commit-config.yaml` (Appendix 1).
3. **The self-test.** `FailureCase` gains `env`; the runner lays it over the caller's environment,
   holds its two tables as module names, and removes probe folders whole; a new module holds the
   case and the invariant (Appendix 2 to 4).

### Out of scope (do NOT build this sprint)

- **`scripts/check_untracked_secrets.py`, the `Makefile`, the workflows.** None changes. The
  Makefile's `export PYTHONUTF8 = 1` stays: other steps rely on it.
- **`scripts/gate_selftest_cases.py`.** Frozen at 346 lines. Not one byte.
- **`.secrets.baseline`**, the hook's `rev`, `pyproject.toml`, `uv.lock`.
- **The four places our own Python opens a file without naming an encoding.** None is a gate.
- **No `laws.md` edit**, no ADR reversal, no version bump, no design-log entry.

### The road not taken (LAW-06)

- **A local hook that runs the `uv`-locked package** (`uv run python -X utf8 -m …`). Rejected for
  this sprint: it changes which build of the scanner judges a commit, more than the defect needs.
- **`PYTHONUTF8=1` set inside `check_untracked_secrets.py`.** Rejected: a commit goes from git to
  pre-commit to the hook, with no script of ours between them.
- **A machine-wide `PYTHONUTF8=1`.** Rejected: it mends one machine. A new machine, a cloud session
  and a sandbox would skip again, silently.
- **Only `PYTHONUTF8=0` in the case's environment.** Rejected: on Linux the case could then never
  fail, and the remote job is the one place the self-test runs without being asked.
- **`PYTHONDONTWRITEBYTECODE=1` for every case** (work-queue 130). Rejected: it prevents one kind of
  leftover; removing the folder whole removes every kind, and clears the stale one in a checkout.
- **Failing the self-test when a probe path is left at the end.** Not built: a file held open by
  another program on Windows would fail it for a reason no gate is about.

---

## The design decisions — made, and recorded in DL-299

Do not add a design-log entry. They are recorded; this is their summary.

1. **The hook's own entry puts its interpreter in UTF-8 mode.** One place, and every caller passes
   through it: the commit, both secrets steps of `make ci`, the remote job, a hand run.
2. **`scripts/check_untracked_secrets.py` does not change.** It runs the hook.
3. **The self-test runs the hook in the environment that would skip the file** (`PYTHONUTF8=0`,
   `PYTHONCOERCECLOCALE=0`, `LC_ALL=C`) and requires the finding by name, so a tool that merely
   crashes there does not read as a pass.
4. **`FailureCase` gains `env`**, laid over the caller's environment for the one command.
5. **An invariant pins the entry's text** in `.pre-commit-config.yaml`.
6. **A probe folder is removed with whatever is in it** (work-queue 130).

---

## Blast radius — measured 2026-10-14

| What | Detail |
| --- | --- |
| Files changed | `.pre-commit-config.yaml` (94 → 99 lines), `scripts/gate_selftest.py` (157 → 153), `scripts/gate_selftest_types.py` (37 → 41), `scripts/gate_selftest_encoding_cases.py` (new, 54), `tests/test_gate_selftest_runner.py` (new, about 145), this file, this sprint's row in `README.md` |
| Agents affected | none; no file under `agents/`, `kernel/`, `contracts/`, `orchestration/` or `surfaces/` |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | none; nothing here ships in an image |
| Rollback | revert the commit. Nothing is written to the graph, the broker or Azure |

After the merge every commit on a Windows machine is scanned in full. A commit that holds a
credential-shaped line in a file with a character outside cp1252 is refused locally, where it
used to be refused by the remote after the push. That is the point of the sprint.

---

## Steps, in order

1. **Read the rules** (MUST RULE above) and write the Law reading record.
2. **Write the eight tests** and run them on the unchanged tree. T2 and T3 must pass; T1 and T4 to
   T8 must fail. Paste the red output into the Closeout.
3. **Apply the Appendix**, exactly, keeping LF line endings. Check the four blob ids.
4. **Run the tests**: ten cases pass.
5. **Run the self-test**, redirected to a file: `uv run python scripts/gate_selftest.py`. The new
   case and the new invariant read `PASS`. Then
   `find . -name "_gate_selftest_probe*" -not -path "./.git/*" -not -path "./.venv/*"` prints nothing.
6. **Prove the guards can fail (DL-70)**: plant each break of the table under Traps, one at a
   time, see the named test go red, restore.
7. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections**; set Status to `BUILT` here and in this sprint's `README.md` row.

---

## Test plan

All eight in `tests/test_gate_selftest_runner.py`. A *child* is the test's own interpreter run
with `-c`; every case built in a test uses a temporary folder as the root.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| T1 | 🎯 a case's `env` outranks the caller's | the caller's `PYTHONUTF8` set to `1`; a case with `env={"PYTHONUTF8": "0"}` whose child prints `sys.flags.utf8_mode` and exits 1 | `run_failure_case` passes it with `must_output` naming mode 0 |
| T2 | 🪤 a case with no `env` keeps the caller's, whole | a variable set in the caller; a case with no `env` whose child prints it and exits 1 | the child printed the caller's value |
| T3 | 🪤 a failure that does not show the finding is not a pass | a child that exits 1 and prints nothing; `must_output` naming the finding | `run_failure_case` returns false and says *without proving* |
| T4 | 🎯 a probe folder goes with what the gate left in it | a case whose file is `scripts/_gate_selftest_probe_left/agents/probe/settings.py` and whose child writes a `.pyc` into a `__pycache__` beside it, then exits 1 | after the case the probe folder does not exist and `scripts/` does |
| T5 | 🪤 the sweep takes a stale probe folder and nothing else | a stale probe folder holding a `.pyc` two levels down; a neighbour folder holding one; a probe-named folder under `.git` holding one; a stale probe file | the stale folder and the stale file are gone, the file is the one name returned, the neighbour's and `.git`'s files are still there |
| T6 | 🎯 the plant is undecodable where the scan would skip it | the one case of the new module | its file's UTF-8 bytes raise `UnicodeDecodeError` under `cp1252` and under `ascii`; its first line holds the made-up credential; its `env` is exactly the three keys; its command ends by scanning that file; `must_output` names `Basic Auth Credentials` and the file's first line |
| T7 | 🎯 the invariant reads the hook's entry | the repository's `.pre-commit-config.yaml` copied into a temporary root three ways: as it is, with ` -X utf8` cut from the entry, with the entry line removed | `check_invariant` is true for the first and false for the other two; the repository's file holds the full entry exactly once |
| T8 | the runner runs the new case and invariant | the runner's `CASES` and `ALL_INVARIANTS` | each holds the new name exactly once, and no name appears twice in either |

T1, T4 and T5 fail on the unchanged tree: T1 because `FailureCase` takes no `env`, T4 and T5 on
their assertion (the folder is still there). T6 to T8 fail there because the new module does not
exist: load it inside the test and report a missing module with `pytest.fail`, so the red run is
a test failure and not a collection error.

---

## Success factors

- [ ] On the built tree T1 to T8 pass (ten cases); on the unchanged tree T2 and T3 pass and the rest fail.
- [ ] The four files of the Appendix have its blob ids.
- [ ] The self-test's new case and new invariant read `PASS`, and a run leaves no probe path.
- [ ] No file other than those named in *Blast radius* changes; no version bump; `uv.lock` and `.secrets.baseline` untouched.
- [ ] Law-cycle question answered No, with the reason, in the Law reading record.
- [ ] Every break under Traps planted, watched to fail, restored, stated per break.
- [ ] Every touched Python module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The planted character is written as an escape.** In `gate_selftest_encoding_cases.py` it is the
six ASCII characters `\u274c` between quotes. An editor that stores the character itself changes
the blob id, and makes the module one more file cp1252 cannot decode.

🪤 **`make ci` proves nothing about the entry.** The Makefile exports `PYTHONUTF8=1`, so its two
secrets steps read every file with or without this sprint. The proof is the self-test's case.

🪤 **The self-test needs the network for one case.** `pip-audit-cve` asks a vulnerability service.
If your sandbox has no network that case fails: name it in the Return notes and change nothing.
The new case needs none: pre-commit's hook environment is already installed in the user's cache.
If pre-commit tries to install it and cannot, say so and stop.

🪤 **The runner's imports carry `# noqa: E402`**, each line of the block, because the root is put
on the path first. The new import follows its neighbours. Add no other `noqa`.

🪤 **`shutil.rmtree` is given `ignore_errors=True` on purpose.** The functions it replaces
swallowed the same error.

🪤 **The breaks to plant, each alone, with the test that must go red:**

| # | Break | Red |
| --- | --- | --- |
| 01 | cut ` -X utf8` from the entry in `.pre-commit-config.yaml` | T7, and the self-test's case and invariant |
| 02 | remove the entry line | T7, and the self-test's case and invariant |
| 03 | the runner passes no `env` to the command | T1 |
| 04 | the runner passes `env=dict(case.env)` | T2 |
| 05 | the runner merges the other way: `{**case.env, **os.environ}` | T1 |
| 06 | `_remove_probe_dirs` calls `path.rmdir()` inside `try` in place of `shutil.rmtree` | T4, T5 |
| 07 | `_remove_probe_dirs` loses its `.git` guard | T5 |
| 08 | `run_failure_case` no longer calls `_remove_probe_dirs` | T4 |
| 09 | `sweep_stale_probes` no longer calls `_remove_probe_dirs` | T5 |
| 10 | the case's `env` loses `PYTHONUTF8` | T6 |
| 11 | the planted character becomes `"\u00e9"`, which cp1252 decodes | T6 |
| 12 | the planted character becomes the empty text | T6 |
| 13 | the case's `must_output` line is removed | T6 |
| 14 | `CASES` loses `*ENCODING_FAILURE_CASES` | T8 |
| 15 | `ALL_INVARIANTS` loses `*ENCODING_INVARIANTS` | T8 |
| 16 | the invariant's `must_contain` becomes `("detect_secrets.pre_commit_hook",)` | T7 |
| 17 | in `run_failure_case`, `missing = []` | T3 |
| 18 | the credential loses its `":", "notarealpassword",` parts | T6, and the self-test's case |
| 19 | the case's command scans `README.md` | T6, and the self-test's case |

Restore each file before the next break. `git status` must show only your own work at the end.
For 01, 02, 18 and 19, *the self-test's case* means the line `can-fail: secrets-scan-reads-utf-8`
of `uv run python scripts/gate_selftest.py` reads `FAIL`.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow.
  📌 Current sizes: `scripts/gate_selftest.py` **157**, `scripts/gate_selftest_types.py` **37**,
  `scripts/gate_selftest_cases.py` **346** (frozen).
- Module docstring declares `Agent:` / `Role:` / `External I/O:` (the new module: `tooling`; the
  new test file: `tests`).
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file. Count the steps from the `ci:` target.
- Run the suite with `uv run`, never with the venv's interpreter directly.
- **No version bump and no `uv.lock` change.**
- Secrets never through the worktree. The worktree has **no `.env`** and every test here runs
  without one. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. `main` merged into the branch, then `make gate-ran` from the proving worktree, the printed SHA
   checked against `git rev-parse HEAD`.
2. The planner re-measures: the four blobs against the Appendix, the planner's own test file
   beside the builder's, `break_s273.py` (19 breaks) against the builder's tests alone, the open
   CodeQL alerts set-diffed against the last merged branch's (129, 0 errors).
3. **The case's first Linux run**: the remote `quality` job's self-test step, read from its log,
   lists `can-fail: secrets-scan-reads-utf-8` as `PASS`.
4. **F1**, at no cost: in a scratch worktree of the merged `main`, with no variable set, a page
   holding the plant is staged and `git commit` is refused by the hook, naming the credential; the
   page is then unstaged and deleted, never committed. In the main checkout the self-test reads
   every case passed and the folder dated 2026-08-30 is gone.
5. No deploy. Work-queue 132 and 130 close on F1.

---

## Handover — paste this to Codex

```text
You are building Sprint 273 in the worktree ../ta-s273, on the branch
sprint-273-the-secrets-scan-reads-every-file-as-utf-8. Never work on main.

Read docs/sprints/sprint-273-the-secrets-scan-reads-every-file-as-utf-8.md, whole, before
anything else. It is the spec, and its bottom sections are your handback.

In order:
1. Read scripts/module_size_baseline.py, the CI gate, Module size and Secrets sections of
   CLAUDE.md, and scripts/gate_selftest.py, gate_selftest_types.py and
   gate_selftest_docs_cases.py. Fill the Law reading record in the spec BEFORE any change.
2. Write the eight tests of the Test plan in a new file, tests/test_gate_selftest_runner.py.
   Run them on the unchanged tree: T2 and T3 must pass, the other six must fail. Paste the
   red output into the Closeout.
3. Apply the Appendix exactly, keeping LF line endings. git hash-object must then print the
   four blob ids the Appendix names.
4. Run the tests again: ten cases pass.
5. Run uv run python scripts/gate_selftest.py redirected to a file. The lines for
   secrets-scan-reads-utf-8 and secrets-hook-runs-in-utf-8-mode must read PASS, and no path
   named _gate_selftest_probe* may be left in the tree.
6. Plant the breaks in the table under Traps one at a time; each must go red; restore each.
7. Run make ci redirected to a file and read the file. No version bump, no uv.lock change.
8. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in this
   sprint's row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write
   the repository's git directory; if not, leave the tree uncommitted and say so.

DO NOT: change scripts/gate_selftest_cases.py (frozen), scripts/check_untracked_secrets.py,
the Makefile, any workflow, .secrets.baseline, pyproject.toml or uv.lock; change any file
under agents/, kernel/, contracts/, orchestration/ or surfaces/; edit any existing test; add
a design-log entry; edit docs/STATE.md or docs/work-queue.md; bump the version; add a noqa
other than the E402 the runner's import block already carries; add an allowlist comment; let
any Python module reach 200 lines; measure make ci through a pipe.

Traps: the planted character is an escape of six ASCII characters in the source, not the
character itself; no file you leave in the tree may hold a line shaped like a credential
(assemble it from parts, as the Appendix does); make ci exports PYTHONUTF8=1, so its secrets
steps prove nothing about this sprint; the self-test's pip-audit-cve case needs the network
and may fail in your sandbox: name it, change nothing.

STOP and report, writing nothing further, if: a blob id in step 3 does not match after an
exact application; T2 or T3 fails on the unchanged tree; or the line for
secrets-scan-reads-utf-8 in step 5 reads FAIL on the built tree. For anything smaller (a
wrong path, count or command whose intent is plain), correct it, note it in the Return notes
and continue.

Your handback is complete when each of these is true and stated:
 1. the Law reading record is filled, and was filled first;
 2. the red run of step 2 is pasted;
 3. the four blob ids are pasted, with git ls-files --eol for the four files;
 4. the ten test cases pass, output pasted;
 5. the two self-test lines are pasted, and the find for probe paths printed nothing;
 6. each of the 19 breaks is listed with what went red;
 7. make ci's exit code and its sixteen command lines are pasted from the file;
 8. git status shows only the files the spec names;
 9. Status reads BUILT in the spec and in the README row;
10. anything not done is stated as "not done" or "verified failing".
Never write a Result for work you have not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first change.
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
| <element> | <files> | <what binds it> | <Yes/No + what changed> |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** <Yes/No + why>

**Contradictions found between a rule and this spec:** <none | what, and what you did>

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
<the failing test output, on the unchanged tree>
```

**Proof — the green run:**

```text
<the passing output>
```

**Blob ids and line endings:**

```text
<git hash-object and git ls-files --eol for the four files>
```

**The self-test:**

```text
<the two lines, the total, and the output of the find>
```

**Guards planted:** <per break: what was planted, that it failed, that it was restored>

**Module line counts:** <file **n**, file **n**>

**`make ci`:** redirected to `<path>`. Exit code <n>. `<N passed, M skipped>`, coverage `<100.00 %>`.
dependency audit `<result>`. detect-secrets `<result>`.

**`make gate-ran`:** <not done by the builder; the planner's>

**Not met / verified failing:** <plainly, or "none">

---

## Return notes

- <Scope held / where it moved and why.>
- <What you disagreed with in the spec after reading the rules.>
- <What the next sprint should know that is not obvious from the diff.>

---

## Appendix — the change, measured on the planner's prototype

Four files. Apply each exactly and keep LF line endings.

### 1. `.pre-commit-config.yaml` — the secrets block becomes this

Four comment lines are added under the block's heading and one `entry` line under the hook's
`id`. Nothing else in the file changes. Blob id afterwards: `bd1d6c2a5333feb0dc1f0da06b87fb44f8104939`.

```yaml
  # ── Security: detect secrets ──
  # The entry is spelled out to put the hook's interpreter in UTF-8 mode
  # (DL-299). detect-secrets opens a file with the platform's default encoding
  # and passes over one it cannot decode: on Windows that was every file with
  # a character outside cp1252. `-X utf8` outranks the environment.
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        entry: python -X utf8 -m detect_secrets.pre_commit_hook
        args: [--baseline, .secrets.baseline]
```

### 2. `scripts/gate_selftest_types.py` — `FailureCase` becomes this

Blob id afterwards: `9b7d573d96f089721ac2d3cfd1af1d851e714f2a`. The rest of the file is unchanged.

```python
@dataclass(frozen=True)
class FailureCase:
    """A planted violation that a named gate step must reject.

    `env` is laid over the caller's environment for the command alone.
    """

    name: str
    why: str
    files: dict[str, str]
    command: list[str]
    must_output: tuple[str, ...] = ()
    env: dict[str, str] = field(default_factory=dict)
```

### 3. `scripts/gate_selftest_encoding_cases.py` — new, the whole file

Blob id: `7d24202607bbfced79d44730014a2d5dc6c58dff`. 54 lines.

```python
"""The planted violation and the config fact for the secrets scan's encoding.

Agent: tooling
Role: prove the secrets scan reads a UTF-8 file the platform default cannot decode.
External I/O: none; exports an immutable case table and an invariant table.

detect-secrets opens a file with the platform's default encoding and treats one it
cannot decode as binary: it passes over it. On Windows that default is cp1252, and
184 of 2,408 tracked files hold a character it cannot decode (measured 2026-10-14,
DL-298 and DL-299); a Linux machine in the C locale passes over every file that is
not ASCII. The hook's entry puts its interpreter in UTF-8 mode. The case here runs
the hook in the environment that would skip the file and requires the finding.
"""

from __future__ import annotations

from scripts.gate_selftest_types import PROBE_PREFIX, FailureCase, Invariant

HOOK_ENTRY = "entry: python -X utf8 -m detect_secrets.pre_commit_hook"
# The environment in which an interpreter left to itself cannot decode the plant:
# UTF-8 mode off, and on Linux the C locale with its coercion to UTF-8 off, which
# leaves ASCII. On Windows the first key alone leaves the ANSI code page.
UNDECODING_ENV = {"PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0", "LC_ALL": "C"}
# U+274C is E2 9D 8C in UTF-8, and 9D is a byte cp1252 does not define.
UNDECODABLE = "\u274c"
# Assembled from parts so that no line of this file has the shape the scan reports.
_CREDENTIAL = "".join(
    ("postgresql://someuser", ":", "notarealpassword", "@example.invalid/db")
)
_PROBE = f"scripts/{PROBE_PREFIX}_encoding.md"
_WHY = (
    "DL-298: the commit hook passed a credential-shaped line in a page that held "
    "one character outside cp1252, and the remote scan was the first to read it"
)

ENCODING_FAILURE_CASES: tuple[FailureCase, ...] = (
    FailureCase(
        name="secrets-scan-reads-utf-8",
        why=_WHY,
        files={_PROBE: f'dsn = "{_CREDENTIAL}"\n{UNDECODABLE}\n'},
        command=["uv", "run", "pre-commit", "run", "detect-secrets", "--files", _PROBE],
        must_output=("Basic Auth Credentials", f"{PROBE_PREFIX}_encoding.md:1"),
        env=UNDECODING_ENV,
    ),
)

ENCODING_INVARIANTS: tuple[Invariant, ...] = (
    Invariant(
        name="secrets-hook-runs-in-utf-8-mode",
        why=_WHY,
        path=".pre-commit-config.yaml",
        must_contain=(HOOK_ENTRY,),
    ),
)
```

### 4. `scripts/gate_selftest.py` — the whole file after the change

Blob id: `3c01505c59f9fbd67fe81d2b1c7a516d11083e9a`. 153 lines. What changes against today's file: two imports (`os`,
`shutil`), the import of the new module, the two module names `CASES` and `ALL_INVARIANTS` and
their use in `main`, `env=` in `run_failure_case`, `_remove_probe_dirs` in place of
`_remove_empty_probe_dirs` and `_rmdir_if_empty`, and one sentence of the docstring.

```python
"""Prove every gate can fail.

Agent: tooling
Role: plant a known violation per check and assert the check rejects it.
External I/O: writes probe files into the worktree, runs gate commands, deletes them.

A gate that has never been seen failing is not known to work. On 2026-07-22 three
read green while examining nothing: the security gate had run on zero sprint
merges (DL-52), a status claim had no check that could contradict it (DL-54), and
the secret sweep could not see new files (DL-55). Each was found by accident. This
turns "can this check fail?" from a question someone happens to ask into one the
lane answers on every push.

Probe files are named `_gate_selftest_probe*` and are removed in a finally block;
a stale-probe sweep runs first in case a previous run was killed. A probe folder
goes with whatever a gate wrote into it (a compiled file, a cache).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.gate_selftest_cases import FAILURE_CASES  # noqa: E402
from scripts.gate_selftest_docs_cases import DOCS_FAILURE_CASES  # noqa: E402
from scripts.gate_selftest_encoding_cases import (  # noqa: E402
    ENCODING_FAILURE_CASES,
    ENCODING_INVARIANTS,
)
from scripts.gate_selftest_invariants import INVARIANTS  # noqa: E402
from scripts.gate_selftest_parity_invariants import PARITY_INVARIANTS  # noqa: E402
from scripts.gate_selftest_types import (  # noqa: E402
    PROBE_PREFIX,
    FailureCase,
    Invariant,
)

CASE_TIMEOUT_SECONDS = 300
CASES = (*FAILURE_CASES, *DOCS_FAILURE_CASES, *ENCODING_FAILURE_CASES)
ALL_INVARIANTS = (*INVARIANTS, *PARITY_INVARIANTS, *ENCODING_INVARIANTS)


def sweep_stale_probes(root: Path) -> list[str]:
    """Delete probe files a killed run may have left behind."""
    removed = []
    for path in sorted(root.rglob(f"{PROBE_PREFIX}*")):
        if ".git" in path.parts or not path.is_file():
            continue
        path.unlink()
        removed.append(str(path.relative_to(root)))
    _remove_probe_dirs(root)
    return removed


def run_failure_case(case: FailureCase, root: Path) -> tuple[bool, str]:
    """Plant the violation, run the gate, and require a non-zero exit."""
    written = []
    try:
        for name, content in case.files.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(target)
        completed = subprocess.run(  # noqa: S603 - fixed commands from the case table.
            case.command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=CASE_TIMEOUT_SECONDS,
            check=False,
            env={**os.environ, **case.env},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"could not run: {type(exc).__name__}"
    finally:
        for target in written:
            target.unlink(missing_ok=True)
        _remove_probe_dirs(root)
    if completed.returncode == 0:
        return False, "gate exited 0 on a planted violation — it does not catch this"
    output = f"{completed.stdout}\n{completed.stderr}"
    missing = [needle for needle in case.must_output if needle not in output]
    if missing:
        return False, f"gate failed without proving: {', '.join(missing)}"
    return True, f"rejected (exit {completed.returncode})"


def _remove_probe_dirs(root: Path) -> None:
    """Remove each probe folder with whatever a gate left inside it."""
    for path in sorted(root.rglob(f"{PROBE_PREFIX}*")):
        if ".git" in path.parts or not path.is_dir():
            continue
        shutil.rmtree(path, ignore_errors=True)


def check_invariant(inv: Invariant, root: Path) -> tuple[bool, str]:
    """Assert a config fact whose loss would silently disable a gate."""
    path = root / inv.path
    if not path.is_file():
        return False, f"missing file: {inv.path}"
    text = path.read_text(encoding="utf-8")
    absent = [needle for needle in inv.must_contain if needle not in text]
    if absent:
        return False, f"{inv.path} no longer contains: {', '.join(absent)}"
    present = [needle for needle in inv.must_not_contain if needle in text]
    if present:
        return False, f"{inv.path} still contains: {', '.join(present)}"
    return True, "present"


def main() -> int:
    """Run every case and return non-zero if any gate failed to fail."""
    root = _ROOT
    stale = sweep_stale_probes(root)
    if stale:
        print(f"swept {len(stale)} stale probe file(s): {', '.join(stale)}")

    results: list[tuple[str, bool, str]] = []
    for case in CASES:
        ok, detail = run_failure_case(case, root)
        results.append((f"can-fail: {case.name}", ok, detail))
        print(f"{'PASS' if ok else 'FAIL'}  can-fail: {case.name} — {detail}")
        if not ok:
            print(f"      why it matters: {case.why}")
    for inv in ALL_INVARIANTS:
        ok, detail = check_invariant(inv, root)
        results.append((f"invariant: {inv.name}", ok, detail))
        print(f"{'PASS' if ok else 'FAIL'}  invariant: {inv.name} — {detail}")
        if not ok:
            print(f"      why it matters: {inv.why}")

    failed = [name for name, ok, _ in results if not ok]
    print(f"\ngate self-test: {len(results) - len(failed)}/{len(results)} passed")
    if failed:
        listed = "\n".join(f"  {name}" for name in failed)
        sys.stderr.write(
            "\nA gate did not reject its planted violation, or a gate-enabling "
            "config was lost.\nUntil this is fixed, a green lane is not evidence "
            f"that gate examined anything:\n{listed}\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
