"""Deploy SHA verification tests.

Agent: orchestration
Role: prove the build-SHA cross-check refuses wrong commits and degrades honestly.
External I/O: none — the checker is a fake.
"""

from __future__ import annotations

import pytest

from orchestration.deploy_verify import DeployVerifyError, verify_build_sha


class _Checker:
    """Fake GitHubBuildChecker — structurally satisfies the protocol."""

    def __init__(self, result: bool | None) -> None:
        self._result = result

    def sha_has_successful_build(self, sha: str) -> bool | None:
        _ = sha
        return self._result


def test_verify_returns_true_when_build_exists() -> None:
    """A SHA that heads a successful build run is accepted and sha_verified=True."""
    accepted = "4c8eeb0505bc65c081be3d1fe71049f7d88e0e43"  # pragma: allowlist secret
    assert verify_build_sha(accepted, _Checker(True)) is True


def test_verify_raises_when_no_build_exists() -> None:
    """A SHA with no successful build run is refused with DeployVerifyError."""
    sha = "8fbf3a41339d0a31aa9a057952fe5e6401280ac1"  # pragma: allowlist secret
    with pytest.raises(DeployVerifyError, match=sha):
        verify_build_sha(sha, _Checker(False))


def test_verify_returns_false_when_github_unreadable() -> None:
    """GitHub unreadable returns False (sha_verified=False) — honest degraded path."""
    assert verify_build_sha("abc123", _Checker(None)) is False


def test_verify_returns_false_when_no_checker() -> None:
    """Absent GITHUB_TOKEN means no checker; returns False for sha_verified."""
    assert verify_build_sha("abc123", None) is False


def test_verify_error_message_names_the_given_sha() -> None:
    """The refusal error names the SHA so the operator sees what was wrong."""
    sha = "deadbeef00000000000000000000000000000000"
    with pytest.raises(DeployVerifyError, match=sha):
        verify_build_sha(sha, _Checker(False))
