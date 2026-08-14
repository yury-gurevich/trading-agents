<!-- Agent: execution | Role: sprint spec — let a partial fill advance to filled without breaking append-only, and retire one dead capability declaration -->
# S176 — a partial fill must be able to finish

**Closes:** work-queue item 5 (hardening row P) + [DRIFT-033](../laws/drift-register.md) ·
**Type:** fix ·
**Target version:** next available PATCH at merge — **do not pin it in this file** ·
**Branch:** `sprint-176-a-partial-fill-must-be-able-to-finish`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo or the
> live spine on 2026-08-13. Everything marked **Assumed** has **not** been verified — check it
> before building on it. Do not treat an unmarked claim as measured.

## Why

### 1 · A `partial` fill is stuck as `partial` forever — and so is its price

[`reconciliation_store.py:72`](../../agents/execution/reconciliation_store.py) writes
`broker_status` **only when it is absent**:

```python
if "broker_status" not in node.props:
    props = {"broker_status": broker_fill.status, ...}
```

Write-once, and deliberate — the spine is append-only and `Fill` is protected (DL-94). But it means
a fill that first reaches us as `partial` can **never** become `filled`, no matter what the broker
later says.

🚨 **It is worse than the register records, and this part is new.** `broker_price_cents` is
write-once by the *same* guard ([line 80](../../agents/execution/reconciliation_store.py)), and
[line 53](../../agents/execution/reconciliation_store.py) reads it back as the basis for realized
PnL:

```python
exit_price_cents = int(node.props.get("broker_price_cents", broker_price_cents))
```

So a partial does not merely mislabel a status — **it freezes the price that realized PnL is
computed from**, permanently, at the partially-filled price. Hardening row P is filed as a labelling
defect; it is a money defect.

**Measured — why it is still dormant.** All 188 `Fill` nodes on the live spine:

| `broker_status` | count |
| --- | --- |
| `filled` | 52 |
| `rejected` | 106 |
| *(absent)* | 30 |
| **`partial`** | **0** |

No fill has ever arrived partial, which is the only reason this has never cost anything. A widened
funnel with more limit orders at the open makes it materially more likely — and the failure is
silent divergence between broker and graph, plus wrong PnL.

🟢 **No new graph property is needed.** `broker_status`, `broker_price_cents` and
**`broker_status_refreshed_at`** are all already in the property-enforced vocabulary pack and all
already written. The pack does not move.

### 2 · DRIFT-033 — a declaration naming a system that no longer exists

[`contracts/master.py:99`](../../contracts/master.py) declares
`external_io=("key_vault", "neo4j")`. The Neo4j runtime was deleted in S118 and ADR-0014 made
Postgres the system of record. **Measured 2026-08-13:** that string is still the **only** `neo4j`
reference in `kernel/`, `agents/`, `orchestration/` or `contracts/`. A declaration naming a dead
dependency reads identically to a live one — the DL-70 shape.

🪤 **Drop it; do not replace it with `postgres`.** Measured convention: `analyst`, `forecaster` and
`monitor` all declare `external_io=()` despite using the graph, so the graph is **not** treated as
declared external I/O anywhere. The correct result is `external_io=("key_vault",)`.

It rides in this sprint because it edits a Python file and therefore needs the full CI cycle
anyway — exactly what the register says to do with it.

## The design decision this sprint has to make

**How does a status advance without breaking append-only?** The write-once guard exists for a
reason; removing it wholesale would let any later read overwrite a settled fact. Options:

1. **Monotonic transition allowlist** — permit only forward moves (`partial` → `filled`), reject
   anything else, and refresh `broker_status_refreshed_at` when it moves. **Recommended:** smallest
   change, keeps the guard's intent, and the transition set is explicit and testable.
2. **Terminal-status guard** — freeze only once the status is terminal (`filled`, `rejected`),
   leaving non-terminal states updatable. Equivalent in effect; states the rule as *"terminal facts
   are immutable"* rather than enumerating transitions.
3. **Append a new node per observation** — purest append-only, and the largest change to how
   everything downstream reads a fill.

Whichever wins, `broker_price_cents` must move with the status: a price captured at a partial is not
the price of the completed fill. Record the rejected options in `docs/design-log.md` (LAW-06).

## Steps, in order

1. **Write the failing test first.** A `Fill` observed `partial`, then observed `filled` at a
   different price — assert today's behaviour (status and price both stuck), so the fix has a
   before.
2. **Implement the chosen transition rule**, including `broker_status_refreshed_at`.
3. **Make the PnL basis follow the final price**, not the first one seen.
4. **Prove a backwards or lateral transition is still refused** — `filled` → `partial` must not be
   possible, and neither must `rejected` → anything.
5. **DRIFT-033:** `external_io=("key_vault",)`, and flip the register row to closed with the SHA.
6. **Full CI cycle** — `make ci` redirected to a file, never piped; push; `make gate-ran` **from the
   worktree whose HEAD is the commit**; then merge.

## Success factors

