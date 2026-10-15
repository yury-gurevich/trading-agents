<!-- Agent: planning | Role: sprint handover -->
# Sprint 279 — a pass over the broker's orders or the held book reads each graph label once

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-279-a-pass-reads-each-label-once`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-302](../design-log.md) (measured and decided, planner, 2026-10-15) · [work-queue 101](../work-queue.md) · follows [S252](sprint-252-every-finder-fetches-only-its-pending-work.md) / DL-261

> **Why this bump kind.** A fix: the same decisions, made from the same graph, at a hundredth of
> the transfer. No new capability, no decision path changes.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/execution/laws/laws.md`, `agents/monitor/laws/laws.md`, `agents/analyst/laws/laws.md` | Each agent's **locked constitution** | **LOCKED. Read-only during a build**, except the three new clauses the Appendix gives exactly |
| the three `test-plan.md` beside them | Proven (🟩) vs unproven (⬜) per clause | Read them; you add one row to each (Steps) |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`EXEC-TRG-07`**, **`EXEC-OUT-07`**, **`EXEC-OBS-06`**, **`EXEC-IDM-02`**,
**`EXEC-FAIL-02`**, **`ANLZ-OUT-09`**, the monitor's **`MON-TRG-02`** and its exit rules, and the
three new **`EXEC-PERF-02`**, **`MON-PERF-03`**, **`ANLZ-PERF-02`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **The law-cycle question is answered below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes, both.** `contracts/stop_width.py` and `contracts/positions.py` change, and three agents promise
a bound they did not promise before: a pass reads a whole graph label once, never once per item it
walks. Three new clauses, each proven by the tests below, text exactly as Appendix section 2 gives
it: **`EXEC-PERF-02`** (execution v1.13 → v1.14), **`MON-PERF-03`** (monitor v1.3 → v1.4),
**`ANLZ-PERF-02`** (analyst v1.10 → v1.11). On the prototype the gate derives execution
**41 / 67**, monitor **22 / 47**, analyst **30 / 53**: let the gate tell you.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/execution/drop_sweep.py`, new `drop_sweep_reads.py`, `fill_attempts.py` | execution `laws.md` + `test-plan.md`; conventions | `EXEC-TRG-07` the sweep is cleanup beside the run-start snapshot and never prevents it; `EXEC-OUT-07` drop evidence; `EXEC-IDM-02` no order dropped twice; `EXEC-FAIL-02` contained failure |
| `agents/execution/broker_stop_thresholds.py` | same | `EXEC-OBS-06` the broker stop is the width the one shared resolver decides |
| `contracts/stop_width.py`, `contracts/positions.py` | the three books; [DL-223](../design-log.md) | `EXEC-OBS-06`, `ANLZ-OUT-09`, the monitor's watchdog: one resolver, so the three cannot disagree |
| `agents/monitor/run.py`, `decide.py`, `domain/positions.py` | monitor `laws.md` + `test-plan.md` | the end-of-run evaluation (`MON-TRG-02`'s second work kind), stop checks per position |
| the new tests | conventions §3 | every test cites its clause |

⚠️ **No decision may change.** The same broker orders are dropped or kept, the same stops are
planned with the same widths and sources, the same positions breach, the same thresholds reach the
analyst. The planner proved it on live data (Measured, last row). If your change would alter any
output beyond the number of reads, stop and report.

---

## Goal

At merge, one run-start drop sweep reads the `Fill` and `BrokerStopOrder` labels at most once each,
whatever the number of broker orders, and neither when the broker lists none; a drop it writes is
seen by every later order in the same sweep. One pass over the held book (the analyst's held-stop
read, execution's stop-threshold plan, the monitor's end-of-run evaluation) reads `Fill` at most
once for all its positions' decided widths, and not at all when no position is broker-adopted.
Everything each pass decides is unchanged.

## Why (context)

Work-queue 101's F2 (2026-10-10) left execution at 154.0 MB a night and the monitor at 20.6 MB,
against S252's target of ten times less than the 2026-10-01 baseline (40.3 and 14.3 MB). 134.7 MB of
execution's arrived in its first five minutes, undiagnosed. It is now diagnosed: the drop sweep lists
every `Fill` once per broker order, and the stop-width resolver lists every `Fill` once per adopted
position, in three agents. The first grows with orders × fills, so it only gets worse. The operator
said yes to speccing it for Codex (2026-10-15).

### Measured, 2026-10-15 — read these before designing

All read as the planner, at no cost. Scripts and outputs are in OneDrive
`trading-agents-data/wq101-2026-10-15/`.

| Claim | Value | How it was measured |
| --- | --- | --- |
| Received bytes per minute, four weekday nights | execution **135.5 to 137.0 MB in one minute** at its start (22:31 to 22:33 UTC) and 13.9 to 14.6 MB in one minute ten minutes later; the monitor 15.1 to 15.8 MB **in that same minute** | *[measured]* Azure `RxBytes`, `rx_nights.sh` → `rx_nights.txt`, nights of 2026-10-09, 10-12, 10-13, 10-14 |
| Nightly totals, same nights | execution 152.9 to 154.6 MB, monitor 17.6 to 20.4 MB, analyst 41.1 to 50.1 MB | *[measured]* same |
| Execution's head of run (`sync_run_request`) on live data | **126.81 MB in 564 calls**: 120.89 MB `fill_attempt_chain` listing 346 `Fill`s 348 times (once per broker order), 5.42 MB `broker_stop_orders` listing 93 `BrokerStopOrder`s 211 times | *[measured]* `wq101_read_paths.py` (the real functions; a store that writes nothing, a broker that only reads), `read_paths_main_f091ec61.txt` |
| Execution's submit of `sched-2026-10-14`'s `PMRun` | **12.91 MB**, of which 11.12 MB `_lineage_stop_pct` listing every `Fill` once per adopted position (32 calls) | *[measured]* `read_paths_submit_monitor_f091ec61.txt` |
| The monitor's end-of-run evaluation of that run | **14.81 MB**: the same 11.12 MB, and 2.92 MB the run's one `MarketData` node | *[measured]* same |
| The analyst's held-stop read (`open_position_stop_thresholds`) | **11.23 MB**, the same 11.12 MB | *[measured]* `wq101_checks.py` → `checks_main_f091ec61.txt` |
| The broker's order list | 348 orders (340 pipeline-owned; 153 filled, 33 pending, 162 rejected), oldest 2026-06-16 | *[measured]* `GET /v2/orders?status=all&limit=500`, same file |
| Broker orders whose chains end on the same `Fill` | **10 pairs**, every one a rejected stop `K` and its re-placement `K#1`; the sweep never writes a stop's Fill | *[measured]* same file |
| `Fill` keys equal to their attempt key | 346 of 346 | *[measured]* same file |
| The prototype, same script, same data | head **126.81 → 0.88 MB**; submit **12.91 → 2.14 MB**; evaluation **14.81 → 4.04 MB**; held-stop read **11.23 → 0.46 MB** | *[measured]* `read_paths_proto.txt`, `checks_proto.txt` on `../ta-s279-proto` |
| **No decision changes** | every write the four paths would make hashes equal on `main` and the prototype (68, 71, 2, 65 writes; timestamps and fresh run ids masked); the analyst's 32 thresholds hash equal | *[measured]* `read_paths_digest_*.txt`, `thresholds_digest_*.txt` |
| A night's received bytes after the deploy | execution about 10 MB, the monitor about 7 MB | *[ASSUMED — derived, not measured]* the cut above plus idle polls (0.18 MB per five minutes) and the broker reads. Settles at F2 |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (A1 to A12 below).
2. **The sweep** (`drop_sweep.py`, new `drop_sweep_reads.py`, `fill_attempts.py`): one `SweepReads`
   per sweep, read only when the broker lists an order, inside the sweep's fault boundary; the chain
   rule over nodes already read; the one Fill a drop writes read back by key.
