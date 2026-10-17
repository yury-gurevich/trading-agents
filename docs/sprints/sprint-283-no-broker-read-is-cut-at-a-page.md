<!-- Agent: planning | Role: sprint handover -->
# Sprint 283 — no broker read is cut at a page: run-start reconciliation reads every order the graph waits on, whatever the account holds

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-283-no-broker-read-is-cut-at-a-page`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** [DL-306](../design-log.md) (measured and decided, planner, 2026-10-17) · [work-queue 134](../work-queue.md) · new `EXEC-OBS-08`, `EXEC-PERF-03`, PARAM `broker_recent_order_days`

> **Why this bump kind.** A fix: the run-start refresh exists to read the broker's end of every
> pending order (`EXEC-STA-05`, `EXEC-TRG-07`), and the one-page listing will stop it doing so for
> every order older than the newest 500. No new capability.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 1 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** The amendment this sprint owes is written for you in Appendix section 2: apply it exactly. A clause you believe is wrong is a `drift-register.md` row plus a report |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | `EXEC-TRG-04` (the on-demand `reconcile`) is ⬜ today and stays so; this sprint proves two new clauses |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the one law-adjacent file you may append to |

Binding sections: execution **`OBS`** (`EXEC-OBS-02`, `EXEC-OBS-03`, `EXEC-OBS-05`, new
`EXEC-OBS-08`), **`STA`** (`EXEC-STA-05`), **`TRG`** (`EXEC-TRG-04`, `EXEC-TRG-07`), **`PERF`**
(`EXEC-PERF-02`, new `EXEC-PERF-03`), **`DEP`** (`EXEC-DEP-03`), **`PARAM`**.

### The rule

1. **Before writing code**, read every law file in the map below, whole.
2. Read the agent's `test-plan.md` beside its `laws.md`. Say which clause you rely on is ⬜.
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

**No `contracts/` change; yes, a new guarantee.** Execution now promises that no broker read is cut
at a page and that a run-start read is bounded by the book. The cycle is owed and written for you:
Appendix section 2 adds `EXEC-OBS-08` and `EXEC-PERF-03`, the PARAM row
`broker_recent_order_days`, moves the book to v1.16, and gives the test-plan, ledger and INDEX rows
(43 / 68 → **45 / 70**: both clauses new and proven). 🪤 **`contracts/` must stay untouched:** it
is a fidelity decision path, and a change there would restart the count EXEC-014 waits on.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/execution/alpaca.py`, new `alpaca_order_reads.py` | `agents/execution/laws/laws.md` + `test-plan.md` | `EXEC-DEP-03` (the broker boundary, bounded by `alpaca_timeout`), `EXEC-OBS-02` (a refusal is routed, never silent), `EXEC-TRG-04` (the on-demand `reconcile` reads every order) |
| new `agents/execution/run_start_orders.py`, `reconciliation.py`, `reconciliation_store.py` | same | `EXEC-TRG-07` (run-start reconciliation), `EXEC-STA-05` (a settled Fill is never re-read) |
| `agents/execution/drop_sweep.py` | same | `EXEC-PERF-02` (broker first; neither label when the broker lists no order), `EXEC-OBS-05` (the sweep's stop identity) |
| `agents/execution/broker_stop_realign.py` | same | `EXEC-OBS-06` (a replacement is refused when the order is not `new`) |
| `agents/execution/settings.py`, `broker_factory.py` | same (PARAM) | a new tunable needs its PARAM row; `make ci`'s PARAM step compares them |

⚠️ **One invariant: what the run start writes does not change.** On today's account the prototype's
sweep and reconciliation make byte for byte the writes `main`'s make (F1). If a change of yours
alters any write, any drop, cancel or stop decision, stop and report.

---

## Goal

At merge, no broker read in execution is cut at Alpaca's page of 500. The on-demand read
(`AlpacaBroker.fills()`, behind `reconcile` and the two repair scripts) reads every order the broker
knows, a page at a time. A run start reads only what it needs: run-start reconciliation lists `Fill`
once, names every Fill still waiting on the broker, and the broker answers with every open order,
every order submitted within `broker_recent_order_days` (10), and each waiting order neither listing
shows, read by its id. The drop sweep and the stop realignment read the same open and recent orders,
the realignment also the stops it would move. A stop placed long ago that the broker fills or
expires is settled however many orders the account has taken since, and the next stop pass protects
the position again.

## Why (context)

`AlpacaBroker._list_orders` asks for `status=all&limit=500` and takes the one page. The account holds
353 orders and takes about three a day, so around early December the oldest orders fall off the page,
and the oldest orders are the resting stops. A stop that triggers or expires after that is never read:
its `Fill` stays pending, its fact stays live, the position keeps no stop at the broker while the
graph believes it has one, and the stop's realized PnL is never written. Alpaca expires a GTC stop 90
days after it was placed; the five placed 2026-08-12 expire 2026-11-10 21:00 UTC. That date is still
on the page, and on `main` the expiry is settled and the stop placed again (measured, below), but every
expiry after the account passes 500 would not be. Found while measuring work-queue 101 (DL-302); the
operator, 2026-10-17: *"can you write a plan/sprint for Codex"*.

### Measured, 2026-10-17 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| The account | 353 orders, oldest 2026-06-16; one listing 313 KB; 34 open (29 KB), the oldest open 2026-08-12; 9 orders in 7 days, 84 in 30 | *[measured 2026-10-17]* `wq134_measure.py` (`measure_2026-10-17.txt`) |
| What waits on the broker | 351 Fills, 34 waiting (`status` pending, `broker_status` not terminal), each open at the broker; 32 active stop facts, each open | *[measured 2026-10-17]* same script, the live graph |
| Paging by `until` | 100 a page gives back exactly the 353 orders in 4 pages; no two orders share a `submitted_at` | *[measured 2026-10-17]* same script |
| GTC expiry | every resting stop carries `expires_at` 90 days on; the five oldest expire 2026-11-10 21:00 UTC; no stop has yet reached 90 days | *[measured 2026-10-17]* `wq134_gtc_age.py` (`gtc_age_2026-10-17.txt`) |
| `main` and an expiry | still on the page: settled `rejected`, `…#1` placed for the whole holding at the decided price; beyond the page: never settled, no stop placed | *[measured 2026-10-17]* the planner's tests on `70d0eb32` (`planner_tests_on_unchanged_70d0eb32.txt`) |
| How often the list is read | the sweep and reconciliation at the head of the run, reconciliation again at submit (`pm_execution.py:66`), the realign when a stop is off price: two to four a night | *[measured 2026-10-17]* read from the code; F1's head of run made two |
| The prototype on the live account | head-of-run broker answers 693,294 → 103,694 bytes; the 70 writes and 2 faults identical (`ffee9c076cad2508`); Alpaca accepted the `after` window (13 orders) | *[measured 2026-10-17]* `wq134_f1.py` on `main` and on `proto-s283` (`f1_main_70d0eb32.txt`, `f1_proto.txt`) |
| The two pending buys | CAT 1 and MDLZ 15 still `accepted` after both F1 runs: the guard refused the sweep's cancels | *[measured 2026-10-17]* `f1_pending_buys_untouched.txt` |
| Alpaca's page limit is 500 | the largest `limit` the list endpoint takes | *[ASSUMED — not measured beyond 500]* `main` has asked 500 for months and been answered; nothing here asks more |
| An order with no `Fill` that ends between runs | the window must outlast the longest gap between runs (four days over a holiday weekend) | *[ASSUMED — derived from the weekday schedule]* the default 10 covers two missed nights beyond it |

---

## Scope — and what is deliberately NOT here

1. **Tests first** (Test plan, A1 to A17), under the exact names given; the ones the Test plan marks
   red must be red on the unchanged tree.
2. **The paged listing and the run-start read** (DL-306 D1, D2): new
   `agents/execution/alpaca_order_reads.py`; `AlpacaBroker.fills()` pages, `current_orders` new.
3. **The waiting orders and the narrow read** (D3, D4): new `agents/execution/run_start_orders.py`;
   reconciliation lists `Fill` once and hands it to the refresh; the sweep and the realign take the
   narrow read.
4. **The window** (D5): `broker_recent_order_days`, default 10, 4 to 60, handed on by the factory.
5. **The law cycle** (D6), written for you in Appendix section 2.
6. **PATCH** bump.

### Out of scope (do NOT build this sprint)

- **The `Broker` protocol.** It does not change; the narrow read is a capability one broker has.
- **The paper broker and every existing test double.** They keep listing every order.
- **The 34 `BrokerOrderStatus` facts the refresh appends for unchanged orders** (DL-302's named
  write growth) and **the sweep's cancel of a pending buy when a run fires before the open** (a
  standing operational note).
- **A pause longer than the window**: after one, a previous run's unfilled day order is settled by
  the refresh but gets no drop record. Named, not built.
- **`contracts/`, any pack, any `infra/` script.**

### The road not taken (LAW-06)

- **Page the whole history at every run start.** Rejected: correct, but every night's read grows
  with the account (0.68 MB now, about 2 MB in a year) for orders nothing waits on.
- **Keep one page and raise at 500.** Rejected: it stops the night's reconciliation instead of
  reading it.
- **The `after=` filter alone.** Rejected: it filters by submission, so it misses an August stop
  that fills in December.
- **Account activities (`/v2/account/activities/FILL`).** Rejected: they are dated by the fill, but
  never show an expiry or a cancel, which is exactly the 2026-11-10 case.
- **Add `current_orders` to the `Broker` protocol.** Rejected: twelve test doubles to edit for no
  behaviour; a broker that lists everything is already correct.
- **The sweep reads the graph first and names waiting orders.** Rejected: it would amend
  `EXEC-PERF-02` for nothing the window does not already give it.

---

## The design decisions — made, and recorded in DL-306

Do not edit `docs/design-log.md`. In short (the entry has the measurements and the rejected options):

1. **D1** Every listing is read a page at a time (`list_orders`: newest first, 500 a page, `until`
   the oldest `submitted_at` of the last page; stop on a short page or one that adds nothing new).
   `fills()` keeps meaning every order the broker knows.
2. **D2** `current_orders(waiting)`: `status=open`, then `status=all` after now less the window, then
   for each waiting order neither shows, `GET /v2/orders/{id}`, or by client order id when the Fill
   has no broker id; 404 is *not held*; any other refusal is raised with the broker's words; newest
   first, each order once.
3. **D3** Only reconciliation names waiting orders (one `Fill` read for both); the sweep names none;
   the realign names its targets' stops.
4. **D4** `run_start_orders(broker, waiting)`: the narrow read where the broker has it, `fills()`
   otherwise.
5. **D5** `broker_recent_order_days` = 10, bounded 4 to 60, a code default (no pack entry).
6. **D6** Execution law v1.16 (Appendix section 2); PATCH.

---

