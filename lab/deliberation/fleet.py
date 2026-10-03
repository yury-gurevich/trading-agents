"""Settings exactly as the deployed fleet runs them: code defaults overlaid by the pack's env."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path

from agents.analyst.settings import AnalystSettings
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider.settings import ProviderSettings
from agents.scanner.settings import ScannerSettings

PACK = Path(__file__).resolve().parents[2] / "orchestration/packs/trading_tunables.json"


def pack_env(app: str) -> dict[str, str]:
    """The env overrides the pack injects into one fleet app."""
    return dict(json.loads(PACK.read_text())["apps"].get(app, {}))


@contextmanager
def _env(values: dict[str, str]):
    saved = {k: os.environ.get(k) for k in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def fleet_settings():
    """Return (scanner, analyst, pm, provider) settings as the fleet sees them."""
    with _env(pack_env("scanner")):
        scanner = ScannerSettings()
    with _env(pack_env("analyst")):
        analyst = AnalystSettings()
    with _env(pack_env("portfolio-manager")):
        pm = PortfolioManagerSettings()
    provider = ProviderSettings()
    return scanner, analyst, pm, provider
