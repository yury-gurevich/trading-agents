"""Tests for GitHubActionsReader.sha_has_successful_build.

Agent: surfaces
Role: prove the existence-and-identity SHA check queries correctly and degrades.
External I/O: none; the opener is a fake.
"""

from __future__ import annotations

import json
from io import BytesIO
from typing import TYPE_CHECKING
from urllib.error import URLError

import pytest

from surfaces.dashboard.github_builds import GitHubActionsReader

if TYPE_CHECKING:
    from urllib.request import Request


class _Response(BytesIO):
    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def _reader(opener: object) -> GitHubActionsReader:
    return GitHubActionsReader(
        token="token",  # noqa: S106  # pragma: allowlist secret
        repository="owner/repo",
        workflow="build-images.yml",
        timeout=3.0,
        opener=opener,  # type: ignore[arg-type]
    )


def test_sha_has_successful_build_returns_true_and_uses_head_sha_filter() -> None:
    """Returns True when a run is found; URL carries head_sha and status=success."""
    seen: dict[str, object] = {}
    payload = {"workflow_runs": [{"head_sha": "abc123", "id": 9, "html_url": "..."}]}

    def open_fake(request: Request, *, timeout: float) -> _Response:
        seen.update(url=request.full_url, timeout=timeout)
        return _Response(json.dumps(payload).encode())

    result = _reader(open_fake).sha_has_successful_build("abc123")

    assert result is True
    url = str(seen["url"])
    assert "head_sha=abc123" in url
    assert "status=success" in url


def test_sha_has_successful_build_returns_false_when_no_runs_found() -> None:
    """Returns False when the workflow_runs list is empty (SHA was never built)."""
    payload: dict[str, object] = {"workflow_runs": []}
    opener = lambda *_a, **_kw: _Response(json.dumps(payload).encode())  # noqa: E731
    assert _reader(opener).sha_has_successful_build("abc") is False


@pytest.mark.parametrize(
    "exc",
    [URLError("fail"), TimeoutError(), ValueError("bad json")],
    ids=["url-error", "timeout", "bad-json"],
)
def test_sha_has_successful_build_returns_none_on_read_error(exc: Exception) -> None:
    """Returns None (GitHub unreadable) for any transport or parse error."""
    opener = lambda *_a, **_kw: (_ for _ in ()).throw(exc)  # noqa: E731
    assert _reader(opener).sha_has_successful_build("abc") is None


def test_sha_has_successful_build_returns_none_on_malformed_payload() -> None:
    """Returns None when the response has no workflow_runs key."""
    payload = {"unexpected": "shape"}
    opener = lambda *_a, **_kw: _Response(json.dumps(payload).encode())  # noqa: E731
    assert _reader(opener).sha_has_successful_build("abc") is None
