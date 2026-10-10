<!-- Agent: planning | Role: sprint handover -->
# Sprint 265 — a model request that fails in the operator's chat is audited and answered with one message that says why, the same for the quick ask and a typed question on both vendors

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-265-a-failed-chat-request-is-audited-and-says-why`
**Status:** BUILT
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

- [x] On both vendors a failed request leaves a `CommandAudit` linked to its row: `explain` for an
      explain call, `refused` for an interpret call (C1, C2, D1).
- [x] The quick ask and a typed question show the same message for the same failure, on both
      vendors; a status error reads as its HTTP status and the vendor's message, and never as the
      SDK rendered it (A3, D1, D2).
- [x] Exactly one fault is recorded for a failed request, by the operator's boundary, with the
      error's own type; the bus records none (B1, C1, D1).
- [x] An explicit approve whose request fails is refused; any other fault keeps today's sentence
      (C3, C4).
- [x] A reply that came back, cut off or whole, behaves exactly as on `main` (B2, B3, D4), and
      `plain_error` returns what it returned (A5).
- [x] Nothing of an error's text is in the graph (C6).
- [x] Exactly three existing tests are edited, as E1 to E3 say; no other existing test changes.
- [x] Every file the invariant names is unchanged; the command in the handback checklist prints
      nothing.
- [x] The law cycle done: `OPR-FAIL-01` reworded as given and proven, the changelog, the version,
      the test-plan rows, both rollup lines, DRIFT-107 and DRIFT-108 CORRECTED.
- [x] Design decisions built as recorded in DL-286, or an amendment under it.
- [x] Every guard planted, watched to fail, restored, stated per guard.
- [x] Every touched or new module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage. **Not done:** coverage is 100.00 %, but the overall gate fails at the offline dependency audit, named below.

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
| Kernel status text and surface wording | `surfaces/laws/laws.md` and `test-plan.md`, `docs/laws/conventions.md`, `surfaces/plain_errors.py` (whole) | SRF-FAIL-02 / SRF-OUT-05 | No: move the exact pattern; retain the surface sentence. |
| Operator ledger and both capabilities | `agents/operator/laws/laws.md` and `test-plan.md`, `kernel/errors.py` (whole) | OPR-STA-03 / OPR-FAIL-01 / OPR-FAIL-03 / OPR-FAIL-04 / OPR-OUT-04 / OPR-OUT-05 / OPR-OUT-06 / OPR-IN-03 / OPR-OBS-03 / OPR-IDM-01 | No: ledger outside, request boundary inside; audit before returning; other faults retain the old sentence. |
| Operator result and tests | Both law books and both test plans (whole), `docs/laws/conventions.md` and `drift-register.md` (whole), DL-286 and DL-285 (whole) | OPR-FAIL-01 / OPR-OUT-05 / OPR-NEV-06 / OPR-SEC-02 / SRF-FAIL-02 / SRF-OUT-03 | No: D1-D7 are made; error text stays out of graph properties; malformed JSON remains a fault-free refusal. |

Reading recorded before the first code change, on 2026-10-10 in
`C:/Users/yury_/Downloads/project/ta-s265`, branch
`sprint-265-a-failed-chat-request-is-audited-and-says-why`. The tree was clean,
`.env` absent, HEAD and local `origin/main` both
`436ca19e18b93ab04d0273f3224645c0aa944856` (the branch-cut baseline). No network
refresh was made. CLAUDE.md was read; its `docs/STATE.md` tracker stays untouched
under this handover's explicit exclusion. `pyproject.toml` and `uv.lock` stay
untouched; the planner owns the PATCH bump at merge. No push or merge is authorized.

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?**
No contract changes; yes, the failed-request guarantee grows. Confirmed the owed
cycle: reword OPR-FAIL-01 only, operator v1.7 to v1.8 with changelog; extend the
three named citation rows, both operator rollups, and correct DRIFT-107/108.
The counts remain operator 20 / 51 and surfaces 30 / 37. Implementation and
law amendment were not yet done at this reading record. At handback, the owed
cycle is completed: v1.8, exact clause and changelog, three citation rows, both
rollups, and DRIFT-107/108 CORRECTED, with the tests below.

**Contradictions found between a law and this spec:** none beyond the expressly
adjudicated OPR-FAIL-01 wording replaced by this cycle (DRIFT-107/108).
DRIFT-109 remains out of scope and unchanged.

**Laws found silent where a decision was needed:** no additional silence beyond
DRIFT-107, already decided in DL-286.

**Clauses that were ⬜ and are now proven:** none at reading. Binding gray clauses
OPR-FAIL-03, OPR-NEV-06, OPR-SEC-02, OPR-OBS-03 and OPR-IDM-01 are acknowledged
as unproven whole clauses; focused new assertions will not change their status
or the 20 / 51 rollup.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_s265_a1_status_text_is_split`; `test_s265_a1_other_text_is_not_a_status_error` | `agents/operator/tests/test_failed_request_result.py` | PASS | SRF-FAIL-02 |
| A2 | `test_s265_a2_failed_request_lead_is_pinned` | `agents/operator/tests/test_failed_request_result.py` | PASS | OPR-FAIL-01 |
| A3 | `test_s265_a3_status_reason_is_plain_and_whole`; `test_s265_a3_other_reason_is_stripped_and_whole`; `test_s265_a3_no_reason_names_the_error_type` | `agents/operator/tests/test_failed_request_result.py` | PASS | OPR-FAIL-01 |
| A4 | `test_s265_a4_failed_request_is_an_explained_refusal` | `agents/operator/tests/test_failed_request_result.py` | PASS | OPR-FAIL-01 |
| A5 | `test_vendor_status_error_reads_as_one_sentence`; `test_other_errors_pass_through_unchanged`; `test_dispatch_rewrites_raised_and_returned_vendor_errors` | `surfaces/tests/test_status_fleet_check.py` | PASS | — (existing controls, unedited) |
| B1 | `test_s265_b1_failed_request_returns_its_one_fault_and_silent_row` | `agents/operator/tests/test_failed_request_ledger.py` | PASS | OPR-FAIL-01 / OPR-STA-03 |
| B2 | `test_s265_b2_reply_retains_text_stop_reason_and_vendor_usage` | `agents/operator/tests/test_failed_request_ledger.py` | PASS | OPR-STA-03 |
| B3 | `test_s265_b3_cutoff_is_not_a_failed_request` | `agents/operator/tests/test_failed_request_ledger.py` | PASS | OPR-FAIL-04 / OPR-STA-03 |
| B4 | `test_s265_b4_ledger_write_failure_escapes_request_boundary` | `agents/operator/tests/test_failed_request_ledger.py` | PASS | OPR-FAIL-03 |
| C1 | `test_s265_c1_failed_explain_is_audited_and_answers_through_bus` | `agents/operator/tests/test_failed_request_agent.py` | PASS | OPR-FAIL-01 / OPR-OUT-06 / OPR-IN-03 |
| C2 | `test_s265_c2_failed_interpret_is_audited_and_says_why` | `agents/operator/tests/test_failed_request_agent.py` | PASS | OPR-FAIL-01 / OPR-OUT-06 / OPR-OUT-05 |
| C3 | `test_s265_c3_failed_approve_never_enters_explicit_grammar` | `agents/operator/tests/test_failed_request_agent.py` | PASS | OPR-FAIL-01 |
| C4 | `test_s265_c4_other_fault_keeps_the_old_sentence` | `agents/operator/tests/test_failed_request_faults.py` | PASS | OPR-FAIL-03 |
| C5 | `test_s265_c5_failed_request_then_failed_audit_keeps_both_faults` | `agents/operator/tests/test_failed_request_faults.py` | PASS | OPR-FAIL-01 / OPR-FAIL-03 |
| C6 | `test_s265_c6_error_text_and_type_reach_no_graph_property` | `agents/operator/tests/test_failed_request_faults.py` | PASS | OPR-FAIL-01 / OPR-NEV-06 / OPR-SEC-02 |
| C7 | `test_s265_c7_malformed_json_is_a_fault_free_audited_refusal` | `agents/operator/tests/test_failed_request_faults.py` | PASS | OPR-FAIL-01 / OPR-OUT-05 |
| D1 | `test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors` | `surfaces/tests/test_chat_failed_request.py` | PASS | SRF-FAIL-02 / SRF-OUT-03 / OPR-FAIL-01 |
| D2 | `test_s265_d2_status_sdk_rendering_is_never_shown` | `surfaces/tests/test_chat_failed_request.py` | PASS | SRF-FAIL-02 |
| D3 | `test_s265_d3_scorecard_counts_only_the_failed_interpret` | `surfaces/tests/test_chat_failed_request.py` | PASS | SRF-OUT-08 / OPR-FAIL-01 |
| D4 | `test_d1_cutoff_chat_is_equal_on_both_vendors`; `test_d2_partial_tool_answer_is_never_shown` | `surfaces/tests/test_chat_cutoff.py` | PASS | SRF-FAIL-02 / SRF-OUT-03 / OPR-FAIL-04 |
| E1 | `test_interpret_llm_exception_returns_refusal` | `agents/operator/tests/test_operator_agent.py` | PASS | OPR-FAIL-01 / OPR-IN-03 |
| E2 | `test_c5_failed_interpret_says_why_and_writes_linked_audit` | `agents/operator/tests/test_cutoff_agent.py` | PASS | OPR-FAIL-01 |
| E3 | `test_d3_outage_distinguishes_failed_request_from_cutoff` | `surfaces/tests/test_chat_cutoff.py` | PASS | OPR-FAIL-01 / OPR-FAIL-04 |

