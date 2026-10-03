"""Decision code, Tier A form laws (DEC-FORM-01..08), checked by code on every seat's typed output.

DEC-FORM-07 is the operator's rule (2026-10-03): ALL quant numbers are presented to and interpreted by
the deliberators. Every number in the packet must be read by each seat: copied, its scale named, its
meaning stated, its direction and weight given.

Each violation carries feedback that quotes the dictionary entry, so a retry (and later GEPA) is told
what the key means in this system, not just that it was wrong.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .book.entries import lookup
from .book.house_rules import RULES
from .outputs import Brief, Reading, Ruling

RAW_TO_SCORE = {
    "peBasicExclExtraTTM": "pe",
    "pbQuarterly": "pb",
    "roeTTM": "roe",
    "netProfitMarginTTM": "net_margin",
    "currentRatioQuarterly": "current_ratio",
    "totalDebt/totalEquityQuarterly": "debt_equity",
    "epsGrowthTTMYoy": "eps_growth",
    "revenueGrowthTTMYoy": "revenue_growth",
}
NON_MARKET_PILLARS = {"pm_gate", "order", "data_quality"}  # H4: process facts are never the basis
# A value stops at a separator OR an opening brace, so `quant_metrics=...{atr_pct=1.6` yields atr_pct too.
_PAIR = re.compile(r"([A-Za-z_][A-Za-z0-9_/]*)=([^\s,;{}\)\]]+)")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class Occ:
    value: str  # as rendered, without a trailing %
    raw: str  # as rendered
    block: str  # the line's leading words: "Analyst recommendation for X", "Scanner candidate ..."
    line: str


@dataclass(frozen=True)
class Violation:
    clause: str
    metric: str
    message: str
    feedback: str


def packet_values(context: str) -> dict[str, list[Occ]]:
    out: dict[str, list[Occ]] = {}
    for line in context.splitlines():
        block = line.split(":", 1)[0][:60]
        for k, v in _PAIR.findall(line):
            out.setdefault(k, []).append(Occ(v.rstrip("%"), v, block, line))
    return out


def _num(s: str) -> float | None:
    try:
        return float(s.rstrip("%"))
    except ValueError:
        return None


def _resolution(s: str) -> float:
    """Half a unit in the last rendered digit: '2.32' -> 0.005, '7.441e+04' -> 5."""
    mant, _, exp = s.rstrip("%").lower().partition("e")
    decimals = len(mant.split(".")[1]) if "." in mant else 0
    return 0.5 * 10 ** (-decimals) * 10 ** (int(exp) if exp else 0)


def _same(a: str, b: str) -> bool:
    fa, fb = _num(a), _num(b)
    if fa is None or fb is None:
        return a == b
    return abs(fa - fb) <= max(_resolution(a), _resolution(b)) + 1e-12


def required_numbers(context: str, evidence_only: bool = False) -> dict[str, list[list[Occ]]]:
    """Every number the packet presents, grouped: key -> groups of renderings of the same number.

    A key with two genuinely different numbers (the analyst's and the scanner's relative_strength,
    stop_pct as 4.64% and as 0.0464) yields two groups, and each must be read.
    """
    out: dict[str, list[list[Occ]]] = {}
    for k, occs in packet_values(context).items():
        entry = lookup(k)
        if evidence_only and entry is not None and entry.tier == "bookkeeping":
            continue
        for o in occs:
            numeric = bool(re.search(r"\d", o.value)) and not _DATE.match(o.value)
            absent_quant = o.value == "n/a" and entry is not None and entry.pillar not in NON_MARKET_PILLARS
            if not (numeric or absent_quant):
                continue
            groups = out.setdefault(k, [])
            for g in groups:
                if _same(g[0].value, o.value):
                    g.append(o)
                    break
            else:
                groups.append([o])
    return out


_BOOK_CACHE: dict = {}


def _book() -> dict:
    if not _BOOK_CACHE:
        from .book.dictionary import generate

        _BOOK_CACHE.update(generate())
    return _BOOK_CACHE


def entry_text(key: str) -> str:
    e = lookup(key)
    if e is None:
        return f"`{key}` is not a key of the packet dictionary."
    bands = next((x["bands"] for x in _book()["entries"] if x["key"] == e.key), "")
    txt = f"`{key}` [{e.scale}; {e.direction}]: {e.what}"
    if bands:
        txt += f" Bands: {bands}."
    if e.pitfall:
        txt += f" CAUTION: {e.pitfall}"
    return txt


def _unit_of(key: str, o: Occ) -> str | None:
    """The unit this particular rendering is in, for keys that appear in two units."""
    e = lookup(key)
    if e is None:
        return None
    if key == "relative_strength":
        return "fraction" if o.block.startswith("Scanner") else "percentage_points"
    if "fraction" in e.alt_scales and e.scale == "percent":
        return "percent" if o.raw.endswith("%") else "fraction"
    return e.scale


def _matches(r: Reading, o: Occ) -> bool:
    v = r.value.strip().rstrip("%")
    if v == o.value:
        return True
    got, have = _num(v), _num(o.value)
    if got is not None and have is not None and got == have:
        return True
    return bool(v) and _num(v) is None and v in o.line  # a compound value copied from its line


def _band(v: float, top: float) -> str | None:
    if v >= 0.6 * top:
        return "favourable"
    if v <= 0.4 * top:
        return "unfavourable"
    return None


def _expected_direction(key: str, value: float, pv: dict) -> str | None:
    """What the code's own scoring implies for a buy: favourable / unfavourable / None (no clear call)."""
    e = lookup(key)
    score_key = RAW_TO_SCORE.get(key) or (f"{key}_score" if f"{key}_score" in pv else None)
    if key == "relative_strength":
        score_key = "rs_score"
    if score_key and score_key in pv and score_key != key:
        v = _num(pv[score_key][0].value)
        return None if v is None else _band(v, 100)
    if e and e.scale == "sub_score_0_100":
        return _band(value, 100)
    if key in {"analyst_sentiment_score", "sentiment_score"}:
        return _band(value, 1)
    return None


