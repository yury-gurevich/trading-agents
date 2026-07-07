"""Shared helpers for trading vault seed probes.

Agent: orchestration
Role: keep live probe mechanics small and testable.
External I/O: optional HTTPS requests.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.master.vault_seed import ProbeResult
from contracts.common import Window

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


def required(env: Mapping[str, str], *names: str) -> str:
    """Return the first present env value, or raise for a failed probe result."""
    for name in names:
        value = env.get(name, "")
        if value:
            return value
    raise ValueError(f"missing {'/'.join(names)}")


def run_probe(name: str, check: Callable[[], bool]) -> ProbeResult:
    """Convert probe exceptions and falsey checks into fail-closed results."""
    try:
        ok = check()
    except Exception as exc:
        return ProbeResult(False, f"{name} probe failed: {type(exc).__name__}")
    return ProbeResult(ok, f"{name} probe {'passed' if ok else 'returned no data'}")


def probe_window() -> Window:
    """Return a recent broad market-data window resilient to weekends/holidays."""
    end = datetime.now(UTC).date()
    return Window(start=end - timedelta(days=14), end=end)


def http_json(request: urllib.request.Request) -> object:
    """Read a JSON HTTPS response for an auth probe."""
    with urllib.request.urlopen(request, timeout=15) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))
