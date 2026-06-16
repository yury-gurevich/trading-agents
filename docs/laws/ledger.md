# The landscape — gray → green ledger

The single board for "do we KNOW it works." A row is **green** only when every non-deprecated law in
that scope has ≥ 1 passing functional test citing its ID, and its dependencies are green
(conventions §3). Everything starts **gray** (written in hope) and earns green (proven).

Legend: ⬜ gray (unproven) · 🟩 green (proven) · 🟨 partial · ⛔ blocked by a gray dependency.

## Layer 0 — Dependencies (must go green first)

| Component | Clauses | Status |
| --- | --- | --- |
| DEP-CONFIG | 2 | ⬜ |
| DEP-CLOCK | 1 | ⬜ |
| DEP-NEO4J | 3 | ⬜ |
| DEP-BUS | 3 | ⬜ |
| DEP-FEED | 3 | ⬜ |
| DEP-BROKER | 2 | ⬜ |
| DEP-LLM | 2 | ⬜ |
| DEP-TELE | 2 | ⬜ |

## Layer 1 — Agents

| Agent | Laws authored? | Clauses green / total | Status |
| --- | --- | --- | --- |
| provider | ✅ v0 (draft) | 0 / — | ⬜ template stress-test |
| scanner | — | — | ⬜ |
| analyst | — | — | ⬜ |
| forecaster | — | — | ⬜ |
| portfolio_manager | — | — | ⬜ |
| execution | — | — | ⬜ |
| monitor | — | — | ⬜ |
| reporter | — | — | ⬜ |
| researcher | — | — | ⬜ |
| curator | — | — | ⬜ |
| operator | — | — | ⬜ |
| supervisor | — | — | ⬜ |

## Layer 2 — Choreography

Every edge in [`flow.md`](flow.md) type-aligned and proven on a real run. ⬜

## Layer 3 — Acceptance

One full paper-trading day on real S&P 500 data, persisted, with each agent's job + boundaries
asserted. ⬜ — this row turning 🟩 is the definition of "the system works."
