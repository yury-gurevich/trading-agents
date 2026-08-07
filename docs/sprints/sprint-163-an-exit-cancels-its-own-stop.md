<!-- Agent: planning | Role: sprint handover -->
# Sprint 163 — An exit cancels its own stop

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-163-an-exit-cancels-its-own-stop`
**Status:** SPEC — packaged 2026-08-07; **blocks [chore-flatten-and-resize](chore-flatten-and-resize.md)**
**Version:** fix → **0.89.01** (PATCH: a defect in the exit path, no new capability)
**Effort:** S
**Decisions:** [DL-95](../design-log.md) the finding this closes · [DL-93](../design-log.md) the deadlock it unblocks ·
[ADR-0015](../decisions/0015-exit-lifecycle-and-stop-ownership.md) exit lifecycle + stop ownership ·
[ADR-0017](../decisions/0017-exit-authority-alpha-proposes-risk-disposes.md) alpha proposes, risk disposes ·
[DL-70](../design-log.md) plant the violation · [DL-44](../design-log.md) broker is truth for holdings

> **Why PATCH.** This adds no capability — it makes an existing one work. The exit path already
> intends to handle stops (`place_broker_stops` computes `sold_tickers`); it simply acts on that
> knowledge in one direction only. `0.89.00` → **`0.89.01`**.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED v1. Read-only. Never edit.** A clause you believe is wrong is a `drift-register.md` row plus a report |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`IDN`** (execution is the sole broker interface), **`DEP`** (the broker
boundary), **`FAIL`** (degrade, never crash), **`IDM`** (idempotency), **`OBS`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Also read [`docs/laws/dependencies.md`](../laws/dependencies.md) (`DEP-BROKER`),
   [`docs/laws/conventions.md`](../laws/conventions.md), and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Write the Law reading record** (template at the bottom) **before** your first code change.
5. **If a law contradicts this spec, STOP and report.**
6. **If a law is silent**, that silence is a finding: record it and add a `drift-register.md` row.
7. Every test for behaviour a clause governs **cites the clause ID in its docstring**.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/execution/poll.py::execute_pm_node`, `broker_stops.py` | `agents/execution/laws/laws.md` + `test-plan.md`; `docs/laws/dependencies.md` | `EXEC-IDN-01` sole broker interface; `EXEC-IDN-03` owned labels (`BrokerStopOrder`); `EXEC-FAIL-02` degrade without crashing; `EXEC-IDM-*` — **a cancel must be idempotent and safe to repeat**; `DEP-BROKER-01/02` |
| The cancellation fact on the graph | `agents/execution/laws/laws.md`; `docs/laws/conventions.md` | `EXEC-OBS-02` faults; the append-only rule — a cancel is a **new fact**, never an edit |

⚠️ **`ADR-0015 §3` says stops rest at the exchange precisely so nothing can reconsider them in the
moment.** This sprint cancels a stop **only** when the position it protects is being fully exited on
the same run — i.e. the risk it guards is going to zero anyway. **If you find yourself cancelling a
stop for a position that will still be held afterwards, stop and report:** that would be disarming
risk control, which is the opposite of this fix.

---

## Why this sprint

**The book cannot be sold.** Measured 2026-08-07 04:45 UTC against the live Alpaca paper account, at
the baseline step of the flatten chore — before anything was changed:

| | qty | `qty_available` | resting stop |
| --- | --- | --- | --- |
| ABT | 191 | **0** | sell 191 @ 100.24 |
| BAC | 503 | **0** | sell 503 @ 56.65 |
| BMY | 153 | **0** | sell 153 @ 62.34 |
| CSCO | 177 | **0** | sell 177 @ 106.78 |
| HPE | 229 | **0** | sell 229 @ 41.37 |
| MDT | 233 | **0** | sell 233 @ 82.26 |
| PYPL | 175 | **0** | sell 175 @ 53.81 |
| SCHW | 196 | **0** | sell 196 @ 97.10 |
| USB | 478 | **0** | sell 478 @ 59.47 |
| WFC | 348 | **0** | sell 348 @ 82.07 |

