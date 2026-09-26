"""Load the served-agent roster from pack data, by path.

Agent: tooling
Role: read `orchestration/packs/trading_served_agents.json` by path — never by
      import — so `sb_sas_plan.py`, `servicebus_prepare_routes.py` and their
      test get the served roster as pack data instead of a kernel constant
      (ADR-0012, DL-12). Mirrors `agents/master/grants.py`'s parse/load split.
External I/O: reads the roster JSON file when `load_served_agent_roster` runs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_ROSTER_PATH = _ROOT / "orchestration" / "packs" / "trading_served_agents.json"


@dataclass(frozen=True)
class ServedAgentRoster:
    """The served-type roster a pack supplies: names, roles and image directories."""

    served_agent_types: tuple[str, ...]
    deliberator_peer_agent_types: tuple[str, ...]
    deliberator_manager_type: str
    deliberator_reply_agent_types: tuple[str, ...]
    image_dir_by_agent_type: dict[str, str]


def parse_served_agent_roster(text: str) -> ServedAgentRoster:
    """Parse a served-agent roster from a JSON string."""
    raw: dict[str, Any] = json.loads(text)
    return ServedAgentRoster(
        served_agent_types=tuple(raw["served_agent_types"]),
        deliberator_peer_agent_types=tuple(raw["deliberator_peer_agent_types"]),
        deliberator_manager_type=str(raw["deliberator_manager_type"]),
        deliberator_reply_agent_types=tuple(raw["deliberator_reply_agent_types"]),
        image_dir_by_agent_type=dict(raw["image_dir_by_agent_type"]),
    )


def load_served_agent_roster(
    path: str | Path = _DEFAULT_ROSTER_PATH,
) -> ServedAgentRoster:
    """Load the served-agent roster from a JSON file at *path*."""
    return parse_served_agent_roster(Path(path).read_text(encoding="utf-8"))


_ROSTER = load_served_agent_roster()

SERVED_AGENT_TYPES = _ROSTER.served_agent_types
DELIBERATOR_PEER_AGENT_TYPES = _ROSTER.deliberator_peer_agent_types
DELIBERATOR_MANAGER_TYPE = _ROSTER.deliberator_manager_type
DELIBERATOR_REPLY_AGENT_TYPES = _ROSTER.deliberator_reply_agent_types


def image_dir_for_served_agent(agent_type: str) -> str:
    """Return the source image directory for one served agent type."""
    return _ROSTER.image_dir_by_agent_type[agent_type]
