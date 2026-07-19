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
- **C — CodeQL SAST** (`.github/workflows/codeql.yml` plus the CI security lane with
  `GHAS_ENABLED=true`). Enforcing since 2026-07-04; S127 proved zero open error-level findings and
  the security lane remains required alongside `pip-audit` and `detect-secrets`. Evidence:
  [S129 GitHub hardening proof](reports/sprint-129-fixpack/live-proof.md#3-github-hardening-proof).
- **D — dependency review on PRs** (`.github/workflows/ci.yml`). Shipped in S129 with
  `actions/dependency-review-action` pinned to `2031cfc080254a8a887f58cffee85186f0e49e48`
  (`v4.9.0`), failing moderate-or-higher vulnerable additions and the explicit denied package
  `pkg:pypi/pycrypto`. Evidence:
  [S129 GitHub hardening proof](reports/sprint-129-fixpack/live-proof.md#3-github-hardening-proof).
- **E — container image scanning** (`.github/workflows/build-images.yml`). Shipped in S129 with
  Trivy pinned to `ed142fd0673e97e23eac54620cfb913e5ce36c25` (`v0.36.0`), gating HIGH/CRITICAL
  OS/library findings on representative images for the runtime-only, runtime+Azure, and
  forecaster dependency-layer families (`analyst`, `master`, `forecaster`). Accepted findings must
  be documented in `.trivyignore` with sprint/design-log evidence, scope, owner, and expiry.
  Evidence:
  [S129 GitHub hardening proof](reports/sprint-129-fixpack/live-proof.md#3-github-hardening-proof).
- **F — build + push deploy pipeline** (`.github/workflows/build-images.yml` +
  `scripts/record_deploy.py`). The real shipped shape builds and pushes all 14 images to GHCR on
  `main` and manual dispatch, then records deploy currency through the DL-46 `DeployRecord` flow.
  ADR-0007 still names DockerHub; DL-50 surfaces the GHCR drift and queues a formal ADR amendment
  instead of silently rewriting the accepted ADR. Evidence:
  [S129 GitHub hardening proof](reports/sprint-129-fixpack/live-proof.md#3-github-hardening-proof).

## Open — with unblock triggers

| ID | Item | Why | Unblock trigger |
| --- | --- | --- | --- |
| **G** | Mutation testing (`mutmut`) | 100% line coverage proves lines *run*, not that tests *assert*. Mutmut proves the suite fails when logic breaks — validates test quality beyond coverage | Periodic rigor exercise; run after a stable sprint, not per-PR (it is slow). User flagged it a good candidate (2026-06-18) |

## Branch protection recommendations (with CodeQL)

When GHAS is enabled and `jobs.security.env.GHAS_ENABLED` is `"true"`:

1. Require these checks on `main`: `quality`, `test`, `security`.
2. Keep `security` required because it now contains `pip-audit`, `detect-secrets`, and conditional CodeQL analysis.
3. Keep Dependabot non-major auto-merge enabled; majors remain manual.
4. Keep "dismiss stale approvals" enabled to force re-review after dependency drift.

## How this list stays alive

1. **Trigger-coupling** (primary): landed items move to **Done** with code/workflow evidence; registry
   or supply-chain design drift is surfaced in the design log before any ADR amendment.
2. **STATE.md pointer**: this file is linked from `docs/STATE.md` Pointers, read every session.
3. **Optional**: mirror D–G as GitHub issues with a `hardening` label if/when issue-tracking is
   adopted (the repo has a GitHub remote). Not required while this doc is the single source.
