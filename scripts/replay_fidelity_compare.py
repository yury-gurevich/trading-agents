"""Compare S237 exported live sessions with replayed stage outputs.

Agent: tooling
Role: write layer CSVs, named causes, and the DL-237 verdict summary.
External I/O: reads export/cache dirs and writes reports outside the worktree.
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Any

from scripts.replay_fidelity_layers import layer1_rows, layer2_rows, layer3_row

if TYPE_CHECKING:
    from collections.abc import Callable

_ROOT = Path(__file__).resolve().parents[1]
_PASS_FLOOR = 0.90  # DL-237 per-stage agreement floor.
_MIN_ANALYST_DENOMINATOR = 100  # DL-237 minimum clean analyst decisions.
_DECISION_PATHS = (
    "agents/scanner/",
    "agents/analyst/",
    "agents/portfolio_manager/",
    "agents/provider/domain/",
    "agents/execution/order_tolerance.py",
    "contracts/",
    "trading_tunables.json",
    "orchestration/history_window.py",
)


def refuse_worktree_out(out: Path) -> Path:
    """Return a resolved output dir, rejecting paths inside this worktree."""
    resolved = out.resolve()
    try:
        resolved.relative_to(_ROOT.resolve())
    except ValueError:
        return resolved
    raise ValueError(f"fidelity output path is inside the worktree: {out}")


def run_fidelity(
    *,
    export: Path,
    cache: Path | None,
    out: Path,
    git_diff: Callable[[str], tuple[str, ...]] | None = None,
) -> dict[str, Any]:
    """Compare exported sessions and write layer outputs."""
    del cache
    target = refuse_worktree_out(out)
    target.mkdir(parents=True, exist_ok=True)
    diff = git_diff or _git_diff
    layer1: list[dict[str, Any]] = []
    layer2: list[dict[str, Any]] = []
    layer3: list[dict[str, Any]] = []
    clean_rows: list[dict[str, Any]] = []
    non_clean: list[dict[str, Any]] = []
    for path in sorted(export.glob("sched-*.json")):
        session = json.loads(path.read_text(encoding="utf-8"))
        deploy = session.get("deploy", {})
        sha = str(deploy.get("sha", "")) if isinstance(deploy, dict) else ""
        changed = _decision_changes(tuple(diff(sha)))
        rows = layer1_rows(session, changed)
        layer1.extend(rows)
        layer2.extend(layer2_rows(session))
        layer3.append(layer3_row(session))
        if changed:
            non_clean.append(_non_clean_summary(session, rows))
        else:
            clean_rows.extend(rows)
    summary = _summary(clean_rows, non_clean)
    _write_csv(target / "layer1.csv", layer1)
    _write_csv(target / "layer2.csv", layer2)
    _write_csv(target / "layer3.csv", layer3)
    (target / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (target / "fidelity.md").write_text(_markdown(summary), encoding="utf-8")
    return summary


def _summary(
    clean_rows: list[dict[str, Any]], non_clean: list[dict[str, Any]]
) -> dict[str, Any]:
    denominator = len(clean_rows)
    matches = sum(1 for row in clean_rows if row["match"])
    causes = Counter(row["cause"] for row in clean_rows if row["cause"])
    agreement = matches / denominator if denominator else 0.0
    verdict = "INSUFFICIENT"
    if causes.get("unexplained", 0):
        verdict = "FAIL"
    elif denominator >= _MIN_ANALYST_DENOMINATOR:
        verdict = "PASS" if agreement >= _PASS_FLOOR else "FAIL"
    return {
        "verdict": verdict,
        "clean": {
            "denominator": denominator,
            "matches": matches,
            "agreement": agreement,
            "pooled": {"causes": dict(sorted(causes.items()))},
        },
        "non_clean": non_clean,
    }


def _non_clean_summary(
    session: dict[str, Any], rows: list[dict[str, Any]]
) -> dict[str, Any]:
    causes = Counter(row["cause"] for row in rows if row["cause"])
    return {"session": session["session"], "causes": dict(sorted(causes.items()))}


def _decision_changes(paths: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(path for path in paths if path.startswith(_DECISION_PATHS))


def _git_diff(sha: str) -> tuple[str, ...]:
    if not sha or sha == "HEAD":
        return ()
    git = shutil.which("git") or "git"
    result = subprocess.run(  # noqa: S603 - fixed git subcommand over local metadata.
        [git, "diff", "--name-only", sha, "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(line for line in result.stdout.splitlines() if line)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    header = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _markdown(summary: dict[str, Any]) -> str:
    return (
        "# S237 Fidelity\n\n"
        f"verdict: {summary['verdict']}\n\n"
        f"clean denominator: {summary['clean']['denominator']}\n"
    )
