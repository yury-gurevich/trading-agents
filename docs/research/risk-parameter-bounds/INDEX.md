# Risk parameter bounds — external evidence for the risk-shaping numbers

**Status:** Reference · **Date:** 2026-09-15

- **[risk-parameter-bounds.md](risk-parameter-bounds.md)** — per-parameter: what the quantity
  actually bounds, the range the literature or regulation supports, and where our value sits.

**What it answers:** for each risk-shaping `tunable()`, is the number a defensible choice or an
accretion? What min/max envelope can it be argued inside? Which have no external anchor at all?

**Why it exists:** [parameter-inventory](../parameter-inventory/INDEX.md) records *our* numbers and
their `why=` strings. Read closely, several of those strings are labels rather than derivations —
*"before sector caps exist"* (they now do), *"first-slice risk"*, *"a label-bucket cap"*. This
document supplies the missing outside anchor so a parameter discussion happens inside a defensible
range rather than from scratch.

**Headline:** risk per trade is **0.05 %** (1 % position x 5 % stop) against a standard **1–2 %**,
and portfolio heat ~**1.25 %** against a standard **6–10 %** — the book is under-risked by roughly
**5–8x**, and nobody chose that. 🪤 Not a recommendation to size up: there is no realized-outcome
record yet, and sizing an unproven edge multiplies losses equally.

**Consuming work:** work-queue items **60** (`reward_risk` cannot fail), **61** (correlation gate
disabled by one holding), **62** (sizing caps dollars, not risk); the eventual `ge=`/`le=` bounds on
each `tunable()`; [ADR-0013](../../decisions/0013-continuous-improvement-system.md) experimentation.

**Caveat:** point-in-time, and three parameters (`max_names_per_sector`, `base_min_confidence`, the
reward/risk pair) **cannot** be anchored externally until realized outcomes exist. Their honest
status is *unanchored, pending evidence* — do not invent anchors for them.
