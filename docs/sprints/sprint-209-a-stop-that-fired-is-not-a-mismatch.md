<!-- Agent: planning | Role: sprint handover -->
# Sprint 209 — a stop that fired is not a mismatch

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-209-stop-fired-not-mismatch`
**Status:** BUILT
**Version:** *next available PATCH at merge* (main is `0.98.05`)
**Effort:** S — but **not** the "small" the work queue promised: the code is ~4 lines, the **law cycle is the sprint**.
**Decisions:** DL-170 (take the next free number, re-check at merge) · DRIFT-064 · closes work-queue item **42**, retires item **32**'s residue

> **Why this bump kind.** PATCH. No new capability: the sweep already decides exemption correctly
> (`drop_sweep.py:139` already returns on **identity**). Only the *warning* beside that decision asks
> the wrong question. Nothing gains a dimension; a false signal stops being emitted.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/execution/laws/laws.md` | The execution agent's **locked constitution** (LOCKED **v1.5**) | **Read-only during a build** — except the amendment this sprint explicitly owes, below |
| `agents/execution/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | `EXEC-OBS-05` is 🟩 — and it is 🟩 for the *current* wording, which this sprint changes |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`EXEC-OBS`**, **`EXEC-OUT`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read `agents/execution/laws/test-plan.md` alongside its `laws.md`.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It is already answered **Yes** — see why.
5. **Write the Law reading record** **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered **YES**, and this is the whole point of the sprint

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**`contracts/` — NO. Do not touch it.** Every predicate needed already exists and is exported.

**A guarantee changes — YES, and it is written down.** `agents/execution/laws/laws.md:271`,
`EXEC-OBS-05`, closes with:

> *"…and the stale-order sweep asks the broker **the same liveness question** it asks of the graph."*

and its test-plan row (`agents/execution/laws/test-plan.md:103`) says *"and the sweep compares broker
and graph liveness."*

🚨 **The defect this sprint removes is enshrined in a LOCKED clause.** That is why the work-queue row
calling item 42 *"small, and low urgency"* is **wrong about the size** — it measured the diff, not the
cycle. Changing the code without the amendment would leave `EXEC-OBS-05` describing behaviour that no
longer exists: silent law drift, in a LOCKED book, which is precisely the debt this sprint must not create.

**Therefore this sprint owes, in the same unit of work:** the `EXEC-OBS-05` amendment, a `laws.md`
version bump **v1.5 → v1.6** with a Changelog line, the `test-plan.md` row rewritten and its cited
tests updated, the rollup recomputed in **both** [`docs/laws/ledger.md`](../laws/ledger.md) (line 44)
**and** [`docs/laws/INDEX.md`](../laws/INDEX.md) (line 45), and a `DRIFT-064` row recording that the
clause described a defect for the 16 days it stood.

🪤 **The rollup is derived, not declared.** `make ci` recomputes it. `EXEC-OBS-05` is already 🟩 and
stays 🟩 — the expected movement is **35 / 61 → 35 / 61, unchanged**. If your diff moves it, you added
or lost a clause you did not intend to. Let the gate tell you the number; do not hand-edit it to match.

⚠️ **Amend only the final limb.** `EXEC-OBS-05`'s first sentence — *"Liveness of an execution broker
fact is asked in exactly one place"* — is **correct, load-bearing, and the reason item 32 closed.**
This sprint strengthens it. If your amendment weakens or deletes that sentence, you have
misunderstood the sprint: stop and report.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/execution/drop_sweep.py` (`_is_stop_order`, **:132–139**) | `agents/execution/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `EXEC-OBS-05` governs exactly this function; `EXEC-OUT-07` governs what the sweep may cancel |
| `agents/execution/laws/laws.md` | itself, whole file | LOCKED v1.5 → the amendment above is the *only* permitted edit |
| `agents/execution/tests/test_drop_sweep_liveness.py` | same | its two tests cite `EXEC-OBS-05` in their docstrings |

⚠️ **The one invariant this sprint must not break: the sweep must never cancel a live stop.**
`drop_sweep.py:139` returns `is_broker_stop_order(order) or graph_stop` — a truthy return means
*"skip this order, it is a stop"*. **That return is already correct and must keep exempting at least
as much as it does today.** If your change makes `_is_stop_order` return `False` for any order it
currently returns `True` for, you have created a path that cancels live protection. Stop and report.

---

## Goal

The head-of-run stale-order sweep raises `BrokerStopIdentityMismatch` when broker and graph disagree
about **whether an order is a stop** — an identity question, stable within a run — and never merely
because the graph's liveness view has not been refreshed yet. A stop that fired since the previous
run produces **zero** faults. A broker stop with no graph counterpart at all still produces one.

## Why (context)

The sweep runs at `agents/execution/poll.py:124`. The refresh that updates the graph's liveness view
runs at `poll.py:132` → `reconciliation.py:44` → `reconciliation_store.py:32`
(`refresh_pending_fills`) — **11 to 19 seconds later, in the same run, from the same `broker.fills()`
read.** So `_is_stop_order` compares a fresh broker liveness view against a graph liveness view that
the *next statement* is about to update. For every stop that fired since the previous run, the two
must disagree, and a permanent `Fault` row is written recording that the refresh had not run yet.

It costs one permanent `Fault` per fired stop, forever, in the table the operator reads to decide
whether the fleet is healthy. It has already cost more than that: this row was **filed wrong twice**
(the first filing proposed deleting live correct data; [DL-146](../design-log.md) called it a defect
and [DL-147](../design-log.md) corrected that to transient). A signal that cries wolf is exactly what
the operator's etalon bar fails on.

### Measured, 2026-09-16 — read these before designing

All measurements against the live Neon spine from the main checkout (`.env` present), `main` @ `4477a09`.

| Claim | Value | How it was measured |
| --- | --- | --- |
| `BrokerStopIdentityMismatch` faults, all time | **330** | *[measured 2026-09-16]* `list_nodes("Fault")` filtered on `"stop identity mismatch" in message` |
| …in direction `broker_stop=True graph_stop=False` (item 20's original) | **321**, 17 distinct stop keys | *[measured 2026-09-16]* same query, split on the message text |
| …last occurrence of that direction | **2026-08-31** | *[measured 2026-09-16]* S190 merged `193e71b` that day and the direction stops dead — **S190 worked** |
| …in direction `broker_stop=False graph_stop=True` (item 42's residue) | **9**, on 6 dates | *[measured 2026-09-16]* 2026-09-01 (2), -09-08, -09-09, -09-10, -09-14 (3), -09-15 (1) |
| distinct stop keys in that direction | **9** | *[measured 2026-09-16]* one fault per key — **it never recurs for the same stop** |
| every such fault self-corrects in the same run | **9 of 9** | *[measured 2026-09-16]* per fault, the next `BrokerOrderStatus` for that ticker is terminal (`filled` ×8, `rejected` ×1) |
| gap from fault to that terminal write | **11.4 s – 19.4 s**, max 19.4 s | *[measured 2026-09-16]* AMD 16.2, USB 11.6, MDLZ 16.8, DOW 12.9, ABT 11.4, AVGO 19.4, BAC 12.4, KHC 12.2, AMZN 17.8 — reproduces DL-147's 16 s / 11 s independently |
| the 2026-09-15 instance | AMZN, fault `22:32:09.365`, terminal write `22:32:27.149` | *[measured 2026-09-16]* AMZN's protective stop filled at **14:21:16** that afternoon; `sched-2026-09-15` was the next run |
| `Fault` nodes key their time on | **`occurred_at`**, not `created_at` | *[measured 2026-09-16]* `created_at` is absent; sorting by it silently returns unordered rows 🪤 |
| a persistent (non-transient) liveness divergence could hide where `refresh_pending_fills` skips | **impossible for stops** | *[measured 2026-09-16 by code reading]* it skips `Fill.status != "pending"`, but a stop's `Fill.status` is **always** `"pending"` — that is every stop's normal state (the [DL-73](../design-log.md) trap, re-confirmed: 47 of 47 siblings). The real prop is `broker_status`. So the refresh processes **every** stop, and there is no case the sweep's liveness warning uniquely catches |
| `drop_sweep.py` current size | **168 lines** — warning zone | *[measured 2026-09-16]* `wc -l`; hard block at 200, warn at 150 |

---

## Scope — and what is deliberately NOT here

1. **🎯 Plant the failing test first.** Reproduce the transient state in `InMemoryGraphStore`: a
   `BrokerStopOrder` node whose sibling `Fill` still carries `broker_status=None` (not yet refreshed),
   against a broker order for the same key whose status is terminal (`filled`). That is AMZN on
   2026-09-15 exactly. Assert **no fault is raised**. Watch it go **red** and paste the output.
2. **Change `_is_stop_order` (`drop_sweep.py:132–139`) to compare identity to identity.** Broker side
   is already available: `is_broker_stop_order(order)` (`contracts/broker_lifecycle.py:103`). Graph
   side needs the **unfiltered** accessor `broker_stop_orders(graph)`
   (`contracts/broker_stops.py:71`) in place of `active_broker_stop_orders`
   (`:62`) — **it already exists and is already exported; do not add one.**
   The `return` on line 139 stays as it is.
3. **The law cycle**, in full, as itemised in the law-cycle question above.

### Out of scope (do NOT build this sprint)

- **No `contracts/` edit.** Both predicates exist. If you find yourself adding one, re-read step 2.
- **No reordering of `poll.py`.** Moving the refresh before the sweep is a different sprint with a
  real blast radius — see the road not taken.
- **No new post-refresh liveness check.** See the road not taken; this is the debt trap.
- **No touching `_tracked_as_stop`'s matching rule** (key **or** `broker_order_id`). Only the
  accessor it iterates changes.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

- **Reorder the run so the refresh precedes the sweep.** Rejected: it changes what the sweep *sees*,
  not just what it *says*. After a refresh, orders the sweep would have cancelled may present
  differently, and the sweep's cancel path touches live broker state. The row's own first filing was
  wrong in exactly this direction and "acting on it would have deleted live, correct data"
  ([DL-147](../design-log.md)). A warning bug does not justify moving a cancel.
- **Suppress or de-duplicate the fault (lower severity, dedupe by key).** Rejected: it hides the
  symptom and leaves the wrong comparison in place, so the clause stays wrong too. The fault is not
  too loud; it is not a fault.
- **Add a post-refresh liveness check so a "real" divergence is still reported.** Rejected on two
  grounds, and this is the residue trap. (i) **It would be a fifth way to ask the liveness question** —
  the thing `EXEC-OBS-05`'s first sentence forbids and item 32 was closed to stop. (ii) It would have
  **nothing to report**: measured above, the refresh processes every stop from the same `broker.fills()`
  read, so after it runs there is no divergence left to find. Genuine broker↔graph divergence is
  already owned by `reconcile_run_start` (DL-44), which raised the `extra_graph_position AMZN` Flag on
  this very run.
- **Close item 42 as "not a defect" and delete the row.** Rejected: the fault rows are permanent and
  accumulate one per fired stop forever. Transient in effect is not harmless in evidence.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Identity is the sweep's question; liveness is reconciliation's.** The fork is which of the two
   comparisons is the *sweep's* business. Everything above hangs on it, including the clause wording.
2. **Whether liveness disagreement is observed anywhere at all** — this sprint says **no**, on the
   measured ground that after the refresh there is nothing to observe. Write down that measurement,
   because the next person to read a quiet log will want to re-add the check.

🪤 **Take the next free DL number** — `DL-170` at the time of writing — **then re-check it at merge.**
The log has historic duplicates and entries are prepended at the top *and* appended at the bottom. A
branch cut before another DL lands will collide even when the number was free at branch time.

---

## Blast radius — measured 2026-09-16

| What | Detail |
| --- | --- |
| Files changed | `agents/execution/drop_sweep.py` (**168**, must stay < 200 and should not grow), `agents/execution/tests/test_drop_sweep_liveness.py` (**78**), `agents/execution/laws/laws.md`, `agents/execution/laws/test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`, `docs/design-log.md`, `docs/work-queue.md`, `pyproject.toml` |
| Agents affected | `execution` only — confirm no agent imports another |
| Contract change? | **No.** `contracts/broker_lifecycle.py` (**162**) and `contracts/broker_stops.py` (**105**) are read-only here. `git diff --stat contracts/` **must be empty** |
| Graph vocabulary change? | **No** new label or property — fewer `Fault` rows, same shape |
| New env keys / tunables | **None** |
| Deploy implication | **Image-only retag.** No vocabulary, no env key, no tunable |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing test first** and watch it fail. Paste the red output.
4. **Implement** the `_is_stop_order` change.
5. **Law cycle** — clause amendment, `laws.md` v1.6 + Changelog, test-plan row, docstring citations,
   both rollups, `DRIFT-064`.
6. **Prove the guards can fail (DL-70)** — break the implementation, watch each guard go red, restore.
7. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 a stop that fired since the last run raises no mismatch | `BrokerStopOrder` node + sibling `Fill` with `broker_status=None`; broker order same key, `order_type="stop"`, `status="filled"` | `sink.faults == []`, and the order is still **exempted** (`dropped == 0`, `broker.cancelled == []`) — the AMZN 2026-09-15 state |
| A2 | 🪤 a broker stop with no graph counterpart still raises one | the existing `test_live_stop_mismatch_fault_carries_context` fixture (`stop:missing:AMD`, empty graph) | the fault still fires with `broker_stop=True graph_stop=False` context — **this test must pass unchanged** |
| A3 | 🪤 a dead broker stop matching a dead graph stop still raises none | the existing `test_sweep_raises_no_mismatch_for_dead_stop_order` fixture | still passes unchanged — identity-to-identity must not re-introduce a fault here |
| A4 | a graph stop with no broker counterpart raises one | `BrokerStopOrder` in graph, broker order that is **not** a stop (`order_type="limit"`, non-`stop:` key) sharing a `broker_order_id` | the genuine mirror divergence is still reported — the direction is not silenced wholesale |

🪤 **A2 and A3 already pass today, and will still pass after the change — I checked both by hand.**
That is a hazard, not a comfort: **they cannot tell you whether the fix worked.** Only A1 can, and
only if you watch it fail first. A handback whose evidence is "the existing tests still pass" is
returned.

---

## Success factors

- [ ] A test reproducing the transient state (fired stop, unrefreshed graph) asserts **no fault**,
      was **watched red before the fix**, and is green after. The red output is pasted.
- [ ] `_is_stop_order` compares `is_broker_stop_order(order)` against a graph **identity** predicate;
      `active_broker_stop_orders` no longer appears in `drop_sweep.py`'s mismatch path.
- [ ] The `return` at `drop_sweep.py:139` is unchanged, and no order exempted today is unexempted.
- [ ] `git diff --stat contracts/` is **empty**.
- [ ] `EXEC-OBS-05` amended, `laws.md` **v1.5 → v1.6** with a Changelog line, first sentence intact.
- [ ] `test-plan.md` row rewritten to the new wording, cited tests updated, clause IDs in docstrings.
- [ ] Rollup recomputed by the gate in **both** `ledger.md` and `INDEX.md` — expected **unchanged at
      35 / 61**; if it moved, explain why.
- [ ] `DRIFT-064` filed, recording that the clause described a defect from 2026-08-31 to merge.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] `drop_sweep.py` still **< 200** lines (it is 168; report the new number).
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **`Fill.status` is not the discriminator.** Every stop's sibling `Fill` carries `status="pending"` —
that is its normal state, 47 of 47. The real prop is `broker_status`. Using `status` selects the whole
population and will make you think you have found something. This is the [DL-73](../design-log.md)
trap and it has already cost this project one retracted red-severity defect.

🪤 **`Fault` nodes have no `created_at`.** They key on `occurred_at`. Sorting or filtering by
`created_at` returns rows in arbitrary order with no error, which is how a previous measurement of
this very row went wrong.

🪤 **The existing tests passing is not evidence.** See the note under the test plan.

🪤 **"Transient" is not "harmless".** The `Fault` row is permanent even though the condition is not.
Do not let the self-correction argument talk you out of the fix — that argument is what left the row
open for two weeks.

🪤 **`make ci | tail` reports `tail`'s exit code.** Redirect to a file and read the file.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `drop_sweep.py` **168**, `drop_sweep_records.py` **172**, `poll.py` **136**,
  `contracts/broker_lifecycle.py` **162**, `contracts/broker_stops.py` **105**,
  `test_drop_sweep_liveness.py` **78**. 🚨 **Two of these are already in the warning zone** — the fix
  must not grow `drop_sweep.py`. It should shrink or hold.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. None expected here.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**, redirected to a file.
- Version bump: **PATCH**, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**. 🟩 **Every test in this sprint is
  in-memory and needs none**; the live measurements above were taken in the main checkout and are
  quoted here so you do not need to reproduce them. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA
   from the working directory and ignores a `SHA=` argument. **Check the printed SHA against
   `git rev-parse HEAD`.**
2. Merge to `main` locally and push. 🪤 A `git merge` from the branch's own worktree says
   *"Already up to date"* and merges nothing.
3. **Post-merge CodeQL.** `codeql.yml` runs **only on `main`**.
4. **Deploy:** image-only retag.
5. **The live check (the only one that can close item 42).** The fix is unfalsifiable until a stop
   fires. After the next scheduled run in which a protective stop filled during that session, confirm
   **zero** `BrokerStopIdentityMismatch` faults with `occurred_at` on that date, and record it in
   [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md). 🪤 **A run where no stop
   fired proves nothing** — 2026-09-02 raised zero faults for exactly that reason and was briefly
   mistaken for proof. Name the stop that fired, or say the check is still owed.

---

## Handover — paste this to Codex

```text
Branch `sprint-209-stop-fired-not-mismatch` off main. Never commit to main.

