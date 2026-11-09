# EXP-038 — Do the 212 published stock-return predictors still earn after publication, outside micro caps?

**Status:** PRE-REGISTERED 2026-11-09 (planner, `451280f8`) · **COMPLETE 2026-11-09: NONE. No published predictor confirms after publication outside micro caps: 25 of 194 pass discovery, 0 confirm on 2016–2025. The median long-short falls from +0.40 % a month in the papers' own samples to +0.17 % after publication and +0.14 % in 2016–2025; the operator's turnover strategy (`ShareVol`) earned −0.05 % a month after publication. Nothing is built.**
**Decision / origin:** the operator, 2026-11-09, after browsing QuantConnect's strategy library (more
than 400 strategies with code, a small-cap turnover long-short among them): *"Would something like this
… be beneficial for us? Maybe inspire us to test them?"*, then *"fix first, then the rest"* ·
[R011](../where-an-edge-can-exist/INDEX.md) named this screen on 2026-10-24 and it was never run ·
[R012](../idea-testing-foundation/INDEX.md) funnel ([DL-319](../../design-log.md)) · [DL-321](../../design-log.md) ·
**Cost:** $0 (free data, a laptop script).

## 1. Why we needed this experiment

Most of QuantConnect's library is published academic predictors written as code. Testing them one at a
time would take weeks and would mostly re-measure a known result: Chen and Welch (2026, R011) found that
about 200 published long-short portfolios earn a median 7 bp a month outside micro caps after 2005, and
McLean and Pontiff found returns fall by about 58 % after publication. This project's own tests agree:
none of 17 stock-level signals sorted the S&P 500 (EXP-030), and none of nine published allocation
strategies beat its benchmark after publication (EXP-026).

Chen and Zimmermann's Open Source Asset Pricing (OSAP) replicates 212 published predictors as monthly
portfolio returns through December 2025, in several implementations, each with its paper's publication
year. One pass over that data answers for the whole set at once: does any published cross-sectional
predictor still earn after publication in stocks the fleet could trade, so that a replay on the fleet's
own data is worth pre-registering? If none does, QuantConnect's ports of these predictors need not be
tested one by one. The operator's example, the small-cap turnover effect, is OSAP's `ShareVol` (Datar,
Naik and Radcliffe, 1998); `DolVol`, `VolMkt` and `std_turn` are its neighbours.

## 2. Hypothesis

**Unit.** Each predictor's monthly long-short return, OSAP's `LS` (long the top decile, short the bottom,
signed so that the top decile is the one the paper predicts will earn more), in the ex-micro
implementation (only stocks above the NYSE 20th percentile of market equity: OSAP
`LiqScreen_ME_gt_NYSE20pct`), in percent a month.

**H1, per predictor:** the mean `LS` return after publication is above zero.

1. **Discovery.** Each predictor's months from the January after its publication year through
   2015-12. Eligible with at least 24 months (198 of 212). One-sided Newey–West t (Bartlett, 12 lags),
   p from Student's t with n − 1 degrees of freedom; **Benjamini–Hochberg at q = 10 %** across the
   eligible predictors.
2. **Confirmation.** 2016-01 → 2025-12 (120 months, which the discovery step never reads), the same
   test on the discovery passers, **Holm at 5 %** across them.
3. **Economic bar, confirmed predictors only.** The long leg alone (the top decile held long-only, as the
   fleet trades) minus the market (Ken French Mkt-RF + RF), 2016-01 → 2025-12: mean at least **+0.25 % a
   month** (3 % a year, enough to rebalance a decile monthly at about 25 bps a side with up to half of it
   turning over) **and** one-sided Newey–West t at least **1.645**. OSAP reports no turnover, so this
   bar is a gate to a replay, not a verdict on a trade.

**H0:** no predictor confirms.

**Verdicts, by code:**

- **EDGE CANDIDATE:** confirmed and over the economic bar. The next step is a separate pre-registered
  replay on the fleet's S&P 500 cache with real costs, on the operator's word.
- **CONFIRMED, NOT ECONOMIC:** the long-short survives but the long leg does not clear the bar. No use to
  a long-only fleet.
