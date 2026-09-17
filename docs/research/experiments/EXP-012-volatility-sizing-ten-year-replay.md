# EXP-012 - Does volatility-scaled sizing survive a ten-year window with down-legs?

**Date:** 2026-09-18 · **Status:** complete. **No.** Iso-risk sizing delivers the dispersion it promises
(6.40x -> 2.00x) and still loses **$11,619** over 47,549 decisions, with **100 %** of ticker-cluster
resamples negative. Down-legs do favour it and do not come close to paying for it ·
**Feeds:** work-queue item **62**, [ADR-0025](../../decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md)
Decision B

## Purpose

[EXP-009](EXP-009-volatility-sizing-replay.md) measured iso-risk sizing on **61 approved buys over one
month** (`sched-2026-08-17` -> `sched-2026-09-16`) and found it cut per-position risk dispersion 4.2x ->
1.9x while losing **$445**, "almost all of it on one period effect". Work-queue item 62 recorded the
precondition for going further in one sentence:

> **Don't adopt on one window**; re-measure over a window with a down-leg before an ADR.

That is this experiment. The question is narrow and falsifiable: **does a window containing real
down-legs reverse EXP-009's sign?** The risk-parity case predicts it should - equalising loss-at-stop
should pay precisely when things fall.

The decision is capital-risk policy, so it is the operator's (charter OUT-2). This probe informs it and
moves no dial.

## Process

**Data.** [EXP-011](EXP-011-regime-markov-and-barrier-calibration.md)'s cached dataset, reused rather than
re-pulled: **98 names, 263,005 daily bars, 2016-01-04 -> 2026-09-16**, split- and dividend-adjusted, SIP
(consolidated tape). **No network, no spine access, no LLM - this experiment cost nothing.**

**Population.** A decision at the close of **every 5th session from 2017-01-03**, per name, exactly
EXP-011's grid: **47,549 decisions, 98 tickers, 2017-01-06 -> 2026-09-14**. (EXP-011 reported 47,485 on
the same grid; this replay additionally requires >= 20 settled prior windows before it will estimate a
target, which moves the count slightly.)

**Production mirror.** Every quantity is the live one, read from the code rather than assumed:

| Element | Value | Source |
| --- | --- | --- |
| Stop | `clamp(2.0 x ATR14/close, 0.025, 0.08)` | `agents/analyst/settings_stop_target.py:49,60,70` |
| Target | median trailing favourable excursion, <= 120 settled 10-session windows | S211 / ADR-0027 Decision 1 |
| Holding horizon | 10 sessions | `base_max_holding_days` |
| Sizing | `floor(portfolio_value x max_position_pct / price)` | `agents/portfolio_manager/domain/sizing.py:25` |
| `MAX_POSITION_PCT` | **0.01** (live; code default 0.10) | `orchestration/packs/trading_tunables.json:13` |

