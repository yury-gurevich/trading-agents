<!-- Agent: planning | Role: sprint handover -->
# Sprint 136 — Realized PnL from actual fills + a CVE gate that can fail

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-136-realized-pnl-and-gate-integrity`
**Status:** ready for handover (packaged 2026-07-24)
**Effort:** M
**Decisions:** [ADR-0015 §1 + amendment](../decisions/0015-exit-lifecycle-and-stop-ownership.md)

---

## Why this sprint

Two unrelated-looking items, one theme: **the system must not present absent evidence as
measured evidence.** That single defect shape has now produced four separate incidents (DL-57
gate self-test, the phantom `replicas=0`, an acceptance gate that passed on two dead days, and
fabricated realized PnL). Both items below close a remaining instance of it.

### Part A — realized PnL has no source of truth

`agents/monitor/decide.py` used to compute realized `pnl_cents` at **decision** time; 0.74.03
stopped that and marked the seven historical entries `pnl_invalidated_at`. Correct, but it left
the system with **no realized PnL at all**: the reporter now returns
`{closed_trades_with_pnl: 0.0}` and omits `profit_factor` / `expectancy_cents` entirely.

That was deliberate — ADR-0015's amendment records it — because there had never been a filled
sell to derive from or test against. **That blocker is gone:** `ABT 98 @ $101.35` filled
2026-07-23T13:31:36Z (entry $100.78). Realized PnL now has a real source, and a real data point
to verify against.

### Part B — `make ci` cannot fail on a CVE (hardening row L)

The Makefile runs `-uv run pip-audit`. The leading `-` makes make **ignore its exit status**, so
a vulnerable dependency never fails the local gate, while `CLAUDE.md` advertises 9 steps that
fail. GitHub's `security` job runs `pip-audit` *without* the dash, so remote CI does fail — the
**local** gate, the one a developer trusts before pushing, silently does not.

Row L's unblock trigger is "next time `gate_selftest.py` is touched": that script exists to prove
each gate can fail, and it does not cover this one.

---

## Part A — spec

**Compute realized PnL when a sell fill is confirmed, from the price actually traded.**

1. **Source of truth is the sell `Fill`.** When broker evidence confirms a sell filled
   (`agents/execution/reconciliation_store.py::refresh_pending_fills`, which already appends
   `broker_status` and `broker_price_cents`), append a realized figure to that Fill node.
   Appending a **new** property key is permitted; overwriting is not — the store is append-only
   (`kernel/graph_support.py`). Never rewrite an existing value.

2. **Entry basis must come from the position actually sold**, not a guess. `OrderIntent` carries
   `position_ref` on sells (0.74.01), and `contracts/positions.py` can resolve the contributing
   `Position` nodes and their `opened_price_cents`. Use `realized_pnl_cents()` — kept and
   unit-tested for exactly this — for the arithmetic.

3. **If the entry basis cannot be determined, write nothing.** Do not fall back to an assumed
   price, an average, or zero. An unknown is unknown; that is the whole point of this sprint.
   Record a `Fault` (the `GraphFaultSink` is already wired) so an unresolvable fill is visible
   rather than silent.

4. **Partial fills:** realize only on the quantity actually filled. A remainder stays open and is
   realized when it fills (ADR-0015 §5).

5. **The reporter reads realized PnL from fills, not from `CloseDecision`.** Update
   `agents/reporter/domain/trade_outcomes.py` accordingly, and **keep** the existing behaviour of
   omitting `profit_factor` / `expectancy_cents` when there is no evidence — that must not
   regress into a confident `0.0`.

6. `CloseDecision.pnl_cents` stays as historical evidence, still skipped when
   `pnl_invalidated_at` is present. Do not delete or rewrite it.

**Out of scope:** unrealized PnL, fees/commissions, tax lots, multi-lot cost-basis policy
(FIFO/LIFO). If a decision beyond "use the position's `opened_price_cents`" is needed, **stop and
report** rather than inventing a policy.

### Part A — required tests

Test the **graph-pull** path (`poll.py` / `cascade_once`), not only the bus path — a test that
only proves the bus path is worthless here (DL-60 is exactly that lesson).

- A confirmed sell fill produces a realized figure computed from the **fill** price, not the
  decision price.
- The known-good case: entry 10078c, sell fill 10135c, qty 98 → **+5586c** (this is the real ABT
  trade; assert the arithmetic against it).
- A sell fill whose entry basis cannot be resolved writes **no** realized figure and records a
  `Fault`.
- A partial fill realizes only the filled quantity.
- The reporter computes `profit_factor` / `expectancy_cents` from fills once evidence exists, and
  still **omits** them when none does.
- Re-running the refresh does not double-write or raise (append-only safety).

## Part B — spec

1. Remove the `-` prefix from `pip-audit` in the `ci` target so a CVE fails the local gate as
   `CLAUDE.md` claims. Confirm the other 8 steps' behaviour is unchanged.
2. Add a `gate_selftest.py` case that **plants a failing condition for the CVE gate and requires a
   non-zero exit**, so this blind spot cannot regress. Follow the existing case structure; the
   script's purpose is proving a gate can fail, and every case must be demonstrated in both
   directions.
3. If `pip-audit` cannot reach the network in the execution sandbox, say so plainly in the
   handback rather than reporting a pass it did not observe. A sandboxed `pip-audit` is not
   evidence of a clean audit.

---

## Hard constraints (CLAUDE.md)

- `make ci` must pass: 9 steps, **100% coverage floor enforced** — every new line needs a test.
- Module size: **200 lines hard block**, 150 warn. Split rather than grow; several touched files
  are already near the limit.
- Layering: `kernel <- contracts <- agents <- orchestration/surfaces`. Agents never import other
  agents (import-linter enforces).
- Version in `pyproject.toml`: this is a **feat** (new capability: realized PnL) → bump the **two
  middle digits**: `0.74.03` → `0.75.00`.
- Law-clause tests cite their clause ID in the docstring.
- No `# noqa` to bypass any gate.
- **The graph records facts; it does not hold mutable records.** "Update X to the latest Y" is not
  expressible — append a new fact, or a marker superseding an old one (ADR-0015 amendment).

