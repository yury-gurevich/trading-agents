# Research index — external tools and libraries under evaluation

**How to use:** before investigating a third-party tool or library, check the "Answers" column.
If your question is there, the research is already done — read the linked document for
findings and the integration plan instead of re-deriving them. If the status is ✅ Adopted,
look in the "Outcome" column for the ADR or sprint it produced.

| # | Title | Date | Status | Answers | Outcome | Tags |
| --- | --- | --- | --- | --- | --- | --- |
| [R001](qlib-integration.md) | Microsoft Qlib — integration vision | 2026-06-19 | 📋 Active | Can this project benefit from qlib? Which agents, which components, in what order? | Phases Q1–Q4 defined; Q1 (forecaster LightGBM shadow signal) is the recommended entry point | `qlib` `forecaster` `analyst` `portfolio_manager` `researcher` `ml` `backtesting` |

## Status legend

- 📋 Active — research complete; integration phases defined but not yet started
- 🚧 In progress — integration work underway in a sprint
- ✅ Adopted — led to an ADR or shipped sprint; outcome column names it
- 🗄️ Archived — evaluated and not proceeding; document preserved for context

## Adding a new research document

1. Next number is `R002`.
2. Create `<slug>.md` in this folder. Open with the standard header block:
   ```
   # Research: <Tool/Topic> — <subtitle>

   **Status:** Research complete · **Date:** YYYY-MM-DD · **Author:** ...
   **Audience:** Product owner, planning agents, coding agents
   **Source:** <URL or citation>
   ```
3. Add a row to this table immediately — the "Answers" column is the most important field.
4. If research leads to an ADR, update the status to ✅ Adopted and link the ADR in "Outcome."
5. If research leads to a sprint, update "Outcome" with the sprint number and set status to 🚧 In progress.