- [ ] A test proves `partial` → `filled` now lands, with the price updated to the completed price.
- [ ] A test proves `filled` → `partial` and `rejected` → anything are **refused**.
- [ ] Realized PnL for a fill that completed after a partial uses the **final** price. State the
      arithmetic in the closeout.
- [ ] `grep -rn neo4j kernel/ agents/ orchestration/ contracts/` returns **nothing**.
- [ ] [DRIFT-033](../laws/drift-register.md) flipped to closed with the merge SHA.
- [ ] The vocabulary pack did **not** move (confirm the hash both sides).
- [ ] `make ci` green at the 100 % floor; `make gate-ran` exits 0 on the final SHA.

## Traps

- 🪤 **`Fill` is property-enforced.** A **new** property moves the vocabulary pack and forces a full
  `pwsh infra/deploy-agents.ps1 up`, which still discards operator env until
  [S169](sprint-169-one-switch-and-a-deploy-that-keeps-it.md) lands. You need none —
  `broker_status`, `broker_price_cents` and `broker_status_refreshed_at` all already exist. If your
  design needs a new one, say so in the closeout and stop.
- 🪤 **Do not weaken the append-only guarantee to fix this.** `Fill` is protected (DL-94) and the
  drop sweep depends on it. The goal is a *narrower* rule, not no rule. A test that a settled
  terminal status cannot be rewritten is as important as the one that lets a partial finish.
- 🪤 **Zero production partials means your test data is synthetic.** Nothing on the live spine
  exercises this path, so unit-green is the *only* proof you will get. Do not claim a live
  functionality check you cannot run — say plainly that the trigger has never occurred.
- 🪤 **`grep` before you claim DRIFT-033 is done.** The register was verified on 2026-08-05 and again
  on 2026-08-13; both times `contracts/master.py:99` was the sole survivor. Re-verify rather than
  trusting either date.
- 🟠 **Observed while measuring, out of scope unless trivial:** `external_io` naming is inconsistent
  across agents — `contracts/deliberator.py` declares `"LLM provider"` while `contracts/operator.py`
  declares `"llm_provider"`. Mention it in the closeout; do not fix it here without saying so.

## Handover — paste this to Codex

```text
Work item: S176 — a partial fill must be able to finish.
Repo: trading-agents. Read docs/sprints/sprint-176-a-partial-fill-must-be-able-to-finish.md in full
before writing anything. Read CLAUDE.md. Read docs/INDEX.md before opening any docs folder.

WHAT IS WRONG
1. agents/execution/reconciliation_store.py writes broker_status only if absent, so a fill first
   seen as "partial" can never become "filled". broker_price_cents is write-once by the same guard,
   and line 53 reads it back as the basis for realized PnL - so a partial permanently freezes the
   price that PnL is computed from. Filed as a labelling defect; it is a money defect.
   Measured: 188 Fill nodes live - 52 filled, 106 rejected, 30 absent, ZERO partial. Dormant, not
   fixed. No new graph property is needed: broker_status, broker_price_cents and
   broker_status_refreshed_at all already exist in the property-enforced pack.
2. DRIFT-033: contracts/master.py:99 declares external_io=("key_vault", "neo4j"). The Neo4j runtime
   was deleted in S118. Drop it -> ("key_vault",). Do NOT replace it with "postgres": analyst,
   forecaster and monitor all declare external_io=() despite using the graph, so the graph is not
   declared external I/O anywhere.

HOW TO WORK
- Branch first, before any code: sprint-176-a-partial-fill-must-be-able-to-finish. Never commit
  sprint work to main. Work in a git worktree.
- The spec names three ways to let a status advance without breaking append-only, and recommends
  one. Choose deliberately, then record the options you rejected and why in docs/design-log.md
  (LAW-06).
- uv only: `uv pip`, `uv run`. Agents never import other agents. Modules hard-block at 200 lines.

WHAT NOT TO DO
- Do NOT remove the write-once guard wholesale. Fill is append-only and protected (DL-94); the drop
  sweep depends on it. Narrow the rule, do not delete it. A test that a terminal status cannot be
  rewritten matters as much as the one that lets a partial finish.
- Do NOT add a property to Fill. It is property-enforced; a pack move forces a full deploy that
  still wipes operator env (S169, unfixed). The properties you need already exist.
- Do NOT claim a live functionality check. No production fill has ever been partial, so this path
  cannot be exercised on the real spine. Say that plainly rather than implying live proof.

HOW TO PROVE IT
- LAW-02: success is proven, never assumed. Do not report an intent as an outcome.
- Write the failing test FIRST, asserting today's stuck behaviour, so the fix has a before.
- `make ci > ci.txt 2>&1 ; echo $?` then READ ci.txt. Never `make ci | tail` - a pipe reports tail's
  exit code, so a real failure reads as green. All 11 steps, 100% coverage.
- Push the branch, then run `make gate-ran` FROM THE WORKTREE whose HEAD is the commit you are
  proving; it ignores any SHA= argument and resolves from the working directory. Check the SHA it
  prints against `git rev-parse HEAD`. Merge only after it exits 0. No PR required.
- Confirm the vocabulary pack hash is identical both sides.
- Flip the DRIFT-033 row in docs/laws/drift-register.md to closed with the merge SHA.
- Fill in the "Closeout - evidence" block with real measurements. A handback with the placeholder
  comment still in it is not accepted.
```

