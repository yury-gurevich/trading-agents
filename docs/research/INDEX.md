# Research index — external tools and libraries under evaluation

**How to use:** before investigating a third-party tool or library, check the "Answers" column.
If your question is there, the research is already done — read the linked document for
findings and the integration plan instead of re-deriving them. If the status is ✅ Adopted,
look in the "Outcome" column for the ADR or sprint it produced.

| # | Title | Date | Status | Answers | Outcome | Tags |
| --- | --- | --- | --- | --- | --- | --- |
| [R001](qlib-integration/) | Microsoft Qlib — integration vision | 2026-06-19 | 🚧 In progress | Can this project benefit from qlib? Which agents, which components, in what order? | Phase Q1 active — **S58** forecaster `lightgbm`-direct shadow runtime (pyqlib is 3.13-incompatible) → **S59** booster training + price-return IC scorecard; Q2–Q4 later | `qlib` `forecaster` `analyst` `portfolio_manager` `researcher` `ml` `backtesting` |
| [R002](db-placement/) | DB placement — substrate registry vs trading-pack provenance | 2026-06-23 | 📋 Active | What DB does the substrate need? What does AuraDB Free cover? What Azure free-tier DB options exist? Which graph/vector alternatives? | ADR + sprint pending | `neo4j` `cosmos-db` `substrate` `trading-pack` `graph` `vector` `platform` |

## Folder structure — read this before adding an entry

**Every research item is its own folder** under `docs/research/<slug>/`, containing:

- an **`INDEX.md`** — the folder's landing page (one-paragraph summary, status, links to the
  doc(s), what it answers, and the consuming decisions/outcome); and
- the **research document(s)** and any companion assets (diagrams, data extracts, sub-analyses).

A folder may hold a single doc (e.g. `db-placement/`, `qlib-integration/`) or a collection of
related files (e.g. `cloud-free-tiers/` — three provider catalogs). It always has an `INDEX.md`,
because the project rule is: *read a folder's `INDEX.md` before opening files inside it.*

| Folder | Kind | What's in it |
| --- | --- | --- |
| [qlib-integration/](qlib-integration/INDEX.md) | R001 | Microsoft Qlib integration vision. |
| [db-placement/](db-placement/INDEX.md) | R002 | Substrate vs trading-pack DB placement. |
| [cloud-free-tiers/](cloud-free-tiers/INDEX.md) | Reference | AWS/GCP/Azure always-free service catalogs (feeds R002 / DL-15). |
| [parameter-inventory/](parameter-inventory/INDEX.md) | Reference | Every `tunable()` (133 params, 18 files) with defaults/bounds/why — the decision-parameter surface; manual stand-in for CI-1. |

R-numbered folders are formal research docs tracked in the table above; reference folders are
imported/supporting material without an R-number.

## Status legend

- 📋 Active — research complete; integration phases defined but not yet started
- 🚧 In progress — integration work underway in a sprint
- ✅ Adopted — led to an ADR or shipped sprint; outcome column names it
- 🗄️ Archived — evaluated and not proceeding; document preserved for context

## Adding a new research document

1. Next number is `R003`.
2. Create a **folder** `docs/research/<slug>/` (not a loose file). Put the document at
   `<slug>/<slug>.md`, opening with the standard header block:

   ```text
   # Research: <Tool/Topic> — <subtitle>

   **Status:** Research complete · **Date:** YYYY-MM-DD · **Author:** ...
   **Audience:** Product owner, planning agents, coding agents
   **Source:** <URL or citation>
   ```

3. Add an **`<slug>/INDEX.md`** landing page: one-paragraph summary, status, link to the doc(s),
   what it answers, and the consuming decision/outcome.
4. Add a row to the table above (link to the folder) **and** a row to the Folder-structure table —
   the "Answers" column is the most important field.
5. If research leads to an ADR, set status ✅ Adopted and link the ADR in "Outcome."
6. If research leads to a sprint, update "Outcome" with the sprint number and set status 🚧 In progress.
