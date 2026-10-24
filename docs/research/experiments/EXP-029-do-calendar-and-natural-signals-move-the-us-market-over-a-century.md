# EXP-029 — Do calendar, political, natural and superstitious signals move the US market, over a century?

**Status:** PRE-REGISTERED 2026-10-24 (planner, `2f3bd35f`) · **COMPLETE 2026-10-24: nine of 28 pass
discovery, one confirms (the January small-cap effect, +13.7 bps a day, t 3.6), none is economic (an ETF
tilt earns nothing); every strange idea fails at the first stage.**
**Decision / origin:** [R012](../idea-testing-foundation/INDEX.md) batch 1 · [DL-319](../../design-log.md)
· the operator, 2026-10-24: *"Let's test every idea (no matter how strange it may sound at first
glance)"* · **Cost:** $0 (Ken French, NOAA and GFZ public data).

## 1. Why we needed this experiment

The operator asked for every idea to be tested, strange ones included, on a theoretical footing. R012
sets the funnel. This is its first batch: 28 signals that need no forecast (dates, the Moon, the weather
in New York, the Sun's activity, politics, superstition, the market's own last few days), each with a
published or folk claim about its direction. A century of daily returns gives them more power than any
other test in this project, and a split at 1990 leaves 36 years none of them has touched here.

## 2. Hypothesis

