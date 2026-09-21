"""Config primitive tests — env override, bounds, and the constants catalogue."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from agents.analyst.settings import AnalystSettings
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider.settings import ProviderSettings
from kernel import AgentSettings, describe, tunable


class _SampleSettings(AgentSettings):
    model_config = SettingsConfigDict(env_prefix="SAMPLE_", frozen=True)

    min_confidence: float = tunable(
        0.6, why="below 0.6 the signal is indistinguishable from noise", ge=0.0, le=1.0
    )


class _UnboundedSettings(AgentSettings):
    model_config = SettingsConfigDict(env_prefix="UNBOUNDED_", frozen=True)

    label: str = tunable("paper", why="names the current local test profile")


class _ExclusiveLowerSettings(AgentSettings):
    model_config = SettingsConfigDict(env_prefix="STRICT_", frozen=True)

    fraction: float = tunable(
        0.5,
        why="exclusive zero protects division-style fractions",
        gt=0.0,
        le=1.0,
    )


def test_default_is_used_when_no_env():
    assert _SampleSettings().min_confidence == 0.6


def test_env_override(monkeypatch):
    monkeypatch.setenv("SAMPLE_MIN_CONFIDENCE", "0.8")
    assert _SampleSettings().min_confidence == 0.8


def test_bounds_reject_out_of_range(monkeypatch):
    monkeypatch.setenv("SAMPLE_MIN_CONFIDENCE", "1.5")
    with pytest.raises(ValidationError):
        _SampleSettings()


def test_exclusive_lower_bound_rejects_equal_value(monkeypatch):
    monkeypatch.setenv("STRICT_FRACTION", "0.0")
    with pytest.raises(ValidationError):
        _ExclusiveLowerSettings()


def test_describe_catalogues_the_tunable():
    rows = describe(_SampleSettings)
    assert len(rows) == 1
    row = rows[0]
    assert row.env_var == "SAMPLE_MIN_CONFIDENCE"
    assert row.default == 0.6
    assert row.justification
    assert row.minimum == 0.0
    assert row.maximum == 1.0


def test_describe_catalogues_unbounded_tunable():
    rows = describe(_UnboundedSettings)
    assert len(rows) == 1
    row = rows[0]
    assert row.env_var == "UNBOUNDED_LABEL"
    assert row.minimum is None
    assert row.maximum is None


def test_describe_catalogues_exclusive_lower_bound():
    rows = describe(_ExclusiveLowerSettings)
    assert len(rows) == 1
    row = rows[0]
    assert row.env_var == "STRICT_FRACTION"
    assert row.minimum == 0.0
    assert row.maximum == 1.0


def test_describe_exposes_envelope_and_source():
    """DD-04: Tunable documentation exposes its evidence envelope and source."""

    class EnvelopeSettings(AgentSettings):
        model_config = SettingsConfigDict(env_prefix="ENVELOPE_", frozen=True)

        fraction: float = tunable(
            0.6,
            why="Synthetic configuration to prove evidence metadata.",
            ge=0.0,
            le=1.0,
            envelope=(0.5, 0.8),
            source="Synthetic evidence source.",
        )

    row = describe(EnvelopeSettings)[0]
    assert row.envelope_min == 0.5
    assert row.envelope_max == 0.8
    assert row.source == "Synthetic evidence source."


def test_a_tunable_without_an_envelope_is_unchanged():
    """DD-01: Tunables without evidence metadata retain existing catalogue values."""

    row = describe(_UnboundedSettings)[0]
    assert row.envelope_min is None
    assert row.envelope_max is None
    assert row.source is None


def test_an_envelope_without_a_source_is_refused():
    """DD-04: An evidence envelope without provenance is rejected at declaration."""

    with pytest.raises(ValueError, match="source"):
        tunable(
            0.6,
            why="Synthetic configuration to prove provenance is mandatory.",
            envelope=(0.5, 0.8),
        )


def test_exactly_thirteen_risk_settings_declare_evidence_envelopes():
    """DD-04: S207 declares provenance for the thirteen researched risk settings.

    Settings outside the researched set do not receive an evidence envelope.
    """

    documented = {
        f"{settings_cls.__name__}.{row.name}"
        for settings_cls in (
            PortfolioManagerSettings,
            ProviderSettings,
            AnalystSettings,
        )
        for row in describe(settings_cls)
        if row.source is not None
    }

    assert documented == {
        "PortfolioManagerSettings.max_position_pct",
        "PortfolioManagerSettings.max_positions",
        "PortfolioManagerSettings.cash_buffer_pct",
        "PortfolioManagerSettings.max_sector_pct",
        "PortfolioManagerSettings.correlation_lookback_days",
        "PortfolioManagerSettings.correlation_threshold",
        "PortfolioManagerSettings.max_correlated_cluster_pct",
        "PortfolioManagerSettings.min_correlation_bars",
        "ProviderSettings.base_stop_loss_pct",
        "ProviderSettings.base_take_profit_pct",
        "AnalystSettings.scaled_stop_atr_multiplier",
        "AnalystSettings.scaled_stop_floor_pct",
        "AnalystSettings.scaled_stop_ceiling_pct",
    }
