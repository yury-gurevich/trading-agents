# Research index — external tools and libraries under evaluation

**How to use:** before investigating a third-party tool or library, check the "Answers" column.
If your question is there, the research is already done — read the linked document for
findings and the integration plan instead of re-deriving them. If the status is ✅ Adopted,
look in the "Outcome" column for the ADR or sprint it produced.

| # | Title | Date | Status | Answers | Outcome | Tags |
| --- | --- | --- | --- | --- | --- | --- |
| [R001](qlib-integration.md) | Microsoft Qlib — integration vision | 2026-06-19 | 🚧 In progress | Can this project benefit from qlib? Which agents, which components, in what order? | Phase Q1 active — **S58** forecaster `lightgbm`-direct shadow runtime (pyqlib is 3.13-incompatible) → **S59** booster training + price-return IC scorecard; Q2–Q4 later | `qlib` `forecaster` `analyst` `portfolio_manager` `researcher` `ml` `backtesting` |
| [R002](db-placement.md) | DB placement — substrate registry vs trading-pack provenance | 2026-06-23 | 📋 Active | What DB does the substrate need? What does AuraDB Free cover? What Azure free-tier DB options exist? Which graph/vector alternatives? | ADR + sprint pending | `neo4j` `cosmos-db` `substrate` `trading-pack` `graph` `vector` `platform` |

## Status legend

- 📋 Active — research complete; integration phases defined but not yet started
- 🚧 In progress — integration work underway in a sprint
- ✅ Adopted — led to an ADR or shipped sprint; outcome column names it
- 🗄️ Archived — evaluated and not proceeding; document preserved for context

## Adding a new research document

1. Next number is `R002`.
2. Create `<slug>.md` in this folder. Open with the standard header block:

   ```text
   # Research: <Tool/Topic> — <subtitle>

   **Status:** Research complete · **Date:** YYYY-MM-DD · **Author:** ...
   **Audience:** Product owner, planning agents, coding agents
   **Source:** <URL or citation>
   ```

3. Add a row to this table immediately — the "Answers" column is the most important field.
4. If research leads to an ADR, update the status to ✅ Adopted and link the ADR in "Outcome."
5. If research leads to a sprint, update "Outcome" with the sprint number and set status to 🚧 In progress.
