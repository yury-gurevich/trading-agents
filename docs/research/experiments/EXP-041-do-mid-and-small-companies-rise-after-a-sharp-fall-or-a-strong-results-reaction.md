# EXP-041 — Do mid and small companies rise in the ten sessions after a sharp fall or a strong results reaction?

**Status:** PRE-REGISTERED 2026-11-16 (planner, `ff107361`) · COMPLETE 2026-11-16 · **NONE: no cell passes discovery (smallest p 0.51); after a sharp fall or a strong results reaction a mid or small company's next ten sessions are a coin flip against its peers**
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

All MEASURED, `exp041.json` (SHA-256 `301f18c1d7ae…`), one scored run: 7,092 companies, 3,967 ever in a
bucket, 2,723 sessions.

- **Verdict: NONE. No cell passes discovery.** The smallest of the eight two-sided p-values is 0.51
  (Benjamini–Hochberg needed 0.0125 for the first). Confirmation was therefore not entered; its figures
  are shown for the record.

  | Idea | Bucket | Discovery events | Mean excess | t | p | Median excess | Later events | Mean excess, 2022-02 → | t | Less 50 bps |
  | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
  | D1 sharp fall | MID | 7,750 | +0.18 % | +0.54 | 0.59 | −0.10 % | 8,142 | −0.04 % | −0.14 | −0.54 % |
  | D1 sharp fall | SMALL | 18,912 | −0.04 % | −0.11 | 0.91 | −0.32 % | 20,691 | +0.14 % | +0.35 | −0.36 % |
  | D2 fall, no results | MID | 6,448 | +0.27 % | +0.66 | 0.51 | +0.10 % | 6,686 | +0.41 % | +1.00 | −0.09 % |
  | D2 fall, no results | SMALL | 15,874 | +0.13 % | +0.26 | 0.79 | −0.36 % | 17,491 | +0.33 % | +0.74 | −0.17 % |
  | D3 fall around results | MID | 2,018 | +0.19 % | +0.45 | 0.65 | −0.42 % | 2,096 | +0.18 % | +0.46 | −0.32 % |
  | D3 fall around results | SMALL | 4,834 | +0.13 % | +0.33 | 0.74 | −0.23 % | 5,258 | −0.73 % | −1.97 | −1.23 % |
  | E1 strong results reaction | MID | 1,876 | −0.67 % | −0.64 | 0.52 | +0.06 % | 2,165 | +0.12 % | +0.42 | −0.38 % |
  | E1 strong results reaction | SMALL | 4,313 | −0.04 % | −0.17 | 0.87 | −0.55 % | 4,563 | +0.17 % | +0.49 | −0.33 % |

  No mean excess is larger than its own noise in either period except D3 SMALL after 2022 (−0.73 %,
  t −1.97), which was +0.13 % in discovery. Net of 50 bps every cell is below zero in both periods.

- **The operator's trade shape, both periods together (reported, no bar).** After every kind of event
  the trade is close to a coin flip:

  | Idea | Bucket | Events | Ended up | +5 % touched first | −5 % touched first | Mean raw return | Winsorised mean excess |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | D1 sharp fall | MID | 15,892 | 53 % | 49 % | 46 % | +1.02 % | +0.28 % |
  | D1 sharp fall | SMALL | 39,603 | 51 % | 48 % | 49 % | +0.76 % | −0.10 % |
  | D1 sharp fall | LARGE | 12,719 | 54 % | 49 % | 44 % | +1.16 % | +0.29 % |
  | D2 fall, no results | MID | 13,134 | 54 % | 50 % | 47 % | +1.22 % | +0.44 % |
  | D2 fall, no results | SMALL | 33,365 | 51 % | 49 % | 49 % | +0.86 % | −0.10 % |
  | D2 fall, no results | LARGE | 10,403 | 55 % | 51 % | 45 % | +1.25 % | +0.36 % |
  | D3 fall around results | MID | 4,114 | 51 % | 47 % | 44 % | +0.07 % | −0.06 % |
  | D3 fall around results | SMALL | 10,092 | 50 % | 46 % | 48 % | +0.19 % | +0.02 % |
  | D3 fall around results | LARGE | 3,279 | 52 % | 45 % | 43 % | +0.54 % | +0.04 % |
  | E1 strong results reaction | MID | 4,041 | 52 % | 41 % | 40 % | +0.62 % | +0.17 % |
  | E1 strong results reaction | SMALL | 8,876 | 49 % | 42 % | 46 % | −0.00 % | −0.17 % |
  | E1 strong results reaction | LARGE | 3,586 | 53 % | 40 % | 35 % | +0.66 % | +0.16 % |

- **Is it a smaller-company effect? No** (LARGE, reported; mean excess and t, discovery then later):

  | Idea | Discovery | 2022-02 → |
  | --- | --- | --- |
  | D1 sharp fall | +0.24 % (+0.61) | +0.16 % (+0.46) |
  | D2 fall, no results | +0.38 % (+0.84) | +0.23 % (+0.53) |
  | D3 fall around results | −0.25 % (−0.66) | +0.44 % (+1.29) |
  | E1 strong results reaction | +0.47 % (+1.59) | +0.34 % (+0.91) |

- **Other variants (reported, no bar;** mean excess with t, then the winsorised mean**):**

  | Variant | Cell | Discovery | Winsorised | 2022-02 → | Winsorised |
  | --- | --- | --- | --- | --- | --- |
  | Five-session hold | D1 MID | +3.12 % (+1.01) | +0.27 % | −0.03 % (−0.14) | +0.12 % |
  | Five-session hold | D1 SMALL | +0.16 % (+0.54) | +0.05 % | −0.07 % (−0.28) | −0.00 % |
  | Five-session hold | D2 MID | +4.11 % (+0.98) | +0.34 % | +0.15 % (+0.63) | +0.18 % |
  | Five-session hold | D2 SMALL | +0.13 % (+0.36) | +0.04 % | +0.06 % (+0.21) | −0.00 % |
  | Five-session hold | D3 MID | +0.40 % (+1.67) | +0.07 % | −0.04 % (−0.13) | +0.07 % |
  | Five-session hold | D3 SMALL | +0.09 % (+0.43) | +0.10 % | −0.77 % (−3.29) | +0.04 % |
  | Five-session hold | E1 MID | −0.88 % (−1.12) | −0.09 % | +0.18 % (+0.86) | +0.26 % |
  | Five-session hold | E1 SMALL | +0.20 % (+0.66) | −0.26 % | +0.01 % (+0.06) | −0.15 % |
  | Deeper fall (20 %), ten sessions | D1 MID | +15.35 % (+1.02) | −0.11 % | −0.30 % (−0.47) | +0.32 % |
  | Deeper fall (20 %), ten sessions | D1 SMALL | −1.19 % (−2.45) | −0.26 % | −0.07 % (−0.05) | −0.29 % |
  | Stronger reaction (10 points), ten sessions | E1 MID | −1.87 % (−1.17) | −0.12 % | +0.27 % (+0.64) | +0.37 % |
  | Stronger reaction (10 points), ten sessions | E1 SMALL | +0.21 % (+0.51) | −0.26 % | −0.12 % (−0.29) | −0.26 % |

