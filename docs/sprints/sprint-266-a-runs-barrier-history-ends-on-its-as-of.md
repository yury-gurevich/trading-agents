<!-- Agent: planning | Role: sprint handover -->
# Sprint 266 — a run's barrier history ends on the run's as-of, so a barrier claim is stated on the run's own last bar whenever the provider reaches the run

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-266-a-runs-barrier-history-ends-on-its-as-of`
**Status:** BUILT
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-287](../design-log.md) (this sprint's six decisions, made and measured) · [DL-255](../design-log.md) / [DL-256](../design-log.md) (part one, the ingest) · [work-queue 103](../work-queue.md), part two · DRIFT-110

> **Why this bump kind.** No new capability: the provider's law already says the barrier history's
> newest session is the one the daily request judged, and for a run the provider reaches after its
> as-of the code fetches later sessions. A fix, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the one amendment this spec names (`PROV-OUT-08`). A clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: provider **`TRG`**, **`OUT`**, **`STA`**; forecaster **`IN`**, **`OUT`**, **`IDM`**, **`NEV`** (read only: no forecaster file changes).

### The rule

1. **Before writing code**, read every law file in the map below, whole.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Read the law-cycle answer below.** It is already answered; build it as written.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No file in `contracts/` changes, and none may. Yes, the provider's guarantee for the barrier
history grows** (where its window ends), so one law cycle is owed in this unit of work. **No clause
is added: `PROV-OUT-08` is amended**, so the provider's count stays where it is.

| Book | From | What the cycle owes |
| --- | --- | --- |
| `agents/provider/laws/laws.md` | LOCKED v1.9 | **`PROV-OUT-08` amended** by the two insertions under *The clause* below. Changelog line, version up. No other clause changes |
| `agents/provider/laws/test-plan.md` | 24 / 67 | `PROV-OUT-08`'s row gains B1 to B4 and A1 to A3 as citations, and its text says where the window ends. The footer stays 24 / 67 |
| `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` | provider 24 / 67, v1.9 | The provider's line, in both, names this sprint, DL-287 and the new version; the count does not move |
| `docs/laws/drift-register.md` | DRIFT-110 is OPEN | Its status cell becomes CORRECTED, naming this sprint and the tests |

**No forecaster law, test-plan row or file changes.** `FORE-OUT-07` already says a claim's `as_of`
is its history's last bar; this sprint makes that bar the run's own.

🪤 **The law gate does not check each citation.** Measured 2026-10-10: a row that cites one live
test naming the clause passes with a dead citation beside it. List every test `PROV-OUT-08`'s row
cites, with its file, in the handback.

#### The clause

`PROV-OUT-08` keeps every word it has. Two insertions and one note:

1. After *"over a calendar window holding at least `barrier_history_sessions` sessions"* insert:

   > **that ends on the run's as-of** (the `window_end` of the `MarketData` the run was scanned
   > from, read through the run's lineage `AnalystRun ←ANALYZED_BY— ScanRun —DERIVED_FROM→
   > MarketData`: one node, never a listing of them; `PROV-TRG-05`), **whenever the provider reaches
   > the run**

2. After the sentence that ends *"and a ticker the daily request excluded never becomes a buy."*
   insert:

   > A run with no such `MarketData` has no as-of and is served as an ingest no run triggered is:
   > its window ends on the UTC date of the fetch (`PROV-TRG-05`). A `MarketData` whose
   > `window_end` is absent or not a date is a broken node, not a run with no as-of: the work fails
   > before any fetch and no node is written.

3. The trailing note becomes *(DL-241 D10; DRIFT-090, DL-247 D4; DRIFT-110, S266, DL-287.)*

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/provider/barrier_history.py`, new `agents/provider/barrier_window.py` | `agents/provider/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `PROV-OUT-08` (the one request, the node, a failed fetch still writes it), `PROV-TRG-04` (which runs; the deployed loop counts a current run only), `PROV-TRG-05` (a run's as-of; an ingest no run triggered serves today), `PROV-OUT-09` (the guard this path leans on), `PROV-STA-04` |
| nothing in `agents/forecaster/` | `agents/forecaster/laws/laws.md` + `test-plan.md` | `FORE-OUT-07` (`as_of` is the last bar's date, `entry_close` its close), `FORE-IDM-04` (the claim is keyed by model, ticker and last bar; a different claim under the same key is refused), `FORE-TRG-01`, `FORE-NEV-02` (shadow, never gates) |
| nothing in `contracts/` | `contracts/barrier_history.py`, `contracts/provider.py` | `BarrierHistory.window_end` is a required date; `MarketData` nodes carry `window_end` as an ISO date string |

⚠️ **The one invariant this sprint must not break: no decision path changes.** The fidelity count
is running ([DL-237](../design-log.md)); a change to what the scanner, the analyst, the portfolio
manager, execution, the monitor or the provider's ingest reads or decides restarts it. The barrier
history is a side branch only the forecaster's shadow claim reads. If the build needs a change
outside `agents/provider/barrier_history.py`, the new `agents/provider/barrier_window.py`, tests and
the law files named above, **stop and report**.

---

## Goal

At merge, the window of a run's `BarrierHistory` ends on the run's as-of, the same day its
`MarketData` window ends on, whatever day the provider reaches the run. So the history's newest bar
is the run's own last bar, and the forecaster's claim is stated as of that bar and at its close: the
bar the buy's stop and target were computed on.

## Why (context)

S249 made a run's ingest follow the run's as-of (`PROV-TRG-05`) and left nine wall-clock date reads
in place as work-queue 103's second part, with *"which of them run inside a graph-pull run is not
measured"*. Measured now, on the three paths a run can take: **a fleet run reaches one of the nine
as a clock read, the barrier history's** (`agents/provider/barrier_history.py:94`).

That one matters. A run the provider reaches after its as-of (a test run placed for an earlier
session, or a run resumed from the analyst stage on a later day) gets a `MarketData` ending on its
as-of and a `BarrierHistory` ending on the day of the fetch. The forecaster then states the claim
on the history's last bar: a later session's date and close, for a stop and a target the analyst
computed on the as-of's bars. The claim is keyed by that later date (`FORE-IDM-04`), so it can also
take the key of the claim that night's scheduled run would state, and the first claim stands.

The live ledger holds no such claim yet (below). The first barrier claims begin to settle about
2026-10-12 (S241's F4), so the ledger is about to be read.

### Measured, 2026-10-11 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Wall-clock date reads left by S249 | **9**: `agents/provider/barrier_history.py:94`; `agents/scanner/agent.py:182`; `agents/analyst/agent.py:128`; `agents/portfolio_manager/agent.py:119`; `agents/monitor/provider_client.py:63`; `agents/forecaster/agent.py:164`, `price_signal.py:79`, `factor_signal.py:78`, `settlement_pass.py:138` | *[measured]* `grep -rnE "datetime\.now\([^)]*\)\.date\(\)" agents` excluding tests: 11 hits, less the ingest's two that S249 settled (`ingest.py:76`, an ingest no run triggered; `poll.py:160`, the refusal of an as-of after today) |
| Which of the nine a **fleet-shaped** run reaches (each container entrypoint's own find/process pair, the forecaster on its own bus with the deployed legs) | **2**: `barrier_window` (returns today) and `_pass_date` (returns the run's `created_at` date, read from the stamp) | *[measured, run, no `.env`]* a spy on each of the nine, a run placed for an as-of three days back, in memory. Planner's script `wq103b_clock_reads.py`, output `before_main.txt` |
| Which the **in-process pass** (`cascade_once`) reaches | the same two, plus the forecaster's news window and return window (both return today) | *[measured, run]* same script. The factor window is not reached: no factor is enabled by default |
| Which the **served agents on a `run.trigger` event** reach | the scanner's, the analyst's, the portfolio manager's and the monitor's (all return today) | *[measured, run]* same script. The event carries a run id and a universe and **no as-of** |
| What a fleet-shaped run for an as-of three days back stores | `MarketData.window_end` and `RegimeContext.window_end`: the as-of. `BarrierHistory.window_end`: **today**; its newest bar: **today's**; each `BarrierForecast`: `as_of` **today**, `entry_close` **today's close** (101.7538 where the as-of's close is 101.7995) | *[measured, run]* same script, both graph-pull paths alike |
| The same run on the prototype | `BarrierHistory.window_end`, its newest bar and each claim's `as_of`: the as-of; `entry_close` 101.7995; nothing else in the output differs | *[measured, run]* `after_prototype.txt`, diffed against `before_main.txt` |
| Who drives the served agents for a run | nothing outside tests | *[measured, grep]* `Dispatcher` is constructed only in tests; no module outside tests sends a request to the scanner, the analyst, the portfolio manager or the monitor; `surfaces/context.py` binds them and calls the operator, the supervisor and the reporter |
| What the scanner's law says of its served window | it is calculated from `datetime.now(UTC)` on each call | *[measured, read]* `SCAN-STA-03` |
| Who fires the forecaster's three advisory legs | the in-process pass and an RPC caller, never the deployed loop | *[measured, read and run]* `FORE-TRG-01`; `agents/forecaster/poll.py::DEPLOYED_CAPABILITIES` is the barrier leg alone |
| Who places a past as-of on the in-process pass | nothing outside tests | *[measured, read]* `scripts/run_local.py` calls `place_run_request` with no as-of and has no `--as-of` |
| `_pass_date` and the clock | it reads the clock only when the run's `created_at` cannot be parsed, and records the date on the pass node | *[measured, read]* `settlement_pass.py:129-138`; DL-243 D3 chose the creation date on purpose |
| What the provider's law already assumes | *"its newest session is the one the daily request judged"* | *[measured, read]* `PROV-OUT-08`, its guard sentence. False for a run reached after its as-of |
| Live `BarrierHistory` nodes whose window ends off their run's as-of | **0 of 8**; 0 hold a bar later than the as-of; 0 have no `MarketData` lineage | *[measured, Neon, read-only]* `neon_barrier_ledger.py`: each history joined to the `MarketData` its run was scanned from |
| Live `BarrierForecast` claims dated after their run's as-of | **0 of 28** | *[measured, Neon]* same script. One is dated a day before (TGT, `verify-2026-10-01-s248-a`): that run predates S249, so its `MarketData` window followed the clock |
| What the lineage read downloads | the run's `ScanRun` (mean 46 KB) and `MarketData` (**mean 1.85 MB, largest 2.78 MB**) | *[measured, Neon]* `octet_length(props::text)` over 89 and 88 nodes. *[ASSUMED, not measured]* that the read costs exactly these two nodes on Postgres; F1b can read it |
| Existing tests the prototype breaks | **1 of 4,646**: `test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch`, whose clock pin patches a name that moved | *[measured, run]* the full suite on the prototype; with that one test's two lines edited, **4,655 passed, 8 skipped, 100.00 %** |
| The planned tests against the unchanged code | A1, A2 and A3 fail on behaviour: `'2026-10-10' == '2026-10-07'` | *[measured, run]* `proto_tests_red_on_main_code.txt` |
| The planner's breaks against the planned tests | **14 red of 14**, none survived, none failed to apply | *[measured, run]* `planner_mutations.py` on the prototype with the prototype's tests |
| A resumed run keeps the lineage | the cloned `ScanRun` is linked `DERIVED_FROM` the cloned `MarketData`, which copies `window_end` | *[measured, read and run]* `orchestration/resume.py:110-111`, `:126`; A3 on the prototype |
| Staleness in the barrier fetch | counted from the window's end, not from the clock | *[measured, read]* `agents/provider/domain/integrity.py:39` |

The planner's scripts and outputs are outside the repo (OneDrive `trading-agents-data/wq103b-2026-10-11/`).
You do not need them: the Test plan's A1 is the reproduction, and the Appendix holds the prototype.

---

## Scope — and what is deliberately NOT here

1. **The failing tests first.** A1 and A2 of the Test plan, red on the unchanged code on behaviour
   (the history ends today, not on the as-of), pasted in the Closeout.
2. **The run's as-of, read through its lineage.** A new module `agents/provider/barrier_window.py`
   holds `run_as_of(graph, analyst_run)` (the `window_end` of the `MarketData` the run's `ScanRun`
   was derived from, or `None` when the run has no such lineage) and `barrier_window(sessions,
   as_of=None)`, moved from `barrier_history.py` with its two constants, ending on `as_of` when one
   is given and on today's UTC date when none is.
3. **The barrier history uses it.** `write_barrier_history` builds its window with the run's as-of.
   Nothing else in `barrier_history.py` changes: the one request, the node, the failure path.
4. **The one existing test whose clock pin moved** (E1), and the rest of the Test plan.
5. **The law cycle** named above: `PROV-OUT-08` amended, v1.10, the test-plan row, both rollup
   lines, DRIFT-110 CORRECTED.

### Out of scope (do NOT build this sprint)

- **The other eight reads.** Each stays as it is, by decision ([DL-287](../design-log.md) D5):
  - *The scanner's, the analyst's, the portfolio manager's and the monitor's* run only when a served
    agent answers a request that carries no as-of. `SCAN-STA-03` says so for the scanner. No
    container and no script drives them for a run. They are decision-path agents: not touched.
  - *The forecaster's news, return and factor windows* run only in the in-process pass and for an
    RPC caller; their request (`FORE-IN-01`, `FORE-IN-02`) carries no as-of and the deployed loop
    never fires them. **Named, not built:** before any of the three is deployed, or run for a past
    as-of, its window must take the run's as-of, which is a field on `ForecastRequest` and a
    forecaster law cycle.
  - *The settlement pass's date* is the run's creation date by DL-243 D3; the clock is its fallback
    for a run with no readable stamp.
- **Whether a test run should state a claim at all.** A test run's claims sit in the same ledger as
  a scheduled run's; that is so today and is not this sprint's.
- **The current-run rule** (`PROV-TRG-04`, 24 hours from the run's `created_at`). Unchanged.
- **A partial bar.** A run whose as-of is today, placed while the session is open, reads that day's
  unfinished bar in its ingest and here alike. Not this sprint's.
- **`RunTrigger.as_of`**, which `Dispatcher.execute_run` does not publish. Tests only.
- **No new label, property, env key or tunable. No contract change. No ADR reversal.**

### The road not taken (LAW-06)

- **Stamp the as-of on the `AnalystRun`.** Rejected: it changes the analyst's write path (a
  decision-path agent, while the fidelity count runs) and adds a graph property, which makes the
  deploy a full `up`; the 88 runs already written would not carry it.
- **Read the run id out of a key** and fetch the small `RegimeContext` or `RunRequest` by it.
  Rejected: a resume clone's `MarketData` is keyed `resume-link:…`, so the parse fails on exactly
  the runs this fix is for.
- **A props-light read in the graph port.** Rejected here: a port change is an ADR-sized decision,
  for 1.9 MB a night.
- **Refuse a run with no lineage** (a failed node with a named reason). Rejected: `BarrierHistory`
  requires a window's two dates, so the node would need an invented window or a contract change,
  and only a hand-built run can be one: the graph-pull analyst recommends nothing without a
  `MarketData`.
- **Skip a run reached after its as-of** (no history, so no claim). Rejected: the claim on the
  run's own bars is the honest one, and a re-run for a past session that states the scheduled run's
  claim again merges into it, which is what a replay should show.
- **Fix all nine reads.** Rejected: seven are not reached by a fleet run, four of those sit in
  decision-path agents, and three need a contract field for legs nothing deployed fires.

---

## The design decisions — made, and recorded in DL-287

**They are made. Build them as written; if one cannot be built, stop and report.**

1. **D1 — the as-of is the `window_end` of the `MarketData` the run was scanned from**, found by
   edge: the run's `ANALYZED_BY` ancestor (its `ScanRun`), then that node's `DERIVED_FROM`
   descendant. The same walk the portfolio manager and the forecaster's settlement make.
2. **D2 — a run with no such lineage has no as-of and its window ends today** (the UTC date at the
   call), as an ingest no run triggered does under `PROV-TRG-05`.
3. **D3 — a `MarketData` whose `window_end` is absent or not a date fails the work** before any
   fetch: `KeyError` or `ValueError`, raised by the read, outside the fetch's fault boundary. No
   node is written. It is not served today. The value is parsed with `date.fromisoformat(str(…))`:
   it is the provider's own stored datum, not an operator's input, so DL-256 D2's exact-form rule
   is not repeated here.
4. **D4 — one new module, `agents/provider/barrier_window.py`**, holds the lineage read and the
   window helper with its two constants. `barrier_history.py` is at 191 of 200 lines; it falls to
   179.
5. **D5 — the other eight reads stay**, each for the reason under *Out of scope*.
6. **D6 — `PROV-OUT-08` is amended, no clause is added**; DRIFT-110 records the gap.

**Named consequences, told to the operator:**

- A run reached after its as-of now states its claim under the as-of's date. If the scheduled run
  for that session already stated that ticker's claim with the same barriers, the two merge and the
  first `created_at` and `history_ref` stand; with different barriers the later one is refused with
  a fault and the first stands (`FORE-IDM-04`, unchanged).
- A claim stated for an as-of ten or more sessions back can be settled by the next run's pass. The
  barrier scorecard orders claims by `as_of` and does not tell such a claim from a forward one.
- The provider reads one `ScanRun` and one `MarketData` more for each run that holds a qualifying
  buy: about 1.9 MB on such a night.

🪤 **`DL-287` is taken by this sprint's entry on `main`.** If the build forces a decision, add an
amendment under DL-287; do not take a new number.

---

## Blast radius — measured 2026-10-11

| What | Detail |
| --- | --- |
| Files changed | `agents/provider/barrier_history.py` (191 lines, to 179); new `agents/provider/barrier_window.py` (61 in the prototype); `agents/provider/tests/test_barrier_history.py` (156, two lines); two new test files; `agents/provider/laws/laws.md`, `test-plan.md`; `docs/laws/ledger.md`, `INDEX.md`, `drift-register.md`; this file and its README row |
| Agents affected | the provider alone. It imports no other agent |
| Contract change? | no |
| Graph vocabulary change? | no: it reads `MarketData.window_end`, which every scanned `MarketData` carries, and writes the `BarrierHistory` properties it writes today |
| New env keys / tunables | none |
| Decision path? | **none changes.** The scope command in the handback checklist prints nothing for the scanner, the analyst, the portfolio manager, execution, the monitor, the provider's ingest and domain, the contracts and the packs |
| Deploy implication | image-only retag, with the next one; it restarts nothing the fidelity count reads. Until then the fleet's provider still ends the window today |
| Rollback | retag to the tag before it. Nothing beyond the retag: no schema, no pack, no setting. `BarrierHistory` and `BarrierForecast` nodes written meanwhile stay, and the older code reads them as its own |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Read DL-287** in `docs/design-log.md`, and DL-255, DL-256, DL-241 (D3, D10, D11) and DL-243 (D3).
3. **Plant the failing tests first** (A1 and A2) and watch them fail on behaviour, not on an import.
   Paste the red output.
4. **Implement** Scope 2 and 3. The Appendix holds the measured prototype.
5. **Edit the one existing test** (E1), and write the rest of the plan.
6. **The law cycle**: the amended clause, the test-plan row, the docstring citations, both rollup
   lines, DRIFT-110.
7. **Prove the guards can fail (DL-70)**: break the implementation, watch each guard go red, restore.
8. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

New provider tests go in `agents/provider/tests/test_barrier_window_as_of.py`; the end-to-end ones
in `orchestration/tests/test_barrier_claim_as_of.py`. Every one cites `PROV-OUT-08`.

**Fixtures the plan needs (each was needed by the prototype):**

- *A run with lineage, by hand:* `barrier_history_helpers.analyst_run(...)`, a `ScanRun` node, a
  `MarketData` node with `{"window_end": "<ISO date>"}`, and two edges:
  `graph.add_edge(scan, run, "ANALYZED_BY")` and `graph.add_edge(scan, market, "DERIVED_FROM")`.
- *A clock that fails the test if read:* a `datetime` subclass whose `now` raises, set with
  `monkeypatch.setattr(barrier_window, "datetime", …)`. `barrier_history.py` keeps its own
  `datetime` for the node's `created_at`, so that stamp still works.
- *A run for a past as-of, end to end:* `orchestration/tests/helpers.entry_bars()` with every bar's
  date moved back three days (`bar.model_copy(update={"bar_date": bar.bar_date - LAG})`), served by
  a `ReboundingDataSource` subclass; `place_run_request(..., as_of=TODAY - LAG)`; three years of
  bars ending **today** from `agents/forecaster/tests/barrier_helpers.barrier_bars(ticker, 800,
  end=TODAY)` for the barrier request; `ForecasterAgent(..., barrier_fitter=FakeGarchFitter(ACCEPTED))`.
- 🪤 *The long-history source must honour the window's end.* `test_forecaster_stage.py`'s
  `_LongHistorySource` returns every long bar whatever window is asked; copied as it is, the newest
  bar is today's on any code and A1 proves nothing. Filter `window.start <= bar_date <= window.end`.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A past run's claim is stated on the run's own last bar | The in-process pass (`cascade_once`) over a run placed for an as-of three days back; the source holds three later days | One `MarketData` with `window_end` the as-of; one `BarrierHistory` with `window_end` the as-of and each ticker's newest bar dated the as-of; at least one `BarrierForecast`, each with `as_of` the as-of and `entry_close` the long series' close on the as-of |
| A2 | The deployed work list serves the run's as-of | The same run taken through sync, ingest, scan and analysis by each stage's own find/process pair, then `provider_poll.find_current_work` and `process_work_item` | One `BarrierHistory`, `window_end` the as-of, each ticker's newest bar the as-of's |
| A3 | A resumed analysis claims on its source run's as-of | The same run analysed, then `resume_run(graph, source_run_id=…, resume_from="analyst")`, the analyst's pair again, then the provider's deployed work list | Two `AnalystRun`s, two `BarrierHistory` nodes, both with `window_end` the as-of |
| B1 | 🎯 A run's barrier history ends on the run's as-of, and the clock is not read | A hand-built run with lineage to a `MarketData` whose `window_end` is three days back; 800 bars ending today; the clock that fails if read | The one request's window ends on the as-of and is 1,125 days long; the node's `window_end` is the as-of; the newest bar kept is the as-of's; the source did hold later bars |
| B2 | The as-of is read by edge, never by key | Two runs, the second's `ScanRun` and `MarketData` keyed as a resume clone's (`resume-link:…`), with different `window_end` values | `run_as_of` returns each run's own |
| B3 | A run with no `MarketData` is served today | Two cases: a run with no `ScanRun`; a run whose `ScanRun` is derived from nothing | `run_as_of` is `None`; the request's window ends on the clock's UTC date at the call; the node records that end |
| B4 | 🪤 An unreadable `window_end` fails before any fetch | Two cases: a `MarketData` with no `window_end` (`KeyError`); one whose `window_end` is not a date (`ValueError`) | The call raises; the source was asked nothing; no `BarrierHistory` exists |
| E1 | *(existing, edited)* `test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch` | Its clock pin patches `barrier_window.datetime`, where the clock read now lives | Everything it asserts today, unchanged: a hand-built run has no lineage, so its window ends on the pinned clock's date |

**E1 is the only existing test that may change, and only in those two lines** (the import and the
`setattr`). The prototype broke exactly that one of 4,646.

---

## Success factors

- [x] A run reached after its as-of writes a `BarrierHistory` whose `window_end` and newest bar are
      the as-of's, on the in-process pass and on the provider's deployed work list (A1, A2).
- [x] Each claim of such a run carries the as-of as its `as_of` and that day's close as its
      `entry_close` (A1).
- [x] A resumed analysis reads its source run's as-of through the cloned lineage (A3).
- [x] The clock is not read for a run that has an as-of (B1).
- [x] A run with no `MarketData` lineage is served as today (B3, E1); a `MarketData` with no
      readable `window_end` fails the work before any fetch (B4).
- [x] No decision path changes: the scope command prints nothing.
- [x] No file in `agents/forecaster/`, `contracts/`, `kernel/` or `orchestration/` outside
      `orchestration/tests/` changes.
- [x] Exactly one existing test edited, in two lines (E1).
- [x] The law cycle done: `PROV-OUT-08` amended as written, v1.10, changelog, the test-plan row,
      both rollup lines, DRIFT-110 CORRECTED; the provider's count stays 24 / 67.
- [x] Every new guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage; any step the sandbox cannot run named NOT RUN.
      Verified failing: exit 2 at the offline dependency audit. All 4,655 tests pass with
      100.00 % coverage; dependency audit is NOT RUN offline, and both remaining secrets
      checks pass when run separately. See Closeout for the commands and output.

---

## Traps

🪤 **A test that passes on the unchanged code proves nothing.** With a source that ignores the
window's end, or a run whose as-of is today, every assertion in A1 holds before the fix. The as-of
must be in the past and the source must hold, and be able to serve, later bars.
🪤 **A red on an import is not the red this sprint asks for.** The provider's new test file imports
a module that does not exist yet; plant A1 and A2 first, which import nothing new.
🪤 **`mypy` cannot infer `run_once` over a tuple of mixed find/process pairs.** Call it once per
stage.
🪤 **A moved name breaks a `monkeypatch`.** Any test that patches `barrier_history.datetime` to pin
the window's end must patch `barrier_window.datetime`. One does today (E1).
🪤 **`date.fromisoformat` accepts the compact form `20261007` on this Python.** D3 does not refuse
it, on purpose; do not add a strictness test for it.
🪤 **`orchestration/tests/test_barrier_claim_as_of.py` was 190 lines in the prototype.** If yours
grows, move its fixtures to a helper module rather than pass 200.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `agents/provider/barrier_history.py` **191**,
  `agents/provider/tests/test_barrier_history.py` **156**,
  `agents/provider/tests/barrier_history_helpers.py` **124**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers. This sprint adds none: the two window constants move unchanged.
- Faults, not silent failure — `kernel.fault_boundary`. The fetch's boundary stays where it is.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- **Do not touch `pyproject.toml` or `uv.lock`.** The planner bumps the version at merge.
- Secrets never through the worktree — a worktree has **no `.env`**. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. Review the diff against the checklist; re-measure (the scope command; `wq103b_clock_reads.py` on
   the built code against `after_prototype.txt`; the planner's 14 breaks against the builder's
   tests; each test `PROV-OUT-08`'s row cites, resolved by hand); merge `main` in; PATCH bump,
   `uv lock`; Windows `make ci`; push; **`make gate-ran` from `../ta-s266`**, the printed SHA
   checked against `git rev-parse HEAD`; CodeQL set-diff against the open alerts of S265's branch;
   fast-forward `main`; tag.
2. **F1a, at no cost, from the main checkout on the merged code:** `wq103b_clock_reads.py` prints,
   on both graph-pull paths, the history's end, its newest bar and each claim's `as_of` on the
   run's as-of, and everything else as `before_main.txt`.
3. **F1b, at no cost, the live market source, an in-memory graph, nothing written to the live
   graph:** the merged provider is given a run for a past session that a scheduled run held a
   barrier history for (`sched-2026-10-08`), a day or more late. Its `BarrierHistory` must end on
   that session and hold, ticker for ticker, the bars the scheduled run's history holds on the live
   graph (read-only); a control with the clock's window shows a later bar was there to take.
4. Deploy with the next retag; no decision path differs, so the fidelity count stands.
   **Not proven by any of these:** a past-dated run or an analyst-stage resume on the deployed fleet.

---

## Handover — paste this to Codex

```text
Sprint 266 — a run's barrier history ends on the run's as-of, so a barrier claim is stated on the
run's own last bar whenever the provider reaches the run.
Spec: docs/sprints/sprint-266-a-runs-barrier-history-ends-on-its-as-of.md (read ALL of it, then
CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s266, on branch
sprint-266-a-runs-barrier-history-ends-on-its-as-of, cut from main, with its venv synced to the
lock. Work only in that worktree, never in the main checkout and never on main. You have no .env
and no network: every proof is a unit test on an in-memory graph with a fake source. `uv run` is
safe; never run a bare `uv sync`. Do not touch pyproject.toml or uv.lock, and say so: the planner
bumps the version at merge. Do not push and do not merge: commit on the branch and hand back. Do
not edit docs/STATE.md, docs/work-queue.md or docs/design-log.md (one exception: an amendment under
DL-287 if the build forces a decision). If a make ci step cannot run in your sandbox (the
dependency audit needs the network), do not bypass it silently: name the step as NOT RUN in the
handback.

This handover is complete: nobody will send you follow-up messages. Two tiers:
- A wrong line number, count, path, test name or clause number whose intent is plain from the
  spec's Scope and Success factors is NOT a reason to stop: follow the intent, record the
  correction in Return notes, continue. The same holds if a gate wants a rollup line or a test-plan
  row worded differently from the spec: do what the gate accepts and say so.
- STOP and report, without improvising, when: the build needs a change to any production file
  other than agents/provider/barrier_history.py and the new agents/provider/barrier_window.py; to
  anything under contracts/, kernel/, surfaces/, agents/forecaster/, agents/scanner/,
  agents/analyst/, agents/portfolio_manager/, agents/execution/, agents/monitor/ or
  agents/provider/domain/; to agents/provider/ingest.py, ingest_chunked.py, poll.py, agent.py or
  settings.py; to any orchestration file outside orchestration/tests/; an EXISTING test other than
  E1 has to be edited, or E1 needs more than its import line and its setattr line (the planner's
  prototype broke exactly that one of 4,646); a law you read contradicts the spec; or a decision
  D1-D6 cannot be built as written.

What and why: for each AnalystRun holding a buy with a stop and a target, the provider fetches
about three years of daily bars (a BarrierHistory) and the forecaster states an advisory claim on
the history's last bar. The history's window ends on the wall clock's date. A run the provider
reaches after its as-of (a test run placed for an earlier session, or a run resumed from the
analyst stage on a later day) therefore gets a MarketData ending on its as-of and a BarrierHistory
ending today, and its claim is dated and priced on a later session than the bars its stop and
target came from. You make the history's window end on the run's as-of, read through the run's
lineage (AnalystRun <-ANALYZED_BY- ScanRun -DERIVED_FROM-> MarketData, its window_end). You
unit-test it. No decision path changes: the barrier history is a side branch only the forecaster's
shadow claim reads.

MUST RULE before any code: read, whole, agents/provider/laws/laws.md and
agents/forecaster/laws/laws.md (each with its test-plan.md), docs/laws/conventions.md,
docs/laws/drift-register.md, agents/provider/barrier_history.py, agents/forecaster/settling_bars.py
(the same lineage walk, in another agent: do not import it), orchestration/resume.py, and DL-287,
DL-255, DL-256, DL-241 (D3, D10, D11) and DL-243 (D3) in docs/design-log.md. Fill the Law reading
record first.
Law-cycle answer: YES for provider, and NO new clause: PROV-OUT-08 is amended by the two insertions
the spec gives under "The clause", changelog, version v1.9 -> v1.10; the count stays 24 / 67.
PROV-OUT-08's test-plan row gains citations. NO forecaster law changes. NO contracts/ file changes.

Order (the spec's Steps): laws -> plant A1 and A2, watch them fail on behaviour (the history ends
today, not on the as-of; not on an import), paste the red -> implement (the Appendix holds the
measured prototype) -> edit E1's two lines -> the remaining tests -> the law cycle and DRIFT-110 ->
break and restore every guard -> make ci to a file.

Build (decisions D1-D6 are made; build them as written):
1. agents/provider/barrier_window.py (new): run_as_of(graph, analyst_run) -> date | None, the
   window_end of the MarketData the run's ScanRun was derived from, by edge (ancestors over
   ANALYZED_BY, then descendants over DERIVED_FROM, depth 1 each), None when either node is absent;
   and barrier_window(sessions, as_of=None), moved from barrier_history.py with _DAYS_PER_SESSION
   and _WINDOW_MARGIN_DAYS unchanged, ending on as_of, or on today's UTC date when as_of is None.
