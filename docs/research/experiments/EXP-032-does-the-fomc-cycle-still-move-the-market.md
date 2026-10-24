# EXP-032 — Does the FOMC cycle still move the market after its papers' samples?

**Status:** PRE-REGISTERED 2026-10-24 (planner). Sections 1–5 and Appendix P are fixed before any return
is computed.
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

*Pending.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

## Appendix P — Pre-registration (frozen)

| # | Idea (source) | Signal days | Predicted |
| --- | --- | --- | --- |
| F1 | Announcement day (Lucca and Moench 2015) | the session of a scheduled announcement | + |
| F2 | The day before (Lucca and Moench 2015) | the session before it | + |
| F3 | Even weeks of the FOMC cycle (Cieslak, Morse and Vissing-Jorgensen 2019) | sessions −1 … +3, +10 … +14, +20 … +24, +30 … +34 counted from the latest announcement session (session −1 = the one before the next announcement) | + |

Comparison: every other SPY session from 1994-02-04. Discovery BH 10 % over 3; confirmation Holm 5 %
one-sided; economic: SPY on signal days only, 1 bp a side, against SPY held, by Sharpe.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

*Pending.*
