<!-- Agent: planning | Role: sprint handover -->
# Sprint 146 — A position with no floor: why ABT's stop never came back, and the lineage of four filled orders

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-146-unprotected-position`
**Status:** SPEC — 🟠 **96 ABT shares (~$10k) have carried no protective stop since a 403**
**Version:** fix → **0.80.03** (PATCH: last two digits; `0.80.02` is current)
**Effort:** M
**Decisions:** [ADR-0015](../decisions/) §3 broker stops · [DL-62](../design-log.md) gap-down
exposure · [DL-57](../design-log.md)/[DL-59](../design-log.md) intent ≠ outcome ·
[DL-70](../design-log.md) plant violations · [DL-73](../design-log.md) **(RETRACTED — read it before
you audit anything)** · [DL-44](../design-log.md) broker truth

> **Read [DL-73](../design-log.md) first, including its retraction.** A prior audit of this exact
> area produced a red-severity defect that did not exist, because it filtered `Position` nodes on
> `status == "open"` instead of using `contracts/positions.py::is_active_position_node`. The
> position book is **correct**: 23 nodes, 9 active, one per held ticker, every quantity matching the
> broker. **Do not "fix" reconciliation. Do not close superseded nodes.** If your work makes you
> want to, you have made the same mistake — stop and re-read.

---

## Why this sprint

ADR-0015 §3 exists so every held position has a durable floor at the broker. Eight of nine held
names have one at the correct quantity. **ABT does not**, and has not since its stop submission was
refused. DL-62 describes the exposure this leaves — a gap-down between the 22:30 run and the next
open — and MRVL already turned that exposure into a real **−$1,330.12**.

This is not a big sprint. It is a small one about a real hole in a capital-protection guarantee.

---

## What the audit actually found (2026-07-28, fleet `:s145`)

### Finding 1 — ABT is unprotected, and the skip is unexplained

```text
D5 · Broker holdings with no live protective stop
NO-STOP ABT    qty=96
NO-STOP AMD    qty=55          <- defensible: full-exit sell already pending
OK  BAC  held=503 stop_qty=503     OK  PYPL held=175 stop_qty=175
OK  CSCO held=177 stop_qty=177     OK  SCHW held=196 stop_qty=196
OK  HPE  held=229 stop_qty=229     OK  USB  held=478 stop_qty=478
                                   OK  WFC  held=348 stop_qty=348
