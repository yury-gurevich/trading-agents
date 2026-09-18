<!-- Agent: planning | Role: sprint handover -->
# Sprint 212 — a trace says why nothing was submitted, and exits 0 when the run is complete

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-212-trace-says-why-nothing-was-submitted`
**Status:** BUILT
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** closes work-queue items **66** and **67** · no ADR · no DRIFT row expected

> **Why this bump kind.** PATCH. No new capability. The run already records why its orders were withheld
> (on the `DeliberationRun`), and `print_trace` already counts eight stages. The operator's trace doesn't
> print the first fact, and the CLI's exit code contradicts the second.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/execution/laws/laws.md` | The execution agent's **locked constitution** | **LOCKED. Read-only.** This sprint reads execution's records; it must not change what execution writes |
| `agents/deliberator/laws/laws.md` | The deliberator's **locked constitution** | **LOCKED. Read-only.** Same: read its `DeliberationRun`, never change it |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`EXEC-OBS`** (what `ExecutionRun` records), **`DLIB-OBS`** (what `DeliberationRun`
records), and **LAW-02** (success is proven, never assumed — an exit code is a proof claim).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered **NO**, with the reason

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No.** Both changes live in operator tooling: `orchestration/` (the trace renderer) and `scripts/trace_run.py`.
No agent's code, no `contracts/` file and no graph write is touched. The trace *reads* two properties the
deliberator already writes (`verdicts`, `vetoed_tickers`) and one execution already writes
(`deliberation_status`). A repo-wide search for `batch_trace`, `print_trace` or `trace_run` in any `laws.md`
finds **none**, so no clause governs the renderer.

