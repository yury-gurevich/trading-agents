# Operations ledger — append-only

Every operational action and charter change writes one row. **Never edit past rows.**
This is both the audit trail and the input to the tuning loop (`loop.md`, Loop 2).
Times are Melbourne local (AEST/AEDT).

| ts | subsystem | action | outcome | duration | cost | operator | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-06-21 ~01:0x | region-residency | rename RG traiding-agent→trading-agents (create+move+delete) | ok | ~5m | ~0 | AI+op | transient bicep, deleted after |
| 2026-06-21 ~01:1x | graph-store | create Aura Professional trial `8cf6d231` (GCP Sydney) | ok | ~5m | trial | AI+op | throwaway test rig, not permanent |
| 2026-06-21 ~02:0x | fleet-compute | deploy full 13-agent fleet (manual az) | ok | ~12m | ~cents | AI+op | AgentInstance 12 / CapGrant 27 verified |
| 2026-06-21 ~02:1x | fleet-compute | teardown — delete all 13 apps | ok | ~3m | — | AI+op | spend → 0 |
| 2026-06-21 ~02:1x | graph-store | pause Aura | ok | <1m | — | AI+op | conserve trial credit |
| 2026-06-21 | identity-secrets | provision OIDC deploy app + 3 repo secrets + GHCR_PAT | ok | — | 0 | AI+op | see ci-cd-setup.md |
| 2026-06-24 | housekeeping | research docs → folder-per-topic (cloud-free-tiers, db-placement, qlib) + INDEX convention | ok | — | 0 | AI+op | cross-links repointed; rule added to research/INDEX |
| 2026-06-24 | housekeeping | consolidate CodeQL into a self-contained tool under codeql/ (8 scripts + packs + README/INDEX) | ok | — | 0 | AI+op | fixed PSScriptRoot depth, ruff per-file-ignores, gitignore generated runs; make ci green |
| 2026-06-24 | housekeeping | root sweep — stale *.db + empty INDEX.md → del; drop redundant root run_codeql_ast.ps1 shim | ok | — | 0 | AI+op | desktop.ini/folderico left UNTOUCHED per operator; conftest.py kept (pytest root) |
| 2026-06-24 | housekeeping | size audit — delete .tools + .codeql-db + caches | ok | — | 0 | AI+op | reclaimed ~1.3 GB (2.0 G → 719 M); GitHub pack ~3 MB, no history bloat |
| 2026-06-24 | housekeeping | charter drafted — Housekeeping & Navigability (future Librarian agent) | ok | — | 0 | AI+op | this register; LAW-01 CI-05 graduation path |

> Seed entries reconstructed from this session. Going forward, `ta` appends rows
> automatically at the end of each action.
