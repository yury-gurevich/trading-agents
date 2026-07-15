"""Deploy-currency and GitHub build evidence tests.

Agent: surfaces
Role: prove current/behind/unverified without tag-shape inference.
External I/O: none; GitHub and Azure reads are injected fakes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from io import BytesIO
from typing import TYPE_CHECKING, Any, cast
from urllib.error import URLError

import pytest

from kernel import InMemoryGraphStore
from orchestration.deploy_record import record_deploy
from surfaces.dashboard.github_builds import (
    GitHubActionsReader,
    GitHubReadError,
    MainImageBuild,
    build_github_reader,
)
from surfaces.dashboard.projections_currency import deploy_currency_projection
from surfaces.tests.test_dashboard_costs import _settings

if TYPE_CHECKING:
    from urllib.request import Request


class _BuildReader:
    def __init__(self, sha: str = "main-sha", *, fail: bool = False) -> None:
        self.sha = sha
        self.fail = fail

    def latest_main_image_build(self) -> MainImageBuild:
        if self.fail:
            raise GitHubReadError("GitHub build read failed (test)")
        return MainImageBuild(self.sha, 42, "https://github.example/build/42")


def _containers(*tags: str) -> list[dict[str, Any]]:
    return [
        {"name": f"app-{index}", "image": f"repo/app:{tag}", "image_tag": tag}
        for index, tag in enumerate(tags)
    ]


def _record(graph: InMemoryGraphStore, *, sha: str = "main-sha") -> None:
    record_deploy(
        graph,
        tag="s123",
        git_sha=sha,
        actor="operator",
        deployed_at=datetime(2026, 7, 14, tzinfo=UTC),
    )


def test_currency_current_and_both_behind_comparisons() -> None:
    graph = InMemoryGraphStore()
    _record(graph)

    current = deploy_currency_projection(
        graph, _containers("s123", "s123"), _BuildReader(), azure_verified=True
    )
    mixed = deploy_currency_projection(
        graph, _containers("s123", "s121"), _BuildReader(), azure_verified=True
    )
    old_sha = deploy_currency_projection(
        graph,
        _containers("s123"),
        _BuildReader("new-main-sha"),
        azure_verified=True,
    )

    assert current["status"] == "current"
    assert mixed["status"] == "behind"
    assert old_sha["status"] == "behind"
    evidence = cast("dict[str, object]", old_sha["evidence"])
    assert evidence["fleet_matches_record"] is True
    assert evidence["main_matches_record"] is False


@pytest.mark.parametrize("case", ["azure", "record", "token", "read"])
def test_currency_unverified_when_any_evidence_is_unavailable(case: str) -> None:
    graph = InMemoryGraphStore()
    if case != "record":
        _record(graph)
    reader = None if case == "token" else _BuildReader(fail=case == "read")
    result = deploy_currency_projection(
        graph, _containers("s123"), reader, azure_verified=case != "azure"
    )
    assert result["status"] == "unverified"


class _Response(BytesIO):
    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


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

    reader = GitHubActionsReader(
        token="token",  # noqa: S106  # pragma: allowlist secret
        repository="owner/repo",
        workflow="build-images.yml",
        timeout=3.0,
        opener=open_fake,
    )
    build = reader.latest_main_image_build()

    assert build == MainImageBuild("abc", 7, "https://example/run/7")
    assert "branch=main&status=success&per_page=1" in str(seen["url"])
    assert seen["timeout"] == 3.0


def test_github_reader_absent_token_and_sanitized_failures() -> None:
    assert build_github_reader(_settings(), {}) is None
    assert (
        build_github_reader(
            _settings(),
            {"GITHUB_TOKEN": "token"},  # pragma: allowlist secret
        )
        is not None
    )
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


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"workflow_runs": []}, "no successful main image build"),
        ({"workflow_runs": [{"head_sha": "abc"}]}, "response was incomplete"),
    ],
)
def test_github_reader_rejects_missing_build_evidence(
    payload: dict[str, object], message: str
) -> None:
    reader = GitHubActionsReader(
        token="token",  # noqa: S106  # pragma: allowlist secret
        repository="owner/repo",
        workflow="build-images.yml",
        timeout=3.0,
        opener=lambda *_args, **_kwargs: _Response(json.dumps(payload).encode()),
    )
    with pytest.raises(GitHubReadError, match=message):
        reader.latest_main_image_build()


def test_github_reader_uses_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "token")  # pragma: allowlist secret
    assert build_github_reader(_settings()) is not None
