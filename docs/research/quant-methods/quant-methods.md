# Quant methods — what each one measures, why it matters, and what we're missing

**Status:** Reference / analysis · **Date:** 2026-06-24 · **Audience:** the operator (non-quant) + the
analyst/forecaster/PM agents + the Deliberation roles.

> Purpose (operator's ask): *"If it trades, make sure the decision is based on facts with the aid of
> quant parameters — and I need to understand what each one means, individually and in combination.
> Also identify the quant areas we did NOT cover, and what deterministic parameters would raise the
> confidence of a prediction."*
>
> Every parameter named here is a real `tunable()` — see [../parameter-inventory/](../parameter-inventory/INDEX.md)
> for defaults/bounds. This doc explains *meaning*; that doc is the *registry*.

---

## How to read a signal (the 4 questions)

For every signal below: **(1) what it measures** in plain language · **(2) why it matters** for a
trade · **(3) how to read it** (the number → the meaning) · **(4) the knob** that tunes it.

A single signal is rarely decisive — the analyst combines them into pillars (see *How they combine*).
The point of this doc is that **no number in a trade rationale should be a black box to you.**

---

## Part 1 — The signals we actually use

### A. Trend & momentum — *is it moving up, and with force?*

| Signal | Measures | Why it matters | Read it | Knob |
| --- | --- | --- | --- | --- |
| **SMA-200 / EMA-20 / EMA-50** | the average price over a window (simple vs exponentially-weighted) | the *direction* of the tide; price above a rising long average = uptrend | price > SMA200 = long-term up; EMA20 > EMA50 = short-term up | `sma_long_period=200`, `ema_short=20`, `ema_long=50` |
| **Golden Cross** | short average crossing *above* a long average | a regime flip from down to up | cross up = bullish trigger | `golden_cross_short_period=50` |
| **MACD** (12/26/9) | momentum = difference of two EMAs, vs its own signal line | acceleration/deceleration of trend | MACD > signal = momentum building; histogram shrinking = fading | `macd_fast/slow/signal` |
| **12-month momentum** (+0.6 in the demo) | trailing ~1-year return | the single most robust cross-sectional anomaly in equities (winners keep winning, medium-term) | positive = participating in an uptrend | (provider-supplied) |
| **Relative strength vs SPY** | the candidate's trailing return *minus* the benchmark's | is this name *leading or lagging the market*? leaders outperform | spread > 0 = beating the market | `rs_window=20`, `relative_strength_weight=0.2`, `benchmark_ticker=SPY` |

### B. Mean-reversion & extremes — *is it stretched and likely to snap back?*

| Signal | Measures | Why it matters | Read it | Knob |
| --- | --- | --- | --- | --- |
| **RSI** (14) | speed/size of recent up-moves vs down-moves, 0–100 | flags overbought (chasing risk) / oversold (bounce odds) | >70 overbought · <30 oversold · ~55 neutral (the demo's RSI 55 = *no edge*) | `rsi_period=14` |
| **RSI-2** | the same, ultra-short (2-day) | a fast pullback-in-uptrend timing signal | <10 in an uptrend = dip to buy | `rsi2_period=2` |
| **Stochastic** (14/3) | where the close sits within the recent high–low range | momentum *extreme* detection | >80 high in range · <20 low | `stoch_k/d_period` |
| **Williams %R** (14) | same idea, inverted scale | confirmation of stochastic | −20 overbought · −80 oversold | `williams_period=14` |
| **Bollinger Bands** (20, 2σ) | price ± 2 standard deviations of a moving average | how far price is from "normal"; band width = volatility | touch upper = stretched up; squeeze = vol coiling | `bollinger_window`, `bollinger_sigma` |

### C. Volatility & risk — *how violent is it, how much market risk does it carry?*

| Signal | Measures | Why it matters | Read it | Knob |
| --- | --- | --- | --- | --- |
| **ATR** (14) | average true daily range (size of the daily candle) | the *natural noise* of the name — how wide a stop must be to not get shaken out | high ATR = needs a wider stop / smaller size | `atr_period=14` |
| **Beta** (scanner) | cov/var of the name's returns vs the benchmark | systematic (market) risk — a beta-2 name moves twice the market | >1 = amplifies market moves; gate at `max_beta` | `max_beta=2.5`, `beta_min_observations` |
| **Daily-move σ anomaly** (provider) | is any bar's intraday return an outlier vs the pooled distribution? | a data-integrity *and* event flag — a >Nσ move means earnings/news/bad-print | tripped = the batch is "degraded" until reviewed | `max_daily_move_sigma` |
| **VIX regime** (provider) | the market's implied-volatility "fear gauge" | sets the *backdrop* — the same setup is worse in a risk-off tape | risk_on<15 · risk_off≥20 · high≥25 · extreme≥35 | `vix_*_threshold` |

### D. Trend *quality* / regime — *is the trend real, or just noise?*

| Signal | Measures | Why it matters | Read it | Knob |
| --- | --- | --- | --- | --- |
| **Choppiness Index** (14) | is the market trending or ranging? | trend signals (MACD, golden cross) only work in *trending* regimes; in chop they whipsaw | high = choppy (distrust trend signals) · low = trending | `choppiness_period=14` |
| **Nadaraya–Watson deviation** (bw 8, lookback 50) | a *kernel-regression* smoother of price; signal = how far price sits from the smoothed path | a statistically-grounded "fair value" band — deviation flags over/under-extension without the lag of moving averages | large +dev = stretched above fair value | `nw_bandwidth=8.0`, `nw_lookback=50` |

### E. Volume & conviction — *is money actually behind the move?*

| Signal | Measures | Why it matters | Knob |
| --- | --- | --- | --- |
| **OBV** (on-balance volume, signal 20) | running sum of volume signed by up/down days | rising price on rising OBV = real accumulation; price up on falling OBV = weak/​distribution | `obv_signal_period=20` |
| **Average volume** (scanner) | mean daily volume | *liquidity* — can you get in/out without moving the price? | `min_average_volume=500000` |

### F. Patterns — *recognisable shapes*
**Swing-based chart patterns** (`pattern_lookback=60`, `pattern_min_swing_pct=2.0`): detects local
highs/lows ("swings") and the structures they form. Lowest-confidence pillar; confirmation only.

### G. Fundamentals — *is the business sound?*
`fundamental_rules.py` gates on per-ticker key metrics (the provider pulls them from Finnhub). The
**fundamental pillar weight is 0.3** — a third of the technical score. (This is the thinnest-explained
layer in the code and a candidate for the same treatment as this doc.)

### H. Sentiment — *what is the news tone?* (champion–challenger, ADR-0002)
- **Loughran–McDonald lexicon** (champion) — a *finance-specific* word list (e.g. "liability" is
  negative in finance, neutral in English). Rule-based, deterministic, defensible.
- **FinBERT** (challenger, advisory) — a transformer fine-tuned on financial text; richer but a
  black box, so it's *advisory* and gated by an information-coefficient comparison before it earns weight.
- Sentiment pillar weight **0.2**.

### I. The ML shadow — the forecaster
- **LightGBM** gradient-boosted trees on no-lookahead price/return features (momentum/volatility
  windows, multi-horizon returns). Runs as a **shadow** — it predicts, we *measure*, it does not decide.
- **Information Coefficient (IC)** = the Pearson correlation between the model's prediction and the
  *realised* forward return. **This is the single most important number for trusting any predictor**:
  IC ≈ 0 means no skill; IC ≥ ~0.03–0.05 on out-of-sample data is a genuine edge. Alpha158 and FinBERT
  only earn weight when their IC beats the incumbent.

### J. Sizing & risk gates — *how much, and is the portfolio still sane?*
| Gate | Measures | Knob |
| --- | --- | --- |
| **Fixed-fraction sizing** | `qty = (portfolio × max_position_pct) // price` — same % of capital regardless of the name's risk | `max_position_pct=0.10` |
| **Reward/risk** | (target − entry) / (entry − stop) must clear a floor | `min_reward_risk_ratio=1.5` |
| **Sector cap / position cap / cash buffer** | concentration + liquidity guards | `max_sector_pct=0.30`, `max_positions=10`, `cash_buffer_pct=0.05` |

---

## How they combine (the part you most need to trust)

The analyst builds a weighted composite:

```
score = technical(0.5) + fundamental(0.3) + sentiment(0.2)      (+ relative-strength inside technical, 0.2;
                                                                   + Alpha158 pillar, weight 0.0 = off)
confidence = floor(0.3) + span(0.6) × normalised score
```

…then the provider's **regime** gates it (the same score must clear a higher bar in risk-off), the
scanner has already filtered for **liquidity / relative-strength / beta / earnings-proximity**, and
the PM applies **sizing + reward-risk + concentration** gates. So a trade is: *survived the funnel →
scored above the confidence floor → cleared the regime gate → passed risk sizing.* **Every one of those
is a number you can now read.**

**The honest weakness:** the combination is a **fixed linear weighting** (0.5/0.3/0.2) with **absolute
thresholds** (RSI 70, etc.). It does not adapt to regime, it does not rank names *against each other*,
and it sizes every position the same regardless of its volatility. That is where confidence is left on
the table — see Parts 2 and 3.

---

## Part 2 — Quant areas we have NOT covered

| Area | What it is | Why it would help | What it needs |
| --- | --- | --- | --- |
| **Volatility modelling** | realised vol, EWMA/GARCH, vol-of-vol | size and stops should scale to *current* volatility, not a fixed % | rolling σ of returns (deterministic) |
| **Position-sizing theory** | Kelly / fractional-Kelly, vol-targeting, risk-parity | fixed-fraction over/under-bets by risk; sizing is the highest-leverage unused lever | per-name vol + edge estimate |
| **Portfolio optimisation** | mean-variance (Markowitz), risk budgeting | accounts for *correlations* — 5 tech names ≠ 5 independent bets | a covariance matrix |
| **Cross-sectional factors** | value / quality / size / low-vol (Fama–French style) | the durable equity premia; complements momentum | fundamentals you already pull, ranked cross-sectionally |
| **Risk-adjusted metrics** | Sharpe, Sortino, max-drawdown, VaR/CVaR | judge a *strategy/position* on return-per-unit-risk, not raw return | a returns series (the monitor/reporter have it) |
| **Regime detection** | beyond VIX bands — HMM / change-point on returns | thresholds should shift with the regime, automatically | a regime classifier over returns |
| **Correlation / breadth** | pairwise correlation, market breadth | concentration risk + "is the whole market participating or just a few names?" | the covariance/breadth computation |
| **Microstructure / liquidity** | spread, depth, slippage modelling | execution quality; `slippage_bps=0` is currently a fiction | quote data (not in the free feeds) |
| **Options / implied vol** | implied vol surface, skew, put/call | forward-looking risk the price series can't see | an options feed |
| **Event studies** | earnings drift, the 4-days-to-earnings risk the demo flagged | the Challenger's best objection was an *uncovered* event-risk factor | an earnings/event model (you have the dates) |

**The standout gap, in plain terms:** the system has a **rich signal layer** (Part 1) but a **thin risk
& portfolio layer**. It is good at *"is this name attractive?"* and weak at *"how much, given its
volatility, my other positions, and the regime?"*

---

## Part 3 — Deterministic parameters to raise prediction confidence

All deterministic (computable from the data we already have — no ML, so they're *champion*-eligible,
not advisory). Ordered by leverage:

1. **Realised volatility (rolling σ of daily returns).** *Measures:* the name's current volatility.
   *Confidence:* lets stops/size scale to reality instead of a flat `stop=5%`. *Adds:* `realized_vol_window`.
2. **Volatility-targeted sizing** (replace fixed-fraction). *Measures:* size so each position contributes
   *equal risk*. *Confidence:* stops one volatile name from dominating P&L. *Adds:* `target_position_vol`.
   **(Highest leverage — Part 2's standout gap.)**
3. **Cross-sectional rank / percentile** of every signal. *Measures:* a name's RSI/momentum *relative to
   the universe today*, not vs a fixed 70. *Confidence:* absolute thresholds are regime-blind; ranks
   self-normalise. *Adds:* `rank_universe` flag per signal.
4. **Correlation-to-book / concentration penalty.** *Measures:* how correlated a new name is to what you
   already hold. *Confidence:* directly answers the Challenger's "you're piling onto overweight tech."
   *Adds:* `max_avg_correlation`.
5. **Regime-conditional thresholds.** *Measures:* the VIX regime *modulates* the confidence floor and
   reward/risk gate (already computed, currently barely used). *Confidence:* tightens the bar exactly
   when it should. *Adds:* per-regime multipliers on `confidence_floor` / `min_reward_risk_ratio`.
6. **Multi-timeframe agreement.** *Measures:* do the daily and weekly signals *agree*? *Confidence:*
   agreement across horizons is a classic confirmation filter. *Adds:* `confirm_timeframes`.
7. **Event-risk gate (deterministic).** *Measures:* days-to-earnings × the name's historical earnings
   gap. *Confidence:* encodes the demo's winning objection as a rule, not a vibe. *Adds:*
   `earnings_gap_lookback` (you already gate on `earnings_exclusion_days`).
8. **Expectancy / Sharpe gating from the ledger.** *Measures:* the *realised* profit-factor/expectancy
   of past trades with this signal profile. *Confidence:* closes the loop — only keep what has paid.
   (This is also the eval the Deliberation/DSPy loop needs.)

---

## Why this matters here

- **Legibility (LAW-05):** a trade is now explainable as *facts + named, interpretable parameters* — no
  black boxes in the rationale. That is the precondition for the operator to trust an automated trade.
- **The Deliberation roles** (`Defender`/`Challenger`/`Judge`) need exactly this grounding to argue a
  decision *on the merits* — Part 3's gaps are precisely the objections a good Challenger should raise.
- **Champion-eligible:** every Part-3 addition is deterministic, so it strengthens the *defensible
  champion* layer rather than adding more advisory ML — the right place to invest first (the signal
  layer is rich; the risk layer is where confidence is currently lost).
