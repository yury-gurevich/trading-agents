# `ops/` index — every subsystem and its status

**How to use:** find the subsystem you're about to touch, open its charter, run its gates
*before* you act. If you're changing how a subsystem works, its charter is the file you
must update in the same change (see `maintenance/loop.md`).

| Subsystem | Tier | Charter | Status |
| --- | --- | --- | --- |
| [identity-secrets](subsystems/identity-secrets/charter.md) | 0 foundation | ✅ drafted | worked example |
| registry | 1 supply | ⬜ stub | charter pending |
| region-residency | 1 cross-cutting | ⬜ stub | charter pending (needs ADR) |
| graph-store | 2 state | ⬜ stub | charter pending |
| fleet-compute | 3 compute | ⬜ stub | charter pending |
| observability | 4 signal | ⬜ stub | charter pending |
| operator-cli (`ta`) | x | ⬜ stub | charter pending (build alongside the CLI) |

## Framework files

| File | Answers |
| --- | --- |
| [README.md](README.md) | What is this realm, why does it exist, what are the principles? |
| [subsystem-map.md](subsystem-map.md) | The big parts, tiers, data-flow, the dependency DAG |
| [_template/charter.md](_template/charter.md) | The "law" schema every charter follows |
| [maintenance/loop.md](maintenance/loop.md) | When/how does maintenance fire? The tuning + LLM-review loop |
| [maintenance/ledger.md](maintenance/ledger.md) | Append-only trace of every operational action |
| [maintenance/points-of-no-return.md](maintenance/points-of-no-return.md) | Every irreversible step, system-wide |

## Adding a subsystem charter

1. Copy `_template/charter.md` to `subsystems/<name>/charter.md`.
2. Fill every section (write "none", never delete a section).
3. Add the row above; set tier from `subsystem-map.md`.
4. List its Points of No Return in `maintenance/points-of-no-return.md`.
5. Wire its gates into `ta <subsystem> preflight`.
