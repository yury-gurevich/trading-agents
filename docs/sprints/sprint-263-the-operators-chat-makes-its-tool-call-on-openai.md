<!-- Agent: planning | Role: sprint handover -->
# Sprint 263 — the operator's chat makes its tool call on OpenAI, with the effort and the model its declared vendor accepts

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-263-the-operators-chat-makes-its-tool-call-on-openai`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-284](../design-log.md) (this sprint's nine decisions, made and measured) · [DL-282](../design-log.md) amendment 2 (what S262's paid check refuted) · [work-queue 121](../work-queue.md)

> **Why this bump kind.** No new capability: S262 already promises the dashboard chat on the declared
> vendor, and on OpenAI the code cannot deliver it. A fix, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/operator/laws/laws.md`, `surfaces/laws/laws.md` | One component's **locked constitution** | **LOCKED.** This sprint amends these two under a law cycle, named below. Any other clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md`, `surfaces/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: operator **`DEP`**, **`NEV`**, **`FAIL`**, **`STA`**, **`PERF`**, **`PARAM`**;
surfaces **`DEP`**.

### The rule

1. **Before writing code**, read every law file in the map below, whole.
2. Read each component's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It is answered for you; confirm it against what you read.
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No file in `contracts/` changes, and none may. Yes, two components change a guarantee**, so two law
cycles are owed in this unit of work:

