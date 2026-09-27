"""Layer row builders for S237 fidelity comparison.

Agent: tooling
Role: compare per-stage live and replay outputs with named causes.
External I/O: none.
"""

from __future__ import annotations

from typing import Any

_CONFIDENCE_TOLERANCE = 1e-9


def layer1_rows(
    session: dict[str, Any], changed_paths: tuple[str, ...]
) -> list[dict[str, Any]]:
    """Return scanner, analyst, and PM comparison rows."""
    replay = session.get("replay", {})
    rows: list[dict[str, Any]] = []
    rows.extend(_scanner_rows(session, replay, changed_paths))
    rows.extend(_analyst_rows(session, replay, changed_paths))
    rows.extend(_pm_rows(session, replay, changed_paths))
    return rows


def layer2_rows(session: dict[str, Any]) -> list[dict[str, Any]]:
    """Return precomputed Layer 2 rows when a fixture supplies them."""
    return list(session.get("layer2", ()))


def layer3_row(session: dict[str, Any]) -> dict[str, Any]:
    """Count live approval-to-fill outcomes from the export."""
    fills = session.get("fills", ())
    return {
        "session": session["session"],
        "approved": len(session.get("pm", {}).get("order_intents", ())),
        "vetoed": len(session.get("deliberation", {}).get("vetoed_tickers", ())),
        "submitted": int(session.get("execution", {}).get("submitted", 0)),
        "dropped_rejected": int(session.get("execution", {}).get("dropped", 0))
        + int(session.get("execution", {}).get("rejected", 0)),
        "filled": sum(1 for item in fills if item.get("status") == "filled"),
        "expired": sum(1 for item in fills if item.get("status") == "expired"),
    }


def _scanner_rows(
    live: dict[str, Any], replay: dict[str, Any], changed: tuple[str, ...]
) -> list[dict[str, Any]]:
    left = _candidate_ranks(live.get("scanner", {}))
    right = _candidate_ranks(replay.get("scanner", live.get("scanner", {})))
    return [
        _row(
            live,
            "scanner",
            ticker,
            "rank",
            left.get(ticker),
            right.get(ticker),
            changed,
        )
        for ticker in sorted(set(left) | set(right))
    ]


def _analyst_rows(
    live: dict[str, Any], replay: dict[str, Any], changed: tuple[str, ...]
) -> list[dict[str, Any]]:
    left = _recommendations(live.get("analyst", {}))
    right = _recommendations(replay.get("analyst", live.get("analyst", {})))
    rows = []
    for ticker in sorted(set(left) | set(right)):
        for field in (
            "action",
            "exit_trigger",
            "confidence",
            "technical_score",
            "suggested_stop_pct",
        ):
            rows.append(
                _row(
                    live,
                    "analyst",
                    ticker,
                    field,
                    left.get(ticker, {}).get(field),
                    right.get(ticker, {}).get(field),
                    changed,
                )
            )
    return rows


def _pm_rows(
    live: dict[str, Any], replay: dict[str, Any], changed: tuple[str, ...]
) -> list[dict[str, Any]]:
    left = _pm_decisions(live.get("pm", {}))
    right = _pm_decisions(replay.get("pm", live.get("pm", {})))
    rows = []
    for ticker in sorted(set(left) | set(right)):
        for field in ("decision", "reason", "quantity", "stop_pct"):
            rows.append(
                _row(
                    live,
                    "pm",
                    ticker,
                    field,
                    left.get(ticker, {}).get(field),
                    right.get(ticker, {}).get(field),
                    changed,
                )
            )
    return rows


def _row(
    session: dict[str, Any],
    stage: str,
    ticker: str,
    field: str,
    live: object,
    replay: object,
    changed: tuple[str, ...],
) -> dict[str, Any]:
    match = _matches(field, live, replay)
    return {
        "session": session["session"],
        "stage": stage,
        "ticker": ticker,
        "field": field,
        "live": live,
        "replay": replay,
        "match": match,
        "cause": "" if match else _cause(session, stage, field, changed),
    }


def _cause(
    session: dict[str, Any], stage: str, field: str, changed: tuple[str, ...]
) -> str:
    if changed:
        return f"code_changed:{changed[0]}"
    missing = tuple(session.get("not_persisted", ()))
    if stage == "scanner" and "benchmark" in missing:
        return "not_persisted:benchmark"
    name = f"{stage}.{field}"
    return f"not_persisted:{name}" if name in missing else "unexplained"


def _candidate_ranks(block: dict[str, Any]) -> dict[str, int]:
    candidates = block.get("candidate_set", {}).get("candidates", ())
    return {str(item["ticker"]): int(item["rank"]) for item in candidates}


def _recommendations(block: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = block.get("recommendation_set", {}).get("recommendations", ())
    return {str(item["ticker"]): dict(item) for item in rows}


def _pm_decisions(block: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {
        str(item["ticker"]): {"decision": "approved", **dict(item)}
        for item in block.get("order_intents", ())
    }
    for item in block.get("rejections", ()):
        out[str(item["ticker"])] = {"decision": "rejected", **dict(item)}
    return out


def _matches(field: str, left: object, right: object) -> bool:
    if field == "confidence" and left is not None and right is not None:
        return abs(float(left) - float(right)) <= _CONFIDENCE_TOLERANCE
    return left == right
