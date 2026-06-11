# Sprint 16 — Operator agent (P5 begins: intent parsing + model-call ledger)

**Status:** planned · **Branch:** `sprint-16-operator` · **Build phase:** P5 (operator + supervisor safety) · **Effort: M**

## Goal

Implement the `OperatorAgent` — the bounded LLM bridge that maps human-language commands to
typed, policy-bound intents. Two capabilities: `interpret(HumanCommand) -> CommandResult`
(natural language → `TypedIntent`, refusal, or clarification request) and
`explain(ExplainRequest) -> Explanation` (evidence-grounded graph query + LLM narration).
Every LLM call is recorded in an append-only `LLMCall` ledger; every parsed command produces a
`CommandAudit -[:RESULTED_IN]-> Intent` provenance record. No LLM is called in CI — a
`FakeLLMClient` makes tests fully deterministic and infra-free.

## Why (context)

- P5 bridges the human operator to the trading system via a typed, policy-bound grammar. The
  operator is the ONLY agent that calls an LLM (`external_io=("llm_provider",)` is exclusive).
- Read first: `docs/sprints/README.md` (guardrails + gate); `docs/architecture.md` (layers,
  the one rule, why `LLMClient` is a kernel primitive); `contracts/operator.py` (the two
  capabilities, `TypedIntent`, `CommandResult`, `IntentFamily`); `agents/operator/mission.md`
  (update it — it still references Postgres, which was retired in ADR-0001); `contracts/supervisor.py`
  (`TypedIntent` flows here in Sprint 17; understand the shape now); `kernel/bus.py` +
  `kernel/errors.py` (`AgentBase`, `fault_boundary`); `agents/reporter/agent.py`
  (reference for a clean, well-sized agent.py); `agents/supervisor/agent.py` (how P4 partial
  implementation was handled — same pattern applies here for `explain`).
- Sprint 17 will complete P5: `dispatch_intent`, `system_status`, `flag_for_human` in the
  supervisor + the capability matrix + hard-NO surface + policy-parity test.

## Key design constraints (do not break)

- **`FakeLLMClient` for all CI tests.** The `AnthropicLLMClient` is production; the `FakeLLMClient`
  is a deterministic stub keyed on input keywords. Tests must never hit a real API or require
  `ANTHROPIC_API_KEY` — if the key is absent, `AnthropicLLMClient` should raise `ConfigurationError`
  at construction, not at call time.
- **`LLMClient` is a kernel protocol.** `kernel/llm.py` defines the protocol and the fake;
  `agents/operator/` imports it and provides the Anthropic backend. The kernel itself does NOT
  import the `anthropic` SDK — only the operator does.
- **The one rule.** `agents/operator/` imports `kernel` + `contracts` only. It never imports
  another agent. The `explain` capability reads the graph directly (same pattern as reporter).
- **Ledger is append-only.** Every `LLMCall` node is written once; never mutated. The `CommandAudit`
  node is written once with the final outcome. Idempotency key = `f"audit:{correlation_id}"`.
- **Confirmation policy is in the grammar, not the LLM.** The `requires_confirmation` field is
  set by the domain grammar after parsing — it is NOT left to the LLM to decide. The intent
  mapper overrides with the declared policy per family.
- **Refusals are explained, never silent.** `CommandResult(outcome="refused", message=Explanation(...))`
  must always include a summary of why.
- **Small files, headers, < 200 lines; no magic numbers.**

## Confirmation policy (bake this into `domain/grammar.py`, not prompts)

| Family | `requires_confirmation` | Rationale |
| --- | --- | --- |
| `status` | `False` | Read-only, no side-effect |
| `explain` | `False` | Read-only, no side-effect |
| `run` | `True` | Initiates a trading run; irreversible until completed |
| `approve` | `True` | Approves a pending order or proposal |
| `reject` | `True` | Rejects a pending item |
| `modify` | `True` | Parameter change; requires audit trail |
| `mode` | `True` | Switches operating mode |
| `stage` | `True` | Stage promotion/demotion is a risk gate |
| `pause` | `False` | Stop signal; low risk, reversible |
| `resume` | `False` | Restart signal; low risk |

## Deliverables

