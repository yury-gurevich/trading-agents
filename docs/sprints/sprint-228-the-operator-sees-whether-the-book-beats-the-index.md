<!-- Agent: planning | Role: sprint handover -->
# Sprint 228 — the operator sees whether the book beats the index without asking

**Phase:** Etalon-first continuous improvement (DL-19) · next leg P16, item **E16.2**
**Branch:** `sprint-228-the-operator-sees-whether-the-book-beats-the-index`
**Status:** MERGED `d07be9e8` · tag `v0.112.00` · no deploy (the dashboard runs locally); live check done 2026-09-25
**Version:** *next available MINOR at merge*
**Effort:** S
**Decisions:** [DL-220](../design-log.md) (Telegram moves to E19.1; the tile's colour rule) · work-queue item **81** · reads what [S226](sprint-226-a-run-says-whether-the-book-beat-the-index.md) / `RPT-OUT-07` writes · DL-47 (glance-first dashboard)

> **Why this bump kind.** The dashboard and the chat gain an answer they did not have. That is a
> MINOR. No agent, contract or image changes.

**Builder:** Codex. Every behaviour is pinned by a row in the test plan.
**If a number you measure differs from one written here, stop and report. Do not adjust and continue.**

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: reporter **`RPT-OUT-07`** (what `performance_metrics` means),
**`RPT-IDM-03`** (its as-of date), **`RPT-FAIL-04`** (a failed calculation still writes a Snapshot),
and **`RPT-SEC-02`** (never logs P&L to external systems). `surfaces/` has **no law book**; its
binding rules are DL-47's dashboard requirements in [`design-log.md`](../design-log.md) (search
`## DL-47`), above all **req 5** (the run selector scopes everything) and **req 14** (no S-numbers or DL
chips in the UI).
🩹 **[S229](sprint-229-every-component-that-decides-answers-to-a-law-book.md) is ranked ahead of this
sprint and gives `surfaces/` a law book (`surfaces/laws/laws.md`, prefix `SRF`).** If it has merged when
you build, that book binds: read it first, and cite its clauses in your test docstrings.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's expected answer is No.** The surfaces read the `Snapshot` the reporter already writes.
No `contracts/` file changes, and no agent gains a guarantee. The reporter's law book is read, not
amended. If your design needs a `contracts/` edit or a reporter change, **stop and report**: that
means the spec is wrong, not that the law cycle is due.

`RPT-SEC-02` stays satisfied because both new readers are **local and deterministic**: the dashboard
runs on the operator's machine, and the new chat tool answers from the graph without calling a model.
🪤 **Do not route the chat answer through the operator agent or any LLM.** That would send P&L to a
vendor, and whether that is allowed is exactly the question this sprint defers to E19.1 (see *Road
not taken*).

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `surfaces/queries/performance.py` (new) | `agents/reporter/laws/laws.md` + `test-plan.md` | `RPT-OUT-07` names the metric keys and their meaning; `RPT-IDM-03` the as-of date; `RPT-FAIL-04` the degraded shape you must read without crashing |
| `surfaces/dashboard/projections_vitals.py`, a new `surfaces/dashboard/projections_performance.py` | DL-47 in `docs/design-log.md` | req 5: the tile follows the selected run; req 14: plain words, no internal IDs |
| `surfaces/mcp_tools.py`, `surfaces/mcp_server.py`, `surfaces/dashboard/chat.py`, `static/index.html` | DL-47; `RPT-SEC-02` | the chat answer is a graph read, never a model call |
| `surfaces/dashboard/settings.py` | `docs/laws/conventions.md` (no magic numbers) | the colour threshold is a named, bounded setting with a `why` |

⚠️ **One invariant: the surfaces print the reporter's numbers and compute none of their own.** Rounding
and choosing a colour are fine. Recomputing a return, re-deriving exposure or reading
`BrokerPositionSnapshot` directly is not: that is the "two definitions of return" failure the next-leg
plan forbids (§5, *One metric definition*; DL-208 is the precedent). If you find you need a number the
Snapshot does not carry, stop and report.

---

## Goal

