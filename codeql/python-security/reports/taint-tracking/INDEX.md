# Taint tracking (SSRF / URL injection) -- reports

**Query:** `TaintTracking.ql` -- tracks untrusted input (MCP tool args, CLI
arguments, environment variables) flowing into `urllib.request.urlopen`
without validation against an allow-list of hosts.

---

## Latest result

No taint-tracking report has been generated yet; `latest/` is intentionally empty.
After the first run, this folder should contain:

| File | Answers |
| --- | --- |
| `latest/report.md` | What is the current taint flow count? Is any untrusted URL reaching urlopen? |
| `latest/results.sarif` | Machine-readable copy for GitHub Security / VS Code SARIF Viewer |

Run from the repo root:

```powershell
.\codeql\scripts\run_codeql_agent_boundary.ps1 -Query codeql\python-security\TaintTracking.ql -OutputDir codeql\python-security\reports\taint-tracking -Rebuild
```

These two files are overwritten on every run.

---

## Archived scans -- history

Each run creates a subfolder under `archive/` named `yyyy-MM-dd-HH.mm`.
These are never overwritten -- use them to compare results across scans.

| Run | Findings | Notes |
| --- | --- | --- |
| _(none yet)_ | | |

Each archive subfolder contains `report.md` and `results.sarif`.

---

Back to [reports INDEX](../INDEX.md).
