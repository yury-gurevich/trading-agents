# EXP-004 · Arm the drift firewall — Class-1 cases + an LLM-judge scorer

**Date:** 2026-06-25 · **Status:** ✅ complete — **firewall armed** (grounded ≫ blind on Class-1, judge
sharper than keyword) · **Feeds:** DL-24 model-swap gate; DL-21/22 DSPy signal

## Purpose

EXP-003 proved the harness *runs* but left the firewall **unarmed**. gpt-5.5 caught the textbook
(**Class-2**) flaws *blind*, so two things never materialised: (a) the blind-vs-grounded delta — the
measurable ROI of grounding — and (b) confidence in the scorer, because keyword-match is too lenient (it
fires on generic caution). Until the eval *discriminates*, the DL-24 rule "a model swap must pass the
eval" is a **gate with no teeth**, and DSPy (DL-21/22) has no signal to compile against.

**Question:** on **Class-1** cases — flaws derivable *only* from our implementation, not world knowledge —
(1) does *grounded* materially beat *blind*, and (2) is an **LLM-judge** scorer sharper than keyword-match?

## Process (method — the build, then the run)

**Build.** Scorer mechanism stays kernel-pure (decision-agnostic); the trading cases stay caller-side
(platform/pack wall).

- **Class-1 case library (≥ 6).** Each flaw must be *invisible* from finance world-knowledge and revealed
  **only** by a cited our-implementation fact (that citation is what *proves* it is Class-1). Seed set:

  | # | Decision | Flaw — needs *our* fact | Where the fact lives (citation) |
  | --- | --- | --- | --- |
  | 1 | "this 9% single-name move is fine" | won't trip `max_daily_move_sigma` — sigma is **pooled cross-sectional**, not per-name | validate-once fix, 0.28.01 |
  | 2 | "Friday's signal is still fresh Monday" | staleness counts **calendar days, not trading sessions** — N sessions stale over a long weekend | DL-10 |
  | 3 | "4 semis pass the sector cap, so size up" | the GICS-sector cap has **no name-correlation penalty** | quant-methods Part 2/3; the live 5-position concentration |
  | 4 | "high-beta name, normal size" | sizing is **fixed-fraction**, not vol-adjusted/Kelly | quant-methods (sizing) |
  | 5 | "Alpha158 is enabled, trust the factor" | the Alpha158 pillar **weight = 0.00** — contributes nothing | S68 / Q2 |
  | 6 | (one more from the 133-tunable inventory) | … | parameter-inventory |

  Each case carries: the flaw, the our-fact that reveals it (+ citation), the flaw-revealing **grounding**,
  and **blind** = bare decision + raw signal only.

- **LLM-judge scorer.** `score_debate` gains an *injectable* judge: instead of keyword-in-text, an LLM
  reads the Challenger's turns **and the case's flaw statement** and rules "did it identify *this specific*
  flaw?" (semantic, not lexical). Kernel-pure, judge injected — mirrors `deliberate()`'s client injection;
  a deterministic fake judge keeps the unit gate at 100% coverage. (New sibling module if it crosses 150 LOC.)

**Run.** Blind vs grounded on each Class-1 case, scored by **both** scorers (keyword + LLM-judge), on gpt-5.5.

## Delivery

- **Harness** (kernel, v0.30.00): `LLMJudgeScorer` (injectable semantic scorer — "did the Challenger catch
  *this* flaw?", JSON `{"caught": …}`) + `run_debates` (run each debate once so both scorers share the
  result — no double model spend). `EvalCase` gained a `flaw` field. **1098 tests, 100% coverage.**
- **Cases** (`scripts/deliberation_eval.py`, pack side): the **6-case Class-1 library** + a 2×2 runner
  (blind|grounded × keyword|judge). Live transcript → scratchpad `exp004_class1.txt`.
- **Run:** gpt-5.5, `--class1 --real`, 1 round.

### Result (gpt-5.5)

| | keyword | llm-judge |
| --- | --- | --- |
| **BLIND** | 33% | **0%** |
| **GROUNDED** | 83% | **83%** |
| **Δ grounded − blind** | **+50 pp** | **+83 pp** |

Grounded, all 6 flaws were caught by *both* scorers; pass-rate 83% (5/6) — one case had its flaw caught
yet the Judge still **upheld** it (a Judge-calibration data point, exactly what DSPy will tune). Blind, the
judge scored **0%** while keyword scored 33%: blind, the model raised *generic* caution that keyword-matched
but did **not name the specific flaw** — and the judge correctly refused to count it.

## Interpretation (success factors verified, LAW-02)

1. ✅ **Class-1 verified** — 6 cases, each citing its our-fact (pooled sigma 0.28.01 · calendar staleness
   DL-10 · no name-correlation penalty · fixed-fraction sizing · Alpha158 w=0.00 · LightGBM shadow).
2. ✅ **Grounding ROI shown — decisively.** +50 pp (keyword) and **+83 pp (judge)**, both far past the 0.30
   bar. On Class-1, grounding is the difference between catching nothing and catching everything — the ROI
   EXP-003 *couldn't* show on textbook (Class-2) flaws now shows in full.
3. ✅ **Scorer sharper.** Blind, keyword = 33% but judge = **0%** — the judge rejected the generic-caution
   false-positives the keyword scorer accepted. The LLM-judge measures *did it catch the actual flaw*, not
   *did cautious words appear*.
4. ✅ **CI-safe** — deterministic fake judge, **100% coverage**, `make ci` green (1098 passed).
5. ✅ **Pack wall** — Class-1 cases caller-side; `LLMJudgeScorer` / `run_debates` kernel-pure.

**Verdict — the drift firewall is armed.** Grounding *and* a semantic scorer both pay off precisely where
DL-24 needs them: on flaws only our implementation reveals. **Decision (factor 2 held): freeze a golden
verdict baseline on this Class-1 library** — that frozen set becomes the concrete **model-swap regression
gate** (a downgrade/side-grade must reproduce it) *and* DSPy's compile metric. The one upheld-despite-caught
case is the first calibration target. Next experiment: **EXP-005 — freeze the golden baseline + a model-swap
A/B** (run the gate against a cheaper model and measure the regression).