```

The evidence, and what it rules out:

- Fill `stop:5244d9de63d93691:ABT` — `status='rejected'`, `reason='HTTP Error 403: Forbidden'`,
  `broker_order_id='rejected:stop:5244d9de63d93691:ABT'`. So the submission was **refused before it
  reached the broker**, and `rejected_broker_fill` recorded that correctly (DL-57 working).
- **No `BrokerStopOrder` node exists for ABT** — there are exactly 7, none of them ABT. So
  `_place_stop`'s `graph.get_node(BROKER_STOP_ORDER_LABEL, key) is not None` guard
  (`agents/execution/broker_stops.py:67-69`) is **not** what blocks the retry, and neither is
  `active_broker_stop_refs` at line 52. **That hypothesis is already eliminated — do not re-test it.**
- On 2026-07-28 the run **did** place SCHW's missing stop (`stop:b56b2d2f124326d3:SCHW`, qty 196) —
  so `place_broker_stops` ran, worked, and skipped ABT specifically.

**The open question is which of the remaining gates ABT fails**, in
`agents/execution/broker_stops.py::place_broker_stops` (lines 48-58):

1. `_fresh_snapshot_quantities(snapshot)` returned `None` — no; SCHW's stop was placed in the same call.
2. `_broker_quantity_matches(threshold, broker_quantities)` — `threshold.quantity` vs broker's 96.
3. `threshold.ticker in sold_tickers` — the PM approved only `AMD sell` that run, so ABT is not in it.
4. **`open_position_stop_thresholds(graph)` never yields ABT at all** — the most likely candidate.
   `contracts/positions.py::_stop_threshold` needs `stop_pct`, and ABT's active node
   `broker:ABT:96:10437` was **created by reconciliation** (`provenance='reconciled-from-broker'`,
   `degraded=True`), not by a PM order intent that carried a `stop_pct`.

If (4) is the cause, the defect is general and serious: **every position adopted from a broker
snapshot rather than opened through the normal path is structurally incapable of receiving a
stop.** ABT is simply the one currently exposed. Confirm before assuming.

### Finding 2 — four filled orders with no `Fill` node

| `client_order_id` | Ticker | Qty | Broker status |
| --- | --- | --- | --- |
| `pm-run-f1f38e5c76104d259ff5383294141273:AMD:buy` | AMD | 19 | `filled` |
| `pm-run-f1f38e5c76104d259ff5383294141273:HPE:buy` | HPE | 229 | `filled` |
| `pm-run-f1f38e5c76104d259ff5383294141273:MRVL:buy` | MRVL | 44 | `filled` |
| `pm-run-6f34914d941d415aada73523ab14d2ea:CSCO:buy` | CSCO | 88 | `filled` |

These are why `broker-reconciled:AMD`, `broker-reconciled:HPE`, `broker-reconciled:MRVL` and
`broker-reconciled:CSCO` exist — the monitor had to invent Positions from a snapshot because no
`Fill` carried the lineage. Ignore the five `dep-broker-probe-*` / `probe-s138-*` orders; they are
test probes with no Fill by design.

### Finding 3 — the credential probe builds a doubled path

`orchestration/packs/trading_vault_probes.py:154`: `_alpaca_account_request` falls back to
`ALPACA_ENDPOINT` and then appends `/v2/account`. The documented `.env.example:108` value already
ends in `/v2`, so the Alpaca credential probe requests `/v2/v2/account` and 404s whenever
`EXECUTION_ALPACA_BASE_URL` is unset. The execution agent is unaffected — it reads
`EXECUTION_ALPACA_BASE_URL` with its own default (`agents/execution/settings.py:70`).

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. See
> [Handback contract](#handback-contract--mandatory) — results go in this file.

### 1 · Find out why ABT is skipped — diagnosis before fix

Do **not** patch until the gate is identified. Write a focused test that reproduces the skip from
the real shape: an active Position with `provenance='reconciled-from-broker'`, `degraded=True`, and
whatever `stop_pct` that node actually carries (inspect it — do not assume), a fresh snapshot whose
holdings match its quantity, and an `OrderIntentSet` that does not sell it. Assert that
`place_broker_stops` places **no** stop, then walk gates 2-4 above until you can name the one that
fails.

State the answer explicitly in the return notes.

**Result:**

### 2 · A snapshot-adopted position must still be able to receive a stop

Assuming item 1 confirms gate 4 (or whichever it is), fix the **cause**:

- A position adopted from a broker snapshot has no PM-supplied `stop_pct`. It still needs a floor.
  Give it one from a declared default — `kernel.tunable(..., why=...)` with bounds, **never a bare
  literal** — and make the fallback explicit and visible rather than implicit.
- The stop price arithmetic must reuse `contracts/stop_rule.py::check_stop`'s own computation, as
  S138 required, so the two cannot drift.
- A position that genuinely cannot be given a justified stop must raise a **`Fault` naming the
  ticker and the reason** — silence is what let ABT sit unprotected (DL-57).
- **Do not force a stop where the guard is right to refuse.** `_broker_quantity_matches` correctly
  refused SCHW while the graph and broker disagreed, and that self-healed. Preserve that behaviour
  exactly; S145 proved it works.

**Result:**

### 3 · A refused stop must be retried, and its refusal must be visible

The 403 was recorded and then nothing happened — for days, on a live position.

- After a refused stop submission, the next run must **re-attempt** it (no `BrokerStopOrder` node is
  written on refusal today, so confirm the retry actually happens rather than assuming).
- Surface unprotected held positions as a **`Fault`** each run they remain unprotected, so the
  condition is loud instead of discoverable only by an audit.
- Diagnose the `HTTP Error 403: Forbidden` itself far enough to say whether it was transient
  (retry suffices) or structural (e.g. shares committed to another order). **Say which in the return
  notes**; if structural, the retry must not become an infinite loop of refusals.

**Result:**

### 4 · Lineage for the four filled orphans (append-only)

`scripts/repair_orphan_fills.py` — dry-run by default, `--apply` to write, `--since` bounded by a
declared tunable, in the `scripts/repair_close_pnl.py` mould.

- Find broker orders whose `client_order_id` has **no** `Fill` chain, resolved via
  `agents.execution.fill_attempts.fill_attempt_chain` so it stays correct with S145 attempt ordinals.
- Adopt **broker state read at run time** — status, `filled_avg_price`, `filled_qty`,
  `broker_order_id`. Never carry an `OrderIntent`'s `est_price_cents` in as if it were a fill price.
- Write through the **same** `agents/execution/store.py::write_fills` path the agent uses, so both
  routes converge on one key and either can run second as a no-op. Attach
  `Fill -EXECUTES-> OrderIntent` where the `OrderIntent` exists.
- Allowlist the `dep-broker-probe-*` / `probe-s138-*` prefixes as **data with a reason string**, not
  an inline `if`.
- **Never write an `ExecutionRun`** — forging the node whose absence proves a crash happened would
  destroy the record in order to tidy it (DL-72).
- Second run reports `already_recorded` for every row and changes no node count.

**Result:**

### 5 · The probe path fix (Finding 3)

`_alpaca_account_request` must not append `/v2` to a base URL that already ends in it. Fix the
fallback; do not change `EXECUTION_ALPACA_BASE_URL`'s meaning.

**Result:**

### 6 · An audit that uses the code's own predicates

`scripts/audit_broker_graph.py`, read-only, non-zero exit on any failure. This exists because the
first version of this sprint was built on an audit that re-derived its own definitions and was
wrong (DL-73 retraction).

- **It must import `contracts.positions.is_active_position_node`** and must **not** filter Positions
  on `status` or any hand-rolled prop check. Same rule for Fill chains: use `fill_attempt_chain`.
- Checks: **A1** one active Position per held ticker with matching quantity · **A2** every held
  position has a live broker stop at the right quantity · **A3** broker orders with no `Fill` chain
  (allowlisted probes excluded) · **A4** unacknowledged `Flag` count, reported not enforced.
- A comment at the top stating why the predicates are imported rather than reimplemented, citing
  DL-73's retraction. This is the guard against repeating the mistake.

**Result:**

### 7 · Prove every check can fail (DL-70)

Plant the violation and require the failure — no presence assertions:

- plant a held position with no stop → **A2 fails**; run item 2's placement → passes;
- plant a filled broker order with no Fill → **A3 fails**; run item 4's repair → passes;
- plant **two** active Positions for one held ticker → **A1 fails** (this is the check whose absence
  produced DL-73);
- plant a Position carrying `broker_superseded_by` → **A1 still passes**, proving the audit honours
  the real predicate rather than counting raw nodes;
- plant `ALPACA_ENDPOINT=https://paper-api.alpaca.markets/v2` → assert the probe URL has one `/v2`;
- plant a stop submission that raises 403 → assert a `Fault` is recorded **and** the next run
  re-attempts.

