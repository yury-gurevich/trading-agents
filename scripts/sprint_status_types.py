"""The vocabulary and record types shared by the sprint-status checker.

Agent: tooling
Role: hold the status types both the classifier and its renderer depend on.
External I/O: none.

This module exists to break a cycle, not to organise code for its own sake.
Splitting rendering out of `check_sprint_status.py` (to honour the 200-line
block, which `make ci` cannot enforce under `scripts/` — work-queue item 78)
left the renderer importing its types back from the checker while the checker
imported the renderer. CodeQL raised five **error-level** `py/unsafe-cyclic-import`
alerts and the Security Findings gate failed `main`, correctly. A `TYPE_CHECKING`
guard does not make a cycle safe; it only hides it from the interpreter.

Types live here, below both, so neither has to import the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pathlib import Path

CanonicalStatus = Literal["SPEC", "BUILT", "MERGED"]
Status = Literal["SPEC", "BUILT", "MERGED", "UNMAPPED", "MISSING"]


@dataclass(frozen=True)
class Classification:
    """One status line resolved to a token, with its evidence kept verbatim."""

    status: Status
    evidence: str


@dataclass(frozen=True)
class DocumentStatus:
    """One sprint document's declared status, and the line it was read from."""

    path: Path
    status: Status
    line: str | None
    evidence: str


@dataclass(frozen=True)
class StatusReport:
    """Every document scanned under one root."""

    root: Path
    entries: tuple[DocumentStatus, ...]

    def count(self, status: Status) -> int:
        """How many documents carry this status."""
        return sum(entry.status == status for entry in self.entries)


@dataclass(frozen=True)
class GateResult:
    """A scan plus whatever it refuses to let pass."""

    report: StatusReport
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """True when every document declares a status its README row agrees with."""
        return not self.errors
