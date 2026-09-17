# EXP-009 - Should position size follow volatility, and does the regime label have anything to scale by?

**Date:** 2026-09-17 · **Status:** complete. Iso-risk sizing does what it promises on risk dispersion, but in
this month it would have lost **$445 more** than today's sizing, almost all of it on one period effect. The
regime classifier has **never received a VIX value in production** · **Feeds:** work-queue items **62** and
**64** ([ADR-0025](../../decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md)
Decision B), new item **70** (regime has no input)

## Purpose

Work-queue items 62 and 64 are "one question" under ADR-0025 Decision B: *volatility should scale position
risk, and a regime label that moves no risk number is not a regime input*. The ruling authorised no
implementation. Its named next step was a champion–challenger measurement, because two concerns were
unresolved:

1. **What would volatility-adjusted sizing actually change?** Today every buy is sized to 1 % of equity in
   dollars (`MAX_POSITION_PCT = 0.01`). A calm stock and a volatile stock get the same dollars, so the same
   dollars carry very different loss-at-stop. The deliberator raises this on nearly every night it debates.
2. **Would two volatility adjustments compound?** The stop is already ATR-scaled (`mode=scaled`, 2 × ATR,
   bounded 3–8 %). Scaling size by that stop again could, in principle, stack the effect invisibly.

For item 64, the question was whether the regime label ever varies, since it doesn't matter what it would
modulate if it never changes.

The decision is a capital-risk policy, so it is the operator's. This probe informs it and moves no dial.

## Process

**Population.** Every approved **buy** on a scheduled run whose sizing gate recorded the equity it used and
whose `Recommendation` recorded ATR stop evidence: **61 orders, 20 runs, 17 tickers,
`sched-2026-08-17` → `sched-2026-09-16`**. Equity ranged $102,005–$102,796. It includes orders the deliberator
later vetoed: this evaluates the sizing *policy* on the PM's decisions, not the trades that happened.

**Validation.** Today's quantity reconstructs as `floor(0.01 × equity ÷ price)` for **61 / 61** orders exactly
(`agents/portfolio_manager/domain/sizing.py:25`).

**Stops.** The recorded `stop_target_scaled_stop_pct` / `scaled_target_pct` for every order: today's policy,
applied uniformly, including the 47 orders that ran under flat stops before S198. Under flat stops every
position already carries identical risk, so there is nothing to compare.

**Arms.**

| Arm | Quantity |
| --- | --- |
| A — fixed 1 % notional (champion) | `floor(0.01 × E ÷ P)` |
| B — iso-risk | `floor(R × E ÷ (P × stop))`, with R = the champion's **mean** planned risk (**0.0552 %** of equity), so the book carries the same total risk and only its distribution changes |
| C — iso-risk, notional capped at 2 % | B, capped at `floor(0.02 × E ÷ P)` |

**Ex-ante:** planned risk per position (`qty × price × stop ÷ equity`) and notional per position.

**Ex-post:** entry at the next session's open after the run's last bar. Exit at the stop (or the open if it
gapped through), the target, or the close after **10 sessions** (`base_max_holding_days`), whichever comes
first. The daily low is checked before the high, so on a day that touches both the stop wins (conservative).
Bars run through 2026-09-16, so 8 recent orders are marked to market before 10 sessions and 4 have no
forward bars. Same exits for every arm; only quantity differs.

**Robustness.** P&L attributed by ticker; a **ticker-cluster bootstrap** (5,000 resamples of the 17 tickers)
because repeated names (AMZN ×8, MDLZ ×6, USB ×6) are not independent.

**Regime.** Every `RegimeContext` for a scheduled run (50 rows, `sched-2026-07-07` → `sched-2026-09-16`), then
every `fetch_regime_inputs` implementation in `agents/provider/`.

## Delivery

- This record; scripts and full output in the appendices. The scripts need `.env` (live Neon spine), are
  read-only and cost nothing.

