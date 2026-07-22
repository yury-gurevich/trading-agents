# Deployment

> **Status: interim.** The current setup deploys all agents in a **single monolithic container**.
> This is a temporary shortcut. The accepted architecture (ADR-0007) is **one Docker image per
> agent**, orchestrated by a **master bootstrap agent**, running on Azure Container Apps. The
> per-agent split is tracked under the P14 milestone. The documentation below describes the
> current monolith deployment; it will be superseded when P14 ships.

Container deployment for the trading-agents app and its Prometheus observability sidecar.

## Files

| File | Purpose |
| --- | --- |
| `Dockerfile` | Python 3.13-slim image; entrypoint `surfaces.entrypoint` starts /metrics server then CLI |
| `docker-compose.yml` | App + Prometheus stack; works with both `docker compose up` and `docker stack deploy` |
| `infra/prometheus/prometheus.compose.yml` | Committed Prometheus config; scrapes `app:8000`; remote_write commented out |
| `infra/prometheus/prometheus.local.yml` | Generated config with Azure credentials; gitignored; enables remote_write to Azure Monitor |
| `infra/setup-prometheus-auth.ps1` | Generates `prometheus.local.yml` and writes Azure SP creds to `.env` |
| `infra/setup-azure.ps1` | Provisions Azure Monitor Workspace + Azure Managed Grafana |
| `infra/setup-grafana-datasource.ps1` | Wires Prometheus data source into Grafana and patches the dashboard |

## Prerequisites

0. **PostgreSQL graph spine** — the system of record is PostgreSQL
   ([ADR-0014](decisions/0014-postgresql-system-of-record.md)). Point `.env` `POSTGRES_DSN` at the
   direct Postgres/Neon host and apply the schema before any app starts:

   ```bash
   uv run --extra runtime --extra postgres alembic -c infra/migrations/alembic.ini upgrade head
   ```

1. **`.env` file** — copy `.env.example` and fill in `POSTGRES_DSN` plus the live provider/broker/LLM keys:

   ```bash
   cp .env.example .env
   # edit .env
   ```

2. **Prometheus config** — the committed `prometheus.compose.yml` scrapes metrics locally with no Azure creds. To enable remote_write to Azure Monitor, generate `prometheus.local.yml` first:

   ```powershell
   .\infra\setup-prometheus-auth.ps1
   ```

   Then point `configs.prometheus_config.file` in `docker-compose.yml` at `prometheus.local.yml`.

## Local dev

Start both services and tail logs:

```bash
uv run --extra runtime --extra postgres alembic -c infra/migrations/alembic.ini upgrade head
make stack-up
# or
docker compose up
```

| Endpoint | URL |
| --- | --- |
| App `/metrics` | <http://localhost:8000/metrics> |
| Prometheus UI | <http://localhost:9090> |

Stop:

```bash
make stack-down
# or
docker compose down
```

## Swarm stack deploy

Build the image, initialise a single-node swarm if needed, then deploy:

```bash
make stack-deploy
# expands to:
docker build -t trading-agents:local .
docker swarm init           # skip if already a swarm node
docker stack deploy -c docker-compose.yml trading-agents
```

Remove the stack:

```bash
make stack-rm
# or
docker stack rm trading-agents
```

## Enabling Azure remote_write

The Swarm stack uses Docker `configs:` to inject the Prometheus config. To switch to the generated config with Azure credentials:

1. Generate `infra/prometheus/prometheus.local.yml`:

   ```powershell
   .\infra\setup-prometheus-auth.ps1
   ```

2. Update `docker-compose.yml` — change the last two lines under `configs:`:

   ```yaml
   configs:
     prometheus_config:
       file: ./infra/prometheus/prometheus.local.yml   # was prometheus.compose.yml
   ```

3. Re-deploy:

   ```bash
   docker stack deploy -c docker-compose.yml trading-agents
   ```

## Azure observability stack

| Component | Details |
| --- | --- |
| Azure Monitor Workspace | `trading-agents-monitor`, Australia East, resource group `trading-agents-prod` |
| Prometheus query endpoint | `https://trading-agents-monitor-bhg7e8avecgscecw.australiaeast.prometheus.monitor.azure.com` |
| Azure Managed Grafana | `https://trading-agents-grafana-hecpbea2b9cqckf2.eau.grafana.azure.com` |
| Dashboard | "Trading Agents — System Health" (`uid: trading-agents-main`) |
| Prometheus auth | Service principal `trading-agents-prometheus`; credentials in `.env` (gitignored) |

