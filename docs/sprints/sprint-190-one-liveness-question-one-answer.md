<!-- Agent: planning | Role: sprint handover — one liveness predicate for execution's broker facts -->
# Sprint 190 — Every broker fact answers "is this still live?" the same way

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-190-one-liveness-question-one-answer`
**Status:** BUILT
**Version:** `0.94.02`
**Effort:** M
**Decisions:** [DL-139](../design-log.md) (the 2026-08-31 re-measurement + *predicate, not property*) · DL-129 (`Fill.status` is immutable) · DL-130 (the sweep compares a type against a lifecycle) · DL-131 (a fired stop is never reconciled) · [DRIFT-055](../laws/drift-register.md) + [DRIFT-029](../laws/drift-register.md) · closes work-queue items **32**, **20** and **12**'s Fill half

> **Why this bump kind.** No new capability. `EXEC-OBS-03` already promises that "the broker remains
> truth for liveness" for the protective-stop lifecycle; the code asks the graph instead, and asks it
> three different ways. This is the clause becoming true — a **PATCH**.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/execution/laws/laws.md` | Execution's **locked constitution** (LOCKED v1.3) | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/execution/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`IDN`**, **`STA`**, **`OBS`**, **`OUT`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read `test-plan.md` alongside `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes, and the answer is pre-decided here so it cannot be skipped:** this sprint adds
`contracts/broker_lifecycle.py` and edits `contracts/broker_stops.py`. It therefore owes the full
cycle **in this unit of work**:

- a new clause in `agents/execution/laws/laws.md` (see *Law cycle owed*, below), version → **v1.4**,
  Changelog line;
- a `test-plan.md` row per new clause, plus **new rows under `EXEC-OBS-03`** for the limb that was
  never tested;
- the clause ID cited in each test docstring;
- the rollup updated in **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` — 🪤 **derived,
  not declared**: let `make ci` compute it;
- the `drift-register.md` row for `EXEC-OBS-03` moved to CORRECTED (see below).

#### Law cycle owed — the specifics

🚨 **`EXEC-OBS-03` is 🟩 green on five tests and one of its three limbs has never been exercised.**
The clause reads: *"placement is an immutable `BrokerStopOrder` fact, cancellation is a `cancelled_at`
marker (never a deletion), **and the broker remains truth for liveness**"*. The five cited tests prove
placement idempotency, cancellation-as-marker, unprotected-position faults and replacement. **None of
them asks whether a stop the broker has already filled still reads live.** In production it does.
That is item 30's class (a clause proven against a proxy), found in a second agent.

- **`DRIFT-055` is already filed** (2026-08-31, with this spec): `EXEC-OBS-03` green on partial
  coverage; the broker-truth-for-liveness limb unproven and false in production. Move it to
  **CORRECTED** when the limb has a test — do not open a second row.
- 🎯 **`DRIFT-029` already names this sprint's design as the end-state**: *"the right end-state is a
  current-status read model derived from `BrokerOrderStatus` facts rather than a mutable Fill
  status."* Read that row before designing — it also records that `partial` still refreshes
  indefinitely, and why that was left open.
- **Add `EXEC-OBS-05`** (IDs are append-only — do not renumber): *"Liveness of an execution broker
  fact is asked in exactly one place. A `BrokerStopOrder` whose order has reached a terminal broker
  state is not live regardless of `cancelled_at`; a resting-stop `Fill` is not an open order; and the
  stale-order sweep asks the same liveness question of the broker that it asks of the graph."*
- Do **not** rewrite `EXEC-OBS-03`. It is right; the code was wrong.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `contracts/broker_lifecycle.py` *(new)* | `agents/execution/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `EXEC-IDN-03` (execution exclusively owns `BrokerStopOrder`, `BrokerOrderStatus`); `EXEC-OBS-03` |
| `contracts/broker_stops.py` | same | `EXEC-OBS-03` — `cancelled_at` is a marker, never a deletion. **Keep that true**: this sprint adds a *reader*, it must not stop writing or start deleting |
| `agents/execution/drop_sweep.py` | same | `EXEC-OUT-07` (`dropped` is an outcome distinct from `rejected`/`skipped`) |
| `agents/execution/reconciliation_store.py` | same | `EXEC-STA-05` — refresh terminates on a terminal `broker_status`; **`partial` still refreshes** |
| `agents/reporter/domain/trade_outcomes.py` | `agents/reporter/laws/laws.md` | reporter reads execution's facts; changing what "terminal" means changes reported PnL |

⚠️ **The one invariant this sprint must not break: `partial` is not terminal.** `EXEC-STA-05` says a
partial fill still refreshes, and S176 exists because a partial could never upgrade. If a unified
terminal set swallows `partial`, you have re-broken S176. Stop and report instead.

---

## Goal

At merge, exactly one module answers "is this execution broker fact still live?", and every caller
asks it there. A `BrokerStopOrder` whose order has reached a terminal broker state is **not** returned
by `active_broker_stop_orders`, whatever `cancelled_at` says. A resting-stop `Fill` is **not** counted
as an open order. The stale-order sweep asks the broker for *liveness*, not for *order type*, so a
dead stop stops mismatching forever.

## Why (context)

Three defects were found in one sitting on 2026-08-24 and recorded as DL-129, DL-130 and DL-131. They
look like three bugs and are one: **execution's graph facts each denormalise lifecycle differently,
and only `Position` has a predicate that hides it** (`contracts/positions.py:126`,
`is_active_position_node`). Patching them separately re-creates the shape a fourth time.

The cost so far is **two retracted work-queue claims** — item 12 read `Fill.status` as a 202-item
backlog when 27 were open, and item 20 read 228 faults as a growing divergence when the broker agreed
with the graph about all of them. Both retractions have the same root: the reader had to know which
of five properties carries the truth, and guessed.

### Measured, 2026-08-31 — read these before designing

All figures below are **read-only `SELECT`s against the live Neon spine** from the main worktree with
`.env` present. Nothing was written. The fleet was not touched.

