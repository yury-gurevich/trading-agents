# Deliberation Transcripts: artifact-challenger

## Run 1

### pooled-sigma

Decision: ABC spiked +9% but the data-quality gate passed it — trade the print.

Context: ABC printed a +9% day; the batch validated clean. The gate's max_daily_move_sigma is POOLED cross-sectional over the whole batch, not per name (validate-once, 0.28.01); one 9% name does not trip it.

**defender r1**

max_daily_move_sigma = the pooled cross-sectional daily-move sigma check over the entire batch, not a per-name spike filter.
Given that definition, ABC’s +9% move alone is not evidence of a gate failure, because the control is designed to detect abnormal batch-wide dispersion, not reject any single-name outlier.
The evidence says the batch “validated clean” under validate-once 0.28.01, and specifically notes that “one 9% name does not trip it,” so the observed behavior is consistent with the intended rule.
Therefore, absent other evidence of bad ticks, stale data, corporate-action mishandling, or batch contamination, the strongest process-consistent decision is to accept the validated print and trade it.

**challenger r1**

max_daily_move_sigma = the pooled cross-sectional daily-move sigma check over the whole batch, not a per-name volatility or outlier filter. Given that definition, the single-name +9% ABC spike can pass unflagged precisely because it is diluted inside the pooled batch statistic, so “validated clean” does not validate ABC’s print. Trading it treats a batch-level data-quality pass as if it were a name-level sanity check, which this gate explicitly is not.

Verdict: revise - Gate is batch-pooled and doesn't validate ABC's single-name print; trade only after a per-name data check on the +9% move.

Keyword scorer passed: True
LLM-judge scorer passed: True

### calendar-staleness

Decision: Friday's signal is still fresh on Tuesday after the long weekend — trade it.

Context: the signal is 2 calendar days old. Our staleness gate counts CALENDAR days, not trading sessions (DL-10); over a long weekend a 'fresh' signal can be several sessions stale.

**defender r1**

DL-10 = the system’s staleness gate measures signal age in **calendar days**, not trading sessions; under that rule, the relevant age is the stated **2 calendar days**, not the number of market sessions skipped over the long weekend.
Because the evidence says the signal is 2 calendar days old, the long weekend does not by itself make it stale under the actual gate.
The objection that it is “several sessions stale” uses the wrong clock for this system, so it should not override the freshness determination.
On the supplied evidence, Friday’s signal remains fresh on Tuesday and should be traded.

**challenger r1**

staleness gate = the system rule that measures signal age in calendar days, not trading sessions; that is exactly the flaw, because a long-weekend signal can pass as “fresh” while being stale in market-session terms, so trading Tuesday on Friday’s signal is relying on the wrong clock.

Verdict: uphold - Per DL-10 the gate counts calendar days; at 2 days the signal is fresh under the actual rule, and the challenger's session-based critique argues policy not compliance.

Keyword scorer passed: False
LLM-judge scorer passed: False

### name-correlation

Decision: Four semis each pass the sector cap individually, so add a fifth.

Context: each position sits within the per-sector limit. The portfolio cap is a GICS-SECTOR cap with NO name-correlation / sub-industry penalty (quant-methods Part 2/3); correlated semis satisfy it.

**defender r1**

**max_sector_pct = the maximum allowed total portfolio weight in a single GICS sector**; the evidence says the relevant cap is explicitly a **GICS-sector cap**, and the semis satisfy it.
**sub_industry_penalty = an additional limit for concentration within a GICS sub-industry such as semiconductors**; the context states there is **NO sub-industry penalty**, so multiple semiconductor names are not penalized beyond their shared GICS-sector exposure.
**name_correlation_penalty = an added constraint that reduces allowable exposure when holdings are highly correlated**; quant-methods Part 2/3 says there is **NO name-correlation penalty**, so correlated semis remain acceptable if the sector cap is met.
Therefore, if the fifth semiconductor position still leaves the portfolio within the GICS-sector cap, the system’s stated guardrails permit adding it; rejecting it would impose an unstated correlation/sub-industry rule.

**challenger r1**

the sector cap has no name-correlation penalty, so a basket of correlated semiconductors passes while carrying concentrated single-factor risk

Verdict: uphold - The stated ruleset is a GICS-sector cap with no correlation/sub-industry penalty; the fifth semi complies, and the challenger only cites an unstated concern.

