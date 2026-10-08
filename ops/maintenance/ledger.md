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
| 2026-07-19 | housekeeping | post-S128/S129/S130 sweep — G-IDX: new docs/reports/INDEX.md + docs/design/INDEX.md, both registered in docs/INDEX.md; G-DOC: S130 rows in sprints README/INDEX SHIPPED-stamped, S128 phase-map row added, S129 PR-#50 note → merged, R005 → ✅ Adopted + next-number R006; G-LINK: 9 dead links fixed (design-log ×7, qlib-integration ×2) + sprint-98 mcp.py pointer repointed to surfaces/mcp_tools.py; G-ROOT: .trivyignore confirmed legitimate root config (build-images.yml `trivyignores:`) | ok | — | 0 | Librarian | working-tree only, not committed — planning agent reviews; no file moved/deleted |
| 2026-10-09 | housekeeping | charter v0.2: the tracker trim (OPS-TRIM) and gate G-SIZE: size limits in bytes for the seven most-edited trackers, what leaves each at a trim and where it goes, weekly cadence | ok | — | 0 | planner+op | operator approved a maintenance schedule for the frequently edited files; commit `315886a8` |
| 2026-10-09 | housekeeping | first tracker trim (OPS-TRIM), three of five trackers: `docs/work-queue.md` 247,897 → 44,527 bytes (limit 65,536): 71 closed or folded rows, the 12 dated paragraphs above the table and three sections moved verbatim to `docs/work-queue-archive/closed-2026-10-09.md` (205,036 bytes), 23 open rows stay; `docs/sprints/README.md` 176,108 → 84,960 bytes (limit 98,304): 172 MERGED rows outside the newest twelve shortened (166 goal cells to their headline or first 200 characters, 74 status cells to their first clause), nothing moved; `docs/sprints/INDEX.md` 118,978 → 24,329 bytes (limit 49,152): the 107 merged rows of the queued table deleted, 7 rows stay | partial | — | 0 | Librarian | NOT trimmed, still over their limits and unchanged: `docs/design-log.md` (1,236,245 bytes, limit 524,288), because moving the entries below DL-240 leaves 12 anchored links dead (6 in six sprint documents, 6 between entries that land in different archive files) and both fixes were outside the pass; `docs/laws/functionality-checks.md` (256,152 bytes, limit 163,840), because it is not one table in date order (two tables, five runs of rows, newest first then oldest first). The rows of the two sprint tables as they were are in git at `315886a8`; every line that left the work queue is in the archive file (187 of 187 checked). Link check, sprint-status check and markdownlint pass; branch handed to the planner to verify and merge |

> Seed entries reconstructed from this session. Going forward, `ta` appends rows
> automatically at the end of each action.
