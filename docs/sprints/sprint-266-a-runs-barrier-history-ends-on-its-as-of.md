<!-- Agent: planning | Role: sprint handover -->
# Sprint 266 — a run's barrier history ends on the run's as-of, so a barrier claim is stated on the run's own last bar whenever the provider reaches the run

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-266-a-runs-barrier-history-ends-on-its-as-of`
**Status:** SPEC
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

- [ ] A run reached after its as-of writes a `BarrierHistory` whose `window_end` and newest bar are
      the as-of's, on the in-process pass and on the provider's deployed work list (A1, A2).
- [ ] Each claim of such a run carries the as-of as its `as_of` and that day's close as its
      `entry_close` (A1).
- [ ] A resumed analysis reads its source run's as-of through the cloned lineage (A3).
- [ ] The clock is not read for a run that has an as-of (B1).
- [ ] A run with no `MarketData` lineage is served as today (B3, E1); a `MarketData` with no
      readable `window_end` fails the work before any fetch (B4).
- [ ] No decision path changes: the scope command prints nothing.
- [ ] No file in `agents/forecaster/`, `contracts/`, `kernel/` or `orchestration/` outside
      `orchestration/tests/` changes.
- [ ] Exactly one existing test edited, in two lines (E1).
- [ ] The law cycle done: `PROV-OUT-08` amended as written, v1.10, changelog, the test-plan row,
      both rollup lines, DRIFT-110 CORRECTED; the provider's count stays 24 / 67.
- [ ] Every new guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage; any step the sandbox cannot run named NOT RUN.

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
| <element> | <files> | <clause IDs> | <Yes/No + what changed> |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** <Yes/No + what it owed and what was done>

**Contradictions found between a law and this spec:** <none | what, and what you did>

**Laws found silent where a decision was needed:** <none | what, and the drift row filed>

**Clauses that were ⬜ and are now proven:** <IDs, and the rollup in ledger.md + INDEX.md>

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | <name> | <file> | PASS/FAIL | <clause IDs> |

**Tests added beyond the plan:** <none | what and why>

---

## Closeout — evidence

**Status:** <BUILT | MERGED>

**Tree the proofs ran in (and `.env` present?):** <path, branch, .env yes/no>

**Result:** <what is now true, in the artefact's own words — not the intent restated>

**Files changed:** <list>

**Design decisions:** recorded as [`DL-287`](../design-log.md) — <one line on any amendment, or "built as written">

**Proof — the red run first:**

```text
<the failing test output, before the implementation>
```

**Proof — the green run:**

```text
<the passing output>
```

**Guards planted:** <per guard: what was planted, that it failed, that it was restored>

**Module line counts:** <file **n**, file **n**>

**`make ci`:** redirected to `<path>`. Exit code <n>. `<N passed, M skipped>`, coverage `<100.00 %>`.
dependency audit `<result>`. detect-secrets `<result>`.

**`make gate-ran`:** run from `<worktree path>` at `<full 40-char SHA>`:

```text
GATE PROVEN for <sha>:
  Security Findings: success
  CI: success
```

**Not met / verified failing:** <plainly, or "none">

---

## Return notes

- <Scope held / where it moved and why.>
- <What you disagreed with in the spec after reading the laws.>
- <What the next sprint should know that is not obvious from the diff.>

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
