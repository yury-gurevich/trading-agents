# EXP-034 — How much of the after-close news move is left minutes after the headline?

**Status:** PRE-REGISTERED 2026-10-24 (planner, `79e62645`; Amendment 1 `b346f3ba` before any return) ·
**COMPLETE 2026-10-24: H0. Five minutes after an after-close headline, the good-news stocks still earn
+0.17 % over SPY to the next open, which 20 bps of cost takes; half the move is gone within a minute.**
**Amendment 1 — 2026-10-24, before any return was read (planner).** The coverage pilot found that many
stocks do not trade in the minutes after an evening headline: no minute bar starts after τ by τ + 1
minute for 65 % of events, by τ + 5 for 49 %, by τ + 15 for 38 %, by τ + 60 for 25 %. Section 5.2's
rule would price those entries at the last trade *before* the headline, a price no order placed after
the news could get. **The primary is therefore computed on the events with a trade after the headline
by τ + 5 minutes** (the entry bar starts at or after τ's minute); the as-registered all-events figure
is reported beside it. Nothing else changes.
**Decision / origin:** [EXP-028](EXP-028-does-an-llm-reading-headlines-after-its-cutoff-predict-the-next-day.md)
§7.4 and §8; the operator, 2026-10-24, on the fleet's next-open entry: *"Is this something that can be
changed?"* · [DL-319](../../design-log.md) · **Cost:** $0 (Alpaca market data; no new LLM call).

## 1. Why we needed this experiment

EXP-028 found that `gpt-4o-mini` reads after-close headlines correctly: the stocks it called good rose
0.38 % by the next open and those it called bad fell 1.06 % (a spread of 1.43 %), but the whole move sits
in the overnight gap, before the fleet's next-open entry. Alpaca accepts extended-hours limit orders
(16:00–20:00 ET), and its minute bars include extended hours *[measured 2026-10-24: AAPL on 2024-05-02,
bars through the evening and the pre-market]*. If part of the move is still there a few minutes after a
headline, an event-driven reader (news stream → model → after-hours order) could take it. If it is gone
within a minute, no build can.

## 2. Hypothesis

**Events.** EXP-028's stock-sessions whose headlines arrived after the close (16:00–18:30 ET), labelled
good or bad by the mean of those headlines' labels (EXP-028's, unchanged). The event time τ is the first
after-close headline's timestamp.

**The statistic.** For a delay L, the entry price is the close of the last minute bar that starts before
τ + L; the exit is the next session's open (the S235 cache, as EXP-028). X_L = the stock's return from
entry to exit minus SPY's over the same window (SPY's minute bars and next open).

- **Primary, H1 — the move can be taken.** For L = 5 minutes, the per-session mean of the good stocks'
  X_5, **net of 20 bps** (an after-hours limit entry and an opening exit), is above 0 with the lower
  bound of its 95 % interval above 0, and above 0 in each half of the sessions.
- **H0 — it cannot.** Otherwise.

**The interval.** Stationary block bootstrap over sessions, mean block 20, 5,000 resamples, seed 0.

**Why this bar.** Five minutes covers a news stream's delivery, a model call and an order with room to
spare; 20 bps a round trip allows for after-hours spreads several times the regular session's. Only the
good side is primary: the fleet buys, it does not sell short.

## 3. Data

EXP-028's kit (`headlines.csv.gz`, the labels in `out_req_*.jsonl`); Alpaca SIP **1-minute bars**,
`adjustment=all`, 16:00–20:00 ET on each event session, for the event symbols and SPY (fetched for this
experiment, kit `exp034-2026-10-24/`); the S235 cache's daily opens for the exit.

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; the provider's Alpaca data key; no LLM; $0.

## 5. How it was conducted

1. Event stock-sessions from EXP-028's after-close headlines (labels as frozen there); τ per stock-
   session. L = 1, 5, 15, 60 minutes.
2. Entry price as section 2; if no bar falls between τ and τ + L, the last earlier bar's close is used
   and the event is flagged stale (its share reported).
3. Exit: the next session's open in the S235 cache; SPY's from the SPY benchmark file.
4. **Reported, not barred:** good minus bad and good alone at every L, and the share of EXP-028's
   close-to-open spread still left at each L; the result at 10 and 40 bps; stale shares; by year.
5. **Pilot (before the freeze):** coverage only (events with an entry bar and an exit), no return.

