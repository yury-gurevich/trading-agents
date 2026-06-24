# CodeQL Agent Cross-Import Boundary Check

Custom CodeQL query that enforces the core architecture rule of this repo:
**no agent may import another agent**. Agents are islands, joined only by the
shared `contracts` vocabulary and the plumbing `kernel`.

---

## Quick start

```powershell
# Rebuild the database from current source, run the query, generate the report:
.\codeql\scripts\run_codeql_agent_boundary.ps1 -Rebuild

# Run against the existing database (no rebuild):
.\codeql\scripts\run_codeql_agent_boundary.ps1
```

The report opens at:

```text
codeql\python-security\reports\agent-cross-import\latest\report.md
```

---

## Components

### 1. The query — `codeql/python-security/AgentCrossImport.ql`

A `.ql` file written in the CodeQL query language (a Datalog-like logic
language). It is a `@kind problem` query — each matching import statement
produces one finding with a precise file:line location.

**What it checks:**

For every `import` statement in a file under `agents/<agent_name>/`, the query
extracts:

1. The **importing agent** — the agent package the importing file belongs to
   (parsed from the file path: `agents/execution/agent.py` → `execution`).
2. The **imported agent** — the second path segment of the imported module
   (`agents.provider.sources` → `provider`).

A finding is raised when `importedAgent != importingAgent` — i.e. one agent
reaches into another agent's package.

**What it does NOT flag:**

- Same-agent imports (`agents/execution/agent.py` importing
  `agents/execution/broker.py`) — these are internal to one agent and allowed.
- Imports of `kernel`, `contracts`, `orchestration`, or `surfaces` — agents
  may import any layer below them.
- `agents/master` — deliberately excluded because it is not in the
  `.importlinter` independence contract (it is a control-plane agent, not a
  pipeline agent).

### 2. The qlpack — `codeql/python-security/qlpack.yml`

```yaml
name: local/python-security
version: 0.0.1
dependencies:
  codeql/python-all: "*"
```

This is the **pack manifest**. It declares that our custom queries depend on
`codeql/python-all` (the standard Python CodeQL library). Without this file,
the CodeQL CLI cannot resolve the `import python` statement in the query.

### 3. The runner script — `codeql/scripts/run_codeql_agent_boundary.ps1`

A PowerShell script that automates the full pipeline:

| Step | What it does |
| --- | --- |
| Step 0 (optional) | Rebuild the CodeQL database from current source (`-Rebuild` flag) |
| Step 1 | Run the query against the database (`codeql database run-queries`) |
| Step 2 | Decode the binary `.bqrs` results to CSV + generate SARIF (`codeql database interpret-results`) |
| Step 3 | Parse the CSV and generate a human-readable markdown report |

**Parameters:**

| Parameter | Default | Description |
| --- | --- | --- |
| `-Rebuild` | (switch) | Rebuild the database from current source before running |
| `-Database` | `.codeql-db\python` | Path to the CodeQL database |
| `-Query` | `codeql\python-security\AgentCrossImport.ql` | Path to the query file |
| `-SearchPath` | `codeql\python-security` | CodeQL pack search path |
| `-OutputDir` | `codeql\python-security\reports\agent-cross-import` | Where to write report and SARIF |

**Exit codes:**

- `0` — clean, no violations found
- `1` — violations found (prints each one to console)

**Output files (per run):**

| File | Format | Purpose |
| --- | --- | --- |
| `latest\report.md` | Markdown | Latest report — always overwritten, easy to link |
| `latest\results.sarif` | SARIF 2.1.0 | Latest SARIF — always overwritten |
| `archive\yyyy-MM-dd-HH.mm\report.md` | Markdown | Timestamped archive — one per run, preserved for history |
| `archive\yyyy-MM-dd-HH.mm\results.sarif` | SARIF 2.1.0 | Timestamped archive |

All paths are relative to the query folder, e.g.
`codeql\python-security\reports\agent-cross-import\latest\report.md`.

### 4. The cleanup script — `codeql/scripts/clean_codeql_reports.ps1`

A PowerShell script that deletes archived reports to keep the reports folder
from growing without bound.

**Modes (pick one):**

| Mode | What it does |
| --- | --- |
| `-KeepNewest N` | Keep the N most recent archive subfolders per query; delete the rest |
| `-OlderThanDays N` | Delete archive subfolders older than N days |
| `-AllArchives` | Delete every archive subfolder (keeps `latest/`) |
| `-Everything` | Delete all report and SARIF files (keeps `INDEX.md`) |

Add `-WhatIf` to any mode to preview without deleting.

**Examples:**

