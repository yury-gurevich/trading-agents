# EXP-027 — Do insiders' open-market purchases predict the next month's return? (the screen, 2017–2021)

**Status:** DESIGN FIXED 2026-10-24 (planner, `2ba192af`), before any outcome was computed: sections 1–5
and Appendix P. · **COMPLETE 2026-10-24: no cell passes (net 20-session excess −0.52 % to +0.36 %); the
operator's kill rule applies and the search for a trading edge ends.** This is the **screen** on 2017–2021; the confirmation on 2022–2026 is a separate
pre-registration (EXP-028), whose insider data is not downloaded until that pre-registration is
committed.
**Decision / origin:** [R011](../where-an-edge-can-exist/INDEX.md) §5 · [DL-317](../../design-log.md)
Amendments 1–2 · the operator, 2026-10-24, asked whether to run this last test or stop, and whether
their address may go in the SEC header: *"ok on both"* · **Cost:** $0 (SEC and Alpaca data).

## 1. Why we needed this experiment

**The decision that waits.** Whether the project keeps searching for a trading edge at all. Inside
single-stock picking (EXP-015, EXP-023, EXP-024, EXP-025) and outside it (EXP-026: nine published
strategies after publication) nothing carries. R011 named one class of input never tested here and
still supported by the literature: information that is slow to be priced, of which insiders'
open-market purchases are the cleanest (Cohen, Malloy and Pomorski 2012; cluster purchases about
+3.8 % over 21 days, 1986–2016; strongest in smaller firms).

**The kill rule, agreed by the operator before anything is read:** if no cell of this screen clears
its bar, or the confirmation (EXP-028) fails, **the search for a trading edge ends.**

## 2. Hypothesis

**Cells.** Three signals × two universes = six cells (Appendix P).

**The statistic.** For each cell, the mean over events of the **20-session excess return**: from the
open after the filing to the open 20 sessions later, minus the benchmark's return over the same
window, **minus 0.50 % for costs** (25 bps a side).

**The screen's bar (a cell passes):** the net mean is **at least +1.0 %**, and the net mean is above 0
in **at least 4 of the 5 years** 2017–2021 (by entry date).

**The outcome.** If at least one cell passes, EXP-028 is pre-registered on filings 2022-01-01 →
2026-06-30 for the passing cells only, with Holm across them and a bar no weaker than *the net mean's
95 % lower bound above 0*. If no cell passes: the kill rule applies.

**Why this bar.** It is R011 §5's, fixed before the data were fetched. +1 % net per month-long trade
is worth building on (about 12 % a year if capital turns monthly); a screen asks only whether a cell
is worth the confirmation, so it uses a point bar and the years' consistency, and leaves the interval
to the confirmation on unseen data.

## 3. Data

| Input | Span | Where |
| --- | --- | --- |
| SEC Form 345 data sets, 21 quarterly files | filings 2016 Q4 → 2021 Q4 (2016 Q4 only for the 30-day cluster look-back) | OneDrive `trading-agents-data/insider-sec/` |
| `purchases.csv.gz` (stage 1): every Form 4 open-market purchase line (code P, acquired) | 173,625 lines, 5,966 issuers | kit |
| Alpaca SIP daily bars, `adjustment=all`, resolved per filing quarter `asof` its last day; SPY and IWM | each quarter from 60 days before to 120 days after | kit `bars.csv.gz` |
| S235 S&P 500 cache (membership and bars) | 2016-01-04 → 2026-09-25 | OneDrive `trading-agents-data/` |

The kit is OneDrive `trading-agents-data/exp027-2026-10-24/`. SIP bars are licensed and never enter
the repo. **Known defects:** a filing's issuer symbol is typed by the filer ("NYSE: RPT", "LEN,
LEN.B"); it is cleaned to its first ticker and unparseable ones are dropped (counted); a symbol Alpaca
cannot resolve as of the quarter's end has no bars (counted as coverage).

## 4. Tools and setup