When the operator opens the dashboard, one vital on the status line says whether the book is ahead of
or behind the market, in green, amber or red, for the selected run. Its detail shows since-inception
and rolling-20-session excess return, the book's return, SPY's return, SPY at the book's exposure,
average exposure, max drawdown, sessions counted and equity. The operator chat answers *"are we beating
the market?"* with the same numbers, from the same Snapshot, with no model call. A run whose Snapshot
has no performance group (every run before S226 deployed) reads **unavailable**, never zero.

## Why (context)

S226 (E16.1) made the reporter compute the scoreboard. Right now the only place a human can see it
is the tail of a headline string, **truncated at 80 characters** by `trace_run.py`. The next-leg plan's
P16 exit is *"the dashboard shows portfolio return, SPY return and exposure-matched SPY … the operator
chat can answer 'are we beating the market?' from graph facts only"*. This sprint is that exit.

### Measured, 2026-09-25 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| The first production Snapshots carrying the performance group | `manual-2026-09-24` and `sched-2026-09-24` | *[measured 2026-09-25]* `walk_chain(graph, run_id)["Snapshot"]` on the live Postgres spine, `.env` loaded |
| Where the numbers live | `Snapshot.props["metrics"]["performance"]`, **12 keys**: `portfolio_return_pct`, `benchmark_return_pct`, `exposure_matched_return_pct`, `excess_return_pct`, `average_exposure_pct`, `max_drawdown_pct`, `rolling_portfolio_return_pct`, `rolling_exposure_matched_return_pct`, `rolling_excess_return_pct`, `performance_sessions`, `performance_gap_sessions`, `equity_cents` | *[measured 2026-09-25]* same read; the keys match `agents/reporter/domain/performance.py:51-63` |
| `sched-2026-09-24` values | excess **−0.2787** pts, portfolio **−0.4523 %**, SPY **−0.9094 %**, exposure-matched **−0.1737 %**, exposure **21.19 %**, drawdown **−0.9392 %**, rolling-20 excess **−0.5892** pts, sessions **32**, gaps **0**, equity **10,200,072** cents | *[measured 2026-09-25]* same read. `manual-2026-09-24` is identical: both have the UTC as-of date 2026-09-24 (`RPT-IDM-03`) |
| Headline text | `… vs SPY: -0.28 pts over 32 sessions at 21% invested` | *[measured 2026-09-25]* `Snapshot.props["headline_summary"]` |
| 🪤 **The Snapshot key is NOT `snapshot:<run_id>`** | `snapshot:pm-run-ee4ba3be…` for `sched-2026-09-24`; `graph.get_node("Snapshot", "snapshot:sched-2026-09-24")` returns **None** | *[measured 2026-09-25]* live spine. The reporter keys by the `PMRun` key. `surfaces/queries/runs.py:96` and `surfaces/cli_commands.py:55` use the `run_id` form and belong to the older message-run listing: **do not copy them** |
| Surfaces may import orchestration | yes: `surfaces/context.py:27`, `surfaces/dashboard/hold_answer_panel.py:12` | *[measured 2026-09-25]* `.importlinter` forbids agents → surfaces/orchestration, not surfaces → orchestration |
| No fleet image ships `surfaces/` | 0 Dockerfiles copy it | *[measured 2026-09-25]* `grep -rn "COPY surfaces"` over every Dockerfile. The dashboard runs locally |
| Telegram sends only two notices | `send_hold_notice`, `send_degraded_notice` in `orchestration/scheduled_dispatch_human.py`; **no nightly per-run notice exists** | *[measured 2026-09-25]* read of the module. This is why the Telegram line moves to E19.1 |
| Module sizes at spec time | `projections_vitals.py` **136**, `settings.py` **166**, `mcp_tools.py` **148**, `mcp_server.py` **135**, `chat.py` **138**, `static/infra.js` **188** (JS is not size-gated, but keep it under 200 by the same rule) | *[measured 2026-09-25]* `wc -l` on `main` @ `44dc1f66` |
| The colour threshold | green at ≥ 0, red at ≤ −1.00 pts, amber between | *[ASSUMED — a display choice, recorded as DL-220]* There is no evidence base for a "bad" excess over six weeks; the red line is where the gap is no longer rounding noise at 21 % exposure. It is a setting so it can move without a code change |

---

## Scope — and what is deliberately NOT here

