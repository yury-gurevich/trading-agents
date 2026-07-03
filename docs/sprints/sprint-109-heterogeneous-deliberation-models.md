# Sprint 109 — heterogeneous deliberation: GPT-5.5 debaters, Opus judge (ADR-0010)

**Phase:** LLM interaction quality (ADR-0010 / DL-24)
**Branch:** `sprint-109-heterogeneous-deliberation-models`
**Status:** shipped (0.51.00 → 0.52.00; **live-Opus closeout deferred** — see Closeout evidence)
**Effort:** M

---

## Codex kickoff (paste this)

> Execute **Sprint 109 — heterogeneous deliberation models** exactly as specified in this file
> (`docs/sprints/sprint-109-heterogeneous-deliberation-models.md`). It is a complete, self-contained
> handover.
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-109-heterogeneous-deliberation-models`.
>   Read the files under *Execution notes* first.
> - **The one trap — two different "judges":** the **debate Judge** (inside `deliberate()`,
>   `JUDGE_SYSTEM`, rules uphold/overturn/revise — *this is the "deciding party" that moves to Opus*)
>   is NOT the **scorer Judge** (`LLMJudgeScorer`, EXP-004, grades "did the Challenger catch the flaw?").
>   This sprint changes ONLY the debate Judge. **Do not touch `LLMJudgeScorer`'s model** — EXP-005 holds
>   the scorer fixed at champion.
> - **Hard gate every commit:** `make ci` green — 9 steps, **100 % coverage**, modules **≤ 200 lines**,
>   coding-agent `Agent:`/`Role:` headers. Bump `pyproject.toml` 0.51.00 → 0.52.00 + `uv lock`.
> - **Governance step (required, not optional):** changing the debate Judge model is an ADR-0010 §5
>   trigger — **re-freeze** the drift-firewall golden (`scripts/deliberation_golden.json`) with the new
>   split config, and update ADR-0010 to record Opus as the champion debate judge.
> - **Live check** with **real models** (`uv run --extra llm python …`): prove the Defender/Challenger
>   ran on GPT-5.5 and the Verdict came from Opus, and that the re-frozen gate still trips on a weaker
>   debater. Record the row in `docs/laws/functionality-checks.md`.
> - **Do NOT merge or push to `main`** — commit on the branch only, and stop for operator confirmation.
> - Read the *Session gotchas*. When done, append a **Closeout evidence** block (like S99/S108's) and set
>   **Status** to shipped.

---

## Goal

The deliberation is a debate: a **Defender** (proponent) and a **Challenger** (opponent) argue, and a
**Judge** (the deciding third party) rules. Today `deliberate()` runs **all three roles through one
model** (currently GPT-5.5 via `LLM_PROVIDER=openai`). The operator wants the **arguing parties on
GPT-5.5** and the **deciding Judge on Opus** (`claude-opus-4-8`) — strong, aggressive advocacy adjudicated
by the strongest-reasoning model. This sprint makes the debate model **per-role**, configures the Opus
judge behind **dedicated env vars** (so the operator agent's `ANTHROPIC_MODEL` is untouched), threads it
through the production challenger-veto, and **re-freezes the drift-firewall** so the gate reflects the new
champion.

## Decisions (resolved with the operator, 2026-07-03 — do not reopen)

- **Split:** Defender + Challenger → GPT-5.5 (existing `OPENAI_MODEL`); debate Judge → Opus.
- **Config:** **dedicated** `DELIBERATION_JUDGE_PROVIDER` / `DELIBERATION_JUDGE_MODEL` (default
  `anthropic` / `claude-opus-4-8`). Do **not** repurpose `ANTHROPIC_MODEL` (it drives the operator agent).
- **Delivery:** Codex, from this handover.

## Scope

### In

- **`kernel/deliberation.py` — per-role judge.** `deliberate(llm, proposition, *, max_rounds=3,
  judge_llm=None)`: the Defender/Challenger rounds use `llm`; the final Judge call uses `judge_llm or
  llm`. Backward-compatible (one-arg callers keep single-model behaviour). `JUDGE_SYSTEM` /
  `DEFENDER_SYSTEM` / `CHALLENGER_SYSTEM` prompt text is **unchanged**.
- **Two-model builder (`scripts/deliberate.py`).** Add `build_role_llms(real) -> tuple[LLMClient,
  LLMClient]` returning `(argue_llm, judge_llm)`: `argue_llm` = the existing `_build_llm` path (OpenAI
  GPT-5.5); `judge_llm` from the new env (`DELIBERATION_JUDGE_PROVIDER`/`_MODEL`), built with the existing
  `_OpenAIText` / `_AnthropicText` adapters + the matching key. The demo `main()` calls
  `deliberate(argue_llm, prop, judge_llm=judge_llm)` and its MODE line prints **both** models
  (e.g. `MODE: real (debate OpenAI gpt-5.5 · judge Anthropic claude-opus-4-8)`).
- **Production wiring.** Thread the judge through the veto path so the tool and production agree:
  `orchestration/veto.py::deliberate_pm_node(..., judge_llm=None)` → `deliberate(llm, prop,
  judge_llm=judge_llm)`; `orchestration/local_pipeline.cascade_once(..., deliberation_judge_llm=None)`
  passes it; `scripts/run_local.py --veto` builds both via `build_role_llms(True)` and passes both.
- **Eval consistency (`scripts/deliberation_eval.py`).** The eval debates use the split models too
  (`build_role_llms` → `deliberate(argue, judge_llm=judge)`), so the harness measures the real
  configuration. **The `LLMJudgeScorer` scorer stays exactly as-is** (champion, EXP-004).
- **Re-freeze the drift-firewall (`scripts/deliberation_gate.py`).** The `--freeze` path must generate the
  golden with the split debate (GPT-5.5 debaters + Opus judge inside `deliberate`), while the **scorer
  judge stays champion** and `--check MODEL` still varies only the **debater**. Regenerate
  `scripts/deliberation_golden.json` via `--freeze --real` and commit it. **Add a docstring note naming
  the two judges** so the next reader doesn't conflate them.
- **Config + capture.** Add `DELIBERATION_JUDGE_PROVIDER` / `DELIBERATION_JUDGE_MODEL` to `.env` and
  `.env.example` (if present). Update **ADR-0010** (champion debate judge = Opus; heterogeneous
  debater/judge is intentional; re-freeze recorded per §5) + a `design-log.md` line.

### Out

- **`LLMJudgeScorer`'s model** (EXP-004 semantic scorer) — unchanged; conflating it with the debate Judge
  is the failure mode this sprint guards against.
- Any change to prompt **content**, ruling semantics, or the veto's subtract-only rule (DL-31).
- DSPy-compiling these prompts (ADR-0010 harness generalization — a later, separate sprint).
- Changing the operator agent's model.

## Deliverables

- `deliberate(..., judge_llm=None)` + unit tests: judge uses `judge_llm` when given (assert via two
  distinct `FakeLLMClient`s — one for debate, one returning a fixed verdict), falls back to `llm`
  otherwise; existing single-model tests still pass.
- `build_role_llms` + tests (env-driven provider/model selection; default anthropic/opus; missing-key
  error path).
- Veto + `cascade_once` + `run_local.py` threaded; tests for the new param.
- Re-frozen `scripts/deliberation_golden.json` (committed) + gate docstring naming the two judges.
- `.env`/`.env.example` entries + ADR-0010 + design-log update.
- `make ci` green, 100 % coverage, modules ≤ 200 lines; 0.51.00 → 0.52.00 + `uv lock`.

## Functionality check (sprint-close rule)

With **real models** (`uv run --extra llm python …`; `.env` has both keys):

1. **Split proven:** run `scripts/deliberate.py --real` on a sample decision → the MODE line names
   **debate = OpenAI GPT-5.5** and **judge = Anthropic claude-opus-4-8**; capture the transcript +
   Verdict as evidence that the arguing turns and the ruling came from different providers. `--score`
   still prints.
2. **Firewall intact:** `scripts/deliberation_gate.py --freeze --real` regenerates the golden with the
   split config; then `--check <a weaker/other debater model> --real` still **trips** on at least one
   golden case (the drift-firewall works against the new baseline).
3. *(Optional, if cheap)* `scripts/run_local.py --real --veto` against Aura `bce05bd6` → the persisted
   `DeliberationRun` reflects the split models; **tear down** the run's nodes → prior count.

Record the row in `docs/laws/functionality-checks.md` (models used, the sample verdict, the gate-trip
evidence, teardown if the optional live veto ran).

## Dependencies

- **ADR-0010** (eval-gated prompts; models are a gated parameter) — this is a governed model change; update
  its record. **EXP-004/EXP-005** (the scorer + the gate) — reuse; do not alter the scorer.
- Reuses `kernel/deliberation.py`, `scripts/{deliberate,deliberation_gate,deliberation_eval}.py`,
  `orchestration/{veto,local_pipeline}.py`. Anthropic + OpenAI keys already in `.env`; `llm` extra
  installs both SDKs.

## Version bump

New capability (heterogeneous per-role deliberation models). **0.51.00 → 0.52.00** (feat → MINOR).

## Execution notes (for the coding agent — cold-start handover)

**Start.** From `main` (`git pull`; HEAD ≥ `c12ea93`):
`git checkout -b sprint-109-heterogeneous-deliberation-models`. Read `kernel/deliberation.py` (the
`deliberate` loop + the three SYSTEM prompts), `scripts/deliberate.py` (`_build_llm`, `_OpenAIText`,
`_AnthropicText`), `scripts/deliberation_gate.py` (`--freeze`/`--check`, `_GOLDEN`, and note its `_score`
already separates a debater from the **scorer** judge — different from this sprint's debate judge),
`scripts/deliberation_eval.py`, `orchestration/veto.py`, `orchestration/local_pipeline.py`, `ADR-0010`.

**Gate.** `make ci` green — 9 steps, **100 % coverage**, modules ≤ 200 lines, coding-agent headers.

**Boundaries.** `kernel/deliberation.py` stays dependency-free (LLM via the injected `LLMClient` port —
no provider SDK in kernel). The provider adapters live in `scripts/` (tooling); `orchestration` receives
built clients as params, never imports `scripts`. No new graph labels.

**Commit.** Branch-per-sprint; commit only your own files; conventional message ending with
`Co-Authored-By: …`. Do **not** merge/push to `main` without operator confirmation.

**Session gotchas (carried from S104–S99):**

1. **Two judges — do not conflate.** Debate Judge (`deliberate`, → Opus) vs scorer Judge
   (`LLMJudgeScorer`, EXP-004, stays champion). Every name/test must make clear which one it means.
2. **Real models:** OpenAI GPT-5.5 (`OPENAI_MODEL`, `LLM_PROVIDER=openai`) for debate; Opus via
   `DELIBERATION_JUDGE_MODEL=claude-opus-4-8` + `ANTHROPIC_API_KEY`. Run live checks with
   `uv run --extra llm python …`. Unit tests use `FakeLLMClient` (two distinct instances to prove the
   split).
3. **`_parse_verdict` already fails safe** to `revise` on unparseable JSON — keep that; Opus must still
   return the `{"ruling":..,"rationale":..}` JSON (JUDGE_SYSTEM already demands JSON-only).
4. **Re-freezing rewrites a committed artifact** (`deliberation_golden.json`) — that is expected and must
   be committed; note the model config in the closeout so the baseline's provenance is clear.
5. **`detect-secrets`** false-positives on `key`/`secret`/`token` near string literals — neutral names or
   `# pragma: allowlist secret`. Keep real keys in `.env` only.
