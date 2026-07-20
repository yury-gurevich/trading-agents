# Copilot Instructions — trading-agents

These rules are always on for this repository. Keep generated changes consistent with the existing architecture and prefer the smallest safe edit.

## Core Workflow

- Use `docs/INDEX.md` before exploring files under `docs/`.
- For architecture decisions, check `docs/decisions/INDEX.md` first.
- For law work, check `docs/laws/INDEX.md` first.
- For sprint/status work, treat `docs/STATE.md` as the single live tracker.
- Do not treat `docs/build-plan.md` as current status; it is a phase record.
- When updating `docs/STATE.md`, include Melbourne local time in the "Last updated" stamp.
- Capture decisions, trade-offs, constraints, and ruled-out options while fresh: use `docs/design-log.md` for in-flight reasoning and ADRs under `docs/decisions/` for closed decisions.

## CI and Validation

- The local CI gate is `make ci`.
- When asking Coding Agent to fix CI, include exact repo anchors such as `.github/workflows/ci.yml`, `.github/workflows/codeql.yml`, `.github/codeql-config.yml`, `codeql/INDEX.md`, the failing run URL or id, branch name, and expected verification command.
- Do not declare a change green unless `make ci` passes locally.
- After pushing, confirm GitHub CI with `gh run list` before calling the change complete.
- The CI gate includes ruff, formatting, mypy, import-linter, module size, module headers, pytest with 100% coverage floor, pip-audit, and detect-secrets.
- Python is `>= 3.13`.
- Ruff, mypy strict mode, import-linter, module size, and detect-secrets are hard gates.

## Architecture

- Respect the enforced dependency direction: `kernel <- contracts <- agents <- orchestration / surfaces`.
- Agents never import other agents.
- Agents communicate through typed messages on the bus.
- `kernel` must not import `contracts`, `agents`, or higher layers.
- Keep modules under the 200-line hard limit; split before crossing it.

## Coding Style

- Use double quotes for strings.
- Use type annotations throughout.
- Use Pydantic v2 for DTOs, contracts, request/response types, and settings.
- Prefer structured logging via kernel observability; do not add `print()` in library code.
- Transactional data is append-only by convention.
- Tests live under `tests/`; contract tests assert typed shapes and unit tests cover private logic.

## Versioning

- Version format is `MAJOR.MM.PP` in `pyproject.toml`.
- Feature merges to `main` bump the middle group and reset patch, for example `0.13.06` to `0.14.00`.
- Fixes, CVE patches, and refactors bump only the last group.

## Secrets

- Never create credential files inside the repo tree, even untracked scratch files.
- Put local secrets only in gitignored `.env` or `infra/*.local.json` files.
- If a secret appears in the tree, remove it from the working tree and index, then verify it never reached a commit before continuing.

## Branches and Releases

- Use a dedicated branch per sprint or chore: `sprint-NN-<slug>` or `chore-<slug>`.
- Do not commit sprint work directly to `main`.
- Merge to `main` is the deploy trigger.

## Domain Skills

- Use the existing `.claude/skills/` playbooks as domain references when the task matches them: fleet checks/deploys, run diagnosis/resume, feed diagnosis, broker reconciliation, and cost audits.

## Date Display

- When displaying a date, include local time in the same string, for example `2026-04-18 11:37`.
