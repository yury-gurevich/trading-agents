"""Human-review render helpers.

Agent: surfaces
Role: render approval command output.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.supervisor import DispatchResult


def render_approve(result: DispatchResult, subject: str) -> str:
    """Render a single approve command result."""
    if not result.accepted:
        lines = [f"approve refused: {subject}"]
        if result.rejection:
            lines.append(f"  reason: {result.rejection}")
        return "\n".join(lines)
    lines = [f"approved: {subject}"]
    if result.routed_to:
        lines.append(f"  routed_to: {result.routed_to}")
    return "\n".join(lines)
