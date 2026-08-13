<!-- Agent: deliberator | Role: sprint spec — stop the veto asserting evidence it did not compute, and stop an unreviewed order counting as an approved one -->
# S175 — the veto says only what it can prove

**Closes:** work-queue items 4 and 6 · **Opens from:** [DL-104](../design-log.md) (a), (b), (d) ·
**Type:** fix ·
**Target version:** next available PATCH at merge — **do not pin it in this file** ·
**Branch:** `sprint-175-the-veto-says-only-what-it-can-prove`

> Handover to a delegated coding agent. Everything under **Measured** was read off this repo or the
> live spine on 2026-08-13, after S174 shipped. Everything marked **Assumed** has **not** been
> verified — check it before building on it. Do not treat an unmarked claim as measured.

## Why

Three defects, one theme: **the veto states things it has not established.** They are bundled
because they share a blast radius — the deliberator and execution's read of its verdict — so one
branch, one CI cycle, one deploy.

### 1 · The invented ATR fragment, and S174 just made it worse

[`context_pm.py:146`](../../agents/deliberator/context_pm.py) `_atr_pct` averages the true range of
**every bar handed in**, then [`_atr_fragment`](../../agents/deliberator/context_pm.py) renders
`stop_pct vs ATR% -> PASSED/FAILED` **inside the `stop_vs_regime_volatility gate:` line** — a gate
that compares `stop_pct`/`target_pct` to the regime bases and **never performs that comparison at
all**. DL-104 attributed **6 of 15** veto objections to this one string, across *both* vendors.

**Measured today, and this is new.** S174 took the window from 41 bars to 202, so the invented
figure moved with it:

| Ticker | analyst `atr_pct` (14-period, real) | deliberator ATR% @ 41 bars | @ 202 bars | fragment @ 41 | fragment @ 202 |
| --- | --- | --- | --- | --- | --- |
| AMD | **7.32 %** | 7.81 % | **4.07 %** | `FAILED` | **`PASSED`** |
| XOM | **2.51 %** | 2.17 % | 2.15 % | `PASSED` | `PASSED` |

**AMD flips `FAILED` → `PASSED` on the same order, same 5 % stop, same regime, same gate — only the
history window changed.** The number also now disagrees with the analyst's own ATR by **3.25
percentage points**. A fragment whose verdict is decided by an unrelated sprint is not evidence.

### 2 · A fail-open is stored as `uphold`, so an unreviewed order trades

[`review_record.py:41`](../../agents/deliberator/review_record.py) `fail_open_review()` returns
`OrderReview("uphold", …, failed_open=True)`. [`poll.py:77`](../../agents/deliberator/poll.py) then
builds the veto list as `if review.verdict != "uphold"` — so **a fail-open is never added to
`vetoed_tickers`**, and [`deliberation_gate.py`](../../agents/execution/deliberation_gate.py)
`drop_vetoed` reads *only* `vetoed_tickers`. The `failed_open` flag is recorded and never consulted.

**Proven live on `sched-2026-08-13`, not theorised:** three debates failed open; execution submitted
3 of 8; **two of those three (AMD, DOW) reached the paper broker on fail-open verdicts** — orders
with no review at all, indistinguishable at the gate from a genuine `uphold`. Only VZ was really
upheld.

🟢 **This one needs no new graph property.** `failed_open_tickers` is **already** in the
property-enforced vocabulary pack and **already written** by `poll.py`. Execution simply never reads
it. No pack move.

### 3 · The veto reasons about portfolio state it cannot see

The packet carries per-ticker sector ([`context.py:121`](../../agents/deliberator/context.py)) and
**no portfolio or batch context at all** — no holdings, no position count, no sibling orders in the
same PMRun. DL-104 recorded the veto concluding *"deployed=0 despite holding USB and WFC"* on a flat
book. **Measured today:** it objected that *"GOOG is treated as a new ticker even though the
portfolio already holds GOOGL"* — an objection it had no data to support, which happens to be a
reasonable point about dual-class tickers. **A model guessing correctly is still guessing.**

## The design decisions this sprint has to make

1. **Fragment: delete, or relabel honestly?** Deleting is smallest and removes a real input the
   model may be using. Relabelling must stop implying a gate outcome — no `PASSED`/`FAILED` inside a
   `gate:` line for a comparison no gate makes. **Recommended: delete**, and record the reasoning.
