"""Language models for the lab: a deterministic fake ($0) and real providers through dspy.LM.

The fake exists to prove the bench end to end offline. It reads the packet like a careless expert on
its first attempt (a sub-score read as a ratio, a rounded value, a process-only basis, "revise blocks")
and corrects itself once it is given law feedback.
"""

from __future__ import annotations

import json
import os
import re

import dspy
from dspy.lm15 import Message, Response, TextPart, Usage, response_to_events

from .laws import _num, _unit_of, accepted_directions, packet_values, required_numbers

# $ per million tokens (input, output), from Anthropic's price list cached 2026-09-25.
PRICES = {
    "claude-opus-5-5": (4.0, 20.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-haiku-4-5": (1.0, 5.0),
}


def make_lm(spec: dict):
    """spec = {"model": "anthropic/claude-opus-5-5" | "openai/gpt-5.5" | "fake", "effort": ..., "max_tokens": ...}."""
    if spec["model"] == "fake":
        eng = FakeEngine()
        return dspy.LM("fake/expert", engine=eng, cache=False)
    # Without its key every call fails, and a failed call must never be graded as the model's answer.
    key = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}.get(spec["model"].split("/", 1)[0])
    if key and not os.environ.get(key):
        raise SystemExit(f"REFUSED: {spec['model']} needs {key} in the environment; no call was made.")
    kwargs = {"max_tokens": spec.get("max_tokens", 16000), "cache": False, "num_retries": 3}
    if spec.get("effort"):
        kwargs["reasoning_effort"] = spec["effort"]
    # Never pass temperature: Opus 5.5 rejects sampling parameters (DL-264 amendment 5).
    return dspy.LM(spec["model"], **kwargs)


def price(model: str) -> tuple[float, float] | None:
    return PRICES.get(model.split("/", 1)[-1])


# ---------------------------------------------------------------------------------- fake


def _field(text: str, name: str) -> str:
    m = re.search(rf"\[\[ ## {name} ## \]\]\n(.*?)(?=\n\[\[ ## |\Z)", text, re.S)
    return m.group(1).strip() if m else ""


def _r(pv, key, scale, direction, weight="high", meaning="", value=None):
    v = value if value is not None else (pv[key][0].value if key in pv else "n/a")
    return {
        "metric": key,
        "value": v,
        "scale": scale,
        "meaning_here": meaning or f"{key} as read",
        "direction": direction,
        "weight": weight,
    }


def _fav(pv, key, lo=40, hi=60):
    try:
        v = float(pv[key][0].value)
    except (KeyError, ValueError):
        return "neutral"
    return "favourable" if v >= hi else "unfavourable" if v <= lo else "neutral"


def _all_readings(packet: str, pv: dict, high: tuple[str, ...] = ()) -> list[dict]:
    """One reading per number in the packet, with the unit and direction our own code implies."""
    out = []
    for key, groups in required_numbers(packet).items():
        for g in groups:
            o = g[0]
            v = _num(o.value)
            acc = accepted_directions(key, v, pv) if v is not None else None
            d = sorted(acc - {"neutral"} or acc)[0] if acc else None
            out.append(
                {
                    "metric": key,
                    "value": o.raw,
                    "scale": _unit_of(key, o) or "raw_indicator",
                    "meaning_here": f"{key} as the dictionary defines it",
                    "direction": d or "neutral",
                    "weight": "high" if key in high else "low",
                }
            )
    return out


def fake_reply(system: str, user: str) -> str:
    packet = _field(user, "packet")
    feedback = _field(user, "law_feedback")
    pv = packet_values(packet)
    careful = feedback.startswith(("- DEC", "Your previous answer"))
    is_json = "Outputs will be a JSON object" in system
    if "JUDGE" in system:
        trend_down = (
            _fav(pv, "sma_distance_pct_score") == "unfavourable" and _fav(pv, "rs_score") == "unfavourable"
        )
        if careful:
            own = [
                _r(pv, "sma_distance_pct", "percent", _fav(pv, "sma_distance_pct_score")),
                _r(pv, "rs_score", "sub_score_0_100", _fav(pv, "rs_score")),
                _r(
                    pv,
                    "rsi_score",
                    "sub_score_0_100",
                    _fav(pv, "rsi_score"),
                    "low",
                    "contrarian: oversold is only support when the trend agrees (H7)",
                ),
            ]
            own = _all_readings(packet, pv, high=("sma_distance_pct", "rs_score"))
            ruling = {
                "own_readings": own,
                "decisive": ["sma_distance_pct", "rs_score"],
                "market_conditions": "regime and VIX as stated in the packet",
                "accepted": ["con: price is below its 200-day average"],
                "rejected": ["pro: oversold bounce, because the trend readings disagree"],
                "ruling": "overturn" if trend_down else "uphold",
                "rationale": "Trend and relative strength decide; oversold sub-scores do not outweigh them.",
            }
        else:
            own = [
                _r(pv, "value_portfolio_ratio", "ratio", "favourable"),
                _r(pv, "pe", "ratio", "favourable", meaning="a P/E ratio"),
            ]
            ruling = {
                "own_readings": own,
                "decisive": ["value_portfolio_ratio"],
                "market_conditions": "fine",
                "accepted": [],
                "rejected": [],
                "ruling": "uphold",
                "rationale": "All gates passed; a revise would block it anyway.",
            }
        out = {"ruling": ruling}
    else:
        side = "con" if ("CON deliberator" in system or "CHALLENGER" in system) else "pro"
        conf = pv["confidence_score"][0].value if "confidence_score" in pv else "0"
        reads = [
            _r(pv, "rsi_score", "sub_score_0_100", _fav(pv, "rsi_score"), "medium"),
            _r(pv, "sma_distance_pct", "percent", _fav(pv, "sma_distance_pct_score")),
            _r(
                pv,
                "confidence_score",
                "fraction_0_1",
                "favourable",
                "medium",
                value=conf if careful else str(round(float(conf), 2)),
            ),
        ]
        if not careful:
            reads.append(_r(pv, "pe", "ratio", "favourable", "medium", "a P/E ratio"))
        if careful:
            reads = _all_readings(packet, pv, high=("sma_distance_pct",))
        out = {
            "brief": {
                "readings": reads,
                "gaps": ["holdings are not in the packet"],
                "case": f"{side} case built on the readings above.",
            }
        }
    if is_json:
        return json.dumps(out)
    key, val = next(iter(out.items()))
    return f"[[ ## {key} ## ]]\n{json.dumps(val)}\n\n[[ ## completed ## ]]"


class FakeEngine:
    def complete(self, request):
        system = (
            request.system
            if isinstance(request.system, str)
            else "".join(p.text for p in (request.system or []))
        )
        user = request.messages[-1].text or ""
        text = fake_reply(system, user)
        n_in, n_out = (len(system) + len(user)) // 4, len(text) // 4
        return Response(
            id=None,
            model="fake",
            message=Message.assistant([TextPart(text)]),
            finish_reason="stop",
            usage=Usage(input_tokens=n_in, output_tokens=n_out, total_tokens=n_in + n_out),
        )

    def stream(self, request):
        return response_to_events(self.complete(request))

    def close(self):
        pass
