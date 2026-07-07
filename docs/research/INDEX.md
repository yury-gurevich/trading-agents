# Research index — external tools and libraries under evaluation

**How to use:** before investigating a third-party tool or library, check the "Answers" column.
If your question is there, the research is already done — read the linked document for
findings and the integration plan instead of re-deriving them. If the status is ✅ Adopted,
look in the "Outcome" column for the ADR or sprint it produced.

| # | Title | Date | Status | Answers | Outcome | Tags |
| --- | --- | --- | --- | --- | --- | --- |
| [R001](qlib-integration/) | Microsoft Qlib — integration vision + workflow addendum | 2026-06-19 | ✅ Adopted | Can this project benefit from qlib? Which agents, which components, which *workflows*, in what order? | **All planned phases shipped** — Q1 (S58–S59), Q2 (S68), Q1b (S110), Q1c (S111), Q3 (S112), **Q5 A+B (S113 0.57.00 + S115 0.58.00: the governed factor-mining loop is CLOSED, Moonshot #3)**. Only Q4 remains, parked behind its 60-day live-data prerequisite | `qlib` `forecaster` `analyst` `portfolio_manager` `researcher` `ml` `backtesting` |
| [R002](db-placement/) | DB placement — substrate registry vs trading-pack provenance + **Postgres migration plan** | 2026-06-23 | 🚧 In progress | What DB does the substrate need? What does AuraDB Free cover? Which graph/vector alternatives? **How do we move the spine to PostgreSQL?** | **DL-43 (2026-07-06):** Postgres = system of record, Neo4j = ad-hoc analysis workbench; plan in `postgres-migration-plan.md`; S116–S118 defined (S116 after S115); ADR-0001 supersede at S117 | `postgres` `pgvector` `neo4j` `substrate` `spine` `graph` `vector` `platform` |
| [R003](textgrad/) | TextGrad — textual-gradient optimization for continuous improvement | 2026-07-03 | 🗄️ Archived | What is TextGrad vs DSPy? Should it join the optimizer stack now? What would make it worth adopting later? | Not adopted — stays the ADR-0010 bake-off candidate behind the `PromptOptimizer` port; revisit triggers named in the doc | `textgrad` `dspy` `prompt-optimization` `adr-0010` `continuous-improvement` |
| [R004](a2a-boundary/) | A2A (Agent2Agent) — interop standard, boundary only | 2026-07-04 | 🗄️ Archived | How closely do we follow A2A standards/best practice? Should A2A replace any internal mechanism? When/how would compatibility be added? | Not adopted internally (permanent on current architecture — convergent principles, stronger enforcement). Future: A2A front-door adapter in `surfaces/` (MCP-surface pattern) behind named triggers | `a2a` `interop` `surfaces` `mcp` `adr-0012` `platform` |

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
| [textgrad/](textgrad/INDEX.md) | R003 | TextGrad evaluated for continuous improvement — not adopted; ADR-0010 bake-off candidate. |
| [a2a-boundary/](a2a-boundary/INDEX.md) | R004 | A2A interop standard — convergent principles, no internal adoption; boundary adapter behind triggers. |
| [cloud-free-tiers/](cloud-free-tiers/INDEX.md) | Reference | AWS/GCP/Azure always-free service catalogs (feeds R002 / DL-15). |
| [parameter-inventory/](parameter-inventory/INDEX.md) | Reference | Every `tunable()` (133 params, 18 files) with defaults/bounds/why — the decision-parameter surface; manual stand-in for CI-1. |
| [quant-methods/](quant-methods/INDEX.md) | Reference | What each quant signal *measures*, why it matters, how to read it + uncovered areas + deterministic params to raise prediction confidence. |
| [experiments/](experiments/INDEX.md) | Log | Research-probe experiments (purpose · process · delivery · interpretation). EXP-001 = do the LLMs understand our parameters (gpt-5.4 vs 5.5). |

R-numbered folders are formal research docs tracked in the table above; reference folders are
imported/supporting material without an R-number.

## Status legend

- 📋 Active — research complete; integration phases defined but not yet started
- 🚧 In progress — integration work underway in a sprint
- ✅ Adopted — led to an ADR or shipped sprint; outcome column names it
- 🗄️ Archived — evaluated and not proceeding; document preserved for context

## Adding a new research document

1. Next number is `R005`.
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
