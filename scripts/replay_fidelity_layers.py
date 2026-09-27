"""S237 Layer 1 rows: per stage, per ticker, the live decision beside the replayed one.

Agent: tooling
Role: flatten live and replayed stage outputs into comparable field rows.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from contracts.analyst import RecommendationSet
    from contracts.portfolio_manager import OrderIntentSet
    from contracts.scanner import CandidateSet

# Trap 7 / DL-237: one absolute float tolerance, stated once, used for every float.
TOLERANCE = 1e-9
_ANALYST_JUDGED = ("action", "exit_trigger", "confidence")
_ANALYST_DIAGNOSTIC = ("technical_score", "suggested_stop_pct", "reason")
_PM_FIELDS = ("decision", "reason", "quantity", "stop_pct")
_JUDGED_ACTIONS = frozenset({"buy", "sell"})  # R5: PM agreement over judged recs

Fields = dict[str, dict[str, object]]


def scanner_rows(
    session: str, live: Mapping[str, Any], replay: CandidateSet | None
) -> list[dict[str, Any]]:
    """Membership and rank per ticker (judged), filter verdicts where stored."""
    live_set = live.get("candidate_set") or {}
    ranks = {
        str(c["ticker"]): {"rank": c["rank"]} for c in live_set.get("candidates", ())
    }
    replay_set = replay.model_dump(mode="json") if replay is not None else {}
    replayed = {
        str(c["ticker"]): {"rank": c["rank"]} for c in replay_set.get("candidates", ())
    }
    rows = _rows(session, "scanner", ranks, replayed, ("rank",), judged=True)
    stored = _verdicts(live.get("filter_trace") or live_set.get("filter_trace"))
    if stored:
        mine = _verdicts(replay_set.get("filter_trace"))
        rows += _rows(session, "scanner", stored, mine, ("filter",), judged=False)
    return rows


def analyst_rows(
    session: str, live: Mapping[str, Any], replay: RecommendationSet | None
) -> list[dict[str, Any]]:
    """Action, exit trigger and confidence per ticker; the rest are diagnostics."""
    mine = _decisions(replay.model_dump(mode="json")) if replay is not None else {}
    theirs = _decisions(live.get("recommendation_set") or {})
    return _rows(
        session, "analyst", theirs, mine, _ANALYST_JUDGED, judged=True
    ) + _rows(session, "analyst", theirs, mine, _ANALYST_DIAGNOSTIC, judged=False)


def pm_rows(
    session: str,
    live: Mapping[str, Any],
    recommendations: Mapping[str, Any],
    replay: OrderIntentSet | None,
) -> list[dict[str, Any]]:
    """Decision and reason per ticker, quantity and stop pct for an approval."""
    theirs: Fields = {
        str(item["ticker"]): _approved(item) for item in live.get("order_intents", ())
    }
    theirs |= {
        str(item["ticker"]): _rejected(item) for item in live.get("rejections", ())
    }
    mine: Fields = {}
    if replay is not None:
        dumped = replay.model_dump(mode="json")
        mine = {str(item["ticker"]): _approved(item) for item in dumped["approved"]}
        mine |= {str(item["ticker"]): _rejected(item) for item in dumped["rejected"]}
    actions = {
        str(item["ticker"]): str(item["action"])
        for item in recommendations.get("recommendations", ())
    }
    rows = _rows(session, "pm", theirs, mine, _PM_FIELDS, judged=True)
    for row in rows:
        row["judged"] = actions.get(str(row["ticker"]), "buy") in _JUDGED_ACTIONS
    return rows


def matches(left: object, right: object) -> bool:
    """Equal, with every float compared within the one tolerance."""
    if isinstance(left, float) and isinstance(right, float | int):
        return abs(left - right) <= TOLERANCE
    if isinstance(right, float) and isinstance(left, int):
        return abs(left - right) <= TOLERANCE
    return left == right


def _rows(
    session: str,
    stage: str,
    live: Fields,
    replay: Fields,
    fields: tuple[str, ...],
    *,
    judged: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ticker in sorted(set(live) | set(replay)):
        for name in fields:
            theirs = live.get(ticker, {}).get(name)
            mine = replay.get(ticker, {}).get(name)
            rows.append(
                {
                    "session": session,
                    "stage": stage,
                    "ticker": ticker,
                    "field": name,
                    "live": theirs,
                    "replay": mine,
                    "match": matches(theirs, mine),
                    "judged": judged,
                }
            )
    return rows


def _decisions(recommendation_set: Mapping[str, Any]) -> Fields:
    out: Fields = {
        str(item["ticker"]): {
            "action": item.get("action"),
            "exit_trigger": item.get("exit_trigger"),
            "confidence": item.get("confidence"),
            "technical_score": item.get("technical_score"),
            "suggested_stop_pct": item.get("suggested_stop_pct"),
        }
        for item in recommendation_set.get("recommendations", ())
    }
    for item in recommendation_set.get("rejections", ()):
        out[str(item["ticker"])] = {"action": "rejected", "reason": item.get("reason")}
    return out


def _verdicts(trace: object) -> Fields:
    if not isinstance(trace, dict):
        return {}
    return {
        str(item["ticker"]): {
            "filter": f"{item.get('decision')}:{item.get('filter_fired') or ''}"
        }
        for item in trace.get("verdicts", ())
    }


def _approved(item: Mapping[str, Any]) -> dict[str, object]:
    return {
        "decision": "approved",
        "quantity": item.get("quantity"),
        "stop_pct": item.get("stop_pct"),
    }


def _rejected(item: Mapping[str, Any]) -> dict[str, object]:
    return {"decision": "rejected", "reason": item.get("reason")}
