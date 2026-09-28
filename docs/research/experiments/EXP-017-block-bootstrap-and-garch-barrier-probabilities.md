# EXP-017 — Do block-bootstrap or GARCH paths forecast stop-first / target-first better than today's bootstrap, on the history the fleet actually has?

**Status:** PRE-REGISTERED 2026-09-28 (planner). **Nothing has been simulated or scored.** Everything under
*Purpose* and *Process* is fixed before the first simulated path. A change after it is a new experiment.
**Decision:** [DL-240](../../design-log.md) (the book as a distribution; the ledger's challengers are simulation
models) · operator, 2026-09-28: *"EXP-017"* · work-queue **92** · test bed from
[EXP-011](EXP-011-regime-markov-and-barrier-calibration.md), rebuilt as in
[EXP-016](EXP-016-jev-barrier-probabilities.md).
**Cost:** $0 (local simulation; `arch` is pulled in for the run only, not added to the repo).

## Purpose

**Question.** For the fleet's own stop and target, do simulated 10-session paths that keep volatility
clustering, from a **stationary block bootstrap** or a **GARCH(1,1)** model, give better stop-first /
target-first / neither probabilities than the plain per-day bootstrap (`all_history`, EXP-011's best)? And
does any of them still beat climatology when it only sees the **~203 bars** the live fleet has per name?

**Why it matters.** DL-240 builds a ledger of declared against realised probabilities, then lets the PM size
on them. So far the best model beats climatology by only 0.006–0.010 Brier (about 1 % skill), with an
interval that nearly touches zero. A ledger for a model that barely beats averages gives the PM nothing to
size on. This decides whether the live ledger is worth building, and on which model and history depth.

**Hypotheses** (each names its arm and baseline; none is re-labelled afterwards):

- **H1a:** the block bootstrap (`B5`, full history) has a lower 3-outcome Brier than the plain bootstrap
  (`B1`, full history), 95 % interval of the difference below zero.
- **H1b:** GARCH (`G`, full history) has a lower Brier than `B1`, 95 % interval below zero.
- **H2 (production):** at least one model on the **203-bar** history beats climatology, 95 % interval below
  zero.
- **Materiality bar for building the live ledger on a model:** Brier skill against climatology
  (1 − Brier ÷ Brier_climatology) of at least **2 %**, with its 95 % interval above zero, on the history depth
  production would give it. 2 % is double today's best; it is a judgement, set now.
- **H0.** No model meets its hypothesis. Then daily-path models cannot do much better than averages here,
  and exits are chosen by replaying simple rules instead (DL-240 step 5 without a probability model).

Two primary tests (H1a, H1b) are run at 95 % each; that is stated, not corrected, and read with it in mind.

## Process

Everything below is fixed now.

**Test bed.** EXP-011's decisions rebuilt from the replay cache exactly as in EXP-016 (reproduction check:
**47,485** cases, realised 0.285 / 0.480 / 0.235, else the run stops). Barriers: stop = clamp(2 × ATR14 ÷
close, 2.5 %, 8 %); target = median best 10-session close-to-high rise over the 120 prior settled windows.
Outcome over the next 10 sessions, low before high. **Scored:** every case dated 2018–2026 (2017 feeds
climatology only). Every decision has at least 251 prior bars, so both history depths exist for every case.

**Daily moves.** For a name, each session *j* is the triple (high, low, close) relative to the prior close.
Everything a model uses is dated at or before the decision.

**Models** (1,000 paths × 10 sessions per case; a path's barrier rule is the test bed's):

- **`B1` — plain bootstrap** (EXP-011's `all_history`): each simulated day is an independent draw of a past
  session's triple.
- **`B5` — stationary block bootstrap** (Politis–Romano, mean block length **5**): a path starts at a random
  past session and continues through consecutive sessions, jumping to a new random start with probability
  1/5 each day (and whenever it would run past the decision).
- **`G` — GARCH(1,1) with Student-t innovations, filtered historical simulation.** Fitted with `arch`
  (constant mean, returns in %) per name and calendar month on the history available at the month's first
  decision date; decisions later that month reuse those parameters, with the variance recursion run on data
  up to the decision. Standardised residuals z = (r − μ) ÷ σ, and each day's high and low as
  log-distances from the prior close ÷ σ, are resampled together from the fitted history; each simulated
  day's σ follows the GARCH recursion from the decision-day forecast, and its close, high and low are the
  resampled day's scaled by that σ (high and low never cross the close).
- **`climatology`** (baseline): outcome shares of all cases in earlier years.

**History depths.** `full`: everything at or before the decision (up to ~10 years). `short`: the last **203**
sessions only (the live fleet's window). Each of `B1`, `B5`, `G` runs at both depths: six models plus
climatology.

**Scoring** (2018–2026):

- 3-outcome Brier and Brier skill against climatology for all seven;
- H1a (`B5_full` − `B1_full`), H1b (`G_full` − `B1_full`), H2 (each `*_short` − climatology) and the skill
  intervals, from **1,000** resamples of whole decision dates (seed `20260928`);
- calibration of P(stop first) and P(target first) in 0.1 buckets with at least 100 cases;
- Brier by year, and by regime at decision;
- fit failures (a failed fit falls back to the previous month's parameters for that name; the count is
  reported, and more than 2 % failed fits makes `G` INSUFFICIENT).

**Seeds.** Paths: `20260917` (as EXP-011). Date resampling: `20260928`.

## Delivery

*(Empty until the run.)*

## Interpretation

*(Empty until the run.)*
