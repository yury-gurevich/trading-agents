---
name: diagnose-ci
description: "Use when: diagnosing GitHub Actions CI failures, CodeQL failures, code scanning not enabled, workflow YAML errors, failed gh runs, security job failures, or local/remote CI mismatches in this repo."
argument-hint: "failure summary, run URL, workflow name, or branch"
---

# Diagnose CI and CodeQL

Use this skill to investigate CI, GitHub Actions, CodeQL, code scanning, dependency review, pip-audit, detect-secrets, or workflow YAML failures in `trading-agents`.

## Start Here

1. Identify the failing surface: `CI`, `CodeQL`, `build-images`, `security-findings`, dependency review, pip-audit, detect-secrets, or local `make ci`.
2. If a GitHub run URL or run id is provided, inspect that exact run first with `gh run view` and only then inspect nearby workflows.
3. If no run is provided, list recent runs with `gh run list --limit 10` and choose the newest failed run that matches the user request.
4. Do not assume GitHub runner paths exist locally. Treat `/home/runner/work/...` paths as remote evidence only, then map them back to repo-relative paths.

## Repo Anchors

- CI workflow: `.github/workflows/ci.yml`
- Dedicated CodeQL workflow: `.github/workflows/codeql.yml`
- CodeQL config: `.github/codeql-config.yml`
- CodeQL tool map: `codeql/INDEX.md`
- CodeQL local overview: `codeql/README.md`
- Local CodeQL scripts: `codeql/scripts/`
- Custom Python CodeQL pack: `codeql/python-security/`
- Workflow YAML diagnostics pack: `codeql/yaml-diagnostics/`
- Local CI gate: `make ci`

## Evidence Checklist

Gather the smallest evidence set that explains the failure:

1. Workflow name, run id, branch, commit SHA, and failing job/step.
2. The failing command or action and the first meaningful error line.
3. Whether the failure is local-only, GitHub-only, or reproducible both locally and remotely.
4. The exact workflow file and step that owns the failure.
5. Any required repository setting, permission, or feature flag, especially for code scanning and GHAS.

## GitHub Actions Procedure

Use GitHub CLI when the user asks about a remote run:

```powershell
gh run list --limit 10
gh run view <run-id> --log-failed
gh run view <run-id> --json name,headBranch,headSha,event,status,conclusion,jobs
```

Then map failing steps back to repo files:

- Quality job failures usually map to `pyproject.toml`, package code, `scripts/check_module_size.py`, or `scripts/check_module_header.py`.
- Test job failures usually map to `tests/` plus the package under test.
- Security job failures usually map to dependency review, `pip-audit`, detect-secrets, or inline CodeQL in `.github/workflows/ci.yml`.
- Dedicated CodeQL failures usually map to `.github/workflows/codeql.yml`, `.github/codeql-config.yml`, or `codeql/` packs.

## CodeQL Procedure

For code scanning or CodeQL failures:

1. Check whether the failing run is from `.github/workflows/codeql.yml` or the `security` job in `.github/workflows/ci.yml`.
2. Verify CodeQL permissions include `security-events: write` on the job that uploads results.
3. Verify the workflow uses `github/codeql-action/init` before `github/codeql-action/analyze`.
4. Verify `languages: python`, `build-mode: none`, and the intended queries/config are present.
5. For local query-pack issues, read `codeql/INDEX.md` before drilling into subfolders.
6. Run the local suite when needed:

```powershell
pwsh codeql/scripts/run_codeql_local_suite.ps1 -Rebuild
python codeql/scripts/codeql_errors.py
```

Use local CodeQL results to explain query-pack or SARIF issues. Use GitHub run logs to explain upload, permission, code scanning, or Actions environment issues.

## Local Validation

When code changes are made, prefer the narrowest relevant check first, then the full gate if the change is intended to be complete:

```powershell
make ci
```

For workflow-only edits, also inspect the YAML and, when relevant, compare against recent GitHub run logs. Do not claim GitHub CI is green until `gh run list` or a specific `gh run view` confirms it after push.

## Reporting Format

Report findings in this order:

1. Root cause or most likely local hypothesis.
2. Evidence: run id, workflow, job, step, and key error line.
3. Fix applied or recommended.
4. Validation performed locally.
5. Remote validation status from GitHub, or state clearly that remote validation requires a push/new run.

Keep the explanation bounded. Do not broaden into unrelated workflow cleanup unless the failing step requires it.
