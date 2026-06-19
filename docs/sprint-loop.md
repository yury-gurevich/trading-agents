# Sprint Loop Standard

Last updated: 2026-06-04

This workflow keeps branch work short-lived, preserves recovery points, and
keeps quality gates consistent across stages.

## Branching

1. Sync `main` with `origin/main`.
2. Create one short-lived branch per unit of work:
   - `feat/<scope>-YYYY-MM-DD`
   - `fix/<scope>-YYYY-MM-DD`
3. Develop only on that branch until the change is ready to verify.

## Quality Gate

Every branch must pass both commands before merge:

```bash
uv run pre-commit run --all-files
uv run pytest
```

SQLite connection warnings are merge blockers. Pytest is configured to fail on:

- `pytest.PytestUnraisableExceptionWarning`
- unclosed-database `ResourceWarning`

**CI is now the full gate.** The enforcing `test` job runs `pytest tests/v2 -m "not
llm_qualification"` against Azure Postgres with the coverage floor enforced (76%).
A green CI run proves the integration + coverage gate passed. `uv run pytest` locally
before merge is still good practice (catches issues faster), but CI is no longer
informational-only.

## Version Closeout

Before the final quality gate on a branch that is about to merge, run:

```bash
uv run trading-bump-version
```

or:

```bash
make bump-version
```

The command enforces release type from the sprint-loop branch prefix:

- `feat/...` bumps the minor version and resets patch, for example `0.13.6` -> `0.14.0`
- `fix/...` bumps only the patch version, for example `0.13.6` -> `0.13.7`

It uses the branch merge-base with `origin/main` or `main`, updates both
`pyproject.toml` and `src/trading_v2/core/version.py`, and is idempotent on the
same branch. Re-running it on an already bumped branch keeps the same target
version instead of incrementing again.

If the working-tree version has drifted away from both the branch-base version
and the expected target version, treat that as a merge blocker and resolve it
before continuing.

After the version bump, rerun the full branch quality gate.

## Multi-Step Progress Reports

Keep local progress reports for active multi-step work under `docs/sprints/`.

- Use one Markdown file per active effort.
- Update it when scope, decisions, blockers, or next steps change materially.
- Treat it as local working memory, not public documentation.

## Merge And Checkpoint

1. Clean the branch history so only meaningful commits remain.
2. Fast-forward `main` from the verified branch whose version has already been
   bumped by `trading-bump-version`.
3. Create two closeout checkpoints on `main`:
   - Permanent annotated tag: `checkpoint-YYYYMMDD-<slug>`
   - Temporary backup branch: `backup/main-after-YYYYMMDD-<slug>`
4. Push `main`, the tag, and the backup branch to `origin`.

## Cleanup

1. Delete the merged feature branch locally.
2. Delete the merged feature branch on GitHub.
3. Run a prune/fetch refresh so local remote-tracking refs stay accurate.
4. Keep only:
   - `main`
   - the current active work branch
   - at most one temporary backup branch
5. Audit unmerged remote branches before deleting them. Never auto-delete them.

## Backup Retention

- Keep checkpoint tags forever.
- Keep the temporary backup branch only until the next sprint closes cleanly.
