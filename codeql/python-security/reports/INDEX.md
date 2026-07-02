# CodeQL scan reports -- index

Each CodeQL query has its own subfolder. Inside each query folder:

- `latest/` -- overwritten on every run; always reflects the most recent scan.
- `archive/<timestamp>/` -- one subfolder per run, never overwritten; for history.
- `INDEX.md` -- query-specific index listing every archived run.

**Start here:** pick a query. If it already has a generated `latest/report.md`, open that;
otherwise run the query from the query-specific index first.

---

## Query folders

| Folder | Query file | Answers |
| --- | --- | --- |
| [agent-cross-import/](agent-cross-import/INDEX.md) | `AgentCrossImport.ql` | Does any agent import another agent? (architecture boundary) |
| [taint-tracking/](taint-tracking/INDEX.md) | `TaintTracking.ql` | Does untrusted input reach `urlopen` without validation? (SSRF / URL injection) |

---

## How to generate a new report

```powershell
# Agent cross-import boundary (rebuild database from current source):
.\scripts\run_codeql_agent_boundary.ps1 -Rebuild

# Same query, reuse existing database:
.\scripts\run_codeql_agent_boundary.ps1
```

## How to clean up old reports

```powershell
# Keep only the 10 most recent archives per query:
.\scripts\clean_codeql_reports.ps1 -KeepNewest 10

# Delete archives older than 30 days:
.\scripts\clean_codeql_reports.ps1 -OlderThanDays 30

# Preview deleting all archives (keeps latest/):
.\scripts\clean_codeql_reports.ps1 -AllArchives -WhatIf
```

See [codeql/python-security/README.md](../README.md) for full documentation of
the query pack, configuration choices, and file layout.
