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

**Result:** _fill at handback_

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

**Result:** _fill at handback_

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

**Result:** _fill at handback_

### 4 · The infinite loop gets a test

`work_loop`'s `# pragma: no cover` is why the spinning half has never been exercised. Make the loop
testable — inject the clock/sleep, or bound the iterations under test — and cover the two behaviours
that matter: **a no-progress pass sleeps**, and **a poison item does not spin**.

Removing a `pragma: no cover` from the one function whose failure mode caused an outage is a large
part of this sprint's value. If you conclude it genuinely cannot be covered, that is a finding to
report, not a line to leave as-is.

**Result:** _fill at handback_

### 5 · Prove the containment on the real shape (DL-70)

Reconstruct the 2026-07-30 shape in a test: a work item whose processing always raises, against a
graph that never advances it. Assert **bounded** attempts and **bounded** fault writes over a
simulated window — not "no exception".

Then plant the regression: revert the backoff and watch the same test fail with an unbounded count.
**Both observations go in the closeout.** A containment you have not seen fail to contain is not
proven.

**Result:** _fill at handback_

### 6 · Record the drift you find (do not fix it here)

If the kernel's laws do not declare loop-termination or fault-emission bounds, open a
`docs/laws/drift-register.md` row. Apply the **S152 standing convention** — *decided → amend;
appeared → it stays a drift row and becomes a code fix* — and do not amend any `laws.md` in this
sprint.

**Result:** _fill at handback_

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
| `kernel/work_loop.py` | `docs/laws/conventions.md` | | |
| `kernel/fault_graph.py` / `kernel/errors.py` | | | |
| Affected agents' `laws.md` (`FAIL` / `OBS` sections) | | | |
| `docs/laws/drift-register.md` | | | |

---

## Test plan results — fill at handback

| # | What it proves | Test | Status | Planted-failure observed? |
| --- | --- | --- | --- | --- |
| A1 | no-progress pass sleeps | | | |
| A2 | empty pass sleeps (unchanged) | | | |
| A3 | productive pass does not sleep (unchanged) | | | |
| B4 | backoff grows to a ceiling | | | |
| B5 | poison item quarantined | | | |
| B6 | quarantine is findable | | | |
| B7 | healthy sibling still processes | | | |
| C8 | repeated signature writes one node | | | |
| C9 | suppressed volume recoverable | | | |
| C10 | distinct signatures both write | | | |
| C11 | cross-run recurrence still reads as recurrence | | | |
| D12 | 2026-07-30 shape bounded | | | |
| D13 | planted regression unbounded | | | |

---

## Closeout — evidence

> **Fill this in at handback. Do not return the sprint with this block unedited.**

- Files changed:
- Version bump (`pyproject.toml`, `uv.lock` restaged):
- `make ci` — pass count, skips, coverage:
- Coverage change on `kernel/work_loop.py` (the `pragma: no cover` question):
- Planted-failure observations (items 5 and 13 especially):
- Remote gate run IDs **and job conclusions**, with a run asserted to exist for the head SHA:
- Not met / deliberately deferred:

---

## Return notes

- Branch and base commit:
- **Which collapse shape you chose (1, 2 or 3) and why:**
- Every red remote run hit on the way (run ID + cause + fix):
- Anything the laws or this spec contradicted:
- Anything found and deliberately not fixed:
