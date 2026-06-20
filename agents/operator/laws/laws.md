# `Operator` — Laws

**Prefix:** `OPR` · **status:** LOCKED v1 · **Owner:** Yury Gurevich

> Translate the operator's human-language commands into typed, policy-bound intents;
> explain system state from stored evidence; refuse or escalate anything ambiguous or unsafe.

Each clause has a stable ID (`OPR-CAT-NN`). IDs are append-only (conventions §2). A clause is
green only when a functional test cites its ID (conventions §3). Tests + status live in
`test-plan.md`.

## Identity & purpose (`IDN`)

- **OPR-IDN-01** — The operator's single job is bounded LLM translation: accept a human text
  command or explain request, call the LLM within a structured tool schema, and emit one typed
  `TypedIntent`, a refusal, or a clarification request. It is the sole LLM boundary.
- **OPR-IDN-02** — The operator exclusively writes these graph labels (single-writer rule):
  `CommandAudit`, `Intent`, `LLMCall`.

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
  context manager (model, prompt, response, timestamp).

## Determinism & idempotency (`IDM`)

- **OPR-IDM-01** — The operator is non-deterministic (LLM output may vary across identical
  inputs). The graph audit is the stable record; `CommandAudit.outcome` is the single source of
  truth.
- **OPR-IDM-02** — Duplicate `interpret` calls with the same text produce separate `CommandAudit`
  and `LLMCall` nodes. No deduplication.
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

## Type alignment (`TYP`)

- **OPR-TYP-01** — `CommandResult`, `TypedIntent`, and `HumanCommand` match `contracts/operator.py`
  exactly.
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

- **OPR-DEP-01** — `DEP-LLM` — Anthropic Claude (or injected FakeLLMClient); sole external call.
- **OPR-DEP-02** — `DEP-NEO4J` — graph for `CommandAudit`, `Intent`, `LLMCall` writes and
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

- **OPR-PERF-01** — `max_tokens=512` caps LLM output length; controls both cost and latency.
- **OPR-PERF-02** — `explain_max_evidence_nodes=20` caps graph traversal before LLM call.
- **OPR-PERF-03** — Single-turn calls (no streaming); latency dominated by LLM round-trip.

## Capability declaration (`CAP`)

```json
{
  "llm": {
    "operations": ["complete"],
    "schema": "tool_use",
    "max_tokens": 512
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
| `model` | `"claude-sonnet-4-6"` | `str` | YES | Production default for structured intent parsing |
| `max_tokens` | `512` | `int ≥ 64 ≤ 4096` | YES | Structured output needs short output; cap controls cost |
| `explain_max_evidence_nodes` | `20` | `int ≥ 1 ≤ 100` | YES | Bound graph evidence included in explanation prompts |
| `system_prompt` | `""` | `str` | YES | Champion slot for DSPy-compiled interpret prompt (ADR-0010); empty = dynamic construction |

## Divergence register

| ID | Law says | Code / contract says | Decision |
| --- | --- | --- | --- |
| — | — | — | no known drift |

## Changelog

- v1 — authored S71 and locked immediately (full first-principles cycle).
- v1.1 — S72: added `system_prompt` tunable (ADR-0010 immediate consequence); wired into `_interpret_command`.
