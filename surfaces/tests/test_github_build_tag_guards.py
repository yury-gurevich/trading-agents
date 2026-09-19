"""GitHub image-build ancestry and tag-boundary guard tests.

Agent: surfaces
Role: prove GitHub build evidence fails closed outside main history.
External I/O: none; GitHub reads are injected fakes.
"""

from __future__ import annotations

import json
from email.message import Message
from io import BytesIO
from typing import TYPE_CHECKING, Any
from urllib.error import HTTPError, URLError
from zipfile import ZipFile

import pytest

from kernel import InMemoryGraphStore
from orchestration.deploy_record import (
    DeployRecordVerificationError,
    record_verified_deploy,
)
from surfaces.dashboard.github_builds import (
    GitHubActionsReader,
    GitHubReadError,
    MainImageBuild,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from urllib.request import Request


_SHA = "576ee571451a3b454a180ea1eee4c12f8889d186"  # pragma: allowlist secret


class _Response(BytesIO):
    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def test_divergent_build_is_not_deploy_evidence() -> None:
    def open_fake(request: Request, *, timeout: float) -> _Response:
        del timeout
        if "/runs?" in request.full_url:
            if "branch=main" in request.full_url:
                return _Response(b'{"workflow_runs": []}')
            return _runs_response(_SHA, 29904029290, "chore-container-smoke")
        if "/compare/" in request.full_url:
            return _Response(json.dumps({"status": "diverged", "ahead_by": 1}).encode())
        return _Response(_log_zip("trading-agents-master:smoke-test"))

    reader = _reader(open_fake)
    assert reader.image_builds_for_tag("smoke-test", _SHA) == ()
    graph = InMemoryGraphStore()
    with pytest.raises(DeployRecordVerificationError, match="build evidence"):
        record_verified_deploy(
            graph,
            tag="smoke-test",
            git_sha=_SHA,
            actor="operator",
            build_reader=reader,
        )
    assert not graph.list_nodes("DeployRecord")


@pytest.mark.parametrize(
    "comparison",
    [
        HTTPError("https://example.invalid", 404, "missing", Message(), None),
        URLError("secret transport detail"),
        {"status": "behind"},
    ],
)
def test_unreadable_or_malformed_ancestry_refuses(comparison: object) -> None:
    def open_fake(request: Request, *, timeout: float) -> _Response:
        del timeout
        if "/runs?" in request.full_url:
            return _runs_response(_SHA, 7, "release")
        if "/compare/" in request.full_url:
            if isinstance(comparison, BaseException):
                raise comparison
            return _Response(json.dumps(comparison).encode())
        return _Response(_log_zip("trading-agents-master:s215"))

    with pytest.raises(GitHubReadError) as caught:
        _reader(open_fake).image_builds_for_tag("s215", _SHA)

    assert "secret transport detail" not in str(caught.value)
    assert "example.invalid" not in str(caught.value)


def test_ancestry_uses_main_as_compare_base() -> None:
    seen: list[str] = []

    def open_fake(request: Request, *, timeout: float) -> _Response:
        del timeout
        seen.append(request.full_url)
        if "/runs?" in request.full_url:
            return _runs_response(_SHA, 7, "release")
        if "/compare/" in request.full_url:
            return _Response(json.dumps({"status": "ahead", "ahead_by": 3}).encode())
        return _Response(_log_zip("trading-agents-master:s215"))

    assert _reader(open_fake).image_builds_for_tag("s215", _SHA) == ()
    assert any(f"/compare/main...{_SHA}" in url for url in seen)


def test_non_object_json_response_refuses() -> None:
    reader = _reader(lambda *_args, **_kwargs: _Response(b"[]"))

    with pytest.raises(GitHubReadError, match="response was incomplete"):
        reader.latest_main_image_build()


@pytest.mark.parametrize(
    ("suffix", "matches"),
    [(b'"', True), (b"\n", True), (b" ", True), (b"", True), (b"-rc1", False)],
)
def test_tag_boundary_matches_only_complete_docker_tags(
    suffix: bytes, *, matches: bool
) -> None:
    def open_fake(request: Request, *, timeout: float) -> _Response:
        del timeout
        if "/runs?" in request.full_url:
            return _runs_response(_SHA, 7, "main")
        return _Response(_log_zip_bytes(b"trading-agents-master:s214" + suffix))

    result = _reader(open_fake).image_builds_for_tag("s214", _SHA)

    assert (result == (MainImageBuild(_SHA, 7, "https://example/run/7"),)) is matches


def test_main_run_skips_compare_and_url_shapes_are_preserved() -> None:
    seen: list[str] = []

    def open_fake(request: Request, *, timeout: float) -> _Response:
        del timeout
        seen.append(request.full_url)
        if "/runs?" in request.full_url:
            return _runs_response(_SHA, 7, "main")
        return _Response(_log_zip("trading-agents-master:s215"))

    reader = _reader(open_fake)
    assert reader.image_builds_for_tag("s215", _SHA)
    assert reader.image_builds_for_tag("s215")
    assert not any("/compare/" in url for url in seen)
    assert any("branch=main&status=success&per_page=100" in url for url in seen)
    assert any("status=success&per_page=100&head_sha=" in url for url in seen)


def _runs_response(sha: str, run_id: int, branch: str) -> _Response:
    return _Response(
        json.dumps(
            {
                "workflow_runs": [
                    {
                        "head_sha": sha,
                        "id": run_id,
                        "head_branch": branch,
                        "html_url": f"https://example/run/{run_id}",
                    }
                ]
            }
        ).encode()
    )


def _log_zip(text: str) -> bytes:
    return _log_zip_bytes(text.encode())


def _log_zip_bytes(text: bytes) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("build.txt", text)
    return output.getvalue()


def _reader(opener: Callable[..., Any]) -> GitHubActionsReader:
    return GitHubActionsReader(
        token="token",  # noqa: S106  # pragma: allowlist secret
        repository="owner/repo",
        workflow="build-images.yml",
        timeout=3.0,
        opener=opener,
    )
