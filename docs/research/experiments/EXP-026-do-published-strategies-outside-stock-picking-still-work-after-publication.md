# EXP-026 — Do nine published strategies outside single-stock picking still work after they were published?

**Status:** PRE-REGISTERED 2026-10-24 (planner). Sections 1–5 and Appendix P are fixed before the first
strategy is computed; a change of design after it is a new experiment.
**Decision / origin:** the operator, 2026-10-24: *"search promising strategies OUTSIDE THIS PROJECTS
MENTALITY. need promising paths investigated, tests/experiments done and methods adopted/rejected"* ·
[DL-318](../../design-log.md) · follows [EXP-025](EXP-025-which-way-of-managing-a-position-guards-against-a-bad-future.md)
and [R011](../where-an-edge-can-exist/INDEX.md) · **Cost:** $0 (Tiingo, Cboe and Coinbase public data;
no LLM, no broker).

## 1. Why we needed this experiment

**The decision that waits.** Whether this project has any promising path. Everything tested so far sat
inside one frame: daily picking of single S&P 500 stocks. In that frame nothing carries (EXP-015,
EXP-023, EXP-024, EXP-025), and the literature says nothing should (R011: published anomalies earn a
median 7 bp a month in non-micro stocks after 2005). The operator asked to look outside the frame:
other asset classes, crypto, volatility, the calendar, and monthly allocation across assets.

**Why published strategies, scored only after publication.** Each candidate is a strategy someone
published with its rules. Scoring it only on the months after its publication date makes the test out
of sample by construction: the rules were fixed by someone who could not see these data, and nothing
here is tuned. It answers the question an investor faces: *had I adopted this when it appeared, would
it have served me?* Decay after publication is the rule (R011: Sharpe ratios about halve), so this is
a hard test, and the right one.

**What building without it would risk.** Building a new pack around a strategy whose backtest is its
publication's own sample.

## 2. Hypothesis

**The statistic.** For each strategy *S* and its benchmark *B* (Appendix P), on the same sessions of
*S*'s post-publication window: `dSharpe = Sharpe(S) − Sharpe(B)`, each the annualised mean of daily
returns over cash divided by their standard deviation (×√252; ×√365 and cash at 0 for crypto).

**The interval.** Stationary block bootstrap over sessions (mean block 20, 5,000 resamples, seed 0),
paired: one set of index draws for *S* and *B*. Nine strategies are nine chances, so each interval is
the Bonferroni one: the 0.278th and 99.722nd percentiles (two-sided 1 − 0.05/9).

**The verdict, per strategy, by code:**

- **EDGE (adopt: build and paper-trade next)** — the interval's lower bound is above 0, `dSharpe` is
  above 0 in each half of the window, and *S*'s CAGR is at least *B*'s.
- **DEFENCE (adopt as a guard candidate)** — not EDGE; *S*'s maximum drawdown is at most 0.6 × *B*'s,
  its CAGR at least *B*'s minus 3 points, and `dSharpe` at least 0.
- **REJECT** — neither.