## Do not

- Do not commit, push, merge, or touch `main`.
- Do not modify `docs/STATE.md`, any ADR, `infra/`, or any `.env`.
- Do not deploy, and do not run any repair or teardown script against the live database.
- Do not change closure semantics, `order_from_close`, or `order_from_intent`.
- Do not resolve the monitor-vs-analyst decider conflict — that is an **open operator decision**
  (ADR-0015 amendment, final section) and is explicitly out of scope.

---

## Closeout — evidence (coding agent fills at handback; never leave this placeholder)

- **Files changed:** `Makefile`; `pyproject.toml`; `uv.lock`; `contracts/pnl.py`;
  `contracts/positions.py`; `agents/monitor/domain/exit_rules.py`;
  `agents/execution/realized_pnl.py`; `agents/execution/reconciliation.py`;
  `agents/execution/reconciliation_store.py`;
  `agents/execution/tests/test_realized_pnl_refresh.py`;
  `agents/execution/tests/test_realized_pnl_multilot.py`;
  `orchestration/tests/test_realized_pnl_graph_pull.py`;
  `agents/reporter/domain/trade_outcomes.py`; `agents/reporter/result.py`;
  `agents/reporter/tests/test_trade_outcomes.py`;
  `agents/reporter/tests/test_reporter_agent.py`; `tests/test_positions_contract.py`;
  `scripts/gate_selftest.py`; `scripts/gate_selftest_cases.py`;
  `docs/sprints/sprint-136-realized-pnl-and-gate-integrity.md`.
- **`make ci` verbatim result:**
  ```text
  uv run ruff check . --output-format=github
  uv run ruff format --check .
  778 files already formatted
  uv run mypy kernel contracts agents orchestration surfaces
  Success: no issues found in 657 source files
  Contracts: 4 kept, 0 broken.
  Required test coverage of 100.0% reached. Total coverage: 100.00%
  ====================== 1774 passed, 6 skipped in 32.30s =======================
  uv run pip-audit
  No known vulnerabilities found
  uv run pre-commit run detect-secrets --all-files
  Detect secrets...........................................................Passed
  uv run python scripts/check_untracked_secrets.py
  Detect secrets...........................................................Passed
  detect-secrets (untracked): scanning 5 new file(s)
  ```
  Command exit code: `0`.
- **Realized-PnL proof (the ABT arithmetic):** graph-pull test
  `orchestration/tests/test_realized_pnl_graph_pull.py::test_cascade_once_refreshes_abt_sell_fill_realized_pnl_from_broker_price`
  seeds entry `opened_price_cents=10078`, a pending sell Fill whose decision-time
  `price_cents=1`, and broker evidence `ABT sell quantity=98 price=$101.35`.
  Reconciliation appends `broker_price_cents=10135` and `realized_pnl_cents=5586`.
  Arithmetic: `(10135 - 10078) * 98 = 57 * 98 = 5586`.
- **Part B both directions (gate passes clean / fails on a planted CVE):**
  clean direction is covered by final `make ci` running non-ignored `uv run pip-audit`
  and reporting `No known vulnerabilities found`. Failure direction on the final tree:
  ```text
  PASS  can-fail: pip-audit-cve — rejected (exit 1)
  PASS  invariant: pip-audit-not-ignored-by-ci — present
  gate self-test: 9/9 passed
  ```
- **Anything not done, and why:** no commit, push, merge, deploy, ADR/STATE/infra/.env
  edit, live database repair, or monitor-vs-analyst decider resolution was performed; all
  were explicitly out of scope. No unsettled implementation decision was encountered.
