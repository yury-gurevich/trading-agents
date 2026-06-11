<!-- Agent: planning | Role: sprint handover -->
# Sprint 21 — Incident view + explain on demand + P6 exit (P6 closes)

**Status:** planned · **Branch:** `sprint-21-incidents-explain-p6-exit` · **Build phase:** P6 (surfaces) · **Effort: M**

## Goal

Three deliverables: (1) surface `Fault` nodes in the CLI (`cli incidents`), completing the
"recover" leg of the P6 operator checklist; (2) add `cli explain <pos_id>` that triggers
`reporter.narrative` on demand for any position; (3) write the `test_p6_exit.py` integration
test that proves the four-part operator checklist end-to-end and formally closes P6.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/architecture.md`; `docs/build-plan.md` (P6 exit
  criterion: "an operator can run, inspect, approve, and recover entirely from the dashboard");
  `agents/supervisor/store.py` (`write_fault` — Fault node props: `source_agent`, `source_module`,
  `capability`, `severity`, `error_type`, `message`, `correlation_id`, `occurred_at`, `created_at`;
  NO `status` field — all faults are permanently open in P6);
  `agents/supervisor/domain/health.py` (`open_incidents` counts all Fault nodes since
  `status != "resolved"` is always True for nodes without a `status` prop);
  `contracts/reporter.py` (`NarrativeRequest(position_id: str)` → `TradeNarrative`;
  `TradeNarrative.story` is an `Explanation`);
  `contracts/common.py` (`Explanation.summary: str` — the text field is `summary`, not `text`);
  `surfaces/cli_commands.py` (**currently 172L** — must extract Sprint 20 additions first;
  see Part A0 below);
  `surfaces/render.py` (currently 159L — stays under 200L with additions).

- **P6 exit criterion.** After this sprint the following must all be provable by
  `test_p6_exit.py`:
  - **Run**: `cli command "run the scan"` returns `accepted=True`,
    `routed_to="orchestration.execute_run"`.
  - **Inspect**: `cli status` returns a health summary; `cli incidents` returns a fault list
    (empty or populated); `cli positions` returns a position list.
  - **Approve**: seed a `Flag`; `cli approve <subject>` returns `accepted=True`; a
    `FlagResolution` node exists in the graph.
  - **Recover**: seed a `Fault`; `cli incidents` output contains the fault's `source_agent`.
  - **Explain**: `cli explain <pos_id>` returns a `TradeNarrative`; output contains
    `Explanation.summary` text (non-empty).

- `Explanation.summary` is the narrative text field — **not** `.text`. Verify against
  `contracts/common.py` before writing the render helper.

## Part A0 — Prerequisite: free `cli_commands.py` headroom (zero-behaviour refactor)

`cli_commands.py` is 172L. Adding two new command handlers (~25L) would reach ~197L — one
line from the hard cap. **Before touching Part A or B**, extract the Sprint 20 additions
(`cmd_narrative` and `cmd_approve`) into a new `surfaces/cli_commands_extra.py`:

```python
# surfaces/cli_commands_extra.py
"""Extended CLI command handlers (narrative display and approve flow).

Agent: surfaces
Role: implement narrative and approve sub-commands behind the argparse glue.
External I/O: MessageBus calls through the injected surface context.
"""
```

Move `cmd_narrative` and `cmd_approve` (and any helpers used only by them) to the new file.
Import them back into `cli_commands.py` or directly into `cli.py`'s `_dispatch` — whichever
is cleaner. Both files must have valid coding-agent headers.

**Run `make ci` after A0.** The gate must be green (zero behaviour change) before proceeding.
This brings `cli_commands.py` to ~142L and creates `cli_commands_extra.py` at ~32L.

## Part A — Incident view

### A1. `surfaces/queries/faults.py` — new file, ≤ 60L

```python
@dataclass(frozen=True)
class FaultView:
    fault_id: str        # node key (truncated hash, display-friendly)
    source_agent: str
    capability: str
    severity: str
    message: str
    occurred_at: str

def open_faults(graph: GraphStore) -> tuple[FaultView, ...]:
    """Return all Fault nodes, newest first. All faults are open in P6 (no resolution)."""
    faults = [
        FaultView(
            fault_id=node.key[:12],
            source_agent=str(node.props.get("source_agent", "")),
            capability=str(node.props.get("capability", "")),
            severity=str(node.props.get("severity", "")),
            message=str(node.props.get("message", "")),
            occurred_at=str(node.props.get("occurred_at", "")),
        )
        for node in graph.list_nodes("Fault")
    ]
    return tuple(sorted(faults, key=lambda f: f.occurred_at, reverse=True))