## Closeout — evidence

**Result:** Implemented as a narrow monotonic transition allowlist: only
`Fill.broker_status` `partial -> filled` may replace existing `Fill` broker refresh values. The
allowed replacement set is limited to `broker_status`, `broker_price_cents`,
`broker_status_refreshed_at`, and `realized_pnl_cents`; terminal `filled` and `rejected` fills are
still skipped before a refresh write. The ordinary graph merge remains append-only outside that
specific completion. Version bumped `0.90.08 -> 0.90.09`.

**Files changed:** `agents/execution/broker_status_refresh.py`,
`agents/execution/reconciliation_store.py`, `agents/execution/realized_pnl.py`,
`kernel/graph_support.py`, `kernel/graph_postgres_queries.py`, `contracts/master.py`,
`agents/execution/tests/test_partial_fill_completion.py`, `tests/test_graph_partial_completion.py`,
`docs/design-log.md`, `docs/laws/drift-register.md`, `pyproject.toml`, `uv.lock`.

**Design decision:** chose the recommended monotonic transition allowlist. Recorded as
[DL-109](../design-log.md#dl-109---s176-lets-only-partial-broker-fills-complete---status-decided-2026-08-13).
Rejected: terminal-status guard (broader than the measured defect), append-new-node/read-model
rewrite (larger downstream reader change), and removing the write-once guard wholesale (would permit
terminal rewrites).

**Before test:** after planting `agents/execution/tests/test_partial_fill_completion.py`, the focused
pre-fix run was red:

```text
uv run pytest agents/execution/tests/test_partial_fill_completion.py --no-cov
2 failed, 1 passed
test_partial_broker_status_can_finish_with_final_price:
  assert 'partial' == 'filled'
test_completed_after_partial_sell_uses_final_price_for_realized_pnl:
  assert 'partial' == 'filled'
```

The seeded partial node carried `broker_price_cents=10135` and the expected completed price was
`10200`; because the status never advanced, the price remained the partial observation too.

**After tests:** focused/related tests passed:

```text
uv run pytest agents/execution/tests/test_partial_fill_completion.py tests/test_graph_partial_completion.py agents/execution/tests/test_fill_refresh_terminal.py agents/execution/tests/test_realized_pnl_refresh.py tests/test_graph.py tests/test_graph_postgres.py --no-cov
32 passed, 1 skipped
```

`partial -> filled` now lands with `broker_price_cents=10200`. `filled -> partial` and
`rejected -> filled` are refused by the terminal-refresh skip and leave no `BrokerOrderStatus`
refresh rows.

**Realized PnL arithmetic:** the completed-after-partial sell test opens ABT at `10000` cents,
observes a partial at `10135`, then completes at `10200` for quantity `10`. The final realized PnL
is `(10200 - 10000) * 10 = 2000` cents, and the test asserts `realized_pnl_cents == 2000`.

**DRIFT-033:** closed in `docs/laws/drift-register.md` with merge SHA
`b17ff5fd1037052e4ff163d026c91fa72119892b`. Verification:

```text
grep -rn neo4j kernel/ agents/ orchestration/ contracts/
# no output; exit 1
```

**Vocabulary pack:** unchanged. `git hash-object orchestration/packs/trading_graph_vocabulary.json`
on the S176 tree and on `57f540f^` both returned:

```text
40bd1b108e3338bd002ca7cf0dacb7133efbd371
```

**Local CI:** ran unpiped and redirected:

```text
make ci > ci.txt 2>&1
$LASTEXITCODE
0
```

Readback summary:

```text
ruff check: passed
ruff format --check: 977 files already formatted
mypy: Success: no issues found in 805 source files
import-linter: Contracts: 4 kept, 0 broken
pytest: 2243 passed, 6 skipped in 90.14s
coverage: TOTAL 14566 stmts, 0 missing, 100.00%; required 100.0% reached
pip-audit: No known vulnerabilities found
detect-secrets: Passed
untracked secret scan: scanning 4 new file(s), Passed
```

**Remote gate:** ran `make gate-ran` from this worktree after pushing branch
`sprint-176-a-partial-fill-must-be-able-to-finish`:

```text
GATE PROVEN for b17ff5fd1037052e4ff163d026c91fa72119892b:
  Security Findings: success
  CI: success
```

Main was then fast-forwarded and pushed with checkpoint tag
`checkpoint-20260813-s176-partial-fill-finish` plus backup branch
`backup/main-after-20260813-s176-partial-fill-finish`. Post-merge `make gate-ran` from `main`:

```text
GATE PROVEN for b17ff5fd1037052e4ff163d026c91fa72119892b:
  Security Findings: success
  CI: success
  CodeQL: success
  Build and push agent images: success
  Security Findings: success
  CI: success
```

**Live proof:** not claimed. The live spine measurement in the spec found zero production
`partial` fills, so this path cannot be exercised on the real fleet yet. Unit and graph-backend
tests are the only functionality proof for S176.
