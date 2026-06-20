# Sprint 69 — Provider law cycle: lock the template

**Branch:** `sprint-69-provider-law-cycle`
**Version bump:** 0.10.0 → 0.11.0 (feat/MINOR — law infrastructure is production
behaviour change: caller authz gate + benchmark field)

---

## Goal

Complete the provider law's full *author → reconcile → test → green* cycle and lock
`agents/provider/laws/laws.md` as v1, making the template safe to copy to the eleven
remaining agents (conventions §11).

Two OPEN drifts blocked the cycle:

- **DRIFT-006** (`PROV-OUT-01`): benchmark was fetched as a separate `provider_client`
  request (S38 workaround). Law says it is a requested *field* of the market-data
  request.
- **DRIFT-007** (`PROV-SEC-07`): `Capability.allowed_callers` was declared in the
  contract but never enforced in any bus implementation.

Both were forced decisions: DRIFT-006 → change code to match rule; DRIFT-007 → build
enforcement now.

---

## What shipped

### DRIFT-007 — Caller authorization gate

**`kernel/bus.py`** — New predicate `caller_authorized(allowed_callers, sender)`:
empty tuple = unrestricted, non-empty = gate. `MessageBus` Protocol gains `allowed_callers`
param on `register()`. `InProcessBus` stores per-`(recipient, capability)` allowed list and
checks it before dispatch — unauthorized sender gets an `Unauthorized` error response.

**`kernel/bus_azure.py`** and **`kernel/bus_celery.py`** — Same gate pattern imported
from `kernel.bus`.

**`kernel/agent.py`** — `AgentBase.bind()` passes `capability.allowed_callers` to
`bus.register()`.

**`contracts/provider.py`** — Provider capabilities gain real caller lists:
`get_market_data` → `(scanner, analyst, portfolio_manager, monitor, forecaster)`;
`get_regime` → `(analyst, portfolio_manager)`. CONTRACT 0.4.0 → 0.5.0.

**Tests:** `tests/test_bus.py`, `tests/test_bus_azure.py`, `tests/test_bus_celery.py`
each gain an authz test; `test_provider_reconcile.py::test_unauthorized_caller_is_refused_by_the_capability_gate`
cites PROV-SEC-07.

All existing provider tests updated: `sender="tester"` → `sender="analyst"` (bulk
replace; tester is no longer in `get_market_data`'s allowed list).

### DRIFT-006 — Benchmark as a first-class `DataRequest` field

**`contracts/provider.py`** — `DataRequest` gains `benchmark_ticker: Ticker | None`
and `fields` now documents `"benchmark"` as a supported field. `MarketData` gains
`benchmark: tuple[OHLCVBar, ...] = ()`.

**`agents/provider/market_fields.py`** — `OptionalFields` gains `benchmark`;
`collect_optional_fields` gains `benchmark_ticker` param; `_fetch_optional` gains
`taint: bool = True` — the benchmark fetch passes `taint=False` so a degraded
benchmark never sets `used_fallback` on the candidate quality.

**`agents/provider/agent.py`** — passes `benchmark_ticker=data_request.benchmark_ticker`
and returns `benchmark=optional.benchmark`.

**`agents/analyst/provider_client.py`** — `request_benchmark_bars` removed;
`request_market_data` gains `benchmark_ticker` param and includes `"benchmark"` in
`fields`.

**`agents/analyst/agent.py`** — removed `request_benchmark_bars` import/call; uses
`market.benchmark` directly.

**Tests:** `test_provider_reconcile.py::test_benchmark_is_served_as_a_field_without_tainting_candidate_quality`
cites PROV-OUT-01; `tests/test_relative_strength.py` rewritten to use
`request_market_data` + `benchmark_ticker`.

### Provider law citation pass

Law-ID docstrings added to **7 provider test files** (domain, fundamentals, news,
sentiment, sector\_source, earnings\_source, pubsub) covering all clauses with
existing tests. `PROV-NEV-08` (raw headlines, no classification) gets its citation.

### test-plan.md bound and green

23 of 43 testable clauses turned 🟩. 20 gap tests remain ⬜ — written in later
sprints as the provider gains real source integration. Remaining gaps are logged
with `_tbd_` in the test-plan (non-blocking; conventions allow partial green at lock).

### laws.md locked

Status changed DRAFT v0 → **LOCKED v1**. Divergence register updated:
DRIFT-006 and DRIFT-007 both **CORRECTED**. Changelog v1 entry added.

### Template locked

`docs/laws/_TEMPLATE.md` gains a lock comment (S69, 2026-06-20): do not copy an
earlier version; copy from this commit forward.

`docs/laws/ledger.md` provider row updated to 🟨 partial (23/43 green; template
now locked).

---

## Test counts

| Metric | Value |
| --- | --- |
| Tests at start (v0.10.0) | 894 |
| Tests at end (v0.11.0) | 894 |
| Coverage | 100.00 % |
| New files | `agents/provider/tests/test_provider_reconcile.py` |

---

## Not in scope

- CAP + PARAM backfills for the 11 other agents (S70+; gated on this locked template).
- `system_prompt` tunable on operator/forecaster settings (separate chore, ADR-0010
  immediate consequence; not a MINOR-worthy change).
- Remaining ⬜ gap tests in the provider test-plan (later sprints, non-blocking).