### Result 1 - ex-ante risk (61 orders)

| Arm | Risk % equity min / median / max | Max ÷ min | CV | Notional % equity min / max | Book risk % | Book notional % |
| --- | --- | --- | --- | --- | --- | --- |
| A champion | 0.0188 / 0.0445 / 0.0789 | **4.21** | 0.29 | 0.50 / 1.00 | 3.02 | 55.1 |
| B iso-risk | 0.0296 / 0.0508 / 0.0551 | **1.86** | 0.15 | 0.37 / 1.66 | 2.91 | 59.0 |
| C iso-risk, 2 % cap | identical to B — the cap never binds (max notional 1.66 %) | | | | | |

- Today's sizing makes the riskiest position carry **4.2×** the planned loss of the calmest. Iso-risk cuts that
  to **1.9×**, not 1.0×, for two measured reasons:
  - **Whole shares.** At about $1,000 a position the median order is 6 shares (range 1–34). Rounding leaves
    achieved risk at **0.54–1.00** of the intended budget (median 0.92).
  - **The 8 % stop cap.** 8 orders (AMD, AVGO, INTC; ATR 4.1–6.8 %) have stops clamped below 2 × ATR, so their
    stop understates their volatility.
- **No compounding at book level.** Total planned risk is unchanged by construction (3.02 % → 2.91 %). Notional
  rises 7 % (55.1 % → 59.0 %) as capital shifts toward calm names (NEE, USB at 1.6 % each).

### Result 2 - ex-post P&L (57 simulated orders)

| Arm | Total P&L | SD per position | Worst position | Best position | Loss per stop-out (19) |
| --- | --- | --- | --- | --- | --- |
| A champion | **−$184** | $49 | −$88 | +$159 | −$19 … −$88 |
| B / C iso-risk | **−$629** | $41 | −$61 | +$115 | −$31 … −$61 |

Exits: time 28, stop 15, stop through a gap 4, target 2, still open 8.

- **Iso-risk delivered its promise:** per-position SD **−17 %**, worst loss **−30 %**, and stop-out losses
  narrowed from a $69 spread to a $30 spread.
- **It lost $445 more.** Ticker-cluster bootstrap 95 % interval for B − A: **[−$1,036, −$14]**; 98 % of
  resamples negative.
- **Attribution: this was the month, not the method.** AMD alone is **−$255** of it (+11.1 % mean return,
  volatile, halved by iso-risk). Calm names fell and got more capital: USB −$104, NEE −$67, MDLZ −$25.
  Stops under 4 % averaged **−2.70 %**; stops of 6 % or more averaged **+1.11 %**. Excluding AMD, the gap is
  −$190. The approved set as a whole returned −0.43 % mean (−2.14 % median) over 10 sessions.

### Result 3 - the regime label has never had an input

- **50 / 50** scheduled `RegimeContext` rows are labelled `neutral`, with **0** label changes and `vix` **absent on
  all 50**. Base parameters are identical on every row (stop 0.05, target 0.10, min confidence 0.60).
- **Cause, read in the code.** `classify_regime` returns `"neutral"` when `inputs.vix is None`
  (`agents/provider/domain/regime.py:20-21`). The composite source delegates regime inputs to the price source
  (`agents/provider/composite.py:44-46`), and **every** production source hard-codes `vix=None`:
  `alpaca_data.py:54`, `tiingo.py:46`, `fmp.py:46`, `stooq.py:42`, `fundamentals.py:73`. The only
  implementation that returns a value is `FakeDataSource` (`sources.py:122`), used by tests and by
  `scripts/run_local.py`'s offline mode (`vix=12.0`).
- **Nothing records the gap.** `_get_regime` adds `regime_source_degraded` only when the fetch *raises*
  (`agents/provider/agent.py:146`); a source that returns nothing produces a clean `neutral`.
