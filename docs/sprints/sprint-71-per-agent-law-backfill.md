# Sprint 71 — Per-agent law backfill (remaining 7 agents)

**Branch:** `sprint-71-per-agent-law-backfill`
**Phase:** Law cycle
**Status:** shipped

## Goal

Author full 18-section law files for the remaining 7 agents that were not covered in S70
(monitor, reporter, forecaster, operator, supervisor, curator, researcher). Run the full
first-principles cycle: author → reconcile → citation pass → test-plan → LOCKED v1.

## What shipped

### Law files authored (all LOCKED v1)

| Agent | Prefix | Clauses | Green after S71 |
| --- | --- | --- | --- |
| monitor | MON | 40 | 19 |
| reporter | RPT | 40 | 17 |
| forecaster | FORE | 46 | 15 |
| operator | OPR | 51 | 14 |
| supervisor | SUP | 49 | 21 |
| curator | CUR | 48 | 20 |
| researcher | RES | 44 | 18 |

Total green clauses added: **124**

### Files changed

**New law files (7):**

- `agents/monitor/laws/laws.md` — LOCKED v1 (40 clauses, prefix MON)
- `agents/reporter/laws/laws.md` — LOCKED v1 (40 clauses, prefix RPT)
- `agents/forecaster/laws/laws.md` — LOCKED v1 (46 clauses, prefix FORE)
- `agents/operator/laws/laws.md` — LOCKED v1 (51 clauses, prefix OPR)
- `agents/supervisor/laws/laws.md` — LOCKED v1 (49 clauses, prefix SUP)
- `agents/curator/laws/laws.md` — LOCKED v1 (48 clauses, prefix CUR)
- `agents/researcher/laws/laws.md` — LOCKED v1 (44 clauses, prefix RES)

**New test-plan files (7):**

- `agents/monitor/laws/test-plan.md`
- `agents/reporter/laws/test-plan.md`
- `agents/forecaster/laws/test-plan.md`
- `agents/operator/laws/test-plan.md`
- `agents/supervisor/laws/test-plan.md`
- `agents/curator/laws/test-plan.md`
- `agents/researcher/laws/test-plan.md`

**Test files with citation docstrings added:**

- `agents/monitor/tests/test_monitor_agent.py`
- `agents/monitor/tests/test_monitor_pubsub.py`
- `agents/monitor/tests/test_monitor_exits.py`
- `agents/reporter/tests/test_reporter_agent.py`
- `agents/reporter/tests/test_reporter_pubsub.py`
- `agents/reporter/tests/test_reporter_boundary.py`
- `agents/forecaster/tests/test_forecaster_agent.py`
- `agents/forecaster/tests/test_forecaster_boundary.py`
- `agents/operator/tests/test_operator_agent.py`
- `agents/supervisor/tests/test_supervisor_gate.py`
- `agents/supervisor/tests/test_supervisor_health_flags.py`
- `agents/curator/tests/test_build_dataset.py`
- `agents/curator/tests/test_train_predictor.py`
- `agents/curator/tests/test_promote_predictor.py`
- `agents/curator/tests/test_p10_boundary.py`
- `agents/researcher/tests/test_propose.py`
- `agents/researcher/tests/test_p7_boundary.py`
- `agents/researcher/tests/test_proposal.py`

**Docs updated:**

- `docs/laws/INDEX.md` — 7 agents updated to LOCKED v1 (S71)
- `docs/laws/ledger.md` — 7 new rows with green clause counts
- `docs/sprints/INDEX.md` — S71 complete; next number S72
- `docs/sprints/README.md` — S71 row added
- `docs/STATE.md` — Last updated with Melbourne timestamp

## CI result

`make ci` passed locally (9/9 steps). GitHub CI confirmed green after push.

## Notes

- All 7 law files were authored from first principles using code reading + contract
  inspection, never copying from another agent's `laws.md`.
- Citation pass resolved all E501 violations introduced by docstrings.
- Researcher `laws.md` uses `confidence_floor_reference` as a plain float tunable
  to avoid cross-agent import (RES-NEV-04).
- The out-of-band curator law (CUR-NEV-01) is the key invariant separating ML training
  from live trading decisions.
