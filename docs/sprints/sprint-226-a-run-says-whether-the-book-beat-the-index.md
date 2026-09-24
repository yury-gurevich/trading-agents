<!-- Agent: planning | Role: sprint handover — S226, next-leg E16.1: the reporter measures the book against the index -->
# Sprint 226 — a run says whether the book beat the index

**Phase:** Next leg, P16 scoreboard ([next-leg-plan.md](../next-leg-plan.md) item E16.1)
**Branch:** `sprint-226-a-run-says-whether-the-book-beat-the-index`
**Status:** BUILT
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-209](../design-log.md) (the next leg, accepted 2026-09-23) · the builder records this sprint's design decisions as the next free DL number

> **Why this bump kind.** The reporter gains a dimension it never had: portfolio return against a
> benchmark. That is a new capability, so a MINOR bump.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/reporter/laws/laws.md` | The reporter's **locked constitution** (v1.1) | **This sprint amends it through a law cycle** (see below). Every other clause stays read-only |
| `agents/reporter/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read to learn what is proven. Add a row per new clause |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | `drift-register.md` is the one law-adjacent file you may append to freely |

Binding sections here: **`RPT-IDN-01`**, **`RPT-OUT-01`**, **`RPT-NEV-03`**, **`RPT-IDM-01`**, **`RPT-ORD-01`**,
**`RPT-FAIL-01`**, **`RPT-TYP-01`**, **`RPT-TYP-03`**, **`RPT-SEC-02`**, the `CAP` block and the `PARAM` table.

### The rule

