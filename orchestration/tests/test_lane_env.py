"""Lane process environment checks.

Agent: orchestration
Role: prove DL-328 D3 isolation against independent planted name lists.
External I/O: reads committed pack files and a temporary synthetic JSON file.
"""

import os
from decimal import Decimal
from pathlib import Path

import pytest

from agents.deliberator.settings import DeliberatorSettings
from agents.execution.settings import ExecutionSettings
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider.settings import ProviderSettings
from kernel import AzureServiceBusSettings
from orchestration.lane_env import (
    isolate_lane,
    load_tunables_pack,
    pack_tunables,
    refuse_leaks,
)
from orchestration.lane_guard import LaneRefusedError
from orchestration.tests.lane_fixtures import (
    LANE,
    MEASURED_FEED_NAMES,
    MEASURED_FLEET_NAMES,
    PACKS,
    SAFE_NOW,
    planted_environment,
)
from orchestration.tests.lane_fixtures import (
    preserve_environment as preserve_environment,
)


def test_the_lane_environment_holds_no_fleet_value() -> None:
    """DL-328 D3: both shell-only and file-supplied values are removed or replaced."""
    for split in (False, True):
        shell, dotenv = planted_environment()
        if split:
            for name in MEASURED_FLEET_NAMES[7:]:
                dotenv.pop(name)
        before = {*shell.values(), *(v for v in dotenv.values() if v is not None)}
        path = shell["PATH"]
        isolate_lane(shell, dotenv, now=SAFE_NOW, pack=load_tunables_pack())
        allowed = {*LANE.values(), path, *(f"feed-{n}" for n in MEASURED_FEED_NAMES)}
        assert (before & set(shell.values())) <= allowed
        assert {name: shell[name] for name in MEASURED_FEED_NAMES} == {
            name: f"feed-{name}" for name in MEASURED_FEED_NAMES
        }
        assert shell["POSTGRES_DSN"] == LANE["LANE_POSTGRES_DSN"]
        for name in ("EXECUTION_ALPACA_API_KEY", "PROVIDER_ALPACA_API_KEY"):
            assert shell[name] == LANE["ALPACA_TEST_API_KEY"]
        for name in ("EXECUTION_ALPACA_SECRET_KEY", "PROVIDER_ALPACA_API_SECRET"):
            assert shell[name] == LANE["ALPACA_TEST_API_SECRET"]
        assert shell["EXECUTION_ALPACA_BASE_URL"] == "https://paper-api.alpaca.markets"
        for name, filename in (
            ("GRAPH_VOCABULARY_PATH", "trading_graph_vocabulary.json"),
            ("PORTFOLIO_MANAGER_ISSUER_MAP_PATH", "trading_issuer_map.json"),
        ):
            assert Path(shell[name]) == PACKS / filename
            assert Path(shell[name]).is_file()
        assert shell["PATH"] == path
        assert not (
            {"TIINGO_API_KEY", "HF_TOKEN", "EMPTY_VALUE", "PLAIN_NAME", *LANE}
            & shell.keys()
        )


@pytest.mark.usefixtures("preserve_environment")
def test_settings_built_after_isolation_reach_only_the_lane() -> None:
    """DL-328 D3 / EXEC-OUT-03: settings see lane endpoints and the full pack."""
    shell, dotenv = planted_environment()
    os.environ.clear()
    os.environ.update(shell)
    isolate_lane(os.environ, dotenv, now=SAFE_NOW, pack=load_tunables_pack())
    execution, provider = ExecutionSettings(), ProviderSettings()
    assert execution.alpaca_api_key == LANE["ALPACA_TEST_API_KEY"]
    assert execution.alpaca_secret_key == LANE["ALPACA_TEST_API_SECRET"]
    assert execution.alpaca_base_url == "https://paper-api.alpaca.markets"
    assert execution.deliberation_grace_seconds == 1800
    assert provider.alpaca_api_key == LANE["ALPACA_TEST_API_KEY"]
    assert provider.alpaca_api_secret == LANE["ALPACA_TEST_API_SECRET"]
    bus = AzureServiceBusSettings()
    assert not bus.connection_string
    assert not bus.connection_strings_json
    pm = PortfolioManagerSettings()
    assert pm.max_position_pct == Decimal("0.01")
    assert pm.max_positions == 60
    assert DeliberatorSettings(role="manager").request_timeout_seconds == 240


def test_a_surviving_fleet_value_is_refused_by_name() -> None:
    """DL-328 D3: compare values across arbitrary names and report sorted sources."""
    # pragma: allowlist nextline secret
    fleet = {"POSTGRES_DSN": "live", "OPENAI_API_KEY": "sk"}
    with pytest.raises(LaneRefusedError) as error:
        refuse_leaks({"renamed": "sk", "alias": "live"}, fleet)
    assert str(error.value) == (
        "fleet values still in the lane's environment: OPENAI_API_KEY, POSTGRES_DSN"
    )
    refuse_leaks({"renamed": "lane"}, fleet)


def test_the_pack_leaves_out_the_peers_and_refuses_a_conflict(tmp_path: Path) -> None:
    """DL-328 D3: manager values survive peer omission; unequal duplicates fail."""
    packed = pack_tunables(load_tunables_pack())
    assert packed["DELIBERATOR_REQUEST_TIMEOUT_SECONDS"] == "240"
    assert packed["SCANNER_CANDIDATE_CAP"] == "25"
    assert pack_tunables(
        {"apps": {"a": {"X": "1"}, "b": {"X": 1}, "c": "not an object"}}
    ) == {"X": "1"}
    with pytest.raises(ValueError, match="sets X twice"):
        pack_tunables({"apps": {"a": {"X": "1"}, "b": {"X": "2"}}})
    with pytest.raises(ValueError, match="no apps object"):
        pack_tunables({})
    path = tmp_path / "pack.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_tunables_pack(path)
