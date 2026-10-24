# EXP-035 — Do the funds that sell popular ideas beat SPY after they launched?

**Status:** PRE-REGISTERED 2026-10-24 (planner, `7510d6b7`) · **COMPLETE 2026-10-24: all twenty funds are
REJECT against SPY after launch; the IBD 50 fund did measurably worse.**
**Decision / origin:** [R012](../idea-testing-foundation/INDEX.md) batches 4 and 5 · [DL-319](../../design-log.md)
· the operator, 2026-10-24: *"what do people know that we do not … Let's test every idea"* · **Cost:** $0.

## 1. Why we needed this experiment

Many ideas the project has not tested itself are sold as funds: copying hedge funds' 13F filings,
copying members of Congress, social-media sentiment, disruptive innovation, the IBD 50 growth list, new
issues, factor tilts, covered calls, trend following and tail-risk hedges. A fund's record after its
launch is the idea's out-of-sample record with real costs paid: its sponsor could not see those days.

## 2. Hypothesis

As [EXP-026](EXP-026-do-published-strategies-outside-stock-picking-still-work-after-publication.md):
`dSharpe` = the fund's Sharpe minus SPY's on the same sessions (daily returns over BIL); a stationary
block bootstrap (mean block 20, 5,000 resamples, seed 0), Bonferroni over 20: the 0.125th and
99.875th percentiles. **EDGE**: lower bound above 0, both halves above 0, CAGR at least SPY's.
**DEFENCE**: not EDGE; maximum drawdown at most 0.6 × SPY's, CAGR at least SPY's minus 3 points, and
`dSharpe` at least 0. **REJECT**: neither.

## 3. Data

Tiingo adjusted closes (distributions reinvested; fund fees already deducted) for the 20 funds, SPY and
BIL, to 2026-10-23 (kit `exp035-2026-10-24/inputs/`).

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; no repo code; $0.

## 5. How it was conducted

Each fund from the first session of the month after its launch (Appendix P) to its last session (KRUZ
closed 2025-03-20); SPY over the same sessions; the statistic, interval and verdict as section 2.
**Reported, not barred:** CAGR, volatility, maximum drawdown, the worst month, each year.

**What this cannot claim.** A fund is one implementation of its idea, with its fees; the windows differ
(from 2003 to 2023), and most fall in a strong decade for US large caps.

## 6. Results

All MEASURED from the frozen script (Appendix R). CAGR · Sharpe (over BIL) · maximum drawdown; the
interval is the Bonferroni one over 20.

| Fund | Idea | Scored | Fund | SPY, same sessions | dSharpe [interval] | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| GURU | 13F copying | 2012-07-02 → 2026-10-23 | 11.45 % · 0.58 · -38.5 % | 14.76 % · 0.82 · -33.7 % | -0.23 [-0.59, +0.08] | REJECT |
| NANC | Congress (Democrats) | 2023-03-01 → 2026-10-23 | 23.06 % · 1.06 · -20.9 % | 21.16 % · 1.07 · -18.8 % | -0.01 [-0.42, +0.36] | REJECT |
| KRUZ | Congress (Republicans) | 2023-03-01 → 2025-03-20 | 13.01 % · 0.61 · -10.4 % | 20.60 % · 1.13 · -10.0 % | -0.52 [-1.40, +0.28] | REJECT |
| BUZZ | social sentiment | 2021-04-01 → 2026-10-23 | 6.77 % · 0.26 · -56.9 % | 13.95 % · 0.67 · -24.5 % | -0.41 [-1.14, +0.31] | REJECT |
| ARKK | disruptive innovation | 2014-11-03 → 2026-10-23 | 13.30 % · 0.47 · -81.0 % | 13.63 % · 0.71 · -33.7 % | -0.24 [-0.95, +0.33] | REJECT |
| FFTY | IBD 50 growth | 2015-05-01 → 2026-10-23 | 3.57 % · 0.19 · -59.5 % | 13.82 % · 0.71 · -33.7 % | -0.52 [-1.11, -0.01] | REJECT |
| IPO | recent IPOs | 2013-11-01 → 2026-10-23 | 7.37 % · 0.33 · -68.8 % | 13.88 % · 0.75 · -33.7 % | -0.42 [-1.02, +0.18] | REJECT |
| MTUM | momentum | 2013-05-01 → 2026-10-23 | 14.97 % · 0.71 · -34.1 % | 14.22 % · 0.77 · -33.7 % | -0.07 [-0.52, +0.33] | REJECT |
| QUAL | quality | 2013-08-01 → 2026-10-23 | 13.65 % · 0.74 · -34.1 % | 13.99 % · 0.76 · -33.7 % | -0.02 [-0.18, +0.13] | REJECT |
| USMV | minimum volatility | 2011-11-01 → 2026-10-23 | 11.73 % · 0.78 · -33.1 % | 14.80 % · 0.82 · -33.7 % | -0.04 [-0.41, +0.36] | REJECT |
| VLUE | value | 2013-05-01 → 2026-10-23 | 13.31 % · 0.67 · -39.5 % | 14.22 % · 0.77 · -33.7 % | -0.10 [-0.46, +0.29] | REJECT |
| RSP | equal weight | 2003-05-01 → 2026-10-23 | 11.24 % · 0.58 · -59.9 % | 11.44 % · 0.62 · -55.2 % | -0.04 [-0.19, +0.14] | REJECT |
| MOAT | wide moats | 2012-05-01 → 2026-10-23 | 13.75 % · 0.73 · -33.3 % | 14.40 % · 0.80 · -33.7 % | -0.07 [-0.39, +0.24] | REJECT |
| NOBL | dividend aristocrats | 2013-11-01 → 2026-10-23 | 10.34 % · 0.59 · -35.4 % | 13.88 % · 0.75 · -33.7 % | -0.16 [-0.58, +0.25] | REJECT |
| COWZ | free-cash-flow yield | 2017-01-03 → 2026-10-23 | 13.72 % · 0.63 · -38.6 % | 15.10 % · 0.74 · -33.7 % | -0.11 [-0.61, +0.48] | REJECT |
| JEPI | covered-call income | 2020-06-01 → 2026-10-23 | 10.67 % · 0.74 · -13.7 % | 17.04 % · 0.85 · -24.5 % | -0.11 [-0.72, +0.52] | REJECT |
| PTLC | trend following | 2015-07-01 → 2026-10-23 | 9.15 % · 0.58 · -26.6 % | 14.11 % · 0.72 · -33.7 % | -0.14 [-0.65, +0.38] | REJECT |
| TAIL | tail-risk hedge | 2017-07-03 → 2026-10-23 | -7.38 % · -0.61 · -55.5 % | 14.88 % · 0.71 · -33.7 % | -1.32 [-3.14, +0.32] | REJECT |
| SWAN | Treasuries plus calls | 2018-12-03 → 2026-10-23 | 6.25 % · 0.34 · -31.0 % | 15.51 % · 0.71 · -33.7 % | -0.37 [-1.06, +0.26] | REJECT |
| QYLD | Nasdaq covered calls | 2014-01-02 → 2026-10-23 | 8.71 % · 0.52 · -24.7 % | 13.58 % · 0.73 · -33.7 % | -0.21 [-0.58, +0.18] | REJECT |

