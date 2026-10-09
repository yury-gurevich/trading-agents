<!-- Agent: planning | Role: sprint handover -->
# Sprint 264 — a reply cut off at the cap is recorded with its stop reason and its tokens, and the chat says so in one sentence, the same on both vendors

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-264-a-cut-off-reply-is-recorded-and-the-chat-says-so`
**Status:** MERGED 2026-10-10 — `0.125.02`, fast-forwarded to `cc050bba`, tag `v0.125.02`, GATE PROVEN `cc050bba` (CI, CodeQL, Security Findings); no deploy; F1a passed and F1b passed on OpenAI (a real cut-off, $0.0033); F1b on Anthropic is owed after its account is funded (2026-10-11)
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

- [x] On both vendors a cut-off reply's row holds the vendor's stop reason and token counts (A1, B1,
      C1, C2, D1).
- [x] The chat shows the one sentence for a cut-off `explain` and a cut-off `interpret`, on both
      vendors, and no part of the cut reply (C1, C2, D1, D2).
- [x] A cut-off `explain` writes its `CommandAudit` with outcome `explain`; a cut-off `interpret`
      writes one with outcome `refused`; neither records a fault (C1, C2).
- [x] An explicit approve keeps its grammar on a cut-off (C3).
- [x] A request that fails behaves exactly as on `main` (B4, C5, D3), and a vendor's refusal is not
      raised (A3).
- [x] `_AnthropicTransport`, `_AnthropicClient`, `AnthropicLLMClient` and every file the invariant
      names are unchanged; the command in the handback checklist prints nothing.
- [x] The law cycle done: `OPR-STA-03` reworded and re-proven, `OPR-FAIL-04` added and proven, the
      changelog, the version, the test-plan rows and footer, both rollups, DRIFT-106 CORRECTED.
- [x] Design decisions built as recorded in DL-285, or an amendment under it.
- [x] Every guard planted, watched to fail, restored, stated per guard.
- [x] Every touched or new module under 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage.

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
| Anthropic operator adapter | `agents/operator/laws/laws.md` and `test-plan.md`; `kernel/llm.py`; both `tests/test_llm_adapter_ownership.py` and `tests/test_llm_adapter_security.py`; `agents/deliberator/laws/laws.md` (whole, read-only) | `OPR-STA-03`, `OPR-SEC-01`; adapter port stop metadata; `DLIB-OUT-05`, `DLIB-FAIL-04`, `DLIB-OBS-05` protect the unchanged debate client | No: keep all three shared/debate classes byte-identical; set operator stop reason and usage before raising only for `max_tokens`. |
| Operator ledger | Whole operator law book and test plan; `docs/laws/conventions.md` and `drift-register.md` (whole) | `OPR-STA-03`, `OPR-OBS-02` | No: catch only `LLMCompletionStoppedError`; `OPR-OBS-02` is currently gray, not claimed proven by this sprint. |
| Operator agent and result parser | Whole operator law book and test plan; DL-285 and DL-284 including amendments 1 and 2 | `OPR-OUT-04/05/06`, `OPR-FAIL-01/02`, `OPR-IN-03`, `OPR-OBS-03`, `OPR-IDM-01`, `OPR-NEV-05`; new `OPR-FAIL-04` owed | No: audit cut-off explain as `explain` before returning; preserve explicit grammar and failed-request behavior. `OPR-OBS-03` and `OPR-IDM-01` are currently gray; neither rollup row is promoted here. |
| New dashboard chat tests and citation | `surfaces/laws/laws.md` and `test-plan.md` (whole) | `SRF-FAIL-02`, `SRF-OUT-03`, `SRF-OUT-05` | No: exercise the real adapters on fake SDKs through chat; no surfaces production or constitution change. The explicitly authorized `SRF-FAIL-02` test-plan citation is the only existing surfaces file to change. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No contracts changes; YES operator guarantee. Owed: amend `OPR-STA-03`, add/prove `OPR-FAIL-04`, bump operator v1.6, changelog, test-plan rows/footer, both derived rollups and DRIFT-106. Surfaces: citation only, no clause/version change. Reading completed and this record written before the first code change on 2026-10-10; implementation and proof not done at this point.

**Contradictions found between a law and this spec:** None blocking D1-D6. DRIFT-107 already records the failed-request audit gap, which remains outside scope. AGENTS.md says 14 CI steps while CLAUDE.md says 15 and explicitly explains that discrepancy; use the actual Makefile target. The sprint's explicit citation-only exception authorizes `surfaces/laws/test-plan.md` despite the broader invariant wording.

**Laws found silent where a decision was needed:** The cut-off guarantee is owed as new `OPR-FAIL-04`, already decided by DL-285 and tracked by DRIFT-106. No additional undecided silence found.

**Clauses that were ⬜ and are now proven:** No existing gray clause promoted. New `OPR-FAIL-04` is proven; `OPR-STA-03` is re-proven. Gate-derived operator 20 / 51 in both rollups; surfaces 30 / 37 unchanged.

**Pre-code workspace record:** `C:\Users\yury_\Downloads\project\ta-s264`, branch `sprint-264-a-cut-off-reply-is-recorded-and-the-chat-says-so`; clean at start. `HEAD`, `main`, and `origin/main` all `2680c962600133cd2f40efd80705396e9ebfe90e`. Active tracker per CLAUDE.md is `docs/STATE.md`; the handover forbids changing it, so sprint intent/evidence stays here. No push/merge/version bump; no existing test edits; all named invariant paths excluded. D1-D6 will be built as written, without a design-log amendment.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_anthropic_cutoff_records_metadata_before_raising` | `agents/operator/tests/test_cutoff_adapter.py` | PASS | OPR-STA-03 |
| A2 | `test_a2_finished_anthropic_reply_keeps_its_stop_reason` | `agents/operator/tests/test_cutoff_adapter.py` | PASS | OPR-STA-03 |
| A3 | `test_a3_anthropic_refusal_returns_without_raising` | `agents/operator/tests/test_cutoff_adapter.py` | PASS | OPR-STA-03 |
| A4 | `test_a4_failed_request_clears_anthropic_metadata` | `agents/operator/tests/test_cutoff_adapter.py` | PASS | OPR-STA-03 |
| B1 | `test_b1_cutoff_helper_records_usage_and_error_stop_reason` | `agents/operator/tests/test_cutoff_ledger.py` | PASS | OPR-STA-03 |
| B2 | `test_b2_finished_helper_records_response_stop_and_usage` | `agents/operator/tests/test_cutoff_ledger.py` | PASS | OPR-STA-03 |
| B3 | `test_b3_client_without_metadata_uses_stamped_estimates` | `agents/operator/tests/test_cutoff_ledger.py` | PASS | OPR-STA-03 |
| B4 | `test_b4_helper_propagates_failed_request_and_records_silence` | `agents/operator/tests/test_cutoff_ledger.py` | PASS | OPR-FAIL-01 |
| C1 | `test_c1_cutoff_explain_audits_before_returning_the_sentence` | `agents/operator/tests/test_cutoff_agent.py` | PASS | OPR-FAIL-04 / OPR-OUT-06 / OPR-STA-03 |
| C2 | `test_c2_cutoff_interpret_refuses_with_reason_and_linked_audit` | `agents/operator/tests/test_cutoff_agent.py` | PASS | OPR-FAIL-04 / OPR-OUT-05 / OPR-OBS-03 |
| C3 | `test_c3_explicit_approve_keeps_grammar_after_cutoff` | `agents/operator/tests/test_cutoff_agent.py` | PASS | OPR-FAIL-04 |
| C4 | `test_c4_finished_call_records_the_clients_stop_reason` | `agents/operator/tests/test_cutoff_agent.py` | PASS | OPR-STA-03 |
| C5 | `test_c5_failed_interpret_keeps_the_old_fault_and_refusal` | `agents/operator/tests/test_cutoff_agent.py` | PASS | OPR-FAIL-01 |
| C6 | `test_c6_cutoff_sentence_is_pinned_letter_for_letter` | `agents/operator/tests/test_cutoff_agent.py` | PASS | OPR-FAIL-04 |
| D1 | `test_d1_cutoff_chat_is_equal_on_both_vendors` | `surfaces/tests/test_chat_cutoff.py` | PASS | SRF-FAIL-02 / SRF-OUT-03 / OPR-FAIL-04 |
| D2 | `test_d2_partial_tool_answer_is_never_shown` | `surfaces/tests/test_chat_cutoff.py` | PASS | OPR-FAIL-04 |
| D3 | `test_d3_outage_distinguishes_failed_request_from_cutoff` | `surfaces/tests/test_chat_cutoff.py` | PASS | OPR-FAIL-01 / OPR-FAIL-04 |