| Claim | Value | How it was measured |
| --- | --- | --- |
| `BrokerStopOrder` nodes | **46** | *[measured 2026-08-31]* `count(*) WHERE label='BrokerStopOrder'` |
| …reading live today (`cancelled_at IS NULL`) | **29** | same, `props->>'cancelled_at' IS NULL` |
| Active `Position`s by `is_active_position_node` | **28** | status open, no `broker_absent`, no `broker_superseded_by` |
| **Graph-active stops whose own `Fill` is terminal** | **1** — `stop:87403939105c0a24:PYPL` | join `BrokerStopOrder` to `Fill` on identical key |
| **Every `BrokerStopOrder` has a `Fill` at the identical key** | **46 / 46, 0 missing** | anti-join; this is what makes the fix a predicate, not a new property |
| Stops carrying `cancelled_at` whose `Fill` says `filled` | **7** | the fired-then-mislabelled set |
| …in which the fill was recorded **before** the cancel | **7 of 7** | `broker_status_refreshed_at` vs `cancelled_at`, per node |
| …lag, fill → "cancelled" | **1–3 days** | e.g. AVGO filled `08-14T22:30`, marked cancelled `08-17T22:52` |
| `BrokerStopIdentityMismatch` faults | **304** *(was 228 on 08-24)* | `count(*)` by `error_type` |
| …distinct order keys behind them | **17** *(was 13 on 08-24)* | regex over `props->>'message'` — **the fault carries no context** |
| …faults carrying a non-empty `context` | **0 of 304** | `props->'context'` |
| …all in the same direction | `broker_stop=True graph_stop=False`, 17/17 | same parse |
| `Fill` nodes | **259** | `count(*)` |
| …`status='pending'` | **248** | the immutable submit-time field (DL-129) |
| …genuinely open (pending + non-terminal `broker_status`) | **29** | DL-129's definition, re-measured |
| …**of which are resting-stop Fills** | **28** | `key LIKE 'stop:%'`, and `props ? 'stop_order_key'` agrees |
| …of which are real orders | **1** (an MSFT buy from `sched-2026-08-28`) | the remainder |
| `Fill` lifecycle markers in use | `status` 259 · `broker_status` 230 · `broker_status_refreshed_at` 219 · `submitted_at` 163 · `drop_reason`/`dropped_at` 125 · `pnl_unresolved_at` 1 | `props ? '<name>'` per property |
| Distinct "terminal" vocabularies in the code | **6 sets in 5 modules** | see the table below |
| `Fault` nodes total | **6,393**, of which **5,762** are one `execution/poll::position_sync` `ValueError` burst on 2026-07-30/31 | grouped by `error_type`, `source_module` |

**🚨 Two carried claims are corrected by this measurement — do not design against the old ones.**

1. **DL-130 said "13 objects, not a growing fault".** It is **17** objects seven days later — AVGO,
   AMZN, MSFT, WFC, INTC, AMD and XOM joined the original ten. The population grows by one per stop
   that dies. The *repetition* count is what tracks sweeps; the *object* count tracks stop-outs.
2. **DL-129's leftover — "24 open Fills carry no `submitted_at`" — is not a mystery.** 28 of the 29
   open Fills are **resting stops**: `_write_stop_fill` never writes `submitted_at`, and a GTC stop
   that has not fired is `pending` by design, forever. The Fill-hygiene item is a **naming** problem,
   not a backlog. That is why `is_open_fill_node` alone is not enough (see decision 3).

**The six vocabularies, measured by reading the code 2026-08-31:**

| Where | Set | What it calls terminal |
| --- | --- | --- |
| `agents/execution/reconciliation_store.py:30` | `_TERMINAL_BROKER_STATUSES` | `{filled, rejected}` |
| `agents/execution/drop_sweep.py:29` | `_DROP_TERMINAL_REASONS` | `{canceled, cancelled, expired}` |
| `agents/execution/run.py:32` | `COMPLETED_EXIT_STATUSES` | `{filled, partial, partially_filled}` |
| `agents/execution/filled_entry_stops.py:25` | `_FILLED_STATUSES` | `{filled}` |
| `agents/reporter/domain/trade_outcomes.py:45` | *inline literal* | `{canceled, cancelled, expired}` |
| `agents/execution/drop_sweep.py:26` | `_STOP_TYPES` | `{stop, stop_limit}` — **a type set standing in for liveness** |

🪤 **`canceled` never appears in `broker_status`** *[measured: the only values present are `rejected`
(140), `filled` (79) and unset (29)]* — because `EXEC-OUT-07` deliberately routes a drop to
`drop_reason`/`dropped_at` instead. So `_TERMINAL_BROKER_STATUSES` missing `canceled` has never bitten.
**Do not "fix" it by adding `canceled` to that set** without checking `EXEC-OUT-07` first.

### The live specimen — read this before you write the fixture

```text
BrokerStopOrder stop:87403939105c0a24:PYPL
  broker_order_id a812d605-5419-4482-b704-d647a1bf07c9
  placed_at       2026-08-11T22:41:02+00:00
  cancelled_at    (absent)          <- active_broker_stop_orders() returns it

Fill            stop:87403939105c0a24:PYPL      <- same key, same broker_order_id
  status                     pending            <- immutable submit-time fact (DL-129)
  broker_status              filled             <- the graph already knows
  broker_status_refreshed_at 2026-08-28T22:30:45+00:00
  realized_pnl_cents         -9758

Position broker:PYPL:175:5665 / broker:PYPL:17:5894
  status "open", broker_absent "true"           <- is_active_position_node() -> False, correctly
```

**The information was never missing.** The same graph, at the same key, has said "filled" for three
days. Only the predicate is absent. 🪤 **This is why the fix must not be a new `filled_at` property:**
R007 §5 — a derived row is indistinguishable from an observed one at read time.

