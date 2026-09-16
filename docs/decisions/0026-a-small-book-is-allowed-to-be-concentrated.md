---
type: Architecture Decision
status: accepted
closes: "Once concentration is measured against deployed capital (ADR-0025), a small book cannot grow — from flat, the allowance is 30% of zero, so every order fails forever. Is a small book allowed to be concentrated? And if so, what carries concentration control while the book is too small for a ratio to mean anything?"
tags: [portfolio-manager, risk, concentration, bootstrap, deployed-capital, not-evaluated, diversification, adr-0025, adr-0023, pm-nev-06, pm-nev-09]
amends: ADR-0025
---

# ADR 0026 — A small book is allowed to be concentrated

**Status:** Accepted · **Date:** 2026-09-16 · **Decider:** operator (*"Yes - accept the risk"*,
2026-09-16), on a proposal from the planning agent

## Context — how this question arose

[ADR-0025](0025-concentration-measures-the-book-position-risk-measures-the-capital-base.md) was
accepted earlier the same day: concentration gates (`max_sector_pct`, `correlated_cluster_pct`) divide
by **deployed capital** rather than total equity, thresholds unchanged at 0.30 and 0.25.

That ADR's migration check re-computed every gate against `sched-2026-09-15` — a **23-position,
21.24 %-deployed** book — and found every approval and rejection unchanged. **The check was correct
and it was not sufficient.** It tested the steady state and never tested the **bootstrap**.

🪤 **The planning agent found this while preparing the implementation sprint, not during the
decision.** Recording that plainly: ADR-0025 was accepted on an incomplete check. Nothing in it is
wrong, but it would have deadlocked the book on contact with a flat portfolio.

### What the implementation actually does to a small book

`sector_exposure_outcome` (`agents/portfolio_manager/domain/sector_gate_outcomes.py:57-63`) decides
`PASSED` on `total <= max_sector_pct * portfolio_value`. Substitute deployed capital for
`portfolio_value`, with a typical `$1,000` order:

| Book | Deployed | New-sector total | Allowed @ 0.30 | Verdict |
| --- | --- | --- | --- | --- |
| **0** | **$0** | $1,000 | **$0** | **FAIL** |
| 1 | $1,000 | $1,000 | $300 | FAIL |
| 2 | $2,000 | $1,000 | $600 | FAIL |
| 3 | $3,000 | $1,000 | $900 | FAIL |
| 4 | $4,000 | $1,000 | $1,200 | PASS |

Adding a **second name to a sector that already holds one** needs a 7-position book before it passes.

**From flat the allowance is `0.30 × 0 = 0`, so every order fails, so the book never acquires a
position, so the allowance stays zero. It is a permanent deadlock, not a slow start.**

### This is not hypothetical

*[measured 2026-09-16, live Neon spine, book size read from the `max_positions` gate's own
`held_issuers` evidence across all 58 runs that recorded one]*

| Claim | Value |
| --- | --- |
| Runs with a book of **fewer than 4** positions | **8 of 58 — 14 %** |
| Runs with fewer than 7 | 12 of 58 — 21 % |
| Runs with fewer than 10 | 24 of 58 — 41 % |
| Smallest book ever recorded | **1 position** |
| Book deliberately **flattened to zero** | 2026-08-07, [`functionality-checks.md`](../laws/functionality-checks.md) |
| Book today | 24 issuers, 21.24 % deployed |

The project has flattened the book on purpose once and has run a sub-4-name book in one run out of
seven. A rule that cannot survive a flat book is a rule that cannot survive this project's own
operating history.

## Why the decision was reached

### 1. The gate is not malfunctioning — it is telling the truth

The tempting reading is "the deployed denominator is broken at small N". It is not. **A one-position
book genuinely is 100 % concentrated.** A two-name book in one sector genuinely is 100 % concentrated
in that sector. The ratio is correct; it is the *only* correct answer to the question
`max_sector_pct` asks.

This matters because it rules out the whole family of "fix the arithmetic" responses. There is no
denominator that makes a one-position book look diversified, and inventing one would be falsifying
the measurement to get a convenient answer.

### 2. So the cap is really a minimum-diversification requirement

A 30 %-of-book sector cap **implies at least four sectors**. A 25 % cluster cap implies four
uncorrelated clusters. Expressed as a percentage it looks like a limit on bigness; enforced from
flat it is a demand that the book already be diversified before it is allowed to become diversified.

That reframing is what turns this from an implementation bug into a policy question, and it is the
step the decision actually turns on: **either the book may pass through a concentrated phase on its
way to a diversified one, or it may never start.** There is no third state.

### 3. The risk being accepted is bounded and already bounded elsewhere

Accepting "a small book may be concentrated" sounds unbounded. It is not, because concentration
during bootstrap is still controlled — by `max_names_per_sector`, which is a **count** (≤ 3), has no
denominator, is therefore completely insensitive to book size, and is **the one concentration control
in this system with a real track record: 17 actual rejections**, including META and BAC on
`sched-2026-09-15`. Position size is independently capped at 1 % of equity by `sizing`, which
ADR-0025 left on the equity denominator precisely so it keeps working at any book size.

