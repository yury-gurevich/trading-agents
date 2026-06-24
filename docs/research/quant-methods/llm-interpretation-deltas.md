# LLM parameter interpretation — critique & the deltas DSPy must close

**Status:** Reference / experiment · **Date:** 2026-06-24 · **Model:** gpt-5.4 (the deliberation model)

> Method: asked the debate model to interpret **86 decision parameters cold** — given only
> `agent.name = default`, with our `why` justifications **withheld** — so we test *its* understanding,
> not its ability to parrot ours. Then critiqued against [quant-methods.md](quant-methods.md) and the
> code. **The deltas are the targets DSPy (the role-prompt compiler, DL-21) must close**, because a
> Defender/Challenger that misreads a parameter argues from a flawed model.

## Headline: the model is a competent quant — which is the good news *and* the trap

It correctly read ~90% on general finance knowledge: RSI-14 ("standard medium-term"), MACD 12/26/9,
ATR → "stops, targets, position sizing depend on current volatility", the VIX ladder, reward/risk 1.5,
`confidence_floor`/`span` → "confidence runs 0.3 to 0.9". So the debate stands on a solid foundation.
**But its errors aren't ignorance — they're (a) misreading our *implementation*, and (b) assuming the
system is more sophisticated than it is.** Both are dangerous in a debate, because they sound right.

## Delta class 1 — implementation misreads (model's general knowledge ≠ our code)

| Param | Model's reading | Actual (our code) | Why it matters in a debate |
| --- | --- | --- | --- |
| `provider.max_daily_move_sigma=4.0` | "max one-day move **in that stock's volatility units**; extreme movers filtered" | a **pooled cross-sectional z-score** across *all* tickers' intraday returns — a **data-integrity gate**, not a per-stock vol filter (the DL-17 bug) | a Challenger arguing "this name's 4σ move" is *wrong*; it's 4σ vs the whole universe's pooled distribution |
| `provider.base_stop_loss_pct` / `base_take_profit_pct` / `base_min_confidence` | fixed provider stops/threshold | **seed defaults the regime + confidence modulate** (`base_*`) | a Defender citing "fixed 5% stop" misses that the gate *tightens in risk-off* |
| `analyst.signal_diversity_slack=5.0` | UNSURE → "tolerance for **correlated** signals" | slack to surface a signal from an **unused pillar** in the rationale (diversity of *explanation*, not of correlation) | wrong mental model of how the rationale is built |

## Delta class 2 — the dangerous one: the model assumes guardrails we don't have

The model read `portfolio_manager.max_sector_pct=0.30` as *"limits hidden concentration **from
correlated holdings**."* That is the textbook-correct *intent* — **but our run just opened 4
semiconductors** (INTC/AMD/CSCO/QCOM). We have a **sector cap, not a name-correlation penalty**, and
the sector classification let them through. So:

- a **Defender** would (plausibly, fluently) claim "concentration is controlled" — *false for our system*;
- a **Challenger** would *fail to attack* the concentration, falsely reassured by a guardrail that
  doesn't actually bind.

Same pattern elsewhere: the model assumes sizing is risk-appropriate (it's **fixed-fraction**, not
vol-targeted) and that thresholds adapt (they're **absolute**, not regime-conditional). **The model
debates an idealised system; we run a thinner one.** This is the single most important finding.

## Delta class 3 — honest uncertainty (the `UNSURE` flags)

The model flagged `UNSURE` and *guessed well* on `nw_bandwidth`/`nw_lookback` (Nadaraya-Watson),
`alpha158_pillar_weight` (disabled factor pillar), `ingest_chunk_size` (rate-limit chunking). These are
**low-risk** — it knew it didn't know. Only `signal_diversity_slack` was an UNSURE that guessed *wrong*.

## Delta class 4 — process: the ask truncated

The response hit the 3500-token cap mid-`scanner.min_price`, so `max_beta`, `earnings_exclusion_days`,
`candidate_cap`, `bypass_scanner_filter` went uncovered. **DSPy must chunk the parameter context**, not
dump 86 at once — itself a steering requirement.

## What DSPy must encode (the correction targets)

1. **Per-parameter implementation notes** wherever the model's finance knowledge ≠ our code (Class 1).
   Source: the `tunable()` `why` fields we *withheld* here + [quant-methods.md](quant-methods.md).
2. **Explicit "the system does NOT do X" facts** (Class 2) — the [quant-methods Part 2](quant-methods.md)
   coverage gaps as first-class context, so the roles cannot assume guardrails we lack. *Without this,
   the debate is falsely reassuring — worse than no debate.*
3. **Chunked, retrieved context** (Class 4) — feed each role only the parameters relevant to the
   decision under test, not all 86.
4. **The eval still decides** (DL-21): even with perfect context, compile the roles against *do upheld
   decisions outperform?* — understanding is necessary, not sufficient.

## The meta-insight

The model doesn't need to be taught *finance* — it needs to be taught **this system's actual behaviour
and its limits**. DSPy's job here is less "make it smarter" and more "stop it assuming we're smarter
than we are." That is exactly what makes a debate *defensible* rather than *plausible*.