**Tests added beyond the plan:** no additional behavior rows. Extra parameter cases cover a multiline SDK body (DOTALL), both timeout texts in the non-status reader, stripping a padded reason, a status with no readable body, both empty and whitespace-only reasons, and malformed list/empty replies. These guard unchanged parsing and whole-reason disclosure. The focused run contains 58 new cases and 29 existing controls (87 passed).

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s265`, branch `sprint-265-a-failed-chat-request-is-audited-and-says-why`; `.env` absent. Branch-cut main baseline `436ca19e18b93ab04d0273f3224645c0aa944856`; no vendor or network proof.

**Result:** Unit-proven with both real operator adapters on fake SDKs: failed quick asks and typed questions show the fixed failed-request sentence and the whole plain reason, leave linked audits (`explain` / `refused`), and record one operator fault with the original error type. Failed explicit approval creates no intent; graph failures keep the old refusal; malformed JSON remains fault-free. The focused suite passed 87 cases; all 32 temporary guard breaks failed and passed after exact restoration. No live vendor was called.

**Files changed:**

- `agents/operator/agent.py`
- `agents/operator/domain/result.py`
- `agents/operator/laws/laws.md`
- `agents/operator/laws/test-plan.md`
- `agents/operator/ledger.py`
- `agents/operator/tests/failed_request_helpers.py`
- `agents/operator/tests/failed_request_texts.py`
- `agents/operator/tests/test_cutoff_agent.py`
- `agents/operator/tests/test_failed_request_agent.py`
- `agents/operator/tests/test_failed_request_faults.py`
- `agents/operator/tests/test_failed_request_ledger.py`
- `agents/operator/tests/test_failed_request_result.py`
- `agents/operator/tests/test_operator_agent.py`
- `docs/laws/INDEX.md`
- `docs/laws/drift-register.md`
- `docs/laws/ledger.md`
- `docs/sprints/README.md`
- `docs/sprints/sprint-265-a-failed-chat-request-is-audited-and-says-why.md`
- `kernel/llm_error_text.py`
- `surfaces/laws/test-plan.md`
- `surfaces/plain_errors.py`
- `surfaces/tests/chat_failed_request_helpers.py`
- `surfaces/tests/test_chat_cutoff.py`
- `surfaces/tests/test_chat_failed_request.py`

**Design decisions:** recorded as [`DL-286`](../design-log.md) — D1-D7 built as written; no amendment and no change to `docs/design-log.md`.

**Proof — the red run first:**

```text
Before any production edit; uv run pytest agents/operator/tests/test_failed_request_agent.py surfaces/tests/test_chat_failed_request.py --no-cov -q; exit 1.
FFFFFFFFFF                                                               [100%]
================================== FAILURES ===================================
_______ test_s265_c1_failed_explain_is_audited_and_answers_through_bus ________
agents\operator\tests\test_failed_request_agent.py:25: in test_s265_c1_failed_explain_is_audited_and_answers_through_bus
    assert response.message_type == "response"
