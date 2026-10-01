<!-- Agent: planning | Role: sprint handover -->
# Sprint 249 — a run's market window ends on the run's as-of date, whenever the provider gets to it

**Phase:** Etalon-first continuous improvement (DL-19) · work-queue 103
**Branch:** `sprint-249-a-runs-market-window-ends-on-its-as-of`
**Status:** MERGED 2026-10-01 — `0.120.03`, fast-forwarded to `f3956bac`, tag `v0.120.03`, GATE PROVEN `f3956bac` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,793 passed, 8 skipped, 100.00 %); built by a Claude cloud session on `claude/vibrant-pasteur-4x99vq` (cut from `main` `a9fff56`); **F1 PASS** (the merged provider on the live sources, a request for as-of 2026-09-30 ingested on 2026-10-01: `window_end` 2026-09-30, 203 bars a name, 10 of 10 names identical to `sched-2026-09-30`, on the single and the chunked path); DL-256, provider laws v1.7 (22 / 67), DRIFT-095 corrected; **deployed `s249`** 2026-10-01 17:01–17:08 AEST (operator: *"you can retag"*): image-only, the three injected packs byte-identical between `v0.120.02` and `v0.120.03`; build `36827807053` **15 / 15** from `f3956bac`; **16 / 16** apps and `dispatcher-cron` on `s249`, all `Succeeded`, one active revision each, latest = ready; CPU, memory, env counts and the full scale blocks identical to the pre-retag snapshot; `DeployRecord` written; rollback `s248`
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-255](../design-log.md) (the defect, measured, and the direction) · the builder's
decisions go to the **next free DL** (`DL-256` at spec time) · opens **DRIFT-095**

> **Why this bump kind.** No new capability. A `RunRequest` already carries its as-of date and the
> provider already serves a window; the provider ignores the first when it builds the second.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/provider/laws/laws.md` | The provider's **locked constitution**, v1.6 | **LOCKED.** This sprint amends it by one clause, named below, and nothing else |
| `agents/provider/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`IN`**, **`TRG`**, **`STA`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read `agents/provider/laws/test-plan.md` alongside `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Read the law-cycle answer below.** It is already decided: this sprint owes a clause.
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
   *(S248's builder met a contradiction that was older than the sprint and did not change what the
   sprint touched; it recorded a drift row and carried on, and that was accepted. Use the same
   judgement: stop when the contradiction is about what you are changing.)*
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered here: **YES**

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

Both. `contracts/provider.py` gains a constant for the `RunRequest` property that holds the as-of,
and the provider gains a guarantee no clause states. *[measured 2026-10-01]* `PROV-TRG-02` names a
`RunRequest` as a trigger and `PROV-IN-02` accepts a regime request "with a single as-of date";
nothing says which dates a run's ingest serves.

So this sprint owes a **law cycle in the same unit of work**:

- A new clause **`PROV-TRG-05`** (the next free `TRG` id; IDs are append-only). It must say, in your
  wording: an ingest triggered by a `RunRequest` serves that run's as-of date. The market window ends
  on it and starts the declared lookback before it; the regime is read as of it; the news and
  earnings windows are anchored on it. This holds whenever the provider reaches the request. An
  ingest with no run behind it serves today.
- `laws.md` version **v1.6 → v1.7** with a Changelog line that names the *why* (DL-255).
- `test-plan.md` rows for the clause, the clause ID in each test docstring.
- The rollup in **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` (21 / 66 today).
  🪤 The rollup is derived: `make ci` recomputes it. Let the gate tell you the number.
- **DRIFT-095** in `docs/laws/drift-register.md`: the law was silent and the code used the clock.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/provider/poll.py`, `ingest.py`, `ingest_chunked.py` | `agents/provider/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `PROV-TRG-02` a `RunRequest` is the trigger; `PROV-IN-02` regime by as-of; `PROV-STA-04` every stored datum carries its as-of; new `PROV-TRG-05` |
| `contracts/provider.py` | same | the `RunRequest` property names live here (`RUN_REQUEST_*_PROP`) |
| `orchestration/start.py` | `docs/laws/conventions.md` | the writer of the `RunRequest`; it must write the same property name it writes today |

⚠️ **A scheduled run must not change.** Its as-of is the UTC day it runs, so its window is the same
before and after this sprint. If any test of the scheduled path needs a different expected value,
stop: something else moved.

---

## Goal

At merge, a `RunRequest`'s ingest serves the run's own as-of. `MarketData.window_end`,
`RegimeContext.window_end` and the regime's as-of all equal the request's as-of date, the bar window
starts the declared lookback before it, and the news and earnings windows are anchored on it. A test
run fired the next morning for yesterday's session reads the same window as the scheduled run did.

## Why (context)

The fleet test run `verify-2026-10-01-s248-a` was placed for as-of 2026-09-30, the same session as
that morning's `sched-2026-09-30`. It read 202 bars a name where the scheduled run read 203, and it
bought TGT where the scheduled run had rejected it.

The provider builds its window from the clock. `agents/provider/ingest.py:72-75` (`_today_window`)
returns `today − lookback … today`, and `ingest_once` (`:167`) and `ingest_chunked`
(`ingest_chunked.py:136`) both use it. `agents/provider/poll.py:90-99` (`ingest_run_node`) reads the
request's tickers, run id, lookback and benchmark, and never its as-of. The regime is then read as of
`window.end` (`ingest.py:177`), and the news and earnings fetches anchor on `window.end`
(`fundamentals.py:98`, `:139`), so they follow the clock too.

Every test run and replay for a past session therefore reads a window shifted to the day it happens
to run, with headlines published after its as-of. A scheduled run that the provider reached after
00:00 UTC would shift the same way; the run window is 22:30–00:30 UTC, so that is one late start away.

