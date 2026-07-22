# Sprint 134 Assertion Hardening Report

Sprint 134 acted on backlog row K: mutation survivors in trade-gating and
money-parsing code that were line-covered but assertion-weak after S132.

## Scope

- Branch: `sprint-134-assertion-hardening`
- Version: Round 1 bumped `0.71.05` to `0.71.06`; Rounds 2 and 3 stayed at
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
| S134 Round 3 rerun | 5,678 | 876 | 177 | 6,731 | 84.36% |

The Round 3 full rerun exited 0 with no suspicious, skipped, or incompetent
mutants. Net delta versus S132: +298 killed and -298 survived. Net delta
versus Round 2: +107 killed and -107 survived.

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

Round 3 closed the bounce-back by forcing every one of the 127 residual analyst
survivors into an auditable per-mutant disposition. The result is 107 killed,
12 individually justified equivalent survivors, and 8 recommendation-rationale
wording exclusions. There are 0 untriaged targeted analyst survivors. The
anti-hand-wave artifact is
[`round-3-dispositions.csv`](round-3-dispositions.csv).

| Module | Round 3 before | Killed | Equivalent | Wording exclusion | Round 3 after | Untriaged |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `alpha_features` | 6 | 4 | 2 | 0 | 2 | 0 |
| `alpha_pillar` | 1 | 1 | 0 | 0 | 0 | 0 |
| `analyze` | 23 | 21 | 2 | 0 | 2 | 0 |
| `indicators` | 8 | 5 | 3 | 0 | 3 | 0 |
| `indicators_event` | 1 | 1 | 0 | 0 | 0 | 0 |
| `indicators_kernel` | 13 | 8 | 5 | 0 | 5 | 0 |
| `indicators_pattern` | 35 | 35 | 0 | 0 | 0 | 0 |
| `indicators_range` | 6 | 6 | 0 | 0 | 0 | 0 |
| `recommend` | 18 | 10 | 0 | 8 | 8 | 0 |
| `technical_rules` | 3 | 3 | 0 | 0 | 0 | 0 |
| `technical_rules_event` | 1 | 1 | 0 | 0 | 0 | 0 |
| `technical_rules_pattern` | 4 | 4 | 0 | 0 | 0 | 0 |
| `technical_rules_range` | 8 | 8 | 0 | 0 | 0 | 0 |
| **Targeted total** | **127** | **107** | **12** | **8** | **20** | **0** |

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
would alter behavior. Round 3 moved only the eight `recommend.x_decide`
rationale mutants that change named prose strings into this bucket; the exact
strings are recorded per mutant in `round-3-dispositions.csv`.

Equivalent/default-normalization residuals in non-analyst helper code are
recorded as a permanent non-target unless the product contract changes.
Examples include `_fill_from_order` missing/odd status or side defaults that
still normalize to the same rejected/buy behavior, and ratio helpers where the
public gate outcome is unchanged. The remaining targeted analyst residuals are
not blanket-excluded: each has an individual iterator-shape, dead-initializer,
defensive-guard, or wording reason in `round-3-dispositions.csv`.

## Files Touched

- `agents/execution/tests/test_alpaca_broker.py`
- `agents/analyst/tests/test_analyst_alpha_features.py`
- `agents/analyst/tests/test_analyst_alpha_feature_edges.py`
- `agents/analyst/tests/test_analyst_alpha_integration.py`
- `agents/analyst/tests/test_analyst_alpha_pillar.py`
- `agents/analyst/tests/test_analyst_domain.py`
- `agents/analyst/tests/test_analyze_domain.py`
- `agents/analyst/tests/test_indicators.py`
- `agents/analyst/tests/test_indicators_event.py`
- `agents/analyst/tests/test_indicators_kernel.py`
- `agents/analyst/tests/test_indicators_pattern.py`
- `agents/analyst/tests/test_indicators_pattern_edges.py`
- `agents/analyst/tests/test_indicators_pattern_triangles.py`
- `agents/analyst/tests/test_indicators_range.py`
- `agents/analyst/tests/test_recommend_domain.py`
- `agents/analyst/tests/test_relative_strength.py`
- `agents/analyst/tests/test_sentiment_reading.py`
- `agents/analyst/tests/test_technical_rules.py`
- `agents/analyst/tests/test_technical_rules_event.py`
- `agents/analyst/tests/test_technical_rules_pattern.py`
- `agents/analyst/tests/test_technical_rules_range.py`
- `agents/portfolio_manager/tests/test_portfolio_manager_edges.py`
- `agents/portfolio_manager/tests/test_reward_risk.py`
- `agents/portfolio_manager/tests/test_sector_cap.py`
- `agents/portfolio_manager/tests/test_sector_name_count.py`
- `agents/portfolio_manager/tests/test_portfolio_manager_audit.py`
- `docs/reports/sprint-134-assertion-hardening/README.md`
- `docs/reports/sprint-134-assertion-hardening/round-3-dispositions.csv`

No behavioral production bug was found; production source was not changed.
