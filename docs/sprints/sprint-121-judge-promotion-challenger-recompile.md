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

<!-- Coding agent: replace this comment. Required: files changed; version/deps; exact `make ci`
summary (counts + coverage); the promoted JUDGE_SYSTEM diff reference + artifact citation; golden
re-freeze before/after robust-passing sets + firewall PASS line; challenger call plan + verbatim
comparison table + the adopt-or-keep decision with numbers; live default-prompt deliberation
proof (no env opt-in); functionality-checks.md row; statement of any deviation. Do not merge. -->
