"""Test-lane environment — the lane's process holds only the lane's endpoints.

Agent: orchestration
Role: rewrite the process environment for a test-lane run (DL-328): drop every name
      the env file declares and every fleet endpoint name, carry only the data-feed
      keys, point the graph at the lane DSN and the broker and market data at the
      test paper account, apply the tunables pack as a full ``up`` does, then refuse
      when any fleet secret's value is still present.
External I/O: reads the tunables pack, the vocabulary and issuer-map paths it names.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from agents.portfolio_manager.issuer_map import ISSUER_MAP_PATH_ENV
from kernel.graph_env import GRAPH_VOCABULARY_PATH_ENV
from orchestration.lane_guard import (
    FLEET_SECRET_NAMES,
    PAPER_BASE_URL,
    LaneRefusedError,
    fleet_values,
    lane_values,
    refuse_unsafe_start,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping
    from datetime import datetime

    from orchestration.lane_guard import LaneValues

PACKS = Path(__file__).resolve().parent / "packs"
TUNABLES_PATH = PACKS / "trading_tunables.json"
VOCABULARY_PATH = PACKS / "trading_graph_vocabulary.json"
ISSUER_MAP_PATH = PACKS / "trading_issuer_map.json"

FEED_NAMES = (
    "PROVIDER_FINNHUB_API_KEY",
    "PROVIDER_FMP_API_KEY",
    "PROVIDER_ALPHAVANTAGE_API_KEY",
    "PROVIDER_TIINGO_API_KEY",
    "PROVIDER_FRED_API_KEY",
)
"""The only env-file values a lane run carries: read-only data feeds."""

DROPPED_NAMES = (
    *FLEET_SECRET_NAMES,
    "ALPACA_BASE_URL",
    "EXECUTION_ALPACA_BASE_URL",
    "AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON",
    "AZURE_SERVICEBUS_NAMESPACE_ENDPOINT",
    "MASTER_URL",
    "GRAPH_VOCABULARY_B64",
    "PORTFOLIO_MANAGER_ISSUER_MAP_B64",
)
"""Fleet endpoint names dropped even when the shell, not the env file, set them."""

PEER_APPS = ("deliberator-proponent", "deliberator-opponent")
"""Not applied: the peers differ from the manager only in a Service Bus wait."""


def load_tunables_pack(path: Path = TUNABLES_PATH) -> Mapping[str, object]:
    """Read the tunables pack a full ``up`` injects."""
    data: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("tunables pack must be a JSON object")
    return data


def pack_tunables(pack: Mapping[str, object]) -> dict[str, str]:
    """Return the pack's per-app values as one environment, the peers left out."""
    apps = pack.get("apps")
    if not isinstance(apps, dict):
        raise ValueError("tunables pack has no apps object")
    merged: dict[str, str] = {}
    for app, values in apps.items():
        if app in PEER_APPS or not isinstance(values, dict):
            continue
        for name, value in values.items():
            if merged.get(name, str(value)) != str(value):
                raise ValueError(f"tunables pack sets {name} twice, differently")
            merged[name] = str(value)
    return merged


def lane_environment(
    environ: MutableMapping[str, str],
    dotenv: Mapping[str, str | None],
    lane: LaneValues,
    *,
    pack: Mapping[str, object],
) -> None:
    """Rewrite *environ* so a run built from it reaches only the lane."""
    for name in {*dotenv, *DROPPED_NAMES}:
        environ.pop(name, None)
    for name in FEED_NAMES:
        value = (dotenv.get(name) or "").strip()
        if value:
            environ[name] = value
    environ.update(pack_tunables(pack))
    environ.update(
        {
            "POSTGRES_DSN": lane.dsn,
            "EXECUTION_ALPACA_API_KEY": lane.key,
            "EXECUTION_ALPACA_SECRET_KEY": lane.secret,
            "EXECUTION_ALPACA_BASE_URL": PAPER_BASE_URL,
            "PROVIDER_ALPACA_API_KEY": lane.key,
            "PROVIDER_ALPACA_API_SECRET": lane.secret,
            GRAPH_VOCABULARY_PATH_ENV: str(VOCABULARY_PATH),
            ISSUER_MAP_PATH_ENV: str(ISSUER_MAP_PATH),
        }
    )


def isolate_lane(
    environ: MutableMapping[str, str],
    dotenv: Mapping[str, str | None],
    *,
    now: datetime,
    pack: Mapping[str, object],
) -> LaneValues:
    """Refuse an unsafe start, else rewrite *environ* for the lane and prove it."""
    lane = lane_values(dotenv)
    fleet = fleet_values(environ, dotenv)
    refuse_unsafe_start(lane, fleet, now=now)
    lane_environment(environ, dotenv, lane, pack=pack)
    refuse_leaks(environ, fleet)
    return lane


def refuse_leaks(environ: Mapping[str, str], fleet: Mapping[str, str]) -> None:
    """Raise LaneRefusedError when any fleet secret's value is still present."""
    present = set(environ.values())
    leaked = sorted(name for name, value in fleet.items() if value in present)
    if leaked:
        raise LaneRefusedError(
            f"fleet values still in the lane's environment: {', '.join(leaked)}"
        )
