<!-- Agent: planning | Role: sprint handover -->
# Sprint 280 — an order the broker ends after filling part of it is a fill of that part, never a dropped decision

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-280-a-partly-filled-order-is-a-fill-of-its-part`
**Status:** SPEC
**Version:** *next available PATCH at merge* (the prototype took `0.128.02` → `0.128.03`)
**Effort:** M
**Decisions:** [DL-303](../design-log.md) (measured and decided, planner, 2026-10-16) · [work-queue 135](../work-queue.md) · amends `EXEC-OUT-07`, `EXEC-OBS-06`; new `EXEC-TYP-04`

> **Why this bump kind.** A fix: `EXEC-OUT-07` already says only a decision that *did not fill* is
> dropped, and `EXEC-OBS-06` already says the resting stop is the one the PM decided; the code broke
> both on the one partly filled order the fleet has met. No new capability.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 1 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** The amendment this sprint owes is written for you in Appendix section 2: apply it exactly. A clause you believe is wrong is a `drift-register.md` row plus a report |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | `EXEC-OUT-07` is ⬜ today: this sprint proves it for the first time |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the one law-adjacent file you may append to |

Binding sections: execution **`OUT`** (`EXEC-OUT-07`), **`OBS`** (`EXEC-OBS-01`, `EXEC-OBS-06`),
**`STA`** (`EXEC-STA-05`, `EXEC-STA-06`), **`TYP`** (`EXEC-TYP-02`, new `EXEC-TYP-04`), **`NEV`**
(`EXEC-NEV-02`); dispatcher `DSP-OUT-06` (the brief's fills).

### The rule

1. **Before writing code**, read every law file in the map below, whole.
2. Read each agent's `test-plan.md` beside its `laws.md`. Say which clause you rely on is ⬜.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. The law-cycle question is answered below.
5. **Write the Law reading record** (bottom of this file) before your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. A law silent where you needed a decision is a finding: a `drift-register.md` row.
8. Every test cites its clause IDs in its docstring (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes, both.** `contracts/broker_lifecycle.py` gains `fill_quantity_key` and
`BROKER_FILLED_QUANTITY_PROP`; `contracts/stop_width.py` matches on the filled quantity; execution
gains a new property and a new fault. The cycle is owed and written for you: Appendix section 2
amends `EXEC-OUT-07` and `EXEC-OBS-06`, adds `EXEC-TYP-04`, moves the book to v1.15, and gives the
test-plan, ledger and INDEX rows (41 / 67 → **43 / 68**: `EXEC-OUT-07` proven for the first time,
`EXEC-TYP-04` new and proven).

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/execution/alpaca_orders.py`, `broker.py` | `agents/execution/laws/laws.md` + `test-plan.md` | `EXEC-OUT-07`, `EXEC-TYP-02`, `EXEC-NEV-02` (the quantity is never overridden, "subject to broker partial fill") |
| `agents/execution/broker_status_refresh.py`, `reconciliation_store.py`, `order_status_store.py`, new `partial_fill.py` | same | `EXEC-STA-05` (a terminal Fill is never re-read), `EXEC-OUT-07`, `EXEC-OBS-01`, `EXEC-OBS-02` |
| `agents/execution/realized_pnl.py` | same | `EXEC-STA-06` (an unresolvable PnL is recorded once) |
| `contracts/broker_lifecycle.py`, `contracts/stop_width.py`, `agents/execution/filled_entry_stops.py` | same, plus `agents/analyst/laws/laws.md` and `agents/monitor/laws/laws.md` (both read the resolver) | `EXEC-OBS-06`; DL-223 (one stop-width resolver) |
| `agents/monitor/domain/positions.py` | `agents/monitor/laws/laws.md` + `test-plan.md` | `MON-FAIL-03` (a fill without valid lineage) |
| `orchestration/daily_brief_fills.py` | `orchestration/laws/dispatcher/laws.md` + `test-plan.md` | `DSP-OUT-06` (the fills that became known) |
| `orchestration/packs/trading_graph_vocabulary.json` | `docs/laws/conventions.md`; [DL-85](../design-log-archive/INDEX.md) (the fail-closed write guard) | `Fill` is property-checked: an undeclared property raises `VocabularyError` |
| `infra/deploy-agents.ps1` | none (tooling); read `Enable-LlmCandidates`, `Set-AppVocabulary`, `Set-JobVocabulary` | the new step reuses the two read-back setters |

⚠️ **One invariant: `Fill.quantity` stays the ordered quantity.** It is written once at submit and
the store is append-only (`EXEC-STA-05`); every submission, tolerance and drop record reads it as
ordered. If a change of yours would rewrite it, or make `BrokerFill.quantity` mean filled, stop and
report.

---

## Goal

