# EXP-005 · Operationalise the drift firewall — golden baseline + model-swap gate

**Date:** 2026-06-25 · **Status:** ✅ complete — **firewall demonstrably trips on a real
side-grade** (gpt-5.4 silently dropped a flaw gpt-5.5 caught) · **Feeds:** DL-24 (the gate is now
runnable); DL-21/22 (the golden set is DSPy's compile metric)

## Purpose

EXP-004 *armed* the firewall (proved grounding + a semantic scorer discriminate on Class-1). EXP-005
makes it **operational and falsifiable**: freeze the champion's verdicts as a **golden baseline**, build a
**regression gate**, and run a live **model-swap A/B** to show the gate catches the exact failure DL-24
foresees — a model swap that makes "reports come out slightly different deep in the code," silently.

**Question:** does a concrete gate (champion golden + a candidate run) actually catch a real regression
when the debate model is swapped — and by how much?

## Process

- **Gate primitive** (`kernel/deliberation_gate.py`, kernel-pure): `passing_names` (a model's competence
  set) + `check_baseline(candidate, golden_passing)` → `BaselineCheck{regressed, gained, passed}`. Trips
  iff the candidate fails any case the golden passed. Pure set logic; the golden (trading cases) lives
  pack-side.
- **Runner** (`scripts/deliberation_gate.py`): `--freeze` runs the champion on the grounded Class-1 library
  and writes `deliberation_golden.json`; `--check MODEL` runs MODEL as the **debater** while the champion
  stays the **judge** — *the fixed measuring instrument*, so the A/B isolates the debate model and does not
  confound it with judge quality.
- **Run:** froze the golden on **gpt-5.5**; checked **gpt-5.4** as the candidate debater (judge held at
  gpt-5.5). 1 round, grounded.

## Delivery

- `kernel/deliberation_gate.py` (+ 4 tests, 100% coverage); `scripts/deliberation_gate.py`; the committed
  golden artifact `scripts/deliberation_golden.json` (model, date, passing set, per-case). v0.31.00,
  `make ci` green (1102 passed). Live transcripts → scratchpad `exp005_freeze.txt`, `exp005_check_54.txt`.

### Result

| | model | pass-rate | regressed vs golden |
| --- | --- | --- | --- |
| **golden** | gpt-5.5 | 5/6 (83%) | — |
| **candidate** | gpt-5.4 | 4/6 (67%) | **`calendar-staleness`** |

**Verdict: FAIL — firewall tripped.** Swapping the debater from gpt-5.5 to gpt-5.4 silently lost the
`calendar-staleness` flaw (staleness counts calendar days, not trading sessions — DL-10). gpt-5.5 caught
it; gpt-5.4 did not. The golden's one non-passing case (`fixed-fraction-size`) is the champion's own
upheld-despite-caught miss from EXP-004 — *not* counted against the candidate, because the gate measures
**regression from the champion**, not perfection.

## Interpretation

1. ✅ **Golden frozen** — a committed, provenance-stamped artifact (model + date + passing set).
2. ✅ **Gate works** — pure, CI-tested; trips on exactly the regressed case, reports it by name.
3. ✅ **A/B measured** — a real near-peer side-grade (5.5→5.4) **regressed one Class-1 flaw** (−16 pp). The
   firewall caught precisely the silent drift DL-24 was built to stop.
4. ✅ **CI-safe** — deterministic fakes in tests, 100% coverage, `make ci` green.
5. ✅ **Pack wall** — gate logic kernel-pure; the golden (trading cases) pack-side.

**What this means.** DL-24 is no longer a principle — it is a command you can run: a model change must
clear `deliberation_gate.py --check <model>` against the golden before it ships. The same golden set is
DSPy's compile metric (DL-21/22): when a swap regresses, you re-compile the role prompts against this set
until the gate passes again — that is the firewall *and* the repair loop.

**Honest limitation (LAW-06).** LLM debates are non-deterministic, so a single-run golden + single-run
check carry sampling noise; `calendar-staleness` could be a borderline case. The production gate should
**average N runs** (freeze the golden as cases that pass robustly across N; trip only on a regression that
persists across N) before it blocks a deploy. The mechanism is proven; hardening it to N-run is the next
increment — and is exactly what CI-4's multi-run variance support (S93) already plans to provide.
