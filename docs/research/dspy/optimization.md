# DSPy evaluation and optimisers

**Part of:** [R009 · DSPy](INDEX.md) · **Version studied:** 3.4.0, cross-checked against 3.3.1 ·
**Sources:** the docs source (`learn/evaluation/`, `learn/optimization/`,
`diving-deeper/choosing-an-optimizer.md`, `diving-deeper/gepa-in-depth.md`,
`diving-deeper/metrics-and-evaluation.md`) and `dspy/teleprompt/gepa/gepa.py`.

Stages 2 and 3 of DSPy: measuring a program, then tuning it. Stage 1 is in
[concepts.md](concepts.md).

---

## Data: `Example`

- `dspy.Example(question=..., answer=...)` is a dict with dot access. `.with_inputs("question")`
  marks which keys are inputs; every other key is a label or metadata.
- `.inputs()` and `.labels()` split an example. A module's output is a `dspy.Prediction`, a subclass
  of `Example`.
- **How much data.** The docs say 20 inputs already help and 200 go a long way for evaluation; for
  optimisation, 30 examples give value and 300 or more is the aim.
- **How to split.** Most prompt optimisers overfit a small training set, so the docs recommend an
  unusual split: **20 % train, 80 % validation**. GEPA is the exception: maximise the training set
  and keep the validation set just big enough to represent the task.
- **Labels are optional.** Many metrics need only the inputs and the program's own output. Our
  deterministic evidence checks are of that kind: the packet is the ground truth, and no human label
  is needed.

---

## Metrics

A metric is any callable. Its full signature, as optimisers call it:

```python
def metric(gold, pred, trace=None, pred_name=None, pred_trace=None): ...
```

