<!-- Agent: planning | Role: sprint handover -->
# Sprint 25 — P8 market pack + stage command wiring (P8 closes)

**Status:** planned · **Branch:** `sprint-25-p8-market-pack` · **Build phase:** P8 · **Effort: M**

## Goal

Close P8 with two deliverables: (1) wire the `"stage"` intent family end-to-end through
operator → supervisor gate → `execution.promote_stage`, making `cli stage promote <target>`
the operator's single entry point for stage transitions; (2) introduce the `MarketPack`
abstraction in the kernel and prove the P8 exit criterion (G6): a new market pack can be
registered and used without modifying kernel, contracts, agents, or orchestration.

## Why (context)

- Read first: `docs/sprints/README.md`; `docs/architecture.md`; `docs/build-plan.md`
  (P8 exit: "a new market pack can be added without core control-plane changes (G6)");
  `agents/supervisor/domain/matrix.py` (`"stage": RouteSpec(None, None, False)` and
  `"stage": "P8"` in BUILD_PHASES — **two one-line changes enable it**);
  `agents/supervisor/domain/gate.py` (68L — add `bus` parameter + `"stage"` inline
  execution; see Part A2);
  `agents/supervisor/agent.py` (`_dispatch_intent` calls `dispatch_intent(self._graph,
  intent)` — **add `self.bus` as a third argument**);
  `contracts/execution.py` (`PromoteStageRequest`, `PromoteStageResult` already declared;
  `promote_stage` capability already in CONTRACT from Sprint 24);
  `surfaces/cli_commands.py` (**184L — 16L from hard cap; A0 extraction is mandatory
  before any new commands**);
  `surfaces/context.py` (`SurfaceContext(graph, bus)` frozen dataclass — add
  `pack_registry: MarketPackRegistry | None = None`);
  `agents/scanner/universe.py` (`UniverseSource` protocol, `StaticUniverse` — the
  `MarketPack` wraps this, does not replace it);
  `agents/execution/settings.py` (`ExecutionStageValue` typedef — `MarketPack.max_stage`
  uses the same literal type).

- **`stage` wiring pattern.** The gate already handles `approve` inline by calling
  `resolve_flag_by_subject(graph, ...)`. The `stage` family follows the same pattern:
  when `spec.available` and `family == "stage"`, the gate calls `execution.promote_stage`
  via the bus and returns a `DispatchResult` whose `rejection` carries the result reason.
  The gate needs bus access to make this call — add `bus: MessageBus | None = None` to
  `dispatch_intent`. The supervisor's `_dispatch_intent` passes `self.bus`.
  Import `PromoteStageRequest` + `PromoteStageResult` from `contracts.execution` in
  `gate.py` (allowed — contracts are the shared vocabulary; no agent imports another agent).

- **`cli stage promote` command.** Does NOT call `operator.interpret`. Like `cli approve`,
  it pre-builds a `TypedIntent` directly and calls `supervisor.dispatch_intent`. This avoids
  LLM round-trip for an unambiguous structural command:
  ```python
  TypedIntent(
      family="stage",
      parameters={"stage": target_stage, "confirmed": "true" if confirmed else ""},
      requires_confirmation=True,
      provenance=Provenance(run_id=correlation_id("stage", target_stage), source_agent="cli"),
  )
  ```
  The gate enforces the confirmation requirement (re-routes through the existing confirmation
  flag pattern if `confirmed != "true"`). This is identical to how `cli approve` works.

- **`MarketPack` abstraction.** Minimal Protocol in `kernel/market_pack.py` — do NOT add
  any trading knowledge to the kernel. The pack declares: `name`, `exchange`, `universe_name`
  (maps to an existing `StaticUniverse` key), `data_source_key` (informational for now),
  `max_stage: ExecutionStage` (the highest stage this pack supports), and
  `is_ready() → tuple[bool, str]`. A `MarketPackRegistry` holds named packs.
  The default `USEquitiesSP500Pack` lives in `orchestration/packs/` (not kernel — packs are
  domain objects).

- **G6 proof.** The P8 exit test proves G6 by registering a second `EuropeStocksTestPack`
  alongside the default SP500 pack without touching any kernel, contracts, agents, or
  orchestration source file. The pack is defined entirely in the test file. The registry
  accepts it, lists it, and reports its readiness — all without core changes.