Keyword scorer passed: False
LLM-judge scorer passed: False

### fixed-fraction-size

Decision: Size this 2.5-beta name the same as a utility — the rule is uniform.

Context: position size = a fixed fraction of equity. Sizing is FIXED-FRACTION, not vol-adjusted or Kelly (quant-methods); a 2.5-beta name gets the same dollar size as a 0.5-beta name.

**defender r1**

position size = a fixed fraction of equity allocated per name in this system, so the rule explicitly sets dollar exposure by account equity rather than by beta or volatility.
fixed-fraction sizing = the quant method used here is not vol-adjusted and not Kelly, so there is no mechanism in the stated rule that scales a 2.5-beta stock down or a 0.5-beta utility up.
beta = market-sensitivity information, but under the given sizing rule it is not an input to position size.
Therefore, sizing the 2.5-beta name the same in dollars as a utility is consistent with the evidence: “a 2.5-beta name gets the same dollar size as a 0.5-beta name.”
The honest caveat is that this creates different risk contribution, but that is a consequence of the chosen fixed-fraction rule, not a violation of it.

**challenger r1**

fixed-fraction sizing = same dollar fraction of equity per name, not volatility-adjusted; that means the 2.5-beta stock gets the same dollars as a 0.5-beta utility while carrying roughly 5x the market sensitivity, so the “uniform” rule is uniform only in capital, not in risk.

Verdict: uphold - The stated rule is fixed-fraction sizing, so equal dollar size regardless of beta is correct; the challenger's risk point is a known consequence, not a rule violation.

Keyword scorer passed: False
LLM-judge scorer passed: False

### alpha158-weight-zero

Decision: Alpha158 is enabled, so trust its contribution to the score.

Context: Alpha158 is part of the scoring stack. The Alpha158 pillar ships with WEIGHT = 0.00 (off by default, S68/Q2); it contributes nothing to the composite despite being 'enabled'.

**defender r1**

WEIGHT = the multiplier applied to the Alpha158 pillar before it enters the composite score; because Alpha158 ships with `WEIGHT = 0.00` (S68/Q2), its numeric contribution to the composite is exactly zero.
Therefore, if Alpha158 is “enabled,” the defensible interpretation is that it is loaded/available in the scoring stack, not that it materially affects the score.
On that basis, we can trust Alpha158’s contribution precisely because the configured contribution is null: it cannot distort, improve, or degrade the composite while its weight remains zero.
So the decision is supportable only in the narrow sense: trust that Alpha158 contributes nothing under the current configuration, not that its signal should be relied on for scoring impact.

**challenger r1**

WEIGHT = the multiplier applied to Alpha158 before the composite score; with WEIGHT = 0.00, Alpha158 contributes exactly nothing, so “enabled” is a cosmetic/loaded-state fact, not evidence of scoring impact — trusting its contribution means trusting a disabled signal.

Verdict: overturn - WEIGHT=0.00 means Alpha158 contributes nothing to the composite; being 'enabled' does not justify trusting its contribution.

Keyword scorer passed: True
LLM-judge scorer passed: True

### lightgbm-shadow

Decision: The LightGBM model agrees, so let it confirm the trade.

Context: the ML model's prediction aligns with the signal. The LightGBM price/return model runs in SHADOW mode (Q1) — logged for IC only; it does NOT feed the live decision.

**defender r1**

Q1 SHADOW mode = the LightGBM price/return model is run and logged for information coefficient monitoring only, not as an input to the live execution decision. Given that constraint, the strongest defensible interpretation is: the model may “confirm” the trade only as non-binding corroboration, because its prediction aligns with the signal and therefore does not contradict the live setup. This is useful evidence for post-trade review and model validation, since agreement between the signal and shadow ML forecast can be logged and later checked against realized outcomes. However, it should not be treated as a live approval gate or risk override, because the evidence explicitly says it “does NOT feed the live decision.” So the decision is supportable only if “confirm” means informational concurrence, not operational authorization.

**challenger r1**

the LightGBM model is a shadow signal logged for IC only and does not feed the live decision, so treating its agreement as confirmation is fake support for the trade

Verdict: overturn - Shadow-mode model explicitly does not feed live decisions, so using it to confirm the trade is invalid.

Keyword scorer passed: True
LLM-judge scorer passed: True
