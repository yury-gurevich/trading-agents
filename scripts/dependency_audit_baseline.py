"""The dependency advisories this repo accepts, and the premises behind each.

Agent: tooling
Role: name every advisory the dependency audit tolerates, with the facts that
      must stay true for it to keep tolerating them.
External I/O: none; exports immutable checker constants.

An acceptance here is not a mute button. Every field below is re-measured on each
run by `scripts/check_dependency_audit.py`, and the gate fails the moment one of
them stops holding - a fix ships, the advisory disappears, or the package becomes
reachable from a deployed container.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AcceptedAdvisory:
    """An advisory the audit tolerates, plus the premises that justify it."""

    vuln_id: str
    package: str
    aliases: tuple[str, ...]
    decision: str
    reason: str
    retire_when: str
    # The sole optional extra that pulls the package in. The audit fails if any
    # Dockerfile installs it, because then the "reaches no container" premise is
    # false. None means the acceptance rests on other grounds only.
    reachable_only_via_extra: str | None = None


ACCEPTED: tuple[AcceptedAdvisory, ...] = (
    AcceptedAdvisory(
        vuln_id="PYSEC-2026-2447",
        package="diskcache",
        aliases=("GHSA-w8v5-vhqr-4h9v", "CVE-2025-69872"),
        decision="DL-184",
        reason=(
            "no fix release exists, nothing imports dspy, and the attack needs "
            "write access to the cache directory - which is code execution already"
        ),
        retire_when=(
            "diskcache publishes a fixed release, or the optimizer extra is dropped"
        ),
        reachable_only_via_extra="optimizer",
    ),
)