# H7: contrarian oscillators (and their sub-scores) score oversold as bullish, but oversold in a downtrend is not
# support. Their direction for a buy is read WITH the trend, so they accept a set of directions, not one.
CONTRARIAN_RAW = {
    "rsi",
    "rsi2",
    "stochastic_k",
    "stochastic_d",
    "williams_r",
    "bollinger_position",
    "nw_deviation_pct",
}
CONTRARIAN_KEYS = CONTRARIAN_RAW | {f"{k}_score" for k in CONTRARIAN_RAW - {"stochastic_d"}}
TREND_SCORES = (
    "sma_distance_pct_score",
    "ema_spread_pct_score",
    "macd_histogram_score",
    "golden_cross_score",
)


def trend_state(pv: dict) -> str | None:
    """'up' / 'down' / 'mixed' from the code's own trend sub-scores (mean >= 60 / <= 40), None if absent."""
    vals = [_num(pv[k][0].value) for k in TREND_SCORES if k in pv]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    m = sum(vals) / len(vals)
    return "up" if m >= 60 else "down" if m <= 40 else "mixed"


def accepted_directions(key: str, value: float, pv: dict) -> set[str] | None:
    """The directions an expert may give this reading for a buy; None where the code makes no clear call."""
    if key == "stochastic_d" and "stochastic_k_score" in pv:
        e = _band(_num(pv["stochastic_k_score"][0].value) or 50, 100)
    else:
        e = _expected_direction(key, value, pv)
    if e is None:
        return None
    if key not in CONTRARIAN_KEYS:
        return {e}
    down = trend_state(pv) == "down"
    if e == "favourable":  # oversold: support only when the trend agrees (H7)
        return {"unfavourable", "neutral"} if down else {"favourable", "neutral"}
    return {"unfavourable"} if down else {"unfavourable", "neutral"}  # overbought


def check_reading(r: Reading, pv: dict, seat: str) -> list[Violation]:
    occs = pv.get(r.metric)
    if not occs:
        return [
            Violation(
                "DEC-FORM-01",
                r.metric,
                f"{seat}: `{r.metric}` is not a key in the packet",
                "Name the metric by its exact packet key (e.g. rsi_score), nothing else. "
                + entry_text(r.metric),
            )
        ]
    out: list[Violation] = []
    matched = [o for o in occs if _matches(r, o)]
    if not matched:
        out.append(
            Violation(
                "DEC-FORM-01",
                r.metric,
                f"{seat}: {r.metric}={r.value} but the packet says {', '.join(o.raw for o in occs)}",
                "Copy values exactly as written; do not round or recompute.",
            )
        )
    e = lookup(r.metric)
    if e is not None:
        allowed = {_unit_of(r.metric, o) for o in matched} if matched else {e.scale, *e.alt_scales}
        if r.metric == "relative_strength" and not matched:
            allowed |= {"fraction"}
        if r.scale not in allowed:
            out.append(
                Violation(
                    "DEC-FORM-02",
                    r.metric,
                    f"{seat}: read {r.metric}={r.value} as {r.scale}; here it is {'/'.join(sorted(allowed))}",
                    entry_text(r.metric),
                )
            )
    got = _num(r.value)
    if got is not None:
        acc = accepted_directions(r.metric, got, pv)
        if acc and r.direction != "neutral" and r.direction not in acc:
            out.append(
                Violation(
                    "DEC-FORM-02",
                    r.metric,
                    f"{seat}: called {r.metric}={r.value} {r.direction}; our scoring, read with the trend "
                    f"for contrarian oscillators (H7), makes it {' or '.join(sorted(acc))}",
                    entry_text(r.metric),
                )
            )
    return out


