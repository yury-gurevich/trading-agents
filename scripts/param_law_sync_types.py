"""Shared PARAM reconciliation report types.

Agent: tooling
Role: hold issues and reports without coupling independent comparison modules.
External I/O: none.
"""

from dataclasses import dataclass, field

from scripts.param_law_sync_sources import Location

MISSING_PARAM = "settings field has no PARAM row"
MISSING_SETTING = "PARAM row has no settings field"
TUNABLE_MISMATCH = "Tunable column disagrees with settings metadata"


@dataclass(frozen=True)
class ParamIssue:
    agent: str
    name: str
    kind: str
    location: Location
    detail: str


@dataclass
class ParamSyncReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors
