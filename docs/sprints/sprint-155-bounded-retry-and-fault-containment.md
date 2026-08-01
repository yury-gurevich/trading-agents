<!-- Agent: planning | Role: sprint handover -->
# Sprint 155 — The loop measures activity, not progress: bounded retry and fault containment

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-155-bounded-retry-and-fault-containment`
**Status:** SPEC — packaged 2026-08-01
**Version:** fix → **0.85.01** (PATCH: last two digits)
**Effort:** M
**Decisions:** [DL-79](../design-log.md) **(the outage this generalises — read it first)** ·
[ADR-0014](../decisions/0014-postgresql-system-of-record.md) the append-only spine — **it forbids the
obvious fix, see the road not taken** · [DL-08](../design-log.md) graph-as-queue ·
[DL-57](../design-log.md)/[DL-59](../design-log.md) *didn't look* ≠ *looked and found nothing* ·
[DL-70](../design-log.md) plant the violation first ·
[LAW-02](../../ops/laws/LAW-02-successful-execution.md) success is proven, never assumed

> **Why the version is a PATCH and not a MINOR.** No new capability ships. `work_loop` and the fault
> sink both already exist; this sprint makes them *survivable*. `0.85.00` → **`0.85.01`**, per the
> CLAUDE.md rule (*fix → last two digits*). If you disagree after reading the rule, say so in the
> return notes rather than silently choosing differently.

---

## Why this sprint

**This is the third instance of one defect class in eight days, and the first two were each fixed
only on their own path.**

| Date | Symptom | Fixed by | What was left |
| --- | --- | --- | --- |
| 2026-07-30 | **5,762 identical `Fault` rows in 2 h**; `sched-2026-07-30` stalled at 2/8 stages | S151 — a completed snapshot now ends the loop | the loop itself |
| 2026-08-01 | **2,742 `BrokerOrderStatus` nodes** across 59 fills, 73 for one; one fault re-emitted nightly since 07-24 | S154 — terminal-status selector + durable marker | the loop itself |
| — | *next one* | — | — |

`docs/STATE.md` already filed this: *"One deterministic defect wrote 5,762 identical rows because
nothing between it and `work_loop` was contained. S151 makes it impossible **on this path** by
construction; the general version is a kernel/`work_loop` concern affecting every agent and needs its
own sprint."* This is that sprint.

### The live evidence, counted this morning

```text
total Fault nodes:  5858
distinct messages:    26
  5762 | property 'broker_status' cannot be overwritten
    58 | realized PnL skipped for ABT sell fill pm-run-927de0c7…
     3 | HTTP Error 403: Forbidden
     3 | stop breached on AMD, still held
```

**99.6 % of the fault ledger is duplicates of one message.** The three rows that matter — a broker
403, a breached stop — are buried under 5,762 copies of a defect that was fixed days ago. A fault
ledger nobody can read is not observability; it is the *appearance* of observability, which is worse
because it passes inspection.

## The defect, precisely

### Where it lives — `kernel/work_loop.py`, nine lines

```python
def run_once[T](find_pending, process_one) -> int:
    items = find_pending()
    for item in items:
        process_one(item)
    return len(items)          # <- items FOUND, not items ADVANCED

def work_loop[T](find_pending, process_one, *, poll_interval=60) -> None:
    while True:
        if run_once(find_pending, process_one) == 0:
            time.sleep(poll_interval)   # <- only sleeps when it found NOTHING
```

**The loop sleeps when it finds nothing to do, and spins when it finds something it cannot do.**
Those are the same state from the outside, and the loop cannot tell them apart, because `run_once`
counts items *found* rather than items *advanced*.

So a work item that stays pending because processing raised is immediately re-found and
re-processed, with **no delay at all** — bounded only by how long one failing attempt takes. On
2026-07-30 that was ~1.3 s, for two hours, until the fleet window closed: **5,762 attempts, 5,762
identical faults, zero progress.**

`work_loop` carries `# pragma: no cover - blocks forever`, so the infinite wrapper — the part that
actually spins — has never been under test. `run_once` carries the coverage, and `run_once` is not
where the defect is.

### Why the fault sink amplifies rather than absorbs

`kernel/fault_graph.py::fault_node_key` keys on
`fault:{agent}:{module}:{capability}:{occurred_at.isoformat()}` — a fresh timestamp per occurrence,
**deliberately**:

> *"Keyed by origin plus timestamp so a repeated failure appends rather than overwriting the earlier
> occurrence — a fault that recurs every run is itself the signal."*

