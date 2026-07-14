<!-- Agent: planning | Role: fix-sprint backlog -->
# S127 fixpack — issue collection

Running list of small, confirmed defects and cleanups batched for the next fix sprint.
**How it works:** anyone appends a row while the issue is fresh; the planning agent packages
S127 from this list when it justifies a sprint. One row per issue; link the evidence. Genuine
law-vs-reality drift also gets a `DRIFT-NN` row in `docs/laws/drift-register.md` — this list
then just points at it (never two full records of one issue).

| # | Kind | Issue | Evidence / pointer | Reported |
| --- | --- | --- | --- | --- |
| 1 | error | **Log drawer ignores the selected run** — always queries the latest fleet window, so run `sched-2026-07-08` shows 2026-07-13 log lines. Fix shape known: pass the selected run to `/api/containers/<name>/logs`, resolve its day from the RunRequest (`run_window` already exists; `/bundle` already does this), fall back to latest only when unscoped; label the shown window in the drawer. | **DRIFT-022**; `surfaces/dashboard/bundle_azure.py` (`container_logs` → `latest_window`) | operator, 2026-07-14 |
| 2 | cleanup | **Dead client-side summary shim** — `verdict.js compactSummary()` rewrites the old server wording, but since 0.68.03 the server already emits the compact sentence; the shim is dead code and a second wording source that can drift. Delete it once no cached pages depend on the old wording. | `surfaces/dashboard/static/verdict.js` | planning agent, 2026-07-14 |
| 3 | debt | **Quant evidence not fully persisted for deliberation** — all three roles receive the same rendered context, but the analyst `ScoreBreakdown.metrics` payload is not persisted in full into `Recommendation` / rendered by `veto_context`; full quant-signal availability unproven. Needs a typed bounded payload + a three-role capture test. May graduate to its own sprint at packaging. | S125 return notes (`docs/sprints/sprint-125-operator-chat.md`) | S125 handback, 2026-07-13 |
