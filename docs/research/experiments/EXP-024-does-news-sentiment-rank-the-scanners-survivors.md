# EXP-024 — Does news sentiment, read by the lexicon or by FinBERT, rank the scanner's survivors over 2017–2026?

**Status:** PRE-REGISTERED 2026-10-23 (`410a79c1`; Amendment 1 `095cf8e7`) | COMPLETE 2026-10-23 ·
**nothing carries: neither the lexicon nor FinBERT ranks the scanner's survivors at 10 sessions on
Benzinga's news, and FinBERT is not better than the lexicon; no code changes.** Sections 1–5 and
Appendix P are as pre-registered, with Amendment 1.
**Decision / origin:** [DL-316](../../design-log.md) · work-queue **138** · the operator, 2026-10-23:
*"pre-register this as EXP-024: FinBERT and the word-list scores, tested over 2017–2026 on Alpaca's
historical news"* · **Cost:** $0 (Alpaca's news on the account the fleet already uses; FinBERT on
this machine's CPU; no LLM).

**Amendment 1 — 2026-10-23 17:25 AEDT, the planner (technical decisions are delegated), recorded
before the pilot; no scored session has been read.** A dev pilot on 2016-10 → 2016-12 found two
things the pre-registration got wrong. Appendix P stays as frozen; this overrides it in the four
respects below, and changes nothing about what is tested or how it is read.

1. **The symbol news carried.** Section 3 says a line's membership episode gives the ticker news
   carried that day. It does not: the file names a line by today's ticker throughout (META in 2016).
   In the dev pilot, 32 survivor tickers were served no headline, most of them renamed since (FB →
   META, UTX → RTX, BBT → TFC). The fix is `exp024_renames.py`, which takes each line's symbol of the
   day from three sources, the first that covers the line winning:
   - S235's own symbol map (`scripts/sp500_symbol_map.csv`);
   - Alpaca's `name_change` corporate actions, chained back from the line. Measured: they are
     complete from 2020 only, with 2 in 2017, 2 in 2018, 53 in 2019 and 304 in 2020. A chain is
     refused when the rename into the line's symbol came after the line left the index, because
     the symbol then belongs to another issuer (BBBY, LLL and XL). CCL is refused by review: CUK is
     Carnival plc's own listing;
   - eleven hand rows for 2016–2019: TSO, COH, PCLN, CBG, HCN, LUK, KORS, HRS, TMK, BHGE and SYMC.
     Each switch date is the first item tagged with the new symbol, where the old symbol's items stop
     (0 to 5 items overlap). Each was found as a line with no tagged item for a year, or whose news
     began more than 60 days after its first survivor row.

   The company-table lookup stays on the line, since the analyst's table is keyed by today's ticker.
   A class-share tag written `BRK-B` or `BF/B` counts as its dotted ticker; Benzinga uses all three.
   **Ruled out:** FMP's symbol-change history (402 on the fleet's plan), and serving one share class
   another's news (DISCK is mostly tagged DISCA; that is thin coverage, not a rename).
2. **FinBERT's check tolerance is 1e-5, not 1e-6.** On 3,000 real pilot headlines, batch composition
   alone moves a score by up to 1.22e-6 (float32 arithmetic). The 1e-6 was set from 256 synthetic
   headlines (2.1e-7). The check exists to catch batching that changes a score materially, and
   1e-5 still does.
3. **The check reads the scores the run uses.** It compares the scores the run actually used for the
   first 1,000 pilot headlines with one-at-a-time scores. It stops the pilot, as pre-registered, and
   the scored run reports it.
4. **Batches of 32, ordered by token length.** The batch size is unchanged; the order cuts padding
   (14 → 17.7 headlines a second, measured). Distinct headlines may be scored in passes as the fetch
   lands, into one cache, each headline once. The run time becomes about 6.5 hours of fetching and
   8 to 11 hours of FinBERT *[estimate: about 520,000 distinct headlines]*.

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

**MEASURED.** One scored run, 2026-10-23 09:30 → 11:51 UTC, `exp024.json` (Appendix R).
696,537 rows over 2,446 sessions. Every stop passed: no month missing or thin, and FinBERT's used
scores within 8.9e-8 of one at a time.

**Nothing carries.** Holm across the three needs p ≤ 0.0167 for the first. The smallest p is 0.117
(H3). Mean IC at 10 sessions, 2017-01-03 → 2026-09-25, 95 % interval:

| Test | Mean IC | 95 % interval | p | Carries (Holm) | Sessions with an IC |
| --- | --- | --- | --- | --- | --- |
| H1 — the lexicon | **+0.0022** | [−0.0101, +0.0206] | 0.406 | no | 2,435 |
| H2 — FinBERT | **−0.0050** | [−0.0168, +0.0108] | 0.609 | no | 2,436 |
| H3 — FinBERT minus the lexicon, on the lexicon's rows | **−0.0091** | [−0.0289, +0.0030] | 0.117 | no | 2,435 |

**Reported, not tested:**

- **Horizons 5 and 20:** lexicon +0.0013 and +0.0021; FinBERT −0.0056 and −0.0048.
- **By year, H1 (the lexicon):** 2017 +0.034, 2018 −0.017, 2019 +0.023, 2020 +0.002, 2021 −0.007,
  2022 +0.007, 2023 +0.006, 2024 −0.003, 2025 +0.005, 2026 −0.040 (nine months). Six of ten years are
  positive, with no trend.
- **By year, H2 (FinBERT):** 2017 +0.005, 2018 +0.001, 2019 −0.000, 2020 −0.017, 2021 −0.006,
  2022 +0.025, 2023 −0.008, 2024 −0.019, 2025 −0.015, 2026 −0.021. Seven of ten years are at or below
  zero.
- **Coverage:** the share of rows served a headline rises from 52.8 % (2017) to 75.3 % (2025). The
  share with a lexicon reading rises from 23.7 % to 38.4 %. FinBERT reads every served row.
- **The 99 company-table names** (156,274 rows, own-headline filter applied): lexicon −0.0039
  [−0.0363, +0.0370]; FinBERT −0.0013 [−0.0157, +0.0217].
- **Never served over the whole window:** 2 tickers (JEF and MUR).
- **The pilot** and **the feed overlap** are in Appendix R.

## 7. Conclusions

**Nothing carries,** so section 2's reading applies. On Benzinga's news, neither the lexicon nor
FinBERT shows 10-session ranking information among the scanner's survivors that this test can see.
FinBERT does not read the news better than the lexicon; if anything it leans the other way. DL-315
D3's sentiment half is answered for the replay. Whether the forward ledger still measures sentiment
is the operator's call. No code changes.

**What the test could see.** The intervals came out narrower than section 2 estimated. At 95 %,
FinBERT's mean IC is below **+0.011** and the lexicon's below **+0.021**. EXP-015 set +0.01 as the
bar for an IC worth building on. FinBERT's interval rules that out. The lexicon's does not quite,
but its point estimate (+0.002) sits far below it, and no year after 2019 reached +0.01.

**What it does not say:**

- **Not the live feed.** This experiment read Benzinga's headlines. In the overlap week they were
  13.7 % of what Finnhub serves the live pillar for the same names. A wider feed is not shown to
  carry, and not shown to be empty.
- **Not short horizons.** The panel's horizons are 5, 10 and 20 sessions, and all three are flat. A
  1-to-2-day effect, where the literature finds most of news tone's information *[literature, not
  measured here]*, is not measured. The fleet holds for longer than that, at 25 bps a side.
