<!-- Agent: planning | Role: chore spec + closeout: three frozen oversize scripts split under the block -->
# chore-three-scripts-leave-the-size-baseline — three frozen scripts fit the 200-line block, and the baseline lists twelve

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `chore-three-scripts-leave-the-size-baseline`
**Status:** BUILT
**Version:** no bump
**Effort:** S
**Decisions:** none owed beyond the split seams, which are the builder's call and go in the closeout ·
closes three of the fifteen entries in `scripts/module_size_baseline.py` (work-queue item 78's ratchet)

> **Why no bump.** All three files are `scripts/` tooling. No image copies them (the only `scripts/`
> files in any Dockerfile are `dispatch_scheduled_run.py` and `universe_sp100.txt`), and coverage does
> not read `scripts/`. CLAUDE.md: a change that ships no package behaviour takes no bump. No bump
> also means no `uv lock`, which a cloud session cannot re-resolve.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

No agent law book binds these files: they are tooling under `scripts/`, outside every agent folder,
and the one agent module they call (`agents/master/remediation_gate.py`) is **not touched**. The
binding rules are the repo's: [`CLAUDE.md`](../../CLAUDE.md) (module size, version scheme, branch
convention) and [`docs/laws/conventions.md`](../laws/conventions.md).

### The law-cycle question

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No.** It moves code between `scripts/` modules with no behaviour change. If you find yourself
editing anything under `agents/`, `contracts/`, `kernel/`, `orchestration/` or `surfaces/`, **stop
and report**: that is outside this chore.

### Element → rule map

| Element you will touch | Read first | Why it binds |
| --- | --- | --- |
| `scripts/check_worktrees.py` and its new sibling | `CLAUDE.md` § Module size | 200-line hard block; the module header (`Agent:` / `Role:` / `External I/O:`) is a gate step |
| `scripts/retrain_return_model_helpers.py`, `scripts/retrain_return_model.py`, `tests/test_retrain_return_model.py` | same | the CLI and the test import 11 public names from the helpers module |
| `scripts/remediation_gate.py` and its new sibling | same | `make ci` imports nothing from it; it is run by hand |
| `scripts/module_size_baseline.py` | its own docstring | the list may only shrink; a split file's entry **must** be deleted |

⚠️ **No behaviour change.** Every split file must produce the same output for the same input. If a
split seems to need a behaviour change, stop and report.

---

## Goal

`scripts/check_worktrees.py`, `scripts/retrain_return_model_helpers.py` and
`scripts/remediation_gate.py` are each **under 200 lines** (aim under 150), each new module carries
the standard header, the three entries are deleted from `LEGACY_MAX_LINES`, and every script behaves
exactly as before. The frozen list goes from **15** to **12**.

## Why (context)

CLAUDE.md froze the oversize `scripts/` files on 2026-09-23 as a ratchet that "can only get
shorter". No entry has left the list since, and three of them sit within six lines of the block,
so they are the cheapest to clear. The operator wants standing debt counts down, and this is a
mechanical chore whose whole proof runs without `.env`.

### Measured, 2026-10-03 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Current sizes | `check_worktrees.py` **201**, `retrain_return_model_helpers.py` **200**, `remediation_gate.py` **206** | *[measured 2026-10-03]* `wc -l` at `main` `e31a67d5`; equal to their baseline ceilings, so none has shrunk since the freeze |
| Entries in `LEGACY_MAX_LINES` | **15** | *[measured 2026-10-03]* `scripts/module_size_baseline.py` |
| Importers of `retrain_return_model_helpers` | `scripts/retrain_return_model.py` (140 lines; imports 9 names), `tests/test_retrain_return_model.py` (168 lines; reaches 11 names as `helpers.<name>`, no monkeypatching) | *[measured 2026-10-03]* grep |
| Importers of `scripts/check_worktrees.py` and `scripts/remediation_gate.py` | **none** (run by `make worktrees` and by hand). `orchestration/master_serve.py` imports `agents.master.remediation_gate`, a different module | *[measured 2026-10-03]* grep |
| `remediation_gate.py --check` (fake LLM, $0) | exit **0**: `pass_rate: 1.00`, `regressed: none`, `gained: none`, `VERDICT: PASS` | *[measured 2026-10-03]* `uv run python scripts/remediation_gate.py --check`, main checkout |
| The guard that forces the entry deletion | `tests/test_check_module_size.py::test_every_baselined_path_is_over_the_block_today` fails with `"<name> is <n>; delete its entry"` when a listed file drops under 200 | *[measured 2026-10-03, read]* the test body; *[ASSUMED — not run]* that it goes red on the split, which step 3 below proves |

