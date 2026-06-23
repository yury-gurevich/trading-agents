# Cloud free-tier catalogs — always-free service limits (AWS · GCP · Azure)

**What this folder is:** imported reference catalogs of *free-forever* (not 12-month-trial)
cloud services across the three major providers. Reference material for infrastructure and
data-store placement decisions — read these before assuming a component needs a paid tier.

**Consuming decisions:** [R002 db-placement](../db-placement.md) and `docs/design-log.md`
**DL-15** (substrate registry should not use Neo4j → candidate: Azure Cosmos DB free) and
**DL-16/DL-17** (data-feed + ingest pacing). Azure is the project's substrate (Container Apps
fleet in `australiaeast`), so the Azure catalog is the primary one for placement choices.

| File | Provider | Covers | Highlights for this project |
| --- | --- | --- | --- |
| [microsoft-free-forever.md](microsoft-free-forever.md) | **Azure** (primary) | DB, compute, AI/ML, dev tools, networking, identity, messaging, analytics | Cosmos DB free (1,000 RU/s, multi-API incl. Gremlin/vector), Container Apps free, Key Vault free, Service Bus free, PostgreSQL Flexible (pgvector), AI Search (vector) |
| [aws-free-forever.md](aws-free-forever.md) | AWS | compute, DB, storage, AI/ML, analytics, messaging, dev tools, identity | DynamoDB (25 GB), Lambda, S3, SNS/SQS, Secrets Manager |
| [google-cloud-free-forever.md](google-cloud-free-forever.md) | GCP | compute, DB, storage, AI/ML, analytics, dev tools, identity | Cloud Run, Firestore, BigQuery, Pub/Sub, Secret Manager; note Aura's free Neo4j runs on GCP |

## Known discrepancy to verify

The Azure catalog lists **Cosmos DB free = 1,000 RU/s + 5 GB storage**, while
[R002 db-placement](../db-placement.md) cited **1,000 RU/s + 25 GB**. The 25 GB figure was the
historical lifetime-free allowance; Microsoft has revised free-tier storage over time. **Verify the
live limit in the Azure portal before sizing the substrate registry against either number.**

## Caveats on the catalogs themselves

- Figures are point-in-time imports (2026-06) and **not continuously verified** — providers change
  free tiers. Treat as a starting map, confirm against the provider console before committing.
- "Free-forever" excludes 12-month-trial offers; a few rows note the trial caveat inline
  (e.g. AWS EC2 t2/t3.micro is 12-month-only, flagged in the AWS file).
