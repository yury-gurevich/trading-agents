"""Trading credential probes for Key Vault seeding.

Agent: orchestration
Role: provide pack-specific live working-checks for injected vault seed entries.
External I/O: optional HTTPS calls to market-data, broker, LLM, and Neo4j services.
"""

from __future__ import annotations

import urllib.request
from collections.abc import Callable, Mapping

from agents.master.vault_seed import ProbeResult
from agents.provider.alpaca_data import AlpacaDataSource
from agents.provider.fmp import FMPDataSource
from agents.provider.fundamentals import FinnhubDataSource
from agents.provider.tiingo import TiingoDataSource
from orchestration.packs.trading_vault_probe_support import (
    http_json,
    patched_env,
    probe_window,
    required,
    run_probe,
)

Probe = Callable[[Mapping[str, str]], ProbeResult]
PROBES: dict[str, Probe] = {}
_ALPACA_KEY_NAMES = (
    "PROVIDER_ALPACA_API_KEY",
    "ALPACA_PAPER_API_KEY",
    "ALPACA_API_KEY",
)
_ALPACA_SECRET_NAMES = ("PROVIDER_ALPACA_API_SECRET", "ALPACA_API_SECRET")


def _probe(name: str) -> Callable[[Probe], Probe]:
    def register(func: Probe) -> Probe:
        PROBES[name] = func
        return func

    return register


@_probe("tiingo")
def probe_tiingo(env: Mapping[str, str]) -> ProbeResult:
    """Check Tiingo with a one-symbol daily OHLCV fetch."""
    return run_probe(
        "tiingo",
        lambda: bool(
            TiingoDataSource(
                api_key=required(env, "PROVIDER_TIINGO_API_KEY", "TIINGO_API_KEY"),
                base_url=env.get("PROVIDER_TIINGO_BASE_URL", "https://api.tiingo.com"),
                timeout=int(env.get("PROVIDER_TIINGO_TIMEOUT", "15")),
            ).fetch_ohlcv(("AAPL",), probe_window())
        ),
    )


@_probe("fmp")
def probe_fmp(env: Mapping[str, str]) -> ProbeResult:
    """Check FMP with a one-symbol daily OHLCV fetch."""
    return run_probe(
        "fmp",
        lambda: bool(
            FMPDataSource(
                api_key=required(env, "PROVIDER_FMP_API_KEY", "FMP_API_KEY"),
                base_url=env.get(
                    "PROVIDER_FMP_BASE_URL", "https://financialmodelingprep.com"
                ),
                timeout=int(env.get("PROVIDER_FMP_TIMEOUT", "15")),
            ).fetch_ohlcv(("AAPL",), probe_window())
        ),
    )


@_probe("finnhub")
def probe_finnhub(env: Mapping[str, str]) -> ProbeResult:
    """Check Finnhub with a one-symbol profile/sector fetch."""
    return run_probe(
        "finnhub",
        lambda: bool(
            FinnhubDataSource(
                api_key=required(env, "PROVIDER_FINNHUB_API_KEY", "FINNHUB_API_KEY"),
                base_url=env.get(
                    "PROVIDER_FINNHUB_BASE_URL", "https://finnhub.io/api/v1"
                ),
                timeout=int(env.get("PROVIDER_FINNHUB_TIMEOUT", "10")),
            ).fetch_sectors(("AAPL",))
        ),
    )


@_probe("alpaca-data")
def probe_alpaca_data(env: Mapping[str, str]) -> ProbeResult:
    """Check Alpaca market data with a one-symbol bars fetch."""
    return run_probe(
        "alpaca-data",
        lambda: bool(_alpaca_data_source(env).fetch_ohlcv(("AAPL",), probe_window())),
    )


@_probe("alpaca-broker")
def probe_alpaca_broker(env: Mapping[str, str]) -> ProbeResult:
    """Check Alpaca broker auth with a non-mutating account request."""
    return run_probe(
        "alpaca-broker", lambda: http_json(_alpaca_account_request(env)) is not None
    )


@_probe("openai")
def probe_openai(env: Mapping[str, str]) -> ProbeResult:
    """Check OpenAI auth with the models endpoint."""
    req = urllib.request.Request(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {required(env, 'OPENAI_API_KEY')}"},
    )
    return run_probe("openai", lambda: http_json(req) is not None)


@_probe("anthropic")
def probe_anthropic(env: Mapping[str, str]) -> ProbeResult:
    """Check Anthropic auth with the models endpoint."""
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/models?limit=1",
        headers={
            "anthropic-version": "2023-06-01",
            "x-api-key": required(env, "ANTHROPIC_API_KEY"),
        },
    )
    return run_probe("anthropic", lambda: http_json(req) is not None)


@_probe("neo4j")
def probe_neo4j(env: Mapping[str, str]) -> ProbeResult:
    """Check Neo4j by building the configured graph store and doing one cheap read."""
    from kernel.graph_env import build_graph_from_env
    from kernel.startup import graph_reachable

    def check() -> bool:
        with patched_env(env):
            graph = build_graph_from_env()
        try:
            return graph_reachable(graph)
        finally:
            close = getattr(graph, "close", None)
            if callable(close):
                close()

    return run_probe("neo4j", check)


def _alpaca_data_source(env: Mapping[str, str]) -> AlpacaDataSource:
    return AlpacaDataSource(
        api_key=required(env, *_ALPACA_KEY_NAMES),
        api_secret=required(env, *_ALPACA_SECRET_NAMES),
        base_url=env.get(
            "PROVIDER_ALPACA_DATA_BASE_URL", "https://data.alpaca.markets"
        ),
        feed=env.get("PROVIDER_ALPACA_DATA_FEED", "iex"),
        timeout=int(env.get("PROVIDER_ALPACA_DATA_TIMEOUT", "15")),
    )


def _alpaca_account_request(env: Mapping[str, str]) -> urllib.request.Request:
    base_url = env.get(
        "EXECUTION_ALPACA_BASE_URL",
        env.get("ALPACA_ENDPOINT", "https://paper-api.alpaca.markets"),
    )
    return urllib.request.Request(  # noqa: S310
        f"{base_url}/v2/account",
        headers={
            "APCA-API-KEY-ID": required(env, *_ALPACA_KEY_NAMES),
            "APCA-API-SECRET-KEY": required(
                env, "EXECUTION_ALPACA_SECRET_KEY", "ALPACA_API_SECRET"
            ),
        },
    )
