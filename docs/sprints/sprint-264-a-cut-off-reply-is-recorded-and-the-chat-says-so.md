<!-- Agent: planning | Role: sprint handover -->
# Sprint 264 — a reply cut off at the cap is recorded with its stop reason and its tokens, and the chat says so in one sentence, the same on both vendors

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-264-a-cut-off-reply-is-recorded-and-the-chat-says-so`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-285](../design-log.md) (this sprint's six decisions, made and measured) · [DL-284](../design-log.md) amendments 1 and 2 (how the defect was found, and corrected) · [work-queue 124](../work-queue.md) · DRIFT-106

> **Why this bump kind.** No new capability: the operator's law already says every model call is
> recorded and every `explain` call is audited, and for a reply the vendor cut off the code does
> neither in full. A fix, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/operator/laws/laws.md` | The operator's **locked constitution** | **LOCKED.** This sprint amends it under a law cycle, named below. Any other clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `surfaces/laws/laws.md` | The surfaces' locked constitution | **LOCKED, read-only.** No clause of it changes in this sprint |
| `agents/<name>/laws/test-plan.md`, `surfaces/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: operator **`STA`**, **`OUT`**, **`FAIL`**, **`OBS`**, **`IDM`**; surfaces
**`FAIL`**, **`OUT`**.

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

**No file in `contracts/` changes, and none may. Yes, the operator gains a guarantee**, so one law
cycle is owed in this unit of work:

| Book | From | What the cycle owes |
| --- | --- | --- |
| `agents/operator/laws/laws.md` | LOCKED v1.6 | **`OPR-STA-03` reworded**, keeping what it says and adding: the row carries the vendor's own stop reason and the vendor's own token counts whether the reply finished or the vendor cut it off; a client that exposes neither is recorded as `unknown` with a stamped estimate. **New clause `OPR-FAIL-04`**: a reply the vendor cut off at the output cap is neither a fault nor an answer. It is recorded as `OPR-STA-03` says; `interpret` reads it as a refusal whose reason is the cut-off sentence, and the explicit command grammar still applies; `explain` returns the cut-off sentence; no part of the cut reply is shown; the `CommandAudit` is written and linked as for any call; the same on every vendor. Changelog line, version up |
| `agents/operator/laws/test-plan.md` | 19 / 50 | A row for `OPR-FAIL-04`; `OPR-STA-03`'s row cites the tests that now prove the reworded clause; the footer line set to what the gate derives |
| `surfaces/laws/test-plan.md` | 30 / 37 | `SRF-FAIL-02`'s row gains test D1 as one more citation. **No clause and no version of the surfaces book changes** |
| `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` | operator 19 / 50 | The operator's rollup line, in both, names this sprint and carries the count the gate derives |
| `docs/laws/drift-register.md` | DRIFT-106 is OPEN | Its status cell becomes CORRECTED, naming this sprint and the tests. Leave DRIFT-107 as it is: it belongs to work-queue 125 |

One clause ID is added and proven, so the operator's count moves. The law gate was run against a
planted clause, step by step (measured, table below): it derives **20 / 51**.
🪤 **The rollup is derived, not declared.** `make ci` recomputes it. Let the gate tell you the number.
🪤 **The gate does not read the test plan's own footer** (`## Green: 19 / 50`): measured, a stale
footer passes. Set it by hand to the gate's number.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/llm_anthropic.py` (**the class `OperatorAnthropicLLMClient`, one import and one constant, nothing else**) | `agents/operator/laws/laws.md` + `test-plan.md`; the docstring of `LLMClient` in `kernel/llm.py` (it is the kernel's rule for adapters: expose `last_stop_reason`, raise the stopped-completion error for a vendor-declared truncation); `tests/test_llm_adapter_ownership.py` and `tests/test_llm_adapter_security.py` (read both whole); `agents/deliberator/laws/laws.md` (read only) | `OPR-STA-03` (every call recorded), `OPR-SEC-01` (the key stays inside the client); the debate's client lives in the same file and must not change |
| `agents/operator/ledger.py` | `agents/operator/laws/laws.md` + `test-plan.md` | `OPR-STA-03`, `OPR-OBS-02` (the operator's calls are diagnosable from the graph alone) |
| `agents/operator/agent.py` | the same | `OPR-OUT-04` (explain returns an `Explanation`), `OPR-OUT-05` (every refusal is explained), `OPR-OUT-06` (a `CommandAudit` for **every** interpret and explain call, linked to its `LLMCall`), `OPR-FAIL-01` (a failed call is a fault and a refusal: unchanged), `OPR-IN-03` (never raises to the bus), `OPR-OBS-03` (a refusal is recorded), `OPR-IDM-01` (the audit's outcome is the record) |
| `agents/operator/domain/result.py` | the same | `OPR-OUT-05`, `OPR-NEV-05`, `OPR-FAIL-02` |
| `surfaces/tests/` (**a new test file only; no production file under `surfaces/` changes**) | `surfaces/laws/laws.md` + `test-plan.md` | `SRF-FAIL-02` (chat errors reach the operator in plain words, not raw SDK internals), `SRF-OUT-03` (a model-composed answer records its audit and ledger facts), `SRF-OUT-05` (operator-facing text carries no sprint, design-log, drift or law id) |

⚠️ **The one invariant this sprint must not break: the debate's client does not change, and a request
that fails is not taken for a reply that was cut off.** In `kernel/llm_anthropic.py` the classes
`_AnthropicTransport`, `_AnthropicClient` and `AnthropicLLMClient` stay byte for byte as they are.
`kernel/llm_anthropic_responses.py`, `kernel/llm_openai.py`, `kernel/llm_openai_operator.py`,
`kernel/llm.py`, `kernel/llm_ledger.py`, `kernel/llm_tokens.py`, `kernel/llm_factory.py`,
`kernel/llm_outage.py`, everything under `agents/deliberator/`, every file under `surfaces/` that is
not a new test, and `contracts/` do not change. Nor does any file under a fidelity decision path:
`agents/scanner/`, `agents/analyst/`, `agents/portfolio_manager/`, `agents/provider/domain/`,
`agents/execution/order_tolerance.py`, `orchestration/packs/trading_tunables.json`,
`orchestration/packs/trading_issuer_map.json`, `orchestration/history_window.py`. A time-out, a
refused key or any other exception from the client keeps today's path exactly (work-queue 125 owns
it). **If your build needs one of these changed, stop and report.**

---

## Goal

At merge, when a vendor cuts the operator's reply off at the output cap, on OpenAI or on Anthropic,
for `explain` or for `interpret`: the `LLMCall` row holds the vendor's own stop reason and the
vendor's own token counts; the `CommandAudit` is written and linked to that row; no fault is raised;
no part of the cut reply is shown; and the chat shows one fixed sentence that says the reply was cut
off. Every other operator row carries its vendor's stop reason too, where the client exposes one. A
request that fails is handled exactly as today.

## Why (context)

[S263](sprint-263-the-operators-chat-makes-its-tool-call-on-openai.md)'s paid check found that all
three ledger rows it wrote read `stop_reason: unknown` although the client held `completed`
([DL-284](../design-log.md) amendments 1 and 2). Reading the caller showed why: the operator agent
passes no stop reason to the ledger on any path, and reads the usage only after a call that
returned. The deliberator's wrapper reads both on both paths; the operator's two call sites were
never given one.

Measured through each real adapter and the dashboard's chat handler, a reply cut at the cap is today
three different events. On OpenAI the adapter raises: the row holds 0 output tokens stamped
`estimated` where the vendor billed 4,096, no `CommandAudit` is written, a fault is recorded, and the
chat shows the vendor's field name. On Anthropic the adapter does not raise: the tokens are kept and
the chat says *"No explanation returned."* with nothing saying why. And if Anthropic's reply is cut
inside the tool block, the chat shows the half sentence as an answer.

No cut-off has happened in the chat: the live ledger holds none from any agent, and the one real
cut-off this system has seen was produced on purpose (table below). The cost of leaving
it is that the first one will be recorded as free on one vendor, unexplained on the other, and
counted by the outage check as a call that returned nothing.

### Measured, 2026-10-09 — read these before designing

Scripts, their outputs and the prototype's diff are outside the repository
(`trading-agents-data/wq124-2026-10-09/`). The builder cannot reach them and does not need to: what
matters is in this file, and the prototype is in the Appendix. Everything below was run in the
sprint's worktree, which has no `.env`, on `main` at `2ce40c30`, with no call to a vendor, unless a
row says otherwise.

| Claim | Value | How it was measured |
| --- | --- | --- |
| No operator row carries a stop reason | **23 of 23** rows written by the measurement read `unknown`, the good replies and the vendor-filtered ones included | *[measured]* `wq124_cutoff_paths.py`: each real operator adapter built by `build_operator_llm` on a fake SDK, bound by `build_test_context`, each turn sent through `surfaces.dashboard.chat.handle_chat` |
| OpenAI, the quick ask *explain this run*, reply cut | chat: `refused`, *"openai completion stopped: stop_reason=max_output_tokens"*. Row: `unknown`, 9 in (a word count), **0 out**, `estimated`. **No `CommandAudit`.** One fault, from `kernel.bus` | *[measured]* the same script; the fake reply carries 21,133 in and 4,096 out |
| OpenAI, a typed question whose parse is cut | chat: `refused`, *"Operator could not parse the command."* Row as above. **No `CommandAudit`.** One fault, from the agent's own boundary | *[measured]* |
| OpenAI, a typed question parsed, then its answer cut | chat: the vendor-worded line again. Two rows, the second as above. One `CommandAudit` (`intent`); the explain call has none | *[measured]* |
| Anthropic, the quick ask, reply cut while thinking | chat: `answer`, *"No explanation returned."* Row: `unknown`, 21,133 in, 4,096 out, `vendor`. `CommandAudit` `explain`. No fault | *[measured]* |
| Anthropic, a typed question whose parse is cut | chat: `refused`, *"model returned no tool result"*. Row as above. `CommandAudit` `refused` | *[measured]* |
| Anthropic, reply cut inside the tool block | chat: `answer`, **`'The run finished: 8 of'`**, the half sentence shown as the answer | *[measured on an ASSUMED reply shape]* a `tool_use` block whose `input` holds a partial answer, with `stop_reason: max_tokens`. Whether the vendor returns a partial `input` is not known; the fix does not depend on it |
| An explicit `approve flag-12` whose parse is cut | OpenAI: `refused`, *"Operator could not parse the command."* Anthropic: `needs_confirmation`, because `normalize_explicit_intent` pins the grammar over whatever the model returned | *[measured]* |
| The outage check on a cut-off row | `kernel.llm_outage.is_silent_call` reads it **silent** on OpenAI (both capabilities) and on Anthropic for the explain: an empty response with `unknown` | *[measured]* the same script calls the predicate on each row |
| A reply the vendor filtered or refused (`content_filter`, `refusal`) | both vendors: `answer`, *"No explanation returned."*; row `unknown`; read silent | *[measured]* not changed by this sprint beyond the row's stop reason |
| **Not a cut-off:** the request fails (a time-out; the vendor answering HTTP 400) | both vendors alike. The quick ask: `refused`, the error's own text, which for a vendor's status error the surface already rewords (*"The language model refused the request (HTTP 400): ..."*); no `CommandAudit`; fault from `kernel.bus`. A typed question: *"Operator could not parse the command."*, the reason shown nowhere; no `CommandAudit`; fault from the agent. The row reads silent, as it should | *[measured]* eight cases, **identical before and after the prototype.** This is work-queue 125 and DRIFT-107, not this sprint |
| What the chat page shows of a turn | only `turn.message`; `outcome` changes nothing on screen except for `needs_confirmation`, `dispatched` and `confirmed_dispatch` | *[measured, read]* `renderTurn` and `send` in `surfaces/dashboard/static/chat.js`, both whole |
| Who else reads a `CommandAudit`'s outcome | `surfaces/queries/scorecard_actions.py::_acts`: an audit with no `Intent` whose outcome is not `explain` counts as **a human action** on the unattended scorecard | *[measured, read]* the function whole; `grep CommandAudit` over every tracked `.py` outside tests finds only the operator's store, the contract and this reader |
| The live ledger | 1,456 `LLMCall` rows. **None, from any agent, reads `max_tokens`, `length` or `max_output_tokens`.** The operator has 9 rows, all `unknown`, all `claude-opus-5`, 2026-09-23 and -24; the largest reply 703 output tokens; none at or over 4,096 | *[measured 2026-10-09 23:37 AEDT, read-only, the main checkout with its `.env`]* `wq124_live_ledger_read.py` |
| How OpenAI reports a cut-off | `status: "incomplete"`, `incomplete_details.reason: "max_output_tokens"`; `output` holds one `reasoning` item and no function call; `usage` reads 278 in and 64 out, all 64 of them reasoning, 0 cached | *[measured 2026-10-10 00:27 AEDT, one paid call, $0.0033 at the price pack's rates]* `gpt-5.5` (the vendor names it `gpt-5.5-2026-04-23`) at `xhigh` with the cap at 64, a typed question through the chat handler on an in-memory graph, on `main` at `ad741063`. On that code the chat said *"Operator could not parse the command."*, the row read `unknown`, 13 in, 0 out, `estimated`, no `CommandAudit` was written and a fault was recorded: the second row of this table, now on a real reply. A reply cut inside the function call's arguments has not been produced |
| How Anthropic reports a cut-off | `stop_reason: "max_tokens"` | *[read in the SDK's types and in `kernel/llm_anthropic_responses.py` — NOT produced by the vendor]* its account is empty until 2026-10-11; the paid check after merge produces one |
| A prototype of the whole change | four files, 58 lines added and 14 removed (Appendix). After it, on both vendors: the sentence in the chat for every cut-off case; rows 21,133 in, 4,096 out, `vendor`, with `max_output_tokens` or `max_tokens`; good replies read `completed` or `tool_use`; filtered ones `content_filter` or `refusal`; audits `explain`, `refused`, and `intent` then `explain`; no fault; no row read silent; the explicit approve asks for confirmation on both | *[measured]* the same script on the prototype; the two outputs were diffed |
| Existing tests the prototype breaks | **None.** 857 passed: `agents/operator`, `agents/deliberator/tests`, `surfaces/tests`, and under `tests/` the operator, adapter-ownership, adapter-security and outage files. So no existing test guards any of this | *[measured]* run on the prototype |
| Prototype tests for every row of the Test plan | 25 cases pass on the prototype; on `main` the file fails at collection, on the import of the two new names | *[measured]* `proto_test_cut_off.py`, 412 lines, outside the repository |
| The prototype broken 23 ways, one at a time | **23 red, none survived.** The break and the test that caught it are in the handback checklist, item 4 | *[measured]* `planner_mutations.py` |
| `mypy`, the import contracts, the size and header checks on the prototype | clean. `kernel/llm_anthropic.py` **168** lines, `agents/operator/agent.py` **168**, `agents/operator/ledger.py` **75**, `agents/operator/domain/result.py` **100** | *[measured]* |
| The law gate on a planted `OPR-FAIL-04` | clause only: red, *"1 missing row(s): OPR-FAIL-04"* and *"operator claims 19 / 50; derived 19 / 51"* on both rollups. A 🟩 row citing a test that does not exist: red, *"cites no live test"*. The test exists and its docstring names no clause: red, *"no resolved test docstring names OPR-FAIL-04"*. Docstring cites it, rollups unchanged: red, *"derived 20 / 51"*. Both rollups say 20 / 51: **exit 0**. The test plan's footer was stale throughout and never reported | *[measured]* `scripts/check_law_coverage.py`, seven runs, every file restored |
| The SDKs in the worktree's environment | `openai` 2.49.0 is installed (it arrives with DSPy). **`anthropic` is not**: it is in the `llm` extra | *[measured]* `importlib.util.find_spec` in the worktree's venv |

---

## Scope — and what is deliberately NOT here

1. **Anthropic's operator client keeps the vendor's stop reason and raises on a cut-off (D1).** In
   `kernel/llm_anthropic.py`, the class `OperatorAnthropicLLMClient` only.
2. **One helper records a completion on both paths (D2).** `agents/operator/ledger.py` gains
   `complete_recorded`.
3. **The agent's two call sites use it; a cut-off says the sentence (D3, D4, D5).**
   `agents/operator/agent.py` and `agents/operator/domain/result.py`.
4. **The law cycle**, as the table above says, and DRIFT-106 marked CORRECTED.

### Out of scope (do NOT build this sprint)

- **A request that fails**: a time-out, a refused key, an account with no credit. It writes no
  `CommandAudit` either, and a typed question then says *"Operator could not parse the command."*
  with the reason shown nowhere. Measured above, filed as work-queue 125 and DRIFT-107, and it
  needs its own decision. Do not add a fault boundary to `_explain`, do not write an audit on that
  path, do not reword *"Operator could not parse the command."*
- **A reply the vendor filtered or refused.** It keeps today's sentence; its row now names the
  reason. Do not raise on `refusal` or `content_filter`.
- **Showing part of a cut reply, a retry, a larger cap.** The cap stays 4,096 and its bound stays.
- **The debaters** (work-queue 123), the OpenAI operator adapter, the factory, the port.
- **Any production file under `surfaces/`**, the chat page, the scorecard, the outage script.
- **The operator container.** It keeps the fake client, which exposes no stop reason.
- **`docs/STATE.md`, `docs/work-queue.md`, `docs/design-log.md`** (one exception: an amendment under
  DL-285 if the build forces a decision).
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

Recorded in full in [DL-285](../design-log.md). In short:

- **Show the part of the reply that arrived, marked as cut.** Rejected: OpenAI returns no usable
  part, so the vendors would differ again, and half a sentence about the book reads as a statement.
- **Leave Anthropic's client as it is and let the agent compare stop reasons.** Rejected: the agent
  would need each vendor's vocabulary, which the port assigns to the adapter.
- **Raise from `explain` and let the bus report it**, as OpenAI does today. Rejected: it skips the
  audit, records a fault for a call that completed and was billed, and shows a vendor's field name.
- **Reword the error at the surface**, in `surfaces/plain_errors.py`, where a vendor's status error
  is already reworded. Rejected: it would change the words on one path of one vendor and leave the
  row's tokens, the missing audit, the fault and Anthropic's unexplained answer as they are.
- **Audit a cut-off `explain` as `refused`.** Rejected: the scorecard would count a question as a
  human action.
- **Record a fault for a cut-off.** Rejected: the row and the audit are the record, and on the
  dashboard the fault sink is in memory.
- **Name the cap or the vendor in the sentence.** Rejected: the agent is handed a client and does
  not know its cap, and the vendor's word is on the row.
- **Raise on a vendor's refusal too.** Rejected for now: the OpenAI adapter returns the refusal
  dictionary on `content_filter`, so raising on Anthropic's `refusal` would make the vendors differ.
- **Fold the failed request in.** Sequenced, not rejected: work-queue 125.

---

## The design decisions — made, and recorded in DL-285

Build them as written. If one cannot be built as written, stop and report.

- **D1.** `OperatorAnthropicLLMClient` has `last_stop_reason`: the port's `unknown` after
  construction and at the start of every `complete`, the reply's `stop_reason` after the request.
  When that is `max_tokens`, `complete` raises
  `LLMCompletionStoppedError(provider="anthropic", stop_reason="max_tokens")`, **after**
  `last_stop_reason` and `last_usage` are set. Every other stop reason, `refusal` included, returns
  as today.
- **D2.** `agents/operator/ledger.py::complete_recorded(call, llm, *, system, user, tool_schema)`
  returns `str | None`. On the stopped-completion error it sets the capture's stop reason from the
  error and its usage from the client, and returns `None`. On a reply it sets the response, the
  client's stop reason (`kernel.llm_stop_reason`) and its usage, and returns the reply. **Any other
  exception passes through untouched.**
- **D3.** The sentence is one constant, `CUT_OFF_REPLY`, in `agents/operator/domain/result.py`:
  *"The model's reply was cut off at its output limit before it finished, so there is no answer. Ask
  again, or ask something narrower."* It names no vendor, no model, no number and not the word
  *token*. One test pins it letter for letter.
- **D4.** `explain`: on a cut-off the `CommandAudit` is written with outcome **`explain`**, linked
  to the row, exactly as for an answer; then `Explanation(summary=CUT_OFF_REPLY)` is returned. No
  fault.
- **D5.** `interpret`: a cut-off is read as `{"outcome": "refused", "reason": CUT_OFF_REPLY}` and
  passed through `normalize_explicit_intent` like any reply, so an explicit `approve <target>`
  keeps its grammar and everything else is refused with the sentence. The existing flow writes the
  audit. No fault.
- **D6.** Nothing else moves: a failed request, a vendor's refusal, the cap, every surfaces file.

🪤 **Take the next free DL number only if the build forces a new decision, then re-check it at
merge.** DL-285 is this sprint's; an amendment goes under it.

---

## Blast radius — measured 2026-10-09

| What | Detail |
| --- | --- |
| Files changed | `kernel/llm_anthropic.py` **162**, `agents/operator/ledger.py` **48**, `agents/operator/agent.py` **164**, `agents/operator/domain/result.py` **93**; `agents/operator/laws/laws.md` and `test-plan.md`; `surfaces/laws/test-plan.md` (one row); `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md` (one row each). New: test files as you need them, each under 200 lines |
| Agents affected | operator; kernel (one adapter class); surfaces by a test only. No agent imports another |
| Contract change? | No, and none is allowed |
| Graph vocabulary change? | No. `stop_reason` is already a declared property of `LLMCall`; the operator's rows change its value from `unknown` to the vendor's word |
| New env keys / tunables | None |
| Deploy implication | None required. The chat runs in the dashboard, from the main checkout; the fleet's operator container binds the fake client; the debate's Anthropic client is unchanged. The next retag carries the code |
| Rollback | Revert the merge commit. Nothing is deployed and nothing outside the repository changes |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Read DL-285** in `docs/design-log.md`, and DL-284's amendments 1 and 2.
3. **Plant the failing tests first** (A1 and D1 of the Test plan, with the sentence written out in
   the test so the file collects) and watch them fail on behaviour. Paste the red output.
4. **Implement**, in the order of Scope 1 to 3. The Appendix holds the measured prototype.
5. **The law cycle**: the reworded clause, the new clause, the test-plan rows, the docstring
   citations, the rollups, DRIFT-106.
6. **Prove the guards can fail (DL-70)**: break the implementation, watch each guard go red, restore.
7. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Each vendor's SDK is a fake injected through `importlib.import_module`, as the existing operator
tests do, with `SimpleNamespace` replies. The D tests build each **real** operator adapter with
`kernel.llm_factory.build_operator_llm` on that fake and send the turn through
`surfaces.dashboard.chat.handle_chat`. In the fake replies below a cut-off carries 21,133 input and
4,096 output tokens.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 Anthropic's cut-off is recorded, then raised | a reply with `stop_reason="max_tokens"`, once with a `thinking` block only and once with a `tool_use` block whose `input` holds a partial answer; with a schema and without | `LLMCompletionStoppedError` with provider `anthropic` and stop reason `max_tokens`; `last_stop_reason == "max_tokens"` and `last_usage` holds 21,133 and 4,096 when it is raised. `OPR-STA-03` |
| A2 | a finished reply keeps the vendor's word | `stop_reason="tool_use"`, a `tool_use` block; one call with a schema, one without | `last_stop_reason` is `unknown` before the first call and `tool_use` after each; the results are what they are today |
| A3 | 🪤 a vendor's refusal is not a raise | `stop_reason="refusal"`, no tool block | no raise; `last_stop_reason == "refusal"`; an empty answer without a schema, the refusal dictionary with one |
| A4 | a failed request clears the last stop reason | a good call, then `create` raises `TimeoutError` | the error propagates; `last_stop_reason == "unknown"`, `last_usage is None`. `OPR-STA-03` |
| B1 | 🎯 the helper on a cut-off | a stub client that sets its stop reason and usage, then raises the stopped-completion error | `None` is returned; the row holds the stop reason, 21,133, 4,096 and `vendor`. `OPR-STA-03` |
| B2 | the helper on a reply | a stub that returns text with stop reason `completed` | the text is returned and is the capture's response; the row holds `completed` and the vendor's counts |
| B3 | 🪤 a client that exposes neither | `kernel.FakeLLMClient` | the row reads `unknown` and `estimated`, as the fleet's operator container writes today |
| B4 | 🪤 any other error is not a cut-off | a stub that raises `TimeoutError` | it propagates; the row reads `unknown`, 0 out, `estimated`, and `is_silent_call` is true for it. `OPR-FAIL-01` |
| C1 | 🎯 `explain`, cut off | the stub of B1, once per vendor's word (`max_tokens`, `max_output_tokens`) | the summary is the sentence; the one row holds that word and the vendor's counts; one `CommandAudit`, outcome `explain`, with a `PRODUCED_BY` edge to the row; the fault sink is empty. `OPR-FAIL-04` / `OPR-OUT-06` / `OPR-STA-03` |
| C2 | 🎯 `interpret`, cut off | the same stub, a typed question | outcome `refused`, no intent, the message is the sentence; the row as in C1; one `CommandAudit`, outcome `refused`, linked; no `Intent` node; the fault sink is empty. `OPR-FAIL-04` / `OPR-OUT-05` / `OPR-OBS-03` |
| C3 | 🪤 an explicit approve keeps its grammar | the same stub, the text `approve flag-12` | outcome `intent`, family `approve`, parameters `{"target": "flag-12"}`, confirmation required; the row holds the cut-off word. `OPR-FAIL-04` |
| C4 | a finished call's row carries the client's stop reason | a stub answering with `completed`, then one with `tool_use` | the `explain` row reads `completed`, the `interpret` row `tool_use`. `OPR-STA-03` |
| C5 | 🪤 a failed request is still a fault and the old refusal | a stub that raises `TimeoutError`, on `interpret` | the message is *"Operator could not parse the command."*; one fault of type `TimeoutError`; the row reads `unknown` and `estimated`. `OPR-FAIL-01` |
| C6 | the sentence | the constant | equal to D3's text letter for letter; lower-cased it contains none of `openai`, `anthropic`, `gpt`, `claude`, `token`; it contains no digit. `OPR-FAIL-04` |
| D1 | 🎯 one event reads the same on both vendors, through the chat | for each of: the quick ask *explain this run* with its reply cut; a typed question with its parse cut; a typed question parsed and its answer cut. Each on `openai` and on `anthropic` | on both: the turn's message is the sentence; the outcome and the audits are `answer` and `explain`, `refused` and `refused`, `answer` and `intent` plus `explain`; no fault; the last row holds 21,133, 4,096, `vendor`; no row is read silent. The stop reasons are each vendor's own (`max_output_tokens`, `max_tokens`; `completed`, `tool_use` for the parsed call). **With the stop reasons left out, what was observed on the two vendors is equal.** `SRF-FAIL-02` / `OPR-FAIL-04` |
| D2 | 🪤 a reply cut inside the tool block shows no part of itself | Anthropic, the quick ask, the partial-answer reply of A1 | the message is the sentence, and the partial text appears nowhere in the turn. `OPR-FAIL-04` |
| D3 | 🪤 the outage check reads a failed request silent, and a cut-off not | on each vendor: the quick ask cut; then the quick ask with `create` raising `TimeoutError` | the cut-off row is not silent; the failed row is, the turn's message is not the sentence, and one fault was recorded |

---

## Success factors

- [ ] On both vendors a cut-off reply's row holds the vendor's stop reason and token counts (A1, B1,
      C1, C2, D1).
- [ ] The chat shows the one sentence for a cut-off `explain` and a cut-off `interpret`, on both
      vendors, and no part of the cut reply (C1, C2, D1, D2).
- [ ] A cut-off `explain` writes its `CommandAudit` with outcome `explain`; a cut-off `interpret`
      writes one with outcome `refused`; neither records a fault (C1, C2).
- [ ] An explicit approve keeps its grammar on a cut-off (C3).
- [ ] A request that fails behaves exactly as on `main` (B4, C5, D3), and a vendor's refusal is not
      raised (A3).
- [ ] `_AnthropicTransport`, `_AnthropicClient`, `AnthropicLLMClient` and every file the invariant
      names are unchanged; the command in the handback checklist prints nothing.
- [ ] The law cycle done: `OPR-STA-03` reworded and re-proven, `OPR-FAIL-04` added and proven, the
      changelog, the version, the test-plan rows and footer, both rollups, DRIFT-106 CORRECTED.
- [ ] Design decisions built as recorded in DL-285, or an amendment under it.
- [ ] Every guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched or new module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The existing suite is green on the prototype and proves nothing here.** 857 tests pass with the
whole change in, and they passed before it. Only the tests of this plan guard it.
🪤 **A red on an import is not the red asked for.** A test file that imports `CUT_OFF_REPLY` or
`complete_recorded` fails at collection before the implementation exists. Plant A1 and D1 first with
the sentence written out in the test, so they collect and fail on what the code does.
🪤 **The worktree has no Anthropic SDK.** Inject a fake module through `importlib.import_module`, as
`agents/operator/tests/test_operator_llm_usage.py` does. Its fake replies have no `stop_reason`
attribute at all and must keep passing: an absent stop reason reads `unknown` and is not a cut-off.
🪤 **`except Exception` in the helper takes a time-out for a cut-off.** Catch the stopped-completion
error and nothing else. B4, C5 and D3 are the guards.
🪤 **The audit of a cut-off `explain` stays `explain`.** Written as `refused` it becomes a human
action on the unattended scorecard.
🪤 **Do not answer a cut-off `explain` before its audit is written**, and do not skip
`normalize_explicit_intent` for a cut-off `interpret`.
🪤 **The debate's client is in the same file.** `AnthropicLLMClient` does not reset its stop reason
before a request; leave that as it is. Change the operator's class only.
🪤 **Tests must not depend on a `.env`.** `build_test_context` builds the agent with
`OperatorSettings()`, which reads one where it exists; the main checkout's sets the provider to
`openai`. Every D test sets `OPERATOR_LLM_PROVIDER` and deletes `OPERATOR_MODEL` and
`OPERATOR_EFFORT` itself.
🪤 **`graph.list_nodes` returns a tuple.** Compare with `not ...` or with `()`, never with `[]`.
🪤 **`OPR-OUT-06` says "every call" and a failed request still writes no audit.** That is DRIFT-107
and work-queue 125. Do not fix it here, and do not let the new clause claim it.
🪤 **A summary that fits the test is not the clause** (conventions §7a). `OPR-FAIL-04` asserts
several things at once (recorded, not a fault, a refusal on `interpret` with the grammar kept, the
sentence on `explain`, nothing of the cut reply shown, the audit written, the same on every
vendor); its row is 🟩 only when the cited tests prove each of them.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `kernel/llm_anthropic.py` **162**, `agents/operator/agent.py` **164**,
  `agents/operator/tests/test_operator_agent.py` **182**. The planner's prototype tests ran to 412
  lines in one file: yours need at least three.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. The vendor's stop word is a named
  module constant, as `_CUT_OFF` is in `kernel/llm_openai_operator.py`.
- Faults, not silent failure — `kernel.fault_boundary`. A cut-off is not a fault (D4, D5); a failed
  request still is.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- The version bump is the planner's, at merge: do not touch `pyproject.toml` or `uv.lock`.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. Review the diff against the checklist; re-measure (the scope command; `wq124_cutoff_paths.py`
   against the built code; the guards broken again by the planner); merge `main` in; PATCH bump,
   `uv lock`; Windows `make ci`; push; **`make gate-ran` from `../ta-s264`**, the printed SHA checked
   against `git rev-parse HEAD`; CodeQL set-diff against the open alerts of S263's branch (127, no
   error); fast-forward `main`; tag.
2. **F1a, at no cost, from the main checkout on the merged code:** `wq124_cutoff_paths.py` prints,
   for every cut-off case on both vendors, the sentence, the vendor's counts and stop word, the
   audits and no fault; the time-out cases print what they print today.
3. **F1b, paid, on the operator's word: under one cent a vendor.** One typed question through the
   chat handler on an in-memory graph, the real adapter built with the cap at 64, so the vendor cuts
   the reply: about 290 input and 64 output tokens. One was produced on OpenAI before the build
   (2026-10-10, $0.0033, the Measured table), on `main`'s code; after merge the same call on the
   built code must show the sentence, the vendor's counts and stop word on the row, and the audit.
   On Anthropic after its account is funded (2026-10-11), where it also reads that vendor's own
   cut-off reply for the first time: the stop word, the counts, what the tool block holds.
4. No deploy. **Not proven by any of these:** a reply cut off at the real cap of 4,096 on the
   21,000-token explain prompt.

---

## Handover — paste this to Codex

```text
Sprint 264 — a reply cut off at the cap is recorded with its stop reason and its tokens, and the
chat says so in one sentence, the same on both vendors.
Spec: docs/sprints/sprint-264-a-cut-off-reply-is-recorded-and-the-chat-says-so.md (read ALL of it,
then CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s264, on branch
sprint-264-a-cut-off-reply-is-recorded-and-the-chat-says-so, cut from main, with its venv synced to
the lock. Work only in that worktree, never in the main checkout and never on main. You have no
.env and no network: every proof is a unit test. The Anthropic SDK is NOT installed there (openai
is): inject a fake module through importlib.import_module, as the existing operator tests do.
`uv run` is safe; never run a bare `uv sync`. Do not touch pyproject.toml or uv.lock, and say so:
the planner bumps the version at merge. Do not push and do not merge: commit on the branch and hand
back. Do not edit docs/STATE.md, docs/work-queue.md or docs/design-log.md (one exception: an
amendment under DL-285 if the build forces a decision). If a make ci step cannot run in your sandbox
(the dependency audit needs the network), do not bypass it silently: name the step as NOT RUN in
the handback.

This handover is complete: nobody will send you follow-up messages. Two tiers:
- A wrong line number, count, path, test name or clause number whose intent is plain from the spec's
  Scope and Success factors is NOT a reason to stop: follow the intent, record the correction in
  Return notes, continue. The same holds if a gate wants a rollup line or a test-plan row worded
  differently from the spec: do what the gate accepts and say so.
- STOP and report, without improvising, when: the build needs a change to _AnthropicTransport,
  _AnthropicClient or AnthropicLLMClient in kernel/llm_anthropic.py, to
  kernel/llm_anthropic_responses.py, kernel/llm_openai.py, kernel/llm_openai_operator.py,
  kernel/llm.py, kernel/llm_ledger.py, kernel/llm_tokens.py, kernel/llm_factory.py,
  kernel/llm_outage.py, to anything under agents/deliberator/, to any file under surfaces/ that is
  not a new test, to contracts/, or to any file under agents/scanner/, agents/analyst/,
  agents/portfolio_manager/, agents/provider/domain/, agents/execution/order_tolerance.py,
  orchestration/history_window.py, orchestration/packs/trading_tunables.json or
  orchestration/packs/trading_issuer_map.json; an EXISTING test has to be edited (the planner's
  prototype broke none of 857); a law you read contradicts the spec; or a decision D1-D6 cannot be
  built as written.

What and why: the operator's dashboard chat asks a model for one forced tool call, on OpenAI or on
Anthropic. When the vendor cuts the reply off at the output cap, the two vendors behave differently
today (measured, the spec's table): on OpenAI the adapter raises, the ledger row records 0 output
tokens where the vendor billed 4,096, no CommandAudit is written and the chat shows the vendor's
field name; on Anthropic the adapter does not raise and the chat says "No explanation returned.",
or shows half a sentence as an answer. And no operator ledger row carries a stop reason at all. You
make the Anthropic operator client raise on a cut-off as the OpenAI one does, add one helper that
records the stop reason and the usage on both paths, use it at the agent's two call sites, and make
a cut-off say one fixed sentence. You unit-test all of it. You call no vendor.

MUST RULE before any code: read, whole, agents/operator/laws/laws.md and surfaces/laws/laws.md (each
with its test-plan.md), agents/deliberator/laws/laws.md (read only), docs/laws/conventions.md,
docs/laws/drift-register.md, kernel/llm.py, tests/test_llm_adapter_ownership.py,
tests/test_llm_adapter_security.py, and DL-285 and DL-284 (amendments 1 and 2) in
docs/design-log.md. Fill the Law reading record first.
Law-cycle answer: YES for operator (OPR-STA-03 reworded, NEW clause OPR-FAIL-04, changelog, version
up); surfaces gets one more citation on SRF-FAIL-02's test-plan row and NO clause or version change;
NO contracts/ file changes. The gate derives the operator's count (the planner measured 20 / 51).

Order (the spec's Steps): laws -> plant A1 and D1 with the sentence written out in the test, watch
them fail on behaviour (not on an import), paste the red -> implement Scope 1, 2, 3 (the Appendix
holds the measured prototype) -> the remaining tests -> the law cycle and DRIFT-106 -> break and
restore every guard -> make ci to a file.

Build (decisions D1-D6 are made; build them as written):
1. kernel/llm_anthropic.py, class OperatorAnthropicLLMClient only: last_stop_reason (unknown after
   construction and at the start of each complete, the reply's stop_reason after the request); on
   max_tokens raise LLMCompletionStoppedError(provider="anthropic", stop_reason="max_tokens") after
   the stop reason and the usage are set. One import, one module constant.
2. agents/operator/ledger.py: complete_recorded(call, llm, *, system, user, tool_schema) -> str |
   None. Catches the stopped-completion error ONLY.
3. agents/operator/domain/result.py: CUT_OFF_REPLY (D3's exact text); parse_json(None) is the
   refusal whose reason is that sentence.
4. agents/operator/agent.py: both call sites go through complete_recorded; explain writes its audit
   with outcome "explain" and then returns the sentence on a cut-off; interpret needs no other
   change.
5. The law cycle; DRIFT-106 to CORRECTED.

DO NOT: change the debate's client or anything else the invariant names; catch any exception but
the stopped-completion error in the helper; raise on a vendor's refusal or filter; add a fault
boundary to _explain; write an audit for a failed request; reword "Operator could not parse the
command." or "No explanation returned."; audit a cut-off explain as "refused"; record a fault for a
cut-off; show any part of a cut reply; retry; raise the cap or its bound; name a vendor, a model, a
number or the word token in the sentence; give the operator container a real client; change a file
under surfaces/ other than adding tests; let a test depend on a .env; edit an existing test; pin a
version number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The red output of A1 and D1 pasted, from before the implementation, each failing on behaviour.
 3. Test plan results: one row for each of A1-A4, B1-B4, C1-C6 and D1-D3, with file and status.
 4. Every guard's break-and-restore stated, one line per guard. At least these, each of which the
    planner broke on the prototype and saw red (the test that caught it in brackets):
    the Anthropic raise removed (A1, D1, D2); the raise placed before the stop reason is kept (A1);
    the stop reason not reset before the request (A4); a refusal raising too (A3); the wrong
    cut-off word, and the other vendor's word on the error (A1); in the helper: usage not read on
    the cut-off path (B1, C1), stop reason not kept on the cut-off path (B1), stop reason not kept
    on the finished path (B2, C4), usage not read on the finished path (B2), the response not kept
    (B2), every exception taken for a cut-off (B4, C5, D3), an empty string returned instead of
    None (C1); in the agent: a cut-off explain answering before its audit (C1), audited as
    "refused" (C1), saying "No explanation returned." (C1, D2), interpret calling the client
    directly (C2, C3), explain calling the client directly (C1, C4); in result.py: a cut-off parse
    with no reason (C2), a cut-off parse asking for clarification (C2), the sentence reworded,
    naming a vendor, naming the cap (C6).
 5. This prints nothing, and you say so (run it against the commit the branch was cut from if main
    has moved; name which you used):
    git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration/history_window.py orchestration/packs kernel/llm.py kernel/llm_ledger.py kernel/llm_tokens.py kernel/llm_factory.py kernel/llm_outage.py kernel/llm_openai.py kernel/llm_openai_operator.py kernel/llm_anthropic_responses.py agents/deliberator surfaces/dashboard surfaces/queries surfaces/context.py surfaces/operator_tools.py surfaces/mcp_tools.py surfaces/laws/laws.md pyproject.toml uv.lock docs/STATE.md docs/work-queue.md
 6. `git diff main -- kernel/llm_anthropic.py` pasted whole: one import, one constant and the
    operator's class; _AnthropicTransport, _AnthropicClient and AnthropicLLMClient untouched.
 7. Every EXISTING test you edited, named, with the reason. The expected answer: none.
 8. The operator law book's old and new version, OPR-STA-03 and OPR-FAIL-04 quoted as written, the
    test-plan rows quoted, DRIFT-106's new status cell quoted, and the rollup lines make ci printed.
 9. The law gate's output (scripts/check_law_coverage.py), exit code stated.
10. make ci output file named, exit code stated, every NOT RUN step named with its reason.
11. Module line counts for every touched or new Python module; Status BUILT here and in the README
    row (the status cell leads with BUILT).
12. One line saying no vendor was called, and anything in the build you are unsure of.
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

**Design decisions:** recorded as [`DL-285`](../design-log.md) — <one line on any amendment, or "built as written">

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

## Appendix — the planner's prototype

Measured on `main` at `2ce40c30`: with this diff applied, the 857 existing tests named in the
Measured table pass, `mypy`, the import contracts, the size and header checks are clean, and the
planner's 25 prototype test cases pass. It is the shape to build; the tests and the law cycle are
yours. It was removed from the worktree after measuring, so you start from `main`'s code.

```diff
--- a/kernel/llm_anthropic.py
+++ b/kernel/llm_anthropic.py
@@ -11,7 +11,7 @@ import importlib
 import json
 from typing import TYPE_CHECKING

-from kernel.llm import STOP_REASON_UNKNOWN
+from kernel.llm import STOP_REASON_UNKNOWN, LLMCompletionStoppedError
 from kernel.llm_anthropic_responses import (
     _stop_reason,
     _text,
@@ -26,6 +26,7 @@ if TYPE_CHECKING:
 # Anthropic 0.120.2, measured offline 2026-10-08 (DL-274 D2): non-streaming
 # requests require 3,600 s * max_tokens / 128,000 <= 600 s.
 NONSTREAMING_MAX_TOKENS = 21_333
+_CUT_OFF = "max_tokens"


 class ConfigurationError(RuntimeError):
@@ -128,12 +129,14 @@ class OperatorAnthropicLLMClient(_AnthropicClient):
             max_tokens=max_tokens,
             effort=effort,
         )
+        self.last_stop_reason = STOP_REASON_UNKNOWN

     def complete(
         self, *, system: str, user: str, tool_schema: dict[str, object]
     ) -> str:
-        """Call Anthropic with a bounded tool-use response."""
+        """Force one named tool, recording usage even for a cut-off reply."""
         name = "parse_intent" if tool_schema else "answer_question"
+        self.last_stop_reason = STOP_REASON_UNKNOWN
         schema = tool_schema or {
             "type": "object",
             "properties": {"answer": {"type": "string"}},
@@ -158,5 +161,8 @@ class OperatorAnthropicLLMClient(_AnthropicClient):
             ],
             tool_choice={"type": "tool", "name": name},
         )
