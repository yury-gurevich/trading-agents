"""Fakes ($0) that prove the explain grader and the compile step, never a model.

Explainer qualities:
- `good` answers from the answer keys. It must pass; this proves the parse -> grade path.
- `flawed` makes the errors a fluent but untrained reader makes, all at once. Sub-scores are read as
  ratios, contrarian oscillators the naive way round, with no sub-score mapping. technical_score is
  taken as a plain mean with no relative-strength blend, bookkeeping is skipped, and there are no real
  interactions. It must fail on those checks.
- `hedging` is `good` with every direction "neutral": right about everything, committed to nothing.
  It must fail on direction.
- `instructed` makes each `flawed` error UNLESS its instructions carry the matching lesson
  (`LESSONS`). It is the student the compile step must improve.

`FakeReflection` stands in for GEPA's reflection model. For each check the metric's feedback names
(`CHECK:` headers), it appends that lesson to the current instruction. It proves the loop: feedback
leads to an instruction, which changes the behaviour, which shows in the held-out score. It says
nothing about what a real reflection model would write.
"""

from __future__ import annotations

import json
import re

from dspy.lm15 import Message, Response, TextPart, Usage, response_to_events

from .engines import _field
from .explain_grade import (
    EXPECTED_INTERACTIONS,
    allowed_concepts,
    expected_derivations,
    expected_pillars,
    implied_sub_score,
)
from .laws import _num, _unit_of, accepted_directions, packet_values, required_numbers

FLAWS = ("coverage", "scale", "contrarian", "implied", "derivations", "pillars", "interactions")
# check header in the metric's feedback -> the flaw it reveals -> the lesson that removes it
LESSONS = {
    "coverage": "Read bookkeeping numbers too when your scope says EVERY number.",
    "scale": "Keys the dictionary marks sub_score_0_100 (pe, roe, ...) are 0-100 scores, never ratios.",
    "contrarian": "Contrarian oscillators (RSI, stochastic, Williams %R, Bollinger) score oversold as "
    "favourable: take their direction from the sub-score bands, not from momentum intuition.",
    "implied": "For every raw indicator, look up its bands and state the sub-score they assign.",
    "derivations": "technical_score is 80 % the indicator sub-score mean plus 20 % rs_score; confidence is "
    "0.3 + 0.6 x composite.",
    "pillars": "Give each pillar the verdict its own score's band implies.",
    "interactions": "Name where trend and contrarian readings, valuation and quality, or risk and regime "
    "disagree, and what that means together.",
}
CHECK_TO_FLAW = {
    "COVERAGE": "coverage",
    "SCALE": "scale",
    "DIRECTION": "contrarian",
    "CRITICAL": "contrarian",
    "SUB-SCORE": "implied",
    "DERIVATIONS": "derivations",
    "PILLARS": "pillars",
    "INTERACTIONS": "interactions",
}

_INPUTS = {
    "technical_score": "indicator sub-scores, rs_score",
    "fundamental_score": "pe, pb, roe, net_margin, current_ratio, debt_equity, eps_growth, revenue_growth",
    "composite_score": "technical_score, fundamental_score, sentiment_score",
    "confidence_score": "composite_score",
    "applied_stop_pct": "atr_pct",
    "reward_risk_ratio": "applied_target_pct, applied_stop_pct",
}


def _interp(key, o, pv, flaws: set[str], hedging: bool) -> dict:
    v = _num(o.value)
    concepts = allowed_concepts(key) or {"bookkeeping"}
    concept = sorted(concepts - {"bookkeeping"} or concepts)[0]
    acc = accepted_directions(key, v, pv) if v is not None else None
    direction = sorted(acc - {"neutral"} or acc)[0] if acc else "neutral"
    implied = implied_sub_score(key, v, pv, o.block) if v is not None else None
    scale = _unit_of(key, o) or "raw_indicator"
    if "scale" in flaws and scale == "sub_score_0_100":
        scale = "ratio"  # `pe=60` read as a P/E of 60
    if "contrarian" in flaws and key in ("rsi", "stochastic_k", "williams_r", "bollinger_position", "rsi2"):
        if v is not None:
            direction = "favourable" if v > 50 else "unfavourable"  # momentum read, not contrarian
    if "implied" in flaws:
        implied = None
    if hedging:
        direction = "neutral"
    return {
        "metric": key,
        "value": o.raw,
        "scale": scale,
        "concept": concept,
        "meaning_here": f"{key} as the dictionary defines it",
        "direction": direction,
        "implied_sub_score": implied,
    }