⏰ **This specimen has a shelf life, and that changes nothing you build.** `sched-2026-08-31`
(22:30 UTC) is the first run since PYPL filled on Friday — the cron is `30 22 * * 1-5`, so 08-29 and
08-30 were weekend. That run will find PYPL's position inactive and write `cancelled_at`, moving it
from the "graph-active" bucket into the "fired but labelled cancelled" bucket (7 → 8), i.e. **28
active / 0 contradictions / 8 mislabelled**.

🚨 **Build the fixture from the shapes printed above, in-test — never from the spine.** A worktree has
no `.env`, and you are told not to query the spine at all; both bucket states are given here, and the
*defect* is identical in either. The live numbers are **context for the reviewer**, not fixture
inputs. If the counts matter to a claim you want to make at handback, say which bucket you assumed
and let the merge re-measure it.

---

## Scope — and what is deliberately NOT here

1. **The failing test first.** A `BrokerStopOrder` with `cancelled_at` absent whose sibling `Fill`
   reads `broker_status="filled"` must **not** be returned by `active_broker_stop_orders`. Assert on
   the returned tuple, not on a count.
2. **One module: `contracts/broker_lifecycle.py`.** It owns the terminal vocabulary and every
   liveness predicate for execution's broker facts. Nothing else defines a terminal-status set.
3. **`contracts/broker_stops.py` delegates.** `active_broker_stop_orders` keeps its name and
   signature — it has five call sites — and asks the new predicate. Callers do not change.
