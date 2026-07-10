---
name: diagnose-feeds
description: Investigate why provider enrichment feeds (fundamentals, news, sectors, earnings, sentiment) ran degraded on a run — secrets, rate limits, or vendor failure. Use when a trace shows *_degraded notes or the analyst scored on technicals alone.
---

# Diagnose degraded provider feeds

Degraded feeds are silent confidence killers: the analyst blends fewer pillars, scores drop, and
a normal market day can read as a no-trade day. Feed degradation is a WARN (field-gated), never a
Flag — so it will not announce itself.

**Input:** a run id whose trace shows `notes: ..._degraded` (from `/diagnose-run` step 1).

## Procedure

1. **Which feeds, and is it new?** Compare the run's trace `notes` against the previous runs'
   traces (`scripts/trace_run.py --run-id <earlier>`). All-four degraded across every fleet run
   points at credentials/config; a single feed degrading points at the vendor or rate limits.
2. **Did the provider container even hold the keys?** The entitlement map is
   `orchestration/packs/trading_secrets.json` (provider entries: Finnhub, Alpha Vantage, Tiingo,
   Alpaca). DL-36 tested activation means: if a **required** credential failed its live test, the
   agent would refuse activation and write an `Escalation` — check those first
   (`/diagnose-run` step 3 snippet). A feed key marked optional can be absent/stale **without**
   an Escalation: that is the silent case.
3. **Test the keys from here** — the repo has a smoke tester:
   `pwsh scripts/test-api-keys.ps1` (or the `/check-api` skill). A key that passes locally but
   fails in-fleet means the **vault copy** is stale — compare with the S108 seeder's
   read-back (`scripts/seed_key_vault.py --dry-run`).
4. **Rate limits at 22:30 UTC.** The scheduled window hits vendors with ~99 tickers of
   enrichment in minutes. Finnhub free tier: 60 req/min; Tiingo: 50 req/hr
   (`docs/laws/tiingo-usage-limits.md`). Check provider container logs for HTTP 429s in the
   window (`az containerapp logs show -g trading-agents -n provider --type console --tail 300`).
5. **Vendor outage** — if keys test green and no 429s, hit the vendor endpoint once manually
   (the curl lines are commented in `.env`) and note the response.

## Report format

Feed(s) affected · first run affected · cause (stale vault secret / missing entitlement /
rate limit / vendor / unknown-with-evidence) · proof (test outputs, log lines) · bounded
recommendation: re-seed via the S108 tested-before-insert seeder · entitlement fix as branch+PR ·
rate-limit strategy change as a drift item for the planning agent (never hand-edit the vault
without the seeder's live test).
