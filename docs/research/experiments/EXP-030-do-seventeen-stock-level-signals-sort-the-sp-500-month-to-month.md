# EXP-030 — Do seventeen stock-level signals, plausible and strange, sort the S&P 500 month to month?

**Status:** PRE-REGISTERED 2026-10-24 (planner, `a68d6f6c`) · **COMPLETE 2026-10-24: all seventeen fail
discovery; none sorts the S&P 500 month to month.**
**Decision / origin:** [R012](../idea-testing-foundation/INDEX.md) batch 3 · [DL-319](../../design-log.md)
· the operator, 2026-10-24: *"Let's test every idea (no matter how strange)"* · **Cost:** $0.

## 1. Why we needed this experiment

R012's third batch: signals about single stocks that the project has not tested, from the published
(closeness to the 52-week high, lottery stocks, low volatility, momentum, same-month seasonality,
volume shocks, media attention, nominal price, round-number prices) to the strange (a ticker that is a
common English word, alphabetical order, ticker length, "sin" industries). One month's holding keeps
turnover, and so cost, low.

## 2. Hypothesis

**The statistic.** Each month-end, S&P 500 members are sorted by the signal; the next month's
equal-weighted return of the top quintile minus the bottom (continuous signals), or of the signal group
minus the rest (binary signals), with the predicted sign of Appendix P. Monthly series; t-statistic with
Newey–West (2 lags); p-values from the normal.

**Discovery** (formations 2017-01 → 2021-06, 54 months): Benjamini–Hochberg at q = 10 % over the 17
two-sided p-values. **Confirmation** (formations 2021-07 → 2026-07, 61 months): one-sided in the
discovery's direction, Holm at 5 % across the passers. **Economic bar** for a confirmed idea: the
favourable group held long-only, rebalanced monthly, 25 bps a side on its turnover, beats the
equal-weighted universe on the confirmation months: mean net monthly excess above 0 with t above 1.65.

## 3. Data

The S235 cache (bars with volume, membership, sectors, benchmark; 2016-01-04 → 2026-09-25; checksums
as EXP-022 §3); the Benzinga archive (EXP-024) for headline counts; a list of the 9,894 most common
English words (`first20hours/google-10000-english`, no-swears version, fetched 2026-10-24) for ticker
fluency. Adjustment-error crossings are masked as in EXP-025.

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; no repo code; no randomness; $0.

## 5. How it was conducted

1. Month-ends are the cache's last session of each month. A stock is in the month's universe if it is
   a member at the formation close and has that close; its holding return runs from that close to the
   next month-end close (or its last close if its bars end, as in EXP-025).
2. Signals by Appendix P, from data up to the formation close only.
3. Quintiles by signal each month (binary signals: the group against the rest), equal weights.
4. Discovery, confirmation and the economic bar as section 2 fixes.
5. **Reported, not barred:** each idea's mean monthly spread in both periods, the group sizes, and
   the long-only group's mean excess over the universe.

**What this cannot claim.** Ten years and one index: power is modest (a monthly spread of about
0.8 % is needed to pass at 54 months). Momentum, trend and short-term reversal overlap rules EXP-023
already read at 10 sessions on the scanner's survivors.

## 6. Results

All MEASURED from the frozen script (Appendix R). Mean monthly spread (Appendix P's direction: top
quintile minus bottom, or group minus rest), Newey–West t; the economic column is the favourable
group's net monthly excess over the equal-weighted universe on the confirmation months.

