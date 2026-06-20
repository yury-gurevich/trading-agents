# Sprint 70 — Per-agent law backfill (4 of 11)

**Branch:** `sprint-70-per-agent-law-backfill`
**Phase:** Law cycle
**Status:** shipped

---

## Goal

Author full 18-section `laws.md` + `test-plan.md` for scanner, analyst, portfolio_manager, and
execution agents. Drive each through the full author → reconcile → citation → green cycle.
Lock all four files LOCKED v1.

---

## What shipped

### New files

| File | Description |
| --- | --- |
| `agents/scanner/laws/laws.md` | LOCKED v1 — prefix SCAN; 39 clauses, 18 green |
| `agents/scanner/laws/test-plan.md` | 18 green clauses cited to real test functions |
| `agents/analyst/laws/laws.md` | LOCKED v1 — prefix ANLZ; 43 clauses, 24 green |
| `agents/analyst/laws/test-plan.md` | 24 green clauses cited to real test functions |
| `agents/portfolio_manager/laws/laws.md` | LOCKED v1 — prefix PM; 43 clauses, 23 green |
| `agents/portfolio_manager/laws/test-plan.md` | 23 green clauses cited to real test functions |
| `agents/execution/laws/laws.md` | LOCKED v1 — prefix EXEC; 49 clauses, 30 green |
| `agents/execution/laws/test-plan.md` | 30 green clauses cited to real test functions |
| `agents/scanner/tests/test_scanner_explain.py` | Split from `test_scanner_agent.py` to stay under 200-line hard block |

### Modified files (citation pass)

12 test files received law-ID docstrings:

- `agents/scanner/tests/test_scanner_agent.py`
- `agents/scanner/tests/test_scanner_pubsub.py`
- `agents/analyst/tests/test_analyst_agent.py`
- `agents/analyst/tests/test_analyst_pubsub.py`
- `agents/portfolio_manager/tests/test_portfolio_manager_agent.py`
- `agents/portfolio_manager/tests/test_pm_pubsub.py`
- `agents/portfolio_manager/tests/test_sector_cap.py`
- `agents/portfolio_manager/tests/test_reward_risk.py`
- `agents/execution/tests/test_execution_agent.py`
- `agents/execution/tests/test_execution_pubsub.py`
- `agents/execution/tests/test_stage_gate.py`
- `agents/execution/tests/test_promote_stage.py`

### Docs updated

- `docs/laws/INDEX.md` — 4 agents: ⬜ → ✅ LOCKED v1 (S70)
- `docs/laws/ledger.md` — 4 new rows with green clause counts
- `docs/sprints/INDEX.md` — S70 complete; S71 next
- `docs/sprints/README.md` — S70 row added

---

## Green clause counts

| Agent | Prefix | Green / Total |
| --- | --- | --- |
| scanner | SCAN | 18 / 39 |
| analyst | ANLZ | 24 / 43 |
| portfolio_manager | PM | 23 / 43 |
| execution | EXEC | 30 / 49 |
| **total added** | | **95** |

---

## CI result

895 passed, 4 skipped, 100% coverage. All 9 steps green.

---

## What's next (S71)

Author laws for the remaining 7 agents: monitor, reporter, forecaster, operator, supervisor,
curator, researcher.