THE CLAIM: a stop that fired since the previous run is not an identity mismatch.

MUST RULE - before you open an editor: read agents/execution/laws/laws.md (whole file, it is
LOCKED v1.5), agents/execution/laws/test-plan.md, docs/laws/conventions.md and
docs/laws/drift-register.md. Then fill the "Law reading record" section of
docs/sprints/sprint-209-a-stop-that-fired-is-not-a-mismatch.md BEFORE your first code change.
If a law contradicts this spec, STOP and report - the law is more likely right than the spec.

THE DEFECT. agents/execution/drop_sweep.py:132-139, _is_stop_order:
    broker_stop = is_live_broker_stop_order(order)   # broker LIVENESS
    graph_stop  = _tracked_as_stop(graph, order)     # graph LIVENESS (active_broker_stop_orders)
    if broker_stop != graph_stop: record_stop_mismatch(...)
    return is_broker_stop_order(order) or graph_stop  # IDENTITY - already correct
The sweep runs at poll.py:124. The refresh that updates the graph's liveness view runs at
poll.py:132 -> reconciliation.py:44 -> reconciliation_store.py:32, 11-19 s later IN THE SAME RUN
and from the SAME broker.fills() read. So for every stop that fired since the last run the two
views must disagree, and a permanent Fault is written saying the refresh had not run yet.
Measured on the live spine 2026-09-16: 9 such faults, 9 distinct keys, one per key, every one
resolved to a terminal broker status 11.4-19.4 s later in the same run.

