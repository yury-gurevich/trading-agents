# EXP-010 - What does the reward_risk floor reject on the ratio S211 actually built?

**Date:** 2026-09-17 · **Status:** complete. The 1.0 floor was calibrated on a different ratio from the one
S211 builds. On the built ratio it rejects **55-68 %** of names, not the ~21 % it was ruled on. Operator set
the floor to **0.80** (**16-18 %**) · **Feeds:** [ADR-0027](../../decisions/0027-reward-risk-compares-measured-upside-against-measured-downside.md)
*Correction*, [S211](../../sprints/sprint-211-reward-risk-compares-two-measured-quantities.md) (returned
before merge for the floor), work-queue item **60**

## Purpose

ADR-0027 chose the 1.0 floor from a table of **median favourable excursion ÷ median adverse excursion**. Its
decision, and S211's spec, derive the **target** from the median favourable excursion but leave the **stop**
untouched (2 × ATR, clamped). The gate reads `target_pct ÷ stop_pct`, so the ratio that ships is **median
favourable excursion ÷ the ATR-scaled stop**. That's a different denominator. This probe measures what the
floor does on the ratio actually built, before the branch merges.

## Process

- **Code:** S211's branch worktree, uncommitted handback state (the code that would merge). The real
  `score_candidate` and `resolve_stop_target` are called, not a re-implementation.
- **Data:** the `MarketData` snapshot behind each of the last three scheduled `AnalystRun`s
  (`sched-2026-09-14`, `-15`, `-16`), live Neon spine, read-only: **98 names, 202-203 bars each**.
- **Settings:** production mode `scaled` (`orchestration/packs/trading_tunables.json`), branch defaults
  otherwise: horizon 10 sessions, lookback 120 windows, ATR multiplier 2.0.
- **Two ratios per name:**
  - **Built:** `target_pct ÷ stop_pct` as the gate reads it.
  - **ADR:** the same target ÷ the median of `observed_drawdown` over the same 120 prior windows.
- **Population:** every name in the snapshot, not only the scanner's survivors. Candidates are a subset.

## Delivery

- This record, with the script and full output in the appendices. The script needs `.env`, is read-only
  and costs nothing.

### Result 1 - the built ratio sits around 0.95, not 1.35

| Run | Stop median | Target median (old target) | Built ratio p25 / median / p75 | ADR ratio p25 / median / p75 |
| --- | --- | --- | --- | --- |
| sched-2026-09-14 | 4.2 % | 4.2 % (8.4 %) | 0.837 / **0.976** / 1.113 | 0.973 / 1.235 / 1.566 |
| sched-2026-09-15 | 4.3 % | 4.2 % (8.6 %) | 0.829 / **0.957** / 1.088 | 0.969 / 1.236 / 1.580 |
| sched-2026-09-16 | 4.6 % | 4.2 % (9.1 %) | 0.837 / **0.934** / 1.036 | 0.967 / 1.231 / 1.592 |

- The gate genuinely discriminates: **95-98 distinct values** of 98, where production today has one.
- **No name lacked an estimate:** 120 samples each, `target_estimate_unavailable` = 0.

### Result 2 - share of names below each floor

| Floor | Built 09-14 | Built 09-15 | Built 09-16 | ADR ratio (all three) |
| --- | --- | --- | --- | --- |
| 0.70 | 10 % | 11 % | 12 % | 5 % |
| 0.75 | 12 % | 11 % | 16 % | 8-9 % |
| **0.80** | **17 %** | **16 %** | **18 %** | 11-12 % |
| 0.85 | 26 % | 28 % | 29 % | 13-15 % |
| 0.90 | 33 % | 36 % | 41 % | 16-18 % |
| **1.00** | **55 %** | **58 %** | **68 %** | 29-30 % |
| 1.50 | 98 % | 97 % | 97 % | 69-71 % |

## Interpretation

1. **The 1.0 floor as built would reject most of the book.** This is the failure ADR-0027 itself warned about
   ("the threshold and the derivation are calibrated together and must move together"). This time the
   planning agent caused it, by writing a spec whose denominator differed from the one measured.
2. **A floor below 1.0 on this ratio is not looser than the ADR's sentence.** The target is the **median**
   favourable excursion, so by construction half of prior windows reached it. The stop sits beyond the
   typical fall: the median name's stop is about **1.3×** its median adverse excursion (ADR median 1.23 ÷ built
   median 0.95), so fewer than half of windows reach it. The two legs aren't equally likely, which makes
   "target at least equal to stop" a stricter test than "typical upside at least equal to typical downside".
