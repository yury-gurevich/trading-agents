# Sprint 119 Deliberation Prompt Report

Agent: tooling
Role: record the live S119 compiled-role prompt evidence and saved model
      conversations for operator review.
External I/O: none.

## Summary

S119 compiled opt-in deliberation role prompt artifacts for all three roles:

- `scripts/deliberation_defender_prompt.json`
- `scripts/deliberation_challenger_prompt.json`
- `scripts/deliberation_judge_prompt.json`

No default prompt was flipped. Runtime still uses the hand-written constants unless
`DELIBERATION_PROMPT_ARTIFACT_DIR` is set.

No local Docker path was used; all local validation was repo commands only.

## Local Gate

`make ci`: 1421 passed, 5 skipped, 100.00% coverage. Ruff, format check,
mypy, import-linter, module hard block, headers, detect-secrets, and the test
suite passed. The known optional optimizer dependency advisory
`diskcache 5.6.3 / CVE-2025-69872` remains reported by `pip-audit` and ignored
by the Makefile.

## Live Report

Call plan before the final real report:

`6 cases x 4 prompt sets x 3 repeats = 72 debate calls (+72 scorer calls)`.

Final live champion-vs-challenger table:

| role | champion pass kw/judge | challenger pass kw/judge | champion understanding | challenger understanding | champion stability | challenger stability | firewall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| defender | 78%/83% | 78%/78% | 17% | 17% | 75% | 75% | PASS |
| challenger | 78%/83% | 61%/61% | 17% | 17% | 75% | 75% | PASS |
| judge | 78%/83% | 94%/94% | 17% | 17% | 75% | 100% | PASS |

Raw output: `live-report.txt`.

## Saved Conversations

Final n=3 live transcripts:

- `live-report-transcripts/champion.md`
- `live-report-transcripts/artifact-defender.md`
- `live-report-transcripts/artifact-challenger.md`
- `live-report-transcripts/artifact-judge.md`

Earlier one-run probe transcripts are kept under `live-probe-transcripts/`. They
show the rejected Challenger calibration before the final v4 prompt passed the
golden firewall.

## Proof Files

- `golden-firewall-proof.txt`: champion and each loaded role artifact returned
  `VERDICT: PASS`.
- `load-path-proof.txt`: env-set artifact load proof, real artifact-loaded
  deliberation (`VERDICT: REVISE`), then env-unset byte-identical default proof.

## Graph Writes

The checked path is `scripts/deliberate.py` plus kernel deliberation; it does not
construct or write a graph store. No graph rows were created and no teardown was
needed.
