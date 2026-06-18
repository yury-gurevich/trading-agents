# CodeQL Local Tooling Guide

Last verified: 2026-06-18 21:47 (local)

## Purpose

This guide explains the local CodeQL workflow in this repository, where data is stored, what each script does, and how to run it end to end.

## Grand View

The local workflow has four stages:

1. Install or reuse the local CodeQL CLI in the repository.
2. Build a local multi-language CodeQL database cluster from repository source code.
3. Run CodeQL analyses for the supported languages tracked in this repository.
4. Generate human-readable and machine-readable reports across all produced SARIF files.

This gives a repeatable local security-analysis loop independent of the GitHub Actions UI.

## Local Database And Artifacts Locations

Primary local database cluster:

- .codeql-db/all-languages

Language subdatabases:

- .codeql-db/all-languages/python
- .codeql-db/all-languages/yaml
- .codeql-db/all-languages/actions

Primary scan outputs:

- .codeql-db/python-security-and-quality.sarif
- .codeql-db/actions-code-scanning.sarif

YAML analysis note:

- The YAML subdatabase is created by default, but CodeQL 2.25.6 does not successfully execute local queries against that finalized YAML dataset in this repository, so `.codeql-db/yaml-code-scanning.sarif` is not produced by the default workflow.

Generated reports:

- .codeql-db/reports/codeql-current-report.md
- .codeql-db/reports/codeql-diff-report.md
- .codeql-db/reports/codeql-owner-report.md
- .codeql-db/reports/codeql-snapshot.json
- .codeql-db/reports/baseline-findings.json

Local CodeQL CLI install location:

- .tools/codeql

## Scripts Added

1) scripts/setup_codeql_local.ps1

What it does:

- Downloads the CodeQL CLI if it is missing.
- Creates the default database cluster at .codeql-db/all-languages.
- Builds the `python`, `yaml`, and `actions` subdatabases by default.
- Downloads the stock query packs needed for Python and GitHub Actions.
- Runs Python security-and-quality and the default GitHub Actions query pack.
- Skips YAML query execution with an explicit message because local CodeQL 2.25.6 fails to query the finalized YAML dataset.
- Produces SARIF for Python and GitHub Actions.

Typical usage:

- powershell -ExecutionPolicy Bypass -File scripts/setup_codeql_local.ps1 -Rebuild

Key parameters:

- -Languages: Overrides the default language set (`python`, `yaml`, `actions`).
- -Rebuild: Deletes and rebuilds the local database cluster.
- -SkipAnalyze: Creates the database cluster only and skips query analysis.
- -CodeQLTag: Overrides the CodeQL CLI release tag.

1) scripts/generate_codeql_reports.ps1

What it does:

- Reads one or more SARIF results.
- Aggregates findings across all supplied languages.
- Builds a current triage report.
- Builds an owner-grouped report by top-level folder.
- Builds a baseline diff report with added, resolved, and unchanged findings.
- Writes snapshot JSON and optionally updates baseline JSON.

Typical usage:

- powershell -ExecutionPolicy Bypass -File scripts/generate_codeql_reports.ps1 -UpdateBaseline

Key parameters:

- -SarifPath: One or more custom SARIF input paths.
- -OutputDir: Custom report output folder.
- -BaselinePath: Custom baseline JSON path.
- -UpdateBaseline: Refreshes the baseline from the current aggregated snapshot.

1) scripts/run_codeql_local_suite.ps1

What it does:

- Orchestrates setup, analysis, and aggregated report generation in one command.
- Uses the same default language set as `scripts/setup_codeql_local.ps1`.
- Optionally rebuilds the database cluster and updates the baseline.
- Aggregates the SARIF files that actually exist, so the current default report set covers Python and GitHub Actions.

Typical usage (full run):

- powershell -ExecutionPolicy Bypass -File scripts/run_codeql_local_suite.ps1 -Rebuild -UpdateBaseline

Fast usage (reports only from existing SARIF files):

- powershell -ExecutionPolicy Bypass -File scripts/run_codeql_local_suite.ps1 -SkipSetup -UpdateBaseline

1) scripts/run_codeql_ast.ps1

What it does:

- Ensures the local `codeql/python-queries` pack is available.
- Ensures the `codeql/python-all` pack has a lock file when needed for `printAst.ql`.
- Resolves the Python database from `.codeql-db/all-languages/python` first and falls back to `.codeql-db/python` for legacy setups.
- Converts a repository file path into the exact Windows source-archive selector format CodeQL expects.
- Runs the built-in `printAst.ql` query against the Python database.
- Writes AST graph artifacts under `.codeql-db/ast/<sanitized-file-path>/`.

Typical usage:

- powershell -ExecutionPolicy Bypass -File scripts/run_codeql_ast.ps1 -SourceFile kernel/agent.py
- make codeql-ast FILE=kernel/agent.py

Key parameters:

- -SourceFile: Repository-relative or absolute source file path.
- -Language: CodeQL database language folder to query (defaults to `python`).
- -OutputDir: Artifact root relative to the repo root (defaults to `.codeql-db/ast`).

## How To Select The Local Database In VS Code

