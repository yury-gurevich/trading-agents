<!-- Agent: planning | Role: sprint handover -->
# Sprint 121 — Promote the compiled judge; recompile the challenger (S119 resolution)

**Phase:** Deliberation quality (DL-42 follow-through — first prompt **promotion** on the
ADR-0010 champion-challenger rails)
**Branch:** `sprint-121-judge-promotion-challenger-recompile`
**Status:** ready for handover (packaged 2026-07-08; execute after S120 merges)
**Effort:** S/M

---

## Why this sprint (the S119 result, and the operator's direction)

S119's live report split three ways: the compiled **judge** clearly beat the champion (pass
94%/94% vs 78%/83%; verdict stability 100% vs 75%; firewall PASS with a *gained* case), the
**defender** was flat, and the compiled **challenger** *regressed* (61% vs 78%/83%). Promotion was
deliberately operator-held (S119 decision 4). The operator directed resolution 2026-07-08:
*"this will have to be resolved sooner rather than later."* **Pasting this kickoff is the
operator's promotion approval for the judge.** The challenger regression is resolved by iterating
the compile — or by honestly keeping the hand-written champion if the new artifact still loses.

## Decisions taken at packaging (LAW-06)

1. **Judge promotion mechanism: the compiled prompt becomes the champion constant.** Replace
   `JUDGE_SYSTEM`'s text in `kernel/deliberation.py` with the compiled judge prompt (cite the
   artifact version `2026-07-08-s119-v4` and task `deliberation.judge@claude-opus-4-8` in the
   module docstring/comment). This reaches every composition (live veto path included) with zero
   env dependency; the byte-identical default test keeps its meaning (defaults = constants).
   *Ruled out:* env-default flip in `scripts/deliberate.py` only (misses the live veto path);
   loading the artifact file at kernel import (kernel stays I/O-free).
2. **Golden re-freeze is mandatory with the promotion** — the S119 note said exactly this
   (re-freeze only when a prompt is promoted; that now happens). New baseline with the promoted
   judge, robust-passing set recorded; the drift firewall guards the *new* champion from here on.
3. **Challenger: recompile and gate; keeping the champion is a valid outcome.** One bounded
   iteration (the S119 probe transcripts show the earlier calibration failure mode). Adopt only
   if the new artifact beats the champion on pass-rate + stability with firewall PASS; otherwise
   keep the hand-written champion, keep the losing artifact committed as the record, and say so
   plainly (LAW-02). Defender stays champion either way (flat result; no churn without a win).

## Codex kickoff (paste this)