### 1. Kernel LLM protocol — `kernel/llm.py`

```python
class LLMClient(Protocol):
    def complete(self, *, system: str, user: str, tool_schema: dict) -> str:
        """Call the LLM and return the tool-call result as a JSON string."""
        ...

class FakeLLMClient:
    """Deterministic stub for CI. Returns canned JSON keyed on user text keywords."""
    def __init__(self, responses: dict[str, str]):
        self._responses = responses
    def complete(self, *, system: str, user: str, tool_schema: dict) -> str:
        for key, response in self._responses.items():
            if key.lower() in user.lower():
                return response
        return '{"family": "status", "parameters": {}, "outcome": "intent"}'
```

Export `LLMClient`, `FakeLLMClient` from `kernel/__init__.py`.

`AnthropicLLMClient` lives in `agents/operator/llm_anthropic.py` (NOT in kernel). Raises
`ConfigurationError` at construction if `ANTHROPIC_API_KEY` is absent:

```python
class AnthropicLLMClient:
    def __init__(self, *, api_key: str, model: str = "claude-sonnet-4-6"):
        ...
    def complete(self, *, system: str, user: str, tool_schema: dict) -> str:
        # Use Anthropic tool use (structured output):
        # client.messages.create(
        #     model=self.model, max_tokens=512,
        #     system=system,
        #     messages=[{"role": "user", "content": user}],
        #     tools=[{"name": "parse_intent", "description": "...", "input_schema": tool_schema}],
        #     tool_choice={"type": "tool", "name": "parse_intent"},
        # )
        # Extract the tool_use block's JSON input field and return it as a string.
        ...
```

### 2. Operator settings — `agents/operator/settings.py`

`OperatorSettings(AgentSettings)`, `env_prefix="OPERATOR_"`. Justified tunables:
- `model` (default `"claude-sonnet-4-6"`, why: production default for intent parsing)
- `max_tokens` (default 512, ge=64, le=4096, why: intent parsing needs only a short
  structured response; cap prevents runaway cost)
- `explain_max_evidence_nodes` (default 20, ge=1, le=100, why: cap the graph evidence
  window for the explain prompt to control LLM context size)

### 3. Operator domain — `agents/operator/domain/`

**`agents/operator/domain/grammar.py`** — the 10-family intent grammar:
- `INTENT_FAMILIES: dict[IntentFamily, FamilySpec]` where `FamilySpec` has
  `description`, `params: tuple[str, ...]`, and `requires_confirmation: bool`.
  Populate from the confirmation policy table above.
- `apply_confirmation_policy(family: IntentFamily, intent: TypedIntent) -> TypedIntent`:
  returns the intent with `requires_confirmation` set by policy, ignoring the LLM's value.

**`agents/operator/domain/prompts.py`** — prompt builders:
- `build_interpret_system() -> str`: system prompt describing the trading system and the
  10 intent families with their parameters.
- `build_interpret_user(command: HumanCommand) -> str`: `f"Command: {command.text}\nActor: {command.actor}\nChannel: {command.channel}"`
- `INTENT_TOOL_SCHEMA: dict` — the JSON schema for the `parse_intent` tool, conforming to
  what Anthropic's API expects:
  ```python
  INTENT_TOOL_SCHEMA = {
      "type": "object",
      "properties": {
          "outcome": {"type": "string", "enum": ["intent", "refused", "needs_clarification"]},
          "family": {"type": "string", "enum": [<all 10 families>]},
          "parameters": {"type": "object"},
          "reason": {"type": "string"},
      },
      "required": ["outcome"],
  }
  ```
- `build_explain_system() -> str`: explain-mode system prompt.
- `build_explain_user(subject: str, evidence: list[dict]) -> str`: includes serialized
  graph evidence nodes.

**`agents/operator/domain/evidence.py`** — graph evidence retrieval for `explain`:
- `gather_evidence(graph, subject: str, max_nodes: int) -> list[dict]`:
  Heuristic search: if subject mentions a ticker, look for recent `Recommendation`,
  `OrderIntent`, `Fill`, `Position`, `CloseDecision` nodes for that ticker.
  If subject mentions "status" or "system", pull recent `Snapshot`, `MonitorRun`, `PMRun`.
  Return a list of node prop dicts (label + key + props). Return at most `max_nodes`.

