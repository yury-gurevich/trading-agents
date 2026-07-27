# R007 · Ontology guardrails (RDFS / OWL) for the agent loop

**Status:** 🗄️ Archived (evaluated — the reasoner is ruled out permanently on the current
evidence-store architecture; the constraint half is recommended in plain Python) ·
**Date:** 2026-07-27

Should this platform tether its agent loop to a formal ontology (W3C RDFS/OWL), as argued in
Frank Coyle's *"Why Agentic Systems Need Ontologies"* (AI Engineer World's Fair 2026)?
**Answer: take "OWL constrains", refuse "RDFS infers."** The constraint half is worth ~100 lines
of first-party Python; the inference half is architecturally incompatible with LAW-02 and should
not be adopted at all.

**The finding that justifies acting.** `labels_owned` / `labels_read` are declared in **eight**
agents' law files and read by **no code whatsoever** (zero `.py` hits). An ownership ontology was
already authored here and never wired — the fourth instance in a single day of the DL-65 pattern,
*a guard can be present, documented, and still not guard*.

**Why the reasoner is refused.** A reasoner asserts facts nobody observed. Every expensive bug this
month was an unasserted fact treated as fact — a `CloseDecision` read as evidence of closure
(DL-60, four stranded positions), `pnl_cents` computed at decision time (0.74.03). Adding inference
to an append-only *evidence* store would industrialise that failure mode.

**Not watched.** No transcript is published; the talk's argument is reconstructed from its title,
published thesis, and one operator-supplied slide. Everything measured against this repo carries
its own evidence and is not reconstructed.

- **[ontology-guardrails.md](ontology-guardrails.md)** — full evaluation: the claim, what the
  platform already has, the `labels_owned` gap, a device-by-device value table, why inference is
  refused, the recommended constraint-only subset, what is ruled out, and revisit triggers.
