<!-- Agent: planning | Role: sprint handover -->
# Sprint 156 — The law book's own proof becomes checkable

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-156-law-coverage-is-checkable`
**Status:** SPEC — closes hardening rows **R** and **R²**, puts **O** into warn-only shadow
**Version:** feat → **0.86.00** (MINOR: two middle digits, zeroing the patch group)
**Effort:** M–L
**Decisions:** [ADR-0021](../decisions/0021-clause-summary-mirrors-the-law.md) a clause summary
mirrors the law, never the test · [conventions §3](../laws/conventions.md) green *is* a docstring
citation · [DL-87](../design-log.md) a partial test is not a smaller clause ·
[DL-70](../design-log.md) plant the violation · [DL-57](../design-log.md)/[DL-59](../design-log.md)
*didn't look* must not render as *looked and found nothing* · [DL-82](../design-log.md) **warn-only
shadow first** (the precedent this sprint reuses) · [LAW-02](../../ops/laws/LAW-02-successful-execution.md)
success is proven, never assumed

> **Why MINOR and not PATCH.** This ships a **new gate** — `scripts/check_law_coverage.py` plus a
> tenth `make ci` step. New capability by the CLAUDE.md rule (*feat → two middle digits*), the same
> call S143 made for the vocabulary guard. `0.85.06` → **`0.86.00`**, patch group zeroed. If you
> disagree after reading the rule, say so in the return notes rather than silently choosing
> differently.

---

## 🔴 MUST RULE — this sprint edits the law book. Read this section twice.

Every other sprint tells you **`laws.md` is read-only, never edit it**. That still holds, absolutely.
This sprint is unusual because its *subject* is the law book's bookkeeping, so the rule needs to be
stated precisely rather than as a slogan:

| File | This sprint | Why |
| --- | --- | --- |
| `agents/*/laws/laws.md` | ☠️ **NEVER EDIT.** Not one character. | LOCKED constitutions. A clause you believe is wrong is a `drift-register.md` row plus a report — never an edit. Amending one is its own cycle with its own ADR (S152) |
| `agents/*/laws/test-plan.md` | ✅ **You edit these** — statuses and the Test column | This is the bookkeeping the sprint is fixing |
| `docs/laws/ledger.md`, `docs/laws/INDEX.md` | ✅ You reconcile the counters | They must equal what the test-plans actually say |
| `docs/laws/conventions.md` | ☠️ **NEVER EDIT.** | Amendable only by a new ADR ([ADR-0021](../decisions/0021-clause-summary-mirrors-the-law.md) was the last one) |
| `docs/laws/drift-register.md` | ✅ Append-only, for findings | The one law-adjacent file you may add to |
| `docs/hardening-backlog.md` | ✅ Move rows R and R² to Done, with evidence | |

**The single most dangerous move available to you in this sprint is flipping a ⬜ to 🟩, or keeping a
🟩 that should fall.** ADR-0021 exists because exactly that happened in S151. Read it before you
touch a status. **When in doubt, go ⬜** — a wrongly-gray clause costs a future test; a wrongly-green
one costs the ledger its meaning, silently, for everyone who reads it afterwards.

### Before writing code

1. Read [`docs/laws/conventions.md`](../laws/conventions.md) end to end — especially **§2** (IDs are
   append-only and immutable), **§3** (the *only* definition of green), **§7** (test citation) and
   **§7a** (the summary mirrors the law). §3 is the specification your checker implements.
2. Read [ADR-0021](../decisions/0021-clause-summary-mirrors-the-law.md) and
   [DL-87](../design-log.md).
3. Read **one** agent's `laws.md` + `test-plan.md` pair in full (execution is the best example — it
   carries all three of this sprint's failure modes) so you know what the documents actually look
   like before you parse 14 of them.
4. Fill the **Law reading record** near the bottom of this file **before** your first code change.
5. **If a law contradicts this spec, STOP and report.** A contradiction you surface is a success.

---

## Why this sprint

`conventions.md` §3 states the only definition of done in this repo:

> A clause is **GREEN** iff **≥ 1 passing functional test cites its ID** (in the test's docstring).

**Nothing checks that.** It is enforced by whoever last edited a table, and the measurements below
were taken on 2026-08-02 against `main` at `9bf1301`.

### Measurement 1 — 29 of 284 green rows are not green

Every `🟩` row was parsed and each cited test resolved against the live tree:

| Failure mode | Count | What it means |
| --- | --- | --- |
| Cited test function **does not exist anywhere** | **10** | The proof was deleted; the green stayed |
| Test exists, **docstring never names the clause ID** | **19** | Fails §3's literal wording |
| Survive the check | 255 | A **ceiling, not a floor** — see the caveat below |

The 10 with no test at all: `EXEC-IN-02`, `EXEC-TRG-03`, `EXEC-TRG-05`, `MON-OUT-02`, `MON-OUT-03`,
`MON-OUT-05`, `MON-NEV-01`, `PM-TYP-03`, `PROV-FAIL-02`, `PROV-OBS-03`. Several survive only in the
`mutants/` snapshot — they were deleted when **ADR-0017 retired `execute_close` and the monitor's
exit authoring**, and nothing flagged the greens that pointed at them.

> **The caveat that keeps this honest.** The check is mechanical: *does a docstring name the ID?* It
> cannot catch the S151 shape — a real citation on a test that proves one third of its clause. So
> 255 is an upper bound on what is proven, and this sprint does not change that. It removes the
> three failure modes that *are* mechanically detectable. Say so in the closeout; do not let the new
> gate be read as "the book is now verified".

### Measurement 2 — 101 clauses have no row at all

| | |
| --- | --- |
| Clause IDs across 14 `laws.md` files | **653** |
| Rows across 14 `test-plan.md` files | **553** |
| **Clauses with no row at all** | **101** — provider 22, master 21, execution 13, scanner 13, analyst 12, portfolio_manager 12, monitor 7, reporter 1 |
| **Orphan rows** (row exists, clause does not) | **1** — `RPT-OBS-03` |

A clause with no row cannot be ⬜ *or* 🟩 — it is simply absent from the document whose own header
calls it **the master**, so it never surfaces as unproven in any count. That is
[DL-57](../design-log.md) at document level, and it is why the ratios have always read better than
the book is.

`RPT-OBS-03` is the mirror image: a row proving a clause that does not exist. `RPT-TYP-03` exists in
`laws.md` with no row. **Do not "fix" this by renaming either one** — §2 makes IDs immutable. Report
it and add a drift row.

### Measurement 3 — three incompatible table schemas

| Schema | Agents | Problem |
| --- | --- | --- |
| `Law \| What the test must prove \| Scenario \| Test \| Status` | analyst, execution, portfolio_manager, provider, scanner | The good one |
| `Clause \| Proof obligation \| Test type \| Test(s) \| Status` | deliberator | Same shape, different headers |
| `Clause \| Status \| Test` | curator, forecaster, monitor, operator, reporter, researcher, supervisor | **No summary column at all**, and the Test column carries bare function names with no file |
| `Clause \| Description \| Test \| Status` | master | Fourth variant |

**Seven of fourteen agents have nowhere for ADR-0021's rule to apply.** `laws.md` also varies: 13
agents mark clauses `**EXEC-IDN-01**` (bold) and provider marks them `` `PROV-IDN-01` `` (backticks).
Your parser must handle both or it will silently see zero clauses for provider — mine did, on the
first pass.

### Why a gate and not another manual reconciliation

S152 reconciled these counters **by hand**, correctly, six weeks ago. The drift reappeared one
document down within the same month. A hand pass fixes the instance; only a gate fixes the class.
This is the DL-52/DL-54/DL-55 lesson that produced `gate_selftest.py` in the first place.

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. See
> [Handback contract](#handback-contract--mandatory) — results go in this file, not in chat.

### 1 · `scripts/check_law_coverage.py` — the checker

A new gate script in the shape of the existing ones (`scripts/check_module_size.py` is the model:
module docstring with `Agent:` / `Role:` / `External I/O:`, `main(argv) -> int`, human-readable
failure lines naming the file and the offending ID).

It must parse **all four table schemas** and **both clause-marker styles**, and enforce:

| # | Assertion | Mode in this sprint |
| --- | --- | --- |
| A | Every `🟩` row cites ≥1 test that **exists** in the tree | **hard fail** |
| B | For every `🟩` row, ≥1 cited test's **docstring contains the clause ID** | **hard fail** |
| C | No **orphan row** — every row's ID exists in that agent's `laws.md` | **hard fail** |
| D | `ledger.md` and `laws/INDEX.md` green/total counters **equal** the values derived from the test-plans | **hard fail** |
| E | Every clause ID in `laws.md` has a row in `test-plan.md` | ⚠️ **warn only** — prints the count and the IDs, exit 0 |

**E is warn-only on purpose, and this is a decision, not a shortcut.** Hard-failing it means writing
101 rows before the gate can go green, which drags a mechanical fix into a judgement-heavy one and
makes the sprint unlandable. [DL-82](../design-log.md) set this precedent for property enforcement
for the same reason: **shadow first, enforce once the backlog is zero.** S157 writes the rows and
flips E to hard fail. Say in the warning exactly how many and which, so it cannot be ignored quietly.

**Resolution rules** (these decide whether the checker is usable at all):

- A citation may be `file.py::test_name` **or** a bare `test_name`. Resolve bare names within
  `agents/<agent>/tests/**`; if a cited file is named, prefer it.
- **Ambiguity is a failure, not a guess.** If a bare name resolves to two different functions in one
  agent's tests, fail and name both — otherwise a rename could silently re-point a green.
- A row may cite several tests. It passes if **at least one** resolves *and* cites the ID.
- Ignore anything under `mutants/` entirely. It is a mutmut snapshot, not the live tree, and it is
  the reason three of the 10 dead citations look alive to a naive grep.
- Read docstrings with `ast.get_docstring`, not a regex over the file. A clause ID appearing in a
  comment, an assertion string or another test's docstring is **not** a citation.

Wire it into `make ci` after the module-header step, and into `.pre-commit-config.yaml` if the other
checkers are there.

**Result:**

### 2 · A gate that has never failed is not known to work

Add a case to [`scripts/gate_selftest_cases.py`](../../scripts/gate_selftest_cases.py) for the new
check, in the same shape as the existing entries. That file's own docstring is the argument:

> *Every entry here exists because a real defect got through. A check that has never been observed
> failing is not known to work.*

Plant at least: a 🟩 row citing a test that does not exist, and a 🟩 row whose cited test exists but
whose docstring omits the ID. Run `make gate-selftest` and paste the output in the closeout.

**Result:**

### 3 · Work the 29 down to zero — bias to ⬜

For each of the 29 rows, one of exactly two outcomes. **There is no third option and no "leave it".**

**The 10 with no test (mechanical — just do it):** demote to ⬜. Put the reason in the Test column,
naming the test that went and why it is gone where you know it (`test_execute_close_*` and the
monitor exit tests went with **ADR-0017**). Do not hunt for a replacement test; that is a future
sprint's work, and inventing a citation is the failure mode this sprint exists to stop.

**The 19 whose docstring omits the ID (judgement — report every one):** open the clause in `laws.md`
and the test, and decide:

- The test's assertions **genuinely cover the clause as written** → add the clause ID to its
  docstring, in the existing convention (`"""EXEC-FAIL-03: ..."""`), and keep 🟩.
- **Anything less than that** → demote to ⬜, naming what the test does cover.

**Record all 19 in the table at the bottom of this file** — clause, test, the decision, and one line
of evidence. This is the reviewable artifact; a bare "fixed 19 docstrings" is an incomplete handback.

🚨 **Do not widen a clause summary to make a test fit it, and do not narrow one either.** That is
literally ADR-0021. If you catch yourself editing the summary column to make a status defensible,
stop — you have found a second instance of the S151 defect and it is a finding worth reporting.

**Expect the book-wide green count to fall.** That is the correct outcome and must be stated plainly
in the closeout, not smoothed over. A ratio that gets worse because it got honest is the point.

**Result:**

### 4 · Reconcile the roll-ups from the derived counts

Once assertion D exists, `ledger.md` and `laws/INDEX.md` stop being hand-maintained opinions. Update
both to the derived values — **after** item 3, so you are reconciling to the corrected book rather
than to the current claim.

Both files currently disagree with the test-plans for **8 of 14 agents** and with *each other* for
several. Do not assume either is right: derive, then write. Note in the closeout which agents moved
and by how much.

**Result:**

### 5 · Report the schema divergence — do not fix it here

Measurement 3 is real and out of scope. Add **one** `drift-register.md` row naming it as a single
finding (four schemas, seven agents with no summary column, two clause-marker styles), plus the
`RPT-OBS-03` / `RPT-TYP-03` mismatch. **One row for the pattern, not eleven rows for the instances.**

Do **not** normalise the tables in this sprint. Making seven agents grow a summary column means
restating ~140 clauses, and the durable answer is to *generate* that column from `laws.md` so
ADR-0021 becomes mechanically true instead of remembered. That is S157's question, and pre-empting
it by hand here would create exactly the hand-maintained duplication this sprint is removing.

**Result:**

### 6 · Close the hardening rows with evidence

Move **R** and **R²** from *Open* to *Done* in
[`docs/hardening-backlog.md`](../hardening-backlog.md) with the before/after numbers and the gate
that keeps them shut. Leave **O** open, and update its trigger to name S157 and the warn-only mode.

**Result:**

---

## Test plan — every test I want, and why

**Ground rules.** Every test **plants the violation and requires the failure** (DL-70). A test that
asserts a good book passes, without ever having proven a bad one fails, is not evidence — that is
the exact defect this sprint is about, one level up. Names below are descriptive, not prescriptive.
**If you conclude one of these is wrong or untestable, say so with a reason — do not silently drop
it.**

Build the checker against **synthetic fixture books in `tmp_path`**, not against the real
`agents/**` tree. A test that reads the live law book changes meaning every time someone edits a
table, and would have to be updated by the same sprint that breaks it.

### A · The checker's assertions

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | a clean book passes | fixture: 1 clause, 1 row 🟩, a real test citing the ID | exit 0, no output |
| A2 | **dead citation is caught** | 🟩 row citing `test_gone` that exists nowhere | non-zero exit; message names the clause **and** the missing test |
| A3 | **uncited docstring is caught** | 🟩 row citing a real test whose docstring omits the ID | non-zero exit; message names both. **This is assertion B, the 19-row failure mode** |
| A4 | a comment is not a citation | test whose *docstring* omits the ID but a `#` comment contains it | still fails — proves `ast.get_docstring`, not a file grep |
| A5 | ⬜ rows are not checked | ⬜ row citing a dead test | passes — an unproven clause is allowed to have no working citation |
| A6 | **ambiguity fails, never guesses** | same bare `test_name` in two files in one agent | non-zero exit naming both paths |
| A7 | orphan row is caught | row for `FOO-BAR-99` with no such clause in `laws.md` | non-zero exit naming the row |
| A8 | **roll-up drift is caught** | fixture ledger claiming 5 green where the plan has 4 | non-zero exit naming the file, the agent, claimed vs derived |
| A9 | missing row **warns and does not fail** | clause with no row | **exit 0**, output names the clause and the count. Proves E is shadow, deliberately |
| A10 | `mutants/` is ignored | cited test that exists **only** under `mutants/` | non-zero exit — proves the snapshot cannot resurrect a dead green |

### B · Schema and format tolerance

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | all four table schemas parse | one fixture per schema (5-col, deliberator variant, 3-col, master 4-col) | identical verdicts for equivalent content — the 3-col agents must not silently pass by being unparseable |
| B2 | **both clause-marker styles parse** | `**ID**` and `` `ID` `` clause lines | both recovered. **Plant the backtick-only file and require the clause count to be non-zero** — a parser that sees zero clauses reports a perfect book |
| B3 | `file.py::name` and bare `name` both resolve | one row of each | both pass |

### C · The real book

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| C1 | the checker passes on the corrected tree | — | `make ci` green at handback, with E's warning showing exactly 101 (or your corrected count) |
| C2 | gate self-test covers the new step | item 2's planted cases | `make gate-selftest` green with the new case included |

---

## Explicit non-goals

- **No `laws.md` edit of any kind.** Not a typo, not the `RPT-TYP-03`/`RPT-OBS-03` mismatch. Drift row.
- **No `conventions.md` edit.** ADR-only.
- **No new clause IDs, no renumbering, no renaming.** §2 is absolute.
- **No table normalisation** and no new summary columns (item 5).
- **No writing of the 101 missing rows.** That is S157, and E stays warn-only until then.
- **No hunting for replacement tests** for the 10 dead citations. Demote, name, move on.
- **No production source changes.** If you find yourself editing `agents/*/[!t]*.py`, stop — this
  sprint touches `scripts/`, `tests/`, `docs/` and `agents/*/laws/*` plus test docstrings only.
- **No deploy, no live-spine work, no functionality check.** You have no `.env` and no credentials;
  that is operator sequencing after merge and it is not your job.

### The road not taken (LAW-06)

Options weighed and **ruled out** — record any further ones you rule out during implementation:

- **Hand-reconcile all three documents again (the S152 approach).** Rejected: it was done correctly
  six weeks ago and the drift returned inside a month, one document down. The instance is not the
  problem.
- **Hard-fail assertion E immediately.** Rejected: 101 rows must be written before the gate can pass,
  which turns a mechanical fix into a judgement marathon and produces a sprint that cannot land.
  DL-82's warn-only shadow is the same trade, already decided once.
- **Generate the whole test-plan from `laws.md` now.** This is almost certainly the right end-state —
  it makes ADR-0021 mechanically true rather than a rule people must remember — but it would rewrite
  553 rows including 284 status marks in the same change that is trying to establish whether those
  marks are trustworthy. Sequence it after the audit, not before. **S157.**
- **Just delete the 10 dead-citation greens' rows.** Rejected: the clause still exists, so deleting
  the row converts a *visibly* wrong green into an *invisibly* missing clause — measurement 2's
  failure mode, chosen deliberately. Demote to ⬜ instead.
- **Make the checker warn on everything at first.** Rejected: A/B/C/D have a known, finite, named
  backlog of 29 + 1 that this sprint closes. A gate whose backlog is closed in the same sprint should
  enforce; only E has an open backlog.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, all four remote gates green **before** merging locally
   (DL-56 — pushing is the gate; no PR required).
2. Nothing to deploy. This sprint changes no runtime behaviour, so the fleet stays on `:s155` and no
   functionality check is owed.
3. Planning reviews the 19 adjudications in item 3's table. **This is the review that matters** —
   every one of them is a green that survived or fell.
4. S157: generate the 101 missing rows, decide the summary-generation question, flip E to hard fail.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds, never a bare literal.
- Faults, not silent failure — `kernel.fault_boundary`, errors redirected with provenance.
- `make ci` all 9 steps green — **10 with yours** — and **100.00 % coverage floor**, before handback.
  Never lower the floor.
- Version bump in `pyproject.toml` to **0.86.00** (feat → MINOR), `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the test docstring.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48 — drift reconciliation is the coding agent's step).
- Secrets never through the worktree — chat or gitignored `.env` only.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the placeholder sections below.**
Not a separate report file. Not chat-only. Not a summary that points elsewhere.

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the six spec items above, in place.
3. Fill the **Adjudication table** — one row per each of the 29, with the decision and its evidence.
4. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
5. Fill the **Closeout — evidence** block with real pasted output: `make ci` counts, the
   `make gate-selftest` run, the checker's warn-only E output, the remote gate job results.
6. Fill the **Return notes** block.
7. State any success factor you did **not** meet plainly, as "verified failing" or "not done"
   (LAW-02 — intent is never restated as outcome; a proven failure is a valid handback, a silent gap
   is not).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses/sections that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| `scripts/check_law_coverage.py` | | conventions §2, §3, §7, §7a | |
| `agents/*/laws/test-plan.md` edits | | conventions §3 (green definition), ADR-0021 | |
| `docs/laws/ledger.md` + `laws/INDEX.md` | | conventions §3 rollup | |
| `scripts/gate_selftest_cases.py` | | DL-70 | |

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

---

## Adjudication table — fill at handback (item 3)

| # | Clause | Cited test | Decision | Evidence (one line) |
| --- | --- | --- | --- | --- |
| 1 | `EXEC-IN-02` | `test_execute_close_stage_status_and_reconcile` | | |
| 2 | `EXEC-TRG-03` | `test_execute_close_stage_status_and_reconcile` | | |
| 3 | `EXEC-TRG-05` | `test_execute_close_stage_status_and_reconcile` | | |
| 4 | `MON-OUT-02` | `test_stop_rule_writes_check_close_and_dispatches_execution` | | |
| 5 | `MON-OUT-03` | `test_stop_rule_writes_check_close_and_dispatches_execution` | | |
| 6 | `MON-OUT-05` | `test_hold_writes_check_without_close_decision` | | |
| 7 | `MON-NEV-01` | `test_stop_rule_writes_check_close_and_dispatches_execution` | | |
| 8 | `PM-TYP-03` | `test_order_intent_gate_report_is_additive_and_round_trips` | | |
| 9 | `PROV-FAIL-02` | `test_fundamentals_failure_degrades_without_affecting_ohlcv` | | |
| 10 | `PROV-OBS-03` | `test_fundamentals_failure_degrades_without_affecting_ohlcv` | | |
| 11 | `ANLZ-NEV-05` | `test_recommendation_carries_sentiment_score_when_present` | | |
| 12 | `ANLZ-OBS-02` | `test_degraded_market_data_returns_explained_rejection` | | |
| 13 | `CUR-FAIL-01` | `test_build_dataset_degrades_on_graph_fault` | | |
| 14 | `CUR-FAIL-03` | `test_train_predictor_degrades_on_graph_fault` | | |
| 15 | `FORE-IN-02` | `test_forecast_return_persists_and_returns_a_shadow_prediction` | | |
| 16 | `FORE-FAIL-03` | `test_forecast_return_falls_back_to_neutral_on_a_model_fault` | | |
| 17 | `PM-OUT-06` | `test_order_intent_emits_pm_gate_report` | | |
| 18 | `PM-OBS-01` | `test_evaluate_orders_sizes_order_and_stores_money_as_cents` | | |
| 19 | `PROV-IDM-01` | `test_integrity_nonzero_sigma_without_anomaly_stays_clean` | | |
| 20 | `PROV-TYP-01` | `test_get_market_data_round_trips_and_writes_provenance` | | |
| 21 | `RPT-OUT-06` | `test_reporter_fault_boundary_returns_degraded_payloads` | | |
| 22 | `RES-OUT-06` | `test_propose_insufficient_evidence_writes_no_flag` | | |
| 23 | `SCAN-TYP-02` | `test_run_scan_calls_provider_and_returns_ranked_candidates` | | |
| 24 | `SUP-IN-04` | `test_record_dispatch_run_writes_one_message_per_step` | | |
| 25 | `SUP-IN-05` | `test_report_fault_writes_one_fault_node` | | |
| 26 | `SUP-OUT-04` | `test_record_dispatch_run_writes_one_message_per_step` | | |
| 27 | `SUP-OUT-05` | `test_report_fault_writes_one_fault_node` | | |
| 28 | `SUP-FAIL-03` | `test_record_dispatch_run_returns_rejection_when_graph_write_fails` | | |
| 29 | `SUP-FAIL-04` | `test_report_fault_returns_rejection_when_graph_write_fails` | | |

> Rows 1–10 are the dead citations — expected decision **⬜ demote**, but verify each yourself; my
> resolution ignored `mutants/` and searched only `agents/<agent>/tests/**`, so a test that legitimately
> lives elsewhere (`tests/`, `orchestration/tests/`) would look dead to me and is a finding worth
> reporting. Rows 11–29 are the judgement calls.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s)/assertion covered |
| --- | --- | --- | --- | --- |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Files changed:**

**Proven (LAW-02):**

**Green count before → after (book-wide, and per agent that moved):**

**Not met / verified failing:**

---

## Return notes
