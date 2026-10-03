"""Report git worktrees and branches that are merged and safe to remove.

Agent: tooling
Role: measure housekeeping debt - every worktree, local branch and remote
      branch already contained in main, so cleanup is a reading rather than a
      recollection. Read-only: it removes nothing.
External I/O: subprocess via `scripts/worktree_git.py` (`git`, and `gh` when
              present for open-PR heads).

Exit 0 when nothing is stale, 1 when something is. Deliberately NOT a `make ci`
step: stale worktrees are untidy, not broken, and a housekeeping backlog must
never be able to fail the gate. Output is ASCII - this console renders the
repo's em-dashes as mojibake. A permanently standing worktree goes in
`.worktree-keep` (one directory name per line, gitignored): without it that
worktree is reported every run, and a check that cries wolf is worse than none.
"""

from __future__ import annotations

import sys
from pathlib import Path

# `python scripts/check_worktrees.py` puts scripts/, not the repo root, on sys.path.
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.worktree_git import (
    dirty_count,
    git,
    is_contained,
    open_pr_heads,
    primary_root,
    worktrees,
)

MAIN = "main"
REMOTE_MAIN = "origin/main"
KEEP_FILE = ".worktree-keep"


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
    dirty = dirty_count(path)
    if dirty:
        return f"KEEP - {dirty} uncommitted file(s)", False
    if is_contained(head, MAIN):
        return "STALE - merged and clean", True
    return "ACTIVE - commits not in main", False


def _report_worktrees(root: Path) -> list[str]:
    """Print every secondary worktree's verdict; return the stale paths."""
    stale: list[str] = []
    kept = _kept(root)
    print("Worktrees")
    for record in worktrees():
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
    live = {r.get("branch", "").removeprefix("refs/heads/") for r in worktrees()}
    local = [
        name
        for raw in git("branch", "--merged", MAIN).splitlines()
        if (name := raw.lstrip("*+ ").strip())
        and name != MAIN
        and name not in live
        and not name.startswith("backup/")
    ]
    remote = [
        short
        for raw in git("branch", "-r", "--merged", REMOTE_MAIN).splitlines()
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
    root = primary_root()
    stale = _report_worktrees(root)
    local, remote = _report_branches(open_pr_heads())
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
