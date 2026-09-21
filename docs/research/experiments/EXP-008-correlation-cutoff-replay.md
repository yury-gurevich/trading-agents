# EXP-008 - Does the 0.70 correlation cutoff decide anything, and is it noise?

**Date:** 2026-09-17 · **Status:** complete - no cutoff between 0.50 and 0.70 changes a single approval at
today's book, and the verdict near 0.70 is sampling noise, not outlier days · **Feeds:** work-queue item
**68**, [ADR-0025](../../decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md)
(concentration family), the deliberator's recurring `correlated_cluster_pct` objection

## Purpose

`PORTFOLIO_MANAGER_CORRELATION_THRESHOLD = 0.70` is a **binary inclusion test**. A held issuer whose pairwise
close-return correlation with the candidate is at or above 0.70 joins the cluster at full value. Below that,
it contributes nothing. Since 2026-09-14 the deliberator has led buy vetoes with this ground: *"a binary >0.70
inclusion test that discards MSFT 0.4607/DIS/NFLX entirely rather than haircutting co-movement"* (AMZN,
`sched-2026-09-16`).

The operator raised two questions:

1. **Does the cutoff decide anything?** If it were lower, or weighted rather than binary, would any past
   approval have been rejected? If not, retuning it cannot lift a veto.
2. **Does a high cutoff shield us from noise?** The hypothesis: a high bar stops volatile or unusual samples
   from inflating correlations and wrongly rejecting candidates. If noise dominates instead, the binary line
   may amplify it rather than filter it.

This matters because the correlation threshold is a risk cap. The
[experimentation charter](../../../ops/departments/experimentation/charter.md) (OUT-2) makes a risk cap
**ADR-only**, never a tuning-loop move. This probe informs that decision; it moves no dial.

## Process

**Population.** Every scheduled `PMRun` with at least one approved order carrying a `correlated_cluster_pct`
gate outcome: **17 runs, 38 orders**, `sched-2026-08-20` to `sched-2026-09-16`. Gate outcomes were first
recorded on 2026-08-20. Three `verify-*` runs were loaded and excluded. The correlation gate runs **last** in
`agents/portfolio_manager/domain/order_decision.py`, so a variant cannot change any other gate's verdict on
the same order.

**Inputs, read-only from the live spine:**

- **Bars:** the run's own `MarketData` snapshot, found through the same `AnalystRun ← ScanRun → MarketData`
  walk the PM uses (`agents/portfolio_manager/poll.py::_market_and_regime`).
- **Holdings:** the run's `BrokerPositionSnapshot` (`market_value_cents` per ticker). The PM reads *current*
  graph `Position` nodes, which are not historical, so broker holdings at run start are the faithful
  reconstruction.
- **Issuers:** `orchestration/packs/trading_issuer_map.json` through `issuer_key`.
- **Settings:** the live pack. Lookback 120 days, `min_correlation_bars` 60, cap 0.25.

**Replay.** A pure-Python re-implementation of `correlation_math.py` (close-to-close returns, Pearson over
overlapping days) and of `correlation.py` / `correlation_census.py`: best correlation across an issuer's
tickers, pairs under 60 bars skipped, cluster value = cost + own issuer + clustered issuers. Orders are
processed in approval order. An order's cost joins the book only if it passes under that variant, so the
in-batch interaction is kept.

**Validation (the condition for trusting the replay).** At 0.70 the replay must reproduce what the fleet
recorded.

**Variants.** All use the **deployed-capital denominator** (current policy since S210), applied to every run:

| Variant | Weight given to a held issuer with correlation ρ |
| --- | --- |
| binary 0.70 (champion) | 1 if ρ ≥ 0.70, else 0 |
| binary 0.65 / 0.60 / 0.50 | 1 if ρ ≥ cutoff, else 0 |
| ramp 0.5→0.9 | 0 below 0.5, rising linearly to 1 at 0.9 |
| weighted ρ⁺ | max(ρ, 0): every positive correlation counts in proportion |

