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

**Result:** Done. New `agents/execution/exit_stops.py` (108 lines). `cancel_stops_for_exits` takes
the sold tickers from the **PM's approved intents** (`EXEC-NEV-01` — execution does not choose what
to free) and cancels each matching active `BrokerStopOrder`. It returns only the tickers whose fact
actually flipped, re-reading `active_broker_stop_orders` afterwards: a cancel that failed leaves the
stop resting, so that position is still protected and must not be reported as freed. `settle_stops`
sequences reconcile → cancel → place, and `poll.py` calls it in one line — **`poll.py` went
191 → 188 lines**, so the fix shrank the call site rather than growing it.

### 2 · 🎯 Decide what happens when the exit fails after its stop is cancelled

The judgement call. State the decision and the rejected option in the return notes (LAW-06).
**Non-negotiable:** a held position that ends the run without a stop must be **loud** — a fault, not
a log line. Trap 3.

**Result:** Done — **and it was not mine to decide.** `EXEC-OBS-03` already prescribes it: *“A held
position that ends a run with no live broker stop is surfaced as an `UnprotectedPosition` fault and
retried on the next run.”* Implemented as `report_unprotected_exits`, called after `run_submit`. It
faults only for a **freed** ticker whose sell came back `rejected` — a freed ticker with no fill at
all was skipped as an already-completed exit and is no longer held, so faulting on it would be a
false alarm.

### 3 · Idempotent and safe to repeat

A second run over the same PMRun must not double-cancel, fault spuriously, or resurrect a cancelled
stop. Cite `EXEC-IDM-*`.

**Result:** Done. Cancellation is an appended `cancelled_at` marker, so the fact leaves
`active_broker_stop_orders` and a replay finds nothing to cancel: the second call returns an empty
set, issues no broker cancel, and raises no fault.

### 4 · Prove the checks can fail (DL-70)

Every test plants the violation and requires the failure. **Watch each one fail before trusting it.**

**Result:** Done, and it caught a false pass. Planting `freed = frozenset()` in place of the cancel
call gave **2 failed, 5 passed** — A1 (ordering) and A3 (unprotected fault), exactly the pair that
depends on the wiring. Restored, 7 passed.

🚨 **Before that, A1 was green for the wrong reason.** The fixture returned the Position *node key*
instead of the real `position_ref`, so the stop looked stale to `reconcile_broker_stops`, which
cancelled it through the **pre-existing** path — the new code never ran and the test still passed.
Found because A3 failed while A1 “passed”. The helper now reads the ref back from `open_positions`
and says why in its docstring.

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
| `execute_pm_node` ordering | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/dependencies.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `EXEC-IDN-01`; `EXEC-IDN-03`; `EXEC-NEV-01`; `EXEC-FAIL-01`; `EXEC-DEP-03`; `EXEC-DEP-04` | Yes. `EXEC-NEV-01` (*never decides what to trade*) is why the cancel is keyed off the **PM's approved sells** and never off execution's own view of the book — execution acts on the intent it was given, it does not choose which positions to free. |
| The cancellation fact | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md` | `EXEC-IDN-03`; `EXEC-OBS-03`; `EXEC-IDM-01`; `EXEC-IDM-02` | Yes, decisively — see below. |

**🚨 `EXEC-OBS-03` already decides item 2; it was never mine to judge.** The spec framed
"what happens when the exit fails after its stop is cancelled" as the sprint's judgement call. The
law had already settled it:

> *A held position that ends a run with **no live broker stop** is surfaced as an
> `UnprotectedPosition` fault and retried on the next run — a refusal is never recorded once and then
> forgotten.*

So item 2 is implementation of an existing clause, not a decision. The fault type, the loudness, and
the retry-next-run expectation are all prescribed. This is the law doing exactly what the law-first
gate exists for.

**Contradictions found between a law and this spec:** None. The spec's item-2 framing was
*weaker* than the law, and was tightened to match it.

**Laws found silent where a decision was needed:** None new. One **pre-existing** limitation found
in the code rather than the law, filed as `DRIFT-038`: `_place_stop` refuses to place when any
`BrokerStopOrder` fact exists at the key (`stop:{position_ref}:{ticker}`), including a **cancelled**
one, and records *"existing inactive BrokerStopOrder fact blocks retry"*. So `EXEC-OBS-03`'s
"retried on the next run" cannot currently succeed for a position whose stop was cancelled while it
is still held — the fault repeats truthfully, but the retry never lands. **Out of scope here**
(it needs an attempt-chained stop key, like `Fill` already has); this sprint makes the fault
accurate and attributable rather than pretending the retry works.

**Clauses that were ⬜ and are now proven:** `EXEC-OBS-03` (⬜ → 🟩, A3/A5) and
`EXEC-DEP-04` (⬜ → 🟩, A1/A5 — broker cancel plus the append-write it was waiting on).

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_exit_cancels_its_stop_before_submitting` | `agents/execution/tests/test_exit_stops.py` | PASS | `EXEC-DEP-04`; `EXEC-IDN-03` |
| A2 | `test_surviving_position_keeps_its_stop` | `agents/execution/tests/test_exit_stop_cancel.py` | PASS | `EXEC-IDN-03`; ADR-0015 s3 |
| A3 | `test_rejected_exit_leaves_position_loudly_unprotected` | `agents/execution/tests/test_exit_stops.py` | PASS | `EXEC-OBS-03` |
| A4 | `test_cancelling_an_exit_stop_is_idempotent` | `agents/execution/tests/test_exit_stop_cancel.py` | PASS | `EXEC-IDM-01` |
| A5 | `test_cancellation_is_an_appended_marker_not_a_deletion` | `agents/execution/tests/test_exit_stop_cancel.py` | PASS | `EXEC-OBS-03`; `EXEC-IDN-03` |
| A6 | `test_a_buy_cancels_no_stop` | `agents/execution/tests/test_exit_stop_cancel.py` | PASS | `EXEC-NEV-01` |

