<!-- Agent: planning | Role: sprint handover -->
# Sprint 251 — every open drift row is decided: the law says what the code does, or the row says what it waits for

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 104
**Branch:** `sprint-251-every-open-drift-row-is-decided`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** L
**Decisions:** [DL-259](../design-log.md) (the planner's ruling on each of the 23 rows, with the
roads not taken) · the builder's decisions go to the **next free DL** (`DL-260` at spec time;
`DL-258` is reserved for S250) · closes or decides DRIFT-030, 031, 032, 034, 037, 039, 040, 059, 060,
061, 065, 074, 076, 077, 078, 081, 082, 083, 084, 085, 086, 087, 094

> **Why this bump kind.** No new capability and no behaviour change. Law books are amended to say
> what the code already does; one capability declaration in `contracts/` is corrected.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice.** This sprint *is* a law cycle, so the usual "LOCKED, read-only" status
is lifted for exactly the clauses named in the row table below, and for nothing else.

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md`, `orchestration/laws/dispatcher/laws.md`, `surfaces/laws/laws.md` | A **locked constitution** each | Amend **only** the clauses the row table names. Bump the book's version, add a Changelog line naming the DRIFT row |
| each book's `test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | One row per clause. A reworded 🟩 clause keeps a citing test that proves the new wording |
| `docs/laws/drift-register.md` | The worklist | Each row's status cell is rewritten: `CORRECTED (S251, …)` or `DECIDED (S251, …)` |
| `docs/laws/ledger.md`, `docs/laws/INDEX.md` | Rollups and versions | Both, for every book touched. The gate derives the counts |

### The rule

1. **Before writing anything**, read whole: `docs/laws/conventions.md`, `docs/laws/drift-register.md`,
   `docs/laws/_TEMPLATE.md`, and the `laws.md` + `test-plan.md` of every book in the row table.
2. For each row, **read the code the row describes** and confirm the row is still true. A row that has
   gone stale is recorded as such, not amended blind.
3. **Write the Law reading record** (bottom of this file) before your first edit.
4. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).
5. **If a row cannot be closed without changing behaviour, leave it OPEN**, say why in its status cell
   and in the Return notes, and go on. The rows are independent.

### 🩹 The law-cycle question — answered here: **YES, for 13 books**

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

It amends clauses in 13 books and corrects one `owns_graph` declaration. The cycle is owed per book:
version bump, Changelog line, test-plan row per clause, clause ID in each citing test, both rollups.
🪤 **The rollup is derived.** `make ci` recomputes it; let the gate give the number.

⚠️ **The one invariant: no behaviour changes.** No file under `agents/`, `kernel/`, `orchestration/`
or `surfaces/` changes except law books, tests and docstrings. The single exception is
`contracts/execution.py`'s `owns_graph` (DRIFT-094). If closing a row seems to need a code change,
that row stays OPEN.

---

## Goal

At merge, no row in `docs/laws/drift-register.md` reads `OPEN`. Each of the 23 rows below is either
`CORRECTED` (the law now says what the code does, with a citing test where the clause is proven) or
`DECIDED` (it waits for a named feature, and says which). No runtime behaviour differs from `main`.

## Why (context)

The register holds **22 OPEN rows and one PARTLY CORRECTED** *[measured 2026-10-01]*, the oldest from
2026-08-06. Most were filed by builders who found a law out of date and were told the book was
read-only for their sprint. That rule was right each time, and it has left the constitution
describing a pub/sub fleet while the fleet runs graph-pull. Two recent sprints (S248, S249) each had
to stop and reason about a contradiction older than themselves. The etalon's product is the method;
a law book that does not describe the system is a defect in the product.