3. **The resolver** (`contracts/stop_width.py`): `LineageFills`, a read held for one pass and made
   only when an adopted Position asks; `decided_stop_pct(..., fills=None)`.
4. **The three passes** pass one `LineageFills` down: `contracts/positions.py`,
   `agents/execution/broker_stop_thresholds.py`, `agents/monitor/run.py` → `decide.py` →
   `domain/positions.py`.
5. **The law**: three clauses as given, test-plan rows, rollups.

### Out of scope (do NOT build this sprint)

- **The other per-item whole-`Fill` reads**, both conditional and absent from the measured nights:
  `run.py::_completed_exit_fill` (per sell intent) and `broker_stop_writes.py` (per rejected stop
  placement). Named in DL-302.
- **The broker's 500-order limit** (work-queue 134): a separate defect with its own decision.
- **The monitor's `MarketData` read** (2.92 MB, the run's prices) and the analyst's other reads.
- **`kernel/`.** No new store method.
- **No new label, property, edge, env key or tunable. No ADR reversal.**

### The road not taken (LAW-06)

- **Fetch each order's chain by key.** Rejected: equivalent today (346 of 346 keys follow the
  attempt rule) but about 700 round trips for the same bytes as one list, and it leans on a key
  invariant no clause states.
- **Skip the read-back because today's shared chains are all stops.** Rejected: the guarantee would
  rest on data, not code.
- **Make `fills` a required parameter.** Rejected: every lone call (tests, two repair scripts) changes
  for no behaviour; the source guard (A11) holds the production calls instead.
- **One batch call that returns every width.** Rejected: one adopted lot's `ValueError` would fail
  the whole book, where execution's plan contains it per ticker.
- **A cache across passes.** Rejected: a long-lived process would serve a stale Fill.

---

## The design decisions — made, and recorded in DL-302

1. **D1** The sweep reads `Fill` and `BrokerStopOrder` once (`SweepReads`); the chain rule moves to
   `fill_attempt_chain_in` / `latest_fill_attempt_in`, the graph forms become wrappers.
2. **D2** A drop's Fill is read back by key (`SweepReads.reread`).
3. **D3** No broker order, no read; a failed read is one fault (capability `drop_unfilled_orders`)
   and no order is touched.
