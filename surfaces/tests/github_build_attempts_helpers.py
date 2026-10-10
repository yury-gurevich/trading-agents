"""Attempt-specific GitHub responses with an exact archive-request trace.

Agent: surfaces
Role: supply offline build-run, ancestry and per-attempt archive evidence.
External I/O: none; the opener serves only in-memory responses.
"""

from __future__ import annotations

import json
from io import BytesIO
from typing import TYPE_CHECKING
from zipfile import ZipFile

from surfaces.dashboard.github_builds import GitHubActionsReader, MainImageBuild

if TYPE_CHECKING:
    from urllib.request import Request


SHA = "s267-commit"
RUN_ID = 7
RUN_URL = "https://example/run/7"
BUILD = MainImageBuild(SHA, RUN_ID, RUN_URL)
TAG_LOG = "ghcr.io/owner/trading-agents-master:s259"
OTHER_LOG = "ghcr.io/owner/trading-agents-scanner:s259"
MISSING = object()
_BASE = "https://api.github.com/repos/owner/repo/actions/runs/7/"


def _archive(text: str) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("scan.txt", OTHER_LOG)
        archive.writestr("master.txt", text)
    return output.getvalue()


class AttemptGitHub:
    """Serve distinct archives by exact URL, recording each attempted read."""

    def __init__(
        self,
        logs: dict[int, str | bytes | Exception],
        *,
        count: object = MISSING,
        branch: str = "main",
        ahead_by: object = 0,
    ) -> None:
        self.archives: list[str] = []
        self.urls: list[str] = []
        self.ahead_by = ahead_by
        self.row: dict[str, object] = {
            "id": RUN_ID,
            "head_sha": SHA,
            "head_branch": branch,
            "html_url": RUN_URL,
        }
        if count is not MISSING:
            self.row["run_attempt"] = count
        self.payloads = {
            f"attempts/{attempt}/logs": log for attempt, log in logs.items()
        }
        self.payloads["logs"] = logs[max(logs)]
        self.reader = GitHubActionsReader(
            token="",
            repository="owner/repo",
            workflow="build-images.yml",
            timeout=3.0,
            opener=self.open,
        )

    def open(self, request: Request, *, timeout: float) -> BytesIO:
        """Return a canned response; an unknown request fails the test locally."""
        assert timeout == 3.0
        url = request.full_url
        self.urls.append(url)
        if "/actions/workflows/build-images.yml/runs?" in url:
            return BytesIO(json.dumps({"workflow_runs": [self.row]}).encode())
        if f"/compare/main...{SHA}" in url:
            if isinstance(self.ahead_by, Exception):
                raise self.ahead_by
            return BytesIO(json.dumps({"ahead_by": self.ahead_by}).encode())
        assert url.startswith(_BASE), f"Unexpected GitHub request: {url}"
        path = url.removeprefix(_BASE)
        self.archives.append(path)
        assert path in self.payloads, f"Unexpected archive path: {path}"
        payload = self.payloads[path]
        if isinstance(payload, Exception):
            raise payload
        return BytesIO(_archive(payload) if isinstance(payload, str) else payload)
