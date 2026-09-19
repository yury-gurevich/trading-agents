<!-- Agent: planning | Role: sprint handover -->
# Sprint 216 — every tracked text file is LF, and a CRLF can no longer reach the repo

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-216-line-endings-lf`
**Status:** MERGED
**Version:** *no bump*. Only line terminators change, plus one config file and one test, so no package behaviour moves (CLAUDE.md, Version scheme)
**Effort:** S
**Decisions:** closes work-queue item **69** · no ADR · no DRIFT row expected

> **Why no bump.** Python, PowerShell, YAML and JSON readers treat `\r\n` and `\n` the same. Nothing any
> agent, script or test does changes.

**Builder:** GitHub Copilot. This spec gives every command, every expected number and every test case.
**If a number you see differs from the one written here, stop and report. Do not adjust and continue.**

---

## 🔴 MUST RULE — read before you touch anything

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `CLAUDE.md`, sections *CI gate* and *Version scheme* | The 12-step gate; no bump without package behaviour | Binding |
| `docs/laws/conventions.md` | How tests cite law clauses | Read it. No clause governs line endings, so the new test cites none |
| `docs/laws/drift-register.md` | The one law-adjacent file you may append to | Not expected to change |

### 🩹 The law-cycle question — answered **NO**

No file in `contracts/` changes, no agent behaviour changes, and no agent makes a new guarantee. 52 files
change only their line terminators; `.gitattributes` and one test are added.

⚠️ **The one invariant: file content does not change.** After the renormalization commit,
`git diff --ignore-cr-at-eol HEAD~1 HEAD` must print **nothing**. If it prints anything, stop and report.

---

## Goal

After this sprint every tracked text file is stored with LF line endings. A committed `.gitattributes`
makes git store LF on every future `git add`, whatever tool or operating system wrote the file. A test fails
if either of those stops being true.

## Why (context)

**52** of the 1,742 tracked files are stored CRLF or mixed, and the repo has no `.gitattributes`, so what gets
committed depends on which tool wrote the file. On the operator's Windows machine, Git for Windows' system
config sets `core.autocrlf=true` (the operator's global config overrides it to `false`). VS Code creates new
files with CRLF. Python's `write_text` writes CRLF on Windows; `scripts/remediation_gate.py:162` regenerates
its golden file that way. A flip turns a one-line edit into a whole-file diff and makes a merge conflict on
every line. It happened to all of `docs/work-queue.md` on 2026-09-17.

`.gitattributes` is enforced by git itself at `git add`, so it covers every commit, including docs commits
that go straight to `main` without a gate.

### Measured, 2026-09-19 — on `main` @ `4bc2ea6`

| Claim | Value | How |
| --- | --- | --- |
| CRLF or mixed files | **52** (38 `i/crlf`, 14 `i/mixed`): 11 `.py`, 19 `.md`, 9 `.ps1`, 3 `.yml`, 2 `.json`, 2 `.qls`, and one each of `.txt`, `.ini`, `.csv`, `.codeqlignore`, `.bicep`, `.secrets.baseline` | `git ls-files --eol` |
| Every other file | 1,672 `i/lf`, 15 `i/-text` (14 `.png`, 1 `.ico`), 3 `i/none` (empty) | same |
| **Dry run of this exact change** | `.gitattributes` (the 3 lines below) + `git add --renormalize .` stages **53** files. `git diff --cached --ignore-cr-at-eol` shows **only** `.gitattributes`. Index after: **1,725** `i/lf` *(at `4bc2ea6`; the rule that holds on any later `main` is **`i/lf` after = `i/lf` before + 53** — re-measured 2026-09-19 at `f253aff`: 1,673 before, so **1,726** after)*, 15 `i/-text`, 3 `i/none`, **0** `i/crlf`, **0** `i/mixed`. **0** `.png`/`.ico` staged. `ruff format --check` on the 11 `.py`: `11 files already formatted` | throwaway detached worktree at `4bc2ea6`, deleted after |
| The pre-commit hooks will not edit the 52 | **0** have trailing whitespace; **0** lack a final newline | byte scan of all 52 |
| Files that must stay CRLF | **0**: no `.bat`/`.cmd`; no signed `.ps1` (`SIG # Begin signature` appears nowhere) | `git ls-files`; grep |
| Code that byte-compares or hashes these files | **none**. `remediation_selector_golden.json` is read with `json.loads(read_text())` (`scripts/remediation_gate.py:175`); `security/findings-baseline.json` is parsed as a JSON `--baseline` (`.github/workflows/security-findings.yml:80`); `universe_sp500.txt` is read line by line | grep |
| Open branches that could conflict | `dependabot/github_actions/…` touches 4 workflow files, none of them among the 52 | `git diff --name-only` |
| `git ls-files --eol -z` record shape | `i/<class> w/<class> attr/<attrs>` + TAB + path + NUL, e.g. `i/crlf  w/crlf  attr/                 \tagents/scanner/agent.py\0` | git docs; matches the non-`-z` output above |

