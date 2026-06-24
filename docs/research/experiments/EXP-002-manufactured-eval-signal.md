# EXP-002 · Can we manufacture a DSPy eval signal *without* trade outcomes?

**Date:** 2026-06-24 · **Status:** complete · **Feeds:** DL-23 (manufacture the eval set); unblocks DSPy

## Purpose

DSPy needs an eval set to optimise the deliberation roles, and the "natural" metric (do upheld
decisions out-perform?) needs **realised trade outcomes that don't exist yet** (the 5 live positions
haven't resolved). That was framed as a wall. **Probe the creative escape:** can we manufacture an eval
signal *today* from our own documented knowledge — i.e. does injecting EXP-001's grounding make the
debate catch a flaw it otherwise misses, on a case whose right answer we already know?

## Process

- One decision — **"Buy NVDA at market today"** — debated twice on **gpt-5.5**, one round, identical
  roles. The only difference was the **context**:
  - **Ungrounded:** price signals only (`momentum +0.7; RSI 60; stop -3%`).
  - **Grounded:** + *"portfolio already holds INTC, AMD, CSCO, QCOM (all semiconductors); the pipeline
    has a 30% sector cap but NO name-correlation penalty; sizing is fixed-fraction; the stop is not
    earnings-gap-aware"* — i.e. the EXP-001 deltas + quant-methods Part-2 gaps as context.
- **Deterministic score (the answer key):** did the Challenger raise the *known* flaw — correlated
  semiconductor concentration?

## Delivery

- Transcript: session scratchpad `eval_demo.txt` (both debates side by side).

## Interpretation

- **Ungrounded:** the Challenger missed concentration entirely — it didn't know the book — and gave only
  generic objections (tight stop, no catalyst).
- **Grounded:** the Challenger nailed it — *"crowded semiconductor cluster… all sell off together on the
  same AI/semis factor shock… most correlated, high-beta name without volatility-adjusted sizing or
  correlation control."*
- **The delta (caught vs missed) is a binary, deterministic training signal available NOW**, scored
  against our own documented gaps — **no trade outcomes required.** Path B (DL-23) is proven: we can
  manufacture DSPy's eval set today, and grow the answer key as we discover more gaps.

**Bug surfaced:** the *ungrounded* run's Judge returned **unparseable JSON** → `_parse_verdict` defaulted
to `revise` ("judge response unparseable"). The judge prompt/parser is **not robust** to the model
wrapping or prosifying its JSON. Follow-up: harden the judge output contract (e.g. tool-use / stricter
parse / retry) — tracked for the deliberation harness.
