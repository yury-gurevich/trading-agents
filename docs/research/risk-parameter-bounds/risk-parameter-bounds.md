<!-- Agent: planning | Role: external evidence for what each risk parameter's bounds should be -->
# Risk parameter bounds — what the outside world says each number should be

**Status:** Reference · **Date:** 2026-09-15 · **Companion to:**
[parameter-inventory](../parameter-inventory/INDEX.md)

## Why this exists

The parameter inventory records **our** numbers — default, bounds, unit, and the `why=` string
attached to each `tunable()`. This document records **the outside world's** numbers: for each
risk-shaping parameter, what the quantity actually is, what range the literature or regulation
supports, and where our value sits inside it.

🚨 **The distinction matters because the `why=` strings are not justifications.** Read carefully,
several of them say so themselves — *"before sector caps exist"* (they now exist),
*"first-slice risk"*, *"a label-bucket cap"*. They are labels written as the numbers accreted, not
derivations. Treating them as evidence is a category error this document exists to correct.

🪤 **Nothing here is a recommendation to change a live value.** A parameter change is an operator
decision with capital consequences ([ADR-0013](../../decisions/0013-continuous-improvement-system.md)
governs how a value moves, and safety caps are ADR-only, never experiments). This is the evidence
layer that makes such a discussion possible — a **min/max envelope**, so that when a value is
argued about, it is argued inside a defensible range.

---

## The headline finding: the book is under-risked by roughly 5–8x

The industry unit of account is **risk per trade** — how much of the account is lost if the stop is
hit — not position size. Our system caps position *size* and never computes risk per trade.
Converting:

| Quantity | Our live value | Standard practice | Ratio |
| --- | --- | --- | --- |
| Risk per trade | `1 % position x 5 % stop` = **0.05 %** | **1–2 %** of equity | **20–40x tighter** |
| Portfolio heat (all open risk) | ~25 positions x 0.05 % = **~1.25 %** | **6–10 %** total | **5–8x tighter** |

Van Tharp's framing: at 2 % risk per trade you can absorb ~50 consecutive losses before halving the
account; at 10 % it takes 7. At **0.05 %** it takes roughly **1,400** — which is not prudence, it is
a position too small to express a view. 🪰 **This is the quantitative form of the referee's nightly
complaint** that sizing "caps dollars not volatility-adjusted risk" (work-queue item 62).

⚠️ **Do not read this as "increase the size".** It is pre-production with no realized-outcome record
(`known_outcomes` was **0** at S198), and sizing up an unproven edge multiplies losses just as
faithfully as gains. The finding is that the number is **far outside the band anyone else uses**, and
nobody chose that deliberately.

---

## Portfolio construction

| Parameter | Live | Code default | What it really bounds | Evidence-supported range | Verdict |
| --- | --- | --- | --- | --- | --- |
| `max_position_pct` | **0.01** | 0.10 | Single-issuer concentration, as a fraction of portfolio value | **UCITS 5/10/40**: ≤5 % per issuer, extendable to 10 %, with all ≥5 % holdings capped at 40 % aggregate. Retail funds sit at 5 % | Live **0.01 is 5x below** the regulatory ceiling; the **code default 0.10 exceeds** the retail limit. Defensible envelope: **0.01–0.05** |
| `max_positions` | **60** | 10 | How many concurrent names — the diversification axis | Evans & Archer (1968): **10–15**. Statman (1987): **30–40**. Modern reviews: **30–50**, some argue 100+ | Live **60 is above** the modern consensus (fine — excess names cost little). The **code default 10 sits at the 1968 floor**. Envelope: **30–60** |
| `max_sector_pct` | 0.30 *(code default; never operator-set)* | 0.30 | Total deployment into one sector label | No single regulatory anchor; UCITS constrains *issuers*, not sectors. Common fund mandates use **20–25 %**; index-concentration work treats >30 % as concentrated | **0.30 is at the permissive edge** of common practice. Envelope: **0.15–0.30** |
| `max_names_per_sector` | 3 *(code default)* | 3 | Count of issuers per sector label | No external anchor — a bucket count is not a risk measure. Its own `why` calls it "a label-bucket cap" | **Arbitrary, and admits it.** Measured: this gate **fails 20 times** — it is one of only three that ever reject. An arbitrary number doing real gating is the worst combination here |
| `cash_buffer_pct` | 0.05 *(code default)* | 0.05 | Cash held back from deployment | Convention only; 2–10 % typical for unlevered long books | **0.05 is conventional.** Low priority |

---

## Trade construction

