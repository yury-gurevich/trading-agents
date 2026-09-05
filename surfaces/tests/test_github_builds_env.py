"""GitHub Actions reader environment binding tests.

Agent: surfaces
Role: prove token binding and sanitized GitHub read failures.
External I/O: none; GitHub reads are injected fakes.
"""

from __future__ import annotations

from urllib.error import URLError

import pytest

from surfaces.dashboard.github_builds import (
    GitHubActionsReader,
    GitHubReadError,
    build_github_reader,
)
from surfaces.tests.test_dashboard_costs import _settings


def test_github_reader_binds_only_when_token_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert build_github_reader(_settings(), {}) is None
    assert (
        build_github_reader(
            _settings(),
            {"GITHUB_TOKEN": "token"},  # pragma: allowlist secret
        )
        is not None
    )
    monkeypatch.setenv("GITHUB_TOKEN", "token")  # pragma: allowlist secret
    assert build_github_reader(_settings()) is not None


def test_github_reader_sanitizes_latest_transport_failure() -> None:
    reader = GitHubActionsReader(
        token="token",  # noqa: S106  # pragma: allowlist secret
        repository="owner/repo",
        workflow="build-images.yml",
        timeout=3.0,
        opener=lambda *_args, **_kwargs: (_ for _ in ()).throw(URLError("secret")),
    )

    with pytest.raises(GitHubReadError, match="transport") as caught:
        reader.latest_main_image_build()
    assert "secret" not in str(caught.value)