2. agents/provider/barrier_history.py: write_barrier_history builds its window with
   barrier_window(sessions, run_as_of(agent._graph, node)). The read sits OUTSIDE the fetch's fault
   boundary, so an unreadable window_end raises and nothing is fetched or written. Nothing else in
   the module changes.
3. The one existing test (E1), the new tests (A1-A3, B1-B4), the law cycle.

DO NOT: fall back to today when a MarketData exists but its window_end cannot be read; catch the
KeyError or ValueError; find the MarketData by key or by parsing a run id; list MarketData nodes;
read RunRequest or RegimeContext; stamp anything on the AnalystRun; change the current-run rule,
the window's length, the one request, the node's properties or the failure path; change any other
of the eight wall-clock reads the spec lists as out of scope; import anything from
agents/forecaster in production code; add a ForecastRequest field; add a law clause; edit an
existing test other than E1; let a test depend on a .env or on the day of the week; pin a version
number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The red output of A1 and A2 pasted, from before the implementation, each failing on behaviour.
 3. Test plan results: one row for each of A1-A3, B1-B4 and E1, with file and status.
 4. Every guard's break-and-restore stated, one line per guard. At least these, each of which the
    planner broke on the prototype and saw red:
    barrier_history.py: the as-of never passed to the window.
    barrier_window.py: the window ignoring the as-of it is given; the window ending the day after
    the as-of; the lineage read always finding no as-of; the ScanRun looked for among the run's
    descendants; the MarketData looked for among the scan's ancestors; any edge from the ScanRun
    taken for its MarketData; the window's start read as the as-of; a MarketData with no
    window_end served today; a window_end that is not a date served today; a run with no ScanRun
    raising; a ScanRun with no MarketData raising; the window's margin dropped; the window's
    length counted in sessions.
 5. This prints nothing, and you say so (run it against the commit the branch was cut from if main
    has moved; name which you used):
    git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/monitor agents/execution agents/forecaster agents/deliberator agents/operator agents/master agents/supervisor agents/reporter agents/curator agents/researcher agents/provider/domain agents/provider/ingest.py agents/provider/ingest_chunked.py agents/provider/poll.py agents/provider/agent.py agents/provider/settings.py agents/provider/entrypoint.py contracts kernel surfaces infra scripts orchestration/packs orchestration/history_window.py orchestration/local_pipeline.py orchestration/resume.py orchestration/start.py pyproject.toml uv.lock docs/STATE.md docs/work-queue.md docs/design-log.md
 6. `git diff main -- agents/provider/barrier_history.py agents/provider/barrier_window.py` pasted
    whole.
 7. `git diff main -- agents/provider/tests/test_barrier_history.py` pasted whole, and one line
    saying no other existing test changed.
 8. The provider law book's old and new version, PROV-OUT-08 quoted as written, its test-plan row
    quoted, DRIFT-110's status cell quoted, and both rollup lines.
 9. The law gate's output (scripts/check_law_coverage.py), exit code stated, AND every test
    PROV-OUT-08's row cites listed with its file: the gate does not check each citation.