- `gold` is the `Example`, and `pred` is the program's `Prediction`.
- `trace` is a list of `(predictor, inputs, outputs)` covering every step of the run. It is filled
  in **only during compilation**, which lets a metric grade intermediate steps (for example each
  role's readings) and not only the final answer.
- `pred_name` and `pred_trace` narrow that view to one predictor. GEPA uses them to score one step of
  a multi-step program.
- 🪤 **GEPA refuses a metric that cannot accept all five positional arguments.** It runs
  `inspect.signature(metric).bind(None, None, None, None, None)` in its constructor. Declare all five
  even if you ignore three of them.

**Three return shapes, handled differently:**

| Return | `Evaluate` reads | Optimisers read |
| --- | --- | --- |
| `bool` | percentage of `True` | pass/fail |
| `float` | mean | the score |
| `dspy.Prediction(score=..., feedback=...)` | mean of `score` | score; **GEPA also reads `feedback`** |

**The `trace` switch.** A common pattern returns a continuous score when `trace is None` (plain
evaluation) and a strict pass/fail when `trace is not None` (bootstrapping, where only clearly good
traces should become demos).

**LLM judges are modules.** `dspy.evaluate.SemanticF1` and `CompleteAndGrounded` subclass
`dspy.Module`, so a judge can itself be inspected, traced and optimised. The docs suggest that if
your metric is a DSPy program, you optimise the metric too. That is useful later, but a
deterministic metric comes first here: it costs nothing and cannot drift.

**`dspy.Evaluate`** runs a program over a dev set in parallel:
`Evaluate(devset=..., metric=..., num_threads=..., display_table=..., failure_score=0.0,
save_as_json=...)`, and calling it returns an `EvaluationResult` with `.score` and `.results`. A
failing metric scores `failure_score` rather than stopping the run. 3.4 raises `ValueError` on an
empty dev set.

---

## What optimisers tune

Every optimiser turns one or more of three knobs:

1. **Instructions:** the docstring of each predictor's signature. This is the only text
   instruction optimisers change. Field names and descriptions are never touched
   ([concepts.md](concepts.md)).
2. **Demos:** the worked examples attached to a predictor.
3. **Weights:** fine-tuning. This needs a model with a fine-tuning API, so it is **not available for
   Claude**. `BootstrapFinetune` and `BetterTogether`'s weight step are out of scope here.

`.compile(student, trainset=..., valset=...)` always returns a new copy. The student you pass in is
never changed.

| Optimiser | Tunes | Needs | Cost shape | Use when |
| --- | --- | --- | --- | --- |
| `LabeledFewShot(k)` | demos | labelled examples | no LM calls | honest baseline |
| `BootstrapFewShot` | demos | metric + a few inputs | one run per training example | first try; needs a reliable metric |
| `BootstrapFewShotWithRandomSearch` (`BootstrapRS`) | demos | metric + valset | × `num_candidate_programs` | demos vary in quality |
| `KNNFewShot` | demos chosen per call | an embedder | embedding only | inputs need different demos |
| `COPRO` | instructions | metric | ≈ breadth × depth × predictors | wording is wrong, demos fine |
| `MIPROv2` | instructions **and** demos | metric; `auto` budget | Bayesian search; hundreds of calls | both weak, budget available |
| `SIMBA` | instructions (rules) and demos | metric | minibatch steps targeting the worst cases | failures share a pattern |
| `InferRules` | appends readable rules | metric | bootstrap + rule extraction | you want the rules stated |
| **`GEPA`** | instructions (and `Flex` code) | **metric with feedback** | reflection plus evaluation; see below | a feedback-rich metric exists; **our case** |
| `Ensemble` | combines compiled programs | several programs | × programs at inference | several good candidates |
| `ReAnchor` (3.4, experimental) | decision thresholds only | metric + labelled sets | no instruction rewriting | calibrating `bool` / `Literal` / `Choice` decisions |

Two notes from the selection guide that apply to us:

- **Demo tuning tends to overfit; instruction tuning tends to generalise.** A debate over ~9,000-char
  packets makes demos expensive in tokens, and a small trainset would overfit them.
- **GEPA is the only optimiser that reads `feedback`.** COPRO and MIPROv2 see only which of two
  candidates scored higher. Our answer key can say *why* a reading was wrong (*"`pe=30` is a 0–100
  sub-score; the P/E is `peTTM`"*), and only GEPA can use that sentence.

---

## GEPA in depth

**Loop.** GEPA keeps a population of candidate programs. It runs them on a minibatch and reads the
metric's `feedback` for the failures. A `reflection_lm` then proposes a new instruction for **one
predictor per iteration** (round-robin by default). Candidates are kept on a per-example **Pareto
frontier**: any program that is best on at least one example survives. The final winner is the
program with the highest *aggregate* validation score.

**Constructor (3.4, read in source):**

```python
dspy.GEPA(metric, *,
          auto=None | "light" | "medium" | "heavy",   # exactly ONE of these three budget knobs
          max_full_evals=None, max_metric_calls=None,
          reflection_lm=None,              # defaults to the configured LM; usually pass a strong one
          reflection_minibatch_size=3,
          candidate_selection_strategy="pareto",   # or "current_best" (greedy)
          skip_perfect_score=True, perfect_score=1.0, failure_score=0.0,
          component_selector="round_robin",        # or "all", or a custom selector
          use_merge=True, max_merge_invocations=5,
          instruction_proposer=None, code_proposer=None,   # code_proposer is new in 3.4 (Flex)
          num_threads=None, log_dir=None, track_stats=False, seed=0, ...)
```

**Details that change how we would run it:**

- **Two models, two budgets.** `reflection_lm` is called rarely and benefits from a strong model.
  The program's own model is called on every evaluation. Production uses `claude-opus-5` for every
  role, and the prompt must be tuned *for that model*, so we cannot evaluate on a cheaper one.
- **Examples that already score `perfect_score` leave the reflection batch.** Reflection sees only
  failures.
- **`track_stats=True`** keeps every candidate, its lineage and its per-example scores in
  `detailed_results`. `log_dir` writes each iteration's proposed instructions to disk.
- **3.4 fixed a 3.3.1 bug** in which failed examples could shift or drop out of GEPA's trace-capture
  scores.

### What a GEPA run would cost here

`auto` is converted into metric calls by `auto_budget()` in `gepa.py`. Recomputed with that exact
formula (`minibatch_size=35`, a full evaluation every 5 steps):

| `auto` | 1 predictor, valset 30 | 3 predictors, valset 30 | 3 predictors, valset 100 |
| --- | --- | --- | --- |
| light | **500** | 1,355 | 1,915 |
| medium | 840 | 1,865 | 2,565 |
| heavy | 1,245 | 2,200 | 3,040 |

**Price per metric call.** One call runs the *whole program*. Two measured per-call costs for
`claude-opus-5`:

- **≈ $0.07** per call at `effort=high`, the old free-text format, `max_tokens` 4,096 (S245 live
  check: 20 calls, $1.45).
- **≈ $0.17** per call at `effort=max`, the S246 guided format and ~9,000-char packets (the
  2026-09-30 replay: 19 calls, $3.25).

| Setup | light, 1 predictor, valset 30 | light, 3 predictors, valset 30 |
| --- | --- | --- |
| **Judge only, over recorded debates** (1 call per metric call) | ≈ $36–85 | — |
| Full debate re-run (≥ 3 calls per metric call) | ≈ $109–255 | ≈ $295–690 |

Reflection-model calls come on top.

**Three levers bring this within a tight budget:**

1. **Optimise one role at a time over recorded inputs.** The replay corpus
   (`orchestration/replay_corpus.py`) rebuilds each recorded order's packet, and the graph holds each
   debate's transcript. The judge can be tuned as a *one-predictor program* whose inputs are recorded
   `(decision, context, transcript)`, so each metric call is one judge call and the other roles never
   re-run.
2. **Set `max_metric_calls` directly**, not `auto`, so the dollar ceiling is a number stated before
   the run. For example, 150 metric calls × $0.07–0.17 ≈ $11–26.
3. **Keep DSPy's response cache on.** Re-running the same candidate on the same example costs nothing.

---

## Handing a result to a DSPy-free runtime

An optimiser run ends in `program.save("x.json")`. That file holds each predictor's new instructions
(and demos, if any), and it can be diffed and reviewed like any other change. The runtime stays
DSPy-free by the S246 pattern:

1. Read the new instructions from the saved file.
2. Render them with DSPy offline into the golden fixture
   (`scripts/render_guided_turn_golden.py` generalised to every role).
3. Update the kernel literals. CI proves them equal to the golden.
4. Changing a prompt moves `PROMPT_RECIPE_HASH`, which is how a promotion is traced
   (`DLIB-OBS-07`), and ADR-0010's frozen-set gate decides whether it ships.

Measured on 2026-09-30: 3.4.0 renders S246's messages byte-for-byte like 3.3.1
([v3.4.md](v3.4.md)), so this path does not depend on which of the two versions is installed.