2. **What does a fail-open mean at the gate?** 🚨 **Do not simply flip it to fail-closed** — S147
   chose fail-open deliberately so a vendor outage cannot halt trading, and the Anthropic key is
   usage-limited to 2026-09-01. The defect is that it is **invisible and unlabelled**, not that it
   permits. Make an unreviewed order *distinguishable* first; whether it also blocks is a posture
   decision (see 3).
3. **Advisory vs binding must be declared, not accidental** (DL-104 d). Today there are **two**
   silent routes to an unreviewed order reaching the broker: the grace expiring
   (`proceeded_unvetoed`, at least loud) and a fail-open (silent). A declared mode makes both
   answerable. 🪤 This is a **safety posture, not a free tunable** — a switch that can turn the veto
   off belongs in an ADR with the reasoning, not in a `tunable()` an experiment can move.
4. **Batch context: supply it, or forbid reasoning about it?** Giving the packet portfolio state is
   more work and more tokens; instructing the model that it cannot see the book is cheaper and
   honest. Either is defensible — record the rejected one.

Record every rejected option in `docs/design-log.md` (LAW-06).

## Steps, in order

1. **Reproduce first.** Re-render the PM context for AMD off `market-data:sched-2026-08-13` and
   quote the fragment as it stands. That is the before half.
2. **Remove or relabel the fragment** (decision 1).
3. **Make a fail-open distinguishable at the gate** — execution must be able to tell *reviewed and
   upheld* from *never reviewed*, using the `failed_open_tickers` that already exists.
4. **Declare the posture** (decision 3), with the ADR if that is the route.
5. **Fix the batch-context claim** (decision 4).
6. **Full CI cycle** — `make ci` redirected to a file, never piped; push; `make gate-ran` **from the
   worktree whose HEAD is the commit**; then merge.

## Success factors

- [ ] No string in the PM packet renders a `PASSED`/`FAILED` for a comparison the PM gate does not
      perform. Add a test that fails if one is reintroduced.
- [ ] Given a `DeliberationRun` with a fail-open for ticker X, execution's behaviour for X is
      **explicitly asserted** in a test and is not silently identical to a genuine `uphold`.
- [ ] A named replay of `sched-2026-08-13`'s AMD packet shows the fragment gone (or honest), quoted
      before and after.
- [ ] The posture is declared somewhere a reader can find it, and the routes not taken are in the
      design log.
- [ ] `make ci` green at the 100 % floor; `make gate-ran` exits 0 on the final SHA.

## Traps

- 🪤 **`DeliberationRun` is property-enforced.** A **new** property on it moves the vocabulary pack
  and forces a full `pwsh infra/deploy-agents.ps1 up`, which still discards operator env until
  [S169](sprint-169-one-switch-and-a-deploy-that-keeps-it.md) lands. Its allowed properties already
  include `failed_open_count`, `failed_open_reason`, `failed_open_tickers`, `verdicts`,
  `vetoed_tickers` — **step 3 needs none beyond these.** If your design needs a new one, say so in
  the closeout and stop.
- 🚨 **Do not make the veto fail closed as a side effect.** An outage must not stop trading. If your
  change would block orders when the LLM is unreachable, that is a posture change requiring the
  operator, not an implementation detail.
- 🪤 **This changes verdicts, so it changes trades.** Removing a fragment that produced ~40 % of
  objections will reduce vetoes. That is the point, not a regression — but it also means verdicts
  before and after this sprint are **not comparable**, which matters for
  [S173](sprint-173-a-verdict-must-be-reproducible.md)'s 56 % self-agreement baseline. Say so in the
  closeout; S173 must re-baseline after this lands.
- 🪤 **`effort` and `request_timeout_seconds` are live and coupled.** `DELIBERATOR_EFFORT=high` with
  `request_timeout_seconds=60` (raised from 30 on 2026-08-13 after three fail-opens). At `effort=high`
  the peer-call tail measured **39.1 s** across 32 calls versus **23.0 s** across 90 pre-`effort`
  calls. If you add turns or lengthen prompts you move that tail again. Measure it.
- 🪤 **`sched-2026-08-13` was consumed early**, so the next scheduled run is **2026-08-14** and it is
  the single-variable readout for the 60 s timeout. Do not deploy this sprint before that run is
  read, or you confound it.

