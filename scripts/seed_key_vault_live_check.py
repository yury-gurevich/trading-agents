"""Live evidence check for the Key Vault seeder.

Agent: tooling
Role: prove pass/write, fail/reject, and dry-run/no-write against real Key Vault.
External I/O: Azure Key Vault and the live Tiingo credential probe.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_RESOURCE_GROUP = "trading-agents"


def main(argv: list[str] | None = None) -> int:
    """Run the retained live seeder check and print JSON evidence."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description="live Key Vault seedcheck")
    parser.add_argument("--env-file", type=Path, default=_ROOT / ".env")
    parser.add_argument("--vault-url", default="")
    args = parser.parse_args(argv)

    from scripts.seed_key_vault import _default_vault_url, _prefer_sp_credential_env

    from agents.master.key_vault import AzureKeyVaultSecretStore
    from agents.master.vault_seed import SeedEntry, seed_vault
    from orchestration.packs.trading_vault_probes import PROBES

    load_dotenv(args.env_file)
    _prefer_sp_credential_env()
    vault_url = args.vault_url or _default_vault_url()
    if not vault_url:
        raise SystemExit(
            "MASTER_KEY_VAULT_URL, infra/key-vault.local.json, or --vault-url required"
        )
    env = dict(os.environ)
    if not env.get("PROVIDER_TIINGO_API_KEY"):
        raise SystemExit("PROVIDER_TIINGO_API_KEY required for live seedcheck")

    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    names = {
        "pass": f"seedcheck-tiingo-{stamp}",
        "bad": f"seedcheck-badkey-{stamp}",
        "dry": f"seedcheck-dryrun-{stamp}",
    }
    writer = AzureKeyVaultSecretStore(vault_url)
    summary: dict[str, object] = {
        "resource_group": _RESOURCE_GROUP,
        "vault_url": vault_url,
        "names": names,
    }
    try:
        pass_out = seed_vault(
            (SeedEntry(names["pass"], "PROVIDER_TIINGO_API_KEY", "tiingo"),),
            env,
            PROBES,
            writer,
            apply=True,
        )
        assert pass_out[0].status == "seeded", pass_out
        summary["pass_status"] = pass_out[0].status
        summary["pass_readback_equal"] = (
            writer.get_secret(names["pass"]) == env["PROVIDER_TIINGO_API_KEY"]
        )
        assert summary["pass_readback_equal"] is True

        bad_value = "seedcheck-invalid"  # pragma: allowlist secret
        bad_env = {**env, "PROVIDER_TIINGO_API_KEY": bad_value}
        bad_out = seed_vault(
            (SeedEntry(names["bad"], "PROVIDER_TIINGO_API_KEY", "tiingo"),),
            bad_env,
            PROBES,
            writer,
            apply=True,
        )
        assert bad_out[0].status == "rejected", bad_out
        summary["bad_status"] = bad_out[0].status
        summary["bad_absent"] = writer.get_secret(names["bad"]) == ""
        assert summary["bad_absent"] is True

        dry_out = seed_vault(
            (SeedEntry(names["dry"], "PROVIDER_TIINGO_API_KEY", "tiingo"),),
            env,
            PROBES,
            writer,
            apply=False,
        )
        assert dry_out[0].status == "seeded", dry_out
        summary["dry_status"] = dry_out[0].status
        summary["dry_absent"] = writer.get_secret(names["dry"]) == ""
        assert summary["dry_absent"] is True
    finally:
        deleted: list[str] = []
        for name in names.values():
            writer.delete_secret(name)
            deleted.append(name)
        summary["deleted"] = deleted

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
