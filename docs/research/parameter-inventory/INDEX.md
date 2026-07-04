# Parameter inventory — the complete decision-parameter surface

**Status:** Reference (auto-extracted) · **Date:** 2026-07-04

Every `tunable()` in the system in one readable place — **136 parameters across 18 files** — with
each one's default, bounds, unit, and recorded justification.

- **[parameter-inventory.md](parameter-inventory.md)** — the full per-agent tables, split into
  *decision-shaping* (analyst, provider, scanner, PM, monitor, forecaster, execution, curator,
  researcher) and *plumbing / infra* (operator, master, reporter, supervisor, kernel configs).

**Why it exists:** the parameters are scattered across 18 settings files with no single view, so any
discussion of "what shapes a decision" naturally surfaces some and forgets the rest. This is the
manual stand-in until **CI-1** (ADR-0013 / S90) generates it automatically via `describe_all()`.

**Consuming work:** [ADR-0013](../../decisions/0013-continuous-improvement-system.md) (CI-1 catalogue),
the Experimentation charter (these are the tunables it sweeps), and the Deliberation primitive (a
debate argues over these values for a given decision).

**Caveat:** a point-in-time snapshot — regenerate (see the doc's foot) after adding/retiring a
`tunable()`; CI-1 makes the regeneration automatic and drift-proof.
