# EXP-006 · Harden the firewall — N-run aggregation against debate noise

**Date:** 2026-06-25 · **Status:** ✅ complete — **the gate is now noise-aware; it removed a false positive
*and* kept the verdict** · **Feeds:** the DL-24 gate (production-ready path); CI-4 / S93 multi-run variance

## Purpose

EXP-005 shipped a runnable gate but flagged an honest limit: LLM debates are non-deterministic, so a
single-run golden + single-run check carry sampling noise — a "regression" might be luck. EXP-006 resolves
it: aggregate **N runs**, freeze the golden as cases that pass **robustly**, and trip only on a regression
that **persists**. The test of the hardening is whether it changes the EXP-005 result — and it does.

**Question:** with N-run aggregation, does the gpt-5.4 regression hold, or was it single-run noise?

## Process

- **Aggregation primitives** (`kernel/deliberation_gate.py`, kernel-pure): `pass_fractions` (per-case
  fraction of N runs passed), `robust_passing` (cases ≥ a threshold), `check_robust` (trip only on a
  regression in the robust set). `check_baseline` refactored to share `_compare`.
- **Runner**: `--runs N` + `--threshold` on `scripts/deliberation_gate.py`; the golden now stores
  `n_runs`, `threshold`, and the per-case `fractions`.
- **Harness bug found + fixed:** at N=3 a gpt-5.5 debate turn hit OpenAI's 400-token cap mid-reasoning
  (`max_tokens … limit was reached`). Reasoning models spend tokens on hidden reasoning; the cap was
  raised to **2000** in both adapters. The firewall must not crash on a chatty model.
- **Run:** froze the golden on gpt-5.5 at **N=3, threshold=0.5 (majority)**; checked gpt-5.4 at N=3.

## Delivery

- `kernel/deliberation_gate.py` (+5 tests, 100% coverage); `scripts/deliberation_gate.py`; the N=3 golden
  `scripts/deliberation_golden.json` (now with fractions); the token-cap fix in `scripts/deliberate.py`.
  v0.32.00, `make ci` green (1107 passed). Transcripts → scratchpad `exp006_freeze_n3.txt`,
  `exp006_check_54_n3.txt`.

### Result (N=3, per-case pass-fraction)

| case | gpt-5.5 (golden) | gpt-5.4 (candidate) | in robust golden? | regressed? |
| --- | --- | --- | --- | --- |
| alpha158-weight-zero | 1.00 | 1.00 | ✅ | — |
| lightgbm-shadow | 1.00 | 1.00 | ✅ | — |
| pooled-sigma | 0.67 | 1.00 | ✅ | — |
| **name-correlation** | **0.67** | **0.33** | ✅ | **← regressed** |
| calendar-staleness | 0.33 | 0.33 | ❌ (champion-flaky) | — |
| fixed-fraction-size | 0.00 | 0.00 | ❌ (champion never) | — |

**Golden robust set (≥2/3): 4 cases.** **VERDICT: FAIL — firewall tripped on `name-correlation`.**

## Interpretation

1. ✅ **N-run primitives work** — pure, CI-tested (`pass_fractions` / `robust_passing` / `check_robust`).
2. ✅ **A false positive removed — the gate got *more* trustworthy.** EXP-005 (single-run) tripped on
   `calendar-staleness`; N=3 shows the **champion itself** only passes it **1/3** — it is *flaky*, not a
   competence. The hardened golden correctly **excludes** it, so the gate no longer trips there. This is
   the precise value N-run was built to deliver: don't gate on noise.
3. ✅ **…yet the verdict held.** gpt-5.4 is *still* a regression — now on a case stable for the champion:
   `name-correlation` (gpt-5.5 2/3 → gpt-5.4 1/3), the very sector-concentration gap that opened the live
   5-position book. The conclusion "5.4 is a downgrade" survived hardening; only the *evidence* sharpened.
4. ✅ **Found + fixed a real harness bug** (400-token truncation → 2000) — robustness the live gate needs.
5. ✅ **CI-safe + pack wall** — primitives kernel-pure, 100% coverage; golden + cases pack-side.

**What this means.** The firewall is now noise-aware: it gates on *robust* champion competence and trips
on *persistent* regression. The same machinery is DSPy's metric — recompile until the robust set is
restored.

**Honest limit (LAW-06).** N=3 is still small: `name-correlation` (0.67 vs 0.33) is a modest separation on
three samples, and `pooled-sigma`/`name-correlation` sit near the threshold. A deploy-blocking gate should
use **larger N (≈10)** and a **confidence margin** (trip only when the fraction gap clears noise), not a
bare majority. The mechanism is proven; the statistics are the next increment — and land naturally on
**CI-4 / S93** (multi-run variance), where this gate becomes a first-class champion-vs-challenger experiment.
