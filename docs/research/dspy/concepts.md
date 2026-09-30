# DSPy concepts — signatures, modules, adapters, language models

**Part of:** [R009 · DSPy](INDEX.md) · **Version studied:** 3.4.0 (released 2026-09-25), cross-checked
against 3.3.1, which is what `uv.lock` pins today · **Sources:** the DSPy docs source at each release
tag (`docs/docs/learn/`, `docs/docs/diving-deeper/`) and the installed package source.

This is the "programming" stage of DSPy: how a task becomes a program. Evaluation and optimisation
are in [optimization.md](optimization.md); call shapes are in [api-reference.md](api-reference.md).

---

## The one idea that everything else follows from

A hand-written prompt mixes four separate decisions:

| Concern | The question it answers | DSPy object |
| --- | --- | --- |
| **What** | Which inputs go in, which typed outputs come out | `Signature` |
| **How it looks on the wire** | How inputs are written and outputs are parsed | `Adapter` |
| **Strategy** | Think first? Use tools? Sample several times? | `Module` |
| **Tuning** | Which instructions and examples work best for this model | Optimiser |

DSPy keeps these apart, so each can change without touching the others. You can swap the model or
the adapter and keep the program, and you can swap `ChainOfThought` for another module and keep the
signature. An optimiser can then rewrite the instructions against a metric.

**What this repo does today (S246).** We use the *adapter's rendered text* as a frozen format.
DSPy renders it offline, and the kernel reproduces it byte for byte. That gives us DSPy's typed
reasoning shape, but it leaves the optimisation stage unused: there is no metric, no dataset, no
optimiser run, and no saved program. See [three-roles-goal.md](three-roles-goal.md) for what that
leaves open.

The docs name three stages and ask that they be done in order:

1. **Programming.** Define the task, the pipeline and a few examples.
2. **Evaluation.** Build a development set and a metric.
3. **Optimisation.** Tune prompts or weights against that metric.

In the docs' words, *"it's unproductive to launch optimization runs using a poorly designed program
or a bad metric."*

---

## Signatures

A signature declares inputs and outputs. It says what to do, not how to ask.

- **Inline:** `dspy.Signature("question -> answer")`. Types are optional: `"context: list[str],
  question: str -> answer: str"`.
- **Class-based:** subclass `dspy.Signature`, declare typed fields with `dspy.InputField(desc=...)`
  and `dspy.OutputField(desc=...)`, and write a docstring.

Six facts decide how we design ours:

1. **The docstring is the instructions.** The adapter renders it at the end of the system message
   as *"In adhering to this structure, your objective is: …"*. With no docstring, DSPy writes
   *"Given the fields X, produce the fields Y."*
2. 🪤 **Optimisers rewrite only the docstring.** GEPA, MIPROv2 and COPRO change
   `signature.instructions`. They never touch field names, `desc` or `prefix`. Anything we put in a
   field description stays exactly as written, and an optimiser cannot improve it. S246's
   `meaning_here` description is fixed text for this reason.
3. **Field names are meaning.** `question` and `answer` are read by the model. Names must be
   unambiguous, because an optimiser cannot rename them later.
4. **Field order is prompt order.** Inputs first, then outputs, in declaration order.
   `ChainOfThought` prepends `reasoning`, so the reasoning is written before the answer.
5. **Types are pydantic.** Every field is a pydantic `FieldInfo`, and constraints such as `gt` and
   `min_length` are shown to the model. Output types can be `Literal[...]`, lists, dicts or pydantic
   models. A pydantic *output* renders its full JSON schema, descriptions included.
   🪤 A pydantic *input* loses its field descriptions: the model sees only the values (measured in
   DL-250). A glossary written as descriptions on an input model never reaches the model.
6. **Signatures are immutable.** `with_instructions`, `append`, `prepend`, `insert`, `delete` and
   `with_updated_fields` each return a new class. Compare with `Signature.equals(other)`; plain `==`
   compares class identity.

Output fields are required. A missing one raises `AdapterParseError`, unless the field has a
default, a `default_factory`, or an annotation that allows `None`.

---

## Modules