10. make ci output file named, exit code stated, every NOT RUN step named with its reason.
11. Module line counts for every touched or new Python module; Status BUILT here and in the README
    row (the status cell leads with BUILT).
12. Anything in the build you are unsure of.
State anything not met as "not done" or "verified failing". Never write a Result for work not done.
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
| Provider barrier history and window | `agents/provider/laws/laws.md` (whole, LOCKED v1.9) and `test-plan.md` (whole) | `PROV-OUT-08`, `PROV-TRG-04`, `PROV-TRG-05`, `PROV-OUT-09`, `PROV-STA-04` | No: D1-D6 are compatible. Read the as-of before the fetch boundary; missing lineage and broken stored dates remain distinct. These binding rows are green. |
| Forecaster claim and lineage (read only) | `agents/forecaster/laws/laws.md` (whole, LOCKED v1.10) and `test-plan.md` (whole); `agents/forecaster/settling_bars.py` (whole) | `FORE-IN-07`, `FORE-OUT-07`, `FORE-IDM-04`, `FORE-TRG-01`, `FORE-NEV-02`, `FORE-NEV-04` | No: the claim already uses the history's last bar and stays advisory. No forecaster changes. `FORE-IN-02`, `FORE-IDM-03`, `FORE-OBS-01` remain gray; this sprint does not claim those guarantees. |
| Payload and resumed lineage (read only) | `contracts/barrier_history.py`; relevant `contracts/provider.py` payload/property declarations; `agents/provider/barrier_history.py` (whole); `orchestration/resume.py` (whole) | `PROV-OUT-08`, `PROV-TRG-05`, `FORE-IN-07` | No: existing required history dates and copied `MarketData.window_end` support the edge walk without a property or contract change. |
| Governance and recorded decisions | `CLAUDE.md`, `AGENTS.md`, docs indexes; `docs/laws/conventions.md` and `drift-register.md` (whole); DL-287, DL-255, DL-256, DL-241 (including D3/D10/D11), DL-243 (including D3) | conventions sections 2-4, 7, 7a, 9; LAW-02, LAW-06 | No: build DL-287 as written. Older DL-255's barrier deferral is resolved by DL-287. The sprint's explicit exclusions override general tracker, version, and push instructions. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes for the provider's stronger window-end guarantee; no `contracts/` change and no new clause. Owed after implementation: the exact `PROV-OUT-08` insertions, v1.9 to v1.10, changelog, cited row, both rollups, DRIFT-110 CORRECTED; 24 / 67 unchanged. No forecaster law cycle.

