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
| **C** | CodeQL SAST (was shipped, then **reverted**) | Code-level static analysis beyond `pip-audit` (deps only) | **Blocked:** the repo is **private** and code scanning needs **GitHub Advanced Security** (paid) — the `analyze` step fails with "Code scanning is not enabled." Re-add `codeql.yml` when the repo goes **public** or GHAS is enabled |
| **D** | `dependency-review-action` on PRs | Blocks a PR that introduces a vulnerable/denied dependency at review time (Dependabot only reacts after merge) | Next hardening pass, or first time a bad dep slips through — small, can land any time |
| **E** | Container image scanning (Trivy/Grype) | Scans the built image for **OS-level** CVEs in the `python:3.13-slim` base + apt layers — which `pip-audit` (Python deps only) never sees | **When F lands** — there must be a built image to scan |
| **F** | Build + push **deploy pipeline** (`deploy.yml`) | The real "merge-to-main = deploy" trigger: build per-agent images → push to DockerHub (ADR-0007). Until it exists, merge-to-main only runs CI, not a deploy | **P14 container-per-agent split** (its own sprint) — see `docs/decisions/0007` |
| **G** | Mutation testing (`mutmut`) | 100% line coverage proves lines *run*, not that tests *assert*. Mutmut proves the suite fails when logic breaks — validates test quality beyond coverage | Periodic rigor exercise; run after a stable sprint, not per-PR (it is slow). User flagged it a good candidate (2026-06-18) |

## How this list stays alive

1. **Trigger-coupling** (primary): E and F are chained — E is in F's own "out of scope / follow-up"
   note, so finishing F naturally surfaces E. F is tied to the **P14** milestone in `docs/build-plan.md`
   and ADR-0007.
2. **STATE.md pointer**: this file is linked from `docs/STATE.md` Pointers, read every session.
3. **Optional**: mirror D–G as GitHub issues with a `hardening` label if/when issue-tracking is
   adopted (the repo has a GitHub remote). Not required while this doc is the single source.