🪤 **The answer flips to YES if you take the road not taken below** (a `deliberation_vetoed_count` property
on `ExecutionRun`). That adds an execution output guarantee and a vocabulary property, so it would owe an
`EXEC-*` law cycle **and** a full `up` deploy. It is deliberately out of scope.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/batch_trace.py` (**188** lines) | `docs/laws/conventions.md`; LAW-02 | Operator-facing proof surface; no agent clause — confirm by reading |
| new `orchestration/trace_deliberation.py` | `agents/deliberator/laws/laws.md` + `test-plan.md` (the `DeliberationRun` output clauses) | You render the deliberator's recorded fields; read which ones are guaranteed and which may be absent on old rows |
| `scripts/trace_run.py` (**37** lines) | LAW-02 | An exit code is a machine-readable verdict |
| `orchestration/tests/test_batch_trace.py` (**187** lines) | `docs/laws/conventions.md` §3 | Test file is near the 200-line block — new tests go in a new file |

⚠️ **The invariant: the trace reads, it never writes.** `batch_trace.py`'s docstring says *"Reads only; never
writes."* If any change here would call `merge_node`, `add_edge` or any store write, **stop and report**.

---

## Goal

When a run's portfolio manager approves buys and the deliberator vetoes them, `trace_run.py` prints a
`[deliberation]` block between `[pm]` and `[execution]`. The block says how many were reviewed, how many
vetoed, and which tickers, so `approved=4` followed by `submitted=0` explains itself on one screen. And
`trace_run.py` exits **0** on a complete run and **non-zero** on an incomplete one, with the stage count
taken from the same tuple the `RESULT` line uses, never a literal.

## Why (context)

On 2026-09-17 the operator asked *"how did we go with the last run"*. The trace for `sched-2026-09-16` read
`[pm] approved=4` then `[execution] submitted=0 rejected=0`, and acceptance said `PASS`. Nothing on either
screen said why. It took several hand-written graph queries to find the `DeliberationRun` with
`vetoed_tickers=('USB','WFC','AMZN','MDLZ')`. The same run's `trace_run.py` printed
`RESULT 8/8 stages complete OK batch processed` and **exited 1**. Anything that wraps it (a skill, a `&&`
chain, a loop) reads every healthy night as a failure, which is the cries-wolf shape DL-125 warns about.

### Measured, 2026-09-17 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Exit code on a complete run | **1** | *[measured 2026-09-17]* `trace_run.py --run-id sched-2026-09-16` and `--run-id sched-2026-09-15`: both print `8/8 … OK batch processed`, both exit 1 |
| Cause of the wrong exit | `sys.exit(0 if complete == 7 else 1)` | *[measured]* `scripts/trace_run.py:33`; `_COMPLETE_KEYS` = `PositionSync` + 7 `CHAIN` labels = **8** (`orchestration/batch_trace.py:22`, `orchestration/batch_chain.py:19-27`) |
| Stale docstring | `"Returns number of completed stages (max 7)."` | *[measured]* `orchestration/batch_trace.py:26` |
| Existing test already expects 8 | `assert "8/8 stages complete" in out` | *[measured]* `orchestration/tests/test_batch_trace.py:98` — the renderer is right; only the CLI's literal is stale |
| The trace already has the DeliberationRun in hand | `walk_chain` stores it under `nodes["DeliberationRun"]` | *[measured]* `orchestration/batch_chain.py:48-51` (`DELIBERATION_KEY`); `print_trace` never reads it |
| What the run recorded | `verdicts` all `revise`; `vetoed_tickers=('USB','WFC','AMZN','MDLZ')`; `ExecutionRun` `skipped=0`, `deliberation_blocked_count=0`, `deliberation_status=applied` | *[measured 2026-09-17, live spine]* `DeliberationRun pm-run-eb9bcad8…`, `ExecutionRun execution-submit-pm-run-eb9bcad8…` |
| 🔁 It recurred the next night | `sched-2026-09-17`: PM approved **3** (USB, AMZN, WFC); `verdicts` all `revise`; `vetoed_tickers=('USB','AMZN','WFC')`; `ExecutionRun` `submitted=0 rejected=0 skipped=0 deliberation_blocked_count=0`, `deliberation_status=applied` | *[measured 2026-09-18, live spine]* `DeliberationRun`/`ExecutionRun` for `pm-run-87942b0d882644eda8ad95a618a06cc3`. Same unreconciled shape one night later, on `:s211` — **A4/A5 model a case that has now happened twice** |
| Why `ExecutionRun` can't reconcile it | `drop_vetoed` runs before the counters; `skipped` counts only `result.skipped + filtered.blocked_count` (posture filter) | *[measured]* `agents/execution/pm_execution.py:58`, `:83` |
| A rendering already exists — in the dashboard, not the CLI | `f"reviewed={reviewed}  vetoed={vetoed_count}"` | *[measured]* `orchestration/packs/trading_deliberation_view.py:42`; no `orchestration/*.py` imports `orchestration.packs` today |
| Veto frequency this block would have explained | at least one buy vetoed on **7 of the last 12** `DeliberationRun`s; **all** reviewed buys vetoed on 6 of them; **20 of 26 reviewed buys vetoed (77 %)** across that window | *[re-measured 2026-09-18]* last 12 `DeliberationRun`s by `created_at`, verdicts read from `verdicts` (2026-09-04 → 2026-09-17) |

---

## Scope — and what is deliberately NOT here

1. **`trace_run.py` exits 0 exactly when the run is complete.** The comparison uses the total `print_trace`
   derives from `_COMPLETE_KEYS`, returned or exposed alongside the count. **Do not replace `7` with `8`.**
   A hard-coded stage count is exactly what drifted when `PositionSync` was added. Fix the `max 7` docstring.
2. **`[deliberation]` block in the trace**, printed after `[pm]` and before `[execution]`, when
   `nodes["DeliberationRun"]` exists. At minimum:
   `reviewed=<n>  vetoed=<n>`, the vetoed tickers when any, and `status=<deliberation_status>` read from
   the `ExecutionRun` when present. Missing or malformed props render as `?` or are omitted. They never raise:
   old `DeliberationRun` rows predate some fields.
3. **When approved buys exceed submitted orders and a veto explains the gap, say so in one line.** For
   example: `  withheld=4 by deliberation veto`. Compute it only from the recorded facts
   (`approved`, `vetoed_tickers`, `submitted`). If they don't reconcile, print the numbers without a
   `withheld` claim. **Never infer a cause the record does not state.**
4. **Keep every module under 200 lines.** `batch_trace.py` is at 188, so the new rendering lives in a new
   module (suggested: `orchestration/trace_deliberation.py`), called from `print_trace`.

### Out of scope (do NOT build this sprint)

- **No change to what execution or the deliberator writes.** Not `pm_execution.py`, not `drop_vetoed`,
  not the `ExecutionRun` properties.
- **No acceptance-gate change.** `accept.py` said PASS on a fully vetoed night, and that is **correct**: the
  veto bound as ADR-0022 intends. A no-trade night is not a failure.
- **No dashboard change.** The observatory view already renders `reviewed/vetoed`.
- **No `laws.md` edit** — the law-cycle question is answered No.
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Record `deliberation_vetoed_count` on `ExecutionRun` so the counts reconcile on the record itself.**
  Rejected for this sprint: it adds an execution output guarantee (an `EXEC-*` law cycle), a graph vocabulary
  property (so the deploy becomes a full `up`, not a retag), and it duplicates a fact already on the
  `DeliberationRun` that the `ExecutionRun` is linked to. Revisit only if something other than a human
  reader (a gate, a metric) needs the count without walking the edge.
- **Import `orchestration/packs/trading_deliberation_view.py` into `batch_trace`.** Rejected:
  no `orchestration/*.py` module imports a pack today. The substrate→pack direction is the ADR-0012 wall
  (substrate must not depend on the trading pack), and one small reader of three properties does not justify
  opening that direction. If you find the duplication is real, record it as a design-log note, not an import.
- **Change `sys.exit(0 if complete == 7 …)` to `== 8`.** Rejected: it fixes today and re-arms the same trap
  for the next stage added.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **How the CLI learns the total** — `print_trace` returns `(complete, total)`, returns a small result
   object, or the module exposes the stage count. What hangs on it: `print_trace`'s other callers and tests
   (`orchestration/tests/test_batch_trace.py`, `test_graph_pull_e2e.py`, `test_position_sync_display_branches.py`,
   `test_resume.py`, `orchestration/packs/trading_acceptance.py` — **grep them all before changing the
   return type**).
2. **The `withheld` line's exact rule** — which recorded facts must agree before the line claims a veto
   explains the gap, and what prints when they don't.

🪤 **Take the next free DL number, then re-check it at merge.** S211 is in flight and records DL-172; `main`
may gain more before you merge.

---

## Blast radius — measured 2026-09-17

| What | Detail |
| --- | --- |
| Files changed | `scripts/trace_run.py` (37), `orchestration/batch_trace.py` (188), new `orchestration/trace_deliberation.py`, new test module, `docs/design-log.md`, `pyproject.toml` + `uv.lock` |
| Agents affected | **None** — operator tooling only |
| Contract change? | **No** |
| Graph vocabulary change? | **No** — reads existing properties only |
| New env keys / tunables | **None** |
| Deploy implication | **None.** `trace_run.py` runs on the operator's machine, not in the fleet; no image carries it. Merge is enough |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** and watch them fail. Paste the red output.
4. **Implement.**
5. **Prove the guards can fail (DL-70)** — break the implementation, watch each guard go red, restore.
6. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

All tests use an in-memory `GraphStore` fixture. **No `.env`, no network** — they must run in a worktree.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A complete run exits 0 | Full 8-artifact chain (reuse `test_batch_trace.py`'s `full_graph` shape) | `trace_run` `main()` raises `SystemExit(0)`; build-the-graph patched to the fixture |
| A2 | 🪤 An incomplete run exits non-zero | Chain truncated after `PMRun` | `SystemExit` code ≠ 0 |
| A3 | 🪤 The total is not a literal | Monkeypatch/extend the stage tuple by one in the test | A1's fixture now exits non-zero — proves the comparison follows the tuple |
| A4 | 🎯 A fully vetoed night explains itself | `PMRun` approving 4 buys; `DeliberationRun` with `verdicts` all `revise`, `vetoed_tickers` = all 4; `ExecutionRun` `submitted=0`, `deliberation_status=applied` | Output has a `[deliberation]` block **between** `[pm]` and `[execution]` with `reviewed=4`, `vetoed=4`, the four tickers, `status=applied`, and a `withheld=4` line |
| A5 | Partial veto | 3 approved, 2 vetoed, `submitted=1` | `vetoed=2`, the two tickers, `withheld=2` |
| A6 | 🪤 No invented cause | 4 approved, `vetoed_tickers=()`, `submitted=0` | Block prints `vetoed=0` and **no** `withheld … veto` line |
| A7 | Old row, missing fields | `DeliberationRun` with no `verdicts` / `vetoed_tickers` props | Renders without raising; shows `?` or omits, per your decision 2 |
| A8 | No deliberation at all | Chain without a `DeliberationRun` | No `[deliberation]` block; the rest of the output is byte-identical to today's (compare against an existing test's expectations) |

---

## Success factors

- [ ] `trace_run.py --run-id <complete run>` exits 0 and an incomplete run exits non-zero (A1, A2), and the
      total follows the stage tuple (A3).
- [ ] A fully vetoed night prints reviewed, vetoed, tickers and the withheld line on one screen (A4), and no
      line claims a veto the record does not state (A6).
- [ ] Nothing execution or the deliberator writes has changed: `git diff --stat -- agents contracts` is empty.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Law-cycle question answered No with the reason, in the Law reading record.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] 🟢 **Operator check, planning agent at merge (needs `.env`, main checkout):** `trace_run.py --run-id
      sched-2026-09-16` prints `[deliberation] reviewed=4 vetoed=4` with USB, WFC, AMZN, MDLZ and exits 0.

---

## Traps

🪤 **`8/8 stages complete` already passes a test.** The renderer is right. Only the CLI's `== 7` is wrong. A fix
that edits the renderer's counting is fixing the wrong file.
🪤 **`skipped` and `deliberation_blocked_count` are not veto counts.** Both read 0 on a fully vetoed night.
`deliberation_blocked_count` counts only the *binding-posture no-DeliberationRun* filter. Use
`vetoed_tickers` from the `DeliberationRun`.
🪤 **`verdicts` is a `Mapping` in memory and may arrive as a `mappingproxy` or `dict` from Postgres.**
`vetoed_tickers` may arrive as a `tuple` or a `list`. Read them the way `trading_deliberation_view.py:26-30`
does (`isinstance(…, Mapping)`, `isinstance(…, tuple | list)`), and test both shapes.
🪤 **`print_trace` has more callers than the CLI.** Changing its return type silently breaks
`trading_acceptance.py` or `test_resume.py` if you don't grep first.
🪤 **A worktree has no `.env`.** Every test here is in-memory. The live `sched-2026-09-16` check is the planning
agent's at merge, not yours. Do not try to reach the spine.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `orchestration/batch_trace.py` **188**, `orchestration/tests/test_batch_trace.py` **187**,
  `scripts/trace_run.py` **37**, `orchestration/batch_chain.py` **75**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — in particular, **no stage-count literal**.
- Faults, not silent failure — but the trace is a reader: malformed props render, they don't raise.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- PATCH version bump, `uv.lock` staged with it. 🪤 **S211 is in flight and bumps too** — take the next free
  PATCH at merge, not at branch time.
- **Line endings are LF.** The repo has no `.gitattributes`; check `git ls-files --eol` on every file you
  touch before committing. A CRLF flip turns a 10-line change into a whole-file diff.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving**, and check the printed SHA
   against `git rev-parse HEAD`.
2. Merge to `main` locally and push. 🪤 Not from the branch's own worktree.
3. **Post-merge CodeQL** on the merged SHA.
4. **Deploy: none.** Operator tooling, not in any image.
5. Planning agent runs the operator check above from the main checkout and records it in
   `docs/laws/functionality-checks.md`.

---

## Handover — paste this to Codex

```text
Sprint 212 - a trace says why nothing was submitted, and exits 0 when the run is complete.
Spec: docs/sprints/sprint-212-a-trace-says-why-nothing-was-submitted.md (read it whole).

BRANCH: sprint-212-trace-says-why-nothing-was-submitted, in its own worktree, cut from current origin/main.
Never commit to main. Take the next free PATCH version at merge time (S211 is also bumping).

MUST RULE: before any code, read agents/execution/laws/laws.md + test-plan.md,
agents/deliberator/laws/laws.md + test-plan.md, docs/laws/conventions.md and docs/laws/drift-register.md,
then fill the Law reading record at the bottom of the spec.
LAW-CYCLE ANSWER: NO. Operator tooling only (orchestration/ + scripts/trace_run.py). No agents/,
no contracts/, no graph writes. If you find yourself editing agents/ or contracts/, STOP and report.

WHAT TO BUILD:
1. scripts/trace_run.py:33 exits via `complete == 7`, but print_trace counts 8 stages
   (_COMPLETE_KEYS). Make the CLI compare against the total print_trace derives. DO NOT just
   change 7 to 8. Fix the "max 7" docstring at orchestration/batch_trace.py:26.
   print_trace has other callers (trading_acceptance.py, test_resume.py,
   test_graph_pull_e2e.py, test_position_sync_display_branches.py). Grep before changing its return.
2. Print a [deliberation] block between [pm] and [execution] when nodes["DeliberationRun"] exists
   (walk_chain already puts it there): reviewed, vetoed, vetoed tickers, status (from ExecutionRun
   deliberation_status). When approved buys exceed submitted and vetoed_tickers explains it, print
   one "withheld=N by deliberation veto" line. Never claim a cause the record does not state.
   batch_trace.py is at 188 lines: put the rendering in a new module.
   Do NOT import orchestration/packs/* from orchestration/*.py (ADR-0012 wall).

ORDER: record 2 design decisions in docs/design-log.md -> write tests A1-A8 from the spec and watch
them FAIL (paste red output) -> implement -> break each guard, watch it go red, restore ->
make ci redirected to a file (never piped) -> fill Closeout + Return notes, set Status: BUILT.

TRAPS: skipped and deliberation_blocked_count are NOT veto counts (both 0 on a fully vetoed night).
verdicts/vetoed_tickers may be Mapping/mappingproxy/dict and tuple/list: test both shapes.
Worktree has no .env: all tests in-memory; do not reach the live spine.
Keep line endings LF (no .gitattributes in repo): check git ls-files --eol before committing.
Every module < 200 lines, 100.00% coverage, no # noqa.
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
| `orchestration/batch_trace.py` | `docs/laws/conventions.md`; `docs/laws/drift-register.md`; execution and deliberator law/test-plan files | LAW-02; conventions §3/§7. No agent clause governs the operator renderer itself. | Yes. Keep the trace read-only and expose the stage total from the same tuple `print_trace` uses instead of changing its existing integer return contract. |
| `orchestration/trace_deliberation.py` | `agents/deliberator/laws/laws.md`; `agents/deliberator/laws/test-plan.md`; `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `DLIB-OUT-02` (green) guarantees `DeliberationRun` verdicts and vetoed tickers; `EXEC-OUT-09` (green) guarantees `ExecutionRun.deliberation_status` and posture-blocked count. | Yes. Render only recorded facts, tolerate missing historical props, and do not add execution-side counts or vocabulary. |
| `scripts/trace_run.py` | `docs/laws/conventions.md`; `docs/laws/drift-register.md` | LAW-02: the exit code is a machine-readable proof claim. | Yes. The CLI must compare completed stages with the exported total, not a literal. |
| new trace tests | `docs/laws/conventions.md`; execution and deliberator test plans | conventions §3/§7; `DLIB-OUT-02`; `EXEC-OUT-09`; LAW-02. | Yes. New tests will cite the governed law IDs in docstrings even though the production change is operator tooling. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. Scope is operator tooling only (`orchestration/` trace rendering plus `scripts/trace_run.py`). It reads existing `DeliberationRun` and `ExecutionRun` properties, changes no agent write, no `contracts/` file, no graph vocabulary, and no deployment surface.

**Contradictions found between a law and this spec:** None.

**Laws found silent where a decision was needed:** No agent law governs `batch_trace`, `print_trace`, or `trace_run`; LAW-02 governs the proof claim and DL-174 records the design choices. No drift row is added because no agent guarantee is being added or changed.

**Clauses that were ⬜ and are now proven:** None. This sprint relies on already-green `DLIB-OUT-02` and `EXEC-OUT-09`; it does not promote a law clause.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_trace_run_exits_zero_for_complete_trace` | `orchestration/tests/test_trace_run_cli.py` | PASS | LAW-02 |
| A2 | `test_trace_run_exits_nonzero_for_incomplete_trace` | `orchestration/tests/test_trace_run_cli.py` | PASS | LAW-02 |
| A3 | `test_trace_run_uses_stage_tuple_total` | `orchestration/tests/test_trace_run_cli.py` | PASS | LAW-02 |
| A4 | `test_fully_vetoed_trace_explains_withheld_orders` | `orchestration/tests/test_trace_deliberation.py` | PASS | `DLIB-OUT-02` / `EXEC-OUT-09` / LAW-02 |
| A5 | `test_partial_veto_trace_explains_only_matching_gap` | `orchestration/tests/test_trace_deliberation.py` | PASS | `DLIB-OUT-02` / `EXEC-OUT-09` / LAW-02 |
| A6 | `test_trace_does_not_invent_veto_cause` | `orchestration/tests/test_trace_deliberation.py` | PASS | `DLIB-OUT-02` / LAW-02 |
| A7 | `test_old_deliberation_row_renders_unknowns` | `orchestration/tests/test_trace_deliberation.py` | PASS | `DLIB-OUT-02` / LAW-02 |
| A8 | `test_trace_without_deliberation_keeps_existing_shape` | `orchestration/tests/test_trace_deliberation.py` | PASS | LAW-02 |

**Tests added beyond the plan:** `orchestration/tests/test_trace_deliberation_edges.py` covers malformed defensive paths: non-numeric `submitted`, absent `ExecutionRun`, absent `PMRun`, missing/invalid PM payload, mismatch between veto count and submitted gap, and vetoed tickers outside approved buys.

---

## Closeout — evidence

**Status:** BUILT and BRANCH-GATED at rebased evidence commit `cd15f3cdc6b2786d4039238926a96a0a9bf4a3db`; this gate-evidence update must be pushed and re-proven before merge.

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\trading-agents-sprint-212-trace-says-why-nothing-was-submitted`; `Test-Path .env` returned `False`.

**Result:** Implemented operator-tooling trace repair. `trace_run.py` now exits 0 when `complete == trace_stage_total()`. `print_trace` now prints a `[deliberation]` block after `[pm]` and before `[execution]` when `walk_chain` found a `DeliberationRun`; the block renders reviewed/vetoed/status/tickers and only prints `withheld=N by deliberation veto` when approved buy tickers, vetoed tickers and submitted count reconcile exactly.

**Files changed:** `orchestration/batch_trace.py`, `orchestration/trace_deliberation.py`, `scripts/trace_run.py`, `orchestration/tests/test_trace_deliberation.py`, `orchestration/tests/test_trace_deliberation_edges.py`, `orchestration/tests/test_trace_run_cli.py`, `docs/design-log.md`, `docs/STATE.md`, this sprint file, `pyproject.toml`, `uv.lock`.

**Design decisions:** `DL-174` records (1) exposing the stage total without changing `print_trace`'s integer return type, and (2) the exact conservative rule for the withheld line. Rejected: returning a tuple/result object, changing `7` to `8`, using `skipped`/`deliberation_blocked_count`, or inferring a cause from `approved > submitted`.

**Proof — the red run first:**

```text
uv run pytest orchestration\tests\test_trace_deliberation.py orchestration\tests\test_trace_run_cli.py --no-cov
collected 8 items
orchestration\tests\test_trace_deliberation.py FFFF.                     [ 62%]
orchestration\tests\test_trace_run_cli.py F.F                            [100%]
FAILED ... test_trace_run_exits_zero_for_complete_trace
FAILED ... test_trace_run_uses_stage_tuple_total
FAILED ... test_fully_vetoed_trace_explains_withheld_orders
FAILED ... test_partial_veto_trace_explains_only_matching_gap
FAILED ... test_trace_does_not_invent_veto_cause
FAILED ... test_old_deliberation_row_renders_unknowns
========================= 6 failed, 2 passed in 1.78s =========================

DL-70 guard breaks after implementation:
- permissive CLI exit (`complete <= total`) made `test_trace_run_exits_nonzero_for_incomplete_trace` fail: `assert 0 != 0`.
- forced deliberation rendering without a `DeliberationRun` made `test_trace_without_deliberation_keeps_existing_shape` fail.
- weakened withheld reconciliation made `test_trace_does_not_invent_veto_cause` fail on `withheld=4 by deliberation veto`.
```

**Proof — the green run:**

```text
uv run pytest orchestration\tests\test_trace_deliberation.py orchestration\tests\test_trace_deliberation_edges.py orchestration\tests\test_trace_run_cli.py --no-cov
collected 15 items
orchestration\tests\test_trace_deliberation.py .....                     [ 33%]
orchestration\tests\test_trace_deliberation_edges.py .......             [ 80%]
orchestration\tests\test_trace_run_cli.py ...                            [100%]
============================= 15 passed in 1.47s ==============================

uv run pytest orchestration\tests\test_batch_trace.py orchestration\tests\test_pm_rejection_rendering.py orchestration\tests\test_position_sync_display_branches.py orchestration\tests\test_trace_deliberation.py orchestration\tests\test_trace_run_cli.py --no-cov
============================= 20 passed in 1.90s ==============================
```

**Guards planted:** A1-A8 from the sprint plan plus seven defensive edge guards. A1/A3/A4/A5/A6/A7 failed on the pre-change code; A2/A6/A8 were also proven able to fail via intentional DL-70 breaks and restored.

**Module line counts:** `orchestration/batch_trace.py` 198; `orchestration/trace_deliberation.py` 83; `scripts/trace_run.py` 37; `orchestration/tests/test_trace_deliberation.py` 199; `orchestration/tests/test_trace_deliberation_edges.py` 133; `orchestration/tests/test_trace_run_cli.py` 84.

**`make ci`:** after rebasing onto `origin/main` @ `ed70b8a9e656cdda90b72c9dcc3c5ee009af23a3`, branch tip `1ea1bbdae82dda81858cb52eca38661605ffcc7a` ran `make ci > $env:TEMP\s212-ci-rebased-main4.txt 2>&1; Write-Output $LASTEXITCODE` and exited `0`. Log tail: `2811 passed, 6 skipped in 89.29s`, `Required test coverage of 100.0% reached. Total coverage: 100.00%`; `uv run pip-audit` -> `No known vulnerabilities found`; detect-secrets passed and untracked secret scan reported `no untracked files to scan`.

**`make gate-ran`:** after the branch was force-with-lease pushed over `origin/main` @ `ed70b8a9e656cdda90b72c9dcc3c5ee009af23a3`, `gh run watch 35311035095 --exit-status` exited `0`; CI run `35311035095` succeeded (`security`, `quality`, `test`) and Security Findings run `35311035059` succeeded. From this worktree, `git rev-parse HEAD` printed `cd15f3cdc6b2786d4039238926a96a0a9bf4a3db`, and `make gate-ran` exited `0`:

```text
uv run python scripts/assert_gate_ran.py
GATE PROVEN for cd15f3cdc6b2786d4039238926a96a0a9bf4a3db:
  CI: success (attempt 1)
  Security Findings: success (attempt 1)
```

**Not met / verified failing:** Final evidence-commit reproof pending after this update; merge not done; deployment not required; live operator check from main checkout not done in this worktree because `.env` is absent and the sprint explicitly keeps live spine access out of this build worktree.

---

## Return notes

- Branch local build and branch gate are green with no `agents/` or `contracts/` diff (`git diff --stat -- agents contracts` and `git diff --name-only -- agents contracts` produced no output). Final evidence commit must still be pushed and re-proven before merge.
- The operator check still belongs after merge from the main checkout with `.env`: `trace_run.py --run-id sched-2026-09-16` should print `[deliberation] reviewed=4  vetoed=4` with USB, WFC, AMZN, MDLZ and exit 0.
- S212 changes operator tooling only; no deploy is implied.
