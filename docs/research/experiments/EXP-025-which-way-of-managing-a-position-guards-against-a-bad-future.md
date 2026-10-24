# EXP-025 — When entries carry no skill, which way of managing a position guards against a bad future, and does any of them earn more?

**Status:** EXPLORATION 2026-10-24 (planner), **not a pre-registered test**: about 45 comparisons on
data looked at once, to rank candidates. Nothing here is a verdict. A rule it points to needs its own
pre-registration on data not used here. · **Verdict of the exploration:** no management rule earns
more than holding; a stop near −5 % and a market trend guard cut the catastrophic losses at a price;
overnight-only holding is the one pattern that held in both halves, and it lives or dies on its cost.
**Decision / origin:** the operator, 2026-10-24 · [DL-317](../../design-log.md) · **Cost:** $0 (no LLM,
no broker); about 25 seconds of compute; one Tiingo request for SPY's history.

## 1. Why we needed this experiment

**The operator, 2026-10-24:** *"If we cannot get an edge because we cannot beat VIX, we cannot see
future. what is left to do is to minimise risk of catastrophic losses. I want to explore managing funds
via SEVERAL different methods to see what would win. For example: sell a ticket when say 1% profit
reached. Keep the stock for 7 days and sell it regardless of performance. Find correlation between
tickets and buy correlated stock. Buy last session on Friday and sell on Monday … We trade individual
tickets NOT A PORTFOLIO under the hard set of rules … CAN WE BE BETTER THAN OTHER SIMILAR APPS."*

**The decision that waits.** What the project is for, once prediction is ruled out: EXP-015, EXP-023
and EXP-024 found no ranking skill in the price-only score, its parts, or news sentiment
([DL-315](../../design-log.md), [DL-316](../../design-log.md)); EXP-012 and EXP-013 found that sizing
down in volatility or stress costs money.

**Why an exploration, and why on entries with no skill.** The operator asked to try many methods and
see which wins, which ranks candidates rather than testing one. The premise is *"we cannot see the
future"*, so every S&P 500 member on every session is an entry: what a rule earns then is what the rule
itself earns, not what an entry signal gives it. This also keeps
[EXP-022](EXP-022-does-an-exit-besides-the-stop-make-the-book-earn-more.md)'s sealed question
untouched: no pipeline entry, no pipeline exit and no arm of it is used or read.

## 2. Hypothesis

None: an exploration. The questions, fixed before the first run:

- **Q1, management.** On entries with no skill, does any exit or holding rule earn more per unit of
  capital-time than holding, and what does each do to the left tail? (The operator's +1 % take-profit
  and 7-day hold, beside stops, brackets and a trailing stop.)
- **Q2, calendar.** Does a hold over the weekend, overnight, at the turn of the month or before a
  holiday earn more than other sessions, after cost?
- **Q3, correlation.** When a highly correlated peer moves and a ticket lags, does the ticket catch up?
- **Q4, the bad future.** Does a market guard (stand aside below SPY's 200-day average, or while VIX is
  above 30) cut the catastrophic losses, and at what price, including in the slow crashes the cache's
  decade lacks?
- **Q5, the VIX premium.** How often does VIX overstate the volatility that follows, and does selling
  that insurance (Cboe's BXM and PUT indices) beat holding?

## 3. Data

| Input | Rows / span | SHA-256 prefix | Where |
| --- | --- | --- | --- |
| S235 S&P 500 cache: `sp500_bars`, `_benchmark`, `_membership`, `_sessions`, `_vix` (`.csv.gz`) | 1,360,156 bars, 721 lines, 2016-01-04 → 2026-09-25 | `198cffbb3542`, `f40b8b60506a`, `db971f1b3b95`, `15ba1326e091`, `f80fa60b3ed9` (= EXP-022 §3) | OneDrive `trading-agents-data/` |
| Cboe VIX close | 1990-01-02 → 2026-09-21 | `e5d4fe621031` (`vix.csv.gz`) | OneDrive `trading-agents-data/` |
| SPY daily, adjusted (Tiingo) | 8,492 sessions, 1993-01-29 → 2026-10-23 | `33b168d14446` | kit `inputs/SPY_tiingo.csv` |
| Cboe BXM (buy-write) | daily 2002-03-22 → 2026-10-23 | `a1d9119bae27` | kit `inputs/BXM.csv` |
| Cboe PUT (put-write) | daily from 2007-01-03 (sparse before) | `852d86bba7ec` | kit `inputs/PUT.csv` |
| Cboe SPX (price) | 1975-01-02 → 2026-10-22 | `b15d39fea9dc` | kit `inputs/SPX.csv`, **downloaded; only its first and last lines seen** |

The kit is OneDrive `trading-agents-data/explore-mgmt-2026-10-24/`. SIP and Tiingo bars are licensed
and never enter the repo. **Known defects:** the cache's four Alpaca adjustment errors (TGNA
2017-06-01, RTX 2020-04-03, APTV 2017-12-05, SW 2016-05-16, from `scripts/sp500_known_moves.csv`) are
masked: any return or trade that spans one is dropped. The cache has no bars for a line outside the
index; a trade whose bars end exits at its last close (0.1–0.3 % of trades). Cboe's indices are gross
of trading costs.

## 4. Tools and setup