- `PROV-OUT-02` is 🟩 on `test_regime_classifier_covers_vix_bands` and
  `test_get_regime_maps_vix_to_policy_and_graph`. Both hand the classifier a VIX value, which no production
  source ever does, so the clause is green on a path production never takes.

## Interpretation

1. **The deliberator's sizing objection is textbook-true but low-stakes at today's book.** Positions risk
   **0.02–0.08 %** of equity each, and the whole book at its stops is **about 3 %**. Iso-risk would move the worst
   single-position loss from $88 to $61 on a $102k account.
2. **Iso-risk sizing did what it claims and would still have cost money this month.** One month, one market
   regime and 17 names can't separate the method from the period. A high-beta rally rewarded exactly the names
   iso-risk halves. The bootstrap interval excludes zero only across *tickers*, not across *time*, and a single
   window is one draw of time. **This is not evidence that volatility sizing is worse. It is evidence that it
   is not free, and that one month cannot settle it.**
3. **The compounding fear is not borne out at book level.** Total planned risk is held constant by
   construction. The effect is a 7 % shift of notional toward calm names, which is visible and bounded.
4. **Implementation limits would blunt any adoption today:**
   - Whole-share rounding leaves positions at 54–100 % of the intended risk.
   - The 8 % stop cap mis-states risk for the most volatile names.
   - A 2 % notional cap would never bind at current settings.
5. **Item 64 is not a policy question yet. It is a data defect.** The regime label cannot scale anything
   because it has never been computed from data. Every night is `neutral` by default. Nothing marks the output
   degraded, and the clause's green tests run on a source production doesn't use: the DRIFT-058 shape (a check
   that cannot fail), found in the provider.

**Decision taken:** none. Sizing policy is capital-risk (ADR-only).

**What it feeds:**

- **New work-queue item 70** — the regime classifier has no production input and says nothing about it. A fix
  outranks the policy question: until VIX (or another measured input) arrives, "should regime scale risk" has
  nothing to scale by.
- **Items 62/64** — ADR-0025 Decision B's direction stands, but this evidence argues against adopting iso-risk
  sizing now. Re-measure over a longer window, ideally one containing a down-leg, before an ADR. Record the
  whole-share and stop-cap limits as preconditions in any future sizing ADR.
- **The deliberator's sizing ground** is true, cheap in dollars, and not something a sizing change would remove
  without cost. That is useful context when reading its vetoes.

**Caveats:**

- Hypothetical fills at the next open for every approved buy, including vetoed and unfilled ones. Limit-order
  non-fills and slippage beyond the gap rule are not modelled.
- One 10-session horizon; the last 12 orders have short or no forward windows.
- The iso-risk budget is calibrated on the same population it is evaluated on. That only fixes the *level* of
  risk, not which names win, so it cannot manufacture the P&L result.

## Appendix A - loader (`sizing_load.py`)

Run from the repo root with `.env` present: `PYTHONPATH=. uv run python sizing_load.py`, then
`uv run python sizing_replay.py`.

