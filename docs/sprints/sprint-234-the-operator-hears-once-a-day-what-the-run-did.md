<!-- Agent: planning | Role: sprint handover -->
# Sprint 234 — the operator hears once a day what the run did, with the money in it

**Phase:** Etalon-first continuous improvement (DL-19) · next leg P19, item **E19.1**
**Branch:** `sprint-234-the-operator-hears-once-a-day-what-the-run-did`
**Status:** BUILT (2026-09-26, cloud session; branch pushed, the planner gates and merges)
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [DL-230](../design-log.md) (operator, 2026-09-26: the brief may carry P&L amounts) ·
[DL-220](../design-log.md) (E16.2's Telegram line moved here) · work-queue **83** · the builder
records its decisions as the next free DL number (**DL-231** today)

> **Why this bump kind.** The dispatcher gains a capability it does not have: a daily report to the
> operator. That is a MINOR, with a law cycle on the dispatcher book.

**Builder:** Codex, after S233 (or a cloud session). **Your worktree has no `.env` and no network**:
every proof is on fixtures. The planner previews the brief on the live graph before deploy, and the
first real send is the functionality check. **If a number you measure differs from one written here,
stop and report. Do not adjust and continue.**

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md`, `orchestration/laws/dispatcher/laws.md` | A component's **locked constitution** | **LOCKED. Read-only during a build**, except the dispatcher amendments this spec names (the law-cycle answer is Yes). Any other clause you believe is wrong is a `drift-register.md` row plus a report |
| `.../laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: dispatcher **`DSP-TRG-02`** (calendar skip before notices), **`DSP-STA-02`** and
**`DSP-FAIL-01`** (Telegram failures are contained faults), **`DSP-NEV-02`** (never talks to the
broker), **`DSP-SEC-01`**, **`DSP-OBS-02`** (Melbourne time first), **`DSP-PERF-01`**, **`DSP-TYP-01`**,
the `CAP` block; reporter **`RPT-SEC-02`** (read [DL-230](../design-log.md) for why it is not amended);
supervisor `compute_health` (the one definition of "needs a human").

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's answer is Yes (a new guarantee), No (`contracts/`).** The dispatcher gains the brief.
Owed in this unit of work: **dispatcher laws LOCKED v1 → v1.1** with a Changelog line naming DL-230 and
this sprint:

- **`DSP-IDN-04`** (new): the scheduled dispatcher sends one daily brief per scheduled run it placed; it
  reports what the run did and never decides anything from it.
- **`DSP-TRG-03`** (new): the brief is attempted on every fire once the run's `Snapshot` exists,
  **including after the action window**; on the last fire of the day a placed run with no `Snapshot`
  gets one RED brief instead.
- **`DSP-OUT-06`** (new): the brief's content (scope item 3).
- **`DSP-IDM-03`** (new): at most one brief per run id, recorded on the dispatcher's own `RunRequest`.
- **`DSP-SEC-02`** (new, DL-230): P&L amounts leave only in the brief, only to the configured operator
  chat, only through the injected port. The job's printed output and every fault carry no amount.
- **`DSP-FAIL-03`** (new): composing or sending a brief can fail only into a fault; it never changes the
  placement outcome and never crashes the fire.
- **`DSP-DEP-01`** amended: the graph reads now include the reporter's `Snapshot`, `Fill`, `Fault` and
  `Flag` facts and the pack's acceptance verdict. **`CAP`** gains `send_brief` and the read labels.

Plus a `test-plan.md` row per clause with the clause ID in each test docstring, both rollups
(`docs/laws/ledger.md` and `docs/laws/INDEX.md`, derived by `make ci`), and the header's version.
**`RPT-SEC-02` is not amended** (DL-230): its subject is the reporter, which still sends nothing.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/scheduled_dispatch_human.py` (164) | dispatcher `laws.md` + `test-plan.md` | the fire's order: calendar skip, polling, the action-window early return |
| new `orchestration/daily_brief*.py` | dispatcher book; reporter `RPT-SEC-02`, `RPT-OUT-07`, `RPT-IDM-03`; DL-224 | reads the reporter's facts, never recomputes them |
| `orchestration/telegram_client.py` (120), `telegram_port.py` (41) | `DSP-SEC-01`, `DSP-STA-02`, `DSP-FAIL-01` | the port boundary and its failure containment |
| `scripts/dispatch_scheduled_run.py` (129) | `DSP-SEC-02` (new) | its printed line goes to the job log, an external system |
| `orchestration/Dockerfile` | DL-218 (a missing COPY killed every fire at import) | the slim image copies file by file |
| `agents/supervisor/domain/health.py` (read only) | supervisor book | `compute_health` is the one definition of open incidents and pending human flags |

⚠️ **The one invariant: the brief can never stop, delay or change a run's placement.** If your design
lets a brief exception, a slow Telegram call or a missing module reach the placement path, stop and
report.

---

## Goal

After this sprint, the operator gets one Telegram message per scheduled run, about ten minutes after it
finishes. It gives the verdict, the money (equity and its change since the previous brief), the vs-SPY
scoreboard, what was ordered, what filled and which stops were hit, and what needs them, usually
nothing. A run that did not finish by the day's last dispatcher fire gets one RED message instead. The
text is deterministic and makes no LLM call. Nothing else changes: placement, holds and notices behave
exactly as before.

## Why (context)

The etalon bar is unattended operation with the evidence discipline catching its own defects. Today the
operator learns what happened by opening the dashboard or asking the planner. P19's first item gives
them one glance a day, pushed to them. The operator decided on 2026-09-26 that the brief may carry dollar
amounts ([DL-230](../design-log.md)).

### Measured, 2026-09-26 — read these before designing

From the planner's session on `main` @ `4e032403`, the live Neon spine (read-only) and the code.

| # | Claim | Value | How it was measured |
| --- | --- | --- | --- |
| 1 | When a run finishes | `MonitorRun` created at **22:42–22:46 UTC** on the last five scheduled runs (09-21 … 09-25); `PMRun` 22:39–22:42 | *[measured]* `walk_chain` timestamps |
| 2 | When the dispatcher fires | cron `*/10 22-23 * * 1-5` UTC: every 10 minutes, **22:00 → 23:50**; placement only 22:30–23:20 (`_ACTION_START`, `_ACT_BY`) | *[measured]* deployment record; `scheduled_dispatch_actions.py` |
| 3 | 🪤 **The fire returns early outside the action window** | `dispatch_with_human_answer` returns `outside_window(...)` before placement when `not is_action_time(now)`; a brief placed after that line never runs at 23:30–23:50 | *[measured]* read, `scheduled_dispatch_human.py` |
| 4 | Where each fire's run id comes from | `as_of` = today's UTC date; `decide_scheduled_run` names `sched-YYYY-MM-DD`; a non-session date exits **before** the graph opens | *[measured]* read, `scripts/dispatch_scheduled_run.py` |
| 5 | The verdict | `orchestration.packs.trading_acceptance.accept_run(graph, run_id).verdict` ∈ `PASS`, `NO_TRADE`, `UNPROVEN`, `FAIL`; **PASS** on all five runs above | *[measured]* |
| 6 | 🪤 **The verdict's import closure is heavy** | importing `trading_acceptance` loads **48** first-party modules outside `kernel`/`contracts`, **31** of them `agents.portfolio_manager.*` | *[measured]* fresh interpreter, `sys.modules` |
| 7 | The image guard | `tests/test_dispatch_scheduled_run.py::test_dispatcher_image_copies_everything_its_entrypoint_imports` walks every `from x import y` **including inside functions** (`ast.walk`) from `scripts/dispatch_scheduled_run.py` and fails on a missing `COPY` | *[measured]* read. A lazy import does not escape it |
| 8 | The scoreboard text | `Snapshot.headline_summary` ends with the reporter's clause, e.g. `vs SPY: -0.43 pts over 33 sessions at 21% invested` (sched-2026-09-25) | *[measured]* |
| 9 | The money | `Snapshot.metrics["performance"]["equity_cents"]`: **10,197,632** (09-25), **10,200,072** (09-24). Present from sched-2026-09-24; earlier Snapshots have no `performance` | *[measured]* |
| 10 | 🪤 Stored Snapshots are not rewritten | 09-24's equity was computed before DL-224 (the earliest-per-date rule), so the first brief's change (−$24.40) compares two rules | *[measured]*; DL-224 |
| 11 | Orders a run placed | `Fill` nodes with `source_run_id` = the run's `PMRun` id carry `ticker`, `side`, `quantity`, `order_applied_limit_price_cents`, `broker_status` | *[measured]* Fill properties |
| 12 | 🎯 **When a fill became known** | `broker_status_refreshed_at` is written when the status changes: the **108** filled `Fill`s carry refresh dates spread over two months, and no run after 2026-09-24 14:15 re-stamped any. `submitted_at` is useless for stops (a resting stop's placement date, and `None` on 24 stop fills) | *[measured]* |
| 13 | "Needs you" | `agents.supervisor.domain.health.compute_health(graph, None)` returns `open_incidents` and `pending_human_flags`; it imports only `kernel.fault_incidents`. Today: **0** live incidents | *[measured]* |
| 14 | The Telegram port | `TelegramClient.send_degraded_notice` sends plain text via `sendMessage` to the configured `chat_id` and returns the `message_id` or `None`; failures set `last_error`, never raise | *[measured]* read |
| 15 | How notices stay single | the degraded notice writes `degraded_notified_at` / `degraded_notice_message_id` on the `RunRequest`, and skips when present | *[measured]* read |
| 16 | The job's printed line | `format_dispatch_result` prints `placed/skipped/held <run_id> reason=…` to stdout, which the Container Apps job ships to Log Analytics | *[measured]* read; deployment |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (A1, A3, A6 below). Watch them fail on `main`. Paste the red output.
2. **When the brief goes.** In `dispatch_with_human_answer`, after the calendar decision and **before**
   the action-window early return (row 3), call one guarded brief step. It sends when today's run has a
   `Snapshot` and no brief marker; on the day's last fire (**23:50 UTC**, a named constant whose
   comment cites the cron) it sends the RED brief for a placed run with no `Snapshot`. A skipped run, or
   a held run that was never placed, gets no brief: the hold notice already told the operator.
3. **What it says** (plain text, Melbourne time first, one message):
   - verdict and header: `🟢 PASS · sched-2026-09-25 · Sat 26 Sep 08:50` (🟢 `PASS`/`NO_TRADE`,
     🟡 `UNPROVEN`, 🔴 `FAIL` or not finished), plus ` · degraded` for a degraded run;
   - money: `Equity $101,976.32 (−$24.40 since sched-2026-09-24)`; with no earlier `Snapshot` carrying
     `performance`, `(no earlier figure)`;
   - scoreboard: the reporter's own clause from `headline_summary` (row 8), never recomputed;
   - orders this run (row 11): `BUY 16 BMY ≤ $61.82`, or `Orders: none`;
   - filled since the last brief (row 12): filled `Fill`s, orders and stops, whose
     `broker_status_refreshed_at` lies after the previous briefed run's `PMRun.created_at` and no later
     than this run's; a stop fill reads `stopped out`; or `Filled: none`;
   - needs you: from `compute_health` (row 13), `nothing` or `2 open incidents · 1 critical flag`.
   The RED brief names the last stage that finished.
4. **Once per run.** On success, write `brief_sent_at`, `brief_message_id` and `brief_verdict` on the
   run's `RunRequest` (the dispatcher's own node, row 15). A failed send writes nothing and is retried on
   the next fire.
5. **Faults, never failure.** Composing and sending run inside a fault boundary: any exception or a
   `None` message id becomes a graph `Fault` (no amount in its message or context) and the fire goes on
   to place exactly as before. The brief module is imported inside that boundary, so a missing module
   degrades to a fault rather than a dead fire.
6. **The port.** `TelegramPort.send_brief(*, text: str) -> int | None` and its `TelegramClient`
   implementation, on the same pattern as `send_degraded_notice`.
7. **The image.** Add every module the brief imports to `orchestration/Dockerfile` until the closure test
   (row 7) passes. Expect about 48 lines (row 6).
8. **A preview.** `scripts/brief_preview.py --run-id <id>` prints the brief for any run from the live
   graph and **sends nothing and writes nothing**. The planner uses it before deploy.
9. **The law cycle** as answered above, and **DL-231** for the design decisions.

### Out of scope (do NOT build this sprint)

- **Two-way commands** (E19.2) and the **G-scorecard** (E19.3).
- **Any LLM call.** The brief is deterministic text.
- **Recomputing any figure the reporter owns** (equity, excess, sessions, exposure). Read them.
- **Rewriting stored Snapshots** (row 10).
- **Changing the cron, the action window, holds, notices or placement.**
- **Amending `RPT-SEC-02`** (DL-230). **No ADR reversal.**

### The road not taken (LAW-06)

- **The reporter sends the brief.** Rejected: `RPT-SEC-02`, and the reporter cannot read the pack's
  acceptance verdict, which lives above it in `orchestration/`.
- **Send the brief after the placement code.** Rejected by row 3: fires after 23:20 would never brief, and
  a run that finishes late would stay silent.
- **A new verdict computed in the dispatcher** (stage counts, fault counts). Rejected: a second
  definition of "did the run pass" beside `accept_run` is the dashboard's DL-208 failure again.
- **Copy whole `orchestration/` and `agents/portfolio_manager/` into the image.** A design decision for
  you (below), not a default: the file-by-file list is what DL-218's closure test guards.
- **Detect new fills by comparing with the previous brief's stored key list.** Rejected by row 12: the
  refresh timestamp already says when a fill became known, with no extra state.
- **A brief for held runs.** Rejected: the hold notice exists, and a second message about the same hold
  spends the notification budget.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Which module composes and which selects**, so each stays under 200 lines and the composer is a pure
   function of facts (testable without a graph).
2. **The "previous briefed run"** when a day was skipped, held or failed: the latest earlier `RunRequest`
   carrying `brief_sent_at`, or the previous scheduled run with a `Snapshot`.
3. **How the image carries the closure**: file-by-file `COPY` lines, or whole directories, and why.
4. **The exact text** of each line, including the RED brief and the degraded marker.

🪤 **Take the next free DL number, then re-check it at merge.** S232 holds DL-228, S233 DL-229, and
DL-230 is the operator's decision. Take **DL-231**.

---

## Blast radius — measured 2026-09-26

| What | Detail |
| --- | --- |
| Files changed | `orchestration/scheduled_dispatch_human.py` (164), `orchestration/telegram_client.py` (120), `orchestration/telegram_port.py` (41), `orchestration/Dockerfile`, `scripts/dispatch_scheduled_run.py` (129) only if its printed line must change; **new** `orchestration/daily_brief*.py`, `scripts/brief_preview.py`, tests; dispatcher `laws.md` (159) and `test-plan.md` (36); `docs/laws/ledger.md`, `docs/laws/INDEX.md` |
| Agents affected | none import another. The dispatcher (pack orchestration) reads the supervisor's `compute_health` and the pack's `accept_run`; `import-linter` must stay 4 kept / 0 broken |
| Contract change? | no |
| Graph vocabulary change? | **no** *[measured 2026-09-26]*: `RunRequest` declares no properties in `orchestration/packs/trading_graph_vocabulary.json` (the degraded notice already writes `degraded_notified_at` there the same way), so the three brief properties move no pack. If your design adds a declared property anywhere, the deploy becomes a full `up`: say so |
| New env keys / tunables | none. `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` already reach the job |
| Deploy implication | the dispatcher image rebuilds; **operator approval**; **image-only retag** of `dispatcher-cron` |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record DL-231.**
3. **Plant the failing tests first** (A1, A3, A6) and watch them fail. Paste the red output.
4. **Implement** scope items 2–8.
5. **Law cycle**: the clauses, test-plan rows, docstring citations, rollups, version, Changelog.
6. **Prove the guards can fail (DL-70)**: move the brief after the early return (A4 red); drop the marker
   check (A2 red); let a send exception escape (A6 red); print the equity in the job line (A10 red).
   Restore each.
7. **`make ci` green** — every step, **redirected to a file, never piped**.
8. **Fill the handback sections.**

---

## Test plan

Fixtures are in-memory graphs shaped like the live facts in the Measured table, and a fake Telegram port.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 a finished run gets its brief | a run like sched-2026-09-25: `PASS`, equity 10,197,632, previous brief's run with 10,200,072, the row-8 headline, no orders, no fills, 0 incidents | one `send_brief` whose text holds `PASS`, `sched-2026-09-25`, `$101,976.32`, `−$24.40`, `vs SPY: -0.43 pts over 33 sessions at 21% invested`, `Orders: none`, `Filled: none`, `Needs you: nothing`; the `RunRequest` carries `brief_sent_at`, `brief_message_id`, `brief_verdict` (`DSP-OUT-06`, `DSP-IDN-04`) |
| A2 | 🪤 a second fire sends nothing | A1, fired twice | exactly one send (`DSP-IDM-03`) |
| A3 | 🎯 not before the Snapshot; RED on the last fire | a placed run with no `Snapshot` at 22:40, then at 23:50 | no send at 22:40; one RED brief at 23:50 naming the last finished stage (`DSP-TRG-03`) |
| A4 | 🪤 the brief survives the early return | A1 at 23:30 UTC, outside the action window | the brief is sent and the placement result equals the no-brief result (`DSP-TRG-03`, `DSP-PERF-01`) |
| A5 | no brief for skipped or never-placed runs | a calendar skip; a held run with no `RunRequest` | no send (`DSP-TRG-02`) |
| A6 | 🎯 a failed send changes nothing else | the port raises, then returns `None` | a `Fault` with no amount; no marker; the `ScheduledDispatchResult` equals the no-brief result; the next fire retries (`DSP-FAIL-03`, `DSP-STA-02`) |
| A7 | a compose failure is contained | a `Snapshot` whose `metrics` is malformed | a `Fault`, no send, placement unchanged (`DSP-FAIL-03`) |
| A8 | 🎯 filled since the last brief | order and stop fills with `broker_status_refreshed_at` before, inside and after the window; a stop fill with `submitted_at=None` | only the in-window fills appear; the stop reads `stopped out` (`DSP-OUT-06`) |
| A9 | orders and money formatting | a buy and a sell with limit prices; no earlier `performance` Snapshot | `BUY 16 BMY ≤ $61.82`; `(no earlier figure)`; thousands separators and a signed change |
| A10 | 🪤 no amount outside the brief | A1 through the script's `main` with a fake port | the printed line and every `Fault` contain no dollar figure (`DSP-SEC-02`) |
| A11 | the image carries the brief | the existing closure test | passes with the new imports; `make ci`'s image step stays green (DL-218) |
| A12 | needs-you and degraded | 2 live incidents and 1 unresolved critical flag; a degraded run | `2 open incidents · 1 critical flag`; ` · degraded` in the header |
| A13 | the preview sends and writes nothing | `brief_preview` on A1's graph | prints A1's text; zero port calls; no marker |

---

## Success factors

- [ ] A finished scheduled run produces exactly one brief with the verdict, the money, the scoreboard,
      orders, fills and needs-you (A1, A2).
- [ ] The brief is sent on any fire after the `Snapshot`, including after the action window (A4), and a
      run that never finished gets one RED brief on the last fire (A3).
- [ ] No brief, compose or send can change or stop placement (A4, A6, A7).
- [ ] No dollar amount appears outside the Telegram message (A10).
- [ ] The image carries every module the brief imports (A11).
- [ ] Dispatcher laws v1.1: `DSP-IDN-04`, `DSP-TRG-03`, `DSP-OUT-06`, `DSP-IDM-03`, `DSP-SEC-02`,
      `DSP-FAIL-03` added, `DSP-DEP-01` and `CAP` amended, test-plan rows, both rollups.
- [ ] DL-231 recorded with rejected alternatives.
- [ ] Every guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The early return (row 3).** The obvious place for the brief, after placement, is exactly where fires
after 23:20 never arrive.
🪤 **A lazy import is still a copied import (row 7).** The closure test follows imports inside functions;
it will demand the whole verdict closure in the Dockerfile, and it is right to.
🪤 **Snapshots carry no `created_at`** (DL-225). Order runs by `PMRun.created_at`, as the supervisor does.
🪤 **`submitted_at` is not a fill time** (row 12), and it is `None` on stop fills.
🪤 **Stored Snapshots are not rewritten** (row 10). The first brief's change compares two rules; say
nothing clever about it, just print the two stored figures' difference.
🪤 **The job log is an external system** (row 16). `DSP-SEC-02` covers stdout and fault text, not only
Telegram.
🪤 **`equity_cents` is a float in the graph** (10197632.0). Format from integer cents.
🪤 **Your worktree has no network and no `.env`.** Live evidence is the planner's.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Near the block: `orchestration/scheduled_dispatch_human.py` **164**, `orchestration/scheduled_dispatch.py` **179**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: the last-fire time is a named constant whose comment cites the cron.
- Faults, not silent failure — `kernel.fault_boundary` or the existing `fault_safe`.
- `make ci` **every step** green, **100.00 % coverage floor**, **redirected to a file, never piped**.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the worktree whose `HEAD` is
   the commit being proven; check the printed SHA against `git rev-parse HEAD`.
2. Merge to `main` locally and push. Post-merge CodeQL.
3. **Planner, before deploy:** `brief_preview.py --run-id` on the last two scheduled runs from the live
   graph; show the operator the text.
4. **Deploy with operator approval**: rebuild the dispatcher image; image-only retag of `dispatcher-cron`.
5. **Functionality check on the first scheduled run after deploy:** exactly one Telegram brief arrives
   about ten minutes after the run finishes; the `RunRequest` carries the three brief properties; the next
   fire sends nothing; the job log shows no amount; the operator confirms the message. Record it in
   `docs/laws/functionality-checks.md`.

---

## Handover — paste this to Codex

```text
Sprint 234 — the operator hears once a day what the run did, with the money in it (P19 E19.1).
Spec: docs/sprints/sprint-234-the-operator-hears-once-a-day-what-the-run-did.md (read all of it).

Branch: sprint-234-the-operator-hears-once-a-day-what-the-run-did, in its own worktree. Never main.
You have NO .env and NO network. Every proof is on in-memory fixtures and a fake Telegram port.

What: one deterministic Telegram message per scheduled run, sent by the scheduled dispatcher once the
run's Snapshot exists: verdict (accept_run), equity and its change since the previous brief (from the
Snapshots' metrics.performance.equity_cents), the reporter's own vs-SPY clause (Snapshot
headline_summary), orders this run, fills since the last brief (by broker_status_refreshed_at), and
needs-you (supervisor compute_health). A placed run with no Snapshot by the 23:50 UTC fire gets one
RED brief. Operator decision DL-230: dollar amounts are allowed, but only inside the brief.

MUST RULE before any code: read orchestration/laws/dispatcher/{laws.md,test-plan.md}, the reporter
book's RPT-SEC-02 and DL-230, agents/supervisor/domain/health.py, docs/laws/conventions.md,
docs/laws/drift-register.md. Fill the Law reading record first.
Law-cycle answer: YES (new guarantee). Dispatcher laws v1 -> v1.1: DSP-IDN-04, DSP-TRG-03,
DSP-OUT-06, DSP-IDM-03, DSP-SEC-02, DSP-FAIL-03 new; DSP-DEP-01 and CAP amended; test-plan rows;
docstring citations; rollups via make ci. Do NOT amend RPT-SEC-02.

Build:
1. Red first: A1 (a finished run gets its brief), A3 (none before the Snapshot; RED on the last
   fire), A6 (a failed send changes nothing else). Paste the red run.
2. In dispatch_with_human_answer, call one guarded brief step AFTER the calendar decision and BEFORE
   the action-window early return (otherwise 23:30-23:50 fires never brief).
3. Brief module(s): pure composer + fact selection; import it inside the fault boundary.
4. TelegramPort.send_brief(*, text) -> int | None; TelegramClient implements it like
   send_degraded_notice.
5. Once per run: brief_sent_at, brief_message_id, brief_verdict on the run's RunRequest. A failed send
   writes nothing and retries next fire.
6. orchestration/Dockerfile: COPY every module the closure test demands (~48).
7. scripts/brief_preview.py --run-id <id>: prints the brief, sends nothing, writes nothing.

Order: DL-231 (re-check the number) -> red A1/A3/A6 -> implement -> law cycle -> DL-70 plants (brief
after the early return; no marker check; a send exception escapes; equity printed in the job line;
each must go red; restore) -> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- let any brief failure, slow call or missing module reach or change placement.
- recompute the reporter's figures, or write a second verdict beside accept_run.
- print or fault any dollar amount outside the Telegram message (the job log is external).
- use submitted_at as a fill time (it is None on stop fills).
- touch the cron, the action window, holds, notices, placement, or stored Snapshots.
- grow scheduled_dispatch_human.py (164) or scheduled_dispatch.py (179) past 200.
- claim a live proof: the preview and the first real send are the planner's.
- pin a version: MINOR, next available at merge, uv.lock staged with it.
RunRequest declares no vocabulary properties (measured), so the deploy is an image-only retag; if
your design adds a declared property anywhere, say so.

Handback: Law reading record, Test plan results, Closeout (red then green, DL-70 plants, line counts,
make ci file + exit code), Return notes. Status: BUILT, and this sprint's README.md row leads with BUILT
in the same commit. Commit on the branch; the planner pushes, gates and merges. Anything not met:
"not done".
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

*Filled 2026-09-26, in worktree `s234` on `f2e97d56`, before the first code change. Whole files read:
dispatcher `laws.md` (LOCKED v1) and `test-plan.md`; reporter `laws.md` (LOCKED v1.3) and
`test-plan.md`; supervisor `laws.md` (LOCKED v1.2) and `test-plan.md` rows `SUP-OUT-02`/`SUP-OBS-02`;
`docs/laws/conventions.md`; `docs/laws/drift-register.md`; DL-230, DL-224, DL-225, DL-220, DL-218, DL-70.*

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `orchestration/scheduled_dispatch_human.py` (164) | dispatcher `laws.md` + `test-plan.md` | `DSP-TRG-02` 🟩, `DSP-TRG-01` 🟩, `DSP-PERF-01` 🟩, `DSP-IDM-02` 🟩, `DSP-OUT-01`/`-02`/`-05` 🟩, **`DSP-TYP-01` ⬜** | **Yes.** The step goes after the calendar skip *and* the answer marking, immediately before `is_action_time`, so the hold, poll and answer order is byte-identical (`DSP-TRG-02`) and fires after 23:20 still reach it (row 3). `ScheduledDispatchResult` gains no field. `DSP-TYP-01` is ⬜, so result equality is asserted by A4/A6, not assumed |
| new `orchestration/daily_brief*.py` | dispatcher book; reporter book (`RPT-SEC-02` ⬜, `RPT-OUT-07` 🟩, `RPT-IDM-03` 🟩, `RPT-FAIL-04` 🟩, `RPT-OUT-06` ⬜, `RPT-STA-02` 🟩); DL-224, DL-225, DL-230, DL-220 | `DSP-NEV-02` ⬜, `DSP-SEC-01` ⬜, `DSP-OBS-02` 🟩; the six new clauses; `RPT-SEC-02` stays unamended | **Yes.** `RPT-FAIL-04`'s contained failure stores `equity_cents: 0.0` with zero sessions and `RPT-OUT-06`'s degraded Snapshot has no `performance` group, so a figure counts only with sessions > 0 (DL-220: unavailable never reads as zero). Runs are ordered by `PMRun.created_at` (DL-225). Only `sched-*` runs are references: a manual run's Snapshot dates an intraday sync (DL-224) |
| `orchestration/telegram_client.py` (120), `telegram_port.py` (41) | dispatcher book | `DSP-SEC-01` ⬜, `DSP-STA-02` 🟩, `DSP-FAIL-01` 🟩 | **Yes.** `fault_safe` stores `str(exc)` and the traceback on the `Fault`, so a port exception that carried the text would put an amount in a fault. The brief records its own fault naming only the step and an error type (`DSP-SEC-02`). `send_brief` mirrors `send_degraded_notice`: never raises, sets `last_error` |
| `scripts/dispatch_scheduled_run.py` (129) | `DSP-SEC-02` (new); measured row 16 | `DSP-SEC-01` ⬜ | **No code change.** The brief's text never enters `ScheduledDispatchResult`, so `format_dispatch_result` cannot print it; A10 drives `main` to prove it rather than asserting it |
| `orchestration/Dockerfile` | DL-218; the closure test (row 7) | — | **Yes.** Importing `agents.supervisor.domain.health` runs `agents/supervisor/__init__.py`, which imports `SupervisorAgent`: 10 files row 6's 48 does not count (DL-231) |
| `agents/supervisor/domain/health.py` (read only) | supervisor book | `SUP-OUT-02` 🟩, **`SUP-OBS-02` ⬜** | **Yes, a finding.** `SUP-OBS-02` says `open_incidents` derives from `Flag` nodes; `compute_health` counts live `Fault` incidents (DL-208). The brief prints `compute_health`'s numbers as they are: **DRIFT-076** |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **Yes, a new
guarantee; no `contracts/` change.** Dispatcher laws LOCKED v1 → v1.1: `DSP-IDN-04`, `DSP-TRG-03`,
`DSP-OUT-06`, `DSP-IDM-03`, `DSP-SEC-02`, `DSP-FAIL-03` new; `DSP-DEP-01` and `CAP` amended.
`RPT-SEC-02` is not amended (DL-230).

**Contradictions found between a law and this spec:** none. Checked: `DSP-IDN-01` ("decides one
outcome") and `DSP-NEV-02` (no broker) hold, because the brief reads graph facts and decides
nothing; `DSP-OUT-01`'s "no degraded-posture properties" is placement's write, and the three brief
properties arrive later on a finished run; `DSP-IDM-02`'s re-merge keeps them, because placement
re-writes the same values.

**Laws found silent where a decision was needed:** (1) `DSP-IDN-03` says the book governs
`scheduled_dispatch*.py`, readiness, answers and notices, and is silent on the brief's modules.
Decided: the new `DSP-IDN-04` names `daily_brief*.py`; `DSP-IDN-03` is not in the spec's amendment
list, so it stays and **DRIFT-077** records it. (2) No clause says which run a fire concerns when
`--as-of` names a past session (functionality checks do this). Decided (DL-231): a fire briefs only
its own UTC day; `DSP-TRG-03` states it, so this law cycle closes the silence. **Clauses relied on
that are ⬜:** `DSP-TYP-01`, `DSP-SEC-01`, `DSP-NEV-02`, `DSP-DEP-01`, `RPT-SEC-02`, `RPT-OUT-06`,
`SUP-OBS-02`.

**Clauses that were ⬜ and are now proven:** **`DSP-SEC-01`**, by
`tests/test_dispatcher_credential.py::test_the_bot_credential_never_leaves_the_port_on_any_path`: the
real `TelegramClient` carries a hold notice, an answer (poll, acknowledge, confirm), a degraded notice
and the brief through `main`; the credential reaches the transport on every call and no printed line,
graph fact or dispatch parameter. `DSP-DEP-01` stays ⬜: the new `CAP` conformance test proves its
graph and port halves only (named as partial in its row).

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_a_finished_run_gets_its_brief` | `orchestration/tests/test_daily_brief_dispatch.py` | 🟩 pass; **red first** at `5ed442a` | `DSP-OUT-06`, `DSP-IDN-04`, `DSP-IDM-03` |
| A2 | `test_a2_a_second_fire_sends_nothing` (fires 22:50, 23:00, 23:50) | `orchestration/tests/test_daily_brief_dispatch.py` | 🟩 pass | `DSP-IDM-03` |
| A3 | `test_a3_nothing_before_the_snapshot_then_red_on_the_last_fire` | `orchestration/tests/test_daily_brief_dispatch.py` | 🟩 pass; **red first** at `5ed442a` | `DSP-TRG-03`, `DSP-IDM-03` |
| A4 | `test_a4_the_brief_survives_the_windows_early_return` (also: the graph's only change is the three marker properties) | `orchestration/tests/test_daily_brief_boundaries.py` | 🟩 pass | `DSP-TRG-03`, `DSP-PERF-01`, `DSP-IDN-04` |
| A5 | `test_a5_no_brief_for_a_skipped_or_a_never_placed_run` (the skipped day carries a finished chain) | `orchestration/tests/test_daily_brief_boundaries.py` | 🟩 pass | `DSP-TRG-02`, `DSP-TRG-03`, `DSP-IDN-04` |
| A6 | `test_a6_a_failed_send_changes_nothing_else_and_the_next_fire_retries` (the port raises quoting the text, then returns `None`) | `orchestration/tests/test_daily_brief_dispatch.py` | 🟩 pass; **red first** at `5ed442a` | `DSP-FAIL-03`, `DSP-STA-02`, `DSP-SEC-02`, `DSP-IDM-03` |
| A7 | `test_a7_a_malformed_snapshot_is_a_fault_and_nothing_else` ×2 (metrics not a mapping; equity not a number) | `orchestration/tests/test_daily_brief_boundaries.py` | 🟩 pass | `DSP-FAIL-03`, `DSP-SEC-02` |
| A8 | `test_a8_only_fills_that_became_known_since_the_previous_brief` (both edges, a naive time, a pending fill, `submitted_at` inside and refresh outside, an unreadable time) | `orchestration/tests/test_daily_brief_facts.py` | 🟩 pass | `DSP-OUT-06` |
| A9 | `test_a9_money_is_integer_cents_with_separators_and_a_signed_change`; `test_a9_orders_and_fills_read_as_the_broker_holds_them`; graph-side `test_orders_are_this_runs_fills_including_a_resumed_runs`, `test_no_reference_figure_reads_no_earlier_figure` ×5 | `orchestration/tests/test_daily_brief_text.py`; `orchestration/tests/test_daily_brief_facts.py` | 🟩 pass | `DSP-OUT-06` |
| A10 | `test_a10_no_amount_leaves_through_the_job_log_or_a_fault` ×2 (sent; port raised) through `main` | `tests/test_dispatch_brief_script.py` | 🟩 pass | `DSP-SEC-02` |
| A11 | `test_dispatcher_image_copies_everything_its_entrypoint_imports`, its reader now following `from a.b import c` to a submodule | `tests/test_dispatch_scheduled_run.py`, `tests/image_closure.py` | 🟩 pass | none (DL-218's guard) |
| A12 | `test_a12_needs_you_is_what_health_counts_and_degraded_says_so` (through the real `compute_health`) | `orchestration/tests/test_daily_brief_facts_edges.py` | 🟩 pass | `DSP-OUT-06` |
| A13 | `test_a13_the_preview_prints_the_brief_and_sends_and_writes_nothing` (a graph that refuses writes; building a Telegram client raises) | `tests/test_brief_preview.py` | 🟩 pass | `DSP-OUT-06`, `DSP-IDM-03` |

**Tests added beyond the plan:** `test_a_missing_brief_module_is_a_fault_and_the_fire_places`,
`test_a_fault_the_graph_refuses_still_never_stops_the_fire`, `test_a_refire_for_a_past_session_briefs_nothing`
(`orchestration/tests/test_daily_brief_boundaries.py`); `test_the_reference_is_the_previous_scheduled_run_by_pm_time` (a manual run, a later run, a
Snapshot with no PMRun, one with no RunRequest, and a second Snapshot of the same run are none of them a
reference) (`orchestration/tests/test_daily_brief_facts.py`); `test_this_runs_missing_figure_prints_no_amount` ×2,
`test_the_scoreboard_is_the_reporters_clause_as_stored` ×2, `test_unreadable_facts_are_named_data_errors_not_guesses`,
`test_a_red_brief_names_the_stage_and_what_the_run_ordered` (`orchestration/tests/test_daily_brief_facts_edges.py`); `test_the_measured_run_reads_exactly_as_specified`,
`test_the_header_colour_is_the_verdicts` ×4, `test_needs_you_counts_read_as_words`,
`test_the_time_is_the_operators_and_utc_without_zone_data` (`orchestration/tests/test_daily_brief_text.py`); three `send_brief` port tests
(`orchestration/tests/test_telegram_brief.py`: plain text to the configured chat only; failures as values
keeping the transport error; a refused send's fault names the port's error word, and a port whose error
carries text is reduced to `no message id`); `tests/test_brief_preview.py` RED preview, unknown run, no
`POSTGRES_DSN`; `tests/test_dispatcher_credential.py` (`DSP-SEC-01`, above);
`orchestration/tests/test_dispatcher_capability.py::test_every_fire_stays_inside_the_declared_capability`
(the `CAP` block parsed from the law book and held against what six real fires read, write and send).

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** worktree `/home/user/s234` (a cloud session), branch
`sprint-234-the-operator-hears-once-a-day-what-the-run-did` from `origin/main` @ `f2e97d56`. **No `.env`**,
no fleet or Neon access: every proof is on in-memory graphs and fake or transport-replaced Telegram ports.

**Result:** the scheduled dispatcher sends one deterministic brief per scheduled run once its Snapshot
exists, and one RED brief at the 23:50 UTC fire for a placed run with none; the brief never reaches
placement. Measured in code, not live: the preview and the first real send are the planner's.

**Files changed:** `orchestration/daily_brief.py`, `daily_brief_facts.py`, `daily_brief_fills.py`,
`daily_brief_guard.py`, `daily_brief_text.py` (new); `orchestration/scheduled_dispatch_human.py` (+1
import, +3 lines: the call); `orchestration/telegram_port.py`, `telegram_client.py` (`send_brief`);
`orchestration/Dockerfile` (+61 `COPY`, 39 → 100); `scripts/brief_preview.py` (new);
`tests/test_dispatch_scheduled_run.py` and `tests/image_closure.py` (the closure reader, split out and
following submodules); tests and fixtures under `orchestration/tests/` and `tests/`; dispatcher
`laws.md` and `test-plan.md` (v1.1); `docs/laws/ledger.md`, `docs/laws/INDEX.md` (32 / 36);
`docs/laws/drift-register.md` (DRIFT-076, DRIFT-077); `docs/design-log.md` (DL-231); this spec and the
sprint README row; `pyproject.toml` 0.113.00 → **0.114.00** and `uv.lock` (one line). Not changed:
`scripts/dispatch_scheduled_run.py`, the cron, the action window, holds, notices, placement, any Snapshot.

**Design decisions:** [DL-231](../design-log.md): five modules with a pure composer; the previous briefed
run is the latest earlier *scheduled* run with a Snapshot, by `PMRun.created_at`; file-by-file `COPY`
(61, not ~48: the supervisor package `__init__` adds 10); the exact text; the RED brief does not call
`accept_run` (`brief_verdict` `NOT_FINISHED`); a fire briefs only its own UTC day. Plus the closure
test's blind spot, found and fixed.

**Proof — the red run first** (`5ed442a`: the three tests against the unchanged dispatcher, exit 1):

```text
FFF                                                                      [100%]
=================================== FAILURES ===================================
____________________ test_a1_a_finished_run_gets_its_brief _____________________
orchestration/tests/test_daily_brief_dispatch.py:83: in test_a1_a_finished_run_gets_its_brief
    assert telegram.briefs == [_A1_TEXT]
E   AssertionError: assert [] == ['🟢 PASS · sc...you: nothing']
E     
E     Right contains one more item: '🟢 PASS · sched-2026-09-25 · Sat 26 Sep 08:50\nEquity $101,976.32 (−$24.40 since sched-2026-09-24)\nvs SPY: -0.43 
E     Use -v to get more diff
________ test_a3_nothing_before_the_snapshot_then_red_on_the_last_fire _________
orchestration/tests/test_daily_brief_dispatch.py:106: in test_a3_nothing_before_the_snapshot_then_red_on_the_last_fire
    assert telegram.briefs == [
E   AssertionError: assert [] == ['🔴 NOT FINIS...you: nothing']
E     
E     Right contains one more item: '🔴 NOT FINISHED · sched-2026-09-25 · Sat 26 Sep 09:50\nLast stage finished: execution\nOrders: none\nNeeds you: no
E     Use -v to get more diff
_____ test_a6_a_failed_send_changes_nothing_else_and_the_next_fire_retries _____
orchestration/tests/test_daily_brief_dispatch.py:140: in test_a6_a_failed_send_changes_nothing_else_and_the_next_fire_retries
    assert len(faults) == 2
E   assert 0 == 2
E    +  where 0 = len(())
=========================== short test summary info ============================
FAILED orchestration/tests/test_daily_brief_dispatch.py::test_a1_a_finished_run_gets_its_brief
FAILED orchestration/tests/test_daily_brief_dispatch.py::test_a3_nothing_before_the_snapshot_then_red_on_the_last_fire
FAILED orchestration/tests/test_daily_brief_dispatch.py::test_a6_a_failed_send_changes_nothing_else_and_the_next_fire_retries
3 failed in 0.53s
```

**Proof — the green run:** see `make ci` below (the same three tests pass at every later commit; the
full suite line is quoted there). In the simulated slim image (only the Dockerfile's `COPY` set, the
repo root off `sys.path`), the calendar-skip smoke prints `skipped sched-2026-07-04` and an A1-shaped
fire sends exactly A1's text with no fault:

```text
smoke exit 0 | skipped sched-2026-07-04 reason=2026-07-04 is not a NYSE trading session
drive exit 0
result: placed sched-2026-09-25
briefs sent: 1
🟢 PASS · sched-2026-09-25 · Sat 26 Sep 08:50
Equity $101,976.32 (−$24.40 since sched-2026-09-24)
vs SPY: -0.43 pts over 33 sessions at 21% invested
Orders: none
Filled: none
Needs you: nothing
marker: {'brief_sent_at': '2026-09-25T22:50:00+00:00', 'brief_message_id': 101, 'brief_verdict': 'PASS'}
```

The same simulation without `agents/portfolio_manager/domain/deployment_floor.py`: `result: placed`,
`briefs sent: 0`, `FAULT: daily brief not sent for sched-2026-09-25: brief failed (ImportError)`, smoke
still green.

**Guards planted** (each applied to the committed file, its test run, the file restored with `git
checkout`; every restore re-ran green, and `git status` was clean after the last):

| # | Plant | Test | Planted | Restored |
| --- | --- | --- | --- | --- |
| 1 | the brief call moved after the action-window return | A4 | **red**: `assert 0 == 1` (no brief at 23:30) | green |
| 2 | the marker check dropped (`if request is None:`) | A2 | **red**: two extra briefs at 23:00 and 23:50 | green |
| 3 | a send exception escapes: the step's `except` around `send_brief` removed **and** the guard narrowed to `ImportError` | A6 | **red**: `RuntimeError: telegram refused the brief: …` out of the fire | green |
| 3a/3b | either layer alone removed | A6 | green, both: each layer alone contains a send failure | — |
| 4 | the equity printed in the job line (`sys.stdout.write(f"brief {run_id} equity={…}")` in the step) | A10 | **red**, both params: `+ brief sched-2026-09-25 equity=10197632` | green |
| 5 | the fault quotes the exception (`f"send failed ({exc})"`) | A6 | **red**: an amount in the Fault | green |
| 6 | the Dockerfile loses `deployment_floor.py` | A11 | **red**: `dispatcher image omits imported modules: ['agents/portfolio_manager/domain/deployment_floor.py']`; **main's old closure test passes the same Dockerfile** | green |
| 7 | `CAP` forgets the `Fill` read | CAP test | **red**: `Extra items in the left set: 'Fill'` | green |

**Module line counts:** `daily_brief.py` 87, `daily_brief_facts.py` 166 ⚠, `daily_brief_fills.py` 101,
`daily_brief_guard.py` 71, `daily_brief_text.py` 179 ⚠, `scheduled_dispatch_human.py` **168** (was 164),
`scheduled_dispatch.py` **179** (unchanged), `telegram_client.py` 133, `telegram_port.py` 45,
`scripts/brief_preview.py` 81, `scripts/dispatch_scheduled_run.py` 129 (unchanged),
`tests/test_dispatch_scheduled_run.py` 143 (was 191; 198 before its reader moved to
`tests/image_closure.py`, 68). ⚠ = over the 150 warning, under the 200 block.

**`make ci`:** *pending: filled from the run's file below*

**`make gate-ran`:** *planner, after push*

**Not met / verified failing:**

- **`uv.lock` was not regenerated by `uv lock`**: it needs `download.pytorch.org` (the forecaster extra's
  torch index), which this environment's network policy refuses (403), and offline the torch metadata is
  not cached. The one line a version-only bump changes (`version = "0.113.0"` → `"0.114.0"`, the shape of
  S231's bump) was edited to match, and `uv sync --frozen` passes. **Not verified by `uv lock`**: run it
  at merge (expected no-op).
- **No live proof:** the preview on the live graph and the first real send are the planner's.
- **`DSP-DEP-01` stays ⬜** (partial, named in its row).

---

## Return notes

- **Numbers to re-check at merge.** DL-231 was free on `main` at build time (S232 holds DL-228, S233
  DL-229). DRIFT-076/077 follow S232's reserved DRIFT-075. Version **0.114.00** was the next MINOR at
  build time; if S232 or S233 merges first with a MINOR, re-bump and re-lock. Rollups read 32 / 36.
- **The closure test was blind to `from a.b import c`** (DL-218's class, one import form wider). With the
  Dockerfile the old test accepted, every brief would have died at import: contained as a fault, the
  feature silently dead, the build smoke green. The corrected reader demands nothing new on `main`, so
  the running image was never exposed. The slim-image simulation that found it
  (copy the `COPY` set, run a fire) could be a CI step; it is not added here.
- **The spec's "about 48 lines" is 61**: row 6 (48, 31 PM) and row 13 reproduce exactly; the estimate
  omitted that importing `agents.supervisor.domain.health` runs `agents/supervisor/__init__.py`, which
  imports `SupervisorAgent` (10 files).
- **Two findings recorded, not fixed:** DRIFT-076 (`SUP-OBS-02` says `open_incidents` derives from
  `Flag`s; `compute_health` counts `Fault` incidents) and DRIFT-077 (`DSP-IDN-03`'s scope sentence and
  the book's purpose line predate the brief). Neither book was in S234's amendment list.
- **A coverage-gate quirk:** any clause-shaped ID written in a `laws.md` counts as that book's own
  clause, so the dispatcher changelog cannot name the reporter's clause by ID (it read 37 clauses with
  one missing row until reworded).
- **Needs-you counts the brief's own faults.** A send that failed at 22:50 is a live `Fault`, so the
  brief that succeeds at 23:00 says `1 open incident`: honest, and resolvable like any other.
- **Planner's preview:** `PYTHONPATH=. python scripts/brief_preview.py --run-id sched-2026-09-25` from a
  tree with the live `.env`. It prints the full brief (or the RED one for an unfinished run) with the
  current time in the header, and builds no Telegram client. sched-2026-09-25 against sched-2026-09-24
  should read −$24.40 (two rules, DL-224); sched-2026-09-24 should read `(no earlier figure)`.
- **First real send:** the first fire after the Snapshot exists, most likely 22:50 UTC (08:50 AEST).
  The job log line is unchanged (`placed …` or `skipped …`).
- **The script tests drive `main` at 23:30** (outside the window), because `main` places with the real
  file universe and the fixtures place one ticker.
