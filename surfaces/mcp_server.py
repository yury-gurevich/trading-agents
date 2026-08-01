"""MCP server exposing trading-agents operator tools.

Agent: surfaces
Role: translate MCP tool calls into bounded bus requests and graph reads.
External I/O: MCP stdio transport; MessageBus calls through the surface context.
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from mcp import types
from mcp.server import Server

from surfaces.context import SurfaceContext, paper_context
from surfaces.mcp_tools import dispatch_tool as _dispatch_tool

if TYPE_CHECKING:
    from mcp.server.context import ServerRequestContext

TOOLS: list[types.Tool] = [
    types.Tool(
        name="command",
        description=(
            "Send a natural-language command through the operator and supervisor. "
            "If confirmation is required, call again with confirmed=true."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Plain-language command."},
                "confirmed": {
                    "type": "boolean",
                    "description": "Explicit confirmation for gated commands.",
                },
            },
            "required": ["text"],
        },
    ),
    types.Tool(
        name="status",
        description="Return health, open incidents, pending flags, and last run.",
        input_schema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="runs",
        description="List recent dispatcher runs, newest first.",
        input_schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum runs to return.",
                }
            },
        },
    ),
    types.Tool(
        name="incidents",
        description="List all open fault incidents.",
        input_schema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="explain",
        description="Generate or retrieve the trade narrative for a position.",
        input_schema={
            "type": "object",
            "properties": {
                "position_id": {
                    "type": "string",
                    "description": "Position node key.",
                }
            },
            "required": ["position_id"],
        },
    ),
]

server = Server("trading-agents")
_ctx: SurfaceContext | None = None


def _context() -> SurfaceContext:  # pragma: no cover
    global _ctx
    if _ctx is None:
        _ctx = paper_context()
    return _ctx


async def list_tools(
    _ctx: ServerRequestContext[object, object] | None = None,
    _params: types.PaginatedRequestParams | None = None,
) -> types.ListToolsResult:
    """Return the static tool catalog."""
    return types.ListToolsResult(tools=TOOLS)


async def call_tool(
    _ctx: ServerRequestContext[object, object],
    params: types.CallToolRequestParams,
) -> types.CallToolResult:  # pragma: no cover
    """Bridge async MCP calls to the synchronous surface dispatch."""
    result = await asyncio.to_thread(
        _dispatch_tool, _context(), params.name, params.arguments or {}
    )
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps(result, default=str))]
    )


server.add_request_handler("tools/list", types.PaginatedRequestParams, list_tools)
server.add_request_handler("tools/call", types.CallToolRequestParams, call_tool)


async def _amain() -> None:  # pragma: no cover
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:  # pragma: no cover
    """Run the MCP stdio server."""
    asyncio.run(_amain())


if __name__ == "__main__":  # pragma: no cover
    main()
