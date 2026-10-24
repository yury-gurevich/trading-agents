# EXP-036 — Do S&P 500 firms that change their annual report's wording underperform those that do not ("Lazy Prices")?

**Status:** PRE-REGISTERED 2026-10-24 (planner, `62771916`) · **COMPLETE 2026-10-25: H0 on the primary (the
next month: +0.14 %, t 1.15), with a lead: in months 2–6 the changers lag the universe by 1.04 % (t −4.2,
post-hoc), the paper's slow drift. Not built; a confirmation needs data not yet seen.**
**Decision / origin:** [R011](../where-an-edge-can-exist/INDEX.md), [R012](../idea-testing-foundation/INDEX.md)
batch 4 · the operator, 2026-10-24, offered the last five queued ideas: *"only the annual-report wording
test."* · [DL-319](../../design-log.md) · **Cost:** $0 (SEC EDGAR, the operator's address in the
User-Agent by their word).

## 1. Why we needed this experiment

Cohen, Malloy and Nguyen (*Lazy Prices*, JF 2020; 1995–2014) found that firms whose 10-K or 10-Q language
changes most from the year before underperform those that change least, by up to 188 bps a month long-
short, and that the return arrives over months as the news the changes foreshadow comes out: investors
do not read the changes. It is the one queued idea whose mechanism the project's other tests have not
ruled out: EXP-028 and EXP-034 showed that headlines are priced within minutes, but a change buried in a
200-page filing is information of a slower kind. Every year scored here is after the paper's sample.

## 2. Hypothesis

**The signal.** For each firm's 10-K, the cosine similarity of its word-count vector with the firm's
previous 10-K (filed 9 to 15 months earlier). Low similarity = a "changer".

**The statistic.** Each month-end from 2017-01 to 2026-07, S&P 500 members with a 10-K filed in the last
12 months (by the month-end) are sorted into similarity quintiles; the next month's equal-weighted return
of the most similar quintile (Q5, "non-changers") minus the least similar (Q1). Monthly series;
Newey–West t (3 lags).

- **H1 — the effect holds:** the mean monthly Q5 − Q1 spread is above 0 with t above 1.96.
- **H0:** otherwise.

**Economic bar (for H1 only):** Q5 held long-only, rebalanced monthly, 25 bps a side on its turnover,
beats the equal-weighted universe: mean net monthly excess above 0 with t above 1.65.

**Why this bar.** One hypothesis, scored entirely after the paper's sample: no correction is needed, and
the paper's own sign is the prediction.

## 3. Data

