# EXP-032 — Does the FOMC cycle still move the market after its papers' samples?

**Status:** PRE-REGISTERED 2026-10-24 (planner, `583c5a29`) · **COMPLETE 2026-10-24: both published FOMC
effects reproduce on their papers' samples and vanish after them; none is economic.**
**Decision / origin:** [R012](../idea-testing-foundation/INDEX.md) batch 4b · [DL-319](../../design-log.md)
· the operator, 2026-10-24: *"Let's test every idea"* · **Cost:** $0.

## 1. Why we needed this experiment

Two of the strongest published timing effects concern the Federal Reserve's scheduled meetings: the
**pre-FOMC drift** (Lucca and Moench 2015: the S&P 500 rose about 0.49 % in the 24 hours before
announcements, 1994–2011) and the **FOMC cycle** (Cieslak, Morse and Vissing-Jorgensen 2019: the equity
premium was earned in even weeks of the cycle, 1994–2016). Both are flows of a known schedule, R012's
third source. This experiment asks whether each held after its paper's sample.

## 2. Hypothesis

**The statistic.** *b*: the difference in SPY's mean daily return between signal days and other days
(OLS on a dummy, Newey–West 5 lags), as EXP-029.

**Discovery** = the paper's own sample (1994-02-04 → 2011-12-30 for F1 and F2, → 2016-12-30 for F3):
Benjamini–Hochberg at 10 % over the three. **Confirmation** = after it (2012-01-03 → 2026-10-23 for F1 and
F2; 2017-01-03 → for F3): one-sided in the discovery's direction, Holm at 5 %. **Economic bar:** holding
SPY on signal days only (cash, BIL, otherwise), 1 bp a side, beats SPY held throughout on Sharpe over the
confirmation period.

## 3. Data

SPY daily (Tiingo, adjusted, EXP-026's kit, 1993-01-29 → 2026-10-23); BIL for cash from 2007-05-30 (SHY
before, as EXP-026); **scheduled FOMC announcement dates** (the last day of each scheduled meeting) parsed
from the Federal Reserve's historical pages (1994–2020) and its meeting calendar (2021–2027): 271 dates,
8 a year (7 in 2020, when the March meeting was cancelled); unscheduled meetings, conference calls and
notation votes excluded (`fomc_parse.py`, kit `fomc_announcement_dates.txt`).

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; no repo code; $0.

## 5. How it was conducted

Signals by Appendix P on SPY's sessions; *b*, t and p as section 2; the funnel and the economic bar as
section 2. **Reported, not barred:** each idea's *b* in both periods, signal-day counts, and the
annualised effect.

**What this cannot claim.** Lucca and Moench measured 14:00-to-14:00 returns; a daily close-to-close
return on the announcement day holds the morning's drift and the afternoon's reaction together, so F1
is the tradable version (buy at the close before, sell at the close after), not their exact window.

## 6. Results

All MEASURED from the frozen script (Appendix R); SPY daily returns, *b* in basis points a day (t).

| # | Idea | Discovery (the paper's sample) | Confirmation (after it) | Verdict |
| --- | --- | --- | --- | --- |
| F1 | Announcement day | **+31.5 (2.98)**, 144 days, 1994–2011 | +4.7 (0.47), 117 days, 2012–2026; p 0.32 | fails confirmation |
| F2 | The day before | +12.0 (0.89), 143 days | +6.2 (0.88), 117 days | fails discovery |
| F3 | Even weeks of the cycle | **+9.0 (2.99)**, 3,000 days, 1994–2016 | **−6.3 (−1.43)**, 1,274 days, 2017–2026 | fails confirmation |

Benjamini–Hochberg passes F1 and F3 on discovery; Holm passes neither on confirmation. Held only on
signal days (1 bp a side), F1 earned 2.1 % a year against SPY's 14.9 % (Sharpe 0.20 against 0.83) and F3
4.0 % against 15.1 % (0.18 against 0.74).

## 7. Conclusions

1. **Both Fed effects were real in their papers' samples and are gone after them.** The announcement
   day earned +31.5 bps over other days in 1994–2011 and +4.7 bps since; the even-week cycle +9 bps a
   day to 2016 and −6.3 bps since. Publication decay, again (R011).
2. **No FOMC timing rule is worth building.**

## 8. Recommended code changes, and how to implement them

**None.**

## Appendix P — Pre-registration (frozen)

| # | Idea (source) | Signal days | Predicted |
| --- | --- | --- | --- |
| F1 | Announcement day (Lucca and Moench 2015) | the session of a scheduled announcement | + |
| F2 | The day before (Lucca and Moench 2015) | the session before it | + |
| F3 | Even weeks of the FOMC cycle (Cieslak, Morse and Vissing-Jorgensen 2019) | sessions −1 … +3, +10 … +14, +20 … +24, +30 … +34 counted from the latest announcement session (session −1 = the one before the next announcement) | + |

