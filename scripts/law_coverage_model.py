"""Data model for the law-coverage checker.

Agent: tooling
Role: share parsed law-book records between the checker modules.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class Citation:
    """A test citation from a law test-plan row."""

    raw: str
    test_name: str
    file_part: str | None = None


@dataclass(frozen=True)
class TestPlanRow:
    """One parsed row from an agent's law test plan."""

    agent: str
    path: Path
    line_number: int
    clause_id: str
    test_text: str
    green: bool


@dataclass(frozen=True)
class AgentBook:
    """The parsed laws and test-plan rows for one agent."""

    agent: str
    laws_path: Path
    plan_path: Path
    law_ids: frozenset[str]
    rows: tuple[TestPlanRow, ...]


@dataclass(frozen=True)
class RollupClaim:
    """A green/total claim read from a roll-up document."""

    path: Path
    line_number: int
    green: int
    total: int


@dataclass(frozen=True)
class TestTarget:
    """A test function resolved from the live test tree."""

    path: Path
    name: str
    docstring: str


@dataclass(frozen=True)
class Resolution:
    """The result of resolving one cited test name."""

    citation: Citation
    targets: tuple[TestTarget, ...] = ()
    missing: str | None = None
    ambiguous: tuple[Path, ...] = ()
