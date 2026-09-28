# EXP-016 — Does Jev say how often a trade reaches its target before its stop, and is it right?

**Status:** PRE-REGISTERED 2026-09-28 (planner). **No scored call has been made.** Everything under
*Purpose* and *Process* is fixed before the first scored call. A change after it is a new experiment, not
an edit to this one.
**Decision:** [DL-240](../../design-log.md) (the book as a distribution; the ledger comes first) · operator,
2026-09-28: *"I want to try JEV AI on it"* · work-queue **92** · the Jev idea in [ideas.md](../../ideas.md)
(2026-09-23/24) · test bed from [EXP-011](EXP-011-regime-markov-and-barrier-calibration.md).
**Cost:** Jev bills input only, $0.042 per million tokens; the run is capped at 10 M input tokens ($0.42).

## Purpose

**Question.** For the fleet's own stop and target on a trade, does TypeSafe's **Jev** (`jev-latest`) give
probabilities for *stop first / target first / neither within 10 sessions* that come true, better than the
cheap baselines EXP-011 already scored?

**Why it matters.** DL-240 makes the book a distribution: each position carries the chance of reaching its
target first, its stop first, or neither. Nothing may size on a probability until a ledger shows it comes
true. EXP-011 found the best cheap model (`all_history`, a bootstrap over the name's own past days) beats
climatology by only **0.0060** Brier. Jev returns a calibrated distribution over typed options in one call
for fractions of a cent, so it is the cheapest candidate to try as a challenger. Jev's vendor measures
calibration against frontier models' agreement, not against outcomes; this measures it against outcomes.

**Hypotheses.**

- **H1 (primary): Jev adds to the simulation.** Arm **J2** (features plus the `all_history` estimate) has a
  lower 3-outcome Brier score than `all_history` alone, and the 95 % confidence interval of the difference
  lies below zero.
- **H2 (secondary): Jev forecasts on its own.** Arm **J1** (features only) has a lower Brier score than
  climatology, 95 % interval below zero.
- **H0.** Neither holds. Jev then earns no place as a forecaster in the ledger. That says nothing about the
  other typed decisions the ideas entry proposes to shadow.

Two arms are tested, and each hypothesis names its own arm and baseline; neither is re-labelled after the
fact.

## Process

Everything below is fixed now.

**Test bed: EXP-011's decisions, rebuilt from the replay cache** (`scripts/replay_dataset.py`, OneDrive
`trading-agents-data`: 263,005 SIP bars, 98 names, 2016-01-04 → 2026-09-16; never the repo). A decision at
the close of every 5th session from 2017-01-03, per name. S211's barriers exactly as EXP-011 computed them:
stop = clamp(2 × ATR14 ÷ close, 2.5 %, 8 %); target = median best close-to-high rise within 10 sessions over
the 120 prior settled windows. Outcome over the next 10 sessions: the low is checked before the high (a day
touching both counts as a stop); otherwise neither. **Reproduction check before any scored call:** 47,485
cases with realised shares 0.285 / 0.480 / 0.235. A mismatch stops the run and is reported.

**Test sample.** **60 decision dates** drawn uniformly without replacement from the 2018–2026 decision dates
(seed `20260928`), with every name on each drawn date: about 5,900 cases. Whole dates, because names on one
date move together.

**Pilot (not scored).** Up to **30 cases** from 2017 dates, to check the request and response shapes and the
feature rendering. The prompt is then frozen and recorded in *Delivery*. Pilot answers are never scored.

**Baselines, on the same test cases:**

- **climatology:** outcome shares of all cases in earlier years (EXP-011's yearly refit);
- **`all_history`:** 1,000 simulated 10-session paths per case, resampling the name's own daily moves dated
  at or before the decision (EXP-011's code; seed `20260917`).

**Arms.** One Jev request per case, one `choice` question with three options:

- **`stop_first`**: the low reaches the stop level on some day before the high reaches the target level
  (a day touching both counts here);
- **`target_first`**: the high reaches the target level first;
- **`neither`**: neither level is reached within 10 sessions.

The `state` holds only features computed in code, rounded to 2 decimals, with no ticker, date, sector or
name (Jev's documentation advises keeping arithmetic in code, and anonymity keeps it from recalling a
famous stock's history):

- the barriers: stop distance %, target distance %, target-to-stop ratio;
- volatility: ATR14 % of price; 20-session realised volatility ÷ its 250-session median;
- trend: returns over 5, 20, 60 and 250 sessions %; close against its 50- and 200-session averages %;
  distance below the 250-session high %;
- market: VIX close and the provider's regime label for it.

**J1** sends those features. **J2** sends the same plus the `all_history` probabilities, labelled as a
historical resampling estimate. Nothing else differs.

**Scoring** (test sample only):

- 3-outcome Brier for J1, J2, climatology and `all_history`;
- differences J2 − `all_history` (H1) and J1 − climatology (H2), each with a 95 % interval from 1,000
  resamples of whole dates (seed `20260928`);
- calibration: for P(stop first) and P(target first), declared against realised share in buckets of 0.1,
  shown where a bucket holds at least 50 cases;
- Brier by year, as a check on period effects or recall;
- Jev's `confidence` against its accuracy, descriptive only;
- tokens, cost, latency and errors.

**Failure handling.** A request that fails after 3 attempts is recorded as missing. If more than 2 % of the
test cases are missing, the verdict is INSUFFICIENT. Otherwise the missing cases are dropped from all four
models alike.

## Delivery

*(Empty until the run.)*

## Interpretation

*(Empty until the run.)*
