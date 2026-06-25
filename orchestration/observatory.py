"""Pipeline observatory — render one run's per-stage I/O and check its invariants.

Agent: orchestration
Role: a human-legible "print" of a graph-pull run. For each stage: what triggered
      it, the values it produced, and whether each value holds its locked invariant
      (required / floor / ceiling / one-of) — OK vs WARN. Domain-agnostic: the
      stages and the invariants are supplied by the caller (platform/pack wall);
      this module only evaluates and renders. A checker that prints, not a printer
      that occasionally checks.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Check:
    """One locked invariant on a named observed value — the floor/ceiling/lock."""

    key: str
    kind: str  # "required" | "floor" | "ceiling" | "oneof"
    bound: float | tuple[str, ...] | None = None


@dataclass(frozen=True)
class StageView:
    """One stage's I/O for the observatory.

    ``outputs`` are the artifacts a human reads; ``observed`` are the scalar values
    the invariants are checked against.
    """

    name: str
    trigger: str
    observed: dict[str, object]
    reached: bool
    checks: tuple[Check, ...] = field(default_factory=tuple)
    outputs: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Breach:
    """A single invariant that did not hold — the thing for a human to inspect."""

    stage: str
    key: str
    detail: str


def _holds(value: object, check: Check) -> tuple[bool, str]:
    """Evaluate one invariant; return (ok, failure-detail)."""
    if check.kind == "required":
        return value is not None, "MISSING"
    if value is None:
        return False, "MISSING"
    if check.kind == "floor":
        actual, bound = float(value), float(check.bound)  # type: ignore[arg-type]
        return actual >= bound, f"{value} < floor {check.bound}"
    if check.kind == "ceiling":
        actual, bound = float(value), float(check.bound)  # type: ignore[arg-type]
        return actual <= bound, f"{value} > ceiling {check.bound}"
    return value in check.bound, f"{value} not in {check.bound}"  # type: ignore[operator]


def breaches(stage: StageView) -> tuple[Breach, ...]:
    """Every invariant a stage failed (an unreached stage counts as one breach)."""
    if not stage.reached:
        return (Breach(stage.name, "*stage*", "NOT REACHED"),)
    out: list[Breach] = []
    for check in stage.checks:
        ok, detail = _holds(stage.observed.get(check.key), check)
        if not ok:
            out.append(Breach(stage.name, check.key, detail))
    return tuple(out)


def render(stages: tuple[StageView, ...]) -> str:
    """Render the per-stage I/O panel + the breach summary — the human print."""
    lines: list[str] = []
    total: list[Breach] = []
    for stage in stages:
        stage_breaches = breaches(stage)
        if not stage.reached:
            lines.append(f"[{stage.name}]  <- {stage.trigger}   ... NOT REACHED")
        else:
            lines.append(f"[{stage.name}]  <- {stage.trigger}")
            lines.extend(f"  {line}" for line in stage.outputs)
            lines.extend(f"  WARN  {b.key}: {b.detail}" for b in stage_breaches)
        total.extend(stage_breaches)
    head = (
        "OK - all invariants hold"
        if not total
        else f"{len(total)} WARN - inspect above"
    )
    lines.append("")
    lines.append(f"OBSERVATORY  {head}")
    return "\n".join(lines)


# A cross-stage invariant: given each reached stage's observed values (keyed by stage
# name), return a Breach if the boundary is violated, else None. The pack supplies them.
CrossCheck = Callable[[dict[str, dict[str, object]]], "Breach | None"]


@dataclass(frozen=True)
class AcceptanceResult:
    """The PASS/FAIL verdict for one run — every per-stage and cross-stage breach."""

    passed: bool
    breaches: tuple[Breach, ...]


def accept(
    stages: tuple[StageView, ...], cross_checks: tuple[CrossCheck, ...]
) -> AcceptanceResult:
    """The Layer-3 verdict: PASS iff no stage and no cross-stage boundary failed."""
    found: list[Breach] = []
    for stage in stages:
        found.extend(breaches(stage))
    observed = {stage.name: stage.observed for stage in stages if stage.reached}
    for cross_check in cross_checks:
        breach = cross_check(observed)
        if breach is not None:
            found.append(breach)
    return AcceptanceResult(passed=not found, breaches=tuple(found))
