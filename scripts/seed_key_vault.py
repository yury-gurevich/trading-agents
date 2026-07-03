"""Seed Azure Key Vault from .env after live credential checks.

Agent: tooling
Role: wire trading seed manifest/probes into the master vault seeding mechanism.
External I/O: filesystem, optional Azure Key Vault writes, live credential probes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from collections.abc import Iterable

    from agents.master.key_vault import VaultWriter
    from agents.master.vault_seed import SeedEntry, SeedOutcome

_ROOT = Path(__file__).resolve().parents[1]
_PACKS = _ROOT / "orchestration" / "packs"
_DEFAULT_MANIFEST = _PACKS / "trading_vault_seed.json"
_DEFAULT_ENV = _ROOT / ".env"
_LOCAL_VAULT = _ROOT / "infra" / "key-vault.local.json"
_RESOURCE_GROUP = "trading-agents"

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@dataclass
class _DryRunWriter:
    """No-op writer used when dry-run has no vault URL."""

    def get_secret(self, _name: str) -> str:
        """Return no secrets; dry-run never reads Key Vault."""
        return ""

    def set_secret(self, _name: str, _value: str) -> None:
        """Ignore writes; seed_vault does not call this during dry-run."""

    def delete_secret(self, _name: str) -> None:
        """Ignore deletes; dry-run never deletes Key Vault secrets."""


def main(argv: list[str] | None = None) -> int:
    """Run the seed command and return a process status code."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    args = _parser().parse_args(argv)
    load_dotenv(args.env_file)
    from agents.master.vault_seed import load_seed_manifest, seed_vault
    from orchestration.packs.trading_vault_probes import PROBES

    _prefer_sp_credential_env()
    entries = load_seed_manifest(str(args.manifest))
    selected = _filter_entries(entries, args.only)
    writer = _writer(args.vault_url, apply=args.apply)
    outcomes = seed_vault(
        selected,
        dict(os.environ),
        PROBES,
        writer,
        apply=args.apply,
    )
    _print_summary(outcomes, apply=args.apply, vault_url=args.vault_url)
    return 1 if any(outcome.status == "rejected" for outcome in outcomes) else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="seed Key Vault after live checks")
    parser.add_argument("--apply", action="store_true", help="write verified secrets")
    parser.add_argument("--vault-url", default=_default_vault_url())
    parser.add_argument("--env-file", type=Path, default=_DEFAULT_ENV)
    parser.add_argument("--manifest", type=Path, default=_DEFAULT_MANIFEST)
    parser.add_argument("--only", nargs="*", default=(), help="limit to kv_name(s)")
    return parser


def _filter_entries(
    entries: Iterable[SeedEntry], only: Iterable[str]
) -> tuple[SeedEntry, ...]:
    selected = frozenset(only)
    if not selected:
        return tuple(entries)
    return tuple(entry for entry in entries if entry.kv_name in selected)


def _writer(vault_url: str, *, apply: bool) -> VaultWriter:
    if not apply:
        return _DryRunWriter()
    if not vault_url:
        raise SystemExit("MASTER_KEY_VAULT_URL or --vault-url is required for --apply")
    from agents.master.key_vault import AzureKeyVaultSecretStore

    return AzureKeyVaultSecretStore(vault_url)


def _default_vault_url() -> str:
    url = os.environ.get("MASTER_KEY_VAULT_URL", "")
    if url or not _LOCAL_VAULT.exists():
        return url
    try:
        raw = json.loads(_LOCAL_VAULT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    return str(raw.get("vault_url", ""))


def _prefer_sp_credential_env() -> None:
    """Let explicit local service-principal aliases drive Azure SDK auth."""
    aliases = {
        "AZURE_SP_CLIENT_ID": "AZURE_CLIENT_ID",
        "AZURE_SP_CLIENT_SECRET": "AZURE_CLIENT_SECRET",  # pragma: allowlist secret
        "AZURE_SP_TENANT_ID": "AZURE_TENANT_ID",
    }
    if all(os.environ.get(source) for source in aliases):
        for source, target in aliases.items():
            os.environ[target] = os.environ[source]


def _print_summary(
    outcomes: Iterable[SeedOutcome], *, apply: bool, vault_url: str
) -> None:
    mode = "apply" if apply else "dry-run"
    print(f"KEY VAULT SEED ({mode})")
    print(f"  resource_group: {_RESOURCE_GROUP}")
    print(f"  vault_url: {vault_url or '<none>'}")
    print("")
    print(f"{'kv_name':<28} {'status':<9} message")
    print("-" * 72)
    for outcome in outcomes:
        print(f"{outcome.kv_name:<28} {outcome.status:<9} {outcome.message}")


if __name__ == "__main__":
    raise SystemExit(main())