---

## Scope — and what is deliberately NOT here

1. **Split `check_worktrees.py`.** A natural seam: the git/gh plumbing (`_git_exe`, `_git`, `_root`,
   `_worktrees`, `_is_contained`, `_dirty_count`, `_open_pr_heads`) in one module, the verdict and
   report logic plus `main` in the other. `make worktrees` must keep working.
2. **Split `retrain_return_model_helpers.py`.** A natural seam: the swap trio
   (`candidate_path_for`, `plan_swap`, `execute_swap`) or the formatting helpers
   (`render_comparison_table`, `_format_metric`, `_format_delta`, `_COMPARISON_COLUMNS`) move out.
   The CLI and the test must import every name from the module that defines it. Do not delete or
   weaken any test.
3. **Split `remediation_gate.py`.** A natural seam: the two structured-LLM adapter classes
   (`_AnthropicStructured`, `_OpenAIStructured`), `_build_real_llm` and `_fake` move to a sibling;
   the freeze/check CLI stays.
4. **Delete the three entries** from `LEGACY_MAX_LINES`. Nothing else in that file changes.

### Out of scope (do NOT build this sprint)

- **The other twelve baseline entries.** One chore, three files; the rest stay frozen.
- **Any file outside `scripts/`** except `tests/test_retrain_return_model.py`'s import lines.
- **CLAUDE.md, the work queue, STATE.md.** The planner updates those at merge.
- **No version bump, no `uv.lock` change.** If `uv.lock` changes in your tree, revert it.
- **No re-export shims** that exist only to keep an old import path alive: point the importer at the
  defining module instead. Re-exports are how a split hides a dependency.

### The road not taken (LAW-06)

- **Trim lines to fit (delete blank lines, merge statements).** Rejected: the exact failure
  `chore-split-modules-before-the-block` was written to undo. A file trimmed to 199 is one edit from
  the block again.
- **Raise the ceilings.** Rejected: the baseline's docstring and CLAUDE.md forbid it.
- **Split all fifteen.** Rejected: several are 228–363 lines with real design seams; a bounded
  three-file chore is the right size for a first cloud-session test of the credit.

---

## Blast radius — measured 2026-10-03

| What | Detail |
| --- | --- |
| Files changed | `scripts/check_worktrees.py` 201, `scripts/retrain_return_model_helpers.py` 200, `scripts/remediation_gate.py` 206, `scripts/retrain_return_model.py` 140, `tests/test_retrain_return_model.py` 168, `scripts/module_size_baseline.py` 38; plus three new `scripts/` modules |
| Agents affected | none |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | **none**; no image contains these files |
| Rollback | `git revert` of the merge commit; nothing runs in the fleet, so there is nothing else to undo |

---

## Steps, in order

1. **Read** CLAUDE.md § Module size and the baseline's docstring. Write the reading record.
2. **Record the before-state** in your own tree: `uv run python scripts/remediation_gate.py --check`
   (expect exit 0, PASS) and `uv run python scripts/check_worktrees.py` (any exit; keep the output).
3. **Plant the red first:** split **one** file below 200 **without** deleting its baseline entry,
   run `uv run pytest tests/test_check_module_size.py -q`, and paste the failure naming that file.
4. **Do the three splits**, then delete the three entries.
5. **Prove no behaviour change:** re-run both commands from step 2 in the same tree; the output must
   be byte-identical (`diff` the saved files). `uv run pytest tests/test_retrain_return_model.py -q`
   passes with the same test count as before.
