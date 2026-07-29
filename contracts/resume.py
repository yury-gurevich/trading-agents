"""Typed resume-from-stage boundary between supervisor and orchestration.

Agent: contracts
Role: declare the immutable request and placement result shapes.
External I/O: none.
"""

from __future__ import annotations

from typing import Literal

from contracts.common import _Frozen

ResumeStage = Literal[
    "position_sync",
    "provider",
    "scanner",
    "analyst",
    "pm",
    "execution",
    "monitor",
    "reporter",
]
RESUME_STAGES: tuple[ResumeStage, ...] = (
    "position_sync",
    "provider",
    "scanner",
    "analyst",
    "pm",
    "execution",
    "monitor",
    "reporter",
)
BROKER_RESUME_STAGES = frozenset(
    {"position_sync", "provider", "scanner", "analyst", "pm", "execution"}
)
BROKER_RESUME_CONSEQUENCE = (
    "re-running from this stage can submit new orders at the broker"
)


class ResumeRequest(_Frozen):
    """One supervisor-validated resume placement request."""

    source_run_id: str
    resume_from: ResumeStage


class ResumePlacement(_Frozen):
    """The child run and linked upstream evidence written by orchestration."""

    child_run_id: str
    node_key: str
    resume_from: ResumeStage
    linked: tuple[str, ...]
    created: bool