1. Open the CodeQL extension side panel.
2. In Databases, click From a folder.
3. Select one language subdatabase such as .codeql-db/all-languages/python.
4. Add .codeql-db/all-languages/yaml or .codeql-db/all-languages/actions separately when you want those views.
5. Run queries against the selected language subdatabase.

Important:

- Select a language folder such as `.codeql-db/all-languages/python`.
- Do not select `.codeql-db/all-languages`.
- Do not select `.codeql-db`.
- Do not select `.codeql-db/all-languages/python/db-python` directly.
- Do not select a report file such as `.codeql-db/reports/codeql-snapshot.json`.

## AST Viewer Rule

The CodeQL AST viewer only works when the active editor is the database-source copy of a file opened from the selected Python database source archive.

What works:

- Run `CodeQL: Add Database Source to Workspace` for `.codeql-db/all-languages/python`.
- Open the Python file from that added database-source tree.
- Run `CodeQL: View AST` on that database-source tab.

What does not work:

- Opening the normal workspace `file:` copy of `kernel/agent.py`.
- Opening `.codeql-db/python-security-and-quality.sarif`.
- Opening any Markdown or report file under `.codeql-db/reports`.

Important:

- A normal repository tab is not enough even if the path matches a file inside the database.
- The extension requires a `codeql-zip-archive` source tab, not a normal `file:` tab.

If you still get the AST error, the fastest tested fallback is to run:

- powershell -ExecutionPolicy Bypass -File scripts/run_codeql_ast.ps1 -SourceFile kernel/agent.py

That command writes the AST graph artifacts directly under `.codeql-db/ast/` without relying on the VS Code AST UI.

## Verified Database Health

The local database cluster has been validated with the CodeQL CLI:

- `codeql resolve database .codeql-db/all-languages/python` succeeded.
- `codeql resolve database .codeql-db/all-languages/yaml` succeeded.
- `codeql resolve database .codeql-db/all-languages/actions` succeeded.
- the built-in `printAst.ql` query still resolves against the Python subdatabase after the cluster switch.
- direct local YAML query execution still fails on CodeQL 2.25.6 because the finalized YAML dataset is missing `yaml.dbscheme.stats`.

Important coverage note:

- The tracked non-Python content that CodeQL can analyze in this repository is YAML configuration and GitHub Actions workflow content.
- Representative Markdown and JSON files such as `README.md`, `docs/PRD.md`, and `infra/parameters.json` are not captured as CodeQL databases here.

## Tested AST Output

Validated end to end on 2026-06-18 20:20 local using:

- powershell -ExecutionPolicy Bypass -File scripts/run_codeql_ast.ps1 -SourceFile kernel/agent.py

Observed successful outcomes:

- AST query output written to `.codeql-db/ast/kernel__agent.py/printAst.bqrs`.
- Decoded graph artifacts written to `.codeql-db/ast/kernel__agent.py/nodes.csv` and `edges.csv`.
- Result counts: 194 nodes and 386 edges.

## Tested Status

Validated end to end on 2026-06-18 21:57 local using:

- powershell -ExecutionPolicy Bypass -File scripts/run_codeql_local_suite.ps1 -Rebuild -UpdateBaseline
- powershell -ExecutionPolicy Bypass -File scripts/run_codeql_ast.ps1 -SourceFile kernel/agent.py

Observed successful outcomes:

- The CodeQL cluster was created at .codeql-db/all-languages.
- SARIF files were generated for Python and Actions.
- The YAML subdatabase was created and resolved, but YAML analysis was skipped because local query execution fails on CodeQL 2.25.6.
- Aggregated reports were generated under .codeql-db/reports.
- AST graph artifacts remained available under `.codeql-db/ast/kernel__agent.py`.

## Files Created For This Tooling Work

Repository files created:

- scripts/setup_codeql_local.ps1
- scripts/generate_codeql_reports.ps1
- scripts/run_codeql_local_suite.ps1
- scripts/run_codeql_ast.ps1
- docs/codeql-local-tooling.md

Repository files updated:

- Makefile (adds `codeql-ast` target)
- .gitignore (ignores .tools/ and .codeql-db/ local artifacts)

Generated local artifacts (not meant for git):

- .tools/codeql (local CodeQL CLI)
- .codeql-db/all-languages (local CodeQL database cluster)
- .codeql-db/python-security-and-quality.sarif
- .codeql-db/actions-code-scanning.sarif
- .codeql-db/ast/*
- .codeql-db/reports/*

## Operational Notes

- The default workflow now targets `python`, `yaml`, and `actions`.
- Python uses `codeql/python-queries:codeql-suites/python-security-and-quality.qls`.
- GitHub Actions uses `codeql/actions-queries`.
- YAML database creation is enabled by default, but local YAML query execution is currently skipped on CodeQL 2.25.6 because the finalized dataset is missing `yaml.dbscheme.stats`.
- The repo includes `codeql/yaml-diagnostics` as a local YAML query pack for future use once the local YAML query path becomes viable.
- The AST query still uses the built-in `printAst.ql` from `codeql/python-queries`.
- Rebuild can take a few minutes depending on machine performance.
- The baseline file is intended for local trend tracking; refresh it with `-UpdateBaseline` when desired.
