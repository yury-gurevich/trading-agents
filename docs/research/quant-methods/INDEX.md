# Quant methods — interpretation, coverage, and gaps

**Status:** Reference / analysis · **Date:** 2026-06-24

The operator-readable guide to the quantitative methods behind every decision: what each signal
*measures*, why it matters, how to read it, and how they combine — plus the quant areas we have **not**
covered and the **deterministic** parameters that would raise prediction confidence.

- **[quant-methods.md](quant-methods.md)** — Part 1: every signal in use (trend, mean-reversion,
  volatility, regime, volume, patterns, fundamentals, sentiment, the ML shadow, sizing/risk) with the
  4-question reading (measures / why / how-to-read / knob). Part 2: uncovered quant areas. Part 3:
  prioritised deterministic additions.
- **[llm-interpretation-deltas.md](llm-interpretation-deltas.md)** — asked the deliberation model
  (gpt-5.4) to interpret 86 parameters *cold*; critique + the deltas DSPy must close. Key finding: the
  model is a competent quant but **assumes guardrails we don't have** (e.g. "sector cap limits
  correlated concentration" — yet we opened 4 semis). DSPy must teach *our actual behaviour and limits*,
  not idealised finance.

**Why it exists:** a trade you can't explain in terms of facts + interpretable parameters is not a
defensible decision (LAW-05). This makes the quant legible to the operator and grounds the Deliberation
roles so they can argue a decision on the merits.

**Companion:** [../parameter-inventory/](../parameter-inventory/INDEX.md) is the *registry* (every
`tunable()` default/bound); this is the *meaning*. **Feeds:** the "perfect the bundle" backlog
(Part 3 is a deterministic, champion-eligible to-do list) and the Deliberation/DSPy eval (Part 3 item 8).
