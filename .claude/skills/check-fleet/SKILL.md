---
name: check-fleet
description: Fleet health + deploy-currency audit — are all 13 Container Apps + dispatcher job healthy, on the code you think they are on (DL-46), activated, and able to reach the spine and bus? Use for "is the fleet ok", "are we running latest", pre/post-deploy verification.
---

# Check the fleet

The standing fleet fails **silently**: scale-to-zero means "0 replicas" is normal, and tag-pinned
images mean a green CI says nothing about what is deployed (DL-46). This audit distinguishes
healthy-idle from broken.

## Procedure

1. **Inventory + tags (the DL-46 tripwire, manual):**

   ```bash
   az containerapp list -g trading-agents --query "[].{n:name, img:properties.template.containers[0].image}" -o table
   az containerapp job show -n dispatcher-cron -g trading-agents --query "properties.template.containers[0].image" -o tsv
   gh run list --workflow build-images.yml --limit 5
   ```

   Every app + the job should share one tag; compare its build date against the latest merge to
   `main` that touched `agents/ kernel/ contracts/ orchestration/`. **Behind = finding**, even if
   everything else is green.

2. **Job cadence:** `az containerapp job execution list -g trading-agents -n dispatcher-cron -o table`
   — one `Succeeded` per trading day at 22:30 UTC.

3. **Scale windows:** replicas must be 0 outside 22:25–00:30 UTC and 1 inside. Outside the
   window, `az containerapp replica list` returning empty is **healthy**, not down.

4. **Activation registry (graph):** `AgentInstance` + `CapabilityGrant` nodes exist per agent
   type; recent `Escalation` nodes mean a credential failed its live activation test (DL-36).

5. **Spine + bus:**

   ```bash
   PYTHONPATH=. uv run python -c "import os,psycopg;from dotenv import load_dotenv;load_dotenv();psycopg.connect(os.environ['POSTGRES_DSN'],connect_timeout=10).close();print('spine ok')"
   uv run python scripts/servicebus_prepare_routes.py   # idempotent; also verifies reachability
   ```

6. **Last run's verdict** — a fleet audit without a pipeline outcome is half an answer:
   `PYTHONPATH=. uv run python scripts/accept.py --run-id <latest sched-*>`.

## Report format

One line per layer (images/tags · job · scale · activation · spine · bus · last verdict) with
✓/⚠/✗ and the evidence. If images are behind main: recommend `/deploy-fleet` (operator-approved).
Never "all green" without having run every step (LAW-02).
