"""Trading master composition root.

Agent: orchestration
Role: wire trading pack remediation data into the otherwise pack-neutral master.
External I/O: reads orchestration pack JSON fixtures when building the agent.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from agents.master.agent import MasterAgent
from agents.master.key_vault import NullSecretStore
from agents.master.remediation import load_remediations
from agents.master.remediation_execution import RefetchFromKeyVaultExecutor
from agents.master.remediation_gate import load_prompt_artifact
from agents.master.settings import MasterSettings

if TYPE_CHECKING:
    from agents.master.credential_test import CredentialTest, PassCache
    from agents.master.grants import GrantPolicy
    from agents.master.key_vault import SecretStore
    from agents.master.secret_map import SecretMap
    from kernel import GraphStore, LLMClient

_PACKS = Path(__file__).resolve().parent / "packs"
_REMEDIATIONS = _PACKS / "trading_remediations.json"
_PROMPT = _PACKS / "trading_remediation_prompt.json"


def build_trading_master(
    graph: GraphStore,
    *,
    settings: MasterSettings | None = None,
    secret_store: SecretStore | None = None,
    grant_policy: GrantPolicy | None = None,
    secret_map: SecretMap | None = None,
    credential_tests: tuple[CredentialTest, ...] = (),
    pass_cache: PassCache | None = None,
    remediation_llm: LLMClient | None = None,
) -> MasterAgent:
    """Build a master wired with trading remediation catalogue and safe executors."""
    store = secret_store or NullSecretStore()
    prompt = load_prompt_artifact(str(_PROMPT))
    refetch = RefetchFromKeyVaultExecutor(store)
    return MasterAgent(
        graph=graph,
        settings=settings or MasterSettings(),
        secret_store=store,
        grant_policy=grant_policy,
        secret_map=secret_map,
        credential_tests=credential_tests,
        pass_cache=pass_cache,
        remediation_llm=remediation_llm,
        remediation_catalogue=load_remediations(str(_REMEDIATIONS)),
        remediation_system_prompt=prompt.system_prompt,
        remediation_executors={refetch.name: refetch},
    )