**What this cannot claim.** A minute bar's close is not a fill: an order arriving at τ + 5 minutes may
trade worse, more so in thin evening trading, which the 20 bps is meant to absorb. Benzinga's
timestamp may lag the company's release by seconds or minutes; the delay is counted from what the
fleet would see.

## 6. Results

All MEASURED from the frozen script (Appendix R). Coverage: 7,862 after-close stock-sessions (5,996
good, 1,859 bad) on 679 sessions, 7,855 priced; a trade after the headline exists for 35 % of events by
1 minute, 51 % by 5, 62 % by 15, 75 % by 60.

**Primary (Amendment 1: good stocks with a trade after the headline by τ + 5 minutes; 2,885 events, 629
sessions): H0.** Gross excess over SPY to the next open **+0.174 %**; net of 20 bps **−0.026 %**
[−0.144, +0.102], halves −0.055 % and +0.002 %. At 10 bps +0.074 % [−0.044, +0.202]; at 40 bps
−0.226 % [−0.344, −0.098]. By year, gross: 2024 +0.229 %, 2025 +0.141 %, 2026 +0.148 %.
**As registered (all good events, stale prices included; 5,995 events):** gross +0.146 %, net of 20 bps
−0.054 % [−0.109, +0.004].

**How fast the move goes** (reported, not barred; to the next open, excess over SPY; *live* = events
with a trade after the headline by that delay):

| Delay after the headline | Good stocks, live | Bad stocks, live | Good − bad, live | Good − bad, all events |
| --- | --- | --- | --- | --- |
| at the close (EXP-028, for scale) | +0.376 % | −1.059 % | +1.433 % | — |
| 1 minute | +0.266 % (1,987) | −0.482 % | +0.665 % | +0.393 % |
| 5 minutes | +0.174 % (2,885) | −0.137 % | +0.312 % | +0.229 % |
| 15 minutes | +0.123 % (3,586) | −0.128 % | +0.235 % | +0.150 % |
| 60 minutes | +0.135 % (4,383) | −0.003 % | +0.112 % | +0.075 % |

## 7. Conclusions

1. **The after-hours market prices the news within minutes.** Of the 1.4 % spread between good and bad
   after-close news, under half is left one minute after the headline and about a fifth after five.
2. **What is left at five minutes does not pay a realistic cost.** The good-news stocks' +0.17 % to the
   next open is taken by 20 bps of after-hours spread and opening exit; H0. A minute bar's close is
   also kinder than a real fill in thin evening trading.
3. **The fleet's entry cannot be changed into an edge with this signal.** Only a sub-minute reader
   with near-zero cost could reach the +0.27 % left at one minute (a figure read here after the fact,
   gross of fills): high-frequency territory, not this fleet's.
4. **Taken with EXP-028:** the model understands news, and so does the market, faster.

## 8. Recommended code changes, and how to implement them

**None.** No event-driven news reader is worth a sprint on this evidence.

## Appendix P — Pre-registration (frozen)

- Events: EXP-028's after-close stock-sessions (headlines 16:00–18:30 ET on the decision session),
  label = mean of their EXP-028 labels; good > 0, bad < 0; τ = the first such headline's timestamp.
- Entry at L ∈ {1, 5, 15, 60} minutes: the close of the last 1-minute bar starting before τ + L (stale
  if none starts after τ). Exit: the next session's open. X_L = stock return − SPY return over the same
  window.
- **Primary:** L = 5, good stocks, per-session mean of X_5 − 0.20 %; H1 if the 95 % interval's lower
  bound (stationary block bootstrap, block 20, 5,000, seed 0) is above 0 and both halves' means are
  above 0; else H0.

## Appendix R — Run record

- 2026-10-24, planner. `exp034.py fetch`: 538,271 one-minute bars (16:00–20:00 ET) for 7,862 events on
  680 sessions plus SPY. Coverage pilot (no return): the stale shares behind Amendment 1.
- After Amendment 1 the scorer was changed to compute the primary on live entries and keep the
  as-registered figure; a dead helper left by the change was removed before the freeze.
- Frozen `exp034.py` SHA-256 `05cb8eb34c6704f3ba2f790078f8231702822876384c3e966e5d69cb82d2aee9`;
  `minute_bars.csv.gz` `6dddc48c2a7bc63938132b658b917ccc8c2587ae00675cb5230a66400c4b710a`; scored
  once; `exp034.json` `4077085e0d218ec84b6f3622778f090a6fc56db0f3e69f1d30abb58381adf7ee`. Kit OneDrive
  `trading-agents-data/exp034-2026-10-24/`.