+        self.last_stop_reason = _stop_reason(response)
+        if self.last_stop_reason == _CUT_OFF:
+            raise LLMCompletionStoppedError(provider="anthropic", stop_reason=_CUT_OFF)
         data = _tool_input(response)
         return json.dumps(data) if tool_schema else str(data.get("answer", ""))
--- a/agents/operator/ledger.py
+++ b/agents/operator/ledger.py
@@ -11,13 +11,14 @@ from contextlib import contextmanager
 from typing import TYPE_CHECKING

 from agents.operator.prompt_recipe import PROMPT_RECIPE_HASH
+from kernel import LLMCompletionStoppedError, llm_stop_reason, llm_usage
 from kernel.llm_ledger import LLMCallCapture
 from kernel.llm_ledger import record_llm_call as _record_llm_call

 if TYPE_CHECKING:
     from collections.abc import Iterator

-    from kernel import GraphStore
+    from kernel import GraphStore, LLMClient


 @contextmanager
@@ -46,3 +47,29 @@ def record_llm_call(
         prompt_recipe_hash=PROMPT_RECIPE_HASH,
     ) as capture:
         yield capture
+
+
+def complete_recorded(
+    call: LLMCallCapture,
+    llm: LLMClient,
+    *,
+    system: str,
+    user: str,
+    tool_schema: dict[str, object],
+) -> str | None:
+    """Complete inside an open capture; None means the vendor cut the reply off.
+
+    The stop reason and the usage are read on both paths: a reply cut at the cap
+    was generated and billed in full, so a capture that read them only after a
+    call that returned would record the dearest calls as costing nothing.
+    """
+    try:
+        raw = llm.complete(system=system, user=user, tool_schema=tool_schema)
+    except LLMCompletionStoppedError as exc:
+        call.set_stop_reason(exc.stop_reason)
+        call.set_usage(llm_usage(llm))
+        return None
+    call.set_response(raw)
+    call.set_stop_reason(llm_stop_reason(llm))
+    call.set_usage(llm_usage(llm))
+    return raw
--- a/agents/operator/domain/result.py
+++ b/agents/operator/domain/result.py
@@ -20,9 +20,16 @@ if TYPE_CHECKING:

 Outcome = Literal["intent", "refused", "needs_clarification"]

