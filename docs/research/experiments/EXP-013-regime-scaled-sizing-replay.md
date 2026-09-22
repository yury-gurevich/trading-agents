<!-- Agent: research | Role: experiment record for work-queue item 64 — does the regime label deserve to move a risk number? -->
# EXP-013 — Scaling position size by the regime label, replayed 2017–2026

**Status:** COMPLETE · **Date:** 2026-09-22 · **Cost:** $0 (cached bars, no network at run time, no LLM)
**Closes:** work-queue item **64** · **Corrects:** [ADR-0031](../../decisions/0031-regime-scales-the-risk-budget-atr-keeps-the-stop.md)
**Reproduce:** `uv run python scripts/replay_dataset.py` once, then
`uv run python scripts/exp013_regime_sizing.py`

## Why this exists

Work-queue item 64 has been open since 2026-09-15 on one complaint: *the regime label is computed,
stored and carried, and never changes a single risk number.* Two ADRs narrowed it and neither shipped
code. The remaining task, as written, was **"measure the multiplier for the risk budget"**.

🚨 **That task could not be done as specified, because its target no longer exists.**

- **2026-09-18** — [ADR-0025's Correction](../../decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md)
  **withdrew Decision B** on [EXP-012](EXP-012-volatility-sizing-ten-year-replay.md)'s evidence:
  iso-risk sizing lost **$11,619** over 47,549 decisions, 100 % of bootstrap resamples negative.
  Fixed **1 % notional** sizing stands as champion, and item 62 closed with **no code change**.
- **2026-09-20** — ADR-0031 assigned the regime the **risk budget**, a quantity that exists only
  under risk-based sizing, and said the regime attaches to it *"when that lands"*.

🪰 **ADR-0031 cites EXP-012 zero times.** It was written two days after the correction that removed
its premise. The risk budget cannot land; it was measured and declined.

So the only coherent live question is the one ADR-0031 had assigned to *neither* owner: **should the
regime scale the notional cap — the sizing knob that actually exists?**

## Method

**Data.** [EXP-011](EXP-011-regime-markov-and-barrier-calibration.md)'s dataset, rebuilt: **98 names,
263,005 split- and dividend-adjusted SIP daily bars, 2016-01-04 → 2026-09-16** (Alpaca), plus Cboe's
keyless VIX history (9,277 sessions, 1990 → 2026-09-21). 🪤 **It had to be rebuilt because it was
gone** — EXP-011 and EXP-012 each carried their loader as a markdown appendix and left the data in a
scratch directory. It is now built by `scripts/replay_dataset.py` and cached outside the worktree.

**Population.** EXP-011's grid: a decision at the close of every 5th session from 2017-01-03, per
name — **47,533 decisions**. (EXP-012 reported 47,549 on the same grid with a slightly different
warm-up requirement.)

**Production mirror.** Read from the code, not restated: `classify_regime` with
`ProviderSettings` thresholds (VIX ≤ 15 `risk_on`, ≥ 20 `risk_off`, ≥ 25 `high_volatility`,
≥ 35 `extreme_volatility`), and the ADR-0013 scaled stop
`clamp(scaled_stop_atr_multiplier × ATR14 / close, floor, ceiling)` from `AnalystSettings`.

**Arms.** The champion is today's flat weight. Challengers apply a per-regime multiplier to position
size — the ADR-0031 direction, *less risk when the market is dangerous* — at two strengths. A third,
**inverted**, arm is not a proposal: it prices the direction of the gradient.

## Result 1 — the label does move, but not for long enough

Over 2017-2026 the classifier is not stuck: **409 label changes in 2,475 sessions (16.5 % of days)**,
and all five labels are used — `neutral` 35.6 %, `risk_on` 32.5 %, `risk_off` 16.9 %,
`high_volatility` 12.4 %, `extreme_volatility` 2.5 %. So item 64's own cheap test — *"if it is one
value on every run, the question is moot"* — is **passed**: roughly a third of days are non-neutral.

🪤 **But the median run length is 2 sessions, against a 10-session holding horizon.** A position
sized by the label at entry is usually held through a different regime. That bounds how much any
multiplier could be worth before a single dollar is measured.

## Result 2 — returns rise with stress, and so does return per unit of risk

Forward 10-session return by the regime at entry, under the deployed stop bracket:

| Regime | n | mean % | stdev | mean/sd | win % |
| --- | --- | --- | --- | --- | --- |
| `risk_on` | 15,025 | 0.644 | 4.196 | 0.1535 | 53.1 |
| `neutral` | 17,123 | 0.287 | 5.041 | **0.0570** | 48.4 |
| `risk_off` | 8,234 | 0.923 | 5.469 | 0.1687 | 54.4 |
| `high_volatility` | 5,879 | 0.909 | 6.453 | 0.1409 | 53.1 |
| **`extreme_volatility`** | 1,272 | **1.880** | 8.646 | **0.2174** | 56.4 |

🎯 **The stressed buckets are the best ones, and not only in raw return.** `extreme_volatility` has
the highest mean *and* the highest mean/sd; `neutral` is the **worst** on both. Without the bracket
the ordering is the same and steeper (`neutral` 0.246 % → `extreme_volatility` 2.105 %).

🪰 **The stop bracket is already doing the volatility job.** Stop-out rates are nearly flat across
regimes (29.8 %–34.0 %) because the stop is ATR-scaled and widens with volatility — mean stop 3.60 %
in `risk_on`, 7.30 % in `extreme_volatility`. Loss per stop-out is capped by construction, which is
why the left tail does not punish the stressed buckets.

## Result 3 — every "less risk when stressed" arm loses

Summed weighted return, deployed stop bracket, pct-points over 47,533 decisions:

| Arm | Total | Delta |
| --- | --- | --- |
| champion (flat 1.0) | 29,926 | — |
| mild (1.1/1.0/0.9/0.8/0.6) | 28,108 | **−1,818** |
| strong (1.2/1.0/0.8/0.6/0.4) | 26,769 | **−3,157** |
| *inverted* (0.8/1.0/1.2/1.4/1.6) | 33,083 | *+3,157* |

**Ticker-cluster bootstrap on the strong arm** (2,000 resamples over 98 names):
**95 % CI [−3,699, −2,574] pct-points, 100 % of resamples negative.**

🎯 **Same mechanism EXP-012 found, and stronger.** EXP-012 showed mean return rising with stop width
(decile 2 +0.092 % → decile 9 +0.532 %) and concluded iso-risk *buys down the return gradient by
construction*. Regime scaling does the same thing one level up: it cuts exposure in exactly the
states where this system's 10-session forward returns were highest.

## Conclusion

**Do not scale position size by the regime label.** Measured negative in direction, not merely
insignificant, under both the raw and bracketed tests, with a bootstrap that never crosses zero.

**Item 64's underlying complaint stands and is now answered rather than open:** the regime label
moves no risk number, and on this system's configuration **it should not**. The label's value is as
*evidence* — it is recorded, it is `measured` rather than defaulted since S213, and the referee and
the operator can read it — not as a multiplier.

## 🪤 Caveats that bound this

1. **Survivorship, and it cuts directly against the finding.** The universe is today's 98 names
   back-projected through 2018 Q4, COVID and 2022. Every panic in this sample was followed by a
   recovery *for names that were still listed in 2026*. Buying into stress looks good partly because
   the sample cannot contain the names it killed. This is the single largest limitation.
2. **Population is grid decisions, not PM-approved buys** — the same caveat ADR-0025's Correction
   named as *"the caveat that most limits this record"*.
3. **The target leg is not modelled.** Stop and 10-session timeout only; a take-profit would truncate
   the right tail, which is where the stressed buckets earn their advantage.
4. **Configuration-bound, like EXP-012.** A 10-session horizon and a 2 × ATR stop clamped 2.5–8 %.
   🪤 **Re-open if any of those change**, particularly a longer horizon.
5. **Multipliers are illustrative.** Two strengths were priced, not optimised. The finding is the
   sign of the gradient, not a tuned number — and the sign is what the decision needs.

## What this changes

- **Work-queue item 64 closes** — measured, not built.
- **ADR-0031 needs a correction**: its premise (a risk budget to attach to) was withdrawn before it
  was written, and the quantity it explicitly left to *neither* owner is now measured as one the
  regime should not own either.
- **ADR-0025's Correction is reinforced**, not contradicted: the same return gradient defeats
  volatility scaling in both the sizing half and the regime half.
- 🚨 **This experiment moves no dial and ships no sizing change.** Confirming it as policy is
  capital-risk and remains the operator's.
