"""Shared RunRequest posture vocabulary.

Agent: contracts
Role: name the run posture values read by orchestration and execution.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping

RunPosture = Literal["normal", "degraded"]

RUN_POSTURE_NORMAL: Final[RunPosture] = "normal"
RUN_POSTURE_DEGRADED: Final[RunPosture] = "degraded"


def run_posture(props: Mapping[str, object] | None) -> RunPosture:
    """Read a RunRequest posture, treating legacy absent values as normal."""
    if props is not None and props.get("run_posture") == RUN_POSTURE_DEGRADED:
        return RUN_POSTURE_DEGRADED
    return RUN_POSTURE_NORMAL