```python
"""Load approved buys + sizing inputs + stop evidence + forward bars + regime history; pickle."""
import pickle
import re
from dotenv import load_dotenv

load_dotenv(r"<repo>\.env")
from kernel.graph_env import build_graph_from_env  # noqa: E402
from agents.portfolio_manager.poll import _market_and_regime  # noqa: E402

OUT = r"<scratch-dir>\sizing_data.pkl"
g = build_graph_from_env()
orders = []
latest_bars = None
latest_created = ""
for pm in sorted(g.list_nodes("PMRun"), key=lambda n: str(n.props.get("created_at"))):
    ois = pm.props.get("order_intent_set") or {}
    buys = [i for i in (ois.get("approved") or ()) if i.get("action") == "buy"]
    if not buys:
        continue
    an_id = ois.get("source_analyst_run_id") or pm.props.get("source_analyst_run_id")
    an = g.get_node("AnalystRun", an_id)
    if an is None:
        continue
    market, regime, run_id = _market_and_regime(g, an)
    if market is None or not str(run_id).startswith("sched-"):
        continue
    as_of = max(b.bar_date for b in market.bars)
    for it in buys:
        gates = {x.get("name"): dict(x) for x in (it.get("gate_report") or ())}
        sz = gates.get("sizing", {})
        m = re.search(r"portfolio_value_usd=([\d.]+)", str(sz.get("detail", "")))
        rec = g.get_node("Recommendation", f"{an_id}:{it['ticker']}")
        rp = rec.props if rec is not None else {}
        orders.append(dict(
            run=run_id, as_of=as_of, created=str(pm.props.get("created_at")), ticker=it["ticker"],
            qty=int(it["quantity"]), price=float(it["est_price"]["amount"]),
            stop_pct=it.get("stop_pct"), target_pct=it.get("target_pct"), atr_intent=it.get("decision_atr_pct"),
            equity=float(m.group(1)) if m else None, sizing_value=sz.get("value"), sizing_detail=str(sz.get("detail", ""))[:300],
            mode=rp.get("stop_target_mode"), atr_pct=rp.get("stop_target_atr_pct"),
            scaled_stop=rp.get("stop_target_scaled_stop_pct"), scaled_target=rp.get("stop_target_scaled_target_pct"),
            flat_stop=rp.get("stop_target_flat_stop_pct"), flat_target=rp.get("stop_target_flat_target_pct"),
            applied_stop=rp.get("stop_target_applied_stop_pct"), applied_target=rp.get("stop_target_applied_target_pct"),
            regime=getattr(regime, "label", None), vix=getattr(regime, "vix", None),
        ))
    if str(pm.props.get("created_at")) > latest_created:
        latest_created = str(pm.props.get("created_at"))
        latest_bars = [(b.ticker.upper(), b.bar_date, b.open, b.high, b.low, b.close) for b in market.bars]

regimes = []
for n in g.list_nodes("RegimeContext"):
    snap = n.props.get("snapshot") or {}
    rid = n.key.replace("regime-context:", "")
    if rid.startswith("sched-"):
        regimes.append((rid, snap.get("label"), snap.get("vix"), snap.get("base_stop_loss_pct"), snap.get("base_take_profit_pct"), snap.get("base_min_confidence")))
pickle.dump(dict(orders=orders, bars=latest_bars, regimes=sorted(regimes)), open(OUT, "wb"))
print("orders", len(orders), "runs", len({o["run"] for o in orders}), "bars", len(latest_bars or []), "regimes", len(regimes))
print("with scaled evidence", sum(o["scaled_stop"] is not None for o in orders), "with equity", sum(o["equity"] is not None for o in orders))
print("first/last run", orders[0]["run"], orders[-1]["run"])
```

## Appendix B - replay (`sizing_replay.py`)

