"""Credential-probe classification tests.

Agent: master
Role: prove pack-declared credential failure classes are preserved for readiness.
External I/O: none (injected HTTP transports).
"""

from __future__ import annotations

import json

from agents.master.credential_probes import parse_credential_tests
from agents.master.credential_result import CredentialCheckResult
from agents.master.tests.credential_probe_testkit import http_declaration


def _declaration() -> str:
    return json.dumps(
        {
            "provider": [
                {
                    "name": "provider-key",
                    "kind": "http_status",
                    "url": "https://example.invalid/models",
                    "expected_statuses": [200],
                    "credential_failure_statuses": [401, 402],
                }
            ]
        }
    )


def test_listed_credential_failure_status_is_unrecoverable() -> None:
    """MST-FAIL-05: a listed 4xx is an unrecoverable credential failure."""
    (credential_test,) = parse_credential_tests(
        _declaration(), http_transport=lambda _request: 402
    )

    result = credential_test.run({})

    assert isinstance(result, CredentialCheckResult)
    assert (result.status, result.reason) == (
        "credential_failure",
        "unrecoverable:http_402",
    )


def test_unlisted_credential_failure_status_is_unexpected() -> None:
    """MST-FAIL-05: an unlisted 4xx is an unexpected credential failure."""
    (credential_test,) = parse_credential_tests(
        _declaration(), http_transport=lambda _request: 418
    )

    result = credential_test.run({})

    assert isinstance(result, CredentialCheckResult)
    assert (result.status, result.reason) == (
        "credential_failure",
        "unexpected:http_418",
    )


def test_server_error_stays_a_transient_credential_failure() -> None:
    """MST-FAIL-05: a 5xx stays a transient credential transport failure."""
    (credential_test,) = parse_credential_tests(
        http_declaration(), http_transport=lambda _request: 503
    )

    result = credential_test.run({"PROVIDER_LLM_KEY": "sentinel"})

    assert isinstance(result, CredentialCheckResult)
    assert (result.status, result.reason) == ("transport_failure", "http_503")