- **Not news in general.** It reads tone only. What an item is about (earnings, guidance, a deal)
  is not read.

**Together with EXP-015 and EXP-023:** in the replay, neither the price-only ranking nor news tone
shows skill at choosing among the scanner's survivors. What DL-315 D3 leaves for the edge question:
the exits (EXP-022, sealed until the fidelity PASS), fundamentals (forward through the claims
ledger), and the candidate DL-316 named, filing text ("Lazy Prices").

## 8. Recommended code changes, and how to implement them

**None.** Nothing carries, and `agents/analyst/` cannot change before the fidelity PASS in any case.
Three calls go to the operator, and none is urgent:

1. **The sentiment pillar's weight (0.20).** It shows no ranking information here, so in the
   composite it adds variation without signal. **The planner's recommendation: keep it as it is**,
   as DL-315 did for the price-only ranking. A change is a decision-path change that restarts the
   fidelity count, the measured gain is nil, and this result does not certify Finnhub's wider feed
   as empty. Record it in the ADR that closes DL-315's line.
2. **The forward sentiment measurement** (DL-315 D3, the claims ledger). **Recommendation:** stop
   treating it as an edge line. Keep the shadow readings, which cost nothing.
3. **FinBERT's challenger seat (ADR-0002).** H3 gives no reason to promote it. Two hygiene items
   stand whatever the operator decides:
   - pin `model_ref` to revision `4556d130`;
   - record the weights' non-commercial licence (CC BY-NC-SA 4.0) in ADR-0002.

   Together they are a small chore after the PASS: a `revision` setting passed to the pipeline, and
   a line in the ADR.

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

- **Code:** the runs import from a detached worktree (`../ta-exp024`). The prescore ran at `410a79c1`;
  the pilot and the scored run ran at `095cf8e7` (Amendment 1), clean. The two commits differ in
  docs only.
- **Environment:** the main venv's Python 3.13.2, numpy 2.5.3, torch 2.14.0+cpu, transformers
  5.17.0; i7-7660U. Every stage ran detached through `run_exp024.ps1` at BelowNormal priority,
  keeping the machine awake.
- **The fetch:** 2026-10-23 04:46 → 09:22 UTC, with no error and no pause needed. It holds 121 month
  files, 2016-10-01 → 2026-10-23 09:15 UTC: **1,998,632 items from 40,037 calls**. Manifest
  SHA-256 `c345c53647ed77f14f5f2c4b85ac556a15f61c79acad5c430cec07d1301f1c2f`.
- **The dev pilot (before Amendment 1):** the whole chain on 2016-10 → 2016-12. It found the two
  defects Amendment 1 records: 32 tickers never served, and the 1e-6 check passing at only
  8.6e-7. It also found that Benzinga writes class shares `BRK.B`, `BRK-B` and `BF/B`. Its output
  sits in a scratch folder and was not used.
- **The rename table:** `exp024_renames.py` on the full fetch. 46 lines carry spans; 4 chains were
  refused (BBBY, LLL and XL after leaving the index, and CCL by review); 11 hand rows; **0 line-years**
  with survivor rows and no tagged item. Six lines start their news more than 60 days after their
  first survivor row, all thin coverage rather than renames: AN, AOS, DRE and TEL (62–76 days),
  DISCK and BF.B. `renames.json` SHA-256
  `b1bdac87e3a3e16b892e012d388b04bde1654799c3dee231b4ad337aa3cafff3`; Alpaca's `name_changes.json`
  (3,703 records) `f6196a828f6ccc9d844954323323f503d0d32d9303e1cee42622e2c771ab9354`.
- **The prescore (Amendment 1):** 06:22 → 08:11 UTC, run on the 61 months fetched by then. It scored
  122,682 distinct headlines of the scored window in 6,473 s (19 a second on average, 0 over 512
  tokens) into `finbert_scores.jsonl`. No target was read.
- **The pilot:** 09:24 → 09:29 UTC. Every stop passed:
  - 19,315 rows over 53 sessions, 1,181 of them on a renamed symbol;
  - no month missing or thin (median month 16,350.5 items);
  - FinBERT's used scores within **1.8e-7** of one at a time (limit 1e-5);
  - the weights' SHA-256 and min own 2 as pre-registered;
  - 6,649 distinct headlines, 6,388 scored then.

  Coverage: 58.5 % of rows served a headline, 29.4 % with a lexicon reading. Eight tickers were
  never served in the pilot: AN, BF.B, DISCK, DPS, EQR, HBI, TEL and VFC. **The pilot's IC, reported
  as section 5 requires and read for nothing:** H1 −0.0133 (p 0.005), H2 −0.0132 (p 0.19), H3
  −0.0221 (p 0.04). Each rests on 6 bootstrap sessions. `pilot.json` SHA-256
  `48b89c20cc238f135ae8fbf9bfbe069a0bd7b593381950d4936b666c4c9d8cc5`.
- **Feed overlap (step 9, reported):** in the week of 2026-10-13 → 2026-10-19, for the 99
  company-table tickers, Finnhub served **8,541** distinct headlines and Alpaca **1,736**. 1,167 match
  exactly: **13.7 % of Finnhub's** and 67 % of Alpaca's. Finnhub aggregates about five times as many
  headlines, so this experiment reads Benzinga's slice of what the live pillar reads.
- **Frozen before the scored run** (SHA-256):
  - `exp024_score.py` `9d41667b989fb3de38e64c937adc64b47fc21d99a48f425a52024134eb688f0b`
  - `exp024_renames.py` `0bf26c5b28b02ff40a20492aac18bffe219fc57a8d769240dd9c080eee4a8d5e`
  - `exp024_news.py` `4f79ede5bdef0254f2be342a0cd83ee8297b67c3c0352b539d200436b068feaf`
  - `exp024_overlap.py` `ea0ac8d8afeb2c23541ea449614e58c0719d242390545c3f8781a9ac633de6fd`
  - `exp024_coverage_probe.py` `d6bfa0ce535b411a8a0325615e2c104bea322024626a2e39df8ead13e809daea`
  - `run_exp024.ps1` `70dc8af5c7b8c149dae6fafbe0b281c3587d74b0f087a2ab39a5bf542a3de401`
- **The scored run:** 09:30:51 → 11:51:01 UTC, from `095cf8e7`, clean, `exp024_score.py` at its
  frozen SHA-256. EXP-015's panel digest checked first (`aff1a727…`). 696,537 rows (the stop passed),
  21,724 of them on a renamed symbol; no month missing or thin. 327,012 distinct headlines: 122,682
  from the prescore and 204,358 scored in the run (8,225 s, 0 over 512 tokens). The check is
  reported: 8.9e-8. The lexicon took 21 s. Verdict `COMPLETE`.
- **Output:** OneDrive `trading-agents-data/experiments/EXP-024/`: `exp024.json` SHA-256
  `afdfb09e26308354f708e0d98904faac4bfdf69d1da2d0ce4019728336bfedf9`, with `exp024.md`, `pilot.json`,
  `prescore.json` and the score cache `finbert_scores.jsonl`. The news is in
  `trading-agents-data/news-alpaca/`. The kit is `trading-agents-data/exp024-2026-10-23/` (scripts,
  runner, log, stdout and stderr, probe, rename table, name changes, overlap).

## Appendix S — Scripts