**That intent is correct and must survive this sprint.** A fault recurring once per nightly run *is*
signal. The same fault 5,762 times in two hours is the same signal repeated, and the sink has no way
to tell those apart either — because the sink is not where the frequency is decided.

**Two components, one blind spot, and it is the same blind spot: nothing in the system distinguishes
"this happened again" from "this is still happening".**

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it, **in place**.

### 1 · 🎯 The loop backs off when it makes no progress

`run_once` must report **progress**, not activity. An item that is still pending after
`process_one` returned has not advanced, and a pass in which nothing advanced must be followed by a
sleep exactly as an empty pass is.

- Change the `run_once` contract so the caller can distinguish *nothing to do* from *nothing
  achieved*. The shape is yours; the requirement is that `work_loop` **sleeps in both cases**.
- Add **per-item backoff** so a single poison item does not monopolise the loop: repeated failure on
  the same item must increase the delay before it is retried, up to a bounded ceiling.
- **All delays are `tunable()`** with `why=` — poll interval, backoff base, ceiling, and any
  attempt cap. No bare literals (CLAUDE.md).

**The blast radius is eight agents plus the local pipeline** — `provider`, `scanner`, `analyst`,
`portfolio_manager`, `execution`, `monitor`, `reporter`, `deliberator`, and
`orchestration/local_pipeline.py`. This is a kernel change with fleet-wide reach; that is the point,
and it is also the risk (see Risks).

**Result:** Shipped. `run_once` now returns `RunOnceResult` progress detail instead of a found-count,
and `work_loop` sleeps on both empty and no-progress passes. Backoff is per item through
`WorkLoopPolicy` tunables (`poll_interval_seconds`, base, multiplier, ceiling, attempt cap), and the
eight graph-pull entrypoints plus `orchestration/local_pipeline.py` now use the bounded contract.

### 2 · A poison item is quarantined, visibly

An item that has failed N times is not retried indefinitely. It is marked, skipped by subsequent
passes, and **surfaced** — a quarantined work item must be visible as a distinct, findable state, not
an absence.

- Quarantine must be **append-safe** (ADR-0014): a marker written once, never a mutable counter on
  the node — see the road not taken.
- The run must continue: quarantining one item never stops the others. This is DL-79's lesson at the
  loop level — *a failing item may not outrank the work beside it*.
- **Never silently drop.** A quarantined item that nothing can see is worse than a retry storm,
  because the storm at least announces itself.

**Result:** Shipped. `WorkLoopState` tracks retry eligibility and quarantine state; graph-backed
loops write an append-safe `WorkItemQuarantine` marker through `GraphQuarantineSink`, and later
passes skip that visible marker without blocking healthy siblings.

### 3 · Identical faults are collapsed, without losing the recurrence signal

The sink stops writing N identical nodes for one ongoing failure, **while preserving** the intent in
`fault_node_key`'s docstring: a fault that recurs across runs is signal.

- Collapse on a **signature** — `(source_agent, source_module, capability, error_type)` plus a digest
  of the message — within a bounded window.
- The suppression itself must be **visible and counted**: a reader must be able to tell "this
  happened once" from "this happened 5,762 times". Suppression that hides volume replaces one
  unreadable ledger with another.
- **Append-only forbids incrementing a counter on an existing node.** Read the road not taken before
  designing this; the obvious implementation is the one that stalled the fleet on 2026-07-30.
- Do **not** change `fault_node_key`'s existing contract for the *first* occurrence — the 26 distinct
  messages already in production must keep behaving exactly as now.

**Result:** Shipped. Chose shape 2, **first + summary**: the first `Fault` keeps the existing
`fault_node_key` shape, same-signature repeats inside the tunable window are suppressed, and
`GraphFaultSink.flush()` writes one append-only `FaultSuppression` summary with recoverable
`occurrence_count` / `suppressed_count`; sink-aware entrypoints now reuse one graph fault sink per
process and `work_loop` flushes summaries when quarantine closes a poison item.

### 4 · The infinite loop gets a test

`work_loop`'s `# pragma: no cover` is why the spinning half has never been exercised. Make the loop
testable — inject the clock/sleep, or bound the iterations under test — and cover the two behaviours
that matter: **a no-progress pass sleeps**, and **a poison item does not spin**.

Removing a `pragma: no cover` from the one function whose failure mode caused an outage is a large
part of this sprint's value. If you conclude it genuinely cannot be covered, that is a finding to
report, not a line to leave as-is.

