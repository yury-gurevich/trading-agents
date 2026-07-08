# Deliberation Transcripts: artifact-judge

## Run 1

### pooled-sigma

Decision: ABC spiked +9% but the data-quality gate passed it — trade the print.

Context: ABC printed a +9% day; the batch validated clean. The gate's max_daily_move_sigma is POOLED cross-sectional over the whole batch, not per name (validate-once, 0.28.01); one 9% name does not trip it.

**defender r1**

Defend the decision: **trade the print**.

**data-quality gate = the batch-level validation step that decides whether the incoming dataset is clean enough to use for trading**, and the evidence says the batch “validated clean.” **max_daily_move_sigma = a pooled cross-sectional daily-move check across the whole batch, not a per-name outlier filter**, so ABC’s isolated +9% move is not, by design, sufficient to fail the gate. This is exactly consistent with validate-once 0.28.01: the system is checking whether the batch distribution is anomalous, not whether any single stock had a large return. Therefore, absent another explicit per-name halt, stale-price flag, corporate-action issue, or failed validation, the clean batch means ABC’s +9% print is accepted as valid input. The strongest case for the decision is that rejecting it would invent a per-name guardrail the documented gate does not contain.

**challenger r1**

**data-quality gate = the batch-level validation step that decides whether the incoming dataset is clean enough to use for trading**, and it only says the batch is usable, not that every individual name’s print is economically tradable. **max_daily_move_sigma = a pooled cross-sectional daily-move threshold over the whole batch**, so it is structurally blind to exactly the failure mode here: a single-name bad tick, split/dividend/corporate-action miss, stale prior close, or venue-specific anomaly. “Gate passed” is therefore weak evidence for ABC specifically; it proves only that ABC’s +9% did not distort the pooled batch enough to fail validation. Trading the print confuses batch cleanliness with name-level truth and creates an obvious adverse-selection risk: the more extreme the single-name move, the more you need per-name scrutiny, precisely where this gate gives you none. The decision should be rejected unless an independent ABC-level price/corporate-action/news check confirms the +9% move.

Verdict: revise - the single-name +9% cannot trip the pooled cross-sectional gate, so the outlier passes unflagged without per-name verification

Keyword scorer passed: True
LLM-judge scorer passed: True

### calendar-staleness

Decision: Friday's signal is still fresh on Tuesday after the long weekend — trade it.

Context: the signal is 2 calendar days old. Our staleness gate counts CALENDAR days, not trading sessions (DL-10); over a long weekend a 'fresh' signal can be several sessions stale.

**defender r1**

**DL-10 staleness gate = the system rule that measures signal age in calendar days, not trading sessions.** On that rule, the relevant fact is not that Tuesday follows a long weekend, but that **signal_age_calendar_days = elapsed calendar days since the signal timestamp**, and the evidence says it is **2 calendar days old**. If the system classifies a 2-calendar-day-old signal as “fresh,” then the long weekend does not create an additional staleness penalty under DL-10. The concern that it “can be several sessions stale” is not operative here because DL-10 explicitly does **not** count trading sessions. Therefore, on the stated evidence and the system’s own staleness definition, the signal remains fresh and should be traded, assuming no other gate blocks it.

**challenger r1**

**DL-10 staleness gate = the system rule that measures signal age in calendar days, not trading sessions.** That rule cuts against the decision: a “Friday signal on Tuesday after a long weekend” is not inherently 2 calendar days old, so the evidence either has a timestamp problem or the “Friday” label is being misused.

**signal_age_calendar_days = elapsed calendar days from the signal timestamp to the trade evaluation time.** If that value is truly 2, then this is not a normal Friday-to-Tuesday signal; if it is Friday-to-Tuesday, the age calculation is wrong and the staleness gate is being bypassed on bad data.

**freshness_threshold_calendar_days = the maximum allowed calendar age before DL-10 blocks the signal.** The defender never states this threshold, so “2 days is fresh” is an unsupported assumption, not a conclusion.

**trade_eligibility = permission to execute only after all required gates pass, not merely the staleness gate.** Even if DL-10 passes, “trade it” is overreach unless data validity, market-regime, risk, liquidity, and execution gates are also cleared.

