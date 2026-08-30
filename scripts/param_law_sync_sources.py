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


@dataclass(frozen=True)
class Location:
    path: Path
    line_number: int


@dataclass(frozen=True)
class ParamRow:
    agent: str
    name: str
    tunable: str
    location: Location


def settings_field_locations(root: Path, agent: str) -> dict[str, Location]:
    found: dict[str, Location] = {}
    for path in sorted((root / "agents" / agent).glob("settings*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or not node.name.endswith("Settings"):
                continue
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(
                    item.target, ast.Name
                ):
                    found.setdefault(item.target.id, Location(path, item.lineno))
    return found


def agent_settings_location(root: Path, agent: str) -> Location:
    return Location(root / "agents" / agent / "settings.py", 1)


def param_rows(root: Path, agent: str) -> dict[str, ParamRow]:
    path = root / "agents" / agent / "laws" / "laws.md"
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
        rows[name] = ParamRow(agent, name, cells[3], Location(path, index))
    return rows


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
