"""Render EXP-014's verdict document as one page of Markdown (S250, DL-258 D6).

Agent: tooling
Role: verdict and base-25's interval first; then arms, differences, control, blocks.
External I/O: none.
"""

from __future__ import annotations

from typing import Any

from scripts.replay_verdict_rule import BASE_ARM

A_KEY = "annualised_excess_pts"
_ARM_HEADER = (
    "| Arm | Slippage (bps) | A (pts/yr) | 95 % interval | Portfolio % "
    "| Exposure-matched % | SPY % | Avg exposure % | Max drawdown % |"
)
_ARM_RULE = "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |"


def render_markdown(document: dict[str, Any]) -> str:
    """The page: a refusal replaces everything after the title."""
    lines = [f"# {document['experiment']} verdict: {_title(document)}", ""]
    if document["refusals"]:
        lines += ["The scorer gives no verdict:", ""]
        lines += [
            f"- **{item['arm']}**: {item['reason']}" for item in document["refusals"]
        ]
        return "\n".join([*lines, ""])
    arms, boot = document["arms"], document["bootstrap"]
    base = arms[BASE_ARM]
    lines += [
        f"**{BASE_ARM}:** A = {_pts(base['whole'][A_KEY])} pts a year, 95 % interval "
        f"{_interval(base['interval'])}; {boot['pairs']:,} session pairs, "
        f"{boot['resamples']:,} resamples, mean block {boot['mean_block']}, "
        f"seed {boot['seed']}.",
        "",
        "## Arms",
        "",
        _ARM_HEADER,
        _ARM_RULE,
    ]
    lines += [_arm_row(name, arm) for name, arm in arms.items()]
    lines += ["", f"## Paired differences from {BASE_ARM}", ""]
    lines += [f"| Arm | A(X) - A({BASE_ARM}) | 95 % interval |"]
    lines += ["| --- | ---: | --- |"]
    lines += [
        f"| {name} | {_pts(item['point'])} | {_interval(item['interval'])} |"
        for name, item in document["differences"].items()
    ]
    control = document["control"]
    lines += [
        "",
        "## Control",
        "",
        f"The replica of {BASE_ARM} earning SPY at its exposure: "
        f"A = {control[A_KEY]:+.6f}, interval [{control['interval'][0]:+.6f}, "
        f"{control['interval'][1]:+.6f}] (tolerance {control['tolerance_pts']:g}): "
        f"{'PASS' if control['passed'] else 'FAIL'}.",
    ]
    lines += _blocks("Years", arms, "years", positive=True)
    lines += _blocks("Halves", arms, "halves", positive=False)
    lines += _provenance(document["provenance"])
    return "\n".join([*lines, ""])


def _title(document: dict[str, Any]) -> str:
    verdict = document["verdict"]
    if verdict is None:
        return "NO VERDICT"
    detail = verdict["reading"] or ", ".join(verdict["pillars"])
    title = f"{verdict['verdict']} ({detail})" if detail else verdict["verdict"]
    return title if document["appendix_p"] else f"{title}, NOT Appendix P's bootstrap"


def _arm_row(name: str, arm: dict[str, Any]) -> str:
    whole = arm["whole"]
    cells = (
        name,
        str(arm["slippage_bps"]),
        _pts(whole[A_KEY]),
        _interval(arm["interval"]),
        *(
            f"{whole[key]:.2f}"
            for key in (
                "portfolio_return_pct",
                "exposure_matched_return_pct",
                "benchmark_return_pct",
                "average_exposure_pct",
                "max_drawdown_pct",
            )
        ),
    )
    return "| " + " | ".join(cells) + " |"


def _blocks(title: str, arms: dict[str, Any], key: str, *, positive: bool) -> list[str]:
    names = list(arms)
    lines = ["", f"## {title} (A, pts a year)", ""]
    lines += ["| Block | " + " | ".join(names) + " |"]
    lines += ["| --- |" + " ---: |" * len(names)]
    for index, row in enumerate(arms[names[0]][key]):
        label = f"{row['label']} ({row['first']} → {row['last']})"
        label += ", partial" if row["partial"] else ""
        cells = [_pts(arms[name][key][index][A_KEY]) for name in names]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    if positive:
        counts = [str(arms[name]["years_with_positive_excess"]) for name in names]
        lines.append("| Years with positive excess | " + " | ".join(counts) + " |")
    return lines


def _provenance(provenance: dict[str, Any]) -> list[str]:
    cache = ", ".join(
        f"`{name}` {value}" for name, value in provenance["cache"].items()
    )
    withheld = ", ".join(
        f"{name} {count}"
        for name, count in provenance["withheld_member_sessions"].items()
    )
    rule = "on" if provenance["require_history"] else "off"
    return [
        "",
        "## Provenance",
        "",
        f"- Commit: `{provenance['commit']}`",
        f"- Sessions: {provenance['sessions']}, {provenance['first_session']} → "
        f"{provenance['last_session']}; history rule {rule}",
        f"- Cache (SHA-256 prefix): {cache}",
        f"- Member-sessions withheld by the history rule: {withheld}",
    ]


def _pts(value: float) -> str:
    return f"{value:+.2f}"


def _interval(bounds: list[float]) -> str:
    return f"[{bounds[0]:+.2f}, {bounds[1]:+.2f}]"
