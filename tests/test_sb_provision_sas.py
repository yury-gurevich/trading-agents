"""Service Bus SAS provisioner tests.

Agent: tooling
Role: prove Azure command planning and secret-safe CLI boundaries.
External I/O: subprocess only for missing-env import smoke; no live Azure.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from scripts import sb_provision_sas as cli
from scripts import sb_sas_azure as azure
from scripts.sb_sas_plan import SasGrant


def test_provisioner_script_direct_execution_imports_helpers() -> None:
    env = os.environ.copy()
    env.pop("SERVICEBUS_SAS_RESOURCE_GROUP", None)
    env.pop("SERVICEBUS_SAS_NAMESPACE", None)

    completed = subprocess.run(
        [sys.executable, "scripts/sb_provision_sas.py", "--dry-run"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "SERVICEBUS_SAS_RESOURCE_GROUP" in completed.stderr
    assert "ModuleNotFoundError" not in completed.stderr


def test_dry_run_prints_non_secret_rule_summary(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "plan_from_repo",
        lambda _root: (SasGrant("scanner", "run.trigger", ("Listen",)),),
    )

    code = cli.main(
        [
            "--resource-group",
            "rg",
            "--namespace-name",
            "bus",
            "--dry-run",
        ]
    )

    assert code == 0
    out = capsys.readouterr().out
    assert '"rule": "ta-scanner"' in out
    assert "connection_string" not in out


def test_provision_sas_creates_rules_and_sets_key_vault_secrets(monkeypatch) -> None:
    calls: list[tuple[tuple[str, ...], bool, bool]] = []
    secrets: list[tuple[str, str, str]] = []

    def fake_az(args, *, capture=False, check=True):
        calls.append((tuple(args), capture, check))
        if capture:
            topic = args[args.index("--topic-name") + 1]
            return f"conn-for-{topic}"
        return ""

    monkeypatch.setattr(azure, "az_cli", fake_az)
    monkeypatch.setattr(
        azure,
        "set_secret",
        lambda vault, name, value: secrets.append((vault, name, value)),
    )
    grants = (
        SasGrant("scanner", "run.trigger", ("Listen",)),
        SasGrant("scanner", "scan.candidates.ready", ("Send",)),
    )

    summary = azure.provision_sas(
        grants,
        resource_group="rg",
        namespace_name="bus",
        key_vault_name="kv",
        ensure_topics=True,
    )

    assert summary == {"targets": 1, "rules": 2}
    assert any(call[0][:3] == ("servicebus", "topic", "create") for call in calls)
    assert any(
        call[0][:5]
        == ("servicebus", "topic", "authorization-rule", "create", "--resource-group")
        for call in calls
    )
    assert len(secrets) == 2
    assert (
        "kv",
        "servicebus-connection-string-scanner",
        "conn-for-run.trigger",
    ) in secrets
    assert any(
        secret[1] == "servicebus-connection-strings-scanner" for secret in secrets
    )