At merge, an order the broker ended (`expired`, `canceled`) after filling part of it is recorded as
a fill of the part that filled: the drop sweep leaves it alone, the refresh settles its `Fill` as
`filled` with `broker_filled_quantity` set to the broker's filled quantity, and the unfilled rest is
told once as an `UnfilledRemainder` warning. Every reader of an executed size (the stop-width match,
an entry stop's lot, a Position drawn from a Fill, the brief's fill line, a sell's realized PnL)
reads the filled quantity, so the share the broker holds carries the PM's decided stop. A new deploy
step, `deploy-agents.ps1 -Action vocabulary`, carries the moved vocabulary to every app and the job
without a full `up`.

## Why (context)

`sched-2026-10-14` bought 2 UNH as a day limit order. Alpaca filled 1 at $401.11 and the order
expired with 1 unfilled. `sched-2026-10-15`'s run-start drop sweep recorded the whole decision as
*dropped unfilled* (`DroppedDecision … qty=2`), the refresh settled the Fill `rejected`, and
reconciliation adopted the share the broker holds as a Position with no lineage
(`broker:UNH:1:40111`, `degraded`), on the monitor's defaults: a 5 % stop where the PM decided
5.65 %, a 10 % target where it decided 4.12 %. The money is protected; the record is wrong, and the
stop resting at the broker is not the one decided. The operator, 2026-10-16: *"deploy them first,
then fix UNH as the next sprint."*

### Measured, 2026-10-16 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| UNH's order | `qty` 2, `filled_qty` 1 at 401.11, `status: expired`, `time_in_force: day` | *[measured 2026-10-16]* `GET /v2/orders/675ec6db-…` (`wq135_unh_stop.py`, `last_reads.txt`) |
| What `main` made of it | `rejected`/`expired`; sweep: `drop_reason`, a `BrokerOrderStatus` drop fact, `DroppedDecision … qty=2`; refresh: `broker_status: rejected` | *[measured 2026-10-16]* the live graph, and `wq135_f1_replay.py` on `main` `75472497` (`f1_before_main_75472497.txt`) reproduces it exactly |
| The adopted share's stop | 0.05, source `fallback`; resting stop $381.05 | *[measured 2026-10-16]* `decided_stop_pct` in the replay; `GET /v2/orders?status=open&symbols=UNH` |
| The PM's decision | `stop_pct` 0.0565, `target_pct` 0.0412 | *[measured 2026-10-16]* `OrderIntent pm-run-99db…:UNH` |
| How often | 1 order of 350 since 2026-06-16 filled in part; 155 filled whole | *[measured 2026-10-16]* `wq135_partials.py`, the whole order history paged |
| The prototype on the same data | no drop; `filled`, `broker_filled_quantity` 1, `broker_price_cents` 40111; one `UnfilledRemainder`; stop 0.0565 `lineage`; an entry-stop plan of 1 share at 0.0565 | *[measured 2026-10-16]* `wq135_f1_replay.py` on `proto-s280` (`f1_prototype.txt`) |
| Readers of an executed size | five: `contracts/stop_width.py::_equals_holding`, `filled_entry_stops.py::_pending_lot`, `monitor/domain/positions.py::position_from_fill`, `orchestration/daily_brief_fills.py::fills_between`, `realized_pnl.py::realized_pnl_props` | *[measured 2026-10-16]* `grep` for `quantity` reads on Fill nodes and `BrokerFill` under `agents/`, `contracts/`, `orchestration/`, `surfaces/` |
| The vocabulary on the fleet (`s279`) | master and the three deliberators `eae68f28`'s; the other 12 apps `v0.125.x`'s; the job `v0.126.00`'s | *[measured 2026-10-16]* every app's `GRAPH_VOCABULARY_B64` decoded and hashed (`deploy-s279-2026-10-16/packs_live.py`) |
| A partial fill is ever `partially_filled` at the next run start | not seen | *[ASSUMED — not measured]* every buy is a day order, which ends by 20:00 UTC; a GTC order could be. Named, not built |

---

## Scope — and what is deliberately NOT here

1. **Tests first** (Test plan, A1 to A21), under the exact names given; the ones the Test plan marks
   red must be red on the unchanged tree.
2. **The broker contract and the Alpaca mapping** (DL-303 D1, D2): `BrokerFill.filled_quantity`,
   `executed_quantity`, `filled_quantity_of`, `status_of(raw, filled_quantity)`.
3. **The refresh** (D3): `Fill.broker_filled_quantity` with the `filled` status; the
   `BrokerOrderStatus` fact carries `filled_quantity`; one `UnfilledRemainder` warning
   (`agents/execution/partial_fill.py`).
4. **One reader of a Fill's executed size** (D4): `contracts.broker_lifecycle.fill_quantity_key`,
   used by the four Fill readers; realized PnL reads `executed_quantity`.
5. **The vocabulary** declares `Fill.broker_filled_quantity`; **the deploy step**
   `-Action vocabulary` (D7).
6. **The law cycle** (D6), written for you in Appendix section 2.
7. **PATCH** bump (D8).

### Out of scope (do NOT build this sprint)

- **The live UNH record.** It stays as written: no hand edit, no correcting write, no re-opening of a
  settled Fill (DL-303 D5; `EXEC-STA-05`).
- **A partly filled `replaced` order**, and a partial sell's own exit bookkeeping beyond its PnL.
- **The newest-500 order list** (work-queue 134).
- **Running the deploy step.** The planner runs it; you never run `pwsh`, `az` or anything in `infra/`.

### The road not taken (LAW-06)

- **`BrokerFill.quantity` means filled.** Rejected: every submission, tolerance and drop record reads
  it as ordered.
- **A new status value (`partial_ended`).** Rejected: every consumer of `filled` (stops, lineage,
  PnL, brief) would have to learn it.
- **Keep `rejected` and add a quantity.** Rejected: the sweep and the refresh would still write the
  decision unfilled.
- **Record the remainder as a drop.** Rejected: the decision filled; a drop on its Fill would count
  it in `ExecutionRun.dropped` and mark it dropped. The remainder is told, not recorded as a drop.
- **Correct the live UNH Fill.** Rejected: an edit of graph truth by hand.
- **A full `up` to carry the vocabulary.** Rejected: it reverts the three live-only settings (the
  manager's wait, three debates at once, the debaters' lock). Setting it on execution alone was also
  rejected: it leaves 12 apps and the job on older packs.

---

## The design decisions — made, and recorded in DL-303

Do not edit `docs/design-log.md`. In short (the entry has the measurements and the rejected options):

1. **D1** `BrokerFill.filled_quantity: int | None = None`; `executed_quantity(fill)` = it when
   given, else `quantity` for `filled` and `partial`, else 0. `quantity` stays ordered.
2. **D2** `status_of` maps `expired`/`canceled`/`cancelled` with a filled quantity above 0 to
   `filled`; `order_status` keeps the broker's end word; `reason` stays `None` for a fill.
   `partially_filled` stays `partial`; `replaced` is untouched.
3. **D3** The refresh writes `broker_filled_quantity` with a `filled` status only; the
   `BrokerOrderStatus` fact carries `filled_quantity`; `report_unfilled_remainder` warns once when
   the filled quantity is below `Fill.quantity`. Once is guaranteed by `EXEC-STA-05`: a Fill settled
   `filled` is never refreshed again, so the call needs no guard of its own.
4. **D4** `fill_quantity_key(fill)` names `broker_filled_quantity` when written, else `quantity`;
   the four Fill readers read through it; realized PnL reads `executed_quantity`.
5. **D5** The live UNH record stays as written.
6. **D6** Execution law v1.15 (Appendix section 2).
7. **D7** `deploy-agents.ps1 -Action vocabulary`.
8. **D8** PATCH.

---

## Blast radius — measured 2026-10-16

| What | Detail |
| --- | --- |
| Files changed | production: `agents/execution/alpaca_orders.py` **163**, `broker.py` **143**, `broker_status_refresh.py` **82**, `order_status_store.py` **48**, `reconciliation_store.py` **162**, `realized_pnl.py` **120**, `filled_entry_stops.py` **174**, new `partial_fill.py` **50**; `contracts/broker_lifecycle.py` **182**, `contracts/stop_width.py` **144**; `agents/monitor/domain/positions.py` **98**; `orchestration/daily_brief_fills.py` **105**; the vocabulary pack; `infra/deploy-agents.ps1`; laws (Appendix section 2); `pyproject.toml`, `uv.lock` |
| Agents affected | execution (the code), monitor (one reader), analyst (reads the shared resolver, no code change), the dispatcher's brief; no agent imports another |
| Contract change? | yes: `contracts/broker_lifecycle.py`, `contracts/stop_width.py`; the law cycle is owed and written |
| Graph vocabulary change? | yes: `Fill.broker_filled_quantity` (additive) |
| New env keys / tunables | none |
| Deploy implication | **`pwsh infra/deploy-agents.ps1 -Action vocabulary`** (all 16 apps and the job, each read back), **then** an image-only retag; no full `up` |
| Rollback | retag to `s279`. The vocabulary stays (additive: the `s279` images never write the new property and read the pack unharmed). Fills settled by the new code keep `broker_filled_quantity`, which the `s279` code does not read: a partly filled Fill settled by S280 would, after a rollback, be matched on its ordered quantity again |

---

## Steps, in order

1. **Read the laws** (MUST RULE) and write the Law reading record.
2. The design decisions are recorded (DL-303). Do not edit `docs/design-log.md`.
3. **Write `agents/execution/tests/partial_fill_helpers.py` and the tests A1 to A21** under the names
   and files below. Run them on the unchanged tree and paste the output: the red/green split must be
   the one the Test plan states.
4. **Apply Appendix section 1** (production) exactly. Change nothing else in production code.
5. **Apply Appendix section 2** (the law book, its test plan, the ledger and INDEX rows) exactly.
6. **Apply Appendix section 3** (the vocabulary pack and the deploy script) exactly.
7. **Plant the breaks B1 to B24** (Traps) one at a time; each must turn at least one of your tests
   red; restore each before the next.
8. **Bump** PATCH (`0.128.02` → `0.128.03`, or the next PATCH if `main` moved); `uv lock --offline`;
   stage `uv.lock`.
9. **`make ci`**, redirected to a file. Read the file.
10. **Fill the handback sections**; set Status to `BUILT` here and in this sprint's
    `docs/sprints/README.md` row.

---

## Test plan

Under exactly these names and files (the planner judges the breaks by them). The support module
`agents/execution/tests/partial_fill_helpers.py` holds `unh_order(**changes)` (UNH's order as
Alpaca returned it: `qty` "2", `filled_qty` "1", `filled_avg_price` "401.11", `limit_price`
"401.2", `status` "expired", `time_in_force` "day", `client_order_id` the Fill key), `seed_unh`
(a `PMRun`, an `OrderIntent` with `stop_pct` 0.05650079080214057, a pending `Fill` of `quantity` 2
with `source_run_id` the PM run, an `ExecutionRun`, the `EXECUTES`/`EMITTED_BY`/`EXECUTED_BY` edges)
and `adopt_unh` (the adopted `Position broker:UNH:1:40111`, `provenance` `reconciled-from-broker`,
`quantity` 1, `opened_price_cents` 40111, `stop_pct` 0.05). The broker double is
`agents/execution/tests/broker_stop_helpers.py::TrackingBroker`.

| # | Test (exact name) | File | Must prove | Red before? |
| --- | --- | --- | --- | --- |
| A1 | 🎯 `test_an_expired_order_that_filled_part_is_a_fill_of_that_part` | `agents/execution/tests/test_partial_fill_mapping.py` | `fill_from_order(unh_order())`: `filled`, `quantity` 2, `filled_quantity` 1, `executed_quantity` 1, price 401.11, `order_status` `expired`, `reason` None (`EXEC-OUT-07` / `EXEC-TYP-04`) | red |
| A2 | `test_every_ended_status_with_a_fill_is_filled` (parametrized `expired`, `canceled`, `cancelled`) | same | each `filled` with `filled_quantity` 1 (`EXEC-OUT-07`) | red |
| A3 | `test_an_ended_order_with_nothing_filled_stays_unfilled` (parametrized `filled_qty` "0", None) | same | `rejected`, reason `expired`, `executed_quantity` 0 (`EXEC-OUT-07`) | red (by import) |
| A4 | `test_a_partly_filled_order_in_flight_stays_partial` | same | `partially_filled` → `partial`, `filled_quantity` 1 (`EXEC-STA-05`) | red |
| A5 | 🪤 `test_a_replaced_order_is_not_read_as_a_fill` | same | `replaced` with `filled_qty` 1 → `rejected` (`EXEC-OUT-07`) | red (by import) |
| A6 | `test_a_fractional_or_missing_filled_qty_is_read_as_whole_shares` | same | "1.0" → 1; "" and absent → None (`EXEC-TYP-04`) | red |
| A7 | `test_where_the_broker_does_not_say_the_order_quantity_stands` (parametrized) | same | no `filled_quantity`: `filled` 3 → 3, `partial` → 3, `rejected` → 0, `pending` → 0 (`EXEC-TYP-04`) | red |
| A8 | 🎯 `test_the_sweep_drops_no_part_of_a_partly_filled_order` | `agents/execution/tests/test_partial_fill_refresh.py` | the sweep returns 0, cancels nothing, writes no `drop_reason`, no `Fault`, no `BrokerOrderStatus` (`EXEC-OUT-07`) | red |
| A9 | 🪤 `test_an_ended_order_that_filled_nothing_is_still_dropped` | same | with `filled_qty` "0": one drop, `drop_reason`, `broker_status` `rejected` (never the raw word), status facts `{expired, rejected}`, one `DroppedDecision` (`EXEC-OUT-07`) | passes |
| A10 | 🎯 `test_the_refresh_settles_the_filled_part_and_tells_the_rest_once` | same | after two refreshes: `filled`, `broker_filled_quantity` 1, `broker_price_cents` 40111, `quantity` 2, the props unchanged by the second; one `BrokerOrderStatus` with `quantity` 2 and `filled_quantity` 1; exactly one fault, `UnfilledRemainder`, `warning`, message starting `filled 1 of 2 UNH side=buy;` and holding `(expired)` (`EXEC-OUT-07` / `EXEC-TYP-04` / `EXEC-STA-05`) | red |
| A11 | `test_a_whole_fill_writes_its_quantity_and_tells_nothing` | same | `filled`, `filled_qty` "2": `broker_filled_quantity` 2, no fault (`EXEC-TYP-04`) | red |
| A12 | `test_an_ended_order_with_nothing_filled_writes_no_filled_quantity` | same | `filled_qty` "0": `rejected`, no `broker_filled_quantity`, no fault (`EXEC-OUT-07` / `EXEC-TYP-04`) | passes |
| A13 | 🎯 `test_the_adopted_share_takes_the_decided_stop` | same | before the refresh `decided_stop_pct` is `(0.05, "fallback")`; after it `(0.0565…, "lineage")` (`EXEC-OBS-06`) | red |
| A14 | 🪤 `test_the_entry_stop_covers_only_the_shares_the_broker_filled` | same | `filled_entry_stop_thresholds` with `broker_quantities={"UNH": 1}`: one plan, quantity 1, opened 40111, the decided width (`EXEC-OBS-06` / `EXEC-TYP-04`) | red |
| A15 | `test_a_partly_filled_sell_realizes_pnl_on_the_shares_it_sold` | `agents/execution/tests/test_partial_fill_pnl.py` | a sell of 10 that filled 4 at 101.35 over a 100.00 entry: `realized_pnl_cents` 540, `broker_filled_quantity` 4, one `UnfilledRemainder` (`EXEC-TYP-04` / `EXEC-OUT-07`) | red |
| A16 | `test_the_draft_holds_the_filled_quantity_where_the_broker_gave_one` | `agents/monitor/tests/test_position_from_partial_fill.py` | `position_from_fill` gives 1 with `broker_filled_quantity` 1, 2 without (`EXEC-TYP-04`) | red |
| A17 | `test_a_fill_line_counts_the_shares_the_broker_filled` | `orchestration/tests/test_daily_brief_filled_quantity.py` | `fills_between` gives 1 with `broker_filled_quantity` 1, 2 without (`DSP-OUT-06` / `EXEC-TYP-04`) | red |
| A18 | `test_the_action_is_declared_and_dispatched` | `tests/test_vocabulary_step.py` | `'vocabulary'` in the `ValidateSet`; the switch throws when `Enable-Vocabulary` fails (DL-303 D7) | red |
| A19 | `test_the_step_sets_every_app_and_the_job_and_reads_each_back` | same | the step loops `@("master") + @($AGENTS.Keys)` through `Set-AppVocabulary`, then `Set-JobVocabulary`, returns `$ok -and $jobOk`, and calls no `containerapp` itself (DL-303 D7) | red |
| A20 | `test_the_agent_list_holds_the_fifteen_agent_apps` | same | `$AGENTS` names 15 apps, `execution` among them, not `master` (DL-303 D7) | passes |
| A21 | `test_the_pack_declares_the_filled_quantity_on_fill` | same | `broker_filled_quantity` in the pack's `Fill` properties (`EXEC-TYP-04`) | red |

The red/green split above is the prototype's tests run on `main` at the spec commit
(`planner_tests_on_unchanged.txt`): A3 and A5 are red only because their module imports
`executed_quantity`; say so in your output.

---

## Success factors

- [ ] A1 to A21 exist under the names above, each citing its clauses; the red/green split on the
      unchanged tree is the Test plan's; all green after.
- [ ] Appendix sections 1 to 3 applied exactly: every file equals the prototype's blob
      (`prototype_blobs.txt`, OneDrive `trading-agents-data/wq135-2026-10-16/`).
- [ ] No existing test changed; every existing test passes.
- [ ] B1 to B24 each red against your tests, each restored.
- [ ] Every touched module, test files included, under 200 lines after `ruff format`.
- [ ] Version PATCH, `uv.lock` one line changed.
- [ ] `make ci` exit 0, 100.00 % coverage (the dependency audit may be the only step that cannot
      reach its network; say so if it is).
- [ ] **F1 (the planner's, at review, no cost):** `wq135_f1_replay.py` on the built tree prints what
      it prints on the prototype (`f1_prototype.txt`): no drop, `filled` 1 of 2 at 40111, one
      `UnfilledRemainder`, the adopted share's stop `(0.0565…, lineage)`, an entry-stop plan of 1.
- [ ] **F2 (the planner's, after deploy):** the vocabulary step reads every target `[OK]` and every
      app's decoded pack equals the repo's; the first weekday night on the new tag runs 8 / 8 with
      no `VocabularyError`; every buy `Fill` settled `filled` that night carries
      `broker_filled_quantity` equal to the broker's `filled_qty`. A real partial fill cannot be
      scheduled (1 in 350): when the next one comes, it settles as a fill and its share carries its
      decided stop.

---

## Traps

🪤 **`Fill.quantity` is never rewritten.** The filled quantity is a new property beside it. A test
that asserts `quantity == 1` after the refresh asserts the wrong thing.
🪤 **A10 must refresh twice.** Once proves the write; twice proves the warning is told once and the
settled Fill is not touched again (`EXEC-STA-05`).
🪤 **A13 must show the before.** Assert the fallback before the refresh, then the lineage after; a
test that only asserts after passes if the Position already recorded the decided width.
🪤 **A14 holds the money invariant.** A 2-share stop on a 1-share holding would try to sell a share
the account does not own. Assert the plan's quantity is 1.
🪤 **A9 and A12 are the other half of `EXEC-OUT-07`.** An order that filled nothing is still the
drop it was; do not let the fix make every ended order a fill.
🪤 **`ruff format` grows test files.** Measure sizes after formatting; `test_partial_fill_refresh.py`
is 157 lines on the prototype.
🪤 **The in-memory store returns list props as tuples.** Compare scalars.
🪤 **Never run the deploy step.** `infra/` is applied as text and tested from source only.

**Breaks — plant one at a time against your tests, restore each:**

| # | File | Plant |
| --- | --- | --- |
| B1 | `alpaca_orders.py` | `status_of`'s ended-with-a-fill condition is `False` |
| B2 | `alpaca_orders.py` | `fill_from_order` does not pass `filled_quantity` |
| B3 | `alpaca_orders.py` | `filled_quantity_of` reads nothing (`raw = None`) |
| B4 | `alpaca_orders.py` | `filled_quantity_of` reads `qty` |
| B5 | `alpaca_orders.py` | `replaced` with a fill is `filled` |
| B6 | `broker.py` | `executed_quantity` ignores `filled_quantity` |
| B7 | `broker.py` | `executed_quantity` counts a `rejected` order |
| B8 | `broker_status_refresh.py` | no `broker_filled_quantity` written |
| B9 | `broker_status_refresh.py` | `broker_filled_quantity` is `broker_fill.quantity` |
| B10 | `order_status_store.py` | the status fact carries no `filled_quantity` |
| B11 | `partial_fill.py` | the remainder is never told |
| B12 | `partial_fill.py` | the warning's severity is `error` |
| B13 | `partial_fill.py` | `filled > ordered` for `filled >= ordered` (a whole fill is told) |
| B14 | `contracts/broker_lifecycle.py` | `fill_quantity_key` always `quantity` |
| B15 | `contracts/stop_width.py` | the match reads `quantity` |
| B16 | `filled_entry_stops.py` | the lot reads `quantity` |
| B17 | `agents/monitor/domain/positions.py` | the draft reads `quantity` |
| B18 | `orchestration/daily_brief_fills.py` | the fill line reads `quantity` |
| B19 | `realized_pnl.py` | PnL on `broker_fill.quantity` |
| B20 | vocabulary pack | `broker_filled_quantity` removed from `Fill` |
| B21 | `deploy-agents.ps1` | the step skips the job |
| B22 | `deploy-agents.ps1` | the step skips the master |
| B23 | `deploy-agents.ps1` | the `'vocabulary'` switch line removed |
| B24 | `alpaca_orders.py` | `filled_quantity >= 0` (an ended order with nothing filled is a fill) |

On the prototype all 24 went red against the planner's own tests (`breaks_on_prototype.txt`).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Sizes after the change: `contracts/broker_lifecycle.py` **182**, `filled_entry_stops.py`
  **174**, `alpaca_orders.py` **163**, `reconciliation_store.py` **162**. Section 1 places them; add
  nothing to them.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers. Nothing here is a tunable.
- Faults, not silent failure: the remainder is a warning fault on the sink the refresh already has.
- `make ci` **every step** green, **100.00 % coverage floor**, redirected to a file, never piped.
- Version bump PATCH, `uv.lock` staged with it.
- A worktree has **no `.env`**. State which tree you ran in.

---

## Sequencing after merge (the planner's)

1. Review: blobs against `prototype_blobs.txt`; the planner's tests (`planner_tests/`) beside the
   builder's; `s280_breaks.py` against the builder's tests alone; CodeQL set-diff against the S279
   remote branch (133 open, 0 errors); F1 on the built tree.
2. `make gate-ran` from `../ta-s280`, the SHA checked against `git rev-parse HEAD`; merge.
3. Deploy: decode and compare every injected pack first; `pwsh infra/deploy-agents.ps1 -Action
   vocabulary` (17 `[OK]`); then the image-only retag; `DeployRecord`; rollback `s279`. F2; close
   work-queue 135.

---

## Handover — paste this to Codex

```text
You are building Sprint 280 in the worktree ../ta-s280, on the branch
sprint-280-a-partly-filled-order-is-a-fill-of-its-part. Never work on main. The worktree and its
venv are ready; never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-280-a-partly-filled-order-is-a-fill-of-its-part.md, whole, before anything
else. It is the spec, and its bottom sections are your handback. The Appendix holds the production
code, the law text and the pack and script changes, which you apply exactly. Your work is the
tests, the bump and the evidence.

In order:
1. Read agents/execution/laws/laws.md and test-plan.md, agents/monitor/laws/laws.md,
   agents/analyst/laws/laws.md, orchestration/laws/dispatcher/laws.md and the test-plan.md beside
   each, docs/laws/conventions.md and docs/laws/drift-register.md. Fill the Law reading record in
   the spec BEFORE any code.
2. Write agents/execution/tests/partial_fill_helpers.py and the tests A1 to A21 under the exact
   names and files in the Test plan, each docstring citing its clauses. Run them on the unchanged
   tree and paste the output into the Closeout: the red/green split must be the Test plan's last
   column (A9, A12 and A20 pass already; A3 and A5 are red only by their module's import).
3. Apply Appendix section 1 exactly (twelve files; agents/execution/partial_fill.py is new). Change
   nothing else in production code. Change no existing test.
4. Apply Appendix section 2 exactly (execution laws.md, test-plan.md, docs/laws/ledger.md,
   docs/laws/INDEX.md). The test-plan rows name your tests; if a name differs, your name is wrong.
5. Apply Appendix section 3 exactly (the vocabulary pack and infra/deploy-agents.ps1).
6. Plant the breaks B1 to B24 (Traps) one at a time; each must turn at least one of your tests red;
   restore each before the next. Record each in the Closeout.
7. Bump the version PATCH (0.128.02 -> 0.128.03) in pyproject.toml, run uv lock --offline, stage
   uv.lock. Run make ci redirected to a file and read the file. If the dependency audit is the only
   step that fails for want of network, say so; the planner runs it.
8. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: run infra/ scripts, pwsh or any az command; reach the network; change kernel/, any
Dockerfile or any pack beyond section 3; rewrite Fill.quantity or make BrokerFill.quantity mean
filled; add or reword a law clause beyond section 2; change any existing test; use noqa; let any
module, test files included, reach 200 lines; measure make ci through a pipe.

Traps (the spec's Traps section has them all): Fill.quantity stays the ordered 2 after the refresh;
A10 refreshes twice; A13 asserts the fallback before and the lineage after; A14's plan is 1 share;
A9 and A12 keep an ended order that filled nothing a drop; ruff format grows test files, measure
after formatting; the in-memory store returns list props as tuples.

Two tiers when something does not fit. A wrong command, count, path or line number whose intent is
plain: correct it, record it in Return notes, and carry on. A law that contradicts the spec, an
existing test failing, or a measurement in the spec that does not reproduce: STOP and report. State
anything not done as "not done" or "verified failing". Never write a Result for work you have not
done.
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
| *(builder)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(builder)*

**Contradictions found between a law and this spec:** *(builder)*

**Laws found silent where a decision was needed:** *(builder)*

**Clauses that were ⬜ and are now proven:** *(builder)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| *(builder)* | | | | |

**Tests added beyond the plan:** *(builder)*

---

## Closeout — evidence

**Status:** *(builder)*

**Tree the proofs ran in (and `.env` present?):** *(builder)*

**Result:** *(builder)*

**Files changed:** *(builder)*

**Design decisions:** recorded as [`DL-303`](../design-log.md) by the planner.

**Proof — the red run first:** *(builder)*

**Proof — the green run:** *(builder)*

**Guards planted:** *(builder)*

**Module line counts:** *(builder)*

**`make ci`:** *(builder)*

**`make gate-ran`:** *(planner, at review)*

**Not met / verified failing:** *(builder)*

---

## Return notes

- *(builder)*

---

## Appendix — the change, measured on the planner's prototype

The planner's prototype is `d996b462`, the local branch `proto-s280` in `../ta-s280-proto`, cut from
`75472497`. All three sections apply with `git apply` to this branch's base. On the prototype
`make ci` exited 0 (5,134 passed, 9 skipped, 100.00 %, the dependency audit clean); its 24 planted
breaks went red; `wq135_f1_replay.py` printed `f1_prototype.txt`.

### 1. Production — twelve files under `agents/`, `contracts/` and `orchestration/`

```diff
diff --git a/agents/execution/alpaca_orders.py b/agents/execution/alpaca_orders.py
index cfe8cc54..fc44c57e 100644
--- a/agents/execution/alpaca_orders.py
+++ b/agents/execution/alpaca_orders.py
@@ -11,6 +11,7 @@ from decimal import ROUND_HALF_UP, Decimal
 from typing import Literal

 from agents.execution.broker import BrokerFill
+from contracts.broker_lifecycle import RESOLVED_UNFILLED_BROKER_STATUSES
 from contracts.common import Money

 _PENDING = frozenset({"new", "accepted", "pending_new", "held", "accepted_for_bidding"})
@@ -78,7 +79,8 @@ def fill_from_order(
     """Map an Alpaca order object onto a BrokerFill; never raise on a dict."""
     if not isinstance(order, dict):
         return rejected(idempotency_key, reference, "malformed_broker_response")
-    status = status_of(str(order.get("status", "")))
+    filled = filled_quantity_of(order)
+    status = status_of(str(order.get("status", "")), filled or 0)
     return BrokerFill(
         idempotency_key=idempotency_key,
         ticker=str(order.get("symbol", "")),
@@ -92,6 +94,7 @@ def fill_from_order(
         order_type=_optional_str(order.get("type")),
         time_in_force=_optional_str(order.get("time_in_force")),
         order_status=_optional_str(order.get("status")),
+        filled_quantity=filled,
     )


@@ -109,9 +112,15 @@ def rejected(idempotency_key: str, reference: Money, reason: str) -> BrokerFill:
     )


-def status_of(raw: str) -> BrokerStatus:
-    """Map Alpaca order status onto the broker contract status."""
-    if raw == "filled":
+def status_of(raw: str, filled_quantity: int = 0) -> BrokerStatus:
+    """Map Alpaca order status onto the broker contract status.
+
+    An order the broker ended after filling part of it is a fill of that part: the
+    filled quantity was executed and only the rest went unfilled (DL-303).
+    """
+    if raw == "filled" or (
+        raw in RESOLVED_UNFILLED_BROKER_STATUSES and filled_quantity > 0
+    ):
         return "filled"
     if raw == "partially_filled":
         return "partial"
@@ -120,6 +129,14 @@ def status_of(raw: str) -> BrokerStatus:
     return "rejected"


+def filled_quantity_of(order: dict[str, object]) -> int | None:
+    """Return Alpaca's `filled_qty` in whole shares, or None when it is absent."""
+    raw = order.get("filled_qty")
+    if raw in (None, ""):
+        return None
+    return int(float(str(raw)))
+
+
 def side_of(raw: str) -> BrokerSide:
     """Map Alpaca side strings onto the broker contract side."""
     return "sell" if raw == "sell" else "buy"
diff --git a/agents/execution/broker.py b/agents/execution/broker.py
index b4afa1b0..c361209f 100644
--- a/agents/execution/broker.py
+++ b/agents/execution/broker.py
@@ -48,6 +48,16 @@ class BrokerFill:
     # The broker's raw order status (Alpaca `new`, `accepted`, ...). `status` folds
     # `new` and `accepted` into `pending`, and only a `new` order is replaceable.
     order_status: str | None = None
+    # The broker's filled quantity (Alpaca `filled_qty`); `quantity` stays the ordered
+    # one. None where a broker does not say (DL-303).
+    filled_quantity: int | None = None
+
+
+def executed_quantity(fill: BrokerFill) -> int:
+    """Return the shares the broker executed: its filled quantity, else the order's."""
+    if fill.filled_quantity is not None:
+        return fill.filled_quantity
+    return fill.quantity if fill.status in ("filled", "partial") else 0


 @dataclass(frozen=True)
diff --git a/agents/execution/broker_status_refresh.py b/agents/execution/broker_status_refresh.py
index 9aa86d53..f501a13a 100644
--- a/agents/execution/broker_status_refresh.py
+++ b/agents/execution/broker_status_refresh.py
@@ -11,6 +11,9 @@ from datetime import UTC, datetime
 from decimal import ROUND_HALF_UP, Decimal
 from typing import TYPE_CHECKING

+from agents.execution.broker import executed_quantity
+from contracts.broker_lifecycle import BROKER_FILLED_QUANTITY_PROP
+
 if TYPE_CHECKING:
     from agents.execution.broker import BrokerFill
     from kernel import Node
@@ -51,6 +54,8 @@ def broker_status_props(
             "broker_status_broker_order_id": broker_fill.broker_order_id,
             _BROKER_STATUS_REFRESHED_AT_PROP: datetime.now(tz=UTC).isoformat(),
         }
+        if broker_fill.status == _FILLED_STATUS:
+            props[BROKER_FILLED_QUANTITY_PROP] = executed_quantity(broker_fill)
     if _should_write_price(node, broker_fill):
         props[_BROKER_PRICE_CENTS_PROP] = current_broker_price_cents
     return props
diff --git a/agents/execution/filled_entry_stops.py b/agents/execution/filled_entry_stops.py
index 9709d3fd..8932a0f4 100644
--- a/agents/execution/filled_entry_stops.py
+++ b/agents/execution/filled_entry_stops.py
@@ -12,7 +12,7 @@ from decimal import ROUND_HALF_UP, Decimal
 from typing import TYPE_CHECKING

 from agents.execution.broker_stop_types import BrokerStopThresholdPlan
-from contracts.broker_lifecycle import is_filled_buy_fill
+from contracts.broker_lifecycle import fill_quantity_key, is_filled_buy_fill
 from contracts.position_refs import position_ref_for_keys
 from contracts.positions import PositionStopThreshold

@@ -71,7 +71,7 @@ def _pending_lot(
     if graph.get_node("Position", position_key) is not None:
         return None
     try:
-        quantity = _int_prop(fill, "quantity")
+        quantity = _int_prop(fill, fill_quantity_key(fill))
         opened_price_cents = _opened_price_cents(fill)
     except (TypeError, ValueError):
         return None
diff --git a/agents/execution/order_status_store.py b/agents/execution/order_status_store.py
index ba9bc30f..22a1e75d 100644
--- a/agents/execution/order_status_store.py
+++ b/agents/execution/order_status_store.py
@@ -31,6 +31,7 @@ def write_order_status(
             "fill_key": fill_node.key,
             "ticker": broker_fill.ticker,
             "quantity": broker_fill.quantity,
+            "filled_quantity": broker_fill.filled_quantity,
             "broker_order_id": broker_fill.broker_order_id,
             "status": broker_fill.status,
             "reason": broker_fill.reason,
diff --git a/agents/execution/partial_fill.py b/agents/execution/partial_fill.py
new file mode 100644
index 00000000..d9417d68
--- /dev/null
+++ b/agents/execution/partial_fill.py
@@ -0,0 +1,50 @@
+"""The rest of a decision the broker ended after filling part of it.
+
+Agent: execution
+Role: tell the operator, once, that a partly filled order's remainder was not executed.
+External I/O: the injected FaultSink.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING
+
+from agents.execution.broker import executed_quantity
+from kernel import AgentFault
+
+if TYPE_CHECKING:
+    from agents.execution.broker import BrokerFill
+    from kernel import FaultSink, Node
+
+
+def report_unfilled_remainder(
+    sink: FaultSink, fill_node: Node, broker_fill: BrokerFill
+) -> None:
+    """Warn once when a filled order executed fewer shares than it asked (DL-303)."""
+    ordered = int(str(fill_node.props.get("quantity", 0)))
+    filled = executed_quantity(broker_fill)
+    if broker_fill.status != "filled" or filled >= ordered:
+        return
+    sink.submit(
+        AgentFault(
+            source_agent="execution",
+            source_module="agents.execution.partial_fill",
+            capability="refresh_pending_fills",
+            severity="warning",
+            error_type="UnfilledRemainder",
+            message=(
+                f"filled {filled} of {ordered} {broker_fill.ticker} "
+                f"side={broker_fill.side}; the broker ended the rest "
+                f"({broker_fill.order_status}) "
+                f"broker_order_id={broker_fill.broker_order_id} "
+                f"client_order_id={broker_fill.idempotency_key}"
+            ),
+            context={
+                "fill_key": fill_node.key,
+                "ticker": broker_fill.ticker,
+                "ordered": ordered,
+                "filled": filled,
+                "broker_order_status": broker_fill.order_status,
+            },
+        )
+    )
diff --git a/agents/execution/realized_pnl.py b/agents/execution/realized_pnl.py
index 6f040337..57ce9899 100644
--- a/agents/execution/realized_pnl.py
+++ b/agents/execution/realized_pnl.py
@@ -10,6 +10,7 @@ from __future__ import annotations
 from datetime import UTC, datetime
 from typing import TYPE_CHECKING

+from agents.execution.broker import executed_quantity
 from agents.execution.broker_status_refresh import completes_partial_fill
 from contracts.pnl import realized_pnl_cents
 from contracts.positions import PositionBasis, position_basis_for_ref
@@ -43,7 +44,7 @@ def realized_pnl_props(
     basis = position_basis_for_ref(
         graph, position_ref=position_ref, ticker=broker_fill.ticker
     )
-    pnl = _pnl_from_basis(basis, broker_fill.quantity, exit_price_cents)
+    pnl = _pnl_from_basis(basis, executed_quantity(broker_fill), exit_price_cents)
     if pnl is None:
         _record_unresolved(sink, fill_node, broker_fill, "entry basis unresolved")
         return _unresolved_props()
diff --git a/agents/execution/reconciliation_store.py b/agents/execution/reconciliation_store.py
index a216ed88..17478988 100644
--- a/agents/execution/reconciliation_store.py
+++ b/agents/execution/reconciliation_store.py
@@ -17,6 +17,7 @@ from agents.execution.broker_status_refresh import (
 )
 from agents.execution.fill_attempts import broker_idempotency_key
 from agents.execution.order_status_store import write_order_status
+from agents.execution.partial_fill import report_unfilled_remainder
 from agents.execution.realized_pnl import realized_pnl_props
 from agents.execution.snapshot_account import account_snapshot_props
 from contracts.broker_lifecycle import is_terminal_fill_broker_status
@@ -64,6 +65,7 @@ def refresh_pending_fills(
         )
         if props:
             graph.merge_node("Fill", node.key, props)
+        report_unfilled_remainder(sink, node, broker_fill)


 def write_snapshot(
diff --git a/agents/monitor/domain/positions.py b/agents/monitor/domain/positions.py
index a8746c02..8b785828 100644
--- a/agents/monitor/domain/positions.py
+++ b/agents/monitor/domain/positions.py
@@ -12,6 +12,7 @@ from datetime import UTC, datetime
 from typing import TYPE_CHECKING

 from agents.monitor.domain.exit_rules import ExitPosition
+from contracts.broker_lifecycle import fill_quantity_key
 from contracts.stop_width import decided_stop_pct

 if TYPE_CHECKING:
@@ -54,7 +55,7 @@ def position_from_fill(
         run_id=run_id,
         ticker=str(fill.props["ticker"]),
         opened_price_cents=int(fill.props["price_cents"]),
-        quantity=int(fill.props["quantity"]),
+        quantity=int(fill.props[fill_quantity_key(fill)]),
         stop_pct=stop_pct,
         target_pct=target_pct,
         horizon_days=default_horizon_days,
diff --git a/contracts/broker_lifecycle.py b/contracts/broker_lifecycle.py
index a1776529..d3057a0b 100644
--- a/contracts/broker_lifecycle.py
+++ b/contracts/broker_lifecycle.py
@@ -50,6 +50,9 @@ TERMINAL_BROKER_ORDER_STATUSES = frozenset(
 RESOLVED_UNFILLED_BROKER_STATUSES = frozenset({"canceled", "cancelled", "expired"})
 COMPLETED_EXIT_BROKER_STATUSES = frozenset({"filled", "partial", "partially_filled"})
 FILLED_BROKER_STATUSES = frozenset({"filled"})
+# The refresh writes the broker's filled quantity beside `quantity`, the ordered
+# one (DL-303).
+BROKER_FILLED_QUANTITY_PROP = "broker_filled_quantity"
 _ENDED_MARKERS = ("cancelled_at", "replaced_at")


@@ -148,6 +151,17 @@ def is_completed_exit_fill(fill: Node) -> bool:
     return _effective_fill_status(fill) in COMPLETED_EXIT_BROKER_STATUSES


+def fill_quantity_key(fill: Node) -> str:
+    """Name the property that holds a Fill's executed size (DL-303).
+
+    The broker's filled quantity once the refresh wrote one, else the ordered
+    `quantity` (a Fill settled before DL-303, or one still in flight).
+    """
+    if BROKER_FILLED_QUANTITY_PROP in fill.props:
+        return BROKER_FILLED_QUANTITY_PROP
+    return "quantity"
+
+
 def is_filled_buy_fill(fill: Node) -> bool:
     """Return whether a buy Fill has reached a filled broker outcome."""
     return (
diff --git a/contracts/stop_width.py b/contracts/stop_width.py
index e8138860..03b523d9 100644
--- a/contracts/stop_width.py
+++ b/contracts/stop_width.py
@@ -14,7 +14,7 @@ from __future__ import annotations

 from typing import TYPE_CHECKING, Literal, NamedTuple

-from contracts.broker_lifecycle import is_filled_buy_fill
+from contracts.broker_lifecycle import fill_quantity_key, is_filled_buy_fill

 if TYPE_CHECKING:
     from kernel import GraphStore, Node
@@ -110,9 +110,12 @@ def _lineage_stop_pct(


 def _equals_holding(fill: Node, position: Node) -> bool:
-    """Exact quantity AND exact broker price: never a guess across lots (DL-223)."""
+    """Exact filled quantity AND exact broker price: never a guess across lots.
+
+    DL-223; the quantity is the one the broker filled (DL-303).
+    """
     run_id = fill.props.get("source_run_id")
-    quantity = _whole(fill.props.get("quantity"))
+    quantity = _whole(fill.props.get(fill_quantity_key(fill)))
     price = _whole(fill.props.get("broker_price_cents"))
     return (
         quantity is not None
diff --git a/orchestration/daily_brief_fills.py b/orchestration/daily_brief_fills.py
index 61213570..2c51b22f 100644
--- a/orchestration/daily_brief_fills.py
+++ b/orchestration/daily_brief_fills.py
@@ -14,7 +14,11 @@ from __future__ import annotations
 from datetime import UTC, datetime
 from typing import TYPE_CHECKING

-from contracts.broker_lifecycle import FILLED_BROKER_STATUSES, is_resting_stop_fill
+from contracts.broker_lifecycle import (
+    FILLED_BROKER_STATUSES,
+    fill_quantity_key,
+    is_resting_stop_fill,
+)
 from orchestration.daily_brief_text import BriefDataError, FillLine, OrderLine

 if TYPE_CHECKING:
@@ -55,7 +59,7 @@ def fills_between(
             continue
         line = FillLine(
             side=_text(fill, "side"),
-            quantity=_whole(fill, "quantity"),
+            quantity=_whole(fill, fill_quantity_key(fill)),
             ticker=_text(fill, "ticker"),
             price_cents=_cents(fill, "broker_price_cents"),
             stopped_out=is_resting_stop_fill(fill),
```

### 2. The law — the execution book, its test plan, the ledger and INDEX rows

```diff
diff --git a/agents/execution/laws/laws.md b/agents/execution/laws/laws.md
index 280f64a5..6005b0fa 100644
--- a/agents/execution/laws/laws.md
+++ b/agents/execution/laws/laws.md
@@ -1,6 +1,6 @@
 # `Execution` — Laws

-**Prefix:** `EXEC` · **status:** LOCKED v1.14 · **Owner:** Yury Gurevich
+**Prefix:** `EXEC` · **status:** LOCKED v1.15 · **Owner:** Yury Gurevich

 > Be the single, auditable, idempotent broker boundary. Execute only what the portfolio
 > manager has approved and the stage gate allows.
@@ -114,7 +114,12 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   `Fill.dropped_at` plus an append-only `BrokerOrderStatus` drop fact. The broker's normalised
   account of the order stays in `Fill.broker_status` and a **raw terminal reason is never
   written into it** — two vocabularies in that one property is what stalled the fleet on
-  2026-07-30. *(Declares capability decided in ADR-0018; shape settled by S151/DL-79.)*
+  2026-07-30. A decision whose order the broker ended (`expired`, `canceled`) after filling
+  **part** of it is **not** dropped: its `Fill` settles `filled` for the part that filled
+  (`EXEC-TYP-04`), no drop evidence is written for it, and the unfilled rest is told once as an
+  `UnfilledRemainder` warning fault naming the ticker, filled of ordered and the broker's end word.
+  *(Declares capability decided in ADR-0018; shape settled by S151/DL-79; the partly filled
+  order by S280 / DL-303.)*
 - **EXEC-OUT-08** — Every submitted order records its price-tolerance evidence durably: the
   selected mode, the decided price, the **applied** tolerance and limit price, and the
   **counterfactual** mode, tolerance and limit price for the band that was not used. The
@@ -235,6 +240,12 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   `current_stage`, `reason`, and `provenance` (`EXEC-OUT-05`). `CONTRACT.version` names the current
   schema. No clause promises that it moves when a payload field is added, removed or renamed
   (DRIFT-060). Since v1.11 the output clauses name exactly these fields (DRIFT-061).
+- **EXEC-TYP-04** — `Fill.quantity` is the quantity ordered; `Fill.broker_filled_quantity` is the
+  whole number of shares the broker filled, from 1 to `Fill.quantity`, written once with
+  `broker_status` `filled` and read from the broker's own filled quantity where it gives one.
+  Every reader of a Fill's executed size (the stop-width match, an entry stop's lot, a Position
+  drawn from a Fill, the brief's fills, a sell's realized PnL) reads the filled quantity where it
+  is written, else `Fill.quantity`. *(S280 / DL-303.)*

 ---

@@ -301,7 +312,8 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   the S190 / DL-139 correction for DRIFT-055 and the S209 / DL-170 correction for DRIFT-064.)*
 - **EXEC-OBS-06** — The protective stop resting at the broker is the stop the PM decided. Its width
   is read through the one shared stop-width resolver: a broker-adopted position takes the `stop_pct`
-  of the one filled production buy that equals it exactly in quantity and broker price, and with no
+  of the one filled production buy that equals it exactly in the quantity the broker filled
+  (`EXEC-TYP-04`) and in broker price, and with no
   exact match it takes the fallback; every stop fact records its `stop_pct_source` (`lineage`,
   `position` or `fallback`). A live stop whose price differs from the decided price by one cent or
   more is **replaced in place**, never cancelled and re-placed, so the position is never without a
@@ -531,3 +543,9 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   `BrokerStopOrder` once per sweep and the stop-threshold plan reads `Fill` once per plan, where both
   read the whole label once per item. Why: 348 broker orders made each run start list 346 Fills 348
   times. No drop, cancel, stop or reconciliation decision changes; 40 / 66 -> 41 / 67.
+- **v1.15 — S280 / DL-303 (2026-10-16).** `EXEC-OUT-07` amended and proven for the first time: an
+  order the broker ended after filling part of it is a fill of that part, never a dropped
+  decision, and its rest is told once. New `EXEC-TYP-04`: `Fill.broker_filled_quantity`, and every
+  reader of an executed size reads it. `EXEC-OBS-06` matches an adopted position on the quantity
+  the broker filled. Why: UNH's 1 of 2 on 2026-10-15 was written dropped and its share adopted
+  on the fallback stop. 41 / 67 -> 43 / 68.
diff --git a/agents/execution/laws/test-plan.md b/agents/execution/laws/test-plan.md
index cb733645..dfae7a5c 100644
--- a/agents/execution/laws/test-plan.md
+++ b/agents/execution/laws/test-plan.md
@@ -35,7 +35,7 @@ Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID
 | EXEC-OUT-04 | reconcile returns ReconcileResult with matched, discrepancies, provenance (no run_id) and writes a Reconciliation node. | reconcile + schema | `test_execution_agent.py::test_reconcile_reports_unrecorded_broker_fill`; `tests/test_contract_required_payload_fields.py::test_execution_payload_fields_required_by_law` | 🟩 |
 | EXEC-OUT-05 | promote_stage returns PromoteStageResult with accepted, previous_stage, current_stage, reason, provenance; only a confirmed, accepted promotion writes a StageTransition; an unaccepted one writes none and says why in reason. | gate + schema | `test_promote_stage.py::test_promote_stage_writes_flag_when_evidence_passes`; `test_promote_stage.py::test_promote_stage_confirmed_writes_transition_and_status_reads_graph`; `tests/test_contract_required_payload_fields.py::test_execution_payload_fields_required_by_law` | 🟩 |
 | EXEC-OUT-06 | execution.fills.ready event is a claim-check ref; run_id in envelope. | pub/sub | `test_execution_pubsub.py::test_run_id_propagated_in_fills_ready_event` | 🟩 |
-| EXEC-OUT-07 | A decision unfilled in its session is dropped, recorded via Fill.drop_reason/dropped_at plus an append-only BrokerOrderStatus drop fact, and no raw terminal reason is written into Fill.broker_status. | boundary | _tbd_ | ⬜ |
+| EXEC-OUT-07 | A decision unfilled in its session is dropped, recorded via Fill.drop_reason/dropped_at plus an append-only BrokerOrderStatus drop fact, and no raw terminal reason is written into Fill.broker_status; an order the broker ended after filling part of it is not dropped, settles filled for its part, and its rest is told once as an UnfilledRemainder warning. | boundary | `test_partial_fill_mapping.py::test_an_expired_order_that_filled_part_is_a_fill_of_that_part`; `::test_every_ended_status_with_a_fill_is_filled`; `::test_an_ended_order_with_nothing_filled_stays_unfilled`; `::test_a_replaced_order_is_not_read_as_a_fill`; `test_partial_fill_refresh.py::test_the_sweep_drops_no_part_of_a_partly_filled_order`; `::test_the_refresh_settles_the_filled_part_and_tells_the_rest_once`; `::test_an_ended_order_with_nothing_filled_writes_no_filled_quantity`; `::test_an_ended_order_that_filled_nothing_is_still_dropped` | 🟩 |
 | EXEC-OUT-08 | Every submitted order records applied and counterfactual tolerance mode, bps and limit price; the counterfactual never reaches the broker. | happy | _tbd_ | ⬜ |
 | EXEC-OUT-09 | Every graph-pull ExecutionRun records deliberation posture, deliberation status and posture-blocked buy count as separate facts. | posture | `test_deliberation_posture.py::test_advisory_posture_submits_unvetoed_buy_and_records_warning`; `test_deliberation_posture_degraded.py::test_degraded_run_drops_buys_without_waiting_and_submits_sell`; `test_deliberation_posture.py::test_fail_open_submission_severity_follows_posture`; `::test_deliberation_posture_is_mode_selector_not_tunable`; `test_trading_deliberation_posture.py::test_advisory_fail_open_passes_when_attributed`; `test_graph_vocabulary_deliberation.py::test_execution_run_deliberation_posture_props_are_declared` | 🟩 |

@@ -83,6 +83,7 @@ Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID
 | EXEC-TYP-01 | Fill.price is Decimal; broker string parsed before persisting. | schema | `test_execution_agent.py::test_submit_records_fill_cents_and_executes_lineage` | 🟩 |
 | EXEC-TYP-02 | Fill.status ∈ {filled, partial, rejected, pending}; no other values. | schema | `test_execution_agent.py::test_broker_rejection_records_rejected_fill_and_fault` | 🟩 |
 | EXEC-TYP-03 | Execution payloads carry the required ExecutionResult, Fill, ReconcileResult, StageStatus, PromoteStageResult fields, and CONTRACT.version names the current schema (no promise it moves with the shape). | schema | `tests/test_contract_required_payload_fields.py::test_execution_payload_fields_required_by_law`; `test_execution_pubsub.py::test_execution_result_is_deserializable` | 🟩 |
+| EXEC-TYP-04 | Fill.quantity is the ordered quantity; Fill.broker_filled_quantity is the whole shares the broker filled (1 to quantity), written once with broker_status filled from the broker's own figure; every reader of an executed size (stop-width match, entry-stop lot, Position draft, brief fills, sell realized PnL) reads it where written, else quantity. | schema | `test_partial_fill_mapping.py::test_an_expired_order_that_filled_part_is_a_fill_of_that_part`; `::test_a_fractional_or_missing_filled_qty_is_read_as_whole_shares`; `::test_where_the_broker_does_not_say_the_order_quantity_stands`; `test_partial_fill_refresh.py::test_the_refresh_settles_the_filled_part_and_tells_the_rest_once`; `::test_a_whole_fill_writes_its_quantity_and_tells_nothing`; `::test_the_entry_stop_covers_only_the_shares_the_broker_filled`; `test_partial_fill_pnl.py::test_a_partly_filled_sell_realizes_pnl_on_the_shares_it_sold`; `agents/monitor/tests/test_position_from_partial_fill.py::test_the_draft_holds_the_filled_quantity_where_the_broker_gave_one`; `orchestration/tests/test_daily_brief_filled_quantity.py::test_a_fill_line_counts_the_shares_the_broker_filled`; `tests/test_vocabulary_step.py::test_the_pack_declares_the_filled_quantity_on_fill` | 🟩 |

 ## Security

@@ -104,7 +105,7 @@ Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID
 | EXEC-OBS-03 | Stop placement is an immutable fact, cancellation a cancelled_at marker, broker truth decides liveness, and a held position with no live stop raises UnprotectedPosition and is retried. | failure | `test_broker_stops.py::test_execute_pm_node_places_one_weighted_broker_stop_idempotently`; `test_exit_stop_cancel.py::test_cancellation_is_an_appended_marker_not_a_deletion`; `test_exit_stops.py::test_rejected_exit_leaves_position_loudly_unprotected`; `test_broker_stop_replacement.py::test_cancelled_stop_is_replaced_on_next_run`; `test_broker_stop_replacement_e2e.py::test_rejected_exit_reprotects_on_later_hold_run`; `tests/test_broker_stop_liveness.py::test_filled_sibling_fill_makes_uncancelled_stop_inactive`; `tests/test_broker_stop_liveness.py::test_cancelled_stop_with_nonterminal_fill_stays_inactive`; `tests/test_broker_stop_liveness.py::test_resting_stop_fill_keeps_stop_live`; `tests/test_broker_stop_liveness.py::test_missing_sibling_fill_keeps_stop_live`; `test_stop_derivation_provenance.py::test_a_stop_from_an_active_position_records_that_lineage`; `test_stop_derivation_provenance.py::test_a_stop_from_a_pending_fill_records_that_lineage`; `test_stop_derivation_provenance.py::test_the_percent_source_does_not_answer_which_lineage_placed_the_stop`; `test_stop_derivation_provenance.py::test_an_adopted_holding_is_protected_from_the_position_not_the_fill`; `test_deliberation_posture_degraded.py::test_degraded_run_still_places_protective_stops`; S230 replacement markers: `test_broker_stop_realign.py::test_a_mismatched_new_stop_is_replaced_in_place`; `::test_a_failed_replace_keeps_the_old_stop_and_retries`. | 🟩 |
 | EXEC-OBS-04 | Deliberation fail-open severity follows recorded posture, so advisory outages are warnings and binding no-verdict buy submissions are errors that acceptance can distinguish; degraded no-verdict buy holds are warnings. | observable | `test_deliberation_posture.py::test_advisory_posture_submits_unvetoed_buy_and_records_warning`; `::test_binding_posture_blocks_unvetoed_buy_and_records_error`; `test_deliberation_posture_degraded.py::test_degraded_run_drops_buys_without_waiting_and_submits_sell`; `test_deliberation_posture.py::test_fail_open_submission_severity_follows_posture`; `test_trading_deliberation_posture.py::test_advisory_fail_open_fails_without_reason`; `test_trading_acceptance_deliberation.py::test_advisory_veto_that_reviewed_nothing_fails_acceptance`; `test_trading_deliberation_unvetoed.py::test_unvetoed_advisory_buy_breaches`; `::test_a_veto_that_reviewed_nothing_breaches`; `::test_a_partially_degraded_veto_stays_green` | 🟩 |
 | EXEC-OBS-05 | Liveness of an execution broker fact is asked in exactly one place; a terminal BrokerStopOrder is not live regardless of cancelled_at; a resting-stop Fill is not an open order; and the sweep compares broker and graph stop identity instead of liveness views. | observable | `tests/test_broker_stop_liveness.py::test_filled_sibling_fill_makes_uncancelled_stop_inactive`; `tests/test_broker_fill_lifecycle.py::test_resting_stop_fill_is_not_an_open_order_fill`; `tests/test_broker_fill_lifecycle.py::test_pending_buy_fill_is_an_open_order_fill`; `agents/execution/tests/test_drop_sweep_identity.py::test_fired_stop_with_unrefreshed_graph_status_raises_no_mismatch`; `agents/execution/tests/test_drop_sweep_identity.py::test_graph_stop_identity_mismatch_still_faults`; `agents/execution/tests/test_drop_sweep_liveness.py::test_sweep_raises_no_mismatch_for_dead_stop_order`; `agents/execution/tests/test_drop_sweep_liveness.py::test_live_stop_mismatch_fault_carries_context`; `tests/test_broker_lifecycle_invariants.py::test_broker_lifecycle_vocabulary_lives_in_one_module`; `tests/test_broker_lifecycle_invariants.py::test_broker_order_lifecycle_status_drives_live_stop_orders`; S230: `tests/test_broker_stop_replaced.py::test_a_replaced_order_is_not_live`; `::test_a_replaced_at_marker_ends_the_fact_without_deleting_it` | 🟩 |
-| EXEC-OBS-06 | The broker stop is the PM-decided stop: its width comes through the one shared resolver (an adopted position takes the stop_pct of the one filled production buy equal in quantity and broker price, otherwise the fallback) and every stop fact records stop_pct_source lineage/position/fallback; a live stop one cent or more off its decided price is replaced in place, never cancelled and re-placed, with replaced_at/replaced_by markers on the old fact and replaces on the new; a replacement is refused with a warning fault and the old stop left live when the order is not new, when the decided stop is at or above the current price, or when the broker refuses, and is retried next run. | failure | `tests/test_stop_width.py::test_the_resolver_returns_the_width_the_pm_decided`; `::test_all_three_readers_agree_on_the_decided_stop`; `::test_an_older_lot_of_another_size_does_not_match`; `::test_no_exact_match_falls_back_and_says_so`; `::test_a_fill_path_position_keeps_its_own_width`; `::test_an_exact_buy_that_decided_no_width_is_not_lineage`; `::test_a_verification_fill_is_never_lineage`; `::test_a_position_with_no_width_needs_a_fallback`; `test_broker_stop_realign.py::test_a_mismatched_new_stop_is_replaced_in_place`; `::test_an_accepted_stop_is_not_replaced`; `::test_a_stop_is_never_moved_to_or_above_the_market`; `::test_a_failed_replace_keeps_the_old_stop_and_retries`; `::test_a_failed_replace_leaves_no_marker`; `::test_a_matching_stop_is_left_alone`; `::test_replacement_is_idempotent_across_runs`; `test_broker_stop_replace_adapters.py::test_alpaca_replace_patches_the_stop_price_under_the_new_key`; `::test_alpaca_refusal_carries_the_broker_message`; `::test_alpaca_rejected_replacement_raises`; `::test_paper_broker_models_alpacas_refusal_of_an_accepted_stop`; `::test_unreadable_broker_orders_leave_every_stop_and_fault`; `::test_a_stop_the_broker_does_not_list_is_skipped_as_unknown` | 🟩 |
+| EXEC-OBS-06 | The broker stop is the PM-decided stop: its width comes through the one shared resolver (an adopted position takes the stop_pct of the one filled production buy equal in the quantity the broker filled and in broker price, otherwise the fallback) and every stop fact records stop_pct_source lineage/position/fallback; a live stop one cent or more off its decided price is replaced in place, never cancelled and re-placed, with replaced_at/replaced_by markers on the old fact and replaces on the new; a replacement is refused with a warning fault and the old stop left live when the order is not new, when the decided stop is at or above the current price, or when the broker refuses, and is retried next run. | failure | `tests/test_stop_width.py::test_the_resolver_returns_the_width_the_pm_decided`; `::test_all_three_readers_agree_on_the_decided_stop`; `::test_an_older_lot_of_another_size_does_not_match`; `::test_no_exact_match_falls_back_and_says_so`; `::test_a_fill_path_position_keeps_its_own_width`; `::test_an_exact_buy_that_decided_no_width_is_not_lineage`; `::test_a_verification_fill_is_never_lineage`; `::test_a_position_with_no_width_needs_a_fallback`; `test_broker_stop_realign.py::test_a_mismatched_new_stop_is_replaced_in_place`; `::test_an_accepted_stop_is_not_replaced`; `::test_a_stop_is_never_moved_to_or_above_the_market`; `::test_a_failed_replace_keeps_the_old_stop_and_retries`; `::test_a_failed_replace_leaves_no_marker`; `::test_a_matching_stop_is_left_alone`; `::test_replacement_is_idempotent_across_runs`; `test_broker_stop_replace_adapters.py::test_alpaca_replace_patches_the_stop_price_under_the_new_key`; `::test_alpaca_refusal_carries_the_broker_message`; `::test_alpaca_rejected_replacement_raises`; `::test_paper_broker_models_alpacas_refusal_of_an_accepted_stop`; `::test_unreadable_broker_orders_leave_every_stop_and_fault`; `::test_a_stop_the_broker_does_not_list_is_skipped_as_unknown`; `test_partial_fill_refresh.py::test_the_adopted_share_takes_the_decided_stop`; `::test_the_entry_stop_covers_only_the_shares_the_broker_filled` | 🟩 |
 | EXEC-OBS-07 | A broker-position divergence is flagged per episode: the episode opens with a `warn` at the run-start reconciliation that first sees it, under a subject naming its kind, ticker and first-sight snapshot; it becomes `critical` only when still present at the next run-start reconciliation, its `warn` closed as superseded; it closes by an appended FlagResolution, never by changing or deleting a Flag, when the divergence is gone; a divergence seen again after its episode closed opens a new episode at `warn` whatever the ticker's history; a live divergence always has exactly one unresolved Flag and an absent one none. | lifecycle | S248: `test_reconciliation_flag_episodes.py::test_a_second_episodes_first_sighting_is_warn`; `::test_a_third_episode_is_flagged_and_escalates_when_it_survives`; `::test_a_live_divergence_always_has_exactly_one_open_flag`; `::test_nothing_already_written_is_rewritten`; `test_reconciliation_flag_upgrade.py::test_an_open_suffixless_flag_is_the_open_episode`; `::test_spent_suffixless_keys_do_not_touch_a_new_episode`; `::test_the_subject_is_deterministic_and_well_formed`; `::test_a_repeated_call_for_one_snapshot_is_not_a_survived_run`; `::test_an_open_critical_supersedes_a_stray_open_warn`; `::test_a_spent_critical_key_is_never_rewritten`; `::test_each_call_reads_flag_and_resolution_once`; re-cited from `EXEC-TRG-07`: `test_reconciliation_flags.py::test_first_sight_of_a_divergence_is_warn_not_critical`; `::test_a_divergence_surviving_a_run_escalates_to_critical`; `::test_repeating_a_divergence_never_mints_a_second_unresolvable_flag`; `::test_an_adopted_divergence_is_retired_on_the_next_run` | 🟩 |

 ## S204 row declarations
diff --git a/docs/laws/INDEX.md b/docs/laws/INDEX.md
index 131faa94..a01725d7 100644
--- a/docs/laws/INDEX.md
+++ b/docs/laws/INDEX.md
@@ -43,7 +43,7 @@ Each agent's law files live at `agents/<name>/laws/`:
 | scanner | ✅ LOCKED v1.5 (S259, DL-276) | 18 / 41 | S259 (DL-276) reconciles `PARAM` only: the upper bound of `min_average_volume` follows the code, no clause changes; S251 names the graph-pull trigger in `SCAN-TRG-02` (DRIFT-085) and narrows `SCAN-TYP-01`'s version sentence (DRIFT-060); DL-203 reconciles `PARAM` only; S205 rewrites `SCAN-TYP-01` into required fields and closes DRIFT-047 without moving the count; S183's `SCAN-OUT-06`/`SCAN-OUT-07`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | portfolio_manager | ✅ LOCKED v1 (S70), amended **v1.12** (S259, DL-276) | 33 / 51 | S259 (DL-276) reconciles `PARAM` only: the bounds of six rows follow the code, no clause changes; S251 narrows `PM-OBS-01`/`PM-OUT-06`/`PM-STA-04` (no PM snapshot; DRIFT-039), `PM-OBS-04` (per candidate; DRIFT-065), uses emitted strings in `PM-OUT-03` (DRIFT-037), names graph-pull in `PM-TRG-02` (DRIFT-086), narrows `PM-TYP-03`'s version sentence (DRIFT-060); files DRIFT-098; S240 adds and proves `PM-IN-05`: held names weighed once per ticker at the run's own snapshot marks, a resumed run at the snapshot of the run it resumes (DRIFT-079 closed); DL-203 reconciles `PARAM` only; S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders applied weights; S211 adds and proves `PM-OBS-05`: reward-risk compares measured target evidence against stop risk and can reject measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows; S204 gives every clause a row and makes rowless clauses a hard gate |
 | deliberator | ✅ LOCKED v1.18 (S277, DL-289) | 35 / 66 | S277 (DL-289 amendment 4) adds and proves DLIB-FAIL-05, refusal-only sticky switching with one model-attributed row per attempt; re-proves DLIB-FAIL-01, DLIB-OUT-02 (always-written llm_switches) and DLIB-DEP-05 (handed-over fallback construction). S276 (DL-289 amendment 1) adds and proves DLIB-DEP-05 and DLIB-NEV-11; amended DLIB-OUT-02 re-proven for the models that answered; effort defaults to empty. Before that S257 (DL-274) reconciles `PARAM` only: `max_tokens` defaults to 16,384 with the same upper bound and `request_timeout_seconds` may reach 300, no clause changes; S256 (DL-272) adds and proves `DLIB-IDM-04` (settle-on-take and visible reply faults), `DLIB-OBS-08` (every completion, including a repeat, is its own row), and proves spend attribution `DLIB-OBS-02`; S255 (DL-269) adds and proves `DLIB-OUT-08`: recorded arithmetic reproduces before rendering, with first-failure withholding and old-packet parity; DRIFT-102/103 corrected; S254 / ADR-0032 adds and proves `DLIB-NEV-10`: prompt libraries reach vendors only through the agent's own client; before that S252 / DL-261: `DLIB-TRG-01` now proven for the key-and-edge candidate bound and order-property filter, 27 / 59. S246 adds and proves `DLIB-OUT-06` (each debater turn records its guided reasoning exactly as written, or why it could not be read, never failing the turn or the order) and `DLIB-OUT-07` (each debated order's record carries its decision and evidence packet), and amends `DLIB-TYP-01`; S245 adds and proves `DLIB-NEV-09` (every fact a role prompt states about our code is pinned to that code; the false calendar-day staleness fact removed, DRIFT-092); DL-203 reconciles `PARAM` only; S222 moves the vendor adapters to `kernel/` and proves `DLIB-SEC-02` key containment; S214 narrows `vetoed_tickers` to `overturn` verdicts only, routes unreadable judge answers through loud fail-open, and proves `DLIB-OUT-04`; S206 adds and proves `DLIB-NEV-08`; S205 rewrites and proves `DLIB-TYP-01`; S200 adds `DLIB-OBS-07` and turns `DLIB-IDM-02` green by hashing the system prompt too; S199 adds `DLIB-OBS-05`/`DLIB-OBS-06`; S172 proves concurrent-order record order and pending-reply handling; S194 added `DLIB-OBS-04`; S189 added stop-reason audit evidence; S167 added `DLIB-OBS-03` proof |
-| execution | ✅ LOCKED **v1.14** (S279, DL-302) | 41 / 67 | S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault; the stop plan shares one lazy Fill read; no decision changes. S258 (DL-276) reconciles `PARAM` only: the bounds of `slippage_bps`, `min_promotion_runs`, `min_approval_rate` and `alpaca_timeout` follow the code, no clause changes; S252 / DL-261: `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66. S251 adds and proves `EXEC-IDN-04` (the divergence-family Flag exception, `owns_graph` widened; DRIFT-094), names the contract's fields in `EXEC-OUT-01/02/04/05` (DRIFT-061) and narrows `EXEC-TYP-03`'s version sentence (DRIFT-060); S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode, `critical` only when it survived a run, whatever the ticker's history; S230 adds/proves `EXEC-OBS-06`: the broker stop is the PM-decided stop, read through the shared resolver, and a mismatched live stop is replaced in place with `replaced_at`/`replaces` markers; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; DL-203 reconciles `PARAM` only; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 adds/proves `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
+| execution | ✅ LOCKED **v1.15** (S280, DL-303) | 43 / 68 | S280 (DL-303) amends and proves `EXEC-OUT-07` (an order the broker ended after filling part of it is a fill of that part, its rest told once) and adds and proves `EXEC-TYP-04` (`Fill.broker_filled_quantity`, read by every reader of an executed size); `EXEC-OBS-06` matches on the filled quantity. S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault; the stop plan shares one lazy Fill read; no decision changes. S258 (DL-276) reconciles `PARAM` only: the bounds of `slippage_bps`, `min_promotion_runs`, `min_approval_rate` and `alpaca_timeout` follow the code, no clause changes; S252 / DL-261: `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66. S251 adds and proves `EXEC-IDN-04` (the divergence-family Flag exception, `owns_graph` widened; DRIFT-094), names the contract's fields in `EXEC-OUT-01/02/04/05` (DRIFT-061) and narrows `EXEC-TYP-03`'s version sentence (DRIFT-060); S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode, `critical` only when it survived a run, whatever the ticker's history; S230 adds/proves `EXEC-OBS-06`: the broker stop is the PM-decided stop, read through the shared resolver, and a mismatched live stop is replaced in place with `replaced_at`/`replaces` markers; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; DL-203 reconciles `PARAM` only; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 adds/proves `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | monitor | ✅ LOCKED v1.4 (S279, DL-302) | 22 / 47 | S279 (DL-302) adds and proves `MON-PERF-03`: the end-of-run evaluation shares one lazy Fill read across the book and retains each decided width; no decision changes. S252 / DL-261: `MON-TRG-02` bounds both work kinds, sync from requests and their linked snapshot; DRIFT-097 corrected, 21 / 46 unchanged. S251 names the graph-pull triggers in `MON-TRG-02` (DRIFT-086) and files DRIFT-097 for the unbounded sync poll; S205 rewrites and proves `MON-TYP-01`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | reporter | ✅ LOCKED v1.5 (S253, DL-262, DL-263) | 26 / 43 | S253 rewrites `RPT-OUT-02` (book counts from the broker's fills in the run's window, outcomes since the inception; DRIFT-099), amends `RPT-IN-01` and `RPT-NEV-03` (DRIFT-101), and adds and proves `RPT-IDM-04`; S251 names the run's own benchmark lineage in `RPT-OUT-07` (DRIFT-087) and the graph-pull trigger in `RPT-TRG-02` (DRIFT-086); v1.3 (DL-224) latest-per-date snapshot; S226 adds benchmark-relative `performance_metrics`, as-of bounded graph reads, contained performance failure, and backward-compatible snapshots; S205 rewrites `RPT-TYP-01`; S156 removed orphan `RPT-OBS-03`; S204 gives every clause a row and makes rowless clauses a hard gate |
 | forecaster | ✅ LOCKED v1.10 (S252, DL-261) | 25 / 52 | S252 / DL-261: `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged. S251 names the four legs (`FORE-IDN-01`), one node per prediction (`FORE-OBS-01`; DRIFT-081) and the shadow scorecards' subject (`FORE-IDM-03`; DRIFT-083); S243 amends and re-proves `FORE-FAIL-04` (a designed refusal is a `warning`, a missing input an `error`); S241 adds and proves `FORE-OUT-08`, `FORE-IDM-05`, `FORE-FAIL-05` (the settlement of each barrier claim and `barrier_scorecard`) and amends `FORE-IDN-02`/`TRG-01`/`OUT-03`; the S239 second follow-up (D10) re-words the barrier clauses for the provider-written history; the S239 follow-up amends `FORE-TRG-01`/`FORE-TRG-02` (graph-pull trigger; the deployed loop fires `forecast_barrier` only); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim); DL-203 reconciled `PARAM`; S205 proved `FORE-TYP-01`; counters are clauses proven / clauses declared |
diff --git a/docs/laws/ledger.md b/docs/laws/ledger.md
index c96fa513..e6d3bbe9 100644
--- a/docs/laws/ledger.md
+++ b/docs/laws/ledger.md
@@ -41,7 +41,7 @@ and torn down to zero. Historical Neo4j rows remain valid evidence for the pre-S
 | forecaster | ✅ v1.10 (LOCKED) | 25 / 52 | 🟨 partial — **25 of 52 clauses proven** after S252 (DL-261): `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged; v1.9 (S251, DL-260) names the four legs in `FORE-IDN-01`, one recorded node per prediction in `FORE-OBS-01` (DRIFT-081) and the three shadow scorecards in `FORE-IDM-03` (DRIFT-083), all still gray, count unchanged; v1.8 (S243, DL-247) amends and re-proves `FORE-FAIL-04`: a designed "no claim" records a `warning`, a missing or broken input an `error` (DRIFT-089), count unchanged; after S241 (DL-243) adds and proves `FORE-OUT-08` (each claim settled once by EXP-018's rule from a provider-written `MarketData`; `barrier_scorecard` over EXP-018's fixed climatology), `FORE-IDM-05` (settled once, one pass per run) and `FORE-FAIL-05` (void with a named reason, never a false outcome), and amends and re-proves `FORE-IDN-02`/`TRG-01`/`OUT-03`; v1.6 (S239, DL-241 D10) re-words `FORE-IN-07`/`TRG-01`/`OUT-07`/`IDM-04`/`FAIL-04`/`NEV-04` for the provider-written history, count unchanged; before that the S239 follow-up amends and re-proves `FORE-TRG-01`/`FORE-TRG-02` (the deployed graph-pull loop fires `forecast_barrier` only; count unchanged); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim), each proven; 27 have a gray row |
 | portfolio_manager | ✅ v1 (LOCKED, amended **v1.12**) | 33 / 51 | 🟨 partial — **33 of 51 clauses proven** after S259 (DL-276) reconciles `PARAM` only (the bounds of six rows follow the code; no clause moves) and S251 (DL-260) narrows `PM-OBS-01`/`PM-OUT-06`/`PM-STA-04` to what `PMRun` and `OrderIntentResult` carry (the `portfolio_state_snapshot` promise withdrawn, DRIFT-039; `PM-STA-04` now green), makes `PM-OBS-04` per candidate (DRIFT-065), uses the emitted reason strings in `PM-OUT-03` (DRIFT-037), names the graph-pull trigger in `PM-TRG-02` (DRIFT-086) and narrows `PM-TYP-03`'s version sentence (DRIFT-060); DRIFT-098 filed for `PM-OUT-01`/`PM-TYP-03`; before that S240 adds and proves `PM-IN-05`: a run weighs each held ticker once at its own snapshot mark (adoption mark, then cost, as fallbacks) and a resumed run reads the snapshot of the run it resumes, closing DRIFT-079; `PM-IDN-01` stays gray (current-state conjunct proven, the whole-purpose boundary proof still owed); S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders the applied weights; S211 adds and proves `PM-OBS-05`: reward-risk now compares measured target evidence against stop risk, varies across measured profiles, and rejects measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows |
 | deliberator | ✅ v1.18 (LOCKED) | 35 / 66 | S277 (DL-289 amendment 4) adds and proves DLIB-FAIL-05, refusal-only sticky switching with one model-attributed row per attempt; re-proves DLIB-FAIL-01, DLIB-OUT-02 (always-written llm_switches) and DLIB-DEP-05 (handed-over fallback construction). S276 (DL-289 amendment 1) adds and proves DLIB-DEP-05 and DLIB-NEV-11; amended DLIB-OUT-02 re-proven for the models that answered; effort defaults to empty. 🟨 partial — **35 of 66 clauses proven** after S257 (DL-274) reconciles `PARAM` only (the output cap 16,384, the peer wait up to 300 seconds; no clause moves) and S256 (DL-272) adds and proves `DLIB-IDM-04` (settle-on-take and visible reply faults), `DLIB-OBS-08` (every completion is its own row), and proves spend attribution `DLIB-OBS-02`; S255 (DL-269) adds and proves `DLIB-OUT-08`: recorded arithmetic reproduces before rendering, with first-failure withholding and old-packet parity; DRIFT-102/103 corrected; before that S254 / ADR-0032: `DLIB-NEV-10` proves prompt libraries use only the agent's own client; before that S252 (DL-261): `DLIB-TRG-01` now proven for the key-and-edge candidate bound and order-property filter, 27 / 59; before that S246 (DL-252) adds and proves `DLIB-OUT-06` (each defender and challenger turn records its guided reasoning, readings then gaps before the argument, exactly as written or why it could not be read, and an unreadable one never fails the turn or the order) and `DLIB-OUT-07` (each debated order's record carries its decision and evidence packet), and amends `DLIB-TYP-01` (`DebateTurnRecord.reasoning`, `.reasoning_error`); before that S245 (DL-251) adds and proves `DLIB-NEV-09`: every fact the challenger and judge prompts state about our code is pinned by a test that reads that code, the false calendar-day staleness fact and the stale name-correlation example are gone (DRIFT-092), and the champions rebuild byte for byte from pack-side sources; before that S222 moves its vendor adapters to `kernel/` and proves `DLIB-SEC-02` with a key-containment sentinel; S214 narrows `vetoed_tickers` to `overturn` verdicts only, routes unreadable judge answers through loud fail-open, and proves `DLIB-OUT-04`; S206 adds and proves `DLIB-NEV-08`: rendered debate-context verdicts name their enforcing check and agent, while descriptive stop-target regime evidence has no verdict; S205 rewrites and proves `DLIB-TYP-01`; S200 adds `DLIB-OBS-07` and promotes `DLIB-IDM-02`; S199 adds `DLIB-OBS-05`/`DLIB-OBS-06`; S172 proves concurrent-order record order and pending-reply handling; S194 adds `DLIB-OBS-04`; S189 added stop-reason audit evidence; S167 proves queryable fail-open causes |
-| execution | ✅ v1.14 (LOCKED) | 41 / 67 | 🟨 partial — **41 of 67 clauses proven** after S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault, and the stop plan shares one lazy Fill read, no decision changes; before that S258 (DL-276) reconciles `PARAM` only (the bounds of four rows follow the code; no clause moves) and S252 (DL-261): `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66; before that S251 (DL-260) adds and proves `EXEC-IDN-04`: execution writes divergence-family `Flag`/`FlagResolution` nodes and no others, both labels now in `owns_graph` as the one declared shared pair (DRIFT-094); `EXEC-OUT-01`/`-02`/`-04`/`-05` name the contract's fields (DRIFT-061); `EXEC-TYP-03`'s version sentence (DRIFT-060); before that S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode (`warn` at first sight under a subject naming the first-sight snapshot, `critical` only if still present at the next run-start reconciliation, a new episode at `warn` whatever the ticker's history, one unresolved Flag per live divergence); S230 adds/proves `EXEC-OBS-06`: the broker stop's width comes through the shared stop-width resolver (PM lineage first, fallback only without it) and a live stop resting off its decided price is replaced in place, never cancelled and re-placed; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 added/proved `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; S204 gives every clause a row and promotes missing rows to a hard gate |
+| execution | ✅ v1.15 (LOCKED) | 43 / 68 | 🟨 partial — **43 of 68 clauses proven** after S280 (DL-303) amends and proves `EXEC-OUT-07` (a partly filled ended order is a fill of its part, its rest told once) and adds and proves `EXEC-TYP-04` (`Fill.broker_filled_quantity`, read by every reader of an executed size), `EXEC-OBS-06` matching on the filled quantity; before that S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault, and the stop plan shares one lazy Fill read, no decision changes; before that S258 (DL-276) reconciles `PARAM` only (the bounds of four rows follow the code; no clause moves) and S252 (DL-261): `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66; before that S251 (DL-260) adds and proves `EXEC-IDN-04`: execution writes divergence-family `Flag`/`FlagResolution` nodes and no others, both labels now in `owns_graph` as the one declared shared pair (DRIFT-094); `EXEC-OUT-01`/`-02`/`-04`/`-05` name the contract's fields (DRIFT-061); `EXEC-TYP-03`'s version sentence (DRIFT-060); before that S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode (`warn` at first sight under a subject naming the first-sight snapshot, `critical` only if still present at the next run-start reconciliation, a new episode at `warn` whatever the ticker's history, one unresolved Flag per live divergence); S230 adds/proves `EXEC-OBS-06`: the broker stop's width comes through the shared stop-width resolver (PM lineage first, fallback only without it) and a live stop resting off its decided price is replaced in place, never cancelled and re-placed; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 added/proved `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; S204 gives every clause a row and promotes missing rows to a hard gate |
 | monitor | ✅ v1.4 (LOCKED) | 22 / 47 | 🟨 partial — **22 of 47 clauses proven** after S279 (DL-302) adds and proves `MON-PERF-03`: the end-of-run evaluation shares one lazy Fill read across the book and retains each decided width, no decision changes; before that S252 (DL-261): `MON-TRG-02` bounds both work kinds, sync from requests and their linked snapshot; DRIFT-097 corrected, 21 / 46 unchanged; S251 (DL-260) names the graph-pull triggers in `MON-TRG-02` with the key-and-edge bound for `ExecutionRun` work only (DRIFT-086; the sync poll is DRIFT-097), count unchanged; after S205 rewrites and proves `MON-TYP-01`; S204 gives every clause a row and promotes missing rows to a hard gate |
 | reporter | ✅ v1.5 (LOCKED) | 26 / 43 | 🟨 partial — **26 of 43 clauses proven** after S253 (DL-262, DL-263) rewrites `RPT-OUT-02` (the book counts are the broker's filled `Fill`s in the run's window, the outcomes cumulative since the inception; DRIFT-099), amends `RPT-IN-01` and `RPT-NEV-03` (an undefined metric is absent; DRIFT-101), and adds and proves `RPT-IDM-04` (no fill refreshed after the run is read; a re-report reproduces the book); S251 (DL-260) says `RPT-OUT-07`'s benchmark is the run's own `MarketData` by lineage, a missing one `missing benchmark` (DRIFT-087), and names the graph-pull trigger in `RPT-TRG-02` (DRIFT-086), count unchanged; v1.3 (work-queue 88, DL-224) was never reflected here and is now; after S226 adds benchmark-relative performance metrics, as-of bounded graph reads, contained performance failure, and backward-compatible `performance_metrics`; S205 rewrites `RPT-TYP-01` into required fields; S204 gives every clause a row and promotes missing rows to a hard gate |
 | researcher | ✅ v1.2 (LOCKED) | 20 / 43 | 🟨 partial — **20 of 43 clauses proven** after S205 rewrites and proves `RES-TYP-01`; 23 have a gray row |
```

### 3. The vocabulary pack and the deploy step

```diff
diff --git a/infra/deploy-agents.ps1 b/infra/deploy-agents.ps1
index 1470e3b6..43a6b497 100644
--- a/infra/deploy-agents.ps1
+++ b/infra/deploy-agents.ps1
@@ -15,7 +15,7 @@
 # POSTGRES_DSN is the schema/admin DSN; fleet roles use per-target DSNs.

 param(
-  [ValidateSet('preflight', 'up', 'postgres-flip', 'servicebus-flip', 'sensor', 'llm-candidates', 'down')]
+  [ValidateSet('preflight', 'up', 'postgres-flip', 'servicebus-flip', 'sensor', 'llm-candidates', 'vocabulary', 'down')]
   [string]$Action = 'preflight',
   [string]$Tag = 'latest',
   # DL-294 amendment 1: one readiness check, at the wake, before the 22:30 UTC dispatch.
@@ -769,6 +769,24 @@ function Enable-ContainerSensor {
   return ($held -eq "1") -and $vocabOk
 }

+function Enable-Vocabulary {
+  # DL-303: a vocabulary that moved reaches the master, every agent app and the job
+  # without a full `up`, which would revert the live-only settings. Run it BEFORE the
+  # retag: an older image never writes the new properties, so it reads the new pack
+  # unharmed. Each target is read back; a failed one is reported and the rest still set.
+  Top "GRAPH VOCABULARY"
+  $ok = $true
+  foreach ($name in @("master") + @($AGENTS.Keys)) {
+    $appOk = Set-AppVocabulary $name
+    Check $appOk "graph vocabulary on $name"
+    $ok = $ok -and $appOk
+  }
+  $jobOk = Set-JobVocabulary
+  Check $jobOk "graph vocabulary on $DISPATCHER_JOB"
+  Bot
+  return $ok -and $jobOk
+}
+
 function Enable-LlmCandidates {
   # DL-289: run BEFORE the retag that brings a master or a role image of S276 or later.
   # Those images write properties the earlier vocabulary refuses: the master
@@ -1018,5 +1036,6 @@ switch ($Action) {
   'servicebus-flip' { Flip-ServiceBusSas }
   'sensor' { if (-not (Enable-ContainerSensor)) { throw "container sensor not enabled" } }
   'llm-candidates' { if (-not (Enable-LlmCandidates)) { throw "LLM candidates not enabled" } }
+  'vocabulary' { if (-not (Enable-Vocabulary)) { throw "graph vocabulary not set" } }
   'down' { Down }
 }
diff --git a/orchestration/packs/trading_graph_vocabulary.json b/orchestration/packs/trading_graph_vocabulary.json
index dbf60ec8..ca89bb11 100644
--- a/orchestration/packs/trading_graph_vocabulary.json
+++ b/orchestration/packs/trading_graph_vocabulary.json
@@ -446,6 +446,7 @@
     "Fill": [
       "attempt_ordinal",
       "actual_open_price_cents",
+      "broker_filled_quantity",
       "broker_idempotency_key",
       "broker_order_id",
       "broker_price_cents",
```
