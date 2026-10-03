"""Answer keys from the fleet's code, and the grader for iteration 1's explanations.

Everything that can be computed is computed: concept families, units, directions, the sub-score a raw
indicator maps to (by calling the analyst's own scorers), the six aggregates (by the analyst's own
formulas), the pillar verdicts. The expected INTERACTIONS per scenario are the planner's draft for the
operator to approve; they are the only hand-written key.
"""

from __future__ import annotations

from agents.analyst.domain import fundamental_rules as fr
from agents.analyst.domain import relative_strength as rsm
from agents.analyst.domain import technical_rules as tr
from agents.analyst.domain import technical_rules_event as tre
from agents.analyst.domain import technical_rules_pattern as trp
from agents.analyst.domain import technical_rules_range as trr

from .book.entries import lookup
from .explain_models import Explanation
from .laws import (
    CONTRARIAN_KEYS,
    CONTRARIAN_RAW,
    _matches,
    _num,
    _unit_of,
    accepted_directions,
    packet_values,
    required_numbers,
)

# ---- (a) concept families -------------------------------------------------------------------------------
_C = {
    "momentum_oscillator": "rsi rsi_score rsi2 rsi2_score stochastic_k stochastic_k_score stochastic_d williams_r "
    "williams_r_score",
    "trend": "sma_distance_pct sma_distance_pct_score ema_spread_pct ema_spread_pct_score macd_histogram "
    "macd_histogram_score macd_line_price macd_signal_price golden_cross golden_cross_score sma_N_usd ema_N_usd "
    "choppiness choppiness_score",
    "volatility": "atr_pct atr_pct_score decision_atr_pct bollinger_upper_usd bollinger_lower_usd "
    "bollinger_middle_usd bollinger_position bollinger_position_score",
    "mean_reversion": "nw_deviation_pct nw_deviation_pct_score bollinger_position bollinger_position_score",
    "volume_flow": "obv obv_score obv_signal volume_shares average_volume",
    "pattern": "turnaround turnaround_score",
    "composite_score": "technical_score fundamental_score composite_score confidence_score confidence",
    "relative_strength": "relative_strength rs_score scanner_score",
    "valuation": "pe pb peBasicExclExtraTTM pbQuarterly",
    "profitability": "roe net_margin roeTTM netProfitMarginTTM",
    "growth": "eps_growth revenue_growth epsGrowthTTMYoy revenueGrowthTTMYoy",
    "balance_sheet": "current_ratio debt_equity currentRatioQuarterly totalDebt/totalEquityQuarterly",
    "sentiment": "analyst_sentiment_score sentiment_score provider_sentiment_score sentiment_articles "
    "sentiment_batch_weighted_articles sentiment_positive_words sentiment_negative_words",
    "risk_management": "suggested_stop_pct suggested_target_pct applied_stop_pct applied_target_pct stop_pct "
    "target_pct flat_stop_pct flat_target_pct scaled_stop_pct scaled_target_pct flat_reward_risk_ratio "
    "scaled_reward_risk_ratio applied_reward_risk_ratio value_reward_risk_ratio favorable_excursion_pct "
    "favorable_excursion_horizon_days decision_atr_pct",
    "market_regime": "label vix_index base_min_confidence_score base_stop_loss_pct base_take_profit_pct "
    "base_max_holding_days",
    "event_risk": "days_to_earnings",
    "systematic_risk": "beta",
    "liquidity": "average_volume volume_shares",
    "concentration": "value_sector_exposure_ratio value_cluster_exposure_ratio value_sector_issuers "
    "existing_sector_issuers held_sector_value_usd cluster_value_usd cluster_weight_total correlated_issuers "
    "below_threshold_top existing_issuer_value_usd holding_TICKER_value_usd deployed_usd deployed_portfolio_usd "
    "value_positions",
    "position_sizing": "value_portfolio_ratio quantity_shares position_value_usd portfolio_value_usd "
    "account_equity_usd account_cash_usd buying_power_usd value_order_cost_usd order_cost_usd",
    "forecast": "barrier_p_stop_first barrier_p_target_first barrier_p_neither barrier_settled_claims",
    "price_level": "open_usd high_usd low_usd close_usd est_price_usd latest_close",
    "data_quality": "requested_tickers returned_tickers history_bars indicators_available fundamentals_available",
}
CONCEPTS: dict[str, set[str]] = {}
for concept, keys in _C.items():
    for k in keys.split():
        CONCEPTS.setdefault(k, set()).add(concept)


def allowed_concepts(key: str) -> set[str] | None:
    e = lookup(key)
    if e is None:
        return None
    allowed = set(CONCEPTS.get(e.key, set()))
    if e.tier == "bookkeeping" or not allowed:
        allowed.add("bookkeeping")
    return allowed


