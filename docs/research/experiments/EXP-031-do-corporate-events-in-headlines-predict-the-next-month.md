# EXP-031 — Do corporate events named in headlines (analyst calls, buybacks, dividends, guidance, beats, approvals) predict the next month?

**Status:** PRE-REGISTERED 2026-10-24 (planner, `d92035ca`) · **COMPLETE 2026-10-24: none of the fourteen
testable events passes discovery; the next day's excess after each is about zero, so the news is priced
before the fleet's next open.** Two types (dividend cuts, splits) are too rare to test.
**Decision / origin:** [R012](../idea-testing-foundation/INDEX.md) batch 4a · [DL-319](../../design-log.md)
· the operator, 2026-10-24: *"Let's test every idea"* · **Cost:** $0.

## 1. Why we needed this experiment

Event studies hold some of finance's best-documented drifts: after analyst upgrades and downgrades
(Womack 1996), earnings surprises (post-earnings drift), buyback announcements (Ikenberry, Lakonishok
and Vermaelen 1995), dividend changes, stock splits, guidance changes. The project has the events in its
own news archive: Benzinga headlines name them in fixed phrases ("X Upgrades Y to Buy", "Y Beats Q3 EPS
Estimates"). This batch reads sixteen event types by keyword and asks whether a stock drifts after one,
as the fleet could trade it (the next open).

## 2. Hypothesis

**The statistic.** For each event type, the mean **20-session excess return** of the stocks it names:
from the open after the event's decision session (the 18:30 ET rule of EXP-028) to the close 20
sessions later, minus the S&P 500 members' equal-weighted mean over the same window. Events are averaged
per session, and the t-statistic is Newey–West (20 lags) over the session series.

**Discovery** (decision sessions 2016-10-03 → 2021-06-30): Benjamini–Hochberg at q = 10 % over the 16
two-sided p-values. **Confirmation** (2021-07-01 → 2026-08-26): one-sided in the discovery's direction,
Holm at 5 %. **Economic bar** for a confirmed positive event: buying it at the next open and selling 20
sessions later, 25 bps a side, earns a mean net excess above 0 with t above 1.65 on the confirmation
sessions; a confirmed negative event is an avoid rule and is reported only.

## 3. Data

The Benzinga archive (EXP-024; 2016-10 → 2026-10-23), headlines naming exactly one symbol that is an S&P
500 member on the decision session, de-duplicated by symbol, session and event; the S235 cache bars
(opens and closes) and membership.

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; no repo code; no randomness; $0.

## 5. How it was conducted

1. Each headline is matched against Appendix P's sixteen patterns (case-insensitive); a stock-session is
   an event of a type if any of its headlines match.
2. Returns: open(*t*+1) → close(*t*+20), minus the members' mean over the same window; also 1 and 5
   sessions (reported).
3. Discovery, confirmation and the economic bar as section 2 fixes; types with under 100 events in
   discovery read INSUFFICIENT.
4. **Reported, not barred:** counts, 1- and 5-session excess, hit rates, examples of matched headlines.

**What this cannot claim.** Keywords miss and mis-read some headlines (the pilot reports examples).
Benzinga's timestamps are its own; the open after the decision session is later than a fast trader's
entry, so a fail here does not rule out a faster reader.

## 6. Results

All MEASURED from the frozen script (Appendix R). Excess over the members' mean, from the open after the
decision session; t is Newey–West (20 lags) over the session series; net is the confirmation's 20-session
excess minus 0.50 %.

| # | Event | Pred. | Discovery: events, 20-session excess (t), next day | Confirmation: events, 20-session excess (t), next day, net | Verdict |
| --- | --- | --- | --- | --- | --- |
| E1 | Analyst upgrade | + | 5,931, −0.04 % (−0.05), −0.03 % | 5,117, +0.29 % (1.56), +0.05 %, −0.24 % | fails discovery |
| E2 | Analyst downgrade | − | 5,333, −0.01 % (−0.74), −0.11 % | 4,918, −0.06 % (−0.23), −0.01 % | fails discovery |
| E3 | Price target raised | + | 11,779, −0.18 % (−0.37), −0.03 % | 29,860, +0.08 % (−0.27), −0.01 %, −0.54 % | fails discovery |
| E4 | Price target cut | − | 6,882, +0.51 % (0.02), 0.00 % | 22,026, +0.09 % (−0.26), +0.02 % | fails discovery |
| E5 | Coverage initiated at buy | + | 2,151, +0.25 % (0.81), +0.02 % | 2,296, +0.59 % (1.99), +0.04 %, +0.20 % | fails discovery |
| E6 | Buyback announced | + | 331, −0.40 % (−0.68), +0.09 % | 727, +0.41 % (2.02), +0.15 %, +0.08 % | fails discovery |
| E7 | Dividend raised | + | 1,053, +0.11 % (−0.10), +0.01 % | 1,098, +0.04 % (0.19), +0.10 %, −0.45 % | fails discovery |
| E8 | Dividend cut | − | 41, −3.77 % (−1.83), −0.34 % | 17 | insufficient |
| E9 | Stock split | + | 40, +0.86 % (1.45), +0.66 % | 112, +0.97 % (0.47) | insufficient |
| E10 | Guidance raised | + | 1,015, −0.01 % (0.29), −0.15 % | 1,793, −0.13 % (−0.06), −0.09 %, −0.52 % | fails discovery |
| E11 | Guidance cut | − | 308, +0.44 % (0.67), −0.04 % | 625, −0.19 % (−1.18), +0.22 % | fails discovery |
| E12 | Earnings beat | + | 4,020, +0.04 % (0.84), −0.09 % | 7,575, +0.09 % (1.01), −0.04 %, −0.31 % | fails discovery |
| E13 | Earnings miss | − | 2,112, +0.28 % (1.80), +0.04 % | 3,610, −0.09 % (0.66), +0.04 % | fails discovery |
| E14 | CEO departure | − | 149, **−1.14 % (−2.08)**, −0.31 % | 169, −0.07 % (−0.39), −0.26 % | fails discovery |
| E15 | FDA approval | + | 512, −0.34 % (−0.64), −0.02 % | 631, +0.01 % (0.07), 0.00 %, −0.46 % | fails discovery |
| E16 | Legal trouble | − | 499, +0.77 % (1.74), −0.12 % | 976, +0.67 % (1.35), +0.14 % | fails discovery |

**Benjamini–Hochberg at 10 % passes none of the fourteen testable types**; the smallest p-value, CEO
departures' 0.038, is above its threshold of 0.007.

## 7. Conclusions

1. **The events are priced before the fleet can act.** The day after an upgrade, a beat, a raised
   target or guidance, or an approval, S&P 500 names earn within ±0.15 % of the index: the reaction
   happens at the announcement or overnight, before the next open.
2. **No drift follows over the month either.** Post-earnings drift, analyst-revision drift and the
   buyback drift, among the most published event effects, read about zero in large caps from 2016,
   as Martineau found for earnings (R011).
3. **The near misses do not hold.** CEO departures (−1.14 %, t −2.1, 149 events) fade to −0.07 % after
   2021; initiations at buy and buybacks lean positive after 2021 only; legal trouble leans the wrong way.

## 8. Recommended code changes, and how to implement them

**None.** A faster reader (minutes, not the next open) is the only form this batch leaves open; it
would need intraday prices to test and a different fleet to trade.

## Appendix P — Pre-registration (frozen)

| # | Event | Pattern (Python `re`, case-insensitive, on the headline) | Predicted |
| --- | --- | --- | --- |
| E1 | Analyst upgrade | `\bupgrade[sd]?\b` and not `downgrad` | + |
| E2 | Analyst downgrade | `\bdowngrade[sd]?\b` | − |
| E3 | Price target raised | `price target (raised\|increased\|boosted\|lifted\|bumped)\|(raises\|lifts\|boosts\|bumps\|increases) (its \|the )?price target` | + |
| E4 | Price target cut | `price target (lowered\|cut\|reduced\|trimmed\|slashed)\|(lowers\|cuts\|trims\|reduces\|slashes) (its \|the )?price target` | − |
| E5 | Coverage initiated at buy | `initiat\w* .*\b(buy\|outperform\|overweight)\b` | + |
| E6 | Buyback announced | `\b(buyback\|repurchase)\b` and `\b(announc\|authoriz\|approv\|new\|launch)` | + |
| E7 | Dividend raised | `\b(raises\|increases\|hikes\|boosts\|lifts)\b.*\bdividend\|\bdividend (increase\|hike\|raise)` | + |
| E8 | Dividend cut | `\b(cuts\|slashes\|suspends\|reduces\|eliminates\|halts)\b.*\bdividend\|\bdividend (cut\|suspension)` | − |
| E9 | Stock split announced | `\bstock split\b\|\b\d+-for-\d+\b` | + |
| E10 | Guidance raised | `\b(raises\|boosts\|lifts\|increases\|ups\|hikes)\b.*\b(guidance\|outlook\|forecast)\|\b(guidance\|outlook)\b.*\b(raised\|above)\b` | + |
| E11 | Guidance cut | `\b(lowers\|cuts\|reduces\|slashes\|trims)\b.*\b(guidance\|outlook\|forecast)\|\b(guidance\|outlook)\b.*\b(lowered\|below)\b` | − |
| E12 | Earnings beat | `\b(beats\|tops\|exceeds\|surpasses)\b.*\b(estimate\|consensus\|eps\|expectations)` | + |
| E13 | Earnings miss | `\b(misses\|falls short\|miss)\b.*\b(estimate\|consensus\|eps\|expectations)` | − |
| E14 | CEO departure | `\bceo\b.*\b(resign\|steps? down\|depart\|to exit\|retire\|ousted\|fired\|leaving)` | − |
| E15 | FDA approval | `\bfda\b.*\b(approv\|clears\|clearance\|grants)` | + |
| E16 | Legal trouble | `\b(sec probe\|investigation\|subpoena\|lawsuit\|sues\|sued\|class action\|antitrust)\b` | − |

Discovery BH q = 10 % over 16; confirmation Holm 5 % one-sided; economic for positive events: next-open
buy, 20-session hold, 25 bps a side, mean net excess > 0 with t > 1.65.

## Appendix R — Run record

- 2026-10-24, planner. Pilot (`--pilot`, counts and three matched headlines a type): discovery counts
  from 40 (splits) to 11,779 (raised targets); matches read correctly in the main, with known noise
  (reverse splits under E9, credit-rating outlooks under E11).
- Frozen `exp031.py` SHA-256 `8459724d35d190d04e2cf67d772dc0463503cf146e47bdf237833d7bb1ca7382`;
  `exp031.json` SHA-256 `eb687bf91b474e099f95f7b9c825afad6e32febffd87b72bc6e38fce55ee00c0`. Kit
  OneDrive `trading-agents-data/exp031-2026-10-24/`.

```text
python exp031.py <OneDrive>/trading-agents-data/news-alpaca <OneDrive>/trading-agents-data <kit>/exp031.json
```

## Appendix S — Scripts

### `exp031.py`

```python
"""EXP-031 (R012 batch 4a): sixteen corporate events read from Benzinga headlines, 20-session drift.

Usage: python exp031.py <news_dir> <cache_dir> <out.json> [--pilot]
"""

from __future__ import annotations

import gzip
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

START, DISC_END, CONF_START, END = "2016-10-01", "2021-06-30", "2021-07-01", "2026-08-26"
ADJ = {"TGNA": "2017-06-01", "RTX": "2020-04-03", "APTV": "2017-12-05"}
H = (1, 5, 20)
I = re.I
EV = {
    "E1": (lambda s: re.search(r"\bupgrade[sd]?\b", s, I) and not re.search(r"downgrad", s, I), 1),
    "E2": (lambda s: re.search(r"\bdowngrade[sd]?\b", s, I), -1),
    "E3": (lambda s: re.search(r"price target (raised|increased|boosted|lifted|bumped)|(raises|lifts|boosts|bumps|increases) (its |the )?price target", s, I), 1),
    "E4": (lambda s: re.search(r"price target (lowered|cut|reduced|trimmed|slashed)|(lowers|cuts|trims|reduces|slashes) (its |the )?price target", s, I), -1),
    "E5": (lambda s: re.search(r"initiat\w* .*\b(buy|outperform|overweight)\b", s, I), 1),
    "E6": (lambda s: re.search(r"\b(buyback|repurchase)\b", s, I) and re.search(r"\b(announc|authoriz|approv|new|launch)", s, I), 1),
    "E7": (lambda s: re.search(r"\b(raises|increases|hikes|boosts|lifts)\b.*\bdividend|\bdividend (increase|hike|raise)", s, I), 1),
    "E8": (lambda s: re.search(r"\b(cuts|slashes|suspends|reduces|eliminates|halts)\b.*\bdividend|\bdividend (cut|suspension)", s, I), -1),
    "E9": (lambda s: re.search(r"\bstock split\b|\b\d+-for-\d+\b", s, I), 1),
    "E10": (lambda s: re.search(r"\b(raises|boosts|lifts|increases|ups|hikes)\b.*\b(guidance|outlook|forecast)|\b(guidance|outlook)\b.*\b(raised|above)\b", s, I), 1),
    "E11": (lambda s: re.search(r"\b(lowers|cuts|reduces|slashes|trims)\b.*\b(guidance|outlook|forecast)|\b(guidance|outlook)\b.*\b(lowered|below)\b", s, I), -1),
    "E12": (lambda s: re.search(r"\b(beats|tops|exceeds|surpasses)\b.*\b(estimate|consensus|eps|expectations)", s, I), 1),
    "E13": (lambda s: re.search(r"\b(misses|falls short|miss)\b.*\b(estimate|consensus|eps|expectations)", s, I), -1),
    "E14": (lambda s: re.search(r"\bceo\b.*\b(resign|steps? down|depart|to exit|retire|ousted|fired|leaving)", s, I), -1),
    "E15": (lambda s: re.search(r"\bfda\b.*\b(approv|clears|clearance|grants)", s, I), 1),
    "E16": (lambda s: re.search(r"\b(sec probe|investigation|subpoena|lawsuit|sues|sued|class action|antitrust)\b", s, I), -1),
}


def norm(t: str) -> str:
    return str(t).upper().replace("-", ".").replace("/", ".")


def nw_t(x: np.ndarray, lags: int) -> float:
    n = len(x)
    e = x - x.mean()
    s = (e @ e) / n
    for l in range(1, min(lags, n - 1) + 1):
        s += 2 * (1 - l / (lags + 1)) * (e[l:] @ e[:-l]) / n
    return float(x.mean() / math.sqrt(s / n))


def main() -> None:
    news, cache, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    pilot = "--pilot" in sys.argv
    sessions = pd.DatetimeIndex(pd.read_csv(cache / "sp500_sessions.csv.gz")["date"])
    mem = pd.read_csv(cache / "sp500_membership.csv.gz")
    mem["key"] = mem["ticker"].map(norm)
    by_key = {k: g for k, g in mem.groupby("key")}
    rows = []
    for f in sorted(news.glob("20*.jsonl.gz")):
        if f.name[:7] < START[:7] or f.name[:7] > END[:7]:
            continue
        for line in gzip.open(f, "rt", encoding="utf-8"):
            it = json.loads(line)
            syms = {norm(s) for s in it.get("symbols", [])}
            if len(syms) != 1 or not it.get("headline"):
                continue
            hl = it["headline"]
            hits = [k for k, (fn, _) in EV.items() if fn(hl)]
            if hits:
                rows.append((syms.pop(), hl, it["created_at"], hits))
    df = pd.DataFrame(rows, columns=["symbol", "headline", "created_at", "hits"])
    ts = pd.to_datetime(df["created_at"], utc=True).dt.tz_convert("America/New_York")
    etd = ts.dt.tz_localize(None).dt.normalize()
    mins = ts.dt.hour * 60 + ts.dt.minute
    k = pd.Series(sessions.searchsorted(etd, side="left"), index=df.index)
    on = sessions[k.clip(upper=len(sessions) - 1)] == etd.to_numpy()
    k = k + (on & (mins > 18 * 60 + 30)).astype(int)
    df["session"] = sessions[k.clip(upper=len(sessions) - 1)].to_numpy()
    df = df[(df["session"] >= START) & (df["session"] <= END)]
    ok = []
    for s, d in zip(df["symbol"], df["session"].dt.strftime("%Y-%m-%d")):
        g = by_key.get(s)
        ok.append(bool(g is not None and ((g["first"] <= d) & (g["last"] >= d)).any()))
    df = df[pd.Series(ok, index=df.index)]
    ev = df.explode("hits").rename(columns={"hits": "event"})
    examples = {e: ev[ev["event"] == e]["headline"].head(3).tolist() for e in EV}
    ev = ev.drop_duplicates(["symbol", "session", "event"])
    if pilot:
        for e in EV:
            x = ev[ev["event"] == e]
            print(e, "disc", int((x["session"] <= DISC_END).sum()), "conf", int((x["session"] >= CONF_START).sum()), examples[e][:3])
        return
    bars = pd.read_csv(cache / "sp500_bars.csv.gz", parse_dates=["date"])
    bars = bars[bars["date"] >= "2016-06-01"]
    O = bars.pivot(index="date", columns="line", values="open").sort_index()
    C = bars.pivot(index="date", columns="line", values="close").reindex(O.index)
    cal, lines = O.index, list(O.columns)
    Ov, Cv = O.to_numpy(), pd.DataFrame(C).ffill(limit=25).to_numpy()
    raw_c = C.to_numpy()
    brk = np.zeros_like(Ov, bool)
    for l, d in ADJ.items():
        if l in lines and pd.Timestamp(d) in cal:
            brk[cal.get_loc(pd.Timestamp(d)), lines.index(l)] = True
    cb = np.cumsum(brk, 0)
    member = np.zeros_like(Ov, bool)
    for r in pd.read_csv(cache / "sp500_membership.csv.gz", parse_dates=["first", "last"]).itertuples():
        if r.line in lines:
            member[(cal >= r.first) & (cal <= r.last), lines.index(r.line)] = True
    bars["key"] = bars["symbol"].map(norm)
    key_line = bars.drop_duplicates(["key", "date"]).set_index(["key", "date"])["line"]
    pos = {d: i for i, d in enumerate(cal)}
    bench = {}
    n = len(cal)
    for h in H:
        m = np.full(n, np.nan)
        for i in range(n - h - 1):
            r = Cv[i + h] / Ov[i + 1] - 1
            okm = member[i] & ~np.isnan(r) & ~np.isnan(raw_c[i]) & ((cb[i + h] - cb[i]) == 0)
            if okm.any():
                m[i] = np.mean(r[okm])
        bench[h] = m
    rec = []
    for r in ev.itertuples():
        i = pos.get(r.session)
        line = key_line.get((r.symbol, r.session))
        if i is None or line is None or i + max(H) >= n:
            continue
        j = lines.index(line)
        o = Ov[i + 1, j]
        if np.isnan(o):
            continue
        x = {"event": r.event, "session": r.session, "i": i}
        for h in H:
            if cb[i + h, j] - cb[i, j] > 0:
                x[f"x{h}"] = np.nan
            else:
                x[f"x{h}"] = (Cv[i + h, j] / o - 1) - bench[h][i]
        rec.append(x)
    R = pd.DataFrame(rec)
    res = {}
    for e, (_, pred) in EV.items():
        x = R[R["event"] == e].dropna(subset=["x20"])
        row = {"predicted": pred}
        for per, m in (("discovery", x["session"] <= DISC_END), ("confirmation", x["session"] >= CONF_START)):
            y = x[m]
            row[per] = {"events": int(len(y))}
            if len(y) >= 30:
                s20 = y.groupby("i")["x20"].mean().sort_index().to_numpy()
                row[per].update({"x20_pct": float(y["x20"].mean() * 100), "t20": nw_t(s20, 20),
                                 "x1_pct": float(y["x1"].mean() * 100), "x5_pct": float(y["x5"].mean() * 100),
                                 "hit20": float((y["x20"] > 0).mean())})
                net = y.groupby("i")["x20"].mean().sort_index().to_numpy() - 0.005
                row[per].update({"net20_pct": float(net.mean() * 100), "net_t": nw_t(net, 20)})
        d = row["discovery"]
        if d["events"] >= 100 and "t20" in d:
            d["p_two"] = math.erfc(abs(d["t20"]) / math.sqrt(2))
        res[e] = row
    ps = sorted((res[e]["discovery"]["p_two"], e) for e in res if "p_two" in res[e]["discovery"])
    cut = 0
    for i, (p, e) in enumerate(ps, 1):
        if p <= 0.10 * i / len(ps):
            cut = i
    passed = [e for _, e in ps[:cut]]
    conf = []
    for e in passed:
        sgn = 1.0 if res[e]["discovery"]["x20_pct"] > 0 else -1.0
        c = res[e]["confirmation"]
        c["p_one"] = 0.5 * math.erfc(c["t20"] * sgn / math.sqrt(2)) if "t20" in c else 1.0
        conf.append((c["p_one"], e))
    conf.sort()
    holm = set()
    for i, (p, e) in enumerate(conf):
        if p <= 0.05 / (len(conf) - i):
            holm.add(e)
        else:
            break
    for e in res:
        v = "INSUFFICIENT" if "p_two" not in res[e]["discovery"] else "FAILS DISCOVERY"
        if e in passed:
            v = "FAILS CONFIRMATION"
        if e in holm:
            v = "CONFIRMED"
            c = res[e]["confirmation"]
            if res[e]["discovery"]["x20_pct"] > 0 and c.get("net20_pct", -1) > 0 and c.get("net_t", 0) > 1.65:
                v = "CONFIRMED AND ECONOMIC"
            elif res[e]["discovery"]["x20_pct"] < 0:
                v = "CONFIRMED (an avoid rule)"
        res[e]["verdict"] = v
        res[e]["examples"] = examples[e]
    out.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print("BH passers:", passed, "| Holm confirmed:", sorted(holm))


if __name__ == "__main__":
    main()
```
