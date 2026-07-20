"""Lazy package export regressions.

Agent: tooling
Role: keep package-level convenience imports working after row-J closure slimming.
External I/O: none.
"""

from __future__ import annotations


def test_orchestration_package_exports_still_resolve() -> None:
    from orchestration import Dispatcher, RunResult, RunScheduler, RunTrigger

    assert Dispatcher.__name__ == "Dispatcher"
    assert RunScheduler.__name__ == "RunScheduler"
    assert RunResult.__name__ == "RunResult"
    assert RunTrigger.__name__ == "RunTrigger"


def test_provider_and_scanner_package_exports_still_resolve() -> None:
    from agents.provider import ProviderAgent
    from agents.scanner import ScannerAgent

    assert ProviderAgent.__name__ == "ProviderAgent"
    assert ScannerAgent.__name__ == "ScannerAgent"