Comparison: every other SPY session from 1994-02-04. Discovery BH 10 % over 3; confirmation Holm 5 %
one-sided; economic: SPY on signal days only, 1 bp a side, against SPY held, by Sharpe.

## Appendix R — Run record

- 2026-10-24, planner. Fed pages fetched (1994–2021 historical, the calendar page); `fomc_parse.py`
  checked by eye year by year (8 a year, 7 in 2020; 2021's dates from the calendar page) before the
  pre-registration `583c5a29`.
- Frozen SHA-256: `exp032.py` `65ceb1caf4ec06ce76476e49527962c6e52005e97469485037c249e1c568df80`,
  `fomc_parse.py` `0385181686ce5951cd8bc9227c43ca2ba5b54be2288f8a4d3b301b67b2805227`,
  `fomc_announcement_dates.txt` `b2ff7983d41ff5dd0a6e7075d2f9dd49c9ead519c10361b441f186d2ae29fbef`;
  `exp032.json` `98fcbbf324b8d8aa07f774b60bb71377ac4dc34fb0494201df483af70a660c6d`. Kit OneDrive
  `trading-agents-data/exp032-2026-10-24/`.

```text
python fomc_parse.py <kit>/fed <kit>/fomc_announcement_dates.txt
python exp032.py <exp026 kit>/inputs/SPY.csv <...>/BIL.csv <...>/SHY.csv <kit>/fomc_announcement_dates.txt <kit>/exp032.json
```

## Appendix S — Scripts

### `fomc_parse.py`

```python
"""Parse scheduled FOMC announcement dates (the last day of each scheduled meeting), 1994-2027."""
import datetime as dt
import glob
import re
import sys
from pathlib import Path

MON = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                   "september", "october", "november", "december"], 1)}


def month_of(word):
    w = word.lower().strip(".")
    for k, v in MON.items():
        if k.startswith(w[:3]):
            return v
    return None


def parse(span, y):
    if re.search(r"unscheduled|cancel|notation|call", span, re.I):
        return None
    day = int(re.findall(r"\d+", span)[-1])
    words = [w for w in re.findall(r"[A-Za-z]+", span)]
    months = [month_of(p) for w in words for p in w.split("/") if month_of(p)]
    if "/" in span:
        months = [month_of(p) for p in re.findall(r"[A-Za-z]+", span.split("/")[-1])] or months
    return dt.date(y, months[-1], day)


fed = Path(sys.argv[1])
dates = {}
for f in sorted(glob.glob(str(fed / "h*.htm"))):
    t = open(f, encoding="utf-8", errors="replace").read()
    for h in re.findall(r"<h5[^>]*>(.*?)</h5>", t, re.S):
        h = re.sub(r"\s+", " ", h).strip()
        m = re.match(r"(.+?) Meeting - (\d{4})$", h)
        if m:
            d = parse(m.group(1), int(m.group(2)))
            if d:
                dates.setdefault(d.year, []).append(d)
t = open(fed / "cal.htm", encoding="utf-8", errors="replace").read()
for panel in re.split(r'<div class="panel panel-default">', t)[1:]:
    yh = re.search(r"(\d{4}) FOMC Meetings", panel)
    if not yh:
        continue
    y = int(yh.group(1))
    if y < 2021:
        continue
    for mo, dd in re.findall(r'fomc-meeting__month[^>]*>\s*<strong>([^<]+)</strong>.*?fomc-meeting__date[^>]*>([^<]+)<', panel, re.S):
        d = parse(f"{mo.strip()} {dd.strip().rstrip('*')}", y)
        if d:
            dates.setdefault(y, []).append(d)
out = []
for y in sorted(dates):
    ds = sorted(set(dates[y]))
    merged = []
    for d in ds:
        if merged and (d - merged[-1]).days <= 3:
            merged[-1] = d
        else:
            merged.append(d)
    out += merged
    print(y, len(merged), " ".join(d.strftime("%m-%d") for d in merged))
Path(sys.argv[2]).write_text("\n".join(str(d) for d in out) + "\n")
print("total", len(out))
```

### `exp032.py`

```python
"""EXP-032 (R012 batch 4b): the FOMC announcement day, the day before, and the even-week cycle, on SPY.

Usage: python exp032.py <spy.csv> <bil.csv> <shy.csv> <fomc_dates.txt> <out.json>
"""

from __future__ import annotations

import json
import math
import sys

import numpy as np
import pandas as pd

IDEAS = {"F1": ("2011-12-30", "2012-01-03"), "F2": ("2011-12-30", "2012-01-03"), "F3": ("2016-12-30", "2017-01-03")}


def nw(y, x, lags=5):
    X = np.column_stack([np.ones_like(x), x])
    A = np.linalg.inv(X.T @ X)
    beta = A @ X.T @ y
    u = X * (y - X @ beta)[:, None]
    S = u.T @ u
    for l in range(1, lags + 1):
        G = u[l:].T @ u[:-l]
        S += (1 - l / (lags + 1)) * (G + G.T)
    V = A @ S @ A
    return float(beta[1]), float(beta[1] / math.sqrt(V[1, 1]))


def main() -> None:
    spy_p, bil_p, shy_p, f_p, out = sys.argv[1:6]
    s = pd.read_csv(spy_p, parse_dates=["date"]).set_index("date")["adjClose"]
    s = s.loc["1994-01-01":]
    r = s.pct_change()
    cash = pd.read_csv(bil_p, parse_dates=["date"]).set_index("date")["adjClose"].pct_change().reindex(r.index)
    shy = pd.read_csv(shy_p, parse_dates=["date"]).set_index("date")["adjClose"].pct_change().reindex(r.index)
    cash = cash.fillna(shy).fillna(0.0)
    cal = r.index
    ann = pd.DatetimeIndex(pd.to_datetime(open(f_p).read().split()))
    ann = ann[(ann >= cal[0]) & (ann <= cal[-1])]
    pos = cal.searchsorted(ann)
    pos = pos[pos < len(cal)]
    f1 = np.zeros(len(cal), bool)
    f1[pos] = True
    f2 = np.zeros(len(cal), bool)
    f2[pos[pos > 0] - 1] = True
    f3 = np.zeros(len(cal), bool)
    last = -10**9
    nxt = np.searchsorted(pos, np.arange(len(cal)), side="left")
    for i in range(len(cal)):
        k_prev = np.searchsorted(pos, i, side="right") - 1
        k = i - pos[k_prev] if k_prev >= 0 else None
        to_next = pos[nxt[i]] - i if nxt[i] < len(pos) else None
        if to_next == 1:
            f3[i] = True
        elif k is not None and (0 <= k <= 3 or 10 <= k <= 14 or 20 <= k <= 24 or 30 <= k <= 34):
            f3[i] = True
    sig = {"F1": f1, "F2": f2, "F3": f3}
    valid = r.notna().to_numpy() & (cal >= "1994-02-04")
    res = {}
    for k, (d_end, c_start) in IDEAS.items():
        row = {}
        for per, m in (("discovery", (cal <= d_end)), ("confirmation", (cal >= c_start))):
            use = valid & m
            b, t = nw(r.to_numpy()[use], sig[k][use].astype(float))
            yrs = use.sum() / 252
            row[per] = {"b_bps": b * 1e4, "t": t, "p_two": math.erfc(abs(t) / math.sqrt(2)),
                        "signal_days": int((sig[k] & use).sum()), "days": int(use.sum()),
                        "annual_effect_pct": b * (sig[k] & use).sum() / yrs * 100}
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
        res[k]["confirmation"]["p_one"] = 0.5 * math.erfc(res[k]["confirmation"]["t"] * sgn / math.sqrt(2))
        conf.append((res[k]["confirmation"]["p_one"], k))
    conf.sort()
    holm = set()
    for i, (p, k) in enumerate(conf):
        if p <= 0.05 / (len(conf) - i):
            holm.add(k)
        else:
            break
    for k in res:
        v = "FAILS DISCOVERY" if k not in passed else ("CONFIRMED" if k in holm else "FAILS CONFIRMATION")
        m = valid & (cal >= IDEAS[k][1])
        posn = pd.Series(sig[k], index=cal)[m].astype(float)
        sw = posn.diff().abs().fillna(0)
        strat = posn * r[m] + (1 - posn) * cash[m] - sw * 0.0001
        ex_s, ex_m = strat - cash[m], r[m] - cash[m]
        yrs = m.sum() / 252
        res[k]["economic"] = {"sharpe": float(ex_s.mean() / ex_s.std() * math.sqrt(252)),
                              "spy_sharpe": float(ex_m.mean() / ex_m.std() * math.sqrt(252)),
                              "cagr_pct": float(((1 + strat).prod() ** (1 / yrs) - 1) * 100),
                              "spy_cagr_pct": float(((1 + r[m]).prod() ** (1 / yrs) - 1) * 100),
                              "time_in_market": float(posn.mean())}
        if v == "CONFIRMED" and res[k]["economic"]["sharpe"] > res[k]["economic"]["spy_sharpe"]:
            v = "CONFIRMED AND ECONOMIC"
        res[k]["verdict"] = v
    open(out, "w").write(json.dumps(res, indent=1))
    for k, v in res.items():
        d, c = v["discovery"], v["confirmation"]
        print(k, f"disc {d['b_bps']:.1f}bp t {d['t']:.2f} n {d['signal_days']} | conf {c['b_bps']:.1f}bp t {c['t']:.2f} n {c['signal_days']} | {v['verdict']} | econ {v['economic']}")


if __name__ == "__main__":
    main()
```
