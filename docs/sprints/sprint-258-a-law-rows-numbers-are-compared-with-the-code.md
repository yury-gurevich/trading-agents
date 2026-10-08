<!-- Agent: planning | Role: sprint handover -->
# Sprint 258 — A law row's default and bounds are compared with the code, and a wrong number fails the gate

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-258-a-law-rows-numbers-are-compared-with-the-code`
**Status:** BUILT
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-276](../design-log.md) (decisions D1 to D6 this sprint builds) · work-queue **114** ·
[DL-275](../design-log.md) (the finding: sprint 257's builder planted an old number and the gate stayed
green)

> **Why this bump kind.** No new capability. A gate that was believed to compare a law row's numbers with
> the code does not, and twelve rows already state bounds the code does not enforce.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the amendments this spec names. A clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding here: the `PARAM` table of the execution book, and the `PARAM` section of
[`docs/laws/_TEMPLATE.md`](../laws/_TEMPLATE.md), which says what the table is for.

### The rule

1. **Before writing code**, read every law file in the map below, whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides what this sprint owes.
5. **Write the Law reading record** (at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row (take the next free number).
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's answer: No.** No file in `contracts/` changes, no agent's code changes, and no agent
promises anything new. What is owed is one reconciliation:

- Four `PARAM` rows of `agents/execution/laws/laws.md` are rewritten to state the bounds the code
  enforces (D3 gives each row). The book's next version, `PARAM`-only, with a Changelog line naming S258
  and DL-276.

Edit no clause, and edit no other law book. Eight more rows disagree with the code; they sit in three
books this sprint must not touch (D4 says why).

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `scripts/param_law_sync*.py`, `scripts/check_param_law_sync.py` | `docs/laws/conventions.md`; the `PARAM` section of `docs/laws/_TEMPLATE.md` (do not edit the template) | The step is the gate for every book's `PARAM` table. No agent's book governs it |
| `agents/execution/laws/laws.md` | the whole book and its `test-plan.md` | Four rows of its `PARAM` table change. No clause of the book governs the table's numbers *[measured, read: `EXEC-DEP-01` to `-04` are the bus, the graph and the broker]*, so this sprint's tests are tests of tooling and cite DL-276, not a clause |

🚨 **Nothing under these paths may change, not a law book, not a test, not a comment:**
`agents/scanner/`, `agents/analyst/`, `agents/portfolio_manager/`, `agents/provider/domain/`,
`agents/execution/order_tolerance.py`, `contracts/`, `orchestration/packs/`,
`orchestration/history_window.py`. They are the fidelity check's decision paths: a changed file under
any of them restarts a count that takes weeks to accumulate. If the suite cannot pass without touching
one, stop and report.

---

## Goal

At merge, the parameter step of `make ci` fails when a `PARAM` row's Value cell differs from the settings
field's default, or when its Type cell states other bounds than the field enforces. The four execution
rows state the code's bounds. Eight named rows are excused by a list that can only get shorter.

## Why (context)

Sprint 257's spec said the parameter step would fail until two law rows followed the code. Its builder
put an old number back in a row and the step stayed green: it compares a row's name and its Tunable cell
and nothing else. Nothing had ever compared the numbers, and they have drifted. A law book is where the
operator reads what rail a setting has; twelve rows state a rail the code does not have.

### Measured, 2026-10-08 — read these before designing

Everything here was measured in a worktree with no `.env`, at `main` `60a19e29`. The prototype is on no
branch.

| Claim | Value | How it was measured |
| --- | --- | --- |
| What the step compares today | a row's name against the settings fields, and its Tunable cell against whether the field is a `tunable()`. `ParamRow` holds `name`, `tunable`, `location` | *[measured, read and run]* `scripts/param_law_sync_sources.py`, `scripts/param_law_sync.py`; with the deliberator's `max_tokens` row put back to `8192` the step exits 0 |
| Books and rows | 16 books, **235** rows that have a settings field | *[measured]* the step's own readers over the tree |
| How Value cells are written | 177 in backticks, 45 in backticks and double quotes, 9 a dash (`—`), 4 the bare word `empty`. One reads `` `Decimal("100000.00")` `` | *[measured]* every row |
| What the defaults are | 102 `int`, 66 `str`, 57 `float`, 5 `Decimal`, 2 `None`, 2 `bool`, 1 `date`. No field is required and none has a default factory | *[measured]* `model_fields` of the 16 settings classes |
| Value cells against defaults | **235 of 235 agree** under the reading rules of D1. A dash stands for a secret whose default is `None` (2) or `""` (7); `empty` stands for `""` | *[measured]* the prototype prints no Value failure |
| How bounds are written | `≥` and `≤`, `>=` and `<=`, `>`, `<`, and intervals such as `[0.0, 1.0]` and `(0, 1]`, with units and words around them (`int days [1, 60]`, `float ∈ (0, 1]`, `` `int ≥ 1` (shares) ``) | *[measured]* every Type cell |
| Type cells against the code's bounds | 164 rows have a bound in code. **152** state the same bounds. **8** state a different number or strictness, **3** state one side where the code has two, **1** states none. 71 rows have no bound on either side. No row states a bound the code lacks | *[measured]* every row; the twelve are listed below |
| The step on today's books, with the prototype | exit 1; four `[FAIL]` lines, the four execution rows; one `[WARN]` line naming the eight excused rows; the two envelope warnings as before | *[measured]* |
| With the four execution rows rewritten (D3) | exit 0 | *[measured]* |
| Six wrong rows planted one at a time | each exits 1 and names the row: a Value back at `8192`; an upper bound back at `8192`; a bound dropped; a string default changed; an excused row edited and still wrong (two lines: the row, and its list entry); an excused row reconciled with its entry left behind | *[measured]* restored after each, exit 0 |
| Printing a law's symbols on Windows | `print("int ≥ 1")` raises `UnicodeEncodeError` when stdout is redirected: the encoding is `cp1252`. `make ci` is always run redirected | *[measured]* this machine, Python 3.13 |
| The prototype against the whole suite | with the four execution rows rewritten, **exactly one existing test fails** (4,329 pass, 8 skipped): `tests/test_param_law_sync_repo.py::test_the_repo_has_no_param_settings_divergence_left`, which pins the number of warnings at two; the prototype adds the line for the excused rows. `scripts/gate_selftest.py` passes 31 of 31 | *[measured]* a throwaway worktree at `60a19e29` |
| Module sizes | `scripts/param_law_sync.py` **197**, `scripts/param_law_sync_sources.py` **153**, `scripts/param_law_sync_envelopes.py` 37, `scripts/check_param_law_sync.py` 29. The prototype put its wiring in `param_law_sync.py` and reached 228: over the block | *[measured]* `wc -l` |
| `scripts/gate_selftest_cases.py` | 346 lines, frozen at that size in `scripts/module_size_baseline.py`: it may shrink, never grow | *[measured, read]* |
| The code's bound is the intended rail for each of the twelve rows | *[ASSUMED]* The tunables' `why` texts were read and none says which side is right. The code's bound is the one that has run | D3 decides it; a rail that looks wrong is a drift-register row, not a code change here |

**The twelve rows.** Law text as written today, and the bounds the field has.

| Row | Type cell today | The field's bounds | This sprint |
| --- | --- | --- | --- |
| `execution.slippage_bps` | `` `int ≥ 0, ≤ 100` (basis points) `` | `ge=0`, `le=1000` | rewritten (D3) |
| `execution.min_promotion_runs` | `` `int ≥ 1` `` | `ge=3`, `le=200` | rewritten (D3) |
| `execution.min_approval_rate` | `` `float ∈ (0, 1]` `` | `ge=0.0`, `le=1.0` | rewritten (D3) |
| `execution.alpaca_timeout` | `` `int ≥ 1, ≤ 120` (seconds) `` | `ge=1`, `le=60` | rewritten (D3) |
| `portfolio_manager.starting_cash` | `` `Decimal ≥ 0` (USD) `` | `ge=0.0`, `le=1000000000.0` | excused (D4) |
| `portfolio_manager.max_position_pct` | `` `float ≥ 0.01, ≤ 1.0` `` | `ge=0.0`, `le=1.0` | excused (D4) |
| `portfolio_manager.max_positions` | `` `int ≥ 1, ≤ 50` `` | `ge=1`, `le=500` | excused (D4) |
| `portfolio_manager.cash_buffer_pct` | `` `float ≥ 0.0, ≤ 0.50` `` | `ge=0.0`, `le=0.95` | excused (D4) |
| `portfolio_manager.min_order_quantity` | `` `int ≥ 1` (shares) `` | `ge=1`, `le=1000000` | excused (D4) |
| `portfolio_manager.price_lookback_days` | `` `int ≥ 1, ≤ 30` (days) `` | `ge=0`, `le=14` | excused (D4) |
| `scanner.min_average_volume` | `` `float ≥ 0` (shares/day) `` | `ge=0.0`, `le=1000000000.0` | excused (D4) |
| `analyst.scaled_stop_atr_multiplier` | `` `float` (ratio) `` | `ge=0.0`, `le=5.0` | excused (D4) |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first (A1, A4, A5, A7).**
2. **The step reads a row's Value and Type cells** and compares them with the field (D1, D2).
3. **The excused list** (D4): eight entries, exactly as given, in a module of its own.
4. **The four execution rows** (D3), the book's next version and its Changelog line.
5. **Output that cannot crash** on a console without the laws' symbols (D5).

### Out of scope (do NOT build this sprint)

- **Any file under a fidelity decision path** (the list under the MUST RULE). That includes the three
  books holding the eight excused rows.
- **Any settings file.** No default and no bound changes in code.
- **`scripts/gate_selftest_cases.py`.** It is frozen at its size. The unit tests plant the wrong numbers.
- **`docs/laws/_TEMPLATE.md`, `docs/laws/INDEX.md`, `docs/laws/ledger.md`.** The planner moves the
  execution book's label in the two rollups at merge.
- **The Rationale cell** against the tunable's `why`, **the members** of a `Literal` or an enum in a Type
  cell, and **units**. Not compared.
- **`pyproject.toml` and `uv.lock`.** The planner bumps the version at merge.
- **The merge and the push.** Commit on the branch and hand back.

### The road not taken (LAW-06)

- **Rewrite all twelve rows now.** Rejected: eight sit in books under the fidelity check's decision paths
  (`scripts/replay_fidelity_git.py` counts every file under those directories, a law book included). The
  count restarted on 2026-10-08 and needs four clean sessions and ten judged recommendations.
- **Teach the fidelity check to ignore law books.** Rejected: it narrows a rule that was fixed before its
  result was known ([DL-237](../design-log.md)).
- **Change the code's bounds to match the books.** Rejected: that changes what a setting may be set to,
  on no evidence, and eight of the fields are under the same decision paths.
- **Compare only the bounds a row states.** Rejected: three rows state one side of two. A rail nobody
  wrote down is the defect this sprint exists for.
- **Warn and stay green.** Rejected: the queue's item 33 removed a warning baseline for 57 divergences
  because accepted debt that only a list knows about is not seen. The excused list here fails the gate
  the moment a row changes.
- **A case in the gate self-test.** Rejected for this sprint: the file is frozen at 346 lines, and
  splitting it is a chore of its own.

---

## The design decisions — made, and recorded in DL-276

**Build them as written.** Record in `docs/design-log.md` (take the next free number) only a decision the
spec did not make, or a place where you had to depart from one of these, with the reason.

| # | Decision | Rejected |
| --- | --- | --- |
| D1 | **The Value cell is compared with the field's default, for every row that has a settings field.** Reading rules, after surrounding backticks are removed: a dash (`-`, `—`, `–`) agrees with `None` and with `""` and with nothing else; `Decimal("x")` reads as `x`; a `bool` default is `true` or `false` in any case; an `int`, `float` or `Decimal` default is compared as a decimal number, so `0.10` agrees with `Decimal("0.10")` and with `0.1`, and `,` or `_` may group digits; a `date` default is its ISO form; a `str` default may be written with or without double quotes, and the bare word `empty` agrees with `""`; a `None` default agrees with `none`, `null`, `unset` or `empty`. **A cell that cannot be read against its default's type is a failure, not a skip** | skipping what cannot be read: a silent skip is how this gap lasted |
| D2 | **The Type cell's bounds are compared with the field's.** Read every notation the books use: `>=` and `≥` (inclusive lower), `>` (exclusive lower), `<=` and `≤` (inclusive upper), `<` (exclusive upper), and an interval with `[` or `(` on the left and `]` or `)` on the right. The bounds stated must be the same set the field has (`ge`, `gt`, `le`, `lt` from its metadata), each number equal as a decimal. A row with no bound on either side passes | comparing only what a row states: see the road not taken |
| D3 | **For the twelve rows the law follows the code.** No settings file changes. The four execution rows become, in the book's own notation: `` `int ≥ 0, ≤ 1000` (basis points) `` for `slippage_bps`; `` `int ≥ 3, ≤ 200` `` for `min_promotion_runs`; `` `float ≥ 0.0, ≤ 1.0` `` for `min_approval_rate`; `` `int ≥ 1, ≤ 60` (seconds) `` for `alpaca_timeout`. Value, Tunable and Rationale cells are unchanged | changing the code: see the road not taken |
| D4 | **Eight rows are excused by a list that can only get shorter.** A mapping from `agent.name` to the row's Type cell exactly as written today, in a module of its own, with a comment saying why (fidelity decision paths) and when an entry goes (the first deploy that restarts the fidelity count, or after DL-237's verdict). An entry excuses a bounds disagreement only, and only while the Type cell equals the recorded text. An entry whose row agrees with the code, or whose cell was edited, is itself a failure that says to delete it. Entries are judged only for books present under the root being checked, so a test's temporary root is not affected. The eight keys and texts are the eight "excused" rows of the table above, byte for byte | a count instead of the texts: it would excuse a different eight |
| D5 | **Output.** One `[FAIL]` line for each disagreement, in the step's existing form (`path:line: agent.name …`), saying what the law states and what the code has. One `[WARN]` line naming every excused row that was used. The exit code is 1 on any failure, as today. **No line may raise on a console that cannot encode a law's symbols**: on a `cp1252` stream a failing row whose Type cell holds `≥` or `∈` still prints, with the symbol replaced, and the step still exits 1 | printing through plain `print`: measured to crash on Windows |
| D6 | The planner's: work-queue 114 stays open for the eight rows. Nothing to build | |

---

## Blast radius — measured 2026-10-08

| What | Detail |
| --- | --- |
| Files changed | `scripts/param_law_sync.py` **197**, `scripts/param_law_sync_sources.py` **153**, `scripts/check_param_law_sync.py` 29, new modules beside them; `agents/execution/laws/laws.md` (four rows, the version, one Changelog line); tests |
| Agents affected | none at run time. No agent module changes |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | none: `scripts/` ships in no image, and `agents/execution/laws/laws.md` is not a fidelity decision path |
| Rollback | revert the commit |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Plant the failing tests first** (A1, A4, A5, A7) and watch them fail. Paste the red output.
3. **Implement** D1, D2, D4 and D5.
4. **Rewrite the four execution rows** (D3), the book's version and its Changelog line.
5. **Prove the guards can fail (DL-70):** break each guarded property, watch the guard go red, restore.
6. **`make ci`**, every step of the `ci:` target, **redirected to a file, never piped**. Name any step
   your sandbox cannot run as NOT RUN.
7. **Fill the handback sections** at the bottom of this file and set Status to `BUILT`, here and in
   this sprint's `README.md` row.

---

## Test plan

Every test builds its own small book and settings class in a temporary root, as
`tests/test_param_law_sync.py` does, unless the row says otherwise.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A Value cell that differs from the default fails | A tunable with default `16384` and a row stating `` `8192` `` | Exit 1; the line names the row, the law's value and the code's default. With `` `16384` `` it exits 0 |
| A2 | 🎯 Every way the books write a value is read | One case for each form in D1: a number in backticks; `0.10` against a `Decimal` default; `` `Decimal("100000.00")` ``; a string with and without double quotes; `empty`; a dash against `None` and against `""`; `true` and `false`; a date | Each agrees and exits 0; each with a different value exits 1 |
| A3 | 🪤 A value that cannot be read is a failure, not a skip | A number field whose row states words; a dash against a default of `5` | Exit 1, and the line says the cell could not be compared |
| A4 | 🎯 Every way the books write a bound is read | A field with `ge` and `le`, and its row in each notation of D2, with units and words around it; `gt` and `lt` fields against `>`, `<` and the four interval shapes | Each agrees and exits 0; one number changed exits 1; `(0, 1]` against `ge=0` exits 1 |
| A5 | 🪤 A missing side and an extra side both fail | A field with `ge` and `le` and a row stating the lower bound alone; a row stating no bound; a field with no bound and a row stating one | Each exits 1. A field and a row with no bound exit 0 |
| A6 | 🎯 The excused list excuses exactly what it records | A temporary root with a book and a mapping patched in for the test: the row as recorded; the row edited and still wrong; the row reconciled; an entry for a book the root does not have | Recorded: exit 0 and one `[WARN]` line naming it. Edited: exit 1, the row and the entry both named. Reconciled: exit 1, the entry named. Absent book: ignored |
| A7 | 🪤 The repository itself | `check_root` on the repository | No failure; the warnings are the two envelope lines and one line naming exactly the eight rows; the list's keys are exactly those eight |
| A8 | 🪤 A failing row prints on a console without its symbols | The command's `main` with stdout replaced by a `cp1252` text stream, and a failing row whose Type cell holds `≥` | No exception; exit 1; the row's name is in the output |
| B1 | 🎯 The four execution rows state the code's bounds | `agents/execution/laws/laws.md` | The four rows read as D3 gives them; `git diff main` over the book shows those four rows, the version line and the Changelog line and nothing else |
| B2 | 🪤 The existing tests of the step | `tests/test_param_law_sync.py`, `tests/test_param_law_sync_component_books.py`, and `test_a_repo_divergence_fails_rather_than_warns` in `tests/test_param_law_sync_repo.py` | They pass with no edit. `scripts/gate_selftest.py` still passes every case; if your sandbox cannot run it, name it NOT RUN (the remote gate runs it) |

No test may skip when a dependency is missing. A skipped proof is not a proof.

---

## Success factors

- [x] A Value cell that differs from the default fails the step (A1), in every form the books use (A2),
      and an unreadable one fails too (A3).
- [x] A Type cell whose bounds differ from the field's fails the step, in every notation (A4), with a
      side missing or extra (A5).
- [x] The excused list holds exactly the eight rows, excuses only what it records, and an entry that is
      no longer needed fails the step (A6, A7).
- [x] The step never raises on a `cp1252` console (A8).
- [x] The four execution rows state the code's bounds; no clause is edited (B1).
- [x] Nothing under a fidelity decision path, no settings file, `pyproject.toml`, `uv.lock` or
      `scripts/gate_selftest_cases.py` is touched.
- [x] Every new guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module < 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage, or each step that could not run named as NOT RUN.

---

## Traps

🪤 **`scripts/param_law_sync.py` is at 197 lines.** The comparison and the excused list go in new modules;
the prototype that wired them into that file reached 228. Move code out before adding any.
🪤 **One existing test pins the old output.** Measured on the prototype; it needs a deliberate edit, named
in the handback with its reason. Any other is a finding: name it.

- `tests/test_param_law_sync_repo.py::test_the_repo_has_no_param_settings_divergence_left`: asserts two
  warnings, both envelope lines. It becomes A7. Its docstring says "none is baselined": that stays true
  of names and Tunable cells, and is no longer true of bounds, so the docstring must say what holds now.

The other test in that file, and every test in `tests/test_param_law_sync.py` and
`tests/test_param_law_sync_component_books.py`, passed on the prototype with no edit (B2).
🪤 **The symbols are not ASCII.** The eight recorded texts hold `≥` and `≤`. Read and write every file as
UTF-8 with LF endings, and compare text, not bytes of another encoding. Do not "normalise" a recorded
text: the entry excuses the row only while it matches the book character for character.
🪤 **A number inside a type is not a bound.** `Literal[...]` and `dict[str, float]` hold brackets and
commas. No row today reads as an interval by accident; keep it so (A7 would show it).
🪤 **Compare as decimals.** `Decimal(str(0.1))` equals `Decimal("0.10")`; `float("0.10") == 0.1` is not the
comparison to rely on for `1e9` against `1000000000.0`.
🪤 **A worktree has no `.env`**, and the settings classes read one if present. Read defaults from
`model_fields`, as the step does today; do not instantiate a settings class.
🪤 **The planner's earlier numbers were wrong.** DL-275's amendment said 41 stated bounds, all equal. It
read one notation of four. This spec's table replaces it.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` beyond the import-order ones the
  step's entrypoint already carries.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `kernel.tunable(..., why=...)` with bounds. This sprint adds no tunable.
