# EXP-027 — Do insiders' open-market purchases predict the next month's return? (the screen, 2017–2021)

**Status:** DESIGN FIXED 2026-10-24 (planner), before any outcome is computed: sections 1–5 and
Appendix P. This is the **screen** on 2017–2021; the confirmation on 2022–2026 is a separate
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

*Pending.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

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

*Pending.*

## Appendix S — Scripts

*Pending.*
