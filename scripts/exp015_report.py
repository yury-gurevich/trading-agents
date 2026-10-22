"""EXP-015's result pages: the walk-forward, then the holdout and verdict (S289).

Agent: tooling
Role: render a stage's JSON record as one Markdown page to check against the bar.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scripts.exp015_spec import BAR_FOLDS_WON, BAR_IC_DIFFERENCE, EXPERIMENT

if TYPE_CHECKING:
    from collections.abc import Mapping

_HEADER = "| Fold | Train | Test | Ensemble IC | Baseline IC | Spread (ens / base) |"
_RULE = "| --- | --- | --- | --- | --- | --- |"


def walk_forward_page(record: Mapping[str, Any]) -> str:
    """The walk-forward page: bars 1 and 2, the control, and a row per fold."""
    reading = record["reading"]
    boot, control = reading["bootstrap"], reading["control"]
    lines = [
        f"# {EXPERIMENT} walk-forward — {record['verdict']}",
        "",
        f"Commit `{record['commit']}`, panel `{record['panel_sha256'][:16]}`.",
        "",
        "| Bar | Reading | Holds |",
        "| --- | --- | --- |",
        f"| 1: mean IC difference >= {BAR_IC_DIFFERENCE}, CI low > 0 | "
        f"{_num(reading['mean_ic_difference'])} over {reading['sessions']} sessions; "
        f"[{_num(boot['low'])}, {_num(boot['high'])}] on {boot['sessions']} | "
        f"{_yes(reading['bar1'])} |",
        f"| 2: ensemble ahead in >= {BAR_FOLDS_WON} of {reading['folds']} folds | "
        f"{reading['folds_won']} | {_yes(reading['bar2'])} |",
        f"| control: shuffled target, CI contains 0 | [{_num(control['low'])}, "
        f"{_num(control['high'])}] | {_yes(control['passed'])} |",
        "",
        _HEADER,
        _RULE,
    ]
    lines += [_fold_row(fold) for fold in record["folds"]]
    lines += ["", "Secondary universe (descriptive):", ""]
    lines += [_fold_row(fold) for fold in record["secondary"]]
    return "\n".join(lines) + "\n"


def holdout_page(walk: Mapping[str, Any], record: Mapping[str, Any]) -> str:
    """The verdict page: bar 3 on the holdout, its net top deciles, the verdict."""
    reading, fold = record["reading"], record["holdout"]
    top, bars = fold["top_decile"], walk["reading"]
    lines = [
        f"# {EXPERIMENT} — {record['verdict']}",
        "",
        f"Walk-forward `{record['walk_forward_sha256'][:16]}` "
        f"(bars 1 and 2: {_yes(bars['bar1'])}, {_yes(bars['bar2'])}).",
        "",
        f"Bar 3: holdout IC difference {_num(reading['mean_ic_difference'])} over "
        f"{reading['sessions']} sessions; net top decile ensemble "
        f"{_num(top['ensemble']['net_return'])} vs baseline "
        f"{_num(top['baseline']['net_return'])}: {_yes(reading['bar3'])}.",
        "",
        _HEADER,
        _RULE,
        _fold_row(fold),
        _fold_row(record["secondary"]),
    ]
    return "\n".join(lines) + "\n"


def _fold_row(fold: Mapping[str, Any]) -> str:
    ic, spread = fold["ic"], fold["decile_spread"]
    return (
        f"| {fold['name']} | {fold['train_first']}..{fold['train_last']} | "
        f"{fold['test_first']}..{fold['test_last']} | {_num(_mean(ic['ensemble']))} | "
        f"{_num(_mean(ic['baseline']))} | {_num(spread['ensemble'])} / "
        f"{_num(spread['baseline'])} |"
    )


def _mean(values: Mapping[str, float]) -> float | None:
    return sum(values.values()) / len(values) if values else None


def _num(value: float | None) -> str:
    return "n/a" if value is None or value != value else f"{value:.4f}"


def _yes(flag: bool) -> str:
    return "yes" if flag else "no"
