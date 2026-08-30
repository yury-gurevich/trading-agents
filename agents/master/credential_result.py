"""Credential probe result values.

Agent: master
Role: define sanitized credential-test outcomes shared by loaders and runners.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CheckStatus = Literal["passed", "credential_failure", "transport_failure"]


@dataclass(frozen=True)
class CredentialCheckResult:
    """Sanitized result of one credential test."""

    status: CheckStatus
    reason: str = ""


type CheckResult = bool | CredentialCheckResult


def credential_passed() -> CredentialCheckResult:
    """Return a successful credential-test result."""
    return CredentialCheckResult("passed")


def credential_failed(reason: str = "") -> CredentialCheckResult:
    """Return a credential-rejection result."""
    return CredentialCheckResult("credential_failure", reason)


def credential_transport_failed(reason: str) -> CredentialCheckResult:
    """Return a non-blocking transport-failure result."""
    return CredentialCheckResult("transport_failure", reason)


def coerce_result(value: CheckResult) -> CredentialCheckResult:
    """Convert the legacy bool result form to a structured probe result."""
    if isinstance(value, CredentialCheckResult):
        return value
    return credential_passed() if value else credential_failed()
