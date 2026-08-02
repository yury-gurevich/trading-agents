<!-- Agent: planning | Role: chore handover -->
# Chore — `EXEC-FAIL-03` proven in full, and the rule that stops a clause shrinking to fit its test

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `chore-exec-fail-03-coverage`
**Status:** SHIPPED — see [Closeout](#closeout)
**Version:** fix → **0.85.06** (PATCH: last two digits)
**Effort:** S
**Decisions:** [ADR-0021](../decisions/0021-clause-summary-mirrors-the-law.md) a clause summary
mirrors the law, never the test · [conventions §3/§4/§7/§7a](../laws/conventions.md) ·
[DL-70](../design-log.md) a test is only trusted once observed failing ·
[LAW-02](../../ops/laws/LAW-02-successful-execution.md) success is proven, never assumed

> **Why PATCH.** No new capability and no production behaviour change — three functional tests, a
> corrected law-book row, and a convention. `0.85.05` → **`0.85.06`**.

---

## Why this chore

S151 flipped `EXEC-FAIL-03` ⬜ → 🟩 on a roll-up-containment test that proved one third of it, **and
reworded the clause summary in `test-plan.md` toward that test's scenario** so the row read as a
complete match. The planning review reverted the flip and returned execution to 30 / 57, leaving two
things owed: the missing coverage, and a rule so the rewording cannot recur.

The clause, as locked:

> **EXEC-FAIL-03** — Graph write failure → **fault recorded**; fills already held in-process are safe
> (**idempotency key prevents re-submission to broker**). Safe to retry: **a repeated graph write
> appends a new record**.

Three conjuncts. The kept S151 test
(`test_drop_sweep_append_safe.py::test_rollup_failure_is_contained_after_drops_are_recorded`) covers
the first, in the drop-sweep path. This chore proves all three in the **submit** path, which is where
the clause bites: a spine outage between the broker accepting an order and the graph recording it.

---

## What shipped

**`agents/execution/tests/test_graph_write_failure_retry.py`** — a `FillWriteFailsOnceGraph` whose
first `Fill` write raises, and a `RecordingBroker` that logs the idempotency key of every submit.

| # | Test | Conjunct proved |
| --- | --- | --- |
| 1 | `test_graph_write_failure_is_faulted_and_persists_no_fill` | Fault recorded (`RuntimeError`, capability `submit`), `submitted=0`, zero `Fill` nodes — and the order **did** reach the broker |
| 2 | `test_retry_after_graph_write_failure_never_resubmits_to_the_broker` | Two submit calls, **one stable idempotency key** → one broker order, and the retry writes the `Fill` |
| 3 | `test_repeated_graph_write_appends_instead_of_overwriting` | An unchanged rewrite replays onto ordinal 0; a changed one **appends** `…#1` with ordinal 0 preserved |

**Law book.** `EXEC-FAIL-03` summary widened to carry all three conjuncts and flipped 🟩; execution
**30 → 31 / 57** in `ledger.md` and `laws/INDEX.md`.

**[ADR-0021](../decisions/0021-clause-summary-mirrors-the-law.md) + [conventions §7a](../laws/conventions.md)** — the standing convention, written where it binds
rather than left in a return note. Inserted as **§7a**, not renumbered to §12: sprint docs and test
docstrings cite `conventions §3/§4/§7`, and renumbering would break those the way renumbering a
clause ID breaks traceability (§2).

---

## Planted failures — observed, not assumed (DL-70)

Each conjunct was watched failing on a defect planted in production code, then reverted.

| Conjunct | Planted defect | Observed failure |
| --- | --- | --- |
| Fault recorded | `run_submit`'s outer `fault_boundary` given a throwaway sink | `AssertionError: assert [] == ['RuntimeError']` |
| Idempotency key | `order_from_intent` appends a `uuid4` to the key | `assert ['pm-run-fixture:AAPL:buy:7d4c89dd…'] == ['pm-run-fixture:AAPL:buy']`; measured consequence: **broker `order_count = 2`**, two Fill nodes — the oversell hazard 0.74.01 closed |
| Repeated append | `select_fill_attempt` always returns ordinal 0 | `ValueError: property 'status' cannot be overwritten` — the DL-79 collision shape |

**One assertion was wrong and was replaced, not explained away.** The first draft used
`PaperBroker.order_count` alone to prove "no re-submission". Planting a broker that never de-dupes
left the test **passing**, because `PaperBroker._fills` is itself keyed by idempotency key — the
probe measured the fake's storage, not the property. Replaced with `RecordingBroker.submissions`,
which records what the caller actually sent, and re-planted at the real source: an unstable key.

---

## Found, not fixed — hardening row R

Reconciling execution's counter meant counting the others. **`ledger.md` and `laws/INDEX.md` disagree
with the test-plans they summarise for 8 of 14 agents** — `portfolio_manager` reads 33 / 24 / 24,
`monitor` 24 / 19 / 19, `curator` 24 / 22 / 20, and five more. Filed as
[hardening row R](../hardening-backlog.md) rather than corrected here: **the larger number is not
automatically the right one**, since a 🟩 is only true if a passing test cites that ID. Copying the
bigger figure into the roll-up would be precisely the over-claim this chore exists to prevent. It
wants the S152-style per-row verification pass, in one sweep with row O.

Also fixed in passing: ADR-0019 and ADR-0020 were missing their Tags cell in
[`docs/decisions/INDEX.md`](../decisions/INDEX.md).

---

## Closeout

**Success factors and their proof.**

| Success factor | Proven result |
| --- | --- |
| All three conjuncts of `EXEC-FAIL-03` covered by tests citing the ID | 3 tests in `agents/execution/tests/test_graph_write_failure_retry.py`, each citing `EXEC-FAIL-03` |
| Each observed failing before being trusted | Planted-failure table above; three distinct failure modes |
| Execution ledger reconciled | 30 → **31 / 57** in `ledger.md` + `laws/INDEX.md`, matching the 🟩 count in `test-plan.md` |
| The clause summary matches `laws.md` | Row widened to all three conjuncts; rule fixed in ADR-0021 + conventions §7a |
| `make ci` green, all 9 steps | **2067 passed / 5 skipped / 100.00 % coverage**, exit 0 — ruff, format, mypy (750 files), import-linter (4 kept / 0 broken), module size, module header, pytest, pip-audit, detect-secrets |
| Remote gates green on the branch tip, by `headSha` | 4/4 on `50418c2` — table below |

**Remote gates, verified by SHA rather than by quoted run ID.** Implementation commit `50418c2`:

| Workflow | Job | Run ID | Job ID | Conclusion |
| --- | --- | --- | --- | --- |
| CI | `quality` | `30744641758` | `91488051450` | success |
| CI | `test` | `30744641758` | `91488103066` | success |
| CI | `security` | `30744641758` | `91488051471` | success |
| Security Findings | `gate` | `30744641752` | `91488051589` | success |

Both runs carry `headSha=50418c2` — a run **exists** for the SHA, which is
[hardening row M](../hardening-backlog.md)'s assertion, not merely that some run was green.

**A local-only environment gap, recorded because it will recur.** The first `make ci` in a fresh
worktree failed `tests/test_deliberator_servicebus_peer.py` with `ModuleNotFoundError: No module
named 'azure'`. Not a defect: `azure` is an optional extra, a new worktree gets its own `.venv`, and
`uv sync` does not install it. Same commit passed in the main checkout and on CI (2063 passed).
Fixed with `uv sync --extra azure`; the extra also un-skips
`test_bus_azure_receiver_integration.py`, which is why the local count is 2067 / 5 skipped where CI
reads 2066 / 6.

**Not in scope, deliberately:** hardening row R (the 8-agent counter drift), hardening row O (clauses
with no test-plan row at all), and the 13 execution clauses that still carry no row.
