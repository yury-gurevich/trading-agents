<!-- Agent: planning | Role: research — E17.1 measurement spike -->
# E17.1: can we source a survivorship-free S&P 500 universe?

**Date:** 2026-09-25 · **Leg:** P17 (next-leg plan), item E17.1 · **Cost:** $0, ~50 vendor requests ·
**Decision:** [DL-226](../../design-log.md)

**Answer: yes, at 95.3 % of member-days on what we already pay for, and about 99 % once ticker renames
are mapped.** That clears the plan's ~90 % bar, so P17 proceeds on a survivorship-free universe, not the
"replay the survivors and report an upper bound" fallback. Two of the plan's three assumptions were
wrong, in opposite directions: FMP does not sell us membership, and Alpaca's delisted coverage is good.

## What the plan assumed, and what was measured

| Plan assumption | Measured 2026-09-25 |
| --- | --- |
| FMP historical constituents *[assumed available on our plan]* | 🔴 **Not available.** `/api/v3/sp500_constituent` and `/api/v3/historical/sp500_constituent` → **403** ("legacy endpoint, only for subscriptions before 2025-08-31"); `/stable/sp500-constituent` and `/stable/historical-sp500-constituent` → **402** ("not available under your current subscription"). |
| *(not in the plan)* Finnhub | 🔴 `/index/constituents` and `/index/historical-constituents` → **403**. |
| *(not in the plan)* Wikipedia | 🟩 **Usable.** The change log moved on 2026-08-11 from *List of S&P 500 companies* to its own article, *Historical components of the S&P 500* (409 dated rows, 1976 → 2026-09-21). |
| Alpaca delisted coverage *[assumed thin]* | 🟩 **93.4 %** of removed-name member-days (below). |
| Tiingo delisted coverage *[assumed good]* | 🟡 Not needed for the bulk; it also has no bars for the two names Alpaca lacks (STI, TE). |

## Membership: Wikipedia's change log reconciles

Method: start from today's 503-line constituent table and undo each dated change backwards (remove
the name added, restore the name removed), then replay it forwards over every business day from
2016-01-04 to 2026-09-25.

- **244** change rows since 2016 (227 additions, 228 removals), 17–30 a year, the index's normal
  turnover.
- **Member count stays 503–508** in every year back to 2016. The index has 500–505 lines because of
  dual share classes, so the reconstruction drifts by at most ~3 names over ten years.
- **3** records since 2016 fail to reconcile (an added ticker is not in the set when undone): SATS
  (2026), FLT (2018) and RE (2017). All are **renames** the log does not record (FLT → CPAY, RE → EG).
- Result: **725** tickers were ever members; **1,421,814** member-days; **222** tickers not in today's
  list carry **241,288** of them (**17.0 %**). That 17 % is the survivorship bias a survivors-only
  replay would carry.

## Bars: Alpaca SIP daily bars cover the gap

`/v2/stocks/bars`, `feed=sip`, `adjustment=raw`, 2016-01-01 → 2026-09-24, 50 symbols per request.
Only counts were kept; no bars were stored.

| Set | Member-days | With a bar | Coverage |
| --- | --- | --- | --- |
| 222 removed names | 241,288 | 225,293 | **93.4 %** (44 requests) |
| 503 current members | 1,180,526 | 1,129,524 | **95.7 %** |
| **All** | **1,421,814** | **1,354,817** | **95.3 %** |

- **Missing entirely:** STI (SunTrust, merged into Truist 2019), TE (TECO Energy, 2016), and one
  row with no ticker: 2,899 member-days, **0.2 %**. Tiingo has neither.
- **Survivors' shortfall is renames, not missing data:** PSKY (formerly CBS / VIAC / PARA), DOW (the
  2019 spin-off, and the old Dow Chemical before it), VTRS (Mylan), LIN (Praxair), APTV (Delphi).
  Their history sits under the old tickers. A rename map should lift the total to about 99 %
  *[estimated, not measured]*.
- **Identity check:** 15 acquired or taken-private names were checked for bars after the deal date.
  **14 of 15 stop on or within a day of it** (CELG, TWTR, ATVI, XLNX, RHT, TIF, CTXS, VMW, PXD, JNPR,
  HES, ANSS, DFS, SIVB). **MON** (Monsanto, acquired 2018-06) has bars until 2022: the ticker was
  reused. Harmless for a member-day read, but a ticker reused *before* a membership window would
  attach another company's prices, so E17.2 must check it.
- 🪤 **The free plan refuses recent SIP bars:** an `end` of today returned **403**; yesterday worked.

## What E17.2 must build (carried into the plan)

1. **The membership log**, parsed from *Historical components of the S&P 500* plus the current table,
   frozen as a dated snapshot with attribution (Wikipedia text is CC BY-SA 4.0; the facts are what we
   keep). Membership is not licensed data, but it goes to the cache with the bars.
2. **A rename map** (old ticker, new ticker, date) for the chains the log does not record, starting
   with the six above; a reconciliation test that the reconstructed count stays within 500–506.
3. **A ticker-reuse guard:** a symbol's bars are used only inside its own membership window, and a
   window whose bars start long before or run long after the company's known life is flagged.
4. **Bars from Alpaca SIP**, cached in OneDrive as today (the repo is public and SIP bars are
   licensed), with the 0.2 % residue reported as uncovered rather than filled.

**Caveat:** Wikipedia is crowd-edited, not an index-provider feed. The reconciliation (counts within
~3 of the true index over ten years) is the evidence that it is good enough for a replay; it would not
be good enough for anything that trades on the membership itself.