**Contradictions found between a law and this spec:** none. `AGENTS.md` still says merge requires instruction while `CLAUDE.md` removes that permission requirement; reported here under its source-of-truth rule. The explicit sprint instruction forbids merging in either case.

**Laws found silent where a decision was needed:** the barrier window end and broken stored-date handling are already recorded as DRIFT-110 and decided in DL-287 D1-D3/D6; no additional silence found.

**Clauses that were ⬜ and are now proven:** none; the amendment re-proves the existing green `PROV-OUT-08`, leaving 24 / 67.

**Pre-code reading gate:** recorded on 2026-10-11 in `C:\Users\yury_\Downloads\project\ta-s266`, branch `sprint-266-a-runs-barrier-history-ends-on-its-as-of`, clean starting HEAD/base `b991d39ef28156d10feef6d2bad9b9dca272be4a` (also local `main` and `origin/main` at reading). `.env` absent. No Python changes preceded this record. `docs/STATE.md`, `docs/work-queue.md`, `docs/design-log.md`, `pyproject.toml`, and `uv.lock` are excluded by the handover.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a_past_runs_claim_is_stated_on_its_own_last_bar` | `orchestration/tests/test_barrier_claim_as_of.py` | PASS | `PROV-OUT-08 / FORE-OUT-07` |
| A2 | `test_the_deployed_work_list_serves_the_runs_as_of` | `orchestration/tests/test_barrier_claim_as_of.py` | PASS | `PROV-OUT-08 / PROV-TRG-04` |
| A3 | `test_a_resumed_analysis_uses_its_source_runs_as_of` | `orchestration/tests/test_barrier_claim_as_of.py` | PASS | `PROV-OUT-08` |
| B1 | `test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock` | `agents/provider/tests/test_barrier_window_as_of.py` | PASS | `PROV-OUT-08 / PROV-TRG-05` |
| B2 | `test_the_as_of_is_read_by_edge_never_by_key` | `agents/provider/tests/test_barrier_window_as_of.py` | PASS | `PROV-OUT-08` |
| B3 | `test_a_run_with_no_market_data_is_served_today` | `agents/provider/tests/test_barrier_window_as_of.py` | PASS (2 cases) | `PROV-OUT-08 / PROV-TRG-05` |
| B4 | `test_an_unreadable_window_end_fails_before_any_fetch` | `agents/provider/tests/test_barrier_window_as_of.py` | PASS (2 cases) | `PROV-OUT-08` |
| E1 | `test_only_buys_with_both_barriers_get_a_history_from_one_fetch` | `agents/provider/tests/test_barrier_history.py` | PASS | `PROV-TRG-04 / PROV-OUT-08 / PROV-TRG-01` |

**Tests added beyond the plan:** none. B3 and B4 each have the two planned parameter cases, so A1-A3/B1-B4 add nine cases. The new `orchestration/tests/barrier_as_of_helpers.py` keeps fixtures separate and every Python module under 200 lines.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s266`, branch `sprint-266-a-runs-barrier-history-ends-on-its-as-of`; `.env` absent (checked before tests). Unit fixtures use an in-memory graph and fake sources/fitter. `uv run --frozen` with `UV_OFFLINE=1`; no bare `uv sync`.

