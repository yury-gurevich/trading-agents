"""Render EXP-022's verdict document as one page of Markdown (S282).

Agent: tooling
Role: the verdict and each exit arm's paired difference first; then the arms, their
      exits, the 25 bps years, the control and provenance.
External I/O: none.
"""

from __future__ import annotations

from typing import Any

from scripts.exit_verdict_rule import BAR_BPS, CHALLENGERS, CHAMPION, arm_name

R_KEY = "annualised_return_pts"
A_KEY = "annualised_excess_pts"
_DIFF_HEADER = (
    "| Arm | dR (pts/yr) | Interval | First half | Second half "
    "| dA (pts/yr) | dA interval | Reading |"
)
_ARM_KEYS = ("portfolio_return_pct", "average_exposure_pct", "max_drawdown_pct")
_ARM_HEADER = (
    "| Arm | Slippage (bps) | R (pts/yr) | A (pts/yr) | Portfolio % "
    "| Avg exposure % | Max drawdown % | Buys a year |"
)


def render_markdown(document: dict[str, Any]) -> str:
    """The page: a refusal replaces everything after the title."""
    lines = [f"# {document['experiment']} verdict: {_title(document)}", ""]
    if document["refusals"]:
        lines += ["The scorer gives no verdict:", ""]
        lines += [
            f"- **{item['arm']}**: {item['reason']}" for item in document["refusals"]
        ]
        return "\n".join([*lines, ""])
    boot = document["bootstrap"]
    lines += [
        "Each exit arm against stops-only at its own slippage: dR is the difference "
        f"in annualised return, each interval 95 % over a family's "
        f"{boot['comparisons']} challengers; {boot['pairs']:,} session pairs, "
        f"{boot['resamples']:,} resamples, mean block {boot['mean_block']}, "
        f"seed {boot['seed']}.",
        "",
        "## Paired differences from stops-only",
        "",
        _DIFF_HEADER,
        "| --- | ---: | --- | ---: | ---: | ---: | --- | --- |",
    ]
    readings = document["verdict"]["readings"]
    for name, item in document["differences"].items():
        excess = item["excess"]
        cells = (
            name,
            _pts(item["point"]),
            _interval(item["interval"]),
            *(_pts(gap) for gap in item["halves"]),
            _pts(excess["point"]),
            _interval(excess["interval"]),
            readings[name],
        )
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## Arms", "", _ARM_HEADER, "| --- |" + " ---: |" * 7]
    lines += [_arm_row(name, arm) for name, arm in document["arms"].items()]
    lines += _exits(document["arms"])
    lines += _years(document)
    control = document["control"]
    lines += [
        "",
        "## Control",
        "",
        f"Each arm rebuilt in its own order scores its own R and A within "
        f"{control['tolerance_pts']:g}: largest deviation "
        f"{control['max_deviation_pts']:.3g}, "
        f"{'PASS' if control['passed'] else 'FAIL'}.",
    ]
    lines += _provenance(document["provenance"])
    return "\n".join([*lines, ""])


def _title(document: dict[str, Any]) -> str:
    verdict = document["verdict"]
    if verdict is None:
        return "NO VERDICT"
    title = verdict["verdict"]
    if verdict["leader"]:
        title += f" (leader: {verdict['leader']}; {', '.join(verdict['winners'])})"
    return title if document["appendix_p"] else f"{title}, NOT Appendix P"


def _arm_row(name: str, arm: dict[str, Any]) -> str:
    whole = arm["whole"]
    cells = [name, str(arm["slippage_bps"]), _pts(whole[R_KEY]), _pts(whole[A_KEY])]
    cells += [f"{whole[key]:.2f}" for key in _ARM_KEYS]
    cells.append(f"{arm['profile']['buys_per_year']:.1f}")
    return "| " + " | ".join(cells) + " |"


def _exits(arms: dict[str, Any]) -> list[str]:
    lines = ["", "## Exits (round trips by the reason that closed them)", ""]
    lines += ["| Arm | Reason | Trips | Gains % | Mean return % | Median sessions |"]
    lines += ["| --- | --- | ---: | ---: | ---: | ---: |"]
    for name, arm in arms.items():
        for reason, item in arm["profile"]["exits"].items():
            lines.append(
                f"| {name} | {reason} | {item['count']} | {item['gain_share_pct']:.1f} "
                f"| {item['mean_return_pct']:+.2f} | {item['median_held_sessions']:g} |"
            )
    return lines


def _years(document: dict[str, Any]) -> list[str]:
    names = [arm_name(stem, BAR_BPS) for stem in CHALLENGERS]
    differences = document["differences"]
    lines = ["", f"## Years (dR at {BAR_BPS} bps, pts a year)", ""]
    lines += ["| Year | " + " | ".join(names) + " |"]
    lines += ["| --- |" + " ---: |" * len(names)]
    rows = document["arms"][arm_name(CHAMPION, BAR_BPS)]["years"]
    for index, row in enumerate(rows):
        label = row["label"] + (", partial" if row["partial"] else "")
        cells = [_pts(differences[name]["years"][index]) for name in names]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return lines


def _provenance(provenance: dict[str, Any]) -> list[str]:
    cache = ", ".join(f"`{key}` {value}" for key, value in provenance["cache"].items())
    rule = "on" if provenance["require_history"] else "off"
    return [
        "",
        "## Provenance",
        "",
        f"- Commit: `{provenance['commit']}`",
        f"- Sessions: {provenance['sessions']}, {provenance['first_session']} → "
        f"{provenance['last_session']}; start {provenance['start']}; "
        f"history rule {rule}",
        f"- Cache (SHA-256 prefix): {cache}",
    ]


def _pts(value: float) -> str:
    return f"{value:+.2f}"


def _interval(bounds: list[float]) -> str:
    return f"[{bounds[0]:+.2f}, {bounds[1]:+.2f}]"