def explain_reply(
    packet: str, case: str, evidence_only: bool, flaws: set[str], hedging: bool = False
) -> dict:
    pv = packet_values(packet)
    req = required_numbers(packet, evidence_only=evidence_only or "coverage" in flaws)
    interps = [_interp(k, g[0], pv, flaws, hedging) for k, groups in req.items() for g in groups]
    derivs = expected_derivations(pv)
    if "derivations" in flaws and "technical_score" in derivs:
        derivs["technical_score"] = derivs["technical_score"] / 0.8 * 0.85  # a plain mean, no 80/20 blend
        derivs.pop("confidence_score", None)
    derivations = [
        {"name": n, "inputs": _INPUTS[n].split(", "), "rule": "per the dictionary", "computed": x}
        for n, x in derivs.items()
    ]
    pillars = [
        {
            "pillar": p,
            "verdict": "mixed" if "pillars" in flaws else sorted(ok - {"neutral"})[0],
            "because": [p],
        }
        for p, ok in expected_pillars(pv).items()
    ]
    interactions = [
        {
            "keys_a": ["composite_score"],
            "keys_b": ["confidence_score"],
            "relation": "confirms",
            "meaning": "both ok",
        }
    ]
    if "interactions" not in flaws:
        interactions = []
        for a, b, rels in EXPECTED_INTERACTIONS.get(case, []):
            ka, kb = (
                sorted(k for k in a if k in pv) or sorted(a),
                sorted(k for k in b if k in pv) or sorted(b),
            )
            interactions.append(
                {"keys_a": ka[:3], "keys_b": kb[:3], "relation": sorted(rels)[0], "meaning": "read together"}
            )
    return {
        "interpretations": interps,
        "derivations": derivations,
        "pillars": pillars,
        "interactions": interactions,
        "situation": "fake situation",
        "overall": "mixed",
    }


def _text(request) -> tuple[str, str]:
    system = (
        request.system if isinstance(request.system, str) else "".join(p.text for p in request.system or [])
    )
    return system, request.messages[-1].text or ""


def _response(text: str, n_in: int) -> Response:
    n_out = len(text) // 4
    return Response(
        id=None,
        model="fake",
        message=Message.assistant([TextPart(text)]),
        finish_reason="stop",
        usage=Usage(input_tokens=n_in, output_tokens=n_out, total_tokens=n_in + n_out),
    )


class _Engine:
    def stream(self, request):
        return response_to_events(self.complete(request))

    def close(self):
        pass


class ExplainFakeEngine(_Engine):
    def __init__(self, quality: str, tickers: dict[str, str]):
        self.quality, self.tickers = quality, tickers  # ticker -> case name (never sent to a model)

    def flaws(self, system: str) -> set[str]:
        if self.quality == "flawed":
            return set(FLAWS)
        if self.quality == "instructed":
            objective = system.split("your objective is:")[-1].split("=== REFERENCE BOOK")[0]
            return {f for f in FLAWS if LESSONS[f] not in objective}
        return set()

    def complete(self, request):
        system, user = _text(request)
        packet, decision = _field(user, "packet"), _field(user, "decision")
        case = next((n for t, n in self.tickers.items() if re.search(rf"\b{t}\b", decision)), "")
        out = explain_reply(
            packet, case, "JUDGE" not in system, self.flaws(system), self.quality == "hedging"
        )
        text = f"[[ ## explanation ## ]]\n{json.dumps(out)}\n\n[[ ## completed ## ]]"
        return _response(text, (len(system) + len(user)) // 4)


class FakeReflection(_Engine):
    """GEPA's reflection model, scripted: current instruction + the lesson for each check the feedback names."""

    def complete(self, request):
        system, user = _text(request)
        prompt = system + user
        current = prompt.split("```", 2)[1].strip() if prompt.count("```") >= 2 else ""
        named = {flaw for check, flaw in CHECK_TO_FLAW.items() if re.search(rf"^{check}:", prompt, re.M)}
        new = current + "".join(f" {LESSONS[f]}" for f in FLAWS if f in named and LESSONS[f] not in current)
        return _response(f"```\n{new}\n```", len(prompt) // 4)
