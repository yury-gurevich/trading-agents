<!-- Agent: deliberator | Role: sprint spec — measure whether the veto agrees with itself before anything is built on its verdicts -->
# S173 — a verdict must be reproducible

**Closes:** [DL-104](../design-log.md) (e) · **Opens from:** [DL-105](../design-log.md) ·
**Type:** feat ·
**Target version:** next available MINOR after
[S172](sprint-172-independent-debates-run-independently.md) (`0.91.00` or `0.92.00` depending on
order) · **Branch:** `sprint-173-a-verdict-must-be-reproducible`

> Handover to a delegated coding agent. Everything under **Measured** was read off the live spine on
> 2026-08-10/11. Everything marked **Assumed** has **not** been verified — check it before building
> on it.

## Why

**The veto does not agree with itself, and nothing measures that but hand-reading.**

**Measured** ([DL-104](../design-log.md)). Two `DeliberationRun`s on the **same model, same prompt,
same eighteen tickers, 3.5 hours apart** agreed on **9 of 16** comparable verdicts — **56 %**, on a
binary verdict, barely distinguishable from chance. Cross-vendor agreement was *higher*:
`claude-opus-5` vs `gpt-5.5` agreed on **12 of 17** shared tickers (**71 %**). Across four runs
carrying real verdicts, **45 `revise` of 58 real debates (78 %)**.

🪤 **A fail-open is stored with `verdict: "uphold"`** (`review_record.fail_open_review`), so any run
with fail-opens must have those tickers **excluded** before a rate is computed. DL-104's run D is
5 of **6**, not 5 of 10. Every metric in this sprint must apply that exclusion, and must prove it
applies it.

Until reproducibility is a number the gate reads, *"is the veto right"* is answered by hand — which
is exactly how DL-104 was produced, and does not scale to a nightly decision.

**Why the Batch API is the right substrate** ([DL-105](../design-log.md)). Measuring reproducibility
means replaying the same debates many times: thousands of independent requests with **no latency
budget at all**. That is the Message Batches API's exact shape — up to 100 k requests per batch,
results keyed by `custom_id`, most complete inside an hour, **50 % off**. The live path's constraint
is wall clock (S172); this path's constraint is neither, so the two do not compete.

**Assumed, and to be checked first:** that replaying a stored `PMRun` reconstructs a
byte-identical deliberation context. If it does not, the harness is measuring context drift rather
than verdict reproducibility, and that must be fixed before any rate is reported.

## Steps, in order

1. **A read-only replay harness** — rebuild the deliberation context for a stored `PMRun` and its
   order set, deterministically, without touching the live spine. Follow the pattern `accept.py`,
   `trace_run.py` and `observatory.py` already use: **zero** `merge_node` / `add_edge` calls. This is
   the S160-revision-2 rule — a derivation writes nothing.
2. **Batch submission** with `custom_id` = `{pm_run}:{ticker}:{repeat}:{role}`. 🚨 Results arrive in
   **any order** — key by `custom_id`, never by position.
3. **Prompt caching on the shared prefix.** Every request in a batch shares the system prompt and
   most of the order-independent context; put the `cache_control` breakpoint at the end of the
   shared span, not at the end of the whole prompt, or each request writes its own entry and nothing
   is ever read.
4. **The metrics**, each with fail-opens excluded and the exclusion count reported alongside:
   **self-agreement** (same model, same input, N repeats), **cross-vendor agreement**, and
   **agreement with the DL-104 hand-checked ground truth** on the tickers where it exists.
5. **The gate** — `scripts/deliberation_quality.py`, reporting PASS/FAIL against a `tunable()`
   floor. Ships **warn-only**, exactly as S156 did for law-coverage assertion E: a gate whose
   threshold has never been calibrated must not block a merge on its first day.
6. **Re-derive the 56 % baseline** from the four existing `DeliberationRun`s through the new harness.
   If the harness cannot reproduce the hand-computed figure, the harness is wrong — say so and stop.

## Success factors

1. **Self-agreement is a number with a confidence interval**, measured over ≥ 5 repeats on ≥ 3
   historical `PMRun`s, with the fail-open exclusion count reported next to it.
2. **The 56 % baseline is reproduced or refuted** against DL-104's four runs, by the harness rather
   than by hand.
3. **The harness writes nothing** — a planted `merge_node` in the derivation path fails a test,
   watched failing first.
4. **Batch economics measured, not assumed:** report actual batch cost against the equivalent
   synchronous cost, and the observed turnaround.
5. **The gate can fail** — a planted low-agreement fixture drives `deliberation_quality.py` to FAIL;
   a planted high-agreement fixture drives it to PASS.
6. `make ci` exit 0 unpiped to a file, 100.00 % coverage floor held.

## Traps

- 🪤 **Do not run this before [DL-104](../design-log.md) (a) and (b) land.** Six of fifteen vetoes
  were manufactured by the deliberator's own context builder (the invented ATR fragment at
  `context_pm.py:138`). Measuring reproducibility over that fragment measures the fragment.
- 🪤 **Batch is Anthropic-only, and the deliberator key is limited until 2026-09-01**
  ([DL-99](../design-log.md)). Either wait for the date or resolve the limit —
  [S170](sprint-170-one-llm-adapter-in-the-plumbing.md) carries the same dependency.
- 🪤 **The `fallbacks` parameter is rejected on the Batches API.** A refusal in a batch result is
  handled by the caller, not by a server-side fallback.
- 🪤 **`max_tokens: 0` is rejected inside a batch** — the cache pre-warm trick does not apply here.
- 🪤 **Self-agreement is not accuracy.** A veto that agrees with itself 100 % of the time on unsound
  grounds is reproducibly wrong. This gate measures *precision of process*; DL-104 class-3 (the
  grounds that checked out correct) is the only accuracy signal we have, and it is 2 of 15.
- 🪤 **Do not let the harness become a second live tracker.** Its output is a report, not state; the
  live "does it work" proof stays in `docs/laws/ledger.md` and `docs/laws/drift-register.md`.

## Closeout — evidence

<!-- Coding agent: replace this comment with the proven result. Required: files changed, the measured
     self-agreement figure with its confidence interval and fail-open exclusion count, whether the
     56 % baseline reproduced, the planted-write test watched failing first, measured batch cost vs
     synchronous cost and turnaround, both planted gate fixtures, the exact `make ci` summary
     (unpiped, redirected to a file), and `make gate-ran` output for the final tip.
     Do not merge until every success factor above is answered with a measurement. -->
