---
type: Architecture Decision
status: accepted
closes: "What do the portfolio manager's ratio gates divide by — total equity or deployed capital? Three gates divide by equity, the book runs at 21% deployed, and two of the three have therefore never been able to reject anything. And should volatility scale the risk numbers at all, given the regime label is computed, stored, carried and changes none of them?"
tags: [portfolio-manager, risk, concentration, sizing, denominator, deployed-capital, equity, volatility, regime, adr-0023, dl-119, pm-nev-06, pm-nev-09]
amends: ADR-0023
---

# ADR 0025 — Concentration measures the book; position risk measures the capital base

**Status:** Accepted · **Date:** 2026-09-16 · **Decider:** operator (*"yes"*, 2026-09-16), on a
proposal from the planning agent

## Context

**Two of the portfolio manager's eight gates have ever rejected anything.** Measured 2026-09-16
against the live Neon spine, across every `PMRun` ever recorded:

| Gate | Evaluated | Rejected | Shape |
| --- | --- | --- | --- |
| `sizing` | 75 | **20** | ratio ÷ equity, cap **1 %** |
| `max_names_per_sector` | 55 | **17** | a **count** (≤ 3), no denominator |
| `max_sector_pct` | 55 | **0** | ratio ÷ equity, cap **30 %** |
| `correlated_cluster_pct` | 38 | **0** | ratio ÷ equity, cap **25 %** |
| `reward_risk` | 55 | **0** | **one distinct value (2.00) across 294 recordings** |
| `max_positions` | 75 | **0** | count ≤ 60, holding 24 — live, far off |
| `min_order_quantity` | 75 | **0** | floor ≥ 1 |
| `cash_available` | 75 | **0** | floor nothing approaches |

### The rule that explains it

**An equity-denominated cap is inert whenever the cap exceeds the deployment ratio.**

The book is **21.24 % deployed** — `$21,711.95` of `$102,208.78` equity (measured against the Alpaca
paper account and the graph, 2026-09-16; graph and broker agree on 23 positions). So the *entire book
collapsed into a single cluster* reads **0.2124**, and:

- `max_sector_pct` at **0.30** — **cannot be reached.**
- `correlated_cluster_pct` at **0.25** — **cannot be reached.** Highest value ever observed across 38
  recordings is **0.0199**, or **8 % of its own threshold**.
- `sizing` at **0.01** sits *below* the deployment ratio, which is precisely why it is one of the two
  gates that fires.

`max_names_per_sector` fires because it is a **count**: no denominator, so no deployment sensitivity.
On `sched-2026-09-15` it was the only concentration control that did anything, rejecting META and BAC
on `sector_name_count`.

### The argument that settles it: the threshold silently changed meaning

Nobody edited these gates. **The book moved underneath them.**

| Date | Deployment | What a 30 % *equity* sector cap meant |
| --- | --- | --- |
| 2026-08-07 | **2.02×** (`$208,245.24` deployed, per [`functionality-checks.md`](../laws/functionality-checks.md)) | **14.8 % of the book** — a real constraint |
| 2026-09-16 | **0.21×** (`$21,711.95` deployed) | **141 % of the book** — unreachable |

The same number was a binding constraint and then a decoration, with no change to the code, no
alert, and nothing in the evidence trail marking the transition. A risk limit whose meaning is a
function of how invested you happen to be is not a risk limit.

### This is why ADR-0023's prediction failed

[ADR-0023](0023-concentration-is-issuer-and-correlation-not-a-vendor-label.md) established that
concentration is measured by **issuer and correlation**, not by a vendor label, and S184 built
`correlated_cluster_pct` to do it. [DL-119](../design-log.md) predicted the veto rate would fall.
It did not — work-queue item 59 recorded that prediction as **measured false**, all-time 78.9 %.

**The mechanism was right and inert.** The gate ADR-0023 asked for was built correctly and then
divided by a denominator that made it incapable of rejecting anything. ADR-0023 is not reversed here;
it is completed.

🪤 **The referee found this before we did.** The MDLZ veto of 2026-09-15 called
`correlated_cluster_pct` *"a vacuous PASS, not evidence of independence"*, reasoning from the
`20.7 %`-deployed book. That is the second half of the operator's etalon bar — the evidence
discipline catching its own defect — working without prompting.

---

## Decision A — the denominator is chosen per question, not per codebase

**There is no single right denominator, because two different questions are being asked.**

1. **"How much of my capital is at risk in this one position?"** → **total equity.**
   This is `sizing`. Deployed capital would be circular: the first position of a run would be 100 %
   of deployed, and the cap would tighten as the book fills — a limit that punishes diversification.
   **`sizing` is correct today and does not change.**

2. **"How concentrated is my book?"** → **deployed capital.**
   This is `max_sector_pct` and `correlated_cluster_pct`. Concentration is a property of the
   portfolio, not of how invested the portfolio happens to be. Dividing by equity makes a
   concentration reading depend on a quantity that has nothing to do with concentration.