# ---- (a) the sub-score a raw indicator maps to, by the analyst's own scorers ---------------------------
_FUND = {keys[0]: (name, bands, default) for name, keys, _pos, bands, default in fr._FUNDAMENTAL_RULES}
_FUND.update({keys[-1]: (name, bands, default) for name, keys, _pos, bands, default in fr._FUNDAMENTAL_RULES})


def implied_sub_score(key: str, value: float, pv: dict, block: str = "") -> float | None:
    one = {
        "rsi": tr.score_rsi,
        "bollinger_position": tr.score_bollinger,
        "sma_distance_pct": tr.score_sma_distance,
        "ema_spread_pct": tr.score_ema_crossover,
        "rsi2": tre.score_rsi2,
        "atr_pct": trr.score_atr,
        "williams_r": trr.score_williams,
        "choppiness": trr.score_choppiness,
        "nw_deviation_pct": trp.score_kernel,
    }
    if key in one:
        return one[key](value)
    if key == "relative_strength" and not block.startswith("Scanner"):
        return rsm.score_relative_strength(value)
    if key in _FUND:
        _name, bands, default = _FUND[key]
        return fr._score_metric(value, bands, default)

    def num(k):
        return _num(pv[k][0].value) if k in pv else None

    if key == "macd_histogram" and num("macd_line_price") is not None:
        return tr.score_macd(num("macd_line_price"), value)
    if key == "stochastic_k" and num("stochastic_d") is not None:
        return trr.score_stochastic(value, num("stochastic_d"))
    if key == "obv" and num("obv_signal") is not None:
        return tre.score_obv(value, num("obv_signal"))
    if key == "golden_cross":
        return tre.score_golden_cross(value >= 0.5)
    return None


# ---- (b) the six aggregates, by the analyst's own formulas ------------------------------------------------
_INDICATOR_SUBSCORES = (
    "rsi_score macd_histogram_score bollinger_position_score sma_distance_pct_score ema_spread_pct_score "
    "atr_pct_score stochastic_k_score williams_r_score choppiness_score obv_score golden_cross_score rsi2_score "
    "nw_deviation_pct_score turnaround_score"
).split()
_FUND_SUBSCORES = "pe roe net_margin current_ratio pb debt_equity eps_growth revenue_growth".split()


def expected_derivations(
    pv: dict, weights=(0.5, 0.3, 0.2), blend=0.2, floor=0.3, span=0.6
) -> dict[str, float]:
    def g(k):
        return _num(pv[k][0].value) if k in pv else None

    out: dict[str, float] = {}
    subs = [g(k) for k in _INDICATOR_SUBSCORES if g(k) is not None]
    if subs and g("rs_score") is not None:
        out["technical_score"] = (1 - blend) * sum(subs) / len(subs) / 100 + blend * g("rs_score") / 100
    fund = [g(k) for k in _FUND_SUBSCORES if g(k) is not None]
    if fund:
        out["fundamental_score"] = sum(fund) / len(fund) / 100
    parts = [(weights[0], g("technical_score")), (weights[1], g("fundamental_score"))]
    if g("sentiment_score") is not None:
        parts.append((weights[2], g("sentiment_score")))
    parts = [(w, v) for w, v in parts if v is not None]
    if parts:
        out["composite_score"] = sum(w * v for w, v in parts) / sum(w for w, _ in parts)
    if g("composite_score") is not None:
        out["confidence_score"] = floor + span * g("composite_score")
    if g("atr_pct") is not None:
        out["applied_stop_pct"] = 2 * g("atr_pct")
    if g("applied_target_pct") and g("applied_stop_pct"):
        out["reward_risk_ratio"] = g("applied_target_pct") / g("applied_stop_pct")
    return out


def _band_set(v: float | None, top: float) -> set[str]:
    if v is None:
        return {"absent"}
    x = v / top
    if x >= 0.6:
        return {"favourable"}
    if x >= 0.5:
        return {"favourable", "mixed"}
    if x > 0.4:
        return {"unfavourable", "mixed"}
    return {"unfavourable"}


def expected_pillars(pv: dict) -> dict[str, set[str]]:
    def g(k):
        if k not in pv or pv[k][0].value == "n/a":
            return None
        return _num(pv[k][0].value)

    rr = g("value_reward_risk_ratio")
    label = pv["label"][0].value if "label" in pv else ""
    return {
        "technical": _band_set(g("technical_score"), 1),
        "relative_strength": _band_set(g("rs_score"), 100),
        "fundamental": _band_set(g("fundamental_score"), 1),
        "sentiment": _band_set(g("analyst_sentiment_score"), 1),
        "risk": {"absent"} if rr is None else ({"unfavourable"} if rr < 1 else {"mixed", "favourable"}),
        "regime": {"favourable"}
        if label == "risk_on"
        else {"mixed", "neutral"}
        if label == "neutral"
        else {"unfavourable"},
    }