4. **`drop_sweep._is_stop_order` asks liveness on both sides.** `broker_stop` becomes *"is this a
   live stop order"* — type **and** non-terminal broker status — so a dead stop matches a dead graph
   fact and raises nothing. (DL-130's decision, unchanged.)
5. **Fill predicates that survive contact with the data.** `is_open_order_fill` (pending, non-terminal
   `broker_status`, not dropped, **and not a resting-stop fill**) and `is_resting_stop_fill`. Item 12
   was misread twice because these two populations share one word.
6. **The mismatch fault carries context.** `idempotency_key`, `broker_order_id`, `order_type`,
   `broker_status`, `broker_stop`, `graph_stop`. 0 of 304 have any today; DL-130's own analysis needed
   a regex over free text.
7. **The three merged work-queue rows close** — 32, 20, and item 12's Fill half.

### Out of scope (do NOT build this sprint)

- **Backfilling history.** The 304 faults, the 17 dead keys and the 7 mislabelled `cancelled_at`
  stops stay as they are. DL-130 already decided *fix the predicate, not the data*. Prove that **no
  new** mismatch is raised; do not write `FaultResolution`s.
- **A `resolved_reason` on `BrokerStopOrder`** distinguishing *cancelled by us* from *stopped out*.
  It is the natural next question and it is a **separate** decision with a graph-write in it. Name it
  in Return notes; do not build it.
- **`pg_teardown`'s delete path** — item 12's other half. Untouched.
- **The 5,762 `ValueError` faults** from 2026-07-30. One dead incident, one month old; it distorts
  every fault-population percentage but changes nothing here.
- **Item 27's live proof.** Different item, different evidence.
- **No ADR reversal.** ADR-0015 §3 stands.

### The road not taken (LAW-06)

- **Add `filled_at` / `resolved_at` to `BrokerStopOrder` and write it when the stop fires.** Rejected:
  the graph *already holds* the fact at the identical key (**46/46, measured**), so this denormalises
  a fact for the third time — the exact defect being fixed. R007 §5: a derived row is
  indistinguishable from an observed one. It also needs a new writer in the run path, which is more
  blast radius for less truth.
- **Suppress or resolve the 304 faults.** Rejected in DL-130 and still rejected: the detector would
  keep manufacturing the class for every stop that dies. Suppressing a predicate that cannot be right
  is how a warning channel dies.
- **Narrow `_list_orders`' `status=all&limit=500` window.** Rejected: it lowers the rate and hides the
  defect. 🪤 Worth knowing separately — at 242 orders the 500 cap is not binding **yet**, and nothing
  watches for the day it is.
- **Three separate patches, one per DL row.** Rejected: DL-131's finding *is* that they are one shape.
  Three patches would leave the fourth instance free to appear.
- **Put the predicates in `contracts/positions.py` beside `is_active_position_node`.** Rejected: that
  file is **187 lines** and the position read model is not the broker read model.

---

## The design decisions this sprint has to make

**`DL-139` already records decision 1 and the rejected alternatives** (written 2026-08-31 with this
spec). **Append decisions 2–4 to it as an amendment before implementing (LAW-06)** — do not open a
new row for the same sprint.

1. **Liveness is derived from the sibling `Fill`, not written onto the stop.** The join is by
   identical node key, falling back to `broker_order_id` — the pairing `drop_sweep._tracked_as_stop`
   already uses. Decide and record what happens when the sibling Fill is missing: **measured 0/46
   today**, so the honest default is *treat the stop as live and let the existing
   `UnprotectedPosition` path speak*, never *silently dead*.
2. **One terminal vocabulary, and `partial` is not in it.** Reconcile the six sets above into named
   frozensets in the new module. 🪤 `EXEC-STA-05` requires `partial` to keep refreshing and S176
   exists because a partial could never upgrade — if a single set cannot serve all six call sites,
   **say so and keep two named sets rather than forcing one**. Do not quietly widen `run.py`'s
   `COMPLETED_EXIT_STATUSES`, which deliberately includes `partial`.
3. **A resting stop is not an open order.** `is_open_order_fill` excludes stop fills; **28 of the 29
   "open" Fills are stops**, so this single decision is what makes the number readable. Decide the
   discriminator: `props ? 'stop_order_key'` (**49 Fills**, semantic) beats `key LIKE 'stop:%'`
   (**49 Fills**, stringly-typed) — same population today, and the first survives a key-format change.
4. **Where the module lives and what it may import.** `contracts/` may not import `agents/`
   (import-linter). The predicate takes a `GraphStore` and a `Node`, exactly as
   `contracts/positions.py` does.

🪤 **`DL-139` is taken by this spec's own measurement entry — amend it, do not open `DL-140`.** The
log has historic duplicates and a branch cut before another DL lands collides even when the number
was free at branch time (S183 hit this), so re-check at merge either way.

---

## Blast radius — measured 2026-08-31

| What | Detail |
| --- | --- |
| Files changed | `contracts/broker_lifecycle.py` *(new)* · `contracts/broker_stops.py` **100** · `agents/execution/drop_sweep.py` **167** · `agents/execution/drop_sweep_records.py` **163** · `agents/execution/reconciliation_store.py` **161** · possibly `agents/reporter/domain/trade_outcomes.py` **52** |
| 🚨 Modules with no headroom | `agents/execution/broker_stop_actions.py` **191 / 200** and `agents/execution/broker_stops.py` **187 / 200**. **Do not add a line to either.** If the change wants to live there, it belongs in the new module |
| Agents affected | execution (owner), reporter (reader). ✅ Neither imports the other — both reach the facts through `contracts/` |
| Contract change? | **Yes** — new `contracts/` module + edit. The law cycle above is **mandatory** |
| Graph vocabulary change? | **No.** The fix writes no new property. 🪤 Verified: `BrokerStopOrder` declares no property allowlist in `orchestration/packs/trading_graph_vocabulary.json`, but **`Fill` does** — if you end up writing any new `Fill` property, the pack changes and the deploy becomes a full `up`. Check before you write |
| New env keys / tunables | none |
| Deploy implication | **Image-only retag would suffice for this sprint.** 🪤 But the fleet is owed a full `up` regardless — S189 added `stop_reason` to `LLMCall`'s property list, and a retag against a stale vocabulary pack hits the fail-closed write guard mid-cascade (S148 stall, DL-85) |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Append decisions 2–4 to `DL-139`** in `docs/design-log.md` (decision 1 is already recorded).
3. **Plant the failing tests first** and watch them fail. Paste the red output.
4. **Implement** `contracts/broker_lifecycle.py`; make `contracts/broker_stops.py` delegate.
5. **Repoint** `drop_sweep`, `reconciliation_store` and the reporter's inline literal.
6. **Law cycle** — `EXEC-OBS-05`, test-plan rows (including the new `EXEC-OBS-03` rows), docstring
   citations, both rollups, `DRIFT-055` → CORRECTED.
7. **Prove the guards can fail (DL-70)** — break each predicate in turn, watch its guard go red,
   restore. State it per guard.
8. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
9. Fill the handback sections at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A stop whose sibling `Fill` is `filled` is not live | `BrokerStopOrder` with no `cancelled_at` + `Fill` at the same key, `broker_status="filled"` — the PYPL shape | `active_broker_stop_orders` returns `()`; `active_broker_stop_refs` omits the ref |
| A2 | A cancelled stop is still not live | `cancelled_at` set, `Fill` non-terminal | Unchanged behaviour — `cancelled_at` keeps working, the marker is never deleted (`EXEC-OBS-03`) |
| A3 | 🪤 A resting stop **is** live | no `cancelled_at`, `Fill` `pending`/unset — the 28-node majority | Still returned. **The negative that stops this sprint from unprotecting the fleet** |
| A4 | The sweep raises nothing for a dead stop | broker order type `stop`, broker status `canceled`, graph fact cancelled | No `BrokerStopIdentityMismatch`; the order stays exempt from cancellation |
| A5 | The sweep still raises for a real mismatch | live broker stop, no graph fact | Fault raised **and its `context` carries `idempotency_key`, `broker_order_id`, `order_type`, `broker_status`** |
| A6 | A resting-stop Fill is not an open order | the A3 fixture | `is_open_order_fill` → `False`; `is_resting_stop_fill` → `True` |
| A7 | A genuinely open order is | pending buy, no `broker_status` | `is_open_order_fill` → `True` |
| A8 | 🪤 `partial` still refreshes | `broker_status="partial"` | `refresh_pending_fills` still reads it (`EXEC-STA-05`, S176). **If this goes green by accident, you have re-broken S176** |
| A9 | One vocabulary | — | Static test: no module outside `contracts/broker_lifecycle.py` defines a terminal-status frozenset. Shaped like `tests/test_deploy_script_invariants.py`, which pins text invariants |

---

## Success factors

- [ ] `active_broker_stop_orders` excludes a stop whose order reached a terminal broker state, with
      `cancelled_at` absent — asserted on the returned tuple.
- [ ] The 28 genuinely resting stops are still returned (A3). **No position loses protection.**
- [ ] `is_open_order_fill` returns `False` for all 28 resting-stop Fills and `True` for the open order.
- [ ] `_is_stop_order` asks liveness on both sides; a dead stop raises no fault.
- [ ] `BrokerStopIdentityMismatch` carries structured context.
- [ ] Exactly one module defines a terminal-status set (A9).
- [ ] `partial` still refreshes (A8) — `EXEC-STA-05` and S176 intact.
- [ ] Design decisions recorded as `DL-139` with rejected alternatives.
- [ ] Law cycle done: `EXEC-OBS-05`, laws **v1.4**, test-plan rows, both rollups, `DRIFT-055`
      moved to CORRECTED.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines; `broker_stop_actions.py` and `broker_stops.py` **not grown**.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The count going down is not the proof.** Fewer active stops is also what a predicate that is too
aggressive produces, and that one silently unprotects positions. A3 is the test that separates them —
write it before A1 passes.

🪤 **`partial` is not terminal.** Six sets disagree about terminal; exactly one of them
(`run.py:32`) deliberately includes `partial`. A single unified set is the obvious refactor and it is
how S176 gets re-broken.

🪤 **The specimen moves overnight, so do not hard-code a count.** `sched-2026-08-31` writes
`cancelled_at` on PYPL, taking the buckets from 29-active/1-contradiction to 28-active/0. **Both
shapes are in the spec** — assert on the *behaviour* of a fixture you built, never on a population
size read from the live graph.

🪤 **`cancelled_at` must keep being written.** This sprint adds a reader. If `cancel_stop` stops
writing the marker, `EXEC-OBS-03`'s "cancellation is a marker, never a deletion" breaks and the audit
trail loses the one lifecycle fact it does have.

🪤 **The fault count will not fall to zero.** 304 historical records stay (out of scope). The proof
is that **no new one is raised**, measured on the next run — not that the total dropped.

🪤 **`contracts/` cannot import `agents/`.** The predicate needs the broker's status vocabulary, which
today lives in `agents/execution/`. Move the *vocabulary* down into `contracts/`; do not import up.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `contracts/broker_stops.py` **100**, `contracts/positions.py` **187**,
  `agents/execution/drop_sweep.py` **167**, `agents/execution/drop_sweep_records.py` **163**,
  `agents/execution/reconciliation_store.py` **161**, `agents/execution/broker_stops.py` **187**,
  `agents/execution/broker_stop_actions.py` **191**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. A status set is neither a tunable nor
  a mode selector; it is a vocabulary. Do not register one.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- PATCH bump, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**, so **every fixture in this sprint
  must be built in-test from the shapes above**, not read from the spine. State which tree you ran in.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA
   from the working directory and ignores a `SHA=` argument. **Check the printed SHA against
   `git rev-parse HEAD`.**
2. Merge to `main` locally and push. 🪤 A `git merge` from the branch's own worktree says *"Already up
   to date"* and merges nothing.
3. **Post-merge CodeQL.** `codeql.yml` runs only on `main`. 🪤 And a docs commit pushed on top
   **cancels** the merge commit's own CodeQL run (`concurrency: cancel-in-progress`, work-queue item
   31) — check `HEAD`'s run completed `success` before pushing anything else.
