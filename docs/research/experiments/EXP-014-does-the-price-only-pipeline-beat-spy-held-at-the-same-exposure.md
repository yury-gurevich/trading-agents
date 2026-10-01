# EXP-014 — Does the price-only pipeline earn more than SPY held at the same exposure, over the index as it stood?

**Status:** PRE-REGISTERED 2026-10-01 (planner). **No scored run exists under this design.** Sections
1–5 and Appendix P are fixed before the first one. A change of design after it is a new experiment.
**Decision / origin:** next-leg plan E17.5 ([next-leg-plan.md](../../next-leg-plan.md)), work-queue
**82** · scope [DL-232](../../design-log.md) · fidelity gate [DL-237](../../design-log.md) · this design
[DL-257](../../design-log.md) · tooling
[S250](../../sprints/sprint-250-a-replays-excess-return-comes-with-an-interval-and-a-verdict.md) ·
**Cost:** $0 of LLM spend; about 7 hours of local compute.

## 1. Why we needed this experiment

**The decision that waits.** G-EDGE: the operator chooses between putting an edge to work (P18A:
capital deployment, pillar reweighting, a signal-discovery loop) and freezing the trading pack as the
platform's reference workload (P18B). It is a capital-risk decision and it is the operator's. This
experiment is its input, and nothing else in the next leg can start before it.

**What building without it would risk.** Three more sprints tuning a pipeline that only harvests
market exposure, or freezing one that has an edge nobody measured.

**What earlier evidence says.**

- **Live** (the brief for `sched-2026-09-30`): the book is **−0.60 pts** behind SPY held at the same
  exposure, over **36 sessions** at **22 %** invested. Thirty-six sessions cannot tell skill from luck.
- **One smoke replay** (S235, 2026-09-27, 10 bps, 2016-01-04 → 2026-09-25): portfolio **+217.9 %**,
  exposure-matched SPY **+232.2 %**, excess **−14.3 pts**, average exposure 78.5 %. It was recorded as a
  smoke run, not a verdict, and it has no interval.
- **That smoke run decided on history the fleet never has** *[measured 2026-10-01]*. The cache starts
  on 2016-01-04, so **113 of its 552 buys** were decided on fewer than 200 bars: 103 in 2016, 10 on
  lines that had just joined the index, 57 on fewer than 50 bars, the least on 11. A fleet run
  declares a lookback that covers 200 sessions (`required_history_bars`), and its names arrive with
  203 bars each. This experiment removes that defect before it scores anything.
- **EXP-011, EXP-012, EXP-013** each replayed one mechanism (barrier ratios, volatility sizing, regime
  sizing) on today's 98 survivors. None replayed the whole pipeline, and each carried a survivorship
  caveat. This experiment runs on the index as it stood, so that caveat is closed here.

## 2. Hypothesis

**The statistic.** *Annualised excess return over exposure-matched SPY*, in percentage points a year:

`A = ((1 + P/100)^(252/n) − (1 + E/100)^(252/n)) × 100`

where `P` is `portfolio_return_pct`, `E` is `exposure_matched_return_pct` and `n` is
`performance_sessions`, all three as returned by
`agents/reporter/domain/performance.calculate_performance`, the function the live `Snapshot` uses.
Exposure-matched SPY holds, each session, the fraction of equity the book had invested at the previous
close, and holds the rest in cash at 0 %.