1. **A read-side query, failing test first.** `surfaces/queries/performance.py` exposes
   `run_performance(graph, run_id) -> PerformanceView`. It finds the Snapshot **through the run
   chain** (`orchestration.batch_chain.walk_chain(graph, run_id).get("Snapshot")`), reads
   `metrics["performance"]`, and returns a frozen view with `status` of `measured`,
   `no_sessions` (`performance_sessions == 0`, the `RPT-FAIL-04` / empty-metrics case) or
   `unavailable` (no Snapshot, no performance group, or a key missing). It never raises on a missing
   or partial group; it never returns zeros for `unavailable`.
2. **A dashboard vital.** `vitals_projection` gains a `performance` entry for the **selected** run
   (DL-47 req 5), built in a new `surfaces/dashboard/projections_performance.py` so the vitals module
   does not grow past the warning band. It carries the rounded numbers, a `tone` of `good` / `warn` /
   `crit` / `idle` and one plain-words line, e.g. *"vs SPY −0.28 pts · 32 sessions · 21 % invested"*.
   The render goes in a **new** `static/performance.js` (included from `index.html`), not in
   `infra.js`. Clicking or hovering the vital shows the detail listed in *Goal*. Same visual language as
   the existing vitals.
3. **A colour threshold as a setting.** `DashboardSettings` gains one bounded field for the red line
   (default **1.0** pts, bounds 0.1–10.0, a `why` naming DL-220). Green when excess ≥ 0; red when excess
   ≤ −threshold; amber between; `idle` (grey) for `no_sessions` and `unavailable`. If `settings.py`
   would cross 200 lines, split it rather than grow it.
4. **A chat answer.** A `performance` tool in `surfaces/mcp_tools.py` (plus its declaration in
   `mcp_server.py`, beside `incidents`), a quick-ask button *"vs the market"* in `index.html`, and its
   mapping in `chat.py`'s `_QUICK_TOOLS`. It takes an optional `run_id` (default: the latest run the
   dashboard would select) and returns the numbers plus one summary sentence:
   *"Behind the market by 0.28 pts over 32 sessions: the book returned −0.45 %, SPY −0.91 %, and SPY
   at the book's 21 % exposure −0.17 %. Last 20 sessions: behind by 0.59 pts."* Say *ahead of*,
   *behind* or *level with*. **No model call on this path.**
5. **Design decisions** recorded in `docs/design-log.md` as **DL-220** before implementing (see below).

### Out of scope (do NOT build this sprint)

- **Any Telegram message.** There is no nightly notice to add a line to; the per-session brief is
  E19.1, and it carries the scoreboard line **and** the `RPT-SEC-02` decision (DL-220).
- **Any change to the reporter, its law book or `contracts/`.** The numbers are right as they are;
  S226's planner review reproduced them to 0.0001 pts.
- **A chart or an equity curve.** One vital, one chat answer. Charts arrive with P17's replay.
- **Fixing `surfaces/queries/runs.py:96` / `cli_commands.py:55`.** They serve the message-run listing,
  a separate model; changing them widens this sprint. Note them in *Return notes* if you think they
  are dead.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

- **Add the Telegram line now, by building a nightly notice.** Rejected: that notice *is* E19.1's
  daily brief, with its own notification budget and its own `RPT-SEC-02` question. Building half of it
  here would pre-empt both.
- **Route the chat answer through the operator agent (LLM) for nicer wording.** Rejected: it sends P&L
  to a vendor (`RPT-SEC-02`), costs money per question, and adds a failure mode to a question that has
  one right answer already in the graph.
- **Recompute the scoreboard in the dashboard from `BrokerPositionSnapshot`.** Rejected: two
  definitions of return, the DL-208 failure on the number that matters most.
- **Colour on the rolling-20 excess instead of since-inception.** Rejected for the tone, because
  since-inception is the headline number the reporter already prints. Rolling-20 is shown in the detail.
