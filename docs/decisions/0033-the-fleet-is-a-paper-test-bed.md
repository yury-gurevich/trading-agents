---
type: Architecture Decision
status: accepted
closes: "What is the project for, now that no trading edge was found: a paper test bed, capital, a pause, or the etalon alone?"
tags: [direction, paper, capital, edge, etalon, dl-317, dl-315, exp-014, exp-022]
---

# ADR-0033 — The fleet is a paper test bed: it trades paper, with no capital

**Status:** Accepted
**Date:** 2026-10-26
**Deciders:** Operator
**Closes:** [DL-317](../design-log.md)'s open question (Amendment 3), work-queue 140

---

## Context

Through October 2026 the project tested whether anything it can build earns more than holding the
index:

- **The fleet's own pipeline.** [EXP-014](../research/experiments/EXP-014-does-the-price-only-pipeline-beat-spy-held-at-the-same-exposure.md)
  (scored early on the operator's word, provisional until the fidelity PASS): over 2017–2026 the
  replayed book earned +166.6 % against +167.1 % for SPY held at its exposure, −0.02 points a year
  [−3.85, +4.16]. [EXP-022](../research/experiments/EXP-022-does-an-exit-besides-the-stop-make-the-book-earn-more.md)
  (same terms): every exit besides the stop earned less, about −11 points a year at 25 bps.
- **Everything else.** EXP-015, EXP-023 and EXP-024 (the ranking's parts, sentiment), EXP-025 to
  EXP-036 (management rules, published strategies, insider purchases, a century of calendar signals,
  stock-level signals, headline events, the FOMC cycle, Bitcoin, idea-selling funds, an LLM reading
  news, filing text): no tradable edge in 130-plus ideas. The one robust finding is defence: a
  200-day trend guard halves the worst drawdowns at a few points of return a year.
- **The live paper book**, 2026-07-08 → 2026-10-23: +2.07 % against SPY's +1.89 % *[measured
  2026-10-24, Alpaca, read-only]*.

DL-317 Amendment 3 put four options to the operator: (a) keep the fleet as a paper research harness,
no capital; (b) run capital, if any, as SPY with the 200-day guard; (c) pause the fleet to stop its
costs; (d) keep the repository as the method's etalon. The operator ruled out (c) on 2026-10-24
(Amendment 4). On 2026-10-26: *"a paper test bed"*.

## Decision

1. **The fleet keeps running on the Alpaca paper account, with no capital.** No live-money path is
   built or wired.
2. **The measure of done is the etalon bar** (the operator, 2026-08-20): the pack trades unattended
   for a sustained stretch, and its evidence catches its own defects without the operator. An edge was
   never part of that bar.
3. **The search for an edge is no longer the goal.** An edge experiment runs when the operator asks
   for one; the open leads (EXP-036's confirmation, the rest of R012's catalogue) stay unbuilt until
   then.
4. **The trading code stays as it is:** the ranking by [DL-315](../design-log.md), the stop-only exit
   by EXP-022. A decision-path change is made for the bar (running unattended, honest evidence), not
   for return.

## Consequences

- The running costs continue (Container Apps, Neon, the debaters' LLM calls). Work that cuts a cost
  without moving a decision is in scope, for example work-queue 141's option A (the forecaster image
  without torch).
- The fidelity count, the final reading of EXP-014 and EXP-022, and DL-315's ADR go ahead as recorded;
  they close the research line.
- The work queue ranks first what stops the fleet running unattended or its evidence catching its own
  defects.
- Capital needs a new ADR. Should the operator reopen it, the evidence points at DL-317 A: SPY with
  the 200-day guard, one check and one order a day.

## Alternatives considered

- **(b) Capital as SPY with the 200-day guard.** Not chosen. It is the one rule with measured
  defence, and it needs almost no system; it reopens only by a new ADR.
- **(c) Pause the fleet.** Ruled out by the operator on 2026-10-24 (DL-317 Amendment 4).
- **(d) The repository as the method's etalon, alone.** Not a rival: the bar is the etalon's, and a
  paper fleet running unattended is how it is proven. Folded into decision 2.
- **Keep searching for an edge as the goal.** Not chosen: 130-plus ideas came back null, and the
  fleet's own pipeline earns what the index earns at its exposure.
