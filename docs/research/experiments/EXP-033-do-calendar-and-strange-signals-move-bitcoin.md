# EXP-033 — Do calendar and strange signals move Bitcoin?

**Status:** PRE-REGISTERED 2026-10-24 (planner, `7f111bcd`) · **COMPLETE 2026-10-24: none of the seven
passes discovery on BTC.**
**Decision / origin:** [R012](../idea-testing-foundation/INDEX.md) batch 5 · [DL-319](../../design-log.md)
· the operator, 2026-10-24: *"Let's test every idea"* · **Cost:** $0.

## 1. Why we needed this experiment

Crypto is younger, trades every day of the year and is more retail-driven than US stocks: if calendar or
mood effects live anywhere, they should live there. Batch 1's signals that fit a 24/7 market are tested
on BTC, which Alpaca trades.

## 2. Hypothesis

**The statistic.** *b*: the difference in BTC's mean daily return (Coinbase BTC-USD, UTC days) between
signal days and comparison days, OLS on a dummy with Newey–West (5 lags), as EXP-029.

**Discovery** 2015-07-21 → 2020-12-31: Benjamini–Hochberg at 10 % over the seven. **Confirmation**
2021-01-01 → 2026-10-23: one-sided in the discovery's direction, Holm at 5 %. **Economic bar:** holding
BTC on favourable days only (or stepping aside on unfavourable ones), 25 bps a side, beats holding BTC on
Sharpe over the confirmation period.

## 3. Data

EXP-026's kit: `BTC-USD.csv` (4,115 complete days, 2015-07-20 → 2026-10-24; the incomplete last day
dropped). ETH is not tested here (EXP-026 found it gappy).

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; Meeus's moon phases as EXP-029; no repo code; $0.

## 5. How it was conducted

Signals by Appendix P on UTC dates; the funnel and the economic bar as section 2. **Reported, not
barred:** each idea's *b* in both periods and its day counts.

**What this cannot claim.** One exchange, one coin, eleven years; crypto's regime changed with the
arrival of spot ETFs in 2024.

## 6. Results

All MEASURED from the frozen script (Appendix R); BTC daily returns, *b* in basis points a day (t).

| # | Idea | Discovery 2015-07 → 2020 | Confirmation 2021 → 2026-10 | Verdict |
| --- | --- | --- | --- | --- |
| K1 | Weekend | −10.3 (−0.61), 568 days | −1.3 (−0.12), 606 | fails discovery |
| K2 | Monday | +30.3 (1.25), 284 | +21.3 (0.96), 303 | fails discovery |
| K3 | Turn of the month | +49.4 (2.09), 261; p 0.037 | +0.8 (0.04), 279 | fails discovery |
| K4 | New moon against full moon | +30.9 (1.18), 469 | −10.2 (−0.55), 504 | fails discovery |
| K5 | Halloween | −3.7 (−0.21), 968 | +11.4 (0.88), 1,026 | fails discovery |
| K6 | After a −5 % day | +55.6 (1.28), 139 | +23.4 (0.49), 91 | fails discovery |
| K7 | After a +5 % day | −38.6 (−1.08), 158 | +8.8 (0.23), 101 | fails discovery |

Benjamini–Hochberg at 10 % passes none (the smallest p, 0.037, is above its threshold of 0.014).

## 7. Conclusions

1. **Bitcoin's calendar is as empty as the S&P 500's.** BTC's daily swings (about 3.5 % a day) dwarf
   any calendar effect a decade can resolve, and the one lean (the turn of the month, +49 bps a day to
   2020) was gone after it (+0.8 bps).

## 8. Recommended code changes, and how to implement them

**None.**

## Appendix P — Pre-registration (frozen)

| # | Idea | Signal days | Comparison | Predicted |
| --- | --- | --- | --- | --- |
| K1 | Weekend | Saturday and Sunday (UTC) | weekdays | ± |
| K2 | Monday | Monday | other days | ± |
| K3 | Turn of the month | the last day of a month and the first three of the next | other days | + |
| K4 | The Moon | within 3 days of a new moon | within 3 days of a full moon | + |
| K5 | Halloween | November → April | May → October | + |
| K6 | After a crash day | the previous day's return ≤ −5 % | other days | ± |
| K7 | After a surge day | the previous day's return ≥ +5 % | other days | ± |

Discovery BH 10 % over 7; confirmation Holm 5 % one-sided; economic at 25 bps a side against BTC held,
by Sharpe.

## Appendix R — Run record

- 2026-10-24, planner. Frozen `exp033.py` SHA-256
  `2ca5b898ab63c9a4556aff8a9e29cf3cb5d1c8a5cbd283a3a168302e96e4291b` (it imports EXP-029's frozen
  `moon_phases`, `nw_test`, `p_two`, `p_one`); `exp033.json` SHA-256
  `cde6a2d9026b197d2ada279a47fdd2a68cdda52816851eff640a4b9083c43ccc`. Kit OneDrive
  `trading-agents-data/exp033-2026-10-24/`.

```text
python exp033.py <exp026 kit>/inputs/BTC-USD.csv <exp029 kit>/exp029.py <kit>/exp033.json
```

## Appendix S — Scripts

