# Sprint 01 — Kernel runtime: in-process bus + AgentBase

**Status:** active · **Branch:** `sprint-01-kernel-runtime` · **Build phase:** P1 (first slice)

## Goal

Make a trivial agent answer a **typed request over the in-process bus, end to end**,
with inbound/outbound payload validation and the central fault channel wired. This
is the runtime spine every real agent will stand on — proven cheaply and
deterministically, with **no external infrastructure**.

## Why (context)

- The boundary map (P0) is done: contracts exist, but nothing runs yet.
- `docs/architecture.md` §Communication describes the two-backend bus. This sprint
  builds **only the in-process backend** plus the agent lifecycle. The distributed
  (Celery) backend, databases, Neo4j, and MCP come in later sprints.
- Read first: `docs/architecture.md`, `kernel/contract.py` (the `AgentContract` /
  `Capability` descriptors), `kernel/envelope.py` (`AgentMessage`), `kernel/errors.py`
  (`AgentFault`, `fault_boundary`, `CollectingFaultSink`).

## Key design constraint (do not break)

The kernel must stay domain-pure: **`kernel/` imports nothing from `contracts/` or
`agents/`.** `AgentBase` validates payloads using the model classes carried *on the
`AgentContract` object passed to it at runtime* (`capability.request`,
`capability.response`) — it never imports a contract module. `import-linter` will
fail the build if this is violated.

## Deliverables

1. **`kernel/bus.py`**
   - `MessageBus` (Protocol): `register(recipient, capability, handler)` and
     `request(message: AgentMessage) -> AgentMessage`.
   - `InProcessBus(MessageBus)`: synchronous dispatch.
     - Constructor takes an optional `FaultSink` (default `CollectingFaultSink`).
     - `register(...)`: store `handler` keyed by `(recipient, capability)`.
       `handler` signature: `Callable[[dict], dict]` (validated payload in → payload out).
     - `request(msg)`:
       - unknown `(recipient, capability)` → return an `error` `AgentMessage`
         (`correlation_id = msg.id`, payload describes the miss). Do not raise.
       - otherwise run the handler inside `fault_boundary(self.sink, agent=msg.recipient,
         module="kernel.bus", capability=msg.capability, reraise=False)`. On success
         return a `response` message (`correlation_id = msg.id`, payload = handler output).
         On exception the boundary records the fault; return an `error` message whose
         payload carries `error_type`/`message` from the captured fault.

2. **`kernel/agent.py`**
   - `AgentBase`:
     - `__init__(self, contract: AgentContract, bus: MessageBus)`.
     - `bind() -> None`: for each `cap` in `contract.consumes`, register a wrapper that
       1) validates inbound: `request_model = cap.request.model_validate(payload)`,
       2) dispatches to the subclass handler for `cap.name`,
       3) validates outbound: `cap.response.model_validate(result)`,
       4) returns `result.model_dump(mode="json")`.
     - Handler lookup: subclasses register handlers via a small decorator or a
       `handlers: dict[str, Callable]` map — your call; keep it simple and typed.
   - Keep it generic over any contract. No domain logic here.

3. **`kernel/__init__.py`** — export `MessageBus`, `InProcessBus`, `AgentBase`.

4. **`tests/test_bus.py`** — define a tiny **test-only** contract (two pydantic
   payload models + an `AgentContract` with one `echo` capability) and an `EchoAgent`
   subclassing `AgentBase`, entirely inside the test module. Do **not** add anything
   to `agents/` or `contracts/` (that would change the real boundary map).
   Cover:
   - **round-trip**: request → response returns the echoed payload;
     `response.message_type == "response"`; `response.correlation_id == request.id`.
   - **inbound validation**: a malformed payload yields an `error` message (no crash)
     and records a fault on the sink with the right `source_*`.
   - **handler raising**: a handler that raises yields an `error` message and a fault
     on the sink carrying `source_module` / `error_type`.
   - **unknown capability**: yields an `error` message, not an exception.

## Steps

1. Branch `sprint-01-kernel-runtime` off `main`.
2. Write `kernel/bus.py` (header + < 200 lines).
3. Write `kernel/agent.py` (header + < 200 lines).
4. Export the new symbols from `kernel/__init__.py`.
5. Write `tests/test_bus.py` covering the four cases above.
6. Run `make ci`; fix until green. If coverage climbs, raise the floor in
   `pyproject.toml` (`--cov-fail-under` and `[tool.coverage.report] fail_under`) to the
   new measured value — never lower it.
7. Push the branch and hand back the report (below). Do not merge to `main`.

## Acceptance criteria

- `kernel/bus.py` and `kernel/agent.py` exist, each with a coding-agent header and
  under 200 lines.
- `import-linter` still reports the "Kernel is pure plumbing" contract **KEPT**.
- `tests/test_bus.py` passes all four cases.
- `make ci` is fully green; coverage at or above the (possibly raised) floor.
- No changes under `agents/` or `contracts/`; the boundary meta-test still passes.

## Out of scope (do NOT build this sprint)

Distributed/Celery bus · Postgres or Neo4j adapters · Alembic/migrations · MCP
binding · the observability/metrics adapter · any real agent. Each is its own later
sprint — flag if you think one is needed early.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts.
- New total coverage % and whether the floor was raised.
- Any design decision worth recording (handler-registration style, error payload
  shape) or anything that felt out of scope.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`.
