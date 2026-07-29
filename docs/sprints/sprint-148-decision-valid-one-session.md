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

### 3 · 🚨 Resting broker stops are exempt — cancel none of them, ever

- The sweep **must not** cancel any resting stop. Identify them two ways (see the warning above) and
  require both signals to agree before treating an order as sweepable.
- The sweep must also not cancel an order **from the current run** — only prior runs.
- Prove it by planting: a graph with resting stops **and** a stale entry order must come out of the
  sweep with **every stop still live** and only the entry cancelled (test C1). Also plant a stop
  whose `client_order_id` does *not* start with `stop:` and require it to survive anyway (test C2) —
  otherwise you have proven a naming convention, not a safety property.

**Result:**

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

### 7 · Declare every new label, edge and prop in the vocabulary

- Any new node, edge or signature goes in
  [`orchestration/packs/trading_graph_vocabulary.json`](../../orchestration/packs/trading_graph_vocabulary.json).
- Re-run `scripts/vocabulary_coverage.py` and `scripts/vocabulary_signatures.py`; paste the output
  into the closeout.

**Result:**

### 8 · Prove the checks can fail (DL-70)

No presence assertions. Plant the violation and require the failure — the test plan below specifies
the violation for every test.

**Result:**

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
| `alpaca_orders.py` — `order_body` | | | |
| `settings.py` — the tolerance tunable | | | |
| `poll.py` + the drop sweep | | | |
| `broker_stops.py` / `broker_stop_actions.py` (read-only) | | | |
| `reporter/domain/metrics.py` | | | |
| `contracts/execution.py` / `portfolio_manager.py` | | | |
| `trading_graph_vocabulary.json` | | | |

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

**Clauses that were ⬜ unproven in `test-plan.md` and are now proven by this sprint's tests:**

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
| B1 | | | | |
| B2 | | | | |
| B3 | | | | |
| B4 | | | | |
| B5 | | | | |
| C1 | | | | |
| C2 | | | | |
| C3 | | | | |
| C4 | | | | |
| D1 | | | | |
| D2 | | | | |
| D3 | | | | |
| D4 | | | | |
| E1 | | | | |
| E2 | | | | |
| E3 | | | | |
| E4 | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Files changed:**

_(fill in)_

**Proven (LAW-02):**

_(paste real command output: `make ci` counts and coverage, remote gate job IDs and results,
planted-violation runs showing the failure before the fix, vocabulary script output)_

**The tolerance value shipped, and why:**

_(fill in — the number, its bounds, and the `why` string)_

**Not met / verified failing:**

_(fill in — a proven failure is a valid handback; a silent gap is not)_

---

## Return notes

_(fill in: the item-2 deviation from the ADR's literal wording and why; what surprised you; what you
deliberately did not do; anything the next sprint inherits; and whether `main` had moved when you
finished)_