**Test added beyond the plan:** `test_unprotected_report_ignores_tickers_that_were_never_freed` — a
rejected sell for a ticker that was never freed must raise nothing, so the fault cannot drift into a
generic “rejected sell” alarm.

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):** Worktree `trading-agents-s163`, branch
`sprint-163-an-exit-cancels-its-own-stop` off `df04cfc`. **`.env` absent** — no live broker or graph
proof was attempted here; the production evidence for the defect was gathered read-only from the
main checkout before the branch existed.

**Item 2 decision — post-cancel exit failure, and why:** Prescribed by `EXEC-OBS-03`, not chosen:
fault with `UnprotectedPosition` and let the next run retry. Rejected alternative: re-place the stop
inline after a rejected exit — it cannot work today (`DRIFT-038`) and would have hidden the
condition the law wants surfaced.

**Module line counts after any split:** `poll.py` **191 → 188** (the call site shrank). New:
`exit_stops.py` **108**. The test module reached **257** and **failed the 200-line hard block**;
split into `test_exit_stops.py` **54** (through the real run path), `test_exit_stop_cancel.py`
**133** (unit), `exit_stop_helpers.py` **96** (shared fixtures) — split, not golfed.

**Proven (LAW-02):** 7 tests pass; `uv run mypy agents/execution` clean across 82 source files.

**Planted violations watched fail:** `freed = frozenset()` in place of the cancel → **2 failed, 5
passed** (A1 ordering, A3 unprotected fault). Restored → 7 passed. Separately, the A1 false pass
described under item 4 was found and fixed before the gate.

**Final full gate:** `make ci` redirected to a file, **`MAKE_CI_EXIT=0`**:

```text
Contracts: 4 kept, 0 broken.
TOTAL                                                14188      0   3012      0  100.00%
================= 2158 passed, 6 skipped in 132.91s (0:02:12) =================
No known vulnerabilities found
Detect secrets...........................................................Passed
Detect secrets...........................................................Passed
```

Three earlier gate runs failed and are recorded rather than hidden: `MAKE_CI_EXIT=2` on a mypy
`arg-type` error (a test helper typed `-> object`), then on `ruff format`, then on the 200-line
hard block. The gate did its job three times.

**Remote gate / gate-ran / merge:** _pending operator go — branch committed locally, not pushed,
not merged._

**Not met / verified failing:** No live-environment proof (no `.env` in the worktree): that the
cancel actually frees `qty_available` at Alpaca is **still inferred, not observed**. It becomes
observable only when the flatten runs — that is the chore's functionality check, not this sprint's.
`DRIFT-038` is filed, not fixed: `_place_stop` refuses to place while any `BrokerStopOrder` fact
exists at the key, including a cancelled one, so `EXEC-OBS-03`’s “retried on the next run” cannot
currently land for a still-held position whose stop was cancelled. The fault repeats truthfully;
the retry does not. Needs an attempt-chained stop key, as `Fill` already has.

---

## Return notes

- The law-first gate earned its keep twice. `EXEC-OBS-03` **already decided** the item the spec
  framed as this sprint's judgement call, and `EXEC-NEV-01` is why the freed set is derived from the
  PM's approved intents rather than from execution's own view of the book.
- The sprint-defining test passed for the wrong reason on the first attempt. A fixture that assumed
  an identifier instead of reading it back routed the whole scenario through a **pre-existing** code
  path. Assert the ordering, and read identifiers back — do not construct them.
- `DRIFT-038` bounds the fix honestly: this sprint makes the unprotected condition **accurate and
  attributable**; it does not make the retry land.
- Scope held: no stop-placement policy change, no ADR reversal, no flatten, no parameter move.
