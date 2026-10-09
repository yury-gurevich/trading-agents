"""Select the declared vendor's probes and credential entitlements once.

Agent: master
Role: reject invalid declarations before handing any vendor credential over.
External I/O: none; pure selection over injected pack data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kernel.llm_factory import KEY_ENV

if TYPE_CHECKING:
    from agents.master.credential_test import CredentialTest
    from agents.master.secret_map import SecretMap


def select_llm_provider(
    provider: str,
    tests: tuple[CredentialTest, ...],
    secret_map: SecretMap | None,
) -> tuple[tuple[CredentialTest, ...], SecretMap | None]:
    """Validate tags, then keep only the selected vendor's probes and key."""
    if provider and provider not in KEY_ENV:
        raise ValueError(f"unknown MASTER_LLM_PROVIDER {provider!r}")
    for test in tests:
        if test.llm_provider and test.llm_provider not in KEY_ENV:
            raise ValueError(f"unknown probe llm_provider {test.llm_provider!r}")
    if not provider:
        return tests, secret_map
    selected = tuple(test for test in tests if test.llm_provider in ("", provider))
    other_keys = {env for vendor, env in KEY_ENV.items() if vendor != provider}
    secrets = (
        {
            agent_type: [(kv, env) for kv, env in pairs if env not in other_keys]
            for agent_type, pairs in secret_map.items()
        }
        if secret_map is not None
        else None
    )
    for agent_type, pairs in (secrets or {}).items():
        if any(env == KEY_ENV[provider] for _, env in pairs) and not any(
            test.llm_provider == provider
            and (not test.agent_types or agent_type in test.agent_types)
            for test in selected
        ):
            raise ValueError(f"{agent_type} granted {provider} key without its probe")
    return selected, secrets