**Exits.** Entry at the next session's open. Exit at the stop, the target, or the close after 10
sessions, whichever comes first. **The daily low is checked before the high**, so a day touching both is
scored as a stop (conservative), and a gap through the stop fills at that day's open. Identical exits for
every arm - only quantity differs. Equity is held at **$102,000** throughout (today's book).

**Arms.**

| Arm | Quantity |
| --- | --- |
| A - fixed 1 % notional (champion) | `floor(0.01 x E / P)` |
| B - iso-risk | `floor(R x E / (P x stop))`, `R` = A's **mean** planned risk = **0.0426 %** of equity |
| C - iso-risk, 2 % notional cap | B, capped at `floor(0.02 x E / P)` |
| E - 50/50 blend | `floor((qty_A + qty_B) / 2)` |
| F - iso-risk, never above 1 % notional | `min(qty_B, qty_A)` |

`R` is set to A's mean so the book carries the **same total planned risk** and only its *distribution*
changes - the same construction EXP-009 used.

## Delivery

This record; the replay script is in Appendix A. It is deterministic (bootstrap seeded) and re-runs from
the cached dataset in about a minute.

### Result 1 - ex-ante risk dispersion (iso-risk delivers)

| Arm | Risk % equity min / median / max | Max / min | CV |
| --- | --- | --- | --- |
| A champion | 0.0125 / 0.0393 / 0.0800 | **6.40** | 0.36 |
| B iso-risk | 0.0213 / 0.0409 / 0.0426 | **2.00** | 0.09 |

Today's sizing makes the riskiest position carry **6.4x** the planned loss of the calmest - worse than
the 4.2x EXP-009 measured on one month, because ten years contains more extreme ATRs. Iso-risk cuts it
to **2.00x**, not 1.0x, for the two reasons EXP-009 named: whole-share rounding, and the **8 % stop
ceiling**, which makes the widest names' stops understate their volatility.

### Result 2 - ex-post P&L (iso-risk loses, and more clearly than before)

| Arm | Total P&L | SD per position | Worst single position |
| --- | --- | --- | --- |
| A champion | **$107,525** | $36.46 | -$292 |
| B iso-risk | **$95,906** | $33.36 | **-$308** |

**B - A = -$11,619.** Ticker-cluster bootstrap (5,000 resamples of the 98 tickers): 95 % interval
**[-$19,210, -$4,186]**, **100 %** of resamples negative. EXP-009's month gave -$445 at 98 % negative;
the ten-year window does not rescue iso-risk, it **convicts** it.

🪤 **One EXP-009 finding does not replicate.** There, iso-risk improved the worst single position by
30 %. Over ten years B's worst position is **worse** (-$308 vs -$292): iso-risk buys more of low-stop
names, and a low-stop name that gaps through its stop loses more shares' worth. The SD improvement is
also milder (-8.5 % here vs -17 % there).

### Result 3 - down-legs favour iso-risk, and it is not nearly enough

| Window | n | A | B | B - A |
| --- | --- | --- | --- | --- |
| 2017-2021 | 24,518 | $80,699 | $78,410 | -$2,290 |
| 2022-2026 | 23,031 | $26,826 | $17,497 | **-$9,330** |
| **2018 Q4 down-leg** | 1,155 | -$16,129 | -$13,124 | **+$3,006** |
| **2020 COVID crash** | 490 | $1,609 | -$552 | **-$2,161** |
| **2022 bear** | 4,019 | -$16,050 | -$14,938 | **+$1,112** |
| EXP-009's window | 392 | -$2,189 | -$3,033 | -$844 |

**The hypothesis is confirmed in direction and refuted in magnitude.** Iso-risk helps in two of the
three down-legs - exactly where risk parity says it should - but the three together net **+$1,957**
against a **-$11,619** total. 🪤 **And it does not help in the sharpest fall:** in the COVID crash
iso-risk *lost* $2,161, because a gap-driven crash punishes share count, not stop width.

### Result 4 - the mechanism: volatile names earn more over ten sessions

Mean 10-session realised return by stop-width decile (n = 4,754 each):

| Decile | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 | D9 | D10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Mean stop | 2.52 % | 2.89 % | 3.30 % | 3.67 % | 4.05 % | 4.45 % | 4.93 % | 5.55 % | 6.52 % | 7.89 % |
| Mean return | +0.265 % | **+0.092 %** | +0.070 % | +0.090 % | +0.204 % | +0.140 % | +0.169 % | +0.252 % | **+0.532 %** | +0.466 % |

From D2 to D9 the gradient is monotone in intent and steep in size - **volatile names returned about
5x** what calm ones did over this horizon. Iso-risk moves capital *down* that gradient by construction:
it buys more of the low-stop names precisely because they are calm. **That is the whole result.**
EXP-009 saw the same thing in one month (calm names -2.70 %, volatile +1.11 %) and could not tell it
from a period effect; ten years says it is not a period effect.

🪤 **D1 breaks the monotonicity** (+0.265 %) because the **2.5 % stop floor** binds there: those names'
stops are set by the clamp, not their ATR, so the decile is not a clean volatility bucket.

### Result 5 - no variant rescues it

| Arm | P&L | Risk max/min | Max notional |
| --- | --- | --- | --- |
| A fixed 1 % notional (champion) | **$107,525** | 6.40 | 1.00 % |
| B iso-risk | $95,906 | **2.00** | 1.70 % |
| C iso-risk, 2 % notional cap | $95,906 | 2.00 | 1.70 % |
| E 50/50 blend | $99,553 | 4.24 | 1.35 % |
| F iso-risk, never above 1 % notional | $82,984 | 3.41 | 1.00 % |

- **C is identical to B** - the 2 % cap never binds even over ten years, replicating EXP-009's finding
  on 61 orders.
- **E buys about half the dispersion cut for about a third of the cost** - the only variant offering a
  real trade rather than a strict loss.
- **F is the worst of both.** Capping iso-risk at the champion's notional means it only ever *cuts*
  positions, never adds, so it sheds return without completing the risk equalisation.

## Interpretation

1. **The named precondition is met and the answer is negative.** Item 62 asked for a longer window with
   a down-leg before an ADR. It now exists, and it strengthens EXP-009's conclusion rather than
   reversing it: 98 % negative on one month becomes **100 %** on ten years.
2. **Iso-risk is not wrong about risk - it is wrong about return.** Its dispersion claim is real and
   large (6.40x -> 2.00x). It simply funds that improvement by systematically buying less of what paid.
3. **The deliberator's nightly complaint is true but costly to act on.** *"Fixed-fraction 0.01 sizing
   caps dollars not volatility-adjusted risk"* is a correct description of the code and a correct
   statement of textbook practice. On this book's horizon and stop rule, acting on it costs money. This
   is the same shape as [EXP-008](EXP-008-correlation-cutoff-replay.md)'s correlation finding: **the
   referee's ground is true, and the fix it implies does not pay.**
4. **What would change the answer.** A longer holding horizon, a stop that is not ATR-derived, or a
   universe where the volatility-return gradient runs the other way. None of those is today's system.

**Decision taken:** none. This is capital-risk policy (charter OUT-2: ADR only).

**What it feeds:**

- **Work-queue item 62** can move from "re-measure before an ADR" to a decided question.
- 🚨 **[ADR-0025](../../decisions/0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md)
  Decision B ruled the *direction*** - *"yes, volatility should scale position risk"* (operator, "yes",
  2026-09-16) - **and this evidence contradicts that ruling on returns.** Confirming, amending or
  overriding it is the operator's call; this record does not presume it. Note the ruling authorised no
  implementation, so nothing shipped on it.
- If the dispersion goal is taken as primary regardless of cost, **arm E** is the honest middle and
  should be priced explicitly rather than reached for as a compromise.

**Caveats:**

- **Population is every grid decision, not PM-approved buys.** The analyst and PM filters select a
  subset this replay cannot reconstruct without re-running the LLM path. EXP-009's approved-buy
  population showed the **same sign** on its month, which is corroboration, not proof.
- 🚨 **Survivorship.** The 98 names are *today's* universe projected backwards; names that fell out
  before 2026 are absent. Both arms share the bias, but it is the most serious limitation on **Result
  4** specifically - a universe of survivors may reward volatility more than the live universe did.
- **This is not a realizable book.** Equity is constant, positions overlap without a `max_positions`
  limit, and there is no compounding. The comparison is valid arm-against-arm on identical decisions;
  the dollar totals are not a P&L forecast.
- **No transaction costs.** B carries about 7 % more notional (EXP-009), so costs would widen the gap
  against B.
- **Both clamps bite.** The 2.5 % floor and 8 % ceiling compress the extremes, which *blunts* iso-risk
  at both ends - the un-clamped version was not measured.

## Appendix A - replay script (`exp012_sizing.py`)

Reads only `mc_data.pkl` from EXP-011. No `.env`, no network.

```python
import pickle, statistics, random

SP = r"<EXP-011 scratch dir>"
EQUITY, MAX_POS_PCT = 102000.0, 0.01
ATR_N, ATR_MULT, STOP_FLOOR, STOP_CEIL = 14, 2.0, 0.025, 0.08
HORIZON, MAX_WINDOWS, GRID, START = 10, 120, 5, "2017-01-03"

d = pickle.load(open(SP + r"\mc_data.pkl", "rb"))
bars = d["bars"]

def atr_pct(o, h, l, c, i):
    if i < ATR_N:
        return None
    tot = 0.0
    for j in range(i - ATR_N + 1, i + 1):
        pc = c[j - 1]
        tot += max(h[j] - l[j], abs(h[j] - pc), abs(l[j] - pc))
    return (tot / ATR_N) / c[i]

rows = []
for tk in sorted(bars):
    b = sorted(bars[tk])
    dates = [x[0] for x in b]
    o = [float(x[1]) for x in b]; h = [float(x[2]) for x in b]
    l = [float(x[3]) for x in b]; c = [float(x[4]) for x in b]
    n = len(b)
    fav = [None] * n
    for i in range(n - HORIZON):                       # window STARTING at i
        fav[i] = (max(h[i + 1:i + 1 + HORIZON]) - c[i]) / c[i]
    for i in range(n):
        if dates[i] < START or (i % GRID) or i + 1 >= n:
            continue
        a = atr_pct(o, h, l, c, i)
        if a is None:
            continue
        stop = min(max(a * ATR_MULT, STOP_FLOOR), STOP_CEIL)
        hi = i - HORIZON                               # settled windows only
        if hi < 0:
            continue
        prior = [fav[j] for j in range(max(0, hi - MAX_WINDOWS + 1), hi + 1) if fav[j] is not None]
        if len(prior) < 20:
            continue
        target = statistics.median(prior)
        entry = o[i + 1]
        if target <= 0 or entry <= 0:
            continue
        sp, tp = entry * (1 - stop), entry * (1 + target)
        ret, kind = None, None
        for k in range(i + 1, min(i + 1 + HORIZON, n)):
            if l[k] <= sp:                             # low before high
                px = min(sp, o[k])                     # gap -> fill at open
                ret, kind = (px - entry) / entry, ("gap" if o[k] < sp else "stop")
                break
            if h[k] >= tp:
                ret, kind = target, "target"
                break
        if ret is None:
            k = min(i + HORIZON, n - 1)
            ret, kind = (c[k] - entry) / entry, "time"
        rows.append((tk, dates[i], entry, stop, target, ret, kind))

qtyA = [int((EQUITY * MAX_POS_PCT) // r[2]) for r in rows]
riskA = [q * r[2] * r[3] / EQUITY for q, r in zip(qtyA, rows)]
live = [i for i, q in enumerate(qtyA) if q > 0]
R = sum(riskA[i] for i in live) / len(live)
qtyB = [int((R * EQUITY) // (r[2] * r[3])) for r in rows]
```

Arms C/E/F, the decile table and the bootstrap follow from `rows`, `qtyA` and `qtyB` directly.

### Appendix B - console output (2026-09-18)

```text
decisions: 47549  tickers: 98  2017-01-06 -> 2026-09-14
R (champion mean planned risk) = 0.0426% of equity
A champion: risk% min/med/max 0.0125/0.0393/0.0800  max/min 6.40  CV 0.36
B iso-risk: risk% min/med/max 0.0213/0.0409/0.0426  max/min 2.00  CV 0.09

P&L total: A $107,525   B $95,906   B-A $-11,619
window                            n             A             B          B-A
2017-2021                     24518        80,699        78,410       -2,290
2022-2026                     23031        26,826        17,497       -9,330
2018 Q4 down-leg               1155       -16,129       -13,124        3,006
2020 COVID crash                490         1,609          -552       -2,161
2022 bear                      4019       -16,050       -14,938        1,112
EXP-009 window                  392        -2,189        -3,033         -844

B-A ticker-cluster bootstrap 95% CI: [$-19,210, $-4,186]  share negative 100%
exits: {'time': 11639, 'target': 22028, 'stop': 11683, 'gap': 2199}
worst single position: A $-292   B $-308
SD per position:       A $36.46   B $33.36

stop-width decile -> mean 10-session return, mean stop
  D1: stop  2.52%   mean return +0.265%   n=4754
  D2: stop  2.89%   mean return +0.092%   n=4754
  D3: stop  3.30%   mean return +0.070%   n=4754
  D4: stop  3.67%   mean return +0.090%   n=4754
  D5: stop  4.05%   mean return +0.204%   n=4754
  D6: stop  4.45%   mean return +0.140%   n=4754
  D7: stop  4.93%   mean return +0.169%   n=4754
  D8: stop  5.55%   mean return +0.252%   n=4754
  D9: stop  6.52%   mean return +0.532%   n=4754
  D10: stop  7.89%   mean return +0.466%   n=4754

A fixed 1% notional (champion)       P&L $  107,525   risk max/min  6.40   max notional  1.00%
B iso-risk (full)                    P&L $   95,906   risk max/min  2.00   max notional  1.70%
C iso-risk, 2% notional cap          P&L $   95,906   risk max/min  2.00   max notional  1.70%
E 50/50 blend of A and B             P&L $   99,553   risk max/min  4.24   max notional  1.35%
F iso-risk, never exceed 1% notional P&L $   82,984   risk max/min  3.41   max notional  1.00%
```