- **A fixed red line in code.** Rejected: no magic numbers, and the threshold is a judgement that
  should move without a release.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` as DL-220 with their rejected alternatives BEFORE implementing
(LAW-06).** The planner has already written the Telegram half of DL-220; extend that entry, do not start
a new one.

1. **Where "latest run" comes from for the chat tool** — reuse the dashboard's own selection
   (`_latest_run_id` in `projections_vitals.py` or `route_selection.py`), not a second definition.
2. **What `unavailable` looks like on the vital** — grey, the words *"no scoreboard for this run"*,
   and nothing that reads as zero.
3. **Rounding** — two decimals for points and percent, whole percent for exposure, matching the
   reporter's headline (`snapshot_result.py`), including its `-0.00 → 0.00` rule.

🪤 **Take DL-220 as written; re-check at merge.** The log has historic duplicates, and a branch cut
before another DL lands will collide even when the number was free at branch time.

---

## Blast radius — measured 2026-09-25

| What | Detail |
| --- | --- |
| Files changed | new `surfaces/queries/performance.py`, new `surfaces/dashboard/projections_performance.py`, new `surfaces/dashboard/static/performance.js`; edited `projections_vitals.py` (136), `settings.py` (166), `mcp_tools.py` (148), `mcp_server.py` (135), `chat.py` (138), `static/index.html`; tests under `surfaces/tests/` |
| Agents affected | **none** |
| Contract change? | **no** — the law cycle is not owed |
| Graph vocabulary change? | **no** — read-only |
| New env keys / tunables | one `DashboardSettings` field (local dashboard only; no fleet env) |
| Deploy implication | **none** — no image ships `surfaces/`. After merge, restart the local dashboard on `main` |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Extend DL-220** in `docs/design-log.md` with decisions 1–3.
3. **Plant the failing tests first** (A1–A3) and watch them fail. Paste the red output.
4. **Implement** scope items 1–4.
5. **No law cycle** unless your answer to the law-cycle question changed. If it did, stop and report.
6. **Prove the guards can fail (DL-70)** — for A3 and A5, break the implementation (return `0.0`
   for a missing group; look the Snapshot up by `snapshot:<run_id>`), watch each go red, restore.
7. **`make ci` green** — every step of the `ci:` target, **redirected to a file, never piped**.
8. **Render it.** Start the dashboard from your worktree against an in-memory graph seeded with the
   A1 fixture and take a headless screenshot of the vitals line and the chat answer. The worktree has
   no `.env`, so a live-spine render is the planner's job after merge. **Say which you did.**
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Fixture: a `RunRequest` → … → `PMRun` → `ExecutionRun` → `MonitorRun` → `Snapshot` chain in an
in-memory graph, with the Snapshot keyed **`snapshot:pm-run-<hex>`** and `metrics["performance"]`
set to the `sched-2026-09-24` values in the Measured table.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 `run_performance` reads the reporter's numbers | the fixture above | `status == "measured"`; every one of the 12 values equals the Snapshot's, unchanged (`RPT-OUT-07`) |
| A2 | the vital for a behind-by-0.28 run is amber | A1 fixture, default threshold | `tone == "warn"`; line reads `vs SPY −0.28 pts · 32 sessions · 21 % invested` |
| A3 | 🪤 a run with no performance group reads unavailable, not zero | Snapshot with only `portfolio`/`signal`/`regime` groups (a pre-S226 run) | `status == "unavailable"`, `tone == "idle"`, no numeric fields rendered (`RPT-FAIL-04` read side) |
| A4 | `performance_sessions == 0` reads *no sessions* | the reporter's empty-metrics dict | `status == "no_sessions"`, `tone == "idle"` |
| A5 | 🪤 the Snapshot is found by the chain, not by `snapshot:<run_id>` | A1 fixture, plus **no** node at `snapshot:<run_id>` | A1 still passes; a lookup by `snapshot:<run_id>` would fail this test |
| A6 | tone boundaries | excess `0.00`, `-0.00`, `+0.01`, `-0.99`, `-1.00`, `-1.01` | `good`, `good`, `good`, `warn`, `crit`, `crit` at the default threshold; moving the setting to 0.5 moves `-0.99` to `crit` |
| A7 | the vital follows the selected run (DL-47 req 5) | two runs with different excess | `vitals_projection(..., run_id=<older>)` reports the older run's numbers |
| A8 | 🎯 the chat answers from the graph with no model call | A1 fixture; a context whose operator/LLM port raises if called | `dispatch_tool(ctx, "performance", {})` returns the numbers and the *Behind the market by 0.28 pts…* sentence; the LLM port was never called |
| A9 | the quick-ask button is wired | `chat.py`'s `_QUICK_TOOLS`, `index.html` | *"vs the market"* maps to `performance`, and the button exists (DL-47: never show an unwired control) |
| A10 | unknown `run_id` in the chat tool | a run id with no chain | a plain-words `unavailable` answer, not an exception |

---

## Success factors

- [ ] The dashboard's vitals line shows a *vs SPY* vital for the selected run, coloured by the
      DL-220 rule, with the full detail on demand.
- [ ] The chat's *"vs the market"* answers from the Snapshot with the numbers and one sentence, with no
      model call (A8).
- [ ] A pre-S226 run reads **unavailable**, never zero (A3).
- [ ] No change to `agents/`, `contracts/`, any law book, any Dockerfile or `infra/`.
- [ ] DL-220 extended with decisions 1–3 and their rejected alternatives.
- [ ] Law-cycle question answered No, with the reason.
- [ ] A3 and A5 guards planted, watched to fail, restored — stated per guard.
- [ ] Every touched Python module < 200 lines; `static/infra.js` not grown.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **`snapshot:<run_id>` looks right and returns None on every graph-pull run.** Measured on the live
spine. Two existing surfaces use it; they are not your model. Walk the chain.
🪤 **A missing number rendered as `0.00` reads as "level with the market".** That is the most
believable lie this vital can tell. `unavailable` must look different from zero.
🪤 **`performance_metrics` on the `RunSnapshot` contract is not what is stored.** The graph node
carries `metrics["performance"]`; the contract field is the reply payload. Read the node.
🪤 **"Latest run" defined twice.** If the chat tool picks its own latest run, the button and the
vital can disagree on the same screen, which is DL-207's contradiction again.
🪤 **Your worktree has no `.env`.** Any "it works on live data" claim from the worktree is vacuous;
prove with the fixture and say so.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `settings.py` **166**, `mcp_tools.py` **148**, `chat.py` **138**,
  `projections_vitals.py` **136**, `mcp_server.py` **135**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — the red line is a bounded setting with a `why`.
- Faults, not silent failure — an unreadable Snapshot is `unavailable` with a reason, not an exception
  and not a zero.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving**, and check the printed
   SHA against `git rev-parse HEAD`.
2. Merge to `main` locally and push. 🪤 Not from the branch's own worktree.
3. **Post-merge CodeQL** on `main`.
4. **No deploy.** Restart the local dashboard on `main`, then the planner's functionality check: the
   vital and the chat answer on the live spine for `sched-2026-09-24` must read **−0.28 pts, 32
   sessions, 21 %**, amber; and the Snapshot's `equity_cents` must equal that run's
   `BrokerPositionSnapshot` equity to the cent (the P16 exit's reconciliation clause). Record it in
   `docs/laws/functionality-checks.md`.
   🟩 **Done 2026-09-25 ~19:30 AEST** on `main` = `d07be9e8` with `.env`, read-only against the live
   spine. `GATE PROVEN` for `d07be9e821ab72bc2870fd4ae3a3a7ebc00ed9da` (CI, CodeQL, Security Findings,
   attempt 1) from the sprint worktree, then a fast-forward, so the merged SHA is the proven one.
   `sched-2026-09-24` → amber, `vs SPY −0.28 pts · 32 sessions · 21 % invested`, and the chat tool's
   sentence as in A8; `sched-2026-09-23` → *no scoreboard for this run*. 🪤 **The reconciliation clause
   holds for the day, not for the run:** `equity_cents` **10,200,072** equals the *earliest* fresh
   `BrokerPositionSnapshot` of 2026-09-24, `manual-2026-09-24`'s intraday one (14:15 UTC); the
   scheduled run's own post-close snapshot read **10,196,728**. The reporter keeps one point per UTC
   day, the earliest, so on a two-run day the daily series carries intraday equity against SPY's close.
   A reporter question, filed as work-queue **88**, not a surfaces defect.

---

## Handover — paste this to Codex

```text
Sprint 228 — the operator sees whether the book beats the index without asking.
Spec: docs/sprints/sprint-228-the-operator-sees-whether-the-book-beats-the-index.md (read all of it).

