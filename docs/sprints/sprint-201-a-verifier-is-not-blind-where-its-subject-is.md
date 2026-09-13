<!-- Agent: planning | Role: sprint handover — the teardown's self-check sees what the deleter cannot reach -->
# Sprint 201 — a teardown's self-check is not blind in the same place the teardown is

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-201-a-teardown-verifier-is-not-blind-where-the-deleter-is`
**Status:** BUILT
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** work-queue **item 52** (closed) · work-queue **item 51** (**retracted**) · hardening row **T** (new) · [DL-94](../design-log.md) recurring

> **Why this bump kind.** PATCH. `pg_teardown`'s docstring already promises it "exits non-zero if any
> deletable row survived"; the code could not deliver that promise. No new capability.

---

## 🔴 MUST RULE — laws read before code

| Location | What lives there | How treated |
| --- | --- | --- |
| `docs/laws/conventions.md` | §9 drift/register conventions | read |
| `docs/laws/functionality-checks.md` | the register this defect corrupts | read; its 2026-09-13 row is corrected here |

**Law-cycle question — does this sprint change `contracts/`, or add a guarantee an agent did not
previously make?** **No.** `scripts/pg_teardown_targets.py` is tooling; no agent law governs it, no
`contracts/` file changes, no graph vocabulary moves, nothing deploys. So no clause is owed — and
saying so explicitly is the convention, not silence.

⚠️ **The invariant this must not break: a protected production row is never deletable.** The fix
*widens* a key pattern, which is the one change that could plausibly reach `Position`, `Fill`,
`BrokerStopOrder` or `BrokerOrderStatus`. Asserted directly, not assumed —
`test_widening_the_pattern_keeps_protected_labels_unreachable`.

---

## Goal

`pg_teardown --run-id` finds container-owned rows wherever the owner's key sits inside the key, and
its survivor check can see the same rows — so an under-delete exits non-zero instead of printing a
confident count.

## Why (context)

Work-queue item 52, found by S200's own functionality check. The teardown of
`verify-2026-09-13-s200` printed `deleted_edges=171 deleted_nodes=146 protected_kept=26`, **exited
0**, and left a `BrokerPositionSnapshot` — a label that **is** in `RUN_ARTIFACT_LABELS`, i.e.
declared disposable.

🚨 **The script's own docstring promises the opposite**, and names the defect it is now guilty of:
*"`--run-id` verifies itself … exits non-zero if any deletable row survived. Printing a count and
exiting 0 while orphans remained is the defect DL-94 records."* So this is DL-94 recurring **through
the verifier** rather than through the deleter.

### Measured, 2026-09-13

| Claim | Value | How |
| --- | --- | --- |
| Orphan left by the S200 teardown | `broker-position-snapshot:pm-run-e9f5109333ea…:2026-09-13T05:59:49` | *[measured]* post-teardown key scan |
| Teardown exit code | **0** | *[measured]* `TEARDOWN_EXIT=0` with the orphan present |
| Root cause | `_owned_patterns` used `contains=False` | *[read in code]* `like_pattern(f"{key}:", contains=False)` → `<key>:%` |
| Why the self-check missed it too | `survivors()` calls **the same** `_owned_patterns` | *[read in code]* |
| Pre-existing orphans of the same shape | **2 more**, from **2026-07-23** and **2026-09-01** | *[measured]* read-only sweep of all **6,259** rows in `RUN_ARTIFACT_LABELS` |
| Orphans remaining after cleanup | **0** | *[measured]* same sweep re-run |
| Shapes the old suite covered | `<container key>:<suffix>` only | *[read]* `monitor-run-…:broker:WFC:…:check` — which a prefix anchor *does* catch |

🪤 **That last row is why this survived.** The existing test pinned the shape that worked. The shape
that failed puts a label slug in front of the owner's key, and nothing asserted it.

---

## Scope

1. **`_owned_patterns` matches contains, not prefix** — one line, `contains=False` → `True`, so the
   pattern is `%<container key>:%`.
2. **Five tests**, in a new file because `test_pg_teardown_targets.py` is at 186 of 200 lines.
3. **One existing assertion updated** — it pinned the literal prefix string; its *intent* ("the owned
   pass produces a pattern for the container key") is unchanged and now stronger.
4. **The live spine cleaned** — all three orphans removed via the supported `--prefix` path.
5. **Item 51 retracted** and hardening row **T** written, because the false finding has a cause worth
   recording.

### Out of scope

- **Widening the walk's label list.** DL-94 already considered and rejected it; a `PositionCheck`'s
  only edge is to a protected `Position`, so no lawful walk reaches it. The owned-key pass exists
  precisely because the walk cannot.
- **A law cycle.** Answered No above, with the reason.

### The road not taken

- **Make `survivors()` scan every `RUN_ARTIFACT_LABELS` row regardless of pattern.** It would have
  caught this, and every future shape. Rejected: it turns a targeted check into a full-table scan
  whose failures are unattributable to a run, and the real defect is the pattern being wrong in *both*
  places — fixing the pattern fixes the verifier too, which is the smaller and more honest change.
- **Hard-coding the `<label-slug>:<container>` shape.** Rejected: it encodes today's key conventions
  in the deleter, so the next naming scheme reintroduces the bug silently. Contains-matching is
  shape-agnostic.
- **Leaving the two historical orphans.** Rejected: the functionality-check register's central claim
  is that checks tear down after themselves. Two rows that outlived their runs by months make that
  claim false wherever anyone looks.

---

## Blast radius

| What | Detail |
| --- | --- |
| Files changed | `scripts/pg_teardown_targets.py` **198**, `tests/test_pg_teardown_targets.py` **188**, `tests/test_pg_teardown_orphans.py` **112** (new) |
| Contract change? | No |
| Graph vocabulary change? | No |
| Deploy implication | **None.** `pg_teardown` is operator tooling; it is in no agent image |
| Live data touched | 3 orphan rows deleted via `--prefix`, each a declared disposable artifact whose parent container no longer existed |

---

## Success factors

- [x] A `<slug>:<container>:<suffix>` row is collected for deletion.
- [x] `survivors()` reports it, so the exit code can fail.
- [x] The previously-covered `<container>:<suffix>` shape still resolves.
- [x] Protected labels remain unreachable — asserted, not assumed.
- [x] Live spine: **0** orphans of this shape remain, measured over 6,259 rows.
- [x] Tests watched **red first**.
- [x] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **Widening a deleter's pattern is the scariest class of change in this repo.** The only reason it
is safe is that every consuming query is scoped to `RUN_ARTIFACT_LABELS`. If a future edit adds a
protected label to that tuple, this fix becomes dangerous — which is why a test asserts the scoping
rather than the outcome.

🪤 **A verifier that shares its subject's reachability assumption can only confirm what its subject
already handled.** This is the generalisable lesson, and it is not specific to teardown: the same
shape produced hardening row **T** twice more in the same session.

---

## Test plan results

| # | Test | Status |
| --- | --- | --- |
| A1 | `test_collect_finds_a_row_keyed_slug_then_container` | PASS (red first) |
| A2 | `test_survivors_reports_the_orphan_so_the_exit_code_can_fail` | PASS (red first) |
| A3 | `test_the_prefixed_child_shape_still_resolves` | PASS |
| A4 | `test_widening_the_pattern_keeps_protected_labels_unreachable` | PASS |
| A5 | `test_a_container_key_is_specific_enough_to_widen_safely` | PASS (red first) |

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in:** `C:/Users/yury_/Downloads/project/wt-s201`, **no `.env`**. The live-spine
sweep and the orphan cleanup ran in the **main** checkout, where `.env` lives.

**Result:** `_owned_patterns` emits `%<container key>:%`, so both `<container>:child` and
`<slug>:<container>:child` are collected, and `survivors()` — which shares the function — can see
both. A teardown that under-deletes now exits non-zero.

**Proof — the red run, before the fix:**

```text
E  AssertionError: assert '%pm-run-e9f5109333ea4851b404c58fd0306bb9:%' in ['pm-run-e9f5109333ea4851b404c58fd0306bb9:%']
FAILED tests/test_pg_teardown_orphans.py::test_collect_finds_a_row_keyed_slug_then_container
FAILED tests/test_pg_teardown_orphans.py::test_survivors_reports_the_orphan_so_the_exit_code_can_fail
FAILED tests/test_pg_teardown_orphans.py::test_a_container_key_is_specific_enough_to_widen_safely
3 failed, 2 passed
```

**Proof — the green run:** `17 passed` across both teardown test files; full `make ci` **exit 0**,
`2674 passed, 6 skipped`, coverage `100.00 %`, pip-audit clean, detect-secrets clean.

**Live cleanup:** 3 orphans removed (`--prefix`, 1 node each, 0 edges); the 6,259-row sweep then
reported **`orphans remaining: 0 NONE`**.

**Not met / verified failing:** none.

---

## Return notes

- **Item 51 was mine, and it is retracted, not quietly dropped.** `llm_call_keys` is a parameter that
  creates `PRODUCED_BY` edges, not a property; the relationship it claimed was missing exists **944
  times** across 27 runs, with **27 of 27** real debates linked and **0** defects. I repeated
  [DL-73](../design-log.md) against an explicit warning never to audit the graph on raw props.
- **The sprint's real value is larger than its diff.** One line of code, but it found two orphans
  nobody knew about and produced hardening row **T**, which generalises a mistake made three times in
  one session.
- **What the next sprint should know:** hardening row T's rule — *grep for an existing target before
  writing a probe* — is the cheapest thing in this sprint and the only part that will keep paying.
