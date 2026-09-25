<!-- Agent: planning | Role: sprint handover -->
# Sprint 230 — a protective stop rests where the PM decided it, not at the fallback

**Phase:** Etalon-first continuous improvement (DL-19) · live defect, ranked above features
**Branch:** `sprint-230-a-stop-rests-where-the-pm-decided`
**Status:** BUILT
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-222](../design-log.md) (the measurement) · work-queue item **87** · DL-156 (the stop mode flipped to `scaled`, 2026-09-05) · [DL-200](../design-log.md) / S225 (why every stop comes from a broker-adopted Position) · ADR-0015 §3 (resting protective stops) · ADR-0017 (the stop is an unconditional floor) · design decisions go to **DL-223**

> **Why this bump kind.** No new capability. The execution law already promises that the fallback
> stop is for positions *"with no PM stop lineage"* (its `PARAM` row), and the code applies it to
> positions that have one. That is a PATCH.

**Builder:** Codex. Every behaviour is pinned by a row in the test plan.
**If a number you measure differs from one written here, stop and report. Do not adjust and continue.**
🪤 **[S229](sprint-229-every-component-that-decides-answers-to-a-law-book.md) is being built in parallel.**
It touches no product code, but it edits `docs/laws/ledger.md`, `docs/laws/INDEX.md`,
`docs/laws/drift-register.md` and `docs/design-log.md` (DL-221). Rebase onto `main` after it merges,
expect textual conflicts in those four files, and let `make ci` re-derive the rollups.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: execution **`EXEC-OBS-03`** (the protective-stop lifecycle is reconstructable;
cancellation is a marker, never a deletion), **`EXEC-OBS-05`** (liveness is asked in exactly one
place), **`EXEC-DEP-04`** (the broker capabilities execution relies on), the execution `PARAM` row
**`broker_stop_fallback_stop_pct`**, and **`EXEC-NEV-07`** (protective stops are never weakened by the
degraded posture). Monitor **`MON-NEV-05`** (reads other agents' nodes, never mutates them) and
**`MON-STA-02`** (append-only). The analyst's held-position stop check (search the analyst book for
`stop_breached` / ADR-0017).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes, on both counts.** `contracts/` gains the stop-width resolver and a `replaced` broker status,
and execution gains a guarantee it does not make today: *a live stop whose price differs from its
decided price is replaced*. **A law cycle is owed in this sprint:** an execution clause (or an
amendment to `EXEC-OBS-03`) for the decided width and the replacement, the `PARAM` row reworded if
needed, a `test-plan.md` row per clause, the clause ID in each test docstring, both rollups
(`ledger.md` + `INDEX.md`), and a `drift-register.md` row recording that the fallback was applied to
positions with lineage from 2026-09-05. Check the analyst and monitor books for any clause that names
`Position.stop_pct` as the source; amend it if one exists.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| new `contracts/stop_width.py` (the resolver) | execution + analyst + monitor books | one definition of the decided stop, read by three agents (the DL-208 rule) |
| `contracts/positions.py` (187), `contracts/broker_lifecycle.py` (162), `contracts/broker_stops.py` (105) | execution book `EXEC-OBS-03/05` | the shared threshold and the one liveness question |
| `agents/execution/broker_stop_thresholds.py` (142), `broker_stops.py` (185), `broker_stop_actions.py` (131), `broker_stop_writes.py` (104) | execution book | stop placement, the new replace path, the facts it writes |
| `agents/execution/broker.py` (124), `alpaca.py` (189), `alpaca_orders.py` (136), `paper_broker.py` (183) | execution book `EXEC-DEP-03/04` | the `Broker` port gains `replace_stop` |
| `agents/monitor/domain/positions.py` | monitor book `MON-NEV-05` | its stop watchdog reads the same threshold |

⚠️ **One invariant: at no moment may a held position have no live stop because of this sprint.** That
is why the replacement is Alpaca's atomic *replace* and never cancel-then-place. If your design opens a
window where a position is unprotected, stop and report.

---

## Goal

For every held position, the protective stop resting at Alpaca sits at the width the PM decided when
it bought: `OrderIntent.stop_pct`, reached through the fill's lineage. The 5 % fallback applies only
where no lineage exists, and says so. A live stop whose price differs from its decided price by a cent
or more is **replaced in place**, with the old order recorded as replaced, never deleted. The analyst,
the monitor and execution read one resolver, so they cannot disagree about where a stop is.

## Why (context)

The operator asked why losing positions were not sold. The answer is ADR-0017: exits are the stop or a
thesis collapse, and neither had fired. Measuring the stops found that **none of them rests where it
was decided.** Since DL-156 flipped the PM to volatility-scaled stops on 2026-09-05, calm names have
carried looser stops than decided and volatile names tighter ones, so the volatile names are the ones
most likely to be shaken out on ordinary noise. That is the exact failure DL-77 measured flat stops
for. The money is small (positions are ~1 % of the book; the gap is up to ~$23 of loss exposure per
position), but it is risk control not doing what it was decided to do, on every buy since
2026-09-05.

