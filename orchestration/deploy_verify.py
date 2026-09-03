"""Verify the SHA supplied to record_deploy was actually built by the image workflow.

Agent: orchestration
Role: cross-check the given commit SHA against GitHub Actions before writing a record.
External I/O: none — the GitHubBuildChecker is injected.
"""

from __future__ import annotations

from typing import Protocol


class GitHubBuildChecker(Protocol):
    """Read-only port: check whether a SHA heads a successful image-build run."""

    def sha_has_successful_build(self, sha: str) -> bool | None:
        """Return True if found, False if not found, None if GitHub is unreadable."""
        ...  # pragma: no cover - protocol declaration only.


class DeployVerifyError(RuntimeError):
    """The given SHA was not found in any successful build-images.yml run."""


def verify_build_sha(sha: str, checker: GitHubBuildChecker | None) -> bool:
    """Cross-check the SHA against GitHub Actions; return whether it was verified.

    Args:
        sha:     The commit SHA the caller intends to record.
        checker: An injected GitHub checker, or None when no token is available.

    Returns:
        True  — a successful build-images.yml run exists for the given SHA.
        False — GitHub was unreadable; caller should record with sha_verified=False.

    Raises:
        DeployVerifyError — GitHub was reachable but no successful build run exists
                            for this SHA. The caller must not write the record.
    """
    if checker is None:
        return False
    result = checker.sha_has_successful_build(sha)
    if result is None:
        return False  # GitHub unreadable — honest degraded path (DL-149 decision 3)
    if not result:
        raise DeployVerifyError(
            f"No successful build-images.yml run exists for SHA {sha!r}. "
            "Provide the commit the images were built from, not the current HEAD."
        )
    return True
