---
name: deploy-fleet
description: Rebuild agent images at a named tag and retag the running fleet (16 apps + dispatcher job) — the bounded DL-46 deploy procedure. Use after merges that must reach the fleet, or when /check-fleet reports images behind main. Requires operator approval before executing.
---

# Deploy the fleet to a new tag

**This changes production. Confirm with the operator before executing** (state what tag, from
which commit). The procedure is the one proven 2026-07-09 (DL-46 repair): image-only updates
preserve env vars, secrets, and KEDA scale rules — verified then.

## Procedure

1. **Pick the tag** — repo convention is the sprint-style name (`s121`, `s122`, …), immutable
   and human-readable. Never deploy `latest`.

   **Then decide the path, and prove the decision — image-only retag or full `up`?** The
   deciding question is whether the **vocabulary pack** moved since the currently deployed
   commit, because image and pack must travel together:

   ```bash
   git show <deployed-commit>:orchestration/packs/trading_graph_vocabulary.json | sha256sum
   git show HEAD:orchestration/packs/trading_graph_vocabulary.json | sha256sum
   ```

   - **Hashes identical** → image-only retag (this skill). Verified this way on 2026-08-07 for
     `:s162` (`b8d1a30f…` both sides).
   - **Hashes differ** → **stop and use `pwsh infra/deploy-agents.ps1 up -Tag <tag>`.** An
     image-only retag would leave a new image against a stale pack, and the write guard is
     **fail-closed**: the first write of an undeclared property raises `VocabularyError` and
     stalls the run mid-cascade (the S148 stall, DL-85; S161 hit exactly this decision).

   Adding a property to one of the **property-enforced** labels is what usually moves the pack.
   Check which labels those are rather than assuming — `Rejection`, for instance, is *not* one,
   which is why S162 needed no pack move despite writing a new property.

2. **Build all 15 images at the tag** (from `main` unless the operator says otherwise):

   ```bash
   gh workflow run build-images.yml --ref main -f image_tag=<tag>
   gh run watch <run-id> --exit-status     # ~2 min; all 15 must push
   ```

3. **List the live inventory first — never trust the list below as complete:**

   ```bash
   az containerapp list -g trading-agents --query "[].name" -o tsv | sort
   ```

   🚨 **This step is not optional.** On 2026-08-07 this skill still named **13** apps while the
   fleet had **16** — the three deliberators had been added and never backfilled here. Following
   the hardcoded list would have left `deliberator-manager`, `deliberator-opponent` and
   `deliberator-proponent` on the old tag: a silent partial deploy, which is exactly the DL-46
   currency failure this skill exists to prevent. A stale list fails *quietly*, because the
   apps you do retag all report `Succeeded`. Reconcile the inventory against the pairs below and
   **add any app that is missing** before running step 4.

4. **Retag every app + the job** (image-only update):

   ```bash
   # app name : image suffix — portfolio-manager maps to portfolio_manager,
   # and all three deliberators share the single `deliberator` image
   for pair in "master:master" "scanner:scanner" "analyst:analyst" \
     "portfolio-manager:portfolio_manager" "execution:execution" "monitor:monitor" \
     "reporter:reporter" "forecaster:forecaster" "operator:operator" \
     "supervisor:supervisor" "curator:curator" "researcher:researcher" "provider:provider" \
     "deliberator-manager:deliberator" "deliberator-opponent:deliberator" \
     "deliberator-proponent:deliberator"; do
     az containerapp update -n "${pair%%:*}" -g trading-agents \
       --image "ghcr.io/yury-gurevich/trading-agents-${pair##*:}:<tag>" \
       --query properties.provisioningState -o tsv
   done
   az containerapp job update -n dispatcher-cron -g trading-agents \
     --image "ghcr.io/yury-gurevich/trading-agents-dispatcher:<tag>"
   ```

   Every update must return `Succeeded`.

5. **Verify** — every app on the new tag, config intact. The tag count must equal the
   inventory count from step 3; a smaller number is a partial deploy, not a rounding error:

   ```bash
   az containerapp list -g trading-agents --query "[].properties.template.containers[0].image" -o tsv | sort | uniq -c
   az containerapp list -g trading-agents --query "[].properties.provisioningState" -o tsv | sort | uniq -c
   az containerapp list -g trading-agents --query "[].{name:name,min:properties.template.scale.minReplicas,rules:length(properties.template.scale.rules)}" -o tsv
   az containerapp job show -n dispatcher-cron -g trading-agents --query "{image:properties.template.containers[0].image,cron:properties.configuration.scheduleTriggerConfig.cronExpression}" -o tsv
   ```

   Check the KEDA rules across **all** apps, not one sampled app — an image-only update is
   supposed to preserve them, and "supposed to" is what verification is for.

6. **Record the verified deploy fact** (LAW-02) on the graph, then note the same tag,
   commit, and verification output wherever the work is being tracked:

   ```bash
   PYTHONPATH=. uv run python scripts/record_deploy.py \
     --tag <tag> --git-sha <full-built-commit-sha> --actor <operator>
   ```

   Run this only after step 5 proves every target is on that tag. The append-only
   `DeployRecord` is the dashboard's currency evidence; never backfill a tag or SHA
   from inference.

Full re-provisioning (env/secret/scale changes, new apps) is **not** this skill — that is
`pwsh infra/deploy-agents.ps1 up -Tag <tag>`, which re-runs alembic + Service Bus routes too.

## Failure handling

A non-`Succeeded` update: re-run that one app's update; if it still fails, `az containerapp
revision list` to check the active revision, and report — do not improvise config changes. The
previous tag remains deployable as the rollback (same command, old tag).
