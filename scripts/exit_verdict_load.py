"""Load EXP-022's arm folders and refuse what Appendix P does not name (S282).

Agent: tooling
Role: check the manifest against Appendix P's twelve arms, load them through S250's
      loader, and refuse an arm whose fills are missing or whose exits differ.
External I/O: reads arm folders under the out-root.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from scripts.exit_verdict_rule import FAMILIES, POLICIES, arm_name
from scripts.replay_verdict_load import LoadedArms, load_arms

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.replay_arms import Manifest

FILLS = "fills.csv"


def load_exit_arms(out_root: Path, manifest: Manifest) -> LoadedArms:
    """Every Appendix P arm from `<out-root>/<arm>/`, refused by name if it misfits."""
    refusals = manifest_refusals(manifest)
    if refusals:  # a manifest Appendix P does not name is never loaded
        return LoadedArms(refusals=refusals)
    loaded = load_arms(out_root, manifest)
    for spec in manifest.arms:
        record = loaded.records.get(spec.name)
        if record is None:
            continue
        if not (out_root / spec.name / FILLS).is_file():
            loaded.refusals.append(_refuse(spec.name, f"missing {FILLS}"))
        told = record.get("exits")
        want = spec.exits.as_dict() if spec.exits.declared else None
        if told != want:
            reason = f"exits is {told!r}; the manifest says {want!r}"
            loaded.refusals.append(_refuse(spec.name, reason))
    return loaded


def manifest_refusals(manifest: Manifest) -> list[dict[str, str]]:
    """Each Appendix P arm the manifest omits or sets otherwise, and each extra."""
    specs = {spec.name: spec for spec in manifest.arms}
    refusals: list[dict[str, str]] = []
    for bps in FAMILIES:
        for stem, policy in POLICIES.items():
            name = arm_name(stem, bps)
            spec = specs.pop(name, None)
            if spec is None:
                reason = "Appendix P names it; the manifest does not"
                refusals.append(_refuse(name, reason))
                continue
            if (spec.slippage_bps, spec.overrides, spec.exits) != (bps, (), policy):
                reason = (
                    f"the manifest gives it {spec.slippage_bps} bps, overrides "
                    f"{list(spec.overrides)}, exits {spec.exits.as_dict()}; "
                    f"Appendix P {bps} bps, no overrides, exits {policy.as_dict()}"
                )
                refusals.append(_refuse(name, reason))
    refusals.extend(
        _refuse(name, "the manifest names it; Appendix P does not") for name in specs
    )
    return refusals


def _refuse(arm: str, reason: str) -> dict[str, str]:
    return {"arm": arm, "reason": reason}
