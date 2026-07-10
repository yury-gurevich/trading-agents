---
name: deploy-fleet
description: Rebuild agent images at a named tag and retag the running fleet (13 apps + dispatcher job) — the bounded DL-46 deploy procedure. Use after merges that must reach the fleet, or when /check-fleet reports images behind main. Requires operator approval before executing.
---

# Deploy the fleet to a new tag

**This changes production. Confirm with the operator before executing** (state what tag, from
which commit). The procedure is the one proven 2026-07-09 (DL-46 repair): image-only updates
preserve env vars, secrets, and KEDA scale rules — verified then.

## Procedure

1. **Pick the tag** — repo convention is the sprint-style name (`s121`, `s122`, …), immutable
   and human-readable. Never deploy `latest`.

2. **Build all 14 images at the tag** (from `main` unless the operator says otherwise):

   ```bash
   gh workflow run build-images.yml --ref main -f image_tag=<tag>
   gh run watch <run-id> --exit-status     # ~2 min; all 14 must push
   ```

3. **Retag the 13 apps + the job** (image-only update):

   ```bash
   # app name : image suffix — portfolio-manager maps to portfolio_manager
   for pair in "master:master" "scanner:scanner" "analyst:analyst" \
     "portfolio-manager:portfolio_manager" "execution:execution" "monitor:monitor" \
     "reporter:reporter" "forecaster:forecaster" "operator:operator" \
     "supervisor:supervisor" "curator:curator" "researcher:researcher" "provider:provider"; do
     az containerapp update -n "${pair%%:*}" -g trading-agents \
       --image "ghcr.io/yury-gurevich/trading-agents-${pair##*:}:<tag>" \
       --query properties.provisioningState -o tsv
   done
   az containerapp job update -n dispatcher-cron -g trading-agents \
     --image "ghcr.io/yury-gurevich/trading-agents-dispatcher:<tag>"
   ```

   Every update must return `Succeeded`.

4. **Verify** — all 14 on the new tag, config intact:

   ```bash
   az containerapp list -g trading-agents --query "[].properties.template.containers[0].image" -o tsv | sort | uniq -c
   az containerapp show -n scanner -g trading-agents --query "{env:properties.template.containers[0].env[].name, scale:properties.template.scale.rules[].name}"
   ```

5. **Record it** (LAW-02): note tag, commit, verification output wherever the work is being
   tracked (STATE.md if a planning session; the PR/chat if a repair session).

Full re-provisioning (env/secret/scale changes, new apps) is **not** this skill — that is
`pwsh infra/deploy-agents.ps1 up -Tag <tag>`, which re-runs alembic + Service Bus routes too.

## Failure handling

A non-`Succeeded` update: re-run that one app's update; if it still fails, `az containerapp
revision list` to check the active revision, and report — do not improvise config changes. The
previous tag remains deployable as the rollback (same command, old tag).