---

## Scope

1. **`.gitattributes`** at the repo root, exactly these three lines, each ending in LF:

   ```text
   * text=auto eol=lf
   *.png binary
   *.ico binary
   ```

2. **One content-free renormalization commit**, `git add --renormalize .` and nothing else.
3. **One guard test file**, `tests/test_line_endings.py`, specified below.

### Out of scope

- **Markdown linting.** That is work-queue item 73, a separate sprint after this one merges.
- **Any git config, VS Code setting or pre-commit hook.**
- **Fixing `remediation_gate.py:162`'s `write_text`.** `.gitattributes` makes it harmless at commit time.
- **Removing `desktop.ini`** (tracked Windows junk in the root). It is only renormalized here.
- **No version bump.**

### The road not taken (LAW-06)

- **`* text eol=lf` without `auto`.** Rejected: it treats every file as text, the 15 images included, unless
  every binary extension is listed. `text=auto` lets git detect binaries by content, and the two `binary`
  lines are belt and braces.
- **A per-extension list (`*.py text eol=lf` and so on).** Rejected: every new extension is unprotected
  until someone remembers to add it.
- **A new `make ci` step.** Rejected: CLAUDE.md, AGENTS.md and the Copilot instructions all document a
  12-step gate, and remote CI mirrors it. A pytest test runs inside step 9 and changes no step count.
- **A pre-commit `mixed-line-ending` hook as the guard.** Rejected: hooks run only where installed and only
  on staged files, while `.gitattributes` is applied by git on every `git add`.
- **Checking the working tree (`w/`) instead of the index (`i/`).** Rejected: on Windows a file can be CRLF
  on disk before `git add`, and git then stores it LF. The index is what reaches the repo.

## The design decisions this sprint records

Record the five rejected options above, and the choice made, in `docs/design-log.md` as the next free DL
number. Expect **DL-178**; DL-177 is S215's. Re-check at merge.

---

## The guard test — `tests/test_line_endings.py`

Header docstring shaped like `surfaces/tests/test_github_builds.py` (`Agent:` / `Role:` / `External I/O:`).
No law clause governs this, so no clause ID is cited. Under 200 lines.

1. A pure function `offending_eol_paths(records: str) -> list[str]`. It takes the raw `git ls-files --eol -z`
   output, splits it on NUL, splits each non-empty record on its **first TAB**, reads the first
   whitespace-separated field of the left part, and returns the paths whose field is `i/crlf` or
   `i/mixed`, in input order.
2. A parametrized test of that function. **Every row below is one case, input to expected output:**

   | Record passed in (`\t` = TAB, NUL-terminated) | Expected return |
   | --- | --- |
   | `i/lf    w/lf    attr/text=auto eol=lf \tagents/a.py` | `[]` |
   | `i/crlf  w/crlf  attr/                 \tb.py` | `["b.py"]` |
   | `i/mixed w/mixed attr/                 \tdocs/c.md` | `["docs/c.md"]` |
   | `i/-text w/-text attr/-text            \tdocs/d.png` | `[]` |
   | `i/none  w/none  attr/text=auto eol=lf \te.txt` | `[]` |
   | `i/lf    w/crlf  attr/text=auto eol=lf \tf.ps1` (CRLF on disk, LF stored) | `[]` |
   | `i/crlf  w/crlf  attr/                 \tdocs/my file.md` (space in path) | `["docs/my file.md"]` |
   | the `b.py` record followed by the `docs/c.md` record | `["b.py", "docs/c.md"]` |
   | empty string | `[]` |

3. `test_gitattributes_declares_lf_and_binaries`: read `.gitattributes` at the repo root (the directory
   above `tests/`). Its lines must include `* text=auto eol=lf`, `*.png binary` and `*.ico binary`. A
   missing file fails with a message naming it.
4. `test_no_tracked_file_is_stored_crlf`: run `git ls-files --eol -z` in the repo root, feed the output
   to `offending_eol_paths`, and assert the result is `[]`. On failure the message lists the paths.
   **If `git` cannot be found, the test fails; it never skips.** A skipped guard is a disabled guard.
   Find the executable with `shutil.which("git")`. Decode as UTF-8.