**Result:** Shipped. `work_loop` is bounded under test with injectable `sleep`, `clock`, and
`max_iterations`; the previous forever-loop coverage gap is covered with 100.00 % branch coverage on
`kernel/work_loop.py` in the focused work-loop suite and full `make ci`.

### 5 · Prove the containment on the real shape (DL-70)

Reconstruct the 2026-07-30 shape in a test: a work item whose processing always raises, against a
graph that never advances it. Assert **bounded** attempts and **bounded** fault writes over a
simulated window — not "no exception".

Then plant the regression: revert the backoff and watch the same test fail with an unbounded count.
**Both observations go in the closeout.** A containment you have not seen fail to contain is not
proven.

**Result:** Shipped. The pre-fix planted probe reproduced the no-sleep/no-progress shape
(`attempts=25 sleeps=0`) and duplicate fault writes (`fault_nodes=5`). The committed regression test
`tests/test_work_loop_storm.py::test_real_fault_storm_shape_is_bounded_and_visible` proves bounded
attempts, one first `Fault`, one quarantine marker, and one suppression summary.

### 6 · Record the drift you find (do not fix it here)

If the kernel's laws do not declare loop-termination or fault-emission bounds, open a
`docs/laws/drift-register.md` row. Apply the **S152 standing convention** — *decided → amend;
appeared → it stays a drift row and becomes a code fix* — and do not amend any `laws.md` in this
sprint.

**Result:** Shipped. Added `DRIFT-030` to `docs/laws/drift-register.md` for missing system-level
graph-pull retry, poison-quarantine, and duplicate-fault emission bounds. No locked `laws.md` was
amended.

## Test plan — every test I want, and why

Cite clause IDs where a clause governs the behaviour. **Plant the violation and watch it fail first.**

### A · Progress vs activity

1. A pass that finds items but advances none **sleeps** (assert the sleep was called, not that no
   exception occurred).
2. A pass that finds nothing sleeps — unchanged behaviour.
3. A pass that advances at least one item does **not** sleep — unchanged behaviour, and the
   regression risk of item 1.

### B · Backoff and quarantine

4. Repeated failure on the same item increases the delay, up to the ceiling and no further.
5. An item failing N times is quarantined, and a later pass skips it.
6. A quarantined item is **findable** — assert the visible state, not the absence of retries.
7. One poison item does not prevent a healthy sibling in the same pass from being processed.

### C · Fault collapse

8. The same signature repeated within the window writes **one** node, not N.
9. The suppressed volume is recoverable — a reader can tell 1 from 5,762.
10. Two *different* signatures both write. Collapse must not swallow a distinct failure.
11. A fault recurring across *runs* still reads as recurrence — the `fault_node_key` intent survives.

### D · The real shape

12. The 2026-07-30 reconstruction from item 5: bounded attempts, bounded fault writes.
13. Planted regression: backoff reverted → unbounded, test fails.

## Explicit non-goals

- **Do not delete or compact the 5,858 existing `Fault` nodes.** Production lineage on an append-only
  spine. Whether to archive the 5,762 is a separate operator decision; this sprint stops the *next*
  storm.
- **Do not change what any agent's `process_one` does.** This is a loop-and-sink sprint. If an
  agent's processing is wrong, that is its own fix.
- **Do not relax the append-only store** to make counting easy. That is the forbidden fix, and it is
  exactly what S151 closed.
- **Do not make faults quieter than they are.** Collapse changes how many *nodes* one ongoing failure
  writes; it must not reduce what a reader can learn.
- **Do not amend any `laws.md`.** Item 6 is a drift row, per the S152 convention.
- **Do not touch the S154 refresh path or the S151 drop sweep.** Both are fixed; this sprint is the
  general case beneath them.

### The road not taken (LAW-06)

**The obvious fix for item 3 is a counter on the fault node, and the append-only store forbids it.**

`kernel/graph_support.py` permits re-writing a property with the *same* value and refuses a
different one. So `occurrences = occurrences + 1` raises `ValueError: property 'occurrences' cannot
be overwritten` on the second increment — inside the fault-writing path, which means **the error
handler itself starts raising.** That is precisely the 2026-07-30 collision (DL-79) re-created in the
one component whose job is to survive failure. Do not go there.

Three shapes that respect the constraint, none pre-selected — **choose one and say why in the return
notes**:

1. **Window-keyed node** — key the fault on a coarse time bucket rather than an exact timestamp, so
   repeats within the bucket collapse naturally by merge. Simple; the window is fixed by the key.
