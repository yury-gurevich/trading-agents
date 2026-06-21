# Design log — in-flight discussions, options, and what we ruled out

The home for design reasoning **before** it hardens into an ADR. Captures the question, the
options weighed (including the ones rejected and *why*), and the current status. This is the
LAW-05 ("every choice has a recorded why") and LAW-01 ("everything is a proposal") record for
threads that are discussed but not yet decided. When an entry resolves, it graduates to an ADR
and is marked CLOSED here.

---

## DL-01 · Primary organizing lens for `ops/`  ·  status: OPEN

**Question.** A filesystem is one tree, so the `ops/` realm can show only one organizing lens
as folders. Which is primary?

| Lens | Organizes by | Residency appears as |
| --- | --- | --- |
| Departmental | who owns / escalation | a GRC concern |
| DataCentre | kind of resource (compute/network/storage) | an attribute (region property) |
| **Lifecycle** | when in the process (build→deploy→operate→recover→retire) | a gate in the flow |

**Key insight (keep regardless of choice).** These are **views, not rival taxonomies.** The
*atoms* (the OIDC app, the Aura instance, a gate) are lens-independent; only the grouping
changes. Pick one lens for the folder tree; express the others as view-indexes now and **Neo4j
queries later** (one graph, project any view). This is a strong argument for modelling `ops/`
in the graph.

**Ruled out.** Committing the tree to one lens *permanently* (violates LAW-01). The current
`departments/` layout is provisional.

**Status.** Operator leaned **Lifecycle** (interrupted before confirming). Not final. Decide
before filling the remaining charters, so they're filed under the right primary lens.

---

## DL-02 · Data-residency: governing gate vs infrastructure attribute  ·  status: OPEN

**Question.** Is residency a **gate** that can block any operation, or an **attribute** of the
infra layer?

- **Option A — governance gate (GRC owns it).** Every deploy/data-move passes a residency check
  first. ✅ provable to a regulator (LAW-05); wrong-region move is structurally impossible.
  ❌ extra ceremony per region-touching action.
- **Option B — infra attribute (region property).** ✅ simpler, fewer gates, matches the
  DataCentre lens. ❌ residency becomes implicit/scattered; nothing *stops* a non-compliant
  move; "prove why here?" is manual and audit-risky.

**Recommendation on record.** **Option A** — financial data with tax-jurisdiction exposure; the
cost of an undefendable region is high. Note the lens choice (DL-01) tugs this: DataCentre→B,
Departmental/Lifecycle-with-GRC→A.

**Status.** Operator leaned **Option A** (interrupted before confirming). Not final.

---

## DL-03 · Multi-tenant residency model — the three-plane decomposition  ·  status: DRAFT (not decided)

The most important architectural idea from the 2026-06-21 platform discussion. Captured so it
is not lost; **not committed** — there are no real clients yet.

**The unlock — classify data by *who it is about*:**

| Tier | Examples | About | Residency? |
| --- | --- | --- | --- |
| Operational | master registry, identity, grants, sessions | the system | none — central |
| Reference/market | OHLCV, news, fundamentals, the universe | instruments | none — global |
| Signal/model | scores, forecasts, regime, model artifacts | instruments | none — global |
| Client-personal | KYC, PII, identity | the client | **strictly zoned** |
| Client-financial | positions, orders, fills, P&L, broker links | the client | **zoned + retention** |

Only the bottom two rows carry a jurisdiction. Everything that makes it a *trading* system is
about stocks, not people.

**Falls onto the 12 agents as three planes:**
- **Signal plane** (scanner · analyst · forecaster · provider) — market signals about
  instruments → **global, shared, one instance, cheap.**
- **Client plane** (portfolio_manager · execution · monitor · reporter) — applies signals to a
  *client's* portfolio → **the only part that gets zoned**, deployed per residency zone.
- **Control plane** (master · operator · supervisor · curator · researcher) — orchestration →
  **central "home" region.**

**Consequences / sub-points:**
- "Spin up an EU zone" = the `ta` deploy framework run with `--region=eu` against an EU graph.
  The multi-region topology *is* the ops framework parameterised by zone.
- **Compute follows data:** processing is itself a transfer (GDPR), so client-plane agents must
  *run* in the zone of the data they touch — not just store there.
- **Aggregation:** zones report anonymized aggregates upward; the centre sees money, never people.
- **Residency is 3 strands** that can point to different countries for one person:
  data-protection (where privacy law applies — extraterritorial, e.g. GDPR follows EU residents),
  tax (CRS/FATCA reporting + retention), regulatory (which financial regulator governs the
  service). The onboarding "interview" must capture them separately; the data domicile is
  derived to satisfy the **strictest intersection**; if none lawful → **decline the client.**

**Ruled out (implicitly).** One global graph for all clients (fails residency); full
stack-per-zone for the *entire* fleet (needless cost — only the client plane needs zoning).

**Status.** DRAFT model, deferred until real clients. **The constraint to protect now:** do not
build a single-tenant data model that can't partition by residency zone later. Graduate to an
ADR ("tenant-partitioned by residency zone; domicile policy-derived at onboarding") when the
data model is next touched.

---

## DL-04 · Model `ops/` in Neo4j as a multi-view engine  ·  status: IDEA (later)

Per DL-01: tag each operational atom once (`Subsystem`/`Gate`/`Runbook`, `DEPENDS_ON`/`AFFECTS`),
then query any lens (departmental / datacentre / lifecycle) and run change-impact ("what breaks
if I touch X?"). Seed from the markdown charters first; graduate to the graph when they stabilise.