> Execute **Sprint 121 — judge promotion + challenger recompile** exactly as specified in this
> file (`docs/sprints/sprint-121-judge-promotion-challenger-recompile.md`). Read first: the S119
> closeout + `docs/reports/sprint-119-deliberation-roles/` (the numbers being acted on),
> `kernel/deliberation.py` + `kernel/deliberation_prompt_artifacts.py`,
> `scripts/compile_deliberation_prompts.py` + `compare_deliberation_prompts.py` +
> `deliberation_gate.py` (all shipped in S119 — this sprint mostly *uses* them).
>
> - **Start:** from `main` (`git pull` — S120 must already be merged),
>   `git checkout -b sprint-121-judge-promotion-challenger-recompile` (delete any stale local
>   branch first). **Hard gate:** `make ci` green, 100 % coverage, ≤200-line modules, headers.
>   Bump `pyproject.toml` **PATCH** from whatever `main` holds (prompt tuning/promotion — no new
>   capability) + `uv lock`.
> - **Part A — promote the judge (deterministic):**
>   1. Replace the `JUDGE_SYSTEM` text with the compiled judge prompt from
>      `scripts/deliberation_judge_prompt.json` (verbatim), citing artifact version + task in
>      code. The old text remains recoverable via git + the artifact history.
>   2. Update any test pinning the old judge text; the byte-identical defaults test stays.
>   3. **Re-freeze the golden** with the promoted judge (real Opus judge, n=3, same procedure as
>      the S109 re-freeze); record the robust-passing set before/after. `deliberation_gate.py
>      --check` must PASS on the new baseline.
> - **Part B — recompile the challenger (live, bounded):**
>   1. One compile iteration for the challenger role only (same pipeline, S109 models, budgets
>      unchanged — debaters 8000 / judge 2000). State the call plan before running; stay within
>      ~100 debate calls total including the comparison.
>   2. Run the champion-vs-challenger comparison **against the promoted-judge baseline**; include
>      the per-role table verbatim in the closeout.
>   3. **Adopt or keep, by the numbers:** if the new challenger artifact beats the champion
>      (pass-rate and stability, firewall PASS) → replace `CHALLENGER_SYSTEM` the same way as the
>      judge and note it; if not → keep the hand-written champion, commit the losing artifact +
>      report as the record, and state the negative result plainly. Defender is untouched.
> - **Live check (sprint-close rule):** one real deliberation on the default (promoted) prompts —
>   record the verdict + that no env opt-in was needed; firewall PASS line on the new baseline;
>   no graph writes expected (state if any; tear down to 0). Record in
>   `docs/laws/functionality-checks.md`. Update the S119 report dir (or a sibling `sprint-121-*`
>   dir) with the new transcripts/report.
> - **Out of scope — flag, don't build:** defender changes; new eval cases; EvoPrompt/TextGrad
>   (R003); DL-39/DL-40; any veto-path logic change beyond the prompt text; scheduling/broker
>   anything (that is S120).
> - **Do NOT merge or push to `main`** — commit on the branch only; fill **Closeout evidence**
>   here.

---

## Notes for the coding agent

- The S119 probe transcripts (`live-probe-transcripts/`) document the challenger calibration
  failure that preceded v4 — read them before the recompile so v5 doesn't repeat it.
- After the judge promotion the S119 report's champion numbers are historical — do not edit that
  report; new numbers live in the new report dir.
- API keys from `.env` (funded); explicit-path `load_dotenv`; never echo keys. Windows: keep the
  UTF-8 stdout reconfigure pattern in any new script output.

---

## Closeout evidence

Completed on branch `sprint-121-judge-promotion-challenger-recompile`; not merged and not pushed to
`main`.

Files changed:

- Prompt promotion / split: `kernel/deliberation.py`, `kernel/deliberation_prompts.py`.
- Artifact loader pins/tests: `tests/test_deliberation_prompt_artifacts.py`.
- Challenger role-only compile support: `scripts/compile_deliberation_prompts.py`,
  `tests/test_deliberation_prompt_pipeline.py`.
- Live artifacts/evidence: `scripts/deliberation_challenger_prompt.json`,
  `scripts/deliberation_golden.json`,
  `docs/reports/sprint-121-judge-promotion-challenger-recompile/`.
- Functionality and sprint indices: `docs/laws/functionality-checks.md`,
  `docs/sprints/README.md`, `docs/sprints/INDEX.md`, `docs/STATE.md`.
- Version/deps: `pyproject.toml` `0.65.00 -> 0.65.01`; `uv.lock` refreshed.

Local gate:

- Focused pre-live slice after promotions:
  `uv run pytest tests/test_deliberation.py tests/test_deliberation_prompt_artifacts.py tests/test_deliberation_prompt_pipeline.py --no-cov`
  passed: `28 passed`.
- Focused Ruff and module/header checks passed; `kernel/deliberation_prompts.py` is `199` lines
  after the split/promotions.
- Final `make ci`: `1439 passed, 5 skipped`, `100.00%` coverage (`9946` stmts, `0`
  miss, `2016` branches, `0` partial). Ruff, format check, mypy, import-linter,
  module hard block, headers, detect-secrets, and the test suite passed. The known optional
  optimizer dependency advisory `diskcache 5.6.3 / CVE-2025-69872` remains reported by
  `pip-audit` and ignored by the Makefile.

Promoted defaults:

- `JUDGE_SYSTEM` now comes from `scripts/deliberation_judge_prompt.json`, task
  `deliberation.judge`, version `2026-07-08-s119-v4-judge-claude-opus-4-8`.