- **`cli packs` surface.** The CLI reads `ctx.pack_registry.all_packs()` (via
  `SurfaceContext.pack_registry`). The `SurfaceContext` gains an optional `pack_registry`
  field; `paper_context()` and `test_context()` wire up a default registry containing
  `USEquitiesSP500Pack`.

## Part A0 — Prerequisite: free `cli_commands.py` headroom (zero-behaviour refactor)

`cli_commands.py` is 184L. Any new command pushes it past the hard cap. **Before any other
changes**, extract the three read-only query commands added in recent sprints:

### A0.1 New file: `surfaces/cli_commands_queries.py` — ≤ 60L

```python
"""Read-only CLI query command handlers (explain, stage, proposals).

Agent: surfaces
Role: implement read-only sub-commands behind the argparse glue.
External I/O: MessageBus calls through the injected surface context.
"""
```

Move `cmd_explain`, `cmd_stage`, and `cmd_proposals` (and any imports used only by them)
from `cli_commands.py` into this file.

### A0.2 Update `cli.py`

Import these three handlers from `cli_commands_queries` instead of `cli_commands`.

**Run `make ci` after A0** — must be green (zero behaviour change). `cli_commands.py`
should reach ~154L; `cli_commands_queries.py` ~30L.

## Part A — Wire `stage` through supervisor gate

### A1. `agents/supervisor/domain/matrix.py`

Two changes:
1. Enable: `"stage": RouteSpec("execution", "promote_stage", True)`.
2. Remove `"stage"` from `BUILD_PHASES` dict.

### A2. `agents/supervisor/domain/gate.py` — ≤ 90L after change

Update `dispatch_intent` signature:
```python
def dispatch_intent(
    graph: GraphStore, intent: TypedIntent, *, bus: MessageBus | None = None
) -> DispatchResult:
```

Add `MessageBus` import under `TYPE_CHECKING`. Add `PromoteStageRequest` +
`PromoteStageResult` imports from `contracts.execution` (always imported — not
`TYPE_CHECKING` since used at runtime).

After the `spec.available` check, add the `stage` special-case **before** the approve
special-case:

```python
if intent.family == "stage" and bus is not None:
    target = intent.parameters.get("stage") or intent.parameters.get("target", "")
    confirmed = intent.parameters.get("confirmed") == "true"
    response = bus.request(AgentMessage(
        sender="supervisor",
        recipient="execution",
        message_type="request",
        capability="promote_stage",
        payload=PromoteStageRequest(
            target_stage=target,  # type: ignore[arg-type] - validated by execution agent
            reason=f"operator stage request via {intent.provenance.source_agent}",
            confirmed=confirmed,
        ).model_dump(mode="json"),
    ))
    promote = PromoteStageResult.model_validate(response.payload)
    if promote.accepted:
        return DispatchResult(
            accepted=True,
            routed_to="execution.promote_stage",
            provenance=promote.provenance,
        )
    return rejected(intent.provenance.run_id, promote.reason)
```

`AgentMessage` is importable from `kernel` (the kernel exports it). Verify the exact import
path from existing gate.py imports or from `kernel/__init__.py` before writing.

### A3. `agents/supervisor/agent.py`

Update `_dispatch_intent`:
```python
result = dispatch_intent(self._graph, intent, bus=self.bus)
```

`self.bus` is available on `AgentBase` — all agents inherit it.

### A4. `surfaces/cli_commands.py` — add `cmd_stage_promote` (≤ 175L total)

```python
from contracts.common import Provenance
from contracts.operator import TypedIntent

def cmd_stage_promote(args: argparse.Namespace, ctx: SurfaceContext, out) -> None:
    target = str(args.target)
    confirmed = getattr(args, "confirmed", False)
    intent = TypedIntent(
        family="stage",
        parameters={"stage": target, "confirmed": "true" if confirmed else ""},
        requires_confirmation=True,
        provenance=Provenance(
            run_id=f"stage:{target}",
            source_agent="cli",
        ),
    )
    response = ctx.bus.request(AgentMessage(
        sender="cli",
        recipient="supervisor",
        message_type="request",
        capability="dispatch_intent",
        payload=intent.model_dump(mode="json"),
    ))
    result = DispatchResult.model_validate(response.payload)
    if result.accepted:
        print(f"stage promotion dispatched to {result.routed_to}", file=out)
    else:
        print(f"refused: {result.rejection}", file=out)
```

