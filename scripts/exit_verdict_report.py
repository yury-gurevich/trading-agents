"""Write EXP-022's verdict.json and one-page verdict.md, byte-stable (S282).

Agent: tooling
Role: assemble the scored arms, their exit profiles and provenance into a sorted,
      rounded document, and mark whether it ran exactly as Appendix P froze it.
External I/O: writes verdict.json and verdict.md under the out-root.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from scripts.exit_verdict_markdown import render_markdown
from scripts.exit_verdict_rule import BAR_BPS, CHAMPION, EXPERIMENT, START, arm_name
from scripts.replay_verdict_report import HISTORY_COUNTER, stable
from scripts.replay_verdict_score import MEAN_BLOCK, RESAMPLES, SEED

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.replay_arms import Manifest
    from scripts.replay_verdict_load import LoadedArms

FROZEN_BOOTSTRAP = (RESAMPLES, MEAN_BLOCK, SEED)


def verdict_document(
    manifest: Manifest,
    loaded: LoadedArms,
    scored: dict[str, Any] | None,
    profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """The verdict or the refusals, every arm's numbers and exits, and provenance."""
    refusals = [*loaded.refusals, *(scored["refusals"] if scored else [])]
    bootstrap = scored["bootstrap"] if scored else {}
    specs = {spec.name: spec for spec in manifest.arms}
    arms = {
        name: {
            "exits": specs[name].exits.as_dict(),
            "profile": profiles.get(name),
            "slippage_bps": specs[name].slippage_bps,
            **numbers,
        }
        for name, numbers in (scored["arms"] if scored else {}).items()
    }
    told = tuple(bootstrap.get(key) for key in ("resamples", "mean_block", "seed"))
    frozen = (manifest.experiment, manifest.start, manifest.require_history) == (
        EXPERIMENT,
        START,
        True,
    )
    return cast(
        "dict[str, Any]",
        stable(
            {
                "absent_inputs": loaded.absent_inputs,
                "appendix_p": frozen and told == FROZEN_BOOTSTRAP,
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


def _provenance(loaded: LoadedArms) -> dict[str, Any]:
    champion = arm_name(CHAMPION, BAR_BPS)
    record = loaded.records.get(champion) or next(iter(loaded.records.values()), {})
    return {
        "cache": record.get("cache", {}),
        "commit": record.get("commit"),
        "first_session": record.get("first_session"),
        "last_session": record.get("last_session"),
        "require_history": record.get("require_history"),
        "sessions": record.get("sessions"),
        "start": record.get("start"),
        "withheld_member_sessions": {
            name: counters.get(HISTORY_COUNTER)
            for name, counters in loaded.absent_inputs.items()
        },
    }