**Tests added beyond the plan:** None: 17 planned functions, 30 parameterized cases. B1 additionally distinguishes the stopped error's reason from conflicting client metadata; it is still the planned helper proof.

---

## Closeout — evidence

**Status:** MERGED

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s264`, branch `sprint-264-a-cut-off-reply-is-recorded-and-the-chat-says-so`; `.env` absent. Every completion uses an injected SDK or stub, with no vendor called.

**Result:** The restored sprint suite passes 30 cases: both vendors' cut-offs keep billed usage and stop words, write linked audits without faults, show the fixed sentence and retain explicit approval grammar. Failed requests keep the old refusal/fault path. All 25 planted guard mutations fail on behavior and restore exact source bytes.

**Files changed:**

- `kernel/llm_anthropic.py`
- `agents/operator/ledger.py`
- `agents/operator/domain/result.py`
- `agents/operator/agent.py`
- `agents/operator/tests/cutoff_helpers.py`
- `agents/operator/tests/test_cutoff_adapter.py`
- `agents/operator/tests/test_cutoff_ledger.py`
- `agents/operator/tests/test_cutoff_agent.py`
- `surfaces/tests/chat_cutoff_helpers.py`
- `surfaces/tests/test_chat_cutoff.py`
- `agents/operator/laws/laws.md`
- `agents/operator/laws/test-plan.md`
- `surfaces/laws/test-plan.md`
- `docs/laws/INDEX.md`
- `docs/laws/ledger.md`
- `docs/laws/drift-register.md`
- `docs/sprints/README.md`
- `docs/sprints/sprint-264-a-cut-off-reply-is-recorded-and-the-chat-says-so.md`

**Design decisions:** recorded as [`DL-285`](../design-log.md) — built as written; no amendment.

**Proof — the red run first:**

```text
Command: uv run --no-sync pytest agents/operator/tests/test_cutoff_adapter.py surfaces/tests/test_chat_cutoff.py --no-cov -q
UV_OFFLINE=1; exit 1; before all production implementation edits.

