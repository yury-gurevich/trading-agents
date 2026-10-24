# EXP-026 — Do nine published strategies outside single-stock picking still work after they were published?

**Status:** PRE-REGISTERED 2026-10-24 (planner, `b1fcaf84`) · **COMPLETE 2026-10-24: no strategy has an
edge after its publication; two multi-asset trend rules (S1, S4) pass as DEFENCE, seven are rejected.**
Sections 1–5 and Appendix P were fixed before the first strategy was computed.
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

All MEASURED, from the frozen script (Appendix R), 5 bps a side for ETFs and 25 bps for crypto.
`dSharpe` is the strategy's Sharpe minus its benchmark's; the interval is the Bonferroni one over nine.

| # | Strategy | Verdict | dSharpe [interval] | Halves | Strategy: CAGR · Sharpe · max DD | Benchmark: CAGR · Sharpe · max DD | dSharpe vs SPY |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | Faber 5-asset trend (2007-06 →) | **DEFENCE** | +0.08 [−0.38, +0.53] | +0.09, +0.04 | 4.77 % · 0.45 · **−14.4 %** | 5.91 % · 0.37 · −47.1 % (the five, static) | −0.09 |
| S2 | Antonacci dual momentum (2013 →) | REJECT | −0.33 [−0.65, +0.01] | −0.48, −0.25 | 8.14 % · 0.48 · −33.7 % | 14.69 % · 0.80 · −33.7 % (SPY) | −0.33 |
| S3 | Halloween, sell in May (2003 →) | REJECT | −0.14 [−0.52, +0.27] | +0.02, −0.31 | 7.02 % · 0.45 · −34.9 % | 11.45 % · 0.59 · −55.2 % (SPY) | −0.14 |
| S4 | Time-series momentum, long-only (2012-06 →) | **DEFENCE** | +0.02 [−0.48, +0.47] | −0.09, +0.07 | 4.03 % · 0.48 · **−9.3 %** | 5.06 % · 0.46 · −20.3 % (the eight, static) | −0.36 |
| S5 | Industry momentum, top 3 of 9 (1999-09 →) | REJECT | −0.06 [−0.29, +0.15] | +0.00, −0.15 | 7.94 % · 0.43 · −51.7 % | 9.08 % · 0.49 · −53.5 % (nine, equal) | −0.02 |
| S6 | Leveraged trend, SSO above SPY's 200-day (2016-10 →) | REJECT | −0.05 [−0.58, +0.52] | −0.05, −0.05 | 17.63 % · 0.70 · −36.3 % | 15.16 % · 0.75 · −33.7 % (SPY) | −0.05 |
| S7 | Short volatility while VIX < VIX3M (2014-04 →) | REJECT | −0.09 [−0.77, +0.57] | +0.09, −0.28 | 21.17 % · 0.64 · **−56.0 %** | 13.68 % · 0.73 · −33.7 % (SPY) | −0.09 |
| S8 | Crypto weekly momentum, BTC (2018-09 →) | REJECT | −0.35 [−1.09, +0.37] | −0.10, −0.79 | 10.36 % · 0.44 · −61.2 % | 34.98 % · 0.80 · −76.7 % (BTC held) | — |
| S9 | Risk parity, unlevered (2012-02 →) | REJECT | −0.30 [−0.94, +0.28] | −0.79, +0.03 | 5.85 % · 0.52 · −20.5 % | 14.60 % · 0.81 · −33.7 % (SPY) | −0.30 |

**No interval's lower bound is above zero: no strategy has an edge after its publication.** None beats
its benchmark's Sharpe by a margin the interval can tell from zero; S2's interval nearly excludes zero
from below.

- **At 25 bps a side** (ETFs): S1 4.00 %, S2 7.28 %, S3 6.17 %, S4 3.34 %, S5 6.41 %, S6 15.28 %,
  S7 15.32 %, S9 5.62 % CAGR. Trades a year: 2 (S2, S3) to 12 (monthly rules); S8 27.7.
- **The tails:** S7's worst day −21.6 % (February 2018) and worst month −27.6 %, with −34 % in 2018
  and −19.7 % in 2024; S8's worst month −31.4 %; S6's worst month −20.3 %.