+CUT_OFF_REPLY = (
+    "The model's reply was cut off at its output limit before it finished, "
+    "so there is no answer. Ask again, or ask something narrower."
+)

-def parse_json(raw: str) -> dict[str, object]:
-    """Parse model JSON, normalizing malformed output to a refusal."""
+
+def parse_json(raw: str | None) -> dict[str, object]:
+    """Parse model JSON; malformed output, or a cut-off reply (None), is a refusal."""
+    if raw is None:
+        return {"outcome": "refused", "reason": CUT_OFF_REPLY}
     try:
         data = json.loads(raw)
     except json.JSONDecodeError:
--- a/agents/operator/agent.py
+++ b/agents/operator/agent.py
@@ -19,6 +19,7 @@ from agents.operator.domain.prompts import (
     build_interpret_user,
 )
 from agents.operator.domain.result import (
+    CUT_OFF_REPLY,
     intent_from_data,
     message,
     outcome,
@@ -27,7 +28,7 @@ from agents.operator.domain.result import (
     request_correlation,
     with_graph,
 )
-from agents.operator.ledger import record_llm_call
+from agents.operator.ledger import complete_recorded, record_llm_call
 from agents.operator.settings import OperatorSettings
 from agents.operator.store import write_command_audit, write_intent
 from contracts.common import Explanation
@@ -43,7 +44,6 @@ from kernel import (
     FakeLLMClient,
     FaultSink,
     GraphStore,
-    llm_usage,
 )
 from kernel.errors import fault_boundary

@@ -104,9 +104,9 @@ class OperatorAgent(AgentBase):
             prompt=user,
             system_prompt=system,
         ) as call:
-            raw = self._llm.complete(system=system, user=user, tool_schema={})
-            call.set_response(raw)
-            call.set_usage(llm_usage(self._llm))
+            raw = complete_recorded(
+                call, self._llm, system=system, user=user, tool_schema={}
+            )
         assert call.node is not None
         write_command_audit(
             self._graph,
@@ -117,6 +117,8 @@ class OperatorAgent(AgentBase):
             outcome="explain",
             llm_call_node=call.node,
         )
+        if raw is None:
+            return Explanation(summary=CUT_OFF_REPLY)
         return Explanation(summary=raw.strip() or "No explanation returned.")

     def _interpret_command(self, command: HumanCommand) -> CommandResult:
@@ -132,11 +134,13 @@ class OperatorAgent(AgentBase):
             prompt=user,
             system_prompt=system,
         ) as call:
-            raw = self._llm.complete(
-                system=system, user=user, tool_schema=INTENT_TOOL_SCHEMA
+            raw = complete_recorded(
+                call,
+                self._llm,
+                system=system,
+                user=user,
+                tool_schema=INTENT_TOOL_SCHEMA,
             )
-            call.set_response(raw)
-            call.set_usage(llm_usage(self._llm))
         assert call.node is not None
         data = normalize_explicit_intent(command.text, parse_json(raw))
         parsed_outcome = outcome(data)
```