FFFFFFF                                                                  [100%]
================================== FAILURES ===================================
____ test_a1_anthropic_cutoff_records_metadata_before_raising[False-False] ____
agents\operator\tests\test_cutoff_adapter.py:34: in test_a1_anthropic_cutoff_records_metadata_before_raising
    with pytest.raises(LLMCompletionStoppedError) as stopped:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE LLMCompletionStoppedError
____ test_a1_anthropic_cutoff_records_metadata_before_raising[False-True] _____
agents\operator\tests\test_cutoff_adapter.py:34: in test_a1_anthropic_cutoff_records_metadata_before_raising
    with pytest.raises(LLMCompletionStoppedError) as stopped:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE LLMCompletionStoppedError
____ test_a1_anthropic_cutoff_records_metadata_before_raising[True-False] _____
agents\operator\tests\test_cutoff_adapter.py:34: in test_a1_anthropic_cutoff_records_metadata_before_raising
    with pytest.raises(LLMCompletionStoppedError) as stopped:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE LLMCompletionStoppedError
_____ test_a1_anthropic_cutoff_records_metadata_before_raising[True-True] _____
agents\operator\tests\test_cutoff_adapter.py:34: in test_a1_anthropic_cutoff_records_metadata_before_raising
    with pytest.raises(LLMCompletionStoppedError) as stopped:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE LLMCompletionStoppedError
_____________ test_d1_cutoff_chat_is_equal_on_both_vendors[quick] _____________
surfaces\tests\test_chat_cutoff.py:31: in test_d1_cutoff_chat_is_equal_on_both_vendors
    assert turn["message"] == EXPECTED_REPLY
E   assert 'openai compl...output_tokens' == "The model's ...ing narrower."
E
E     - The model's reply was cut off at its output limit before it finished, so there is no answer. Ask again, or ask something narrower.
E     + openai completion stopped: stop_reason=max_output_tokens
_____________ test_d1_cutoff_chat_is_equal_on_both_vendors[parse] _____________
surfaces\tests\test_chat_cutoff.py:31: in test_d1_cutoff_chat_is_equal_on_both_vendors
    assert turn["message"] == EXPECTED_REPLY
E   assert 'Operator cou... the command.' == "The model's ...ing narrower."
E
E     - The model's reply was cut off at its output limit before it finished, so there is no answer. Ask again, or ask something narrower.
E     + Operator could not parse the command.
____________ test_d1_cutoff_chat_is_equal_on_both_vendors[answer] _____________
surfaces\tests\test_chat_cutoff.py:31: in test_d1_cutoff_chat_is_equal_on_both_vendors
    assert turn["message"] == EXPECTED_REPLY
E   assert 'openai compl...output_tokens' == "The model's ...ing narrower."
E
E     - The model's reply was cut off at its output limit before it finished, so there is no answer. Ask again, or ask something narrower.
E     + openai completion stopped: stop_reason=max_output_tokens
=========================== short test summary info ===========================
FAILED agents/operator/tests/test_cutoff_adapter.py::test_a1_anthropic_cutoff_records_metadata_before_raising[False-False]
FAILED agents/operator/tests/test_cutoff_adapter.py::test_a1_anthropic_cutoff_records_metadata_before_raising[False-True]
FAILED agents/operator/tests/test_cutoff_adapter.py::test_a1_anthropic_cutoff_records_metadata_before_raising[True-False]
FAILED agents/operator/tests/test_cutoff_adapter.py::test_a1_anthropic_cutoff_records_metadata_before_raising[True-True]
FAILED surfaces/tests/test_chat_cutoff.py::test_d1_cutoff_chat_is_equal_on_both_vendors[quick]
FAILED surfaces/tests/test_chat_cutoff.py::test_d1_cutoff_chat_is_equal_on_both_vendors[parse]
FAILED surfaces/tests/test_chat_cutoff.py::test_d1_cutoff_chat_is_equal_on_both_vendors[answer]
7 failed in 2.25s
```

**Proof — the green run:**

```text
Command: uv run --no-sync pytest agents/operator/tests/test_cutoff_adapter.py agents/operator/tests/test_cutoff_ledger.py agents/operator/tests/test_cutoff_agent.py surfaces/tests/test_chat_cutoff.py --no-cov -q
UV_OFFLINE=1; exit 0 after every mutation was restored and the fixture-key annotation.