| # | Idea | Predicted | Discovery 2017-01 → 2021-06 | Confirmation 2021-07 → 2026-07 | Favourable group, net | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| X1 | 52-week high | + | −0.23 % (−0.30) | −0.06 % (−0.11) | −0.34 % (−1.37) | fails discovery |
| X2 | Lottery stocks (MAX) | − | +0.36 % (0.60) | +0.66 % (1.16) | −0.58 % (−2.42) | fails discovery |
| X3 | Volatility | − | +0.20 % (0.28) | +0.74 % (1.18) | −0.50 % (−1.73) | fails discovery |
| X4 | Short-term reversal | − | −0.46 % (−1.11) | +0.66 % (1.45) | −0.75 % (−3.38) | fails discovery |
| X5 | Momentum 12−1 | + | −0.36 % (−0.52) | +0.68 % (1.34) | +0.27 % (1.04) | fails discovery |
| X6 | Same-month seasonality | + | +0.04 % (0.11) | −0.04 % (−0.12) | −0.39 % (−1.96) | fails discovery |
| X7 | Just below a round $10 | + | +0.01 % (0.11) | −0.07 % (−0.52) | −0.50 % (−3.77) | fails discovery |
| X8 | Ticker is a common word | + | −0.10 % (−0.61) | −0.12 % (−0.64) | −0.12 % (−0.70) | fails discovery |
| X9 | Ticker starts A–M | ± | +0.08 % (0.78) | −0.08 % (−0.87) | −0.04 % (−1.09) | fails discovery |
| X10 | One- or two-letter ticker | ± | −0.14 % (−0.86) | +0.19 % (1.36) | +0.16 % (1.26) | fails discovery |
| X11 | Sin stocks | + | **−0.67 % (−1.56)** | **−0.73 % (−1.82)** | −0.73 % (−1.84) | fails discovery |
| X12 | Media attention | − | +0.41 % (1.35) | +0.49 % (1.64) | −0.47 % (−3.81) | fails discovery |
| X13 | Recent index addition | ± | −0.41 % (−0.62) | +0.77 % (0.87) | +0.58 % (0.67) | fails discovery |
| X14 | Nominal price | + | −0.13 % (−0.21) | −0.64 % (−1.74) | −0.44 % (−2.16) | fails discovery |
| X15 | Volume shock | + | +0.16 % (0.67) | −0.22 % (−0.74) | −0.59 % (−3.33) | fails discovery |
| X16 | Beta | ± | +0.83 % (1.02) | +0.80 % (0.92) | +0.57 % (1.16) | fails discovery |
| X17 | Trend (200-day) | + | +0.22 % (0.41) | +0.44 % (0.85) | +0.05 % (0.18) | fails discovery |

**Benjamini–Hochberg at 10 % passes none of the seventeen**; the smallest discovery p-value is 0.12
(sin stocks, in the opposite direction to the claim).

## 7. Conclusions

1. **No stock-level signal sorts the S&P 500 month to month, plausible or strange.** Seventeen ideas,
   including six with a published effect in large samples, read inside two standard errors in both
   periods. This is Chen and Welch's finding (R011) on this project's own data.
2. **Where a sign is steady, it is against the claim.** Sin stocks trailed the index in both periods
   (−0.7 % a month) and media attention leaned the wrong way; neither clears the bar.
3. **Costs make the favourable groups worse than the index.** At 25 bps a side, most long-only groups
   trail the equal-weighted universe on the confirmation months.

## 8. Recommended code changes, and how to implement them

**None.** Next in R012: events and filings (FOMC days, the earnings-announcement premium, 13F copying,
congressional trades, short interest, filing text), then other markets.

## Appendix P — Pre-registration (frozen)

| # | Idea (source) | Signal at the formation close | Spread | Predicted |
| --- | --- | --- | --- | --- |
| X1 | 52-week high (George and Hwang 2004) | close ÷ the highest close of the last 252 sessions | Q5 − Q1 | + |
| X2 | Lottery stocks, MAX (Bali, Cakici and Whitelaw 2011) | the highest daily return of the last 21 sessions | Q5 − Q1 | − |
| X3 | Low volatility (Ang et al. 2006) | the standard deviation of the last 21 daily returns | Q5 − Q1 | − |
| X4 | Short-term reversal (Jegadeesh 1990) | the last 21 sessions' return | Q5 − Q1 | − |
| X5 | Momentum (Jegadeesh and Titman 1993) | return from 252 to 21 sessions ago | Q5 − Q1 | + |
| X6 | Same-month seasonality (Heston and Sadka 2008) | the stock's mean return in the coming calendar month in earlier years (at least one) | Q5 − Q1 | + |
| X7 | Round numbers (Bhattacharya, Holden and Jacobsen 2012) | among stocks within 2 % of a multiple of $10: just below it | below − above | + |
| X8 | Ticker fluency (Head, Smith and Watson 2009) | the ticker (letters only, 3 or more) is a common English word | group − rest | + |
| X9 | Alphabetical order | the ticker starts A–M | group − rest | ± |
| X10 | Ticker length | 1 or 2 letters | group − rest | ± |
| X11 | Sin stocks (Hong and Kacperczyk 2009) | MO, PM, STZ, BF.B, TAP, WYNN, LVS, MGM, CZR, PENN | group − rest | + |
| X12 | Media attention (Fang and Peress 2009) | Benzinga headlines naming the stock in the last 21 sessions | Q5 − Q1 | − |
| X13 | Recent index addition | its membership began within the last 63 sessions | group − rest | ± |
| X14 | Nominal price (Birru and Wang 2016) | the close in dollars | Q5 − Q1 | + |
| X15 | Volume shock (Gervais, Kaniel and Mingelgrin 2001) | mean volume of the last 5 sessions ÷ the last 63 | Q5 − Q1 | + |
| X16 | Beta | beta on SPY over the last 252 sessions | Q5 − Q1 | ± |
| X17 | Trend | close ÷ its 200-session average | Q5 − Q1 | + |

