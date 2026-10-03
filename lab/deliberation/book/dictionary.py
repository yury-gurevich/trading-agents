"""Generate book Part I from the code: entries + bands probed from the scorers + fleet weights.

Run:  PYTHONPATH=. uv run --frozen --extra optimizer python -m lab.deliberation.book.dictionary
Writes book/generated/dictionary.md (what the model reads) and dictionary.json (what checkers read).
"""

from __future__ import annotations

import json
from pathlib import Path

from agents.analyst.domain import (
    fundamental_rules as fr,
)
from agents.analyst.domain import (
    relative_strength as rsm,
)
from agents.analyst.domain import (
    technical_rules as tr,
)
from agents.analyst.domain import (
    technical_rules_event as tre,
)
from agents.analyst.domain import (
    technical_rules_pattern as trp,
)
from agents.analyst.domain import (
    technical_rules_range as trr,
)

from ..fleet import fleet_settings
from .entries import ENTRIES

GEN = Path(__file__).parent / "generated"


def _steps(fn, lo: float, hi: float, step: float, unit: str = "") -> str:
    """Probe a one-argument scorer over a grid; bisect each cut; describe the step function exactly."""
    n = round((hi - lo) / step)
    xs = [lo + i * step for i in range(n + 1)]
    cuts: list[tuple[float, bool, float]] = []  # (cut value, cut belongs to upper band, upper score)
    prev_x, prev_s = xs[0], fn(xs[0])
    first = prev_s
    for x in xs[1:]:
        s = fn(x)
        if s != prev_s:
            a, b = prev_x, x
            for _ in range(60):
                m = (a + b) / 2
                a, b = (m, b) if fn(m) == prev_s else (a, m)
            c = round(b, 6) + 0.0
            cuts.append((c, fn(c) == s, s))
        prev_x, prev_s = x, s
    if not cuts:
        return f"any -> {first:g}"
    parts = [f"x {'<' if cuts[0][1] else '<='} {cuts[0][0]:g}{unit} -> {first:g}"]
    for i, (c, upper, s) in enumerate(cuts):
        lo_txt = f"{'>=' if upper else '>'} {c:g}{unit}"
        if i + 1 < len(cuts):
            c2, up2, _ = cuts[i + 1]
            parts.append(f"x {lo_txt} and {'<' if up2 else '<='} {c2:g}{unit} -> {s:g}")
        else:
            parts.append(f"x {lo_txt} -> {s:g}")
    return "; ".join(parts)


def _fund(name: str) -> str:
    for rule_name, keys, require_positive, bands, default in fr._FUNDAMENTAL_RULES:
        if rule_name == name:
            ops = {"lt": "<", "le": "<=", "gt": ">"}
            txt = "; ".join(f"raw {ops[op]} {thr:g} -> {score:g}" for op, thr, score in bands)
            pos = " Non-positive raw values are skipped (no key)" if require_positive else ""
            return f"raw = {' or '.join(keys)}; first match wins: {txt}; otherwise -> {default:g}{pos}"
    raise KeyError(name)