..............................                                           [100%]
30 passed in 3.72s
```

**Guards planted:** Raw per-guard output is in `.tools/s264-proof/mutation-01.log` through `mutation-25.log`; the runner checks exit 1, resolved test failures and no collection errors, then verifies byte-for-byte restoration.

1. Anthropic raise removed: RED exit 1, 8 behavior failure(s), caught by `test_a1_anthropic_cutoff_records_metadata_before_raising`, `test_d1_cutoff_chat_is_equal_on_both_vendors`, `test_d2_partial_tool_answer_is_never_shown`; restored exact source bytes.
2. Anthropic raise before stop reason is kept: RED exit 1, 4 behavior failure(s), caught by `test_a1_anthropic_cutoff_records_metadata_before_raising`; restored exact source bytes.
3. Anthropic stop reason not reset before request: RED exit 1, 1 behavior failure(s), caught by `test_a4_failed_request_clears_anthropic_metadata`; restored exact source bytes.
4. Anthropic refusal raises too: RED exit 1, 2 behavior failure(s), caught by `test_a3_anthropic_refusal_returns_without_raising`; restored exact source bytes.
5. Wrong Anthropic cut-off word: RED exit 1, 4 behavior failure(s), caught by `test_a1_anthropic_cutoff_records_metadata_before_raising`; restored exact source bytes.
6. Other vendor stop word on Anthropic error: RED exit 1, 4 behavior failure(s), caught by `test_a1_anthropic_cutoff_records_metadata_before_raising`; restored exact source bytes.
7. Other vendor name on Anthropic error: RED exit 1, 4 behavior failure(s), caught by `test_a1_anthropic_cutoff_records_metadata_before_raising`; restored exact source bytes.
8. Helper usage not read on cut-off path: RED exit 1, 4 behavior failure(s), caught by `test_b1_cutoff_helper_records_usage_and_error_stop_reason`, `test_c1_cutoff_explain_audits_before_returning_the_sentence`; restored exact source bytes.
9. Helper stop reason not kept on cut-off path: RED exit 1, 2 behavior failure(s), caught by `test_b1_cutoff_helper_records_usage_and_error_stop_reason`; restored exact source bytes.
10. Helper stop reason not kept on finished path: RED exit 1, 3 behavior failure(s), caught by `test_b2_finished_helper_records_response_stop_and_usage`, `test_c4_finished_call_records_the_clients_stop_reason`; restored exact source bytes.
11. Helper usage not read on finished path: RED exit 1, 1 behavior failure(s), caught by `test_b2_finished_helper_records_response_stop_and_usage`; restored exact source bytes.
12. Helper response not kept: RED exit 1, 1 behavior failure(s), caught by `test_b2_finished_helper_records_response_stop_and_usage`; restored exact source bytes.
13. Every exception taken for a cut-off: RED exit 1, 4 behavior failure(s), caught by `test_b4_helper_propagates_failed_request_and_records_silence`, `test_c5_failed_interpret_keeps_the_old_fault_and_refusal`, `test_d3_outage_distinguishes_failed_request_from_cutoff`; restored exact source bytes.
14. Helper empty string instead of None: RED exit 1, 2 behavior failure(s), caught by `test_c1_cutoff_explain_audits_before_returning_the_sentence`; restored exact source bytes.
15. Cut-off explain returns before its audit: RED exit 1, 2 behavior failure(s), caught by `test_c1_cutoff_explain_audits_before_returning_the_sentence`; restored exact source bytes.
16. Cut-off explain audited as refused: RED exit 1, 2 behavior failure(s), caught by `test_c1_cutoff_explain_audits_before_returning_the_sentence`; restored exact source bytes.
17. Cut-off explain says No explanation returned: RED exit 1, 3 behavior failure(s), caught by `test_c1_cutoff_explain_audits_before_returning_the_sentence`, `test_d2_partial_tool_answer_is_never_shown`; restored exact source bytes.
18. Interpret calls the client directly: RED exit 1, 4 behavior failure(s), caught by `test_c2_cutoff_interpret_refuses_with_reason_and_linked_audit`, `test_c3_explicit_approve_keeps_grammar_after_cutoff`; restored exact source bytes.
19. Explain calls the client directly: RED exit 1, 3 behavior failure(s), caught by `test_c1_cutoff_explain_audits_before_returning_the_sentence`, `test_c4_finished_call_records_the_clients_stop_reason`; restored exact source bytes.
20. Cut-off parse has no reason: RED exit 1, 2 behavior failure(s), caught by `test_c2_cutoff_interpret_refuses_with_reason_and_linked_audit`; restored exact source bytes.
21. Cut-off parse asks for clarification: RED exit 1, 2 behavior failure(s), caught by `test_c2_cutoff_interpret_refuses_with_reason_and_linked_audit`; restored exact source bytes.
22. Cut-off sentence reworded: RED exit 1, 1 behavior failure(s), caught by `test_c6_cutoff_sentence_is_pinned_letter_for_letter`; restored exact source bytes.
23. Cut-off sentence names a vendor: RED exit 1, 1 behavior failure(s), caught by `test_c6_cutoff_sentence_is_pinned_letter_for_letter`; restored exact source bytes.
24. Cut-off sentence names the cap: RED exit 1, 1 behavior failure(s), caught by `test_c6_cutoff_sentence_is_pinned_letter_for_letter`; restored exact source bytes.
25. Helper cut-off reason read from client instead of error: RED exit 1, 2 behavior failure(s), caught by `test_b1_cutoff_helper_records_usage_and_error_stop_reason`; restored exact source bytes.

```text
01. RED exit 1; Anthropic raise removed; 8 behavior failure(s); restored exact bytes
02. RED exit 1; Anthropic raise before stop reason is kept; 4 behavior failure(s); restored exact bytes
03. RED exit 1; Anthropic stop reason not reset before request; 1 behavior failure(s); restored exact bytes
04. RED exit 1; Anthropic refusal raises too; 2 behavior failure(s); restored exact bytes
05. RED exit 1; Wrong Anthropic cut-off word; 4 behavior failure(s); restored exact bytes
06. RED exit 1; Other vendor stop word on Anthropic error; 4 behavior failure(s); restored exact bytes
07. RED exit 1; Other vendor name on Anthropic error; 4 behavior failure(s); restored exact bytes
08. RED exit 1; Helper usage not read on cut-off path; 4 behavior failure(s); restored exact bytes
09. RED exit 1; Helper stop reason not kept on cut-off path; 2 behavior failure(s); restored exact bytes
10. RED exit 1; Helper stop reason not kept on finished path; 3 behavior failure(s); restored exact bytes
11. RED exit 1; Helper usage not read on finished path; 1 behavior failure(s); restored exact bytes
12. RED exit 1; Helper response not kept; 1 behavior failure(s); restored exact bytes
13. RED exit 1; Every exception taken for a cut-off; 4 behavior failure(s); restored exact bytes
14. RED exit 1; Helper empty string instead of None; 2 behavior failure(s); restored exact bytes
15. RED exit 1; Cut-off explain returns before its audit; 2 behavior failure(s); restored exact bytes
16. RED exit 1; Cut-off explain audited as refused; 2 behavior failure(s); restored exact bytes
17. RED exit 1; Cut-off explain says No explanation returned; 3 behavior failure(s); restored exact bytes
18. RED exit 1; Interpret calls the client directly; 4 behavior failure(s); restored exact bytes
19. RED exit 1; Explain calls the client directly; 3 behavior failure(s); restored exact bytes
20. RED exit 1; Cut-off parse has no reason; 2 behavior failure(s); restored exact bytes
21. RED exit 1; Cut-off parse asks for clarification; 2 behavior failure(s); restored exact bytes
22. RED exit 1; Cut-off sentence reworded; 1 behavior failure(s); restored exact bytes
23. RED exit 1; Cut-off sentence names a vendor; 1 behavior failure(s); restored exact bytes
24. RED exit 1; Cut-off sentence names the cap; 1 behavior failure(s); restored exact bytes
25. RED exit 1; Helper cut-off reason read from client instead of error; 2 behavior failure(s); restored exact bytes
25/25 guards red; all source bytes restored.
```

**Module line counts:** All ten touched/new Python modules are below 200 lines.

```text
agents/operator/agent.py: 168 lines
agents/operator/domain/result.py: 100 lines
agents/operator/ledger.py: 75 lines
agents/operator/tests/cutoff_helpers.py: 145 lines
agents/operator/tests/test_cutoff_adapter.py: 121 lines
agents/operator/tests/test_cutoff_agent.py: 150 lines
agents/operator/tests/test_cutoff_ledger.py: 102 lines
kernel/llm_anthropic.py: 168 lines
surfaces/tests/chat_cutoff_helpers.py: 74 lines
surfaces/tests/test_chat_cutoff.py: 107 lines
```

**Law cycle — verbatim clauses, plan rows and drift status:**

```text
Operator law book: LOCKED v1.6 -> LOCKED v1.7.