1. **Before writing code**, read every law file in the map below: the whole file, the first time.
2. Read `agents/reporter/laws/test-plan.md` alongside `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes, on both counts. This sprint owes a law cycle in the same unit of work:**

- **`contracts/reporter.py`** gains `RunSnapshot.performance_metrics: dict[str, float]`, with a
  default of `{}` so that every `ReportSnapshotResult` already in the graph still validates
  (`RPT-TYP-03`).
- **New guarantees:** the reporter reports return against a benchmark, bounded to what was known on
  the run's own date.

The cycle covers:

- new clauses (proposed wording below; refine it, but keep the substance);
- amend `RPT-OUT-01`, `RPT-TYP-01` and `RPT-ORD-01` in place, keeping their IDs;
- add `BrokerPositionSnapshot` and `MarketData` to the `CAP` block's `labels_read`;
- two `PARAM` rows;
- bump `laws.md` to v1.2 with a Changelog line;
- `test-plan.md` rows;
- clause IDs cited in test docstrings;
- the rollups in **both** `docs/laws/ledger.md` and `docs/laws/INDEX.md`. The rollup is derived, so
  let `make ci` tell you the number.

Proposed clauses:

- **RPT-OUT-07** — `report` returns `performance_metrics`: return on the book against the
  benchmark, from the start date `performance_inception` to the run's as-of date. It is computed only
  from facts other agents wrote: execution's `fresh` `BrokerPositionSnapshot` equity and holdings, and
  the benchmark bars on the provider's `MarketData`.
- **RPT-IDM-03** — The as-of date is the UTC date of the run's `PMRun.created_at`. No fact dated after
  it is read, so re-reporting an old run reproduces its figures however much the graph has grown since.
- **RPT-FAIL-04** — A performance failure is contained. If the performance inputs cannot be read, the
  rest of the snapshot is still produced, `performance_metrics` reports zero sessions, and a fault is
  recorded.
- **Amend RPT-ORD-01** — "No cross-run *ordering* dependency." Reading upstream facts recorded by
  earlier runs is allowed. Depending on the reporter's own earlier output is not.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/reporter/domain/performance.py` *(new, pure)* | reporter `laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `RPT-OUT-07`, `RPT-NEV-03` (undefined → 0 and say why), `RPT-IDN-01` (it synthesises, never decides) |
| `agents/reporter/performance_inputs.py` *(new, graph reads)* | same | `RPT-IDM-03`, `RPT-NEV-02` (reads only, never mutates another agent's nodes), `CAP` `labels_read` |
| `agents/reporter/result.py` (**155** lines) | same | `RPT-OUT-01`, `RPT-FAIL-01`, `RPT-FAIL-04` |
| `agents/reporter/settings.py` | same, `PARAM` table | Two new tunables need `PARAM` rows, or the PARAM/settings sync fails the gate (item 33) |
| `contracts/reporter.py` | same, plus `RPT-TYP-01`/`RPT-TYP-03` | Adding a field changes `contracts/`: the law cycle is mandatory |

⚠️ **The reporter never decides (RPT-IDN-01, RPT-NEV-01).** Nothing in this sprint may feed a
performance number back into a gate, a size or a veto. It is a readout. If you find yourself wiring it
anywhere but `Snapshot` / `RunSnapshot`, stop and report.

---

## Goal

After merge and deploy, every run's reporter `Snapshot` carries `metrics.performance`. That group states
the book's time-weighted return since `performance_inception` (2026-08-10), the benchmark's return over
the same sessions, what the benchmark would have returned at the book's own exposure, the excess over
that, average exposure, max drawdown, and the same figures over the last `performance_rolling_sessions`
sessions. Each figure is recomputable from graph facts alone (`RPT-OBS-01`), and re-reporting the
`sched-2026-09-22` PM run reproduces the reference values measured below.

## Why (context)

The operator accepted the next-leg plan on 2026-09-23. Its first question is *are we beating the
index?*, and nothing in the system can answer it. Reporter metrics stop at profit factor and
expectancy (`agents/reporter/domain/metrics.py`), and the PRD's G1–G5 contain no return goal. Every
later leg depends on this number: P17's ten-year replay scores itself with the **same** function
(one definition of "return", the DL-208 lesson), and the G-EDGE decision reads both.

### Measured, 2026-09-23 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Execution already records account equity and cash every run | `BrokerPositionSnapshot` props `account_status`, `account_equity_cents`, `account_cash_cents`, `account_buying_power_cents`, `holdings[].market_value_cents`, `created_at` | *[measured 2026-09-23]* `agents/execution/snapshot_account.py`, `reconciliation_store.py:69-94`; live graph: **178** snapshots, **97** `fresh` with account fields, the first on `sched-2026-08-06` |
| The benchmark series already reaches the graph every run | `MarketData.props.snapshot.benchmark` = list of `{ticker, bar_date, open, high, low, close, volume}` | *[measured 2026-09-23]* live graph: **12** scheduled `MarketData` nodes carry it, the first `sched-2026-09-04`; `market-data:sched-2026-09-22` holds **203** SPY bars, the last `bar_date 2026-09-22 close 773.44` |
| The equity series before 2026-08-10 is a different book | 2026-08-06/07: equity **$103,150**, cash **−$104,967**, holdings **$208,117** (**~2× gross, on margin**); 2026-08-10: **0** holdings | *[measured 2026-09-23]* live snapshots; recorded as DL-93 and executed by `chore-flatten-and-resize`. **Hence `performance_inception = 2026-08-10`.** |
| A snapshot and a benchmark bar align by date | The scheduled run's snapshot is written at ~22:30 UTC on session date *d*, after that session's close; the SPY bar with `bar_date` *d* is that close | *[measured 2026-09-23]* `sched-2026-09-22` snapshot `2026-09-22T22:30:35Z` ↔ SPY `bar_date 2026-09-22` |
| **Reference values, as of 2026-09-22** | **31 dates, 30 pairs, 0 gaps.** portfolio **−0.4644 %** · benchmark **+0.0543 %** · exposure-matched **+0.0399 %** · excess **−0.5042 %** · average exposure **21.11 %** · max drawdown **−0.864 %** | *[measured 2026-09-23]* a read-only script over the live graph implementing exactly the definitions in Scope item 1 (earliest `fresh` snapshot per UTC date ≥ 2026-08-10; benchmark from `market-data:sched-2026-09-22`) |
| `PMRun` carries a creation time | `PMRun` props: `approved_count`, `created_at`, `order_intent_set`, `rejected_count`, `source_analyst_run_id` | *[measured 2026-09-23]* live graph, latest `PMRun` |
| The paper account has had no deposits or withdrawals since inception | none | *[ASSUMED — not measured]* A paper account has none unless reset. The live check below is the settle: if the reference values reproduce, the assumption held for the window |
| Nothing downstream breaks on a new `RunSnapshot` field | — | *[ASSUMED — not measured]* The builder greps every reader of `ReportSnapshotResult` / `RunSnapshot` (dispatcher, surfaces, dashboard) and states the result in the handback |

---

## Scope — and what is deliberately NOT here

1. **The failing test first: a pure performance function** in `agents/reporter/domain/performance.py`.
   It takes plain data (a list of `(date, equity_cents, long_value_cents)` points and a
   `{date: close}` benchmark map) and returns `dict[str, float]`. It imports nothing from the graph,
   the bus or the kernel's I/O, so `scripts/` can import it for P17. Definitions:
   - **Points:** one per UTC date: the earliest `fresh` snapshot on that date, with dates ≥ inception
     and ≤ as-of. `long_value` = the sum of `holdings[].market_value_cents`.
   - **Pairs:** consecutive points *(a, b)*. A pair is **usable** only when both dates have a
     benchmark close. Otherwise it counts in `performance_gap_sessions` and is skipped.
   - `portfolio_return_pct` = (∏ over usable pairs of E_b / E_a − 1) × 100.
   - `benchmark_return_pct` = (∏ over usable pairs of C_b / C_a − 1) × 100.
   - `exposure_matched_return_pct` = (∏ over usable pairs of (1 + w_a × (C_b / C_a − 1)) − 1) × 100,
     where w_a = long_value_a / E_a.
   - `excess_return_pct` = portfolio − exposure-matched.
   - `average_exposure_pct` = the mean of w_a over usable pairs × 100.
   - `max_drawdown_pct`: the worst peak-to-trough fall in E across all points, × 100 (≤ 0).
   - `rolling_portfolio_return_pct`, `rolling_exposure_matched_return_pct`,
     `rolling_excess_return_pct`: the same formulas over the **last** `performance_rolling_sessions`
     usable pairs.
   - `performance_sessions` = the number of usable pairs. `equity_cents` = the latest point's equity.
   - **Fewer than one usable pair** → every figure is `0.0` and `performance_sessions = 0.0`
     (`RPT-NEV-03`).
2. **Graph reads** in `agents/reporter/performance_inputs.py`: the snapshots, and the benchmark map
   from the `MarketData` node with the greatest `window_end` ≤ as-of whose `snapshot.benchmark` is
   non-empty. The as-of date is the UTC date of `PMRun.created_at` (`RPT-IDM-03`).
3. **Wire it into `build_snapshot`** inside its **own** `fault_boundary`, so that a performance
   failure never loses the portfolio, signal and regime groups (`RPT-FAIL-04`). The result lands in
   `metrics_blob["performance"]` and in `RunSnapshot.performance_metrics`. The headline gains **one**
   clause:
   - normally: `"vs SPY: −0.50 pts over 30 sessions at 21 % invested"`, with the ticker read from the
     bars, never hard-coded;
   - with no usable pair: `"Performance: no usable sessions since 2026-08-10 (<reason>)"`.
4. **Two tunables** in `ReporterSettings`, each with a `PARAM` row:
   - `performance_inception`: a date, default `2026-08-10`. *why:* the book was flattened and resized
     that day (DL-93); the equity before it was ~2× gross on margin and is a different system.
   - `performance_rolling_sessions`: an int, default `20`, `ge=5`, `le=120`.
5. **The law cycle** as set out above.

### Out of scope (do NOT build this sprint)

- **Any dashboard, chat or Telegram surface.** That is E16.3, the next sprint. 🪤 It carries a law
  question this sprint must not pre-empt: `RPT-SEC-02` forbids the reporter logging P&L to external
  systems, and Telegram is one.
- **Backfilling equity before 2026-08-06 from Alpaca portfolio history.** It is ruled out (see
  below), not deferred.
- **A new graph label, or a new property on any label.** The metrics live inside `Snapshot.metrics`
  and `ReportSnapshotResult.snapshot`, which are existing dict props. If you believe a vocabulary
  change is needed, stop and report: it turns the deploy into a full `up`.
- **Feeding any performance number into a decision.** That violates `RPT-NEV-01`.
- **No ADR reversal.**

### The road not taken (LAW-06)

- **A new `EquitySnapshot` label written by execution**, as the plan's first draft said. Rejected:
  execution already records the same facts on `BrokerPositionSnapshot` every run (measured above). A
  second label would be a second definition of equity.
- **Fetching SPY in the reporter.** Rejected: the reporter holds no credentials (`RPT-SEC-01`), and the
  provider already stores the benchmark on `MarketData` every run.
- **Backfilling from Alpaca portfolio history to start at 2026-07-07.** Rejected: everything before
  2026-08-10 is the ~2× margin book that DL-93 flattened. Scoring it would blend two systems into one
  number and flatter the current one (the +2.13 % since July was mostly earned there).
- **Excess against raw SPY only.** Rejected: at ~21 % invested, raw SPY compares a mostly-cash book to
  a fully invested one. Exposure-matched is the honest comparison; raw SPY is reported beside it.
- **Simple return E_last / E_first.** Rejected in favour of chaining pairs: with no cash flows the two
  are identical, but chaining is what makes the gap and exposure handling well-defined, and it is the
  shape P17's replay needs.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Whether to read the latest `MarketData` or the run's own.** The spec says the greatest
   `window_end` ≤ as-of, which covers a run whose own ingest carried no benchmark. Confirm it, or
   argue for the run's own node.
2. **Where the pure function lives.** The spec says `agents/reporter/domain/performance.py`, importable
   by `scripts/` for P17. If import-linter objects to a script importing it, record the fix. Moving it
   into `kernel/` is **not** an option: return against a benchmark is pack vocabulary (ADR-0012).
3. **The headline wording**, including negative zero and rounding (for example `−0.00 pts`).

🪤 **Take the next free DL number, then re-check it at merge.** The log is prepended at the top, and a
branch cut before another DL lands will collide.

---

## Blast radius — measured 2026-09-23

| What | Detail |
| --- | --- |
| Files changed | `agents/reporter/result.py` (**155**, warn band: add at most ~6 lines, put logic in the new modules), `agents/reporter/settings.py` (**29**), `contracts/reporter.py` (**80**), new `agents/reporter/domain/performance.py`, new `agents/reporter/performance_inputs.py`, reporter `laws.md` (**166**) + `test-plan.md` (**46**), `docs/laws/ledger.md`, `docs/laws/INDEX.md`, tests |
| Agents affected | reporter only; it imports no other agent |
| Contract change? | **yes**: `RunSnapshot.performance_metrics` (default `{}`), so the law cycle is mandatory |
| Graph vocabulary change? | **no**: dict contents of existing props |
| New env keys / tunables | `REPORTER_PERFORMANCE_INCEPTION`, `REPORTER_PERFORMANCE_ROLLING_SESSIONS`, with code defaults and **no pack row** |
| Deploy implication | `contracts/` compiles into every image, so the merge auto-build rebuilds all of them: **image-only retag of the full fleet**, pack read-back unchanged. Confirm at deploy that all three injected packs are byte-identical |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** (A1–A3) and watch them fail. Paste the red output.
4. **Implement.**
5. **Law cycle:** clauses, `test-plan.md` rows, docstring citations, both rollups, `PARAM` rows,
   Changelog v1.2.
6. **Prove the guards can fail (DL-70):** break each guard, watch it go red, restore it.
7. **`make ci` green**: every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 The worked example (`RPT-OUT-07`) | 3 points: E = 1,000,000 / 1,010,000 / 999,900 cents; long = 500,000 / 505,000 / 0; closes 100 / 102 / 101 | portfolio **−0.0100**, benchmark **+1.0000**, exposure-matched **+0.504902** (to 1e-6), excess **−0.514902**, average exposure **50.0**, max drawdown **−1.000000** (999,900 / 1,010,000 = 0.99 exactly), sessions **2** |
| A2 | 🎯 The as-of bound (`RPT-IDM-03`) | Graph: snapshots on d1…d4, `PMRun.created_at` on d3 | d4 is never read. The result equals the one from a graph with d4 absent |
| A3 | 🎯 Inception (`RPT-OUT-07`) | A `fresh` snapshot dated before inception with −$104,967 cash | It contributes to no figure, including max drawdown |
| A4 | Earliest fresh snapshot per date | Two `fresh` snapshots on one date (22:30 and 22:44 UTC, different equity) plus one `stale` | The 22:30 one is used; the `stale` one never is |
| A5 | Benchmark gap | A date with no benchmark close | That pair is skipped and `performance_gap_sessions` = 1; the next pair still counts |
| A6 | 🪤 Too little data (`RPT-NEV-03`) | One point only | Every figure `0.0`, `performance_sessions` `0.0`, and the headline states the reason. No exception |
| A7 | 🪤 No benchmark anywhere (`RPT-NEV-03`) | Snapshots but no `MarketData` with a non-empty benchmark | As A6, with the reason naming the missing benchmark |
| A8 | 🪤 Containment (`RPT-FAIL-04`) | A graph whose `MarketData` read raises | Portfolio, signal and regime groups are intact; performance reports zero sessions; one fault reaches the sink |
| A9 | Backward compatibility (`RPT-TYP-03`) | A `ReportSnapshotResult` payload written **before** this sprint (no `performance_metrics`) | `claim_check_read` + `RunSnapshot.model_validate` succeed |
| A10 | Rolling window | 25 usable pairs, `performance_rolling_sessions=20` | The rolling figures use exactly the last 20 pairs; the since-inception figures use all 25 |
| A11 | Purity | Import `agents.reporter.domain.performance` in a subprocess | `kernel.graph*`, the bus and `agents.reporter.store` are not in `sys.modules` |

---

## Success factors

- [ ] Re-reporting the **`sched-2026-09-22`** PM run (`pm-run-9a0beefaf3b44fcfa1721c32d65c7b2d`)
      against the live graph, from the **main checkout with `.env`**, read-only through `build_snapshot`
      on an in-memory copy **or** by a dry call that does not write, reproduces the reference values to
      within 0.0001 pts: **−0.4644 / +0.0543 / +0.0399 / −0.5042**, exposure **21.11**, drawdown
      **−0.864**, sessions **30**, gaps **0**.
- [ ] After deploy, the next scheduled run's `Snapshot` node carries `metrics.performance` with
      `performance_sessions` = 31 (or more) and the headline clause.
- [ ] No figure is read from a fact dated after the run's as-of date (A2).
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Law cycle done: v1.2, new clauses 🟩, both rollups updated, `PARAM` rows present.
- [ ] Every new guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module < 200 lines; `result.py` still < 160.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The reference numbers can be matched by accident.** A function that reads the *latest*
`MarketData` rather than the one bounded by as-of will reproduce them today and drift tomorrow. A2 is
the guard; the re-report of `sched-2026-09-22` a few days after merge is the live check.

🪤 **`holding_count` is not exposure.** Use the sum of `holdings[].market_value_cents`. A count of 23
names says nothing about the 21 % invested.

🪤 **Negative cash is real, not a bug to clamp.** The pre-inception snapshots have cash of
−$104,967. The inception bound excludes them; do not "fix" negative cash anywhere.

🪤 **The equity at 22:30 UTC is that session's closing equity.** Do not shift dates by one to "align"
with the bar. The Alpaca +1-day label trap concerns portfolio-history bars, which this sprint does not
read.

🪤 **A performance number must never reach a gate.** `RPT-IDN-01` / `RPT-NEV-01`: the reporter
synthesises; it never decides.

🪤 **The skip count is an environment fingerprint** (DL-193). A worktree has no `.env`, so state which
tree every proof ran in. The live reproduction **needs** the main checkout's `.env`.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `agents/reporter/result.py` **155**, `agents/reporter/domain/metrics.py` **104**,
  `agents/reporter/settings.py` **29**, `contracts/reporter.py` **80**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure: `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- Version bump: MINOR, with `uv.lock` staged alongside it.
