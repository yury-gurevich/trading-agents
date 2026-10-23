# EXP-024 — Does news sentiment, read by the lexicon or by FinBERT, rank the scanner's survivors over 2017–2026?

**Status:** PRE-REGISTERED 2026-10-23 (the commit that adds this file) | COMPLETE — · *verdict once
complete*
**Decision / origin:** [DL-316](../../design-log.md) · work-queue **138** · the operator, 2026-10-23:
*"pre-register this as EXP-024: FinBERT and the word-list scores, tested over 2017–2026 on Alpaca's
historical news"* · **Cost:** $0 (Alpaca's news on the account the fleet already uses; FinBERT on
this machine's CPU; no LLM).

## 1. Why we needed this experiment

[DL-315](../../design-log.md) D3 moved the edge question to the exits and to *"what the replay
cannot see, fundamentals and sentiment in the live composite, measured forward through the claims
ledger"*. Measured forward, an answer takes years. Two facts make the sentiment half visible to the
replay now:

- **The news exists, point in time.** Alpaca's News API serves Benzinga's news on the account the
  fleet already uses, back to 2015 by Alpaca's documentation. The provider does not read it today:
  `AlpacaDataSource.fetch_news` returns nothing, and the live pillar reads Finnhub's company news.
  Measured 2026-10-23 by a probe that counted and read no return: on 22 sessions, two a year from
  2016-10 to 2026-08, each 7-day window held 2,429 to 8,364 items. **64 % of the survivors were
  served at least one headline** (47.5 % in 2019-02, 79.2 % in 2026-02), and **the lexicon's pillar
  would form on 33 %** (17.4 % in 2017-08, 47.8 % in 2026-08). Both are a slight under-count: the
  probe's window missed items revised after it.
- **Both scorers predate the window.** The lexicon is the Loughran–McDonald lists plus a fixed set of
  headline words: a classification of words, not of returns. FinBERT's weights are the Hub revision
  `4556d130` (2023-05-23). Its later commits (2026-10-12) add licence text, a README and a
  safetensors copy. The model card names its training text as the Financial PhraseBank (Malo et al.,
  2014) and Reuters TRC2. Neither scorer can have seen what followed a 2017–2026 headline. A modern
  finance LLM (FinMA, FinGPT, a Qwen fine-tune) cannot be tested this way, because its training text
  covers the window: in a backtest it may know what followed the headline, and the company's name
  distracts it (Glasserman and Lin, 2023, arXiv 2309.17322).

**The decisions that wait on the answer:**

- Does the binding sentiment pillar (the lexicon, composite weight 0.20) carry ranking information,
  point the wrong way, or carry nothing?
