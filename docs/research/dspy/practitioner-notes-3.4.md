# DSPy 3.4.0 — practitioner notes, verified against the source and by running it

**Part of:** [R009 · DSPy](INDEX.md) · **Date:** 2026-10-03 · **Version:** `dspy==3.4.0` (what `uv.lock`
now pins), installed in a throwaway environment outside the repo · **Asked for by:** the operator
(*"your understanding of DSPy is lacking in depth … get yourself to the expected expertise level"*)

**How this was built.** Every claim below is labelled. **[measured]** means it was run offline with
DSPy's own `DummyLM`, or with a scripted custom engine (`complete(Request) -> Response`). Neither
makes an API call or costs anything. **[source]** means it was read in the installed package, with the
file named. **[not verified live]** means it needs a real provider call, which this session cannot make
(it has no API key). The four experiment scripts live in the planner's scratchpad, not in the repo.
Their key lines are quoted here.

---

## 1. The mental model, in one paragraph

A **Signature** is a typed contract: input and output fields, each with a description, plus
**instructions** (the class docstring). A **Predict** is the only learnable unit (`Parameter`). Its
state is its signature (instructions plus field descriptions), its **demos** (few-shot examples) and,
optionally, its own **LM**. A **Module** composes predictors in plain Python. An **Adapter** turns
signature + demos + inputs into chat messages, and parses the reply back into typed fields. An
**optimiser** changes predictor state (instructions and/or demos) to raise a **metric** over a
**dataset**. Nothing else is learnable: not the field descriptions, not the input values, and not
anything an adapter adds.

## 2. What the model actually sees (ChatAdapter) **[measured]**

The messages are: one **system** message, then demos as user/assistant pairs, then the current
**user** message (`dspy/adapters/base.py: format`).

| Text | Where it appears | Rewritten by optimisers? |
| --- | --- | --- |
| Signature instructions (the docstring) | system, at the end: *"your objective is: …"* | **Yes**: GEPA, MIPROv2, SIMBA, InferRules, COPRO |
| Input and output field descriptions (`desc=`) | system, in a numbered list | No |
| **Output** type schemas (pydantic, including sub-field `description`s, `Literal` options) | system, inline as a JSON schema | No |
| **Input** values | user message, one `[[ ## name ## ]]` section each | No |
| 🚨 **Input** model sub-field descriptions and docstrings | **nowhere**. A typed input is rendered as bare JSON | — |
| Demos | user/assistant pairs between system and user | Yes: Bootstrap*, MIPROv2, SIMBA |

🚨 **Consequence for the lab:** the meaning of a packet key cannot be attached to a typed packet's
schema. The experiment put `Field(description=…)` on every sub-field of an input model, and none of it
reached the prompt. Meanings must arrive as **data** (the book) or in a field `desc`.

**Parsing is forgiving** **[measured]**. `parse_value` runs `json_repair` and then pydantic, so a
trailing comma in a typed output parses cleanly. The repo's DSPy-free runtime (S246, DL-252 D6) is
strict on purpose and rejected exactly that (1 of 20 reading blocks). So parse failures in production
are a property of our parser, not of the model's output.

**`ChatAdapter` → `JSONAdapter` fallback** happens only on `AdapterParseError`. It is a second LM call,
on by default (`use_json_adapter_fallback=True`). **`JSONAdapter`** asks the provider for structured
output (a JSON schema) when the LM declares `response_format` support, which constrains decoding rather
than parsing free text **[source: `json_adapter.py`]**. For the judge's decision basis, that is the
robust choice **[not verified live for Anthropic in 3.4]**.

## 3. The LM layer (3.4 is a transition release)

- `dspy.LM("anthropic/claude-opus-5-5", reasoning_effort="high", max_tokens=…)`. **[measured]**
  `reasoning_effort` becomes the canonical `Reasoning(effort="high")`, which the Anthropic provider
  sends as `output_config.effort` for the adaptive-thinking model families **[source:
  `_vendor/lm15/providers/anthropic.py`]**.
