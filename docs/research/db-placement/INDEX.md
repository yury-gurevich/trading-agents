# R002 · DB placement — substrate registry vs trading-pack provenance

**Status:** 📋 Active · **Date:** 2026-06-23

Where should the substrate registry and the trading-pack provenance graph each live?

- **[db-placement.md](db-placement.md)** — full capability mapping: AuraDB Free limits, Azure
  free-tier DB options, graph/vector alternatives, and the recommended placement.

**Answers:** What DB does the substrate need? What does AuraDB Free cover? What Azure free-tier DB
options exist? Which graph/vector alternatives?

**Consuming decisions:** `docs/design-log.md` **DL-15** (substrate should not use Neo4j → Azure
Cosmos DB free is the candidate). Provider free-tier figures live in
[../cloud-free-tiers/](../cloud-free-tiers/INDEX.md).

**Outcome:** ADR + sprint pending.
