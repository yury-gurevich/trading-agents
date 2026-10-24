# EXP-029 — Do calendar, political, natural and superstitious signals move the US market, over a century?

**Status:** PRE-REGISTERED 2026-10-24 (planner). Sections 1–5 and Appendix P are fixed before any return
is computed; a change of design after it is a new experiment.
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

*Pending.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

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

*Pending.*

## Appendix S — Scripts

*Pending.*
