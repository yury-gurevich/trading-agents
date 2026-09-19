"""Tracked-file line-ending guard tests.

Agent: repository
Role: prove Git stores tracked text files with LF endings.
External I/O: local Git index read through the git executable.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def offending_eol_paths(records: str) -> list[str]:
    """Return index paths stored with CRLF or mixed endings."""
    offending_paths: list[str] = []
    for record in records.split("\0"):
        if not record:
            continue
        metadata, path = record.split("\t", maxsplit=1)
        index_eol = metadata.split(maxsplit=1)[0]
        if index_eol in {"i/crlf", "i/mixed"}:
            offending_paths.append(path)
    return offending_paths


@pytest.mark.parametrize(
    ("records", "expected"),
    [
        ("i/lf    w/lf    attr/text=auto eol=lf \tagents/a.py\0", []),
        ("i/crlf  w/crlf  attr/                 \tb.py\0", ["b.py"]),
        ("i/mixed w/mixed attr/                 \tdocs/c.md\0", ["docs/c.md"]),
        ("i/-text w/-text attr/-text            \tdocs/d.png\0", []),
        ("i/none  w/none  attr/text=auto eol=lf \te.txt\0", []),
        ("i/lf    w/crlf  attr/text=auto eol=lf \tf.ps1\0", []),
        (
            "i/crlf  w/crlf  attr/                 \tdocs/my file.md\0",
            ["docs/my file.md"],
        ),
        (
            "i/crlf  w/crlf  attr/                 \tb.py\0"
            "i/mixed w/mixed attr/                 \tdocs/c.md\0",
            ["b.py", "docs/c.md"],
        ),
        ("", []),
    ],
)
def test_offending_eol_paths(records: str, expected: list[str]) -> None:
    assert offending_eol_paths(records) == expected


def test_gitattributes_declares_lf_and_binaries() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    attributes_path = repo_root / ".gitattributes"

    assert attributes_path.is_file(), f"missing {attributes_path}"
    attributes = attributes_path.read_text(encoding="utf-8").splitlines()

    assert "* text=auto eol=lf" in attributes
    assert "*.png binary" in attributes
    assert "*.ico binary" in attributes


def test_no_tracked_file_is_stored_crlf() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    git_executable = shutil.which("git")

    assert git_executable is not None, "git executable is required for this guard"
    result = subprocess.run(  # noqa: S603 - fixed git executable, no shell.
        [git_executable, "ls-files", "--eol", "-z"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    assert offending_eol_paths(result.stdout.decode("utf-8")) == []
