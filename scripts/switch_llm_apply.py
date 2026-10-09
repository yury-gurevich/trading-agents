"""Snapshot and narrowly apply the declared LLM provider.

Agent: tooling
Role: refuse replicas, stop on a failed update and verify configuration preservation.
External I/O: evidence files and injected Azure reads/updates.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from scripts.switch_llm_azure import SwitchOperationError, changed_fields, live_value

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from pathlib import Path

    from scripts.switch_llm_azure import Azure
    from scripts.switch_llm_config import LlmPack


def read_values(
    azure: Azure, pack: LlmPack, emit: Callable[[str], None]
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Report every live value without printing app credentials."""
    snapshots = {app: azure.snapshot(app) for app in pack.apps}
    changed = []
    emit(f"declared provider: {pack.provider}")
    for app, key in pack.apps.items():
        value = live_value(snapshots[app], key)
        differs = value != pack.provider
        if differs:
            changed.append(app)
        emit(f"{app}: {key}={value or '<absent>'}; {'differs' if differs else 'equal'}")
    return snapshots, changed


def apply(
    azure: Azure,
    pack: LlmPack,
    snapshots: dict[str, dict[str, Any]],
    changed: list[str],
    directory: Path,
    *,
    even_if_running: bool,
    clock: Callable[[], datetime],
    emit: Callable[[str], None],
) -> tuple[int, datetime]:
    """Save before/after evidence and return the instant preceding any update."""
    since = clock()
    if not even_if_running:
        for app in pack.apps:
            if azure.has_replicas(app):
                emit(f"refused: {app} has replicas; use --even-if-running to override")
                return 1, since
    directory.mkdir(parents=True, exist_ok=True)
    for app, snapshot in snapshots.items():
        _write(directory, app, "before", snapshot)
    since = clock()
    emit(f"proof since: {since.isoformat()}")
    updated: list[str] = []
    try:
        for app in changed:
            azure.update(app, pack.apps[app], pack.provider)
            updated.append(app)
            emit(f"{app}: updated {pack.apps[app]}={pack.provider}")
    except Exception as exc:
        reason = (
            str(exc) if isinstance(exc, SwitchOperationError) else type(exc).__name__
        )
        emit(
            f"update failed: {reason}; already changed: {', '.join(updated) or 'none'}"
        )
        return 1, since
    failed = False
    for app, key in pack.apps.items():
        after = azure.snapshot(app)
        _write(directory, app, "after", after)
        fields = changed_fields(snapshots[app], after, key)
        if fields:
            emit(f"{app}: other configuration moved: {', '.join(fields)}")
            failed = True
        if live_value(after, key) != pack.provider:
            emit(f"{app}: declared provider was not applied")
            failed = True
        if app not in changed:
            emit(f"{app}: unchanged, activation not re-proven")
    return int(failed), since


def _write(directory: Path, app: str, phase: str, snapshot: dict[str, Any]) -> None:
    (directory / f"{app}.{phase}.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def changed_from_evidence(directory: Path, pack: LlmPack) -> list[str]:
    """Recover changed apps from the original apply's before snapshots."""
    return [
        app
        for app, key in pack.apps.items()
        if live_value(
            json.loads((directory / f"{app}.before.json").read_text(encoding="utf-8")),
            key,
        )
        != pack.provider
    ]