Each as frozen. The scorers import the repo's own code from the worktree. The SHA-256 in Appendix R
is of the files on disk, five of which have CRLF line endings (only `exp024_news.py` is LF). The text
below is LF, and equals each file byte for byte once CRLF is read as LF (checked 2026-10-23).

### `exp024_coverage_probe.py`

The coverage probe, run before the pre-registration (counts only, no return read).

```python
"""EXP-024 coverage probe: how much Alpaca (Benzinga) news reaches the scanner's survivors.

Read-only, counts only. It reads the panel's sessions, lines and survivor flags (never a return)
and the membership episodes, fetches every news item in a 7-day window before sample sessions,
and asks the analyst's own ``subject_sentiment`` whether a pillar would form. It records no score.

Run from the main checkout:  .venv/Scripts/python.exe -I <this file> <repo> <data dir> <out json>
"""

from __future__ import annotations

import csv
import gzip
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

NY = ZoneInfo("America/New_York")
URL = "https://data.alpaca.markets/v1beta1/news"
LOOKBACK_DAYS = 7
CAP = 20
MIN_OWN = 2


def env_keys(repo: Path) -> tuple[str, str]:
    vals = {}
    for line in (repo / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals["PROVIDER_ALPACA_API_KEY"], vals["PROVIDER_ALPACA_API_SECRET"]


def fetch(keys: tuple[str, str], start: datetime, end: datetime) -> tuple[list[dict], int]:
    items: list[dict] = []
    token = None
    calls = 0
    while True:
        q = {"start": start.isoformat(), "end": end.isoformat(), "limit": "50", "sort": "desc",
             "include_content": "false"}
        if token:
            q["page_token"] = token
        req = urllib.request.Request(f"{URL}?{urllib.parse.urlencode(q)}", headers={
            "APCA-API-KEY-ID": keys[0], "APCA-API-SECRET-KEY": keys[1]})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    body = json.loads(r.read())
                break
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt < 4:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise
        calls += 1
        items.extend(body.get("news", []))
        token = body.get("next_page_token")
        time.sleep(0.32)
        if not token:
            return items, calls


def episodes(data: Path) -> dict[str, list[tuple[str, date, date]]]:
    out: dict[str, list[tuple[str, date, date]]] = {}
    with gzip.open(data / "sp500_membership.csv.gz", "rt", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out.setdefault(row["line"], []).append(
                (row["ticker"], date.fromisoformat(row["first"]), date.fromisoformat(row["last"])))
    return out


def ticker_on(eps: dict, line: str, day: date) -> str:
    for ticker, first, last in eps.get(line, ()):
        if first <= day <= last:
            return ticker
    return line


def sample_sessions(sessions: np.ndarray) -> list[str]:
    uniq = sorted(set(sessions.tolist()))
    picks = []
    for year in range(2016, 2027):
        for month, day in ((2, 10), (8, 10)) if year > 2016 else ((10, 20), (12, 9)):
            target = date(year, month, day).isoformat()
            later = [s for s in uniq if s >= target]
            if later and later[0][:4] == str(year):
                picks.append(later[0])
    return picks


def main(repo: Path, data: Path, out: Path) -> None:
    sys.path.insert(0, str(repo))
    from agents.analyst.domain.sentiment_subject import COMPANY_NAMES, subject_sentiment
    from agents.analyst.domain.sentiment_weights import batch_headline_weights

    keys = env_keys(repo)
    with np.load(data / "experiments" / "EXP-015" / "panel.npz", allow_pickle=False) as d:
        sessions, lines, primary = d["sessions"], d["lines"], d["primary"]
    eps = episodes(data)
    rows = []
    for s in sample_sessions(sessions):
        day = date.fromisoformat(s)
        end = datetime.combine(day, dtime(16, 0), NY)
        start = end - timedelta(days=LOOKBACK_DAYS)
        t0 = time.time()
        items, calls = fetch(keys, start, end)
        lo, hi = start.astimezone(ZoneInfo("UTC")), end.astimezone(ZoneInfo("UTC"))
        def ts(v: str) -> datetime:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        before = sum(1 for i in items if ts(i["created_at"]) < lo)
        revised = sum(1 for i in items if ts(i["updated_at"]) - ts(i["created_at"]) > timedelta(hours=1))
        items = [i for i in items if lo <= ts(i["created_at"]) <= hi]
        by_symbol: dict[str, list[tuple[str, str]]] = {}
        for it in items:
            for sym in it.get("symbols") or ():
                if it.get("headline"):
                    by_symbol.setdefault(sym, []).append((it["created_at"], it["headline"]))
        surv = [str(x) for x in lines[(sessions == s) & primary]]
        served = {}
        for line in surv:
            tk = ticker_on(eps, line, day)
            heads = sorted(by_symbol.get(tk, ()), reverse=True)[:CAP]
            if heads:
                served[line] = (tk, tuple(h for _, h in heads))
        weights = batch_headline_weights({ln: v[1] for ln, v in served.items()})
        pillar = sum(1 for ln, (tk, hs) in served.items()
                     if subject_sentiment(tk, hs, MIN_OWN, headline_weights=weights)[0] is not None)
        listed = [ln for ln in surv if ticker_on(eps, ln, day) in COMPANY_NAMES]
        row = {"session": s, "articles": len(items), "tagged": sum(1 for i in items if i.get("symbols")),
               "calls": calls, "created_before_start": before, "updated_1h_after_created": revised, "seconds": round(time.time() - t0, 1), "survivors": len(surv),
               "served": len(served), "pillar": pillar, "listed": len(listed),
               "mean_served_headlines": round(float(np.mean([len(v[1]) for v in served.values()])) if served else 0.0, 2),
               "oldest_created": min((i["created_at"] for i in items), default=None)}
        rows.append(row)
        print(json.dumps(row), flush=True)
        out.write_text(json.dumps({"partial": True, "rows": rows}, indent=1), encoding="utf-8")
    out.write_text(json.dumps({"lookback_days": LOOKBACK_DAYS, "cap": CAP, "min_own": MIN_OWN,
                               "rows": rows}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
```

### `exp024_news.py`

The fetch.