---

## Blast radius — measured 2026-09-19

| What | Detail |
| --- | --- |
| Files changed | `.gitattributes` (new, 3 lines); 52 files, line terminators only; `tests/test_line_endings.py` (new); `docs/design-log.md`; this spec's handback sections |
| Agents affected | **No behaviour change.** 7 of the 11 `.py` files ship in images (`agents/analyst/agent.py`, `agents/reporter/agent.py`, `agents/scanner/agent.py`, `agents/provider/domain/market_calendar.py`, `kernel/bus_azure.py`, `orchestration/dispatcher.py`, `orchestration/steps.py`), so the merge rebuilds images. The fleet does not move |
| Contract, vocabulary, env keys, tunables | None |
| Deploy implication | **None.** S213's pending deploy carries these bytes. Until then `/check-fleet` may call the fleet "behind `main`"; that is expected and content-free |

---

## Steps, in order — run every command from the worktree root and compare with the expected output

| # | Do | Expected |
| --- | --- | --- |
| 1 | `git worktree add ../trading-agents-sprint-216-line-endings-lf -b sprint-216-line-endings-lf origin/main`, then work only in that directory. Then run `git ls-files --eol \| awk '{print $1}' \| sort \| uniq -c` and **write the numbers down** | a worktree with **no** `.env`; census shows `38 i/crlf` and `14 i/mixed` (**52** together), `15 i/-text`, `3 i/none`. Your `i/lf` number is the baseline step 10 checks against |
| 2 | Write `tests/test_line_endings.py` exactly as specified. Run `uv run pytest tests/test_line_endings.py --no-cov -q` | **red**: the `.gitattributes` test fails (file missing), and the index test lists **52** paths. Paste the output |
| 3 | Create `.gitattributes` with the 3 lines, then `git add .gitattributes` and `git commit -m "chore: add .gitattributes (text=auto eol=lf)"` | `1 file changed, 3 insertions(+)` |
| 4 | `git diff --ignore-cr-at-eol --stat` | **empty**: no tracked file has a content change on disk. (`git status` may or may not list some of the 52 as modified; that depends on file timestamps, not content, so do not judge by it.) Anything shown here would be swept into the next commit: stop |
| 5 | `git add --renormalize .` then `git diff --cached --name-only \| wc -l` | **52** |
| 6 | `git diff --cached --ignore-cr-at-eol --stat` | **empty** |
| 7 | `git diff --cached --name-only \| grep -cE '\.(png\|ico)$'` | **0** |
| 8 | `git commit -m "chore: renormalize line endings to LF (content-free)"` | the pre-commit hooks pass without editing any file |
| 9 | `git diff --ignore-cr-at-eol HEAD~1 HEAD` and `git show --stat HEAD \| tail -1` | **empty**, then `52 files changed, …`. Paste both |
| 10 | `git ls-files --eol \| awk '{print $1}' \| sort \| uniq -c` | `15 i/-text`, `3 i/none`, and `i/lf` equal to **the step-1 `i/lf` baseline + 53**, and nothing else. No `i/crlf`, no `i/mixed`. (1,725 at `4bc2ea6`; 1,726 from `f253aff` on, because this spec added one LF file. Docs commits landing after that raise it further, which is fine. Only the +53 is pinned) |
| 11 | `uv run pytest tests/test_line_endings.py --no-cov -q` | **green** |
| 12 | **DL-70:** delete the `* text=auto eol=lf` line, run step 11 (red), restore it, run step 11 again (green). Paste both | — |
| 13 | Record DL-178 in `docs/design-log.md`; commit it together with the test | — |
| 14 | `make ci > <file> 2>&1; echo $?`, never piped | exit **0**. Paste the pytest summary line |
| 15 | `git push -u origin sprint-216-line-endings-lf`; wait for CI; `make gate-ran` from the worktree | `GATE PROVEN`, and the SHA printed equals `git rev-parse HEAD` |
| 16 | Fill the handback sections below, set **Status:** `BUILT`, commit, push, then `make gate-ran` on that final commit | `GATE PROVEN` for the final SHA |

---

## Success factors

- [ ] Step 9's content diff is empty; the renormalization commit changes 52 files.
- [ ] Step 10 shows only `i/lf`, `i/-text` and `i/none`, with the counts written above.
- [ ] The test was red first (step 2) and green after (step 11), and the DL-70 break was red (step 12).
- [ ] All nine parser cases pass.
- [ ] DL-178 records the choice and the five rejected options.
- [ ] `make ci` exit 0; no version bump; `pyproject.toml` and `uv.lock` untouched.
- [ ] `make gate-ran` passes for the final commit, with the SHA checked.