### Measured, 2026-10-01 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Open rows | 22 `OPEN` + DRIFT-081 `PARTLY CORRECTED` | *[measured]* `grep` of the status cells in `drift-register.md` |
| DRIFT-039's field | `portfolio_state_snapshot`: **0** hits in `agents/` and `contracts/` outside tests | *[measured]* `grep -rn` |
| DRIFT-034's label | `RecommendationOutcome`: **0** hits in `agents`, `contracts`, `orchestration`, `kernel`, `surfaces` | *[measured]* `grep -rln` |
| DRIFT-037's strings | the PM emits `sector_concentration` and `reward_risk_below_min` | *[measured, read]* `agents/portfolio_manager/domain/` |
| DRIFT-061's shapes | `Fill`: ticker, side, quantity, price, broker_order_id, status. `ExecutionResult`: run_id, stage, fills, submitted, rejected, dropped, skipped, provenance. `ReconcileResult`: matched, discrepancies, provenance. `PromoteStageResult`: accepted, previous_stage, current_stage, reason, provenance | *[measured, read]* `contracts/execution.py:36-73` |
| DRIFT-031's schemas | still four test-plan table layouts across 14 agent books; the reporter's `RPT-TYP-03` now has its row | *[measured]* the header row of each `test-plan.md` |
| Where the non-agent books live | `orchestration/laws/dispatcher/`, `surfaces/laws/`, `docs/laws/dependencies.md` (`DEP-BUS-01..04`) | *[measured]* |
| Ledger versions that disagree with the books | reporter: book **v1.3**, ledger v1.2; supervisor: book **v1.2**, ledger v1.1 | *[measured]* the `**Prefix:**` line of each `laws.md` against `docs/laws/ledger.md` |
| Whether the gate reads `dependencies.md` | **not measured** | *[ASSUMED not]* `scripts/check_law_coverage.py` has no reference to it; confirm before relying on it |

---

## Scope — the 23 rows, each with its ruling

Rulings are the planner's ([DL-259](../design-log.md)). **A** = amend the clause to what the code does.
**N** = narrow the clause to what is true. **W** = waits for a feature; the row becomes `DECIDED`.