4. **Deploy:** a retag would carry this sprint, but the fleet is owed a full `up` for S189's
   vocabulary move. Ship it with that one.
5. **The live proof.** On the first run after deploy: **zero new `BrokerStopIdentityMismatch` faults**,
   and `active_broker_stop_orders` equal to the broker's live stop count. Record it in
   `docs/laws/functionality-checks.md`.

---

## Handover — paste this to Codex

```text
Sprint 190 — every broker fact answers "is this still live?" the same way.
Branch: sprint-190-one-liveness-question-one-answer, cut from main. Never commit to main.
Spec: docs/sprints/sprint-190-one-liveness-question-one-answer.md — read it whole first.

MUST RULE, before you open an editor:
  Read agents/execution/laws/laws.md (LOCKED v1.3) and its test-plan.md, whole, plus
  docs/laws/conventions.md and docs/laws/drift-register.md. Write the "Law reading record"
  section of the spec BEFORE your first code change. laws.md is READ-ONLY except for the
  law cycle this sprint owes (below). If a law contradicts the spec, STOP and report — the
  law is more likely right.

THE PROBLEM. Execution's graph facts each denormalise lifecycle differently and only Position
has a predicate hiding it (contracts/positions.py:126). Three defects, one shape:
  - a BrokerStopOrder is "active" iff cancelled_at is None, so a stop that FIRED stays active
    forever (DL-131);
  - the stale-order sweep compares order TYPE against graph LIFECYCLE, so every dead stop
    mismatches forever — 304 faults, 17 distinct keys (DL-130);
  - Fill.status is an immutable submit-time fact and has no predicate, so audits misread it
    twice (DL-129).

MEASURED 2026-08-31 on the live spine (read-only SELECTs; do NOT re-run against the fleet):
  46 BrokerStopOrder nodes, 29 reading live, 28 active Positions.
  EVERY BrokerStopOrder has a Fill at the IDENTICAL key (46/46) — this is why the fix is a
  predicate, not a new property. The graph already holds the answer.
  1 live contradiction today: stop:87403939105c0a24:PYPL has no cancelled_at while its own
  Fill reads broker_status=filled, refreshed 2026-08-28, realized_pnl_cents=-9758.
  7 more stops carry cancelled_at while their Fill says filled — in all 7 the fill was
  recorded 1-3 DAYS BEFORE the cancel, so this is not a race: a fired stop is eventually
  mislabelled "cancelled by us".
  29 "open" Fills — 28 of them are RESTING STOPS (pending by design, forever), 1 is a real
  order. That is why "open fill" needs two predicates, not one.
  0 of 304 mismatch faults carry any context; the key is only inside the message string.

WHAT TO BUILD:
  1. NEW contracts/broker_lifecycle.py — the ONLY place that defines a terminal-status
     vocabulary and every liveness predicate for execution's broker facts.
  2. contracts/broker_stops.py delegates. active_broker_stop_orders keeps its name and
     signature (5 call sites) and excludes a stop whose sibling Fill reached a terminal
     broker state, whatever cancelled_at says. Join by identical key, fall back to
     broker_order_id (drop_sweep._tracked_as_stop already pairs them that way).
     If the sibling Fill is missing (0/46 today), treat the stop as LIVE — never silently dead.
  3. drop_sweep._is_stop_order: the broker side asks "is this a LIVE stop", i.e. type AND
     non-terminal status. Today it asks type only (drop_sweep.py:26,130).
  4. Fill predicates: is_open_order_fill (pending, non-terminal broker_status, not dropped,
     NOT a resting-stop fill) and is_resting_stop_fill. Discriminate on the presence of
     'stop_order_key', not on the key string.
  5. record_stop_mismatch: add context {idempotency_key, broker_order_id, order_type,
     broker_status, broker_stop, graph_stop}.

ORDER OF WORK: failing tests FIRST, paste the red output into the spec. Then implement.
Then break each predicate in turn, watch its guard go red, restore it, and say so per guard.

DO NOT:
  - Do not add filled_at/resolved_at (or any property) to BrokerStopOrder. The fact already
    exists on the sibling Fill; writing it again is the third denormalisation and R007 §5
    says a derived row is indistinguishable from an observed one.
  - Do not treat "partial" as terminal. EXEC-STA-05 requires partial to keep refreshing and
    S176 exists because a partial could never upgrade. run.py:32's COMPLETED_EXIT_STATUSES
    deliberately includes partial — leave it. If one set cannot serve every call site, keep
    two NAMED sets and say why.
  - Do not add "canceled" to reconciliation_store's terminal set without reading EXEC-OUT-07
    first — drops are routed to drop_reason on purpose, and no Fill has broker_status=canceled.
  - Do not backfill: leave the 304 faults, the 17 dead keys and the 7 mislabelled stops alone.
    Prove NO NEW mismatch is raised. Do not write FaultResolutions.
  - Do not add a line to agents/execution/broker_stop_actions.py (191/200) or
    agents/execution/broker_stops.py (187/200). Put it in the new module.
  - Do not import agents/ from contracts/ — import-linter will fail the gate.
  - Do not write a new Fill property. Fill has a property allowlist in
    orchestration/packs/trading_graph_vocabulary.json; touching it turns the deploy into a
    full `up`. BrokerStopOrder has no allowlist, but you are not writing to it either.
  - Do not touch the fleet, do not deploy, do not run anything against the live spine. Every
    fixture is built IN-TEST from the shapes printed in the spec. The live counts there are
    context for the reviewer, not inputs -- and one of them (PYPL) moves after the 22:30 UTC
    run on 2026-08-31, which is exactly why you must not assert on a population size.

LAW CYCLE — OWED, because this sprint changes contracts/:
  - Add EXEC-OBS-05 (append-only IDs, do not renumber): liveness of an execution broker fact
    is asked in exactly one place; a stop whose order reached a terminal broker state is not
    live regardless of cancelled_at; a resting-stop Fill is not an open order; the sweep asks
    the broker the same liveness question it asks the graph.
  - Do NOT rewrite EXEC-OBS-03. It already says "the broker remains truth for liveness" and it
    is right — it is green on five tests, none of which exercise that limb. Add test-plan
    rows under EXEC-OBS-03 for the limb. DRIFT-055 is ALREADY FILED for this — move it to
    CORRECTED, do not open a second row. Read DRIFT-029 too: it already names this sprint's
    design as the end-state ("a current-status read model derived from BrokerOrderStatus
    facts rather than a mutable Fill status") and records why partial was left open.
  - laws.md -> v1.4 with a Changelog line; a test-plan row per clause; the clause ID cited in
    each test docstring; rollups in BOTH docs/laws/ledger.md and docs/laws/INDEX.md — let
    `make ci` compute the number, do not declare it.

TESTS THAT MUST EXIST (full table in the spec): the fired stop is not live; the cancelled stop
is still not live; A RESTING STOP IS STILL LIVE (this is the one that stops the sprint from
unprotecting the fleet — write it early); a dead stop raises no sweep fault; a real mismatch
still raises one AND carries context; a resting-stop Fill is not an open order; a real open
order is; partial still refreshes; and a static test that no module outside
contracts/broker_lifecycle.py defines a terminal-status frozenset (shape it like
tests/test_deploy_script_invariants.py).

PROOF REQUIRED AT HANDBACK: fill Test plan results, Closeout — evidence (red output first,
then green), Guards planted (per guard), Module line counts, and set Status: BUILT.
`make ci` must be run REDIRECTED TO A FILE (never piped — a pipe reports the pipe's exit
code), exit 0, 100.00 % coverage. Version: PATCH bump, uv.lock staged with it. Then push the
branch and run `make gate-ran` FROM THE WORKTREE whose HEAD is the commit being proven, and
paste its output with the full 40-char SHA. A handback with a placeholder left unfilled is
returned, not repaired.
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
| `contracts/broker_lifecycle.py` | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md` | `EXEC-IDN-03`, `EXEC-OBS-03`, `EXEC-STA-05`, `EXEC-OUT-07`, `EXEC-OBS-05` (to add) | Yes. `partial` must stay non-terminal, missing sibling Fill must default live, and the law amendment belongs in this sprint rather than another drift row. |
| `contracts/broker_stops.py` | Same execution law files and umbrella laws | `EXEC-OBS-03`, `EXEC-IDN-03`, `EXEC-OBS-05` (to add) | Yes. `cancelled_at` remains an audit marker; liveness becomes a reader predicate, not a stop property or deletion. |
| `agents/execution/drop_sweep.py` / `drop_sweep_records.py` | Same execution law files and umbrella laws | `EXEC-OUT-07`, `EXEC-OBS-03`, `EXEC-OBS-05` (to add) | Yes. Drops keep their own vocabulary; the mismatch detector must compare live-stop predicates on both sides and carry structured context. |
| `agents/execution/reconciliation_store.py` | Same execution law files and umbrella laws | `EXEC-STA-05`, `EXEC-OUT-07`, `EXEC-OBS-05` (to add) | Yes. Terminal refresh remains `filled`/`rejected`; `partial` is deliberately refreshable. |
| `agents/reporter/domain/trade_outcomes.py` | `agents/reporter/laws/laws.md`; execution law files and umbrella laws | `RPT-IDN-01`, `RPT-NEV-01`, `RPT-NEV-02`, `RPT-OBS-01`, plus execution lifecycle clauses read as upstream fact semantics | Yes. Reporter must remain a read-only projection and import contract vocabulary rather than define its own lifecycle literals. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes. It adds
`contracts/broker_lifecycle.py`, edits `contracts/broker_stops.py`, and adds execution guarantee
`EXEC-OBS-05` in this unit of work.