- **Unexpected: one vendor bad print, found after the run** (`exp041_outlier.py`, Appendix R). AquaBounty
  (AQB) closes at $528.00, then **$0.14** on 2017-01-09 and $3.33 the next day, then $529.80: two wrong
  bars. They make one "fall" of 99.97 % and one "gain" of 15,080 %, which is the whole of the deep-fall
  MID cell's +15.35 % in discovery (without its three largest events that cell's mean raw return is
  −0.72 %) and of the five-session D1 and D2 MID means of +3 % and +4 %. No barred cell contains the
  event: AquaBounty's D1 and D2 event of 2016-12-27 blocks a new one through 2017-01-11. Bad prints can
  also inflate a
  cell's noise; the medians and winsorised means, fixed as reported measures before the run, are the
  check: across the eight barred cells and both periods they lie between −0.63 % and +0.46 %. A scan of
  the panel (`exp041_aqb.py`) finds 23 one-session close ratios beyond 50×, and only AquaBounty's two fall
  on a company that is in a bucket that session.

## 7. Conclusions

Buying a mid or small company after a sharp fall, or after a strong reaction to its results, and
holding ten sessions earns nothing over its peers: none of the eight cells is distinguishable from zero
on 2017–2021, so nothing was carried to the later years, and those years agree. The four rules are
closed at this horizon, as section 2 fixed.

The nearest thing to an effect is the fall with no results release in mid and large companies: a
winsorised mean of +0.35 % to +0.46 % in both periods, the direction the literature gives it. It is not
significant and it is smaller than the 50 bps a round trip costs, so it is not a lead. In the SMALL
bucket, where the literature places the effect, the typical such fall loses to its peers (median −0.36 % and
−0.63 %).

For the operator's style the trade-shape table is the plain answer. In the MID and SMALL buckets
49 % to 54 % of the trades end up. After a fall, +5 % comes before −5 % in
46 % to 50 % of them and −5 % first in 44 % to 49 %; after a strong results
reaction, 41 % to 42 % and 40 % to 46 %. There is no tilt to take a small gain from.

Smaller companies are not easier at this horizon: LARGE reads the same as MID and SMALL.

What this does not say: nothing about other entry rules (this is two families, four rules), about
horizons under a week, about intraday entries, or about the companies first listed after 2021; and it
is a test of means, not of a managed book. One vendor bad print was found by its size; smaller wrong
bars would pass unseen, which is why the medians are read beside the means.

With EXP-015, EXP-023, EXP-030, EXP-031 and EXP-038, the public price, news and filing signals this
project has tested now cover a month and a fortnight, in large, mid and small companies, and none
carries. What is left untested is information the market does not already hold in public
form at the close, or a horizon shorter than the fleet's daily cycle.

## 8. Recommended code changes, and how to implement them

None. By the rule fixed in section 2, on NONE nothing is built and no simulation is pre-registered; the
fleet's universe stays the S&P 500.

For the operator, not a build: the one-to-two-week, small-gain style has now been tested from both
sides (exits in EXP-022 and EXP-040, entries here) and has no measured source of profit in public daily
data. The choices that remain are the operator's: keep the fleet as the paper test bed it is, holding
what it buys ([ADR-0033](../../decisions/0033-the-fleet-is-a-paper-test-bed.md)); or name a different
source of information to test.

Data worth keeping: the kit's 7,092-company daily panel with delisted companies and results dates is
the first survivorship-free universe beyond the S&P 500 this project has, and a later experiment can
reuse it at $0. The SEC's 2022 → 2026 insider files would add the companies listed since 2021; they
need the operator to set a contact address for `www.sec.gov` in an environment variable.

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

2026-11-16, this laptop.

**Build, and the defects fixed before any return was read.** The first build (kept as `bars_v1/`,
`registry_v1.csv`) set each issuer's `asof` to the end of its last quarter. The pilot checks showed
four defects, each from dates, names and row counts:

1. *A blank ticker became "NAN".* The reader turned empty and "N/A" ticker fields into a missing value
   that printed as `NAN`, a real ticker. 21 issuers were priced as one closed-end fund and about 200
   were dropped as collisions with it. Fixed in `exp041_registry.py` (missing values are read as text and
   rejected).
2. *An `asof` after a delisting.* A company bought in mid-quarter was asked for as of the quarter's
   end; the vendor answered with a later holder of the ticker (132 groups of issuers shared one series:
   NetSuite's "N" with a later company's). Fixed by the registry's `asof` rule (section 3).
3. *Bankruptcies named by their over-the-counter ticker.* 1,366 issuers had no bars under their last
   ticker; `exp041_fallback.py` tried the earlier ones and recovered 96 (Vanguard Natural Resources,
   Westmoreland, Willbros, Orchids Paper, Orexigen among them).
4. *A later holder's history for an unlisted issuer.* An over-the-counter "MRNA" came back as Moderna.
   A first rule (a bar within 14 days of `asof`) dropped 684 rows; `exp041_asof_check.py` showed that
   551 of them began after `asof`, mostly blank-cheque companies whose shares started trading about 55
   days after their first filing, and 127 ended before it (companies that had left their exchange). The
   rule was narrowed to "first bar more than 100 days after `asof`": 153 rows dropped.

