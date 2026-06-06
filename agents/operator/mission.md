# Operator LLM Agent

**Mission.** Translate the operator's human-language commands into typed,
policy-bound intents; explain system state from stored evidence; refuse or
escalate anything ambiguous or unsafe.

## Owns
- The allowed intent grammar and typed command schemas.
- Command audit trail and confirmation tokens.
- The LLM call ledger (every call recorded with prompt/response hashes).
- Evidence-grounded explanation/narration.

## Boundary — contract: `contracts/operator.py`
- **Consumes:** `interpret(HumanCommand) -> CommandResult`,
  `explain(ExplainRequest) -> Explanation`.
- **Emits:** `intent_parsed`, `command_refused`.
- **Depends on (messages only):** `supervisor` (to dispatch validated intents).

## Data ownership
- **Postgres:** `command_audits`, `command_confirmation_tokens`, `llm_call_ledger`.
- **Graph:** `CommandAudit`, `Intent` (`CommandAudit -[:RESULTED_IN]-> Intent`).

## External I/O (exclusive)
- LLM provider (OpenAI default, Ollama local) via the kernel client + ledger.

## MCP surface
- `interpret`, `explain`. **Also the MCP host** — the bounded bridge that lets an
  external LLM drive the system through the allowed command grammar.

## Never
- Invent trades outside the policy and data path.
- Bypass approval, stage, or capability gates.
- Submit broker actions directly.
- Mutate strategy parameters outside the approval and audit flow.
- Become a free-form, open-ended trading advisor.