Branch: sprint-228-the-operator-sees-whether-the-book-beats-the-index, in its own worktree. Never main.

MUST RULE before any code: read agents/reporter/laws/laws.md + test-plan.md (RPT-OUT-07, RPT-IDM-03,
RPT-FAIL-04, RPT-SEC-02), docs/laws/conventions.md, docs/laws/drift-register.md, and DL-47 in
docs/design-log.md (req 5: the run selector scopes everything; req 14: plain words in the UI). Fill
the Law reading record in the spec BEFORE the first code change.

Law-cycle answer expected: NO. No contracts/ change, no agent change, no law edit. If you need one,
STOP and report.

Build (surfaces/ only):
1. surfaces/queries/performance.py: run_performance(graph, run_id) -> frozen view with status
   measured | no_sessions | unavailable. Find the Snapshot via
   orchestration.batch_chain.walk_chain(graph, run_id).get("Snapshot") and read
   node.props["metrics"]["performance"] (12 keys, listed in the spec).
2. A "performance" vital on the dashboard for the SELECTED run: new
   surfaces/dashboard/projections_performance.py, wired into vitals_projection; render in a NEW
   static/performance.js (do not grow infra.js, 188 lines).
3. DashboardSettings: one bounded red-line setting (default 1.0 pts, bounds 0.1–10.0, why cites
   DL-220). Tone: >= 0 good, <= -threshold crit, between warn, idle for no_sessions/unavailable.