A module wraps a prompting strategy around any signature, and holds the learnable parameters: its
instructions, its demos and its LM.

**`dspy.Predict` is the only thing that calls the model.** Every other module is built from one or
more `Predict` instances, which is why optimisers look for `Predict` objects.

| Module | What it does | Relevance here |
| --- | --- | --- |
| `Predict` | One call, signature unchanged | The base of everything |
| `ChainOfThought` | `Predict` over `signature.prepend("reasoning", ...)`. `rationale_field_type=` makes the reasoning a typed pydantic model | **S246 uses exactly this** for defender and challenger |
| `BestOfN` | Runs a module N times at `temperature=1.0` with different `rollout_id`s and keeps the best by `reward_fn` | Inference-time selection |
| `Refine` | Like `BestOfN`, but after a failed attempt an extra LLM call writes advice, which is injected as a `hint_` input on the retry | **Inference-time enforcement** of a deterministic check ([three-roles-goal.md](three-roles-goal.md)) |
| `MultiChainComparison` | Reads M completions and writes one synthesised answer | Comparing several drafts |
| `majority` | A function, not a module: votes over completions | Discrete answers |
| `Parallel` / `Module.batch` | A thread-pool runner that carries settings into each worker | Evaluation runs |
| `ReAct` / `ReActV2` | A tool-using agent loop (`ReActV2` is async in 3.4) | Not needed for debate |
| `ProgramOfThought` / `CodeAct` | Write code, run it in a sandbox, answer from the output | Not needed |
| `RLM` | A REPL-driven explorer of large contexts (experimental) | Not needed |
| `Flex` | Its whole implementation is source code that GEPA can rewrite (experimental) | Not now |

**Composing modules.** Subclass `dspy.Module`, assign sub-modules in `__init__`, and write
`forward()`. Assignment is registration: optimisers find predictors by walking `self.__dict__`.
Always call `module(...)`, never `module.forward(...)`. `__call__` is what adds usage tracking,
callbacks and the caller stack.

**`named_predictors()`** lists what an optimiser will tune. For a three-role debate module it
returns `defender.predict`, `challenger.predict` and `judge.predict` (measured,
[three-roles-goal.md](three-roles-goal.md)).

**`_compiled=True`** freezes a sub-module. You can optimise one role, embed it, and optimise the
rest without disturbing it.

`Refine` and `BestOfN` in detail (read in the 3.4 source, `dspy/predict/refine.py`):

- Every attempt runs on `lm.copy(rollout_id=..., temperature=1.0)`. The temperature is forced to
  1.0, and each copy keeps its own `history`, so count calls through
  `dspy.clients.base_lm.GLOBAL_HISTORY`, not `lm.history`.
- The **whole wrapped module** is re-run. Wrapping a whole debate would re-run every role on a
  failure, so wrap only the step you are checking.
- `Refine`'s advice call (`OfferFeedback`) is sent the wrapped module's **source code**, its
  trajectory and the reward function's source code. It costs one extra LLM call per failed attempt.
- Failures inside an attempt are `print`ed, not logged.

---

## Adapters

An adapter sits between `Predict` and the model. It formats the signature, the demos and the inputs
into chat messages, and parses the reply back into typed values.

**Lifecycle:** preprocess → format → LM call → postprocess → parse. Each step can be overridden;
debug a malformed prompt by walking them in order.

| Adapter | Output format | Use when |
| --- | --- | --- |
| `ChatAdapter` (default) | `[[ ## field ## ]]` markers; a JSON schema for non-primitive types | Any model. **This is S246's format** |
| `JSONAdapter` | One JSON object, via native structured output where the model supports it | Models with a JSON mode; lower latency |
| `XMLAdapter` | `<field>value</field>` | Models that prefer tags |
| `TwoStepAdapter` | A free-form answer, then a cheap second model extracts the fields | Reasoning models that format badly |
| `BAMLAdapter` | JSON, with the schema shown in a compact BAML-style form | Deeply nested outputs |

What matters for us:

