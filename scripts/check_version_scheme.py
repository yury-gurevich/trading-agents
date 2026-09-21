"""Check the project version uses the repository's declared format.

Agent: tooling
Role: enforce the `MAJOR.MMM.PP` project-version convention in the offline CI gate.
External I/O: reads a local pyproject.toml file and writes reports to stdout.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

_VERSION = re.compile(r"\d+\.\d{1,3}\.\d{2}\Z")


def check_version(path: Path) -> str | None:
    """Return an actionable error when the project version has the wrong shape."""
    try:
        project = tomllib.loads(path.read_text(encoding="utf-8"))["project"]
        version = project["version"]
    except (KeyError, OSError, tomllib.TOMLDecodeError) as exc:
        return f"{path}: cannot read [project].version: {exc}"
    if not isinstance(version, str) or not _VERSION.fullmatch(version):
        return f"{path}: version {version!r} must match MAJOR.MMM.PP"
    return None


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        print("usage: check_version_scheme.py [pyproject.toml]")
        return 2
    path = Path(argv[0]) if argv else Path("pyproject.toml")
    error = check_version(path)
    if error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
