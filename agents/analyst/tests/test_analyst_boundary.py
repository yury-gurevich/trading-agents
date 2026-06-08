"""Analyst implementation boundary tests.

Agent: analyst
Role: assert analyst production code does not import other agent implementations.
External I/O: none.
"""

from __future__ import annotations

from pathlib import Path


def test_analyst_does_not_import_other_agent_code() -> None:
    analyst_root = Path(__file__).parents[1]
    production = [
        path for path in analyst_root.rglob("*.py") if "tests" not in path.parts
    ]
    imported_text = "\n".join(path.read_text(encoding="utf-8") for path in production)

    assert "agents.provider" not in imported_text
    assert "agents.scanner" not in imported_text
    assert "agents.portfolio_manager" not in imported_text
