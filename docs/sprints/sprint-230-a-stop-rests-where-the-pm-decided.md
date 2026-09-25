<!-- Agent: planning | Role: sprint handover -->
# Sprint 230 — a protective stop rests where the PM decided it, not at the fallback

**Phase:** Etalon-first continuous improvement (DL-19) · live defect, ranked above features
**Branch:** `sprint-230-a-stop-rests-where-the-pm-decided`
**Status:** SPEC
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

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| *(builder fills)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(builder fills)*

**Contradictions found between a law and this spec:** *(builder fills)*

**Laws found silent where a decision was needed:** *(builder fills)*

**Clauses that were ⬜ and are now proven:** *(builder fills)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| *(builder fills)* | | | | |

**Tests added beyond the plan:** *(builder fills)*

---

## Closeout — evidence

**Status:** *(builder fills: BUILT)*

**Tree the proofs ran in (and `.env` present?):** *(builder fills)*

**Result:** *(builder fills)*

**Files changed:** *(builder fills)*

**Design decisions:** recorded as [`DL-223`](../design-log.md) — *(builder fills)*

**Proof — the red run first:**

```text
(builder pastes)
```

**Proof — the green run:**

```text
(builder pastes)
```

**Guards planted:** *(builder fills, per guard)*

**Module line counts:** *(builder fills)*

**`make ci`:** *(builder fills: file, exit code, passed/skipped, coverage, dependency audit, detect-secrets)*

**`make gate-ran`:** *(builder fills: worktree path, full SHA, pasted output)*

**Declared `Fill` property added?** *(builder fills: yes/no — decides retag vs full `up`)*

**Not met / verified failing:** *(builder fills)*

---

## Return notes

- *(builder fills)*
