<!-- Agent: planning | Role: sprint handover -->
# Sprint 119 — DSPy-compiled deliberation roles (DL-42): quality by measurement, not eloquence

**Phase:** Deliberation quality (DL-42 — the layer above the closed DL-41; second real instance of
the ADR-0010 `PromptOptimizer` port after S107's remediation selector)
**Branch:** `sprint-119-dspy-deliberation-roles`
**Status:** ready for handover (packaged 2026-07-08)
**Effort:** M/L

---

## Design decisions taken at packaging (LAW-06 — roads not taken recorded)

1. **Compile all three role prompts (defender, challenger, judge) — but gate and promote each
   independently.** The judge is measurable *objectively*: the Class-1/Class-2 eval cases have
   known expected verdicts, so judge compilation is scored by expected-verdict/keyword checks, not
   by an LLM judging itself (the EXP-004 `LLMJudgeScorer` is a separate scorer and stays the
   second opinion). *Ruled out:* debaters-only (leaves judge inconsistency — the verdict decider —
   on the table); one all-or-nothing promotion (a role that regresses would block the ones that
   improve).
2. **Runtime never imports DSPy** (ADR-0010, S107 precedent). Compilation is offline via
   `kernel/dspy_optimizer.py::DSPyPromptOptimizer` behind the port (`optimizer` extra — the
   diskcache advisory stays out of runtime/images); the runtime only ever loads a committed
   `PromptArtifact` JSON, and **only when env opts in**. Default = the hand-written champions,
   byte-identical (that is the regression fence).
3. **The metric is understanding + correctness + stability, with the firewall as a hard veto:**
   (a) Class-1 grounded pass-rate (known-flaw cases, keyword + LLM-judge scorers — the 2×2 rig in
   `scripts/deliberation_eval.py`); (b) `score_understanding` cited/understood rate (DL-31);
   (c) verdict stability across n=3 repeats on the four robust-passing golden cases. A compiled
   prompt that trips `scripts/deliberation_gate.py --check` is **rejected regardless of gains**.
   *Ruled out:* eloquence/style metrics (DL-31's whole point), a fresh eval set (the scaffolding
   already exists — DL-42's stated advantage).
4. **Promotion stays operator-held.** This sprint ships compiled artifacts + the
   champion-vs-challenger report; flipping any role's default is a later explicit commit. Nothing
   about the live veto path changes by default. *Ruled out:* auto-promote on a better score
   (ADR-0010's gate guards drift; the operator holds the swap, same as S111 `--apply`).

## Codex kickoff (paste this)

> Execute **Sprint 119 — DSPy-compiled deliberation roles** exactly as specified in this file
> (`docs/sprints/sprint-119-dspy-deliberation-roles.md`), including the four packaging decisions
> above. Read first: design-log **DL-42** (the layer distinction vs DL-41), `kernel/deliberation.py`
> (`DEFENDER_SYSTEM`/`CHALLENGER_SYSTEM`/`JUDGE_SYSTEM` — the compile targets),
> `kernel/optimizer.py` + `kernel/dspy_optimizer.py` (the port), `agents/master/remediation_gate.py`
> (`parse_prompt_artifact`/`load_prompt_artifact` — the S107 artifact pattern to mirror),
> `scripts/deliberation_eval.py` (Class-1/Class-2 libraries + 2×2 scorers),
> `scripts/deliberation_gate.py` + `scripts/deliberation_golden.json` (the drift firewall), and
> `kernel/deliberation_understanding.py` (`score_understanding`).
>
> - **Start:** from `main` (`git pull`), `git checkout -b sprint-119-dspy-deliberation-roles`
>   (delete any stale local branch first). **Hard gate:** `make ci` green, 100 % coverage,
>   ≤200-line modules, headers. Bump `pyproject.toml` **0.63.00 → 0.64.00** (feat) + `uv lock`.
> - **Part A — override plumbing + compile pipeline (code, CI-tested):**
>   1. **Role-prompt overrides in the kernel (additive, pure):** the deliberation entry points
>      accept optional per-role system prompts, defaulting to the current constants. With no
>      override the composed prompts are **byte-identical** to today — pin that with a test.
>   2. **Deliberation artifact loader** mirroring the S107 parse/load functions (placement per
>      layering — kernel beside `optimizer.py` is fine; kernel must not import agents). Artifact
>      `task` names: `deliberation.defender` / `.challenger` / `.judge`; model-stamped per
>      ADR-0010's (task × model) rule.
>   3. **Compile pipeline** `scripts/compile_deliberation_prompts.py`: builds `PromptExample`s from
>      the existing Class-1/Class-2 case libraries (reuse, don't re-author), runs
>      `DSPyPromptOptimizer` per role, writes one artifact JSON per role under `scripts/` (S107
>      pattern). Unit-test with the injectable `dspy_module` fake — no network, no real DSPy in CI.
>   4. **Champion-vs-challenger comparison** (extend `deliberation_gate.py` or a sibling script):
>      runs both prompt sets through metric (3) above, prints a per-role table
>      (pass-rate / understanding / stability, champion vs challenger), and **exits nonzero if the
>      challenger trips the golden firewall**. Fake-LLM unit path for CI.
>   5. **Env opt-in in the composition root** (`scripts/deliberate.py`): artifact path(s) via env
>      (e.g. `DELIBERATION_PROMPT_ARTIFACT_DIR` or per-role vars — pick one, document it); unset →
>      exactly current behavior. LLM and DSPy stay out of the kernel.
> - **Part B — the real compile + report (live; needs OpenAI + Anthropic keys from `.env`):**
>   1. Compile with the S109 role models (GPT-5.5 debaters, Opus `claude-opus-4-8` judge), DSPy via
>      `--extra optimizer`. Do not lower the S109 token budgets (debaters 8000 / judge 2000 — the
>      empty-challenger lesson).
>   2. Run the champion-vs-challenger report with **real** models on Class-1 grounded + the
>      stability repeats; include the per-role table verbatim in the closeout. Keep spend bounded:
>      state the call count before running (cases × 2 prompt sets × repeats); if it exceeds ~150
>      debate calls, trim repeats, not cases.
>   3. Golden firewall proof: `deliberation_gate.py --check` PASS with champion prompts **and**
>      with each compiled artifact loaded.
>   4. **Load-path proof:** one real deliberation with artifacts loaded via env (record verdict +
>      that the composed system prompts came from the artifacts), then unset env → prove prompts
>      are byte-identical to the constants again. No graph writes expected; if any occur, tear
>      down to 0 and say so. Record in `docs/laws/functionality-checks.md`.
>   5. Commit the compiled artifacts + report. **Do NOT flip any default** — promotion is a
>      separate operator decision (decision 4).
> - **Out of scope — flag, don't build:** promoting/defaulting any compiled prompt; the
>   EvoPrompt/TextGrad bake-off (R003 — same port, later); DL-39 (transcript-as-training-source)
>   and DL-40 (literacy-tiered explanations); any change to the live veto path, PM gates, or
>   locked laws; new eval cases beyond the existing libraries.
> - **Do NOT merge or push to `main`** — commit on the branch only; fill **Closeout evidence** here.

---

## Notes for the coding agent

- DSPy sits in the `optimizer` extra on purpose (accepted diskcache advisory, offline-only, in no
  deployed image) — do not move it into `runtime`, and keep `dspy` imports lazy/optional exactly
  like `kernel/dspy_optimizer.py` does today.
- `kernel/deliberation.py` is near the size warning — if the override params push it, split rather
  than squeeze (house rule; `veto_context_pm.py` is the S114 precedent).
- The four robust-passing golden cases are `alpha158-weight-zero`, `calendar-staleness`,
  `lightgbm-shadow`, `pooled-sigma` (re-frozen with the real Opus judge in the S109 re-run) — they
  are the stability set; do not re-freeze the golden in this sprint unless a prompt is promoted
  (which this sprint does not do).
- Windows console: model output can hit cp1252 encode errors — the eval scripts already
  reconfigure stdout to UTF-8; keep that pattern in new scripts.
- API keys come from `.env` (funded); load via explicit-path `load_dotenv`, never echo them.

---

## Closeout evidence

<!-- Coding agent: replace this comment. Required: files changed; version/deps; the byte-identical
no-override test; compile-pipeline unit evidence (fake dspy_module); exact `make ci` summary
(counts + coverage); live evidence — the real compile call counts + spend note, the per-role
champion-vs-challenger table verbatim, golden firewall PASS lines (champion + each artifact),
load-path proof (env set → artifact prompts; env unset → byte-identical constants); committed
artifact filenames; the functionality-checks.md row; explicit statement that no default was
flipped. State any deviation from spec explicitly. Do not merge. -->
