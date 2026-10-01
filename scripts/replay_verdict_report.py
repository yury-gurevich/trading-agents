"""Write EXP-014's verdict.json and one-page verdict.md, byte-stable (S250).

Agent: tooling
Role: assemble the scored arms into a sorted, rounded document (DL-258 D6).
External I/O: writes verdict.json and verdict.md under the out-root.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from scripts.replay_verdict_markdown import render_markdown
from scripts.replay_verdict_rule import BASE_ARM
from scripts.replay_verdict_score import MEAN_BLOCK, RESAMPLES, SEED

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.replay_arms import Manifest
    from scripts.replay_verdict_load import LoadedArms

DECIMALS = 6
HISTORY_COUNTER = "member_sessions_below_required_history"


def verdict_document(
    manifest: Manifest, loaded: LoadedArms, scored: dict[str, Any] | None
) -> dict[str, Any]:
    """The verdict or the refusals, every arm's numbers, and provenance."""
    refusals = [*loaded.refusals, *(scored["refusals"] if scored else [])]
    bootstrap = scored["bootstrap"] if scored else {}
    specs = {spec.name: spec for spec in manifest.arms}
    arms = {
        name: {
            "overrides": list(specs[name].overrides),
            "slippage_bps": specs[name].slippage_bps,
            **numbers,
        }
        for name, numbers in (scored["arms"] if scored else {}).items()
    }
    return cast(
        "dict[str, Any]",
        stable(
            {
                "absent_inputs": loaded.absent_inputs,
                "appendix_p": (
                    bootstrap.get("resamples"),
                    bootstrap.get("mean_block"),
                    bootstrap.get("seed"),
                )
                == (RESAMPLES, MEAN_BLOCK, SEED),
                "arms": arms,
                "bootstrap": bootstrap,
                "control": scored["control"] if scored else None,
                "differences": scored["differences"] if scored else {},
                "experiment": manifest.experiment,
                "provenance": _provenance(loaded),
                "refusals": refusals,
                "verdict": None if refusals or not scored else scored["verdict"],
            }
        ),
    )


def write_verdict(out_root: Path, document: dict[str, Any]) -> None:
    """verdict.json (sorted keys, 6 decimals) and verdict.md beside the arms."""
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "verdict.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_root / "verdict.md").write_text(render_markdown(document), encoding="utf-8")


def stable(value: object) -> object:
    """Floats to 6 decimals, -0.0 made 0.0, tuples as lists (keys sort at write)."""
    if isinstance(value, float):
        return round(value, DECIMALS) + 0.0
    if isinstance(value, dict):
        return {str(key): stable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [stable(item) for item in value]
    return value


def _provenance(loaded: LoadedArms) -> dict[str, Any]:
    record = loaded.records.get(BASE_ARM) or next(iter(loaded.records.values()), {})
    return {
        "cache": record.get("cache", {}),
        "commit": record.get("commit"),
        "first_session": record.get("first_session"),
        "last_session": record.get("last_session"),
        "require_history": record.get("require_history"),
        "sessions": record.get("sessions"),
        "withheld_member_sessions": {
            name: counters.get(HISTORY_COUNTER)
            for name, counters in loaded.absent_inputs.items()
        },
    }
