"""GitHub Actions image-build reader tests.

Agent: surfaces
Role: prove GitHub build evidence parsing and tag-specific lookup.
External I/O: none; GitHub reads are injected fakes.
"""

from __future__ import annotations

import json
from io import BytesIO
from typing import TYPE_CHECKING, Any
from urllib.error import URLError
from zipfile import ZipFile

import pytest

from surfaces.dashboard.github_builds import (
    GitHubActionsReader,
    GitHubReadError,
    MainImageBuild,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from urllib.request import Request


class _Response(BytesIO):
    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def _log_zip(text: str) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("build.txt", text)
    return output.getvalue()


def test_github_reader_parses_latest_successful_main_build() -> None:
    seen: dict[str, object] = {}

    def open_fake(request: Request, *, timeout: float) -> _Response:
        seen.update(url=request.full_url, timeout=timeout)
        payload = {
            "workflow_runs": [
                {"head_sha": "abc", "id": 7, "html_url": "https://example/run/7"}
            ]
        }
        return _Response(json.dumps(payload).encode())

    reader = _reader(open_fake)
    build = reader.latest_main_image_build()

    assert build == MainImageBuild("abc", 7, "https://example/run/7")
    assert "branch=main&status=success&per_page=1" in str(seen["url"])
    assert seen["timeout"] == 3.0


def test_github_reader_finds_successful_builds_that_published_tag() -> None:
    seen: list[str] = []

    def open_fake(request: Request, *, timeout: float) -> _Response:
        assert timeout == 3.0
        url = request.full_url
        seen.append(url)
        if "head_sha=s194-sha" in url:
            return _runs_response(("s194-sha", 7, "https://example/run/7"))
        if "runs?branch=main&status=success&per_page=100" in url:
            return _runs_response(
                ("newer-sha", 8, "https://example/run/8"),
                ("s194-sha", 7, "https://example/run/7"),
            )
        if url.endswith("/8/logs"):
            return _Response(_log_zip("ghcr.io/owner/trading-agents-master:s195"))
        return _Response(_log_zip("ghcr.io/owner/trading-agents-master:s194"))

    assert _reader(open_fake).image_builds_for_tag("s194") == (
        MainImageBuild("s194-sha", 7, "https://example/run/7"),
    )
    assert _reader(open_fake).image_builds_for_tag("s194", git_sha="s194-sha") == (
        MainImageBuild("s194-sha", 7, "https://example/run/7"),
    )
    assert seen == [
        "https://api.github.com/repos/owner/repo/actions/workflows/"
        "build-images.yml/runs?branch=main&status=success&per_page=100",
        "https://api.github.com/repos/owner/repo/actions/runs/8/logs",
        "https://api.github.com/repos/owner/repo/actions/runs/7/logs",
        "https://api.github.com/repos/owner/repo/actions/workflows/"
        "build-images.yml/runs?branch=main&status=success&per_page=100"
        "&head_sha=s194-sha",
        "https://api.github.com/repos/owner/repo/actions/runs/7/logs",
    ]


def test_github_reader_rejects_missing_tagged_build_evidence() -> None:
    def open_fake(request: Request, *, timeout: float) -> _Response:
        if "runs?branch=main&status=success&per_page=100" in request.full_url:
            return _runs_response(("abc", 7, "https://example/run/7"))
        return _Response(_log_zip("ghcr.io/owner/trading-agents-master:s123"))

    with pytest.raises(GitHubReadError, match="tag s194"):
        _reader(open_fake).image_builds_for_tag("s194")


def test_github_reader_returns_empty_for_missing_candidate_build() -> None:
    seen: list[str] = []

    def open_fake(request: Request, *, timeout: float) -> _Response:
        del timeout
        seen.append(request.full_url)
        if "head_sha=missing-sha" in request.full_url:
            return _runs_response()
        return pytest.fail("unexpected log read")

    assert _reader(open_fake).image_builds_for_tag("s194", git_sha="missing-sha") == ()
    assert seen == [
        "https://api.github.com/repos/owner/repo/actions/workflows/"
        "build-images.yml/runs?branch=main&status=success&per_page=100"
        "&head_sha=missing-sha",
    ]


def test_github_reader_requires_a_tag_before_reading() -> None:
    reader = _reader(lambda *_args, **_kwargs: pytest.fail("unexpected GitHub read"))

    with pytest.raises(GitHubReadError, match="tag is required"):
        reader.image_builds_for_tag(": ")


def test_github_reader_rejects_unreadable_build_logs() -> None:
    def open_fake(request: Request, *, timeout: float) -> _Response:
        if "runs?branch=main&status=success&per_page=100" in request.full_url:
            return _runs_response(("abc", 7, "https://example/run/7"))
        return _Response(b"not a zip")

    with pytest.raises(GitHubReadError, match="log response"):
        _reader(open_fake).image_builds_for_tag("s194")


def test_github_reader_sanitizes_log_transport_failures() -> None:
    def open_fake(request: Request, *, timeout: float) -> _Response:
        if "runs?branch=main&status=success&per_page=100" in request.full_url:
            return _runs_response(("abc", 7, "https://example/run/7"))
        raise URLError("secret")

    with pytest.raises(GitHubReadError, match="transport") as caught:
        _reader(open_fake).image_builds_for_tag("s194")
    assert "secret" not in str(caught.value)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"workflow_runs": {}}, "no successful main image build"),
        ({"workflow_runs": []}, "no successful main image build"),
        ({"workflow_runs": ["bad"]}, "no successful main image build"),
        ({"workflow_runs": [{"head_sha": "abc"}]}, "response was incomplete"),
    ],
)
def test_github_reader_rejects_missing_build_evidence(
    payload: dict[str, object], message: str
) -> None:
    reader = _reader(lambda *_args, **_kwargs: _Response(json.dumps(payload).encode()))

    with pytest.raises(GitHubReadError, match=message):
        reader.latest_main_image_build()


def _runs_response(*rows: tuple[str, int, str]) -> _Response:
    payload = {
        "workflow_runs": [
            {"head_sha": sha, "id": run_id, "html_url": url}
            for sha, run_id, url in rows
        ]
    }
    return _Response(json.dumps(payload).encode())


def _reader(opener: Callable[..., Any]) -> GitHubActionsReader:
    return GitHubActionsReader(
        token="token",  # noqa: S106  # pragma: allowlist secret
        repository="owner/repo",
        workflow="build-images.yml",
        timeout=3.0,
        opener=opener,
    )