6. **mypy `--strict`** covers tests; annotate; `if TYPE_CHECKING:` for annotation-only imports.
7. `jq` is installed + allowed (`Bash(jq:*)`); `gh --jq` also works.

## Notes

This is ADR-0010 in action: models are a **gated** parameter, and here the operator deliberately moves the
adjudicator to Opus. The value is asymmetric-by-design — let the debaters be fast and combative, let the
decision be made by the strongest reasoner — while the drift-firewall (re-frozen) still guarantees the
configuration cannot silently degrade. The debate Judge and the scorer Judge staying distinct is what
keeps the eval meaningful.

## Closeout evidence

- **Implemented by Codex** on `sprint-109-heterogeneous-deliberation-models`; merged to `main` `81c3922` at
  **0.52.00**. `make ci` verified locally: **9/9 green, 1266 passed / 5 skipped / 100% coverage**.
- **Shipped:** per-role `judge_llm` in `kernel.deliberate`; `scripts/deliberate.build_role_llms`; dedicated
  `DELIBERATION_JUDGE_*` env (default `anthropic` / `claude-opus-4-8`); threaded through the veto. **Bonus
  beyond scope:** the veto now debates a **grounded** proposition (`orchestration/veto_context.py` injects
  real graph evidence provider→scanner→analyst→PM), fixing the S96 thin-proposition finding. The EXP-004
  `LLMJudgeScorer` was left untouched, as required.
- **Functional activity proven** via a **temporary gpt-5 judge** (`DELIBERATION_JUDGE_MODEL=gpt-5`, inline
  override): a live `scripts/deliberate.py --real` produced `MODE: real (debate OpenAI gpt-5.5 · judge
  OpenAI gpt-5)`, real Defender/Challenger turns, and a separate-judge `VERDICT: REVISE`.
- **⚠ DEFERRED — the two items below are NOT done** (Anthropic `credit balance too low`; **operator
  accepted landing without them, 2026-07-03**, on the basis that Opus↔GPT judge substitution is unlikely to
  differ dramatically and the wheels-move test proved functional activity):
  1. The **real-Opus** functionality check (GPT-5.5 debaters + Opus judge live).
  2. The **drift-firewall golden re-freeze** — the committed `scripts/deliberation_golden.json` is the
     **pre-Opus baseline** and MUST be re-frozen (`scripts/deliberation_gate.py --freeze --real`) at the
     re-run, else the gate baseline does not reflect the shipped champion.
  A re-run is scheduled (Sunday 2026-07-05 calendar reminder). Until then, ADR-0010's "champion judge =
  Opus, gated" is **asserted in config but not yet gate-proven**.
