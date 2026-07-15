"""Read the newest successful main image-build fact from GitHub Actions.

Agent: surfaces
Role: provide one token-bounded, read-only GitHub evidence port.
External I/O: GitHub REST API through HTTPS.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from surfaces.dashboard.settings import DashboardSettings


class GitHubReadError(RuntimeError):
    """A sanitized GitHub read failure safe to show on the dashboard."""


@dataclass(frozen=True)
class MainImageBuild:
    """Evidence identifying the newest successful main image workflow run."""

    git_sha: str
    run_id: int
    url: str


class GitHubReader(Protocol):
    """Read-only source for the main image build used by deploy currency."""

    def latest_main_image_build(self) -> MainImageBuild:
        """Return the newest successful main build."""
        ...  # pragma: no cover - protocol declaration only.


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
        workflow = quote(self._workflow, safe="")
        url = (
            f"https://api.github.com/repos/{self._repository}/actions/workflows/"
            f"{workflow}/runs?branch=main&status=success&per_page=1"
        )
        request = Request(  # noqa: S310 - fixed GitHub HTTPS origin.
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": "2026-03-10",
            },
        )
        try:
            with self._opener(request, timeout=self._timeout) as response:
                payload = cast("dict[str, object]", json.load(response))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            code = getattr(exc, "code", "transport")
            raise GitHubReadError(f"GitHub build read failed ({code})") from None
        runs = payload.get("workflow_runs")
        if not isinstance(runs, list) or not runs or not isinstance(runs[0], dict):
            raise GitHubReadError("GitHub returned no successful main image build")
        row = runs[0]
        try:
            return MainImageBuild(
                git_sha=str(row["head_sha"]),
                run_id=int(cast("int | str", row["id"])),
                url=str(row["html_url"]),
            )
        except (KeyError, TypeError, ValueError):
            raise GitHubReadError("GitHub build response was incomplete") from None


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
