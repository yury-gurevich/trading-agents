"""Champion/challenger artifact swap for the rolling return-model retrain CLI.

Agent: tooling
Role: name the challenger artifact path, plan the archive-then-install swap, and
      execute it - the only part of the retrain loop that moves model files.
External I/O: execute_swap performs the explicit --apply artifact move/copy.
"""

from __future__ import annotations

import shutil
from pathlib import Path

SwapStep = tuple[str, Path, Path]


def candidate_path_for(model_path: Path, *, stamp: str) -> Path:
    """Return the sprint-standard challenger artifact path for an active model."""
    return (
        model_path.parent
        / "candidates"
        / f"{model_path.stem}-{stamp}{model_path.suffix}"
    )


def plan_swap(model_path: Path, candidate_path: Path, *, stamp: str) -> list[SwapStep]:
    """Plan archive-then-install steps without deleting any artifact."""
    archive_path = (
        model_path.parent / "archive" / f"{model_path.stem}-{stamp}{model_path.suffix}"
    )
    return [
        ("archive", model_path, archive_path),
        ("install", candidate_path, model_path),
    ]


def execute_swap(steps: list[SwapStep]) -> None:
    """Execute a planned archive/install swap."""
    for action, source, destination in steps:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if action == "archive":
            shutil.move(source, destination)
        elif action == "install":
            shutil.copy2(source, destination)
        else:
            raise ValueError(f"unknown swap action: {action}")