E   AssertionError: assert 'error' == 'response'
E
E     - response
E     + error
_ test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[timeout-quick] __
surfaces\tests\test_chat_failed_request.py:34: in test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors
    assert turn["message"] == expected
E   AssertionError: assert 'Request timed out.' == 'The request ...st timed out.'
E
E     - The request to the language model failed, so there is no answer. Request timed out.
E     + Request timed out.
_ test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[timeout-parse] __
surfaces\tests\test_chat_failed_request.py:34: in test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors
    assert turn["message"] == expected
E   AssertionError: assert 'Operator cou... the command.' == 'The request ...st timed out.'
E
E     - The request to the language model failed, so there is no answer. Request timed out.
E     + Operator could not parse the command.
_ test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[timeout-answer] _
surfaces\tests\test_chat_failed_request.py:34: in test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors
    assert turn["message"] == expected
E   AssertionError: assert 'Request timed out.' == 'The request ...st timed out.'
E
E     - The request to the language model failed, so there is no answer. Request timed out.
E     + Request timed out.
__ test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[status-quick] __
surfaces\tests\test_chat_failed_request.py:34: in test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors
    assert turn["message"] == expected
E   AssertionError: assert 'The language...cess the API.' == 'The request ...cess the API.'
E
E     - The request to the language model failed, so there is no answer. The vendor answered HTTP 400: Your credit balance is too low to access the API.
E     + The language model refused the request (HTTP 400): Your credit balance is too low to access the API.
__ test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[status-parse] __
surfaces\tests\test_chat_failed_request.py:34: in test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors
    assert turn["message"] == expected
E   AssertionError: assert 'Operator cou... the command.' == 'The request ...cess the API.'
E
E     - The request to the language model failed, so there is no answer. The vendor answered HTTP 400: Your credit balance is too low to access the API.
E     + Operator could not parse the command.
_ test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[status-answer] __
surfaces\tests\test_chat_failed_request.py:34: in test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors
    assert turn["message"] == expected
E   AssertionError: assert 'The language...cess the API.' == 'The request ...cess the API.'
E
E     - The request to the language model failed, so there is no answer. The vendor answered HTTP 400: Your credit balance is too low to access the API.
E     + The language model refused the request (HTTP 400): Your credit balance is too low to access the API.
__ test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[empty-quick] ___
surfaces\tests\test_chat_failed_request.py:34: in test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors
    assert turn["message"] == expected
E   AssertionError: assert '' == 'The request ...imeoutError).'
E
E     - The request to the language model failed, so there is no answer. The error gave no reason (TimeoutError).
__ test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[empty-parse] ___
surfaces\tests\test_chat_failed_request.py:34: in test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors
    assert turn["message"] == expected
E   AssertionError: assert 'Operator cou... the command.' == 'The request ...imeoutError).'
E
E     - The request to the language model failed, so there is no answer. The error gave no reason (TimeoutError).
E     + Operator could not parse the command.
__ test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[empty-answer] __
surfaces\tests\test_chat_failed_request.py:34: in test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors
    assert turn["message"] == expected
E   AssertionError: assert '' == 'The request ...imeoutError).'
E
E     - The request to the language model failed, so there is no answer. The error gave no reason (TimeoutError).
=========================== short test summary info ===========================
FAILED agents/operator/tests/test_failed_request_agent.py::test_s265_c1_failed_explain_is_audited_and_answers_through_bus
FAILED surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[timeout-quick]
FAILED surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[timeout-parse]
FAILED surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[timeout-answer]
FAILED surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[status-quick]
FAILED surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[status-parse]
FAILED surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[status-answer]
FAILED surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[empty-quick]
FAILED surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[empty-parse]
FAILED surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors[empty-answer]
10 failed in 2.26s
```

**Proof — the green run:**

```text
........................................................................ [ 82%]
...............                                                          [100%]
87 passed in 3.30s
GREEN_EXIT=0

make ci (output redirected; outbound requests blocked by loopback-only proxies)
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
Success: no issues found in 1188 source files
Contracts: 5 kept, 0 broken.
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 4646 passed, 8 skipped, 2470 warnings in 524.61s (0:08:44) ==========
  File "C:\Users\yury_\Downloads\project\ta-s265\.venv\Lib\site-packages\requests\adapters.py", line 723, in send
    raise ProxyError(e, request=request)
