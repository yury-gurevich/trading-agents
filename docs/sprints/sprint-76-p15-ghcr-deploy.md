# Sprint 76 — P15 GHCR build pipeline + Container Apps deploy

**Phase:** P15 (multi-agent container split)
**Branch:** `sprint-76-p15-ghcr-deploy`
**Status:** planned

---

## Goal

Ship the full build-push-deploy pipeline so each agent runs as its own live Azure
Container App. After this sprint, pushing to `main` automatically rebuilds all 13
images and updates the running fleet.

Registry decision: **GHCR** (ADR-0011). Key Vault already provisioned in Azure
(S75 wired the code side; this sprint wires the Azure resource and the master's
managed identity).

---

## Prerequisites

Before starting, confirm in Azure (subscription `payg-@Office`, `5ef50a27`):

- [ ] `trading-agents` RG exists with `trading-agents-env` (Container Apps) and
  `trading-agents-logs` (Log Analytics) — done in S75 infra session.
- [ ] A GitHub PAT with `read:packages` + `write:packages` scope exists and is stored
  as repo secret `GHCR_PAT`. (Needed for the deploy workflow to pull images.)
- [ ] `GHCR_AZURE_CLIENT_ID` / `GHCR_AZURE_SUBSCRIPTION_ID` / `GHCR_AZURE_TENANT_ID`
  repo secrets set, OR `azure/login` federated credential configured for the Actions
  runner. (Needed for `az containerapp update`.)

---

## Scope

### Part A — GitHub Actions build+push (GHCR)

Create `.github/workflows/build-images.yml`:

```yaml
name: Build and push agent images
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    strategy:
      matrix:
        agent: [master, scanner, analyst, portfolio_manager, execution,
                monitor, reporter, forecaster, operator, supervisor,
                curator, researcher, provider]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write        # push to GHCR

    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: agents/${{ matrix.agent }}/Dockerfile
          push: true
          tags: |
            ghcr.io/${{ github.repository_owner }}/trading-agents-${{ matrix.agent }}:latest
            ghcr.io/${{ github.repository_owner }}/trading-agents-${{ matrix.agent }}:${{ github.sha }}
```

**Notes:**
- Matrix builds all 13 agents in parallel (no sequential dependency at image level).
- `GITHUB_TOKEN` is sufficient for push — no `GHCR_PAT` needed for the build job.
- `GHCR_PAT` (read:packages) is only needed by Azure Container Apps to pull.

### Part B — Azure Key Vault provisioning

The master agent needs a Key Vault to read from. Create
`infra/key-vault.bicep` (deployed once, not on every CI run):

Resources to create in `trading-agents` RG:
- `Microsoft.KeyVault/vaults` — `trading-agents-kv` (soft-delete enabled, RBAC
  auth model, not access policies)
- Role assignment: master's Container App managed identity →
  `Key Vault Secrets User` role

Run via `pwsh infra/setup-key-vault.ps1` (same pattern as `setup-container-apps.ps1`).
Writes `MASTER_KEY_VAULT_URL=https://trading-agents-kv.vault.azure.net/` to `.env`.

Populate initial secrets via `infra/seed-key-vault.ps1` (reads from `.env`, writes
each API key to Key Vault under its kebab-case name):

```
tiingo-api-key, alpaca-key-id, alpaca-secret-key,
finnhub-api-key, fmp-api-key, anthropic-api-key
```

### Part C — Container Apps deploy workflow

Create `.github/workflows/deploy-agents.yml` (triggered after `build-images` succeeds
on main, or `workflow_dispatch`):

Deploy order matters — master must be running before trading agents send EHLO:

1. Deploy `master` Container App (with `MASTER_KEY_VAULT_URL` + managed identity)
2. Deploy remaining 12 agents in parallel (with `MASTER_URL` + `MASTER_PUBLIC_KEY_PEM`)

Each app: `az containerapp create` (first deploy) or `az containerapp update` (subsequent).

Create `infra/deploy-agents.ps1` — the imperative deploy script the workflow calls.
Variables it needs (from repo secrets / env):
- `GHCR_PAT` — pull credential
- `MASTER_KEY_VAULT_URL` — passed to master
- `AZURE_CA_ENV_ID` — which environment to deploy into

### Part D — docker-compose local smoke test

Add a `docker-compose.local.yml` override that substitutes GHCR image refs for local
builds, so `docker compose -f docker-compose.yml -f docker-compose.local.yml up` can
be used to test the full stack locally without Azure.

---

## Files to create / modify

| File | Action |
| --- | --- |
| `.github/workflows/build-images.yml` | New — matrix build+push on main push |
| `.github/workflows/deploy-agents.yml` | New — sequential master → parallel agents |
| `infra/key-vault.bicep` | New — Key Vault + managed identity role assignment |
| `infra/setup-key-vault.ps1` | New — one-shot Key Vault provisioner |
| `infra/seed-key-vault.ps1` | New — populate secrets from .env into Key Vault |
| `infra/deploy-agents.ps1` | New — imperative deploy script (called by workflow) |
| `docker-compose.local.yml` | New — local override with build: context instead of image: ghcr.io |
| `docs/deployment.md` | Update — currently documents old Prometheus/Grafana path; rewrite for GHCR + Container Apps |
| `docs/STATE.md` | Update at closeout |

---

## Exit criteria

- [ ] `main` push triggers `build-images` → all 13 images appear in GHCR
  (`github.com/yury-gurevich?tab=packages`)
- [ ] `trading-agents-kv` Key Vault exists in `trading-agents` RG with the 6
  secrets seeded
- [ ] `deploy-agents` workflow runs to completion; master Container App is ACTIVE
  in `trading-agents-env`
- [ ] At least one trading agent (scanner) boots, sends EHLO to master, receives
  signed ACTIVATE, and enters `idle_loop` (visible in Container Apps log stream)
- [ ] `make ci` still green (no regressions)

---

## Version bump

No version bump — infra-only sprint (no new Python capability). Version stays `0.13.0`.

---

## Deferred (S77+)

- Secret rotation / Key Vault event notifications
- Durable handshake queue (Azure Service Bus replacing in-process queue)
- Per-agent Container App scaling rules
- Healthcheck / liveness probe wired to `/health` (already implemented in `http_server.py`)
