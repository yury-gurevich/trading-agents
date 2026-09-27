"""Materialize fleet settings for the S235 replay harness.

Agent: tooling
Role: combine code defaults, checked-in fleet pack env names, and replay overrides.
External I/O: reads orchestration/packs/trading_tunables.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from agents.analyst.settings import AnalystSettings
from agents.execution.settings import ExecutionSettings
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider.settings import ProviderSettings
from agents.scanner.settings import ScannerSettings

_ROOT = Path(__file__).resolve().parents[1]
_PACK = _ROOT / "orchestration" / "packs" / "trading_tunables.json"


@dataclass(frozen=True)
class ReplaySettings:
    scanner: ScannerSettings
    analyst: AnalystSettings
    provider: ProviderSettings
    portfolio: PortfolioManagerSettings
    execution: ExecutionSettings
    non_defaults: dict[str, str]


_APPS: dict[str, type[BaseModel]] = {
    "scanner": ScannerSettings,
    "analyst": AnalystSettings,
    "provider": ProviderSettings,
    "portfolio-manager": PortfolioManagerSettings,
    "execution": ExecutionSettings,
}


def build_effective_settings(overrides: tuple[str, ...]) -> ReplaySettings:
    """Return code defaults plus fleet pack app values plus explicit KEY=VALUE."""
    raw_values = _pack_values()
    raw_values.update(_parse_overrides(overrides))
    scanner_default = _defaults(ScannerSettings)
    analyst_default = _defaults(AnalystSettings)
    provider_default = _defaults(ProviderSettings)
    portfolio_default = _defaults(PortfolioManagerSettings)
    execution_default = _defaults(ExecutionSettings)
    defaults: dict[str, BaseModel] = {
        "scanner": scanner_default,
        "analyst": analyst_default,
        "provider": provider_default,
        "portfolio-manager": portfolio_default,
        "execution": execution_default,
    }
    by_app: dict[str, dict[str, str]] = {name: {} for name in _APPS}
    for key, value in raw_values.items():
        app, field = _resolve_key(key)
        by_app[app][field] = value
    scanner = _build(ScannerSettings, scanner_default, by_app["scanner"])
    analyst = _build(AnalystSettings, analyst_default, by_app["analyst"])
    provider = _build(ProviderSettings, provider_default, by_app["provider"])
    portfolio = _build(
        PortfolioManagerSettings, portfolio_default, by_app["portfolio-manager"]
    )
    execution = _build(ExecutionSettings, execution_default, by_app["execution"])
    built: dict[str, BaseModel] = {
        "scanner": scanner,
        "analyst": analyst,
        "provider": provider,
        "portfolio-manager": portfolio,
        "execution": execution,
    }
    return ReplaySettings(
        scanner=scanner,
        analyst=analyst,
        provider=provider,
        portfolio=portfolio,
        execution=execution,
        non_defaults=_non_defaults(raw_values, defaults, built),
    )


def _pack_values() -> dict[str, str]:
    data = json.loads(_PACK.read_text(encoding="utf-8"))
    values: dict[str, str] = {}
    for app, app_values in data["apps"].items():
        if app in _APPS:
            values.update(app_values)
    return values


def _parse_overrides(overrides: tuple[str, ...]) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in overrides:
        if "=" not in item:
            raise ValueError(f"{item} must be KEY=VALUE")
        key, value = item.split("=", 1)
        _resolve_key(key)
        values[key] = value
    return values


def _resolve_key(key: str) -> tuple[str, str]:
    for app, settings_type in _APPS.items():
        prefix = _env_prefix(settings_type)
        if key.startswith(prefix):
            field = key.removeprefix(prefix).lower()
            if field in settings_type.model_fields:
                return app, field
    raise ValueError(f"unknown replay setting {key}")


def _defaults[SettingsT: BaseModel](settings_type: type[SettingsT]) -> SettingsT:
    return settings_type.model_validate({})


def _build[SettingsT: BaseModel](
    settings_type: type[SettingsT], defaults: SettingsT, values: dict[str, str]
) -> SettingsT:
    return settings_type.model_validate({**defaults.model_dump(), **values})


def _env_prefix(settings_type: type[BaseModel]) -> str:
    return str(settings_type.model_config.get("env_prefix", ""))


def _non_defaults(
    raw_values: dict[str, str],
    defaults: dict[str, BaseModel],
    built: dict[str, BaseModel],
) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in sorted(raw_values.items()):
        app, field = _resolve_key(key)
        default_value = getattr(defaults[app], field)
        effective_value = getattr(built[app], field)
        if effective_value != default_value:
            out[key] = value
    return out