**Noise checks** ran on every candidate→held pair observed with 0.50 ≤ ρ < 0.90 (16 pairs, latest run per
pair):

- Fisher-z 95 % interval (n = overlapping days, 82–83).
- **Split-half:** ρ on the first half of the overlap window vs the second half.
- **Shock-day removal:** ρ with the 5 days of largest mean absolute return across the whole universe
  removed. This tests the "unusual samples" hypothesis directly.
- **Spearman** rank correlation, which is robust to outliers.

## Delivery

- This record. The two scripts and the full console output are in the appendices. The scripts need `.env`
  (live Neon spine) and cost nothing: no LLM calls, no broker calls.
- A visual summary (private claude.ai artifact) published 2026-09-17.

### Validation

**38 / 38** cluster memberships identical to the recorded `cluster_issuers`, and **38 / 38** cluster values
within 5 % of the recorded `cluster_value_usd`.

### Result 1 - rejections by variant (38 orders, cap 0.25)

| Variant | Rejected | Median ratio | Max ratio | Mean issuers clustered |
| --- | --- | --- | --- | --- |
| binary 0.70 (champion) | **0** | 0.051 | 0.102 | 0.45 |
| binary 0.65 | **0** | 0.072 | 0.148 | 0.58 |
| binary 0.60 | **0** | 0.082 | 0.152 | 0.95 |
| binary 0.50 | **0** | 0.085 | 0.206 | 1.29 |
| ramp 0.5→0.9 | **0** | 0.066 | 0.098 | 1.29 |
| weighted ρ⁺ | **5** (all MDLZ) | 0.159 | 0.300 | 14.47 |

Weighted ρ⁺ rejects MDLZ on every night it was approved: 08-24 (0.278), 09-11 (0.262), 09-14 (0.280),
09-15 (0.289), 09-16 (0.300).

### Result 2 - noise on the 16 near-threshold pairs

| Check | Pairs whose side of 0.70 is not stable |
| --- | --- |
| 95 % interval spans 0.70 | **12 / 16** |
| First and second half disagree about 0.70 | **7 / 16** |
| Dropping the 5 biggest market days flips 0.70 | **2 / 16** (mean Δρ **+0.001**) |
| Spearman flips 0.70 | **3 / 16** |

Last night's decisive pairs:

- WFC–USB: **0.717** [0.59, 0.81], halves 0.772 / 0.638, **counted**.
- WFC–C: **0.679** [0.54, 0.78], halves 0.637 / 0.736, **not counted**.
- MDLZ–KO 0.640, MDLZ–KHC 0.610, MDLZ–MO 0.581: all **not counted**.

## Interpretation

1. **The cutoff decides nothing at today's book.** Positions are about $1,000 each against $19.6k–26.9k
   deployed, so a cluster needs roughly five issuers before it reaches 25 %. Lowering the line all the way
   to 0.50 raises the worst ratio from 0.10 to 0.21 and rejects nothing. **Retuning the cutoff cannot lift a
   single veto.** The deliberator's objection is about what the gate *means*; it is not a lever that
   changes what trades.
2. **The shield hypothesis is half right.** A high bar does demand strong evidence. But the estimate itself
   is the problem. With 82 days, 12 of 16 near-line pairs have intervals spanning 0.70, and 7 of 16 fall on
   opposite sides of it depending on which half of the window you read. **Near the line, counted vs not
   counted is a coin flip.** The binary cliff turns ordinary sampling error into an all-or-nothing verdict,
   and moving the cliff only moves the coin flip.
3. **Unusual days are not the driver (measured, not assumed).** Removing the five largest market-wide days
   changes the mean correlation by +0.001 and flips 2 of 16 pairs. Outlier-robust estimation would not fix
   this. The noise is ordinary sampling variance plus drift across the window.
4. **Weighted ρ⁺ is a different gate, not a better setting.** When every positive correlation counts, the
   average candidate "clusters" with about 14 issuers, so the ratio mostly measures co-movement with the
   whole book. It would reject MDLZ every night: a staples name in a staples-heavy book (KO, KHC, MO, WMT held on 09-16).
   That may be a legitimate policy, but it is a new question, not a tuning of this one.