- **NONE:** nothing confirms. Published cross-sectional predictors give this project no edge outside
  micro caps after publication.

**Why this bar:** R012's funnel (DL-319 D2). Of 198 predictors with no effect, about ten pass a 5 % test
by luck; the false-discovery rate and an untouched confirmation period keep that out.

**Reported, not barred:**

- The medians across predictors of the mean `LS` in each paper's own sample, after publication, and over
  2016–2025: the decay on this data.
- The rows of `ShareVol`, `DolVol`, `VolMkt` and `std_turn`, whatever they show.
- The same screen on three other implementations: each paper's original method (micro caps included),
  value weights forced, and value-weighted deciles (179 predictors).
- The 14 predictors published 2014–2016 with fewer than 24 discovery months: their 2016–2025 figures only.

## 3. Data

| File (OSAP release 2026.10 unless noted) | What | sha256 prefix |
| --- | --- | --- |
| `AltPorts_LiqScreen_ME_gt_NYSE20pct.parquet` | **primary**: 212 predictors, deciles + `LS`, ex-micro, 1926-01 → 2025-12, 1,238,068 rows | `fcd2ae40` |
| `PredictorPortsFull_OP.parquet` | each paper's own method, 212 predictors | `76599d94` |
| `AltPorts_LiqScreen_VWforce.parquet` | value weights forced, 212 predictors | `e64df0fc` |
| `AltPorts_DecilesVW.parquet` | value-weighted deciles, 179 predictors | `95409cb1` |
| `SignalDoc.csv` | 331 rows, 212 `Predictor`: acronym, authors, publication year (1973–2016, median 2006), sign, sample years | `0ceb1102` |
| `F-F_Research_Data_Factors.csv` (Ken French, CRSP 202609) | monthly Mkt-RF and RF, 1926-07 → 2026-09 | `a3894d74` |

**Source.** Hugging Face `OpenSourceAP/CrossSection`, branch `Data-Release-2026.10` (built from CRSP v2
and Compustat; CRSP keeps delisted firms), and the Ken French data library; downloaded 2026-11-09
19:58–20:02 AEDT into OneDrive `trading-agents-data/exp038-2026-11-09/inputs/`. Not committed: the
portfolios derive from licensed data.

**Known defects** (OSAP release notes): seven option-based predictors end in 2022-12, three governance
predictors in 2007, `PatentsRD` in 2006, `ProbInformedTrading` in 2012. Each is tested on the months it
has, n is reported, and an empty confirmation window counts as not confirmed. 26 predictors were revised
materially against the 2025.10 release (listed in the release notes).

**Read before this pre-registration:** the release notes, `SignalDoc.csv`'s metadata (the papers' own
reported returns were not printed), the files' columns, dates and counts, and the pilot (section 5). No
return after any publication date was computed.

## 4. Tools and setup

Laptop (Intel i7-7660U, 2 cores / 4 threads, Windows 10 Pro 10.0.19045). Python 3.12.2 in an isolated
`uv run --no-project` environment: pandas 3.1.1, numpy 2.5.4, scipy 1.18.1, pyarrow 26.0.1. Script
`exp038_screen.py` (Appendix P digest), kept in the kit folder. No random draws, so no seed. No paid
service. The repo commit is this pre-registration's.

## 5. How it was conducted

1. **Download** (done, section 3).
2. **Pilot** (done 2026-11-09, `pilot.json` in the kit), mechanical only, on data no test reads: all 212
   predictors present in the primary file; for every one, `LS` equals the top decile minus the bottom
   decile month by month (worst miss 5.0e-13), so the long leg is always decile 10; returns are in
   percent (median absolute decile return before 1974: 3.38); the market series covers all 120
   confirmation months; in each paper's own sample years, 205 of 209 predictors point the way the paper
   said (three have no ex-micro data in their sample years).
3. **Freeze.** The script's digest and the parameters are in Appendix P; this commit is the
   pre-registration.
4. **Score once:** from the kit folder,
   `uv run --no-project --with pandas==3.1.1 --with pyarrow==26.0.1 --with scipy==1.18.1 --with numpy==2.5.4 python -I exp038_screen.py score .`
   writes `exp038.json` and prints the summary. Sections 6–8 and Appendix R follow from that output.
