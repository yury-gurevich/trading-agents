"""Report git worktrees and branches that are merged and safe to remove.

Agent: tooling
Role: measure housekeeping debt - every worktree, local branch and remote
      branch already contained in main, so cleanup is a reading rather than a
      recollection. Read-only: it removes nothing.
External I/O: subprocess (`git`, and `gh` when present for open-PR heads).

Exit 0 when nothing is stale, 1 when something is. Deliberately NOT a `make ci`
step: stale worktrees are untidy, not broken, and a housekeeping backlog must
never be able to fail the gate. Output is ASCII - this console renders the
repo's em-dashes as mojibake. A permanently standing worktree goes in
`.worktree-keep` (one directory name per line, gitignored): without it that
worktree is reported every run, and a check that cries wolf is worse than none.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

MAIN = "main"
REMOTE_MAIN = "origin/main"
KEEP_FILE = ".worktree-keep"
GIT_TIMEOUT_SECONDS = 60
GH_TIMEOUT_SECONDS = 60


def _git_exe() -> str:
    """Return the resolved git executable, or raise if it is not installed."""
    git = shutil.which("git")
    if not git:
        raise RuntimeError("git not found")
    return git


def _git(*args: str, cwd: Path | None = None) -> str:
    """Run a git command and return its stripped stdout ('' on failure)."""
    result = subprocess.run(  # noqa: S603 - fixed git executable, no shell.
        [_git_exe(), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _root() -> Path:
    """Return the primary worktree's path."""
    return Path(_git("rev-parse", "--path-format=absolute", "--git-common-dir")).parent


def _worktrees() -> list[dict[str, str]]:
    """Parse `git worktree list --porcelain` into one record per worktree."""
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in _git("worktree", "list", "--porcelain").splitlines():
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


def _is_contained(sha: str, base: str) -> bool:
    """Return whether a commit is already an ancestor of base."""
    completed = subprocess.run(  # noqa: S603 - fixed git executable, no shell.
        [_git_exe(), "merge-base", "--is-ancestor", sha, base],
        capture_output=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    return completed.returncode == 0


def _dirty_count(path: Path) -> int:
    """Count uncommitted (including untracked) files in a worktree."""
    lines = _git("status", "--porcelain", cwd=path).splitlines()
    return len([line for line in lines if line.strip()])


def _open_pr_heads() -> set[str]:
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


def _kept(root: Path) -> set[str]:
    """Return worktree directory names the operator marked as standing."""
    keep = root / KEEP_FILE
    if not keep.is_file():
        return set()
    return {
        line.strip()
        for line in keep.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def _verdict(path: Path, head: str, kept: set[str]) -> tuple[str, bool]:
    """Return one worktree's verdict line and whether it is stale."""
    if path.name in kept:
        return f"KEEP - listed in {KEEP_FILE}", False
    dirty = _dirty_count(path)
    if dirty:
        return f"KEEP - {dirty} uncommitted file(s)", False
    if _is_contained(head, MAIN):
        return "STALE - merged and clean", True
    return "ACTIVE - commits not in main", False


def _report_worktrees(root: Path) -> list[str]:
    """Print every secondary worktree's verdict; return the stale paths."""
    stale: list[str] = []
    kept = _kept(root)
    print("Worktrees")
    for record in _worktrees():
        path = Path(record["worktree"])
        if path.resolve() == root.resolve():
            print(f"  - {path.name}: primary")
            continue
        branch = record.get("branch", "").removeprefix("refs/heads/") or "(detached)"
        line, is_stale = _verdict(path, record.get("HEAD", "HEAD"), kept)
        if is_stale:
            stale.append(str(path))
        print(f"  - {path.name} [{branch}]: {line}")
    return stale


def _report_branches(open_prs: set[str]) -> tuple[list[str], list[str]]:
    """Print merged local and remote branches; return both stale name lists."""
    live = {r.get("branch", "").removeprefix("refs/heads/") for r in _worktrees()}
    local = [
        name
        for raw in _git("branch", "--merged", MAIN).splitlines()
        if (name := raw.lstrip("*+ ").strip())
        and name != MAIN
        and name not in live
        and not name.startswith("backup/")
    ]
    remote = [
        short
        for raw in _git("branch", "-r", "--merged", REMOTE_MAIN).splitlines()
        if "->" not in raw
        and (short := raw.strip().removeprefix("origin/"))
        and short != MAIN
        and short not in open_prs
        and not short.startswith("backup/")
    ]
    print("\nMerged local branches with no worktree")
    print("\n".join(f"  - {name}" for name in local) or "  (none)")
    print("\nMerged remote branches with no open PR")
    print("\n".join(f"  - origin/{name}" for name in remote) or "  (none)")
    return local, remote


def main() -> int:
    """Print the housekeeping report; exit 1 when anything is prunable."""
    root = _root()
    stale = _report_worktrees(root)
    local, remote = _report_branches(_open_pr_heads())
    print(f"\nSkipped: backup/*, open-PR branches, worktrees in {KEEP_FILE}.")
    if not (stale or local or remote):
        print("\nCLEAN - no stale worktrees or merged branches.")
        return 0
    print(
        f"\nSTALE - {len(stale)} worktree(s), "
        f"{len(local)} local branch(es), {len(remote)} remote branch(es)."
    )
    print("Remove with: git worktree remove <path> ; git branch -d <name> ;")
    print("             git push origin --delete <name>")
    return 1


if __name__ == "__main__":
    sys.exit(main())
