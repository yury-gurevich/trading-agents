"""Trading-pipeline observatory facade (pack, not substrate).

Agent: orchestration
Role: expose per-stage views for the full trading spine and render them.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.batch_chain import walk_chain
from orchestration.observatory import StageView, render
from orchestration.packs.trading_observatory_views import SPEC

if TYPE_CHECKING:
    from kernel import GraphStore


def observe_run(graph: GraphStore, run_id: str) -> tuple[StageView, ...]:
    """Build the per-stage views for one run; unreached stages are explicit."""
    nodes = walk_chain(graph, run_id)
    views: list[StageView] = []
    for name, label, trigger, extractor in SPEC:
        node = nodes.get(label)
        if node is None:
            views.append(StageView(name, trigger, {}, reached=False))
        else:
            views.append(extractor(graph, node))
    return tuple(views)


def inspect(graph: GraphStore, run_id: str) -> str:
    """Observe one run and render the observatory print."""
    return render(observe_run(graph, run_id))
