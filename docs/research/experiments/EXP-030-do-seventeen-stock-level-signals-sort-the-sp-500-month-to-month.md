# EXP-030 — Do seventeen stock-level signals, plausible and strange, sort the S&P 500 month to month?

**Status:** PRE-REGISTERED 2026-10-24 (planner). Sections 1–5 and Appendix P are fixed before any return
is computed.
**Decision / origin:** [R012](../idea-testing-foundation/INDEX.md) batch 3 · [DL-319](../../design-log.md)
· the operator, 2026-10-24: *"Let's test every idea (no matter how strange)"* · **Cost:** $0.

## 1. Why we needed this experiment

R012's third batch: signals about single stocks that the project has not tested, from the published
(closeness to the 52-week high, lottery stocks, low volatility, momentum, same-month seasonality,
volume shocks, media attention, nominal price, round-number prices) to the strange (a ticker that is a
common English word, alphabetical order, ticker length, "sin" industries). One month's holding keeps
turnover, and so cost, low.

## 2. Hypothesis

**The statistic.** Each month-end, S&P 500 members are sorted by the signal; the next month's
equal-weighted return of the top quintile minus the bottom (continuous signals), or of the signal group
minus the rest (binary signals), with the predicted sign of Appendix P. Monthly series; t-statistic with
Newey–West (2 lags); p-values from the normal.

**Discovery** (formations 2017-01 → 2021-06, 54 months): Benjamini–Hochberg at q = 10 % over the 17
two-sided p-values. **Confirmation** (formations 2021-07 → 2026-07, 61 months): one-sided in the
discovery's direction, Holm at 5 % across the passers. **Economic bar** for a confirmed idea: the
favourable group held long-only, rebalanced monthly, 25 bps a side on its turnover, beats the
equal-weighted universe on the confirmation months: mean net monthly excess above 0 with t above 1.65.

## 3. Data

The S235 cache (bars with volume, membership, sectors, benchmark; 2016-01-04 → 2026-09-25; checksums
as EXP-022 §3); the Benzinga archive (EXP-024) for headline counts; a list of the 9,894 most common
English words (`first20hours/google-10000-english`, no-swears version, fetched 2026-10-24) for ticker
fluency. Adjustment-error crossings are masked as in EXP-025.

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; no repo code; no randomness; $0.

## 5. How it was conducted

1. Month-ends are the cache's last session of each month. A stock is in the month's universe if it is
   a member at the formation close and has that close; its holding return runs from that close to the
   next month-end close (or its last close if its bars end, as in EXP-025).
2. Signals by Appendix P, from data up to the formation close only.
3. Quintiles by signal each month (binary signals: the group against the rest), equal weights.
4. Discovery, confirmation and the economic bar as section 2 fixes.
5. **Reported, not barred:** each idea's mean monthly spread in both periods, the group sizes, and
   the long-only group's mean excess over the universe.

**What this cannot claim.** Ten years and one index: power is modest (a monthly spread of about
0.8 % is needed to pass at 54 months). Momentum, trend and short-term reversal overlap rules EXP-023
already read at 10 sessions on the scanner's survivors.

## 6. Results

*Pending.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

## Appendix P — Pre-registration (frozen)

| # | Idea (source) | Signal at the formation close | Spread | Predicted |
| --- | --- | --- | --- | --- |
| X1 | 52-week high (George and Hwang 2004) | close ÷ the highest close of the last 252 sessions | Q5 − Q1 | + |
| X2 | Lottery stocks, MAX (Bali, Cakici and Whitelaw 2011) | the highest daily return of the last 21 sessions | Q5 − Q1 | − |
| X3 | Low volatility (Ang et al. 2006) | the standard deviation of the last 21 daily returns | Q5 − Q1 | − |
| X4 | Short-term reversal (Jegadeesh 1990) | the last 21 sessions' return | Q5 − Q1 | − |
| X5 | Momentum (Jegadeesh and Titman 1993) | return from 252 to 21 sessions ago | Q5 − Q1 | + |
| X6 | Same-month seasonality (Heston and Sadka 2008) | the stock's mean return in the coming calendar month in earlier years (at least one) | Q5 − Q1 | + |
| X7 | Round numbers (Bhattacharya, Holden and Jacobsen 2012) | among stocks within 2 % of a multiple of $10: just below it | below − above | + |
| X8 | Ticker fluency (Head, Smith and Watson 2009) | the ticker (letters only, 3 or more) is a common English word | group − rest | + |
| X9 | Alphabetical order | the ticker starts A–M | group − rest | ± |
| X10 | Ticker length | 1 or 2 letters | group − rest | ± |
| X11 | Sin stocks (Hong and Kacperczyk 2009) | MO, PM, STZ, BF.B, TAP, WYNN, LVS, MGM, CZR, PENN | group − rest | + |
| X12 | Media attention (Fang and Peress 2009) | Benzinga headlines naming the stock in the last 21 sessions | Q5 − Q1 | − |
| X13 | Recent index addition | its membership began within the last 63 sessions | group − rest | ± |
| X14 | Nominal price (Birru and Wang 2016) | the close in dollars | Q5 − Q1 | + |
| X15 | Volume shock (Gervais, Kaniel and Mingelgrin 2001) | mean volume of the last 5 sessions ÷ the last 63 | Q5 − Q1 | + |
| X16 | Beta | beta on SPY over the last 252 sessions | Q5 − Q1 | ± |
| X17 | Trend | close ÷ its 200-session average | Q5 − Q1 | + |

Discovery Benjamini–Hochberg q = 10 % over 17; confirmation Holm 5 % one-sided; economic: favourable
group long-only, net of 25 bps a side, mean monthly excess over the equal-weighted universe with
t > 1.65 on the confirmation months.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

*Pending.*