- **Machine.** Intel Core (family 6, model 142), 4 logical cores, 16 GB RAM, Windows 10 Pro.
- **Software.** Python 3.13.2, numpy 2.5.3, pandas 3.0.6 (the repo's main venv); no repo code.
- **Random seed.** 0. **External services.** sec.gov (the operator's address in the User-Agent, by
  their word), Alpaca market data (the provider key). **Cost cap.** $0.

## 5. How it was conducted

1. **Insider purchase lines:** a Form 4 (not 4/A) non-derivative line, code P, acquired, value
   (shares × price) at least $10,000, whose reporting owner is a director or an officer (ten-percent
   owners and "other" are left out).
2. **Events:** lines grouped by issuer symbol and filing date. **Entry:** the open of the first
   session strictly after the filing date (a Form 4 may be filed until 22:00 ET). **Exit:** the open
   20 sessions after entry (5 and 60 reported).
3. **Signals:** V1 any insider purchase; V2 a cluster, at least two distinct insiders with purchases
   filed within the 30 calendar days to the event's filing date; V3 a purchase by a CEO or CFO (title
   matching CEO, Chief Executive, CFO or Chief Financial). Per issuer and signal, no new event within
   20 sessions of the last one's entry.
4. **Universes:** U1, the issuer is an S&P 500 member on the filing date (S235 membership by ticker);
   the benchmark is the equal-weighted mean of all members over the same window (cache bars). U2,
   every issuer with bars, a close of at least $5 and a 20-session median dollar volume of at least
   $2 million before entry; the benchmark is IWM over the same window (Alpaca bars).
5. **Reported, not barred:** each cell's 95 % interval (stationary block bootstrap over entry dates,
   mean block 20, 2,000 resamples, seed 0), the gross mean, the hit rate, each year, 5 and 60
   sessions, U2 at 50 bps a side, and coverage (events with an entry and an exit price).
6. **Failure handling:** a cell with fewer than 100 events reads INSUFFICIENT, not a pass; coverage
   under 80 % is reported as a limitation of that universe.

**What this cannot claim, stated before the result.** A screen passes candidates; only EXP-028 can
confirm one. The universes and the $10,000 and $2 million floors were chosen by the planner; the
events come from one SEC data set.

## 6. Results

All MEASURED from the frozen scripts (Appendix R). Events built: 32,724 issuer-days with an insider
purchase of at least $10,000 (13,399 clusters, 10,111 with a CEO or CFO); priced and in a universe:
2,145 in U1, 14,708 in U2; after the 20-session de-duplication, the cells below. Net = gross minus
0.50 % (25 bps a side).

| Cell | Events | Gross 20-session excess | **Net** | Net 95 % interval | Net > 0 in years | Hit rate (net) | Screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1-U1 any purchase, S&P 500 | 1,499 | +0.04 % | **−0.46 %** | [−0.96, +0.06] | 1 of 5 | 45 % | FAIL |
| V2-U1 cluster, S&P 500 | 380 | +0.86 % | **+0.36 %** | [−0.57, +1.40] | 4 of 5 | 47 % | FAIL |
| V3-U1 CEO/CFO, S&P 500 | 307 | +0.25 % | **−0.25 %** | [−1.19, +0.67] | 1 of 5 | 50 % | FAIL |
| V1-U2 any purchase, liquid ≥ $5 | 8,978 | +0.32 % | **−0.18 %** | [−0.91, +0.49] | 1 of 5 | 47 % | FAIL |
| V2-U2 cluster, liquid ≥ $5 | 3,090 | +0.31 % | **−0.19 %** | [−1.27, +0.85] | 3 of 5 | 48 % | FAIL |
| V3-U2 CEO/CFO, liquid ≥ $5 | 2,916 | −0.02 % | **−0.52 %** | [−1.54, +0.47] | 1 of 5 | 47 % | FAIL |

**No cell passes the screen's bar (net ≥ +1.0 % and positive in ≥ 4 of 5 years).** The nearest, the
S&P 500 clusters, nets +0.36 % with an interval from −0.57 % to +1.40 %.

- **By year, net:** V2-U1 2017 +0.38, 2018 +0.04, 2019 −0.21, 2020 +1.19, 2021 +0.24; V2-U2 2017
  +0.77, 2018 −0.02, 2019 +0.33, 2020 −1.56, 2021 +0.22.
- **Other horizons, gross:** 5 sessions −0.08 % to +0.32 %; 60 sessions −0.20 % to +1.13 % (V3-U1
  +1.13 %, V2-U1 +1.05 %, the U2 cells −0.20 % to +0.15 %).