So the risk accepted is narrow and specific: **during bootstrap, concentration is controlled by name
count and per-position size, but not by sector or cluster value share.** It is not "concentration is
unmanaged".

### 4. The floor is derivable, so it is not a number anyone has to defend

The two controls coincide at a computable point. Three names at the maximum position size fit inside
the percentage cap exactly when:

```
names_cap × max_position_pct ÷ pct_cap  ≤  deployed ÷ equity

sector:      3 × 0.01 ÷ 0.30  =  10 % of equity
correlation: 3 × 0.01 ÷ 0.25  =  12 % of equity
```

**Below that floor the ratio cap is stricter than the count cap** (and at the bottom, impossible).
**Above it the ratio cap is looser than the count cap**, and earns its place by catching the case the
count cap misses — three names that are unusually large.

This is the reason the decision could be taken without haggling over a constant: the floor is not
chosen, it is *implied* by two caps that already exist and were already agreed. It also moves
automatically if either cap is ever retuned, so it cannot silently go stale the way the 30 % equity
cap did (ADR-0025's central finding).

The book today is **21.24 % deployed — above both floors**, so both gates go live on the current book
the moment this ships. Nothing is suppressed today.

## Decision

**Accepted: a small book is allowed to be concentrated.**

1. `max_sector_pct` and `correlated_cluster_pct` report **whole-gate `NOT_EVALUATED`** — never
   `FAILED` — while `deployed < names_cap × max_position_pct ÷ pct_cap` of equity (10 % and 12 %
   respectively at today's tunable values).
2. The floor is **derived from existing tunables at evaluation time**, not stored as a new constant
   or tunable.
3. `max_names_per_sector` and `sizing` are the concentration controls below the floor. Neither
   changes.
4. The gate evidence must **state the floor, the actual deployment, and that the floor was the reason**
   whenever it returns `NOT_EVALUATED`, so a suppressed gate is never mistakable for a passing one —
   the same discipline S208 established.

This reuses the existing `PM-NEV-09` whole-gate `NOT_EVALUATED` mechanism that
[S208](../sprints/sprint-208-a-risk-gate-says-what-it-can-reject.md) strengthened. It introduces no
new mechanism.

## The road not taken

- **Floor the denominator instead — `max(deployed, X)`.** Rejected: it reports a *number that is not
  true*. A one-position book would read 20 % concentrated when it is 100 % concentrated. ADR-0025
  exists because a concentration reading stopped meaning what it said; fixing that by making a
  different reading lie is a straight repeat of the error.
- **Let the gate return `FAILED` below the floor and accept that the book cannot bootstrap.**
  Rejected: measured, the book has been flat or near-flat in 14 % of runs, and was flattened on
  purpose in August. This is a deadlock, not a conservative default.
- **Use a post-trade denominator (`deployed + this order`).** Rejected: it does not help. The first
  order into a flat book is still 100 % of the post-trade book, so it still fails a 30 % cap. It
  changes the arithmetic without changing the conclusion.
- **Keep the equity denominator for small books and switch at a threshold.** Rejected: two
  denominators for one gate means the reported value changes meaning mid-life with no marker — the
  precise failure ADR-0025 was written to end. `NOT_EVALUATED` is honest about the discontinuity;
  a silent denominator swap is not.
- **Lower the caps so a small book passes.** Rejected: a cap low enough for a 2-name book is no cap
  at all for a 25-name book, and it re-encodes a book size into a constant — ADR-0025's rejected
  option, one layer down.
- **Suppress by position count rather than deployment share.** Rejected as less robust: positions are
  not equal-sized (today they range `$156` to `$1,122`), so a count floor approximates the thing a
  deployment-share floor states exactly.

## Consequences

- Work-queue item **65** gains this as scope. It was already ADR-ruled and build-ready; it is now
  fully specified.
- A defect found alongside this, needing no decision and fixed in the same sprint: the PASS/FAIL test
  uses a raw comparison (`total <= max_sector_pct * portfolio_value`) while the reported value uses a
  zero-safe helper that returns `0.0` for a non-positive denominator
  (`sector_gate_outcomes.py:126-128`, `correlation.py:130-131`, `position_gates.py:160-161`). At
  `deployed = 0` the evidence would read **`value=0.0000` with `outcome=FAILED`** — the number
  contradicting the verdict.
- 🪤 **`NOT_EVALUATED` below the floor is a real reduction in enforcement, not a formality.** Any
  acceptance reading or law-coverage claim that counts a `NOT_EVALUATED` concentration gate as
  evidence of bounded concentration is wrong, and the sprint owes a test that says so.
- The PM law cycle owed by ADR-0025's implementation now also covers this: `PM-NEV-06` and
  `PM-NEV-09` describe these gates, and "is allowed to be concentrated below a derived floor" is a
  guarantee the agent makes.
