/**
 * @name Agent-to-agent import violation
 * @description Agents must not import other agents. Each agent is an island,
 *              joined only by the shared `contracts` vocabulary and the
 *              plumbing `kernel`. The .importlinter `independence` contract
 *              enforces this at CI time; this query provides the same check as
 *              a CodeQL problem query with precise source locations.
 * @kind problem
 * @id local/py/agent-cross-import
 * @problem.severity error
 * @precision very-high
 * @tags architecture maintainability
 */

import python

// ---------------------------------------------------------------------------
// The 12 independent agent packages (from .importlinter:contract:agents-are-islands).
// `master` is deliberately excluded - it is not in the independence contract.
// ---------------------------------------------------------------------------

from
  Import imp,
  string importedModule,
  string importedAgent,
  string importingFile,
  string importingAgent
where
  importingFile = imp.getLocation().getFile().getRelativePath() and
  importingFile.matches("agents/" + importingAgent + "/%") and
  importingAgent in [
    "provider", "scanner", "analyst", "forecaster", "portfolio_manager",
    "execution", "monitor", "reporter", "researcher", "curator",
    "operator", "supervisor"
  ] and
  importedModule = imp.getAnImportedModuleName() and
  importedModule.matches("agents.%") and
  importedAgent = importedModule.regexpCapture("agents\\.([^.]+)", 1) and
  importedAgent in [
    "provider", "scanner", "analyst", "forecaster", "portfolio_manager",
    "execution", "monitor", "reporter", "researcher", "curator",
    "operator", "supervisor"
  ] and
  // Exclude test files - tests legitimately wire agents together.
  not importingFile.matches("%/tests/%") and
  // The violation: importing a *different* agent.
  importedAgent != importingAgent
select imp,
  "Agent '" + importingAgent + "' imports agent '" + importedAgent +
    "' - agents must be independent (talk only via messages on the bus)."
