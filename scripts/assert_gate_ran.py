"""Assert a workflow run exists for a commit, and went green, before merging it.

Agent: tooling
Role: turn "did the branch go green?" from an eyeball check into a failing command.
External I/O: runs `git rev-parse` and reads the GitHub REST API through `gh`.

Hardening row M: on 2026-07-23 a pushed branch produced **no runs at all** and the
cause was never established. "No runs appeared" looks identical to "not pushed
yet" if you only glance at the run list, so the branch-is-the-gate rule can be
defeated by an infrastructure miss rather than a process mistake.

Measured 2026-08-05, and it is the likelier reading of that incident: the GitHub
API's `head_sha` filter matches only the **full 40-character SHA**. Handed an
abbreviated one it returns `total_count: 0` — no error, no warning, no hint the
query was malformed:

    head_sha=c145e5e79a3a3aa7435897d5ec80800167884892  ->  total_count: 2
    head_sha=c145e5e                                   ->  total_count: 0

Both runs existed and both had passed. So this script resolves the full SHA
itself and refuses an abbreviated one outright, rather than inheriting the bug it
exists to catch.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

# `python scripts/assert_gate_ran.py` puts scripts/ on sys.path, not the repo root,
# so the package import fails on clean infrastructure while passing locally off an
# editable install. Same pattern as gate_selftest.py, and measured: CI red at 18/21.
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.gate_run_selection import latest_per_workflow  # noqa: E402

# The workflows whose absence means the commit was never really gated. `gate`
# lives in Security Findings; `quality`/`test`/`security` live in CI.
REQUIRED_WORKFLOWS = ("CI", "Security Findings")
# GitHub creates runs a few seconds after the push, not synchronously with it.
WAIT_SECONDS = 120
POLL_SECONDS = 10
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
TERMINAL_SUCCESS = "success"


class GateNotProven(SystemExit):
    """Exit non-zero with a message naming what was not proven."""

    def __init__(self, message: str) -> None:
        """Print the reason to stderr and exit 1."""
        print(f"GATE NOT PROVEN: {message}", file=sys.stderr)
        super().__init__(1)


def resolve_sha(explicit: str | None) -> str:
    """Return a full 40-character SHA, refusing anything abbreviated."""
    if explicit is None:
        explicit = subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607 - fixed git, no shell.
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    sha = explicit.strip().lower()
    if not FULL_SHA.match(sha):
        raise GateNotProven(
            f"{explicit!r} is not a full 40-character SHA. The GitHub API's "
            "head_sha filter silently returns total_count: 0 for an abbreviated "
            "SHA, so an abbreviated query cannot distinguish 'no runs' from "
            "'wrong question'. Pass the full SHA or omit --sha to use HEAD."
        )
    return sha


def _query_once(sha: str) -> dict[str, object]:
    """Ask GitHub for the runs attached to one full SHA."""
    endpoint = f"repos/:owner/:repo/actions/runs?head_sha={sha}"
    result = subprocess.run(  # noqa: S603 - fixed gh executable, no shell.
        ["gh", "api", endpoint],  # noqa: S607 - gh resolved from PATH by design.
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GateNotProven(
            f"`gh api` failed for {sha}: {result.stderr.strip() or 'no stderr'}"
        )
    return json.loads(result.stdout)


def fetch_runs(
    sha: str, runs_json: Path | None, wait_seconds: int = WAIT_SECONDS
) -> dict[str, object]:
    """Return the runs payload for one SHA, waiting for GitHub to create them.

    A query issued immediately after `git push` returns zero — measured
    2026-08-05: zero at t+0, then `total_count: 2` by t+15s. Without this wait the
    assertion would fail on every ordinary push, and an assertion that cries wolf
    is one people learn to ignore, which is worse than not having it. The wait is
    also what makes *never created* distinguishable from *not created yet* — the
    distinction row M could not make by eye.
    """
    if runs_json is not None:
        return json.loads(runs_json.read_text(encoding="utf-8"))
    deadline = time.monotonic() + wait_seconds
    payload = _query_once(sha)
    while not payload.get("workflow_runs") and time.monotonic() < deadline:
        time.sleep(POLL_SECONDS)
        payload = _query_once(sha)
    return payload


def check(sha: str, payload: dict[str, object]) -> list[str]:
    """Return the reasons this commit is not proven green; empty means proven."""
    runs = payload.get("workflow_runs") or []
    if not isinstance(runs, list) or not runs:
        return [
            f"no workflow run exists for {sha}. This is the row-M symptom: it is "
            "indistinguishable from 'not pushed yet' on a glance. Confirm the push "
            "landed, then re-run; if the push landed and this stays empty, the run "
            "was never created and merging would bypass the gate entirely."
        ]
    reasons = []
    # Only the newest attempt of each workflow decides: a re-run that fixed a gate
    # must be provable, or the tool teaches people to bypass it (gate_run_selection).
    newest = latest_per_workflow(runs)
    for required in REQUIRED_WORKFLOWS:
        if required not in newest:
            reasons.append(f"workflow {required!r} produced no run for {sha}")
    for name, run in newest.items():
        status = str(run.get("status"))
        conclusion = run.get("conclusion")
        if status != "completed":
            reasons.append(f"{name} is {status}, not completed — wait, do not merge")
        elif conclusion != TERMINAL_SUCCESS:
            reasons.append(f"{name} concluded {conclusion!r}, not 'success'")
    return reasons


def main(argv: list[str] | None = None) -> int:
    """Assert the commit has green runs, printing what was actually observed."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sha", default=None, help="commit to check (default HEAD)")
    parser.add_argument(
        "--runs-json",
        type=Path,
        default=None,
        help="read the runs payload from a file instead of calling gh (self-test)",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=WAIT_SECONDS,
        help=f"how long to wait for GitHub to create the runs (default {WAIT_SECONDS})",
    )
    args = parser.parse_args(argv)

    sha = resolve_sha(args.sha)
    payload = fetch_runs(sha, args.runs_json, args.wait_seconds)
    reasons = check(sha, payload)
    if reasons:
        raise GateNotProven("; ".join(reasons))

    # Print what was judged, not every attempt: listing a superseded failure
    # beside GATE PROVEN reads as a contradiction and invites a second guess.
    newest = latest_per_workflow(payload.get("workflow_runs") or [])
    print(f"GATE PROVEN for {sha}:")
    for name, run in sorted(newest.items()):
        superseded = run.get("run_attempt")
        attempt = f" (attempt {superseded})" if isinstance(superseded, int) else ""
        print(f"  {name}: {run.get('conclusion')}{attempt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