```python
"""Champion (fixed 1% notional) vs volatility-adjusted (iso-risk) sizing, ex-ante and ex-post."""
import json
import math
import pickle
import statistics as st
from collections import Counter, defaultdict

S = r"<scratch-dir>"
d = pickle.load(open(S + r"\sizing_data.pkl", "rb"))
H = 10  # holding horizon in sessions (base_max_holding_days is 10 in every regime row)
CAP = 0.01

pop = [o for o in d["orders"] if o["scaled_stop"] is not None and o["equity"] is not None]
assert all(math.floor(CAP * o["equity"] / o["price"]) == o["qty"] for o in pop)

# iso-risk budget: the champion's mean planned risk per position under today's (scaled) stops
R = st.mean(CAP * o["scaled_stop"] for o in pop)


def qty(o, arm):
    E, P, s = o["equity"], o["price"], o["scaled_stop"]
    if arm == "A fixed 1% notional (champion)":
        return math.floor(CAP * E / P)
    q = math.floor(R * E / (P * s))
    if arm == "C iso-risk, notional cap 2%":
        q = min(q, math.floor(0.02 * E / P))
    return q


ARMS = ["A fixed 1% notional (champion)", "B iso-risk, uncapped", "C iso-risk, notional cap 2%"]

bars = defaultdict(list)
for t, day, op, hi, lo, cl in d["bars"]:
    bars[t].append((day, op, hi, lo, cl))
for t in bars:
    bars[t].sort()
last_day = max(b[0] for bs in bars.values() for b in bs)


def simulate(o):
    series = [b for b in bars.get(o["ticker"].upper(), []) if b[0] > o["as_of"]]
    if not series:
        return None
    entry = series[0][1]
    s, tp = o["scaled_stop"], o["scaled_target"]
    stop, target = entry * (1 - s), entry * (1 + tp)
    for i, (day, op, hi, lo, cl) in enumerate(series[:H]):
        if i > 0 and op <= stop:
            return entry, op, "stop (gap)", i + 1
        if lo <= stop:
            return entry, stop, "stop", i + 1
        if i > 0 and op >= target:
            return entry, op, "target (gap)", i + 1
        if hi >= target:
            return entry, target, "target", i + 1
    n = min(len(series), H)
    reason = "time" if len(series) >= H else "still open (marked)"
    return entry, series[n - 1][4], reason, n


out = {"R_budget_pct_equity": R * 100, "n_orders": len(pop), "runs": len({o["run"] for o in pop}),
       "first_run": pop[0]["run"], "last_run": pop[-1]["run"], "bars_through": str(last_day), "arms": {}}
rows = []
for o in pop:
    sim = simulate(o)
    rows.append((o, sim))

print(f"population: {len(pop)} approved buys, {out['runs']} scheduled runs, {pop[0]['run']} -> {pop[-1]['run']}; sizing reconstruction 61/61 exact")
print(f"iso-risk budget R = {R*100:.4f}% of equity per position (= champion mean planned risk)")
print(f"stops: scaled (2x ATR, bounded 3-8%) for every order; horizon {H} sessions; bars through {last_day}")
print(f"exit reasons: {Counter(sim[2] for _, sim in rows if sim)}; no forward bars: {sum(sim is None for _, sim in rows)}")
print()
print(f"{'arm':34s} {'risk%eq min/med/max':>24s} {'max/min':>8s} {'CV':>5s} {'notional%eq min/max':>20s} {'sum risk%':>9s} {'sum notl%':>9s}")
for arm in ARMS:
    risk, notl = [], []
    for o in pop:
        q = qty(o, arm)
        risk.append(q * o["price"] * o["scaled_stop"] / o["equity"] * 100)
        notl.append(q * o["price"] / o["equity"] * 100)
    rs = sorted(risk)
    cv = st.pstdev(risk) / st.mean(risk)
    print(f"{arm:34s} {rs[0]:7.4f}/{st.median(rs):7.4f}/{rs[-1]:7.4f} {rs[-1]/rs[0]:8.2f} {cv:5.2f} {min(notl):8.3f}/{max(notl):8.3f} {sum(risk):9.3f} {sum(notl):9.2f}")
    pnl, pnl_stop, per_risk = [], [], []
    for o, sim in rows:
        if sim is None:
            continue
        entry, exitp, reason, n = sim
        q = qty(o, arm)
        p = q * (exitp - entry)
        pnl.append(p)
        if reason.startswith("stop"):
            pnl_stop.append(p)
    out["arms"][arm] = dict(risk_min=rs[0], risk_med=st.median(rs), risk_max=rs[-1], risk_ratio=rs[-1] / rs[0], risk_cv=cv,
                            notional_min=min(notl), notional_max=max(notl), sum_risk=sum(risk), sum_notional=sum(notl),
                            pnl_total=sum(pnl), pnl_sd=st.pstdev(pnl), pnl_worst=min(pnl), pnl_best=max(pnl),
                            stop_losses=pnl_stop, n_sim=len(pnl))
print()
print(f"{'arm':34s} {'total P&L $':>11s} {'sd/position $':>13s} {'worst $':>9s} {'best $':>8s} {'stop-outs: n, min..max loss $':>32s}")
for arm in ARMS:
    a = out["arms"][arm]
    sl = a["stop_losses"]
    rng = f"{len(sl)}, {min(sl):.0f}..{max(sl):.0f}" if sl else "0"
    print(f"{arm:34s} {a['pnl_total']:11.2f} {a['pnl_sd']:13.2f} {a['pnl_worst']:9.2f} {a['pnl_best']:8.2f} {rng:>32s}")

# per-order detail for the page
detail = []
for o, sim in rows:
    r = dict(run=o["run"], ticker=o["ticker"], price=o["price"], equity=o["equity"], atr=o["atr_pct"], stop=o["scaled_stop"], target=o["scaled_target"],
             qA=qty(o, ARMS[0]), qB=qty(o, ARMS[1]), qC=qty(o, ARMS[2]))
    if sim:
        r.update(entry=sim[0], exit=sim[1], reason=sim[2], sessions=sim[3])
    detail.append(r)
out["orders"] = detail
out["regimes"] = [dict(run=x[0], label=x[1], vix=x[2]) for x in d["regimes"]]
json.dump(out, open(S + r"\sizing_results.json", "w"), indent=1, default=str)

# top risk under champion vs iso-risk
print()
print("largest planned-risk positions under the champion (ticker, run, ATR%, stop, risk%eq A -> C):")
for o in sorted(pop, key=lambda o: -o["scaled_stop"])[:5]:
    ra = qty(o, ARMS[0]) * o["price"] * o["scaled_stop"] / o["equity"] * 100
    rc = qty(o, ARMS[2]) * o["price"] * o["scaled_stop"] / o["equity"] * 100
    print(f"  {o['ticker']:5s} {o['run'][6:]} ATR {o['atr_pct']:.2f}% stop {o['scaled_stop']*100:.2f}%  {ra:.4f} -> {rc:.4f}")
print("smallest (calmest):")
for o in sorted(pop, key=lambda o: o["scaled_stop"])[:5]:
    ra = qty(o, ARMS[0]) * o["price"] * o["scaled_stop"] / o["equity"] * 100
    rc = qty(o, ARMS[2]) * o["price"] * o["scaled_stop"] / o["equity"] * 100
    nc = qty(o, ARMS[2]) * o["price"] / o["equity"] * 100
    print(f"  {o['ticker']:5s} {o['run'][6:]} ATR {o['atr_pct']:.2f}% stop {o['scaled_stop']*100:.2f}%  {ra:.4f} -> {rc:.4f} (notional {nc:.2f}%)")
print("distinct tickers:", len({o['ticker'] for o in pop}), Counter(o['ticker'] for o in pop).most_common(6))
```

