# Agent cross-import -- reports

**Query:** `AgentCrossImport.ql` -- flags any agent importing a different agent.
**Architecture rule:** agents are islands; they talk only via typed messages on
the bus, never by importing each other.

---

## Latest result -- start here

| File | Answers |
| --- | --- |
| [latest/report.md](latest/report.md) | What is the current violation count? Is the boundary clean? |
| [latest/results.sarif](latest/results.sarif) | Machine-readable copy for GitHub Security / VS Code SARIF Viewer |

These two files are overwritten on every run.

---

## Archived scans -- history

Each run creates a subfolder under `archive/` named `yyyy-MM-dd-HH.mm`.
These are never overwritten -- use them to compare results across scans.

| Run | Findings | Notes |
| --- | --- | --- |
| [archive/2026-06-23-17.47/](archive/2026-06-23-17.47/) | 0 | Existing database |
| [archive/2026-06-23-17.45/](archive/2026-06-23-17.45/) | 0 | Fresh database rebuild |
| [archive/2026-06-23-17.36/](archive/2026-06-23-17.36/) | 0 | Fresh database rebuild |

Each archive subfolder contains `report.md` and `results.sarif`.

---

Back to [reports INDEX](../INDEX.md).
