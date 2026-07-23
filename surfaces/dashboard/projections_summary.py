"""Dashboard verdict summary line and the shared projection value helpers.

Agent: surfaces
Role: turn a projected verdict + stages into the one sentence an operator reads at a
      glance, and hold the small typed accessors the verdict projection shares.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping


def _summary(
    verdict: str,
    stages: list[dict[str, object]],
    faults: list[dict[str, str]],
    *,
    confidence_bar: object = None,
) -> str:
    missing = _missing_stage(stages)
    if missing is not None:
        complete = sum(bool(stage.get("reached")) for stage in stages)
        return (
            f"Run stopped before {missing} — {complete}/{len(stages)} stages completed."
        )
    non_acceptance = next(
        (fault["message"] for fault in faults if fault["code"] != "acceptance"), None
    )
    if non_acceptance is not None:
        return f"Attention needed: {non_acceptance.lower()}."
    if verdict == "NO_TRADE":
        rejected = _observed(stages, "analyst", "rejected")
        noun = "candidate" if rejected == 1 else "candidates"
        bar = (
            f" ({float(confidence_bar):g})"
            if isinstance(confidence_bar, int | float)
            else ""
        )
        return f"{rejected} {noun} below confidence bar{bar}"
    if verdict == "UNPROVEN":
        submitted = _observed(stages, "execution", "submitted")
        noun = "order" if submitted == 1 else "orders"
        return f"{submitted} {noun} placed, none filled yet"
    if verdict == "PASS":
        scored = _observed(stages, "analyst", "scored")
        submitted = _observed(stages, "execution", "submitted")
        order_noun = "order" if submitted == 1 else "orders"
        candidate_noun = "candidate" if scored == 1 else "candidates"
        return f"{submitted} {order_noun}, {scored} {candidate_noun}"
    return "Acceptance failed."


def _missing_stage(stages: list[dict[str, object]]) -> str | None:
    row = next((stage for stage in stages if not stage.get("reached")), None)
    return str(row["name"]) if row is not None else None


def _observed(stages: list[dict[str, object]], name: str, key: str) -> int:
    row = next((stage for stage in stages if stage.get("name") == name), {})
    observed = row.get("observed", {})
    return _as_int(observed.get(key) if isinstance(observed, Mapping) else 0)


def _nested_value(
    source: Mapping[str, object], name: str, default: object, *, key: str | None = None
) -> object:
    value = source.get(name, default)
    if key is not None:
        return value.get(key, default) if isinstance(value, Mapping) else default
    return value


def _as_int(value: object) -> int:
    return int(value) if isinstance(value, (int, float)) else 0
