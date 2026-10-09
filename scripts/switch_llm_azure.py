"""Narrow Azure calls and configuration-preservation comparisons.

Agent: tooling
Role: parse only Azure stdout and compare every non-provider configuration field.
External I/O: Azure CLI subprocesses through an injected runner.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

type Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


class SwitchOperationError(RuntimeError):
    """A credential-free error constructed by this command's Azure boundary."""


def run_az(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run the resolved CLI without a shell; keep progress/error streams separate."""
    executable = shutil.which("az")
    if not executable:
        raise SwitchOperationError("Azure CLI executable az is unavailable")
    return subprocess.run(  # noqa: S603 - resolved az, argument list, no shell
        [executable, *args], capture_output=True, text=True, check=False
    )


class Azure:
    """The command's sole Azure boundary; every call requests JSON stdout."""

    def __init__(
        self, runner: Runner, resource_group: str, subscription: str | None
    ) -> None:
        self.runner = runner
        self.resource_group = resource_group
        self.subscription = subscription

    def call(
        self, app: str, operation: list[str], extra: list[str] | None = None
    ) -> object:
        """Return JSON stdout or raise an app-scoped, credential-free error."""
        args = [
            "containerapp",
            *operation,
            "--name",
            app,
            "--resource-group",
            self.resource_group,
        ]
        if self.subscription:
            args += ["--subscription", self.subscription]
        args += [*(extra or []), "-o", "json"]
        result = self.runner(args)
        if result.returncode:
            raise SwitchOperationError(
                f"{app} {' '.join(operation)} failed (exit {result.returncode})"
            )
        try:
            return json.loads(result.stdout)
        except ValueError as exc:
            raise SwitchOperationError(
                f"{app} {' '.join(operation)} returned invalid JSON"
            ) from exc

    def snapshot(self, app: str) -> dict[str, Any]:
        """Read one complete app configuration for durable evidence."""
        value = self.call(app, ["show"])
        if not isinstance(value, dict):
            raise SwitchOperationError(f"{app} show returned no app object")
        return value

    def has_replicas(self, app: str) -> bool:
        """Count replicas, never infer them from properties.runningStatus."""
        value = self.call(app, ["replica", "list"])
        if not isinstance(value, list):
            raise SwitchOperationError(f"{app} replica list returned no list")
        return bool(value)

    def update(self, app: str, key: str, provider: str) -> None:
        """Change exactly one declared environment variable."""
        self.call(app, ["update"], ["--set-env-vars", f"{key}={provider}"])


def live_value(snapshot: dict[str, Any], key: str) -> str:
    """Read a plain provider value; absent/secretref values count as differing."""
    containers = snapshot["properties"]["template"]["containers"]
    values = [
        entry.get("value", "")
        for container in containers
        for entry in container.get("env", [])
        if entry["name"] == key
    ]
    return (
        str(values[0]) if values and all(value == values[0] for value in values) else ""
    )


def preserved_fields(snapshot: dict[str, Any], key: str) -> dict[str, Any]:
    """Project every field D8 promises equal, removing only the declared key."""
    props = snapshot["properties"]
    template = props["template"]
    configuration = props["configuration"]
    containers = deepcopy(template["containers"])
    for container in containers:
        container["env"] = sorted(
            (entry for entry in container.get("env", []) if entry["name"] != key),
            key=lambda entry: entry["name"],
        )
    return {
        "properties.template.containers": containers,
        "properties.template.scale": template.get("scale"),
        "properties.configuration.secrets": sorted(
            entry["name"] for entry in configuration.get("secrets", [])
        ),
        "properties.configuration.ingress": configuration.get("ingress"),
        "properties.configuration.registries": configuration.get("registries"),
        "identity": snapshot.get("identity"),
    }


def changed_fields(
    before: dict[str, Any], after: dict[str, Any], key: str
) -> list[str]:
    """Name each protected field that moved between snapshots."""
    old = preserved_fields(before, key)
    new = preserved_fields(after, key)
    return [field for field in old if old[field] != new[field]]