| Row | Book | Ruling | What to do |
| --- | --- | --- | --- |
| 082 | provider | A | Widen `PROV-TRG-01`: the provider acts on a recorded data need (a request event, a `RunRequest`, or an `AnalystRun`'s qualifying buys). Keep it 🟩: cite it in a graph-pull test as well as the pub/sub one |
| 084 | provider | A | State in the `OUT` clause that describes a bar that served bars are **raw** (no adjustment requested). Prove it on the request the Alpaca source builds |
| 085 | scanner | A | Name the graph-pull trigger in `SCAN-TRG`: a `MarketData` with no `SCANNED_BY` edge is a request |
| 086 | analyst, PM, monitor, reporter, provider | A | Name each book's graph-pull trigger in its `TRG-02`. Add to each: pending work is found by key and edge, and props are fetched for pending items only (`tests/test_poll_payloads.py`). The bound lives in each agent's clause, not in a system book |
| 077 | dispatcher | A | Add the daily brief to `DSP-IDN-03`'s scope sentence and to the purpose line |
| 087 | reporter | A | `RPT-OUT-07`: the benchmark bars are the run's own `MarketData`'s, reached by lineage; a missing one is "missing benchmark", never another run's |
| 076 | supervisor | A | `SUP-OBS-02`: `open_incidents` comes from live `Fault` incidents (DL-208); `pending_human_flags` from unresolved critical `Flag`s |
| 078 | surfaces | N | `SRF-OUT-03` covers operator-mediated answers. Name the quick asks as graph reads that write no audit facts |
| 081 | forecaster | A | `FORE-IDN-01` names the four legs. `FORE-OBS-01`: one recorded node per prediction (`ShadowPrediction`, or `BarrierForecast` for a barrier claim) |
| 083 | forecaster | N | `FORE-IDM-03`'s subject is the three shadow scorecards; `FORE-IDM-05` keeps the barrier one |
| 037 | PM | A | `PM-OUT-03`'s examples use the emitted strings (`sector_concentration`, `reward_risk_below_min`) |
| 065 | PM | N | `PM-OBS-04` is per evaluated candidate: it discloses reachability from the evidence that candidate had. It does not claim a gate can fail somewhere in its population |
| 039 | PM | N | `PM-OBS-01`, `PM-OUT-06`, `PM-STA-04` claim only what `PMRun` carries. Remove the `portfolio_state_snapshot` promise; name execution's `BrokerPositionSnapshot` as where the run's pre-trade book is recorded |
| 074 | analyst | A | A new `ANLZ` clause for the held-position stop check (ADR-0017), citing `tests/test_stop_width.py::test_all_three_readers_agree_on_the_decided_stop` and an analyst test of the check itself |
| 061 | execution | A | `EXEC-OUT-01`, `-02`, `-04`, `-05` name the fields the contract carries today |
| 094 | execution, supervisor, `contracts/execution.py` | A | Declare the exception: execution may write divergence-family `Flag` and `FlagResolution` nodes. Amend `SUP-IDN-02`, execution's CAP block and `owns_graph`. Nothing else in `contracts/` moves |
| 060 | every book that names `CONTRACT.version` | N | Those clauses mean the current schema's identity. No clause promises that the version moves with the shape; no gate is added |
| 040 | provider | N | `PROV-OUT-04` promises fetch time and the fallback flag. It no longer promises the vendor or a transformation. The gap itself is filed as work-queue 105, not hidden |
| 059 | master | A | One clause for what is true today: master refuses to start in a remediation mode it cannot honour (`agents/master/remediation_posture.py`, with its test). Say in the book that attempting remediation is outside the constitution until DL-36 Pieces C and D are built |
| 032 | `docs/laws/dependencies.md` | A | A new `DEP-BUS` clause: a local test run never transacts with the production Service Bus. Cite the existing guard's test |
| 031 | — | W→DECIDED | The four test-plan layouts stay; the gate parses all four since S204 and every clause has a row. The reporter mismatch is already fixed. No file changes but the row |
| 030 | — | W | No kernel law book exists to hold a retry and quarantine envelope. `DECIDED`: owed when a substrate book is authored (next-leg E20.3). Do not create the book here |
| 034 | — | W | `RecommendationOutcome` does not exist. `DECIDED`: the sprint that builds it owns its law cycle |

Also in scope: the two ledger versions that disagree with their books (measured above), and every
version this sprint bumps, in `ledger.md` and `INDEX.md`.

### Out of scope (do NOT build this sprint)

- **Any behaviour change.** Not the snapshot of DRIFT-039, not the vendor field of DRIFT-040, not a
  contract-version gate, not a supervisor capability for flags.
- **A kernel or substrate law book.** That is E20.3's.
- **Unifying the test-plan layouts.** Fourteen files of churn for no proof gained.
- **Rewording a clause the table does not name**, however tempting. File a new drift row instead.
- **`docs/laws/_TEMPLATE.md`.** Not edited.
- **No ADR reversal.**

### The road not taken (LAW-06)

In [DL-259](../design-log.md), per row. The general ones:

- **Build what the old clauses promised.** Rejected for this sprint: each is a feature with its own
  spec, and under the fixes-before-features rule a law that overstates is repaired by stating less.
- **One sprint per book.** Rejected: thirteen gate cycles for text.
- **Leave rows that wait as `OPEN`.** Rejected: `OPEN` means a decision is owed. These have one.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **The wording of each amended clause.** Yours, within the ruling. Keep each clause falsifiable.
2. **Which test proves each reworded 🟩 clause**, and where a new test is needed.
3. **For a new clause with no test today: write the test, or leave the row ⬜.** State which, per clause.
4. **Whether `docs/laws/dependencies.md` takes a test-plan row for the new `DEP-BUS` clause**, after
   measuring whether the gate reads that file.
5. **Any row you found stale**, and what you did instead.

🪤 **Take the next free DL number, then re-check it at merge.** `DL-260` at spec time; `DL-258` is
reserved for S250.

---

## Blast radius — measured 2026-10-01

| What | Detail |
| --- | --- |
| Files changed | 13 law books and their test-plans (provider, scanner, analyst, PM, monitor, reporter, execution, supervisor, forecaster, master, dispatcher, surfaces, `docs/laws/dependencies.md`); `contracts/execution.py` (`owns_graph`); test docstrings and a few new tests; `docs/laws/drift-register.md`, `ledger.md`, `INDEX.md`; `docs/design-log.md`; this file and its README row |
| Agents affected | none in behaviour |
| Contract change? | Yes: execution's `owns_graph` gains two labels |
| Graph vocabulary change? | No. The vocabulary pack is not touched; its `owners` map stays empty |
| New env keys / tunables | None |
| Deploy implication | Image-only retag at the next deploy; nothing here needs one |
| Rollback | Revert the merge. No graph write, order or setting changes |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Confirm each row against the code.** Note any that are stale.
3. **Record the design decisions** in `docs/design-log.md`.
4. **One book at a time, one commit a book:** clauses, version, Changelog, test-plan, citing tests,
   then that book's drift rows. Run `uv run python scripts/check_law_coverage.py` after each.
5. **Prove the guards can fail (DL-70)** — the plants in the handover.
6. **`make ci` green** — every step, **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| D1 | 🎯 No row is open | the register after the sprint | no status cell begins `OPEN` or `PARTLY`; each of the 23 names S251 and its ruling |
| D2 | 🎯 Behaviour is untouched | `git diff main -- agents kernel orchestration surfaces contracts`, law books and tests excluded | only `contracts/execution.py`'s `owns_graph` differs |
| D3 | A reworded proven clause is still proven | each 🟩 clause the table amends | its test-plan row names a test whose docstring cites it and whose assertions match the new wording |
| D4 | `PROV-TRG-01` holds on graph-pull | a `RunRequest` on the graph, no bus event | the provider ingests it; with no request of any kind it does nothing |
| D5 | Served bars are raw | the request the Alpaca source builds | no adjustment is asked for |
| D6 | The held-stop clause | a held position at and beyond its decided stop | the analyst's check reports the breach from the shared stop-width resolver |
| D7 | Execution's declared labels match what it writes | `contracts/execution.py` `owns_graph`; the divergence flag writer | both labels are declared; the supervisor's clause names the exception |
| D8 | Master refuses a mode it cannot honour | `remediation_mode='automatic'` with the guard unwired | startup is refused; the test cites the new clause |
| D9 | A test run never reaches the production bus | the existing pytest guard | cited by the new `DEP-BUS` clause |
| D10 | Rollups and versions agree | every book touched | `laws.md`, `ledger.md` and `INDEX.md` carry the same version; the counts are the gate's |

---

## Success factors

- [ ] No `OPEN` or `PARTLY` status in the drift register (D1), or each remaining one named with its reason.
- [ ] No behaviour change (D2).
- [ ] Every amended book: version bumped, Changelog line naming its DRIFT rows, test-plan rows, rollups in both files.
- [ ] Reporter and supervisor versions agree between book, ledger and INDEX.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Each guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

**Owed to the planner, not the builder:** `uv lock` with the PATCH bump, Windows `make ci`,
`make gate-ran`, the merge. **F1** (after merge): the planner re-reads five amended clauses of its own
choosing against the live graph or the running code, and files work-queue 105 if it is not there.

---

## Traps

🪤 **Demoting a 🟩 clause by rewording it.** A clause is green only while a test cites it and proves
what it now says. Reword, then re-read the test.
🪤 **A clause for an unbuilt feature.** That is the unfalsifiable-claim defect. Where the code does
less than the old clause said, the clause says less.
🪤 **IDs are append-only** (conventions §2). Never renumber or reuse; a new clause takes the next free
ID in its section.
🪤 **The IDE reformats markdown tables on open.** Check `git diff -w` shows no deletion you did not
make, and that line endings stay LF.
🪤 **A drift row's history is evidence.** Rewrite the status cell and keep "Was: OPEN (…)" in it.
🪤 **`check_law_coverage` fails on a clause with no row.** Add the row in the same commit as the clause.
🪤 **Thirteen books in one branch.** Commit per book so a mistake is one revert, not the sprint.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it (the planner's).
- Secrets never through the worktree. **State which tree you ran in.**
- 🪤 `make ci` does not run markdownlint and the commit hook does. Leave a blank line before and
  after every fenced code block.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the proving worktree.
2. Merge to `main` locally and push.
3. Post-merge CodeQL on `main`.
4. No deploy of its own; the next retag carries `owns_graph`.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 251 — every open drift row is decided: the law says what the code does, or the row says what
it waits for. Spec: docs/sprints/sprint-251-every-open-drift-row-is-decided.md on main (read ALL of
it, then CLAUDE.md, then DL-259 in docs/design-log.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-251-every-open-drift-row-is-decided, cut from main. Never main. If your session forces
another branch name, use it and name it in the handback.
You have NO .env, NO gh and no route to download.pytorch.org. You cannot run `make gate-ran`: it is
owed to the planner. Leave pyproject.toml's version and uv.lock untouched and say so. Take the next
free DL (DL-260 at spec time; DL-258 is reserved for another sprint; re-check on main).

This handover is complete: nobody will send you follow-up messages. If a row cannot be closed as
ruled, leave it OPEN, say why in its status cell and in Return notes, and go on to the next row.

What and why: docs/laws/drift-register.md holds 22 OPEN rows and one PARTLY CORRECTED. Each records a
law clause that no longer describes the code, found by a sprint whose law book was read-only. This
sprint is the law cycle that closes them. The spec's row table gives the planner's ruling for each of
the 23: amend the clause to what the code does (A), narrow it to what is true (N), or mark the row
DECIDED because it waits for a feature that does not exist (W).

MUST RULE before any edit: read, whole, docs/laws/conventions.md, docs/laws/drift-register.md,
docs/laws/_TEMPLATE.md, and laws.md + test-plan.md for provider, scanner, analyst, portfolio_manager,
monitor, reporter, execution, supervisor, forecaster, master, orchestration/laws/dispatcher,
surfaces/laws, and docs/laws/dependencies.md. For each row, read the code it describes and confirm
the row is still true. Fill the Law reading record first.

Law-cycle answer: YES, per book: version bump, Changelog line naming the DRIFT rows, a test-plan row
per clause, the clause ID in each citing test's docstring, rollups in docs/laws/ledger.md AND
docs/laws/INDEX.md (let make ci give the counts). Also bring the reporter and supervisor versions in
ledger.md into line with their books.

THE ONE INVARIANT: no behaviour changes. Under agents/, kernel/, orchestration/, surfaces/ you may
change only law books, tests and docstrings. The single exception is contracts/execution.py's
owns_graph (DRIFT-094: add the two labels execution already writes). If a row seems to need a code
change, that row stays OPEN.

Order: next free DL (your wording and test choices, with rejected alternatives) -> one book at a
time, ONE COMMIT A BOOK (clauses, version, Changelog, test-plan, citing tests, that book's drift
rows; run `uv run python scripts/check_law_coverage.py` after each) -> DL-70 plants, each red,
pasted, restored:
  (a) remove a new clause's test-plan row: check_law_coverage red;
  (b) remove the clause citation from a test that proves a reworded green clause: the gate's rollup
      for that book drops, shown;
  (c) make the provider ignore a RunRequest in the D4 test's fixture path: D4 red;
  (d) drop one label from owns_graph: D7 red
-> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- change runtime behaviour, a tunable, an env key, a graph label or the vocabulary pack.
- write a clause for something the code does not do. Where the code does less, the clause says less.
- reword a clause the row table does not name. File a new drift row instead.
- renumber or reuse a clause ID. IDs are append-only.
- create a kernel or substrate law book; unify the test-plan layouts; edit docs/laws/_TEMPLATE.md.
- delete a drift row's history: rewrite the status cell and keep "Was: OPEN (...)".
- claim a live proof or GATE PROVEN: those are the planner's.
- pin a version: PATCH, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including which rows you found stale.
[ ] A table of all 23 rows: ruling, clause(s) amended, the citing test, final status, commit.
[ ] Test plan results: D1-D10, each with final test name or check, file, PASS.
[ ] The diff proof for D2 (the command and its output).
[ ] Each DL-70 plant: what was planted, its red output, restored.
[ ] The DL number used, with your decisions and their rejected alternatives.
[ ] Every book's version before and after, and the rollup before and after, as the gate printed them.
[ ] Module line counts for every Python file touched (all < 200).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how pyproject.toml and uv.lock were touched (untouched and owed, or what changed).
[ ] Rows left OPEN, each with its reason, or "none".
[ ] Status: BUILT in this file and in its docs/sprints/README.md row, in the same commit.
[ ] A blank line before and after every fenced code block in this file (the commit hook lints it).
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first edit.
2. Fill the **Test plan results** table and the 23-row table.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`, here and in the README row.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| *(builder fills)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(builder fills)*

**Contradictions found between a law and this spec:** *(builder fills)*

**Rows found stale, and what was done:** *(builder fills)*

**Clauses that were ⬜ and are now proven:** *(builder fills)*

---

## The 23 rows — fill at handback

| Row | Ruling | Clause(s) amended | Citing test | Final status | Commit |
| --- | --- | --- | --- | --- | --- |
| *(builder fills)* | | | | | |

---

## Test plan results — fill at handback

| Plan # | Final test name or check | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| *(builder fills)* | | | | |

**Tests added beyond the plan:** *(builder fills)*

---

## Closeout — evidence

*(builder fills every field below; a field left as written here returns the handback)*

**Tree the proofs ran in (and `.env` present?):**

**Result:**

**Files changed:**

**Design decisions:**

**Behaviour untouched — the diff proof:**

**Guards planted:**

**Versions and rollups, before and after:**

**Module line counts:**

**`make ci`:**

**`pyproject.toml` and `uv.lock`:**

**Owed to the planner:**

**Rows left OPEN:**

---

## Return notes

*(builder fills)*
