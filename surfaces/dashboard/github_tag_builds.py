"""Select GitHub image builds whose logs published a requested tag.

Agent: surfaces
Role: filter successful image workflow evidence by published Docker tag.
External I/O: none directly; uses the injected reader's GitHub helpers.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING
from urllib.parse import quote
from zipfile import BadZipFile, ZipFile

from surfaces.dashboard.github_builds import GitHubReadError, MainImageBuild

if TYPE_CHECKING:
    from surfaces.dashboard.github_builds import GitHubActionsReader


_DOCKER_TAG_CHARACTERS = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")


def image_builds_for_tag(
    reader: GitHubActionsReader, tag: str, git_sha: str | None = None
) -> tuple[MainImageBuild, ...]:
    """Return successful qualifying builds whose logs declare the requested tag."""
    clean_tag = tag.removeprefix(":").strip()
    if not clean_tag:
        raise GitHubReadError("GitHub image tag is required")
    clean_sha = git_sha.strip().lower() if git_sha is not None else None
    runs = (
        reader._successful_main_image_runs(per_page=100)
        if clean_sha is None
        else reader._successful_image_runs(per_page=100, git_sha=clean_sha, branch=None)
    )
    matches = tuple(
        build
        for row in runs
        for build in (reader._build_from_run(row),)
        if clean_sha is None or _run_commit_is_on_main(reader, row, build.git_sha)
        if run_log_mentions_tag(reader, build.run_id, clean_tag)
    )
    if not matches and clean_sha is not None:
        return ()
    if not matches:
        raise GitHubReadError(
            f"GitHub returned no successful image build for tag {clean_tag}"
        )
    return matches


def run_log_mentions_tag(reader: GitHubActionsReader, run_id: int, tag: str) -> bool:
    """Return whether any workflow log names the requested image tag."""
    url = (
        f"https://api.github.com/repos/{reader._repository}/actions/runs/{run_id}/logs"
    )
    raw = reader._read_bytes(url)
    marker = f"trading-agents-master:{tag}".encode()
    try:
        with ZipFile(BytesIO(raw)) as archive:
            return any(
                _contains_complete_tag(archive.read(name), marker)
                for name in archive.namelist()
            )
    except BadZipFile:
        raise GitHubReadError("GitHub build log response was incomplete") from None


def _run_commit_is_on_main(
    reader: GitHubActionsReader, row: dict[str, object], git_sha: str
) -> bool:
    if row.get("head_branch") == "main":
        return True
    url = (
        f"https://api.github.com/repos/{reader._repository}/compare/main..."
        f"{quote(git_sha, safe='')}"
    )
    payload = reader._read_json(url)
    ahead_by = payload.get("ahead_by")
    if isinstance(ahead_by, bool) or not isinstance(ahead_by, int):
        raise GitHubReadError("GitHub commit ancestry response was incomplete")
    return ahead_by == 0


def _contains_complete_tag(log: bytes, marker: bytes) -> bool:
    start = log.find(marker)
    while start >= 0:
        end = start + len(marker)
        if end == len(log) or log[end] not in _DOCKER_TAG_CHARACTERS:
            return True
        start = log.find(marker, end)
    return False
