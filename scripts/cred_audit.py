"""Audit which credential each fleet target is actually delivered.

Agent: tooling
Role: prove per-target scoped credentials are delivered, not merely wired.
External I/O: Azure CLI reads and one PostgreSQL connection per target.

Env-var wiring cannot answer this question: `postgres-flip` rewrites the *value*
of the `postgres-dsn` secret while the env var name is unchanged, so a read-only
`az containerapp show` looks identical whether the fleet holds scoped per-role
DSNs or one shared admin DSN (DL-54). This reads the delivered value, reports the
role it names, and connects as it. No credential is ever printed.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.cred_audit_azure import audit_target, bus_secret_ref  # noqa: E402
from scripts.cred_audit_plan import (  # noqa: E402
    FLEET_TARGETS,
    TargetAudit,
    audit_json,
    summarize,
)

RESOURCE_GROUP_ENV = "POSTGRES_ROLE_RESOURCE_GROUP"
DEFAULT_RESOURCE_GROUP = "trading-agents"


def main(argv: list[str] | None = None) -> int:
    """Run the audit and return a process exit code."""
    args = _parser().parse_args(argv)
    resource_group = (
        args.resource_group
        or os.environ.get(RESOURCE_GROUP_ENV)
        or DEFAULT_RESOURCE_GROUP
    )
    targets = args.target or list(FLEET_TARGETS)
    try:
        audits = tuple(_audit_all(targets, resource_group, args.check_bus))
    except Exception as exc:
        sys.stderr.write(f"error credential audit failed: {type(exc).__name__}\n")
        return 1
    print(audit_json(audits))
    ok = bool(summarize(audits)["ok"])
    if args.strict and not ok:
        sys.stderr.write("error one or more targets are not on a scoped credential\n")
        return 1
    return 0


def _audit_all(
    targets: list[str], resource_group: str, check_bus: bool
) -> list[TargetAudit]:
    audits = []
    for target in targets:
        audit = audit_target(target, resource_group)
        if check_bus:
            audit = _with_bus_note(audit, resource_group)
        audits.append(audit)
    return audits


def _with_bus_note(audit: TargetAudit, resource_group: str) -> TargetAudit:
    """Append the Service Bus secretRef name (not its value) to the note."""
    ref = bus_secret_ref(audit.target, resource_group)
    detail = f"bus secretRef: {ref or 'none'}"
    note = f"{audit.note}; {detail}" if audit.note else detail
    return TargetAudit(
        target=audit.target,
        expected_role=audit.expected_role,
        observed_role=audit.observed_role,
        verdict=audit.verdict,
        missing_privileges=audit.missing_privileges,
        note=note,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="audit delivered per-target credentials (prints no secrets)"
    )
    parser.add_argument("--resource-group", default="")
    parser.add_argument(
        "--target", action="append", help="audit one target (repeatable)"
    )
    parser.add_argument(
        "--check-bus",
        action="store_true",
        help="also report each target's Service Bus secretRef name",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 unless every target is on its own scoped role",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
