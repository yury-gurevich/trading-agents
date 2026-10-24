# Where can an edge still exist for this project? What the field knows, and Microsoft's RD-Agent beside us

**Date:** 2026-10-24 (planner) · **Asked by:** the operator, 2026-10-24: *"actively research methods that
may work for us … what do people know that we do not. there is a microsoft repo that does approximately
the same job, but uses slightly different approach"*, then *"I need a path that is at least promising,
otherwise we should abandon the project"* · **Feeds:** [DL-317](../../design-log.md) · **Cost:** $0
(web research; no data bought, no LLM run)

## 1. The finding in one paragraph

Three independent lines say the arena this project chose (S&P 500 large caps, daily public prices and
news tone, long only) holds no edge that survives costs: **our own 25 experiments** (no ranking skill,
no sentiment, exits only reshape outcomes: EXP-015, EXP-023, EXP-024, EXP-025), **the literature**
(published anomalies earned a median 7 bp a month in non-micro stocks after 2005, "eliminated by even
modest allowances for luck or transaction costs": Chen and Welch, 2026), and **Microsoft's own
automated version of this work** (RD-Agent(Q): IC 0.016 on the NASDAQ 100 in 2024–2025). The method
is not what failed; the arena is the most competed corner of the market. What the field knows and we
did not use: edges that remain sit in **information that is slow to be priced** (insider purchases,
filing changes), in **capacity** (stocks too small for funds), in **bearing risk**, and in **cost**.

## 2. What people know that we did not act on

| What is known | Evidence | What it means here |
| --- | --- | --- |
| Published anomalies have been of little use outside micro caps since 2005 | Chen and Welch, *What Useful Alphas?* (arXiv 2607.06502, July 2026): ~200 published long-short portfolios; median 48 bp/month all stocks to 2005, 19 bp after; **non-micro (top 3,000, 90 % of cap) 26 bp, after 2005 7 bp** | Our null results are the expected result in our universe, not a defect in our tools |
| Anomalies decay after publication | McLean and Pontiff (97 predictors: −58 % post-publication); Jacobs and Müller (JFE 2020: the US is the only one of 39 markets with a reliable post-publication decline); a 72-strategy study: Sharpe halves after publication (arXiv 2105.01380) | A method from a paper is, on average, half as good when we test it, and in US large caps less than that |
| Post-earnings drift is gone in large caps | Martineau, *Rest in Peace PEAD* (CFR): non-existent since 2006 outside micro caps; contested by two 2025 papers | Not a candidate in our universe |
| Machine-learning stock picking earns mostly in hard-to-trade stocks | Gu, Kelly and Xiu (RFS 2020): out-of-sample Sharpe 1.35 long-short, S&P 500 timing 0.77 vs 0.51; Avramov, Cheng and Metzker (Mgmt Sci 2023): **profits fall 62 % without micro caps**, further with costs; still positive on the long side | A better model of the same prices in large caps would not have rescued EXP-015 |
| An LLM's backtest leaks the future it was trained on | *Detecting Lookahead Bias in LLM Forecasts* (arXiv 2512.23847): the headline signal's lookahead measure collapses after the training cutoff; on 2024 post-cutoff news the raw signal still predicted (coefficient ~0.36, t ~3.6, ~7,568 observations); DatedGPT (2026) trains year-cut models for clean tests | Any LLM signal is scored only on dates after the model's cutoff; the next-day news effect sits mostly at the open, which our next-open fills do not capture |
| Automated search multiplies false discoveries | Deflated Sharpe ratio and the probability of backtest overfitting (Bailey and López de Prado); `purgedcv` implements CPCV, PBO and DSR | Our pre-registration with Holm or Bonferroni is the stricter form; keep it for every automated search |
| Replicated factor data is free | Jensen, Kelly and Pedersen (JF 2023): 153 factors, 13 themes, 93 countries, **universes All / Mega / Large / Small / Micro**, capped value weights, to Dec 2025, CC BY-NC 4.0, form download at jkpfactors.com; Open Source Asset Pricing (Chen and Zimmermann): 212 predictors, `openassetpricing` Python package | Screen published methods in the Mega and Large universes before building any of them |
| Insiders' open-market purchases carry information | Cohen, Malloy and Pomorski (JF 2012): opportunistic insiders' trades predict returns; cluster purchases ~3.8 % vs 2 % over 21 days (1986–2016); strongest in smaller firms; post-2010 large-cap evidence thin | The one information source never tested here, free from the SEC (2006 Q1 → 2026 Q3, structured Form 3/4/5) |
| Investors are slow to read filing changes | Cohen, Malloy and Nguyen, *Lazy Prices* (JF 2020): firms that change their 10-K language underperform, up to 188 bp/month long-short (1995–2014), returns arrive with later news; replication since 2014 unknown | Free from EDGAR; text comparison, no LLM needed; the agents' natural work |
| Retail herding reverses | Barber, Huang, Odean and Schwarz: top Robinhood-bought names −3 % over 5 days (−6 % extreme), mostly small caps | An avoid rule at most; no free point-in-time data |

## 3. Microsoft's RD-Agent(Q) beside this project

**What it is.** [RD-Agent](https://github.com/microsoft/RD-Agent) (NeurIPS 2025, arXiv 2505.15155) runs
an LLM research loop on Qlib: a research agent proposes a factor or model hypothesis, a coding agent
(Co-STEER) writes it, Qlib backtests it, feedback picks the next direction (a multi-armed bandit).
About 44 loops in 12 hours, under $10 a run.

**How it differs from ours.** We let the LLM *propose within a bounded catalogue* and score it with a
deterministic harness, and we pre-register every test ([R001](../qlib-integration/INDEX.md) Q5,
S113/S115); RD-Agent lets the LLM *write the factor code* and keeps whatever its validation window
favours.

**What its results say** (read from the paper 2026-10-24):

| Market and test window | RD-Agent(Q) | Baseline |
| --- | --- | --- |
| CSI 300 (Chinese large caps), test 2017-01 → 2020-08, o3-mini | IC 0.0532, annualised return 14.2 %, IR 1.74, MDD −7.4 % | Alpha158 IC 0.0341, 5.7 %, IR 0.85 |
| **NASDAQ 100, test 2024 → 2025-06**, o4-mini | **IC 0.0162**, IR 1.77, no return reported | — |

No confidence intervals (the authors say so), no correction for the loops tried, a daily long-short
book. Its strong result is in a market dominated by retail traders; in US large caps its IC is the
size our own experiments measured and could not tell from zero. **Adopting it would generate more
candidates in the same exhausted arena.** It could serve later as a hypothesis generator for the
information path, inside our pre-registration (it needs Python ≤ 3.12 for Qlib: a separate
environment).

**The look-alike, TradingAgents** (UCLA and Tauric Research, arXiv 2412.20138, not Microsoft): analyst,
bull and bear researchers, trader and risk agents, the shape of our own fleet. Its backtest window is
short, it has no published live record, its orders go to a simulated exchange, and an LLM's backtest
is exposed to lookahead. Nothing in it is evidence of an edge.

## 4. Paths, ranked by promise

1. **The information path (promising, unproven).** Insider open-market purchases first (SEC Form 4,
   free, 2006 →), then filing changes (*Lazy Prices*, EDGAR). It is the one class of input never
   tested here, the literature's mechanism (insiders know more; inattention) differs from everything
   ruled out, and reading documents is what an agent fleet is for. Long-only buys, individual tickets,
   daily cadence: it fits the fleet. **Weakness:** the evidence is strongest in smaller firms and thin
   for US large caps after 2010.
2. **Capacity: mid and small caps (S&P 400/600).** Where published effects still pay (all stocks after
   2005: 19 bp against 7 bp non-micro) and where a $100,000 book can trade what funds cannot. Pairs
   with the information path. **Weakness:** wider spreads, and a point-in-time membership history to
   build (R008's Wikipedia method extends to both indices).
3. **Defence ([EXP-025](../experiments/EXP-025-which-way-of-managing-a-position-guards-against-a-bad-future.md)).** A 200-day guard halved every bear since 1994 at ~2.7 points of CAGR. Robust,
   but it is the index with insurance, not an edge.
4. **Screen before building.** For any of the above, read the JKP Mega and Large universes and the
   Open Source Asset Pricing returns first ($0), so the project tests only what has survived
   elsewhere.

**Ruled out as paths to an edge** (each measured here or in the literature): more price-based ranking
in large caps; sentiment by lexicon or FinBERT; exit rules on unskilled entries; weekend, turn-of-month
and VIX rules; PEAD in large caps; adopting RD-Agent in this universe; selling index options premium
(BXM/PUT trailed SPY 2007–2026).

## 5. How to test the information path without fooling ourselves

1. **Explore on half, seal the other half.** Insider purchases on the S&P 500 cache, 2017–2021 only;
   2022–2026 is neither downloaded nor read. Entry at the open after the filing date (a Form 4 can be
   filed until 22:00 ET); forward excess over all members at 5, 20 and 60 sessions; any purchase,
   cluster purchases (two or more insiders within 30 days), officer purchases. $0, a planner script.
   **Needs:** an SEC User-Agent with a contact address (the SEC refuses anonymous downloads: 403
   measured 2026-10-24).
2. **Pre-register on the sealed half** (EXP-026) only if the exploration clears a bar fixed now: a
   mean 20-session excess of at least +1 % after 25 bps a side, positive in at least 4 of 5 years.
3. **Kill rule, agreed before anything is read:** if the exploration misses its bar, or EXP-026 fails,
   the search for a trading edge ends.

## Sources

- Chen and Welch, *What Useful Alphas?*, arXiv 2607.06502 (2026): <https://arxiv.org/abs/2607.06502>
- R&D-Agent-Quant, arXiv 2505.15155 (NeurIPS 2025): <https://arxiv.org/html/2505.15155v2>; code <https://github.com/microsoft/RD-Agent>
- TradingAgents, arXiv 2412.20138: <https://arxiv.org/abs/2412.20138>
- Jensen, Kelly and Pedersen, *Is There a Replication Crisis in Finance?* (JF 2023): <https://www.nber.org/papers/w28432>; data <https://jkpfactors.com/data>
- Open Source Asset Pricing: <https://www.federalreserve.gov/econres/feds/open-source-cross-sectional-asset-pricing.htm>; downloader <https://github.com/mk0417/open-asset-pricing-download>
- Strategy decay after publication, arXiv 2105.01380: <https://arxiv.org/pdf/2105.01380>; Jacobs and Müller: <https://portal.fis.tum.de/en/publications/anomalies-across-the-globe-once-public-no-longer-existent/>
- Martineau, *Rest in Peace Post-Earnings Announcement Drift*: <https://ideas.repec.org/a/now/jnlcfr/104.00000122.html>; UCLA Anderson brief: <https://anderson-review.ucla.edu/is-post-earnings-announcement-drift-a-thing-again/>
- Gu, Kelly and Xiu: <https://www.nber.org/papers/w25398.pdf>; Avramov, Cheng and Metzker: <https://pubsonline.informs.org/doi/fpi/10.1287/mnsc.2022.4449>
- Lookahead bias in LLM forecasts, arXiv 2512.23847: <https://arxiv.org/pdf/2512.23847>; DatedGPT: <https://www.alphaxiv.org/abs/2603.11838>
- Cohen, Malloy and Nguyen, *Lazy Prices*: <https://www.nber.org/papers/w25084>
- Insider cluster purchases (1986–2016): <https://tuck.dartmouth.edu/uploads/content/insider_sentiment_stock_returns.pdf>
- SEC Insider Transactions Data Sets: <https://www.sec.gov/dera/data/form-345>
- Barber, Huang, Odean and Schwarz (Robinhood herding): <https://www.evidenceinvestor.com/post/why-most-robinhood-traders-earn-lousy-returns>
- Backtest-overfitting tools: <https://en.wikipedia.org/wiki/Purged_cross-validation>
