"""Deterministic lane fixtures, independent of production name lists.

Agent: orchestration
Role: provide literal measured names, synthetic values and in-memory clients.
External I/O: reads the committed vocabulary; never contacts an endpoint.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from agents.provider.agent import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary
from orchestration.tests.helpers import source

if TYPE_CHECKING:
    from collections.abc import Iterator

MEASURED_FLEET_NAMES = (
    "ALPACA_API_KEY",
    "ALPACA_PAPER_API_KEY",
    "EXECUTION_ALPACA_API_KEY",
    "PROVIDER_ALPACA_API_KEY",
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
MEASURED_ENDPOINT_NAMES = (
    "ALPACA_BASE_URL",
    "EXECUTION_ALPACA_BASE_URL",
    "AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON",
    "AZURE_SERVICEBUS_NAMESPACE_ENDPOINT",
    "MASTER_URL",
    "GRAPH_VOCABULARY_B64",
    "PORTFOLIO_MANAGER_ISSUER_MAP_B64",
)
MEASURED_FEED_NAMES = (
    "PROVIDER_FINNHUB_API_KEY",
    "PROVIDER_FMP_API_KEY",
    "PROVIDER_ALPHAVANTAGE_API_KEY",
    "PROVIDER_TIINGO_API_KEY",
    "PROVIDER_FRED_API_KEY",
)
LANE = {
    # pragma: allowlist nextline secret
    "ALPACA_TEST_API_KEY": "PKLANE",
    # pragma: allowlist nextline secret
    "ALPACA_TEST_API_SECRET": "lane-secret",
    "ALPACA_TEST_ENDPOINT": "https://paper-api.alpaca.markets/v2",
    "LANE_POSTGRES_DSN": "postgresql://u:p@ep-lane-1.ap-southeast-2.aws.neon.tech/db",
}
SAFE_NOW = datetime(2026, 11, 27, 3, tzinfo=UTC)
PACKS = Path(__file__).resolve().parents[1] / "packs"


@pytest.fixture
def preserve_environment() -> Iterator[None]:
    """DL-328 D3: restore every environment name, including isolation's additions."""
    before = dict(os.environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(before)


def planted_environment() -> tuple[dict[str, str], dict[str, str | None]]:
    """Build distinct shell/file values so either source's leaks are observable."""
    shell = {
        name: f"shell-{name}"
        for name in (*MEASURED_FLEET_NAMES, *MEASURED_ENDPOINT_NAMES)
    }
    shell["PATH"] = os.environ.get("PATH", "fixture-path")
    dotenv: dict[str, str | None] = {
        name: f"file-{name}" for name in MEASURED_FLEET_NAMES
    }
    dotenv.update({name: f"feed-{name}" for name in MEASURED_FEED_NAMES})
    dotenv.update(LANE)
    for name in ("TIINGO_API_KEY", "HF_TOKEN"):
        dotenv[name] = f"unused-{name}"
    dotenv.update(EMPTY_VALUE=None, PLAIN_NAME="file-plain")
    shell["PLAIN_NAME"] = "shell-plain"
    return shell, dotenv


def guarded_graph() -> GuardedGraphStore:
    """Create the memory graph under the fleet's committed vocabulary."""
    declaration = json.loads(
        (PACKS / "trading_graph_vocabulary.json").read_text(encoding="utf-8")
    )
    return GuardedGraphStore(InMemoryGraphStore(), Vocabulary.from_mapping(declaration))


def provider(graph: GuardedGraphStore) -> ProviderAgent:
    """Build the provider on the deterministic, date-relative source."""
    return ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source(),
        settings=ProviderSettings(max_staleness_days=7),
    )


class CountingFake(FakeLLMClient):
    """Count completions while retaining the deterministic fake boundary."""

    def __init__(self, response: str) -> None:
        super().__init__({"DECISION UNDER TEST": response})
        self.calls = 0

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        self.calls += 1
        return super().complete(system=system, user=user, tool_schema=tool_schema)
