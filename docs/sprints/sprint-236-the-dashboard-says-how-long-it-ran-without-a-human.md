<!-- Agent: planning | Role: sprint handover -->
# Sprint 236 — the dashboard says how long the pack has run without a human, from the graph alone

**Phase:** Etalon-first continuous improvement (DL-19) · next leg P19, item **E19.3** (the G-scorecard)
**Branch:** `sprint-236-the-dashboard-says-how-long-it-ran-without-a-human`
**Status:** BUILT · 2026-09-27 · Claude cloud session, branch pushed; `make gate-ran`, `uv lock` and Windows `make ci` owed to the planner
**Version:** *next available MINOR at merge*
**Effort:** S (one query, one vital, one tool, one law cycle)
**Decisions:** PRD §10 (G1, G3) · [next-leg plan](../next-leg-plan.md) § P19 · [DL-220](../design-log.md)
(the vital pattern S228 set) · [DL-231](../design-log.md) (the brief writes `brief_verdict`) ·
work-queue **83** · the builder records its decisions as **DL-235** (**DL-234 is S235's**, built in
parallel)

> **Why this bump kind.** The dashboard and the chat gain an answer they could not give: whether the
> pack is meeting its autonomy goals, and for how many sessions in a row. New capability → MINOR.

**Builder:** a Claude cloud session (claude.ai/code). **It has no `.env`, no `gh`, and cannot reach
`download.pytorch.org`** ([DL-228](../design-log.md), CLAUDE.md ☁️). So: every proof is on in-memory
graph fixtures; `make gate-ran` is **owed to the planner**; and the version bump's `uv lock` may fail to
re-resolve, in which case `uv.lock` stays untouched and the handback says so. Run results read through
the GitHub connector are an observation, never `GATE PROVEN`. The live read is the planner's, after
merge. **If a number you measure differs from one written here, stop and report. Do not adjust and
continue.** S235 is being built at the same time by Codex in `scripts/`; the two share no file.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `surfaces/laws/laws.md` + `test-plan.md` | The surfaces book, **LOCKED v1.1** | This sprint **owes it a law cycle** (below): the amendment is in scope, nothing else in it is |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`SRF-TRG-02`** (the MCP tool catalogue), **`SRF-OUT-03`** (chat answers are
grounded and audited), **`SRF-OUT-05`** (no sprint, DL, drift or law ids in operator text),
**`SRF-OUT-06`** (no unwired control), **`SRF-OUT-07`** (the vital pattern this sprint copies),
**`SRF-PARAM`**, plus the `NEV` and `PERF` sections.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read `surfaces/laws/test-plan.md` alongside `surfaces/laws/laws.md`. If a clause you rely on is ⬜,
   say so.
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

**Yes: a new guarantee, no contract change.** The surfaces gain a vital, a chat answer and an MCP tool,
exactly the shape S228 added. The cycle owed, in the same unit of work:

- `SRF-TRG-02` lists the new tool (`scorecard`);
- a new clause **`SRF-OUT-08`** stating what the scorecard reports and from what (Scope item 7);
- one `PARAM` row per new tunable;
- the book's version to **v1.2** with a Changelog line;
- a `test-plan.md` row per new or changed clause, each citing its tests;
- the rollup in **both** `docs/laws/ledger.md` and `docs/laws/INDEX.md` (let `make ci` tell you the
  number: it recomputes it);
- a `drift-register.md` row for anything the change slips under.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| **new** `surfaces/queries/scorecard*.py` | `surfaces/laws/laws.md` + `test-plan.md`; conventions | `SRF-OUT-08` (new); graph reads only, no model, no agent request |
| `surfaces/dashboard/projections_vitals.py` (133), **new** projection module, `static/index.html` (148), **new** `static/*.js` | same | `SRF-OUT-05`, `SRF-OUT-06`, `SRF-OUT-07`'s pattern |
| `surfaces/mcp_tools.py` (150), **new** `surfaces/scorecard_tool.py` | same | `SRF-TRG-02` |
| `surfaces/dashboard/chat.py` (141) `_QUICK_TOOLS` | same | `SRF-OUT-03`: a quick tool answers from the graph, no model |
| `surfaces/dashboard/settings.py` (**176**) | `SRF-PARAM` | new tunables; the file must be split, not grown past 200 |
| `orchestration/packs/trading_acceptance.py` `accept_run` (read only) | `docs/laws/` acceptance rows | **the** per-run verdict; never recompute it |
| `orchestration/daily_brief.py` (read only) | dispatcher laws v1.1 | writes `brief_verdict` on the `RunRequest` once a brief is sent |
| `orchestration/scheduled_dispatch.py` `ProviderTradingCalendar` (read only) | — | the one session calendar the dashboard already uses |
| `contracts/operator.py` `IntentFamily` (read only) | operator laws | which intents change state |

⚠️ **One invariant: the scorecard decides nothing and recomputes no verdict.** A session's verdict is
the acceptance gate's (stored as `brief_verdict`, or `accept_run`'s). If your design needs a verdict
rule of its own, stop and report.

---

## Goal

After this sprint the dashboard shows one glance tile, and the chat and MCP give one answer, saying
whether the pack is meeting the PRD's two autonomy goals over the last 30 days:

- **G1:** the share of scheduled sessions whose run completed (`PASS` or `NO_TRADE`);
- **G3:** the share of healthy sessions on which a human acted.

Both answers also say how many sessions in a row have run with no human action, which is the clock
P19's exit needs (20 sessions). Every number comes from graph facts: the acceptance verdict, and the
records human actions already leave. What the graph cannot see is listed, not guessed.

## Why (context)

P19's exit is *"20 consecutive NYSE sessions, with no human command except reading; G1 and G3
measured by code, not asserted"*. Nothing measures either today. E19.1 (S234) now briefs the operator
every run, and the etalon bar is *"trades unattended for a sustained stretch… operator out of the
loop"*. Without a count, "unattended" is a feeling.

### Measured, 2026-09-27 — read these before designing

From the planner's session on `main` @ `4cd87b73` against the live spine. **Not reproducible in your
worktree** (no `.env`); your proofs are in-memory fixtures.