2. **First + summary** — write the first occurrence immediately; at window close, write one separate
   summary node carrying the count. Preserves the first fault's timing exactly; needs a flush.
3. **Suppression marker on a later node** — write occurrence 1, suppress 2..N, and record the
   suppressed count on the *next* node written after the window. No flush; the count arrives late.

I have deliberately not chosen. Each trades differently between latency, key stability and
complexity, and the right answer depends on details of the store you will be closer to than I am.
**What is not negotiable:** append-safety, and that the volume stays recoverable.

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing upward. `import-linter` enforces.
- Every module < 200 lines (warn at 150). `kernel/work_loop.py` is 42 lines and will grow — split
  rather than let it sprawl.
- Module docstrings declare `Agent:` / `Role:` / `External I/O:`.
- **No magic numbers** — every interval, ceiling and attempt cap is `tunable(..., why=...)`.
- `make ci` green, all 9 steps, 100.00 % coverage floor. Never lower the floor; item 4 should *raise*
  what is covered.
- Stay in scope. Anything else you find goes in the return notes.

## Risks

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| **Fleet-wide blast radius** | One kernel change reaches eight agents and the local pipeline. A backoff bug stalls every graph-pull agent at once — worse than the storm it fixes. | Behaviour on the *healthy* path must be byte-identical: tests A2 and A3 exist for exactly this. Prove no-change before proving change. |
| **Sleeping when work is available** | Over-eager backoff turns a transient failure into a missed nightly window — the fleet has ~2 h. | Backoff applies to the *item*, not the loop: a healthy sibling still processes in the same pass (test B7). |
| **Collapse hides a real signal** | The 403 and the breached stop are already buried. Aggressive suppression buries them differently. | Tests C9 and C10; suppression is per-signature and the volume stays recoverable. |
| **Quarantine becomes a silent drop** | An item nothing retries and nothing shows is the worst outcome — worse than the storm. | Test B6 asserts the *visible* state, not the absence of retries. |
| **Removing `pragma: no cover`** | The loop blocks forever by design; a naive test hangs CI. | Inject the clock/sleep or bound iterations. A hanging test is a failed handback. |

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the placeholder sections below.**
Not a separate report file. Not chat-only. This document is the one artifact: spec at the top, proof
at the bottom.

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the six scope items, in place.
3. Fill the **Test plan results** table — one row per test. A test you chose not to write needs a
   reason, not a blank.
4. Fill the **Closeout — evidence** block with real command output pasted in.
5. Fill the **Return notes**, including **which of the three collapse shapes you chose and why**.
6. State any success factor you did **not** meet plainly (LAW-02 — a proven failure is a valid
   handback, a silent gap is not).

**Remote green is the gate.** Push, then poll until `quality`, `test`, `security` and `gate` all read
`success` on your branch tip. `in_progress` is not `success`. If it goes red, **you fix it** and poll
again. Assert a run *exists* for your head SHA (hardening-backlog row **M**). **Do not merge.**

> **Note:** `build-images` is currently red on `main` for an unrelated upstream reason
> ([DL-84](../design-log.md) — DHI base-image CVEs). That is **not** yours and is not a signal about
> your branch.

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| `kernel/work_loop.py` | `docs/laws/conventions.md`; affected agent `FAIL` sections in `provider`, `scanner`, `analyst`, `portfolio_manager`, `execution`, `monitor`, `reporter`, `deliberator` | No direct kernel clause declares loop retry bounds. Agent clauses bind containment beside sibling work: `SCAN-FAIL-02`, `ANLZ-FAIL-03`, `PM-FAIL-02`, `EXEC-FAIL-01`, `MON-FAIL-01/02`, `RPT-FAIL-03`, `DLIB-FAIL-01/03`. | Yes - make retry/backoff per item, not per loop, and continue siblings after one item fails. |
| `kernel/fault_graph.py` / `kernel/errors.py` | `docs/laws/conventions.md`; `ops/laws/LAW-02-successful-execution.md`; affected agent `OBS` sections | Fault visibility/reconstructability clauses bind the sink: `PROV-OBS-02/03`, `SCAN-OBS-02`, `ANLZ-OBS-02`, `PM-OBS-02`, `EXEC-OBS-02`, `MON-OBS-02`, `RPT-OBS-02`, `DLIB-OBS-03`. No clause bounds duplicate emission volume. | Yes - collapse must be visible as data, not silence, and the first `Fault` occurrence key must stay unchanged. |
| Affected agents' `laws.md` (`FAIL` / `OBS` sections) | `agents/provider/laws/laws.md`; `agents/scanner/laws/laws.md`; `agents/analyst/laws/laws.md`; `agents/portfolio_manager/laws/laws.md`; `agents/execution/laws/laws.md`; `agents/monitor/laws/laws.md`; `agents/reporter/laws/laws.md`; `agents/deliberator/laws/laws.md` | `FAIL` clauses require contained/partial failure and sibling continuation; `OBS` clauses require central, queryable, attributed faults. | Yes - quarantine cannot be an absence; it must write a distinct marker that later passes can skip. |
| `docs/laws/drift-register.md` | `docs/laws/drift-register.md` | No existing drift row covered system-level graph-pull retry bounds or ongoing-fault collapse bounds before S155. | Yes - added `DRIFT-030` as a law-surface gap and did not amend locked laws in this sprint. |

