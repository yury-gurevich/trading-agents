---
type: Architecture Decision
status: accepted
closes: "The reward_risk gate has one distinct value (2.00) across 294 recordings because target and stop are both derived from the same regime base pair, so the ratio is identically base_take_profit_pct / base_stop_loss_pct. Should the gate be retired, or given an independent target derivation? And if the derivation changes, what happens to the 1.5 floor that was calibrated against a constant?"
tags: [analyst, portfolio-manager, risk, reward-risk, stop-target, excursion, threshold, exp-010, exp-011, s211, adr-0017, adr-0025, pm-nev, anlz-obs-05, dl-119]
amends: ADR-0025
---

# ADR 0027 — `reward_risk` compares measured upside against measured downside

**Status:** Accepted · **Date:** 2026-09-16 · **Decider:** operator (*"60 fix"* then *"1 is good"*,
2026-09-16), on a proposal from the planning agent

## Context

[ADR-0025](0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md) narrowed
work-queue item **60** to a choice — give `reward_risk` an independent target derivation, or retire it
as a gate and keep it as a disclosure — and deferred the decision. The planning agent recommended
**retire**. The operator ruled **fix**.

### The pinning is provable, not merely observed

`agents/analyst/domain/stop_target.py:86`:

```python
def _scaled_target(flat_stop, flat_target, scaled_stop):
    return min(flat_target * (scaled_stop / flat_stop), _MAX_PCT)
```

So in scaled mode `target / stop = [flat_target × scaled_stop / flat_stop] / scaled_stop
= flat_target / flat_stop`, and in flat mode it is `flat_target / flat_stop` directly.

**In both modes the ratio is identically `base_take_profit_pct / base_stop_loss_pct`** — 10 % / 5 % =
**2.00**. Measured: **one distinct value across 294 recordings**, never once rejecting.
[S208](../sprints/sprint-208-a-risk-gate-says-what-it-can-reject.md) made the gate *disclose* this
(`comparison=STRUCTURALLY_DETERMINED`); it did not change it.

The target carries **no per-name information**. `reward_risk` is a configuration check wearing a
gate's clothes: it asks whether two constants divide to more than 1.5.

### Would an independent derivation actually discriminate?

*[measured 2026-09-16 against `MarketData` snapshots on the live spine; 98 names, 10-session horizon,
~110 rolling windows each; ratio = median favourable excursion ÷ median adverse excursion]*

| Snapshot | min | p25 | median | p75 | max | below 1.5 | below 1.0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-08-14 | 0.44 | 0.89 | 1.14 | 1.44 | 2.74 | **78 %** | ~40 % |
| 2026-09-14 | 0.60 | 1.04 | 1.36 | 1.68 | 3.11 | 60 % | 17 % |
| 2026-09-15 | 0.60 | 1.04 | 1.35 | 1.66 | 3.00 | 62 % | 21 % |
| **2026-09-16** | **0.60** | **1.04** | **1.35** | **1.66** | **3.00** | **62 %** | **21 %** |

**74 distinct values of 98** on the August snapshot, against the current **one**. The gate would
genuinely discriminate.

🪤 **And the distribution drifts.** The median moved **1.14 → 1.35** in a month while the three recent
snapshots agree to two decimal places. The ratio is stable week-to-week and regime-dependent
month-to-month. This is load-bearing for the threshold decision below.

## Decision

### 1 · The target is derived from measured favourable excursion

The analyst derives `target_pct` from the candidate's **trailing favourable excursion** — the exact
mirror of the adverse-excursion measurement the analyst already performs.
`agents/analyst/domain/stop_target_outcome.py:29` computes *"the deepest close-to-low fall over the
`horizon_days` sessions following the decision bar, as a fraction of the decision close"*
(`ANLZ-OBS-05`). The mirror swaps `min(bar.low)` for `max(bar.high)` and the sign.

Chosen because the machinery, the horizon and the law already exist, and because its **realised**
counterpart is already backfilled onto every `Recommendation`
(`stop_target_observed_drawdown_pct`, `agents/analyst/outcome_backfill.py`) — so the loop that
validates the estimate against what actually happened exists on day one rather than being owed.

⚠️ `observed_drawdown` is a **backfill**, computed after the horizon settles. It cannot set today's
target. The decision-time input is a **trailing** estimate over prior windows from bars already
fetched; the backfilled realised value is the check on it, not the input.

### 2 · The floor moves from 1.5 to **1.0**

> 🚨 **Corrected twice on 2026-09-17, before merge: the gate ships disclosure-only (floor `0`).** First the floor moved to `0.80` (*Correction*: the table above measures a different ratio). Then 10 years of evidence showed the ratio doesn't predict returns (*Correction 2*). See both at the end.

`1.5` was never a judgement about reward against risk. It was a number that sat safely below a
constant 2.00, and it has no meaning independent of that constant. Shipping the new derivation
against the old floor would reject **62 %** of candidates overnight.

**1.0 is a line that can be said out loud:** *never buy a name whose typical 10-session upside is
smaller than its typical downside.* Measured on current data it rejects **21 %** — a real filter, not
a veto of the book.

