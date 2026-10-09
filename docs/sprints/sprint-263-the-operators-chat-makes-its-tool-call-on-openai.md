<!-- Agent: planning | Role: sprint handover -->
# Sprint 263 — the operator's chat makes its tool call on OpenAI, with the effort and the model its declared vendor accepts

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-263-the-operators-chat-makes-its-tool-call-on-openai`
**Status:** MERGED 2026-10-09 — `0.125.01`, fast-forwarded to `9df7dacd`, tag `v0.125.01`, GATE PROVEN `9df7dacd` (CI, CodeQL, Security Findings); no deploy; F1a and F1b passed; 🔴 found by F1b and not caused by this sprint: the operator's ledger row carries no stop reason and drops a cut-off call's tokens (work-queue 124)
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

- [x] With the provider `openai` and no model or effort set, the binding builds the OpenAI operator
      client with `gpt-5.5` and `xhigh` (C2), and its call is the request captured from the vendor (A8).
- [x] A reply cut at the cap raises after its tokens are recorded (A3); an unusable reply is the
      refusal (A4).
- [x] An explicit model of the other vendor's family builds nothing and leaves the chat disconnected
      with the reason on standard error (B3, C1).
- [x] On Anthropic the resolved model and effort are what they were: `claude-opus-5`, `max` (B1, C2).
- [x] `build_llm`, `OpenAILLMClient` and its helpers, `kernel/llm_anthropic*.py` and
      `agents/deliberator/` are unchanged apart from the two deleted alias lines and the rider;
      the command in the handback checklist prints nothing.
- [x] Both law cycles done: `OPR-DEP-01` and `SRF-DEP-03` reworded and re-proven, the `effort` row
      and the `CAP` line, changelogs, versions, test-plan rows, both rollups.
- [x] `scripts/check_param_law_sync.py` exits 0.
- [x] Every guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module under 200 lines.
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
| Responses operator adapter | `agents/operator/laws/laws.md` and `test-plan.md` (whole); `tests/test_llm_adapter_ownership.py` and `tests/test_llm_adapter_security.py` (whole) | OPR-DEP-01, OPR-NEV-05, OPR-FAIL-01/02, OPR-STA-03, OPR-PERF-01/03, OPR-SEC-01 | No: D1-D4 preserve the tool boundary, refusal and accounting; PERF-01/03 are gray and remain gray unless their whole guarantees are proven. |
| Factory and operator settings | Same operator book and test plan, adapter ownership/security tests | OPR-DEP-01; PARAM effort and CAP | No: D5-D6 require the authorized operator amendment; `build_llm` stays unchanged. |
| Dashboard chat binding | `surfaces/laws/laws.md` and `test-plan.md` (whole) | SRF-DEP-02/03 | No: a mismatch disconnects chat with one stderr reason and leaves the dashboard useful. |
| Deleted aliases and isolated-test rider | `agents/deliberator/laws/laws.md` (whole, read only) | DLIB-DEP-03, DLIB-FAIL-04, DLIB-OBS-05/06 | No: only the two aliases, their separating blank line, and D9's test line/comment may change. |
| Law-cycle procedure | `docs/laws/conventions.md` and `drift-register.md` (whole); DL-284 and DL-282 amendment 2 | conventions sections 3, 4, 7, 7a, 9; LAW-02/06 | No: decisions already recorded; no new decision or drift found. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No contracts changes; YES operator and surfaces amendments, no new clause IDs. Owed: OPR-DEP-01, PARAM effort/CAP, SRF-DEP-03, versions/changelogs, test-plan rows and both rollups. Both cycles subsequently completed and re-proven; the record itself was filled before code.

**Contradictions found between a law and this spec:** None outside the explicitly authorized amendments. The operator's existing Anthropic constructor proof remains valid for that selected vendor.

**Laws found silent where a decision was needed:** None beyond D1-D9 and the two amendments already authorized by DL-284.

**Clauses that were ⬜ and are now proven:** None: existing OPR-DEP-01 and SRF-DEP-03 remain green after their amendments. OPR-PERF-01/03 and OPR-STA-01 are gray; this sprint does not claim their whole guarantees. Gate-derived counts remain operator 19 / 50 and surfaces 30 / 37 in both rollups.

**Pre-code baseline:** `C:\Users\yury_\Downloads\project\ta-s263`, branch `sprint-263-the-operators-chat-makes-its-tool-call-on-openai`, HEAD/main/origin-main `02dd0d49fc51bae7a6bdeff5ea0d4de624e12c97`. Only the supplied fixture is untracked; its SHA256 matches `fd6c917a973db0d54e3eda70d3dc97231f6ccb7b2b9ce62200d6cbd6b8a735a8`. `.env` absent. All proofs will be offline. The binding handover excludes tracker edits, version/lock edits, push, merge and vendor calls. CLAUDE.md's 15-step CI target overrides AGENTS.md's stale 14-step count; disagreement recorded, neither rule file edited. Law reading recorded before any Python or configuration change.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_measured_request` | `tests/test_operator_responses.py` | PASS | OPR-DEP-01 / OPR-NEV-05 |
| A2 | `test_a2_function_call_and_usage` | `tests/test_operator_responses.py` | PASS | OPR-STA-03 |
| A3 | `test_a3_cutoff_records_before_raise` | `tests/test_operator_responses.py` | PASS | OPR-FAIL-01 / OPR-STA-03 |
| A4 | `test_a4_unusable_output_is_refused` | `tests/test_operator_responses_edges.py` | PASS | OPR-NEV-05 / OPR-FAIL-02 |
| A5 | `test_a5_filtered_reply_is_refused` | `tests/test_operator_responses_edges.py` | PASS | OPR-FAIL-02 / OPR-STA-03 |
| A6 | `test_transport_failure_clears_old_accounting` | `tests/test_openai_operator_edges.py` | PASS | OPR-STA-03 / OPR-FAIL-01 |
| A7 | `test_optional_sdk_is_lazy_and_missing_key_refuses` | `tests/test_openai_operator_edges.py` | PASS | OPR-SEC-01 / OPR-DEP-01 |
| A8 | `test_a8_captured_wire_replay` | `tests/test_operator_responses_wire.py` | PASS | OPR-DEP-01 / OPR-STA-03 |
| B1 | `test_b1_effort_follows_provider` | `tests/test_operator_provider_guards.py` | PASS | OPR-DEP-01 |
| B2 | `test_b2_unknown_provider_effort` | `tests/test_operator_provider_guards.py` | PASS | OPR-DEP-01 |
| B3 | `test_b3_mismatched_model_builds_nothing` | `tests/test_operator_provider_guards.py` | PASS | OPR-DEP-01 |
| B4 | `test_b4_unknown_model_family_is_vendors_to_judge` | `tests/test_operator_provider_guards.py` | PASS | OPR-DEP-01 |
| C1 | `test_c1_mismatch_disconnects_with_reason` | `surfaces/tests/test_chat_model_mismatch.py` | PASS | SRF-DEP-03 |
| C2 | `test_c2_binding_passes_resolved_settings` | `surfaces/tests/test_chat_model_mismatch.py` | PASS | SRF-DEP-03 / OPR-DEP-01 |
| D1 | `test_b6_openai_key_never_escapes_operator` | `tests/test_openai_operator_security.py` | PASS | OPR-SEC-01 / OPR-DEP-01 |
| E1 | `test_our_effort_values_are_all_valid_openai_values` | `agents/deliberator/tests/test_llm_openai_adapter.py` | PASS | DL-105 (existing rider docstring unchanged) |