- **ETH, reported only:** the same weekly rule 18.37 % CAGR against 29.91 % held, Sharpe 0.58 against
  0.74, maximum drawdown −57.4 % against −79.4 %.

**Before publication against after it** (Sharpe, strategy against benchmark; reported, not barred):

| # | Before (from) | After |
| --- | --- | --- |
| S2 | 0.42 vs 0.22 (2008-06) | 0.48 vs 0.80 |
| S3 | 0.61 vs 0.55 (1993-05) | 0.45 vs 0.59 |
| S4 | 0.86 vs 0.65 (2008-06) | 0.48 vs 0.46 |
| S6 | 0.41 vs 0.42 (2006-06) | 0.70 vs 0.75 |
| S7 | 1.20 vs 1.70, CAGR 69.9 % (2011-10) | 0.64 vs 0.73, CAGR 21.2 % with −56 % |
| S9 | 1.00 vs 0.17 (2006-06) | 0.52 vs 0.81 |

**Context, not barred — SPY over the DEFENCE windows, and EXP-025's SPY-only 200-day guard (cash in
BIL, 5 bps a side):**

| Window | SPY: CAGR · max DD · Sharpe | SPY 200-day guard | The DEFENCE rule |
| --- | --- | --- | --- |
| 2007-06 → (S1's) | 10.61 % · −55.2 % · 0.54 | 7.51 % · −25.2 % · 0.56 | S1: 4.77 % · −14.4 % · 0.45 |
| 2012-06 → (S4's) | 15.11 % · −33.7 % · 0.84 | 10.92 % · −20.2 % · 0.80 | S4: 4.03 % · −9.3 % · 0.48 |

**Controls:** (a) static SPY against static SPY: largest daily difference 0.0; (b) two runs gave the
same JSON byte for byte (SHA-256 `ca7d2f7b…`). Pilot: no ETF has a missing session inside its window;
BTC has every day; ETH misses 2 days (reported only).

## 7. Conclusions

1. **Nothing outside single-stock picking showed an edge after its publication either.** Nine families,
   nine published rules, each scored only on years its author could not see: none beat its benchmark's
   risk-adjusted return by a margin the interval can tell from zero. Where earlier data exist, the
   pattern the literature predicts held: dual momentum, risk parity and the Halloween rule had a higher
   Sharpe than their benchmarks before publication and a lower one after it, and short volatility's
   return fell from 70 % to 21 % a year with a −56 % drawdown.
2. **The last fifteen years made SPY the hardest benchmark there is.** Every allocation that moved money
   out of US large caps (into bonds, commodities, foreign stocks, cash) lost to simply holding SPY:
   risk parity 5.9 % against 14.6 %, dual momentum 8.1 % against 14.7 %.
3. **More return came only with more risk.** Leveraged trend (17.6 %) and filtered short volatility
   (21.2 %) out-earned SPY, at a lower Sharpe and deeper drawdowns (−36 %, −56 %, a −21.6 % day). That
   is leverage, not edge, and short volatility is the catastrophic-loss profile the operator wants to
   avoid.
4. **Crypto momentum protected and gave up the gains.** The weekly rule cut BTC's drawdown from −77 %
   to −61 % and its return from 35 % to 10 % a year.
5. **Defence is real, it has a price, and the simplest one is the cheapest.** Multi-asset trend (S1,
   S4) cut drawdowns by about two thirds against their own mixes, but against SPY they cost 6–11 points
   a year. The SPY-only 200-day guard of EXP-025 kept more of SPY's return (7.5 % and 10.9 %) for
   about half SPY's drawdown.
6. **Taken with EXP-015, EXP-023, EXP-024, EXP-025 and R011:** no rule built from public prices,
   calendars, sentiment or published allocations has shown an edge over holding the index, here or in
   the literature after publication. What remains untested is information that is slow to be priced
   (insider purchases, filing changes) and smaller stocks.
7. **What this cannot claim.** One post-publication window per strategy, nine strategies; a REJECT
   here says the published rule did not serve after publication, not that no variant could. Tuning a
   variant on these windows would spend them.

## 8. Recommended code changes, and how to implement them

**None to the fleet.** No EDGE result exists to build.

- **The DEFENCE results are allocation rules, not fleet features.** S1, S4 and EXP-025's SPY guard
  each rebalance a handful of ETFs once a month or on a trend switch. If the operator wants defence
  with capital, the cheapest form is the SPY 200-day guard: one check and one order, not sixteen
  agents. Running capital that way is the operator's decision ([DL-317](../../design-log.md) option A).
- **Rejected, not to be built:** dual momentum, Halloween, industry momentum, leveraged trend, filtered
  short volatility, crypto weekly momentum, unlevered risk parity.
- **The one candidate left for an edge** is the insider-purchase test of R011, which waits on the
  operator's word for an SEC contact address.

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

- 2026-10-24, planner. Data fetched about 01:30–01:40 UTC (Tiingo 22 ETFs, Cboe VIX/VIX3M, Coinbase
  BTC/ETH); only spans and row counts were read before the pre-registration commit `b1fcaf84`, and no
  strategy was computed before it.
- Pilot (`--pilot`: data checks, control (a), SPY over each window): passed. SPY CAGR by window: S1
  10.61 %, S2 14.69 %, S3 11.45 %, S4 15.11 %, S5 8.53 %, S6 15.16 %, S7 13.68 %, S9 14.60 %.
- Frozen `exp026.py` SHA-256 `0802ea06d8a9a9ec465245579a2321862ea5ffc30399a40f22a4d8623a520c12`;
  run twice 01:49:13–01:49:49 UTC; `exp026.json` = `exp026_rerun.json`, SHA-256
  `ca7d2f7b0b0b3fd54f53d5eec6cbe172243a29bc8c2ad772cd35a0a2e2997a70`. Kit OneDrive
  `trading-agents-data/exp026-2026-10-24/` (`inputs/`, `pilot.json`, `exp026.json`, `context.txt`).
- The context rows of section 6 were computed after the run by a separate snippet (output
  `context.txt`); they are not part of the bar.

```text
python exp026.py <kit>/inputs <kit>/pilot.json --pilot
python exp026.py <kit>/inputs <kit>/exp026.json
```

## Appendix S — Scripts

### `exp026.py`

```python
"""EXP-026 (DL-318): nine published strategies, each scored only after its publication.

Read-only. Usage: python exp026.py <inputs_dir> <out.json> [--pilot]
--pilot computes data checks and benchmarks only; no strategy is computed.
"""

from __future__ import annotations

import bisect
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

END = "2026-10-23"
COST_ETF, COST_CRYPTO = 0.0005, 0.0025
B, SEED, BLOCK = 5000, 0, 20
Q = 0.05 / 9 / 2
ETFS = ["SPY", "EFA", "EEM", "IEF", "TLT", "AGG", "SHY", "BIL", "VNQ", "DBC", "GLD", "SSO", "SVXY",
        "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]
SECTORS = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]


def load(inp: Path):
    spy = pd.read_csv(inp / "SPY.csv", parse_dates=["date"])
    cal = pd.DatetimeIndex(spy["date"].dt.tz_localize(None) if spy["date"].dt.tz else spy["date"])
    cal = cal[cal <= END]
    O, C, gaps = {}, {}, {}
    for t in ETFS:
        d = pd.read_csv(inp / f"{t}.csv", parse_dates=["date"])
        d["date"] = d["date"].dt.tz_localize(None) if d["date"].dt.tz else d["date"]
        d = d.set_index("date").reindex(cal)
        first = d["adjClose"].first_valid_index()
        missing = d["adjClose"].loc[first:].isna().to_numpy()
        run, worst = 0, 0
        for m in missing:
            run = run + 1 if m else 0
            worst = max(worst, run)
        gaps[t] = {"first": str(first.date()), "longest_gap_sessions": int(worst), "missing_sessions": int(missing.sum())}
        c = d["adjClose"].copy()
        c.loc[first:] = c.loc[first:].ffill()
        o = d["adjOpen"].where(d["adjOpen"].notna(), c)
        O[t], C[t] = o, c
    O, C = pd.DataFrame(O), pd.DataFrame(C)
    O["CASH"], C["CASH"] = cash_series(O, C)
    vix = cboe(inp / "VIX.csv").reindex(cal).ffill()
    vix3m = cboe(inp / "VIX3M.csv").reindex(cal).ffill()
    crypto = {k: pd.read_csv(inp / f"{k}.csv", parse_dates=["date"]).set_index("date")["close"].loc[:END]
              for k in ("BTC-USD", "ETH-USD")}
    for k, s in crypto.items():
        full = pd.date_range(s.index[0], s.index[-1], freq="D")
        gaps[k] = {"first": str(s.index[0].date()), "missing_days": int(len(full) - len(s))}
    return cal, O, C, vix, vix3m, crypto, gaps


def cboe(path: Path) -> pd.Series:
    d = pd.read_csv(path)
    d["DATE"] = pd.to_datetime(d["DATE"], format="%m/%d/%Y")
    return d.set_index("DATE")["CLOSE"]


def cash_series(O, C):
    n = len(C)
    oc, cc = np.ones(n), np.ones(n)
    for i in range(1, n):
        on, intra = 1.0, 1.0
        for src in ("BIL", "SHY"):
            p, o, c = C[src].iloc[i - 1], O[src].iloc[i], C[src].iloc[i]
            if not (np.isnan(p) or np.isnan(o) or np.isnan(c)):
                on, intra = o / p, c / o
                break
        oc[i] = cc[i - 1] * on
        cc[i] = oc[i] * intra
    return oc, cc


def month_ends(cal):
    s = pd.Series(cal, index=cal)
    return [i for i in range(len(cal) - 1) if cal[i].month != cal[i + 1].month]


def simulate(O, C, targets: dict, start: int, end: int, cost: float):
    """Decisions read at a close (targets keyed by calendar position), traded at the next open."""
    cols = list(O.columns)
    Ov, Cv = O.to_numpy(), C.to_numpy()
    keys = sorted(targets)
    k0 = bisect.bisect_left(keys, start) - 1
    if k0 < 0:
        raise SystemExit("no decision before the window")
    w = targets[keys[k0]]
    h = w * (1 - cost * np.abs(w).sum())
    h = h * (Cv[start] / Ov[start])
    h = np.nan_to_num(h)
    rets, trades, v_prev = [float(h.sum()) - 1.0], 0, float(h.sum())
    for d in range(start + 1, end + 1):
        ratio = np.where(h != 0, Ov[d] / Cv[d - 1], 1.0)
        h = h * ratio
        if (d - 1) in targets:
            v = h.sum()
            w_new = targets[d - 1]
            moved = np.abs(w_new - h / v).sum()
            if moved > 1e-12:
                trades += 1
                h = w_new * v * (1 - cost * moved)
        h = h * np.where(h != 0, Cv[d] / Ov[d], 1.0)
        v = float(h.sum())
        rets.append(v / v_prev - 1)
        v_prev = v
    return np.array(rets), trades


def weights(cols, **kw):
    w = np.zeros(len(cols))
    for k, v in kw.items():
        w[cols.index(k)] = v
    w[cols.index("CASH")] += 1 - w.sum()
    return w


def strategies(cal, O, C, vix, vix3m):
    cols = list(O.columns)
    Cv = C
    me = month_ends(cal)
    r = Cv / Cv.shift(1) - 1
    vol60 = r.rolling(60).std()
    sma200 = Cv["SPY"].rolling(200).mean()
    out = {}

    def ret(t, i, months):
        j = me[me.index(i) - months] if me.index(i) >= months else None
        if j is None:
            return np.nan
        return Cv[t].iloc[i] / Cv[t].iloc[j] - 1

    # S1 Faber 5
    s1, b1 = {}, {}
    for k, i in enumerate(me):
        if k < 9:
            continue
        five = ["SPY", "EFA", "IEF", "VNQ", "DBC"]
        if any(np.isnan(Cv[t].iloc[me[k - 9]]) for t in five):
            continue
        sel = {t: 0.2 for t in five if Cv[t].iloc[i] > np.mean([Cv[t].iloc[me[k - m]] for m in range(10)])}
        s1[i] = weights(cols, **sel)
        b1[i] = weights(cols, **{t: 0.2 for t in five})
    out["S1"] = (s1, b1)
    # S2 dual momentum
    s2, b2 = {}, {}
    for i in me:
        r12 = {t: ret(t, i, 12) for t in ("SPY", "EFA", "BIL", "AGG")}
        if any(np.isnan(v) for v in r12.values()):
            continue
        if r12["SPY"] > r12["BIL"]:
            s2[i] = weights(cols, **{max(("SPY", "EFA"), key=lambda t: r12[t]): 1.0})
        else:
            s2[i] = weights(cols, AGG=1.0)
        b2[i] = weights(cols, SPY=1.0)
    out["S2"] = (s2, b2)
    # S3 Halloween
    s3, b3 = {}, {}
    for i in me:
        if np.isnan(Cv["SPY"].iloc[i]):
            continue
        m = cal[i].month
        if m == 10:
            s3[i] = weights(cols, SPY=1.0)
        elif m == 4:
            s3[i] = weights(cols)
        b3[i] = weights(cols, SPY=1.0)
    out["S3"] = (s3, b3)
    # S4 time-series momentum, inverse-vol weights
    eight = ["SPY", "EFA", "EEM", "IEF", "TLT", "GLD", "DBC", "VNQ"]
    s4, b4 = {}, {}
    for i in me:
        r12 = {t: ret(t, i, 12) for t in eight + ["BIL"]}
        sig = {t: vol60[t].iloc[i] for t in eight}
        if any(np.isnan(v) for v in list(r12.values()) + list(sig.values())):
            continue
        inv = {t: 1 / sig[t] for t in eight}
        tot = sum(inv.values())
        base = {t: inv[t] / tot for t in eight}
        s4[i] = weights(cols, **{t: base[t] for t in eight if r12[t] > r12["BIL"]})
        b4[i] = weights(cols, **base)
    out["S4"] = (s4, b4)
    # S5 industry momentum, top 3 of 9 by 6-month return
    s5, b5 = {}, {}
    for i in me:
        r6 = {t: ret(t, i, 6) for t in SECTORS}
        if any(np.isnan(v) for v in r6.values()):
            continue
        top = sorted(SECTORS, key=lambda t: r6[t], reverse=True)[:3]
        s5[i] = weights(cols, **{t: 1 / 3 for t in top})
        b5[i] = weights(cols, **{t: 1 / 9 for t in SECTORS})
    out["S5"] = (s5, b5)
    # S6 leveraged trend, S7 filtered short volatility: checked each session
    s6, s7, spy_b = {}, {}, {}
    for i in range(len(cal)):
        if not np.isnan(sma200.iloc[i]) and not np.isnan(Cv["SSO"].iloc[i]):
            s6[i] = weights(cols, SSO=1.0) if Cv["SPY"].iloc[i] > sma200.iloc[i] else weights(cols)
        if not np.isnan(vix.iloc[i]) and not np.isnan(vix3m.iloc[i]) and not np.isnan(Cv["SVXY"].iloc[i]):
            s7[i] = weights(cols, SVXY=1.0) if vix.iloc[i] < vix3m.iloc[i] else weights(cols)
        if i in me:
            spy_b[i] = weights(cols, SPY=1.0)
    out["S6"] = (s6, spy_b)
    out["S7"] = (s7, spy_b)
    # S9 unlevered risk parity
    s9 = {}
    for i in me:
        four = ["SPY", "TLT", "GLD", "DBC"]
        sig = {t: vol60[t].iloc[i] for t in four}
        if any(np.isnan(v) for v in sig.values()):
            continue
        tot = sum(1 / v for v in sig.values())
        s9[i] = weights(cols, **{t: (1 / sig[t]) / tot for t in four})
    out["S9"] = (s9, spy_b)
    return out


WINDOWS = {"S1": "2007-06-01", "S2": "2013-01-01", "S3": "2003-01-01", "S4": "2012-06-01",
           "S5": "1999-09-01", "S6": "2016-10-01", "S7": "2014-04-01", "S8": "2018-09-01", "S9": "2012-02-01"}
NAMES = {"S1": "Faber 5-asset trend", "S2": "Antonacci dual momentum", "S3": "Halloween (sell in May)",
         "S4": "Time-series momentum, long-only", "S5": "Industry momentum, top 3 of 9",
         "S6": "Leveraged trend (SSO above SPY's 200-day)", "S7": "Short volatility when VIX < VIX3M",
         "S8": "Crypto weekly momentum (BTC)", "S9": "Risk parity, unlevered"}
BENCH = {"S1": "same five, static", "S2": "SPY", "S3": "SPY", "S4": "same eight, static inverse-vol",
         "S5": "nine sectors, equal", "S6": "SPY", "S7": "SPY", "S8": "BTC held", "S9": "SPY"}


def crypto_sim(close: pd.Series, start: str, rule: bool, cost: float):
    r = close.pct_change()
    days = close.index
    pos = pd.Series(np.nan, index=days)
    for i, d in enumerate(days):
        if d.weekday() == 6 and i >= 7:
            pos.iloc[i] = (1.0 if close.iloc[i] / close.iloc[i - 7] - 1 > 0 else 0.0) if rule else 1.0
    pos = pos.ffill().shift(2).fillna(0.0)  # decided at a close, traded at the next close
    if not rule:
        pos[:] = 1.0
    w = r.index >= start
    rr, pp = r[w].to_numpy(), pos[w].to_numpy()
    out = pp * rr
    change = np.abs(np.diff(np.r_[0.0, pp]))
    out = (1 + out) * (1 - cost * change) - 1
    return pd.Series(out, index=r.index[w]), int((change > 0).sum())


def stats(r: pd.Series, rc: pd.Series, ann: float) -> dict:
    eq = (1 + r).cumprod()
    yrs = len(r) / ann
    ex = r - rc
    monthly = (1 + r).groupby([r.index.year, r.index.month]).prod() - 1
    return {
        "cagr_pct": float((eq.iloc[-1] ** (1 / yrs) - 1) * 100),
        "vol_pct": float(r.std() * np.sqrt(ann) * 100),
        "sharpe": float(ex.mean() / ex.std() * np.sqrt(ann)),
        "max_drawdown_pct": float((eq / eq.cummax() - 1).min() * 100),
        "worst_month_pct": float(monthly.min() * 100),
        "worst_day_pct": float(r.min() * 100),
    }


def draws(n, rng, rows):
    out = np.empty((rows, n), np.int64)
    pos = np.arange(n)
    for k in range(rows):
        st = rng.random(n) < 1.0 / BLOCK
        st[0] = True
        g = np.cumsum(st) - 1
        first = pos[st]
        base = rng.integers(n, size=len(first))
        out[k] = (base[g] + pos - first[g]) % n
    return out


def dsharpe_ci(eS, eB, ann, rng):
    vals = []
    for _ in range(B // 500):
        d = draws(len(eS), rng, 500)
        a, b = eS[d], eB[d]
        vals.append(a.mean(1) / a.std(1, ddof=1) * np.sqrt(ann) - b.mean(1) / b.std(1, ddof=1) * np.sqrt(ann))
    v = np.concatenate(vals)
    return [float(np.quantile(v, Q)), float(np.quantile(v, 1 - Q))]


def verdict(res):
    s, b = res["strategy"], res["benchmark"]
    lo = res["dsharpe_ci"][0]
    if lo > 0 and min(res["dsharpe_halves"]) > 0 and s["cagr_pct"] >= b["cagr_pct"]:
        return "EDGE"
    if (s["max_drawdown_pct"] >= 0.6 * b["max_drawdown_pct"] and s["cagr_pct"] >= b["cagr_pct"] - 3
            and res["dsharpe"] >= 0):
        return "DEFENCE"
    return "REJECT"


def score(rS, rB, rc, ann, rng):
    eS, eB = (rS - rc).to_numpy(), (rB - rc).to_numpy()
    sh = lambda e: e.mean() / e.std(ddof=1) * np.sqrt(ann)  # noqa: E731
    h = len(eS) // 2
    res = {
        "sessions": int(len(rS)),
        "strategy": stats(rS, rc, ann),
        "benchmark": stats(rB, rc, ann),
        "dsharpe": float(sh(eS) - sh(eB)),
        "dsharpe_halves": [float(sh(eS[:h]) - sh(eB[:h])), float(sh(eS[h:]) - sh(eB[h:]))],
        "dsharpe_ci": dsharpe_ci(eS, eB, ann, rng),
    }
    res["verdict"] = verdict(res)
    return res


def main() -> None:
    inp, out = Path(sys.argv[1]), Path(sys.argv[2])
    pilot = "--pilot" in sys.argv
    cal, O, C, vix, vix3m, crypto, gaps = load(inp)
    rng = np.random.default_rng(SEED)
    pos = {d: i for i, d in enumerate(cal)}
    end = len(cal) - 1
    rc_all = pd.Series(C["CASH"].to_numpy(), index=cal).pct_change().fillna(0.0)
    result = {"gaps": gaps, "windows": WINDOWS, "names": NAMES, "benchmarks": BENCH}
    strats = strategies(cal, O, C, vix, vix3m) if not pilot else None
    spy_static = {i: weights(list(O.columns), SPY=1.0) for i in month_ends(cal)}
    for sid, start in WINDOWS.items():
        if sid == "S8":
            continue
        st = pos[cal[cal >= start][0]]
        idx = cal[st : end + 1]
        if pilot:
            continue
        s_t, b_t = strats[sid]
        rows = {}
        for lab, cost in (("5bps", COST_ETF), ("25bps", 0.0025)):
            rS, nS = simulate(O, C, s_t, st, end, cost)
            rB, _ = simulate(O, C, b_t, st, end, cost)
            rSPY, _ = simulate(O, C, spy_static, st, end, cost)
            rS, rB, rSPY = (pd.Series(x, index=idx) for x in (rS, rB, rSPY))
            rc = rc_all.loc[idx]
            if lab == "5bps":
                res = score(rS, rB, rc, 252, rng)
                res["trades_per_year"] = float(nS / (len(idx) / 252))
                res["vs_spy"] = {"spy": stats(rSPY, rc, 252), "dsharpe": float(
                    (rS - rc).mean() / (rS - rc).std() * np.sqrt(252) - (rSPY - rc).mean() / (rSPY - rc).std() * np.sqrt(252))}
                res["years"] = {str(y): [round(float((1 + g).prod() - 1) * 100, 2), round(float((1 + rB[rB.index.year == y]).prod() - 1) * 100, 2)]
                                for y, g in rS.groupby(rS.index.year)}
                rows = res
            else:
                rows["at_25bps"] = {"cagr_pct": stats(rS, rc, 252)["cagr_pct"], "sharpe": stats(rS, rc, 252)["sharpe"]}
        keys = sorted(s_t)
        first = keys[0] + 1
        if st - first >= 504:
            pr = pd.Series(simulate(O, C, s_t, first, st - 1, COST_ETF)[0], index=cal[first:st])
            pb = pd.Series(simulate(O, C, b_t, first, st - 1, COST_ETF)[0], index=cal[first:st])
            rcp = rc_all.loc[cal[first:st]]
            rows["pre_publication"] = {"from": str(cal[first].date()), "strategy": stats(pr, rcp, 252),
                                       "benchmark": stats(pb, rcp, 252)}
        result[sid] = rows
    # S8 crypto
    for coin in ("BTC-USD", "ETH-USD"):
        if pilot:
            break
        rS, nS = crypto_sim(crypto[coin], WINDOWS["S8"], True, COST_CRYPTO)
        rB, _ = crypto_sim(crypto[coin], WINDOWS["S8"], False, COST_CRYPTO)
        rc = pd.Series(0.0, index=rS.index)
        res = score(rS, rB, rc, 365, rng)
        res["trades_per_year"] = float(nS / (len(rS) / 365))
        res["years"] = {str(y): [round(float((1 + g).prod() - 1) * 100, 2), round(float((1 + rB[rB.index.year == y]).prod() - 1) * 100, 2)]
                        for y, g in rS.groupby(rS.index.year)}
        result["S8" if coin == "BTC-USD" else "S8_ETH_reported_only"] = res
    # Control (a): static SPY against SPY reads dSharpe 0.
    st = pos[cal[cal >= "2007-06-01"][0]]
    a, _ = simulate(O, C, spy_static, st, end, COST_ETF)
    b, _ = simulate(O, C, spy_static, st, end, COST_ETF)
    result["control_a_dsharpe"] = float(np.abs(a - b).max())
    if pilot:
        bench = {}
        for sid, start in WINDOWS.items():
            if sid == "S8":
                continue
            st = pos[cal[cal >= start][0]]
            rB, _ = simulate(O, C, spy_static, st, end, COST_ETF)
            bench[sid] = {"spy_cagr_pct": stats(pd.Series(rB, index=cal[st:]), rc_all.loc[cal[st:]], 252)["cagr_pct"]}
        result["pilot_spy_benchmarks"] = bench
    out.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
```
