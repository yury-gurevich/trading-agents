# EXP-041 — Do mid and small companies rise in the ten sessions after a sharp fall or a strong results reaction?

**Status:** PRE-REGISTERED 2026-11-16 (planner)
**Decision / origin:** the operator, 2026-11-16: *"I was hoping to keep stock for a week or two or when
win reaches certain percentage and then sell. Short term and small reward"*, then *"I guess yes"* to a
buy-side test at that horizon on smaller companies; [DL-324](../../design-log.md);
[R012](../idea-testing-foundation/INDEX.md) batch 7 · **Cost:** $0 (free vendor bars, public SEC
indexes, this laptop)

## 1. Why we needed this experiment

The operator's style is a holding of one to two weeks for a small gain. Every exit rule the replay can
run has now been measured behind or level with the stop alone
([EXP-022](EXP-022-does-an-exit-besides-the-stop-make-the-book-earn-more.md),
[EXP-037](EXP-037-does-a-take-profit-earn-more-than-the-stop-alone-in-falling-markets.md),
[EXP-040](EXP-040-does-selling-what-the-analyst-would-not-buy-today-beat-the-stop-alone.md)): in EXP-040
the week-long book won six trades in ten and still netted +0.24 % a trade. The style needs buys that
rise within the fortnight more often than the fleet's do, so the open question is on the buy side.

Nothing the fleet has tested answers it. The price-only score does not rank S&P 500 names
([EXP-015](EXP-015-price-only-ensemble-vs-technical-score.md),
[EXP-023](EXP-023-which-of-the-technical-scores-rules-carry-its-rank-ic.md)); monthly reversal fails on
the S&P 500 ([EXP-030](EXP-030-do-seventeen-stock-level-signals-sort-the-sp-500-month-to-month.md), X4);
headline events are priced by the next open
([EXP-031](EXP-031-do-corporate-events-in-headlines-predict-the-next-month.md)); and of 212 published
predictors none confirms outside micro caps
([EXP-038](EXP-038-do-published-stock-predictors-still-earn-after-publication-outside-micro-caps.md)),
with one lead, the return around the last earnings announcement. All of that is large companies, a
month's horizon, or both. The literature puts the two effects closest to the operator's style, the
short-term reversal after a fall and the drift after an earnings surprise, mostly in smaller companies
and in the first weeks. This experiment measures both there, at ten sessions, on a universe that keeps
the companies that later failed or were bought.

## 2. Hypothesis

**Universe.** US companies whose insiders filed with the SEC between 2016q4 and 2021q4 (section 3),
ranked on each month's last session by median dollar volume over the last 60 sessions (at least 40
bars, and one in the last 5). The rank holds for the next month: **LARGE** 1–500, **MID** 501–1000,
**SMALL** 1001–2000.

**Events**, each read at a session's close for a company in the bucket, bought at the next session's
open and sold at the close ten sessions after the event (if it stops trading sooner, at its last close):

| Idea | Event at the close of session t | Predicted | Source |
| --- | --- | --- | --- |
| **D1** sharp fall | the close is 10 % or more below the close five sessions earlier | + | Jegadeesh 1990; Lehmann 1990 |
| **D2** sharp fall, no results | D1, and no results release in sessions t−5 … t | + | Da, Liu and Schaumburg 2014 |
| **D3** sharp fall around results | D1, and a results release in sessions t−5 … t | − | Bernard and Thomas 1989; Chan 2003 |
| **E1** strong results reaction | t is a results-release session and the company's return over t−1 and t is 5 points or more above its bucket's equal-weighted mean | + | Chan, Jegadeesh and Lakonishok 1996; Brandt et al. 2008 |

A results release is a form 8-K with item 2.02; its session is the first whose 16:00 New York close is
at or after the SEC's acceptance time. After an event a company gives no new event of the same idea for
ten sessions.

