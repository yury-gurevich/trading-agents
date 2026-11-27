"""Lane start refusals.

Agent: orchestration
Role: prove DL-328 D2 from independently measured values and boundary clocks.
External I/O: none.
"""

from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from orchestration.lane_guard import (
    LaneRefusedError,
    LaneValues,
    fleet_values,
    lane_values,
    neon_endpoint_id,
    refuse_unsafe_start,
)
from orchestration.tests.lane_fixtures import LANE, MEASURED_FLEET_NAMES, SAFE_NOW

FLEET_DSN = "postgresql://u:p@ep-fleet-1234.aws.neon.tech/db"
LANE_DSN = "postgresql://u:p@ep-lane-5678.aws.neon.tech/db"


def test_each_missing_lane_value_is_named() -> None:
    """DL-328 D2: refuse missing/blank values by name and strip all four inputs."""
    # pragma: allowlist nextline secret
    missing = {"ALPACA_TEST_API_KEY": "k", "ALPACA_TEST_API_SECRET": "  "}
    with pytest.raises(LaneRefusedError) as error:
        lane_values(missing)
    assert str(error.value) == (
        "missing lane values: ALPACA_TEST_API_SECRET, "
        "ALPACA_TEST_ENDPOINT, LANE_POSTGRES_DSN"
    )
    assert lane_values({k: f" {v} " for k, v in LANE.items()}) == LaneValues(
        "PKLANE", "lane-secret", LANE["ALPACA_TEST_ENDPOINT"], LANE["LANE_POSTGRES_DSN"]
    )


@pytest.mark.parametrize("name", MEASURED_FLEET_NAMES)
def test_every_fleet_name_is_read_from_the_env_file_then_the_environment(
    name: str,
) -> None:
    """DL-328 D2: every measured fleet name is read, with file precedence."""
    assert fleet_values({}, {name: "f"}) == {name: "f"}
    assert fleet_values({name: "s"}, {}) == {name: "s"}
    assert fleet_values({name: "s"}, {name: "f"}) == {name: "f"}
    # pragma: allowlist nextline secret
    assert fleet_values({"HF_TOKEN": "x"}, {"PATH": "y"}) == {}


@pytest.mark.parametrize("name", MEASURED_FLEET_NAMES)
@pytest.mark.parametrize("field", ["key", "secret"])
def test_a_test_value_equal_to_a_fleet_value_is_refused(name: str, field: str) -> None:
    """DL-328 D2: either lane credential equal to any fleet value is refused."""
    lane = lane_values(LANE)
    fleet = fleet_values({}, {name: getattr(lane, field)})
    with pytest.raises(LaneRefusedError, match=f"fleet's {name}"):
        refuse_unsafe_start(lane, fleet, now=SAFE_NOW)


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.alpaca.markets",
        "https://paper-api.alpaca.markets.example.com/v2",
        "paper-api.alpaca.markets",
    ],
)
def test_an_endpoint_other_than_the_paper_host_is_refused(endpoint: str) -> None:
    """DL-328 D2 / EXEC-OUT-03: only the exact paper host is allowed."""
    with pytest.raises(LaneRefusedError, match="paper host"):
        refuse_unsafe_start(
            replace(lane_values(LANE), endpoint=endpoint), {}, now=SAFE_NOW
        )


@pytest.mark.parametrize(
    "dsn",
    [
        FLEET_DSN,
        # pragma: allowlist nextline secret
        "postgresql://other:other@ep-fleet-1234-pooler.aws.neon.tech/other",
        "postgresql://u:p@EP-FLEET-1234.aws.neon.tech/db",
    ],
)
def test_the_fleets_database_endpoint_is_refused_direct_or_pooled(dsn: str) -> None:
    """DL-328 D2: a path/user/case/pooler change cannot hide the fleet endpoint."""
    with pytest.raises(LaneRefusedError, match="live graph"):
        refuse_unsafe_start(
            replace(lane_values(LANE), dsn=dsn),
            {"POSTGRES_DSN": FLEET_DSN},
            now=SAFE_NOW,
        )


def test_a_lane_graph_on_its_own_endpoint_starts() -> None:
    """DL-328 D2: a separate endpoint starts; a hostless lane DSN is refused."""
    lane = replace(lane_values(LANE), dsn=LANE_DSN)
    for fleet in ({}, {"POSTGRES_DSN": FLEET_DSN}):
        refuse_unsafe_start(lane, fleet, now=SAFE_NOW)
    assert neon_endpoint_id(FLEET_DSN) == "ep-fleet-1234"
    with pytest.raises(LaneRefusedError, match="names no host"):
        refuse_unsafe_start(replace(lane, dsn="not a dsn"), {}, now=SAFE_NOW)


@pytest.mark.parametrize(
    ("now", "refused"),
    [
        (datetime(2026, 11, 27, 21, 59, 59, tzinfo=UTC), False),
        (datetime(2026, 11, 27, 22, tzinfo=UTC), True),
        (datetime(2026, 11, 27, 23, 59, 59, tzinfo=UTC), True),
        (datetime(2026, 11, 28, tzinfo=UTC), False),
        (datetime(2026, 11, 28, 9, 30, tzinfo=timezone(timedelta(hours=11))), True),
    ],
)
def test_the_fleets_nightly_window_is_refused(now: datetime, refused: bool) -> None:
    """DL-328 D2: refuse the inclusive UTC window, including offset clocks."""
    if refused:
        with pytest.raises(LaneRefusedError, match="nightly window"):
            refuse_unsafe_start(lane_values(LANE), {}, now=now)
    else:
        refuse_unsafe_start(lane_values(LANE), {}, now=now)
