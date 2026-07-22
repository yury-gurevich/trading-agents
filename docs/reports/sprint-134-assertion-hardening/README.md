# Sprint 134 Assertion Hardening Report

Sprint 134 acted on backlog row K: mutation survivors in trade-gating and
money-parsing code that were line-covered but assertion-weak after S132.

## Scope

- Branch: `sprint-134-assertion-hardening`
- Version: Round 1 bumped `0.71.05` to `0.71.06`; Round 2 stayed at
  `0.71.06` with no dependency or lockfile change
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
| S134 Round 1 rerun | 5,440 | 1,114 | 177 | 6,731 | 80.82% |
| S134 Round 2 rerun | 5,567 | 987 | 177 | 6,731 | 82.71% |

The Round 2 full rerun exited 0 with no timeout, suspicious, skipped, or
incompetent mutants. Net delta versus S132: +191 killed and -191 survived.
Net delta versus Round 1: +127 killed and -127 survived.

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
test docstrings.

### Analyst Pure-Math Bounce-Back

Round 2 removed the blanket analyst exclusion from the report and hardened
known-input/known-output assertions across the existing analyst tests. The
targeted analyst-domain survivor bucket moved from 249 at Round 2 start to 127
after the WSL rerun.

| Module | Round 2 before | Round 2 after | Delta |
| --- | ---: | ---: | ---: |
| `alpha_features` | 32 | 6 | -26 |
| `alpha_pillar` | 5 | 1 | -4 |
| `analyze` | 23 | 23 | 0 |
| `indicators` | 12 | 8 | -4 |
| `indicators_event` | 5 | 1 | -4 |
| `indicators_kernel` | 13 | 13 | 0 |
| `indicators_pattern` | 62 | 35 | -27 |
| `indicators_range` | 10 | 6 | -4 |
| `recommend` | 22 | 18 | -4 |
| `relative_strength` | 2 | 0 | -2 |
| `scoring` | 24 | 0 | -24 |
| `technical_rules` | 17 | 3 | -14 |
| `technical_rules_event` | 2 | 1 | -1 |
| `technical_rules_pattern` | 4 | 4 | 0 |
| `technical_rules_range` | 16 | 8 | -8 |
| **Targeted total** | **249** | **127** | **-122** |

This is a real drop, but not a completed row-K closeout. The remaining 127
targeted survivors are not blanket-excluded here. They are recorded as residual
Round 2 work until each is either killed or audited individually. The sampled
residuals include a mix of likely-equivalent iterator-shape changes, wording
mutants in recommendation rationale, and still-killable pure math around
pattern/range/analyze helpers; the still-killable items are why backlog row K
returns to Partial rather than Done.

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

Equivalent/default-normalization residuals in non-analyst helper code are
recorded as a permanent non-target unless the product contract changes.
Examples include `_fill_from_order` missing/odd status or side defaults that
still normalize to the same rejected/buy behavior, and ratio helpers where the
public gate outcome is unchanged. Analyst scoring, indicator, alpha, and
technical pure-math survivors are not included in this permanent exclusion.

## Files Touched

- `agents/execution/tests/test_alpaca_broker.py`
- `agents/analyst/tests/test_analyst_alpha_features.py`
- `agents/analyst/tests/test_analyst_alpha_integration.py`
- `agents/analyst/tests/test_analyst_alpha_pillar.py`
- `agents/analyst/tests/test_analyst_domain.py`
- `agents/analyst/tests/test_indicators.py`
- `agents/analyst/tests/test_indicators_event.py`
- `agents/analyst/tests/test_indicators_kernel.py`
- `agents/analyst/tests/test_indicators_pattern.py`
- `agents/analyst/tests/test_indicators_range.py`
- `agents/analyst/tests/test_relative_strength.py`
- `agents/analyst/tests/test_sentiment_reading.py`
- `agents/analyst/tests/test_technical_rules.py`
- `agents/analyst/tests/test_technical_rules_range.py`
- `agents/portfolio_manager/tests/test_portfolio_manager_edges.py`
- `agents/portfolio_manager/tests/test_reward_risk.py`
- `agents/portfolio_manager/tests/test_sector_cap.py`
- `agents/portfolio_manager/tests/test_sector_name_count.py`
- `agents/portfolio_manager/tests/test_portfolio_manager_audit.py`

No behavioral production bug was found; production source was not changed.