**The statistic** (EXP-031's, at ten sessions). For each idea and bucket, the mean **ten-session excess
return**: from the open after the event to the close ten sessions after it, minus the same quantity
averaged over every company in the bucket. Events are averaged per session, and the t-statistic is
Newey–West (10 lags) over the session series.

**The funnel** (R012), over the eight cells D1, D2, D3, E1 × MID, SMALL:

- **Discovery**, event sessions 2017-01-03 → 2021-12-31: Benjamini–Hochberg at q = 10 % over the eight
  two-sided p-values.
- **Confirmation**, event sessions 2022-02-01 → the last with ten sessions after it: one-sided in the
  discovery's direction, Holm at 5 % over the passers.
- **Economic bar** for a confirmed positive cell: the same mean less 50 bps (25 bps a side) is above 0
  with t above 1.65 on the confirmation sessions. A confirmed negative cell is an avoid rule, reported.

**Verdict:** **LEAD** if a cell passes all three; **CONFIRMED, NOT ECONOMIC** if a cell confirms and none
passes the bar; **NONE** otherwise.

**Reported, no bar:** LARGE for every idea (is the effect a smaller-company one?); a five-session hold;
a deeper fall (20 %) and a stronger reaction (10 points); per cell the events, the mean raw return, the
median and the 1 %–99 % winsorised mean excess, the share of events that ended up, and the operator's
trade shape: the share that touched +5 % above the entry before −5 % below it within the ten sessions (a
session with both counts as the stop).

**What follows, fixed now:** LEAD → the planner pre-registers a book simulation of that cell (limited
capital, the operator's sell-at-a-gain-or-after-ten-sessions exit, against holding the market) before
proposing anything to build; the operator decides. NONE → these four rules are closed at this horizon.

## 3. Data

All in OneDrive `trading-agents-data/exp041-2026-11-16/`; vendor bars are licensed, never in the repo.

- **Registry** (`registry.csv`, SHA-256 `073600b111cd…`): 8,637 issuers from the SEC's Form
  3/4/5 data sets 2016q4 → 2021q4 (21 files, already on disk from EXP-027), each with the ticker its
  insiders' filings named most often in its last quarter and an `asof` date on which it was listed under
  it: the end of the latest earlier quarter with the same ticker, else its first filing date.
  Foreign issuers file no such forms, so ADRs are out, and so are funds without insiders' filings.
- **Earlier tickers** (`registry_fallback1.csv`, `registry_fallback2.csv`): for the 1,366 issuers with
  no bars under their last ticker (a bankrupt company trading over the counter under a "Q" ticker, an
  unlisted one), their previous ticker (251 tried, 86 found) and the one before (27 tried, 10 found).
- **Bars** (`bars/`, 54 files, checksums in `bars.sha256` `128a0e7c10d4…`): Alpaca SIP daily
  bars, `adjustment=all`, 2016-01-04 → 2026-10-30, each ticker resolved by the vendor as of its `asof`
  date so that renamed and delisted companies keep their own history. 7,367 registry rows have
  bars; 153 are dropped because their first bar is more than 100 days after `asof` (a later holder of the
  ticker); 7,214 − 7,092 = 122 more are the same series under two issuers (a holding-company
  reorganisation), kept once with both issuers' releases. **7,092 companies; 3,967 are in a bucket at
  some time.** 2,723 sessions. Every bucket is full (500 / 500 / 1,000) at every year end, 2016 → 2026.
- **Results releases** (`earnings.csv`, `b6c115a2c586…`): 167,471 forms 8-K with item 2.02
  filed from 2016-11-01, with the SEC's acceptance time, from `data.sec.gov`'s filing index for every
  registry issuer (none missing). 119,935 fall on a session of a kept company, 82,167 while it
  is in a bucket; in each year 2017 → 2026, about 90 % to 94 % of bucket companies have three or more.
- **Event counts** (`count.log`, `fc08bb84f1e2…`; calendar years 2017–2021 / 2022–2026; no
  return after an event was computed):

  | Idea | MID | SMALL | LARGE |
  | --- | --- | --- | --- |
  | D1 sharp fall | 7,750 / 8,422 | 18,912 / 21,356 | 5,803 / 7,199 |
  | D2 sharp fall, no results release | 6,448 / 6,954 | 15,874 / 18,136 | 4,745 / 5,914 |
  | D3 sharp fall around a results release | 2,018 / 2,129 | 4,834 / 5,320 | 1,511 / 1,811 |
  | E1 strong results reaction | 1,876 / 2,182 | 4,313 / 4,598 | 1,628 / 1,981 |

- **Known limits of the data.** Companies first listed after 2021 are absent (the registry's files end
  there; the SEC's file host refuses a client with no contact address, and the address was not sent),
  so the later years are the 2021 population as it ages; the buckets stay full. Rank by dollar volume
  stands in for size. A company that leaves its exchange exits at its last listed close, so the loss
  after a bankruptcy's delisting is not seen. Item 2.02 also covers trading updates, and a press
  release can precede its 8-K. A registry row can still carry a wrong ticker (an insider's typing).
- **Seen before:** EXP-038 read monthly portfolios of the earnings-announcement return and of monthly
  reversal through 2025, on another universe; EXP-030 the S&P 500's monthly reversal. No return of
  this data set has been read.

## 4. Tools and setup

Intel Core i7-7660U (2 cores / 4 threads), 16 GB, Windows 10 Pro 19045. Python 3.13.2, numpy 2.5.3,
pandas 3.0.6, requests 2.34.2 (the repo's venv, `python -I`). Repo `a1e97e53`. Alpaca market data v2
(`feed=sip`, the paper account's free plan); SEC `data.sec.gov/submissions`. No randomness: the tests are
analytic (Newey–West, normal p-values). No LLM, no broker order. Cost cap $0.

## 5. How it was conducted

1. `exp041_registry.py` built the registry; `exp041_bars.py` fetched the bars; `exp041_fallback.py` and a
   second `exp041_bars.py` pass fetched the earlier tickers (twice); `exp041_earnings.py` fetched the
   releases. None reads a return.
2. **Defects found and fixed before any return was read** (Appendix R will carry the detail): a blank
   ticker read as the ticker "NAN"; an `asof` at the quarter's end, after a mid-quarter delisting, which
   the vendor answered with a later holder of the ticker; one series under two issuers; companies whose
   last ticker is an over-the-counter one. Each was found from dates, names and row counts.
3. `exp041_score.py selftest`: on synthetic random-walk prices the funnel returns NONE, and with +0.3 % a
   session planted for ten sessions after each 10 % fall it measures +2.74 % (2.3 to 3.3 expected) and
   returns LEAD. `count` printed the event counts of section 3.
4. This record is committed with the scripts' checksums: the pre-registration.
5. `exp041_score.py score` runs once. Sections 6–8 are written from its output, the rule unchanged.

**What this cannot claim, stated before the result.** It measures a mean over every event of a kind, with
each session counting once; a book with limited capital buys only some of them, which is why LEAD goes
to a simulation and not to a build. Costs are assumed at 25 bps a side and can be higher in the SMALL
bucket. The benchmark is the bucket's equal-weighted mean, not a fund one can hold. The fleet's universe
is the S&P 500, so any lead needs a universe change before it can trade. One decade.

## 6. Results

*To be written after the run.*

## 7. Conclusions

*To be written after the run.*

## 8. Recommended code changes, and how to implement them

*To be written after the run.*

## Appendix P — Pre-registration (frozen)

Cells: D1 (five-session return ≤ −10 %), D2 (D1, no 8-K item 2.02 release in t−5 … t), D3 (D1 with one),
E1 (release session, return over t−1 and t ≥ 5 points above the bucket's equal-weighted mean) × MID
(dollar-volume rank 501–1000) and SMALL (1001–2000); rank on each month's last session by the 60-session
median dollar volume, held the next month. Buy at the open after the event, sell at the close ten
sessions after it; no repeat of an idea for a company within ten sessions. Statistic: the per-session
mean of the event's return minus the bucket's equal-weighted mean of the same quantity; Newey–West, 10
lags. Discovery 2017-01-03 → 2021-12-31, Benjamini–Hochberg q = 10 % over eight two-sided p; confirmation
from 2022-02-01, one-sided in the discovery's direction, Holm 5 %; economic bar for a positive cell: the
mean less 50 bps has t > 1.65 on the confirmation sessions. LEAD = a cell passes all three; CONFIRMED,
NOT ECONOMIC; NONE. LARGE, the five-session hold, the −20 % and +10-point variants and the trade-shape
shares are reported without a bar. SHA-256: `exp041_score.py` `28e2dcb68909c9155687ed672d47a473f9e3306efb1084c21af8f332c523f02d`,
`registry.csv` `073600b111cdc05bd0060edc7d4af11bb66b20c7e1867efdb16ae5cbf7ec797a`, `registry_fallback1.csv` `9b5b06a8ca4e816fbe9b6ca873e88b0a09e41abe5351670fcdf2eb17ede5c870`,
`registry_fallback2.csv` `3ed48fc7c0be67d4c19a5be51c1b5813ecbe0b322bd8a39129f4681dd9b050e5`, `earnings.csv` `b6c115a2c586e09bcc2579790b3cd863328de21eaf6733e9374a829d4d82e2d9`,
`bars.sha256` `128a0e7c10d45fb5905d8517a37fe325beef4a2a30c86677152c9dd7982c0d45`, `count.log` `fc08bb84f1e257e498fd68a7588f86bc1e497dc99f3a16759b2b43c5408b12d2`.

## Appendix R — Run record

*To be written after the run.*

## Appendix S — Scripts

Kit: OneDrive `trading-agents-data/exp041-2026-11-16/`. Build, in order (`Z` = the folder of the SEC's
`20YYqN_form345.zip` files, `E` = an env file with the Alpaca keys):
`python -I exp041_registry.py Z registry.csv`; `python -I exp041_bars.py registry.csv E bars`;
`python -I exp041_fallback.py Z registry.csv bars 1 registry_fallback1.csv`, then `exp041_bars.py` on
that file; the same with `2`; `python -I exp041_earnings.py registry.csv earnings.csv earnings.done`.
Scoring, with `R` = the three registry files: `python -I exp041_score.py selftest`, `… count --bars bars
--registry R --earnings earnings.csv`, `… score --bars bars --registry R --earnings earnings.csv --out
exp041.json`. SHA-256 of the build scripts: `exp041_registry.py` `2e2786220e3a886f…`,
`exp041_fallback.py` `52bac8fe074c8a34…`, `exp041_bars.py` `1499d1ea7b55ea74…`,
`exp041_earnings.py` `6de1132a0e428c71…`. Three pilot checks (`exp041_check.py`,
`exp041_dupes.py`, `exp041_asof_check.py`; dates, names and counts only) stay in the kit.

### `exp041_score.py`

```python
"""EXP-041: do mid and small companies rise in the ten sessions after a sharp drop or a strong earnings reaction?

Reads the kit's daily bars (one company per CIK, delisted ones included) and earnings-release times.
Ranks companies each month end by median dollar volume (LARGE 1-500, MID 501-1000, SMALL 1001-2000),
finds four kinds of event at a session's close, buys at the next open, sells at the close ten sessions
later, and scores the return against the same bucket's equal-weighted mean over the same window.

  python -I exp041_score.py liquid   --bars <dir> --registry <csv> <csv> <csv> --out <ciks.txt>
  python -I exp041_score.py count    --bars <dir> --registry <csv> <csv> <csv> --earnings <csv>
  python -I exp041_score.py selftest
  python -I exp041_score.py score    --bars <dir> --registry <csv> <csv> <csv> --earnings <csv> --out <json>

`liquid` and `count` compute no return after an event. `selftest` uses synthetic prices only.
"""

from __future__ import annotations

import argparse
import json
import math
import warnings
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HOLD, HOLD_SHORT = 10, 5
DROP, DROP_DEEP, BEAT, BEAT_BIG = -0.10, -0.20, 0.05, 0.10
RANK_WINDOW, RANK_MIN_BARS = 60, 40
BUCKETS = {"LARGE": (1, 500), "MID": (501, 1000), "SMALL": (1001, 2000)}
BARRED_BUCKETS = ("MID", "SMALL")
SIGNALS = ("D1", "D2", "D3", "E1")  # barred; the variants below are reported only
DISCOVERY = ("2017-01-01", "2021-12-31")
CONFIRMATION = ("2022-02-01", "2026-12-31")  # a month after discovery, so no holding window spans both
BH_Q, HOLM_ALPHA, COST_ROUND_TRIP, ECON_T = 0.10, 0.05, 0.005, 1.65
TARGET, STOP = 0.05, -0.05
MIN_NAMES_A_SESSION = 500
ASOF_SLACK_DAYS = 100
NY = ZoneInfo("America/New_York")
warnings.filterwarnings("ignore", category=RuntimeWarning)  # all-NaN windows of companies not yet listed


# ---------------------------------------------------------------- loading

def load_bars(folder: Path, registries: list[Path]) -> dict:
    """Bars of every registry row (the main registry first, then the earlier-ticker passes).

    A row's bars are dropped if their first session is more than ASOF_SLACK_DAYS after the row's
    `asof` date: for a ticker that no listed company held on that date the vendor answers with a
    LATER holder's history, which is usually another company. (The slack keeps a blank-cheque company
    whose shares began trading some weeks after its first filing.) Bars that END before the date are
    kept: a company that had left its exchange by then, whose listed history is wanted.
    """
    rows = pd.concat([pd.read_csv(r, dtype={"cik": np.int64}) for r in registries])
    asof = {(q, c): a for q, c, a in zip(rows["quarter"], rows["cik"], rows["asof"])}
    wide = {k: [] for k in ("open", "high", "low", "close", "volume")}
    fetched = wrong = 0
    for path in sorted(folder.glob("*.csv.gz")):
        df = pd.read_csv(path, dtype={"cik": np.int64, "date": str, "open": np.float64, "high": np.float64,
                                      "low": np.float64, "close": np.float64, "volume": np.float64})
        if df.empty:
            continue
        stem = path.name[: -len(".csv.gz")]
        first = pd.to_datetime(df.groupby("cik")["date"].min())
        limit = pd.to_datetime(first.index.map(lambda c: asof[(stem, c)])) + pd.Timedelta(days=ASOF_SLACK_DAYS)
        near = set(first.index[first.to_numpy() <= limit.to_numpy()])
        fetched += df["cik"].nunique()
        wrong += df["cik"].nunique() - len(near)
        ok = (df[["open", "high", "low", "close"]] > 0).all(axis=1) & (df["volume"] >= 0) & df["cik"].isin(near)
        df = df[ok].drop_duplicates(["cik", "date"])
        for k in wide:
            wide[k].append(df.pivot(index="date", columns="cik", values=k))
    mats = {k: pd.concat(v, axis=1).sort_index() for k, v in wide.items()}
    keep = mats["close"].notna().sum(axis=1) >= MIN_NAMES_A_SESSION
    out = {k: m[keep].to_numpy(dtype=np.float64) for k, m in mats.items()}
    out["sessions"] = list(mats["close"].index[keep])
    out["ciks"] = [int(c) for c in mats["close"].columns]
    out["fetched"], out["not_listed_at_asof"] = fetched, wrong
    return one_series_one_company(out, registries[0])


def one_series_one_company(P: dict, registry: Path) -> dict:
    """Registry entries whose bars are the same series are one company: the entry seen last is kept,
    and `alias` sends the others' CIKs to it (so its earnings releases are those of all of them)."""
    reg = pd.read_csv(registry, dtype={"cik": np.int64}).set_index("cik")
    C, V = P["close"], P["volume"]
    groups: dict[tuple, list[int]] = {}
    for i in range(C.shape[1]):
        ok = np.isfinite(C[:, i])
        key = (int(np.argmax(ok)), int(ok.sum()), round(float(np.nansum(C[:, i])), 4), round(float(np.nansum(V[:, i])), 0))
        groups.setdefault(key, []).append(i)
    keep, alias = [], {}
    for cols in groups.values():
        best = max(cols, key=lambda i: (reg.at[P["ciks"][i], "quarter"], int(reg.at[P["ciks"][i], "n"]), -P["ciks"][i]))
        keep.append(best)
        alias.update({P["ciks"][i]: P["ciks"][best] for i in cols})
    keep.sort()
    out = {k: (v[:, keep] if isinstance(v, np.ndarray) else v) for k, v in P.items()}
    out["ciks"] = [P["ciks"][i] for i in keep]
    out["alias"] = alias
    out["loaded"] = C.shape[1]
    return out


def load_earnings(path: Path, sessions: list[str], ciks: list[int], alias: dict[int, int]) -> np.ndarray:
    """ER[t, i]: session t is the first whose 16:00 New York close is at or after a release by i."""
    er = np.zeros((len(sessions), len(ciks)), dtype=bool)
    col = {c: i for i, c in enumerate(ciks)}
    df = pd.read_csv(path, dtype={"cik": np.int64, "accepted": str})
    df["cik"] = df["cik"].map(lambda c: alias.get(c, c))
    when = pd.to_datetime(df["accepted"], utc=True).dt.tz_convert(NY)
    day = when.dt.strftime("%Y-%m-%d").to_numpy()
    late = (when.dt.hour >= 16).to_numpy()
    sess = np.array(sessions)
    pos = np.where(late, np.searchsorted(sess, day, side="right"), np.searchsorted(sess, day, side="left"))
    for c, p in zip(df["cik"].to_numpy(), pos):
        if c in col and p < len(sessions):
            er[p, col[c]] = True
    return er


# ---------------------------------------------------------------- panel

def buckets(close: np.ndarray, volume: np.ndarray, sessions: list[str]) -> np.ndarray:
    """B[t, i]: the bucket (1 LARGE, 2 MID, 3 SMALL, 0 none) of i on session t, set at the previous month end."""
    T, N = close.shape
    dv = close * volume
    out = np.zeros((T, N), dtype=np.int8)
    month = [s[:7] for s in sessions]
    ends = [t for t in range(T - 1) if month[t] != month[t + 1]]
    for k, m in enumerate(ends):
        if m + 1 < RANK_WINDOW:
            continue
        win = dv[m + 1 - RANK_WINDOW : m + 1]
        enough = (np.isfinite(win).sum(axis=0) >= RANK_MIN_BARS) & np.isfinite(win[-5:]).any(axis=0)
        med = np.where(enough, np.nanmedian(np.where(np.isfinite(win), win, np.nan), axis=0), -np.inf)
        order = np.argsort(-med, kind="stable")
        rank = np.empty(N, dtype=np.int64)
        rank[order] = np.arange(1, N + 1)
        rank[~enough] = 10**9
        row = np.zeros(N, dtype=np.int8)
        for code, (lo, hi) in enumerate(BUCKETS.values(), start=1):
            row[(rank >= lo) & (rank <= hi)] = code
        last = ends[k + 1] if k + 1 < len(ends) else T - 1
        out[m + 1 : last + 1] = row
    return out


def prepare(P: dict) -> tuple[dict, np.ndarray]:
    """Buckets ranked over every company, then only the companies ever in a bucket are kept."""
    B = buckets(P["close"], P["volume"], P["sessions"])
    ever = B.any(axis=0)
    Q = {k: (v[:, ever] if isinstance(v, np.ndarray) and v.ndim == 2 else v) for k, v in P.items()}
    Q["ciks"] = [c for c, hit in zip(P["ciks"], ever) if hit]
    return Q, B[:, ever]


def shift_back(a: np.ndarray, k: int) -> np.ndarray:
    """a[t - k] at row t (NaN / False for the first k rows)."""
    out = np.full_like(a, np.nan if a.dtype.kind == "f" else 0)
    out[k:] = a[:-k]
    return out


def bucket_mean(x: np.ndarray, B: np.ndarray) -> np.ndarray:
    """M[t, i]: the equal-weighted mean of x[t] over the companies in i's bucket on session t."""
    out = np.full(x.shape, np.nan)
    for code in (1, 2, 3):
        mask = (B == code) & np.isfinite(x)
        n = mask.sum(axis=1)
        mean = np.where(n > 0, np.where(mask, x, 0.0).sum(axis=1) / np.maximum(n, 1), np.nan)
        out = np.where(B == code, mean[:, None], out)
    return out


def forward(open_: np.ndarray, close: np.ndarray, hold: int) -> np.ndarray:
    """F[t, i]: close of the last traded session in t+1 .. t+hold over the open of t+1, minus one."""
    T, _ = close.shape
    entry = np.full(close.shape, np.nan)
    entry[:-1] = open_[1:]
    px = np.full(close.shape, np.nan)
    for k in range(1, hold + 1):
        nxt = np.full(close.shape, np.nan)
        nxt[:-k] = close[k:]
        px = np.where(np.isfinite(nxt), nxt, px)
    f = px / entry - 1.0
    f[T - hold :] = np.nan  # the exit session must exist
    return f


def touch(open_, high, low, close, hold):
    """First of +TARGET (by the high) or STOP (by the low) from the entry open; a session with both is a stop."""
    entry = np.full(close.shape, np.nan)
    entry[:-1] = open_[1:]
    state = np.zeros(close.shape, dtype=np.int8)  # 0 neither, 1 target first, -1 stop first
    for k in range(1, hold + 1):
        hi, lo = np.full(close.shape, np.nan), np.full(close.shape, np.nan)
        hi[:-k], lo[:-k] = high[k:], low[k:]
        stop = (lo <= entry * (1 + STOP)) & (state == 0)
        state[stop] = -1
        target = (hi >= entry * (1 + TARGET)) & (state == 0)
        state[target] = 1
    return state


def signals(P: dict, ER: np.ndarray, B: np.ndarray) -> dict[str, np.ndarray]:
    close = P["close"]
    r1 = close / shift_back(close, 1) - 1.0
    r5 = close / shift_back(close, 5) - 1.0
    abn = r1 - bucket_mean(r1, B)
    abn2 = abn + shift_back(abn, 1)
    recent = ER.copy()
    for k in range(1, 6):
        recent |= shift_back(ER, k)
    drop, deep = r5 <= DROP, r5 <= DROP_DEEP
    return {"D1": drop, "D2": drop & ~recent, "D3": drop & recent, "E1": ER & (abn2 >= BEAT),
            "D1_deep": deep, "E1_big": ER & (abn2 >= BEAT_BIG)}


def events(sig: np.ndarray, B: np.ndarray, code: int, buyable: np.ndarray, hold: int) -> np.ndarray:
    """First triggers only: after an event a company gives no new one of that kind for `hold` sessions."""
    T, N = sig.shape
    out = np.zeros((T, N), dtype=bool)
    free_from = np.zeros(N, dtype=np.int64)
    raw = sig & (B == code) & buyable
    for t in range(T):
        ev = raw[t] & (free_from <= t)
        out[t] = ev
        free_from[ev] = t + hold + 1
    return out


# ---------------------------------------------------------------- statistics

def newey_west_t(x: np.ndarray, lags: int) -> tuple[float, float]:
    n = len(x)
    if n < 2 * lags + 2:
        return float("nan"), float("nan")
    d = x - x.mean()
    var = (d @ d) / n
    for k in range(1, lags + 1):
        var += 2.0 * (1.0 - k / (lags + 1.0)) * (d[k:] @ d[:-k]) / n
    if var <= 0:
        return float(x.mean()), float("nan")
    return float(x.mean()), float(x.mean() / math.sqrt(var / n))


def p_two(t: float) -> float:
    return math.erfc(abs(t) / math.sqrt(2.0)) if math.isfinite(t) else 1.0


def p_one(t: float, sign: int) -> float:
    return 0.5 * math.erfc(sign * t / math.sqrt(2.0)) if math.isfinite(t) else 1.0


def benjamini_hochberg(p: dict[str, float], q: float) -> set[str]:
    order = sorted(p, key=p.get)
    m, cut = len(order), 0
    for i, key in enumerate(order, start=1):
        if p[key] <= q * i / m:
            cut = i
    return set(order[:cut])


def holm(p: dict[str, float], alpha: float) -> set[str]:
    order, out = sorted(p, key=p.get), set()
    for i, key in enumerate(order):
        if p[key] > alpha / (len(order) - i):
            break
        out.add(key)
    return out


def cell(ev, fwd, bench, state, sessions, window, hold) -> dict:
    lo, hi = window
    rows = [t for t, s in enumerate(sessions) if lo <= s <= hi and ev[t].any() and np.isfinite(bench[t][ev[t]]).all()]
    if not rows:
        return {"events": 0, "sessions": 0}
    excess = [fwd[t][ev[t]] - bench[t][ev[t]] for t in rows]
    raw = np.concatenate([fwd[t][ev[t]] for t in rows])
    allx = np.concatenate(excess)
    daily = np.array([e.mean() for e in excess])
    mean, t = newey_west_t(daily, hold)
    net_mean, net_t = newey_west_t(daily - COST_ROUND_TRIP, hold)
    st = np.concatenate([state[t][ev[t]] for t in rows])
    w_lo, w_hi = np.percentile(allx, [1, 99])
    return {
        "events": int(len(allx)), "sessions": len(rows),
        "mean_excess_pct": round(100 * mean, 3), "t": round(t, 2),
        "net_mean_excess_pct": round(100 * net_mean, 3), "net_t": round(net_t, 2),
        "event_mean_excess_pct": round(100 * float(allx.mean()), 3),
        "event_median_excess_pct": round(100 * float(np.median(allx)), 3),
        "event_winsorised_mean_excess_pct": round(100 * float(np.clip(allx, w_lo, w_hi).mean()), 3),
        "mean_raw_return_pct": round(100 * float(raw.mean()), 3),
        "share_up": round(float((raw > 0).mean()), 3),
        "share_target_first": round(float((st == 1).mean()), 3),
        "share_stop_first": round(float((st == -1).mean()), 3),
    }


def analyse(P: dict, B: np.ndarray, ER: np.ndarray, hold: int = HOLD) -> dict:
    sig = signals(P, ER, B)
    fwd = forward(P["open"], P["close"], hold)
    bench = bucket_mean(fwd, B)
    state = touch(P["open"], P["high"], P["low"], P["close"], hold)
    buyable = np.isfinite(fwd)
    out = {}
    for name, s in sig.items():
        for code, bucket in enumerate(BUCKETS, start=1):
            ev = events(s, B, code, buyable, hold)
            out[f"{name} {bucket}"] = {
                "discovery": cell(ev, fwd, bench, state, P["sessions"], DISCOVERY, hold),
                "confirmation": cell(ev, fwd, bench, state, P["sessions"], CONFIRMATION, hold),
            }
    return out


def funnel(cells: dict) -> dict:
    barred = [f"{s} {b}" for s in SIGNALS for b in BARRED_BUCKETS]
    p_disc = {k: p_two(cells[k]["discovery"].get("t", float("nan"))) for k in barred}
    passed = benjamini_hochberg(p_disc, BH_Q)
    sign = {k: 1 if cells[k]["discovery"]["t"] > 0 else -1 for k in passed}
    p_conf = {k: p_one(cells[k]["confirmation"].get("t", float("nan")), sign[k]) for k in passed}
    confirmed = holm(p_conf, HOLM_ALPHA)
    economic = {k: cells[k]["confirmation"]["net_t"] > ECON_T for k in confirmed if sign[k] > 0}
    rows = {k: {"p_discovery": round(p_disc[k], 5), "passed_discovery": k in passed,
                "direction": sign.get(k), "p_confirmation": round(p_conf[k], 5) if k in passed else None,
                "confirmed": k in confirmed, "economic": economic.get(k)} for k in barred}
    verdict = ("LEAD" if any(economic.values()) else
               "CONFIRMED, NOT ECONOMIC" if confirmed else "NONE")
    return {"rows": rows, "verdict": verdict}


def count(P: dict, B: np.ndarray, ER: np.ndarray) -> dict:
    """Event counts by year. Reads the open of the next session only; no return after an event."""
    sig = signals(P, ER, B)
    buyable = np.zeros(P["close"].shape, dtype=bool)
    buyable[:-HOLD] = np.isfinite(P["open"][1 : len(P["sessions"]) - HOLD + 1])
    years = np.array([s[:4] for s in P["sessions"]])
    out = {"sessions": [P["sessions"][0], P["sessions"][-1], len(P["sessions"])], "companies": len(P["ciks"]),
           "bucket_members_median": {b: int(np.median((B == c).sum(axis=1)[B.any(axis=1)]))
                                     for c, b in enumerate(BUCKETS, start=1)},
           "first_bucketed_session": P["sessions"][int(np.argmax(B.any(axis=1)))],
           "earnings_releases": int(ER.sum()), "releases_in_a_bucket": int((ER & (B > 0)).sum())}
    for name, s in sig.items():
        for code, bucket in enumerate(BUCKETS, start=1):
            ev = events(s, B, code, buyable, HOLD)
            per = ev.sum(axis=1)
            out[f"{name} {bucket}"] = {y: int(per[years == y].sum()) for y in sorted(set(years)) if per[years == y].sum()}
    return out


# ---------------------------------------------------------------- self-test

def synthetic(seed: int, drift: float) -> tuple[dict, np.ndarray, np.ndarray]:
    """Random-walk prices; with `drift`, every company gains that much a session for ten sessions after a 10 % five-session fall."""
    rng = np.random.default_rng(seed)
    T, N = 900, 1300
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2017-01-02", periods=T)]
    ret = rng.normal(0.0, 0.02, size=(T, N))
    close = np.empty((T, N))
    close[0] = 50.0
    boost = np.zeros(N, dtype=np.int64)
    for t in range(1, T):
        r = ret[t] + np.where(boost > 0, drift, 0.0)
        close[t] = close[t - 1] * (1.0 + r)
        boost = np.maximum(boost - 1, 0)
        if t >= 5:
            boost[(close[t] / close[t - 5] - 1.0 <= DROP) & (boost == 0)] = HOLD
    open_ = np.vstack([close[:1], close[:-1]])  # the open is the previous close, so the hold is ten full sessions
    volume = np.tile(rng.lognormal(12.0, 1.5, size=N), (T, 1))
    P = {"open": open_, "high": np.maximum(open_, close), "low": np.minimum(open_, close), "close": close,
         "volume": volume, "sessions": days, "ciks": list(range(1, N + 1))}
    P, B = prepare(P)
    return P, B, np.zeros(P["close"].shape, dtype=bool)


def selftest() -> int:
    global DISCOVERY, CONFIRMATION
    keep = DISCOVERY, CONFIRMATION
    DISCOVERY, CONFIRMATION = ("2017-01-01", "2018-12-31"), ("2019-01-01", "2030-12-31")
    ok = True
    for label, drift, lo, hi in (("no effect planted", 0.0, -0.4, 0.4), ("+0.3 % a session planted", 0.003, 2.3, 3.3)):
        cells = analyse(*synthetic(7, drift))
        got = cells["D1 MID"]["discovery"]
        good = lo <= got["mean_excess_pct"] <= hi
        ok &= good
        print(f"{label}: D1 MID events {got['events']} mean excess {got['mean_excess_pct']} % t {got['t']} "
              f"(expected {lo} to {hi}) {'ok' if good else 'MISMATCH'}")
        f = funnel(cells)
        print("  verdict", f["verdict"], {k: v["passed_discovery"] for k, v in f["rows"].items()})
        ok &= (f["verdict"] == "NONE") == (drift == 0.0)
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    mean, t = newey_west_t(x, 0)
    plain = x.mean() / math.sqrt(x.var() / len(x))
    ok &= abs(t - plain) < 1e-9
    ok &= benjamini_hochberg({"a": 0.001, "b": 0.04, "c": 0.5}, 0.10) == {"a", "b"}
    ok &= holm({"a": 0.001, "b": 0.04}, 0.05) == {"a", "b"} and holm({"a": 0.03, "b": 0.04}, 0.05) == set()
    DISCOVERY, CONFIRMATION = keep
    print("selftest passed" if ok else "SELFTEST FAILED")
    return 0 if ok else 1


# ---------------------------------------------------------------- entry

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("liquid", "count", "selftest", "score"))
    ap.add_argument("--bars", type=Path)
    ap.add_argument("--registry", type=Path, nargs="+", help="the main registry, then the earlier-ticker passes")
    ap.add_argument("--earnings", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.mode == "selftest":
        return selftest()
    P = load_bars(a.bars, a.registry)
    loaded, distinct, alias = P["loaded"], len(P["ciks"]), P["alias"]
    build = {"registry_rows_with_bars": P["fetched"], "dropped_not_listed_at_asof": P["not_listed_at_asof"],
             "price_series": loaded, "distinct_price_series": distinct}
    P, B = prepare(P)
    if a.mode == "liquid":
        a.out.write_text("\n".join(str(c) for c in P["ciks"]) + "\n", encoding="utf-8")
        print("sessions", P["sessions"][0], P["sessions"][-1], len(P["sessions"]), build, "ever in a bucket", len(P["ciks"]))
        return 0
    ER = load_earnings(a.earnings, P["sessions"], P["ciks"], alias)
    if a.mode == "count":
        print(json.dumps({"build": build, **count(P, B, ER)}, indent=1))
        return 0
    cells = analyse(P, B, ER)
    short = analyse(P, B, ER, HOLD_SHORT)
    result = {"sessions": [P["sessions"][0], P["sessions"][-1], len(P["sessions"])], "companies": len(P["ciks"]),
              "build": build, "funnel": funnel(cells), "hold_10": cells, "hold_5": short}
    text = json.dumps(result, indent=1)
    a.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### `exp041_registry.py`

```python
"""EXP-041 stage 1: a ticker registry of US companies from SEC Form 3/4/5 filings, 2016q4 -> 2021q4.

One row per issuer CIK: the ticker its insiders' filings named most often in the last quarter the
issuer appears with a ticker, and an `asof` date on which the bar vendor resolves that ticker:
the end of the latest EARLIER quarter in which the issuer had the same ticker (it filed again after
that date, so it was listed on it); for an issuer seen in one quarter only, its first filing date.
Reads the SEC "insider transactions" data sets already on disk. No price is read.

  python -I exp041_registry.py <dir of 20YYqN_form345.zip> <registry.csv>
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

QUARTER_END = {"1": "03-31", "2": "06-30", "3": "09-30", "4": "12-31"}
MISSING = {"", "NONE", "NA", "N/A", "N.A.", "N.A", "NULL", "TBD", "-", "--", "NYSE", "NASDAQ", "OTC"}


def clean(raw: str) -> str | None:
    s = str(raw).upper().strip()
    if s in MISSING:
        return None
    s = re.sub(r"^(NYSE|NASDAQ|NYSEMKT|NYSEAMERICAN|AMEX|OTC|OB|OTCBB)\s*:\s*", "", s)
    s = re.sub(r"[\[\]\(\)]", " ", s)
    s = re.sub(r"(:OTC|\bOB\b)", " ", s)
    tok = [t for t in re.split(r"[\s,;/]+", s) if t]
    if not tok or tok[0] in MISSING:
        return None
    t = tok[0].replace("-", ".")
    return t if re.fullmatch(r"[A-Z]{1,5}(\.[A-Z])?", t) else None


def main() -> None:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    parts = []
    for path in sorted(src.glob("20*q*_form345.zip")):
        q = path.name[:6]
        with zipfile.ZipFile(path) as z, z.open("SUBMISSION.tsv") as f:
            sub = pd.read_csv(f, sep="\t", usecols=["FILING_DATE", "ISSUERCIK", "ISSUERNAME", "ISSUERTRADINGSYMBOL"],
                              dtype=str, quoting=3, on_bad_lines="skip", keep_default_na=False)
        sub["ticker"] = sub["ISSUERTRADINGSYMBOL"].map(clean)
        sub["filed"] = pd.to_datetime(sub["FILING_DATE"], format="%d-%b-%Y", errors="coerce")
        sub = sub[sub["ticker"].notna() & sub["ISSUERCIK"].str.fullmatch(r"\d+") & sub["filed"].notna()]
        g = sub.groupby(["ISSUERCIK", "ticker"]).agg(n=("ticker", "size"), name=("ISSUERNAME", "first"),
                                                     first_filed=("filed", "min")).reset_index()
        g["quarter"] = q
        parts.append(g)
        print(q, "issuers", g["ISSUERCIK"].nunique(), flush=True)
    df = pd.concat(parts)
    df["cik"] = df["ISSUERCIK"].astype(int)
    df = df.sort_values(["cik", "quarter", "n", "ticker"], ascending=[True, True, False, True])
    modal = df.drop_duplicates(["cik", "quarter"]).sort_values(["cik", "quarter"])
    rows = []
    for cik, grp in modal.groupby("cik"):
        last = grp.iloc[-1]
        earlier = grp.iloc[:-1]
        same = earlier[earlier["ticker"] == last["ticker"]]
        if len(same):
            q = same.iloc[-1]["quarter"]
            asof = f"{q[:4]}-{QUARTER_END[q[5]]}"
        else:
            asof = last["first_filed"].strftime("%Y-%m-%d")
        rows.append((cik, last["ticker"], asof, last["quarter"], int(last["n"]), last["name"]))
    reg = pd.DataFrame(rows, columns=["cik", "ticker", "asof", "quarter", "n", "name"])
    before = len(reg)
    reg = reg.sort_values(["asof", "ticker", "n", "cik"], ascending=[True, True, False, True]).drop_duplicates(["asof", "ticker"])
    reg.sort_values("cik").to_csv(out, index=False)
    print("issuers", before, "kept", len(reg), "dropped as ticker collisions", before - len(reg))
    print("distinct asof dates", reg["asof"].nunique(), "| by last quarter:")
    print(reg.groupby("quarter").size().to_string())


if __name__ == "__main__":
    main()
```

### `exp041_fallback.py`

```python
"""EXP-041 stage 2b: earlier tickers for registry companies that got no bars under their last one.

A company that left its exchange (a bankruptcy trading over the counter under a "Q" ticker, say)
is named by its insiders' last filings under a ticker the bar vendor does not carry. For each such
company this lists its earlier tickers, latest first, each with an `asof` date set by the registry's
rule, and writes pass <k>: the k-th earlier ticker of every company still without bars.

  python -I exp041_fallback.py <dir of form345 zips> <registry.csv> <bars dir> <k> <out.csv>
"""

from __future__ import annotations

import csv
import gzip
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from exp041_registry import QUARTER_END, clean  # noqa: E402


def with_bars(folder: Path) -> set[int]:
    have = set()
    for path in folder.glob("*.csv.gz"):
        with gzip.open(path, "rt") as fh:
            next(fh)
            have.update(int(line.split(",", 1)[0]) for line in fh)
    return have


def main() -> None:
    src, registry, bars, k, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), int(sys.argv[4]), Path(sys.argv[5])
    reg = {int(r["cik"]): r for r in csv.DictReader(open(registry, encoding="utf-8"))}
    missing = set(reg) - with_bars(bars)
    parts = []
    for path in sorted(src.glob("20*q*_form345.zip")):
        with zipfile.ZipFile(path) as z, z.open("SUBMISSION.tsv") as f:
            sub = pd.read_csv(f, sep="\t", usecols=["FILING_DATE", "ISSUERCIK", "ISSUERTRADINGSYMBOL"], dtype=str,
                              quoting=3, on_bad_lines="skip", keep_default_na=False)
        sub = sub[sub["ISSUERCIK"].str.fullmatch(r"\d+")]
        sub["cik"] = sub["ISSUERCIK"].astype(int)
        sub = sub[sub["cik"].isin(missing)].copy()
        sub["ticker"] = sub["ISSUERTRADINGSYMBOL"].map(clean)
        sub["filed"] = pd.to_datetime(sub["FILING_DATE"], format="%d-%b-%Y", errors="coerce")
        sub = sub[sub["ticker"].notna() & sub["filed"].notna()]
        g = sub.groupby(["cik", "ticker"]).agg(n=("ticker", "size"), first_filed=("filed", "min")).reset_index()
        g["quarter"] = path.name[:6]
        parts.append(g)
    df = pd.concat(parts).sort_values(["cik", "quarter", "n", "ticker"], ascending=[True, True, False, True])
    modal = df.drop_duplicates(["cik", "quarter"]).sort_values(["cik", "quarter"])
    rows = []
    for cik, grp in modal.groupby("cik"):
        tried, order = {reg[cik]["ticker"]}, 0
        for i in range(len(grp) - 1, -1, -1):  # latest quarter first
            row = grp.iloc[i]
            if row["ticker"] in tried:
                continue
            tried.add(row["ticker"])
            order += 1
            if order != k:
                continue
            same = grp.iloc[:i][grp.iloc[:i]["ticker"] == row["ticker"]]
            if len(same):
                q = same.iloc[-1]["quarter"]
                asof = f"{q[:4]}-{QUARTER_END[q[5]]}"
            else:
                asof = row["first_filed"].strftime("%Y-%m-%d")
            rows.append((cik, row["ticker"], asof, f"fallback{k}-{row['quarter']}", int(row["n"]), reg[cik]["name"]))
    fb = pd.DataFrame(rows, columns=["cik", "ticker", "asof", "quarter", "n", "name"])
    fb = fb.sort_values(["asof", "ticker", "n", "cik"], ascending=[True, True, False, True]).drop_duplicates(["asof", "ticker"])
    fb.sort_values("cik").to_csv(out, index=False)
    print("registry", len(reg), "without bars", len(missing), f"with an earlier ticker (pass {k})", len(fb))


if __name__ == "__main__":
    main()
```

### `exp041_bars.py`

```python
"""EXP-041 stage 2: Alpaca SIP daily bars (adjustment=all) for every registry issuer, 2016-01-04 -> 2026-10-30.

Each ticker is resolved as of its registry `asof` date, so renamed and delisted companies map to
their own history. One gz file per registry quarter; a finished file is skipped on a re-run. Bars only.

  python -I exp041_bars.py <registry.csv> <env_file> <out_dir>
"""

from __future__ import annotations

import csv
import gzip
import sys
import time
from pathlib import Path

import requests

URL = "https://data.alpaca.markets/v2/stocks/bars"
START, END = "2016-01-04", "2026-10-30"


def env(path: str) -> dict[str, str]:
    out = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def fetch(symbols, asof, headers):
    token = None
    while True:
        params = {"symbols": ",".join(symbols), "timeframe": "1Day", "start": START, "end": END,
                  "adjustment": "all", "feed": "sip", "limit": 10000, "asof": asof}
        if token:
            params["page_token"] = token
        for attempt in range(8):
            try:
                r = requests.get(URL, headers=headers, params=params, timeout=90)
            except requests.RequestException:
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(5 * (attempt + 1))
                continue
            r.raise_for_status()
            break
        else:
            raise SystemExit(f"gave up on {asof} {symbols[0]}..")
        body = r.json()
        for sym, bars in (body.get("bars") or {}).items():
            for b in bars:
                yield sym, b["t"][:10], b["o"], b["h"], b["l"], b["c"], b["v"]
        token = body.get("next_page_token")
        time.sleep(0.32)
        if not token:
            return


def main() -> None:
    reg = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    e = env(sys.argv[2])
    headers = {"APCA-API-KEY-ID": e["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": e["ALPACA_API_SECRET"]}
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    for quarter in sorted({r["quarter"] for r in reg}):
        done = out / f"{quarter}.csv.gz"
        if done.exists():
            continue
        mine = [r for r in reg if r["quarter"] == quarter]
        rows, seen, tmp = 0, set(), out / f"{quarter}.part"
        with gzip.open(tmp, "wt", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["cik", "date", "open", "high", "low", "close", "volume"])
            for asof in sorted({r["asof"] for r in mine}):
                cik = {r["ticker"]: r["cik"] for r in mine if r["asof"] == asof}
                syms = sorted(cik)
                for i in range(0, len(syms), 100):
                    for sym, *rest in fetch(syms[i : i + 100], asof, headers):
                        w.writerow([cik[sym], *rest])
                        rows += 1
                        seen.add(cik[sym])
        tmp.rename(done)
        print(quarter, "companies", len(mine), "with bars", len(seen), "rows", rows, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
```

### `exp041_earnings.py`

```python
"""EXP-041 stage 3: when each registry company released earnings, from SEC EDGAR.

For every CIK, reads data.sec.gov's filing index and keeps each form 8-K that carries item 2.02
("Results of Operations and Financial Condition") filed from 2016-11-01: its acceptance time (UTC).
Appends to the output and to a done-list, so a re-run resumes. No price is read.

  python -I exp041_earnings.py <registry.csv> <earnings.csv> <done.txt>
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import requests

BASE = "https://data.sec.gov/submissions/"
HEADERS = {"User-Agent": "trading-agents-research/1.0", "Accept-Encoding": "gzip, deflate"}
FIRST = "2016-11-01"


def get(name: str) -> dict | None:
    for attempt in range(6):
        try:
            r = requests.get(BASE + name, headers=HEADERS, timeout=60)
        except requests.RequestException:
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code == 404:
            return None
        if r.status_code in (403, 429, 500, 502, 503, 504):
            time.sleep(20 * (attempt + 1))
            continue
        r.raise_for_status()
        time.sleep(0.15)
        return r.json()
    raise SystemExit(f"gave up on {name}")


def releases(block: dict) -> list[tuple[str, str, str]]:
    out = []
    for form, items, accepted, filed, acc in zip(block["form"], block["items"], block["acceptanceDateTime"],
                                                 block["filingDate"], block["accessionNumber"]):
        if form == "8-K" and "2.02" in items.split(",") and filed >= FIRST:
            out.append((accepted, filed, acc))
    return out


def main() -> None:
    reg = [int(r["cik"]) for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))]
    out, done_path = Path(sys.argv[2]), Path(sys.argv[3])
    done = set(done_path.read_text().split()) if done_path.exists() else set()
    new = not out.exists()
    with out.open("a", newline="", encoding="utf-8") as fh, done_path.open("a", encoding="utf-8") as dh:
        w = csv.writer(fh)
        if new:
            w.writerow(["cik", "accepted", "filed", "accession"])
        missing = rows = 0
        for n, cik in enumerate(reg, start=1):
            if str(cik) in done:
                continue
            top = get(f"CIK{cik:010d}.json")
            if top is None:
                missing += 1
            else:
                found = releases(top["filings"]["recent"])
                for older in top["filings"].get("files", []):
                    if older["filingTo"] >= FIRST:
                        block = get(older["name"])
                        if block:
                            found += releases(block)
                for accepted, filed, acc in sorted(set(found)):
                    w.writerow([cik, accepted, filed, acc])
                rows += len(found)
            dh.write(f"{cik}\n")
            if n % 250 == 0:
                fh.flush()
                dh.flush()
                print(n, "of", len(reg), "rows this run", rows, "not on EDGAR", missing, flush=True)
    print("done; rows this run", rows, "not on EDGAR", missing, flush=True)


if __name__ == "__main__":
    main()
```
