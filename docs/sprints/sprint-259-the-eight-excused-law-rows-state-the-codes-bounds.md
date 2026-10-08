<!-- Agent: planning | Role: sprint handover -->
# Sprint 259 — The eight excused law rows state the bounds the code enforces, and the excused list is empty

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-259-the-eight-excused-law-rows-state-the-codes-bounds`
**Status:** MERGED 2026-10-08 — `0.123.04`, fast-forwarded to `49146e40`, tag `v0.123.04`, GATE PROVEN `49146e40` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (4,392 passed, 8 skipped, 100.00 %, dependency audit clean); built by the planner on the operator's word ("tonight"); portfolio manager laws v1.12, scanner v1.5, analyst v1.10 (`PARAM` only, no clause changes); red first, then each of the eight rows put back fails the parameter step; the excused list is empty and a test holds it empty; open CodeQL alerts 127, the same as `main`'s, none new; **F1 PASS** (on the merged `main` the step exits 0 with no excused row, and each row put back makes it exit 1); **deployed `s259a` 2026-10-08**, before the fidelity count's first session, so nothing counted is lost; work-queue 114 closed
**Version:** `0.123.04`
**Effort:** S
**Decisions:** [DL-276](../design-log.md) (D3, D4 and D6, and its amendment of 2026-10-08: why tonight) ·
closes work-queue **114**

> **Why this bump kind.** No new capability. Eight law rows state bounds the code does not have. Three law
> books change, and they ship inside their agents' images, so the retag needs a release tag to build from.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the amendments this spec names |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `drift-register.md` is the one law-adjacent file a builder may append to |

Binding here: the `PARAM` tables of the portfolio manager's, the scanner's and the analyst's books.

### The rule

1. Before any edit, read each book's `PARAM` section, its version line and its Changelog, and every other
   line of the book and of its `test-plan.md` that names one of the eight parameters.
2. **Answer the law-cycle question below.**
3. **Write the Law reading record** (at the bottom) before the first edit.
4. **If a clause states a bound for one of the eight parameters, STOP**: the law then contradicts itself
   and the rewrite is not `PARAM`-only.

### The law-cycle question

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No.** No contract, no code and no clause changes. What is owed is the reconciliation
[DL-276](../design-log.md) D3 decided for all twelve rows and S258 did for four: the law follows the code.
Each of the three books takes its next version, `PARAM`-only, with one Changelog line naming S259 and
DL-276.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/portfolio_manager/laws/laws.md` | the book's `PARAM` table and Changelog; every mention of the six parameters in the book and its `test-plan.md` | Six rows of its `PARAM` table change |
| `agents/scanner/laws/laws.md` | the same, for `min_average_volume` | One row changes |
| `agents/analyst/laws/laws.md` | the same, for `scaled_stop_atr_multiplier` | One row changes |
| `scripts/param_law_sync_excused.py`, `tests/test_param_law_sync_repo.py`, `tests/param_law_sync_helpers.py` | `docs/laws/conventions.md`; DL-276 D4 | The recorded list goes to empty; no agent's book governs the tooling |

🚨 **The three books are fidelity decision paths.** `scripts/replay_fidelity_git.py` counts every file
under `agents/portfolio_manager/`, `agents/scanner/` and `agents/analyst/`. That is why S258 left these
rows, and why this sprint is built on this night and no other (below).

---

## Goal

At merge, no `PARAM` row in any book states bounds the code does not enforce, the excused list is empty,
and a test holds it empty. Deployed before `sched-2026-10-08`, so the fidelity count loses nothing.

## Why (context)

S258 made the parameter step of `make ci` compare every row's bounds with the code. Twelve rows disagreed.
Four were rewritten then. Eight sit in books the fidelity check treats as decision code, so they were
excused by a recorded list, to be rewritten "at the first deploy that restarts the fidelity count". The
operator asked what it takes to clear them, and chose tonight.

**Why tonight costs nothing, and tomorrow would.** The fidelity count restarted with the two deploys of
2026-10-08 and its first session is `sched-2026-10-08`, which has not run. A session is clean when no
decision path differs between the commit that was deployed and the commit the replay runs from. Deployed
before that run, this change is simply part of the code the count starts on. Deployed after it, every
session already counted is on other decision code and is lost. Merged and not deployed, it turns the next
retag, whatever it carries, into one that restarts the count.

### Measured, 2026-10-08 — read these before designing

Everything here was measured in `../ta-s259`, cut from `main` `2b8759ab`, with no `.env`.