### 4. Operator store — `agents/operator/store.py`

```python
def write_llm_call(graph, *, correlation_id, model, prompt_hash, response_hash,
                   tokens_in, tokens_out, latency_ms) -> Node:
    # merge_node("LLMCall", f"llmcall:{correlation_id}", {...})

def write_command_audit(graph, *, correlation_id, actor, channel, text,
                        outcome, llm_call_node) -> Node:
    # merge_node("CommandAudit", f"audit:{correlation_id}", {...})
    # add_edge(audit_node, llm_call_node, "PRODUCED_BY")

def write_intent(graph, *, correlation_id, audit_node, intent) -> Node:
    # merge_node("Intent", f"intent:{correlation_id}", {
    #     "family": intent.family, "parameters": json.dumps(intent.parameters),
    #     "requires_confirmation": intent.requires_confirmation
    # })
    # add_edge(audit_node, intent_node, "RESULTED_IN")
```

Owns labels: `CommandAudit`, `Intent`, `LLMCall` (add `LLMCall` to `contracts/operator.py`
`owns_graph` — it is not currently listed). Verify no other agent owns these labels.

### 5. Operator ledger — `agents/operator/ledger.py`

```python
@contextmanager
def record_llm_call(graph, *, correlation_id, model):
    """Context manager that times the call and writes an LLMCall node on exit."""
    # records start time, yields a namespace for the response (tokens_in, tokens_out, hashes)
    # writes LLMCall node on exit (success or fault)
```

Used inside `agent.py` to wrap every `llm.complete(...)` call.

### 6. Operator agent — `agents/operator/agent.py`

`OperatorAgent(AgentBase)`, inject `graph`, `llm`, `settings`, `sink`. ≤ 150 lines.

**`interpret` handler:**
1. Validate `HumanCommand`.
2. Build prompts from `domain/prompts.py`.
3. Inside `record_llm_call(...)`, call `self._llm.complete(...)`.
4. Parse the JSON response; if parsing fails → `CommandResult(outcome="refused", ...)`.
5. Apply confirmation policy via `apply_confirmation_policy`.
6. Write `CommandAudit` + `Intent` (or `CommandAudit` without Intent on refusal).
7. Return `CommandResult`.