- Faults, not silent failure.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Secrets never through the worktree. A worktree has **no `.env`**, and nothing here needs one.
  **State which tree you ran in.**

---

## Sequencing after merge

Owed by the planner, in this order:

1. **Before the handover:** the worktree `../ta-s258` cut from `main` and its venv synced.
2. Review against the checklist; the planner's own plants; the PATCH bump and `uv lock`; the execution
   book's label in the two law rollups; Windows `make ci`, all steps; push the branch; **`make gate-ran`
   exits 0** from the worktree whose `HEAD` is the commit being proven; the branch's open CodeQL alerts
   compared with `main`'s.
3. Merge, the tag.
4. **F1, no cost.** On the merged `main`: the step exits 0; with one real row's Value changed and with one
   real row's bound changed it exits 1 and names the row; restored.
5. **No deploy.** `scripts/` ships in no image.
6. **The eight rows** are rewritten, and their entries deleted, at the first deploy that restarts the
   fidelity count or after DL-237's verdict (work-queue 114).

---

## Handover — paste this to Codex

```text
Sprint 258 — a law row's default and bounds are compared with the code, and a wrong number fails the
gate. Spec: docs/sprints/sprint-258-a-law-rows-numbers-are-compared-with-the-code.md (read ALL of it,
then CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s258, on branch
sprint-258-a-law-rows-numbers-are-compared-with-the-code, cut from main, with its venv synced to the
lock. Work only there, never in the main checkout and never on main. You have no .env and no network:
every proof is a unit test. `uv run` is safe. Do not touch pyproject.toml or uv.lock, and say so: the
planner bumps the version at merge. Do not push and do not merge: commit on the branch and hand back. Do
not edit docs/STATE.md: put intent and results in the spec's Closeout. If a make ci step cannot run in
your sandbox (the dependency audit needs the network), do not bypass it silently: name the step as NOT
RUN in the handback.

This handover is complete: nobody will send you follow-up messages. Two tiers:
- A wrong command, count, path, test name or clause number whose intent is plain from the spec's Scope
  and Success factors is NOT a reason to stop: follow the intent, record the correction in Return
  notes, continue. An existing test that must change because the step now compares numbers is the same
  tier: edit it, and name it with the reason.
- STOP and report, without improvising, when: the suite cannot pass without changing a file under
  agents/scanner/, agents/analyst/, agents/portfolio_manager/, agents/provider/domain/, contracts/,
  orchestration/packs/, orchestration/history_window.py or agents/execution/order_tolerance.py; a
  settings file would have to change; a row outside the twelve the spec lists disagrees with the code;
  or one of the eight recorded texts does not match its book.

What and why: the parameter step of make ci (scripts/check_param_law_sync.py) compares a PARAM row's
name and its Tunable cell with the settings and nothing else. Sprint 257's builder put an old number
back in a row and the step stayed green. The planner then read every row: all 235 Value cells agree
with the code's default, and twelve Type cells state bounds the code does not enforce. Four of those are
in the execution book and are rewritten here. Eight are in books under the fidelity check's decision
paths, which this sprint may not touch, so they are excused by a recorded list that can only get
shorter.

MUST RULE before any code: read, whole, agents/execution/laws/laws.md and its test-plan.md,
docs/laws/conventions.md, docs/laws/drift-register.md, the PARAM section of docs/laws/_TEMPLATE.md, and
DL-276 and DL-275 in docs/design-log.md. Fill the Law reading record first. Law-cycle answer: NO. No
contracts/ file and no new guarantee. Owed: four PARAM rows of the execution book follow the code, the
book's next version, one Changelog line naming S258 and DL-276. Edit no clause and no other law book.

Order (the spec's Steps): laws -> plant A1, A4, A5 and A7, watch them fail, paste the red -> implement
-> the four execution rows -> break and restore every guard -> make ci to a file.

Build (decisions D1-D5 are made; build them as written):
1. The step reads each row's Value and Type cells and compares them with the settings field: the
   default by the reading rules of D1, the bounds by D2. An unreadable value is a failure.
2. The excused list of D4 in a module of its own: the eight keys and Type-cell texts from the spec's
   table of twelve rows, byte for byte.
3. Output by D5, safe on a cp1252 console.
4. agents/execution/laws/laws.md: the four rows as D3 gives them, the version, the Changelog line.
5. Tests A1-A8, B1 and B2 from the spec's Test plan.
scripts/param_law_sync.py is at 197 lines of 200: put the new code in new modules.

DO NOT: change any settings file; change anything under the eight decision paths named above; edit
scripts/gate_selftest_cases.py, docs/laws/_TEMPLATE.md, docs/laws/INDEX.md or docs/laws/ledger.md;
teach the fidelity check anything; make a disagreement a warning; skip a value the step cannot read;
pin a version number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The red output of A1, A4, A5 and A7 pasted, from before the implementation.
 3. Test plan results: one row for each of A1-A8, B1 and B2, with file and status.
 4. Every guard's break-and-restore stated, one line per guard.
 5. The step's output on the built tree pasted whole: exit 0, the two envelope warnings and one line
    naming exactly the eight excused rows.
 6. The four execution rows as they now read, the Changelog line, and the book's version; no clause
    edited.
 7. This prints nothing, and you say so:
    git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration/packs orchestration/history_window.py pyproject.toml uv.lock scripts/gate_selftest_cases.py docs/laws/_TEMPLATE.md
    and so does:  git diff main --stat -- 'agents/*/settings*.py' orchestration/settings.py surfaces/dashboard/settings.py
 8. Every EXISTING test you edited, named, with the reason for each edit.
 9. make ci output file named, exit code stated, every NOT RUN step named with its reason.
10. Module line counts for every touched or new module; Status BUILT here and in the README row.
State anything not met as "not done" or "verified failing". Never write a Result for work not done.
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
| PARAM checker and its tests | `docs/laws/conventions.md` (whole); `docs/laws/_TEMPLATE.md` PARAM section; `docs/laws/drift-register.md` (whole); DL-276 and DL-275 in `docs/design-log.md` | Conventions sections 2, 3, 4, 7 and 9; template PARAM; DL-276 D1-D5. No agent clause governs this tooling | Read before code, 2026-10-08. Compare defaults and the complete bounds set; unreadable values fail. Tooling tests cite DL-276, not an invented clause |
| Execution PARAM reconciliation | `agents/execution/laws/laws.md` (whole, LOCKED v1.12); `agents/execution/laws/test-plan.md` (whole) | Conventions section 4 and DL-276 D3 authorize four PARAM Type cells, v1.13 and one Changelog line. EXEC-DEP-01 through EXEC-DEP-04 describe bus, graph and broker dependencies, not PARAM numbers | No change to the planned scope. No clause, Value, Tunable or Rationale cell changes; no runtime or live-dependency proof claimed |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** NO. No contract file or new agent guarantee. Owed: four execution PARAM Type cells following D3, next book version v1.13, and one Changelog line naming S258 and DL-276.

**Contradictions found between a law and this spec:** none. The scoped PARAM discrepancies are already decided by DL-276. AGENTS.md's 14-step count disagrees with CLAUDE.md's 15-step count; CLAUDE.md wins, and the actual target will be counted (Return notes).

**Laws found silent where a decision was needed:** none; D1-D5 decide the tooling behavior, and no agent clause is required for it.

**Clauses that were ⬜ and are now proven:** none. Existing gray execution clauses remain unproven; the sprint relies on no gray clause for numeric comparisons.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a_wrong_value_names_the_law_and_code_and_fails` | `tests/test_param_law_sync_values.py` | PASS (1 case) | DL-276 |
| A2 | `test_every_value_form_compares_the_default` | `tests/test_param_law_sync_values.py` | PASS (24 cases) | DL-276 |
| A3 | `test_unreadable_values_fail_instead_of_skipping` | `tests/test_param_law_sync_values.py` | PASS (8 cases) | DL-276 |
| A4 | `test_every_bound_notation_compares_numbers`; `test_exclusive_lower_bound_is_not_inclusive`; `test_units_and_grouped_decimal_bounds`; `test_numeric_literal_members_are_not_an_interval` | `tests/test_param_law_sync_bounds.py` | PASS (13 cases) | DL-276 |
| A5 | `test_missing_or_extra_bounds_fail`; `test_no_bounds_on_either_side_passes` | `tests/test_param_law_sync_bounds.py` | PASS (4 cases) | DL-276 |
| A6 | `test_an_excuse_requires_its_exact_still_wrong_text`; `test_an_excuse_never_excuses_a_wrong_value`; `test_an_excuse_fails_when_code_catches_up_without_a_cell_edit`; `test_an_absent_book_is_not_judged`; `test_an_entry_for_a_missing_field_in_a_present_book_fails` | `tests/test_param_law_sync_excused.py` | PASS (8 cases) | DL-276 |
| A7 | `test_the_repo_has_no_param_settings_divergence_left` | `tests/test_param_law_sync_repo.py` | PASS (1 case; exact eight keys/texts and three warnings) | DRIFT-052 / DL-276 |
| A8 | `test_a_failing_symbolic_row_prints_on_cp1252`; `test_a_warning_prints_on_cp1252`; `test_a_stream_without_encoding_keeps_the_symbols` | `tests/test_param_law_sync_output.py` | PASS (3 cases) | DL-276 |
| B1 | `test_the_four_execution_rows_state_the_decided_bounds`; local `git diff main -- agents/execution/laws/laws.md` | `tests/test_param_law_sync_execution_rows.py`; execution book | PASS (1 case; diff contains only four Type cells, version and one Changelog line) | DL-276 |
| B2 | All eight original step tests; `test_surfaces_book_syncs_against_mapped_dashboard_settings`; `test_a_repo_divergence_fails_rather_than_warns` | `tests/test_param_law_sync.py`; `tests/test_param_law_sync_component_books.py`; `tests/test_param_law_sync_repo.py` | PASS (10 cases, no edits). Gate self-test: 30/31 PASS; live CVE case NOT RUN (network) | Existing DD-04 / DRIFT-052 citations unchanged |

