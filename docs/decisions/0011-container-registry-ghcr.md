---
type: Architecture Decision
status: accepted
closes: "Where do we store Docker container images? DockerHub, GHCR, or Azure Container Registry?"
tags: [docker, ghcr, github, container-registry, p15, ci-cd]
---

# ADR-0011 — Container registry: GitHub Container Registry (GHCR)

**Status:** Accepted
**Date:** 2026-06-21
**Deciders:** Operator

---

## Context

ADR-0007 established the container-per-agent model: each agent ships as its own Docker
image, pushed to a registry, then deployed to Azure Container Apps. The choice of registry
was deferred to the first build-and-push sprint (S76). Three options were evaluated:

| Option | Auth for push | Auth for pull (Azure) | Cost | Ecosystem fit |
| --- | --- | --- | --- | --- |
| **DockerHub** | Separate account + PAT | PAT secret | Free tier: 1 private repo | External to code |
| **GHCR (GitHub)** | `GITHUB_TOKEN` (automatic) | PAT with `read:packages` | Free (same quota as GH storage) | Same ecosystem as code + CI |
| **Azure Container Registry** | Managed identity or SP | Managed identity (native) | ~$5/mo minimum (Basic tier) | Azure-native but overkill at this scale |

The code repository is already on GitHub and CI runs via GitHub Actions. No existing
DockerHub account. ACR would add $5+/mo for infrastructure that GHCR provides free.

## Decision

**Use GitHub Container Registry (GHCR)** at `ghcr.io/yury-gurevich/`.

### Image naming convention

One image per agent, namespaced by project:

```
ghcr.io/yury-gurevich/trading-agents-master:latest
ghcr.io/yury-gurevich/trading-agents-scanner:latest
ghcr.io/yury-gurevich/trading-agents-analyst:latest
... (one per agent)
```

Tag `latest` always points to the HEAD of `main`. Immutable SHA tags
(`:<git-sha>`) are written alongside for rollback.

### Push

GitHub Actions workflow triggered on merge to `main`:
- Matrix build across all 13 Dockerfiles in parallel
- Authenticates with `GITHUB_TOKEN` (no secrets required for push)
- Pushes both `:latest` and `:<sha>` tags

### Pull (Azure Container Apps)

Azure Container Apps pulls on each deploy. Authentication:
- A GitHub PAT with `read:packages` scope stored as repo secret `GHCR_PAT`
- Passed to `az containerapp create/update --registry-server ghcr.io
  --registry-username <github-user> --registry-password $GHCR_PAT`

The PAT is a one-time setup; once stored in the repo secret it is used
by the deploy workflow automatically.

### Image visibility

Images inherit the repo's visibility. The repo is private → images are
private by default. No extra configuration needed.

## Consequences

- **No DockerHub account required.** Removes one external dependency.
- **CI push is zero-config.** `GITHUB_TOKEN` is injected automatically into every
  Actions run; no secret rotation needed for push.
- **One PAT for pull.** Azure Container Apps needs `GHCR_PAT` in repo secrets. This
  PAT must be renewed before expiry (recommend: no-expiry PAT or a 1-year rotation).
- **13 GHCR image repos** are created automatically on first push — one per agent.
  They appear under `github.com/yury-gurevich?tab=packages`.
- **ACR deferred indefinitely.** If the system grows to a multi-team org with managed
  identity requirements, ACR is the migration path. GHCR handles the single-operator
  phase without cost.

## Rejected alternatives

**DockerHub:** Requires a separate account. Free tier limits private repos to one,
which doesn't scale to 13 images. No advantage over GHCR given the GitHub-native stack.

**Azure Container Registry (ACR):** Better Azure-native pull auth (managed identity,
no PAT), but costs ~$5+/mo from day one and adds an extra Azure resource to manage.
Revisit if managed identity pull becomes a security requirement.