6. **`make ci`** — every step, **redirected to a file, never piped**: `make ci > ci.txt 2>&1; echo $?`.
7. **Push the branch** and fill the handback sections below.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 `make ci`'s module-size step | the three split files, entries deleted | no `[LEGACY]` line for the three files, no block, exit 0 |
| A2 | 🪤 `test_every_baselined_path_is_over_the_block_today` | one file split, entry **kept** | red, naming that file and `delete its entry` (step 3) |
| A3 | `tests/test_retrain_return_model.py` | the split helpers | same test count, all pass, no test edited beyond import lines |
| A4 | `remediation_gate.py --check` before vs after | the split gate | byte-identical output, exit 0 |
| A5 | `check_worktrees.py` before vs after | the split checker | byte-identical output and exit code in the same tree |

---

## Success factors

- [ ] The three files and every new module are under 200 lines, each with the `Agent:` / `Role:` /
  `External I/O:` header.
- [ ] `LEGACY_MAX_LINES` has **12** entries; the three are gone and nothing else changed there.
- [ ] A2 was seen red, then green.
- [ ] A3–A5 show no behaviour change, with the outputs pasted.
- [ ] No re-export shims; no `# noqa` added; no test deleted or weakened.
- [ ] `pyproject.toml` version and `uv.lock` unchanged.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **A file under 200 with its entry still listed fails the gate.** That is the ratchet working, and
it is your red run (A2), not a bug to work around.
🪤 **`check_worktrees.py`'s output depends on the tree's branches.** Compare before and after in the
**same** tree, minutes apart; never compare against the planner's output above.
🪤 **`sys.path` in scripts.** `retrain_return_model.py` inserts the repo root before importing
`scripts.retrain_return_model_helpers`. A new sibling module imported the same way (`from scripts.x
import ...`) works; a bare `import x` works only when run from `scripts/`. Run each script from the
repo root, as `make` does.
🪤 **Do not run `remediation_gate.py --real` or `--freeze`.** `--real` spends money on an LLM and
needs `.env`; `--freeze` rewrites the golden file. Only `--check` is in this chore.

---

## Guardrails (every sprint)

- Every module < 200 lines (warn at 150). Split, don't trim. No `# noqa`.
  📌 Current sizes: `check_worktrees.py` **201**, `retrain_return_model_helpers.py` **200**,
  `remediation_gate.py` **206**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.**
- No version bump, no `uv.lock` change.
- Secrets never through the worktree. **State which tree you ran in.**

---

## Sequencing after merge

1. Branch pushed. **`make gate-ran` is owed to the planner** when the build ran in a cloud session
   (no `gh` there): the planner runs it from a worktree at the branch head and checks the printed SHA.
2. Merge to `main` locally and push. Check `main`'s CodeQL afterwards.
3. **No deploy.**

---

## Handover — paste this into the cloud session

