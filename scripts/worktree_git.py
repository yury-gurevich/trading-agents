"""Git and gh plumbing for the worktree housekeeping report.

Agent: tooling
Role: read the facts `check_worktrees.py` judges - the primary worktree, every
      worktree record, ancestry against a base, dirty-file counts and open-PR
      heads. Read-only: every call is a query; nothing is removed or written.
External I/O: subprocess (`git`, and `gh` when present for open-PR heads).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

GIT_TIMEOUT_SECONDS = 60
GH_TIMEOUT_SECONDS = 60


def git_exe() -> str:
    """Return the resolved git executable, or raise if it is not installed."""
    git = shutil.which("git")
    if not git:
        raise RuntimeError("git not found")
    return git


def git(*args: str, cwd: Path | None = None) -> str:
    """Run a git command and return its stripped stdout ('' on failure)."""
    result = subprocess.run(  # noqa: S603 - fixed git executable, no shell.
        [git_exe(), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def primary_root() -> Path:
    """Return the primary worktree's path."""
    return Path(git("rev-parse", "--path-format=absolute", "--git-common-dir")).parent


def worktrees() -> list[dict[str, str]]:
    """Parse `git worktree list --porcelain` into one record per worktree."""
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in git("worktree", "list", "--porcelain").splitlines():
        if not line:
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value or key
    if current:
        records.append(current)
    return records


def is_contained(sha: str, base: str) -> bool:
    """Return whether a commit is already an ancestor of base."""
    completed = subprocess.run(  # noqa: S603 - fixed git executable, no shell.
        [git_exe(), "merge-base", "--is-ancestor", sha, base],
        capture_output=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    return completed.returncode == 0


def dirty_count(path: Path) -> int:
    """Count uncommitted (including untracked) files in a worktree."""
    lines = git("status", "--porcelain", cwd=path).splitlines()
    return len([line for line in lines if line.strip()])


def open_pr_heads() -> set[str]:
    """Return branch names with an open PR; empty set when `gh` is unavailable."""
    gh = shutil.which("gh")
    if not gh:
        return set()
    result = subprocess.run(  # noqa: S603 - fixed gh executable, no shell.
        [gh, "pr", "list", "--state", "open", "--json", "headRefName"],
        capture_output=True,
        text=True,
        check=False,
        timeout=GH_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        return set()
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError:
        return set()
    return {str(row["headRefName"]) for row in rows}