### Measured, 2026-09-25 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Open protective stops | **25**, all `type=stop`, `side=sell`, `status=new`, `time_in_force=gtc` | *[measured 2026-09-25]* Alpaca paper `GET /v2/orders?status=open` |
| Where they rest | **5.00–5.02 %** below average entry, all 25 | *[measured 2026-09-25]* stop price vs `avg_entry_price` |
| Holdings vs their lineage | **25 of 25** holdings equal their most recent filled buy exactly (quantity and `broker_price_cents` = Alpaca `avg_entry_price`) | *[measured 2026-09-25]* each ticker's latest filled `Fill` with `source_run_id` = `pm-run-*`, against Alpaca `/v2/positions` |
| Lineage path | production buy `Fill` (key `pm-run-<hex>:<TICKER>:buy`) → one `OrderIntent` descendant carrying `stop_pct` | *[measured 2026-09-25]* live spine; the S182 path reads the same edge (`filled_entry_stops._order_intent`, `EXECUTES`) |
| Positions whose decided stop is 5 % already | **16** (bought in flat mode or decided at exactly 5 %) — no change | *[measured 2026-09-25]* |
| 🎯 **Positions whose stop differs** | **9**: tighten AMZN 4.36 %, BAC 4.68 %, BMY 4.15 %, MDLZ 3.90 %, SCHW 4.81 %, USB 4.03 %; widen CSCO 5.28 %, DOW 7.13 %, META 7.29 % | *[measured 2026-09-25]* decided `stop_pct` vs placed. Decided stop prices: AMZN 244.95, BAC 55.18, BMY 58.85, MDLZ 58.44, SCHW 96.02, USB 58.06, CSCO 100.85, DOW 25.98, META 686.35 |
| None is breached at its decided width | lowest margin USB: price **58.40** vs decided **58.06** | *[measured 2026-09-25 ~01:00 UTC]* — prices move; the guard in scope item 4 exists for the day this is false |
| Why the fallback wins | `agents/monitor/reconcile.py:_create_broker_position` writes `stop_pct = settings.default_stop_pct` (0.05), `degraded: True`, `provenance: reconciled-from-broker`; S225 measured **55 of 55** stops ever placed came from broker-adopted keys | *[measured 2026-09-25]* read + DL-200 |
| Three readers of the width | `contracts/positions.py:_stop_lot` (analyst's stop check), `agents/execution/broker_stop_thresholds.py:_stop_pct` (placement), `agents/monitor/domain/positions.py:68` (watchdog) | *[measured 2026-09-25]* grep of `stop_pct` readers |
| Execution only places *missing* stops | `broker_stops.py`: `if threshold.position_ref in protected_refs: continue`; the `Broker` port has `submit`, `submit_stop`, `cancel` and **no replace** | *[measured 2026-09-25]* read |
| 🪤 **Alpaca refuses to replace an `accepted` order** | `PATCH /v2/orders/{id}` → **`422 {"code":42210000,"message":"cannot replace order in accepted status"}`** | *[measured 2026-09-25 ~01:05 UTC]* planner probe on paper: a 1-share buy stop on F at $50, placed after the close, replaced, then cancelled; 0 F orders left |
| When an order leaves `accepted` | an order placed after the close shows `status=new` with `submitted_at` **08:00 UTC** the next day (CSCO, SCHW placed ~22:40 UTC 09-23 → `2026-09-24T08:00:26`) | *[measured 2026-09-25]* open orders. So during the 22:30 UTC run every stop placed on an **earlier** day is `new` |
| What a successful replace returns | *[ASSUMED — per Alpaca's documentation, not measured]* a **new** order id; the old order moves to status `replaced` with `replaced_by`; the new one carries `replaces` | **Owed by the planner before merge:** a replace on a `new` throwaway order after 08:00 UTC. If it differs, the adapter changes, not the design |
| `replaced` in our lifecycle | **absent**: `TERMINAL_BROKER_ORDER_STATUSES = {canceled, cancelled, expired, filled, rejected}` (`contracts/broker_lifecycle.py:46`) | *[measured 2026-09-25]* read. Without it a replaced order reads live forever |
| Graph vocabulary | `BrokerStopOrder` has **no** declared properties; `Fill` **does** (S225 added `derived_from`) | *[measured 2026-09-25]* `orchestration/packs/trading_graph_vocabulary.json` `properties` keys |

---

## Scope — and what is deliberately NOT here

1. **One resolver, failing test first.** `contracts/stop_width.py` exposes
   `decided_stop_pct(graph, position_node, *, fallback) -> (stop_pct, source)` with `source` in
   `lineage | position | fallback`. For a Position with `provenance == "reconciled-from-broker"`, it
   finds the most recent filled buy `Fill` for the ticker whose `quantity` **and**
   `broker_price_cents` equal the Position's `quantity` and `opened_price_cents`, follows its
   `OrderIntent` edge, and returns that `stop_pct` as `lineage`. No exact match → `fallback` (never a
   guess across lots). A non-adopted Position keeps its own `stop_pct` as `position`. The three
   readers above call it; no reader computes a width on its own.
2. **The `Broker` port gains `replace_stop(broker_order_id, stop_price_cents)`** returning the new
   order: Alpaca adapter (`PATCH /v2/orders/{id}` with `stop_price`), paper broker, and the port
   protocol. The paper broker models the 422 for an `accepted` order.
3. **`replaced` is a lifecycle state.** `contracts/broker_lifecycle.py` treats `replaced` as terminal
   for liveness (`EXEC-OBS-05`: asked in exactly one place). The old `BrokerStopOrder` fact gets a
   `replaced_at` / `replaced_by` marker, never a deletion (`EXEC-OBS-03`). The new fact records
   `replaces`, the decided `stop_pct`, `stop_pct_source`, and `derived_from`.
4. **Execution replaces a mismatched live stop.** In `place_broker_stops`, for a protected position
   whose live stop price differs from the resolved stop price by **≥ 1 cent**, call `replace_stop`.
   Guards: (a) skip an order that is not `new` and record why (an `accepted` stop was placed this run
   and is already at the decided width); (b) **never move a stop to or above the current price**.
   Keep the existing stop and raise a warning `Fault` naming the ticker, the decided stop and the
   price, so the operator decides (capital risk is theirs); (c) a replace that fails leaves the old
   stop live and records a fault. It is retried next run, never cancelled.
5. **Law cycle** as answered above, plus `DL-223` for the design decisions.

### Out of scope (do NOT build this sprint)

- **Rewriting existing `Position` nodes.** They are facts. The resolver reads lineage at read time.
- **Changing how the PM decides `stop_pct`**, the stop mode, or any tunable value.
- **Take-profit or time exits.** ADR-0017 retired them.
- **Lot accounting.** If a holding ever spans several buys, the resolver returns `fallback` and says
  so. Designing lot-level stops is a separate question.
- **Adoption writing lineage.** `_create_broker_position` stays as is. The resolver is the one fix, so
  there is one path to reason about (DL-223 records why).
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Cancel the old stop, then place a new one.** Rejected: it opens an unprotected window, and on
  Alpaca the cancelled order's quantity is released asynchronously, so an immediate new sell stop can
  be refused for insufficient quantity. That leaves the position unprotected until the next run.
- **Fix it at adoption only** (`_create_broker_position` reads lineage). Rejected: the 25 existing
  Positions keep `stop_pct = 0.05` because the node already exists (`merge_node` returns it
  untouched), and three readers would still each need to trust the node.
- **Fix it in execution only.** Rejected: the analyst's stop check and the monitor's watchdog would
  keep reading 5 %, so the three would disagree about the same position (DL-208's failure).
- **A one-off script to re-place the 25 stops by hand.** Rejected: the graph's stop facts would
  diverge from the broker, and every future adopted buy would repeat the defect.
- **Move a stop to or above the market when the decided width is already breached.** Rejected: that
  is an immediate market exit taken by a reconciliation routine. Exits are ADR-0017's, and a capital
  decision on the day it happens is the operator's.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` as DL-223, with rejected alternatives, BEFORE implementing.**

1. **The lineage match rule** — exact quantity **and** price against the most recent filled buy, as
   measured 25/25. Record why "nearest" or "quantity only" were rejected.
2. **The replace tolerance** — ≥ 1 cent. A stop computed from the same inputs is deterministic, so any
   difference is real. Record whether rounding (`stop_price_cents`) can produce a one-cent flutter and
   how the test proves it cannot.
3. **Where `replace_stop` lives in the adapters** without growing `alpaca.py` (189) or
   `paper_broker.py` (183) past 200.

🪤 **DL-221 belongs to S229 and DL-222 is the measurement.** Take DL-223 and re-check at merge.

---

## Blast radius — measured 2026-09-25

| What | Detail |
| --- | --- |
| Files changed | new `contracts/stop_width.py`; `contracts/positions.py` (187), `contracts/broker_lifecycle.py` (162), `contracts/broker_stops.py` (105); execution `broker.py` (124), `alpaca.py` (189) or `alpaca_orders.py` (136), `paper_broker.py` (183), `broker_stop_thresholds.py` (142), `broker_stops.py` (185), `broker_stop_actions.py` (131), `broker_stop_writes.py` (104); monitor `domain/positions.py`; the execution law book + test plan; tests |
| Agents affected | execution, monitor, analyst (through `contracts/`). None imports another |
| Contract change? | **yes** — the law cycle above is mandatory |
| Graph vocabulary change? | **only if you add a declared property to `Fill`** (S225 did, and it forced a full `up`). `BrokerStopOrder` properties are undeclared. State which in the handback |
| New env keys / tunables | none expected. The fallback keeps its existing `PARAM` row |
| Deploy implication | `contracts/` is in every image → **rebuild all**; image-only retag unless the vocabulary pack moved (then full `up`). **Operator approval**, with the list of stops the first run will replace |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record DL-223.**
3. **Plant the failing tests first** (A1, A4, A6) and watch them fail. Paste the red output.
4. **Implement** scope items 1–4.
5. **Law cycle** — clause, test-plan rows, docstring citations, rollups, drift row.
6. **Prove the guards can fail (DL-70)**: make the resolver ignore lineage (A1 must go red); let
   execution replace an `accepted` order (A7 red); drop the at-or-above-price guard (A8 red).
   Restore each.
7. **`make ci` green** — every step, **redirected to a file, never piped**.
8. **Fill the handback sections.**

---

## Test plan

Fixture: the live shape, in an in-memory graph. A broker-adopted Position
`broker:USB:16:6050` (`stop_pct 0.05`, `provenance reconciled-from-broker`), its lineage Fill
`pm-run-<hex>:USB:buy` (`quantity 16`, `broker_price_cents 6050`, `broker_status filled`) → OrderIntent
`stop_pct 0.0402588750356905`, and a live `BrokerStopOrder` at **5747** cents, `status new`.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 the resolver returns the decided width | the fixture | `(0.04025…, "lineage")`, not `(0.05, …)` |
| A2 | an older lot does not match | an earlier USB buy with `quantity 15` | still the 16-share lineage |
| A3 | 🪤 no exact match → fallback, said so | Position quantity 32 (two lots) | `(0.05, "fallback")` |
| A4 | 🎯 all three readers agree | the fixture | analyst threshold, execution threshold and monitor watchdog report the same `stop_pct` and stop price (**5806** cents) |
| A5 | a non-adopted Position keeps its own width | a fill-path Position with `stop_pct 0.0713` | `(0.0713, "position")` |
| A6 | 🎯 a mismatched `new` stop is replaced in place | the fixture; paper broker | one `replace_stop` call to **5806**; the old fact carries `replaced_at`/`replaced_by`; one new live fact with `replaces`, `stop_pct_source=lineage`; **no cancel call**; exactly one live stop throughout |
| A7 | 🪤 an `accepted` stop is not replaced | the fixture with the live stop `accepted` | no replace call; reason recorded |
| A8 | 🪤 never at or above the market | price **58.00** against a decided **58.06** | no replace; a warning `Fault` naming USB, 58.06 and 58.00; the 5 % stop stays live |
| A9 | a failed replace keeps the old stop | paper broker raises on replace | old stop live and not marked; fault recorded; retried next run |
| A10 | `replaced` is terminal in the one liveness question | an order with status `replaced` | not live (`EXEC-OBS-05`) |
| A11 | a matching stop is left alone | stop already at 5806 | zero broker calls |
| A12 | idempotent across runs | run placement twice | one replace total |

---

## Success factors

- [ ] On the fixture, the resting stop moves from 57.47 to **58.06** by one replace, with no cancel and
      no unprotected moment (A6).
- [ ] Analyst, monitor and execution read one resolver and agree (A4).
- [ ] The fallback is used only without exact lineage, and every stop fact records its `stop_pct_source`.
- [ ] `accepted` orders and at-or-above-price moves are refused with a recorded reason (A7, A8).
- [ ] Law cycle done: clause(s), test-plan rows, docstrings, both rollups, drift row.
- [ ] DL-223 recorded with rejected alternatives.
- [ ] Every guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **Reconstructing lots from Fills looks easy and is wrong.** Resting-stop records are `Fill`s too, and
they carry the **placement** date, so "buys since the last sell" reads every held ticker as empty.
The planner hit this while measuring. Match the one Fill that equals the holding; do not replay history.
🪤 **Fills from verification runs have no `OrderIntent` edge.** Only `source_run_id` = `pm-run-*` fills
are production lineage.
🪤 **`stop_pct_source=position` has hidden this defect since S225**: it was true (the width came from
the Position) and the Position's own value was the fallback. The new source must say `lineage` or
`fallback`, never a word that reads as both.
🪤 **A replace that returns a new order id breaks every lookup keyed by the old id.** The stale-order
sweep and the status refresh must learn the new id through the `replaces` / `replaced_by` link, or the
next run flags the old id as a mismatch.
🪤 **Your worktree has no `.env` and no network.** The Alpaca adapter is proven by its contract with the
paper broker and a recorded response shape. The live replace is the planner's check.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Near the block: `alpaca.py` **189**, `contracts/positions.py` **187**, `broker_stops.py` **185**,
  `paper_broker.py` **183**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — the 1-cent tolerance is a named constant with a comment, or a tunable if the law
  says so.
- Faults, not silent failure — every refused or failed replace is a recorded fault.
- `make ci` **every step** green, **100.00 % coverage floor**, **redirected to a file, never piped**.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree. **State which tree you ran in.**

---

## Sequencing after merge

1. **Planner, before merge:** replace a `new` throwaway paper order after 08:00 UTC and confirm the
   response shape the adapter assumes (new id, old `replaced`, `replaced_by`/`replaces`).
2. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the worktree at the proven
   commit; check the printed SHA against `git rev-parse HEAD`.
3. Merge to `main` locally and push. Not from the branch's own worktree. Post-merge CodeQL.
4. **Deploy with operator approval**: rebuild all images (`contracts/` changed); image-only retag unless
   the vocabulary pack moved. Present the list of stops the first run will replace (re-measured on the
   day, since prices move) before asking.
5. **Functionality check on the first run after deploy:** Alpaca shows each mismatched stop at its
   decided price (re-measure the list; on 2026-09-25 it was 9), the old orders `replaced`, no
   `UnprotectedPosition` fault, `audit_broker_graph.py` A1/A2 clean, and a second run replaces nothing.
   Record it in `docs/laws/functionality-checks.md`.

---

## Handover — paste this to Codex

```text
Sprint 230 — a protective stop rests where the PM decided it, not at the fallback.
Spec: docs/sprints/sprint-230-a-stop-rests-where-the-pm-decided.md (read all of it).

Branch: sprint-230-a-stop-rests-where-the-pm-decided, in its own worktree. Never main.
S229 is being built in parallel: rebase onto main after it merges; expect conflicts in
docs/laws/ledger.md, docs/laws/INDEX.md, docs/laws/drift-register.md, docs/design-log.md.

The defect (measured on the live broker, 2026-09-25): all 25 protective stops rest 5.00 % below entry.
The PM decided 3.90–7.29 % for the 9 buys since 2026-09-05. Broker-adopted Positions carry
stop_pct=0.05 (agents/monitor/reconcile.py:_create_broker_position), and every stop is placed from
one (S225: 55/55).

MUST RULE before any code: read agents/execution/laws/{laws.md,test-plan.md} (EXEC-OBS-03,
EXEC-OBS-05, EXEC-DEP-04, EXEC-NEV-07, PARAM broker_stop_fallback_stop_pct), the monitor book
(MON-NEV-05, MON-STA-02), the analyst book's held-stop clauses, conventions.md, drift-register.md.
Fill the Law reading record first.

Law-cycle answer: YES (contracts/ changes; execution gains "a mismatched stop is replaced").
Clause(s), test-plan rows, docstring citations, ledger.md + INDEX.md rollups, drift row.

Build:
1. contracts/stop_width.py: decided_stop_pct(graph, position_node, *, fallback) -> (pct, source),
   source in lineage|position|fallback. Adopted Position -> the most recent filled buy Fill
   (source_run_id pm-run-*) with EXACTLY equal quantity AND broker_price_cents -> its OrderIntent
   stop_pct. No exact match -> fallback. The three readers (contracts/positions.py _stop_lot,
   execution broker_stop_thresholds._stop_pct, monitor domain/positions.py:68) all call it.
2. Broker.replace_stop(broker_order_id, stop_price_cents): Alpaca PATCH /v2/orders/{id}; paper broker
   too, and it must return 422 for an accepted order (measured on Alpaca paper).
3. contracts/broker_lifecycle.py: "replaced" is terminal for liveness. Old BrokerStopOrder gets
   replaced_at/replaced_by (marker, never delete); new fact records replaces + stop_pct_source.
4. place_broker_stops: a protected position whose live stop differs from the resolved price by
   >= 1 cent -> replace_stop. Skip non-"new" orders with a reason. NEVER move a stop to or above the
   current price: keep the old stop, raise a warning Fault. A failed replace keeps the old stop live.

Order: DL-223 -> red tests A1/A4/A6 (paste) -> implement -> law cycle -> DL-70 plants (resolver
ignores lineage; replace an accepted order; drop the price guard: each must go red; restore) ->
make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- cancel-then-place. There must never be a moment with no live stop.
- rewrite existing Position nodes, or change _create_broker_position.
- reconstruct lots by replaying Fills: resting-stop Fills carry the placement date. Match the one Fill.
- guess across lots: no exact match means fallback, and say so.
- change how the PM decides stop_pct, or any tunable value.
- grow alpaca.py (189), contracts/positions.py (187), broker_stops.py (185), paper_broker.py (183)
  past 200: split.
- claim a live Alpaca proof from the worktree (no .env, no network). The planner does the live replace.
- pin a version: PATCH, next available at merge, uv.lock staged with it.
State in the handback whether you added a declared property to Fill (that makes the deploy a full up).

Handback: Law reading record, Test plan results, Closeout (red then green, DL-70 plants, line counts,
make ci file + exit code, make gate-ran from the worktree at the full SHA), Return notes. Status: BUILT,
and this sprint's README.md row leads with BUILT in the same commit. Anything not met: "not done".
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

Written before the first code change. Read in full: `agents/execution/laws/{laws.md,test-plan.md}`
(LOCKED v1.8), `agents/monitor/laws/{laws.md,test-plan.md}` (LOCKED v1.1), the analyst book's stop
clauses and PARAM rows (`agents/analyst/laws/laws.md`, grep-read for `stop`, `held`, `breach`, `exit`,
`Position`), `docs/laws/conventions.md`, `docs/laws/drift-register.md`.

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| new `contracts/stop_width.py` | execution, monitor, analyst books | `EXEC-OBS-03` (reconstructable stop lifecycle), execution `PARAM broker_stop_fallback_stop_pct` ("no PM stop lineage"), monitor `PARAM default_stop_pct` ("if OrderIntent lineage is missing stop_pct"), `MON-NEV-05` | **Yes.** Both fallback PARAM rows already say the fallback is for *missing lineage*, so the resolver reads lineage first and names the fallback `fallback`, never `position`. The monitor's own adoption-time fallback (recorded on the Position) is what an adopted Position with no lineage falls back to, so the three readers agree by construction; execution's PARAM covers only a Position that records no width at all (unchanged behaviour). |
| `contracts/positions.py` `_stop_lot` (analyst's held-stop inputs) | analyst book | none: the analyst book has no held-position stop clause | Recorded as a silence (below). The reader changes to the resolver; the analyst's raising behaviour for a lot with no width is kept. |
| `contracts/broker_lifecycle.py`, `contracts/broker_stops.py` | execution `EXEC-OBS-03`, `EXEC-OBS-05` | liveness asked in one place; cancellation (and now replacement) is a marker, never a deletion | **Yes.** `replaced` joins `TERMINAL_BROKER_ORDER_STATUSES` and a `replaced_at` marker ends a fact's liveness inside `is_live_broker_stop_fact`, the one place liveness is asked. No second liveness predicate. |
| `agents/execution/broker_stop_*`, new replace module | execution `EXEC-OBS-03`, `EXEC-NEV-07`, `EXEC-DEP-04`, `EXEC-IDN-03` | stop placement is an immutable fact; stops never weakened by degraded posture; broker cancel + stop placement dependency; execution alone writes `BrokerStopOrder` | **Yes.** The replacement runs inside `place_broker_stops`, which `EXEC-NEV-07` already guarantees runs in degraded posture, so no posture branch is added. New facts go on `BrokerStopOrder` only (undeclared props), so no `Fill` vocabulary change. |
| `agents/execution/broker.py`, `alpaca*.py`, `paper_broker.py` | execution `EXEC-DEP-03/04`, CAP block | the broker dependency lists `place_stop_order`, `cancel_order` — **not** `replace_order` | **Yes.** `EXEC-DEP-04` and the CAP `broker.operations` list must gain order replacement in the law cycle. |
| `agents/monitor/domain/positions.py` | monitor `MON-NEV-05`, `MON-STA-02`, `MON-IDM-01` | reads fills/OrderIntents, never mutates them; exit rules are pure functions of position props + price | Reader only: `exit_position` takes the graph and reads through the resolver. No monitor write changes; `_create_broker_position` untouched. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **Yes, both.**
`contracts/` gains `stop_width.py`, a `replaced` terminal status and a `replaced_at` liveness marker;
execution gains the guarantee that a live stop resting away from its decided price is replaced in
place, never cancel-then-place. Owed: a new execution clause (`EXEC-OBS-06`), `EXEC-DEP-04` + CAP
widened for order replacement, the fallback `PARAM` rationale reworded, test-plan rows, docstring
citations, both rollups, and a drift row.

**Contradictions found between a law and this spec:** none that stop the sprint. One wording point: the
spec's port signature is `replace_stop(broker_order_id, stop_price_cents)`. The execution law says every
broker call carries a stable key (`EXEC-NEV-03` is about submissions, and `BrokerStopOrder.key` *is* the
stop's `client_order_id`). The port therefore takes a keyword `idempotency_key` for the new order's
`client_order_id`, so the replacement's key equals its graph fact's key and the refresh and sweep find it
without following a link. Recorded in DL-223.

**Laws found silent where a decision was needed:** (1) The **analyst book has no held-position stop
clause at all** — no `stop_breached`, no ADR-0017 reference — although `contracts/positions.py`
feeds the analyst's held-stop check. Recorded as **DRIFT-074** (OPEN); not amended here (the analyst
book is LOCKED and the silence predates this sprint). (2) No execution clause said what happens when a live stop's
price differs from its decided price; `EXEC-OBS-06` fills it. (3) `EXEC-DEP-04`/CAP did not declare order
replacement.

**Clauses that were ⬜ and are now proven:** none were ⬜ among the binding set (`EXEC-OBS-03`,
`EXEC-OBS-05`, `EXEC-DEP-04`, `EXEC-NEV-07` are 🟩). `MON-NEV-05` stays ⬜ — this sprint adds no test
that proves the monitor never mutates another agent's nodes. New: `EXEC-OBS-06` (see Test plan results).

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_the_resolver_returns_the_width_the_pm_decided` | `tests/test_stop_width.py` | 🟩 pass (red first) | `EXEC-OBS-06` |
| A2 | `test_an_older_lot_of_another_size_does_not_match` | `tests/test_stop_width.py` | 🟩 pass | `EXEC-OBS-06` |
| A3 | `test_no_exact_match_falls_back_and_says_so` | `tests/test_stop_width.py` | 🟩 pass | `EXEC-OBS-06` |
| A4 | `test_all_three_readers_agree_on_the_decided_stop` | `tests/test_stop_width.py` | 🟩 pass (red first) | `EXEC-OBS-06` |
| A5 | `test_a_fill_path_position_keeps_its_own_width` | `tests/test_stop_width.py` | 🟩 pass | `EXEC-OBS-06` |
| A6 | `test_a_mismatched_new_stop_is_replaced_in_place` | `agents/execution/tests/test_broker_stop_realign.py` | 🟩 pass (red first) | `EXEC-OBS-06`, `EXEC-OBS-03` |
| A7 | `test_an_accepted_stop_is_not_replaced` | `agents/execution/tests/test_broker_stop_realign.py` | 🟩 pass | `EXEC-OBS-06` |
| A8 | `test_a_stop_is_never_moved_to_or_above_the_market` | `agents/execution/tests/test_broker_stop_realign.py` | 🟩 pass | `EXEC-OBS-06` |
| A9 | `test_a_failed_replace_keeps_the_old_stop_and_retries`; `test_a_failed_replace_leaves_no_marker` | `agents/execution/tests/test_broker_stop_realign.py` | 🟩 pass | `EXEC-OBS-06`, `EXEC-OBS-03` |
| A10 | `test_a_replaced_order_is_not_live`; `test_a_replaced_at_marker_ends_the_fact_without_deleting_it` | `tests/test_broker_stop_replaced.py` | 🟩 pass | `EXEC-OBS-05`, `EXEC-OBS-03` |
| A11 | `test_a_matching_stop_is_left_alone` (asserts zero `replace_stop` calls **and** zero `fills()` reads) | `agents/execution/tests/test_broker_stop_realign.py` | 🟩 pass | `EXEC-OBS-06` |
| A12 | `test_replacement_is_idempotent_across_runs` | `agents/execution/tests/test_broker_stop_realign.py` | 🟩 pass | `EXEC-OBS-06` |

**Tests added beyond the plan:** `tests/test_stop_width.py::test_an_exact_buy_that_decided_no_width_is_not_lineage`,
`::test_a_verification_fill_is_never_lineage` (the spec's trap: only `pm-run-*` fills are lineage),
`::test_a_position_with_no_width_needs_a_fallback`; `tests/test_broker_stop_replaced.py::test_the_free_key_skips_every_existing_attempt`;
`agents/execution/tests/test_broker_stop_replace_adapters.py` — the Alpaca PATCH shape against a recorded
response (`EXEC-DEP-04`), Alpaca's 422 surfacing verbatim, a rejected replacement raising, the paper
broker modelling the 422 and an unknown order, unreadable broker orders (no replace, fault) and an order
the broker does not list (skipped as `unknown`, fault). Two existing assertions in
`test_alpaca_broker.py` gained `order_status=` because `fill_from_order` now carries the raw status.

---

## Closeout — evidence

**Status:** BUILT (built as **0.111.02**, PATCH over `main`'s 0.111.01; `uv.lock` updated with it). 🩹 *Planner, at the merge-in of `main` (2026-09-25): S229 merged first as `0.111.02`, so this branch is re-bumped to **0.111.03**.*

**Tree the proofs ran in (and `.env` present?):** the isolated git worktree
`.claude/worktrees/agent-adc55cf3a03d1feb8` on branch `sprint-230-a-stop-rests-where-the-pm-decided`,
**no `.env`** (checked: `ls .env` → no such file), no network. No live Alpaca, Azure or Postgres call was made.

**Result:** on the live-shape fixture the resolver returns `(0.0402588750356905, "lineage")` instead of
`(0.05, …)`; the analyst's held-stop inputs, execution's placement threshold and the monitor's watchdog all
read `stop_pct 0.0402588750356905` and a **5806**-cent stop; the resting 57.47 stop moves to **58.06** by one
`replace_stop` call with no cancel and exactly one live stop before and after; the old fact carries
`replaced_at` / `replaced_by`, the new one `replaces`, `stop_pct_source=lineage`, `derived_from=active_position`.
`accepted` orders, moves to or above the price, unreadable/unlisted orders and broker refusals all keep the
old stop live and raise a warning fault. A second run replaces nothing.

**Files changed:** new `contracts/stop_width.py`, `agents/execution/broker_stop_realign.py`,
`agents/execution/alpaca_replace.py`, `agents/execution/paper_broker_orders.py`; changed
`contracts/{positions,broker_lifecycle,broker_stops}.py`, `agents/execution/{broker,alpaca,alpaca_orders,paper_broker,broker_stop_thresholds,broker_stop_types,broker_stop_writes,broker_stops}.py`,
`agents/monitor/{decide.py,domain/positions.py}`; tests: new `tests/test_stop_width.py`,
`tests/test_broker_stop_replaced.py`, `agents/execution/tests/{stop_realign_helpers,test_broker_stop_realign,test_broker_stop_replace_adapters}.py`,
changed `agents/execution/tests/{broker_protocol_helpers,test_alpaca_broker}.py`; law: execution `laws.md`
(v1.9) + `test-plan.md`, `docs/laws/{ledger,INDEX,drift-register}.md`; `docs/design-log.md` (DL-223);
`pyproject.toml`, `uv.lock`; this spec and its `README.md` row. **Not touched:** `_create_broker_position`,
any `Position` node, the PM's stop decision, any tunable value, and every S229 file.

**Design decisions:** recorded as [`DL-223`](../design-log.md) — one resolver with an exact quantity **and**
broker-price lineage match (nearest / quantity-only / lot replay rejected); an adopted Position without
lineage keeps its adoption-time width and says `fallback`, so the three readers agree whatever the tunables
say; a 1-cent tolerance as a named constant (deterministic integer cents, proven flutter-free by A11/A12);
`replace_stop(broker_order_id, stop_price_cents, *, idempotency_key)` — the keyword names the new order's
`client_order_id`, equal to the new fact's key, so the refresh and the sweep find it without a link; the raw
broker status rides on `BrokerFill.order_status`; the adapters split into `alpaca_replace.py` and
`paper_broker_orders.py`.

**Proof — the red run first** (before any implementation; the capability did not exist):

```text
$ uv run pytest tests/test_stop_width.py::test_the_resolver_returns_the_width_the_pm_decided \
    tests/test_stop_width.py::test_all_three_readers_agree_on_the_decided_stop ... --no-cov -q
__________________ ERROR collecting tests/test_stop_width.py __________________
E   ModuleNotFoundError: No module named 'contracts.stop_width'
ERROR tests/test_stop_width.py
1 error in 8.05s          (exit 4 — A1 and A4 cannot even import the resolver)

$ uv run pytest agents/execution/tests/test_broker_stop_realign.py::test_a_mismatched_new_stop_is_replaced_in_place --no-cov -q
E   TypeError: PaperBroker.__init__() got an unexpected keyword argument 'stop_order_status'
FAILED agents/execution/tests/test_broker_stop_realign.py::test_a_mismatched_new_stop_is_replaced_in_place
1 failed in 2.85s         (exit 1 — no broker can report `new`, and no port can replace)
```

The behavioural reds are the DL-70 plants below (A1 reads `0.05 != 0.0402588750356905`).

**Proof — the green run:**

```text
$ uv run pytest tests/test_stop_width.py tests/test_broker_stop_replaced.py \
    agents/execution/tests/test_broker_stop_realign.py \
    agents/execution/tests/test_broker_stop_replace_adapters.py --no-cov -q -rA
PASSED tests/test_stop_width.py::test_the_resolver_returns_the_width_the_pm_decided
PASSED tests/test_stop_width.py::test_all_three_readers_agree_on_the_decided_stop
PASSED tests/test_stop_width.py::test_an_older_lot_of_another_size_does_not_match
PASSED tests/test_stop_width.py::test_no_exact_match_falls_back_and_says_so
PASSED tests/test_stop_width.py::test_a_fill_path_position_keeps_its_own_width
PASSED tests/test_stop_width.py::test_an_exact_buy_that_decided_no_width_is_not_lineage
PASSED tests/test_stop_width.py::test_a_verification_fill_is_never_lineage
PASSED tests/test_stop_width.py::test_a_position_with_no_width_needs_a_fallback
PASSED tests/test_broker_stop_replaced.py::test_a_replaced_order_is_not_live
PASSED tests/test_broker_stop_replaced.py::test_a_replaced_at_marker_ends_the_fact_without_deleting_it
PASSED tests/test_broker_stop_replaced.py::test_the_free_key_skips_every_existing_attempt
PASSED agents/execution/tests/test_broker_stop_realign.py::test_a_mismatched_new_stop_is_replaced_in_place
PASSED agents/execution/tests/test_broker_stop_realign.py::test_an_accepted_stop_is_not_replaced
PASSED agents/execution/tests/test_broker_stop_realign.py::test_a_stop_is_never_moved_to_or_above_the_market
PASSED agents/execution/tests/test_broker_stop_realign.py::test_a_failed_replace_keeps_the_old_stop_and_retries
PASSED agents/execution/tests/test_broker_stop_realign.py::test_a_failed_replace_leaves_no_marker
PASSED agents/execution/tests/test_broker_stop_realign.py::test_a_matching_stop_is_left_alone
PASSED agents/execution/tests/test_broker_stop_realign.py::test_replacement_is_idempotent_across_runs
PASSED agents/execution/tests/test_broker_stop_replace_adapters.py::test_alpaca_replace_patches_the_stop_price_under_the_new_key
PASSED agents/execution/tests/test_broker_stop_replace_adapters.py::test_alpaca_refusal_carries_the_broker_message
PASSED agents/execution/tests/test_broker_stop_replace_adapters.py::test_alpaca_rejected_replacement_raises
PASSED agents/execution/tests/test_broker_stop_replace_adapters.py::test_paper_broker_models_alpacas_refusal_of_an_accepted_stop
PASSED agents/execution/tests/test_broker_stop_replace_adapters.py::test_unreadable_broker_orders_leave_every_stop_and_fault
PASSED agents/execution/tests/test_broker_stop_replace_adapters.py::test_a_stop_the_broker_does_not_list_is_skipped_as_unknown
24 passed in 1.30s
```

**Guards planted** (each planted, watched red, restored; restoration confirmed by `grep -c "DL-70 PLANT"` = 0
in both files and the original line back in place):

| Guard | Plant | Test | Red output |
| --- | --- | --- | --- |
| Resolver reads lineage | `contracts/stop_width.py`: `decided = None` instead of `_lineage_stop_pct(...)` | A1 | `AssertionError: assert DecidedStop(s...ce='fallback') == (0.0402588750...05, 'lineage')` · `At index 0 diff: 0.05 != 0.0402588750356905` — 1 failed |
| Never replace an `accepted` order | `broker_stop_realign.py`: `if status is None:` instead of `if status != REPLACEABLE_ORDER_STATUS:` | A7 | `AssertionError: assert [('paper:stop...6:USB', 5806)] == []` — replace was called — 1 failed |
| Never to or above the price | `broker_stop_realign.py`: `if False:` instead of the `decided * quantity >= market_value` guard | A8 | `AssertionError: assert [('paper:stop...6:USB', 5806)] == []` — the stop was moved above 58.00 — 1 failed |

**Module line counts** (all under 200): `contracts/stop_width.py` 115 (new), `contracts/positions.py` 190
(was 187), `contracts/broker_lifecycle.py` 168 (162), `contracts/broker_stops.py` 117 (105);
`agents/execution/broker.py` 133 (124), `alpaca.py` **184** (was 189 — the HTTP-error helpers moved out),
`alpaca_orders.py` 146 (136), `alpaca_replace.py` 65 (new), `paper_broker.py` **177** (was 183 — rejection
and replay moved out), `paper_broker_orders.py` 86 (new), `broker_stop_thresholds.py` 137 (142),
`broker_stops.py` 189 (185), `broker_stop_actions.py` 131 (unchanged), `broker_stop_writes.py` 119 (104),
`broker_stop_realign.py` 180 (new), `broker_stop_types.py` 67 (65); `agents/monitor/domain/positions.py` 93
(88), `agents/monitor/decide.py` 59. Tests: `stop_realign_helpers.py` 176, `test_broker_stop_realign.py` 156,
`test_broker_stop_replace_adapters.py` 172, `test_alpaca_broker.py` 195, `broker_protocol_helpers.py` 52,
`tests/test_stop_width.py` 143, `tests/test_broker_stop_replaced.py` 85.

**`make ci`:** `make ci > <scratchpad>/ci.txt 2>&1; echo $?` → **exit 0** (redirected, never piped).
**3178 passed, 6 skipped**, **100.00 %** coverage (TOTAL 18099 statements / 3940 branches, 0 missed);
ruff check + format clean; mypy "no issues found in 1010 source files"; import-linter **4 kept, 0 broken**;
module size, module header, law coverage, PARAM/settings sync, sprint status, markdown links and version
scheme steps passed; dependency audit "No unaccepted vulnerabilities; 1 accepted advisory re-checked"
(PYSEC-2026-2447, DL-184); detect-secrets tracked **Passed**, untracked **Passed**. Re-run on the final
tree after the handback edits (`ci2.txt`): **exit 0**, **3178 passed, 6 skipped**, **100.00 %**, 4 kept /
0 broken, audit and both detect-secrets steps passed, and the sprint-status step reads this spec as `BUILT`.

**`make gate-ran`:** **not done by the builder.** It needs the pushed branch's remote `CI` and
`Security Findings` runs to conclude, and it must be run from this worktree at the proven full SHA. Owed
by the planner before merge (spec *Sequencing after merge*, step 2).

**Declared `Fill` property added?** **No.** The new markers (`replaced_at`, `replaced_by`,
`replaced_by_broker_order_id`, `replaces`, `replaces_broker_order_id`) are on `BrokerStopOrder`, which has
no declared properties; the new stop `Fill` carries only already-declared keys. `BrokerFill.order_status`
is an in-process field and is never written to the graph. Deploy is an image rebuild + retag, not a full `up`.

**Not met / verified failing:** (1) `make gate-ran` — not done (above). (2) The live Alpaca replace probe
(new id, old `replaced`, `replaced_by`/`replaces`) — not done; the worktree has no network, it is the
planner's pre-merge check. The Alpaca adapter is proven only against a recorded response shape. (3)
`MON-NEV-05` stays ⬜. (4) DRIFT-074 (the analyst book's missing held-stop clause) is recorded OPEN, not
fixed.

---

## Return notes

- **Divergence from the spec's port signature:** `replace_stop(broker_order_id, stop_price_cents, *,
  idempotency_key)`. The keyword is the new order's `client_order_id` (= the new `BrokerStopOrder` key,
  `stop:<ref>:<ticker>#N`), so the status refresh and the stale-order sweep find the replacement by its own
  key and id and never follow a link; the trap about lookups keyed by the old id is closed that way. If the
  planner's live probe shows Alpaca ignoring a caller-supplied `client_order_id` on PATCH, the sweep still
  skips the new order (a non-pipeline key) and the fact still carries the new broker id; only the refresh's
  by-key lookup falls back to the by-order-id lookup it already has.
- **`fallback` semantics (DL-223 §3):** an adopted Position with no exact lineage keeps the width recorded on
  it at adoption (the monitor's `default_stop_pct`) and reports `fallback`; execution's
  `broker_stop_fallback_stop_pct` applies only to a Position with no width at all — which is what execution
  did before, now worded that way in the `PARAM` row. All three readers therefore agree for every Position
  that carries a width.
- **[ASSUMED, worth measuring before deploy]** guard (a) reads raw order status from `broker.fills()`, i.e.
  Alpaca `GET /v2/orders?status=all&limit=500`. A resting stop older than the account's 500 most recent orders
  would not be listed; it is then **skipped loudly** (`StopReplaceSkipped`, `order_status=unknown`), never
  replaced blind. The refresh and the drop sweep already depend on the same window.
- **Out of scope, noted:** the S182 pending-`Fill` path (`filled_entry_stops.py`) still labels an
  `OrderIntent`-derived width `position`, not `lineage`. It has never fired in production (DL-200), and
  changing it would rewrite an S225 test assertion (`test_the_percent_source_does_not_answer_which_lineage_placed_the_stop`).
  A one-line follow-up if wanted.
- A replaced order's old stop `Fill` is refreshed to `broker_status=rejected`, reason `replaced` — the same
  path a cancelled stop already takes (Alpaca's `replaced` maps to the port's `rejected`, as `canceled`
  does); `replaced` is now terminal in `contracts/broker_lifecycle.py`, so a raw `replaced` status can never
  read live.
- **First run after deploy:** each mismatched `new` stop is replaced (9 on 2026-09-25; re-measure). A
  position whose decided stop is at or above its price on the day raises `StopReplaceRefused` (warning) and
  keeps its 5 % stop for the operator to decide.
- **S229 rebase:** `docs/laws/{ledger,INDEX,drift-register}.md` and `docs/design-log.md` will conflict
  textually. This sprint took **DL-223**, **DRIFT-073** and **DRIFT-074** (S229's spec cites DRIFT-068 only)
  — re-check both at merge.
