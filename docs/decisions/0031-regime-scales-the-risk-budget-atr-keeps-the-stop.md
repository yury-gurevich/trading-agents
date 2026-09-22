---
type: Architecture Decision
status: accepted
closes: "ADR-0025 Decision B ruled that volatility should scale position risk and that a regime label moving no risk number is not a regime input, but explicitly authorised no implementation because the stop/target bracket is already ATR-scaled and two volatility adjustments could compound invisibly. Which risk number does the regime own, and which does ATR keep?"
tags: [portfolio-manager, provider, regime, sizing, volatility, risk, control-design, adr-0025, adr-0028, exp-009, dl-169]
amends: ADR-0025
---

# ADR 0031 — The regime scales the risk budget; ATR keeps the stop

**Status:** Accepted · **Date:** 2026-09-20 · **Decider:** planning agent, under operator delegation
(*"decisions only: make the best decision that serves the project best"*, 2026-09-20)

## Context

[ADR-0025](0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md) Decision B
accepted the **direction** — *yes, volatility should scale position risk, and a computed regime label
that moves no risk number is not a regime input* — and then stopped, for a stated reason:

> 🚨 **Explicitly NOT accepted as an implementation.** [...] this changes **every position size on
> every run**, and the stop/target bracket is already ATR-scaled (`applied_mode=scaled`), so there is
> interaction risk between two volatility adjustments.

That interaction risk was never resolved, so item **64** sat on a ruled direction with no shape. Two
things have changed since, which together make the shape decidable:

1. **The label now has a real input.** [ADR-0028](0028-the-regime-reads-vix-from-fmp-and-says-when-it-cannot.md)
   made FMP `^VIX` the source; S213 shipped it and it **deployed 2026-09-20 as `s219a`**. Probed live
   the same day through the production path: `vix=14.81`, `vix_status='measured'`, and
   `classify_regime` returns **`risk_on`** — not the `neutral` that all 50 prior scheduled rows carry
   ([EXP-009](../research/experiments/EXP-009-volatility-sizing-replay.md) had correctly reframed item
   64 as moot until this existed).
2. **The two quantities were read, not assumed.** `size_quantity`
   (`agents/portfolio_manager/domain/sizing.py:25`) is
   `(portfolio_value * max_position_pct) // est_price` — a **pure notional fraction with no stop
   distance in it**. The stop/target bracket is separately ATR-scaled via `decision_atr_pct`.

🎯 So the feared "two volatility adjustments" are not yet two. Today volatility touches **one**
quantity (the bracket) and sizing touches **none**. That is what makes it safe to assign owners now,
before anything is built.

## Decision

**Each volatility measure owns exactly one quantity.**

| Quantity | Owner | Why it belongs there |
| --- | --- | --- |
| **Stop distance** (how far away the loss point is) | **ATR** (unchanged) | Idiosyncratic: how much *this instrument* moves. Already `applied_mode=scaled`. |
| **Risk budget** (how much capital is at risk per position) | **Regime** (new) | Market-wide: how dangerous *the market* is. One number, one owner. |
| **Notional ceiling** (`max_position_pct`) | **Neither** — stays a flat cap | A backstop against risk-based sizing producing an enormous position behind a very tight stop. |

🪰 **Read the deployed value, not the code default, before reasoning about the ceiling.** `max_position_pct` defaults to `0.10` in `agents/portfolio_manager/settings.py:32` but the fleet runs **`0.01`** — `orchestration/packs/trading_tunables.json` injects `PORTFOLIO_MANAGER_MAX_POSITION_PCT=0.01` with `MAX_POSITIONS=60`, both confirmed live on the `portfolio-manager` app on 2026-09-20. So the real book shape is **up to 60 names at 1 % each**, not 10 at 10 %. A risk-budget multiplier is therefore a *small* adjustment to an already-small slice, which is the regime that makes this safe to measure at all.

Concretely: the regime multiplies the **risk-budget percentage** and nothing else. It does **not**
widen stops, move the confidence floor, or shorten the holding window.

The two measures then **compose instead of compounding**: one says how far away the exit is, the other
says how much you are willing to lose getting there. Applying both to the *same* quantity is the
invisible double-count ADR-0025 refused to risk; applying each to its own quantity is ordinary
position-risk arithmetic.

## Rejected

- **Let the regime widen stops.** Rejected: that is ATR's quantity. Two owners on one number is
  exactly the compounding ADR-0025 named, and it would be undetectable in the artefacts — the stop
  would simply be wider with no attribution for which input widened it.
- **Let the regime move `min_confidence`.** Rejected: it conflates a *volatility* signal with a
  *conviction* signal. A stressed market does not make the analyst's read less accurate; it makes the
  consequence of being wrong larger, which is a sizing statement.
- **Let the regime shorten `max_holding_days`.** Rejected for now: plausible, wholly unmeasured, and
  it changes exit behaviour rather than risk taken. It can be proposed later on its own evidence.
