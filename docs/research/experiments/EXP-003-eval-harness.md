# EXP-003 · Build the manufactured-eval harness (Path B) — and what the first run taught

**Date:** 2026-06-24 · **Status:** complete (harness shipped; one success factor INCONCLUSIVE — see below)

## Purpose

Build the deterministic eval harness (DL-23 Path B) that scores a debate against a *known-flaw answer
key*, so the deliberation is **measurable without trade outcomes** — the substrate DSPy optimises
against. Defined outcome + test up front, then verify (LAW-02).

## Process

- **`kernel/deliberation_eval.py`** (kernel-pure, generic): `EvalCase` (decision + flaw keywords +
  expected verdict), `score_debate` (Challenger surfaced the flaw? verdict ≠ uphold?), `run_eval`,
  `pass_rate`.
- **`scripts/deliberation_eval.py`** (trading cases — pack, not kernel): 4 adversarial decisions
  (concentration, event-risk, tight-stop, thin-signal), the flaw-revealing facts in the **grounding**,
  blind = bare decision. Runs blind vs grounded.
- Ran blind vs grounded on **gpt-5.5**.

## Delivery

- Harness: `kernel/deliberation_eval.py` — **100% coverage, 6 tests**. Runner: `scripts/deliberation_eval.py`.
- Live transcripts: scratchpad `eval_real.txt`, `eval_real2.txt`.

## Interpretation

**Success factors (LAW-02):** ✅ deterministic scorer (1) · ✅ case library (2) · ✅ CI-safe + 100%
coverage (3) · ✅ platform/pack wall respected (5). **⚠️ Factor 4 (grounded > blind) — NOT shown.**

gpt-5.5 scored **100% blind *and* grounded.** The finding: a strong model catches **textbook** flaws
(concentration, event risk) **from world knowledge alone** — it *knows* NVDA is a semiconductor, so it
raises "sector concentration" without being told the portfolio. So grounding shows **no delta on
Class-2 (textbook) flaws**, and EXP-002's single-sample delta did not hold at aggregate (it was
non-deterministic noise on one blind run).

**What this sharpens (extends DL-22):** grounding's measurable ROI is **Class-1** — facts the model
*cannot* derive (our `max_daily_move_sigma` is pooled; `base_*` is regime-modulated) — **not Class-2**,
which a capable model already knows. Two refinements the harness now enables:

1. **Target Class-1 cases** — adversarial decisions whose flaw needs *our implementation*, not finance
   (e.g. "this stock's individual 9% move won't trip the data gate, because it's pooled cross-sectional").
2. **Replace the keyword scorer** — it is too lenient (matches generic caution). A stricter match or an
   **LLM-judge** is needed to detect subtle grounding effects.

**Verdict:** the **harness is the deliverable and it is done** — the eval infrastructure DSPy needs,
deterministic and CI-safe. The case/scorer tuning is the next iteration (itself an experiment), now
*possible* because the harness exists. **A strong model needs grounding less than expected — which is
itself a result worth knowing before investing in DSPy.**
