<!-- Agent: coding | Role: S131 blast-radius live evidence -->
# Sprint 131 blast-radius live proof

## Start State

- Start command: `git pull --ff-only` on `main` returned `Already up to date`.
- Start commit: `7d7c9fa797ad96ffde0f62c7967050d1d235aa4d`.
- `pyproject.toml` read `0.71.03`; branch `sprint-131-blast-radius` was created.
- Version bump: `0.71.03 -> 0.71.04`; `uv lock` refreshed
  `trading-agents v0.71.3 -> v0.71.4`.
- Secrets discipline: no generated password/DSN was written to the repo tree or printed.

## Postgres Roles And Delivery

- Provision command loaded only `POSTGRES_DSN` from `.env` into process env and ran
  `scripts/pg_provision_roles.py --key-vault-name trading-agents-kv`.
- Result: `PG_PROVISION_EXIT_CODE=0`.
- Permanent roles: `ta_scanner`, `ta_analyst`, `ta_portfolio_manager`, `ta_execution`,
  `ta_monitor`, `ta_reporter`, `ta_forecaster`, `ta_operator`, `ta_supervisor`,
  `ta_curator`, `ta_researcher`, `ta_provider`, `ta_master`, `ta_dispatcher`,
  `ta_ops`.
- Key Vault names use the `postgres-dsn-<role>` shape, for example
  `postgres-dsn-scanner`, `postgres-dsn-portfolio-manager`, and
  `postgres-dsn-dispatcher`.
- Standing fleet flip ran outside the 22:25-00:30 UTC window:
  `pwsh -NoProfile -File infra/deploy-agents.ps1 postgres-flip`.
- Result: all 14 targets returned `[OK] ... POSTGRES_DSN secretref`:
  `master`, 12 agent apps, and `dispatcher-cron`.
- Read-only `az ... show` verification after the flip returned
  `POSTGRES_DSN.secretRef=postgres-dsn` for all 13 Container Apps and the dispatcher
  job.
- `infra/deploy-agents.ps1 preflight` after the flip returned all `[OK]`, including
  `Postgres connect + SELECT 1`, `per-target Postgres DSNs: 14/14`, Service Bus config,
  and `GHCR images present: 14/14`.

## Role Activity Audit

Immediately after the flip the apps were scaled to zero outside the KEDA window, so
`pg_stat_activity` showed `ACTIVE_TA_ROLE_COUNT=0` for container-origin sessions. To
prove the newly delivered identities without starting a trading run outside market hours,
a controlled audit opened one connection per permanent Key Vault role DSN with
`application_name=s131-role-audit` and queried `pg_stat_activity` while all connections
were held open.

```text
CONNECTED_ROLES=ta_analyst,ta_curator,ta_dispatcher,ta_execution,ta_forecaster,ta_master,ta_monitor,ta_operator,ta_ops,ta_portfolio_manager,ta_provider,ta_reporter,ta_researcher,ta_scanner,ta_supervisor
PG_STAT_ACTIVITY_ROLES=ta_analyst,ta_curator,ta_dispatcher,ta_execution,ta_forecaster,ta_master,ta_monitor,ta_operator,ta_ops,ta_portfolio_manager,ta_provider,ta_reporter,ta_researcher,ta_scanner,ta_supervisor
PG_STAT_ACTIVITY_ROLE_COUNT=15
```

Follow-up for the operator: during the next scheduled KEDA window, repeat the same
`pg_stat_activity` role query without `application_name=s131-role-audit` to capture
container-origin sessions from the live fleet.

## Canary Revocability

- Canary provision: `CANARY_PROVISION_EXIT_CODE=0`.
- Before revoke: `CANARY_CONNECT_BEFORE=ok role=ta_canary`.
- Revoke action: `ALTER ROLE ta_canary NOLOGIN`.
- After revoke: `CANARY_CONNECT_AFTER=refused error=OperationalError`.
- Fleet health after canary revoke/teardown: all 13 Container Apps plus
  `dispatcher-cron` returned provisioning state `Succeeded`.
- Teardown:
  - `CANARY_ROLE_EXISTS_AFTER_TEARDOWN=False`.
  - `CANARY_KV_DELETE_EXIT_CODE=0`.
  - `CANARY_KV_PURGE_EXIT_CODE=0`.

## Row-J Dispatcher Image

Measured repo import closure after lazy package-export fixes:

```text
CASE skip exit=0 stdout='skipped sched-2026-07-04 reason=2026-07-04 is not a NYSE trading session'
REPO_FILE_COUNT=43
CASE fake_trading_day exit=1 stderr='error scheduled dispatcher failed: ConnectionTimeout'
REPO_FILE_COUNT=44
```

The retained closure roots are `kernel/`, `contracts/`, the scheduled-dispatch
orchestration files, `agents/provider/domain/market_calendar.py`,
`agents/scanner/universe.py`, `scripts/dispatch_scheduled_run.py`, and
`scripts/universe_sp100.txt`. `orchestration/Dockerfile` no longer COPYs wholesale
`agents/`, `orchestration/`, or `scripts/`.

Local Docker build was attempted for `trading-agents-dispatcher:s131-after`, but the
workstation Docker daemon endpoint timed out before the build reached the Dockerfile:

```text
dial tcp 192.168.164.133:2375: i/o timeout
```

The authoritative image proof is therefore the updated GitHub `build-images.yml` path:
the workflow now runs a dispatcher calendar-skip smoke and emits dispatcher size before
and after.

```text
build-images run: 29714326960, success, head 1efee5b9404eee99760f8ce8c6e6d88740c88b79
workflow URL: https://github.com/yury-gurevich/trading-agents/actions/runs/29714326960
dispatcher digest: sha256:64459ebd068e415f1eaf0f23bff0541ba5de0e8305c454a15437a7555d6e9bc3
dispatcher Trivy: green, HIGH/CRITICAL exit-code gate passed
dispatcher smoke: skipped sched-2026-07-04 reason=2026-07-04 is not a NYSE trading session
dispatcher size: latest 151456849 bytes -> s131-test 149552133 bytes (-1904716 bytes)
```

## One-Time Flip Runbook

Run only outside 22:25-00:30 UTC and only after operator coordination:

```powershell
$env:POSTGRES_ROLE_KEY_VAULT = "trading-agents-kv"
uv run --extra runtime python scripts/pg_provision_roles.py --key-vault-name trading-agents-kv
pwsh -NoProfile -File infra/deploy-agents.ps1 postgres-flip
pwsh -NoProfile -File infra/deploy-agents.ps1 preflight
```

Read-only proof commands:

```powershell
az containerapp show --name <app> --resource-group trading-agents `
  --subscription 5ef50a27-50a4-4d90-9695-da61b2309cf3 `
  --query "properties.template.containers[0].env[?name=='POSTGRES_DSN'].secretRef | [0]" -o tsv
az containerapp job show --name dispatcher-cron --resource-group trading-agents `
  --subscription 5ef50a27-50a4-4d90-9695-da61b2309cf3 `
  --query "properties.template.containers[0].env[?name=='POSTGRES_DSN'].secretRef | [0]" -o tsv
```

Rollback:

```powershell
pwsh -NoProfile -File infra/deploy-agents.ps1 postgres-flip -UseSharedPostgresDsn
```

That repoints every app/job's `POSTGRES_DSN` app secret to the shared DSN value loaded
from `.env`; the per-agent roles can stay dormant.