THE FIX (~4 lines). Compare IDENTITY to IDENTITY in the warning:
  - broker side: is_broker_stop_order(order)      contracts/broker_lifecycle.py:103
  - graph side:  broker_stop_orders(graph)        contracts/broker_stops.py:71  (UNFILTERED)
    in place of active_broker_stop_orders         contracts/broker_stops.py:62  (live-filtered)
Keep _tracked_as_stop's matching rule (key OR broker_order_id); only the accessor changes.
DO NOT change the return on line 139. DO NOT edit anything in contracts/ - both predicates
already exist and are exported. `git diff --stat contracts/` must come back empty.

ORDER OF WORK - failing test FIRST:
1. Write the test that reproduces the transient state in InMemoryGraphStore: a BrokerStopOrder
   node whose sibling Fill still has broker_status=None, against a broker order for the same key
   with order_type="stop" and status="filled". Assert sink.faults == [], dropped == 0,
   broker.cancelled == []. WATCH IT FAIL. PASTE THE RED OUTPUT. This is AMZN on 2026-09-15.
2. Then implement.

THE LAW CYCLE IS OWED AND IS THE BULK OF THIS SPRINT. EXEC-OBS-05 (agents/execution/laws/laws.md:271)
literally ends "...and the stale-order sweep asks the broker the same liveness question it asks of
the graph", and its test-plan row (test-plan.md:103) says "the sweep compares broker and graph
liveness". That wording describes the defect. You must:
  - amend ONLY that final limb. The first sentence ("Liveness of an execution broker fact is asked
    in exactly one place") is correct and load-bearing - if your edit weakens it, you have
    misread the sprint: stop and report.
  - bump agents/execution/laws/laws.md v1.5 -> v1.6 with a Changelog line
  - rewrite the test-plan.md:103 row and its cited test list
  - cite EXEC-OBS-05 in the new test's docstring
  - let `make ci` recompute the rollup in BOTH docs/laws/ledger.md (line 44) and
    docs/laws/INDEX.md (line 45). Expected UNCHANGED at 35 / 61 - EXEC-OBS-05 is already green and
    stays green. If it moves, you changed the clause count; say why. Do not hand-edit it to match.
  - file DRIFT-064 recording that the clause described a defect from 2026-08-31 until this merge.

TRAPS, named because a trap you do not write down gets hit:
  - Fill.status is ALWAYS "pending" for a stop - 47 of 47. It is not a discriminator. The real
    prop is broker_status. (DL-73; this already cost one retracted red-severity defect.)
  - Fault nodes have NO created_at. They key on occurred_at. Sorting by created_at silently
    returns arbitrary order - a previous measurement of this row went wrong that way.
  - The two EXISTING tests in agents/execution/tests/test_drop_sweep_liveness.py pass today AND
    will still pass after the fix (I checked both by hand). They cannot tell you the fix worked.
    Only the new red-first test can. "The existing tests still pass" is a returned handback.
  - "Transient" is not "harmless": the Fault row is permanent, one per fired stop, forever.
  - make ci | tail reports tail's exit code. Redirect to a FILE and read the file.

ALSO ADD these tests: a graph stop whose broker counterpart is NOT a stop (order_type="limit",
non-"stop:" key, shared broker_order_id) must STILL raise a mismatch - the direction is not being
silenced wholesale, only the liveness-lag case.

SIZE: drop_sweep.py is 168 lines, hard block at 200, warn at 150. Do not grow it.
Everything here is in-memory; a worktree has no .env and you do not need one.
Version: next available PATCH (main is 0.98.05). Stage uv.lock with it.
Fill the Handback contract at the bottom of the spec: Law reading record, Test plan results,
Closeout evidence with REAL pasted output (red run first, then green), Return notes,
Status: BUILT. A placeholder left unfilled is returned, not repaired.
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
| `agents/execution/drop_sweep.py` (`_is_stop_order`, `_tracked_as_stop`) | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `EXEC-OBS-05`, `EXEC-OUT-07`, `EXEC-OBS-03` | Yes. The sweep's exemption return is already identity-based and must keep exempting all current stops; only the mismatch warning should stop asking the graph liveness question. |
| `agents/execution/tests/test_drop_sweep_liveness.py` | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md` | `EXEC-OBS-05` | Yes. The new guard must cite `EXEC-OBS-05`, fail before the implementation, and prove the liveness-lag case rather than relying on the existing tests. |
| `agents/execution/laws/laws.md` / `agents/execution/laws/test-plan.md` | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md` | `EXEC-OBS-05` | Yes. Amend only the final sweep limb; keep the first sentence about one liveness predicate intact and bump the law book to v1.6. |
| `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md` | `docs/laws/INDEX.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | conventions §§3, 4, 7, 7a, 9 | Yes. Rollups should stay 35 / 61 because `EXEC-OBS-05` remains green; file `DRIFT-064` for the stale clause wording instead of silently editing it. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**

No `contracts/` change. Yes, the execution guarantee changes: `EXEC-OBS-05` no longer says the
stale-order sweep compares broker and graph liveness; the sweep reports identity disagreement while
liveness remains owned by the central broker lifecycle predicates and reconciliation.

**Contradictions found between a law and this spec:**

None beyond the named `EXEC-OBS-05` final limb that this sprint explicitly amends. The first
sentence of `EXEC-OBS-05` is consistent with the spec and stays load-bearing.

**Laws found silent where a decision was needed:**

None. The required decision is an amendment to existing `EXEC-OBS-05`, not a new-law gap.

**Clauses that were ⬜ and are now proven:**

None expected. `EXEC-OBS-05` is already 🟩 and should remain 🟩 with revised wording.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_fired_stop_with_unrefreshed_graph_status_raises_no_mismatch` | `agents/execution/tests/test_drop_sweep_identity.py` | 🟩 red first on old implementation, green after | `EXEC-OBS-05` |
| A2 | `test_live_stop_mismatch_fault_carries_context` | `agents/execution/tests/test_drop_sweep_liveness.py` | 🟩 unchanged, green | `EXEC-OBS-05` |
| A3 | `test_sweep_raises_no_mismatch_for_dead_stop_order` | `agents/execution/tests/test_drop_sweep_liveness.py` | 🟩 unchanged, green | `EXEC-OUT-07`, `EXEC-OBS-05` |
| A4 | `test_graph_stop_identity_mismatch_still_faults` | `agents/execution/tests/test_drop_sweep_identity.py` | 🟩 red on intentional broken graph identity check, green after restore | `EXEC-OBS-05` |

**Tests added beyond the plan:**

- `tests/test_broker_lifecycle_invariants.py::test_broker_order_lifecycle_status_drives_live_stop_orders` — direct coverage for the shared broker-order lifecycle predicate after `drop_sweep.py` stopped calling `is_live_broker_stop_order`; cites `EXEC-OBS-05`.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\trading-agents`, branch `sprint-209-stop-fired-not-mismatch`; `.env` present but not read for this in-memory implementation. Live-spine measurements were not reproduced.

**Result:** `_is_stop_order` now records `BrokerStopIdentityMismatch` only for stop identity disagreement: broker side uses `is_broker_stop_order(order)`, graph side uses unfiltered `broker_stop_orders(graph)`, and the existing exemption return still skips every broker or graph stop identity. No `contracts/` files changed.

**Files changed:** `agents/execution/drop_sweep.py`; `agents/execution/tests/test_drop_sweep_identity.py`; `tests/test_broker_lifecycle_invariants.py`; `agents/execution/tests/test_drop_sweep_liveness.py` (unchanged tests kept); execution laws/test-plan; law rollups/drift register; `docs/design-log.md`; sprint handback; `pyproject.toml`; `uv.lock`.

**Design decisions:** recorded as `DL-170`.

**Proof — the red run first:**

```text
uv run pytest agents/execution/tests/test_drop_sweep_liveness.py::test_fired_stop_with_unrefreshed_graph_status_raises_no_mismatch --no-cov
FAILED agents/execution/tests/test_drop_sweep_liveness.py::test_fired_stop_with_unrefreshed_graph_status_raises_no_mismatch
E   AssertionError: assert [AgentFault(... 'broker_status': 'filled', 'broker_stop': False, 'graph_stop': True})] == []
============================== 1 failed in 1.47s ==============================