🪤 **The threshold and the derivation are calibrated together and must move together.** This is
[ADR-0025](0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md)'s finding
one layer down: there, a cap stopped meaning anything when the book's deployment changed underneath
it; here, a floor never meant anything because the quantity it bounded was a constant. A sprint that
changes one and not the other ships a defect either way.

### 3 · The floor is **absolute**, and that is deliberate

The measured distribution drifts with regime. A fixed floor therefore rejects a different *fraction*
of candidates in different months — 21 % today, more in a worse regime.

**That is the intent, not a defect.** In a regime where names offer poor upside for the downside
taken, the correct behaviour is to trade less. This is the opposite case to ADR-0025, where a fixed
cap silently stopped binding: there the constant broke the measurement, here the constant *is* the
policy and the varying rejection rate is the policy working.

🚨 **Recorded so it is not "fixed" later.** A future reader who notices the rejection rate moving with
the regime may be tempted to make the floor relative — a percentile of the current distribution, say.
That would guarantee a fixed fraction of the book passes regardless of whether any of it is worth
buying, which is precisely the failure this ADR exists to end. **Making `reward_risk` relative
requires a new ADR.**

## The road not taken

- **Retire the gate, keep it as a disclosure** (the planning agent's recommendation). Rejected by the
  operator. Recorded because it was the standing recommendation and the reasoning stays valid: a gate
  that cannot discriminate is the shape item 61 closed. The measurement above is what makes *fix* the
  better call — an independent derivation genuinely varies, so there is something real to gate on.
- **Give the target its own ATR multiple** (`target = atr_pct × target_multiplier`). Rejected: both
  legs would still scale with the same ATR, so the ratio stays `target_mult / stop_mult` — constant
  again, with variation only where the stop's floor/ceiling clamps happen to bite. It changes the
  constant without removing the pinning.
- **Scale the target by analyst confidence.** Rejected: confidence is a blended score, not a return
  estimate, and it is already measured as weakly discriminating — the referee noted on
  `sched-2026-09-15` that the confidence floor *"rejected 0 of 29"*. Deriving a price target from it
  would inherit that.
- **Derive the target from price structure** (swing highs, resistance). Not rejected on merit —
  deferred. It needs a swing-detection component that does not exist, where the excursion mirror is
  ~20 lines against machinery already in place. Revisit if excursion proves a poor estimator against
  the backfilled realised values.
- **Keep 1.5 and let the book contract.** Rejected: a 62 % rejection rate is not a considered risk
  posture, it is an un-recalibrated constant.
- **Make the floor a percentile of the live distribution.** Rejected: see §3.

## Consequences

- Work-queue item **60** is specified, and its recorded size — *"small, fix or retire either way"* —
  is **wrong**. It is a derivation change in the analyst plus a threshold change in the PM plus a
  law cycle across both agents. The row is corrected rather than discovered mid-sprint.
- 🪤 **The change lands in the analyst, not the PM**, where the row is filed.
  `resolve_stop_target` lives in `agents/analyst/domain/stop_target.py` and is called from
  `agents/analyst/domain/recommend.py:163` — the target is **analyst-authored**, and `reward_risk` is
  a PM *gate* reading it. So the derivation moves in the analyst and only the threshold moves in the
  PM. (Exit authority between monitor and analyst is settled separately by
  [ADR-0017](0017-exit-authority-alpha-proposes-risk-disposes.md); it is not the authority for this
  change, and is cited here only so the next reader does not assume a conflict.)
- **Both law books are touched.** The analyst's, for a target derived from measured excursion
  (`ANLZ-OBS-05` is the adjacent clause); the PM's, because `reward_risk`'s threshold and its
  `STRUCTURALLY_DETERMINED` disclosure both change — a gate that now varies **must not** be labelled
  structurally fixed, which `PM-OBS-04` already requires.
- 🟠 **The estimate is unconditional.** It measures what a name typically does, not what it does when
  the analyst has chosen to buy it. The backfilled realised values are the means to close that gap;
  the first sprint does not close it, and must say so rather than imply the estimate is conditional.
- The `1.5` value currently in `min_reward_risk_ratio`
  (`agents/portfolio_manager/settings.py:67`) becomes `1.0`, with the `why=` restated: it is now a
  bound on a measured quantity, not on a constant.

## Correction — 2026-09-17, at S211's handback, before merge

**What went wrong.** The *Evidence* table measures **median favourable excursion ÷ median adverse
excursion**. Decision 1 derives the **target** from the favourable excursion, and S211's spec kept the
**stop** untouched (2 × ATR, clamped) as an invariant. `reward_risk` reads `target_pct ÷ stop_pct`, so the
quantity actually built is **median favourable excursion ÷ ATR stop**, with a different denominator from the one the
1.0 floor was chosen on. The planning agent introduced this when writing the spec. The implementation
followed the spec correctly.

**Measured on the built code**
([EXP-010](../research/experiments/EXP-010-reward-risk-floor-on-the-built-ratio.md): S211 branch, live
`MarketData`, 98 names × the last three scheduled runs, production `scaled` mode):

| Floor | Share of names rejected on the built ratio |
| --- | --- |
| 1.00 | **55 % · 58 % · 68 %** |
| 0.85 | 26 % · 28 % · 29 % |
| **0.80** | **17 % · 16 % · 18 %** |
| 0.75 | 12 % · 11 % · 16 % |

The built ratio's median is **0.93-0.98**, against 1.23 for this ADR's ratio on the same bars. Shipping 1.0
would have rejected most of the book: the exact failure decision 2 warns about, one layer down.

**Therefore (operator, 2026-09-17, *"0.80"*):**

1. **Decision 2 is amended: `min_reward_risk_ratio` = `0.80`.** Said out loud: *never buy a name whose
   typical 10-session upside is less than four-fifths of the distance to its stop.* It keeps the roughly
   one-in-five filter the 1.0 ruling was made for.
2. **Below 1.0 is not looser than the original sentence.** The target is a median excursion, which half of
   prior windows reach. The median name's stop sits about 1.3× beyond its median adverse excursion, so fewer
   than half of windows reach the stop. Requiring the target to at least equal the stop is therefore stricter
   than requiring typical upside to at least equal typical downside.
3. **§3 is unchanged:** the floor stays absolute. 0.80 is a calibration point on three nights in one regime,
   not a promise about the rejection share.
4. **Decision 1 is unchanged.** Stop invariant, median estimator, and trailing windows all stand.

**Consequence not stated above.** The target's median falls from **8.4-9.1 %** (2 × stop) to **4.2 %**. No
exit reads it: exit triggers are `stop` and `thesis` only (`agents/analyst/domain/recommend.py:26`). So this
changes the gate and what the deliberator is shown, not when positions close.

**Road not taken:**

- **Keep 1.0.** Rejects 55-68 %, a veto of the book rather than a filter.
- **Gate on this ADR's ratio instead** (favourable ÷ adverse, ~30 % below 1.0 on the replay). Rejected: the
  gate would stop comparing the target with the stop actually placed, and it needs a further contract field
  for the adverse estimate.
- **0.85.** Rejects 26-29 %, stricter than the filter that was approved.

## Correction 2 — 2026-09-17, same evening, before merge: the gate is disclosure-only

**What the first correction didn't test:** whether the ratio says anything about the trade.
[EXP-011](../research/experiments/EXP-011-regime-markov-and-barrier-calibration.md) recomputed S211's exact stop
and target on 10 years of consolidated-tape bars for the 98 names (47,485 decisions, 2017-2026). It measured
the realised trade return with the full payoff: −stop, +target, or the 10th-session close.

- **The ratio doesn't predict returns.** Names at or above 0.80 minus names below: **+0.03 %** per trade
  [95 % CI −0.17 %, +0.23 %]. That's +0.10 % in 2017-2021 and **−0.08 %** in 2022-2026, and no ratio bucket
  stands out.
- **The rejection share at 0.80 swings from 0 % to 99 % a night.** Median **49 %**, p90 89 %, and more than half
  the book on 47 % of nights. The first correction's 16-18 % was measured on three nights at the **10th
  percentile**. A reasoned mechanism, consistent with 2018 and 2022: the stop reads 14 sessions and the
  target about 6 months, so after a volatility spike the ratio collapses across the whole book.
- **What the target does get right:** it was touched within 10 sessions **50.2 %** of the time, exactly as a
  median should be. Decision 1 is sound.

**§3's premise is measured and not found.** §3 accepted a rejection rate that moves with the market, on the
reasoning that in poor regimes the correct behaviour is to trade less. That requires low-ratio names to be
worse buys, and on this evidence they aren't.

**Therefore (operator, 2026-09-17, *"Disclosure only"*):**

1. **`min_reward_risk_ratio` = `0`.** The measured target, its evidence and the varying ratio appear in every
   gate report, and no order is rejected on the ratio. A non-positive stop still rejects (`invalid_stop_loss`).
   That is a validity check, not this policy.
2. **The detail must say so.** With the floor at 0 the gate can't fail, so `PM-OBS-04` requires the detail to
   disclose it rather than read `comparison=INFORMATIVE`.
3. **This supersedes decision 2 and *Correction*'s 0.80.** Decision 1 (the derivation) and the stop invariant
   stand. §3's absolute-floor rule stands for any future floor: re-enabling the gate needs evidence that the
   ratio predicts returns, and a relative floor still needs a new ADR.
4. This is the planning agent's original recommendation (*retire as a gate, keep as a disclosure*), now
   adopted on measurement rather than argument.

**Road not taken:**

- **Keep 0.80.** Rejects a median 49 % of names a night for no measured benefit.
- **A low floor such as 0.60** (a crash guard). It still filters on a quantity with no measured predictive
  power, and "crash guard" is the stop's job.
- **Hold S211 until more evidence.** Rejected: the derivation, the evidence fields and the honest disclosure
  are worth shipping now. Only the rejection was unproven.