- Secrets never through the worktree.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**, run from the worktree whose
   `HEAD` is the commit being proven. **Check the printed SHA against `git rev-parse HEAD`.**
2. Merge to `main` locally and push.
3. **Post-merge CodeQL:** check it after merging.
4. **Deploy:** an image-only retag of all 16 apps to the merge's build, after confirming the three
   injected packs are byte-identical to the deployed commit.
5. **Functionality check:** the `sched-2026-09-22` re-report (Success factor 1) and the next
   scheduled run's `Snapshot`. Append a row to `docs/laws/functionality-checks.md`.

---

## Handover — paste this to Codex

```text
Sprint 226 — "a run says whether the book beat the index". Branch:
sprint-226-a-run-says-whether-the-book-beat-the-index (create it in a worktree; never commit to main).
Spec: docs/sprints/sprint-226-a-run-says-whether-the-book-beat-the-index.md — read it whole.

MUST RULE: before any code, read agents/reporter/laws/laws.md, its test-plan.md,
docs/laws/conventions.md and docs/laws/drift-register.md, then fill the Law reading record.

LAW CYCLE IS OWED (contracts/reporter.py changes): RunSnapshot gains
performance_metrics: dict[str, float] = {}. Add clauses RPT-OUT-07, RPT-IDM-03, RPT-FAIL-04; amend
RPT-OUT-01, RPT-TYP-01, RPT-ORD-01 (keep IDs); add BrokerPositionSnapshot and MarketData to CAP
labels_read; PARAM rows for REPORTER_PERFORMANCE_INCEPTION (2026-08-10) and
REPORTER_PERFORMANCE_ROLLING_SESSIONS (20, 5..120); laws v1.2 + Changelog; test-plan rows; cite
clause IDs in test docstrings; rollups in docs/laws/ledger.md AND docs/laws/INDEX.md.

BUILD: a pure function in agents/reporter/domain/performance.py (no graph/bus imports), graph reads
in agents/reporter/performance_inputs.py, wired into build_snapshot inside its OWN fault_boundary.
Definitions are in Scope item 1 — implement them exactly. As-of = UTC date of PMRun.created_at;
never read a fact dated after it.

TESTS FIRST: A1–A3 red before any implementation; paste the red output. Then A4–A11.

DO NOT: add a graph label or property; fetch market data in the reporter; backfill from Alpaca;
feed any performance number into a decision; touch any dashboard, chat or Telegram surface;
edit any law clause other than those named; pipe make ci into anything.

TRAPS: read the as-of-bounded MarketData, not the latest; exposure = sum of market_value_cents,
not holding_count; negative cash before inception is real; do not shift dates by one.
result.py is 155 lines — keep it under 160 and put logic in the new modules.

HANDBACK: fill Law reading record, Test plan results, Closeout evidence (red run, green run, guards
planted, line counts, make ci redirected to a file with exit code), Return notes; set Status: BUILT
and update this sprint's docs/sprints/README.md row to lead with BUILT in the same commit. State
which tree each proof ran in and whether .env was present.
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
| `agents/reporter/domain/performance.py` | reporter `laws.md`, reporter `test-plan.md`, `docs/laws/conventions.md`, `docs/laws/drift-register.md` | `RPT-OUT-07`, `RPT-NEV-03`, `RPT-IDN-01` | Yes: define a pure, total projection that returns zero-valued metrics for insufficient usable pairs rather than raising or influencing a decision. |
| `agents/reporter/performance_inputs.py` | reporter `laws.md`, reporter `test-plan.md`, `docs/laws/conventions.md`, `docs/laws/drift-register.md` | `RPT-IDM-03`, `RPT-NEV-02`, `RPT-CAP` | Yes: inputs must be read-only and explicitly bounded to the UTC PMRun as-of date; MarketData is selected by `window_end`, never by recency alone. |
| `agents/reporter/result.py` | reporter `laws.md`, reporter `test-plan.md`, `docs/laws/conventions.md`, `docs/laws/drift-register.md` | `RPT-OUT-01`, `RPT-FAIL-01`, `RPT-FAIL-04`, `RPT-ORD-01` | Yes: keep the existing snapshot path intact and isolate performance in its own `fault_boundary`, with no dependency on prior reporter output. |
| `agents/reporter/settings.py` | reporter `laws.md`, reporter `test-plan.md`, `docs/laws/conventions.md`, `docs/laws/drift-register.md` | `RPT-PARAM` | Yes: both processing controls require bounded `tunable()` declarations and matching PARAM rows. |
| `contracts/reporter.py` | reporter `laws.md`, reporter `test-plan.md`, `docs/laws/conventions.md`, `docs/laws/drift-register.md` | `RPT-TYP-01`, `RPT-TYP-03` | Yes: use a defaulted `performance_metrics` mapping so existing claim-checked snapshots remain deserializable. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes to both. `RunSnapshot` gains a backward-compatible `performance_metrics` mapping, and the reporter gains date-bounded benchmark-performance guarantees. This sprint therefore amends the locked reporter law to v1.2, adds the three scoped clauses, updates the named existing clauses, CAP/PARAM rows, test-plan rows, and both derived rollups.

**Contradictions found between a law and this spec:** None. The existing reporter law confines the reporter to read-only projection, which matches the scope; its absence of benchmark-performance guarantees is addressed by this explicit law cycle.

**Laws found silent where a decision was needed:** None beyond the explicitly scoped new guarantee. The handover supplies the required decision and mandates its same-sprint amendment, so no separate drift row is warranted.

**Clauses that were ⬜ and are now proven:** `RPT-OUT-07`, `RPT-IDM-03`, `RPT-FAIL-04`, and the amended limbs of `RPT-OUT-01`, `RPT-TYP-01`, and `RPT-ORD-01`.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_performance_worked_example` | `agents/reporter/tests/test_performance.py` | GREEN | `RPT-OUT-07` |
| A2 | `test_performance_inputs_do_not_read_after_pmrun_as_of` | `agents/reporter/tests/test_performance.py` | GREEN; mutation-proven red | `RPT-IDM-03` |
| A3 | `test_performance_inputs_exclude_pre_inception_margin_book` | `agents/reporter/tests/test_performance.py` | GREEN | `RPT-OUT-07` |
| A4 | `test_performance_uses_earliest_fresh_snapshot_per_date` | `agents/reporter/tests/test_performance_snapshot.py` | GREEN | `RPT-OUT-07`, `RPT-IDM-03` |
| A5 | `test_performance_skips_missing_benchmark_pair_then_continues` | `agents/reporter/tests/test_performance_metrics.py` | GREEN | `RPT-OUT-07` |
| A6 | `test_performance_returns_zero_when_no_pair_is_usable`; `test_snapshot_names_too_little_data_without_raising` | `agents/reporter/tests/test_performance_metrics.py`; `agents/reporter/tests/test_performance_snapshot.py` | GREEN | `RPT-NEV-03`, `RPT-OUT-07` |
| A7 | `test_snapshot_names_missing_benchmark_without_raising` | `agents/reporter/tests/test_performance_snapshot.py` | GREEN | `RPT-NEV-03`, `RPT-FAIL-04` |
| A8 | `test_snapshot_contains_performance_fault_without_losing_other_groups` | `agents/reporter/tests/test_performance_snapshot.py` | GREEN | `RPT-FAIL-04`, `RPT-OUT-01` |
| A9 | `test_legacy_snapshot_without_performance_metrics_deserializes` | `agents/reporter/tests/test_performance_compat.py` | GREEN | `RPT-TYP-03`, `RPT-TYP-01` |
| A10 | `test_performance_rolling_metrics_use_only_last_configured_pairs` | `agents/reporter/tests/test_performance_metrics.py` | GREEN | `RPT-OUT-07` |
| A11 | `test_performance_calculator_import_is_pure` | `agents/reporter/tests/test_performance_metrics.py` | GREEN | `RPT-CAP`, `RPT-OUT-07` |

