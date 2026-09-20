"""Telegram Key Vault seed manifest contract tests.

Agent: orchestration
Role: keep dispatcher Telegram credentials seedable before deployment.
External I/O: reads the checked-in manifest only.
"""

from __future__ import annotations

import json
from pathlib import Path

from orchestration.packs import trading_vault_probes as probes


def test_telegram_seed_entries_share_the_telegram_probe() -> None:
    """S219: dispatcher Telegram secrets can be seeded into Key Vault together."""
    entries = json.loads(
        Path("orchestration/packs/trading_vault_seed.json").read_text(encoding="utf-8")
    )
    telegram_entries = {
        entry["kv_name"]: entry
        for entry in entries
        if entry["kv_name"].startswith("telegram-")
    }

    assert set(telegram_entries) == {"telegram-bot-token", "telegram-chat-id"}
    assert {entry["env_var"] for entry in telegram_entries.values()} == {
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    }
    assert {entry["probe"] for entry in telegram_entries.values()} == {"telegram"}
    assert "telegram" in probes.PROBES