- **Scale several numbers at once.** Rejected: with one knob a champion–challenger can attribute the
  result. With four, it cannot, and the first live regime data is days old.
- **Name the multipliers in this ADR.** Rejected deliberately. *Which* quantity the regime owns is a
  design question and belongs here; *how much* it moves is a measurement and belongs to an experiment.
  🪤 Writing a multiplier table here would be the unmeasured-claim-in-a-confident-voice pattern this
  repo keeps paying for.

## Consequences

- 🚨 **This ADR ships no code, and no sizing change is authorised by it** — that restriction is
  inherited from ADR-0025 Decision B and is *not* lifted here. Work-queue item **64** narrows from
  *"should the regime change a risk number"* to *"measure the multiplier for the risk budget"*.
- **The blocking evidence is now obtainable for the first time.** The gate is a champion–challenger on
  one `as_of` under a **non-neutral** regime, which `sched-2026-09-21` is expected to produce. Until a
  run records a non-`neutral` label with `vix_status='measured'`, there is still nothing to measure
  against, and item **70** remains the dependency.
- Making sizing risk-based (dividing by the stop distance) is item **62**'s half, closed in direction
  by ADR-0025. This ADR does not re-open it; it fixes where the regime attaches **when** that lands,
  so the two arrive compatible rather than colliding.
- `max_position_pct` survives as a ceiling rather than the primary driver. 🪤 Without it, risk-based
  sizing behind a very tight stop can demand a position far larger than the book should hold in one
  name — the failure mode that makes naive risk sizing dangerous.
- The PM law book owes a clause cycle in the implementing sprint: the agent's sizing guarantee changes
  from a notional fraction to a risk fraction under a named ceiling.

## Correction — 2026-09-22, on EXP-013: the quantity this ADR assigned does not exist

**What this ADR rested on.** It assigned the regime the **risk budget** — *"how much capital is at
risk per position"* — and said `max_position_pct` stays a flat ceiling owned by neither measure,
because the ceiling is *"a backstop against risk-based sizing producing an enormous position behind a
very tight stop"*. Both statements presume risk-based sizing is coming. The Consequences section said
so directly: the regime attaches to it **"when that lands"**.

🪰 **It cannot land, and it had already been declined two days before this ADR was written.**
[ADR-0025's Correction](0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md)
(2026-09-18) withdrew Decision B on [EXP-012](../research/experiments/EXP-012-volatility-sizing-ten-year-replay.md):
iso-risk sizing lost **$11,619** over 47,549 decisions with 100 % of bootstrap resamples negative, and
fixed 1 % notional sizing stands as champion. **This ADR cites EXP-012 zero times.** That is the
failure — not the reasoning, which is sound given its premise, but that the premise had been removed
and the ADR did not read the record before assigning an owner.

**So the live question was the one this ADR left to neither owner**, and it has now been measured
([EXP-013](../research/experiments/EXP-013-regime-scaled-sizing-replay.md), 47,533 decisions,
2017-2026, $0): **should the regime scale the notional cap?**

| Arm (deployed stop bracket) | Total, pct-points | Delta |
| --- | --- | --- |
| champion (flat 1.0) | 29,926 | — |
| mild (1.1/1.0/0.9/0.8/0.6) | 28,108 | −1,818 |
| strong (1.2/1.0/0.8/0.6/0.4) | 26,769 | **−3,157** |

Bootstrap on the strong arm: **95 % CI [−3,699, −2,574], 100 % negative.** The mechanism is the one
EXP-012 named: forward 10-session return **rises** with regime stress (`neutral` 0.287 % →
`extreme_volatility` 1.880 %) and so does return per unit of dispersion (0.057 → 0.217), so cutting
size when stressed buys *down* the return gradient.

**Therefore (planning agent, under delegated technical decisions; the policy call remains the
operator's):**

1. **The decision table's middle row is void.** There is no risk budget for the regime to own, and
   none is authorised. The ATR row and the flat-ceiling row stand.
2. **The regime should not scale the notional cap either** — measured negative in direction, not
   merely insignificant.
3. **The regime label stays as evidence, not as a multiplier.** It is recorded, `measured` rather
   than defaulted since S213, and readable by the referee and the operator. Item **64**'s complaint
   — *a label that moves no risk number* — is answered: on this configuration it should not move one.
4. **The ceiling's justification is restated.** `max_position_pct` is not a backstop against
   risk-based sizing that is never coming; it is the **primary** sizing control, and the only one.
5. **Scope, as with ADR-0025's Correction.** This is measured for a 10-session horizon and a 2 × ATR
   stop clamped 2.5–8 %, on a survivorship-biased universe. 🪤 **Re-open if any of those change.**

**Road not taken:** *retract this ADR outright.* Rejected — its ATR/ceiling assignment is still the
right shape and would have to be re-derived, and the record of how a premise went stale between two
ADRs written two days apart is worth keeping visible. A retraction would hide it.