temporary guard break: _tracked_as_stop returned False
uv run pytest agents/execution/tests/test_drop_sweep_liveness.py::test_graph_stop_identity_mismatch_still_faults --no-cov
FAILED agents/execution/tests/test_drop_sweep_liveness.py::test_graph_stop_identity_mismatch_still_faults
E   AssertionError: assert ['broker:old-run:AMZN:buy'] == []
============================== 1 failed in 1.27s ==============================
```

**Proof — the green run:**

```text
uv run pytest tests/test_broker_lifecycle_invariants.py agents/execution/tests/test_drop_sweep_identity.py agents/execution/tests/test_drop_sweep_liveness.py --no-cov
============================== 6 passed in 1.97s ==============================

make ci > C:\Users\yury_\AppData\Local\Temp\trading-agents-s209-make-ci-2.txt 2>&1
exit=0
TOTAL                                                     16525      0   3518      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2768 passed, 4 skipped in 222.88s (0:03:42) =================
No known vulnerabilities found
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 1 new file(s)
```

**Guards planted:** A1 was planted against the old implementation and failed on a false `BrokerStopIdentityMismatch` for a fired stop awaiting graph refresh. A4 was proven by intentionally breaking graph stop identity matching; the broker attempted to cancel `broker:old-run:AMZN:buy`, proving the guard protects the mirror mismatch path. The lifecycle predicate test was added after the first full `make ci` found coverage at 99.98%; the second full gate restored 100.00%.

**Module line counts:** `agents/execution/drop_sweep.py` 167; `agents/execution/tests/test_drop_sweep_liveness.py` 78; `agents/execution/tests/test_drop_sweep_identity.py` 98; `tests/test_broker_lifecycle_invariants.py` 96.

**`make ci`:** redirected to `C:\Users\yury_\AppData\Local\Temp\trading-agents-s209-make-ci-2.txt`. Exit code `0`.

**`make gate-ran`:** run from `C:\Users\yury_\Downloads\project\trading-agents` at `e6094ec70247e00ff53cdd126c409cb40ecc3f66`:

```text
uv run python scripts/assert_gate_ran.py
GATE PROVEN for e6094ec70247e00ff53cdd126c409cb40ecc3f66:
  CI: success (attempt 1)
  Security Findings: success (attempt 1)
```

**Not met / verified failing:** Merge, deploy, and live fired-stop proof are not done yet. The live check requires a future scheduled run where a protective stop actually fired; a no-stop-fired run proves nothing.

---

## Return notes

- `DRIFT-064` records that `EXEC-OBS-05` described the defect from S190 until this amendment.
- First full `make ci` exited 2 only because removing the sweep's indirect call to `is_live_broker_stop_order` exposed missing direct coverage in `contracts/broker_lifecycle.py`; `test_broker_order_lifecycle_status_drives_live_stop_orders` fixes that without reintroducing liveness into the sweep.
- `git diff --stat -- contracts` is empty.