**Contradictions found between a law and this spec:** None. `EXEC-OBS-03` already says the broker
remains truth for liveness; the spec makes the code satisfy that limb instead of changing the clause.

**Laws found silent where a decision was needed:** The current law surface has no single clause
stating that execution broker-fact liveness is asked in one place, that resting-stop Fills are not
open orders, or that the stale-order sweep compares broker and graph liveness. `EXEC-OBS-05` will
cover that silence. `EXEC-STA-05` is also ⬜ in the read test-plan and must keep `partial`
non-terminal.

**Clauses that were ⬜ and are now proven:** `EXEC-OBS-03`'s broker-truth-for-liveness limb now has
direct tests; `EXEC-STA-05` now proves `filled`/`rejected` terminal refresh and the `partial` boundary;
new `EXEC-OBS-05` is added with tests for stop liveness, resting-stop fills, sweep liveness parity,
and structured mismatch evidence.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_filled_sibling_fill_makes_uncancelled_stop_inactive` | `tests/test_broker_stop_liveness.py` | Passed | `EXEC-OBS-03`, `EXEC-OBS-05` |
| A2 | `test_cancelled_stop_with_nonterminal_fill_stays_inactive` | `tests/test_broker_stop_liveness.py` | Passed | `EXEC-OBS-03`, `EXEC-OBS-05` |
| A3 | `test_resting_stop_fill_keeps_stop_live` | `tests/test_broker_stop_liveness.py` | Passed | `EXEC-OBS-03`, `EXEC-OBS-05` |
| A4 | `test_sweep_raises_no_mismatch_for_dead_stop_order` | `agents/execution/tests/test_drop_sweep_liveness.py` | Passed | `EXEC-OUT-07`, `EXEC-OBS-05` |
| A5 | `test_live_stop_mismatch_fault_carries_context` | `agents/execution/tests/test_drop_sweep_liveness.py` | Passed | `EXEC-OBS-05` |
| A6 | `test_resting_stop_fill_is_not_an_open_order_fill` | `tests/test_broker_fill_lifecycle.py` | Passed | `EXEC-OBS-05` |
| A7 | `test_pending_buy_fill_is_an_open_order_fill` | `tests/test_broker_fill_lifecycle.py` | Passed | `EXEC-OBS-05` |
| A8 | `test_partial_broker_status_still_refreshes_status_evidence` | `agents/execution/tests/test_fill_refresh_terminal.py` | Passed | `EXEC-STA-05` |
| A9 | `test_broker_lifecycle_vocabulary_lives_in_one_module` | `tests/test_broker_lifecycle_invariants.py` | Passed | `EXEC-OBS-05` |

**Tests added beyond the plan:** `test_missing_sibling_fill_keeps_stop_live`,
`test_broker_order_id_fallback_finds_terminal_sibling_fill`,
`test_terminal_and_dropped_fills_are_not_open_order_fills`,
`test_resolved_drop_statuses_are_not_live_broker_stops`,
`test_rejected_broker_status_is_not_reselected_for_order_status_writes`,
`test_partial_broker_status_can_finish_with_final_price`.

---

## Closeout — evidence

**Status:** BUILT locally; branch remote gate pending after commit and push.

**Tree the proofs ran in (and `.env` present?):**
`C:\Users\yury_\Downloads\project\trading-agents-sprint-190-one-liveness-question-one-answer`,
branch `sprint-190-one-liveness-question-one-answer`, base HEAD
`de72610ca62ce69b47c24a5d207e9b6ebee93750`; `.env` present: `False`.

**Result:** `contracts/broker_lifecycle.py` now owns execution broker lifecycle vocabularies and
predicates. `contracts/broker_stops.py` delegates active-stop reads to it; drop-sweep compares broker
and graph live-stop predicates; fill refresh keeps `partial` non-terminal; reporter resolved-unfilled
logic imports the contract vocabulary. `DRIFT-055` is corrected and execution law/test-plan rollups
are updated to v1.4.

**Files changed:** `contracts/broker_lifecycle.py`, `contracts/broker_stops.py`,
`agents/execution/drop_sweep.py`, `agents/execution/drop_sweep_records.py`,
`agents/execution/filled_entry_stops.py`, `agents/execution/reconciliation_store.py`,
`agents/execution/run.py`, `agents/execution/tests/test_drop_sweep_liveness.py`,
`agents/execution/tests/test_fill_refresh_terminal.py`, `agents/reporter/domain/trade_outcomes.py`,
`scripts/_audit_broker_graph_drops.py`, `tests/test_broker_stops_contract.py`,
`tests/test_broker_stop_liveness.py`, `tests/test_broker_fill_lifecycle.py`,
`tests/test_broker_lifecycle_invariants.py`, `agents/execution/laws/laws.md`,
`agents/execution/laws/test-plan.md`, `docs/design-log.md`, `docs/laws/INDEX.md`,
`docs/laws/drift-register.md`, `docs/laws/ledger.md`, `docs/STATE.md`, `pyproject.toml`,
`uv.lock`, and this sprint file.

**Design decisions:** `DL-139` amended before implementation with decisions 2-4: two named terminal
vocabularies instead of forcing `partial` into a single set; resting stops discriminate by semantic
`stop_order_key`; the lifecycle module lives in `contracts/` and imports no agents.

**Proof — the red run first:**

```text
uv run pytest tests\test_broker_stops_contract.py agents\execution\tests\test_drop_sweep.py tests\test_broker_lifecycle_invariants.py --no-cov

