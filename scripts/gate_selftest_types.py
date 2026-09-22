"""Shared types for the gate self-test.

Agent: tooling
Role: name the case and invariant shapes the runner and the tables share.
External I/O: none.

These sit below the case table, the invariant table and the runner, so no module
imports a caller back to name a type (DL-198).
"""

from __future__ import annotations

from dataclasses import dataclass, field

PROBE_PREFIX = "_gate_selftest_probe"


@dataclass(frozen=True)
class FailureCase:
    """A planted violation that a named gate step must reject."""

    name: str
    why: str
    files: dict[str, str]
    command: list[str]
    must_output: tuple[str, ...] = ()


@dataclass(frozen=True)
class Invariant:
    """A config fact whose regression would silently disable a gate."""

    name: str
    why: str
    path: str
    must_contain: tuple[str, ...] = field(default=())
    must_not_contain: tuple[str, ...] = field(default=())
