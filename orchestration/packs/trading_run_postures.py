"""Trading-pack declarations for run postures.

Agent: orchestration
Role: load baked trading posture data without hard-coding trading agent names.
External I/O: reads the packaged JSON resource.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import cast


def degradable_agent_types() -> frozenset[str]:
    """Return agent types the trading pack permits a degraded run to omit."""
    raw = resources.files(__package__).joinpath("trading_run_postures.json").read_text()
    data = json.loads(raw)
    postures = cast("dict[str, object]", data.get("postures", {}))
    degraded = cast("dict[str, object]", postures.get("degraded", {}))
    rows = degraded.get("degradable_agents", ())
    if not isinstance(rows, list):
        return frozenset()
    return frozenset(
        str(row["agent_type"])
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("agent_type"), str)
    )
