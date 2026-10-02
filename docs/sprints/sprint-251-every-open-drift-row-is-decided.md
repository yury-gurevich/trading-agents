<!-- Agent: planning | Role: sprint handover -->
# Sprint 251 — every open drift row is decided: the law says what the code does, or the row says what it waits for

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 104
**Branch:** `sprint-251-every-open-drift-row-is-decided`
**Status:** MERGED 2026-10-02 — `0.121.01`, fast-forwarded to `d526faf4`, tag `v0.121.01`, GATE PROVEN `d526faf4` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,932 passed, 8 skipped, 100.00 %); built by a Claude cloud session on `claude/compassionate-hamilton-g1wdjb`, one commit a law book; all 23 ruled rows decided across 13 books, no behaviour change (the only code edit is execution's `owns_graph`); DRIFT-098 closed by the planner at merge; **two rows remain open**, both filed during the sprint: DRIFT-096 and DRIFT-097 (work-queue 106); deployed with `s251` 2026-10-02
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
| 096 | analyst | A | Filed by S250 (2026-10-01), after this table was written. State what the code does with a candidate whose bars cover fewer sessions than `required_history_bars`: it is scored, each indicator that lacks history is absent and visible as a `*_missing_bars` metric, and only fewer than `min_history_bars` rejects. Cite an existing analyst test of that path |

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

Read whole, 2026-10-01, before the first edit: `docs/laws/conventions.md`, `drift-register.md`,
`_TEMPLATE.md`, `dependencies.md`, `ledger.md`, `INDEX.md`, and `laws.md` + `test-plan.md` of the 12
books below. Also read the gate itself (`scripts/check_law_coverage.py`, `law_coverage_docs.py`,
`law_coverage_tests.py`, `law_coverage_status.py`) and the code each row describes.

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| provider | `agents/provider/laws/laws.md` v1.7, `test-plan.md` | `PROV-TRG-01/02`, `PROV-OUT-04`, `PROV-OUT-07` | Yes. `PROV-TRG-02` already names a `RunRequest` (v1.5), so DRIFT-082 is `TRG-01` only. The only live OHLCV source is Alpaca (`composite.py`), so "raw" goes in `PROV-OUT-07`, the clause that describes a bar. `PROV-OUT-04` can turn green: the `MarketSnapshot` does carry `created_at` and `used_fallback` |
| scanner | `agents/scanner/laws/laws.md` v1.3, `test-plan.md` | `SCAN-TRG-02`, `SCAN-TYP-01` | `SCAN-TRG-02` called pub/sub "the primary production trigger path", which is false. It is amended with the graph-pull trigger. `SCAN-TYP-01` carries DRIFT-060's sentence |
| analyst | `agents/analyst/laws/laws.md` v1.6, `test-plan.md` | `ANLZ-TRG-02`, new `ANLZ-OUT-09` | Yes. The held-stop check (`domain/analyze.py::_stop_breached`) skips a position whose broker stop is live, and a book with no readable stop inputs is a fault and an empty result. Both go in the clause, because the code does them. ADR-0017's four `test_exit_authority.py` tests cited no clause |
| portfolio_manager | `agents/portfolio_manager/laws/laws.md` v1.10, `test-plan.md` | `PM-TRG-02`, `PM-OUT-03`, `PM-OUT-06`, `PM-OBS-01`, `PM-OBS-04`, `PM-STA-04`, `PM-TYP-03` | Yes. `PM-OUT-01` and `PM-TYP-03` also list `portfolio_state_snapshot` as an `OrderIntentSet` field, which the contract does not carry. Neither is named for that by the row table, so I filed it as **DRIFT-098** and did not reword them |
| monitor | `agents/monitor/laws/laws.md` v1.1, `test-plan.md` | `MON-TRG-02` | Yes. The end-of-run poll finds work by key and edge. Its second work kind, position sync (`position_sync.py::find_pending_position_sync`), lists every `BrokerPositionSnapshot` with props and walks each one's edges. So the bound is stated for `ExecutionRun` work only, and the sync poll is filed as **DRIFT-097** |
| reporter | `agents/reporter/laws/laws.md` v1.3, `test-plan.md` | `RPT-TRG-02`, `RPT-OUT-07`, `RPT-IDM-03` | The ledger says v1.2 while the book says v1.3. The reporter's poll fetches every position-sync `MonitorRun` and then drops it (they never gain `REPORTED_BY`), so the clause says so |
| execution | `agents/execution/laws/laws.md` v1.10, `test-plan.md`; `contracts/execution.py` | `EXEC-OUT-01/02/04/05`, `EXEC-TYP-03`, CAP; new `EXEC-IDN-04` | Yes. `tests/test_boundary_map.py::test_each_graph_label_has_one_writer` fails when two contracts own one label. Adding the two labels to `owns_graph` needs that test changed to name the one declared exception. `owns_graph` has no runtime reader (grep: only `kernel/contract.py` and tests), so adding labels changes no behaviour |
| supervisor | `agents/supervisor/laws/laws.md` v1.2, `test-plan.md` | `SUP-IDN-02`, `SUP-OBS-02` | The ledger says v1.1 while the book says v1.2. Independence rule (conventions §5): the clause names the divergence *family* and a role, never another agent |
| forecaster | `agents/forecaster/laws/laws.md` v1.8, `test-plan.md` | `FORE-IDN-01`, `FORE-OBS-01`, `FORE-IDM-03` | No test covers the return leg's node, so `FORE-OBS-01` stays ⬜ with the partial named |
| master | `agents/master/laws/laws.md` v1.7, `test-plan.md` | new `MST-FAIL-07`; `PARAM` `remediation_mode` | The `PARAM` rationale promised "one remediation shot" under `automatic`, which the code refuses. Corrected as part of DRIFT-059 |
| dispatcher | `orchestration/laws/dispatcher/laws.md` v1.1, `test-plan.md` | `DSP-IDN-03`, purpose line | No |
| surfaces | `surfaces/laws/laws.md` v1.2, `test-plan.md` | `SRF-OUT-03` | Yes. "explain this run" is a quick ask too, but the model composes it, so it stays inside the audited half |
| dependencies | `docs/laws/dependencies.md` | new `DEP-BUS-05` | Yes. The gate never reads this file: `_law_book_paths` globs `agents/*/laws`, `orchestration/laws/*` and `surfaces/laws` only. The guard (`conftest.py`) blocks **sends** only, so the clause says send, not "transact" |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes, for 13
books. `contracts/execution.py`'s `owns_graph` gains `Flag` and `FlagResolution`, and nothing else in
`contracts/` moves. Three new clauses are added: `ANLZ-OUT-09`, `EXEC-IDN-04` and `MST-FAIL-07`, plus
`DEP-BUS-05` in the charter. Each one states a guarantee the code already keeps.

**Contradictions found between a law and this spec:** (1) The spec's DRIFT-039 ruling names
`PM-OBS-01`, `PM-OUT-06` and `PM-STA-04`. `PM-OUT-01` and `PM-TYP-03` make the same false field claim,
and `PM-TYP-03` is 🟩 on it. They are left as they are and filed as DRIFT-098. (2) The handover says
"a test run never transacts with the production Service Bus". The guard covers sends only, so
`DEP-BUS-05` says "sends". (3) Execution's book comment says Flag keys are "supervisor-owned", and the
contract test forbade a shared label. Both are resolved by the declared exception (DRIFT-094).

**Rows found stale, and what was done:** DRIFT-031's reporter half is stale: `RPT-TYP-03` has its row,
so only the layout question remains, and it is DECIDED. DRIFT-081's `IDN-02` third was already
corrected in S241, so only `IDN-01` and `OBS-01` were amended. DRIFT-086's provider half was mostly
done: `PROV-TRG-02` v1.5 names the `RunRequest`, and S251 adds the poll's bound. No row was false as
filed.

**Clauses that were ⬜ and are now proven:** `PROV-TRG-02`, `PROV-OUT-04`, `SUP-OBS-02`, and the new
`ANLZ-OUT-09`, `EXEC-IDN-04` and `MST-FAIL-07`. The test-plan results below give the citing tests.

---

## The 23 rows — fill at handback

| Row | Ruling | Clause(s) amended | Citing test | Final status | Commit |
| --- | --- | --- | --- | --- | --- |
| 082 | A | `PROV-TRG-01` (🟩) | `test_graph_pull_trigger.py::test_a_recorded_run_request_is_ingested_with_no_bus_event` + the pub/sub test | CORRECTED | `d38be32` |
| 084 | A | `PROV-OUT-07` (🟩) | `test_alpaca_raw_bars.py::test_the_bars_request_asks_for_no_price_adjustment` | CORRECTED | `d38be32` |
| 040 | N | `PROV-OUT-04` (⬜ → 🟩) | `test_served_fact_provenance.py::test_a_served_fact_links_to_its_fetch_time_and_fallback_flag` | CORRECTED (gap = work-queue 105) | `d38be32` |
| 085 | A | `SCAN-TRG-02` (🟩) | `test_scanner_poll.py` (3) + `tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work` | CORRECTED | `2349da0` |
| 086 | A | `PROV-TRG-02` (⬜ → 🟩), `SCAN-TRG-02`, `ANLZ-TRG-02`, `PM-TRG-02`, `MON-TRG-02`, `RPT-TRG-02` (🟩) | each agent's poll tests + `tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work` | CORRECTED (monitor sync poll filed as DRIFT-097) | `d38be32`…`34f54c7` |
| 074 | A | new `ANLZ-OUT-09` (🟩) | `tests/test_analyst_held_stop.py` (3 tests, 4 cases), `test_exit_authority.py` (4), `tests/test_stop_width.py::test_all_three_readers_agree_on_the_decided_stop` | CORRECTED | `fe590b7` |
| 037 | A | `PM-OUT-03` (🟩) | `test_sector_cap.py::test_rejects_second_same_sector_order_over_cap`, `test_reward_risk.py::test_rejects_when_reward_risk_below_minimum` | CORRECTED | `7fb20b0` |
| 065 | N | `PM-OBS-04` (🟩) | its five existing tests, unchanged | CORRECTED | `7fb20b0` |
| 039 | N | `PM-OBS-01` (🟩), `PM-OUT-06` (⬜), `PM-STA-04` (⬜ → 🟩) | `test_pm_run_record.py::test_a_pm_run_carries_its_order_intent_set_and_no_portfolio_snapshot`, `test_pm_pubsub.py::test_order_intent_result_is_deserializable` | CORRECTED (`PM-OUT-01`/`PM-TYP-03` → DRIFT-098) | `7fb20b0` |
| 087 | A | `RPT-OUT-07` (🟩) | `test_benchmark_lineage.py` (2) + its six existing tests | CORRECTED | `34f54c7` |
| 061 | A | `EXEC-OUT-01`, `-02`, `-04`, `-05` (🟩) | existing tests + `tests/test_contract_required_payload_fields.py::test_execution_payload_fields_required_by_law` | CORRECTED | `cfa989d` |
| 060 | N | `SCAN-TYP-01`, `PM-TYP-03`, `EXEC-TYP-03` (🟩) | their existing required-field tests | CORRECTED | `2349da0`, `7fb20b0`, `cfa989d` |
| 094 | A | new `EXEC-IDN-04` (🟩), `SUP-IDN-02` (🟩), execution CAP, `contracts/execution.py` `owns_graph` | `test_divergence_flag_ownership.py::test_every_label_the_divergence_writer_writes_is_declared`, `tests/test_boundary_map.py::test_each_graph_label_has_one_writer` | CORRECTED | `cfa989d`, `b0787b8` |
| 076 | A | `SUP-OBS-02` (⬜ → 🟩) | `test_supervisor_health_sources.py::test_open_incidents_count_faults_and_pending_flags_count_critical_flags` + three health tests | CORRECTED | `b0787b8` |
| 081 | A | `FORE-IDN-01`, `FORE-OBS-01` (both ⬜, partials named) | none whole (return leg uncovered) | CORRECTED | `288333e` |
| 083 | N | `FORE-IDM-03` (⬜) | none (no repeatability test) | CORRECTED | `288333e` |
| 059 | A | new `MST-FAIL-07` (🟩) + "outside the constitution" paragraph + `PARAM` rationale | `test_remediation_posture.py` (3) | CORRECTED | `f0a6a03` |
| 077 | A | `DSP-IDN-03` (⬜), purpose line | none | CORRECTED | `1b39f73` |
| 078 | N | `SRF-OUT-03` (🟩) | `test_chat_quick_asks.py::test_a_quick_ask_is_a_graph_read_that_writes_no_audit_fact` + the audited-answer test | CORRECTED | `cba7d09` |
| 032 | A | new `DEP-BUS-05` (charter; no test-plan, the gate does not read it) | `tests/test_pytest_servicebus_guard.py` (3) + `conftest.py` fixture | CORRECTED | `697787f` |
| 031 | W→DECIDED | none | n/a | DECIDED | `a075a35` |
| 030 | W | none | n/a | DECIDED (owed with E20.3) | `a075a35` |
| 034 | W | none | n/a | DECIDED (owed by `RecommendationOutcome`'s sprint) | `a075a35` |

---

## Test plan results — fill at handback

| Plan # | Final test name or check | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| D1 | script over every `\| DRIFT-` row: none of the 23 has a status cell starting `OPEN`/`PARTLY`; each names S251 and its ruling (output below) | `docs/laws/drift-register.md` | PASS (the only OPEN rows are DRIFT-098/097, filed by this sprint) | n/a |
| D2 | `git diff --stat origin/main -- agents kernel orchestration surfaces contracts` minus `*/laws/*` and `*/tests/*` | (below) | PASS: only `contracts/execution.py`, +5 lines in `owns_graph` | n/a |
| D3 | `scripts/check_law_coverage.py` exit 0 after every book; each reworded 🟩 row names a test whose docstring cites it and asserts the new wording | every `test-plan.md` | PASS | per row above |
| D4 | `test_a_recorded_run_request_is_ingested_with_no_bus_event`, `test_an_idle_graph_asks_the_feed_for_nothing` | `agents/provider/tests/test_graph_pull_trigger.py` | PASS | `PROV-TRG-01`, `PROV-TRG-02` |
| D5 | `test_the_bars_request_asks_for_no_price_adjustment[sip/iex]` | `agents/provider/tests/test_alpaca_raw_bars.py` | PASS | `PROV-OUT-07` |
| D6 | `test_a_close_at_or_beyond_the_decided_stop_is_a_forced_stop_sell` (at 58.06; beyond at 57.60, still above the fallback stop 57.47), `test_a_close_above_the_decided_stop_is_no_stop_exit`, `test_a_position_with_a_live_broker_stop_is_left_to_that_stop` | `tests/test_analyst_held_stop.py` | PASS | `ANLZ-OUT-09` |
| D7 | `test_every_label_the_divergence_writer_writes_is_declared`; `test_each_graph_label_has_one_writer` | `agents/execution/tests/test_divergence_flag_ownership.py`; `tests/test_boundary_map.py` | PASS (red before the `owns_graph` edit) | `EXEC-IDN-04`, `SUP-IDN-02` |
| D8 | `test_automatic_remediation_refuses_a_master_that_cannot_remediate` (+2) | `agents/master/tests/test_remediation_posture.py` | PASS | `MST-FAIL-07` |
| D9 | `test_pytest_guard_rejects_live_servicebus_send` (+2) | `tests/test_pytest_servicebus_guard.py` | PASS | `DEP-BUS-05` |
| D10 | script comparing each book's `**status:** LOCKED vX` with its `ledger.md` and `INDEX.md` row; counts are the gate's (`_derived_counter`) | `docs/laws/ledger.md`, `docs/laws/INDEX.md` | PASS, 12 of 12 books | n/a |

**Tests added beyond the plan:** `agents/provider/tests/test_served_fact_provenance.py` (`PROV-OUT-04`, clean and degraded);
`agents/portfolio_manager/tests/test_pm_run_record.py` (`PM-STA-04`/`PM-OBS-01`);
`agents/supervisor/tests/test_supervisor_health_sources.py` (`SUP-OBS-02`);
`surfaces/tests/test_chat_quick_asks.py` (`SRF-OUT-03`, four asks).
`agents/analyst/tests/test_analyst_poll_processed.py` is an existing test moved, unchanged, out of a
file that reached 200 lines. Changed test assertions: one, in `tests/test_boundary_map.py::test_each_graph_label_has_one_writer`,
which now allows exactly the declared `Flag`/`FlagResolution` pair shared by `execution` and
`supervisor`, where before it allowed no shared label. Everything else is docstring citations.

---

## Closeout — evidence

*(builder fills every field below; a field left as written here returns the handback)*

**Tree the proofs ran in (and `.env` present?):** a claude.ai cloud container, `/home/user/trading-agents`
on branch `claude/compassionate-hamilton-g1wdjb` (the session forced this name instead of
`sprint-251-every-open-drift-row-is-decided`). No `.env`. The `uv` environment was synced from the
unchanged `uv.lock`.

**Result:** All 23 rows are CORRECTED (20) or DECIDED (3), and no runtime behaviour differs from
`main`. Seven more clauses are green: four existing ones moved ⬜ → 🟩 (`PROV-TRG-02`, `PROV-OUT-04`,
`PM-STA-04`, `SUP-OBS-02`), and three new clauses were added already proven (`ANLZ-OUT-09`,
`EXEC-IDN-04`, `MST-FAIL-07`). Two new rows were filed OPEN, each a finding the row table did not cover: DRIFT-098 and
DRIFT-097. Not done: live proof (F1, the planner's).

**Files changed:** 12 `laws.md` + their `test-plan.md`; `docs/laws/dependencies.md`,
`drift-register.md`, `ledger.md`, `INDEX.md`; `contracts/execution.py` (`owns_graph`); nine new test
files (listed under module line counts; one is a moved test); citation-only docstring edits in 20
existing test modules and `conftest.py`; `tests/test_boundary_map.py` (one assertion); `docs/design-log.md`
(DL-260); this file, `docs/sprints/README.md`, `docs/sprints/INDEX.md`.

**Design decisions:** [DL-260](../design-log.md) (DL-258 stayed reserved; DL-260 was free on `main`
at `b050f706`). Fifteen decisions, each with what was rejected. The main ones: each book's own `TRG-02`
carries the bound. The monitor's bound covers `ExecutionRun` work only, so the sync poll is DRIFT-097.
"Raw" goes in `PROV-OUT-07`. The DRIFT-094 exception is declared by family, and the boundary-map test
allows exactly that pair. `DEP-BUS-05` says "sends", not "transacts". `PM-OUT-01`/`PM-TYP-03` are not
reworded; they are DRIFT-098. The forecaster's three clauses stay ⬜.

**Behaviour untouched — the diff proof:**

```text
$ git diff --stat origin/main -- agents kernel orchestration surfaces contracts ":(exclude)*/laws/*" ":(exclude)*/tests/*"
 contracts/execution.py | 5 +++++
 1 file changed, 5 insertions(+)
$ git diff origin/main -- contracts
@@ -118,6 +118,11 @@ CONTRACT = AgentContract(
         "BrokerStopOrder",
+        # Shared with the supervisor for one family only: the run-start
+        # broker-position divergence Flags and the FlagResolutions that close them
+        # (EXEC-IDN-04, DRIFT-094).
+        "Flag",
+        "FlagResolution",
     ),
```

`owns_graph` has no runtime reader (grep: `kernel/contract.py` declares it; only tests read it). The
vocabulary pack's `owners` map is untouched. Outside those five trees, the only non-doc, non-test
change is a `conftest.py` docstring.

**Guards planted:** each was planted, watched fail, and restored with `git checkout`, and each
restore was re-run green.

(a) The new `ANLZ-OUT-09` row deleted from the analyst test-plan:

```text
[FAIL] docs/laws/ledger.md:40: analyst claims 27 / 50; derived 26 / 50
[FAIL] docs/laws/INDEX.md:41: analyst claims 27 / 50; derived 26 / 50
[FAIL] law coverage: 1 clause(s) have no test-plan row (assertion E)
[FAIL] agents/analyst/laws/test-plan.md: 1 missing row(s): ANLZ-OUT-09
exit=1
```

(b) `PROV-OUT-04` (reworded and now green) stripped from both its citing tests' docstrings, then the
row demoted as the gate demands. The provider's derived rollup drops:

```text
[FAIL] agents/provider/laws/test-plan.md:35: PROV-OUT-04 no resolved test docstring names PROV-OUT-04: agents/provider/tests/test_served_fact_provenance.py::test_a_served_fact_links_to_its_fetch_time_and_fallback_flag, agents/provider/tests/test_provider_agent.py::test_get_market_data_round_trips_and_writes_provenance
exit=1
--- row demoted to ⬜:
[FAIL] docs/laws/ledger.md:38: provider claims 24 / 67; derived 23 / 67
[FAIL] docs/laws/INDEX.md:40: provider claims 24 / 67; derived 23 / 67
exit=1
```

(c) The provider ignores every `RunRequest` (`poll.find_pending` returns `[]`). D4 goes red and the
idle half stays green:

```text
E   AssertionError: assert [] == [('ingest', 'run-request:r1')]
E     Right contains one more item: ('ingest', 'run-request:r1')
1 failed, 1 passed in 0.40s
```

(d) `"FlagResolution"` dropped from `owns_graph`. D7 goes red. It was also red before the edit was
made, on both labels:

```text
E   AssertionError: assert {'BrokerPosit...agResolution'} <= {'BrokerOrder..., 'Flag', ...}
E     Extra items in the left set:
E     'FlagResolution'
1 failed in 0.49s
```

**Versions and rollups, before and after** (the gate's `_derived_counter`, run on `origin/main` and on
HEAD):

| Book | Version before → after | Rollup before → after |
| --- | --- | --- |
| provider | v1.7 → v1.8 | 22 / 67 → 24 / 67 |
| scanner | v1.3 → v1.4 | 18 / 41 → 18 / 41 |
| analyst | v1.6 → v1.7 | 26 / 49 → 27 / 50 |
| portfolio_manager | v1.10 → v1.11 | 32 / 51 → 33 / 51 |
| monitor | v1.1 → v1.2 | 21 / 46 → 21 / 46 |
| reporter | v1.3 (ledger and INDEX said v1.2) → v1.4 | 25 / 42 → 25 / 42 |
| execution | v1.10 → v1.11 | 38 / 64 → 39 / 65 |
| supervisor | v1.2 (ledger and INDEX said v1.1) → v1.3 | 22 / 48 → 23 / 48 |
| forecaster | v1.8 → v1.9 | 25 / 52 → 25 / 52 |
| master | v1.7 → v1.8 | 24 / 50 → 25 / 51 |
| dispatcher | v1.1 → v1.2 | 32 / 36 → 32 / 36 |
| surfaces | v1.2 → v1.3 | 29 / 36 → 29 / 36 |
| `dependencies.md` (no version) | `DEP-BUS` 4 clauses (ledger said 3) → 5 | not read by the gate |

**Module line counts:** every Python file touched is under 200. New files: `test_graph_pull_trigger.py` 51,
`test_alpaca_raw_bars.py` 39, `test_served_fact_provenance.py` 82, `tests/test_analyst_held_stop.py` 128,
`test_analyst_poll_processed.py` 20, `test_pm_run_record.py` 45, `test_divergence_flag_ownership.py` 56,
`test_supervisor_health_sources.py` 43, `test_chat_quick_asks.py` 34. Edited files: `contracts/execution.py` 135,
`conftest.py` 56, `test_analyst_poll.py` 192, `test_exit_authority.py` 185, `test_position_sync_poll_branches.py` 46,
`test_monitor_poll.py` 173, `test_monitor_position_sync_work_items.py` 92, `test_pm_poll.py` 168, `test_pm_pubsub.py` 117,
`test_reward_risk.py` 163, `test_sector_cap.py` 158, `test_barrier_history.py` 130, `test_provider_agent.py` 181,
`test_reporter_poll.py` 55, `test_scanner_poll.py` 78, `test_supervisor_fault_incidents.py` 110,
`test_supervisor_health_flags.py` 196, `test_remediation_posture.py` 63, `tests/test_boundary_map.py` 72,
`tests/test_contract_required_payload_fields.py` 121, `tests/test_poll_payloads.py` 70,
`tests/test_pytest_servicebus_guard.py` 63, `tests/test_stop_width.py` 143. (`test_analyst_poll.py`
reached 200 at one point; the test that pushed it there was moved, not compressed.)

**`make ci`:** `make ci > scratchpad/ci.txt 2>&1; echo $?` gave **exit 0**, with all 15 steps green:
ruff, format, mypy, import-linter (5 kept, 0 broken), module size, module header, law coverage,
PARAM/settings sync, sprint status, markdown links, version scheme, pytest **3,810 passed, 8 skipped,
100.00 %** (baseline on `main`: 3,793 passed, 8 skipped), dependency audit ("No unaccepted
vulnerabilities; 1 accepted advisory re-checked"), detect-secrets Passed, and untracked secrets
("no untracked files to scan"). `pre-commit run --files <every changed file>`, markdownlint included,
also passes.

**`pyproject.toml` and `uv.lock`:** untouched. Both are owed to the planner: the PATCH bump and the
`uv lock` that re-resolves it, which this container cannot reach (`download.pytorch.org`).
`check_version_scheme` passed on the unchanged version.

**Owed to the planner:** the PATCH bump + `uv lock`, Windows `make ci`, `make gate-ran` on the
merged SHA, the merge, F1 (five amended clauses against the live graph or code), `docs/STATE.md`
(not touched here), and DL number re-check at merge (DL-260 used).

**Rows left OPEN:** none of the 23. Two new rows were filed OPEN by this sprint, each needing a
decision or a code change outside its scope. **DRIFT-098**: `PM-OUT-01`/`PM-TYP-03` still list
`portfolio_state_snapshot`, and the row table did not name them for that. **DRIFT-097**: the monitor's
position-sync poll lists every `BrokerPositionSnapshot`, which needs a code change.

---

## Return notes

- **Branch.** The session forced `claude/compassionate-hamilton-g1wdjb`; it was cut from `main`
  `b050f706` and carries 17 commits, one a book.
- **DRIFT-098 (new, OPEN).** `PM-OUT-01` and `PM-TYP-03` claim the same never-built
  `portfolio_state_snapshot` that DRIFT-039 withdrew from three other clauses. `PM-TYP-03` is 🟩 with
  that false conjunct, because its tests prove other fields. I did not reword them (DO NOT: a clause
  the row table does not name). A one-line amendment closes it; nothing behaves differently.
- **DRIFT-097 (new, OPEN).** The monitor's sync poll still downloads every `BrokerPositionSnapshot`
  on each poll. `MON-TRG-02` states the bound for `ExecutionRun` work only, and says so.
- **`PM-OBS-01`.** The clause now names the props `PMRun` really carries
  (`order_intent_set, approved_count, rejected_count, source_analyst_run_id, created_at`). My first
  test assumed `order_intent_set` alone and failed. The test now pins the measured set.
- **`DEP-BUS-05` says "sends".** The guard does not cover a receive, so it says less than the
  handover's "never transacts".
- **Still gray, on purpose.** `PM-OUT-06`, `FORE-IDN-01`, `FORE-OBS-01`, `FORE-IDM-03` and
  `DSP-IDN-03`. Each test-plan row names the partial proof, where one exists.
- **The first baseline `make ci` exit 2.** Detect-secrets reported "files were modified" because I
  was editing files while it ran. A clean re-run passed, and so did the final full run.
- Spec hygiene: every fenced block in this file has a blank line before and after, and markdownlint
  passes.

### Planner, at merge (2026-10-02)

- **Behaviour untouched, measured.** Under `agents/`, `kernel/`, `orchestration/`, `surfaces/` and `contracts/`, the only change outside law books and tests is the `owns_graph` declaration in `contracts/execution.py`.
- **Proven.** Windows `make ci` exit 0 (3,932 passed, 8 skipped, 100.00 %); `GATE PROVEN` for `d526faf4` from the proving worktree, printed SHA equal to `HEAD`; fast-forwarded after a rebase onto `main`; open CodeQL alerts equal the last merged branch's (131, 0 added); the lock's package set is unchanged.
- **Re-read by the planner (F1).** `PROV-TRG-01`, `SUP-OBS-02`, `ANLZ-OUT-09`, `MST-FAIL-07` and `EXEC-IDN-04` against the code and their cited tests; the law coverage gate passes; each amended book's version agrees in `laws.md`, `ledger.md` and `INDEX.md`.
- **The rebase.** S250 merged first. Its rows in the sprint README and INDEX were restored to their merged text, and the builder's new PM row was renumbered DRIFT-096 → **DRIFT-098** because S250 had taken 096.
- **DRIFT-098 closed here.** `PM-OUT-01` and `PM-TYP-03` listed a field the contract never had; the builder rightly left them, as the table did not name them. The two field lists now match `OrderIntentSet`.
- **Not zero.** Two rows are open, both filed while this sprint ran: **DRIFT-097** (the monitor's position-sync poll downloads every broker snapshot on each poll; a code change) and **DRIFT-096** (the analyst's book on a candidate with short history; filed by S250 after this sprint's session began, so row 096 of the table above was never seen by the builder). Both are work-queue 106.
- **Accepted as built:** `DEP-BUS-05` says "sends", which is what the guard covers; five clauses stay ⬜ with their partial proofs named.
