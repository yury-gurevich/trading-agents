<!-- Agent: planning | Role: chore spec + closeout: three frozen oversize scripts split under the block -->
# chore-three-scripts-leave-the-size-baseline — three frozen scripts fit the 200-line block, and the baseline lists twelve

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `chore-three-scripts-leave-the-size-baseline`
**Status:** SPEC
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
| *to fill* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *to fill*

**Contradictions found between a law and this spec:** *to fill*

**Laws found silent where a decision was needed:** *to fill*

**Clauses that were ⬜ and are now proven:** *to fill*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | *to fill* | | | |

**Tests added beyond the plan:** *to fill*

---

## Closeout — evidence

**Status:** *to fill*

**Tree the proofs ran in (and `.env` present?):** *to fill*

**Result:** *to fill*

**Files changed:** *to fill*

**Split seams chosen:** *to fill — per file, what moved where and why*

**Proof — the red run first:**

```text
to fill
```

**Proof — no behaviour change (A3–A5):**

```text
to fill
```

**Module line counts:** *to fill*

**`make ci`:** *to fill — file, exit code, pass count, coverage*

**`make gate-ran`:** *owed to the planner if built in a cloud session*

**Not met / verified failing:** *to fill*

---

## Return notes

- *to fill*
