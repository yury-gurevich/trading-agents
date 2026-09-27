"""The replay scripts read the fleet's own environment names.

Agent: tooling
Role: prove the sector fetch finds the fleet's Finnhub key and the builder loads .env.
External I/O: none; environment and HTTP are faked.

S235's live sector fetch failed on its first call: it read `FINNHUB_API_KEY`, while the
fleet's `.env` and the provider call it `PROVIDER_FINNHUB_API_KEY`; and
`replay_universe.py` never loaded `.env`, unlike `replay_dataset.py`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts import replay_universe
from scripts.sp500_context import fetch_sectors

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_the_sector_fetch_reads_the_providers_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S235-A15: the key comes from PROVIDER_FINNHUB_API_KEY, the fleet's name."""
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    planted = "fleet-key"  # pragma: allowlist secret - synthetic fixture token
    monkeypatch.setenv("PROVIDER_FINNHUB_API_KEY", planted)
    tokens: list[str] = []

    def get(url: str, *, params: dict[str, str], timeout: int) -> str:
        del url, timeout
        tokens.append(params["token"])
        return '{"finnhubIndustry":"Technology"}'

    fetch_sectors(tmp_path, ("AAA",), get=get, sleep=lambda _seconds: None)

    assert tokens == [planted]


def test_the_builder_loads_the_repos_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """S235: `replay_universe.py` loads `.env` like `replay_dataset.py` does."""
    loaded: list[object] = []
    monkeypatch.setattr(replay_universe, "load_dotenv", loaded.append)
    monkeypatch.setattr(replay_universe, "describe", lambda: "described")

    assert replay_universe.main(["--describe"]) == 0
    assert [str(path).replace("\\", "/").endswith("/.env") for path in loaded] == [True]
