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
- **G — mutation testing (`mutmut`)**. Shipped in S132 as a manual periodic exercise, not a CI
  gate. The scoped decision-engine run improved from 5,282/6,731 killed (78.47%) to 5,376/6,731
  killed (79.87%); the remaining 1,355 survivor/no-test rows are documented-equivalent in the
  report. Re-run after a stable sprint or when decision-engine gate logic changes. Evidence:
  [S132 mutation testing report](reports/sprint-132-mutation-testing/README.md).
- **H — base-image CVE remediation** (`agents/*/Dockerfile`, `orchestration/Dockerfile`, and
  `.github/workflows/build-images.yml`). Shipped in S130: Trivy now ignores unfixed findings while
  still failing fixed HIGH/CRITICAL OS/library findings, `.trivyignore` remains empty, and all 14
  images use two-stage `dhi.io/python:3.13-dev` -> `dhi.io/python:3.13` builds with venv-carrying
  runtimes. Manual `build-images` run `29681635979` built/pushed all 14 `s130-test` images and
  passed every Trivy gate; the actionable finding count dropped from S129's representative `22` to
  `0` gate-blocking findings. Evidence:
  [S130 base-image live proof](reports/sprint-130-base-image/live-proof.md#final-live-run).
- **J — dispatcher image carries only its measured runtime slice.** Shipped in S131:
  `scripts/dispatch_scheduled_run.py` was measured at a 43-file calendar-skip closure and a
  44-file fake-trading-day closure; `orchestration/Dockerfile` now copies `kernel/`,
  `contracts/`, the scheduled-dispatch orchestration files, the two needed agent modules
  (`agents/provider/domain/market_calendar.py`, `agents/scanner/universe.py`), and the
  dispatcher script/universe file instead of wholesale `agents/`, `orchestration/`, and
  `scripts/`. Evidence:
  [S131 blast-radius proof](reports/sprint-131-blast-radius/live-proof.md#row-j-dispatcher-image).
- **K — assertion-strength gap in trade-gating + money-parsing code** (surfaced by S132
  mutation). Closed in S134 over three rounds: R1 killed the alpaca money-parser bucket
  (39 → 7 named default-normalization residuals) plus the PM gate / reward-risk / sector
  boundaries; R2 took the targeted analyst-domain survivors 249 → 127 with a per-module
  before/after table; R3 forced **all 127** into an auditable per-mutant disposition —
  **107 killed, 12 individually justified equivalents, 8 named wording exclusions, 0
  untriaged**. Scoped decision-engine kill-rate 79.87 % → **84.36 %** (5,678/6,731).
  Permanent justified non-targets: the `# pragma: no cover` Alpaca HTTPS transport
  (live/paper-verified), string/render/audit wording survivors, the 7 `_fill_from_order`
  default-normalization residuals, and the 20 R3 residuals named individually in the CSV.
  Evidence: [S134 report](reports/sprint-134-assertion-hardening/README.md) +
  [Round 3 dispositions](reports/sprint-134-assertion-hardening/round-3-dispositions.csv).
- **I — per-agent blast-radius scoping, Postgres + Service Bus.** Part 1 shipped in
  S131: 15 per-agent Neon/Postgres roles with secret-backed `POSTGRES_DSN` delivery.
  Part 2 shipped in S133: the shared Service Bus namespace string was replaced for
  measured bus targets by entity-level topic SAS rules, per-target Key Vault
  primary/bundle secrets, Container Apps secretRefs, and a rollback-only shared
  credential path. The bus carries claim-check refs/RPC envelopes, not data, so this
  is lower severity than the Postgres half; the value is attribution, revocability,
  and removal of the last shared runtime credential. Evidence:
  [S131 Postgres proof](reports/sprint-131-blast-radius/live-proof.md) +
  [S133 Service Bus proof](reports/sprint-133-servicebus-sas/live-proof.md).
- **L — standing container smoke check: every agent image starts its real entrypoint.**
  Shipped 2026-07-22 (`chore-container-smoke`). DRIFT-016/017/018 were the *same* defect three
  times — an agent container not starting its real entrypoint, recorded as "unit gate hid it"
  (×2) and "hidden by local graph demos", each caught only by a live fleet run. A provider-only
  smoke already proved the assertion shape; `build-images.yml` now applies it to **all 12 agent
  images** (`master` performs no master-handshake; `dispatcher` keeps its calendar-skip smoke):
  run with no activation config and require a **non-zero exit** *and* output reaching for the
  master, which proves the entrypoint ran the agent rather than merely that the image exists.
  Adds a 180 s timeout (exit 124) so a hang fails loudly. Verified by dispatch run
  `29904029290` — all 14 jobs green and **all 12 images printed the assertion**, confirming the
  step executed rather than silently skipping (the DL-52 failure mode). Motivated by the R006
  [defect-detection-rate analysis](research/code-quality-tooling/defect-detection-rate.md):
  the unit suite caught **0 of 14** escaped defects, so this was the highest-leverage quality
  work available.

## Open — with unblock triggers

No open hardening rows after S133.

| ID | Item | Why | Unblock trigger |
| --- | --- | --- | --- |

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
