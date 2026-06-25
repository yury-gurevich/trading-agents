"""Layer-3 acceptance gate for the trading pipeline (pack, not substrate).

Agent: orchestration
Role: turn the observatory into a PASS/FAIL verdict on a run — every per-stage
      invariant AND the cross-stage CONSERVATION boundaries: no agent fabricates or
      exceeds its mandate, so each stage's output count is bounded by its input. This
      is the trading content of the Layer-3 "each agent's job + boundaries asserted"
      acceptance row. The verdict mechanism is substrate (observatory.accept); the
      conservation invariants are the trading pack (ADR-0012).
External I/O: none (reads the injected GraphStore via observe_run).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.observatory import AcceptanceResult, Breach, CrossCheck, accept
from orchestration.packs.trading_observatory import observe_run

if TYPE_CHECKING:
    from kernel import GraphStore


def _conserves(child: str, child_key: str, parent: str, parent_key: str) -> CrossCheck:
    """No fabrication: a stage's output count cannot exceed its input count."""

    def check(observed: dict[str, dict[str, object]]) -> Breach | None:
        out = observed.get(child, {}).get(child_key)
        src = observed.get(parent, {}).get(parent_key)
        if not isinstance(out, int) or not isinstance(src, int):
            return None
        if out > src:
            return Breach(
                child, child_key, f"{out} > {parent}.{parent_key}={src} (fabricated)"
            )
        return None

    return check


# Each agent's output is bounded by its input — the boundaries asserted (EXEC-NEV-01:
# "never decides what to trade"; the scanner/analyst/PM cannot invent names).
_CONSERVATION: tuple[CrossCheck, ...] = (
    _conserves("scanner", "survived", "provider", "returned"),
    _conserves("analyst", "scored", "scanner", "survived"),
    _conserves("pm", "approved", "analyst", "scored"),
    _conserves("execution", "submitted", "pm", "approved"),
)


def accept_run(graph: GraphStore, run_id: str) -> AcceptanceResult:
    """The Layer-3 acceptance verdict over one persisted run."""
    return accept(observe_run(graph, run_id), _CONSERVATION)


def render_acceptance(result: AcceptanceResult) -> str:
    """Human-readable PASS/FAIL verdict — one line per breach."""
    if result.passed:
        return "ACCEPTANCE  PASS - every stage did its job within its boundaries"
    lines = [f"  FAIL  {b.stage}.{b.key}: {b.detail}" for b in result.breaches]
    return "ACCEPTANCE  FAIL\n" + "\n".join(lines)