# ---- (b) the interactions each scenario should reveal: PLANNER DRAFT, for operator approval ----------
CONTRARIAN = set(
    "rsi rsi_score rsi2 rsi2_score stochastic_k stochastic_k_score stochastic_d williams_r "
    "williams_r_score bollinger_position bollinger_position_score nw_deviation_pct "
    "nw_deviation_pct_score".split()
)
TREND = set(
    "sma_distance_pct sma_distance_pct_score ema_spread_pct ema_spread_pct_score macd_histogram "
    "macd_histogram_score macd_line_price golden_cross golden_cross_score rs_score relative_strength "
    "technical_score".split()
)
VALUATION = {"pe", "pb", "peBasicExclExtraTTM", "pbQuarterly"}
QUALITY_GROWTH = set(
    "eps_growth revenue_growth epsGrowthTTMYoy revenueGrowthTTMYoy debt_equity "
    "totalDebt/totalEquityQuarterly roe net_margin roeTTM netProfitMarginTTM".split()
)
FUNDAMENTAL = VALUATION | QUALITY_GROWTH | {"fundamental_score"}
SENTIMENT = {
    "sentiment_score",
    "analyst_sentiment_score",
    "provider_sentiment_score",
    "sentiment_negative_words",
}
REWARD_RISK = set(
    "value_reward_risk_ratio applied_target_pct applied_stop_pct scaled_reward_risk_ratio "
    "favorable_excursion_pct".split()
)
FORECAST = {"barrier_p_stop_first", "barrier_p_target_first", "barrier_p_neither"}
HORIZON = {"base_max_holding_days", "barrier_horizon_sessions", "favorable_excursion_horizon_days"}
CORRELATION = set(
    "correlated_issuers cluster_weight_total value_cluster_exposure_ratio cluster_value_usd".split()
)
HOLDINGS = {
    "holding_HELD_value_usd",
    "held_sector_value_usd",
    "value_sector_exposure_ratio",
    "deployed_portfolio_usd",
}
REGIME = {"label", "vix_index"}
RISK = {"beta", "atr_pct", "atr_pct_score", "barrier_p_stop_first"}

EXPECTED_INTERACTIONS: dict[str, list[tuple[set[str], set[str], set[str]]]] = {
    "extended_leader": [
        (CONTRARIAN, TREND, {"contradicts"}),
        (VALUATION, TREND, {"contradicts", "qualifies"}),
    ],
    "falling_knife": [
        (CONTRARIAN, TREND, {"contradicts"}),
        (REWARD_RISK, REWARD_RISK, {"qualifies", "contradicts"}),
        (FORECAST, TREND, {"contradicts"}),
    ],
    "value_trap": [(VALUATION, QUALITY_GROWTH, {"contradicts"})],
    "pillars_in_conflict": [(SENTIMENT, TREND | CONTRARIAN, {"contradicts"})],
    "earnings_inside_hold": [({"days_to_earnings"}, HORIZON, {"qualifies", "contradicts"})],
    "correlated_with_holding": [(CORRELATION, HOLDINGS, {"qualifies", "confirms"})],
    "risk_off_high_beta": [(REGIME, RISK, {"qualifies", "contradicts"})],
    "steady_compounder": [(TREND, FUNDAMENTAL, {"confirms"})],
}


H11_SUBSCORES = set(_FUND_SUBSCORES)
_FIELDS = ("value", "scale", "concept", "direction", "implied", "critical")


def group_name(g: set[str]) -> str:
    """A readable name for a key group of EXPECTED_INTERACTIONS (used in feedback, never in grading)."""
    for name, v in globals().items():
        if name.isupper() and isinstance(v, set) and v == g:
            return name.lower().replace("_", " ") + " readings"
    return ", ".join(f"`{k}`" for k in sorted(g)[:6])


def _hits(keys: list[str], group: set[str]) -> bool:
    return any((lookup(k).key if lookup(k) else k) in group or k in group for k in keys)