Discovery Benjamini–Hochberg q = 10 % over 17; confirmation Holm 5 % one-sided; economic: favourable
group long-only, net of 25 bps a side, mean monthly excess over the equal-weighted universe with
t > 1.65 on the confirmation months.

## Appendix R — Run record

- 2026-10-24, planner. Pilot (`--pilot`, group sizes only): 54 discovery and 61 confirmation months for
  every idea (X13: 49 and 58, months with at least three additions); about 100 stocks a quintile;
  binary groups: 51 word tickers, 327 A–M, 58 short tickers, 8 sin stocks, 5 additions a month.
- Frozen `exp030.py` SHA-256 `ba1179345e8abc29a2515232862db27bc364235b25d8591a8597a22c48e65374`;
  `exp030.json` SHA-256 `3dc95f69570050eba64d762e55e3093453409b18ff9fa9da0c5aa3946bbbe511`. Kit OneDrive
  `trading-agents-data/exp030-2026-10-24/` (with `common10k.txt`).

```text
python exp030.py <OneDrive>/trading-agents-data <OneDrive>/trading-agents-data/news-alpaca <kit>/common10k.txt <kit>/exp030.json
```

## Appendix S — Scripts

### `exp030.py`

```python
"""EXP-030 (R012 batch 3): seventeen stock-level signals on S&P 500 members, monthly.

Discovery formations 2017-01 → 2021-06 (BH q = 10 %), confirmation 2021-07 → 2026-07 (Holm 5 %,
one-sided), economic bar long-only at 25 bps a side. Usage:
python exp030.py <cache_dir> <news_dir> <words.txt> <out.json> [--pilot]
"""

from __future__ import annotations

import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ADJ = {"TGNA": "2017-06-01", "RTX": "2020-04-03", "APTV": "2017-12-05"}
SIN = {"MO", "PM", "STZ", "BF.B", "TAP", "WYNN", "LVS", "MGM", "CZR", "PENN"}
DISC_END, CONF_START, CONF_END = "2021-06-30", "2021-07-01", "2026-07-31"
PRED = {"X1": 1, "X2": -1, "X3": -1, "X4": -1, "X5": 1, "X6": 1, "X7": 1, "X8": 1, "X9": 0, "X10": 0,
        "X11": 1, "X12": -1, "X13": 0, "X14": 1, "X15": 1, "X16": 0, "X17": 1}
BINARY = {"X7", "X8", "X9", "X10", "X11", "X13"}
COST = 0.0025


def norm(t: str) -> str:
    return str(t).upper().replace("-", ".").replace("/", ".")


def nw_t(x: np.ndarray, lags: int = 2) -> float:
    x = x[~np.isnan(x)]
    n = len(x)
    e = x - x.mean()
    s = (e @ e) / n
    for l in range(1, lags + 1):
        s += 2 * (1 - l / (lags + 1)) * (e[l:] @ e[:-l]) / n
    return float(x.mean() / math.sqrt(s / n))


def main() -> None:
    cache, news, words_p, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
    pilot = "--pilot" in sys.argv
    bars = pd.read_csv(cache / "sp500_bars.csv.gz", parse_dates=["date"])
    C = bars.pivot(index="date", columns="line", values="close").sort_index()
    V = bars.pivot(index="date", columns="line", values="volume").reindex(C.index)
    SYM = bars.pivot(index="date", columns="line", values="symbol").reindex(C.index)
    cal, lines = C.index, list(C.columns)
    Cv, Vv = C.to_numpy(), V.to_numpy()
    R = Cv[1:] / Cv[:-1] - 1
    R = np.vstack([np.full((1, len(lines)), np.nan), R])
    brk = np.zeros_like(Cv, bool)
    for l, d in ADJ.items():
        if l in lines and pd.Timestamp(d) in cal:
            brk[cal.get_loc(pd.Timestamp(d)), lines.index(l)] = True
    R[brk] = np.nan
    cb = np.cumsum(brk, 0)
    mem = pd.read_csv(cache / "sp500_membership.csv.gz", parse_dates=["first", "last"])
    member = np.zeros_like(Cv, bool)
    added = np.full(len(lines), None, dtype=object)
    for r in mem.itertuples():
        if r.line in lines:
            j = lines.index(r.line)
            member[(cal >= r.first) & (cal <= r.last), j] = True
    first_dates = {lines.index(r.line): [] for r in mem.itertuples() if r.line in lines}
    for r in mem.itertuples():
        if r.line in lines and r.first > pd.Timestamp("2016-01-04"):
            first_dates[lines.index(r.line)].append(r.first)
    spy = pd.read_csv(cache / "sp500_benchmark.csv.gz", parse_dates=["date"]).set_index("date")["close"].reindex(cal)
    rs = spy.pct_change().to_numpy()
    words = {w.strip().lower() for w in open(words_p, encoding="utf-8") if len(w.strip()) >= 3}
    # media attention: headlines naming each line, by session
    key_to_line = {}
    for j, l in enumerate(lines):
        for s in pd.unique(SYM.iloc[:, j].dropna()):
            key_to_line.setdefault(norm(s), j)
    cnt = np.zeros_like(Cv)
    for f in sorted(news.glob("20*.jsonl.gz")):
        for line in gzip.open(f, "rt", encoding="utf-8"):
            it = json.loads(line)
            k = cal.searchsorted(pd.Timestamp(it["created_at"][:10]))
            if k >= len(cal):
                continue
            for s in it.get("symbols", []):
                j = key_to_line.get(norm(s))
                if j is not None:
                    cnt[k, j] += 1
    month = cal.to_period("M")
    me = [i for i in range(len(cal) - 1) if month[i] != month[i + 1]]
    me_set = me
    # monthly returns per line for seasonality
    mret = {}
    for a, b in zip(me[:-1], me[1:]):
        mret[cal[b].to_period("M")] = Cv[b] / Cv[a] - 1
    results = {k: {"months": []} for k in PRED}
    for a, b in zip(me[:-1], me[1:]):
        fdate = cal[a]
        if fdate < pd.Timestamp("2017-01-01") or fdate > pd.Timestamp(CONF_END):
            continue
        uni = member[a] & ~np.isnan(Cv[a])
        held = Cv[a + 1 : b + 1]
        last = pd.DataFrame(held).ffill().to_numpy()[-1]
        ret = last / Cv[a] - 1
        ret[(cb[b] - cb[a]) > 0] = np.nan
        uni &= ~np.isnan(ret)
        win = lambda n: slice(max(a - n + 1, 0), a + 1)  # noqa: E731
        with np.errstate(all="ignore"):
            hist = Cv[win(252)]
            sig = {
                "X1": Cv[a] / np.nanmax(hist, 0) * np.where(np.sum(~np.isnan(hist), 0) >= 200, 1, np.nan),
                "X2": np.nanmax(R[win(21)], 0),
                "X3": np.nanstd(R[win(21)], 0),
                "X4": Cv[a] / Cv[a - 21] - 1,
                "X5": (Cv[a - 21] / Cv[a - 252] - 1) if a >= 252 else np.full(len(lines), np.nan),
                "X14": Cv[a].copy(),
                "X15": np.nanmean(Vv[win(5)], 0) / np.nanmean(Vv[win(63)], 0),
                "X17": Cv[a] / np.nanmean(Cv[win(200)], 0) * np.where(np.sum(~np.isnan(Cv[win(200)]), 0) >= 200, 1, np.nan),
                "X12": np.where(np.sum(~np.isnan(Cv[win(21)]), 0) >= 21, cnt[win(21)].sum(0), np.nan),
            }
            rr, rm = R[win(252)], rs[win(252)]
            ok = ~np.isnan(rr) & ~np.isnan(rm)[:, None]
            beta = np.full(len(lines), np.nan)
            for j in np.nonzero(uni)[0]:
                m = ok[:, j]
                if m.sum() >= 200:
                    x, y = rm[m], rr[m, j]
                    beta[j] = np.cov(x, y)[0, 1] / np.var(x, ddof=1)
            sig["X16"] = beta
            target = cal[b].to_period("M")
            past = [mret[p] for p in mret if p.month == target.month and p < target and p <= fdate.to_period("M")]
            sig["X6"] = np.nanmean(np.vstack(past), 0) if past else np.full(len(lines), np.nan)
            k10 = np.round(Cv[a] / 10)
            rel = Cv[a] / (10 * k10) - 1
            near = (k10 >= 1) & (np.abs(rel) <= 0.02) & (rel != 0)
            sig["X7"] = np.where(near, (rel < 0).astype(float), np.nan)
        tick = np.array([norm(s) if isinstance(s, str) else "" for s in SYM.iloc[a]])
        letters = np.array([t.replace(".", "") for t in tick])
        sig["X8"] = np.array([1.0 if (len(t) >= 3 and t.isalpha() and t.lower() in words) else 0.0 for t in letters])
        sig["X9"] = np.array([1.0 if t[:1] and t[:1] <= "M" else 0.0 for t in letters])
        sig["X10"] = np.array([1.0 if 0 < len(t) <= 2 else 0.0 for t in letters])
        sig["X11"] = np.array([1.0 if t in SIN else 0.0 for t in tick])
        sig["X13"] = np.array([1.0 if any(cal[max(a - 62, 0)] <= d <= fdate for d in first_dates.get(j, [])) else 0.0
                               for j in range(len(lines))])
        umean = np.nanmean(ret[uni])
        for k, s in sig.items():
            v = np.where(uni, s, np.nan)
            ok = ~np.isnan(v)
            if k in BINARY:
                g1, g0 = ok & (v == 1), ok & (v == 0)
                if g1.sum() < 3 or g0.sum() < 3:
                    continue
                top, bot = g1, g0
            else:
                if ok.sum() < 50:
                    continue
                q = np.nanquantile(v, [0.2, 0.8])
                top, bot = ok & (v >= q[1]), ok & (v <= q[0])
            spread = np.nanmean(ret[top]) - np.nanmean(ret[bot])
            pred = PRED[k] if PRED[k] != 0 else 1
            fav = top if pred > 0 else bot
            results[k]["months"].append({"f": str(fdate.date()), "spread": float(spread), "n_top": int(top.sum()),
                                         "n_bot": int(bot.sum()), "fav_excess": float(np.nanmean(ret[fav]) - umean),
                                         "fav": [lines[j] for j in np.nonzero(fav)[0]]})
    res = {}
    for k, v in results.items():
        ms = v["months"]
        disc = [m for m in ms if m["f"] <= DISC_END]
        conf = [m for m in ms if m["f"] >= CONF_START]
        row = {"predicted": PRED[k], "disc_months": len(disc), "conf_months": len(conf),
               "mean_group_sizes": [float(np.mean([m["n_top"] for m in ms])) if ms else 0, float(np.mean([m["n_bot"] for m in ms])) if ms else 0]}
        if not pilot and len(disc) > 12 and len(conf) > 12:
            d = np.array([m["spread"] for m in disc])
            c = np.array([m["spread"] for m in conf])
            td, tc = nw_t(d), nw_t(c)
            row.update({"disc_mean_pct": float(d.mean() * 100), "disc_t": td, "disc_p": math.erfc(abs(td) / math.sqrt(2)),
                        "conf_mean_pct": float(c.mean() * 100), "conf_t": tc})
            # long-only favourable group, net of turnover cost, confirmation months
            prev, nets = None, []
            for m in conf:
                cur = set(m["fav"])
                turn = 1.0 if prev is None else len(cur ^ prev) / max(len(cur) + len(prev), 1)
                nets.append(m["fav_excess"] - 2 * COST * turn)
                prev = cur
            nets = np.array(nets)
            row["econ_net_mean_pct"] = float(nets.mean() * 100)
            row["econ_t"] = nw_t(nets)
        res[k] = row
    if pilot:
        for k, v in res.items():
            print(k, v["disc_months"], v["conf_months"], [round(x, 1) for x in v["mean_group_sizes"]])
        out.write_text(json.dumps(res, indent=1), encoding="utf-8")
        return
    ps = sorted((res[k]["disc_p"], k) for k in res if "disc_p" in res[k])
    m_, cut = len(ps), 0
    for i, (p, k) in enumerate(ps, 1):
        if p <= 0.10 * i / m_:
            cut = i
    passed = [k for _, k in ps[:cut]]
    conf = []
    for k in passed:
        sgn = 1.0 if res[k]["disc_mean_pct"] > 0 else -1.0
        res[k]["conf_p_one"] = 0.5 * math.erfc(res[k]["conf_t"] * sgn / math.sqrt(2))
        conf.append((res[k]["conf_p_one"], k))
    conf.sort()
    holm = set()
    for i, (p, k) in enumerate(conf):
        if p <= 0.05 / (len(conf) - i):
            holm.add(k)
        else:
            break
    for k in res:
        v = "FAILS DISCOVERY"
        if k in passed:
            v = "FAILS CONFIRMATION"
        if k in holm:
            v = "CONFIRMED"
            if res[k]["econ_net_mean_pct"] > 0 and res[k]["econ_t"] > 1.65:
                v = "CONFIRMED AND ECONOMIC"
        res[k]["verdict"] = v
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("BH passers:", passed, "| Holm confirmed:", sorted(holm))


if __name__ == "__main__":
    main()
```
