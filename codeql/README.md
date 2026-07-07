# CodeQL — local static-analysis tool

Self-contained CodeQL capability for this repo: the custom **query packs**, the
**management scripts** that run them, and the generated reports. Everything CodeQL lives
under `codeql/`; nothing CodeQL-specific belongs in the general `scripts/` tree.

## Layout

```text
codeql/
├── README.md              # this file — the tool overview + entry points
├── INDEX.md               # folder map
├── scripts/               # the management layer (run / report / clean / setup)
├── python-security/       # query pack — agent cross-import + taint tracking (see its README)
└── yaml-diagnostics/      # query pack — YAML parse-error + unresolved-include diagnostics
```

Generated outputs (`*.sarif`, `reports/**/latest|archive`, the local `.codeql-db/` and the
downloaded CLI under `.tools/`) are **not committed** — they are rebuilt by the scripts.

## Entry points

| Task | Command (run from repo root) |
| --- | --- |
| Install the CodeQL CLI + packs | `pwsh codeql/scripts/setup_codeql_local.ps1` |
| Run the full local suite (python/yaml/actions) | `pwsh codeql/scripts/run_codeql_local_suite.ps1 -Rebuild` |
| Run the **agent-boundary** check + report | `pwsh codeql/scripts/run_codeql_agent_boundary.ps1 -Rebuild` |
| Run the AST helper on one file | `pwsh codeql/scripts/run_codeql_ast.ps1 -SourceFile <path>` |
| Aggregate SARIF → markdown reports | `pwsh codeql/scripts/generate_codeql_reports.ps1` |
| List error-level findings | `python codeql/scripts/codeql_errors.py` |
| Clean old reports | `pwsh codeql/scripts/clean_codeql_reports.ps1 -KeepNewest 10` |

The scripts resolve the repo root as `$PSScriptRoot\..\..` — they must stay two levels
under the root (i.e. directly in `codeql/scripts/`).

## The packs

- **`python-security/`** — enforces the core architecture rule *no agent imports another
  agent* (`AgentCrossImport.ql`) plus taint tracking. See `python-security/README.md`.
- **`yaml-diagnostics/`** — surfaces YAML parse errors and unresolved includes in workflow
  files (`parse-errors.ql`, `unresolved-includes.ql`).