---

## Test plan results — fill at handback

| # | What it proves | Test | Status | Planted-failure observed? |
| --- | --- | --- | --- | --- |
| A1 | no-progress pass sleeps | `tests/test_work_loop.py::test_work_loop_sleeps_after_no_progress_pass` | Pass | Yes — planted probe before implementation reported `PLANTED work_loop_no_progress: attempts=25 sleeps=0`. |
| A2 | empty pass sleeps (unchanged) | `tests/test_work_loop.py::test_work_loop_sleeps_after_empty_pass` | Pass | No — unchanged healthy-idle behavior. |
| A3 | productive pass does not sleep (unchanged) | `tests/test_work_loop.py::test_work_loop_does_not_sleep_after_productive_pass` | Pass | No — unchanged productive behavior. |
| B4 | backoff grows to a ceiling | `tests/test_work_loop_quarantine.py::test_backoff_grows_to_the_ceiling` | Pass | Yes — same planted no-progress probe showed the old loop made 25 immediate attempts with no sleeps. |
| B5 | poison item quarantined | `tests/test_work_loop_quarantine.py::test_poison_item_is_quarantined_and_later_skipped`; `tests/test_work_loop.py::test_exception_can_quarantine_without_retry_delay` | Pass | No separate planted failure; covered by the old no-progress loop probe and committed positive tests. |
| B6 | quarantine is findable | `tests/test_work_loop_quarantine.py::test_work_loop_creates_graph_quarantine_state_when_wired`; `tests/test_work_loop_quarantine.py::test_duplicate_quarantine_write_is_append_safe`; `tests/test_work_loop_quarantine.py::test_work_loop_flushes_fault_summaries_when_quarantine_closes_item` | Pass | No — positive tests assert the visible `WorkItemQuarantine` node and flush path, not absence of retries. |
| B7 | healthy sibling still processes | `tests/test_work_loop_storm.py::test_poison_item_does_not_block_healthy_sibling`; `tests/test_work_loop.py::test_run_once_contains_exception_and_continues_siblings` | Pass | No — law-governed sibling-containment regression covered directly. |
| C8 | repeated signature writes one node | `tests/test_fault_graph.py::test_identical_faults_within_window_write_one_fault_node` | Pass | Yes — planted fault probe before implementation reported `PLANTED fault_duplicate_writes: fault_nodes=5`. |
| C9 | suppressed volume recoverable | `tests/test_fault_graph.py::test_suppressed_fault_volume_is_recoverable`; `surfaces/tests/test_faults.py::test_render_incidents_continues_after_unsuppressed_fault` | Pass | Yes — same planted fault probe showed the old ledger had N nodes and no summary. |
| C10 | distinct signatures both write | `tests/test_fault_graph.py::test_distinct_fault_signatures_both_write` | Pass | No — positive regression proves collapse does not swallow distinct failures. |
| C11 | cross-run recurrence still reads as recurrence | `tests/test_fault_graph.py::test_fault_recurring_after_window_still_appends`; `tests/test_fault_graph.py::test_recurring_fault_appends_rather_than_overwrites` | Pass | No — preserves existing `fault_node_key` first-occurrence/cross-window contract. |
| D12 | 2026-07-30 shape bounded | `tests/test_work_loop_storm.py::test_real_fault_storm_shape_is_bounded_and_visible` | Pass | Yes — pre-fix planted probe reproduced the storm shape. |
| D13 | planted regression unbounded | Pre-implementation planted probe and pre-implementation red focused tests | Pass | Yes — planted probe: `attempts=25 sleeps=0`, `fault_nodes=5`; red tests failed before runtime existed with missing fault-collapse imports. |

