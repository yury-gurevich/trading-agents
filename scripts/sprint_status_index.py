"""Read the sprint README's status column so it can be reconciled with each spec.

Agent: tooling
Role: map each sprint document to the status cell of its README row.
External I/O: reads docs/sprints/README.md.

Work-queue item 22 Part B. The README's last column and each spec's `**Status:**`
line were two hand-kept records of one fact, and both drifted: S205, S207 and S223
were merged while their rows still read `SPEC`, and 69 merged specs still
declared `SPEC` themselves. Neither is the source of truth; the
gate requires them to agree, so a status change has to be made in both places.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

_ROW: Final = re.compile(r"^\|\s*\[[^\]]*\]\((?P<target>[^)#]+\.md)\)")
# A cell boundary is a pipe that Markdown has not been told to escape.
_CELL_BOUNDARY: Final = re.compile(r"(?<!\\)\|")
_LEADING_TOKEN: Final = re.compile(r"\**(?P<token>[A-Za-z]+)")


def readme_cells(readme: Path) -> dict[str, str]:
    """Status cell (the row's last cell) for each document the README links."""
    cells: dict[str, str] = {}
    for line in readme.read_text(encoding="utf-8").splitlines():
        match = _ROW.match(line)
        if match is None:
            continue
        parts = _CELL_BOUNDARY.split(line.rstrip())
        cells[match.group("target")] = parts[-2].strip()
    return cells


def leading_token(cell: str) -> str | None:
    """The first word of a status cell, ignoring its bold markers."""
    match = _LEADING_TOKEN.match(cell)
    return match.group("token") if match else None