**Result:** A1/A2 prove that a run reached three days after its as-of writes a history ending on the as-of, with that day's newest bar; A1 proves each claim uses that date and close. A3 proves the resumed lineage preserves the end. B1-B4 prove the unchanged 1,125-day window, the edge-only read, the UTC fallback only for missing lineage, and an exception before any fetch/history write for a broken stored date. All 14 cited test functions resolve and cite `PROV-OUT-08`; their 16 parameter cases pass after all 14 guards have been restored.

**Files changed:**

- `agents/provider/barrier_history.py`
- `agents/provider/barrier_window.py`
- `agents/provider/laws/laws.md`
- `agents/provider/laws/test-plan.md`
- `agents/provider/tests/test_barrier_history.py`
- `agents/provider/tests/test_barrier_window_as_of.py`
- `docs/laws/INDEX.md`
- `docs/laws/drift-register.md`
- `docs/laws/ledger.md`
- `docs/sprints/README.md`
- `docs/sprints/sprint-266-a-runs-barrier-history-ends-on-its-as-of.md`
- `orchestration/tests/barrier_as_of_helpers.py`
- `orchestration/tests/test_barrier_claim_as_of.py`

**Design decisions:** recorded as [`DL-287`](../design-log.md) — built as written; no amendment.

**Proof — the red run first:**

```text
Command (UV_OFFLINE=1, PYTHONUTF8=1):
uv run --frozen pytest --no-cov -vv orchestration/tests/test_barrier_claim_as_of.py
Captured before any production implementation in red-a1-a2-concise.txt.
Law reading was already committed as 54b240a1.

============================= test session starts =============================
collecting ... collected 2 items

orchestration/tests/test_barrier_claim_as_of.py::test_a_past_runs_claim_is_stated_on_its_own_last_bar FAILED [ 50%]
orchestration/tests/test_barrier_claim_as_of.py::test_the_deployed_work_list_serves_the_runs_as_of FAILED [100%]

================================== FAILURES ===================================
____________ test_a_past_runs_claim_is_stated_on_its_own_last_bar _____________
orchestration\tests\test_barrier_claim_as_of.py:45: in test_a_past_runs_claim_is_stated_on_its_own_last_bar
    assert end == AS_OF
E   assert datetime.date(2026, 10, 10) == datetime.date(2026, 10, 7)
______________ test_the_deployed_work_list_serves_the_runs_as_of ______________
orchestration\tests\test_barrier_claim_as_of.py:73: in test_the_deployed_work_list_serves_the_runs_as_of
    assert end == AS_OF
E   assert datetime.date(2026, 10, 10) == datetime.date(2026, 10, 7)
=========================== short test summary info ===========================
FAILED orchestration/tests/test_barrier_claim_as_of.py::test_a_past_runs_claim_is_stated_on_its_own_last_bar - assert datetime.date(2026, 10, 10) == datetime.date(2026, 10, 7)
FAILED orchestration/tests/test_barrier_claim_as_of.py::test_the_deployed_work_list_serves_the_runs_as_of - assert datetime.date(2026, 10, 10) == datetime.date(2026, 10, 7)
============================== 2 failed in 4.69s ==============================
RED_EXIT=1
```

**Proof — the green run:**

```text
============================= test session starts =============================
collecting ... collected 16 items

agents/provider/tests/test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch PASSED [  6%]
agents/provider/tests/test_barrier_history_failures.py::test_a_dropped_ticker_carries_its_named_reason PASSED [ 12%]
agents/provider/tests/test_newest_session_guard.py::test_a_real_history_day_never_drops_a_buy_from_its_barrier_history PASSED [ 18%]
agents/provider/tests/test_barrier_history_failures.py::test_a_failed_fetch_still_writes_a_failed_node PASSED [ 25%]
agents/provider/tests/test_barrier_history_failures.py::test_an_exception_in_the_fetch_path_still_writes_a_failed_node PASSED [ 31%]
agents/provider/tests/test_barrier_history.py::test_the_history_passes_the_packs_vocabulary_guard PASSED [ 37%]
agents/forecaster/tests/test_barrier_route.py::test_a_failed_fetch_never_leaves_the_forecaster_waiting PASSED [ 43%]
agents/provider/tests/test_barrier_window_as_of.py::test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock PASSED [ 50%]
agents/provider/tests/test_barrier_window_as_of.py::test_the_as_of_is_read_by_edge_never_by_key PASSED [ 56%]
agents/provider/tests/test_barrier_window_as_of.py::test_a_run_with_no_market_data_is_served_today[no-scan] PASSED [ 62%]
agents/provider/tests/test_barrier_window_as_of.py::test_a_run_with_no_market_data_is_served_today[no-market] PASSED [ 68%]
agents/provider/tests/test_barrier_window_as_of.py::test_an_unreadable_window_end_fails_before_any_fetch[absent] PASSED [ 75%]
agents/provider/tests/test_barrier_window_as_of.py::test_an_unreadable_window_end_fails_before_any_fetch[not-a-date] PASSED [ 81%]
orchestration/tests/test_barrier_claim_as_of.py::test_a_past_runs_claim_is_stated_on_its_own_last_bar PASSED [ 87%]
orchestration/tests/test_barrier_claim_as_of.py::test_the_deployed_work_list_serves_the_runs_as_of PASSED [ 93%]
orchestration/tests/test_barrier_claim_as_of.py::test_a_resumed_analysis_uses_its_source_runs_as_of PASSED [100%]

============================= 16 passed in 3.27s ==============================
CITATION_TEST_EXIT=0
```

**Guards planted:** each mutation was applied separately, its selected test failed with exit 1, then both production files were restored to their exact original bytes before the next mutation. No collection/import failures. The full cited-test green run above was taken after restoration.

| Guard | File | Deliberate break | Failing test | Result / restore |
| --- | --- | --- | --- | --- |
| G01 | `agents/provider/barrier_history.py` | as-of never passed to the window | `test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock` | RED, exit 1; exact bytes restored |
| G02 | `agents/provider/barrier_window.py` | window ignores the given as-of | `test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock` | RED, exit 1; exact bytes restored |
| G03 | `agents/provider/barrier_window.py` | window ends the day after the as-of | `test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock` | RED, exit 1; exact bytes restored |
| G04 | `agents/provider/barrier_window.py` | lineage always finds no as-of | `test_the_as_of_is_read_by_edge_never_by_key` | RED, exit 1; exact bytes restored |
| G05 | `agents/provider/barrier_window.py` | ScanRun sought among the run's descendants | `test_the_as_of_is_read_by_edge_never_by_key` | RED, exit 1; exact bytes restored |
| G06 | `agents/provider/barrier_window.py` | MarketData sought among the scan's ancestors | `test_the_as_of_is_read_by_edge_never_by_key` | RED, exit 1; exact bytes restored |
| G07 | `agents/provider/barrier_window.py` | any edge from the ScanRun taken for its MarketData | `test_the_as_of_is_read_by_edge_never_by_key` | RED, exit 1; exact bytes restored |
| G08 | `agents/provider/barrier_window.py` | window start read as the as-of | `test_the_as_of_is_read_by_edge_never_by_key` | RED, exit 1; exact bytes restored |
| G09 | `agents/provider/barrier_window.py` | MarketData with no window_end served today | `test_an_unreadable_window_end_fails_before_any_fetch[absent]` | RED, exit 1; exact bytes restored |
| G10 | `agents/provider/barrier_window.py` | non-date window_end served today | `test_an_unreadable_window_end_fails_before_any_fetch[not-a-date]` | RED, exit 1; exact bytes restored |
| G11 | `agents/provider/barrier_window.py` | a run with no ScanRun raises | `test_a_run_with_no_market_data_is_served_today[no-scan]` | RED, exit 1; exact bytes restored |
| G12 | `agents/provider/barrier_window.py` | a ScanRun with no MarketData raises | `test_a_run_with_no_market_data_is_served_today[no-market]` | RED, exit 1; exact bytes restored |
| G13 | `agents/provider/barrier_window.py` | window margin dropped | `test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock` | RED, exit 1; exact bytes restored |
| G14 | `agents/provider/barrier_window.py` | window length counted in sessions | `test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock` | RED, exit 1; exact bytes restored |

