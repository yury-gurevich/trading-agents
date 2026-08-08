"""Decide which graph rows a run-scoped teardown may delete, and prove none survive.

Agent: tooling
Role: separate the two questions `pg_teardown.py` used to answer with one tuple —
      *is this a disposable run artifact?* and *may the walk traverse through it?* —
      and enumerate run-owned rows the edge walk cannot reach.
External I/O: PostgreSQL database (via a caller-supplied cursor).

Broker-mirroring rows are production state, not proof artifacts (DL-44 / S120). They
are never deleted and are never traversed *through*, so one run's lineage can never
reach another run's rows via a shared `Position`. Before this split the barrier was
incidental: `Position`'s only bridge from the reached set is
`Fill -> BrokerStopOrder -> Position`, and it held solely because `BrokerStopOrder`
happened to be missing from the artifact list — a label that reads exactly like a run
artifact, so adding it would have deleted the live book (DL-94).
"""

from __future__ import annotations

from typing import Any

#: Broker-mirroring production state. Never deleted, never traversed through.
PROTECTED_LABELS = (
    "Position",
    "Fill",
    "BrokerStopOrder",
    "BrokerOrderStatus",
)

#: Disposable proof artifacts of a single pipeline run.
RUN_ARTIFACT_LABELS = (
    "RunRequest",
    "MarketData",
    "RegimeContext",
    "ScanRun",
    "Candidate",
    "AnalystRun",
    "SentimentReading",
    "Recommendation",
    "PMRun",
    "Rejection",
    "OrderIntent",
    "DeliberationRun",
    "ExecutionRun",
    "BrokerPositionSnapshot",
    "MonitorRun",
    "PositionCheck",
    "CloseDecision",
    "Snapshot",
    "TradeNarrative",
)

#: Artifacts whose key prefixes the keys of the rows they own, e.g. a `PositionCheck`
#: keyed `monitor-run-<id>:broker:WFC:348:8639:check`. `PositionCheck` and
#: `CloseDecision` have exactly one edge each — to `Position`, a protected label — so
#: no lawful walk can reach them and only this prefix pass collects them.
RUN_CONTAINER_LABELS = (
    "ScanRun",
    "AnalystRun",
    "PMRun",
    "ExecutionRun",
    "MonitorRun",
    "DeliberationRun",
)

_WALK = """
WITH RECURSIVE target(label, key) AS (
    SELECT label, key
    FROM nodes
    WHERE key LIKE %s ESCAPE '\\' AND label <> ALL(%s)
    UNION
    SELECT neighbor.label, neighbor.key
    FROM target t
    JOIN LATERAL (
        SELECT e.child_label AS label, e.child_key AS key
        FROM edges e
        WHERE e.parent_label = t.label AND e.parent_key = t.key
        UNION
        SELECT e.parent_label AS label, e.parent_key AS key
        FROM edges e
        WHERE e.child_label = t.label AND e.child_key = t.key
    ) neighbor ON true
    JOIN nodes n ON n.label = neighbor.label AND n.key = neighbor.key
    WHERE n.label = ANY(%s)
)
SELECT label, key
FROM target
"""


def like_pattern(stamp: str, *, contains: bool) -> str:
    """Escape a stamp for LIKE, anchoring it as a prefix unless `contains`.

    Patterns escape with a backslash, which is PostgreSQL's default LIKE escape
    character. The set-matching queries below must therefore omit `ESCAPE` — it is a
    syntax error on the `LIKE ANY(...)` form, and redundant on any form.
    """
    escaped = stamp.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%" if contains else f"{escaped}%"


def collect(cursor: Any, run_id: str) -> list[tuple[str, str]]:  # noqa: ANN401
    """Return every deletable row of a run: walk-reachable, then container-owned."""
    stamp = like_pattern(run_id, contains=True)
    cursor.execute(
        _WALK,
        (stamp, list(PROTECTED_LABELS), list(RUN_ARTIFACT_LABELS)),
    )
    found = {(str(label), str(key)) for label, key in cursor.fetchall()}
    owned_patterns = _owned_patterns(found)
    if owned_patterns:
        cursor.execute(
            "SELECT label, key FROM nodes WHERE label = ANY(%s) AND key LIKE ANY(%s)",
            (list(RUN_ARTIFACT_LABELS), owned_patterns),
        )
        found |= {(str(label), str(key)) for label, key in cursor.fetchall()}
    return sorted(found)


def survivors(
    cursor: Any,  # noqa: ANN401
    run_id: str,
    targets: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Return deletable rows that still carry the run's stamps after a teardown."""
    patterns = [like_pattern(run_id, contains=True), *_owned_patterns(set(targets))]
    cursor.execute(
        "SELECT label, key FROM nodes WHERE label = ANY(%s) AND key LIKE ANY(%s)",
        (list(RUN_ARTIFACT_LABELS), patterns),
    )
    return sorted((str(label), str(key)) for label, key in cursor.fetchall())


def protected_neighbours(
    cursor: Any,  # noqa: ANN401
    targets: list[tuple[str, str]],
) -> int:
    """Count protected rows adjacent to the target set — the walk stopped at these.

    Counting by key stamp instead would report 0 for the common case: a `Fill` keyed
    `exit:<ref>:WFC:sell` carries no run stamp and is spared only because the walk
    refuses to traverse it. A teardown that spares ten broker rows must say ten.
    """
    if not targets:
        return 0
    cursor.execute(
        "WITH t(label, key) AS (SELECT * FROM unnest(%s::text[], %s::text[])) "
        "SELECT count(*) FROM ("
        "  SELECT DISTINCT n.label, n.key FROM nodes n JOIN edges e ON "
        "  (e.parent_label = n.label AND e.parent_key = n.key AND EXISTS ("
        "    SELECT 1 FROM t WHERE t.label = e.child_label AND t.key = e.child_key))"
        "  OR (e.child_label = n.label AND e.child_key = n.key AND EXISTS ("
        "    SELECT 1 FROM t WHERE t.label = e.parent_label AND t.key = e.parent_key))"
        "  WHERE n.label = ANY(%s)"
        ") spared",
        (
            [label for label, _ in targets],
            [key for _, key in targets],
            list(PROTECTED_LABELS),
        ),
    )
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def protected_matches(cursor: Any, patterns: list[str]) -> int:  # noqa: ANN401
    """Count protected production rows a pattern would have matched."""
    cursor.execute(
        "SELECT count(*) FROM nodes WHERE label = ANY(%s) AND key LIKE ANY(%s)",
        (list(PROTECTED_LABELS), patterns),
    )
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def _owned_patterns(found: set[tuple[str, str]]) -> list[str]:
    """Build `<container key>:%` patterns for every run container in `found`."""
    return sorted(
        like_pattern(f"{key}:", contains=False)
        for label, key in found
        if label in RUN_CONTAINER_LABELS
    )