## Appendix C - console output (2026-09-17)

```text
population: 61 approved buys, 20 scheduled runs, sched-2026-08-17 -> sched-2026-09-16; sizing reconstruction 61/61 exact
iso-risk budget R = 0.0552% of equity per position (= champion mean planned risk)
stops: scaled (2x ATR, bounded 3-8%) for every order; horizon 10 sessions; bars through 2026-09-16
exit reasons: Counter({'time': 28, 'stop': 15, 'still open (marked)': 8, 'stop (gap)': 4, 'target': 2}); no forward bars: 4

arm                                     risk%eq min/med/max  max/min    CV  notional%eq min/max sum risk% sum notl%
A fixed 1% notional (champion)      0.0188/ 0.0445/ 0.0789     4.21  0.29    0.501/   0.999     3.015     55.11
B iso-risk, uncapped                0.0296/ 0.0508/ 0.0551     1.86  0.15    0.370/   1.655     2.910     59.01
C iso-risk, notional cap 2%         0.0296/ 0.0508/ 0.0551     1.86  0.15    0.370/   1.655     2.910     59.01

arm                                total P&L $ sd/position $   worst $   best $    stop-outs: n, min..max loss $
A fixed 1% notional (champion)         -184.18         48.99    -87.50   158.58                     19, -88..-19
B iso-risk, uncapped                   -629.47         40.83    -61.25   115.33                     19, -61..-31
C iso-risk, notional cap 2%            -629.47         40.83    -61.25   115.33                     19, -61..-31

largest planned-risk positions under the champion (ticker, run, ATR%, stop, risk%eq A -> C):
  AVGO  2026-08-17 ATR 4.11% stop 8.00%  0.0612 -> 0.0306
  AVGO  2026-08-18 ATR 4.22% stop 8.00%  0.0592 -> 0.0296
  INTC  2026-08-19 ATR 6.84% stop 8.00%  0.0753 -> 0.0527
  INTC  2026-08-20 ATR 6.40% stop 8.00%  0.0789 -> 0.0502
  INTC  2026-08-24 ATR 6.05% stop 8.00%  0.0747 -> 0.0543
smallest (calmest):
  NEE   2026-08-20 ATR 1.64% stop 3.28%  0.0326 -> 0.0544 (notional 1.66%)
  USB   2026-09-01 ATR 1.67% stop 3.34%  0.0320 -> 0.0540 (notional 1.62%)
  NEE   2026-08-19 ATR 1.69% stop 3.37%  0.0312 -> 0.0538 (notional 1.60%)
  USB   2026-09-04 ATR 1.71% stop 3.42%  0.0339 -> 0.0551 (notional 1.61%)
  USB   2026-09-08 ATR 1.72% stop 3.43%  0.0336 -> 0.0546 (notional 1.59%)
distinct tickers: 17 [('AMZN', 8), ('MDLZ', 6), ('USB', 6), ('XOM', 5), ('GOOG', 5), ('AMD', 5)]
```