3. **0.80 keeps the filter the operator approved.** It rejects 16-18 % on the built ratio, against the ~21 %
   the 1.0 ruling was based on. Said out loud: *never buy a name whose typical 10-session upside is less than
   four-fifths of the distance to its stop.*
4. **The target halves**, from a median of 8.4-9.1 % to 4.2 %. Nothing exits on it: exit triggers are `stop`
   and `thesis` only (`agents/analyst/domain/recommend.py:26`). So this changes only the gate and what the
   deliberator is shown. Recorded so a later reader doesn't mistake it for an exit-policy change.
5. **The ADR ratio replays at 29-30 % below 1.0, not the ADR's 21 %.** This probe's adverse median uses
   `observed_drawdown` over exactly the 120 windows the estimate uses. The ADR's ~110 windows were computed
   separately. The gap is unexplained and doesn't affect the decision, which is about the built ratio.

**Decision taken:** operator, 2026-09-17: `min_reward_risk_ratio` ships at **0.80**, not 1.0. S211 was
returned before merge for the one-value change. Recorded in ADR-0027 *Correction*.

**Caveats:**

- Three consecutive nights in one market regime. ADR-0027 §3 accepts that the rejection share moves with the
  regime, so this is a calibration point, not a constant.
- The population is the whole 98-name snapshot. The analyst gates buy candidates only, so the nightly share
  among candidates can differ.
- Fundamentals and news were omitted from scoring. They don't feed the stop or the target, so the ratios
  are unaffected.

## Appendix A - replay (`rr_floor_replay.py`)

Run from the S211 worktree so its code is imported, with `<repo>` pointed at the main checkout's `.env`:
`PYTHONPATH=. uv run python rr_floor_replay.py`.

```python
"""EXP-010: the reward_risk ratio S211 builds, replayed on live MarketData (read-only).

Run from the S211 worktree (its code), with the main checkout's .env loaded for the spine:
    PYTHONPATH=. uv run python rr_floor_replay.py
"""
import statistics as st

from dotenv import load_dotenv

load_dotenv(r"<repo>\.env")
from agents.analyst.domain.scoring import score_candidate
from agents.analyst.domain.stop_target import resolve_stop_target
from agents.analyst.domain.stop_target_outcome import observed_drawdown
from agents.analyst.settings import AnalystSettings
from agents.portfolio_manager.poll import _market_and_regime
from contracts.scanner import Candidate
from kernel.graph_env import build_graph_from_env

FLOORS = (0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 1.0, 1.5)
g = build_graph_from_env()
# production runs ANALYST_STOP_TARGET_MODE=scaled (orchestration/packs/trading_tunables.json)
s = AnalystSettings().model_copy(update={"stop_target_mode": "scaled"})
h, lookback = s.stop_target_drawdown_horizon_days, s.stop_target_excursion_lookback_windows
print(f"mode={s.stop_target_mode} horizon={h} lookback={lookback} atr_mult={s.scaled_stop_atr_multiplier}")
runs = sorted(g.list_nodes("AnalystRun"), key=lambda n: str(n.props.get("created_at")))
picked = []
for an in reversed(runs):
    market, regime, run_id = _market_and_regime(g, an)
    if market is not None and run_id.startswith("sched-"):
        picked.insert(0, (market, regime, run_id))
    if len(picked) == 3:
        break
for market, regime, run_id in picked:
    by: dict[str, list] = {}
    for b in market.bars:
        by.setdefault(b.ticker.upper(), []).append(b)
    bench = tuple(by.get("SPY", ()))
    built, adr, stops, targets, samples, unavailable = [], [], [], [], set(), 0
    for t, bars in sorted(by.items()):
        bars = tuple(sorted(bars, key=lambda b: b.bar_date))
        sc = score_candidate(Candidate(ticker=t, rank=1, score=0.5, survived_filters=()), bars, {}, bench, (), s)
        if sc.rejection_reason:
            continue
        p = resolve_stop_target(regime, sc.metrics, s)
        if p is None:
            unavailable += 1
            continue
        built.append(p.target_pct / p.stop_pct)
        stops.append(p.stop_pct)
        targets.append(p.target_pct)
        samples.add(int(sc.metrics["favorable_excursion_sample_count"]))
        # ADR-0027's calibration denominator: median adverse excursion over the same prior windows
        adv = [
            abs(o.drawdown_pct)
            for i in range(max(0, len(bars) - h - lookback), len(bars) - h)
            if (o := observed_drawdown(bars[i : i + h + 1], bars[i].bar_date, h)) is not None
        ]
        if adv and st.median(adv) > 0:
            adr.append(p.target_pct / st.median(adv))
    pct = lambda xs, f: f"{100 * sum(r < f for r in xs) / len(xs):.0f}%"
    q = lambda xs: " / ".join(f"{x:.3f}" for x in (min(xs), *st.quantiles(xs, n=4), max(xs)))
    print(f"\n{run_id}: names={len(by)} scored={len(built)} target_unavailable={unavailable} samples={sorted(samples)}")
    print(f"  stop   min/p25/median/p75/max  {q(stops)}")
    print(f"  target min/p25/median/p75/max  {q(targets)}   (old target = 2 x stop, median {2 * st.median(stops):.3f})")
    print(f"  BUILT  target/stop             {q(built)}   distinct={len({round(r, 4) for r in built})}")
    print(f"  ADR    target/median adverse   {q(adr)}")
    print("  below floor, BUILT:", {f: pct(built, f) for f in FLOORS})
    print("  below floor, ADR:  ", {f: pct(adr, f) for f in FLOORS})
```