- Does the FinBERT challenger read the news better than the champion
  ([ADR-0002](../../decisions/0002-sentiment-champion-challenger.md)'s question)? S57 built a
  `sentiment_scorecard` that compares the two on live Finnhub news. No reading of it is recorded in
  STATE, the work queue or the ledger.
- Does DL-315 D3's sentiment half still need the forward ledger?

**Nothing in the fleet changes on this result before the fidelity PASS.** `agents/analyst/` is a
decision path of the fidelity count, so a change to the pillar waits for the PASS whatever this
reads.

## 2. Hypothesis

Each scorer is read as the fleet reads it (section 5) on the scanner's survivors, against the
10-session forward excess return over SPY, over the **scored window 2017-01-03 → 2026-09-25**.

- **H1 — the lexicon (L).** The analyst's sentiment pillar, on the rows where it forms. Its mean
  per-session Spearman rank IC differs from 0.
- **H2 — FinBERT (F).** The forecaster's reading: the mean aligned FinBERT score over the served
  headlines, on the rows with at least one. Its mean per-session rank IC differs from 0.
- **H3 — the challenger against the champion.** On the rows where both form, the per-session IC of F
  minus that of L differs from 0.
- **The test.** A two-sided bootstrap p for each, with Holm's step-down across the three at a
  family-wise 5 %. A hypothesis **carries** when Holm rejects it; its sign is reported. H0 for each:
  a mean of 0.
- **Why this bar.** It is EXP-023's interval and test on EXP-015's survivors and target, so the three
  experiments read the same evidence the same way. Holm, because three questions are asked at once.
- **The economic reading, fixed now, not a test.** A positive scorer that carries is *worth building
  on* when its mean IC is at least **+0.01**, EXP-015's bar. DL-315 worked out that +0.01 is worth
  about 0.1 % per 10 sessions to a top-decile pick, against 0.5 % for a round trip at 25 bps a side
  *[estimate, not measured]*.
- **What the test can see.** L forms on about 95 rows a session and F on about 185, against about
  290 in EXP-023. Its interval half-width there was about 0.015 over 1,761 sessions. Scaled by the
  square roots of the row and session ratios, that gives about **±0.022 for L and ±0.016 for F**
  over 2,446 sessions *[estimate]*. This test can find a strong signal, but it cannot settle a weak
  one: an IC near +0.01 would probably read as not carrying.

**What each outcome leads to, fixed before the run:**

- **L carries, positive, IC ≥ +0.01:** the binding pillar ranks on this feed. Next comes a new
  pre-registration: a portfolio replay of the composite with sentiment against the price-only
  pipeline, in EXP-014's design. Whether the provider's news moves to Alpaca's feed is its own
  decision.
- **F carries positive and H3 carries positive:** the challenger reads the news better than the
  champion. ADR-0002's promotion becomes the operator's decision, after the fidelity PASS. The
  weights' licence goes with it: CC BY-NC-SA 4.0, non-commercial (the card's terms since
  2026-10-12).
- **L carries negative:** the binding pillar points the wrong way. A fix outranks a feature: the
  operator decides whether its weight goes to 0. That is a decision-path change, made after the PASS.
- **F carries negative only:** the challenger stays advisory, and nothing changes.
- **A positive carry below +0.01:** reported as information too small to pay for a reorder at
  25 bps a side. Nothing is built.
- **Nothing carries:** on this feed, news tone shows no 10-session ranking information that this test
  can see. DL-315 D3's sentiment half is answered for the replay. Whether the forward ledger still
  measures sentiment is the operator's call. No code changes.

**Reported, not tested:**

- Horizons 5 and 20.
- Per-year means.
- Coverage per year: the share of survivors served a headline, and the share with each reading.
- The rows whose ticker is in the analyst's company table (99 tickers), where the own-headline filter
  applies, reported apart.
- The pilot's IC (section 5, step 7).
- The feed overlap on one recent week (section 5, step 9).

## 3. Data

- **EXP-015's panel:** OneDrive `trading-agents-data/experiments/EXP-015/panel.npz`, panel digest
  `aff1a727…`, the cache checksums EXP-023's section 3 lists. Measured 2026-10-23 (sessions, lines
  and survivor flags only; no return was read):
  - sessions 2016-10-17 → 2026-09-25: 2,499 sessions, 715,852 survivor rows;
  - **the scored window** 2017-01-03 → 2026-09-25: 2,446 sessions, **696,537** survivor rows;
  - **the pilot** 2016-10-17 → 2016-12-30: 53 sessions, 19,315 survivor rows;
  - survivors per session: 187 (2022) to 415 (2021) on average by year.
- **The ticker on each session:** `sp500_membership.csv.gz` (line, ticker, first, last). A line's
  episode gives the ticker that news carried that day. 3 episodes have a ticker that differs from
  the line.
- **The news:** Alpaca `GET /v1beta1/news` (Benzinga). Every item from 2016-10-01 through the fetch
  day is fetched once, without bodies. It is stored per month as JSONL.gz in OneDrive
  `trading-agents-data/news-alpaca/`: id, `created_at`, `updated_at`, headline, symbols and source,
  plus a manifest with each file's count and SHA-256. It never goes in the repo: the repo is public
  and the news is licensed.
