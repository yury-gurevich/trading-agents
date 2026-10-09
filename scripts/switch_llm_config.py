"""Read and validate the fleet's declared LLM provider.

Agent: tooling
Role: own offline switch inputs, CLI bounds and evidence-path validation.
External I/O: committed pack JSON and evidence directory paths.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from kernel import AgentSettings, tunable
from kernel.llm_factory import KEY_ENV


class SwitchSettings(AgentSettings):
    """Bounded graph-proof polling defaults, overridable on the command line."""

    poll_seconds: float = tunable(
        30.0, why="Poll one fleet proof every 30 seconds.", gt=0
    )
    wait_seconds: float = tunable(
        900.0, why="Stop waiting after a bounded fifteen minutes.", ge=0
    )


@dataclass(frozen=True)
class LlmPack:
    """The provider and apply-ordered app environment keys."""

    provider: str
    apps: dict[str, str]
    probes: dict[str, dict[str, frozenset[str]]]


def load_pack(root: Path) -> LlmPack:
    """Validate provider and target keys, reading vendor probe names as data."""
    packs = root / "orchestration/packs"
    raw = json.loads((packs / "trading_llm.json").read_text(encoding="utf-8"))
    provider = raw["provider"]
    apps = raw["apps"]
    if provider not in KEY_ENV:
        raise ValueError(f"unknown declared provider {provider!r}")
    if not isinstance(apps, dict) or not apps or next(iter(apps)) != "master":
        raise ValueError("LLM apps must be an ordered map with master first")
    if not all(
        isinstance(app, str) and isinstance(key, str) and key.endswith("LLM_PROVIDER")
        for app, key in apps.items()
    ):
        raise ValueError("invalid LLM app environment key")
    declaration = json.loads(
        (packs / "trading_credential_tests.json").read_text(encoding="utf-8")
    )
    probes: dict[str, dict[str, frozenset[str]]] = {}
    for app, entries in declaration.items():
        probes[app] = {}
        for vendor in KEY_ENV:
            probes[app][vendor] = frozenset(
                entry["name"]
                for entry in entries
                if entry.get("llm_provider") == vendor
            )
    for app in apps:
        if app != "master" and not probes.get(app, {}).get(provider):
            raise ValueError(f"{app} has no declared {provider} probe")
    return LlmPack(provider, apps, probes)


def evidence_directory(value: str, root: Path) -> Path:
    """Refuse evidence files inside the repository, including resolved symlinks."""
    if not value:
        raise ValueError("--apply requires --evidence-dir outside the repository")
    path = Path(value).resolve()
    if path.is_relative_to(root.resolve()):
        raise ValueError("--evidence-dir must be outside the repository")
    return path


def utc_timestamp(value: str) -> datetime:
    """Require an aware UTC ISO timestamp for proof resumption."""
    at = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if at.tzinfo is None or at.utcoffset() != UTC.utcoffset(at):
        raise ValueError("--prove-since requires a UTC ISO timestamp")
    return at.astimezone(UTC)
