"""Scan not-yet-tracked files for secrets.

Agent: tooling
Role: close the gap where a brand-new file escapes the detect-secrets sweep.
External I/O: git and pre-commit subprocesses.

`pre-commit run detect-secrets --all-files` resolves "all files" through git, so
it sees tracked files only. A module that has been written but never `git add`ed
is invisible to it: `make ci` reports a clean secret scan, and the finding only
appears at commit time. That is the wrong moment — the point of the local gate is
to fail before you get there. This scans exactly the files `--all-files` skips.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

GIT_TIMEOUT_SECONDS = 60
SCAN_TIMEOUT_SECONDS = 300


def untracked_files() -> list[str]:
    """Return files git knows about but does not track, honouring .gitignore."""
    git = shutil.which("git")
    if not git:
        raise RuntimeError("git not found")
    completed = subprocess.run(  # noqa: S603 - fixed git executable, no shell.
        [git, "ls-files", "--others", "--exclude-standard"],
        check=True,
        text=True,
        capture_output=True,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def scan(paths: list[str]) -> int:
    """Run the detect-secrets hook against *paths* and return its exit code."""
    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError("uv not found")
    completed = subprocess.run(  # noqa: S603 - fixed uv executable, no shell.
        [uv, "run", "pre-commit", "run", "detect-secrets", "--files", *paths],
        check=False,
        timeout=SCAN_TIMEOUT_SECONDS,
    )
    return completed.returncode


def main() -> int:
    """Scan untracked files, reporting what was covered."""
    try:
        paths = untracked_files()
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        sys.stderr.write(f"error listing untracked files: {type(exc).__name__}\n")
        return 1
    if not paths:
        print("detect-secrets (untracked): no untracked files to scan")
        return 0
    print(f"detect-secrets (untracked): scanning {len(paths)} new file(s)")
    code = scan(paths)
    if code != 0:
        sys.stderr.write(
            "\nThese files are not tracked yet, so the --all-files sweep skipped "
            "them.\nCommit would have failed. Fix them now or mark false positives "
            "with an inline `pragma: allowlist secret`.\n"
        )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