---

## Traps

🪤 **Do not convert anything by hand.** No editor "change line endings", no PowerShell, no Python rewrite.
`git add --renormalize .` is the entire conversion. Anything else risks changing content.

🪤 **Do not open `.md` files in the editor during steps 3–9.** VS Code runs markdownlint as the markdown
formatter on this machine and rewrites content on save. That was measured on 2026-09-19, when it altered
headings and text in `docs/design-log.md`. If step 6 or 9 shows any change, stop and report.

🪤 **`git add --renormalize .` restages every tracked file from disk.** A tracked file you edited, the
design log included, would ride into the "content-free" commit. That is why step 4 checks the content
diff and the DL entry waits until step 13.

🪤 **Read the index column (`i/`), not the working tree (`w/`).** After step 8 your working-tree copies may
still be CRLF on disk. Git stores them LF, and that is correct.

🪤 **Do not change any git config.** `core.autocrlf=true` in Git for Windows' system config is exactly what
`.gitattributes` overrides.

🪤 **The test must fail, not skip, when `git` is missing.** Ruff may flag `subprocess.run` with a partial
executable path (`S603`/`S607`). Resolve `git` with `shutil.which` and check `pyproject.toml`'s per-file
ignores for tests before adding any `noqa`.

🪤 **`.secrets.baseline` is one of the 52.** Its content must not change. If detect-secrets rewrites it
during `make ci`, confirm `git diff --ignore-cr-at-eol .secrets.baseline` is empty, and add no entries.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module under 200 lines. No `# noqa` to bypass size.
- `make ci` all 12 steps green, 100.00 % coverage floor (tests are outside the coverage source).
  **Never pipe the gate:** `make ci | tail` reports `tail`'s exit code.
- Secrets never through the worktree. The worktree has no `.env`, and this sprint needs none.

---

## Sequencing after merge (planner)

1. Verify the handback: `make gate-ran` on the tip, the step 9 and step 10 outputs, the red run and the DL-70 break.
2. Merge `--no-ff` to `main` and push. The push rebuilds images; the fleet does not move.
3. **Live check, from the main checkout:** `git ls-files --eol` shows 0 CRLF or mixed. Then, in a scratch
   worktree, write a file with CRLF endings and `git add` it: the index must show `i/lf`. That proves a CRLF
   can no longer reach the repo. Delete the scratch worktree. Record the check in
   `docs/laws/functionality-checks.md`.
4. Package work-queue item 73 (markdownlint) next.

---

## Handover — paste this to Copilot

```text
Sprint 216 - every tracked text file is LF, and a CRLF can no longer reach the repo.
Spec: docs/sprints/sprint-216-every-text-file-is-lf.md. Read it whole first, then AGENTS.md and CLAUDE.md.
Follow the "Steps, in order" table exactly. Each step gives the expected output; if what you see differs,
STOP and report. Do not adjust and continue.

WHERE: git worktree add ../trading-agents-sprint-216-line-endings-lf -b sprint-216-line-endings-lf origin/main
Work only in that worktree (it has no .env). Never commit to main. Do not merge. No version bump:
pyproject.toml and uv.lock must not change.

LAW-CYCLE ANSWER: NO. Line endings, one config file and one test. If you find yourself editing agents/ or
contracts/ beyond the renormalization, STOP.

WHAT: (1) .gitattributes with exactly: "* text=auto eol=lf", "*.png binary", "*.ico binary".
(2) One content-free commit made by "git add --renormalize ." and nothing else: 52 files, and
"git diff --ignore-cr-at-eol HEAD~1 HEAD" must be empty. (3) tests/test_line_endings.py exactly as specified,
including all nine parser cases in the spec's table.

ORDER: test first (red: .gitattributes missing, 52 paths) -> commit .gitattributes alone ->
"git diff --ignore-cr-at-eol --stat" must be empty -> git add --renormalize . (expect 52 staged, empty --ignore-cr-at-eol
diff, 0 png/ico) -> commit -> eol census (15 i/-text, i/lf = before + 53, 3 i/none) -> test green -> DL-70 (remove
the eol line, red, restore) -> DL-178 in docs/design-log.md, committed with the test ->
make ci > <file> 2>&1; echo $?   (never pipe) -> push -> make gate-ran from the worktree, SHA equals
git rev-parse HEAD -> fill the handback, Status: BUILT, commit, push, make gate-ran again.

TRAPS:
- Never convert files by hand: no editor EOL switch, no PowerShell, no Python rewrite.
- Do not open .md files in the editor during the renormalization. VS Code's markdownlint formatter rewrites
  them on save.
- git add --renormalize . restages every tracked file from disk. A tracked file you edited would ride into
  the content-free commit, so the DL entry waits until after it.
- The test reads the index column (i/), not the working tree (w/).
- The test must FAIL, not skip, if git is missing (use shutil.which).
- Do not change git config. Do not add .secrets.baseline entries.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first change.
2. Fill the **Test plan results** table. A case you did not write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a `Result:`
   for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE your first change

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Repository line-ending guard | `docs/laws/conventions.md`; `docs/laws/drift-register.md` | None: no agent law governs repository line endings. | Yes: the guard test cites no law clause and no law-cycle work is added. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. It changes no contracts or agent behaviour; the repository-level Git/index guard does not add an agent guarantee.

**Contradictions found between a law and this spec:** None.

**Laws found silent where a decision was needed:** No law governs repository line endings; the sprint scope explicitly supplies the required repository-level decision.

---

## Test plan results — fill at handback

| Case | Final test name | Status |
| --- | --- | --- |
| parser, nine cases | `test_offending_eol_paths` | PASS — 9 parameter cases passed. |
| `.gitattributes` rules | `test_gitattributes_declares_lf_and_binaries` | PASS — green after creation; DL-70 removal failed as required, then passed after restoration. |
| no tracked file stored CRLF | `test_no_tracked_file_is_stored_crlf` | PASS — normalized index returned no CRLF or mixed paths. |

---

## Closeout — evidence

**Status:** MERGED

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\trading-agents-sprint-216-line-endings-lf` on `sprint-216-line-endings-lf`; `.env` absent (`Test-Path .env` returned `False`).