- **Known defects:**
  - **The API's window is not the creation time.** In the probe's 22 windows, 364 of 114,255 items
    fetched (0.3 %) were created before the window's start, up to 254 in one week of 2023-08. The
    window seems to follow `updated_at` *[inferred; Alpaca's documentation does not say]*. The fetch
    therefore runs through the fetch day, keeps each id once, and decides visibility on `created_at`
    alone.
  - **Revisions.** An item carries its latest headline, not the one first published. In the probe,
    1,123 of 114,255 items (1.0 %) were updated more than an hour after they were created, 4.4 % at
    most in one week (2023-08). An update may or may not change the headline. This cannot be undone;
    it is named.
  - **A different feed.** The live pillar reads Finnhub's company news, and Benzinga tags tickers its
    own way. A pass says the scorer reads information in news of this kind; it does not certify
    Finnhub's feed. Step 9 reports the overlap.
  - **A possible early gap.** A thread on Alpaca's forum reports items missing between 2015-02 and
    2016-10, and a reply disputes it. The pilot starts 2016-10-17, and step 1's stop rule checks every
    month.
  - **The panel's own:** EXP-015's four masked adjustment errors. No sector is read.

## 4. Tools and setup

- **Machine:** i7-7660U (2 cores, 4 threads), Windows 10.
- **Software:** the main checkout's venv: Python 3.13.2, numpy 2.5.3, torch 2.14.0+cpu, transformers
  5.17.0.
- **The scorers, the repo's own at this file's commit:**
  - the lexicon: `subject_sentiment` (`agents/analyst/domain/sentiment_subject.py`) with
    `batch_headline_weights`;
  - FinBERT: `FinBERTModel` (`agents/forecaster/finbert.py`), its `model_ref` the local snapshot of
    revision `4556d13015211d73dccd3fdd39d39232506f3e43` (weights blob SHA-256 `e15a7b57…`), with
    `align_label` and `aggregate` (`agents/forecaster/domain/sentiment.py`).
- **The scripts:** a planner's read-only scripts in OneDrive `trading-agents-data/exp024-2026-10-23/`,
  in the route [DL-314](../../design-log.md) D4 set: `exp024_news.py` (the fetch) and
  `exp024_score.py` (the readings, IC and test). They reuse `scripts/exp015_ranks.session_ic`, the
  `scripts/exp015_rule.interval` method, and EXP-023's p and Holm. Each goes verbatim into
  Appendix S, with its SHA-256 in Appendix R.
- **Measured on this machine, 2026-10-23:** FinBERT scores **35.6 headlines a second** in batches of
  32 (17.6 one at a time). On 256 headlines the batched and the one-at-a-time scores agree within
  2.1e-7, and two runs are identical.
- **Run time *[estimate]*:** the fetch, about 2.7 million items and 54,000 calls (5,177 items a
  week on the probe's average), about 6 hours at 150 calls a minute; FinBERT on the distinct served headlines, about
  4 hours (about 500,000 at 35.6 a second: about 950 new served headlines a week).
- **Seed and cap:** bootstrap seed 0. Cost cap $0.

## 5. How it was conducted

1. **The fetch.** Month by month from 2016-10-01 to the fetch day: ascending, 50 a page, page
   tokens. Each id is kept once, at its latest `updated_at`. At most 150 calls a minute, paused
   21:45 → 00:15 UTC: the key may share Alpaca's rate limit with the fleet's provider at night.
   **A stop condition:** if a month from 2016-10 to 2026-09 holds fewer than a quarter of the median
   month's items, the run stops unscored as `STOPPED` and the operator decides.
2. **The served set** for a survivor line on session *t*, as the provider serves it live
   (`finnhub_news_lookback_days` 7, `max_news_per_ticker` 20, newest first in `_parse_news`):
   - the line's ticker on *t*, from its membership episode;
   - the items with `created_at` in (close − 7 days, close], where close is 16:00 America/New_York
     on *t*;
   - whose symbols include that ticker and whose headline is not empty;
   - newest first by `created_at`, the first 20 headlines.
3. **The lexicon's reading (L):** `batch_headline_weights` over the served sets of the session's
   survivors, keyed by ticker. Then `subject_sentiment(ticker, served, 2, headline_weights=…)`, and
   the pillar is its raw score / 100. Where the pillar does not form, the row has no L.
4. **FinBERT's reading (F):** each distinct served headline is scored once through the
   `FinBERTModel` pipeline, in batches of 32, and aligned by `align_label`. The reading is the mean
   over the served set, as in `aggregate`. A row with no served headline has no F.
5. **IC.** `session_ic` per scorer per session: at least 10 rows with both values, and no IC for a
   flat session. For H3, on L's rows, IC(F) − IC(L) per session where both have an IC.
6. **Interval and test,** EXP-023's exactly:
   - every 10th session;
   - stationary bootstrap, mean block 20, 10,000 resamples, seed 0;
   - percentile 95 % interval;
   - two-sided p = min(1, 2 × (1 + resampled means on the far side of 0) / 10,001).

   Holm then runs over the three p-values.
7. **Pilot, not scored:** the whole chain on 2016-10-17 → 2016-12-30. It proves the alignment and the
   run time. Its IC is reported in Appendix R, and no design choice may change on it. The scripts may
   be fixed for defects after the pilot. After that they are frozen, and their SHA-256 goes in
   Appendix R before the first scored session is read.
8. **Stop conditions:**
   - the scored window must hold 696,537 survivor rows, each with a ticker;
   - on 1,000 pilot headlines, the batched FinBERT scores must equal the one-at-a-time ones within
     1e-6.

   Either failing stops the run as `STOPPED`, unscored.
9. **Feed overlap, reported:** for the analyst's 99 company-table tickers, Finnhub's company news for
   one recent week (2026-10-13 → 2026-10-19) against Alpaca's served set for the same days. The
   figure is the share of Finnhub headlines with an exact, case-folded match.
10. **Outputs** go to OneDrive `trading-agents-data/experiments/EXP-024/`: a JSON record and a page.
    The headlines and their scores stay there. Nothing licensed goes in the repo.

## 6. Results

*Written after the run.*

## 7. Conclusions

*Written after the run.*

## 8. Recommended code changes, and how to implement them

*Written after the run.*

## Appendix P — Pre-registration (frozen)

Frozen at the commit that adds this file (`git log --diff-filter=A` on this path). Never edited.

- **Scorers:** L = `subject_sentiment` (min own 2, batch weights over the session's survivors) / 100;
  F = the mean `align_label`ed FinBERT score over the served headlines (`FinBERTModel`, revision
  `4556d130`).
- **Served set:** the line's ticker on the session; `created_at` in (16:00 New York − 7 days, 16:00
  New York]; symbols include the ticker; newest first; at most 20 headlines.
- **Universe:** the scanner's survivors in EXP-015's panel.
- **Target:** the 10-session forward excess return over SPY (EXP-015's `returns − spy` at horizon
  10).
- **Scored window:** 2017-01-03 → 2026-09-25 (2,446 sessions, 696,537 survivor rows).
- **Hypotheses:** H1 mean IC(L) ≠ 0; H2 mean IC(F) ≠ 0; H3 mean of IC(F) − IC(L), on L's rows, ≠ 0.
- **Statistic:** the mean of per-session Spearman ICs (`session_ic`, at least 10 rows, flat sessions
  excluded).
- **Interval and test:** every 10th session; stationary bootstrap, mean block 20, 10,000 resamples,
  seed 0; percentile 95 %; two-sided p = min(1, 2 × (1 + far-side count) / 10,001); Holm across
  the three at 0.05.
- **Economic reading:** a positive carry is worth building on at a mean IC of +0.01 or more.
- **Outcomes:** as section 2 lists them.
- **Stops:** a month holding under a quarter of the median month's items; a scored window that does
  not hold 696,537 survivor rows; a batched FinBERT score off the one-at-a-time one by more than
  1e-6.
- **Pilot:** 2016-10-17 → 2016-12-30, not scored.

## Appendix R — Run record

*Written during the run.*

## Appendix S — Scripts

*Added verbatim when frozen.* The coverage probe that measured section 1's figures before this
pre-registration (counts only, no return read) is `exp024_coverage_probe.py` in the kit folder; its
output is `coverage_probe.json`.
