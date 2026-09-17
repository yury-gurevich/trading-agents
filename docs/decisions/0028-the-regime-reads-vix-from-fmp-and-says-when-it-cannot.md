---
type: Architecture Decision
status: accepted
closes: "The regime classifier has never received a VIX value in production: every live source hard-codes vix=None, classify_regime maps None to neutral, and nothing marks the regime degraded, so all 50 scheduled runs were a silent neutral. Where does VIX come from, and what must the regime say when it cannot get one?"
tags: [provider, regime, vix, data-feed, fmp, fred, cboe, degraded, prov-out-02, prov-out-03, adr-0006, dl-36, drift-058]
amends: ADR-0006
---

# ADR 0028 — The regime reads VIX from FMP, and says so when it cannot

**Status:** Accepted · **Date:** 2026-09-17 · **Decider:** planning agent, under operator delegation
(*"I have no idea. investigate if you have to. make your best decision"*, 2026-09-17)

## Context

[EXP-009](../research/experiments/EXP-009-volatility-sizing-replay.md) found that the provider's regime label
has never been computed from data (work-queue item **70**):

- **50 / 50** scheduled `RegimeContext` rows (`sched-2026-07-07` → `sched-2026-09-16`) are `neutral`, with
  **0** label changes and `vix` absent on every one.
- `classify_regime` returns `"neutral"` when `inputs.vix is None` (`agents/provider/domain/regime.py:20-21`).
- `CompositeSource.fetch_regime_inputs` delegates to the **price** source (`agents/provider/composite.py:44-46`),
  and **every** production source hard-codes `vix=None`: `alpaca_data.py:54`, `tiingo.py:46`, `fmp.py:46`,
  `stooq.py:42`, `fundamentals.py:73`. Only `FakeDataSource` (`sources.py:122`, tests and `run_local.py`)
  returns a value.
- `_get_regime` marks `regime_source_degraded` only when the fetch **raises** (`agents/provider/agent.py:146`).
  A source that returns nothing yields a clean, confident `neutral`.
- `PROV-OUT-02` is 🟩 on tests that hand the classifier a VIX value production never supplies. This is the
  DRIFT-058 shape (a check that cannot fail), and `PROV-OUT-03` promises a total output space that includes
  DEGRADED.

Two questions follow: **where VIX comes from**, and **what the regime says when it can't get it**.

### Who reads the label today — the blast radius

Measured by searching every non-test module: **no risk number reads the label.** `base_min_confidence`,
`base_stop_loss_pct` and `base_take_profit_pct` come straight from settings regardless of the label
(work-queue item 64). The label reaches three places:

- the analyst's summary text (`agents/analyst/result.py:78,85`, `domain/recommend_summary.py:30`)
- the deliberator's prompt, which today reads `vix_index=None` (`agents/deliberator/context_pm.py:63`)
- the operator trace (`orchestration/batch_trace.py:78`)

**Supplying VIX changes no order.** It changes what the label says, what the deliberator is told, and whether
item 64's policy question has anything to act on.

## Evidence — measured 2026-09-17

**Every candidate, probed live** (read-only GETs with credentials already in `.env`; nothing printed):

| Source | Result | Freshness |
| --- | --- | --- |
| **FMP** `stable/historical-price-eod/light?symbol=^VIX` and `stable/quote?symbol=^VIX` | ✅ 200, daily history + quote | 2026-09-16 close present at 03:58 UTC on 09-17 |
| **FRED** `VIXCLS` | ✅ 200 | **one session behind**: at 03:58 UTC on 09-17 the latest observation was 09-15 (`last_updated 2026-09-16 08:38 -05`) |
| **Cboe** `cdn.cboe.com/.../VIX_History.csv` (no key) | ✅ 200, 9,275 rows since 1990 | 09-16 present |
| **Finnhub** `quote?symbol=^VIX` | ❌ *"Market data subscription required for CFD indices"* | — |
| **Alpha Vantage** `TIME_SERIES_DAILY&symbol=VIX` | ❌ *"Invalid API call"* | — |
| **Tiingo** `daily/VIX/prices` | ❌ 404 *"Ticker 'VIX' not found"* | — |

**The three working sources agree exactly:** 74 common days (2026-06-01 → 2026-09-16), maximum
|FMP − FRED| = **0.000**, maximum |FMP − Cboe| = **0.000**.

**FMP is already trusted by the provider:** `fmp-api-key → PROVIDER_FMP_API_KEY` is in the provider's
entitlements (`orchestration/packs/trading_secrets.json`), and the `fmp` probe in
`orchestration/packs/trading_credential_tests.json` tests it before handover (DL-36). No new secret, grant,
vendor or cost.