```text
python exp034.py fetch <exp028 kit> <repo>/.env <kit>/minute_bars.csv.gz
python exp034.py pilot <exp028 kit> <kit>/minute_bars.csv.gz <OneDrive>/trading-agents-data <kit>/pilot.json
python exp034.py score <exp028 kit> <kit>/minute_bars.csv.gz <OneDrive>/trading-agents-data <kit>/exp034.json
```

## Appendix S — Scripts

### `exp034.py`

```python
"""EXP-034: how much of the after-close news move is left L minutes after the headline (after-hours).

Usage: python exp034.py fetch <exp028_kit> <env_file> <bars_out.csv.gz>
       python exp034.py pilot|score <exp028_kit> <bars.csv.gz> <sp500_cache_dir> <out.json>
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

LS = (1, 5, 15, 60)
COSTS = (0.0010, 0.0020, 0.0040)
B, SEED, BLOCK = 5000, 0, 20


def norm(t: str) -> str:
    return str(t).upper().replace("-", ".").replace("/", ".")


def env(path: str) -> dict[str, str]:
    out = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def events(kit: Path) -> pd.DataFrame:
    sys.path.insert(0, str(kit))
    import exp028_score as s  # the frozen labeller

    lab, _ = s.labels(kit)
    h = pd.read_csv(kit / "headlines.csv.gz", dtype={"id": str}, parse_dates=["session"])
    h = h[h["tclass"] == "after_close"].merge(lab, on=["id", "symbol"], how="inner")
    h["ts"] = pd.to_datetime(h["created_at"], utc=True)
    g = h.groupby(["symbol", "session"]).agg(label=("label", "mean"), tau=("ts", "min"), n=("id", "size")).reset_index()
    return g[g["label"] != 0].reset_index(drop=True)


def fetch(kit: Path, envf: str, out: Path) -> None:
    ev = events(kit)
    e = env(envf)
    H = {"APCA-API-KEY-ID": e["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": e["ALPACA_API_SECRET"]}
    rows = []
    for sess, grp in ev.groupby("session"):
        day = pd.Timestamp(sess).tz_localize("America/New_York")
        start = (day + pd.Timedelta(hours=16)).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
        end = (day + pd.Timedelta(hours=20)).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
        syms = sorted(set(grp["symbol"])) + ["SPY"]
        for i in range(0, len(syms), 40):
            token = None
            while True:
                q = {"symbols": ",".join(syms[i : i + 40]), "timeframe": "1Min", "start": start, "end": end,
                     "adjustment": "all", "feed": "sip", "limit": 10000, "asof": pd.Timestamp(sess).strftime("%Y-%m-%d")}
                if token:
                    q["page_token"] = token
                url = "https://data.alpaca.markets/v2/stocks/bars?" + urllib.parse.urlencode(q)
                for attempt in range(5):
                    try:
                        body = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=60))
                        break
                    except urllib.error.HTTPError as err:
                        if err.code == 429:
                            time.sleep(5 * (attempt + 1))
                            continue
                        raise
                for sym, bars in (body.get("bars") or {}).items():
                    rows += [(str(sess.date()), sym, b["t"], b["c"]) for b in bars]
                token = body.get("next_page_token")
                time.sleep(0.31)
                if not token:
                    break
    pd.DataFrame(rows, columns=["session", "symbol", "t", "close"]).to_csv(out, index=False, compression="gzip")
    print("events", len(ev), "sessions", ev["session"].nunique(), "bar rows", len(rows))


def stationary(n, rng):
    out = np.empty((B, n), np.int64)
    pos = np.arange(n)
    for k in range(B):
        st = rng.random(n) < 1.0 / BLOCK
        st[0] = True
        grp = np.cumsum(st) - 1
        first = pos[st]
        base = rng.integers(n, size=len(first))
        out[k] = (base[grp] + pos - first[grp]) % n
    return out


def analyse(kit: Path, bars_p: Path, cache: Path, out: Path, pilot: bool) -> None:
    ev = events(kit)
    bars = pd.read_csv(bars_p, parse_dates=["t"])
    bars["session"] = pd.to_datetime(bars["session"])
    bars["key"] = bars["symbol"].map(norm)
    by = {k: g.sort_values("t") for k, g in bars.groupby(["key", "session"])}
    daily = pd.read_csv(cache / "sp500_bars.csv.gz", usecols=["symbol", "date", "open"], parse_dates=["date"])
    daily = daily[daily["date"] >= "2023-12-01"]
    daily["key"] = daily["symbol"].map(norm)
    dopen = daily.drop_duplicates(["key", "date"]).set_index(["key", "date"])["open"]
    spy = pd.read_csv(cache / "sp500_benchmark.csv.gz", parse_dates=["date"]).set_index("date")["open"]
    cal = spy.index
    rows = []
    for r in ev.itertuples():
        k = cal.searchsorted(r.session)
        if k + 1 >= len(cal) or cal[k] != r.session:
            continue
        nxt = cal[k + 1]
        x_open = dopen.get((norm(r.symbol), nxt))
        s_open = spy.get(nxt)
        b = by.get((norm(r.symbol), r.session))
        sb = by.get(("SPY", r.session))
        if x_open is None or b is None or sb is None or np.isnan(x_open):
            continue
        row = {"session": r.session, "label": r.label}
        for L in LS:
            cut = r.tau + pd.Timedelta(minutes=L) - pd.Timedelta(minutes=1)
            bb, ss = b[b["t"] <= cut], sb[sb["t"] <= cut]
            if bb.empty or ss.empty:
                row[f"x{L}"] = np.nan
                continue
            row[f"stale{L}"] = bool(bb["t"].iloc[-1] < r.tau.floor("min"))
            row[f"x{L}"] = (x_open / bb["close"].iloc[-1] - 1) - (s_open / ss["close"].iloc[-1] - 1)
        rows.append(row)
    R = pd.DataFrame(rows)
    res = {"events": int(len(ev)), "priced": int(len(R)), "good": int((R["label"] > 0).sum()), "bad": int((R["label"] < 0).sum()),
           "sessions": int(R["session"].nunique())}
    for L in LS:
        res[f"coverage_{L}"] = float(R[f"x{L}"].notna().mean())
        res[f"stale_{L}"] = float(R.get(f"stale{L}", pd.Series(dtype=bool)).fillna(False).mean())
    if pilot:
        print(json.dumps(res, indent=1))
        return
    rng = np.random.default_rng(SEED)
    for tag, good in (("primary", R[(R["label"] > 0) & (R["stale5"] == False)]),  # noqa: E712  Amendment 1
                      ("registered_all_events", R[R["label"] > 0])):
        s5 = good.dropna(subset=["x5"]).groupby("session")["x5"].mean().sort_index()
        d = stationary(len(s5), rng)
        for c in COSTS:
            net = s5.to_numpy() - c
            boot = net[d].mean(1)
            half = len(net) // 2
            res[f"{tag}_{int(c * 1e4)}bps"] = {"sessions": int(len(net)), "events": int(good["x5"].notna().sum()),
                                               "mean_net_pct": float(net.mean() * 100),
                                               "ci95_pct": [float(np.percentile(boot, 2.5) * 100), float(np.percentile(boot, 97.5) * 100)],
                                               "halves_pct": [float(net[:half].mean() * 100), float(net[half:].mean() * 100)]}
        res[f"{tag}_gross_pct"] = float(s5.mean() * 100)
        if tag == "primary":
            res["by_year_good_x5_pct"] = {str(y): float(v * 100) for y, v in s5.groupby(s5.index.year).mean().items()}
    p = res["primary_20bps"]
    res["verdict"] = "H1" if (p["ci95_pct"][0] > 0 and min(p["halves_pct"]) > 0) else "H0"
    for L in LS:
        for tag, x in (("live", R[R[f"stale{L}"] == False]), ("all", R)):  # noqa: E712
            x = x.dropna(subset=[f"x{L}"])
            gm = x[x["label"] > 0].groupby("session")[f"x{L}"].mean()
            bm = x[x["label"] < 0].groupby("session")[f"x{L}"].mean()
            both = gm.index.intersection(bm.index)
            res[f"L{L}_{tag}"] = {"good_pct": float(gm.mean() * 100), "bad_pct": float(bm.mean() * 100),
                                  "good_minus_bad_pct": float((gm[both] - bm[both]).mean() * 100), "sessions_both": int(len(both)),
                                  "good_events": int((x["label"] > 0).sum())}
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "fetch":
        fetch(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))
    else:
        analyse(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5]), mode == "pilot")
```