After the fixes `exp041_dupes.py` finds no series under two kept companies. Bars: main pass 7,271
companies, 13.2 million rows; earlier-ticker passes 86 and 10 companies. Releases: 8,656 issuers asked,
none missing from EDGAR.

**Self-test** (`selftest.log`): no effect planted, D1 MID −0.091 % (t −0.47), verdict NONE; +0.3 % a
session planted, +2.742 % (t 13.73), verdict LEAD; the Newey–West, Benjamini–Hochberg and Holm checks
pass.

**Pre-registration** `ff107361`. `frozen.sha256` verified immediately before scoring: its eleven entries
unchanged (the 54 bar files against `bars.sha256` after the run: all equal).

**Score.** `python -I exp041_score.py score …`, run once, 77 s, exit 0. `exp041.json` SHA-256
`301f18c1d7ae4618c502b158797dbc0accb885e6a8e9160c9567579abcecd133`, `score.log`
`bc87ae9e204ade04c2f4720b059426c3b732b01f77d1e55373f35543b8f34aae`. No defect in the scorer, no re-run.

**After the run** (`exp041_outlier.py`, `outlier.log`): the deep-fall MID cell's discovery events sorted
by return. AquaBounty 2017-01-09, closes t−5 … t+2: 486.00, 496.20, 520.60, 516.60, 528.00, **0.14**,
**3.33**, 529.80; entry open 2.00; return +15,080 %. Next: Hertz 2020-05-26 +359 % (its bankruptcy
rally, real), Tilray 2020-03-13 +156 % (real). 1,534 events, mean raw return +9.45 %; without the top
three −0.72 %. `exp041_aqb.py` (`aqb.log`): AquaBounty's D1 and D2 events fall on 2016-12-27, its
deep-fall event on 2017-01-09; 23 one-session close ratios beyond 50× in the panel, two on a bucketed
company, both AquaBounty's. The scored output was not changed.

The content of `exp041.json`, laid out one cell a line (checked equal to the file after parsing):

