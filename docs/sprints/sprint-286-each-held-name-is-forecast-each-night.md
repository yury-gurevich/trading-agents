<!-- Agent: planning | Role: sprint handover -->
# Sprint 286 — Each held name is forecast each night, on its live stop and declared target

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-286-each-held-name-is-forecast-each-night`
**Status:** BUILT
**Version:** `0.129.00` (MINOR; local main was `0.128.08` at build)
**Effort:** M
**Decisions:** [DL-310](../design-log.md) (decided, ten decisions with the roads not taken) · work-queue 92 ([DL-240](../design-log.md) and its amendment: the daily re-read of held names feeds the exits)

> **Why this bump kind.** The forecaster gains a dimension it did not have: a claim on every name the book holds, not only on new buys. A MINOR.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/forecaster/laws/laws.md`, `agents/provider/laws/laws.md` | Two **locked constitutions** | **LOCKED. Read-only during a build**, except Appendix section 2, which you apply exactly. A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/forecaster/laws/test-plan.md`, `agents/provider/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read them to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`IN`** (FORE-IN-07), **`TRG`** (FORE-TRG-01, PROV-TRG-01/02/04), **`OUT`** (FORE-OUT-07, FORE-OUT-08, the new FORE-OUT-09 and FORE-OUT-10, PROV-OUT-08), **`IDM`** (FORE-IDM-04, FORE-IDM-05), **`FAIL`** (FORE-FAIL-04), **`PERF`** (the new FORE-PERF-04), **`NEV`** (FORE-NEV-01/02: shadow only, nothing on the decision path).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes: three new guarantees, no contract change.** The forecaster now claims on every held name (`FORE-OUT-09`), reports those claims apart (`FORE-OUT-10`) and bounds its reads (`FORE-PERF-04`); the provider's history now holds the held names. The cycle is written for you in Appendix section 2: forecaster v1.10 → v1.11 (three new clauses, `FORE-IN-07`, `FORE-TRG-01` and `FORE-FAIL-04` amended, a Changelog line), provider v1.10 → v1.11 (`PROV-TRG-01/02/04` and `PROV-OUT-08` amended, a Changelog line), the `test-plan.md` rows naming your tests, and both rollups: forecaster **25 / 52 → 28 / 55**, provider **24 / 67** unchanged. **`contracts/` is not touched** (DL-310 D8): its deploy would restart the fidelity count.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/forecaster/held_plan.py` (new) | forecaster `laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `FORE-OUT-09` (the held book, the live stop, the declared target); `FORE-NEV-01/02` (reads Position, `BrokerStopOrder`, Fill, `OrderIntent`; writes none) |
| `agents/forecaster/held_claim.py` (new), `barrier_forecast.py`, `barrier_refusal.py` | same | `FORE-IN-07` (the held request's prices), `FORE-OUT-09` (barriers from the claim's close), `FORE-FAIL-04` (designed vs malformed refusals) |
| `agents/forecaster/history_cache.py` (new), `agent.py` | same | `FORE-PERF-04` (one history read per run) |
| `agents/forecaster/barrier_store.py` | same | `FORE-OUT-07`, `FORE-OUT-09` (the held key and five properties), `FORE-IDM-04` |
| `agents/forecaster/poll.py` | same | `FORE-TRG-01` (wait while the book holds a name; one request per held name; `held_count`) |
| `agents/forecaster/settlement_pass.py`, `settlement_store.py` | same | `FORE-PERF-04` (open claims by key and edge), `FORE-IDM-05` (never settled twice), `FORE-OUT-08` |
| `agents/forecaster/barrier_scorecard.py` | same | `FORE-OUT-10`, `FORE-OUT-08` (the buys' metrics stay as they are) |
| `agents/provider/barrier_history.py` | provider `laws.md` + `test-plan.md` | `PROV-TRG-04`, `PROV-OUT-08` |
| `orchestration/packs/trading_graph_vocabulary.json` | forecaster `FORE-IDN-02`; `kernel/graph_vocabulary.py` | five new `BarrierForecast` properties, or the fleet's guard refuses the claim |
| `tests/poll_reference.py` (existing) | provider `PROV-TRG-02` | the reference finder calls the provider's `_qualifying_tickers`, whose signature gains the graph |

⚠️ **Nothing on the decision path moves.** The forecaster reads the book and writes only its own claims, settlements and markers; no file under `contracts/`, `agents/scanner/`, `agents/analyst/`, `agents/portfolio_manager/`, `agents/provider/domain/`, `agents/execution/`, `agents/monitor/` or `orchestration/packs/trading_tunables.json` changes. If your change needs one, stop and report: deploying it would restart the fidelity count EXP-014 and EXP-022 wait on.

---

## Goal

At merge, every run's barrier pass states a claim on each name the book holds as well as on each new buy: the probability that over the next 10 sessions the price reaches the stop the broker holds first, the target its buy declared first (or, once past it, the declared width again), or neither, measured from the claim's own close and settled by the same rule as a buy's claim. A held name the graph cannot give a stop or a target for is a named, designed refusal. The provider's one history request carries the held names; the forecaster reads that history once per run; the settlement pass reads only the open claims; the scorecard reports held claims apart and leaves the buys' metrics exactly as S241 reports them.

## Why (context)

Item 92: the book only exits on its stop. The exit experiment (EXP-022) that decides which exit to build waits for the fidelity PASS, four clean sessions on one unchanged decision code; `sched-2026-10-20` is session 1. DL-240's amendment names *"the same object, re-read each day for a held name"* as what decides take-profit, trim and add. On 2026-10-20, 13 of the 34 held names closed above the target their buy declared, and nothing measured what their next ten sessions look like. This sprint states that measurement nightly, as shadow evidence, without touching any decision path, so it can be deployed while the count runs; it also raises the barrier ledger from about 2 claims a night to about 36.

### Measured, 2026-10-21 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Held names after `sched-2026-10-20` | 34, all broker-adopted (`reconciled-from-broker`) | *[measured 2026-10-21]* live graph, `is_active_position_node`; `wq92_held.py` |
| Names closed above their declared target | **13 of 34**: $745 of gain up to the targets and $484 above; to their stops they would give back $1,822 | *[measured 2026-10-21]* `wq92_held_sched-2026-10-20.txt` (broker positions, stops, lineage targets) |
| The live stop from the graph alone | the newest `BrokerStopOrder` under the holding's position_ref equals the broker's open stop on **34 of 34** | *[measured 2026-10-21]* `wq92_plan_from_graph.txt` |
| The declared target from lineage | the exact lineage buy's `OrderIntent.target_pct`: **33 of 34** (UNH, the S280 partial fill, none); a buy's `OrderIntent.position_ref` is `None`, so the link is Fill → `EXECUTES` | *[measured 2026-10-21]* `wq92_held.py`, `wq92_plan_from_graph.txt` |
| A claim's cost | about 0.04 s a name after a first import of about 9 s; last night's three claim requests answered 0.1 to 0.2 s apart | *[measured 2026-10-21]* `wq92_cost.txt`; the claims' `created_at` |
| A history's size | about 36 KB of JSON a ticker: about 1.3 MB a night with 36 tickers; read once a claim, about 47 MB a night | *[measured 2026-10-21]* `wq92_cost.txt` |
| The graph's size | 123 MB, `MarketData` 47 MB of it (about 500 KB a night) | *[measured 2026-10-21]* `pg_database_size`, `pg_column_size` by label |
| The extreme-move guard on a barrier fetch | cannot fire below 66 tickers (√(n−1) against 8σ); buys and held names together were 36 | *[measured 2026-10-21]* `agents/provider/domain/integrity.py`, `max_daily_move_sigma` 8.0 |
| F1 on the prototype | 34 held requests, 32 held claims, 2 designed refusals (PM: the fit failed; UNH: no declared target), 3 buy claims; byte for byte the same on a second run, digest `9d5791f9a903ba29` | *[measured 2026-10-21]* kit `s286_f1.py` on `book_sched-2026-10-20.json` → `f1_proto.txt` |
| Whether a held claim has skill | *[ASSUMED — not measured]* unknown until held claims settle (ten sessions after the first one); the scorecard reports them apart so they cannot blur the buys' measured skill (+5.69 %) | the F2 and the scorecard after 2026-11-04 |

---

## Scope — and what is deliberately NOT here

1. **The held book's plan** (`held_plan.py`, Appendix section 1): one request per held name, carrying its live stop (dollars), and its declared target and width when its lineage declares them.
2. **The held claim** (`held_claim.py`, `barrier_forecast.py`, `barrier_refusal.py`, `barrier_store.py`): barriers from the claim's own close, `declared` or `rebased`; designed refusals for a missing stop, a missing target, a close at or below the stop; the held key and five properties.
3. **The trigger** (`poll.py`): a run waits for its history while the book holds a name; the deployed loop requests each held name's claim after the buys'; `ForecasterRun.held_count`.
4. **The provider's history** (`agents/provider/barrier_history.py`): the barrier buys, then each held name, once each, in one request; a run with no buy gets one while the book holds a name.
5. **Bounded reads** (`history_cache.py`, `agent.py`, `settlement_pass.py`, `settlement_store.py`): one history read per run; the pass finds open claims by key and edge; a settlement without its edge is linked, not redone.
6. **The scorecard** (`barrier_scorecard.py`): the buys' metrics unchanged; held claims under `held_` once one exists.
7. **The vocabulary pack**: five `BarrierForecast` properties.
8. **The law cycle and one existing-test edit** (Appendix section 2), exactly.

### Out of scope (do NOT build this sprint)

- **Any exit.** No sell, trim, take-profit or time exit: EXP-022 decides those, and each is a decision-path change.
- **Anything the PM, the analyst or the deliberators read.** The held claims are shadow evidence (`FORE-NEV-01/02`); nothing consumes them this sprint.
- **A public `decided_target_pct` in `contracts/`.** The lineage rule is imported (DL-310 D8).
- **A retention rule for `BarrierHistory`**, and a climatology of their own for held claims (named in DL-310).
- **No `laws.md` edit** beyond Appendix section 2. **No ADR reversal.**

### The road not taken (LAW-06)

- **A live take-profit now.** Rejected (the operator chose this sprint): a decision-path deploy restarts the fidelity count, and EXP-022 decides which exit comes first.
- **The run's broker snapshot as the held set.** Rejected: its holdings carry no position_ref, and the active Positions are what the analyst scored and what execution's stops are keyed on.
- **The declared target alone, refusing names past it.** Rejected: 13 of 34 refused, the names whose exit matters most.
- **Every target re-based from the close.** Rejected: loses the declared target for the 21 names below it, the level EXP-022's take-profit arm sells at.
- **One `BarrierHistory` per ticker.** Rejected: a `contracts/` change (its key and type).
- **One pooled scorecard.** Rejected: it would change S241's measured skill by mixing held claims in under the buys' names.

---

## The design decisions this sprint has to make

**None are left to make: DL-310 records D1 to D10 with the rejected alternatives, on `main`.** Do not add a design-log entry. If a decision there does not survive contact with the code, stop and report.

---

## Blast radius — measured 2026-10-21

| What | Detail |
| --- | --- |
| Files changed | Production (Appendix section 1, 13 files): new `agents/forecaster/held_plan.py` **105**, `held_claim.py` **89**, `history_cache.py` **38**; `barrier_forecast.py` 160 → **176**, `barrier_refusal.py` 83 → **88**, `barrier_store.py` 92 → **110**, `agent.py` 166 → **169**, `poll.py` 154 → **172**, `settlement_pass.py` 138 → **144**, `settlement_store.py` 93 → **100**, `barrier_scorecard.py` 66 → **85**; `agents/provider/barrier_history.py` 179 → **183**; `orchestration/packs/trading_graph_vocabulary.json` (+5 properties). Law and rollups (section 2): the two `laws.md` and `test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`. One existing test file: `tests/poll_reference.py`. Your tests: seven files (Test plan) |
| Agents affected | forecaster, provider. Neither imports the other; both import `contracts.positions` (and the forecaster `contracts.broker_stops`, `contracts.position_refs`, `contracts.stop_width`), unchanged |
| Contract change? | **No.** `ForecastRequest.subject_kind` already allows `"position"` |
| Graph vocabulary change? | **Yes: five properties on `BarrierForecast`** (`declared_target_pct`, `stop_price`, `subject_kind`, `target_basis`, `target_price`). No new label or edge |
| New env keys / tunables | none |
| Deploy implication | **`deploy-agents.ps1 -Action vocabulary` first** (the master injects the pack into every app; an older image reads the larger vocabulary as before), **then an image-only retag**. No fidelity decision path (`scripts/replay_fidelity_git.py`'s `DECISION_PATHS`): the count holds |
| Rollback | Retag to `s285`. A retag does not undo: the held claims and settlements already written (append-only, shadow; nothing reads them but the scorecard), the five vocabulary properties (harmless to `s285`), the larger `BarrierHistory` nodes (about 1.3 MB a night) |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **No design-log entry**: DL-310 is decided.
3. **Write the tests A1 to A17 under the exact names in the Test plan** and run them on the unchanged tree: every one fails or errors (the new modules do not exist; the claim, poll, settlement and scorecard behave as before). Paste the output.
4. **Apply Appendix section 1 exactly.**
5. **Apply Appendix section 2 exactly** (law cycle, rollups, `tests/poll_reference.py`).
6. **Plant the breaks B1 to B25** one at a time against your tests alone; each turns at least one red; restore each.
7. **Bump MINOR, `uv lock --offline`, `make ci` redirected to a file.**
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Each docstring cites the clauses in the last column. The names are fixed: the test-plan rows in Appendix section 2 cite them. Paths: `agents/forecaster/tests/` unless the row names `agents/provider/tests/`.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 `test_held_plan.py::test_a_held_name_carries_its_live_stop_and_declared_target` | an adopted COP 8 @ $124.41 with its lineage buy (Fill → `EXECUTES` → `OrderIntent.target_pct` 0.0495660894245197) and a stop of 11708 cents under its position_ref | `held_requests` = `(("COP", {"stop_price": 117.08, "target_price": round(124.41 × 1.0495660894245197, 4), "target_pct": 0.0495660894245197}),)` (`FORE-OUT-09`) |
| A2 | `…plan.py::test_a_pm_lineage_position_declares_its_own_target` | a Position with no provenance, `target_pct` 0.1, entry 8692 cents, stop 8257 | `("KO", {"stop_price": 82.57, "target_price": 95.612, "target_pct": 0.1})` (`FORE-OUT-09`) |
| A3 | `…plan.py::test_a_target_the_lineage_does_not_declare_is_left_out` | COP adopted with no lineage buy; UNH whose buy declared no target; MO in two lots (the first with a lineage buy); META `broker_absent` | requests for COP, MO, UNH only; COP and UNH carry only `stop_price`; MO carries nothing (`FORE-OUT-09`, `FORE-FAIL-04`) |
| A4 | `…plan.py::test_the_newest_live_placement_is_the_stop` | COP: a 11000-cent stop `replaced_at`, then `#1` at 11708 placed later; KO: its only stop `cancelled_at` | COP's `stop_price` 117.08; KO's request has no `stop_price` (`FORE-OUT-09`) |
| A5 | 🎯 `test_held_poll.py::test_every_held_name_gets_a_claim_request_beside_the_buys` | the deployed run (AAPL, GOOG buys; NVDA sell) and the held COP | requests `recommendation` AAPL, GOOG, then `position` COP with `stop_price` 117.08 and the run's history key; `ForecasterRun.held_count` 1 (`FORE-TRG-01`, `FORE-OUT-09`) |
| A6 | `…poll.py::test_a_run_waits_for_its_bars_while_the_book_holds_a_name` | a run with an empty recommendation set | found while nothing is held; not found once COP is held; found again once its `BarrierHistory` exists (`FORE-TRG-01`) |
| A7 | 🎯 `test_held_claim.py::test_a_held_claim_measures_its_barriers_from_its_close` | 760 COP bars; a `position` request with stop 0.8 × close, target 1.03 × close, width 0.05; the store wrapped in the pack's vocabulary guard | the claim `barrier-garch-v1:held:COP:{as_of}`: `stop_pct` ≈ 0.2, `target_pct` ≈ 0.03, `subject_kind` `position`, `target_basis` `declared`, `stop_price`, `declared_target_pct` 0.05, `entry_close` = the last close (`FORE-OUT-09`, `FORE-IN-07`) |
| A8 | `…claim.py::test_past_its_target_a_held_claim_asks_for_the_width_again` | stop 0.9 × close, target 0.97 × close | `target_pct` 0.05, `target_basis` `rebased`, `stop_pct` ≈ 0.1 (`FORE-OUT-09`) |
| A9 | `…claim.py::test_what_a_held_claim_cannot_stand_on_is_refused` (6 cases) | no stop; no target; stop = close; width 0; a negative stop price; target 2.5 × close | no claim and one fault each: `warning` "no live stop", `warning` "no declared target", `warning` "at or below the live stop", `error` "must be positive" twice, `error` "outside (0, 1]" (`FORE-FAIL-04`) |
| A10 | `…claim.py::test_a_buy_and_a_held_claim_on_one_bar_both_stand` | a buy request and a held request for COP on one history | two claims, `…:COP:{as_of}` and `…:held:COP:{as_of}`; no fault (`FORE-IDM-04`) |
| A11 | 🎯 `test_held_reads.py::test_a_runs_claims_read_its_history_once` | a history of three tickers; a graph counting reads by label; three claim requests | one `BarrierHistory` read; three claims; no fault (`FORE-PERF-04`) |
| A12 | `…reads.py::test_a_history_the_provider_writes_later_is_read_when_it_lands` | a `HistoryCache`; a key with no node, then the node written | `None`, then the history (`FORE-PERF-04`) |
| A13 | 🎯 `…reads.py::test_a_pass_lists_no_claim_and_settles_the_open_ones` | a buy claim on AAPL and a held claim on KO, both reaching the target; the counting graph | zero listings of `BarrierForecast` and `BarrierSettlement`; both settled `target` (`FORE-PERF-04`, `FORE-OUT-08`) |
| A14 | `…reads.py::test_a_settlement_written_without_its_edge_is_linked_not_redone` | a claim whose `BarrierSettlement` (outcome `stop`) exists with no `SETTLED_BY` edge; a run whose bars reach the target | the settlement still `stop`; no open claim left; the pass marker `settled` 0 (`FORE-IDM-05`) |
| A15 | 🎯 `test_held_scorecard.py::test_held_claims_are_scored_apart_and_the_buys_scores_stand` | S241's ledger fixture, then three held claims (two settled, one open) | the non-`held_` metrics and `sample_size` equal the buys-only ledger's; no `held_` name without held claims; `held_settled` 2, `held_open` 1, `held_realised_target` 0.5, `held_skill` present (`FORE-OUT-10`) |
| A16 | 🎯 `agents/provider/tests/test_barrier_history_held.py::test_the_history_holds_the_buys_then_each_held_name_once` | AAPL and KO buys, an XOM hold; KO and COP held; META `broker_absent` | one fetch for `("AAPL", "KO", "COP")`; `requested` in that order (`PROV-TRG-04`, `PROV-OUT-08`) |
| A17 | `…history_held.py::test_a_run_with_no_buy_gets_a_history_while_the_book_holds_a_name` | a hold-and-sell run, a run with no recommendation set | nothing pending while nothing is held; the first run pending once COP is held, the bare run never (`PROV-TRG-04`) |

On the unchanged tree every one fails or errors. After Appendix section 1 all seventeen pass, and the existing suites pass unchanged except `tests/test_poll_same_work.py`, which needs section 2's `tests/poll_reference.py`.

---

## Success factors

- [ ] On the built tree, F1 (`s286_f1.py` on the frozen book, run from the main checkout with `PYTHONPATH=<built tree>`) prints exactly the prototype's output (`f1_proto.txt`, digest `9d5791f9a903ba29`): 34 held requests, 32 held claims, 2 designed refusals, 3 buy claims. *(Planner, at review.)*
- [x] No file under `contracts/`, `kernel/` or a decision path changes; no existing test changes but `tests/poll_reference.py`.
- [x] Design decisions recorded with rejected alternatives: DL-310, already on `main`.
- [x] Law cycle done as Appendix section 2: `FORE-OUT-09`, `FORE-OUT-10`, `FORE-PERF-04` 🟩; forecaster 28 / 55 and provider 24 / 67 in both rollups.
- [x] B1 to B25 each planted, watched to fail against your tests alone, restored — stated per break.
- [x] Every touched module < 200 lines, test files included.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The poll sends prices; the claim converts them.** A held request carries `stop_price` and `target_price` in dollars, never fractions: only the claim knows its own last close, the close its settlement measures from (`FORE-OUT-08`). A fraction computed in the poll from another close would settle against barriers the claim never stated.
🪤 **Past its target, the width again, not a refusal.** 13 of 34 names on 2026-10-20 were past their target; refusing them refuses the names whose exit matters most.
🪤 **A held claim's key has its own segment.** Without `held:` a buy and a held claim on one bar collide, and `FORE-IDM-04` refuses the second.
🪤 **The scorecard's buys stay byte for byte.** Pooling would change S241's measured skill; `held_` names appear only once a held claim exists (the existing empty-ledger test pins that).
🪤 **The settlement pass must not list.** `keys_without_edge` answers by key and edge; a `list_nodes("BarrierForecast")` anywhere in the pass is the defect A13 catches. A settlement written without its edge must be linked, or the claim faults every night (A14).
🪤 **Never cache a missing history.** The provider writes the node after the forecaster may first look (A12).
🪤 **The vocabulary pack is part of the deploy**: without its five properties the fleet's guard refuses every held claim. A7 writes through the guard.
🪤 **`_equals_holding` is imported from `contracts/stop_width.py`, private on purpose** (DL-310 D8). Do not copy it and do not make it public: either changes `contracts/` or forks the rule DL-222/223 made one.
🪤 **Sizes.** `barrier_forecast.py` 176, `poll.py` 172, `provider/barrier_history.py` 183 after section 1: do not grow them; keep each new test file under 200 after `ruff format`.
🪤 **Write files with an editor, not a shell heredoc** (Git Bash's heredoc has eaten backslashes before).

**The breaks** (plant one at a time in production code, run your A1 to A17 alone, expect red, restore):

| # | Break | # | Break |
| --- | --- | --- | --- |
| B1 | `held_plan._ENDED = ()` | B14 | `poll._history_ready` ignores the held book |
| B2 | `_live_stops` keeps the oldest placement | B15 | the held requests go as `recommendation` |
| B3 | `_declared_target_pct` drops its one-lot check | B16 | `HistoryCache.read` always reads the graph |
| B4 | an adopted holding reads its own `target_pct` | B17 | `HistoryCache.read` holds a missing key |
| B5 | `target_price` = entry × width (no 1 +) | B18 | the pass lists every claim again |
| B6 | `rebased` measures `target_price / close − 1` | B19 | the pass skips `relink_settlement` |
| B7 | the stop refusal reads `close < stop_price` | B20 | the scorecard pools held claims with buys |
| B8 | "no declared target" is an error | B21 | the scorecard reports `held_` with no held claim |
| B9 | `stop_pct` = `stop_price / close` | B22 | the provider adds no held name |
| B10 | the held key loses its `held:` segment | B23 | the provider puts held names before buys |
| B11 | the held claim writes no `subject_kind` | B24 | the provider's finder ignores the held book |
| B12 | `barrier_forecast` never sees a held subject | B25 | `target_basis` removed from the vocabulary pack |
| B13 | the poll sends no held request | | |

The kit's `s286_breaks.py` holds each break as an exact replacement.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes after the Appendix: `barrier_forecast.py` **176**, `poll.py` **172**, `agent.py` **169**, `settlement_pass.py` **144**, `agents/provider/barrier_history.py` **183**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. No tunable is added: the key segment, the ended markers and the subject name are names, not values.
- Faults, not silent failure — `kernel.fault_boundary` (the claim's existing boundary covers every held refusal).
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- Version bump MINOR, `uv.lock` staged with it.
- Secrets never through the worktree — your worktree has **no `.env`**, and nothing in this sprint needs one. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the branch's worktree; check the printed SHA against `git rev-parse HEAD`.
2. Planner's review: CodeQL set-diff against the baseline branch first; the blobs against `prototype_blobs.txt` (kit); the planner's tests on the built tree; B1 to B25 against Codex's tests alone; F1 (equals `f1_proto.txt` byte for byte).
3. Merge to `main` locally and push; tag `v<version>`; post-merge CodeQL.
4. **Deploy, on the operator's word: `pwsh infra/deploy-agents.ps1 -Action vocabulary` (17 `[OK]`, each app's decoded pack = the repo's), then an image-only retag.** The fidelity count holds (no decision path); record the rollback tag `s285`. F2 on the first weekday night after: 8 / 8; the run's `BarrierHistory` requests the buys and then every held name; a held claim (`…:held:…`) for each held name with a live stop and a declared target and a named designed refusal for each without; no `error` fault from the forecaster; no `VocabularyError`; the `BarrierSettlementPass` written. Ten sessions later, the first held claims settle; then read `barrier_scorecard`'s `held_` metrics.

---

## Handover — paste this to Codex

```text
You are building Sprint 286 in the worktree ../ta-s286, on the branch
sprint-286-each-held-name-is-forecast-each-night. Never work on main. The worktree and its venv
are ready; never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-286-each-held-name-is-forecast-each-night.md, whole, before anything
else. It is the spec, and its bottom sections are your handback. The Appendix holds the
production code, the law text and one existing-test edit, which you apply exactly. Your work is
the tests A1 to A17, the breaks, the bump and the evidence.

In order:
1. Read agents/forecaster/laws/laws.md and test-plan.md, agents/provider/laws/laws.md and
   test-plan.md, docs/laws/conventions.md and docs/laws/drift-register.md, whole. Fill the Law
   reading record in the spec BEFORE any code.
2. Write the tests A1 to A17 under the exact file paths and names in the Test plan (six forecaster
   test files under agents/forecaster/tests/, one provider file under agents/provider/tests/; a
   helper module of your own is fine), each docstring citing the clauses in its row. Run them on
   the unchanged tree and paste the output into the Closeout: every one fails or errors.
3. Apply Appendix section 1 exactly (13 files: 12 Python modules, 3 of them new, and the graph
   vocabulary pack). Change nothing else in production code.
4. Apply Appendix section 2 exactly (the two agents' laws.md and test-plan.md,
   docs/laws/ledger.md, docs/laws/INDEX.md and tests/poll_reference.py). Change no other existing
   test. The test-plan rows name your tests; if a name differs, your name is wrong.
5. Plant the breaks B1 to B25 (Traps) one at a time; each must turn at least one of your A1 to A17
   (with agents/forecaster/tests/test_barrier_scorecard.py, which pins the empty ledger) red;
   restore each before the next. Record each in the Closeout.
6. Bump the version MINOR to the next number after main's in pyproject.toml, run
   uv lock --offline, stage uv.lock. Run make ci redirected to a file and read the file. If the
   dependency audit is the only step that fails for want of network, say so; the planner runs it.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: reach the network or any live service; run infra/ scripts, pwsh or any az command; change
contracts/, kernel/, agents/scanner, agents/analyst, agents/portfolio_manager, agents/execution,
agents/monitor, agents/provider/domain, orchestration/packs/trading_tunables.json or any
Dockerfile; copy or make public contracts/stop_width.py's _equals_holding (import it as the
Appendix does); add or reword a law clause beyond section 2; add a design-log entry; use noqa;
let any module, test files included, reach 200 lines; measure make ci through a pipe; write files
with a shell heredoc.

Traps (the spec's Traps section has them all): the poll sends prices and the claim converts them on
its own close; past its target a held name gets the declared width again, not a refusal; the held
key has its own segment; the scorecard's buy metrics stay byte for byte and held_ names appear only
once a held claim exists; the settlement pass must not list; never cache a missing history; the
vocabulary pack's five properties are part of the change.

Two tiers when something does not fit. A wrong command, count, path or line number whose intent is
plain: correct it, record it in Return notes, and carry on. A law that contradicts the spec, an
existing test failing outside section 2's files, or a measurement in the spec that does not
reproduce: STOP and report. State anything not done as "not done" or "verified failing". Never
write a Result for work you have not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output: the step lines and their verdicts, not the whole `make ci` log.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Held plan, held claims, storage and vocabulary | `agents/forecaster/laws/laws.md` v1.10 and `test-plan.md`, whole; `docs/laws/conventions.md`, whole | `FORE-IN-07`, `FORE-OUT-07/08`, `FORE-IDM-04`, `FORE-FAIL-04`, `FORE-NEV-01/02`, `FORE-IDN-02`; Appendix's new `FORE-OUT-09` | Yes: send prices, convert on the claim's close, import the existing private lineage rule, and guard the write with the vocabulary pack. |
| Poll, history cache, settlement and scorecard | Same forecaster files, whole; `docs/laws/drift-register.md`, whole | `FORE-TRG-01`, `FORE-IDM-05`, `FORE-OUT-08`, `FORE-NEV-01/02`; Appendix's new `FORE-OUT-10`, `FORE-PERF-04` | Yes: preserve buy metrics, never cache a missing history, and find open claims by key and edge. |
| Provider history and reference finder | `agents/provider/laws/laws.md` v1.10 and `test-plan.md`, whole; both umbrella files above, whole | `PROV-TRG-01/02/04`, `PROV-OUT-08` | Yes: one ordered, deduplicated request; no recommendation set still triggers nothing. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes: three new forecaster guarantees, with no contract change. Apply only Appendix section 2's v1.11 amendments and rollups after the red run and section 1. The new clauses are not yet proven. Existing relied-on clauses are green; `FORE-IDN-01`, `FORE-STA-01`, `FORE-IDM-03`, `FORE-OBS-01`, existing performance clauses and CAP remain gray, and this sprint claims no proof of their whole statements. Provider dependency rows remain structural; no live dependency proof is attempted.

**Contradictions found between a law and this spec:** None found beyond the explicit amendments supplied by section 2. Read `CLAUDE.md`, repository indexes and DL-310 D1-D10 before code. Scope: Appendix only, new tests, MINOR/lock and handback. Initial tree clean, branch `sprint-286-each-held-name-is-forecast-each-night`, HEAD/main/origin-main `dd3abd8b49564963aa26f8a76f0884380c8dd1da`; `.env` absent. No network, live services, deployment, main edits or tracker edits authorized.

**Laws found silent where a decision was needed:** Held claims, separate held scores and bounded reads are the already-decided silences resolved by DL-310 and Appendix section 2. No additional decision was needed; no additional drift row or law amendment is made.

**Clauses that were ⬜ and are now proven:** At the pre-code record none were proven. After the unchanged-tree red run and exact Appendix application, `FORE-OUT-09`, `FORE-OUT-10` and `FORE-PERF-04` have passing functional tests A1-A15. No existing gray clause is promoted beyond Appendix section 2.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a_held_name_carries_its_live_stop_and_declared_target` | `agents/forecaster/tests/test_held_plan.py` | PASS | `FORE-OUT-09` |
| A2 | `test_a_pm_lineage_position_declares_its_own_target` | `agents/forecaster/tests/test_held_plan.py` | PASS | `FORE-OUT-09` |
| A3 | `test_a_target_the_lineage_does_not_declare_is_left_out` | `agents/forecaster/tests/test_held_plan.py` | PASS | `FORE-OUT-09`, `FORE-FAIL-04` |
| A4 | `test_the_newest_live_placement_is_the_stop` | `agents/forecaster/tests/test_held_plan.py` | PASS | `FORE-OUT-09` |
| A5 | `test_every_held_name_gets_a_claim_request_beside_the_buys` | `agents/forecaster/tests/test_held_poll.py` | PASS | `FORE-TRG-01`, `FORE-OUT-09` |
| A6 | `test_a_run_waits_for_its_bars_while_the_book_holds_a_name` | `agents/forecaster/tests/test_held_poll.py` | PASS | `FORE-TRG-01` |
| A7 | `test_a_held_claim_measures_its_barriers_from_its_close` | `agents/forecaster/tests/test_held_claim.py` | PASS | `FORE-OUT-09`, `FORE-IN-07` |
| A8 | `test_past_its_target_a_held_claim_asks_for_the_width_again` | `agents/forecaster/tests/test_held_claim.py` | PASS | `FORE-OUT-09` |
| A9 | `test_what_a_held_claim_cannot_stand_on_is_refused` (six cases) | `agents/forecaster/tests/test_held_claim.py` | PASS, 6/6 | `FORE-FAIL-04` |
| A10 | `test_a_buy_and_a_held_claim_on_one_bar_both_stand` | `agents/forecaster/tests/test_held_claim.py` | PASS | `FORE-IDM-04` |
| A11 | `test_a_runs_claims_read_its_history_once` | `agents/forecaster/tests/test_held_reads.py` | PASS | `FORE-PERF-04` |
| A12 | `test_a_history_the_provider_writes_later_is_read_when_it_lands` | `agents/forecaster/tests/test_held_reads.py` | PASS | `FORE-PERF-04` |
| A13 | `test_a_pass_lists_no_claim_and_settles_the_open_ones` | `agents/forecaster/tests/test_held_reads.py` | PASS | `FORE-PERF-04`, `FORE-OUT-08` |
| A14 | `test_a_settlement_written_without_its_edge_is_linked_not_redone` | `agents/forecaster/tests/test_held_reads.py` | PASS | `FORE-IDM-05` |
| A15 | `test_held_claims_are_scored_apart_and_the_buys_scores_stand` | `agents/forecaster/tests/test_held_scorecard.py` | PASS | `FORE-OUT-10` |
| A16 | `test_the_history_holds_the_buys_then_each_held_name_once` | `agents/provider/tests/test_barrier_history_held.py` | PASS | `PROV-TRG-04`, `PROV-OUT-08` |
| A17 | `test_a_run_with_no_buy_gets_a_history_while_the_book_holds_a_name` | `agents/provider/tests/test_barrier_history_held.py` | PASS | `PROV-TRG-04` |

**Tests added beyond the plan:** No additional test names. A3 also checks boolean, text, zero and negative lineage targets. A1 checks the empty book; A4 also checks an older placement read after the newest one; A12 also checks that an already-read history is reused. `held_helpers.py` supplies synthetic fixtures and graph read counters. The existing `test_barrier_scorecard.py` is run unchanged alongside the sprint tests.

---

## Closeout — evidence

**Status:** BUILT — local source and test proof complete; overall CI is verified failing at the offline dependency audit.

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s286`, branch `sprint-286-each-held-name-is-forecast-each-night`; `.env` absent. Ready `.venv/Scripts/python.exe`; no sync, network or live-service proof.

**Result:** Applied both Appendix sections exactly (20/20 blobs), wrote all A1-A17 (22 cases), proved each red before implementation and green afterward, and proved B1-B25 red/restored against the final tests. Full pytest: 5,264 passed, 9 skipped, 100.00% coverage. Version `0.129.00` and offline lock update complete. `make ci` exited 2 only at the dependency audit's unavailable PyPI lookup; fresh audit, remote and live proof are not done.

**Files changed:** 31 paths: Appendix section 1's 13 production/vocabulary paths; section 2's seven law/rollup/reference-test paths; the six fixed test files in the results table and `agents/forecaster/tests/held_helpers.py`; `pyproject.toml`, `uv.lock`, this handover and `docs/sprints/README.md`. No other production or existing-test file changed. No protected path or tracker changed.

**Design decisions:** recorded as [`DL-310`](../design-log.md) — ten decisions, the rejected alternatives under *Ruled out*.

**Proof — the red run first:**

```text
Tree: C:/Users/yury_/Downloads/project/ta-s286
Command: .venv/Scripts/python.exe -m pytest --no-cov -vv
  agents/forecaster/tests/test_held_plan.py
  agents/forecaster/tests/test_held_poll.py
  agents/forecaster/tests/test_held_claim.py
  agents/forecaster/tests/test_held_reads.py
  agents/forecaster/tests/test_held_scorecard.py
  agents/provider/tests/test_barrier_history_held.py
Production and existing tests unchanged; RED_EXIT=1.
agents/forecaster/tests/test_held_plan.py::test_a_held_name_carries_its_live_stop_and_declared_target FAILED [  4%]
agents/forecaster/tests/test_held_plan.py::test_a_pm_lineage_position_declares_its_own_target FAILED [  9%]
agents/forecaster/tests/test_held_plan.py::test_a_target_the_lineage_does_not_declare_is_left_out FAILED [ 13%]
agents/forecaster/tests/test_held_plan.py::test_the_newest_live_placement_is_the_stop FAILED [ 18%]
agents/forecaster/tests/test_held_poll.py::test_every_held_name_gets_a_claim_request_beside_the_buys FAILED [ 22%]
agents/forecaster/tests/test_held_poll.py::test_a_run_waits_for_its_bars_while_the_book_holds_a_name FAILED [ 27%]
agents/forecaster/tests/test_held_claim.py::test_a_held_claim_measures_its_barriers_from_its_close FAILED [ 31%]
agents/forecaster/tests/test_held_claim.py::test_past_its_target_a_held_claim_asks_for_the_width_again FAILED [ 36%]
agents/forecaster/tests/test_held_claim.py::test_what_a_held_claim_cannot_stand_on_is_refused[no-stop] FAILED [ 40%]
agents/forecaster/tests/test_held_claim.py::test_what_a_held_claim_cannot_stand_on_is_refused[no-target] FAILED [ 45%]
agents/forecaster/tests/test_held_claim.py::test_what_a_held_claim_cannot_stand_on_is_refused[at-stop] FAILED [ 50%]
agents/forecaster/tests/test_held_claim.py::test_what_a_held_claim_cannot_stand_on_is_refused[zero-width] FAILED [ 54%]
agents/forecaster/tests/test_held_claim.py::test_what_a_held_claim_cannot_stand_on_is_refused[negative-stop] FAILED [ 59%]
agents/forecaster/tests/test_held_claim.py::test_what_a_held_claim_cannot_stand_on_is_refused[wide-target] FAILED [ 63%]
agents/forecaster/tests/test_held_claim.py::test_a_buy_and_a_held_claim_on_one_bar_both_stand FAILED [ 68%]
agents/forecaster/tests/test_held_reads.py::test_a_runs_claims_read_its_history_once FAILED [ 72%]
agents/forecaster/tests/test_held_reads.py::test_a_history_the_provider_writes_later_is_read_when_it_lands FAILED [ 77%]
agents/forecaster/tests/test_held_reads.py::test_a_pass_lists_no_claim_and_settles_the_open_ones FAILED [ 81%]
agents/forecaster/tests/test_held_reads.py::test_a_settlement_written_without_its_edge_is_linked_not_redone FAILED [ 86%]
agents/forecaster/tests/test_held_scorecard.py::test_held_claims_are_scored_apart_and_the_buys_scores_stand FAILED [ 90%]
agents/provider/tests/test_barrier_history_held.py::test_the_history_holds_the_buys_then_each_held_name_once FAILED [ 95%]
agents/provider/tests/test_barrier_history_held.py::test_a_run_with_no_buy_gets_a_history_while_the_book_holds_a_name FAILED [100%]
============================= 22 failed in 2.51s ==============================
Full failure trace: ../s286-evidence/red.txt. Every A1-A17 failed: five absent-module
failures; assertions pin missing held requests, wrong refusal severities/reasons,
three history reads, claim listings, an unlinked settlement, pooled scores and
missing held histories. No existing test was run or edited in this red proof.
```

**Proof — the green run:**

```text
Command: .venv/Scripts/python.exe -m pytest --no-cov -v
  agents/forecaster/tests/test_held_plan.py
  agents/forecaster/tests/test_held_poll.py
  agents/forecaster/tests/test_held_claim.py
  agents/forecaster/tests/test_held_reads.py
  agents/forecaster/tests/test_held_scorecard.py
  agents/provider/tests/test_barrier_history_held.py
  agents/forecaster/tests/test_barrier_scorecard.py
GREEN_EXIT=0
collecting ... collected 26 items
============================= 26 passed in 2.18s ==============================
APPENDIX_BLOBS=20/20
```

**Guards planted:** All B1-B25 planted separately against A1-A17 plus the unchanged `test_barrier_scorecard.py`; every child exited 1 with a named failing test. Restored original bytes after each child, including failure cleanup. The runner asserted all original files were restored after B25.

```text
B1 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.27s
B2 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.26s
B3 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.31s
B4 EXIT=1 RESTORED=True 3 failed, 23 passed in 2.28s
B5 EXIT=1 RESTORED=True 2 failed, 24 passed in 2.33s
B6 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.26s
B7 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.28s
B8 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.24s
B9 EXIT=1 RESTORED=True 2 failed, 24 passed in 2.24s
B10 EXIT=1 RESTORED=True 2 failed, 24 passed in 2.32s
B11 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.27s
B12 EXIT=1 RESTORED=True 9 failed, 17 passed in 2.30s
B13 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.23s
B14 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.26s
B15 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.30s
B16 EXIT=1 RESTORED=True 2 failed, 24 passed in 2.28s
B17 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.24s
B18 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.30s
B19 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.27s
B20 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.46s
B21 EXIT=1 RESTORED=True 3 failed, 23 passed in 2.26s
B22 EXIT=1 RESTORED=True 2 failed, 24 passed in 2.27s
B23 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.30s
B24 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.22s
B25 EXIT=1 RESTORED=True 1 failed, 25 passed in 2.26s
BREAKS_PROVEN=25/25; ALL_ORIGINAL_BYTES_RESTORED
```

| Break | At least one test observed red |
| --- | --- |
| B1 | `test_the_newest_live_placement_is_the_stop` |
| B2 | `test_the_newest_live_placement_is_the_stop` |
| B3 | `test_a_target_the_lineage_does_not_declare_is_left_out` |
| B4 | `test_a_held_name_carries_its_live_stop_and_declared_target`, `test_a_target_the_lineage_does_not_declare_is_left_out`, `test_the_newest_live_placement_is_the_stop` |
| B5 | `test_a_held_name_carries_its_live_stop_and_declared_target`, `test_a_pm_lineage_position_declares_its_own_target` |
| B6 | `test_past_its_target_a_held_claim_asks_for_the_width_again` |
| B7 | `test_what_a_held_claim_cannot_stand_on_is_refused[at-stop]` |
| B8 | `test_what_a_held_claim_cannot_stand_on_is_refused[no-target]` |
| B9 | `test_a_held_claim_measures_its_barriers_from_its_close`, `test_past_its_target_a_held_claim_asks_for_the_width_again` |
| B10 | `test_a_held_claim_measures_its_barriers_from_its_close`, `test_a_buy_and_a_held_claim_on_one_bar_both_stand` |
| B11 | `test_a_held_claim_measures_its_barriers_from_its_close` |
| B12 | `test_a_held_claim_measures_its_barriers_from_its_close`, `test_past_its_target_a_held_claim_asks_for_the_width_again`, `test_what_a_held_claim_cannot_stand_on_is_refused[no-stop]`, `test_what_a_held_claim_cannot_stand_on_is_refused[no-target]`, `test_what_a_held_claim_cannot_stand_on_is_refused[at-stop]`, `test_what_a_held_claim_cannot_stand_on_is_refused[zero-width]`, `test_what_a_held_claim_cannot_stand_on_is_refused[negative-stop]`, `test_what_a_held_claim_cannot_stand_on_is_refused[wide-target]`, `test_a_buy_and_a_held_claim_on_one_bar_both_stand` |
| B13 | `test_every_held_name_gets_a_claim_request_beside_the_buys` |
| B14 | `test_a_run_waits_for_its_bars_while_the_book_holds_a_name` |
| B15 | `test_every_held_name_gets_a_claim_request_beside_the_buys` |
| B16 | `test_a_runs_claims_read_its_history_once`, `test_a_history_the_provider_writes_later_is_read_when_it_lands` |
| B17 | `test_a_history_the_provider_writes_later_is_read_when_it_lands` |
| B18 | `test_a_pass_lists_no_claim_and_settles_the_open_ones` |
| B19 | `test_a_settlement_written_without_its_edge_is_linked_not_redone` |
| B20 | `test_held_claims_are_scored_apart_and_the_buys_scores_stand` |
| B21 | `test_held_claims_are_scored_apart_and_the_buys_scores_stand`, `test_an_empty_ledger_reports_counts_and_no_scores`, `test_another_models_ledger_is_its_own` |
| B22 | `test_the_history_holds_the_buys_then_each_held_name_once`, `test_a_run_with_no_buy_gets_a_history_while_the_book_holds_a_name` |
| B23 | `test_the_history_holds_the_buys_then_each_held_name_once` |
| B24 | `test_a_run_with_no_buy_gets_a_history_while_the_book_holds_a_name` |
| B25 | `test_a_held_claim_measures_its_barriers_from_its_close` |

**Module line counts:** All touched Python files are below 200 after formatting; production counts reproduce the Appendix's measurements.

```text
agents/forecaster/agent.py: 169
agents/forecaster/barrier_forecast.py: 176
agents/forecaster/barrier_refusal.py: 88
agents/forecaster/barrier_scorecard.py: 85
agents/forecaster/barrier_store.py: 110
agents/forecaster/held_claim.py: 89
agents/forecaster/held_plan.py: 105
agents/forecaster/history_cache.py: 38
agents/forecaster/poll.py: 172
agents/forecaster/settlement_pass.py: 144
agents/forecaster/settlement_store.py: 100
agents/provider/barrier_history.py: 183
agents/forecaster/tests/held_helpers.py: 153
agents/forecaster/tests/test_held_claim.py: 141
agents/forecaster/tests/test_held_plan.py: 91
agents/forecaster/tests/test_held_poll.py: 59
agents/forecaster/tests/test_held_reads.py: 108
agents/forecaster/tests/test_held_scorecard.py: 41
agents/provider/tests/test_barrier_history_held.py: 61
tests/poll_reference.py: 63
```

**`make ci`:** Redirected to `C:/Users/yury_/Downloads/project/s286-evidence/ci.txt`, then read. **Exit 2; overall gate VERIFIED FAILING.** Steps 1-13 completed successfully; step 14 alone failed for unavailable network. Steps 15-16 did not run inside `make` and were run separately, both exit 0. No floor or baseline was relaxed. `UV_OFFLINE=1`, `UV_NO_SYNC=1`; HTTP(S) proxies pointed to an unavailable loopback port, preventing external access. The inherited OpenAI credential was removed from the gate process. Fresh dependency audit remains owed to the planner.

| Step | Check | Verdict |
| --- | --- | --- |
| 1 | ruff | PASS |
| 2 | format | PASS |
| 3 | mypy | PASS |
| 4 | import-linter | PASS |
| 5 | module size | PASS |
| 6 | module header | PASS |
| 7 | law coverage | PASS |
| 8 | PARAM/settings sync | PASS |
| 9 | sprint status | PASS |
| 10 | tracker size | PASS |
| 11 | Markdown links | PASS |
| 12 | version scheme | PASS |
| 13 | pytest (100.00% floor) | PASS |
| 14 | dependency audit | VERIFIED FAILING: offline PyPI lookup |
| 15 | detect-secrets | PASS separately; NOT RUN inside make after step 14 stopped |
| 16 | untracked secrets | PASS separately; NOT RUN inside make after step 14 stopped |

Pasted command/result lines from the redirected gate (not a pipe):

```text
make ci > C:/Users/yury_/Downloads/project/s286-evidence/ci.txt 2>&1
MAKE_CI_EXIT=2
uv run ruff check . --output-format=github
uv run ruff format --check .
1808 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 1284 source files
uv run lint-imports
Contracts: 5 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
uv run python scripts/check_tracker_size.py
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
TOTAL                                                           21716      0   4666      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_gate_selftest_leaves_nothing.py:57: a link needs a privilege here
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 5264 passed, 9 skipped, 2470 warnings in 434.67s (0:07:14) ==========
uv run python scripts/check_dependency_audit.py
dependency audit failed: WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
requests.exceptions.ProxyError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=9): Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it")))
make: *** [Makefile:60: ci] Error 1
```

Pasted output of the separately completed security steps:

```text
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
DETECT_SECRETS_EXIT=0
uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
UNTRACKED_SECRETS_EXIT=0
```

**`make gate-ran`:** Not done (offline, no push); planner at review, for the final branch SHA from this worktree.

**Not met / verified failing:** `make ci` exit 0 is verified failing: the dependency audit cannot refresh PyPI metadata offline. No vulnerability-clean audit is claimed. Nine pytest cases are skipped for missing local services/secrets, link privilege, SciPy or opt-in network flags (exact reasons above). F1, F2, remote gates, push, merge and deployment are not done. The decision path's live behaviour and held-claim skill are not measured here.

---

## Return notes

- Count correction: the fixed A1-A17 paths name five forecaster test files and one provider test file, not six forecaster test files. Added exactly those six test files plus `agents/forecaster/tests/held_helpers.py` (seven new test/helper modules).
- The handover's main-version snapshot was `0.128.07`; local `main` and `origin/main` were both `dd3abd8b49564963aa26f8a76f0884380c8dd1da`, version `0.128.08`. The next MINOR is still `0.129.00`; `uv lock --offline` exited 0, resolved 180 packages and changed only the project version in `uv.lock` (`0.129.0` after normalization). The lock is staged.
- Corrected the new synthetic Fill fixture from `action` to the shared lineage rule's `side`. Reversed both Appendices, repeated the unchanged-tree red proof (22/22 failed), and reapplied both sections exactly before the passing proof and all 25 break runs. No production adjustment was made.
- A focused coverage check found A4 had not exercised an older placement read after a newer one. Added that ordering to A4: all three new modules then measured 100.00% statement and branch coverage (102 statements, 38 branches). Stopped the first in-progress `make ci` because it began before this test addition; that invocation is interrupted, not a gate result. Repeated the final tests' red proof on the original production/version, the exact Appendix application and the break proof before the final gate.
- Command correction: the additional coverage probe initially named importable modules in `--source`, causing pre-import/collection errors. Re-ran with filesystem scope `--source=agents/forecaster` and a three-file report include; the corrected probe passed. No existing test was run in that failed probe, and no production change was needed.
- Every production line count reproduces the spec; all 20 Appendix blobs match after the breaks. Protected paths and trackers have zero diff; the sole existing-test edit is `tests/poll_reference.py`.
- The first standalone secrets hook reported modified files while the handback was being edited. With edits stopped, the rerun passed; untracked-secrets also passed. `.secrets.baseline` is unchanged. The final full suite reproduces the prototype's 5,264 passed / 9 skipped and 100.00% coverage; the overall gate is still verified failing solely at the offline audit.
- F1, F2, remote gates, push, merge and deployment are not done; they remain planner/operator work. No network or live-service access was used. No new decision, design-log entry or drift amendment was needed.

---

## Appendix — the prototype (`proto-s286` `1e14034b`: `make ci` 5,264 passed, 9 skipped, 100.00 %, every step green, the dependency audit included; 25 / 25 breaks red against the planner's tests; F1 digest `9d5791f9a903ba29`)

Apply with `git apply` from the worktree root: section 1, then section 2. Section 1 is production code and the graph vocabulary pack, section 2 the law cycle, both rollups and the one existing-test edit. The version bump is yours (step 6), not here.

### Section 1 — production code and the vocabulary pack (13 files)

```diff
diff --git a/agents/forecaster/agent.py b/agents/forecaster/agent.py
index abba3b17..bbf358e2 100644
--- a/agents/forecaster/agent.py
+++ b/agents/forecaster/agent.py
@@ -17,6 +17,7 @@ from agents.forecaster.barrier_forecast import forecast_barrier
 from agents.forecaster.barrier_scorecard import barrier_scorecard
 from agents.forecaster.domain.sentiment import NEUTRAL, ModelReading, aggregate
 from agents.forecaster.factor_prediction import forecast_factor
+from agents.forecaster.history_cache import HistoryCache
 from agents.forecaster.model import FakeSentimentModel
 from agents.forecaster.price_signal import read_return
 from agents.forecaster.provider_client import request_news
@@ -72,6 +73,7 @@ class ForecasterAgent(AgentBase):
         self._barrier_fitter = (
             barrier_fitter if barrier_fitter is not None else ArchGarchFitter()
         )
+        self._histories = HistoryCache()
         self.handlers = {
             "forecast": self._forecast,
             "forecast_return": self._forecast_return,
@@ -140,6 +142,7 @@ class ForecasterAgent(AgentBase):
             self._settings,
             self._barrier_fitter,
             request,
+            self._histories,
         )

     def _read_sentiment(self, ticker: str) -> ModelReading:
diff --git a/agents/forecaster/barrier_forecast.py b/agents/forecaster/barrier_forecast.py
index ff2bf608..1879a274 100644
--- a/agents/forecaster/barrier_forecast.py
+++ b/agents/forecaster/barrier_forecast.py
@@ -1,10 +1,12 @@
 """forecast_barrier: state how likely a buy's target comes before its stop.

 Agent: forecaster
-Role: for one ticker and its stop and target, read ~3 years of its own daily bars
-      from the BarrierHistory the provider wrote for the run (DL-241 D10), fit
-      GARCH(1,1)-t, simulate EXP-018's 10-session paths and record the three
-      probabilities as an append-only, advisory BarrierForecast claim. Any refusal
+Role: for one ticker and its stop and target (a buy's, or a held name's live stop
+      and declared target measured from the claim's close, DL-310), read ~3 years
+      of its own daily bars from the BarrierHistory the provider wrote for the run
+      (DL-241 D10), fit GARCH(1,1)-t, simulate EXP-018's 10-session paths and
+      record the three probabilities as an append-only, advisory BarrierForecast
+      claim. Any refusal
       (malformed barriers, no or a failed history, a ticker the provider dropped,
       short history, a failed fit, a conflicting rerun) records a fault and returns
       the neutral reading; a claim is never fabricated (FORE-FAIL-04). A designed
@@ -38,6 +40,8 @@ from agents.forecaster.domain.barrier_garch import (
 )
 from agents.forecaster.domain.features import confidence_from_history
 from agents.forecaster.domain.sentiment import NEUTRAL
+from agents.forecaster.held_claim import held_barriers, held_prices
+from agents.forecaster.held_plan import HELD_SUBJECT
 from contracts.common import Provenance
 from contracts.forecaster import ForecastRequest, ShadowPrediction
 from kernel.errors import fault_boundary
@@ -46,6 +50,7 @@ if TYPE_CHECKING:
     from pydantic import BaseModel

     from agents.forecaster.barrier_fit import GarchFitter
+    from agents.forecaster.history_cache import HistoryCache
     from agents.forecaster.settings import ForecasterSettings
     from contracts.barrier_history import BarRow
     from kernel import FaultSink, GraphStore
@@ -57,8 +62,12 @@ def forecast_barrier(
     settings: ForecasterSettings,
     fitter: GarchFitter,
     request: BaseModel,
+    histories: HistoryCache | None = None,
 ) -> ShadowPrediction:
-    """Return P(target first) as a shadow prediction, or the neutral reading."""
+    """Return P(target first) as a shadow prediction, or the neutral reading.
+
+    ``histories`` lets the run's claims share one read of its BarrierHistory.
+    """
     forecast = ForecastRequest.model_validate(request)
     run_id = f"forecaster-run-{uuid.uuid4().hex}"
     claim: BarrierClaim | None = None
@@ -70,7 +79,7 @@ def forecast_barrier(
         reraise=False,
     ) as capture:
         try:
-            claim = _state_claim(graph, settings, fitter, forecast)
+            claim = _state_claim(graph, settings, fitter, forecast, histories)
         except BarrierClaimRefusedError as refusal:
             record_refusal(sink, refusal)
         else:
@@ -103,11 +112,14 @@ def _state_claim(
     settings: ForecasterSettings,
     fitter: GarchFitter,
     forecast: ForecastRequest,
+    histories: HistoryCache | None,
 ) -> BarrierClaim:
     """Read, fit and simulate; raise BarrierClaimRefusedError on any refusal."""
-    stop, target = barriers(forecast.features)
     ticker = forecast.subject_ref
-    history = read_history(graph, forecast.history_ref, ticker)
+    held = forecast.subject_kind == HELD_SUBJECT
+    prices = held_prices(ticker, forecast.features) if held else None
+    stop, target = (0.0, 0.0) if held else barriers(forecast.features)
+    history = read_history(graph, forecast.history_ref, ticker, histories)
     rows = history.histories[ticker].bars
     if len(rows) < settings.barrier_min_history_sessions:
         raise BarrierClaimRefusedError(
@@ -115,6 +127,9 @@ def _state_claim(
             f"{settings.barrier_min_history_sessions}; no claim",
             severity=DESIGNED,
         )
+    plan = None if prices is None else held_barriers(ticker, prices, rows[-1][4])
+    if plan is not None:
+        stop, target = plan.stop_pct, plan.target_pct
     r, lh_pct, ll_pct = _moves(rows)
     params = accept_fit(fitter.fit(r))
     if params is None:
@@ -148,6 +163,7 @@ def _state_claim(
         seed=seed,
         history_ref=str(forecast.history_ref),
         sessions_requested=history.sessions_requested,
+        held=plan,
     )


diff --git a/agents/forecaster/barrier_refusal.py b/agents/forecaster/barrier_refusal.py
index 0e7f8b20..d54bb9e9 100644
--- a/agents/forecaster/barrier_refusal.py
+++ b/agents/forecaster/barrier_refusal.py
@@ -15,10 +15,11 @@ from __future__ import annotations

 from typing import TYPE_CHECKING

-from contracts.barrier_history import BARRIER_HISTORY_LABEL, BarrierHistory
+from agents.forecaster.history_cache import HistoryCache
 from kernel.errors import fault_from_exception

 if TYPE_CHECKING:
+    from contracts.barrier_history import BarrierHistory
     from kernel import FaultSink, GraphStore
     from kernel.errors import Severity

@@ -50,14 +51,18 @@ def record_refusal(sink: FaultSink, refusal: BarrierClaimRefusedError) -> None:
     )


-def read_history(graph: GraphStore, ref: str | None, ticker: str) -> BarrierHistory:
-    """The provider's BarrierHistory for this request, holding this ticker's bars."""
-    node = graph.get_node(BARRIER_HISTORY_LABEL, ref) if ref else None
-    if node is None:
+def read_history(
+    graph: GraphStore, ref: str | None, ticker: str, cache: HistoryCache | None = None
+) -> BarrierHistory:
+    """The provider's BarrierHistory for this request, holding this ticker's bars.
+
+    With ``cache``, the run's claims share one read of the node (FORE-PERF-04).
+    """
+    history = (cache or HistoryCache()).read(graph, ref) if ref else None
+    if history is None:
         raise BarrierClaimRefusedError(
             f"{ticker}: no BarrierHistory {ref!r} in the graph; no claim"
         )
-    history = BarrierHistory.model_validate(dict(node.props))
     if ticker in history.dropped:
         # A failed history is dropped too; the provider faulted its own fetch.
         raise BarrierClaimRefusedError(
diff --git a/agents/forecaster/barrier_scorecard.py b/agents/forecaster/barrier_scorecard.py
index 672fd6c9..d81fdf05 100644
--- a/agents/forecaster/barrier_scorecard.py
+++ b/agents/forecaster/barrier_scorecard.py
@@ -3,7 +3,10 @@
 Agent: forecaster
 Role: answer the barrier_scorecard capability from the forecaster's own ledger, its
       BarrierForecast claims and their BarrierSettlements: counts settled, void and
-      open, then EXP-018's scores over the settled ones (FORE-OUT-08). Read-only and
+      open, then EXP-018's scores over the settled ones (FORE-OUT-08): buys' claims
+      under the names S241 gave them, held names' claims apart under ``held_``
+      once the ledger holds one (DL-310), each against the same climatology.
+      Read-only and
       repeatable (FORE-IDM-05); never promotion-eligible (FORE-OUT-04); it reports
       and decides nothing (FORE-NEV-01/02).
 External I/O: GraphStore reads via the injected backend.
@@ -29,29 +32,45 @@ def barrier_scorecard(graph: GraphStore, request: BaseModel) -> Scorecard:
     """Score one model's ledger; never promotion-eligible."""
     req = BarrierScorecardRequest.model_validate(request)
     claims, settlements = model_ledger(graph, req.model_id)
-    settled = sorted(
-        (
-            (str(node.props["as_of"]), key)
-            for key, node in settlements.items()
-            if node.props["outcome"] != VOID
-        )
-    )
-    cases = [_case(claims[key], settlements[key]) for _as_of, key in settled]
-    metrics: dict[str, float] = {
-        "settled": float(len(cases)),
-        "void": float(len(settlements) - len(cases)),
-        "open": float(len(claims) - len(settlements)),
-    }
-    metrics.update(ledger_scores(cases))
+    held = {key for key, node in claims.items() if _held(node)}
+    buys = {key: node for key, node in claims.items() if key not in held}
+    metrics, sample_size = _scores(buys, settlements, "")
+    if held:
+        held_claims = {key: claims[key] for key in held}
+        metrics.update(_scores(held_claims, settlements, "held_")[0])
     return Scorecard(
         model_id=req.model_id,
         metrics=metrics,
-        sample_size=len(cases),
+        sample_size=sample_size,
         fresh_as_of=datetime.now(tz=UTC),
         promotion_eligible=False,
     )


+def _held(claim: Node) -> bool:
+    return claim.props.get("subject_kind") == "position"
+
+
+def _scores(
+    claims: dict[str, Node], settlements: dict[str, Node], prefix: str
+) -> tuple[dict[str, float], int]:
+    """Counts and scores over ``claims``, names prefixed; and the settled count."""
+    mine = {key: node for key, node in settlements.items() if key in claims}
+    settled = sorted(
+        (str(node.props["as_of"]), key)
+        for key, node in mine.items()
+        if node.props["outcome"] != VOID
+    )
+    cases = [_case(claims[key], mine[key]) for _as_of, key in settled]
+    metrics: dict[str, float] = {
+        "settled": float(len(cases)),
+        "void": float(len(mine) - len(cases)),
+        "open": float(len(claims) - len(mine)),
+    }
+    metrics.update(ledger_scores(cases))
+    return {f"{prefix}{name}": value for name, value in metrics.items()}, len(cases)
+
+
 def _case(claim: Node, settlement: Node) -> ScoredCase:
     """A settled claim: what it declared, what happened, and its recorded Brier."""
     return ScoredCase(
diff --git a/agents/forecaster/barrier_store.py b/agents/forecaster/barrier_store.py
index 821f73c7..69938cc6 100644
--- a/agents/forecaster/barrier_store.py
+++ b/agents/forecaster/barrier_store.py
@@ -2,7 +2,9 @@

 Agent: forecaster
 Role: persist a barrier claim with every field its later settlement reads, keyed
-      so a rerun on the same last bar merges into the same node (DL-241 D2/D5).
+      so a rerun on the same last bar merges into the same node (DL-241 D2/D5); a
+      held name's claim is keyed apart from a buy's and says which stop and target
+      it stood on (DL-310).
 External I/O: GraphStore writes via the injected backend.
 """

@@ -22,9 +24,12 @@ if TYPE_CHECKING:
     from datetime import date

     from agents.forecaster.domain.barrier_garch import GarchParams
+    from agents.forecaster.held_claim import HeldBarriers
     from kernel import GraphStore, Node

 BARRIER_LABEL = "BarrierForecast"
+#: The key segment and ``subject_kind`` of a held name's claim.
+HELD_KEY_SEGMENT = "held"


 @dataclass(frozen=True)
@@ -44,11 +49,14 @@ class BarrierClaim:
     history_ref: str
     """The provider's BarrierHistory key the bars were read from (DL-241 D10)."""
     sessions_requested: int
+    held: HeldBarriers | None = None
+    """A held name's stop and target, and where they came from; None for a buy."""

     @property
     def key(self) -> str:
-        """``{model_id}:{ticker}:{as_of}``: one claim per model, ticker and bar."""
-        return f"{BARRIER_MODEL_ID}:{self.ticker}:{self.as_of.isoformat()}"
+        """``{model_id}:{ticker}:{as_of}``, or ``{model_id}:held:{ticker}:{as_of}``."""
+        subject = "" if self.held is None else f"{HELD_KEY_SEGMENT}:"
+        return f"{BARRIER_MODEL_ID}:{subject}{self.ticker}:{self.as_of.isoformat()}"


 def write_claim(graph: GraphStore, claim: BarrierClaim) -> Node:
@@ -83,6 +91,16 @@ def write_claim(graph: GraphStore, claim: BarrierClaim) -> Node:
         "created_at": datetime.now(tz=UTC).isoformat(),
         "shadow": True,
     }
+    if claim.held is not None:
+        props.update(
+            {
+                "subject_kind": "position",
+                "target_basis": claim.held.basis,
+                "stop_price": claim.held.prices.stop_price,
+                "target_price": claim.held.prices.target_price,
+                "declared_target_pct": claim.held.prices.target_pct,
+            }
+        )
     existing = graph.get_node(BARRIER_LABEL, claim.key)
     if existing is not None:
         # A rerun on the same last bar (a resumed run) keeps where and when the claim
diff --git a/agents/forecaster/held_claim.py b/agents/forecaster/held_claim.py
new file mode 100644
index 00000000..6289f065
--- /dev/null
+++ b/agents/forecaster/held_claim.py
@@ -0,0 +1,89 @@
+"""Held-name claim barriers: the live stop and the declared target, from the close.
+
+Agent: forecaster
+Role: turn a held-name request's prices into the claim's barriers as fractions of
+      its own last close (DL-310): the stop is ``1 - stop_price / close``; the
+      target is ``target_price / close - 1`` while the close is below it (basis
+      ``declared``), else the declared width again from the close (basis
+      ``rebased``: the name already passed its target). A missing stop or target,
+      or a close at or below the live stop, is a designed refusal (FORE-FAIL-04);
+      a price that is not positive, or a barrier outside (0, 1], is malformed
+      (FORE-IN-07). A barrier is never made up.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from typing import Literal
+
+from agents.forecaster.barrier_refusal import DESIGNED, BarrierClaimRefusedError
+
+TargetBasis = Literal["declared", "rebased"]
+
+
+@dataclass(frozen=True)
+class HeldPrices:
+    """What the request says of a held name: its live stop and declared target."""
+
+    stop_price: float
+    target_price: float
+    target_pct: float
+
+
+@dataclass(frozen=True)
+class HeldBarriers:
+    """A held-name claim's barriers, measured from the claim's own close."""
+
+    prices: HeldPrices
+    stop_pct: float
+    target_pct: float
+    basis: TargetBasis
+
+
+def held_prices(ticker: str, features: dict[str, float]) -> HeldPrices:
+    """The request's prices, or a refusal before the history is read."""
+    if "stop_price" not in features:
+        raise BarrierClaimRefusedError(
+            f"{ticker}: held with no live stop in the graph; no claim",
+            severity=DESIGNED,
+        )
+    if "target_price" not in features or "target_pct" not in features:
+        raise BarrierClaimRefusedError(
+            f"{ticker}: held with no declared target in its lineage; no claim",
+            severity=DESIGNED,
+        )
+    prices = HeldPrices(
+        stop_price=features["stop_price"],
+        target_price=features["target_price"],
+        target_pct=features["target_pct"],
+    )
+    if min(prices.stop_price, prices.target_price) <= 0 or not (
+        0 < prices.target_pct <= 1
+    ):
+        raise BarrierClaimRefusedError(
+            f"{ticker}: held prices must be positive and the declared width in "
+            f"(0, 1]: {prices}; no claim"
+        )
+    return prices
+
+
+def held_barriers(ticker: str, prices: HeldPrices, close: float) -> HeldBarriers:
+    """The claim's stop and target as fractions of ``close``."""
+    if close <= prices.stop_price:
+        raise BarrierClaimRefusedError(
+            f"{ticker}: close {close} at or below the live stop "
+            f"{prices.stop_price}; no claim",
+            severity=DESIGNED,
+        )
+    stop_pct = 1 - prices.stop_price / close
+    basis: TargetBasis = "declared" if close < prices.target_price else "rebased"
+    target_pct = (
+        prices.target_price / close - 1 if basis == "declared" else prices.target_pct
+    )
+    if not (0 < stop_pct <= 1 and 0 < target_pct <= 1):
+        raise BarrierClaimRefusedError(
+            f"{ticker}: barriers from close {close} outside (0, 1]: "
+            f"stop_pct={stop_pct} target_pct={target_pct}; no claim"
+        )
+    return HeldBarriers(prices, stop_pct, target_pct, basis)
diff --git a/agents/forecaster/held_plan.py b/agents/forecaster/held_plan.py
new file mode 100644
index 00000000..a5258d59
--- /dev/null
+++ b/agents/forecaster/held_plan.py
@@ -0,0 +1,105 @@
+"""Held-name barrier plans: the live stop and the declared target of each held name.
+
+Agent: forecaster
+Role: for each name the book holds (`contracts.positions.open_positions`, the book
+      the analyst scored), read the stop the broker holds for it (the newest
+      `BrokerStopOrder` execution placed under its position_ref, not cancelled or
+      replaced) and the target its buy declared (an adopted holding's filled
+      production buy, matched by the rule its stop is read by, DL-222/223; a
+      PM-lineage Position's own `target_pct`), as the features of a held-name
+      claim request (DL-310). Every held name gets a request; a stop or a target
+      the graph does not give is left out of its features, so the claim's refusal
+      names what was missing (FORE-FAIL-04).
+External I/O: none (graph reads only: Position, BrokerStopOrder and, for an
+      adopted holding, Fill each read once per pass).
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING, Final
+
+from contracts.broker_stops import BROKER_STOP_ORDER_LABEL
+from contracts.position_refs import position_ref_for_keys
+from contracts.positions import POSITION_LABEL, is_active_position_node
+from contracts.stop_width import ADOPTED_PROVENANCE, LineageFills, _equals_holding
+
+if TYPE_CHECKING:
+    from kernel import GraphStore, Node
+
+#: The ForecastRequest subject of a held-name claim.
+HELD_SUBJECT: Final = "position"
+#: Append-only markers that end a stop placement's life (EXEC-OBS-03).
+_ENDED = ("cancelled_at", "replaced_at")
+_EXECUTES_EDGE = "EXECUTES"
+
+
+def held_requests(graph: GraphStore) -> tuple[tuple[str, dict[str, float]], ...]:
+    """``(ticker, features)`` for each held name, in ticker order.
+
+    The features carry ``stop_price`` (the live stop, in dollars) and, when the
+    buy's target is known, ``target_price`` and ``target_pct`` (its declared
+    width): the claim measures both from its own last close.
+    """
+    by_ticker: dict[str, list[Node]] = {}
+    for node in graph.list_nodes(POSITION_LABEL):
+        if is_active_position_node(node):
+            by_ticker.setdefault(str(node.props["ticker"]), []).append(node)
+    if not by_ticker:
+        return ()
+    stops = _live_stops(graph)
+    fills = LineageFills(graph)
+    requests = []
+    for ticker, nodes in sorted(by_ticker.items()):
+        features: dict[str, float] = {}
+        ref = position_ref_for_keys(tuple(node.key for node in nodes))
+        if ref in stops:
+            features["stop_price"] = stops[ref]
+        target_pct = _declared_target_pct(graph, nodes, fills)
+        if target_pct is not None:
+            entry = int(nodes[0].props["opened_price_cents"]) / 100
+            features["target_price"] = round(entry * (1 + target_pct), 4)
+            features["target_pct"] = target_pct
+        requests.append((ticker, features))
+    return tuple(requests)
+
+
+def _live_stops(graph: GraphStore) -> dict[str, float]:
+    """position_ref -> the newest placement's stop price, if that one still lives."""
+    newest: dict[str, Node] = {}
+    for node in graph.list_nodes(BROKER_STOP_ORDER_LABEL):
+        ref = str(node.props["position_ref"])
+        if ref not in newest or str(node.props["placed_at"]) > str(
+            newest[ref].props["placed_at"]
+        ):
+            newest[ref] = node
+    return {
+        ref: int(node.props["stop_price_cents"]) / 100
+        for ref, node in newest.items()
+        if not any(node.props.get(marker) for marker in _ENDED)
+    }
+
+
+def _declared_target_pct(
+    graph: GraphStore, nodes: list[Node], fills: LineageFills
+) -> float | None:
+    """The target width the holding's buy declared, or None (one lot only)."""
+    if len(nodes) != 1:
+        return None
+    position = nodes[0]
+    if position.props.get("provenance") == ADOPTED_PROVENANCE:
+        matches = sorted(
+            (fill for fill in fills.nodes() if _equals_holding(fill, position)),
+            key=lambda fill: (str(fill.props.get("submitted_at") or ""), fill.key),
+        )
+        if not matches:
+            return None
+        orders = graph.descendants(
+            matches[-1], max_depth=1, edge_types={_EXECUTES_EDGE}
+        )
+        order = next(iter(orders), None)
+        value = None if order is None else order.props.get("target_pct")
+    else:
+        value = position.props.get("target_pct")
+    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
+        return None
+    return float(value)
diff --git a/agents/forecaster/history_cache.py b/agents/forecaster/history_cache.py
new file mode 100644
index 00000000..a3af0c17
--- /dev/null
+++ b/agents/forecaster/history_cache.py
@@ -0,0 +1,38 @@
+"""The BarrierHistory a run's claims read, held once per run in the forecaster.
+
+Agent: forecaster
+Role: keep the last BarrierHistory read, by key, so a run's claims (its buys and
+      every held name, each one request) read the provider's node once, not once
+      a claim (FORE-PERF-04, DL-310). The node is written once and never changed,
+      so a held copy cannot go stale; a key with no node yet is never held, so a
+      history the provider writes later is read when it lands.
+External I/O: GraphStore reads via the injected backend.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING
+
+from contracts.barrier_history import BARRIER_HISTORY_LABEL, BarrierHistory
+
+if TYPE_CHECKING:
+    from kernel import GraphStore
+
+
+class HistoryCache:
+    """One BarrierHistory, by key: the run's claims share one read."""
+
+    def __init__(self) -> None:
+        """Hold nothing until the first read."""
+        self._key: str | None = None
+        self._history: BarrierHistory | None = None
+
+    def read(self, graph: GraphStore, key: str) -> BarrierHistory | None:
+        """The history under ``key``, read from the graph only when not held."""
+        if key != self._key or self._history is None:
+            node = graph.get_node(BARRIER_HISTORY_LABEL, key)
+            if node is None:
+                return None
+            self._key = key
+            self._history = BarrierHistory.model_validate(dict(node.props))
+        return self._history
diff --git a/agents/forecaster/poll.py b/agents/forecaster/poll.py
index d3f49533..79fef39f 100644
--- a/agents/forecaster/poll.py
+++ b/agents/forecaster/poll.py
@@ -4,8 +4,9 @@ Agent: forecaster
 Role: find AnalystRun nodes not yet forecast and, for each recommendation, request
       the chosen advisory legs from the forecaster over the bus: shadow sentiment,
       return and factor predictions, and a barrier claim for each buy carrying a stop
-      and a target (FORE-TRG-01/02: an unconsumed AnalystRun is the trigger, never a
-      timer; FORE-NEV: shadow, never gates). The caller names the legs (DL-241 D9).
+      and a target and for each held name (DL-310) (FORE-TRG-01/02: an unconsumed
+      AnalystRun is the trigger, never a timer; FORE-NEV: shadow, never gates). The
+      caller names the legs (DL-241 D9).
       The predictions are a side branch off AnalystRun — they never touch the
       PM/execution path, so a missing or slow forecaster cannot block a trade.
 External I/O: none directly (the bus carries the forecast RPCs; provider owns the I/O).
@@ -13,8 +14,9 @@ External I/O: none directly (the bus carries the forecast RPCs; provider owns th

 from __future__ import annotations

-from typing import TYPE_CHECKING
+from typing import TYPE_CHECKING, Literal

+from agents.forecaster.held_plan import HELD_SUBJECT, held_requests
 from contracts.analyst import RecommendationSet
 from contracts.barrier_history import (
     BARRIER_HISTORY_LABEL,
@@ -24,6 +26,7 @@ from contracts.barrier_history import (
     is_current_run,
 )
 from contracts.forecaster import ForecastRequest
+from contracts.positions import open_position_tickers
 from kernel import AgentMessage
 from kernel.graph_pending import pending_nodes

@@ -50,8 +53,9 @@ DEPLOYED_CAPABILITIES = (BARRIER_CAPABILITY,)
 def find_pending(graph: GraphStore, *, now: datetime | None = None) -> list[Node]:
     """Return AnalystRun nodes with no ForecasterRun that are ready to forecast.

-    A run holding a buy with both barriers waits until the provider has written its
-    BarrierHistory (DL-241 D10); a run with no such buy never waits. With ``now``
+    A run holding a buy with both barriers, or run while the book holds a name,
+    waits until the provider has written its BarrierHistory (DL-241 D10, DL-310); a
+    run with neither never waits. With ``now``
     (the deployed loop), only a current run counts (DL-241 D11).
     """
     since = None if now is None else now - CLAIM_RUN_MAX_AGE
@@ -69,7 +73,9 @@ def _history_ready(graph: GraphStore, node: Node) -> bool:
     raw = node.props.get("recommendation_set")
     if raw is None:  # no recommendations to wait for; processing reports the gap
         return True
-    if not barrier_buys(RecommendationSet.model_validate(raw)):
+    if not barrier_buys(RecommendationSet.model_validate(raw)) and not (
+        open_position_tickers(graph)
+    ):
         return True
     return (
         graph.get_node(BARRIER_HISTORY_LABEL, barrier_history_key(node.key)) is not None
@@ -110,11 +116,22 @@ def forecast_analyst_node(
                 features=_barrier_features(recommendation),
                 history_ref=barrier_history_key(node.key),
             )
+    held = held_requests(graph) if BARRIER_CAPABILITY in capabilities else ()
+    for ticker, features in held:
+        _request_forecast(
+            bus,
+            BARRIER_CAPABILITY,
+            ticker,
+            features=features,
+            history_ref=barrier_history_key(node.key),
+            subject_kind=HELD_SUBJECT,
+        )
     forecaster_run = graph.merge_node(
         FORECASTER_RUN_LABEL,
         node.key,
         {
             "recommendation_count": len(recommendation_set.recommendations),
+            "held_count": len(held),
             "source_analyst_run_id": node.key,
         },
     )
@@ -136,6 +153,7 @@ def _request_forecast(
     *,
     features: dict[str, float] | None = None,
     history_ref: str | None = None,
+    subject_kind: Literal["recommendation", "position"] = "recommendation",
 ) -> None:
     """Fire one advisory forecast RPC; the forecaster persists the shadow output."""
     bus.request(
@@ -145,7 +163,7 @@ def _request_forecast(
             message_type="request",
             capability=capability,
             payload=ForecastRequest(
-                subject_kind="recommendation",
+                subject_kind=subject_kind,
                 subject_ref=ticker,
                 features=features or {},
                 history_ref=history_ref,
diff --git a/agents/forecaster/settlement_pass.py b/agents/forecaster/settlement_pass.py
index 233bf5c5..d5a18674 100644
--- a/agents/forecaster/settlement_pass.py
+++ b/agents/forecaster/settlement_pass.py
@@ -6,6 +6,8 @@ Role: find AnalystRuns not yet passed over and, for each, read the MarketData th
       ScanRun -DERIVED_FROM-> MarketData: one node, never a listing), settle or void
       every open BarrierForecast claim its bars decide (FORE-OUT-08, FORE-FAIL-05),
       then record one BarrierSettlementPass so the run is passed once (FORE-IDM-05).
+      Only open claims are read, by key and edge (no SETTLED_BY yet), never a
+      listing of every claim or settlement (FORE-PERF-04, DL-310).
       Loop work fired by the run (FORE-TRG-01/02), never a timer; it sends nothing
       on the bus and touches nothing on the decision path (FORE-NEV-01/02).
 External I/O: GraphStore reads and writes via the injected backend.
@@ -19,7 +21,11 @@ from typing import TYPE_CHECKING

 from agents.forecaster.barrier_store import BARRIER_LABEL
 from agents.forecaster.domain.barrier_settlement import VOID, settle
-from agents.forecaster.settlement_store import settled_claim_keys, write_settlement
+from agents.forecaster.settlement_store import (
+    SETTLED_EDGE,
+    relink_settlement,
+    write_settlement,
+)
 from agents.forecaster.settling_bars import bars_by_ticker, settling_market
 from contracts.barrier_history import CLAIM_RUN_MAX_AGE, is_current_run
 from kernel import CollectingFaultSink
@@ -73,10 +79,10 @@ def settle_analyst_node(
     market = settling_market(graph, node)
     settling_ref = market.key if market is not None else None
     bars = bars_by_ticker(market, sink) if market is not None else {}
-    settled = settled_claim_keys(graph)
     counts: Counter[str] = Counter()
-    for claim in graph.list_nodes(BARRIER_LABEL):
-        if claim.key not in settled:
+    for claim_key in graph.keys_without_edge(BARRIER_LABEL, SETTLED_EDGE):
+        claim = graph.get_node(BARRIER_LABEL, claim_key)
+        if claim is not None and not relink_settlement(graph, claim):
             status = _settle_claim(graph, sink, claim, bars, pass_date, settling_ref)
             counts[status] += 1
     marker = graph.merge_node(
diff --git a/agents/forecaster/settlement_store.py b/agents/forecaster/settlement_store.py
index 1ea02322..4a51e353 100644
--- a/agents/forecaster/settlement_store.py
+++ b/agents/forecaster/settlement_store.py
@@ -31,9 +31,16 @@ def settlement_key(claim_key: str) -> str:
     return f"settlement:{claim_key}"


-def settled_claim_keys(graph: GraphStore) -> set[str]:
-    """The keys of every claim that already has a settlement."""
-    return {str(node.props["claim_key"]) for node in graph.list_nodes(SETTLEMENT_LABEL)}
+def relink_settlement(graph: GraphStore, claim: Node) -> bool:
+    """Link a settlement written without its edge (a pass stopped between the two).
+
+    True when the claim was already settled: the pass leaves it as written.
+    """
+    node = graph.get_node(SETTLEMENT_LABEL, settlement_key(claim.key))
+    if node is None:
+        return False
+    graph.add_edge(claim, node, SETTLED_EDGE)
+    return True


 def write_settlement(
diff --git a/agents/provider/barrier_history.py b/agents/provider/barrier_history.py
index 4b8cfd83..3b9893f7 100644
--- a/agents/provider/barrier_history.py
+++ b/agents/provider/barrier_history.py
@@ -1,8 +1,9 @@
 """Provider barrier-history work kind: the long daily history a barrier claim needs.

 Agent: provider
-Role: find AnalystRun nodes holding a buy with both a suggested stop and target and no
-      BarrierHistory yet; fetch those tickers' daily bars in ONE request through the
+Role: find AnalystRun nodes holding a buy with both a suggested stop and target, or
+      run while the book holds a name (DL-310), and no BarrierHistory yet; fetch
+      those buys' and held names' daily bars in ONE request through the
       provider's own fetch path (the source's feed and end rule, then validation and
       the unchanged extreme-move guard), and write ONE BarrierHistory node linked from
       the AnalystRun. A dropped ticker is listed with its reason; a failed fetch still
@@ -27,6 +28,7 @@ from contracts.barrier_history import (
     barrier_history_key,
     is_current_run,
 )
+from contracts.positions import open_position_tickers
 from contracts.provider import DataRequest
 from kernel.errors import fault_boundary
 from kernel.graph_pending import pending_nodes
@@ -46,7 +48,7 @@ _SOURCE_FAILED_NOTE = "source_unavailable"
 def find_pending_barrier_history(
     graph: GraphStore, *, now: datetime | None = None
 ) -> list[Node]:
-    """AnalystRun nodes with a qualifying buy and no BarrierHistory yet.
+    """AnalystRun nodes with a qualifying buy or a held name, and no history yet.

     With ``now`` (the deployed loop), only a current run counts (DL-241 D11): the
     store is asked only for runs created since ``now - CLAIM_RUN_MAX_AGE``, so the
@@ -59,13 +61,13 @@ def find_pending_barrier_history(
             graph, ANALYST_RUN_LABEL, BARRIER_HISTORY_EDGE, created_at_from=since
         )
         if (now is None or is_current_run(node.props, now))
-        and _qualifying_tickers(node)
+        and _qualifying_tickers(graph, node)
     ]


 def write_barrier_history(node: Node, *, agent: ProviderAgent) -> None:
     """Fetch the run's qualifying tickers once and write one linked BarrierHistory."""
-    tickers = _qualifying_tickers(node)
+    tickers = _qualifying_tickers(agent._graph, node)
     sessions = agent._settings.barrier_history_sessions
     window = barrier_window(sessions, run_as_of(agent._graph, node))
     market: MarketData | None = None
@@ -84,12 +86,14 @@ def write_barrier_history(node: Node, *, agent: ProviderAgent) -> None:
     agent._graph.add_edge(node, written, BARRIER_HISTORY_EDGE)


-def _qualifying_tickers(node: Node) -> tuple[str, ...]:
+def _qualifying_tickers(graph: GraphStore, node: Node) -> tuple[str, ...]:
+    """The run's barrier buys, then each held name, once each, in that order."""
     raw = node.props.get("recommendation_set")
     if raw is None:
         return ()
-    recommendation_set = RecommendationSet.model_validate(raw)
-    return tuple(dict.fromkeys(rec.ticker for rec in barrier_buys(recommendation_set)))
+    buys = barrier_buys(RecommendationSet.model_validate(raw))
+    held = open_position_tickers(graph)
+    return tuple(dict.fromkeys((*(rec.ticker for rec in buys), *held)))


 def _history(
diff --git a/orchestration/packs/trading_graph_vocabulary.json b/orchestration/packs/trading_graph_vocabulary.json
index ca89bb11..920f0217 100644
--- a/orchestration/packs/trading_graph_vocabulary.json
+++ b/orchestration/packs/trading_graph_vocabulary.json
@@ -572,6 +572,7 @@
     "BarrierForecast": [
       "as_of",
       "created_at",
+      "declared_target_pct",
       "entry_close",
       "fit_status",
       "garch_alpha",
@@ -590,7 +591,11 @@
       "seed",
       "shadow",
       "stop_pct",
+      "stop_price",
+      "subject_kind",
+      "target_basis",
       "target_pct",
+      "target_price",
       "ticker"
     ],
     "BarrierHistory": [
```

### Section 2 — the law cycle, the rollups and `tests/poll_reference.py` (7 files)

```diff
diff --git a/agents/forecaster/laws/laws.md b/agents/forecaster/laws/laws.md
index 443dca31..865c6067 100644
--- a/agents/forecaster/laws/laws.md
+++ b/agents/forecaster/laws/laws.md
@@ -1,6 +1,6 @@
 # `Forecaster` — Laws

-**Prefix:** `FORE` · **status:** LOCKED v1.10 · **Owner:** Yury Gurevich
+**Prefix:** `FORE` · **status:** LOCKED v1.11 · **Owner:** Yury Gurevich

 > Produce clearly-labelled shadow ML forecasts (sentiment + price/return) and measure
 > them via scorecards — every output is advisory and never gates a decision until
@@ -43,16 +43,22 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   no claim, a fault, and the `FORE-OUT-06` neutral reading, never a raise to the bus. The stock's
   daily bars are read **only** from that provider-written node, never requested over the bus; no
   named node, a node that does not hold the ticker, a ticker the provider dropped, or a failed node
-  is a refusal (`FORE-FAIL-04`).
+  is a refusal (`FORE-FAIL-04`). A **held name's** request (`subject_kind: "position"`, `FORE-OUT-09`)
+  carries prices, not fractions: `stop_price` (the live stop, dollars), `target_price` (the declared
+  target, dollars) and `target_pct` (the declared width, in (0, 1]); its barriers are measured from
+  the claim's own close once the history is read. A missing stop or target is refused before the
+  history is read; a price that is not positive or a width outside (0, 1] is malformed.

 ## Triggers (`TRG`)

 - **FORE-TRG-01** — Every capability runs on a request, never on an event subscription. A request
   comes from an RPC caller or from the forecaster's graph-pull loop: for each `AnalystRun` that has no
-  `ForecasterRun` yet (and, when it holds a buy with both a stop and a target, whose `BarrierHistory`
-  the provider has written; a run with no such buy never waits), the loop requests the legs its
+  `ForecasterRun` yet (and, when it holds a buy with both a stop and a target or the book holds a
+  name, whose `BarrierHistory` the provider has written; a run with neither never waits), the loop
+  requests the legs its
   caller names and then records one `ForecasterRun` for it, so an `AnalystRun` is forecast once. The **deployed** loop names
-  `forecast_barrier` only, fired once per buy that carries both a stop and a target; `forecast`,
+  `forecast_barrier` only, fired once per buy that carries both a stop and a target and once per held
+  name (`FORE-OUT-09`), and its `ForecasterRun` records `held_count`; `forecast`,
   `forecast_return` and `forecast_factor` are fired by the in-process pipeline or an RPC caller, never
   by the deployed loop. A leg name the loop does not know is refused before any request. The deployed
   loop also counts only a *current* `AnalystRun`, one created within 24 h (the shared
@@ -121,6 +127,24 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   `skill_hi` (1,000 resamples of whole `as_of` dates, a fixed seed). A score it cannot compute is
   absent, never zero: with no settled claim only the counts are reported, and with fewer than two
   settled dates there is no interval. The scorecard reports; it decides nothing (`FORE-NEV-01/02`).
+- **FORE-OUT-09** — Each name the book holds gets a barrier claim per run, beside the buys'
+  (DL-310). The held book is `contracts.positions`' active Positions, the book the analyst scored.
+  Its **stop** is the one the broker holds: the newest `BrokerStopOrder` execution placed under the
+  holding's position_ref, unless that placement was cancelled or replaced. Its **target** is the one
+  its buy declared: for a broker-adopted Position, the `target_pct` of the `OrderIntent` its one
+  exact lineage buy executed (the rule its stop is read by, DL-222/223), and for a PM-lineage
+  Position its own `target_pct`, as a price from the holding's entry; two lots of one name, or no
+  such buy, declare none. The claim measures both from its last close: `stop_pct` = 1 − stop ÷ close;
+  while the close is below the target, `target_pct` = target ÷ close − 1 (`target_basis: declared`),
+  and once at or past it, the declared width again (`target_basis: rebased`). It is keyed
+  `{model_id}:held:{ticker}:{as_of}`, apart from a buy's claim on the same bar, and carries what
+  `FORE-OUT-07` lists plus `subject_kind: position`, `target_basis`, `stop_price`, `target_price` and
+  `declared_target_pct`. It is settled by `FORE-OUT-08`'s rule like any claim. It reads Position,
+  `BrokerStopOrder`, Fill and `OrderIntent` nodes and writes none of them (`FORE-NEV-01/02`).
+- **FORE-OUT-10** — `barrier_scorecard` reports the buys' claims under the names `FORE-OUT-08` gives
+  them, exactly as it would with no held claim in the ledger, and, once the ledger holds a held-name
+  claim, the held claims' own counts and scores under the same names prefixed `held_`, against the
+  same climatology. `sample_size` counts the buys' settled claims. *(DL-310.)*

 ## Prohibitions (`NEV`)

@@ -193,9 +217,11 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   whose the refusal is**. A **designed** "no claim", the system working as intended, is a
   `warning`, never an open incident: a ticker the provider dropped or a history it wrote as failed
   (the provider records its own fault for the failed fetch), fewer than
-  `barrier_min_history_sessions` bars, or a fit outside EXP-018's acceptance rule. A **missing or
-  broken input** is an `error`: no named `BarrierHistory`, one that does not hold the ticker,
-  malformed barriers (`FORE-IN-07`), an optimiser exception or an absent `arch`. *(DL-247 D3,
+  `barrier_min_history_sessions` bars, a fit outside EXP-018's acceptance rule, or a held name with
+  no live stop, no declared target, or a close at or below its live stop (`FORE-OUT-09`). A **missing
+  or broken input** is an `error`: no named `BarrierHistory`, one that does not hold the ticker,
+  malformed barriers or held prices (`FORE-IN-07`), a held claim's barrier outside (0, 1], an
+  optimiser exception or an absent `arch`. *(DL-247 D3,
   DRIFT-089.)*
 - **FORE-FAIL-05** — A claim that cannot be settled honestly is never scored as a stop, a target or
   neither: it is settled `void` with a named `void_reason` and no `brier`. `suspected_corporate_action`
@@ -256,6 +282,13 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   bars minimum for full confidence).
 - **FORE-PERF-03** — `news_lookback_days=7` caps the provider request window; `price_lookback_days
   =90` caps the return model window.
+- **FORE-PERF-04** — A run's claims share **one read** of its `BarrierHistory` per forecaster
+  process: the node is written once and never changed, so the last one read is held by key and a key
+  with no node yet is never held. A settlement pass finds the open claims **by key and edge** (a
+  `BarrierForecast` with no `SETTLED_BY` yet) and reads only those: it never lists every claim or
+  every settlement, so its reads grow with the open claims, not with the ledger. A settlement written
+  without its edge (a pass stopped between the two) is linked on the next pass, never settled again.
+  *(DL-310: held names add ~34 claims a night, and a history of ~36 tickers is ~1.3 MB.)*

 ## Capability declaration (`CAP`)

@@ -408,3 +441,10 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   candidate props. The existing current-run and history-readiness predicates remain; a local call
   without `now` stays unbounded. Why: the two idle polls downloaded every `AnalystRun` separately.
   Payload, backlog, bad-stamp and existing loop tests re-prove the clause; 25 / 52 unchanged.
+- v1.11 — S286 / DL-310 (2026-10-21): a barrier claim on every held name. New `FORE-OUT-09` (the held
+  book, its live stop and declared target, the claim's barriers from its close, its key and fields),
+  `FORE-OUT-10` (the scorecard keeps the buys' metrics and reports held claims under `held_`) and
+  `FORE-PERF-04` (one history read per run; a settlement pass reads open claims only). Amended
+  `FORE-IN-07` (the held request's prices), `FORE-TRG-01` (a run waits for its history while the book
+  holds a name; one request per held name; `held_count`) and `FORE-FAIL-04` (three designed held
+  refusals; malformed held prices). 25 / 52 → 28 / 55.
diff --git a/agents/forecaster/laws/test-plan.md b/agents/forecaster/laws/test-plan.md
index 41d39c1e..4490c3aa 100644
--- a/agents/forecaster/laws/test-plan.md
+++ b/agents/forecaster/laws/test-plan.md
@@ -10,8 +10,8 @@
 | FORE-IN-04 | ⬜ | — |
 | FORE-IN-05 | ⬜ | — |
 | FORE-IN-06 | ⬜ | — |
-| FORE-IN-07 | 🟩 | `test_malformed_barriers_record_no_claim`, `test_no_named_history_records_no_claim`, `test_a_ticker_the_history_never_requested_records_no_claim`, `test_a_ticker_the_provider_dropped_records_no_claim`, `test_a_failed_history_records_no_claim`, `test_a_successful_call_writes_one_complete_claim`, `test_the_poll_asks_for_a_claim_only_for_buys_with_both_barriers`, `test_the_forecaster_waits_for_the_runs_barrier_history`, `test_a_run_with_no_qualifying_buy_never_waits`, `test_a_deployed_forecaster_claims_from_the_provider_written_history`, `test_the_local_pipeline_claims_from_the_provider_written_history`, `test_no_barrier_history_is_an_error_and_an_incident`, `test_every_missing_or_broken_input_is_an_error` |
-| FORE-TRG-01 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction`, `test_main_runs_the_graph_pull_loop_with_the_barrier_leg_only`, `test_an_unknown_leg_is_refused_before_any_request`, `test_the_local_pipeline_still_fires_all_four_legs`, `test_the_forecaster_waits_for_the_runs_barrier_history`, `test_a_run_with_no_qualifying_buy_never_waits`, `test_a_failed_fetch_never_leaves_the_forecaster_waiting`, `test_the_forecaster_claims_a_current_run_only`, `test_the_deployed_loop_settles_on_a_current_run_only`, `test_the_pass_reads_only_its_own_runs_market_data`, `orchestration/tests/test_forecaster_settlement_stage.py::test_the_local_pipeline_settles_an_older_claim`, `tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work` (both finders), `test_forecaster_pending_payloads.py::test_each_forecaster_finder_fetches_only_its_current_backlog`, `test_forecaster_pending_payloads.py::test_both_finders_keep_the_shared_current_run_predicate` |
+| FORE-IN-07 | 🟩 | `test_malformed_barriers_record_no_claim`, `test_no_named_history_records_no_claim`, `test_a_ticker_the_history_never_requested_records_no_claim`, `test_a_ticker_the_provider_dropped_records_no_claim`, `test_a_failed_history_records_no_claim`, `test_a_successful_call_writes_one_complete_claim`, `test_the_poll_asks_for_a_claim_only_for_buys_with_both_barriers`, `test_the_forecaster_waits_for_the_runs_barrier_history`, `test_a_run_with_no_qualifying_buy_never_waits`, `test_a_deployed_forecaster_claims_from_the_provider_written_history`, `test_the_local_pipeline_claims_from_the_provider_written_history`, `test_no_barrier_history_is_an_error_and_an_incident`, `test_every_missing_or_broken_input_is_an_error`, `test_a_held_claim_measures_its_barriers_from_its_close` |
+| FORE-TRG-01 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction`, `test_main_runs_the_graph_pull_loop_with_the_barrier_leg_only`, `test_an_unknown_leg_is_refused_before_any_request`, `test_the_local_pipeline_still_fires_all_four_legs`, `test_the_forecaster_waits_for_the_runs_barrier_history`, `test_a_run_with_no_qualifying_buy_never_waits`, `test_a_failed_fetch_never_leaves_the_forecaster_waiting`, `test_the_forecaster_claims_a_current_run_only`, `test_the_deployed_loop_settles_on_a_current_run_only`, `test_the_pass_reads_only_its_own_runs_market_data`, `orchestration/tests/test_forecaster_settlement_stage.py::test_the_local_pipeline_settles_an_older_claim`, `tests/test_poll_payloads.py::test_no_poll_downloads_a_payload_to_find_its_work` (both finders), `test_forecaster_pending_payloads.py::test_each_forecaster_finder_fetches_only_its_current_backlog`, `test_forecaster_pending_payloads.py::test_both_finders_keep_the_shared_current_run_predicate`, `test_every_held_name_gets_a_claim_request_beside_the_buys`, `test_a_run_waits_for_its_bars_while_the_book_holds_a_name` |
 | FORE-TRG-02 | 🟩 | `test_served_forecast_is_request_triggered_shadow_only`, `test_main_runs_the_graph_pull_loop_with_the_barrier_leg_only`, `test_no_agent_entrypoint_references_retired_loop` |
 | FORE-OUT-01 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction` |
 | FORE-OUT-02 | 🟩 | `test_every_forecast_is_a_shadow_signal`, `test_served_forecast_is_request_triggered_shadow_only` |
@@ -20,7 +20,9 @@
 | FORE-OUT-05 | 🟩 | `test_forecast_persists_and_returns_a_shadow_prediction` |
 | FORE-OUT-06 | 🟩 | `test_forecast_with_no_news_is_neutral_zero_confidence` |
 | FORE-OUT-07 | 🟩 | `test_a_rising_history_reaches_the_target_first`, `test_a_falling_history_reaches_the_stop_first`, `test_a_flat_history_with_wide_barriers_reaches_neither`, `test_a_session_touching_both_barriers_counts_as_the_stop`, `test_the_simulation_equals_exp018`, `test_a_successful_call_writes_one_complete_claim`, `test_a_full_pass_never_reaches_the_decision_path`, `test_a_deployed_forecaster_claims_from_the_provider_written_history`, `test_the_local_pipeline_claims_from_the_provider_written_history` |
-| FORE-OUT-08 | 🟩 | `test_the_outcome_is_exp018s`, `test_the_settlement_equals_the_test_beds_outcome_on_random_paths`, `test_the_entry_is_the_settling_series_own_close`, `test_a_settlement_records_every_field_the_ledger_needs`, `test_a_split_settles_void_with_no_brier`, `test_the_settlement_passes_the_packs_vocabulary_guard`, `test_the_oracle_is_the_records_run`, `test_the_scorecard_reports_the_ledger_as_exp018_scores_it`, `test_fewer_than_two_settled_dates_give_no_interval`, `test_an_empty_ledger_reports_counts_and_no_scores`, `test_another_models_ledger_is_its_own`, `orchestration/tests/test_forecaster_settlement_stage.py::test_the_local_pipeline_settles_an_older_claim` |
+| FORE-OUT-08 | 🟩 | `test_the_outcome_is_exp018s`, `test_the_settlement_equals_the_test_beds_outcome_on_random_paths`, `test_the_entry_is_the_settling_series_own_close`, `test_a_settlement_records_every_field_the_ledger_needs`, `test_a_split_settles_void_with_no_brier`, `test_the_settlement_passes_the_packs_vocabulary_guard`, `test_the_oracle_is_the_records_run`, `test_the_scorecard_reports_the_ledger_as_exp018_scores_it`, `test_fewer_than_two_settled_dates_give_no_interval`, `test_an_empty_ledger_reports_counts_and_no_scores`, `test_another_models_ledger_is_its_own`, `orchestration/tests/test_forecaster_settlement_stage.py::test_the_local_pipeline_settles_an_older_claim`, `test_a_pass_lists_no_claim_and_settles_the_open_ones` |
+| FORE-OUT-09 | 🟩 | `test_a_held_name_carries_its_live_stop_and_declared_target`, `test_a_pm_lineage_position_declares_its_own_target`, `test_a_target_the_lineage_does_not_declare_is_left_out`, `test_the_newest_live_placement_is_the_stop`, `test_every_held_name_gets_a_claim_request_beside_the_buys`, `test_a_held_claim_measures_its_barriers_from_its_close`, `test_past_its_target_a_held_claim_asks_for_the_width_again` |
+| FORE-OUT-10 | 🟩 | `test_held_claims_are_scored_apart_and_the_buys_scores_stand` |
 | FORE-NEV-01 | 🟩 | `test_every_forecast_is_a_shadow_signal`, `test_contract_declares_never_clauses_and_no_external_io`, `test_a_full_deployed_pass_never_reaches_the_decision_path`, `test_nothing_outside_the_forecaster_reads_the_ledger` |
 | FORE-NEV-02 | 🟩 | `test_contract_declares_never_clauses_and_no_external_io`, `test_served_forecast_is_request_triggered_shadow_only`, `test_forecast_factor_enabled_writes_shadow_only_prediction`, `test_a_full_deployed_pass_never_reaches_the_decision_path`, `test_nothing_outside_the_forecaster_reads_the_ledger` |
 | FORE-NEV-03 | 🟩 | `test_scorecard_is_never_promotion_eligible`, `test_contract_declares_never_clauses_and_no_external_io`, `test_the_scorecard_reports_the_ledger_as_exp018_scores_it` |
@@ -30,14 +32,14 @@
 | FORE-IDM-01 | ⬜ | — |
 | FORE-IDM-02 | ⬜ | — |
 | FORE-IDM-03 | ⬜ | the three shadow scorecards read-only and repeatable over `ShadowPrediction` nodes; no test calls each twice on one graph state; _tbd_ |
-| FORE-IDM-04 | 🟩 | `test_the_same_bars_give_the_same_claim_merged_into_one_node`, `test_a_different_claim_for_the_same_last_bar_is_refused`, `test_the_seed_is_stable_across_processes` |
-| FORE-IDM-05 | 🟩 | `test_a_claim_is_settled_once`, `test_the_scorecard_is_read_only_and_repeatable` |
+| FORE-IDM-04 | 🟩 | `test_the_same_bars_give_the_same_claim_merged_into_one_node`, `test_a_different_claim_for_the_same_last_bar_is_refused`, `test_the_seed_is_stable_across_processes`, `test_a_buy_and_a_held_claim_on_one_bar_both_stand` |
+| FORE-IDM-05 | 🟩 | `test_a_claim_is_settled_once`, `test_the_scorecard_is_read_only_and_repeatable`, `test_a_settlement_written_without_its_edge_is_linked_not_redone` |
 | FORE-ORD-01 | ⬜ | — |
 | FORE-ORD-02 | ⬜ | — |
 | FORE-FAIL-01 | 🟩 | `test_forecast_falls_back_to_neutral_on_a_model_fault` |
 | FORE-FAIL-02 | 🟩 | `test_forecast_survives_a_provider_fault` |
 | FORE-FAIL-03 | ⬜ | Demoted S156: `test_forecast_return_falls_back_to_neutral_on_a_model_fault` covers a generic injected model exception, not the specific missing-LightGBM-file clause. |
-| FORE-FAIL-04 | 🟩 | `test_a_fit_is_accepted_or_capped_as_exp018_did`, `test_the_boundary_tolerance_is_exp018s`, `test_every_other_fit_fails`, `test_a_failed_fit_records_no_claim`, `test_a_fitter_exception_records_no_claim`, `test_short_history_records_no_claim_and_never_fits`, `test_a_ticker_the_provider_dropped_records_no_claim`, `test_a_failed_history_records_no_claim`, `test_no_named_history_records_no_claim`, `test_without_arch_the_default_fitter_records_no_claim`, `test_a_failed_fetch_never_leaves_the_forecaster_waiting`, `test_a_ticker_the_provider_dropped_is_a_warning_not_an_incident`, `test_no_barrier_history_is_an_error_and_an_incident`, `test_every_designed_refusal_is_a_warning`, `test_every_missing_or_broken_input_is_an_error` |
+| FORE-FAIL-04 | 🟩 | `test_a_fit_is_accepted_or_capped_as_exp018_did`, `test_the_boundary_tolerance_is_exp018s`, `test_every_other_fit_fails`, `test_a_failed_fit_records_no_claim`, `test_a_fitter_exception_records_no_claim`, `test_short_history_records_no_claim_and_never_fits`, `test_a_ticker_the_provider_dropped_records_no_claim`, `test_a_failed_history_records_no_claim`, `test_no_named_history_records_no_claim`, `test_without_arch_the_default_fitter_records_no_claim`, `test_a_failed_fetch_never_leaves_the_forecaster_waiting`, `test_a_ticker_the_provider_dropped_is_a_warning_not_an_incident`, `test_no_barrier_history_is_an_error_and_an_incident`, `test_every_designed_refusal_is_a_warning`, `test_every_missing_or_broken_input_is_an_error`, `test_a_target_the_lineage_does_not_declare_is_left_out`, `test_what_a_held_claim_cannot_stand_on_is_refused` |
 | FORE-FAIL-05 | 🟩 | `test_a_split_is_void_never_a_stop`, `test_the_corporate_action_bounds_are_the_specs`, `test_too_few_bars_is_not_a_settlement`, `test_an_unsettled_claim_is_void_45_days_after_as_of`, `test_a_split_settles_void_with_no_brier`, `test_a_claim_the_pass_cannot_read_faults_and_stays_open`, `test_an_unreadable_market_data_faults_and_the_age_rule_still_runs` |
 | FORE-TYP-01 | 🟩 | `tests/test_contract_required_payload_fields.py::test_forecaster_payload_fields_required_by_law` |
 | FORE-TYP-02 | ⬜ | — |
@@ -54,6 +56,7 @@
 | FORE-PERF-01 | ⬜ | — |
 | FORE-PERF-02 | ⬜ | — |
 | FORE-PERF-03 | ⬜ | — |
+| FORE-PERF-04 | 🟩 | `test_a_runs_claims_read_its_history_once`, `test_a_history_the_provider_writes_later_is_read_when_it_lands`, `test_a_pass_lists_no_claim_and_settles_the_open_ones` |
 | FORE-CAP | ⬜ | — |

-## **Green: 25 / 52**
+## **Green: 28 / 55**
diff --git a/agents/provider/laws/laws.md b/agents/provider/laws/laws.md
index 02c2f0e4..ea54e386 100644
--- a/agents/provider/laws/laws.md
+++ b/agents/provider/laws/laws.md
@@ -2,7 +2,7 @@

 # Provider — Laws

-**Prefix:** `PROV` · **status:** LOCKED v1.10 · **Owner:** Yury Gurevich
+**Prefix:** `PROV` · **status:** LOCKED v1.11 · **Owner:** Yury Gurevich

 > The provider is the system's **single sealed boundary to the outside market**: it turns raw external
 > feeds into clean, validated, provenance-stamped facts so that every other agent can reason on data
@@ -45,12 +45,12 @@ IDs are append-only (conventions §2). A clause is green only when a functional
 - `PROV-TRG-01` — **Request-driven**: it acts only on a **recorded data need**. That is a data
   request on the bus (a data-request event consumed from its subscribed topic, ADR-0005, or a
   capability request from an authorised caller, `PROV-SEC-07`), an unconsumed **`RunRequest`** on
-  the graph (DL-08, `PROV-TRG-05`), or an **`AnalystRun`'s qualifying buys** with no `BarrierHistory`
-  yet (`PROV-TRG-04`). A `RunRequest` needs no bus event to be acted on. It is never self-initiated
+  the graph (DL-08, `PROV-TRG-05`), or an **`AnalystRun`'s qualifying buys or held names** with no
+  `BarrierHistory` yet (`PROV-TRG-04`). A `RunRequest` needs no bus event to be acted on. It is never self-initiated
   (`PROV-TRG-02`). *(DRIFT-082; was: only a data-request event from its subscribed topic.)*
 - `PROV-TRG-02` — It **never self-triggers** — no timer, no scheduled fetch, no speculative
   prefetch absent a request. A data need another stage recorded in the graph (a `RunRequest`, DL-08;
-  an `AnalystRun`'s qualifying buys, `PROV-TRG-04`) is a request: finding it unconsumed is a
+  an `AnalystRun`'s qualifying buys or held names, `PROV-TRG-04`) is a request: finding it unconsumed is a
   trigger, not a self-trigger, and a poll that finds none fetches nothing. The poll finds its
   pending work **by key and edge alone**: a `RunRequest` with no `INGESTED_BY` edge, and a current
   `AnalystRun` with no `BARRIER_HISTORY_BY` edge. It **fetches props only for those nodes**, so a poll
@@ -58,9 +58,11 @@ IDs are append-only (conventions §2). A clause is green only when a functional
 - `PROV-TRG-03` — Precondition to fetch is a **valid** request; otherwise it rejects and does not
   fetch.
 - `PROV-TRG-04` — An `AnalystRun` holding at least one **buy with both a suggested stop and a
-  suggested target** (the contract's `barrier_buys` rule) and no `BarrierHistory` yet is a trigger
-  for the barrier history (`PROV-OUT-08`). A run with no such buy triggers nothing: sells, holds and a
-  buy missing either barrier ask for no history. The **deployed** loop counts only a *current* run,
+  suggested target** (the contract's `barrier_buys` rule), or run while the book holds a name
+  (`contracts.positions`' active Positions, DL-310), and no `BarrierHistory` yet is a trigger for the
+  barrier history (`PROV-OUT-08`). A run with neither triggers nothing: sells, holds and a buy missing
+  either barrier ask for no history while nothing is held, and a run with no recommendation set asks
+  for none at all. The **deployed** loop counts only a *current* run,
   one created within 24 h (`contracts/barrier_history.is_current_run`, DL-241 D11): an older run is
   never fetched, so the backlog of runs no forecaster ever read is not claimed on later bars.
 - `PROV-TRG-05` — An ingest a **`RunRequest`** triggers serves **that run's as-of** (its
@@ -108,7 +110,8 @@ IDs are append-only (conventions §2). A clause is green only when a functional
   clause. *(DRIFT-080 — S238, DL-233, DL-239; DRIFT-084 — S251.)*
 - `PROV-OUT-08` — For an `AnalystRun` that triggers `PROV-TRG-04` it makes **one** OHLCV request
   through its own fetch path (the source's feed and end rule, then validation and the extreme-move
-  guard of `PROV-OUT-09`, all shared with the daily request) for **exactly** those buys' tickers,
+  guard of `PROV-OUT-09`, all shared with the daily request) for **exactly** those buys' tickers
+  and then each held name's, each once (a name both bought and held, once),
   over a calendar window holding at least `barrier_history_sessions` sessions
   **that ends on the run's as-of** (the `window_end` of the `MarketData` the run was scanned
   from, read through the run's lineage `AnalystRun ←ANALYZED_BY— ScanRun —DERIVED_FROM→
@@ -121,8 +124,9 @@ IDs are append-only (conventions §2). A clause is green only when a functional
   extreme-move guard, or nothing served), never silently absent; a served ticker whose last bar is
   stale is listed as `stale`. A **failed fetch still writes the node**, `status: failed` with the
   reason and every ticker dropped with it, so no reader waits forever — never an empty success, never
-  no node. A barrier fetch holds too few tickers for the `PROV-OUT-09` guard to fire (its √(n−1)
-  ceiling), so this path **leans on the daily request's guard**: its newest session is the one the
+  no node. A barrier fetch of fewer than 66 tickers cannot fire the `PROV-OUT-09` guard (its √(n−1)
+  ceiling against `max_daily_move_sigma` 8; with the held names it was 36 on 2026-10-20), so this path
+  **leans on the daily request's guard**: its newest session is the one the
   daily request judged, and a ticker the daily request excluded never becomes a buy.
   A run with no such `MarketData` has no as-of and is served as an ingest no run triggered is:
   its window ends on the UTC date of the fetch (`PROV-TRG-05`). A `MarketData` whose
@@ -518,3 +522,8 @@ status:
   fetch's UTC date; an absent or unparseable stored `window_end` fails before any fetch or
   history write. Why: the clock shifted a late run's history and claim beyond the bars its
   barriers came from (DRIFT-110). No new clause, contract, property or tunable; 24 / 67 unchanged.
+- v1.11 — S286 / DL-310 (2026-10-21): the barrier history also holds every held name. `PROV-TRG-01`,
+  `PROV-TRG-02` and `PROV-TRG-04` amended (a run triggers its history while the book holds a name,
+  with or without a barrier buy; a run with no recommendation set never does); `PROV-OUT-08` amended
+  (one request for the barrier buys, then each held name, once each; the guard's reach restated:
+  fewer than 66 tickers cannot fire it). No new clause, contract or tunable; 24 / 67 unchanged.
diff --git a/agents/provider/laws/test-plan.md b/agents/provider/laws/test-plan.md
index 9f08c668..ccf7b80e 100644
--- a/agents/provider/laws/test-plan.md
+++ b/agents/provider/laws/test-plan.md
@@ -113,8 +113,8 @@ Status: ⬜ gray (no passing test) · 🟩 green (≥1 passing test cites the ID
 | PROV-IDN-03 | Provider exclusive ownership of market-fact/regime artifacts and durable store needs a single-writer proof. | boundary | _tbd_ | ⬜ |
 | PROV-IN-02 | Regime request with a single as-of date is accepted and served. | happy | _tbd_ | ⬜ |
 | PROV-TRG-03 | Invalid requests must be rejected before any fetch occurs. | boundary | _tbd_ | ⬜ |
-| PROV-TRG-04 | An `AnalystRun` with a buy carrying both barriers and no `BarrierHistory` triggers the barrier history; sells, holds, a buy missing a barrier, or no recommendation set trigger nothing; the loop carries both work kinds. | trigger | `test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch; test_barrier_history.py::test_a_run_without_a_qualifying_buy_gets_no_history; test_barrier_history.py::test_the_provider_loop_carries_both_work_kinds; tests/test_barrier_current_run.py::test_the_provider_writes_history_for_a_current_run_only; tests/test_barrier_current_run.py::test_the_provider_deployed_work_list_uses_the_wall_clock` | 🟩 |
-| PROV-OUT-08 | One OHLCV request through the fetch path (feed and end rule, validation, the `PROV-OUT-09` guard) shared with the daily request, for exactly the qualifying tickers over a calendar window holding `barrier_history_sessions` sessions and ending on the run's as-of (`MarketData.window_end` read through `ANALYZED_BY` then `DERIVED_FROM`, one node per hop), whenever the provider reaches the run; no lineage ends on the fetch's UTC date, but an absent or unparseable stored `window_end` raises before any fetch and writes no history; one linked `BarrierHistory` with ≤ 760 bars and the count per ticker; dropped tickers named; stale ones marked; a failed fetch still writes a failed node. | happy + partial + fault + past as-of + resume + no lineage + broken date | `test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch; test_barrier_history_failures.py::test_a_dropped_ticker_carries_its_named_reason; test_newest_session_guard.py::test_a_real_history_day_never_drops_a_buy_from_its_barrier_history; test_barrier_history_failures.py::test_a_failed_fetch_still_writes_a_failed_node; test_barrier_history_failures.py::test_an_exception_in_the_fetch_path_still_writes_a_failed_node; test_barrier_history.py::test_the_history_passes_the_packs_vocabulary_guard; agents/forecaster/tests/test_barrier_route.py::test_a_failed_fetch_never_leaves_the_forecaster_waiting; test_barrier_window_as_of.py::test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock; test_barrier_window_as_of.py::test_the_as_of_is_read_by_edge_never_by_key; test_barrier_window_as_of.py::test_a_run_with_no_market_data_is_served_today; test_barrier_window_as_of.py::test_an_unreadable_window_end_fails_before_any_fetch; orchestration/tests/test_barrier_claim_as_of.py::test_a_past_runs_claim_is_stated_on_its_own_last_bar; orchestration/tests/test_barrier_claim_as_of.py::test_the_deployed_work_list_serves_the_runs_as_of; orchestration/tests/test_barrier_claim_as_of.py::test_a_resumed_analysis_uses_its_source_runs_as_of` | 🟩 |
+| PROV-TRG-04 | An `AnalystRun` with a buy carrying both barriers, or run while the book holds a name, and no `BarrierHistory` triggers the barrier history; with nothing held, sells, holds and a buy missing a barrier trigger nothing, and no recommendation set never does; the loop carries both work kinds. | trigger | `test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch; test_barrier_history.py::test_a_run_without_a_qualifying_buy_gets_no_history; test_barrier_history.py::test_the_provider_loop_carries_both_work_kinds; tests/test_barrier_current_run.py::test_the_provider_writes_history_for_a_current_run_only; tests/test_barrier_current_run.py::test_the_provider_deployed_work_list_uses_the_wall_clock; test_barrier_history_held.py::test_the_history_holds_the_buys_then_each_held_name_once; test_barrier_history_held.py::test_a_run_with_no_buy_gets_a_history_while_the_book_holds_a_name` | 🟩 |
+| PROV-OUT-08 | One OHLCV request through the fetch path (feed and end rule, validation, the `PROV-OUT-09` guard) shared with the daily request, for exactly the qualifying tickers (the barrier buys, then each held name, once each) over a calendar window holding `barrier_history_sessions` sessions and ending on the run's as-of (`MarketData.window_end` read through `ANALYZED_BY` then `DERIVED_FROM`, one node per hop), whenever the provider reaches the run; no lineage ends on the fetch's UTC date, but an absent or unparseable stored `window_end` raises before any fetch and writes no history; one linked `BarrierHistory` with ≤ 760 bars and the count per ticker; dropped tickers named; stale ones marked; a failed fetch still writes a failed node. | happy + partial + fault + past as-of + resume + no lineage + broken date | `test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch; test_barrier_history_failures.py::test_a_dropped_ticker_carries_its_named_reason; test_newest_session_guard.py::test_a_real_history_day_never_drops_a_buy_from_its_barrier_history; test_barrier_history_failures.py::test_a_failed_fetch_still_writes_a_failed_node; test_barrier_history_failures.py::test_an_exception_in_the_fetch_path_still_writes_a_failed_node; test_barrier_history.py::test_the_history_passes_the_packs_vocabulary_guard; agents/forecaster/tests/test_barrier_route.py::test_a_failed_fetch_never_leaves_the_forecaster_waiting; test_barrier_window_as_of.py::test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock; test_barrier_window_as_of.py::test_the_as_of_is_read_by_edge_never_by_key; test_barrier_window_as_of.py::test_a_run_with_no_market_data_is_served_today; test_barrier_window_as_of.py::test_an_unreadable_window_end_fails_before_any_fetch; orchestration/tests/test_barrier_claim_as_of.py::test_a_past_runs_claim_is_stated_on_its_own_last_bar; orchestration/tests/test_barrier_claim_as_of.py::test_the_deployed_work_list_serves_the_runs_as_of; orchestration/tests/test_barrier_claim_as_of.py::test_a_resumed_analysis_uses_its_source_runs_as_of; test_barrier_history_held.py::test_the_history_holds_the_buys_then_each_held_name_once` | 🟩 |
 | PROV-OUT-09 | The extreme-move guard judges each ticker's newest bar only, against the pooled moves of every ticker's bar on that same session; beyond `max_daily_move_sigma` σ the ticker is excluded, named in `anomalous_tickers`, a per-ticker partial degradation, never a whole-batch taint; fewer than two moves or no spread is not judged; an older bar is never re-judged; one guard for the daily request and the barrier history; a pool of n moves cannot exceed √(n−1) σ, so it excludes only on a session of more than `max_daily_move_sigma`² + 1 moves. | history day + newest bar + both paths + lagging ticker + abstain + ceiling | `test_newest_session_guard.py::test_a_real_old_extreme_day_keeps_the_name; test_newest_session_guard.py::test_a_bad_newest_bar_is_still_dropped_by_name; test_newest_session_guard.py::test_the_daily_ingest_keeps_a_name_with_a_real_crash_mid_window; test_newest_session_guard.py::test_a_real_history_day_never_drops_a_buy_from_its_barrier_history; test_newest_session_guard.py::test_a_lagging_ticker_is_judged_on_its_own_newest_session; test_newest_session_guard.py::test_a_session_of_one_move_abstains; test_newest_session_guard.py::test_a_session_of_65_names_or_fewer_cannot_pass_8_sigma; test_barrier_history_failures.py::test_a_dropped_ticker_carries_its_named_reason; test_provider_agent.py::test_integrity_anomaly_is_reported_without_crashing` | 🟩 |
 | PROV-OUT-03 | Exactly one of SUCCESS, DEGRADED, or FAULT is produced for every request; existing split rows do not prove the total/exclusive space. | total-space | _tbd_ | ⬜ |
 | PROV-NEV-02 | Provider must never score, rank, size, order, or decide. | boundary | _tbd_ | ⬜ |
diff --git a/docs/laws/INDEX.md b/docs/laws/INDEX.md
index 84b43d19..5227dc00 100644
--- a/docs/laws/INDEX.md
+++ b/docs/laws/INDEX.md
@@ -38,7 +38,7 @@ Each agent's law files live at `agents/<name>/laws/`:

 | Agent | `laws.md` | Green clauses | Notes |
 | --- | --- | --- | --- |
-| provider | ✅ LOCKED v1.10 (S266, DL-287) | 24 / 67 | S266 (DL-287) amends and re-proves `PROV-OUT-08`: barrier history ends on the run's as-of by lineage whenever the provider reaches it, missing lineage serves the fetch's UTC date, and a broken stored date fails before any fetch or history write (DRIFT-110); count unchanged; S255 (DL-269) amends and re-proves `PROV-OUT-02`: the regime records its four label thresholds; count unchanged; S251 amends `PROV-TRG-01` (every recorded data need, re-proven on graph-pull; DRIFT-082), `PROV-TRG-02` (the poll's key-and-edge bound, now green; DRIFT-086), `PROV-OUT-07` (served bars are raw; DRIFT-084) and narrows `PROV-OUT-04` (fetch time and fallback flag, now green; DRIFT-040); S249 adds and proves `PROV-TRG-05` (a `RunRequest`'s ingest serves the run's as-of whenever the provider reaches it; an unusable as-of is refused before any fetch; no run serves today; DRIFT-095); S243 adds and proves `PROV-OUT-09` (the extreme-move guard judges each ticker's newest session only; its √(n−1) ceiling stated) and amends `PROV-OUT-08`; S239 adds and proves `PROV-TRG-04` / `PROV-OUT-08` (the `BarrierHistory` per `AnalystRun`) and reconciles `PROV-TRG-02` with graph-pull; S238 adds and proves `PROV-OUT-07` (consolidated-tape volume, entitlement-respecting requests, loud refusal; DRIFT-080); DL-203 reconciles `PARAM` only; S213 adds FMP `^VIX` regime freshness evidence and proves `PROV-OUT-03` without adding clauses; S187 adds PARAM rows only; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
+| provider | ✅ LOCKED v1.11 (S286, DL-310) | 24 / 67 | S286 (DL-310) amends `PROV-TRG-01/02/04` and `PROV-OUT-08`: the barrier history also holds every held name; 24 / 67 unchanged. Before: S266 (DL-287) amends and re-proves `PROV-OUT-08`: barrier history ends on the run's as-of by lineage whenever the provider reaches it, missing lineage serves the fetch's UTC date, and a broken stored date fails before any fetch or history write (DRIFT-110); count unchanged; S255 (DL-269) amends and re-proves `PROV-OUT-02`: the regime records its four label thresholds; count unchanged; S251 amends `PROV-TRG-01` (every recorded data need, re-proven on graph-pull; DRIFT-082), `PROV-TRG-02` (the poll's key-and-edge bound, now green; DRIFT-086), `PROV-OUT-07` (served bars are raw; DRIFT-084) and narrows `PROV-OUT-04` (fetch time and fallback flag, now green; DRIFT-040); S249 adds and proves `PROV-TRG-05` (a `RunRequest`'s ingest serves the run's as-of whenever the provider reaches it; an unusable as-of is refused before any fetch; no run serves today; DRIFT-095); S243 adds and proves `PROV-OUT-09` (the extreme-move guard judges each ticker's newest session only; its √(n−1) ceiling stated) and amends `PROV-OUT-08`; S239 adds and proves `PROV-TRG-04` / `PROV-OUT-08` (the `BarrierHistory` per `AnalystRun`) and reconciles `PROV-TRG-02` with graph-pull; S238 adds and proves `PROV-OUT-07` (consolidated-tape volume, entitlement-respecting requests, loud refusal; DRIFT-080); DL-203 reconciles `PARAM` only; S213 adds FMP `^VIX` regime freshness evidence and proves `PROV-OUT-03` without adding clauses; S187 adds PARAM rows only; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | analyst | ✅ LOCKED v1.12 (S284, DL-308) | 31 / 54 | S284 (DL-308) adds and proves `ANLZ-OUT-11`: the lexicon sentiment pillar scores only headlines that name the ticker's company. S279 (DL-302) adds and proves `ANLZ-PERF-02`: the held-stop read shares one lazy Fill read across the book and retains each lineage width; no decision changes. S259 (DL-276) reconciles `PARAM` only: the bounds of `scaled_stop_atr_multiplier` follow the code, no clause changes; S255 (DL-269) adds and proves `ANLZ-OUT-10`: each scored recommendation records its constants and actual mean order; S253 adds and proves `ANLZ-IN-05` (a candidate under `required_history_bars` is scored; only fewer than `min_history_bars` rejects; DRIFT-096); S251 adds and proves `ANLZ-OUT-09` (the held-position stop check; DRIFT-074) and names the graph-pull trigger in `ANLZ-TRG-02` (DRIFT-086); DL-203 reconciles `PARAM` only; S211 adds and proves `ANLZ-OBS-06` for decision-time favourable-excursion target evidence and missing-estimate rejection; S205 rewrites `ANLZ-TYP-01` into required fields without moving the count; S198 declares and proves `ANLZ-OBS-05`; S156 citation check plus S186's `ANLZ-OBS-04`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | scanner | ✅ LOCKED v1.5 (S259, DL-276) | 18 / 41 | S259 (DL-276) reconciles `PARAM` only: the upper bound of `min_average_volume` follows the code, no clause changes; S251 names the graph-pull trigger in `SCAN-TRG-02` (DRIFT-085) and narrows `SCAN-TYP-01`'s version sentence (DRIFT-060); DL-203 reconciles `PARAM` only; S205 rewrites `SCAN-TYP-01` into required fields and closes DRIFT-047 without moving the count; S183's `SCAN-OUT-06`/`SCAN-OUT-07`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | portfolio_manager | ✅ LOCKED v1 (S70), amended **v1.12** (S259, DL-276) | 33 / 51 | S259 (DL-276) reconciles `PARAM` only: the bounds of six rows follow the code, no clause changes; S251 narrows `PM-OBS-01`/`PM-OUT-06`/`PM-STA-04` (no PM snapshot; DRIFT-039), `PM-OBS-04` (per candidate; DRIFT-065), uses emitted strings in `PM-OUT-03` (DRIFT-037), names graph-pull in `PM-TRG-02` (DRIFT-086), narrows `PM-TYP-03`'s version sentence (DRIFT-060); files DRIFT-098; S240 adds and proves `PM-IN-05`: held names weighed once per ticker at the run's own snapshot marks, a resumed run at the snapshot of the run it resumes (DRIFT-079 closed); DL-203 reconciles `PARAM` only; S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders applied weights; S211 adds and proves `PM-OBS-05`: reward-risk compares measured target evidence against stop risk and can reject measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows; S204 gives every clause a row and makes rowless clauses a hard gate |
@@ -46,7 +46,7 @@ Each agent's law files live at `agents/<name>/laws/`:
 | execution | ✅ LOCKED **v1.16** (S283, DL-306) | 45 / 70 | S283 (DL-306) adds and proves `EXEC-OBS-08` (no broker read is cut at a page limit; run-start reconciliation reads every order the graph waits on, by id where no listing shows it) and `EXEC-PERF-03` (a run-start broker read is bounded by the book), with PARAM row `broker_recent_order_days`. S280 (DL-303) amends and proves `EXEC-OUT-07` (an order the broker ended after filling part of it is a fill of that part, its rest told once) and adds and proves `EXEC-TYP-04` (`Fill.broker_filled_quantity`, read by every reader of an executed size); `EXEC-OBS-06` matches on the filled quantity. S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault; the stop plan shares one lazy Fill read; no decision changes. S258 (DL-276) reconciles `PARAM` only: the bounds of `slippage_bps`, `min_promotion_runs`, `min_approval_rate` and `alpaca_timeout` follow the code, no clause changes; S252 / DL-261: `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66. S251 adds and proves `EXEC-IDN-04` (the divergence-family Flag exception, `owns_graph` widened; DRIFT-094), names the contract's fields in `EXEC-OUT-01/02/04/05` (DRIFT-061) and narrows `EXEC-TYP-03`'s version sentence (DRIFT-060); S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode, `critical` only when it survived a run, whatever the ticker's history; S230 adds/proves `EXEC-OBS-06`: the broker stop is the PM-decided stop, read through the shared resolver, and a mismatched live stop is replaced in place with `replaced_at`/`replaces` markers; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; DL-203 reconciles `PARAM` only; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 adds/proves `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | monitor | ✅ LOCKED v1.4 (S279, DL-302) | 22 / 47 | S279 (DL-302) adds and proves `MON-PERF-03`: the end-of-run evaluation shares one lazy Fill read across the book and retains each decided width; no decision changes. S252 / DL-261: `MON-TRG-02` bounds both work kinds, sync from requests and their linked snapshot; DRIFT-097 corrected, 21 / 46 unchanged. S251 names the graph-pull triggers in `MON-TRG-02` (DRIFT-086) and files DRIFT-097 for the unbounded sync poll; S205 rewrites and proves `MON-TYP-01`; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
 | reporter | ✅ LOCKED v1.5 (S253, DL-262, DL-263) | 26 / 43 | S253 rewrites `RPT-OUT-02` (book counts from the broker's fills in the run's window, outcomes since the inception; DRIFT-099), amends `RPT-IN-01` and `RPT-NEV-03` (DRIFT-101), and adds and proves `RPT-IDM-04`; S251 names the run's own benchmark lineage in `RPT-OUT-07` (DRIFT-087) and the graph-pull trigger in `RPT-TRG-02` (DRIFT-086); v1.3 (DL-224) latest-per-date snapshot; S226 adds benchmark-relative `performance_metrics`, as-of bounded graph reads, contained performance failure, and backward-compatible snapshots; S205 rewrites `RPT-TYP-01`; S156 removed orphan `RPT-OBS-03`; S204 gives every clause a row and makes rowless clauses a hard gate |
-| forecaster | ✅ LOCKED v1.10 (S252, DL-261) | 25 / 52 | S252 / DL-261: `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged. S251 names the four legs (`FORE-IDN-01`), one node per prediction (`FORE-OBS-01`; DRIFT-081) and the shadow scorecards' subject (`FORE-IDM-03`; DRIFT-083); S243 amends and re-proves `FORE-FAIL-04` (a designed refusal is a `warning`, a missing input an `error`); S241 adds and proves `FORE-OUT-08`, `FORE-IDM-05`, `FORE-FAIL-05` (the settlement of each barrier claim and `barrier_scorecard`) and amends `FORE-IDN-02`/`TRG-01`/`OUT-03`; the S239 second follow-up (D10) re-words the barrier clauses for the provider-written history; the S239 follow-up amends `FORE-TRG-01`/`FORE-TRG-02` (graph-pull trigger; the deployed loop fires `forecast_barrier` only); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim); DL-203 reconciled `PARAM`; S205 proved `FORE-TYP-01`; counters are clauses proven / clauses declared |
+| forecaster | ✅ LOCKED v1.11 (S286, DL-310) | 28 / 55 | S286 / DL-310: a barrier claim on every held name, its live stop and declared target from the claim's close (`FORE-OUT-09`), held claims scored apart (`FORE-OUT-10`), one history read per run and open-claims-only settlement (`FORE-PERF-04`); 25 / 52 → 28 / 55. Before: S252 / DL-261: `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged. S251 names the four legs (`FORE-IDN-01`), one node per prediction (`FORE-OBS-01`; DRIFT-081) and the shadow scorecards' subject (`FORE-IDM-03`; DRIFT-083); S243 amends and re-proves `FORE-FAIL-04` (a designed refusal is a `warning`, a missing input an `error`); S241 adds and proves `FORE-OUT-08`, `FORE-IDM-05`, `FORE-FAIL-05` (the settlement of each barrier claim and `barrier_scorecard`) and amends `FORE-IDN-02`/`TRG-01`/`OUT-03`; the S239 second follow-up (D10) re-words the barrier clauses for the provider-written history; the S239 follow-up amends `FORE-TRG-01`/`FORE-TRG-02` (graph-pull trigger; the deployed loop fires `forecast_barrier` only); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim); DL-203 reconciled `PARAM`; S205 proved `FORE-TYP-01`; counters are clauses proven / clauses declared |
 | operator | ✅ LOCKED v1.10 (S269, DL-292) | 20 / 51 | S269 (DL-292) rewords and re-proves `OPR-FAIL-02`: only text, a number or a boolean is a value; `null`, lists and objects are omitted from required and optional parameters, so missing required values are refused with the existing sentence and audit, while scalar text and blank-text behavior are unchanged; DRIFT-112 corrected; no clause added; before that S268 (DL-290) rewords and re-proves `OPR-FAIL-02`: an intent of no known family, or lacking a parameter its family requires under any accepted name, is refused before its audit, which reads `refused`, and no `Intent` is written; the prompt states each family's parameter names; DRIFT-109 corrected; no clause added; before that S265 (DL-286) rewords and re-proves `OPR-FAIL-01`: failed requests are audited on both capabilities, one operator fault and one plain reason, no grammar or error text in graph; malformed JSON is a fault-free refusal; DRIFT-107/108 corrected; no clause added; before that S264 (DL-285) re-proves `OPR-STA-03` for vendor stop reasons and billed counts on both reply paths and adds/proves `OPR-FAIL-04` for audited, fault-free cut-offs with one sentence and explicit grammar preserved; DRIFT-106 corrected; before that S263 (DL-284) amends and re-proves `OPR-DEP-01` for provider effort resolution and pre-call model-family refusal; PARAM effort and CAP reconciled; before that S262 (DL-282) amends and re-proves `OPR-DEP-01` for the selected vendor, model resolution and no fallback; PARAM reconciled; before that S256 (DL-272) rewrites and proves `OPR-IDM-02`: duplicate commands share the audit and intent, but every model call has its own ledger row; DRIFT-104 corrected; S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; counters are clauses proven / clauses declared |
 | supervisor | ✅ LOCKED v1.3 (S251, DL-260) | 23 / 48 | S251 declares the divergence-family exception in `SUP-IDN-02` (DRIFT-094) and proves `SUP-OBS-02` (DRIFT-076); v1.2 (DL-225) `last_successful_run`; S205 rewrites and proves `SUP-TYP-01`; S179 proves append-only `FaultResolution` retirement (`SUP-OBS-03`); counters are clauses proven / clauses declared |
 | curator | ✅ LOCKED v1.1 (S205) | 23 / 47 | S205 rewrites and proves `CUR-TYP-01`; counters are clauses proven / clauses declared |
diff --git a/docs/laws/ledger.md b/docs/laws/ledger.md
index e798fa5f..02edbb14 100644
--- a/docs/laws/ledger.md
+++ b/docs/laws/ledger.md
@@ -35,10 +35,10 @@ and torn down to zero. Historical Neo4j rows remain valid evidence for the pre-S

 | Agent | Laws authored? | Clauses green / total | Status |
 | --- | --- | --- | --- |
-| provider | ✅ v1.10 (LOCKED) | 24 / 67 | 🟨 partial — **24 of 67 clauses proven** after S266 (DL-287) amends and re-proves `PROV-OUT-08`: the barrier history ends on the run's as-of by lineage whenever the provider reaches it, missing lineage serves the fetch's UTC date, and a broken stored date raises before any fetch or history write (DRIFT-110); count unchanged; before that S255 (DL-269) amends and re-proves `PROV-OUT-02`: the regime records its four label thresholds; count unchanged; before that S251 (DL-260) amends four clauses to the code: `PROV-TRG-01` names every recorded data need (a bus request, an unconsumed `RunRequest`, an `AnalystRun`'s qualifying buys) and is re-proven with no bus event (DRIFT-082); `PROV-TRG-02` states the poll's key-and-edge bound and turns green (DRIFT-086); `PROV-OUT-07` says served bars are raw (DRIFT-084); `PROV-OUT-04` is narrowed to fetch time and the fallback flag and turns green (DRIFT-040, the vendor gap is work-queue 105); before that S249 (DL-256) adds and proves `PROV-TRG-05`: an ingest a `RunRequest` triggers serves that run's as-of whenever the provider reaches it (window, coverage check, regime, news and earnings anchors), an unusable as-of is refused before any fetch, and an ingest with no run serves today (DRIFT-095); before that S243 (DL-247) adds and proves `PROV-OUT-09`: the extreme-move guard judges each ticker's newest session only, against that session's cross-section, so a real extreme day in a name's history never drops it (DRIFT-088), and states the guard's √(n−1) ceiling (DRIFT-090, CORRECTED: the barrier path leans on the daily request's guard, DL-247 D4); `PROV-OUT-08` amended and re-proven; before that S239 (DL-241 D10) adds and proves `PROV-TRG-04` / `PROV-OUT-08` (the `BarrierHistory` per `AnalystRun`, one batched fetch, dropped tickers named, a failed fetch still written); before that S238 adds and proves `PROV-OUT-07`: a bar's volume is the consolidated tape's (the Alpaca feed defaults to SIP), a SIP request never ends inside the plan's 15-minute recent-data window, and a refusal fails loud with no IEX fallback (DRIFT-080); S213 sharpens and proves `PROV-OUT-03` for FMP `^VIX` freshness without adding clauses; S187 added PARAM rows only; S204 gives every clause a row and promotes missing rows to a hard gate; S169-sweep demoted `PROV-OUT-04` |
+| provider | ✅ v1.11 (LOCKED) | 24 / 67 | 🟨 partial — **24 of 67 clauses proven** after S286 (DL-310) amends `PROV-TRG-04` and `PROV-OUT-08` (the barrier history holds every held name) and S266 (DL-287) amends and re-proves `PROV-OUT-08`: the barrier history ends on the run's as-of by lineage whenever the provider reaches it, missing lineage serves the fetch's UTC date, and a broken stored date raises before any fetch or history write (DRIFT-110); count unchanged; before that S255 (DL-269) amends and re-proves `PROV-OUT-02`: the regime records its four label thresholds; count unchanged; before that S251 (DL-260) amends four clauses to the code: `PROV-TRG-01` names every recorded data need (a bus request, an unconsumed `RunRequest`, an `AnalystRun`'s qualifying buys) and is re-proven with no bus event (DRIFT-082); `PROV-TRG-02` states the poll's key-and-edge bound and turns green (DRIFT-086); `PROV-OUT-07` says served bars are raw (DRIFT-084); `PROV-OUT-04` is narrowed to fetch time and the fallback flag and turns green (DRIFT-040, the vendor gap is work-queue 105); before that S249 (DL-256) adds and proves `PROV-TRG-05`: an ingest a `RunRequest` triggers serves that run's as-of whenever the provider reaches it (window, coverage check, regime, news and earnings anchors), an unusable as-of is refused before any fetch, and an ingest with no run serves today (DRIFT-095); before that S243 (DL-247) adds and proves `PROV-OUT-09`: the extreme-move guard judges each ticker's newest session only, against that session's cross-section, so a real extreme day in a name's history never drops it (DRIFT-088), and states the guard's √(n−1) ceiling (DRIFT-090, CORRECTED: the barrier path leans on the daily request's guard, DL-247 D4); `PROV-OUT-08` amended and re-proven; before that S239 (DL-241 D10) adds and proves `PROV-TRG-04` / `PROV-OUT-08` (the `BarrierHistory` per `AnalystRun`, one batched fetch, dropped tickers named, a failed fetch still written); before that S238 adds and proves `PROV-OUT-07`: a bar's volume is the consolidated tape's (the Alpaca feed defaults to SIP), a SIP request never ends inside the plan's 15-minute recent-data window, and a refusal fails loud with no IEX fallback (DRIFT-080); S213 sharpens and proves `PROV-OUT-03` for FMP `^VIX` freshness without adding clauses; S187 added PARAM rows only; S204 gives every clause a row and promotes missing rows to a hard gate; S169-sweep demoted `PROV-OUT-04` |
 | scanner | ✅ v1.5 (LOCKED) | 18 / 41 | 🟨 partial — **18 of 41 clauses proven**: S259 (DL-276) reconciles `PARAM` only (the upper bound of `min_average_volume` follows the code; no clause moves); S251 (DL-260) names the graph-pull trigger in `SCAN-TRG-02` (a `MarketData` with no `SCANNED_BY` edge, found by key and edge; DRIFT-085) and narrows `SCAN-TYP-01`'s version sentence (DRIFT-060), count unchanged; S205 rewrites `SCAN-TYP-01` into required fields and closes DRIFT-047 without moving the count; S183 added and proved `SCAN-OUT-06`/`SCAN-OUT-07`; S204 gives every clause a row and promotes missing rows to a hard gate |
 | analyst | ✅ v1.12 (LOCKED) | 31 / 54 | 🟨 partial — **31 of 54 clauses proven** after S284 (DL-308) adds and proves `ANLZ-OUT-11`: the lexicon sentiment pillar scores only headlines that name the ticker's company, no pillar below two; before that S279 (DL-302) adds and proves `ANLZ-PERF-02`: the held-stop read shares one lazy Fill read across the book and retains each lineage width, no decision changes; before that S259 (DL-276) reconciles `PARAM` only (the bounds of `scaled_stop_atr_multiplier` follow the code; no clause moves) and S255 (DL-269) adds and proves `ANLZ-OUT-10`: each scored recommendation records its constants and actual mean order; before that S253 (DL-263) adds and proves `ANLZ-IN-05`: a candidate under `required_history_bars` is scored on the indicators its bars allow, each missing core indicator visible as `<metric>_missing_bars`, and only fewer than `min_history_bars` rejects (DRIFT-096); before that S251 (DL-260) adds and proves `ANLZ-OUT-09`: a held position's stop check reads the shared stop-width resolver, a close at or below the decided stop is a forced `stop` sell, a live broker stop owns the exit, an unreadable book is a fault (DRIFT-074); `ANLZ-TRG-02` names the graph-pull trigger (DRIFT-086); before that S211 adds and proves `ANLZ-OBS-06`: decision-time favourable-excursion target evidence is measured from prior settled windows, serialized, and missing evidence rejects instead of falling back to a constant target; S205 rewrites `ANLZ-TYP-01` into required fields without moving the count; S198 adds and proves `ANLZ-OBS-05`; S186 adds and proves `ANLZ-OBS-04`; S204 gives every clause a row and promotes missing rows to a hard gate · S152 declared 3 new clauses (43→46) · S169-sweep demoted `ANLZ-OBS-01` |
-| forecaster | ✅ v1.10 (LOCKED) | 25 / 52 | 🟨 partial — **25 of 52 clauses proven** after S252 (DL-261): `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged; v1.9 (S251, DL-260) names the four legs in `FORE-IDN-01`, one recorded node per prediction in `FORE-OBS-01` (DRIFT-081) and the three shadow scorecards in `FORE-IDM-03` (DRIFT-083), all still gray, count unchanged; v1.8 (S243, DL-247) amends and re-proves `FORE-FAIL-04`: a designed "no claim" records a `warning`, a missing or broken input an `error` (DRIFT-089), count unchanged; after S241 (DL-243) adds and proves `FORE-OUT-08` (each claim settled once by EXP-018's rule from a provider-written `MarketData`; `barrier_scorecard` over EXP-018's fixed climatology), `FORE-IDM-05` (settled once, one pass per run) and `FORE-FAIL-05` (void with a named reason, never a false outcome), and amends and re-proves `FORE-IDN-02`/`TRG-01`/`OUT-03`; v1.6 (S239, DL-241 D10) re-words `FORE-IN-07`/`TRG-01`/`OUT-07`/`IDM-04`/`FAIL-04`/`NEV-04` for the provider-written history, count unchanged; before that the S239 follow-up amends and re-proves `FORE-TRG-01`/`FORE-TRG-02` (the deployed graph-pull loop fires `forecast_barrier` only; count unchanged); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim), each proven; 27 have a gray row |
+| forecaster | ✅ v1.11 (LOCKED) | 28 / 55 | 🟨 partial — **28 of 55 clauses proven** after S286 (DL-310): a barrier claim on every held name (`FORE-OUT-09`, `FORE-OUT-10`, `FORE-PERF-04` new and green); before that, 25 / 52 after S252 (DL-261): `FORE-TRG-01` bounds both current-run finders before props are read; local calls stay unbounded; 25 / 52 unchanged; v1.9 (S251, DL-260) names the four legs in `FORE-IDN-01`, one recorded node per prediction in `FORE-OBS-01` (DRIFT-081) and the three shadow scorecards in `FORE-IDM-03` (DRIFT-083), all still gray, count unchanged; v1.8 (S243, DL-247) amends and re-proves `FORE-FAIL-04`: a designed "no claim" records a `warning`, a missing or broken input an `error` (DRIFT-089), count unchanged; after S241 (DL-243) adds and proves `FORE-OUT-08` (each claim settled once by EXP-018's rule from a provider-written `MarketData`; `barrier_scorecard` over EXP-018's fixed climatology), `FORE-IDM-05` (settled once, one pass per run) and `FORE-FAIL-05` (void with a named reason, never a false outcome), and amends and re-proves `FORE-IDN-02`/`TRG-01`/`OUT-03`; v1.6 (S239, DL-241 D10) re-words `FORE-IN-07`/`TRG-01`/`OUT-07`/`IDM-04`/`FAIL-04`/`NEV-04` for the provider-written history, count unchanged; before that the S239 follow-up amends and re-proves `FORE-TRG-01`/`FORE-TRG-02` (the deployed graph-pull loop fires `forecast_barrier` only; count unchanged); S239 amends `FORE-IDN-02` and adds `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-FAIL-04` (the barrier claim), each proven; 27 have a gray row |
 | portfolio_manager | ✅ v1 (LOCKED, amended **v1.12**) | 33 / 51 | 🟨 partial — **33 of 51 clauses proven** after S259 (DL-276) reconciles `PARAM` only (the bounds of six rows follow the code; no clause moves) and S251 (DL-260) narrows `PM-OBS-01`/`PM-OUT-06`/`PM-STA-04` to what `PMRun` and `OrderIntentResult` carry (the `portfolio_state_snapshot` promise withdrawn, DRIFT-039; `PM-STA-04` now green), makes `PM-OBS-04` per candidate (DRIFT-065), uses the emitted reason strings in `PM-OUT-03` (DRIFT-037), names the graph-pull trigger in `PM-TRG-02` (DRIFT-086) and narrows `PM-TYP-03`'s version sentence (DRIFT-060); DRIFT-098 filed for `PM-OUT-01`/`PM-TYP-03`; before that S240 adds and proves `PM-IN-05`: a run weighs each held ticker once at its own snapshot mark (adoption mark, then cost, as fallbacks) and a resumed run reads the snapshot of the run it resumes, closing DRIFT-079; `PM-IDN-01` stays gray (current-state conjunct proven, the whole-purpose boundary proof still owed); S220 amends and re-proves `PM-NEV-08` / `PM-OBS-03`: correlated issuers contribute on the ADR-0030 `0.50..0.90` ramp and gate detail renders the applied weights; S211 adds and proves `PM-OBS-05`: reward-risk now compares measured target evidence against stop risk, varies across measured profiles, and rejects measured upside below measured downside at the configured floor; S210 amends `PM-NEV-06`/`PM-NEV-08`/`PM-NEV-09` so concentration ratios use deployed capital and deployment-floor evidence is explicit without moving the count; S208 declares and proves `PM-OBS-04`; S197 declared and proved `PM-OBS-03`; S184 made PM-NEV-07/08/09 green and closed the v1.3 widened PM-NEV-06 and PM-TYP-03 rows |
 | deliberator | ✅ v1.18 (LOCKED) | 35 / 66 | S277 (DL-289 amendment 4) adds and proves DLIB-FAIL-05, refusal-only sticky switching with one model-attributed row per attempt; re-proves DLIB-FAIL-01, DLIB-OUT-02 (always-written llm_switches) and DLIB-DEP-05 (handed-over fallback construction). S276 (DL-289 amendment 1) adds and proves DLIB-DEP-05 and DLIB-NEV-11; amended DLIB-OUT-02 re-proven for the models that answered; effort defaults to empty. 🟨 partial — **35 of 66 clauses proven** after S257 (DL-274) reconciles `PARAM` only (the output cap 16,384, the peer wait up to 300 seconds; no clause moves) and S256 (DL-272) adds and proves `DLIB-IDM-04` (settle-on-take and visible reply faults), `DLIB-OBS-08` (every completion is its own row), and proves spend attribution `DLIB-OBS-02`; S255 (DL-269) adds and proves `DLIB-OUT-08`: recorded arithmetic reproduces before rendering, with first-failure withholding and old-packet parity; DRIFT-102/103 corrected; before that S254 / ADR-0032: `DLIB-NEV-10` proves prompt libraries use only the agent's own client; before that S252 (DL-261): `DLIB-TRG-01` now proven for the key-and-edge candidate bound and order-property filter, 27 / 59; before that S246 (DL-252) adds and proves `DLIB-OUT-06` (each defender and challenger turn records its guided reasoning, readings then gaps before the argument, exactly as written or why it could not be read, and an unreadable one never fails the turn or the order) and `DLIB-OUT-07` (each debated order's record carries its decision and evidence packet), and amends `DLIB-TYP-01` (`DebateTurnRecord.reasoning`, `.reasoning_error`); before that S245 (DL-251) adds and proves `DLIB-NEV-09`: every fact the challenger and judge prompts state about our code is pinned by a test that reads that code, the false calendar-day staleness fact and the stale name-correlation example are gone (DRIFT-092), and the champions rebuild byte for byte from pack-side sources; before that S222 moves its vendor adapters to `kernel/` and proves `DLIB-SEC-02` with a key-containment sentinel; S214 narrows `vetoed_tickers` to `overturn` verdicts only, routes unreadable judge answers through loud fail-open, and proves `DLIB-OUT-04`; S206 adds and proves `DLIB-NEV-08`: rendered debate-context verdicts name their enforcing check and agent, while descriptive stop-target regime evidence has no verdict; S205 rewrites and proves `DLIB-TYP-01`; S200 adds `DLIB-OBS-07` and promotes `DLIB-IDM-02`; S199 adds `DLIB-OBS-05`/`DLIB-OBS-06`; S172 proves concurrent-order record order and pending-reply handling; S194 adds `DLIB-OBS-04`; S189 added stop-reason audit evidence; S167 proves queryable fail-open causes |
 | execution | ✅ v1.16 (LOCKED) | 45 / 70 | 🟨 partial — **45 of 70 clauses proven** after S283 (DL-306) adds and proves `EXEC-OBS-08` (no broker read is cut at a page limit; run-start reconciliation reads every order the graph waits on, by id where no listing shows it) and `EXEC-PERF-03` (a run-start broker read is bounded by the book: open orders, the recent window, the waiting Fills), with PARAM row `broker_recent_order_days`; before that S280 (DL-303) amends and proves `EXEC-OUT-07` (a partly filled ended order is a fill of its part, its rest told once) and adds and proves `EXEC-TYP-04` (`Fill.broker_filled_quantity`, read by every reader of an executed size), `EXEC-OBS-06` matching on the filled quantity; before that S279 (DL-302) adds and proves `EXEC-PERF-02`: the drop sweep reads each label once, sees written drops and contains one failed-read fault, and the stop plan shares one lazy Fill read, no decision changes; before that S258 (DL-276) reconciles `PARAM` only (the bounds of four rows follow the code; no clause moves) and S252 (DL-261): `EXEC-TRG-07` bounds sync requests; new proven `EXEC-TRG-08` names graph-pull submit and its candidate/grace rule; DRIFT-100 corrected, 40 / 66; before that S251 (DL-260) adds and proves `EXEC-IDN-04`: execution writes divergence-family `Flag`/`FlagResolution` nodes and no others, both labels now in `owns_graph` as the one declared shared pair (DRIFT-094); `EXEC-OUT-01`/`-02`/`-04`/`-05` name the contract's fields (DRIFT-061); `EXEC-TYP-03`'s version sentence (DRIFT-060); before that S248 adds/proves `EXEC-OBS-07`: a broker-position divergence is flagged per episode (`warn` at first sight under a subject naming the first-sight snapshot, `critical` only if still present at the next run-start reconciliation, a new episode at `warn` whatever the ticker's history, one unresolved Flag per live divergence); S230 adds/proves `EXEC-OBS-06`: the broker stop's width comes through the shared stop-width resolver (PM lineage first, fallback only without it) and a live stop resting off its decided price is replaced in place, never cancelled and re-placed; S227 adds/proves `EXEC-NEV-07`: degraded `RunRequest`s hold buys without deliberation wait while exits and protective stops continue; S209 amends `EXEC-OBS-05` so the stale-order sweep compares stop identity, not liveness views, without moving the count; S205 rewrites `EXEC-TYP-03` into required fields and records DRIFT-060/DRIFT-061; S190 added/proved `EXEC-OBS-05`, the missing `EXEC-OBS-03` liveness limb, and `EXEC-STA-05`; S204 gives every clause a row and promotes missing rows to a hard gate |
diff --git a/tests/poll_reference.py b/tests/poll_reference.py
index c1c406f2..92c5314f 100644
--- a/tests/poll_reference.py
+++ b/tests/poll_reference.py
@@ -50,11 +50,11 @@ def reporter(graph: GraphStore) -> list[Node]:


 def barrier(graph: GraphStore, now: datetime) -> list[Node]:
-    """Current AnalystRuns with a qualifying buy and no BarrierHistory."""
+    """Current AnalystRuns with a qualifying buy or held name and no BarrierHistory."""
     return [
         node
         for node in _unprocessed(graph, "AnalystRun", "BARRIER_HISTORY_BY")
-        if is_current_run(node.props, now) and _qualifying_tickers(node)
+        if is_current_run(node.props, now) and _qualifying_tickers(graph, node)
     ]


```