## Handover — paste this to Codex

```text
Work item: S175 — the veto says only what it can prove.
Repo: trading-agents. Read docs/sprints/sprint-175-the-veto-says-only-what-it-can-prove.md in full
before writing anything. Read CLAUDE.md. Read docs/INDEX.md before opening any docs folder.

WHAT IS WRONG (three defects, one branch)
1. The deliberator's PM context renders "stop_pct vs ATR% -> PASSED/FAILED" inside a line labelled
   "stop_vs_regime_volatility gate:", for a comparison no gate performs, using an ATR averaged over
   every bar supplied. After S174 widened the window 41 -> 202 bars, AMD flipped FAILED -> PASSED on
   an unchanged order. DL-104 attributed 6 of 15 veto objections to this one string.
2. A failed-open debate is recorded with verdict "uphold", so it never enters vetoed_tickers and
   execution cannot tell an unreviewed order from an approved one. On 2026-08-13 two orders (AMD,
   DOW) reached the paper broker this way. failed_open_tickers ALREADY exists on DeliberationRun and
   is already written - execution just never reads it. No new graph property is needed.
3. The packet carries no portfolio or batch context, and the model reasons about the book anyway.

HOW TO WORK
- Branch first, before any code: sprint-175-the-veto-says-only-what-it-can-prove. Never commit
  sprint work to main. Work in a git worktree.
- The spec names four design decisions and recommends where it can. Choose deliberately, then record
  the options you rejected and why in docs/design-log.md (LAW-06).
- uv only: `uv pip`, `uv run`. Agents never import other agents. Modules hard-block at 200 lines.
- Constants that influence a forecast go through kernel.config.tunable() with a `why=`.

WHAT NOT TO DO
- Do NOT make the veto fail closed. S147 chose fail-open deliberately so a vendor outage cannot halt
  trading. The defect is that a fail-open is invisible, not that it permits. Making it
  distinguishable is in scope; making it block is a posture decision for the operator.
- Do NOT add a new property to DeliberationRun. It is property-enforced; a new one moves the
  vocabulary pack and forces a full deploy that still wipes operator env (S169, unfixed). The
  properties you need already exist. If you believe you need a new one, stop and say so.
- Do NOT treat fewer vetoes after this change as a regression. Fewer is the goal.

HOW TO PROVE IT
- LAW-02: success is proven, never assumed. Do not report an intent as an outcome.
- `make ci > ci.txt 2>&1 ; echo $?` then READ ci.txt. Never `make ci | tail` - a pipe reports tail's
  exit code, so a real failure reads as green. All 11 steps, 100% coverage.
- Push the branch, then run `make gate-ran` FROM THE WORKTREE whose HEAD is the commit you are
  proving; it ignores any SHA= argument and resolves from the working directory. Check the SHA it
  prints against `git rev-parse HEAD`. Merge only after it exits 0. No PR required.
- Required before/after: the AMD packet fragment replayed off market-data:sched-2026-08-13, and a
  test showing execution's behaviour for a fail-open ticker is explicitly asserted rather than
  incidentally equal to an uphold.
- Fill in the "Closeout - evidence" block with real measurements. A handback with the placeholder
  comment still in it is not accepted.
```

## Closeout — evidence

**Result:** implemented on branch `sprint-175-the-veto-says-only-what-it-can-prove`.

**Files changed:** `agents/deliberator/context.py`, `agents/deliberator/context_pm.py`,
`agents/execution/deliberation_gate.py`, `agents/execution/deliberation_faults.py`,
`agents/execution/poll.py`, `agents/execution/tests/test_execution_poll.py`,
`tests/test_veto_context.py`, [ADR-0022](../decisions/0022-the-veto-gates-buys-never-exits.md),
`docs/decisions/INDEX.md`, `docs/design-log.md`, `docs/STATE.md`, `pyproject.toml`, and `uv.lock`.

