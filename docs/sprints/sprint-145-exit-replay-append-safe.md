<!-- Agent: planning | Role: sprint handover -->
# Sprint 145 — The exit replay was write-once: unbrick execution, make attempts append-safe

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-145-exit-replay-append-safe`
**Status:** SPEC — 🔴 **execution is currently bricked in production; this is a fix, not a feature**
**Version:** fix → **0.80.02** (PATCH: last two digits; `0.80.01` is current)
**Effort:** M
**Decisions:** [DL-71](../design-log.md) · exit key from 0.74.01 · [DL-44](../design-log.md) broker
truth · [DL-57](../design-log.md)/[DL-59](../design-log.md) intent ≠ outcome ·
[DL-70](../design-log.md) plant violations · [ADR-0015](../decisions/) §3 ·
[ADR-0016](../decisions/) one rail · [ADR-0017](../decisions/) exit authority

---

## Why this sprint

`sched-2026-07-27` — the first session-day run after the broker-stops deploy — reached **4 of 7
stages** and scored `ACCEPTANCE FAIL`. Execution crashed on an uncaught `ValueError`, restarted,
crashed again, and kept doing that every few minutes until the KEDA window closed. Monitor and
reporter never ran.

The crash is not self-clearing. `find_pending` returns every `PMRun` with no downstream
`ExecutionRun`, and `run_once` processes items in order; the poisoned node is returned first on
every poll, forever. **Tonight's run, and every run after it, hits the same crash before reaching
its own work.** Execution is bricked until this ships.

Two things did go right in the same run and must not be broken by the fix:

- **Broker-native stops went live for the first time** (ADR-0015 §3's pending proof) — six resting
  `sell stop` orders at Alpaca, placed 22:40:25–29 UTC: BAC 503 @ 56.65, CSCO 177 @ 106.78,
  HPE 229 @ 41.37, PYPL 175 @ 53.81, USB 478 @ 59.47, WFC 348 @ 82.07, each with a real broker
  order id. `place_broker_stops` runs *before* `run_submit` in `poll.py`, which is the only reason
  the proof survived the crash.
- **The MRVL forced stop-sell filled** — `44 @ $195.98` at 2026-07-27 13:36 UTC, realized
  **−$1,330.12**. First realized forced-stop exit in the system's history.

---

## What actually happened — the chain, with evidence

**1. The MRVL exit completed at Monday's open.** Alpaca closed order: `MRVL sell market qty=44
status=filled filled_avg=195.982955 at=2026-07-27T13:36:29`. The graph agrees — Fill
`exit:e67227ec57fa1e46:MRVL:sell` carries `broker_status=filled`, `broker_price_cents=19598`,
`realized_pnl_cents=-133012`, refreshed `2026-07-27T22:40:24`.

**2. Nothing removed the position from the book.** Position reconciliation from the broker
snapshot is the monitor's step (stage 6, DL-44). The last completed run was 07-24; 07-25 and 07-26
were clean weekend calendar skips. So when the analyst ran at 22:39 on 07-27, `broker:MRVL:44:22621`
was still an open Position.

**3. The analyst re-decided a sell on a position that no longer existed.** Trace:
`MRVL sell conf=0.66`. Correct behaviour given its inputs — its inputs were nine hours stale.

**4. The PM approved a full exit of it.** `pm-run-df925eea…`: `approved=3 rejected=7`, including
`MRVL sell qty=44 est=$189.28` carrying the **same** `position_ref` as the exit that had already
filled (the `e67227ec…` in the Fill key above — it is a hash of the open Position node keys, and
those had not changed, because nothing had closed the position).

**5. Execution submitted all three intents, then died writing the first fill.** AMD sell 55
(22:40:30) and ABT buy 95 (22:40:31) are `accepted` at Alpaca right now. No MRVL order exists with
a 22:40 timestamp, so that submission was refused at submit time — DL-59's named case — and
`rejected_broker_fill` built a durable rejected outcome **carrying the same idempotency key**.
`write_fills` then tried to merge it onto the filled node from step 1:

```text
Traceback (most recent call last):
  File "/app/agents/execution/entrypoint.py", line 40, in <module>
    main()
  File "/app/agents/execution/entrypoint.py", line 30, in main
    work_loop(
  File "/app/kernel/work_loop.py", line 40, in work_loop
    if run_once(find_pending, process_one) == 0:
  File "/app/kernel/work_loop.py", line 28, in run_once
    process_one(item)
  File "/app/agents/execution/entrypoint.py", line 32, in <lambda>
    lambda node: execute_pm_node(node, graph=graph, broker=broker, settings=settings)
  File "/app/agents/execution/poll.py", line 88, in execute_pm_node
    result = run_submit(graph, broker, sink, {}, order_set, default_stage=settings.stage)
  File "/app/agents/execution/run.py", line 46, in run_submit
    provenance = write_fills(graph, run_id=run_id, fills=fills, order_set=order_set)
  File "/app/agents/execution/store.py", line 43, in write_fills
    node = graph.merge_node("Fill", ...)
  File "/app/kernel/graph_postgres.py", line 68, in merge_node
    return self._raise_merge_conflict(label, key, props, schema_version)
  File "/app/kernel/graph_postgres.py", line 142, in _raise_merge_conflict
    _append_props(current.props, props)
  File "/app/kernel/graph_support.py", line 71, in _append_props
    raise ValueError(f"property {name!r} cannot be overwritten")
ValueError: property 'price_cents' cannot be overwritten
```

`price_cents` was `19451` (the 07-25 reference price) and the replay carried `18928` (`est=$189.28`).

**6. It crash-looped.** Tracebacks at 22:40:31 and 22:40:43, then container-restart backoff to
roughly one attempt per five minutes — a `BrokerPositionSnapshot`, a divergence `Flag` and a
realized-PnL `Fault` appended on each pass — through `2026-07-28T00:33:16`, when the KEDA window
closed. No `ExecutionRun`. No monitor. No reporter.

### The defect, precisely

0.74.01 keyed exit orders on the position rather than the run, so an unfilled sell would *"replay
instead of duplicating"*. The key is one string doing two jobs:

- **at the broker** it is the `client_order_id` — the oversell guard, and it worked;
- **in the graph** it is the `Fill` node key — and the graph is append-only.

A replay is byte-identical only if the reference price never moves. It always moves. **The replay
path had never actually replayed before**; its first real execution is the one that killed the
cascade. The oversell guard was correct; the assumption that a replay is a *rewrite* was not.

### Two consequences to clean up

- **Two live orders have no lineage.** AMD sell 55 and ABT buy 95 are `accepted` at Alpaca with no
  `Fill` node and no `ExecutionRun`. A naive retry will be refused as a duplicate `client_order_id`
  and record `rejected` for orders that are live — a lineage lie of exactly the DL-57/DL-59 class.
- **SCHW (196 sh, $20.4k) holds no broker stop.** This one is the guard working, not a defect:
  `_broker_quantity_matches` compares the graph Position (`broker:SCHW:98:10177`, qty 98) against
  the broker holding (196) and refuses to size a stop it cannot justify. It self-heals once the
  monitor reconciles. **Verify it, do not "fix" it.**

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. See
> [Handback contract](#handback-contract--mandatory) — results go in this file.

### 1 · One attempt = one node (the unbrick)

Separate the two jobs the key is doing.

- `BrokerOrder.idempotency_key` stays exactly `exit:{position_ref}:{ticker}:sell` — the broker
  `client_order_id`, the 0.74.01 oversell guard. **Do not change it.**
- The **graph node key** gains an attempt discriminator when a node already exists under that key
  (recommended `f"{idempotency_key}#{n}"`, n from the first free ordinal). The node carries the
  attempt ordinal and the broker idempotency key as props so the attempts of one exit stay
  queryable as a chain.
- **Hard invariant:** `write_fills` never merges onto an existing `Fill` node with differing
  immutable props. Not "usually"; never. Every attempt is its own immutable fact, which is what an
  append-only store means (the same reasoning as `repair_close_pnl.py` appending markers rather
  than rewriting history).
- Re-run the S144 vocabulary checks (`scripts/vocabulary_coverage.py`,
  `scripts/vocabulary_signatures.py`) and declare anything new in
  `orchestration/packs/trading_graph_vocabulary.json`.

**Result:** ⬜

### 2 · Never re-issue a completed exit

- Before submitting a sell intent that carries a `position_ref`, look up the exit's Fill chain. If
  the latest attempt has `broker_status` in `{filled, partially_filled}`, **do not submit**. Record
  a `Fault` (source `execution`, naming ticker, `position_ref`, prior fill key) and account for it
  in the `ExecutionResult` as skipped — visible, not silent (DL-57).
- Do **not** skip on `rejected`/`canceled`: that is a genuine re-attempt, and item 1 is what makes
  it writable.
- Rationale: the broker's duplicate-`client_order_id` refusal is the outer guard and it held. This
  is the inner one, and its real value is that the *reason* becomes legible instead of arriving as
  an opaque submit-time rejection.

**Result:** ⬜

### 3 · One bad intent must not kill three stages

Execution is a fan-out stage. A per-item defect must degrade to a per-item fault — the DRIFT-014 /
S128 pattern (*one 429 costs one ticker, not the feed*) applied to order submission.

- Wrap per-intent submit-and-write in `kernel.fault_boundary`. The `ExecutionRun` is still written
  with whatever succeeded, so the cascade reaches monitor and reporter.
- Test: three intents, the middle one raises → the other two submit, `ExecutionRun` is written with
  the correct `submitted` count, one `Fault` is recorded, and `run_once` returns without raising.
- This is the half of the fix that would have limited last night's blast radius to one ticker even
  with the item-1 defect still present. Ship both.

**Result:** ⬜

### 4 · Adopt, don't fabricate — the orphaned 2026-07-27 orders

- When a submission is refused **and** the broker reports an existing order for that
  `client_order_id`, execution adopts the broker's order (its status and `broker_order_id`) rather
  than writing a fabricated rejection. Broker is truth for order state (DL-44).
- The two orphans (AMD sell 55, ABT buy 95, both submitted 2026-07-27 22:40) must end up with
  honest `Fill` nodes reflecting their **real** broker state.
- If adopting inside the submit path proves too broad for this sprint, a one-shot repair script in
  the `scripts/repair_close_pnl.py` mould (append, never rewrite) is an acceptable way to heal the
  two existing orphans — but the submit-path behaviour must still be specified and tested, because
  a crash-then-retry recreates this situation every time it happens.

**Result:** ⬜

### 5 · Prove the checks can fail (DL-70)

No presence assertions. Plant the violation and require the failure:

- plant a `Fill` under an exit key, write a second attempt with a different `price_cents`, assert a
  **second node** exists and the first is untouched;
- plant a `filled` exit Fill, submit the same intent again, assert it is skipped **and** a `Fault`
  is recorded naming the position;
- the item-3 test above is itself a planted-violation test — keep it that shape.

**Result:** ⬜

---

## Explicit non-goals

- **No change to the broker idempotency key scheme** (0.74.01). It did its job; the oversell hazard
  it exists to prevent is still real.
- **No change to the stop path** (ADR-0015 §3). It placed six live stops last night. Touch nothing
  in `broker_stops.py` beyond what item 1 forces, and re-verify the stop e2e test still passes.
- **Do not "fix" SCHW's missing stop.** Verify it heals after the resume (see above).
- **No S144 vocabulary enablement in this branch.** It stays a separate dated action, sequenced
  after this fix and the resumed run.
- **No monitor or analyst change** — see the road not taken.

### The road not taken (LAW-06)

The upstream cause is that **the analyst scored a book that was nine hours stale**: the broker
snapshot is written by execution at stage 5, but the position book is only healed by the monitor at
stage 6, one full run later. Reconciling before the analyst decides would have made every
downstream symptom impossible.

It is not this sprint because it reorders the cascade, touches DL-44's ownership of position truth,
and would ship as a design change on top of a production outage. Recorded as **DL-71 option B** so
it is not silently dropped — it is deferred, not rejected, and it is the natural successor sprint.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, all four remote gates green **before** merging locally
   (DL-56 — pushing is the gate; no PR required).
2. Build + retag the fleet at the next `:sNNN` tag. The running fleet is `:s143`; the fix is not in
   it, so nothing changes in production until the retag.
3. **Resume the run** (`/resume-run`) and prove the cascade completes: 7/7 stages, monitor and
   reporter reached, MRVL leaves the position book, SCHW receives its broker stop, and the AMD/ABT
   orphans carry honest Fill nodes.
4. Only then, S144's dated fleet enablement of `GRAPH_VOCABULARY_B64`.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds, never a bare literal.
- Faults, not silent failure — `kernel.fault_boundary`, errors redirected with provenance.
- `make ci` all 9 steps green, **100.00 % coverage floor**, before handback. Never lower the floor.
- Version bump in `pyproject.toml` to **0.80.02** (fix → PATCH), `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the test docstring.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48 — drift reconciliation is the coding agent's step).
- Secrets never through the worktree — chat or gitignored `.env` only.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the two placeholder sections below.**
Not a separate report file. Not chat-only. Not a summary that points elsewhere.

Specifically:

1. Fill the `**Result:**` line under **each** of the five spec items above, in place.
2. Fill the **Closeout — evidence** block at the bottom of this file, with real command output
   pasted in — `make ci` counts, the remote gate job results, the planted-violation runs.
3. Fill the **Return notes** block at the bottom of this file.
4. State any success factor you did **not** meet plainly, as "verified failing" or "not done"
   (LAW-02 — intent is never restated as outcome; a proven failure is a valid handback, a silent
   gap is not).

An incomplete handback is returned, not repaired (DL-48).

---

## Closeout — evidence

> **PLACEHOLDER — the coding agent fills this in. Do not hand back with it unfilled.**

**Files changed:**
*(list every file, with a phrase on why)*

**Proven (LAW-02):**

- ⬜ `make ci` — *N passed / N skipped / coverage %*, pip-audit clean, detect-secrets clean, gate
  self-test *N/N*.
- ⬜ Remote gates green **before** merge on `<sha>`: `quality` · `test` · `security` · `gate`.
- ⬜ Item 1 — a second attempt writes a **new node**; paste the test name and the assertion.
- ⬜ Item 2 — a completed exit is skipped with a `Fault`; paste the test name and the Fault message.
- ⬜ Item 3 — a poisoned intent leaves the other two submitted and the `ExecutionRun` written;
  paste the counts.
- ⬜ Item 4 — the AMD/ABT orphans carry Fill nodes matching their real broker state; paste the
  before/after.
- ⬜ Item 5 — every new check observed **failing** on a planted violation, not merely passing.
- ⬜ **Functionality check** against the live spine (`docs/laws/functionality-checks.md`), plus
  teardown of anything created. Unit-green ≠ works.

**Not done, deliberately:**

- ⬜ *(list, with the reason — or "nothing")*

---

## Return notes

> **PLACEHOLDER — the coding agent fills this in.**

- **Decisions made inside the sprint** (and anything ruled out — LAW-06):
- **Surprises / anything the spec got wrong:**
- **Did `main` move? Merge performed, `make ci` re-run?**
- **Out-of-scope findings** (flag, do not fix):