4. Chat: a "performance" tool in mcp_tools.py + its mcp_server.py declaration, a "vs the market"
   quick button in index.html, its _QUICK_TOOLS mapping in chat.py. Deterministic text only.

Order: extend DL-220 in docs/design-log.md with the three decisions -> plant tests A1–A10 and paste
the red run -> implement -> break A3 and A5 on purpose, watch them fail, restore -> make ci redirected
to a file (never piped), exit 0, 100.00 % -> headless screenshot from the worktree on the fixture.

DO NOT:
- look the Snapshot up by "snapshot:<run_id>". It returns None on every graph-pull run (measured on
  the live spine; the real key is snapshot:pm-run-<hex>).
- render a missing number as 0.00. Unavailable must look different from "level with the market".
- recompute any return in surfaces. Print the reporter's numbers; round and colour only.
- call the operator agent or any LLM from the chat tool (RPT-SEC-02, cost).
- touch agents/, contracts/, any laws.md, any Dockerfile, infra/, or Telegram code.
- pin a version number: MINOR bump, next available at merge, uv.lock staged with it.
- claim live-data proof from the worktree. It has no .env.

Handback: fill Law reading record, Test plan results, Closeout evidence (red and green output, guards,
line counts, make ci file + exit code, make gate-ran from the worktree at the full SHA), Return notes.
Set Status: BUILT and change this sprint's README.md row to lead with BUILT in the same commit.
Anything not met: say "not done" or "verified failing". Never write a Result for work not done.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `surfaces/queries/performance*.py`, `projections_performance.py`, `performance_tool.py` | `agents/reporter/laws/laws.md` + `test-plan.md`; `surfaces/laws/laws.md` + `test-plan.md` | `RPT-OUT-07`, `RPT-IDM-03`, `RPT-FAIL-04`, `RPT-SEC-02`; `SRF-OUT-01`, `SRF-OUT-05`, `SRF-FAIL-02`, `SRF-TYP-01` | Yes: `RPT-FAIL-04` writes zero-session metrics, so zero sessions is its own `no_sessions` status that shows no number. |
| `mcp_tools.py`, `mcp_server.py`, `chat.py`, `index.html`, `performance.js` | `surfaces/laws/laws.md` | `SRF-TRG-02`, `SRF-IN-04`, `SRF-NEV-03`, `SRF-OUT-06`, `SRF-OUT-03` | **Yes: `SRF-TRG-02` fixes the catalogue at five tools**, so a sixth needs the book amended (below). |
| `settings.py` | `surfaces/laws/laws.md` `PARAM`; `docs/laws/conventions.md` | the `PARAM` table lists every `DashboardSettings` field (gate-enforced) | Yes: the threshold needs a `PARAM` row. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **No `contracts/`
change and no agent change, but yes, a law cycle on the surfaces book.** The spec expected "No"
because it predates S229, which locked `SRF-TRG-02` at five tools and made the `PARAM` table
gate-enforced for `DashboardSettings`. The book is amended to **v1.1**: `SRF-TRG-02` lists
`performance`, new clause **`SRF-OUT-07`** (the reporter's numbers only, unavailable never zero, no
model call), a `PARAM` row for `performance_behind_threshold_pts`, a changelog line, and the ledger and
INDEX at **28 / 35** (DL-220 decision 9).