**Result:**

### 8 · Prove it against production

- Run the audit **before** any change; paste the failing rows (expect A2:ABT and A3:×4).
- Apply fixes; run the repair dry-run then `--apply`.
- Run the audit again; paste it. **Target: A1, A2, A3 clean; A4 reported.**
- ABT must end with a live broker stop at qty 96 **or** a stated, evidenced reason why it must not
  have one — a refusal you can justify is a valid outcome, a silent gap is not (LAW-02).
- Record the row in `docs/laws/functionality-checks.md`, with teardown for anything the check created.

**Result:**

---

## Explicit non-goals

- **Do not touch reconciliation or Position supersession.** It is correct. See the DL-73 retraction.
- **Do not acknowledge the 46 Flags.** Operator action from the dashboard (S127); bulk-acking from a
  script destroys the signal that some are real. Report the count.
- **Do not change the S145 exit-replay, attempt-key, or adoption paths.** Shipped, tested, and
  proven in production on 2026-07-28. If the audit implicates them, **stop and report**.
- **Do not force a stop onto AMD.** It has a full-exit sell pending; a stop under a closing position
  is what S138 Part B's `sold_tickers` skip exists to prevent.
- **No broker-side cleanup** — do not cancel or modify live orders.
- **No cascade reordering** — DL-71 option B stays out.

### The road not taken (LAW-06)

**Placing ABT's stop by hand and moving on.** It would close the exposure in one API call, and the
temptation is real while the position sits unprotected. Rejected because the same 403 will recur on
the next snapshot-adopted position and nobody will be watching; the hole is the missing retry and
the missing Fault, not the missing order. If the operator wants the exposure closed *now*, that is a
separate deliberate action — not this sprint quietly doing it and calling the defect fixed.

**Writing the audit against raw node props again, because it is quicker.** That is exactly how
DL-73 happened. The import rule in item 6 is the fix.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, all remote gates green **before** merging locally
   (DL-56 — pushing is the gate; no PR required).
2. The repair script needs no retag. The **code** fixes do: build + retag at the next `:sNNN`
   (fleet is on `:s145`).
3. Re-run the audit **after the next scheduled run** — proving reconciliation and stop placement
   keep A1/A2 clean is the real proof, not making them clean once.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds (the stop-pct fallback and `--since`
  default included).
- Faults, not silent failure — `kernel.fault_boundary`, errors redirected with provenance.
- `make ci` all 9 steps green, **100.00 % coverage floor**, before handback. Never lower the floor.
- Version bump in `pyproject.toml` to **0.80.03** (fix → PATCH), `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the test docstring.
- Declare any new label/edge/prop in `orchestration/packs/trading_graph_vocabulary.json` and re-run
  `scripts/vocabulary_coverage.py` + `scripts/vocabulary_signatures.py`.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48).
- Secrets never through the worktree — chat or gitignored `.env` only.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the two placeholder sections below.**
Not a separate report file. Not chat-only. Not a summary that points elsewhere.

1. Fill the `**Result:**` line under **each** of the eight spec items above, in place.
2. Fill the **Closeout — evidence** block with real command output: the **before** audit, `make ci`
   counts, the remote gate results, the repair dry-run and `--apply` tables, and the **after** audit.
3. Fill the **Return notes** block — including item 1's answer (**which gate skipped ABT**) and
   item 3's (**was the 403 transient or structural**).
4. State any success factor you did **not** meet plainly, as "verified failing" or "not done".

An incomplete handback is returned, not repaired (DL-48).

---

## Closeout — evidence

**Files changed:**

_(fill in)_

**Proven (LAW-02):**

_(fill in — before-audit, `make ci`, remote gates, repair output, after-audit, ABT's final stop state)_

**Not done, deliberately:**

_(fill in)_

---

## Return notes

- **Which gate skipped ABT (item 1), and was the 403 transient or structural (item 3)?**
- **Decisions made inside the sprint** (and anything ruled out — LAW-06):
- **Surprises / anything the spec got wrong:**
- **Did `main` move? Merge performed, `make ci` re-run?**
- **Out-of-scope findings** (flag, do not fix):