### A5. `surfaces/cli.py` — `stage promote` subcommand

Extend the existing `stage` subparser to have a `promote` sub-subcommand with a `target`
positional argument and an optional `--confirmed` flag. Wire to `cmd_stage_promote`.

The existing `cli stage` (read-only status display) stays as the default action when no
sub-subcommand is given.

### A6. Tests for stage wiring

**`agents/supervisor/tests/test_stage_dispatch.py`** — ≤ 60L:
- `dispatch_intent` with `family="stage"`, sufficient evidence, `confirmed="true"` →
  calls `execution.promote_stage`, returns `accepted=True, routed_to="execution.promote_stage"`.
- `dispatch_intent` with insufficient evidence → returns `accepted=False, rejection` contains
  "need N runs" or "confirmation required".
- `dispatch_intent` without bus (`bus=None`) → stage dispatch skipped, falls through to
  `not_available_reason` (graceful degradation when bus unavailable).

Wait — without bus, the spec is now `available=True` but there's no bus. Add a guard: if
`intent.family == "stage"` and `bus is None`, return a `rejected` with reason `"stage
dispatch requires bus context"`. This prevents silent no-ops.

**`surfaces/tests/test_stage_promote_cli.py`** — ≤ 60L:
- `cli stage promote broker_shadow` with seeded snapshots and approval → dispatches correctly.
- `cli stage promote broker_shadow` without evidence → "refused: need N runs".
- `cli stage promote broker_shadow` (first call, evidence ok) → "refused: confirmation required".
- `cli stage promote broker_shadow --confirmed` (after first call + FlagResolution) → accepted.

## Part B — `MarketPack` abstraction

### B1. `kernel/market_pack.py` — ≤ 60L

```python
"""Market-pack protocol and registry — kernel-level abstractions only.

No trading knowledge: the kernel owns the shape; packs live in orchestration.
External I/O: none.
"""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.execution import ExecutionStage


class MarketPack(Protocol):
    """One tradeable universe + its exchange, data-source mapping, and stage ceiling."""

    name: str
    exchange: str
    universe_name: str
    data_source_key: str
    max_stage: str   # ExecutionStage literal; Protocol uses str to avoid import cycle

    def is_ready(self) -> tuple[bool, str]:
        """Return (ready, reason). Reason is operator-readable."""
        ...  # pragma: no cover


class MarketPackRegistry:
    """Mutable registry of named market packs."""

    def __init__(self) -> None:
        self._packs: dict[str, MarketPack] = {}

    def register(self, pack: MarketPack) -> None:
        """Register a pack; silently replaces an existing entry with the same name."""
        self._packs[pack.name] = pack

    def get(self, name: str) -> MarketPack | None:
        return self._packs.get(name)

    def all_packs(self) -> tuple[MarketPack, ...]:
        return tuple(self._packs.values())
```

Update `kernel/__init__.py` to export `MarketPack` and `MarketPackRegistry`.

### B2. `orchestration/packs/__init__.py` + `orchestration/packs/us_equities_sp500.py` — ≤ 40L

```python
"""US Equities S&P 500 market pack.

Agent: orchestration
Role: declare the default universe, exchange, and readiness policy for the SP500 pack.
External I/O: none.
"""

class USEquitiesSP500Pack:
    """Default paper-stage pack: S&P 500 universe on NYSE/NASDAQ via Stooq."""

    name = "us_equities_sp500"
    exchange = "NYSE/NASDAQ"
    universe_name = "sp500"
    data_source_key = "stooq"
    max_stage = "paper"

    def is_ready(self) -> tuple[bool, str]:
        return True, "default pack; always ready for paper stage"
```

### B3. `surfaces/context.py` — add `pack_registry` to `SurfaceContext`

