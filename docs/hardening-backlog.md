<!-- Agent: planning | Role: cross-cutting security/quality backlog (not a feature phase) -->
# Hardening backlog

Cross-cutting supply-chain, security, and code-quality improvements that are **deferred but not
dropped**. Each item names its **unblock trigger** — the event after which it should be picked up —
so it resurfaces at the right time instead of being forgotten. Reviewed whenever a trigger fires or
at sprint boundaries; referenced from `docs/STATE.md` Pointers.

## Done

- **A — least-privilege workflow token** (`permissions: contents: read` in `ci.yml`). Shipped
  2026-06-18 (`chore/dependabot-and-hygiene`).
- **B — GitHub Actions pinned to commit SHAs** (Dependabot `github-actions` ecosystem keeps them
  fresh). Shipped 2026-06-18.
- **Weekly Dependabot** (uv / github-actions / docker). Shipped 2026-06-18.
- **Dependabot auto-merge** (`.github/workflows/dependabot-auto-merge.yml`): non-major dependency PRs
  auto-approve + auto-merge once the required CI checks pass; branch protection on `main` requires
  `quality` + `test` + `security`. Majors stay open for review; docker `python` majors are ignored
  (codebase targets 3.13). Shipped 2026-06-18 (`chore/dependabot-automerge`).

## Open — with unblock triggers

| ID | Item | Why | Unblock trigger |
| --- | --- | --- | --- |
| **C** | CodeQL SAST (workflow restored; activation pending GHAS) | Code-level static analysis beyond `pip-audit` (deps only) + PR-time security findings | `codeql.yml` has been restored and CI security lane has conditional CodeQL steps. **Set `jobs.security.env.GHAS_ENABLED` to `"true"` only after GHAS/code scanning is enabled** in repo settings (private repo requirement). |
| **D** | `dependency-review-action` on PRs | Blocks a PR that introduces a vulnerable/denied dependency at review time (Dependabot only reacts after merge) | Next hardening pass, or first time a bad dep slips through — small, can land any time |
| **E** | Container image scanning (Trivy/Grype) | Scans the built image for **OS-level** CVEs in the `python:3.13-slim` base + apt layers — which `pip-audit` (Python deps only) never sees | **When F lands** — there must be a built image to scan |
| **F** | Build + push **deploy pipeline** (`deploy.yml`) | The real "merge-to-main = deploy" trigger: build per-agent images → push to DockerHub (ADR-0007). Until it exists, merge-to-main only runs CI, not a deploy | **P14 container-per-agent split** (its own sprint) — see `docs/decisions/0007` |
| **G** | Mutation testing (`mutmut`) | 100% line coverage proves lines *run*, not that tests *assert*. Mutmut proves the suite fails when logic breaks — validates test quality beyond coverage | Periodic rigor exercise; run after a stable sprint, not per-PR (it is slow). User flagged it a good candidate (2026-06-18) |

## Branch protection recommendations (with CodeQL)

When GHAS is enabled and `jobs.security.env.GHAS_ENABLED` is `"true"`:

1. Require these checks on `main`: `quality`, `test`, `security`.
2. Keep `security` required because it now contains `pip-audit`, `detect-secrets`, and conditional CodeQL analysis.
3. Keep Dependabot non-major auto-merge enabled; majors remain manual.
4. Keep "dismiss stale approvals" enabled to force re-review after dependency drift.

## How this list stays alive

1. **Trigger-coupling** (primary): E and F are chained — E is in F's own "out of scope / follow-up"
   note, so finishing F naturally surfaces E. F is tied to the **P14** milestone in `docs/build-plan.md`
   and ADR-0007.
2. **STATE.md pointer**: this file is linked from `docs/STATE.md` Pointers, read every session.
3. **Optional**: mirror D–G as GitHub issues with a `hardening` label if/when issue-tracking is
   adopted (the repo has a GitHub remote). Not required while this doc is the single source.
