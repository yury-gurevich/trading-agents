# EXP-028 — Does an LLM reading headlines published after its training cutoff predict the next day's return?

**Status:** PRE-REGISTERED 2026-10-24 (planner). Sections 1–5 and Appendix P are fixed before any return
is read; the model's labels may be collected first (they are not outcomes).
**Decision / origin:** [DL-317](../../design-log.md) Amendments 4–5; the operator, 2026-10-24: *"let's
see if it works"*, then *"yes, i approve $20 for OpenAI"* · **Cost:** about $1.40 of OpenAI Batch spend
(estimate from token counts), capped at $20 by the script.

## 1. Why we needed this experiment

**The decision that waits.** The operator keeps the fleet running and asked whether an LLM can find
what the price-based tools could not (DL-317 Amendment 4). Training one on our data was ruled out
(lookahead, no signal, a tiny trade record). The one LLM result with evidence after a model's cutoff is
Lopez-Lira and Tang's: ChatGPT-3.5's reading of a headline predicted the next day's return, and a 2026
paper found the signal still significant on 2024 news after the cutoff ([R011](../where-an-edge-can-exist/INDEX.md)).

**What it also answers.** The operator asked whether the fleet's entry (decide at night, buy at the next
open) and the cost of one-day trades can be changed. The same labels, read against four windows of
return, show where any effect sits: overnight, the next day, from the close, or from the open after an
early read.

**Why this model.** Every GPT-3.5 model is retired on the fleet's key *[measured 2026-10-24: 404 on
`gpt-3.5-turbo-0125`, `-1106`, `-16k`, `-instruct`]*; `gpt-4o-mini-2024-07-18`, trained on data to
October 2023, is served. Scoring from 2024-01-01 leaves two months of margin after its cutoff: it cannot
have read any headline it scores, or the prices that followed.

## 2. Hypothesis

**The statistic.** For each decision session *t* with at least one stock the model calls good, P(*t*)
is the mean over those stocks of their **next-day excess return**: from the open of *t* + 1 to its
close, minus the equal-weighted mean of all S&P 500 members over the same hours. **Net** = P(*t*) − 2 ×
5 bps (buy at the open, sell at the close). This is what the fleet can capture as it trades today.

- **H1 — EDGE.** The mean of net P(*t*) over sessions is above 0 with the lower bound of its 95 %
  interval above 0, and the mean is above 0 in each half of the sessions.
- **H0 — NONE.** Otherwise.

**The interval.** Stationary block bootstrap over sessions, mean block 20, 5,000 resamples, seed 0.

**Why this bar.** One model, one primary window: no correction. 5 bps a side is a realistic cost for
liquid S&P 500 names with limit orders, and the cheapest the project has assumed; at 25 bps a one-day
trade needs 0.5 % a day, a bar no published headline signal reaches. Both costs above are reported.

## 3. Data

| Input | Span | Where |
| --- | --- | --- |
| Benzinga headlines (Alpaca news archive, EXP-024) | created 2024-01-01 → 2026-09-24 | OneDrive `trading-agents-data/news-alpaca/` |
| The headline set (`exp028_build.py`): a single symbol, an S&P 500 member on the decision session, de-duplicated by symbol, session and text | **152,728** headlines, 555 symbols, 685 sessions; by arrival: market hours 78,550, before the open 50,608, after the close 19,201, overnight or non-session days 4,369 | kit `headlines.csv.gz` |
| Company names | Alpaca's asset list (150,380 named; the rest use the ticker) | kit |
| S235 cache bars (`adjustment=all`) and membership | to 2026-09-25 | OneDrive `trading-agents-data/` |

The kit is OneDrive `trading-agents-data/exp028-2026-10-24/`.

## 4. Tools and setup

- **Machine** as EXP-026. Python 3.13.2, pandas 3.0.6, numpy 2.5.3, openai 2.49.0, tiktoken 0.13.0.
- **Model** `gpt-4o-mini-2024-07-18`, temperature 0, at most 2 output tokens, via the Batch API.
- **Random seed** 0. **Cost cap** $20 (the operator's), enforced from the batches' recorded usage.

## 5. How it was conducted

1. **Decision session.** A headline belongs to the fleet's nightly run at 18:30 ET: to session *t* if
   it arrives on *t* by 18:30 ET, else to the next session. Its arrival class: market hours (09:30–16:00
   on *t*), after the close (16:00–18:30 on *t*), before the open (on *t* before 09:30), overnight
   (after 18:30 the evening before, or a non-session day).
2. **The prompt** is Lopez-Lira and Tang's, verbatim in Appendix P; one headline per request.
3. **The label.** The first word: YES → +1, NO → −1, anything else 0. Per stock and session, the mean
   of its headlines' labels: **good** above 0, **bad** below 0.
4. **Returns** from the cache, each minus the members' equal-weighted mean over the same window:
   **DAY** open(*t*+1) → close(*t*+1) (primary); **OVN** close(*t*) → open(*t*+1); **CC** close(*t*) →
   close(*t*+1); **DAY0** open(*t*) → close(*t*), for headlines that arrived before *t*'s open (what an
   early-morning read could buy at *t*'s open).
5. **Pilot (before the freeze):** 100 live requests: 53 YES, 28 UNKNOWN, 19 NO, every answer parsed.
6. **Reported, not barred:** the good-minus-bad spread for DAY, OVN, CC and DAY0; good alone and bad
   alone; each by arrival class and by year; at 10 and 25 bps a side; hit rates; label shares.
7. **Failure handling.** No verdict if under 95 % of answers parse or over 1 % of requests fail
   (failures re-run once first).

**What this cannot claim, stated before the result.** OVN measures the move an after-hours or
closing-auction buyer would face, not what they would be filled at (extended-hours prices are not in
daily bars). One model and one prompt; a NONE verdict says this reading of headlines did not carry,
not that no LLM could. The S&P 500 is where the literature finds the effect weakest.

## 6. Results

*Pending.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

## Appendix P — Pre-registration (frozen)

- Model `gpt-4o-mini-2024-07-18`; temperature 0; `max_tokens` 2; one user message:

```text
Forget all your previous instructions. Pretend you are a financial expert. You are a financial expert with stock recommendation experience. Answer "YES" if good news, "NO" if bad news, or "UNKNOWN" if uncertain in the first line. Then elaborate with one short and concise sentence on the next line. Is this headline good or bad for the stock price of {name} in the short term?

Headline: {headline}
```

- Headlines 2024-01-01 → 2026-09-24, one symbol, an S&P 500 member on the decision session; decision
  session by the 18:30 ET rule; labels YES +1, NO −1, else 0; good above 0, bad below 0.
- **Primary:** mean over sessions of [mean next-day (open → close) excess return of the good stocks −
  10 bps]; EDGE if its 95 % interval (stationary block bootstrap, block 20, 5,000, seed 0) is above 0
  and both halves' means are above 0; else NONE.
- Secondary as section 5.6. Cap $20.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

*Pending.*