### Measured, 2026-10-01 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| A run with as-of 2026-09-30, ingested on 2026-10-01, writes `window_end` 2026-10-01 | yes | *[measured, no `.env`]* the reproduction below, on `InMemoryGraphStore` with `FakeDataSource` |
| The regime context and the regime's own as-of move with it | yes | *[measured, no `.env`]* same reproduction |
| Live `RunRequest`s carrying `requested_at`, and its shape | **81 of 81**, a 10-character date string | *[measured, Neon]* `Counter` over `RunRequest.requested_at` |
| Scheduled runs whose `window_end` differs from their as-of | **0 of 60** | *[measured, Neon]* `RunRequest.requested_at` against `regime-context:{run_id}.window_end` |
| Other runs whose `window_end` differs from their as-of | **8 of 21**, each by one day | *[measured, Neon]* six `check-s16x` / `check-s17x` runs (as-of 08-07, window 08-08), `probe-s178-flaglifecycle` (08-17 / 08-18), `verify-2026-10-01-s248-a` (09-30 / 10-01) |
| The two runs for 2026-09-30 | scheduled: `window_end` 09-30, 203 bars a name, 2025-12-09 → 2026-09-30. Test: `window_end` 10-01, 202 bars a name, 2025-12-10 → 2026-09-30 | *[measured, Neon]* `market-data:{run_id}`; the newest bar and its close are equal (AAPL 333.02, TGT 156.69) |
| What it changed | scanner dropped 44 on relative strength against 41; TGT 0.587 (reject) → 0.61 (buy); 1,855 headlines against 1,894 | *[measured]* `scripts/trace_run.py` on both runs. The split between the bar shift and the newer headlines was not measured |
| News and earnings anchor on `window.end` | yes | *[measured, read and run]* `fundamentals.py:98` `news_to = window.end`; `:139` `from_date = window.end`. B4 below asserts it |
| The bar source can serve a window that ended in the past | yes | *[measured, read]* `agents/provider/alpaca_request.py:57-69`: a SIP `end` is midnight after `window.end`, capped by the recent-data wall; existing tests `test_sip_past_window_ends_at_the_midnight_after_it` |
| The lookback on the request is already declared against the as-of | yes | *[measured, read]* `orchestration/start.py:73-80`, `declared_lookback_days(settings, as_of=requested, …)` |
| The coverage check uses the clock | yes | *[measured, read]* `agents/provider/poll.py:142-145`, `_covered_sessions` |
| Wall-clock date reads in `agents` | **11**: the two this sprint fixes (`ingest.py:74`, `poll.py:143`), the barrier history's (`barrier_history.py:94`), and 8 in the analyst, forecaster, monitor, portfolio manager and scanner | *[measured]* `grep -rn -E "datetime\.now\([^)]*\)\.date\(\)" agents` excluding tests. **Which of the 8 run inside a graph-pull run is not measured**; see Out of scope |

**The reproduction** (run from the repo root, no `.env`):

```python
from datetime import UTC, datetime

from agents.provider import ProviderAgent
from agents.provider.poll import ingest_run_node
from agents.provider.sources import FakeDataSource
from contracts.provider import (
    MARKET_DATA_LABEL,
    RUN_REQUEST_LABEL,
    RUN_REQUEST_LOOKBACK_DAYS_PROP,
    RUN_REQUEST_REQUIRED_HISTORY_BARS_PROP,
)
from kernel import InMemoryGraphStore, InProcessBus

AS_OF = "2026-09-30"
graph = InMemoryGraphStore()
agent = ProviderAgent(InProcessBus(), graph=graph, source=FakeDataSource())
node = graph.merge_node(
    RUN_REQUEST_LABEL,
    "run-request:r1",
    {
        "run_id": "r1",
        "tickers": ["AAPL"],
        "requested_at": AS_OF,
        RUN_REQUEST_LOOKBACK_DAYS_PROP: 365,
        RUN_REQUEST_REQUIRED_HISTORY_BARS_PROP: 200,
    },
)
ingest_run_node(node, agent=agent)
market = graph.get_node(MARKET_DATA_LABEL, "market-data:r1")
regime = graph.get_node("RegimeContext", "regime-context:r1")
print("today (UTC)             :", datetime.now(tz=UTC).date())
print("run's as-of             :", AS_OF)
print("MarketData.window_end   :", market.props["window_end"])
print("RegimeContext.window_end:", regime.props["window_end"])
print("regime as_of            :", str(regime.props["snapshot"].get("as_of"))[:10])
```

Output on `main` @ `99ea8487`, run on 2026-10-01:

```text
today (UTC)             : 2026-10-01
run's as-of             : 2026-09-30
MarketData.window_end   : 2026-10-01
RegimeContext.window_end: 2026-10-01
regime as_of            : 2026-10-01
```

The last three lines should read `2026-09-30` on any day the script is run.

---

## Scope — and what is deliberately NOT here

1. **The failing tests first.** B1, B2 and B3 from the test plan, red on `main`, pasted in the
   Closeout.
2. **The as-of has a name in the contract.** `contracts/provider.py` gains
   `RUN_REQUEST_REQUESTED_AT_PROP = "requested_at"`, beside the three constants already there.
   `orchestration/start.py` writes it by that name. **The value stays `"requested_at"`**: 81 live
   nodes and the readers in `surfaces/` use it.
3. **The provider reads it.** `ingest_run_node` takes the as-of from the request and the window is
   `as-of − lookback … as-of`, on both the single and the chunked path. The regime request, the
   stored `window_end` values, and the news and earnings anchors follow because they already key on
   `window.end`.
4. **The coverage check uses it.** `_covered_sessions` counts sessions up to the as-of, the same
   date the dispatcher declared the lookback against.
5. **An ingest with no run keeps today.** `ingest_once` called without an as-of behaves as now.
6. **The law cycle** named above: `PROV-TRG-05`, v1.7, test-plan rows, both rollups, DRIFT-095.

### Out of scope (do NOT build this sprint)

- **The 8 wall-clock date reads in five other agents.** `agents/analyst/agent.py:128`,
  `agents/forecaster/agent.py:164`, `factor_signal.py:78`, `price_signal.py:79`,
  `settlement_pass.py:139`, `agents/monitor/provider_client.py:63`,
  `agents/portfolio_manager/agent.py:119`, `agents/scanner/agent.py:182`. They build windows for
  requests an agent sends to the provider directly. Whether any of them runs inside a graph-pull run
  is not measured, and the monitor's is a "latest price" read that may be right as it is. They stay
  in work-queue 103 as its second part.
