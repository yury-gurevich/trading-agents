<!-- Agent: planning | Role: sprint handover -->
# Sprint 22 — MCP tool-binding (P1 closes)

**Status:** planned · **Branch:** `sprint-22-mcp-tool-binding` · **Build phase:** P1 remainder · **Effort: M**

## Goal

Expose the trading-agents operator surface as an MCP server so that Claude and other AI
assistants can send natural-language commands, inspect system state, and read position
narratives through the same bounded gateway the CLI uses. This closes the last open P1
item ("MCP binding remains") noted in `docs/build-plan.md`.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/architecture.md` (surfaces layer, never-drive
  constraint); `docs/build-plan.md` (P1 status: MCP binding + RAG remain);
  `kernel/contract.py` (`AgentContract.mcp_tools` tuple + `Capability.mcp: bool` — these
  declare which capabilities are MCP-accessible; generate tool schemas from them);
  `contracts/operator.py` (`mcp_tools=("interpret", "explain")`);
  `contracts/reporter.py` (`mcp_tools=("report", "narrative")`);
  `contracts/supervisor.py` (`mcp_tools=("system_status", "flag_for_human")`);
  `surfaces/context.py` (`paper_context`, `test_context` — same factories the CLI uses);
  `surfaces/cli_commands.py` (bus-call pattern with `AgentMessage` — replicate, don't
  import from CLI modules; the MCP server is a peer of the CLI, not built on top of it);
  `pyproject.toml` (`mcp>=1.0` is an optional extra; must move to dev group for CI — see
  Part A); `surfaces/render.py` (**187L — MCP server must not add to this file**; returns
  JSON, not text).

- **MCP server is async; bus calls are synchronous.** Use `asyncio.to_thread` to call the
  synchronous bus from the async MCP handler. Tests call the synchronous `_dispatch_tool`
  function directly — no async infrastructure needed in tests.

- **`mcp` package is already typed-but-not-installed.** It is in `mypy.overrides
  ignore_missing_imports` (meaning mypy skips it). After moving to the dev group, remove it
  from `ignore_missing_imports` — or keep it there and add a `# type: ignore` on the import
  in `mcp_server.py` if no stubs are available. Do not break `mypy --strict`.

- **Confirmation semantics:** the MCP `command` tool does NOT auto-confirm. An AI assistant
  that receives `"confirmation required — resubmit with confirmed=true"` in the response is
  expected to call the tool again with the appropriate flag. This is the designed two-step.
  (The CLI auto-confirms for `cli approve` because the human already expressed intent by
  typing the command. An AI assistant should make the confirmation explicit.)

- **`channel` value:** CLI commands use `channel="dashboard"`. MCP commands must use
  `channel="mcp"` so audit records and intent logs distinguish the source surface.

## Part A — Install the MCP dependency

### A1. `pyproject.toml`

Move `mcp>=1.0` from `[project.optional-dependencies]` into the `[dependency-groups] dev`
group so CI installs it unconditionally:

```toml
[dependency-groups]
dev = [
    ...existing entries...,
    "mcp>=1.0",
]
```

Keep the `[project.optional-dependencies] mcp` stanza for users who install the package
without dev tooling — but add a comment noting the dev group also pins it.

### A2. `mypy.overrides`

Remove `"mcp", "mcp.*"` from the `ignore_missing_imports` override block (they are now
installed). If `mcp` ships typed stubs, mypy will type-check it. If it raises mypy errors,
add a per-file `# type: ignore[import-untyped]` in `mcp_server.py` only — do not suppress
broadly.

### A3. Verify gate is still green

Run `make ci` after A1–A2 before writing any server code. The dependency change is the
riskiest part; confirm no side-effects before proceeding.

## Part B — MCP server

### B1. `surfaces/mcp_server.py` — server definition, ≤ 150L

```python
"""MCP server — exposes trading-agents operator tools over Model Control Protocol.

Agent: surfaces
Role: translate MCP tool calls into bounded bus requests through operator and supervisor.
External I/O: MCP stdio transport; MessageBus calls through the injected surface context.
"""
```

The server exposes **five tools** (derived from the `mcp_tools` contract annotations, ordered
by how an AI assistant would use them):

| Tool name | Maps to | Returns |
| --------- | ------- | ------- |
| `command` | `operator.interpret` → `supervisor.dispatch_intent` | accepted, routed_to, reason |
| `status` | `supervisor.system_status` | healthy, open_incidents, pending_flags, last_run |
| `runs` | `surfaces.queries.runs.recent_runs` (graph read) | list of run summaries |
| `incidents` | `surfaces.queries.faults.open_faults` (graph read) | list of fault views |
| `explain` | `reporter.narrative` | position_id, story summary, evidence_refs |

**Tool schemas** — declare as `list[types.Tool]` constants so `list_tools` is a pure lookup:

```python
TOOLS = [
    types.Tool(
        name="command",
        description=(
            "Send a natural-language command through the operator and supervisor. "
            "If confirmation is required the response says so — call again with "
            "confirmed=true in the text or as a parameter to proceed."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The command in plain language."},
                "confirmed": {
                    "type": "boolean",
                    "description": "Set true to confirm a command that requires confirmation.",
                },
            },
            "required": ["text"],
        },
    ),
    types.Tool(
        name="status",
        description="Return system health: open incidents, pending flags, last run.",
        inputSchema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="runs",
        description="List recent dispatcher runs, newest first.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10, "description": "Max runs to return."},
            },
        },
    ),
    types.Tool(
        name="incidents",
        description="List all open fault incidents.",
        inputSchema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="explain",
        description="Generate or retrieve the trade narrative for a position on demand.",
        inputSchema={
            "type": "object",
            "properties": {
                "position_id": {"type": "string", "description": "The position node key."},
            },
            "required": ["position_id"],
        },
    ),
]
```

**Async entry and dispatch:**

```python
server = Server("trading-agents")
_ctx: SurfaceContext | None = None

def _context() -> SurfaceContext:
    global _ctx
    if _ctx is None:
        _ctx = paper_context()
    return _ctx

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return TOOLS

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    result = await asyncio.to_thread(_dispatch_tool, _context(), name, arguments)
    return [types.TextContent(type="text", text=json.dumps(result, default=str))]

async def _amain() -> None:
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

def main() -> None:
    """Synchronous entry point for `python -m surfaces.mcp_server`."""
    asyncio.run(_amain())
```

### B2. `surfaces/mcp_tools.py` — synchronous tool handlers, ≤ 150L

Extract the synchronous dispatch logic into a companion module so `mcp_server.py` stays
under 150L and the handlers are testable without async:

```python
"""Synchronous MCP tool handler implementations.

Agent: surfaces
Role: implement each MCP tool as a plain function returning a JSON-serialisable dict.
External I/O: MessageBus calls through the injected surface context.
"""

def dispatch_tool(ctx: SurfaceContext, name: str, arguments: dict) -> dict:
    """Route one MCP tool call to the appropriate handler."""
    handlers = {
        "command": _cmd_command,
        "status": _cmd_status,
        "runs": _cmd_runs,
        "incidents": _cmd_incidents,
        "explain": _cmd_explain,
    }
    handler = handlers.get(name)
    if handler is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return handler(ctx, arguments)
    except Exception as exc:
        return {"error": str(exc)}
```

**Individual handlers:**

`_cmd_command(ctx, args) → dict`:
- Build `HumanCommand(text=args["text"], actor="assistant", channel="mcp")`
- Inject `confirmed=true` into parameters if `args.get("confirmed")` is truthy
- Send to `operator.interpret` via bus
- If `result.refused` or no intent, return `{"accepted": False, "reason": result.message}`
- Send intent to `supervisor.dispatch_intent` via bus
- Return `{"accepted": dispatch.accepted, "routed_to": dispatch.routed_to, "reason": dispatch.reason}`

`_cmd_status(ctx, args) → dict`:
- Send `StatusRequest(run_id=None)` to `supervisor.system_status` via bus
- Return `{"healthy": report.healthy, "open_incidents": report.open_incidents, "pending_flags": report.pending_human_flags, "last_run": report.last_successful_run}`

`_cmd_runs(ctx, args) → dict`:
- Call `recent_runs(ctx.graph, limit=args.get("limit", 10))`
- Return `{"runs": [{"run_id": r.run_id, "completed": r.completed, "steps": len(r.steps)} for r in runs]}`

`_cmd_incidents(ctx, args) → dict`:
- Call `open_faults(ctx.graph)`
- Return `{"incidents": [{"fault_id": f.fault_id, "agent": f.source_agent, "capability": f.capability, "severity": f.severity, "message": f.message} for f in faults]}`

`_cmd_explain(ctx, args) → dict`:
- Send `NarrativeRequest(position_id=args["position_id"])` to `reporter.narrative` via bus
- If bus error, return `{"error": f"narrative not available for {position_id}"}`
- Return `{"position_id": narrative.position_id, "summary": narrative.story.summary, "evidence_refs": list(narrative.story.evidence_refs)}`

Use the same `AgentMessage(sender="mcp", recipient=..., ...)` pattern as `cli_commands.py`.
Do not import from `cli_commands.py` — duplicate the bus-call boilerplate (5–8 lines each).

### B3. `surfaces/__main__mcp.py` — entry point, ≤ 10L

```python
"""Entry point: python -m surfaces.mcp_server"""
from surfaces.mcp_server import main

if __name__ == "__main__":
    main()
```

Wait — `surfaces/__main__.py` already exists for `python -m surfaces`. Add an `mcp` submodule
entry instead. Check if `python -m surfaces.mcp_server` already works from `mcp_server.py`'s
`if __name__ == "__main__": main()` block — if so, no separate `__main__mcp.py` is needed.

### B4. `pyproject.toml` — optional script entry

```toml
[project.scripts]
trading-agents-mcp = "surfaces.mcp_server:main"
```