**Contradictions found between a law and this spec:** `SRF-TRG-02` (five tools) against scope item 4
(a sixth). Resolved by amending the book, not by leaving the clause false.

**Laws found silent where a decision was needed:** the surfaces book said nothing about the scoreboard;
`SRF-OUT-07` fills it. `SRF-OUT-03` speaks of LLM chat answers; the deterministic quick asks (`status`,
`incidents`, now `performance`) were already outside it, and `SRF-OUT-07` states that this one makes no
model call.

**Clauses that were ⬜ and are now proven:** none were ⬜ among those relied on. New and proven:
`SRF-OUT-07`. `RPT-SEC-02` stays ⬜ in the reporter's plan: this sprint keeps it satisfied (A8 proves
no agent or model is reached), but it is the reporter's clause and E19.1's decision.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_run_performance_reads_the_reporters_numbers_unchanged` | `surfaces/tests/test_performance_scoreboard.py` | 🟩 (red first) | `RPT-OUT-07`, `SRF-OUT-07` |
| A2 | `test_a2_a_run_behind_by_028_is_amber_with_the_plain_line` | same | 🟩 | `SRF-OUT-07` |
| A3 | `test_a3_a_run_without_the_group_reads_unavailable_not_zero`; `test_a3_a_partial_group_and_a_missing_snapshot_read_unavailable` | same | 🟩 (guard planted) | `RPT-FAIL-04`, `SRF-OUT-07` |
| A4 | `test_a4_zero_sessions_reads_no_sessions` | same | 🟩 | `RPT-FAIL-04`, `SRF-OUT-07` |
| A5 | `test_a5_the_snapshot_is_found_by_the_chain_not_by_run_id` | same | 🟩 (guard planted) | `SRF-OUT-07` |
| A6 | `test_a6_tone_boundaries_at_the_default_red_line` (7 cases, incl. `-0.004`); `test_a6_moving_the_red_line_moves_the_tone` | same | 🟩 | `SRF-OUT-07` |
| A7 | `test_a7_the_vital_follows_the_selected_run` | same | 🟩 | `SRF-OUT-01`, `SRF-OUT-07` |
| A8 | `test_a8_the_chat_answers_from_the_graph_with_no_model_call`; `test_a8_ahead_and_level_read_in_plain_words` | `surfaces/tests/test_performance_chat.py` | 🟩 | `SRF-OUT-07`, `RPT-SEC-02` |
| A9 | `test_a9_the_quick_ask_is_wired_to_the_tool`; `test_a9_the_chat_quick_ask_answers_for_the_selected_run` | same | 🟩 | `SRF-OUT-06`, `SRF-OUT-07` |
| A10 | `test_a10_an_unknown_run_answers_unavailable_in_plain_words` | same | 🟩 | `SRF-FAIL-02`, `SRF-OUT-07` |

**Tests added beyond the plan:** `test_the_benchmark_name_comes_from_the_reporters_headline`
(DL-220 decision 7); `test_the_vital_route_serves_the_selected_run_and_404s_unknown_runs`
(`SRF-IN-01`); `surfaces/tests/test_performance_text.py` (level lead, no-sessions answer, gap
sessions, the `-0.00` rule). `test_mcp_server.py::test_error_paths_and_tool_catalog` now expects six
tools.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** the worktree
`../trading-agents-sprint-228-the-operator-sees-whether-the-book-beats-the-index`, **no `.env`**. Every
proof here is on fixtures; the live-spine check is the post-merge functionality check.

**Result:** the dashboard has a *vs SPY* vital for the selected run, coloured by the DL-220 rule, with
the nine numbers and the sentence on click; the chat's *vs the market* and the MCP `performance` tool
answer from the Snapshot with no agent or model call; a pre-scoreboard run reads *no scoreboard for
this run* with no number. **Rendered headless** (Edge) from the worktree on the A1 fixture: the vital
reads `vs SPY −0.28 pts · 32 sessions · 21 % invested`, amber; the chat answer reads the A8 sentence.
Not rendered on live data (no `.env` here).

**Files changed:** new `surfaces/queries/performance.py` (84), `surfaces/queries/performance_text.py`
(103), `surfaces/dashboard/projections_performance.py` (63), `surfaces/performance_tool.py` (39),
`surfaces/dashboard/static/performance.js` (52); edited `projections.py` (one `latest_run_id`),
`route_selection.py` and `projections_vitals.py` (use it; vitals carries `performance`), `app.py`
(`/api/runs/<run>/performance`), `settings.py`, `mcp_tools.py`, `mcp_server.py`, `chat.py`,
`index.html`, `app.css`; `surfaces/laws/{laws,test-plan}.md` v1.1; `docs/laws/{ledger,INDEX}.md`;
`docs/design-log.md` (DL-220); tests. **No change to `agents/`, `contracts/`, any Dockerfile or
`infra/`.** `static/infra.js` untouched (188).

**Design decisions:** recorded as [`DL-220`](../design-log.md) decisions 4–10: one `latest_run_id`
(the dashboard had two copies); unavailable carries no number; rounding and the tone on the displayed
value; the benchmark's name read from the reporter's headline; the vital on its own route and slot;
the surfaces book amended to v1.1; the recent-window clause names no length.

**Proof — the red run first:**

```text
surfaces\tests\test_performance_scoreboard.py:13: in <module>
    from surfaces.dashboard.projections_performance import (
E   ModuleNotFoundError: No module named 'surfaces.dashboard.projections_performance'
ERROR surfaces/tests/test_performance_scoreboard.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
```

**Proof — the green run:**

```text
uv run pytest surfaces/tests/test_performance_text.py surfaces/tests/test_performance_scoreboard.py surfaces/tests/test_performance_chat.py
26 passed
```

**Guards planted:** **A3**: a missing group returned as `measured` zeros gave `assert 'measured' ==
'unavailable'`, `1 failed`; restored. **A5**: the Snapshot looked up by `snapshot:<run_id>` made A1 and
A5 both fail with `assert 'unavailable' == 'measured'`; restored (`cmp` identical), 22 passed.

**Module line counts:** `app.py` 180, `settings.py` 176, `test_performance_scoreboard.py` 158,
`mcp_server.py` 151, `mcp_tools.py` 150, `test_performance_chat.py` 143, `chat.py` 141,
`projections.py` 137, `projections_vitals.py` 133 (was 136), `performance_text.py` 103; all < 200.

**`make ci`:** redirected to a file, **exit 0**: **3,209 passed, 6 skipped, 100.00 %**; law coverage
and PARAM sync pass on the v1.1 book; `No unaccepted vulnerabilities; 1 accepted advisory re-checked`;
detect-secrets tracked and untracked **Passed**. The first run was exit 2 (ruff: line lengths, and the
typographic minus in string literals, now `chr(0x2212)`), the second 99.96 % (five wording branches
untested, now pinned by `test_performance_text.py`).

**`make gate-ran`:** run from this worktree after the push, on the branch tip that carries this
block; its full SHA and output are recorded in the merge entry in `docs/STATE.md`, because writing
them here would change the SHA being proven.

**Not met / verified failing:** the live-spine render and the P16 reconciliation clause (Snapshot
`equity_cents` against the run's `BrokerPositionSnapshot` equity) are the planner's post-merge
functionality check: not done from this worktree, which has no `.env`.

---

## Return notes

- 🩹 **The spec's law-cycle answer was stale.** It was written before S229 locked `SRF-TRG-02` at five
  tools; the book is amended to v1.1 in this sprint (DL-220 decision 9).
- 🪤 **"Latest run" was already defined twice** (`projections_vitals._latest_run_id`,
  `route_selection.selected_run`); now one `projections.latest_run_id`.
- The spec's sentence said *"Last 20 sessions"*; the Snapshot does not carry the rolling window, so the
  answer says *"Over the most recent sessions"* (DL-220 decision 10). If the operator wants the number,
  the reporter should write it into the performance group: a reporter change, not a surfaces one.
- `surfaces/queries/runs.py:96` and `surfaces/cli_commands.py:55` still read `snapshot:<run_id>`, which
  finds nothing on graph-pull runs; left alone as the spec asked. They look dead for graph-pull runs.
- The vital is its own slot at the front of the status line, fed by `/api/runs/<run>/performance`,
  because `infra.js` rewrites the whole vitals line on every refresh.