| # | Claim | Value | How it was measured |
| --- | --- | --- | --- |
| 1 | PRD §10 | **G1** *"≥95% of scheduled cycles complete without silent failure over a rolling 30 days"*; **G3** *"after stabilization, intervention needed on fewer than 20% of healthy trading days"* | *[measured]* `docs/PRD.md:375–377` |
| 2 | The per-run verdict | `accept_run(graph, run_id).verdict` ∈ `PASS`, `NO_TRADE`, `UNPROVEN`, `FAIL`; `.passed` is true for all but `FAIL` | *[measured]* `orchestration/packs/trading_acceptance.py:33–72` |
| 3 | 🪤 **It is slow** | **2.94 s per run** (20 runs: 58.7 s); a dashboard refresh cannot re-derive a 30-day window | *[measured]* timed on the live spine |
| 4 | A stored verdict exists from S234 on | once a brief is **sent**, the dispatcher writes `brief_verdict` (`accept_run`'s word, or `NOT_FINISHED` when no Snapshot existed by the 23:50 UTC last fire), `brief_sent_at`, `brief_message_id` on the `RunRequest`. A failed send writes none | *[measured]* `orchestration/daily_brief.py:33–72`; first real brief owed `sched-2026-09-28` |
| 5 | Human actions the graph records | `CommandAudit` **33** (actor `operator` 30 / `cli` 3; channel `dashboard`; linked to an `Intent` by `RESULTED_IN`); `RunRequest` **77**: `sched` 57, `check` 9, `verify` 7, `confirm` 2, `manual` 1, `probe` 1, and **1** with `resume_from`; `DeployRecord` **68** (`deployed_at`, `actor`); `Escalation` **24** (all created 2026-09-24, `status=open`); `RunHoldAnswer` **0** | *[measured]* `list_nodes` per label |
| 6 | Which intents change state | `IntentFamily`: `status`, `explain` read; `approve`, `reject`, `modify`, `run`, `mode`, `stage`, `pause`, `resume` act. Live `Intent` families: resume 7, explain 6, status 5, approve 5 | *[measured]* `contracts/operator.py:15`; live counts |
| 7 | Not human | `FlagResolution` **102**, of which 94 are `resolved_by=run-start-reconciliation` (automatic) | *[measured]* |
| 8 | 🪤 **Naive timestamps** | `RunRequest.requested_at` carries **no UTC offset** (all 20 in the window); `CommandAudit`, `DeployRecord`, `Escalation` carry one | *[measured]* comparing them raised `TypeError` until normalised |
| 9 | **Baseline, 20 sessions 2026-08-28 → 2026-09-25** (the definitions in Scope) | **G1 = 14 / 20 = 70.0 %** (six `FAIL`: 08-28, 09-08 to 09-11, 09-15: the referee never ran, or the only order went unfilled). **G3 = 4 of 14 healthy sessions** had an operational action (28.6 %): verify runs on 09-04 and 09-16, a manual run + resume + approve on 09-24, and **24 escalations** on 09-25. **11 of 14** counting deploys. Both clocks: **0** | *[measured]* a planner scratch script, `accept_run` per session |
| 10 | Actions the graph does **not** see | planner broker probes and cancels (Alpaca, not the graph), Azure changes other than deploys (e.g. the forced master replica of 2026-09-26), direct graph repairs by scripts (`FaultResolution` `resolved_by` a sweep script, 3 nodes) | *[measured]* 2026-09-26 STATE entries; `FaultResolution` props |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (A1, A3, A6 below). Watch them fail on `main`. Paste the red output.
2. **The window.** The sessions (`ProviderTradingCalendar`) in the last `scorecard_window_days` (**30**)
   calendar days whose dispatcher window has **closed** (23:50 UTC on that date has passed). A session
   still in its window is not yet counted.
3. **One verdict per session, never recomputed by the scorecard.** Read `RunRequest` `sched-<date>`:
   - it has `brief_verdict` → use that word;
   - it has none → `accept_run(graph, run_id).verdict`, **memoised per run id for the process**, so no
     run is judged twice (row 3);
   - there is no `RunRequest` → `MISSED`.
   **Complete** means `PASS` or `NO_TRADE`. `UNPROVEN`, `FAIL`, `NOT_FINISHED` and `MISSED` are not.
   **G1** = complete / counted sessions.
4. **Human actions, by kind, each with the timestamp it carries** (naive ones read as UTC, row 8):
   - `command`: a `CommandAudit` whose `Intent` family acts (row 6), or with no `Intent` at all (an
     attempted command, e.g. `needs_clarification`). A `status`/`explain` intent is **reading** and
     never counts;
   - `run`: a `RunRequest` whose `run_id` does not start with `sched-` (`requested_at`);
   - `resume`: a `RunRequest` with `resume_from` (`resumed_at`);
   - `hold_answer`: a `RunHoldAnswer`;
   - `escalation`: an `Escalation` (`created_at`), because it is a request for a human;
   - `deploy`: a `DeployRecord` (`deployed_at`). **Reported, but it is a change, not an operational
     intervention.**
5. **Attribution.** An action belongs to the first counted session whose scheduled placement
   (`RunRequest.requested_at`, or 22:30 UTC on that date if there is none) comes **after** it, and not
   before the previous session's placement. So a weekend action counts against Monday's run.
6. **What it reports.**
   - **G1** (complete / counted) against `scorecard_g1_target` (**0.95**).
   - **G3** = healthy (complete) sessions with any action other than `deploy`, over healthy sessions,
     against `scorecard_g3_target` (**0.20**). The same share counting deploys, shown beside it.
   - **Two clocks**, both counted back from the latest counted session and stopped by the first that
     fails: **unattended** (complete, and no action other than `deploy`) and **untouched** (complete,
     and no action at all). P19's written exit (*"no human command except reading"*) is the
     **untouched** clock; the operator may later accept **unattended**. The scorecard shows both and
     picks neither. Target `scorecard_clock_sessions` (**20**).
   - **Per session**: date, verdict, action kinds and counts.
   - **Blind spots**: a fixed list naming the action kinds the graph does not record (row 10).
7. **`SRF-OUT-08`** (the law cycle). Suggested wording, adjust to the book's voice: *"The unattended
   vital and the `scorecard` answer report G1, G3 and the two clocks over the configured window from
   graph facts only: each session's verdict is the acceptance gate's (stored `brief_verdict`, else
   `accept_run`), a reading intent is never counted as an intervention, and the kinds the graph cannot
   see are listed. They make no model call and no agent request."*
8. **The vital.** One glance tile in the status line: for example `unattended 0 of 20 sessions ·
   cycles 70 % · hands-on 4 of 14 days`. Tone: **red** when G1 is below target, **amber** when G3 is at or
   above target, **green** otherwise. The detail lists the sessions and the blind spots. No sprint, DL
   or law ids in the text (`SRF-OUT-05`). A window with no counted session reads unavailable and shows
   no number.
9. **The answer.** An MCP tool `scorecard` (registered like `performance`) returning the numbers and
   one sentence; a chat quick tool `"running unattended"` → `scorecard`, answered from the graph with
   no model call.
10. **The tunables** (`scorecard_window_days` 30, `scorecard_g1_target` 0.95, `scorecard_g3_target`
    0.20, `scorecard_clock_sessions` 20), each with a `why` citing PRD §10 or the P19 exit, bounds, and
    a `PARAM` row. `surfaces/dashboard/settings.py` is **176** lines: move them into a new settings
    module rather than grow it.
11. **The design decisions** go to `docs/design-log.md` as **DL-235** before implementation.

### Out of scope (do NOT build this sprint)

- **Two-way commands (E19.2).** When they land they write `CommandAudit` rows, which this scorecard
  already counts.
- **Recording the blind spots** (broker probes, Azure changes). The process freeze forbids a new
  tracking surface unless a defect reached the broker or the fleet. Name them, do not build them.
- **Storing a scorecard** in the graph, or a new label or property. It is computed on read.
- **Changing the acceptance verdict, the brief, or any agent.** Read only.
- **Adding the scorecard to the Telegram brief.** A later decision.
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Re-derive every verdict on every refresh.** Rejected: 2.94 s per run (row 3).
- **A verdict of its own** (e.g. "a Snapshot exists"). Rejected: two definitions of "complete" is
  DL-208's contradiction again; the acceptance gate owns it.
- **Treat `UNPROVEN` as complete** (`.passed` does). Rejected for an autonomy claim: a run whose
  decision is still undecided has not completed. Shown, not counted.
- **Count deploys as interventions in G3.** Rejected as the single number: P17 and P20 deploy by
  design, and G3 is about the run needing a human. Shown beside it, and the **untouched** clock counts
  them.
- **Pick one clock for P19.** Rejected: whether a deploy breaks *"unattended"* is the operator's
  reading of the etalon bar, not a technical choice. Both are shown.
- **Attribute actions by Melbourne calendar day.** Rejected: runs are at 22:30 UTC, so a Melbourne day
  splits one operating cycle; the placement-to-placement window follows the run.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` as DL-235, with their rejected alternatives, BEFORE implementing.**

1. **Where the memo lives** and how long it holds (per process is enough: a past run's `accept_run` word
   only changes when late evidence lands, and `brief_verdict` replaces it from S234 on).
2. **Module boundaries**: the query (sessions, verdicts, actions, attribution, clocks) versus its text,
   versus the vital projection, versus the tool, each under 200 lines.
3. **How the verdict function is injected** so tests can supply verdicts without building a full run
   chain, while production is provably `accept_run` (A2).
4. **The unavailable case**: no counted session, or the graph read fails.

🪤 **DL-235 is yours; DL-234 is S235's**, built in parallel. Re-check both at handback.

---

## Blast radius — measured 2026-09-27

| What | Detail |
| --- | --- |
| Files changed | **new** `surfaces/queries/scorecard*.py`, **new** `surfaces/scorecard_tool.py`, **new** projection and settings modules, `surfaces/dashboard/projections_vitals.py` (133), `surfaces/mcp_tools.py` (150), `surfaces/dashboard/chat.py` (141), `surfaces/dashboard/static/index.html` (148) plus a **new** `static/*.js`; `surfaces/laws/laws.md`, `surfaces/laws/test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`; tests under `surfaces/tests/` |
| Agents affected | none. `surfaces` reads the graph; no agent imports it |
| Contract change? | no. A new **guarantee** (the law cycle above) |
| Graph vocabulary change? | no. Read only |
| New env keys / tunables | four dashboard tunables (Scope 10), all with code defaults, none injected by the deploy |
| Deploy implication | **none.** `surfaces/` ships in no image; the operator's dashboard picks it up on restart |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record DL-235.**
3. **Plant the failing tests first** (A1, A3, A6) and watch them fail on `main`. Paste the red output.
4. **Implement.**
5. **Law cycle**: `SRF-TRG-02`, `SRF-OUT-08`, `PARAM` rows, v1.2 and Changelog, test-plan rows,
   docstring citations, rollups in the ledger and `docs/laws/INDEX.md`, drift row if owed.
6. **Prove the guards can fail (DL-70)**: count a `status` intent (A3 red); count `UNPROVEN` as
   complete (A1 red); drop the memo (A5 red); compare a naive timestamp without normalising (A7 red).
   Restore each.
7. **`make ci` green** — every step, **redirected to a file, never piped**.
8. **Fill the handback sections.**

---

## Test plan

Fixtures are an `InMemoryGraphStore` with `RunRequest`, `CommandAudit` → `Intent`, `DeployRecord`,
`Escalation` and `RunHoldAnswer` nodes, and an injected verdict function, except in A2.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 G1 counts only complete sessions | five sessions: `PASS`, `NO_TRADE`, `UNPROVEN`, `FAIL`, no `RunRequest` | G1 = 2 / 5; the last reads `MISSED`; the per-session rows carry each verdict (`SRF-OUT-08`) |
| A2 | 🎯 the verdict is the acceptance gate's | — | production resolves to `orchestration.packs.trading_acceptance.accept_run` (identity); a stored `brief_verdict` is used as written, and `accept_run` is not called for that run |
| A3 | 🎯 reading is never an intervention | a healthy session with a `status` and an `explain` intent only | G3 counts it as untouched; both clocks continue through it |
| A4 | every acting kind counts | one healthy session each with: an `approve` intent, a command with no intent, a `manual-` run, a resume, a hold answer, an escalation | each session counts toward G3, with its kind named |
| A5 | 🪤 no run is judged twice | two reads of the same window | the verdict function is called once per run without `brief_verdict`, never for runs with one |
| A6 | 🎯 attribution follows the run | an action at Saturday 03:00 UTC; Friday's and Monday's placements at 22:30 UTC | the action belongs to Monday's session, not Friday's |
| A7 | 🪤 naive timestamps read as UTC | a `RunRequest.requested_at` with no offset beside an aware `CommandAudit.created_at` | no `TypeError`; the attribution is correct |
| A8 | the two clocks | latest three sessions: complete and untouched; complete with a deploy; complete with an escalation | untouched clock 1, unattended clock 2; both stop at the escalation |
| A9 | the window | a session inside its dispatcher window (before 23:50 UTC); one 31 days back | neither is counted |
| A10 | the vital's tone and text | G1 below target; G1 met with G3 at target; both met | red, amber, green; the text carries no `S2`, `DL-`, `DRIFT-` or clause id (`SRF-OUT-05`); an empty window reads unavailable with no number |
| A11 | the tool and the chat | the MCP `scorecard` call and the chat's `"running unattended"` | the same numbers from both; no model call (assert the LLM port is untouched, as S228's A8 does) |
| A12 | the blind spots are listed | — | the answer names broker actions, Azure changes other than deploys, and script repairs as not counted |

---

## Success factors

- [ ] G1, G3 (and G3 with deploys), and both clocks are computed from graph facts only, with each
      session's verdict taken from the acceptance gate (A1, A2), reading never counted (A3).
- [ ] A dashboard refresh judges no run twice (A5).
- [ ] The vital, the MCP tool and the chat give the same numbers, with no model call (A10, A11).
- [ ] The surfaces law book is v1.2 with `SRF-OUT-08`, the tool in `SRF-TRG-02`, four `PARAM` rows,
      test-plan rows, and both rollups updated.
- [ ] DL-235 recorded with rejected alternatives.
- [ ] Every guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **`.passed` is not "complete".** It is true for `UNPROVEN`. Use the verdict word.
🪤 **A failed brief writes no `brief_verdict`.** The fallback to `accept_run` is not only for history.
🪤 **`RunRequest.requested_at` is naive** (row 8); every other action timestamp is aware. Normalise once.
🪤 **A command with no `Intent`** (e.g. `needs_clarification`) is still a human trying to act. It counts.
🪤 **The escalations of 2026-09-24 are open.** Count them on the session they were created for, once;
their status does not matter to G3.
🪤 **`settings.py` is 176 lines.** Four tunables with bounds and `why` push it over 200.
🪤 **Do not make the vital read the selected run.** The scorecard is a window, not a run; the selected
run does not scope it (say so in `SRF-OUT-08`, so `SRF-OUT-01` is not read as covering it).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `surfaces/dashboard/settings.py` **176**, `surfaces/mcp_tools.py` **150**,
  `surfaces/dashboard/chat.py` **141**, `surfaces/dashboard/projections_vitals.py` **133**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds, and a `PARAM` row each.
- Faults, not silent failure: an unreadable graph shows the vital as unavailable, never as zero.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump of the kind named at the top. **Cloud:** try `uv lock`; if it cannot reach
  `download.pytorch.org`, leave `uv.lock` untouched and say so in the handback. The planner re-locks.
- Secrets never through the worktree. **State which tree you ran in.**

---

## Sequencing after merge

1. **Cloud session:** `make ci` green in the session (redirected to a file), branch pushed. **Owed to
   the planner:** `uv lock` if the session could not re-resolve it, then `make ci` on Windows (S232's
   path test passed on Linux and failed on Windows), then **`make gate-ran` exits 0**, run from the
   worktree whose `HEAD` is the commit being proven; check the printed SHA against `git rev-parse HEAD`.
2. Merge to `main` locally and push. Post-merge CodeQL. S235 merges independently; whichever lands
   second re-bumps to the next MINOR.
3. **No deploy.** `surfaces/` ships in no image.
4. **Planner's live check (the functionality check)**, from the main checkout with `.env`: restart the
   dashboard, read the tile, and call `scorecard` over MCP. **Pass:** the numbers equal the planner's
   independent recomputation (the scratch script behind row 9) for the same window; the first refresh
   is slow only for runs without `brief_verdict`, and the second refresh judges none; the chat's
   `"running unattended"` gives the same sentence. Record it in
   `docs/laws/functionality-checks.md`. From `sched-2026-09-28` on, `brief_verdict` should back each
   new session.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 236 — the dashboard says how long the pack has run without a human, from the graph alone
(P19 E19.3). Spec: docs/sprints/sprint-236-the-dashboard-says-how-long-it-ran-without-a-human.md
on main (read all of it). Repo: yury-gurevich/trading-agents.

Branch: sprint-236-the-dashboard-says-how-long-it-ran-without-a-human, cut from main. Never main.
You have NO .env, NO gh and no route to download.pytorch.org. Proofs are InMemoryGraphStore fixtures.
Codex builds S235 at the same time in scripts/; you share no file. You take DL-235; DL-234 is S235's.
You cannot run `make gate-ran`: that is owed to the planner. If `uv lock` cannot re-resolve after the
version bump, leave uv.lock untouched and say exactly that. A run result read through the GitHub
connector is an observation, never GATE PROVEN.

Why: P19's exit is 20 consecutive sessions with no human command except reading, with PRD G1 (>=95 %
of scheduled cycles complete, rolling 30 days) and G3 (intervention on <20 % of healthy days)
measured by code. Nothing measures them today. Measured baseline (20 sessions to 2026-09-25): G1 70 %,
G3 4 of 14 (11 of 14 counting deploys), both clocks 0.

MUST RULE before any code: read surfaces/laws/laws.md + test-plan.md (LOCKED v1.1), the operator laws
for IntentFamily, docs/laws/conventions.md, docs/laws/drift-register.md, CLAUDE.md. Fill the Law
reading record first. Law-cycle answer: YES (new guarantee, no contract): SRF-TRG-02 gains
`scorecard`, new SRF-OUT-08, four PARAM rows, v1.2 + Changelog, test-plan rows, rollups in
docs/laws/ledger.md AND docs/laws/INDEX.md (make ci recomputes them), drift row if owed.

Build:
1. Red first: A1 (G1 counts only PASS/NO_TRADE; UNPROVEN, FAIL, NOT_FINISHED, MISSED do not), A3 (a
   status/explain intent is never an intervention), A6 (a weekend action belongs to Monday's run).
2. Window: ProviderTradingCalendar sessions in the last scorecard_window_days (30) whose dispatcher
   window closed (23:50 UTC that date).
3. Verdict per session: RunRequest `sched-<date>`.brief_verdict if present; else accept_run(...)
   .verdict MEMOISED per run id (it costs 2.94 s per run); no RunRequest -> MISSED. Never a verdict
   rule of your own.
4. Actions: CommandAudit whose Intent (RESULTED_IN) family acts, or with no Intent; non-`sched-`
   RunRequests; RunRequests with resume_from; RunHoldAnswer; Escalation; DeployRecord (reported as a
   change, not an operational intervention). status/explain = reading, never counted.
   RunRequest.requested_at is NAIVE: read it as UTC.
5. Attribution: an action belongs to the first counted session whose placement (requested_at, else
   22:30 UTC that date) comes after it.
6. Report G1, G3 (healthy sessions with a non-deploy action / healthy sessions) and G3 counting
   deploys; the `unattended` clock (complete, no non-deploy action) and the `untouched` clock
   (complete, no action at all), both counted back from the latest session; per-session rows; the
   blind spots (broker actions, Azure changes other than deploys, script repairs).
7. Vital tile (red: G1 below target; amber: G3 at/above target; green otherwise; empty window ->
   unavailable, no number; no sprint/DL/law ids in text). MCP tool `scorecard`; chat quick tool
   "running unattended" -> scorecard. No model call anywhere.
8. Tunables scorecard_window_days 30, scorecard_g1_target 0.95, scorecard_g3_target 0.20,
   scorecard_clock_sessions 20, in a NEW settings module (settings.py is 176 lines).

Order: DL-235 (re-check the number) -> red A1/A3/A6 -> implement -> law cycle -> DL-70 plants (count
a status intent; count UNPROVEN as complete; drop the memo; compare a naive timestamp raw — each must
go red; restore) -> make ci redirected to a file, exit 0, 100.00 %.

DO NOT:
- recompute or reinterpret a verdict; use `.passed` as "complete" (it is true for UNPROVEN).
- judge a run twice per process, or call accept_run for a run that carries brief_verdict.
- let the selected run scope the scorecard (it is a window, not a run).
- add a graph label, property, stored scorecard, or anything that records the blind spots.
- change the brief, the acceptance gate, any agent, contracts/ or kernel/.
- grow settings.py (176), mcp_tools.py (150), chat.py (141) or projections_vitals.py (133) past 200.
- claim a live proof or GATE PROVEN: the live read and the gate are the planner's after push.
- pin a version: MINOR, next available at merge; uv.lock as above.

Handback: Law reading record, Test plan results, Closeout (red then green, DL-70 plants, line counts,
make ci file + exit code, how uv.lock was touched), Return notes. Status: BUILT, and this sprint's
README.md row leads with BUILT in the same commit. Commit on the branch and PUSH it, then stop: no
merge. Name what is owed (uv lock if not re-resolved, make gate-ran, Windows make ci). Anything not
met: "not done".
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

*Filled 2026-09-27 before the first code change, in the cloud checkout `/home/user/trading-agents` on
branch `sprint-236-the-dashboard-says-how-long-it-ran-without-a-human`, cut from `main` @ `8d4eb09c`,
no `.env`. Read whole: `surfaces/laws/laws.md` and `test-plan.md` (v1.1), `agents/operator/laws/laws.md`
(v1.3), `docs/laws/conventions.md`, `docs/laws/drift-register.md`, `CLAUDE.md`; read for the clauses
named: `orchestration/laws/dispatcher/laws.md` (v1.1).*

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| new `surfaces/queries/scorecard*.py` (window, verdicts, human actions, attribution, clocks, text) | surfaces book + test-plan; operator book; dispatcher book; conventions; drift register | `SRF-IDN-01`, `SRF-IDN-02` (read-only), `SRF-DEP-01`, new `SRF-OUT-08`; `OPR-OUT-06`, `OPR-OUT-07`, `OPR-TYP-02`, `OPR-IDN-02`; `DSP-IDM-03` | **Yes, twice.** (1) `OPR-OUT-06` writes a `CommandAudit` for every `explain` call, not only every `interpret`, and an explain writes no `Intent` (`outcome="explain"`, `agents/operator/agent.py:111-119`). Scope 4's "a `CommandAudit` … with no `Intent` at all" would count every *Explain this run* press as an intervention, which A3 forbids; an explain-capability audit is reading and is never counted. (2) `DSP-IDM-03` names the property and its words (`brief_verdict`: `accept_run`'s word, or `NOT_FINISHED`); A2 writes it through the dispatcher's own brief path, not by hand, so a renamed property fails the proof. |
| new `surfaces/dashboard/projections_scorecard.py`; `surfaces/dashboard/app.py` (one GET route); `static/index.html` (148); new `static/scorecard.js`; `static/app.css` | surfaces book + test-plan | `SRF-OUT-01`, `SRF-OUT-05`, `SRF-OUT-06`, `SRF-OUT-07` (the pattern copied), `SRF-TRG-01`, `SRF-TYP-02`, `SRF-FAIL-01`, `SRF-NEV-02` | **Yes.** `SRF-OUT-01` scopes contextual panels to the selected run; the scorecard is a window, so it gets its own `GET /api/scorecard`, which takes no run parameter, and its script never listens for a run selection: the selected run *cannot* scope it, and `SRF-OUT-08` says so. It stays out of `/api/vitals` because its first read judges every unbriefed run (2.94 s each, row 3) and would hold every other vital behind it. `SRF-FAIL-01`'s shape (degrade, stay HTTP 200, say so) gives the unreadable case: unavailable, no number. |
| `surfaces/mcp_tools.py` (150), `surfaces/mcp_server.py`, new `surfaces/scorecard_tool.py` | surfaces book + test-plan | `SRF-TRG-02`, `SRF-IN-04`, `SRF-NEV-03`, `SRF-TYP-01`, `SRF-FAIL-02`, `SRF-SEC-02` | Yes: `SRF-TRG-02` fixes the catalogue at six tools, so a seventh needs the amendment. DL-225's trap (`test_entry_imports.py`) forbids the tool importing anything under `surfaces.dashboard`, whose package init loads the chat and so `mcp_tools` half-built. |
| `surfaces/dashboard/chat.py` (141) `_QUICK_TOOLS` | surfaces book + test-plan | `SRF-OUT-03`, `SRF-OUT-06`, `SRF-IN-03`, `SRF-TYP-01` | Yes, a silence (below): the quick ask calls the tool with no run argument and no model. |
| new `surfaces/scorecard_settings.py`; `surfaces/dashboard/settings.py` (176) | `SRF-PARAM`; conventions; `scripts/param_law_sync_sources.py` (read only: S235 owns `scripts/`) | every `DashboardSettings` field has exactly one `PARAM` row, gate-enforced | **Yes.** The gate reads `DashboardSettings` alone and the MCP tool may not import `surfaces.dashboard`, so the four tunables live in a `ScorecardSettings` outside the dashboard package and `DashboardSettings` inherits from it: each `PARAM` row still meets its field, and the tile and the tool read one declaration. `dispatcher_fire_utc` moves into the same class for the same reason (the scorecard places a session at that tick); its row, its environment name and its readers do not change. |
| `orchestration/packs/trading_acceptance.py` `accept_run` (read only) | `docs/laws/ledger.md` Layer 3; DL-59 | the one per-run verdict (`PASS`, `NO_TRADE`, `UNPROVEN`, `FAIL`); `.passed` is true for all but `FAIL` | No: "complete" is the word (`PASS`, `NO_TRADE`), never `.passed`. |
| `orchestration/daily_brief.py` (read only) | dispatcher book v1.1 | `DSP-IDM-03`, `DSP-OUT-06`, `DSP-TRG-03` | **A finding, no change:** the brief goes once the Snapshot exists (~22:40 UTC), before the next open, so a run that submitted orders is briefed `UNPROVEN` and, one brief per run, keeps that word. By Scope 3 such a session never counts complete. The scorecard reads it as written; DL-235 and the return notes carry it. |
| `orchestration/scheduled_dispatch.py` `ProviderTradingCalendar` (read only) | none governs it | none | **Yes, asked and decided by the operator:** every `RunRequest` writer stores `requested_at` as a bare date (`orchestration/start.py:87`, `as_of.isoformat()`), not the naive 22:30 timestamp the A6/A7 fixtures model. Read literally as UTC it is midnight, 22.5 h before the run. The operator chose (2026-09-27) that a bare date reads as the dispatcher's placing tick, 22:30 UTC, on that date: DL-235 decision 5. |
| `contracts/operator.py` `IntentFamily` (read only) | operator book v1.3 | `OPR-TYP-02`, `OPR-NEV-01`, `OPR-OUT-06`, `OPR-OUT-07` | Yes: reading is `status` and `explain`; every other family acts, including one the contract may add later (the safe side for an autonomy claim), and a test pins the two reading words to the contract's literal. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **Yes: a new
guarantee, no `contracts/` change** (the spec's answer, confirmed by reading). The surfaces book goes to
**v1.2**: `SRF-TRG-02` lists `scorecard`; new `SRF-OUT-08`; four `PARAM` rows (and the
`dispatcher_fire_utc` row names its second reader); a Changelog line; test-plan rows for both clauses;
the rollups in `docs/laws/ledger.md` and `docs/laws/INDEX.md`; **DRIFT-078** for the silence below.

**Contradictions found between a law and this spec:** none that stop the build. Two were resolved on
the spec's own stated intent: (1) Scope 4's "a `CommandAudit` with no `Intent` counts" against
`OPR-OUT-06` (explain calls write one too), read as "an interpret call that produced no `Intent`",
because A3 and Scope 4's next sentence say reading never counts; (2) `SRF-TRG-02`'s six tools against
Scope 9's seventh, resolved by the amendment the spec asks for.

**Laws found silent where a decision was needed:** (1) `SRF-OUT-03` says dashboard chat answers are
grounded in the selected run and record `CommandAudit`, `LLMCall` and `Intent` facts. The deterministic
quick asks (`status`, `incidents`, `performance` since S228) already do neither, and `scorecard` joins
them by design. S228 noted the silence without a register row; this sprint files **DRIFT-078** (forced
decision: narrow `SRF-OUT-03` to operator-mediated answers, or audit the quick asks) and `SRF-OUT-08`
states the scorecard's own behaviour. (2) No law says what instant a `RunRequest`'s `requested_at`
holds; the operator decided how the scorecard reads a bare date (above).

**Clauses that were ⬜ and are now proven:** none of the clauses relied on is ⬜. `SRF-PERF-02` (⬜,
projection reads bounded by timeout and cache settings) is neither relied on nor proven: the
scorecard's read is bounded by `scorecard_window_days` and the per-process memo, not by a timeout. To
be added and proven: `SRF-OUT-08`; `SRF-TRG-02` stays 🟩 with the scorecard tests in its row.
*At handback:* done. `SRF-OUT-08` is 🟩 on 18 cited tests, `SRF-TRG-02` stays 🟩 with the A11 test
added, and the gate derives 29 / 36.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_g1_counts_only_complete_sessions` (six sessions: the table's five plus the handover's `NOT_FINISHED`, so G1 = 2 / 6) | `surfaces/tests/test_scorecard_g1_g3.py` | 🟩 red first on `main`; guard planted | `SRF-OUT-08` |
| A2 | `test_a2_production_judges_with_accept_run_itself`; `test_a2_the_tile_and_the_tool_share_the_process_memo`; `test_a2_a_stored_brief_verdict_is_used_as_written` (the word written by the dispatcher's own brief path, S234's fixtures) | `surfaces/tests/test_scorecard_verdicts.py` | 🟩 | `SRF-OUT-08`, `DSP-IDM-03` |
| A3 | `test_a3_reading_is_never_an_intervention` (a `status` intent, an `explain` intent and an explain call's Intent-less audit) | `surfaces/tests/test_scorecard_g1_g3.py` | 🟩 red first on `main`; guard planted | `SRF-OUT-08`, `OPR-OUT-06` |
| A4 | `test_a4_every_acting_kind_counts` (approve, a refused command with no Intent, a `manual-` run, a resume, a hold answer at 22:40 UTC, an escalation) | `surfaces/tests/test_scorecard_g1_g3.py` | 🟩 guard planted (hold answer by its run) | `SRF-OUT-08` |
| A5 | `test_a5_no_run_is_judged_twice` | `surfaces/tests/test_scorecard_verdicts.py` | 🟩 guard planted | `SRF-OUT-08` |
| A6 | `test_a6_a_weekend_action_belongs_to_mondays_run` | `surfaces/tests/test_scorecard_attribution.py` | 🟩 red first on `main` | `SRF-OUT-08` |
| A7 | `test_a7_naive_timestamps_read_as_utc` (naive `requested_at` beside `+10:00` command times) | `surfaces/tests/test_scorecard_attribution.py` | 🟩 guard planted | `SRF-OUT-08` |
| A8 | `test_a8_a_deploy_stops_one_clock_and_an_escalation_both` | `surfaces/tests/test_scorecard_attribution.py` | 🟩 | `SRF-OUT-08` |
| A9 | `test_a9_open_and_old_sessions_are_not_counted` | `surfaces/tests/test_scorecard_attribution.py` | 🟩 | `SRF-OUT-08` |
| A10 | `test_a10_the_tile_is_red_amber_or_green_in_plain_words` (three cases); `test_a10_an_empty_window_reads_unavailable_and_shows_no_number` | `surfaces/tests/test_scorecard_tile.py` | 🟩 | `SRF-OUT-08`, `SRF-OUT-05` |
| A11 | `test_a11_mcp_chat_and_tile_give_one_answer_with_no_model_call` (two different selected runs, one answer; the bus refuses every call) | `surfaces/tests/test_scorecard_chat.py` | 🟩 | `SRF-OUT-08`, `SRF-TRG-02` |
| A12 | `test_a12_every_answer_names_what_the_graph_cannot_see` | `surfaces/tests/test_scorecard_tile.py` | 🟩 | `SRF-OUT-08` |

**Tests added beyond the plan:** 31 more test cases in the same six new files. The ones that guard a
decision: `test_every_intent_family_but_reading_acts` (ten cases, one per `IntentFamily` literal, so a
family the contract adds later acts until decided otherwise); `test_the_operators_own_reading_records_are_never_actions`
(the real `OperatorAgent` writes an explain call, a typed explain command and a pause: four audits,
one counted; guard planted); `test_a6_a_bare_date_is_placed_at_the_placing_tick` (the operator's 22:30
decision; guard planted); `test_the_default_window_is_row_nines_twenty_sessions` (from 2026-09-27 the
window is 2026-08-28 → 2026-09-25, twenty sessions). The rest cover the edges: an empty stored word falls
back to the gate; a judge that raises is asked again; actions at the window's opening or after its last
placement count nowhere; a resume is one resume, never also a run; an unreadable time or placement stops
the count (four cases); an empty window, an unreadable graph (no store text leaks) and a record with no
readable time all read unavailable; no healthy session gives no hands-on share; sessions list newest
first; the four goals are the PRD's and `DashboardSettings` inherits them; the tool's empty and
unplaceable answers are plain words; the quick ask, the slot and a script that never listens for a run
selection; the route ignores any run parameter and refuses POST; the tool's clock is aware UTC.
Changed: `test_mcp_server.py::test_error_paths_and_tool_catalog` (the catalogue gains `scorecard`) and
`test_dashboard_jargon.py::test_api_display_strings_contain_no_internal_identifiers` (adds
`/api/scorecard`).

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** the claude.ai cloud checkout `/home/user/trading-agents`,
branch `sprint-236-the-dashboard-says-how-long-it-ran-without-a-human` cut from `main` @ `8d4eb09c`.
**No `.env`, no `gh`.** Dependencies from `uv sync --frozen` (the dev group, no extras). Every proof is
an `InMemoryGraphStore` fixture; nothing was read on the live spine.

**Result:** on in-memory graphs, `GET /api/scorecard` (the tile), the MCP `scorecard` tool and the
chat's *Running unattended* give one answer from graph facts: G1 (complete over counted sessions, the
last 30 days of closed sessions), G3 and G3 counting deploys, and the *unattended* and *untouched*
clocks, with each session's verdict the acceptance gate's (the stored `brief_verdict`, else
`accept_run` judged once per process, else `MISSED`), reading never counted, the three blind spots
listed, and no model call or agent request. The selected run cannot scope it (the route takes no run).
An empty window, an unreadable graph or an unplaceable record shows no number. The surfaces book is
LOCKED **v1.2** with `SRF-OUT-08` 🟩, and both rollups read **29 / 36** (derived by the gate).

**Files changed:** new `surfaces/queries/scorecard.py`, `scorecard_model.py`, `scorecard_actions.py`,
`scorecard_verdicts.py`, `scorecard_text.py`, `surfaces/scorecard_settings.py`,
`surfaces/scorecard_tool.py`, `surfaces/dashboard/projections_scorecard.py`,
`surfaces/dashboard/static/scorecard.js`; changed `surfaces/dashboard/settings.py` (inherits
`ScorecardSettings`; `dispatcher_fire_utc` moved into it), `app.py` (one GET route), `chat.py` (the
quick ask), `surfaces/mcp_tools.py`, `surfaces/mcp_server.py`, `static/index.html`, `static/app.css`;
tests: six new `surfaces/tests/test_scorecard_*.py`, new `scorecard_fixtures.py`, and
`test_mcp_server.py`, `test_dashboard_jargon.py` (one line each); laws and docs:
`surfaces/laws/laws.md`, `surfaces/laws/test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`,
`docs/laws/drift-register.md` (DRIFT-078), `docs/design-log.md` (DL-235), this spec,
`docs/sprints/README.md`, `pyproject.toml` (`0.114.01` → `0.115.00`). `uv.lock` untouched.

**Design decisions:** [DL-235](../design-log.md): the process memo; module boundaries and the tile's own
route; the verdict injected through the memo; the unavailable case; **the operator's decision** that a
bare-date `requested_at` is placed at 22:30 UTC; an explain call is reading; one kind per record and a
hold answer on the run it names; the window; what the operator reads. Each decision carries its
rejected alternatives; the known limits close the entry.

**Proof — the red run first:**

```text
$ uv run --frozen pytest --no-cov -q surfaces/tests/test_scorecard_g1_g3.py \
      surfaces/tests/test_scorecard_attribution.py   # main @ 8d4eb09c plus only the new tests; exit 2
ERROR collecting surfaces/tests/test_scorecard_g1_g3.py
surfaces/tests/test_scorecard_g1_g3.py:16: in <module>
    from surfaces.queries.scorecard import scorecard
E   ModuleNotFoundError: No module named 'surfaces.queries.scorecard'
ERROR collecting surfaces/tests/test_scorecard_attribution.py
surfaces/tests/test_scorecard_attribution.py:13: in <module>
    from surfaces.queries.scorecard import scorecard
E   ModuleNotFoundError: No module named 'surfaces.queries.scorecard'
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
2 errors in 0.72s
```

Committed red as `8e74d2c` before any implementation.

**Proof — the green run:**

```text
surfaces/tests/test_scorecard_g1_g3.py::test_a1_g1_counts_only_complete_sessions PASSED [ 33%]
surfaces/tests/test_scorecard_g1_g3.py::test_a3_reading_is_never_an_intervention PASSED [ 66%]
surfaces/tests/test_scorecard_attribution.py::test_a6_a_weekend_action_belongs_to_mondays_run PASSED [100%]
============================== 3 passed in 0.53s ===============================
$ uv run --frozen pytest --no-cov -q surfaces/tests/test_scorecard_*.py
49 passed in 0.70s
```

**Guards planted:** each planted in production code, the guard run red, then `git checkout` and run
green; the tree was clean after each.

| # | Planted | Guard | Red, as it failed | Restored |
| --- | --- | --- | --- | --- |
| 1 | a `status` intent counts (`READING_FAMILIES` = `{"explain"}`) | A3 | `At index 1 diff: {'command': 1} != {}` | 1 passed |
| 2 | `UNPROVEN` counts as complete (added to `COMPLETE`) | A1 | `('sched-2026-09-22', 'UNPROVEN', True) != ('sched-2026-09-22', 'UNPROVEN', False)` | 1 passed |
| 3 | the memo dropped (`VerdictMemo.word` judges every read) | A5 | `Left contains 3 more items`: each unbriefed run judged twice | 1 passed |
| 4 | a naive time compared raw (`instant` returns it unchanged) | A7 | `TypeError: can't compare offset-naive and offset-aware datetimes` | 1 passed |
| 5 | a bare date read at midnight (decision 5's ruled-out reading) | `test_a6_a_bare_date_is_placed_at_the_placing_tick` | `At index 0 diff: {'run': 1} != {'command': 1, 'run': 1}` | passed |
| 6 | every Intent-less audit counts (Scope 4 read literally) | `test_the_operators_own_reading_records_are_never_actions`; A3 | `['command', 'command', 'command'] != ['command']`; `{'command': 1} != {}` | passed |
| 7 | a hold answer placed by its time alone | A4 | `('sched-2026-09-24', {}) != ('sched-2026-09-24', {'hold_answer': 1})` | 1 passed |
| 8 | the `scorecard_clock_sessions` `PARAM` row removed | `check_param_law_sync.py` | `[FAIL] surfaces/dashboard/settings.py:1: surfaces.scorecard_clock_sessions settings field has no PARAM row` | exit 0 |

Plants 1–4 are the four the spec names. My first attempt at plant 7 was malformed (a comment swallowed
the call: a `SyntaxError`, not a red); it was redone and failed as shown.

**Module line counts** (total lines, as `check_module_size.py` counts them; `main` in brackets):

| Module | Lines |
| --- | --- |
| `surfaces/queries/scorecard.py` | 108 (new) |
| `surfaces/queries/scorecard_model.py` | 125 (new) |
| `surfaces/queries/scorecard_actions.py` | 129 (new) |
| `surfaces/queries/scorecard_verdicts.py` | 62 (new) |
| `surfaces/queries/scorecard_text.py` | 141 (new) |
| `surfaces/scorecard_settings.py` | 63 (new) |
| `surfaces/scorecard_tool.py` | 68 (new) |
| `surfaces/dashboard/projections_scorecard.py` | 63 (new) |
| `surfaces/dashboard/settings.py` | 174 (176) |
| `surfaces/mcp_tools.py` | 152 (150) |
| `surfaces/mcp_server.py` | 160 (151) |
| `surfaces/dashboard/chat.py` | 146 (141) |
| `surfaces/dashboard/app.py` | 184 (180) |
| `surfaces/dashboard/projections_vitals.py` | 133 (133, untouched) |
| `surfaces/tests/scorecard_fixtures.py` | 198 (new) |
| `surfaces/tests/test_scorecard_g1_g3.py` / `_verdicts` / `_attribution` / `_edges` / `_tile` / `_chat` | 176 / 160 / 130 / 93 / 198 / 184 (new) |

**`make ci`:** `UV_FROZEN=1 make ci > <scratchpad>/make_ci_final.txt 2>&1` (the cloud container's scratchpad, not
persisted), **exit 0**, all 15 steps: ruff clean; format 1,338 files; mypy no issues in 1,053 files;
import-linter 5 kept, 0 broken; module size 0 `[FAIL]` (warnings only); module header; law coverage;
PARAM/settings sync; sprint status; markdown links; version scheme; pytest **3,358 passed, 6 skipped,
100.00 %** (18,802 statements, 4,078 branches, none missed); dependency audit *"No unaccepted
vulnerabilities; 1 accepted advisory re-checked"*; detect-secrets passed; untracked secrets *"no
untracked files to scan"*. `UV_FROZEN=1` because after the bump a plain `uv run` re-locks and fails on
`download.pytorch.org`; frozen, every step runs against the committed lock, as CI's `uv sync --frozen`
does. The first full run failed at detect-secrets on a fake connection string with a user and password
in it, in a test I wrote; the next failed on this handback quoting it. Both were reworded, not
allowlisted. The pinned
markdownlint hook (not a `make ci` step) also passes on every changed document.

**`make gate-ran`:** *(planner, after push)* — **owed.** The cloud container has no `gh`.

**Not met / verified failing:**

- **`make gate-ran`: not done**, owed to the planner (no `gh`).
- **`uv lock`: not done.** It fails reaching `download.pytorch.org` (`tunnel error: unsuccessful`), so
  `uv.lock` is **untouched**: `cmp` against the pre-bump copy is byte-identical, and its own version
  line still reads `0.114.1`. Owed to the planner before merge.
- **`make ci` on Windows: not done**, owed to the planner.
- **The live check: not done** (no `.env`): the tile and the MCP `scorecard` on the live spine, the
  second refresh judging nothing, and the `functionality-checks.md` row. Owed to the planner; the
  comparison with row 9 must use this build's readings (return notes).

## Return notes

- **Placement of a bare date: the operator's decision, and a likely difference from row 9.** Every
  `RunRequest` writer stores `requested_at` as a date (`orchestration/start.py:87`). Asked mid-build,
  the operator chose 22:30 UTC on that date (DL-235 decision 5). Row 9's scratch script probably read
  midnight: it puts 2026-09-24's escalations on 09-25, where this build puts any created before 22:30
  UTC on 09-24. **The planner's live comparison has to recompute with the 22:30 reading**, and with
  decisions 6 and 7 below, before calling a mismatch a defect.
- **An explain call is reading (DL-235 decision 6).** `OPR-OUT-06` writes a `CommandAudit` for every
  `explain`, with no `Intent`; a typed "explain" command writes an explain `Intent` *and then* that second
  audit (`surfaces/operator_tools.py` sends a typed explain to the explain capability). Scope 4 read
  literally counts every one of those audits as an intervention. Row 5/6's live graph holds 33 audits
  and 23 intents, 6 of them explain; by that code path each explain intent left a second, Intent-less
  audit, so the literal rule would charge at least those. *[inferred from the code; not measured live]*
- **A hold answer counts on the run it names (DL-235 decision 7, refined during the build).** The run it
  releases is placed after the answer, which a 22:30 bare-date placement cannot show; by time alone a
  22:40 answer would land on the next session and leave the released run reading unattended. A resume
  keeps the spec's `resumed_at` (its error is the conservative one).
- **Finding, not changed: a briefed run that submitted orders reads `UNPROVEN` for good.** The brief is
  sent once the Snapshot exists (~22:40 UTC), before the next open, and one brief per run
  (`DSP-IDM-03`). By Scope 3 such a session never counts complete, so G1 will stay low on every night
  the pack trades. That is a decision about the verdict's source, outside this sprint.
- **Finding: the window bounds the clocks.** *[measured over 2026–2027 with the provider calendar]* a
  30-day window's 31 dates hold 18–23 sessions and 28 days hold fewer than 20, when the 20-session clock
  cannot reach its target.
- **Record inside the dispatcher window.** A command or an activation escalation made after 22:30 UTC
  for that night's run counts against the next session (DL-235 known limit b2).
- **Where the tile lives.** Its own `GET /api/scorecard`; `/api/vitals` and `projections_vitals.py`
  (listed in the blast radius) are untouched, so the one slow first read never holds the other vitals.
  On a restart the first read judges only unbriefed runs, once; the second judges none.
- **Settings.** `ScorecardSettings` (`surfaces/scorecard_settings.py`) holds the four tunables and
  `dispatcher_fire_utc`, moved from `DashboardSettings`, which now inherits them: same environment names
  (`DASHBOARD_…`), same `PARAM` rows, same readers. The PARAM gate was planted with a missing row and
  failed by name, so it sees the inherited fields.
- **Numbers to re-check at merge.** DL-235 (DL-234 is S235's: both insert at the top of
  `design-log.md`, a trivial conflict for whichever merges second). DRIFT-078 (S235 may file one too).
  Version `0.115.00`: if S235 lands first at `0.115.00`, this re-bumps to `0.116.00`.
- **Read-only books cited.** The scorecard tests cite `OPR-OUT-06`, `OPR-OUT-07`, `OPR-TYP-02` and
  `DSP-IDM-03` because they depend on them; the operator and dispatcher test-plans are unchanged.
- **Left to the planner's pickup:** STATE.md, the work-queue row (83), `docs/sprints/INDEX.md` and the
  next-leg plan still say specced; only this spec and its README row say BUILT.
