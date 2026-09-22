"""Audit every locked dependency and re-check each advisory the repo accepts.

Agent: tooling
Role: fail the gate on any unaccepted vulnerability, and on any accepted one
      whose stated justification has stopped being true.
External I/O: runs `uv export` and `pip-audit`; reads Dockerfiles; prints a report.

Scope is the lockfile with every extra and group, not the interpreter that happens
to be running. A bare `pip-audit` audits whatever is installed, which in CI is
`uv sync --frozen` - no optional extras - so the packages the fleet images install
were never audited there at all, and an ignore aimed at one of them suppressed
nothing (DL-199). The lock is the same set everywhere.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from shutil import which
from typing import Any

# Run directly (`python scripts/check_dependency_audit.py`) only `scripts/` is on
# sys.path, not the repo root, so the sibling import below needs the root first.
# Same shape as scripts/check_sprint_status.py.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.dependency_audit_rules import evaluate  # noqa: E402

_EXPORT = [
    "uv",
    "export",
    "--frozen",
    "--all-extras",
    "--all-groups",
    "--no-emit-project",
    "--format",
    "requirements-txt",
]


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a fixed local command, returning its result without raising on exit."""
    executable = which(command[0])
    if executable is None:
        raise RuntimeError(f"{command[0]} was not found on PATH")
    return subprocess.run(  # noqa: S603 - fixed, local, read-only arguments.
        [executable, *command[1:]],
        cwd=cwd,
        capture_output=True,
        check=False,
        text=True,
    )


def audit_report(root: Path) -> dict[str, Any]:
    """Export the whole lock and return pip-audit's JSON report for it."""
    exported = _run(_EXPORT, root)
    if exported.returncode:
        raise RuntimeError(exported.stderr.strip() or "uv export failed")
    with tempfile.TemporaryDirectory() as directory:
        requirements = Path(directory) / "locked-requirements.txt"
        requirements.write_text(exported.stdout, encoding="utf-8")
        audited = _run(
            [
                "uv",
                "run",
                "pip-audit",
                "--progress-spinner",
                "off",
                "--no-deps",
                "--disable-pip",
                "--format",
                "json",
                "-r",
                str(requirements),
            ],
            root,
        )
    try:
        return dict(json.loads(audited.stdout))
    except json.JSONDecodeError as exc:
        raise RuntimeError(audited.stderr.strip() or f"pip-audit: {exc}") from exc


def tracked_dockerfiles(root: Path) -> dict[str, str]:
    """Return every tracked Dockerfile's text, keyed by repo-relative path."""
    listed = _run(["git", "ls-files", "*Dockerfile"], root)
    if listed.returncode:
        raise RuntimeError(listed.stderr.strip() or "git ls-files failed")
    names = [name for name in listed.stdout.splitlines() if name]
    return {name: (root / name).read_text(encoding="utf-8") for name in names}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit locked dependencies.")
    parser.add_argument(
        "--audit-json",
        type=Path,
        help="read a recorded pip-audit JSON report instead of running the audit",
    )
    arguments = parser.parse_args(argv)
    try:
        report = (
            json.loads(arguments.audit_json.read_text(encoding="utf-8"))
            if arguments.audit_json
            else audit_report(_ROOT)
        )
        dockerfiles = tracked_dockerfiles(_ROOT)
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"dependency audit failed: {exc}")
        return 1
    errors, notes = evaluate(report, dockerfiles)
    for line in (*notes, *errors):
        print(line)
    if errors:
        return 1
    print(f"No unaccepted vulnerabilities; {len(notes)} accepted advisory re-checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