## Appendix D - attribution and bootstrap output (2026-09-17)

```text
ticker  n   stop%   mean ret   P&L A    P&L B    B-A
AMD     5   7.61   +11.05%     510.8    255.4   -255.4
USB     5   3.43    -3.47%    -174.1   -278.2   -104.1
NEE     3   3.28    -3.41%     -99.8   -167.2    -67.4
MDLZ    5   3.59    -1.17%     -57.5    -82.1    -24.6
WFC     2   4.54    -3.39%     -67.1    -86.8    -19.7
MSFT    1   3.74    -3.74%     -19.1    -38.2    -19.1
XOM     5   4.35    -2.94%    -148.7   -165.8    -17.1
INTC    3   8.00    +2.03%      61.8     48.2    -13.6
MO      2   5.92    +6.56%     128.4    119.8     -8.6
DOW     2   6.70    +1.71%      34.3     27.5     -6.8
GOOGL   3   6.18    -1.78%     -36.5    -36.5     +0.0
WMT     1   5.42    +0.42%       4.0      4.0     +0.0
AMZN    7   4.70    -1.29%     -72.9    -67.3     +5.5
CSCO    3   6.99    -1.84%     -55.6    -41.9    +13.7
C       1   4.31    +4.78%      44.0     62.8    +18.8
GOOG    5   4.46    -1.55%     -79.1    -58.8    +20.3
AVGO    4   6.18    -5.27%    -157.2   -124.4    +32.7
calm (stop<4%): n 13 mean ret -2.70% | volatile (stop>=6%): n 24 mean ret +1.11%
total B-A -445.3; ticker-cluster bootstrap 95% CI [-1035.6, -14.0]; resamples with B-A<0: 98%
B-A excluding AMD: -189.9
mean 10-session return of approved buys: -0.43%, median -2.14%
```
