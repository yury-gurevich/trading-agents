<!-- Agent: planning | Role: sprint handover -->
# Sprint 258 — A law row's default and bounds are compared with the code, and a wrong number fails the gate

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-258-a-law-rows-numbers-are-compared-with-the-code`
**Status:** SPEC
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

- [ ] A Value cell that differs from the default fails the step (A1), in every form the books use (A2),
      and an unreadable one fails too (A3).
- [ ] A Type cell whose bounds differ from the field's fails the step, in every notation (A4), with a
      side missing or extra (A5).
- [ ] The excused list holds exactly the eight rows, excuses only what it records, and an entry that is
      no longer needed fails the step (A6, A7).
- [ ] The step never raises on a `cp1252` console (A8).
- [ ] The four execution rows state the code's bounds; no clause is edited (B1).
- [ ] Nothing under a fidelity decision path, no settings file, `pyproject.toml`, `uv.lock` or
      `scripts/gate_selftest_cases.py` is touched.
- [ ] Every new guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage, or each step that could not run named as NOT RUN.

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
| *(fill)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(fill)*

**Contradictions found between a law and this spec:** *(fill, or "none")*

**Laws found silent where a decision was needed:** *(fill, or "none")*

**Clauses that were ⬜ and are now proven:** *(fill, or "none")*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| *(fill)* | | | | |

**Tests added beyond the plan:** *(fill, or "none")*

---

## Closeout — evidence

**Status:** SPEC

**Tree the proofs ran in (and `.env` present?):** *(fill)*

**INTENT (recorded before code):** *(fill)*

**Result:** *(fill only for work done)*

**Files changed:** *(fill)*

**Design decisions:** *(fill)*

**Proof — the red run first:** *(paste)*

**Proof — the green run:** *(paste)*

**The step's output on the built tree:** *(paste whole)*

**Guards planted:** *(one line per guard)*

**Existing tests edited:** *(each, with its reason)*

**The four execution rows, the Changelog line and the book's version:** *(paste)*

**Module line counts:** *(fill)*

**`make ci`:** *(output file, exit code, each NOT RUN step)*

**Scope proof:** *(the two commands of checklist item 7 and their empty output)*

**`make gate-ran`:** owed by the planner at merge.

**Not met / verified failing:** *(fill, or "none")*

---

## Return notes

*(fill)*
