"""Azure CLI command helpers for Service Bus SAS tooling.

Agent: tooling
Role: build and run fixed Azure CLI commands with output suppressed by default.
External I/O: Azure CLI subprocesses.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

from scripts.sb_sas_plan import SasGrant, authorization_rule_name

if TYPE_CHECKING:
    from collections.abc import Sequence

AZ_CLI_TIMEOUT_SECONDS = 120


def rule_args(resource_group: str, namespace_name: str, grant: SasGrant) -> list[str]:
    """Return common topic authorization-rule flags."""
    return [
        "--resource-group",
        resource_group,
        "--namespace-name",
        namespace_name,
        "--topic-name",
        grant.topic,
        "--name",
        authorization_rule_name(grant.target),
    ]


def base_args(resource_group: str, namespace_name: str) -> list[str]:
    """Return common Service Bus namespace flags."""
    return ["--resource-group", resource_group, "--namespace-name", namespace_name]


def az_cli(args: Sequence[str], *, capture: bool = False, check: bool = True) -> str:
    """Run Azure CLI without shell expansion or accidental secret output."""
    az = shutil.which("az")
    if not az:
        raise RuntimeError("Azure CLI not found")
    completed = subprocess.run(  # noqa: S603 - fixed az executable, no shell.
        [az, *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=AZ_CLI_TIMEOUT_SECONDS,
    )
    if check and completed.returncode != 0:
        raise RuntimeError("Azure CLI command failed")
    return completed.stdout or ""