- **One coercion function.** Every adapter calls `parse_value(value, annotation)`: `str` passes
  through; `Literal` and `Enum` are matched; otherwise `json_repair.loads`, then
  `ast.literal_eval`, then pydantic `TypeAdapter`. S246 deliberately *rejects* the `json_repair` step
  (DL-252 D6), so a repaired reading is recorded as an error, not silently fixed.
- **ChatAdapter falls back to JSONAdapter.** In 3.3.1 it fell back on *any* exception. In 3.4 it
  falls back only on `AdapterParseError`. Turn it off with `use_json_adapter_fallback=False` when a
  parse failure should be visible.
- **You can print the exact prompt.** `adapter.format(signature, demos, inputs)` returns the
  messages, and `adapter.format_system_message(signature)` returns the system message alone.
  `dspy.inspect_history()` prints the last calls. S246's golden fixture is built from these calls.
- **Native model features arrive as types.** `dspy.Reasoning` maps to a model's native reasoning
  mode. `dspy.Citations` extracts Anthropic's native citations. `dspy.History` expands earlier turns
  into real chat messages. `dspy.Image`, `dspy.Audio` and `dspy.File` handle other media; 3.3 made
  their file and URL loading explicit (`from_path`, `from_url`).

---

## Language models

- `dspy.LM("anthropic/<model>", api_key=...)` configures a model. It went through LiteLLM up to 3.3;
  3.4 adds native engines (see [v3.4.md](v3.4.md)).
- 🪤 **Responses are cached by default.** The same request returns the same answer. Pass a new
  `rollout_id` with a non-zero temperature to force a fresh sample, or `cache=False` to disable the
  cache. The cache is a disk cache built on `diskcache`, which is the dependency behind the DL-184
  advisory.
- **Every LM keeps `history`** with the prompt, messages, response, `usage`, `cost`, model and a
  timestamp. `dspy.configure(track_usage=True)` adds per-prediction usage through
  `prediction.get_lm_usage()`. Cached responses count as zero.
- **Errors are typed:** `dspy.LMError` and its subclasses `ContextWindowExceededError` and
  `LMRateLimitError` (which carries `retry_after`).
- **Using your own client.** In 3.3 you subclass `dspy.BaseLM` and implement `forward()`. 🚨 **In
  3.4 that is deprecated, and it is removed in 3.5.** The replacement is an engine object with
  `complete(Request) -> Response`, passed as `dspy.LM(..., engine=MyEngine())`. DSPy still owns
  caching, retries, callbacks, history and usage accounting. This is how our `LLMClient` would plug
  in if DSPy ever ran live.

---

## Settings, context and threads

- `dspy.configure(lm=..., adapter=..., track_usage=...)` sets global defaults. Only the thread that
  first calls it may call it again; any other thread raises `RuntimeError`.
- `with dspy.context(lm=other):` overrides settings for one block. It is built on `contextvars`, so
  it survives `await` and `asyncio` tasks.
- 🪤 **Plain `threading.Thread` and `ThreadPoolExecutor` do not inherit `dspy.context`.**
  `dspy.Parallel`, `Module.batch` and `asyncify` copy the override into each worker. If you use your
  own pool, copy `dspy.settings.thread_local_overrides.get()` in yourself.
- Settings are read when a call happens, not when the object is built. A `dspy.context` around a call
  reaches every sub-module inside it.

---

## Saving and loading

- `program.save("x.json")` writes only state: each predictor's instructions, demos, field prefixes
  and descriptions, and the LM configuration. **The API key is never written.** The file is plain
  JSON, so it can be diffed and reviewed. `program.load("x.json")` into a freshly built instance.
- `save_program=True` pickles the whole module into a directory. Loading it needs
  `allow_pickle=True`, because loading a pickle can run code.
- `allow_unsafe_lm_state=False` (the default) drops `api_base`, `base_url` and `model_list` on load.
- Loading is transactional: it runs on a copy first and leaves the module untouched if it fails.
- Callbacks and history are never saved.

**Why this matters here.** The saved JSON is the natural handover from an offline optimiser run to a
DSPy-free runtime. Read each predictor's `signature.instructions` from the file, render them with
the kernel renderer that S246 proved byte-identical, and pin them in a golden fixture. See
[three-roles-goal.md](three-roles-goal.md).
