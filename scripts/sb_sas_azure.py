"""Azure CLI operations for scoped Service Bus SAS provisioning.

Agent: tooling
Role: idempotently apply topic authorization rules and Key Vault secrets.
External I/O: Azure CLI and Key Vault; command output is suppressed for secrets.
"""

from __future__ import annotations

import json

from scripts.sb_sas_cli import az_cli, base_args, rule_args
from scripts.sb_sas_kv import set_secret
from scripts.sb_sas_plan import (
    SasGrant,
    grants_by_target,
    primary_grant_for_target,
    target_bundle_secret_name,
    target_secret_name,
)


def provision_sas(
    grants: tuple[SasGrant, ...],
    *,
    resource_group: str,
    namespace_name: str,
    key_vault_name: str = "",
    rotate: str = "",
    ensure_topics: bool = False,
) -> dict[str, object]:
    """Create/update scoped rules, rotate if requested, and store secrets."""
    touched = 0
    for grant in _selected_grants(grants, rotate):
        if ensure_topics:
            _ensure_topic(resource_group, namespace_name, grant.topic)
        _ensure_rule(resource_group, namespace_name, grant)
        if rotate:
            _renew_primary_key(resource_group, namespace_name, grant)
        touched += 1
    if key_vault_name:
        _store_target_secrets(
            grants,
            resource_group=resource_group,
            namespace_name=namespace_name,
            key_vault_name=key_vault_name,
            target_filter=rotate,
        )
    return {"targets": _target_count(grants, rotate), "rules": touched}


def _selected_grants(
    grants: tuple[SasGrant, ...], target_filter: str
) -> tuple[SasGrant, ...]:
    return tuple(
        grant for grant in grants if not target_filter or grant.target == target_filter
    )


def _target_count(grants: tuple[SasGrant, ...], target_filter: str) -> int:
    return len({grant.target for grant in _selected_grants(grants, target_filter)})


def _ensure_topic(resource_group: str, namespace_name: str, topic: str) -> None:
    base = base_args(resource_group, namespace_name)
    if az_cli(["servicebus", "topic", "show", *base, "--name", topic], check=False):
        return
    az_cli(["servicebus", "topic", "create", *base, "--name", topic, "-o", "none"])


def _ensure_rule(resource_group: str, namespace_name: str, grant: SasGrant) -> None:
    base = rule_args(resource_group, namespace_name, grant)
    exists = az_cli(
        ["servicebus", "topic", "authorization-rule", "show", *base, "-o", "none"],
        check=False,
    )
    command = "update" if exists else "create"
    az_cli(
        [
            "servicebus",
            "topic",
            "authorization-rule",
            command,
            *base,
            "--rights",
            *grant.rights,
            "-o",
            "none",
        ]
    )


def _renew_primary_key(
    resource_group: str, namespace_name: str, grant: SasGrant
) -> None:
    az_cli(
        [
            "servicebus",
            "topic",
            "authorization-rule",
            "keys",
            "renew",
            *rule_args(resource_group, namespace_name, grant),
            "--key",
            "PrimaryKey",
            "-o",
            "none",
        ]
    )


def _store_target_secrets(
    grants: tuple[SasGrant, ...],
    *,
    resource_group: str,
    namespace_name: str,
    key_vault_name: str,
    target_filter: str,
) -> None:
    for target, target_grants in grants_by_target(grants).items():
        if target_filter and target != target_filter:
            continue
        bundle = _connection_bundle(resource_group, namespace_name, target_grants)
        set_secret(
            key_vault_name,
            target_bundle_secret_name(target),
            json.dumps(bundle),
        )
        primary = primary_grant_for_target(target, grants)
        if primary is not None:
            set_secret(
                key_vault_name,
                target_secret_name(target),
                bundle[primary.topic]["connection_string"],
            )


def _connection_bundle(
    resource_group: str, namespace_name: str, grants: tuple[SasGrant, ...]
) -> dict[str, dict[str, object]]:
    return {
        grant.topic: {
            "rights": list(grant.rights),
            "connection_string": _connection_string(
                resource_group, namespace_name, grant
            ),
        }
        for grant in grants
    }


def _connection_string(
    resource_group: str, namespace_name: str, grant: SasGrant
) -> str:
    return az_cli(
        [
            "servicebus",
            "topic",
            "authorization-rule",
            "keys",
            "list",
            *rule_args(resource_group, namespace_name, grant),
            "--query",
            "primaryConnectionString",
            "-o",
            "tsv",
        ],
        capture=True,
    ).strip()