**Why this bar.** The operator's two aims are profit and no catastrophic loss: EDGE serves the first,
DEFENCE the second at a bounded cost (EXP-025's 200-day guard would have read DEFENCE). Sharpe, not
return, is primary because several strategies hold cash; requiring CAGR ≥ the benchmark's keeps EDGE
from rewarding a strategy that only holds less risk.

## 3. Data

| Input | Span | Where |
| --- | --- | --- |
| 22 ETFs, Tiingo daily (`adjOpen`, `adjClose`, splits and dividends): SPY, EFA, EEM, IEF, TLT, AGG, SHY, BIL, VNQ, DBC, GLD, SSO, SVXY, XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY | each from its listing (SPY 1993-01-29 … SVXY 2011-10-04) to 2026-10-23 | kit `inputs/<TICKER>.csv` |
| Cboe VIX and VIX3M closes | VIX 1990-01-02, VIX3M 2009-09-18 → 2026-10-23 | kit `inputs/VIX.csv`, `VIX3M.csv` |
| Coinbase BTC-USD and ETH-USD daily candles (UTC days) | BTC 2015-07-20, ETH 2016-05-18 → 2026-10-23 (the 10-24 candle, incomplete, dropped) | kit `inputs/BTC-USD.csv`, `ETH-USD.csv` |

The kit is OneDrive `trading-agents-data/exp026-2026-10-24/`; vendor data never enters the repo.
**Known defects:** the ETFs were chosen in 2026 among those that survived (a mild survivorship
choice); SVXY changed from −1× to −0.5× VIX futures on 2018-02-28 (the test holds what an investor
held); Coinbase is one exchange's price; Cboe's VIX3M before 2009-09-18 is not in the file and no
strategy needs it.

## 4. Tools and setup

- **Machine.** Intel Core (family 6, model 142), 4 logical cores, 16 GB RAM, Windows 10 Pro.
- **Software.** Python 3.13.2, numpy 2.5.3, pandas 3.0.6 (the repo's main venv); the script imports no
  repo code. Repo `main` at the pre-registration commit.
- **Random seed.** 0.
- **External services.** None at run time; data fetched once 2026-10-24 (Appendix R).
- **Cost cap.** $0.

## 5. How it was conducted

1. **Simulation.** One day-by-day value simulation per strategy and per benchmark. A decision is read
   at a session's close and traded at the next session's open (the fleet's cadence): the old weights
   earn the overnight move, the new ones the day. Between decisions holdings drift. Cash is BIL from
   2007-05-30, SHY before it from 2002-07-26, and 0 before that. Each trade pays 5 bps a side on the
   weight it moves (25 bps for crypto); a static benchmark is rebalanced monthly at the same cost.
   Crypto trades at the next UTC day's close.
2. **Scoring.** The window is Appendix P's, from the first session on or after the publication month's
   end + 1 to 2026-10-23. `dSharpe`, its interval and the verdict as section 2 fixes. The halves split
   the window's sessions in two.
3. **Pilot (before the freeze).** Only the benchmarks and data checks are computed: each input's span,
   gaps over 5 days, and each benchmark's CAGR over its window. No strategy is computed in the pilot.
   The script is then frozen and its SHA-256 recorded in Appendix R.
4. **Controls.** (a) A static 100 % SPY "strategy" against SPY reads `dSharpe` 0 exactly. (b) Running
   twice gives byte-identical output.
5. **Reported, not barred.** CAGR, volatility, maximum drawdown, worst month, worst day, trades a year,
   each strategy against SPY as well as its benchmark, the result at 25 bps a side for the ETF
   strategies, each calendar year, the pre-publication years where data exist, and the ETH version of
   S8.
6. **Failure handling.** No verdict, and the reason named, if an input has a gap over 5 sessions inside
   a window (crypto: 2 days), a control fails, or a strategy's window is under 5 years.

**What this experiment cannot claim, stated before the result.** Nine published strategies are a sample
of what is public, not of what works; a pass is evidence for that strategy's rules on one post-
publication window, not proof it continues. The windows differ in length and regime (S5's starts in
1999, S6's in 2016). The ETF list and the crypto exchange were chosen in 2026.

## 6. Results

*Pending — written from the recorded run.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

## Appendix P — Pre-registration (frozen)

Publication months are the planner's dating from the citations (month approximate). Every rule reads
at a close and trades at the next open (crypto: the next close).

| # | Strategy (source, published) | Rule | Benchmark | Window starts |
| --- | --- | --- | --- | --- |
| S1 | Tactical asset allocation, 5 assets (Faber, *A Quantitative Approach to Tactical Asset Allocation*, J. Wealth Mgmt, spring 2007) | At each month-end close, each of SPY, EFA, IEF, VNQ, DBC is held at 20 % if its close is above the mean of its last 10 month-end closes (this one included), else its 20 % is cash | the same five at 20 % each, always held | 2007-06-01 |
| S2 | Global equities momentum, "dual momentum" (Antonacci, *Risk Premia Harvesting Through Dual Momentum*, SSRN 2012) | At each month-end close: if SPY's 12-month total return exceeds BIL's, hold whichever of SPY and EFA has the higher 12-month return; else hold AGG | SPY | 2013-01-01 |
| S3 | Halloween, "sell in May" (Bouman and Jacobsen, AER, December 2002) | Hold SPY from the first session of November through the last session of April; cash from May through October | SPY | 2003-01-01 |
| S4 | Time-series momentum, long-only (Moskowitz, Ooi and Pedersen, JFE, May 2012) | At each month-end close, each of SPY, EFA, EEM, IEF, TLT, GLD, DBC, VNQ gets weight (1/σ) / Σ(1/σ) over all eight (σ = its last 60 sessions' daily volatility) and is held at it only if its 12-month return exceeds BIL's; the rest is cash | the same eight at the same weights, always held | 2012-06-01 |
| S5 | Industry momentum (Moskowitz and Grinblatt, JF, August 1999) | At each month-end close, hold equally the three of XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY with the highest 6-month return | the nine, equally weighted | 1999-09-01 |
| S6 | Leverage for the long run (Gayed and Bilello, SSRN, 2016) | Hold SSO (2× S&P 500) while SPY's close is above its 200-session average; cash otherwise; checked each session | SPY | 2016-10-01 |
| S7 | Short volatility with a term-structure filter (after Simon and Campasano, J. Derivatives, spring 2014) | Hold SVXY while VIX's close is below VIX3M's; cash otherwise; checked each session | SPY | 2014-04-01 |
| S8 | Crypto time-series momentum (Liu and Tsyvinski, *Risks and Returns of Cryptocurrency*, NBER, August 2018) | At each Sunday's UTC close, hold BTC for the next seven days if its last seven days' return is above 0; else cash (0 %) | BTC held | 2018-09-01 |
| S9 | Risk parity, unlevered (Asness, Frazzini and Pedersen, *Leverage Aversion and Risk Parity*, FAJ, January 2012) | At each month-end close, SPY, TLT, GLD, DBC at weights (1/σ) / Σ(1/σ), σ over the last 60 sessions | SPY | 2012-02-01 |

Costs: 5 bps a side for ETFs, 25 bps for crypto. Interval: 0.278th–99.722nd percentiles of 5,000
paired stationary-block resamples, mean block 20, seed 0. Verdict: EDGE, DEFENCE or REJECT as section 2
fixes. Ends 2026-10-23.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

*Pending.*