- **U2 at 50 bps a side:** −0.68 %, −0.69 %, −1.02 %.
- **Coverage:** 181 of 56,640 purchase lines had an unparseable symbol; Alpaca resolved 92–96 % of
  each quarter's symbols; 14 of 2,145 U1 events lack a 20-session exit (a line leaving the index).

## 7. Conclusions

1. **Insiders' open-market purchases did not predict the next month's return in 2017–2021, as a
   trader could have acted on them.** Bought at the open after the filing, the purchases earned
   +0.04 % to +0.86 % over the benchmark in 20 sessions before costs, and −0.52 % to +0.36 % after.
   The literature's cluster effect (about +3.8 % over 21 days, 1986–2016) is not there.
2. **Not in large caps, and not in smaller liquid stocks either.** U2 spans every issuer with at least
   $2 million a day of trading, where the literature locates the effect; it reads no better than U1.
3. **What this cannot claim.** Returns measured from the transaction date, or in microcaps below the
   $2 million floor, may differ; neither is tradable for this book. A different signal built on the
   same filings (sizes relative to holdings, repeated buyers) was not tested, and testing variants on
   these years after this result would spend them.
4. **The kill rule applies (the operator, 2026-10-24).** The search for a trading edge ends. The
   2022–2026 insider data was never downloaded; EXP-028 is not pre-registered.

## 8. Recommended code changes, and how to implement them

**None.** No signal to build. What the project does next is the operator's decision ([DL-317](../../design-log.md)
Amendment 3).

## Appendix P — Design (frozen)

| Cell | Signal | Universe | Benchmark |
| --- | --- | --- | --- |
| V1-U1 | any insider purchase ≥ $10,000 | S&P 500 member on the filing date | members, equal-weighted |
| V2-U1 | cluster: ≥ 2 insiders within 30 days | S&P 500 member | members, equal-weighted |
| V3-U1 | CEO or CFO purchase | S&P 500 member | members, equal-weighted |
| V1-U2 | any insider purchase ≥ $10,000 | close ≥ $5, 20-session median dollar volume ≥ $2 m | IWM |
| V2-U2 | cluster: ≥ 2 insiders within 30 days | as U2 | IWM |
| V3-U2 | CEO or CFO purchase | as U2 | IWM |

