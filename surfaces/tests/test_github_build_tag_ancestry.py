"""GitHub image-build ancestry and exact-tag regression tests.

Agent: surfaces
Role: prove GitHub build evidence accepts merged tag builds only.
External I/O: none; GitHub reads are injected fakes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from io import BytesIO
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

from kernel import InMemoryGraphStore
from orchestration.deploy_record import record_verified_deploy
from surfaces.dashboard.github_builds import GitHubActionsReader, MainImageBuild

if TYPE_CHECKING:
    from collections.abc import Callable
    from urllib.request import Request


_S211_SHA = "7d3ff519c06fd7df9ad38da38508e41b506dbb12"  # pragma: allowlist secret


class _Response(BytesIO):
    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def test_tag_dispatched_build_of_main_ancestor_is_evidence() -> None:
    reader = _reader(_s211_opener)

    assert reader.image_builds_for_tag("s211", _S211_SHA) == (
        MainImageBuild(_S211_SHA, 35217747046, "https://example/run/35217747046"),
    )


def test_tag_dispatched_main_ancestor_records_a_deploy() -> None:
    graph = InMemoryGraphStore()

    node = record_verified_deploy(
        graph,
        tag="s211",
        git_sha=_S211_SHA,
        actor="operator",
        build_reader=_reader(_s211_opener),
        deployed_at=datetime(2026, 9, 17, 0, 0, tzinfo=UTC),
    )

    assert node.props["tag"] == "s211"
    assert node.props["git_sha"] == _S211_SHA


def test_tag_lookup_rejects_prefixes_of_published_tag() -> None:
    def open_fake(request: Request, *, timeout: float) -> _Response:
        del timeout
        if "/runs?" in request.full_url:
            return _runs_response(
                "1a6f3429a728b0348ed2059de52b535803cb3fa4",  # pragma: allowlist secret
                35336964246,
                "main",
            )
        return _Response(_log_zip("trading-agents-master:s214"))

    reader = _reader(open_fake)

    sha = "1a6f3429a728b0348ed2059de52b535803cb3fa4"  # pragma: allowlist secret
    assert reader.image_builds_for_tag("s214", sha) == (
        MainImageBuild(
            sha,
            35336964246,
            "https://example/run/35336964246",
        ),
    )
    assert reader.image_builds_for_tag("s21", sha) == ()
    assert reader.image_builds_for_tag("s2", sha) == ()


def _s211_opener(request: Request, *, timeout: float) -> _Response:
    del timeout
    url = request.full_url
    if "/runs?" in url:
        if "branch=main" in url:
            return _runs_response()
        return _runs_response(_S211_SHA, 35217747046, "v0.98.08")
    if "/compare/main..." in url:
        return _Response(json.dumps({"status": "behind", "ahead_by": 0}).encode())
    return _Response(_log_zip("trading-agents-master:s211"))


def _runs_response(
    sha: str | None = None, run_id: int = 0, branch: str = ""
) -> _Response:
    runs: list[dict[str, object]] = []
    if sha is not None:
        runs.append(
            {
                "head_sha": sha,
                "id": run_id,
                "head_branch": branch,
                "html_url": f"https://example/run/{run_id}",
            }
        )
    return _Response(json.dumps({"workflow_runs": runs}).encode())


def _log_zip(text: str) -> bytes:
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
