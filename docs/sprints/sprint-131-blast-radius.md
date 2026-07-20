<!-- Agent: planning | Role: sprint handover -->
# Sprint 131 — Blast radius: per-agent Postgres roles (row I, part 1) + dispatcher image slim (row J)

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-131-blast-radius`
**Status:** ready for handover (packaged 2026-07-20)
**Effort:** M

---

## Why this sprint

The 2026-07-19 threat-model review (STATE + backlog rows I/J) named the platform's two real
blast-radius gaps. Code visibility is Kerckhoffs-fine and the DL-36 ladder already scopes
vendor keys per agent — but **every container holds the same `POSTGRES_DSN`**, so one
compromised agent can read/write the *entire* graph under an identity indistinguishable
from every other agent; and the **dispatcher image COPYs the whole repo**, contradicting
the per-agent image design. This sprint fixes the Postgres half of row I (the biggest
prize) and all of row J. The Service Bus half of row I (per-agent SAS per topic) is
deliberately deferred to its own sprint — different Azure machinery, separately testable.

Timing: the P12 scorecard-run needs clean-news nights accumulating (they start
2026-07-20); this sprint uses that waiting window. **Kickoff precondition: the operator has
confirmed the 2026-07-20 nightly run came back healthy** — if it did not, run fixes first.

## What already exists (read before estimating)

- **Per-agent secret machinery (DL-36)**: master is sole Key Vault accessor; ACTIVATE
  delivers min-privilege grants from `orchestration/packs/trading_secrets.json`
  (provider/execution/operator rows only today). `POSTGRES_DSN` does NOT ride this — it is
  a plain env var on all 13 apps + the dispatcher job (see `az containerapp show -n
  scanner` env list) and in the local `.env`.
- **The graph schema is two tables** (`nodes`, `edges`) owned by the `neondb` database's
  default role; alembic manages DDL (`infra/migrations/`). Neon supports standard Postgres
  roles (`CREATE ROLE … LOGIN PASSWORD`), and `pg_stat_activity` shows connections per
  role — the audit win.
- **Infra update paths**: image-only retag = `/deploy-fleet` (preserves env); env/secret
  changes = `az containerapp update --set-env-vars` or the full
  `infra/deploy-agents.ps1 up`. KEDA windows: master 22:25, agents 22:30–00:30 UTC —
  infra flips must happen OUTSIDE that window.
- **Dispatcher image** (`orchestration/Dockerfile`): COPYs `agents/ orchestration/
  scripts/` wholesale. The job entrypoint is `scripts/dispatch_scheduled_run.py` →
  `orchestration/scheduled_dispatch.py`; universe loading uses the shared
  `agents/scanner/universe.py::load_universe_file`. The true import closure is measured,
  not assumed (`python -X importtime` or a `modulefinder` pass).
- **Rollback**: the shared-DSN env value stays in Key Vault/`.env` untouched during the
  sprint; reverting = re-pointing env vars back. No schema change is involved.

## Decisions taken at packaging (LAW-06)

1. **Same privileges, distinct identities — this sprint.** All per-agent roles get the
   same table grants (SELECT/INSERT/UPDATE on `nodes`/`edges` + sequences). The win now is
   **attribution + revocability** (audit by `current_user`; one role revocable without
   touching the rest). *Ruled out (deferred, recorded):* label/row-level security per
   agent — real least-privilege, but needs a per-label write-matrix design and RLS policy
   testing; do not improvise it into this sprint.
2. **15 roles**: 12 agents + master + dispatcher + `ops` (operator's local dashboard/.env
   use). Names `ta_<agent>`. Passwords generated at provisioning, placed directly into
   Key Vault + app env — **never a file in the repo tree** (CLAUDE.md secrets rule; the
   provisioning script prints nothing).
3. **Delivery stays env-var, not ACTIVATE grants, for now.** The spine DSN is needed
   before activation (agents poll the graph to find work), so it cannot ride the ACTIVATE
   payload without a bootstrap redesign. Per-app env with per-agent values closes the
   shared-credential hole today. *Ruled out:* moving DSN into the DL-36 grant flow this
   sprint (bootstrap-order redesign — design-log item if ever wanted).
4. **Service Bus SAS scoping is OUT** (row I part 2, own sprint): per-topic authorization
   rules + per-agent connection strings are orthogonal machinery; bundling both halves
   makes the live check unreviewable.
5. **Row J = measured slim, not guessed.** The coder measures
   `dispatch_scheduled_run.py`'s import closure and COPYs exactly the needed packages
   (expected: `kernel/ contracts/ orchestration/ scripts/dispatch_scheduled_run.py +
   scripts/universe_*.txt + agents/scanner/`); if the closure genuinely needs more, record
   why rather than widening silently.

## Kickoff (paste this)

> Execute **Sprint 131 — blast radius** exactly as specified in this file
> (`docs/sprints/sprint-131-blast-radius.md`). Read first: backlog rows I/J in
> `docs/hardening-backlog.md`; `infra/migrations/` + `kernel/graph_postgres*.py` (the
> spine); `infra/deploy-agents.ps1` (env delivery); `orchestration/Dockerfile` +
> `scripts/dispatch_scheduled_run.py` (row J); `docs/laws/dependencies.md`
> (DEP-POSTGRES); design-log **DL-48** (the process contract this kickoff enforces).
>
> **Contract (DL-48 — enforced):**
>
> - **Start:** `git pull` on `main` — `pyproject.toml` must read **0.71.03** (stop and
>   report if not). Branch `sprint-131-blast-radius`. Bump **PATCH → 0.71.04** (hardening)
>   - `uv lock`.
> - **Drift rule:** before handback, `git fetch`; if `origin/main` moved, merge it in,
>   re-run the full gate, record what moved in the Return notes.
> - **Secrets rule** (CLAUDE.md): no generated password ever exists as a repo-tree file or
>   in command output; place directly into Key Vault + app env; `.env` gets only the `ops`
>   role's DSN (operator applies it — tell them, do not edit their `.env`).
> - **Handback rule:** Closeout + Return notes last; incomplete handbacks are bounced.
> - Hard gate: `make ci` green (exit code captured), 100 % coverage, ≤200-line modules,
>   headers, `tunable(..., why=...)` where thresholds appear.
>
> **Work items:**
>
> - **A (roles):** an idempotent provisioning script (`scripts/pg_provision_roles.py`,
>   stdlib + psycopg, DSN from env only) that creates the 15 `ta_<name>` LOGIN roles with
>   identical grants on `nodes`/`edges` (+ future-tables default privileges), rotatable
>   (`--rotate <name>` re-issues a password), silent about secrets; unit-test the SQL
>   generation pure-functionally (no live DB in tests).
> - **B (delivery):** extend `infra/deploy-agents.ps1` so each app/job receives its own
>   `POSTGRES_DSN` (per-agent role) as a Container Apps **secret-backed** env var; a
>   bounded `az` runbook section in the sprint report for the one-time flip on the
>   standing fleet — executed OUTSIDE the 22:25–00:30 UTC window.
> - **C (row J):** measure the dispatcher entrypoint's import closure; slim
>   `orchestration/Dockerfile` COPY to it; the image must still build, pass Trivy, and
>   smoke (calendar-skip path runs to completion in the runner, as S130's provider smoke
>   did).
> - **D (docs):** backlog row I narrowed to "part 2: Service Bus SAS" with part-1 evidence;
>   row J → Done; `docs/laws/dependencies.md` DEP-POSTGRES note on per-role identities;
>   design-log entry for the deferred RLS step + the ruled-out ACTIVATE-delivery option.
> - **Functionality check (LAW-02), live, outside the fleet window:** (1) provision roles
>   on Neon, flip the fleet env, then `az containerapp show` per app proves each carries
>   its own secret-backed DSN; (2) during the next scheduled run (or one manual fire),
>   query `pg_stat_activity`/connection audit showing **distinct `ta_<agent>` roles**
>   active; (3) revocability: revoke a throwaway `ta_canary` role → connection refused,
>   loudly, while the fleet stays green; (4) row-J image: build run green + smoke +
>   size before/after. Record in `docs/laws/functionality-checks.md` + evidence under
>   `docs/reports/sprint-131-blast-radius/`; tear down `ta_canary` and any disposable
>   artifacts to zero.
> - **Wrap up:** README/INDEX rows; Closeout + Return notes; push, hand back.
>   **Do not merge.** The fleet env flip is coordinated with the operator (it touches
>   production config even though no image changes).
>
> **Rollback:** repoint every app's `POSTGRES_DSN` secret back to the shared value (kept
> in Key Vault untouched); roles can stay dormant. Row J: `git revert`.

## Guardrails

- No schema/DDL changes to `nodes`/`edges`; alembic untouched except if default-privilege
  grants need a migration (record the decision if so).
- No RLS/row-level policies this sprint (decision 1); no Service Bus changes (decision 4).
- Infra flips only outside 22:25–00:30 UTC; never during a live run window.
- Generated passwords: never printed, never in the tree, never in closeout text.
- The dashboard/local `.env` keeps working throughout (ops role handed to the operator
  before the shared DSN is ever retired — and the shared DSN is NOT retired this sprint).

## Definition of done

1. Every fleet target (13 apps + dispatcher) connects to Neon under its own `ta_<agent>`
   role, proven by per-role connection evidence from a real run window.
2. One role's revocation demonstrably locks out only that identity (canary proof).
3. The dispatcher image ships only its measured import closure, builds Trivy-green, and
   smokes.
4. Backlog rows updated (I narrowed to part 2, J Done); `make ci` green at 100 %;
   closeout + return notes filled.

## Closeout (coding agent fills; planning agent verifies before merge)

```text
CLOSEOUT — Sprint 131
Branch / merge commit:   sprint-131-blast-radius / not merged by instruction
make ci:                 MAKE_CI_EXIT_CODE=0; 1608 passed, 5 skipped; coverage 100.00%
Functionality check:     PG_PROVISION_EXIT_CODE=0; fleet flip 14/14 secretRefs; preflight
                          per-target Postgres DSNs 14/14; controlled pg_stat_activity audit
                          saw 15 distinct ta_<agent> roles; ta_canary refused after NOLOGIN
                          while fleet stayed Succeeded; dispatcher build-images run
                          29714326960 passed Trivy + calendar-skip smoke by digest and size
                          moved 151456849 -> 149552133 bytes
