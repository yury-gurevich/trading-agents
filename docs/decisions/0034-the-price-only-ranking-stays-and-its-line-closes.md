---
type: Architecture Decision
status: accepted
closes: "Does the price-only ranking change, now that EXP-014 found no edge: re-weight it, replace it, reverse it, or keep it and stop researching it?"
tags: [edge, ranking, analyst, scanner, dl-315, dl-316, exp-014, exp-015, exp-023, exp-024]
---

# ADR-0034 — The price-only ranking stays in the code, and its research line closes

**Status:** Accepted
**Date:** 2026-10-27
**Deciders:** Operator (DL-315, decided 2026-10-23 before EXP-014 was scored)
**Closes:** [DL-315](../design-log.md) D2, work-queue 82

---

## Context

[DL-315](../design-log.md) fixed, on 2026-10-23, what follows if
[EXP-014](../research/experiments/EXP-014-does-the-price-only-pipeline-beat-spy-held-at-the-same-exposure.md)
finds no edge: the ranking code stays, and its research line closes in an ADR written with the
verdict. The rule was set while every EXP-014 arm was sealed and unread, so it cannot lean on what
the arms show.

**EXP-014's verdict, final 2026-10-27.** Scored 2026-10-26 on the operator's word (Amendment 2); final
once the fidelity count read PASS on 2026-10-27 through `sched-2026-10-26`, replayed from `v0.128.06`
(5 of 5 clean sessions, scanner 125 / 125, analyst 193 / 193, PM 16 / 16 judged recommendations against
a floor of 10, 0 unexplained).

- **H0, indistinguishable.** Over 2017-01-03 → 2026-09-25 (2,445 session pairs), `base-25` earned
  +166.60 % against +167.13 % for SPY held at the same exposure: A = −0.02 pts a year, 95 % interval
  [−3.85, +4.16]. SPY held whole earned +297.07 %.
- **H2 fails for both ablations.** `technical-only-25`: A = +1.80 [−2.75, +7.08], paired difference
  from `base-25` +1.83 [+0.00, +4.05], neither lower bound above 0, the lead coming from 2025 and the
  partial 2026. `relative-strength-only-25`: A = −1.27 [−3.14, +0.62].
- **H1 does not hold**, so DL-315 D4's H1 branch (read the edge as sizing, stops or exposure) does
  not apply.

**What came before it.** [EXP-015](../research/experiments/EXP-015-price-only-ensemble-vs-technical-score.md):
the technical score's mean rank IC at 10 sessions is −0.0099 [−0.0175, +0.0119] over 2018–2024, and a
LightGBM ensemble failed walk-forward. [EXP-023](../research/experiments/EXP-023-which-of-the-technical-scores-rules-carry-its-rank-ic.md):
none of the score's 16 components carries after Holm; the scanner's selection beats the members it
turns away by +0.06 % [−0.13 %, +0.31 %]. [EXP-024](../research/experiments/EXP-024-does-news-sentiment-rank-the-scanners-survivors.md):
neither the lexicon nor FinBERT ranks the survivors at 10 sessions.

## Decision

1. **The ranking code stays as it is.** `agents/analyst/` and `agents/scanner/` do not change because
   of this result: no re-weighted technical score, no ensemble, no switch to one pillar (H2 failed).
2. **The research line closes.** No further experiment on the price-only ranking is planned. This
   includes the reversal-score shape that EXP-023 section 7 left open.
3. **The sentiment pillar keeps its weight of 0.20** ([DL-316](../design-log.md), the operator,
   2026-10-24). Sentiment is no longer an edge line; its shadow readings stay.
4. **Edge work happens elsewhere**, as [ADR-0033](0033-the-fleet-is-a-paper-test-bed.md) records:
   pre-registered experiments beside the paper test bed, the open lead being EXP-036's confirmation.
   Fundamentals in the live composite are measured forward through the claims ledger (DL-315 D3).

## Consequences

- The trading pack has no demonstrated stock-picking skill. The fleet ranks names the way it did, as a
  paper test bed ([ADR-0033](0033-the-fleet-is-a-paper-test-bed.md)), not as a source of excess return.
- Nothing is built, merged or deployed for this ADR, and no decision path moves, so the fidelity count
  is untouched.
- The `technical-only` hint (+1.83 [+0.00, +4.05] over `base-25`, led by 2025–2026) is recorded and
  not acted on. It failed H2's pre-registered bar, and every cached session has now been read.
- **What reopens the line:** only a new pre-registered experiment, on sessions the line has not read
  (after 2026-09-25), that shows the ranking earns more than SPY at its exposure.
- The etalon bar is unaffected. This finding is the evidence discipline working as intended.

## Alternatives considered

- **A reversal score on sessions after 2026-09-25.** Ruled out (DL-315): the lean had faded on 2025 →.
  Confirming +0.01 IC would take years *[estimate, scaled from seven years' interval]*. At that size
  it would be worth about 0.1 % a pick per 10 sessions, against 0.5 % a round trip at 25 bps a side
  *[estimate, not measured]*.
- **EXP-015's LightGBM ensemble.** Ruled out: it failed walk-forward bars 1 and 2, and its holdout has
  been read once and is spent.
- **Switching to the technical score alone.** Ruled out: H2 failed, and the paired lead's lower bound
  sits at 0, carried by 2025 and 2026.
- **Re-weighting the rules.** Ruled out by EXP-023 section 7: every cached session has been read.
- **Removing the ranking, or picking at random.** Ruled out: nothing gained. `agents/analyst/` is a
  decision path, so the change would restart the fidelity count for no measured benefit.