**Accepted: `sizing` keeps equity. `max_sector_pct` and `correlated_cluster_pct` move to deployed
capital. The numeric thresholds (0.30 and 0.25) are unchanged.**

### The migration rejects nothing retroactively — checked, not asserted

Re-computed against `sched-2026-09-15`'s own recorded gate details:

| Subject | Today ÷ equity | Proposed ÷ deployed | Cap | Verdict |
| --- | --- | --- | --- | --- |
| Banking (held + WFC + BAC) | 0.0383 | **0.1803** | 0.30 | passes, real headroom |
| Media (held + META) | 0.0274 | **0.1289** | 0.30 | passes |
| Food Products (held + MDLZ) | 0.0196 | **0.0922** | 0.30 | passes |
| WFC correlated cluster | 0.0097 | **0.0455** | 0.25 | passes |
| MDLZ correlated cluster | 0.0097 | **0.0458** | 0.25 | passes |

**Every approval and every rejection on that run is unchanged.** The gates become *capable* of
binding without a retroactive shock — the numbers 0.30 and 0.25 become meaningful rather than
decorative, and today's book sits inside them with headroom.

### Implementation notes

- `portfolio.deployed_value` **already exists** (`agents/portfolio_manager/portfolio.py:37`) and is
  **already disclosed** in the gate detail (`agents/portfolio_manager/domain/position_gates.py:97`,
  `deployed_portfolio_usd=`). This is a denominator swap, not new machinery.
- 🪤 `portfolio.value` (`portfolio.py:32`) is documented *"the equity-backed portfolio value used for
  sizing"* and returns `self.cash.amount`. It works only because equity is loaded into the `cash`
  field. **The naming lies and should be fixed in the same change**, or the next reader will
  reasonably believe `sizing` divides by cash.
- A gate detail must state **which denominator it used**, so a future reader can tell a 0.18 that
  means "18 % of the book" from a 0.18 that means "18 % of equity". Same discipline as S208.
- Both gates keep whole-gate `NOT_EVALUATED` when they cannot be computed (`PM-NEV-09`, S208).

## Decision B — volatility scales the risk numbers: direction accepted, magnitude to be measured

Work-queue items **62** (*sizing caps dollars, not risk*) and **64** (*the regime label is computed,
stored and carried — and never changes a single risk number*) are **the same question**: should
volatility scale the risk numbers?

The referee has argued this nightly and is right. On `sched-2026-09-15`, AMZN:

> *"sizing is a fixed-fraction notional cap, not volatility-adjusted for a beta-1.383/ATR-2.35 % name"*

**Accepted in direction: yes, volatility should scale position risk, and a computed regime label that
moves no risk number is not a regime input.**

🚨 **Explicitly NOT accepted as an implementation.** Unlike Decision A, this changes **every position
size on every run**, and the stop/target bracket is already ATR-scaled (`applied_mode=scaled`), so
there is interaction risk between two volatility adjustments. **No sizing change ships on this ADR.**
The next step is a champion–challenger measurement on the same `as_of` with the cheapest sufficient
design, under the existing experiment harness — not a sprint that rewrites sizing.

## Consequence for `reward_risk` (work-queue item 60)

`reward_risk` has **one distinct value (2.00) in 294 recordings** because target and stop derive from
the same base pair; [S208](../sprints/sprint-208-a-risk-gate-says-what-it-can-reject.md) made it
*disclose* that (`comparison=STRUCTURALLY_DETERMINED`). This ADR does not settle it, but it narrows
it: a gate that cannot discriminate is the shape item 61 closed. **Either give it an independent
target derivation so it can vary, or retire it as a gate and keep it as a disclosure.** The planning
agent's recommendation is **retire**; the decision is deferred, not taken here.

---

## The road not taken

- **Move every ratio gate to deployed capital.** Rejected: it breaks `sizing`. At today's 4.707×
  ratio, AMZN's `0.009723` would become `0.0458` against a `0.01` cap — **every order would fail**.
  Thresholds are calibrated *jointly* with their denominator; the denominator is not independently
  choosable per codebase.
- **Keep equity and lower the concentration thresholds instead** (e.g. 30 % → 6 %). Rejected: it
  encodes today's deployment ratio into a constant. The book has run at 2.02× and at 0.21× within six
  weeks; any such constant is wrong at one of those and silently so.
- **Raise deployment so the existing caps bind.** Rejected: that is a capital-allocation decision
  being made by a measurement artefact. How invested the book is must not be driven by wanting a gate
  to work.
- **Scale sizing by volatility in this ADR.** Rejected: see Decision B. The direction is ruled; the
  magnitude is an experiment, and shipping it unmeasured is how two ATR adjustments compound
  invisibly.