- **OPR-STA-03** — Every LLM call is recorded in an `LLMCall` graph node via `record_llm_call`
  context manager (model, prompt, response, timestamp). The row carries the vendor's own stop
  reason and token counts whether the reply finished or the vendor cut it off. A client that
  exposes neither is recorded as `unknown` with a stamped estimate.

- **OPR-FAIL-04** — A reply the vendor cut off at the output cap is neither a fault nor an
  answer. It is recorded as `OPR-STA-03` says; `interpret` reads it as a refusal whose reason
  is `CUT_OFF_REPLY`, and the explicit command grammar still applies; `explain` returns
  `CUT_OFF_REPLY`; no part of the cut reply is shown; the `CommandAudit` is written and linked
  to its `LLMCall` as for any reply; the same on every vendor. `CUT_OFF_REPLY` is:
  "The model's reply was cut off at its output limit before it finished, so there is no answer.
  Ask again, or ask something narrower."

agents/operator/laws/test-plan.md
| OPR-STA-03 | 🟩 | Every call records model, prompt, response and timestamp; the vendor's stop reason and counts survive finished and cut-off replies; clients exposing neither retain unknown with a stamped estimate: `test_explain_returns_text_and_writes_audit_and_llm_call`; `agents/operator/tests/test_cutoff_adapter.py::test_a1_anthropic_cutoff_records_metadata_before_raising`; `test_a2_finished_anthropic_reply_keeps_its_stop_reason`; `test_a4_failed_request_clears_anthropic_metadata`; `agents/operator/tests/test_cutoff_ledger.py::test_b1_cutoff_helper_records_usage_and_error_stop_reason`; `test_b2_finished_helper_records_response_stop_and_usage`; `test_b3_client_without_metadata_uses_stamped_estimates`; `agents/operator/tests/test_cutoff_agent.py::test_c1_cutoff_explain_audits_before_returning_the_sentence`; `test_c4_finished_call_records_the_clients_stop_reason` |
| OPR-FAIL-04 | 🟩 | A vendor cut-off is neither a fault nor an answer; recorded under OPR-STA-03; interpret refuses with CUT_OFF_REPLY through the explicit grammar; explain returns that sentence; no partial reply is shown; CommandAudit links to LLMCall as for any reply, on every vendor: `agents/operator/tests/test_cutoff_agent.py::test_c1_cutoff_explain_audits_before_returning_the_sentence`; `test_c2_cutoff_interpret_refuses_with_reason_and_linked_audit`; `test_c3_explicit_approve_keeps_grammar_after_cutoff`; `test_c6_cutoff_sentence_is_pinned_letter_for_letter`; `surfaces/tests/test_chat_cutoff.py::test_d1_cutoff_chat_is_equal_on_both_vendors`; `test_d2_partial_tool_answer_is_never_shown`; `test_d3_outage_distinguishes_failed_request_from_cutoff` |