```

### A2. `surfaces/queries/__init__.py` — export `FaultView`, `open_faults`

### A3. `surfaces/render.py` — add `render_incidents`

```python
def render_incidents(faults: tuple[FaultView, ...], out) -> None:
    if not faults:
        print("no open incidents", file=out)
        return
    print(f"Open incidents: {len(faults)}", file=out)
    for f in faults:
        print(f"\n  [{f.fault_id}] {f.source_agent} · {f.capability}", file=out)
        print(f"  severity: {f.severity}", file=out)
        print(f"  {f.message}", file=out)
        print(f"  {f.occurred_at}", file=out)
```

### A4. `surfaces/cli_commands.py` — add `cmd_incidents`

```python
from surfaces.queries.faults import open_faults
from surfaces.render import render_incidents

def cmd_incidents(args: argparse.Namespace, ctx: SurfaceContext, out) -> None:
    del args
    render_incidents(open_faults(ctx.graph), out)
```

Update `cli.py`: add `sub.add_parser("incidents")` in `_parser()`; add
`if args.command == "incidents": cmd_incidents(args, ctx, out)` in `_dispatch()`.

### A5. Tests for incident view

**`surfaces/tests/test_queries.py`** — extend or new file `test_faults.py`:

- `open_faults` on an empty graph → empty tuple, no crash.
- `open_faults` with two `Fault` nodes → returns both, newest-first by `occurred_at`.

**`surfaces/tests/test_cli.py`** or `test_cli_narrative_approve.py` — extend:

- `cli incidents` on empty graph → `"no open incidents"`.
- `cli incidents` with a seeded `Fault` node → output contains the `source_agent` value.

## Part B — Explain on demand

### B1. `surfaces/cli_commands.py` — add `cmd_explain`

```python
from contracts.reporter import NarrativeRequest, TradeNarrative
from surfaces.render import render_explain

def cmd_explain(args: argparse.Namespace, ctx: SurfaceContext, out) -> None:
    pos_id = str(args.pos_id)
    response = ctx.bus.request(
        AgentMessage(
            sender="cli",
            recipient="reporter",
            message_type="request",
            capability="narrative",
            payload=NarrativeRequest(position_id=pos_id).model_dump(mode="json"),
        )
    )
    if response.message_type == "error":
        print(f"explain failed for position: {pos_id}", file=out)
        return
    narrative = TradeNarrative.model_validate(response.payload)
    render_explain(narrative, out)
```

(`AgentMessage` is already imported in `cli_commands.py`.)

Update `cli.py`: `explain` subparser with `pos_id` positional argument.

### B2. `surfaces/render.py` — add `render_explain`

```python
def render_explain(narrative: TradeNarrative, out) -> None:
    print(f"Narrative — position {narrative.position_id}", file=out)
    print(f"  {narrative.story.summary}", file=out)
    for ref in narrative.story.evidence_refs:
        print(f"    ref: {ref}", file=out)
```

(`TradeNarrative.story` is an `Explanation`; its text field is `.summary`. Verify prop name
against `contracts/common.py` before writing — do not guess.)

### B3. Tests for explain on demand

Extend `surfaces/tests/test_cli.py` or `test_cli_narrative_approve.py`:

- `cli explain <pos_id>` with a `test_context` that has a valid `Position` node linked to
  a full graph chain → calls `reporter.narrative`; output contains non-empty text (the
  narrative summary). The reporter agent must be bound in `test_context` (it already is).
- `cli explain <unknown_pos_id>` (reporter returns error) → `"explain failed"` message.

## Part C — P6 exit test

### C1. `surfaces/tests/test_p6_exit.py` — new file, ≤ 120L

Prove all four operator capabilities end-to-end using `test_context`:

```python
"""P6 exit criterion test.

Proves the four-part operator checklist: run, inspect, approve, recover, explain.
"""

def test_p6_run(ctx):
    """cli command 'run' is accepted and routed to orchestration."""
    result = _command(ctx, "run the daily scan")
    assert result.accepted
    assert result.routed_to == "orchestration.execute_run"

