"""Credential loading for dependency probes.

Agent: probes
Role: read real creds from the local .env (v1 .env as the documented fallback).
External I/O: reads .env files.
"""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_LOCAL = _ROOT / ".env"
_V1 = _ROOT.parent / "traiding-system" / ".env"


def _parse(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def load_creds() -> dict[str, str]:
    """Local .env wins; v1 .env fills any gaps (the creds-first project rule)."""
    merged = _parse(_V1)
    merged.update(_parse(_LOCAL))
    return merged