5. **Failures.** A crash before output is fixed, recorded in Appendix R and re-run. Changing any number in
   section 2 makes a new experiment.

## 6. Results

**The bar (MEASURED, primary: ex-micro, `LS`, percent a month):**

| Step | Count |
| --- | --- |
| Eligible for discovery (at least 24 post-publication months with data through 2015) | 194 of 212 |
| Passed discovery, Benjamini–Hochberg q = 10 % | 25 |
| Confirmed on 2016-01 → 2025-12, Holm 5 % | **0** |
| Over the economic bar | not reached |

The smallest confirmation p values were `Mom6m` 0.0143 (+0.95 % a month, t 2.21), `IO_ShortInterest` 0.0200 (+3.61 %,
t 2.08) and `SmileSlope` 0.0247 (+0.55 %, t 1.99); Holm needed 0.002 for the first. Of the 25 passers, 24 earn less in
2016–2025 than in discovery (all but `IO_ShortInterest`) and 4 are below zero.

**The decay (MEASURED, medians across predictors, before costs):**

| Window | Median `LS`, % a month |
| --- | --- |
| Each paper's own sample years | +0.40 |
| After publication, through 2025 | +0.17 |
| 2016–2025 | +0.14 (69 % of predictors above zero) |

181 of 209 predictors with both figures earn less after publication than in their paper's sample: a 59 % fall in the
median, close to McLean and Pontiff's 58 %.

**The operator's turnover question (MEASURED, reported by name):**

| Predictor | Published | Own sample | After publication | Discovery | 2016–2025 |
| --- | --- | --- | --- | --- | --- |
| `ShareVol` (Datar, Naik, Radcliffe: share volume) | 1998 | +0.49 | **−0.05** | −0.06 (t −0.24) | −0.02 (t −0.07) |
| `DolVol` (Brennan, Chordia, Subrahmanyam: dollar volume) | 1998 | +0.26 | +0.04 | +0.22 (t 0.90) | −0.28 (t −1.99) |
| `VolMkt` (Haugen, Baker: volume to market equity) | 1996 | +0.33 | +0.13 | +0.25 (t 0.54) | −0.11 (t −0.29) |
| `std_turn` (Chordia, Subrahmanyam, Anshuman: turnover volatility) | 2001 | +1.16 | +0.48 | +0.46 (t 1.06) | +0.49 (t 1.02) |

None passes discovery; the turnover effect has not paid outside micro caps since it was published.

**Other implementations (MEASURED, reported, not barred):**

| Implementation | Passed discovery | Confirmed | Median own sample / after publication / 2016–2025 |
| --- | --- | --- | --- |
| Each paper's own method (micro caps included) | 57 | 0 | +0.60 / +0.23 / +0.18 |
| Value weights forced | 4 | 0 | +0.36 / +0.10 / +0.05 |
| Value-weighted deciles (179 predictors) | 5 | 1: `AnnouncementReturn` | +0.43 / +0.12 / +0.09 |

