"""Shared remediation record types.

Agent: master
Role: dataclass records shared by remediation execution and the graph store,
      kept import-cycle-free (imports nothing from either side).
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RemediationAttempt:
    """One execution attempt for a planned remediation."""

    remediation: str
    status: str
    message: str
    executor: str
    auto: bool
