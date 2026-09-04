"""Pick which attempt of a workflow run decides whether a commit is proven.

Agent: tooling
Role: reduce the many runs GitHub attaches to one SHA to the newest attempt per
      workflow, so a re-run that fixed a gate is what gets judged.
External I/O: none — pure functions over an already-fetched runs payload.

A re-run or re-dispatch leaves the earlier attempt attached to the same SHA.
Judging *every* attempt means a workflow that failed, was fixed and re-ran green
stays red forever -- so the very commit that repairs a gate can never be proven.

Measured 2026-09-04: `Security Findings` concluded `failure` at 11:35:53 because
CodeQL had not yet marked code-scanning alert #178 fixed -- it did at 11:38:08,
two minutes later. A re-dispatch then concluded `success`, and `assert_gate_ran`
still reported GATE NOT PROVEN off the dead first attempt. A proof tool that
cannot be satisfied is one people learn to bypass, which is worse than not having
one at all.

The trade-off is deliberate: latest-wins also accepts a flaky failure that was
re-run until it passed. That is the same bargain GitHub's own required status
checks make, and the alternative -- any attempt pins the commit red -- is
unusable.
"""

from __future__ import annotations


def run_order(run: dict[str, object]) -> tuple[str, int]:
    """Sort key placing the newest attempt last: start time, then run id."""
    started = str(run.get("run_started_at") or run.get("created_at") or "")
    raw_id = run.get("id")
    run_id = raw_id if isinstance(raw_id, int) else 0
    return (started, run_id)


def latest_per_workflow(runs: list[object]) -> dict[str, dict[str, object]]:
    """Keep only the newest run of each workflow name, keyed by that name."""
    newest: dict[str, dict[str, object]] = {}
    for run in runs:
        if not isinstance(run, dict):
            continue
        name = str(run.get("name"))
        current = newest.get(name)
        if current is None or run_order(run) > run_order(current):
            newest[name] = run
    return newest
