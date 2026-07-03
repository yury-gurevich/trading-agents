"""Fail-closed Key Vault seeding mechanism.

Agent: master
Role: verify candidate secrets with injected probes before writing them.
External I/O: delegated to injected probes and VaultWriter only.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from agents.master.key_vault import VaultWriter

SeedStatus = Literal["seeded", "rejected", "skipped"]
Probe = Callable[[Mapping[str, str]], "ProbeResult"]


@dataclass(frozen=True)
class ProbeResult:
    """Result of one live credential working-check."""

    ok: bool
    message: str


@dataclass(frozen=True)
class SeedEntry:
    """One allowlisted secret to seed from an env var after a named probe passes."""

    kv_name: str
    env_var: str
    probe: str


@dataclass(frozen=True)
class SeedOutcome:
    """Operator-facing result for one seed entry."""

    kv_name: str
    status: SeedStatus
    message: str


class _Writer(Protocol):
    def set_secret(self, name: str, value: str) -> None:
        """Write one verified secret."""
        ...  # pragma: no cover - protocol declaration only.


def seed_vault(
    entries: Sequence[SeedEntry],
    env: Mapping[str, str],
    probes: Mapping[str, Probe],
    writer: VaultWriter | _Writer,
    *,
    apply: bool,
) -> tuple[SeedOutcome, ...]:
    """Verify and maybe seed each entry; never write unverified candidates."""
    outcomes: list[SeedOutcome] = []
    for entry in entries:
        value = env.get(entry.env_var, "")
        if not value:
            outcomes.append(_outcome(entry, "skipped", "env var is empty or missing"))
            continue
        probe = probes.get(entry.probe)
        if probe is None:
            outcomes.append(_outcome(entry, "rejected", "unknown probe"))
            continue
        try:
            result = probe(env)
        except Exception as exc:
            outcomes.append(
                _outcome(entry, "rejected", f"probe raised {type(exc).__name__}")
            )
            continue
        if not result.ok:
            outcomes.append(_outcome(entry, "rejected", result.message))
            continue
        if not apply:
            outcomes.append(_outcome(entry, "seeded", f"would seed: {result.message}"))
            continue
        try:
            writer.set_secret(entry.kv_name, value)
        except Exception as exc:
            outcomes.append(
                _outcome(entry, "rejected", f"write failed: {type(exc).__name__}")
            )
            continue
        outcomes.append(_outcome(entry, "seeded", result.message))
    return tuple(outcomes)


def parse_seed_manifest(text: str) -> tuple[SeedEntry, ...]:
    """Parse a seed manifest JSON array into validated entries."""
    raw: object = json.loads(text)
    if not isinstance(raw, list):
        raise ValueError("seed manifest must be a JSON array")
    entries: list[SeedEntry] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("seed manifest entries must be JSON objects")
        kv_name = item.get("kv_name")
        env_var = item.get("env_var")
        probe = item.get("probe")
        if not (
            isinstance(kv_name, str)
            and isinstance(env_var, str)
            and isinstance(probe, str)
            and kv_name
            and env_var
            and probe
        ):
            raise ValueError("seed entries need non-empty kv_name, env_var, probe")
        if kv_name in seen:
            raise ValueError(f"duplicate seed entry {kv_name!r}")
        seen.add(kv_name)
        entries.append(SeedEntry(kv_name, env_var, probe))
    return tuple(entries)


def load_seed_manifest(path: str) -> tuple[SeedEntry, ...]:
    """Load seed entries from a JSON file."""
    return parse_seed_manifest(Path(path).read_text(encoding="utf-8"))


def _outcome(entry: SeedEntry, status: SeedStatus, message: str) -> SeedOutcome:
    return SeedOutcome(entry.kv_name, status, message)