The mutation runner's restoration output:

```text
RESTORED_SHA256 agents/provider/barrier_window.py 4d786a3095caf4e6e90c5d13ed60aea0730cbf162e9feb18cd4d9e16da73cc83
RESTORED_SHA256 agents/provider/barrier_history.py 689d13f43471f463b836f901915d83f4e128c387eb8e6c71e462902e6e864541
GUARDS_PROVEN=14/14
```

**Module line counts:** `agents/provider/barrier_history.py` **179**, `agents/provider/barrier_window.py` **61**, `agents/provider/tests/test_barrier_history.py` **156**, `agents/provider/tests/test_barrier_window_as_of.py` **162**, `orchestration/tests/barrier_as_of_helpers.py` **122**, `orchestration/tests/test_barrier_claim_as_of.py` **98**. Every touched/new Python module is under 200 lines.

**`make ci`:** redirected to `C:\Users\yury_\AppData\Local\Temp\ta-s266-evidence-20261011\make-ci.txt`, never piped. **Exit 2**, recorded in `make-ci-exit.txt` beside it. **4,655 passed, 8 skipped, 100.00 % coverage.** Steps 1-12 passed. Step 13, dependency audit, is **NOT RUN offline**: the attempted command failed because the blocked proxy could not reach PyPI; no vulnerability audit result was obtained. The overall CI gate is **verified failing**, not green.

The command ran with `UV_OFFLINE=1`, `UV_FROZEN=1`, `PYTHONUTF8=1`; HTTP/HTTPS/ALL proxy pointed at the closed loopback port `127.0.0.1:9`, with localhost exempted. No external network was used. Actual command, relevant log output, and the wrapper's exit output:

```text
make ci > 'C:\Users\yury_\AppData\Local\Temp\ta-s266-evidence-20261011\make-ci.txt' 2>&1
uv run ruff check . --output-format=github
uv run ruff format --check .
1667 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 1192 source files
Contracts: 5 kept, 0 broken.
docs_seen=270 SPEC=10 BUILT=1 MERGED=259 UNMAPPED=0 MISSING=0
TOTAL                                                           20245      0   4290      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 4655 passed, 8 skipped, 2470 warnings in 429.51s (0:07:09) ==========
uv run python scripts/check_dependency_audit.py
requests.exceptions.ProxyError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=9): Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it")))
make: *** [Makefile:59: ci] Error 1
MAKE_CI_EXIT=2
```

All 15 steps are accounted for:

| Step | Check | Proven result |
| --- | --- | --- |
| 1 | ruff | PASS in `make ci` |
| 2 | ruff format | PASS in `make ci` |
| 3 | mypy | PASS in `make ci`, 1,192 source files |
| 4 | import-linter | PASS in `make ci`, 5 kept / 0 broken |
| 5 | module size | PASS in `make ci`; existing warnings retained |
| 6 | module header | PASS in `make ci` |
| 7 | law coverage | PASS in `make ci` |
| 8 | PARAM/settings sync | PASS in `make ci`; existing PM envelope warnings retained |
| 9 | sprint status | PASS in `make ci`, no unmapped/missing statuses |
| 10 | Markdown links | PASS in `make ci` |
| 11 | version scheme | PASS in `make ci`; no version/lock edits |
| 12 | pytest | PASS in `make ci`, 4,655 passed / 8 skipped / 100.00 % |
| 13 | dependency audit | NOT RUN offline; attempt failed before an audit result |
| 14 | detect-secrets | NOT RUN within `make ci` after its stop; PASS separately, exit 0 |
| 15 | untracked secrets | NOT RUN within `make ci` after its stop; PASS separately, exit 0 |

The two remaining commands ran separately under the same offline environment (also redirected, not piped). Their output files are `detect-secrets.txt` and `untracked-secrets.txt` in the evidence directory above, with exit codes in the respective `*-exit.txt` files. Actual command/output:

```text
uv run --frozen pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
DETECT_SECRETS_EXIT=0
uv run --frozen python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
UNTRACKED_SECRETS_EXIT=0
```

**`make gate-ran`:** NOT RUN. The handover forbids pushing or merging, and remote proof is the planner's after its merge-time PATCH bump. No remote gate, merge, deployment, live source, or live graph proof is claimed.

**Not met / verified failing:** `make ci` exit 0 is **not done**: the attempted gate is **verified failing**, exit 2 at the offline dependency audit; the vulnerability audit itself is **NOT RUN** for lack of external network. The eight skipped tests are named above. Remote gates, push, merge, version bump, deployment, Postgres cost measurement, and live F1a/F1b are **not done**, as assigned to the planner. No STOP condition was encountered, and no other requested branch-local proof is missing.

### Scope and exact diffs

The requested protected-scope command **prints nothing**, exit 0. Compared against local `main` at the branch's cut commit `b991d39ef28156d10feef6d2bad9b9dca272be4a`; no moved-main correction was needed. Its captured stdout file `protected-scope.txt` has zero lines. `pyproject.toml` and `uv.lock` are untouched; the planner bumps the version at merge.

```text
git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/monitor agents/execution agents/forecaster agents/deliberator agents/operator agents/master agents/supervisor agents/reporter agents/curator agents/researcher agents/provider/domain agents/provider/ingest.py agents/provider/ingest_chunked.py agents/provider/poll.py agents/provider/agent.py agents/provider/settings.py agents/provider/entrypoint.py contracts kernel surfaces infra scripts orchestration/packs orchestration/history_window.py orchestration/local_pipeline.py orchestration/resume.py orchestration/start.py pyproject.toml uv.lock docs/STATE.md docs/work-queue.md docs/design-log.md
```

Whole production diff (`git diff main -- agents/provider/barrier_history.py agents/provider/barrier_window.py`):

```diff
diff --git a/agents/provider/barrier_history.py b/agents/provider/barrier_history.py
index b38f5508..4b8cfd83 100644
--- a/agents/provider/barrier_history.py
+++ b/agents/provider/barrier_history.py
@@ -12,10 +12,10 @@ External I/O: none directly (delegates to ProviderAgent, which calls the DataSou

 from __future__ import annotations

-import math
-from datetime import UTC, datetime, timedelta
+from datetime import UTC, datetime
 from typing import TYPE_CHECKING, Literal

+from agents.provider.barrier_window import barrier_window, run_as_of
 from contracts.analyst import RecommendationSet
 from contracts.barrier_history import (
     BARRIER_HISTORY_EDGE,
@@ -27,23 +27,18 @@ from contracts.barrier_history import (
     barrier_history_key,
     is_current_run,
 )
-from contracts.common import Window
 from contracts.provider import DataRequest
 from kernel.errors import fault_boundary
 from kernel.graph_pending import pending_nodes

 if TYPE_CHECKING:
     from agents.provider.agent import ProviderAgent
+    from contracts.common import Window
     from contracts.provider import DataQualityTrace, MarketData, OHLCVBar
     from kernel import GraphStore, Node
     from kernel.errors import AgentFault

 ANALYST_RUN_LABEL = "AnalystRun"
-#: Calendar days asked per session: 250 a year is below the exchange's 251-253, so
-#: the window always over-asks (EXP-018: 752 sessions in 1,097 days; DL-241 D3).
-_DAYS_PER_SESSION = 365.25 / 250
-#: Slack for a holiday cluster, a non-session end day, a session not yet served.
-_WINDOW_MARGIN_DAYS = 14
 #: The quality note the provider's fetch path writes when the source itself failed.
 _SOURCE_FAILED_NOTE = "source_unavailable"

@@ -72,7 +67,7 @@ def write_barrier_history(node: Node, *, agent: ProviderAgent) -> None:
     """Fetch the run's qualifying tickers once and write one linked BarrierHistory."""
     tickers = _qualifying_tickers(node)
     sessions = agent._settings.barrier_history_sessions
-    window = barrier_window(sessions)
+    window = barrier_window(sessions, run_as_of(agent._graph, node))
     market: MarketData | None = None
     with fault_boundary(
         agent.sink,
@@ -89,13 +84,6 @@ def write_barrier_history(node: Node, *, agent: ProviderAgent) -> None:
     agent._graph.add_edge(node, written, BARRIER_HISTORY_EDGE)


-def barrier_window(sessions: int) -> Window:
-    """A calendar window ending today that holds at least ``sessions`` sessions."""
-    end = datetime.now(tz=UTC).date()
-    days = math.ceil(sessions * _DAYS_PER_SESSION) + _WINDOW_MARGIN_DAYS
-    return Window(start=end - timedelta(days=days), end=end)
-
-
 def _qualifying_tickers(node: Node) -> tuple[str, ...]:
     raw = node.props.get("recommendation_set")
     if raw is None:
diff --git a/agents/provider/barrier_window.py b/agents/provider/barrier_window.py
new file mode 100644
index 00000000..183c07f3
--- /dev/null
+++ b/agents/provider/barrier_window.py
@@ -0,0 +1,61 @@
+"""The window a barrier history covers: how long it is, and the day it ends on.
+
+Agent: provider
+Role: read the as-of of the run an AnalystRun belongs to through the run's lineage
+      (AnalystRun <-ANALYZED_BY- ScanRun -DERIVED_FROM-> MarketData: one node, never
+      a listing of them), the `window_end` the provider itself stored for that run
+      (PROV-TRG-05), and build the calendar window ending on it that holds the
+      sessions a barrier claim is fitted on (PROV-OUT-08, DL-241 D3).
+External I/O: GraphStore reads via the injected backend.
+"""
+
+from __future__ import annotations
+
+import math
+from datetime import UTC, date, datetime, timedelta
+from typing import TYPE_CHECKING
+
+from contracts.common import Window
+
+if TYPE_CHECKING:
+    from kernel import GraphStore, Node
+
+#: Calendar days asked per session: 250 a year is below the exchange's 251-253, so
+#: the window always over-asks (EXP-018: 752 sessions in 1,097 days; DL-241 D3).
+_DAYS_PER_SESSION = 365.25 / 250
+#: Slack for a holiday cluster, a non-session end day, a session not yet served.
+_WINDOW_MARGIN_DAYS = 14
+_ANALYZED_EDGE = "ANALYZED_BY"
+_DERIVED_FROM = "DERIVED_FROM"
+
+
+def run_as_of(graph: GraphStore, analyst_run: Node) -> date | None:
+    """The as-of of the run ``analyst_run`` was scanned for, or None when it has none.
+
+    The `window_end` of the MarketData the run's ScanRun was derived from. Only a
+    run built by hand has no such lineage: the graph-pull analyst recommends
+    nothing without a MarketData.
+    """
+    scan = next(
+        iter(graph.ancestors(analyst_run, max_depth=1, edge_types={_ANALYZED_EDGE})),
+        None,
+    )
+    if scan is None:
+        return None
+    market = next(
+        iter(graph.descendants(scan, max_depth=1, edge_types={_DERIVED_FROM})), None
+    )
+    if market is None:
+        return None
+    return date.fromisoformat(str(market.props["window_end"]))
+
+
+def barrier_window(sessions: int, as_of: date | None = None) -> Window:
+    """A calendar window holding at least ``sessions`` sessions, ending on ``as_of``.
+
+    ``as_of`` is the run's as-of; a run with none is served as an ingest no run
+    triggered is, ending on today's UTC date (PROV-TRG-05).
+    """
+    end = as_of or datetime.now(tz=UTC).date()
+    days = math.ceil(sessions * _DAYS_PER_SESSION) + _WINDOW_MARGIN_DAYS
+    return Window(start=end - timedelta(days=days), end=end)
```