**The statistic.** For each idea, *b*: the difference in the mean daily excess return of the US market
(Ken French's `Mkt-RF`) between its signal days and its comparison days (Appendix P), estimated by OLS
with Newey–West standard errors (5 lags); for C6 the return is the smallest size decile minus the
largest.

**Discovery (1926-07-01 → 1989-12-29, or from the idea's first data).** Two-sided p-values; the
Benjamini–Hochberg procedure at **q = 10 %** across all 28 decides which pass.

**Confirmation (1990-01-02 → the data's end).** Each discovery pass is re-tested with the same rule,
one-sided in the discovery's direction, **Holm at 5 %** across the passers.

**The economic bar** for a confirmed idea, on the confirmation period: a trade on the market (hold it
only on favourable days, or step aside only on unfavourable ones, whichever the sign gives) must have a
higher Sharpe than holding the market, at 1 bp a side (a closing-auction order on SPY), and its CAGR is
reported at 1 and 5 bps. Same-day weather ideas are mechanism tests and are not traded.

**The verdict per idea:** FAILS DISCOVERY, FAILS CONFIRMATION, CONFIRMED (not economic) or CONFIRMED
AND ECONOMIC.

## 3. Data

| Input | Span | Where |
| --- | --- | --- |
| Ken French `F-F_Research_Data_Factors_daily` (Mkt-RF, RF) | 1926-07-01 → 2026-08-31, 26,317 days | kit `inputs/` |
| Ken French `Portfolios_Formed_on_ME_daily`, value-weighted deciles | same | kit |
| NOAA GHCN-Daily, New York Central Park `USW00094728`: TMAX, PRCP, SNOW from 1869; TSUN (sunshine minutes) 1965-01 → 2021-10 | | kit `inputs/nyc_central_park.csv.gz` |
| GFZ Potsdam Kp/ap/Ap and sunspot number, daily | 1932-01-01 → 2026-10-23 | kit `inputs/kp_ap_since_1932.txt` |
| Moon phases | computed (Meeus, *Astronomical Algorithms*, ch. 49, main terms; error under an hour) | the script |

The kit is OneDrive `trading-agents-data/exp029-2026-10-24/`. **Known defects:** early CRSP index
returns carry stale prices (a known source of day-of-week artefacts before the 1960s); Saturday
sessions until 1952; TSUN ends 2021-10; the US daylight-saving rule is uniform only from 1967.

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy 2.5.3, pandas 3.0.6; no repo code; no randomness; $0.

## 5. How it was conducted

1. Daily returns in decimals; `Mkt-RF` for every idea but C6.
2. Each idea's signal and comparison days by Appendix P; ideas whose data start late discover from
   their first year.
3. OLS of the return on a signal dummy over signal ∪ comparison days, Newey–West (5 lags): *b*, its
   t-statistic, the two-sided p-value (normal).
4. Benjamini–Hochberg at 10 % over the 28 discovery p-values; for the passers, the confirmation's
   one-sided p-values and Holm at 5 %.
5. The economic bar for each confirmed tradable idea.
6. **Reported, not barred:** every idea's *b* in both periods, its signal-day count, and the
   annualised value of the effect (*b* × signal days a year).

**What this cannot claim, stated before the result.** A pass is a statistical regularity on one
market's index; a fail on a same-day weather idea says nothing about a forecast-based trade. Most of
these signals were published from data before 1990, so the confirmation is also a post-publication
test.

## 6. Results

All MEASURED from the frozen script (Appendix R). *b* is signal days minus comparison days, in basis
points of the market's daily excess return (C6: smallest size decile minus largest).

| # | Idea | Predicted | Discovery *b* (t), signal days | Confirmation 1990 → *b* (t), signal days | Verdict |
| --- | --- | --- | --- | --- | --- |
| C1 | Monday | − | **−24.18 (−10.99)**, 3,097 | −1.33 (−0.41), 1,741 | fails confirmation |
| C2 | Friday | + | **+6.48 (3.49)**, 3,184 | −1.20 (−0.43), 1,847 | fails confirmation |
| C3 | Pre-holiday | + | **+31.17 (8.44)**, 629 | +7.78 (1.54), 327; p 0.061 | fails confirmation |
| C4 | Turn of the month | + | **+15.59 (7.69)**, 3,048 | +5.00 (1.72), 1,760; p 0.042 | fails confirmation (Holm) |
| C5 | Halloween | + | +2.57 (1.48), 8,423 | +2.99 (1.35), 4,536 | fails discovery |
| C6 | **January, small caps** | + | **+33.73 (9.48)**, 1,447 | **+13.70 (3.58)**, 758; p 0.0002 | **CONFIRMED** |
| C7 | Santa Claus rally | + | **+23.04 (5.12)**, 446 | +8.72 (1.48), 254; p 0.070 | fails confirmation |
| C8 | Option-expiry week | ± | −1.49 (−0.45), 988 | +0.29 (0.11), 2,161 | fails discovery |
| C9 | Quarter-end day | ± | +8.65 (1.58), 254 | +3.81 (0.47), 146 | fails discovery |
| C10 | First day of the year | + | +3.07 (0.22), 64 | +12.45 (0.58), 37 | fails discovery |
| C11 | First half of the month | + | **+6.35 (3.72)**, 8,388 | +1.64 (0.72), 4,571 | fails confirmation |
| P1 | Pre-election year | + | +2.34 (1.24), 4,341 | +3.91 (1.65), 2,266 | fails discovery |
| P2 | Democratic president | + | +2.94 (1.70), 8,799 | +3.26 (1.46), 5,041 | fails discovery |
| P3 | Midterm year | − | −1.25 (−0.60), 4,186 | −4.82 (−1.88), 2,432 | fails discovery |
| N1 | New moon against full moon | + | +0.95 (0.40), 4,064 | +1.80 (0.53), 2,193 | fails discovery |
| N2 | Sunshine in New York (1965 →) | + | +2.28 (0.43), 1,095 | +1.45 (0.30), 397 | fails discovery |
| N3 | Rain in New York | − | −3.32 (−1.65), 3,604 | +1.76 (0.59), 2,048 | fails discovery |
| N4 | Snow in New York | ± | −2.35 (−0.66), 684 | −0.85 (−0.13), 271 | fails discovery |
| N5 | Cold | + | −1.38 (−0.73), 3,759 | +4.06 (1.39), 1,718 | fails discovery |
| N6 | Heat | − | +0.38 (0.19), 3,741 | +0.27 (0.10), 2,228 | fails discovery |
| N7 | Geomagnetic storm in the last 6 days | − | −0.66 (−0.33), 3,369 | +0.80 (0.25), 1,230 | fails discovery |
| N8 | Sunspots above median | ± | −1.30 (−0.74), 7,670 | −2.44 (−1.07), 3,610 | fails discovery |
| N9 | Daylight-saving Monday (1967 →) | − | −23.76 (−1.28), 46 | −20.02 (−1.15), 73 | fails discovery |
| N10 | Autumn (seasonal mood) | − | −3.11 (−1.44), 4,308 | +0.61 (0.23), 2,301 | fails discovery |
| S1 | Friday the 13th | − | −13.93 (−1.42), 109 | +31.26 (1.63), 61 | fails discovery |
| M1 | After a −2 % day | + | −16.01 (−1.49), 463 | +20.51 (1.94), 342 | fails discovery |
| M2 | After a +2 % day | − | **+38.95 (3.83)**, 393 | −14.21 (−1.27), 280 | fails confirmation (sign reversed) |
| M3 | After three down days | + | **−9.72 (−3.17)**, 1,945 | +14.82 (3.12), 828 | fails confirmation (sign reversed) |

**Discovery:** nine pass Benjamini–Hochberg at 10 % (C1, C6, C3, C4, C7, M2, C11, C2, M3). **Confirmation:**
one passes Holm at 5 % — **C6, the January small-cap effect**.

**C6's economic bar** could not be applied as registered: its return is the spread between the smallest
and largest size deciles, which no ETF holds. **Post-hoc check, reported, not barred** (kit
`january_etf_check.txt`): holding a small-cap ETF instead of SPY in January, 5 bps a side, earned IWM −
SPY **+0.14 %** a January (t 0.25, positive in 13 of 26 years, 2001–2026) and IWC (micro caps) − SPY
**+0.01 %** (t 0.01, 9 of 21, 2006–2026); the tilt's CAGR was 8.45 % against SPY's 8.60 % and 10.66 %
against 11.04 %.

## 7. Conclusions

1. **None of the strange ideas moves the market, even over 64 years of discovery.** The Moon, New
   York's sunshine, rain, snow and temperature, geomagnetic storms, sunspots, daylight-saving Mondays,
   autumn mood and Friday the 13th all fail at the first stage; so do the presidential cycle, the party
   in office and the midterm year. Each was given exactly the bar the plausible ideas had.
2. **The classic calendar effects were real and mostly faded after 1990.** Monday −24 bps a day before,
   −1.3 after; pre-holiday +31 → +8; turn of the month +16 → +5; Santa Claus +23 → +9; first half of the
   month +6 → +2. Publication, cheaper trading and the end of stale prices in the early index all point
   the same way. The survivors' signs held, but not their size.
3. **The market's short-term memory reversed.** Before 1990 big moves continued the next day; after it
   they reverse (after three down days +14.8 bps, t 3.1; after a −2 % day +20.5 bps). The early index's
   stale prices explain the first; the second is the "buy the dip" pattern of EXP-013 and EXP-025.
   It fails this experiment as registered (the sign reversed), and its regime dependence (opposite in
   the two periods) is a reason not to build on it.
4. **One effect survives, where we cannot trade it.** The January small-cap effect (Keim 1983) still
   holds in the smallest decile (+13.7 bps a day, t 3.6), but it does not reach ETFs: IWM and IWC
   tilts earned nothing in January (t 0.25, 0.01). It lives in micro caps, where spreads take it.
5. **Batch 1 adds nothing to build.** The funnel worked as designed: nine signals that a naive
   one-at-a-time test would have called discoveries, one confirmed, none economic.

## 8. Recommended code changes, and how to implement them

**None.** The next batches follow R012 §3: the cross-section on the S235 cache and the Benzinga
archive, then events and filings, then other markets.

## Appendix P — Pre-registration (frozen)

"Signal" days against "comparison" days; the predicted sign of signal minus comparison in brackets.

| # | Idea (source) | Signal days | Comparison days | Predicted |
| --- | --- | --- | --- | --- |
| C1 | Monday effect (French 1980) | Mondays | all other days | − |
| C2 | Friday effect | Fridays | all other days | + |
| C3 | Pre-holiday (Ariel 1990) | a session whose next session is later than the normal next session (not a plain weekend) | all other days | + |
| C4 | Turn of the month (Ariel 1987; Lakonishok and Smidt 1988) | the last session of a month and the first three of the next | all other days | + |
| C5 | Halloween, sell in May (Bouman and Jacobsen 2002) | November through April | May through October | + |
| C6 | January effect, small caps (Keim 1983) | January sessions, return = smallest decile − largest | other months, same return | + |
| C7 | Santa Claus rally | the last five sessions of December and the first two of January | all other days | + |
| C8 | Option-expiry week (from 1973-04) | Monday to Friday of the week holding the month's third Friday | all other days | ± |
| C9 | Quarter-end window dressing | the last session of March, June, September, December | all other days | ± |
| C10 | First session of the year | it | all other days | + |
| C11 | First half of the month (Ariel 1987) | calendar days 1–15 | days 16–31 | + |
| P1 | Pre-election year (Hirsch) | years ≡ 3 mod 4 | other years | + |
| P2 | Party in office (Santa-Clara and Valkanov 2003) | a Democratic president (inauguration to inauguration) | a Republican president | + |
| P3 | Midterm-year weakness | years ≡ 2 mod 4 | other years | − |
| N1 | The Moon (Dichev and Janes 2003; Yuan, Zheng and Zhu 2006) | within 3 days of a new moon | within 3 days of a full moon | + |
| N2 | Sunshine in New York (Saunders 1993; Hirshleifer and Shumway 2003), from 1965 | TSUN in its calendar month's top quarter | TSUN in its month's bottom quarter | + |
| N3 | Rain in New York | PRCP ≥ 2.5 mm that day | days without | − |
| N4 | Snow in New York | SNOW > 0 that day | days without | ± |
| N5 | Cold (Cao and Wei 2005) | TMAX in its month's bottom 20 % | all other days | + |
| N6 | Heat (Cao and Wei 2005) | TMAX in its month's top 20 % | all other days | − |
| N7 | Geomagnetic storms (Krivelyova and Robotti 2003), from 1932 | a day of Ap ≥ 40 within the previous six calendar days | all other days | − |
| N8 | Sunspots, from 1932 | the day's sunspot number above its 1932–1989 median | below it | ± |
| N9 | Daylight-saving Mondays (Kamstra, Kramer and Levi 2000), from 1967 | the session after a US clock change (rules of 1967, 1974, 1975, 1976, 1987, 2007) | other Mondays | − |
| N10 | Autumn mood, seasonal affective disorder (Kamstra, Kramer and Levi 2003) | 21 September → 20 December | the rest of the year | − |
| S1 | Friday the 13th (Kolb and Rodriguez 1987) | Fridays falling on the 13th | other Fridays | − |
| M1 | After a big down day | the previous session's market return ≤ −2 % | all other days | + |
| M2 | After a big up day | the previous session's return ≥ +2 % | all other days | − |
| M3 | After three down days | the previous three sessions each below 0 | all other days | + |

Discovery: Benjamini–Hochberg q = 10 % over the 28 two-sided p-values. Confirmation: one-sided in the
discovery's direction, Holm 5 % over the passers. Economic: a tradable confirmed idea beats the market's
Sharpe at 1 bp a side over 1990 →. "±": no direction claimed; the discovery's sign is carried forward.

## Appendix R — Run record

- 2026-10-24, planner. Data fetched about 03:20 UTC (Ken French daily factors and size deciles, NOAA
  GHCN Central Park, GFZ Kp/Ap); spans only were read before the pre-registration `2f3bd35f`.
- Pilot (`--pilot`, signal-day counts only): every count matches its calendar arithmetic (turn of
  month 3,048 = 4 × 12 × 63.5; daylight-saving Mondays 46 and 73, two a year). Noted: TSUN after 1990
  reads lower against 1965–1989's thresholds (397 sunny against 875 cloudy days).
- Frozen `exp029.py` SHA-256 `9819b50d9d1efd50b12edec5a0b4e56b25fd94cb8369dc8c6f9353b5a8083bd4`;
  `exp029.json` SHA-256 `0287425bf73cac4da8d572871b5517adb01cddcae26c0c325b0452e44a658bf2`.
- Post-hoc January ETF check (Tiingo IWM, IWC, SPY to 2026-10-23), after the scored run: kit
  `january_etf_check.txt`.

```text
python exp029.py <kit>/inputs <kit>/pilot.json --pilot
python exp029.py <kit>/inputs <kit>/exp029.json
```

## Appendix S — Scripts

### `exp029.py`

```python
"""EXP-029 (DL-319, R012 batch 1): 28 calendar, political, natural and superstitious signals, 1926 →.

Discovery 1926-07 → 1989-12 (Benjamini–Hochberg q = 10 %), confirmation 1990 → (Holm 5 %, one-sided),
then an economic bar. Usage: python exp029.py <inputs_dir> <out.json> [--pilot]
"""

from __future__ import annotations

import gzip
import json
import math
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SPLIT = pd.Timestamp("1990-01-01")
Q_BH, ALPHA_HOLM, LAGS = 0.10, 0.05, 5
DEM = [("1933-03-04", "1953-01-20"), ("1961-01-20", "1969-01-20"), ("1977-01-20", "1981-01-20"),
       ("1993-01-20", "2001-01-20"), ("2009-01-20", "2017-01-20"), ("2021-01-20", "2025-01-20")]
SAME_DAY = {"N2", "N3", "N4", "N5", "N6"}


def french(path: Path, section: int = 0) -> pd.DataFrame:
    text = zipfile.ZipFile(path).read(zipfile.ZipFile(path).namelist()[0]).decode("latin-1").splitlines()
    blocks, cur, header = [], [], None
    for line in text:
        head = line.split(",")[0].strip()
        if head.isdigit() and len(head) == 8:
            cur.append(line)
        else:
            if cur:
                blocks.append((header, cur))
                cur = []
            if line.startswith(",") and line.count(",") > 2:
                header = [c.strip() for c in line.split(",")]
    if cur:
        blocks.append((header, cur))
    hdr, rows = blocks[section]
    df = pd.DataFrame([r.split(",") for r in rows]).iloc[:, : len(hdr)]
    df.columns = ["date"] + hdr[1:]
    df["date"] = pd.to_datetime(df["date"].str.strip(), format="%Y%m%d")
    return df.set_index("date").apply(pd.to_numeric) / 100.0


def moon_phases(k0: int, k1: int, full: bool) -> list[date]:
    out = []
    for k in range(k0, k1):
        kk = k + (0.5 if full else 0.0)
        T = kk / 1236.85
        jde = 2451550.09766 + 29.530588861 * kk + 0.00015437 * T**2 - 0.00000015 * T**3 + 0.00000000073 * T**4
        E = 1 - 0.002516 * T - 0.0000074 * T**2
        r = math.radians
        M = r(2.5534 + 29.1053567 * kk - 0.0000014 * T**2)
        Mp = r(201.5643 + 385.81693528 * kk + 0.0107582 * T**2 + 0.00001238 * T**3)
        F = r(160.7108 + 390.67050284 * kk - 0.0016118 * T**2 - 0.00000227 * T**3)
        if full:
            c = (-0.40614 * math.sin(Mp) + 0.17302 * E * math.sin(M) + 0.01614 * math.sin(2 * Mp) + 0.01043 * math.sin(2 * F)
                 + 0.00734 * E * math.sin(Mp - M) - 0.00515 * E * math.sin(Mp + M) + 0.00209 * E * E * math.sin(2 * M)
                 - 0.00111 * math.sin(Mp - 2 * F) - 0.00057 * math.sin(Mp + 2 * F) + 0.00056 * E * math.sin(2 * Mp + M)
                 - 0.00042 * math.sin(3 * Mp))
        else:
            c = (-0.40720 * math.sin(Mp) + 0.17241 * E * math.sin(M) + 0.01608 * math.sin(2 * Mp) + 0.01039 * math.sin(2 * F)
                 + 0.00739 * E * math.sin(Mp - M) - 0.00514 * E * math.sin(Mp + M) + 0.00208 * E * E * math.sin(2 * M)
                 - 0.00111 * math.sin(Mp - 2 * F) - 0.00057 * math.sin(Mp + 2 * F) + 0.00056 * E * math.sin(2 * Mp + M)
                 - 0.00042 * math.sin(3 * Mp))
        jd = jde + c
        out.append((pd.Timestamp("1970-01-01") + pd.to_timedelta(jd - 2440587.5, unit="D")).date())
    return out


def nth_sunday(y: int, m: int, n: int) -> date:
    d = date(y, m, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def last_sunday(y: int, m: int) -> date:
    d = date(y + (m == 12), (m % 12) + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() + 1) % 7)


def dst_changes() -> list[date]:
    out = []
    for y in range(1967, 2027):
        if y <= 1973 or 1976 <= y <= 1986:
            out += [last_sunday(y, 4), last_sunday(y, 10)]
        elif y == 1974:
            out += [date(1974, 1, 6), last_sunday(1974, 10)]
        elif y == 1975:
            out += [date(1975, 2, 23), last_sunday(1975, 10)]
        elif y <= 2006:
            out += [nth_sunday(y, 4, 1), last_sunday(y, 10)]
        else:
            out += [nth_sunday(y, 3, 2), nth_sunday(y, 11, 1)]
    return out


def nw_test(y: np.ndarray, x: np.ndarray):
    X = np.column_stack([np.ones_like(x), x])
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    e = y - X @ beta
    u = X * e[:, None]
    S = u.T @ u
    for lag in range(1, LAGS + 1):
        w = 1 - lag / (LAGS + 1)
        G = u[lag:].T @ u[:-lag]
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv
    b, se = beta[1], math.sqrt(V[1, 1])
    t = b / se
    return float(b), float(t)


def p_two(t: float) -> float:
    return math.erfc(abs(t) / math.sqrt(2))


def p_one(t: float, sign: float) -> float:
    return 0.5 * math.erfc((t * sign) / math.sqrt(2))


def main() -> None:
    inp, out = Path(sys.argv[1]), Path(sys.argv[2])
    pilot = "--pilot" in sys.argv
    ff = french(inp / "F-F_Research_Data_Factors_daily_CSV.zip")
    me = french(inp / "Portfolios_Formed_on_ME_daily_CSV.zip", 0)
    cal = ff.index
    df = pd.DataFrame(index=cal)
    df["ex"] = ff["Mkt-RF"]
    df["rf"] = ff["RF"]
    df["mkt"] = df["ex"] + df["rf"]
    df["smb10"] = me["Lo 10"].reindex(cal) - me["Hi 10"].reindex(cal)
    d = pd.Series(cal, index=cal)
    wd, mon, yr, dom = d.dt.weekday, d.dt.month, d.dt.year, d.dt.day
    nxt_gap = (d.shift(-1) - d).dt.days
    normal = np.where(wd == 4, 3, np.where(wd == 5, 2, 1))
    month_id = yr * 12 + mon
    last_of_month = month_id != month_id.shift(-1)
    pos_in_month = d.groupby(month_id).cumcount()
    last_of_year = yr != yr.shift(-1)
    first_of_year = yr != yr.shift(1)
    rank_from_end_year = d.groupby(yr).cumcount(ascending=False)
    third_fri = {(y, m): nth_sunday(y, m, 1) - timedelta(days=2) + timedelta(weeks=3) if nth_sunday(y, m, 1).day > 2 else None
                 for y in range(1926, 2027) for m in range(1, 13)}
    # third Friday: first Friday of the month + 14 days
    def third_friday(y, m):
        f = date(y, m, 1) + timedelta(days=(4 - date(y, m, 1).weekday()) % 7)
        return f + timedelta(days=14)
    tf = d.map(lambda x: third_friday(x.year, x.month))
    week_of = d.dt.date.map(lambda x: x - timedelta(days=x.weekday()))
    exp_week = (week_of == tf.map(lambda x: x - timedelta(days=x.weekday()))) & (d >= pd.Timestamp("1973-04-26"))
    dem = pd.Series(False, index=cal)
    for a, b in DEM:
        dem |= (cal >= a) & (cal < b)
    news = np.array(moon_phases(-950, 340, False), dtype="datetime64[D]")
    fulls = np.array(moon_phases(-950, 340, True), dtype="datetime64[D]")
    dd = cal.values.astype("datetime64[D]")

    def near(events):
        i = np.searchsorted(events, dd)
        lo = np.abs((dd - events[np.clip(i - 1, 0, len(events) - 1)]).astype(int))
        hi = np.abs((events[np.clip(i, 0, len(events) - 1)] - dd).astype(int))
        return np.minimum(lo, hi)

    new_w, full_w = near(news) <= 3, near(fulls) <= 3
    # weather
    g = pd.read_csv(inp / "nyc_central_park.csv.gz", header=None, usecols=[1, 2, 3, 5], names=["date", "el", "val", "q"],
                    dtype={"date": str, "el": str, "val": float, "q": str})
    g = g[g["q"].isna()]
    w = g.pivot_table(index="date", columns="el", values="val", aggfunc="first")
    w.index = pd.to_datetime(w.index, format="%Y%m%d")
    w = w.reindex(cal)
    disc = cal < SPLIT

    def month_q(series, q):
        ref = series[disc].groupby(series[disc].index.month).quantile(q)
        return series.index.month.map(ref)

    tsun = w.get("TSUN")
    tsun_ok = tsun.notna()
    tsun_disc = tsun.where(cal < SPLIT)
    ref_hi = tsun_disc.groupby(cal.month).quantile(0.75)
    ref_lo = tsun_disc.groupby(cal.month).quantile(0.25)
    sunny = tsun >= cal.month.map(ref_hi)
    cloudy = tsun <= cal.month.map(ref_lo)
    tmax = w["TMAX"]
    cold = tmax <= month_q(tmax, 0.2)
    hot = tmax >= month_q(tmax, 0.8)
    # geomagnetic and sunspots
    kp = []
    for line in open(inp / "kp_ap_since_1932.txt"):
        if line.startswith("#") or not line.strip():
            continue
        p = line.split()
        kp.append((date(int(p[0]), int(p[1]), int(p[2])), float(p[23]), float(p[24])))
    kp = pd.DataFrame(kp, columns=["date", "Ap", "SN"]).set_index("date")
    kp.index = pd.to_datetime(kp.index)
    kp = kp.where(kp >= 0)
    ap = kp["Ap"].asfreq("D")
    storm_prev6 = (ap >= 40).astype(float).rolling(6).max().shift(1).reindex(cal)
    sn = kp["SN"].reindex(cal)
    sn_med = kp["SN"][(kp.index >= "1932-01-01") & (kp.index < SPLIT)].median()
    dst = set(dst_changes())
    dst_mon = d.map(lambda x: (x.date() - timedelta(days=1)) in dst or (x.date() - timedelta(days=2)) in dst and x.weekday() == 1 and False)
    after_sunday = d.shift(1)
    dst_session = pd.Series(False, index=cal)
    for ch in dst:
        ts = pd.Timestamp(ch)
        k = cal.searchsorted(ts, side="right")
        if 0 < k < len(cal):
            dst_session.iloc[k] = True
    prev = df["mkt"].shift(1)
    ideas = {
        "C1": (wd == 0, wd != 0, "ex", -1), "C2": (wd == 4, wd != 4, "ex", 1),
        "C3": (nxt_gap > normal, nxt_gap <= normal, "ex", 1),
        "C4": (last_of_month | (pos_in_month <= 2), ~(last_of_month | (pos_in_month <= 2)), "ex", 1),
        "C5": (mon.isin([11, 12, 1, 2, 3, 4]), ~mon.isin([11, 12, 1, 2, 3, 4]), "ex", 1),
        "C6": (mon == 1, mon != 1, "smb10", 1),
        "C7": (((mon == 12) & (rank_from_end_year <= 4)) | ((mon == 1) & (d.groupby(yr).cumcount() <= 1)),
               ~(((mon == 12) & (rank_from_end_year <= 4)) | ((mon == 1) & (d.groupby(yr).cumcount() <= 1))), "ex", 1),
        "C8": (exp_week, (~exp_week) & (d >= pd.Timestamp("1973-04-26")), "ex", 0),
        "C9": (last_of_month & mon.isin([3, 6, 9, 12]), ~(last_of_month & mon.isin([3, 6, 9, 12])), "ex", 0),
        "C10": (first_of_year, ~first_of_year, "ex", 1),
        "C11": (dom <= 15, dom > 15, "ex", 1),
        "P1": (yr % 4 == 3, yr % 4 != 3, "ex", 1), "P2": (dem, ~dem, "ex", 1), "P3": (yr % 4 == 2, yr % 4 != 2, "ex", -1),
        "N1": (pd.Series(new_w, index=cal), pd.Series(full_w, index=cal), "ex", 1),
        "N2": (sunny & tsun_ok, cloudy & tsun_ok, "ex", 1),
        "N3": (w["PRCP"] >= 25, w["PRCP"] < 25, "ex", -1), "N4": (w["SNOW"] > 0, w["SNOW"] == 0, "ex", 0),
        "N5": (cold & tmax.notna(), (~cold) & tmax.notna(), "ex", 1), "N6": (hot & tmax.notna(), (~hot) & tmax.notna(), "ex", -1),
        "N7": (storm_prev6 == 1, storm_prev6 == 0, "ex", -1),
        "N8": (sn > sn_med, sn <= sn_med, "ex", 0),
        "N9": (dst_session & (wd == 0), (~dst_session) & (wd == 0) & (d >= pd.Timestamp("1967-01-01")), "ex", -1),
        "N10": (((mon == 9) & (dom >= 21)) | mon.isin([10, 11]) | ((mon == 12) & (dom <= 20)),
                ~(((mon == 9) & (dom >= 21)) | mon.isin([10, 11]) | ((mon == 12) & (dom <= 20))), "ex", -1),
        "S1": ((wd == 4) & (dom == 13), (wd == 4) & (dom != 13), "ex", -1),
        "M1": (prev <= -0.02, prev > -0.02, "ex", 1), "M2": (prev >= 0.02, prev < 0.02, "ex", -1),
        "M3": ((prev < 0) & (prev.shift(1) < 0) & (prev.shift(2) < 0), ~((prev < 0) & (prev.shift(1) < 0) & (prev.shift(2) < 0)) & prev.shift(2).notna(), "ex", 1),
    }
    res = {}
    for k, (sig, cmp_, col, pred) in ideas.items():
        sig = pd.Series(sig, index=cal).fillna(False).astype(bool)
        cmp_ = pd.Series(cmp_, index=cal).fillna(False).astype(bool) & ~sig
        y = df[col]
        row = {"predicted": pred}
        for per, m in (("discovery", cal < SPLIT), ("confirmation", cal >= SPLIT)):
            use = (sig | cmp_) & m & y.notna()
            row[per] = {"signal_days": int((sig & use).sum()), "comparison_days": int((cmp_ & use).sum()),
                        "from": str(cal[use][0].date()) if use.any() else None}
            if not pilot and use.sum() > 50 and (sig & use).sum() >= 10:
                b, t = nw_test(y[use].to_numpy(), sig[use].astype(float).to_numpy())
                yrs = use.sum() / 252
                row[per].update({"b_bps": b * 1e4, "t": t, "p_two": p_two(t),
                                 "annual_effect_pct": b * (sig & use).sum() / yrs * 100})
        res[k] = row
    if pilot:
        out.write_text(json.dumps(res, indent=1), encoding="utf-8")
        for k, v in res.items():
            print(k, v["discovery"]["signal_days"], v["discovery"]["comparison_days"], v["discovery"]["from"], "|",
                  v["confirmation"]["signal_days"], v["confirmation"]["comparison_days"])
        return
    # Benjamini–Hochberg on discovery
    keys = [k for k in res if "p_two" in res[k]["discovery"]]
    ps = sorted((res[k]["discovery"]["p_two"], k) for k in keys)
    m = len(ps)
    cut = 0
    for i, (p, k) in enumerate(ps, 1):
        if p <= Q_BH * i / m:
            cut = i
    passed = [k for _, k in ps[:cut]]
    for k in res:
        res[k]["discovery_pass"] = k in passed
    # Holm on confirmation, one-sided in the discovery's direction
    conf = []
    for k in passed:
        sgn = 1.0 if res[k]["discovery"]["b_bps"] > 0 else -1.0
        c = res[k]["confirmation"]
        c["p_one"] = p_one(c["t"], sgn) if "t" in c else 1.0
        conf.append((c["p_one"], k))
    conf.sort()
    holm_ok = set()
    for i, (p, k) in enumerate(conf):
        if p <= ALPHA_HOLM / (len(conf) - i):
            holm_ok.add(k)
        else:
            break
    # economic bar
    for k in res:
        v = "FAILS DISCOVERY"
        if res[k]["discovery_pass"]:
            v = "FAILS CONFIRMATION"
        if k in holm_ok:
            v = "CONFIRMED"
            sig, cmp_, col, _ = ideas[k]
            sig = pd.Series(sig, index=cal).fillna(False).astype(bool)
            cmp_ = pd.Series(cmp_, index=cal).fillna(False).astype(bool) & ~sig
            if k not in SAME_DAY and col == "ex":
                m_ = cal >= SPLIT
                good = res[k]["discovery"]["b_bps"] > 0
                all_others = (sig | cmp_).sum() == len(cal) or (sig | cmp_)[m_].mean() > 0.99
                if good and all_others:
                    inm = sig
                elif good:
                    inm = ~cmp_
                else:
                    inm = ~sig
                econ = {}
                for cost, tag in ((0.0001, "1bp"), (0.0005, "5bps")):
                    pos = inm[m_].astype(float)
                    switch = pos.diff().abs().fillna(0)
                    r = pos * df["mkt"][m_] + (1 - pos) * df["rf"][m_] - switch * cost
                    exr, exm = r - df["rf"][m_], df["ex"][m_]
                    eq = (1 + r).cumprod()
                    yrs = len(r) / 252
                    econ[tag] = {"sharpe": float(exr.mean() / exr.std() * math.sqrt(252)),
                                 "market_sharpe": float(exm.mean() / exm.std() * math.sqrt(252)),
                                 "cagr_pct": float((eq.iloc[-1] ** (1 / yrs) - 1) * 100),
                                 "market_cagr_pct": float(((1 + df["mkt"][m_]).prod() ** (1 / yrs) - 1) * 100),
                                 "time_in_market": float(pos.mean())}
                res[k]["economic"] = econ
                if econ["1bp"]["sharpe"] > econ["1bp"]["market_sharpe"]:
                    v = "CONFIRMED AND ECONOMIC"
            else:
                res[k]["economic"] = "not tradable as measured" if k in SAME_DAY else "spread of size deciles, not an ETF trade"
        res[k]["verdict"] = v
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("BH passers:", passed, "| Holm confirmed:", sorted(holm_ok))


if __name__ == "__main__":
    main()
```
