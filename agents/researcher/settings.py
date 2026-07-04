"""Researcher agent settings and evidence/proposal tunables.

Agent: researcher
Role: own defaults for evidence window, proposal bounds, and parameter references.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class ResearcherSettings(AgentSettings):
    """Settings for bounded research proposals."""

    model_config = SettingsConfigDict(env_prefix="RESEARCHER_", frozen=True)

    lookback_days: int = tunable(
        90,
        why="Quarterly history for slow changes.",
        ge=30,
        le=365,
        unit="days",
    )
    min_sample_runs: int = tunable(
        5,
        why="Multiple runs avoid one-day drift.",
        ge=3,
        le=100,
        unit="runs",
    )
    min_evidence_window_days: int = tunable(
        30,
        why="Monthly window for parameter-change evidence.",
        ge=7,
        le=365,
        unit="days",
    )
    max_changes_per_proposal: int = tunable(
        2,
        why="Small proposals stay reviewable and reversible.",
        ge=1,
        le=5,
    )
    confidence_floor_reference: float = tunable(
        0.30,
        why="Analyst confidence-floor baseline without importing analyst.",
        ge=0.0,
        le=1.0,
    )
    confidence_step: float = tunable(
        0.05,
        why="Gradual threshold moves keep effects measurable.",
        ge=0.01,
        le=0.20,
    )
    confidence_low_water: float = tunable(
        0.40,
        why="Below this average, demand stronger signals.",
        ge=0.0,
        le=1.0,
    )
    confidence_high_water: float = tunable(
        0.70,
        why="Above this average, allow more candidates.",
        ge=0.0,
        le=1.0,
    )
    backtest_top_k: int = tunable(
        20,
        why=(
            "Portfolio breadth for walk-forward proposal evidence; "
            "equal-weight top-K by score."
        ),
        ge=5,
        le=100,
    )
    backtest_slippage_bps: float = tunable(
        10.0,
        why=(
            "Per-unit-turnover cost charged in the walk-forward simulator; "
            "keeps evidence honest about churn."
        ),
        ge=0.0,
        le=100.0,
        unit="bps",
    )
    backtest_holdout_fraction: float = tunable(
        0.3,
        why=(
            "Trailing fraction of the window reported separately as "
            "out-of-sample consistency (R001 risk register: OOS >= 30%)."
        ),
        ge=0.3,
        le=0.5,
    )
