---
type: Architecture Decision
status: accepted
closes: "The PM's correlation gate treats a held issuer as fully clustered at ρ ≥ 0.70 and wholly absent below it. EXP-008 measured that no cutoff between 0.50 and 0.70 changes a single approval, and that the verdict near 0.70 is sampling noise. Should the gate stay a binary cliff, become a ramp, or weight every positive correlation?"
tags: [portfolio-manager, concentration, correlation, risk-gate, control-design, adr-0025, exp-008, dl-185]
amends: ADR-0025
---

# ADR 0030 — The correlation gate is a ramp, not a cliff

**Status:** Accepted · **Date:** 2026-09-20 · **Decider:** planning agent, under operator delegation
(*"decisions only: make the best decision that serves the project best"*, 2026-09-20)

## Context

`PORTFOLIO_MANAGER_CORRELATION_THRESHOLD = 0.70` (`agents/portfolio_manager/settings.py:107`) is a
**binary inclusion test**. A held issuer whose pairwise close-return correlation with the candidate is
at or above 0.70 joins the cluster **at full value**; one below it contributes **nothing**.

Measured consequences on `sched-2026-09-16`: **WFC** clusters USB at `0.7172` but ignores C at
`0.6788`; **AMZN** clusters Alphabet at `0.7031` and ignores MSFT at `0.4607`; **MDLZ** reads
`correlated_issuers=none` beside KO `0.6397`, KHC `0.6097` and MO `0.5811` — the whole staples complex,
invisible.

Since 2026-09-14 this has been the **referee's lead ground** on buy vetoes, appearing in every
real-debate run since (MDLZ 09-14, AMZN 09-15, AMZN on both 09-16 runs).

## The measurement that decides it

[EXP-008](../research/experiments/EXP-008-correlation-cutoff-replay.md) replayed **17 scheduled runs /
38 approvals**, validated **38 / 38** against recorded cluster membership *and* cluster value.

| Variant | Rejections (cap 0.25) | Mean share | Worst share |
| --- | --- | --- | --- |
| binary 0.70 (champion) | **0** | 0.051 | 0.102 |
| binary 0.60 | **0** | 0.082 | 0.152 |
| ramp 0.5→0.9 | **0** | 0.066 | **0.098** |
| weighted ρ⁺ | **5** (all MDLZ) | 0.159 | **0.300** |

And the line itself does not survive its own error bars, on the 16 pairs with 0.50 ≤ ρ < 0.90:

| Check | Pairs whose side of 0.70 is not stable |
| --- | --- |
| 95 % interval spans 0.70 | **12 / 16** |
| First and second half of the window disagree | **7 / 16** |
| Spearman flips the side | **3 / 16** |
| Dropping the 5 biggest market days flips it | **2 / 16** (mean Δρ **+0.001**) |

🪰 That last row matters: the instability is **not** outlier days. It is ordinary sampling noise in ρ
over an 82–83 day window.

## Decision

**The cluster becomes a ramp: contribution rises linearly from 0 at ρ = 0.50 to 1 at ρ = 0.90.**

Three reasons, in order of weight:

1. **It matches what the estimate can actually resolve.** A binary line converts a number whose 95 %
   interval spans 0.70 on **12 of 16** near-line pairs into a confident yes/no. That is the same sin
   this repo keeps finding elsewhere — a check asserting more precision than its input supports.
   A ramp degrades continuously, so 0.69 and 0.71 stop being the difference between *nothing* and
   *everything*.
2. **It carries no retroactive shock, measured.** **0 of 38** approvals rejected — the identical bar
   ADR-0025 applied before moving the denominator. 🎯 And its **worst share is 0.098 against the
   cliff's 0.102**: the ramp is *not* a loosening. It reads the same book slightly more tightly at the
   top while counting the near-misses the cliff discards.
3. **It retires an inert lead ground.** The referee's critique is true and has been leading every
   recent real debate, yet **no retune lifts a veto** — so the argument consumes the debate without
   being able to change an outcome. Removing the cliff removes the ground.

## Rejected

- **Keep the binary cliff at 0.70.** Rejected: it is the option the noise measurement specifically
  indicts, and it keeps feeding the referee a true-but-inert lead argument.
- **Lower the cutoff to 0.60 or 0.50.** Rejected: measured to change **nothing** (0 rejections either
  way), so it buys none of the benefit while keeping all of the cliff's noise sensitivity. 🪤 It also
  looks like action while being none — the worst kind of tuning move.
- **Weight every positive correlation (ρ⁺).** Rejected on measurement, not taste: it rejects **MDLZ on
  all 5 nights it was approved**, with a worst share of **0.300 against the 0.25 cap**. That is a real
  retroactive shock, and counting every positive ρ turns a *cluster* check into a **book-wide
  co-movement** check — a different gate, not a better one.
- **Treat it as a `/tuner` question.** Rejected, and this is why item 61 was wrong to close without
  filing it: *where* the line sits is a tuning question, but *binary versus graded* changes what the
  gate means. Meaning is an ADR.

## Consequences

- 🚨 **This ADR ships no code.** Work-queue item **68** narrows from *"decide the gate's meaning"* to
  *"implement the ramp"*. The implementation is a small PM sprint and **owes a fresh EXP-008 replay on
  the book as it stands then** — 0/38 was measured on a 17-run history, not promised for the future.
- `PORTFOLIO_MANAGER_CORRELATION_THRESHOLD` does not disappear. It becomes the **ramp floor** (0.50),
  with a new ceiling (0.90); both remain `tunable()` and both are now *shape* parameters of a graded
  test rather than a single decision boundary.
- 🪤 **The threshold is pack-injected, so the implementing deploy is a full `up`, not a retag.**
  `PORTFOLIO_MANAGER_CORRELATION_THRESHOLD` is declared in
  `orchestration/packs/trading_tunables.json:16` and confirmed live on the `portfolio-manager`
  app at `0.70`. Adding a ceiling key moves that pack, and an image-only retag refreshes no
  injected pack — the S202 trap. Verified by reading the running app, not the file.
- The PM law book needs a clause cycle in the implementing sprint: the gate's guarantee changes from
  *"issuers at or above the threshold"* to *"issuers in proportion to correlation"*.
- S197's `below_threshold_top` census stops being disclosure-only — the near-misses it already records
  are exactly what the ramp counts.
- Item **65**'s row named the binary cutoff as the second compounding cause and ADR-0025 ruled only on
  the denominator. This closes that gap.
