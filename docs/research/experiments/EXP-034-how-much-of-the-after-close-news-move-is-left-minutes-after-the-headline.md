# EXP-034 — How much of the after-close news move is left minutes after the headline?

**Status:** PRE-REGISTERED 2026-10-24 (planner). Sections 1–5 and Appendix P are fixed before any
minute price is read.
**Amendment 1 — 2026-10-24, before any return was read (planner).** The coverage pilot found that many
stocks do not trade in the minutes after an evening headline: no minute bar starts after τ by τ + 1
minute for 65 % of events, by τ + 5 for 49 %, by τ + 15 for 38 %, by τ + 60 for 25 %. Section 5.2's
rule would price those entries at the last trade *before* the headline, a price no order placed after
the news could get. **The primary is therefore computed on the events with a trade after the headline
by τ + 5 minutes** (the entry bar starts at or after τ's minute); the as-registered all-events figure
is reported beside it. Nothing else changes.
**Decision / origin:** [EXP-028](EXP-028-does-an-llm-reading-headlines-after-its-cutoff-predict-the-next-day.md)
§7.4 and §8; the operator, 2026-10-24, on the fleet's next-open entry: *"Is this something that can be
changed?"* · [DL-319](../../design-log.md) · **Cost:** $0 (Alpaca market data; no new LLM call).

## 1. Why we needed this experiment

EXP-028 found that `gpt-4o-mini` reads after-close headlines correctly: the stocks it called good rose
0.38 % by the next open and those it called bad fell 1.06 % (a spread of 1.43 %), but the whole move sits
in the overnight gap, before the fleet's next-open entry. Alpaca accepts extended-hours limit orders
(16:00–20:00 ET), and its minute bars include extended hours *[measured 2026-10-24: AAPL on 2024-05-02,
bars through the evening and the pre-market]*. If part of the move is still there a few minutes after a
headline, an event-driven reader (news stream → model → after-hours order) could take it. If it is gone
within a minute, no build can.

## 2. Hypothesis

**Events.** EXP-028's stock-sessions whose headlines arrived after the close (16:00–18:30 ET), labelled
good or bad by the mean of those headlines' labels (EXP-028's, unchanged). The event time τ is the first
after-close headline's timestamp.

**The statistic.** For a delay L, the entry price is the close of the last minute bar that starts before
τ + L; the exit is the next session's open (the S235 cache, as EXP-028). X_L = the stock's return from
entry to exit minus SPY's over the same window (SPY's minute bars and next open).

- **Primary, H1 — the move can be taken.** For L = 5 minutes, the per-session mean of the good stocks'
  X_5, **net of 20 bps** (an after-hours limit entry and an opening exit), is above 0 with the lower
  bound of its 95 % interval above 0, and above 0 in each half of the sessions.
- **H0 — it cannot.** Otherwise.

**The interval.** Stationary block bootstrap over sessions, mean block 20, 5,000 resamples, seed 0.

**Why this bar.** Five minutes covers a news stream's delivery, a model call and an order with room to
spare; 20 bps a round trip allows for after-hours spreads several times the regular session's. Only the
good side is primary: the fleet buys, it does not sell short.

## 3. Data

EXP-028's kit (`headlines.csv.gz`, the labels in `out_req_*.jsonl`); Alpaca SIP **1-minute bars**,
`adjustment=all`, 16:00–20:00 ET on each event session, for the event symbols and SPY (fetched for this
experiment, kit `exp034-2026-10-24/`); the S235 cache's daily opens for the exit.

## 4. Tools and setup

Machine as EXP-026; Python 3.13.2, numpy, pandas; the provider's Alpaca data key; no LLM; $0.

## 5. How it was conducted

1. Event stock-sessions from EXP-028's after-close headlines (labels as frozen there); τ per stock-
   session. L = 1, 5, 15, 60 minutes.
2. Entry price as section 2; if no bar falls between τ and τ + L, the last earlier bar's close is used
   and the event is flagged stale (its share reported).
3. Exit: the next session's open in the S235 cache; SPY's from the SPY benchmark file.
4. **Reported, not barred:** good minus bad and good alone at every L, and the share of EXP-028's
   close-to-open spread still left at each L; the result at 10 and 40 bps; stale shares; by year.
5. **Pilot (before the freeze):** coverage only (events with an entry bar and an exit), no return.

**What this cannot claim.** A minute bar's close is not a fill: an order arriving at τ + 5 minutes may
trade worse, more so in thin evening trading, which the 20 bps is meant to absorb. Benzinga's
timestamp may lag the company's release by seconds or minutes; the delay is counted from what the
fleet would see.

## 6. Results

*Pending.*

## 7. Conclusions

*Pending.*

## 8. Recommended code changes, and how to implement them

*Pending.*

## Appendix P — Pre-registration (frozen)

- Events: EXP-028's after-close stock-sessions (headlines 16:00–18:30 ET on the decision session),
  label = mean of their EXP-028 labels; good > 0, bad < 0; τ = the first such headline's timestamp.
- Entry at L ∈ {1, 5, 15, 60} minutes: the close of the last 1-minute bar starting before τ + L (stale
  if none starts after τ). Exit: the next session's open. X_L = stock return − SPY return over the same
  window.
- **Primary:** L = 5, good stocks, per-session mean of X_5 − 0.20 %; H1 if the 95 % interval's lower
  bound (stationary block bootstrap, block 20, 5,000, seed 0) is above 0 and both halves' means are
  above 0; else H0.

## Appendix R — Run record

*Pending.*

## Appendix S — Scripts

*Pending.*