- **The barrier history window** (`agents/provider/barrier_history.py:94`). DL-241 and DL-243 tie a
  barrier claim to the run's creation date on purpose, and settle it against real later sessions.
  Whether a past-as-of run should make a claim at all is a design question, not this fix.
- **Fundamentals and sectors.** The sources serve the latest value only. A past-as-of run still
  reads today's fundamentals; nothing in this sprint can change that, and the spec does not claim
  point-in-time replay.
- **The readers of `requested_at` in `surfaces/`** and `orchestration/resume.py`, which copies it.
- **No new label, property, env key or tunable.** The property already exists on every `RunRequest`.
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Derive the as-of from the run id** (`sched-2026-09-30`). Rejected: test runs and resumes do not
  carry a date in their id, and they are the runs this defect hits.
- **Have the dispatcher write the window on the request.** Rejected: the lookback and the as-of are
  already there; a third field would be a second copy of the same fact, free to disagree.
- **Leave the provider alone and forbid past-as-of runs.** Rejected: 8 of 21 non-scheduled runs
  already are, and a scheduled run reached after midnight UTC is one too.
- **Fix all 11 wall-clock reads in one sprint.** Rejected: 8 of them are in five other agents with
  five law books, and which matter is not measured. The provider's ingest is the run's foundation.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **A `RunRequest` with no as-of, or one that does not parse.** Recommended: refuse it with a
   `ValueError`, as `_lookback_days` already does for a bad lookback. All 81 live requests carry one,
   and falling back to today is the defect this sprint removes. The cost: the helper in
   `agents/provider/tests/test_provider_poll.py` builds requests without one and must add it.
2. **Which strings parse.** The dispatcher writes a 10-character date. Decide whether a full ISO
   datetime is also accepted (its date) or refused, and prove the choice.
3. **How the as-of reaches the window**: a parameter on `ingest_once` and `ingest_chunked`, or a
   `Window` built in `poll.py` and passed down. Mind the sizes below.
4. **An as-of in the future.** Decide: refuse, or serve up to today. The dispatcher never writes one.

🪤 **Take the next free DL number, then re-check it at merge.** `DL-256` at spec time.

---

## Blast radius — measured 2026-10-01

| What | Detail |
| --- | --- |
| Files changed | `contracts/provider.py` (**174**), `orchestration/start.py` (**100**), `agents/provider/poll.py` (**145**), `agents/provider/ingest.py` (**179**), `agents/provider/ingest_chunked.py` (**159**), a new test file beside `agents/provider/tests/test_provider_poll.py` (**94**), that file's request helper; `agents/provider/laws/laws.md`, `test-plan.md`; `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`; `docs/design-log.md`; this file and its README row |
| Agents affected | provider. `orchestration` writes the same property under a constant. No agent imports another |
| Contract change? | Yes: one constant in `contracts/provider.py`. The law cycle above is mandatory |
| Graph vocabulary change? | No. `RunRequest.requested_at` exists on all 81 live nodes |
| New env keys / tunables | None |
| Deploy implication | Image-only retag |
| Rollback | Retag to the previous tag. Nothing else to undo: each run's `MarketData` and `RegimeContext` are immutable nodes keyed by run id, and a rollback changes only how later runs build their window |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant B1, B2 and B3 first** and watch them fail. Paste the red output.
4. **Implement.**
5. **Law cycle:** `PROV-TRG-05`, v1.7, test-plan rows, docstring citations, both rollups, DRIFT-095.
6. **Prove the guards can fail (DL-70)** — the three plants in the handover, each red, pasted, restored.
7. **`make ci` green** — every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| B1 | 🎯 A run's window ends on its as-of | a `RunRequest` with as-of 2026-09-30 and a recording data source | the source is asked for a window ending 2026-09-30 and starting the lookback before it; `MarketData.window_end` is 2026-09-30 |
| B2 | 🎯 The regime is read as of the run's as-of | the same request, a recording regime source | the regime source is asked for 2026-09-30; `RegimeContext.window_end` is 2026-09-30 |
| B3 | 🎯 The chunked path does the same | the same request, `ingest_chunk_size` below the universe size | every chunk is asked for the same window ending 2026-09-30; one `MarketData`, `window_end` 2026-09-30 |
| B4 | News and earnings are anchored on the as-of | the same request, a recording source | the news window ends on 2026-09-30 and the earnings window starts on it |
| B5 | 🪤 A run whose as-of is today is unchanged | a `RunRequest` whose as-of is the UTC date the test runs on | the window equals `_today_window(lookback)` exactly |
| B6 | The coverage check uses the as-of | a past as-of whose lookback covers the required sessions as of that date; one whose lookback does not | the first is ingested; the second is refused with the existing error |
| B7 | 🪤 A request with no usable as-of | absent; empty; a string that is not a date | the behaviour decision 1 chose, with no fetch made |
| B8 | An ingest with no run keeps today | `ingest_once` with no run and no as-of | the window is today's, as now |
| B9 | The writer and the reader agree | `place_run_request(..., as_of=D)` then `ingest_run_node` on the node it wrote | `window_end` is `D`; the node carries the as-of under `RUN_REQUEST_REQUESTED_AT_PROP`, whose value is `"requested_at"` |

---

## Success factors

- [ ] The reproduction above prints the run's as-of on its last three lines.
- [ ] B1–B9 pass; B1, B2 and B3 were red on `main` first, and the red output is pasted.
- [ ] No existing test of the scheduled or standalone path changed its expected values.
- [ ] `RUN_REQUEST_REQUESTED_AT_PROP == "requested_at"`.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Law cycle done: `PROV-TRG-05`, v1.7, test-plan rows, both rollups, DRIFT-095.
- [ ] Each of the three guards planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

**Owed to the planner, not the builder:** `uv lock` with the PATCH bump, Windows `make ci`,
`make gate-ran` from the proving worktree, merge, the image-only retag, and one live check.
**F1** (before the deploy, no orders and no LLM call): the branch's provider, built with the live
data sources from `main`'s `.env` on an in-memory graph, ingests a request for as-of 2026-09-30; its
`MarketData` is compared with the live `market-data:sched-2026-09-30` read from Neon. Pass:
`window_end` 2026-09-30, 203 bars a name, the same first and last bar dates, the same closes.