def test_p6_inspect_status(ctx):
    """cli status returns a health summary."""
    report = _status(ctx)
    assert report is not None

def test_p6_inspect_incidents(ctx, fault_graph):
    """cli incidents shows seeded fault."""
    faults = open_faults(fault_graph)
    assert any("analyst" in f.source_agent for f in faults)

def test_p6_approve(ctx, flag_graph):
    """cli approve resolves a pending flag."""
    result = _approve(ctx, flag_graph, "run/test-123")
    assert result.accepted
    assert flag_graph.list_nodes("FlagResolution")

def test_p6_explain(ctx, position_graph):
    """cli explain returns a narrative for a seeded position."""
    narrative = _explain(ctx, position_graph, <pos_id>)
    assert narrative.story.summary  # non-empty
```

(Use `test_context` factory from `surfaces/context.py`. Each helper `_command`, `_status`,
`_approve`, `_explain` does the bus call directly rather than going through `main()` — keeps
the test readable. Use inline fixture setup rather than complex parametrize.)

The test file name and structure are intentionally simple — the test is documentation of
the exit criterion, not an exhaustive integration suite.

## Steps

1. Branch `sprint-21-incidents-explain-p6-exit` off `main`.
2. **A0 first** (extract to `cli_commands_extra.py`). `make ci` must be green — zero behaviour
   change — before continuing.
3. **Part A**: `faults.py` → `__init__.py` → `render.py` → `cli_commands.py` → `cli.py` →
   incident tests. `make ci`.
4. **Part B**: `cli_commands.py` → `render.py` → `cli.py` → explain tests. `make ci`.
5. **Part C**: `test_p6_exit.py`. `make ci` must be fully green including the new P6 test.
6. **Line count check**: `wc -l surfaces/cli_commands.py surfaces/cli_commands_extra.py surfaces/render.py`.
   All must be < 200L.
7. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- `cli incidents` on empty graph → `"no open incidents"`.
- `cli incidents` with a seeded `Fault` node → output contains the agent name.
- `cli explain <pos_id>` calls `reporter.narrative` and renders `Explanation.summary`.
- `test_p6_exit.py` green: all five assertions pass.
- `cli_commands.py` < 200L; `cli_commands_extra.py` < 200L; `render.py` < 200L.
- Import-linter 4/4 kept.
- `make ci` green at/above coverage floor (100.00).

## Out of scope (do NOT build this sprint)

Fault acknowledgement/resolution (P9 observability); reject/modify intents (P7); MCP
tool-binding (next sprint after P6 closes, or Sprint 22); recommendation evidence view
(P7); scorecard surfaces (P7); position P&L arithmetic (needs sell-price fills).

## P6 exit evaluation (planning agent performs after merge)

After this sprint merges to `main`, verify the P6 exit criterion:

> "An operator can run, inspect, approve, and recover entirely from the dashboard."

The checklist:

| Capability | CLI entry point | Sprint delivered |
| ---------- | --------------- | ---------------- |
| Run | `cli command "run ..."` → `routed_to: orchestration.execute_run` | S20 |
| Inspect — status | `cli status` | S18 |
| Inspect — runs | `cli runs`, `cli run` | S18 |
| Inspect — positions | `cli positions`, `cli position` | S19 |
| Inspect — narratives | `cli narrative` | S20 |
| Inspect — incidents | `cli incidents` | **S21** |
| Approve | `cli flags`, `cli approve` | S20 |
| Recover (see faults) | `cli incidents` | **S21** |
| Explain on demand | `cli explain` | **S21** |

If all rows are green and `test_p6_exit.py` passes, close P6 in `docs/STATE.md` and
`docs/build-plan.md`. Plan Sprint 22 to begin P7 (researcher self-management) or as
a focused MCP tool-binding sprint before P7.

## Handback report (paste into PR / reply)

- Confirm `A0` extraction: list of functions moved to `cli_commands_extra.py`.
- Final line counts: `cli_commands.py`, `cli_commands_extra.py`, `render.py`.
- Confirm `Explanation.summary` is the correct field name (from `contracts/common.py`).
- Whether `test_p6_exit.py` revealed any gaps that needed patching.
- New coverage % and floor; note whether P6 exit criterion was met.

The planning agent will review, merge to `main`, update docs, close P6 if the exit test
passes, and plan Sprint 22.