```python
from kernel import MarketPack, MarketPackRegistry  # (or from kernel.market_pack)
from orchestration.packs.us_equities_sp500 import USEquitiesSP500Pack

@dataclass(frozen=True)
class SurfaceContext:
    graph: GraphStore
    bus: MessageBus
    pack_registry: MarketPackRegistry = field(default_factory=MarketPackRegistry)
```

Update `paper_context()` and `_context()` to register `USEquitiesSP500Pack` in the
default registry. Update `test_context()` similarly (single pack registered by default).

### B4. `surfaces/queries/packs.py` — ≤ 40L

```python
"""Pack query projections.

Agent: surfaces
Role: project MarketPackRegistry into display-ready views.
External I/O: none.
"""

@dataclass(frozen=True)
class PackView:
    name: str
    exchange: str
    universe_name: str
    max_stage: str
    ready: bool
    ready_reason: str

def all_packs(registry: MarketPackRegistry) -> tuple[PackView, ...]:
    return tuple(
        PackView(
            name=p.name,
            exchange=p.exchange,
            universe_name=p.universe_name,
            max_stage=p.max_stage,
            ready=ready,
            ready_reason=reason,
        )
        for p in registry.all_packs()
        for ready, reason in (p.is_ready(),)
    )
```

### B5. `surfaces/render.py` — add `render_packs` (≤ 175L total)

```python
def render_packs(packs: tuple[PackView, ...], out) -> None:
    if not packs:
        print("no market packs registered", file=out)
        return
    print(f"Market packs: {len(packs)}", file=out)
    for p in packs:
        status = "ready" if p.ready else f"not ready: {p.ready_reason}"
        print(f"\n  {p.name}  ({p.exchange})  stage-ceiling: {p.max_stage}", file=out)
        print(f"  universe: {p.universe_name}  status: {status}", file=out)
```

### B6. `surfaces/cli_commands.py` — add `cmd_packs`

```python
def cmd_packs(args: argparse.Namespace, ctx: SurfaceContext, out) -> None:
    del args
    from surfaces.queries.packs import all_packs
    from surfaces.render import render_packs
    render_packs(all_packs(ctx.pack_registry), out)
```

### B7. `surfaces/cli.py` — `cli packs` subcommand

## Part C — P8 exit test

### C1. `surfaces/tests/test_p8_exit.py` — ≤ 80L

```python
"""P8 exit criterion: G6 — new market pack without core control-plane changes.

Proves that a new MarketPack implementation can be registered and queried
without modifying kernel, contracts, agents, or orchestration source files.
"""

from kernel import MarketPackRegistry
from orchestration.packs.us_equities_sp500 import USEquitiesSP500Pack
from surfaces.queries.packs import all_packs

class EuropeStocksTestPack:
    """Fictitious second pack defined entirely in test scope."""
    name = "europe_stocks_test"
    exchange = "LSE"
    universe_name = "lse_100"
    data_source_key = "test"
    max_stage = "paper"
    def is_ready(self) -> tuple[bool, str]:
        return False, "test pack not production-ready"

def test_p8_register_second_pack_no_core_changes():
    """New pack added to registry without touching kernel/contracts/agents/orchestration."""
    registry = MarketPackRegistry()
    registry.register(USEquitiesSP500Pack())
    registry.register(EuropeStocksTestPack())
    packs = registry.all_packs()
    assert len(packs) == 2
    names = {p.name for p in packs}
    assert "us_equities_sp500" in names
    assert "europe_stocks_test" in names

def test_p8_pack_readiness():
    """Packs report their own readiness without core knowledge."""
    registry = MarketPackRegistry()
    registry.register(USEquitiesSP500Pack())
    registry.register(EuropeStocksTestPack())
    views = all_packs(registry)
    sp500 = next(v for v in views if v.name == "us_equities_sp500")
    eu = next(v for v in views if v.name == "europe_stocks_test")
    assert sp500.ready
    assert not eu.ready

def test_p8_cli_packs_shows_both(ctx_with_two_packs):
    """cli packs surface renders two packs from registry."""
    ...

def test_p8_stage_promote_end_to_end(ctx, snapshots_ok):
    """cli stage promote → supervisor → execution.promote_stage dispatched."""
    ...
```

