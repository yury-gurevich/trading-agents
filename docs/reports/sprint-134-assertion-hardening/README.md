# Sprint 134 Assertion Hardening Report

Sprint 134 acted on backlog row K: mutation survivors in trade-gating and
money-parsing code that were line-covered but assertion-weak after S132.

## Scope

- Branch: `sprint-134-assertion-hardening`
- Version: `0.71.05` to `0.71.06`; `uv.lock` refreshed by `uv lock`
- Baseline: S132 report and `actionable-mutants.csv`
- Mutmut command:
  `UV_PROJECT_ENVIRONMENT=/home/yury/.cache/trading-agents-s134-native-venv uv run mutmut run --max-children 8`
- Test proof before mutmut: `844 passed, 4 skipped` for the S132 pytest scope
- LAW-02 scope: offline mutation and CI proof only; no infra, graph, broker,
  or teardown proof was required or run

## Overall Result

| Run | Killed | Survived | No tests | Total | Kill rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| S132 baseline | 5,376 | 1,178 | 177 | 6,731 | 79.87% |
| S134 rerun | 5,440 | 1,114 | 177 | 6,731 | 80.82% |

The S134 full rerun exited 0 with no timeout, suspicious, skipped, or
incompetent mutants. Net delta versus S132: +64 killed and -64 survived.

## Targeted Buckets

### Money Parsers

S132 listed 39 actionable pure-helper survivors in
`agents.execution.alpaca`: 18 in `_order_body`, 20 in `_fill_from_order`, and
1 in `_price_of`. S134 added exact assertions for order body construction,
parsed fill fields, malformed fill rejection, sparse-order defaults, rejected
reason handling, and price selection. After the rerun, `_order_body` and
`_price_of` had no survivors; `_fill_from_order` retained 7 survivors
(`mutmut_14`, `mutmut_16`, `mutmut_19`, `mutmut_47`, `mutmut_49`,
`mutmut_52`, `mutmut_53`) in equivalent default-normalization paths for
missing/odd status and side values.

### Decision And Gate Boundaries

S132 listed 101 actionable survivors in the analyst scoring, recommendation,
PM sizing, PM gate-report, and concentration modules. S134 hardened the
non-equivalent boundary cases with at/below/above assertions for confidence
floor, bounded/composite scoring, reward-risk ratio, nonpositive stop,
position sizing/cash/capacity, sector dollar cap, sector name count, and share
sizing. The full rerun killed the targeted boundary mutants cited in the new
test docstrings. Remaining survivors in the broad modules are context/detail,
string/render/audit, or equivalent helper-default mutants rather than trade
gate boundary changes.

## Deliberate Exclusions

The `# pragma: no cover` Alpaca HTTPS transport bucket remains deliberately
outside this sprint. Those methods cross the provider/paper-broker boundary
and are verified by live DEP-BROKER and paper-run checks, not by asserting
HTTP mock calls back to themselves. Removing the pragmas or unit-testing the
transport mock would inflate a metric while weakening the test design, so no
pragma was removed and mutmut remains manual rather than wired into `make ci`.

String, render, audit, and explanatory-detail mutants remain deliberately
outside this sprint. Killing those mutants would over-specify operator prose,
reason text, list formatting, or audit context that is intentionally allowed
to evolve. S134 instead asserts structured trade outcomes, thresholds,
boolean gate decisions, money values, and parser fields where a mutation
would alter behavior.

Equivalent/default-normalization residuals are recorded as a permanent
non-target unless the product contract changes. Examples include
`_fill_from_order` missing/odd status or side defaults that still normalize to
the same rejected/buy behavior, and ratio helpers where the public gate
outcome is unchanged.

## Files Touched

- `agents/execution/tests/test_alpaca_helpers.py`
- `agents/execution/tests/test_alpaca_broker.py`
- `agents/analyst/tests/test_analyst_domain.py`
- `agents/analyst/tests/test_relative_strength.py`
- `agents/portfolio_manager/tests/test_portfolio_manager_edges.py`
- `agents/portfolio_manager/tests/test_reward_risk.py`
- `agents/portfolio_manager/tests/test_sector_cap.py`
- `agents/portfolio_manager/tests/test_sector_name_count.py`
- `agents/portfolio_manager/tests/test_portfolio_manager_audit.py`

No behavioral production bug was found; production source was not changed.
