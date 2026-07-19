<!-- Agent: coding | Role: S129 live functionality-check evidence -->
# Sprint 129 Live Functionality Check

Date: 2026-07-19

Scope: quant-evidence persistence, dashboard projection read-cache, dependency-review PR hardening,
and Trivy image scanning. Secrets and connection strings were loaded only from existing local or
GitHub configuration and were not printed or written into the repo tree.

## 1. Local Opt-In Deliberation Proof

Command shape: an in-memory `cascade_once` deliberation run with an injected recording LLM, using
the same opt-in veto stage as `scripts/run_local.py --veto`.

- Run id: `s129-local-deliberation`
- Graph store: `InMemoryGraphStore`
- Stage counts: provider, scanner, analyst, forecaster, portfolio_manager, deliberation,
  execution, monitor, and reporter each ran once.
- Deliberation runs persisted: `1`
- Debate ticker: `AAPL`
- Verdict: `uphold`
- Newly persisted Recommendation quant metrics included `composite_score=0.5`,
  `confidence=0.6`, `history_bars=2.0`, `indicators_available=0.0`, and
  `technical_score=0.5`.
- Transcript evidence: Defender, Challenger, and Judge each cited the quant context; the cited
  metric that was previously absent from Recommendation nodes was `composite_score`.

No durable graph rows were written, so graph teardown was not required for this leg.

## 2. Live Neon Dashboard Cache Proof

Command shape: a local WSGI dashboard server against live Neon via `PostgresGraphStore`, with DSN
suppressed, no Azure/GitHub reader writes, and a fixed interaction script:

1. `/api/runs`
2. `/api/verdict?run=sched-2026-07-15`
3. `/api/runs/sched-2026-07-15/stages`
4. `/api/runs/sched-2026-07-15/flags`
5. `/api/runs/sched-2026-07-15/positions`
6. `/api/runs/sched-2026-07-15/recovery`
7. `/api/vitals?run_id=sched-2026-07-15`

Observed result:

- Selected run: `sched-2026-07-15`
- Projection cache TTL: `5.0` seconds
- Self-heal refetch interval: `90.0` seconds
- First interaction pass Postgres `_run` calls: `18`
- Second interaction pass inside TTL Postgres `_run` calls: `0`
- Round-trip reduction: `18`
- Verdict unchanged inside TTL: `true`
- Verdict hero result: `GREEN`
- Verdict summary: `1 order, 1 candidate`
- Graph writes performed by the check: `0`

The local server was stopped after the check.

## 3. GitHub Hardening Proof

PR proof:

- Draft PR: <https://github.com/yury-gurevich/trading-agents/pull/50>
- PR CI run: <https://github.com/yury-gurevich/trading-agents/actions/runs/29679386195>
- Security job: `success`
- Dependency review step: `success`, pinned `actions/dependency-review-action`, PR-only, blocking
  vulnerable additions and denied dependencies.

Image scan proof:

- Manual `build-images.yml` run:
  <https://github.com/yury-gurevich/trading-agents/actions/runs/29679397636>
- Event/ref/tag: `workflow_dispatch` on `sprint-129-fixpack`, `image_tag=s129-fixpack`
- Representative images scanned by Trivy: `analyst`, `master`, and `forecaster`
- Trivy gate result: executed and failed on HIGH/CRITICAL findings, as intended.
- Per representative image: `22` findings (`HIGH: 19`, `CRITICAL: 3`)
- Sample findings included `CVE-2026-53615`, `CVE-2026-41992`, `CVE-2026-54369`,
  `CVE-2025-69720`, `CVE-2026-13221`, `CVE-2026-42496`, `CVE-2026-8376`,
  `CVE-2026-42497`, `CVE-2026-48962`, `CVE-2026-57432`, and `CVE-2026-9538`.

No CVE was accepted or baselined in Sprint 129. `.trivyignore` now documents the accepted-findings
path; the follow-up is a base-image remediation or a formal accepted-findings entry with owner and
expiry, not silent suppression.

## 4. Teardown Sweep

Disposable local artifacts were stopped or removed:

- Deliberation live check wrote no durable rows.
- Dashboard live check was read-only; local WSGI server stopped.
- Postgres sweep: `uv run python scripts/pg_teardown.py --prefix s129-livecheck --contains --env-file .env`
- Sweep result: `deleted_edges=0`, `deleted_nodes=0`

The GitHub PR and workflow runs are retained as review/audit evidence. Branch-tagged GHCR images
from the manual build run are CI artifacts and were not represented by any repo file.
