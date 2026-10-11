"""Plant isolated charters with distracting tables and tracker bytes.

Agent: tests
Role: supply Sprint 261's charter fixtures without growing its test module.
External I/O: writes only to the test's temporary directory.
"""

from __future__ import annotations

import importlib

import pytest

CHARTER = "ops/departments/housekeeping/charter.md"
BAD_ROWS = (
    "| `docs/bad.md` | 40 kB |",
    "| `docs/bad.md` | 0.5 MB |",
    "| `docs/bad.md` | about 40 KB |",
    "| `docs/bad.md` | 0 KB |",
    "| `docs/bad.md` | |",
    "| docs/bad.md | 1 KB |",
    "| `docs/bad.md` `docs/second.md` | 1 KB |",
    "| `docs/bad.md` |",
)


def load_checker():
    try:
        return importlib.import_module("scripts.check_tracker_size")
    except ModuleNotFoundError as exc:
        pytest.fail(f"tracker size checker is missing: {exc}")


def charter(rows="| `docs/a.md` | 2 KB |"):
    return (
        "# Planted charter\n\n"
        "## Before\n\n"
        "| Tracker | Limit |\n| --- | --- |\n| `docs/before.md` | 99 KB |\n\n"
        "## OPS-TRIM · Planted limits\n\n"
        "| Tracker | Limit |\n| --- | --- |\n"
        f"{rows}\n\n"
        "### Another table\n\n"
        "| Topic | Note |\n| --- | --- |\n| other | unreadable as a limit |\n\n"
        "## After\n\n"
        "| Tracker | Limit |\n| --- | --- |\n| `docs/after.md` | 99 KB |\n"
    )


def plant(root, rows="| `docs/a.md` | 2 KB |", files=None, *, text=None):
    target = root / CHARTER
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        charter(rows) if text is None else text, encoding="utf-8", newline="\n"
    )
    for name, content in (files or {}).items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def broken_tables():
    return (
        (charter().replace("## OPS-TRIM", "## Moved"), "section, found 0"),
        (charter().replace("| Tracker | Limit |", "| Name | Size |"), "table, found 0"),
        (
            charter().replace("| Topic | Note |", "| Tracker | Limit |"),
            "table, found 2",
        ),
        (charter(""), "has no rows"),
        (charter("| `docs/a.md` | 2 KB |\n| `docs/a.md` | 1 KB |"), "is listed twice"),
    )