**Tests added beyond the plan:** `test_snapshot_ignores_prior_reporter_performance_output` (`RPT-ORD-01`), malformed-input edge coverage in `test_performance_inputs_edges.py` (`RPT-IDM-03`), the no-fresh-snapshot fallback (`RPT-NEV-03`), the zero-equity drawdown guard (`RPT-OUT-07`), and the reporter field assertion in `test_reporter_payload_fields_required_by_law` (`RPT-TYP-01`).

---

## Closeout — evidence

**Status:** BUILT and BRANCH-GATED on branch `sprint-226-a-run-says-whether-the-book-beat-the-index`; not merged.

**Tree the proofs ran in (and `.env` present?):** Red proof ran in `C:\Users\yury_\Downloads\project\trading-agents-sprint-226-red-proof` from `main` `59c0818ad3858dde795162bb77eb9d108f1dced0` with no `.env`. Green unit, line-count, and local gate proofs ran in `C:\Users\yury_\Downloads\project\trading-agents-sprint-226-a-run-says-whether-the-book-beat-the-index` with no `.env`. The read-only reference re-report ran from the S226 worktree against an in-memory graph copy after loading the main checkout `.env`; it performed no live writes.

**Result:** Built the reporter performance group from existing `BrokerPositionSnapshot` and as-of-bounded `MarketData`, exposed it as `RunSnapshot.performance_metrics`, and kept the numbers out of all decision paths and user surfaces. The live reference re-report of `sched-2026-09-22` matched the sprint values to 0.0001 percentage points: portfolio `-0.464357`, benchmark `0.054332`, exposure-matched `0.039868`, excess `-0.504225`, average exposure `21.107334`, max drawdown `-0.863749`, sessions `30`, gaps `0`.

