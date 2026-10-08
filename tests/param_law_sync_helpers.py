"""Small synthetic books for DL-276 numeric reconciliation proofs.

Agent: tooling
Role: provide isolated settings and PARAM fixtures with literal law expectations.
External I/O: temporary filesystem writes only.
"""

from pathlib import Path

EXCUSED_ROWS = {
    "portfolio_manager.starting_cash": "`Decimal ≥ 0` (USD)",
    "portfolio_manager.max_position_pct": "`float ≥ 0.01, ≤ 1.0`",
    "portfolio_manager.max_positions": "`int ≥ 1, ≤ 50`",
    "portfolio_manager.cash_buffer_pct": "`float ≥ 0.0, ≤ 0.50`",
    "portfolio_manager.min_order_quantity": "`int ≥ 1` (shares)",
    "portfolio_manager.price_lookback_days": "`int ≥ 1, ≤ 30` (days)",
    "scanner.min_average_volume": "`float ≥ 0` (shares/day)",
    "analyst.scaled_stop_atr_multiplier": "`float` (ratio)",
}


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