**All twenty are REJECT.** None has an interval above zero; FFTY's lies wholly below it (−1.11 to
−0.01): the IBD 50 did measurably worse than SPY. KRUZ closed on 2025-03-20 after two years.

## 7. Conclusions

1. **No fund that sells a popular idea beat SPY after it launched.** Copying hedge funds (GURU),
   members of Congress (NANC, KRUZ), social-media sentiment (BUZZ), innovation (ARKK), growth lists
   (FFTY), new issues (IPO), seven factor tilts, covered calls, trend following and tail hedges: each
   earned less than SPY or the same at more risk, after its fees.
2. **The ideas people pay for are the ideas this project already ruled out.** The funds' records
   agree with EXP-026's published strategies and R011's literature: after the idea is public, the
   index is the hardest benchmark.
3. **Insurance is expensive.** TAIL lost 7.4 % a year while SPY made 14.9 %; the defence that paid in
   EXP-025 was a trend guard, not bought insurance.

## 8. Recommended code changes, and how to implement them

**None.**

## Appendix P — Pre-registration (frozen)

| Fund | The idea it sells | Scored from |
| --- | --- | --- |
| GURU | copy hedge funds' top 13F holdings | 2012-07 |
| NANC | copy Democratic members of Congress's trades | 2023-03 |
| KRUZ | copy Republican members of Congress's trades | 2023-03 (closed 2025-03-20) |
| BUZZ | stocks with the most positive social-media sentiment | 2021-04 |
| ARKK | disruptive innovation, active | 2014-11 |
| FFTY | the IBD 50 (CAN SLIM growth) | 2015-05 |
| IPO | recent initial public offerings | 2013-11 |
| MTUM | momentum | 2013-05 |
| QUAL | quality | 2013-08 |
| USMV | minimum volatility | 2011-11 |
| VLUE | value | 2013-05 |
| RSP | the S&P 500 equally weighted | 2003-05 |
| MOAT | wide economic moats | 2012-05 |
| NOBL | dividend aristocrats | 2013-11 |
| COWZ | free-cash-flow yield | 2017-01 |
| JEPI | equity income with covered calls | 2020-06 |
| PTLC | trend following on US large caps (launched 2015-06-11) | 2015-07 |
| TAIL | tail-risk hedge (puts and Treasuries) | 2017-07 |
| SWAN | Treasuries plus long calls | 2018-12 |
| QYLD | Nasdaq-100 covered calls | 2014-01 |

Benchmark SPY; Bonferroni over 20; EDGE / DEFENCE / REJECT as section 2.

## Appendix R — Run record

- 2026-10-24, planner. Tiingo histories fetched (spans only read) before the pre-registration
  `7510d6b7`; PTLC's file starts 2005-12-22, before the fund's launch (2015-06-11), so its start is the
  launch, as Appendix P fixes.
