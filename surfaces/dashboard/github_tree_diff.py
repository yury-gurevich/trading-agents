"""Name the runtime files whose content differs between two commits.

Agent: surfaces
Role: prove whether main changed anything a fleet image runs since a deploy.
External I/O: none directly; uses the injected reader's GitHub helpers.
"""

from __future__ import annotations

import binascii
from base64 import b64decode
from functools import lru_cache
from typing import TYPE_CHECKING
from urllib.parse import quote

from surfaces.dashboard.github_builds import GitHubReadError
from surfaces.dashboard.image_paths import (
    VERSIONED_FILES,
    runs_in_image,
    without_project_version,
)

if TYPE_CHECKING:
    from surfaces.dashboard.github_builds import GitHubActionsReader


# Commits are immutable, so a comparison never needs to be read twice.
@lru_cache(maxsize=4)
def runtime_changes(
    reader: GitHubActionsReader, base_sha: str, head_sha: str
) -> tuple[str, ...]:
    """Return runtime paths that differ, ignoring a version-label-only bump."""
    base = _runtime_blobs(reader, base_sha)
    head = _runtime_blobs(reader, head_sha)
    changed = sorted(
        path for path in base.keys() | head.keys() if base.get(path) != head.get(path)
    )
    return tuple(
        path
        for path in changed
        if not (
            path in VERSIONED_FILES
            and path in base
            and path in head
            and _same_except_version(reader, base[path], head[path])
        )
    )


def _runtime_blobs(reader: GitHubActionsReader, sha: str) -> dict[str, str]:
    url = (
        f"https://api.github.com/repos/{reader._repository}/git/trees/"
        f"{quote(sha, safe='')}?recursive=1"
    )
    payload = reader._read_json(url)
    entries = payload.get("tree")
    if payload.get("truncated") is not False or not isinstance(entries, list):
        raise GitHubReadError("GitHub file listing was incomplete")
    return {
        str(entry["path"]): str(entry["sha"])
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("type") == "blob"
        and isinstance(entry.get("sha"), str)
        and runs_in_image(str(entry.get("path", "")))
    }


def _same_except_version(
    reader: GitHubActionsReader, base_blob: str, head_blob: str
) -> bool:
    base = without_project_version(_blob_text(reader, base_blob))
    return base == without_project_version(_blob_text(reader, head_blob))


def _blob_text(reader: GitHubActionsReader, blob_sha: str) -> str:
    url = (
        f"https://api.github.com/repos/{reader._repository}/git/blobs/"
        f"{quote(blob_sha, safe='')}"
    )
    payload = reader._read_json(url)
    content = payload.get("content")
    if payload.get("encoding") != "base64" or not isinstance(content, str):
        raise GitHubReadError("GitHub file content was incomplete")
    try:
        return b64decode(content).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError):
        raise GitHubReadError("GitHub file content was incomplete") from None