- **Machine.** Intel Core (family 6, model 142), 4 logical cores, 16 GB RAM, Windows 10 Pro.
- **Software.** Python 3.13.2, numpy 2.5.3, pandas 3.0.6 (the repo's main venv). The scripts import
  no repo code. Repo `main` at `5c7f1e08`.
- **Random seed.** 0. Stationary block bootstrap, mean block 20 sessions, 1,000 resamples, over entry
  dates (management, correlation) or sessions (calendar).
- **External services.** Tiingo (one request, the project's key); Cboe's public CSVs. No LLM, no broker.

## 5. How it was conducted

1. **Management (Q1)** — `explore_mgmt.py`, family A. Every line that is an index member at the close
   of session *t* enters at the open of *t*+1, for *t*+1 from 2017-01-03 to the last session whose
   20-session path fits: **1,222,155 entries, the same for every rule.** A take-profit rests at entry ×
   (1 + tp) and a stop at entry × (1 − sl); a bar touching both counts as the stop; an open beyond a
   barrier fills at the open; a trailing stop rises to each session's high × (1 − trail), read after
   that session; a time exit sells at the open after *k* sessions. The **rate** is Σ return ÷ Σ sessions
   held × 252: what a book earns a year if freed capital is re-spent at once on an entry like it. Costs
   are 5 and 25 bps a side. Each rule's rate at 5 bps is differenced from `hold-20` with one set of
   bootstrap draws. Tails: the mean of the worst 1 % of trades (CVaR 1 %), the share losing more than
   10 %, and the worst day's batch (every name entered that day, averaged).
2. **The guard split (Q4)** — the same trades split by whether SPY, or the ticket itself, closed above
   its 200-session average at the decision.
3. **Calendar (Q2)** — family B, 2017-01-03 → 2026-09-25: the members' equal-weight mean and SPY, per
   session; overnight = close to the next open, daytime = open to close. A weekend is an overnight
   whose previous session was a Friday. The turn of the month is its last session and the next first
   three; pre-holiday is a session before a non-weekend market closure.
4. **Correlation (Q3)** — family C. Every 21 sessions, each member's peer is the member whose daily
   returns over the last 120 sessions correlate most with its own; only pairs at 0.6 or above trade.
   The forward return from the next open over 1 or 5 sessions is scored as excess over all members'
   mean that day.
5. **Market guards and VIX (Q4, Q5)** — family E and `vix_premium` on the cache; then
   `explore_long.py` on SPY 1993–2026 (1993–2016 never seen by the first script), Cboe BXM and PUT
   from 2007-01-03, and VIX against the next 21 sessions' realised SPY volatility.
6. **Overnight holding** — `explore_overnight.py`: SPY held only from each close to the next open, at
   0 to 2 bps a side, with and without the 200-day guard, and the life of NightShares 500 (NSPY), a
   fund built to do exactly this.

The three scripts are verbatim in Appendix S; their outputs and checksums are in Appendix R.

## 6. Results

All MEASURED.

**Q1 — management rules on 1,222,155 entries with no skill, 2017–2026.**

| Rule | Win rate | Avg win / avg loss | Rate, gross | Rate, 5 bps | Rate, 25 bps | 5 bps rate − hold-20 [95 %] | Worst 1 % of trades | Trades losing > 10 % | Worst day's batch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hold-1 | 52 % | +1.42 / −1.42 % | 13.8 % | −11.4 % | −112.0 % | [−30.7, −15.6] | −8.7 % | 0.2 % | −9.9 % |
| **hold-5 (7 calendar days)** | 54 % | +3.22 / −3.20 % | 13.4 % | 8.4 % | −11.8 % | [−9.0, +2.5] | −18.2 % | 2.0 % | −19.0 % |
| hold-7 | 55 % | +3.83 / −3.78 % | 13.3 % | 9.7 % | −4.7 % | [−7.1, +2.9] | −21.1 % | 2.9 % | −24.9 % |
| hold-10 | 55 % | +4.63 / −4.52 % | 13.2 % | 10.7 % | +0.6 % | [−4.9, +2.8] | −24.7 % | 4.4 % | −27.8 % |
| hold-20 (baseline) | 56 % | +6.81 / −6.32 % | 13.1 % | 11.8 % | +6.7 % | — | −33.3 % | 8.3 % | −35.1 % |
| **take +1 % or sell at 5** | **79 %** | **+1.04 / −3.43 %** | 10.3 % | 0.3 % | −39.4 % | [−17.2, −5.8] | −13.7 % | 0.9 % | −10.4 % |
| … filled only 10 bps through | 77 % | +1.06 / −3.39 % | 4.2 % | −5.2 % | −43.0 % | [−22.9, −11.4] | −14.0 % | 0.9 % | −10.8 % |
| take +1 % or sell at 20 | 90 % | +1.07 / −7.86 % | 10.1 % | 4.8 % | −16.3 % | [−11.4, −3.2] | −23.7 % | 2.5 % | −27.2 % |
| take +1 %, stop −5 %, 20 | 84 % | +1.06 / −4.99 % | 6.0 % | −2.0 % | −34.0 % | [−21.2, −7.0] | −7.6 % | 0.1 % | −4.7 % |
| take +1 %, stop −1 %, 5 | 45 % | +1.02 / −1.02 % | −19.1 % | −37.8 % | −112.6 % | [−59.7, −40.3] | −2.0 % | 0.0 % | −1.0 % |
| take +2 % or sell at 5 | 66 % | +1.92 / −3.22 % | 12.0 % | 5.0 % | −23.2 % | [−12.4, −1.3] | −15.7 % | 1.3 % | −14.4 % |
| take +5 %, stop −5 %, 20 | 55 % | +4.64 / −4.69 % | 10.4 % | 7.9 % | −2.3 % | [−9.2, +1.8] | −11.0 % | 0.4 % | −6.8 % |
| take +10 %, stop −5 %, 20 | 47 % | +6.37 / −4.63 % | 10.3 % | 8.4 % | +0.7 % | [−7.8, +1.4] | −11.9 % | 0.6 % | −7.0 % |
| **stop −5 % only, 20** | 45 % | +6.90 / −4.63 % | 10.3 % | 8.6 % | +1.7 % | **[−7.1, +1.1]** | **−12.2 %** | **0.6 %** | **−7.0 %** |
| trailing 5 %, 20 | 42 % | +5.28 / −3.17 % | 9.0 % | 6.7 % | −2.7 % | [−10.9, +0.9] | −10.0 % | 0.3 % | −6.9 % |

The worst single trade is −90.1 % held 20 sessions and **−45.8 % with a −5 % stop**: a gap through the
stop. In the halves (5 bps) `hold-20` reads 14.7 % and 8.6 %, `stop −5 %` 11.6 % and 5.1 %, the +1 %
take-profit 2.1 % and −1.7 %. Every worst batch but one (the ±1 % bracket's, 2022-08-26) falls
between 2020-02-21 and 2020-03-11.

**Q4 within the cache — the guard split, `hold-20`, 2017–2026.**

| Entries made when | Trades | Mean, 20 sessions | Rate | Worst 1 % | Losing > 10 % |
| --- | --- | --- | --- | --- | --- |
| SPY above its 200-day | 1,018,655 | +0.78 % | 9.8 % | −33.2 % | 7.8 % |
| SPY below its 200-day | 203,500 | **+2.34 %** | 29.5 % | −33.6 % | 11.1 % |
| ticket above its own 200-day | 739,359 | +0.78 % | 9.9 % | −29.9 % | 6.9 % |
| ticket below its own 200-day | 445,631 | +1.45 % | 18.3 % | −37.3 % | 10.2 % |

**And outside it — SPY's 20-session holds by the same split** (`explore_long.py`):

| Period | Mean when SPY above | Mean when below | Below, 5th percentile |
| --- | --- | --- | --- |
| 1994–2016 | +0.98 % | **+0.24 %** | −11.0 % |
| 2017–2026 | +1.03 % | **+2.28 %** | −9.4 % |
| dot-com, 2000-03 → 2003-03 | −1.52 % | −1.09 % | −11.6 % |
| GFC, 2007-10 → 2009-03 | −4.59 % | −3.02 % | −18.0 % |

**Q4 — market guards, SPY open to open, decided at the previous close.**

| Period | SPY held | Only above its 200-day (5 bps a switch) | Only while VIX ≤ 30 |
| --- | --- | --- | --- |
| 1994–2026: CAGR · max drawdown · Sharpe | 10.83 % · −55.4 % · 0.65 | 8.09 % · **−28.3 %** · **0.70** | 7.43 % · −55.0 % · 0.57 |
| 1994–2016 | 9.10 % · −55.4 % · 0.55 | 6.99 % · −28.3 % · 0.61 | 6.10 % · −55.0 % · 0.48 |
| 2017–2026 | 15.03 % · −32.0 % · 0.90 | 10.72 % · −20.1 % · 0.89 | 10.60 % · −29.1 % · 0.79 |
| dot-com bear, total | −45.5 % | **−22.2 %** | −53.0 % |
| GFC, total | −54.0 % | **−13.3 %** | −33.6 % |
| COVID, total | −30.2 % | −19.0 % | −14.5 % |
| 2022 bear, total | −25.8 % | −9.9 % | −27.5 % |

The 200-day guard switched 210 times in 33 years (about three round trips a year); 50 times in
2017–2026 on the cache, where it read 15.24 % → 10.63 % CAGR and −32.1 % → −20.1 % drawdown.

**Q2 — calendar, 2017–2026, mean per trade in bps [95 %], members equal-weight (SPY).**

| Hold | Members | SPY | Net at 5 bps a side, members | Break-even cost a side |
| --- | --- | --- | --- | --- |
| every overnight | 4.5 [1.0, 7.5] | 4.2 [0.9, 7.1] | −13.9 %/yr | 2.2 bps |
| every daytime | 0.8 [−1.8, 3.5] | 2.1 [−0.6, 4.9] | −23.2 %/yr | 0.4 bps |
| **Friday close → Monday open** | **0.9 [−9.6, 9.4]** | **0.2 [−10.1, 8.3]** | −4.6 %/yr | 0.5 bps |
| Friday close → Monday close | 3.4 [−8.9, 14.9] | 6.5 [−3.6, 16.3] | −3.3 %/yr | 1.7 bps |
| **Friday open → Monday open** (the fleet's cadence) | 3.8 [−8.4, 14.8] | 2.1 [−9.2, 12.3] | −3.1 %/yr | 1.9 bps |
| turn-of-month sessions | 6.0 [−3.9, 14.6] | 8.0 [−0.9, 16.4] | −1.9 %/yr | 3.0 bps |
| other sessions | 5.1 [−0.5, 10.0] | 5.9 [1.1, 10.4] | — | — |
| pre-holiday sessions (about 10 a year) | **20.7 [5.1, 35.6]** | 15.7 [−0.2, 29.7] | +1.0 %/yr | 10.4 bps |

Of the members' 2017–2026 log return, **91 % arrived overnight** and 10 % in the daytime; weekend
overnights carried 2 %. On SPY 1993–2016, unseen by the first script: overnight +3.93 bps (t 4.80),
daytime +0.21 (t 0.17); Friday close → Monday open +5.67 (t 2.90), gone in 2017–2026 (+0.32, t 0.08);
Friday open → Monday open +3.24 (t 0.95) and +2.04 (t 0.37); turn of month +7.92 (t 2.33) against
+3.25 elsewhere; pre-holiday +7.23 (t 1.03). **94 % of SPY's 1993–2026 log return arrived overnight.**

**Q3 — correlated catch-up, pairs correlated 0.6 or more, excess over all members, bps per trade [95 %].**

| Signal → trade | Hold 1 | Hold 5 | Trades a year |
| --- | --- | --- | --- |
| peer up ≥ 3 %, ticket lagged ≥ 2.5 % → buy the laggard | −1.6 [−9.0, 5.2] | +1.6 [−11.0, 14.3] | ~1,370 |
| peer down ≤ −3 %, ticket held up ≥ 2.5 % → buy the holdout | +2.1 [−5.8, 10.7] | +4.9 [−15.6, 27.3] | ~1,220 |
| peer outran ticket ≥ 5 % over 5 days → buy the laggard | +3.8 [−0.3, 8.0] | +15.0 [−3.3, 34.4] (halves 24.6, 5.7) | ~5,200 |
| ticket outran peer ≥ 5 % over 5 days → buy the leader | −3.7 [−8.7, 1.1] | −15.7 [−38.2, 3.1] | ~5,100 |

**Q5 — VIX and selling insurance.** VIX stood above the next 21 sessions' realised SPY volatility on
**84.1 %** of days 1993–2026 (8,470 days), by 3.72 points on average (median 4.45), and 83–85 % in each
of three decades. Its worst misses are the crashes: 2020-02-20, VIX 15.6 against 78.9 realised.

| 2007-01-03 → 2026-10-23 | CAGR | Vol | Max drawdown | Sharpe | GFC total | 2022 total |
| --- | --- | --- | --- | --- | --- | --- |
| SPY, total return | 10.89 % | 19.5 % | −55.2 % | 0.63 | −54.8 % | −24.1 % |
| BXM, buy-write (sells a monthly at-the-money call) | 6.04 % | 14.2 % | −40.1 % | 0.48 | −38.9 % | −17.0 % |
| PUT, put-write (sells a monthly at-the-money put) | 7.26 % | 13.8 % | −37.1 % | 0.58 | −34.7 % | −13.6 % |

**Overnight-only SPY** (bought at each close, sold at the next open):

| | 1994–2016 | 2017–2026 | 1994–2026 |
| --- | --- | --- | --- |
| SPY held: CAGR · vol · max drawdown · Sharpe | 9.06 % · 19.0 · −55.2 · 0.55 | 15.10 % · 18.1 · −33.7 · 0.87 | 10.83 % · 18.7 · −55.2 · 0.64 |
| overnight, 0 bps | 9.65 % · 10.3 · −32.8 · **0.95** | 10.86 % · 11.6 · −29.4 · 0.94 | 10.01 % · 10.7 · −32.8 · **0.95** |
| overnight, 0.5 bps a side | 6.92 % · 0.70 | 8.10 % · 0.73 | 7.27 % · 0.71 |
| overnight, 1 bp a side | 4.26 % · 0.46 | 5.41 % · 0.51 | 4.60 % · 0.47 |
| overnight, 2 bps a side | −0.86 % · −0.03 | 0.23 % · 0.08 | −0.54 % · 0.00 |
| overnight, 1 bp, only above the 200-day | 5.62 % · 6.4 · −15.1 · 0.89 | 6.77 % · 7.4 · −18.3 · 0.92 | 5.96 % · 6.7 · −18.3 · 0.90 |

**NSPY's life, 2022-06-08 → 2023-07-31:** our overnight series returned **−6.9 %** (daytime +20.7 %,
held +12.4 %). The fund reported −6.9 % since inception against the S&P 500's +22 % and was liquidated
on 2023-07-31 with $3.7 million ([wealthmanagement.com](https://www.wealthmanagement.com/etfs/-night-effect-etfs-to-shut-down-with-overnight-stock-returns-elusive),
[etf.com](https://www.etf.com/sections/news/2-nightshares-etfs-close-after-struggling-gain-traction)).
From 2023-08-01 to 2026-10-23 the overnight series returned +53.6 % and the daytime +12.4 %.

## 7. Conclusions

1. **An exit rule cannot make money out of entries that carry none; it only changes the shape.** The
   +1 % take-profit wins 79 % of trades and earns nothing after costs, because its average loss
   (−3.43 %) is three times its average win (+1.04 %), and it turns capital over eight times as often
   as a 20-session hold. Selling
   after 7 days earns what holding earns (13.4 % against 13.1 % gross) and pays more cost. This is the
   arithmetic of a fair game (no stopping rule changes its expected value), now measured on this
   project's universe.
2. **What guards an individual ticket is the stop, and it is cheap.** A −5 % stop cut the worst 1 % of
   trades from −33 % to −12 %, the tickets losing over 10 % from 8.3 % to 0.6 %, and the worst day's
   batch from −35 % to −7 %. Its price, −3.2 points a year at 5 bps, cannot be told from zero
   ([−7.1, +1.1]). The fleet already has one (the ATR stop, 3.9–7.3 % below entry). **It does not cap
   a gap** (worst trade −46 % behind it): only a ticket's size caps what a gap can take.
3. **What guards the book in a slow crash is the trend guard, and it is insurance, not edge.** Standing
   aside while SPY closes below its 200-day average halved every bear since 1994 (dot-com −45 % →
   −22 %, 2008 −54 % → −13 %, 2022 −26 % → −10 %) and cut the 33-year worst drawdown from −55 % to
   −28 %, with a slightly better Sharpe (0.70 against 0.65). Its price is about 2.7 points of CAGR a
   year, 4.3 in the V-shaped 2017–2026. The VIX guard is not one: it rode the dot-com bear to −53 %.
4. 🪤 **The cache's decade rewards buying weakness, and the decade before it did not.** Entries while
   SPY was below its 200-day average returned +2.28 % over 20 sessions in 2017–2026 against +0.24 % in
   1994–2016. Every replay finding that favours weakness or stress (EXP-012's volatile names, EXP-013's
   stress gradient, EXP-023's weakness lean) may be the decade's, and EXP-014 and EXP-022 score on the
   same window. A rule that wins in the replay by buying dips has not been tested against 2000–02 or 2008.
5. **The operator's four ideas:** the +1 % take-profit loses to holding (interval below zero); the
   7-day hold is neutral before cost and behind after; correlated catch-up does not carry (the one
   lean, +15 bps over 5 days, crosses zero and faded from 24.6 to 5.7 between the halves); Friday to
   Monday earned about nothing in 2017–2026 (+0.2 bps on SPY) and loses after cost, and its 1993–2016
   premium (+5.7 bps) has gone.
6. **Overnight holding is the strongest pattern found, and its whole question is cost.** It held in
   both halves at t 4.8 and 3.0; at zero cost SPY overnight-only earned the market's return with 57 %
   of its volatility (Sharpe 0.95 against 0.64, worst drawdown −33 % against −55 %), but at 1 bp a side
   it falls to 4.6 % a year. A fund built on it lost 6.9 % in 13 months and closed, and our series
   reproduces that loss: the effect is capturable, and it can lag for a year. It needs auction orders
   (Alpaca accepts `opg` and `cls`) and a cost below about half a basis point a side, which nobody here
   has measured.
7. **Selling the insurance VIX overprices did not beat holding.** VIX overstated the next month 84 % of
   the time, yet BXM and PUT trailed SPY by 3.6 to 4.9 points a year since 2007 and still fell 35–39 %
   in 2008. The premium is real; capping the upside in a rising market cost more than it paid.
8. **Can we be better than other similar apps?** Not by seeing the future: nothing here earns more
   than SPY held. Two hard rules beat SPY's risk: the trend guard (half the drawdown, the same Sharpe or
   better, over 33 years) and, if its cost can be made near zero, the overnight hold. Most retail
   trading loses to cost and to crashes; a book that keeps its stop, caps each ticket's size, steps
   aside in a downtrend and trades little would lose less than they do. That is defence, not edge.
9. **What this cannot claim.** About 45 comparisons at 95 %: two or three would pass by chance, and
   pre-holiday is the kind that does. The management rules run on daily bars (a bar touching both
   barriers is the stop; a take-profit fills on a touch unless stated). The cache covers one decade
   and the S&P 500's members only; the long history is SPY alone. Cboe's indices carry no costs.

## 8. Recommended code changes, and how to implement them

**None now.** An exploration does not move code. Three candidates, ranked by the planner, each the
operator's to start ([DL-317](../../design-log.md)):

1. **A market trend guard as the book's hard rule:** no new buys, and held names sold, while SPY closes
   below its 200-day average. First a pre-registration on data nobody here has read: the S&P 500 from
   1975 to 1993 (Cboe's SPX file, downloaded, not analysed) and non-US index histories. Then its cost to
   this book: a replay arm after the fidelity PASS (a new arm kind, so a Codex sprint on the replay
   tooling). Capital-risk policy: the operator's.
2. **The overnight hold, cost first:** measure what SPY's opening and closing auctions would cost
   against the bars this used, from Alpaca's trade prints ($0), before any capital decision.
3. **The fleet's real slippage:** every verdict above turns on whether cost is 5 or 25 bps a side, and
   it has never been measured (EXP-022 §2).

## Appendix P — Pre-registration

None: an exploration (section 2). The questions Q1–Q5 were written before the first run; the
overnight hold and the NSPY check were added after the long-history run showed overnight returns
significant in both halves, and are marked as such here.

## Appendix R — Run record

- 2026-10-24, about 00:50–01:25 UTC: `explore_mgmt.py` (21 s), `explore_long.py`, `explore_overnight.py`;
  repo `main` `5c7f1e08`; each exited 0.
- A fix before the first run: a ticket new to the index has no 200-day history in the cache, and the
  draft counted it as below its average. It is now a third state, left out of the split.

| File (kit) | SHA-256 |
| --- | --- |
| `explore_mgmt.py` | `61bbfed594540c5d521ad31708dc0dfa80f1eb4cf88868b30812a8f6b844b9a6` |
| `explore_long.py` | `37f16d99950550b59a0679e60fc1e163b232551e2c63b0d250e83658161fd674` |
| `explore_overnight.py` | `bc391c8b66a5f1950957e47eee2ce43cfa5961f5401b75323ea646cf798e9b09` |
| `explore_mgmt.json` | `4502b62320ffde74896a26a4228415ef0e9803a882598ab561c44eb462b6f194` |
| `explore_long.json` | `9681564182520d8998231183100a0819764363e96c8d8e305dc378c8274ef24e` |
| `overnight.txt` | `d78216ff75b4247733f1fb0955a31c0ff7b94b78b1194ff5e9d03a511c8a7c16` |

The kit's `.py` files may carry CRLF line endings; Appendix S is LF and equal after normalising.

```text
python explore_mgmt.py <OneDrive>/trading-agents-data <kit>/explore_mgmt.json
python explore_long.py <kit>/inputs/SPY_tiingo.csv <OneDrive>/trading-agents-data/vix.csv.gz <kit>/inputs/BXM.csv <kit>/inputs/PUT.csv <kit>/explore_long.json
python explore_overnight.py <kit>/inputs/SPY_tiingo.csv > <kit>/overnight.txt
```

## Appendix S — Scripts

### `explore_mgmt.py` — families A, B, C, E and the VIX premium on the S235 cache

```python
"""Exploration, NOT a pre-registered test: position-management rules, calendar holds,
correlated catch-up, a market trend guard and the VIX premium, on the S235 S&P 500 cache.

Read-only. Writes aggregates only (never bars: the bars are licensed SIP data).
No pipeline entries are used (EXP-022 stays sealed): every member line is an entry.
Usage: python explore_mgmt.py <cache_dir> <out.json>
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

START, END, SPLIT = "2017-01-03", "2026-09-25", "2022-01-03"
ADJ_ERRORS = {"TGNA": "2017-06-01", "RTX": "2020-04-03", "APTV": "2017-12-05", "SW": "2016-05-16"}
B, SEED, BLOCK, MAXK = 1000, 0, 20, 20
COSTS = (0.0005, 0.0025)  # 5 and 25 bps a side


def load(cache: Path):
    bars = pd.read_csv(cache / "sp500_bars.csv.gz", usecols=["line", "date", "open", "high", "low", "close"])
    sessions = pd.read_csv(cache / "sp500_sessions.csv.gz")["date"].astype(str).tolist()
    lines = sorted(bars["line"].astype(str).unique())
    si = {d: i for i, d in enumerate(sessions)}
    li = {x: j for j, x in enumerate(lines)}
    rows = bars["date"].astype(str).map(si).to_numpy()
    cols = bars["line"].astype(str).map(li).to_numpy()
    mats = {}
    for c in ("open", "high", "low", "close"):
        m = np.full((len(sessions), len(lines)), np.nan)
        m[rows, cols] = bars[c].to_numpy(float)
        mats[c] = m
    sess = np.array(sessions)
    member = np.zeros((len(sessions), len(lines)), bool)
    for r in pd.read_csv(cache / "sp500_membership.csv.gz").astype(str).itertuples():
        if r.line in li:
            member[(sess >= r.first) & (sess <= r.last), li[r.line]] = True
    brk = np.zeros_like(member)
    for line, day in ADJ_ERRORS.items():
        if line in li and day in si:
            brk[si[day], li[line]] = True
    spy = pd.read_csv(cache / "sp500_benchmark.csv.gz").astype({"date": str}).set_index("date").reindex(sessions)
    vix = pd.read_csv(cache / "sp500_vix.csv.gz").astype({"date": str}).set_index("date")["vix_close"].reindex(sessions)
    return sessions, lines, mats, member, brk, spy, vix


def draws(n: int, rng) -> np.ndarray:
    """Stationary block bootstrap index draws (mean block BLOCK, wrapping)."""
    out = np.empty((B, n), np.int64)
    pos = np.arange(n)
    for r in range(B):
        st = rng.random(n) < 1.0 / BLOCK
        st[0] = True
        g = np.cumsum(st) - 1
        first = pos[st]
        base = rng.integers(n, size=len(first))
        out[r] = (base[g] + pos - first[g]) % n
    return out


def ci(v: np.ndarray) -> list[float]:
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def simulate(m, e, j, tp=None, sl=None, trail=None, k_max=5, through=0.0):
    """One rule over entries at the open of session e. Stop wins a bar touching both."""
    O, H, L, C = m["open"], m["high"], m["low"], m["close"]
    n = len(e)
    p0 = O[e, j]
    stop = p0 * (1 - sl) if sl else np.full(n, -np.inf)
    target = p0 * (1 + tp) if tp else np.full(n, np.inf)
    alive = np.ones(n, bool)
    px = np.full(n, np.nan)
    held = np.zeros(n, np.int16)
    why = np.zeros(n, np.int8)  # 1 stop, 2 target, 3 time, 4 bars ended
    last = p0.copy()

    def close_out(mask, price, k, reason):
        nonlocal alive
        px[mask] = price[mask]
        held[mask] = k
        why[mask] = reason
        alive &= ~mask

    for k in range(k_max):
        s = e + k
        o, h, lo, c = O[s, j], H[s, j], L[s, j], C[s, j]
        close_out(alive & np.isnan(c), last, max(k, 1), 4)
        if k > 0:
            close_out(alive & (o <= stop), o, k + 1, 1)
            close_out(alive & (o >= target), o, k + 1, 2)
        close_out(alive & (lo <= stop), stop, k + 1, 1)
        close_out(alive & (h >= target * (1 + through)), target, k + 1, 2)
        last = np.where(alive, c, last)
        if trail:
            stop = np.where(alive, np.maximum(stop, h * (1 - trail)), stop)
    o = O[e + k_max, j]
    close_out(alive & ~np.isnan(o), o, k_max, 3)
    close_out(alive.copy(), last, k_max, 4)
    exit_s = np.where(why == 3, e + k_max, e + held - 1)
    return px / p0 - 1, held.astype(float), why, exit_s


def net(ret, c):
    return (1 + ret) * (1 - c) / (1 + c) - 1


def per_date(values, e_rel, n_dates):
    return np.bincount(e_rel, weights=values, minlength=n_dates)


def family_a(m, member, cb, sessions, spy_up, own_up, rng_draws, e_lo, e_hi, split_i):
    t_idx, j_idx = np.nonzero(member[e_lo - 1 : e_hi - 1])
    t_idx = t_idx + e_lo - 1
    e = t_idx + 1
    ok = ~np.isnan(m["close"][t_idx, j_idx]) & ~np.isnan(m["open"][e, j_idx]) & ~np.isnan(m["close"][e, j_idx])
    e, j = e[ok], j_idx[ok]
    e_rel = e - e_lo
    n_dates = e_hi - e_lo
    rules = {
        "hold-1": dict(k_max=1),
        "hold-5 (7 calendar days)": dict(k_max=5),
        "hold-7": dict(k_max=7),
        "hold-10": dict(k_max=10),
        "hold-20 (baseline)": dict(k_max=20),
        "take +1% or sell at 5": dict(tp=0.01, k_max=5),
        "take +1% or sell at 5, fill 10bp through": dict(tp=0.01, k_max=5, through=0.001),
        "take +1% or sell at 20": dict(tp=0.01, k_max=20),
        "take +1%, stop -5%, 20": dict(tp=0.01, sl=0.05, k_max=20),
        "take +1%, stop -1%, 5": dict(tp=0.01, sl=0.01, k_max=5),
        "take +2% or sell at 5": dict(tp=0.02, k_max=5),
        "take +5%, stop -5%, 20": dict(tp=0.05, sl=0.05, k_max=20),
        "take +10%, stop -5%, 20": dict(tp=0.10, sl=0.05, k_max=20),
        "stop -5% only, 20": dict(sl=0.05, k_max=20),
        "trailing 5%, 20": dict(sl=0.05, trail=0.05, k_max=20),
    }
    results, base = {}, None
    sims = {}
    for name, kw in rules.items():
        ret, held, why, exit_s = simulate(m, e, j, **kw)
        keep = (cb[exit_s, j] - cb[e, j]) == 0
        sims[name] = (ret, held, why, keep)
    keep_all = np.logical_and.reduce([v[3] for v in sims.values()])
    for name, (ret, held, why, _) in sims.items():
        r, h, w, er = ret[keep_all], held[keep_all], why[keep_all], e_rel[keep_all]
        n5, n25 = net(r, COSTS[0]), net(r, COSTS[1])
        srt = np.sort(r)
        k1 = max(1, len(srt) // 100)
        cohort = per_date(r, er, n_dates) / np.maximum(np.bincount(er, minlength=n_dates), 1)
        sums = {k: per_date(v, er, n_dates) for k, v in (("g", r), ("n5", n5), ("n25", n25), ("h", h))}
        h1 = er < (split_i - e_lo)
        res = {
            "trades": int(len(r)),
            "mean_gross_pct": float(r.mean() * 100),
            "win_rate_gross": float((r > 0).mean()),
            "win_rate_net5": float((n5 > 0).mean()),
            "mean_sessions_held": float(h.mean()),
            "rate_gross_pct_yr": float(r.sum() / h.sum() * 252 * 100),
            "rate_net5_pct_yr": float(n5.sum() / h.sum() * 252 * 100),
            "rate_net25_pct_yr": float(n25.sum() / h.sum() * 252 * 100),
            "rate_net5_half1": float(n5[h1].sum() / h[h1].sum() * 252 * 100),
            "rate_net5_half2": float(n5[~h1].sum() / h[~h1].sum() * 252 * 100),
            "p1_trade_pct": float(np.percentile(r, 1) * 100),
            "p01_trade_pct": float(np.percentile(r, 0.1) * 100),
            "cvar1_trade_pct": float(srt[:k1].mean() * 100),
            "worst_trade_pct": float(srt[0] * 100),
            "share_below_-10pct": float((r < -0.10).mean()),
            "share_below_-20pct": float((r < -0.20).mean()),
            "avg_win_pct": float(r[r > 0].mean() * 100),
            "avg_loss_pct": float(r[r <= 0].mean() * 100),
            "worst_cohort_pct": float(cohort.min() * 100),
            "worst_cohort_date": sessions[int(cohort.argmin()) + e_lo],
            "exit_reasons": {lab: float((w == code).mean()) for code, lab in ((1, "stop"), (2, "target"), (3, "time"), (4, "ended"))},
        }
        if name == "hold-20 (baseline)":
            base = sums
        res["_sums"] = sums
        results[name] = res
    for name, res in results.items():
        s = res.pop("_sums")
        diffs = (s["n5"][rng_draws].sum(1) / s["h"][rng_draws].sum(1) - base["n5"][rng_draws].sum(1) / base["h"][rng_draws].sum(1)) * 252 * 100
        res["rate_net5_minus_baseline_ci"] = ci(diffs)
    # The guard split: hold-20 and stop -5% by the market's and the ticket's own 200-session trend at decision.
    guards = {}
    for name in ("hold-20 (baseline)", "stop -5% only, 20", "take +1% or sell at 5"):
        ret, held, _, _ = sims[name]
        r, h = ret[keep_all], held[keep_all]
        t = e[keep_all] - 1
        for gname, flag in (("SPY above its 200-day", spy_up[t].astype(float)), ("ticket above its own 200-day", own_up[t, j[keep_all]])):
            for state in (True, False):
                sel = flag == (1.0 if state else 0.0)
                rr = np.sort(r[sel])
                guards[f"{name} | {gname} = {state}"] = {
                    "trades": int(sel.sum()),
                    "mean_gross_pct": float(rr.mean() * 100),
                    "rate_gross_pct_yr": float(rr.sum() / h[sel].sum() * 252 * 100),
                    "cvar1_trade_pct": float(rr[: max(1, len(rr) // 100)].mean() * 100),
                    "share_below_-10pct": float((rr < -0.10).mean()),
                }
    return results, guards


def series_stats(x: np.ndarray, rng_draws_s, h1: np.ndarray):
    x = np.asarray(x, float)
    ok = ~np.isnan(x)
    per_year = float(ok.sum() / (len(x) / 252))
    boot = np.array([np.nanmean(x[d]) for d in rng_draws_s]) * 1e4
    return {
        "n": int(ok.sum()),
        "mean_bps": float(np.nanmean(x) * 1e4),
        "mean_bps_ci": ci(boot),
        "half1_bps": float(np.nanmean(x[h1]) * 1e4),
        "half2_bps": float(np.nanmean(x[~h1]) * 1e4),
        "win_rate": float((x[ok] > 0).mean()),
        "per_year": per_year,
        "gross_pct_yr": float(np.nanmean(x) * per_year * 100),
        "net5_pct_yr": float((np.nanmean(x) - 2 * COSTS[0]) * per_year * 100),
        "net25_pct_yr": float((np.nanmean(x) - 2 * COSTS[1]) * per_year * 100),
        "breakeven_bps_a_side": float(np.nanmean(x) * 1e4 / 2),
        "worst_pct": float(np.nanmin(x) * 100),
    }


def family_b(m, member, brk, spy, sessions, s_lo, s_hi, split_i, rng):
    O, C = m["open"], m["close"]
    idx = np.arange(s_lo, s_hi)
    prev_mem = member[idx - 1]
    on = O[idx] / C[idx - 1] - 1
    intra = C[idx] / O[idx] - 1
    cc = C[idx] / C[idx - 1] - 1
    bad = brk[idx]
    for a in (on, cc):
        a[bad | ~prev_mem] = np.nan
    intra[~member[idx]] = np.nan
    ew = {"overnight": np.nanmean(on, 1), "intraday": np.nanmean(intra, 1), "close_to_close": np.nanmean(cc, 1)}
    so, sc = spy["open"].to_numpy(float), spy["close"].to_numpy(float)
    sp = {"overnight": so[idx] / sc[idx - 1] - 1, "intraday": sc[idx] / so[idx] - 1, "close_to_close": sc[idx] / sc[idx - 1] - 1}
    dates = pd.to_datetime(pd.Series(sessions))
    gap = (dates.diff().dt.days.to_numpy())[idx]
    wd = dates.dt.weekday.to_numpy()
    prev_fri = wd[idx - 1] == 4
    weekend = prev_fri & (gap >= 3)
    nxt_gap = np.r_[(dates.diff().dt.days.to_numpy())[1:], 1][idx]
    pre_holiday = (nxt_gap >= 2) & ~((wd[idx] == 4) & (nxt_gap == 3))
    month = dates.dt.month.to_numpy()
    first_of_month = np.r_[True, month[1:] != month[:-1]]
    tom = np.zeros(len(sessions), bool)
    for i in np.nonzero(first_of_month)[0]:
        tom[max(i - 1, 0) : i + 3] = True
    tom = tom[idx]
    h1 = idx < split_i
    n = len(idx)
    d = draws(n, rng)
    out = {}
    for src, ser in (("equal-weight members", ew), ("SPY", sp)):
        on_s, id_s, cc_s = ser["overnight"], ser["intraday"], ser["close_to_close"]
        fri_intra = np.full(n, np.nan)
        fri_intra[1:] = id_s[:-1]
        mon_intra = id_s
        cases = {
            "every overnight (close to next open)": on_s,
            "every daytime (open to close)": id_s,
            "weekend: Friday close to Monday open": np.where(weekend, on_s, np.nan),
            "weekend: Friday close to Monday close": np.where(weekend, on_s + mon_intra + on_s * mon_intra, np.nan),
            "weekend, fleet-feasible: Friday open to Monday open": np.where(weekend, (1 + fri_intra) * (1 + on_s) - 1, np.nan),
            "weekday overnights only (Mon-Thu close to next open)": np.where(~weekend & (gap == 1), on_s, np.nan),
            "Monday close to close": np.where(weekend, cc_s, np.nan),
            "turn of month sessions (close to close)": np.where(tom, cc_s, np.nan),
            "other sessions (close to close)": np.where(~tom, cc_s, np.nan),
            "pre-holiday sessions (close to close)": np.where(pre_holiday, cc_s, np.nan),
            "all sessions (close to close)": cc_s,
        }
        out[src] = {k: series_stats(v, d, h1) for k, v in cases.items()}
        tot = np.nansum(np.log1p(cc_s))
        out[src]["_share_of_log_return"] = {
            "overnight": float(np.nansum(np.log1p(on_s)) / tot),
            "daytime": float(np.nansum(np.log1p(id_s)) / tot),
            "weekend overnights": float(np.nansum(np.log1p(np.where(weekend, on_s, np.nan))) / tot),
            "turn of month": float(np.nansum(np.log1p(np.where(tom, cc_s, np.nan))) / tot),
        }
    return out


def family_c(m, member, brk, s_lo, s_hi, split_i, rng):
    O, C = m["open"], m["close"]
    R = C / np.roll(C, 1, 0) - 1
    R[0] = np.nan
    R[brk] = np.nan
    S, N = R.shape
    peer = np.full((S, N), -1)
    pcor = np.full((S, N), np.nan)
    for r in range(s_lo - 1, s_hi, 21):
        cols = np.nonzero(member[r])[0]
        X = R[r - 119 : r + 1, cols]
        good = np.isnan(X).sum(0) <= 10
        cols, X = cols[good], X[:, good]
        X = np.where(np.isnan(X), np.nanmean(X, 0), X)
        Z = (X - X.mean(0)) / X.std(0)
        cor = Z.T @ Z / len(Z)
        np.fill_diagonal(cor, -2)
        best = cor.argmax(1)
        peer[r : r + 21, cols] = cols[best]
        pcor[r : r + 21, cols] = cor[np.arange(len(cols)), best]
    R5 = pd.DataFrame(R).rolling(5).sum().to_numpy()
    out = {}
    t = np.arange(s_lo - 1, s_hi - 6)
    for h in (1, 5):
        fwd = O[t + 1 + h] / O[t + 1] - 1
        crosses = np.zeros_like(fwd, bool)
        for k in range(2, h + 2):
            crosses |= brk[t + k]
        fwd[crosses] = np.nan
        fwd[~member[t]] = np.nan
        xs = fwd - np.nanmean(fwd, 1, keepdims=True)
        pi = peer[t]
        has = pi >= 0
        rp = np.where(has, np.take_along_axis(R[t], np.maximum(pi, 0), 1), np.nan)
        rp5 = np.where(has, np.take_along_axis(R5[t], np.maximum(pi, 0), 1), np.nan)
        ri, ri5 = R[t], R5[t]
        strong = pcor[t] >= 0.6
        conds = {
            "peer up >=3%, ticket lagged by >=2.5% -> buy the laggard": (rp >= 0.03) & (rp - ri >= 0.025),
            "peer down <=-3%, ticket held up by >=2.5% -> buy the holdout": (rp <= -0.03) & (ri - rp >= 0.025),
            "peer outran ticket by >=5% over 5 days -> buy the laggard": (rp5 - ri5 >= 0.05),
            "ticket outran peer by >=5% over 5 days -> buy the leader": (ri5 - rp5 >= 0.05),
        }
        d = draws(len(t), rng)
        h1 = (t + 1) < split_i
        for cname, cond in conds.items():
            sel = cond & strong & ~np.isnan(xs)
            cnt = sel.sum(1).astype(float)
            sx = np.where(sel, xs, 0).sum(1)
            sf = np.where(sel, fwd, 0).sum(1)
            boot = sx[d].sum(1) / np.maximum(cnt[d].sum(1), 1) * 1e4
            out[f"{cname} | hold {h}"] = {
                "trades": int(cnt.sum()),
                "trades_per_year": float(cnt.sum() / len(t) * 252),
                "mean_excess_vs_all_members_bps": float(sx.sum() / max(cnt.sum(), 1) * 1e4),
                "excess_ci_bps": ci(boot),
                "excess_half1_bps": float(sx[h1].sum() / max(cnt[h1].sum(), 1) * 1e4),
                "excess_half2_bps": float(sx[~h1].sum() / max(cnt[~h1].sum(), 1) * 1e4),
                "mean_raw_return_bps": float(sf.sum() / max(cnt.sum(), 1) * 1e4),
                "win_rate_excess": float((xs[sel] > 0).mean()),
            }
    return out


def family_e(spy, vix, sessions, s_lo, s_hi):
    o = spy["open"].to_numpy(float)
    c = spy["close"].to_numpy(float)
    sma = pd.Series(c).rolling(200).mean().to_numpy()
    up = c > sma
    idx = np.arange(s_lo, s_hi - 1)
    seg = o[idx + 1] / o[idx] - 1  # bought at the open of idx, held to the next open

    def stats(r, inmkt):
        eq = np.cumprod(1 + r)
        peak = np.maximum.accumulate(eq)
        yrs = len(r) / 252
        w21 = pd.Series(np.log1p(r)).rolling(21).sum().min()
        return {
            "cagr_pct": float((eq[-1] ** (1 / yrs) - 1) * 100),
            "vol_pct": float(r.std() * np.sqrt(252) * 100),
            "sharpe_rf0": float(r.mean() / r.std() * np.sqrt(252)),
            "max_drawdown_pct": float((eq / peak - 1).min() * 100),
            "worst_21_sessions_pct": float(np.expm1(w21) * 100),
            "time_in_market": float(inmkt.mean()),
        }

    inm = up[idx - 1]
    switches = int(np.abs(np.diff(inm.astype(int))).sum())
    guarded = np.where(inm, seg, 0.0)
    cost = np.zeros(len(idx))
    cost[1:][np.diff(inm.astype(int)) != 0] = COSTS[0]
    vix_ok = (vix.to_numpy(float) <= 30)[idx - 1]
    return {
        "SPY held throughout": stats(seg, np.ones(len(idx), bool)),
        "SPY only while above its 200-day average (5 bps a switch)": stats(guarded - cost, inm) | {"switches": switches},
        "SPY only while VIX <= 30": stats(np.where(vix_ok, seg, 0.0), vix_ok),
    }, up


def vix_premium(spy, vix, sessions, s_lo, s_hi):
    c = spy["close"].to_numpy(float)
    lr = np.log(c[1:] / c[:-1])
    lr = np.r_[np.nan, lr]
    rows = []
    for s in range(s_lo, s_hi - 21):
        rv = np.sqrt(np.sum(lr[s + 1 : s + 22] ** 2) * 252 / 21) * 100
        rows.append((sessions[s], float(vix.iloc[s]), rv))
    df = pd.DataFrame(rows, columns=["date", "vix", "rv"])
    df["gap"] = df["vix"] - df["rv"]
    df["year"] = df["date"].str[:4]
    worst = df.nsmallest(3, "gap")
    return {
        "days": int(len(df)),
        "mean_vix": float(df.vix.mean()),
        "mean_realised_next_21": float(df.rv.mean()),
        "mean_gap_pts": float(df.gap.mean()),
        "median_gap_pts": float(df.gap.median()),
        "share_vix_above_realised": float((df.gap > 0).mean()),
        "worst_gaps": [{"date": r.date, "vix": r.vix, "realised": round(r.rv, 1)} for r in worst.itertuples()],
        "by_year_share_vix_above": df.groupby("year")["gap"].apply(lambda g: round(float((g > 0).mean()), 3)).to_dict(),
        "by_year_mean_gap": df.groupby("year")["gap"].mean().round(2).to_dict(),
    }


def main() -> None:
    cache, out = Path(sys.argv[1]), Path(sys.argv[2])
    t0 = time.time()
    sessions, lines, m, member, brk, spy, vix = load(cache)
    si = {d: i for i, d in enumerate(sessions)}
    s_lo, s_end, split_i = si[START], si[END] + 1, si[SPLIT]
    cb = np.cumsum(brk, axis=0)
    print(f"loaded {len(sessions)} sessions x {len(lines)} lines in {time.time() - t0:.0f}s", flush=True)
    rng = np.random.default_rng(SEED)
    guard, spy_up = family_e(spy, vix, sessions, s_lo, s_end)
    own_sma = pd.DataFrame(m["close"]).rolling(200, min_periods=200).mean().to_numpy()
    own_up = np.where(np.isnan(own_sma), np.nan, (m["close"] > own_sma).astype(float))
    e_hi = len(sessions) - 1 - MAXK
    a_draws = draws(e_hi - s_lo, rng)
    a, a_guards = family_a(m, member, cb, sessions, spy_up, own_up, a_draws, s_lo, e_hi, split_i)
    print(f"family A done {time.time() - t0:.0f}s", flush=True)
    b = family_b(m, member, brk, spy, sessions, s_lo, s_end, split_i, rng)
    print(f"family B done {time.time() - t0:.0f}s", flush=True)
    c = family_c(m, member, brk, s_lo, s_end, split_i, rng)
    print(f"family C done {time.time() - t0:.0f}s", flush=True)
    v = vix_premium(spy, vix, sessions, s_lo, s_end)
    result = {
        "status": "EXPLORATION, not a pre-registered test: ~45 comparisons on one decade; a pass here is a hypothesis",
        "window": [START, END],
        "split": SPLIT,
        "costs_a_side": COSTS,
        "bootstrap": {"B": B, "seed": SEED, "mean_block": BLOCK},
        "A_management_rules_on_every_member_entry": a,
        "A_guard_split": a_guards,
        "B_calendar": b,
        "C_correlated_catch_up": c,
        "E_market_guard": guard,
        "V_vix_premium": v,
        "seconds": round(time.time() - t0, 1),
    }
    out.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(f"wrote {out} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
```

### `explore_long.py` — SPY 1993–2026, Cboe BXM and PUT, VIX by decade

```python
"""Exploration, NOT a pre-registered test: the same questions on index-level history 1993-2026,
which holds the slow crashes (2000-02, 2008) the S&P cache's decade lacks.

Inputs: SPY adjusted daily (Tiingo), Cboe VIX close (1990-), Cboe BXM and PUT index closes.
1993-2016 is out of sample relative to explore_mgmt.py's 2017-2026 window.
Usage: python explore_long.py <spy.csv> <vix.csv.gz> <BXM.csv> <PUT.csv> <out.json>
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

COST = 0.0005
PERIODS = {
    "1994-2026 whole": ("1994-01-03", "2026-10-23"),
    "1994-2016 (outside the cache's decade)": ("1994-01-03", "2016-12-30"),
    "2017-2026 (the cache's decade)": ("2017-01-03", "2026-10-23"),
    "dot-com bear 2000-03..2003-03": ("2000-03-24", "2003-03-11"),
    "GFC 2007-10..2009-03": ("2007-10-09", "2009-03-09"),
    "COVID 2020-02..2020-03": ("2020-02-19", "2020-03-23"),
    "2022 bear": ("2022-01-03", "2022-10-12"),
}


def stats(r: pd.Series) -> dict:
    r = r.dropna()
    eq = (1 + r).cumprod()
    yrs = len(r) / 252
    return {
        "total_pct": round(float((eq.iloc[-1] - 1) * 100), 1),
        "cagr_pct": round(float((eq.iloc[-1] ** (1 / yrs) - 1) * 100), 2) if yrs >= 1 else None,
        "vol_pct": round(float(r.std() * np.sqrt(252) * 100), 1),
        "max_drawdown_pct": round(float((eq / eq.cummax() - 1).min() * 100), 1),
        "sharpe_rf0": round(float(r.mean() / r.std() * np.sqrt(252)), 2),
    }


def main() -> None:
    spy_p, vix_p, bxm_p, put_p, out_p = sys.argv[1:6]
    s = pd.read_csv(spy_p, parse_dates=["date"]).set_index("date")
    s.index = s.index.tz_localize(None) if s.index.tz is not None else s.index
    o, c = s["adjOpen"], s["adjClose"]
    vix = pd.read_csv(vix_p, parse_dates=["date"]).set_index("date")["vix_close"].reindex(s.index).ffill()
    res: dict = {"status": "EXPLORATION, index level, 1993-2026"}

    # 1. Market guards, open to open, decided at the previous close.
    seg = o.shift(-1) / o - 1
    up = (c > c.rolling(200).mean()).shift(1)
    calm = (vix <= 30).shift(1)
    sw = up.astype(float).diff().abs().fillna(0)
    arms = {
        "SPY held": seg,
        "SPY only above its 200-day (5 bps a switch)": seg.where(up == True, 0.0) - sw * COST,  # noqa: E712
        "SPY only while VIX <= 30": seg.where(calm == True, 0.0),  # noqa: E712
    }
    res["guards"] = {
        p: {a: stats(r.loc[lo:hi]) for a, r in arms.items()} for p, (lo, hi) in PERIODS.items()
    }
    res["guards_switches_1994_2026"] = int(sw.loc["1994":].sum())

    # 2. Calendar effects on SPY, split at 2017 (1993-2016 never seen by explore_mgmt.py).
    on = o / c.shift(1) - 1
    day = c / o - 1
    cc = c / c.shift(1) - 1
    dts = pd.Series(s.index, index=s.index)
    gap = dts.diff().dt.days
    wd = dts.dt.weekday
    weekend = (wd.shift(1) == 4) & (gap >= 3)
    nxt = gap.shift(-1)
    pre_hol = (nxt >= 2) & ~((wd == 4) & (nxt == 3))
    first = dts.dt.month != dts.dt.month.shift(1)
    tom = first | first.shift(-1, fill_value=False) | first.shift(1, fill_value=False) | first.shift(2, fill_value=False)
    fri_open_mon_open = ((1 + day.shift(1)) * (1 + on) - 1).where(weekend)
    cases = {
        "every overnight": on,
        "every daytime": day,
        "weekend Fri close -> Mon open": on.where(weekend),
        "weekend Fri open -> Mon open": fri_open_mon_open,
        "weekday overnights": on.where(~weekend & (gap == 1)),
        "turn of month sessions": cc.where(tom),
        "other sessions": cc.where(~tom),
        "pre-holiday sessions": cc.where(pre_hol),
    }
    cal = {}
    for name, x in cases.items():
        row = {}
        for lab, lo, hi in (("1993-2016", "1993-02-01", "2016-12-30"), ("2017-2026", "2017-01-03", "2026-10-23")):
            v = x.loc[lo:hi].dropna()
            row[lab] = {
                "n": int(len(v)),
                "mean_bps": round(float(v.mean() * 1e4), 2),
                "t": round(float(v.mean() / v.std() * np.sqrt(len(v))), 2),
                "win": round(float((v > 0).mean()), 3),
            }
        cal[name] = row
    tot = np.log1p(cc.loc["1993-02-01":]).sum()
    cal["_share_of_log_return_1993_2026"] = {
        "overnight": round(float(np.log1p(on.loc["1993-02-01":]).sum() / tot), 3),
        "daytime": round(float(np.log1p(day.loc["1993-02-01":]).sum() / tot), 3),
        "weekend overnights": round(float(np.log1p(on.where(weekend).loc["1993-02-01":]).sum() / tot), 3),
    }
    res["calendar_spy"] = cal

    # 3. Twenty-session SPY holds entered at each open: buy-and-hold vs a -5% stop, split by the
    #    200-day state at the decision close. Is "entries below the trend earn more" only 2017-2026's?
    O, H, L = s["adjOpen"].to_numpy(), s["adjHigh"].to_numpy(), s["adjLow"].to_numpy()
    n = len(O)
    upn = (c > c.rolling(200).mean()).to_numpy()
    rows = []
    for e in range(201, n - 21):
        p0, stop = O[e], O[e] * 0.95
        ret_h = O[e + 20] / p0 - 1
        ret_s = None
        for k in range(20):
            if k > 0 and O[e + k] <= stop:
                ret_s = O[e + k] / p0 - 1
                break
            if L[e + k] <= stop:
                ret_s = -0.05
                break
        if ret_s is None:
            ret_s = ret_h
        rows.append((s.index[e], upn[e - 1], ret_h, ret_s))
    df = pd.DataFrame(rows, columns=["date", "up", "hold", "stop"]).set_index("date")
    hs = {}
    for lab, lo, hi in (("1994-2016", "1994-01-03", "2016-12-30"), ("2017-2026", "2017-01-03", "2026-10-23"),
                        ("2000-03..2003-03", "2000-03-24", "2003-03-11"), ("2007-10..2009-03", "2007-10-09", "2009-03-09")):
        d = df.loc[lo:hi]
        for state in (True, False):
            x = d[d["up"] == state]
            if len(x) == 0:
                continue
            hs[f"{lab} | SPY above 200-day = {state}"] = {
                "n": int(len(x)),
                "hold20_mean_pct": round(float(x["hold"].mean() * 100), 2),
                "hold20_p5_pct": round(float(x["hold"].quantile(0.05) * 100), 1),
                "stop5_mean_pct": round(float(x["stop"].mean() * 100), 2),
                "stop5_p5_pct": round(float(x["stop"].quantile(0.05) * 100), 1),
            }
    res["spy_20_session_holds"] = hs

    # 4. Selling the insurance: Cboe BXM (buy-write) and PUT (put-write) vs SPY total return.
    def idx(path, col):
        d = pd.read_csv(path)
        d["DATE"] = pd.to_datetime(d["DATE"], format="%m/%d/%Y")
        return d.set_index("DATE")[col]

    bxm, put = idx(bxm_p, "BXM"), idx(put_p, "PUT")
    common = c.index.intersection(bxm.index).intersection(put.index)
    common = common[common >= "2007-01-03"]
    tr = {"SPY total return": c.reindex(common), "BXM buy-write": bxm.reindex(common), "PUT put-write": put.reindex(common)}
    ins = {}
    for p, (lo, hi) in PERIODS.items():
        if pd.Timestamp(hi) < common[0]:
            continue
        lo = max(pd.Timestamp(lo), common[0])
        ins[p if lo == pd.Timestamp(PERIODS[p][0]) else f"{p} (from {lo.date()})"] = {
            k: stats(v.pct_change().loc[lo:hi]) for k, v in tr.items()
        }
    res["insurance_sellers_vs_spy"] = ins

    # 5. VIX against the next 21 sessions' realised SPY volatility, by decade.
    lr = np.log(c / c.shift(1))
    rv = np.sqrt((lr**2).rolling(21).sum().shift(-21) * 252 / 21) * 100
    g = (vix - rv).dropna()
    vp = {}
    for lab, lo, hi in (("1993-2001", "1993-02-01", "2001-12-31"), ("2002-2011", "2002-01-01", "2011-12-31"),
                        ("2012-2026", "2012-01-01", "2026-12-31"), ("all", "1993-02-01", "2026-12-31")):
        x = g.loc[lo:hi]
        vp[lab] = {"days": int(len(x)), "mean_gap_pts": round(float(x.mean()), 2),
                   "median_gap_pts": round(float(x.median()), 2), "share_vix_above": round(float((x > 0).mean()), 3)}
    worst = g.nsmallest(400)
    vp["_worst_episodes"] = sorted({str(d.date())[:7] for d in worst.index})
    res["vix_premium"] = vp
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, default=str)
    print("wrote", out_p)


if __name__ == "__main__":
    main()
```

### `explore_overnight.py` — overnight-only SPY and the NSPY window

```python
"""Exploration, NOT a pre-registered test: SPY held only overnight (close to next open) at auction
costs, with and without the 200-day guard, and the NightShares 500 (NSPY) window as a check that
the measured overnight return is the one a fund could capture.

Usage: python explore_overnight.py <spy_tiingo.csv>
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd


def stats(r: pd.Series) -> str:
    r = r.dropna()
    eq = (1 + r).cumprod()
    y = len(r) / 252
    return (
        f"cagr={(eq.iloc[-1] ** (1 / y) - 1) * 100:6.2f} vol={r.std() * np.sqrt(252) * 100:5.1f} "
        f"mdd={(eq / eq.cummax() - 1).min() * 100:6.1f} sharpe={r.mean() / r.std() * np.sqrt(252):5.2f}"
    )


def main() -> None:
    s = pd.read_csv(sys.argv[1], parse_dates=["date"]).set_index("date")
    o, c = s["adjOpen"], s["adjClose"]
    on = o / c.shift(1) - 1
    day = c / o - 1
    held = c / c.shift(1) - 1
    up = (c > c.rolling(200).mean()).shift(1)
    for lab, lo, hi in (("1994-2016", "1994-01-03", "2016-12-30"), ("2017-2026", "2017-01-03", "2026-10-23"),
                        ("1994-2026", "1994-01-03", "2026-10-23")):
        print(lab)
        print("   SPY held (close to close)      ", stats(held.loc[lo:hi]))
        for bps in (0, 0.5, 1, 2):
            print(f"   overnight only, {bps:3.1f} bp a side  ", stats((on - 2 * bps / 1e4).loc[lo:hi]))
        print("   overnight only 1bp + 200-day    ", stats((on - 2e-4).where(up == True, 0.0).loc[lo:hi]))  # noqa: E712
    for lo, hi in (("2022-06-08", "2023-07-31"), ("2023-01-03", "2023-07-31"), ("2023-08-01", "2026-10-23")):
        def total(r: pd.Series) -> str:
            return f"{((1 + r.loc[lo:hi]).prod() - 1) * 100:6.1f}%"

        print(lo, hi, "overnight", total(on), " daytime", total(day), " held", total(held))


if __name__ == "__main__":
    main()
```
