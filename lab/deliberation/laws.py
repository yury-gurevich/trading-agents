"""Decision code, Tier A form laws (DEC-FORM-01..06), checked by code on every seat's typed output.

Each violation carries feedback that quotes the dictionary entry, so a retry (and later GEPA) is told
what the key means in this system, not just that it was wrong.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .book.entries import ENTRIES
from .book.house_rules import RULES
from .outputs import Brief, Reading, Ruling

DICT = {e.key: e for e in ENTRIES}
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
NON_MARKET_PILLARS = {"pm_gate"}  # H4: process facts are never the basis
_PAIR = re.compile(r"([A-Za-z_][A-Za-z0-9_/]*)=([^\s,;}\)\]]+)")


@dataclass(frozen=True)
class Violation:
    clause: str
    metric: str
    message: str
    feedback: str


def packet_values(context: str) -> dict[str, list[tuple[str, str]]]:
    """key -> [(value as rendered, block)], block = the line's leading words (Analyst, Scanner, ...)."""
    out: dict[str, list[tuple[str, str]]] = {}
    for line in context.splitlines():
        block = line.split(":", 1)[0][:40]
        for k, v in _PAIR.findall(line):
            out.setdefault(k, []).append((v.rstrip("%"), block))
    return out


def _entry_text(key: str) -> str:
    e = DICT.get(key)
    if e is None:
        return f"`{key}` is not a key of the packet dictionary."
    bands = next((x["bands"] for x in _BOOK()["entries"] if x["key"] == key), "")
    txt = f"`{key}` [{e.scale}; {e.direction}]: {e.what}"
    if bands:
        txt += f" Bands: {bands}."
    if e.pitfall:
        txt += f" CAUTION: {e.pitfall}"
    return txt


_BOOK_CACHE: dict = {}


def _BOOK() -> dict:  # noqa: N802
    if not _BOOK_CACHE:
        from .book.dictionary import generate

        _BOOK_CACHE.update(generate())
    return _BOOK_CACHE


def _num(s: str) -> float | None:
    try:
        return float(s.rstrip("%"))
    except ValueError:
        return None


def _expected_direction(key: str, value: float, pv: dict) -> str | None:
    """What the code's own scoring implies for a buy: favourable / unfavourable / None (no clear call)."""
    e = DICT.get(key)
    score_key = RAW_TO_SCORE.get(key) or (f"{key}_score" if f"{key}_score" in pv else None)
    if key == "relative_strength":
        score_key = "rs_score"
    if score_key and score_key in pv and score_key != key:
        v = _num(pv[score_key][0][0])
        return None if v is None else _band(v, 100)
    if e and e.scale == "sub_score_0_100":
        return _band(value, 100)
    if key in {"analyst_sentiment_score", "sentiment_score"}:
        return _band(value, 1)
    return None


def _band(v: float, top: float) -> str | None:
    if v >= 0.6 * top:
        return "favourable"
    if v <= 0.4 * top:
        return "unfavourable"
    return None


def check_reading(r: Reading, pv: dict, seat: str) -> list[Violation]:
    out: list[Violation] = []
    occ = pv.get(r.metric)
    if not occ:
        return [
            Violation(
                "DEC-FORM-01",
                r.metric,
                f"{seat}: `{r.metric}` is not a key in the packet",
                "Name the metric by its exact packet key (e.g. rsi_score), nothing else. "
                + _entry_text(r.metric),
            )
        ]
    got = _num(r.value)
    match = [(v, b) for v, b in occ if v == r.value.rstrip("%") or (got is not None and _num(v) == got)]
    if not match:
        out.append(
            Violation(
                "DEC-FORM-01",
                r.metric,
                f"{seat}: {r.metric}={r.value} but the packet says {', '.join(v for v, _ in occ)}",
                "Copy values exactly as written; do not round or recompute.",
            )
        )
    e = DICT.get(r.metric)
    if e is not None:
        allowed = {e.scale}
        if r.metric == "relative_strength" and any(b.startswith("Scanner") for _, b in (match or occ)):
            allowed.add("fraction")
        if r.scale not in allowed:
            out.append(
                Violation(
                    "DEC-FORM-02",
                    r.metric,
                    f"{seat}: read {r.metric} as {r.scale}; it is {'/'.join(sorted(allowed))}",
                    _entry_text(r.metric),
                )
            )
    if got is not None:
        exp = _expected_direction(r.metric, got, pv)
        if exp and r.direction != "neutral" and r.direction != exp:
            out.append(
                Violation(
                    "DEC-FORM-02",
                    r.metric,
                    f"{seat}: called {r.metric}={r.value} {r.direction}; our scoring makes it {exp}",
                    _entry_text(r.metric),
                )
            )
    return out


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


def check_brief(b: Brief, context: str, seat: str) -> list[Violation]:
    pv = packet_values(context)
    out = [v for r in b.readings for v in check_reading(r, pv, seat)]
    return out + _falsified(b.case + " " + " ".join(r.meaning_here for r in b.readings), seat)


def check_ruling(rl: Ruling, context: str) -> list[Violation]:
    seat = "judge"
    pv = packet_values(context)
    out = [v for r in rl.own_readings for v in check_reading(r, pv, seat)]
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
        if r.weight == "high" and r.metric in DICT and DICT[r.metric].pillar not in NON_MARKET_PILLARS
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
