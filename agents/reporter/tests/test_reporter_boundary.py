"""Reporter boundary tests.

Agent: reporter
Role: assert reporter production code imports no other agent implementation.
External I/O: filesystem reads for import-boundary inspection.
"""

from __future__ import annotations

from pathlib import Path

from contracts import AGENT_MODULES


def test_reporter_does_not_import_other_agent_code() -> None:
    """RPT-NEV-02: reporter production code imports no other agent implementation."""
    root = Path("agents/reporter")
    production = [path for path in root.rglob("*.py") if "tests" not in path.parts]
    imported_text = "\n".join(path.read_text(encoding="utf-8") for path in production)
    forbidden = [f"agents.{name}" for name in AGENT_MODULES if name != "reporter"]
    assert not [name for name in forbidden if name in imported_text]