- **Per-role models:** set `predictor.lm = …` per predictor **[measured]**. That LM is **saved into
  the program state**, so strip it before exporting an artifact. A custom engine without
  `dump_state()` / `load_state()` refuses to save **[measured]**.
- **Custom engines are the 3.5-proof integration point** **[source]**. An object with
  `complete(Request) -> Response` and `stream()`, passed as `dspy.LM(..., engine=…)`.
  `BaseLM.forward` subclasses are deprecated in 3.4 and removed in 3.5. **If DSPy is ever routed
  through our kernel `LLMClient` port (and its `LLMCall` ledger), write an engine.**
- **Prompt caching:** `dspy.LM(..., prompt_cache=dspy.lm15.CacheConfig(...))` puts Anthropic
  `cache_control` on the **system** message, or on a message boundary (`prefix_until_index`), never
  mid-message **[source]**.
- 🚨 **Sampling parameters and Opus 5.5.** `dspy.Refine` copies the LM with `temperature=1.0`
  (**[measured]**: requests carried `temperature=1.0`). `Predict` sets `temperature=0.7` when `n > 1`.
  SIMBA and MIPROv2 sample with temperatures too. For first-party Anthropic, lm15 sends `temperature`
  as given (it drops it only for listed third-party servers) **[source: `compat.py`,
  `anthropic.py:694–720`]**. Anthropic's documentation says Opus 5.5 rejects sampling parameters with a
  400. **So `Refine`, `BestOfN` and `n > 1` are expected to fail on our champion model as shipped**
  **[not verified live]**. The lab's retry-with-feedback (the decision code's form-law retry) must be
  our own loop, not `dspy.Refine`.
- 🚨 **`dspy.track_usage()` misses work done in `dspy.Parallel` threads** **[measured]**: 3 sequential
  calls reported 60 tokens, while 3 parallel calls reported none. The lab counts cost in its own engine
  or ledger.

## 4. Modules worth knowing here

| Module | Use in this project | Note |
| --- | --- | --- |
| `Predict` | every seat | the only learnable unit |
| `ChainOfThought(sig, rationale_field_type=T)` | readings before the argument | prepends one `reasoning` **output** field typed `T` (str by default). This is **written** reasoning, separate from the model's private thinking |
| `dspy.Reasoning` (type) | not the guided reasoning | a field of this type asks the provider for **native** thinking and removes the field from the prompt; it defaults to `reasoning_effort="low"` if none is set **[source]** |
| `dspy.Parallel` / `module.batch` | pro and con concurrently | **[measured]** 3 predictors ran, 2 in parallel; see the usage caveat |
| `dspy.History` (input type) | the finance-model consultation as a multi-turn dialogue | turns render as prior user/assistant messages |
| `Refine`, `BestOfN` | — | sampling-temperature problem above; Refine also spends an extra LM call writing *advice* |
| `MultiChainComparison` | possible later judge variant | compares M attempts and synthesises; its default `temperature=0.7` carries the same sampling problem **[source]** |
| `experimental.Choice / Score / Noul` | the judge's ruling with a recorded distribution | generative models **self-report** confidence. With `dspy.experimental.TypeSafe` (a System One client, in 3.4) the same signature runs on TypeSafe's Jev: the shadow path in [ideas.md](../../ideas.md) without new plumbing |
| `Flex`, `RLM`, `ReAct(V2)`, `CodeAct` | not needed | Flex lets GEPA evolve Python source; not for this project |

## 5. Optimisers: what each one changes **[source, GEPA measured]**