**Proof — step 2, the red run:**

```text
.........FF                                                              [100%]
FAILED tests/test_line_endings.py::test_gitattributes_declares_lf_and_binaries
AssertionError: missing C:\Users\yury_\Downloads\project\trading-agents-sprint-216-line-endings-lf\.gitattributes
FAILED tests/test_line_endings.py::test_no_tracked_file_is_stored_crlf
AssertionError: assert ['.codeqlignore', ...] == []
2 failed, 9 passed in 14.06s
```

**Proof — steps 6 and 9, the empty content diffs, and step 9's `git show --stat` line:**

```text
$ git diff --cached --ignore-cr-at-eol --stat
[no output]
$ git diff --ignore-cr-at-eol HEAD~1 HEAD
[no output]
$ git show --stat HEAD | tail -1
 52 files changed, 7231 insertions(+), 7231 deletions(-)
```

**Proof — step 10, the eol census:**

```text
     15 i/-text
   1726 i/lf
      3 i/none
```

**Proof — steps 11 and 12, green and the DL-70 break:**

```text
...........                                                              [100%]
11 passed in 1.80s

.........F.                                                              [100%]
FAILED tests/test_line_endings.py::test_gitattributes_declares_lf_and_binaries
AssertionError: assert '* text=auto eol=lf' in ['*.png binary', '*.ico binary']
1 failed, 10 passed in 1.82s

...........                                                              [100%]
11 passed in 1.76s
```

**`make ci`:** `make ci > ci.txt 2>&1; echo $?` returned `True` in PowerShell (successful command). `ci.txt` recorded `2869 passed, 6 skipped`, `Required test coverage of 100.0% reached. Total coverage: 100.00%`, `No known vulnerabilities found`, and both tracked and untracked `Detect secrets` checks passed.

**`make gate-ran`:** `C:\Users\yury_\Downloads\project\trading-agents-sprint-216-line-endings-lf`, implementation SHA `68a2a396d8372e6eceae87c5dacaef1767df5985` (equal to `git rev-parse HEAD` before this closeout commit).

```text
uv run python scripts/assert_gate_ran.py
GATE PROVEN for 68a2a396d8372e6eceae87c5dacaef1767df5985:
  CI: success (attempt 1)
  Security Findings: success (attempt 1)
```

**Not met / verified failing:** none.

---

## Return notes

- The initial attributes-only commit hook added the required final newline to `.gitattributes`; after re-staging, the commit passed. The first renormalization commit attempt exposed the new untracked guard's missing final newline and fixed-executable `S603` suppression; the guard was corrected using the existing `scripts/check_untracked_secrets.py` convention, and the staged 52-file index was re-proven unchanged before the successful commit.
- The planner re-verified that `M  tests/test_bus_azure.py` was an expected member of the staged 52-file normalization. No version bump, deploy, or merge occurred; `pyproject.toml` and `uv.lock` remain untouched.