5. **By construction (reasoned, not measured here), the ramp is the least noise-sensitive shape that keeps the gate's meaning.** Near 0.70 a pair
   contributes about half its value, so a sampling error of ±0.1 moves the verdict smoothly instead of
   flipping it. At today's book it rejects nothing, same as the champion.

**Decision taken:** none. The threshold is a risk cap (charter OUT-2: ADR only).

**What it feeds:**

- Work-queue item 68 changes from "one measurement, then an ADR" to "an ADR about gate meaning (binary,
  ramp or weighted), not urgent". No cutoff tested changes what trades.
- If a shape change is taken, the case for ramp over binary rests on result 2, not result 1.
- The deliberator's correlation ground is **true but inert**: vetoes citing it are not caused by a gate we
  can retune. Items 60 (S211) and 62/64 remain the capital-path levers.

**Caveats:**

- Only orders the PM approved are in the population. Candidates rejected earlier never reach this gate
  under any variant, so the population is complete for this gate.
- The deployed denominator is applied to all 17 runs, although 16 of them ran under the equity denominator
  before S210. This is a counterfactual under today's policy, the same method S210's migration check used.
- Pair noise is measured on 16 pairs, one run each. That is enough to show the line is unstable, not to
  estimate a rate.

## Re-replay before the S220 merge - 2026-09-21

[ADR-0030](../../decisions/0030-the-correlation-gate-is-a-ramp-not-a-cliff.md) made this a **merge
gate**, not a formality: *"0 of 38 was measured on a 17-run history, not promised for the future."*
Re-run on the book as it stands, with the committed appendix scripts unchanged, from the main
checkout (the only tree with `.env`; the S220 build worktree has none).

**The sample grew**: **22** runs / **45** approvals carrying a `correlated_cluster_pct` outcome,
against the 17 / 38 measured on 2026-09-17 - `sched-2026-09-17` and `sched-2026-09-18` are new.

🟩 **Validation first, before any counterfactual.** Replayed cluster membership is **identical on
45 / 45** recorded approvals and cluster value is within 5 % on **45 / 45**. The replay reproduces
the gate that actually ran; only then is it allowed to answer what a different shape would have done.

| Variant | Orders | Rejections (cap 0.25) | Median share | Worst share | Mean clustered |
| --- | --- | --- | --- | --- | --- |
| binary 0.70 (champion) | 45 | **0** | 0.051 | **0.106** | 0.47 |
| binary 0.65 | 45 | 0 | 0.072 | 0.148 | 0.60 |
| binary 0.60 | 45 | 0 | 0.082 | 0.152 | 0.96 |
| binary 0.50 | 45 | 0 | 0.093 | 0.206 | 1.33 |
| **ramp 0.5→0.9 (S220)** | 45 | **0** | 0.066 | **0.098** | 1.33 |
| weighted ρ⁺ | 45 | **6** (all MDLZ) | 0.164 | **0.301** | 14.69 |

