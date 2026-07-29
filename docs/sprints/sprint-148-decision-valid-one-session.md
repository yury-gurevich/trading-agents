<!-- Agent: planning | Role: sprint handover -->
# Sprint 148 — Fill it or drop it: a decision is valid for one session (ADR-0018)

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-148-decision-valid-one-session`
**Status:** SPEC — 🔴 **the largest measured cost in the system: ≈ −$2,850 across two exits**
**Version:** feat → **0.82.00** (MINOR: two middle digits, zeroing the patch group)
**Effort:** M
**Decisions:** [ADR-0018](../decisions/0018-decision-validity-same-session-or-dropped.md) **(this
sprint implements it — read it in full first; it is accepted, not up for redesign)** ·
[ADR-0015](../decisions/0015-exit-lifecycle-and-stop-ownership.md) §3 broker stops **(the exemption)**
· [ADR-0017](../decisions/0017-exit-authority-alpha-proposes-risk-disposes.md) forced exits become
best-effort · [ADR-0013](../decisions/0013-continuous-improvement-system.md) the tolerance is a
tunable, its value an experiment · [DL-62](../design-log.md) gap-down exposure ·
[DL-57](../design-log.md)/[DL-59](../design-log.md) intent ≠ outcome · [DL-70](../design-log.md)
plant violations

> **The decision is closed.** The operator ruled on 2026-07-29: *"Drop it if it is not filled.
> Decided."* Do not re-open the trade-off in this sprint. If the **implementation** forces a
> question the ADR does not answer, that is a finding — record it and report, do not decide it
> silently.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

### What the law folders are

This repo is governed by a **law book**. It is not documentation and it is not advisory — it is the
constitution the code is required to satisfy, and it outranks this sprint document.

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** — numbered clauses with IDs of the form `<AGENT>-<SECTION>-<NN>` | **LOCKED v1. Read-only. Never edit.** A clause you believe is wrong is a drift-register row plus a report, never an edit |
| `agents/<name>/laws/test-plan.md` | The clause-by-clause test map: which clauses are proven (🟩) and which are unproven (⬜) | Read it to learn whether the behaviour you are changing is currently *proven* or merely *asserted* |
| `docs/laws/*.md` | The **umbrella laws** — conventions, dependencies, drift register, ledger, functionality checks | Same status as agent laws. `drift-register.md` is the **one law-adjacent file you may append to** |

Clause **sections**: `IDN` identity · `IN` inputs · `TRG` triggers · `OUT` outputs ·
**`NEV` prohibitions** · `STA` state & effects · **`IDM` determinism & idempotency** · `ORD` ordering ·
**`FAIL` failure/recovery** · `TYP` types · `SEC` security · `DEP` dependencies · `OBS` observability ·
`PERF` performance · `CAP` capabilities · **`PARAM` parameters**.

For **this** sprint the binding sections are **`NEV`** (execution never overrides quantities, never
decides what to trade — a price tolerance must not become a decision), **`IDM`** (the idempotency
key survives a cancel), **`PARAM`** (the tolerance is a declared tunable, not a literal), and
**`FAIL`**. This sprint **cancels live broker orders**, so read the prohibitions first and hardest.

### The rule

1. **Before writing code**, for **every** element in the map below, open and read its law file(s).
   Read the whole file the first time — not a keyword grep.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜ (unproven),
   say so — you may be the first to test it.
3. Also read: [`docs/laws/conventions.md`](../laws/conventions.md),
   [`docs/laws/dependencies.md`](../laws/dependencies.md) (**`DEP-BROKER` governs the Alpaca
   boundary — this sprint changes what we send it**), and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Write the Law reading record** (template near the bottom) into this document **before** your
   first code change. It is the first thing reviewed at handback.
5. **If a law contradicts this spec, STOP and report.** The law is the constitution; this sprint doc
   is one sprint's opinion and it can be wrong. **A contradiction you surface is a success.**
6. **If a law is silent** where you must decide, that silence is a finding: record it and add a
   `docs/laws/drift-register.md` row.
7. Every test for behaviour a clause governs **must cite the clause ID in its docstring**.

### Element → law map (read all of these)

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/execution/alpaca_orders.py` — `order_body` (item 1) | `agents/execution/laws/laws.md` + `test-plan.md` + `docs/laws/dependencies.md` | The payload we send the broker. `EXEC-NEV-*` (never override quantity, never decide what to trade), `EXEC-IDN-01`, `DEP-BROKER` |
| `agents/execution/settings.py` — the tolerance tunable (item 1) | `agents/execution/laws/laws.md` (**`PARAM` section**) + `docs/laws/conventions.md` | `EXEC-PARAM-*` declares execution's tunables. **Check whether the section can hold a new one, or whether this is DRIFT-024/025's declaration debt a fourth time** |
| `agents/execution/poll.py` + a new drop sweep (items 2, 3) | `agents/execution/laws/laws.md` + `test-plan.md` | Cancelling live orders is a broker effect: `EXEC-NEV-*`, `EXEC-IDM-*`, `EXEC-FAIL-*`, `EXEC-STA-*` |
| `agents/execution/broker_stops.py` / `broker_stop_actions.py` (**read-only — item 3 must not change behaviour**) | `agents/execution/laws/laws.md` + [ADR-0015](../decisions/0015-exit-lifecycle-and-stop-ownership.md) §3 | **The exemption.** Read this before writing the sweep so you know exactly what it must never touch |
| `agents/reporter/domain/metrics.py` (item 4) | `agents/reporter/laws/laws.md` + `test-plan.md` | `RPT-*` — a dropped decision is not a rejection and not a loss; the reporter must not mis-project it |
| `contracts/execution.py` / `contracts/portfolio_manager.py` (**read-only unless a field is genuinely required**) | `agents/execution/laws/laws.md` + `agents/portfolio_manager/laws/laws.md` | `est_price` is the decided price this sprint anchors on; the PM owns it |
| `orchestration/packs/trading_graph_vocabulary.json` (item 7) | `docs/laws/conventions.md` | S143/S144: any new label, edge or signature must be declared or the guard throws on first write |

### What the trial is measuring

The law-first rule has now run twice ([DL-74](../design-log.md)). On S146 it surfaced DRIFT-024
before any code; on S147 it surfaced **DRIFT-025** and caught a reporter defect before it existed.
It is retained on that evidence.

Answer honestly in the record, per element: **did reading the law change what you were going to
do?** "No — the intended approach already complied" is a good answer and must be recorded as such.
A record that is vague, or written after the code, defeats the trial and is an incomplete handback
(DL-48).

---

## Why this sprint

The run fires at **22:30 UTC**, after the US close. It scores a completed daily bar, decides, and
submits **market** orders that cannot fill that session. They queue and execute at the **next open,
roughly 15 hours later, at a price nobody decided on.**

| Exit | Decided at | Filled at | Realized | Gap component |
| --- | --- | --- | --- | --- |
| MRVL (forced stop, 07-27) | — | `$195.98` | **−$1,330.12** | overnight |
| AMD (discretionary sell, 07-28) | `est $494.90` | `$467.35` | **−$3,515.60** | **≈ −$1,515** |

Two data points are not a trend, but the mechanism is structural: **every decision this system makes
executes at a price the decider never saw.**

And it is not only a pricing problem. **An unfilled order is live broker state that interferes.** As
of 2026-07-29, `MDT` holds 118 shares with **no protective stop**, because an unfilled
`MDT buy 115` from the same day makes Alpaca refuse the stop as a wash trade (`code 40310000`).
`ABT` spent two days in exactly that state for exactly that reason (S146). The orphaned-fill
machinery S145 and S146 had to build exists because stale orders exist.

**This sprint removes the class, not the instance.**

---

## What is already in place (read this before estimating)

The plumbing is further along than the ADR implies. Confirm each of these yourself:

- **The decided price already reaches the broker adapter and is discarded.**
  `Broker.submit(..., limit_price: Money)` ([`broker.py:54`](../../agents/execution/broker.py#L54))
  is satisfied by `AlpacaBroker.submit` ([`alpaca.py:50`](../../agents/execution/alpaca.py#L50)),
  which passes `limit_price` to `_fill_from_order` **as a fallback reference price only** — and then
  builds the payload with `order_body(...)`, which takes no price at all and hardcodes
  `"type": "market"` ([`alpaca_orders.py:22-33`](../../agents/execution/alpaca_orders.py#L22-L33)).
- **`limit_price` is already `est_price`.**
  `order_from_intent` sets `limit_price=intent.est_price`
  ([`domain/orders.py:43`](../../agents/execution/domain/orders.py#L43)). The decision price is
  carried end to end today. Nothing upstream needs to change to give you an anchor.
- **`Broker.cancel(broker_order_id)` already exists** on the port
  ([`broker.py:77`](../../agents/execution/broker.py#L77)) and is implemented.
- **Stops go through a different method.** `submit_stop(..., tif="gtc")` with
  `stop_order_body(...)` is a separate path. Item 1 must not touch it.
- **S147 just built the head-of-run stage** — execution now has a `RunRequest` work source
  (`find_pending_position_sync` in [`poll.py`](../../agents/execution/poll.py)). **That is the
  natural home for the drop sweep** (item 2), and it is why this sprint is M and not L.

So item 1 is a small, surgical change to one payload builder plus one tunable. **The risk in this
sprint is not item 1. It is item 3.**

---

## 🚨 The one thing that must not break

**A resting broker stop is not a decision and must never be cancelled.**

ADR-0018 §"The one exemption" is explicit: a `gtc` sell stop is a standing *risk instrument*. It is
the mechanism that makes dropping alpha decisions safe. Nine positions currently rely on it; seven
carry one right now.

**If the drop sweep cancels the resting stops, every held position loses its floor overnight, and
this sprint will have converted a −$2,850 pricing problem into an unbounded one.** That is the worst
outcome available in this codebase, and it is one over-broad `for order in open_orders:` away.

Identify stops **two ways, and require both** — do not rely on a `client_order_id` string prefix
alone:

1. the broker order's `type` is `stop` / `stop_limit`, **and/or**
2. the order is tracked as a `BrokerStopOrder` in the graph.

Then test it by **planting a resting stop and requiring the sweep to leave it alone** (test C1). A
test that only checks "the buy was cancelled" does not prove the stop survived.

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. Results go in this file.

### 1 · Orders carry a bounded price tolerance instead of being unconditional market orders

- Add a tolerance to `ExecutionSettings` as a `kernel.tunable(..., why=..., ge=..., le=..., unit=...)`
  — **never a literal**. Basis points is the natural unit and matches `slippage_bps` next to it.
  Start **conservative**; ADR-0018 leaves the value deliberately open and ADR-0013 makes it an
  experiment, so the *bounds* and the `why` matter more than the number.
- `order_body` gains the price and emits a bounded order rather than `"type": "market"`. Direction
  matters and getting it backwards is a silent money bug:
  - **buy** → limit at `est_price × (1 + tolerance)` — never pay more than tolerance above the
    decided price;
  - **sell** → limit at `est_price × (1 - tolerance)` — never receive less than tolerance below it.
- Round to the cent deterministically (`Decimal`, `ROUND_HALF_UP` — the `Money` convention already
  used in `alpaca_orders.price_of` and `paper_broker._paper_price`). No floats.
- **`time_in_force` stays `day`.** It is already `day`, and a day order cannot survive its session —
  that is the broker enforcing this ADR for free. Do not change it to `gtc`.
- **Do not touch `stop_order_body` or `submit_stop`.**
- `PaperBroker` must stay consistent so tests and the paper stage do not diverge from live
  behaviour: a paper order whose price is outside tolerance must not fill.

**Result:**
Shipped. `ExecutionSettings.order_price_tolerance_bps` is a bounded `kernel.tunable`
defaulting to 50 bps (`ge=0`, `le=500`, `unit="bps"`), `order_body` now builds
`limit`/`day` Alpaca payloads from the PM decided price, and `PaperBroker` mirrors the live bounded
limit behavior by leaving outside-tolerance orders pending instead of filling them. `stop_order_body`
and `submit_stop` stayed untouched.

### 2 · A head-of-run drop sweep: cancel what did not fill, and say so

- At the **head of the run** — the S147 `RunRequest` work source in `agents/execution/poll.py` is
  the right home — find broker orders still open from a **previous** run and cancel them.
- Each cancelled order is **dropped**: record a `Fault` naming the ticker, the decided price, and
  the reason (`unfilled at session end`), per ADR-0018 §3 and DL-57. **Silence is forbidden.**
- The graph must show the outcome. A dropped decision's `Fill` chain ends in a terminal, honest
  state — **append, never rewrite** (S145's lesson: one attempt = one immutable node).
- **Why the head of the run and not the close.** The fleet is scaled to zero at session end
  (KEDA window 22:30 → 00:30 UTC; the close is 20:00 UTC), so nothing is running to do it there.
  Cancelling at the head of the next run satisfies ADR-0018 §2's actual requirement — *a decision is
  never carried into a later session* — because the sweep runs **before** any new decision is made.
  `tif=day` means the broker has usually expired the order already; the sweep exists to catch what
  is still `accepted`, and to produce the visible record. **State this in your return notes as a
  deliberate deviation** from the ADR's literal "end of that session" wording, and see the road not
  taken for the after-close job.

**Result:**
Shipped as a head-of-run sweep in `agents/execution/poll.py` before run reconciliation. The sweep
reads broker orders, skips current-run orders, cancels previous-run pending non-stop orders, records
drop evidence on the existing Fill chain, writes a `BrokerOrderStatus -> REFRESHES -> Fill`
terminal refresh, and emits a visible `DroppedDecision` Fault with ticker, decided price,
idempotency key, broker order id, and `unfilled at session end`.

### 3 · 🚨 Resting broker stops are exempt — cancel none of them, ever

- The sweep **must not** cancel any resting stop. Identify them two ways (see the warning above) and
  require both signals to agree before treating an order as sweepable.
- The sweep must also not cancel an order **from the current run** — only prior runs.
- Prove it by planting: a graph with resting stops **and** a stale entry order must come out of the
  sweep with **every stop still live** and only the entry cancelled (test C1). Also plant a stop
  whose `client_order_id` does *not* start with `stop:` and require it to survive anyway (test C2) —
  otherwise you have proven a naming convention, not a safety property.

**Result:**
Shipped. The sweep exempts broker-native stops by broker order type (`stop`/`stop_limit`) and graph
`BrokerStopOrder` facts, records a warning if those signals disagree, and never cancels a stop even
when its client id lacks the `stop:` prefix. Current-run orders are exempt before stale-order
cancellation.

### 4 · A dropped decision is visible, and is not a rejection or a loss

- Execution's result must distinguish **dropped** from **rejected** and from **skipped**. A dropped
  decision was approved and simply did not execute — DL-57/DL-59: intent is not outcome, and an
  outcome that is not recorded did not happen.
- `agents/reporter/domain/metrics.py` reads `approved_count` / `rejected_count` off the PMRun. Make
  sure a dropped decision does **not** land in either bucket, and does **not** appear as a realized
  loss. If the reporter needs a new count to stay honest, add it.
- ADR-0018 §"Consequences" names this explicitly: *approval count and execution count diverge*.
  That divergence must be legible on the surface, not inferred.

**Result:**
Shipped. `ExecutionResult` now has an additive `dropped` count and dropped fills stay out of the
`rejected` bucket. Reporter metrics now surface `approved_count`, `execution_count`,
`rejected_count`, `dropped_decision_count`, and `approval_execution_gap`; dropped/canceled fills are
not treated as realized losses.

### 5 · ADR-0017's forced exit becomes best-effort — and that makes A2 load-bearing

- A forced daily-rail sell is now a bounded order and **can fail to fill**. On a gapping-down open
  the limit will not be reached, the sell is dropped, and the position stays held another session.
  **This is the accepted consequence, not a bug** — do not add a market-order escape hatch for it.
- It is only safe because the **resting broker stop is the real floor**. Therefore S146's audit
  check `A2` (every held position carries a live stop at the right quantity) stops being nice-to-have
  and becomes a safety invariant.
- **A position with no broker stop AND a dropped forced exit has no protection at all that day.**
  That combination must be *detectable*: make it a distinct, visible condition. Extending
  `scripts/audit_broker_graph.py` is the cheapest home.

**Result:**
Shipped. Forced exits now travel the same bounded limit path as entries and may remain unfilled.
`scripts/audit_broker_graph.py` now reports the distinct A5 condition: a held position with no live
full-quantity broker stop and a dropped sell/forced exit. Prefixless broker-native stops still clear
the risk condition via order metadata, not naming convention.

### 6 · Containment and idempotency

- The sweep wraps per-order work in `kernel.fault_boundary`. **One order's cancel failure must not
  stop the others** — DL-71's fan-out lesson, and the sweep is a fan-out over live broker orders.
- A cancel that fails (already filled, already expired, unknown id) degrades to a `Fault` and the
  run continues. Racing a fill at the open is a normal outcome, not an error.
- The sweep is **idempotent**: a second pass in the same run cancels nothing and writes no duplicate
  drop record.
- **The idempotency key must survive.** `EXEC-NEV-*` forbids skipping it. A cancelled order's
  `client_order_id` is spent — confirm what re-deciding the same ticker tomorrow does under the
  existing key scheme (`{run_id}:{ticker}:{side}` for entries, `exit:{position_ref}:{ticker}:sell`
  for exits). **The exit key is not run-scoped** — if tomorrow re-decides the same exit, it rebuilds
  the same key. S145 made that append-safe; confirm a *cancelled* attempt does not block a new one,
  and test it.

**Result:**
Shipped. Per-order cancellation is wrapped in `kernel.fault_boundary`; one cancel failure records a
Fault and the sweep continues to other orders. Re-running the sweep in the same run records no
duplicate drops. S145's append-safe attempt chain was verified for exit keys: a dropped
`exit:{position_ref}:{ticker}:sell` attempt does not block tomorrow's re-decision, which writes
`#1`.

### 7 · Declare every new label, edge and prop in the vocabulary

- Any new node, edge or signature goes in
  [`orchestration/packs/trading_graph_vocabulary.json`](../../orchestration/packs/trading_graph_vocabulary.json).
- Re-run `scripts/vocabulary_coverage.py` and `scripts/vocabulary_signatures.py`; paste the output
  into the closeout.

**Result:**
No vocabulary pack change was needed: the implementation used existing graph vocabulary
(`Fill`, `Fault`, `BrokerOrderStatus`, `REFRESHES`, `BrokerStopOrder`). Both vocabulary scripts
were rerun after the implementation and exited 0 with no output.

### 8 · Prove the checks can fail (DL-70)

No presence assertions. Plant the violation and require the failure — the test plan below specifies
the violation for every test.

**Result:**
Shipped. The test suite includes planted inversions/failures for tolerance direction, bare literal
tolerance config, stop-sweep exemption, sweep idempotency, dropped-vs-rejected/loss metrics, A5
audit detection, cancel-failure containment, and vocabulary rejection.

---

## Test plan — every test I want, and why

**Ground rules.** Every test cites its clause ID(s) in the docstring. Every test **plants the
violation** and requires the failure. Names below are descriptive, not prescriptive. **If you think
a test is wrong or untestable, say so with a reason — do not silently drop it.**

### A · The tolerance (order construction)

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | a buy is bounded above the decided price | `est_price` 100.00, tolerance *t* | payload is a bounded order at `100.00 × (1+t)`, **not** `type: market`. Assert the exact cent |
| A2 | a sell is bounded below the decided price | same | limit is `100.00 × (1-t)`. **Plant the inverted sign and require the test to fail** — the buy/sell direction is a silent money bug and must be pinned in both directions |
| A3 | rounding is deterministic to the cent | a price whose tolerance lands on a half-cent | `Decimal` + `ROUND_HALF_UP`, no float drift; same input → same payload every time (`EXEC-IDM-*`) |
| A4 | the tolerance is a declared tunable | — | it is a `kernel.tunable` with `why`, `ge`, `le`, `unit` — **not a literal**. Plant a bare literal and require the gate to reject it |
| A5 | `time_in_force` stays `day` | — | the payload still says `day`; a change to `gtc` fails the test. Guards item 1's "do not change this" against a future tidy-up |
| A6 | a paper order outside tolerance does not fill | `PaperBroker`, price beyond tolerance | no fill — paper and live agree, so the paper stage keeps telling the truth |

### B · The drop sweep

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | a prior run's unfilled order is cancelled | one open order from an earlier run | `cancel` called exactly once with that broker order id |
| B2 | the current run's order is left alone | an open order from *this* run | **not** cancelled. Plant it alongside a stale one and prove only the stale one goes |
| B3 | a filled order is never cancelled | an order already `filled` | no cancel call |
| B4 | the drop is recorded, not silent | a stale order | a `Fault` naming ticker, decided price, and reason; the `Fill` chain ends in a terminal state; **nothing rewritten in place** (append-only, S145) |
| B5 | the sweep is idempotent | run it twice in one run | second pass cancels nothing and writes no duplicate drop record |

### C · 🚨 Stop safety — the tests that matter most

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| C1 | 🚨 **resting stops survive the sweep** | 7 resting `gtc` stops **and** 1 stale entry order | after the sweep: **all 7 stops still live**, exactly 1 cancel call, and it was the entry. If one test in this sprint survives a future refactor, make it this one |
| C2 | 🚨 a stop is safe even without the `stop:` prefix | a stop whose `client_order_id` does not start with `stop:` | it still survives — proves a **safety property**, not a naming convention |
| C3 | a stop is never converted to a bounded order | run item 1's path over a stop submission | `submit_stop` / `stop_order_body` is unchanged: still `type: stop`, still `tif: gtc` |
| C4 | the exemption holds when the sweep partially fails | stops present, one cancel raises | the raising cancel is contained and **no stop is cancelled in the fallout** |

### D · Visibility and honest metrics

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| D1 | dropped ≠ rejected | one dropped, one genuinely rejected | the execution result distinguishes them; a dropped decision is not counted as a rejection |
| D2 | dropped ≠ realized loss | a dropped sell | the reporter reports no realized loss for it. **Plant the wrong behaviour** (count it as a loss) and require the failure |
| D3 | approval and execution counts may legally diverge | 3 approved, 1 dropped | the surface shows the divergence rather than hiding it — ADR-0018's named consequence |
| D4 | 🚨 unprotected **and** dropped is detectable | a held position with no stop whose forced exit was dropped | the audit reports it as a distinct condition. This is item 5's safety net; without it the ADR's accepted risk is invisible |

### E · Containment, idempotency, vocabulary

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| E1 | one cancel failure does not stop the sweep | 3 stale orders, the **middle** one raises | the other two are cancelled, one `Fault` recorded, the call returns normally (DL-71) |
| E2 | a cancel racing a fill is not an error | cancel raises "already filled" | contained as a `Fault`, run continues, no crash into `work_loop` |
| E3 | a cancelled exit can be re-decided tomorrow | a cancelled exit attempt under `exit:{position_ref}:{ticker}:sell` | a fresh attempt writes a new append-safe node and is not blocked by the cancelled one (S145's attempt chain) |
| E4 | every new label and edge is declared | the new nodes/edges | the vocabulary guard accepts them, **and** an undeclared edge is rejected — otherwise you have only proven the guard is quiet |

---

## Explicit non-goals

- **No intraday decision path.** Re-validating at the open is explicitly ruled out in ADR-0018.
- **No change to the run schedule.** Moving the run inside the session is ruled out — the analyst's
  15 pillars need completed daily bars.
- **No after-close cancel job.** See the road not taken; the head-of-run sweep is this sprint.
- **No change to `submit_stop`, `stop_order_body`, `broker_stops.py` or `broker_stop_actions.py`**
  beyond what item 3 requires to *exclude* them.
- **No tuning of the tolerance value.** Ship a conservative default with bounds and a `why`. Moving
  it is an ADR-0013 experiment with a measured drop rate, not a judgement call in this sprint.
- **No manual broker cleanup.** Do not cancel or modify live orders by hand while developing. The
  sweep must be exercised against fixtures and the paper broker, never by improvising against
  production.
- **No `laws.md` edits.** LOCKED v1. Findings go to `drift-register.md`.

### The road not taken (LAW-06)

Ruled out — record any further options you rule out during implementation:

- **An after-close cancel job (the ADR's literal wording).** A second scheduled window at ~20:05 UTC
  that cancels unfilled orders at the true session end. Rejected **for this sprint only**: it needs a
  new KEDA window and a new job, and the head-of-run sweep already prevents a decision reaching a
  later session. Worth doing when the drop record needs to be timely rather than eventually correct
  — **deferred, not rejected.**
- **Relying on `tif=day` alone.** The broker already expires day orders, so why sweep at all?
  Rejected: expiry produces no `Fault`, no drop record, and no `Fill`-chain terminal state, so the
  system would forget the decision instead of recording that it was dropped. That is DL-57's failure
  mode exactly. It also does not cover an order sitting `accepted`.
- **Marketable limit orders (limit far through the touch).** Would fill essentially always and keep
  fill rates high. Rejected: it is a market order wearing a costume, and it re-creates the exact
  problem the ADR closes.
- **Cancelling stops too, for uniformity.** Rejected permanently — see the 🚨 warning. Alpha
  decisions expire; risk instruments persist (ADR-0017's line).
- **Making the tolerance per-ticker (volatility-scaled).** Genuinely attractive — a 50 bps band means
  something different for USB than for AMD. Rejected as scope: it needs a volatility input on the
  intent and turns one tunable into a model. Revisit after the drop rate is measured (ADR-0013).

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **all four remote gates green before merging locally**
   (DL-56 — pushing is the gate; no PR required).
2. Build + retag the fleet at `:s148`. The running fleet is `:s147`.
3. **Watch the first scheduled run closely, and check the drop rate first.** If the tolerance is too
   tight, nothing trades; if too wide, the ADR bought nothing. Either way the value moves on
   evidence (ADR-0013), not argument.
4. **Verify `MDT` receives its protective stop** once its blocking buy is cancelled or dropped. That
   is the concrete, currently-failing thing this sprint should fix.
5. Record the functionality check in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds, never a bare literal.
- Faults, not silent failure — `kernel.fault_boundary`, errors redirected with provenance.
- `make ci` all 9 steps green, **100.00 % coverage floor**, before handback. Never lower the floor.
- Version bump in `pyproject.toml` to **0.82.00** (feat → MINOR), `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the test docstring.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48).
- Secrets never through the worktree — chat or gitignored `.env` only.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the placeholder sections below.**
Not a separate report file. Not chat-only.

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the eight spec items, in place.
3. Fill the **Test plan results** table — one row per planned test, with its final name and status.
   A test you chose not to write needs a reason, not a blank.
4. Fill the **Closeout — evidence** block with real command output: `make ci` counts, the remote gate
   job results, the planted-violation runs, the vocabulary script output.
5. Fill the **Return notes**, including the item-2 deviation and what you chose for the tolerance
   default and why.
6. State any success factor you did **not** meet plainly, as "verified failing" or "not done"
   (LAW-02 — a proven failure is a valid handback, a silent gap is not).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| `alpaca_orders.py` — `order_body` | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/dependencies.md`; ADR-0018 | `EXEC-IDN-01`; `EXEC-IN-01`; `EXEC-NEV-01`; `EXEC-NEV-02`; `EXEC-NEV-03`; `EXEC-TYP-01`; `EXEC-TYP-02`; `EXEC-DEP-03`; `DEP-BROKER-01`; `DEP-BROKER-02` | Yes - the bounded price is execution-owned guardrail math only, not a trading decision. Preserve side, quantity, idempotency key, `day` TIF, Decimal money, and the existing four-value Fill status unless the contract is deliberately amended. |
| `settings.py` — the tolerance tunable | `agents/execution/laws/laws.md` PARAM section; `agents/execution/laws/test-plan.md`; `docs/laws/conventions.md`; ADR-0013; ADR-0018 | `EXEC-PARAM`; `EXEC-IDN-01`; `EXEC-NEV-01`; conventions section 3; conventions section 7 | Yes - the tolerance must be a declared `kernel.tunable` with `why`, bounds, and unit. The locked execution law does not declare this new parameter, so record law silence in `drift-register.md` after this pre-edit record. |
| `poll.py` + the drop sweep | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `docs/laws/dependencies.md`; ADR-0018; DL-57; DL-59; DL-70 | `EXEC-IDN-01`; `EXEC-IDN-02`; `EXEC-NEV-01`; `EXEC-NEV-03`; `EXEC-STA-03`; `EXEC-IDM-01`; `EXEC-IDM-02`; `EXEC-FAIL-01`; `EXEC-FAIL-02`; `EXEC-FAIL-03`; `EXEC-OBS-01`; `EXEC-OBS-02`; `DEP-BROKER-01`; `DEP-BROKER-02` | Yes - the sweep must be append-only, per-order contained, idempotent, visible through Fault/drop evidence, and current-run safe. Cancellation is a broker effect, so each cancel failure degrades to evidence instead of aborting fan-out. |
| `broker_stops.py` / `broker_stop_actions.py` (read-only) | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; ADR-0015 §3 amendment; ADR-0017; ADR-0018; DL-62 | `EXEC-IDN-01`; `EXEC-NEV-01`; `EXEC-NEV-02`; `EXEC-NEV-03`; `EXEC-STA-03`; `EXEC-IDM-01`; `EXEC-OBS-02`; ADR-0015 §3 broker-native stop exemption | Yes - stops are risk instruments, not expiring alpha decisions. The sweep must require stop-type/graph-stop evidence checks before cancellation and must not touch `submit_stop` / `stop_order_body` behavior. |
| `reporter/domain/metrics.py` | `agents/reporter/laws/laws.md`; `agents/reporter/laws/test-plan.md`; ADR-0018; DL-57; DL-59 | `RPT-IDN-01`; `RPT-OUT-01`; `RPT-OUT-02`; `RPT-NEV-01`; `RPT-NEV-02`; `RPT-NEV-03`; `RPT-STA-02`; `RPT-IDM-01`; `RPT-TYP-02`; `RPT-OBS-01`; `RPT-OBS-02` | No - the intended reporter change is a read-only projection. It must keep dropped decisions out of rejected/loss buckets and may add a metric so approval-vs-execution divergence is visible. |
| `contracts/execution.py` / `portfolio_manager.py` | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md`; ADR-0018 | `EXEC-IN-01`; `EXEC-OUT-01`; `EXEC-TYP-02`; `EXEC-TYP-03`; `PM-OUT-02`; `PM-TYP-01`; `PM-IDM-02`; `PM-OBS-01` | Yes - `OrderIntent.est_price` is already the decided Decimal price and PM-owned. Prefer threading existing fields into execution rather than adding upstream contract fields. If a dropped outcome needs additive execution contract fields, keep PM untouched. |
| `trading_graph_vocabulary.json` | `docs/laws/conventions.md`; DL-70; S143/S144 vocabulary guard context from the sprint brief | conventions section 3; conventions section 7; DL-70 can-fail rule | No - any new label, edge, or signature must be declared and proven by both acceptance and a planted undeclared violation. |

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

None found before code. One constraint matters: `EXEC-TYP-02` currently permits only `filled`,
`partial`, `rejected`, and `pending` Fill statuses, so I will not silently introduce a `dropped`
Fill status unless the contract/law gap is explicitly recorded. The current intended path is to
make dropped visible via additive result metrics, reason/provenance, Fault/drop evidence, and
reporter projection rather than pretending it is a rejection.

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

- Execution PARAM is silent on the new `order_price_tolerance_bps` tunable required by ADR-0018.
- Execution's locked label/capability/output clauses are silent on durable dropped-decision evidence
  and any additive `ExecutionResult` drop count needed to distinguish dropped from rejected.

**Clauses that were ⬜ unproven in `test-plan.md` and are now proven by this sprint's tests:**

Now proven by the sprint tests and focused can-fail coverage: `EXEC-NEV-02`, `EXEC-FAIL-03`,
`RPT-IDM-01`, and `RPT-TYP-02`.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_order_body_builds_bounded_buy_limit_payload` | `agents/execution/tests/test_order_tolerance.py` | Passed | `EXEC-IN-01`; `EXEC-NEV-01`; `EXEC-TYP-01` |
| A2 | `test_order_body_builds_bounded_sell_limit_payload` | `agents/execution/tests/test_order_tolerance.py` | Passed | `EXEC-IN-01`; `EXEC-NEV-01`; `EXEC-TYP-01` |
| A3 | `test_order_body_rounds_half_cent_up_and_keeps_day_tif` | `agents/execution/tests/test_order_tolerance.py` | Passed | `EXEC-IDM-01`; `EXEC-TYP-01`; `EXEC-NEV-02` |
| A4 | `test_execution_order_price_tolerance_is_declared_tunable` | `agents/execution/tests/test_order_tolerance.py` | Passed | `EXEC-PARAM`; `EXEC-NEV-01` |
| A5 | `test_order_body_rounds_half_cent_up_and_keeps_day_tif` | `agents/execution/tests/test_order_tolerance.py` | Passed | `EXEC-IDM-01`; `EXEC-TYP-01`; `EXEC-NEV-02` |
| A6 | `test_paper_broker_order_outside_tolerance_does_not_fill` | `agents/execution/tests/test_broker_positions.py` | Passed | `EXEC-NEV-01`; `EXEC-TYP-01` |
| B1 | `test_sweep_cancels_prior_run_order_and_records_drop` | `agents/execution/tests/test_drop_sweep.py` | Passed | `EXEC-STA-03`; `EXEC-OBS-02`; `EXEC-FAIL-01` |
| B2 | `test_sweep_leaves_current_and_filled_orders_alone` | `agents/execution/tests/test_drop_sweep.py` | Passed | `EXEC-IDM-01`; `EXEC-IDM-02` |
| B3 | `test_sweep_leaves_current_and_filled_orders_alone` | `agents/execution/tests/test_drop_sweep.py` | Passed | `EXEC-IDM-01`; `EXEC-IDM-02` |
| B4 | `test_sweep_cancels_prior_run_order_and_records_drop` | `agents/execution/tests/test_drop_sweep.py` | Passed | `EXEC-STA-03`; `EXEC-OBS-02`; `EXEC-FAIL-01` |
| B5 | `test_sweep_is_idempotent_for_same_run` | `agents/execution/tests/test_drop_sweep.py` | Passed | `EXEC-IDM-01`; `EXEC-STA-03` |
| C1 | `test_sweep_exempts_resting_stops_and_prefixless_stop` | `agents/execution/tests/test_drop_sweep.py` | Passed | `EXEC-NEV-01`; `EXEC-NEV-03` |
| C2 | `test_sweep_exempts_resting_stops_and_prefixless_stop` | `agents/execution/tests/test_drop_sweep.py` | Passed | `EXEC-NEV-01`; `EXEC-NEV-03` |
| C3 | `test_stop_order_body_builds_exact_gtc_stop_payload` | `agents/execution/tests/test_alpaca_stop_orders.py` | Passed | `EXEC-NEV-01`; `EXEC-TYP-01`; `EXEC-IDM-01` |
| C4 | `test_cancel_failure_is_contained_and_other_orders_continue` | `agents/execution/tests/test_drop_sweep.py` | Passed | `EXEC-FAIL-01`; `EXEC-FAIL-02` |
| D1 | `test_execution_result_counts_dropped_separately_from_rejected` | `agents/execution/tests/test_execution_domain.py` | Passed | `EXEC-TYP-02`; `EXEC-OBS-02` |
| D2 | `test_dropped_sell_is_not_counted_as_realized_loss` | `agents/reporter/tests/test_trade_outcomes.py` | Passed | `RPT-OUT-02`; `RPT-NEV-03` |
| D3 | `test_dropped_decision_is_visible_but_not_rejected` | `agents/reporter/tests/test_metrics_narrative.py` | Passed | `RPT-IDN-01`; `RPT-NEV-01`; `RPT-TYP-02` |
| D4 | `test_audit_a5_fails_unprotected_position_with_dropped_sell` | `tests/test_audit_broker_graph.py` | Passed | `EXEC-OBS-02`; `RPT-NEV-03` |
| E1 | `test_cancel_failure_is_contained_and_other_orders_continue` | `agents/execution/tests/test_drop_sweep.py` | Passed | `EXEC-FAIL-01`; `EXEC-FAIL-02` |
| E2 | `test_cancel_failure_is_contained_and_other_orders_continue` | `agents/execution/tests/test_drop_sweep.py` | Passed | `EXEC-FAIL-01`; `EXEC-FAIL-02` |
| E3 | `test_dropped_exit_key_can_be_redecided_tomorrow` | `agents/execution/tests/test_drop_sweep.py` | Passed | `EXEC-IDM-01`; `EXEC-NEV-03` |
| E4 | `test_the_guard_can_actually_reject_a_write` | `orchestration/tests/test_graph_vocabulary_e2e.py` | Passed | Vocabulary guard rejection path |

**Tests added beyond the plan:**

- `test_resolved_rejected_order_is_recorded_as_drop_without_cancel`
- `test_untracked_pipeline_order_is_faulted_after_cancel_attempt`
- `test_resolved_untracked_order_is_faulted_without_cancel`
- `test_graph_tracked_stop_mismatch_is_faulted_and_exempted`
- `test_run_marking_helpers_tolerate_missing_lineage_and_existing_count`
- `test_paper_broker_cancel_records_each_broker_order_once` now asserts pending stop cancellation
  mutates the paper order state to rejected/canceled.
- `test_canceled_broker_status_is_not_counted_as_realized_loss`

---

## Closeout — evidence

**Files changed:**

Implementation:

- `agents/execution/settings.py`
- `agents/execution/alpaca_orders.py`
- `agents/execution/alpaca.py`
- `agents/execution/broker.py`
- `agents/execution/broker_factory.py`
- `agents/execution/paper_broker.py`
- `agents/execution/paper_broker_math.py`
- `agents/execution/poll.py`
- `agents/execution/drop_sweep.py`
- `agents/execution/drop_sweep_records.py`
- `agents/execution/domain/result.py`
- `agents/execution/store.py`
- `agents/reporter/domain/metrics.py`
- `agents/reporter/domain/trade_outcomes.py`
- `agents/reporter/result.py`
- `contracts/execution.py`
- `scripts/_audit_broker_graph_impl.py`
- `scripts/_audit_broker_graph_drops.py`

Tests/docs/version:

- `agents/execution/tests/test_order_tolerance.py`
- `agents/execution/tests/test_drop_sweep.py`
- `agents/execution/tests/test_drop_sweep_edges.py`
- `agents/execution/tests/drop_sweep_helpers.py`
- `agents/execution/tests/test_execution_domain.py`
- `agents/execution/tests/test_alpaca_broker.py`
- `agents/execution/tests/test_alpaca_stop_orders.py`
- `agents/execution/tests/test_broker_positions.py`
- `agents/reporter/tests/test_metrics_narrative.py`
- `agents/reporter/tests/test_trade_outcomes.py`
- `tests/test_audit_broker_graph.py`
- `tests/test_contract_values.py`
- `docs/STATE.md`
- `docs/laws/drift-register.md`
- `docs/sprints/sprint-148-decision-valid-one-session.md`
- `pyproject.toml`
- `uv.lock`

**Proven (LAW-02):**

Local gates:

```text
uv lock
Resolved 170 packages in 2.11s
Updated trading-agents v0.81.0 -> v0.82.0
```

```text
uv run pytest tests/test_contract_values.py agents/execution/tests/test_drop_sweep.py agents/execution/tests/test_drop_sweep_edges.py agents/execution/tests/test_broker_positions.py agents/reporter/tests/test_trade_outcomes.py --no-cov
38 passed in 1.51s
```

```text
uv run pytest agents/execution/tests/test_execution_domain.py agents/execution/tests/test_drop_sweep_edges.py --no-cov
11 passed in 1.03s
```

```text
uv run python scripts/vocabulary_coverage.py
exit 0, no output
uv run python scripts/vocabulary_signatures.py
exit 0, no output
```

```text
git diff --check
exit 0, no output
```

```text
make ci
uv run ruff check . --output-format=github
uv run ruff format --check .
842 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 707 source files
uv run lint-imports
Contracts: 4 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
warnings only; no hard 200-line block
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run pytest
1930 passed, 5 skipped in 158.38s
Required test coverage of 100.0% reached. Total coverage: 100.00%
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 8 new file(s)
exit 0
```

Planted violation evidence:

- A2 planted inverted sell/buy direction under `pytest.raises(AssertionError)` in
  `test_order_body_builds_bounded_sell_limit_payload`.
- A4 planted a bare-literal settings class under `pytest.raises(AssertionError)` in
  `test_execution_order_price_tolerance_is_declared_tunable`.
- C1/C2 planted seven graph/broker stops plus a prefixless stop alongside a stale entry; only the
  stale entry was canceled.
- B5 planted a duplicate sweep and proved the second pass wrote no duplicate drop/status/fault.
- D2 planted a dropped sell with bogus negative `realized_pnl_cents`; reporter returned no closed
  PnL.
- D4 planted held position + dropped sell + no stop; audit reported distinct A5 FAIL, then a
  prefixless broker-native stop cleared it.
- E1/E2 planted three stale orders with the middle cancel raising; the first and third were
  canceled and one Fault was recorded.
- E4 existing vocabulary guard test plants an undeclared write/signature and requires rejection.

Remote gates:

Pending branch push at this point in the local closeout. The branch will be pushed after this
evidence is committed; final remote run IDs/results will be recorded in the return/handoff notes.

**The tolerance value shipped, and why:**

Default: `50` bps. Bounds: `ge=0`, `le=500`, `unit="bps"`. Why string shipped:
`Bound entry and discretionary-exit orders near the PM's decided price so after-close decisions do
not trade at unevaluated opens.`

Rationale: 50 bps is conservative enough to prevent the large unevaluated-open gap ADR-0018 was
written to close, but not tuned as a performance claim. Future movement belongs to ADR-0013
experimentation using measured drop rate/fill quality, not this implementation sprint.

**Not met / verified failing:**

- Remote GitHub gates are not yet proven in this local file section because they require the branch
  commit to be pushed first.
- Post-merge deployment, fleet retag to `:s148`, scheduled-run watch, MDT stop verification, and
  `docs/laws/functionality-checks.md` entry are not done; the sprint sequencing explicitly puts
  them after merge/deploy.
- No manual broker cleanup was performed, by sprint non-goal.

---

## Return notes

- Item-2 deviation from ADR-0018 literal wording: the cancellation/drop sweep runs at the head of
  the next run, not in an after-close job. That is deliberate because the fleet scales to zero at
  session end; `time_in_force=day` usually lets the broker expire the order, and the head sweep runs
  before any new decision so stale decisions still cannot enter a later session.
- Surprise: the graph vocabulary did not need new labels/edges. The honest drop path fits existing
  `Fill`, `Fault`, `BrokerOrderStatus`, and `REFRESHES` vocabulary.
- Deliberately did not do: no `submit_stop`/`stop_order_body` behavior change, no market-order
  escape hatch for forced exits, no per-ticker tolerance model, no after-close job, no locked-law
  edits, no live broker/manual cleanup.
- The implementation records `DRIFT-026` because locked execution laws are silent on the new
  tolerance tunable and durable dropped-decision semantics.
- Main movement check before commit: `git rev-parse main` and `git merge-base main HEAD` both
  returned `04e81c3162a623c14304f6d7ed77b41c1bfcb2c5`; `git rev-list --left-right --count
  main...HEAD` returned `0 0`.
