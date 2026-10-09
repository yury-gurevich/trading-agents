"""Load master's injected declarations without importing a trading pack.

Agent: master
Role: resolve base64 or file declarations for grants, secrets and probes.
External I/O: configured declaration files only.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

from agents.master.credential_probes import (
    load_credential_tests,
    parse_credential_tests,
)
from agents.master.grants import load_grant_policy, parse_grant_policy
from agents.master.secret_map import load_secret_map, parse_secret_map

if TYPE_CHECKING:
    from collections.abc import Callable

    from agents.master.credential_test import CredentialTest
    from agents.master.grants import GrantPolicy
    from agents.master.secret_map import SecretMap
    from agents.master.settings import MasterSettings


def _resolve_pack[T](
    b64: str, path: str, parse: Callable[[str], T], load: Callable[[str], T]
) -> T | None:
    """Base64 wins over a file; absent inputs leave the declaration absent."""
    if b64:
        return parse(base64.b64decode(b64).decode("utf-8"))
    if path:
        return load(path)
    return None


def load_master_packs(
    settings: MasterSettings,
) -> tuple[GrantPolicy | None, SecretMap | None, tuple[CredentialTest, ...]]:
    """Read all three declarations; provider selection follows in build_app."""
    grants = _resolve_pack(
        settings.grant_policy_b64,
        settings.grant_policy_path,
        parse_grant_policy,
        load_grant_policy,
    )
    secrets = _resolve_pack(
        settings.secret_map_b64,
        settings.secret_map_path,
        parse_secret_map,
        load_secret_map,
    )
    tests = _resolve_pack(
        settings.credential_tests_b64,
        settings.credential_tests_path,
        parse_credential_tests,
        load_credential_tests,
    )
    return grants, secrets, tests or ()