4. **D4** `LineageFills`, optional `fills=` on `decided_stop_pct`; each of the three passes makes one.
5. **D5** A source guard: every production call of `decided_stop_pct` passes `fills=`.
6. **D6** Three new PERF clauses.
7. **D7** PATCH; image-only retag.
8. **D8** S258's test pinned the execution book at exactly `v1.13`, so any later amendment failed it
   (found by the prototype's `make ci`). It now pins `v1.13` or later (Appendix section 3).

---

## Blast radius — measured 2026-10-15

| What | Detail |
| --- | --- |
| Files changed | `agents/execution/drop_sweep.py` 167 → **183**, `fill_attempts.py` 127 → **137**, new `drop_sweep_reads.py` **46**, `broker_stop_thresholds.py` 137 → **146**; `contracts/stop_width.py` 115 → **141**, `contracts/positions.py` 190 → **193**; `agents/monitor/run.py` 117 → **121**, `decide.py` 59 → **62**, `domain/positions.py` 93 → **97**; three `laws.md`, three `test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`; new tests; one existing test, `tests/test_param_law_sync_execution_rows.py` (Appendix section 3); `pyproject.toml`, `uv.lock`; this spec and its README row |
| Agents affected | execution, monitor, analyst (through `contracts/positions.py`; no analyst file changes). None imports another |
| Contract change? | yes, `contracts/stop_width.py` (a new class, a new keyword) and `contracts/positions.py` (passes it): the law cycle above |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | image-only retag. Each image copies `contracts/` and its own `agents/<name>/` whole, so the new module ships |
| Rollback | retag to the tag before the deploy. A retag undoes nothing else because nothing else changes: no write changes shape, no pack, no broker order |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. The design decisions are recorded (DL-302). Do not edit `docs/design-log.md`.
3. **Write the tests A1 to A12** and their support module under the names below, and run them on the
   unchanged tree. Paste the output: **A1, A2, A5, A6, A7, A8, A10 and A11 must be red** (A10 through
   the missing `LineageFills`, which it imports inside the test, so the module still imports). A3, A4,
   A9 and A12 pin what the unchanged tree already does (equivalence, the empty sweep, the empty book,
   the guard's own reader) and pass before section 1; say so.
4. **Apply Appendix section 1** (production) exactly, and **Appendix section 3** (one existing
   test, S258's, which pinned the execution book at exactly v1.13) exactly.
5. **Apply Appendix section 2** (the three `laws.md`) exactly. Then add one row to each
   `test-plan.md`, after its `*-PERF-01` row, marked 🟩 and naming your tests (Test plan's last
   column says which); set the three agents' rows of `docs/laws/ledger.md` and `docs/laws/INDEX.md`
   to the new version, naming S279 and DL-302, with the count the law gate derives.
6. **Plant the breaks B1 to B14** (Traps) one at a time; each must turn at least one of your tests
   red; restore each before the next.
7. **Bump** PATCH: `0.128.01` → `0.128.02`; `uv lock --offline`; stage `uv.lock`.
8. **`make ci`**, redirected to a file. Read the file.
9. **Fill the handback sections**; set Status to `BUILT` here and in this sprint's
   `docs/sprints/README.md` row.

---

## Test plan

Under exactly these names and files (the planner judges the breaks by them). The support module
`tests/label_reads_support.py` holds `LabelReadCounter`, an `InMemoryGraphStore` whose `list_nodes`
counts each call in a `Counter` by label (`listed`), and the seeders you need. A seeded adopted
Position carries `provenance="reconciled-from-broker"`, a 5 % `stop_pct`, and one filled production
buy that equals it exactly (`source_run_id` starting `pm-run-`, `side` buy, `broker_status`
`filled`, the same `quantity`, `broker_price_cents` equal to its `opened_price_cents`, `ticker`),
which `EXECUTES` an `OrderIntent` carrying the decided `stop_pct`.

| # | Test (exact name) | File | Plants | Must prove | Row |
| --- | --- | --- | --- | --- | --- |
| A1 | 🎯 `test_a1_one_sweep_reads_each_label_once` | `agents/execution/tests/test_drop_sweep_reads.py` | three broker orders from an earlier run: a pending limit order with its Fill lineage, a filled one, a stop with its `BrokerStopOrder` fact | `listed["Fill"] == 1`, `listed["BrokerStopOrder"] == 1`, one drop, only the pending order cancelled (`EXEC-PERF-02` / `EXEC-OUT-07`) | EXEC |
| A2 | `test_a2_the_run_start_reads_fill_twice_whatever_the_orders` | same | A1's orders, then `poll.sync_run_request` on a `RunRequest` | `listed["Fill"] == 2` (the sweep's and the refresh's), `listed["BrokerStopOrder"] == 1` (`EXEC-PERF-02` / `EXEC-TRG-07`) | EXEC |
| A3 | 🪤 `test_a3_a_drop_in_the_sweep_is_seen_by_a_later_order` | same | Fill `K` with lineage and Fill `K#1` (`broker_idempotency_key` `K`, `attempt_ordinal` 1, pending); broker orders **in this order**: `K` rejected with reason `expired`, then `K#1` pending | one drop, **no cancel**, one `BrokerOrderStatus` (`EXEC-PERF-02` / `EXEC-IDM-02`) | EXEC |
| A4 | `test_a4_no_broker_order_reads_no_label` | same | a broker with no orders | `listed` is empty (`EXEC-PERF-02`) | EXEC |
| A5 | `test_a5_a_failed_read_is_one_fault_and_no_cancel` | same | a counter whose `list_nodes("Fill")` raises; **two** pending orders | returns 0, nothing cancelled, exactly one fault, capability `drop_unfilled_orders` (two today, one per order: DL-302 D3) (`EXEC-PERF-02` / `EXEC-FAIL-02`) | EXEC |
| A6 | 🎯 `test_a6_the_analysts_held_book_reads_fill_once` | `tests/test_stop_width_reads.py` | three adopted Positions, three tickers, three different decided widths | `open_position_stop_thresholds` gives each ticker its own decided width, `listed["Fill"] == 1` (`ANLZ-PERF-02` / `ANLZ-OUT-09`) | ANLZ |
| A7 | `test_a7_executions_stop_plan_reads_fill_once` | same | the same book | `broker_stop_thresholds(graph, fallback_stop_pct=0.05)`: each plan its decided width, every source `lineage`, `listed["Fill"] == 1` (`EXEC-PERF-02` / `EXEC-OBS-06`) | EXEC |
| A8 | `test_a8_the_monitors_evaluation_reads_fill_once` | same | the same book; prices where one ticker sits **below its decided stop and above the 5 % fallback's** (or the reverse), the others above both | `evaluate_and_write` checks all three, the `MonitorRun` records exactly the breaches the decided widths give, and the evaluation adds exactly one `Fill` read (`MON-PERF-03`) | MON |
| A9 | 🪤 `test_a9_a_book_with_no_adopted_position_reads_no_fill` | same | three Positions **not** adopted, each recording its own width | the three passes together read no `Fill` (`EXEC-PERF-02` / `MON-PERF-03` / `ANLZ-PERF-02`) | all three |
| A10 | `test_a10_a_lone_call_still_reads_its_lineage` | same | the adopted book; `LineageFills` imported **inside** the test | `decided_stop_pct` with no `fills` gives the lineage width and reads once; two calls sharing one `LineageFills` read once more in all and give each its own width (`EXEC-OBS-06` / `ANLZ-OUT-09`) | — |
| A11 | `test_a11_every_resolver_call_shares_its_pass_read` | `tests/test_stop_width_reads_guard.py` | reads `agents/` and `contracts/` source, outside every `tests` directory, with `ast` | every call of `decided_stop_pct` (by name or attribute) passes `fills=`; there are exactly 3 (`EXEC-PERF-02` / `MON-PERF-03` / `ANLZ-PERF-02`) | all three |
| A12 | `test_a12_the_guard_sees_a_call_without_a_shared_read` | same | a probe file **under `tmp_path`**, one call without `fills=` and one with | the guard's reader returns exactly those two, flagged and not | — |

---

## Success factors

- [ ] A1 to A12 exist under the names above, each citing its clauses; A1, A2, A5, A6, A7, A8, A10 and
      A11 red before section 1; all twelve green after.
- [ ] Appendix sections 1 to 3 applied exactly: the nine production files, three `laws.md` and S258's
      test equal the prototype's blobs (`prototype_blobs.txt`, OneDrive `trading-agents-data/wq101-2026-10-15/`).
- [ ] No existing test changed but the one Appendix section 3 gives; every existing test passes.
- [ ] B1 to B14 each red against your tests, each restored.
- [ ] Every touched module, test files included, under 200 lines after `ruff format`.
- [ ] Version `0.128.02`, `uv.lock` one line changed.
- [ ] `make ci` exit 0, 100.00 % coverage (the dependency audit may be the only step that cannot reach
      its network; say so if it is).
- [ ] **F1 (the planner's, at review, no cost):** `wq101_read_paths.py` and `wq101_checks.py` on the
      built tree read what the prototype read and hash every write and the thresholds equal to `main`'s.
- [ ] **F2 (the planner's, after deploy):** the first weekday night on the new tag: execution's
      `RxBytes` at its start under 5 MB and its night under 40.3 MB, the monitor's night under 14.3 MB;
      the run completes as before. Then work-queue 101 closes.

---

## Traps

🪤 **A3's order matters.** With `K#1` listed first, the pending order is cancelled and dropped first
and the rejected one then finds it dropped: the test passes with or without the read-back and
proves nothing. List `K` (rejected, `expired`) first.
🪤 **A8 must tell the decided width from the fallback.** A price below both stops, or above both,
passes with or without the lineage. Put one ticker between its decided stop and the 5 % fallback's.
🪤 **Count around the pass.** Where a test reads the graph itself before the pass (A8 reads
`active_positions`), take `listed["Fill"]` just before the pass and assert on the difference.
🪤 **A6 to A8 must be red on the unchanged tree by their counts, not by an import.** Import
`LineageFills` inside A10 only.
🪤 **A12 writes under `tmp_path` only.** A probe file inside the repository is left behind by a killed
run and read by the next one.
🪤 **`InMemoryGraphStore` returns list props as tuples.** Compare widths and counts, not raw props.
🪤 **detect-secrets flags `"..._API_KEY": "x"` style literals.** None is needed here; do not add one.
🪤 **`ruff format` grows test files.** Measure sizes after formatting.

**Breaks — plant one at a time against your tests, restore each:**

| # | File | Plant |
| --- | --- | --- |
| B1 | `drop_sweep.py` | delete the line `reads.reread(fill)` |
| B2 | `drop_sweep_reads.py` | `reread` stores `fill` itself, not the read-back |
| B3 | `drop_sweep_reads.py` | `latest_fill` reads `self.graph.list_nodes("Fill")` each call |
| B4 | `drop_sweep.py` | `_tracked_as_stop` iterates `type(reads).read(reads.graph).stops` |
| B5 | `drop_sweep.py` | read the labels even when the broker lists no order |
| B6 | `drop_sweep.py` | `_read_graph` reads outside its fault boundary |
| B7 | `stop_width.py` | `LineageFills.nodes` lists the label each call |
| B8 | `stop_width.py` | `LineageFills.__init__` lists the label at once |
| B9 | `stop_width.py` | `decided_stop_pct` ignores `fills` (`LineageFills(graph)` always) |
| B10 | `contracts/positions.py` | a new `LineageFills(graph)` per ticker |
| B11 | `broker_stop_thresholds.py` | `fills=LineageFills(graph)` per lot |
| B12 | `agents/monitor/run.py` | `fills=LineageFills(graph)` per position |
| B13 | `agents/monitor/decide.py` | `exit_position(graph, position)` without `fills` |
| B14 | `agents/monitor/domain/positions.py` | `decided_stop_pct(graph, node)` without `fills` |

On the prototype, all 14 went red against the planner's own tests (`s279_breaks_on_prototype.txt`).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Sizes after the change: `contracts/positions.py` **193**, `drop_sweep.py` **183**. Section 1
  already places them; add nothing to them.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers. Nothing here is a tunable.
- Faults, not silent failure: the sweep's graph read stays inside a `fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**, redirected to a file, never piped.
- Version bump PATCH, `uv.lock` staged with it.
- A worktree has **no `.env`**. State which tree you ran in.

---

## Sequencing after merge (the planner's)

1. Review: blobs against `prototype_blobs.txt`; the planner's tests (`planner_tests/`) beside the
   builder's; `s279_breaks.py` against the builder's tests alone; CodeQL set-diff against the S278
   remote branch (133 open, 0 errors); F1 on the built tree.
2. `make gate-ran` from `../ta-s279`, the SHA checked against `git rev-parse HEAD`; merge, fast-forward.
3. Deploy with the next retag (image-only, after or with the S277 and S278 deploy); record the
   rollback tag; F2; close work-queue 101.

---

## Handover — paste this to Codex

```text
You are building Sprint 279 in the worktree ../ta-s279, on the branch
sprint-279-a-pass-reads-each-label-once. Never work on main. The worktree and its venv are ready;
never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-279-a-pass-reads-each-label-once.md, whole, before anything else. It is
the spec, and its bottom sections are your handback. The Appendix holds the production code and the
law text, which you apply exactly. Your work is the tests, the law rows, the bump and the evidence.

In order:
1. Read agents/execution/laws/laws.md, agents/monitor/laws/laws.md, agents/analyst/laws/laws.md and
   the three test-plan.md beside them, docs/laws/conventions.md and docs/laws/drift-register.md.
   Fill the Law reading record in the spec BEFORE any code.
2. Write tests/label_reads_support.py and the tests A1 to A12 under the exact names and files in
   the Test plan, each docstring citing its clauses. Run them on the unchanged tree and paste the
   output into the Closeout: A1, A2, A5, A6, A7, A8, A10 and A11 must be red; A3, A4, A9 and A12
   pass already (Steps, step 3).
3. Apply Appendix section 1 exactly (nine files; drop_sweep_reads.py is new). Change nothing else
   in production code. Apply Appendix section 3 exactly (S258's test pinned the execution book at
   exactly v1.13; it now pins v1.13 or later). Change no other existing test.
4. Apply Appendix section 2 to the three laws.md exactly. Then add one row to each test-plan.md
   after its PERF-01 row, marked 🟩, naming your tests (the Test plan's Row column). Set the
   execution, monitor and analyst rows of docs/laws/ledger.md and docs/laws/INDEX.md to the new
   versions, naming S279 and DL-302, with the counts the law gate derives (41 / 67, 22 / 47,
   30 / 53 on the prototype).
5. Plant the breaks B1 to B14 (Traps) one at a time; each must turn at least one of your tests red;
   restore each before the next. Record each in the Closeout.
6. Bump the version PATCH (0.128.01 -> 0.128.02) in pyproject.toml, run uv lock --offline, stage
   uv.lock. Run make ci redirected to a file and read the file. If the dependency audit is the only
   step that fails for want of network, say so; the planner runs it.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: run infra/ scripts, pwsh or any az command; reach the network; change kernel/, any pack,
any Dockerfile, run.py or broker_stop_writes.py; add or reword a law clause beyond section 2; change
any existing test beyond section 3; use noqa; let any module, test files included, reach 200 lines; measure make ci
through a pipe.

Traps (the spec's Traps section has them all): in A3 list the rejected order K before the pending
K#1, or the test proves nothing; in A5 plant two orders; in A8 put one ticker between its decided
stop and the 5 % fallback's; count Fill reads around the pass only; import LineageFills inside A10
only; A12 writes its probe under tmp_path, never in the repository;
the in-memory store returns list props as tuples; ruff format grows test files, measure after
formatting.

Two tiers when something does not fit. A wrong command, count, path or line number whose intent is
plain: correct it, record it in Return notes, and carry on. A law that contradicts the spec, an
existing test failing, or a measurement in the spec that does not reproduce: STOP and report. State
anything not done as "not done" or "verified failing". Never write a Result for work you have not done.
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
| *(builder)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(builder)*

**Contradictions found between a law and this spec:** *(builder)*

**Laws found silent where a decision was needed:** *(builder)*

**Clauses that were ⬜ and are now proven:** *(builder)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| *(builder)* | | | | |

**Tests added beyond the plan:** *(builder)*

---

## Closeout — evidence

**Status:** *(builder)*

**Tree the proofs ran in (and `.env` present?):** *(builder)*

**Result:** *(builder)*

**Files changed:** *(builder)*

**Design decisions:** recorded as [`DL-302`](../design-log.md) (planner).

**Proof — the red run first:** *(builder)*

**Proof — the green run:** *(builder)*

**Guards planted:** *(builder)*

**Module line counts:** *(builder)*

**`make ci`:** *(builder)*

**`make gate-ran`:** *(the planner's, at review)*

**Not met / verified failing:** *(builder)*

---

## Return notes

- *(builder)*

---

## Appendix — the change, measured on the planner's prototype

The planner's prototype is `d24daa79`, the local branch `proto-s279` in `../ta-s279-proto`, cut from
`f091ec61`. All three sections apply with `git apply` to this branch's base. On the prototype
`make ci` exited 0 (5,107 passed, 9 skipped, 100.00 %, audit clean); its 14 planted breaks went red.

### 1. Production — nine files under `agents/` and `contracts/`

```diff
diff --git a/agents/execution/broker_stop_thresholds.py b/agents/execution/broker_stop_thresholds.py
index 0a158461..7b417606 100644
--- a/agents/execution/broker_stop_thresholds.py
+++ b/agents/execution/broker_stop_thresholds.py
@@ -21,7 +21,7 @@ from contracts.positions import (
     active_position_nodes,
     open_positions,
 )
-from contracts.stop_width import decided_stop_pct
+from contracts.stop_width import LineageFills, decided_stop_pct

 if TYPE_CHECKING:
     from agents.execution.broker_stop_types import StopPctSource
@@ -51,6 +51,7 @@ def broker_stop_thresholds(
     }
     plans: list[BrokerStopThresholdPlan] = []
     errors: list[BrokerStopThresholdError] = []
+    fills = LineageFills(graph)
     for ticker, nodes in sorted(positions_by_ticker.items()):
         try:
             plans.append(
@@ -60,6 +61,7 @@ def broker_stop_thresholds(
                     tuple(sorted(nodes, key=lambda node: node.key)),
                     refs_by_ticker[ticker],
                     fallback_stop_pct=fallback_stop_pct,
+                    fills=fills,
                 )
             )
         except ValueError as exc:
@@ -83,8 +85,9 @@ def _threshold_plan_or_raise(
     position_ref: str,
     *,
     fallback_stop_pct: float,
+    fills: LineageFills,
 ) -> BrokerStopThresholdPlan:
-    lots = tuple(_lot(graph, ticker, node, fallback_stop_pct) for node in nodes)
+    lots = tuple(_lot(graph, ticker, node, fallback_stop_pct, fills) for node in nodes)
     stop_pcts = {lot.stop_pct for lot in lots}
     if len(stop_pcts) != 1:
         raise ValueError(f"active lots for {ticker} carry different stop_pct values")
@@ -113,12 +116,18 @@ def _threshold_plan_or_raise(


 def _lot(
-    graph: GraphStore, ticker: Ticker, node: Node, fallback_stop_pct: float
+    graph: GraphStore,
+    ticker: Ticker,
+    node: Node,
+    fallback_stop_pct: float,
+    fills: LineageFills,
 ) -> _Lot:
     try:
         quantity = _int_prop(node, "quantity")
         opened = _int_prop(node, "opened_price_cents")
-        stop_pct, source = decided_stop_pct(graph, node, fallback=fallback_stop_pct)
+        stop_pct, source = decided_stop_pct(
+            graph, node, fallback=fallback_stop_pct, fills=fills
+        )
     except (TypeError, ValueError) as exc:
         message = f"active lot for {ticker} lacks stop threshold inputs"
         raise ValueError(message) from exc
diff --git a/agents/execution/drop_sweep.py b/agents/execution/drop_sweep.py
index d51cab7a..93114f45 100644
--- a/agents/execution/drop_sweep.py
+++ b/agents/execution/drop_sweep.py
@@ -10,6 +10,7 @@ from __future__ import annotations
 from typing import TYPE_CHECKING

 from agents.execution.drop_sweep_ack import has_untracked_order_ack
+from agents.execution.drop_sweep_reads import SweepReads
 from agents.execution.drop_sweep_records import (
     DROP_REASON,
     mark_execution_runs,
@@ -17,12 +18,10 @@ from agents.execution.drop_sweep_records import (
     record_stop_mismatch,
     remember_execution_run,
 )
-from agents.execution.fill_attempts import latest_fill_attempt
 from contracts.broker_lifecycle import (
     is_broker_stop_order,
     is_resolved_drop_status,
 )
-from contracts.broker_stops import broker_stop_orders
 from kernel import fault_boundary

 if TYPE_CHECKING:
@@ -35,6 +34,9 @@ def sweep_unfilled_orders(
 ) -> int:
     """Cancel previous-run non-stop orders and record each dropped decision."""
     broker_orders = _read_broker_orders(broker, sink)
+    reads = _read_graph(graph, sink) if broker_orders else None
+    if reads is None:
+        return 0
     dropped = 0
     touched_runs: set[str] = set()
     for order in broker_orders:
@@ -46,7 +48,7 @@ def sweep_unfilled_orders(
             capability="drop_unfilled_orders",
             reraise=False,
         ):
-            recorded = _sweep_order(graph, broker, sink, order, run_id, touched_runs)
+            recorded = _sweep_order(reads, broker, sink, order, run_id, touched_runs)
         if recorded:
             dropped += 1
     with fault_boundary(
@@ -61,15 +63,16 @@ def sweep_unfilled_orders(


 def _sweep_order(
-    graph: GraphStore,
+    reads: SweepReads,
     broker: Broker,
     sink: FaultSink,
     order: BrokerFill,
     run_id: str,
     touched_runs: set[str],
 ) -> bool:
-    fill = latest_fill_attempt(graph, order.idempotency_key)
-    if _skip_order(graph, order, fill, run_id, sink):
+    graph = reads.graph
+    fill = reads.latest_fill(order.idempotency_key)
+    if _skip_order(reads, order, fill, run_id, sink):
         return False
     if _is_resolved_drop(order):
         recorded = record_drop(graph, sink, order, fill, _resolved_drop_status(order))
@@ -78,7 +81,8 @@ def _sweep_order(
         recorded = record_drop(graph, sink, order, fill, "canceled")
     else:
         return False
-    if recorded:
+    if recorded and fill is not None:
+        reads.reread(fill)
         remember_execution_run(graph, fill, touched_runs)
     return recorded

@@ -95,8 +99,20 @@ def _read_broker_orders(broker: Broker, sink: FaultSink) -> tuple[BrokerFill, ..
     return () if capture.fault is not None else orders


+def _read_graph(graph: GraphStore, sink: FaultSink) -> SweepReads | None:
+    with fault_boundary(
+        sink,
+        agent="execution",
+        module="agents.execution.drop_sweep",
+        capability="drop_unfilled_orders",
+        reraise=False,
+    ) as capture:
+        reads = SweepReads.read(graph)
+    return None if capture.fault is not None else reads
+
+
 def _skip_order(
-    graph: GraphStore,
+    reads: SweepReads,
     order: BrokerFill,
     fill: Node | None,
     run_id: str,
@@ -108,9 +124,9 @@ def _skip_order(
         return True
     if _is_current_run(order, fill, run_id):
         return True
-    if fill is None and has_untracked_order_ack(graph, order):
+    if fill is None and has_untracked_order_ack(reads.graph, order):
         return True
-    return _is_stop_order(graph, order, sink)
+    return _is_stop_order(reads, order, sink)


 def _pipeline_owned(order: BrokerFill) -> bool:
@@ -128,9 +144,9 @@ def _is_current_run(order: BrokerFill, fill: Node | None, run_id: str) -> bool:
     return fill is not None and fill.props.get("source_run_id") == run_id


-def _is_stop_order(graph: GraphStore, order: BrokerFill, sink: FaultSink) -> bool:
+def _is_stop_order(reads: SweepReads, order: BrokerFill, sink: FaultSink) -> bool:
     broker_stop = is_broker_stop_order(order)
-    graph_stop = _tracked_as_stop(graph, order)
+    graph_stop = _tracked_as_stop(reads, order)
     if broker_stop != graph_stop:
         record_stop_mismatch(
             sink, order, broker_stop=broker_stop, graph_stop=graph_stop
@@ -138,11 +154,11 @@ def _is_stop_order(graph: GraphStore, order: BrokerFill, sink: FaultSink) -> boo
     return is_broker_stop_order(order) or graph_stop


-def _tracked_as_stop(graph: GraphStore, order: BrokerFill) -> bool:
+def _tracked_as_stop(reads: SweepReads, order: BrokerFill) -> bool:
     return any(
         order.idempotency_key == stop.key
         or order.broker_order_id == stop.broker_order_id
-        for stop in broker_stop_orders(graph)
+        for stop in reads.stops
     )


diff --git a/agents/execution/drop_sweep_reads.py b/agents/execution/drop_sweep_reads.py
new file mode 100644
index 00000000..34caf09a
--- /dev/null
+++ b/agents/execution/drop_sweep_reads.py
@@ -0,0 +1,46 @@
+"""The graph labels one drop sweep reads, each read once (EXEC-PERF-02).
+
+Agent: execution
+Role: hold the Fill and BrokerStopOrder labels for one head-of-run sweep, so the
+      sweep reads each once rather than once per broker order (DL-302).
+External I/O: injected GraphStore reads.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from typing import TYPE_CHECKING
+
+from agents.execution.fill_attempts import latest_fill_attempt_in
+from contracts.broker_stops import broker_stop_orders
+
+if TYPE_CHECKING:
+    from contracts.broker_stops import BrokerStopOrder
+    from kernel import GraphStore, Node
+
+
+@dataclass(frozen=True)
+class SweepReads:
+    """One sweep's Fill nodes by key, and its BrokerStopOrder facts."""
+
+    graph: GraphStore
+    fills: dict[str, Node]
+    stops: tuple[BrokerStopOrder, ...]
+
+    @classmethod
+    def read(cls, graph: GraphStore) -> SweepReads:
+        """Read both labels once, in the store's list order."""
+        fills = {node.key: node for node in graph.list_nodes("Fill")}
+        return cls(graph=graph, fills=fills, stops=broker_stop_orders(graph))
+
+    def latest_fill(self, broker_idempotency_key: str) -> Node | None:
+        """The latest Fill attempt for one broker key, as a fresh read would find it."""
+        return latest_fill_attempt_in(self.fills.values(), broker_idempotency_key)
+
+    def reread(self, fill: Node) -> None:
+        """Hold the stored copy of a Fill the sweep has just written.
+
+        A drop marks the one Fill it found; a later order whose chain ends on the same
+        Fill must see that mark, as it did when every order read the label afresh.
+        """
+        self.fills[fill.key] = self.graph.get_node("Fill", fill.key) or fill
diff --git a/agents/execution/fill_attempts.py b/agents/execution/fill_attempts.py
index c261c334..b325b61e 100644
--- a/agents/execution/fill_attempts.py
+++ b/agents/execution/fill_attempts.py
@@ -11,7 +11,7 @@ from dataclasses import dataclass
 from typing import TYPE_CHECKING, Any

 if TYPE_CHECKING:
-    from collections.abc import Mapping
+    from collections.abc import Iterable, Mapping

     from kernel import GraphStore, Node

@@ -52,7 +52,14 @@ def select_fill_attempt(

 def latest_fill_attempt(graph: GraphStore, broker_idempotency_key: str) -> Node | None:
     """Return the latest Fill node for one broker idempotency key."""
-    chain = fill_attempt_chain(graph, broker_idempotency_key)
+    return latest_fill_attempt_in(graph.list_nodes("Fill"), broker_idempotency_key)
+
+
+def latest_fill_attempt_in(
+    fills: Iterable[Node], broker_idempotency_key: str
+) -> Node | None:
+    """Return the latest attempt for one broker key from Fill nodes already read."""
+    chain = fill_attempt_chain_in(fills, broker_idempotency_key)
     return None if not chain else chain[-1]


@@ -60,11 +67,14 @@ def fill_attempt_chain(
     graph: GraphStore, broker_idempotency_key: str
 ) -> tuple[Node, ...]:
     """Return Fill nodes for one broker key, ordered by attempt ordinal."""
-    nodes = [
-        node
-        for node in graph.list_nodes("Fill")
-        if _belongs_to_chain(node, broker_idempotency_key)
-    ]
+    return fill_attempt_chain_in(graph.list_nodes("Fill"), broker_idempotency_key)
+
+
+def fill_attempt_chain_in(
+    fills: Iterable[Node], broker_idempotency_key: str
+) -> tuple[Node, ...]:
+    """Return the chain for one broker key from Fill nodes already read."""
+    nodes = [node for node in fills if _belongs_to_chain(node, broker_idempotency_key)]
     return tuple(
         sorted(nodes, key=lambda node: attempt_ordinal(node, broker_idempotency_key))
     )
diff --git a/agents/monitor/decide.py b/agents/monitor/decide.py
index e49ee9d3..be3265a9 100644
--- a/agents/monitor/decide.py
+++ b/agents/monitor/decide.py
@@ -16,6 +16,7 @@ from kernel import AgentFault
 from kernel.fault_graph import GraphFaultSink

 if TYPE_CHECKING:
+    from contracts.stop_width import LineageFills
     from kernel import FaultSink, GraphStore, Node


@@ -25,11 +26,13 @@ def evaluate_one(
     monitor_run_id: str,
     position: Node,
     current_price_cents: int,
+    *,
+    fills: LineageFills | None = None,
 ) -> bool:
     """Evaluate one open position; return whether its stop is breached."""
     ticker = str(position.props["ticker"])
     observation, trigger = evaluate_position(
-        exit_position(graph, position), current_price_cents
+        exit_position(graph, position, fills=fills), current_price_cents
     )
     breached = observation == "stop_breached"
     write_check(
diff --git a/agents/monitor/domain/positions.py b/agents/monitor/domain/positions.py
index ad709d1f..a8746c02 100644
--- a/agents/monitor/domain/positions.py
+++ b/agents/monitor/domain/positions.py
@@ -15,6 +15,7 @@ from agents.monitor.domain.exit_rules import ExitPosition
 from contracts.stop_width import decided_stop_pct

 if TYPE_CHECKING:
+    from contracts.stop_width import LineageFills
     from kernel import GraphStore, Node


@@ -62,15 +63,18 @@ def position_from_fill(
     )


-def exit_position(graph: GraphStore, node: Node) -> ExitPosition:
+def exit_position(
+    graph: GraphStore, node: Node, *, fills: LineageFills | None = None
+) -> ExitPosition:
     """Return an exit-rule position whose stop is the decided width (DL-223).

     The width comes from the shared resolver, so the watchdog reads the same
-    stop that execution rests at the broker and the analyst checks.
+    stop that execution rests at the broker and the analyst checks. A pass over
+    the book passes one `fills` for every position (DL-302).
     """
     return ExitPosition(
         opened_price_cents=int(node.props["opened_price_cents"]),
-        stop_pct=decided_stop_pct(graph, node).stop_pct,
+        stop_pct=decided_stop_pct(graph, node, fills=fills).stop_pct,
     )


diff --git a/agents/monitor/run.py b/agents/monitor/run.py
index 2cf3422f..f2905764 100644
--- a/agents/monitor/run.py
+++ b/agents/monitor/run.py
@@ -23,6 +23,7 @@ from agents.monitor.store import (
     write_monitor_run,
 )
 from contracts.monitor import CloseDecisionSet
+from contracts.stop_width import LineageFills
 from kernel.errors import fault_boundary

 if TYPE_CHECKING:
@@ -92,6 +93,7 @@ def _evaluate_positions(
 ) -> tuple[int, int]:
     positions_checked = 0
     stop_breaches = 0
+    fills = LineageFills(graph)
     for position in positions:
         ticker = str(position.props["ticker"])
         current_price_cents = prices.get(ticker)
@@ -100,7 +102,9 @@ def _evaluate_positions(
             continue
         positions_checked += 1
         stop_breaches += int(
-            evaluate_one(graph, sink, monitor_run_id, position, current_price_cents)
+            evaluate_one(
+                graph, sink, monitor_run_id, position, current_price_cents, fills=fills
+            )
         )
     return positions_checked, stop_breaches

diff --git a/contracts/positions.py b/contracts/positions.py
index 8d1a43e6..3b11bf6c 100644
--- a/contracts/positions.py
+++ b/contracts/positions.py
@@ -12,7 +12,7 @@ from decimal import ROUND_HALF_UP, Decimal
 from typing import TYPE_CHECKING

 from contracts.position_refs import position_ref_for_keys
-from contracts.stop_width import decided_stop_pct
+from contracts.stop_width import LineageFills, decided_stop_pct

 if TYPE_CHECKING:
     from contracts.common import Ticker
@@ -96,8 +96,9 @@ def open_position_stop_thresholds(
     graph: GraphStore,
 ) -> tuple[PositionStopThreshold, ...]:
     """Return weighted stop inputs for active positions grouped by ticker."""
+    fills = LineageFills(graph)
     return tuple(
-        _stop_threshold(graph, ticker, tuple(sorted(nodes, key=lambda n: n.key)))
+        _stop_threshold(graph, ticker, tuple(sorted(nodes, key=lambda n: n.key)), fills)
         for ticker, nodes in sorted(_active_nodes_by_ticker(graph).items())
     )

@@ -154,9 +155,9 @@ def _basis_lot(node: Node) -> PositionBasisLot | None:


 def _stop_threshold(
-    graph: GraphStore, ticker: Ticker, nodes: tuple[Node, ...]
+    graph: GraphStore, ticker: Ticker, nodes: tuple[Node, ...], fills: LineageFills
 ) -> PositionStopThreshold:
-    lots = tuple(_stop_lot(graph, ticker, node) for node in nodes)
+    lots = tuple(_stop_lot(graph, ticker, node, fills) for node in nodes)
     stop_pcts = {stop_pct for _quantity, _opened, stop_pct in lots}
     if len(stop_pcts) != 1:
         raise ValueError(f"active lots for {ticker} carry different stop_pct values")
@@ -178,12 +179,14 @@ def _stop_threshold(
     )


-def _stop_lot(graph: GraphStore, ticker: Ticker, node: Node) -> tuple[int, int, float]:
+def _stop_lot(
+    graph: GraphStore, ticker: Ticker, node: Node, fills: LineageFills
+) -> tuple[int, int, float]:
     try:
         return (
             int(node.props["quantity"]),
             int(node.props["opened_price_cents"]),
-            decided_stop_pct(graph, node).stop_pct,
+            decided_stop_pct(graph, node, fills=fills).stop_pct,
         )
     except (KeyError, TypeError, ValueError) as exc:
         message = f"active lot for {ticker} lacks stop threshold inputs"
diff --git a/contracts/stop_width.py b/contracts/stop_width.py
index d1b44adb..e8138860 100644
--- a/contracts/stop_width.py
+++ b/contracts/stop_width.py
@@ -28,6 +28,25 @@ PRODUCTION_RUN_PREFIX = "pm-run-"
 _EXECUTES_EDGE = "EXECUTES"


+class LineageFills:
+    """The Fill label for one pass over a held book: read once, and only if asked.
+
+    A pass that resolves many Positions shares one of these, so an adopted Position
+    costs no fresh read of every Fill (DL-302).
+    """
+
+    def __init__(self, graph: GraphStore) -> None:
+        """Hold the store; nothing is read until an adopted Position asks."""
+        self._graph = graph
+        self._nodes: tuple[Node, ...] | None = None
+
+    def nodes(self) -> tuple[Node, ...]:
+        """Every Fill node, read on the first call and held for the pass."""
+        if self._nodes is None:
+            self._nodes = self._graph.list_nodes("Fill")
+        return self._nodes
+
+
 class DecidedStop(NamedTuple):
     """A stop width and the source it was read from."""

@@ -36,7 +55,11 @@ class DecidedStop(NamedTuple):


 def decided_stop_pct(
-    graph: GraphStore, position: Node, *, fallback: float | None = None
+    graph: GraphStore,
+    position: Node,
+    *,
+    fallback: float | None = None,
+    fills: LineageFills | None = None,
 ) -> DecidedStop:
     """Return the stop width the PM decided for a held Position, and its source.

@@ -44,11 +67,12 @@ def decided_stop_pct(
     whose quantity and broker price equal it exactly; with no exact match it keeps
     the width it recorded at adoption and says `fallback`. Any other Position is
     its own `position` source. `fallback` applies only to a Position that records
-    no width at all; without one, that Position raises ValueError.
+    no width at all; without one, that Position raises ValueError. A pass over
+    many Positions passes one `fills` for all of them.
     """
     recorded = _recorded_stop_pct(position)
     if position.props.get("provenance") == ADOPTED_PROVENANCE:
-        decided = _lineage_stop_pct(graph, position)
+        decided = _lineage_stop_pct(graph, position, fills or LineageFills(graph))
         if decided is not None:
             return DecidedStop(decided, "lineage")
         return DecidedStop(_or_fallback(recorded, fallback), "fallback")
@@ -73,9 +97,11 @@ def _or_fallback(recorded: float | None, fallback: float | None) -> float:
     return width


-def _lineage_stop_pct(graph: GraphStore, position: Node) -> float | None:
+def _lineage_stop_pct(
+    graph: GraphStore, position: Node, fills: LineageFills
+) -> float | None:
     matches = sorted(
-        (fill for fill in graph.list_nodes("Fill") if _equals_holding(fill, position)),
+        (fill for fill in fills.nodes() if _equals_holding(fill, position)),
         key=lambda fill: (str(fill.props.get("submitted_at") or ""), fill.key),
     )
     if not matches:
```

### 2. The law — three `laws.md`

```diff
diff --git a/agents/analyst/laws/laws.md b/agents/analyst/laws/laws.md
index 65879073..b6b30144 100644
--- a/agents/analyst/laws/laws.md
+++ b/agents/analyst/laws/laws.md
@@ -1,6 +1,6 @@
 # `Analyst` — Laws

-**Prefix:** `ANLZ` · **status:** LOCKED v1.10 · **Owner:** Yury Gurevich
+**Prefix:** `ANLZ` · **status:** LOCKED v1.11 · **Owner:** Yury Gurevich

 > Score scanner candidates into evidence-backed trade recommendations — or explain clearly
 > why none qualify today.
@@ -271,6 +271,10 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 - **ANLZ-PERF-01** — The analyst's latency budget is dominated by two provider round-trips
   (market data + regime). The scoring computation itself (all pillars for all candidates in a
   typical 5-candidate set) is pure in-process Python and adds negligible latency.
+- **ANLZ-PERF-02** — One run's held-stop read (`ANLZ-OUT-09`'s stop inputs) reads the `Fill` label
+  at most once, whatever the number of held positions, and not at all when no position is
+  broker-adopted; each position still takes its own lineage width. *(DL-302; measured 11.2 MB a
+  run before it, 32 adopted positions.)*

 ---

@@ -431,3 +435,7 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 - v1.10 — amendment (S259 / DL-276, 2026-10-08). `PARAM` only: the Type cell of
   `scaled_stop_atr_multiplier` states the bounds the settings enforce; S258 had recorded it as
   excused. No clause, default or code bound changes; 29 / 52 unchanged.
+
+- v1.11 — amendment (S279 / DL-302, 2026-10-15). Adds and proves `ANLZ-PERF-02`: the held-stop
+  read shares one `Fill` read across the book, where it read the label once per position. No
+  threshold, stop check or recommendation changes; 29 / 52 → 30 / 53.
diff --git a/agents/execution/laws/laws.md b/agents/execution/laws/laws.md
index 69117a1e..280f64a5 100644
--- a/agents/execution/laws/laws.md
+++ b/agents/execution/laws/laws.md
@@ -1,6 +1,6 @@
 # `Execution` — Laws

-**Prefix:** `EXEC` · **status:** LOCKED v1.13 · **Owner:** Yury Gurevich
+**Prefix:** `EXEC` · **status:** LOCKED v1.14 · **Owner:** Yury Gurevich

 > Be the single, auditable, idempotent broker boundary. Execute only what the portfolio
 > manager has approved and the stage gate allows.
@@ -328,6 +328,13 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 - **EXEC-PERF-01** — Each broker order submission is bounded by `alpaca_timeout` (default
   15 s). Sequential submission of a typical 5-order set completes within 75 s in the worst
   case. No external I/O beyond the broker is performed during `submit`.
+- **EXEC-PERF-02** — A pass reads a whole graph label once, never once per item it walks. One
+  run-start drop sweep reads `Fill` and `BrokerStopOrder` at most once each, whatever the number of
+  broker orders, and neither when the broker lists no order; a drop it writes is seen by every later
+  order in the same sweep, as a fresh read would see it. One stop-threshold plan reads `Fill` at most
+  once for every active position's decided width, and not at all when no position is
+  broker-adopted. A failed read in the sweep is one contained fault and no order is touched.
+  *(Declares the bound decided in DL-302; measured 126.3 MB of 136 MB per run start before it.)*

 ---

@@ -520,3 +527,7 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   corrected). Payload/grace tests and the existing submit-anchor test prove the new clause;
   39 / 65 -> 40 / 66. No broker, posture, grace, exit or protective-stop policy changes.
 - **v1.13 — S258 / DL-276 (2026-10-08).** PARAM only: reconciles the bounds of `slippage_bps`, `min_promotion_runs`, `min_approval_rate` and `alpaca_timeout` with settings; no clause, default or code bound changes.
+- **v1.14 — S279 / DL-302 (2026-10-15).** New `EXEC-PERF-02`: the drop sweep reads `Fill` and
+  `BrokerStopOrder` once per sweep and the stop-threshold plan reads `Fill` once per plan, where both
+  read the whole label once per item. Why: 348 broker orders made each run start list 346 Fills 348
+  times. No drop, cancel, stop or reconciliation decision changes; 40 / 66 -> 41 / 67.
diff --git a/agents/monitor/laws/laws.md b/agents/monitor/laws/laws.md
index ab28acd3..057293cb 100644
--- a/agents/monitor/laws/laws.md
+++ b/agents/monitor/laws/laws.md
@@ -1,6 +1,6 @@
 # `Monitor` — Laws

-**Prefix:** `MON` · **status:** LOCKED v1.3 · **Owner:** Yury Gurevich
+**Prefix:** `MON` · **status:** LOCKED v1.4 · **Owner:** Yury Gurevich

 > Watch open positions and decide when to exit under policy (stop, target, time, regime)
 > — then hand every close to execution and explain every hold.
@@ -159,6 +159,10 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 - **MON-PERF-01** — `price_lookback_days=2` keeps the provider request window narrow.
 - **MON-PERF-02** — The monitor holds no open connections between calls; provider request latency
   is bounded by the bus timeout (no infinite wait).
+- **MON-PERF-03** — One end-of-run evaluation reads the `Fill` label at most once for every
+  position's decided stop width, whatever the number of positions, and not at all when no position
+  is broker-adopted; each position still takes its own lineage width. *(DL-302; measured 11.1 MB a
+  run before it, 32 adopted positions.)*

 ## Capability declaration (`CAP`)

@@ -213,3 +217,6 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   linked snapshot. Why: snapshot-side discovery downloaded snapshots that never become sync work.
   The existing work and marker writer are unchanged; a later snapshot for a synced request is
   excluded and a half-written marker is repaired. DRIFT-097 corrected; 21 / 46 unchanged.
+- v1.4 — S279 / DL-302 (2026-10-15). New `MON-PERF-03`: the end-of-run evaluation shares one
+  `Fill` read across its positions' stop widths, where it read the label once per position. No
+  check, breach or adoption decision changes; 21 / 46 -> 22 / 47.
```

### 3. One existing test — S258's pin of the execution book's version

```diff
diff --git a/tests/test_param_law_sync_execution_rows.py b/tests/test_param_law_sync_execution_rows.py
index f38f1063..129ba257 100644
--- a/tests/test_param_law_sync_execution_rows.py
+++ b/tests/test_param_law_sync_execution_rows.py
@@ -1,10 +1,11 @@
 """DL-276 D3 pins the four authorized execution PARAM amendments.

 Agent: tooling
-Role: pin exact Type cells, next book version and the one S258 Changelog line.
+Role: pin exact Type cells, the book at S258's version or later, and its Changelog line.
 External I/O: read the execution law book only.
 """

+import re
 from pathlib import Path

 from scripts.param_law_sync_sources import param_rows
@@ -29,5 +30,7 @@ def test_the_four_execution_rows_state_the_decided_bounds():
     rows = param_rows(_ROOT, "execution")
     assert {name: rows[name].type_cell for name in _CELLS} == _CELLS
     book = (_ROOT / _BOOK).read_text(encoding="utf-8")
-    assert "**status:** LOCKED v1.13" in book
+    status = re.search(r"\*\*status:\*\* LOCKED v1\.(\d+) ", book)
+    assert status is not None
+    assert int(status.group(1)) >= 13  # v1.13 is S258's; a later amendment moves it on
     assert book.splitlines().count(_CHANGELOG) == 1
```
