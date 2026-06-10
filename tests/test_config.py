"""Config primitive tests — env override, bounds, and the constants catalogue."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, describe, tunable


class _SampleSettings(AgentSettings):
    model_config = SettingsConfigDict(env_prefix="SAMPLE_", frozen=True)

    min_confidence: float = tunable(
        0.6, why="below 0.6 the signal is indistinguishable from noise", ge=0.0, le=1.0
    )


class _UnboundedSettings(AgentSettings):
    model_config = SettingsConfigDict(env_prefix="UNBOUNDED_", frozen=True)

    label: str = tunable("paper", why="names the current local test profile")


def test_default_is_used_when_no_env():
    assert _SampleSettings().min_confidence == 0.6


def test_env_override(monkeypatch):
    monkeypatch.setenv("SAMPLE_MIN_CONFIDENCE", "0.8")
    assert _SampleSettings().min_confidence == 0.8


def test_bounds_reject_out_of_range(monkeypatch):
    monkeypatch.setenv("SAMPLE_MIN_CONFIDENCE", "1.5")
    with pytest.raises(ValidationError):
        _SampleSettings()


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
