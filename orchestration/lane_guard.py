"""Test-lane refusals — what must hold before a run may start on the test account.

Agent: orchestration
Role: refuse a test-lane start that could reach the fleet's broker account, graph or
      data budget (work-queue 136 option A, DL-307, DL-328): a missing lane value, a
      test key equal to a fleet key, an endpoint other than Alpaca's paper host, a lane
      graph on the live Neon endpoint, or a start inside the fleet's nightly window.
External I/O: none (reads the mappings and the clock it is handed).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, time
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime

LANE_KEY = "ALPACA_TEST_API_KEY"
LANE_SECRET = "ALPACA_TEST_API_SECRET"  # noqa: S105  # pragma: allowlist secret
LANE_ENDPOINT = "ALPACA_TEST_ENDPOINT"
LANE_DSN = "LANE_POSTGRES_DSN"
PAPER_HOST = "paper-api.alpaca.markets"
PAPER_BASE_URL = f"https://{PAPER_HOST}"

FLEET_KEY_NAMES = (
    "ALPACA_API_KEY",
    "ALPACA_PAPER_API_KEY",
    "EXECUTION_ALPACA_API_KEY",
    "PROVIDER_ALPACA_API_KEY",
)
"""Every name a fleet Alpaca key id is read from: execution's and provider's."""

FLEET_SECRET_NAMES = (
    *FLEET_KEY_NAMES,
    "ALPACA_API_SECRET",
    "ALPACA_PAPER_API_SECRET",
    "EXECUTION_ALPACA_SECRET_KEY",
    "PROVIDER_ALPACA_API_SECRET",
    "POSTGRES_DSN",
    "SERVICEBUS_CONNECTION_STRING",
    "AZURE_SERVICEBUS_CONNECTION_STRING",
    "TELEGRAM_BOT_TOKEN",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
)
"""Names whose values reach the fleet's account, graph, bus, phone or LLM balance."""

FLEET_WINDOW_UTC = (time(22, 0), time(23, 59, 59))
"""The fleet's nightly window, the master's wake (22:00) to midnight (DL-294).

The lane shares the data vendors' per-key budgets (Finnhub, FMP, Alpha Vantage)
with the fleet, so a lane run inside the window could degrade the fleet's run.
"""


class LaneRefusedError(RuntimeError):
    """A test-lane start was refused; the message names the condition."""


@dataclass(frozen=True)
class LaneValues:
    """The four values a lane run is built from, read from the env file."""

    key: str
    secret: str
    endpoint: str
    dsn: str


def lane_values(dotenv: Mapping[str, str | None]) -> LaneValues:
    """Return the lane's four values; refuse when any is missing or blank."""
    names = (LANE_KEY, LANE_SECRET, LANE_ENDPOINT, LANE_DSN)
    missing = [name for name in names if not (dotenv.get(name) or "").strip()]
    if missing:
        raise LaneRefusedError(f"missing lane values: {', '.join(missing)}")
    key, secret, endpoint, dsn = (str(dotenv[name]).strip() for name in names)
    return LaneValues(key=key, secret=secret, endpoint=endpoint, dsn=dsn)


def fleet_values(
    environ: Mapping[str, str], dotenv: Mapping[str, str | None]
) -> dict[str, str]:
    """Return each fleet secret's value from the env file, else the environment."""
    values: dict[str, str] = {}
    for name in FLEET_SECRET_NAMES:
        value = (dotenv.get(name) or environ.get(name) or "").strip()
        if value:
            values[name] = value
    return values


def refuse_unsafe_start(
    lane: LaneValues, fleet: Mapping[str, str], *, now: datetime
) -> None:
    """Raise LaneRefusedError unless every start condition holds."""
    _refuse_window(now)
    _refuse_fleet_keys(lane, fleet)
    if urlsplit(lane.endpoint).hostname != PAPER_HOST:
        raise LaneRefusedError(
            f"{LANE_ENDPOINT} must be Alpaca's paper host {PAPER_HOST}"
        )
    _refuse_fleet_graph(lane.dsn, fleet.get("POSTGRES_DSN", ""))


def neon_endpoint_id(dsn: str) -> str:
    """Return the DSN's endpoint id: the host's first label without ``-pooler``.

    Neon serves one compute endpoint under two host names, direct and pooled
    (``ep-x`` and ``ep-x-pooler``); both reach the same database.
    """
    host = (urlsplit(dsn).hostname or "").lower()
    first = host.split(".", 1)[0]
    return first.removesuffix("-pooler")


def _refuse_window(now: datetime) -> None:
    start, end = FLEET_WINDOW_UTC
    clock = now.astimezone(UTC).time()
    if start <= clock <= end:
        raise LaneRefusedError(
            "inside the fleet's nightly window (22:00 to 24:00 UTC): the lane "
            "shares the data vendors' budgets with the fleet's run"
        )


def _refuse_fleet_keys(lane: LaneValues, fleet: Mapping[str, str]) -> None:
    for name, value in fleet.items():
        if value in (lane.key, lane.secret):
            raise LaneRefusedError(
                f"a test Alpaca value equals the fleet's {name}: the lane would "
                "trade on the fleet's account"
            )


def _refuse_fleet_graph(lane_dsn: str, fleet_dsn: str) -> None:
    if not neon_endpoint_id(lane_dsn):
        raise LaneRefusedError(f"{LANE_DSN} names no host")
    if fleet_dsn and neon_endpoint_id(lane_dsn) == neon_endpoint_id(fleet_dsn):
        raise LaneRefusedError(
            f"{LANE_DSN} is on the fleet's database endpoint: the lane would "
            "write to the live graph"
        )
