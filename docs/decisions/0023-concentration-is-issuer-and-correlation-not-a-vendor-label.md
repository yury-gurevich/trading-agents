---
type: Architecture Decision
status: accepted
closes: "How does the portfolio manager account for correlated exposure across its book? The law says a per-sector name count is the correlation penalty — but the labels it counts are vendor industry strings, share classes of one issuer count as two names, and the correlation that actually bites crosses labels entirely."
tags: [portfolio-manager, risk, concentration, correlation, issuer, dual-class, sectors, deliberator, dl-119, adr-0012, pm-nev-06]
---

# ADR 0023 — Concentration is measured by issuer and correlation, not by a vendor label

**Status:** Accepted · **Date:** 2026-08-20 · **Decider:** planning agent under delegated authority
(operator: *"item 18 ADR"*, 2026-08-20)

## Context

**The deliberator has rejected the same thing on four consecutive nights, and it is right.**
[DL-119](../design-log.md): across the four real binding runs the veto rejected **19 of 26**
PM-approved orders — **73 %** — and `verify-2026-08-20-s182-a` approved four and traded **none**.
The dominant objection is always the same shape:

> *AMZN: "the sector gates are label-based counts with no name-correlation penalty, so 'Retail' lets
> AMZN pass at 1 name while the book already carries correlated mega-cap tech beta (AAPL, NVDA, AMD,
> CSCO, NFLX, PYPL)"*
>
> *GOOG: "the PM treats GOOG as a new ticker while the portfolio already holds GOOGL, and the
> sector/name-count gates do not catch duplicate Alphabet issuer exposure"*
>
> *INTC: "would add to existing AMD/NVDA semiconductor exposure, and the sector/name caps pass
> without any name-correlation penalty"*

**The law already claims to have solved this.** `PM-NEV-06`:

> Never opens more than `max_names_per_sector` distinct names in any one sector (**GICS level 1**),
> independent of the dollar cap. A basket of small correlated names is still one bet; **the count cap
> is the name-correlation penalty the dollar-weight cap misses**.

Both statements are true at once, and that is the whole problem. **The penalty exists in law and is
defeated in practice by the data it runs on.**

### Measured, 2026-08-20, on `verify-2026-08-20-s182-a`

**1 · The labels are not GICS level 1.** GICS level 1 has **11** sectors. The provider returns **30
distinct labels**, at industry granularity: `Semiconductors`, `Banking`, `Aerospace & Defense`,
`Pharmaceuticals`, `Media`, `Retail`, `Communications`, `Technology`. None of `Semiconductors`,
`Banking` or `Pharmaceuticals` is a GICS sector. **The law's parenthetical is factually wrong about
its own input.**

**2 · Finer labels make the cap weaker, not stronger.** `max_names_per_sector=3` over **30** buckets
permits up to 90 names; over the 11 the law assumes, 33. The gate is roughly **three times more
permissive** than the clause intends.

**3 · The correlated cluster is scattered across five labels.**

| Ticker | Label |
| --- | --- |
| AMZN | `Retail` |
| NVDA, AMD, AVGO, INTC | `Semiconductors` |
| MSFT, AAPL | `Technology` |
| CSCO | `Communications` |
| META, GOOG, GOOGL | `Media` |

The mega-cap AI complex occupies five buckets, so the cap admits **3 × 5 = 15** of these names before
firing once. That is the AMZN objection, exactly.

**4 · Share classes count as two names.** GOOG and GOOGL are both `Media`, so Alphabet consumes
**2 of 3** slots as if it were two independent bets. **No issuer mapping exists anywhere in the
repo** — grep for `issuer` / `dual_class` returns nothing.

**5 · A ticker with no label silently bypasses both gates.**
`concentration.py:55-57` — `sector = self._sectors.get(...); if sector is None: return ()`. An empty
outcome tuple is indistinguishable from a passed gate. Coverage is 99/99 today, so this is latent —
but it is the same absence-as-silence shape S183 is fixing in the scanner's earnings gate.

**6 · The dollar cap never sees held positions.** `SectorBook.__init__` seeds `_names` from held
positions but **never `_deployed`**, so `max_sector_pct` counts only the current batch. Masked today
because the name count binds first — which will stop being true the moment the name count is fixed.

### What the portfolio manager actually has

Measured: **tickers, quantities, sector labels, cash, portfolio value.** Nothing else. `beta` is
computed by the scanner and **never passed on**. There is no correlation input, no issuer key, and
no factor model. So *"no correlation dimension at all"* is not rhetoric — it is literally true.