**Tests added beyond the plan:** none outside A1-A8/B1. Within-plan extensions cover non-finite and unsupported defaults, grouped/scientific bounds, numeric Literal members, present-book missing entries, code-only reconciliation, warning output and encoding-less stdout. The plan accounts for all 73 step tests; none is skipped.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s258`, branch `sprint-258-a-law-rows-numbers-are-compared-with-the-code`; `.env` absent (`Test-Path .env`: `False`). Initial worktree clean; HEAD, main and origin/main all `8d55cb569b01680ca583b52d25adecf742a87802`. Only this worktree is used.

**INTENT (recorded before code):** Implement DL-276 D1-D5 within the listed scripts/tests and four execution PARAM Type cells. First prove A1/A4/A5/A7 red and paste that evidence; then complete A1-A8/B1/B2, break and restore each guard, and redirect `make ci` to `.tools/s258/ci.txt`. Every touched module stays below 200 lines. No network, settings, fidelity decision paths, contracts, other law books, version files, STATE, push or merge. A network-dependent CI step is named NOT RUN, never presented as green.

**Result:** BUILT and locally unit-proven. D1-D5 implemented; all 235 defaults agree, the four execution Type cells agree, and exactly eight recorded bounds disagreements are excused. All 73 step tests passed inside the full suite: 4,392 passed, eight existing skips, 100.00% configured coverage. All 19 final guard mutations rejected and restored byte for byte. Full CI is NOT green: its dependency audit is NOT RUN offline.

**Files changed:** `agents/execution/laws/laws.md`; this spec and `docs/sprints/README.md`; `scripts/check_param_law_sync.py`; `scripts/param_law_sync.py`; `scripts/param_law_sync_bounds.py`; `scripts/param_law_sync_excused.py`; `scripts/param_law_sync_numbers.py`; `scripts/param_law_sync_output.py`; `scripts/param_law_sync_sources.py`; `scripts/param_law_sync_types.py`; `scripts/param_law_sync_values.py`; `tests/param_law_sync_helpers.py`; `tests/test_param_law_sync_bounds.py`; `tests/test_param_law_sync_excused.py`; `tests/test_param_law_sync_execution_rows.py`; `tests/test_param_law_sync_output.py`; `tests/test_param_law_sync_repo.py`; `tests/test_param_law_sync_values.py`. Ignored evidence and offline launch helpers live only in `.tools/s258/`.

**Design decisions:** DL-276 D1-D5 built as written; no new design question or departure. Shared report types were moved to their own module so `param_law_sync.py` is 190 lines. No settings, contracts, runtime decisions, law clauses or other law books changed. The rejected alternatives remain recorded in this spec and DL-276.

**Proof — the red run first:** Before implementation, after fixing the synthetic `lt` fixture (initial run preserved in `.tools/s258/red-initial.txt`):

```text
uv run pytest --no-cov -q tests/test_param_law_sync_values.py tests/test_param_law_sync_bounds.py tests/test_param_law_sync_repo.py::test_the_repo_has_no_param_settings_divergence_left
RED_EXIT=1
FFFFFFFFFFFF.F                                                           [100%]
================================== FAILURES ===================================
_____________ test_a_wrong_value_names_the_law_and_code_and_fails _____________
tests\test_param_law_sync_values.py:15: in test_a_wrong_value_names_the_law_and_code_and_fails
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_a_wrong_value_names_the_l0'])
_ test_every_bound_notation_compares_numbers[`float \u2265 0, \u2264 1` (ratio)-, ge=0, le=1] _
tests\test_param_law_sync_bounds.py:38: in test_every_bound_notation_compares_numbers
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_every_bound_notation_comp0'])
_ test_every_bound_notation_compares_numbers[float >= 0, <= 1 seconds-, ge=0, le=1] _
tests\test_param_law_sync_bounds.py:38: in test_every_bound_notation_compares_numbers
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_every_bound_notation_comp1'])
__ test_every_bound_notation_compares_numbers[`float > 0, < 1`-, gt=0, lt=1] __
tests\test_param_law_sync_bounds.py:38: in test_every_bound_notation_compares_numbers
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_every_bound_notation_comp2'])
___ test_every_bound_notation_compares_numbers[`float [0, 1]`-, ge=0, le=1] ___
tests\test_param_law_sync_bounds.py:38: in test_every_bound_notation_compares_numbers
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_every_bound_notation_comp3'])
_ test_every_bound_notation_compares_numbers[`float \u2208 (0, 1]`-, gt=0, le=1] _
tests\test_param_law_sync_bounds.py:38: in test_every_bound_notation_compares_numbers
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_every_bound_notation_comp4'])
___ test_every_bound_notation_compares_numbers[`float [0, 1)`-, ge=0, lt=1] ___
tests\test_param_law_sync_bounds.py:38: in test_every_bound_notation_compares_numbers
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_every_bound_notation_comp5'])
___ test_every_bound_notation_compares_numbers[`float (0, 1)`-, gt=0, lt=1] ___
tests\test_param_law_sync_bounds.py:38: in test_every_bound_notation_compares_numbers
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_every_bound_notation_comp6'])
_________________ test_exclusive_lower_bound_is_not_inclusive _________________
tests\test_param_law_sync_bounds.py:49: in test_exclusive_lower_bound_is_not_inclusive
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_exclusive_lower_bound_is_0'])
_______ test_missing_or_extra_bounds_fail[, ge=0, le=10-`int \u2265 0`] _______
tests\test_param_law_sync_bounds.py:64: in test_missing_or_extra_bounds_fail
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_missing_or_extra_bounds_f0'])
___________ test_missing_or_extra_bounds_fail[, ge=0, le=10-`int`] ____________
tests\test_param_law_sync_bounds.py:64: in test_missing_or_extra_bounds_fail
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_missing_or_extra_bounds_f1'])
_____________ test_missing_or_extra_bounds_fail[-`int \u2265 0`] ______________
tests\test_param_law_sync_bounds.py:64: in test_missing_or_extra_bounds_fail
    assert main([str(tmp_path)]) == 1