surfaces/laws/test-plan.md
| SRF-FAIL-02 | Chat, MCP, and operator-tool errors reach the operator in plain words, not raw SDK JSON or tracebacks. | `surfaces/tests/test_dashboard_chat.py::test_chat_unbound_invalid_requests_and_method_guard`; `surfaces/tests/test_mcp_server.py::test_command_tool_refusal_returns_reason`; `surfaces/tests/test_mcp_server.py::test_error_paths_and_tool_catalog`; `surfaces/tests/test_chat_cutoff.py::test_d1_cutoff_chat_is_equal_on_both_vendors` | 🟩 |

DRIFT-106 new status cell:
**CORRECTED (S264 / DL-285, operator v1.7, 2026-10-10).** Vendor stop reasons and billed usage survive both reply paths; cut-offs write linked audits without a fault or partial answer and show the same fixed sentence. Proven by `agents/operator/tests/test_cutoff_adapter.py`, `test_cutoff_ledger.py`, `test_cutoff_agent.py` and `surfaces/tests/test_chat_cutoff.py` (A1-A4, B1-B4, C1-C6, D1-D3). `OPR-STA-03` amended and `OPR-FAIL-04` added/proven. DRIFT-107 remains outside scope.
```

**Law gate:** `uv run --no-sync python scripts/check_law_coverage.py`, exit 0; `.tools/s264-proof/law.log` has empty stdout. The gate is quiet on success, including inside `make ci`; it prints no rollup lines. The following separate measurement uses its own `_derived_counter(discover_agent_books(Path.cwd()))` helper and reads the actual two rollup rows:

```text
operator: derived 20 / 51
surfaces: derived 30 / 37
docs/laws/ledger.md: | operator | ✅ v1.7 (LOCKED) | 20 / 51 | 🟨 partial — **20 of 51 clauses proven** after S264 (DL-285) re-proves `OPR-STA-03` for vendor stop reasons and billed counts on both reply paths and adds/proves `OPR-FAIL-04` for audited, fault-free cut-offs with one sentence and explicit grammar preserved; DRIFT-106 corrected; before that S263 (DL-284) amends and re-proves `OPR-DEP-01` for provider effort resolution and pre-call model-family refusal; PARAM effort and CAP reconciled; before that S262 (DL-282) amends and re-proves `OPR-DEP-01` for the selected vendor, model resolution and no fallback; PARAM reconciled; before that S256 (DL-272) rewrites and proves `OPR-IDM-02`: duplicate commands share audit/intent while every model call has its own row; DRIFT-104 corrected; S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; 31 have a gray row |
docs/laws/INDEX.md: | operator | ✅ LOCKED v1.7 (S264, DL-285) | 20 / 51 | S264 (DL-285) re-proves `OPR-STA-03` for vendor stop reasons and billed counts on both reply paths and adds/proves `OPR-FAIL-04` for audited, fault-free cut-offs with one sentence and explicit grammar preserved; DRIFT-106 corrected; before that S263 (DL-284) amends and re-proves `OPR-DEP-01` for provider effort resolution and pre-call model-family refusal; PARAM effort and CAP reconciled; before that S262 (DL-282) amends and re-proves `OPR-DEP-01` for the selected vendor, model resolution and no fallback; PARAM reconciled; before that S256 (DL-272) rewrites and proves `OPR-IDM-02`: duplicate commands share the audit and intent, but every model call has its own ledger row; DRIFT-104 corrected; S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; counters are clauses proven / clauses declared |
```

**Scope proof:** Exact requested command, against unchanged `main` at the branch's starting commit; no protected-path diff. Existing tests edited: none. No vendor was called. `pyproject.toml` and `uv.lock` are unchanged; the planner owns the version bump.

```text
git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration/history_window.py orchestration/packs kernel/llm.py kernel/llm_ledger.py kernel/llm_tokens.py kernel/llm_factory.py kernel/llm_outage.py kernel/llm_openai.py kernel/llm_openai_operator.py kernel/llm_anthropic_responses.py agents/deliberator surfaces/dashboard surfaces/queries surfaces/context.py surfaces/operator_tools.py surfaces/mcp_tools.py surfaces/laws/laws.md pyproject.toml uv.lock docs/STATE.md docs/work-queue.md
Exit 0; stdout is empty. Reference main = 2680c962600133cd2f40efd80705396e9ebfe90e.
_AnthropicTransport: byte-for-byte unchanged.
_AnthropicClient: byte-for-byte unchanged.
AnthropicLLMClient: byte-for-byte unchanged.
Existing tests edited: none.
pyproject.toml and uv.lock unchanged; version bump belongs to the planner.
.env present: False
No vendor called; all completion tests inject SDKs or stub clients.
```

**Entire `git diff main -- kernel/llm_anthropic.py`:**

```diff
diff --git a/kernel/llm_anthropic.py b/kernel/llm_anthropic.py
index 40c9e810..cf0ebfdd 100644
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
```

**`make ci`:** `make ci > ci.txt 2>&1` in `C:\Users\yury_\Downloads\project\ta-s264`, with `UV_OFFLINE=1`, `PYTHONUTF8=1` and `PYTHONPATH=.tools/s264-proof/offline`. Exit **2**, verified failing overall. Steps 1-12 passed, including **4,588 passed, 8 skipped, 100.00 % coverage**. Step 13, dependency audit, is **NOT RUN to completion**: the offline socket guard blocked the required PyPI query before any external network access. Steps 14 and 15 were not reached by `make ci`; both exact commands were then run separately and passed. No gate or coverage floor was bypassed or changed. Actual output excerpt:

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 1179 source files
uv run lint-imports
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
docs_seen=268 SPEC=10 BUILT=1 MERGED=257 UNMAPPED=0 MISSING=0
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
TOTAL                                                           20205      0   4278      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 4588 passed, 8 skipped, 2470 warnings in 473.02s (0:07:53) ==========
uv run python scripts/check_dependency_audit.py
OSError: S264 offline proof blocks external network
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: S264 offline proof blocks external network"))
make: *** [Makefile:59: ci] Error 1
MAKE_CI_EXIT=2
```

