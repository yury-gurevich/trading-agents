"""Scanner boundary tests.

Agent: scanner
Role: assert scanner does not import provider implementation code.
External I/O: filesystem reads via import graph inspection.
"""

from __future__ import annotations

from pathlib import Path


def test_scanner_does_not_import_provider_agent_code() -> None:
    scanner_root = Path(__file__).parents[1]

    imported_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in scanner_root.rglob("*.py")
        if "tests" not in path.parts
    )

    assert "agents.provider" not in imported_text