Statistic: mean over events of (20-session open-to-open return − benchmark's) − 0.50 %. A cell passes
at a net mean ≥ +1.0 % with the net mean > 0 in ≥ 4 of 2017–2021's five years; fewer than 100 events
is INSUFFICIENT. No pass in any cell: the search for a trading edge ends (the operator's kill rule).

## Appendix R — Run record

- 2026-10-24, planner. SEC Form 345 files 2016 Q4 → 2021 Q4 downloaded about 02:15 UTC (21 files,
  8–16 MB each; the operator's address in the User-Agent); 2022 onward not downloaded.
- Stage 1 `insider_events.py`: 173,625 purchase lines, 5,966 issuers. Stage 2 `insider_bars.py`:
  2,978,362 bar rows, 02:33–02:45 UTC. Both before the design commit `2ba192af` read only counts.
- Pilot (counts only, no return read): 32,724 events; U1 2,145 priced (14 without a 20-session exit),
  U2 14,708; clusters 621 and 5,862; CEO/CFO 367 and 4,044.
- Frozen SHA-256: `insider_events.py` `24ae98cb06c73db157d3ae2cb6efa3bd54eba34d5fcd0522fc135b9178fd260a`,
  `insider_bars.py` `2060c804dba91ef3bd485a73afcebedda3886c2a53e5e90a7940eb3a680adb79`,
  `insider_screen.py` `aba39ee1d8aa1ed7f5e816e72d5dd5428d620cebe41e368101aab8d15a702888`.
- Scored run 02:47:43–02:49:22 UTC; `screen.json` SHA-256
  `3ea08bf8538db0710bb5975eb867074759ae7d74361c81cf250f6a403ee3efb3`. Kit OneDrive
  `trading-agents-data/exp027-2026-10-24/`; SEC files in `trading-agents-data/insider-sec/`.

```text
python insider_events.py <OneDrive>/trading-agents-data/insider-sec <kit>/purchases.csv.gz
python insider_bars.py <kit>/purchases.csv.gz <repo>/.env <kit>/bars.csv.gz
python insider_screen.py <kit>/purchases.csv.gz <kit>/bars.csv.gz <OneDrive>/trading-agents-data <kit>/screen.json
```

## Appendix S — Scripts

### `insider_events.py`

```python
"""EXP-027 stage 1: every open-market insider purchase (Form 4, code P) filed 2016-10 → 2021-12.

Reads the SEC Form 345 data sets; writes one row per purchase line. No price is read.
Usage: python insider_events.py <sec_zip_dir> <out.csv.gz>
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pandas as pd


def read(z: zipfile.ZipFile, name: str, cols: list[str]) -> pd.DataFrame:
    with z.open(name) as f:
        return pd.read_csv(f, sep="\t", usecols=cols, dtype=str, quoting=3, on_bad_lines="skip")


def main() -> None:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    parts = []
    for path in sorted(src.glob("20*q*_form345.zip")):
        z = zipfile.ZipFile(path)
        sub = read(z, "SUBMISSION.tsv", ["ACCESSION_NUMBER", "FILING_DATE", "DOCUMENT_TYPE", "ISSUERCIK", "ISSUERNAME", "ISSUERTRADINGSYMBOL"])
        own = read(z, "REPORTINGOWNER.tsv", ["ACCESSION_NUMBER", "RPTOWNERCIK", "RPTOWNER_RELATIONSHIP", "RPTOWNER_TITLE"])
        tr = read(z, "NONDERIV_TRANS.tsv", ["ACCESSION_NUMBER", "TRANS_DATE", "TRANS_CODE", "TRANS_SHARES", "TRANS_PRICEPERSHARE", "TRANS_ACQUIRED_DISP_CD"])
        sub = sub[sub["DOCUMENT_TYPE"] == "4"]
        tr = tr[(tr["TRANS_CODE"] == "P") & (tr["TRANS_ACQUIRED_DISP_CD"] == "A")]
        own = own.drop_duplicates("ACCESSION_NUMBER")  # one reporting owner per filing (the first listed)
        df = tr.merge(sub, on="ACCESSION_NUMBER").merge(own, on="ACCESSION_NUMBER", how="left")
        df["shares"] = pd.to_numeric(df["TRANS_SHARES"], errors="coerce")
        df["price"] = pd.to_numeric(df["TRANS_PRICEPERSHARE"], errors="coerce")
        df["value"] = df["shares"] * df["price"]
        df["filing_date"] = pd.to_datetime(df["FILING_DATE"], format="%d-%b-%Y", errors="coerce")
        df["trans_date"] = pd.to_datetime(df["TRANS_DATE"], format="%d-%b-%Y", errors="coerce")
        df["quarter_file"] = path.name[:6]
        parts.append(df)
        print(path.name, len(df), flush=True)
    ev = pd.concat(parts, ignore_index=True)
    ev = ev.rename(columns={"ACCESSION_NUMBER": "accession", "ISSUERCIK": "issuer_cik", "ISSUERNAME": "issuer",
                            "ISSUERTRADINGSYMBOL": "symbol", "RPTOWNERCIK": "owner_cik",
                            "RPTOWNER_RELATIONSHIP": "relationship", "RPTOWNER_TITLE": "title"})
    ev["symbol"] = ev["symbol"].str.strip().str.upper()
    keep = ["accession", "filing_date", "trans_date", "issuer_cik", "issuer", "symbol", "owner_cik",
            "relationship", "title", "shares", "price", "value", "quarter_file"]
    ev = ev[keep].dropna(subset=["filing_date", "symbol"])
    ev = ev[(ev["filing_date"] >= "2016-10-01") & (ev["filing_date"] <= "2021-12-31")]
    ev.to_csv(out, index=False, compression="gzip")
    print("rows", len(ev), "issuers", ev["issuer_cik"].nunique(), "symbols", ev["symbol"].nunique())
    print(ev["relationship"].value_counts().head(12).to_string())


if __name__ == "__main__":
    main()
```

### `insider_bars.py`

```python
"""EXP-027 stage 2: Alpaca SIP daily bars (adjustment=all) for every officer/director purchase symbol.

Per filing quarter, symbols are resolved as of the quarter's end (`asof`), so renamed and delisted
names map to their entity. Writes bars only; no outcome is computed.
Usage: python insider_bars.py <purchases.csv.gz> <env_file> <out.csv.gz>
"""

from __future__ import annotations

import re
import sys
import time

import pandas as pd
import requests

URL = "https://data.alpaca.markets/v2/stocks/bars"


def clean(raw: str) -> str | None:
    s = re.sub(r"^(NYSE|NASDAQ|NYSEMKT|NYSEAMERICAN|AMEX|OTC|OB|OTCBB)\s*:\s*", "", str(raw).upper().strip())
    s = re.sub(r"[\[\]\(\)]", " ", s)
    s = re.sub(r"(:OTC|\bOB\b)", " ", s)
    tok = [t for t in re.split(r"[\s,;/]+", s) if t]
    if not tok:
        return None
    t = tok[0].replace("-", ".")
    return t if re.fullmatch(r"[A-Z]{1,5}(\.[A-Z])?", t) else None


def env(path: str) -> dict[str, str]:
    out = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def fetch(symbols, start, end, asof, headers):
    rows, token = [], None
    while True:
        params = {"symbols": ",".join(symbols), "timeframe": "1Day", "start": start, "end": end,
                  "adjustment": "all", "feed": "sip", "limit": 10000, "asof": asof}
        if token:
            params["page_token"] = token
        for attempt in range(5):
            r = requests.get(URL, headers=headers, params=params, timeout=60)
            if r.status_code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            break
        body = r.json()
        for sym, bars in (body.get("bars") or {}).items():
            rows += [(sym, b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]) for b in bars]
        token = body.get("next_page_token")
        time.sleep(0.32)
        if not token:
            return rows


def main() -> None:
    ev = pd.read_csv(sys.argv[1], parse_dates=["filing_date"])
    e = env(sys.argv[2])
    headers = {"APCA-API-KEY-ID": e["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": e["ALPACA_API_SECRET"]}
    ins = ev[ev["relationship"].fillna("").str.contains("Director|Officer") & (ev["value"] >= 10000)
             & (ev["filing_date"] >= "2017-01-01")].copy()
    ins["clean"] = ins["symbol"].map(clean)
    print("lines", len(ins), "unparsed symbols", int(ins["clean"].isna().sum()), flush=True)
    out = []
    for q, grp in ins.dropna(subset=["clean"]).groupby(ins["filing_date"].dt.to_period("Q")):
        syms = sorted(grp["clean"].unique())
        start = (q.start_time - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
        end = (q.end_time + pd.Timedelta(days=120)).strftime("%Y-%m-%d")
        asof = q.end_time.strftime("%Y-%m-%d")
        n0 = len(out)
        for i in range(0, len(syms), 100):
            out += [(str(q),) + row for row in fetch(syms[i : i + 100], start, end, asof, headers)]
        got = len({r[1] for r in out[n0:]})
        print(q, "symbols", len(syms), "with bars", got, "rows", len(out) - n0, flush=True)
    for bench in ("SPY", "IWM"):
        out += [("bench",) + row for row in fetch([bench], "2016-06-01", "2022-06-30", "2022-06-30", headers)]
    df = pd.DataFrame(out, columns=["quarter", "symbol", "date", "open", "high", "low", "close", "volume"])
    df.to_csv(sys.argv[3], index=False, compression="gzip")
    print("wrote", len(df))


if __name__ == "__main__":
    main()
```

### `insider_screen.py`

```python
"""EXP-027 stage 3: the insider-purchase screen, six cells, 2017–2021 (design fixed at `2ba192af`).

Usage: python insider_screen.py <purchases.csv.gz> <bars.csv.gz> <sp500_cache_dir> <out.json>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from insider_bars import clean  # noqa: E402

HORIZONS = (5, 20, 60)
COST = 0.0050  # 25 bps a side, round trip
COST_HIGH = 0.0100  # 50 bps a side, U2 reported
ADJ_ERRORS = {"TGNA": "2017-06-01", "RTX": "2020-04-03", "APTV": "2017-12-05"}
CEO_CFO = re.compile(r"\bCEO\b|CHIEF EXECUTIVE|\bCFO\b|CHIEF FINANCIAL", re.I)
B, SEED, BLOCK = 2000, 0, 20


def norm(t: str) -> str:
    return str(t).upper().replace("-", ".").replace("/", ".")


def build_events(purchases: Path) -> pd.DataFrame:
    ev = pd.read_csv(purchases, parse_dates=["filing_date"])
    ev = ev[ev["relationship"].fillna("").str.contains("Director|Officer") & (ev["value"] >= 10000)].copy()
    ev["sym"] = ev["symbol"].map(clean)
    ev = ev.dropna(subset=["sym"])
    ev["ceo_cfo"] = ev["title"].fillna("").str.contains(CEO_CFO)
    g = ev.groupby(["sym", "filing_date"]).agg(ceo_cfo=("ceo_cfo", "any"), value=("value", "sum"),
                                               quarter=("quarter_file", "first")).reset_index()
    owners = ev[["sym", "filing_date", "owner_cik"]].drop_duplicates()
    cluster = []
    by_sym = {s: d for s, d in owners.groupby("sym")}
    for row in g.itertuples():
        d = by_sym[row.sym]
        w = d[(d["filing_date"] <= row.filing_date) & (d["filing_date"] > row.filing_date - pd.Timedelta(days=30))]
        cluster.append(w["owner_cik"].nunique() >= 2)
    g["cluster"] = cluster
    g = g[(g["filing_date"] >= "2017-01-01") & (g["filing_date"] <= "2021-12-31")]
    g["quarter"] = g["filing_date"].dt.to_period("Q").astype(str)
    return g.reset_index(drop=True)


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


def summarise(df: pd.DataFrame, cal: pd.DatetimeIndex, draws, cost: float) -> dict:
    out = {"events": int(len(df))}
    if len(df) == 0:
        return out
    for h in HORIZONS:
        x = df[f"xs{h}"].dropna()
        e = df.loc[x.index, "entry"]
        net = x - cost
        res = {"n": int(len(x)), "gross_mean_pct": float(x.mean() * 100), "net_mean_pct": float(net.mean() * 100),
               "hit_rate_net": float((net > 0).mean())}
        if h == 20:
            pos = cal.get_indexer(e)
            n = len(cal)
            sums = np.bincount(pos, weights=net.to_numpy(), minlength=n)
            cnts = np.bincount(pos, minlength=n).astype(float)
            boot = sums[draws].sum(1) / np.maximum(cnts[draws].sum(1), 1)
            res["net_ci95_pct"] = [float(np.percentile(boot, 2.5) * 100), float(np.percentile(boot, 97.5) * 100)]
            yrs = net.groupby(e.dt.year).mean() * 100
            res["net_by_year_pct"] = {str(k): round(float(v), 3) for k, v in yrs.items()}
            res["years_positive"] = int((yrs > 0).sum())
            res["n_by_year"] = {str(k): int(v) for k, v in e.dt.year.value_counts().sort_index().items()}
        out[f"h{h}"] = res
    h20 = out["h20"]
    if h20["n"] < 100:
        out["screen"] = "INSUFFICIENT"
    else:
        out["screen"] = "PASS" if (h20["net_mean_pct"] >= 1.0 and h20["years_positive"] >= 4) else "FAIL"
    return out


def dedupe(df: pd.DataFrame, cal: pd.DatetimeIndex) -> pd.DataFrame:
    keep, last = [], {}
    for i, row in df.sort_values("entry").iterrows():
        p = cal.get_loc(row["entry"])
        if row["sym"] in last and p - last[row["sym"]] < 20:
            continue
        last[row["sym"]] = p
        keep.append(i)
    return df.loc[keep]


def u2(events: pd.DataFrame, bars: Path):
    b = pd.read_csv(bars, parse_dates=["date"])
    bench = b[b["quarter"] == "bench"]
    iwm = bench[bench["symbol"] == "IWM"].set_index("date")["open"]
    cal = pd.DatetimeIndex(bench[bench["symbol"] == "SPY"]["date"].sort_values().unique())
    per = {k: d.set_index("date").sort_index() for k, d in b[b["quarter"] != "bench"].groupby(["quarter", "symbol"])}
    rows = []
    for ev in events.itertuples():
        d = per.get((ev.quarter, ev.sym))
        if d is None:
            continue
        k = cal.searchsorted(ev.filing_date, side="right")
        if k >= len(cal) - max(HORIZONS) - 1:
            continue
        entry = cal[k]
        if entry not in d.index:
            continue
        prior = d.loc[d.index < entry].tail(20)
        if len(prior) < 10 or prior["close"].iloc[-1] < 5 or (prior["close"] * prior["volume"]).median() < 2e6:
            continue
        r = {"sym": ev.sym, "entry": entry, "cluster": ev.cluster, "ceo_cfo": ev.ceo_cfo}
        o0 = d.at[entry, "open"]
        for h in HORIZONS:
            ex = cal[k + h]
            if ex in d.index:
                px = d.at[ex, "open"]
            else:
                before = d.loc[d.index <= ex, "close"]
                px = before.iloc[-1] if len(before) else np.nan
            r[f"xs{h}"] = (px / o0 - 1) - (iwm.get(ex, np.nan) / iwm.get(entry, np.nan) - 1)
        rows.append(r)
    return pd.DataFrame(rows), cal


def u1(events: pd.DataFrame, cache: Path):
    bars = pd.read_csv(cache / "sp500_bars.csv.gz", usecols=["line", "date", "open"], parse_dates=["date"])
    O = bars.pivot(index="date", columns="line", values="open").sort_index()
    cal = O.index
    mem = pd.read_csv(cache / "sp500_membership.csv.gz", parse_dates=["first", "last"])
    mem["key"] = mem["ticker"].map(norm)
    Ov = O.to_numpy()
    lines = list(O.columns)
    brk = np.zeros(Ov.shape, bool)
    for line, day in ADJ_ERRORS.items():
        if line in lines and pd.Timestamp(day) in cal:
            brk[cal.get_loc(pd.Timestamp(day)), lines.index(line)] = True
    cb = np.cumsum(brk, 0)
    member = np.zeros(Ov.shape, bool)
    for r in mem.itertuples():
        if r.line in lines:
            member[(cal >= r.first) & (cal <= r.last), lines.index(r.line)] = True
    ew_cache: dict = {}

    def ew(k, h):
        if (k, h) not in ew_cache:
            ok = member[k] & ~np.isnan(Ov[k]) & ~np.isnan(Ov[k + h]) & ((cb[k + h] - cb[k]) == 0)
            ew_cache[(k, h)] = float(np.mean(Ov[k + h, ok] / Ov[k, ok] - 1))
        return ew_cache[(k, h)]

    rows = []
    for ev in events.itertuples():
        m = mem[(mem["key"] == norm(ev.sym)) & (mem["first"] <= ev.filing_date) & (mem["last"] >= ev.filing_date)]
        if m.empty or m.iloc[0]["line"] not in lines:
            continue
        j = lines.index(m.iloc[0]["line"])
        k = cal.searchsorted(ev.filing_date, side="right")
        if k >= len(cal) - max(HORIZONS) - 1 or np.isnan(Ov[k, j]):
            continue
        r = {"sym": ev.sym, "entry": cal[k], "cluster": ev.cluster, "ceo_cfo": ev.ceo_cfo}
        for h in HORIZONS:
            if np.isnan(Ov[k + h, j]) or cb[k + h, j] - cb[k, j] > 0:
                r[f"xs{h}"] = np.nan
            else:
                r[f"xs{h}"] = (Ov[k + h, j] / Ov[k, j] - 1) - ew(k, h)
        rows.append(r)
    return pd.DataFrame(rows), cal


def main() -> None:
    purchases, bars, cache, out = (Path(a) for a in sys.argv[1:5])
    events = build_events(purchases)
    result = {"events_built": {"all": int(len(events)), "cluster": int(events["cluster"].sum()),
                               "ceo_cfo": int(events["ceo_cfo"].sum())}}
    rng = np.random.default_rng(SEED)
    for uname, (df, cal) in (("U1", u1(events, cache)), ("U2", u2(events, bars))):
        cal = cal[(cal >= "2017-01-01") & (cal <= "2021-12-31")]
        draws = stationary(len(cal), rng)
        df = df[df["entry"] <= "2021-12-31"]
        result[f"{uname}_events_priced"] = int(len(df))
        for vname, mask in (("V1", np.ones(len(df), bool)), ("V2", df["cluster"].to_numpy(bool)),
                            ("V3", df["ceo_cfo"].to_numpy(bool))):
            cell = dedupe(df[mask], cal)
            res = summarise(cell, cal, draws, COST)
            if uname == "U2":
                res["h20_net_mean_at_50bps_pct"] = summarise(cell, cal, draws, COST_HIGH).get("h20", {}).get("net_mean_pct")
            result[f"{vname}-{uname}"] = res
            print(vname, uname, res.get("screen"), res.get("h20", {}).get("n"), res.get("h20", {}).get("net_mean_pct"), flush=True)
    out.write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
```
