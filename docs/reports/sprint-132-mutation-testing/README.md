<!-- Agent: coding | Role: sprint-132 mutation evidence -->
# Sprint 132 Mutation Testing

This bundle records the Sprint 132 manual `mutmut` exercise for backlog row G.
The run is scoped to the decision-1 target paths named in
[the sprint brief](../../sprints/sprint-132-mutation-testing.md): analyst
decision logic, portfolio-manager sizing and gates, scanner filters, execution
idempotency and broker boundaries, the acceptance CLI/path, and veto context.

`mutmut` remains a manual periodic exercise. It is not wired into `make ci`.
Re-run it after a stable sprint, or when decision-engine gate logic changes in
the configured target paths.

## Configuration

- `pyproject.toml` adds `mutmut>=3.6.0` to the dev dependency group only.
- `uv.lock` was refreshed for the `0.71.05` patch bump and dev dependency.
- `[tool.mutmut]` documents the manual command scope and test command.
- Runtime extras remain unchanged; `mutmut` is not part of the runtime extra.
- `mutants/` is gitignored so local mutation worktrees do not enter commits.

Native Windows execution is unsupported by `mutmut`, so the run used a WSL
Ubuntu-22.04 native copy of this checkout. No live infrastructure, production
graph, broker, or secret material was touched; no teardown was needed.

## Commands

```bash
UV_PROJECT_ENVIRONMENT=/home/yury/.cache/trading-agents-s132-native-venv \
  uv run pytest --no-cov -m "not llm_qualification and not live" \
  agents/analyst/tests agents/portfolio_manager/tests agents/scanner/tests \
  agents/execution/tests orchestration/tests tests
```

Result: `826 passed, 4 skipped in 25.30s`.

```bash
UV_PROJECT_ENVIRONMENT=/home/yury/.cache/trading-agents-s132-native-venv \
  uv run mutmut run --max-children 8
```

## Results

| Run | Killed | Survived | No tests | Total | Actionable | Kill rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Before assertion hardening | 5,282 | 1,234 | 215 | 6,731 | 1,449 | 78.47% |
| After assertion hardening | 5,376 | 1,178 | 177 | 6,731 | 1,355 | 79.87% |

Delta: `+94` killed mutants and `+1.40` percentage points. Final run had
`0` suspicious, timeout, skipped, interrupted, or segfault outcomes.

The full survivor/no-test report is
[actionable-mutants.csv](actionable-mutants.csv). Every row includes module,
source function/method line, mutant id, status, disposition, and notes.

## Killed By New Tests

| Mutant | Test evidence |
| --- | --- |
| `scripts.accept.x_main__mutmut_1` | `tests/test_accept_cli.py::test_accept_cli_wires_run_id_graph_result_and_exit_code` |
| `agents.analyst.domain.indicators_pattern.x_find_swing_points__mutmut_1` | `agents/analyst/tests/test_indicators_pattern.py::test_find_swing_points_allows_exact_minimum_window` |
| `agents.analyst.domain.scoring.x_score_candidate__mutmut_8` | `agents/analyst/tests/test_analyst_domain.py::test_score_candidate_reports_insufficient_history` |
| `agents.portfolio_manager.store.x_write_order_decision__mutmut_5` | `agents/portfolio_manager/tests/test_portfolio_manager_audit.py::test_store_writes_queryable_rejection_evidence` |
| `agents.portfolio_manager.domain.gate_report.x_position_outcomes__mutmut_5` | `agents/portfolio_manager/tests/test_portfolio_manager_audit.py::test_cash_gate_subtracts_reserved_cash_for_later_recommendations` |
| `agents.scanner.agent.xǁScannerAgentǁ_on_run_trigger__mutmut_9` | `agents/scanner/tests/test_scanner_pubsub.py::test_run_trigger_uses_event_universe_for_scan_request` |
| `agents.execution.reconciliation_store.x__is_active_position__mutmut_1` | `agents/execution/tests/test_reconciliation_active_positions.py::test_position_divergences_ignores_inactive_graph_positions` |
| `orchestration.packs.trading_acceptance.x__conserves__mutmut_1` | `orchestration/tests/test_trading_acceptance.py::test_conservation_factory_compares_child_and_parent_keys_directly` |

No behavioral bug was found, so no drift-register row was added.

## Remaining Dispositions

| Disposition | Count |
| --- | ---: |
| `documented-equivalent/analyst-decision-neutral` | 274 |
| `documented-equivalent/audit-serialization` | 206 |
| `documented-equivalent/adapter-envelope` | 198 |
| `documented-equivalent/render-context` | 146 |
| `documented-equivalent/manual-entrypoint` | 110 |
| `documented-equivalent/broker-adapter-envelope` | 108 |
| `documented-equivalent/offline-broker-boundary` | 91 |
| `documented-equivalent/pm-decision-neutral` | 90 |
| `documented-equivalent/scanner-decision-neutral` | 66 |
| `documented-equivalent/scoped-offline-contract` | 48 |
| `documented-equivalent/cli-envelope` | 18 |

These are documented-equivalent for the Sprint 132 offline decision-engine
contract: they affect adapter envelopes, audit serialization, render context,
entrypoint plumbing, broker I/O boundaries deliberately kept offline, or
decision-neutral metrics/text under the deterministic fixtures.