**Remaining local security steps:** `UV_OFFLINE=1` and the offline guard remained set; cached pre-commit hooks also ran with Git protocols denied and npm offline.

```text
Command: uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
DETECT_SECRETS_EXIT=0

Command: uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
UNTRACKED_SECRETS_EXIT=0
```

The first detect-secrets run flagged the fixed `fixture-key` equality in the new test helper. It now has the same inline fixture allowlist annotation as its constructor argument. `.secrets.baseline` is unchanged. This annotation came after the full CI run; its executable AST and line count are identical, and the restored 30-case sprint suite plus the security check passed after it. No production change followed the full coverage run.

**`make gate-ran`:** **NOT RUN** — the handover forbids pushing and the worktree is offline. No remote gate, merge or deployment is claimed.

**Not met / verified failing:** `make ci` exit 0 is **not done**; the actual exit is **2**, verified failing at the offline dependency audit. Dependency vulnerability results are **NOT RUN**. Push, remote gates, merge, version bump, deploy, live vendor calls and the planner's post-merge F1/F2 proofs are **not done**, as instructed. No implementation or local behavior proof remains unfilled.

---

## Return notes

- Scope held: D1-D6 built as DL-285 records them, without an amendment. No contracts, surfaces production, debate plumbing, cap, retry or failed-request audit change. The sole existing surfaces edit is the explicitly authorized `SRF-FAIL-02` citation. No existing test was edited; no vendor was called; no `.env` is present.
- No law contradicted D1-D6. `OPR-OBS-02`, `OPR-OBS-03` and `OPR-IDM-01` remain gray; this work proves the new `OPR-FAIL-04` and re-proves `OPR-STA-03`. DRIFT-106 is corrected; DRIFT-107's failed-request audit gap is unchanged.
- Corrections to the spec's mechanical expectations: the actual Makefile and CLAUDE.md have 15 steps, despite AGENTS.md's 14; the law gate is quiet on success, so the rollups above were measured separately rather than attributed to CI stdout. The two later security steps were run separately because dependency auditing cannot finish offline. The full CI result remains failing.
- No build decision remains uncertain. The faked SDK tests prove local behavior, not a live Anthropic partial-tool shape or paid-call behavior. The planner still owns the PATCH bump at merge, remote gates, deployment, F1 and F2. Preserve the distinction between a billed cut-off and a failed request, and keep both explicit command grammar and the linked `explain` audit.

---

## Planner's review at the merge — 2026-10-10

