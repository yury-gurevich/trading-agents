<!-- Agent: kernel | Role: sprint spec for the DL-99 fixables -->
# S167 — a fault count cannot lie, and a fail-open says why

**Closes:** the two code-shaped halves of [DL-99](../design-log.md) · **Type:** fix ·
**Target version:** 0.89.08 (PATCH — defect fixes, no new capability) ·
**Branch:** `sprint-167-a-fault-count-cannot-lie`

> Handover to a delegated coding agent. Everything under **Measured** was observed on the live
> system on 2026-08-08 and can be relied on. Everything marked **Assumed** has *not* been verified —
> check it before building on it.

## Why

Two defects, found while investigating why the deliberation veto produced no real debate.

**Measured.** The `:s166` run `check-s166-veto-gate` wrote a `DeliberationRun` with
`real_debate_count=0, failed_open_count=18` and the rationale `"llm unavailable (fail-open)"`. That
rationale is misleading: **58 `LLMCall` nodes were logged in the same window** across all three
roles (proponent 28, opponent 20, manager 10), so the peers were reachable. The 18 `Fault` nodes
carry the real cause:

```text
Error code: 400 - invalid_request_error
"You have reached your specified API usage limits.
 You will regain access on 2026-09-01 at 00:00 UTC."
```

**Measured.** The pre-Monday audit reported **"Faults today = 0"** while those 18 were being
written, and it was reported as a PASS three times. `Fault` nodes stamp **`occurred_at`**; the query
read `props->>'created_at'`, which is `NULL` on every `Fault` node. Counted both ways at the same
moment: `occurred_at > '2026-08-08T06:50'` → **18**; `created_at > …` → **0**.

A green that comes from querying a field which does not exist is indistinguishable from a real
green. Same shape as DL-94 (a teardown counting the wrong rows), and worse here, because this was
the instrument certifying the system clean before a trading run.

## Scope — two items, both bounded

### 1. Reading Faults goes through one helper that cannot read a missing field

- Add a single place (suggested: `kernel/fault_query.py`) answering *"which Faults occurred in this
  window"* and *"how many"*. Every caller uses it; **no caller may name a `Fault` timestamp property
  inline.**
- The helper **must fail loudly on a property that does not exist** rather than returning an empty
  result. A typo or a renamed field has to raise, not report zero.
- Sweep existing callers onto it. **Assumed, not verified:** that the affected callers are limited
  to `scripts/` audit code and the `diagnose-run` path. Confirm with a repo-wide grep for `Fault`
  alongside `created_at` / `occurred_at`; do not trust this list.

### 2. A fail-open records why it failed open

- `FAIL_OPEN_RATIONALE` in `agents/deliberator/review_record.py` is a **fixed string** asserting a
  cause (`"llm unavailable"`) the code never established. Keep a human-readable rationale, and add a
  **queryable** `failed_open_reason` to the `DeliberationRun` — the exception class plus a truncated
  message.
- This is the S158 lesson one level deeper: S158 replaced a rationale *substring* with counted
  facts. The counts are right; the reason attached to them is still a guess.

## What must NOT change

- **Fail-open stays.** An LLM outage must never block a run (S147,
  [ADR-0022](../decisions/0022-the-veto-gates-buys-never-exits.md)). This sprint changes what a
  fail-open *records*, never whether it happens.
- **Do not touch the S166 gate.** `deliberation_status`, the grace window and the buys-only rule are
  proven in production and out of scope.
- No change to execution's submit path.

## 🪤 Traps

- **`DeliberationRun` is one of the five property-enforced labels** (`DeliberationRun`,
  `BrokerPositionSnapshot`, `Fill`, `LLMCall`, `Recommendation`). Adding `failed_open_reason`
  **moves the vocabulary pack**, so the deploy is a full `pwsh infra/deploy-agents.ps1 up -Tag <tag>`,
  **not** an image-only retag. A stale pack raises `VocabularyError` fail-closed on the first write
  and stalls the run mid-cascade (S148 / DL-79). Declare the new property in
  `orchestration/packs/trading_graph_vocabulary.json` in the same commit.
- **The API limit is not yours to fix.** Access returns **2026-09-01 00:00 UTC**; it is an account
  setting, not code. Every run until then will legitimately fail open. Do not "fix" it with retries,
  wider timeouts, or by suppressing the fault.
- Faults collapse (S155 `FaultSuppression`). **Measured:** `FaultSuppression` count was **0** at the
  time of writing, so these 18 were not collapsed. If you change fault reading, make sure a
  collapsed fault is still counted.

## Success factors

- [ ] Exactly one code path reads `Fault` timestamps; a repo-wide grep finds no inline property name.
- [ ] Querying a non-existent Fault property **raises**, proven by a test that expects the raise.
- [ ] A fail-open `DeliberationRun` carries a `failed_open_reason` naming the real error, with the
      400-usage-limit case covered by a test.
- [ ] `failed_open_reason` is declared in the vocabulary pack.
- [ ] Every new behaviour observed failing on a **planted defect first** (DL-70) — including one that
      reproduces the exact `created_at`/`occurred_at` mistake and shows the helper catching it.
- [ ] `make ci` exit 0, 100 % coverage, **measured unpiped to a file**
      (`make ci > /tmp/ci.txt 2>&1 ; echo $?` then read the file — a pipe reports the pipe's exit
      code, hardening row S).
- [ ] Remote `make gate-ran` exit 0 before merge.

## Process

Full cycle: worktree → own branch → `make ci` locally → push → `make gate-ran` **exit 0** → merge to
`main` locally → push → cut the `v0.89.08` tag. PRs are not required. Run the delegated agent with
`--sandbox workspace-write` (hardening row N).

## Closeout — evidence

_To be filled by the implementer before handback. A handback with this section unfilled is not
accepted._

**Local gate.** _`make ci` exit code, pass/skip counts, coverage %._

**Planted defects (DL-70).** _Table: what was planted → which tests failed._

**Remote gate.** _`make gate-ran` output and the full SHA._

**Deploy note.** _Confirm whether the pack hash moved, and therefore which deploy path applies._

**Not proven.** _State plainly what this sprint does NOT establish._
