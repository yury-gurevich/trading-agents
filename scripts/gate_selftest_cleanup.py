"""Remove what a gate self-test run planted, and name what is left.

Agent: tooling
Role: remove probe folders with their contents and name any probe path left.
External I/O: deletes probe paths under a root and changes their permission bits.

A probe folder goes with whatever a gate wrote into it (a compiled file, a cache). A
folder its owner may not change cannot be removed, and `shutil.rmtree` then leaves it
and says nothing. On Windows that is the read-only attribute, which 437 of the 444
folders of one checkout carried (measured 2026-10-14, DL-299 amendment 1); on Linux it
is a folder without the owner's write bit. So the owner's rights are given back first,
and the runner fails a run that still leaves a probe path.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import stat
from pathlib import Path

from scripts.gate_selftest_types import PROBE_PREFIX


def probe_paths(root: Path) -> list[Path]:
    """List every probe path under the root, git's own folder aside."""
    return [
        path
        for path in sorted(root.rglob(f"{PROBE_PREFIX}*"))
        if ".git" not in path.parts
    ]


def remove_probe_dirs(root: Path) -> None:
    """Remove each probe folder with whatever a gate left inside it."""
    for path in probe_paths(root):
        if path.is_dir():
            _make_writable(path)
            shutil.rmtree(path, ignore_errors=True)


def probes_left(root: Path) -> list[str]:
    """Name every probe path still in the tree: a run must leave none."""
    return [str(path.relative_to(root)) for path in probe_paths(root)]


def _make_writable(path: Path) -> None:
    """Give the owner the right to change a folder and everything under it."""
    _restore_owner(path)
    for folder, folders, files in os.walk(path):
        for name in (*folders, *files):
            _restore_owner(Path(folder, name))


def _restore_owner(path: Path) -> None:
    # A link is removed as a link: what it points at is not ours to change.
    if path.is_symlink():
        return
    with contextlib.suppress(OSError):
        path.chmod(stat.S_IRWXU)