Version:                 0.71.03 → 0.71.04 (PATCH); uv.lock refreshed
Backlog rows:            I → narrowed to part 2 Service Bus SAS; J → Done
Drift rule:              git fetch before handback; origin/main stayed at
                          7d7c9fa797ad96ffde0f62c7967050d1d235aa4d, no merge needed
Deviations from spec:    container-origin pg_stat_activity capture deferred to next KEDA
                          window because apps were scaled to zero; local Docker daemon timed
                          out, so image build/smoke/size proof used the GitHub runner
```

## Return notes (coding agent appends at handback — mandatory)

Append below, at the very end of this file, everything the next session needs that the
closeout numbers don't carry: surprises, in-flight decisions and why, drift observed,
follow-ups. A handback is not accepted while this section is empty or the closeout
placeholder is unfilled (LAW-02 + DL-48).

<!-- return notes go below this line -->

- Branch `sprint-131-blast-radius` is pushed and intentionally unmerged. The standing
  fleet's `POSTGRES_DSN` app secret now points at per-target role DSNs delivered from
  `trading-agents-kv`; shared rollback material remains untouched.
- Rollback for the fleet env flip is
  `pwsh -NoProfile -File infra/deploy-agents.ps1 postgres-flip -UseSharedPostgresDsn`.
  The per-agent roles can remain dormant after rollback.
- `.env` was not edited. If local operator tooling should stop using the shared spine
  identity, the operator should apply the `ta_ops` DSN from Key Vault to their own `.env`.
- Canary cleanup is complete: `ta_canary` was revoked, then the database role and Key
  Vault secret were deleted/purged to zero.
- The dispatcher image proof is a runner substitute for local Docker: local daemon access
  timed out before the Dockerfile was evaluated; GitHub run `29714326960` built/pushed
  `s131-test`, passed Trivy, ran the Saturday calendar-skip smoke, and recorded the size
  reduction.
- Operator follow-up: during the next scheduled KEDA window, repeat the role query against
  `pg_stat_activity` to capture container-origin `ta_<agent>` sessions. The controlled
  audit already proved all 15 role credentials and Postgres attribution, but it used
  `application_name=s131-role-audit` connections rather than live app replicas.
- Backlog row I now means only Service Bus SAS scoping part 2; Postgres blast-radius part
  1 is complete. Row J is Done. The deferred RLS step and the ruled-out ACTIVATE-delivery
  option are recorded in DL-51.