**Ten positions, ten resting `gtc` sell stops, each for the full quantity, and `qty_available = 0` on
every one.** Alpaca reserves shares against open sell orders, so a full-exit sell has no shares to
sell. `shorting_enabled: True`, which is why an orphaned stop is dangerous rather than merely untidy.

### The gap, precisely

`execute_pm_node` ([`poll.py:169-180`](../../agents/execution/poll.py#L169)) runs:

1. `reconcile_run_start` — snapshot
2. `reconcile_broker_stops` — cancels only stops whose `position_ref` is **no longer active**. The
   positions being sold are still active here, so nothing is cancelled.
3. `place_broker_stops` — computes `sold_tickers` and **skips placing new** stops for them.
4. `run_submit` — submits the exits into a position with zero available shares.

**`place_broker_stops` already knows exactly which tickers are being sold. It uses that knowledge
only to decline placing a stop, never to cancel the one already resting.** That is the whole defect.

### It is already costing us, in the other direction

Five `Fill` rows are `status=rejected` with `HTTP Error 403`, three carrying Alpaca's reason:

```text
{"code":40310000,
 "existing_order_id":"fd1f1c2c-4911-4df5-b7a1-e2e9929a7341",
 "message":"potential wash trade detected. use complex orders",
 "reject_reason":"opposite side market/stop order exists"}
```

Two **SCHW buys** were rejected the same way. Different path, same root cause: the system places
resting stops and then does not account for them when it next wants to trade that name.

📌 **Marked measured vs assumed.** The rejections above are **observed**. The exit-blocked-by-
`qty_available` case is **inferred** from `qty_available = 0` — no exit has been attempted since the
stops were placed (2026-07-28 → 08-04) because the analyst has returned `hold` throughout. **Test A1
exists to turn that inference into an observation** before the fix is trusted.

### Why it matters now

DL-93/S162 established the pipeline cannot **buy** (`available_for_buys = -105,748.50`). This
establishes it cannot **sell** either. The deadlock is closed at both ends, and the flatten packaged
to open it runs straight into the second wall.

---

## 🪤 Traps

1. **Do not cancel a stop for a position that survives the run.** ADR-0015 §3. Cancel only for
   tickers in `sold_tickers` — and only when the exit is a **full** exit.
2. **Broker and graph must move together.** `cancel_stop` already appends the cancellation fact; use
   it rather than calling `broker.cancel` directly. A broker-side cancel with a stale active
   `BrokerStopOrder` fact leaves the position **unprotected while the graph believes it is
   protected** — and `place_broker_stops` skips any ref in `active_broker_stop_refs(graph)`, so it
   will not self-heal. That is worse than the bug being fixed.
3. **The exit can still fail after the cancel.** If the sell is rejected *after* its stop is
   cancelled, the position is now held **unprotected**. Decide and state what happens: the honest
   options are re-place the stop, or raise an `UnprotectedPosition` fault (the mechanism
   `_record_unprotected_fault` already provides). **Silence is not an option.**
4. **Cancels must be idempotent.** A re-run must not fault on a stop already cancelled — `EXEC-IDM-*`.
5. **Module size.** `poll.py` and `broker_stops.py` are both near the limits; check before adding.
   Split rather than golf (S162 left three modules at 193–198 against the 200 block).
6. **Do not fix this by disabling stops.** Not placing stops at all would make exits work and remove
   risk control. `broker_stop_fallback_stop_pct` is not the lever here.

---

## What ships

> Fill in the `**Result:**` line under each item.

### 1 · An exit cancels the stop that reserves its shares

Before `run_submit`, cancel the active `BrokerStopOrder` for every ticker with an approved **full
exit** this run, via the existing `cancel_stop` so the graph fact and the broker move together.

**Result:**

### 2 · 🎯 Decide what happens when the exit fails after its stop is cancelled

The judgement call. State the decision and the rejected option in the return notes (LAW-06).
**Non-negotiable:** a held position that ends the run without a stop must be **loud** — a fault, not
a log line. Trap 3.

**Result:**

### 3 · Idempotent and safe to repeat

A second run over the same PMRun must not double-cancel, fault spuriously, or resurrect a cancelled
stop. Cite `EXEC-IDM-*`.

**Result:**

### 4 · Prove the checks can fail (DL-70)

Every test plants the violation and requires the failure. **Watch each one fail before trusting it.**

**Result:**

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 **the 2026-08-07 case** | a position with a resting full-quantity stop and `qty_available=0`, plus an approved full exit | the stop is cancelled **before** submit and the exit reaches the broker. **Assert the ordering**, not just the end state — a test that only checks "both happened" passes on the broken order too |
| A2 | a surviving position keeps its stop | approved exit for A, position B also held with a stop | B's stop is **untouched**. ADR-0015 §3 |
| A3 | 🪤 exit rejected after cancel is loud | cancel succeeds, submit returns rejected | the run ends with an `UnprotectedPosition` fault (or the re-placed stop, per item 2) — **never silently unprotected** |
| A4 | idempotent | run the same PMRun twice | one cancellation fact, no second broker cancel, no spurious fault. Cite `EXEC-IDM-*` |
| A5 | broker and graph agree | cancel path | the `BrokerStopOrder` fact is appended-inactive, and `active_broker_stop_refs` no longer returns it |
| A6 | partial/non-exit orders untouched | an approved **buy** | no stop is cancelled for any ticker |

---

## Explicit non-goals

- **No change to stop *placement* policy, thresholds, or `broker_stop_fallback_stop_pct`.**
- **No ADR-0015 or ADR-0017 reversal.** Stops remain unconditional floors; this only removes a stop
  whose position is going to zero on the same run.
- **No flatten, no resize, no parameter move.** Those are the chore, and they run *after* this.
- **No `laws.md` edits.** Findings go to `drift-register.md`.

### The road not taken (LAW-06)

- **`DELETE /v2/positions?cancel_orders=true`** — Alpaca flattens and cancels related orders in one
  call. Rejected: no lineage, and it bypasses `EXEC-IDN-01` — the mechanism DL-93 already ruled out.
- **Hand-cancel the ten stops and run the chore today.** Rejected: it manufactures a divergence in
  the *protection* layer, the one place a silent divergence can cost real money (trap 2).
- **Use bracket/OCO orders so the exit replaces the stop atomically.** The better long-term shape,
  and what Alpaca's own error message suggests ("use complex orders"). Rejected *for this sprint* as
  too large for a fix that must unblock a deadlock today — but it belongs in the design log as the
  direction ADR-0015 §3 probably wants eventually.
- **Widen `qty_available` handling by selling only what is free.** Rejected: it would submit a sell
  for zero shares and call it success.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**, merge, push.
2. **Fleet retag required** — this changes agent behaviour. Check whether the vocabulary pack moved
   (hash it at both commits); if it did not, image-only, as with `:s162`.
3. **Then run [chore-flatten-and-resize](chore-flatten-and-resize.md)**, which is blocked on this.
4. Record the functionality check — and note it is the **first observed successful exit** since the
   stops were placed on 2026-07-28.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 11 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — redirect to a file and read the file (row S).
- Version bump to **0.89.01**, `uv.lock` staged with it.
- Money in integer cents. Never floats.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. State which tree you ran in.

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the four items.
3. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
4. Fill **Closeout — evidence** with real pasted output.
5. Fill **Return notes**, including the item-2 decision and its rejected option.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `execute_pm_node` ordering | | | |
| The cancellation fact | | | |

**Contradictions found between a law and this spec:**

**Laws found silent where a decision was needed:**

**Clauses that were ⬜ and are now proven:**

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |
| A4 | | | | |
| A5 | | | | |
| A6 | | | | |

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):**

**Item 2 decision — post-cancel exit failure, and why:**

**Module line counts after any split:**

**Proven (LAW-02):**

**Planted violations watched fail:**

**Final full gate:**

**Remote gate / gate-ran / merge:**

**Not met / verified failing:**

---

## Return notes
