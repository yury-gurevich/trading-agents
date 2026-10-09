# `Operator` — Laws

**Prefix:** `OPR` · **status:** LOCKED v1.7 · **Owner:** Yury Gurevich

> Translate the operator's human-language commands into typed, policy-bound intents;
> explain system state from stored evidence; refuse or escalate anything ambiguous or unsafe.

Each clause has a stable ID (`OPR-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **OPR-IDN-01** — The operator's single job is bounded LLM translation: accept a human text
  command or explain request, call the LLM within a structured tool schema, and emit one typed
  `TypedIntent`, a refusal, or a clarification request. It is the sole **operator-command** LLM
  boundary — the only path from human text to a `TypedIntent`. It is **not** the only agent
  permitted to call a model: any agent may do so under its own laws, bounded parameters and fault
  boundary ([ADR-0020](../../../docs/decisions/0020-llmcall-is-substrate-not-the-operators.md)).
- **OPR-IDN-02** — The operator exclusively writes these graph labels (single-writer rule):
  `CommandAudit`, `Intent`. **`LLMCall` is deliberately not in this list**: it is a
  substrate-level audit record written by *every* agent that calls a model, into one shared cost
  ledger, and is therefore multi-writer by design (ADR-0020).

## Inputs (`IN`)

- **OPR-IN-01** — `interpret` accepts `HumanCommand { text: str, actor: str, channel:
  Literal["dashboard","phone","mcp"] }`. No other formats accepted.
- **OPR-IN-02** — `explain` accepts `ExplainRequest { subject: str }`. `subject` is a
  human-readable question about system state.
- **OPR-IN-03** — Malformed input → `CommandResult(outcome="refused", ...)` returned; fault
  recorded; never raises to bus.
- **OPR-IN-04** — The operator accepts commands only from authenticated actors on declared
  channels (`dashboard`, `phone`, `mcp`). Unknown channels are rejected.

## Triggers (`TRG`)

- **OPR-TRG-01** — `interpret` triggered by RPC request from the surfaces CLI, MCP tool, or
  dispatcher.
- **OPR-TRG-02** — `explain` triggered by RPC request only.
- **OPR-TRG-03** — No event subscription; the operator never self-triggers.

## Outputs (`OUT`)

- **OPR-OUT-01** — `interpret` returns `CommandResult { outcome, intent: TypedIntent | None,
  message: Explanation }`.
- **OPR-OUT-02** — `outcome` is exactly one of `"intent"`, `"refused"`, or
  `"needs_clarification"`.
- **OPR-OUT-03** — `TypedIntent { family, parameters, requires_confirmation, provenance }` is
  returned only when `outcome == "intent"`.
- **OPR-OUT-04** — `explain` returns `Explanation { summary }` from LLM over graph evidence.
- **OPR-OUT-05** — Every refusal and clarification request is explained; never a silent empty
  result.
- **OPR-OUT-06** — A `CommandAudit` graph node is written for every `interpret` and `explain`
  call, linking to the `LLMCall` node.
- **OPR-OUT-07** — An `Intent` graph node is written when `outcome == "intent"`, linked to the
  `CommandAudit`.

## Prohibitions (`NEV`)

- **OPR-NEV-01** — Never invents trades outside the policy and data path. `TypedIntent.family`
  is one of the declared `IntentFamily` literals; it cannot invent a new family at runtime.
- **OPR-NEV-02** — Never bypasses approval, stage, or capability gates. Intents that require
  confirmation have `requires_confirmation=True`; the supervisor enforces the gate.
- **OPR-NEV-03** — Never submits broker actions directly. Intents are routed through the
  supervisor's `dispatch_intent`.
- **OPR-NEV-04** — Never mutates strategy parameters outside the approval and audit flow.
  Parameter changes are typed intents that go through the review queue.
- **OPR-NEV-05** — Never becomes a free-form open-ended trading advisor. The LLM is constrained
  by a strict tool schema (`INTENT_TOOL_SCHEMA`); free-form responses are refused.
- **OPR-NEV-06** — Never logs raw LLM API keys or operator credentials to the graph or any
  audit record.

## State & effects (`STA`)

- **OPR-STA-01** — Stateless between calls. No conversation history is maintained between `interpret`
  calls; each is an independent single-turn LLM exchange.
- **OPR-STA-02** — Graph writes are append-only. `CommandAudit`, `LLMCall`, and `Intent` nodes
  accumulate; none are overwritten.
- **OPR-STA-03** — Every LLM call is recorded in an `LLMCall` graph node via `record_llm_call`
  context manager (model, prompt, response, timestamp). The row carries the vendor's own stop
  reason and token counts whether the reply finished or the vendor cut it off. A client that
  exposes neither is recorded as `unknown` with a stamped estimate.

## Determinism & idempotency (`IDM`)

- **OPR-IDM-01** — The operator is non-deterministic (LLM output may vary across identical
  inputs). The graph audit is the stable record; `CommandAudit.outcome` is the single source of
  truth.
- **OPR-IDM-02** — Duplicate `interpret` calls with the same text and no request id share one
  correlation id (`OPR-IDM-03`), and so one `CommandAudit` and one `Intent`. Each LLM call they
  make is its own `LLMCall` row: the first under the correlation id, each later one with a
  `:repeat-N` suffix. No LLM call is deduplicated.
- **OPR-IDM-03** — Correlation IDs are derived from `(actor, channel, text)` hash; the same
  command from the same actor produces the same `correlation_id`, making audit logs searchable.

## Ordering & concurrency (`ORD`)

- **OPR-ORD-01** — No ordering dependency between `interpret` calls.
- **OPR-ORD-02** — Concurrent calls are safe (no shared mutable state); each produces
  independent graph nodes.

## Failure, recovery & rollback (`FAIL`)

- **OPR-FAIL-01** — LLM call failure (network error, timeout, malformed JSON): `fault_boundary`
  captures; `CommandResult(outcome="refused", ...)` returned; fault emitted.
- **OPR-FAIL-02** — LLM returns unrecognised intent family or missing required fields: `parse_json`
  returns `None`; result is `outcome="refused"`.
- **OPR-FAIL-03** — Graph write failure (CommandAudit / LLMCall node): fault recorded; the
  `CommandResult` is still returned.
- **OPR-FAIL-04** — A reply the vendor cut off at the output cap is neither a fault nor an
  answer. It is recorded as `OPR-STA-03` says; `interpret` reads it as a refusal whose reason
  is `CUT_OFF_REPLY`, and the explicit command grammar still applies; `explain` returns
  `CUT_OFF_REPLY`; no part of the cut reply is shown; the `CommandAudit` is written and linked
  to its `LLMCall` as for any reply; the same on every vendor. `CUT_OFF_REPLY` is one fixed
  sentence that says the reply was cut off and names no vendor, model, number or the word
  *token*; its letters are pinned by a test, not quoted here.

## Type alignment (`TYP`)

- **OPR-TYP-01** — The operator payload types carry, at minimum, the fields its own clauses
  require; the clause, not `contracts/operator.py`, is the authority on what must be present.
  `CommandResult` carries `outcome`, `intent`, and `message` (`OPR-OUT-01`/`OPR-OUT-02`).
  `TypedIntent` carries `family`, `parameters`, `requires_confirmation`, and `provenance`
  (`OPR-OUT-03`/`OPR-TYP-02`/`OPR-TYP-03`). `HumanCommand` carries `text`, `actor`, `channel`, and
  `request_id` (`OPR-IN-01`/`OPR-OBS-01`/`OPR-IDM-03`).
- **OPR-TYP-02** — `TypedIntent.family` is constrained to `IntentFamily` literals; no runtime
  extension.
- **OPR-TYP-03** — `requires_confirmation: bool` is always present on `TypedIntent`; never None.

## Security & privilege (`SEC`)

- **OPR-SEC-01** — The LLM client (`LLMClient`) is injected; the operator holds no API keys
  directly. Keys live in env-vars only, accessed through the kernel `FakeLLMClient` or the real
  client's constructor.
- **OPR-SEC-02** — Never logs LLM API credentials, session tokens, or raw operator text to the
  graph beyond what `LLMCall` intentionally records (model, prompt, response).
- **OPR-SEC-03** — Cannot escalate privilege. Intents always flow through the supervisor's
  capability gate; the operator has no direct path to broker or stage-change actions.
- **OPR-SEC-04** — `explain_max_evidence_nodes=20` bounds the graph data sent to the LLM; prevents
  exfiltrating unbounded graph contents through the LLM context.
- **OPR-SEC-05** — Revocable without breaking the system; if the operator is down, no commands
  are parsed but the trading pipeline continues autonomously.

## Dependencies (`DEP`)

- **OPR-DEP-01** — `DEP-LLM` — the declared LLM provider (or injected FakeLLMClient);
  sole external call. Provider selection never falls back to another vendor; an empty model
  and an empty effort resolve that provider's defaults, while explicit values are passed as set.
  An explicit model whose name belongs to another provider's family is refused before any call.
- **OPR-DEP-02** — `DEP-POSTGRES` — graph for `CommandAudit`, `Intent`, `LLMCall` writes and
  evidence reads for `explain`.
- **OPR-DEP-03** — `DEP-BUS` — routes resulting `TypedIntent` to `supervisor.dispatch_intent`
  (via surfaces, not directly).

## Observability & audit (`OBS`)

- **OPR-OBS-01** — Every command is recorded in a `CommandAudit` node with `actor`, `channel`,
  `text`, `outcome`, and a link to the `LLMCall`. Full audit trail without the RPC response.
- **OPR-OBS-02** — `LLMCall` node captures prompt + response; operator drift is diagnosable from
  the graph alone.
- **OPR-OBS-03** — Refusals are recorded with `outcome="refused"`; never disappear silently.

## Performance envelope (`PERF`)

- **OPR-PERF-01** — `max_tokens=4096` caps thinking *plus* structured output together;
  controls both cost and latency. On models where thinking is on by default a tighter
  ceiling is spent reasoning before any tool call is emitted, so the parse returns refused.
- **OPR-PERF-02** — `explain_max_evidence_nodes=20` caps graph traversal before LLM call.
- **OPR-PERF-03** — Single-turn calls (no streaming); latency dominated by LLM round-trip.

## Capability declaration (`CAP`)

```json
{
  "llm": {
    "operations": ["complete"],
    "schema": "tool_use",
    "max_tokens": 4096,
    "effort": ""
  },
  "graph": {
    "operations": ["append_write", "read"],
    "labels_owned": ["CommandAudit", "Intent", "LLMCall"],
    "labels_read": ["Flag", "Fault", "MonitorRun", "Snapshot"]
  },
  "messaging": {
    "operations": ["request"],
    "peers": ["supervisor"]
  }
}
```

## Parameters (`PARAM`)

| Name | Value | Type | Tunable | Rationale |
| --- | --- | --- | --- | --- |
| `llm_provider` | `"anthropic"` | `str` | YES | Operator-declared provider; selection is an operator act, never an automatic fallback |
| `model` | `""` | `str` | YES | Empty resolves `default_model_for(llm_provider)` (`claude-opus-5` or `gpt-5.5`); an explicit model wins; every call records the resolved value |
| `effort` | `""` | `""\|none\|low\|medium\|high\|xhigh\|max` | YES | Empty resolves the provider's deepest operator effort (`max` on Anthropic, `xhigh` on OpenAI); explicit values pass as set for the vendor's model to accept or refuse, without translating the effort ladder |
| `max_tokens` | `4096` | `int ≥ 64 ≤ 4096` | YES | Caps thinking plus structured output together; too tight and the parse refuses before emitting a tool call |
| `explain_max_evidence_nodes` | `20` | `int ≥ 1 ≤ 100` | YES | Bound graph evidence included in explanation prompts |
| `system_prompt` | `""` | `str` | YES | Champion slot for DSPy-compiled interpret prompt (ADR-0010); empty = dynamic construction |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| — | — | — | no known drift |

## Changelog

- v1.7 — S264 / DL-285 (2026-10-10): `OPR-STA-03` also records vendor stop reasons
  and billed token counts on finished and cut-off replies, retaining stamped estimates for
  clients without metadata. Adds `OPR-FAIL-04`: cut-offs are recorded and audited without a
  fault or partial answer, with one fixed sentence and the explicit grammar preserved on
  every vendor. Unit-proven through real adapters on fake SDKs; no failed-request change.

- v1.6 — S263 / DL-284 (2026-10-09): `OPR-DEP-01` also resolves an empty effort
  from the selected provider and refuses an explicit model from another provider's family
  before any call. PARAM effort defaults to empty and accepts `none`; CAP follows that default.
  Re-proven on Responses wire replay, effort resolution and model-family refusal. No clause added.

- v1.5 — S262 / DL-282 (2026-10-09): `OPR-DEP-01` names the declared provider and its
  no-fallback/model-resolution rules. PARAM adds `llm_provider`, makes `model` empty with
  provider resolution, and names provider-neutral effort. The container retains its fake client.

- v1 — authored S71 and locked immediately (full first-principles cycle).
- v1.1 — S72: added `system_prompt` tunable (ADR-0010 immediate consequence); wired into `_interpret_command`.
- v1.2 — chore-anthropic-effort-max: added the `effort` tunable (Anthropic `output_config`,
  default `max`) and raised `max_tokens` 512 → 4096, because effort-driven thinking shares
  that ceiling with the structured output. `model` default moved `claude-sonnet-4-6` →
  `claude-opus-5`: the deployed container never reads `.env`, so the code default — not the
  operator's local file — is what the fleet actually runs.

- **v1.1 — `chore-llmcall-substrate` (2026-08-01), per [ADR-0020](../../../docs/decisions/0020-llmcall-is-substrate-not-the-operators.md).**
  A **narrowing** of two existing clauses, not a new declaration — which is why it needed an ADR
  rather than the S152 amendment convention (that convention governs *lacking declarations* of
  decided capabilities, not scope reductions on locked, proven clauses).
  - `OPR-IDN-01` — *"the sole LLM boundary"* → *"the sole **operator-command** LLM boundary"*.
    *Why:* S153 makes the deliberator call a model directly. Leaving the broader sentence standing
    while narrowing only the label claim would have left a known-untrue clause in a constitution.
    The operator's real job — the only path from human text to a `TypedIntent` — is unchanged.
  - `OPR-IDN-02` — `LLMCall` removed from the single-writer list; `CommandAudit` and `Intent`
    remain exclusive. *Why:* an audit record of a provider call carries no operator concept and no
    trading concept; it is substrate (ADR-0012). It is also already a **cost ledger** read by
    `surfaces/dashboard/llm_costs.py` and the `/audit-costs` skill, so a per-agent label would have
    hidden the system's largest LLM spender from the bill while the report still rendered a
    confident total.
  - `contracts/operator.py` — `owns_graph` narrowed to `("CommandAudit", "Intent")`.
  - **`OPR-IDN-02` stays 🟩.** `test_operator_boundary_claims_graph_labels_once` was re-pointed to
    the amended wording and still proves it exactly — the clause remains fully proven, and the
    assertion was **not** loosened to accommodate the change. A second test pins the exclusion so
    `LLMCall` cannot drift back in.
  - The operator's own LLM-calling behaviour, prompts, tools and outputs are **unchanged**. Nothing
    it does today is altered; only its claim over what *other* agents may do.
- v1.3 — S205 rewrites `OPR-TYP-01` from a file-as-oracle contract assertion into explicit
  required fields for `CommandResult`, `TypedIntent`, and `HumanCommand`. No contract shape changes.
- v1.4 — S256 / DL-272 (2026-10-08). Rewrites `OPR-IDM-02`: identical commands
  without a request id reuse their correlation-keyed audit and intent, as the code
  already does, while every paid model call now has its own ledger row. Corrects
  DRIFT-104; no other clause changes.
