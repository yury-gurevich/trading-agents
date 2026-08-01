"""Deliberator package import-boundary tests.

Agent: deliberator
Role: prove the deliberator bundle stays inside its agent boundary.
External I/O: reads local source files.
"""

from __future__ import annotations

from pathlib import Path


def test_deliberator_package_imports_no_orchestration_or_other_agent() -> None:
    """ADR-0012: deliberator remains inside its agent boundary."""
    root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("from orchestration", "import orchestration")):
                offenders.append(f"{path.name}: {stripped}")
            if stripped.startswith("from agents.") and not stripped.startswith(
                "from agents.deliberator"
            ):
                offenders.append(f"{path.name}: {stripped}")
    assert offenders == []