Use `test_context()` fixture throughout. `ctx_with_two_packs` is a local fixture that
creates a `test_context` and registers both `USEquitiesSP500Pack` and `EuropeStocksTestPack`
into `ctx.pack_registry`.

## Steps

1. Branch `sprint-25-p8-market-pack` off `main`.
2. **A0 first** (extract to `cli_commands_queries.py`). `make ci` green before any new code.
3. **Part A1–A3**: matrix + gate + supervisor wiring. `make ci`.
4. **Part A4–A6**: `cmd_stage_promote` + CLI subcommand + stage dispatch tests. `make ci`.
5. **Part B1–B2**: `kernel/market_pack.py` + `orchestration/packs/`. `make ci`.
6. **Part B3–B7**: `SurfaceContext` update + queries/packs + render + cli. `make ci`.
7. **Part C**: `test_p8_exit.py`. `make ci` final — must be fully green.
8. **Line count check**: `wc -l surfaces/cli_commands.py surfaces/cli_commands_queries.py
   surfaces/render.py agents/supervisor/domain/gate.py kernel/market_pack.py`.
   All < 200L.
9. Push; hand back.

## Acceptance criteria

- `cli stage promote broker_shadow` (with seeded evidence + approval) → dispatches through
  supervisor gate → `execution.promote_stage` called → `StageTransition` written.
- `cli stage promote broker_shadow` without evidence → "refused: need N runs".
- `MarketPackRegistry.register()` + `all_packs()` work without any imports from agents or
  orchestration in the test.
- `test_p8_exit.py` green: `EuropeStocksTestPack` registered without touching core.
- `cli packs` shows both packs with correct readiness status.
- `gate.dispatch_intent(graph, intent, bus=None)` with `family="stage"` → graceful error
  ("stage dispatch requires bus context") rather than silent no-op.
- `cli_commands.py` ≤ 175L; `cli_commands_queries.py` ≤ 60L; `render.py` ≤ 175L;
  `gate.py` ≤ 90L; `market_pack.py` ≤ 60L.
- Import-linter 4/4 kept (gate imports `contracts.execution` — allowed; no agent imports
  another agent; kernel `market_pack.py` imports only typing).
- `make ci` green at/above coverage floor (100.00).

## P8 exit evaluation (planning agent performs after merge)

P8 exit criterion: "a new market pack can be added without core control-plane changes (G6)."

| Capability | Status |
| --- | --- |
| `MarketPack` Protocol in kernel | S25 |
| `MarketPackRegistry` in kernel | S25 |
| Default `USEquitiesSP500Pack` registered | S25 |
| G6 proof: `EuropeStocksTestPack` registered in test-only scope | S25 |
| `cli packs` surfaces registered packs | S25 |
| Stage gate machinery | S24 |
| `cli stage promote` through operator/supervisor | S25 |

If `test_p8_exit.py` passes and G6 is met, close P8 in STATE.md + build-plan.md.

## Out of scope (do NOT build this sprint)

Operator `interpret` LLM path for `"stage"` text commands (FakeLLMClient already handles
it; real LLM usage deferred to P9 hardening); Alpaca broker client (P9+); exchange calendar
implementation (stub sufficient — `USEquitiesSP500Pack.exchange = "NYSE/NASDAQ"` is the
declaration; calendar enforcement is P9); per-pack readiness checklists beyond `is_ready()`
(P9); pack-specific risk policy overrides (P9); proposal range validation in supervisor
gate (P9 hardening pass).

## Handback report (paste into PR / reply)

- Confirm A0 extraction: `cli_commands.py` final line count; `cli_commands_queries.py` line count.
- Confirm gate.py line count and that `bus=None` guard is present.
- Confirm `kernel/__init__.py` exports `MarketPack` and `MarketPackRegistry`.
- Confirm `SurfaceContext.pack_registry` is non-optional (has a default factory) so
  existing tests don't break.
- `test_p8_exit.py` result — specifically whether `EuropeStocksTestPack` was defined
  entirely in test scope with no core file changes.
- New coverage % and floor; total test count.

The planning agent will review, merge to `main`, close P8 if G6 is met, and plan Sprint 26
(P9 — observability stack: Prometheus + Grafana over the metrics adapter).