```python
"""EXP-024's news fetch (DL-316): every Alpaca (Benzinga) news item, month by month, to OneDrive.

A planner's read-only script: it reads Alpaca's News API with the provider's key and writes outside
the repo. Resumable: a month whose file is in the manifest is skipped.

  python -B -I exp024_news.py <repo with .env> <news_dir> [--start 2016-10]

Each month's API window [first day 00:00Z, next month 00:00Z) is fetched ascending, 50 a page, no
bodies; the current month runs last, alone, up to now. At most 150 calls a minute across three
workers, and none 21:45 -> 00:15 UTC (the fleet's night window; the key may share its rate limit).
Each item keeps id, created_at, updated_at, headline, symbols, source. Dedupe by id is the scorer's.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

URL = "https://data.alpaca.markets/v1beta1/news"
PER_MINUTE = 150
WORKERS = 3
PAUSE = ((21, 45), (0, 15))  # UTC, crosses midnight
KEEP = ("id", "created_at", "updated_at", "headline", "symbols", "source")


class Limiter:
    """One call at least 60 / PER_MINUTE seconds after the last, across threads; none in the pause."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self) -> None:
        while paused(datetime.now(UTC)):
            time.sleep(30)
        with self._lock:
            now = time.monotonic()
            slot = max(now, self._next)
            self._next = slot + 60.0 / PER_MINUTE
        time.sleep(max(0.0, slot - now))


def paused(now: datetime) -> bool:
    (h0, m0), (h1, m1) = PAUSE
    minute = now.hour * 60 + now.minute
    return minute >= h0 * 60 + m0 or minute < h1 * 60 + m1


def env_keys(repo: Path) -> tuple[str, str]:
    vals: dict[str, str] = {}
    for line in (repo / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals["PROVIDER_ALPACA_API_KEY"], vals["PROVIDER_ALPACA_API_SECRET"]


def call(keys: tuple[str, str], limiter: Limiter, query: dict[str, str]) -> dict:
    req = urllib.request.Request(f"{URL}?{urllib.parse.urlencode(query)}", headers={
        "APCA-API-KEY-ID": keys[0], "APCA-API-SECRET-KEY": keys[1]})
    for attempt in range(8):
        limiter.wait()
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 7:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 7:
                raise
        time.sleep(min(300, 10 * 2**attempt))
    raise RuntimeError("unreachable")


def month_starts(first: str, now: datetime) -> list[datetime]:
    y, m = (int(x) for x in first.split("-"))
    out = []
    while (y, m) <= (now.year, now.month):
        out.append(datetime(y, m, 1, tzinfo=UTC))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def next_month(start: datetime) -> datetime:
    return (start + timedelta(days=32)).replace(day=1)


def fetch_month(keys, limiter, news_dir: Path, start: datetime, end: datetime) -> dict[str, object]:
    t0, calls, count, token = time.time(), 0, 0, None
    tmp = news_dir / f"{start:%Y-%m}.jsonl.gz.part"
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        while True:
            q = {"start": start.isoformat().replace("+00:00", "Z"), "end": end.isoformat().replace("+00:00", "Z"),
                 "limit": "50", "sort": "asc", "include_content": "false"}
            if token:
                q["page_token"] = token
            body = call(keys, limiter, q)
            calls += 1
            for item in body.get("news") or ():
                fh.write(json.dumps({k: item.get(k) for k in KEEP}, ensure_ascii=False) + "\n")
                count += 1
            token = body.get("next_page_token")
            if not token:
                break
    path = news_dir / f"{start:%Y-%m}.jsonl.gz"
    tmp.replace(path)
    return {"month": f"{start:%Y-%m}", "items": count, "calls": calls, "seconds": round(time.time() - t0, 1),
            "window": [q["start"], q["end"]], "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "fetched_at": datetime.now(UTC).isoformat(timespec="seconds")}


def main(argv: list[str]) -> int:
    repo, news_dir = Path(argv[1]), Path(argv[2])
    first = argv[argv.index("--start") + 1] if "--start" in argv else "2016-10"
    news_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = news_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8")) if manifest_path.exists() else {"months": {}}
    keys, limiter, lock = env_keys(repo), Limiter(), threading.Lock()
    now = datetime.now(UTC)
    starts = month_starts(first, now)
    past, current = starts[:-1], starts[-1]

    def run(start: datetime, end: datetime) -> None:
        if f"{start:%Y-%m}" in manifest["months"]:
            return
        row = fetch_month(keys, limiter, news_dir, start, end)
        with lock:
            manifest["months"][row["month"]] = row
            manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", "utf-8")
        print(json.dumps({k: row[k] for k in ("month", "items", "calls", "seconds")}), flush=True)

    with ThreadPoolExecutor(WORKERS) as pool:
        for f in [pool.submit(run, s, next_month(s)) for s in past]:
            f.result()
    run(current, datetime.now(UTC).replace(microsecond=0))
    total = sum(int(r["items"]) for r in manifest["months"].values())
    print(f"DONE months={len(manifest['months'])} items={total}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

### `exp024_renames.py`

The symbol news carried (Amendment 1).

```python
"""EXP-024: the symbol each panel line's news carried on each day (a defect fix found by the dev pilot).

The membership file names a line by today's ticker; Benzinga tags an item with the ticker of its
day. Spans come from three sources, first match per line wins:
  1. S235's own symbol map (scripts/sp500_symbol_map.csv): explicit spans;
  2. Alpaca's name_change corporate actions (name_changes.json), chained backwards from the line;
  3. HAND: renames before Alpaca's records (2016-10 .. 2019), each checked on the news below.
Every span is checked on the news: items tagged with the old symbol inside the span, and with the
line's symbol inside it. Lines with survivor rows in a year and no tagged item are listed.

  python -B exp024_renames.py <tree> <data dir> <news_dir> <kit>
"""

from __future__ import annotations

import csv
import gzip
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

SYMBOL = re.compile(r"^[A-Z]{1,5}(\.[A-Z])?$")
START = "2016-10-01"
# old symbol, the line (today's symbol), the first day under the new symbol. Each is checked below.
# The day is the first item tagged with the new symbol (measured 2026-10-23 on this fetch): the old
# symbol's items stop there. LUK: the index held Leucadia until 2018-05-24; earlier JEF tags are not it.
HAND: tuple[tuple[str, str, str], ...] = (
    ("TSO", "ANDV", "2017-08-08"), ("COH", "TPR", "2017-11-02"), ("PCLN", "BKNG", "2018-02-28"),
    ("CBG", "CBRE", "2018-04-03"), ("HCN", "WELL", "2018-04-25"), ("LUK", "JEF", "2018-05-24"),
    ("KORS", "CPRI", "2019-01-11"), ("HRS", "LHX", "2019-07-03"), ("TMK", "GL", "2019-08-22"),
    ("BHGE", "BKR", "2019-10-22"), ("SYMC", "GEN", "2019-11-06"),
)
# chained renames reviewed and refused: the old symbol is another listing of the same issuer
REJECT = {"CCL": "CUK is Carnival plc's own listing; Carnival Corp traded as CCL throughout"}


def day_before(stamp: str) -> str:
    return (date.fromisoformat(stamp) - timedelta(days=1)).isoformat()


