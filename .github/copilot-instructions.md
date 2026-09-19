# Copilot Instructions — trading-agents

These rules are always on for this repository. **[`CLAUDE.md`](../CLAUDE.md) is the source of truth and [`AGENTS.md`](../AGENTS.md) is its short form. Read both before starting; where this file disagrees with them, they win.** Keep generated changes consistent with the existing architecture and prefer the smallest safe edit.

## Core Workflow

- Use `docs/INDEX.md` before exploring files under `docs/`.
- For architecture decisions, check `docs/decisions/INDEX.md` first.
- For law work, check `docs/laws/INDEX.md` first.
- Sprint work arrives as a spec in `docs/sprints/`. Read it whole, obey its MUST RULE, and fill its handback sections (Law reading record, Test plan results, Closeout — evidence, Return notes) with real pasted output. An unfilled placeholder gets the handback returned.
- For sprint/status work, treat `docs/STATE.md` as the single live tracker.
- Do not treat `docs/build-plan.md` as current status; it is a phase record.
- When updating `docs/STATE.md`, include Melbourne local time in the "Last updated" stamp.
- Capture decisions, trade-offs, constraints, and ruled-out options while fresh: use `docs/design-log.md` for in-flight reasoning and ADRs under `docs/decisions/` for closed decisions.

## CI and Validation

- The local CI gate is `make ci`, 12 steps: ruff, format, mypy, import-linter, module size, module header, law coverage, PARAM/settings sync, pytest with a 100.00 % coverage floor, pip-audit, detect-secrets, untracked secrets.
- **Never measure the gate through a pipe.** `make ci | tail` reports `tail`'s exit code, not `make`'s. Run `make ci > <file> 2>&1; echo $?` and read the file.
- Do not declare a change green unless `make ci` exits 0 locally.
- After pushing a branch, prove it with `make gate-ran`, run from the worktree whose `HEAD` is the commit you pushed. It must print `GATE PROVEN`, and the SHA it prints must equal `git rev-parse HEAD`. Do not substitute a hand-written `gh run list` query.
- When asking Coding Agent to fix CI, include exact repo anchors such as `.github/workflows/ci.yml`, `.github/workflows/codeql.yml`, `.github/codeql-config.yml`, `codeql/INDEX.md`, the failing run URL or id, branch name, and expected verification command.
- Python is `>= 3.13`. Use `uv run` and `uv pip`, never bare `pip`.

## Architecture

- Respect the enforced dependency direction: `kernel <- contracts <- agents <- orchestration / surfaces`.
- Agents never import other agents.
- Agents communicate through typed messages on the bus.
- `kernel` must not import `contracts`, `agents`, or higher layers.
- Keep modules under the 200-line hard limit; split before crossing it. Never use `# noqa` to bypass it.

## Coding Style

- Use double quotes for strings.
- Use type annotations throughout.
- Use Pydantic v2 for DTOs, contracts, request/response types, and settings.
- Prefer structured logging via kernel observability; do not add `print()` in library code.
- Transactional data is append-only by convention.
- Tests live under `tests/`; contract tests assert typed shapes and unit tests cover private logic.

## Versioning

- Version format is `MAJOR.MM.PP` in `pyproject.toml`; stage `uv.lock` with every bump.
- A feature bumps the middle group and resets the last: `0.13.06` to `0.14.00`.
- A fix, CVE patch or refactor bumps only the last group: `0.13.06` to `0.13.07`.
- Docs-only changes, and read-only tooling that ships no package behaviour, take no bump.

## Secrets and the live system

- Never create credential files inside the repo tree, even untracked scratch files.
- Put local secrets only in gitignored `.env` or `infra/*.local.json` files.
- If a secret appears in the tree, remove it from the working tree and index, then verify it never reached a commit before continuing.
- Only the main checkout has a `.env`, and it points at the production graph and the broker. Build in a worktree, which has none, and never run a script that writes to the live system (for example `scripts/record_deploy.py`) unless the sprint spec tells you to.

## Branches and Releases

- Work in a dedicated git worktree on a branch per sprint or chore, `sprint-NN-<slug>` or `chore-<slug>`, created before any code.
- Do not commit sprint work directly to `main`, and do not merge to `main` yourself. Merge is the deploy trigger; the planner merges after verifying the handback.
- Keep LF line endings. The repo has no `.gitattributes` yet, so check `git ls-files --eol` on the files you touched before committing.

## Domain Skills

- Use the existing `.claude/skills/` playbooks as domain references when the task matches them: fleet checks/deploys, run diagnosis/resume, feed diagnosis, broker reconciliation, and cost audits.

## Date Display

- When displaying a date, include local time in the same string, for example `2026-04-18 11:37`.