Re-measured by the planner in `../ta-s264`, not taken from the handback.

- **Scope.** The checklist's scope command against `main` (`2680c962`, which has not moved) prints
  nothing: no fidelity decision path, no pack, no tracker, no version file, no production file of
  the surfaces. In `kernel/llm_anthropic.py` the diff is one import, one constant and the operator's
  class; the debate's three classes are untouched. No existing test was edited: the ten Python
  files changed are the four production modules and six new test files. Every changed file is LF.
- **The code is the measured prototype**, line for line: every added and every removed line of the
  four production modules equals the prototype's (58 added, 14 removed).
- **The measurement on the built code.** The planner's end-to-end script (each real adapter on a
  fake SDK through the chat handler, 21 cases, 23 ledger rows) prints on the built code exactly what
  it printed on the prototype: the sentence for every cut-off case on both vendors, the vendor's
  counts and stop word on the row, the audits, no fault; the eight failed-request cases as on `main`.
- **Guards.** 31 things broken one at a time against the builder's four test files, each restored
  and the tree left clean: **31 went red, no gap.** The 23 of the spec, and eight the builder was
  not given: a cut-off `interpret` refusing before the normaliser and the audit; no stop reason
  before the first call; the usage dropped before the raise; a cut-off `explain` recording a fault;
  the finished path writing a fixed stop word; `interpret`'s reason being a different sentence; the
  cut-off path keeping a response text; the raise only when no tool block came back.
- **The tests, read.** 17 functions, 30 cases, each citing its clause. D1 writes the sentence out
  and compares what was observed on the two vendors. The surfaces' tests import the operator's
  test helper, as the orchestration tests import agents' helpers.
- **One change made by the planner on the branch.** `OPR-FAIL-04` as built quoted the sentence
  inside the law. The law now says what the sentence must be (one fixed sentence that says the reply
  was cut off and names no vendor, model, number or the word *token*) and leaves its letters to the
  test that pins them: two copies of one text, with no gate comparing them, drift. The clause's
  other assertions and its test-plan row are as built. The Closeout above quotes the clause as the
  builder wrote it.
- **Seen and accepted.** `test_c5_failed_interpret_keeps_the_old_fault_and_refusal` and
  `test_d3_outage_distinguishes_failed_request_from_cutoff` assert that a failed request writes no
  `CommandAudit`. That is today's behaviour, which this sprint was told to keep, and it is DRIFT-107:
  the sprint that closes work-queue 125 edits those two assertions. The handback's `make ci` stopped
  at the dependency audit, which needs the network the builder does not have; the planner's Windows
  run is the proof.
- **Version.** PATCH, `0.125.01` to `0.125.02`; `uv lock` changed the version line alone (180
  packages).

**The gate and the merge.** Windows `make ci` exit 0 on the branch: all 15 steps, 4,588 passed, 8
skipped, 100.00 % coverage, and the dependency audit the builder could not run found nothing
unaccepted (one accepted advisory re-checked). `GATE PROVEN` for `cc050bba`, run from `../ta-s264`,
the printed SHA equal to its `HEAD`: CI, CodeQL and Security Findings each `success`. Open CodeQL
alerts on the branch: 127, the same alert numbers as on the last merged branch, none at error level
and none in a file this sprint touched. `main` fast-forwarded to that commit and tagged `v0.125.02`.

**After the merge, 2026-10-10 ([functionality checks](../laws/functionality-checks.md)).** *F1a passed*
on the merged `main`, from the main checkout, at no cost: the planner's end-to-end script prints
exactly what it printed on the prototype. On both vendors every cut-off question shows the one
sentence, each cut-off row holds the vendor's 21,133 and 4,096 with `max_output_tokens` or
`max_tokens`, the audits read `explain`, `refused`, and `intent` then `explain`, there is no fault,
and an explicit approve asks for confirmation; the eight failed-request turns read as before the
sprint. *F1b passed on OpenAI* (the operator: *"go for it"*): one paid call, $0.0033, `gpt-5.5` at
`xhigh` with the cap at 64, a typed question through the chat handler on an in-memory graph. The
vendor answered `incomplete`, `max_output_tokens`, one reasoning item, 278 in and 64 out. The chat
showed the sentence; the row reads `max_output_tokens`, 278, 64, `vendor`, and the outage check does
not read it silent; the `CommandAudit` reads `refused`; no fault. The same call on the code before
the sprint (the Measured table) gave *"Operator could not parse the command."*, a row of 13 and 0
stamped `estimated`, no audit and a fault. *Owed:* F1b on Anthropic after its account is funded
(2026-10-11), on the operator's word. *Not proven:* a reply cut at the real cap of 4,096 on the
21,000-token explain prompt; a reply cut inside a function call's arguments or a tool block.

**Written at the merge, before the gate — what was still owed then:** the planner's
Windows `make ci`, the remote gate and the CodeQL set-diff for the commit that holds this block;
then F1a (the measurement on the merged `main`, at no cost) and F1b (one paid cut-off on OpenAI on
the built code, on the operator's word; Anthropic's after its account is funded).

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