### `exp033.py`

```python
"""EXP-033 (R012 batch 5): seven calendar and strange signals on BTC, daily, 2015 →.

Usage: python exp033.py <BTC-USD.csv> <exp029.py> <out.json>
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys

import numpy as np
import pandas as pd

SPLIT, END = "2021-01-01", "2026-10-23"


def main() -> None:
    btc_p, e29_p, out = sys.argv[1:4]
    spec = importlib.util.spec_from_file_location("e29", e29_p)
    e29 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e29)
    c = pd.read_csv(btc_p, parse_dates=["date"]).set_index("date")["close"].loc[:END]
    r = c.pct_change()
    cal = r.index
    d = pd.Series(cal, index=cal)
    wd, mon = d.dt.weekday, d.dt.month
    last_of_month = d.dt.is_month_end
    tom = last_of_month | (d.dt.day <= 3)
    dd = cal.values.astype("datetime64[D]")
    news = np.array(e29.moon_phases(150, 340, False), dtype="datetime64[D]")
    fulls = np.array(e29.moon_phases(150, 340, True), dtype="datetime64[D]")

    def near(ev):
        i = np.searchsorted(ev, dd)
        lo = np.abs((dd - ev[np.clip(i - 1, 0, len(ev) - 1)]).astype(int))
        hi = np.abs((ev[np.clip(i, 0, len(ev) - 1)] - dd).astype(int))
        return np.minimum(lo, hi)

    prev = r.shift(1)
    ideas = {
        "K1": (wd >= 5, wd < 5, 0), "K2": (wd == 0, wd != 0, 0), "K3": (tom, ~tom, 1),
        "K4": (pd.Series(near(news) <= 3, index=cal), pd.Series(near(fulls) <= 3, index=cal), 1),
        "K5": (mon.isin([11, 12, 1, 2, 3, 4]), ~mon.isin([11, 12, 1, 2, 3, 4]), 1),
        "K6": (prev <= -0.05, prev > -0.05, 0), "K7": (prev >= 0.05, prev < 0.05, 0),
    }
    res = {}
    for k, (sig, cmp_, pred) in ideas.items():
        sig = pd.Series(sig, index=cal).fillna(False).astype(bool)
        cmp_ = pd.Series(cmp_, index=cal).fillna(False).astype(bool) & ~sig
        row = {"predicted": pred}
        for per, m in (("discovery", cal < SPLIT), ("confirmation", cal >= SPLIT)):
            use = (sig | cmp_) & m & r.notna()
            b, t = e29.nw_test(r[use].to_numpy(), sig[use].astype(float).to_numpy())
            row[per] = {"b_bps": b * 1e4, "t": t, "p_two": e29.p_two(t), "signal_days": int((sig & use).sum()),
                        "comparison_days": int((cmp_ & use).sum())}
        res[k] = row
    ps = sorted((res[k]["discovery"]["p_two"], k) for k in res)
    cut = 0
    for i, (p, k) in enumerate(ps, 1):
        if p <= 0.10 * i / len(ps):
            cut = i
    passed = [k for _, k in ps[:cut]]
    conf = []
    for k in passed:
        sgn = 1.0 if res[k]["discovery"]["b_bps"] > 0 else -1.0
        res[k]["confirmation"]["p_one"] = e29.p_one(res[k]["confirmation"]["t"], sgn)
        conf.append((res[k]["confirmation"]["p_one"], k))
    conf.sort()
    holm = set()
    for i, (p, k) in enumerate(conf):
        if p <= 0.05 / (len(conf) - i):
            holm.add(k)
        else:
            break
    m = cal >= SPLIT
    for k in res:
        v = "FAILS DISCOVERY" if k not in passed else ("CONFIRMED" if k in holm else "FAILS CONFIRMATION")
        if k in holm:
            sig, cmp_, _ = ideas[k]
            sig = pd.Series(sig, index=cal).fillna(False).astype(bool)
            cmp_ = pd.Series(cmp_, index=cal).fillna(False).astype(bool) & ~sig
            good = res[k]["discovery"]["b_bps"] > 0
            inm = (~cmp_ if good else ~sig)[m].astype(float)
            sw = inm.diff().abs().fillna(0)
            strat = inm * r[m] - sw * 0.0025
            sh = lambda x: float(x.mean() / x.std() * math.sqrt(365))  # noqa: E731
            res[k]["economic"] = {"sharpe": sh(strat), "btc_sharpe": sh(r[m]), "time_in_market": float(inm.mean())}
            if res[k]["economic"]["sharpe"] > res[k]["economic"]["btc_sharpe"]:
                v = "CONFIRMED AND ECONOMIC"
        res[k]["verdict"] = v
    open(out, "w").write(json.dumps(res, indent=1))
    for k, v in res.items():
        dsc, cf = v["discovery"], v["confirmation"]
        print(k, f"disc {dsc['b_bps']:.1f}bp t {dsc['t']:.2f} n {dsc['signal_days']} | conf {cf['b_bps']:.1f}bp t {cf['t']:.2f} n {cf['signal_days']} | {v['verdict']}", v.get("economic", ""))


if __name__ == "__main__":
    main()
```