**Tests added beyond the plan:** `test_model_family_prefixes` pins all five OpenAI prefixes and the Anthropic prefix plus unclassified names; `test_missing_arguments_and_output` covers absent SDK fields. A2 also checks cache overflow clamping, ignored cache-write tokens, the adapter default and first-of-two function calls. All prove D1-D6 without expanding production scope.

---

## Closeout — evidence

**Status:** MERGED

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s263`, branch `sprint-263-the-operators-chat-makes-its-tool-call-on-openai`; `.env` absent; `UV_OFFLINE=1`, `UV_FROZEN=1`, no vendor call.

**Result:** Full unit suite: 4,558 passed, 8 skipped, 100.00 % coverage; focused unit suite after fixture annotations: 66 passed; isolated rider: 4 passed after reproducing 1 failed / 3 passed before. The real SDK mock-transport request equals the captured body at `/v1/responses`. All 25 implementation guards fail when broken and pass after byte-for-byte restoration; both law-citation plants fail and restore. PARAM, law coverage and both secret checks exit 0. Overall `make ci` is verified failing (exit 2): the dependency audit cannot query PyPI offline and is NOT RUN online.

**Files changed:**

- `.env.example`
- `agents/deliberator/tests/test_llm_openai_adapter.py`
- `agents/operator/laws/laws.md`
- `agents/operator/laws/test-plan.md`
- `agents/operator/settings.py`
- `agents/operator/tests/test_operator_settings.py`
- `docs/laws/INDEX.md`
- `docs/laws/ledger.md`
- `docs/sprints/README.md`
- `docs/sprints/sprint-263-the-operators-chat-makes-its-tool-call-on-openai.md`
- `kernel/llm_factory.py`
- `kernel/llm_openai.py`
- `kernel/llm_openai_operator.py`
- `surfaces/dashboard/chat_binding.py`
- `surfaces/laws/laws.md`
- `surfaces/laws/test-plan.md`
- `surfaces/tests/test_chat_model_mismatch.py`
- `tests/fixtures/openai_responses_forced_function.json`
- `tests/test_openai_operator.py`
- `tests/test_openai_operator_edges.py`
- `tests/test_openai_operator_security.py`
- `tests/test_operator_provider_guards.py`
- `tests/test_operator_responses.py`
- `tests/test_operator_responses_edges.py`
- `tests/test_operator_responses_wire.py`

**Design decisions:** recorded as [`DL-284`](../design-log.md) — built as written; no amendment required.

**Proof — the red run first:**

```text
uv run pytest tests/test_operator_responses.py::test_a1_measured_request tests/test_operator_responses.py::test_a3_cutoff_records_before_raise tests/test_operator_provider_guards.py::test_b1_effort_follows_provider tests/test_operator_provider_guards.py::test_b3_mismatched_model_builds_nothing surfaces/tests/test_chat_model_mismatch.py::test_c1_mismatch_disconnects_with_reason -q --no-cov
FFFFFFF                                                                  [100%]
================================== FAILURES ===================================
__________________________ test_a1_measured_request ___________________________
tests\test_operator_responses.py:71: in test_a1_measured_request
    client.complete(system="system", user="user", tool_schema=supplied)