🟩 **Both conditions met.** Zero retroactive rejections, and the ramp's worst share **0.098** is under
the bar ADR-0030 set (the cliff's then-measured `0.102`) *and* under the cliff's **current** `0.106`.
🎯 **The cliff's worst share moved and the ramp's did not** - 0.102 → 0.106 for binary 0.70 as five
more approvals landed, while the ramp held at 0.098. The ramp is the tighter reading of this book,
not the looser one, and that gap widened rather than closed.

🪤 **The rejected option got worse, which is the useful control.** Weighted ρ⁺ now rejects **6** MDLZ
approvals (was 5) with a worst share of **0.301** against a 0.25 cap - so the retroactive shock
ADR-0030 refused is real, growing, and specific to one name.

**Noise, re-measured on 18 near-line pairs** (0.50 ≤ ρ < 0.90, was 16): the 95 % interval spans 0.70
on **14 of 18**, split halves disagree about the 0.70 side on **8 of 18**, dropping five shock days
flips **2 of 18**, and Spearman flips **3 of 18**. The case against a single cutoff strengthened with
the larger sample.

**Reproduce it:** run Appendix A then Appendix B from the repository root with `PYTHONPATH` set to the
root, in a tree that has `.env`. 🪤 `uv run python <abs-path-outside-the-repo>` does **not** put the
repo on `sys.path`; without `PYTHONPATH` the loader dies on `ModuleNotFoundError: kernel` before it
reaches the spine.

## Appendix A - loader (`corr_replay_load.py`)

Run from the repo root with `.env` present: `PYTHONPATH=. uv run python corr_replay_load.py`, then `corr_replay.py`.

```python
"""Load every PMRun with approvals + its market bars + run-start broker holdings; pickle."""
import pickle, re
from decimal import Decimal
from dotenv import load_dotenv; load_dotenv(r"<repo>\.env")
from kernel.graph_env import build_graph_from_env
from agents.portfolio_manager.poll import _market_and_regime
g = build_graph_from_env()
out = []
for pm in sorted(g.list_nodes("PMRun"), key=lambda n: str(n.props.get("created_at"))):
    ois = pm.props.get("order_intent_set") or {}
    appr = ois.get("approved") or ()
    recs = []
    for it in appr:
        gr = {x.get("name"): dict(x) for x in (it.get("gate_report") or ())}
        c = gr.get("correlated_cluster_pct")
        if c is None: continue
        recs.append(dict(ticker=it["ticker"], qty=int(it["quantity"]), price=Decimal(str(it["est_price"]["amount"])), corr=c))
    if not recs: continue
    an = g.get_node("AnalystRun", ois.get("source_analyst_run_id") or pm.props.get("source_analyst_run_id"))
    if an is None: print("no analyst", pm.key); continue
    market, regime, run_id = _market_and_regime(g, an)
    if market is None: print("no market", pm.key); continue
    snaps = [n for n in g.list_nodes("BrokerPositionSnapshot") if n.props.get("run_id") == run_id]
    snap = max(snaps, key=lambda n: str(n.props.get("created_at",""))) if snaps else None
    holdings = {}
    if snap is not None:
        for h in snap.props.get("holdings", ()):
            holdings[str(h.get("ticker"))] = Decimal(int(h.get("market_value_cents", 0))) / 100
    eq = Decimal(int(snap.props["account_equity_cents"]))/100 if snap is not None and "account_equity_cents" in snap.props else None
    bars = [(b.ticker.upper(), b.bar_date, b.close) for b in market.bars]
    out.append(dict(pm=pm.key, created=str(pm.props.get("created_at")), run_id=run_id, recs=recs, holdings=holdings, equity=eq, bars=bars))
    print(pm.props.get("created_at","")[:16], run_id, len(recs), "approved-with-corr", len(holdings), "held", len(bars), "bars")
pickle.dump(out, open(r"<scratch-dir>\corr_runs.pkl","wb"))
print("runs", len(out))
```

## Appendix B - replay and noise checks (`corr_replay.py`)

```python
import pickle, math, re
from datetime import timedelta
from decimal import Decimal
from itertools import pairwise
from agents.portfolio_manager.issuer_map import load_issuer_map
from agents.portfolio_manager.domain.issuer import issuer_key
S = r"<scratch-dir>"
runs = pickle.load(open(S + r"\corr_runs.pkl", "rb"))
imap = load_issuer_map("orchestration/packs/trading_issuer_map.json")
LOOKBACK, MINB, CAP = 120, 60, 0.25

def returns(bars):
    latest = max(d for _, d, _ in bars); start = latest - timedelta(days=LOOKBACK)
    grp = {}
    for t, d, c in bars:
        if d >= start: grp.setdefault(t, []).append((d, c))
    return {t: {cur[0]: cur[1] / prev[1] - 1.0 for prev, cur in pairwise(sorted(s))} for t, s in grp.items()}

def pearson(xs, ys):
    n = len(xs)
    if n < 2: return None
    mx, my = sum(xs) / n, sum(ys) / n
    vx = sum((x - mx) ** 2 for x in xs); vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0: return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(vx * vy)

def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v)
    for k, i in enumerate(o): r[i] = float(k)
    return r

def overlap(R, a, b, drop=()):
    A, B = R.get(a, {}), R.get(b, {})
    days = sorted(d for d in A if d in B and d not in drop)
    return days, [A[d] for d in days], [B[d] for d in days]

def pair(R, a, b):
    days, xs, ys = overlap(R, a, b)
    return pearson(xs, ys), len(days)

VARIANTS = {
    "binary 0.70": lambda r: 1.0 if r is not None and r >= 0.70 else 0.0,
    "binary 0.65": lambda r: 1.0 if r is not None and r >= 0.65 else 0.0,
    "binary 0.60": lambda r: 1.0 if r is not None and r >= 0.60 else 0.0,
    "binary 0.50": lambda r: 1.0 if r is not None and r >= 0.50 else 0.0,
    "weighted rho+": lambda r: max(r, 0.0) if r is not None else 0.0,
    "ramp 0.5->0.9": lambda r: 0.0 if r is None else min(1.0, max(0.0, (r - 0.5) / 0.4)),
}

sched = [x for x in runs if x["run_id"].startswith("sched-")]
validation = []; results = {k: [] for k in VARIANTS}; near_pairs = {}
for run in sched:
    R = returns(run["bars"])
    held_issuer_vals, held_issuer_tk = {}, {}
    for t, v in run["holdings"].items():
        k = issuer_key(t, imap); held_issuer_vals[k] = held_issuer_vals.get(k, Decimal(0)) + v
        held_issuer_tk.setdefault(k, set()).add(t.upper())
    deployed = sum(run["holdings"].values(), Decimal(0))
    for name, w in VARIANTS.items():
        vals = dict(held_issuer_vals); tks = {k: set(v) for k, v in held_issuer_tk.items()}
        for rec in run["recs"]:
            cand = rec["ticker"]; iss = issuer_key(cand, imap); cost = rec["price"] * rec["qty"]
            value = cost + vals.get(iss, Decimal(0)); clustered = []
            for held in sorted(vals):
                if held == iss: continue
                best, widest = None, 0
                for ht in tks.get(held, ()):
                    r, n = pair(R, cand.upper(), ht)
                    widest = max(widest, n)
                    if r is not None and (best is None or r > best): best = r
                if widest < MINB: continue
                f = w(best)
                if f > 0:
                    value += vals[held] * Decimal(str(f)); clustered.append(held)
                if name == "binary 0.70" and best is not None and 0.5 <= best < 0.9:
                    near_pairs[(cand.upper(), held)] = (run, sorted(tks[held]))
            ratio = float(value / deployed) if deployed > 0 else 0.0
            passed = ratio <= CAP
            results[name].append((run["run_id"], cand, ratio, passed, len(clustered)))
            if name == "binary 0.70":
                d = rec["corr"]["detail"]; m = re.search(r"cluster_value_usd=([\d.]+)", d); ci = re.search(r"cluster_issuers=([^;]*)", d)
                validation.append((run["run_id"], cand, float(m.group(1)), float(value), ci.group(1), ",".join(sorted({iss, *clustered}))))
            if passed:
                vals[iss] = vals.get(iss, Decimal(0)) + cost; tks.setdefault(iss, set()).add(cand.upper())

print("=== VALIDATION at 0.70 (recorded vs replay cluster_value_usd; cluster membership)")
ok = 0
for rid, t, rec, rep, cr, cp in validation:
    same_members = set(cr.split(",")) == set(cp.split(","))
    close = abs(rec - rep) / max(rec, 1) < 0.05
    ok += same_members
    if not (same_members and close):
        print(f"  DIFF {rid} {t}: recorded {rec:.2f} [{cr}] replay {rep:.2f} [{cp}]")
print(f"  membership identical {ok}/{len(validation)}; value within 5%: {sum(abs(a-b)/max(a,1)<0.05 for _,_,a,b,_,_ in validation)}/{len(validation)}")

print("\n=== COUNTERFACTUAL (deployed-capital denominator, cap 0.25), scheduled runs only")
for name, rows in results.items():
    rej = [(r, t, round(x, 3)) for r, t, x, p, _ in rows if not p]
    ratios = sorted(x for _, _, x, _, _ in rows)
    print(f"  {name:14s} orders={len(rows)} rejected={len(rej)} median_ratio={ratios[len(ratios)//2]:.3f} max={ratios[-1]:.3f} mean_clustered={sum(c for *_, c in rows)/len(rows):.2f}")
    for r in rej[:12]: print("      rejects", r)

# ---- noise / robustness on pairs 0.5-0.9
print("\n=== NOISE CHECK on", len(near_pairs), "candidate-vs-held pairs with 0.50 <= rho < 0.90")
cross = {"split-half disagree on >=0.70": 0, "drop 5 shock days flips 0.70": 0, "spearman flips 0.70": 0, "CI spans 0.70": 0}
rows = []
for (cand, held), (run, htks) in near_pairs.items():
    R = returns(run["bars"])
    # market shock days: largest mean |return| across all tickers
    daymag = {}
    for t, s in R.items():
        for d, v in s.items(): daymag.setdefault(d, []).append(abs(v))
    shock = set(sorted(daymag, key=lambda d: -sum(daymag[d]) / len(daymag[d]))[:5])
    ht = max(htks, key=lambda h: pair(R, cand, h)[0] or -1)
    days, xs, ys = overlap(R, cand, ht); n = len(days)
    r = pearson(xs, ys); h = n // 2
    r1, r2 = pearson(xs[:h], ys[:h]), pearson(xs[h:], ys[h:])
    _, xd, yd = overlap(R, cand, ht, drop=shock); rd = pearson(xd, yd)
    rs = pearson(rank(xs), rank(ys))
    z, se = math.atanh(r), 1 / math.sqrt(n - 3); lo, hi = math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)
    above = r >= 0.70
    if (r1 >= 0.70) != (r2 >= 0.70): cross["split-half disagree on >=0.70"] += 1
    if (rd >= 0.70) != above: cross["drop 5 shock days flips 0.70"] += 1
    if (rs >= 0.70) != above: cross["spearman flips 0.70"] += 1
    if lo < 0.70 < hi: cross["CI spans 0.70"] += 1
    rows.append((r, cand, ht, n, r1, r2, rd, rs, lo, hi, run["run_id"]))
for k, v in cross.items(): print(f"  {k}: {v}/{len(rows)}")
rows.sort(reverse=True)
print("  rho    pair          n   half1  half2  -shock spearman  CI95          run")
for r, c, h, n, r1, r2, rd, rs, lo, hi, rid in rows:
    print(f"  {r:.3f}  {c:>5}-{h:<6} {n:3d}  {r1:.3f}  {r2:.3f}  {rd:.3f}  {rs:.3f}   [{lo:.2f},{hi:.2f}]  {rid}")
import json
json.dump({"orders": {k: [dict(run=r, ticker=t, ratio=round(x,4), passed=p, clustered=c) for r,t,x,p,c in v] for k,v in results.items()},
           "pairs": [dict(rho=round(r,4), cand=c, held=h, n=n, half1=round(r1,4), half2=round(r2,4), no_shock=round(rd,4), spearman=round(rs,4), lo=round(lo,4), hi=round(hi,4), run=rid) for r,c,h,n,r1,r2,rd,rs,lo,hi,rid in rows],
           "validation": [dict(run=a, ticker=b, recorded=c, replay=round(d,2), members_recorded=e, members_replay=f) for a,b,c,d,e,f in validation]},
          open(S + r"\corr_results.json","w"), indent=1)
sh = [r - rd for r, c, h, n, r1, r2, rd, rs, lo, hi, rid in rows]
print(f"  mean change from dropping 5 shock days: {sum(sh)/len(sh):+.3f} (positive = shock days inflate rho)")
```

## Appendix C - console output (2026-09-17, identical on two runs)

```text
=== VALIDATION at 0.70 (recorded vs replay cluster_value_usd; cluster membership)
  membership identical 38/38; value within 5%: 38/38

=== COUNTERFACTUAL (deployed-capital denominator, cap 0.25), scheduled runs only
  binary 0.70    orders=38 rejected=0 median_ratio=0.051 max=0.102 mean_clustered=0.45
  binary 0.65    orders=38 rejected=0 median_ratio=0.072 max=0.148 mean_clustered=0.58
  binary 0.60    orders=38 rejected=0 median_ratio=0.082 max=0.152 mean_clustered=0.95
  binary 0.50    orders=38 rejected=0 median_ratio=0.085 max=0.206 mean_clustered=1.29
  weighted rho+  orders=38 rejected=5 median_ratio=0.159 max=0.300 mean_clustered=14.47
      rejects ('sched-2026-08-24', 'MDLZ', 0.278)
      rejects ('sched-2026-09-11', 'MDLZ', 0.262)
      rejects ('sched-2026-09-14', 'MDLZ', 0.28)
      rejects ('sched-2026-09-15', 'MDLZ', 0.289)
      rejects ('sched-2026-09-16', 'MDLZ', 0.3)
  ramp 0.5->0.9  orders=38 rejected=0 median_ratio=0.066 max=0.098 mean_clustered=1.29

=== NOISE CHECK on 16 candidate-vs-held pairs with 0.50 <= rho < 0.90
  split-half disagree on >=0.70: 7/16
  drop 5 shock days flips 0.70: 2/16
  spearman flips 0.70: 3/16
  CI spans 0.70: 12/16
  rho    pair          n   half1  half2  -shock spearman  CI95          run
  0.817    AMD-INTC    83  0.864  0.752  0.777  0.780   [0.73,0.88]  sched-2026-09-03
  0.781   INTC-AMD     83  0.745  0.827  0.767  0.787   [0.68,0.85]  sched-2026-08-20
  0.768    USB-BAC     82  0.814  0.687  0.791  0.765   [0.66,0.84]  sched-2026-09-08
  0.717    WFC-USB     82  0.772  0.638  0.731  0.665   [0.59,0.81]  sched-2026-09-16
  0.710    XOM-DOW     83  0.745  0.676  0.717  0.675   [0.58,0.80]  sched-2026-08-26
  0.703   AMZN-GOOG    82  0.710  0.715  0.724  0.623   [0.57,0.80]  sched-2026-09-16
  0.679    WFC-C       82  0.637  0.736  0.730  0.667   [0.54,0.78]  sched-2026-09-16
  0.640    DOW-XOM     82  0.711  0.560  0.632  0.618   [0.49,0.75]  sched-2026-09-10
  0.640   MDLZ-KO      82  0.683  0.568  0.605  0.656   [0.49,0.75]  sched-2026-09-16
  0.632   GOOG-AMZN    83  0.561  0.704  0.712  0.602   [0.48,0.75]  sched-2026-08-21
  0.610   MDLZ-KHC     82  0.652  0.583  0.582  0.557   [0.45,0.73]  sched-2026-09-16
  0.581   MDLZ-MO      82  0.700  0.503  0.516  0.493   [0.42,0.71]  sched-2026-09-16
  0.572      C-BAC     83  0.621  0.544  0.588  0.608   [0.41,0.70]  sched-2026-08-21
  0.542    USB-C       82  0.470  0.658  0.648  0.550   [0.37,0.68]  sched-2026-09-16
  0.528   AVGO-INTC    82  0.411  0.740  0.461  0.552   [0.35,0.67]  sched-2026-09-08
  0.511   AVGO-NVDA    83  0.531  0.523  0.438  0.590   [0.33,0.65]  sched-2026-09-04
  mean change from dropping 5 shock days: +0.001 (positive = shock days inflate rho)
```