---

## Traps

🪤 **The red tests are red only on a day that is not the as-of.** B1–B3 use a fixed past date, so
they fail on `main` whenever they run. Do not use "yesterday": compute nothing from the clock in the
expected value.
🪤 **Two test files import `_today_window`** (`test_ingest.py:17`, `test_ingest_chunked.py:16`).
Removing or renaming it forces edits in files at **175** and **198** lines. Keep it for the
standalone path and add beside it.
🪤 **`test_ingest_chunked.py` is at 198 lines.** Two more and `make ci` blocks. New tests go in a new
file.
🪤 **`ingest.py` is at 179 and `contracts/provider.py` at 174.** A parameter costs lines in three
signatures. Count before you finish, not after.
🪤 **A string compare is not a date compare.** `requested_at` is a string on the node. Parse it once,
at the edge, into a `date`.
🪤 **`FakeDataSource` returns no bars.** A test that asserts on bar dates needs its own recording
source; asserting on the `Window` the source was asked for is the direct check.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `ingest.py` **179**, `ingest_chunked.py` **159**, `poll.py` **145**,
  `contracts/provider.py` **174**, `orchestration/start.py` **100**, `test_ingest.py` **175**,
  `test_ingest_chunked.py` **198**, `test_provider_poll.py` **94**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. This sprint needs none.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it (the planner's, see below).
- Secrets never through the worktree — a worktree has **no `.env`**, so any proof needing live data
  is vacuous there. **State which tree you ran in.**
- 🪤 `make ci` does not run markdownlint and the commit hook does. Leave a blank line before and
  after every fenced code block, including inside list items.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** and check the printed SHA
   against `git rev-parse HEAD`.
2. **F1**, then merge to `main` locally and push. 🪤 Check you are not on the branch already.
3. **Post-merge CodeQL** on `main`, and the branch's open alerts against the last merged branch's.
4. The image-only retag (rollback tag recorded with the `DeployRecord`).

---

## Handover — paste this to the Claude cloud session

```text
Sprint 249 — a run's market window ends on the run's as-of date, whenever the provider gets to it.
Spec: docs/sprints/sprint-249-a-runs-market-window-ends-on-its-as-of.md on main (read ALL of it, then
CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-249-a-runs-market-window-ends-on-its-as-of, cut from main. Never main. If your session
forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. Every proof is a unit test on
InMemoryGraphStore with a fake or recording data source. You cannot run `make gate-ran`: it is owed to
the planner. Leave pyproject.toml's version and uv.lock untouched and say so. Take the next free DL
(DL-256 at spec time; re-check on main).

This handover is complete: nobody will send you follow-up messages. If something in the spec is wrong
or blocked, record it in the handback (Return notes, "not done") and stop; do not wait.

What and why: the provider builds a run's window from the clock. agents/provider/ingest.py:72-75
(_today_window) returns today - lookback .. today; ingest_once (:167) and ingest_chunked
(ingest_chunked.py:136) both use it; agents/provider/poll.py:90-99 (ingest_run_node) never reads the
RunRequest's as-of ("requested_at", a 10-character date string, written by orchestration/start.py).
The regime is read as of window.end, and news and earnings anchor on window.end, so they follow the
clock too. Measured live 2026-10-01: 8 of 21 test runs have window_end one day after their as-of
(0 of 60 scheduled runs); a test run for 2026-09-30 read 202 bars a name where the scheduled run read
203, and bought a name the scheduled run rejected. The spec carries a no-credentials reproduction
script and its output: run it first.

MUST RULE before any code: read, whole, agents/provider/laws/laws.md + test-plan.md,
docs/laws/conventions.md, docs/laws/drift-register.md. Fill the Law reading record first.

Law-cycle answer: YES (a contracts/ change and a guarantee no clause states). Add PROV-TRG-05: an
ingest triggered by a RunRequest serves that run's as-of (the market window ends on it and starts the
declared lookback before it; the regime is read as of it; news and earnings are anchored on it;
whenever the provider reaches the request; an ingest with no run serves today). laws.md v1.6 -> v1.7
with a Changelog line; test-plan rows; clause ID in every test docstring; rollups in
docs/laws/ledger.md AND docs/laws/INDEX.md (let make ci give the number); DRIFT-095.

Build:
1. contracts/provider.py: RUN_REQUEST_REQUESTED_AT_PROP = "requested_at" (the value must not change).
   orchestration/start.py writes the as-of under it.
2. agents/provider/poll.py: ingest_run_node reads the as-of, parses it once into a date, and the
   window is as-of - lookback .. as-of on the single and the chunked path. _covered_sessions counts
   up to the as-of.
3. ingest_once with no run and no as-of keeps today's window. Keep _today_window: two test files
   import it.
4. Law cycle.

Order: next free DL (decisions 1-4 with rejected alternatives) -> red B1, B2, B3 (paste) -> implement
-> law cycle -> DL-70 plants (use the clock again in the single path: B1 red; use it in the chunked
path: B3 red; read the regime as of today: B2 red; each red, paste, restore) -> make ci redirected to
a file, exit 0, 100.00 %.

DO NOT:
- change any expected value in a test of the scheduled path or the standalone path.
- touch the other wall-clock date reads (analyst, forecaster, monitor, portfolio manager, scanner) or
  agents/provider/barrier_history.py: out of scope, and the reasons are in the spec.
- change the value "requested_at", or touch surfaces/ or orchestration/resume.py.
- add a label, a property, an env key or a tunable.
- grow any module past 200 (test_ingest_chunked.py is at 198, ingest.py at 179: new tests go in a new
  file); # noqa to bypass a rule.
- compute an expected value from the clock in B1-B4.
- claim a live proof or GATE PROVEN: F1 and the gate are the planner's.
- pin a version: PATCH, next available at merge.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] Test plan results: B1-B9, each with final test name, file, PASS, clause IDs cited.
[ ] Closeout: the red run of B1, B2 and B3 pasted before the fix; the green run after.
[ ] The reproduction script's output after the fix (the last three lines read 2026-09-30).
[ ] Each of the three DL-70 plants: what was planted, its red output, restored.
[ ] The DL number used, with decisions 1-4 and their rejected alternatives.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file, exit code, passed/skipped, coverage 100.00 %, dependency audit, detect-secrets.
[ ] Exactly how pyproject.toml and uv.lock were touched (untouched and owed, or what changed).
[ ] Owed items named: uv lock + PATCH bump, make gate-ran, Windows make ci, F1, retag.
[ ] Status: BUILT in this file and in its docs/sprints/README.md row, in the same commit.
[ ] A blank line before and after every fenced code block in this file (the commit hook lints it).
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`, here and in the README row.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

*Written 2026-10-01, before the first code change, in the cloud session's checkout of `main` @
`a9fff56` (branch `claude/vibrant-pasteur-4x99vq`, the name the session forces; see Return notes).
Read whole: `agents/provider/laws/laws.md` (v1.6, 453 lines), `agents/provider/laws/test-plan.md`,
`docs/laws/conventions.md`, `docs/laws/drift-register.md`.*

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `agents/provider/poll.py` (`ingest_run_node`, `_covered_sessions`) | provider `laws.md` + `test-plan.md`; conventions | `PROV-TRG-02` (a `RunRequest` is a request, ⬜), `PROV-TRG-03` (a valid request is the precondition to fetch, ⬜), new `PROV-TRG-05` | **Yes.** `TRG-03` says an invalid request is refused *before any fetch*, so the as-of is parsed and checked at the top of `ingest_run_node`, beside the lookback check, and B7 asserts the source was never called. |
| `agents/provider/ingest.py`, `ingest_chunked.py` | same | `PROV-IN-01` (a valid window, `start ≤ end`, 🟩), `PROV-IN-02` (a regime request is a single as-of date, ⬜), `PROV-STA-04` (every stored datum carries its as-of, 🟩), `PROV-OUT-05` (append-only, ⬜) | **Yes.** `STA-04` is why the stored `window_end` must *be* the run's as-of, not the clock's day: the node already claims to carry its as-of, and today it carries the wrong one. One window helper serves both paths so the two cannot disagree. |
| `contracts/provider.py` | same; conventions §2 | `PROV-TYP-03` (the contract is versioned, ⬜) | No. The constant names an existing property; no type, field or version moves. |
| `orchestration/start.py` | conventions §5 | none of the provider's (the writer of the request) | No. It writes the same key under the constant. |
| `docs/laws/drift-register.md` | itself; conventions §9 | — | DRIFT-095 (the silence below). |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **YES, both**
(as the spec decided): a constant in `contracts/provider.py`, and a guarantee no clause states (which
dates a run's ingest serves). Owed and done in this unit of work: `PROV-TRG-05`, v1.6 → v1.7 with a
Changelog line, test-plan row, clause ID in every new test's docstring, both rollups, DRIFT-095.

**Contradictions found between a law and this spec:** none about what this sprint changes. One older
one, recorded and not acted on (S248's precedent): **DRIFT-082** (OPEN) — `PROV-TRG-01` still says the
provider acts *only* on a request event from its subscribed topic, and `PROV-TRG-05` is a second clause
that names a graph-pulled `RunRequest` as a trigger. `TRG-05` does not depend on `TRG-01`'s wording;
the widening stays with the planner.

**Laws found silent where a decision was needed:**

1. **Which dates a run's ingest serves** — no clause says (the spec's finding). `PROV-IN-02` says a
   regime request has one as-of; nothing ties it to the run. → `PROV-TRG-05`, DRIFT-095.
2. **What a `RunRequest` with an unusable as-of means** (absent, not a date, a datetime, a date after
   today). `TRG-03` says an invalid request is refused, but no clause says the as-of is part of a
   `RunRequest`'s validity. → decisions 1, 2 and 4 (DL-256), written into `PROV-TRG-05`.
3. **Which "today" an ingest with no run serves.** The code has always used the UTC date; no clause
   names a zone. `PROV-TRG-05` says "the UTC date it runs on", matching the dispatcher's default as-of
   (`scripts/dispatch_scheduled_run.py`, "defaults to today's UTC date").

**Clauses that were ⬜ and are now proven:** none. `PROV-TRG-05` is new and proven (B1–B9). B7 proves
a slice of `PROV-TRG-03` (an invalid as-of is refused before any fetch) and B2 a slice of `PROV-IN-02`
(the regime is read on one as-of), but neither covers its whole clause, so both stay ⬜ (conventions
§7a) and the B-tests cite `PROV-TRG-05` only.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| B1 | `test_a_runs_market_window_ends_on_its_as_of` | `agents/provider/tests/test_run_as_of_window.py` | PASS | `PROV-TRG-05` |
| B2 | `test_the_regime_is_read_as_of_the_runs_as_of` | `agents/provider/tests/test_run_as_of_window.py` | PASS | `PROV-TRG-05` |
| B3 | `test_the_chunked_path_serves_the_same_as_of` | `agents/provider/tests/test_run_as_of_window.py` | PASS | `PROV-TRG-05` |
| B4 | `test_news_and_earnings_are_anchored_on_the_as_of` | `agents/provider/tests/test_run_as_of_window.py` | PASS | `PROV-TRG-05` |
| B5 | `test_a_run_whose_as_of_is_today_is_unchanged` | `agents/provider/tests/test_run_as_of_window.py` | PASS | `PROV-TRG-05` |
| B6 | `test_the_coverage_check_counts_sessions_up_to_the_as_of` + `test_a_lookback_short_of_the_as_ofs_sessions_is_refused` | `agents/provider/tests/test_run_as_of_refusals.py` | PASS (both) | `PROV-TRG-05` |
| B7 | `test_a_request_with_no_usable_as_of_is_refused_before_any_fetch` (9 cases: absent, empty, `not-a-date`, a full datetime, `20260930`, `2026-W40-3`, `2026-9-30`, a non-string, `9999-12-31`) | `agents/provider/tests/test_run_as_of_refusals.py` | PASS (9 / 9) | `PROV-TRG-05` |
| B8 | `test_an_ingest_with_no_run_keeps_todays_window` | `agents/provider/tests/test_run_as_of_window.py` | PASS | `PROV-TRG-05` |
| B9 | `test_the_provider_serves_the_as_of_the_dispatcher_wrote` | `orchestration/tests/test_start_as_of.py` | PASS | `PROV-TRG-05` |

Fixtures: `agents/provider/tests/as_of_helpers.py` (`RecordingSource` records every OHLCV window and
regime date; `RecordingFinnhub` is the real `FinnhubDataSource` with its four downloads overridden,
so B4 checks the dates the Finnhub code computes from `window.end`, not just the window it is handed).
B1–B4 compare against the fixed dates 2026-09-30 / 2025-09-30 / 2026-09-23; nothing in them reads the
clock. B5 and B8 read it on purpose (their claim *is* "today"). B6 uses the 2025 Christmas week so the
as-of's count (5 sessions in 7 days) differs from any count the clock gives this week (6).

**Tests added beyond the plan:** B6 is two tests (one ingested, one refused) and B7 has nine cases,
one per form decision 2 and 4 refuse. No other test was added. Three existing helpers gained the as-of
*input* (decision 1's stated cost), with no expected value changed: `test_provider_poll.py`'s
`_run_request` and its short-lookback node (`"2026-09-30"`), `test_provider_benchmark_ingest.py`'s
`_run_request` (`"2026-09-30"`), and `test_barrier_history.py::test_the_provider_loop_carries_both_work_kinds`
(`TODAY`, the date its fixture bars end on, so that run is exactly what it was).

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):** the claude.ai cloud session's clone,
`/home/user/trading-agents`, branch `claude/vibrant-pasteur-4x99vq` cut from `main` `a9fff56`;
**no `.env`**. Environment built with `uv sync --frozen` (`uv.lock` untouched). Every proof is a unit
test on `InMemoryGraphStore`.

**Result:** a `RunRequest`'s ingest serves its own as-of on both paths. `ingest_run_node` parses
`requested_at` once (exactly `YYYY-MM-DD`, not after today, else `ValueError` before any fetch),
checks the lookback against the sessions up to it, and passes it to `ingest_once` /
`ingest_chunked`, which build the window with one helper, `_run_window`. The regime, the stored
`window_end`s and the news and earnings anchors follow because they key on `window.end`. An ingest
with no run (`as_of=None`) still calls `_today_window`.

**Files changed:** `contracts/provider.py` (`RUN_REQUEST_REQUESTED_AT_PROP = "requested_at"`);
`orchestration/start.py` (writes under it); `agents/provider/poll.py`, `ingest.py`,
`ingest_chunked.py`; new `agents/provider/tests/as_of_helpers.py`, `test_run_as_of_window.py`,
`test_run_as_of_refusals.py`, `orchestration/tests/test_start_as_of.py`; the as-of input in
`test_provider_poll.py`, `test_provider_benchmark_ingest.py`, `test_barrier_history.py`;
`agents/provider/laws/laws.md` (v1.7), `test-plan.md`; `docs/laws/ledger.md`, `docs/laws/INDEX.md`,
`docs/laws/drift-register.md` (DRIFT-095); `docs/design-log.md` (DL-256); this file and its
`docs/sprints/README.md` row.

**Design decisions:** [DL-256](../design-log.md), next free on `main` at `a9fff56` (DL-255 was the
last). D1: an absent or unparseable as-of is refused with `ValueError` before any fetch (rejected:
fall back to today; fall back to the node's creation time; fault and skip). D2: only the exact
`YYYY-MM-DD` string parses, by round trip (`date.fromisoformat(s).isoformat() == s`); a datetime,
the compact and ISO-week forms, an unpadded date and a non-string are refused (rejected: take a
datetime's date, because its zone decides the day; accept whatever `fromisoformat` takes). D3: an
`as_of: date | None = None` parameter on `ingest_once` and `ingest_chunked`, one window helper
`_run_window` for both paths, `_today_window` kept (rejected: build the `Window` in `poll.py` and pass
it down, two copies of one fact; give `_today_window` an as-of, a name that lies). D4: an as-of later
than the UTC date the provider reaches it on is refused (rejected: serve up to today, the defect's
shape; serve the future window, a `window_end` for a session not yet closed).

**Proof — the red run first:** the three tests on unfixed provider code (the contract constant was
already added so the file imported; it changes no behaviour), 2026-10-01 UTC:

```text
E   assert [Window(start...2026, 10, 1))] == [Window(start...2026, 9, 30))]
E     At index 0 diff: Window(start=datetime.date(2025, 10, 1), end=datetime.date(2026, 10, 1)) != Window(start=datetime.date(2025, 9, 30), end=datetime.date(2026, 9, 30))
E   assert [datetime.date(2026, 10, 1)] == [datetime.date(2026, 9, 30)]
E     At index 0 diff: datetime.date(2026, 10, 1) != datetime.date(2026, 9, 30)
E   assert [Window(start...2026, 10, 1))] == [Window(start...2026, 9, 30))]
E     At index 0 diff: Window(start=datetime.date(2025, 10, 1), end=datetime.date(2026, 10, 1)) != Window(start=datetime.date(2025, 9, 30), end=datetime.date(2026, 9, 30))
FAILED agents/provider/tests/test_run_as_of_window.py::test_a_runs_market_window_ends_on_its_as_of
FAILED agents/provider/tests/test_run_as_of_window.py::test_the_regime_is_read_as_of_the_runs_as_of
FAILED agents/provider/tests/test_run_as_of_window.py::test_the_chunked_path_serves_the_same_as_of
3 failed in 0.54s
```

In the same red run of all 18: B4, both B6 tests, all nine B7 cases and B9 failed too (16 failed);
B5 and B8 passed, as they must (the scheduled and standalone paths do not move).

**Proof — the green run:**

```text
agents/provider/tests/test_run_as_of_window.py::test_a_runs_market_window_ends_on_its_as_of PASSED
agents/provider/tests/test_run_as_of_window.py::test_the_regime_is_read_as_of_the_runs_as_of PASSED
agents/provider/tests/test_run_as_of_window.py::test_the_chunked_path_serves_the_same_as_of PASSED
agents/provider/tests/test_run_as_of_window.py::test_news_and_earnings_are_anchored_on_the_as_of PASSED
agents/provider/tests/test_run_as_of_window.py::test_a_run_whose_as_of_is_today_is_unchanged PASSED
agents/provider/tests/test_run_as_of_window.py::test_an_ingest_with_no_run_keeps_todays_window PASSED
agents/provider/tests/test_run_as_of_refusals.py::test_the_coverage_check_counts_sessions_up_to_the_as_of PASSED
agents/provider/tests/test_run_as_of_refusals.py::test_a_lookback_short_of_the_as_ofs_sessions_is_refused PASSED
agents/provider/tests/test_run_as_of_refusals.py::test_a_request_with_no_usable_as_of_is_refused_before_any_fetch[absent] PASSED
agents/provider/tests/test_run_as_of_refusals.py::test_a_request_with_no_usable_as_of_is_refused_before_any_fetch[empty] PASSED
agents/provider/tests/test_run_as_of_refusals.py::test_a_request_with_no_usable_as_of_is_refused_before_any_fetch[not-a-date] PASSED
agents/provider/tests/test_run_as_of_refusals.py::test_a_request_with_no_usable_as_of_is_refused_before_any_fetch[a-full-datetime] PASSED
agents/provider/tests/test_run_as_of_refusals.py::test_a_request_with_no_usable_as_of_is_refused_before_any_fetch[compact-iso] PASSED
agents/provider/tests/test_run_as_of_refusals.py::test_a_request_with_no_usable_as_of_is_refused_before_any_fetch[iso-week] PASSED
agents/provider/tests/test_run_as_of_refusals.py::test_a_request_with_no_usable_as_of_is_refused_before_any_fetch[unpadded] PASSED
agents/provider/tests/test_run_as_of_refusals.py::test_a_request_with_no_usable_as_of_is_refused_before_any_fetch[not-a-string] PASSED
agents/provider/tests/test_run_as_of_refusals.py::test_a_request_with_no_usable_as_of_is_refused_before_any_fetch[after-today] PASSED
orchestration/tests/test_start_as_of.py::test_the_provider_serves_the_as_of_the_dispatcher_wrote PASSED
============================== 18 passed in 0.45s ==============================
```

**The reproduction after the fix** (the spec's script, unchanged, run from the repo root):

```text
today (UTC)             : 2026-10-01
run's as-of             : 2026-09-30
MarketData.window_end   : 2026-09-30
RegimeContext.window_end: 2026-09-30
regime as_of            : 2026-09-30
```

On `main` `a9fff56` the same script printed `2026-10-01` on the last three lines (re-run in this
session before any change; matches the spec).

**Guards planted:** each planted alone, its test run, the file restored and checked byte-identical by
SHA-256.

1. *The clock again in the single path* — `ingest.py`, `window = _run_window(lookback_days, as_of)`
   → `window = _today_window(lookback_days)`. B1 red:

   ```text
   E   assert [Window(start...2026, 10, 1))] == [Window(start...2026, 9, 30))]
   E     At index 0 diff: Window(start=datetime.date(2025, 10, 1), end=datetime.date(2026, 10, 1)) != Window(start=datetime.date(2025, 9, 30), end=datetime.date(2026, 9, 30))
   1 failed in 0.36s
   ```

   Restored: identical.
2. *The clock in the chunked path* — `ingest_chunked.py`, `_run_window(lookback_days, as_of)` →
   `_run_window(lookback_days, None)` (the today branch). B3 red:

   ```text
   E   assert [Window(start...2026, 10, 1))] == [Window(start...2026, 9, 30))]
   E     At index 0 diff: Window(start=datetime.date(2025, 10, 1), end=datetime.date(2026, 10, 1)) != Window(start=datetime.date(2025, 9, 30), end=datetime.date(2026, 9, 30))
   1 failed in 0.39s
   ```

   Restored: identical.
3. *The regime read as of today* — `ingest.py`, `RegimeRequest(as_of=window.end)` →
   `RegimeRequest(as_of=datetime.now(tz=UTC).date())`. B2 red:

   ```text
   E   assert [datetime.date(2026, 10, 1)] == [datetime.date(2026, 9, 30)]
   E     At index 0 diff: datetime.date(2026, 10, 1) != datetime.date(2026, 9, 30)
   1 failed in 0.38s
   ```

   Restored: identical.

**Module line counts** (all < 200; ⚠ = over the 150 warning):

| File | Before | After |
| --- | --- | --- |
| `contracts/provider.py` | 174 ⚠ | 176 ⚠ |
| `orchestration/start.py` | 100 | 101 |
| `agents/provider/poll.py` | 145 | 167 ⚠ |
| `agents/provider/ingest.py` | 179 ⚠ | 191 ⚠ |
| `agents/provider/ingest_chunked.py` | 159 ⚠ | 162 ⚠ |
| `agents/provider/tests/as_of_helpers.py` | new | 135 |
| `agents/provider/tests/test_run_as_of_window.py` | new | 103 |
| `agents/provider/tests/test_run_as_of_refusals.py` | new | 78 |
| `orchestration/tests/test_start_as_of.py` | new | 37 |
| `agents/provider/tests/test_provider_poll.py` | 94 | 97 |
| `agents/provider/tests/test_provider_benchmark_ingest.py` | 159 ⚠ | 161 ⚠ |
| `agents/provider/tests/test_barrier_history.py` | 129 | 130 |

`poll.py` crosses the 150 warning for the first time. `test_ingest.py` (175) and
`test_ingest_chunked.py` (198) are untouched.

**`make ci`:** `make ci > scratchpad/ci.txt 2>&1 ; echo $?` → **exit 0**, in the tree above (no
`.env`). All 15 steps of the `ci:` target ran: ruff, format (1,515 files), mypy, import-linter (5
kept, 0 broken), module size (warnings only), module header, law coverage (provider 22 / 67), PARAM
sync, sprint status, markdown links, version scheme, pytest **3,793 passed, 8 skipped**, coverage
**100.00 %** (19,929 statements, 0 missed), dependency audit ("No unaccepted vulnerabilities; 1
accepted advisory re-checked"), detect-secrets **Passed**, untracked secrets **Passed** (4 new files
scanned).

**`pyproject.toml` and `uv.lock`:** **untouched**, both. The version still reads `0.120.02`; the
PATCH bump and the `uv lock` it needs are the planner's (this session cannot reach
`download.pytorch.org`). The environment was built with `uv sync --frozen`, which does not write the
lock.

**Owed to the planner:** `uv lock` with the PATCH bump (next available at merge); `make gate-ran` from
the proving worktree (check the printed SHA against `git rev-parse HEAD`); Windows `make ci`; **F1**
(the branch's provider on `main`'s live sources, ingest for as-of 2026-09-30, compared with
`market-data:sched-2026-09-30`: `window_end` 2026-09-30, 203 bars a name, same first and last bar
dates, same closes); the merge; the image-only retag. Re-check that DL-256 and DRIFT-095 are still
free at merge.

**Not met / verified failing:** nothing in the builder's list. Not attempted, by design: F1, the gate
and any live proof (no `.env`, no `gh`); no run result read through the GitHub connector is claimed
as `GATE PROVEN`.

---

## Return notes

- **Branch name.** The session forces `claude/vibrant-pasteur-4x99vq`; the spec's
  `sprint-249-a-runs-market-window-ends-on-its-as-of` was not created. Cut from `main` `a9fff56`.
- **What a past-as-of run now refuses that it used to accept.** A `RunRequest` without a usable
  `requested_at` raises `ValueError` in the provider's loop, as a bad lookback already did. All 81 live
  requests carry one (DL-255), and `orchestration/resume.py` copies its source's, so no live request is
  newly refused. A `--as-of` override typed as a datetime or a future date now fails at ingest instead
  of running for the wrong day.
- **A run for today is unchanged** (B5): its window is `_today_window(lookback)` exactly, and the
  coverage check counts to the same date as before. No existing expected value moved.
- **Left as it was, on purpose (spec, Out of scope):** the barrier history window still follows the
  clock, so a past-as-of run's `BarrierHistory` (if its run is current) still ends today while its
  `MarketData` ends on the as-of. Fundamentals and sectors are still the latest values. The eight
  wall-clock reads in five other agents stay in work-queue 103, part two.
- **DRIFT-082** (OPEN, older): `PROV-TRG-01` still reads "only a request event"; `PROV-TRG-05` adds a
  second clause that names a graph-pulled `RunRequest`, which makes the widening the planner already
  owes a little more pressing. Not touched.
- **Partial proofs not counted.** B7 proves a slice of `PROV-TRG-03` and B2 a slice of `PROV-IN-02`;
  both rows stay ⬜ (conventions §7a).

### Planner, at merge (2026-10-01)

- **Scope held.** The diff touches the provider, one constant in `contracts/provider.py`, `orchestration/start.py`, the provider's law book and docs; no `surfaces/`, `orchestration/resume.py`, `barrier_history.py` or other agent.
- **Proven.** Windows `make ci` exit 0 (3,793 passed, 8 skipped, 100.00 %); `GATE PROVEN` for `f3956bac` from the proving worktree, printed SHA equal to `HEAD`; fast-forwarded, so the merged SHA is the gated SHA. The reproduction above re-run by the planner: 2026-09-30 on the branch, 2026-10-01 on `main` `a9fff56f`.
- **F1 PASS** ([functionality-checks](../laws/functionality-checks.md)). The branch's provider on the live sources over an in-memory graph, a request for as-of 2026-09-30 ingested at 05:08 UTC on 2026-10-01: `window_end` 2026-09-30 on `MarketData` and `RegimeContext`, 203 bars a name (2025-12-09 → 2026-09-30), 10 of 10 names identical in dates and closes to `market-data:sched-2026-09-30`. The same with `ingest_chunk_size=5`, the chunked path the fleet's 99 names take. On `main` the same script read 202 bars and 0 of 10.
- **The lock diff is 52 lines, not the version line alone.** Dependabot's uv (`5b44d973`) had dropped dependency markers and ten `greenlet` wheel entries that the planner's uv 0.8.14 writes back. The package set is identical (180 = 180); only `trading-agents` moves, `0.120.2` → `0.120.3`. The same lines will move again whenever the other uv writes the lock.
- **CodeQL: 131 open on the branch against 130 on the last merged branch; 0 error-level on both.** The one added is alert 279, `py/cyclic-import` (note), `ingest_chunked.py:20`: the `ingest` ↔ `ingest_chunked` pairing that alert 61 dismissed on 2026-07-04 as intended (the import in `ingest.py` is inside the function). This sprint changed one name in that import statement, so CodeQL filed it again. Left open, beside the ten `py/cyclic-import` notes already open on `main`; the gate fails on error-level only. `ingest.py` is at 191 lines, so its next change forces a split, and that split is where the pairing can go.
- **Decisions 2 and 4 (DL-256) accepted.** Refusing a datetime and a future as-of is stricter than the spec asked. A refusal is loud: `kernel/work_loop.py` records the failure and backs off, as it does for a bad lookback. One consequence for a planner-fired test run: the as-of is a **UTC** date, so a run placed from Melbourne before 10:00 AEST (11:00 AEDT) with the local date is refused as after today.
- **The three test helpers that gained an as-of** carry an input only; no expected value moved. `test_barrier_history.py`'s `TODAY` is `datetime.now(tz=UTC).date()`, so that run is the run it was.
- **Left as the spec ruled.** The barrier history window still follows the clock, so a past-as-of run that is still current writes a `BarrierHistory` ending today beside a `MarketData` ending on its as-of. With the eight reads in five other agents it is part two of work-queue 103. DRIFT-082 stays open.
- **Deployed.** deployed `s249`** 2026-10-01 17:01–17:08 AEST (operator: *"you can retag"*): image-only, the three injected packs byte-identical between `v0.120.02` and `v0.120.03`; build `36827807053` **15 / 15** from `f3956bac`; **16 / 16** apps and `dispatcher-cron` on `s249`, all `Succeeded`, one active revision each, latest = ready; CPU, memory, env counts and the full scale blocks identical to the pre-retag snapshot; `DeployRecord` written; rollback `s248`.
