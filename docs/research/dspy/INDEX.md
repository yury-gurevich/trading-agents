# R009 · DSPy — a full study, aimed at the three deliberators

**Status:** 📚 Studied · measured baseline · **Date:** 2026-09-30 · **Version studied:** 3.4.0
(released 2026-09-25), cross-checked against 3.3.1, which `uv.lock` pins

**Why this exists.** The operator judged that the repo was using DSPy without understanding it, and
asked for a deep study of modules, optimisers, adapters and the API reference, with local notes.
The goal it serves: **confirm that all three deliberators understand quant and sentiment evidence
and use it as arguments.**

**Sources.** The DSPy docs source at the `3.3.1` and `3.4.0` tags (`learn/`, `diving-deeper/`,
`api/`), the installed package source, the 3.4.0 release notes, and offline experiments run against
3.4.0 with `DummyLM`. The measurements come from the live graph, read-only.

## Files

| File | Read it for |
| --- | --- |
| [three-roles-goal.md](three-roles-goal.md) | **Start here.** Where each role stands (measured), what DSPy offers for each part of the goal, the offline checks, the proposed sequence and the decisions left open |
| [rounds-and-weights.md](rounds-and-weights.md) | How DSPy carries rounds (`dspy.History`), what its decision types offer for a stated weight, and the score arithmetic the debaters are not shown (GILD worked through) |
| [packet-inventory.md](packet-inventory.md) | Everything computed about a trade, against what the deliberators receive today, and the one law (`FORE-NEV-02`) that blocks part of it |
| [concepts.md](concepts.md) | Signatures, modules, adapters, language models, settings and threads, saving and loading |
| [optimization.md](optimization.md) | Data, metrics, `Evaluate`, every optimiser, GEPA in depth, and what a GEPA run would cost here |
| [api-reference.md](api-reference.md) | The call shapes a three-role program would use, checked against the source |
| [v3.4.md](v3.4.md) | What 3.4 changed, and the measured cost of upgrading (prompt-neutral) |

## Headline findings

1. **The judge is the gap.** Over 229 real debated orders, the judge names a quant metric in 40 % of
   rulings and quotes the sentiment score in 3.5 %, and **38 % of its rulings rest on process facts
   alone**. The defender and challenger name quant metrics in 76–81 % of orders. S246 guides only the
   two debaters, so the role that decides records no readings
   ([three-roles-goal.md](three-roles-goal.md)).
2. **The repo uses one quarter of DSPy.** It uses the adapter's rendered text, frozen. The
   evaluation and optimisation stages (a dataset, a metric, an optimiser run, a saved program) have
   never run ([concepts.md](concepts.md)).
3. **Optimisers rewrite only the instructions.** Field names and descriptions are never changed, so
   anything that must survive optimisation, such as a glossary, cannot live in the docstring
   ([concepts.md](concepts.md)).
4. **Checking a value is not checking its meaning.** Code can prove a reading copied its value from
   the packet. Only a reference for meaning (the glossary) can prove it was understood. Shown
   offline: the check caught `0.84` against `0.838` but cannot catch `pe=30` read as a
   price/earnings ratio ([three-roles-goal.md](three-roles-goal.md)).
5. **GEPA fits, and its cost is controllable.** It is the only optimiser that reads the metric's
   `feedback`, and it refuses a metric without all five arguments. A `light` run over three roles is
   about 1,355 program runs, but tuning the judge alone over recorded debates with
   `max_metric_calls=150` costs about $11–26 ([optimization.md](optimization.md)).
6. **3.4 is prompt-neutral here, and diskcache still comes with it.** It renders and parses S246's
   turn byte-for-byte like 3.3.1 (measured), but `diskcache` is still a base dependency, so DSPy
   stays out of production images ([v3.4.md](v3.4.md)).

**Consuming decisions:** [DL-250](../../design-log.md) (the direction and amendment 2),
[DL-252](../../design-log.md) (S246's DSPy-free runtime), work-queue **97**
([work-queue](../../work-queue.md)), [ADR-0010](../../decisions/0010-llm-interaction-quality-gate.md)
(the frozen-set gate on prompt changes).

🔁 **Reversed 2026-10-07.** Finding 6's conclusion (*DSPy stays out of production images*) and the
DSPy-free runtime these notes describe no longer hold: [ADR-0032](../../decisions/0032-dspy-runs-the-llm-roles-at-run-time.md)
puts DSPy in the deliberator's process, with `diskcache` and LiteLLM left out of the image
([DL-266](../../design-log.md), S254). The notes on signatures, modules, adapters and optimisers stand.

**Earlier related research:** [R003 · TextGrad](../textgrad/INDEX.md) compared TextGrad with DSPy
and kept it as the ADR-0010 bake-off candidate.
