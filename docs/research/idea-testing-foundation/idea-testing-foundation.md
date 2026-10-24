# How every idea is tested: the foundation, the funnel and the catalogue

**Date:** 2026-10-24 (planner) · **Asked by:** the operator, 2026-10-24: *"You should be able to come up
with a theoretical foundation for testing. Let's test every idea (no matter how strange it may sound at
first glance)"* · **Feeds:** [DL-319](../../design-log.md), [EXP-029](../experiments/EXP-029-do-calendar-and-natural-signals-move-the-us-market-over-a-century.md) onward

## 1. Where an edge can come from (the theory)

A rule earns more than the market only if someone else, on average, earns less, or if it is paid for
bearing a risk others will not. Every idea belongs to one of five sources, and the source sets how
likely it is to survive:

| Source | Mechanism | Why it can persist | Examples |
| --- | --- | --- | --- |
| **Risk premium** | paid for holding what others avoid | the risk is real; the payment is the price of insurance | the equity premium, volatility selling, illiquidity |
| **Behaviour** | mood, attention, heuristics move prices away from value | arbitrage is costly or risky (limits to arbitrage) | weather and mood, superstition, lottery stocks, overreaction |
| **Flows** | trades made for reasons other than value | the flow recurs on a schedule | month-end pay and pension flows, index rebalancing, tax-loss selling, option expiry |
| **Information** | news reaches prices slowly | reading it costs more than the gain to most | insider filings, text changes, distant news |
| **Microstructure** | who trades at which hour | clienteles differ by time of day | the overnight premium, closing auctions |

**What kills an edge:** cost (it must exceed the round trip), capacity (irrelevant at this book's size),
publication (others trade it away: Sharpe ratios about halve, R011), and luck (it was never there).

## 2. The funnel every idea passes through

1. **State it before looking.** The rule, its data, the direction the literature or the folklore
   predicts, and the comparison, committed before its return is computed.
2. **Discovery on old data, with the false-discovery rate controlled.** All ideas of a batch are tested
   together on the discovery period; Benjamini–Hochberg at q = 10 % across the batch decides which
   go on. A strange idea gets exactly the bar a plausible one gets.
3. **Confirmation on data the discovery never touched.** A passing idea is re-tested, same rule, same
   direction, one-sided, Holm across the batch's passers at 5 %.
4. **The economic bar.** A confirmed idea is turned into a trade (hold on favourable days, or step
   aside on unfavourable ones) and must beat holding the market's Sharpe after a realistic cost.
5. **Only then is it built**, in paper, with the operator's word.

**Data hygiene, always:** a signal uses only what was known before the trade (weather or mood on the
same day is a mechanism test, not a trade); universes are point-in-time; an LLM is scored only on text
after its training cutoff.

## 3. The catalogue, by data and batch

| Batch | Ideas | Data | Status |
| --- | --- | --- | --- |
| **1. Calendar and nature, a century of the US market** | weekday, pre-holiday, turn of month, Halloween, January small caps, Santa Claus, option expiry, quarter end, first day of the year, first half of the month; the presidential cycle, party in office, the midterm year; new against full moon, sunshine, rain, snow, cold, heat in New York, geomagnetic storms, sunspots, daylight-saving Mondays, autumn (seasonal mood); Friday the 13th; after a big down day, after a big up day, after three down days | Ken French daily market and size deciles 1926 →, NOAA Central Park, GFZ Potsdam Kp/Ap | [EXP-029](../experiments/EXP-029-do-calendar-and-natural-signals-move-the-us-market-over-a-century.md): **done**, 1 of 28 confirms, none economic |
| 2. Headlines read by an LLM after its cutoff | good and bad news, next day, overnight, early read | Benzinga archive 2024 → | [EXP-028](../experiments/EXP-028-does-an-llm-reading-headlines-after-its-cutoff-predict-the-next-day.md) (running) |
| 3. The cross-section, cheap | 52-week high, lottery (MAX) stocks, round-number prices, post-split drift, index inclusion, same-month seasonality, news volume and attention, ticker fluency | the S235 cache, the Benzinga archive | [EXP-030](../experiments/EXP-030-do-seventeen-stock-level-signals-sort-the-sp-500-month-to-month.md): **done**, 0 of 17 pass discovery (post-split drift needs raw bars: queued) |
| 4a. Events in headlines | analyst calls, price targets, initiations, buybacks, dividends, splits, guidance, beats, misses, CEO exits, FDA approvals, legal trouble | the Benzinga archive | [EXP-031](../experiments/EXP-031-do-corporate-events-in-headlines-predict-the-next-month.md): **done**, 0 of 14 pass discovery |
| 4b. The FOMC cycle | announcement day, the day before, even weeks | the Fed's pages, SPY | [EXP-032](../experiments/EXP-032-does-the-fomc-cycle-still-move-the-market.md): **done**, reproduces in-sample, gone after |
| 4. Events and filings (rest) | FOMC days (done, 4b), earnings-announcement premium, 13F copying, congressional trades, short interest, filing text changes | Fed calendar, SEC EDGAR, FINRA, House and Senate disclosures | queued |
| 5a. Crypto calendar | weekend, Monday, turn of month, Moon, Halloween, after ±5 % days | Coinbase BTC | [EXP-033](../experiments/EXP-033-do-calendar-and-strange-signals-move-bitcoin.md): **done**, 0 of 7 |
| 5. Other markets (rest) | crypto weekday and weekend (done, 5a), crypto–equity spillover, commodity seasonality, currency carry with ETFs | Coinbase, Tiingo ETFs | queued |
| Excluded until defined | the Super Bowl indicator (which teams count as "NFC" is ambiguous before 1970; 60 yearly observations); Mercury retrograde (needs an ephemeris: queued for batch 3) | — | — |

**Already settled** (not re-tested): price-only stock ranking (EXP-015, EXP-023), news tone by lexicon
or FinBERT (EXP-024), exits and stops (EXP-025), nine published allocations (EXP-026), insider
purchases (EXP-027).