**Files changed:** Reporter runtime and tests (`agents/reporter/__init__.py`, `agent.py`, `result.py`, `settings.py`, `domain/lineage.py`, new `domain/performance.py`, `performance_inputs.py`, `narrative_result.py`, `snapshot_result.py`, reporter performance tests), reporter contract (`contracts/reporter.py`), law/test-plan/rollups, sprint/state docs, version files (`pyproject.toml`, `uv.lock`), and `tests/test_contract_required_fields.py`.

**Design decisions:** [DL-210](../design-log.md#dl-210---performance-is-recomputed-from-as-of-bounded-facts---status-decided-s226-2026-09-23) records the as-of-bounded `MarketData` selection, pure-domain calculation, separate reporter fault boundary, and the rejected alternatives: latest-only `MarketData`, kernel placement, and feeding performance into decisions.

**Proof — the red run first:**

```text
tree=C:\Users\yury_\Downloads\project\trading-agents-sprint-226-red-proof; .env absent
$ uv run pytest agents\reporter\tests\test_performance.py --no-cov
collected 3 items

agents\reporter\tests\test_performance.py FFF                            [100%]

FAIL agents\reporter\tests\test_performance.py::test_performance_worked_example
ModuleNotFoundError: No module named 'agents.reporter.domain.performance'
FAIL agents\reporter\tests\test_performance.py::test_performance_inputs_do_not_read_after_pmrun_as_of
ModuleNotFoundError: No module named 'agents.reporter.performance_inputs'
FAIL agents\reporter\tests\test_performance.py::test_performance_inputs_exclude_pre_inception_margin_book
ModuleNotFoundError: No module named 'agents.reporter.performance_inputs'
3 failed in 7.68s
```

**Proof — the green run:**

```text
tree=C:\Users\yury_\Downloads\project\trading-agents-sprint-226-a-run-says-whether-the-book-beat-the-index; .env absent
$ uv run pytest agents\reporter\tests tests\test_contract_required_fields.py --no-cov
collected 62 items
...
agents\reporter\tests\test_performance.py ...                            [ 14%]
agents\reporter\tests\test_performance_compat.py .                       [ 16%]
agents\reporter\tests\test_performance_inputs_edges.py ..                [ 19%]
agents\reporter\tests\test_performance_metrics.py .....                  [ 27%]
agents\reporter\tests\test_performance_snapshot.py ......                [ 37%]
...
tests\test_contract_required_fields.py ......                            [100%]
62 passed in 1.78s

read-only reference check, in-memory graph copy, main .env loaded, live_writes=0:
portfolio_return_pct=-0.464357 benchmark_return_pct=0.054332 exposure_matched_return_pct=0.039868 excess_return_pct=-0.504225 average_exposure_pct=21.107334 max_drawdown_pct=-0.863749 performance_sessions=30.000000 performance_gap_sessions=0.000000
0 positions opened; 0 closed; 0 recommendations stitched. vs SPY: -0.50 pts over 30 sessions at 21% invested
```

**Guards planted:** A1-A3 were red first on a separate main-based red-proof worktree. A2 was then mutation-proven by temporarily removing the `window_end > as_of` filter; the test failed because the future `MarketData` changed the as-of close from `101.0` to `90.0`, then passed after restoration:

```text
$ uv run pytest agents\reporter\tests\test_performance.py::test_performance_inputs_do_not_read_after_pmrun_as_of --no-cov
E   assert {datetime.date(2026, 8, 12): 90.0} == {datetime.date(2026, 8, 12): 101.0}
FAILED agents/reporter/tests/test_performance.py::test_performance_inputs_do_not_read_after_pmrun_as_of

$ uv run pytest agents\reporter\tests\test_performance.py::test_performance_inputs_do_not_read_after_pmrun_as_of --no-cov
1 passed in 0.90s
```

**Module line counts:** `agents/reporter/result.py` 154; `agents/reporter/performance_inputs.py` 190; `agents/reporter/domain/performance.py` 128; `agents/reporter/domain/lineage.py` 179; `agents/reporter/snapshot_result.py` 49; `agents/reporter/tests/test_performance_snapshot.py` 163; `agents/reporter/tests/test_performance_inputs_edges.py` 104.

**`make ci`:** Redirected to `C:\Users\yury_\Downloads\project\s226-make-ci.log` from the S226 worktree with `.env` absent; exit code `0`.

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
Required test coverage of 100.0% reached. Total coverage: 100.00%
3119 passed, 6 skipped in 111.81s (0:01:51)
No unaccepted vulnerabilities; 1 accepted advisory re-checked
Detect secrets...........................................................Passed
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 9 new file(s)
```

**`make gate-ran`:** First branch proof from `C:\Users\yury_\Downloads\project\trading-agents-sprint-226-a-run-says-whether-the-book-beat-the-index`; `.env` absent; output matched the worktree `HEAD`.

```text
$ make gate-ran
uv run python scripts/assert_gate_ran.py
GATE PROVEN for beb52e12ce873845f6ebdf0ddf63cab62abdce0d:
  CI: success (attempt 1)
  CodeQL: success (attempt 1)
  Security Findings: success (attempt 1)

$ git rev-parse HEAD
beb52e12ce873845f6ebdf0ddf63cab62abdce0d
```

**Not met / verified failing:** Not merged to `main`; not deployed; no next scheduled run has emitted a production `Snapshot` with the new metrics yet; no post-deploy functionality-check row was appended.

---

## Return notes

- S226 is built and branch-gated. The remaining lifecycle steps are merge, image-only retag/deploy, and the next-run live `Snapshot` check.
- The contract field uses `Field(default_factory=dict)` instead of a literal `{}` so the mutable default passes the repo's ruff rules while preserving the required empty-map default behavior.
- There is no `docs/local/STATE.md` in this checkout; the sprint state update is recorded in `docs/STATE.md`.