- `CHALLENGER_SYSTEM` now comes from `scripts/deliberation_challenger_prompt.json`, task
  `deliberation.challenger`, version `2026-07-08-s121-v5-challenger-gpt-5.5`.
- `DEFENDER_SYSTEM` is untouched.
- Tests pin both promoted constants byte-for-byte to their committed artifacts; the default prompt
  byte-identical-to-constants test remains.

Golden re-freeze:

- Before robust-passing set from the pre-S121 golden:
  `['alpha158-weight-zero', 'calendar-staleness', 'lightgbm-shadow', 'pooled-sigma']`.
- Re-freeze command:
  `uv run --extra llm python scripts/deliberation_gate.py --freeze --real --runs 3`.
- After robust-passing set:
  `['alpha158-weight-zero', 'calendar-staleness', 'fixed-fraction-size', 'lightgbm-shadow', 'pooled-sigma']`.
- Re-frozen fractions:
  `{'pooled-sigma': 1.0, 'calendar-staleness': 1.0, 'name-correlation': 0.333, 'fixed-fraction-size': 1.0, 'alpha158-weight-zero': 1.0, 'lightgbm-shadow': 1.0}`.
- Firewall check on the re-frozen baseline:
  `regressed: none`, `gained: none`, `VERDICT: PASS`.

Challenger call plan and result:

- Role-only compile command:
  `uv run --extra optimizer python scripts/compile_deliberation_prompts.py --role challenger --debate-model gpt-5.5 --judge-model claude-opus-4-8 --version 2026-07-08-s121-v5 --output-dir scripts`.
- The compiler path made no debate/model calls; the live comparison plan was
  `6 cases x 4 prompt sets x 3 repeats = 72 debate calls (+72 scorer calls)`, with
  `--max-debate-calls 100`. Debater/Judge budgets stayed at `8000/2000`.
- Final promoted-judge comparison table, verbatim from
  `docs/reports/sprint-121-judge-promotion-challenger-recompile/live-report.txt`:

| role | champion pass kw/judge | challenger pass kw/judge | champion understanding | challenger understanding | champion stability | challenger stability | firewall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| defender | 94%/94% | 100%/100% | 17% | 17% | 100% | 100% | PASS |
| challenger | 94%/94% | 100%/100% | 17% | 17% | 100% | 100% | PASS |
| judge | 94%/94% | 100%/94% | 17% | 22% | 100% | 100% | PASS |

Decision: adopt Challenger. The new Challenger artifact beat the champion on pass-rate
(`100%/100%` vs `94%/94%`), matched stability (`100%` vs `100%`), and passed the firewall. Defender
remained untouched.

Live default-prompt proof:

- Env opt-in was explicitly absent: `ENV_OPT_IN_SET: False`.
- Command:
  `uv run --extra llm python scripts/deliberate.py --real --rounds 1 --decision "Alpha158 is enabled, so trust its contribution to the score." --context "... WEIGHT = 0.00 ..."`
- Verdict:
  `VERDICT: REVISE — the Alpha158 weight is 0.00, so although enabled it contributes nothing to the score — trusting its contribution relies on a disabled signal`.
- Final-default firewall check after adopting Challenger:
  `regressed: none`, `gained: ['name-correlation']`, `VERDICT: PASS`.

Functionality-check register:

- Added the S121 row to `docs/laws/functionality-checks.md` with the re-freeze, comparison,
  final-default live verdict, final-default firewall PASS, and no-graph-write statement.

Graph/write hygiene:

- `scripts/deliberation_gate.py`, `scripts/compare_deliberation_prompts.py`, and
  `scripts/deliberate.py` do not construct a graph store. No graph rows were created and no
  teardown was needed.

Spec deviations / out of scope:

- No defender changes.
- No new eval cases.
- No EvoPrompt/TextGrad (R003), DL-39, DL-40, veto-path logic changes beyond prompt text, or
  scheduling/broker work.