```powershell
# Keep only the 10 most recent archives per query:
.\codeql\scripts\clean_codeql_reports.ps1 -KeepNewest 10

# Delete archives older than 30 days:
.\codeql\scripts\clean_codeql_reports.ps1 -OlderThanDays 30

# Preview deleting all archives:
.\codeql\scripts\clean_codeql_reports.ps1 -AllArchives -WhatIf

# Wipe everything (keep INDEX.md files only):
.\codeql\scripts\clean_codeql_reports.ps1 -Everything
```

### 5. The CodeQL database — `.codeql-db/python`

A CodeQL database is an extracted, indexed representation of the source code.
It is **not** a live database — it is a snapshot. To scan new code, you must
rebuild it with `-Rebuild`.

The database is built by:

```text
codeql database create .codeql-db\python --language=python --source-root=. --overwrite
```

This indexes all `.py` files in the repo (698 modules) and produces a binary
relational database that the query engine can search.

---

## Configuration choices — what we changed from defaults and why

### Test files excluded from the check

**Default:** CodeQL queries scan every file in the database, including tests.

**Our choice:** The query includes `not importingFile.matches("%/tests/%")`
to exclude all test files.

**Why:** Test files legitimately wire multiple agents together for integration
tests. The architecture rule is about production code — agents must be
independent at runtime, not in test fixtures. Without this exclusion the query
would produce 71 findings, all in test helpers like
`agents/reporter/tests/p3_helpers.py` that import `analyst`, `execution`,
`monitor`, `provider`, `scanner` etc. to set up end-to-end test scenarios.

### `agents/master` excluded from the agent list

**Default:** The query lists 12 agent packages to check.

**Our choice:** `master` is not in the list.

**Why:** `master` is a control-plane agent (secret management, HTTP server,
grant policy) — it is not part of the pipeline independence contract defined in
`.importlinter:contract:agents-are-islands`. The import-linter contract
deliberately omits it, and the CodeQL query mirrors that decision.

### `@kind problem` instead of `@kind path-problem`

**Default:** Security queries are often `@kind path-problem` (taint-tracking
with source-to-sink paths).

**Our choice:** This query is `@kind problem` — a simple yes/no check per
import statement, no path tracking.

**Why:** This is an architecture rule, not a data-flow analysis. We do not
need to trace how data moves from source to sink — we just need to know
whether an import statement crosses an agent boundary. `@kind problem` is
simpler, faster, and produces one finding per violation with a precise
file:line location.

### `@problem.severity error` (not warning)

**Default:** CodeQL architecture queries are often `warning`.

**Our choice:** `error`.

**Why:** An agent importing another agent is a hard architecture violation
that breaks the independence contract. It should fail CI, not just warn.

---

## Relationship to import-linter

This repo already has `lint-imports` (import-linter) as step 4 of the 9-step
`make ci` gate. It enforces the same rule via the `.importlinter` contract
`agents-are-islands` (type = `independence`).

**Why use CodeQL too?**

| Aspect | import-linter | CodeQL |
| --- | --- | --- |
| Speed | ~2 seconds | ~30 seconds (query compile + eval) |
| Precision | Package-level (module-to-module) | File-level (every `import` statement) |
| Output | Pass/fail text | SARIF + markdown report with file:line links |
| CI integration | Native (Python, fast) | GitHub Security tab (SARIF upload) |
| Test handling | Does not flag test-file cross-imports | Configurable (we exclude them) |

The two tools are complementary: import-linter is the fast CI gate;
CodeQL produces the auditable report with precise source locations and SARIF
for GitHub Security integration.

---

## File map

```text
codeql/python-security/
  qlpack.yml                  # Pack manifest (depends on codeql/python-all)
  AgentCrossImport.ql         # The boundary check query
  TaintTracking.ql            # SSRF taint-tracking query (separate)
  python-security.qls         # Query suite (runs stock + custom queries)
  reports/
    INDEX.md                      # Top-level index: lists all query folders
    agent-cross-import/          # AgentCrossImport.ql results
      INDEX.md                   # Per-query index (auto-updated each run)
      latest/                    # Overwritten every run
        report.md
        results.sarif
      archive/                   # One subfolder per run, never overwritten
        yyyy-MM-dd-HH.mm/
          report.md
          results.sarif
    taint-tracking/              # TaintTracking.ql results (same structure)
      INDEX.md
      latest/
      archive/

codeql/scripts/
  run_codeql_agent_boundary.ps1   # Runner script (rebuild + query + report)
  clean_codeql_reports.ps1        # Delete old reports (keep newest, by age, or all)

.importlinter                    # The import-linter contract (CI gate)

.codeql-db/python/               # The CodeQL database (built from source)
```