Whole E1 diff (`git diff main -- agents/provider/tests/test_barrier_history.py`):

```diff
diff --git a/agents/provider/tests/test_barrier_history.py b/agents/provider/tests/test_barrier_history.py
index 2222ae3f..05755819 100644
--- a/agents/provider/tests/test_barrier_history.py
+++ b/agents/provider/tests/test_barrier_history.py
@@ -14,7 +14,7 @@ import json
 from datetime import UTC, datetime, time, timedelta
 from typing import TYPE_CHECKING

-from agents.provider import barrier_history
+from agents.provider import barrier_window
 from agents.provider.barrier_history import (
     find_pending_barrier_history,
     write_barrier_history,
@@ -64,7 +64,7 @@ def test_only_buys_with_both_barriers_get_a_history_from_one_fetch(
     The clock is pinned past the midnight after the fixtures were built: the window
     ends on the clock's UTC date at the call, not on the date this module was
     imported. Unpinned, the test failed whenever the suite straddled 00:00 UTC."""
-    monkeypatch.setattr(barrier_history, "datetime", _PastMidnight)
+    monkeypatch.setattr(barrier_window, "datetime", _PastMidnight)
     graph = InMemoryGraphStore()
     run = analyst_run(graph, *MIXED)
     everyone = tuple(
```

**No other existing test changed.** Comparing E1's final content with the base after just the two authorized substitutions proves those are its only changes.

```text
PROVIDER_CLAUSES_DECLARED=67; CHANGED=['PROV-OUT-08']
ONLY_EXISTING_TEST_CHANGED=agents/provider/tests/test_barrier_history.py
E1_EXACTLY_THE_TWO_AUTHORIZED_LINES=True
```

### Exact law-cycle record

**Provider version:** LOCKED v1.9 -> LOCKED v1.10. No new clause; 24 / 67 unchanged. No forecaster file changed.

`PROV-OUT-08`, quoted as written:

```text
- `PROV-OUT-08` — For an `AnalystRun` that triggers `PROV-TRG-04` it makes **one** OHLCV request
  through its own fetch path (the source's feed and end rule, then validation and the extreme-move
  guard of `PROV-OUT-09`, all shared with the daily request) for **exactly** those buys' tickers,
  over a calendar window holding at least `barrier_history_sessions` sessions
  **that ends on the run's as-of** (the `window_end` of the `MarketData` the run was scanned
  from, read through the run's lineage `AnalystRun ←ANALYZED_BY— ScanRun —DERIVED_FROM→
  MarketData`: one node, never a listing of them; `PROV-TRG-05`), **whenever the provider reaches
  the run**, and writes **one**
  `BarrierHistory` node keyed from the `AnalystRun`'s key, linked
  `AnalystRun -BARRIER_HISTORY_BY-> BarrierHistory`. Per ticker it holds
  the last ≤ `barrier_history_sessions` daily bars as (date, open, high, low, close) and the bar
  count; a requested ticker with no bars is listed under `dropped` with its **named reason** (the
  extreme-move guard, or nothing served), never silently absent; a served ticker whose last bar is
  stale is listed as `stale`. A **failed fetch still writes the node**, `status: failed` with the
  reason and every ticker dropped with it, so no reader waits forever — never an empty success, never
  no node. A barrier fetch holds too few tickers for the `PROV-OUT-09` guard to fire (its √(n−1)
  ceiling), so this path **leans on the daily request's guard**: its newest session is the one the
  daily request judged, and a ticker the daily request excluded never becomes a buy.
  A run with no such `MarketData` has no as-of and is served as an ingest no run triggered is:
  its window ends on the UTC date of the fetch (`PROV-TRG-05`). A `MarketData` whose
  `window_end` is absent or not a date is a broken node, not a run with no as-of: the work fails
  before any fetch and no node is written.
  *(DL-241 D10; DRIFT-090, DL-247 D4; DRIFT-110, S266, DL-287.)*
```

Its test-plan row, quoted as written:

```text
| PROV-OUT-08 | One OHLCV request through the fetch path (feed and end rule, validation, the `PROV-OUT-09` guard) shared with the daily request, for exactly the qualifying tickers over a calendar window holding `barrier_history_sessions` sessions and ending on the run's as-of (`MarketData.window_end` read through `ANALYZED_BY` then `DERIVED_FROM`, one node per hop), whenever the provider reaches the run; no lineage ends on the fetch's UTC date, but an absent or unparseable stored `window_end` raises before any fetch and writes no history; one linked `BarrierHistory` with ≤ 760 bars and the count per ticker; dropped tickers named; stale ones marked; a failed fetch still writes a failed node. | happy + partial + fault + past as-of + resume + no lineage + broken date | `test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch; test_barrier_history_failures.py::test_a_dropped_ticker_carries_its_named_reason; test_newest_session_guard.py::test_a_real_history_day_never_drops_a_buy_from_its_barrier_history; test_barrier_history_failures.py::test_a_failed_fetch_still_writes_a_failed_node; test_barrier_history_failures.py::test_an_exception_in_the_fetch_path_still_writes_a_failed_node; test_barrier_history.py::test_the_history_passes_the_packs_vocabulary_guard; agents/forecaster/tests/test_barrier_route.py::test_a_failed_fetch_never_leaves_the_forecaster_waiting; test_barrier_window_as_of.py::test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock; test_barrier_window_as_of.py::test_the_as_of_is_read_by_edge_never_by_key; test_barrier_window_as_of.py::test_a_run_with_no_market_data_is_served_today; test_barrier_window_as_of.py::test_an_unreadable_window_end_fails_before_any_fetch; orchestration/tests/test_barrier_claim_as_of.py::test_a_past_runs_claim_is_stated_on_its_own_last_bar; orchestration/tests/test_barrier_claim_as_of.py::test_the_deployed_work_list_serves_the_runs_as_of; orchestration/tests/test_barrier_claim_as_of.py::test_a_resumed_analysis_uses_its_source_runs_as_of` | 🟩 |
```

DRIFT-110's status cell, quoted as written:

```text
**CORRECTED (S266, provider laws v1.10, 2026-10-11; [DL-287](../design-log.md)).** `PROV-OUT-08` amended: the history ends on the run's as-of by lineage, no lineage serves the fetch's UTC date, and a broken stored date raises before any fetch or history write. Unit-proven by A1-A3 (`orchestration/tests/test_barrier_claim_as_of.py`) and B1-B4 (`agents/provider/tests/test_barrier_window_as_of.py`), with E1's moved clock pin; no live or remote proof claimed.
```

`docs/laws/ledger.md`, whole provider rollup:

```text
| provider | ✅ v1.10 (LOCKED) | 24 / 67 | 🟨 partial — **24 of 67 clauses proven** after S266 (DL-287) amends and re-proves `PROV-OUT-08`: the barrier history ends on the run's as-of by lineage whenever the provider reaches it, missing lineage serves the fetch's UTC date, and a broken stored date raises before any fetch or history write (DRIFT-110); count unchanged; before that S255 (DL-269) amends and re-proves `PROV-OUT-02`: the regime records its four label thresholds; count unchanged; before that S251 (DL-260) amends four clauses to the code: `PROV-TRG-01` names every recorded data need (a bus request, an unconsumed `RunRequest`, an `AnalystRun`'s qualifying buys) and is re-proven with no bus event (DRIFT-082); `PROV-TRG-02` states the poll's key-and-edge bound and turns green (DRIFT-086); `PROV-OUT-07` says served bars are raw (DRIFT-084); `PROV-OUT-04` is narrowed to fetch time and the fallback flag and turns green (DRIFT-040, the vendor gap is work-queue 105); before that S249 (DL-256) adds and proves `PROV-TRG-05`: an ingest a `RunRequest` triggers serves that run's as-of whenever the provider reaches it (window, coverage check, regime, news and earnings anchors), an unusable as-of is refused before any fetch, and an ingest with no run serves today (DRIFT-095); before that S243 (DL-247) adds and proves `PROV-OUT-09`: the extreme-move guard judges each ticker's newest session only, against that session's cross-section, so a real extreme day in a name's history never drops it (DRIFT-088), and states the guard's √(n−1) ceiling (DRIFT-090, CORRECTED: the barrier path leans on the daily request's guard, DL-247 D4); `PROV-OUT-08` amended and re-proven; before that S239 (DL-241 D10) adds and proves `PROV-TRG-04` / `PROV-OUT-08` (the `BarrierHistory` per `AnalystRun`, one batched fetch, dropped tickers named, a failed fetch still written); before that S238 adds and proves `PROV-OUT-07`: a bar's volume is the consolidated tape's (the Alpaca feed defaults to SIP), a SIP request never ends inside the plan's 15-minute recent-data window, and a refusal fails loud with no IEX fallback (DRIFT-080); S213 sharpens and proves `PROV-OUT-03` for FMP `^VIX` freshness without adding clauses; S187 added PARAM rows only; S204 gives every clause a row and promotes missing rows to a hard gate; S169-sweep demoted `PROV-OUT-04` |
```

