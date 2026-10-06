# R010 · A debate-pipeline prototype — what to take, and what not

**Status:** 📚 Studied · **Date:** 2026-10-06 · nothing adopted

**What it is.** A prototype the operator supplied on 2026-10-06, while the work on the three
deliberators was under way ([DL-264](../../design-log.md)). A Proponent writes a trading plan from up
to 60 parameters, an Opponent critiques it, and a Judge computes risk figures, rules and issues
directives. A loop feeds the directives back to the Proponent for up to four rounds.

## Files

| File | Read it for |
| --- | --- |
| [debate-pipeline-prototype.md](debate-pipeline-prototype.md) | The document as received, with its formatting repaired and its content unchanged |

## The planner's reading (not decided)

| In the prototype | Here today | Reading |
| --- | --- | --- |
| The judge returns **directives**, and the next round must answer them | `revise` is 34 of 34 rulings since 2026-09-17, and nothing reads one (DL-264; ADR-0029's register is not built) | **Take the idea.** A ruling needs a reader. Here it cannot be a model that rewrites the order (two rows down). It is ADR-0029's register for a point about the system, and the other debater's next turn for a point about this order |
| Each role answers in **typed JSON**, with a severity or a confidence | S246's typed readings; EXP-019's typed answers | Already the direction |
| The judge **computes** VaR, expected shortfall, drawdown and leverage | 18 of 19 guided turns name missing risk evidence as a gap ([R009](../dspy/three-roles-goal.md)); the packet carries no figure of that kind | **Take the figures, not the method.** A model's arithmetic is not a fact. Computed in code and defined, they are evidence for the packet (work-queue 98) |
| The **Proponent writes the trading plan** | The pipeline decides in code and the debate may only stop a buy (ADR-0022, ADR-0017: the model can subtract, never add) | **Not for us** |
| The loop runs **until the judge accepts**, up to four rounds, with the judge inside it | Two rounds, then one ruling; no role both argues and judges (the deliberation charter) | **Not as drawn.** A judge that directs and then rules on the result is ruling on its own work, and each extra round is three more calls (five calls cost $0.66 an order on 2026-10-06) |
| About 60 generic parameters: leverage, an option overlay, TWAP, tick data | A long-only daily book with no leverage and no options | Not our system. It is the gap DL-250 measured: general finance, not what this code computes |

## Outcome

The first and third rows are carried into [DL-264](../../design-log.md) (amendment 4) as inputs to its
two goals. Nothing is built.

**Consuming decisions:** DL-264 ·
[ADR-0029](../../decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md) · work-queue 98 and 107.