| Book | From | What the cycle owes |
| --- | --- | --- |
| `agents/operator/laws/laws.md` | LOCKED v1.5 | `OPR-DEP-01` reworded, keeping what it says and adding: an empty effort resolves the declared provider's default, as an empty model does; an explicit model whose name belongs to another provider's family is refused before any call. `PARAM` row `effort`: Value `""`, Type `""\|none\|low\|medium\|high\|xhigh\|max`, Rationale as decision D5 below. The `CAP` block's `effort` line follows the row. Changelog line, version up |
| `surfaces/laws/laws.md` | LOCKED v1.4 | `SRF-DEP-03` reworded, adding one more cause that leaves chat disconnected (an explicit model of another provider's family) and that the dashboard's start-up output names that cause. Changelog line, version up |

No clause ID is added, so the rollup counts should not move. Each reworded clause has its
`test-plan.md` row updated to cite the tests that now prove it, and the rollup lines in **both**
`docs/laws/ledger.md` **and** `docs/laws/INDEX.md` name this sprint.
🪤 **The rollup is derived, not declared.** `make ci` recomputes it. Let the gate tell you the number.
🪤 **The parameter step compares every `PARAM` row's Value and bounds with the code** (S258). It is
measured for this sprint: red on the changed default, green once the row follows (table below).

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/llm_openai_operator.py` | `agents/operator/laws/laws.md` + `test-plan.md`; `tests/test_llm_adapter_ownership.py` and `tests/test_llm_adapter_security.py` (read both whole: they are the kernel's rules for adapters) | `OPR-NEV-05` (the model is held to a tool schema; anything else is refused), `OPR-FAIL-01` / `OPR-FAIL-02` (a failed or unusable call is a refusal, never a raise to the bus), `OPR-STA-03` (every call recorded, usage included), `OPR-PERF-01` (the cap covers reasoning and output together), `OPR-PERF-03` (single turn, no streaming) |
| `kernel/llm_factory.py` | the same two test files; `agents/operator/laws/laws.md` | `OPR-DEP-01`: the declared provider is the sole external call and never falls back; S222: vendor adapters and their factory live only in `kernel/` |
| `agents/operator/settings.py` | `agents/operator/laws/laws.md`, the `PARAM` table | the `effort` row; `OPR-DEP-01` |
| `surfaces/dashboard/chat_binding.py` | `surfaces/laws/laws.md` + `test-plan.md` | `SRF-DEP-02` (the dashboard stays useful when chat is absent), `SRF-DEP-03` |
| `kernel/llm_openai.py` (**two lines deleted, nothing else**) | `agents/deliberator/laws/laws.md` (read only) | it is the client every debate turn runs on |
| `agents/deliberator/tests/test_llm_openai_adapter.py` (**one line added and one stale comment corrected, nothing else**) | `agents/deliberator/laws/laws.md` (read only) | DL-105: the debaters' effort values must stay ones the SDK knows |

⚠️ **The one invariant this sprint must not break: the debate's code does not change.**
`kernel/llm_factory.py::build_llm`, `kernel/llm_openai.py::OpenAILLMClient` and its helper functions,
`kernel/llm_anthropic*.py` and everything under `agents/deliberator/` except the rider (one added
test line and its stale comment) stay byte for byte as they are. Nor does any file under a fidelity decision path change:
`agents/scanner/`, `agents/analyst/`, `agents/portfolio_manager/`, `agents/provider/domain/`,
`agents/execution/order_tolerance.py`, `contracts/`, `orchestration/packs/trading_tunables.json`,
`orchestration/packs/trading_issuer_map.json`, `orchestration/history_window.py`. **If your build
needs one of them changed, stop and report.**

---

## Goal

At merge, with `OPERATOR_LLM_PROVIDER=openai` and nothing else set, the operator's dashboard chat
binds a client that asks `gpt-5.5` for one forced function through the vendor's Responses API, at the
deepest effort that model accepts, and returns the function's arguments. A reply cut at the output
cap is recorded with its tokens and refused. An explicit model that belongs to the other vendor
leaves the chat disconnected and the dashboard says why when it starts, instead of sending that name
to a vendor that does not have it. On Anthropic nothing changes.

## Why (context)

[S262](sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it.md) made the
vendor one declared value and gave the operator's chat an OpenAI adapter. Its paid check, F1b, then
failed before any generation: `gpt-5.5` answered HTTP 400 to the operator's default effort `max`,
and, with an accepted effort, HTTP 400 again because Chat Completions takes no function tool
together with a reasoning effort on that model. The adapter's design had been decided unmeasured.
The operator's `.env` also holds `OPERATOR_MODEL=claude-opus-5`, copied from `.env.example`, which
wins over the provider's default and would be sent to OpenAI as is.

Until this is fixed the chat stays on Anthropic, whose account is empty until 2026-10-11, so the
dashboard has no working chat on either vendor.

### Measured, 2026-10-09 — read these before designing

Scripts, the captured prompts, every wire request and reply, and the prototype's diff are outside
the repository (`trading-agents-data/wq121-2026-10-09/`). The builder cannot reach them and does not
need to: what matters is in this file, and one captured reply is in the worktree as a fixture.

| Claim | Value | How it was measured |
| --- | --- | --- |
| The Responses API's request for one forced function | `responses.create(model, max_output_tokens, reasoning={"effort": ...}, instructions, input, tools=[{"type": "function", "name", "description", "parameters", "strict"}], tool_choice={"type": "function", "name": ...}, store)`; `strict` is a required key of the SDK's tool type | *[measured, read]* the installed SDK, `openai` 2.49.0, `types/responses/response_create_params.py`, `function_tool_param.py`, `tool_choice_function_param.py`; and the body the SDK put on a fake transport |
| Where the arguments sit in the reply | `output` is a list of items; the one with `type == "function_call"` has `arguments`, a JSON **string**, and `name`; a `type == "reasoning"` item comes before it when the model reasoned | *[measured]* six replies from the vendor |
| How the reply says it finished | `status: "completed"` and `incomplete_details: null` | *[measured]* six replies |
| How a cut-off reply is reported | `status: "incomplete"`, `incomplete_details.reason: "max_output_tokens"` (the other reason the type allows is `content_filter`) | *[read in the SDK's types — NOT produced by the vendor]* no call came near the cap; the prototype was run on a captured reply cut by hand |
| Usage fields | `usage.input_tokens`, `usage.input_tokens_details.cached_tokens`, `usage.output_tokens`, `usage.output_tokens_details.reasoning_tokens`, `usage.total_tokens`; also `input_tokens_details.cache_write_tokens` | *[measured]* six replies |
| `cached_tokens` is a part of `input_tokens` | assumed, as on Chat Completions | *[ASSUMED]* the SDK calls it *"a detailed breakdown of the input tokens"*; all nine replies read 0. The paid check after merge reads it if a cache hit occurs |
| The chat's real prompts | explain for `sched-2026-10-08`: 21,049 tokens (system 37; `tiktoken`, `o200k_base`), which the vendor counted as 21,133 with the tool; interpret: about 290 | *[measured]* captured from the live graph through the chat binding with a fake model; no vendor call |
| `gpt-5.5`, Responses, effort `max` | HTTP 400: *"Unsupported value: 'max' is not supported with the 'gpt-5.5' model. Supported values are: 'none', 'low', 'medium', 'high', and 'xhigh'."* Nothing billed | *[measured]* one call |
| `gpt-5.5`, Responses, forced function, interpret prompt | `xhigh`: 4.6 s, 187 output tokens, 121 of them reasoning. `high`: 2.9 s, 60, 0. `medium`: 2.9 s, 58, 0. `none`: 3.1 s, 65, 0. Each returned the intent | *[measured]* one call each |
| `gpt-5.5`, Responses, forced function, explain prompt | `xhigh`: 9.4 s, **811 of 4,096** output tokens, 516 reasoning. `high`: 5.8 s, 293, 0 reasoning | *[measured]* one call each |
| The vendor's other road, Chat Completions with effort `none` | accepted on both prompts (3.4 s and 60 tokens; 6.6 s and 307 tokens); `finish_reason` is `tool_calls` | *[measured]* one call each |
| What the measurement cost | $0.38 over nine calls, at the price pack's rates | *[measured]* the vendor's own token counts |
| A prototype of the whole change | five code files and one law row; replaying the six accepted Responses replies through the real SDK on a fake transport gives back what the paid calls returned, with the same stop reason and usage, and the request sent equals the request captured on the wire | *[measured]* `git diff --stat`; the replay, also run in a process where DSPy had registered its lazy `openai` module first |
| Existing tests the prototype breaks | **Eight cases in five test functions, three files**: `tests/test_openai_operator.py::test_b2_operator_forces_one_named_function`; `tests/test_openai_operator_edges.py::test_b3_unusable_tool_reply_is_refused` (four cases), `::test_b3_length_raises_after_recording_usage`, `::test_transport_failure_clears_old_accounting`; `agents/operator/tests/test_operator_settings.py::test_effort_defaults_to_max` | *[measured]* 71 tests over the adapter, the factory, the operator and the chat binding, run on the prototype |
| A test that keeps passing for the wrong reason | `tests/test_openai_operator_security.py::test_b6_openai_key_never_escapes_operator` passes on the prototype although its fake SDK has no `responses`: the operator turns the `AttributeError` into a refusal and the key is still absent | *[measured]* it is in the 62 that passed |
| The parameter step on the prototype | exit 1, `agents/operator/laws/laws.md:190: operator.effort law Value '"max"' differs from code default ''`; exit 0 after the row is rewritten | *[measured]* `scripts/check_param_law_sync.py`, both runs |
| `mypy`, the import contracts, the size check on the prototype | clean; `kernel/llm_openai_operator.py` **118** lines, `kernel/llm_factory.py` **137**, `agents/operator/settings.py` **75**, `surfaces/dashboard/chat_binding.py` **61**, `kernel/llm_openai.py` **103** | *[measured]* |
| Other users of `completion_usage` and `completion_stop_reason` | none: `kernel/llm_openai_operator.py` is the only importer of the two aliases at the foot of `kernel/llm_openai.py` | *[measured]* `grep` over every tracked `.py` |
| The SDK is in the test environment | yes: `openai` 2.49.0 arrives with `dspy` in the dev group | *[measured]* `uv tree --locked --invert --package openai` in the worktree, whose venv was synced with no extra |
| The rider's test | `agents/deliberator/tests/test_llm_openai_adapter.py::test_our_effort_values_are_all_valid_openai_values` **fails on `main` when the file is run alone** (`ImportError: cannot import name 'construct_type' from partially initialized module 'openai._models'`), and passes with one line added | *[measured]* three runs in the worktree. Importing `agents.deliberator.agent` leaves `sys.modules["openai"]` a DSPy `_LazyModule`; a first import of an `openai` submodule in that state is circular |
| Where the operator's variables are set | `.env.example` sets `OPERATOR_MODEL=claude-opus-5`; no pack, no deploy script and no doc outside the sprint files sets `OPERATOR_MODEL`, `OPERATOR_EFFORT` or the provider | *[measured]* `grep` |

---

## Scope — and what is deliberately NOT here

1. **The adapter makes its call through Responses (D1 to D4).** `kernel/llm_openai_operator.py` is
   rewritten; the class keeps its name and constructor arguments, and its default effort becomes
   `"xhigh"`. The Appendix holds the measured prototype. The two aliases at the foot of
   `kernel/llm_openai.py` go with it.
2. **The effort resolves from the provider (D5).** `OperatorSettings.effort` defaults to `""` and
   accepts `""`, `none`, `low`, `medium`, `high`, `xhigh`, `max`; a new `resolved_effort` property
   mirrors `resolved_model`; `kernel/llm_factory.py` gains the per-provider default and
   `default_operator_effort_for`. The chat binding passes the resolved value.
3. **A model of another vendor's family is refused (D6).** `kernel/llm_factory.py` gains the family
   prefixes, `model_provider(model)`, `ModelProviderMismatchError`, and the check at the top of
   `build_operator_llm`. `build_llm` is not touched. The chat binding catches the error, writes one
   line to standard error (`dashboard: operator chat not connected: <the error>`) and returns `None`.
4. **The two law cycles**, as the table above says.
5. **`.env.example` (D8):** the three lines that set `OPERATOR_MODEL` are replaced by a comment
   naming the three operator variables and saying that an unset model and effort resolve from the
   provider. No variable is set there.
6. **The rider (D9):** in `agents/deliberator/tests/test_llm_openai_adapter.py`, one line before the
   submodule import that reads an attribute of the package, so the package is loaded first; and the
   comment above `_OPENAI_REASONING_EFFORT`, which says CI does not install the SDK, corrected (it
   arrives with DSPy in the dev group). Change no assertion and nothing else in that file.
7. **The fixture.** `tests/fixtures/openai_responses_forced_function.json` is already in your
   worktree, untracked: one captured request and reply (Appendix). Commit it unchanged.

### Out of scope (do NOT build this sprint)

- **The debaters.** Their default effort is `max` too and they would send another vendor's model as
  is; on the fleet the tunables pack guards both. Work-queue 123. Do not touch `build_llm`,
  `agents/deliberator/settings.py` or the tunables pack.
- **The operator container.** It keeps the fake client.
- **Streaming, stored replies, `previous_response_id`, strict schemas, the reasoning summary.**
- **A check of the effort against a per-vendor list.** The vendor refuses a value its model does not
  take, before generation and with the supported values named.
- **The cap.** It stays 4,096 and its bound stays `le=4096`.
- **`docs/STATE.md`, `docs/work-queue.md`, `docs/design-log.md`** (one exception: an amendment under
  DL-284 if the build forces a decision).
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

Recorded in full in [DL-284](../design-log.md). In short:

- **Stay on Chat Completions with effort `none`.** Rejected: measured to work, but every other
  effort is refused there with a function tool, so the operator's effort setting would mean nothing
  on this vendor.
- **Translate `max` to `xhigh` in the adapter.** Rejected: an explicit value the model refuses must
  be seen, not rewritten.
- **Default to `high` on OpenAI.** Rejected: with a forced function `high` wrote no reasoning token
  on either prompt.
- **Record the cut-off as Chat's `length`.** Rejected: the ledger keeps each vendor's own word.
- **Refuse any model name not known here.** Rejected: a new or fine-tuned name is the vendor's to
  judge.
- **Stop the dashboard on a mismatched model.** Rejected: the chat is one panel of the status board.

---

## The design decisions — made, and recorded in DL-284

Build them as written. If one cannot be built as written, stop and report.

- **D1.** The call is `self._client.responses.create(...)` with exactly these arguments: `model`,
  `max_output_tokens` (the cap), `reasoning={"effort": <effort>}`, `instructions` (the system text),
  `input` (the user text), `tools` (one function tool: `type`, `name`, `description`, `parameters`,
  `strict: False`), `tool_choice={"type": "function", "name": <name>}`, `store=False`. The function
  names, descriptions and the answer schema stay as they are today.
- **D2.** The arguments are those of the **first** `output` item whose `type` is `function_call`.
  No such item, or arguments that are not a JSON object, give today's refusal dictionary.
- **D3.** `last_stop_reason` is `incomplete_details.reason` when it is set, else `status`, else the
  port's `unknown`. When it is `max_output_tokens` the adapter raises
  `LLMCompletionStoppedError(provider="openai", stop_reason="max_output_tokens")`, **after** setting
  `last_stop_reason` and `last_usage`.
- **D4.** `last_usage`: `tokens_in = input_tokens - cached_tokens` (never below 0),
  `cache_read_tokens = min(cached_tokens, input_tokens)`, `tokens_out = output_tokens`, through
  `llm_usage_or_none`. `cache_write_tokens` is not read.
- **D5.** `DEFAULT_OPERATOR_EFFORT = {"anthropic": "max", "openai": "xhigh"}` in the factory.
  `OperatorSettings.resolved_effort` returns the explicit value or that default. An explicit value is
  passed as set on both vendors.
- **D6.** `MODEL_PREFIXES = {"anthropic": ("claude-",), "openai": ("gpt-", "chatgpt-", "o1", "o3", "o4")}`.
  `build_operator_llm` raises `ModelProviderMismatchError` when the provider is a known one and the
  model starts with a prefix of a different provider. An unknown provider still raises
  `UnknownProviderError`. A model that starts with no listed prefix is built.
- **D7.** The cap and its bound do not change.
- **D8.** `.env.example` sets no operator model.
- **D9.** The rider is one added line and a corrected comment.

🪤 **Take the next free DL number only if the build forces a new decision, then re-check it at
merge.** DL-284 is this sprint's; an amendment goes under it.

---

## Blast radius — measured 2026-10-09

| What | Detail |
| --- | --- |
| Files changed | `kernel/llm_openai_operator.py` **104**, `kernel/llm_factory.py` **97**, `kernel/llm_openai.py` **107** (two alias lines deleted), `agents/operator/settings.py` **69**, `surfaces/dashboard/chat_binding.py` **51**; tests `tests/test_openai_operator.py` **84**, `tests/test_openai_operator_edges.py` **108**, `tests/test_openai_operator_security.py` **84**, `tests/test_operator_llm_factory.py` **83**, `agents/operator/tests/test_operator_settings.py` **39**, `surfaces/tests/test_dashboard_chat_provider.py` **81**, `agents/deliberator/tests/test_llm_openai_adapter.py` **124** (one line); two law books, their test plans, the two rollups; `.env.example`. New: `tests/fixtures/openai_responses_forced_function.json`, and test files as you need them |
| Agents affected | operator; surfaces; kernel. No agent imports another |
| Contract change? | No, and none is allowed |
| Graph vocabulary change? | No |
| New env keys / tunables | None. `OPERATOR_EFFORT` exists; its default changes from `max` to empty |
| Deploy implication | None required. The chat runs in the dashboard, from the main checkout; the fleet's operator container binds the fake client. The next retag carries the code |
| Rollback | Revert the merge commit. Nothing is deployed and nothing outside the repository changes |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Read DL-284** in `docs/design-log.md`, and DL-282's amendment 2.
3. **Plant the failing tests first** (A1, A3, B1, B3, C1 of the Test plan) and watch them fail. Paste
   the red output.
4. **Implement**, in the order of Scope 1 to 3, then 5 to 7.
5. **Law cycles**: the two reworded clauses, the `PARAM` row, the test-plan rows, the docstring
   citations, the rollups.
6. **Prove the guards can fail (DL-70)**: break the implementation, watch each guard go red, restore.
7. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Unit tests inject a fake SDK through `importlib.import_module`, as the existing ones do, with
`SimpleNamespace` replies that carry the field names of the fixture. One test, A8, uses the real SDK.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 the request is the measured one | a fake SDK whose only attribute is `responses`, recording the keyword arguments | for a call with a schema and one without: exactly the eight arguments of D1 and no other; `tool_choice` names `parse_intent` / `answer_question`; one tool, `strict` is `False`, the description is not empty; `store` is `False`; `reasoning` is `{"effort": <the constructor's>}`; `max_output_tokens` is the cap. `OPR-DEP-01` / `OPR-NEV-05` |
| A2 | the reply is read from the function call item | a reply whose `output` is a `reasoning` item, then a `function_call` | the arguments come back as JSON for a schema call, and the `answer` string for a call without one; `last_stop_reason == "completed"`; usage 400 in with 100 cached reads `tokens_in 300`, `cache_read_tokens 100`. `OPR-STA-03` |
| A3 | 🎯🪤 a cut-off reply is recorded, then refused | `status="incomplete"`, `incomplete_details.reason="max_output_tokens"`, `output` a `reasoning` item only, `output_tokens=4096` | `LLMCompletionStoppedError` with provider `openai` and stop reason `max_output_tokens`; `last_stop_reason` and `last_usage.tokens_out == 4096` are set when it is raised. `OPR-FAIL-01` / `OPR-STA-03` |
| A4 | 🪤 an unusable reply is the refusal, not a raise | each of: empty `output`; a `message` item with a `refusal` and no function call; a `function_call` whose `arguments` is `None`, `"not json"`, `"[]"`, `23` | the refusal dictionary `{"outcome": "refused", "reason": "model returned no tool result"}`. `OPR-NEV-05` / `OPR-FAIL-02` |
| A5 | a filtered reply | `status="incomplete"`, reason `content_filter`, no function call | the refusal dictionary, `last_stop_reason == "content_filter"`, no raise |
| A6 | a failed call clears the last call's accounting | `create` raises `TimeoutError` after a good call | the error propagates; `last_stop_reason == "unknown"`, `last_usage is None`. `OPR-STA-03` / `OPR-FAIL-01` |
| A7 | the SDK is loaded lazily and a missing key refuses | as today's `test_optional_sdk_is_lazy_and_missing_key_refuses` | unchanged behaviour on the new adapter. `OPR-SEC-01` |
| A8 | 🎯 the captured reply, through the real SDK | `tests/fixtures/openai_responses_forced_function.json`; the adapter's client replaced by `openai.OpenAI(api_key=..., max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(handler)))` | the body the SDK sends equals the fixture's `request`, the path is `/v1/responses`, the result equals the fixture's `returned`, `last_stop_reason == "completed"`, usage is 286 in, 187 out, 0 cached. `OPR-DEP-01` |
| B1 | 🎯 the effort resolves from the provider | `OPERATOR_EFFORT` unset, the provider set each way; then explicit values | `effort == ""`; `resolved_effort` is `max` on `anthropic` and `xhigh` on `openai`; an explicit `none`, `low`, `medium`, `high`, `xhigh`, `max` is returned as set on both; `maximum` is refused when the settings load. `OPR-DEP-01` |
| B2 | the default effort for an unknown provider | `default_operator_effort_for("opnai")` | `UnknownProviderError` |
| B3 | 🎯🪤 another vendor's model is refused and nothing is built | `build_operator_llm("openai", model="claude-opus-5", ...)` and the reverse with `gpt-5.5`, both vendor classes patched to record calls | `ModelProviderMismatchError` whose message names the model, its family and the declared provider; neither class was called. `OPR-DEP-01` |
| B4 | 🪤 names the table does not know are built; an unknown provider is still its own error | `model="ft:gpt-5.5:acme"`, `"my-local-model"`, `"explicit"` on a known provider; `("opnai", "claude-opus-5")` | the selected class is called once; the last raises `UnknownProviderError`, not the mismatch |
| C1 | 🎯 the binding refuses another vendor's model and says why | `OPERATOR_LLM_PROVIDER=openai`, `OPERATOR_MODEL=claude-opus-5`, a key present, `importlib.import_module` patched to record | `bind_dashboard_chat` returns `None`; standard error holds one line starting `dashboard: operator chat not connected:` that names `claude-opus-5`, `anthropic` and `openai`; the SDK was not imported. `SRF-DEP-03` |
| C2 | the binding passes the resolved effort and model | `OPERATOR_MODEL` and `OPERATOR_EFFORT` unset, the provider each way, `build_operator_llm` replaced by a recorder | `gpt-5.5` with `xhigh` on `openai`; `claude-opus-5` with `max` on `anthropic`. `SRF-DEP-03` / `OPR-DEP-01` |
| D1 | 🪤 the key stays inside the adapter, and the call really ran | today's `test_b6`, its fake SDK now exposing `responses.create` and returning a `function_call` | the result's outcome is `intent` **and** the sentinel key is absent from the result, the graph and the log. `OPR-SEC-01` |
| E1 | the rider | the one line | `uv run pytest agents/deliberator/tests/test_llm_openai_adapter.py -q --no-cov` passes when run alone (it fails before the line) |

---

## Success factors

- [ ] With the provider `openai` and no model or effort set, the binding builds the OpenAI operator
      client with `gpt-5.5` and `xhigh` (C2), and its call is the request captured from the vendor (A8).
- [ ] A reply cut at the cap raises after its tokens are recorded (A3); an unusable reply is the
      refusal (A4).
- [ ] An explicit model of the other vendor's family builds nothing and leaves the chat disconnected
      with the reason on standard error (B3, C1).
- [ ] On Anthropic the resolved model and effort are what they were: `claude-opus-5`, `max` (B1, C2).
- [ ] `build_llm`, `OpenAILLMClient` and its helpers, `kernel/llm_anthropic*.py` and
      `agents/deliberator/` are unchanged apart from the two deleted alias lines and the rider;
      the command in the handback checklist prints nothing.
- [ ] Both law cycles done: `OPR-DEP-01` and `SRF-DEP-03` reworded and re-proven, the `effort` row
      and the `CAP` line, changelogs, versions, test-plan rows, both rollups.
- [ ] `scripts/check_param_law_sync.py` exits 0.
- [ ] Every guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **`test_b6` passes on the new adapter without being touched.** Its fake SDK has no `responses`,
the operator's fault boundary turns the `AttributeError` into a refusal, and the key is still absent.
A green run there proves nothing until the test also asserts the outcome is `intent` (D1).
🪤 **DSPy's lazy `openai`.** Importing the deliberator loads DSPy, which leaves
`sys.modules["openai"]` a lazy placeholder. A first import of a submodule (`openai.types...`) in that
state fails with a circular import. Reading an attribute of the package loads it: `openai.OpenAI(...)`
is enough, which is why the adapters work. In A8 construct the client before you import anything
under `openai.`; better, import nothing under it.
🪤 **Do not make `high` the default because the debaters run on it.** With a forced function `high`
wrote no reasoning token; that is measured, on both prompts.
🪤 **The SDK's effort type is not the model's list.** It names `max` and `minimal`; `gpt-5.5` named
neither as supported. Do not validate against the SDK's type.
🪤 **`strict` must be sent.** It is a required key of the SDK's tool type, and `False` is what the
vendor accepted. A fake SDK will not notice it missing; A1 and A8 must.
🪤 **Tests must not depend on a `.env`.** `OperatorSettings()` reads one where it exists, and the
main checkout's holds `OPERATOR_MODEL=claude-opus-5`. Every test that reaches the binding or the
settings sets or deletes `OPERATOR_LLM_PROVIDER`, `OPERATOR_MODEL` and `OPERATOR_EFFORT` itself; an
environment variable wins over the file. After this sprint a test that binds OpenAI with that file's
model in force would be refused.
🪤 **The stop reason on Chat Completions was `tool_calls`, not `stop`.** Nothing in the new adapter
reads a `finish_reason`; if you find yourself writing one, you are on the old endpoint.
🪤 **`kernel/llm_openai.py` is the debate's client.** Delete the two alias lines and the blank line
that goes with them; `ruff format` must leave the file with no other change.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `kernel/llm_openai_operator.py` **104**, `kernel/llm_factory.py` **97**,
  `tests/test_openai_operator_edges.py` **108**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`. The adapter's `External I/O` line
  names the Responses API.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- The version bump is the planner's, at merge: do not touch `pyproject.toml` or `uv.lock`.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. Review the diff against the checklist; re-measure (the scope command, the edited tests, the
   planted guards); merge `main` in; PATCH bump, `uv lock`; Windows `make ci`; push;
   **`make gate-ran` from `../ta-s263`**, the printed SHA checked against `git rev-parse HEAD`;
   CodeQL set-diff against `main`'s open alerts; fast-forward `main`; tag.
2. **F1a, at no cost, from the main checkout on the merged code:** the six captured Responses
   replies replayed through the real SDK give back what the paid calls returned and the request sent
   equals the captured one (`wq121_replay_wire.py`, outside the repository); and with the operator's
   `.env` as it stands and the provider set to `openai` for the process, the binding returns
   disconnected with the reason line.
3. **F1b, paid, about $0.30 and at most $0.58** (three calls capped at 4,096 output tokens, two of
   them on the 21,000-token explain prompt): S262's driver, unchanged, one `explain` and one
   `interpret` through the dashboard binding on `gpt-5.5`. Neither refused, neither cut; output
   tokens read against 4,096; `cached_tokens` read on the second explain call.
4. On pass: the operator's `.env` gets `OPERATOR_LLM_PROVIDER=openai` and loses `OPERATOR_MODEL`, on
   the operator's word, and the dashboard is restarted.
5. No deploy. **Not proven by any of these:** a reply cut off by the vendor; the return to Anthropic
   (its account is empty until 2026-10-11).

---

## Handover — paste this to Codex

```text
Sprint 263 — the operator's chat makes its tool call on OpenAI, with the effort and the model its
declared vendor accepts.
Spec: docs/sprints/sprint-263-the-operators-chat-makes-its-tool-call-on-openai.md (read ALL of it,
then CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s263, on branch
sprint-263-the-operators-chat-makes-its-tool-call-on-openai, cut from main, with its venv synced to
the lock. It holds one untracked file the planner put there:
tests/fixtures/openai_responses_forced_function.json (a request and reply captured from the vendor);
commit it unchanged. Work only in that worktree, never in the main checkout and never on main. You
have no .env and no network: every proof is a unit test. `uv run` is safe; never run a bare
`uv sync`. Do not touch pyproject.toml or uv.lock, and say so: the planner bumps the version at
merge. Do not push and do not merge: commit on the branch and hand back. Do not edit docs/STATE.md,
docs/work-queue.md or docs/design-log.md (one exception: an amendment under DL-284 if the build
forces a decision). If a make ci step cannot run in your sandbox (the dependency audit needs the
network), do not bypass it silently: name the step as NOT RUN in the handback.

This handover is complete: nobody will send you follow-up messages. Two tiers:
- A wrong line number, count, path, test name or clause number whose intent is plain from the spec's
  Scope and Success factors is NOT a reason to stop: follow the intent, record the correction in
  Return notes, continue. The same holds if a gate wants the law's CAP block or a rollup line worded
  differently from the spec: do what the gate accepts and say so.
- STOP and report, without improvising, when: the build needs a change to kernel/llm_factory.py's
  build_llm, to kernel/llm_openai.py beyond deleting its last two alias lines, to
  kernel/llm_anthropic*.py, to anything under agents/deliberator/ other than the rider (one added
  test line and its stale comment), or to any file under agents/scanner/, agents/analyst/, agents/portfolio_manager/,
  agents/provider/domain/, contracts/, agents/execution/order_tolerance.py,
  orchestration/history_window.py, orchestration/packs/trading_tunables.json or
  orchestration/packs/trading_issuer_map.json; an existing test other than those the spec names has
  to be edited; a law you read contradicts the spec; or a decision D1-D9 cannot be built as written.

What and why: the operator's dashboard chat asks a model for one forced function call. S262 gave it
an OpenAI adapter on the Chat Completions API, decided without a call to the vendor. gpt-5.5 refuses
it twice: the default effort "max" is not a value that model takes, and that endpoint takes no
function tool together with a reasoning effort. The planner then measured the vendor (nine calls):
the Responses API accepts the forced function at every effort the model lists, only "xhigh" makes
it reason, and the largest real prompt used 811 of the 4,096 output tokens. The operator's .env also
names an Anthropic model, which would be sent to OpenAI as is. You rewrite the adapter for the
Responses API, make the effort resolve from the provider as the model already does, and refuse a
model that belongs to the other vendor. You unit-test all of it. You call no vendor.

MUST RULE before any code: read, whole, agents/operator/laws/laws.md and surfaces/laws/laws.md (each
with its test-plan.md), agents/deliberator/laws/laws.md (read only), docs/laws/conventions.md,
docs/laws/drift-register.md, tests/test_llm_adapter_ownership.py, tests/test_llm_adapter_security.py,
and DL-284 and DL-282 (amendment 2) in docs/design-log.md. Fill the Law reading record first.
Law-cycle answer: YES for operator (OPR-DEP-01 reworded, the PARAM effort row, the CAP line) and for
surfaces (SRF-DEP-03 reworded); NO contracts/ file changes; no clause ID is added.

Order (the spec's Steps): laws -> plant A1, A3, B1, B3 and C1, watch them fail, paste the red ->
implement Scope 1, 2, 3 -> .env.example, the rider, the fixture -> the two law cycles -> break and
restore every guard -> make ci to a file.

Build (decisions D1-D9 are made; build them as written):
1. kernel/llm_openai_operator.py on responses.create, exactly the eight arguments of D1; the
   Appendix holds the measured prototype. Delete the two aliases at the foot of kernel/llm_openai.py.
2. kernel/llm_factory.py: DEFAULT_OPERATOR_EFFORT, default_operator_effort_for, MODEL_PREFIXES,
   model_provider, ModelProviderMismatchError, the check at the top of build_operator_llm.
3. agents/operator/settings.py: effort default "", the wider Literal, resolved_effort.
4. surfaces/dashboard/chat_binding.py: resolved_effort; catch the mismatch, one line to standard
   error, return None.
5. .env.example; the rider (one line and its comment); commit the fixture.
6. The law cycles.

DO NOT: touch build_llm or the debate's client; change agents/deliberator/ beyond the rider;
default the OpenAI effort to anything but "xhigh"; translate an explicit effort; check the effort
against a list; read a finish_reason; drop strict or store from the request; raise the cap or its
bound; give the operator container a real client; stop the dashboard on a mismatched model; let a
test depend on a .env; import a submodule of openai before the package is loaded; pin a version
number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The red output of A1, A3, B1, B3 and C1 pasted, from before the implementation.
 3. Test plan results: one row for each of A1-A8, B1-B4, C1-C2, D1 and E1, with file and status.
 4. Every guard's break-and-restore stated, one line per guard. At least: tool_choice not forced
    (A1); store dropped (A1 or A8); strict dropped (A1 or A8); the effort not sent (A1); the first
    output item taken instead of the function call (A2); cached tokens not subtracted (A2); the
    cut-off raise removed (A3); the usage set after the raise (A3); the refusal for non-object
    arguments (A4); resolved_effort replaced by effort in the binding (C2); the OpenAI default
    changed to "high" (B1); the mismatch check removed (B3, C1); the standard-error line removed
    (C1); test D1's outcome assertion, shown red on a fake SDK without `responses`.
 5. This prints nothing, and you say so (run it against the commit the branch was cut from if main
    has moved; name which you used):
    git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration/history_window.py orchestration/packs kernel/llm_anthropic.py kernel/llm_anthropic_responses.py agents/deliberator/settings.py agents/deliberator/agent.py pyproject.toml uv.lock docs/STATE.md docs/work-queue.md
 6. `git diff main -- kernel/llm_openai.py agents/deliberator` pasted whole: two deleted alias lines
    (with their blank line) and the rider's test edit, nothing else. And
    `git diff main -- kernel/llm_factory.py` pasted whole: build_llm's body untouched.
 7. Every EXISTING test you edited, named, with the reason. The expected answer: the five functions
    of the spec's Measured table, test_b6 (D1), test_effort_accepts_every_rung_of_the_api_ladder if
    you add `none` to it, and the rider.
 8. `sha256sum tests/fixtures/openai_responses_forced_function.json`, which must read
    fd6c917a973db0d54e3eda70d3dc97231f6ccb7b2b9ce62200d6cbd6b8a735a8.
 9. The two law books' old and new versions, the reworded clauses quoted, and the rollup lines
    make ci printed.
10. The parameter step's output (scripts/check_param_law_sync.py), exit code stated.
11. `uv run pytest agents/deliberator/tests/test_llm_openai_adapter.py -q --no-cov` run alone: its
    last line, before the rider and after.
12. make ci output file named, exit code stated, every NOT RUN step named with its reason.
13. Module line counts for every touched or new Python module; Status BUILT here and in the README
    row (the status cell leads with BUILT).
14. One line saying the adapter was NOT RUN against the vendor, and anything in it you are unsure of.
State anything not met as "not done" or "verified failing". Never write a Result for work not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| <element> | <files> | <clause IDs> | <Yes/No + what changed> |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** <Yes/No + what it owed and what was done>

**Contradictions found between a law and this spec:** <none | what, and what you did>

**Laws found silent where a decision was needed:** <none | what, and the drift row filed>

**Clauses that were ⬜ and are now proven:** <IDs, and the rollup in ledger.md + INDEX.md>

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | <name> | <file> | PASS/FAIL | <clause IDs> |

**Tests added beyond the plan:** <none | what and why>

---

## Closeout — evidence

**Status:** <BUILT | MERGED>

**Tree the proofs ran in (and `.env` present?):** <path, branch, .env yes/no>

**Result:** <what is now true, in the artefact's own words — not the intent restated>

**Files changed:** <list>

**Design decisions:** recorded as [`DL-284`](../design-log.md) — <one line on any amendment, or "built as written">

**Proof — the red run first:**

```text
<the failing test output, before the implementation>
```

**Proof — the green run:**

```text
<the passing output>
```

**Guards planted:** <per guard: what was planted, that it failed, that it was restored>

**Module line counts:** <file **n**, file **n**>

**`make ci`:** redirected to `<path>`. Exit code <n>. `<N passed, M skipped>`, coverage `<100.00 %>`.
dependency audit `<result>`. detect-secrets `<result>`.

**`make gate-ran`:** run from `<worktree path>` at `<full 40-char SHA>`:

```text
GATE PROVEN for <sha>:
  Security Findings: success
  CI: success
```

**Not met / verified failing:** <plainly, or "none">

---

## Return notes

- <Scope held / where it moved and why.>
- <What you disagreed with in the spec after reading the laws.>
- <What the next sprint should know that is not obvious from the diff.>

---

## Appendix — the planner's prototype and the captured reply

### The adapter, as measured

This is the body the six captured replies were replayed through. It is a prototype: write your own,
but any difference in the request it sends is a decision, and D1 has made that one.

```python
_CUT_OFF = "max_output_tokens"


class OperatorOpenAILLMClient:
    """OpenAI function-calling implementation of the operator LLM port."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "gpt-5.5",
        max_tokens: int = 4096,
        effort: str = "xhigh",
    ) -> None:
        """Fail early without credentials or the optional vendor SDK."""
        ...  # unchanged from today, apart from the default effort

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Force one named function, recording usage even for a cut-off reply."""
        name = "parse_intent" if tool_schema else "answer_question"
        self.last_usage = None
        self.last_stop_reason = STOP_REASON_UNKNOWN
        response = self._client.responses.create(
            model=self.model,
            max_output_tokens=self.max_tokens,
            reasoning={"effort": self.effort},
            instructions=system,
            input=user,
            tools=[
                {
                    "type": "function",
                    "name": name,
                    "description": "Parse one operator command."
                    if tool_schema
                    else "Return one evidence-grounded answer.",
                    "parameters": tool_schema or _ANSWER_SCHEMA,
                    "strict": False,
                }
            ],
            tool_choice={"type": "function", "name": name},
            store=False,
        )
        self.last_stop_reason = response_stop_reason(response)
        self.last_usage = response_usage(response)
        if self.last_stop_reason == _CUT_OFF:
            raise LLMCompletionStoppedError(provider="openai", stop_reason=_CUT_OFF)
        data = _arguments(response)
        return json.dumps(data) if tool_schema else str(data.get("answer", ""))


def response_stop_reason(response: object) -> str:
    """The vendor's own word: the incomplete reason when there is one, else the status."""
    details = getattr(response, "incomplete_details", None)
    reason = str(getattr(details, "reason", "") or "").strip()
    status = str(getattr(response, "status", "") or "").strip()
    return reason or status or STOP_REASON_UNKNOWN


def response_usage(response: object) -> LLMUsage | None:
    """Read Responses usage, separating cached input from billable input."""
    input_tokens = usage_count(response, "usage.input_tokens")
    cached = usage_count(response, "usage.input_tokens_details.cached_tokens")
    return llm_usage_or_none(
        tokens_in=max(0, input_tokens - cached),
        tokens_out=usage_count(response, "usage.output_tokens"),
        cache_read_tokens=min(cached, input_tokens),
    )


def _arguments(response: object) -> dict[str, object]:
    for item in getattr(response, "output", None) or ():
        if getattr(item, "type", "") != "function_call":
            continue
        try:
            data = json.loads(getattr(item, "arguments", ""))
        except (TypeError, ValueError):
            return dict(_REFUSAL)
        return dict(data) if isinstance(data, dict) else dict(_REFUSAL)
    return dict(_REFUSAL)
```

### The factory's check, as measured

```python
def model_provider(model: str) -> str | None:
    """Return the provider whose model family this name starts with, if any."""
    for provider, prefixes in MODEL_PREFIXES.items():
        if model.startswith(prefixes):
            return provider
    return None


# at the top of build_operator_llm:
    owner = model_provider(model)
    if provider in KEY_ENV and owner not in (None, provider):
        raise ModelProviderMismatchError(
            f"model {model!r} belongs to {owner}; the declared llm_provider is "
            f"{provider}. Unset the model to use the provider's default."
        )
```

Run offline on the prototype: `claude-opus-5`, `gpt-5.5`, `o3` and `chatgpt-latest` are placed;
`ft:gpt-5.5:acme`, `my-local-model` and the empty string are not; `("openai", "claude-opus-5")` and
`("anthropic", "gpt-5.5")` raise the mismatch; `("opnai", "claude-opus-5")` raises
`UnknownProviderError`; the binding with the provider `openai` and the model `claude-opus-5` returns
`None` and writes `dashboard: operator chat not connected: model 'claude-opus-5' belongs to
anthropic; the declared llm_provider is openai. Unset the model to use the provider's default.`

### The fixture

`tests/fixtures/openai_responses_forced_function.json` (8,664 bytes, sha256 `fd6c917a…a735a8`, the
full value is in the handback checklist) holds, for the interpret turn at `xhigh` captured
2026-10-09 09:49 UTC: `system`, `user` and `tool_schema` (what the adapter was called with),
`effort` and `max_tokens`, `request` (the body the SDK put on the wire), `reply` (the vendor's body)
and `returned` (the arguments the adapter gave back). It was edited by hand in three places only:
the response id, the two output item ids and the call id are replaced, and the reasoning item's
`encrypted_content` is cut to a placeholder. The reply's `output`:

```text
[
  {"id": "rs_fixture", "type": "reasoning", "content": [], "encrypted_content": "opaque-placeholder", "summary": []},
  {"id": "fc_fixture", "type": "function_call", "status": "completed",
   "arguments": "{\"outcome\":\"intent\",\"family\":\"explain\",\"parameters\":{...}}",
   "call_id": "call_fixture", "name": "parse_intent"}
]
```

and its `usage`:

```text
{"input_tokens": 286, "input_tokens_details": {"cache_write_tokens": 0, "cached_tokens": 0},
 "output_tokens": 187, "output_tokens_details": {"reasoning_tokens": 121}, "total_tokens": 473}
```