requests.exceptions.ProxyError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=9): Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it")))
make: *** [Makefile:59: ci] Error 1
make ci exit code: 2
```

**Guards planted:** 32 / 32 behavioral failures, no import or syntax failures; each source restored byte-for-byte and its guard suite re-run green. Red and restored logs are `guard-NN-red.txt` and `guard-NN-restored.txt` in the proof directory.

- G01 `kernel/llm_error_text.py`: Status text recognized away from start — RED exit 1 (A1); exact bytes restored; GREEN exit 0.
- G02 `kernel/llm_error_text.py`: Status and message swapped — RED exit 1 (A1, A3, D1, D2); exact bytes restored; GREEN exit 0.
- G03 `kernel/llm_error_text.py`: Status error never recognized — RED exit 1 (A1, A3, D1, D2); exact bytes restored; GREEN exit 0.
- G04 `agents/operator/domain/result.py`: Lead sentence reworded — RED exit 1 (A2, A3, A4); exact bytes restored; GREEN exit 0.
- G05 `agents/operator/domain/result.py`: Lead sentence names vendor — RED exit 1 (A2, A3, A4); exact bytes restored; GREEN exit 0.
- G06 `agents/operator/domain/result.py`: SDK status rendering relayed — RED exit 1 (A3, D1, D2); exact bytes restored; GREEN exit 0.
- G07 `agents/operator/domain/result.py`: Empty error has no type name — RED exit 1 (A3, D1); exact bytes restored; GREEN exit 0.
- G08 `agents/operator/domain/result.py`: Error reason dropped — RED exit 1 (A3, A4, C1, C2, C3); exact bytes restored; GREEN exit 0.
- G09 `agents/operator/domain/result.py`: Vendor message dropped — RED exit 1 (A3, D1, D2); exact bytes restored; GREEN exit 0.
- G10 `agents/operator/domain/result.py`: Failed request asks clarification — RED exit 1 (A4, C2, C3); exact bytes restored; GREEN exit 0.
- G11 `agents/operator/domain/result.py`: Failed request refuses without reason — RED exit 1 (A4, C2, C3); exact bytes restored; GREEN exit 0.
- G12 `agents/operator/ledger.py`: Boundary outside ledger capture — RED exit 1 (B4); exact bytes restored; GREEN exit 0.
- G13 `agents/operator/ledger.py`: Captured fault not returned — RED exit 1 (B1, C1, C2, C3); exact bytes restored; GREEN exit 0.
- G14 `agents/operator/ledger.py`: Client called without complete_recorded — RED exit 1 (B2, B3); exact bytes restored; GREEN exit 0.
- G15 `agents/operator/agent.py`: Failed explain answers before audit — RED exit 1 (C1, D1); exact bytes restored; GREEN exit 0.
- G16 `agents/operator/agent.py`: Failed explain audited refused — RED exit 1 (C1, D1, D3); exact bytes restored; GREEN exit 0.
- G17 `agents/operator/agent.py`: Failed explain raises to bus — RED exit 1 (C1, D1, D2); exact bytes restored; GREEN exit 0.
- G18 `agents/operator/agent.py`: Failed explain mistaken for cutoff — RED exit 1 (C1, D1, D2); exact bytes restored; GREEN exit 0.
- G19 `agents/operator/agent.py`: Failed interpret enters grammar — RED exit 1 (C3); exact bytes restored; GREEN exit 0.
- G20 `agents/operator/agent.py`: Failed interpret mistaken for cutoff — RED exit 1 (C2, C3, D1, D2); exact bytes restored; GREEN exit 0.
- G21 `agents/operator/agent.py`: Failed interpret returns before audit — RED exit 1 (C2, C3); exact bytes restored; GREEN exit 0.
- G22 `agents/operator/agent.py`: Failed interpret says old sentence — RED exit 1 (C2, C3, D1, D2); exact bytes restored; GREEN exit 0.
- G23 `agents/operator/agent.py`: Every interpret fault relays request text — RED exit 1 (C4, C5); exact bytes restored; GREEN exit 0.
- G24 `agents/operator/agent.py`: Explain fault labelled interpret — RED exit 1 (C1, D1); exact bytes restored; GREEN exit 0.
- G25 `agents/operator/agent.py`: Failed interpret raises after audit — RED exit 1 (C2, C3, D1, D2); exact bytes restored; GREEN exit 0.
- G26 `agents/operator/agent.py`: Failed interpret audited explain — RED exit 1 (C2, C3, D1, D3); exact bytes restored; GREEN exit 0.
- G27 `agents/operator/agent.py`: Operator boundary reraises — RED exit 1 (C1, C2, C3, C4, C5, C6); exact bytes restored; GREEN exit 0.
- G28 `agents/operator/agent.py`: Fault names another module — RED exit 1 (C1, C2, D1); exact bytes restored; GREEN exit 0.
- G29 `agents/operator/agent.py`: Error text written on audit — RED exit 1 (C6); exact bytes restored; GREEN exit 0.
- G30 `agents/operator/domain/result.py`: Malformed JSON raises instead of refusing — RED exit 1 (C7); exact bytes restored; GREEN exit 0.
- G31 `surfaces/plain_errors.py`: Surface passes through SDK rendering — RED exit 1 (A5); exact bytes restored; GREEN exit 0.
- G32 `surfaces/plain_errors.py`: Surface drops vendor message — RED exit 1 (A5); exact bytes restored; GREEN exit 0.

```text
01: RED exit 1; exact bytes restored; GREEN exit 0; Status text recognized away from start
02: RED exit 1; exact bytes restored; GREEN exit 0; Status and message swapped
03: RED exit 1; exact bytes restored; GREEN exit 0; Status error never recognized
04: RED exit 1; exact bytes restored; GREEN exit 0; Lead sentence reworded
05: RED exit 1; exact bytes restored; GREEN exit 0; Lead sentence names vendor
06: RED exit 1; exact bytes restored; GREEN exit 0; SDK status rendering relayed
07: RED exit 1; exact bytes restored; GREEN exit 0; Empty error has no type name
08: RED exit 1; exact bytes restored; GREEN exit 0; Error reason dropped
09: RED exit 1; exact bytes restored; GREEN exit 0; Vendor message dropped
10: RED exit 1; exact bytes restored; GREEN exit 0; Failed request asks clarification
11: RED exit 1; exact bytes restored; GREEN exit 0; Failed request refuses without reason
12: RED exit 1; exact bytes restored; GREEN exit 0; Boundary outside ledger capture
13: RED exit 1; exact bytes restored; GREEN exit 0; Captured fault not returned
14: RED exit 1; exact bytes restored; GREEN exit 0; Client called without complete_recorded
15: RED exit 1; exact bytes restored; GREEN exit 0; Failed explain answers before audit
16: RED exit 1; exact bytes restored; GREEN exit 0; Failed explain audited refused
17: RED exit 1; exact bytes restored; GREEN exit 0; Failed explain raises to bus
18: RED exit 1; exact bytes restored; GREEN exit 0; Failed explain mistaken for cutoff
19: RED exit 1; exact bytes restored; GREEN exit 0; Failed interpret enters grammar
20: RED exit 1; exact bytes restored; GREEN exit 0; Failed interpret mistaken for cutoff
21: RED exit 1; exact bytes restored; GREEN exit 0; Failed interpret returns before audit
22: RED exit 1; exact bytes restored; GREEN exit 0; Failed interpret says old sentence
23: RED exit 1; exact bytes restored; GREEN exit 0; Every interpret fault relays request text
24: RED exit 1; exact bytes restored; GREEN exit 0; Explain fault labelled interpret
25: RED exit 1; exact bytes restored; GREEN exit 0; Failed interpret raises after audit
26: RED exit 1; exact bytes restored; GREEN exit 0; Failed interpret audited explain
27: RED exit 1; exact bytes restored; GREEN exit 0; Operator boundary reraises
28: RED exit 1; exact bytes restored; GREEN exit 0; Fault names another module
29: RED exit 1; exact bytes restored; GREEN exit 0; Error text written on audit
30: RED exit 1; exact bytes restored; GREEN exit 0; Malformed JSON raises instead of refusing
31: RED exit 1; exact bytes restored; GREEN exit 0; Surface passes through SDK rendering
32: RED exit 1; exact bytes restored; GREEN exit 0; Surface drops vendor message
32 of 32 guard breaks failed on behavior and passed after exact restoration.
GUARD_RUN_EXIT=0
```

**Module line counts:** every touched or new Python module, all below 200.

| File | Lines |
| --- | --- |
| `agents/operator/agent.py` | 174 |
| `agents/operator/domain/result.py` | 123 |
| `agents/operator/ledger.py` | 111 |
| `agents/operator/tests/failed_request_helpers.py` | 77 |
| `agents/operator/tests/failed_request_texts.py` | 42 |
| `agents/operator/tests/test_cutoff_agent.py` | 157 |
| `agents/operator/tests/test_failed_request_agent.py` | 96 |
| `agents/operator/tests/test_failed_request_faults.py` | 129 |
| `agents/operator/tests/test_failed_request_ledger.py` | 108 |
| `agents/operator/tests/test_failed_request_result.py` | 115 |
| `agents/operator/tests/test_operator_agent.py` | 186 |
| `kernel/llm_error_text.py` | 27 |
| `surfaces/plain_errors.py` | 19 |
| `surfaces/tests/chat_failed_request_helpers.py` | 73 |
| `surfaces/tests/test_chat_cutoff.py` | 111 |
| `surfaces/tests/test_chat_failed_request.py` | 115 |

**`make ci`:** redirected to `C:/Users/yury_/Downloads/project/trading-agents-data/s265-codex-proof/make-ci.txt`. Exit code **2**. `4646 passed, 8 skipped, 2470 warnings in 524.61s (0:08:44)`; `Required test coverage of 100.0% reached. Total coverage: 100.00%`. **Dependency audit: NOT RUN against the live advisory feed**: no network is authorized; HTTP/HTTPS outbound traffic was routed to an unavailable loopback proxy, and step 13 could not obtain an audit report. No bypass and no green overall CI claim. Steps 1-12 passed. Steps 14-15 were run explicitly after make stopped, both exit 0, with output below. `.secrets.baseline` unchanged.

```text
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
DETECT_SECRETS_EXIT=0
uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
UNTRACKED_SECRETS_EXIT=0
```

**`make gate-ran`:** NOT RUN — no push or network is authorized. Remote CI and Security Findings for the final branch commit are not proven; the planner owns them before merge. No `GATE PROVEN` claim.

**Not met / verified failing:** the overall `make ci` gate is verified failing (exit 2) at the network-dependent dependency audit; current advisory proof is NOT RUN. A full green CI gate, remote gates, version bump, push, merge, deploy, and live dashboard/vendor checks are not done here. No unresolved implementation uncertainty found in the authorized unit-test scope; real vendor failure behavior in the dashboard remains unproven.

---

## Return notes

- Scope held. The protected-file diff prints nothing against the branch-cut main named below. `pyproject.toml` and `uv.lock` were not touched; the planner bumps the PATCH version at merge. Only E1-E3 changed among existing tests; no contracts, adapters, decision paths, prompt/grammar files, bus, or excluded production surface changed.
- No disagreement requiring a design amendment. The reading confirmed the intended OPR-FAIL-01 law cycle. DRIFT-109 remains OPEN and unchanged. Gray clauses acknowledged in the reading record remain gray; neither law count changed.
- The measured prototype baseline `f3e37421` is historical; this branch was prepared at `436ca19e18b93ab04d0273f3224645c0aa944856`, also main at both scope checks. S265 test names carry `s265` to distinguish them from S264. An explain failure is still reading (`answer` / audit `explain`); a failed typed parse counts as one command. Every D fixture pins provider and deletes model/effort overrides. The law gate emits no output on success and does not validate every citation: all 24 citations were resolved separately below. Pasted command text is complete; invisible trailing spaces were removed to satisfy the whitespace hook. No vendor was called, no retry added, and no raw error text or type added to graph properties.

---

### Scope and complete diff evidence (handback items 5-7)

```text
Scope baseline: main at branch-cut 436ca19e18b93ab04d0273f3224645c0aa944856
git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration kernel/llm.py kernel/llm_ledger.py kernel/llm_tokens.py kernel/llm_factory.py kernel/llm_outage.py kernel/llm_openai.py kernel/llm_openai_operator.py kernel/llm_anthropic.py kernel/llm_anthropic_responses.py kernel/bus.py kernel/errors.py agents/deliberator agents/operator/store.py agents/operator/settings.py agents/operator/domain/grammar.py agents/operator/domain/prompts.py surfaces/dashboard surfaces/queries surfaces/context.py surfaces/operator_tools.py surfaces/mcp_tools.py surfaces/laws/laws.md pyproject.toml uv.lock docs/STATE.md docs/work-queue.md
Output: nothing (no stdout); protected-file scope held.
docs/design-log.md also unchanged; D1-D7 built as written.
Exactly E1-E3 changed; AST outside those three functions unchanged; no other existing test changed.
complete_recorded is character-for-character unchanged.
The status pattern's text is the same characters as on the branch-cut main; the matching call remains .match(text).
No existing kernel file changed; surfaces/plain_errors.py is the only changed surface production file.
.env absent; pyproject.toml and uv.lock unchanged; no version pinned or bumped.
SCOPE_EXIT=0
```

The requested `git diff main -- surfaces/plain_errors.py kernel/llm_error_text.py`, whole:

```diff
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