## Appendix B - console output (2026-09-17)

```text
mode=scaled horizon=10 lookback=120 atr_mult=2.0

sched-2026-09-14: names=98 scored=98 target_unavailable=0 samples=[120]
  stop   min/p25/median/p75/max  0.025 / 0.037 / 0.042 / 0.052 / 0.080
  target min/p25/median/p75/max  0.018 / 0.035 / 0.042 / 0.052 / 0.127   (old target = 2 x stop, median 0.084)
  BUILT  target/stop             0.568 / 0.837 / 0.976 / 1.113 / 1.607   distinct=98
  ADR    target/median adverse   0.514 / 0.973 / 1.235 / 1.566 / 2.872
  below floor, BUILT: {0.6: '2%', 0.7: '10%', 0.75: '12%', 0.8: '17%', 0.85: '26%', 0.9: '33%', 1.0: '55%', 1.5: '98%'}
  below floor, ADR:   {0.6: '3%', 0.7: '5%', 0.75: '8%', 0.8: '12%', 0.85: '13%', 0.9: '18%', 1.0: '30%', 1.5: '71%'}

sched-2026-09-15: names=98 scored=98 target_unavailable=0 samples=[120]
  stop   min/p25/median/p75/max  0.026 / 0.037 / 0.043 / 0.053 / 0.080
  target min/p25/median/p75/max  0.018 / 0.036 / 0.042 / 0.052 / 0.133   (old target = 2 x stop, median 0.086)
  BUILT  target/stop             0.579 / 0.829 / 0.957 / 1.088 / 1.663   distinct=95
  ADR    target/median adverse   0.514 / 0.969 / 1.236 / 1.580 / 2.891
  below floor, BUILT: {0.6: '3%', 0.7: '11%', 0.75: '11%', 0.8: '16%', 0.85: '28%', 0.9: '36%', 1.0: '58%', 1.5: '97%'}
  below floor, ADR:   {0.6: '3%', 0.7: '5%', 0.75: '9%', 0.8: '12%', 0.85: '14%', 0.9: '17%', 1.0: '30%', 1.5: '71%'}

sched-2026-09-16: names=98 scored=98 target_unavailable=0 samples=[120]
  stop   min/p25/median/p75/max  0.026 / 0.038 / 0.046 / 0.054 / 0.080
  target min/p25/median/p75/max  0.018 / 0.036 / 0.042 / 0.052 / 0.138   (old target = 2 x stop, median 0.091)
  BUILT  target/stop             0.543 / 0.837 / 0.934 / 1.036 / 1.721   distinct=96
  ADR    target/median adverse   0.514 / 0.967 / 1.231 / 1.592 / 2.891
  below floor, BUILT: {0.6: '1%', 0.7: '12%', 0.75: '16%', 0.8: '18%', 0.85: '29%', 0.9: '41%', 1.0: '68%', 1.5: '97%'}
  below floor, ADR:   {0.6: '3%', 0.7: '5%', 0.75: '9%', 0.8: '11%', 0.85: '15%', 0.9: '16%', 1.0: '29%', 1.5: '69%'}
```