Provision from scratch:

```powershell
.\infra\setup-azure.ps1               # Azure Monitor Workspace + Grafana
.\infra\setup-prometheus-auth.ps1     # SP auth + prometheus.local.yml
.\infra\setup-grafana-datasource.ps1  # wire data source + patch dashboard
```

## Container Apps Fleet Deploy

`infra/deploy-agents.ps1 up` loads `.env`, verifies `POSTGRES_DSN` with a live `SELECT 1`, runs
`alembic upgrade head`, verifies the stable Service Bus served-agent routes, then deploys master, the
12 agent containers, and the `dispatcher-cron` Container Apps Job. `POSTGRES_DSN` and scoped Service
Bus credentials are injected as Container Apps secret references; the script never prints either
value. Rollback after S118 is no longer a graph environment-variable operation: use `git revert` and
redeploy. Previous GHCR images remain available for image-level rollback.

The normal scheduled posture is a standing fleet scaled to zero outside the daily paper-run window:

```powershell
pwsh infra/deploy-agents.ps1 up -Tag latest
```

Service Bus SAS delivery can be flipped without changing images. Run outside the
22:25-00:30 UTC fleet window:

```powershell
pwsh -NoProfile -File infra\deploy-agents.ps1 servicebus-flip
```

Rollback keeps the shared namespace string untouched and re-points the fleet to it:

```powershell
pwsh -NoProfile -File infra\deploy-agents.ps1 servicebus-flip -UseSharedServiceBusDsn
```

### Verifying which credential the fleet actually holds

**`preflight` and `az containerapp show` cannot answer this.** A flip rewrites the *value* of the
`postgres-dsn` secret while the env var name stays `POSTGRES_DSN=secretref:postgres-dsn`, so both
read the same before and after a flip — and before and after a *rollback*. STATE once carried a
false "flip not yet applied" item for two days for exactly this reason (DL-54).

Use the credential audit, which reads the delivered value, reports the role it names, and connects
as it. It prints roles and verdicts, never a credential:

```powershell
uv run --extra runtime python scripts\cred_audit.py --check-bus --strict
```

