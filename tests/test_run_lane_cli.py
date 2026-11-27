"""Test-lane command refusals and isolated in-memory execution.

Agent: tooling
Role: prove DL-328 D2-D6 at the CLI boundary without running the script.
External I/O: temporary synthetic values files; no network or actual .env.
"""

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from scripts import run_lane as cli

from agents.execution.paper_broker import PaperBroker
from agents.provider.agent import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.scanner.universe import FileUniverse
from kernel import GraphStore
from orchestration.settings import OrchestratorSettings
from orchestration.tests.lane_fixtures import (
    LANE,
    SAFE_NOW,
    guarded_graph,
    provider,
)
from orchestration.tests.lane_fixtures import (
    preserve_environment as preserve_environment,
)


@pytest.fixture(autouse=True)
def clean_environment(
    preserve_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DL-328 D3: no inherited endpoints, and restore the whole environment."""
    os.environ.clear()
    monkeypatch.setattr(cli, "_now", lambda: SAFE_NOW)


def values_file(tmp_path: Path, values: dict[str, str]) -> Path:
    """Write fake inputs under a name that cannot be found by dotenv discovery."""
    path = tmp_path / "lane-values.txt"
    path.write_text("\n".join(f"{k}={v}" for k, v in values.items()), encoding="utf-8")
    return path


def test_an_unsafe_start_is_refused_before_any_endpoint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DL-328 D2: refused starts neither mutate the environment nor build clients."""

    def unexpected(*args: object, **kwargs: object) -> None:
        pytest.fail("endpoint built before isolation returned")

    for target in (
        "kernel.graph_env.build_graph_from_env",
        "agents.provider.entrypoint.build_agent",
        "agents.execution.broker_factory.broker_from_settings",
    ):
        monkeypatch.setattr(target, unexpected)
    before = dict(os.environ)
    # pragma: allowlist nextline secret
    path = values_file(tmp_path, {"ALPACA_TEST_API_KEY": "PKLANE"})
    assert cli.main(["--env-file", str(path)]) == 2
    assert capsys.readouterr().out.startswith("REFUSED: missing lane values")
    assert dict(os.environ) == before
    path = values_file(tmp_path, {**LANE, "POSTGRES_DSN": LANE["LANE_POSTGRES_DSN"]})
    assert cli.main(["--env-file", str(path)]) == 2
    assert "live graph" in capsys.readouterr().out
    assert dict(os.environ) == before


def test_an_isolated_start_runs_one_lane_run_and_prints_its_verdict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DL-328 D3/D4/D5/D6: builders see lane values and one normalized run passes."""
    graph = guarded_graph()
    calls: dict[str, str] = {}

    def build_graph() -> GraphStore:
        calls["dsn"] = os.environ["POSTGRES_DSN"]
        return graph

    def build_provider(
        settings: ProviderSettings, received: GraphStore
    ) -> ProviderAgent:
        assert received is graph
        calls["key"] = settings.alpaca_api_key
        return provider(graph)

    monkeypatch.setattr("kernel.graph_env.build_graph_from_env", build_graph)
    monkeypatch.setattr("agents.provider.entrypoint.build_agent", build_provider)
    monkeypatch.setattr(
        "agents.execution.broker_factory.broker_from_settings", lambda _: PaperBroker()
    )
    monkeypatch.setattr(
        "orchestration.lane_run.last_closed_session",
        lambda _: datetime.now(tz=UTC).date(),
    )
    path = values_file(
        tmp_path,
        {**LANE, "POSTGRES_DSN": "postgresql://u:p@ep-fleet-2.aws.neon.tech/db"},
    )
    assert cli.main(["--env-file", str(path), "--tickers", "aapl, msft"]) == 0
    assert calls == {"dsn": LANE["LANE_POSTGRES_DSN"], "key": "PKLANE"}
    output = capsys.readouterr().out
    assert output.startswith("LANE RUN  2 tickers, at most 12 rounds")
    assert "  run id   lane-20261127-030000" in output
    assert "PASS" in output
    assert len(graph.list_nodes("RunRequest")) == 1
    assert graph.list_nodes("RunRequest")[0].props["tickers"] == ("AAPL", "MSFT")


def test_the_default_universe_is_the_fleets() -> None:
    """DL-328 D1: an omitted ticker list uses the fleet's configured universe."""
    expected = FileUniverse().members(OrchestratorSettings().universe)
    assert expected
    assert cli._tickers("") == expected
