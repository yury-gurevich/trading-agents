"""Read successful main image-build facts from GitHub Actions.

Agent: surfaces
Role: provide one token-bounded, read-only GitHub evidence port.
External I/O: GitHub REST API through HTTPS.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING, Any, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from surfaces.dashboard.settings import DashboardSettings


class GitHubReadError(RuntimeError):
    """A sanitized GitHub read failure safe to show on the dashboard."""


@dataclass(frozen=True)
class MainImageBuild:
    """Evidence identifying one successful main image workflow run."""

    git_sha: str
    run_id: int
    url: str


class GitHubReader(Protocol):
    """Read-only source for the main image build used by deploy currency."""

    def latest_main_image_build(self) -> MainImageBuild:
        """Return the newest successful main build."""
        raise NotImplementedError  # pragma: no cover - protocol declaration only.

    def image_builds_for_tag(
        self, tag: str, git_sha: str | None = None
    ) -> tuple[MainImageBuild, ...]:
        """Return successful image builds that published tag."""
        raise NotImplementedError  # pragma: no cover - protocol declaration only.


class GitHubActionsReader:
    """Small GitHub REST adapter using a caller-supplied token."""

    def __init__(
        self,
        *,
        token: str,
        repository: str,
        workflow: str,
        timeout: float,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        """Bind the token, workflow coordinates, timeout, and HTTPS opener."""
        self._token = token
        self._repository = repository
        self._workflow = workflow
        self._timeout = timeout
        self._opener = opener

    def latest_main_image_build(self) -> MainImageBuild:
        """Read one successful main workflow run and return its head SHA."""
        runs = self._successful_main_image_runs(per_page=1)
        if not runs:
            raise GitHubReadError("GitHub returned no successful main image build")
        return self._build_from_run(runs[0])

    def image_builds_for_tag(
        self, tag: str, git_sha: str | None = None
    ) -> tuple[MainImageBuild, ...]:
        """Read successful main workflow runs and keep those that published tag."""
        clean_tag = tag.removeprefix(":").strip()
        if not clean_tag:
            raise GitHubReadError("GitHub image tag is required")
        clean_sha = git_sha.strip().lower() if git_sha is not None else None
        matches = tuple(
            build
            for build in (
                self._build_from_run(row)
                for row in self._successful_main_image_runs(
                    per_page=100, git_sha=clean_sha
                )
            )
            if self._run_log_mentions_tag(build.run_id, clean_tag)
        )
        if not matches and clean_sha is not None:
            return ()
        if not matches:
            raise GitHubReadError(
                f"GitHub returned no successful image build for tag {clean_tag}"
            )
        return matches

    def _successful_main_image_runs(
        self, *, per_page: int, git_sha: str | None = None
    ) -> list[dict[str, object]]:
        workflow = quote(self._workflow, safe="")
        query = {
            "branch": "main",
            "status": "success",
            "per_page": str(per_page),
        }
        if git_sha:
            query["head_sha"] = git_sha
        url = (
            f"https://api.github.com/repos/{self._repository}/actions/workflows/"
            f"{workflow}/runs?{urlencode(query)}"
        )
        payload = self._read_json(url)
        runs = payload.get("workflow_runs")
        if not isinstance(runs, list):
            raise GitHubReadError("GitHub returned no successful main image build")
        if runs and not isinstance(runs[0], dict):
            raise GitHubReadError("GitHub returned no successful main image build")
        return cast("list[dict[str, object]]", runs)

    def _read_json(self, url: str) -> dict[str, object]:
        request = self._request(url)
        try:
            with self._opener(request, timeout=self._timeout) as response:
                return cast("dict[str, object]", json.load(response))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            code = getattr(exc, "code", "transport")
            raise GitHubReadError(f"GitHub build read failed ({code})") from None

    def _read_bytes(self, url: str) -> bytes:
        request = self._request(url)
        try:
            with self._opener(request, timeout=self._timeout) as response:
                return cast("bytes", response.read())
        except (HTTPError, URLError, TimeoutError) as exc:
            code = getattr(exc, "code", "transport")
            raise GitHubReadError(f"GitHub build read failed ({code})") from None

    def _request(self, url: str) -> Request:
        return Request(  # noqa: S310  # fixed GitHub HTTPS origin.
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": "2026-03-10",
            },
        )

    def _build_from_run(self, row: dict[str, object]) -> MainImageBuild:
        try:
            return MainImageBuild(
                git_sha=str(row["head_sha"]),
                run_id=int(cast("int | str", row["id"])),
                url=str(row["html_url"]),
            )
        except (KeyError, TypeError, ValueError):
            raise GitHubReadError("GitHub build response was incomplete") from None

    def _run_log_mentions_tag(self, run_id: int, tag: str) -> bool:
        url = (
            f"https://api.github.com/repos/{self._repository}/actions/runs/"
            f"{run_id}/logs"
        )
        raw = self._read_bytes(url)
        marker = f"trading-agents-master:{tag}".encode()
        try:
            with ZipFile(BytesIO(raw)) as archive:
                return any(marker in archive.read(name) for name in archive.namelist())
        except BadZipFile:
            raise GitHubReadError("GitHub build log response was incomplete") from None


def build_github_reader(
    settings: DashboardSettings, environ: Mapping[str, str] | None = None
) -> GitHubReader | None:
    """Bind the reader only when GITHUB_TOKEN is present."""
    env = os.environ if environ is None else environ
    token = env.get("GITHUB_TOKEN", "")
    if not token:
        return None
    return GitHubActionsReader(
        token=token,
        repository=settings.github_repository,
        workflow=settings.github_image_workflow,
        timeout=settings.github_timeout_seconds,
    )
