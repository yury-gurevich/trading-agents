"""Analyst settings validation tests.

Agent: analyst
Role: verify the indicator-span ordering validator rejects bad configurations.
External I/O: none.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agents.analyst.settings import AnalystSettings


def test_macd_fast_must_trail_slow() -> None:
    with pytest.raises(ValidationError, match="macd_fast must be below macd_slow"):
        AnalystSettings(macd_fast=26, macd_slow=26)


def test_ema_short_must_trail_long() -> None:
    with pytest.raises(
        ValidationError, match="ema_short_period must be below ema_long_period"
    ):
        AnalystSettings(ema_short_period=50, ema_long_period=50)


def test_default_spans_are_ordered() -> None:
    settings = AnalystSettings()

    assert settings.macd_fast < settings.macd_slow
    assert settings.ema_short_period < settings.ema_long_period
