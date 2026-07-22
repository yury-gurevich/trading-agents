"""Pure logic for the fleet credential-delivery audit.

Agent: tooling
Role: classify each target's delivered credential as scoped, shared, or broken.
External I/O: none.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import urlsplit

from scripts.pg_role_plan import AGENTS, TABLE_PRIVILEGES, TABLES, db_role

FLEET_TARGETS = tuple(agent for agent in AGENTS if agent != "ops")
DISPATCHER_JOB = "dispatcher-cron"
REQUIRED_PRIVILEGES = tuple(
    f"{table}:{privilege}" for table in TABLES for privilege in TABLE_PRIVILEGES
)

SCOPED = "scoped"
DEGRADED = "scoped-degraded"
SHARED = "shared"
CROSS_WIRED = "cross-wired"
UNREACHABLE = "unreachable"
MISSING = "missing"

_FAILING = (SHARED, CROSS_WIRED, UNREACHABLE, MISSING, DEGRADED)


@dataclass(frozen=True)
class TargetAudit:
    """One target's delivered-credential verdict. Holds no secret material."""

    target: str
    expected_role: str
    observed_role: str
    verdict: str
    missing_privileges: tuple[str, ...] = ()
    note: str = ""


def container_name(target: str) -> str:
    """Return the Container App name for *target* (the job has its own name)."""
    if target == "dispatcher":
        return DISPATCHER_JOB
    return target.replace("_", "-")


def expected_role(target: str) -> str:
    """Return the database role *target* must connect as."""
    return db_role(target)


def role_of_dsn(dsn: str) -> str:
    """Return the username in *dsn*, never the credential itself."""
    if not dsn:
        return ""
    try:
        return urlsplit(dsn).username or ""
    except ValueError:
        return ""


def classify(
    target: str,
    observed_role: str,
    *,
    reachable: bool,
    privileges: tuple[str, ...] = (),
    note: str = "",
) -> TargetAudit:
    """Judge one target's delivered credential without any live I/O."""
    wanted = expected_role(target)
    verdict, absent = _verdict(wanted, observed_role, reachable, privileges)
    return TargetAudit(
        target=target,
        expected_role=wanted,
        observed_role=observed_role,
        verdict=verdict,
        missing_privileges=absent,
        note=note,
    )


def _verdict(
    wanted: str, observed: str, reachable: bool, privileges: tuple[str, ...]
) -> tuple[str, tuple[str, ...]]:
    """Return the verdict and any missing privileges for one target."""
    if not observed:
        return MISSING, ()
    if observed != wanted:
        known = {db_role(other) for other in FLEET_TARGETS}
        return (CROSS_WIRED if observed in known else SHARED), ()
    if not reachable:
        return UNREACHABLE, ()
    absent = tuple(p for p in REQUIRED_PRIVILEGES if p not in privileges)
    if absent:
        return DEGRADED, absent
    return SCOPED, ()


def summarize(audits: tuple[TargetAudit, ...]) -> dict[str, object]:
    """Return non-secret totals plus the list of targets needing attention."""
    counts: dict[str, int] = {}
    for audit in audits:
        counts[audit.verdict] = counts.get(audit.verdict, 0) + 1
    failing = tuple(a.target for a in audits if a.verdict in _FAILING)
    return {
        "targets": len(audits),
        "verdicts": dict(sorted(counts.items())),
        "failing": list(failing),
        "ok": not failing and bool(audits),
    }


def audit_json(audits: tuple[TargetAudit, ...]) -> str:
    """Render the audit as printable JSON containing no credential material."""
    return json.dumps(
        {
            "summary": summarize(audits),
            "targets": [
                {
                    "target": a.target,
                    "expected_role": a.expected_role,
                    "observed_role": a.observed_role,
                    "verdict": a.verdict,
                    "missing_privileges": list(a.missing_privileges),
                    "note": a.note,
                }
                for a in audits
            ],
        },
        indent=2,
        sort_keys=True,
    )
