# EXP-007 - Can Aura Free snapshots be stored locally via API?

**Date:** 2026-07-01 · **Status:** complete - Aura snapshot create/list works, local export is blocked on
the current Free tier · **Feeds:** DL-11 Aura backup/restore, S101 permanent graph-store backup plan

## Purpose

The question was narrow and operational: for the current Aura-backed graph, can we create a backup through
the Aura API and store the backup bytes locally?

This matters because an Aura-side snapshot is useful for rollback, but it is not the same as an
off-platform backup. The permanent graph-store decision needs to know whether "backup" means managed
snapshot only, or whether this repo can also hold a local `.backup` artifact for disaster recovery,
region moves, or provider exit.

## Process

- Confirmed this was the Aura path, not the local Docker/Enterprise Neo4j path.
- Checked the official Aura API and backup docs:
  - `https://neo4j.com/docs/aura/api/overview/`
  - `https://neo4j.com/docs/aura/managing-instances/backup-restore-export/`
- Used the repo wrapper `infra/aura.ps1`, which forwards to `tools/scripts/aura.ps1`.
- Verified the active Aura instance through the management API:
  - id: `bce05bd6`
  - name: `trading-agents-free`
  - status: `running`
  - region: `asia-southeast1`
  - type: `free-db`
- Listed snapshots first: none existed.
- Dry-ran the snapshot call:
  - `pwsh infra/aura.ps1 snapshot -WhatIf`
  - confirmed it would call `POST https://api.neo4j.io/v1/instances/bce05bd6/snapshots`.
- Triggered a real on-demand snapshot:
  - `pwsh infra/aura.ps1 snapshot`
  - returned snapshot id `12e7be4a-4f2c-4a4d-9def-c5e9073c215e`.
- Polled snapshots:
  - first state: `Pending`, `exportable=False`
  - final state: `Completed`, `exportable=True`.
- Verified the intended local destination is gitignored:
  - `infra/neo4j/local/backups/`
  - `git check-ignore -v infra/neo4j/local/backups/test.backup`.
- Ran a sanitized download probe against
  `GET /v1/instances/{instance_id}/snapshots/{snapshot_id}/download`.
  The probe did not print the signed URL. If the URL had been granted, it would have saved the file under
  `infra/neo4j/local/backups/` and printed only path, byte size, and SHA-256.
- Confirmed the result with the repo wrapper:
  - `pwsh infra/aura.ps1 export-url -SnapshotId 12e7be4a-4f2c-4a4d-9def-c5e9073c215e`.

## Delivery

Created one Aura-side snapshot:

| Field | Value |
| --- | --- |
| Instance | `trading-agents-free` / `bce05bd6` |
| Instance type | `free-db` |
| Snapshot id | `12e7be4a-4f2c-4a4d-9def-c5e9073c215e` |
| Final snapshot status | `Completed` |
| Final API `exportable` flag | `True` |
| Download endpoint result | `HTTP 403 Forbidden` |
| Local backup artifact | none created |

Wrapper output for the export attempt:

```text
Export URL failed (HTTP 403) - not supported on this tier.
```

No local file was written to `infra/neo4j/local/backups/`.

## Interpretation

1. Aura management API backup creation is proven for the active Free instance. The repo can create and list
   snapshots with `infra/aura.ps1 snapshot|snapshots`.
2. Local storage is not proven and is currently blocked. Even with `status=Completed` and
   `exportable=True`, the download endpoint returns `403 Forbidden` for this key/tier.
3. Therefore, on the current AuraDB Free setup, "backup" means an Aura-managed snapshot, not an
   off-platform local backup artifact.
4. The `exportable` field is not sufficient evidence that bytes can be downloaded. The endpoint permission
   is the real gate.
5. Restore should continue to be treated as a managed Aura/console operation unless a future API key/tier
   proves otherwise.

**Decision pressure.** For local/off-platform backups, use one of two routes:

- Move to an Aura tier/API entitlement that permits snapshot download, then re-run this experiment and
  require a saved file plus SHA-256 as proof.
- Use self-hosted/local Neo4j for the durable store path and script `neo4j-admin dump` or backup into an
  ignored local backup directory.

**Current operational rule:** Aura Free snapshots are acceptable for rollback confidence while the graph is
small and disposable. They are not sufficient as the sole backup plan once the graph becomes durable
production memory.