- **H1 — edge.** On the arm `base-25` (the fleet's settings, 25 bps of slippage a side), `A > 0` and
  the lower bound of its 95 % interval is above 0.
- **H2 — edge in one pillar.** H1 fails, and for an ablation arm `X` (`technical-only-25` or
  `relative-strength-only-25`) the lower bound of `A`'s 95 % interval is above 0 **and** the lower
  bound of the paired difference `A(X) − A(base-25)` is above 0.
- **H0 — no edge.** Neither holds. Reported with one of two readings: *behind* (the upper bound of
  `base-25`'s interval is below 0) or *indistinguishable* (the interval contains 0).

**Why this bar.** It is the plan's own rule, written on 2026-09-23 before any replay existed: *"excess
return over exposure-matched SPY, with a lower CI bound above 0, survives 25 bps of slippage."* The
paired condition on H2 is there because two extra arms are two extra chances to pass by luck: an
ablation must beat the full pipeline on the same days, not only beat zero.

## 3. Data

**Source.** The S235 cache in OneDrive `trading-agents-data` (never the repo: the repo is public and
SIP bars are licensed). Alpaca SIP daily bars, `adjustment=all` (splits and dividends) for the stocks
and for SPY alike, so both sides are total-return series *[measured, read:
`scripts/replay_dataset_sources.py:61`, `scripts/sp500_context.py:55`]*.

**Universe.** The S&P 500 as it stood each day (S231, S233): **732** membership episodes, **721**
lines with bars, **1,360,156** bars, 2016-01-04 → 2026-09-25, **2,698** sessions; SPY and VIX on every
session; Finnhub sectors for 724 lines *[measured 2026-10-01]*.

**Files, frozen for this experiment** (SHA-256 prefix, bytes):

| File | SHA-256 prefix | Bytes |
| --- | --- | --- |
| `sp500_bars.csv.gz` | `198cffbb3542` | 22,675,629 |
| `sp500_benchmark.csv.gz` | `f40b8b60506a` | 50,036 |
| `sp500_membership.csv.gz` | `db971f1b3b95` | 5,474 |
| `sp500_sessions.csv.gz` | `15ba1326e091` | 5,417 |
| `sp500_vix.csv.gz` | `f80fa60b3ed9` | 12,567 |
| `sp500_sectors.csv.gz` | `7a6801c55f21` | 4,638 |

**The scored window.** 2017-01-03 → 2026-09-25: **2,446** sessions, 9.7 years. The 252 sessions of
2016 are history only; no decision is made in them.

**Known defects in the data, each counted in every arm's summary.**

- **No bars before a line joins the index.** 187 lines have their first bar after 2016. In the world,
  the fleet would have had their earlier history. Here a line is not offered to the pipeline until its
  window holds the 200 bars the analyst is always given; held lines stay visible. The member-sessions
  this removes are counted.
- **No bars after a line leaves the index.** A held line exits at its last member close (DL-232).
- **No fundamentals, sentiment, news or earnings dates, and no deliberator** (DL-232). The weights
  renormalise as they do live when those feeds degrade.
- **Sectors** are today's Finnhub industries; a delisted line may have none.
- **Four known Alpaca adjustment errors** (S233) are handled by the harness's rebases and counted.

## 4. Tools and setup

- **Machine.** Intel Core (family 6, model 142), 4 logical cores, 16 GB RAM, Windows 10 Pro.
- **Software.** Python 3.13.2, uv 0.8.14. The scoring uses the standard library only; the harness
  uses the repo's own packages.
- **Repo commit.** The commit that merges S250. Each arm writes it to its `arm.json`, and the scorer
  refuses arms from different commits.
- **Random seed.** 0, for the bootstrap. The replay itself has no randomness.
- **External services.** None. No network, no LLM call, no broker.
- **Cost cap.** $0.

## 5. How it was conducted

1. **Gate.** The run starts only when E17.4's fidelity verdict reads **PASS** (`scripts/replay_fidelity.py`,
   DL-237). It reads INSUFFICIENT until four clean sessions exist. On FAIL this experiment does not
   run, and the gap becomes the work (the plan's rule).
2. **Arms.** Five replays, each over the point-in-time index, `--start 2017-01-03`, to the cache's
   last session, with the history rule on and the fleet's committed pack settings:

   | Arm | Slippage a side | Setting changed |
   | --- | --- | --- |
   | `base-05` | 5 bps | none |
   | `base-10` | 10 bps | none |
   | `base-25` | 25 bps | none |
   | `technical-only-25` | 25 bps | `ANALYST_RELATIVE_STRENGTH_WEIGHT=0.0` |
   | `relative-strength-only-25` | 25 bps | `ANALYST_RELATIVE_STRENGTH_WEIGHT=1.0` |

   The analyst blends `(1 − w) × technical + w × relative strength` with `w = 0.20` live
   (`agents/analyst/domain/scoring.py`), so `w = 0` and `w = 1` are the two drop-one ablations of
   DL-232. No other setting moves. The scanner's own relative-strength filter is not part of the
   ablation.
3. **What each arm receives.** Per session: the members' bars up to that session, SPY bars, VIX, the
   book's own holdings and stops, and sectors. The fleet's scanner, analyst and PM functions decide;
   the harness's broker fills day limit orders on the next session and stops when touched, moves every
   fill against the trader by the arm's slippage, and marks the book daily.
4. **Scoring.** Each arm's daily equity and invested value go through `calculate_performance` with
   the cached SPY closes: once over the whole scored window, and once per calendar year (2017 … 2026,
   the last partial). A session pair belongs to the year of its later session. Nothing is fitted, so
   there is no training window and nothing to purge; the years are evaluation blocks.
5. **Interval.** A stationary block bootstrap over session pairs: mean block length **20** sessions,
   **10,000** resamples, seed **0**, wrapping at the end. One set of index draws is applied to every
   arm, so arms are compared on the same resampled days. Each resampled series is rebuilt and scored
   by `calculate_performance`; `A` is computed from its outputs. The interval is the 2.5th and 97.5th
   percentiles of the 10,000 draws.
6. **Verdict.** Section 2's rule, applied by code to the five arms.
7. **Controls.** (a) A replica that earns exactly SPY at `base-25`'s exposure each day must score
   `A = 0` with an interval of [0, 0]. (b) Scoring twice gives byte-identical output.
8. **Failure handling.** The scorer gives no verdict, and says why, when: an arm is missing; arms
   differ in commit, cache checksums, sessions or history rule; an arm has a gap session; or a control
   fails. A failed or interrupted replay is re-run whole; no arm is patched.
9. **Reported, not barred.** `base-05` and `base-10` (the slippage sweep); each arm's return against
   SPY itself; the per-year table and the count of years with positive excess; the two halves of the
   window; maximum drawdown; average exposure; buys a year; exits by reason; every absent-input
   counter, including the member-sessions the history rule removed.

**What this experiment cannot claim, stated before the result.**

- **It speaks for the price-only pipeline.** Live, the price-only and the full pipeline share a median
  57 % of approvals (S237).
- **It is not a clean holdout.** The pack's settings were chosen with this decade in view (EXP-010 to
  EXP-013, on today's survivors). That bias runs toward finding an edge, so it weakens an EDGE
  verdict and leaves a NO EDGE verdict standing.
- **One smoke run was seen first.** Its −14.3 pts came from older code and included the short-history
  buys. The pass bar predates it; the block length, the yearly windows, the annualisation and the
  ablation rule were fixed today, after it.
- **The universe is the S&P 500; the fleet trades a 99-name list.** The replayed book is about 78 %
  invested where the live book is about 22 %.
- **The interval assumes the future resembles the decade resampled.**

## 6. Results

*Pending — written from the recorded run.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending. The verdict goes into an ADR, and the planner brings the operator one recommendation for
G-EDGE.*

## Appendix P — Pre-registration (frozen)

Frozen at the commit that adds this file (`git log --diff-filter=A` on this path). Never edited.

- **Statistic.** `A = ((1 + P/100)^(252/n) − (1 + E/100)^(252/n)) × 100`, with `P`, `E`, `n` from
  `calculate_performance` over the scored window.
- **Scored window.** 2017-01-03 → 2026-09-25, 2,446 sessions, on the cache files and checksums of
  section 3.
- **Arms.** `base-05`, `base-10`, `base-25`, `technical-only-25` (`ANALYST_RELATIVE_STRENGTH_WEIGHT=0.0`),
  `relative-strength-only-25` (`ANALYST_RELATIVE_STRENGTH_WEIGHT=1.0`); slippage 5, 10, 25, 25, 25 bps
  a side; point-in-time index; history rule on; the fleet's committed pack settings otherwise.
- **Interval.** Stationary block bootstrap over session pairs, mean block 20, 10,000 resamples, seed
  0, one set of draws for all arms, percentile 2.5 / 97.5.
- **Verdict.** EDGE: `base-25`'s lower bound > 0. EDGE IN A PILLAR: not EDGE, and an ablation arm's
  lower bound > 0 with the lower bound of its paired difference from `base-25` > 0. NO EDGE otherwise,
  read as *behind* when `base-25`'s upper bound < 0 and *indistinguishable* when its interval contains 0.
- **Gate.** E17.4's verdict reads PASS before the first arm starts.
- **Controls.** The exposure-matched replica scores 0 with interval [0, 0]; scoring is byte-stable.
- **No verdict** when an arm is missing or the arms differ in commit, cache, sessions or history rule,
  when an arm has a gap session, or when a control fails.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

*Pending. The scripts are S250's, in `scripts/`; the commands used are recorded here at the run.*
