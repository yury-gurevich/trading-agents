"""Core PARAM/settings reconciliation helpers.

Agent: tooling
Role: compare agent law PARAM rows with the corresponding settings model fields.
External I/O: filesystem reads and Python imports of settings modules.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.param_law_sync_baseline import (
    LEGACY_BASELINE,
    MISSING_PARAM,
    MISSING_SETTING,
    TUNABLE_MISMATCH,
    IssueKey,
)
from scripts.param_law_sync_sources import (
    Location,
    ParamRow,
    agent_settings_location,
    param_rows,
    settings_field_locations,
)

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kernel import AgentSettings  # noqa: E402

if TYPE_CHECKING:
    from types import ModuleType

    from pydantic.fields import FieldInfo


@dataclass(frozen=True)
class ParamIssue:
    agent: str
    name: str
    kind: str
    location: Location
    detail: str

    @property
    def key(self) -> IssueKey:
        return (self.agent, self.kind, self.name)


@dataclass
class ParamSyncReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def check_root(root: Path) -> ParamSyncReport:
    resolved = root.resolve()
    baseline: frozenset[IssueKey] = (
        LEGACY_BASELINE if resolved == _ROOT.resolve() else frozenset()
    )
    report = ParamSyncReport()
    for agent in _discover_agents(root):
        for issue in _agent_issues(root, agent):
            message = _format_issue(root, issue)
            if issue.key in baseline:
                report.warnings.append(message.replace("[FAIL]", "[WARN]", 1))
            else:
                report.errors.append(message)
    return report


def _discover_agents(root: Path) -> list[str]:
    agents_root = root / "agents"
    return [
        path.parents[1].name
        for path in sorted(agents_root.glob("*/laws/laws.md"))
        if (path.parents[1] / "settings.py").is_file()
    ]


def _agent_issues(root: Path, agent: str) -> list[ParamIssue]:
    settings_cls = _settings_class(root, agent)
    fields = settings_cls.model_fields
    params = param_rows(root, agent)
    settings_locations = settings_field_locations(root, agent)
    issues: list[ParamIssue] = []

    for name in sorted(set(fields) - set(params)):
        issues.append(
            ParamIssue(
                agent,
                name,
                MISSING_PARAM,
                settings_locations.get(name, agent_settings_location(root, agent)),
                f"{agent}.{name} {MISSING_PARAM}",
            )
        )
    for name in sorted(set(params) - set(fields)):
        row = params[name]
        issues.append(
            ParamIssue(
                agent,
                name,
                MISSING_SETTING,
                row.location,
                f"{agent}.{name} {MISSING_SETTING}",
            )
        )
    for name in sorted(set(params) & set(fields)):
        issue = _tunable_family_issue(agent, params[name], fields[name])
        if issue is not None:
            issues.append(issue)
    return issues


def _settings_class(root: Path, agent: str) -> type[AgentSettings]:
    module = _load_settings_module(root, agent)
    candidates = [
        item
        for item in module.__dict__.values()
        if isinstance(item, type)
        and issubclass(item, AgentSettings)
        and item is not AgentSettings
        and item.__name__.endswith("Settings")
        and item.__module__ == module.__name__
        and not item.__name__.startswith("_")
    ]
    if len(candidates) != 1:
        names = ", ".join(item.__name__ for item in candidates) or "<none>"
        raise RuntimeError(
            f"{agent}: expected one public settings class, found {names}"
        )
    return candidates[0]


def _load_settings_module(root: Path, agent: str) -> ModuleType:
    if root.resolve() == _ROOT.resolve():
        return importlib.import_module(f"agents.{agent}.settings")
    path = root / "agents" / agent / "settings.py"
    spec = importlib.util.spec_from_file_location(f"_param_law_sync_{agent}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"{agent}: cannot load settings module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tunable_family_issue(
    agent: str,
    row: ParamRow,
    info: FieldInfo,
) -> ParamIssue | None:
    expected = _expected_tunable(row.tunable)
    if expected is None:
        return None
    actual = bool(info.description)
    if actual == expected:
        return None
    expected_text = (
        "registered via tunable()" if expected else "not registered via tunable()"
    )
    return ParamIssue(
        agent,
        row.name,
        TUNABLE_MISMATCH,
        row.location,
        (
            f"{agent}.{row.name} law declares {row.tunable}; settings field is "
            f"{'registered' if actual else 'not registered'} via tunable(), "
            f"expected {expected_text}"
        ),
    )


def _expected_tunable(tunable_cell: str) -> bool | None:
    cell = tunable_cell.upper().strip()
    if cell == "YES":
        return True
    if cell.startswith("NO"):
        return False
    return None


def _format_issue(root: Path, issue: ParamIssue) -> str:
    return (
        f"[FAIL] {_display_path(root, issue.location.path)}:"
        f"{issue.location.line_number}: {issue.detail}"
    )


def _display_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