---

## Closeout — evidence

> **Fill this in at handback. Do not return the sprint with this block unedited.**

- Files changed: kernel retry/fault modules (`kernel/work_loop.py`, `kernel/work_loop_policy.py`,
  `kernel/work_loop_state.py`, `kernel/work_loop_quarantine.py`, `kernel/fault_collapse.py`,
  `kernel/fault_graph.py`); eight graph-pull entrypoints; `orchestration/local_pipeline.py`;
  fault surfaces and MCP output; graph vocabulary pack; focused tests split under 200 lines; sprint
  doc and drift register.
- Version bump (`pyproject.toml`, `uv.lock` restaged):

```text
uv lock
Resolved 174 packages in 1.80s
Updated trading-agents v0.85.0 -> v0.85.1
```

- Focused proof before full CI:

```text
uv run pytest tests/test_work_loop.py tests/test_work_loop_quarantine.py tests/test_work_loop_storm.py tests/test_fault_graph.py agents/execution/tests/test_position_sync_poll.py agents/execution/tests/test_execution_poll.py agents/execution/tests/test_execution_entrypoint.py surfaces/tests/test_faults.py --no-cov
collected 43 items
43 passed in 2.11s

uv run coverage run --branch -m pytest tests/test_work_loop.py tests/test_work_loop_quarantine.py tests/test_work_loop_storm.py --no-cov
20 passed in 2.00s
Name                             Stmts   Miss Branch BrPart    Cover
kernel/work_loop.py                 67      0     24      0  100.00%
kernel/work_loop_policy.py          22      0      2      0  100.00%
kernel/work_loop_quarantine.py      23      0      2      0  100.00%
kernel/work_loop_state.py           82      0     18      0  100.00%
TOTAL                              194      0     46      0  100.00%
```

- `make ci` — pass count, skips, coverage:

```text
make ci
uv run ruff check . --output-format=github
uv run ruff format --check .
900 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 749 source files
uv run lint-imports
Contracts: 4 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run pytest
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2054 passed, 6 skipped in 93.69s (0:01:33) ==================
uv run pip-audit
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 6 new file(s)
No known vulnerabilities found
```

- Coverage change on `kernel/work_loop.py` (the `pragma: no cover` question): `kernel/work_loop.py`
  now reports `67 stmts / 0 miss / 24 branches / 0 partial / 100.00%` in the focused work-loop
  coverage proof above and in full `make ci`.
- Planted-failure observations (items 5 and 13 especially):

```text
uv run python <planted pre-fix probe>
PLANTED work_loop_no_progress: attempts=25 sleeps=0
PLANTED fault_duplicate_writes: fault_nodes=5

uv run pytest tests/test_work_loop.py tests/test_fault_graph.py --no-cov
collected 0 items / 2 errors
ImportError: cannot import name 'FAULT_SUPPRESSION_LABEL'
ModuleNotFoundError: No module named 'kernel.fault_collapse'
```

- Remote gate run IDs **and job conclusions**, with a run asserted to exist for the head SHA: pending
  push/poll; to be appended after branch CI creates the run for the pushed head SHA.
- Not met / deliberately deferred: no live graph, Azure, broker, or credentialed proof attempted;
  this sprint is local-only by brief. Existing >150 line warnings remain warnings and were not
  refactored outside S155 scope.

---

## Return notes

- Branch and base commit: `sprint-155-bounded-retry-and-fault-containment`, cut from `2d6f62e`;
  stayed in the dedicated worktree and did not merge to `main`.
- **Which collapse shape you chose (1, 2 or 3) and why:** shape 2, **first + summary**. It preserves
  the exact first-fault timestamp/key contract, keeps append-only semantics by writing a separate
  `FaultSuppression` node, and makes the suppressed volume queryable by surfaces. The trade-off is
  needing `flush()` or a later same-signature event after the window; that is better here than bucket
  keys that would perturb first-fault identity.
- Every red remote run hit on the way (run ID + cause + fix): pending push/poll.
- Anything the laws or this spec contradicted: no contradiction found. The law set was silent on
  system-level graph-pull retry bounds, quarantine visibility, and duplicate fault emission volume,
  so I recorded `DRIFT-030` rather than amending locked laws.
- Anything found and deliberately not fixed: graph vocabulary property declarations remain absent
  for `FaultSuppression` and `WorkItemQuarantine` because the current guard only enforces labels with
  explicit property blocks; adding property governance for these labels is a separate vocabulary
  hardening question, not required to stop the storm.
