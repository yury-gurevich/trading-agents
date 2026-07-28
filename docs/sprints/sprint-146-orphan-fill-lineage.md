<!-- Agent: planning | Role: sprint handover -->
# Sprint 146 — Two live orders nobody recorded: heal the AMD/ABT orphan fills deterministically

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-146-orphan-fill-lineage`
**Status:** SPEC — 🟠 **lineage lie in production; capital is real, the record is missing**
**Version:** fix → **0.80.03** (PATCH: last two digits; `0.80.02` is current)
**Effort:** S–M
**Decisions:** [DL-71](../design-log.md) named limit · [DL-72](../design-log.md) ·
[DL-44](../design-log.md) broker truth · [DL-57](../design-log.md)/[DL-59](../design-log.md)
intent ≠ outcome · [DL-70](../design-log.md) plant violations · [ADR-0017](../decisions/) exit
authority

---

## Why this sprint

S145 unbricked execution and shipped the submit-path adoption that *should* heal the two orphaned
orders from the `sched-2026-07-27` crash. It closed with an honest "not done": the production AMD
and ABT orders still carry **no `Fill` node**, so the graph does not know that capital moved.

This sprint closes that gap and — more importantly — removes the **coincidence** the healing
currently depends on. Right now the orphans would heal only because the crashed `PMRun` never got
an `ExecutionRun`, so `find_pending` still returns it. That is luck, not design. Anything that
writes an `ExecutionRun` for `pm-run-df925eea…` (a resume, a manual repair, a future dedupe change)
makes those two orders **permanently unrecordable**, and the graph carries a silent lie forever.

---

## What the graph and the broker actually say

Probed read-only against production Neon + Alpaca paper on **2026-07-28**, after the S145 merge
(`2c49f88`). This is current state, not S145's narrative.

### The two orphans — live at the broker, absent from the graph

| Ticker | Side | Qty | `client_order_id` | Broker order id | Broker status | Submitted (UTC) |
| --- | --- | --- | --- | --- | --- | --- |
| AMD | sell | 55 | `exit:22d71d0d3acc0586:AMD:sell` | `d040c762-3621-49f7-b862-60540a271aa2` | `accepted` | 2026-07-27T22:40:30.880Z |
| ABT | buy | 95 | `pm-run-df925eea017a4a7e94cd4365bf20c25a:ABT:buy` | `fd1f1c2c-4911-4df5-b7a1-e2e9929a7341` | `accepted` | 2026-07-27T22:40:31.500Z |

The graph holds **43 `Fill` nodes** and **neither of these keys**. Both orders are still `accepted`
— after-hours market orders queued for the next session open.

### The lineage that *does* exist, and the one node that does not

- `PMRun:pm-run-df925eea017a4a7e94cd4365bf20c25a` — `created_at=2026-07-27T22:39:24.518581+00:00`,
  `approved_count=3`, `rejected_count=7`, `source_analyst_run_id=analyst-run-abcb1a68a1824398…`.
- `OrderIntent:pm-run-df925eea017a4a7e94cd4365bf20c25a:AMD` — `action=sell`, `quantity=55`,
  `position_ref=22d71d0d3acc0586`, `est_price_cents=49490`, all seven gates `passed=True`.
- `OrderIntent:pm-run-df925eea017a4a7e94cd4365bf20c25a:ABT` — `action=buy`, `quantity=95`,
  `position_ref=None`, `est_price_cents=10457`, all seven gates `passed=True`.
- `OrderIntent:pm-run-df925eea017a4a7e94cd4365bf20c25a:MRVL` — the phantom exit; `position_ref=`
  `e67227ec57fa1e46`, `est_price_cents=18928` — the `18928` from the S145 traceback.
- **No `ExecutionRun` with `source_pm_run_id=pm-run-df925eea…`.** Confirmed absent; the sorted
  `ExecutionRun` list steps straight from `…d77d55bc` to `…e7474bc6`.

So `write_fills`' `_link_order_intent` has real `OrderIntent` nodes to attach to
(`Fill -EXECUTES-> OrderIntent`, keyed `{pm_run_key}:{ticker}`). The repair is not inventing
lineage; it is attaching a missing fact to lineage that already exists.

### The self-heal that works today — and why it is not good enough

Because that `ExecutionRun` is missing, `pm-run-df925eea…` is **still pending**. On the next
execution pass the S145 code will:

1. **MRVL** → completed-exit skip, one `Fault`, `skipped=1` (S145 item 2);
2. **AMD** → `submit` under the identical `client_order_id` → Alpaca `422 duplicate` →
   `_submit_or_get` falls back to `GET /v2/orders:by_client_order_id` → adopts broker truth →
   honest `Fill` (S145 item 4);
3. **ABT** → same adoption path;

then writes the `ExecutionRun` that has been missing since the crash. **That is the happy path and
it is genuinely likely to work.** The problem is that it is *single-shot and unrepeatable*: once
that `ExecutionRun` exists, `find_pending` never returns this `PMRun` again. If the pass writes the
`ExecutionRun` but the adoption silently fails for one ticker — a 404 on the by-client lookup, a
timeout inside the new per-intent fault boundary, an Alpaca order that has aged out — that ticker's
`Fill` can never be written by the normal path again. **The window closes whether or not the
repair succeeded.** That is what this sprint removes.

### Two facts found while probing that are NOT this sprint's job

Recorded because they are worse than the orphans and must not be lost:

- **The position book is badly diverged from the broker.** AMD: three `open` Position nodes
  (`broker-reconciled:AMD` qty 19, `broker:AMD:37:53978` qty 37, `broker:AMD:55:53127` qty 55) —
  **111 shares of graph position against 55 held**. MRVL: broker holds **no MRVL at all** (the
  07-27 exit filled), yet `broker:MRVL:44:22621` and `broker-reconciled:MRVL` are both still
  `open`. ABT graph 98 vs broker 96; SCHW graph 98 vs broker 196.
- **`exit:e67227ec57fa1e46:MRVL:sell` carries `status='pending'` with `broker_status='filled'`.**
  The realized PnL landed (`realized_pnl_cents=-133012`) but the top-level `status` was never
  promoted, so a reader trusting `status` sees a pending order that closed nine hours earlier.

Both belong to monitor reconciliation / DL-71 option B. See the road not taken.

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. See
> [Handback contract](#handback-contract--mandatory) — results go in this file.

### 1 · A deterministic repair path that does not depend on a pending PMRun

Add `scripts/repair_orphan_fills.py`, in the `scripts/repair_close_pnl.py` mould: dry-run by
default, `--apply` to write, `POSTGRES_DSN` + Alpaca creds from `.env`, **append only, never
rewrite**.

- Find broker orders that have **no `Fill` node** under their `client_order_id` (use
  `agents.execution.fill_attempts.fill_attempt_chain` — an orphan is an empty chain, so the check
  keeps working once attempt ordinals exist).
- Bound the scan: only orders whose `client_order_id` matches a `PMRun`/exit key the graph knows,
  and only within a `--since` window (default: 7 days). Do not adopt arbitrary broker history.
- Write the `Fill` through the **same** `write_fills` path the agent uses, so props, the attempt
  key, and the `Fill -EXECUTES-> OrderIntent` edge are produced by one code path, not two.
- Print a per-order verdict table (`would_adopt` / `adopted` / `already_recorded` / `no_lineage`)
  and a totals line, exactly like `repair_close_pnl.py`.

**Result:**

### 2 · Adopt the broker's state at repair time — never the state in this document

The orders were `accepted` when this sprint was written. They are queued market orders and will
almost certainly be `filled` by the time you run the repair.

- Read status, `filled_avg_price`, `filled_qty`, and `broker_order_id` **from the broker response
  at execution time**. Do not hardcode `accepted`, and do not carry the `est_price_cents` from the
  `OrderIntent` into `price_cents` as though it were a fill price.
- Map `accepted`/`new`/`pending_new` to a non-terminal status; map `filled`/`partially_filled` to
  the filled statuses `repair_close_pnl.py` already recognises; map `canceled`/`expired`/`rejected`
  honestly rather than as a fill.
- If the order has vanished from the broker (404 by client id), write **nothing** and report
  `no_broker_record` — a missing order is not a rejected order (DL-57/DL-59).

**Result:**

### 3 · Idempotent, and safe to run beside the agent

- Running the repair twice writes nothing the second time: the second pass reports
  `already_recorded` for every row and the graph node count is unchanged.
- Running the repair after the agent has already self-healed the orphan must also be a no-op — the
  two paths must converge on the same key, which is what item 1's "same `write_fills`" rule buys.
- Do **not** write an `ExecutionRun` from the repair script. The repair heals *fills*; inventing an
  execution run would forge the very node whose absence proves the crash happened.

**Result:**

### 4 · Prove it against production, and leave the proof behind

- Run dry-run first, paste the verdict table into the closeout, then `--apply`.
- After applying, re-probe and show: `Fill` node for `exit:22d71d0d3acc0586:AMD:sell` and for
  `pm-run-df925eea017a4a7e94cd4365bf20c25a:ABT:buy`, each with the broker's real status and
  `broker_order_id`, each carrying an `EXECUTES` edge to its existing `OrderIntent`.
- If the nightly run heals them before you get there, **say so and prove that instead** — re-probe,
  show the adopted nodes, and demonstrate item 3's no-op on top. A healed-by-the-agent outcome is
  a pass, not a failure; a silent assumption that it healed is a fail (LAW-02).
- Record the row in `docs/laws/functionality-checks.md`, with teardown for anything the check
  itself created.

**Result:**

### 5 · Prove the checks can fail (DL-70)

No presence assertions. Plant the violation and require the failure:

- plant a broker order with no `Fill` node → assert the script reports exactly one `would_adopt`
  and, in dry-run, that the graph is **unchanged**;
- plant a broker order that *is* already recorded → assert `already_recorded` and zero writes;
- plant a by-client lookup that 404s → assert `no_broker_record` and that **no** `Fill` is written
  (this is the DL-57 fabrication guard; it must fail loudly if someone later "helpfully" writes a
  rejected node here);
- plant a `filled` broker order whose `filled_avg_price` differs from the `OrderIntent`
  `est_price_cents` → assert the written `price_cents` came from the **broker**.

**Result:**

---

## Explicit non-goals

- **No position-book reconciliation.** The AMD 111-vs-55 and MRVL 2-open-vs-0-held divergences are
  real and worse than the orphans, but they are the monitor's job under DL-44 and the subject of
  DL-71 option B. Fixing them here would mean this sprint quietly rewrites position truth.
- **No `status`/`broker_status` promotion for `exit:e67227ec…:MRVL:sell`.** Same reason: that is
  the pending-refresh path, not the orphan path.
- **No change to the submit path.** S145 shipped it and it is tested. If the repair reveals the
  adoption is wrong, **stop and report** — do not fix it inside this sprint.
- **No change to the broker idempotency key scheme** (0.74.01).
- **No cancelling or modifying live broker orders.** This sprint records what happened; it does not
  decide what should happen to open capital. That is an operator decision.

### The road not taken (LAW-06)

**Doing nothing and letting the nightly run adopt them.** Genuinely tempting: the path exists, it
is tested, and the `PMRun` is still pending, so it would probably just work. Rejected because the
window is single-shot — the `ExecutionRun` write closes it permanently, whether or not every
ticker healed — and because "probably worked" is not a proof (LAW-02). The repair script is also
the thing that makes the *next* crash-orphan survivable, and there will be a next one.

**Extending the monitor to adopt orphans during reconciliation.** The natural long-term home, and
it would fix the position book at the same time. Deferred to DL-71 option B: it moves order truth
into the monitor's reconciliation pass, which is a cascade-ordering change, and the same argument
that deferred it in S145 still holds — do not reorder the cascade while cleaning up after an
outage.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, all remote gates green **before** merging locally
   (DL-56 — pushing is the gate; no PR required).
2. Run the repair dry-run, then `--apply`, then re-probe. This is a script, not agent code — it
   does **not** require a fleet retag to take effect.
3. Only then consider DL-71 option B (reconcile the book before the analyst decides), which is the
   sprint that makes both the orphans and the position divergence structurally impossible.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds, never a bare literal (the
  `--since` window default included).
- Faults, not silent failure — `kernel.fault_boundary`, errors redirected with provenance.
- `make ci` all 9 steps green, **100.00 % coverage floor**, before handback. Never lower the floor.
- Version bump in `pyproject.toml` to **0.80.03** (fix → PATCH), `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the test docstring.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48 — drift reconciliation is the coding agent's step).
- Secrets never through the worktree — chat or gitignored `.env` only.
- Declare any new label/edge in `orchestration/packs/trading_graph_vocabulary.json` and re-run the
  S144 vocabulary checks. This sprint should need none — that is itself worth confirming.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the two placeholder sections below.**
Not a separate report file. Not chat-only. Not a summary that points elsewhere.

Specifically:

1. Fill the `**Result:**` line under **each** of the five spec items above, in place.
2. Fill the **Closeout — evidence** block at the bottom of this file, with real command output
   pasted in — `make ci` counts, the remote gate job results, the dry-run and `--apply` verdict
   tables, the post-repair probe.
3. Fill the **Return notes** block at the bottom of this file.
4. State any success factor you did **not** meet plainly, as "verified failing" or "not done"
   (LAW-02 — intent is never restated as outcome; a proven failure is a valid handback, a silent
   gap is not).

An incomplete handback is returned, not repaired (DL-48).

---

## Closeout — evidence

**Files changed:**

_(fill in)_

**Proven (LAW-02):**

_(fill in — `make ci` output, remote gate runs, dry-run table, `--apply` table, post-repair probe
showing both Fill nodes with broker-sourced status and their `EXECUTES` edges)_

**Not done, deliberately:**

_(fill in)_

---

## Return notes

- **Decisions made inside the sprint** (and anything ruled out — LAW-06):
- **Surprises / anything the spec got wrong:**
- **Did `main` move? Merge performed, `make ci` re-run?**
- **Out-of-scope findings** (flag, do not fix):
