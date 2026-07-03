"""Seed Key Vault script tests.

Agent: tooling
Role: verify CLI helpers preserve the live vault target and filter behavior.
External I/O: reads temp JSON files only.
"""

from __future__ import annotations

import json

from scripts import seed_key_vault

from agents.master.vault_seed import SeedEntry, SeedOutcome


def test_filter_entries_limits_by_kv_name() -> None:
    entries = (
        SeedEntry("one", "ONE", "p"),
        SeedEntry("two", "TWO", "p"),
    )
    assert seed_key_vault._filter_entries(entries, ("two",)) == (entries[1],)
    assert seed_key_vault._filter_entries(entries, ()) == entries


def test_default_vault_url_prefers_env_then_local_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MASTER_KEY_VAULT_URL", "https://env-vault.example")
    assert seed_key_vault._default_vault_url() == "https://env-vault.example"

    monkeypatch.delenv("MASTER_KEY_VAULT_URL")
    local = tmp_path / "key-vault.local.json"
    local.write_text(json.dumps({"vault_url": "https://file-vault.example"}))
    monkeypatch.setattr(seed_key_vault, "_LOCAL_VAULT", local)
    assert seed_key_vault._default_vault_url() == "https://file-vault.example"


def test_dry_run_writer_does_not_require_azure() -> None:
    writer = seed_key_vault._writer("https://vault.example", apply=False)
    writer.set_secret("ignored", "value")
    assert writer.get_secret("ignored") == ""


def test_service_principal_aliases_drive_azure_sdk_env(monkeypatch) -> None:
    fake_secret = "sp-secret"  # noqa: S105  # pragma: allowlist secret
    monkeypatch.setenv("AZURE_TENANT_ID", "old-tenant")
    monkeypatch.setenv("AZURE_SP_TENANT_ID", "vault-tenant")
    monkeypatch.setenv("AZURE_SP_CLIENT_ID", "sp-client")
    monkeypatch.setenv("AZURE_SP_CLIENT_SECRET", fake_secret)
    seed_key_vault._prefer_sp_credential_env()
    assert seed_key_vault.os.environ["AZURE_TENANT_ID"] == "vault-tenant"
    assert seed_key_vault.os.environ["AZURE_CLIENT_ID"] == "sp-client"
    assert seed_key_vault.os.environ["AZURE_CLIENT_SECRET"] == fake_secret


def test_print_summary_includes_resource_group(capsys) -> None:
    seed_key_vault._print_summary(
        (SeedOutcome("one", "seeded", "ok"),),
        apply=False,
        vault_url="https://vault.example",
    )
    out = capsys.readouterr().out
    assert "resource_group: trading-agents" in out
    assert "one" in out
