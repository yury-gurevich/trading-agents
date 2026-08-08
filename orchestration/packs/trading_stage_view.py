"""Shared reached-StageView builder for trading-pack stage extractors.

Agent: orchestration
Role: build a reached StageView, so stage-view modules can be split by pipeline
      position without one importing another for this helper.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.observatory import StageView

if TYPE_CHECKING:
    from orchestration.observatory import Check


def view(
    name: str,
    trigger: str,
    observed: dict[str, object],
    checks: tuple[Check, ...],
    outputs: tuple[str, ...],
) -> StageView:
    """Build a reached StageView."""
    return StageView(
        name, trigger, observed, reached=True, checks=checks, outputs=outputs
    )