`docs/laws/INDEX.md`, whole provider rollup:

```text
| provider | ✅ LOCKED v1.10 (S266, DL-287) | 24 / 67 | S266 (DL-287) amends and re-proves `PROV-OUT-08`: barrier history ends on the run's as-of by lineage whenever the provider reaches it, missing lineage serves the fetch's UTC date, and a broken stored date fails before any fetch or history write (DRIFT-110); count unchanged; S255 (DL-269) amends and re-proves `PROV-OUT-02`: the regime records its four label thresholds; count unchanged; S251 amends `PROV-TRG-01` (every recorded data need, re-proven on graph-pull; DRIFT-082), `PROV-TRG-02` (the poll's key-and-edge bound, now green; DRIFT-086), `PROV-OUT-07` (served bars are raw; DRIFT-084) and narrows `PROV-OUT-04` (fetch time and fallback flag, now green; DRIFT-040); S249 adds and proves `PROV-TRG-05` (a `RunRequest`'s ingest serves the run's as-of whenever the provider reaches it; an unusable as-of is refused before any fetch; no run serves today; DRIFT-095); S243 adds and proves `PROV-OUT-09` (the extreme-move guard judges each ticker's newest session only; its √(n−1) ceiling stated) and amends `PROV-OUT-08`; S239 adds and proves `PROV-TRG-04` / `PROV-OUT-08` (the `BarrierHistory` per `AnalystRun`) and reconciles `PROV-TRG-02` with graph-pull; S238 adds and proves `PROV-OUT-07` (consolidated-tape volume, entitlement-respecting requests, loud refusal; DRIFT-080); DL-203 reconciles `PARAM` only; S213 adds FMP `^VIX` regime freshness evidence and proves `PROV-OUT-03` without adding clauses; S187 adds PARAM rows only; counters are clauses proven / clauses declared; S204 gives every clause a row and makes rowless clauses a hard gate |
```

**Law gate:** `uv run --frozen python scripts/check_law_coverage.py`, redirected to `law-coverage.txt`: stdout/stderr empty, exit 0. The command wrapper printed:

```text
LAW_COVERAGE_EXIT=0
```

**Every `PROV-OUT-08` citation:** each file and function was resolved with Python AST, its docstring checked for the clause, and the cases then executed (16 passed above).

```text
ALL_CITATIONS_RESOLVED_AND_DOCSTRINGS_CHECKED=14
agents/provider/tests/test_barrier_history.py::test_only_buys_with_both_barriers_get_a_history_from_one_fetch
agents/provider/tests/test_barrier_history_failures.py::test_a_dropped_ticker_carries_its_named_reason
agents/provider/tests/test_newest_session_guard.py::test_a_real_history_day_never_drops_a_buy_from_its_barrier_history
agents/provider/tests/test_barrier_history_failures.py::test_a_failed_fetch_still_writes_a_failed_node
agents/provider/tests/test_barrier_history_failures.py::test_an_exception_in_the_fetch_path_still_writes_a_failed_node
agents/provider/tests/test_barrier_history.py::test_the_history_passes_the_packs_vocabulary_guard
agents/forecaster/tests/test_barrier_route.py::test_a_failed_fetch_never_leaves_the_forecaster_waiting
agents/provider/tests/test_barrier_window_as_of.py::test_a_runs_barrier_history_ends_on_its_as_of_without_reading_the_clock
agents/provider/tests/test_barrier_window_as_of.py::test_the_as_of_is_read_by_edge_never_by_key
agents/provider/tests/test_barrier_window_as_of.py::test_a_run_with_no_market_data_is_served_today
agents/provider/tests/test_barrier_window_as_of.py::test_an_unreadable_window_end_fails_before_any_fetch
orchestration/tests/test_barrier_claim_as_of.py::test_a_past_runs_claim_is_stated_on_its_own_last_bar
orchestration/tests/test_barrier_claim_as_of.py::test_the_deployed_work_list_serves_the_runs_as_of
orchestration/tests/test_barrier_claim_as_of.py::test_a_resumed_analysis_uses_its_source_runs_as_of
```

---

## Return notes

- Scope held. D1-D6 were built as written; no amendment to DL-287 was needed. Production changes are confined to the two named provider modules. E1 changes exactly its import and `setattr` lines; all other tests are new. `pyproject.toml`, `uv.lock`, the state trackers, and the design log are untouched. No push or merge was performed.
- No law/spec contradiction was found. The brief's provider test-plan footer does not exist in the current file; no footer was invented. The provider count remains 24 / 67 in the existing rollups, with only PROV-OUT-08 amended. Shared fixture setup lives in the new `orchestration/tests/barrier_as_of_helpers.py` so both test modules stay under 200 lines. Empty diff context lines in the pasted whole diffs have their trailing space removed for the whitespace gate; all hunks and changed content are retained.
- Unit and mutation proof establish the requested lineage, date, price, fallback, and pre-fetch failure behavior. They do not establish Postgres read cost, live source equality, or live fleet/resume behavior. F1a/F1b, the merge-time version bump, remote gates, merge, deployment, and live proof remain the planner's work. No remaining implementation uncertainty was found within the authorized unit-test scope.

---

## Appendix — the planner's prototype

Measured in `../ta-s266` at `c32398fc` on 2026-10-11 and then removed, so the worktree is clean.
With E1's two lines edited and the Test plan's tests written, the full suite read **4,655 passed, 8
skipped, 100.00 %**, and `ruff`, `mypy`, the import contracts, the size step and the header step
passed on these two files.

**New file, `agents/provider/barrier_window.py`:**

```python
"""The window a barrier history covers: how long it is, and the day it ends on.

Agent: provider
Role: read the as-of of the run an AnalystRun belongs to through the run's lineage
      (AnalystRun <-ANALYZED_BY- ScanRun -DERIVED_FROM-> MarketData: one node, never
      a listing of them), the `window_end` the provider itself stored for that run
      (PROV-TRG-05), and build the calendar window ending on it that holds the
      sessions a barrier claim is fitted on (PROV-OUT-08, DL-241 D3).
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from contracts.common import Window

if TYPE_CHECKING:
    from kernel import GraphStore, Node

#: Calendar days asked per session: 250 a year is below the exchange's 251-253, so
#: the window always over-asks (EXP-018: 752 sessions in 1,097 days; DL-241 D3).
_DAYS_PER_SESSION = 365.25 / 250
#: Slack for a holiday cluster, a non-session end day, a session not yet served.
_WINDOW_MARGIN_DAYS = 14
_ANALYZED_EDGE = "ANALYZED_BY"
_DERIVED_FROM = "DERIVED_FROM"


def run_as_of(graph: GraphStore, analyst_run: Node) -> date | None:
    """The as-of of the run ``analyst_run`` was scanned for, or None when it has none.

    The `window_end` of the MarketData the run's ScanRun was derived from. Only a
    run built by hand has no such lineage: the graph-pull analyst recommends
    nothing without a MarketData.
    """
    scan = next(
        iter(graph.ancestors(analyst_run, max_depth=1, edge_types={_ANALYZED_EDGE})),
        None,
    )
    if scan is None:
        return None
    market = next(
        iter(graph.descendants(scan, max_depth=1, edge_types={_DERIVED_FROM})), None
    )
    if market is None:
        return None
    return date.fromisoformat(str(market.props["window_end"]))


def barrier_window(sessions: int, as_of: date | None = None) -> Window:
    """A calendar window holding at least ``sessions`` sessions, ending on ``as_of``.

    ``as_of`` is the run's as-of; a run with none is served as an ingest no run
    triggered is, ending on today's UTC date (PROV-TRG-05).
    """
    end = as_of or datetime.now(tz=UTC).date()
    days = math.ceil(sessions * _DAYS_PER_SESSION) + _WINDOW_MARGIN_DAYS
    return Window(start=end - timedelta(days=days), end=end)
```

**`agents/provider/barrier_history.py`, the whole change:**

- the imports: `import math` goes; `from datetime import UTC, datetime, timedelta` becomes
  `from datetime import UTC, datetime`; `from agents.provider.barrier_window import barrier_window,
  run_as_of` is added; `from contracts.common import Window` moves under `TYPE_CHECKING`;
- the two constants `_DAYS_PER_SESSION` and `_WINDOW_MARGIN_DAYS`, with their comments, go;
- in `write_barrier_history`, `window = barrier_window(sessions)` becomes
  `window = barrier_window(sessions, run_as_of(agent._graph, node))`;
- the function `barrier_window` goes.

**`agents/provider/tests/test_barrier_history.py`, the whole change (E1):**
`from agents.provider import barrier_history` becomes `from agents.provider import barrier_window`,
and `monkeypatch.setattr(barrier_history, "datetime", _PastMidnight)` becomes
`monkeypatch.setattr(barrier_window, "datetime", _PastMidnight)`.
