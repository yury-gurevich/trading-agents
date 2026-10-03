"""A fake explainer ($0) in two qualities, to prove the grader can tell understanding from its absence.

`good` answers from the answer keys (so it must pass: this proves the parse -> grade path, nothing about a
model). `flawed` makes the errors a fluent but untrained reader makes: sub-scores read as ratios, contrarian
oscillators read the naive way round, no sub-score mapping, technical_score as a plain mean with no
relative-strength blend, bookkeeping skipped, and no real interactions. It must fail, on those checks.
`hedging` is `good` with every direction "neutral": right about everything, committed to nothing. It must
fail on direction.
"""

from __future__ import annotations

import json
import re

from dspy.lm15 import Message, Response, TextPart, Usage

from .engines import _field
from .explain_grade import (
    EXPECTED_INTERACTIONS,
    allowed_concepts,
    expected_derivations,
    expected_pillars,
    implied_sub_score,
)
from .laws import _expected_direction, _num, _unit_of, packet_values, required_numbers

_INPUTS = {
    "technical_score": "indicator sub-scores, rs_score",
    "fundamental_score": "pe, pb, roe, net_margin, current_ratio, debt_equity, eps_growth, revenue_growth",
    "composite_score": "technical_score, fundamental_score, sentiment_score",
    "confidence_score": "composite_score",
    "applied_stop_pct": "atr_pct",
    "reward_risk_ratio": "applied_target_pct, applied_stop_pct",
}


def _interp(key, o, pv, flawed: bool, hedging: bool = False) -> dict:
    v = _num(o.value)
    concepts = allowed_concepts(key) or {"bookkeeping"}
    concept = sorted(concepts - {"bookkeeping"} or concepts)[0]
    direction = (_expected_direction(key, v, pv) if v is not None else None) or "neutral"
    implied = implied_sub_score(key, v, pv, o.block) if v is not None else None
    scale = _unit_of(key, o) or "raw_indicator"
    if flawed:
        if scale == "sub_score_0_100":
            scale = "ratio"  # `pe=60` read as a P/E of 60
        if key in ("rsi", "stochastic_k", "williams_r", "bollinger_position", "rsi2") and v is not None:
            direction = "favourable" if v > 50 else "unfavourable"  # momentum read, not contrarian
        implied = None
    if hedging:
        direction = "neutral"  # right about everything, committed to nothing
    return {
        "metric": key,
        "value": o.raw,
        "scale": scale,
        "concept": concept,
        "meaning_here": f"{key} as the dictionary defines it",
        "direction": direction,
        "implied_sub_score": implied,
    }


def explain_reply(packet: str, case: str, evidence_only: bool, flawed: bool, hedging: bool = False) -> dict:
    pv = packet_values(packet)
    req = required_numbers(packet, evidence_only=evidence_only or flawed)
    interps = [_interp(k, g[0], pv, flawed, hedging) for k, groups in req.items() for g in groups]
    derivs = expected_derivations(pv)
    if flawed and "technical_score" in derivs:
        derivs["technical_score"] = derivs["technical_score"] / 0.8 * 0.85  # a plain mean, no 80/20 blend
        derivs.pop("confidence_score", None)
    derivations = [
        {"name": n, "inputs": _INPUTS[n].split(", "), "rule": "per the dictionary", "computed": x}
        for n, x in derivs.items()
    ]
    pillars = [
        {"pillar": p, "verdict": "mixed" if flawed else sorted(ok - {"neutral"})[0], "because": [p]}
        for p, ok in expected_pillars(pv).items()
    ]
    interactions = []
    for a, b, rels in [] if flawed else EXPECTED_INTERACTIONS.get(case, []):
        ka, kb = sorted(k for k in a if k in pv) or sorted(a), sorted(k for k in b if k in pv) or sorted(b)
        interactions.append(
            {"keys_a": ka[:3], "keys_b": kb[:3], "relation": sorted(rels)[0], "meaning": "read together"}
        )
    if flawed:
        interactions = [
            {
                "keys_a": ["composite_score"],
                "keys_b": ["confidence_score"],
                "relation": "confirms",
                "meaning": "both ok",
            }
        ]
    return {
        "interpretations": interps,
        "derivations": derivations,
        "pillars": pillars,
        "interactions": interactions,
        "situation": "fake situation",
        "overall": "mixed",
    }


class ExplainFakeEngine:
    def __init__(self, quality: str, tickers: dict[str, str]):
        self.flawed, self.hedging, self.tickers = (
            quality == "flawed",
            quality == "hedging",
            tickers,
        )  # ticker -> case name (never sent to a model)

    def complete(self, request):
        system = (
            request.system
            if isinstance(request.system, str)
            else "".join(p.text for p in request.system or [])
        )
        user = request.messages[-1].text or ""
        packet, decision = _field(user, "packet"), _field(user, "decision")
        case = next((n for t, n in self.tickers.items() if re.search(rf"\b{t}\b", decision)), "")
        evidence_only = "JUDGE" not in system
        out = explain_reply(packet, case, evidence_only, self.flawed, self.hedging)
        text = f"[[ ## explanation ## ]]\n{json.dumps(out)}\n\n[[ ## completed ## ]]"
        n_in, n_out = (len(system) + len(user)) // 4, len(text) // 4
        return Response(
            id=None,
            model="fake",
            message=Message.assistant([TextPart(text)]),
            finish_reason="stop",
            usage=Usage(input_tokens=n_in, output_tokens=n_out, total_tokens=n_in + n_out),
        )

    def stream(self, request):
        from dspy.lm15 import response_to_events

        return response_to_events(self.complete(request))

    def close(self):
        pass
