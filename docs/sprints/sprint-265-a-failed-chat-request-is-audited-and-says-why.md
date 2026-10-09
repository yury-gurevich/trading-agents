<!-- Agent: planning | Role: sprint handover -->
# Sprint 265 — a model request that fails in the operator's chat is audited and answered with one message that says why, the same for the quick ask and a typed question on both vendors

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-265-a-failed-chat-request-is-audited-and-says-why`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-286](../design-log.md) (this sprint's seven decisions, made and measured) · [DL-285](../design-log.md) (where the defect was found) · [work-queue 125](../work-queue.md) · DRIFT-107 · DRIFT-108

> **Why this bump kind.** No new capability: the operator's law already says every call has a
> `CommandAudit` and a failed call is refused and recorded, and for a request that fails the code
> writes no audit and a typed question hides the reason. A fix, so PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/operator/laws/laws.md` | The operator's **locked constitution** | **LOCKED.** This sprint amends it under a law cycle, named below. Any other clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `surfaces/laws/laws.md` | The surfaces' locked constitution | **LOCKED, read-only.** No clause of it changes in this sprint |
| `agents/operator/laws/test-plan.md`, `surfaces/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: operator **`FAIL`**, **`OUT`**, **`STA`**, **`OBS`**, **`NEV`**, **`SEC`**,
**`IN`**; surfaces **`FAIL`**, **`OUT`**.

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

**No file in `contracts/` changes, and none may. Yes, the operator's guarantee for a failed request
grows**, so one law cycle is owed in this unit of work. **No clause is added: `OPR-FAIL-01` is
reworded**, so the operator's count stays where it is.

| Book | From | What the cycle owes |
| --- | --- | --- |
| `agents/operator/laws/laws.md` | LOCKED v1.7 | **`OPR-FAIL-01` reworded** to the text under *The clause* below. Changelog line, version up. No other clause changes |
| `agents/operator/laws/test-plan.md` | 20 / 51 | `OPR-FAIL-01`'s row cites the tests that prove each thing the reworded clause asserts. `OPR-OUT-06`'s row gains C1 and C2 (a call that failed is audited too). The footer stays 20 / 51 |
| `surfaces/laws/test-plan.md` | 30 / 37 | `SRF-FAIL-02`'s row gains D1 and D2 as citations. **No clause and no version of the surfaces book changes** |
| `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` | operator 20 / 51 | The operator's line, in both, names this sprint and the new version; the count does not move |
| `docs/laws/drift-register.md` | DRIFT-107 and DRIFT-108 are OPEN | Both status cells become CORRECTED, naming this sprint and the tests. Leave DRIFT-109 as it is: it belongs to work-queue 126 |

🪤 **The law gate does not check each citation.** Measured 2026-10-10: a test that does not exist,
added to `OPR-OUT-06`'s row beside its two live ones, leaves `scripts/check_law_coverage.py` at
**exit 0**. The gate asks that a green row has one live test whose docstring names the clause, not
that every cited test exists. So the handback lists each cited test with its file, and the planner
resolves each one by hand.
🪤 **The gate does not read the test plan's own footer** (measured for S264): leave it at 20 / 51.

#### The clause

Write `OPR-FAIL-01` as this, wrapped as the book wraps its lines:

> **OPR-FAIL-01** — A model request that fails (a network error, a time-out, a status the vendor
> refuses the request with: anything the client raises other than the cut-off of `OPR-FAIL-04`) is a
> fault and never an answer, for `interpret` and for `explain`, on every vendor. `fault_boundary`
> captures it around the model call alone: one fault, carrying the error's own type, and nothing
> raised to the bus. The call is recorded as `OPR-STA-03` says and its `CommandAudit` is written and
> linked as for any call (`OPR-OUT-06`), with outcome `refused` for `interpret` and `explain` for
> `explain`. `interpret` returns `CommandResult(outcome="refused", ...)` and `explain` an
> `Explanation`, each carrying the failed-request message; the explicit command grammar is not
> applied and no `Intent` is written. The failed-request message is one fixed sentence that says the
> request failed and names no vendor, model or number, followed by the error's own reason in plain
> words: the HTTP status and the vendor's message for a status error, the error's text otherwise,
> the error's type when it has no text. The SDK's rendering of a status error is never shown, and
> the error's text is written to no graph record. Its letters are pinned by tests, not quoted here.
> A model reply that is not valid JSON is not a fault: it is the explained refusal of `OPR-OUT-05`.
> A graph write that fails is `OPR-FAIL-03`'s.

The clause it replaces listed *malformed JSON* among the failures that emit a fault. Measured: it
emits none (DRIFT-108). The reworded clause says so; nothing in the code changes for it.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `kernel/llm_error_text.py` (**new**) | No law book governs the kernel. `docs/laws/conventions.md`; the import contract *"Kernel is pure plumbing"* in `pyproject.toml`; `surfaces/laws/laws.md` (`SRF-FAIL-02`: the text this module reads is the text the surface rewords); `surfaces/plain_errors.py`, whole | The pattern moves here from the surface **unchanged, character for character**. The module names no agent and no trading concept |
| `surfaces/plain_errors.py` | `surfaces/laws/laws.md` + `test-plan.md`; `surfaces/tests/test_status_fleet_check.py` (read its three `plain_error` tests) | `SRF-FAIL-02` (errors reach the operator in plain words), `SRF-OUT-05` (no sprint, design-log, drift or law id in operator-facing text). `plain_error` returns what it returns today for every input |
| `agents/operator/ledger.py` | `agents/operator/laws/laws.md` + `test-plan.md`; the docstring of `fault_boundary` in `kernel/errors.py` | `OPR-STA-03` (every call recorded), `OPR-FAIL-01`, `OPR-FAIL-03` (a graph write that fails is its own fault) |
| `agents/operator/agent.py` | the same | `OPR-OUT-04`, `OPR-OUT-05`, `OPR-OUT-06` (a `CommandAudit` for **every** call, linked to its `LLMCall`), `OPR-FAIL-01`, `OPR-FAIL-04` (the cut-off, unchanged), `OPR-IN-03` (never raises to the bus), `OPR-OBS-03` (a refusal is recorded), `OPR-IDM-01` |
| `agents/operator/domain/result.py` | the same | `OPR-OUT-05`, `OPR-NEV-06` and `OPR-SEC-02` (no credential and no raw text in the graph beyond what `LLMCall` records) |
| `agents/operator/tests/`, `surfaces/tests/` (new test files, and **three named existing tests**) | both books' `test-plan.md` | the clauses above; `SRF-OUT-03` (a model-composed answer records its audit and ledger facts) |

⚠️ **The one invariant this sprint must not break: a reply that came back, cut off or whole, is
handled exactly as on `main`, and nothing of an error's text reaches the graph.**
`complete_recorded` in `agents/operator/ledger.py` stays as it is. Every `kernel/llm*.py` that
exists today, `kernel/bus.py`, `kernel/errors.py`, everything under `agents/deliberator/`,
`agents/operator/store.py`, `agents/operator/settings.py`, `agents/operator/domain/grammar.py`,
`agents/operator/domain/prompts.py`, every production file under `surfaces/` other than
`surfaces/plain_errors.py`, and `contracts/` do not change. Nor does any file under a fidelity
decision path: `agents/scanner/`, `agents/analyst/`, `agents/portfolio_manager/`,
`agents/provider/domain/`, `agents/execution/order_tolerance.py`,
`orchestration/packs/trading_tunables.json`, `orchestration/packs/trading_issuer_map.json`,
`orchestration/history_window.py`. **If your build needs one of these changed, stop and report.**

---

## Goal

At merge, when the operator's model request fails, on OpenAI or on Anthropic, for the quick ask
*explain this run* or for a typed question: the `LLMCall` row is written as today; a `CommandAudit`
is written and linked to it (`explain` for an explain call, `refused` for an interpret call); one
fault is recorded with the error's own type; nothing is raised to the bus; and the chat shows one
message that says the request failed and why, the same words on both paths and both vendors. A reply
that came back, whole or cut off, behaves exactly as today.

## Why (context)

Found while measuring [S264](sprint-264-a-cut-off-reply-is-recorded-and-the-chat-says-so.md)
([DL-285](../design-log.md)), which left it alone on purpose. When the request itself fails, the
operator writes no `CommandAudit` for either capability, although `OPR-OUT-06` says every call has
one. The quick ask shows the error's text; a typed question says *"Operator could not parse the
command."* and the reason is shown nowhere. So when a vendor's account runs out of credit, as
Anthropic's did on 2026-10-06, the quick ask says so and a typed question does not.

Measured again for this sprint, with one thing S264's measurement did not plant: an error that has
no text. The quick ask then shows an empty message.

The cost of leaving it: the first vendor outage the operator meets in the chat reads as their own
typing mistake, and the graph holds a model call with no record of what was asked.

### Measured, 2026-10-10 — read these before designing

Scripts, their outputs and the prototype's diff are outside the repository
(`trading-agents-data/wq125-2026-10-10/`). The builder cannot reach them and does not need to: what
matters is in this file, and the prototype is in the Appendix. Everything below was run in this
sprint's worktree, which has no `.env`, on `main` at `f3e37421`, with no call to a vendor, unless a
row says otherwise. Each real operator adapter was built by `build_operator_llm` on a fake SDK,
bound by `build_test_context`, and each turn went through `surfaces.dashboard.chat.handle_chat`.

| Claim | Value | How it was measured |
| --- | --- | --- |
| The quick ask, the request times out, today | chat: `refused`, *"Request timed out."*. Row: `unknown`, 0 out, `estimated`, read silent by the outage check. **No `CommandAudit`.** One fault, recorded by `kernel.bus` | *[measured]* `wq125_failed_request_paths.py`, both vendors alike |
| The quick ask, the vendor answers HTTP 400, today | chat: `refused`, *"The language model refused the request (HTTP 400): Your credit balance is too low to access the API."* (the surface's `plain_error` rewords it). **No `CommandAudit`.** Fault from `kernel.bus` | *[measured]* |
| The quick ask, an error with no text, today | chat: `refused`, **an empty message**. **No `CommandAudit`** | *[measured]* a bare `TimeoutError()` planted. Not seen from a vendor |
| A typed question, any of the three failures, today | chat: `refused`, *"Operator could not parse the command."*, the reason shown nowhere. **No `CommandAudit`.** One fault, from the agent's own boundary | *[measured]* |
| A typed question parsed, then its answer's request fails, today | chat: the reworded vendor line. One `CommandAudit` (`intent`) and one `Intent` (`explain`); **the explain call has no audit** | *[measured]* |
| An explicit `approve flag-12` whose request fails, today | `refused`, *"Operator could not parse the command."*; no audit, no `Intent` | *[measured]* |
| The unattended scorecard, today | counts **no** human action for any failed request (there is no audit to count); counts one `command` for a typed question whose reply was cut off | *[measured]* the same script calls `surfaces.queries.scorecard_actions.human_actions` on each case's graph |
| Who reads a `CommandAudit` | the operator's store, the contract's `owns_graph`, and `surfaces/queries/scorecard_actions.py`: an audit with no `Intent` whose outcome is not `explain` counts as a human action | *[measured]* `grep -rn CommandAudit` over every tracked `.py` outside tests; `_acts` read whole |
| Who asks the operator to `interpret` or `explain` | `surfaces/operator_tools.py` (the dashboard chat and the MCP `command` and `explain` tools) and the command line (`surfaces/cli_commands.py`, `cli_commands_extra.py`), which binds the fake client | *[measured, read]* `grep` for the two capability names; each caller read |
| What each vendor's SDK renders for a refused request | OpenAI 2.49.0: `Error code: 401 - {'error': {'message': 'Incorrect API key provided: not-a-ke***q125. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_api_key'}}`. Anthropic 0.120.2: `Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error', 'message': 'invalid x-api-key'}, 'request_id': 'req_...'}`. The surface's pattern reads the status and the message from both | *[measured 2026-10-10, the main checkout, one request a vendor with a key that is not a key: answered HTTP 401, nothing billed]* `real_status_error_texts.py` |
| What each SDK renders for a time-out | OpenAI: `Request timed out.`. Anthropic: `Request timed out or interrupted. This could be due to a network timeout, dropped connection, or request cancellation. See https://docs.anthropic.com/en/api/errors#long-requests for more details.` | *[measured]* the same script, a client given a time-out of one millisecond |
| OpenAI's message for a wrong key repeats the key, masked | the first eight and the last four characters of the key are in the vendor's message | *[measured]* the row above. The quick ask shows it today. It is written to no graph record, before or after this sprint |
| Anthropic's text for an empty account | `Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API.'}, 'request_id': 'req_011'}` | *[carried]* the `_DRAINED` fixture of `surfaces/tests/test_status_fleet_check.py`, captured on 2026-10-06. Not re-produced |
| A body that is not JSON | OpenAI's SDK uses the response's raw text as the error's text, or `Error code: <status>` alone | *[read]* `openai/_base_client.py`, `_make_status_error_from_response`, in the worktree's environment. **Not handled by this sprint:** such a text is shown as it is, as today |
| A model reply that is not valid JSON | refused with a reason, a `CommandAudit` (`refused`), **0 faults**, for `not json at all`, `[1, 2]` and an empty reply | *[measured]* `malformed_json_fault.py`. `OPR-FAIL-01` lists it among the failures that emit a fault: DRIFT-108 |
| A prototype of the whole change | five files, 129 lines added and 48 removed (Appendix). After it, on both vendors, for a time-out, an HTTP 400 and an error with no text: the quick ask and a typed question show the same message; a `CommandAudit` (`explain`, or `refused`) linked to the failed row; one fault from `agents.operator.agent` with the error's own type; no `Intent`; the row still read silent. A typed question parsed and then failed: audits `intent` and `explain`. An explicit approve: refused with the message | *[measured]* the same script on the prototype; the two outputs were diffed |
| What the prototype leaves alone | a cut-off quick ask, a cut-off typed question, a good quick ask, a good typed question, on each vendor: **every printed line identical before and after** | *[measured]* the four control cases a vendor in the same script |
| What the prototype changes beyond the headline | the turn's outcome word for a failed quick ask goes from `refused` to `answer` (an `Explanation` has no outcome of its own; the cut-off reads `answer` since S264); a failed typed question now counts as one `command` on the scorecard, as a cut-off one does | *[measured]* the diff of the two outputs |
| Existing tests the prototype breaks | **Exactly three functions, four cases, of 4,588**: `test_interpret_llm_exception_returns_refusal`, `test_c5_failed_interpret_keeps_the_old_fault_and_refusal`, `test_d3_outage_distinguishes_failed_request_from_cutoff` (both vendors). 4,584 passed, 8 skipped | *[measured]* the whole suite on the prototype, 412 seconds, no coverage |
| Prototype tests for the Test plan's rows | 22 functions, 48 cases, pass on the prototype, with the three edited tests' new assertions aside; the measured vendor texts are among their fixtures | *[measured]* three files outside the repository (`proto_test_failed_request.py`, `proto_test_failed_request_extra.py`, `proto_test_chat_failed.py`), run with the surface's three `plain_error` tests and S264's two chat tests: 59 passed |
| The prototype broken 32 ways, one at a time | **32 red, none survived.** The break and the tests that caught it are in the handback checklist, item 4 | *[measured]* `planner_mutations.py`. A first run of 30 read 29: one break changed nothing (removing `^` from a pattern used with `match`); it was replaced by a break that does |
| `ruff`, `ruff format`, `mypy`, the import contracts on the prototype | clean over the whole tree; 5 import contracts kept. `agents/operator/agent.py` **174** lines, `agents/operator/ledger.py` **111**, `agents/operator/domain/result.py` **123**, `kernel/llm_error_text.py` **27**, `surfaces/plain_errors.py` **19** | *[measured]* |
| The header check reads test files | a test file under `agents/` or `surfaces/` with no `Agent:` and `Role:` in its docstring fails `scripts/check_module_header.py` | *[measured]* the planner's two prototype test files failed it |
| The law gate on a dead citation | exit 0 (the trap above) | *[measured]* `scripts/check_law_coverage.py`, the test plan restored after |
| Anything a vendor does on a real failure in the chat | **not measured.** No request has failed in the dashboard chat on the live ledger's record: its nine operator rows are all good replies | *[carried from S264, 2026-10-09]* the live ledger read; not re-read |

---

## Scope — and what is deliberately NOT here

1. **The status-error pattern moves to the kernel (D3).** New `kernel/llm_error_text.py` with
   `vendor_status_error`; `surfaces/plain_errors.py` uses it and says what it said.
2. **One helper makes the call inside the caller's fault boundary (D1).**
   `agents/operator/ledger.py` gains `recorded_completion`.
3. **The message (D2).** `agents/operator/domain/result.py` gains `FAILED_REQUEST_REPLY`,
   `failed_request_reply` and `failed_request`.
4. **The agent's two call sites use the helper; a failed request is audited and says the message
   (D4, D5).** `agents/operator/agent.py`.
5. **Three existing tests are edited**, as rows E1 to E3 of the Test plan say, and no other.
6. **The law cycle**, as the table above says; DRIFT-107 and DRIFT-108 marked CORRECTED.

### Out of scope (do NOT build this sprint)

- **The explicit grammar on a failed request.** An `approve flag-12` whose request fails is refused
  with the message. Do not pass a failed request through `normalize_explicit_intent`.
- **Any other fault inside `interpret`.** A graph write that fails keeps *"Operator could not parse
  the command."*. Do not relay every fault's text.
- **A reply that came back**: a cut-off, a vendor's refusal or filter, a good reply.
- **A retry, a longer time-out, a shortened error text.**
- **A new property on `CommandAudit`**, or the error's text or type anywhere in the graph.
- **The scorecard, the chat page, `surfaces/operator_tools.py`, `surfaces/mcp_tools.py`**, the bus.
- **The adapters**, the port, the factory, the debaters (work-queue 123).
- **An intent that lacks its required parameters** (`OPR-FAIL-02`, DRIFT-109, work-queue 126).
- **The operator container.** It keeps the fake client, which never raises.
- **`docs/STATE.md`, `docs/work-queue.md`, `docs/design-log.md`** (one exception: an amendment under
  DL-286 if the build forces a decision).
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

Recorded in full in [DL-286](../design-log.md). In short:

- **Keep `explain` raising to the bus, add its audit first, and have the surface reword a refusal's
  message.** Rejected: one event would keep two idioms and two fault sources; a bare *"Request timed
  out."* in a chat does not say what failed; an error with no text shows an empty message; and the
  sentence that says the model request failed can only be written by the agent, which is the one
  that knows it was the model call.
- **Relay the text of every fault inside `interpret`.** Rejected: a graph failure is not a model
  failure, and only the measured case changes.
- **Apply the explicit grammar to a failed request, as to a cut-off.** Rejected for this sprint: the
  law says a failed call is refused, and whether a command should act while the model is
  unreachable is a decision about commands during an outage, not about what the chat says.
- **A new audit outcome that the scorecard skips.** Rejected: nothing shows whether the words were a
  question or a command, and an approval typed during an outage would leave the count.
- **Audit a failed `explain` as `refused`.** Rejected: the scorecard would count a question as a
  human action.
- **Write the error's text or type on the `CommandAudit`.** Rejected: `OPR-NEV-06` and `OPR-SEC-02`
  keep credentials and raw text out of the graph, a vendor's 401 repeats the key masked, and a new
  property is a graph vocabulary change. The linked row reads silent; the fault holds the rest.
- **Copy the pattern into the operator's domain.** Rejected: two patterns for one vendor format.
  Importing the surface's is not possible: an agent may not import a surface.
- **Have the adapters raise a typed error carrying the status and the message.** Rejected: four
  adapters, the debate's two among them, for a text the SDKs already render one way.
- **Retry once.** Rejected: an empty account or a refused key does not heal, and a paid call is
  doubled with no evidence that it ends differently.

---

## The design decisions — made, and recorded in DL-286

Build them as written. If one cannot be built as written, stop and report.

- **D1.** `agents/operator/ledger.py::recorded_completion(graph, llm, boundary, *, correlation_id,
  model, system, user, tool_schema)` returns `(row, raw, fault)`. It opens the ledger capture
  **outside** and the caller's fault boundary **inside**, around `complete_recorded` alone. The row
  is always written. A reply returns its text and no fault; a cut-off returns `None` and no fault; a
  request that fails returns `None` and the fault the boundary captured. A ledger write that fails
  is not a failed request: it propagates, as today.
- **D2.** The message is built in `agents/operator/domain/result.py`. `FAILED_REQUEST_REPLY` is
  *"The request to the language model failed, so there is no answer."* `failed_request_reply(fault)`
  returns that sentence, one space, and the reason: *"The vendor answered HTTP 400: Your credit
  balance is too low to access the API."* for a status error; the error's text, stripped, for any
  other; *"The error gave no reason (TimeoutError)."* when the text is empty. `failed_request(fault)`
  returns `{"outcome": "refused", "reason": <that message>}`.
- **D3.** `kernel/llm_error_text.py::vendor_status_error(text)` returns `(status, message)` for an
  SDK status-error text and `None` for anything else. The pattern is the one in
  `surfaces/plain_errors.py` today, unchanged; `plain_error` calls it and keeps its own sentence.
- **D4.** `explain`: the `CommandAudit` is written with outcome **`explain`**, linked to the row, on
  every path. On a failed request `Explanation(summary=<the message>)` is returned. Nothing is
  raised: the bus records no fault of its own.
- **D5.** `interpret`: a failed request is read as `failed_request(fault)` and **not** passed
  through `normalize_explicit_intent`. The existing flow then writes the audit (`refused`) and
  returns the refusal. No `Intent`. Any other fault inside `interpret` is caught by the boundary
  that is there today and refused with today's sentence.
- **D6.** The fault is emitted once, by the operator's own boundary: agent `operator`, module
  `agents.operator.agent`, the capability that was called, the error's own type.
- **D7.** Nothing else moves. The scorecard then counts a failed typed question as one `command`,
  as it counts every interpret call that produced no intent; a failed explain is reading.

🪤 **Take the next free DL number only if the build forces a new decision, then re-check it at
merge.** DL-286 is this sprint's; an amendment goes under it.

---

## Blast radius — measured 2026-10-10

| What | Detail |
| --- | --- |
| Files changed | `agents/operator/agent.py` **168**, `agents/operator/ledger.py` **75**, `agents/operator/domain/result.py` **100**, `surfaces/plain_errors.py` **30**; new `kernel/llm_error_text.py`; three existing tests, in `agents/operator/tests/test_operator_agent.py` **182**, `agents/operator/tests/test_cutoff_agent.py` **150** and `surfaces/tests/test_chat_cutoff.py` **107**; `agents/operator/laws/laws.md` and `test-plan.md`; `surfaces/laws/test-plan.md` (one row); `docs/laws/ledger.md`, `docs/laws/INDEX.md` (one line each), `docs/laws/drift-register.md` (two rows). New test files as you need them, each under 200 lines |
| Agents affected | operator; kernel (one new module, no existing kernel file); surfaces (one production module, same behaviour). No agent imports another |
| Contract change? | No, and none is allowed |
| Graph vocabulary change? | No new label and no new property. A failed request now leaves a `CommandAudit` with the properties and the outcome words that exist today, and its `PRODUCED_BY` edge |
| New env keys / tunables | None |
| Deploy implication | None required. The chat runs in the dashboard, from the main checkout; the fleet's operator container binds the fake client, which never raises. The next retag carries the code. No fidelity decision path is touched |
| Rollback | Revert the merge commit. Nothing is deployed and nothing outside the repository changes |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Read DL-286** in `docs/design-log.md`, and DL-285.
3. **Plant the failing tests first** (C1 and D1 of the Test plan, with the message written out in
   the test) and watch them fail on behaviour. Paste the red output.
4. **Implement**, in the order of Scope 1 to 4. The Appendix holds the measured prototype.
5. **Edit the three existing tests** (E1 to E3), and write the rest of the plan.
6. **The law cycle**: the reworded clause, the test-plan rows, the docstring citations, the rollup
   lines, DRIFT-107 and DRIFT-108.
7. **Prove the guards can fail (DL-70)**: break the implementation, watch each guard go red, restore.
8. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Each vendor's SDK is a fake injected through `importlib.import_module`;
`agents/operator/tests/cutoff_helpers.py::scripted_client` does it and raises any exception placed
in its list of replies. The D tests build each **real** operator adapter with it and send the turn
through `surfaces.dashboard.chat.handle_chat`.

The plan's numbers are this sprint's own. S264's tests in the same folders are named
`test_a1_…` to `test_d3_…` too: name yours so the two sets cannot be confused, and put them in
new files.

The lead sentence, written out here once for the tests: *"The request to the language model failed,
so there is no answer."* The fixture texts are the measured ones of the table above: OpenAI's 401,
Anthropic's 401 and 400 (write the request id as `req_011`), and each SDK's time-out text.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 the status text is split | the three vendor status texts; `Error code: 429 - {"message": "slow down"}`; a body whose message is double-quoted because it holds an apostrophe | the status and the message of each. `None` for a time-out text, for an empty text, for `Error code: 400 - no body`, and for a status text that is not at the start |
| A2 | the lead sentence | the constant | equal to the sentence above letter for letter; lower-cased it contains none of `openai`, `anthropic`, `gpt`, `claude`; it contains no digit. `OPR-FAIL-01` |
| A3 | 🎯 the message gives the reason in plain words | a fault for each of: the three status texts, each time-out text, a text of spaces only | the status texts read *"… The vendor answered HTTP 401: …"* with the vendor's message whole; a time-out reads the lead, a space and the SDK's text; no text reads *"… The error gave no reason (TimeoutError)."* For a status text the message contains none of `Error code`, `{`, the body's `type` word. `OPR-FAIL-01` |
| A4 | a failed request is a refusal | a fault | `{"outcome": "refused", "reason": <the message>}`. `OPR-FAIL-01` |
| A5 | 🪤 the surface says what it said | nothing new | the three `plain_error` tests of `surfaces/tests/test_status_fleet_check.py` pass **unedited** |
| B1 | 🎯 the helper on a failed request | a stub client that raises `TimeoutError` | nothing is raised; the row is written and read silent (`unknown`, 0 out, `estimated`); the reply is `None`; the fault returned is the one in the sink, once, with the error's type and text, agent `operator` and the capability of the boundary given. `OPR-FAIL-01` / `OPR-STA-03` |
| B2 | the helper on a reply | a stub that returns text | the text, no fault, an empty sink; the row holds the stop reason and the vendor's counts |
| B3 | 🪤 a cut-off is not a failed request | a stub that raises the stopped-completion error | `None`, **no fault**, an empty sink; the row holds the vendor's stop word and counts and is not read silent. `OPR-FAIL-04` |
| B4 | 🪤 a ledger write that fails is not a failed request | a graph whose `merge_node` raises for `LLMCall`, a stub that returns text | the graph's error propagates; the sink is empty. `OPR-FAIL-03` |
| C1 | 🎯 `explain`, the request fails, through a bus | the stub of B1; the agent bound to a bus with its own sink | the bus's reply is a response, not an error; its summary is the message; one row, read silent; one `CommandAudit`, outcome `explain`, with a `PRODUCED_BY` edge to the row; the agent's sink holds one fault (`TimeoutError`, capability `explain`, module `agents.operator.agent`); **the bus's sink holds none**. `OPR-FAIL-01` / `OPR-OUT-06` / `OPR-IN-03` |
| C2 | 🎯 `interpret`, the request fails | the same stub, a typed question | outcome `refused`, no intent, the message; one row, read silent; one `CommandAudit`, outcome `refused`, linked; no `Intent` node; one fault, capability `interpret`. `OPR-FAIL-01` / `OPR-OUT-06` / `OPR-OUT-05` |
| C3 | 🪤 an explicit approve is refused when its request fails | the same stub, the text `approve flag-12` | outcome `refused`, no intent, the message; audit `refused`; no `Intent`. `OPR-FAIL-01` |
| C4 | 🪤 any other fault keeps the old sentence | a graph whose `merge_node` raises for `CommandAudit`; a stub that returns `{}` | *"Operator could not parse the command."*; one fault, of the graph error's type; one row. `OPR-FAIL-03` |
| C5 | 🪤 a failed request, then a failed audit | the graph of C4 and the stub of B1 | two faults, the request's first; the old sentence; one row |
| C6 | 🪤 the error's text reaches no graph record | a stub that raises an error whose text holds a marker word, on `explain` and on `interpret` | the marker is in the message returned and in no property of any node the graph holds. `OPR-FAIL-01` / `OPR-NEV-06` |
| C7 | 🪤 a reply that is not JSON is not a fault | a fake client answering `not json at all` | refused with a reason, one audit (`refused`), **no fault**. `OPR-FAIL-01` / `OPR-OUT-05` |
| D1 | 🎯 one failure reads the same on both paths and both vendors, through the chat | for each of a time-out, an HTTP 400 and an error with no text, on each of: the quick ask *explain this run*; a typed question; a typed question parsed and its answer's request failing. Each on `openai` and on `anthropic` | **what was observed on the two vendors is equal**, and on both: the turn's message is the message for that failure, the same words on all three paths; the outcomes are `answer`, `refused`, `answer`; the audits are `explain`; `refused`; `intent` and `explain`, each linked to one row; the failed row is read silent; exactly one fault, with the error's type, the capability called and module `agents.operator.agent`; an `Intent` only on the third path. `SRF-FAIL-02` / `SRF-OUT-03` / `OPR-FAIL-01` |
| D2 | 🪤 the SDK's own text is never shown | the HTTP 400, each path, each vendor | the turn's message contains none of `Error code`, `{`, `invalid_request_error`. `SRF-FAIL-02` |
| D3 | the scorecard | a time-out on each path, each vendor | `human_actions` returns nothing for the quick ask and for the parsed question; one `command` for the typed question |
| D4 | 🪤 a reply that came back is untouched | nothing new | S264's `test_d1_cutoff_chat_is_equal_on_both_vendors` and `test_d2_partial_tool_answer_is_never_shown` pass **unedited** |
| E1 | edit `agents/operator/tests/test_operator_agent.py::test_interpret_llm_exception_returns_refusal` | its own raising client | **Keep its name** (two test-plan rows cite it). The `"could not parse"` assertion becomes the message for its error's text; add that one `CommandAudit` with outcome `refused` exists. The file is at 182 lines: stay under 200 |
| E2 | edit `agents/operator/tests/test_cutoff_agent.py::test_c5_failed_interpret_keeps_the_old_fault_and_refusal` | as it is | Rename it to say what it now proves (no test plan cites it). The message assertion becomes the message; `not graph.list_nodes("CommandAudit")` becomes one audit, `refused`, linked to the row. It keeps: one fault of type `TimeoutError`, the row `unknown` and `estimated`, no `Intent` |
| E3 | edit `surfaces/tests/test_chat_cutoff.py::test_d3_outage_distinguishes_failed_request_from_cutoff` | as it is | **Keep its name** (`OPR-FAIL-04`'s row cites it). The failed turn's message becomes the message, its outcome `answer`, and `not failed_graph.list_nodes("CommandAudit")` becomes one audit with outcome `explain`. It keeps: the cut-off row not silent and no fault for it; the failed row silent; one fault of type `TimeoutError` |

---

## Success factors

- [ ] On both vendors a failed request leaves a `CommandAudit` linked to its row: `explain` for an
      explain call, `refused` for an interpret call (C1, C2, D1).
- [ ] The quick ask and a typed question show the same message for the same failure, on both
      vendors; a status error reads as its HTTP status and the vendor's message, and never as the
      SDK rendered it (A3, D1, D2).
- [ ] Exactly one fault is recorded for a failed request, by the operator's boundary, with the
      error's own type; the bus records none (B1, C1, D1).
- [ ] An explicit approve whose request fails is refused; any other fault keeps today's sentence
      (C3, C4).
- [ ] A reply that came back, cut off or whole, behaves exactly as on `main` (B2, B3, D4), and
      `plain_error` returns what it returned (A5).
- [ ] Nothing of an error's text is in the graph (C6).
- [ ] Exactly three existing tests are edited, as E1 to E3 say; no other existing test changes.
- [ ] Every file the invariant names is unchanged; the command in the handback checklist prints
      nothing.
- [ ] The law cycle done: `OPR-FAIL-01` reworded as given and proven, the changelog, the version,
      the test-plan rows, both rollup lines, DRIFT-107 and DRIFT-108 CORRECTED.
- [ ] Design decisions built as recorded in DL-286, or an amendment under it.
- [ ] Every guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched or new module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The existing suite is red on the prototype in three tests and proves nothing else here.** 4,584
tests pass with the whole change in. Only the tests of this plan, and the three edited ones, guard
it.
🪤 **A red on an import is not the red asked for.** A test that imports `FAILED_REQUEST_REPLY`,
`recorded_completion` or `kernel.llm_error_text` fails at collection before the implementation
exists. Plant C1 and D1 first with the message written out in the test: C1 goes through the bus and
D1 through the chat, and neither needs a new name.
🪤 **The order of the two context managers is the sprint.** The ledger capture outside, the fault
boundary inside. The other way round the boundary swallows a ledger write that failed and the
helper returns a row that does not exist. B4 is the guard.
🪤 **`_explain` must not raise for a failed request.** Raised again, the bus records a second fault
and the surface shows the SDK's text. C1 reads the bus's own sink for this.
🪤 **A failed request is not a cut-off.** Both come back from `complete_recorded`'s caller with no
reply text. Tell them apart by the fault, not by `raw is None`: with the fault branch left out, a
failed `explain` says the cut-off sentence.
🪤 **Write the audit before you answer**, on both capabilities.
🪤 **Do not send a failed request through `normalize_explicit_intent`.** C3 is the guard.
🪤 **The audit of a failed `explain` stays `explain`.** Written as `refused` it becomes a human
action on the unattended scorecard.
🪤 **The pattern moves, it is not rewritten.** `re.match` anchors at the start with or without the
`^`. Copy the pattern and the call as they are.
🪤 **The worktree has no Anthropic SDK** (`openai` is installed). Inject a fake module, as the
existing helper does.
🪤 **Tests must not depend on a `.env`.** `build_test_context` builds the agent with
`OperatorSettings()`, which reads one where it exists. Every D test sets `OPERATOR_LLM_PROVIDER`
and deletes `OPERATOR_MODEL` and `OPERATOR_EFFORT` itself, as `chat_case` does.
🪤 **`graph.list_nodes` returns a tuple.** Compare with `not ...` or with `()`, never with `[]`.
🪤 **A test file needs its header.** A file under `agents/` or `surfaces/` whose docstring lacks
`Agent:` and `Role:` fails the header step.
🪤 **A fixture that looks like a secret stops the commit.** Write the request id as `req_011` and
keep OpenAI's masked key as the vendor wrote it (`not-a-ke***q125`). Read every line you add to
`.secrets.baseline`, if you add any.
🪤 **A summary that fits the test is not the clause** (conventions §7a). `OPR-FAIL-01` now asserts
several things at once; its row is 🟩 only when the cited tests prove each of them.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `agents/operator/agent.py` **168**,
  `agents/operator/tests/test_operator_agent.py` **182**,
  `agents/operator/tests/test_cutoff_agent.py` **150**,
  `agents/operator/tests/cutoff_helpers.py` **145**. The planner's prototype tests ran to about
  620 lines in three files: yours need at least four.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. This sprint adds none.
- Faults, not silent failure — `kernel.fault_boundary`. A failed request is a fault; a cut-off is
  not.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- The version bump is the planner's, at merge: do not touch `pyproject.toml` or `uv.lock`.
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. Review the diff against the checklist; re-measure (the scope command;
   `wq125_failed_request_paths.py` against the built code; the guards broken again by the planner;
   each test the law rows cite, resolved by hand); merge `main` in; PATCH bump, `uv lock`; Windows
   `make ci`; push; **`make gate-ran` from `../ta-s265`**, the printed SHA checked against
   `git rev-parse HEAD`; CodeQL set-diff against the open alerts of S264's branch (127, no error);
   fast-forward `main`; tag.
2. **F1a, at no cost, from the main checkout on the merged code:** `wq125_failed_request_paths.py`
   prints, for every failed-request case on both vendors, the message, the audits and one fault,
   and for the eight control cases what it prints today.
3. **F1b, at no cost, a real vendor:** one typed question and one quick ask through the chat
   handler on an in-memory graph, each real adapter built with a key that is not a key. The vendor
   answers HTTP 401 before any generation, so nothing is billed. The chat must show the message
   with the vendor's own words, the audit must be written and one fault recorded.
4. No deploy. **Not proven by any of these:** a time-out, a dropped connection or an empty account
   met in the dashboard itself.

---

## Handover — paste this to Codex

```text
Sprint 265 — a model request that fails in the operator's chat is audited and answered with one
message that says why, the same for the quick ask and a typed question on both vendors.
Spec: docs/sprints/sprint-265-a-failed-chat-request-is-audited-and-says-why.md (read ALL of it,
then CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s265, on branch
sprint-265-a-failed-chat-request-is-audited-and-says-why, cut from main, with its venv synced to
the lock. Work only in that worktree, never in the main checkout and never on main. You have no
.env and no network: every proof is a unit test. The Anthropic SDK is NOT installed there (openai
is): inject a fake module through importlib.import_module, as
agents/operator/tests/cutoff_helpers.py::scripted_client does. `uv run` is safe; never run a bare
`uv sync`. Do not touch pyproject.toml or uv.lock, and say so: the planner bumps the version at
merge. Do not push and do not merge: commit on the branch and hand back. Do not edit docs/STATE.md,
docs/work-queue.md or docs/design-log.md (one exception: an amendment under DL-286 if the build
forces a decision). If a make ci step cannot run in your sandbox (the dependency audit needs the
network), do not bypass it silently: name the step as NOT RUN in the handback.

This handover is complete: nobody will send you follow-up messages. Two tiers:
- A wrong line number, count, path, test name or clause number whose intent is plain from the spec's
  Scope and Success factors is NOT a reason to stop: follow the intent, record the correction in
  Return notes, continue. The same holds if a gate wants a rollup line or a test-plan row worded
  differently from the spec: do what the gate accepts and say so.
- STOP and report, without improvising, when: the build needs a change to complete_recorded, to any
  kernel/llm*.py that exists today, to kernel/bus.py or kernel/errors.py, to anything under
  agents/deliberator/, to agents/operator/store.py, settings.py, domain/grammar.py or
  domain/prompts.py, to any production file under surfaces/ other than surfaces/plain_errors.py, to
  contracts/, or to any file under agents/scanner/, agents/analyst/, agents/portfolio_manager/,
  agents/provider/domain/, agents/execution/order_tolerance.py, orchestration/history_window.py,
  orchestration/packs/trading_tunables.json or orchestration/packs/trading_issuer_map.json; an
  EXISTING test other than the three named in E1-E3 has to be edited (the planner's prototype broke
  exactly those three of 4,588); a law you read contradicts the spec; or a decision D1-D7 cannot be
  built as written.

What and why: the operator's dashboard chat asks a model for one forced tool call, on OpenAI or on
Anthropic. When the request itself fails (a time-out, an empty account, a refused key), measured on
both vendors alike: no CommandAudit is written, although the law says every call has one; the quick
ask "explain this run" lets the error reach the bus and shows its text; a typed question says
"Operator could not parse the command." and the reason is shown nowhere; an error with no text
shows an empty message. You put the model call in its own fault boundary, so a failed request is a
fault and not a raise, write the audit on both capabilities, and answer with one message built in
the operator's domain: a fixed sentence, then the error's own reason in plain words. The pattern
that reads an SDK's status-error text moves from the surface to the kernel, unchanged, so the agent
can use it. You unit-test all of it. You call no vendor.

MUST RULE before any code: read, whole, agents/operator/laws/laws.md and surfaces/laws/laws.md (each
with its test-plan.md), docs/laws/conventions.md, docs/laws/drift-register.md,
surfaces/plain_errors.py, kernel/errors.py, and DL-286 and DL-285 in docs/design-log.md. Fill the
Law reading record first.
Law-cycle answer: YES for operator, and NO new clause: OPR-FAIL-01 is reworded to the text the spec
gives under "The clause", changelog, version up; the count stays 20 / 51. OPR-OUT-06's and
OPR-FAIL-01's test-plan rows gain citations. Surfaces gets two more citations on SRF-FAIL-02's row
and NO clause or version change. NO contracts/ file changes.

Order (the spec's Steps): laws -> plant C1 and D1 with the message written out in the test, watch
them fail on behaviour (not on an import), paste the red -> implement Scope 1, 2, 3, 4 (the
Appendix holds the measured prototype) -> edit the three existing tests (E1-E3) -> the remaining
tests -> the law cycle, DRIFT-107 and DRIFT-108 -> break and restore every guard -> make ci to a
file.

Build (decisions D1-D7 are made; build them as written):
1. kernel/llm_error_text.py (new): vendor_status_error(text) -> (status, message) or None, holding
   the pattern that is in surfaces/plain_errors.py today, character for character.
   surfaces/plain_errors.py: plain_error calls it and returns what it returns today.
2. agents/operator/ledger.py: recorded_completion(graph, llm, boundary, *, correlation_id, model,
   system, user, tool_schema) -> (row, raw, fault). The ledger capture OUTSIDE, the boundary INSIDE,
   around complete_recorded alone. complete_recorded itself does not change.
3. agents/operator/domain/result.py: FAILED_REQUEST_REPLY (D2's exact text),
   failed_request_reply(fault), failed_request(fault).
4. agents/operator/agent.py: both call sites go through recorded_completion with the operator's
   boundary for that capability; explain writes its audit ("explain") and then returns the message
   on a failed request, never raising; interpret reads a failed request as failed_request(fault),
   NOT through normalize_explicit_intent, and the existing flow writes the audit.
5. The three existing tests, the new tests, the law cycle.

DO NOT: change complete_recorded or anything else the invariant names; rewrite the pattern; raise
from _explain for a failed request; send a failed request through the grammar; relay the text of a
fault that is not a failed model request; reword "Operator could not parse the command.", the
cut-off sentence or "No explanation returned."; audit a failed explain as "refused"; answer before
the audit is written; write the error's text or type into the graph or add a property to
CommandAudit; retry; shorten an error's text; name a vendor, a model or a number in the lead
sentence; add a law clause; edit an existing test other than E1-E3; give the operator container a
real client; let a test depend on a .env; pin a version number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The red output of C1 and D1 pasted, from before the implementation, each failing on behaviour.
 3. Test plan results: one row for each of A1-A5, B1-B4, C1-C7, D1-D4 and E1-E3, with file and
    status.
 4. Every guard's break-and-restore stated, one line per guard. At least these, each of which the
    planner broke on the prototype and saw red (the tests that caught it in brackets):
    kernel: the status text found anywhere in the text (A1); status and message swapped (A1, A3,
    D1); a status error never recognised (A1, A3, D1, D2).
    result.py: the lead sentence reworded (A2, A3); the lead naming a vendor (A2); a status error
    relayed as the SDK wrote it (A3, D1, D2); an error with no text giving no type name (A3, D1);
    the reason dropped (A3, C1, C2); the vendor's message dropped from a status error (A3, D1); a
    failed request asking for clarification (A4, C2, C3); a failed request refused with no reason
    (A4, C2, C3).
    ledger.py: the boundary outside the ledger capture (B4); the fault captured and not handed back
    (B1, C1, C2); the client called directly instead of complete_recorded (B2, B3).
    agent.py: a failed explain answering before its audit (C1, D1); audited as "refused" (C1, D1,
    D3); raising to the bus again (C1, D1); taken for a cut-off (C1, D1); a failed interpret going
    through the grammar (C3); taken for a cut-off (C2, C3, D1); refused before its audit (C2, C3);
    saying the old sentence (C2, C3, D1); every interpret fault relaying its text (C4, C5); the
    explain call's fault labelled "interpret" (C1, D1); a failed interpret raised again after its
    audit (C2, C3, D1); a failed interpret audited as "explain" (C2, C3, D1, D3); the boundary
    re-raising (C1, C2, C3, C4); the fault naming another module (C1, D1); the error's text
    written on the audit (C6).
    result.py again: a reply that is not JSON raising instead of refusing (C7).
    surfaces/plain_errors.py: a status error passed through as the SDK wrote it, and the sentence
    losing the vendor's message (the three existing plain_error tests, unedited).
 5. This prints nothing, and you say so (run it against the commit the branch was cut from if main
    has moved; name which you used):
    git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration kernel/llm.py kernel/llm_ledger.py kernel/llm_tokens.py kernel/llm_factory.py kernel/llm_outage.py kernel/llm_openai.py kernel/llm_openai_operator.py kernel/llm_anthropic.py kernel/llm_anthropic_responses.py kernel/bus.py kernel/errors.py agents/deliberator agents/operator/store.py agents/operator/settings.py agents/operator/domain/grammar.py agents/operator/domain/prompts.py surfaces/dashboard surfaces/queries surfaces/context.py surfaces/operator_tools.py surfaces/mcp_tools.py surfaces/laws/laws.md pyproject.toml uv.lock docs/STATE.md docs/work-queue.md
 6. `git diff main -- surfaces/plain_errors.py kernel/llm_error_text.py` pasted whole, and one line
    saying the pattern's text is the same characters as on main.
 7. `git diff main` of the three existing tests pasted whole, and one line saying no other existing
    test changed.
 8. The operator law book's old and new version, OPR-FAIL-01 quoted as written, the test-plan rows
    of OPR-FAIL-01, OPR-OUT-06 and SRF-FAIL-02 quoted, the status cells of DRIFT-107 and DRIFT-108
    quoted, and both rollup lines.
 9. The law gate's output (scripts/check_law_coverage.py), exit code stated, AND every test those
    three rows cite listed with its file: the gate does not check each citation.
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

**Design decisions:** recorded as [`DL-286`](../design-log.md) — <one line on any amendment, or "built as written">

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

Measured on `main` at `f3e37421`: with this diff applied, 4,584 of the 4,588 existing tests pass
and the three functions named in rows E1 to E3 fail; `ruff`, `mypy` and the import contracts are
clean; the planner's 48 prototype test cases pass. It is the shape to build; the tests and the law
cycle are yours. It was removed from the worktree after measuring, so you start from `main`'s code.

```diff
diff --git a/agents/operator/agent.py b/agents/operator/agent.py
index 7ff2821c..00074a70 100644
--- a/agents/operator/agent.py
+++ b/agents/operator/agent.py
@@ -20,6 +20,8 @@ from agents.operator.domain.prompts import (
 )
 from agents.operator.domain.result import (
     CUT_OFF_REPLY,
+    failed_request,
+    failed_request_reply,
     intent_from_data,
     message,
     outcome,
@@ -28,7 +30,7 @@ from agents.operator.domain.result import (
     request_correlation,
     with_graph,
 )
-from agents.operator.ledger import complete_recorded, record_llm_call
+from agents.operator.ledger import recorded_completion
 from agents.operator.settings import OperatorSettings
 from agents.operator.store import write_command_audit, write_intent
 from contracts.common import Explanation
@@ -48,9 +50,11 @@ from kernel import (
 from kernel.errors import fault_boundary

 if TYPE_CHECKING:
+    from contextlib import AbstractContextManager
+
     from pydantic import BaseModel

-    from kernel import LLMClient, MessageBus
+    from kernel import FaultCapture, LLMClient, MessageBus


 class OperatorAgent(AgentBase):
@@ -73,15 +77,18 @@ class OperatorAgent(AgentBase):
         self.sink = sink if sink is not None else CollectingFaultSink()
         self.handlers = {"interpret": self._interpret, "explain": self._explain}

-    def _interpret(self, request: BaseModel) -> CommandResult:
-        command = HumanCommand.model_validate(request)
-        with fault_boundary(
+    def _boundary(self, capability: str) -> AbstractContextManager[FaultCapture]:
+        return fault_boundary(
             self.sink,
             agent="operator",
             module="agents.operator.agent",
-            capability="interpret",
+            capability=capability,
             reraise=False,
-        ) as capture:
+        )
+
+    def _interpret(self, request: BaseModel) -> CommandResult:
+        command = HumanCommand.model_validate(request)
+        with self._boundary("interpret") as capture:
             result = self._interpret_command(command)
         if capture.fault is not None:
             return refused("Operator could not parse the command.")
@@ -97,17 +104,16 @@ class OperatorAgent(AgentBase):
         )
         system = build_explain_system()
         user = build_explain_user(explain.subject, evidence)
-        with record_llm_call(
+        row, raw, fault = recorded_completion(
             self._graph,
+            self._llm,
+            self._boundary("explain"),
             correlation_id=corr,
             model=self._settings.resolved_model,
-            prompt=user,
-            system_prompt=system,
-        ) as call:
-            raw = complete_recorded(
-                call, self._llm, system=system, user=user, tool_schema={}
-            )
-        assert call.node is not None
+            system=system,
+            user=user,
+            tool_schema={},
+        )
         write_command_audit(
             self._graph,
             correlation_id=corr,
@@ -115,8 +121,10 @@ class OperatorAgent(AgentBase):
             channel="dashboard",
             text=explain.subject,
             outcome="explain",
-            llm_call_node=call.node,
+            llm_call_node=row,
         )
+        if fault is not None:
+            return Explanation(summary=failed_request_reply(fault))
         if raw is None:
             return Explanation(summary=CUT_OFF_REPLY)
         return Explanation(summary=raw.strip() or "No explanation returned.")
@@ -127,22 +135,20 @@ class OperatorAgent(AgentBase):
         )
         system = self._settings.system_prompt or build_interpret_system()
         user = build_interpret_user(command)
-        with record_llm_call(
+        row, raw, fault = recorded_completion(
             self._graph,
+            self._llm,
+            self._boundary("interpret"),
             correlation_id=corr,
             model=self._settings.resolved_model,
-            prompt=user,
-            system_prompt=system,
-        ) as call:
-            raw = complete_recorded(
-                call,
-                self._llm,
-                system=system,
-                user=user,
-                tool_schema=INTENT_TOOL_SCHEMA,
-            )
-        assert call.node is not None
-        data = normalize_explicit_intent(command.text, parse_json(raw))
+            system=system,
+            user=user,
+            tool_schema=INTENT_TOOL_SCHEMA,
+        )
+        if fault is not None:
+            data = failed_request(fault)
+        else:
+            data = normalize_explicit_intent(command.text, parse_json(raw))
         parsed_outcome = outcome(data)
         audit = write_command_audit(
             self._graph,
@@ -151,7 +157,7 @@ class OperatorAgent(AgentBase):
             channel=command.channel,
             text=command.text,
             outcome=parsed_outcome,
-            llm_call_node=call.node,
+            llm_call_node=row,
         )
         if parsed_outcome != "intent":
             return CommandResult(outcome=parsed_outcome, message=message(data))
diff --git a/agents/operator/domain/result.py b/agents/operator/domain/result.py
index 4c40c3e8..a8bf7151 100644
--- a/agents/operator/domain/result.py
+++ b/agents/operator/domain/result.py
@@ -14,9 +14,10 @@ from typing import TYPE_CHECKING, Literal
 from agents.operator.domain.grammar import apply_confirmation_policy
 from contracts.common import Explanation, Provenance
 from contracts.operator import CommandResult, TypedIntent
+from kernel.llm_error_text import vendor_status_error

 if TYPE_CHECKING:
-    from kernel import Node
+    from kernel import AgentFault, Node

 Outcome = Literal["intent", "refused", "needs_clarification"]

@@ -26,6 +27,28 @@ CUT_OFF_REPLY = (
 )


+FAILED_REQUEST_REPLY = (
+    "The request to the language model failed, so there is no answer."
+)
+
+
+def failed_request_reply(fault: AgentFault) -> str:
+    """Say the model request failed, then the error's own reason in plain words."""
+    status = vendor_status_error(fault.message)
+    if status is not None:
+        reason = f"The vendor answered HTTP {status[0]}: {status[1]}"
+    else:
+        reason = (
+            fault.message.strip() or f"The error gave no reason ({fault.error_type})."
+        )
+    return f"{FAILED_REQUEST_REPLY} {reason}"
+
+
+def failed_request(fault: AgentFault) -> dict[str, object]:
+    """Read a model request that failed as a refusal; no grammar is applied to it."""
+    return {"outcome": "refused", "reason": failed_request_reply(fault)}
+
+
 def parse_json(raw: str | None) -> dict[str, object]:
     """Parse model JSON; malformed output, or a cut-off reply (None), is a refusal."""
     if raw is None:
diff --git a/agents/operator/ledger.py b/agents/operator/ledger.py
index 121ad62c..9d9d525a 100644
--- a/agents/operator/ledger.py
+++ b/agents/operator/ledger.py
@@ -17,8 +17,9 @@ from kernel.llm_ledger import record_llm_call as _record_llm_call

 if TYPE_CHECKING:
     from collections.abc import Iterator
+    from contextlib import AbstractContextManager

-    from kernel import GraphStore, LLMClient
+    from kernel import AgentFault, FaultCapture, GraphStore, LLMClient, Node


 @contextmanager
@@ -73,3 +74,38 @@ def complete_recorded(
     call.set_stop_reason(llm_stop_reason(llm))
     call.set_usage(llm_usage(llm))
     return raw
+
+
+def recorded_completion(
+    graph: GraphStore,
+    llm: LLMClient,
+    boundary: AbstractContextManager[FaultCapture],
+    *,
+    correlation_id: str,
+    model: str,
+    system: str,
+    user: str,
+    tool_schema: dict[str, object],
+) -> tuple[Node, str | None, AgentFault | None]:
+    """Make one recorded call inside the caller's fault boundary; never raise for it.
+
+    The row is written whatever happens. A reply comes back as text, a cut-off as
+    None, and a request that failed as None with the fault the boundary captured:
+    the caller audits all three and says which it was.
+    """
+    raw: str | None = None
+    with (
+        record_llm_call(
+            graph,
+            correlation_id=correlation_id,
+            model=model,
+            prompt=user,
+            system_prompt=system,
+        ) as call,
+        boundary as failed,
+    ):
+        raw = complete_recorded(
+            call, llm, system=system, user=user, tool_schema=tool_schema
+        )
+    assert call.node is not None
+    return call.node, raw, failed.fault
diff --git a/kernel/llm_error_text.py b/kernel/llm_error_text.py
new file mode 100644
index 00000000..09babde0
--- /dev/null
+++ b/kernel/llm_error_text.py
@@ -0,0 +1,27 @@
+"""Read the text a vendor SDK gives an API status error.
+
+Agent: kernel
+Role: split an SDK status-error string into its HTTP status and the vendor's message.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+import re
+
+# The Anthropic and OpenAI SDKs both render an API status error as
+# "Error code: <status> - <python dict of the body>". A caller that relays or
+# records str(exc) has only that text, so the text is what is read here.
+_VENDOR_ERROR = re.compile(
+    r"^Error code: (?P<status>\d{3}) - "
+    r".*?['\"]message['\"]: (?P<quote>['\"])(?P<message>.*?)(?P=quote)",
+    re.DOTALL,
+)
+
+
+def vendor_status_error(text: str) -> tuple[str, str] | None:
+    """Return (HTTP status, the vendor's message) for a status error, else None."""
+    match = _VENDOR_ERROR.match(text)
+    if match is None:
+        return None
+    return match["status"], match["message"]
diff --git a/surfaces/plain_errors.py b/surfaces/plain_errors.py
index 20d22442..88b562f5 100644
--- a/surfaces/plain_errors.py
+++ b/surfaces/plain_errors.py
@@ -7,24 +7,13 @@ External I/O: none.

 from __future__ import annotations

-import re
-
-# The Anthropic and OpenAI SDKs both render an API status error as
-# "Error code: <status> - <python dict of the body>". It reaches the surface as
-# text (the operator relays str(exc) over the bus), so the text is all there is.
-_VENDOR_ERROR = re.compile(
-    r"^Error code: (?P<status>\d{3}) - "
-    r".*?['\"]message['\"]: (?P<quote>['\"])(?P<message>.*?)(?P=quote)",
-    re.DOTALL,
-)
+from kernel.llm_error_text import vendor_status_error


 def plain_error(text: str) -> str:
     """Return a vendor status error as one sentence; any other text unchanged."""
-    match = _VENDOR_ERROR.match(text)
-    if match is None:
+    parsed = vendor_status_error(text)
+    if parsed is None:
         return text
-    return (
-        f"The language model refused the request (HTTP {match['status']}): "
-        f"{match['message']}"
-    )
+    status, message = parsed
+    return f"The language model refused the request (HTTP {status}): {message}"
```
