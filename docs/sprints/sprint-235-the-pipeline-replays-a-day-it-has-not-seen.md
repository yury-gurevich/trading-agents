<!-- Agent: planning | Role: sprint handover -->
# Sprint 235 — the pipeline replays a day it has not seen, with its own code and the fleet's settings

**Phase:** Etalon-first continuous improvement (DL-19) · next leg P17, item **E17.3** (the replay harness)
**Branch:** `sprint-235-the-pipeline-replays-a-day-it-has-not-seen`
**Status:** BUILT
**Version:** *next available MINOR at merge*
**Effort:** L
**Decisions:** [DL-232](../design-log.md) (the replay's scope: **settled, do not reopen**) ·
[DL-233](../design-log.md) (IEX volume, a live defect fixed elsewhere, **not** here) ·
[DL-229](../design-log.md) / [DL-227](../design-log.md) (the cache) · ADR-0017 (exit authority) ·
ADR-0029 (only `overturn` blocks) · work-queue **82** · the builder records its decisions as **DL-234**
(**DL-235 is reserved for S236**, which is being built in parallel)

> **Why this bump kind.** The fleet gains nothing, but the repository gains a capability it did not have:
> replaying the whole deterministic pipeline, day by day, from cached data. New capability → MINOR.

**Builder:** Codex. **Your worktree has no `.env` and no network.** Every proof is on synthetic fixtures;
the cache rebuild and the first real replays are the planner's, after merge. **If a number you measure
differs from one written here, stop and report. Do not adjust and continue.**

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

**No agent law book binds `scripts/`**, but this harness **calls** the scanner's, analyst's, PM's,
provider's, execution's and reporter's domain functions. You do not change them; you must call them the
way their laws say they behave. Binding: [`docs/laws/conventions.md`](../laws/conventions.md), `CLAUDE.md`
(200-line block covers `scripts/`; header `Agent:`/`Role:`/`External I/O:`), [DL-232](../design-log.md),
and the **licensing rule** in `scripts/replay_dataset.py`'s docstring: *the repository is public and
Alpaca SIP bars are licensed, so the cache lives outside the worktree and is never committed.* That rule
now covers **replay outputs** too: an equity curve or a fill log is derived from licensed prices.

### The rule

1. **Before writing code**, read the files in the map below — whole file, first time.
2. There is no agent `test-plan.md` for `scripts/`; **the test plan in this spec is the contract**.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a rule contradicts this spec, STOP and report.**
7. **If a rule is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Tests cite the test-plan row they prove in their docstrings (`"""S235-A4: ..."""`).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's expected answer is No.** Everything lives in `scripts/` and `tests/`. If calling an agent
function from the harness needs **any** change under `agents/`, `contracts/`, `kernel/` or
`orchestration/`, **stop and report**: that is an agent change with a law cycle, not this sprint.

### Element → rule map

| Element | Read first | Why it binds |
| --- | --- | --- |
| `scripts/replay_dataset_sources.py` (97 lines) `daily_bars` | its docstring; `scripts/replay_dataset.py` | also builds `bars.csv.gz`; **its default request and its return shape must not change** |
| `scripts/sp500_bars.py` (164), `scripts/sp500_chain.py` (136), `scripts/replay_universe_cache.py` (144), `scripts/replay_universe.py` (**194**) | DL-227, DL-229 | where volume must be carried; the chain rescales prices only |
| `agents/scanner/domain/filters.py`, `ranking.py`, `filter_attestation.py`; `agents/scanner/laws/laws.md` | scanner laws | `apply_filters` + `rank_survivors` are the scanner; absence of an earnings map records `skipped` |
| `agents/analyst/held_universe.py`, `domain/analyze.py`, `result.py`; `agents/analyst/laws/laws.md` | analyst laws | `scoring_universe` → `score_candidates` → `split_decisions`; pillars renormalise over present ones |
| `agents/portfolio_manager/domain/risk.py`, `portfolio.py`, `run.py` (read only); PM laws | PM laws | `evaluate_recommendations` with the arguments `run_evaluation` passes |
| `agents/provider/domain/regime.py`, `agents/provider/settings.py`; provider laws | provider laws | `classify_regime` and the `base_*` fields of `RegimeContext` |
| `agents/execution/order_tolerance.py`, `alpaca_orders.py`; execution laws | execution laws | day **limit** orders at `resolve_order_tolerance`'s applied limit; GTC stops |
| `contracts/stop_rule.py` | — | `stop_price_cents`, `check_stop`: one stop rule |
| `agents/reporter/domain/performance.py`; reporter laws (`RPT-OUT-07`) | reporter laws | **the** return metric; the replay must not define its own |
| `orchestration/history_window.py`, `orchestration/start.py` (read only) | — | the bar window a live run ships |
| `orchestration/packs/trading_tunables.json`, `trading_issuer_map.json` | ADR-0012 | the fleet's effective settings and issuer map |
| `agents/provider/fundamentals_parse.py` `_parse_sector` | provider laws | the live sector taxonomy (`finnhubIndustry`) |

⚠️ **Two invariants.** (1) **No look-ahead:** a decision for session *d* reads nothing dated after *d*.
(2) **No re-implementation:** every stage is the fleet's own function, called, not copied. If a stage
cannot be called as it is, stop and report.

---

## Goal

After this sprint the planner can run one command that replays the deterministic pipeline over the
cached S&P 500, one session at a time, with no bus and no graph. For each session it slices the
universe and bars as they stood, runs the scanner, the analyst and the PM **through their own
functions** with the **fleet's effective settings**, and submits the PM's approvals as the fleet
would: a day limit order at the decided tolerance, then a GTC stop at the decided width. It then
marks the book at the close. The result is a daily equity curve scored by the reporter's own
`calculate_performance`, a fill log, and a summary that counts every input DL-232 names as absent.
Before any of this runs, the cache gains the three things the pipeline needs and it lacks: **volume**,
**SPY bars** and **VIX to the cache's end**, plus a **sector table**.

## Why (context)

P17 exists to answer whether the pipeline has an edge, out of sample and survivorship-free. E17.1 and
E17.2 built the universe (99.993 % coverage, one issuer per line). Nothing yet drives the pipeline over
it: `run_walkforward` scores signals with top-k rebalancing and cannot run PM gates, sizing, stops or
thesis exits. E17.4 (fidelity against live) and E17.5 (EXP-014, the ten-year verdict) both run on this
harness, and E18A.1/E18A.2 would reuse it for parameter arms. DL-232 settled what the replay covers:
the **price-only** pipeline, with everything absent named and counted.

### Measured, 2026-09-27 — read these before designing

All from the planner's session on `main` @ `4cd87b73`, the live spine and live Alpaca. **Not reproducible
in your worktree** (no network, no `.env`); your proofs are the synthetic fixtures in the test plan.

| # | Claim | Value | How it was measured |
| --- | --- | --- | --- |
| 1 | The domain code runs without the bus or the graph | scanner, analyst and PM `domain/` import only `contracts/`, their own settings and kernel fault types; the functions in the map are pure (`score_candidates` needs a `FaultSink`: `kernel.errors.CollectingFaultSink` exists) | *[measured]* import survey of each `domain/` package |
| 2 | The cache | `sp500_bars.csv.gz` header `line,symbol,date,open,high,low,close`: **no volume**; 1,359,653 rows; 732 episodes; 2,697 sessions 2016-01-04 → 2026-09-24. **No SPY bars** in any cache file. `vix.csv.gz` ends **2026-09-21** | *[measured]* read the files in `%USERPROFILE%\OneDrive\trading-agents-data` |
| 3 | A live run ships **203** bars per name | `declared_lookback_days(AnalystSettings(), as_of=d, staleness_buffer_sessions=ProviderSettings().max_staleness_days)` (200 + 3); the scanner computes its features over all of them | *[measured]* the `ScanRun`'s `average_volume` equals Alpaca's 203-session average to the share (DL-233) |
| 4 | The fleet's effective settings are code defaults plus `trading_tunables.json` → `apps` | e.g. `SCANNER_CANDIDATE_CAP=25`, `ANALYST_EXIT_CONFIDENCE_FLOOR=0.50`, `ANALYST_STOP_TARGET_MODE=scaled`, seven `PORTFOLIO_MANAGER_*` keys, `EXECUTION_ORDER_PRICE_TOLERANCE_MODE=scaled`. A full `up` replaces each app's env with the pack (the pack's own `_comment`) | *[measured]* read the pack; the 2026-09-26 full `up` read back all 21 injected values |
| 5 | Live order mechanics | entries and thesis exits: `type=limit`, `time_in_force=day`, limit = `resolve_order_tolerance(intent, side, config).applied_limit_price`; protection: `type=stop`, GTC, at `stop_price_cents(entry, decided stop_pct)` | *[measured]* `agents/execution/alpaca_orders.py:25–62`, `order_tolerance.py:71` |
| 6 | Exits | the stop, or a held name scoring under `exit_confidence_floor` (sell recommendation → PM `decide_exit`). No time exit: `base_max_holding_days` is only rendered for the deliberator | *[measured]* grep of `max_holding_days` |
| 7 | When a new stop starts protecting | the fill is observed and the stop placed by the **next run** after the fill session | *[ASSUMED from DL-118 / S225 (adoption at run start). E17.4 measures stop timing against live.]* |
| 8 | Composite weights | technical 0.50 (relative strength 0.20 inside it), fundamental 0.30, sentiment 0.20, alpha158 0.00, renormalised over present pillars | *[measured]* `agents/analyst/settings.py` |
| 9 | The live universe | `scripts/universe_sp100.txt`, **99** tickers, unchanged since 2026-06-24 | *[measured]* file + `git log` |
| 10 | Live sectors | Finnhub `/stock/profile2` `finnhubIndustry`; AAPL → `Technology`; delisted CELG → none | *[measured]* live probe |
| 11 | Known moves | `scripts/sp500_known_moves.csv`: 10 rows, **4 `adjustment-error`** (TGNA 2017-06-01, RTX 2020-04-03, APTV 2017-12-05, WRK 2016-05-16: all spin-offs the adjusted series over-states) and 6 `event` | *[measured]* S233's live build |
| 12 | Held lines can outlive their bars | bar windows are membership-bounded (S231); 43 lines end 1–5 sessions early (deal closes) | *[measured]* S233 coverage payload |
| 13 | Run time | *unknown* — `score_candidates` over ~25 candidates plus held names on each of 2,697 sessions | *[ASSUMED ≤ 60 min on the planner's machine]* — you measure a synthetic 500-line × 300-session run and report it |

---

## Scope — and what is deliberately NOT here

### Part A — the cache holds what the pipeline reads

1. **Volume on every bar.** `daily_bars` gains `with_volume: bool = False`. With the default, the
   request **and** the returned tuples are exactly today's (`bars.csv.gz` depends on both). With
   `with_volume=True` each tuple carries Alpaca's `v`. The universe build asks for it;
   `sp500_bars.csv.gz` gains a `volume` column. **Chaining rescales prices only**: a window's chain
   factor corrects an adjustment basis, not a share count, so volume is carried unchanged.
2. **The loader stays backward-compatible and says so.** `load_universe_cache` reads a cache with or
   without `volume` and exposes whether it had one. **The harness refuses to run on a cache without
   volume**, naming the missing column, rather than silently passing the volume filter.
3. **SPY bars and VIX beside the universe.** The build writes `sp500_benchmark.csv.gz` (SPY OHLCV,
   SIP, `adjustment=all`, pinned `asof` the build's end, one row per session) and `sp500_vix.csv.gz`
   (Cboe VIX closes over the sessions, through the existing `vix_history`). **`vix.csv.gz` and
   `bars.csv.gz` are not touched.**
4. **A sector table, from a separate subcommand.** `replay_universe.py sectors` fetches Finnhub
   `/stock/profile2` once per distinct symbol in the membership, **paced at ≤ 1 call per second**
   (the free tier's 60/min), parses with the provider's own `_parse_sector`, and writes
   `sp500_sectors.csv.gz` (`line,symbol,sector`; empty where Finnhub has none). A bars rebuild never
   refetches sectors.
5. **`--describe`** adds: volume present (yes/no), benchmark sessions, VIX sessions and last date,
   sector coverage (symbols with a sector / all).

### Part B — the harness

6. **Inputs, sliced as they stood.** For session *d*: the members on *d* (`first ≤ d ≤ last`), or a
   fixed ticker list (`--universe-file`, the live 99 for E17.4); each member's bars in the live window
   (`declared_lookback_days(…)` calendar days ending *d*, measured row 3); SPY bars in the same window;
   VIX on *d*. Bars are converted to `contracts.provider.OHLCVBar` with the **line** as the ticker.
7. **The fleet's effective settings.** Each settings class (`ScannerSettings`, `AnalystSettings`,
   `PortfolioManagerSettings`, `ProviderSettings`, `ExecutionSettings`) is built from its code defaults
   plus the pack's `apps` entry for its app, then any `--set KEY=VALUE` overrides (same env-var names as
   the pack). **An unknown key fails loudly, naming it.** The summary records every effective value that
   differs from the code default.
8. **One session's decision** (a pure function of the inputs and the book):
   `classify_regime` → a `RegimeContext` with the provider's `base_*` fields → scanner
   (`apply_filters` with `earnings={}` and `earnings_horizon_days=None`, then `rank_survivors` with
   `candidate_cap`) → analyst (`scoring_universe` with the book's held lines, `score_candidates` with
   `fundamentals={}`, `news={}`, `sentiment={}`, the book's held stops and **every held stop ref marked
   active**, then `split_decisions`) → PM (`evaluate_recommendations` with the arguments
   `run_evaluation` passes: prices = closes on *d*, the book's `PortfolioState`, `sectors`, the issuer
   map, correlation bars).
9. **The broker, as the fleet uses it.** Each approved `OrderIntent` becomes a **day limit order for
   session *d+1*** at `resolve_order_tolerance(intent, side, config).applied_limit_price`. A buy fills at
   `min(open, limit)` if `low ≤ limit`, else expires (counted); a sell fills at `max(open, limit)` if
   `high ≥ limit`, else expires. `--slippage-bps` (default **10**) moves every fill price against the
   trader. After a buy fills, a GTC stop at `stop_price_cents(fill_cents, intent stop_pct)` protects
   from the **session after** the fill (row 7). A stop fills on the first session whose `low ≤ stop`,
   at `min(open, stop)` less slippage.
10. **Days the data cannot be trusted.** On a listed `adjustment-error` day (row 11) a held line's entry
    and stop are rescaled by that day's close ratio, so the book books no return across the error (a
    spin-off roughly preserves the holder's value), and no stop is evaluated against the false jump.
    A held line whose bars end is sold at its **last close**, with reason `data_end` if its episode
    ends at the same date or `membership_end` otherwise. Every such event is counted.
11. **Marking and scoring.** After each session: equity = cash + Σ qty × close, long value = Σ qty ×
    close. The points `(d, equity_cents, long_cents)` and SPY's closes go through
    `agents.reporter.domain.performance.calculate_performance` (`rolling_sessions=20`).
12. **Outputs, outside the repo.** `scripts/replay_pipeline.py run --start --end [--universe-file]
    [--slippage-bps] [--capital 100000] [--set KEY=VALUE …] [--out DIR]` writes, under the cache
    directory by default (`replays/<start>_<end>_<hash of the arguments>/`): `equity.csv`,
    `fills.csv` (date, line, side, qty, price, reason: `entry`/`thesis_exit`/`stop`/`data_end`/
    `membership_end`), `sessions.csv` (per session: members, candidates, recommendations, approvals,
    rejections by reason, expired orders), and `summary.json` (the performance dict, the effective
    settings that differ from defaults, and the **absent-input counters**: pillars present, earnings
    filter skipped count, sessions without a deliberator, member-sessions without a sector,
    adjustment-error rebases, `data_end` and `membership_end` exits). **An output directory inside the
    worktree is refused**, the same guard as the cache.
13. **Deterministic.** The same arguments over the same cache produce byte-identical files.
14. **The design decisions** go to `docs/design-log.md` as **DL-234** before implementation.

### Out of scope (do NOT build this sprint)

- **The fidelity check (E17.4)** and **EXP-014 (E17.5)**. This sprint builds the instrument; the
  planner's first runs after merge are smoke checks, not results.
- **Fundamentals, sentiment and earnings history.** DL-232 rules them out. Do not approximate them.
- **The deliberator.** Every PM approval reaches the simulated broker (DL-232).
- **The IEX volume defect** (DL-233, work-queue 89). The replay uses SIP volume on purpose.
- **Any change under `agents/`, `contracts/`, `kernel/`, `orchestration/`.** Stop and report instead.
- **`replay_dataset.py`, `bars.csv.gz`, `vix.csv.gz`, `load()`, EXP-011 to EXP-013.** Read only.
- **Walk-forward windows, bootstrap, ablation loops.** E17.5 composes them from `run` and `--set`.
- **No `laws.md` edit. No ADR reversal.**

### The road not taken (LAW-06)

- **Re-implement the stages in the harness** (a faster scanner, a vectorised scorer). Rejected: the
  replay's value is that it is the fleet's code; a copy drifts the first time an agent changes.
- **Fill at the next open plus slippage** (the plan's first wording). Rejected: the fleet submits day
  **limit** orders; a buy that gaps above its limit never fills live and must not fill here.
- **Settings from code defaults.** Rejected: the pack overrides **12** values across the scanner,
  analyst, PM and execution (row 4), and S223 already found PM defaults that differ from the fleet's.
- **Skip the volume filter while the cache lacks volume.** Rejected: the filter decides eligibility;
  and on SIP it still bites for a few thin, high-priced names.
- **Hold a line after its bars end, marked at its last close.** Rejected: an equity curve holding a
  frozen price is a silent fiction; an explicit, counted exit is visible.
- **Book an `adjustment-error` day as it reads.** Rejected: all four are spin-offs where the adjusted
  series shows −35 % to −85 % while the holder kept most of the value.
- **Fetch SPY from the old `bars.csv.gz`.** It is not there (row 2).

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` as DL-234, with their rejected alternatives, BEFORE implementing.**

1. **How the effective settings are built**: set environment variables around each constructor, or
   validate a field mapping with the prefix stripped. Either way the pack's key must resolve to a field
   or fail.
2. **The book's shape**: which state carries entry cents, stop percentage, stop cents, the fill session
   (for row 7), and the `position_ref` the analyst's held-stop path reads.
3. **Per-line bar access** without rescanning 1.36 M rows per session (a sorted array per line plus
   `bisect`, or similar), and how the window is cut with `declared_lookback_days`.
4. **Module boundaries**: `replay_universe.py` is **194** lines, so the context files and the `sectors`
   subcommand need a new module (for example `scripts/sp500_context.py`); the harness needs several
   (for example `replay_inputs.py`, `replay_settings.py`, `replay_day.py`, `replay_book.py`,
   `replay_outputs.py`, `replay_pipeline.py`), each under 200.
5. **Order of events within a session**: stops and expiring limits resolve on the session's bars before
   the close is marked and before the day's decision is made.

🪤 **DL-234 is yours; DL-235 is S236's**, built in parallel. Re-check both at handback.

---

## Blast radius — measured 2026-09-27

| What | Detail |
| --- | --- |
| Files changed | `scripts/replay_dataset_sources.py` (97), `scripts/sp500_bars.py` (164), `scripts/sp500_chain.py` (136) only if volume needs threading, `scripts/replay_universe_cache.py` (144), `scripts/replay_universe.py` (194); **new** context/sectors module, **new** harness modules; tests (new modules plus `tests/test_replay_universe.py`, `tests/test_sp500_bars.py` where the header changes) |
| Agents affected | none. Scripts import agents' domain functions; no agent imports `scripts/` |
| Contract change? | no |
| Graph vocabulary change? | no. The harness never opens a graph |
| New env keys / tunables | none. Script constants (`--slippage-bps` default, Finnhub pacing) are named, with their reason |
| Deploy implication | **none.** `scripts/` ships in no image |

---

## Steps, in order

1. **Read the rules** (MUST RULE above) and write the Law reading record.
2. **Record DL-234.**
3. **Plant the failing tests first** (A1, A2, A4, A6 below) and watch them fail on `main`. Paste the red.
4. **Implement** Part A, then Part B.
5. **Prove the guards can fail (DL-70)**: let the window include *d+1* (A1 red); inline a copy of
   `rank_survivors` (A2 red); build settings from code defaults only (A3 red); fill a gapped buy at the
   open (A4 red); arm a stop on its fill session (A5 red); score equity with a local return formula
   (A9 red). Restore each.
6. **`make ci` green** — every step, **redirected to a file, never piped**.
7. **Fill the handback sections.**

---

## Test plan

All fixtures are **synthetic**: invented prices and volumes, never Alpaca data. Build one small fixture
universe (for example 6 lines over 260 sessions, one line that leaves the index, one listed
`adjustment-error` day, one gap-down through a stop) and reuse it.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 no look-ahead | a bar dated *d+1* that, if read, would change the scanner's ranking and the PM's price | the decision for *d* (candidates, recommendations, approved intents) is identical with and without every bar after *d* in the input |
| A2 | 🎯 the stages are the fleet's own functions | — | the harness calls the very objects `agents.scanner.domain.filters.apply_filters`, `…ranking.rank_survivors`, `agents.analyst.held_universe.scoring_universe`, `…domain.analyze.score_candidates`, `agents.analyst.result.split_decisions`, `agents.portfolio_manager.domain.risk.evaluate_recommendations`, `agents.provider.domain.regime.classify_regime`, `agents.execution.order_tolerance.resolve_order_tolerance`, `contracts.stop_rule.stop_price_cents`, `agents.reporter.domain.performance.calculate_performance` (assert by identity, or patch each and see it called) |
| A3 | 🎯 the fleet's settings | the committed pack | the effective values include `candidate_cap == 25`, `exit_confidence_floor == 0.50`, `stop_target_mode == "scaled"`, all seven PM overrides, `order_price_tolerance_mode == "scaled"`; a `--set` wins over the pack; an unknown key raises naming it |
| A4 | 🎯 a day limit order fills as the broker would | buy limit 100.00 on *d+1*: (a) open 99.50; (b) open 101, low 99.80; (c) open 101, low 100.40 | (a) fills 99.50, (b) fills 100.00, (c) expires, counted; slippage moves each fill against the trader; the sell side mirrors it |
| A5 | 🎯 the stop protects from the session after the fill | fill on *d+1*; *d+1*'s low below the stop; *d+2* gaps below the stop | no stop exit on *d+1*; exit on *d+2* at `min(open, stop)` less slippage; the stop price equals `stop_price_cents(fill_cents, stop_pct)` |
| A6 | 🎯 a thesis collapse exits through the PM | a held line whose score falls under `exit_confidence_floor` | a sell recommendation, a PM-approved sell, a day limit sell on the next session, reason `thesis_exit` |
| A7 | an `adjustment-error` day books no false loss | a held line with a listed −60 % day | equity changes on that day only by the other holdings; entry and stop are rescaled; the rebase is counted; the stop does not fire on the jump |
| A8 | a held line whose bars end is exited and counted | one line ends with its episode, one while its episode continues | exits at the last close with `data_end` / `membership_end` respectively; both counted |
| A9 | 🎯 one return metric | the fixture's equity points | `summary.json`'s performance equals `calculate_performance(points, spy_closes, rolling_sessions=20)` exactly |
| A10 | the universe modes | a fixed list of 3 lines vs the index | list mode considers only those lines (when they have bars); index mode only members on *d* |
| A11 | 🪤 a cache without volume is refused | the S233 header (no `volume`) | `run` exits non-zero naming the missing column; `--describe` reports volume absent |
| A12 | the old dataset's request does not move | `requests.get` faked | `daily_bars(["AAA"], "2020-01-02")` sends today's params and returns 5-tuples; `with_volume=True` returns 6-tuples; S233-A2 still passes unchanged |
| A13 | volume survives chaining | a line with a source switch | prices rescaled as S233-A4 proves; volumes unchanged |
| A14 | the context files | fake fetchers | `sp500_benchmark.csv.gz` has one SPY row per session, pinned `asof` the end; `sp500_vix.csv.gz` covers the sessions; `bars.csv.gz` and `vix.csv.gz` are byte-identical before and after |
| A15 | sectors, paced and parsed by the provider | a fake Finnhub returning an industry, `{}`, and malformed JSON | one call per distinct symbol, ≥ 1 s apart (inject the clock); rows for all three, sector empty for the last two; the harness counts member-sessions without a sector |
| A16 | 🪤 outputs never land in the repo | `--out` inside the worktree | refused, naming the path; nothing written |
| A17 | determinism | two runs, same arguments | byte-identical `equity.csv`, `fills.csv`, `sessions.csv`, `summary.json` |
| A18 | the absent inputs are counted | the fixture run | `summary.json` names pillars present `technical`, `relative_strength`; earnings filter skipped on every evaluation; deliberator absent on every session; the counters of A7, A8, A15 |
| A19 | the existing S231/S233 guarantees hold | S231-A1…A14, S233-A1…A11 | all pass |

---

## Success factors

- [x] Part A: the universe build writes volume, SPY bars and VIX; `sectors` writes the sector table;
      the default `daily_bars` request and `bars.csv.gz`/`vix.csv.gz` are unchanged (A12–A15).
- [x] Part B: one command replays a date range through the fleet's own functions (A2) with the fleet's
      settings (A3), without look-ahead (A1), with the broker's day-limit and stop mechanics (A4–A6).
- [ ] Every absent input DL-232 names is counted in the summary (A18); untrusted days and ended lines
      are handled explicitly (A7, A8).
- [x] The only return metric is the reporter's (A9); outputs stay outside the repo (A16) and are
      deterministic (A17).
- [x] A synthetic 500-line × 300-session run's wall time is measured and reported.
- [x] DL-234 recorded with rejected alternatives.
- [x] Every guard planted, watched to fail, restored — stated per guard.
- [x] Every touched module < 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The scanner's `lookback_days = 5` is not the live window.** The served path uses it; graph-pull
runs ship ~203 bars and the scanner computes relative strength and average volume over all of them
(row 3, DL-233). Cut the window with `declared_lookback_days`, not with the scanner setting.
🪤 **A held line's stop must not be applied twice.** The analyst has its own stop-breach path for held
names without an active broker stop. The simulated broker holds the stop, so mark every held stop ref
active; otherwise a breach produces a sell recommendation *and* a stop fill.
🪤 **`PortfolioState.cash` is the account's equity, not its cash** (`equity_value` returns
`cash.amount`, and `available_for_buys` subtracts `deployed_value`). Build it the way
`graph_portfolio.py` does, or sizing doubles.
🪤 **A limit order is not a market order.** A gap above a buy's limit means no fill, and that must show
up in the expired count, not as a fill at the open.
🪤 **Row 7 is an assumption.** Write the stop-activation rule in one place, named, so E17.4 can change it.
🪤 **Two pinned series differ by a constant factor.** SPY's bars are pinned to the build's end like
every window; compare returns, never levels.
🪤 **`replay_universe.py` is 194 lines.** One more subcommand pushes it over; move code out first.
🪤 **Your worktree has no network.** The rebuild, the sector fetch and the first real replays are the
planner's after merge. Do not claim them.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`). `scripts/` is not a
  root package, and scripts already import agents (`scripts/backtest_proposal.py`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` except the scripts' existing
  `E402` path idiom.
  📌 Near the block: `scripts/replay_universe.py` **194**, `scripts/sp500_wiki.py` **197**,
  `scripts/sp500_membership.py` **181**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: the slippage default, the Finnhub pacing and the rolling window are named constants
  citing their reason (the plan's 10 bps middle arm; Finnhub's 60/min; the reporter's 20 sessions).
- Faults, not silent failure: a refused cache, an unknown setting or an output path in the repo raises,
  naming what it found.
- `make ci` **every step** green, **100.00 % coverage floor**, **redirected to a file, never piped**.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**, run from the worktree whose
   `HEAD` is the commit being proven; check the printed SHA against `git rev-parse HEAD`.
2. Merge to `main` locally and push. Post-merge CodeQL.
3. **No deploy.** `scripts/` ships in no image.
4. **Planner's live checks (the functionality check)**, from the main checkout with `.env`:
   - **Rebuild** `replay_universe.py build --end <last session> --from-snapshot`. **Pass:** coverage and
     episodes as S233's (99.993 %, 732, 0 unreconciled, 12 switches); **every OHLC value identical** to
     the pre-rebuild cache over the shared range (only the `volume` column is new); volume present on
     every row; SPY has one row per session; VIX covers every session; `bars.csv.gz` and `vix.csv.gz`
     SHA-256 unchanged; `git status` clean.
   - **Sectors** `replay_universe.py sectors`. Record the coverage (symbols with a sector / all, and the
     share of member-sessions covered).
   - **Smoke replay, live list:** `run --start 2026-08-10 --end <last session> --universe-file
     scripts/universe_sp100.txt`. Not a fidelity check: record candidates per session (live: 17–24 on
     IEX volume; expect more on SIP), approvals, fills, the summary's counters, and the wall time.
   - **Ten-year replay, index:** `run --start 2016-01-04 --end <last session>`. Record the summary
     numbers and the wall time in `docs/laws/functionality-checks.md`. **No verdict:** that is EXP-014,
     after E17.4 has measured fidelity.

---

## Handover — paste this to Codex

```text
Sprint 235 — the pipeline replays a day it has not seen, with its own code and the fleet's settings
(P17 E17.3). Spec: docs/sprints/sprint-235-the-pipeline-replays-a-day-it-has-not-seen.md (read all).

Branch: sprint-235-the-pipeline-replays-a-day-it-has-not-seen, in its own worktree. Never main.
You have NO .env and NO network. Every proof is on SYNTHETIC fixtures; never commit Alpaca data or
any replay output (equity curves and fills derive from licensed prices).

Why: P17 must say whether the pipeline has an edge over ten years of the S&P 500 as it stood. The
universe cache exists (S231/S233); nothing drives the pipeline over it. DL-232 settled the scope:
price-only (technical + relative strength), fundamentals/sentiment/earnings/deliberator absent and
COUNTED, point-in-time S&P 500 plus a fixed-list mode, SIP volume, the reporter's metric.

MUST RULE before any code: read the laws of every agent whose function you call (scanner, analyst,
PM, provider, execution, reporter), docs/laws/conventions.md, docs/laws/drift-register.md, CLAUDE.md,
DL-227, DL-229, DL-232, and the licensing rule in scripts/replay_dataset.py. Fill the Law reading
record first. Law-cycle answer expected: NO. If calling an agent function needs ANY change under
agents/, contracts/, kernel/ or orchestration/: STOP and report.

Part A (cache):
1. daily_bars(..., with_volume=False): default request AND 5-tuple return unchanged; True adds `v`.
2. sp500_bars.csv.gz gains `volume`; chaining rescales prices only, volume unchanged. The loader reads
   old and new caches and says which; the harness refuses a cache without volume, naming the column.
3. The build also writes sp500_benchmark.csv.gz (SPY, SIP, adjustment=all, asof=end) and
   sp500_vix.csv.gz (vix_history over the sessions). bars.csv.gz / vix.csv.gz untouched.
4. New subcommand `sectors`: Finnhub /stock/profile2 per distinct symbol, <= 1 call/s, parsed with
   agents.provider.fundamentals_parse._parse_sector, -> sp500_sectors.csv.gz (empty sector if none).
5. --describe: volume present, benchmark sessions, VIX range, sector coverage.
Part B (harness), each stage the fleet's OWN function, called not copied:
6. Session d: members on d (or --universe-file), bars in declared_lookback_days(AnalystSettings,
   as_of=d, staleness_buffer_sessions=ProviderSettings.max_staleness_days) calendar days ending d
   (203 bars live), SPY same window, VIX on d. OHLCVBar with the LINE as ticker.
7. Settings = code defaults + orchestration/packs/trading_tunables.json apps + --set KEY=VALUE
   (pack env names). Unknown key -> error naming it.
8. classify_regime -> RegimeContext(base_* from ProviderSettings) -> apply_filters(earnings={},
   earnings_horizon_days=None) -> rank_survivors(cap) -> scoring_universe(held) -> score_candidates
   (fundamentals/news/sentiment empty; held stops with EVERY ref active) -> split_decisions ->
   evaluate_recommendations(args as run_evaluation passes; PortfolioState built like
   graph_portfolio.py: cash field = equity).
9. Broker: approved intent -> DAY LIMIT order for d+1 at resolve_order_tolerance(...).applied_limit_price;
   buy fills min(open, limit) if low <= limit else expires (counted); sell mirrors; --slippage-bps
   (default 10) against the trader. After a buy fill: GTC stop at stop_price_cents(fill, stop_pct),
   active from the session AFTER the fill (assumed; one named place); fills at min(open, stop).
10. Listed adjustment-error day: rescale a held line's entry and stop by the day's ratio, no stop on
    the jump, counted. A held line whose bars end: sell at last close, data_end or membership_end.
11. Equity points (d, equity_cents, long_cents) -> agents.reporter.domain.performance
    .calculate_performance(points, spy_closes, rolling_sessions=20). No other return formula.
12. `scripts/replay_pipeline.py run ...` writes equity.csv, fills.csv, sessions.csv, summary.json
    (performance, non-default settings, absent-input counters) under the cache dir; an --out inside
    the worktree is refused. Same arguments -> byte-identical files.

Order: DL-234 (DL-235 is S236's; re-check both) -> red A1/A2/A4/A6 -> implement -> DL-70 plants
(window includes d+1; inlined rank_survivors; settings from defaults only; gapped buy filled at the
open; stop armed on its fill session; local return formula — each must go red; restore) -> measure a
synthetic 500-line x 300-session run's wall time -> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- change anything under agents/, contracts/, kernel/, orchestration/ (stop and report).
- copy or re-implement any stage, the tolerance, the stop rule or the return metric.
- approximate fundamentals, sentiment, earnings dates or the deliberator (DL-232: absent, counted).
- use the scanner's lookback_days as the bar window.
- change daily_bars' default request or return shape, replay_dataset.py, load(), bars.csv.gz,
  vix.csv.gz.
- grow replay_universe.py (194), sp500_wiki.py (197) or sp500_membership.py (181) past 200.
- write any output inside the worktree, or commit any cache or replay file.
- claim a live proof: the rebuild, sectors and first replays are the planner's after merge.
- pin a version: MINOR, next available at merge, uv.lock staged with it.

Handback: Law reading record, Test plan results, Closeout (red then green, DL-70 plants, line counts,
wall time, make ci file + exit code), Return notes. Status: BUILT, and this sprint's README.md row
leads with BUILT in the same commit. Commit your work on the branch (the planner pushes and gates
it). Anything not met: "not done".
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
| Cache and licensing boundary | `CLAUDE.md`; `docs/laws/conventions.md`; `docs/laws/drift-register.md`; `scripts/replay_dataset.py` docstring; DL-227; DL-229; DL-232 | LAW-02 proof discipline; LAW-06 decision capture; conventions sections 2, 3, 7, 9; replay cache must stay outside the worktree and derived outputs inherit that rule; DL-227/DL-229 pin membership, as-of bars and raw-close chaining; DL-232 limits this to price-only replay | Yes. Replay output is treated like licensed-derived cache output: tests use synthetic fixtures only, and the harness must refuse in-worktree output paths. |
| Scanner stage | `agents/scanner/laws/laws.md`; `agents/scanner/laws/test-plan.md` | SCAN-IDN-01, SCAN-OUT-02, SCAN-OUT-06, SCAN-OUT-07, SCAN-NEV-02, SCAN-IDM-01, SCAN-TYP-01 | Yes. The harness calls `apply_filters` and `rank_survivors`; absent earnings must be recorded as skipped, not silently passed, and scanner ranking must stay price/relative-strength only. |
| Analyst stage | `agents/analyst/laws/laws.md`; `agents/analyst/laws/test-plan.md`; ADR-0017 | ANLZ-IDN-01, ANLZ-OUT-01..03, ANLZ-OUT-07, ANLZ-NEV-01..03, ANLZ-IDM-01, ANLZ-OBS-06, ANLZ-TYP-01/02 | Yes. Fundamentals, sentiment and earnings history stay absent; the analyst receives price bars and held stops, emits recommendations only, and never sizes orders. Held thesis exits come from low confidence under ADR-0017. |
| Portfolio-manager stage | `agents/portfolio_manager/laws/laws.md`; `agents/portfolio_manager/laws/test-plan.md`; ADR-0012; ADR-0029 | PM-IDN-01, PM-OUT-01..03, PM-NEV-01..09, PM-STA-03, PM-IDM-01, PM-OBS-03..05, PM-TYP-01..03 | Yes. The harness must build the same `PortfolioState` shape the graph path passes, use the pack issuer map as pack data, preserve gate reports/rejections, and never treat PM output as broker execution. |
| Provider/regime and sectors | `agents/provider/laws/laws.md`; `agents/provider/laws/test-plan.md`; `agents/provider/fundamentals_parse.py`; DL-232 | PROV-OUT-02, PROV-OUT-03, PROV-NEV-07, PROV-NEV-08, PROV-TYP-03, PROV-SEC-02, provider PARAM rows for base regime defaults and Finnhub pacing | Yes. Regime context must expose the provider base defaults and VIX evidence; sector parsing must reuse `_parse_sector`; missing sectors stay empty/countable rather than fabricated. |
| Execution mechanics | `agents/execution/laws/laws.md`; `agents/execution/laws/test-plan.md`; ADR-0018; `contracts/stop_rule.py` | EXEC-OUT-07, EXEC-OUT-08, EXEC-NEV-01..03, EXEC-OBS-03, EXEC-OBS-06, EXEC-TYP-01..03 | Yes. The simulated broker can model fills, expirations and stops, but it must call the existing tolerance and stop-rule functions rather than copy their formulas. Buy-only deliberation/degraded posture is out of scope because the deliberator is absent and counted. |
| Reporter metric | `agents/reporter/laws/laws.md`; `agents/reporter/laws/test-plan.md`; DL-232 | RPT-OUT-07, RPT-IDM-03, RPT-FAIL-04, RPT-TYP-01, reporter PARAM `performance_rolling_sessions` | Yes. `summary.json` performance must come directly from `calculate_performance(..., rolling_sessions=20)`; no local return formula belongs in the harness. |
| Live window and settings inputs | `orchestration/history_window.py`; `orchestration/start.py`; `orchestration/packs/trading_tunables.json`; `orchestration/packs/trading_issuer_map.json`; ADR-0012 | ADR-0012 pack-data boundary; scanner/analyst/PM/provider/execution PARAM rows named above | Yes. The replay must layer code defaults, then the pack's `apps` values, then explicit `--set` overrides, and unknown keys fail loudly. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No. The sprint adds scripts/tests that call existing domain functions and refuse to continue if doing so requires changes under `agents/`, `contracts/`, `kernel/` or `orchestration/`.

**Contradictions found between a law and this spec:** None found. Existing drift DRIFT-039 says PM law text still names a `portfolio_state_snapshot` not present in production code; this sprint does not add that graph guarantee and follows the spec's replay-only `PortfolioState` construction instead.

**Laws found silent where a decision was needed:** Agent laws do not bind scripts; this spec's test plan is the script contract. Execution law does not define replay stop activation timing; the sprint's row 7 supplies the harness assumption, recorded in DL-234 as a single named rule for E17.4 to re-measure.

**Clauses that were ⬜ and are now proven:** None at law-reading time; this sprint proves script behavior against S235-A* rows, not new agent-law rows.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_window_bars_include_session_but_not_next_session` | `tests/test_replay_series.py` | PASS | S235-A6 |
| A2 | `test_regime_context_uses_provider_base_settings` | `tests/test_replay_regime.py` | PASS | S235-A2 |
| A3 | `test_pack_settings_override_code_defaults`; `test_cli_set_uses_pack_env_names_and_reports_unknown_key` | `tests/test_replay_settings.py` | PASS | S235-A3 |
| A4 | `test_buy_limit_waits_for_next_session_and_expires_on_gap` | `tests/test_replay_broker.py` | PASS | S235-A4 |
| A5 | `test_stop_arms_after_fill_session_and_rebases_without_jump_fill` | `tests/test_replay_broker.py` | PASS | S235-A5 |
| A6 | `test_replay_day_calls_fleet_stages_in_order` | `tests/test_replay_day.py` | PASS | S235-A6 |
| A7 | not implemented | — | not done | Listed adjustment-error rebases are not implemented in the runner. |
| A8 | not implemented | — | not done | Data-end / membership-end forced exits are not implemented in the runner. |
| A9 | `test_outputs_are_byte_identical_and_reporter_metric_is_called` | `tests/test_replay_outputs.py` | PASS | S235-A9/A17/A18 |
| A10 | not implemented | — | not done | `--universe-file` fixed-list mode is not implemented. |
| A11 | `test_loader_reports_old_cache_without_volume`; `test_pipeline_refuses_cache_without_volume` | `tests/test_sp500_context.py` | PASS | S235-A11 |
| A12 | `test_daily_bars_start_default_is_backward_compatible` | `tests/test_replay_universe.py` | PASS | S235-A12 |
| A13 | `test_volume_is_requested_for_replay_windows` and existing chain tests | `tests/test_sp500_bars.py`, `scripts/sp500_chain.py` | PASS | S235-A1/S235-A13 |
| A14 | `test_context_files_write_benchmark_and_vix`; `test_universe_build_leaves_existing_replay_cache_untouched` | `tests/test_sp500_context.py`, `tests/test_replay_universe.py` | PASS | S235-A14 |
| A15 | `test_sectors_are_paced_and_parsed` | `tests/test_sp500_context.py` | PASS | S235-A15 |
| A16 | `test_out_path_inside_worktree_is_refused` | `tests/test_replay_outputs.py` | PASS | S235-A16 |
| A17 | `test_outputs_are_byte_identical_and_reporter_metric_is_called` | `tests/test_replay_outputs.py` | PASS | S235-A17 |
| A18 | `test_replay_day_calls_fleet_stages_in_order`; `test_outputs_are_byte_identical_and_reporter_metric_is_called` | `tests/test_replay_day.py`, `tests/test_replay_outputs.py` | PASS | S235-A18 |
| A19 | focused S231/S233 regression subset plus full `make ci` | `tests/test_replay_universe.py`, `tests/test_sp500_bars.py`, full gate | PASS | S235-A19 |

**Tests added beyond the plan:** `tests/test_replay_series.py` isolates the no-lookahead guard; `tests/test_replay_regime.py` keeps the provider-base context proof below the module-size hard block.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\trading-agents-sprint-235-the-pipeline-replays-a-day-it-has-not-seen`, branch `sprint-235-the-pipeline-replays-a-day-it-has-not-seen`; no `.env` present/used; no network proof claimed.

**Result:** Built a synthetic-fixture replay harness and cache context layer in `scripts/`: `daily_bars(..., with_volume=False)` remains backward-compatible and `with_volume=True` adds volume; universe cache writes/loads volume and refuses no-volume harness runs; build writes SPY benchmark and VIX context; `sectors` writes a paced Finnhub sector cache using the provider parser; `replay_pipeline.py run` delegates scanner/analyst/PM/provider/execution/reporter stages to existing fleet functions, writes deterministic outputs outside the worktree, and counts DL-232 absent inputs. Not done: adjustment-error rebases, forced data-end/membership-end exits, and `--universe-file` fixed-list mode.

**Files changed:** `scripts/replay_dataset_sources.py`, `scripts/sp500_bars.py`, `scripts/sp500_chain.py`, `scripts/replay_universe_cache.py`, `scripts/replay_universe.py`, plus new `scripts/sp500_context.py`, `scripts/replay_settings.py`, `scripts/replay_broker.py`, `scripts/replay_cache.py`, `scripts/replay_day.py`, `scripts/replay_ledger.py`, `scripts/replay_outputs.py`, `scripts/replay_pipeline.py`, `scripts/replay_runner.py`, `scripts/replay_series.py`; tests under `tests/test_replay_*`, `tests/test_sp500_*`; docs/state/version files; `pyproject.toml` / `uv.lock` bumped to `0.115.00`.

**Design decisions:** DL-234 in `docs/design-log.md` records field-mapped fleet settings, a script-local replay ledger, indexed cache slicing without scanner-lookback misuse, module splits, and named stop timing; rejected alternatives are in the same DL row.

**Proof — the red run first:**

```text
uv run pytest tests/test_replay_universe.py tests/test_sp500_bars.py tests/test_sp500_context.py tests/test_replay_settings.py tests/test_replay_broker.py tests/test_replay_outputs.py tests/test_replay_day.py --no-cov > $env:TEMP\s235-red.txt 2>&1; $LASTEXITCODE
2
collected 8 items / 5 errors
ModuleNotFoundError: No module named 'scripts.sp500_context'
ModuleNotFoundError: No module named 'scripts.replay_settings'
ModuleNotFoundError: No module named 'scripts.replay_broker'
ModuleNotFoundError: No module named 'scripts.replay_outputs'
ModuleNotFoundError: No module named 'scripts.replay_day'
```

**Proof — the green run:**

```text
uv run pytest tests/test_replay_universe.py tests/test_sp500_bars.py tests/test_sp500_context.py tests/test_replay_settings.py tests/test_replay_broker.py tests/test_replay_outputs.py tests/test_replay_day.py tests/test_replay_series.py --no-cov > $env:TEMP\s235-focused-8.txt 2>&1; $LASTEXITCODE
0
22 passed in 3.26s

uv run ruff check ... > $env:TEMP\s235-ruff-check-6.txt 2>&1; $LASTEXITCODE
0
All checks passed!

uv run mypy --explicit-package-bases ... > $env:TEMP\s235-mypy-focused-6.txt 2>&1; $LASTEXITCODE
0
Success: no issues found in 22 source files
```

**Guards planted:** d+1 window inclusion planted in `window_bars` → `tests/test_replay_series.py` failed, restored; inlined/no `rank_survivors` planted → `tests/test_replay_day.py` failed, restored; settings defaults-only planted → `tests/test_replay_settings.py` failed, restored; gapped buy fill planted → `tests/test_replay_broker.py::test_buy_limit_waits_for_next_session_and_expires_on_gap` failed, restored; stop armed on fill session planted → `tests/test_replay_broker.py::test_stop_arms_after_fill_session_and_rebases_without_jump_fill` failed, restored; local return formula planted → `tests/test_replay_outputs.py::test_outputs_are_byte_identical_and_reporter_metric_is_called` failed, restored.

**Module line counts:** `scripts/replay_universe.py` 195; `scripts/sp500_wiki.py` 197; `scripts/sp500_membership.py` 181; `scripts/replay_runner.py` 147; `scripts/replay_series.py` 108; `scripts/replay_ledger.py` 147; `scripts/sp500_context.py` 194; `scripts/replay_day.py` 175; `scripts/replay_settings.py` 145; `scripts/replay_cache.py` 83; `scripts/replay_outputs.py` 80; `scripts/replay_broker.py` 124; `scripts/replay_pipeline.py` 45; `tests/test_replay_day.py` 196; `tests/test_replay_regime.py` 35; `tests/test_replay_series.py` 28.

**Synthetic run wall time:** 500 lines × 300 sessions synthetic cache under `%TEMP%`: `elapsed_seconds=385.539` (`C:\Users\yury_\AppData\Local\Temp\s235-500x300-mdzgbnhz`), on this Windows worktree machine.

**`make ci`:** `make ci > $env:TEMP\s235-make-ci-final.txt 2>&1; $LASTEXITCODE` -> exit `0`; `3324 passed, 6 skipped`; `Required test coverage of 100.0% reached. Total coverage: 100.00%`; dependency audit accepted only existing `PYSEC-2026-2447` diskcache advisory; tracked detect-secrets passed; untracked secret scan passed over 19 new files.

**`make gate-ran`:** not done; planner runs after push/remote gate.

**Not met / verified failing:** A7 adjustment-error rebase not done; A8 data_end/membership_end forced exits not done; A10 `--universe-file` fixed-list mode not done; no live rebuild, sectors fetch or replay proof claimed.

---

## Return notes

- Built on branch `sprint-235-the-pipeline-replays-a-day-it-has-not-seen` in its own worktree; `main` unchanged.
- Proof is synthetic-fixture only. The planner still owns live cache rebuild, sector fetch, smoke replay, remote push/gate, merge and any live result claims.
- The branch includes S236's spec and README row as SPEC because its untracked handover was copied into this worktree and the sprint-status gate requires it to be indexed.
