# R010 · A debate-pipeline prototype — the target shape, adapted to this system

**Status:** 📚 Studied · **Date:** 2026-10-06 · **2026-10-07:** to be adapted, not copied (operator);
nothing built yet

**What it is.** A prototype the operator supplied on 2026-10-06, while the work on the three
deliberators was under way ([DL-264](../../design-log.md)). A Proponent writes a trading plan from up
to 60 parameters, an Opponent critiques it, and a Judge computes risk figures, rules and issues
directives. A loop feeds the directives back to the Proponent for up to four rounds.

**How to read it.** The operator, 2026-10-07: *"it does not have to be implemented VERBATUM. It can
bee adpted to our needs."* The planner's first reading (2026-10-06) sorted its parts into "take" and
"not for us". That was the wrong question. The prototype is the shape the debate should have; the
table below says what each part becomes in a system that decides in code and lets a model only stop a
buy.

## Files

| File | Read it for |
| --- | --- |
| [debate-pipeline-prototype.md](debate-pipeline-prototype.md) | The document as received, with its formatting repaired and its content unchanged |

## Each part, adapted

| In the prototype | Here today | Adapted to this system |
| --- | --- | --- |
| **Parameters**: one JSON of about 60 strategy fields | A packet of about 9,500 characters built in code from the run's own lineage; several computed facts are withheld ([packet-inventory](../dspy/packet-inventory.md)) | The packet stays ours and is completed: the withheld facts (work-queue 98), the score arithmetic (work-queue 107), and a definition for every key (work-queue 97 c). Its generic fields (leverage, options, TWAP) describe another system and are not copied |
| **Proponent** writes the plan: `summary`, `trades`, `rationale`, `risk_estimates` | The pipeline writes the order in code; the defender argues for it in typed readings, gaps and an argument (S246) | The plan is the order the pipeline produced. The defender's typed turn states the readings its case rests on, what the order hinges on, and from round 2 an answer to each point put to it |
| **Opponent**: `critique`, `suggested_changes`, `severity_score` | The challenger's typed readings, gaps and argument; no severity, and no line between this order and the system | Each of the challenger's points carries the reading it rests on, a typed severity, and whether it is about this order or about every order. A suggested change is one the system can make to one order |
| **Judge**: `verdict`, `risk_metrics`, `directives`, `confidence` | One line of rationale; `revise` in 34 of 34 rulings since 2026-09-17, and nothing reads one (DL-264) | A typed ruling: each contested point, who prevailed and on which reading; the verdict; directives; a probability for each of the three rulings. It implements [ADR-0029](../../decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md) decisions 2 and 3 |
| The judge **computes** VaR, expected shortfall, drawdown and leverage | The packet carries no figure of that kind; 18 of 19 guided turns name the missing risk evidence as a gap ([R009](../dspy/three-roles-goal.md)) | The same figures, computed in code for the order and for the book with and without it, defined, and shown to all three roles. A model's arithmetic is not a fact; code's is |
| **The loop**: the judge's directives go back, up to four rounds, until it accepts | Two fixed rounds, then one ruling; the challenger always speaks last | After round 1 the judge states the points still open. Round 2 must answer each one: concede it, rebut it with a reading, or name it as a matter for the system. The judge then rules. A debate with no open point ends after round 1. `max_rounds` stays the bound |
| The loop **revises the plan** | A ruling can stop a buy and can change nothing else (ADR-0029; the model may subtract, never add) | **Not carried over, on purpose.** The loop improves the debate and the ruling, not the order. A directive about the system goes to ADR-0029's register with its standing answer. Letting a ruling shrink an order is a capital-risk decision that only the operator can reopen |
| **Final verdict**: `supporting_arguments`, `mitigations`, `judge_confidence` | `DeliberationRun` keeps the transcript, the ruling and one line | The record keeps the ruling point by point, with the readings it rests on and the directives it issued |
| `debate_cycle(params)`: three functions and a loop | Three containers; the manager's `_debate` is the loop | Three DSPy predictors ([ADR-0032](../../decisions/0032-dspy-runs-the-llm-roles-at-run-time.md)). In production each runs in its own container and `_debate` is the loop. Offline they compose into one `dspy.Module` whose `forward()` is the same loop, for evaluation and optimisation |

## Outcome

The order of work is in [DL-264](../../design-log.md), amendment 5. The first step,
[S254](../../sprints/sprint-254-each-debater-turn-is-run-by-dspy-and-the-prompt-does-not-change.md),
puts DSPy in the deliberator's process and changes no prompt. Nothing else is built.

**Consuming decisions:** DL-264 · [DL-266](../../design-log.md) ·
[ADR-0029](../../decisions/0029-a-revise-is-a-finding-an-overturn-is-a-block.md) ·
[ADR-0032](../../decisions/0032-dspy-runs-the-llm-roles-at-run-time.md) · work-queue 97, 98, 107 and 110.