- Frozen `exp035.py` SHA-256 `ad90ce7e2e4a7cc944403b12104fd55e1dded64551188c696801704b9781e6e2`;
  `exp035.json` SHA-256 `16133e8b99e936f3a28e351bb310f2b217576dee2f64ec3f5e20c75ae0ad2f3d`. Kit OneDrive
  `trading-agents-data/exp035-2026-10-24/`.

```text
python exp035.py <kit>/inputs <kit>/exp035.json
```

## Appendix S — Scripts

### `exp035.py`

```python
"""EXP-035: twenty funds that sell popular ideas, each against SPY from the month after its launch.

Usage: python exp035.py <inputs_dir> <out.json>
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

START = {"GURU": "2012-07", "NANC": "2023-03", "KRUZ": "2023-03", "BUZZ": "2021-04", "ARKK": "2014-11", "FFTY": "2015-05",
         "IPO": "2013-11", "MTUM": "2013-05", "QUAL": "2013-08", "USMV": "2011-11", "VLUE": "2013-05", "RSP": "2003-05",
         "MOAT": "2012-05", "NOBL": "2013-11", "COWZ": "2017-01", "JEPI": "2020-06", "PTLC": "2015-07", "TAIL": "2017-07",
         "SWAN": "2018-12", "QYLD": "2014-01"}
B, SEED, BLOCK = 5000, 0, 20
Q = 0.05 / 20 / 2


def px(inp: Path, t: str) -> pd.Series:
    return pd.read_csv(inp / f"{t}.csv", parse_dates=["date"]).set_index("date")["adjClose"]


def stats(r: pd.Series, rc: pd.Series) -> dict:
    eq = (1 + r).cumprod()
    yrs = len(r) / 252
    ex = r - rc
    monthly = (1 + r).groupby([r.index.year, r.index.month]).prod() - 1
    return {"cagr_pct": float((eq.iloc[-1] ** (1 / yrs) - 1) * 100), "vol_pct": float(r.std() * math.sqrt(252) * 100),
            "sharpe": float(ex.mean() / ex.std() * math.sqrt(252)), "max_drawdown_pct": float((eq / eq.cummax() - 1).min() * 100),
            "worst_month_pct": float(monthly.min() * 100)}


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


def main() -> None:
    inp, out = Path(sys.argv[1]), Path(sys.argv[2])
    spy = px(inp, "SPY").pct_change()
    bil = px(inp, "BIL").pct_change()
    rng = np.random.default_rng(SEED)
    res = {}
    for t, start in START.items():
        f = px(inp, t).pct_change()
        idx = f.index.intersection(spy.index)
        idx = idx[idx >= pd.Period(start).start_time]
        rS, rB = f.loc[idx].dropna(), spy.loc[idx].dropna()
        idx = rS.index.intersection(rB.index)
        rS, rB = rS.loc[idx], rB.loc[idx]
        rc = bil.reindex(idx).fillna(0.0)
        eS, eB = (rS - rc).to_numpy(), (rB - rc).to_numpy()
        sh = lambda e: e.mean() / e.std(ddof=1) * math.sqrt(252)  # noqa: E731
        vals = []
        for _ in range(B // 500):
            d = draws(len(eS), rng, 500)
            a, b = eS[d], eB[d]
            vals.append(a.mean(1) / a.std(1, ddof=1) * math.sqrt(252) - b.mean(1) / b.std(1, ddof=1) * math.sqrt(252))
        v = np.concatenate(vals)
        h = len(eS) // 2
        row = {"from": str(idx[0].date()), "to": str(idx[-1].date()), "sessions": int(len(idx)),
               "fund": stats(rS, rc), "spy": stats(rB, rc), "dsharpe": float(sh(eS) - sh(eB)),
               "dsharpe_ci": [float(np.quantile(v, Q)), float(np.quantile(v, 1 - Q))],
               "dsharpe_halves": [float(sh(eS[:h]) - sh(eB[:h])), float(sh(eS[h:]) - sh(eB[h:]))]}
        s, b_ = row["fund"], row["spy"]
        if row["dsharpe_ci"][0] > 0 and min(row["dsharpe_halves"]) > 0 and s["cagr_pct"] >= b_["cagr_pct"]:
            row["verdict"] = "EDGE"
        elif s["max_drawdown_pct"] >= 0.6 * b_["max_drawdown_pct"] and s["cagr_pct"] >= b_["cagr_pct"] - 3 and row["dsharpe"] >= 0:
            row["verdict"] = "DEFENCE"
        else:
            row["verdict"] = "REJECT"
        res[t] = row
        print(f"{t:5s} {row['from']} {row['verdict']:8s} dSh {row['dsharpe']:+.2f} [{row['dsharpe_ci'][0]:+.2f},{row['dsharpe_ci'][1]:+.2f}] | "
              f"fund {s['cagr_pct']:6.2f}% sh {s['sharpe']:.2f} dd {s['max_drawdown_pct']:6.1f} | SPY {b_['cagr_pct']:6.2f}% sh {b_['sharpe']:.2f} dd {b_['max_drawdown_pct']:6.1f}")
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
```