```json
{
 "sessions": ["2016-01-04", "2026-10-30", 2723], "companies": 3967,
 "build": {"registry_rows_with_bars": 7367, "dropped_not_listed_at_asof": 153, "price_series": 7214, "distinct_price_series": 7092},
 "verdict": "NONE",
 "funnel": {
  "D1 MID": {"p_discovery": 0.5892, "passed_discovery": false, "direction": null, "p_confirmation": null, "confirmed": false, "economic": null},
  "D1 SMALL": {"p_discovery": 0.91241, "passed_discovery": false, "direction": null, "p_confirmation": null, "confirmed": false, "economic": null},
  "D2 MID": {"p_discovery": 0.50925, "passed_discovery": false, "direction": null, "p_confirmation": null, "confirmed": false, "economic": null},
  "D2 SMALL": {"p_discovery": 0.79486, "passed_discovery": false, "direction": null, "p_confirmation": null, "confirmed": false, "economic": null},
  "D3 MID": {"p_discovery": 0.65271, "passed_discovery": false, "direction": null, "p_confirmation": null, "confirmed": false, "economic": null},
  "D3 SMALL": {"p_discovery": 0.7414, "passed_discovery": false, "direction": null, "p_confirmation": null, "confirmed": false, "economic": null},
  "E1 MID": {"p_discovery": 0.52217, "passed_discovery": false, "direction": null, "p_confirmation": null, "confirmed": false, "economic": null},
  "E1 SMALL": {"p_discovery": 0.86501, "passed_discovery": false, "direction": null, "p_confirmation": null, "confirmed": false, "economic": null}
 },
 "hold_10": {
  "D1 LARGE": {
   "discovery": {"events": 5803, "sessions": 931, "mean_excess_pct": 0.236, "t": 0.61, "net_mean_excess_pct": -0.264, "net_t": -0.68, "event_mean_excess_pct": 0.378, "event_median_excess_pct": 0.073, "event_winsorised_mean_excess_pct": 0.251, "mean_raw_return_pct": 1.004, "share_up": 0.548, "share_target_first": 0.493, "share_stop_first": 0.443},
   "confirmation": {"events": 6916, "sessions": 961, "mean_excess_pct": 0.157, "t": 0.46, "net_mean_excess_pct": -0.343, "net_t": -1.0, "event_mean_excess_pct": 0.438, "event_median_excess_pct": 0.051, "event_winsorised_mean_excess_pct": 0.325, "mean_raw_return_pct": 1.29, "share_up": 0.542, "share_target_first": 0.496, "share_stop_first": 0.442}
  },
  "D1 MID": {
   "discovery": {"events": 7750, "sessions": 1061, "mean_excess_pct": 0.182, "t": 0.54, "net_mean_excess_pct": -0.318, "net_t": -0.95, "event_mean_excess_pct": 0.373, "event_median_excess_pct": -0.104, "event_winsorised_mean_excess_pct": 0.288, "mean_raw_return_pct": 0.856, "share_up": 0.528, "share_target_first": 0.484, "share_stop_first": 0.474},
   "confirmation": {"events": 8142, "sessions": 1030, "mean_excess_pct": -0.043, "t": -0.14, "net_mean_excess_pct": -0.543, "net_t": -1.73, "event_mean_excess_pct": 0.366, "event_median_excess_pct": -0.094, "event_winsorised_mean_excess_pct": 0.278, "mean_raw_return_pct": 1.181, "share_up": 0.537, "share_target_first": 0.497, "share_stop_first": 0.451}
  },
  "D1 SMALL": {
   "discovery": {"events": 18912, "sessions": 1229, "mean_excess_pct": -0.042, "t": -0.11, "net_mean_excess_pct": -0.542, "net_t": -1.42, "event_mean_excess_pct": 0.241, "event_median_excess_pct": -0.317, "event_winsorised_mean_excess_pct": -0.049, "mean_raw_return_pct": 0.732, "share_up": 0.513, "share_target_first": 0.47, "share_stop_first": 0.496},
   "confirmation": {"events": 20691, "sessions": 1145, "mean_excess_pct": 0.136, "t": 0.35, "net_mean_excess_pct": -0.364, "net_t": -0.94, "event_mean_excess_pct": 0.1, "event_median_excess_pct": -0.595, "event_winsorised_mean_excess_pct": -0.145, "mean_raw_return_pct": 0.794, "share_up": 0.503, "share_target_first": 0.486, "share_stop_first": 0.479}
  },
  "D2 LARGE": {
   "discovery": {"events": 4745, "sessions": 774, "mean_excess_pct": 0.382, "t": 0.84, "net_mean_excess_pct": -0.118, "net_t": -0.26, "event_mean_excess_pct": 0.503, "event_median_excess_pct": 0.174, "event_winsorised_mean_excess_pct": 0.381, "mean_raw_return_pct": 1.035, "share_up": 0.548, "share_target_first": 0.507, "share_stop_first": 0.45},
   "confirmation": {"events": 5658, "sessions": 826, "mean_excess_pct": 0.233, "t": 0.53, "net_mean_excess_pct": -0.267, "net_t": -0.6, "event_mean_excess_pct": 0.465, "event_median_excess_pct": 0.098, "event_winsorised_mean_excess_pct": 0.348, "mean_raw_return_pct": 1.432, "share_up": 0.552, "share_target_first": 0.505, "share_stop_first": 0.452}
  },
  "D2 MID": {
   "discovery": {"events": 6448, "sessions": 976, "mean_excess_pct": 0.267, "t": 0.66, "net_mean_excess_pct": -0.233, "net_t": -0.57, "event_mean_excess_pct": 0.558, "event_median_excess_pct": 0.099, "event_winsorised_mean_excess_pct": 0.463, "mean_raw_return_pct": 1.058, "share_up": 0.538, "share_target_first": 0.495, "share_stop_first": 0.479},
   "confirmation": {"events": 6686, "sessions": 946, "mean_excess_pct": 0.406, "t": 1.0, "net_mean_excess_pct": -0.094, "net_t": -0.23, "event_mean_excess_pct": 0.502, "event_median_excess_pct": -0.063, "event_winsorised_mean_excess_pct": 0.421, "mean_raw_return_pct": 1.379, "share_up": 0.539, "share_target_first": 0.501, "share_stop_first": 0.461}
  },
  "D2 SMALL": {
   "discovery": {"events": 15874, "sessions": 1201, "mean_excess_pct": 0.134, "t": 0.26, "net_mean_excess_pct": -0.366, "net_t": -0.72, "event_mean_excess_pct": 0.318, "event_median_excess_pct": -0.364, "event_winsorised_mean_excess_pct": -0.021, "mean_raw_return_pct": 0.832, "share_up": 0.516, "share_target_first": 0.477, "share_stop_first": 0.5},
   "confirmation": {"events": 17491, "sessions": 1129, "mean_excess_pct": 0.33, "t": 0.74, "net_mean_excess_pct": -0.17, "net_t": -0.38, "event_mean_excess_pct": 0.124, "event_median_excess_pct": -0.632, "event_winsorised_mean_excess_pct": -0.174, "mean_raw_return_pct": 0.881, "share_up": 0.504, "share_target_first": 0.493, "share_stop_first": 0.478}
  },
  "D3 LARGE": {
   "discovery": {"events": 1511, "sessions": 573, "mean_excess_pct": -0.252, "t": -0.66, "net_mean_excess_pct": -0.752, "net_t": -1.98, "event_mean_excess_pct": -0.278, "event_median_excess_pct": -0.303, "event_winsorised_mean_excess_pct": -0.316, "mean_raw_return_pct": 0.147, "share_up": 0.536, "share_target_first": 0.449, "share_stop_first": 0.428},
   "confirmation": {"events": 1768, "sessions": 608, "mean_excess_pct": 0.444, "t": 1.29, "net_mean_excess_pct": -0.056, "net_t": -0.16, "event_mean_excess_pct": 0.386, "event_median_excess_pct": -0.228, "event_winsorised_mean_excess_pct": 0.339, "mean_raw_return_pct": 0.884, "share_up": 0.503, "share_target_first": 0.458, "share_stop_first": 0.428}
  },
  "D3 MID": {
   "discovery": {"events": 2018, "sessions": 602, "mean_excess_pct": 0.187, "t": 0.45, "net_mean_excess_pct": -0.313, "net_t": -0.75, "event_mean_excess_pct": -0.095, "event_median_excess_pct": -0.424, "event_winsorised_mean_excess_pct": -0.164, "mean_raw_return_pct": -0.591, "share_up": 0.486, "share_target_first": 0.454, "share_stop_first": 0.457},
   "confirmation": {"events": 2096, "sessions": 594, "mean_excess_pct": 0.18, "t": 0.46, "net_mean_excess_pct": -0.32, "net_t": -0.82, "event_mean_excess_pct": 0.06, "event_median_excess_pct": -0.143, "event_winsorised_mean_excess_pct": 0.044, "mean_raw_return_pct": 0.706, "share_up": 0.535, "share_target_first": 0.48, "share_stop_first": 0.43}
  },
  "D3 SMALL": {
   "discovery": {"events": 4834, "sessions": 864, "mean_excess_pct": 0.128, "t": 0.33, "net_mean_excess_pct": -0.372, "net_t": -0.96, "event_mean_excess_pct": 0.102, "event_median_excess_pct": -0.225, "event_winsorised_mean_excess_pct": -0.015, "mean_raw_return_pct": -0.334, "share_up": 0.496, "share_target_first": 0.46, "share_stop_first": 0.474},
   "confirmation": {"events": 5258, "sessions": 835, "mean_excess_pct": -0.728, "t": -1.97, "net_mean_excess_pct": -1.228, "net_t": -3.32, "event_mean_excess_pct": 0.154, "event_median_excess_pct": -0.446, "event_winsorised_mean_excess_pct": 0.048, "mean_raw_return_pct": 0.677, "share_up": 0.502, "share_target_first": 0.456, "share_stop_first": 0.49}
  },
  "E1 LARGE": {
   "discovery": {"events": 1628, "sessions": 618, "mean_excess_pct": 0.471, "t": 1.59, "net_mean_excess_pct": -0.029, "net_t": -0.1, "event_mean_excess_pct": 0.376, "event_median_excess_pct": 0.05, "event_winsorised_mean_excess_pct": 0.299, "mean_raw_return_pct": 0.891, "share_up": 0.55, "share_target_first": 0.373, "share_stop_first": 0.342},
   "confirmation": {"events": 1958, "sessions": 611, "mean_excess_pct": 0.339, "t": 0.91, "net_mean_excess_pct": -0.161, "net_t": -0.43, "event_mean_excess_pct": 0.133, "event_median_excess_pct": -0.018, "event_winsorised_mean_excess_pct": 0.048, "mean_raw_return_pct": 0.465, "share_up": 0.518, "share_target_first": 0.421, "share_stop_first": 0.356}
  },
  "E1 MID": {
   "discovery": {"events": 1876, "sessions": 604, "mean_excess_pct": -0.672, "t": -0.64, "net_mean_excess_pct": -1.172, "net_t": -1.12, "event_mean_excess_pct": -0.466, "event_median_excess_pct": 0.056, "event_winsorised_mean_excess_pct": -0.007, "mean_raw_return_pct": 0.426, "share_up": 0.519, "share_target_first": 0.387, "share_stop_first": 0.409},
   "confirmation": {"events": 2165, "sessions": 567, "mean_excess_pct": 0.12, "t": 0.42, "net_mean_excess_pct": -0.38, "net_t": -1.32, "event_mean_excess_pct": 0.451, "event_median_excess_pct": 0.169, "event_winsorised_mean_excess_pct": 0.323, "mean_raw_return_pct": 0.795, "share_up": 0.528, "share_target_first": 0.439, "share_stop_first": 0.394}
  },
  "E1 SMALL": {
   "discovery": {"events": 4313, "sessions": 814, "mean_excess_pct": -0.045, "t": -0.17, "net_mean_excess_pct": -0.545, "net_t": -2.01, "event_mean_excess_pct": -0.213, "event_median_excess_pct": -0.55, "event_winsorised_mean_excess_pct": -0.285, "mean_raw_return_pct": -0.188, "share_up": 0.487, "share_target_first": 0.399, "share_stop_first": 0.461},
   "confirmation": {"events": 4563, "sessions": 771, "mean_excess_pct": 0.173, "t": 0.49, "net_mean_excess_pct": -0.327, "net_t": -0.92, "event_mean_excess_pct": 0.039, "event_median_excess_pct": -0.125, "event_winsorised_mean_excess_pct": -0.071, "mean_raw_return_pct": 0.172, "share_up": 0.495, "share_target_first": 0.446, "share_stop_first": 0.45}
  },
  "D1_deep LARGE": {
   "discovery": {"events": 1083, "sessions": 360, "mean_excess_pct": -0.122, "t": -0.15, "net_mean_excess_pct": -0.622, "net_t": -0.74, "event_mean_excess_pct": 0.614, "event_median_excess_pct": 0.451, "event_winsorised_mean_excess_pct": 0.447, "mean_raw_return_pct": 0.853, "share_up": 0.554, "share_target_first": 0.423, "share_stop_first": 0.56},
   "confirmation": {"events": 1175, "sessions": 436, "mean_excess_pct": 0.506, "t": 0.64, "net_mean_excess_pct": 0.006, "net_t": 0.01, "event_mean_excess_pct": 1.025, "event_median_excess_pct": 0.377, "event_winsorised_mean_excess_pct": 0.971, "mean_raw_return_pct": 2.257, "share_up": 0.548, "share_target_first": 0.517, "share_stop_first": 0.473}
  },
  "D1_deep MID": {
   "discovery": {"events": 1534, "sessions": 501, "mean_excess_pct": 15.347, "t": 1.02, "net_mean_excess_pct": 14.847, "net_t": 0.99, "event_mean_excess_pct": 9.926, "event_median_excess_pct": -0.529, "event_winsorised_mean_excess_pct": -0.111, "mean_raw_return_pct": 9.447, "share_up": 0.502, "share_target_first": 0.411, "share_stop_first": 0.576},
   "confirmation": {"events": 1413, "sessions": 529, "mean_excess_pct": -0.299, "t": -0.47, "net_mean_excess_pct": -0.799, "net_t": -1.27, "event_mean_excess_pct": 0.469, "event_median_excess_pct": -0.09, "event_winsorised_mean_excess_pct": 0.32, "mean_raw_return_pct": 1.791, "share_up": 0.544, "share_target_first": 0.498, "share_stop_first": 0.488}
  },
  "D1_deep SMALL": {
   "discovery": {"events": 4128, "sessions": 892, "mean_excess_pct": -1.19, "t": -2.45, "net_mean_excess_pct": -1.69, "net_t": -3.48, "event_mean_excess_pct": -0.184, "event_median_excess_pct": -0.449, "event_winsorised_mean_excess_pct": -0.258, "mean_raw_return_pct": -0.699, "share_up": 0.49, "share_target_first": 0.411, "share_stop_first": 0.578},
   "confirmation": {"events": 4227, "sessions": 927, "mean_excess_pct": -0.068, "t": -0.05, "net_mean_excess_pct": -0.568, "net_t": -0.46, "event_mean_excess_pct": 0.133, "event_median_excess_pct": -1.146, "event_winsorised_mean_excess_pct": -0.293, "mean_raw_return_pct": 1.111, "share_up": 0.489, "share_target_first": 0.476, "share_stop_first": 0.517}
  },
  "E1_big LARGE": {
   "discovery": {"events": 534, "sessions": 334, "mean_excess_pct": 0.593, "t": 1.39, "net_mean_excess_pct": 0.093, "net_t": 0.22, "event_mean_excess_pct": 0.893, "event_median_excess_pct": 0.555, "event_winsorised_mean_excess_pct": 0.821, "mean_raw_return_pct": 1.436, "share_up": 0.567, "share_target_first": 0.451, "share_stop_first": 0.393},
   "confirmation": {"events": 772, "sessions": 407, "mean_excess_pct": 0.962, "t": 1.47, "net_mean_excess_pct": 0.462, "net_t": 0.7, "event_mean_excess_pct": 0.53, "event_median_excess_pct": 0.132, "event_winsorised_mean_excess_pct": 0.394, "mean_raw_return_pct": 0.845, "share_up": 0.51, "share_target_first": 0.482, "share_stop_first": 0.404}
  },
  "E1_big MID": {
   "discovery": {"events": 693, "sessions": 390, "mean_excess_pct": -1.867, "t": -1.17, "net_mean_excess_pct": -2.367, "net_t": -1.48, "event_mean_excess_pct": -0.853, "event_median_excess_pct": -0.457, "event_winsorised_mean_excess_pct": -0.123, "mean_raw_return_pct": 0.33, "share_up": 0.511, "share_target_first": 0.427, "share_stop_first": 0.421},
   "confirmation": {"events": 953, "sessions": 423, "mean_excess_pct": 0.267, "t": 0.64, "net_mean_excess_pct": -0.233, "net_t": -0.56, "event_mean_excess_pct": 0.474, "event_median_excess_pct": 0.332, "event_winsorised_mean_excess_pct": 0.37, "mean_raw_return_pct": 0.851, "share_up": 0.509, "share_target_first": 0.467, "share_stop_first": 0.43}
  },
  "E1_big SMALL": {
   "discovery": {"events": 1861, "sessions": 593, "mean_excess_pct": 0.209, "t": 0.51, "net_mean_excess_pct": -0.291, "net_t": -0.71, "event_mean_excess_pct": -0.189, "event_median_excess_pct": -0.902, "event_winsorised_mean_excess_pct": -0.261, "mean_raw_return_pct": -0.113, "share_up": 0.477, "share_target_first": 0.423, "share_stop_first": 0.484},
   "confirmation": {"events": 2326, "sessions": 609, "mean_excess_pct": -0.119, "t": -0.29, "net_mean_excess_pct": -0.619, "net_t": -1.5, "event_mean_excess_pct": -0.126, "event_median_excess_pct": -0.562, "event_winsorised_mean_excess_pct": -0.26, "mean_raw_return_pct": 0.013, "share_up": 0.485, "share_target_first": 0.454, "share_stop_first": 0.481}
  }
 },
 "hold_5": {
  "D1 LARGE": {
   "discovery": {"events": 6878, "sessions": 962, "mean_excess_pct": 0.112, "t": 0.49, "net_mean_excess_pct": -0.388, "net_t": -1.71, "event_mean_excess_pct": 0.465, "event_median_excess_pct": 0.089, "event_winsorised_mean_excess_pct": 0.394, "mean_raw_return_pct": 0.91, "share_up": 0.55, "share_target_first": 0.415, "share_stop_first": 0.43},
   "confirmation": {"events": 8027, "sessions": 996, "mean_excess_pct": 0.163, "t": 0.72, "net_mean_excess_pct": -0.337, "net_t": -1.48, "event_mean_excess_pct": 0.526, "event_median_excess_pct": 0.022, "event_winsorised_mean_excess_pct": 0.488, "mean_raw_return_pct": 1.117, "share_up": 0.534, "share_target_first": 0.429, "share_stop_first": 0.401}
  },
  "D1 MID": {
   "discovery": {"events": 9224, "sessions": 1093, "mean_excess_pct": 3.121, "t": 1.01, "net_mean_excess_pct": 2.621, "net_t": 0.85, "event_mean_excess_pct": 2.147, "event_median_excess_pct": 0.009, "event_winsorised_mean_excess_pct": 0.273, "mean_raw_return_pct": 2.531, "share_up": 0.531, "share_target_first": 0.425, "share_stop_first": 0.454},
   "confirmation": {"events": 9436, "sessions": 1057, "mean_excess_pct": -0.029, "t": -0.14, "net_mean_excess_pct": -0.529, "net_t": -2.52, "event_mean_excess_pct": 0.189, "event_median_excess_pct": -0.058, "event_winsorised_mean_excess_pct": 0.12, "mean_raw_return_pct": 0.791, "share_up": 0.535, "share_target_first": 0.436, "share_stop_first": 0.412}
  },
  "D1 SMALL": {
   "discovery": {"events": 22721, "sessions": 1241, "mean_excess_pct": 0.16, "t": 0.54, "net_mean_excess_pct": -0.34, "net_t": -1.14, "event_mean_excess_pct": 0.273, "event_median_excess_pct": -0.146, "event_winsorised_mean_excess_pct": 0.054, "mean_raw_return_pct": 0.496, "share_up": 0.514, "share_target_first": 0.426, "share_stop_first": 0.471},
   "confirmation": {"events": 24620, "sessions": 1167, "mean_excess_pct": -0.075, "t": -0.28, "net_mean_excess_pct": -0.575, "net_t": -2.13, "event_mean_excess_pct": 0.13, "event_median_excess_pct": -0.363, "event_winsorised_mean_excess_pct": -0.004, "mean_raw_return_pct": 0.662, "share_up": 0.506, "share_target_first": 0.441, "share_stop_first": 0.446}
  },
  "D2 LARGE": {
   "discovery": {"events": 5647, "sessions": 809, "mean_excess_pct": 0.213, "t": 0.72, "net_mean_excess_pct": -0.287, "net_t": -0.97, "event_mean_excess_pct": 0.641, "event_median_excess_pct": 0.183, "event_winsorised_mean_excess_pct": 0.582, "mean_raw_return_pct": 1.088, "share_up": 0.556, "share_target_first": 0.432, "share_stop_first": 0.446},
   "confirmation": {"events": 6524, "sessions": 870, "mean_excess_pct": 0.37, "t": 1.26, "net_mean_excess_pct": -0.13, "net_t": -0.44, "event_mean_excess_pct": 0.568, "event_median_excess_pct": 0.082, "event_winsorised_mean_excess_pct": 0.538, "mean_raw_return_pct": 1.209, "share_up": 0.538, "share_target_first": 0.443, "share_stop_first": 0.413}
  },
  "D2 MID": {
   "discovery": {"events": 7620, "sessions": 1002, "mean_excess_pct": 4.106, "t": 0.98, "net_mean_excess_pct": 3.606, "net_t": 0.86, "event_mean_excess_pct": 2.612, "event_median_excess_pct": 0.089, "event_winsorised_mean_excess_pct": 0.341, "mean_raw_return_pct": 3.043, "share_up": 0.539, "share_target_first": 0.432, "share_stop_first": 0.468},
   "confirmation": {"events": 7683, "sessions": 974, "mean_excess_pct": 0.155, "t": 0.63, "net_mean_excess_pct": -0.345, "net_t": -1.39, "event_mean_excess_pct": 0.254, "event_median_excess_pct": -0.037, "event_winsorised_mean_excess_pct": 0.176, "mean_raw_return_pct": 0.849, "share_up": 0.533, "share_target_first": 0.448, "share_stop_first": 0.421}
  },
  "D2 SMALL": {
   "discovery": {"events": 18927, "sessions": 1210, "mean_excess_pct": 0.127, "t": 0.36, "net_mean_excess_pct": -0.373, "net_t": -1.06, "event_mean_excess_pct": 0.306, "event_median_excess_pct": -0.167, "event_winsorised_mean_excess_pct": 0.045, "mean_raw_return_pct": 0.58, "share_up": 0.517, "share_target_first": 0.431, "share_stop_first": 0.483},
   "confirmation": {"events": 20500, "sessions": 1154, "mean_excess_pct": 0.061, "t": 0.21, "net_mean_excess_pct": -0.439, "net_t": -1.53, "event_mean_excess_pct": 0.145, "event_median_excess_pct": -0.348, "event_winsorised_mean_excess_pct": -0.0, "mean_raw_return_pct": 0.695, "share_up": 0.509, "share_target_first": 0.45, "share_stop_first": 0.446}
  },
  "D3 LARGE": {
   "discovery": {"events": 1516, "sessions": 574, "mean_excess_pct": 0.185, "t": 0.7, "net_mean_excess_pct": -0.315, "net_t": -1.2, "event_mean_excess_pct": -0.115, "event_median_excess_pct": -0.436, "event_winsorised_mean_excess_pct": -0.156, "mean_raw_return_pct": 0.249, "share_up": 0.513, "share_target_first": 0.369, "share_stop_first": 0.358},
   "confirmation": {"events": 1781, "sessions": 613, "mean_excess_pct": 0.571, "t": 2.08, "net_mean_excess_pct": 0.071, "net_t": 0.26, "event_mean_excess_pct": 0.646, "event_median_excess_pct": -0.091, "event_winsorised_mean_excess_pct": 0.571, "mean_raw_return_pct": 1.114, "share_up": 0.521, "share_target_first": 0.386, "share_stop_first": 0.361}
  },
  "D3 MID": {
   "discovery": {"events": 2023, "sessions": 605, "mean_excess_pct": 0.398, "t": 1.67, "net_mean_excess_pct": -0.102, "net_t": -0.43, "event_mean_excess_pct": 0.06, "event_median_excess_pct": -0.201, "event_winsorised_mean_excess_pct": 0.07, "mean_raw_return_pct": 0.175, "share_up": 0.494, "share_target_first": 0.403, "share_stop_first": 0.401},
   "confirmation": {"events": 2112, "sessions": 601, "mean_excess_pct": -0.035, "t": -0.13, "net_mean_excess_pct": -0.535, "net_t": -2.04, "event_mean_excess_pct": 0.05, "event_median_excess_pct": -0.104, "event_winsorised_mean_excess_pct": 0.065, "mean_raw_return_pct": 0.67, "share_up": 0.539, "share_target_first": 0.405, "share_stop_first": 0.377}
  },
  "D3 SMALL": {
   "discovery": {"events": 4857, "sessions": 864, "mean_excess_pct": 0.091, "t": 0.43, "net_mean_excess_pct": -0.409, "net_t": -1.93, "event_mean_excess_pct": 0.13, "event_median_excess_pct": -0.094, "event_winsorised_mean_excess_pct": 0.103, "mean_raw_return_pct": -0.051, "share_up": 0.493, "share_target_first": 0.412, "share_stop_first": 0.417},
   "confirmation": {"events": 5286, "sessions": 842, "mean_excess_pct": -0.771, "t": -3.29, "net_mean_excess_pct": -1.271, "net_t": -5.43, "event_mean_excess_pct": 0.096, "event_median_excess_pct": -0.372, "event_winsorised_mean_excess_pct": 0.038, "mean_raw_return_pct": 0.694, "share_up": 0.505, "share_target_first": 0.416, "share_stop_first": 0.443}
  },
  "E1 LARGE": {
   "discovery": {"events": 1630, "sessions": 618, "mean_excess_pct": 0.177, "t": 0.94, "net_mean_excess_pct": -0.323, "net_t": -1.72, "event_mean_excess_pct": 0.154, "event_median_excess_pct": 0.041, "event_winsorised_mean_excess_pct": 0.141, "mean_raw_return_pct": 0.462, "share_up": 0.526, "share_target_first": 0.294, "share_stop_first": 0.27},
   "confirmation": {"events": 1972, "sessions": 615, "mean_excess_pct": -0.09, "t": -0.41, "net_mean_excess_pct": -0.59, "net_t": -2.7, "event_mean_excess_pct": -0.068, "event_median_excess_pct": -0.056, "event_winsorised_mean_excess_pct": -0.116, "mean_raw_return_pct": 0.249, "share_up": 0.514, "share_target_first": 0.307, "share_stop_first": 0.281}
  },
  "E1 MID": {
   "discovery": {"events": 1878, "sessions": 605, "mean_excess_pct": -0.883, "t": -1.12, "net_mean_excess_pct": -1.383, "net_t": -1.76, "event_mean_excess_pct": -0.489, "event_median_excess_pct": -0.047, "event_winsorised_mean_excess_pct": -0.094, "mean_raw_return_pct": 0.038, "share_up": 0.501, "share_target_first": 0.301, "share_stop_first": 0.342},
   "confirmation": {"events": 2182, "sessions": 572, "mean_excess_pct": 0.177, "t": 0.86, "net_mean_excess_pct": -0.323, "net_t": -1.57, "event_mean_excess_pct": 0.33, "event_median_excess_pct": -0.121, "event_winsorised_mean_excess_pct": 0.257, "mean_raw_return_pct": 0.669, "share_up": 0.535, "share_target_first": 0.357, "share_stop_first": 0.328}
  },
  "E1 SMALL": {
   "discovery": {"events": 4322, "sessions": 815, "mean_excess_pct": 0.203, "t": 0.66, "net_mean_excess_pct": -0.297, "net_t": -0.96, "event_mean_excess_pct": -0.148, "event_median_excess_pct": -0.421, "event_winsorised_mean_excess_pct": -0.257, "mean_raw_return_pct": -0.154, "share_up": 0.471, "share_target_first": 0.345, "share_stop_first": 0.397},
   "confirmation": {"events": 4583, "sessions": 776, "mean_excess_pct": 0.014, "t": 0.06, "net_mean_excess_pct": -0.486, "net_t": -1.89, "event_mean_excess_pct": -0.061, "event_median_excess_pct": -0.236, "event_winsorised_mean_excess_pct": -0.154, "mean_raw_return_pct": 0.256, "share_up": 0.499, "share_target_first": 0.39, "share_stop_first": 0.395}
  },
  "D1_deep LARGE": {
   "discovery": {"events": 1274, "sessions": 379, "mean_excess_pct": 0.437, "t": 0.73, "net_mean_excess_pct": -0.063, "net_t": -0.11, "event_mean_excess_pct": 1.347, "event_median_excess_pct": 0.424, "event_winsorised_mean_excess_pct": 1.269, "mean_raw_return_pct": 1.354, "share_up": 0.519, "share_target_first": 0.385, "share_stop_first": 0.575},
   "confirmation": {"events": 1249, "sessions": 445, "mean_excess_pct": 0.708, "t": 1.3, "net_mean_excess_pct": 0.208, "net_t": 0.38, "event_mean_excess_pct": 1.67, "event_median_excess_pct": 0.534, "event_winsorised_mean_excess_pct": 1.679, "mean_raw_return_pct": 2.733, "share_up": 0.552, "share_target_first": 0.508, "share_stop_first": 0.453}
  },
  "D1_deep MID": {
   "discovery": {"events": 1786, "sessions": 514, "mean_excess_pct": 16.865, "t": 1.03, "net_mean_excess_pct": 16.365, "net_t": 1.0, "event_mean_excess_pct": 10.366, "event_median_excess_pct": 0.24, "event_winsorised_mean_excess_pct": 0.77, "mean_raw_return_pct": 9.955, "share_up": 0.49, "share_target_first": 0.373, "share_stop_first": 0.586},
   "confirmation": {"events": 1500, "sessions": 552, "mean_excess_pct": 0.554, "t": 0.91, "net_mean_excess_pct": 0.054, "net_t": 0.09, "event_mean_excess_pct": 1.063, "event_median_excess_pct": -0.055, "event_winsorised_mean_excess_pct": 0.553, "mean_raw_return_pct": 2.153, "share_up": 0.55, "share_target_first": 0.479, "share_stop_first": 0.472}
  },
  "D1_deep SMALL": {
   "discovery": {"events": 4735, "sessions": 928, "mean_excess_pct": -0.782, "t": -2.09, "net_mean_excess_pct": -1.282, "net_t": -3.42, "event_mean_excess_pct": 0.751, "event_median_excess_pct": 0.141, "event_winsorised_mean_excess_pct": 0.604, "mean_raw_return_pct": -0.034, "share_up": 0.493, "share_target_first": 0.377, "share_stop_first": 0.591},
   "confirmation": {"events": 4554, "sessions": 955, "mean_excess_pct": 0.264, "t": 0.28, "net_mean_excess_pct": -0.236, "net_t": -0.25, "event_mean_excess_pct": 0.328, "event_median_excess_pct": -0.533, "event_winsorised_mean_excess_pct": 0.015, "mean_raw_return_pct": 1.132, "share_up": 0.503, "share_target_first": 0.464, "share_stop_first": 0.508}
  },
  "E1_big LARGE": {
   "discovery": {"events": 534, "sessions": 334, "mean_excess_pct": 0.425, "t": 1.26, "net_mean_excess_pct": -0.075, "net_t": -0.22, "event_mean_excess_pct": 0.508, "event_median_excess_pct": 0.423, "event_winsorised_mean_excess_pct": 0.543, "mean_raw_return_pct": 0.859, "share_up": 0.549, "share_target_first": 0.388, "share_stop_first": 0.331},
   "confirmation": {"events": 772, "sessions": 407, "mean_excess_pct": 0.142, "t": 0.39, "net_mean_excess_pct": -0.358, "net_t": -0.97, "event_mean_excess_pct": 0.06, "event_median_excess_pct": -0.04, "event_winsorised_mean_excess_pct": 0.007, "mean_raw_return_pct": 0.226, "share_up": 0.504, "share_target_first": 0.381, "share_stop_first": 0.341}
  },
  "E1_big MID": {
   "discovery": {"events": 693, "sessions": 390, "mean_excess_pct": -1.623, "t": -1.35, "net_mean_excess_pct": -2.123, "net_t": -1.76, "event_mean_excess_pct": -0.798, "event_median_excess_pct": -0.342, "event_winsorised_mean_excess_pct": -0.234, "mean_raw_return_pct": 0.034, "share_up": 0.489, "share_target_first": 0.354, "share_stop_first": 0.371},
   "confirmation": {"events": 961, "sessions": 426, "mean_excess_pct": 0.517, "t": 1.56, "net_mean_excess_pct": 0.017, "net_t": 0.05, "event_mean_excess_pct": 0.401, "event_median_excess_pct": 0.008, "event_winsorised_mean_excess_pct": 0.346, "mean_raw_return_pct": 0.721, "share_up": 0.531, "share_target_first": 0.409, "share_stop_first": 0.373}
  },
  "E1_big SMALL": {
   "discovery": {"events": 1862, "sessions": 593, "mean_excess_pct": 0.662, "t": 1.52, "net_mean_excess_pct": 0.162, "net_t": 0.37, "event_mean_excess_pct": 0.064, "event_median_excess_pct": -0.52, "event_winsorised_mean_excess_pct": -0.188, "mean_raw_return_pct": 0.087, "share_up": 0.469, "share_target_first": 0.383, "share_stop_first": 0.434},
   "confirmation": {"events": 2332, "sessions": 613, "mean_excess_pct": -0.4, "t": -1.48, "net_mean_excess_pct": -0.9, "net_t": -3.33, "event_mean_excess_pct": -0.19, "event_median_excess_pct": -0.321, "event_winsorised_mean_excess_pct": -0.305, "mean_raw_return_pct": 0.177, "share_up": 0.495, "share_target_first": 0.416, "share_stop_first": 0.435}
  }
 }
}
```

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
