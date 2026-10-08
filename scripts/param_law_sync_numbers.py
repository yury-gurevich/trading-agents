"""Compare PARAM defaults and bounds, including exact deferred rows.

Agent: tooling
Role: enforce DL-276 D1-D4 and return located numeric failures and used excuses.
External I/O: none; operates on parsed rows and loaded settings metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.param_law_sync_bounds import bounds_text, code_bounds, law_bounds
from scripts.param_law_sync_excused import EXCUSED_BOUNDS
from scripts.param_law_sync_sources import law_book_path
from scripts.param_law_sync_values import value_problem

if TYPE_CHECKING:
    from pathlib import Path

    from pydantic.fields import FieldInfo
    from scripts.param_law_sync_sources import ParamRow


def check_numbers(
    root: Path, agent: str, rows: dict[str, ParamRow], fields: dict[str, FieldInfo]
) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    used: set[str] = set()
    for name in sorted(rows.keys() & fields.keys()):
        row, info = rows[name], fields[name]
        key = f"{agent}.{name}"
        problem = value_problem(row.value, info.default)
        if problem is not None:
            errors.append(_failure(root, row, key, problem))
        actual = code_bounds(info)
        disagrees = law_bounds(row.type_cell) != actual
        recorded = EXCUSED_BOUNDS.get(key)
        if disagrees:
            if recorded == row.type_cell:
                used.add(key)
            else:
                errors.append(
                    _failure(
                        root,
                        row,
                        key,
                        f"law Type {row.type_cell!r} differs from code bounds "
                        f"{bounds_text(actual)}",
                    )
                )
        if recorded is not None and (not disagrees or recorded != row.type_cell):
            errors.append(
                _failure(
                    root,
                    row,
                    key,
                    f"excused list entry {recorded!r} is no longer valid for law "
                    f"Type {row.type_cell!r} and code bounds {bounds_text(actual)}; "
                    "delete it from EXCUSED_BOUNDS",
                )
            )
    for key in sorted(EXCUSED_BOUNDS):
        owner, name = key.split(".", 1)
        if owner == agent and name not in rows.keys() & fields.keys():
            path = law_book_path(root, agent).relative_to(root).as_posix()
            errors.append(
                f"[FAIL] {path}:1: {key} excused list entry has no matching "
                "PARAM/settings "
                "field; delete it from EXCUSED_BOUNDS"
            )
    return errors, used


def _failure(root: Path, row: ParamRow, key: str, detail: str) -> str:
    path = row.location.path.relative_to(root).as_posix()
    return f"[FAIL] {path}:{row.location.line_number}: {key} {detail}"
