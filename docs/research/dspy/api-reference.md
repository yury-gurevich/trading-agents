# DSPy API reference — the calls this project would use

**Part of:** [R009 · DSPy](INDEX.md) · **Version:** 3.4.0 (the differences from 3.3.1 are marked) ·
**Source:** the installed package source and `docs/docs/api/` at the release tag.

A working subset, not the full reference: the calls a three-role deliberation program needs, with
the parameters that matter. The full upstream reference sits under `docs/docs/api/` in the DSPy
repository (adapters, evaluation, experimental, models, modules, optimizers, primitives,
signatures, tools, utils).

---

## Signatures

```python
class Ruling(dspy.Signature):
    """Docstring = instructions. The ONLY text an optimiser rewrites."""
    decision: str = dspy.InputField(desc="...")             # desc: fixed text, shown to the model
    context: str = dspy.InputField(desc="...")
    ruling: Literal["uphold", "overturn", "revise"] = dspy.OutputField()
    rationale: str = dspy.OutputField(desc="...")
    note: str | None = dspy.OutputField(default=None)       # optional output

Sig = dspy.Signature("decision, context -> ruling")        # inline form
Sig.with_instructions("...")         # new class; replaces the docstring
Sig.append_instructions("...")       # new class; appends to the docstring
Sig.prepend("reasoning", dspy.OutputField(), type_=GuidedReasoning)   # new class
Sig.with_updated_fields("context", desc="...")
Sig.instructions, Sig.input_fields, Sig.output_fields, Sig.fields
Sig.equals(Other)                    # structural equality; == is class identity
```

## Modules

```python
dspy.Predict(Sig, **lm_config)                      # the only thing that calls the LM
dspy.ChainOfThought(Sig, rationale_field_type=GuidedReasoning, **lm_config)
dspy.Refine(module, N, reward_fn, threshold, fail_count=None)   # reward_fn(args: dict, pred) -> float
dspy.BestOfN(module, N, reward_fn, threshold, fail_count=None)
dspy.MultiChainComparison(Sig, M=3, temperature=0.7)
dspy.majority(prediction_or_completions, field=None)

class Program(dspy.Module):
    def __init__(self):
        super().__init__()
        self.judge = dspy.ChainOfThought(Ruling, rationale_field_type=GuidedReasoning)
    def forward(self, decision, context, transcript):
        return self.judge(decision=decision, context=context, transcript=transcript)

program(**inputs)                    # always call; never .forward()
program.named_predictors()           # [("judge.predict", Predict), ...]: what optimisers tune
program.set_lm(lm); program.get_lm()
program.batch(examples, num_threads=8)
program.save("p.json"); program.load("p.json")
program.inspect_history(n=1)
pred.get_lm_usage()                  # with dspy.configure(track_usage=True)
```

## Adapters

```python
dspy.ChatAdapter(use_json_adapter_fallback=True)   # default; [[ ## field ## ]] markers
dspy.JSONAdapter(); dspy.XMLAdapter(); dspy.TwoStepAdapter(extraction_model=lm)
adapter.format(signature, demos, inputs)            # -> the exact list of chat messages
adapter.format_system_message(signature)
adapter.format_field_description(signature); adapter.format_field_structure(signature)
adapter.user_message_output_requirements(signature)
adapter.parse(signature, completion)                # -> dict of typed outputs
dspy.inspect_history(n=1)                           # print recent calls as sent
```

`dspy.adapters.utils.parse_value(value, annotation)` is the single coercion function behind every
adapter.

## Language models

```python
lm = dspy.LM("anthropic/claude-opus-5", api_key=..., temperature=..., max_tokens=..., cache=True)
lm("prompt"); lm.history[-1]["usage"]; lm.history[-1]["cost"]
lm.copy(rollout_id=1, temperature=1.0)              # fresh sample despite the cache
dspy.LMError, dspy.ContextWindowExceededError, dspy.LMRateLimitError   # .retry_after

# 3.4: a custom backend is an ENGINE (BaseLM.forward is deprecated; removed in 3.5)
from dspy.lm15 import Message, Response, Usage
class OurEngine:
    def complete(self, request):        # request: dspy.lm15.Request
        ...                             # call our LLMClient; keep its ledger and stop reasons
        return Response(id=None, model=request.model, message=Message.assistant(text),
                        finish_reason="stop", usage=Usage())
lm = dspy.LM("custom/deliberator", engine=OurEngine())
```

## Settings

```python
dspy.configure(lm=lm, adapter=dspy.ChatAdapter(), track_usage=True)  # owner thread only
with dspy.context(lm=other_lm): ...          # scoped; survives await; NOT plain threads
dspy.configure_cache(enable_disk_cache=False, enable_memory_cache=True)
```

## Evaluation

```python
dspy.Example(decision=..., context=..., transcript=...).with_inputs("decision", "context", "transcript")
def metric(gold, pred, trace=None, pred_name=None, pred_trace=None):   # all five: GEPA checks
    return dspy.Prediction(score=0.8, feedback="judge: ruled on process facts only")
dspy.Evaluate(devset=dev, metric=metric, num_threads=8, display_table=5,
              failure_score=0.0, save_as_json="eval.json")(program)    # -> EvaluationResult
```

## Optimisers

```python
dspy.GEPA(metric, max_metric_calls=150, reflection_lm=strong_lm,
          track_stats=True, log_dir="gepa-logs", seed=0).compile(program, trainset=tr, valset=va)
dspy.MIPROv2(metric, auto="light", prompt_model=strong_lm, task_model=lm).compile(program, trainset=tr)
dspy.BootstrapFewShot(metric, max_bootstrapped_demos=4, max_labeled_demos=16).compile(program, trainset=tr)
dspy.COPRO(prompt_model=strong_lm, metric=metric, breadth=10, depth=3).compile(program, trainset=tr, eval_kwargs={})
dspy.SIMBA(metric, bsize=32, max_steps=8).compile(program, trainset=tr)
dspy.experimental.ReAnchor(metric=metric).compile(program, trainset=tr, valset=va)   # 3.4
```

## Testing without an LLM

```python
from dspy.utils.dummies import DummyLM
dspy.configure(lm=DummyLM([{"reasoning": "...", "ruling": "revise", "rationale": "..."}]))
from dspy.clients.base_lm import GLOBAL_HISTORY    # counts calls made on lm.copy() instances too
```

`DummyLM` answers in the adapter's own format: from a list in order, from a dict keyed on prompt
text, or by following demos. Every mechanism in [three-roles-goal.md](three-roles-goal.md) was
checked this way at no cost.
