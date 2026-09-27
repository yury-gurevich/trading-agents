"""Tests for S235 replay settings materialization.

Agent: tooling
Role: verify fixture replay uses fleet settings plus explicit operator overrides.
External I/O: reads checked-in orchestration pack only.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from scripts.replay_settings import build_effective_settings


def test_pack_settings_override_code_defaults() -> None:
    """S235-A3: replay settings start at code defaults, then apply fleet pack envs."""
    settings = build_effective_settings(())

    assert settings.scanner.candidate_cap == 25
    assert settings.analyst.stop_target_mode == "scaled"
    assert settings.execution.order_price_tolerance_mode == "scaled"
    assert settings.portfolio.max_position_pct == Decimal("0.01")
    assert settings.non_defaults["SCANNER_CANDIDATE_CAP"] == "25"


def test_cli_set_uses_pack_env_names_and_reports_unknown_key() -> None:
    """S235-A3: --set accepts only known pack-style environment names."""
    settings = build_effective_settings(("PORTFOLIO_MANAGER_MAX_POSITIONS=7",))

    assert settings.portfolio.max_positions == 7
    assert settings.non_defaults["PORTFOLIO_MANAGER_MAX_POSITIONS"] == "7"
    with pytest.raises(ValueError, match="UNKNOWN_REPLAY_SETTING"):
        build_effective_settings(("UNKNOWN_REPLAY_SETTING=1",))
