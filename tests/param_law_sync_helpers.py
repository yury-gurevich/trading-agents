"""Small synthetic books for DL-276 numeric reconciliation proofs.

Agent: tooling
Role: provide isolated settings and PARAM fixtures for the checker tests.
External I/O: temporary filesystem writes only.
"""

from pathlib import Path


def write_book(
    root: Path,
    *,
    default: str = "5",
    value: str = "`5`",
    annotation: str = "int",
    bounds: str = "",
    type_cell: str = "`int`",
    agent: str = "probe",
) -> Path:
    """Write one settings field; never instantiate settings or read an env file."""
    package = root / "agents" / agent
    laws = package / "laws"
    laws.mkdir(parents=True, exist_ok=True)
    declaration = (
        f"Field(default={default}, description='Synthetic rail.'{bounds})"
        if ", lt=" in bounds
        else f"tunable({default}, why='Synthetic rail.'{bounds})"
    )
    (package / "settings.py").write_text(
        "from datetime import date\nfrom decimal import Decimal\n"
        "from typing import Literal\nfrom pydantic import Field\n"
        "from kernel import AgentSettings, tunable\n\n"
        "class ProbeSettings(AgentSettings):\n"
        f"    limit: {annotation} = {declaration}\n",
        encoding="utf-8",
        newline="\n",
    )
    path = laws / "laws.md"
    path.write_text(
        "# Probe laws\n\n## Parameters (`PARAM`)\n\n"
        "| Name | Value | Type | Tunable | Rationale |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"| `limit` | {value} | {type_cell} | YES | Synthetic rail. |\n\n"
        "## Changelog\n",
        encoding="utf-8",
        newline="\n",
    )
    return path
