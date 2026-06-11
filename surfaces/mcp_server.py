"""MCP server exposing trading-agents operator tools.

Agent: surfaces
Role: translate MCP tool calls into bounded bus requests and graph reads.
External I/O: MCP stdio transport; MessageBus calls through the surface context.
"""

from __future__ import annotations

import asyncio
import json

from mcp import types
from mcp.server import Server

from surfaces.context import SurfaceContext, paper_context
from surfaces.mcp_tools import dispatch_tool as _dispatch_tool

TOOLS: list[types.Tool] = [
    types.Tool(
        name="command",
        description=(
            "Send a natural-language command through the operator and supervisor. "
            "If confirmation is required, call again with confirmed=true."
        ),
        inputSchema={
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
        inputSchema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="runs",
        description="List recent dispatcher runs, newest first.",
        inputSchema={
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
        inputSchema={"type": "object", "properties": {}},
    ),
    types.Tool(
        name="explain",
        description="Generate or retrieve the trade narrative for a position.",
        inputSchema={
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


@server.list_tools()  # type: ignore[no-untyped-call,untyped-decorator]
async def list_tools() -> list[types.Tool]:
    """Return the static tool catalog."""
    return TOOLS


@server.call_tool()  # type: ignore[untyped-decorator]
async def call_tool(
    name: str, arguments: dict[str, object] | None
) -> list[types.TextContent]:  # pragma: no cover
    """Bridge async MCP calls to the synchronous surface dispatch."""
    result = await asyncio.to_thread(_dispatch_tool, _context(), name, arguments or {})
    return [types.TextContent(type="text", text=json.dumps(result, default=str))]


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
