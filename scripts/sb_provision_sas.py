"""Provision per-target Azure Service Bus SAS identities.

Agent: tooling
Role: CLI wrapper for measured Service Bus SAS planning and provisioning.
External I/O: environment, Azure CLI, and optional Key Vault writes; no key output.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.sb_sas_azure import provision_sas  # noqa: E402
from scripts.sb_sas_plan import (  # noqa: E402
    SasGrant,
    _normalize_target,
    authorization_rule_name,
    plan_from_repo,
)

RESOURCE_GROUP_ENV = "SERVICEBUS_SAS_RESOURCE_GROUP"
NAMESPACE_ENV = "SERVICEBUS_SAS_NAMESPACE"
KEY_VAULT_ENV = "SERVICEBUS_SAS_KEY_VAULT"
KEY_VAULT_FALLBACK_ENV = "POSTGRES_ROLE_KEY_VAULT"


def main(argv: list[str] | None = None) -> int:
    """Run the provisioner and return a process exit code."""
    args = _parser().parse_args(argv)
    resource_group = args.resource_group or os.environ.get(RESOURCE_GROUP_ENV, "")
    namespace_name = args.namespace_name or os.environ.get(NAMESPACE_ENV, "")
    key_vault = args.key_vault_name or os.environ.get(KEY_VAULT_ENV, "")
    key_vault = key_vault or os.environ.get(KEY_VAULT_FALLBACK_ENV, "")
    if not resource_group or not namespace_name:
        sys.stderr.write(f"error {RESOURCE_GROUP_ENV} and {NAMESPACE_ENV} required\n")
        return 1
    try:
        rotate = _normalize_target(args.rotate) if args.rotate else ""
        grants = plan_from_repo(args.root)
        if args.dry_run:
            print(json.dumps(_dry_run(grants, rotate), sort_keys=True))
            return 0
        summary = provision_sas(
            grants,
            resource_group=resource_group,
            namespace_name=namespace_name,
            key_vault_name=key_vault,
            rotate=rotate,
            ensure_topics=args.ensure_topics,
        )
    except Exception as exc:
        sys.stderr.write(f"error sb provisioning failed: {type(exc).__name__}\n")
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="provision Service Bus SAS rules")
    parser.add_argument("--root", default=".")
    parser.add_argument("--resource-group", default="")
    parser.add_argument("--namespace-name", default="")
    parser.add_argument("--key-vault-name", default="")
    parser.add_argument("--rotate", default="", help="rotate one target identity")
    parser.add_argument("--ensure-topics", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _dry_run(grants: tuple[SasGrant, ...], rotate: str) -> dict[str, object]:
    selected = tuple(grant for grant in grants if not rotate or grant.target == rotate)
    return {
        "rotate": bool(rotate),
        "targets": sorted({grant.target for grant in selected}),
        "rules": [
            {
                "topic": grant.topic,
                "rule": authorization_rule_name(grant.target),
                "rights": list(grant.rights),
            }
            for grant in selected
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