FAILED tests/test_broker_stops_contract.py::test_filled_sibling_fill_makes_uncancelled_stop_inactive
FAILED tests/test_broker_stops_contract.py::test_resting_stop_fill_is_not_an_open_order_fill
FAILED tests/test_broker_stops_contract.py::test_pending_buy_fill_is_an_open_order_fill
FAILED agents/execution/tests/test_drop_sweep.py::test_sweep_raises_no_mismatch_for_dead_stop_order
FAILED agents/execution/tests/test_drop_sweep.py::test_live_stop_mismatch_fault_carries_context
FAILED tests/test_broker_lifecycle_invariants.py::test_broker_lifecycle_vocabulary_lives_in_one_module
6 failed, 10 passed
```

**Proof — the green run:**

```text
uv run ruff format contracts/broker_lifecycle.py contracts/broker_stops.py agents/execution/drop_sweep.py agents/execution/drop_sweep_records.py agents/execution/filled_entry_stops.py agents/execution/reconciliation_store.py agents/execution/run.py agents/reporter/domain/trade_outcomes.py scripts/_audit_broker_graph_drops.py tests/test_broker_stops_contract.py tests/test_broker_stop_liveness.py tests/test_broker_fill_lifecycle.py tests/test_broker_lifecycle_invariants.py agents/execution/tests/test_drop_sweep.py agents/execution/tests/test_drop_sweep_liveness.py agents/execution/tests/test_fill_refresh_terminal.py agents/execution/tests/test_partial_fill_completion.py agents/execution/tests/test_filled_entry_stops.py agents/reporter/tests/test_trade_outcomes.py
19 files left unchanged