## Decision

**Concentration is measured against the book, by issuer and by measured correlation. A vendor
industry label is an input to that, never the definition of it.** Four parts:

**1 · Aggregate by issuer before counting names.** Share classes of one issuer are **one name** and
one dollar exposure. This is exact, cheap, and needs no statistics — a small issuer map in the
trading pack, owned as pack data (ADR-0012), not hard-coded in an agent.

**2 · Add a correlation dimension computed from data already on the graph.** Every run already
carries **203 bars per ticker**; pairwise return correlation is therefore computable at **zero API
cost**. Concentration is assessed against the *held book*, not against a label. This is the part
that catches AMZN-with-NVDA, which no labelling scheme reliably will.

**3 · Stop asserting GICS level 1.** The labels are vendor industry strings. Either map them to GICS
level 1 and keep the clause honest, or keep the finer labels and **re-derive the cap for 30 buckets
rather than 11**. 🚨 Do not leave a clause claiming a granularity its input does not have.

**4 · A concentration gate that cannot evaluate must say so, never silently pass.** `return ()` on a
missing label becomes an explicit not-evaluated outcome, consistent with S183's rule for the scanner.

## Options considered and rejected

- **Soften the veto to restore throughput** — *rejected*, and it is the tempting one. Lowering the
  bar or letting the grace expire again would make the objections stop *binding* rather than stop
  being *true*. That is DL-104's advisory posture reintroduced by the back door. **Fix the PM, not
  the referee.**
- **Just lower `max_names_per_sector` from 3 to 1** — *rejected*. It would cut the count but not the
  defect: Alphabet would still be two names, and AMZN would still be invisible against NVDA. It
  tightens the wrong dimension and would reject good orders to compensate for missing the bad ones.
- **Business-line / factor classification** (AWS is AI infrastructure, not Retail) — *deferred, not
  rejected*. It is the most faithful answer to the AMZN objection, and there is **no data source for
  it** in any current provider. It is also a judgement rather than a computable fact. Revisit if a
  factor feed is ever adopted; do not fake it with keyword rules.
- **Beta-weighted exposure only** — *rejected as insufficient*. The scanner already computes beta and
  it would be cheap to forward, but beta measures exposure to *the market*, not to *each other*.
  AMD, NVDA and AVGO would all read "high beta" without revealing that they are the same bet. Useful
  as a secondary signal; not a substitute for pairwise correlation.
- **Let the deliberator remain the correlation check** — *rejected*. It is currently doing this job,
  which is why the veto rate is 73 %. An LLM re-deriving portfolio risk from a text packet on every
  order is expensive, non-reproducible (56 % self-agreement, S173), and unbounded. Correlation is a
  computation, and computations belong in the gate.

## Consequences

- **Fewer orders will be approved at first, and that is the point.** The gate begins refusing
  concentration it previously admitted. Throughput should recover as the PM stops emitting orders
  that were only ever going to be vetoed.
- 🚨 **This requires a law-amendment cycle, not a code edit.** The PM `laws.md` is **LOCKED v1**, and
  `PM-NEV-06` both names GICS level 1 and asserts the count cap *is* the correlation penalty. Both
  statements change. New clauses are append-only (conventions §2) and start ⬜ unproven.
- **The trading pack gains an issuer map.** Pack data under ADR-0012, so the substrate stays
  domain-agnostic.
- 🪤 **Fixing the name count un-masks defect 6.** `max_sector_pct` currently never sees held
  positions and is hidden behind the name cap binding first. Land them together or the dollar cap
  silently becomes the weak gate.

## How we will know it worked — the falsifiable part

**The deliberator is the test.** If this ADR is right, the exposure-aggregation objections should
disappear from the verdicts and the veto rate should fall materially from 73 %. **If they persist
after the PM aggregates exposure properly, then the deliberator is over-weighting correlation and
that becomes the finding** — a claim about the referee, not the player, and one we currently have no
way to separate. This ADR makes that separation possible.

## Related

[DL-119](../design-log.md) (the veto-rate measurement) · `PM-NEV-06` (the clause being amended) ·
[ADR-0012](0012-platform-domain-separation.md) (why the issuer map is pack data) ·
[ADR-0019](0019-risk-cap-binds-position-size-not-stop-distance.md) (the risk cap this sits beside) ·
S183 (the same absence-as-silence rule, applied to the scanner)
