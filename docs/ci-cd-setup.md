# CI/CD setup — GHCR build/deploy pipeline

One-time setup for the S76 pipeline (ADR-0011: GitHub Container Registry).
Registry: `ghcr.io/yury-gurevich/trading-agents-<agent>`.

---

## What needs what credential

| Stage | Workflow | Auth | Manual step? |
| --- | --- | --- | --- |
| **Build + push** | `build-images.yml` | workflow `GITHUB_TOKEN` (`permissions: packages: write`) | No — automatic |
| **Pull (Azure pulls images)** | n/a (Container Apps runtime) | `GHCR_PAT` repo secret (`read:packages`) | Yes — mint PAT in browser |
| **Deploy (`az containerapp`)** | `deploy-agents.yml` | Azure OIDC federated credential | ✅ Done (Step 3) |

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

## Step 3 — Azure deploy auth — ✅ PROVISIONED (2026-06-21)

The deploy workflow authenticates to Azure via **OIDC federated credential**
(no stored Azure secret). Already stood up via `az`:

| Item | Value |
| --- | --- |
| App registration | `trading-agents-github-deploy` |
| Client ID (`AZURE_CLIENT_ID`) | `1edc6282-3d1e-4cd7-8574-b88684c382b7` |
| Tenant ID (`AZURE_TENANT_ID`) | `5b2efd16-6b81-4778-82b7-ee95e1c46093` |
| Subscription (`AZURE_SUBSCRIPTION_ID`) | `5ef50a27-50a4-4d90-9695-da61b2309cf3` (payg-@Office) |
| Service principal object id | `dd6bdf90-987f-49d8-ae2a-ad302fabcfdb` |
| Role | `Container Apps Contributor` scoped to the `trading-agents` RG (least-privilege) |
| Federated credential | `github-main` → subject `repo:yury-gurevich/trading-agents:ref:refs/heads/main` |

The three IDs are set as repo secrets (non-sensitive identifiers, but stored as
secrets for `azure/login@v2` convention). The federated credential covers `push`
to main and `workflow_dispatch` on main. **To gate deploys behind a GitHub
Environment later, add a second federated credential** with subject
`repo:yury-gurevich/trading-agents:environment:<name>`.

`deploy-agents.yml` uses:

```yaml
permissions:
  id-token: write   # required for OIDC
  contents: read
steps:
  - uses: azure/login@v2
    with:
      client-id: ${{ secrets.AZURE_CLIENT_ID }}
      tenant-id: ${{ secrets.AZURE_TENANT_ID }}
      subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

The deploy SP can only manage Container Apps in `trading-agents` — it has **no**
Key Vault access. The master's runtime Key Vault role is assigned separately by
`setup-key-vault.ps1` (S76 Part B), keeping CI out of the secret-read path.

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