PROBES = {
    "rsi": lambda: _steps(tr.score_rsi, 0, 100, 0.1),
    "rsi2": lambda: _steps(tre.score_rsi2, 0, 100, 0.1),
    "bollinger": lambda: _steps(tr.score_bollinger, 0, 1, 0.001),
    "sma": lambda: _steps(tr.score_sma_distance, -40, 40, 0.01, "%"),
    "ema": lambda: _steps(tr.score_ema_crossover, -10, 10, 0.01, "%"),
    "atr": lambda: _steps(trr.score_atr, 0, 12, 0.01, "%"),
    "williams": lambda: _steps(trr.score_williams, -100, 0, 0.1),
    "chop": lambda: _steps(trr.score_choppiness, 0, 100, 0.1),
    "nw": lambda: _steps(trp.score_kernel, -10, 10, 0.01, "%"),
    "rs": lambda: _steps(rsm.score_relative_strength, -40, 40, 0.01, " pp"),
    "macd": lambda: (
        f"line>0 and histogram>0 -> {tr._MACD_SCORES[0]:g}; histogram>0 only -> {tr._MACD_SCORES[1]:g}; "
        f"line<0 and histogram<0 -> {tr._MACD_SCORES[2]:g}; otherwise -> {tr._MACD_SCORES[3]:g}"
    ),
    "stochastic": lambda: (
        f"%K and %D both < {trr._STOCH_OVERSOLD:g} -> {trr._STOCH_SCORES[0]:g}; %K < "
        f"{trr._STOCH_OVERSOLD:g} -> {trr._STOCH_SCORES[1]:g}; %K and %D both > {trr._STOCH_OVERBOUGHT:g} -> "
        f"{trr._STOCH_SCORES[2]:g}; %K > {trr._STOCH_OVERBOUGHT:g} -> {trr._STOCH_SCORES[3]:g}; otherwise 50"
    ),
    "golden": lambda: f"golden cross -> {tre._GOLDEN_SCORES[0]:g}; otherwise -> {tre._GOLDEN_SCORES[1]:g}",
    "obv": lambda: f"OBV above its signal -> {tre._OBV_SCORES[0]:g}; otherwise -> {tre._OBV_SCORES[1]:g}",
    "turnaround": lambda: f"signal -> {trp._TURNAROUND_SIGNAL:g}; otherwise -> 50",
}


def generate() -> dict:
    _, analyst, pm, provider = fleet_settings()
    fleet = {
        "composite_weights": {
            "technical": analyst.technical_weight,
            "fundamental": analyst.fundamental_weight,
            "sentiment": analyst.sentiment_weight,
        },
        "technical_rs_blend": analyst.relative_strength_weight,
        "confidence": f"{analyst.confidence_floor} + {analyst.confidence_span} x composite_score",
        "base_min_confidence": provider.base_min_confidence,
        "stop_target_mode": analyst.stop_target_mode,
        "pm_max_position_pct": str(pm.max_position_pct),
        "pm_min_reward_risk_ratio": pm.min_reward_risk_ratio,
    }
    entries = []
    for e in ENTRIES:
        bands = ""
        if e.probe.startswith("fund:"):
            bands = _fund(e.probe[5:])
        elif e.probe:
            bands = PROBES[e.probe]()
        entries.append({**e.__dict__, "bands": bands})
    return {"fleet": fleet, "entries": entries}


def render(book: dict) -> str:
    f = book["fleet"]
    lines = [
        "# Dictionary of the evidence packet (book Part I, generated from the code)",
        "",
        "Every value below means what OUR code computes, not its textbook meaning.",
        f"Composite = weighted mean of present pillars {f['composite_weights']}; technical_score = "
        f"{1 - f['technical_rs_blend']:.0%} indicator mean + {f['technical_rs_blend']:.0%} rs_score; "
        f"confidence = {f['confidence']}; buy floor = {f['base_min_confidence']}.",
        "",
    ]
    for group in dict.fromkeys(e["pillar"] for e in book["entries"]):
        lines.append(f"## {group}")
        for e in (x for x in book["entries"] if x["pillar"] == group):
            line = f"- `{e['key']}` [{e['scale']}; {e['direction']}]: {e['what']}"
            if e["bands"]:
                line += f" Bands: {e['bands']}."
            if e["pitfall"]:
                line += f" CAUTION: {e['pitfall']}"
            lines.append(line)
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    GEN.mkdir(exist_ok=True)
    book = generate()
    (GEN / "dictionary.json").write_text(json.dumps(book, indent=1) + "\n")
    text = render(book)
    (GEN / "dictionary.md").write_text(text + "\n")
    print(f"{len(book['entries'])} entries, {len(text)} chars (~{len(text) // 4} tokens)")


if __name__ == "__main__":
    main()
