"""Dashboard settings — Azure coordinates and bounded read-side tunables.

Agent: surfaces
Role: keep dashboard configuration env-driven, justified, and safely bounded.
External I/O: process environment and the repo .env file.
"""

from typing import Literal

from pydantic import AliasChoices
from pydantic_settings import SettingsConfigDict

from kernel.config import AgentSettings, tunable


class DashboardSettings(AgentSettings):
    """Configuration for the read-only operations dashboard."""

    model_config = SettingsConfigDict(
        env_prefix="dashboard_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    azure_subscription_id: str = tunable(
        "",
        why="ARM subscription containing the standing trading fleet.",
        validation_alias=AliasChoices(
            "DASHBOARD_AZURE_SUBSCRIPTION_ID", "AZURE_SUBSCRIPTION_ID"
        ),
    )
    azure_resource_group: str = tunable(
        "trading-agents",
        why="Resource group used as the bounded dashboard read scope.",
    )
    azure_workspace_id: str = tunable(
        "",
        why="Log Analytics workspace queried for per-container evidence.",
        validation_alias=AliasChoices(
            "DASHBOARD_AZURE_WORKSPACE_ID", "AZURE_LA_WORKSPACE_ID"
        ),
    )
    azure_environment_name: str = tunable(
        "trading-agents-env",
        why="Container Apps environment label rendered in Section I.",
    )
    azure_job_name: str = tunable(
        "dispatcher-cron",
        why="Scheduled dispatcher job that starts each graph-pull run.",
    )
    azure_timeout_seconds: float = tunable(
        20.0,
        why="Bound every Azure REST read so the dashboard still degrades promptly.",
        gt=0,
        le=60,
        unit="seconds",
    )
    azure_credential_mode: Literal["auto", "default", "cli", "service_principal"] = (
        tunable(
            "auto",
            why=(
                "Allow a read-only local operator to select the Azure CLI credential "
                "when the existing service principal lacks dashboard Reader roles."
            ),
        )
    )
    fleet_cache_ttl_seconds: float = tunable(
        30.0,
        why="Avoid repeating thirteen replica reads during one page refresh.",
        ge=0,
        le=300,
        unit="seconds",
    )
    cost_cache_ttl_seconds: float = tunable(
        300.0,
        why="Cost Management is slow and should not be hit on every panel refresh.",
        ge=0,
        le=3600,
        unit="seconds",
    )
    projection_cache_ttl_seconds: float = tunable(
        5.0,
        why=(
            "Collapse rapid repeated graph projections while keeping the verdict "
            "seconds-fresh."
        ),
        ge=0,
        le=30,
        unit="seconds",
    )
    self_heal_refetch_seconds: float = tunable(
        90.0,
        why=(
            "Back off transient dashboard self-heal refetches to reduce repeated "
            "read egress."
        ),
        gt=0,
        le=600,
        unit="seconds",
    )
    github_repository: str = tunable(
        "yury-gurevich/trading-agents",
        why="Repository whose main image-build workflow defines deploy currency.",
    )
    github_image_workflow: str = tunable(
        "build-images.yml",
        why="Workflow that publishes the main fleet images compared with DeployRecord.",
    )
    github_timeout_seconds: float = tunable(
        10.0,
        why="Bound the single read-only GitHub build lookup.",
        gt=0,
        le=30,
        unit="seconds",
    )
    log_tail_default: int = tunable(
        200,
        why="Match the operator-requested useful default log excerpt.",
        ge=1,
        le=1000,
        unit="rows",
    )
    log_tail_max: int = tunable(
        500,
        why="Keep interactive Log Analytics reads and responses bounded.",
        ge=1,
        le=5000,
        unit="rows",
    )
    bundle_log_tail: int = tunable(
        40,
        why="Give the repair bundle useful evidence without multiplying its size.",
        ge=1,
        le=500,
        unit="rows per container",
    )
    master_window_start_utc: str = tunable(
        "22:25", why="Matches daily-master-window in infra/deploy-agents.ps1."
    )
    agent_window_start_utc: str = tunable(
        "22:30", why="Matches daily-agent-window in infra/deploy-agents.ps1."
    )
    window_end_utc: str = tunable(
        "00:30", why="Matches the cron scale-window end in deployment."
    )
    dispatcher_fire_utc: str = tunable(
        "22:30", why="Matches dispatcher-cron in infra/deploy-agents.ps1."
    )