def check_complete(
    readings: list[Reading], context: str, seat: str, evidence_only: bool = False
) -> list[Violation]:
    """DEC-FORM-07: every number in the packet is read (operator rule, house rule H12)."""
    missing = []
    for key, groups in required_numbers(context, evidence_only).items():
        mine = [r for r in readings if r.metric == key]
        for g in groups:
            if not any(_matches(r, o) for r in mine for o in g):
                missing.append(f"{key}={g[0].raw}")
    if not missing:
        return []
    return [
        Violation(
            "DEC-FORM-07",
            ",".join(m.split("=")[0] for m in missing),
            f"{seat}: {len(missing)} numbers in the packet were not read",
            "House rule H12: read EVERY number in the packet, one reading each (a number that does not "
            "matter is still read, with weight low and why). Not yet read: " + "; ".join(missing),
        )
    ]


def _falsified(text: str, seat: str) -> list[Violation]:
    out = []
    for rule in RULES:
        for pat in rule.falsifiers:
            if re.search(pat, text, re.IGNORECASE):
                out.append(
                    Violation(
                        "DEC-FORM-06",
                        rule.id,
                        f"{seat}: statement contradicts house rule {rule.id}",
                        f"House rule {rule.id}: {rule.text}",
                    )
                )
    return out


def check_brief(b: Brief, context: str, seat: str, coverage: str = "evidence") -> list[Violation]:
    pv = packet_values(context)
    out = [v for r in b.readings for v in check_reading(r, pv, seat)]
    if coverage != "none":
        out += check_complete(b.readings, context, seat, evidence_only=coverage == "evidence")
    return out + _falsified(b.case + " " + " ".join(r.meaning_here for r in b.readings), seat)


def check_ruling(rl: Ruling, context: str, coverage: str = "all") -> list[Violation]:
    seat = "judge"
    pv = packet_values(context)
    out = [v for r in rl.own_readings for v in check_reading(r, pv, seat)]
    if coverage != "none":
        out += check_complete(rl.own_readings, context, seat, evidence_only=coverage == "evidence")
    by_key = {r.metric: r for r in rl.own_readings}
    decisive = [by_key[k] for k in rl.decisive if k in by_key]
    for k in rl.decisive:
        if k not in by_key:
            out.append(
                Violation(
                    "DEC-FORM-03",
                    k,
                    f"judge: decisive `{k}` is not among its own readings",
                    "Every decisive metric must be one of your own readings.",
                )
            )
    market = [
        r
        for r in decisive
        if r.weight == "high" and lookup(r.metric) and lookup(r.metric).pillar not in NON_MARKET_PILLARS
    ]
    if not market:
        out.append(
            Violation(
                "DEC-FORM-03",
                "-",
                "judge: no high-weight market reading among the decisive ones",
                "House rule H4: the ruling must rest on market evidence (technical, fundamental, "
                "relative strength, sentiment, volatility, regime). Process facts may support only.",
            )
        )
    if market and all(lookup(r.metric).status == "unproven" for r in market):
        out.append(
            Violation(
                "DEC-FORM-08",
                ",".join(r.metric for r in market),
                "judge: the ruling's market basis is only unproven model output",
                "House rule H13: an unproven number (e.g. the barrier forecast) is read and may support a "
                "ruling, but at least one PROVEN high-weight market reading must carry it.",
            )
        )
    if rl.ruling == "overturn" and not any(
        r.direction == "unfavourable" and r.weight == "high" for r in decisive
    ):
        out.append(
            Violation(
                "DEC-FORM-04",
                "-",
                "judge: overturn without a high-weight unfavourable decisive reading",
                "An overturn blocks a trade; name the market reading that makes it a bad buy.",
            )
        )
    if rl.ruling == "uphold" and not rl.rejected:
        out.append(
            Violation(
                "DEC-FORM-05",
                "-",
                "judge: uphold without answering the opposing case",
                "Name the challenger's strongest claim and why it does not hold.",
            )
        )
    text = " ".join(
        [
            rl.rationale,
            rl.market_conditions,
            *rl.accepted,
            *rl.rejected,
            *(r.meaning_here for r in rl.own_readings),
        ]
    )
    return out + _falsified(text, seat)
