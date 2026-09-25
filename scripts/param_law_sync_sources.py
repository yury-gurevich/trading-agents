"""Source readers for PARAM/settings reconciliation.

Agent: tooling
Role: parse settings fields and law PARAM rows for the sync checker.
External I/O: filesystem reads of settings modules and law markdown files.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

COMPONENT_SETTINGS = {
    "dispatcher": (
        "orchestration/settings.py",
        "orchestration.settings",
        "OrchestratorSettings",
    ),
    "surfaces": (
        "surfaces/dashboard/settings.py",
        "surfaces.dashboard.settings",
        "DashboardSettings",
    ),
}

COMPONENT_LAWS = {
    "dispatcher": "orchestration/laws/dispatcher/laws.md",
    "surfaces": "surfaces/laws/laws.md",
}


@dataclass(frozen=True)
class Location:
    path: Path
    line_number: int


@dataclass(frozen=True)
class ParamRow:
    name: str
    tunable: str
    location: Location


def settings_field_locations(root: Path, agent: str) -> dict[str, Location]:
    found: dict[str, Location] = {}
    class_name = settings_class_name(agent)
    for path in settings_paths(root, agent):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or not node.name.endswith("Settings"):
                continue
            if class_name is not None and node.name != class_name:
                continue
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(
                    item.target, ast.Name
                ):
                    found.setdefault(item.target.id, Location(path, item.lineno))
    return found


def agent_settings_location(root: Path, agent: str) -> Location:
    return Location(settings_module_path(root, agent), 1)


def param_rows(root: Path, agent: str) -> dict[str, ParamRow]:
    path = law_book_path(root, agent)
    lines = path.read_text(encoding="utf-8").splitlines()
    in_param = False
    rows: dict[str, ParamRow] = {}
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped == "## Parameters (`PARAM`)":
            in_param = True
            continue
        if in_param and stripped.startswith("## "):
            break
        if not in_param or not stripped.startswith("|"):
            continue
        cells = split_markdown_row(stripped)
        if len(cells) < 4 or not cells[0].startswith("`"):
            continue
        name = cells[0].strip("`")
        rows[name] = ParamRow(name, cells[3], Location(path, index))
    return rows


def law_book_names(root: Path) -> list[str]:
    agents = [
        path.parents[1].name
        for path in sorted((root / "agents").glob("*/laws/laws.md"))
        if (path.parents[1] / "settings.py").is_file()
    ]
    components = [
        name
        for name in ("dispatcher", "surfaces")
        if law_book_path(root, name).is_file()
        and settings_module_path(root, name).is_file()
    ]
    return [*agents, *components]


def settings_paths(root: Path, agent: str) -> tuple[Path, ...]:
    if agent in COMPONENT_SETTINGS:
        return (settings_module_path(root, agent),)
    return tuple(sorted((root / "agents" / agent).glob("settings*.py")))


def settings_module_path(root: Path, agent: str) -> Path:
    if agent in COMPONENT_SETTINGS:
        return root / COMPONENT_SETTINGS[agent][0]
    return root / "agents" / agent / "settings.py"


def settings_module_name(agent: str) -> str:
    return (
        COMPONENT_SETTINGS[agent][1]
        if agent in COMPONENT_SETTINGS
        else f"agents.{agent}.settings"
    )


def settings_class_name(agent: str) -> str | None:
    return COMPONENT_SETTINGS[agent][2] if agent in COMPONENT_SETTINGS else None


def law_book_path(root: Path, agent: str) -> Path:
    if agent in COMPONENT_LAWS:
        return root / COMPONENT_LAWS[agent]
    return root / "agents" / agent / "laws" / "laws.md"


def split_markdown_row(line: str) -> list[str]:
    body = line.strip().strip("|")
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in body:
        if char == "|" and not escaped:
            cells.append("".join(current).replace("\\|", "|").strip())
            current = []
            continue
        current.append(char)
        escaped = char == "\\" and not escaped
        if char != "\\":
            escaped = False
    cells.append("".join(current).replace("\\|", "|").strip())
    return cells