The pattern's text is the same characters as on the branch-cut main (AST source-segment comparison); the anchored matching call is unchanged.

The requested `git diff main` of the three existing tests, whole:

```diff
diff --git a/agents/operator/tests/test_cutoff_agent.py b/agents/operator/tests/test_cutoff_agent.py
index d1a4a32a..2889e75d 100644
--- a/agents/operator/tests/test_cutoff_agent.py
+++ b/agents/operator/tests/test_cutoff_agent.py
@@ -119,21 +119,28 @@ def test_c4_finished_call_records_the_clients_stop_reason(
     assert not _faults(agent)


-def test_c5_failed_interpret_keeps_the_old_fault_and_refusal() -> None:
-    """OPR-FAIL-01: time-outs retain the old refusal, one fault, and no audit."""
+def test_c5_failed_interpret_says_why_and_writes_linked_audit() -> None:
+    """OPR-FAIL-01: time-outs say why, with one fault and a linked refusal audit."""
     agent, graph = _agent(CompletionStub(failed=True))
     result = agent._interpret(
         HumanCommand(text="question", actor="operator", channel="dashboard")
     )
     assert result.outcome == "refused"
-    assert result.message.summary == "Operator could not parse the command."
+    assert result.message.summary == (
+        "The request to the language model failed, so there is no answer. "
+        "fixture request timed out"
+    )
     assert len(_faults(agent)) == 1
     assert _faults(agent)[0].error_type == "TimeoutError"
     rows = graph.list_nodes("LLMCall")
     assert len(rows) == 1
     assert rows[0].props["stop_reason"] == "unknown"
     assert rows[0].props.get("token_source") == "estimated"
-    assert not graph.list_nodes("CommandAudit")
+    (audit,) = graph.list_nodes("CommandAudit")
+    assert audit.props["outcome"] == "refused"
+    assert (
+        tuple(graph.descendants(audit, max_depth=1, edge_types={"PRODUCED_BY"})) == rows
+    )
     assert not graph.list_nodes("Intent")


diff --git a/agents/operator/tests/test_operator_agent.py b/agents/operator/tests/test_operator_agent.py
index ed18eddd..086824e5 100644
--- a/agents/operator/tests/test_operator_agent.py
+++ b/agents/operator/tests/test_operator_agent.py
@@ -82,7 +82,11 @@ def test_interpret_llm_exception_returns_refusal() -> None:
     bus = _bound_bus(graph, _RaisingLLM({}))
     result = _interpret(bus, "run")
     assert result.outcome == "refused"
-    assert "could not parse" in result.message.summary
+    assert result.message.summary == (
+        "The request to the language model failed, so there is no answer. model down"
+    )
+    (audit,) = graph.list_nodes("CommandAudit")
+    assert audit.props["outcome"] == "refused"


 def test_explain_returns_text_and_writes_audit_and_llm_call() -> None:
diff --git a/surfaces/tests/test_chat_cutoff.py b/surfaces/tests/test_chat_cutoff.py
index f7a5eb7c..e79f1db0 100644
--- a/surfaces/tests/test_chat_cutoff.py
+++ b/surfaces/tests/test_chat_cutoff.py
@@ -99,9 +99,13 @@ def test_d3_outage_distinguishes_failed_request_from_cutoff(
     assert not is_silent_call(cut_graph.list_nodes("LLMCall")[0])
     assert not cut_sink.faults
     assert is_silent_call(failed_graph.list_nodes("LLMCall")[0])
-    assert failed["message"] == "fixture request timed out"
+    assert failed["message"] == (
+        "The request to the language model failed, so there is no answer. "
+        "fixture request timed out"
+    )
     assert failed["message"] != EXPECTED_REPLY
-    assert failed["outcome"] == "refused"
+    assert failed["outcome"] == "answer"
     assert len(failed_sink.faults) == 1
     assert failed_sink.faults[0].error_type == "TimeoutError"
-    assert not failed_graph.list_nodes("CommandAudit")
+    (audit,) = failed_graph.list_nodes("CommandAudit")
+    assert audit.props["outcome"] == "explain"
```