Verdict: revise - the staleness gate counts calendar days not trading sessions, so the long-weekend gap leaves it stale in session terms while it reads fresh

Keyword scorer passed: True
LLM-judge scorer passed: True

### name-correlation

Decision: Four semis each pass the sector cap individually, so add a fifth.

Context: each position sits within the per-sector limit. The portfolio cap is a GICS-SECTOR cap with NO name-correlation / sub-industry penalty (quant-methods Part 2/3); correlated semis satisfy it.

**defender r1**

max_sector_pct = the maximum allowed portfolio exposure to a GICS sector. The evidence says the applicable portfolio cap is a GICS-SECTOR cap, and that the semiconductor positions satisfy it. name-correlation / sub-industry penalty = an additional restriction that would reduce or block exposure because multiple names are economically correlated or in the same sub-industry; the evidence explicitly says this system has none. Therefore, correlated semiconductor holdings are not penalized merely for being semis, and the fifth semi is permissible so long as the resulting GICS-sector exposure remains within max_sector_pct. On the stated evidence—“each position sits within the per-sector limit” and “correlated semis satisfy it”—adding the fifth is consistent with the rule set.

**challenger r1**

max_sector_pct = the maximum allowed aggregate portfolio exposure to a GICS sector, not a per-name limit.
name-correlation / sub-industry penalty = an extra concentration haircut for economically similar names, which this system explicitly does not apply.
The decision’s failure is that “each position sits within the per-sector limit” is irrelevant if max_sector_pct is aggregate: five 8% semiconductor names can each be below a 25% cap while the sector totals 40% and violates it.
“No correlation penalty” only means semis are not further penalized beyond the GICS-sector cap; it does not license unlimited accumulation inside the same sector.
The fifth semi is valid only if total GICS-sector exposure after adding it remains ≤ max_sector_pct, and the decision has not shown that.

Verdict: revise - the sector cap has no name-correlation penalty, so correlated semis pass while carrying concentrated single-factor risk

Keyword scorer passed: True
LLM-judge scorer passed: False

### fixed-fraction-size

Decision: Size this 2.5-beta name the same as a utility — the rule is uniform.

Context: position size = a fixed fraction of equity. Sizing is FIXED-FRACTION, not vol-adjusted or Kelly (quant-methods); a 2.5-beta name gets the same dollar size as a 0.5-beta name.

**defender r1**

fixed-fraction sizing = each position is sized as the same preset fraction of account equity, so the evidence directly supports sizing the 2.5-beta name the same in dollars as a utility.
beta = the stock’s sensitivity to broad-market moves, and while a 2.5-beta name is expected to move more than a 0.5-beta utility, this system’s stated sizing method does not use beta as an input.
vol-adjusted sizing = changing position dollars based on expected volatility, and the context explicitly says sizing is “not vol-adjusted.”
Kelly sizing = changing position size based on estimated edge and variance, and the context explicitly says sizing is not Kelly.
Therefore, under the documented uniform fixed-fraction rule, giving the 2.5-beta name the same dollar allocation as the utility is consistent with the system rather than an exception.

**challenger r1**

fixed-fraction sizing = dollar position size is a preset fraction of account equity, and that rule only standardizes capital deployed, not risk taken.
beta = the name’s sensitivity to broad-market moves, so a 2.5-beta stock can dominate portfolio drawdown relative to a 0.5-beta utility at the same dollar size.
The decision confuses “uniform dollars” with “uniform exposure”: same capital allocation creates radically different market-risk allocation.
The failure mode is obvious—one high-beta position can consume the risk budget, amplify correlated selloffs, and make the portfolio’s realized leverage unintentionally dependent on security mix.
If the rule truly ignores beta, then the rule is mechanically consistent but risk-blind; sizing this name the same as a utility is not justified by risk control, only by obedience to a crude convention.

Verdict: revise - fixed-fraction sizing is not vol-adjusted, so a 2.5-beta name carries far more risk per position than a utility at the same dollar size

