"""Clean sessions for S237: the deploy's decision code equals the replayed code.

Agent: tooling
Role: resolve a session's deploy SHA with git and name the decision paths it changes.
External I/O: runs the local `git` binary read-only; no network.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# Code and pack data a scanner, analyst or PM decision depends on (DL-238 D7). A
# trailing "/" is a directory; anything else is one file, named by its full path.
DECISION_PATHS = (
    "agents/scanner/",
    "agents/analyst/",
    "agents/portfolio_manager/",
    "agents/provider/domain/",
    "agents/execution/order_tolerance.py",
    "contracts/",
    "orchestration/packs/trading_tunables.json",
    "orchestration/packs/trading_issuer_map.json",
    "orchestration/history_window.py",
)
UNKNOWN_DEPLOY = "unknown_deploy"
_STAGE_HOME = {
    "scanner": "agents/scanner/",
    "analyst": "agents/analyst/",
    "pm": "agents/portfolio_manager/",
}


@dataclass(frozen=True)
class DeployCheck:
    """Whether a session's deploy is provably the replayed decision code."""

    sha: str
    changed: tuple[str, ...]

    @property
    def clean(self) -> bool:
        """Clean only when the SHA resolved and no decision path differs."""
        return not self.changed

    def path_for(self, stage: str) -> str:
        """The changed path to name for a stage's difference (its own agent first)."""
        home = _STAGE_HOME.get(stage, "")
        own = [path for path in self.changed if home and path.startswith(home)]
        return (own or list(self.changed))[0]


def check_deploy(deploy: object, repo: Path) -> DeployCheck:
    """Resolve the exported `git_sha`; any doubt is non-clean (R2: fail closed)."""
    sha = ""
    if isinstance(deploy, Mapping):
        sha = str(deploy.get("git_sha") or "").strip()
    if not sha or not _resolves(repo, sha):
        return DeployCheck(sha, (UNKNOWN_DEPLOY,))
    changed = tuple(
        sorted(
            path
            for path in _git(repo, "diff", "--name-only", sha, "HEAD")
            if _decides(path)
        )
    )
    return DeployCheck(sha, changed)


def _decides(path: str) -> bool:
    return any(
        path.startswith(entry) if entry.endswith("/") else path == entry
        for entry in DECISION_PATHS
    )


def _resolves(repo: Path, sha: str) -> bool:
    try:
        _git(repo, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
    except subprocess.CalledProcessError:
        return False
    return True


def _git(repo: Path, *args: str) -> tuple[str, ...]:
    binary = shutil.which("git") or "git"
    result = subprocess.run(  # noqa: S603 - fixed read-only git subcommands.
        [binary, "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(line for line in result.stdout.splitlines() if line)