def map_spans(tree: Path) -> dict[str, list[list[str]]]:
    out: dict[str, list[list[str]]] = {}
    with (tree / "scripts" / "sp500_symbol_map.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["kind"] == "rename":
                out.setdefault(row["line"], []).append([row["symbol"], "0000-01-01", day_before(row["from"])])
            elif row["kind"] == "bars" and row["symbol"] != row["line"]:
                out.setdefault(row["line"], []).append([row["symbol"], row["from"], row["to"]])
    return out


def chain_spans(line: str, events: list[dict]) -> list[list[str]]:
    """Walk back from the line: the latest change into the current symbol, then into its old one."""
    spans, cur, until = [], line, "9999-12-31"
    for _ in range(10):
        into = [e for e in events if e["new_symbol"] == cur and e["process_date"] <= until and e["old_symbol"] != cur]
        if not into:
            break
        e = max(into, key=lambda x: x["process_date"])
        spans.append([e["old_symbol"], "0000-01-01", day_before(e["process_date"])])
        if len(spans) > 1:
            spans[-2][1] = e["process_date"]
        cur, until = e["old_symbol"], day_before(e["process_date"])
    return spans


def main(argv: list[str]) -> int:
    tree, data, news_dir, kit = (Path(a) for a in argv[1:5])
    with np.load(data / "experiments" / "EXP-015" / "panel.npz", allow_pickle=False) as d:
        sessions, lines, primary = d["sessions"], d["lines"], d["primary"]
    surv_lines = sorted(set(lines[primary].tolist()))
    years = {ln: {} for ln in surv_lines}
    for ln, s in zip(lines[primary].tolist(), sessions[primary].tolist(), strict=True):
        years[ln][s[:4]] = years[ln].get(s[:4], 0) + 1
    events = [e for e in json.loads((kit / "name_changes.json").read_text("utf-8"))
              if SYMBOL.match(e.get("old_symbol") or "") and SYMBOL.match(e.get("new_symbol") or "")]
    spans: dict[str, list[list[str]]] = {}
    source: dict[str, str] = {}
    from_map = map_spans(tree)
    last_member: dict[str, str] = {}
    with gzip.open(data / "sp500_membership.csv.gz", "rt", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            last_member[row["line"]] = max(last_member.get(row["line"], ""), row["last"])
    refused: dict[str, str] = {}
    for ln in surv_lines:
        if ln in from_map:
            spans[ln], source[ln] = from_map[ln], "symbol_map"
            continue
        chained = [s for s in chain_spans(ln, events) if s[2] >= START]
        if chained and ln in REJECT:
            refused[ln] = REJECT[ln]
            continue
        if chained and chained[0][2] >= last_member.get(ln, "9999"):  # renamed into ln after it left
            refused[ln] = f"renamed into {ln} after the line left the index ({last_member.get(ln)}): another issuer"
            continue
        if chained:
            spans[ln], source[ln] = chained, "alpaca_name_change"
    for old, ln, first_new in HAND:
        held = spans.setdefault(ln, [])
        earliest = [sp for sp in held if sp[1] == "0000-01-01"]
        if earliest and earliest[0][2] < first_new:
            print(f"HAND row {old}->{ln} refused: {source[ln]} already reaches {earliest[0]}")
            continue
        if earliest:  # extend the chain back: its earliest symbol starts at first_new
            earliest[0][1] = first_new
        held.append([old, "0000-01-01", day_before(first_new)])
        source[ln] = f"{source[ln]}+hand" if ln in source else "hand"
    # count tagged items per symbol per day, latest revision per id
    latest: dict[int, tuple[str, str, tuple[str, ...]]] = {}
    for path in sorted(news_dir.glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for raw in fh:
                it = json.loads(raw)
                held = latest.get(int(it["id"]))
                if held is None or it["updated_at"] > held[0]:
                    latest[int(it["id"])] = (it["updated_at"], it["created_at"][:10],
                                             tuple(s.replace("-", ".").replace("/", ".") for s in it.get("symbols") or ()))
    tagged: dict[str, list[str]] = {}
    for _, day, syms in latest.values():
        for s in syms:
            tagged.setdefault(s, []).append(day)
    for days in tagged.values():
        days.sort()

    def count(sym: str, first: str, last: str) -> int:
        days = tagged.get(sym, [])
        lo = np.searchsorted(days, max(first, START), side="left")
        hi = np.searchsorted(days, last, side="right")
        return int(max(0, hi - lo))

    checks = []
    for ln in sorted(spans):
        for sym, first, last in spans[ln]:
            if last < START:
                continue
            checks.append({"line": ln, "symbol": sym, "first": first, "last": last, "source": source[ln],
                           "items_old_symbol": count(sym, first, last), "items_line_symbol": count(ln, first, last)})

    def symbol_on(ln: str, day: str) -> str:
        for sym, first, last in spans.get(ln, ()):
            if first <= day <= last:
                return sym
        return ln

    dark = []
    for ln in surv_lines:
        for year, rows in sorted(years[ln].items()):
            first, last = f"{year}-01-01", f"{year}-12-31"
            n = count(symbol_on(ln, first), first, last) + (count(symbol_on(ln, last), first, last)
                                                           if symbol_on(ln, first) != symbol_on(ln, last) else 0)
            if rows >= 50 and n == 0:
                dark.append({"line": ln, "year": year, "survivor_rows": rows})
    record = {"spans": spans, "source": source, "refused": refused, "checks": checks, "dark_line_years": dark,
              "news_months": sorted(p.name[:7] for p in news_dir.glob("*.jsonl.gz"))}
    (kit / "renames.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", "utf-8")
    for c in checks:
        print(json.dumps(c))
    print(f"lines with spans {len(spans)}; dark line-years {len(dark)}")
    for d_ in dark:
        print("DARK", json.dumps(d_))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

### `exp024_score.py`

The readings, IC and test: `--prescore`, `--pilot`, and the scored run.

```python
"""EXP-024: news sentiment's rank IC, the lexicon and FinBERT, on EXP-015's survivors (DL-316).

A planner's read-only script. Main venv python, the tree (a clean worktree) first on sys.path:

  python -B exp024_score.py <tree> <cache> <exp015_out> <news_dir> <out_dir> [--pilot | --prescore]

--pilot: 2016-10-17 .. 2016-12-30, not scored. Otherwise the scored window 2017-01-03 .. 2026-09-25.
--prescore (Amendment 1): FinBERT scores the scored window's served headlines on the months fetched so
far, into the cache, and exits before any target is read.
Each scorer is read as the fleet reads it: the analyst's subject_sentiment over the served headlines
(7 days to 16:00 New York, the 20 newest), and the forecaster's mean aligned FinBERT score over them.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
import time
from bisect import bisect_right
from datetime import date, datetime
from datetime import time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

TREE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(TREE))

import numpy as np  # noqa: E402

from agents.analyst.domain.sentiment_subject import COMPANY_NAMES, subject_sentiment  # noqa: E402
from agents.analyst.domain.sentiment_weights import batch_headline_weights  # noqa: E402
from agents.forecaster.domain.sentiment import aggregate, align_label  # noqa: E402
from agents.forecaster.finbert import FinBERTModel  # noqa: E402
from scripts.exp015_ranks import session_ic  # noqa: E402
from scripts.exp015_spec import BLOCK, HORIZONS, RESAMPLES, SEED, STEP_SESSIONS  # noqa: E402
from scripts.exp015_store import load_panel, panel_digest  # noqa: E402
from scripts.replay_settings import build_effective_settings  # noqa: E402
from scripts.replay_verdict_stats import percentile_interval, seeded, stationary_draws  # noqa: E402

PANEL_SHA = "aff1a727b1c0e9d1e9ccef3577d0aa2143150e7396702da3023693bccee52b52"  # pragma: allowlist secret
SNAPSHOT = Path.home() / ".cache/huggingface/hub/models--ProsusAI--finbert/snapshots/4556d13015211d73dccd3fdd39d39232506f3e43"
WEIGHTS_SHA = "e15a7b5738df7f17553399b6d94c6e2ff69c89245d066e8e5d183f5803a554e3"  # pragma: allowlist secret
PILOT, WINDOW = ("2016-10-17", "2016-12-30"), ("2017-01-03", "2026-09-25")
SCORED_ROWS, LOOKBACK, CAP, MIN_OWN = 696_537, 7 * 86_400, 20, 2
MONTHS, MONTH_FLOOR, CHECK_N, CHECK_TOL = ("2016-10", "2026-09"), 0.25, 1_000, 1e-5  # Amendment 1
ALPHA, ECONOMIC, BATCH, CHUNK = 0.05, 0.01, 32, 2_048
NY = ZoneInfo("America/New_York")


def stopped(out_dir: Path, pilot: bool, record: dict, why: str) -> int:
    record |= {"verdict": "STOPPED", "why": why}
    (out_dir / ("pilot.json" if pilot else "exp024.json")).write_text(json.dumps(record, indent=2) + "\n", "utf-8")
    print(f"STOPPED: {why}", file=sys.stderr)
    return 2


def episodes(cache: Path) -> dict[str, list[tuple[str, str, str]]]:
    out: dict[str, list[tuple[str, str, str]]] = {}
    with gzip.open(cache / "sp500_membership.csv.gz", "rt", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out.setdefault(row["line"], []).append((row["ticker"], row["first"], row["last"]))
    return out


RENAMES = Path(__file__).with_name("renames.json")  # exp024_renames.py: the symbol news carried


def ticker_on(eps: dict, line: str, day: str, spans: dict) -> str:
    for symbol, first, last in spans.get(line, ()):
        if first <= day <= last:
            return symbol
    for ticker, first, last in eps.get(line, ()):
        if first <= day <= last:
            return ticker
    return line


def epoch(stamp: str) -> int:
    return int(datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp())


def load_news(news_dir: Path, tickers: set[str]) -> tuple[dict, dict[str, int], dict[str, object]]:
    """Dedupe by id at the latest updated_at; per ticker (created, id, headline) sorted; month counts."""
    latest: dict[int, tuple[str, str, str, tuple[str, ...]]] = {}
    read = 0
    for path in sorted(news_dir.glob("*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for raw in fh:
                item = json.loads(raw)
                read += 1
                key, updated = int(item["id"]), item.get("updated_at") or item["created_at"]
                held = latest.get(key)
                if held is None or updated > held[0]:
                    # Benzinga writes a class share BRK.B, BRK-B or BF/B; membership uses the dot.
                    alias = (s.replace("-", ".").replace("/", ".") for s in item.get("symbols") or ())
                    syms = tuple(dict.fromkeys(s for s in alias if s in tickers))
                    headline = (item.get("headline") or "").strip() if syms else ""
                    latest[key] = (updated, item["created_at"], headline, syms)
    months: dict[str, int] = {}
    per: dict[str, list[tuple[int, int, str]]] = {}
    for key, (_, created, headline, syms) in latest.items():
        months[created[:7]] = months.get(created[:7], 0) + 1
        if headline and syms:
            stamp = epoch(created)
            for s in syms:
                per.setdefault(s, []).append((stamp, key, headline))
    index = {}
    for s, rows in per.items():
        rows.sort()
        index[s] = (np.array([r[0] for r in rows], dtype=np.int64), [r[2] for r in rows])
    return index, dict(sorted(months.items())), {"lines_read": read, "unique_items": len(latest)}


def served(index: dict, ticker: str, close: int) -> tuple[str, ...]:
    """created in (close - 7 days, close], newest first, the first CAP."""
    held = index.get(ticker)
    if held is None:
        return ()
    stamps, heads = held
    hi, lo = bisect_right(stamps, close), bisect_right(stamps, close - LOOKBACK)
    return tuple(heads[i] for i in range(hi - 1, lo - 1, -1))[:CAP]


def reading(values: dict[str, float]) -> dict[str, object]:
    """EXP-023's: mean over all sessions; every 10th session's stationary bootstrap: interval and two-sided p."""
    if not values:
        return {"sessions": 0, "mean": None, "step_sessions": 0, "step_mean": None, "low": None, "high": None, "p": 1.0}
    series = list(values.values())[::STEP_SESSIONS]
    rng = seeded(SEED)
    means = [sum(series[i] for i in stationary_draws(len(series), BLOCK, rng)) / len(series) for _ in range(RESAMPLES)]
    low, high = percentile_interval(means)
    step_mean = sum(series) / len(series)
    far = sum(1 for m in means if (m <= 0.0 if step_mean > 0.0 else m >= 0.0))
    return {
        "sessions": len(values), "mean": sum(values.values()) / len(values),
        "step_sessions": len(series), "step_mean": step_mean, "low": low, "high": high,
        "p": min(1.0, 2.0 * (1 + far) / (RESAMPLES + 1)),
    }  # fmt: skip


def holm(ps: dict[str, float]) -> dict[str, bool]:
    order, out = sorted(ps, key=lambda c: ps[c]), dict.fromkeys(ps, False)
    for k, c in enumerate(order):
        if ps[c] > ALPHA / (len(order) - k):
            break
        out[c] = True
    return out


def by_year(values: dict[str, float]) -> dict[str, float]:
    years: dict[str, list[float]] = {}
    for k, v in values.items():
        years.setdefault(k[:4], []).append(v)
    return {y: sum(v) / len(v) for y, v in sorted(years.items())}


def finbert_scores(heads: list[str], out_dir: Path, log: dict, check: bool = True) -> dict[str, float]:
    """Each distinct headline once, in batches of 32 ordered by token length; resumable through a JSONL
    cache. The check (Amendment 1): the scores used for the first CHECK_N headlines against one at a time."""
    model = FinBERTModel(model_ref=str(SNAPSHOT))
    pipe = model._pipeline
    cache_path = out_dir / "finbert_scores.jsonl"
    scores: dict[str, float] = {}
    if cache_path.exists():
        for raw in cache_path.read_text("utf-8").splitlines():
            h, v = json.loads(raw)
            scores[h] = v
    todo = [h for h in heads if h not in scores]
    sizes = [len(ids) for ids in pipe.tokenizer(todo)["input_ids"]] if todo else []
    todo = [h for _, h in sorted(zip(sizes, todo, strict=True))]
    lengths = sum(1 for n in sizes if n > 512)
    t0 = time.time()
    with cache_path.open("a", encoding="utf-8") as fh:
        for k in range(0, len(todo), CHUNK):
            chunk = todo[k : k + CHUNK]
            for h, r in zip(chunk, pipe(chunk, batch_size=BATCH, truncation=True), strict=True):
                v = align_label(str(r["label"]), float(r["score"]))
                scores[h] = v
                fh.write(json.dumps([h, v], ensure_ascii=False) + "\n")
            fh.flush()
            done = k + len(chunk)
            print(f"finbert {done}/{len(todo)} {done / max(time.time() - t0, 1e-9):.1f}/s", flush=True)
    log |= {"distinct": len(heads), "scored_now": len(todo), "over_512_tokens_scored_now": lengths,
            "seconds": round(time.time() - t0, 1)}
    if check and heads:
        sample = heads[:CHECK_N]
        one = model.score_headlines(tuple(sample))
        log["check_max_abs"] = max(abs(a - scores[h]) for a, h in zip(one, sample, strict=True))
    return scores


def main(argv: list[str]) -> int:
    cache, exp015_out, news_dir, out_dir = (Path(a) for a in argv[2:6])
    pilot, prescore = "--pilot" in argv, "--prescore" in argv
    out_dir.mkdir(parents=True, exist_ok=True)
    record: dict[str, object] = {"experiment": "EXP-024", "pilot": pilot}
    weights_sha = hashlib.sha256((SNAPSHOT / "pytorch_model.bin").read_bytes()).hexdigest()
    min_own = build_effective_settings(()).analyst.sentiment_min_own_headlines
    record |= {"weights_sha256": weights_sha, "min_own": min_own}
    if weights_sha != WEIGHTS_SHA or min_own != MIN_OWN:
        return stopped(out_dir, pilot, record, "FinBERT weights or min_own differ from the pre-registration")
    panel = load_panel(exp015_out)
    if panel_digest(panel) != PANEL_SHA:
        return stopped(out_dir, pilot, record, "EXP-015's panel digest differs")
    span = PILOT if pilot else WINDOW
    mask = panel.primary & (panel.sessions >= span[0]) & (panel.sessions <= span[1])
    idx = np.flatnonzero(mask)
    sessions, lines = panel.sessions[idx], panel.lines[idx]
    record |= {"window": list(span), "rows": len(idx), "sessions": len(np.unique(sessions))}
    if not pilot and len(idx) != SCORED_ROWS:
        return stopped(out_dir, pilot, record, f"scored window holds {len(idx)} survivor rows, not {SCORED_ROWS}")
    eps = episodes(cache)
    renames = json.loads(RENAMES.read_text("utf-8"))
    record["renames_sha256"] = hashlib.sha256(RENAMES.read_bytes()).hexdigest()
    spans = renames["spans"]
    tickers = np.array([ticker_on(eps, str(ln), str(d), spans) for ln, d in zip(lines, sessions, strict=True)])
    record["rows_on_a_renamed_symbol"] = int(sum(1 for t, ln in zip(tickers, lines, strict=True) if t != ln))
    # the company table is keyed by today's ticker: the line, where it lists the line
    subject = np.array([str(ln) if str(ln) in COMPANY_NAMES else str(t) for ln, t in zip(lines, tickers, strict=True)])
    t0 = time.time()
    index, months, news_log = load_news(news_dir, set(tickers.tolist()))
    in_range = {m: n for m, n in months.items() if MONTHS[0] <= m <= MONTHS[1]}
    median = float(np.median(list(in_range.values()))) if in_range else 0.0
    thin = {m: n for m, n in in_range.items() if n < MONTH_FLOOR * median}
    missing = [f"{y}-{m:02d}" for y in range(2016, 2027) for m in range(1, 13)
               if MONTHS[0] <= f"{y}-{m:02d}" <= MONTHS[1] and f"{y}-{m:02d}" not in in_range]
    record |= {"news": news_log | {"seconds": round(time.time() - t0, 1), "median_month": median,
               "thin_months": thin, "missing_months": missing, "months": months}}
    if (thin or missing) and not prescore:
        return stopped(out_dir, pilot, record, f"news months under a quarter of the median or missing: {thin} {missing}")
    lex = np.full(len(idx), np.nan)
    served_n = np.zeros(len(idx), dtype=int)
    heads_by_row: list[tuple[str, ...]] = [()] * len(idx)
    t0 = time.time()
    days, starts, counts = np.unique(sessions, return_index=True, return_counts=True)
    if not all(bool((sessions[s : s + n] == d).all()) for d, s, n in zip(days, starts, counts, strict=True)):
        return stopped(out_dir, pilot, record, "the panel's rows are not in session order")
    for day, start, count in zip(days, starts, counts, strict=True):
        rows = range(int(start), int(start + count))
        close = int(datetime.combine(date.fromisoformat(str(day)), dtime(16, 0), NY).timestamp())
        batch = {str(tickers[r]): served(index, str(tickers[r]), close) for r in rows}
        weights = batch_headline_weights({t: h for t, h in batch.items() if h})
        for r in rows:
            heads = batch[str(tickers[r])]
            heads_by_row[r], served_n[r] = heads, len(heads)
            raw, _ = subject_sentiment(str(subject[r]), heads, min_own, headline_weights=weights)
            if raw is not None:
                lex[r] = max(0.0, min(1.0, raw / 100.0))
    record["lexicon_seconds"] = round(time.time() - t0, 1)
    distinct = sorted({h for heads in heads_by_row for h in heads})
    fin_log: dict[str, object] = {}
    scores = finbert_scores(distinct, out_dir, fin_log, check=not prescore)
    record["finbert"] = fin_log
    if prescore:  # no target is read in this mode
        (out_dir / "prescore.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", "utf-8")
        print(f"PRESCORED distinct={len(distinct)} scored_now={fin_log['scored_now']}")
        return 0
    if pilot and float(fin_log.get("check_max_abs", 0.0)) > CHECK_TOL:
        return stopped(out_dir, pilot, record, f"FinBERT's used scores off one at a time by {fin_log['check_max_abs']}")
    fin = np.full(len(idx), np.nan)
    for r, heads in enumerate(heads_by_row):
        got = aggregate(tuple(scores[h] for h in heads), 1)
        if got is not None:
            fin[r] = got.value
    targets = {h: panel.excess[idx, j] for j, h in enumerate(HORIZONS)}
    ic_l = {h: session_ic(lex, targets[h], sessions) for h in HORIZONS}
    ic_f = {h: session_ic(fin, targets[h], sessions) for h in HORIZONS}
    on_l = np.isfinite(lex)
    ic_f_on_l = session_ic(fin[on_l], targets[10][on_l], sessions[on_l])
    diff = {d: ic_f_on_l[d] - ic_l[10][d] for d in sorted(ic_f_on_l) if d in ic_l[10]}
    tests = {"H1": reading(ic_l[10]), "H2": reading(ic_f[10]), "H3": reading(diff)}
    carries = holm({k: float(v["p"]) for k, v in tests.items()})
    for k, v in tests.items():
        mean = v["mean"]
        v |= {"carries": carries[k], "sign": None if mean is None else ("+" if mean > 0 else "-"),
              "worth_building_on": bool(carries[k] and k != "H3" and mean is not None and mean >= ECONOMIC)}
    listed = np.isin(subject, list(COMPANY_NAMES))
    years = np.array([str(d)[:4] for d in sessions])
    coverage = {y: {"rows": int((years == y).sum()), "served": float((served_n[years == y] > 0).mean()),
                    "lexicon": float(on_l[years == y].mean()), "finbert": float(np.isfinite(fin[years == y]).mean())}
                for y in sorted(set(years.tolist()))}
    never = sorted(set(tickers.tolist()) - {str(tickers[r]) for r in np.flatnonzero(served_n > 0)})
    record |= {
        "tests": tests,
        "reported": {
            "lexicon_ic5_mean": reading(ic_l[5])["mean"], "lexicon_ic20_mean": reading(ic_l[20])["mean"],
            "finbert_ic5_mean": reading(ic_f[5])["mean"], "finbert_ic20_mean": reading(ic_f[20])["mean"],
            "per_year": {"H1": by_year(ic_l[10]), "H2": by_year(ic_f[10]), "H3": by_year(diff)},
            "coverage": coverage,
            "listed_rows": int(listed.sum()),
            "listed_lexicon": reading(session_ic(np.where(listed, lex, np.nan), targets[10], sessions)),
            "listed_finbert": reading(session_ic(np.where(listed, fin, np.nan), targets[10], sessions)),
            "tickers_never_served": never,
        },
        "verdict": "PILOT" if pilot else "COMPLETE",
    }  # fmt: skip
    name = "pilot" if pilot else "exp024"
    (out_dir / f"{name}.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", "utf-8")
    page = [f"# EXP-024 {record['verdict']}: {span[0]} .. {span[1]}", "",
            f"rows {len(idx)}, served {float((served_n > 0).mean()):.3f}, lexicon {float(on_l.mean()):.3f}, "
            f"finbert {float(np.isfinite(fin).mean()):.3f}", "",
            "| test | mean IC | 95 % interval | p | carries (Holm) | worth building on |", "| --- | --- | --- | --- | --- | --- |"]
    for k, v in tests.items():
        mean, low, high = (v[x] for x in ("mean", "low", "high"))
        cell = "n/a" if mean is None else f"{mean:+.4f} | [{low:+.4f}, {high:+.4f}]"
        page.append(f"| {k} | {cell} | {v['p']:.4f} | {v['carries']} | {v['worth_building_on']} |")
    (out_dir / f"{name}.md").write_text("\n".join(page) + "\n", "utf-8")
    print(f"{record['verdict']} rows={len(idx)} " + " ".join(
        f"{k}={v['mean']:+.4f}[{v['low']:+.4f},{v['high']:+.4f}]p={v['p']:.4f}{'*' if v['carries'] else ''}"
        if v["mean"] is not None else f"{k}=n/a" for k, v in tests.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

### `exp024_overlap.py`

Step 9, the feed overlap.

```python
"""EXP-024 step 9, reported: how much of Finnhub's company news Alpaca's (Benzinga's) feed carries.

A planner's read-only script. For the analyst's company-table tickers, Finnhub /company-news for one
week against the Alpaca items tagged with the ticker and created in the same UTC days. The figure is
the share of Finnhub headlines with an exact, case-folded match among Alpaca's.

  python -B exp024_overlap.py <tree> <repo with .env> <news_dir> <out json> [2026-10-13 2026-10-19]
"""

from __future__ import annotations

import gzip
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(TREE))

from agents.analyst.domain.sentiment_subject import COMPANY_NAMES  # noqa: E402

URL = "https://finnhub.io/api/v1/company-news"


def key(repo: Path) -> str:
    for line in (repo / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("PROVIDER_FINNHUB_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise KeyError("PROVIDER_FINNHUB_API_KEY")


def fold(text: str) -> str:
    return " ".join(text.casefold().split())


def main(argv: list[str]) -> int:
    repo, news_dir, out = Path(argv[2]), Path(argv[3]), Path(argv[4])
    first, last = (argv[5], argv[6]) if len(argv) > 6 else ("2026-10-13", "2026-10-19")
    tickers = sorted(COMPANY_NAMES)
    alpaca: dict[str, set[str]] = {t: set() for t in tickers}
    latest: dict[int, tuple[str, str, str, list[str]]] = {}
    for path in sorted(news_dir.glob(f"{first[:7]}*.jsonl.gz")) + sorted(news_dir.glob(f"{last[:7]}*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for raw in fh:
                item = json.loads(raw)
                held = latest.get(int(item["id"]))
                if held is None or item["updated_at"] > held[0]:
                    latest[int(item["id"])] = (item["updated_at"], item["created_at"], item.get("headline") or "",
                                               [s.replace("-", ".").replace("/", ".") for s in item.get("symbols") or ()])
    for _, created, headline, syms in latest.values():
        if first <= created[:10] <= last and headline:
            for s in syms:
                if s in alpaca:
                    alpaca[s].add(fold(headline))
    token, rows = key(repo), []
    for t in tickers:
        q = urllib.parse.urlencode({"symbol": t, "from": first, "to": last, "token": token})
        with urllib.request.urlopen(f"{URL}?{q}", timeout=30) as r:
            items = json.loads(r.read())
        finn = {fold(i.get("headline") or "") for i in items if i.get("headline")}
        rows.append({"ticker": t, "finnhub": len(finn), "alpaca": len(alpaca[t]), "matched": len(finn & alpaca[t])})
        time.sleep(1.1)
    total_f = sum(r["finnhub"] for r in rows)
    total_m = sum(r["matched"] for r in rows)
    record = {"week": [first, last], "tickers": len(rows), "finnhub_headlines": total_f,
              "alpaca_headlines": sum(r["alpaca"] for r in rows), "matched": total_m,
              "share_of_finnhub_matched": total_m / total_f if total_f else None, "rows": rows}
    out.write_text(json.dumps(record, indent=1) + "\n", "utf-8")
    print(json.dumps({k: v for k, v in record.items() if k != "rows"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

### `run_exp024.ps1`

The runner: `pwsh -NoProfile -File run_exp024.ps1 -Stage fetch|prescore|pilot|scored`.

```powershell
# EXP-024's runs (DL-316): one stage at a time, detached, the machine kept awake, priority BelowNormal.
#   pwsh -NoProfile -File run_exp024.ps1 -Stage fetch|prescore|pilot|scored
param(
    [Parameter(Mandatory)][ValidateSet('fetch', 'prescore', 'pilot', 'scored')][string]$Stage,
    [string]$Tree = 'C:\Users\yury_\Downloads\project\ta-exp024',
    [string]$Repo = 'C:\Users\yury_\Downloads\project\trading-agents',
    [string]$Python = 'C:\Users\yury_\Downloads\project\trading-agents\.venv\Scripts\python.exe',
    [string]$Data = 'C:\Users\yury_\OneDrive\trading-agents-data',
    [string]$Kit = 'C:\Users\yury_\OneDrive\trading-agents-data\exp024-2026-10-23'
)
$ErrorActionPreference = 'Stop'
$log = Join-Path $Kit 'exp024_run.log'
function Say([string]$text) { "$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')) $text" | Add-Content -Path $log -Encoding utf8 }

Add-Type -Namespace Win -Name Power -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint flags);'
[void][Win.Power]::SetThreadExecutionState([uint32]2147483649)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED
try {
    $news = Join-Path $Data 'news-alpaca'
    $out = Join-Path $Data 'experiments\EXP-024'
    if ($Stage -eq 'fetch') {
        $script = Join-Path $Kit 'exp024_news.py'
        $argv = @('-B', '-I', $script, $Repo, $news)
        $wd = $Kit
    } else {
        $script = Join-Path $Kit 'exp024_score.py'
        $argv = @('-B', $script, $Tree, $Data, (Join-Path $Data 'experiments\EXP-015'), $news, $out)
        if ($Stage -eq 'pilot') { $argv += '--pilot' }
        if ($Stage -eq 'prescore') { $argv += '--prescore' }
        $wd = $Tree
        Say "commit $(git -C $Tree rev-parse HEAD) dirty_lines $((git -C $Tree status --porcelain --untracked-files=no | Measure-Object).Count)"
    }
    Say "START $Stage script_sha256 $((Get-FileHash $script -Algorithm SHA256).Hash.ToLower())"
    $stdout = Join-Path $Kit "exp024_${Stage}_stdout.txt"
    $stderr = Join-Path $Kit "exp024_${Stage}_stderr.txt"
    $p = Start-Process -FilePath $Python -ArgumentList $argv -WorkingDirectory $wd `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru
    $null = $p.Handle  # cache the handle, or ExitCode reads empty after the exit
    $p.PriorityClass = 'BelowNormal'
    Start-Sleep -Seconds 5
    Get-CimInstance Win32_Process -Filter "ParentProcessId=$($p.Id)" | ForEach-Object {
        (Get-Process -Id $_.ProcessId).PriorityClass = 'BelowNormal'  # the venv launcher's child
    }
    $p.WaitForExit()
    $tail = (Get-Content $stdout -Tail 3) -join ' | '
    Say "END $Stage exit=$($p.ExitCode) $tail"
} catch {
    Say "ERROR $Stage $($_.Exception.Message)"
} finally {
    [void][Win.Power]::SetThreadExecutionState([uint32]2147483648)
}
```