def grade(ex: Explanation, packet: str, case: str, coverage: str) -> dict:
    pv = packet_values(packet)
    req = required_numbers(packet, evidence_only=coverage == "evidence")
    # (a) per number
    rows = []
    for it in ex.interpretations:
        occs = pv.get(it.metric, [])
        matched = [o for o in occs if _matches(it, o)]
        e = lookup(it.metric)
        v = _num(it.value)
        units = (
            {_unit_of(it.metric, o) for o in matched}
            if matched
            else ({e.scale, *e.alt_scales} if e else set())
        )
        exp_dir = accepted_directions(it.metric, v, pv) if v is not None else None
        imp = (
            implied_sub_score(it.metric, v, pv, matched[0].block if matched else "")
            if v is not None
            else None
        )
        concepts = allowed_concepts(it.metric)
        rows.append(
            {
                "metric": it.metric,
                "value": bool(matched),
                "scale": it.scale in units if e else False,
                "concept": None if concepts is None else it.concept in concepts,
                # graded only where the code's score makes a clear call (>= 60 or <= 40); "neutral" there is wrong,
                # except for contrarian oscillators, read with the trend (H7, laws.accepted_directions)
                "direction": None if exp_dir is None else it.direction in exp_dir,
                "implied": None
                if imp is None
                else (it.implied_sub_score is not None and abs(it.implied_sub_score - imp) < 0.51),
            }
        )
        # the two misreadings this system is built to catch must not happen even once (H7, H11)
        r = rows[-1]
        r["got"] = {
            "value": it.value,
            "scale": it.scale,
            "concept": it.concept,
            "direction": it.direction,
            "implied": it.implied_sub_score,
        }
        r["want"] = {
            "value": [o.value for o in occs],
            "scale": sorted(units),
            "concept": sorted(concepts or []),
            "direction": sorted(exp_dir) if exp_dir else None,
            "implied": imp,
        }
        if it.metric in CONTRARIAN_KEYS:
            # H7: read with the trend; and a raw oscillator's sub-score shows the contrarian scoring is known
            got = [
                x
                for x in (r["direction"], r["implied"] if it.metric in CONTRARIAN_RAW else None)
                if x is not None
            ]
            r["critical"] = all(got) if got else None
        elif it.metric in H11_SUBSCORES and e is not None:
            r["critical"] = r["scale"]
        else:
            r["critical"] = None
    covered = 0
    missing = []
    for key, groups in req.items():
        mine = [i for i in ex.interpretations if i.metric == key]
        for g in groups:
            if any(_matches(i, o) for i in mine for o in g):
                covered += 1
            else:
                missing.append(key)
    need = sum(len(g) for g in req.values())
    # (b) combination
    exp_d = expected_derivations(pv)
    got_d = {d.name: d.computed for d in ex.derivations}
    deriv = {n: (n in got_d and abs(got_d[n] - x) <= max(0.01 * abs(x), 0.003)) for n, x in exp_d.items()}
    exp_p = expected_pillars(pv)
    got_p = {p.pillar: p.verdict for p in ex.pillars}
    pillars = {n: got_p.get(n, "absent") in ok for n, ok in exp_p.items()}
    expected_int = EXPECTED_INTERACTIONS.get(case, [])
    found = [
        any(
            r.relation in rels
            and ((_hits(r.keys_a, a) and _hits(r.keys_b, b)) or (_hits(r.keys_a, b) and _hits(r.keys_b, a)))
            for r in ex.interactions
        )
        for a, b, rels in expected_int
    ]

    def rate(field):
        vals = [r[field] for r in rows if r[field] is not None]
        return (sum(vals) / len(vals)) if vals else None

    return {
        "coverage": covered / need if need else 1.0,
        "missing": missing[:40],
        "per_number": {f: rate(f) for f in ("value", "scale", "concept", "direction", "implied", "critical")},
        "errors": [r for r in rows if any(r[f] is False for f in _FIELDS)][:60],
        "derivations": deriv,
        "derivation_values": {n: {"want": x, "got": got_d.get(n)} for n, x in exp_d.items()},
        "pillar_values": {n: {"want": sorted(ok), "got": got_p.get(n, "absent")} for n, ok in exp_p.items()},
        "pillars": pillars,
        "interactions_recall": (sum(found) / len(found)) if found else None,
        "interactions_found": found,
        "expected_interactions": [[group_name(a), group_name(b), sorted(r)] for a, b, r in expected_int],
        "situation": ex.situation,
        "overall": ex.overall,
    }


# Pre-registered pass bar (DL-264 amendment 9), applied to FIRST attempts only (no feedback, no retry).
PASS_BAR = {
    "coverage": 1.0,
    "value": 0.98,
    "scale": 0.95,
    "concept": 0.90,
    "direction": 0.90,
    "implied": 0.90,
    "critical": 1.0,  # contrarian oscillators read the right way round, H11 sub-scores never read as ratios
    "derivations_correct": 5,  # of 6
    "pillars_correct": 5,  # of 6
    "interactions_recall": 0.70,
}


def passes(g: dict) -> dict[str, bool]:
    pn = g["per_number"]
    out = {"coverage": g["coverage"] >= PASS_BAR["coverage"]}
    for f in _FIELDS:
        out[f] = pn[f] is None or pn[f] >= PASS_BAR[f]
    out["derivations"] = sum(g["derivations"].values()) >= PASS_BAR["derivations_correct"]
    out["pillars"] = sum(g["pillars"].values()) >= PASS_BAR["pillars_correct"]
    out["interactions"] = (
        g["interactions_recall"] is None or g["interactions_recall"] >= PASS_BAR["interactions_recall"]
    )
    return out