## Blast radius — measured 2026-10-17

| What | Detail |
| --- | --- |
| Files changed | production: `agents/execution/alpaca.py` **188**, new `alpaca_order_reads.py` **129**, new `run_start_orders.py` **65**, `settings.py` **162**, `broker_factory.py` **35**, `drop_sweep.py` **184**, `broker_stop_realign.py` **182**, `reconciliation.py` **121**, `reconciliation_store.py` **169**; laws (Appendix section 2); `pyproject.toml`, `uv.lock`; tests: four new files and two new support modules |
| Agents affected | execution only; no agent imports another |
| Contract change? | no (`contracts/` untouched); a new guarantee, so the law cycle is owed and written |
| Graph vocabulary change? | none |
| New env keys / tunables | the tunable `broker_recent_order_days` (code default 10; no env key set, no pack entry) |
| Deploy implication | image-only retag; no fidelity decision path changes (`scripts/replay_fidelity_git.py::DECISION_PATHS`), so the count does not restart |
| Rollback | retag to the previous tag. Nothing else: no vocabulary, pack or graph shape changes, and the `BrokerOrderStatus` facts the new read leads to are the ones the old read wrote |

---

## Steps, in order

1. **Read the laws** (MUST RULE) and write the Law reading record.
2. The design decisions are recorded (DL-306). Do not edit `docs/design-log.md`.
3. **Write the two support modules and the tests A1 to A17** under the names and files below. Run
   them on the unchanged tree and paste the output: the red/green split must be the one the Test
   plan states (run `pytest` with `--continue-on-collection-errors`; two files cannot import there).
4. **Apply Appendix section 1** (production) exactly. Change nothing else in production code.
5. **Apply Appendix section 2** (the law book, its test plan, the ledger and INDEX rows) exactly.
6. **Plant the breaks B1 to B24** (Traps) one at a time; each must turn at least one of your tests
   red; restore each before the next.
7. **Bump** PATCH (`0.128.03` → `0.128.04`, or the next PATCH if `main` moved); `uv lock --offline`;
   stage `uv.lock`.
8. **`make ci`**, redirected to a file. Read the file.
9. **Fill the handback sections**; set Status to `BUILT` here and in this sprint's
   `docs/sprints/README.md` row.

---

## Test plan

Under exactly these names and files (the planner judges the breaks by them).

Two support modules:

- `agents/execution/tests/order_read_helpers.py`: `NOW` (2026-12-07 22:30 UTC);
  `alpaca_order(n, *, days_ago, status="filled", **changes)` (a raw Alpaca order: `id` `order-NNNNN`,
  `client_order_id` `run-NNNNN:TN:buy`, `submitted_at` `days_ago` days and `n` seconds before `NOW`,
  `filled_qty` "1" only when filled); `AlpacaAccount(orders, *, fail=0)`, a callable
  `(method, path, body)` that answers `GET /v2/orders?…` as Alpaca does (`status` open / closed / all,
  `after` and `until` exclusive on `submitted_at`, `direction`, `limit`), `GET /v2/orders/{id}` and
  `GET /v2/orders:by_client_order_id?client_order_id=…` (raising `urllib.error.HTTPError` 404 when it
  holds no such order, or `fail` when set), records every path and gives `listings()` (each listing's
  query); `AgedAccountBroker`, a `TrackingBroker` whose `submit_stop` keeps the stop as a pending
  `BrokerFill` (`broker_order_id` `broker:<key>`, `order_type` stop, `order_status` new), whose
  `expire(broker_order_id, *, beyond_page)` turns it `rejected` / `expired` and, when `beyond_page`,
  hides it from `fills()` (the newest-500 listing), whose `current_orders(waiting)` records the
  `(broker_order_id, idempotency_key)` pairs it was asked for in `waited_on` and returns every pending
  order plus each waiting one it holds, and whose `live_stops()` lists the pending ones.
  🪤 **Import `OrderRef` only under `TYPE_CHECKING` here**, so the module loads on the unchanged tree.
- `agents/execution/tests/stop_pass_helpers.py`: `rest_fallback_stop(graph, broker)` and
  `run_stop_pass(graph, broker)`, the USB fixtures of `stop_realign_helpers.py` (`seed_usb_stop`,
  `run_placement`) typed for any `Broker`, not only `PaperBroker` (mypy refuses the doubles there).

The account most adapter tests use, `_aged_account()`: 34 open GTC stops 66 days old, one GTC stop 98
days old that has `expired`, and 1,168 filled day orders `n` = 100 … 1,267 aged `(n - 100) / 4` days:
1,203 orders, 40 of them inside a 10-day window.

| # | Test (exact name) | File | Must prove | Red before? |
| --- | --- | --- | --- | --- |
| A1 | 🎯 `test_a_listing_past_one_page_reads_every_order` | `agents/execution/tests/test_alpaca_order_reads.py` | `list_orders(account, "all")` returns the 1,203 orders, each once, in 3 listings, each `limit` 500 and `direction` desc, the first with no `until`, the second's `until` the oldest `submitted_at` of the newest 500 (`EXEC-OBS-08`) | red (by import) |
| A2 | `test_fills_reads_every_order_the_broker_knows` | same | `AlpacaBroker.fills()` returns 1,203 fills, the expired stop among them (`EXEC-OBS-08`) | red (by import) |
| A3 | 🎯 `test_the_run_start_read_holds_open_recent_and_waiting_orders` | same | `current_orders(account, (the expired stop's ref,), days=10, now=NOW)`: exactly the 34 open, the 40 recent and the expired stop; the listings asked are `open` then `all`; the last path is `/v2/orders/<its id>`; newest first (`EXEC-OBS-08` / `EXEC-PERF-03`) | red (by import) |
| A4 | `test_the_recent_window_starts_the_configured_days_ago` | same | with `days=12` the second listing's `after` is `(NOW - 12 days).isoformat()` (`EXEC-PERF-03`) | red (by import) |
| A5 | `test_an_order_already_listed_is_read_once` | same | one open order, waited on by its id and by its key alone: returned once, no read by id or key (`EXEC-PERF-03`) | red (by import) |
| A6 | `test_a_waiting_order_with_no_broker_id_is_read_by_its_client_order_id` | same | a 200-day-old cancelled order waited on by key only is returned; the last path is `/v2/orders:by_client_order_id?client_order_id=run-00007%3AT7%3Abuy` (`EXEC-OBS-08`) | red (by import) |
| A7 | `test_a_waiting_order_the_broker_does_not_know_is_left_out` | same | an empty account and two waiting refs (one by id, one by key): `[]`, nothing raised (`EXEC-OBS-08`) | red (by import) |
| A8 | 🪤 `test_any_other_refusal_of_an_order_read_is_raised` | same | `fail=500`: `RuntimeError` matching `HTTP Error 500: refused: {"message":"internal"}` (`EXEC-OBS-02`) | red (by import) |
| A9 | `test_the_window_is_a_bounded_setting_the_factory_hands_on` | same | default 10; 3 and 61 refused naming `broker_recent_order_days`; `broker_from_settings` with keys and 7 gives an `AlpacaBroker` whose `current_orders()` asks `after` within five seconds of the real clock less 7 days (`EXEC-PERF-03`) | red (by import) |
| A10 | `test_waiting_refs_name_every_unsettled_fill_and_no_settled_one` | `agents/execution/tests/test_run_start_orders.py` | six Fills (pending; pending `partial`; pending with no broker id; pending `filled`; pending `rejected`; `status` rejected): the refs are exactly `("", r3)`, `("b1", r1)`, `("b2", r2)` (`EXEC-STA-05` / `EXEC-OBS-08`) | red (by import) |
| A11 | `test_run_start_reconciliation_reads_fill_once_and_names_its_waiting_orders` | same | a graph counting `list_nodes("Fill")`: `reconcile_run_start` reads it once, and the broker is asked for exactly `(("b1", "r1:A:buy"),)` (`EXEC-PERF-03` / `EXEC-OBS-08`) | red (by import) |
| A12 | `test_the_sweep_and_the_realign_take_the_narrow_read` | same | a broker whose `fills()` raises: the sweep asks `current_orders(())`; the stop pass on a 5 % stop resting off its decided price asks for exactly that stop (`(f"broker:{key}", key)`) (`EXEC-PERF-03`) | red (by import) |
| A13 | `test_a_broker_without_a_narrow_read_lists_everything` | same | `AlpacaBroker` is a `NarrowOrderReads`, `PaperBroker` is not; `run_start_orders` on the paper broker and on a `TrackingBroker` returns their `fills()` (`EXEC-OBS-08`) | red (by import) |
| A14 | 🎯 `test_the_refresh_settles_an_old_stop_the_listing_no_longer_shows` | `agents/execution/tests/test_stop_expiry_beyond_page.py` | USB's stop placed by one stop pass, then `expire(…, beyond_page=True)`, then `reconcile_run_start`: the stop's Fill `broker_status` is `rejected`, the fact is not live, and the stop's pair is in the last `waited_on` (`EXEC-OBS-08` / `EXEC-STA-05`) | **red (on behaviour)** |
| A15 | 🎯 `test_a_stop_the_broker_expires_beyond_the_page_is_placed_again` | same | then a second stop pass: one live stop, key `<stop key>#1`, 16 shares, 5,806 cents (the decided price), no fault (`EXEC-OBS-08` / `EXEC-OBS-05` / `EXEC-OBS-03`) | **red (on behaviour)** |
| A16 | `test_a_stop_the_broker_expires_is_placed_again_while_the_listing_shows_it` | same | the same with `beyond_page=False`: settled `rejected` and `…#1` placed: what the fleet does today (`EXEC-OBS-05` / `EXEC-OBS-03`) | passes |
| A17 | `test_a_listing_answer_that_is_not_a_list_reads_as_no_orders` | `agents/execution/tests/test_run_start_orders.py` | as before, `list_orders` given an answer that is not a list returns `[]`, and from `[order, "garbage", {"no": "id"}]` returns the one order (`EXEC-OBS-08`) | red (by import) |

The red/green split above is the planner's tests run on `main` at `70d0eb32`
(`planner_tests_on_unchanged_70d0eb32.txt`): A14 and A15 fail on behaviour (the one-page listing
never shows the expired stop), A16 passes, and the other two files cannot import. Say so in your
output.

---

## Success factors

- [ ] A1 to A17 exist under the names above, each citing its clauses; the red/green split on the
      unchanged tree is the Test plan's; all green after.
- [ ] Appendix sections 1 and 2 applied exactly: every file equals the prototype's blob
      (`prototype_blobs.txt`, OneDrive `trading-agents-data/wq134-2026-10-17/`).
- [ ] No existing test changed; every existing test passes.
- [ ] B1 to B24 each red against your tests, each restored.
- [ ] Every touched module, test files included, under 200 lines after `ruff format`.
- [ ] Version PATCH, `uv.lock` one line changed.
- [ ] `make ci` exit 0, 100.00 % coverage (the dependency audit may be the only step that cannot
      reach its network; say so if it is).
