"""Pure report assembly and the seven-term debate lanes rule.

Agent: tooling
Role: disclose counts and timings from the production record and passive observers.
External I/O: none.
"""

from __future__ import annotations

import statistics
from collections import Counter
from typing import Any


def is_clean(report: dict[str, Any]) -> bool:
    """Apply D3; effective lanes are a measurement, never a pass threshold."""
    return (
        report["real_debate_count"] == report["orders"]
        and report["failed_open_count"] == 0
        and report["replies_nobody_took"] == 0
        and report["mismatched_replies"] == 0
        and report["turns_served_twice"] == 0
        and not report["errors"]
        and (report["transport"] != "live" or report["production_unchanged"] is True)
    )


def timings(values: list[float]) -> list[float] | None:
    """Return median and maximum, or null if no turn was answered."""
    if not values:
        return None
    return [round(statistics.median(values), 3), round(max(values), 3)]


def observations(calls: list[dict[str, Any]]) -> dict[str, int]:
    """Count replies carrying an id other than the manager call's request id."""
    return {"mismatched_replies": sum(r["outcome"] == "mismatched" for r in calls)}


def build_report(
    report: dict[str, Any],
    *,
    props: dict[str, Any],
    counts: dict[str, dict[str, int]],
    reply_topic: str,
    calls: list[dict[str, Any]],
    served: list[dict[str, Any]],
    span: float,
    errors: list[str],
    faults: dict[str, int],
) -> dict[str, Any]:
    """Read the durable counts and count both orphaned and unread late replies."""
    by_id = Counter(row["request_id"] for row in served)
    call_by_id = {row["request_id"]: row for row in calls}
    served_by_id = {row["request_id"]: row for row in served}
    unwaited = [
        row
        for row in served
        if call_by_id.get(row["request_id"], {}).get("outcome") == "raised"
        and row["end"] > call_by_id[row["request_id"]]["return"]
    ]
    late = [r for r in unwaited if r["start"] > call_by_id[r["request_id"]]["return"]]
    answered = [
        row
        for row in calls
        if row["outcome"] == "answered" and row["request_id"] in served_by_id
    ]
    waits = [served_by_id[r["request_id"]]["start"] - r["call"] for r in answered]
    pickups = [r["return"] - served_by_id[r["request_id"]]["end"] for r in answered]
    first_wave = {
        f"pm-lanes:T{n:02d}:defender:r1"
        for n in range(min(report["concurrency"], report["orders"]))
    }
    work = sum(row["end"] - row["start"] for row in served)
    return {
        **report,
        "real_debate_count": props["real_debate_count"],
        "failed_open_count": props["failed_open_count"],
        "failed_open_reason": props.get("failed_open_reason", ""),
        "orphaned_reply_count": props["orphaned_reply_count"],
        "replies_nobody_took": props["orphaned_reply_count"]
        + counts[reply_topic]["active"],
        **observations(calls),
        "turns_asked": len(calls),
        "turns_served": len(served),
        "turns_served_twice": sum(n > 1 for n in by_id.values()),
        "turns_answered_for_nobody": len(unwaited),
        "turns_started_after_caller_gave_up": len(late),
        "first_wave_replicas": len(
            {r["replica"] for r in served if r["request_id"] in first_wave}
        ),
        "by_replica": dict(sorted(Counter(row["replica"] for row in served).items())),
        "span_seconds": round(span, 2),
        "served_work_seconds": round(work, 2),
        "effective_lanes": round(work / span, 2) if span else None,
        "request_wait_seconds": timings(waits),
        "reply_pickup_seconds": timings(pickups),
        "subscriptions": counts,
        "errors": errors,
        "faults": faults,
    }
