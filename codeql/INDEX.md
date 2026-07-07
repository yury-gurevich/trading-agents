# CodeQL tool — folder map

Read [README.md](README.md) first for entry points and usage.

| Path | What it is |
| --- | --- |
| [README.md](README.md) | Tool overview, layout, and the command entry points |
| [scripts/](scripts/) | Management layer — setup, run-suite, agent-boundary, AST, report, clean, errors |
| [python-security/](python-security/README.md) | Query pack: agent cross-import boundary + taint tracking (has its own README) |
| [yaml-diagnostics/](yaml-diagnostics/INDEX.md) | Query pack: YAML parse-error + unresolved-include diagnostics |

## scripts/ — what each does

| Script | Purpose |
| --- | --- |
| `setup_codeql_local.ps1` | Download the CodeQL CLI + build the local DB cluster + install packs |
| `run_codeql_local_suite.ps1` | One-shot: setup/analysis then aggregate reports |
| `run_codeql_agent_boundary.ps1` | Run the agent cross-import query → readable `reports/` output |
| `run_codeql_ast.ps1` | Dump the CodeQL AST for one source file (debugging queries) |
| `generate_codeql_reports.ps1` | SARIF → triage + baseline/diff + owner markdown reports |
| `clean_codeql_reports.ps1` | Delete report runs (keep-newest / by-age / all) |
| `codeql_errors.py` | List error-level findings from the local SARIF (CI-style gate) |

## Not committed (generated)

`*.sarif`, `python-security/reports/**/{latest,archive}`, `.codeql-db/`, `.tools/codeql/` —
rebuilt on demand by the scripts above.
