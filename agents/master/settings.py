"""Master bootstrap agent settings — replay window, EHLO backlog and fleet tunables.

Agent: master
Role: own master's lifecycle and handshake defaults.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from kernel import AgentSettings, tunable


class MasterSettings(AgentSettings):
    """Settings for the master bootstrap lifecycle agent."""

    llm_provider: str = tunable(
        "",
        why="Declared vendor selects probes and keys; empty keeps every declaration.",
    )

    handshake_timeout_2_seconds: float = tunable(
        300.0,
        why=(
            "Master's replay window: seconds a resent EHLO (same boot id and type) "
            "gets the first ACTIVATE back instead of a second activation; must be >= "
            "the kernel's EHLO budget (ehlo_budget_seconds) so every resend replays."
        ),
        ge=30.0,
        le=600.0,
        unit="seconds",
    )
    ehlo_listen_backlog: int = tunable(
        64,
        why=(
            "Listen backlog of master's EHLO server; one activation wave is the 15 "
            "agent types waking together, and 64 holds four waves of resends."
        ),
        ge=16,
        le=1024,
    )
    grant_policy_path: str = tunable(
        "",
        why=(
            "Filesystem path to the pack's grant-policy JSON; empty = the substrate "
            "ships no grants, so every agent type is unknown until a pack supplies one."
        ),
    )
    secret_map_path: str = tunable(
        "",
        why=(
            "Filesystem path to the pack's secret-map JSON; empty = the substrate "
            "entitles no agent type to any secret until a pack supplies the table."
        ),
    )
    grant_policy_b64: str = tunable(
        "",
        why=(
            "Base64-encoded grant-policy JSON injected at deploy time (cloud); takes "
            "precedence over grant_policy_path. Keeps the master image pack-agnostic."
        ),
    )
    secret_map_b64: str = tunable(
        "",
        why=(
            "Base64-encoded secret-map JSON injected at deploy time (cloud); takes "
            "precedence over secret_map_path. Keeps the master image pack-agnostic."
        ),
    )
    credential_tests_path: str = tunable(
        "",
        why=(
            "Filesystem path to the pack's credential-test JSON; empty = no "
            "activation credential tests unless base64 pack data is supplied."
        ),
    )
    credential_tests_b64: str = tunable(
        "",
        why=(
            "Base64-encoded credential-test JSON injected at deploy time (cloud); "
            "takes precedence over credential_tests_path."
        ),
    )
    credential_pass_cache_ttl_minutes: int = tunable(
        5,
        why=(
            "Minutes a costly credential-test pass remains fresh during an "
            "activation wave (0 = never expires)."
        ),
        ge=0,
        le=60,
        unit="minutes",
    )
    fleet_preflight_interval_minutes: int = tunable(
        60,
        why=(
            "Minutes between master-owned whole-fleet readiness checks; bounded so "
            "credential failures are detected promptly without repeated probe cost."
        ),
        ge=5,
        le=240,
        unit="minutes",
    )

    remediation_mode: str = tunable(
        "manual",
        why=(
            "How a credential-test failure is handled (DL-36): 'manual' = refuse + "
            "escalate to a human; 'automatic' = allow ONE auto remediation shot then "
            "force manual. The auto remediation itself is a later piece (C/D)."
        ),
    )
    auto_remediation_scope: str = tunable(
        "safe_only",
        why=(
            "Auto-remediation boundary after the LLM selects a bounded catalogue "
            "plan: 'safe_only' allows only non-destructive remediations to be "
            "auto-eligible; 'all' allows any catalogue remediation to be "
            "auto-eligible. Still gated by remediation_mode='automatic'."
        ),
    )
    max_auto_remediation_attempts: int = tunable(
        1,
        why=(
            "Maximum automatic remediation executor runs for the same failure "
            "signature before forcing human review. Default is one shot."
        ),
        ge=0,
        le=3,
    )

    secret_cache_ttl_minutes: int = tunable(
        5,
        why=(
            "Minutes the master caches a fetched Key Vault secret for repeated "
            "references (0 = never expires). Operator dials: 3 / 5 / 10 / 0."
        ),
        ge=0,
        le=60,
        unit="minutes",
    )

    model_config = SettingsConfigDict(env_prefix="MASTER_", frozen=True)