```text
Repo: yury-gurevich/trading-agents, base branch main.

Build the chore in docs/sprints/chore-three-scripts-leave-the-size-baseline.md. Read that whole
file first, and CLAUDE.md.

Task: split three oversize tooling scripts under the 200-line hard block, with no behaviour change:
scripts/check_worktrees.py (201), scripts/retrain_return_model_helpers.py (200),
scripts/remediation_gate.py (206). Then delete exactly those three entries from LEGACY_MAX_LINES in
scripts/module_size_baseline.py (15 -> 12).

Rules:
- Work on branch chore-three-scripts-leave-the-size-baseline (if the environment forces a claude/
  branch name, use it and say so). Never commit to main.
- Red first: split one file without deleting its baseline entry and paste the failure of
  tests/test_check_module_size.py::test_every_baselined_path_is_over_the_block_today.
- Split, never trim. No re-export shims; point importers at the defining module. No # noqa. Every
  new module gets the Agent:/Role:/External I/O: docstring header.
- Touch nothing outside scripts/ except the import lines of tests/test_retrain_return_model.py.
- No version bump and no uv.lock change.
- Prove no behaviour change: save the output of `uv run python scripts/remediation_gate.py --check`
  and `uv run python scripts/check_worktrees.py` before and after in the same tree and diff them.
  NEVER run remediation_gate.py with --real or --freeze.
- Run `make ci > ci.txt 2>&1; echo $?` (never through a pipe) and report the exit code, the pass
  count and the coverage.
- You cannot run `make gate-ran` (no gh); say it is owed. Push the branch.
- Fill the Law reading record, Test plan results, Closeout and Return notes sections at the bottom
  of the spec, set Status to BUILT, commit that with the code, and push.
- If anything contradicts the spec, or a split seems to need a behaviour change, stop and report.
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
| `scripts/check_worktrees.py` + new sibling | `CLAUDE.md` § Module size, § Architecture boundaries; `scripts/check_module_header.py` (what the header step requires) | 200-line hard block / 150 warn, "split, don't trim", no `# noqa` to bypass; header needs `Agent:` + `Role:` (spec also asks `External I/O:`) | **Yes.** The repo's sibling-import idiom in `scripts/` is `if str(_ROOT) not in sys.path: …` followed by `# noqa: E402` imports. The spec forbids adding `# noqa`, so the new imports either use the bare `sys.path.insert(...)` statement form ruff's E402 tolerates (as `retrain_return_model.py` already does) or a function-local import (as `remediation_gate.py` already does). The two pre-existing `# noqa: S603` comments move *with* the subprocess calls they annotate; none is added |
| `scripts/retrain_return_model_helpers.py`, `scripts/retrain_return_model.py`, `tests/test_retrain_return_model.py` | same, plus the spec's "import every name from the module that defines it" / "no re-export shims" | same | **Yes.** Every public name in the helpers module is reached by the test as `helpers.<name>`, so moving any public name forces the test to reach it through the new module — see Return notes for how that was resolved |
| `scripts/remediation_gate.py` + new sibling | same | same; spec trap: `--real` / `--freeze` never run | No — the file already imports lazily inside functions, so the sibling is imported the same way and nothing at module top changes order |
| `scripts/module_size_baseline.py` | its own docstring; `tests/test_check_module_size.py::test_every_baselined_path_is_over_the_block_today` | the list may only shrink; an entry split below 200 **must** be deleted, and the guard test fails until it is | No — it is exactly the red-first step |
| `docs/laws/conventions.md` | §3 Gray → green, §7 Test citation, §10 Tests are local | binds agent law clauses only | No — no agent law book binds `scripts/` tooling; no clause is cited or moved |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **No.** Only
`scripts/` modules move code between files, plus the import lines of one test. Nothing under
`agents/`, `contracts/`, `kernel/`, `orchestration/` or `surfaces/` is touched.

**Contradictions found between a law and this spec:** None between a law and the spec. One internal
tension inside the spec, reported in Return notes: "touch only the import lines of
`tests/test_retrain_return_model.py`" vs. "the test must import every name from the module that
defines it", given the test reaches all its names as `helpers.<name>`.

**Laws found silent where a decision was needed:** None — the split seams are the builder's call by
the spec's own terms.

