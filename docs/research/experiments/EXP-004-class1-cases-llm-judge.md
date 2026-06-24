# EXP-004 · Arm the drift firewall — Class-1 cases + an LLM-judge scorer

**Date:** 2026-06-25 · **Status:** DESIGNED (pending run) · **Feeds:** DL-24 model-swap gate; DL-21/22 DSPy signal

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

## Delivery (expected)

`kernel/deliberation_eval.py` (or a sibling) with the injectable LLM-judge scorer; `scripts/deliberation_eval.py`
extended with the Class-1 case set; 100% coverage; live transcripts → scratchpad. Filled on run.

## Interpretation (the test — success factors, verified on run, LAW-02)

The experiment **succeeds (firewall armed)** iff:

1. **Class-1 verified** — each case cites its our-fact + source, and an independent read agrees a
   world-knowledge-only model cannot derive the flaw. (≥ 6 cases.)
2. **Grounding ROI shown** — *grounded* pass-rate − *blind* pass-rate **≥ 0.30** on the Class-1 library.
   *If < 0.30, that is itself the finding* — even our implementation gaps are inferable, a louder argument
   that the gate must lean on golden verdicts, not on grounding deltas.
3. **Scorer sharper** — the LLM-judge disagrees with keyword on ≥ 1 case *in the direction of correctness*
   (catches a right-idea/wrong-word, or rejects a generic-caution false-positive); disagreements tabulated.
4. **CI-safe** — deterministic fake judge in tests, 100% coverage, `make ci` green.
5. **Pack wall** — Class-1 trading cases stay caller-side; the judge mechanism stays kernel-pure.

**Decision it informs.** If (2) holds → **freeze a golden verdict baseline** on the Class-1 library: that
frozen set *is* the concrete model-swap regression gate (DL-24) and DSPy's compile metric. If (2) fails →
record that grounding's ROI is below its cost, and the gate rests on the LLM-judge + golden verdicts alone.
Either outcome is a result; both are recorded here on run.