No other existing test changed; AST outside E1-E3 is unchanged.

### Law-cycle quotes and citation resolution (handback items 8-9)

Operator law book: **LOCKED v1.7 → LOCKED v1.8**. No clause added; 20 / 51 unchanged. Surfaces laws stay LOCKED v1.5, unchanged, 30 / 37. OPR-FAIL-01, as written:

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

The three test-plan rows, verbatim:

```text
| OPR-FAIL-01 | 🟩 | A model request that fails (a network error, a time-out, a status the vendor refuses the request with: anything the client raises other than the cut-off of `OPR-FAIL-04`) is a fault and never an answer, for `interpret` and for `explain`, on every vendor. `fault_boundary` captures it around the model call alone: one fault, carrying the error's own type, and nothing raised to the bus. The call is recorded as `OPR-STA-03` says and its `CommandAudit` is written and linked as for any call (`OPR-OUT-06`), with outcome `refused` for `interpret` and `explain` for `explain`. `interpret` returns `CommandResult(outcome="refused", ...)` and `explain` an `Explanation`, each carrying the failed-request message; the explicit command grammar is not applied and no `Intent` is written. The failed-request message is one fixed sentence that says the request failed and names no vendor, model or number, followed by the error's own reason in plain words: the HTTP status and the vendor's message for a status error, the error's text otherwise, the error's type when it has no text. The SDK's rendering of a status error is never shown, and the error's text is written to no graph record. Its letters are pinned by tests, not quoted here. A model reply that is not valid JSON is not a fault: it is the explained refusal of `OPR-OUT-05`. A graph write that fails is `OPR-FAIL-03`'s. Proven by: `agents/operator/tests/test_operator_agent.py::test_interpret_llm_exception_returns_refusal`; `agents/operator/tests/test_failed_request_result.py::test_s265_a2_failed_request_lead_is_pinned`; `agents/operator/tests/test_failed_request_result.py::test_s265_a3_status_reason_is_plain_and_whole`; `agents/operator/tests/test_failed_request_result.py::test_s265_a3_other_reason_is_stripped_and_whole`; `agents/operator/tests/test_failed_request_result.py::test_s265_a3_no_reason_names_the_error_type`; `agents/operator/tests/test_failed_request_result.py::test_s265_a4_failed_request_is_an_explained_refusal`; `agents/operator/tests/test_failed_request_ledger.py::test_s265_b1_failed_request_returns_its_one_fault_and_silent_row`; `agents/operator/tests/test_failed_request_agent.py::test_s265_c1_failed_explain_is_audited_and_answers_through_bus`; `agents/operator/tests/test_failed_request_agent.py::test_s265_c2_failed_interpret_is_audited_and_says_why`; `agents/operator/tests/test_failed_request_agent.py::test_s265_c3_failed_approve_never_enters_explicit_grammar`; `agents/operator/tests/test_failed_request_faults.py::test_s265_c5_failed_request_then_failed_audit_keeps_both_faults`; `agents/operator/tests/test_failed_request_faults.py::test_s265_c6_error_text_and_type_reach_no_graph_property`; `agents/operator/tests/test_failed_request_faults.py::test_s265_c7_malformed_json_is_a_fault_free_audited_refusal`; `surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors` |
| OPR-OUT-06 | 🟩 | `test_interpret_maps_all_ten_families_with_confirmation_policy`, `test_explain_returns_text_and_writes_audit_and_llm_call`; `agents/operator/tests/test_failed_request_agent.py::test_s265_c1_failed_explain_is_audited_and_answers_through_bus`; `agents/operator/tests/test_failed_request_agent.py::test_s265_c2_failed_interpret_is_audited_and_says_why` |
| SRF-FAIL-02 | Chat, MCP, and operator-tool errors reach the operator in plain words, not raw SDK JSON or tracebacks. | `surfaces/tests/test_dashboard_chat.py::test_chat_unbound_invalid_requests_and_method_guard`; `surfaces/tests/test_mcp_server.py::test_command_tool_refusal_returns_reason`; `surfaces/tests/test_mcp_server.py::test_error_paths_and_tool_catalog`; `surfaces/tests/test_chat_cutoff.py::test_d1_cutoff_chat_is_equal_on_both_vendors`; `surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors`; `surfaces/tests/test_chat_failed_request.py::test_s265_d2_status_sdk_rendering_is_never_shown` | 🟩 |
```