| Optimiser | Changes | Note for us |
| --- | --- | --- |
| **GEPA** | **instructions only** (and `Flex` code). **[measured]** field `desc` unchanged | metric `(gold, pred, trace, pred_name, pred_trace)`. Returns `dspy.Prediction(score, feedback, objective_scores={…})`. **[measured]** separate objectives get their own Pareto front. Budget: exactly one of `auto` / `max_metric_calls` / `max_full_evals`. Needs a `reflection_lm` |
| MIPROv2 | instructions + demos | Bayesian search; `init_temperature=1.0` (sampling issue) |
| SIMBA | appends rules to instructions, adds demos | samples at temperature 0.2 |
| BootstrapFewShot (+RandomSearch) | demos | keeps traces that pass the metric. With a stratified trainset it is the tool for item 75 (balanced `uphold` / `overturn` examples) |
| **InferRules** | appends induced natural-language rules to instructions | a **drafting tool for Tier C judgement laws** from operator-approved expert cases. Its rules are candidates for the operator, never the decision code itself |
| COPRO | instructions + the last output field's `prefix` | the prefix is deprecated and no longer rendered |
| ReAnchor (experimental) | thresholds, cuts and weights of decision types | needs probability-bearing outputs; fits nothing on a validation fold |
| BootstrapFinetune / GRPO / BetterTogether | **weights** | relevant only if an open finance model (Fin-R1) is ever tuned locally |

**What GEPA's reflection model sees** **[measured]**, per predictor: each example's **Inputs**,
**Generated Outputs** and **Feedback**, plus the current instruction. The prompt tells it to
*"identify all niche and domain specific factual information … and include it in the instruction"*.
Two consequences:

1. **The feedback text is the steering wheel.** *"basis 'gates passed' is a process fact; name the
   quant reading that decides it"* produced an instruction that fixed the behaviour in one step
   **[measured]**.
2. 🪤 **GEPA copies domain facts into instructions, and it does not see a book placed in the system
   message.** It could write a meaning that contradicts the book. The guard is in the metric:
   feedback **quotes the book's entry** whenever a reading is wrong, and the form laws (DEC-FORM-02 / 06)
   check every candidate's outputs against the dictionary.

## 6. What this changes in the lab design

| Lab section | Was | Now |
| --- | --- | --- |
| §4, §13: where the book lives | "a dedicated input field" | **A custom adapter renders the book in the system message, outside `signature.instructions`.** **[measured]** It survived a GEPA run untouched. It is cacheable with `prompt_cache` (one system breakpoint), and the same bytes reach every seat. The input-field route stays as an arm, since it makes the book visible to GEPA's reflection model at the cost of a larger reflection prompt |
| §2: typed packet | implicit | A typed packet is fine for structure, but **its schema descriptions never reach the model** **[measured]**. Meanings come only from the book |
| §5: `Refine` on the judge | proposed in [three-roles-goal.md](three-roles-goal.md) step 7 | **Our own retry loop** (the form-law retry), because `Refine` forces `temperature=1.0` |
| §11: the judge's output | ChatAdapter text | **JSONAdapter with a schema** for the decision basis, once structured-output support for Opus 5.5 is confirmed live; ChatAdapter as the fallback arm |
| §6: cost | per call | **our engine counts tokens**; `track_usage` is blind inside `Parallel` |
| §14: drafting Tier C | operator and planner | plus **InferRules** as a candidate generator over approved expert cases |
| Production | S246's DSPy-free renderer | unchanged (DL-252). A promoted program is exported from `save()` state: the **instructions and demos** per predictor, with the LM stripped, plus the **adapter's book** version. A parity test renders it byte-for-byte without DSPy |

## 7. Self-assessment: what is known, and what is not yet

- **Known and verified:** prompt rendering and placement; what is and is not learnable; how GEPA
  works, including the reflection prompt, objective scores and budgets; per-role LMs; saving; the
  effort mapping; custom engines; the parse repair; the usage-tracking gap.
- **Read but not run:** MIPROv2, SIMBA and BootstrapFewShot internals; ReAnchor; the TypeSafe client;
  JSONAdapter structured output against a real provider.
- **Needs a live key, on the operator's machine:** the Opus 5.5 temperature 400; JSONAdapter's
  structured output on Anthropic; prompt-cache hits (`cache_read_input_tokens`); GEPA's real cost per
  metric call on our packets.