## Part C — Tests

### C1. `surfaces/tests/test_mcp_server.py` — ≤ 120L

Test the synchronous `dispatch_tool` function directly (no async overhead):

```python
from surfaces.mcp_tools import dispatch_tool
from surfaces.context import test_context

def test_command_tool_run_intent(ctx):
    """command tool with 'run' text returns routed_to."""
    result = dispatch_tool(ctx, "command", {"text": "run the daily scan"})
    assert result["accepted"] is True
    assert result["routed_to"] == "orchestration.execute_run"

def test_status_tool(ctx):
    """status tool returns health dict with expected keys."""
    result = dispatch_tool(ctx, "status", {})
    assert "healthy" in result
    assert "open_incidents" in result

def test_runs_tool_empty(ctx):
    """runs tool on empty graph returns empty list."""
    result = dispatch_tool(ctx, "runs", {})
    assert result["runs"] == []

def test_incidents_tool_with_fault(fault_ctx):
    """incidents tool returns seeded fault."""
    result = dispatch_tool(fault_ctx, "incidents", {})
    assert len(result["incidents"]) == 1
    assert result["incidents"][0]["agent"] == "analyst"

def test_explain_tool(position_ctx):
    """explain tool calls reporter.narrative and returns summary."""
    result = dispatch_tool(position_ctx, "explain", {"position_id": <seeded_pos_id>})
    assert "summary" in result
    assert result["summary"]  # non-empty

def test_unknown_tool_returns_error(ctx):
    """Unknown tool name returns error dict, does not raise."""
    result = dispatch_tool(ctx, "nonexistent", {})
    assert "error" in result

def test_tool_list_has_five_tools():
    """TOOLS constant matches the five expected names."""
    from surfaces.mcp_server import TOOLS
    names = {t.name for t in TOOLS}
    assert names == {"command", "status", "runs", "incidents", "explain"}
```

Use the same `test_context()` fixture pattern as `test_p6_exit.py` — no `pytest.mark.asyncio`,
no async fixtures. The entire test file is synchronous.

### C2. Coverage

All new code in `mcp_server.py` and `mcp_tools.py` must be covered. The async `call_tool`
handler and `_amain` are the only lines that require a `# pragma: no cover` exemption (they
need a live MCP client to exercise). Mark them explicitly:

```python
async def _amain() -> None:  # pragma: no cover
    ...

def main() -> None:  # pragma: no cover
    ...
```

## Steps

1. Branch `sprint-22-mcp-tool-binding` off `main`.
2. **Part A**: update `pyproject.toml`, update `mypy.overrides`, `uv sync`. Run `make ci` —
   must be green before any server code is written. This validates the dependency change.
3. **Part B1**: `mcp_server.py` — server definition, TOOLS constant, async dispatch, main.
4. **Part B2**: `mcp_tools.py` — synchronous handlers.
5. **Part B3/B4**: entry point + pyproject script.
6. **Part C**: tests.
7. **Line count check**: `wc -l surfaces/mcp_server.py surfaces/mcp_tools.py`. Both < 200L.
8. `make ci` green. Push; hand back.

## Acceptance criteria

- `uv run python -m surfaces.mcp_server` starts without error (exits immediately on stdin
  close — this is correct MCP stdio behaviour; no real MCP client needed to verify startup).
- `TOOLS` constant has exactly five entries matching the tool names above.
- `dispatch_tool(ctx, "command", {"text": "run the daily scan"})` returns
  `{"accepted": True, "routed_to": "orchestration.execute_run", ...}` with `test_context`.
- `dispatch_tool(ctx, "status", {})` returns a dict with `healthy`, `open_incidents`, and
  `pending_flags` keys.
- All five tool handlers have test coverage.
- `mcp_server.py` < 150L; `mcp_tools.py` < 150L.
- `mypy --strict` passes (no new `# type: ignore` unless unavoidable due to missing stubs).
- Import-linter 4/4 kept (surfaces may import from `mcp`; no new contracts needed).
- `make ci` green at/above coverage floor (100.00).

## Out of scope (do NOT build this sprint)

RAG vector index (P1 remaining); reject/modify/stage intents (P7/P8); MCP resource
endpoints (expose graph nodes as MCP resources — deferred); authentication/authorisation on
the MCP transport (P8 hardening); streaming tool responses; MCP prompt templates.

## Handback report (paste into PR / reply)

- Confirm `mcp>=1.0` is in the dev dependency group and CI installed it.
- Confirm `python -m surfaces.mcp_server` exits cleanly on stdin close (verify manually or
  with a subprocess test).
- Final line counts: `mcp_server.py`, `mcp_tools.py`.
- Whether `mypy --strict` needed any `# type: ignore` for the MCP import — note the reason.
- New coverage % and floor; any design note for Sprint 23 (P7 kickoff).

The planning agent will review, merge to `main`, update docs (close P1), and plan Sprint 23
(P7 researcher agent kickoff).
