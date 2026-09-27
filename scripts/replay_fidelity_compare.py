"""Run S237's three layers over an export and compute the DL-237 verdict.

Agent: tooling
Role: load sessions, judge each deploy with git, replay Layer 1 stage-isolated, run
      Layer 2 when a cache is given, count Layer 3, and write the report.
External I/O: reads export/cache dirs, runs local git, writes reports outside the repo.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any

from scripts.replay_fidelity_cache import load_cache
from scripts.replay_fidelity_git import DeployCheck, check_deploy
from scripts.replay_fidelity_inputs import effective_settings, load_sessions
from scripts.replay_fidelity_layer2 import layer2_rows
from scripts.replay_fidelity_layer3 import layer3_row
from scripts.replay_fidelity_report import write_report
from scripts.replay_fidelity_session import STAGES, replay_session
from scripts.replay_fidelity_verdict import compute_verdict

if TYPE_CHECKING:
    from scripts.replay_fidelity_inputs import SessionInputs
    from scripts.replay_fidelity_session import SessionResult

_ROOT = Path(__file__).resolve().parents[1]
_NO_CACHE = "no --cache given: Layer 2 needs the S235 replay cache"


def refuse_worktree_out(out: Path) -> Path:
    """Return a resolved output dir, rejecting paths inside this worktree."""
    resolved = out.resolve()
    try:
        resolved.relative_to(_ROOT.resolve())
    except ValueError:
        return resolved
    raise ValueError(f"fidelity output path is inside the worktree: {out}")


def run_fidelity(
    *, export: Path, cache: Path | None, out: Path, repo: Path | None = None
) -> dict[str, Any]:
    """Replay every exported session and write the three layers and the verdict."""
    target = refuse_worktree_out(out)
    sessions = load_sessions(export)
    settings = effective_settings()
    checks: dict[str, DeployCheck] = {}
    results: list[tuple[SessionInputs, DeployCheck, SessionResult]] = []
    for inputs in sessions:
        deploy = inputs.payload.get("deploy")
        key = json.dumps(deploy, sort_keys=True)
        if key not in checks:
            checks[key] = check_deploy(deploy, repo if repo is not None else _ROOT)
        results.append(
            (inputs, checks[key], replay_session(inputs, settings, checks[key]))
        )
    layer1 = [row for _, _, result in results for row in result.rows]
    summary = compute_verdict(
        layer1,
        scanner_sessions=sum(
            1
            for _, check, result in results
            if check.clean and result.replayed["scanner"]
        ),
    )
    summary["replayed"] = {
        stage: sum(1 for *_, result in results if result.replayed[stage])
        for stage in STAGES
    }
    summary["not_replayed"] = [
        {"session": inputs.session, "stage": stage}
        for inputs, _, result in results
        for stage in STAGES
        if result.compared[stage] and not result.replayed[stage]
    ]
    summary["sessions"] = _sessions(results)
    layer2 = None
    summary["layer2"] = {"skipped": True, "reason": _NO_CACHE}
    if cache is not None:
        context = load_cache(cache)
        layer2 = [
            row for inputs in sessions for row in layer2_rows(inputs, settings, context)
        ]
        summary["layer2"] = {
            "skipped": False,
            "sessions": len({row["session"] for row in layer2}),
        }
    layer3 = [layer3_row(inputs.payload) for inputs in sessions]
    totals: Counter[str] = Counter()
    for row in layer3:
        totals.update({k: v for k, v in row.items() if k != "session"})
    summary["layer3"] = dict(totals)
    write_report(target, layer1, layer2, layer3, summary)
    return summary


def _sessions(
    results: list[tuple[SessionInputs, DeployCheck, SessionResult]],
) -> dict[str, Any]:
    clean = [inputs.session for inputs, check, _ in results if check.clean]
    non_clean = [
        {
            "session": inputs.session,
            "git_sha": check.sha,
            "tag": (inputs.payload.get("deploy") or {}).get("tag"),
            "changed": list(check.changed),
            "causes": dict(
                sorted(
                    Counter(row["cause"] for row in result.rows if row["cause"]).items()
                )
            ),
        }
        for inputs, check, result in results
        if not check.clean
    ]
    return {"clean": clean, "non_clean": non_clean}