**What the label would have been.** Using FMP closes on each scheduled run's as-of date with the live
thresholds (risk_on ≤ 15, risk_off ≥ 20, high ≥ 25, extreme ≥ 35): **49 / 49** real run dates have a value.
The one run without one, `sched-2026-07-13-resume-monitor`, is a resume id, not a date. The labels would have
been `neutral` 38, **`risk_on` 10, `risk_off` 1**, with **12 label changes**, against today's 0. VIX ranged
14.25 – 20.66.

## Decision

1. **Source: FMP's `^VIX` daily series is the regime's VIX input.** The provider's regime fetch reads the
   end-of-day bar for the run's as-of session from `stable/historical-price-eod/light?symbol=^VIX` through the
   existing FMP credential. Regime inputs stop being delegated to the price source.
2. **Freshness rule: prefer the as-of session, tolerate one session, refuse older.**
   - A bar dated the as-of session → used, recorded with its date (`vix_as_of`).
   - Newest bar is the **previous** session → used and recorded with its date, plus a **warning-severity**
     note that it is prior-session. The label is still computed.
   - No bar, a bar older than the previous session, a non-numeric value, or a fetch failure → **the regime is
     DEGRADED**: incident ref and fault recorded, `vix` absent, label `neutral`, and the output **says why**.
     A missing input never again produces a clean `neutral`.
3. **The honesty half is a law change.** `PROV-OUT-02` / `PROV-OUT-03` must require that a regime without a
   measured input is reported degraded, with a test on a source that returns *nothing* (not one that raises),
   so the clause can fail. This is owed as a law cycle in the implementing sprint.
4. **No fallback source in the first build.** One vendor serving one number nightly doesn't justify a second
   grant yet. The degraded path makes an outage *visible*, which is what was missing.
5. **Thresholds unchanged** (15 / 20 / 25 / 35 VIX points). They were calibrated in VIX points, and the input
   is now actual VIX points.
6. **This decides nothing about item 64.** Whether the label should move stops, confidence floors or sizing
   remains ADR-0025 Decision B's open question. This ADR only makes the label real so that question has
   something to act on.

## Consequences

- **The deliberator sees a real `vix_index`** and a label that varies (measured: non-neutral on 11 of 49
  nights). Its arguments may cite it. That is intended, and it is the only behavioural change.
- **Deploy is an image rebuild**, not a secret change. Whether it needs a full `up` depends on whether the build
  adds a vocabulary property (e.g. `vix_as_of`); the implementing sprint states it.
- **FMP becomes load-bearing for the regime.** An FMP outage now shows as a degraded regime every night it
  lasts, instead of hiding as `neutral`.
- **ADR-0006 is amended:** FMP's role grows from "validation" to "validation + regime VIX".

### Assumed, not measured — the implementing sprint must prove it live

- **That FMP's as-of bar exists at the 22:30 UTC run.** It was present by 03:58 UTC the next day. Whether it's
  there two hours after the 20:15 UTC VIX close is **unmeasured**. The freshness rule (decision 2) tolerates a
  one-session lag, so the design doesn't depend on the answer, but the first scheduled run after deploy must
  record which case occurred.

## Rejected alternatives

- **FRED `VIXCLS` as the source.** Rejected as primary: at run time it is **always one session behind**
  (measured). It would need a new grant (`PROVIDER_FRED_API_KEY` exists but only `scripts/test-api-keys.ps1`
  uses it). **Kept as the named fallback** if FMP proves unreliable.
- **Cboe's public CSV.** Rejected as a runtime source: an undocumented CDN path with no published terms or
  stability promise, so its failure mode is silent breakage. **Kept as a validation oracle**: it agreed with FMP
  to the cent on 74 days.
- **Finnhub, Alpha Vantage, Tiingo.** Rejected: measured, none serves VIX on our plans.
- **A proxy: VIXY (via Alpaca) or realised volatility computed from our own bars.** Rejected: the thresholds are
  in VIX points. VIXY is a futures ETF with roll decay, not the index level, and realised volatility is a
  different quantity (backward-looking, typically below implied). Either would silently change what
  `risk_on` / `risk_off` mean. Adopting one would need its own thresholds and its own ADR.
- **Keep `neutral` but mark it degraded, with no source.** Rejected: it fixes the honesty defect but leaves the
  label permanently useless, and a free, already-granted, validated source exists.
- **Compute VIX locally from SPX options.** Rejected: needs an options chain feed we don't have, to reproduce a
  number three sources already publish identically.
