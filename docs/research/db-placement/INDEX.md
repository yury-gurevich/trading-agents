# R002 · DB placement — substrate registry vs trading-pack provenance

**Status:** 📋 Active · **Date:** 2026-06-23

Where should the substrate registry and the trading-pack provenance graph each live?

- **[db-placement.md](db-placement.md)** — full capability mapping: AuraDB Free limits, Azure
  free-tier DB options, graph/vector alternatives, and the recommended placement.
- **[postgres-migration-plan.md](postgres-migration-plan.md)** — **the executable plan (2026-07-06,
  DL-43):** PostgreSQL becomes the system of record (spine + pgvector + CI-2 metrics home); Neo4j
  demoted to an ad-hoc local-Docker analysis workbench, out of the runtime. Sprint sequence
  S116 (adapter+parity) → S117 (provision+swap, absorbs S101) → S118 (rip-out).

**Answers:** What DB does the substrate need? What does AuraDB Free cover? What Azure free-tier DB
options exist? Which graph/vector alternatives? **How do we move the spine to PostgreSQL?**

**Consuming decisions:** `docs/design-log.md` **DL-15** (substrate should not use Neo4j), **DL-38**
(spine shrinks; memory bundle-declared), **DL-43** (Postgres system-of-record direction). Provider
free-tier figures live in [../cloud-free-tiers/](../cloud-free-tiers/INDEX.md).

**Outcome:** Migration plan complete (DL-43); ADR-0001 supersede scheduled for S117; sprints
S116–S118 defined, S116 packages after S115 lands.