kernel\llm_openai_operator.py:64: in complete
    response = self._client.chat.completions.create(
               ^^^^^^^^^^^^^^^^^
E   AttributeError: 'types.SimpleNamespace' object has no attribute 'chat'
_____________________ test_a3_cutoff_records_before_raise _____________________
tests\test_operator_responses.py:127: in test_a3_cutoff_records_before_raise
    client.complete(system="s", user="u", tool_schema={})
kernel\llm_openai_operator.py:64: in complete
    response = self._client.chat.completions.create(
               ^^^^^^^^^^^^^^^^^
E   AttributeError: 'types.SimpleNamespace' object has no attribute 'chat'
_______________ test_b1_effort_follows_provider[anthropic-max] ________________
tests\test_operator_provider_guards.py:26: in test_b1_effort_follows_provider
    assert settings.effort == ""
E   AssertionError: assert 'max' == ''
E
E     + max
________________ test_b1_effort_follows_provider[openai-xhigh] ________________
tests\test_operator_provider_guards.py:26: in test_b1_effort_follows_provider
    assert settings.effort == ""
E   AssertionError: assert 'max' == ''
E
E     + max
___ test_b3_mismatched_model_builds_nothing[openai-claude-opus-5-anthropic] ___
tests\test_operator_provider_guards.py:57: in test_b3_mismatched_model_builds_nothing
    with pytest.raises(llm_factory.ModelProviderMismatchError) as error:
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: module 'kernel.llm_factory' has no attribute 'ModelProviderMismatchError'
______ test_b3_mismatched_model_builds_nothing[anthropic-gpt-5.5-openai] ______
tests\test_operator_provider_guards.py:57: in test_b3_mismatched_model_builds_nothing
    with pytest.raises(llm_factory.ModelProviderMismatchError) as error:
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: module 'kernel.llm_factory' has no attribute 'ModelProviderMismatchError'
__________________ test_c1_mismatch_disconnects_with_reason ___________________
surfaces\tests\test_chat_model_mismatch.py:36: in test_c1_mismatch_disconnects_with_reason
    assert result is None
E   AssertionError: assert {'graph': <kernel.graph_memory.InMemoryGraphStore object at 0x0000022EBA41E510>, 'llm': <kernel.llm_openai_operator.OperatorOpenAILLMClient object at 0x0000022EBA469810>} is None
=========================== short test summary info ===========================
FAILED tests/test_operator_responses.py::test_a1_measured_request - Attribute...
FAILED tests/test_operator_responses.py::test_a3_cutoff_records_before_raise
FAILED tests/test_operator_provider_guards.py::test_b1_effort_follows_provider[anthropic-max]
FAILED tests/test_operator_provider_guards.py::test_b1_effort_follows_provider[openai-xhigh]
FAILED tests/test_operator_provider_guards.py::test_b3_mismatched_model_builds_nothing[openai-claude-opus-5-anthropic]
FAILED tests/test_operator_provider_guards.py::test_b3_mismatched_model_builds_nothing[anthropic-gpt-5.5-openai]
FAILED surfaces/tests/test_chat_model_mismatch.py::test_c1_mismatch_disconnects_with_reason
7 failed in 2.21s
EXIT=1
```

**Proof — the green run:**

```text
....................................................................     [100%]
68 passed in 9.09s
EXIT=0

Isolated rider after D9:
....                                                                     [100%]
4 passed in 3.54s
EXIT=0
```

**Guards planted — actual break/restore output:**

```text
tool_choice not forced: RED exit 1 (1 failed in 1.26s); RESTORED exit 0 (1 passed in 1.03s)
store dropped: RED exit 1 (2 failed in 4.68s); RESTORED exit 0 (2 passed in 4.06s)
strict dropped: RED exit 1 (2 failed in 4.60s); RESTORED exit 0 (2 passed in 4.03s)
effort not sent: RED exit 1 (1 failed in 1.23s); RESTORED exit 0 (1 passed in 1.01s)
first output item used instead of function call: RED exit 1 (2 failed in 1.25s); RESTORED exit 0 (2 passed in 1.03s)
cached tokens not subtracted: RED exit 1 (2 failed in 1.54s); RESTORED exit 0 (2 passed in 1.09s)
cutoff raise removed: RED exit 1 (1 failed in 1.35s); RESTORED exit 0 (1 passed in 1.18s)
usage assigned after cutoff raise: RED exit 1 (1 failed in 1.25s); RESTORED exit 0 (1 passed in 1.05s)
non-object arguments accepted: RED exit 1 (1 failed, 5 passed in 1.29s); RESTORED exit 0 (6 passed in 1.06s)
binding passes unresolved effort: RED exit 1 (2 failed in 1.86s); RESTORED exit 0 (2 passed in 1.54s)
OpenAI provider default changed to high: RED exit 1 (1 failed, 1 passed in 1.29s); RESTORED exit 0 (2 passed in 1.09s)
mismatch check removed: RED exit 1 (3 failed in 2.04s); RESTORED exit 0 (3 passed in 1.73s)
stderr reason removed: RED exit 1 (1 failed in 1.83s); RESTORED exit 0 (1 passed in 1.56s)
D1 fake SDK lacks responses: RED exit 1 (1 failed in 1.37s); RESTORED exit 0 (1 passed in 1.09s)
adapter default changed to high: RED exit 1 (2 failed in 1.30s); RESTORED exit 0 (2 passed in 1.02s)
cached input not clamped: RED exit 1 (1 failed, 1 passed in 1.26s); RESTORED exit 0 (2 passed in 1.02s)
cache writes counted: RED exit 1 (2 failed in 1.25s); RESTORED exit 0 (2 passed in 1.01s)
```

```text
agents/operator/laws/test-plan.md: RED exit 1
[FAIL] agents/operator/laws/test-plan.md:46: OPR-DEP-01 green row cites no live test: test_s263_intentionally_missing_guard (test function does not exist)
RESTORED exit 0
surfaces/laws/test-plan.md: RED exit 1
[FAIL] ta-s263/surfaces/laws/test-plan.md:39: SRF-DEP-03 green row cites no live test: test_s263_intentionally_missing_guard (test function does not exist)
RESTORED exit 0
```

PARAM was also proven red after the code default changed and green after its authorized law-row amendment:

```text
[FAIL] agents/operator/laws/laws.md:190: operator.effort law Value '`"max"`' differs from code default ''
[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 — UCITS investment powers and limits
[WARN] portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later
EXIT=1
[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 — UCITS investment powers and limits
[WARN] portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later
EXIT=0
```

The D1 plant keeps the new `result.outcome == "intent"` assertion and replaces its SDK with one exposing only `chat`; it fails on outcome `refused`, then restores to `intent`. Guard commands and full red/green outputs are saved in `C:\Users\yury_\AppData\Local\Temp\ta-s263-evidence\guards-full.txt`.

**D1 successful-outcome assertion, actual red/restore output:**

```text
D1 fake SDK lacks responses
COMMAND: ['uv', 'run', 'pytest', 'tests/test_openai_operator_security.py::test_b6_openai_key_never_escapes_operator', '-q', '--no-cov']
RED EXIT=1
F                                                                        [100%]
================================== FAILURES ===================================
__________________ test_b6_openai_key_never_escapes_operator __________________
tests\test_openai_operator_security.py:65: in test_b6_openai_key_never_escapes_operator
    assert result.outcome == "intent"
E   AssertionError: assert 'refused' == 'intent'
E
E     - intent
E     + refused
=========================== short test summary info ===========================
FAILED tests/test_openai_operator_security.py::test_b6_openai_key_never_escapes_operator
1 failed in 1.37s

RESTORED EXIT=0
.                                                                        [100%]
1 passed in 1.09s
```

**Eight additional guard plants — actual output:**

```text
B4 unclassified model wrongly refused: RED exit 1 (6 failed in 1.50s); RESTORED exit 0 (6 passed in 1.40s)
B4 unknown provider wrongly becomes mismatch: RED exit 1 (6 failed in 2.62s); RESTORED exit 0 (6 passed in 1.52s)
B1 explicit effort replaced by default: RED exit 1 (2 failed in 1.92s); RESTORED exit 0 (2 passed in 3.66s)
A6 old usage survives transport failure: RED exit 1 (1 failed in 1.86s); RESTORED exit 0 (1 passed in 1.83s)
A6 old stop survives transport failure: RED exit 1 (1 failed in 1.81s); RESTORED exit 0 (1 passed in 1.77s)
A7 missing credential accepted: RED exit 1 (1 failed in 1.97s); RESTORED exit 0 (1 passed in 1.46s)
A5 status hides incomplete reason: RED exit 1 (1 failed in 1.85s); RESTORED exit 0 (1 passed in 1.48s)
A1 explicit adapter effort rewritten: RED exit 1 (1 failed in 1.69s); RESTORED exit 0 (1 passed in 1.41s)
```

Commands and complete red/restored outputs: `C:\Users\yury_\AppData\Local\Temp\ta-s263-evidence\extra-guards-full.txt`. Combined with the 17 above, all 25 implementation guards were restored; no mutation remains.

**Module line counts:**

```text
agents/deliberator/tests/test_llm_openai_adapter.py: 124 lines
agents/operator/settings.py: 74 lines
agents/operator/tests/test_operator_settings.py: 45 lines
kernel/llm_factory.py: 130 lines
kernel/llm_openai.py: 103 lines
kernel/llm_openai_operator.py: 114 lines
surfaces/dashboard/chat_binding.py: 60 lines
surfaces/tests/test_chat_model_mismatch.py: 101 lines
tests/test_openai_operator.py: 77 lines
tests/test_openai_operator_edges.py: 109 lines
tests/test_openai_operator_security.py: 79 lines
tests/test_operator_provider_guards.py: 137 lines
tests/test_operator_responses.py: 153 lines
tests/test_operator_responses_edges.py: 74 lines
tests/test_operator_responses_wire.py: 59 lines
```

**Protected-path proof:** checked against `main`, resolved to `02dd0d49fc51bae7a6bdeff5ea0d4de624e12c97` (the branch-cut base is `02dd0d49fc51bae7a6bdeff5ea0d4de624e12c97`). The following command prints nothing:

```text
git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration/history_window.py orchestration/packs kernel/llm_anthropic.py kernel/llm_anthropic_responses.py agents/deliberator/settings.py agents/deliberator/agent.py pyproject.toml uv.lock docs/STATE.md docs/work-queue.md
<no output>
EXIT=0
build_llm source segment: byte-for-byte unchanged against the branch-cut commit
```

**Whole narrow diffs requested by the checklist:**

```diff
diff --git a/agents/deliberator/tests/test_llm_openai_adapter.py b/agents/deliberator/tests/test_llm_openai_adapter.py
index a62a4c02..785bd5c8 100644
--- a/agents/deliberator/tests/test_llm_openai_adapter.py
+++ b/agents/deliberator/tests/test_llm_openai_adapter.py
@@ -88,10 +88,9 @@ def test_openai_length_without_text_raises_stop_reason() -> None:
         _text(response)


-# Read off `openai` 2.49.0 on 2026-08-11. Pinned rather than imported because
-# `openai` is an optional extra (`llm`) that CI's `uv sync --frozen` does not
-# install — an importorskip here would skip on every CI run, which is decoration
-# rather than a check. The live cross-check below runs wherever the extra exists.
+# Read off `openai` 2.49.0 on 2026-08-11. The SDK is optional (`llm`) and also
+# arrives with DSPy in CI's dev group. The pinned check runs without the SDK;
+# the live cross-check runs wherever it exists.
 _OPENAI_REASONING_EFFORT = frozenset(
     {"none", "minimal", "low", "medium", "high", "xhigh", "max"}
 )
@@ -115,6 +114,7 @@ def test_our_effort_values_are_all_valid_openai_values() -> None:
     )

     try:  # pragma: no cover - only where the optional `llm` extra is installed
+        _ = importlib.import_module("openai").OpenAI  # load DSPy's lazy package first
         module = importlib.import_module("openai.types.shared.reasoning_effort")
     except ModuleNotFoundError:
         return
diff --git a/kernel/llm_openai.py b/kernel/llm_openai.py
index 682a1808..26559ce8 100644
--- a/kernel/llm_openai.py
+++ b/kernel/llm_openai.py
@@ -101,7 +101,3 @@ def _finish_reasons(response: object) -> tuple[str, ...]:
         if reason:
             reasons.append(reason)
     return tuple(reasons)
-
-
-completion_usage = _usage
-completion_stop_reason = _stop_reason
```

```diff
diff --git a/kernel/llm_factory.py b/kernel/llm_factory.py
index b01f5a8a..e6385316 100644
--- a/kernel/llm_factory.py
+++ b/kernel/llm_factory.py
@@ -28,11 +28,22 @@ DEFAULT_MODEL: dict[str, str] = {
     "openai": "gpt-5.5",
 }

+DEFAULT_OPERATOR_EFFORT: dict[str, str] = {"anthropic": "max", "openai": "xhigh"}
+
+MODEL_PREFIXES: dict[str, tuple[str, ...]] = {
+    "anthropic": ("claude-",),
+    "openai": ("gpt-", "chatgpt-", "o1", "o3", "o4"),
+}
+

 class UnknownProviderError(RuntimeError):
     """Raised when configuration names a provider that does not exist."""


+class ModelProviderMismatchError(RuntimeError):
+    """Raised when an explicit model belongs to a different known provider."""
+
+
 def build_llm(
     provider: str,
     *,
@@ -63,6 +74,22 @@ def default_model_for(provider: str) -> str:
         raise UnknownProviderError(f"unknown llm_provider {provider!r}") from exc


+def default_operator_effort_for(provider: str) -> str:
+    """Return the selected provider's default operator reasoning effort."""
+    try:
+        return DEFAULT_OPERATOR_EFFORT[provider]
+    except KeyError as exc:
+        raise UnknownProviderError(f"unknown llm_provider {provider!r}") from exc
+
+
+def model_provider(model: str) -> str | None:
+    """Return the provider whose model family this name starts with, if any."""
+    for provider, prefixes in MODEL_PREFIXES.items():
+        if model.startswith(prefixes):
+            return provider
+    return None
+
+
 def build_operator_llm(
     provider: str,
     *,
@@ -72,6 +99,12 @@ def build_operator_llm(
     effort: str,
 ) -> LLMClient:
     """Construct exactly the selected vendor's operator adapter."""
+    owner = model_provider(model)
+    if provider in KEY_ENV and owner not in (None, provider):
+        raise ModelProviderMismatchError(
+            f"model {model!r} belongs to {owner}; the declared llm_provider is "
+            f"{provider}. Unset the model to use the provider's default."
+        )
     if provider == "anthropic":
         return OperatorAnthropicLLMClient(
             api_key=api_key,
```

**Fixture checksum — actual sha256sum output:**

```text
fd6c917a973db0d54e3eda70d3dc97231f6ccb7b2b9ce62200d6cbd6b8a735a8 *tests/fixtures/openai_responses_forced_function.json
```

**Law amendments:** operator LOCKED v1.5 -> v1.6; surfaces LOCKED v1.4 -> v1.5. Reworded clauses:

> - **OPR-DEP-01** — `DEP-LLM` — the declared LLM provider (or injected FakeLLMClient);
>   sole external call. Provider selection never falls back to another vendor; an empty model
>   and an empty effort resolve that provider's defaults, while explicit values are passed as set.
>   An explicit model whose name belongs to another provider's family is refused before any call.

> - **SRF-DEP-03** — Dashboard chat uses the LLM provider declared in operator settings and no
>   other. A missing key for that provider, an unknown provider, or its adapter's configuration
>   failure, or an explicit model belonging to another provider's family leaves chat disconnected.
>   For a model-family mismatch the dashboard's start-up output names that cause.

**Law gate rollups:** `scripts/check_law_coverage.py` prints no lines on success (exit 0); the `make ci` invocation therefore has no printed rollup lines to quote. Its derived counter function reports:

```text
operator: derived 19 / 50
surfaces: derived 30 / 37
law coverage check: True
```

**Isolated rider, same command before and after:**

```text
uv run pytest agents/deliberator/tests/test_llm_openai_adapter.py -q --no-cov
BEFORE: 1 failed, 3 passed in 4.38s
EXIT=1
AFTER: 4 passed in 3.54s
EXIT=0
```

**C2 guard after the new test's typing repair:** `2 failed in 1.88s`, RED exit 1; `2 passed in 1.56s`, RESTORED exit 0. Full output: `C:\Users\yury_\AppData\Local\Temp\ta-s263-evidence\c2-guard-final.txt`.

**`make ci`:** redirected, never piped, to `C:\Users\yury_\AppData\Local\Temp\ta-s263-evidence\make-ci-final.txt`. Exit code **2**, verified failing at step 13. **4,558 passed, 8 skipped; 100.00 % coverage.** `UV_OFFLINE=1`, `UV_FROZEN=1` and HTTP/HTTPS/ALL proxy `http://127.0.0.1:9` prevent external traffic. The dependency audit is **NOT RUN online** because it requires PyPI. The remaining two required checks were run separately.

| Step | Result and evidence |
| --- | --- |
| 1 ruff | PASS, exit 0; `make ci` continued to step 2 |
| 2 format | PASS, 1,648 files formatted; exit 0 |
| 3 mypy | PASS, 1,173 source files; exit 0 |
| 4 import-linter | PASS, 5 contracts kept / 0 broken; exit 0 |
| 5 module size | PASS, exit 0; all touched Python modules under 200 lines (counts above) |
| 6 module header | PASS, exit 0 |
| 7 law coverage | PASS, exit 0; silent success and derived rollups above |
| 8 PARAM/settings sync | PASS, exit 0; actual output above |
| 9 sprint status | PASS, exit 0 |
| 10 markdown links | PASS, exit 0 |
| 11 version scheme | PASS, exit 0; version and lock left unchanged |
| 12 pytest | PASS, 4,558 passed / 8 skipped, 100.00 % coverage; exit 0 |
| 13 dependency audit | NOT RUN online: no network authorized; offline attempt verified failing on the refused loopback proxy |
| 14 detect-secrets | PASS separately after four dummy-key false positives were annotated; exit 0 |
| 15 untracked secrets | PASS separately; exit 0 |

Actual `make ci` command sequence and selected output (the complete output is retained at the named path):

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
uv run lint-imports
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
uv run python scripts/check_dependency_audit.py

1648 files already formatted
Success: no issues found in 1173 source files
Analyzed 647 files, 2218 dependencies.
Contracts: 5 kept, 0 broken.
TOTAL                                                           20186      0   4272      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 4558 passed, 8 skipped, 2470 warnings in 546.69s (0:09:06) ==========
requests.exceptions.ProxyError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=9): Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it")))
make: *** [Makefile:59: ci] Error 1
MAKE_CI_EXIT=2; dependency audit NOT RUN online (offline proxy refused); remaining required steps run separately
```

Actual separate secret-check commands and output after dummy-key annotations:

```text
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
DETECT_SECRETS_EXIT=0
uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
UNTRACKED_SECRETS_EXIT=0
```

**Final fixture annotations:** The first detect-secrets run exited 1, naming only `fixture-value` dummy keys in four new test files. Specific inline `pragma: allowlist secret` comments were added; `.secrets.baseline` was not edited. AST comparison against the files exercised by full CI proves the executable syntax unchanged; focused tests were rerun after annotation.

```text
tests/test_operator_responses_wire.py: syntax tree unchanged; dummy-key annotations only
tests/test_operator_responses.py: syntax tree unchanged; dummy-key annotations only
tests/test_operator_provider_guards.py: syntax tree unchanged; dummy-key annotations only
surfaces/tests/test_chat_model_mismatch.py: syntax tree unchanged; dummy-key annotations only
tests/test_operator_responses_wire.py: syntax tree unchanged; dummy-key annotations only
tests/test_operator_responses.py: syntax tree unchanged; dummy-key annotations only
tests/test_operator_provider_guards.py: syntax tree unchanged; dummy-key annotations only
surfaces/tests/test_chat_model_mismatch.py: syntax tree unchanged; dummy-key annotations only

..................................................................       [100%]
66 passed in 13.58s
FOCUSED_EXIT=0
```

**New top-level tests checked with mypy independently:**

```text
uv run mypy --explicit-package-bases tests/test_operator_provider_guards.py tests/test_operator_responses.py tests/test_operator_responses_edges.py tests/test_operator_responses_wire.py
pyproject.toml: note: unused section(s): module = ['azure.core', 'azure.identity', 'azure.identity.*', 'azure.keyvault', 'celery.*', 'redis', 'redis.*']
Success: no issues found in 4 source files
EXIT=0
```

**B1 and A1 guards re-proven after their new tests' typing repairs:**

```text
B1 after invalid-env typing repair: RED exit 1 (1 failed, 1 passed in 1.37s); RESTORED exit 0 (2 passed in 1.08s)
A1 after explicit import and schema typing repair: RED exit 1 (1 failed in 1.29s); RESTORED exit 0 (1 passed in 1.03s)
```

**`make gate-ran`:** NOT RUN: the handover prohibits push and merge and requires offline proof. No remote gate, merge, deployment or live proof claimed.

**Not met / verified failing:** Overall `make ci` exit 0 is not met: **verified failing, exit 2**, solely because the dependency audit needs network. Dependency audit **NOT RUN online**. Remote gates, merge, deployment, F1a/F1b and a vendor call by this builder are **not done**, as required by the offline handover; these remain the planner's. No green overall CI claim.

---

## Return notes

- The first detect-secrets attempt identified four dummy-key false positives in new tests. Only inline fixture annotations were added; the executable syntax trees match the full-CI files and the scan now passes. No secret or baseline update entered the worktree. The prior typing-failed CI log is retained at `C:\Users\yury_\AppData\Local\Temp\ta-s263-evidence\make-ci-typing-red.txt`; corrected new tests pass mypy and full unit coverage.
- Scope held; `pyproject.toml`, `uv.lock`, the trackers, packs, contracts and all excluded decision paths are unchanged. The planner owns the PATCH bump and remote gate at merge. No push or merge performed.
- No law/spec contradiction outside the two named amendments and no new design decision. AGENTS.md says 14 CI steps; CLAUDE.md and the actual `ci:` target say 15. Neither rule file changed.
- The law-coverage checker is silent on success, so `make ci` cannot print the requested rollup lines. Its own `_derived_counter` was read directly: operator 19 / 50, surfaces 30 / 37; both rollups agree and the gate exits 0. No count was invented or changed.
- The rider assigns the package's `OpenAI` attribute to `_` so the package loads first without ruff B018. Its comment is corrected and every assertion is unchanged. The binding uses `sys.stderr.write` for the required single reason line, satisfying ruff T201.
- Existing tests edited: `test_b2_operator_forces_one_named_function` (Responses wire/reply); `test_b3_unusable_tool_reply_is_refused` (Responses output, with its shared `_sdk` helper); `test_b3_length_raises_after_recording_usage` (vendor word `max_output_tokens`); `test_transport_failure_clears_old_accounting` (a real prior fake call before the transport failure); `test_effort_defaults_to_max`, renamed `test_effort_defaults_to_empty` (new default and provider resolution); `test_b6_openai_key_never_escapes_operator` (Responses fake and successful-outcome assertion); `test_our_effort_values_are_all_valid_openai_values` (D9 rider only). No other existing test function was edited; `test_effort_accepts_every_rung_of_the_api_ladder` is unchanged because B1 already covers `none` on both vendors.
- Adapter NOT RUN against the vendor. Cached input being part of total input and cutoff metadata remain planner assumptions based on SDK types; real non-zero cache hits and a vendor-produced cutoff remain unproved. `cache_write_tokens` is deliberately ignored under D4. F1a/F1b, return-to-Anthropic proof and the dashboard restart remain the planner's.

---

## Planner's review at the merge — 2026-10-09

Re-measured by the planner in `../ta-s263`, not taken from the handback.

- **Scope.** The checklist's scope command against `main` (`02dd0d49`, which has not moved) prints
  nothing: no fidelity decision path, no pack, no tracker, no version file. The body of `build_llm`
  is byte for byte the one on `main`. `kernel/llm_openai.py` lost its two alias lines and the blank
  lines above them, nothing else. Under `agents/deliberator/` one file changed, the rider's test: one
  added line and its comment. Every changed file is LF in the commit, and the fixture's hash is the
  one the planner left in the worktree.
- **The code is the measured prototype.** The built adapter differs from it only in importing
  `LLMUsage` at run time. The factory's check, the settings' property and the binding's refusal are
  the prototype's lines.
- **Existing tests.** Seven existing test functions were edited, each named in Return notes and each
  as the spec asked: five that pinned the old endpoint or the old default, the security test (which
  now asserts the outcome is `intent`), and the rider.
- **Guards.** 43 things broken one at a time, each restored and the tree left clean: **43 went red,
  no gap.** They cover the fourteen of the checklist and more: the request (the forced choice,
  `strict`, `store`, the effort, the cap, the two texts swapped, the description), the reply (the
  first item taken whatever its type, the cut-off raise, the usage or the stop reason set after it,
  the incomplete reason or the status ignored, the three refusals), the usage (cached not
  subtracted, the cache read not clamped), the defaults (`high` on OpenAI, `xhigh` on Anthropic, the
  adapter's own default, an unknown provider given one), the family check (removed, raised for an
  unknown provider, an unknown family refused, a prefix dropped, the message without the model), the
  settings (`none` not accepted, the default back at `max`, the resolved value ignoring either
  side), the binding (the raw effort passed, the reason line removed, the error not caught, a
  mismatch that still binds) and the rider's line. Checked each against one named test as well: the
  security test goes red by itself when the adapter is put back on the old endpoint, and the
  real-SDK test goes red by itself when `strict`, `store` or the effort leaves the request.
- **The vendor's replies on the built code.** The six accepted replies captured on 2026-10-09,
  replayed through the real SDK on a fake transport into the built adapter, in a process where DSPy
  had registered its lazy `openai` module first: each gives back what the paid call returned, with
  the same stop reason and usage, and the request sent equals the request captured on the wire. A
  captured reply cut by hand raises after 4,096 output tokens are recorded.
- **Two changes made by the planner on the branch:**
  1. *The wire test found its fixture by a path relative to the current directory.* It now reads
     from the test file's own directory, as the other fixture readers under `tests/` do. Measured:
     it passes with pytest started from another directory.
  2. *`docs/laws/INDEX.md`* named the previous sprint beside the two new law versions.
- **Seen and accepted.** `.env.example` names the three operator variables in a comment and sets
  none. The handback's `make ci` stopped at the dependency audit, which needs the network the
  builder does not have; the planner's Windows run is the proof.
- **Version.** PATCH, `0.125.00` to `0.125.01`; `uv lock` changed the version line alone (180
  packages).

**The gate and the merge.** Windows `make ci` exit 0 on the branch: all 15 steps, 4,558 passed, 8
skipped, 100.00 % coverage, and the dependency audit the builder could not run found nothing
unaccepted. `GATE PROVEN` for `9df7dacd28b08a5700e6147414e45c01935806a6`, run from `../ta-s263`, the
printed SHA equal to its `HEAD`: CI, CodeQL and Security Findings each `success`. Open CodeQL alerts
on the branch: 127, the same alert numbers as on the last merged branch and on `main`, none at error
level. `main` fast-forwarded to that commit and tagged `v0.125.01`.

**After the merge, 2026-10-09 ([functionality checks](../laws/functionality-checks.md)).** *F1a passed*
on the merged `main`, at no cost: the six captured replies replay as before; with the operator's `.env`
as it stands the binding returns disconnected with the reason line, and it binds `gpt-5.5` at `xhigh`
once the model is emptied for the process. *F1b passed* (the operator: *"you have my ok for $.0.58"*):
one `explain` and one `interpret` through the dashboard binding on `gpt-5.5`, three vendor calls for
$0.27. Both turns answered, none was cut; 797, 233 and 716 output tokens of 4,096; 12.2 and 13.8
seconds a turn. 🔴 *Found by F1b, not caused by this sprint:* each of the three ledger rows reads
`stop_reason: unknown`. The operator agent never passes its client's stop reason to the ledger, and on
a cut-off it never reads the usage the adapter recorded before raising: measured offline on the merged
code, such a call's row holds 0 output tokens stamped `estimated`. So this spec's Goal sentence, *a
reply cut at the output cap is recorded with its tokens*, is true of the adapter (test A3) and
**verified failing in the operator's ledger row**, on either vendor. The deliberator's wrapper reads
both on both paths. Work-queue 124. *Not observed:* a cached input token (0 on all three calls).

**Written at the merge, before the checks — still owed after the merge, none of it proven here:** F1a (the replay and the binding's refusal on
the merged `main`, at no cost), F1b (one paid `explain` and one `interpret` through the dashboard
binding on `gpt-5.5`), and the operator's `.env`. Not proven by any of them: a reply the vendor cut
off, and the return to Anthropic.

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
