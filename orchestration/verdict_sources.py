"""Read recorded verdicts off the graph, with fail-opens already subtracted.

Agent: orchestration
Role: turn what the fleet actually recorded into the same record type the replay
      harness produces, so both can be measured by one set of metrics.
External I/O: reads the injected GraphStore. No writes.

One exclusion predicate, in one place: a fail-open is recorded as
``verdict: "uphold"`` (``agents/deliberator/review_record.py``), so a reader that
does not subtract ``failed_open_tickers`` measures the outage rate and calls it a
verdict. DL-104's run D is 5 of 6, not 5 of 10, for exactly this reason.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from orchestration.verdict_metrics import ReplayVerdict

if TYPE_CHECKING:
    from collections.abc import Sequence

    from kernel import GraphStore
    from orchestration.verdict_metrics import Decision

__all__ = ["real_verdicts", "recorded_as_repeats", "recorded_verdicts"]

CROSS_RUN_KEY = "cross-run"


def real_verdicts(props: Mapping[str, object]) -> dict[str, str]:
    """Read one DeliberationRun's verdicts with its fail-opens subtracted."""
    # The in-memory store freezes props (dict -> mappingproxy, list -> tuple) while
    # the Postgres store returns plain JSON types, so both shapes must be read.
    verdicts = props.get("verdicts")
    if not isinstance(verdicts, Mapping):
        return {}
    failed = props.get("failed_open_tickers")
    excluded = set(failed) if isinstance(failed, list | tuple) else set()
    return {
        str(ticker): str(ruling)
        for ticker, ruling in verdicts.items()
        if ticker not in excluded
    }


def recorded_verdicts(graph: GraphStore) -> dict[Decision, str]:
    """Every real verdict the live fleet has recorded, fail-opens removed."""
    found: dict[Decision, str] = {}
    for node in graph.list_nodes("DeliberationRun"):
        for ticker, ruling in real_verdicts(node.props).items():
            found[(node.key, ticker)] = ruling
    return found


def recorded_as_repeats(
    graph: GraphStore, run_ids: Sequence[str], *, arm: str = "recorded"
) -> tuple[ReplayVerdict, ...]:
    """Present several recorded runs as repeats of one decision, keyed by ticker.

    The comparison is *across* runs — the same ticker judged on two different
    nights — so the decision key is the ticker alone and the run becomes the
    repeat index. This is how DL-104's hand-computed 9-of-16 is re-derived through
    the same code path every other agreement number goes through.
    """
    return tuple(
        ReplayVerdict(
            pm_run=CROSS_RUN_KEY,
            ticker=ticker,
            arm=arm,
            repeat=index,
            ruling=ruling,
        )
        for index, run_id in enumerate(run_ids, start=1)
        for ticker, ruling in sorted(_props(graph, run_id).items())
    )


def _props(graph: GraphStore, run_id: str) -> dict[str, str]:
    node = graph.get_node("DeliberationRun", run_id)
    return {} if node is None else real_verdicts(node.props)