DRIFT-107 and DRIFT-108 status cells, verbatim:

```text
DRIFT-107: **CORRECTED (S265 / DL-286, operator v1.8, 2026-10-10).** Linked audits on both capabilities, one operator request fault and one plain reason, no grammar or graph error text; proven by `test_failed_request_agent.py` C1-C3, `test_failed_request_faults.py` C5-C6, and `test_chat_failed_request.py` D1-D3, with real adapters on fake SDKs. No vendor called.
DRIFT-108: **CORRECTED (S265 / DL-286, operator v1.8, 2026-10-10).** OPR-FAIL-01 now states malformed JSON is an explained refusal without a fault; production parsing unchanged. Proven by `agents/operator/tests/test_failed_request_faults.py::test_s265_c7_malformed_json_is_a_fault_free_audited_refusal` on non-JSON, a list and an empty reply.
```

Both operator rollup lines (`docs/laws/ledger.md`, then `docs/laws/INDEX.md`), verbatim:

```text
| operator | ✅ v1.8 (LOCKED) | 20 / 51 | 🟨 partial — **20 of 51 clauses proven** after S265 (DL-286) rewords and re-proves `OPR-FAIL-01`: failed requests are audited on both capabilities, one operator fault and one plain reason, no grammar or error text in graph; malformed JSON is a fault-free refusal; DRIFT-107/108 corrected; no clause added; before that S264 (DL-285) re-proves `OPR-STA-03` for vendor stop reasons and billed counts on both reply paths and adds/proves `OPR-FAIL-04` for audited, fault-free cut-offs with one sentence and explicit grammar preserved; DRIFT-106 corrected; before that S263 (DL-284) amends and re-proves `OPR-DEP-01` for provider effort resolution and pre-call model-family refusal; PARAM effort and CAP reconciled; before that S262 (DL-282) amends and re-proves `OPR-DEP-01` for the selected vendor, model resolution and no fallback; PARAM reconciled; before that S256 (DL-272) rewrites and proves `OPR-IDM-02`: duplicate commands share audit/intent while every model call has its own row; DRIFT-104 corrected; S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; 31 have a gray row |
| operator | ✅ LOCKED v1.8 (S265, DL-286) | 20 / 51 | S265 (DL-286) rewords and re-proves `OPR-FAIL-01`: failed requests are audited on both capabilities, one operator fault and one plain reason, no grammar or error text in graph; malformed JSON is a fault-free refusal; DRIFT-107/108 corrected; no clause added; before that S264 (DL-285) re-proves `OPR-STA-03` for vendor stop reasons and billed counts on both reply paths and adds/proves `OPR-FAIL-04` for audited, fault-free cut-offs with one sentence and explicit grammar preserved; DRIFT-106 corrected; before that S263 (DL-284) amends and re-proves `OPR-DEP-01` for provider effort resolution and pre-call model-family refusal; PARAM effort and CAP reconciled; before that S262 (DL-282) amends and re-proves `OPR-DEP-01` for the selected vendor, model resolution and no fallback; PARAM reconciled; before that S256 (DL-272) rewrites and proves `OPR-IDM-02`: duplicate commands share the audit and intent, but every model call has its own ledger row; DRIFT-104 corrected; S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; counters are clauses proven / clauses declared |
```