**Clauses that were ⬜ and are now proven:** None; tooling chore, no law clause in scope.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `make ci` step 5, `scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts` | `Makefile` `ci:` | 🟩 passed — 12 `[LEGACY]` lines, none for the three files; `retrain_return_model_helpers.py` is a `[WARN]` (168), no `[FAIL]`; `make ci` exit 0 | none — tooling, no law clause |
| A2 | `tests/test_check_module_size.py::test_every_baselined_path_is_over_the_block_today` | `tests/test_check_module_size.py` | 🟥 seen red (`check_worktrees.py` split to 128, entry kept), then 🟩 after the three entries were deleted (8 / 8 passed; in `make ci`'s 3,966) | none |
| A3 | `tests/test_retrain_return_model.py` (unchanged 11 tests) | `tests/test_retrain_return_model.py` | 🟩 11 passed before, 11 passed after; no assertion or test body logic edited — one import line added and the module alias changed on 5 call lines (see Return notes) | none |
| A4 | `uv run python scripts/remediation_gate.py --check` before vs after | output files in the session scratchpad | 🟩 byte-identical (sha256 `caf00093…dec551` both), exit 0 both | none |
| A5 | `uv run python scripts/check_worktrees.py` before vs after | output files in the session scratchpad | 🟩 byte-identical (sha256 `03c2e204…a754` both), exit 0 both; **plus** a planted-state diff, below | none |

**Tests added beyond the plan:** No new test file. One extra *proof* beyond A5: the before/after A5
run in this tree only exercises the CLEAN path (one worktree, no merged branches), so I planted
temporary local state — a merged branch with no worktree, a stale clean worktree, a dirty worktree,
an active worktree with a commit not in `main`, and a detached merged worktree — ran the pre-split
`check_worktrees.py` (`git show HEAD:scripts/check_worktrees.py`) and the split one in the same tree,
diffed them (identical, both exit 1), then removed every probe worktree and branch.

---

## Closeout — evidence

**Status:** BUILT 2026-10-03 — branch `chore-three-scripts-leave-the-size-baseline`, cut from the
spec commit `47abd6b` (parent `main` `e31a67d`); not merged.

**Tree the proofs ran in (and `.env` present?):** a claude.ai cloud session, the single checkout
`/home/user/trading-agents` (Linux, Python 3.13.14, uv 0.8.17), on the branch above. **No `.env`.**
Every before/after pair ran in that same tree, minutes apart.

**Result:** the three files are under the block (128 / 112 / 168), each split-off module carries
the `Agent:` / `Role:` / `External I/O:` header, `LEGACY_MAX_LINES` lists **12**, the before/after
outputs are byte-identical, and `make ci` exits 0 at 100.00 %.

**Files changed:**

- `scripts/check_worktrees.py` (201 → 128) and new `scripts/worktree_git.py` (99)
- `scripts/remediation_gate.py` (206 → 112) and new `scripts/remediation_gate_llm.py` (111)
- `scripts/retrain_return_model_helpers.py` (200 → 168) and new `scripts/retrain_return_model_swap.py` (46)
- `scripts/retrain_return_model.py` (140 → 142): its import block only
- `tests/test_retrain_return_model.py` (168 → 169): one import line, and the alias on 5 call lines
- `scripts/module_size_baseline.py` (38 → 35): the three entries deleted, nothing else
- this spec

`pyproject.toml` and `uv.lock`: **untouched** (`git diff` empty for both).

**Split seams chosen:**

- **`check_worktrees.py`** — the git/gh plumbing (`_git_exe`, `_git`, `_root`, `_worktrees`,
  `_is_contained`, `_dirty_count`, `_open_pr_heads` and the two timeout constants) moved to
  `scripts/worktree_git.py` as public names (`git_exe`, `git`, `primary_root`, `worktrees`,
  `is_contained`, `dirty_count`, `open_pr_heads`), because they are now imported across a module
  boundary. `_root` became `primary_root` so `main`'s local `root` cannot shadow it. The verdict and
  report logic, `KEEP_FILE`/`MAIN`/`REMOTE_MAIN` and `main` stay. The script reaches its sibling the
  way `retrain_return_model.py` already does — a bare `sys.path.insert(...)` and then
  `from scripts.worktree_git import ...`, which ruff's E402 accepts without a `# noqa`. The two
  existing `# noqa: S603` comments moved with the `subprocess.run` calls they annotate; none was added.
- **`remediation_gate.py`** — `_AnthropicStructured`, `_OpenAIStructured`, `_fake`, `_response`
  and `_build_real_llm` moved to `scripts/remediation_gate_llm.py` (as `AnthropicStructured`,
  `OpenAIStructured`, `fake`, `build_real_llm`; `_response` stays private there). The gate imports
  them inside `_score`, beside the `agents.master` imports it already deferred there, so nothing at
  module top changes order and `--check` still never imports `scripts.deliberate`. The
  freeze/check CLI, the paths and `main` stay.
- **`retrain_return_model_helpers.py`** — the swap trio (`candidate_path_for`, `plan_swap`,
  `execute_swap`) and `SwapStep` moved to `scripts/retrain_return_model_swap.py`. It was the
  module's only External I/O, so the helpers module is now what its title already claimed — pure
  (`External I/O: none`). `pathlib.Path` became annotation-only there and moved under
  `TYPE_CHECKING` at ruff's request (TC003). The CLI imports the trio from the swap module, the
  rest from helpers. Chosen by the operator in-session over the table seam (see Return notes).

**Proof — the red run first:** (`check_worktrees.py` split to 128, its entry still listed)

```text
$ uv run pytest tests/test_check_module_size.py -q --no-cov -p no:cacheprovider
......F.                                                                 [100%]
=================================== FAILURES ===================================
______________ test_every_baselined_path_is_over_the_block_today _______________
tests/test_check_module_size.py:92: in test_every_baselined_path_is_over_the_block_today
    assert count >= module.FAIL_LIMIT, f"{name} is {count}; delete its entry"
E   AssertionError: scripts/check_worktrees.py is 128; delete its entry
E   assert 128 >= 200
E    +  where 200 = <module 'scripts.check_module_size' from '/home/user/trading-agents/scripts/check_module_size.py'>.FAIL_LIMIT
=========================== short test summary info ============================
FAILED tests/test_check_module_size.py::test_every_baselined_path_is_over_the_block_today
1 failed, 7 passed in 0.28s
exit 1

$ uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
[FAIL] scripts/check_worktrees.py: 128 lines is under the block - delete its entry from scripts/module_size_baseline.py so it cannot grow back.
exit 1
```

Green after the three deletions: `tests/test_check_module_size.py` 8 / 8 passed (run together with
A3: `19 passed in 0.40s`), and the module-size step inside `make ci` passed.

**Proof — no behaviour change (A3–A5):**

```text
# A4 -- before and after, same tree
$ uv run python scripts/remediation_gate.py --check      # exit 0 both times
REMEDIATION SELECTOR GATE
  pass_rate: 1.00
  regressed: none
  gained:    none
  VERDICT: PASS
gate output: IDENTICAL
gate exit: IDENTICAL (gate exit 0)
caf00093192adf9385ff097e6b2f146283dabcdf188f5a429d4921f8b3dec551  gate_before.txt
caf00093192adf9385ff097e6b2f146283dabcdf188f5a429d4921f8b3dec551  gate_after.txt

# A5 -- before and after, same tree
$ uv run python scripts/check_worktrees.py               # exit 0 both times
Worktrees
  - trading-agents: primary

Merged local branches with no worktree
  (none)

Merged remote branches with no open PR
  (none)

Skipped: backup/*, open-PR branches, worktrees in .worktree-keep.

CLEAN - no stale worktrees or merged branches.
wt output: IDENTICAL
wt exit: IDENTICAL (wt exit 0)
03c2e204251d450cecc152e1a39e2395fa7579248cb717739ef1d9277ae8a754  wt_before.txt
03c2e204251d450cecc152e1a39e2395fa7579248cb717739ef1d9277ae8a754  wt_after.txt

# A5, extra -- planted state; pre-split script (git show HEAD:...) vs split script
PLANTED: IDENTICAL
Worktrees
  - trading-agents: primary
  - wt-active [probe-active]: ACTIVE - commits not in main
  - wt-detached [(detached)]: STALE - merged and clean
  - wt-dirty [probe-dirty]: KEEP - 1 uncommitted file(s)
  - wt-stale [probe-stale]: STALE - merged and clean

Merged local branches with no worktree
  - probe-merged

Merged remote branches with no open PR
  (none)

Skipped: backup/*, open-PR branches, worktrees in .worktree-keep.

STALE - 2 worktree(s), 1 local branch(es), 0 remote branch(es).
Remove with: git worktree remove <path> ; git branch -d <name> ;
             git push origin --delete <name>
exit 1
(all probe worktrees and branches removed afterwards; `git worktree list` back to the one checkout)

# A3 -- before (main tree, pre-split) and after
$ uv run pytest tests/test_retrain_return_model.py -q --no-cov
...........                                                              [100%]
11 passed in 0.60s                                   # before
$ uv run pytest tests/test_retrain_return_model.py tests/test_check_module_size.py -q --no-cov
...................                                                      [100%]
19 passed in 0.40s                                   # after: 11 + 8
# and inside make ci: tests/test_retrain_return_model.py ...........  (11)

$ uv run python scripts/retrain_return_model.py --help   # imports resolve from the repo root
help exit 0
```

`remediation_gate.py` was run with `--check` only; `--real` and `--freeze` were never run.

**Module line counts:** `check_worktrees.py` **128**, `worktree_git.py` **99**,
`remediation_gate.py` **112**, `remediation_gate_llm.py` **111**,
`retrain_return_model_helpers.py` **168** (warn band), `retrain_return_model_swap.py` **46**;
importers `retrain_return_model.py` 142, `tests/test_retrain_return_model.py` 169.

**`make ci`:** `make ci > ci.txt 2>&1; echo $?` → **exit 0**, read from `ci.txt` (gitignored), all
15 steps run: ruff, format, mypy, import-linter, module size (12 `[LEGACY]`, 0 `[FAIL]`), module
header, law coverage, PARAM sync, sprint status, markdown links, version scheme, pytest **3,966
passed, 8 skipped, TOTAL 100.00 %** ("Required test coverage of 100.0% reached"), dependency audit
("No unaccepted vulnerabilities; 1 accepted advisory re-checked"), detect-secrets Passed,
untracked secrets Passed (3 new files scanned). Run twice: once on the code alone, and again on the
final tree after the handback, the `BUILT` status and the README/INDEX rows were written. The second
run also exited 0, with 3,966 passed, 8 skipped and 100.00 %. Only this paragraph changed after it, and
`check_sprint_status.py` and `check_markdown_links.py` were re-run on that edit (both exit 0).

**`make gate-ran`:** **owed to the planner** — no `gh` in the cloud container. Remote run results,
if read through the GitHub connector, are an observation, not `GATE PROVEN`.

**Not met / verified failing:**

- **"Aim under 150" not met for `retrain_return_model_helpers.py`: 168** (warn band, 32 under the
  block). The operator chose the swap-only seam in-session; moving the table formatters as well
  would have reached ~120.
- **"Touch only the import lines of `tests/test_retrain_return_model.py`" not met as worded:**
  besides one added import line, 5 call lines changed `helpers.<name>(` to `swap.<name>(`. No
  assertion, fixture, argument or test name changed. Operator-approved; see Return notes.

---

## Return notes

- **Spec tension, resolved by the operator in-session.** The spec said both "the test must import
  every name from the module that defines it" and "touch only the import lines" of the test. The
  test reaches every public helper as `helpers.<name>`, so with re-export shims ruled out, *any*
  public name that moves forces a call-site edit. I stopped and asked; the operator chose the
  swap-trio seam with the alias renamed on the 5 call lines (`candidate_path_for` ×1, `plan_swap`
  ×2, `execute_swap` ×2). The alternatives offered were: swap + table (helpers ~120, 6 call lines),
  only the private formatters (test untouched, helpers ~176), or stop and leave the file frozen.
- **Branch.** Built on `chore-three-scripts-leave-the-size-baseline`, as the operator's handover
  named. The cloud environment had pre-assigned `claude/kind-brown-y5y06d`; it was not used.
- **Base.** The spec commit `47abd6b` was not on `main` (only on the session branch), so this branch
  carries it: its parent chain is `47abd6b` → `main` `e31a67d`.
- **`# noqa` count unchanged.** The two `# noqa: S603` in `worktree_git.py` are the ones that sat on
  the same `subprocess.run` calls in `check_worktrees.py`; moved, not added. The new sibling imports
  avoid the repo's usual `# noqa: E402` by using the bare `sys.path.insert(...)` form
  (`check_worktrees.py`) or a function-local import (`remediation_gate.py`).
- **Names made public** in the three new modules because they now cross a module boundary
  (`_git` → `git`, `_build_real_llm` → `build_real_llm`, etc.). No old name is kept alive anywhere.
- **Owed to the planner:** `make gate-ran` from a worktree at this branch's head (check the printed
  SHA), then the merge. No `uv lock` is owed — no bump and no dependency change. No deploy.
- **For the planner at merge** (CLAUDE.md is out of scope here): CLAUDE.md § Module size still
  says "Those 16 are frozen". The baseline listed 15 before this chore and lists 12 after it.
- **Sprint docs.** Setting this spec to `BUILT` made `check_sprint_status.py` fail until the spec's
  row in `docs/sprints/README.md` agreed, so that row's status cell (and the matching
  `docs/sprints/INDEX.md` cell) now reads BUILT. Nothing else in either file changed.
