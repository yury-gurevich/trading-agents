# Sprint 121 Judge Promotion + Challenger Recompile

Agent: tooling
Role: record the live S121 prompt-promotion evidence and saved model
      conversations for operator review.
External I/O: OpenAI and Anthropic APIs; writes report/transcript files.

## Summary

S121 promoted the compiled S119 Judge artifact into the default prompt constants,
re-froze the drift-firewall golden, ran one challenger-only compile iteration, and
adopted the Challenger artifact because it beat the promoted-judge champion by the
numbers. Defender was untouched.

Promoted artifacts:

- Judge: `deliberation.judge`, `2026-07-08-s119-v4-judge-claude-opus-4-8`
- Challenger: `deliberation.challenger`, `2026-07-08-s121-v5-challenger-gpt-5.5`

## Golden Re-Freeze

Before: `['alpha158-weight-zero', 'calendar-staleness', 'lightgbm-shadow', 'pooled-sigma']`

After `uv run --extra llm python scripts/deliberation_gate.py --freeze --real --runs 3`:

```text
robust passing (5): ['alpha158-weight-zero', 'calendar-staleness', 'fixed-fraction-size', 'lightgbm-shadow', 'pooled-sigma']
fractions: {'pooled-sigma': 1.0, 'calendar-staleness': 1.0, 'name-correlation': 0.333, 'fixed-fraction-size': 1.0, 'alpha158-weight-zero': 1.0, 'lightgbm-shadow': 1.0}
```

The re-frozen baseline passed `deliberation_gate.py --check gpt-5.5 --real --runs 3`.

## Challenger Comparison

Call plan before the live comparison:

`6 cases x 4 prompt sets x 3 repeats = 72 debate calls (+72 scorer calls)`.

Final table from `live-report.txt`:

| role | champion pass kw/judge | challenger pass kw/judge | champion understanding | challenger understanding | champion stability | challenger stability | firewall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| defender | 94%/94% | 100%/100% | 17% | 17% | 100% | 100% | PASS |
| challenger | 94%/94% | 100%/100% | 17% | 17% | 100% | 100% | PASS |
| judge | 94%/94% | 100%/94% | 17% | 22% | 100% | 100% | PASS |

Decision: adopt the Challenger artifact. It beat the champion on pass-rate
(`100%/100%` vs `94%/94%`), matched stability (`100%` vs `100%`), and passed the
firewall. Defender remained the hand-written champion.

## Live Default Check

`live-default-deliberation.txt` proves no artifact env opt-in was set:

```text
ENV_OPT_IN_SET: False
VERDICT: REVISE - the Alpha158 weight is 0.00, so although enabled it contributes nothing to the score - trusting its contribution relies on a disabled signal
```

Final-default firewall check after adopting Challenger:

```text
regressed: none
gained:    ['name-correlation']
VERDICT: PASS
```

## Files

- `golden-refreeze.txt`
- `golden-firewall-check.txt`
- `challenger-compile.txt`
- `live-report.txt`
- `live-report-transcripts/`
- `final-default-firewall-check.txt`
- `live-default-deliberation.txt`

## Graph Writes

The exercised paths are `scripts/deliberation_gate.py`,
`scripts/compare_deliberation_prompts.py`, and `scripts/deliberate.py`; they do
not construct a graph store. No graph rows were created and no teardown was
needed.

## Local Gate

`make ci`: `1439 passed, 5 skipped`, `100.00%` coverage
(`9946` stmts, `0` miss, `2016` branches, `0` partial). Ruff, format
check, mypy, import-linter, module hard block, headers, detect-secrets, and
the test suite passed. The known optional optimizer dependency advisory
`diskcache 5.6.3 / CVE-2025-69872` remains reported by `pip-audit` and ignored
by the Makefile.
