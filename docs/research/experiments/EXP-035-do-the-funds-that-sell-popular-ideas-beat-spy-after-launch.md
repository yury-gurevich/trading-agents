# EXP-035 — Do the funds that sell popular ideas beat SPY after they launched?

**Status:** PRE-REGISTERED 2026-10-24 (planner). Sections 1–5 and Appendix P are fixed before any return
is computed.
**Decision / origin:** [R012](../idea-testing-foundation/INDEX.md) batches 4 and 5 · [DL-319](../../design-log.md)
· the operator, 2026-10-24: *"what do people know that we do not … Let's test every idea"* · **Cost:** $0.

## 1. Why we needed this experiment

Many ideas the project has not tested itself are sold as funds: copying hedge funds' 13F filings,
copying members of Congress, social-media sentiment, disruptive innovation, the IBD 50 growth list, new
issues, factor tilts, covered calls, trend following and tail-risk hedges. A fund's record after its
launch is the idea's out-of-sample record with real costs paid: its sponsor could not see those days.

## 2. Hypothesis

As [EXP-026](EXP-026-do-published-strategies-outside-stock-picking-still-work-after-publication.md):
`dSharpe` = the fund's Sharpe minus SPY's on the same sessions (daily returns over BIL); a stationary
block bootstrap (mean block 20, 5,000 resamples, seed 0), Bonferroni over 20: the 0.125th and
99.875th percentiles. **EDGE**: lower bound above 0, both halves above 0, CAGR at least SPY's.
**DEFENCE**: not EDGE; maximum drawdown at most 0.6 × SPY's, CAGR at least SPY's minus 3 points, and
`dSharpe` at least 0. **REJECT**: neither.

## 3. Data

Tiingo adjusted closes (distributions reinvested; fund fees already deducted) for the 20 funds, SPY and
BIL, to 2026-10-23 (kit `exp035-2026-10-24/inputs/`).

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; no repo code; $0.

## 5. How it was conducted

Each fund from the first session of the month after its launch (Appendix P) to its last session (KRUZ
closed 2025-03-20); SPY over the same sessions; the statistic, interval and verdict as section 2.
**Reported, not barred:** CAGR, volatility, maximum drawdown, the worst month, each year.

**What this cannot claim.** A fund is one implementation of its idea, with its fees; the windows differ
(from 2003 to 2023), and most fall in a strong decade for US large caps.

## 6. Results

*Pending.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

## Appendix P — Pre-registration (frozen)

| Fund | The idea it sells | Scored from |
| --- | --- | --- |
| GURU | copy hedge funds' top 13F holdings | 2012-07 |
| NANC | copy Democratic members of Congress's trades | 2023-03 |
| KRUZ | copy Republican members of Congress's trades | 2023-03 (closed 2025-03-20) |
| BUZZ | stocks with the most positive social-media sentiment | 2021-04 |
| ARKK | disruptive innovation, active | 2014-11 |
| FFTY | the IBD 50 (CAN SLIM growth) | 2015-05 |
| IPO | recent initial public offerings | 2013-11 |
| MTUM | momentum | 2013-05 |
| QUAL | quality | 2013-08 |
| USMV | minimum volatility | 2011-11 |
| VLUE | value | 2013-05 |
| RSP | the S&P 500 equally weighted | 2003-05 |
| MOAT | wide economic moats | 2012-05 |
| NOBL | dividend aristocrats | 2013-11 |
| COWZ | free-cash-flow yield | 2017-01 |
| JEPI | equity income with covered calls | 2020-06 |
| PTLC | trend following on US large caps (launched 2015-06-11) | 2015-07 |
| TAIL | tail-risk hedge (puts and Treasuries) | 2017-07 |
| SWAN | Treasuries plus long calls | 2018-12 |
| QYLD | Nasdaq-100 covered calls | 2014-01 |

Benchmark SPY; Bonferroni over 20; EDGE / DEFENCE / REJECT as section 2.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

*Pending.*