`--strict` exits non-zero unless every target is on its own scoped role. Verdicts are `scoped`,
`scoped-degraded` (own role, missing spine grants), `shared` (an unrecognised role — the rollback
state), `cross-wired` (holding *another* agent's role), `unreachable`, and `missing`. Run it after
any flip or rollback, and after a Key Vault rotation, to confirm delivery matches intent.

Default schedule:

| Component | Schedule |
| --- | --- |
| `dispatcher-cron` job | `30 22 * * *` UTC |
| `master` app cron scale window | starts `25 22 * * *` UTC |
| 12 agent app cron scale window | starts `30 22 * * *` UTC |
| all app scale windows | end `30 00 * * *` UTC |

These are deployment parameters, not code literals:

```powershell
pwsh infra/deploy-agents.ps1 up -Tag latest `
  -MasterScaleStart '25 22 * * *' `
  -AgentScaleStart '30 22 * * *' `
  -ScaleEnd '30 00 * * *' `
  -ScaleTimezone UTC `
  -ScaleDesiredReplicas 1 `
  -DispatcherCron '30 22 * * *'
```

To pause scheduled runs without deleting the fleet, disable the schedule and set the app window's
desired replicas to zero:

```powershell
$jobId = az containerapp job show -n dispatcher-cron -g trading-agents --query id -o tsv
az resource update --ids $jobId --set properties.configuration.triggerType=Manual

$apps = @(
  @{ name='master'; rule='daily-master-window'; start='25 22 * * *' },
  @{ name='scanner'; rule='daily-agent-window'; start='30 22 * * *' },
  @{ name='analyst'; rule='daily-agent-window'; start='30 22 * * *' },
  @{ name='portfolio-manager'; rule='daily-agent-window'; start='30 22 * * *' },
  @{ name='execution'; rule='daily-agent-window'; start='30 22 * * *' },
  @{ name='monitor'; rule='daily-agent-window'; start='30 22 * * *' },
  @{ name='reporter'; rule='daily-agent-window'; start='30 22 * * *' },
  @{ name='forecaster'; rule='daily-agent-window'; start='30 22 * * *' },
  @{ name='operator'; rule='daily-agent-window'; start='30 22 * * *' },
  @{ name='supervisor'; rule='daily-agent-window'; start='30 22 * * *' },
  @{ name='curator'; rule='daily-agent-window'; start='30 22 * * *' },
  @{ name='researcher'; rule='daily-agent-window'; start='30 22 * * *' },
  @{ name='provider'; rule='daily-agent-window'; start='30 22 * * *' }
)
foreach ($app in $apps) {
  az containerapp update -n $app.name -g trading-agents --min-replicas 0 --max-replicas 1 `
    --scale-rule-name $app.rule --scale-rule-type cron `
    --scale-rule-metadata "timezone=UTC" "start=$($app.start)" "end=30 00 * * *" `
                          "desiredReplicas=0"
}
```

To resume, set the same scale rules back to `desiredReplicas=1`, then re-enable the schedule:

```powershell
foreach ($app in $apps) {
  az containerapp update -n $app.name -g trading-agents --min-replicas 0 --max-replicas 1 `
    --scale-rule-name $app.rule --scale-rule-type cron `
    --scale-rule-metadata "timezone=UTC" "start=$($app.start)" "end=30 00 * * *" `
                          "desiredReplicas=1"
}
az resource update --ids $jobId `
  --set properties.configuration.triggerType=Schedule `
        properties.configuration.scheduleTriggerConfig.cronExpression='30 22 * * *'
```

To fire the same dispatcher image manually:

```powershell
az containerapp job start -n dispatcher-cron -g trading-agents
```

To simulate a non-trading day, temporarily inject the date into the job template, start the
same image, then remove the override. Do not use `job start --env-vars` for this; on Container Apps
Jobs it can replace the existing secret-backed environment values for that execution.

```powershell
az containerapp job update -n dispatcher-cron -g trading-agents `
  --set-env-vars DISPATCHER_AS_OF=2026-07-04
az containerapp job start -n dispatcher-cron -g trading-agents
az containerapp job update -n dispatcher-cron -g trading-agents `
  --remove-env-vars DISPATCHER_AS_OF
```

Observe fired, skipped, and failed executions through the job execution history and logs:

```powershell
az containerapp job execution list -n dispatcher-cron -g trading-agents -o table
az containerapp job execution show -n dispatcher-cron -g trading-agents `
  --job-execution-name <execution-name> -o jsonc
az containerapp logs show -n dispatcher-cron -g trading-agents --type console --follow
```

After the window closes, prove idle cost by checking every app has zero replicas:

```powershell
foreach ($app in @(
  'master','scanner','analyst','portfolio-manager','execution','monitor','reporter',
  'forecaster','operator','supervisor','curator','researcher','provider'
)) {
  $json = az containerapp replica list -n $app -g trading-agents --only-show-errors -o json
  $count = @($json | ConvertFrom-Json).Count
  "$app replicas=$count"
}
az containerapp job execution list -n dispatcher-cron -g trading-agents -o table
```

`infra/deploy-agents.ps1 down` is the rollback/cost-stop escape hatch. It deletes the
`dispatcher-cron` job and all 13 apps; it is not the normal S103 end state.

## Architecture

```text
┌─────────────────────────────┐
│  Docker stack: trading-agents│
│                              │
│  ┌──────────┐  :8000         │
│  │  app     │──/metrics      │
│  │          │                │
│  │ surfaces │                │
│  │.entrypoint               │
│  └──────────┘                │
│       ▲                      │
│       │ scrape app:8000      │
│  ┌────────────┐  :9090        │
│  │ prometheus │──UI           │
│  └────────────┘               │
│       │ remote_write          │
└───────┼──────────────────────┘
        ▼
  Azure Monitor Workspace
        │
  Azure Managed Grafana
```

The `observability` bridge network lets Prometheus reach the app by service name.
The app's health check on `/metrics` gates Prometheus startup via `depends_on: condition: service_healthy`.