**`explain` handler:**
1. Validate `ExplainRequest`.
2. Gather evidence via `domain/evidence.gather_evidence(...)`.
3. Build explain prompt.
4. Inside `record_llm_call(...)`, call `self._llm.complete(...)`.
5. Parse response as plain text.
6. Write `CommandAudit` (no Intent — explain doesn't produce an intent).
7. Return `Explanation`.

**Do NOT implement:** any attempt to send `TypedIntent` to the supervisor (Sprint 17). The operator
produces an intent and records it; Sprint 17 wires operator → supervisor for actual dispatch.

### 7. Operator `__init__.py`

Export `OperatorAgent`. Update `agents/operator/mission.md`:
- Remove stale Postgres references (`command_audits`, `command_confirmation_tokens`,
  `llm_call_ledger` tables).
- Update graph section: `CommandAudit`, `Intent`, `LLMCall` nodes.
- Update external I/O: `LLMClient` protocol (Anthropic backend in production; `FakeLLMClient`
  in tests).

### 8. Contract update — `contracts/operator.py`

Add `"LLMCall"` to `owns_graph`. No other contract changes this sprint.

### 9. Tests — `agents/operator/tests/`

Build a `FakeLLMClient` fixture that returns canned intent JSON for these inputs:

| Command keyword | Expected `family` | `requires_confirmation` |
| --- | --- | --- |
| "run" / "scan" | `run` | `True` |
| "status" | `status` | `False` |
| "approve" | `approve` | `True` |
| "reject" | `reject` | `True` |
| "explain" / "why" | `explain` | `False` |
| "pause" | `pause` | `False` |
| "resume" | `resume` | `False` |
| "change" / "modify" | `modify` | `True` |
| "promote" / "stage" | `stage` | `True` |
| "mode" | `mode` | `True` |

**`test_operator_agent.py`**:
- `interpret` maps each of the 10 families correctly (confirmation policy applied regardless of
  LLM output).
- `interpret` on malformed LLM JSON → `CommandResult(outcome="refused")`, no crash.
- `interpret` writes `CommandAudit` + `Intent` + `LLMCall` nodes to graph.
- `interpret` when `FakeLLMClient` returns `"refused"` → `CommandResult(outcome="refused")`
  with non-empty `message.summary`.
- `interpret` when `FakeLLMClient` returns `"needs_clarification"` → correct outcome, no Intent node.
- `explain` writes `CommandAudit` + `LLMCall` nodes; returns non-empty `Explanation`.
- **Ledger append-only**: calling `interpret` twice with the same `correlation_id` results in
  exactly one `LLMCall` node (idempotent merge).
- Boundary meta-test: `CommandAudit`, `Intent`, `LLMCall` claimed by exactly one agent.

**`test_operator_grammar.py`** — pure domain tests, no bus:
- All 10 families are in `INTENT_FAMILIES`.
- `apply_confirmation_policy` overrides LLM-supplied value with the declared policy for each family.
- `build_interpret_system()` mentions all 10 family names.

**Coverage floor** — ratchet from 100.00; operator and kernel LLM additions must be covered.

## Steps

1. Branch `sprint-16-operator` off `main`.
2. Read `contracts/operator.py` + `agents/operator/mission.md` + `contracts/supervisor.py` before writing a line.
3. `kernel/llm.py` (protocol + FakeLLMClient); export from `kernel/__init__.py`.
4. `agents/operator/settings.py`; `domain/grammar.py`; `domain/prompts.py`; `domain/evidence.py`.
5. `agents/operator/store.py`; `agents/operator/ledger.py`.
6. `agents/operator/llm_anthropic.py` (Anthropic backend — not tested in CI, just constructed).
7. `agents/operator/agent.py` (≤ 150 lines); `__init__.py`; update `mission.md`; update `contracts/operator.py`.
8. Tests: grammar unit tests first, then agent tests with `FakeLLMClient`.
9. Run the gate. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- `OperatorAgent.interpret` produces `CommandResult` with correctly-typed `TypedIntent` (all 10
  families exercised in tests); confirmation policy applied by grammar, not LLM.
- `OperatorAgent.explain` returns non-empty `Explanation`; evidence gathered from graph.
- `CommandAudit`, `Intent`, `LLMCall` nodes written; `CommandAudit -[:RESULTED_IN]-> Intent` edge
  present for intent outcomes; `CommandAudit -[:PRODUCED_BY]-> LLMCall` edge present for all.
- Ledger append-only: idempotent `LLMCall` node per `correlation_id`.
- `FakeLLMClient` makes all tests infra-free; `AnthropicLLMClient` raises at construction without
  `ANTHROPIC_API_KEY` — zero CI failures from missing keys.
- Refusals and clarifications are non-empty `Explanation`s — never silent.
- All modules headered, < 200 lines; `agent.py` ≤ 150; tunables justified.
- `make ci` green at/above the coverage floor; import-linter 4/4 kept.

## Out of scope (do NOT build this sprint)

`supervisor.dispatch_intent` (Sprint 17); the full capability matrix and hard-NO surface (Sprint 17);
the `operator → supervisor` bus call after intent parsing (Sprint 17); confirmation token flow
(Sprint 17); the `policy_parity` test (Sprint 17); MCP binding for `interpret` + `explain` (Sprint 17
or later); a real LLM integration test (mark `@pytest.mark.integration` and skip in CI without key).
Flag anything you think is needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts (confirm `agent.py` ≤ 150).
- How `FakeLLMClient.complete` works — keyword matching approach, edge cases handled.
- Whether the confirmation policy override worked cleanly or needed a grammar design change.
- How `explain` retrieves graph evidence (which node types, what traversal).
- New coverage % and floor; LLMCall idempotency confirmed.
- Anything that felt out of scope or needs a Sprint 17 design note.

The planning agent will review, merge to `main`, update docs, and plan Sprint 17 (supervisor
capability gate + hard-NO + policy-parity → P5 exit).
