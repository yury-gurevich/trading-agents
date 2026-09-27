"""Write the S237 fidelity report: three layer CSVs, summary.json and fidelity.md.

Agent: tooling
Role: render the computed verdict and layers; decides nothing.
External I/O: writes report files outside the repository worktree.
"""

from __future__ import annotations

import csv
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

LAYER1 = (
    "session",
    "stage",
    "ticker",
    "field",
    "live",
    "replay",
    "match",
    "judged",
    "cause",
    "clean",
)
_UNITS = {
    "scanner": "candidate membership and rank, per session and ticker",
    "analyst": "action, exit trigger and confidence within 1e-9, per ticker",
    "pm": "decision and reason, plus quantity and stop pct for an approval, per judged "
    "recommendation",
}
_WORDS = {
    "PASS": "On the inputs the fleet actually saw, the harness decided what the fleet "
    "decided at every stage: at least 90 % agreement, zero unexplained differences, "
    "every floor met, over clean sessions only.",
    "FAIL": "The harness does not reproduce the fleet on its own inputs. As DL-237 "
    "says, FAIL stops P17: the named causes become the work.",
    "INSUFFICIENT": "Nothing failed the bar, but a stage's denominator is below its "
    "floor, so the verdict is INSUFFICIENT, not PASS.",
}


def write_report(
    target: Path,
    layer1: list[dict[str, Any]],
    layer2: list[dict[str, Any]] | None,
    layer3: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """Write every report file; Layer 2's CSV only when Layer 2 ran."""
    target.mkdir(parents=True, exist_ok=True)
    _csv(target / "layer1.csv", LAYER1, layer1)
    if layer2 is not None:
        _csv(
            target / "layer2.csv", tuple(layer2[0]) if layer2 else ("session",), layer2
        )
    _csv(target / "layer3.csv", tuple(layer3[0]) if layer3 else ("session",), layer3)
    (target / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (target / "fidelity.md").write_text(markdown(summary), encoding="utf-8")


def markdown(summary: dict[str, Any]) -> str:
    """Render the verdict, each stage's number and denominator, and what sat beside."""
    lines = [
        "# S237 fidelity: the replay against the fleet, on the fleet's own inputs",
        "",
        f"**Verdict (DL-237, as amended): {summary['verdict']}.** "
        + _WORDS[summary["verdict"]],
        "",
        "| Stage | Unit | Agreement | Matches / units | Floor | Causes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for stage, block in summary["stages"].items():
        agreement = block["agreement"]
        shown = "n/a" if agreement is None else f"{agreement:.1%}"
        floor = block["floor"]
        causes = ", ".join(f"{k} {v}" for k, v in block["causes"].items()) or "none"
        lines.append(
            f"| {stage} | {_UNITS[stage]} | {shown} | {block['matches']} / "
            f"{block['units']} | {floor['observed']} / {floor['required']} "
            f"{floor['unit']} | {causes} |"
        )
    passthrough = summary["stages"]["pm"]["hold_passthrough"]
    sessions = summary["sessions"]
    lines += [
        "",
        f"PM `hold_recommendation` passthroughs, never pooled: {passthrough['matches']}"
        f" of {passthrough['units']} agree.",
        f"Unexplained clean differences: {summary['unexplained']}.",
        f"Why: {'; '.join(summary['reasons']) or 'every rule held'}.",
        "",
        f"Clean sessions ({len(sessions['clean'])}): "
        f"{', '.join(sessions['clean']) or 'none'}.",
        "Non-clean sessions, reported beside the verdict and never pooled: "
        + (
            "; ".join(
                f"{item['session']} ({', '.join(item['changed'])})"
                for item in sessions["non_clean"]
            )
            or "none"
        )
        + ".",
        "Stages not replayed: "
        + (
            ", ".join(f"{i['session']} {i['stage']}" for i in summary["not_replayed"])
            or "none"
        )
        + ".",
        "",
        _layer2_line(summary["layer2"]),
        "Layer 3 (live only, counts): "
        + ", ".join(f"{k} {v}" for k, v in summary["layer3"].items())
        + ".",
        "",
    ]
    return "\n".join(lines)


def _layer2_line(layer2: dict[str, Any]) -> str:
    if layer2["skipped"]:
        return f"Layer 2 skipped: {layer2['reason']}."
    return (
        f"Layer 2 ran on {layer2['sessions']} session(s): see layer2.csv "
        "(Jaccard against step 0; entered and left against the previous step)."
    )


def _csv(path: Path, header: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows([[_cell(row.get(name)) for name in header] for row in rows])


def _cell(value: object) -> object:
    return "" if value is None else value
