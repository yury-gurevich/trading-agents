---
department: security-iam
tier: 0 foundation
owner: operator + AI ops loop
status: draft
version: 0.1
implements_with: [infra/setup-github-ci.ps1, infra/aura.ps1, agents/master/key_vault.py]
---

# Charter — Security & IAM (identity & secrets)

> Worked example. This is tier-0: every other subsystem depends on it, so it is drafted
> first. Values reflect the real system as of 2026-06-21.

## OPS-IDN · Identity

The root of trust. Owns every credential and identity in the system: the master's RSA
signing keypair, the GitHub→Azure OIDC deploy identity, the GHCR pull token, the Aura
management API key, and (future) the Azure Key Vault that holds per-agent API secrets. It
mints nothing of value itself — humans mint the *root* credentials once; this subsystem
then distributes **minimum-privilege** derivations to everything downstream.

## OPS-OWN · Owns (single-writer)

- Master RSA keypair (`MASTER_PRIVATE_KEY_PEM` / public key handed to agents).
- GitHub OIDC app `trading-agents-github-deploy` (client `1edc6282-…`) + its federated credential.
- GitHub repo secret names — `GHCR_PAT` plus `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_SUBSCRIPTION_ID`.
- Aura API key (gitignored `infra/aura-api.local.json`), GHCR PAT (`infra/ghcr.local.json`).
- Runtime `CapabilityGrant` nodes (issued by the master at ACTIVATE — see `agents/master/`).
- (Future) Azure Key Vault `trading-agents-kv` + the master's access to it.

## OPS-UP · Upstream (needs)

- **Human root mint** (one-time, browser): GHCR PAT, Aura API key. Cannot be API-created.
- **Azure AD / Entra**: to hold the OIDC app + role assignment.
- **GitHub**: to hold repo secrets + the federated credential.

## OPS-DOWN · Downstream (blast radius)

**Everything.** Registry pull, fleet deploy auth, graph auth, and agent activation all fail
without their credential. A bad rotation here can take the whole fleet down. Highest blast
radius in the system → highest gate discipline.

## OPS-GATE · Preflight gates (GO / NO-GO)

| Gate ID | Check | Pass criteria | On fail |
| --- | --- | --- | --- |
| G-ID-01 | Azure CLI logged in to the right sub | `az account show` = payg-@Office | block |
| G-ID-02 | OIDC app + role assignment exist | app `1edc6282-…` has Container Apps Contributor on RG | block |
| G-ID-03 | `GHCR_PAT` valid | GitHub `/user` 200 + scope `read:packages` | block |
| G-ID-04 | Aura API key valid | OAuth token issues | block |
| G-ID-05 | No secret in tracked files | detect-secrets clean | block (commit) |

## OPS-ACT · Actions / Runbooks

| Action | Gates | Idempotent | Dry-run | Postcondition | Rollback | Blast radius |
| --- | --- | --- | --- | --- | --- | --- |
| rotate-ghcr-pat | G-ID-03 | yes | yes | new PAT pulls an image | re-set old PAT | Registry pull, Fleet cold-starts |
| rotate-aura-key | G-ID-04 | yes | yes | `ta aura status` works | re-mint | Aura management only |
| rotate-master-keypair | — | yes | yes | agents verify new signature | redeploy w/ old key | whole fleet handshake |
| provision-keyvault | G-ID-01 | yes | yes | master reads a test secret | (PNR-ID-01) | provider/execution/operator creds |
| grant-agent-secret | G-ID-01 | yes | yes | agent's `config` carries it | remove KV secret | one agent |

## OPS-PNR · Points of no return

| PNR ID | Irreversible step | Why | Guard |
| --- | --- | --- | --- |
| PNR-ID-01 | Delete Key Vault with purge-protection on | name is locked for 90 days; secrets unrecoverable | confirm + export secret inventory first |
| PNR-ID-02 | Delete the OIDC app registration | breaks all CI deploy until re-provisioned + re-secreted | confirm + note it's re-creatable (not data-loss, but outage) |

## OPS-REC · Recovery

- **Backup:** PAT/Aura-key are **re-mintable** (no backup needed — document the mint steps).
  Key Vault: enable soft-delete + purge-protection (90-day recovery). Master keypair:
  store the PEM in Key Vault once KV exists.
- **Restore:** re-run `infra/setup-github-ci.ps1` (PAT) / `az ad app …` (OIDC) / `ta aura` (key).
- **RPO/RTO:** RPO ≈ 0 (creds are re-derivable), RTO ≈ minutes (re-mint + re-set secrets).

## OPS-NEV · Never

- Never commit a secret (split-string or allowlist if a fixture needs a PEM shape).
- Never give the deploy SP Key Vault access (CI stays out of the secret-read path).
- Never reuse one PAT across scopes; never widen a scope "to be safe".
- Never rotate a downstream-critical credential without a dry-run + a rollback ready.

## OPS-OBS · Observability

`ta doctor` runs G-ID-01..05. Secret presence (not values) visible via `gh secret list`
and the gitignored `*.local.json` inventory.

## OPS-TUNE · Tuning

- **Assess:** are rotations on cadence? are any scopes broader than used? failed-auth count.
- **Improve:** LLM-review flags stale PATs, over-broad scopes, or a credential used by more
  subsystems than its charter declares.

## OPS-PARAM · Parameters

| Param | Default | Range | Effect |
| --- | --- | --- | --- |
| GHCR PAT scope | `read:packages` | — | minimum for pull |
| GHCR PAT expiry | none | none / 90d / 1y | rotation cadence |
| master key algo | RSA-2048 PSS | RSA-2048/3072 | signature strength |
| KV SKU | standard | standard/premium | HSM-backed if premium |

## OPS-MNT · Maintenance trigger

**When you touch** `infra/setup-github-ci.ps1`, `infra/*.local.json`, the OIDC app, or
`agents/master/key_vault.py` **→** re-run G-ID-01..05, update this charter's owned-list,
and re-verify downstream **Registry** (pull) and **Fleet** (deploy) gates.

## Changelog

| Version | Date | Change |
| --- | --- | --- |
| 0.1 | 2026-06-21 | initial draft from the live system |