**Design decisions:** recorded as
[DL-108](../design-log.md#dl-108---s175-makes-the-veto-say-only-what-it-can-prove---status-decided-2026-08-13).

1. Removed the invented ATR pass/fail fragment instead of relabelling it advisory. Rejected:
   retaining `stop_pct vs ATR% -> PASSED/FAILED`, because no PM gate performs that comparison;
   adding a new volatility gate, because that is a new posture rather than a correction.
2. Added execution's `applied_failed_open` status using existing `DeliberationRun.failed_open_tickers`.
   Rejected: a new graph property, because `DeliberationRun` is property-enforced and the needed
   property already exists; treating fail-open as `uphold`, because it hides an unreviewed order.
3. Kept S147's fail-open posture and made it loud. Rejected: fail-closed execution, because vendor
   outage blocking is an operator posture decision; an experiment tunable, because veto binding
   mode is governance, not a forecast parameter.
4. Declared portfolio and batch context absent in the packet. Rejected: adding book/batch facts in
   this sprint, because the immediate defect is a false claim, and adding portfolio state would be a
   larger prompt/data-contract change.

**AMD packet replay, production graph source `market-data:sched-2026-08-13`:**

```text
pmrun=pm-run-50de809f427247af8e1ed7f806a6ef39
market=market-data:sched-2026-08-13
before: stop_vs_regime_volatility gate: stop_pct=5.00% vs base_stop_loss_pct=5.00% -> PASSED; target_pct=10.00% vs base_take_profit_pct=10.00% -> PASSED; stop_pct=5.00% vs ATR%=4.07% -> PASSED
after:  stop_vs_regime_volatility gate: stop_pct=5.00% vs base_stop_loss_pct=5.00% -> PASSED; target_pct=10.00% vs base_take_profit_pct=10.00% -> PASSED
```

The after packet also states the boundary explicitly:

```text
Portfolio/batch context: unavailable; this packet contains no holdings, open positions, sibling orders, or dual-class exposure facts. Reviewers must not infer them beyond the explicit PM gate outcomes rendered below.
```

**Fail-open proof:** `test_execute_pm_node_marks_failed_open_deliberation_without_blocking` builds a
`DeliberationRun` with `failed_open_tickers=["AAPL"]`, then asserts all three outcomes: the order is
still submitted, the `ExecutionRun.deliberation_status` is `applied_failed_open` rather than
`uphold`, and a `DeliberationFailedOpenSubmit` fault is recorded. The malformed-payload regression
test proves execution does not fabricate a fail-open or veto from an invalid
`failed_open_tickers` value.

**Vocabulary pack:** did **not** move. `orchestration/packs/trading_graph_vocabulary.json` has no
diff; this change uses `failed_open_tickers`, which is already allowed on `DeliberationRun`.

**S173 baseline impact:** S173's 56 % self-agreement baseline is no longer comparable after this
lands. Fewer veto objections are expected because the packet no longer presents an invented
`stop_pct vs ATR%` pass/fail result that DL-104 tied to 6 of 15 objections. S173 must re-baseline
after S175 is merged and, later, deployed.

**Focused tests:** red-before-green was captured with
`uv run pytest tests/test_veto_context.py agents/execution/tests/test_execution_poll.py --no-cov`;
it failed on the missing portfolio boundary, the still-present ATR wording, and the absent
`DeliberationFailedOpenSubmit` fault (`3 failed, 9 passed`). After the fix, the same target passed
(`12 passed in 1.20s`), and the expanded focused target
`uv run pytest tests/test_veto_context.py agents/execution/tests/test_execution_poll.py agents/execution/tests/test_execution_deliberation_gate.py --no-cov`
passed (`25 passed in 1.24s`).

**`make ci` evidence:** ran unpiped and redirected as
`make ci > ci.txt 2>&1; $exit=$LASTEXITCODE; Write-Output "MAKE_CI_EXIT_CODE=$exit"` from the S175
worktree; exit code `0`.

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
974 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 803 source files
uv run lint-imports
Contracts: 4 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run pytest
TOTAL                                                14540      0   3080      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
================= 2238 passed, 6 skipped in 97.39s (0:01:37) ==================
uv run pip-audit
No known vulnerabilities found
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 2 new file(s)
```

**Remote gate:** `make gate-ran` must be run after the final commit is pushed from the worktree
whose `HEAD` is being proved. Its output is intentionally not pre-pasted into this committed
closeout, because editing this file after the gate would change the SHA the gate proved. The final
handoff must quote the `make gate-ran` output and compare its printed SHA to `git rev-parse HEAD`
before merge.