- **Leave it and note the gates are advisory.** Rejected: nothing here should be advisory. An
  advisory gate says something and is not enforced; these say `PASS` and *cannot* say anything else.
  That is not advisory, it is inert, and it reads identically to a working gate in every artefact.

## Consequences

- Work-queue item **65** is answered by Decision A, and now also carries `max_sector_pct` — a second
  gate found inert for the identical reason during this investigation, folded in rather than filed
  as a new row.
- Items **62** and **64** merge into one measurement under Decision B.
- Item **60** narrows to a fix-or-retire choice, still open.
- Item **63** (*bounds restate the type, none records why*) is unaffected — it is process, and
  [S207](../sprints/sprint-207-a-bound-cites-the-evidence-that-set-it.md) set the pattern.
- The PM law book will need a clause cycle when Decision A ships: the denominator is a guarantee the
  agent makes, and `PM-NEV-06` / `PM-NEV-09` describe these gates. **The sprint that implements this
  owes the law cycle in the same unit of work.**
- 🪤 Until Decision A ships, **three** PM ratio gates remain unable to reject anything. Any acceptance
  reading that treats their `PASS` as evidence of bounded concentration is reading a constant.

## Correction — 2026-09-18, on EXP-012: Decision B's direction is withdrawn

**What the direction rested on.** Decision B accepted *"yes, volatility should scale position risk"* on
two grounds: the referee argues it nightly and is **right about the code**, and it is textbook practice.
Neither ground is a measurement of *this* system. The ADR said so itself and named the next step as a
champion–challenger measurement, authorising no implementation.

**Measured** ([EXP-012](../research/experiments/EXP-012-volatility-sizing-ten-year-replay.md): 47,549
decisions, 98 names, 2017-2026, production stop and target rules):

| | Fixed 1 % notional (champion) | Iso-risk |
| --- | --- | --- |
| Planned risk max ÷ min | 6.40x | **2.00x** |
| Total P&L | **$107,525** | $95,906 |

**B − A = −$11,619**, ticker-cluster bootstrap **[−$19,210, −$4,186]**, **100 %** of resamples negative.
Down-legs favour iso-risk (+$3,006 in the 2018 Q4 leg, +$1,112 in the 2022 bear) but not the COVID crash
(−$2,161), netting +$1,957 — nowhere near the cost. The mechanism is a return gradient in stop width:
**volatile names returned about 5x calm ones** over the 10-session horizon (decile 2 +0.092 % → decile 9
+0.532 %), and iso-risk buys *down* that gradient by construction. No variant rescues it: the 2 % notional
cap never binds, a 50/50 blend costs $7,972, and capping iso-risk at 1 % notional costs $24,541.

**Therefore (planning agent, under operator delegation — *"make decisions in accordance to industry best
practice. We will test the decision later one by one"*, 2026-09-18):**

1. **Decision B's directional acceptance is withdrawn.** Fixed-fraction 1 % notional sizing **stands as
   the champion**. Nothing shipped on Decision B, so nothing is unwound.
2. **The withdrawal is scoped, not universal.** Volatility-scaled sizing remains standard practice and is
   not being called wrong in general. It is measured **negative for this system's configuration**: a
   10-session holding horizon and a 2 × ATR stop clamped to 2.5–8 %. 🪤 **Re-open it if any of those three
   change** — a longer horizon in particular, since the low-volatility premium that makes iso-risk pay
   elsewhere is absent at ten sessions.
3. **Industry practice does not override a negative backtest of your own system.** This is the whole
   reason Decision B refused to ship on argument. The measurement it demanded has now been taken and it
   disagreed with the direction; honouring that is the point of having demanded it.
4. **The 62/64 bundle is dissolved.** Decision B called items 62 and 64 *"the same question"*. They are
   not. The regime half was settled separately by
   [ADR-0028](0028-the-regime-reads-vix-from-fmp-and-says-when-it-cannot.md) (the regime now reads VIX
   from FMP and declares itself degraded when it cannot); the sizing half is settled negatively here.
5. **Decision A is untouched** and remains shipped (S210).

**How this will be tested** (operator: *"we will test the decision later one by one"*): no code changes,
so the test is a **null check** — sizing behaviour on the next scheduled runs must be unchanged, with
`sizing` still reporting a fixed 1 % notional cap. Any future re-opening must clear EXP-012's bar on a
population of **PM-approved** buys rather than grid decisions, which is the caveat that most limits this
record.

**Road not taken:**

- **Adopt the 50/50 blend anyway**, buying half the dispersion cut for a third of the cost. Rejected: it
  is still a measured loss, chosen for how it feels rather than what it returns. If dispersion is later
  ruled to matter independently of return, this is the arm to price — but that is a new decision.
- **Keep the direction "accepted" and simply not implement it.** Rejected: a standing directional ruling
  that the evidence contradicts is exactly the kind of stale commitment that gets implemented later by
  someone reading only the headline.