- **Filings:** every 10-K (form `10-K`; amendments excluded) of firms that were S&P 500 members at any
  time 2016–2026, filed 2015-01-01 → 2026-09-25, from EDGAR (`data.sec.gov` submissions JSON, then
  each filing's primary document). The text is reduced to lowercase words; only the text is kept
  (outside the repo and OneDrive, `C:/Users/yury_/ta-local/exp036/`), with a manifest in the kit.
- **Tickers to CIKs:** the SEC's `company_tickers.json` (current tickers) and the Form 345 data sets
  2016 Q4 → 2021 Q4 (issuer symbol and CIK, for firms that have since left or been renamed).
- **Returns and membership:** the S235 cache (as EXP-030).

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; no repo code; no LLM; $0.

## 5. How it was conducted

1. Map each S&P 500 line's tickers to a CIK; fetch its 10-K list; download each primary document;
   strip tags, scripts and the inline-XBRL header; keep the words (`[a-z]+`).
2. Similarity: cosine of word-count vectors between a 10-K and the same CIK's previous 10-K filed 270 to
   450 days earlier.
3. Formation as section 2; the filing must be dated on or before the month-end; returns as EXP-030
   (month-end close to month-end close; a stock whose bars end exits at its last close).
4. **Pilot (before scoring):** coverage only: lines with a CIK, 10-Ks found and downloaded, similarities
   computed, members with a similarity each month.
5. **Reported, not barred:** the Q5 and Q1 legs against the universe; each year; the spread in the
   second to sixth month after formation (the paper's slow drift).

**What this cannot claim.** Large caps only, where the paper found the effect weaker; one similarity
measure of the paper's four; 10-Ks only, not 10-Qs.

## 6. Results

All MEASURED from the frozen scripts (Appendix R). **Coverage:** 7,335 10-Ks from 687 firms (0 failed),
6,626 year-over-year similarities from 685 firms; 115 formation months, 488 of 504 members a month with a
similarity on average. Raw word-count cosine is compressed (5th, 50th, 95th percentiles 0.9954, 0.9988,
0.9996); the quintiles use ranks.

**Primary: H0.** Next month, non-changers (Q5) minus changers (Q1): **+0.144 %** a month, Newey–West
t **1.15**. Q5 against the universe +0.056 %, Q1 −0.087 %. By year: 2017 +0.32 %, 2018 +0.03 %, 2019
+0.27 %, 2020 −0.41 %, 2021 +0.85 %, 2022 −0.11 %, 2023 +0.22 %, 2024 +0.25 %, 2025 +0.19 %, 2026 −0.38 %.
**Economic** (not required under H0): Q5 long-only, net of 25 bps a side, +0.019 % a month over the
universe (t 0.23).

**Reported, not barred — the slow drift (months 2–6 after formation, cumulative):** Q5 − Q1 **+1.39 %**
(t 2.63, Newey–West 6 lags on overlapping windows).

**Post-hoc, after the scored run (kit `posthoc_legs.txt`), each leg against the universe, months 2–6,
110 formations:** non-changers **+0.44 %** (t 1.06); changers **−1.04 %** (t **−4.22**); Q5 − Q1 +1.47 %
(t 2.84), +1.78 % and +1.17 % in the two halves; non-changers +0.44 % in each half.

## 7. Conclusions

1. **The registered test fails.** In the month after formation the effect is the paper's sign and a
   third of its size, and t 1.15 does not clear the bar. H0.
2. **The paper's slow drift is there, on the changers' side.** Firms whose 10-K changed most lag the
   S&P 500's equal-weighted mean by about 1 % over months 2–6 (t −4.2), in both halves of the decade.
   It is the first effect in this day's 130-plus tests that has a mechanism, holds in both halves and
   is not a calendar artefact. But it was read after the scored run, so it is a lead, not a finding.
3. **For a long-only fleet it is an avoid rule, and a small one.** Leaving out the fifth of the index
   whose 10-K changed most would have lifted the remaining book by roughly a quarter of a point over
   five months *[estimate: 1.04 % × 0.2 ÷ 0.8]*, about half a point a year, before costs and before
   confirmation. Shorting the changers is outside the fleet (DL-240).
4. **A confirmation needs data the lead has not seen:** the same rule, months 2–6 as the primary, on
   S&P MidCap 400 and SmallCap 600 members (the paper found the effect larger in smaller firms), or on
   10-Qs, or on the 10-Ks filed from 2026-10 onward.

## 8. Recommended code changes, and how to implement them

**None now.** If the operator wants the lead pursued: a pre-registered confirmation on the S&P 400 and
600 (point-in-time membership as R008 built for the S&P 500, Alpaca bars, about 11,000 more 10-Ks), with
"changers lag the universe in months 2–6" as the single primary. Only a confirmed effect would become an
avoid filter in the scanner (a Codex sprint, full cycle).

## Appendix P — Pre-registration (frozen)

- Signal: cosine similarity of word counts (`[a-z]+`, lowercased, tags and inline-XBRL header removed)
  between a 10-K and the same firm's previous 10-K filed 270–450 days earlier.
- Formation: month-ends 2017-01 → 2026-07; S&P 500 members with a 10-K filed within the last 12 months on
  or before the month-end; quintiles; next month's equal-weighted return.
- **H1:** mean monthly Q5 − Q1 > 0 with Newey–West (3 lags) t > 1.96. Else H0.
- Economic (only under H1): Q5 long-only, 25 bps a side on turnover, mean net excess over the
  equal-weighted universe > 0 with t > 1.65.

## Appendix R — Run record

- 2026-10-24/25, planner. Downloader tested on 3 firms (35 filings), then run in full (about 20:10 →
  22:50 AEDT): 7,335 10-Ks, 687 CIKs, 0 failed; text 681 MB kept outside the repo and OneDrive. 721 S&P
  500 lines, 700 mapped to a CIK (690 distinct).
- Coverage pilot (no return): 6,626 similarities, 485–490 members a month with one.
- Frozen SHA-256: `exp036_fetch.py` `8f0345172f3f39970a0a258f76f20c861861fa299887dc4d6779b608ff1e19fb`,
  `exp036_score.py` `0d50127a00ea32924f33a2a9bb77831fc354338dce75015d47e0d0de957d87a3`, `manifest.csv`
  `fbf26f7aec2cc698f430057c8613897c4cf00a0f997997b0d967f13685a2693c`, `line_cik.csv`
  `0d0a3d1d6f3692a6cbf9a041df09fb259327429277caa9f15d7390d1b80d2d76`; scored once; `exp036.json`
  `b5ddd4cf553ab1306bccec5946084c5935989ea8dcce5d3b685385647a1e510d`. The post-hoc leg split
  (`posthoc_legs.txt`) was computed after it with the frozen functions. Kit OneDrive
  `trading-agents-data/exp036-2026-10-24/`.

```text
python exp036_fetch.py <OneDrive>/trading-agents-data <...>/insider-sec <local>/text <kit>/manifest.csv
python exp036_score.py <local>/text <kit>/manifest.csv <kit>/line_cik.csv <OneDrive>/trading-agents-data <kit>/exp036.json
```

## Appendix S — Scripts

### `exp036_fetch.py`

```python
"""EXP-036 stage 1: the 10-Ks of every S&P 500 line 2016-2026, as word text. No price is read.

Usage: python exp036_fetch.py <sp500_cache_dir> <insider_sec_dir> <text_out_dir> <manifest.csv> [--limit N]
"""

from __future__ import annotations

import gzip
import html
import json
import re
import sys
import time
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd

UA = {"User-Agent": "trading-agents research ygurevic@gmail.com"}
START, END = "2015-01-01", "2026-09-25"


def get(url: str, tries: int = 5) -> bytes:
    for k in range(tries):
        try:
            time.sleep(0.16)
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and k < tries - 1:
                time.sleep(10 * (k + 1))
                continue
            raise
        except Exception:
            if k < tries - 1:
                time.sleep(5 * (k + 1))
                continue
            raise
    raise RuntimeError(url)


def key(t: str) -> str:
    return re.sub(r"[^A-Z]", "", str(t).upper())


def words(raw: bytes) -> str:
    t = raw.decode("utf-8", errors="replace")
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?is)<ix:header>.*?</ix:header>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return " ".join(re.findall(r"[a-z]+", t.lower()))


def main() -> None:
    cache, sec_dir, out, manifest = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    out.mkdir(parents=True, exist_ok=True)
    bars = pd.read_csv(cache / "sp500_bars.csv.gz", usecols=["line", "symbol"]).drop_duplicates()
    mem = pd.read_csv(cache / "sp500_membership.csv.gz")
    tick = {}
    for line, sym in list(zip(bars["line"], bars["symbol"])) + list(zip(mem["line"], mem["ticker"])):
        tick.setdefault(line, set()).add(key(sym))
    cur = json.loads(get("https://www.sec.gov/files/company_tickers.json"))
    by_ticker = {key(v["ticker"]): int(v["cik_str"]) for v in cur.values()}
    hist = {}
    for z in sorted(sec_dir.glob("20*q*_form345.zip")):
        with zipfile.ZipFile(z).open("SUBMISSION.tsv") as f:
            sub = pd.read_csv(f, sep="\t", usecols=["ISSUERCIK", "ISSUERTRADINGSYMBOL"], dtype=str, quoting=3)
        for c, s in zip(sub["ISSUERCIK"], sub["ISSUERTRADINGSYMBOL"]):
            if isinstance(s, str) and isinstance(c, str):
                hist.setdefault(key(s.split(",")[0].split("/")[0]), Counter())[int(c)] += 1
    line_cik = {}
    for line, ks in tick.items():
        cands = Counter()
        for k in ks:
            if k in hist:
                cands.update(hist[k])
        if not cands:
            for k in ks:
                if k in by_ticker:
                    cands[by_ticker[k]] += 1
        if cands:
            line_cik[line] = cands.most_common(1)[0][0]
    print("lines", len(tick), "with a CIK", len(line_cik), "unique CIKs", len(set(line_cik.values())), flush=True)
    pd.Series(line_cik, name="cik").rename_axis("line").to_csv(out.parent / "line_cik.csv")
    rows = []
    done = set(p.name for p in out.glob("*.txt.gz"))
    ciks = sorted(set(line_cik.values()))[:limit] if limit else sorted(set(line_cik.values()))
    for n, cik in enumerate(ciks, 1):
        s = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
        tables = [s["filings"]["recent"]]
        for extra in s["filings"].get("files", []):
            if extra.get("filingTo", "9999") >= START:
                tables.append(json.loads(get("https://data.sec.gov/submissions/" + extra["name"])))
        for t in tables:
            for form, fd, acc, doc in zip(t["form"], t["filingDate"], t["accessionNumber"], t["primaryDocument"]):
                if form != "10-K" or not (START <= fd <= END) or not doc:
                    continue
                name = f"{cik}_{acc}.txt.gz"
                if name not in done:
                    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{doc}"
                    try:
                        raw = get(url)
                    except Exception as e:  # noqa: BLE001
                        rows.append((cik, fd, acc, doc, -1, str(e)[:80]))
                        continue
                    text = words(raw)
                    with gzip.open(out / name, "wt", encoding="utf-8") as f:
                        f.write(text)
                    rows.append((cik, fd, acc, doc, len(text.split()), ""))
                else:
                    rows.append((cik, fd, acc, doc, None, "cached"))
        if n % 25 == 0:
            print(time.strftime("%H:%M:%S"), "ciks", n, "of", len(ciks), "filings", len(rows), flush=True)
            pd.DataFrame(rows, columns=["cik", "filing_date", "accession", "doc", "words", "note"]).to_csv(manifest, index=False)
    pd.DataFrame(rows, columns=["cik", "filing_date", "accession", "doc", "words", "note"]).to_csv(manifest, index=False)
    print("done: filings", len(rows), flush=True)


if __name__ == "__main__":
    main()
```

### `exp036_score.py`

```python
"""EXP-036 stage 2: 10-K similarity year over year, monthly quintiles of S&P 500 members, Q5 - Q1.

Usage: python exp036_score.py <text_dir> <manifest.csv> <line_cik.csv> <sp500_cache_dir> <out.json> [--pilot]
"""

from __future__ import annotations

import gzip
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ADJ = {"TGNA": "2017-06-01", "RTX": "2020-04-03", "APTV": "2017-12-05"}
FIRST, LAST = "2017-01-01", "2026-07-31"
COST = 0.0025


def nw_t(x: np.ndarray, lags: int = 3) -> float:
    x = x[~np.isnan(x)]
    n = len(x)
    e = x - x.mean()
    s = (e @ e) / n
    for l in range(1, lags + 1):
        s += 2 * (1 - l / (lags + 1)) * (e[l:] @ e[:-l]) / n
    return float(x.mean() / math.sqrt(s / n))


def cosine(a: Counter, b: Counter) -> float:
    common = set(a) & set(b)
    num = sum(a[w] * b[w] for w in common)
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return num / den if den else float("nan")


def similarities(text_dir: Path, manifest: Path) -> pd.DataFrame:
    m = pd.read_csv(manifest, parse_dates=["filing_date"]).drop_duplicates("accession")
    m = m[(m["words"].fillna(1) != -1)]
    out = []
    for cik, g in m.sort_values("filing_date").groupby("cik"):
        prev = None
        for r in g.itertuples():
            p = text_dir / f"{cik}_{r.accession}.txt.gz"
            if not p.exists():
                continue
            with gzip.open(p, "rt", encoding="utf-8") as f:
                c = Counter(f.read().split())
            if len(c) < 500:
                continue
            if prev is not None and 270 <= (r.filing_date - prev[0]).days <= 450:
                out.append((cik, r.filing_date, cosine(c, prev[1])))
            prev = (r.filing_date, c)
    return pd.DataFrame(out, columns=["cik", "filing_date", "sim"])


def main() -> None:
    text_dir, manifest, line_cik_p, cache, out = (Path(a) for a in sys.argv[1:6])
    pilot = "--pilot" in sys.argv
    sims = similarities(text_dir, manifest)
    line_cik = pd.read_csv(line_cik_p).set_index("line")["cik"]
    bars = pd.read_csv(cache / "sp500_bars.csv.gz", usecols=["line", "date", "close"], parse_dates=["date"])
    C = bars.pivot(index="date", columns="line", values="close").sort_index()
    cal, lines = C.index, list(C.columns)
    Cv = C.to_numpy()
    brk = np.zeros_like(Cv, bool)
    for l, d in ADJ.items():
        if l in lines and pd.Timestamp(d) in cal:
            brk[cal.get_loc(pd.Timestamp(d)), lines.index(l)] = True
    cb = np.cumsum(brk, 0)
    member = np.zeros_like(Cv, bool)
    for r in pd.read_csv(cache / "sp500_membership.csv.gz", parse_dates=["first", "last"]).itertuples():
        if r.line in lines:
            member[(cal >= r.first) & (cal <= r.last), lines.index(r.line)] = True
    month = cal.to_period("M")
    me = [i for i in range(len(cal) - 1) if month[i] != month[i + 1]]
    by_cik = {c: g.sort_values("filing_date") for c, g in sims.groupby("cik")}
    rows = []
    for k, (a, b) in enumerate(zip(me[:-1], me[1:])):
        f = cal[a]
        if f < pd.Timestamp(FIRST) or f > pd.Timestamp(LAST):
            continue
        sig = np.full(len(lines), np.nan)
        for j, line in enumerate(lines):
            if not member[a, j] or np.isnan(Cv[a, j]) or line not in line_cik.index:
                continue
            g = by_cik.get(int(line_cik[line]))
            if g is None:
                continue
            g = g[(g["filing_date"] <= f) & (g["filing_date"] > f - pd.Timedelta(days=365))]
            if len(g):
                sig[j] = g["sim"].iloc[-1]

        def hold(i0, i1):
            last = pd.DataFrame(Cv[i0 + 1 : i1 + 1]).ffill().to_numpy()[-1]
            r = last / Cv[i0] - 1
            r[(cb[i1] - cb[i0]) > 0] = np.nan
            return r

        ret = hold(a, b)
        later = hold(b, me[k + 6]) if k + 6 < len(me) else np.full(len(lines), np.nan)
        uni = member[a] & ~np.isnan(Cv[a]) & ~np.isnan(ret)
        ok = uni & ~np.isnan(sig)
        row = {"f": str(f.date()), "universe": int(uni.sum()), "with_sim": int(ok.sum())}
        if ok.sum() >= 100 and not pilot:
            q = np.nanquantile(sig[ok], [0.2, 0.8])
            q1, q5 = ok & (sig <= q[0]), ok & (sig >= q[1])
            um = np.nanmean(ret[uni])
            row.update({"spread": float(np.nanmean(ret[q5]) - np.nanmean(ret[q1])), "q5_x": float(np.nanmean(ret[q5]) - um),
                        "q1_x": float(np.nanmean(ret[q1]) - um), "q5": [lines[j] for j in np.nonzero(q5)[0]],
                        "later_spread": float(np.nanmean(later[q5]) - np.nanmean(later[q1])) if np.isfinite(later[q5]).any() else np.nan})
        rows.append(row)
    res = {"filings_with_similarity": int(len(sims)), "ciks_with_similarity": int(sims["cik"].nunique()),
           "sim_quantiles": [float(x) for x in np.nanquantile(sims["sim"], [0.05, 0.25, 0.5, 0.75, 0.95])] if len(sims) else [],
           "months": len(rows), "mean_universe": float(np.mean([r["universe"] for r in rows])),
           "mean_with_sim": float(np.mean([r["with_sim"] for r in rows]))}
    if pilot:
        print(json.dumps(res, indent=1))
        return
    sp = np.array([r.get("spread", np.nan) for r in rows])
    res.update({"spread_mean_pct": float(np.nanmean(sp) * 100), "spread_t": nw_t(sp),
                "q5_excess_pct": float(np.nanmean([r.get("q5_x", np.nan) for r in rows]) * 100),
                "q1_excess_pct": float(np.nanmean([r.get("q1_x", np.nan) for r in rows]) * 100),
                "later_months_2_to_6_spread_pct": float(np.nanmean([r.get("later_spread", np.nan) for r in rows]) * 100),
                "later_t": nw_t(np.array([r.get("later_spread", np.nan) for r in rows]), 6)})
    res["verdict"] = "H1" if (res["spread_mean_pct"] > 0 and res["spread_t"] > 1.96) else "H0"
    prev, nets = None, []
    for r in rows:
        if "q5" not in r:
            continue
        cur = set(r["q5"])
        turn = 1.0 if prev is None else len(cur ^ prev) / max(len(cur) + len(prev), 1)
        nets.append(r["q5_x"] - 2 * COST * turn)
        prev = cur
    nets = np.array(nets)
    res["economic_q5_net_pct"] = float(nets.mean() * 100)
    res["economic_t"] = nw_t(nets)
    if res["verdict"] == "H1" and res["economic_q5_net_pct"] > 0 and res["economic_t"] > 1.65:
        res["verdict"] = "H1 AND ECONOMIC"
    years = {}
    for r in rows:
        if "spread" in r:
            years.setdefault(r["f"][:4], []).append(r["spread"])
    res["by_year_spread_pct"] = {y: float(np.mean(v) * 100) for y, v in years.items()}
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
```