| Parameter | Live | What it really bounds | Evidence-supported range | Verdict |
| --- | --- | --- | --- | --- |
| `min_reward_risk_ratio` | 1.5 *(code default)* | The payoff ratio a setup must clear | Breakeven win rate is `(1 - W)/W`: R:R **1.0 → 50 %**, **1.5 → 40 %**, **2.0 → 33.3 %**, **3.0 → 25 %**. Convention: >1.5 good, >2.0 excellent | The **threshold is sensible and the gate is inert** — measured, **170 of 170** recommendations carry the identical ratio **2.0**, so it can never fail (work-queue item 60). 🪤 **The number is not the problem; the derivation is.** And R:R is meaningless without a measured win rate, which we do not have |
| `base_stop_loss_pct` | 0.05 | Reference stop distance | Not a literature constant — it is strategy-dependent. The meaningful anchor is the ATR multiple below | Sits inside its own `le=0.08` cap. Envelope follows the ATR work, not a fixed percentage |
| `base_take_profit_pct` | 0.10 | Reference target | Paired with the stop to give R:R 2.0 | Fine **as a pair**; the defect is that the pair is fixed, making R:R constant |
| `scaled_stop_atr_multiplier` | **2.0** | Stop distance in units of ATR — the real volatility control | Chandelier default **3.0** (22-period). By style: scalping 1–1.5, day 1.5–2, **swing 2–3**, position 3–4. Backtests favour **3.0** for profit factor; 4.0 gives biggest wins with worst drawdown | Our `base_max_holding_days = 10` makes this **swing trading**, so the band is **2–3** and **2.0 sits on its floor**. A tighter-than-typical stop means **more stop-outs on noise**. Envelope: **2.0–3.0** |
| `scaled_stop_floor_pct` / `ceiling_pct` | 0.025 / 0.08 | Hard clamp on the scaled stop | Derived from the declared max-risk cap, not external | **Measured 2026-09-15: never bitten, 0 of 32** — but AMD reached **7.995 %** against the 8.00 % ceiling. Live and about to be tested |
| `base_max_holding_days` | 10 | Holding horizon — sets which style's bands apply | Defines the regime: 10 sessions = swing | **Load-bearing for every other row**; changing it moves the ATR band |
| `base_min_confidence` | 0.60 | Analyst score floor for actionability | No external anchor — an internal model score, not a calibrated probability | **Cannot be anchored externally until the score is calibrated against realized outcomes.** Measured: it "filtered 0 of 29" on 2026-09-14 — it is not discriminating |

---

## Correlation

| Parameter | Live | What it really bounds | Evidence-supported range | Verdict |
| --- | --- | --- | --- | --- |
| `correlation_threshold` | 0.70 | When two issuers count as one bet | Effect-size convention places **r = 0.7 as "very large"**; 0.9 is the threshold for ranking validity | **0.70 is a defensible, conventional cut.** Envelope: **0.6–0.8** |
| `min_correlation_bars` | 60 | Minimum overlap before the gate will evaluate | To detect **r = 0.7** at α = 0.05: **~13** samples for 80 % power, ~10 for 90 % | 🪰 **60 is generous — roughly 4–5x the statistical requirement.** The referee's objection that an **81-bar** overlap is "thin" is **weaker than it sounds** for detecting a strong correlation. The real caveat is different: financial correlation is **non-stationary**, so the binding question is regime stability, not power |
| `correlation_lookback_days` | 120 | Window for the pairwise estimate | Common practice 60–252 sessions; shorter tracks regime, longer is stabler | **120 is mid-band and reasonable.** Envelope: **60–252** |
| `max_correlated_cluster_pct` | 0.25 | Cap on one measured correlated cluster | Tighter than the sector cap by design, which is the correct relationship | **Internally coherent** (0.25 < 0.30). Measured: **evaluated on 31 of 181 orders, never failed** — item 61 |

---

## What to do with this

1. **These are envelopes, not proposals.** Each row gives a min/max a value can be argued inside.
   Recording them as `ge=`/`le=` bounds on the `tunable()` — the user's stated intent — makes an
   out-of-band value impossible to set by accident, without committing to any particular value.
2. **Three parameters have no external anchor and cannot get one yet** — `max_names_per_sector`,
   `base_min_confidence`, and the reward/risk *pair*. All three need **realized outcomes** to
   calibrate against, and the outcome recorder (`ANLZ-OBS-05`, S198) has only just started writing.
   🪤 **Do not invent anchors for these.** Their honest status is "unanchored, pending evidence".
3. **The ordering this suggests:** the gates that *never fire* (items 60, 61) cost nothing to fix and
   remove false comfort. The gates that *do* fire on arbitrary numbers (`max_names_per_sector`) and
   the sizing philosophy (item 62) are policy, and should wait for outcome data rather than be
   re-guessed.

## Sources

- [Van Tharp on position sizing and portfolio heat](https://vantharpinstitute.com/van-tharp-teaches-position-sizing-strategies-and-risk-management/)
- [The 2 % rule and fixed-fractional sizing](https://www.asktraders.com/learn-to-trade/risk-management/position-sizing-secrets/)
- [Position sizing methods and risk control](https://zerodha.com/varsity/chapter/position-sizing-active-traders-part-3/)
- [How many stocks are sufficient for equity portfolio diversification? — literature review](https://www.mdpi.com/1911-8074/14/11/551)
- [Evans and Archer, forty years later](https://www.researchgate.net/publication/285691377_Evans_and_archer_-_Forty_years_later)
- [Chandelier Exit — ATR multiplier and lookback](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit)
- [ATR stop-loss strategies by trading style](https://www.luxalgo.com/blog/5-atr-stop-loss-strategies-for-risk-control/)
- [Chandelier exit strategy — backtested multipliers](https://www.quantifiedstrategies.com/chandelier-exit-strategy/)
- [Break-even win rate for a given reward:risk](https://journalplus.co/metrics/break-even-rate/)
- [Risk-reward ratio vs win rate](https://www.luxalgo.com/blog/risk-reward-ratio-vs-win-rate-key-differences-2/)
- [Effect magnitudes — interpreting r = 0.7](https://www.sportsci.org/resource/stats/effectmag.html)
- [Sample size determination for correlation studies](https://www.cfholbert.com/blog/sample-size-correlation/)
- [UCITS 5/10/40 rule and issuer limits](https://www.vettafi.com/insights/enterprise-article-40-act-vs-ucits-what-us-asset-managers-should-know)
- [FCA COLL 5.2 — UCITS investment powers and limits](https://handbook.fca.org.uk/handbook/coll5/coll5s1)
- [When is an index too concentrated? — LSEG](https://www.lseg.com/en/insights/ftse-russell/when-is-an-index-too-concentrated)