E   AssertionError: assert 0 == 1
E    +  where 0 = main(['C:\\Users\\yury_\\AppData\\Local\\Temp\\pytest-of-yury_\\pytest-1226\\test_missing_or_extra_bounds_f2'])
_____________ test_the_repo_has_no_param_settings_divergence_left _____________
tests\test_param_law_sync_repo.py:13: in test_the_repo_has_no_param_settings_divergence_left
    assert len(report.warnings) == 3
E   AssertionError: assert 2 == 3
E    +  where 2 = len(['[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 � UCITS in... portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later'])
E    +    where ['[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 � UCITS in... portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later'] = ParamSyncReport(errors=[], warnings=['[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, ...portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later']).warnings
=========================== short test summary info ===========================
FAILED tests/test_param_law_sync_values.py::test_a_wrong_value_names_the_law_and_code_and_fails
FAILED tests/test_param_law_sync_bounds.py::test_every_bound_notation_compares_numbers[`float \u2265 0, \u2264 1` (ratio)-, ge=0, le=1]
FAILED tests/test_param_law_sync_bounds.py::test_every_bound_notation_compares_numbers[float >= 0, <= 1 seconds-, ge=0, le=1]
FAILED tests/test_param_law_sync_bounds.py::test_every_bound_notation_compares_numbers[`float > 0, < 1`-, gt=0, lt=1]
FAILED tests/test_param_law_sync_bounds.py::test_every_bound_notation_compares_numbers[`float [0, 1]`-, ge=0, le=1]
FAILED tests/test_param_law_sync_bounds.py::test_every_bound_notation_compares_numbers[`float \u2208 (0, 1]`-, gt=0, le=1]
FAILED tests/test_param_law_sync_bounds.py::test_every_bound_notation_compares_numbers[`float [0, 1)`-, ge=0, lt=1]
FAILED tests/test_param_law_sync_bounds.py::test_every_bound_notation_compares_numbers[`float (0, 1)`-, gt=0, lt=1]
FAILED tests/test_param_law_sync_bounds.py::test_exclusive_lower_bound_is_not_inclusive
FAILED tests/test_param_law_sync_bounds.py::test_missing_or_extra_bounds_fail[, ge=0, le=10-`int \u2265 0`]
FAILED tests/test_param_law_sync_bounds.py::test_missing_or_extra_bounds_fail[, ge=0, le=10-`int`]
FAILED tests/test_param_law_sync_bounds.py::test_missing_or_extra_bounds_fail[-`int \u2265 0`]
FAILED tests/test_param_law_sync_repo.py::test_the_repo_has_no_param_settings_divergence_left
13 failed, 1 passed in 4.29s
```

**Proof — the green run:** Final source and tests, from the pytest step of redirected `make ci`; all 73 step tests appear below. The suite's eight pre-existing skips are recorded under `make ci`, not hidden.

```text
[WARN] tests/test_param_law_sync.py: 168 lines (warn 150, hard block 200)
tests\test_param_law_sync.py ........                                    [ 19%]
tests\test_param_law_sync_bounds.py .................                    [ 19%]
tests\test_param_law_sync_component_books.py .                           [ 19%]
tests\test_param_law_sync_excused.py ........                            [ 20%]
tests\test_param_law_sync_execution_rows.py .                            [ 20%]
tests\test_param_law_sync_output.py ...                                  [ 20%]
tests\test_param_law_sync_repo.py ..                                     [ 20%]
tests\test_param_law_sync_values.py .................................    [ 21%]
TOTAL                                                           20066      0   4240      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 4392 passed, 8 skipped, 2470 warnings in 383.23s (0:06:23) ==========
```

New modules' additional type check: `uv run mypy --explicit-package-bases scripts/param_law_sync_values.py scripts/param_law_sync_bounds.py scripts/param_law_sync_numbers.py scripts/param_law_sync_excused.py scripts/param_law_sync_types.py scripts/param_law_sync_output.py`, exit 0: `Success: no issues found in 6 source files`.

**The step's output on the built tree:** same synced interpreter as `uv run`, UTF-8 stdout captured into `.tools/s258/step.txt`; exit 0. cp1252 is separately proven by A8.

```text
[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 — UCITS investment powers and limits
[WARN] portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later
[WARN] excused PARAM bounds: analyst.scaled_stop_atr_multiplier, portfolio_manager.cash_buffer_pct, portfolio_manager.max_position_pct, portfolio_manager.max_positions, portfolio_manager.min_order_quantity, portfolio_manager.price_lookback_days, portfolio_manager.starting_cash, scanner.min_average_volume
```

**Guards planted:** Sequential source/book mutations, each requiring pytest exit 1 with a named FAILED test, then byte-for-byte restore and pytest exit 0. `.tools/s258/guards.txt`, exit 0; full assertion output per plant is in `guard-NN-red.txt` and `guard-NN-restored.txt`. The initial G06 survivor and its correction are recorded in Return notes.

```text
G01 default mismatch: red=1; restored=0; bytes_restored=True
G02 unreadable failure: red=1; restored=0; bytes_restored=True
G03 bound numbers and strictness: red=1; restored=0; bytes_restored=True
G04 missing and extra sides: red=1; restored=0; bytes_restored=True
G05 exact excuse text: red=1; restored=0; bytes_restored=True
G06 reconciled excuse must go: red=1; restored=0; bytes_restored=True
G07 excuses never cover values: red=1; restored=0; bytes_restored=True
G08 missing field excuse must go: red=1; restored=0; bytes_restored=True
G09 absent books ignored: red=1; restored=0; bytes_restored=True
G10 eight exact keys: red=1; restored=0; bytes_restored=True
G11 eight exact texts: red=1; restored=0; bytes_restored=True
G12 cp1252 failures: red=1; restored=0; bytes_restored=True
G13 cp1252 warnings: red=1; restored=0; bytes_restored=True
G14 slippage row: red=1; restored=0; bytes_restored=True
G15 promotion row: red=1; restored=0; bytes_restored=True
G16 approval row: red=1; restored=0; bytes_restored=True
G17 timeout row: red=1; restored=0; bytes_restored=True
G18 next book version: red=1; restored=0; bytes_restored=True
G19 amendment record: red=1; restored=0; bytes_restored=True
GUARDS: 19/19 rejected and restored
```

**Existing tests edited:** only `tests/test_param_law_sync_repo.py::test_the_repo_has_no_param_settings_divergence_left` (A7). Its two-warning assertion became three, with the exact eight keys and texts pinned; its docstring now distinguishes clean names/tunables/defaults from the eight deferred bounds. The other test in that file, and every test in `test_param_law_sync.py` and `test_param_law_sync_component_books.py`, are unchanged and pass.

**The four execution rows, the Changelog line and the book's version:** Value, Tunable and Rationale cells unchanged; no clause edited.

```text
**Prefix:** `EXEC` · **status:** LOCKED v1.13 · **Owner:** Yury Gurevich
| `slippage_bps` | `0` | `int ≥ 0, ≤ 1000` (basis points) | YES | Simulated slippage on paper fills; 0 = no adjustment |
| `min_promotion_runs` | `10` | `int ≥ 3, ≤ 200` | YES | Minimum completed runs before promotion past "broker_shadow" is allowed |
| `min_approval_rate` | `0.70` | `float ≥ 0.0, ≤ 1.0` | YES | Minimum fraction of approved (non-gate-rejected) fills over min_promotion_runs |
| `alpaca_timeout` | `15` | `int ≥ 1, ≤ 60` (seconds) | YES | Per-order broker call timeout; bounded latency budget per submission |
- **v1.13 — S258 / DL-276 (2026-10-08).** PARAM only: reconciles the bounds of `slippage_bps`, `min_promotion_runs`, `min_approval_rate` and `alpaca_timeout` with settings; no clause, default or code bound changes.
```

**Module line counts:** all 16 touched Python modules are below 200; maximum 190. The measured output (UTF-8 / LF for every touched file):

```text
scripts/check_param_law_sync.py: 31
scripts/param_law_sync.py: 190
scripts/param_law_sync_bounds.py: 53
scripts/param_law_sync_excused.py: 20
scripts/param_law_sync_numbers.py: 76
scripts/param_law_sync_output.py: 13
scripts/param_law_sync_sources.py: 155
scripts/param_law_sync_types.py: 33
scripts/param_law_sync_values.py: 66
tests/param_law_sync_helpers.py: 60
tests/test_param_law_sync_bounds.py: 117
tests/test_param_law_sync_excused.py: 100
tests/test_param_law_sync_execution_rows.py: 33
tests/test_param_law_sync_output.py: 65
tests/test_param_law_sync_repo.py: 45
tests/test_param_law_sync_values.py: 94
```

**`make ci`:** `.tools/s258/ci.txt`, exit **2**. The ignored local `sitecustomize.py` explicitly exits 1 before the network dependency audit can start; recorded-audit fixtures remain enabled. No Makefile or gate source was modified. Steps 14 and 15 were executed separately after `make` stopped.

| Step | Check | Result |
| --- | --- | --- |
| 1 | ruff | PASS |
| 2 | format | PASS |
| 3 | mypy (`kernel contracts agents orchestration surfaces`) | PASS |
| 4 | import-linter | PASS |
| 5 | module size | PASS |
| 6 | module header | PASS |
| 7 | law coverage | PASS |
| 8 | PARAM/settings sync | PASS; three expected warnings |
| 9 | sprint status | PASS |
| 10 | markdown links | PASS |
| 11 | version scheme | PASS; version files unchanged |
| 12 | pytest | PASS; 4,392 passed / 8 existing skipped / 100.00% |
| 13 | dependency audit | NOT RUN: network prohibited; explicitly blocked before I/O |
| 14 | detect-secrets | PASS separately, exit 0; `.tools/s258/detect-secrets.txt` |
| 15 | untracked secrets | PASS separately, exit 0; `.tools/s258/untracked-secrets.txt` |

```text
surfaces\scorecard_tool.py                                         17      0      2      0  100.00%
-------------------------------------------------------------------------------------------------------------
TOTAL                                                           20066      0   4240      0  100.00%
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
========= 4392 passed, 8 skipped, 2470 warnings in 383.23s (0:06:23) ==========
uv run python scripts/check_dependency_audit.py
NOT RUN: dependency audit requires the network; offline S258 proof.
make: *** [Makefile:59: ci] Error 1
```

```text
DETECT_SECRETS_EXIT=0
Detect secrets...........................................................Passed
UNTRACKED_SECRETS_EXIT=0
detect-secrets (untracked): no untracked files to scan
```

B2 gate self-test: `.tools/s258/gate-selftest.txt`, exit 1. **NOT RUN in full:** `pip-audit-cve` needs live vulnerability data; the offline launcher blocks it before I/O. The other 30 checks passed. This is not a 31/31 proof.

```text

A gate did not reject its planted violation, or a gate-enabling config was lost.
Until this is fixed, a green lane is not evidence that gate examined anything:
  can-fail: pip-audit-cve
PASS  can-fail: ruff � rejected (exit 1)
PASS  can-fail: module-size � rejected (exit 1)
PASS  can-fail: module-size-reads-scripts � rejected (exit 1)
PASS  can-fail: module-header � rejected (exit 1)
PASS  can-fail: law-coverage � rejected (exit 1)
PASS  can-fail: param-law-sync � rejected (exit 1)
PASS  can-fail: sprint-status � rejected (exit 1)
PASS  can-fail: markdown-links � rejected (exit 1)
PASS  can-fail: version-scheme � rejected (exit 1)
PASS  can-fail: untracked-secrets � rejected (exit 1)
FAIL  can-fail: pip-audit-cve � gate failed without proving: urllib3
      why it matters: the local dependency CVE gate must fail closed on a vulnerable package
PASS  can-fail: accepted-advisory-re-check � rejected (exit 1)
PASS  can-fail: gate-ran-rejects-abbreviated-sha � rejected (exit 1)
PASS  can-fail: gate-ran-rejects-zero-runs � rejected (exit 1)
PASS  can-fail: gate-ran-judges-the-newest-attempt-not-the-first � rejected (exit 1)
PASS  invariant: merge-procedure-asserts-a-run-exists � present
PASS  invariant: gate-ran-target-exists � present
PASS  invariant: security-gate-runs-on-push � present
PASS  invariant: ci-runs-on-push � present
PASS  invariant: sprint-status-gate-wired-locally � present
PASS  invariant: sprint-status-gate-wired-in-ci � present
PASS  invariant: untracked-scan-wired-into-ci � present
PASS  invariant: dependency-audit-not-ignored-by-ci � present
PASS  invariant: dependency-audit-wired-in-ci � present
PASS  invariant: size-block-reads-scripts-locally � present
PASS  invariant: size-block-reads-scripts-in-ci � present
PASS  invariant: dependabot-pins-python-to-3-13 � present
PASS  invariant: graph-vocabulary-guard-wired � present
PASS  invariant: graph-vocabulary-injected-at-deploy � present
PASS  invariant: codeql-custom-query-referenced � present
PASS  invariant: codeql-config-queries-not-overridden � present

gate self-test: 30/31 passed
```

**Scope proof:** both required commands printed nothing. `git diff HEAD -- docs/STATE.md` also printed nothing: this worktree has not changed STATE. During the build, the shared `main` ref advanced from `8d55cb569b01680ca583b52d25adecf742a87802` to `3b6f1fe86877c3157ffe097b43f52b7379cbd603`; comparing STATE with that newer `main` shows its independent update, not a sprint edit. The execution-book diff was reviewed whole: only the four Type cells, version and Changelog. No clause, Value, Tunable or Rationale cell moved.

```text
git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration/packs orchestration/history_window.py pyproject.toml uv.lock scripts/gate_selftest_cases.py docs/laws/_TEMPLATE.md

 git diff main --stat -- 'agents/*/settings*.py' orchestration/settings.py surfaces/dashboard/settings.py

 git diff HEAD --stat -- docs/STATE.md docs/laws/INDEX.md docs/laws/ledger.md
```

**`make gate-ran`:** owed by the planner at merge.

**Not met / verified failing:** full `make ci` and full gate self-test are not proven green: live dependency audit and live CVE plant are NOT RUN (network). Eight existing suite skips remain, named above; no sprint test skips. A non-required broad mypy check of scripts/tests verified failing (43 typing errors, including untyped new and existing tests and the unchanged envelope reader); it is outside configured CI's scope and was not used as green proof. The six new modules' explicit check and CI's configured mypy check pass. Remote gates, version bump, rollup labels and merge-time F1 are owed to the planner. Push, merge and deploy are not done by instruction.

---

## Return notes

- AGENTS.md says 14 CI steps; CLAUDE.md and the actual `ci:` target have 15. Followed the target, including sprint status; no rules file edited.
- Initial red used `tunable(..., lt=...)`, which this API does not accept. Corrected only the temporary fixture to use Pydantic `Field` with description metadata for exclusive upper bounds. `.tools/s258/red-initial.txt` preserves that failed attempt; the required red was re-run and pasted before implementation.
- G06's first mutation survived: the original reconciliation fixture edited the Type cell, so the changed-text check still rejected it. Added `test_an_excuse_fails_when_code_catches_up_without_a_cell_edit` to prove independent stale-entry removal; G06 then fails and restores. Initial evidence remains in `.tools/s258/guards-initial.txt`. G09's scratch mutation was corrected before its run to actually break absent-book scoping. Final 19/19 plants rejected/restored.
- Optional mypy command corrections: PowerShell passes wildcard paths literally to mypy, so enumerated them; namespace modules require `--explicit-package-bases`. The broad scripts/tests attempt then found 43 typing errors outside CI's configured scope, including the unchanged envelope reader; flagged, not fixed. The explicit six-new-module check passes. No existing B2 test was edited to satisfy that optional check.
- The shared generated commit hook points at the main checkout's venv. Use an ignored worktree-local copy with only `INSTALL_PYTHON` redirected to `ta-s258/.venv`, keeping the same pre-commit hook runner/config; leave the shared hook untouched. This keeps the commit's interpreter in the authorized worktree.
- The shared `main` ref advanced independently during the build. Required protected-path comparisons with current `main` still print nothing; STATE is unchanged against the sprint's starting HEAD. No rebase, merge or main-checkout edit was made here.
- `pyproject.toml`, `uv.lock` and `docs/STATE.md` are untouched. The planner bumps PATCH and syncs the lock at merge, moves the execution label in both rollups, runs the live audit/CVE self-test and remote gates, and performs F1. Work-queue 114 remains open for the eight rows, whose text and paths are unchanged here. No push, merge or deploy.

---

## Planner's review and merge-time work — 2026-10-08 20:40 AEDT

**The handback against the checklist.** All ten items are met. Item 9 names two things as NOT RUN, the
dependency audit and the live vulnerability case of the gate self-test; both need the network. The planner
runs the whole gate below.

**Re-measured by the planner, not read from the builder's logs.** Everything here ran in `../ta-s258` on
the builder's commit `a06a5f98`, before `main` was merged in (the merge-in brought documents only).

- Both scope commands of item 7 print nothing, against `main` and against the commit the worktree was cut
  from. Nineteen files changed: three modules edited and six new, one test edited and six test files new,
  the execution book, and two documents. Every one is UTF-8 with LF endings.
- **The built reader reads every row.** A count of the planner's own, over the built functions, gives the
  numbers this spec was written from: 16 books; 235 rows with a settings field; 235 Value cells agree (177
  in backticks, 45 in backticks and quotes, 9 a dash, 4 the bare word `empty`); 164 rows have a bound in
  code, of which 156 state the same set (the 152, and the four execution rows) and 8 are excused by their
  exact text; 71 have no bound on either side. A second detector, written without the built regular
  expressions, looked in every Type cell for a bound symbol, a bracketed pair of numbers, a word such as
  "max" or "at least", and a number the reader had not turned into a bound. It found nothing the reader
  missed (its one hit is the enum member `max` in `operator.effort`).
- **Thirteen wrong numbers planted in real rows and real settings, one at a time.** The step was run as a
  subprocess with a `cp1252` pipe each time. Each exits 1 with the expected `[FAIL]` lines naming the row,
  none raises, each was restored, and the tree is clean: the deliberator's `max_tokens` Value back at
  `8192`; its upper bound back at `8192`; `execution.alpaca_timeout` with its upper bound dropped (the
  line prints with `?` in place of the symbol); a string default changed; a secret's dash replaced by a
  value; an excused row edited and still wrong (two lines); an excused row reconciled with its entry left
  behind; an excused row's Value changed (the entry does not excuse it); an entry deleted while its row is
  still wrong; an interval's upper number changed; a strict bound written as inclusive; and, in code, the
  deliberator's default and then its bound changed with the law left alone.
- **Ten pieces of the comparison removed, one at a time.** Each turns the step's 73 tests red and each was
  restored: bounds never compared (23 tests fail); only the stated bounds compared, so a missing side
  passes (4); a differing Value not a failure (19); an unreadable Value skipped (15); a stale or edited
  excused entry tolerated (4); an entry excusing any text (2); an interval's open side read as closed (3);
  the numeric failures kept out of the report (56); output through plain `print` (2); an execution row put
  back at 120 (3).
- The one existing test the builder edited is the one this spec named. The edit was read: it asserts three
  warnings in place of two, that the third names exactly the eight rows, and that the list equals the
  eight texts written out in the test's own helper.
- The code is the decided design, D1 to D5, and nothing more.

**Changed by the planner at merge.**

- `main` had moved by one commit of documents (the design log, the work queue, `docs/STATE.md`) and was
  merged in with no conflict. The builder wrote no design-log entry, so nothing was renumbered.
- The version is `0.123.03`. `uv lock` changed the version line only; 180 packages before and after.
- The execution book's row in `docs/laws/INDEX.md` and in `docs/laws/ledger.md` reads v1.13 (S258,
  DL-276), `PARAM` only, 40 / 66 unchanged.

**Accepted as built, with the limits known.**

- The code's bounds are read from the field itself. A rail enforced by a validator function is not seen.
- When one Type cell states the same side twice, the reader keeps the last (`≥ 0, ≥ 5` reads 5). No row
  does this.
- Two numbers written with no space after the comma (`[1,100]`) read as one grouped number, so no bound
  is read from them. Against a field that has bounds this fails. Against a field with none it would pass.
  No row is written so; the second detector above would have shown it.
- The builder's wider type check of `scripts` and `tests` found 43 errors. The gate's type check covers the
  package trees and not those two, by configuration, so nothing is owed here.
