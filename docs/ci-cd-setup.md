# CI/CD setup — GHCR build/deploy pipeline

One-time setup for the S76 pipeline (ADR-0011: GitHub Container Registry).
Registry: `ghcr.io/yury-gurevich/trading-agents-<agent>`.

---

## What needs what credential

| Stage | Workflow | Auth | Manual step? |
| --- | --- | --- | --- |
| **Build + push** | `build-images.yml` | workflow `GITHUB_TOKEN` (`permissions: packages: write`) | No — automatic |
| **Pull (Azure pulls images)** | n/a (Container Apps runtime) | `GHCR_PAT` repo secret (`read:packages`) | Yes — mint PAT in browser |
| **Deploy (`az containerapp`)** | `deploy-agents.yml` | Azure SP secret **or** OIDC federated credential | Yes — Azure-side |

The push stage is the important asymmetry: **CI never needs a PAT to push.**
The repo's default workflow permission is `read`, but a job that declares
`permissions: { packages: write }` is granted that scope regardless of the
default. So `build-images.yml` is self-sufficient.

The PAT (`GHCR_PAT`) exists only because Azure Container Apps must pull
**private** images at runtime (including on every scale-from-zero cold start),
and GHCR does not support Azure managed identity. A short-lived `GITHUB_TOKEN`
would expire and break later autoscale pulls, so a long-lived `read:packages`
PAT is required.

---

## Step 1 — Mint the GHCR pull PAT (browser, ~30 s)

GitHub has no API/CLI to create a PAT, so this one step is manual:

1. Open: <https://github.com/settings/tokens/new?scopes=read:packages&description=trading-agents-ghcr-pull>
2. Scope: **`read:packages`** only (already pre-selected by the link).
3. Expiration: no-expiry, or a 1-year reminder to rotate.
4. Generate, copy the `ghp_…` value.

## Step 2 — Wire it as a repo secret (CLI)

```pwsh
pwsh infra/setup-github-ci.ps1 -GhcrPat <paste-token>
```

This runs `gh secret set GHCR_PAT` and prints the resulting secret list.
Equivalent one-liner:

```pwsh
"<paste-token>" | gh secret set GHCR_PAT --repo yury-gurevich/trading-agents
```

## Step 3 — Azure deploy auth (done in S76, Azure-side)

The deploy workflow authenticates to Azure to run `az containerapp`. Two options
(decided in S76):

- **OIDC federated credential** (recommended — no stored secret): an Azure app
  registration with a federated credential bound to
  `repo:yury-gurevich/trading-agents:ref:refs/heads/main`, plus three
  **non-sensitive** repo variables (client id, tenant id, subscription id).
  Used by `azure/login@v2`.
- **Service principal**: `az ad sp create-for-rbac --role "Container Apps
  Contributor" --scopes <trading-agents RG>` → store the JSON as the
  `AZURE_CREDENTIALS` repo secret.

Both are settable via `gh secret set` once the Azure identity exists.

---

## Verification

```pwsh
gh secret list --repo yury-gurevich/trading-agents     # GHCR_PAT present
gh api repos/yury-gurevich/trading-agents/actions/permissions   # enabled: true
```

After the first `main` push that includes `build-images.yml`, confirm the
13 packages appear:

<https://github.com/yury-gurevich?tab=packages>
