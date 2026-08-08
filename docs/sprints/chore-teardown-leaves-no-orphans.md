<!-- Agent: tooling | Role: chore spec + closeout for DL-94 -->
# chore-teardown-leaves-no-orphans — a teardown that under-deletes must not exit 0

**Closes:** [DL-94](../design-log.md) · **Type:** fix · **Version:** 0.89.04 · **Branch:**
`chore-teardown-leaves-no-orphans` · **Deploys:** nothing (tooling only; the fleet stays on `:s165`)

## Why

Tearing down the S162 check, `pg_teardown.py --run-id` reported `deleted_nodes=21`, exited 0, and left
**41 further nodes** carrying the same run's stamps. Teardown is the step that makes a functionality
check honest — `functionality-checks.md` requires stamped rows returned to zero — so a teardown that
silently under-deletes quietly corrupts the register's central claim. A partially-deleted lineage is
worse than an untouched one, because the surviving rows look like real history.

## What was measured first

DL-94 proposed adding five missing labels to `_RUN_ARTIFACT_LABELS`. Measured against the live spine,
**that fix would not have worked, and its obvious successor would have destroyed the book**:

| Finding | Evidence |
| --- | --- |
| `PositionCheck` is unreachable by *any* lawful walk | Its sole edge type graph-wide is `PositionCheck -> Position` (191). `Position` is production state. Widening the label list reaches **0** of them. |
| `Recommendation` is not reached via `Candidate` | Inbound edges are `Rejection -> Recommendation` (129) and `OrderIntent -> Recommendation` (56). No `Candidate` edge exists. |
| The label list was an undeclared traversal barrier | `Position`'s only bridge from the reached set is `Fill -> BrokerStopOrder -> Position`. It held **only** because `BrokerStopOrder` was absent — a label that reads exactly like a run artifact. |

## What shipped

1. **`scripts/pg_teardown_targets.py`** splits the one tuple that was answering two questions.
   `PROTECTED_LABELS` (`Position`, `Fill`, `BrokerStopOrder`, `BrokerOrderStatus`) is broker-mirroring
   production state (DL-44 / S120): never deleted, never traversed *through*. `RUN_ARTIFACT_LABELS` is
   disposable proof, and gains the five labels DL-94 named.
2. **A second enumerator.** Rows are also collected by the key convention `<owning-run-key>:<suffix>`,
   which is the only way to reach `PositionCheck` and `CloseDecision`.
3. **`--run-id` verifies itself.** It re-reads the run's stamps after deleting and **exits 1**, naming
   every survivor. The failure mode DL-94 records cannot recur silently.
4. **`protected_kept` means what it says** — rows the walk *stopped at*, not rows matching the stamp.
   The stamp-based count reported 0 while ten broker rows were spared.

## Success factors

- [x] The five orphaned labels are collected, and `PositionCheck` is collected by prefix, not by walk.
- [x] `Position` / `Fill` / `BrokerStopOrder` / `BrokerOrderStatus` are never deleted by `--run-id`.
- [x] A surviving stamped row makes the script exit non-zero and name it.
- [x] Each behaviour observed failing on a planted defect first (DL-70).
- [x] `make ci` green, measured unpiped to a file.
- [x] Remote `make gate-ran` green.

## Closeout — evidence

**Local gate.** `make ci` **exit 0**, `2180 passed / 6 skipped / 100.00 % coverage`, redirected to a
file and read back (never through a pipe — hardening row S).

**Planted defects, observed failing before the fix (DL-70).**

| Planted defect | Result |
| --- | --- |
| `_run_id_teardown` returns 0 despite survivors (the original bug) | `test_teardown_exits_non_zero_and_names_every_orphan` **failed**, 9 passed |
| Container-owned prefix pass removed (DL-94's own proposed fix) | **3 failed**, 7 passed |
| `BrokerStopOrder` added to `RUN_ARTIFACT_LABELS` | **2 failed**, 8 passed |

**Functionality check — live Neon spine, read-only, `sched-2026-08-07`.** Collection path only; the
delete path was never called; connection opened `read_only`.

- **23 former orphans now collected**: 11 `SentimentReading`, **10 `PositionCheck`**, 1
  `DeliberationRun`, 1 `Rejection`.
- **10 `Fill` rows no longer deleted** — `exit:…:sell`, the ten live flatten exit orders. The old code
  would have deleted the graph's record of ten orders open at the broker (the DL-44 divergence).
- `protected_kept` reports **20** (10 `Fill` + 10 `Position` reached via the new `PositionCheck`s).
- 🪤 The check caught a `psycopg.errors.SyntaxError` — `ESCAPE` is invalid on the `LIKE ANY(...)` form —
  that **all 12 unit tests passed straight through**, because a fake cursor does not parse SQL.

**Teardown of the check itself.** Nothing to tear down: zero writes, zero deletes, zero broker calls.
The `.env` copied into the worktree during setup was deleted before any `git add` and never reached the
index, verified with `git status --porcelain`.

**Remote gate.** `make gate-ran` **exit 0** — GATE PROVEN for `70426300b09c0797f1d80cf383f3c1a1f2135d42`, with **CI: success** and **Security Findings: success**. The target resolves the full SHA itself and refuses an abbreviated one (hardening row M). Merged to `main` as `9d6243c`.

**Not proven.** The delete path has **not** been exercised against live data — only its collection and
verification queries were. The first real `--run-id` teardown is the remaining proof, and it should be
run on a disposable synthetic run, not a production lineage.