`AnnouncementReturn` (Chan, Jegadeesh and Lakonishok, 1996: the stock's return around its last earnings announcement)
earns +0.75 % a month in value-weighted deciles over 2016–2025 (t 2.49, Holm p 0.007 against 0.010), but only +0.15 %
(t 1.36) in the primary. A secondary result, so a lead, not a finding.

**The 18 not eligible (MEASURED, 2016–2025 only):** 14 published 2014–2016 and four with gaps in their data (`Activism1`
and `Activism2` end in 2007; `PatentsRD` has 13 discovery months and `RDcap` none). The largest t among them: `dVolCall`
+0.67 % (t 2.74, 85 months), `OperProfRD` +0.75 % (t 2.21), `BetaTailRisk` +0.64 % (t 1.93), `CBOperProf` +0.51 %
(t 1.79). Across all 212, the largest 2016–2025 t is `Coskewness`'s 3.59; it failed discovery, so the funnel does not count
it, and picking the best of 212 after the fact is the search the funnel exists to stop.

## 7. Conclusions

- **For the decision in section 1: no published cross-sectional predictor earns this project an edge.** Outside micro
  caps, after publication, none confirms on the ten most recent years, and even the original methods with micro caps
  confirm none. The typical predictor's 2016–2025 long-short, +0.14 % a month (about 1.7 % a year) before costs and with
  a short side the fleet cannot hold, leaves a long-only fleet nothing after costs.
- **QuantConnect's ports of these predictors need not be tested one by one.** What this record covers is the library's
  academic stock-selection strategies; its futures, currency, crypto and options strategies are outside it, and EXP-026
  already covered the allocation strategies the fleet could hold.
- **The turnover strategy the operator found is a 1998 result that stopped paying when it was published.**
- **What it does not say:** OSAP is a replication of each paper's method, not QuantConnect's code; micro caps
  (excluded here) are where most predictors still earn, but they are untradeable at the fleet's costs and outside its
  universe. `AnnouncementReturn` in value-weighted deciles is a lead, confirmed only on a secondary implementation.
- **The 3-month figures in strategy libraries:** a Sharpe ratio over one quarter carries an uncertainty of about ±2;
  this record's own 2016–2025 table shows how a ten-year window shrinks such numbers.

## 8. Recommended code changes, and how to implement them

**None.** No predictor reaches the economic bar, so no replay is pre-registered and nothing enters the fleet. The
`AnnouncementReturn` lead would need its own pre-registration on data this record never read (the fleet's own earnings
dates from 2026 onwards); it is not proposed unless the operator asks.

## Appendix P — Pre-registration (frozen)

Committed before the first scored run.

- Script `exp038_screen.py` sha256 `2e30e4e5527ffb7e65852ad8d17646bc1586062674723307521b03fb40fe2855`.
- Inputs sha256: primary `fcd2ae4053d7262868f5531be051ab6039161f7422091651116cf4a6990f3734`; OP
  `76599d94beab94cc8973d8a126e8efbed98ee79f677738c55b2389f17387ba96`; VW forced
  `e64df0fc189f1a4f4ce3ba39fdbba2ee83dfce871c6bf60f5660cbc9222158db`; deciles VW
  `95409cb1014d6b20d5ddf0468e98baeb8fec68ef514bef0e777565eb884679a8`; SignalDoc
  `0ceb11020c2138c2477b732948beaac2e67ccaad8428753e3a79af2bb5ea0178`; Ken French
  `a3894d74d553cab812eabbe706bdbf443c97eb20b24b05e3e5f3ce47e46b90bb`.
- Unit: OSAP `LS`, ex-micro (`LiqScreen_ME_gt_NYSE20pct`), percent a month.
- Discovery: January after the publication year → 2015-12; at least 24 months; one-sided Newey–West t,
  12 lags, Student's t with n − 1 df; Benjamini–Hochberg q = 0.10.
- Confirmation: 2016-01 → 2025-12; same test on the discovery passers; Holm, alpha 0.05.
- Economic bar: decile 10 minus (Mkt-RF + RF), 2016-01 → 2025-12; mean ≥ 0.25 % a month and t ≥ 1.645.
- Verdicts: EDGE CANDIDATE / CONFIRMED, NOT ECONOMIC / NONE, as in section 2.

## Appendix R — Run record

- Scored once, 2026-11-09 09:25:36 → 09:26:03 UTC, from the kit folder, with the Appendix P script (digest re-checked
  before the run: `2e30e4e5…`) and the pinned environment of section 4. Output `exp038.json` sha256
  `42321087b07c563a216aae5c3da09c0ea82e278908aed00ec28b72e8dd241da5`; console output in `run.log`; both in OneDrive
  `trading-agents-data/exp038-2026-11-09/`.
- **One count corrected after the run, not the rule:** section 2 said 198 predictors would be eligible, counted from
  publication years alone. The frozen rule counts months with data: 18 fall short (14 by publication year, four by
  gaps), so 194 were eligible. The Benjamini–Hochberg denominator is 194.
- No defect found; no re-run.

## Appendix S — Scripts

`exp038_screen.py`, verbatim (sha256 `2e30e4e5…`, line endings as committed here: LF). Run as in section 5, step 4.

```python
"""EXP-038: do the 212 published stock-return predictors still earn after publication outside micro caps?

Planner kit script, read-only, $0. Inputs (OSAP release 2026.10 + Ken French monthly factors) in
<kit>/inputs. Two modes:

  pilot  mechanical checks only: every predictor present, the long leg found by the identity
         LS = ret[long] - ret[short] month by month, units, and each predictor's direction in its
         ORIGINAL paper's sample years (never a tested window: every tested month is after publication).
  score  the pre-registered run (EXP-038 section 5): discovery = post-publication months through
         2015-12, Benjamini-Hochberg q = 10 %; confirmation = 2016-01..2025-12, one-sided, Holm 5 %;
         economic bar on the confirmed long legs against the market. Writes exp038.json.

Run: uv run --no-project --with pandas==<v> --with pyarrow==<v> --with scipy==<v> \
         python -I exp038_screen.py {pilot|score} <kit>
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

PRIMARY = "AltPorts_LiqScreen_ME_gt_NYSE20pct.parquet"
SECONDARY = {
    "op_original_paper": "PredictorPortsFull_OP.parquet",
    "vw_forced": "AltPorts_LiqScreen_VWforce.parquet",
    "deciles_vw": "AltPorts_DecilesVW.parquet",
}
DISC_END = pd.Period("2015-12", "M")
CONF_START, CONF_END = pd.Period("2016-01", "M"), pd.Period("2025-12", "M")
MIN_DISC_MONTHS = 24
BH_Q, HOLM_ALPHA = 0.10, 0.05
ECON_MIN_PCT_PER_MONTH, ECON_T = 0.25, 1.645
NW_LAGS = 12
NAMED = ["ShareVol", "DolVol", "VolMkt", "std_turn"]  # the operator's turnover question (2026-11-09)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_ports(path: Path) -> pd.DataFrame:
    d = pd.read_parquet(path)
    d["ym"] = pd.to_datetime(d["date"]).dt.to_period("M")
    return d


def wide(d: pd.DataFrame, signal: str) -> pd.DataFrame:
    s = d[d["signalname"] == signal]
    return s.pivot_table(index="ym", columns="port", values="ret", aggfunc="first").sort_index()


def long_leg(w: pd.DataFrame) -> tuple[str | None, str | None, float]:
    """The (long, short) ports whose difference reproduces LS every month, and the worst miss."""
    ports = sorted(c for c in w.columns if c != "LS")
    if "LS" not in w or len(ports) < 2:
        return None, None, math.inf
    lo, hi = ports[0], ports[-1]
    best = (None, None, math.inf)
    for a, b in ((hi, lo), (lo, hi)):
        diff = (w[a] - w[b] - w["LS"]).abs().dropna()
        miss = float(diff.max()) if len(diff) else math.inf
        if miss < best[2]:
            best = (a, b, miss)
    return best


def nw_t(x: np.ndarray, lags: int = NW_LAGS) -> tuple[float, float, int]:
    """Mean, Newey-West t (Bartlett weights), n."""
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 3:
        return math.nan, math.nan, n
    m = float(x.mean())
    e = x - m
    var = float(e @ e) / n
    for lag in range(1, min(lags, n - 1) + 1):
        var += 2 * (1 - lag / (lags + 1)) * float(e[lag:] @ e[:-lag]) / n
    se = math.sqrt(var / n) if var > 0 else math.nan
    return m, m / se if se and se > 0 else math.nan, n


def p_one_sided(t: float, n: int) -> float:
    return float(stats.t.sf(t, n - 1)) if not math.isnan(t) else 1.0


def bh(pvals: dict[str, float], q: float) -> set[str]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, k = len(items), 0
    for i, (_, p) in enumerate(items, start=1):
        if p <= q * i / m:
            k = i
    return {name for name, _ in items[:k]}


def holm(pvals: dict[str, float], alpha: float) -> set[str]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out = len(items), set()
    for i, (name, p) in enumerate(items):
        if p <= alpha / (m - i):
            out.add(name)
        else:
            break
    return out


def market(kit: Path) -> pd.Series:
    rows = []
    for line in (kit / "inputs" / "F-F_Research_Data_Factors.csv").read_text().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 5 and len(parts[0]) == 6 and parts[0].isdigit():
            rows.append((pd.Period(f"{parts[0][:4]}-{parts[0][4:]}", "M"), float(parts[1]) + float(parts[4])))
    s = pd.Series(dict(rows)).sort_index()
    return s[~s.index.duplicated(keep="first")]  # the monthly block comes first; annual rows are 4-digit


def window(s: pd.Series, start: pd.Period, end: pd.Period) -> np.ndarray:
    return s[(s.index >= start) & (s.index <= end)].to_numpy(dtype=float)


def pilot(kit: Path, doc: pd.DataFrame) -> None:
    d = load_ports(kit / "inputs" / PRIMARY)
    names = list(doc["Acronym"])
    missing = sorted(set(names) - set(d["signalname"]))
    legs, worst, insample = {}, 0.0, []
    for name in names:
        w = wide(d, name)
        a, b, miss = long_leg(w)
        legs[name] = (a, b)
        worst = max(worst, miss)
        r = doc.loc[doc["Acronym"] == name].iloc[0]
        ins = window(w["LS"], pd.Period(f"{int(r.SampleStartYear)}-01", "M"), pd.Period(f"{int(r.SampleEndYear)}-12", "M"))
        insample.append(float(np.nanmean(ins)) if len(ins) else math.nan)
    long_is_top = sum(1 for a, _ in legs.values() if a is not None and a != "01")
    pre1974 = d[(d["ym"] < pd.Period("1974-01", "M")) & (d["port"] != "LS")]["ret"].abs()
    mkt = market(kit)
    ins = np.array(insample)
    print(json.dumps({
        "predictors_in_doc": len(names), "missing_in_primary": missing,
        "long_leg_found": sum(1 for a, _ in legs.values() if a), "long_is_top_port": long_is_top,
        "worst_identity_miss": worst,
        "units_check_pre1974_port_abs_ret_median": float(pre1974.median()) if len(pre1974) else None,
        "market_months": len(mkt), "market_first_last": [str(mkt.index[0]), str(mkt.index[-1])],
        "market_has_2016_2025": bool(len(window(mkt, CONF_START, CONF_END)) == 120),
        "insample_direction_positive": int(np.sum(ins > 0)), "insample_n": int(np.sum(~np.isnan(ins))),
        "versions": {"python": sys.version.split()[0], "pandas": pd.__version__, "numpy": np.__version__,
                     "scipy": __import__("scipy").__version__, "pyarrow": __import__("pyarrow").__version__},
    }, indent=1))


def screen(d: pd.DataFrame, doc: pd.DataFrame, mkt: pd.Series, econ: bool) -> dict:
    rows, disc_p = {}, {}
    for _, r in doc.iterrows():
        name, year = r.Acronym, int(r.Year)
        w = wide(d, name)
        if "LS" not in w:
            rows[name] = {"year": year, "absent": True}
            continue
        ls = w["LS"]
        start = pd.Period(f"{year + 1}-01", "M")
        dm, dt, dn = nw_t(window(ls, start, DISC_END))
        cm, ct, cn = nw_t(window(ls, CONF_START, CONF_END))
        pm, pt, pn = nw_t(window(ls, start, CONF_END))
        im, it, inn = nw_t(window(ls, pd.Period(f"{int(r.SampleStartYear)}-01", "M"), pd.Period(f"{int(r.SampleEndYear)}-12", "M")))
        a, _, _ = long_leg(w)
        row = {"year": year, "insample_mean": im, "insample_t": it, "postpub_mean": pm, "postpub_t": pt,
               "postpub_n": pn, "disc_mean": dm, "disc_t": dt, "disc_n": dn, "conf_mean": cm, "conf_t": ct,
               "conf_n": cn, "long_port": a}
        if dn >= MIN_DISC_MONTHS:
            row["disc_p"] = disc_p[name] = p_one_sided(dt, dn)
        rows[name] = row
    passed = bh(disc_p, BH_Q)
    conf_p = {n: p_one_sided(rows[n]["conf_t"], rows[n]["conf_n"]) for n in passed}
    confirmed = holm(conf_p, HOLM_ALPHA)
    for n in passed:
        rows[n]["conf_p"] = conf_p[n]
    edge = []
    if econ:
        for n in sorted(confirmed):
            w = wide(d, n)
            leg = w[rows[n]["long_port"]]
            ex = (leg - mkt.reindex(leg.index)).dropna()
            em, et, en = nw_t(window(ex, CONF_START, CONF_END))
            rows[n].update({"econ_excess_mean": em, "econ_excess_t": et, "econ_n": en})
            if em >= ECON_MIN_PCT_PER_MONTH and et >= ECON_T:
                edge.append(n)
    def med(key: str) -> float:
        v = [r[key] for r in rows.values() if key in r and not math.isnan(r[key])]
        return float(np.median(v)) if v else math.nan
    def share_pos(key: str) -> float:
        v = [r[key] for r in rows.values() if key in r and not math.isnan(r[key])]
        return float(np.mean([x > 0 for x in v])) if v else math.nan
    return {
        "eligible_for_discovery": len(disc_p), "discovery_passed": sorted(passed),
        "confirmed": sorted(confirmed), "edge_candidates": sorted(edge),
        "median_insample_mean": med("insample_mean"), "median_postpub_mean": med("postpub_mean"),
        "median_conf_mean_2016_2025": med("conf_mean"), "share_conf_mean_positive": share_pos("conf_mean"),
        "rows": rows,
    }


def score(kit: Path, doc: pd.DataFrame) -> None:
    inputs = kit / "inputs"
    mkt = market(kit)
    out = {"inputs_sha256": {p.name: sha(p) for p in sorted(inputs.iterdir()) if p.suffix in {".parquet", ".csv"}},
           "script_sha256": sha(Path(__file__)),
           "primary": screen(load_ports(inputs / PRIMARY), doc, mkt, econ=True)}
    for key, fname in SECONDARY.items():
        out[key] = screen(load_ports(inputs / fname), doc, mkt, econ=False)
    (kit / "exp038.json").write_text(json.dumps(out, indent=1, default=str))
    p = out["primary"]
    print("PRIMARY (ex-micro, ME > NYSE 20th pct):")
    for k in ("eligible_for_discovery", "discovery_passed", "confirmed", "edge_candidates",
              "median_insample_mean", "median_postpub_mean", "median_conf_mean_2016_2025", "share_conf_mean_positive"):
        print(f"  {k}: {p[k]}")
    for n in sorted(set(p["discovery_passed"]) | set(NAMED)):
        r = p["rows"][n]
        print(f"  {n:22s} pub {r['year']} in-sample {r['insample_mean']:+.3f} post-pub {r['postpub_mean']:+.3f} "
              f"disc {r['disc_mean']:+.3f} (t {r['disc_t']:+.2f}, p {r.get('disc_p', float('nan')):.4f}) "
              f"2016-25 {r['conf_mean']:+.3f} (t {r['conf_t']:+.2f}, p {r.get('conf_p', float('nan')):.4f})"
              + (f" long-leg excess {r['econ_excess_mean']:+.3f} (t {r['econ_excess_t']:+.2f})" if "econ_excess_mean" in r else ""))
    for key in SECONDARY:
        s = out[key]
        print(f"{key}: passed {len(s['discovery_passed'])} confirmed {s['confirmed']} median in-sample "
              f"{s['median_insample_mean']:+.3f} post-pub {s['median_postpub_mean']:+.3f} 2016-25 {s['median_conf_mean_2016_2025']:+.3f}")
    print("exp038.json sha256", sha(kit / "exp038.json"))


def main() -> None:
    mode, kit = sys.argv[1], Path(sys.argv[2])
    doc = pd.read_csv(kit / "inputs" / "SignalDoc.csv")
    doc = doc[doc["Cat.Signal"] == "Predictor"].reset_index(drop=True)
    {"pilot": pilot, "score": score}[mode](kit, doc)


if __name__ == "__main__":
    main()
```