- [ ] **F1 (the planner's, at review, no cost):** `wq134_f1.py` on the built tree and on `main`,
      minutes apart, against the live account with every non-GET refused and graph writes
      suppressed: the same writes digest and the same faults on both; the built tree's head-of-run
      order listings are the `open` and the windowed `all`, each one page, and its broker answer
      bytes are less than a sixth of `main`'s; the pending buys are untouched.
- [ ] **F2 (the planner's, after deploy):** the first weekday night on the new tag runs 8 / 8 with
      no new fault from the reads; execution's first five minutes read under S279's 5 MB; every
      waiting Fill that night is settled as on any night. The first old stop that fills or expires
      (2026-11-10 at the latest) settles and its position carries a stop again by the next run.

---

## Traps

🪤 **A14 and A15 must fail on the unchanged tree on behaviour, not on import.** That is why
`order_read_helpers.py` imports `OrderRef` only under `TYPE_CHECKING` and the expiry file imports
nothing new. If they are red by import there, the test proves nothing about the defect.
🪤 **A16 must pass on the unchanged tree.** It is the evidence that the 2026-11-10 expiry is handled
today; a version of it that fails there is testing something else.
🪤 **`after` and `until` are exclusive** in Alpaca and in the double. A double that treats them as
inclusive hides B2.
🪤 **Do not reuse `run_placement` or `seed_usb_stop` with the doubles.** They are typed for
`PaperBroker`; mypy refuses the doubles. Use `stop_pass_helpers.py`.
🪤 **`detect-secrets` and ruff S106 flag a literal secret argument** (`secret_key="s"`). Use a
neutral module constant (`_FAKE = "x"`) and no `noqa`.
🪤 **`ruff format` grows test files.** Measure sizes after formatting; `order_read_helpers.py` is
186 lines on the prototype and `test_alpaca_order_reads.py` 183.
🪤 **The in-memory store returns list props as tuples.** Compare scalars.
🪤 **Never reach the live broker.** Every test answers from a double; the live read is the planner's
F1.

**Breaks — plant one at a time against your tests, restore each:**

| # | File | Plant |
| --- | --- | --- |
| B1 | `alpaca_order_reads.py` | a listing reads one page (the stop condition is always true) |
| B2 | `alpaca_order_reads.py` | the next page ends at the newest order of the last (`max` for `min`) |
| B3 | `alpaca_order_reads.py` | a listing asks `direction` asc |
| B4 | `alpaca_order_reads.py` | the run start skips the open listing |
| B5 | `alpaca_order_reads.py` | the run start skips the recent listing |
| B6 | `alpaca_order_reads.py` | no waiting order is read |
| B7 | `alpaca_order_reads.py` | the window ignores its days |
| B8 | `alpaca_order_reads.py` | a 404 is raised |
| B9 | `alpaca_order_reads.py` | every refusal reads as not held |
| B10 | `alpaca_order_reads.py` | a waiting order is never read by its broker id |
| B11 | `alpaca_order_reads.py` | an order already listed by key is read again |
| B12 | `alpaca_order_reads.py` | the run start's orders are not newest first |
| B13 | `alpaca.py` | the on-demand read lists open orders only |
| B14 | `alpaca.py` | the Alpaca run start ignores its setting (`days=10`) |
| B15 | `broker_factory.py` | the factory drops the setting |
| B16 | `settings.py` | the setting's floor is 1 |
| B17 | `run_start_orders.py` | no broker narrows |
| B18 | `run_start_orders.py` | a settled Fill waits and an unsettled one does not |
| B19 | `reconciliation.py` | reconciliation names no waiting order |
| B20 | `reconciliation.py` | reconciliation reads `Fill` twice (the refresh lists it again) |
| B21 | `reconciliation_store.py` | the refresh ignores the Fills it is given |
| B22 | `drop_sweep.py` | the sweep lists every order (`broker.fills()`) |
| B23 | `broker_stop_realign.py` | the realign lists every order |
| B24 | `broker_stop_realign.py` | the realign asks for none of its stops |

On the prototype all 24 went red against the planner's own tests (`s283_breaks_on_prototype.txt`).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Sizes after the change: `alpaca.py` **188**, `drop_sweep.py` **184**, `broker_stop_realign.py`
  **182**, `reconciliation_store.py` **169**, `settings.py` **162**. Section 1 places them; add
  nothing to them.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: the window is a `tunable()` with bounds and a PARAM row.
- Faults, not silent failure: a refused order read is raised into the caller's existing fault
  boundary; a 404 is the broker saying it holds no such order.
- `make ci` **every step** green, **100.00 % coverage floor**, redirected to a file, never piped.
- Version bump PATCH, `uv.lock` staged with it.
- A worktree has **no `.env`**. State which tree you ran in.

---

## Sequencing after merge (the planner's)

1. Review: CodeQL set-diff against the S282 remote branch first (133 open, 0 errors); blobs against
   `prototype_blobs.txt`; the planner's tests (`planner_tests/`, swap in at the same paths) on the
   built tree; `s283_breaks.py` against the builder's tests alone; F1 on the built tree and `main`.
2. `make gate-ran` from `../ta-s283`, the SHA checked against `git rev-parse HEAD`; merge; tag.
3. Deploy: diff the tag against the fidelity decision paths (expected: none), then an image-only
   retag; `DeployRecord`; rollback the previous tag. F2; close work-queue 134.

---

## Handover — paste this to Codex

```text
You are building Sprint 283 in the worktree ../ta-s283, on the branch
sprint-283-no-broker-read-is-cut-at-a-page. Never work on main. The worktree and its venv are
ready; never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-283-no-broker-read-is-cut-at-a-page.md, whole, before anything else. It
is the spec, and its bottom sections are your handback. The Appendix holds the production code and
the law text, which you apply exactly. Your work is the tests, the bump and the evidence.

In order:
1. Read agents/execution/laws/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any code.
2. Write agents/execution/tests/order_read_helpers.py and stop_pass_helpers.py, then the tests A1
   to A17 under the exact names and files in the Test plan, each docstring citing its clauses. Run
   them on the unchanged tree with pytest --continue-on-collection-errors and paste the output into
   the Closeout: the red/green split must be the Test plan's last column (A16 passes; A14 and A15
   fail on behaviour, not on import; the other two files cannot import).
3. Apply Appendix section 1 exactly (nine files; alpaca_order_reads.py and run_start_orders.py are
   new). Change nothing else in production code. Change no existing test.
4. Apply Appendix section 2 exactly (execution laws.md, test-plan.md, docs/laws/ledger.md,
   docs/laws/INDEX.md). The test-plan rows name your tests; if a name differs, your name is wrong.
5. Plant the breaks B1 to B24 (Traps) one at a time; each must turn at least one of your tests red;
   restore each before the next. Record each in the Closeout.
6. Bump the version PATCH (0.128.03 -> 0.128.04) in pyproject.toml, run uv lock --offline, stage
   uv.lock. Run make ci redirected to a file and read the file. If the dependency audit is the only
   step that fails for want of network, say so; the planner runs it.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: reach the network or the live broker; run infra/ scripts, pwsh or any az command; change
contracts/, kernel/, any pack or any Dockerfile; change the Broker protocol, the paper broker or
any existing test or test helper; add or reword a law clause beyond section 2; use noqa; let any
module, test files included, reach 200 lines; measure make ci through a pipe.

Traps (the spec's Traps section has them all): A14 and A15 fail on the unchanged tree on
behaviour, so order_read_helpers imports OrderRef only under TYPE_CHECKING; A16 passes there;
after and until are exclusive; use stop_pass_helpers, not run_placement or seed_usb_stop, with the
doubles; no literal secret arguments in tests; ruff format grows test files, measure after
formatting.

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
| *to fill* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *to fill*

**Contradictions found between a law and this spec:** *to fill*

**Laws found silent where a decision was needed:** *to fill*

**Clauses that were ⬜ and are now proven:** *to fill*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | *to fill* | | | |

**Tests added beyond the plan:** *to fill*

---

## Closeout — evidence

**Status:** *to fill (BUILT)*

**Tree the proofs ran in (and `.env` present?):** *to fill*

**Result:** *to fill*

**Files changed:** *to fill*

**Design decisions:** recorded as [`DL-306`](../design-log.md) by the planner.

**Proof — the red run first:**

```text
to fill
```

**Proof — the green run:**

```text
to fill
```

**Guards planted:** *to fill (B1 to B24)*

**Module line counts:** *to fill*

**`make ci`:** *to fill*

**`make gate-ran`:** the planner's, at review.

**Not met / verified failing:** *to fill*

---

## Return notes

- *to fill*

---

## Appendix — the change, measured on the planner's prototype

The planner's prototype is `73bb5f6f`, the local branch `proto-s283` in `../ta-s283-proto`, cut from
`70d0eb32`. Both sections apply with `git apply` to this branch's base. On the prototype `make ci`
exited 0 (5,195 passed, 9 skipped, 100.00 %, the dependency audit clean); its 24 planted breaks went
red against the planner's tests (`s283_breaks_on_prototype.txt`); `wq134_f1.py` printed
`f1_proto.txt`, whose writes digest equals `main`'s (`f1_main_70d0eb32.txt`).

### 1. Production — nine files under `agents/execution/`

```diff
diff --git a/agents/execution/alpaca.py b/agents/execution/alpaca.py
index ef27a092..bebae650 100644
--- a/agents/execution/alpaca.py
+++ b/agents/execution/alpaca.py
@@ -12,11 +12,11 @@ import json
 import urllib.error
 import urllib.parse
 import urllib.request
-from decimal import Decimal
 from typing import TYPE_CHECKING

 from agents.execution import alpaca_orders, alpaca_replace
 from agents.execution.alpaca_account import account_from_payload
+from agents.execution.alpaca_order_reads import current_orders, list_orders, order_fills
 from agents.execution.alpaca_positions import positions_from_payload
 from agents.execution.broker import (
     BrokerAccount,
@@ -24,10 +24,12 @@ from agents.execution.broker import (
     BrokerPosition,
     BrokerRejectedError,
 )
-from contracts.common import Money

 if TYPE_CHECKING:
-    from contracts.common import Ticker
+    from collections.abc import Sequence
+
+    from agents.execution.run_start_orders import OrderRef
+    from contracts.common import Money, Ticker

 _ORDERS_PATH = "/v2/orders"
 _BY_CLIENT_PATH = "/v2/orders:by_client_order_id"
@@ -55,6 +57,7 @@ class AlpacaBroker:
         base_url: str,
         timeout: int,
         order_price_tolerance_bps: int = 0,
+        recent_order_days: int = 10,
     ) -> None:
         """Create an Alpaca broker from injected settings."""
         self._api_key = api_key
@@ -62,6 +65,7 @@ class AlpacaBroker:
         self._base_url = base_url
         self._timeout = timeout
         self._order_price_tolerance_bps = order_price_tolerance_bps
+        self._recent_order_days = recent_order_days

     def submit(
         self,
@@ -118,13 +122,15 @@ class AlpacaBroker:
         )

     def fills(self) -> tuple[BrokerFill, ...]:
-        """Return broker-known order outcomes for reconciliation."""
-        zero = Money(amount=Decimal("0"))
-        return tuple(
-            _fill_from_order(order, str(order["client_order_id"]), zero)
-            for order in self._list_orders()
-            if isinstance(order, dict) and order.get("client_order_id")
-        )
+        """Return every order the broker knows, for on-demand reconciliation."""
+        return order_fills(self._list_orders())
+
+    def current_orders(
+        self, waiting: Sequence[OrderRef] = ()
+    ) -> tuple[BrokerFill, ...]:
+        """Return a run start's orders: the open, the recent and each waiting one."""
+        orders = current_orders(self._request, waiting, days=self._recent_order_days)
+        return order_fills(orders)

     def positions(self) -> tuple[BrokerPosition, ...]:
         """Return read-only Alpaca paper holdings for reconciliation."""
@@ -161,10 +167,8 @@ class AlpacaBroker:
             )
             return self._request("GET", f"{_BY_CLIENT_PATH}?{query}", None)

-    def _list_orders(self) -> list[object]:  # pragma: no cover - real HTTPS
-        query = urllib.parse.urlencode({"status": "all", "limit": 500})
-        payload = self._request("GET", f"{_ORDERS_PATH}?{query}", None)
-        return payload if isinstance(payload, list) else []
+    def _list_orders(self) -> list[object]:
+        return list(list_orders(self._request, "all"))

     def _request(  # pragma: no cover - real HTTPS
         self, method: str, path: str, body: dict[str, object] | None
diff --git a/agents/execution/alpaca_order_reads.py b/agents/execution/alpaca_order_reads.py
new file mode 100644
index 00000000..9fea8042
--- /dev/null
+++ b/agents/execution/alpaca_order_reads.py
@@ -0,0 +1,129 @@
+"""Alpaca order reads: every page of a listing, and the orders a run start needs.
+
+Agent: execution
+Role: list Alpaca orders a page at a time so no listing is cut at the page limit, and
+      read a run start's orders: every open order, every order submitted within the
+      recent window, and each order the graph still waits on (DL-306).
+External I/O: HTTPS to Alpaca through the adapter's injected request callable.
+"""
+
+from __future__ import annotations
+
+import urllib.error
+import urllib.parse
+from datetime import UTC, datetime, timedelta
+from decimal import Decimal
+from typing import TYPE_CHECKING
+
+from agents.execution.alpaca_orders import fill_from_order
+from agents.execution.alpaca_replace import http_error_message
+from contracts.common import Money
+
+if TYPE_CHECKING:
+    from collections.abc import Callable, Iterable, Mapping
+
+    from agents.execution.broker import BrokerFill
+    from agents.execution.run_start_orders import OrderRef
+
+    Request = Callable[[str, str, dict[str, object] | None], object]
+    Order = dict[str, object]
+
+# Alpaca's largest page for GET /v2/orders; a full page means there may be more.
+PAGE_LIMIT = 500
+_ORDERS_PATH = "/v2/orders"
+_BY_CLIENT_PATH = "/v2/orders:by_client_order_id"
+_NOT_FOUND = 404
+
+
+def list_orders(
+    request: Request, status: str, *, after: str | None = None
+) -> list[Order]:
+    """Every order one listing names, newest first, read a page at a time.
+
+    Each next page ends before the oldest order of the last (`until`); the read stops
+    on a page shorter than the limit or one that adds no order it has not seen.
+    """
+    orders: dict[str, Order] = {}
+    until: str | None = None
+    while True:
+        page = _page(request, status, after, until)
+        fresh = [order for order in page if str(order["id"]) not in orders]
+        orders.update((str(order["id"]), order) for order in fresh)
+        if len(page) < PAGE_LIMIT or not fresh:
+            return list(orders.values())
+        until = min(str(order["submitted_at"]) for order in page)
+
+
+def current_orders(
+    request: Request,
+    waiting: Iterable[OrderRef],
+    *,
+    days: int,
+    now: datetime | None = None,
+) -> list[Order]:
+    """Every open order, every order of the last `days`, and each waiting order."""
+    since = (now or datetime.now(tz=UTC)) - timedelta(days=days)
+    orders = {str(order["id"]): order for order in list_orders(request, "open")}
+    for order in list_orders(request, "all", after=since.isoformat()):
+        orders.setdefault(str(order["id"]), order)
+    keys = {str(order.get("client_order_id", "")) for order in orders.values()}
+    for ref in waiting:
+        if ref.broker_order_id in orders or ref.idempotency_key in keys:
+            continue
+        found = order_for(request, ref)
+        if found is not None:
+            orders[str(found["id"])] = found
+            keys.add(str(found.get("client_order_id", "")))
+    return sorted(orders.values(), key=_submitted_at, reverse=True)
+
+
+def order_for(request: Request, ref: OrderRef) -> Order | None:
+    """One order by its broker id, else by its client order id; None when unknown.
+
+    The broker's 404 means it holds no such order; any other refusal is raised with
+    the broker's own message, so the caller's fault boundary records it.
+    """
+    if ref.broker_order_id:
+        path = f"{_ORDERS_PATH}/{urllib.parse.quote(ref.broker_order_id, safe='')}"
+    else:
+        query = urllib.parse.urlencode({"client_order_id": ref.idempotency_key})
+        path = f"{_BY_CLIENT_PATH}?{query}"
+    try:
+        order = request("GET", path, None)
+    except urllib.error.HTTPError as exc:
+        if exc.code == _NOT_FOUND:
+            return None
+        raise RuntimeError(http_error_message(exc)) from exc
+    return order if isinstance(order, dict) and order.get("id") else None
+
+
+def order_fills(orders: Iterable[object]) -> tuple[BrokerFill, ...]:
+    """Map each order that carries a client order id to the broker port's fill."""
+    zero = Money(amount=Decimal("0"))
+    return tuple(
+        fill_from_order(order, str(order["client_order_id"]), zero)
+        for order in orders
+        if isinstance(order, dict) and order.get("client_order_id")
+    )
+
+
+def _page(
+    request: Request, status: str, after: str | None, until: str | None
+) -> list[Order]:
+    query: dict[str, object] = {
+        "status": status,
+        "limit": PAGE_LIMIT,
+        "direction": "desc",
+    }
+    if after is not None:
+        query["after"] = after
+    if until is not None:
+        query["until"] = until
+    payload = request("GET", f"{_ORDERS_PATH}?{urllib.parse.urlencode(query)}", None)
+    if not isinstance(payload, list):
+        return []
+    return [order for order in payload if isinstance(order, dict) and order.get("id")]
+
+
+def _submitted_at(order: Mapping[str, object]) -> str:
+    return str(order.get("submitted_at", ""))
diff --git a/agents/execution/broker_factory.py b/agents/execution/broker_factory.py
index 2cb7e8e2..f3870acf 100644
--- a/agents/execution/broker_factory.py
+++ b/agents/execution/broker_factory.py
@@ -27,6 +27,7 @@ def broker_from_settings(settings: ExecutionSettings) -> Broker:
             base_url=settings.alpaca_base_url,
             timeout=settings.alpaca_timeout,
             order_price_tolerance_bps=settings.order_price_tolerance_bps,
+            recent_order_days=settings.broker_recent_order_days,
         )
     return PaperBroker(
         slippage_bps=settings.slippage_bps,
diff --git a/agents/execution/broker_stop_realign.py b/agents/execution/broker_stop_realign.py
index cd8620ff..187604d1 100644
--- a/agents/execution/broker_stop_realign.py
+++ b/agents/execution/broker_stop_realign.py
@@ -22,6 +22,7 @@ from agents.execution.broker_stop_writes import (
     write_stop_fill,
     write_stop_order,
 )
+from agents.execution.run_start_orders import OrderRef, run_start_orders
 from contracts.broker_stops import active_broker_stop_orders, free_broker_stop_order_key
 from contracts.stop_rule import stop_price_cents
 from kernel import AgentFault
@@ -87,8 +88,9 @@ def _mismatched(
 def _order_statuses(
     broker: Broker, sink: FaultSink, targets: list[_Target]
 ) -> dict[str, str | None] | None:
+    waiting = tuple(OrderRef(stop.broker_order_id, stop.key) for _, stop, _ in targets)
     try:
-        orders = broker.fills()
+        orders = run_start_orders(broker, waiting)
     except Exception as exc:
         for target in targets:
             _record(
diff --git a/agents/execution/drop_sweep.py b/agents/execution/drop_sweep.py
index 93114f45..97a2ba72 100644
--- a/agents/execution/drop_sweep.py
+++ b/agents/execution/drop_sweep.py
@@ -18,6 +18,7 @@ from agents.execution.drop_sweep_records import (
     record_stop_mismatch,
     remember_execution_run,
 )
+from agents.execution.run_start_orders import run_start_orders
 from contracts.broker_lifecycle import (
     is_broker_stop_order,
     is_resolved_drop_status,
@@ -95,7 +96,7 @@ def _read_broker_orders(broker: Broker, sink: FaultSink) -> tuple[BrokerFill, ..
         capability="drop_unfilled_orders",
         reraise=False,
     ) as capture:
-        orders = broker.fills()
+        orders = run_start_orders(broker)
     return () if capture.fault is not None else orders


diff --git a/agents/execution/reconciliation.py b/agents/execution/reconciliation.py
index fea9c88c..e0cf5cc9 100644
--- a/agents/execution/reconciliation.py
+++ b/agents/execution/reconciliation.py
@@ -15,6 +15,7 @@ from agents.execution.reconciliation_store import (
     refresh_pending_fills,
     write_snapshot,
 )
+from agents.execution.run_start_orders import run_start_orders, waiting_order_refs
 from kernel import fault_boundary

 if TYPE_CHECKING:
@@ -24,6 +25,7 @@ if TYPE_CHECKING:
         BrokerFill,
         BrokerPosition,
     )
+    from agents.execution.run_start_orders import OrderRef
     from kernel import FaultSink, GraphStore, Node


@@ -39,9 +41,10 @@ def reconcile_run_start(
     graph: GraphStore, broker: Broker, sink: FaultSink, *, run_id: str
 ) -> Node | None:
     """Run fail-open broker reconciliation before execution submits new intents."""
-    broker_fills = _read_fills(broker, sink)
+    fills = graph.list_nodes("Fill")
+    broker_fills = _read_fills(broker, sink, waiting_order_refs(fills))
     if broker_fills is not None:
-        refresh_pending_fills(graph, broker_fills, sink)
+        refresh_pending_fills(graph, broker_fills, sink, fills=fills)
     positions, stale_reason = _read_positions(broker, sink)
     if positions is None:
         return write_snapshot(
@@ -75,9 +78,11 @@ def reconcile_run_start(
     return snapshot


-def _read_fills(broker: Broker, sink: FaultSink) -> tuple[BrokerFill, ...] | None:
+def _read_fills(
+    broker: Broker, sink: FaultSink, waiting: tuple[OrderRef, ...]
+) -> tuple[BrokerFill, ...] | None:
     try:
-        return broker.fills()
+        return run_start_orders(broker, waiting)
     except Exception as exc:
         _record_fault(sink, f"broker fills read failed: {type(exc).__name__}")
         return None
diff --git a/agents/execution/reconciliation_store.py b/agents/execution/reconciliation_store.py
index 17478988..218b8a88 100644
--- a/agents/execution/reconciliation_store.py
+++ b/agents/execution/reconciliation_store.py
@@ -19,11 +19,13 @@ from agents.execution.fill_attempts import broker_idempotency_key
 from agents.execution.order_status_store import write_order_status
 from agents.execution.partial_fill import report_unfilled_remainder
 from agents.execution.realized_pnl import realized_pnl_props
+from agents.execution.run_start_orders import awaits_broker
 from agents.execution.snapshot_account import account_snapshot_props
-from contracts.broker_lifecycle import is_terminal_fill_broker_status
 from contracts.positions import is_active_position_node

 if TYPE_CHECKING:
+    from collections.abc import Iterable
+
     from agents.execution.broker import BrokerAccount, BrokerFill, BrokerPosition
     from kernel import FaultSink, GraphStore, Node

@@ -31,17 +33,22 @@ SnapshotStatus = Literal["fresh", "stale"]


 def refresh_pending_fills(
-    graph: GraphStore, broker_fills: tuple[BrokerFill, ...], sink: FaultSink
+    graph: GraphStore,
+    broker_fills: tuple[BrokerFill, ...],
+    sink: FaultSink,
+    *,
+    fills: Iterable[Node] | None = None,
 ) -> None:
-    """Append broker terminal-status evidence to pending Fill nodes."""
+    """Append broker terminal-status evidence to pending Fill nodes.
+
+    `fills` is the `Fill` label when the caller has read it already (EXEC-PERF-02).
+    """
     by_key = {fill.idempotency_key: fill for fill in broker_fills}
     by_order_id = {
         fill.broker_order_id: fill for fill in broker_fills if fill.broker_order_id
     }
-    for node in graph.list_nodes("Fill"):
-        if node.props.get("status") != "pending":
-            continue
-        if is_terminal_fill_broker_status(node.props.get("broker_status")):
+    for node in graph.list_nodes("Fill") if fills is None else fills:
+        if not awaits_broker(node):
             continue
         broker_fill = by_key.get(broker_idempotency_key(node)) or by_order_id.get(
             str(node.props.get("broker_order_id", ""))
diff --git a/agents/execution/run_start_orders.py b/agents/execution/run_start_orders.py
new file mode 100644
index 00000000..dfb5148d
--- /dev/null
+++ b/agents/execution/run_start_orders.py
@@ -0,0 +1,65 @@
+"""The broker orders a run start reads: narrowed where the broker can, never cut.
+
+Agent: execution
+Role: name the broker orders the graph still waits on, and read the run start's orders
+      through the broker's narrow read when it offers one, else every order (DL-306).
+External I/O: injected Broker reads.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING, NamedTuple, Protocol, runtime_checkable
+
+from agents.execution.fill_attempts import broker_idempotency_key
+from contracts.broker_lifecycle import is_terminal_fill_broker_status
+
+if TYPE_CHECKING:
+    from collections.abc import Iterable, Sequence
+
+    from agents.execution.broker import Broker, BrokerFill
+    from kernel import Node
+
+
+class OrderRef(NamedTuple):
+    """One broker order the graph waits on: its broker id (may be empty) and key."""
+
+    broker_order_id: str
+    idempotency_key: str
+
+
+@runtime_checkable
+class NarrowOrderReads(Protocol):
+    """A broker that can read only the orders a run start needs."""
+
+    def current_orders(
+        self, waiting: Sequence[OrderRef] = ()
+    ) -> tuple[BrokerFill, ...]:
+        """Every open order, every recent order, and each waiting order."""
+        ...  # pragma: no cover - protocol declaration only.
+
+
+def run_start_orders(
+    broker: Broker, waiting: Sequence[OrderRef] = ()
+) -> tuple[BrokerFill, ...]:
+    """The narrow read where the broker offers one; every order it knows otherwise."""
+    if isinstance(broker, NarrowOrderReads):
+        return broker.current_orders(waiting)
+    return broker.fills()
+
+
+def awaits_broker(fill: Node) -> bool:
+    """Whether a Fill still waits on the broker's account (EXEC-STA-05)."""
+    return fill.props.get("status") == "pending" and not is_terminal_fill_broker_status(
+        fill.props.get("broker_status")
+    )
+
+
+def waiting_order_refs(fills: Iterable[Node]) -> tuple[OrderRef, ...]:
+    """The broker order behind every Fill the refresh still waits on."""
+    return tuple(
+        OrderRef(
+            str(fill.props.get("broker_order_id") or ""), broker_idempotency_key(fill)
+        )
+        for fill in fills
+        if awaits_broker(fill)
+    )
diff --git a/agents/execution/settings.py b/agents/execution/settings.py
index b4bae553..eb8974ed 100644
--- a/agents/execution/settings.py
+++ b/agents/execution/settings.py
@@ -120,6 +120,16 @@ class ExecutionSettings(AgentSettings):
         le=60,
         unit="seconds",
     )
+    broker_recent_order_days: int = tunable(
+        10,
+        why=(
+            "How far back a run start lists orders by submission (DL-306): longer "
+            "than the longest gap between two runs, so no order ends unseen."
+        ),
+        ge=4,
+        le=60,
+        unit="days",
+    )
     deliberation_grace_seconds: int = tunable(
         default=900,
         ge=0,
```

### 2. The law — the execution book, its test plan, the ledger and INDEX rows

```diff
diff --git a/agents/execution/laws/laws.md b/agents/execution/laws/laws.md
index 6005b0fa..b6456dce 100644
--- a/agents/execution/laws/laws.md
+++ b/agents/execution/laws/laws.md
@@ -1,6 +1,6 @@
 # `Execution` — Laws

-**Prefix:** `EXEC` · **status:** LOCKED v1.15 · **Owner:** Yury Gurevich
+**Prefix:** `EXEC` · **status:** LOCKED v1.16 · **Owner:** Yury Gurevich

 > Be the single, auditable, idempotent broker boundary. Execute only what the portfolio
 > manager has approved and the stage gate allows.
@@ -332,6 +332,16 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   whatever that ticker's history. A live divergence always has exactly one unresolved Flag, and an
   absent one has none. *(Declares the behaviour S178 built and never declared; repaired by S248 /
   DL-254 after DL-253 measured each ticker's keys spent once, for ever.)*
+- **EXEC-OBS-08** — No broker read is cut at a page limit. Run-start reconciliation reads the
+  broker's account of every order the graph still waits on — each `Fill` not yet settled
+  (`EXEC-STA-05`) — whatever the number of orders the account holds: an order no listing shows is
+  read by its broker id, or by its idempotency key when the `Fill` has no broker id, and an order
+  the broker answers it does not hold is left out. The drop sweep and the stop realignment read
+  every open order and every order submitted within `broker_recent_order_days`, the realignment
+  also the stops it would move. The on-demand `reconcile` reads every order the broker knows, a
+  page at a time. A broker that cannot narrow its read lists every order. *(Declares the fix
+  decided in DL-306; work-queue 134: the newest-500 listing passes 500 orders around early
+  December 2026, after which an old resting stop that triggered or expired was never read.)*

 ---

@@ -347,6 +357,12 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   once for every active position's decided width, and not at all when no position is
   broker-adopted. A failed read in the sweep is one contained fault and no order is touched.
   *(Declares the bound decided in DL-302; measured 126.3 MB of 136 MB per run start before it.)*
+- **EXEC-PERF-03** — A run-start broker read is bounded by the book, not by the account's history:
+  one listing of open orders, one of the orders submitted within `broker_recent_order_days`, and
+  one order read for each waiting `Fill` neither listing shows; an order is returned once however
+  many of those name it. Run-start reconciliation reads `Fill` once for both its waiting orders and
+  its refresh. *(Declares the bound decided in DL-306; measured 313 KB for 353 orders per read,
+  up to four reads a night, before it.)*

 ---

@@ -414,6 +430,7 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 | `alpaca_secret_key` | — | `SecretStr` | NO (secret) | Alpaca paper secret key; never logged or returned |
 | `alpaca_base_url` | `"https://paper-api.alpaca.markets"` | `str` | YES (environment) | Alpaca base URL; switch to live URL only when stage=live* and operator-approved |
 | `alpaca_timeout` | `15` | `int ≥ 1, ≤ 60` (seconds) | YES | Per-order broker call timeout; bounded latency budget per submission |
+| `broker_recent_order_days` | `10` | `int ≥ 4, ≤ 60` (days) | YES | How far back a run start lists orders by submission (`EXEC-OBS-08`, `EXEC-PERF-03`). Longer than the longest gap between two weekday runs (four days over a holiday weekend), so an order with no `Fill` that ended between runs is still seen; a waiting `Fill`'s order is read by id whatever its age |
 | `order_price_tolerance_mode` | `"flat"` | `Literal["flat","scaled"]` — config | NO (mode selector) | ADR-0013 champion–challenger selector; `flat` is the champion. Not a tunable — switching it changes which formula runs, not a value within one |
 | `order_price_tolerance_bps` | `50` | `int ≥ 0, ≤ 500` (bps) | YES | Bounds entry and discretionary-exit orders near the PM's decided price so after-close decisions do not trade at an unevaluated open (ADR-0018) |
 | `scaled_order_price_tolerance_atr_multiplier` | `0.50` | `float ≥ 0.0, ≤ 2.0` (ratio) | YES | Challenger band near half of decision-time daily ATR; observed overnight gaps cluster at 0.3–0.6× ATR |
@@ -549,3 +566,9 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   reader of an executed size reads it. `EXEC-OBS-06` matches an adopted position on the quantity
   the broker filled. Why: UNH's 1 of 2 on 2026-10-15 was written dropped and its share adopted
   on the fallback stop. 41 / 67 -> 43 / 68.
+- **v1.16 — S283 / DL-306 (2026-10-17).** New `EXEC-OBS-08`: no broker read is cut at a page
+  limit; run-start reconciliation reads every order the graph waits on, by id where no listing
+  shows it. New `EXEC-PERF-03`: a run-start broker read is bounded by the book (open orders, the
+  recent window, the waiting Fills). New PARAM row `broker_recent_order_days`. Why: the listing
+  was the newest 500 of an account at 353 orders and three more a day. No drop, cancel, stop or
+  reconciliation decision changes; 43 / 68 -> 45 / 70.
diff --git a/agents/execution/laws/test-plan.md b/agents/execution/laws/test-plan.md
index dfae7a5c..9079feb2 100644
--- a/agents/execution/laws/test-plan.md
+++ b/agents/execution/laws/test-plan.md
@@ -107,6 +107,7 @@ Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID
 | EXEC-OBS-05 | Liveness of an execution broker fact is asked in exactly one place; a terminal BrokerStopOrder is not live regardless of cancelled_at; a resting-stop Fill is not an open order; and the sweep compares broker and graph stop identity instead of liveness views. | observable | `tests/test_broker_stop_liveness.py::test_filled_sibling_fill_makes_uncancelled_stop_inactive`; `tests/test_broker_fill_lifecycle.py::test_resting_stop_fill_is_not_an_open_order_fill`; `tests/test_broker_fill_lifecycle.py::test_pending_buy_fill_is_an_open_order_fill`; `agents/execution/tests/test_drop_sweep_identity.py::test_fired_stop_with_unrefreshed_graph_status_raises_no_mismatch`; `agents/execution/tests/test_drop_sweep_identity.py::test_graph_stop_identity_mismatch_still_faults`; `agents/execution/tests/test_drop_sweep_liveness.py::test_sweep_raises_no_mismatch_for_dead_stop_order`; `agents/execution/tests/test_drop_sweep_liveness.py::test_live_stop_mismatch_fault_carries_context`; `tests/test_broker_lifecycle_invariants.py::test_broker_lifecycle_vocabulary_lives_in_one_module`; `tests/test_broker_lifecycle_invariants.py::test_broker_order_lifecycle_status_drives_live_stop_orders`; S230: `tests/test_broker_stop_replaced.py::test_a_replaced_order_is_not_live`; `::test_a_replaced_at_marker_ends_the_fact_without_deleting_it` | 🟩 |
 | EXEC-OBS-06 | The broker stop is the PM-decided stop: its width comes through the one shared resolver (an adopted position takes the stop_pct of the one filled production buy equal in the quantity the broker filled and in broker price, otherwise the fallback) and every stop fact records stop_pct_source lineage/position/fallback; a live stop one cent or more off its decided price is replaced in place, never cancelled and re-placed, with replaced_at/replaced_by markers on the old fact and replaces on the new; a replacement is refused with a warning fault and the old stop left live when the order is not new, when the decided stop is at or above the current price, or when the broker refuses, and is retried next run. | failure | `tests/test_stop_width.py::test_the_resolver_returns_the_width_the_pm_decided`; `::test_all_three_readers_agree_on_the_decided_stop`; `::test_an_older_lot_of_another_size_does_not_match`; `::test_no_exact_match_falls_back_and_says_so`; `::test_a_fill_path_position_keeps_its_own_width`; `::test_an_exact_buy_that_decided_no_width_is_not_lineage`; `::test_a_verification_fill_is_never_lineage`; `::test_a_position_with_no_width_needs_a_fallback`; `test_broker_stop_realign.py::test_a_mismatched_new_stop_is_replaced_in_place`; `::test_an_accepted_stop_is_not_replaced`; `::test_a_stop_is_never_moved_to_or_above_the_market`; `::test_a_failed_replace_keeps_the_old_stop_and_retries`; `::test_a_failed_replace_leaves_no_marker`; `::test_a_matching_stop_is_left_alone`; `::test_replacement_is_idempotent_across_runs`; `test_broker_stop_replace_adapters.py::test_alpaca_replace_patches_the_stop_price_under_the_new_key`; `::test_alpaca_refusal_carries_the_broker_message`; `::test_alpaca_rejected_replacement_raises`; `::test_paper_broker_models_alpacas_refusal_of_an_accepted_stop`; `::test_unreadable_broker_orders_leave_every_stop_and_fault`; `::test_a_stop_the_broker_does_not_list_is_skipped_as_unknown`; `test_partial_fill_refresh.py::test_the_adopted_share_takes_the_decided_stop`; `::test_the_entry_stop_covers_only_the_shares_the_broker_filled` | 🟩 |
 | EXEC-OBS-07 | A broker-position divergence is flagged per episode: the episode opens with a `warn` at the run-start reconciliation that first sees it, under a subject naming its kind, ticker and first-sight snapshot; it becomes `critical` only when still present at the next run-start reconciliation, its `warn` closed as superseded; it closes by an appended FlagResolution, never by changing or deleting a Flag, when the divergence is gone; a divergence seen again after its episode closed opens a new episode at `warn` whatever the ticker's history; a live divergence always has exactly one unresolved Flag and an absent one none. | lifecycle | S248: `test_reconciliation_flag_episodes.py::test_a_second_episodes_first_sighting_is_warn`; `::test_a_third_episode_is_flagged_and_escalates_when_it_survives`; `::test_a_live_divergence_always_has_exactly_one_open_flag`; `::test_nothing_already_written_is_rewritten`; `test_reconciliation_flag_upgrade.py::test_an_open_suffixless_flag_is_the_open_episode`; `::test_spent_suffixless_keys_do_not_touch_a_new_episode`; `::test_the_subject_is_deterministic_and_well_formed`; `::test_a_repeated_call_for_one_snapshot_is_not_a_survived_run`; `::test_an_open_critical_supersedes_a_stray_open_warn`; `::test_a_spent_critical_key_is_never_rewritten`; `::test_each_call_reads_flag_and_resolution_once`; re-cited from `EXEC-TRG-07`: `test_reconciliation_flags.py::test_first_sight_of_a_divergence_is_warn_not_critical`; `::test_a_divergence_surviving_a_run_escalates_to_critical`; `::test_repeating_a_divergence_never_mints_a_second_unresolvable_flag`; `::test_an_adopted_divergence_is_retired_on_the_next_run` | 🟩 |
+| EXEC-OBS-08 | No broker read is cut at a page limit: run-start reconciliation reads every order the graph waits on (each unsettled Fill) whatever the account's order count, by broker id or by key where no listing shows it, leaving out an order the broker does not hold; the sweep and the realign read every open and every recent order, the realign also its stops; the on-demand reconcile reads every order a page at a time; a broker that cannot narrow lists every order. | paging + waiting + by key + not held + refusal + e2e expiry | `agents/execution/tests/test_alpaca_order_reads.py::test_a_listing_past_one_page_reads_every_order`; `agents/execution/tests/test_alpaca_order_reads.py::test_fills_reads_every_order_the_broker_knows`; `agents/execution/tests/test_alpaca_order_reads.py::test_the_run_start_read_holds_open_recent_and_waiting_orders`; `agents/execution/tests/test_alpaca_order_reads.py::test_a_waiting_order_with_no_broker_id_is_read_by_its_client_order_id`; `agents/execution/tests/test_alpaca_order_reads.py::test_a_waiting_order_the_broker_does_not_know_is_left_out`; `agents/execution/tests/test_run_start_orders.py::test_waiting_refs_name_every_unsettled_fill_and_no_settled_one`; `agents/execution/tests/test_run_start_orders.py::test_a_broker_without_a_narrow_read_lists_everything`; `agents/execution/tests/test_run_start_orders.py::test_a_listing_answer_that_is_not_a_list_reads_as_no_orders`; `agents/execution/tests/test_stop_expiry_beyond_page.py::test_the_refresh_settles_an_old_stop_the_listing_no_longer_shows`; `agents/execution/tests/test_stop_expiry_beyond_page.py::test_a_stop_the_broker_expires_beyond_the_page_is_placed_again` | 🟩 |

 ## S204 row declarations

@@ -121,6 +122,7 @@ Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID
 | EXEC-FAIL-04 | Restart must rebuild the in-process recorded-fill cache from graph Fill nodes. | recovery | _tbd_ | ⬜ |
 | EXEC-PERF-01 | Sequential broker submission latency must be bounded by alpaca_timeout across a typical five-order set. | performance | _tbd_ | ⬜ |
 | EXEC-PERF-02 | A pass reads a whole graph label once, never per item: the run-start drop sweep reads Fill and BrokerStopOrder at most once each and neither with no orders; later orders see each written drop as a fresh read would. A stop-threshold plan reads Fill at most once across all active positions and never without an adopted position. Failed sweep reads emit one contained fault and touch no order. | sweep + read-back + failure + plan + lazy + source guard | `agents/execution/tests/test_drop_sweep_reads.py::test_a1_one_sweep_reads_each_label_once`; `agents/execution/tests/test_drop_sweep_reads.py::test_a2_the_run_start_reads_fill_twice_whatever_the_orders`; `agents/execution/tests/test_drop_sweep_reads.py::test_a3_a_drop_in_the_sweep_is_seen_by_a_later_order`; `agents/execution/tests/test_drop_sweep_reads.py::test_a4_no_broker_order_reads_no_label`; `agents/execution/tests/test_drop_sweep_reads.py::test_a5_a_failed_read_is_one_fault_and_no_cancel`; `tests/test_stop_width_reads.py::test_a7_executions_stop_plan_reads_fill_once`; `tests/test_stop_width_reads.py::test_a9_a_book_with_no_adopted_position_reads_no_fill`; `tests/test_stop_width_reads_guard.py::test_a11_every_resolver_call_shares_its_pass_read` | 🟩 |
+| EXEC-PERF-03 | A run-start broker read is bounded by the book: one listing of open orders, one of the recent window, one order read per waiting Fill neither shows; each order returned once; reconciliation reads Fill once for its waiting orders and its refresh. | window + once + Fill once + narrow callers | `agents/execution/tests/test_alpaca_order_reads.py::test_the_run_start_read_holds_open_recent_and_waiting_orders`; `agents/execution/tests/test_alpaca_order_reads.py::test_the_recent_window_starts_the_configured_days_ago`; `agents/execution/tests/test_alpaca_order_reads.py::test_an_order_already_listed_is_read_once`; `agents/execution/tests/test_alpaca_order_reads.py::test_the_window_is_a_bounded_setting_the_factory_hands_on`; `agents/execution/tests/test_run_start_orders.py::test_run_start_reconciliation_reads_fill_once_and_names_its_waiting_orders`; `agents/execution/tests/test_run_start_orders.py::test_the_sweep_and_the_realign_take_the_narrow_read` | 🟩 |
 | EXEC-SEC-02 | Execution's broker authority must be isolated behind allowed_callers. | security | _tbd_ | ⬜ |
 | EXEC-SEC-05 | Removing the portfolio.orders.ready subscription must quarantine execution without corrupting in-flight data. | quarantine | _tbd_ | ⬜ |
 | EXEC-DEP-01 | Execution bus dependency stands on the Layer-0 bus charter for subscribe/publish and claim-check resolve. | structural | dependencies.md DEP-BUS-* + probes/checks.py | 🧱 |
diff --git a/docs/laws/INDEX.md b/docs/laws/INDEX.md
index a01725d7..91244040 100644
--- a/docs/laws/INDEX.md
+++ b/docs/laws/INDEX.md
@@ -43,7 +43,7 @@ Each agent's law files live at `agents/<name>/laws/`:
 | scanner | ✅ LOCKED v1.5 (S259, DL-276) | 18 / 41 | S259 (DL-276) reconciles `PARAM` only: the upper bound of `min_average_volume` follows the code, no clause changes; S251 names the graph-pull trigger in `SCAN-TRG-02` (DRIFT-085) and narrows `SCAN-TYP-01`'s version sentence (DRIFT-060); DL-203 reconciles `PARAM` only; S205 rewrites `SCAN-TYP-01` into required fields and closes DRIFT-047 without moving the count; S183's `SCAN-OUT-06`/`SCAN-OUT-07`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | portfolio_manager | ✅ LOCKED v1 (S70), amended **v1.12** (S259, DL-276) | 33 / 51 | S259 (DL-276) reconciles `PARAM` only: the bounds of six rows follow the code, no clause changes; S251 narrows `PM-OBS-01`/`PM-OUT-06`/`PM-STA-04` (no PM snapshot; DRIFT-039), `PM-OBS-04` (per candidate; DRIFT-065), uses emitted strings in `PM-OUT-03` (DRIFT-037), names graph-pull in `PM-TRG-02` (DRIFT-086), narrows `PM-TYP-03`'s version sentence (DRIFT-060); files DRIFT-098; S240 adds and proves `PM-IN-05`: held names weighed once per ticker at the run's own snapshot marks, a resumed run at the snapshot of the run it resumes (DRIFT-079 closed); DL-203 reconciles `PARAM` only; S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders applied weights; S211 adds and proves `PM-OBS-05`: reward-risk compares measured target evidence against stop risk and can reject measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows; S204 gives every clause a row and makes rowless clauses a hard gate |
 | deliberator | ✅ LOCKED v1.18 (S277, DL-289) | 35 / 66 | S277 (DL-289 amendment 4) adds and proves DLIB-FAIL-05, refusal-only sticky switching with one model-attributed row per attempt; re-proves DLIB-FAIL-01, DLIB-OUT-02 (always-written llm_switches) and DLIB-DEP-05 (handed-over fallback construction). S276 (DL-289 amendment 1) adds and proves DLIB-DEP-05 and DLIB-NEV-11; amended DLIB-OUT-02 re-proven for the models that answered; effort defaults to empty. Before that S257 (DL-274) reconciles `PARAM` only: `max_tokens` defaults to 16,384 with the same upper bound and `request_timeout_seconds` may reach 300, no clause changes; S256 (DL-272) adds and proves `DLIB-IDM-04` (settle-on-take and visible reply faults), `DLIB-OBS-08` (every completion, including a repeat, is its own row), and proves spend attribution `DLIB-OBS-02`; S255 (DL-269) adds and proves `DLIB-OUT-08`: recorded arithmetic reproduces before rendering, with first-failure withholding and old-packet parity; DRIFT-102/103 corrected; S254 / ADR-0032 adds and proves `DLIB-NEV-10`: prompt libraries reach vendors only through the agent's own client; before that S252 / DL-261: `DLIB-TRG-01` now proven for the key-and-edge candidate bound and order-property filter, 27 / 59. S246 adds and proves `DLIB-OUT-06` (each debater turn records its guided reasoning exactly as written, or why it could not be read, never failing the turn or the order) and `DLIB-OUT-07` (each debated order's record carries its decision and evidence packet), and amends `DLIB-TYP-01`; S245 adds and proves `DLIB-NEV-09` (every fact a role prompt states about our code is pinned to that code; the false calendar-day staleness fact removed, DRIFT-092); DL-203 reconciles `PARAM` only; S222 moves the vendor adapters to `kernel/` and proves `DLIB-SEC-02` key containment; S214 narrows `vetoed_tickers` to `overturn` verdicts only, routes unreadable judge answers through loud fail-open, and proves `DLIB-OUT-04`; S206 adds and proves `DLIB-NEV-08`; S205 rewrites and proves `DLIB-TYP-01`; S200 adds `DLIB-OBS-07` and turns `DLIB-IDM-02` green by hashing the system prompt too; S199 adds `DLIB-OBS-05`/`DLIB-OBS-06`; S172 proves concurrent-order record order and pending-reply handling; S194 added `DLIB-OBS-04`; S189 added stop-reason audit evidence; S167 added `DLIB-OBS-03` proof |
-| execution | ✅ LOCKED **v1.15** (S280, DL-303) | 43 / 68 | S280 (DL-303) amends and proves `EXEC-OUT-07` (an order the broker ended after filling part of it is a fill of that part, its rest told once) and adds and proves `EXEC-TYP-04` (`Fill.broker_filled_quantity`, read by every reader of an executed size); `EXEC-OBS-06` matches on the filled quantity. S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault; the stop plan shares one lazy Fill read; no decision changes. S258 (DL-276) reconciles `PARAM` only: the bounds of `slippage_bps`, `min_promotion_runs`, `min_approval_rate` and `alpaca_timeout` follow the code, no clause changes; S252 / DL-261: `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66. S251 adds and proves `EXEC-IDN-04` (the divergence-family Flag exception, `owns_graph` widened; DRIFT-094), names the contract's fields in `EXEC-OUT-01/02/04/05` (DRIFT-061) and narrows `EXEC-TYP-03`'s version sentence (DRIFT-060); S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode, `critical` only when it survived a run, whatever the ticker's history; S230 adds/proves `EXEC-OBS-06`: the broker stop is the PM-decided stop, read through the shared resolver, and a mismatched live stop is replaced in place with `replaced_at`/`replaces` markers; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; DL-203 reconciles `PARAM` only; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 adds/proves `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
+| execution | ✅ LOCKED **v1.16** (S283, DL-306) | 45 / 70 | S283 (DL-306) adds and proves `EXEC-OBS-08` (no broker read is cut at a page limit; run-start reconciliation reads every order the graph waits on, by id where no listing shows it) and `EXEC-PERF-03` (a run-start broker read is bounded by the book), with PARAM row `broker_recent_order_days`. S280 (DL-303) amends and proves `EXEC-OUT-07` (an order the broker ended after filling part of it is a fill of that part, its rest told once) and adds and proves `EXEC-TYP-04` (`Fill.broker_filled_quantity`, read by every reader of an executed size); `EXEC-OBS-06` matches on the filled quantity. S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault; the stop plan shares one lazy Fill read; no decision changes. S258 (DL-276) reconciles `PARAM` only: the bounds of `slippage_bps`, `min_promotion_runs`, `min_approval_rate` and `alpaca_timeout` follow the code, no clause changes; S252 / DL-261: `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66. S251 adds and proves `EXEC-IDN-04` (the divergence-family Flag exception, `owns_graph` widened; DRIFT-094), names the contract's fields in `EXEC-OUT-01/02/04/05` (DRIFT-061) and narrows `EXEC-TYP-03`'s version sentence (DRIFT-060); S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode, `critical` only when it survived a run, whatever the ticker's history; S230 adds/proves `EXEC-OBS-06`: the broker stop is the PM-decided stop, read through the shared resolver, and a mismatched live stop is replaced in place with `replaced_at`/`replaces` markers; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; DL-203 reconciles `PARAM` only; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 adds/proves `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | monitor | ✅ LOCKED v1.4 (S279, DL-302) | 22 / 47 | S279 (DL-302) adds and proves `MON-PERF-03`: the end-of-run evaluation shares one lazy Fill read across the book and retains each decided width; no decision changes. S252 / DL-261: `MON-TRG-02` bounds both work kinds, sync from requests and their linked snapshot; DRIFT-097 corrected, 21 / 46 unchanged. S251 names the graph-pull triggers in `MON-TRG-02` (DRIFT-086) and files DRIFT-097 for the unbounded sync poll; S205 rewrites and proves `MON-TYP-01`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | reporter | ✅ LOCKED v1.5 (S253, DL-262, DL-263) | 26 / 43 | S253 rewrites `RPT-OUT-02` (book counts from the broker's fills in the run's window, outcomes since the inception; DRIFT-099), amends `RPT-IN-01` and `RPT-NEV-03` (DRIFT-101), and adds and proves `RPT-IDM-04`; S251 names the run's own benchmark lineage in `RPT-OUT-07` (DRIFT-087) and the graph-pull trigger in `RPT-TRG-02` (DRIFT-086); v1.3 (DL-224) latest-per-date snapshot; S226 adds benchmark-relative `performance_metrics`, as-of bounded graph reads, contained performance failure, and backward-compatible snapshots; S205 rewrites `RPT-TYP-01`; S156 removed orphan `RPT-OBS-03`; S204 gives every clause a row and makes rowless clauses a hard gate |
 | forecaster | ✅ LOCKED v1.10 (S252, DL-261) | 25 / 52 | S252 / DL-261: `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged. S251 names the four legs (`FORE-IDN-01`), one node per prediction (`FORE-OBS-01`; DRIFT-081) and the shadow scorecards' subject (`FORE-IDM-03`; DRIFT-083); S243 amends and re-proves `FORE-FAIL-04` (a designed refusal is a `warning`, a missing input an `error`); S241 adds and proves `FORE-OUT-08`, `FORE-IDM-05`, `FORE-FAIL-05` (the settlement of each barrier claim and `barrier_scorecard`) and amends `FORE-IDN-02`/`TRG-01`/`OUT-03`; the S239 second follow-up (D10) re-words the barrier clauses for the provider-written history; the S239 follow-up amends `FORE-TRG-01`/`FORE-TRG-02` (graph-pull trigger; the deployed loop fires `forecast_barrier` only); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim); DL-203 reconciled `PARAM`; S205 proved `FORE-TYP-01`; counters are clauses proven / clauses declared |
diff --git a/docs/laws/ledger.md b/docs/laws/ledger.md
index e6d3bbe9..a91046c5 100644
--- a/docs/laws/ledger.md
+++ b/docs/laws/ledger.md
@@ -41,7 +41,7 @@ and torn down to zero. Historical Neo4j rows remain valid evidence for the pre-S
 | forecaster | ✅ v1.10 (LOCKED) | 25 / 52 | 🟨 partial — **25 of 52 clauses proven** after S252 (DL-261): `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged; v1.9 (S251, DL-260) names the four legs in `FORE-IDN-01`, one recorded node per prediction in `FORE-OBS-01` (DRIFT-081) and the three shadow scorecards in `FORE-IDM-03` (DRIFT-083), all still gray, count unchanged; v1.8 (S243, DL-247) amends and re-proves `FORE-FAIL-04`: a designed "no claim" records a `warning`, a missing or broken input an `error` (DRIFT-089), count unchanged; after S241 (DL-243) adds and proves `FORE-OUT-08` (each claim settled once by EXP-018's rule from a provider-written `MarketData`; `barrier_scorecard` over EXP-018's fixed climatology), `FORE-IDM-05` (settled once, one pass per run) and `FORE-FAIL-05` (void with a named reason, never a false outcome), and amends and re-proves `FORE-IDN-02`/`TRG-01`/`OUT-03`; v1.6 (S239, DL-241 D10) re-words `FORE-IN-07`/`TRG-01`/`OUT-07`/`IDM-04`/`FAIL-04`/`NEV-04` for the provider-written history, count unchanged; before that the S239 follow-up amends and re-proves `FORE-TRG-01`/`FORE-TRG-02` (the deployed graph-pull loop fires `forecast_barrier` only; count unchanged); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim), each proven; 27 have a gray row |
 | portfolio_manager | ✅ v1 (LOCKED, amended **v1.12**) | 33 / 51 | 🟨 partial — **33 of 51 clauses proven** after S259 (DL-276) reconciles `PARAM` only (the bounds of six rows follow the code; no clause moves) and S251 (DL-260) narrows `PM-OBS-01`/`PM-OUT-06`/`PM-STA-04` to what `PMRun` and `OrderIntentResult` carry (the `portfolio_state_snapshot` promise withdrawn, DRIFT-039; `PM-STA-04` now green), makes `PM-OBS-04` per candidate (DRIFT-065), uses the emitted reason strings in `PM-OUT-03` (DRIFT-037), names the graph-pull trigger in `PM-TRG-02` (DRIFT-086) and narrows `PM-TYP-03`'s version sentence (DRIFT-060); DRIFT-098 filed for `PM-OUT-01`/`PM-TYP-03`; before that S240 adds and proves `PM-IN-05`: a run weighs each held ticker once at its own snapshot mark (adoption mark, then cost, as fallbacks) and a resumed run reads the snapshot of the run it resumes, closing DRIFT-079; `PM-IDN-01` stays gray (current-state conjunct proven, the whole-purpose boundary proof still owed); S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders the applied weights; S211 adds and proves `PM-OBS-05`: reward-risk now compares measured target evidence against stop risk, varies across measured profiles, and rejects measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows |
 | deliberator | ✅ v1.18 (LOCKED) | 35 / 66 | S277 (DL-289 amendment 4) adds and proves DLIB-FAIL-05, refusal-only sticky switching with one model-attributed row per attempt; re-proves DLIB-FAIL-01, DLIB-OUT-02 (always-written llm_switches) and DLIB-DEP-05 (handed-over fallback construction). S276 (DL-289 amendment 1) adds and proves DLIB-DEP-05 and DLIB-NEV-11; amended DLIB-OUT-02 re-proven for the models that answered; effort defaults to empty. 🟨 partial — **35 of 66 clauses proven** after S257 (DL-274) reconciles `PARAM` only (the output cap 16,384, the peer wait up to 300 seconds; no clause moves) and S256 (DL-272) adds and proves `DLIB-IDM-04` (settle-on-take and visible reply faults), `DLIB-OBS-08` (every completion is its own row), and proves spend attribution `DLIB-OBS-02`; S255 (DL-269) adds and proves `DLIB-OUT-08`: recorded arithmetic reproduces before rendering, with first-failure withholding and old-packet parity; DRIFT-102/103 corrected; before that S254 / ADR-0032: `DLIB-NEV-10` proves prompt libraries use only the agent's own client; before that S252 (DL-261): `DLIB-TRG-01` now proven for the key-and-edge candidate bound and order-property filter, 27 / 59; before that S246 (DL-252) adds and proves `DLIB-OUT-06` (each defender and challenger turn records its guided reasoning, readings then gaps before the argument, exactly as written or why it could not be read, and an unreadable one never fails the turn or the order) and `DLIB-OUT-07` (each debated order's record carries its decision and evidence packet), and amends `DLIB-TYP-01` (`DebateTurnRecord.reasoning`, `.reasoning_error`); before that S245 (DL-251) adds and proves `DLIB-NEV-09`: every fact the challenger and judge prompts state about our code is pinned by a test that reads that code, the false calendar-day staleness fact and the stale name-correlation example are gone (DRIFT-092), and the champions rebuild byte for byte from pack-side sources; before that S222 moves its vendor adapters to `kernel/` and proves `DLIB-SEC-02` with a key-containment sentinel; S214 narrows `vetoed_tickers` to `overturn` verdicts only, routes unreadable judge answers through loud fail-open, and proves `DLIB-OUT-04`; S206 adds and proves `DLIB-NEV-08`: rendered debate-context verdicts name their enforcing check and agent, while descriptive stop-target regime evidence has no verdict; S205 rewrites and proves `DLIB-TYP-01`; S200 adds `DLIB-OBS-07` and promotes `DLIB-IDM-02`; S199 adds `DLIB-OBS-05`/`DLIB-OBS-06`; S172 proves concurrent-order record order and pending-reply handling; S194 adds `DLIB-OBS-04`; S189 added stop-reason audit evidence; S167 proves queryable fail-open causes |
-| execution | ✅ v1.15 (LOCKED) | 43 / 68 | 🟨 partial — **43 of 68 clauses proven** after S280 (DL-303) amends and proves `EXEC-OUT-07` (a partly filled ended order is a fill of its part, its rest told once) and adds and proves `EXEC-TYP-04` (`Fill.broker_filled_quantity`, read by every reader of an executed size), `EXEC-OBS-06` matching on the filled quantity; before that S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault, and the stop plan shares one lazy Fill read, no decision changes; before that S258 (DL-276) reconciles `PARAM` only (the bounds of four rows follow the code; no clause moves) and S252 (DL-261): `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66; before that S251 (DL-260) adds and proves `EXEC-IDN-04`: execution writes divergence-family `Flag`/`FlagResolution` nodes and no others, both labels now in `owns_graph` as the one declared shared pair (DRIFT-094); `EXEC-OUT-01`/`-02`/`-04`/`-05` name the contract's fields (DRIFT-061); `EXEC-TYP-03`'s version sentence (DRIFT-060); before that S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode (`warn` at first sight under a subject naming the first-sight snapshot, `critical` only if still present at the next run-start reconciliation, a new episode at `warn` whatever the ticker's history, one unresolved Flag per live divergence); S230 adds/proves `EXEC-OBS-06`: the broker stop's width comes through the shared stop-width resolver (PM lineage first, fallback only without it) and a live stop resting off its decided price is replaced in place, never cancelled and re-placed; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 added/proved `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; S204 gives every clause a row and promotes missing rows to a hard gate |
+| execution | ✅ v1.16 (LOCKED) | 45 / 70 | 🟨 partial — **45 of 70 clauses proven** after S283 (DL-306) adds and proves `EXEC-OBS-08` (no broker read is cut at a page limit; run-start reconciliation reads every order the graph waits on, by id where no listing shows it) and `EXEC-PERF-03` (a run-start broker read is bounded by the book: open orders, the recent window, the waiting Fills), with PARAM row `broker_recent_order_days`; before that S280 (DL-303) amends and proves `EXEC-OUT-07` (a partly filled ended order is a fill of its part, its rest told once) and adds and proves `EXEC-TYP-04` (`Fill.broker_filled_quantity`, read by every reader of an executed size), `EXEC-OBS-06` matching on the filled quantity; before that S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault, and the stop plan shares one lazy Fill read, no decision changes; before that S258 (DL-276) reconciles `PARAM` only (the bounds of four rows follow the code; no clause moves) and S252 (DL-261): `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66; before that S251 (DL-260) adds and proves `EXEC-IDN-04`: execution writes divergence-family `Flag`/`FlagResolution` nodes and no others, both labels now in `owns_graph` as the one declared shared pair (DRIFT-094); `EXEC-OUT-01`/`-02`/`-04`/`-05` name the contract's fields (DRIFT-061); `EXEC-TYP-03`'s version sentence (DRIFT-060); before that S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode (`warn` at first sight under a subject naming the first-sight snapshot, `critical` only if still present at the next run-start reconciliation, a new episode at `warn` whatever the ticker's history, one unresolved Flag per live divergence); S230 adds/proves `EXEC-OBS-06`: the broker stop's width comes through the shared stop-width resolver (PM lineage first, fallback only without it) and a live stop resting off its decided price is replaced in place, never cancelled and re-placed; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 added/proved `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; S204 gives every clause a row and promotes missing rows to a hard gate |
 | monitor | ✅ v1.4 (LOCKED) | 22 / 47 | 🟨 partial — **22 of 47 clauses proven** after S279 (DL-302) adds and proves `MON-PERF-03`: the end-of-run evaluation shares one lazy Fill read across the book and retains each decided width, no decision changes; before that S252 (DL-261): `MON-TRG-02` bounds both work kinds, sync from requests and their linked snapshot; DRIFT-097 corrected, 21 / 46 unchanged; S251 (DL-260) names the graph-pull triggers in `MON-TRG-02` with the key-and-edge bound for `ExecutionRun` work only (DRIFT-086; the sync poll is DRIFT-097), count unchanged; after S205 rewrites and proves `MON-TYP-01`; S204 gives every clause a row and promotes missing rows to a hard gate |
 | reporter | ✅ v1.5 (LOCKED) | 26 / 43 | 🟨 partial — **26 of 43 clauses proven** after S253 (DL-262, DL-263) rewrites `RPT-OUT-02` (the book counts are the broker's filled `Fill`s in the run's window, the outcomes cumulative since the inception; DRIFT-099), amends `RPT-IN-01` and `RPT-NEV-03` (an undefined metric is absent; DRIFT-101), and adds and proves `RPT-IDM-04` (no fill refreshed after the run is read; a re-report reproduces the book); S251 (DL-260) says `RPT-OUT-07`'s benchmark is the run's own `MarketData` by lineage, a missing one `missing benchmark` (DRIFT-087), and names the graph-pull trigger in `RPT-TRG-02` (DRIFT-086), count unchanged; v1.3 (work-queue 88, DL-224) was never reflected here and is now; after S226 adds benchmark-relative performance metrics, as-of bounded graph reads, contained performance failure, and backward-compatible `performance_metrics`; S205 rewrites `RPT-TYP-01` into required fields; S204 gives every clause a row and promotes missing rows to a hard gate |
 | researcher | ✅ v1.2 (LOCKED) | 20 / 43 | 🟨 partial — **20 of 43 clauses proven** after S205 rewrites and proves `RES-TYP-01`; 23 have a gray row |
```
