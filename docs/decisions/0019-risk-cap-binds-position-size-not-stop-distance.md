---
type: Architecture Decision
status: accepted
closes: "When a volatility-scaled stop wants more room than the per-position risk cap allows, which gives — the cap or the stop? And how does a high-ATR name get a correct stop without breaching the cap?"
tags: [portfolio-manager, analyst, risk, sizing, stops, volatility, atr, adr-0013, adr-0015, dl-77, dl-78]
---

# ADR 0019 — The risk cap binds position size, never stop distance

**Status:** Accepted · **Date:** 2026-08-01 · **Decider:** planning agent under delegated authority
(operator: *"do what is appropriate to the spirit and letter of this project"*, 2026-08-01)

## Context

S150 shipped the volatility-scaled stop challenger (ADR-0013, off by default). Measuring what the
shipped config actually delivers surfaced a wall that is not the formula's ([DL-78](../design-log.md)):

| Name | Flat 5 % stop | 2×ATR wants | Delivered | Binding constraint |
| --- | --- | --- | --- | --- |
| BAC / USB / SCHW | 5 % | ~2.00× ATR | unchanged | neither — already sane |
| CSCO | 6.1 % | — | 1.5 % touched | formula |
| HPE | 19.7 % | — | 6.1 % | formula |
| AMD | 36.4 % | — | 10.6 % | formula |
| **MRVL** | 39.4 % | **17.1 %** | **18.2 % → 0.94 ATRs** | **the 8 % risk cap** |

MRVL only halves. 2×ATR wants a 17.1 % stop; the 8 % per-position risk cap clamps it, leaving the
stop at **0.94 ATRs** — inside one day's normal range, which is the exact defect S150 set out to fix
([DL-77](../design-log.md)). The scaling did not underperform. It hit a wall that is not its to move.

Two ways past it were identified and neither shipped in S150.

## Decision

**The 8 % per-position risk cap is a capital-safety bound and does not move to accommodate a stop
formula. The stop distance is set by volatility; the *position size* is what shrinks to keep the
resulting dollar risk inside the cap.**

Concretely: given a decided stop distance `stop_pct`, the PM sizes the position so that
`position_value × stop_pct ≤ per_position_risk_budget`, rather than sizing first on a fixed share
count and then discovering the stop cannot fit.

## Why this and not raising the cap

Raising the cap is the change that makes the challenger's numbers look better, which is precisely
why it is the wrong instrument. Three reasons, in the project's own terms:

1. **A safety cap is not a tuning knob.** The repo already draws this line: bounded parameters move
   by experiment under the tuner, but *safety and capital caps are ADR-only, never experiments*.
   Moving a max-risk-per-position bound because a challenger wants more room is the definition of
   fitting the guardrail to the strategy.
2. **The cap is not what is broken.** The mismatch is between a **fixed** share count and a
   **variable** stop distance. Raising the cap treats the symptom on one name and leaves the
   structural mismatch for the next high-ATR ticker.
3. **It fails safe in the right direction.** Under this decision a violently volatile name gets a
   *smaller* position with a *correct* stop. Under the raise-the-cap alternative it keeps a large
   position and takes on more absolute risk — the worse outcome of the two, arrived at by relaxing a
   bound rather than by deciding anything.

## The road not taken (LAW-06)

- **Raise the 8 % cap** — rejected above. If it is ever revisited it must be as a PRD/ADR decision
  about maximum risk per position, argued on capital-preservation grounds, **never** as a
  consequence of a challenger hitting it.
- **Let the stop breach the cap for high-ATR names** — rejected outright. That inverts the
  precedence: the cap exists so that a single position cannot exceed a known loss, and a stop wide
  enough to break it makes the cap decorative.
- **Leave MRVL-class names clamped and accept the 0.94-ATR stop** — rejected. This is the status quo
  and it is measurably the defect DL-77 opened: a stop inside one day's range is touched by noise,
  which converts volatility into realized losses.
- **Exclude high-ATR names from the universe** — rejected as scope-mismatched. The scanner's job is
  candidate selection on its own criteria; smuggling a risk-sizing constraint into it would put a
  capital rule in the wrong agent and hide it from the PM's laws.

## Consequences

- **PM sizing changes**, so this is a behaviour change requiring its own sprint, its own tests, and a
  `PM` law amendment declaring the sizing rule and its parameter. It is **not** a config flip.
- **The S150 stop challenger cannot be fairly evaluated until this lands.** Any promotion report
  written before it is comparing the scaled stop against a cap that clamps it, not against the flat
  champion. Recorded here so a future reading of that report knows what it is looking at.
- **ADR-0013's champion–challenger discipline still applies** to the sizing change itself: it ships
  off by default with the counterfactual recorded, like S149 and S150 before it.
- **DL-78 is closed by this ADR.** Its "successor undecided" state is resolved.

## Status of implementation

Decided, **not built**. No sprint is packaged yet. The dependency order is: this ADR → a PM sizing
sprint (with the law amendment) → only then a meaningful S150 promotion decision.
