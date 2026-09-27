"""The S237 verdict: DL-237's bar, as amended at the return (R5), over clean sessions.

Agent: tooling
Role: pool clean Layer 1 rows into per-stage units and decide PASS, FAIL or
      INSUFFICIENT; non-clean sessions and PM passthroughs are never pooled.
External I/O: none.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

# DL-237: each stage agrees on at least 90 % of its clean units.
AGREEMENT_FLOOR = 0.90
# DL-237 amended / R5: scanner sessions, analyst tickers, PM judged recommendations.
FLOORS = {"scanner": 4, "analyst": 100, "pm": 10}
_FLOOR_UNITS = {
    "scanner": "clean sessions",
    "analyst": "tickers",
    "pm": "judged recommendations",
}
UNEXPLAINED = "unexplained"


def compute_verdict(
    rows: Iterable[Mapping[str, Any]], *, scanner_sessions: int
) -> dict[str, Any]:
    """Return the per-stage agreement, floors, unexplained count and verdict."""
    clean = [row for row in rows if row["clean"]]
    stages = {stage: _stage(clean, stage, judged=True) for stage in FLOORS}
    stages["scanner"]["sessions"] = scanner_sessions
    passthrough = _stage(clean, "pm", judged=False)
    stages["pm"]["hold_passthrough"] = {
        "units": passthrough["units"],
        "matches": passthrough["matches"],
    }
    observed = {
        "scanner": scanner_sessions,
        "analyst": stages["analyst"]["units"],
        "pm": stages["pm"]["units"],
    }
    for stage, block in stages.items():
        block["floor"] = {
            "required": FLOORS[stage],
            "observed": observed[stage],
            "unit": _FLOOR_UNITS[stage],
        }
    unexplained = sum(
        1 for row in clean if not row["match"] and row["cause"] == UNEXPLAINED
    )
    under = [
        stage
        for stage, block in stages.items()
        if block["units"] and block["agreement"] < AGREEMENT_FLOOR
    ]
    short = [stage for stage in stages if observed[stage] < FLOORS[stage]]
    reasons = [f"{stage} agreement under 90 %" for stage in under]
    reasons += [f"{unexplained} unexplained clean difference(s)"] if unexplained else []
    if reasons:
        verdict = "FAIL"
    elif short:
        verdict = "INSUFFICIENT"
        reasons = [f"{stage} below its floor" for stage in short]
    else:
        verdict = "PASS"
    return {
        "verdict": verdict,
        "reasons": reasons,
        "stages": stages,
        "unexplained": unexplained,
    }


def _stage(
    rows: list[Mapping[str, Any]], stage: str, *, judged: bool
) -> dict[str, Any]:
    units: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["stage"] == stage and bool(row["judged"]) is judged:
            units[(str(row["session"]), str(row["ticker"]))].append(row)
    matches = 0
    causes: Counter[str] = Counter()
    for unit in units.values():
        missed = [row for row in unit if not row["match"]]
        if missed:
            causes[str(missed[0]["cause"])] += 1
        else:
            matches += 1
    count = len(units)
    return {
        "units": count,
        "matches": matches,
        "agreement": matches / count if count else None,
        "causes": dict(sorted(causes.items())),
    }
