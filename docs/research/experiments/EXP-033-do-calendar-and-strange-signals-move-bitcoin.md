# EXP-033 — Do calendar and strange signals move Bitcoin?

**Status:** PRE-REGISTERED 2026-10-24 (planner). Sections 1–5 and Appendix P are fixed before any return
is computed.
**Decision / origin:** [R012](../idea-testing-foundation/INDEX.md) batch 5 · [DL-319](../../design-log.md)
· the operator, 2026-10-24: *"Let's test every idea"* · **Cost:** $0.

## 1. Why we needed this experiment

Crypto is younger, trades every day of the year and is more retail-driven than US stocks: if calendar or
mood effects live anywhere, they should live there. Batch 1's signals that fit a 24/7 market are tested
on BTC, which Alpaca trades.

## 2. Hypothesis

**The statistic.** *b*: the difference in BTC's mean daily return (Coinbase BTC-USD, UTC days) between
signal days and comparison days, OLS on a dummy with Newey–West (5 lags), as EXP-029.

**Discovery** 2015-07-21 → 2020-12-31: Benjamini–Hochberg at 10 % over the seven. **Confirmation**
2021-01-01 → 2026-10-23: one-sided in the discovery's direction, Holm at 5 %. **Economic bar:** holding
BTC on favourable days only (or stepping aside on unfavourable ones), 25 bps a side, beats holding BTC on
Sharpe over the confirmation period.

## 3. Data

EXP-026's kit: `BTC-USD.csv` (4,115 complete days, 2015-07-20 → 2026-10-24; the incomplete last day
dropped). ETH is not tested here (EXP-026 found it gappy).

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; Meeus's moon phases as EXP-029; no repo code; $0.

## 5. How it was conducted

Signals by Appendix P on UTC dates; the funnel and the economic bar as section 2. **Reported, not
barred:** each idea's *b* in both periods and its day counts.

**What this cannot claim.** One exchange, one coin, eleven years; crypto's regime changed with the
arrival of spot ETFs in 2024.

## 6. Results

*Pending.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

## Appendix P — Pre-registration (frozen)

| # | Idea | Signal days | Comparison | Predicted |
| --- | --- | --- | --- | --- |
| K1 | Weekend | Saturday and Sunday (UTC) | weekdays | ± |
| K2 | Monday | Monday | other days | ± |
| K3 | Turn of the month | the last day of a month and the first three of the next | other days | + |
| K4 | The Moon | within 3 days of a new moon | within 3 days of a full moon | + |
| K5 | Halloween | November → April | May → October | + |
| K6 | After a crash day | the previous day's return ≤ −5 % | other days | ± |
| K7 | After a surge day | the previous day's return ≥ +5 % | other days | ± |

Discovery BH 10 % over 7; confirmation Holm 5 % one-sided; economic at 25 bps a side against BTC held,
by Sharpe.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

*Pending.*