| Claim | Value | How it was measured |
| --- | --- | --- |
| The eight rows and the bounds each field enforces | the table below | *[measured]* the built reader over the three books and the settings classes' `model_fields` (`s259_measure.py`) |
| A clause that states a bound for one of the eight | none | *[measured]* every line of the three books and their test plans naming a parameter was read (9 lines outside the tables, none states a bound); the old bound numbers were searched for in clause text, none found |
| When a session is clean | no path under `DECISION_PATHS` differs between the deployed `git_sha` and the replay's `HEAD` | *[measured, read whole]* `scripts/replay_fidelity_git.py`, 99 lines |
| The count's first session | `sched-2026-10-08`, fired at 22:30 UTC; the clock read 10:31 UTC when this was written | *[measured]* the clock; the dispatcher's cron `*/10 22-23 * * 1-5` *[carried from the deploy record of `s240`]* |
| What this branch changes against the fleet's commit `b0831f64`, under the decision paths | the three law books and nothing else | *[measured]* `git diff --name-only b0831f64` over the nine paths |
| What it changes against `v0.123.02` outside `docs/`, `scripts/`, `tests/` and `CLAUDE.md` | four law books (the three, and execution's from S258), `pyproject.toml`, `uv.lock` | *[measured]* `git diff --name-only v0.123.02` |
| Packs, `infra/` and the workflows against `v0.123.02` | no file | *[measured]* the same diff over those paths: an image-only retag |

**The eight rows.**

| Row | Type cell before | The field's bounds | Type cell after |
| --- | --- | --- | --- |
| `portfolio_manager.starting_cash` | `` `Decimal ≥ 0` (USD) `` | `ge=0.0`, `le=1000000000.0` | `` `Decimal ≥ 0, ≤ 1,000,000,000` (USD) `` |
| `portfolio_manager.max_position_pct` | `` `float ≥ 0.01, ≤ 1.0` `` | `ge=0.0`, `le=1.0` | `` `float ≥ 0.0, ≤ 1.0` `` |
| `portfolio_manager.max_positions` | `` `int ≥ 1, ≤ 50` `` | `ge=1`, `le=500` | `` `int ≥ 1, ≤ 500` `` |
| `portfolio_manager.cash_buffer_pct` | `` `float ≥ 0.0, ≤ 0.50` `` | `ge=0.0`, `le=0.95` | `` `float ≥ 0.0, ≤ 0.95` `` |
| `portfolio_manager.min_order_quantity` | `` `int ≥ 1` (shares) `` | `ge=1`, `le=1000000` | `` `int ≥ 1, ≤ 1,000,000` (shares) `` |
| `portfolio_manager.price_lookback_days` | `` `int ≥ 1, ≤ 30` (days) `` | `ge=0`, `le=14` | `` `int ≥ 0, ≤ 14` (days) `` |
| `scanner.min_average_volume` | `` `float ≥ 0` (shares/day) `` | `ge=0.0`, `le=1000000000.0` | `` `float ≥ 0, ≤ 1,000,000,000` (shares/day) `` |
| `analyst.scaled_stop_atr_multiplier` | `` `float` (ratio) `` | `ge=0.0`, `le=5.0` | `` `float ≥ 0.0, ≤ 5.0` (ratio) `` |

---

## Scope — and what is deliberately NOT here

1. **The failing test first**: the repository test expects two warnings and an empty list.
2. **The eight Type cells**, each book's next version and its Changelog line.
3. **The excused list emptied**, with a comment saying when it was and why it stays.
4. **The two law rollups**, the version and the lock.

### Out of scope (do NOT build this sprint)

- **Any settings file, any clause, any Value, Tunable or Rationale cell.**
- **Whether each code bound is the right rail.** The law now says what the code allows: up to 500
  positions, a cash buffer up to 0.95, a single-name cap from 0. Whether those limits are wise is a
  capital-risk question for the operator and, for a code change, a decision path of its own.
- **The excusing mechanism.** It stays (D2).

### The road not taken (LAW-06)

- **Wait for the next deploy that restarts the count anyway, or for the fidelity verdict.** Rejected by
  the operator ("tonight"): the wait is one to three weeks and tonight is free.
- **Merge and not deploy.** Rejected: the next retag would then restart the count, whatever it carried.
- **Remove the excusing mechanism now that the list is empty.** Rejected: its tests still prove it,
  an entry fails the gate the moment its row changes, and the repository test now holds the list empty,
  so a new entry cannot arrive quietly.
- **Change the code's bounds to match the books.** Rejected in DL-276: it changes what a setting may be
  set to, on no evidence, in decision code.

---

## The design decisions — made

| # | Decision | Rejected |
| --- | --- | --- |
| D1 | The eight Type cells become the "after" column of the table above, in each book's own notation, large numbers grouped with commas (the reader reads them; S258 proves it) | scientific notation: harder to read in a law |
| D2 | `EXCUSED_BOUNDS` is an empty mapping and the mechanism stays. `test_the_repo_has_no_param_settings_divergence_left` asserts two warnings, both envelope lines, and that the mapping is empty | deleting the mechanism: see the road not taken |
| D3 | Portfolio manager laws v1.12, scanner v1.5, analyst v1.10, each `PARAM`-only with one Changelog line | |
| D4 | Deployed the same night by an image-only retag, before the 22:30 UTC run; the fidelity worktree is then pinned at the new release | deploying later: costs counted sessions |
| D5 | Work-queue 114 closes when the retag is verified | closing at merge: the debt is paid only if the count is not spent on it |

---

## Blast radius — measured 2026-10-08

| What | Detail |
| --- | --- |
| Files changed | three law books (eight Type cells, three version lines, three Changelog entries); `scripts/param_law_sync_excused.py`; `tests/test_param_law_sync_repo.py`, `tests/param_law_sync_helpers.py`; the two law rollups; `pyproject.toml`, `uv.lock`; sprint documents |
| Agents affected | none at run time: no module of any agent changes |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | **an image-only retag the same night.** The three books are decision paths, so this deploy is where the fidelity count starts; nothing counted is lost because nothing has been counted |
| Rollback | the previous tag, `s257`; the manager's live wait of 240 seconds stays valid on both |

---

## Steps, in order

1. Read the laws (the rule above) and write the Law reading record.
2. Edit the repository test and watch it fail on the unchanged books.
3. Rewrite the eight cells, the three versions and Changelog lines; empty the list.
4. Put each row back, one at a time, and watch the step fail; restore.
5. The rollups, the version, the lock.
6. `make ci`, every step, redirected to a file.
7. Push, `make gate-ran`, the CodeQL comparison, merge, tag, the retag and its checks.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🪤 The repository itself | `check_root` on the repository | No failure; two warnings, both envelope lines; the excused mapping is empty. Red before the rows are rewritten |
| A2 | 🎯 Each rewritten row is held by the gate | Each of the eight cells put back to its old text, one at a time | The step exits 1 and names the row |
| A3 | 🪤 The list cannot be refilled quietly | An entry put back for a reconciled row; then the row and its entry both put back | The first exits 1 and says to delete the entry; the second passes the step with its warning and fails A1 |
| B1 | 🎯 The books changed only where decided | `git diff main` over the three books | Eight Type cells, three version lines, three Changelog entries, nothing else |
| B2 | 🪤 The step's other tests | the 72 other tests of the step | They pass with no edit |

---

## Success factors

- [x] No `PARAM` row states bounds the code does not enforce; the step exits 0 with two warnings (A1).
- [x] Each of the eight rows put back fails the step (A2); the list cannot be refilled quietly (A3).
- [x] No clause, Value, Tunable or Rationale cell, settings file or contract is touched (B1).
- [x] `make ci` exit 0, 100.00 % coverage.
- [x] `GATE PROVEN` for the merged SHA; the retag verified before the run; work-queue 114 closed.

---

## Traps

🪤 **The rows and the list change in one commit.** An entry whose row was rewritten fails the gate, and a
rewritten row whose entry is gone is simply compared: neither half passes alone with the other undone.
🪤 **The symbols are not ASCII.** Read and write the books as UTF-8 with LF endings.
🪤 **A retag after 20:25 UTC lands in the master's window.** Do it before.

---

## Guardrails (every sprint)

- Every module < 200 lines. No `# noqa` added.
- `make ci` **every step** green, **100.00 % coverage floor**, redirected to a file, never piped.
- Secrets never through the worktree. This worktree has **no `.env`**, and nothing here needs one.

---

## Sequencing after merge

1. Merge, the tag.
2. **The retag**, image-only, from the release tag, with a snapshot of every app before and after; the
   three deliberators still on `openai`, the manager's wait still 240 seconds, the two five-minute locks.
3. **F1** on the merged `main`: the step exits 0 with two warnings; one row put back exits 1.
4. The fidelity worktree pinned at the new release; work-queue 114 closed.
5. **F2** is the morning check of `sched-2026-10-08`, already owed for S252 to S257: 8 / 8 on the new tag.

---

## Handover — paste this to Codex

Not handed over. Built by the planner on the operator's word (2026-10-08: asked "What needs to be done to
fix it?", then "tonight"), because the window closes at the night's run.

---

## Handback contract — MANDATORY

The sections below are filled by whoever builds, here the planner, under the same rule as any builder:
state anything not met plainly, and never write a result for work not done.

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Six portfolio-manager rows | `agents/portfolio_manager/laws/laws.md`: the `PARAM` table, the version line, the Changelog's last four entries, and lines 46, 81, 107 and 447, the only other lines naming a parameter; `test-plan.md` lines 19, 30, 31, 52, 53 | None states a bound. Line 107 says an order is an integer of at least `min_order_quantity`, the value, not its rail | No |
| One scanner row | `agents/scanner/laws/laws.md`: the `PARAM` table, the version line, the Changelog; no other line names `min_average_volume` | none | No |
| One analyst row | `agents/analyst/laws/laws.md`: the `PARAM` table, the version line, the Changelog; no other line names `scaled_stop_atr_multiplier` | none | No |
| The excused list and its test | DL-276 (whole); `docs/sprints/sprint-258-…` (whole, at its merge the same day) | DL-276 D4: an entry goes when its row is rewritten | No |

**Not read whole, stated plainly:** the three law books and their test plans. They were read where the
table above says, and searched for every parameter name and for the old bound numbers. The template asks
for the whole file; this sprint edits Type cells only, and the search is what would find a contradiction.

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No.

**Contradictions found between a law and this spec:** none.

**Laws found silent where a decision was needed:** none.

**Clauses that were ⬜ and are now proven:** none.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_the_repo_has_no_param_settings_divergence_left` | `tests/test_param_law_sync_repo.py` | red before the rows were rewritten, PASS after | DRIFT-052 / DL-276 |
| A2 | eight plants, the step run on each | the planner's `s259_plants.py`, outside the repository | 8 of 8 exit 1 naming the row | none: tooling |
| A3 | two plants | the same script | both as expected | none: tooling |
| B1 | `git diff main -- agents` | — | 8 Type cells, 3 version lines, 3 Changelog entries; 22 lines added, 11 removed | — |
| B2 | the step's other 72 tests | `tests/test_param_law_sync*.py` | PASS, no edit | DL-276 |

**Tests added beyond the plan:** none. One existing test edited, deliberately: A1, which had asserted
three warnings and the eight recorded texts. Its helper's copy of those texts is deleted with them.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s259`, the sprint's
branch, cut from `main` `2b8759ab`; no `.env`.

**INTENT (recorded before the edit):** the eight rows state the code's bounds, the list is empty and held
empty by a test, and the change is on the fleet before `sched-2026-10-08`. Success is A1 to B2, `make ci`
exit 0, `GATE PROVEN` for the merged SHA, and a retag that differs from the running fleet in its image tag
alone.

**Result:** built. The step exits 0 on the repository with two warnings and no excused row. Merge, gate
and deploy are recorded in the Status line and in `docs/STATE.md` once done.

**Proof — the red run first:** the test edited, the books and the list untouched.

```text
uv run --no-sync pytest --no-cov -q -p no:cacheprovider tests/test_param_law_sync_repo.py
RED_EXIT=1
tests\test_param_law_sync_repo.py:12: in test_the_repo_has_no_param_settings_divergence_left
    assert len(report.warnings) == 2
E   AssertionError: assert 3 == 2
FAILED tests/test_param_law_sync_repo.py::test_the_repo_has_no_param_settings_divergence_left
1 failed, 1 passed in 17.21s
```

**Proof — the green run:** the step, then its tests.

```text
uv run --no-sync python scripts/check_param_law_sync.py        exit 0
[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 — UCITS investment powers and limits
[WARN] portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later

73 passed in 9.00s
```

**Guards planted:** each restored byte for byte; the tree's diff is the same before and after.

```text
baseline: exit 0, 0 [FAIL], 2 [WARN]
OK  1 portfolio_manager.starting_cash put back: exit 1, 1 [FAIL]
OK  2 portfolio_manager.max_position_pct put back: exit 1, 1 [FAIL]
OK  3 portfolio_manager.max_positions put back: exit 1, 1 [FAIL]
OK  4 portfolio_manager.cash_buffer_pct put back: exit 1, 1 [FAIL]
OK  5 portfolio_manager.min_order_quantity put back: exit 1, 1 [FAIL]
OK  6 portfolio_manager.price_lookback_days put back: exit 1, 1 [FAIL]
OK  7 scanner.min_average_volume put back: exit 1, 1 [FAIL]
OK  8 analyst.scaled_stop_atr_multiplier put back: exit 1, 1 [FAIL]
OK  9 an entry put back for a reconciled row: exit 1, 1 [FAIL]
OK  10 a row AND its entry put back: the step exits 0 with the warning, and the repo test exits 1
restored: step exit 0; repo test exit 0 (2 passed in 4.34s)
RESULT: 12 of 12 as expected
```

**Files changed:** `agents/portfolio_manager/laws/laws.md`, `agents/scanner/laws/laws.md`,
`agents/analyst/laws/laws.md`; `scripts/param_law_sync_excused.py`; `tests/test_param_law_sync_repo.py`,
`tests/param_law_sync_helpers.py`; `docs/laws/INDEX.md`, `docs/laws/ledger.md`; `pyproject.toml`,
`uv.lock` (the version line only, 180 packages before and after); this spec and its two table rows; the
design log.

**`make ci`:** redirected to a file, exit **0**, all 15 steps of the `ci:` target: **4,392 passed, 8 skipped, 100.00 %**, the dependency audit clean ("No unaccepted vulnerabilities; 1 accepted advisory re-checked"), on the tree with `main` `86e38a4d` under it. The parameter step printed the two envelope warnings and no excused line.

**`make gate-ran`:** recorded in the Status line at merge.

**Not met / verified failing:** the three law books were not read whole (the reading record says what
was read). Nothing else.

---

## Return notes

- The version is `0.123.04`: the three books ship in their agents' images, and the retag builds from a
  release tag.
- The law now states limits nobody has reviewed as limits: a book may be set to 500 positions, a cash
  buffer of 0.95, a single-name cap of 0. That is what the code has allowed all along. It is named here so
  the operator can decide whether any of them should be tighter, which would be a code change in decision
  code and its own sprint.

---

## Merge and deploy record — 2026-10-08 22:50 AEDT

**Merge.** `make gate-ran` from `../ta-s259` printed GATE PROVEN for
`49146e40414eb32890a54ac7373ad689013b5866` (CI, CodeQL, Security Findings), the commit `git rev-parse HEAD`
gave. The branch's open CodeQL alerts are the same 127 alert numbers as `main`'s. `main` was fast-forwarded
and tagged `v0.123.04`. **F1** on the merged `main`: the step exits 0 with two warnings and no excused row,
each of the eight rows put back makes it exit 1 and name the row, an entry put back for a reconciled row
fails it, and the tree is clean afterwards.

**Deploy.** Image-only, checked first: the three injected packs hash the same at the fleet's commit
`b0831f64` and at `49146e40`; no file under `infra/`, the packs, the workflows or a Dockerfile differs; and
outside `docs/`, `scripts/` and `tests/` the only differences are four law books and the version line.

The fleet was retagged twice, and the second is the deploy of record.

- **`s259`, 11:09–11:17 UTC.** Build `37767377219`: its first attempt pushed 15 images and failed one job,
  because the scanner image's vulnerability scan could not download its database. The planner re-ran that
  one job, which passed. All 16 apps and the job went to `s259` and matched the before-snapshot, image
  aside; 15 of 15 agent types activated. Then `scripts/record_deploy.py` refused to record it: it proves a
  tag by finding the master image's name in the run's log archive, and after a re-run of one job the
  latest archive holds that job alone ([DL-278](../design-log.md)).
- **`s259a`, 11:34–11:41 UTC (22:34–22:41 AEDT).** A fresh build of the same commit in one attempt, run
  `37770503860`, 15 of 15, under a new tag, because a tag the fleet has pulled is not pushed again. All 16
  apps and `dispatcher-cron` are on `s259a`, every one `Succeeded`, latest revision ready; 0 of 16 apps
  differ from the snapshot taken before it, image aside, and the job differs in its image alone; the three
  deliberators still read `openai`, the manager's wait is still 240 seconds, both debater request
  subscriptions still hold the five-minute lock; 15 of 15 agent types activated on the new images
  (11:35–11:41 UTC) with their credentials passed; 0 Escalations, 0 Faults, 0 Flags; every app back at 0
  replicas. `DeployRecord` written: `deploy:2026-10-08T11:44:42.931500+00:00:s259a:49146e40414eb32890a54ac7373ad689013b5866`. Rollback: `s257`.
- **Seen at both retags, and at the day's two earlier ones:** the master's replica being scaled down was
  killed 31 seconds after its stop (exit code 137). Not a serving replica; filed as work-queue 116.

**What this deploy is for.** The fidelity count's first session is `sched-2026-10-08`. It now starts on
the rewritten books. The fidelity worktree is to be pinned at `v0.123.04`.