uv run ruff check contracts/broker_lifecycle.py contracts/broker_stops.py agents/execution/drop_sweep.py agents/execution/drop_sweep_records.py agents/execution/filled_entry_stops.py agents/execution/reconciliation_store.py agents/execution/run.py agents/reporter/domain/trade_outcomes.py scripts/_audit_broker_graph_drops.py tests/test_broker_stops_contract.py tests/test_broker_stop_liveness.py tests/test_broker_fill_lifecycle.py tests/test_broker_lifecycle_invariants.py agents/execution/tests/test_drop_sweep.py agents/execution/tests/test_drop_sweep_liveness.py agents/execution/tests/test_fill_refresh_terminal.py agents/execution/tests/test_partial_fill_completion.py agents/execution/tests/test_filled_entry_stops.py agents/reporter/tests/test_trade_outcomes.py
All checks passed!

uv run pytest tests\test_broker_stops_contract.py tests\test_broker_stop_liveness.py tests\test_broker_fill_lifecycle.py agents\execution\tests\test_drop_sweep.py agents\execution\tests\test_drop_sweep_liveness.py tests\test_broker_lifecycle_invariants.py agents\execution\tests\test_fill_refresh_terminal.py agents\execution\tests\test_partial_fill_completion.py agents\execution\tests\test_filled_entry_stops.py agents\reporter\tests\test_trade_outcomes.py --no-cov
46 passed in 1.59s

uv run pytest agents\execution\tests tests\test_broker_stops_contract.py tests\test_broker_stop_liveness.py tests\test_broker_fill_lifecycle.py tests\test_broker_lifecycle_invariants.py tests\test_audit_broker_graph.py agents\reporter\tests\test_trade_outcomes.py --no-cov
245 passed in 3.39s

uv run python scripts\check_law_coverage.py
[WARN] law coverage: 101 clause(s) have no test-plan row (assertion E warn-only)
[WARN] agents/execution/laws/test-plan.md: 13 missing row(s): EXEC-DEP-01, EXEC-DEP-02, EXEC-DEP-03, EXEC-FAIL-04, EXEC-IDN-01, EXEC-IDN-02, EXEC-ORD-01, EXEC-ORD-02, EXEC-PERF-01, EXEC-SEC-02, EXEC-SEC-05, EXEC-STA-04, EXEC-TRG-04

uv run pytest tests\test_broker_stops_contract.py tests\test_broker_stop_liveness.py tests\test_broker_fill_lifecycle.py agents\execution\tests\test_drop_sweep.py agents\execution\tests\test_drop_sweep_liveness.py agents\execution\tests\test_fill_refresh_terminal.py agents\execution\tests\test_partial_fill_completion.py agents\execution\tests\test_filled_entry_stops.py agents\reporter\tests\test_trade_outcomes.py --cov=contracts.broker_lifecycle --cov-report=term-missing --cov-fail-under=0
contracts\broker_lifecycle.py                                54      0     10      0 100.00%
45 passed in 16.09s
```

**Guards planted:** Broke `is_live_broker_stop_fact` so terminal sibling fills stayed live; A1 failed.
Broke `is_resting_stop_fill`; A6 failed. Broke `is_open_order_fill`; A7 failed. Broke
`is_live_broker_stop_order`; A4 failed. Removed `record_stop_mismatch` context; A5 failed. Added
`partial` to terminal fill statuses; A8 failed. Restored each mutation and re-ran the focused green
slice.

**Module line counts:** `contracts/broker_lifecycle.py` 162; `contracts/broker_stops.py` 105;
`agents/execution/drop_sweep.py` 168; `agents/execution/drop_sweep_records.py` 172;
`agents/execution/filled_entry_stops.py` 175; `agents/execution/reconciliation_store.py` 160;
`agents/execution/run.py` 120; `agents/reporter/domain/trade_outcomes.py` 54;
`agents/execution/tests/test_drop_sweep.py` 194; `agents/execution/tests/test_drop_sweep_liveness.py`
78; `tests/test_broker_stop_liveness.py` 158; `tests/test_broker_fill_lifecycle.py` 90; no touched
module exceeds 200. `uv run python scripts\check_module_size.py contracts agents tests scripts`
exited 0 with warn-only rows below the 200 hard block.

**`make ci`:**

```text
make ci *> $env:TEMP\s190-make-ci.txt; "exit=$LASTEXITCODE"
exit=0

uv run ruff check . --output-format=github
uv run ruff format --check .
1044 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 858 source files
uv run lint-imports
Contracts: 4 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
[WARN] law coverage: 101 clause(s) have no test-plan row (assertion E warn-only)
uv run python scripts/check_param_law_sync.py
uv run pytest
TOTAL                                                     15537      0   3332      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
2432 passed, 6 skipped in 84.03s
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 5 new file(s)
```

**`make gate-ran`:** Pending branch commit, push, and remote workflow completion.

**Not met / verified failing:** Branch push and remote `make gate-ran` proof are pending at this
checkpoint. No live spine query, fleet change, deploy, backfill, or FaultResolution was attempted.

---

## Return notes

- Next question remains separate: add an explicit resolved reason for fired-vs-cancelled stops if we
  want that distinction written to the graph.
- Historical `BrokerStopIdentityMismatch` faults, dead keys, and mislabelled old stops were not
  backfilled by design; proof here is prevention of new local mismatches.
- Live proof is after deployment: zero new `BrokerStopIdentityMismatch` faults and active graph stops
  equal broker live stops, to be recorded in `docs/laws/functionality-checks.md`.
- Fleet deployment was not attempted. This sprint itself can ride an image retag, but S189's graph
  vocabulary move still makes the combined deploy a full `up`.