Keyword scorer passed: True
LLM-judge scorer passed: True

### alpha158-weight-zero

Decision: Alpha158 is enabled, so trust its contribution to the score.

Context: Alpha158 is part of the scoring stack. The Alpha158 pillar ships with WEIGHT = 0.00 (off by default, S68/Q2); it contributes nothing to the composite despite being 'enabled'.

**defender r1**

WEIGHT = the Alpha158 pillar’s multiplier in the composite scoring stack; because Alpha158 ships with WEIGHT = 0.00 per S68/Q2, any Alpha158 signal is multiplied to zero before affecting the final score.
So the strongest defense is not that Alpha158 materially improves the composite, but that enabling it is safe to “trust” operationally because its current contribution is exactly nil.
The evidence says Alpha158 is part of the scoring stack and is “enabled,” so its code path/configuration may be active, but with WEIGHT = 0.00 it cannot move rankings, scores, or decisions.
Therefore, trusting its contribution is defensible only in the narrow sense that its contribution is known, bounded, and non-impactful: zero.

**challenger r1**

WEIGHT = the Alpha158 pillar’s multiplier in the composite scoring stack; with WEIGHT = 0.00, “trust its contribution” is a category error because there is no contribution to trust.

“Enabled” = Alpha158’s code path/configuration is active; enabled status does not imply score impact, predictive validity, or production relevance.

The failure mode is semantic drift: operators may believe Alpha158 is influencing decisions when the composite is actually unchanged, creating false confidence, bad attribution, and wasted debugging when outcomes do not reflect Alpha158.

The decision should be rejected or rewritten as: “Alpha158 is enabled but currently has zero scoring impact due to WEIGHT = 0.00.”

Strongest objection: if Alpha158 is off by default via zero weight, treating it as trustworthy signal is not just unsupported—it directly contradicts the supplied configuration evidence.

Verdict: revise - the Alpha158 weight is 0.00, so although enabled it contributes nothing to the score — trusting it relies on a disabled signal

Keyword scorer passed: True
LLM-judge scorer passed: True

### lightgbm-shadow

Decision: The LightGBM model agrees, so let it confirm the trade.

Context: the ML model's prediction aligns with the signal. The LightGBM price/return model runs in SHADOW mode (Q1) — logged for IC only; it does NOT feed the live decision.

**defender r1**

SHADOW mode = the LightGBM model is logged for information-coefficient monitoring only and does not feed the live trading decision.
Given that definition, the strongest defensible interpretation is that LightGBM can “confirm” the trade only as non-binding corroboration: its prediction aligns with the signal, so it adds evidence that the signal is not isolated.
Q1 = the current deployment phase of the LightGBM price/return model, in which it is observed rather than trusted for execution control.
Because Q1 explicitly excludes live-decision input, the trade should still be approved or rejected by the existing live signal/risk process; LightGBM alignment may be recorded as supportive evidence but should not be treated as an execution gate.
So the decision is defensible only if “confirm” means “log as aligned supporting evidence,” not “allow the model to authorize the trade.”

**challenger r1**

SHADOW mode = the LightGBM model is logged for IC monitoring only and does not feed the live decision, so using it to “confirm the trade” is a direct process violation if confirm affects approval, sizing, timing, or override confidence.
IC monitoring = tracking predictive correlation out-of-sample for research validation, not proving the model is calibrated, causal, stable, or safe for execution.
Q1 = the model’s observed-but-not-trusted deployment phase, which means any appeal to its agreement is exactly the unapproved backdoor you are supposed to avoid.
“Aligns with the signal” = directional agreement only, and without live eligibility, calibration checks, regime validation, leakage controls, and risk integration, it adds no legitimate execution authority.
The weakest assumption is that agreement from a non-live model is independent evidence rather than duplicated signal exposure or data-mined comfort; the decision should be rejected unless LightGBM is logged only and the trade stands entirely on the approved live process.

Verdict: revise - the LightGBM model runs in shadow mode logged for IC only and does not feed the live decision, so its agreement adds no real confirmation

Keyword scorer passed: True
LLM-judge scorer passed: True