Law gate command and output:

```text
uv run python scripts/check_law_coverage.py
(no stdout or stderr)
LAW_GATE_EXIT=0
```

Every citation in those three rows, resolved to its file and clause docstring:

```text
OPR-FAIL-01: 14 live citations
  agents/operator/tests/test_operator_agent.py::test_interpret_llm_exception_returns_refusal [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_result.py::test_s265_a2_failed_request_lead_is_pinned [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_result.py::test_s265_a3_status_reason_is_plain_and_whole [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_result.py::test_s265_a3_other_reason_is_stripped_and_whole [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_result.py::test_s265_a3_no_reason_names_the_error_type [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_result.py::test_s265_a4_failed_request_is_an_explained_refusal [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_ledger.py::test_s265_b1_failed_request_returns_its_one_fault_and_silent_row [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_agent.py::test_s265_c1_failed_explain_is_audited_and_answers_through_bus [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_agent.py::test_s265_c2_failed_interpret_is_audited_and_says_why [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_agent.py::test_s265_c3_failed_approve_never_enters_explicit_grammar [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_faults.py::test_s265_c5_failed_request_then_failed_audit_keeps_both_faults [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_faults.py::test_s265_c6_error_text_and_type_reach_no_graph_property [exists; docstring cites OPR-FAIL-01]
  agents/operator/tests/test_failed_request_faults.py::test_s265_c7_malformed_json_is_a_fault_free_audited_refusal [exists; docstring cites OPR-FAIL-01]
  surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors [exists; docstring cites OPR-FAIL-01]
OPR-OUT-06: 4 live citations
  agents/operator/tests/test_operator_agent.py::test_interpret_maps_all_ten_families_with_confirmation_policy [exists; docstring cites OPR-OUT-06]
  agents/operator/tests/test_operator_agent.py::test_explain_returns_text_and_writes_audit_and_llm_call [exists; docstring cites OPR-OUT-06]
  agents/operator/tests/test_failed_request_agent.py::test_s265_c1_failed_explain_is_audited_and_answers_through_bus [exists; docstring cites OPR-OUT-06]
  agents/operator/tests/test_failed_request_agent.py::test_s265_c2_failed_interpret_is_audited_and_says_why [exists; docstring cites OPR-OUT-06]
SRF-FAIL-02: 6 live citations
  surfaces/tests/test_dashboard_chat.py::test_chat_unbound_invalid_requests_and_method_guard [exists; docstring cites SRF-FAIL-02]
  surfaces/tests/test_mcp_server.py::test_command_tool_refusal_returns_reason [exists; docstring cites SRF-FAIL-02]
  surfaces/tests/test_mcp_server.py::test_error_paths_and_tool_catalog [exists; docstring cites SRF-FAIL-02]
  surfaces/tests/test_chat_cutoff.py::test_d1_cutoff_chat_is_equal_on_both_vendors [exists; docstring cites SRF-FAIL-02]
  surfaces/tests/test_chat_failed_request.py::test_s265_d1_failed_chat_is_equal_on_both_paths_and_vendors [exists; docstring cites SRF-FAIL-02]
  surfaces/tests/test_chat_failed_request.py::test_s265_d2_status_sdk_rendering_is_never_shown [exists; docstring cites SRF-FAIL-02]
OPR-FAIL-01 exact spec words verified; operator v1.7 -> v1.8, 20 / 51 unchanged.
Operator footer: ## Green: 20 / 51
CITATION_EXIT=0
```

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
