"""Trading master composition-root tests.

Agent: orchestration
Role: verify trading pack remediation data and safe executors wire into MasterAgent.
External I/O: reads local orchestration pack JSON fixtures.
"""

from __future__ import annotations

from agents.master.key_vault import CachingSecretStore, NullSecretStore
from kernel import InMemoryGraphStore
from orchestration.master_serve import build_trading_master


def test_build_trading_master_wires_remediation_pack_and_executor() -> None:
    store = CachingSecretStore(NullSecretStore(), ttl_minutes=0)
    master = build_trading_master(InMemoryGraphStore(), secret_store=store)
    assert "refetch-from-key-vault" in master._remediation_executors
    assert {item.name for item in master._remediation_catalogue} == {
        "refetch-from-key-vault",
        "resume-instance",
        "rotate-credential",
        "recreate-instance",
        "pause-and-escalate",
    }
    assert "Never invent an action" in master._remediation_system_prompt
