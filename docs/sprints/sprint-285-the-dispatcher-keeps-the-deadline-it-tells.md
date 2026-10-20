<!-- Agent: planning | Role: sprint handover -->
# Sprint 285 — The dispatcher keeps the deadline it tells, and places the day's run once

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-285-the-dispatcher-keeps-the-deadline-it-tells`
**Status:** BUILT
**Version:** `0.128.07` (PATCH; main `0.128.06`)
**Effort:** M
**Decisions:** [DL-309](../design-log.md) (decided, seven decisions with the roads not taken) · work-queue 131 parts (b) and (d) · [DL-294](../design-log.md) and [DL-300](../design-log.md) (where they were named and read)

> **Why this bump kind.** No new capability: the dispatcher already promises one placement a day and an answer deadline, and it tells the operator a deadline no fire keeps and can hold a run it already placed. A PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `orchestration/laws/dispatcher/laws.md` | The dispatcher's **locked constitution** | **LOCKED. Read-only during a build**, except Appendix section 2, which you apply exactly. A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `orchestration/laws/dispatcher/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`TRG`** (TRG-01, TRG-02, TRG-03), **`NEV`** (the new NEV-04), **`OBS`** (OBS-02, the new OBS-04), **`IDM`** (IDM-02), **`TYP`** (TYP-01), **`PERF`** (PERF-01), **`OUT`** (OUT-02, OUT-05), **`STA`** (STA-01).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the dispatcher's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes: two new guarantees, no contract change.** The dispatcher now guarantees that a placed run is never held again and that each fire's line says what it did. The cycle is written for you in Appendix section 2: `DSP-NEV-04` and `DSP-OBS-04` new, `DSP-TRG-01`, `DSP-IDM-02`, `DSP-TYP-01` and `DSP-PERF-01` amended in `orchestration/laws/dispatcher/laws.md` (v1.6 → v1.7, a Changelog line), their `test-plan.md` rows naming your tests (`DSP-TYP-01` ⬜ → 🟩), the rollup **43 / 47 → 46 / 49** in both `docs/laws/ledger.md` and `docs/laws/INDEX.md`. Apply it exactly; the gate recomputes the rollup.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/scheduled_dispatch_actions.py` | `orchestration/laws/dispatcher/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `DSP-TRG-01` and `DSP-PERF-01` (the window, now read by the fire's tick, last fire 23:10); `DSP-OBS-02` (the deadline text); `DSP-NEV-04` (the new `already_placed`) |
| `orchestration/scheduled_dispatch_human.py` | same | `DSP-NEV-04`; `DSP-OUT-05` (a degraded notice's retry); `DSP-TRG-02` and `DSP-TRG-03` (the calendar skip and the brief stay before the new return) |
| `orchestration/scheduled_dispatch.py` | same | `DSP-TYP-01` (the result's action space gains `already-placed`) |
| `scripts/dispatch_scheduled_run.py` | same | `DSP-OBS-04` (the line a held result prints) |
| Six existing test files (Appendix section 2) | same | they pinned the 23:20 deadline, the six ticks, or a second `placed`; one pinned a hold after a release that had placed the run |

⚠️ **The brief and the sensor do not move.** Every fire still attempts the day's brief before any return that follows the calendar skip (`DSP-TRG-03`), and the job still runs the sensor after the dispatch (`DSP-TRG-04`). If your change moves `brief_safely`, or touches `orchestration/daily_brief*.py`, `orchestration/container_*.py` or `place_scheduled_run`, stop and report.

---

## Goal

Each dispatcher fire places the day's run at most once and says what it did. Once the day's `RunRequest` exists, a fire reads no readiness, writes no `RunHold`, sends no hold notice and prints `already-placed`; inside the window it still retries a degraded notice that was not sent. The last fire that can place a run is the 23:10 tick, read by the fire's ten-minute tick; the hold notice names 23:10, and a run placed by that fire has 20 minutes before the fleet's window ends at 23:30. A fire outside the window says which side of it the fire is on.

## Why (context)

Work-queue 131 parts (b) and (d). Since the window became 22:30 to 23:30 (DL-294), the dispatcher has told the operator *"Choose Run now by 23:20 UTC"*, but no fire after 23:10 can place a run; a fire after the night's run has been placed re-reads the fleet's readiness, so a failing check at about 23:01 would hold a run that already ran and ask the operator to start it; and every night's job log reads `placed` five times and gives the calendar's reason when the true one is the time of day.

### Measured, 2026-10-20 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| What the job prints a night | **12 fires: 5 `placed` (22:30 to 23:10), 7 `skipped … reason=NYSE trading session`**, on each of 14 run nights | *[measured 2026-10-20]* Log Analytics, `ContainerAppConsoleLogs_CL` of `dispatcher-cron`, 2026-09-30 to 2026-10-19 (OneDrive `trading-agents-data/wq131bd-2026-10-20/measure/dispatch_lines_20d.tsv`) |
| How late a fire is | **12 to 47 seconds** after its tick (168 fires) | *[measured 2026-10-20]* the same rows' times |
| The 23:20 fire places | **never** (14 of 14 nights say `skipped`) | *[measured 2026-10-20]* the same rows; read: `is_action_time` compares the clock with 23:20:00 inclusive |
| A placed run can be held | **yes**: a run placed at 22:30 whose 23:01 check fails is held at 23:10, with a notice to answer by 23:20, and four `held … reason=None` lines after | *[measured 2026-10-20]* the dispatcher's own code, graph and Telegram in memory: `wq131_probe.py` on `main` `e82f9d88` → `f1_main_e82f9d88.txt`. On the fleet: never seen (0 `RunHold`; every 23:01 check passed) |
| How long a run takes, from the 22:30 fire to its last stage record | **10 to 19 min on 23 of 25 nights; 30 and 32 min on 09-28 and 10-05; at most 16 min 45 s since debates run three at once (10-09 on)** | *[measured 2026-10-20]* the live graph, 2026-09-14 to 2026-10-19: `wq131_nights.py` → `wq131_nights.txt` |
| A run placed at 23:10 takes as long as one placed at 22:30 | not measured | *[ASSUMED — not measured]* its agents are awake since 22:30, so it may be shorter; no run has ever been held on the fleet |
| The prototype's night | **3 `skipped` before, 1 `placed`, 8 `already-placed`; no hold on the failing-check night** | *[measured 2026-10-20]* `wq131_probe.py` on `proto-s285` → `f1_proto.txt` |

---

## Scope — and what is deliberately NOT here

1. **The fix** (Appendix section 1): `scheduled_dispatch_actions.py` gains `fire_tick`, `already_placed` and a time-aware `outside_window`, and `_ACT_BY` becomes 23:10; `scheduled_dispatch_human.py` returns `already-placed` once the day's `RunRequest` exists (after the brief, before the window check) and retries an unsent degraded notice inside the window; `ScheduledDispatchResult.action` gains `already-placed`; the job's line for a held result falls back to its reason.
2. **The law cycle and six existing tests** (Appendix section 2): dispatcher law v1.7, its test-plan, both rollups, `docs/deployment.md`'s dispatcher row; the six test files named there.
3. **Your tests A1 to A11** in two new files, under the names the Test plan gives.

### Out of scope (do NOT build this sprint)

- **Winding the fleet down when the run completes** (work-queue 131 part a) and **a graph record of every fire** (the rest of part d): separate, and the second needs a graph label.
- **The window's end.** 23:30 is the operator's (DL-294); this sprint fits the last placing fire to it.
- **`place_scheduled_run`.** It still merges the same `RunRequest` when called twice (`DSP-IDM-02`'s existing test calls it directly); the guard sits in the fire, before it is called.
- **The brief and the sensor.** No change.
- **No ADR reversal**, no change to `contracts/`, no graph vocabulary change, no new env key or tunable.

### The road not taken (LAW-06)

All in [DL-309](../design-log.md): the guard inside `place_scheduled_run` alone (a *Run now* answer re-places at every fire, and the fires after the window still say `skipped`); changing only the line (keeps the false hold); keeping 23:20 read by the tick (a run placed then has nine and a half minutes); 23:00 as the last fire (no passing check could ever release a held run); ending the window later (the operator's, for cost).

---

## The design decisions this sprint has to make

**None left: all seven are decided in [DL-309](../design-log.md)** (D1 to D7), measured first. If a law reading contradicts one, stop and report. Do not add a DL entry.

---

## Blast radius — measured 2026-10-20

| What | Detail |
| --- | --- |
| Files changed | `orchestration/scheduled_dispatch_actions.py` 100 → **131**; `scheduled_dispatch_human.py` 168 → **175**; `scheduled_dispatch.py` **179** (one line); `scripts/dispatch_scheduled_run.py` **145** (one line); `orchestration/laws/dispatcher/laws.md`, `test-plan.md`, `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/deployment.md`; tests `test_act_by_local_time.py`, `test_daily_brief_boundaries.py`, `test_scheduled_dispatch_degraded_notices.py`, `test_scheduled_dispatch_notices.py` 170 → **179**, `tests/test_dispatch_brief_script.py`, `tests/test_master_wake_window.py`; your new `orchestration/tests/test_scheduled_dispatch_once.py` (the planner's is **190**) and `tests/test_dispatch_fire_lines.py` (the planner's **126**) |
| Agents affected | none: `orchestration/` and the job's script; no agent imports another |
| Contract change? | No (`ScheduledDispatchResult` lives in `orchestration/`) |
| Graph vocabulary change? | No new label or property: the fire writes less, never more |
| New env keys / tunables | None |
| Deploy implication | **Image-only retag.** No fidelity decision path (`scripts/replay_fidelity_git.py::DECISION_PATHS`): the count holds. Only the dispatcher job runs this code |
| Rollback | Retag the fleet back to `s284`. Nothing else to undo: no graph write changes shape, no order, schema, pack or infra setting changes |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Write the tests A1 to A11** under the Test plan's names and run them on the unchanged tree. Paste that red output: the split must match the Test plan's last line.
3. **Apply Appendix section 1 exactly**, then **section 2 exactly**. Change nothing else.
4. **Prove the guards can fail (DL-70)**: plant B1 to B17 (Traps) one at a time against your tests alone; each must turn at least one red; restore each.
5. **Bump the version PATCH** to the next free number after `main`'s, `uv lock --offline`, stage `uv.lock`.
6. **`make ci` green** — every step, **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Each docstring cites the clauses in the last column. The names are fixed: the test-plan rows in Appendix section 2 cite them. Every fire in a test lands 26 seconds after its tick, as on the fleet.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 `orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so` | twelve fires 22:00:26 to 23:50:26 on 2026-10-19, a passing check at 22:00:45 | `(action, reason)` = 3 × `("skipped", "before the placing window, 22:30 to 23:10 UTC")`, 1 × `("placed", "NYSE trading session")`, 8 × `("already-placed", "placed by an earlier fire")`; one `RunRequest`, no `RunHold` (`DSP-OBS-04`, `DSP-IDM-02`) |
| A2 | 🎯 `…once.py::test_a_placed_run_is_never_held_when_a_later_check_fails` | placed at 22:30:26; a failing check at 23:01:05; fires at 23:10:26 and 23:20:26 | both `already-placed`; **no `FleetPreflight` read** during those two fires (a graph that counts them); no `RunHold`; no hold notice (`DSP-NEV-04`) |
| A3 | `…once.py::test_the_last_placing_fire_is_the_2310_tick` (parametrized) | `is_action_time` at 22:29:59, 22:30:00, 23:10:26, 23:10:59, 23:19:59, 23:20:00, 23:20:26 | False, True, True, True, True, False, False (`DSP-TRG-01`) |
| A4 | 🎯 `…once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not` | (i) a failing check at 22:00:45, held at 22:30; a passing one at 23:01:05; (ii) held at 22:30, a *Run now* answer first read by the 23:20:26 fire | (i) the 23:10:26 fire `placed`, the hold carries `released_at`; (ii) `("held", "after the placing window, 22:30 to 23:10 UTC", <the hold's failures>)`, no `RunRequest`, `answered_with` `run_now` (`DSP-TRG-01`, `DSP-PERF-01`) |
| A5 | `…once.py::test_the_hold_notice_names_the_2310_deadline` | a failing check, the 22:30 fire on 2026-10-19 | the notice's `act_by` is `10:10 Melbourne (23:10 UTC)` (`DSP-OBS-02`, `DSP-TRG-01`) |
| A6 | `…once.py::test_an_override_placed_run_is_already_placed_at_the_next_fire` | held at 22:30; *Run now* read at 22:40; a fire at 22:50 | `placed`, then `already-placed`; one `RunRequest` (`DSP-NEV-04`, `DSP-IDM-02`) |
| A7 | `…once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only` (parametrized) | a degraded check (an LLM-only failure); the 22:30 notice sent with no message id; the next fire at 22:40:26, or at 23:20:26 | `already-placed`, posture `degraded`, the failures carried; at 22:40 the notice is sent and `degraded_notified_at` written; at 23:20 neither (`DSP-OUT-05`, `DSP-NEV-04`) |
| A8 | 🎯 `tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did` | `format_dispatch_result` over real fires | exactly: `skipped sched-2026-10-19 reason=before the placing window, 22:30 to 23:10 UTC` (22:20); `placed … reason=NYSE trading session` (22:30); `already-placed … reason=placed by an earlier fire` (23:50); `held … reason=failing failures=1` (22:30, a failing check); `held … reason=after the placing window, 22:30 to 23:10 UTC failures=1` (23:20, same graph); `skipped … reason=after the placing window, 22:30 to 23:10 UTC` (23:20, empty graph) (`DSP-OBS-04`) |
| A9 | `…lines.py::test_a_skip_answer_still_says_operator` | held at 22:30; *Skip today* read at 22:40 | `skipped sched-2026-10-19 reason=operator` (`DSP-OBS-04`, `DSP-OUT-02`) |
| A10 | `…lines.py::test_the_result_names_one_of_four_actions_and_readiness_only_when_held` | `typing.get_type_hints(ScheduledDispatchResult)["action"]`; fires at 22:20 and 22:30 on a failing check, 22:40 and 22:50 after a passing one | the action's arguments are exactly `("placed", "already-placed", "skipped", "held")`; actions `skipped`, `held`, `placed`, `already-placed`; `readiness_state` `None`, `"failing"`, `None`, `None` (`DSP-TYP-01`) |
| A11 | `…lines.py::test_a_run_placed_at_the_last_fire_ends_before_the_window` | `infra/deploy-agents.ps1`'s `ScaleEnd` default read as text; `_ACT_BY` | `_ACT_BY` + 20 min ≤ the end, and `_ACT_BY` + 30 min > the end: 23:10 is the last fire that fits (`DSP-TRG-01`) |

On the unchanged tree all but A9 fail (A3 on one case, 23:20:00; A4 on case ii). After Appendix section 1 all eleven pass.

---

## Success factors

- [ ] On the built tree, `wq131_probe.py` (planner's F1) prints exactly the prototype's output (`f1_proto.txt`): one `placed`, then `already-placed`, and no hold on the night a later check fails.
- [x] `place_scheduled_run`, the brief, the sensor, `contracts/` and every agent unchanged; no existing test changed beyond Appendix section 2's six files.
- [x] Design decisions recorded with rejected alternatives: DL-309, already on `main`.
- [x] Law cycle done as Appendix section 2: `DSP-NEV-04`, `DSP-OBS-04` and `DSP-TYP-01` 🟩, rollup 46 / 49 in both rollups.
- [x] B1 to B17 each planted, watched to fail against your tests alone, restored — stated per break.
- [x] Every touched module < 200 lines, test files included.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **A fire lands seconds after its tick.** Test fires sit 26 seconds past it. A test at whole minutes passes on the old code too: that is how DL-300's six-tick test counted a 23:20 fire the fleet never has.
🪤 **The new return sits after the brief and before the window check.** Before the brief, a run's brief is never sent (`DSP-TRG-03`); after the window check, the fires after 23:10 still say `skipped`.
🪤 **The degraded retry is inside the window only** (A7's 23:20 case). That is what the fires' re-placing gave before; do not widen it.
🪤 **`test_c5_rehold_after_release_gets_its_own_notice` changes on purpose.** It pinned a hold written after a release that had placed the run: the defect. In Appendix section 2 the release places nothing (an empty universe raises after the release is written), and the re-hold it then tests is still `DSP-STA-01`'s.
🪤 **`place_scheduled_run` keeps merging.** `test_double_fire_merges_to_one_run_request_node` calls it directly; leave both alone.
🪤 **Write files with an editor, not a shell heredoc**: Git Bash's heredoc ate a backslash in the planner's `\n` literal.
🪤 **Sizes.** `test_scheduled_dispatch_notices.py` is 179 after section 2; keep your two new files under 200 (the planner's are 190 and 126), measured after `ruff format`.

**The breaks** (plant one at a time in production code, run your A1 to A11 alone, expect red, restore):

| # | Break | # | Break |
| --- | --- | --- | --- |
| B1 | `_ACT_BY = time(23, 20)` | B10 | `already_placed`'s reason reads `placed earlier` |
| B2 | `is_action_time` reads `now.time()`, not `fire_tick(now)` | B11 | `already_placed` reads the key `run-request-{run_id}` |
| B3 | `_TICK_MINUTES = 1` | B12 | `already_placed` always reports posture `normal` |
| B4 | `outside_window`'s `before` and `after` swapped | B13 | the degraded retry removed |
| B5 | `outside_window` returns `skipped` with a hold | B14 | the degraded retry without `is_action_time(now)` |
| B6 | `outside_window`'s held result carries no failures | B15 | `format_dispatch_result` prints `readiness_state` alone for a hold |
| B7 | the `already_placed` return removed | B16 | `act_by_text` names a fixed `23:20` |
| B8 | the `already_placed` return moved after the window check | B17 | `_ACTION_START = time(22, 40)` |
| B9 | `already-placed` removed from the `Literal` | | |

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes after the Appendix: `scheduled_dispatch_actions.py` **131**, `scheduled_dispatch_human.py` **175**, `scheduled_dispatch.py` **179**, `scripts/dispatch_scheduled_run.py` **145**, `test_scheduled_dispatch_notices.py` **179**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. The window's times stay module constants as before (`_ACTION_START`, `_ACT_BY`, `_TICK_MINUTES`): they follow the deploy script's window, which A11 holds them against; they are not a value to tune.
- Faults, not silent failure — `kernel.fault_boundary` (the fire's existing boundaries cover the new path).
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- Version bump PATCH, `uv.lock` staged with it.
- Secrets never through the worktree — your worktree has **no `.env`**, and nothing in this sprint needs one. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the branch's worktree; check the printed SHA against `git rev-parse HEAD`.
2. Planner's review: CodeQL set-diff against the baseline branch first; the blobs against `prototype_blobs.txt` (kit); the planner's tests on the built tree; B1 to B17 against Codex's tests alone; F1 (`wq131_probe.py` from the built tree: equals `f1_proto.txt` byte for byte).
3. Merge to `main` locally and push; tag `v<version>`; post-merge CodeQL.
4. **Deploy: image-only retag** on the operator's word; the fidelity count holds (no decision path); record the rollback tag `s284`. F2 on the first weekday night after: the job's twelve lines read 3 `skipped … before the placing window`, 1 `placed`, 8 `already-placed`; 8 / 8; no fault. Then close parts (b) and (d) of work-queue 131 (the row stays open for part a and the fire record).

---

## Handover — paste this to Codex

```text
You are building Sprint 285 in the worktree ../ta-s285, on the branch
sprint-285-the-dispatcher-keeps-the-deadline-it-tells. Never work on main. The worktree and its
venv are ready; never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-285-the-dispatcher-keeps-the-deadline-it-tells.md, whole, before anything
else. It is the spec, and its bottom sections are your handback. The Appendix holds the
production code, the law text and six existing-test edits, which you apply exactly. Your work is
the tests A1 to A11, the breaks, the bump and the evidence.

In order:
1. Read orchestration/laws/dispatcher/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any code.
2. Write orchestration/tests/test_scheduled_dispatch_once.py (A1 to A7) and
   tests/test_dispatch_fire_lines.py (A8 to A11) under the exact names in the Test plan, each
   docstring citing the clauses in its row. Run both on the unchanged tree and paste the output
   into the Closeout: all but A9 fail (A3 on its 23:20:00 case, A4 on its second case).
3. Apply Appendix section 1 exactly (four files). Change nothing else in production code.
4. Apply Appendix section 2 exactly (the dispatcher's laws.md and test-plan.md,
   docs/laws/ledger.md, docs/laws/INDEX.md, docs/deployment.md and six existing test files).
   Change no other existing test. The test-plan rows name your tests; if a name differs, your
   name is wrong.
5. Plant the breaks B1 to B17 (Traps) one at a time; each must turn at least one of your A1 to
   A11 red; restore each before the next. Record each in the Closeout.
6. Bump the version PATCH to the next number after main's in pyproject.toml, run
   uv lock --offline, stage uv.lock. Run make ci redirected to a file and read the file. If the
   dependency audit is the only step that fails for want of network, say so; the planner runs it.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: reach the network or any live service; run infra/ scripts, pwsh or any az command; change
contracts/, kernel/, any agent, place_scheduled_run, orchestration/daily_brief*.py,
orchestration/container_*.py, any pack or any Dockerfile; add or reword a law clause beyond
section 2; add a design-log entry; use noqa; let any module, test files included, reach 200 lines;
measure make ci through a pipe; write files with a shell heredoc.

Traps (the spec's Traps section has them all): every test fire lands 26 seconds after its tick;
the new return sits after the brief and before the window check; the degraded retry is inside
the window only; test_c5 changes on purpose (its release now places nothing); place_scheduled_run
keeps merging.

Two tiers when something does not fit. A wrong command, count, path or line number whose intent is
plain: correct it, record it in Return notes, and carry on. A law that contradicts the spec, an
existing test failing outside section 2's files, or a measurement in the spec that does not
reproduce: STOP and report. State anything not done as "not done" or "verified failing". Never
write a Result for work you have not done.
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
| `scheduled_dispatch_actions.py` and A1-A7 | `orchestration/laws/dispatcher/laws.md` v1.6 and `test-plan.md`, whole; `docs/laws/conventions.md` and `drift-register.md`, whole | `DSP-TRG-01`, `DSP-PERF-01`, `DSP-OBS-02`, amended `DSP-IDM-02`, new `DSP-NEV-04` | Read before code on 2026-10-20 in `../ta-s285`, branch `sprint-285-the-dispatcher-keeps-the-deadline-it-tells`, clean HEAD `d7b728aaba92f041bb7f8d9041a08f23ef5b6b19`, no `.env`. Use the fire's tick and literal expected results; apply only the decided amendments. |
| `scheduled_dispatch_human.py` and Appendix's six existing tests | Same four whole files | `DSP-TRG-02`, `DSP-TRG-03`, `DSP-OUT-05`, `DSP-STA-01`, new `DSP-NEV-04` | Keep calendar skip and brief in place; guard before the window return, retry degraded notices inside the window only, and preserve re-hold proof with a release that placed nothing. |
| `scheduled_dispatch.py` and A10 | Same four whole files | `DSP-TYP-01` | This clause is currently gray; prove all four literal actions and readiness only when held. |
| `scripts/dispatch_scheduled_run.py` and A8-A11 | Same four whole files | `DSP-OUT-02`, `DSP-TRG-01`, new `DSP-OBS-04` | Exercise real fires and read `ScaleEnd` as text; no infrastructure script runs. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes: two new guarantees (`DSP-NEV-04`, `DSP-OBS-04`), no contract change. Apply Appendix section 2 exactly: v1.7, the four amendments and Changelog, cited test-plan rows, and both rollups 43 / 47 to 46 / 49. DL-309 D1-D7 were read; no design decision remains to make.

**Contradictions found between a law and this spec:** None beyond the explicit v1.6-to-v1.7 changes authorized by Appendix section 2. The new-test-first sequence is the handover's explicit order.

**Laws found silent where a decision was needed:** The two new guarantees are already decided in DL-309 and supplied in Appendix section 2. No additional silence requiring a decision or drift row was found.

**Clauses that were ⬜ and are now proven:** Pre-code reading recorded `DSP-TYP-01` as gray and the two new clauses as not yet declared. A10 now proves `DSP-TYP-01`; A2/A6/A7 prove new `DSP-NEV-04`; A1/A8/A9 prove new `DSP-OBS-04`. The exact Appendix law cycle and rollups are 46 / 49. `DSP-IDN-03`, `DSP-NEV-02` and `DSP-DEP-01` remain gray.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a_night_places_the_run_once_and_every_later_fire_says_so` | `orchestration/tests/test_scheduled_dispatch_once.py` | PASS (1 case) | `DSP-OBS-04 / DSP-IDM-02` |
| A2 | `test_a_placed_run_is_never_held_when_a_later_check_fails` | `orchestration/tests/test_scheduled_dispatch_once.py` | PASS (1 case) | `DSP-NEV-04` |
| A3 | `test_the_last_placing_fire_is_the_2310_tick` | `orchestration/tests/test_scheduled_dispatch_once.py` | PASS (7 cases) | `DSP-TRG-01` |
| A4 | `test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not` | `orchestration/tests/test_scheduled_dispatch_once.py` | PASS (2 cases) | `DSP-TRG-01 / DSP-PERF-01` |
| A5 | `test_the_hold_notice_names_the_2310_deadline` | `orchestration/tests/test_scheduled_dispatch_once.py` | PASS (1 case) | `DSP-OBS-02 / DSP-TRG-01` |
| A6 | `test_an_override_placed_run_is_already_placed_at_the_next_fire` | `orchestration/tests/test_scheduled_dispatch_once.py` | PASS (1 case) | `DSP-NEV-04 / DSP-IDM-02` |
| A7 | `test_an_unsent_degraded_notice_is_retried_inside_the_window_only` | `orchestration/tests/test_scheduled_dispatch_once.py` | PASS (2 cases) | `DSP-OUT-05 / DSP-NEV-04` |
| A8 | `test_each_fire_prints_what_it_did` | `tests/test_dispatch_fire_lines.py` | PASS (1 case) | `DSP-OBS-04` |
| A9 | `test_a_skip_answer_still_says_operator` | `tests/test_dispatch_fire_lines.py` | PASS (1 case) | `DSP-OBS-04 / DSP-OUT-02` |
| A10 | `test_the_result_names_one_of_four_actions_and_readiness_only_when_held` | `tests/test_dispatch_fire_lines.py` | PASS (1 case) | `DSP-TYP-01` |
| A11 | `test_a_run_placed_at_the_last_fire_ends_before_the_window` | `tests/test_dispatch_fire_lines.py` | PASS (1 case) | `DSP-TRG-01` |

**Tests added beyond the plan:** None. Eleven exact function names, nineteen cases; A4's two specified scenarios are parametrized separately.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s285`, branch `sprint-285-the-dispatcher-keeps-the-deadline-it-tells`; `.env` absent. Ready venv used with `UV_OFFLINE=1`, `UV_NO_SYNC=1`; no sync, external network or live service used. CI HTTP proxies point only at the closed local port `127.0.0.1:9`.

**Result:** Exact unchanged-tree split reproduced (11 failed, 8 passed); after the exact Appendix, all 19 cases pass. B1-B17 each produced exit 1 against A1-A11 alone and were restored byte for byte. All 15 Appendix blobs match; the excluded paths and `place_scheduled_run` are unchanged. Version `0.128.07`, offline lock succeeded. Full CI evidence and its limitation follow.

**Files changed:** 21 paths, all authorized:

- `docs/deployment.md`
- `docs/laws/INDEX.md`
- `docs/laws/ledger.md`
- `docs/sprints/README.md`
- `docs/sprints/sprint-285-the-dispatcher-keeps-the-deadline-it-tells.md`
- `orchestration/laws/dispatcher/laws.md`
- `orchestration/laws/dispatcher/test-plan.md`
- `orchestration/scheduled_dispatch.py`
- `orchestration/scheduled_dispatch_actions.py`
- `orchestration/scheduled_dispatch_human.py`
- `orchestration/tests/test_act_by_local_time.py`
- `orchestration/tests/test_daily_brief_boundaries.py`
- `orchestration/tests/test_scheduled_dispatch_degraded_notices.py`
- `orchestration/tests/test_scheduled_dispatch_notices.py`
- `orchestration/tests/test_scheduled_dispatch_once.py`
- `pyproject.toml`
- `scripts/dispatch_scheduled_run.py`
- `tests/test_dispatch_brief_script.py`
- `tests/test_dispatch_fire_lines.py`
- `tests/test_master_wake_window.py`
- `uv.lock`

**Design decisions:** recorded as [`DL-309`](../design-log.md) — seven decisions with the roads not taken, on `main` before the branch was cut.

**Proof — the red run first:**

```text
$ uv run --offline --no-sync pytest --no-cov -v --tb=short orchestration/tests/test_scheduled_dispatch_once.py tests/test_dispatch_fire_lines.py
============================= test session starts =============================
collecting ... collected 19 items

orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so FAILED [  5%]
orchestration/tests/test_scheduled_dispatch_once.py::test_a_placed_run_is_never_held_when_a_later_check_fails FAILED [ 10%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[22:29:59-False] PASSED [ 15%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[22:30:00-True] PASSED [ 21%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:10:26-True] PASSED [ 26%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:10:59-True] PASSED [ 31%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:19:59-True] PASSED [ 36%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:20:00-False] FAILED [ 42%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:20:26-False] PASSED [ 47%]
orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2310-release] PASSED [ 52%]
orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2320-answer] FAILED [ 57%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_hold_notice_names_the_2310_deadline FAILED [ 63%]
orchestration/tests/test_scheduled_dispatch_once.py::test_an_override_placed_run_is_already_placed_at_the_next_fire FAILED [ 68%]
orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now0-True] FAILED [ 73%]
orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now1-False] FAILED [ 78%]
tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did FAILED [ 84%]
tests/test_dispatch_fire_lines.py::test_a_skip_answer_still_says_operator PASSED [ 89%]
tests/test_dispatch_fire_lines.py::test_the_result_names_one_of_four_actions_and_readiness_only_when_held FAILED [ 94%]
tests/test_dispatch_fire_lines.py::test_a_run_placed_at_the_last_fire_ends_before_the_window FAILED [100%]

================================== FAILURES ===================================
________ test_a_night_places_the_run_once_and_every_later_fire_says_so ________
orchestration\tests\test_scheduled_dispatch_once.py:86: in test_a_night_places_the_run_once_and_every_later_fire_says_so
    assert [(r.action, r.reason) for r in results] == (
E   AssertionError: assert [('skipped', ...ession'), ...] == [('skipped', ...r fire'), ...]
E
E     At index 0 diff: ('skipped', 'NYSE trading session') != ('skipped', 'before the placing window, 22:30 to 23:10 UTC')
E
E     Full diff:
E       [
E           (
E               'skipped',...
E
E     ...Full output truncated (70 lines hidden), use '-vv' to show
__________ test_a_placed_run_is_never_held_when_a_later_check_fails ___________
orchestration\tests\test_scheduled_dispatch_once.py:103: in test_a_placed_run_is_never_held_when_a_later_check_fails
    assert graph.readiness_reads == before
E   assert 2 == 1
E    +  where 2 = <test_scheduled_dispatch_once._ReadGraph object at 0x000002427CF1C830>.readiness_reads
_________ test_the_last_placing_fire_is_the_2310_tick[23:20:00-False] _________
orchestration\tests\test_scheduled_dispatch_once.py:126: in test_the_last_placing_fire_is_the_2310_tick
    assert (
E   AssertionError: assert True is False
E    +  where True = is_action_time(datetime.datetime(2026, 10, 19, 23, 20, tzinfo=datetime.timezone.utc))
E    +    where datetime.datetime(2026, 10, 19, 23, 20, tzinfo=datetime.timezone.utc) = <built-in method fromisoformat of type object at 0x00007FFB7C215760>('2026-10-19T23:20:00+00:00')
E    +      where <built-in method fromisoformat of type object at 0x00007FFB7C215760> = datetime.fromisoformat
_ test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2320-answer] _
orchestration\tests\test_scheduled_dispatch_once.py:145: in test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not
    assert result.reason == "after the placing window, 22:30 to 23:10 UTC"
E   AssertionError: assert 'NYSE trading session' == 'after the pl... to 23:10 UTC'
E
E     - after the placing window, 22:30 to 23:10 UTC
E     + NYSE trading session
________________ test_the_hold_notice_names_the_2310_deadline _________________
orchestration\tests\test_scheduled_dispatch_once.py:162: in test_the_hold_notice_names_the_2310_deadline
    assert telegram.sent[0]["act_by"] == "10:10 Melbourne (23:10 UTC)"
E   AssertionError: assert '10:20 Melbourne (23:20 UTC)' == '10:10 Melbourne (23:10 UTC)'
E
E     - 10:10 Melbourne (23:10 UTC)
E     ?    ^                ^
E     + 10:20 Melbourne (23:20 UTC)
E     ?    ^                ^
_______ test_an_override_placed_run_is_already_placed_at_the_next_fire ________
orchestration\tests\test_scheduled_dispatch_once.py:172: in test_an_override_placed_run_is_already_placed_at_the_next_fire
    assert fire(graph, telegram, at(22, 50)).action == "already-placed"
E   AssertionError: assert 'placed' == 'already-placed'
E
E     - already-placed
E     + placed
_ test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now0-True] _
orchestration\tests\test_scheduled_dispatch_once.py:190: in test_an_unsent_degraded_notice_is_retried_inside_the_window_only
    assert result.action == "already-placed"
E   AssertionError: assert 'placed' == 'already-placed'
E
E     - already-placed
E     + placed
_ test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now1-False] _
orchestration\tests\test_scheduled_dispatch_once.py:190: in test_an_unsent_degraded_notice_is_retried_inside_the_window_only
    assert result.action == "already-placed"
E   AssertionError: assert 'skipped' == 'already-placed'
E
E     - already-placed
E     + skipped
______________________ test_each_fire_prints_what_it_did ______________________
tests\test_dispatch_fire_lines.py:41: in test_each_fire_prints_what_it_did
    assert [format_dispatch_result(result) for result in results] == [
E   AssertionError: assert ['skipped sch...ding session'] == ['skipped sch...to 23:10 UTC']
E
E     At index 0 diff: 'skipped sched-2026-10-19 reason=NYSE trading session' != 'skipped sched-2026-10-19 reason=before the placing window, 22:30 to 23:10 UTC'
E
E     Full diff:
E       [
E     +     'skipped sched-2026-10-19 reason=NYSE trading session',
E     -     'skipped sched-2026-10-19 reason=before the placing window, 22:30 to 23:10 '...
E
E     ...Full output truncated (12 lines hidden), use '-vv' to show
___ test_the_result_names_one_of_four_actions_and_readiness_only_when_held ____
tests\test_dispatch_fire_lines.py:67: in test_the_result_names_one_of_four_actions_and_readiness_only_when_held
    assert get_args(get_type_hints(ScheduledDispatchResult)["action"]) == (
E   AssertionError: assert ('placed', 'skipped', 'held') == ('placed', 'a...pped', 'held')
E
E     At index 1 diff: 'skipped' != 'already-placed'
E     Right contains one more item: 'held'
E
E     Full diff:
E       (
E           'placed',...
E
E     ...Full output truncated (4 lines hidden), use '-vv' to show
__________ test_a_run_placed_at_the_last_fire_ends_before_the_window __________
tests\test_dispatch_fire_lines.py:97: in test_a_run_placed_at_the_last_fire_ends_before_the_window
    assert last + timedelta(minutes=20) <= end
E   assert (datetime.datetime(2026, 10, 19, 23, 20, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=1200)) <= datetime.datetime(2026, 10, 19, 23, 30, tzinfo=datetime.timezone.utc)
E    +  where datetime.timedelta(seconds=1200) = timedelta(minutes=20)
=========================== short test summary info ===========================
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_placed_run_is_never_held_when_a_later_check_fails
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:20:00-False]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2320-answer]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_hold_notice_names_the_2310_deadline
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_override_placed_run_is_already_placed_at_the_next_fire
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now0-True]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now1-False]
FAILED tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did
FAILED tests/test_dispatch_fire_lines.py::test_the_result_names_one_of_four_actions_and_readiness_only_when_held
FAILED tests/test_dispatch_fire_lines.py::test_a_run_placed_at_the_last_fire_ends_before_the_window
======================== 11 failed, 8 passed in 2.60s =========================
RED_EXIT=1
```

**Proof — the green run:**

```text
$ uv run --offline --no-sync pytest --no-cov -v --tb=short orchestration/tests/test_scheduled_dispatch_once.py tests/test_dispatch_fire_lines.py
============================= test session starts =============================
collecting ... collected 19 items

orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so PASSED [  5%]
orchestration/tests/test_scheduled_dispatch_once.py::test_a_placed_run_is_never_held_when_a_later_check_fails PASSED [ 10%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[22:29:59-False] PASSED [ 15%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[22:30:00-True] PASSED [ 21%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:10:26-True] PASSED [ 26%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:10:59-True] PASSED [ 31%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:19:59-True] PASSED [ 36%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:20:00-False] PASSED [ 42%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:20:26-False] PASSED [ 47%]
orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2310-release] PASSED [ 52%]
orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2320-answer] PASSED [ 57%]
orchestration/tests/test_scheduled_dispatch_once.py::test_the_hold_notice_names_the_2310_deadline PASSED [ 63%]
orchestration/tests/test_scheduled_dispatch_once.py::test_an_override_placed_run_is_already_placed_at_the_next_fire PASSED [ 68%]
orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now0-True] PASSED [ 73%]
orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now1-False] PASSED [ 78%]
tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did PASSED [ 84%]
tests/test_dispatch_fire_lines.py::test_a_skip_answer_still_says_operator PASSED [ 89%]
tests/test_dispatch_fire_lines.py::test_the_result_names_one_of_four_actions_and_readiness_only_when_held PASSED [ 94%]
tests/test_dispatch_fire_lines.py::test_a_run_placed_at_the_last_fire_ends_before_the_window PASSED [100%]

============================= 19 passed in 2.26s ==============================
GREEN_EXIT=0

After all 17 breaks were restored and the offline bump:
============================= 19 passed in 2.25s ==============================
RESTORED_EXIT=0
```

**Guards planted:** Each break was planted alone, run against only the two new files with `python -m pytest --no-cov -q --tb=short`, then restored to the saved exact bytes before the next break. Real output:

```text
B1: exit=1; 8 failed, 11 passed in 2.51s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:20:00-False]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:20:26-False]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2320-answer]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_hold_notice_names_the_2310_deadline
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now1-False]
FAILED tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did
FAILED tests/test_dispatch_fire_lines.py::test_a_run_placed_at_the_last_fire_ends_before_the_window
B2: exit=1; 4 failed, 15 passed in 2.46s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:10:26-True]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:10:59-True]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:19:59-True]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2310-release]
B3: exit=1; 1 failed, 18 passed in 2.50s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[23:19:59-True]
B4: exit=1; 3 failed, 16 passed in 2.46s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2320-answer]
FAILED tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did
B5: exit=1; 2 failed, 17 passed in 2.43s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2320-answer]
FAILED tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did
B6: exit=1; 2 failed, 17 passed in 2.45s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2320-answer]
FAILED tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did
B7: exit=1; 7 failed, 12 passed in 2.53s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_placed_run_is_never_held_when_a_later_check_fails
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_override_placed_run_is_already_placed_at_the_next_fire
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now0-True]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now1-False]
FAILED tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did
FAILED tests/test_dispatch_fire_lines.py::test_the_result_names_one_of_four_actions_and_readiness_only_when_held
B8: exit=1; 4 failed, 15 passed in 2.53s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_placed_run_is_never_held_when_a_later_check_fails
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now1-False]
FAILED tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did
B9: exit=1; 1 failed, 18 passed in 2.59s; restored exact bytes
FAILED tests/test_dispatch_fire_lines.py::test_the_result_names_one_of_four_actions_and_readiness_only_when_held
B10: exit=1; 2 failed, 17 passed in 2.61s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so
FAILED tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did
B11: exit=1; 7 failed, 12 passed in 6.92s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_placed_run_is_never_held_when_a_later_check_fails
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_override_placed_run_is_already_placed_at_the_next_fire
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now0-True]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now1-False]
FAILED tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did
FAILED tests/test_dispatch_fire_lines.py::test_the_result_names_one_of_four_actions_and_readiness_only_when_held
B12: exit=1; 2 failed, 17 passed in 2.80s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now0-True]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now1-False]
B13: exit=1; 1 failed, 18 passed in 2.74s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now0-True]
B14: exit=1; 1 failed, 18 passed in 2.64s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now1-False]
B15: exit=1; 1 failed, 18 passed in 2.62s; restored exact bytes
FAILED tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did
B16: exit=1; 1 failed, 18 passed in 2.65s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_hold_notice_names_the_2310_deadline
B17: exit=1; 12 failed, 7 passed in 2.76s; restored exact bytes
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_placed_run_is_never_held_when_a_later_check_fails
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick[22:30:00-True]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2310-release]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not[2320-answer]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_the_hold_notice_names_the_2310_deadline
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_override_placed_run_is_already_placed_at_the_next_fire
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now0-True]
FAILED orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only[now1-False]
FAILED tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did
FAILED tests/test_dispatch_fire_lines.py::test_a_skip_answer_still_says_operator
FAILED tests/test_dispatch_fire_lines.py::test_the_result_names_one_of_four_actions_and_readiness_only_when_held
GUARDS_PROVEN=17/17; all four production files restored
BREAKS_EXIT=0
```

**Module line counts:** Final formatted counts and scope proof after filling the handback:

```text
APPENDIX_BLOBS=15/15 exact matches
SCOPE_OK=21 files, all within the 21 allowed paths
179 orchestration/scheduled_dispatch.py
131 orchestration/scheduled_dispatch_actions.py
175 orchestration/scheduled_dispatch_human.py
 46 orchestration/tests/test_act_by_local_time.py
185 orchestration/tests/test_daily_brief_boundaries.py
106 orchestration/tests/test_scheduled_dispatch_degraded_notices.py
179 orchestration/tests/test_scheduled_dispatch_notices.py
198 orchestration/tests/test_scheduled_dispatch_once.py
145 scripts/dispatch_scheduled_run.py
 68 tests/test_dispatch_brief_script.py
 98 tests/test_dispatch_fire_lines.py
 68 tests/test_master_wake_window.py
PLACE_SCHEDULED_RUN=unchanged source
PROTECTED_PATHS=unchanged; no production edits beyond Appendix section 1
ENV_FILE=absent
VERSION=0.128.07; main=0.128.06; uv.lock=0.128.7
SCOPE_EXIT=0
```

**`make ci`:** Verified failing, exit 2, solely at step 14 (dependency audit). Steps 1-13 passed, including 5,242 passed / 9 skipped and 100.00% coverage. Steps 15-16 passed independently: detect-secrets over tracked files and the untracked-file scanner over both new tests. The audit's attempted PyPI request was refused by the deliberately closed local proxy; no vulnerability verdict is claimed. The planner owes the online audit. `.secrets.baseline` is unchanged.

Ready venv; `UV_OFFLINE=1`, `UV_NO_SYNC=1`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUTF8=1`; HTTP/HTTPS/ALL proxies `http://127.0.0.1:9`, loopback-only `NO_PROXY`, `PIP_NO_INDEX=1`, version checks disabled. Full redirected output, read from `ci.txt`:

```text
$ make ci > ci.txt 2>&1
uv run ruff check . --output-format=github
uv run ruff format --check .
1798 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
pyproject.toml: note: unused section(s): module = ['azure.core', 'azure.identity.*', 'azure.keyvault', 'redis', 'redis.*']
Success: no issues found in 1274 source files
uv run lint-imports

╔══╗─────────▶╔╗ ╔╗      ╔╗◀───┐
╚╣╠╝◀─────┐  ╔╝╚╗║║────▶╔╝╚╗   │
 ║║   ╔══╦══╦╩╗╔╝║║  ╔╦═╩╗╔╝╔═╦══╗
 ║║╔══╣╔╗║╔╗║╔╣║ ║║ ╔╬╣╔╗║║ ║│║╔═╝
╔╣╠╣║║║╚╝║╚╝║║║╚╗║╚═╝║║║║║╚╗║═╣║
╚══╩╩╩╣╔═╩══╩╝╚═╝╚═══╩╩╝╚╩═╩╩═╩╝
  └──▶║║                    ▲
      ╚╝────────────────────┘


---------
Contracts
---------

Analyzed 688 files, 2383 dependencies.
--------------------------------------

Agents may not import one another (talk only via messages) KEPT
Substrate imports no pack module KEPT
Agents may not reach into surfaces or orchestration KEPT
Kernel is pure plumbing — no domain, no contracts, no agents KEPT
Contracts declare schemas only — never import agents or runtime layers KEPT

Contracts: 5 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
[WARN] kernel/bus.py: 159 lines (warn 150, hard block 200)
[WARN] kernel/bus_azure.py: 171 lines (warn 150, hard block 200)
[WARN] kernel/bus_azure_receiver.py: 170 lines (warn 150, hard block 200)
[WARN] kernel/bus_celery.py: 178 lines (warn 150, hard block 200)
[WARN] kernel/deliberation.py: 182 lines (warn 150, hard block 200)
[WARN] kernel/deliberation_guided.py: 151 lines (warn 150, hard block 200)
[WARN] kernel/deliberation_prompts.py: 155 lines (warn 150, hard block 200)
[WARN] kernel/graph_memory.py: 176 lines (warn 150, hard block 200)
[WARN] kernel/graph_postgres.py: 155 lines (warn 150, hard block 200)
[WARN] kernel/graph_postgres_queries.py: 150 lines (warn 150, hard block 200)
[WARN] kernel/llm_anthropic.py: 168 lines (warn 150, hard block 200)
[WARN] kernel/llm_ledger.py: 159 lines (warn 150, hard block 200)
[WARN] kernel/stop.py: 165 lines (warn 150, hard block 200)
[WARN] kernel/work_loop.py: 186 lines (warn 150, hard block 200)
[WARN] kernel/work_loop_state.py: 160 lines (warn 150, hard block 200)
[WARN] contracts/broker_lifecycle.py: 182 lines (warn 150, hard block 200)
[WARN] contracts/forecaster.py: 153 lines (warn 150, hard block 200)
[WARN] contracts/portfolio_manager.py: 151 lines (warn 150, hard block 200)
[WARN] contracts/positions.py: 193 lines (warn 150, hard block 200)
[WARN] contracts/provider.py: 186 lines (warn 150, hard block 200)
[WARN] agents/analyst/domain/recommend.py: 184 lines (warn 150, hard block 200)
[WARN] agents/analyst/domain/scoring.py: 191 lines (warn 150, hard block 200)
[WARN] agents/analyst/domain/technical_rules.py: 163 lines (warn 150, hard block 200)
[WARN] agents/analyst/poll.py: 160 lines (warn 150, hard block 200)
[WARN] agents/analyst/run.py: 169 lines (warn 150, hard block 200)
[WARN] agents/analyst/settings.py: 161 lines (warn 150, hard block 200)
[WARN] agents/analyst/settings_indicators.py: 159 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/helpers.py: 198 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_analyst_agent.py: 199 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_analyst_alpha_features.py: 190 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_analyst_alpha_integration.py: 188 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_analyst_domain.py: 199 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_analyst_poll.py: 192 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_analyze_domain.py: 192 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_exit_authority.py: 185 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_indicators.py: 158 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_indicators_pattern.py: 198 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_indicators_pattern_edges.py: 152 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_indicators_range.py: 169 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_measured_stop_targets.py: 156 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_recommend_domain.py: 160 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_scaled_stop_targets.py: 198 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_sentiment_reading.py: 192 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_sentiment_subject.py: 187 lines (warn 150, hard block 200)
[WARN] agents/analyst/tests/test_stop_target_outcome.py: 153 lines (warn 150, hard block 200)
[WARN] agents/curator/agent.py: 191 lines (warn 150, hard block 200)
[WARN] agents/curator/tests/helpers.py: 164 lines (warn 150, hard block 200)
[WARN] agents/deliberator/context_arithmetic.py: 163 lines (warn 150, hard block 200)
[WARN] agents/deliberator/entrypoint.py: 160 lines (warn 150, hard block 200)
[WARN] agents/deliberator/poll.py: 190 lines (warn 150, hard block 200)
[WARN] agents/deliberator/review_record.py: 169 lines (warn 150, hard block 200)
[WARN] agents/deliberator/servicebus_peer_client.py: 184 lines (warn 150, hard block 200)
[WARN] agents/deliberator/settings.py: 178 lines (warn 150, hard block 200)
[WARN] agents/deliberator/tests/concurrent_review_helpers.py: 170 lines (warn 150, hard block 200)
[WARN] agents/deliberator/tests/test_deliberator_agent.py: 158 lines (warn 150, hard block 200)
[WARN] agents/deliberator/tests/test_llm_output_bounds.py: 155 lines (warn 150, hard block 200)
[WARN] agents/deliberator/tests/test_llm_provider.py: 156 lines (warn 150, hard block 200)
[WARN] agents/deliberator/tests/test_manager_preflight.py: 198 lines (warn 150, hard block 200)
[WARN] agents/deliberator/tests/test_stop_reason_fail_open.py: 199 lines (warn 150, hard block 200)
[WARN] agents/execution/alpaca.py: 188 lines (warn 150, hard block 200)
[WARN] agents/execution/alpaca_orders.py: 163 lines (warn 150, hard block 200)
[WARN] agents/execution/broker_stop_realign.py: 182 lines (warn 150, hard block 200)
[WARN] agents/execution/broker_stops.py: 189 lines (warn 150, hard block 200)
[WARN] agents/execution/deliberation_gate.py: 162 lines (warn 150, hard block 200)
[WARN] agents/execution/drop_sweep.py: 184 lines (warn 150, hard block 200)
[WARN] agents/execution/drop_sweep_records.py: 172 lines (warn 150, hard block 200)
[WARN] agents/execution/filled_entry_stops.py: 174 lines (warn 150, hard block 200)
[WARN] agents/execution/order_tolerance.py: 164 lines (warn 150, hard block 200)
[WARN] agents/execution/paper_broker.py: 177 lines (warn 150, hard block 200)
[WARN] agents/execution/reconciliation_flags.py: 179 lines (warn 150, hard block 200)
[WARN] agents/execution/reconciliation_store.py: 169 lines (warn 150, hard block 200)
[WARN] agents/execution/settings.py: 162 lines (warn 150, hard block 200)
[WARN] agents/execution/store.py: 166 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/broker_stop_helpers.py: 196 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/helpers.py: 152 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/order_read_helpers.py: 193 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/stop_realign_helpers.py: 176 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_alpaca_broker.py: 195 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_alpaca_order_reads.py: 166 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_alpaca_stop_orders.py: 181 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_broker_positions.py: 166 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_broker_stop_branch_edges.py: 187 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_broker_stop_edges.py: 196 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_broker_stop_pending_position.py: 156 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_broker_stop_realign.py: 156 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_broker_stop_replace_adapters.py: 172 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_broker_stop_replacement.py: 195 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_broker_stop_unprotected.py: 168 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_deliberation_posture.py: 199 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_drop_sweep.py: 194 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_drop_sweep_edges.py: 154 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_execution_deliberation_gate.py: 193 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_execution_domain.py: 199 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_execution_poll.py: 196 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_fill_refresh_unresolved_pnl.py: 163 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_filled_entry_stops.py: 170 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_graph_write_failure_retry.py: 158 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_p3_execution_slice.py: 176 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_partial_fill_completion.py: 183 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_position_sync_poll.py: 155 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_realized_pnl_refresh.py: 190 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_reconciliation.py: 187 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_reconciliation_flag_upgrade.py: 160 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_reconciliation_flags.py: 150 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_run_start_orders.py: 172 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_scaled_order_tolerance.py: 181 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_stop_derivation_provenance.py: 163 lines (warn 150, hard block 200)
[WARN] agents/execution/tests/test_tolerance_evidence.py: 163 lines (warn 150, hard block 200)
[WARN] agents/forecaster/agent.py: 166 lines (warn 150, hard block 200)
[WARN] agents/forecaster/barrier_forecast.py: 160 lines (warn 150, hard block 200)
[WARN] agents/forecaster/domain/barrier_garch.py: 172 lines (warn 150, hard block 200)
[WARN] agents/forecaster/domain/factor_signal.py: 193 lines (warn 150, hard block 200)
[WARN] agents/forecaster/poll.py: 154 lines (warn 150, hard block 200)
[WARN] agents/forecaster/settings.py: 171 lines (warn 150, hard block 200)
[WARN] agents/forecaster/tests/barrier_helpers.py: 199 lines (warn 150, hard block 200)
[WARN] agents/forecaster/tests/helpers.py: 172 lines (warn 150, hard block 200)
[WARN] agents/forecaster/tests/test_barrier_claim.py: 195 lines (warn 150, hard block 200)
[WARN] agents/forecaster/tests/test_barrier_garch.py: 182 lines (warn 150, hard block 200)
[WARN] agents/forecaster/tests/test_barrier_garch_oracle.py: 184 lines (warn 150, hard block 200)
[WARN] agents/forecaster/tests/test_barrier_poll.py: 169 lines (warn 150, hard block 200)
[WARN] agents/forecaster/tests/test_barrier_refusals.py: 194 lines (warn 150, hard block 200)
[WARN] agents/forecaster/tests/test_barrier_settlement.py: 175 lines (warn 150, hard block 200)
[WARN] agents/forecaster/tests/test_barrier_settlement_record.py: 193 lines (warn 150, hard block 200)
[WARN] agents/master/agent.py: 182 lines (warn 150, hard block 200)
[WARN] agents/master/credential_probes.py: 187 lines (warn 150, hard block 200)
[WARN] agents/master/entrypoint.py: 179 lines (warn 150, hard block 200)
[WARN] agents/master/http_server.py: 163 lines (warn 150, hard block 200)
[WARN] agents/master/remediation.py: 199 lines (warn 150, hard block 200)
[WARN] agents/master/remediation_execution.py: 180 lines (warn 150, hard block 200)
[WARN] agents/master/remediation_gate.py: 179 lines (warn 150, hard block 200)
[WARN] agents/master/settings.py: 171 lines (warn 150, hard block 200)
[WARN] agents/master/store.py: 194 lines (warn 150, hard block 200)
[WARN] agents/master/tests/test_activation_replay.py: 182 lines (warn 150, hard block 200)
[WARN] agents/master/tests/test_credential_probe_body.py: 175 lines (warn 150, hard block 200)
[WARN] agents/master/tests/test_credential_probes.py: 184 lines (warn 150, hard block 200)
[WARN] agents/master/tests/test_credential_test.py: 165 lines (warn 150, hard block 200)
[WARN] agents/master/tests/test_fleet_preflight.py: 193 lines (warn 150, hard block 200)
[WARN] agents/master/tests/test_master_agent.py: 197 lines (warn 150, hard block 200)
[WARN] agents/master/tests/test_remediation.py: 181 lines (warn 150, hard block 200)
[WARN] agents/master/tests/test_remediation_gate.py: 170 lines (warn 150, hard block 200)
[WARN] agents/master/tests/test_stop_server.py: 183 lines (warn 150, hard block 200)
[WARN] agents/master/tests/test_stop_session.py: 192 lines (warn 150, hard block 200)
[WARN] agents/monitor/reconcile.py: 162 lines (warn 150, hard block 200)
[WARN] agents/monitor/store.py: 165 lines (warn 150, hard block 200)
[WARN] agents/monitor/tests/helpers.py: 193 lines (warn 150, hard block 200)
[WARN] agents/monitor/tests/test_broker_reconcile.py: 188 lines (warn 150, hard block 200)
[WARN] agents/monitor/tests/test_monitor_agent.py: 183 lines (warn 150, hard block 200)
[WARN] agents/monitor/tests/test_monitor_poll.py: 173 lines (warn 150, hard block 200)
[WARN] agents/monitor/tests/test_p3_monitor_slice.py: 159 lines (warn 150, hard block 200)
[WARN] agents/operator/agent.py: 175 lines (warn 150, hard block 200)
[WARN] agents/operator/domain/result.py: 154 lines (warn 150, hard block 200)
[WARN] agents/operator/tests/test_cutoff_agent.py: 157 lines (warn 150, hard block 200)
[WARN] agents/operator/tests/test_operator_agent.py: 197 lines (warn 150, hard block 200)
[WARN] agents/operator/tests/test_parameter_values.py: 173 lines (warn 150, hard block 200)
[WARN] agents/operator/tests/test_required_parameters.py: 196 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/domain/correlation.py: 185 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/domain/order_decision.py: 153 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/domain/position_gates.py: 172 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/domain/risk.py: 163 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/domain/sector_book.py: 196 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/domain/sector_gate_outcomes.py: 161 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/settings.py: 168 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_account_sizing.py: 157 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_concentration_deployed_sector.py: 177 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_correlation_concentration.py: 155 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_correlation_edges.py: 174 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_correlation_ramp.py: 152 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_issuer_concentration.py: 188 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_p3_slice.py: 166 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_pm_poll.py: 168 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_portfolio_manager_audit.py: 176 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_portfolio_manager_edges.py: 184 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_rejection_gate_reports.py: 161 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_reward_risk.py: 163 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_reward_risk_measured_excursion.py: 184 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_sector_cap.py: 158 lines (warn 150, hard block 200)
[WARN] agents/portfolio_manager/tests/test_unified_exits.py: 175 lines (warn 150, hard block 200)
[WARN] agents/provider/agent.py: 191 lines (warn 150, hard block 200)
[WARN] agents/provider/alpaca_data.py: 178 lines (warn 150, hard block 200)
[WARN] agents/provider/barrier_history.py: 179 lines (warn 150, hard block 200)
[WARN] agents/provider/domain/market_calendar.py: 178 lines (warn 150, hard block 200)
[WARN] agents/provider/fundamentals.py: 183 lines (warn 150, hard block 200)
[WARN] agents/provider/ingest.py: 191 lines (warn 150, hard block 200)
[WARN] agents/provider/ingest_chunked.py: 162 lines (warn 150, hard block 200)
[WARN] agents/provider/market_fields.py: 166 lines (warn 150, hard block 200)
[WARN] agents/provider/poll.py: 167 lines (warn 150, hard block 200)
[WARN] agents/provider/sources.py: 192 lines (warn 150, hard block 200)
[WARN] agents/provider/tests/test_barrier_history.py: 156 lines (warn 150, hard block 200)
[WARN] agents/provider/tests/test_barrier_window_as_of.py: 162 lines (warn 150, hard block 200)
[WARN] agents/provider/tests/test_domain.py: 187 lines (warn 150, hard block 200)
[WARN] agents/provider/tests/test_earnings_source.py: 182 lines (warn 150, hard block 200)
[WARN] agents/provider/tests/test_ingest.py: 175 lines (warn 150, hard block 200)
[WARN] agents/provider/tests/test_ingest_chunked.py: 198 lines (warn 150, hard block 200)
[WARN] agents/provider/tests/test_newest_session_guard.py: 157 lines (warn 150, hard block 200)
[WARN] agents/provider/tests/test_provider_agent.py: 181 lines (warn 150, hard block 200)
[WARN] agents/provider/tests/test_provider_benchmark_ingest.py: 161 lines (warn 150, hard block 200)
[WARN] agents/provider/tests/test_sources.py: 169 lines (warn 150, hard block 200)
[WARN] agents/reporter/domain/lineage.py: 179 lines (warn 150, hard block 200)
[WARN] agents/reporter/result.py: 162 lines (warn 150, hard block 200)
[WARN] agents/reporter/tests/helpers.py: 158 lines (warn 150, hard block 200)
[WARN] agents/reporter/tests/p3_helpers.py: 197 lines (warn 150, hard block 200)
[WARN] agents/reporter/tests/test_book_window.py: 164 lines (warn 150, hard block 200)
[WARN] agents/reporter/tests/test_book_window_edges.py: 150 lines (warn 150, hard block 200)
[WARN] agents/reporter/tests/test_performance.py: 160 lines (warn 150, hard block 200)
[WARN] agents/reporter/tests/test_performance_snapshot.py: 162 lines (warn 150, hard block 200)
[WARN] agents/reporter/tests/test_reporter_agent.py: 191 lines (warn 150, hard block 200)
[WARN] agents/reporter/tests/test_trade_outcomes.py: 184 lines (warn 150, hard block 200)
[WARN] agents/researcher/domain/backtest.py: 197 lines (warn 150, hard block 200)
[WARN] agents/researcher/domain/factors.py: 159 lines (warn 150, hard block 200)
[WARN] agents/researcher/tests/test_backtest.py: 164 lines (warn 150, hard block 200)
[WARN] agents/scanner/agent.py: 184 lines (warn 150, hard block 200)
[WARN] agents/scanner/tests/test_scanner_agent.py: 190 lines (warn 150, hard block 200)
[WARN] agents/scanner/tests/test_scanner_earnings.py: 188 lines (warn 150, hard block 200)
[WARN] agents/supervisor/agent.py: 173 lines (warn 150, hard block 200)
[WARN] agents/supervisor/domain/gate.py: 180 lines (warn 150, hard block 200)
[WARN] agents/supervisor/store.py: 162 lines (warn 150, hard block 200)
[WARN] agents/supervisor/tests/test_supervisor_agent.py: 181 lines (warn 150, hard block 200)
[WARN] agents/supervisor/tests/test_supervisor_health_flags.py: 196 lines (warn 150, hard block 200)
[WARN] orchestration/batch_trace.py: 198 lines (warn 150, hard block 200)
[WARN] orchestration/container_alarm_text.py: 183 lines (warn 150, hard block 200)
[WARN] orchestration/container_events.py: 181 lines (warn 150, hard block 200)
[WARN] orchestration/container_sensor.py: 179 lines (warn 150, hard block 200)
[WARN] orchestration/container_sensor_guard.py: 160 lines (warn 150, hard block 200)
[WARN] orchestration/daily_brief_facts.py: 170 lines (warn 150, hard block 200)
[WARN] orchestration/daily_brief_text.py: 183 lines (warn 150, hard block 200)
[WARN] orchestration/local_pipeline.py: 198 lines (warn 150, hard block 200)
[WARN] orchestration/packs/trading_deliberation_view.py: 162 lines (warn 150, hard block 200)
[WARN] orchestration/packs/trading_vault_probes.py: 187 lines (warn 150, hard block 200)
[WARN] orchestration/resume.py: 194 lines (warn 150, hard block 200)
[WARN] orchestration/scheduled_dispatch.py: 179 lines (warn 150, hard block 200)
[WARN] orchestration/scheduled_dispatch_human.py: 175 lines (warn 150, hard block 200)
[WARN] orchestration/shadow_book.py: 183 lines (warn 150, hard block 200)
[WARN] orchestration/tests/daily_brief_fixtures.py: 164 lines (warn 150, hard block 200)
[WARN] orchestration/tests/helpers.py: 196 lines (warn 150, hard block 200)
[WARN] orchestration/tests/shadow_book_helpers.py: 182 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_batch_trace.py: 187 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_container_env.py: 168 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_container_faults.py: 158 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_container_platform.py: 158 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_container_reader.py: 157 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_container_sensor.py: 198 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_daily_brief_boundaries.py: 185 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_deploy_record_verification.py: 167 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_dispatcher_capability.py: 150 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_forecaster_stage.py: 171 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_graph_pull_e2e.py: 158 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_graph_vocabulary_e2e.py: 166 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_realized_pnl_graph_pull.py: 160 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_resume.py: 173 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_scheduled_dispatch_degraded_readiness.py: 171 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_scheduled_dispatch_notices.py: 179 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_scheduled_dispatch_once.py: 198 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_scheduled_dispatch_polling.py: 199 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_scheduled_dispatch_readiness.py: 198 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_shadow_book_derivation.py: 183 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_shadow_book_scorecard.py: 153 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_trace_deliberation.py: 185 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_trading_acceptance.py: 154 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_trading_acceptance_deliberation.py: 190 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_trading_deliberation_not_required.py: 172 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_trading_deliberation_unvetoed.py: 175 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_trading_observatory.py: 159 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_trading_vault_probes.py: 180 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_unified_decision_run.py: 185 lines (warn 150, hard block 200)
[WARN] orchestration/tests/test_veto_stage.py: 193 lines (warn 150, hard block 200)
[WARN] surfaces/dashboard/app.py: 184 lines (warn 150, hard block 200)
[WARN] surfaces/dashboard/azure_rest.py: 189 lines (warn 150, hard block 200)
[WARN] surfaces/dashboard/github_builds.py: 180 lines (warn 150, hard block 200)
[WARN] surfaces/dashboard/llm_costs.py: 185 lines (warn 150, hard block 200)
[WARN] surfaces/dashboard/projections_fleet.py: 195 lines (warn 150, hard block 200)
[WARN] surfaces/dashboard/projections_state.py: 184 lines (warn 150, hard block 200)
[WARN] surfaces/dashboard/projections_verdict.py: 176 lines (warn 150, hard block 200)
[WARN] surfaces/dashboard/read_cache.py: 174 lines (warn 150, hard block 200)
[WARN] surfaces/dashboard/settings.py: 178 lines (warn 150, hard block 200)
[WARN] surfaces/dashboard/time_windows.py: 152 lines (warn 150, hard block 200)
[WARN] surfaces/mcp_server.py: 160 lines (warn 150, hard block 200)
[WARN] surfaces/mcp_tools.py: 152 lines (warn 150, hard block 200)
[WARN] surfaces/operator_tools.py: 152 lines (warn 150, hard block 200)
[WARN] surfaces/render.py: 167 lines (warn 150, hard block 200)
[WARN] surfaces/tests/scorecard_fixtures.py: 198 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_cli_narrative_approve.py: 150 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_dashboard_app.py: 180 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_dashboard_azure_rest.py: 197 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_dashboard_chat.py: 198 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_dashboard_projections.py: 199 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_dashboard_readiness.py: 191 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_dashboard_reholds.py: 159 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_dashboard_state.py: 190 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_dashboard_verdict.py: 176 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_github_build_tag_attempts.py: 152 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_github_build_tag_guards.py: 198 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_github_builds.py: 195 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_lifecycle_flags.py: 190 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_performance_scoreboard.py: 158 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_scorecard_chat.py: 184 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_scorecard_g1_g3.py: 176 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_scorecard_tile.py: 198 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_scorecard_verdicts.py: 169 lines (warn 150, hard block 200)
[WARN] surfaces/tests/test_status_fleet_check.py: 153 lines (warn 150, hard block 200)
[WARN] tests/fidelity_fleet.py: 177 lines (warn 150, hard block 200)
[WARN] tests/fidelity_fleet_data.py: 194 lines (warn 150, hard block 200)
[WARN] tests/fidelity_harness.py: 176 lines (warn 150, hard block 200)
[WARN] tests/graph_postgres_fakes.py: 199 lines (warn 150, hard block 200)
[WARN] tests/law_coverage_fixtures.py: 153 lines (warn 150, hard block 200)
[WARN] tests/poll_payload_remaining.py: 157 lines (warn 150, hard block 200)
[WARN] tests/replay_history_fixtures.py: 155 lines (warn 150, hard block 200)
[WARN] tests/switch_llm_testkit.py: 160 lines (warn 150, hard block 200)
[WARN] tests/test_audit_broker_graph.py: 173 lines (warn 150, hard block 200)
[WARN] tests/test_barrier_testbed.py: 152 lines (warn 150, hard block 200)
[WARN] tests/test_bootstrap.py: 179 lines (warn 150, hard block 200)
[WARN] tests/test_broker_stop_liveness.py: 158 lines (warn 150, hard block 200)
[WARN] tests/test_bus_azure_config.py: 171 lines (warn 150, hard block 200)
[WARN] tests/test_bus_azure_receiver.py: 191 lines (warn 150, hard block 200)
[WARN] tests/test_bus_celery.py: 197 lines (warn 150, hard block 200)
[WARN] tests/test_check_dependency_audit.py: 187 lines (warn 150, hard block 200)
[WARN] tests/test_check_llm_outage_cli.py: 156 lines (warn 150, hard block 200)
[WARN] tests/test_check_markdown_links.py: 151 lines (warn 150, hard block 200)
[WARN] tests/test_check_tracker_size.py: 165 lines (warn 150, hard block 200)
[WARN] tests/test_claim_check.py: 184 lines (warn 150, hard block 200)
[WARN] tests/test_config.py: 162 lines (warn 150, hard block 200)
[WARN] tests/test_contract_values.py: 173 lines (warn 150, hard block 200)
[WARN] tests/test_deliberate_script.py: 166 lines (warn 150, hard block 200)
[WARN] tests/test_deliberation.py: 193 lines (warn 150, hard block 200)
[WARN] tests/test_deliberation_eval.py: 155 lines (warn 150, hard block 200)
[WARN] tests/test_deliberation_guided_text.py: 159 lines (warn 150, hard block 200)
[WARN] tests/test_deliberation_prompt_artifacts.py: 168 lines (warn 150, hard block 200)
[WARN] tests/test_deliberator_reply_inbox.py: 199 lines (warn 150, hard block 200)
[WARN] tests/test_deliberator_runtime.py: 188 lines (warn 150, hard block 200)
[WARN] tests/test_deploy_script_invariants.py: 169 lines (warn 150, hard block 200)
[WARN] tests/test_exit_verdict_cli.py: 174 lines (warn 150, hard block 200)
[WARN] tests/test_export_tiingo_bars.py: 165 lines (warn 150, hard block 200)
[WARN] tests/test_fault_graph.py: 151 lines (warn 150, hard block 200)
[WARN] tests/test_fidelity_export.py: 151 lines (warn 150, hard block 200)
[WARN] tests/test_fidelity_export_edges.py: 155 lines (warn 150, hard block 200)
[WARN] tests/test_gate_selftest_runner.py: 173 lines (warn 150, hard block 200)
[WARN] tests/test_graph.py: 155 lines (warn 150, hard block 200)
[WARN] tests/test_graph_postgres.py: 183 lines (warn 150, hard block 200)
[WARN] tests/test_graph_vocabulary_completeness.py: 194 lines (warn 150, hard block 200)
[WARN] tests/test_graph_vocabulary_properties.py: 152 lines (warn 150, hard block 200)
[WARN] tests/test_law_coverage_assertions.py: 172 lines (warn 150, hard block 200)
[WARN] tests/test_llm_outage.py: 172 lines (warn 150, hard block 200)
[WARN] tests/test_metrics.py: 177 lines (warn 150, hard block 200)
[WARN] tests/test_operator_responses.py: 153 lines (warn 150, hard block 200)
[WARN] tests/test_param_law_sync.py: 168 lines (warn 150, hard block 200)
[WARN] tests/test_pg_teardown_targets.py: 186 lines (warn 150, hard block 200)
[WARN] tests/test_poll_payloads.py: 165 lines (warn 150, hard block 200)
[WARN] tests/test_positions_contract.py: 153 lines (warn 150, hard block 200)
[WARN] tests/test_prompt_recipe.py: 185 lines (warn 150, hard block 200)
[WARN] tests/test_replay_arms.py: 189 lines (warn 150, hard block 200)
[WARN] tests/test_replay_day.py: 196 lines (warn 150, hard block 200)
[WARN] tests/test_replay_exit_policy.py: 161 lines (warn 150, hard block 200)
[WARN] tests/test_replay_exit_runs.py: 164 lines (warn 150, hard block 200)
[WARN] tests/test_replay_fidelity.py: 182 lines (warn 150, hard block 200)
[WARN] tests/test_replay_history_rule.py: 165 lines (warn 150, hard block 200)
[WARN] tests/test_replay_ledger.py: 172 lines (warn 150, hard block 200)
[WARN] tests/test_replay_rounds.py: 171 lines (warn 150, hard block 200)
[WARN] tests/test_replay_runner_progress.py: 155 lines (warn 150, hard block 200)
[WARN] tests/test_replay_universe.py: 199 lines (warn 150, hard block 200)
[WARN] tests/test_replay_verdict_stats.py: 175 lines (warn 150, hard block 200)
[WARN] tests/test_retrain_return_model.py: 169 lines (warn 150, hard block 200)
[WARN] tests/test_score_arithmetic_analyst.py: 154 lines (warn 150, hard block 200)
[WARN] tests/test_sp500_context.py: 153 lines (warn 150, hard block 200)
[WARN] tests/test_veto_context.py: 158 lines (warn 150, hard block 200)
[WARN] tests/test_veto_context_verdict_attribution.py: 165 lines (warn 150, hard block 200)
[WARN] tests/test_work_loop.py: 175 lines (warn 150, hard block 200)
[WARN] tests/test_work_loop_quarantine.py: 196 lines (warn 150, hard block 200)
[WARN] tests/veto_context_fixtures.py: 165 lines (warn 150, hard block 200)
[WARN] scripts/_audit_broker_graph_impl.py: 177 lines (warn 150, hard block 200)
[WARN] scripts/assert_gate_ran.py: 192 lines (warn 150, hard block 200)
[WARN] scripts/backtest_proposal.py: 156 lines (warn 150, hard block 200)
[WARN] scripts/barrier_testbed.py: 164 lines (warn 150, hard block 200)
[LEGACY] scripts/check_law_coverage.py: 228 lines (ceiling 228)
[LEGACY] scripts/check_markdown_links.py: 220 lines (ceiling 220)
[WARN] scripts/check_sprint_status.py: 150 lines (warn 150, hard block 200)
[LEGACY] scripts/compare_deliberation_prompts.py: 363 lines (ceiling 363)
[WARN] scripts/compare_order_tolerances.py: 175 lines (warn 150, hard block 200)
[WARN] scripts/compare_stop_targets.py: 198 lines (warn 150, hard block 200)
[WARN] scripts/compile_deliberation_prompts.py: 170 lines (warn 150, hard block 200)
[WARN] scripts/debate_lanes_scene.py: 183 lines (warn 150, hard block 200)
[LEGACY] scripts/deliberate.py: 246 lines (ceiling 246)
[WARN] scripts/deliberation_eval.py: 180 lines (warn 150, hard block 200)
[LEGACY] scripts/deliberation_gate.py: 230 lines (ceiling 230)
[LEGACY] scripts/deliberation_replay_batch.py: 240 lines (ceiling 240)
[WARN] scripts/dependency_audit_rules.py: 183 lines (warn 150, hard block 200)
[LEGACY] scripts/evaluate_return_model.py: 288 lines (ceiling 288)
[WARN] scripts/exp013_regime_sizing.py: 156 lines (warn 150, hard block 200)
[WARN] scripts/export_tiingo_bars.py: 198 lines (warn 150, hard block 200)
[WARN] scripts/fidelity_exporter.py: 152 lines (warn 150, hard block 200)
[WARN] scripts/gate_selftest.py: 154 lines (warn 150, hard block 200)
[LEGACY] scripts/gate_selftest_cases.py: 346 lines (ceiling 346)
[WARN] scripts/gate_selftest_invariants.py: 186 lines (warn 150, hard block 200)
[WARN] scripts/guided_turn_replay.py: 174 lines (warn 150, hard block 200)
[WARN] scripts/law_coverage_docs.py: 185 lines (warn 150, hard block 200)
[WARN] scripts/law_coverage_tests.py: 156 lines (warn 150, hard block 200)
[WARN] scripts/mine_factors.py: 196 lines (warn 150, hard block 200)
[WARN] scripts/param_law_sync.py: 190 lines (warn 150, hard block 200)
[WARN] scripts/param_law_sync_sources.py: 155 lines (warn 150, hard block 200)
[WARN] scripts/pg_role_plan.py: 153 lines (warn 150, hard block 200)
[WARN] scripts/pg_teardown_targets.py: 198 lines (warn 150, hard block 200)
[WARN] scripts/repair_close_pnl.py: 180 lines (warn 150, hard block 200)
[WARN] scripts/replay_arms.py: 166 lines (warn 150, hard block 200)
[WARN] scripts/replay_broker.py: 160 lines (warn 150, hard block 200)
[WARN] scripts/replay_day.py: 180 lines (warn 150, hard block 200)
[WARN] scripts/replay_exits.py: 196 lines (warn 150, hard block 200)
[WARN] scripts/replay_fidelity_layers.py: 162 lines (warn 150, hard block 200)
[WARN] scripts/replay_ledger.py: 189 lines (warn 150, hard block 200)
[WARN] scripts/replay_marks.py: 194 lines (warn 150, hard block 200)
[WARN] scripts/replay_session.py: 193 lines (warn 150, hard block 200)
[WARN] scripts/replay_universe.py: 199 lines (warn 150, hard block 200)
[WARN] scripts/replay_universe_cache.py: 165 lines (warn 150, hard block 200)
[WARN] scripts/replay_verdict_score.py: 168 lines (warn 150, hard block 200)
[WARN] scripts/retrain_return_model_helpers.py: 168 lines (warn 150, hard block 200)
[LEGACY] scripts/run_local.py: 227 lines (ceiling 227)
[WARN] scripts/sb_sas_azure.py: 169 lines (warn 150, hard block 200)
[WARN] scripts/sb_sas_live_ops.py: 198 lines (warn 150, hard block 200)
[LEGACY] scripts/sb_sas_plan.py: 211 lines (ceiling 212)
[WARN] scripts/servicebus_receiver_live_check.py: 171 lines (warn 150, hard block 200)
[LEGACY] scripts/servicebus_request.py: 216 lines (ceiling 216)
[WARN] scripts/sp500_bars.py: 170 lines (warn 150, hard block 200)
[WARN] scripts/sp500_context.py: 194 lines (warn 150, hard block 200)
[WARN] scripts/sp500_membership.py: 181 lines (warn 150, hard block 200)
[WARN] scripts/sp500_wiki.py: 197 lines (warn 150, hard block 200)
[WARN] scripts/switch_llm_provider.py: 154 lines (warn 150, hard block 200)
[LEGACY] scripts/vocabulary_resolution.py: 268 lines (ceiling 268)
[WARN] scripts/vocabulary_signatures.py: 152 lines (warn 150, hard block 200)
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 — UCITS investment powers and limits
[WARN] portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later
uv run python scripts/check_sprint_status.py
docs/sprints/chore-an-accepted-advisory-re-checks-itself.md: MERGED | **Status:** MERGED `750ac98`
docs/sprints/chore-deploy-pack-off-the-command-line.md: MERGED | **Status:** MERGED — merged to `main` in `976d27ec` (item 22 review, 2026-09-23); the line read: SPEC — packaged 2026-08-02, **blocking the `:s155` deploy**
docs/sprints/chore-deploy-s158.md: MERGED | **Status:** MERGED — executed 2026-08-04 per its README row; an operational chore has no branch, so MERGED records it done (item 22 review, 2026-09-23); the line read: SPEC — packaged 2026-08-04, **awaiting operator approval to execute**
docs/sprints/chore-exec-fail-03-coverage.md: MERGED | **Status:** MERGED — SHIPPED — see [Closeout](#closeout)
docs/sprints/chore-flatten-and-resize.md: MERGED | **Status:** MERGED — executed 2026-08-07 on `:s164` per its README row, after S163 + S164 unblocked it; an operational chore has no branch, so MERGED records it done (item 22 review, 2026-09-23); the line read: 🔴 **BLOCKED** — operator said go 2026-08-07; the baseline step found the flatten cannot execute. See **[DL-95](../design-log.md)**: all ten positions have `qty_available = 0` because each is fully reserved by its own resting `gtc` stop, and nothing in `execute_pm_node` cancels a stop for a ticker being sold. **Nothing was changed** — no env var set, no run fired, no order placed. Unblocks after the exit-cancels-its-stop fix
docs/sprints/chore-one-sector-rejection.md: MERGED | **Status:** MERGED — merged to `main` in `9417df39` (item 22 review, 2026-09-23)
docs/sprints/chore-openai-cutover.md: MERGED | **Status:** MERGED — merged to `main` in `8b30624e` (item 22 review, 2026-09-23)
docs/sprints/chore-split-modules-before-the-block.md: MERGED | **Status:** MERGED — merged to `main` in `63cba7a0` (item 22 review, 2026-09-23)
docs/sprints/chore-teardown-leaves-no-orphans.md: MERGED | **Status:** MERGED — merged to `main` in `9d6243c3` (item 22 review, 2026-09-23)
docs/sprints/chore-three-scripts-leave-the-size-baseline.md: MERGED | **Status:** MERGED 2026-10-08 — no bump, fast-forwarded to `7bbf8737`, GATE PROVEN `7bbf8737` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (4,392 passed, 8 skipped, 100.00 %, dependency audit clean); built by a Claude cloud session on 2026-10-03; the three scripts are 128, 112 and 168 lines and `LEGACY_MAX_LINES` lists 12; the planner's own re-measure: 46 of 47 definitions identical as syntax trees and none missing, both scripts print the same bytes before and after the split, two plants of the size ratchet each red; open CodeQL alerts 127, the same as `main`'s, none new; no deploy (the scripts ship in no image)
docs/sprints/chore-wsl2-dev-env.md: SPEC | **Status:** SPEC — ready for handover (packaged 2026-07-21)
docs/sprints/s127-fixpack-backlog.md: MERGED | **Status:** MERGED — a backlog, not a spec: all 12 rows are marked FIXED, shipped through S127 and S129 (item 22 review, 2026-09-23)
docs/sprints/sprint-01-kernel-runtime.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `97c9db7`) · **Branch:** `sprint-01-kernel-runtime` · **Build phase:** P1 (first slice)
docs/sprints/sprint-02-persistence.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `ad53a5d`) · **Branch:** `sprint-02-persistence` · **Build phase:** P1 (second slice)
docs/sprints/sprint-03-neo4j-store.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `ba2f42c`) · **Branch:** `sprint-03-neo4j-store` · **Build phase:** P1 (storage pivot)
docs/sprints/sprint-04-provider-agent.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `fd1df0c`) · **Branch:** `sprint-04-provider-agent` · **Build phase:** P2 (first vertical slice)
docs/sprints/sprint-05-scanner-agent.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `0898be1`) · **Branch:** `sprint-05-scanner-agent` · **Build phase:** P2 (first vertical slice)
docs/sprints/sprint-06-analyst-agent.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `d44f8f2`; **P2 exit met**) · **Branch:** `sprint-06-analyst-agent` · **Build phase:** P2 (first vertical slice — exit)
docs/sprints/sprint-07-distributed-bus.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `4f4f0f2`; P1 bus exit met) · **Branch:** `sprint-07-distributed-bus` · **Build phase:** P1 (kernel runtime — bus completion)
docs/sprints/sprint-08-observability-adapter.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `515a713`) · **Branch:** `sprint-08-observability-adapter` · **Build phase:** P1 (kernel runtime — observability emission)
docs/sprints/sprint-09-portfolio-manager.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `6a36a3a`; audit-truth follow-ups → hardening sprint) · **Branch:** `sprint-09-portfolio-manager` · **Build phase:** P3 (decision loop)
docs/sprints/sprint-10-hardening.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `3bd1c25`) · **Branch:** `sprint-10-hardening` · **Build phase:** P3 (foundation hardening) · **Effort: L**
docs/sprints/sprint-100-servicebus-receiver.md: MERGED | **Status:** MERGED — tag `v0.61.00` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: closed on branch for operator review (re-based 2026-07-07 onto the 0.60.01 codebase; shipped branch version 0.61.00)
docs/sprints/sprint-101-permanent-graph-store.md: SPEC | **Status:** SPEC — planned
docs/sprints/sprint-102-fleet-run-through.md: MERGED | **Status:** MERGED — shipped — merged `3049955` (0.62.00, 2026-07-08); closeout evidence below
docs/sprints/sprint-103-dispatcher-cron.md: MERGED | **Status:** MERGED — shipped — merged `6caa2f6` (0.63.00, 2026-07-08); closeout evidence below
docs/sprints/sprint-104-credential-tested-activation.md: MERGED | **Status:** MERGED — shipped (0.44.01 → 0.45.00) — A+B core (test-before-handover + Escalation/refuse + mode/one-shot structure). Live domain-test injection (pack) + C/D deferred.
docs/sprints/sprint-105-master-secret-cache.md: MERGED | **Status:** MERGED — shipped (0.45.00 → 0.46.00)
docs/sprints/sprint-106-remediation-planner.md: MERGED | **Status:** MERGED — shipped (0.46.00 → 0.47.00)
docs/sprints/sprint-107-remediation-execution.md: MERGED | **Status:** MERGED — shipped
docs/sprints/sprint-108-vault-seeder.md: MERGED | **Status:** MERGED — shipped
docs/sprints/sprint-109-heterogeneous-deliberation-models.md: MERGED | **Status:** MERGED — shipped (0.51.00 → 0.52.00; **live-Opus closeout deferred** — see Closeout evidence)
docs/sprints/sprint-11-execution.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `50e1911`) · **Branch:** `sprint-11-execution` · **Build phase:** P3 (decision loop) · **Effort: L**
docs/sprints/sprint-110-signal-evaluation-battery.md: MERGED | **Status:** MERGED — shipped on branch (`sprint-110-signal-evaluation-battery`) — code + Tiingo live check
docs/sprints/sprint-111-rolling-retrain.md: MERGED | **Status:** MERGED — shipped on branch (`sprint-111-rolling-retrain`) — code + Tiingo live check complete;
docs/sprints/sprint-112-researcher-backtest-evidence.md: MERGED | **Status:** MERGED — shipped on branch — pending operator review/merge; S111 is merged (`45f6c34`) and the
docs/sprints/sprint-113-governed-factor-proposal.md: MERGED | **Status:** MERGED — tag `v0.57.00` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: ready for handover — from `main` (S112 merged `feb7f87`, S109 re-run merged `b60fc6f`)
docs/sprints/sprint-114-complete-deliberation-evidence.md: MERGED | **Status:** MERGED — shipped — implemented on `sprint-114-complete-deliberation-evidence`; awaiting operator review/merge
docs/sprints/sprint-115-factor-shadow-signal.md: MERGED | **Status:** MERGED — tag `v0.58.00` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: ready for handover — from `main` (S113 merged `3ec2d9e`, 0.57.00)
docs/sprints/sprint-116-postgres-graphstore.md: MERGED | **Status:** MERGED — tag `v0.59.00` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: ready for handover — from `main` (S115 merged `ab66caf`, 0.58.00)
docs/sprints/sprint-117-postgres-fleet-swap.md: MERGED | **Status:** MERGED — tag `v0.60.00` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: closed on branch — not merged/pushed (S116 merged `5f11b93`, 0.60.00)
docs/sprints/sprint-118-neo4j-ripout.md: MERGED | **Status:** MERGED — tag `v0.60.01` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: closed on branch — not merged/pushed (S117 merged `d6776ec`, 0.60.00)
docs/sprints/sprint-119-dspy-deliberation-roles.md: MERGED | **Status:** MERGED — tag `v0.64.00` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-08)
docs/sprints/sprint-12-monitor.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `f0a2e60`) · **Branch:** `sprint-12-monitor` · **Build phase:** P3 (decision loop) · **Effort: L**
docs/sprints/sprint-120-broker-reconciliation.md: MERGED | **Status:** MERGED — tag `v0.65.00` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-08; execute after S119 merges)
docs/sprints/sprint-121-judge-promotion-challenger-recompile.md: MERGED | **Status:** MERGED — tag `v0.65.01` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-08; execute after S120 merges)
docs/sprints/sprint-122-dashboard-run-view.md: MERGED | **Status:** MERGED — tag `v0.66.00` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-10; amended same day — `/bundle` endpoint added
docs/sprints/sprint-123-dashboard-fleet-infra.md: MERGED | **Status:** MERGED — `2ad656e` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-10)
docs/sprints/sprint-124-dashboard-verdict.md: MERGED | **Status:** MERGED — `b9ed20e` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-11)
docs/sprints/sprint-125-operator-chat.md: MERGED | **Status:** MERGED — merged to `main` in `9420b785` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-12)
docs/sprints/sprint-126-resume-and-tripwire.md: MERGED | **Status:** MERGED — merged to `main` in `297354ba` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-14)
docs/sprints/sprint-127-fixpack.md: MERGED | **Status:** MERGED — merged to `main` in `32c73cc3` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-15)
docs/sprints/sprint-128-feed-resilience.md: MERGED | **Status:** MERGED — merged to `main` in `09120b3c` (item 22 review, 2026-09-23); the line read: live check complete (2026-07-19) — code handback 2026-07-16, live proof after DRIFT-023 resolved
docs/sprints/sprint-129-fixpack.md: MERGED | **Status:** MERGED — `3be1ee8` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-19)
docs/sprints/sprint-13-reporter.md: MERGED | **Status:** MERGED — shipped (merged to `main` @ `ab328a5`) · **Branch:** `sprint-13-reporter` · **Build phase:** P3 (decision loop) · **Effort: M**
docs/sprints/sprint-130-base-image.md: MERGED | **Status:** MERGED — merged to `main` in `8aefe2af` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-19)
docs/sprints/sprint-131-blast-radius.md: MERGED | **Status:** MERGED — merged to `main` in `0ca74596` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-20)
docs/sprints/sprint-132-mutation-testing.md: MERGED | **Status:** MERGED — merged to `main` in `15c23d6f` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-20)
docs/sprints/sprint-133-servicebus-sas.md: MERGED | **Status:** MERGED — merged to `main` in `160641f3` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-20)
docs/sprints/sprint-134-assertion-hardening.md: MERGED | **Status:** MERGED — merged to `main` in `d8312605` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-21)
docs/sprints/sprint-135-unified-decision-run.md: MERGED | **Status:** MERGED — ✅ shipped 2026-07-23 (0.74.00) — merged `1b858e7`, deployed `:s136`
docs/sprints/sprint-136-realized-pnl-and-gate-integrity.md: MERGED | **Status:** MERGED — merged to `main` in `b4351832` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-24)
docs/sprints/sprint-137-exit-authority.md: MERGED | **Status:** MERGED — SHIPPED 0.76.00 — merged `29a36f4`, fleet `:s141`, functionality check PROVEN
docs/sprints/sprint-138-broker-native-stops.md: MERGED | **Status:** MERGED — merged to `main` in `ca57fff0` (item 22 review, 2026-09-23); the line read: ready for handover (packaged 2026-07-25)
docs/sprints/sprint-14-dispatcher.md: MERGED | **Status:** MERGED — `7790aa4f` on `main` (Implement Sprint 14 dispatcher) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-14-dispatcher` · **Build phase:** P4 (orchestration) · **Effort: M**
docs/sprints/sprint-143-graph-vocabulary.md: MERGED | **Status:** MERGED — SHIPPED 0.79.00 — merged `798bfd4`, `make ci` 1841 passed / 100.00 %, both remote gates
docs/sprints/sprint-144-vocabulary-live.md: MERGED | **Status:** MERGED — SHIPPED 0.80.00 — merged `d215a76`, `make ci` 1851 passed / 100.00 %, all four remote
docs/sprints/sprint-145-exit-replay-append-safe.md: MERGED | **Status:** MERGED — `2c49f88` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: SPEC — 🔴 **execution is currently bricked in production; this is a fix, not a feature**
docs/sprints/sprint-146-unprotected-position.md: MERGED | **Status:** MERGED — `7b06662` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: SPEC — 🟠 **96 ABT shares (~$10k) have carried no protective stop since a 403**
docs/sprints/sprint-147-fresh-book-before-decision.md: MERGED | **Status:** MERGED — merged to `main` in `2989acb2` (item 22 review, 2026-09-23); the line read: SPEC — closes the **upstream cause** of the 2026-07-27 outage
docs/sprints/sprint-148-decision-valid-one-session.md: MERGED | **Status:** MERGED — merged to `main` in `314fb8b0` (item 22 review, 2026-09-23); the line read: SPEC — 🔴 **the largest measured cost in the system: ≈ −$2,850 across two exits**
docs/sprints/sprint-149-volatility-scaled-tolerance.md: MERGED | **Status:** MERGED — merged to `main` in `eee68d1c` (item 22 review, 2026-09-23); the line read: SPEC — measured challenger to S148's flat tolerance; **ships OFF by default**
docs/sprints/sprint-15-supervisor.md: MERGED | **Status:** MERGED — `8abbe3cb` on `main` (Implement Sprint 15 supervisor lineage) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-15-supervisor` · **Build phase:** P4 (orchestration) · **Effort: M**
docs/sprints/sprint-150-volatility-scaled-stops.md: MERGED | **Status:** MERGED — merged to `main` in `ca977977` (item 22 review, 2026-09-23); the line read: SPEC — measured challenger to the flat stop distance; **ships OFF by default**
docs/sprints/sprint-151-drop-sweep-append-safe.md: MERGED | **Status:** MERGED — merged to `main` in `8f57f5f3` (item 22 review, 2026-09-23); the line read: SPEC — 🔴 **live outage.** `sched-2026-07-30` reached **2/8 stages**; the fleet ran the
docs/sprints/sprint-152-law-amendment-cycle.md: MERGED | **Status:** MERGED — merged to `main` in `4524da53` (item 22 review, 2026-09-23); the line read: SPEC — packaged 2026-07-31, **not yet handed to a coding agent**
docs/sprints/sprint-153-deliberator-agent.md: MERGED | **Status:** MERGED — merged to `main` in `f32581a2` (item 22 review, 2026-09-23); the line read: SPEC — packaged 2026-07-31, **refreshed 2026-08-01** against the live spine and the
docs/sprints/sprint-154-fill-refresh-terminal.md: MERGED | **Status:** MERGED — merged to `main` in `676362a6` (item 22 review, 2026-09-23); the line read: SPEC — 🟠 **not an outage.** Every run is green; the defect is unbounded write growth
docs/sprints/sprint-155-bounded-retry-and-fault-containment.md: MERGED | **Status:** MERGED — merged to `main` in `4091d6c6` (item 22 review, 2026-09-23); the line read: SPEC — packaged 2026-08-01
docs/sprints/sprint-156-law-coverage-is-checkable.md: MERGED | **Status:** MERGED — SHIPPED — merged `23ae35f`, `v0.86.00`; closes hardening rows **R** and **R²**, puts **O** into warn-only shadow
docs/sprints/sprint-158-fail-open-must-be-loud.md: MERGED | **Status:** MERGED — SHIPPED — merged `8be1570`, `v0.86.01`. **NOT DEPLOYED** — the fleet is on `:s155`, so none of this is protecting a live run yet
docs/sprints/sprint-159-tests-never-transact.md: MERGED | **Status:** MERGED — `56a157b` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: SPEC — closes hardening **row T**, whose open question is now answered
docs/sprints/sprint-16-operator.md: MERGED | **Status:** MERGED — `0b5aaa8c` on `main` (Implement Sprint 16 operator agent) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-16-operator` · **Build phase:** P5 (operator + supervisor safety) · **Effort: M**
docs/sprints/sprint-160-shadow-book.md: MERGED | **Status:** MERGED — `2865c5e` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: SPEC **revision 2** — makes selection quality measurable without spending capital.
docs/sprints/sprint-161-pm-knows-what-it-paid.md: MERGED | **Status:** MERGED — `802b1c6` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: SPEC — closes the margin defect that gates every DL-93 decision
docs/sprints/sprint-162-rejections-name-every-gate.md: MERGED | **Status:** MERGED — SHIPPED — merged to `main` 2026-08-07 after independent re-verification of `376fb6b`
docs/sprints/sprint-163-an-exit-cancels-its-own-stop.md: MERGED | **Status:** MERGED — merged to `main` in `a46449eb` (item 22 review, 2026-09-23); the line read: SPEC — packaged 2026-08-07; **blocks [chore-flatten-and-resize](chore-flatten-and-resize.md)**
docs/sprints/sprint-164-a-cancelled-stop-can-be-replaced.md: MERGED | **Status:** MERGED — merged to `main` in `f3b2fcfc` (item 22 review, 2026-09-23); the line read: SPEC — packaged 2026-08-07; **the last gate before [chore-flatten-and-resize](chore-flatten-and-resize.md)**
docs/sprints/sprint-165-score-every-name-not-five.md: MERGED | **Status:** MERGED — merged to `main` in `34ca6ae1` (item 22 review, 2026-09-23); the line read: SPEC — packaged 2026-08-07. 🟢 **Item 3 is already DONE and live** — `SCANNER_CANDIDATE_CAP` set to **25** on the deployed scanner 2026-08-07 (env var, no code, no deploy, no pack move; `env_prefix="SCANNER_"`). Verified: cap=25, `minReplicas=0`, `daily-agent-window` start `30 22 * * 1-5`, image `:s164` — all unchanged. **The remaining sprint is items 1, 2, 4, 5**, and item 1 is the S160 wall
docs/sprints/sprint-166-the-veto-gates-buys.md: MERGED | **Status:** MERGED — merged to `main` in `afc50889` (item 22 review, 2026-09-23)
docs/sprints/sprint-167-a-fault-count-cannot-lie.md: MERGED | **Status:** MERGED — tag `v0.89.08` (cited by its README row) is on `main` (item 22 review, 2026-09-23)
docs/sprints/sprint-169-one-switch-and-a-deploy-that-keeps-it.md: MERGED | **Status:** MERGED — tag `v0.90.10` (cited by its README row) is on `main` (item 22 review, 2026-09-23)
docs/sprints/sprint-17-supervisor-gate.md: MERGED | **Status:** MERGED — `78a3a933` on `main` (Implement Sprint 17 supervisor gate) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-17-supervisor-gate` · **Build phase:** P5 (operator + supervisor safety) · **Effort: M**
docs/sprints/sprint-170-one-llm-adapter-in-the-plumbing.md: SPEC | **Status:** SPEC — never executed as written — DL-101 was closed by S222 (`7d5528e`) instead (item 22 review, 2026-09-23)
docs/sprints/sprint-171-a-reply-must-answer-its-own-request.md: MERGED | **Status:** MERGED — `9a22102` (cited by its README row) is on `main` (item 22 review, 2026-09-23)
docs/sprints/sprint-171-HANDOVER.md: MERGED | **Status:** MERGED — companion handover note to S171, which merged (0.90.01) (item 22 review, 2026-09-23)
docs/sprints/sprint-172-independent-debates-run-independently.md: MERGED | **Status:** MERGED — `3f29c1e`, `0.95.00`, 2026-09-04
docs/sprints/sprint-173-a-verdict-must-be-reproducible.md: MERGED | **Status:** MERGED — `f875f525` on `main` (fix(s173): a round is split by payload bytes, because one 74 MB POST d) (item 22 review, 2026-09-23); the line read: CLOSED — Part A merged and proven; Part B ran one round and was stopped on price (DL-160)
docs/sprints/sprint-174-an-indicator-gets-the-history-it-declares.md: MERGED | **Status:** MERGED — `0916a1b` (cited by its README row) is on `main` (item 22 review, 2026-09-23)
docs/sprints/sprint-175-the-veto-says-only-what-it-can-prove.md: MERGED | **Status:** MERGED — `b90c09f` (cited by its README row) is on `main` (item 22 review, 2026-09-23)
docs/sprints/sprint-176-a-partial-fill-must-be-able-to-finish.md: MERGED | **Status:** MERGED — `57f540f` (cited by its README row) is on `main` (item 22 review, 2026-09-23)
docs/sprints/sprint-177-every-number-names-its-unit.md: MERGED | **Status:** MERGED — merged to `main` in `bc2a1ee5` (item 22 review, 2026-09-23)
docs/sprints/sprint-178-the-health-signal-must-be-able-to-go-green.md: MERGED | **Status:** MERGED — `fd802c2` (cited by its README row) is on `main` (item 22 review, 2026-09-23)
docs/sprints/sprint-179-a-fault-must-be-able-to-stop-being-an-incident.md: MERGED | **Status:** MERGED — `4c8eeb0` (cited by its README row) is on `main` (item 22 review, 2026-09-23)
docs/sprints/sprint-18-surfaces-cli.md: MERGED | **Status:** MERGED — shipped · **Branch:** `sprint-18-surfaces-cli` · **Build phase:** P6 (surfaces) · **Effort: M**
docs/sprints/sprint-180-a-deploy-record-must-name-the-commit-that-was-built.md: MERGED | **Status:** MERGED — `5359667` (cited by its README row) is on `main` (item 22 review, 2026-09-23)
docs/sprints/sprint-181-an-untracked-order-is-reported-once.md: MERGED | **Status:** MERGED — `7ffc730` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: implemented on branch `sprint-181-an-untracked-order-is-reported-once` as `0.90.15`.
docs/sprints/sprint-182-a-new-position-is-protected-on-the-run-that-opens-it.md: MERGED | **Status:** MERGED — `2fc0672` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: implemented on branch
docs/sprints/sprint-183-a-gate-that-did-not-run-says-so.md: MERGED | **Status:** MERGED — `4187770` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: IMPLEMENTED — local proof complete; first pushed implementation tip remote-gated.
docs/sprints/sprint-184-one-issuer-is-one-bet.md: MERGED | **Status:** MERGED — `18c41b1` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: BUILT locally on `sprint-184-one-issuer-is-one-bet`; remote `make gate-ran` is post-push
docs/sprints/sprint-185-the-veto-posture-is-declared-not-arithmetic.md: MERGED | **Status:** MERGED — `5bea06d` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: BUILT — local proof complete; remote `make gate-ran` is post-push evidence.
docs/sprints/sprint-186-a-headline-about-twenty-companies-is-not-news-about-one.md: MERGED | **Status:** MERGED — `4b0daaf` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-187-a-parameter-is-declared-once.md: MERGED | **Status:** MERGED — `7d36771` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-188-a-credential-is-tested-before-it-is-handed-over.md: MERGED | **Status:** MERGED — `5dec736` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-189-an-empty-answer-says-why-it-is-empty.md: MERGED | **Status:** MERGED — `aedb8d4` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-19-list-nodes-lifecycle.md: MERGED | **Status:** MERGED — shipped · **Branch:** `sprint-19-list-nodes-lifecycle` · **Build phase:** P6 (surfaces) · **Effort: M**
docs/sprints/sprint-190-one-liveness-question-one-answer.md: MERGED | **Status:** MERGED
docs/sprints/sprint-191-a-quiet-night-gets-the-same-verdict-twice.md: MERGED | **Status:** MERGED — `97e9fb5` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-192-a-reply-that-arrives-late-is-still-an-answer.md: SPEC | **Status:** SPEC
docs/sprints/sprint-193-a-shim-that-never-runs-is-not-a-shim.md: MERGED | **Status:** MERGED — main gate proven for implementation SHA
docs/sprints/sprint-194-a-number-nobody-records-is-a-number-nobody-has.md: MERGED | **Status:** MERGED + GATE PROVEN on `main`
docs/sprints/sprint-195-the-beta-cap-gates-on-a-benchmark-it-actually-has.md: MERGED | **Status:** MERGED
docs/sprints/sprint-196-a-filter-that-can-answer-says-so.md: MERGED | **Status:** MERGED
docs/sprints/sprint-197-a-gate-says-what-it-examined.md: MERGED | **Status:** MERGED
docs/sprints/sprint-198-a-stop-we-never-measured.md: MERGED | **Status:** MERGED
docs/sprints/sprint-199-a-token-count-comes-from-the-vendor.md: MERGED | **Status:** MERGED — `2e9355ac` on `main` (fix(s199): a recorded LLM cost is the provider's own number, and says) (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-20-narrative-approve.md: MERGED | **Status:** MERGED — shipped · **Branch:** `sprint-20-narrative-approve` · **Build phase:** P6 (surfaces) · **Effort: M**
docs/sprints/sprint-200-a-prompt-says-which-code-rendered-it.md: MERGED | **Status:** MERGED — `7761735a` on `main` (fix(s200): a recorded prompt names the code that rendered it, and the) (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-201-a-verifier-is-not-blind-where-its-subject-is.md: MERGED | **Status:** MERGED — `7c4f11b3` on `main` (fix(s201): a teardown's self-check is not blind where the teardown is) (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-202-a-probe-that-cannot-fail-is-not-an-entry-condition.md: MERGED | **Status:** MERGED — `c1ff150e` on `main` (feat(s202): a credential probe that cannot fail is not an entry condit) (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-203-a-check-that-cannot-fail-says-so.md: MERGED | **Status:** MERGED — `e890f93` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-204-every-clause-declares-how-it-is-proven.md: MERGED | **Status:** MERGED — `24d61f0` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-205-a-type-clause-names-the-fields-it-requires.md: MERGED | **Status:** MERGED `af75079` (`0.98.03`), 2026-09-15
docs/sprints/sprint-206-a-rendered-verdict-names-the-check-that-produced-it.md: MERGED | **Status:** MERGED — SHIPPED
docs/sprints/sprint-207-a-bound-cites-the-evidence-that-set-it.md: MERGED | **Status:** MERGED `d0b4cee` (`0.104.00`) · `GATE PROVEN` for `c484aea` · work-queue item 63 closed · NOT DEPLOYED
docs/sprints/sprint-208-a-risk-gate-says-what-it-can-reject.md: MERGED | **Status:** MERGED `d43280e` · **DEPLOYED `s208`**, 2026-09-16 — gate proven on the merged SHA `773c02e` (CI, CodeQL, Security Findings, image build); 16/16 apps + `dispatcher-cron` retagged, all three injected packs byte-identical, KEDA zero drift, `DeployRecord …:s208:773c02e…`. Live check owed after `sched-2026-09-16`.
docs/sprints/sprint-209-a-stop-that-fired-is-not-a-mismatch.md: MERGED | **Status:** MERGED — `032cd8e` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: code merged `032cd8e` · DEPLOYED `s209`, 2026-09-16 · live fired-stop proof **MET 2026-09-17** on `sched-2026-09-16` (CMCSA + USB stops fired, 0 mismatch faults)
docs/sprints/sprint-21-incidents-explain-p6-exit.md: MERGED | **Status:** MERGED — shipped · **Branch:** `sprint-21-incidents-explain-p6-exit` · **Build phase:** P6 (surfaces) · **Effort: M**
docs/sprints/sprint-210-a-concentration-gate-divides-by-the-book-it-measures.md: MERGED | **Status:** MERGED — `1d515d8` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-211-reward-risk-compares-two-measured-quantities.md: MERGED | **Status:** MERGED `7d3ff51` (`0.98.08`, tag `v0.98.08`) · **DEPLOYED `s211`** 2026-09-17 — 17/17 targets on `:s211`, all `Succeeded` · **LIVE CHECK DISCHARGED** 2026-09-18 on `sched-2026-09-17`: three distinct `reward_risk` values (AMZN 0.8136, USB 0.8479, WFC 0.9484) against a constant 2.00 before, `comparison=DISCLOSURE_ONLY` at `threshold=0.0` throughout, zero `reward_risk_below_min` rejections, zero `STRUCTURALLY_DETERMINED`, evidence named as `target_basis=trailing_favorable_excursion` (horizon 10 d, sample 120). Recorded in [`docs/laws/functionality-checks.md`](../laws/functionality-checks.md). 🟠 **Still owed:** no `DeployRecord` was written for `s211` (work-queue item **72**).
docs/sprints/sprint-212-a-trace-says-why-nothing-was-submitted.md: MERGED | **Status:** MERGED
docs/sprints/sprint-213-a-regime-says-what-vix-it-measured.md: MERGED | **Status:** MERGED — merged to `main` in `028382d2` (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-214-a-revise-is-a-finding-an-overturn-is-a-block.md: MERGED | **Status:** MERGED — merged to `main` in `1a6f3429` (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-215-a-build-is-evidence-for-its-commit-and-its-tag.md: MERGED | **Status:** MERGED
docs/sprints/sprint-216-every-text-file-is-lf.md: MERGED | **Status:** MERGED
docs/sprints/sprint-217-the-master-checks-the-whole-fleet.md: MERGED | **Status:** MERGED
docs/sprints/sprint-218-a-broken-fleet-gets-no-run.md: MERGED | **Status:** MERGED — merged to `main` in `69f36016` (item 22 review, 2026-09-23); the line read: BUILT — amendment **R1** is locally proven (2026-09-20); its final handback SHA still requires remote gate proof. Do not merge or deploy.
docs/sprints/sprint-219-the-human-is-told-and-can-answer.md: MERGED | **Status:** MERGED — merged to `main` in `25bd0531` (item 22 review, 2026-09-23); the line read: BUILT; branch handback SHA still needs remote gate proof. Do not merge or deploy.
docs/sprints/sprint-22-mcp-tool-binding.md: MERGED | **Status:** MERGED — `e09838e0` on `main` (Implement Sprint 22 MCP tool binding) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-22-mcp-tool-binding` · **Build phase:** P1 remainder · **Effort: M**
docs/sprints/sprint-220-a-correlated-issuer-counts-in-proportion.md: MERGED | **Status:** MERGED
docs/sprints/sprint-221-a-rule-the-repo-states-is-a-rule-the-gate-enforces.md: MERGED | **Status:** MERGED
docs/sprints/sprint-222-one-llm-adapter-lives-in-the-kernel.md: MERGED | **Status:** MERGED `7d5528e` (`0.103.02`) · `GATE PROVEN` for `7cea9de` · DEPLOYED 2026-09-21
docs/sprints/sprint-223-an-envelope-says-what-it-checked.md: MERGED | **Status:** MERGED — `b18014e7` on `main` (fix(s223): an envelope names the value it checked and cannot exceed it) (item 22 review, 2026-09-23); the line read: BUILT
docs/sprints/sprint-224-a-spec-says-whether-it-was-built.md: MERGED | **Status:** MERGED `c33985b` (`0.106.00`) · tagged `v0.106.00`, 2026-09-22
docs/sprints/sprint-225-a-stop-says-which-lineage-protected-it.md: MERGED | **Status:** MERGED `fe26574e`
docs/sprints/sprint-226-a-run-says-whether-the-book-beat-the-index.md: MERGED | **Status:** MERGED `e8959675`
docs/sprints/sprint-227-an-llm-outage-holds-the-buys-not-the-run.md: MERGED | **Status:** MERGED `a4ab16d5`
docs/sprints/sprint-228-the-operator-sees-whether-the-book-beats-the-index.md: MERGED | **Status:** MERGED `d07be9e8` · tag `v0.112.00` · no deploy (the dashboard runs locally); live check done 2026-09-25
docs/sprints/sprint-229-every-component-that-decides-answers-to-a-law-book.md: MERGED | **Status:** MERGED `a372b48f` · tag `v0.111.02` · planner review and functionality check 2026-09-25
docs/sprints/sprint-23-p7-researcher.md: MERGED | **Status:** MERGED — `820aea13` on `main` (feat: add P7 researcher proposals) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-23-p7-researcher` · **Build phase:** P7 · **Effort: M**
docs/sprints/sprint-230-a-stop-rests-where-the-pm-decided.md: MERGED | **Status:** MERGED `b96f7a70` · tag `v0.111.03` · deployed `s230` 2026-09-25 18:22 AEST (image-only retag, operator-approved); first-run functionality check owed
docs/sprints/sprint-231-the-replay-universe-is-the-index-as-it-stood.md: MERGED | **Status:** MERGED `5132e7d6` · tag `v0.113.00` · 2026-09-26 · live build: coverage 🟩 99.68 %, identity 🔴 on 2 of 732 lines (E17.2b owed)
docs/sprints/sprint-232-the-substrate-imports-nothing-from-the-pack.md: MERGED | **Status:** MERGED `f685260e` · tag `v0.114.01` · deployed `s232` 2026-09-26 · live boot 🟩, run acceptance owed
docs/sprints/sprint-233-a-replay-line-holds-one-issuers-prices.md: MERGED | **Status:** MERGED · tag `v0.113.01` · 2026-09-26 · live build 🟩 99.99 %, identity checked
docs/sprints/sprint-234-the-operator-hears-once-a-day-what-the-run-did.md: MERGED | **Status:** MERGED `76e226d5` · tag `v0.114.00` · deployed `s234` 2026-09-26 · first real brief sent on `sched-2026-09-28`, one a run since (checked 2026-10-01)
docs/sprints/sprint-235-the-pipeline-replays-a-day-it-has-not-seen.md: MERGED | **Status:** MERGED · tag `v0.116.00` (script env fix `v0.116.01`) · 2026-09-27 · live rebuild and ten-year smoke replay 🟩
docs/sprints/sprint-236-the-dashboard-says-how-long-it-ran-without-a-human.md: MERGED | **Status:** MERGED · tag `v0.115.00` · 2026-09-27 · live read 🟩 (G1 70 %, G3 4 of 14), matched by an independent recomputation
docs/sprints/sprint-237-on-the-fleets-own-inputs-the-replay-decides-what-the-fleet-decided.md: MERGED | **Status:** MERGED · `14e02002` · tag `v0.117.00` · 2026-09-27 · live check: harness equals live on the six latest sessions; DL-237 verdict INSUFFICIENT until four clean sessions (first due after `sched-2026-10-01`)
docs/sprints/sprint-238-a-bar-carries-the-whole-tapes-volume.md: MERGED | **Status:** MERGED `a5c43112` · tag `v0.117.03` · 2026-09-28 · built in a claude.ai cloud session (`claude/festive-shannon-7fibne`), merged from `sprint-238-a-bar-carries-the-whole-tapes-volume` with the planner's one-minute clock margin; F1–F3 🟩 live; **deployed `s238` 2026-09-28 12:04 AEST** (image-only retag, operator-approved, `DeployRecord` recorded); **F4 passed** (read 2026-09-29, recorded 2026-10-02: 25 candidates, 0 volume drops and LLY at 3.00 M on all five runs since the deploy)
docs/sprints/sprint-239-the-forecaster-states-how-likely-a-buy-reaches-its-target.md: MERGED | **Status:** MERGED `0.118.00` (`3eb68b0d`, tag `v0.118.00`) and DEPLOYED `s239` (full `up`), 2026-09-28; owed: F4 on `sched-2026-09-28`. Built by a Claude cloud session (D1–D10); the planner fixed D11 at merge.
docs/sprints/sprint-24-p8-stage-gate.md: MERGED | **Status:** MERGED — `b0f23d70` on `main` (feat: add P8 execution stage gate) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-24-p8-stage-gate` · **Build phase:** P8 · **Effort: M**
docs/sprints/sprint-240-the-pm-weighs-its-book-at-the-runs-own-marks.md: MERGED | **Status:** MERGED `0.117.05`, fast-forwarded to `dc90a352`, tag `v0.117.05`, 2026-09-28; not deployed (PM image retag, the operator's call). Built by a cloud session on `claude/confident-goodall-qgxx4f` (`fd1adbea`); the planner re-branched it under this name.
docs/sprints/sprint-241-each-barrier-claim-is-settled-and-scored.md: MERGED | **Status:** MERGED 2026-09-29 — `e6891411`, tag `v0.119.00`, on `main`; deployed with S242's full `up` (corrected 2026-10-01; the line read: BUILT 2026-09-29 by the cloud session on `claude/loving-meitner-qeoxgm` (cut from `main` `60400a5`), not merged: C1–C9 green, `make ci` exit 0 in the container (3,592 passed, 100.00 %); owed to the planner: `uv lock`, `make gate-ran`, Windows `make ci`, F1–F3, then a full `up` and F4)
docs/sprints/sprint-242-a-poll-downloads-only-the-work-it-takes.md: MERGED | **Status:** MERGED 2026-09-29 — `f704907c`, tag `v0.119.01`, GATE PROVEN `f704907c`, F1 passed on Neon; **deployed `s242`** (full `up`, 2026-09-29 11:21–11:49 AEST, with S241). **F2 PASSED 2026-09-30** (8/8; `RxBytes` provider 489× and scanner 1,782× down; scanner peak 1,025 → 60 MB). Reporter and scanner memory reverted 2026-09-30 to 0.5 CPU / 1 GiB (only resources changed). **Closed 2026-10-01:** `sched-2026-09-30` ran 8/8 on 1 GiB (peak memory reporter 56 MB, scanner 63 MB, 0 restarts); work-queue 93 closed
docs/sprints/sprint-243-a-real-day-in-history-never-drops-a-name.md: MERGED | **Status:** MERGED 2026-09-29 — `7e157697` on `main`, 0.119.02, tag `v0.119.02`; GATE PROVEN for `9391b12b`; F1 passed on Neon; DEPLOYED `s243` (image-only retag, 2026-09-29 16:34 AEST); F2 passed 2026-10-02 (four runs since the deploy)
docs/sprints/sprint-244-every-agent-activates-on-a-busy-or-sleeping-master.md: MERGED | **Status:** MERGED 2026-09-29 — `0.119.03`, fast-forwarded to `a6fbae1e`, tag `v0.119.03`, GATE PROVEN `a6fbae1e`, Windows `make ci` 3,687 passed / 100.00 %; built by a cloud session on `claude/loving-gates-f8vfsd`; **deployed `s244`** (image-only retag, 16 / 16 + dispatcher, DeployRecord); **F1 PASS** (0 EHLO tracebacks, 2 resends, 15 activations, 0 orphans); **F2 measured 2026-10-01** on `sched-2026-09-30`: 0 EHLO tracebacks, 0 resends, 15 activations, each 2–8 s after its own container started; 3 of 15 started ~2 min late waiting for an Azure node, so "all within ~60 s" is not met as written; work-queue 95 closed
docs/sprints/sprint-245-every-fact-the-referee-is-told-is-pinned-to-the-code.md: MERGED | **Status:** MERGED 2026-09-30 — `0.119.05`, fast-forwarded to `d1ba474f`, tag `v0.119.05`, GATE PROVEN `d1ba474f`; Windows `make ci` 3,701 passed / 100.00 %; built by a cloud session on `claude/sprint-245-referee-facts-5co3h4`; live check PASS (old champion asserted calendar-day counting 8 / 10, new 0 / 10, $1.45); **deployed `s245`** 2026-09-30 (image-only retag, 16 / 16 + dispatcher, DeployRecord); **F1 PASS 2026-10-01** on the fleet test run `verify-2026-10-01-s248-a` (planner-fired, not scheduled): the challenger's and the judge's `system_prompt_hash` and the `prompt_recipe_hash` are all new against the last debate night, and 0 of 4 turns mention calendar days
docs/sprints/sprint-246-every-debate-turn-records-how-it-read-the-evidence.md: MERGED | **Status:** MERGED 2026-09-30 — `0.120.00`, fast-forwarded to `0ac9f96b`, tag `v0.120.00`, GATE PROVEN `0ac9f96b` (CI, CodeQL, Security Findings, attempt 1); Windows `make ci` exit 0 (3,764 passed, 8 skipped, 100.00 %); golden regenerated with real DSPy 3.3.1 byte-identical to the committed one; built by a cloud session on `claude/focused-bardeen-3975ju` (cut from `main` `61068bc`). Replay at production effort passed 2026-09-30 (parse 19 / 20, 0 `max_tokens` stops, challenger 32.4–50.4 s, $1.92); **deployed `s246`** 2026-09-30 (image-only retag). **F1 measured 2026-10-01** on the fleet test run `verify-2026-10-01-s248-a` (one debate, TGT): all 4 debater turns carry `reasoning`, 0 `reasoning_error`, 10 / 7 / 6 / 6 readings, 0 fail-opens, 0 `max_tokens` stops; output tokens defender 2,448 / 3,300, challenger 4,012 / 4,059; latency 26.5 / 35.6 s and 46.1 / 45.7 s; the "judge hash unchanged" limb is not verifiable live (no `s245`-era debate exists)
docs/sprints/sprint-248-a-divergence-is-critical-only-when-it-survived-a-run.md: MERGED | **Status:** MERGED 2026-10-01 — `0.120.02`, fast-forwarded to `09699ad0`, tag `v0.120.02`, GATE PROVEN `09699ad0` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,775 passed, 8 skipped, 100.00 %); built by a Claude cloud session on `claude/upbeat-fermi-wva7zm` (cut from `main` `f1192239`); **F1 PASS** (the 53 live subjects replayed in memory through the merged code: first sighting 53 `warn` and 0 `critical`, the next run 53 `critical`, all gone 0 open, a new episode 53 `warn`; 0 of 224 copied nodes rewritten); A10 met with a one-argument edit to the sweep test, accepted (DL-254 D6); DRIFT-094 opened and filed as work-queue 102; **deployed `s248`** 2026-10-01 13:25–13:31 AEST (image-only retag from `v0.120.02`, build `36810254508` 15 / 15; 16 / 16 apps + `dispatcher-cron`, `DeployRecord`; rollback `s246`); **F2 PASS** 2026-10-02 on `sched-2026-10-01` (three stops and one fill moved the book: four `warn` Flags in the new subject format, all resolved in the run, 0 `critical`)
docs/sprints/sprint-249-a-runs-market-window-ends-on-its-as-of.md: MERGED | **Status:** MERGED 2026-10-01 — `0.120.03`, fast-forwarded to `f3956bac`, tag `v0.120.03`, GATE PROVEN `f3956bac` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,793 passed, 8 skipped, 100.00 %); built by a Claude cloud session on `claude/vibrant-pasteur-4x99vq` (cut from `main` `a9fff56`); **F1 PASS** (the merged provider on the live sources, a request for as-of 2026-09-30 ingested on 2026-10-01: `window_end` 2026-09-30, 203 bars a name, 10 of 10 names identical to `sched-2026-09-30`, on the single and the chunked path); DL-256, provider laws v1.7 (22 / 67), DRIFT-095 corrected; **deployed `s249`** 2026-10-01 17:01–17:08 AEST (operator: *"you can retag"*): image-only, the three injected packs byte-identical between `v0.120.02` and `v0.120.03`; build `36827807053` **15 / 15** from `f3956bac`; **16 / 16** apps and `dispatcher-cron` on `s249`, all `Succeeded`, one active revision each, latest = ready; CPU, memory, env counts and the full scale blocks identical to the pre-retag snapshot; `DeployRecord` written; rollback `s248`
docs/sprints/sprint-25-p8-market-pack.md: MERGED | **Status:** MERGED — merged to `main` in `28f8f6da` (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-25-p8-market-pack` · **Build phase:** P8 · **Effort: M**
docs/sprints/sprint-250-a-replays-excess-return-comes-with-an-interval-and-a-verdict.md: MERGED | **Status:** MERGED 2026-10-01 — `0.121.00`, fast-forwarded to `96b03d52`, tag `v0.121.00`, GATE PROVEN `96b03d52` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,915 passed, 8 skipped, 100.00 %); built by a Claude cloud session on `claude/hopeful-davinci-oob51b`, returned once for the holiday-table repair its own handback found; **F1 PASS** (three months on the licensed cache with the history rule on: 54 buys, 0 decided on fewer than 200 bars, least 217, 1,199 member-sessions withheld); the provider's NYSE table now holds every closure from 2016, so the harness window is 203 sessions on all 2,446 scored sessions (194–198 before 2024 until now); deployed with `s251` 2026-10-02 (the calendar repair; `scripts/` ships in no image); owed: F2, EXP-014 itself, once E17.4's fidelity verdict reads PASS
docs/sprints/sprint-251-every-open-drift-row-is-decided.md: MERGED | **Status:** MERGED 2026-10-02 — `0.121.01`, fast-forwarded to `d526faf4`, tag `v0.121.01`, GATE PROVEN `d526faf4` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,932 passed, 8 skipped, 100.00 %); built by a Claude cloud session on `claude/compassionate-hamilton-g1wdjb`, one commit a law book; all 23 ruled rows decided across 13 books, no behaviour change (the only code edit is execution's `owns_graph`); DRIFT-098 closed by the planner at merge; **two rows remain open**, both filed during the sprint: DRIFT-096 and DRIFT-097 (work-queue 106); deployed with `s251` 2026-10-02
docs/sprints/sprint-252-every-finder-fetches-only-its-pending-work.md: MERGED | **Status:** MERGED 2026-10-02 — `0.121.03`, fast-forwarded to `dd22b348`, tag `v0.121.03`, GATE PROVEN `dd22b348` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,966 passed, 8 skipped, 100.00 %, dependency audit clean); built by Codex in `../ta-s252`, rebased over S253 and merged with the planner's mypy fix to the test clock; forecaster laws v1.10 (25 / 52), deliberator v1.12 (27 / 59), execution v1.12 (40 / 66), monitor v1.3 (21 / 46); DRIFT-097 and DRIFT-100 `CORRECTED`; **F1 PASS** (old and new finders on the live graph: 44 comparisons, every pending set equal and in the same order; one idle poll of the six reads 18.7 MB before and only a key query after); **deployed `s255` 2026-10-08**; owed: F2
docs/sprints/sprint-253-a-runs-snapshot-counts-what-the-broker-filled.md: MERGED | **Status:** MERGED 2026-10-02 — `0.121.02`, fast-forwarded to `4152ebd2`, tag `v0.121.02`, GATE PROVEN `4152ebd2` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (3,945 passed, 8 skipped, 100.00 %); built by a Claude cloud session on `claude/magical-archimedes-c24l8w`, merged from `sprint-253-a-runs-snapshot-counts-what-the-broker-filled` with the planner's resumed-run sentence and test; reporter laws v1.5 (26 / 43), analyst laws v1.8 (28 / 51); DRIFT-099, DRIFT-096 and DRIFT-101 `CORRECTED`; **F1 PASS** (the merged reporter over the live graph, its writes captured in memory: 12 / 3, 1 / 1, 0 / 0 and 1 / 3 opened / closed on the four measured runs, 31 exits at −146,279 cents, 129 of 129 filled fills in exactly one window); **deployed `s255` 2026-10-08**; **F2 PASS 2026-10-09** on `sched-2026-10-08` (the snapshot reads 0 opened and 2 closed; the broker filled no buy and two stop sells since the previous run, and the brief's *Filled* line names the same two).
docs/sprints/sprint-254-each-debater-turn-is-run-by-dspy-and-the-prompt-does-not-change.md: MERGED | **Status:** MERGED 2026-10-07 — `0.122.00`, fast-forwarded to `228e16c1`, tag `v0.122.00`, GATE PROVEN `228e16c1` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (4,255 passed, 8 skipped, 100.00 %, dependency audit clean); built by Codex in `../ta-s254`; merged with the planner's dependency layout (DSPy in the dev group, the audit's premise widened, [DL-268](../design-log.md)) and with an import cycle that CodeQL reported as an error on the branch removed; deliberator laws v1.13 (28 / 60, new `DLIB-NEV-10`); the planner's own comparison with `main`: 168 of 168 turns byte-identical; `main`'s own runs are green (CI, CodeQL, Security Findings, *Build and push agent images* 15 / 15): the built deliberator image installed 94 packages with `dspy==3.4.0` and neither `diskcache` nor `litellm` (the installer's list, and the image scan's 95 package rows), its real entrypoint ran to the master handshake, and it is 60.5 MB compressed against `s251`'s 42.5 MB; **deployed `s255` 2026-10-08**; **F1 PASS** 2026-10-07 (one real debate on `gpt-5.5`: 4 of 4 guided turns read, all three system prompt hashes equal the last debate night's, ruling `revise`, $0.79; the defender's turn reached 94 % of the output cap, work-queue 111); **F2 PASS 2026-10-09** on `sched-2026-10-08` (one debated buy on `gpt-5.5`, the first guided turns executed inside the built image: the three system prompt hashes equal the last debate night's, all five calls carry the `prompt_recipe_hash` computed on `main`, `09d1bc82c6e4…`, no order failed open, peak working set 149, 123 and 123 MB against 1 GiB).
docs/sprints/sprint-255-the-packet-states-the-score-arithmetic.md: MERGED | **Status:** MERGED 2026-10-08 — `0.123.00`, fast-forwarded to `fec365a1`, tag `v0.123.00`, GATE PROVEN `fec365a1` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (4,304 passed, 7 skipped, 100.00 %, dependency audit clean); built by Codex in `../ta-s255` after one stop on the planner's false clause (the first line's scale claim, corrected: [DL-270](../design-log.md)); analyst laws v1.9 (`ANLZ-OUT-10`), provider v1.9 (`PROV-OUT-02` amended), deliberator v1.14 (`DLIB-OUT-08`); merged on the operator's word, on `gpt-5.5`'s evidence: the corrected line read 54 of 54 right in [EXP-021](../research/experiments/EXP-021-does-the-corrected-first-line-read-as-well-as-the-measured-one.md), not measured on Opus; **F1 PASS** (the merged code on `main` rebuilds the nine recorded packets from the live graph 9 of 9 byte-equal and adds no line to any, because their records predate the new fields); `main`'s own runs are green (CI, CodeQL, Security Findings, *Build and push agent images* 15 / 15), and the built images of the analyst, the provider and the deliberator each ran their real entrypoint to the master handshake; **deployed `s255` 2026-10-08**; **F2 PASS 2026-10-09** on `sched-2026-10-08` (36 of 36 recommendations carry their arithmetic and the rule reproduces each confidence, the regime carries its thresholds, the one debated packet ends with the three lines, none withheld, and `main` rebuilds it byte for byte; the largest turn wrote 7,215 output tokens).
docs/sprints/sprint-256-a-served-request-is-settled-when-it-is-taken.md: MERGED | **Status:** MERGED 2026-10-08 — `0.123.01`, fast-forwarded to `b3f1ee1f`, tag `v0.123.01`, GATE PROVEN `b3f1ee1f` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (4,322 passed, 8 skipped, 100.00 %, dependency audit clean); built by Codex in `../ta-s256`, complete against the twelve-item checklist; deliberator laws v1.15 (`DLIB-IDM-04`, `DLIB-OBS-08`; `DLIB-OBS-02` proven), operator v1.4 (`OPR-IDM-02` rewritten), DRIFT-104 corrected; the planner's own re-measure: the reproduction prints its *after* block and six pieces of the old behaviour each turn the tests red; open CodeQL alerts 127, the same as sprint 255's branch, none new; **F1 PASS** (the merged code on the live namespace, disposable topics with the default one-minute lock and a 70-second handler: served once, no error, one reply, nothing given to a second consumer, both topics deleted); **deployed `s257` 2026-10-08**; **F2 PASS 2026-10-09** on `sched-2026-10-08` (one debated buy: each debater replica started once and restarted 0 times, the three apps wrote no console line, no ledger key holds `:repeat-`, 0 `Fault`s; the slowest turn took 67.5 s, with the five-minute lock still set by hand).
docs/sprints/sprint-257-a-debaters-turn-may-write-16384-output-tokens.md: MERGED | **Status:** MERGED 2026-10-08 — `0.123.02`, fast-forwarded to `b0831f64`, tag `v0.123.02`, GATE PROVEN `b0831f64` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (4,330 passed, 8 skipped, 100.00 %, dependency audit clean); built by Codex in `../ta-s257`, complete against the nine-item checklist; deliberator laws v1.16 (`PARAM` only, no clause changes); the planner's own re-measure: eight pieces of the old behaviour put back one at a time each turn the tests red; the builder found the spec's claim about the parameter step false ([DL-275](../design-log.md), work-queue 114); open CodeQL alerts 127, the same as `main`'s, none new; **F1a PASS** (Anthropic's 0.120.2 client accepts 16,384 and 21,333 and refuses 21,334 before sending, and both adapters put 16,384 in the request, on the real libraries with an in-memory transport); **F1b PASS** (one real debate on `gpt-5.5` at the new cap and a 240-second wait: all five calls ended normally, the defender's first turn wrote 10,658 output tokens, which the old cap of 8,192 would have cut, the slowest call took 93.8 s, the order 231 s, $0.88); **deployed `s257` 2026-10-08**, the manager's wait set to 240 seconds on the live app; **F2 PASS 2026-10-09** on `sched-2026-10-08` (one debated buy: all five calls ended on `stop`, the largest turn wrote 7,215 of 16,384 output tokens, the slowest took 67.5 of 240 s, and the deliberation record landed 222 s after the PM run against execution's grace of 1,800 s).
docs/sprints/sprint-258-a-law-rows-numbers-are-compared-with-the-code.md: MERGED | **Status:** MERGED 2026-10-08 — `0.123.03`, fast-forwarded to `b9ea3038`, tag `v0.123.03`, GATE PROVEN `b9ea3038` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (4,392 passed, 8 skipped, 100.00 %, dependency audit clean) and the gate self-test 31 of 31; built by Codex in `../ta-s258`, complete against the ten-item checklist; execution laws v1.13 (`PARAM` only, no clause changes); the planner's own re-measure: a count over the built reader gives the spec's numbers (235 rows, every default agrees, 156 bounds agree, 8 excused) and finds no bound the reader missed, and ten pieces of the comparison removed one at a time each turn the tests red; open CodeQL alerts 127, the same as `main`'s, none new; **F1 PASS** (on the merged `main` the step exits 0, and each of thirteen wrong numbers planted in a real law row or settings file makes it exit 1 and name the row, each restored); no deploy (`scripts/` ships in no image); work-queue 114 stays open for the eight excused rows
docs/sprints/sprint-259-the-eight-excused-law-rows-state-the-codes-bounds.md: MERGED | **Status:** MERGED 2026-10-08 — `0.123.04`, fast-forwarded to `49146e40`, tag `v0.123.04`, GATE PROVEN `49146e40` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (4,392 passed, 8 skipped, 100.00 %, dependency audit clean); built by the planner on the operator's word ("tonight"); portfolio manager laws v1.12, scanner v1.5, analyst v1.10 (`PARAM` only, no clause changes); red first, then each of the eight rows put back fails the parameter step; the excused list is empty and a test holds it empty; open CodeQL alerts 127, the same as `main`'s, none new; **F1 PASS** (on the merged `main` the step exits 0 with no excused row, and each row put back makes it exit 1); **deployed `s259a` 2026-10-08**, before the fidelity count's first session, so nothing counted is lost; work-queue 114 closed
docs/sprints/sprint-26-p9-observability.md: MERGED | **Status:** MERGED — its README row records it shipped; no merge commit or tag was found to cite (item 22 review, 2026-09-23)
docs/sprints/sprint-260-debates-at-once-lose-no-reply-and-the-repo-can-show-it.md: MERGED | **Status:** MERGED 2026-10-09 — `0.124.00`, fast-forwarded to `19239d25`, tag `v0.124.00`, GATE PROVEN `19239d25` (CI, CodeQL, Security Findings); Windows `make ci` exit 0 (4,436 passed, 8 skipped, 100.00 %, dependency audit clean); built by Codex in `../ta-s260`, complete against the twelve-item checklist; no law change; the planner's own re-measure: the kernel's old default of ten requests a pass put back turns A1 red (the builder could only simulate it inside the harness), and both handback commands give their counts with a connection string in the environment; merged with the planner's removal of a module global and a bare delete that CodeQL reported on the branch, and with the builder's design-log entry renumbered to [DL-281](../design-log.md); open CodeQL alerts 127, the same as `main`'s, none new; **live before the merge PASS** (disposable topics: one to four at once clean, 16 turns of 10 s in 186.7 s at one and 50.2 s at four; ten requests a pass with late replicas failed 2 of 4 orders open); **F1 PASS** (on the merged `main`, live, 8 orders, 2 rounds, turns of 20 s, a wait of 240 s: one, two, three and four at once all clean, 32 turns in 712.7, 356.3, 268.6 and 181.0 s, effective lanes 0.90, 1.80, 2.38 and 3.54; ten requests a pass with late replicas read not clean, 2 of 4 failed open and 2 replies nobody took; every topic deleted, the fleet's three subscriptions unchanged); no deploy (`scripts/` ships in no image, and the one new argument rides the next retag); the dial stays at 1; next: the operator's call on one paid proof on the fleet at three at once
docs/sprints/sprint-261-a-tracker-over-its-byte-limit-fails-make-ci.md: MERGED | **Status:** MERGED 2026-10-11 — no version bump, fast-forwarded to `be7594cb`, GATE PROVEN `be7594cb` (CI, CodeQL, Security Findings); no deploy; F1 passed at no cost
docs/sprints/sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it.md: MERGED | **Status:** MERGED 2026-10-09 — `0.125.00`, fast-forwarded to `d01b71b3`, tag `v0.125.00`, GATE PROVEN `d01b71b3`; **deployed `s262` 2026-10-09**; F1a passed (the command against the fleet); 🔴 F1b verified failing (the OpenAI chat adapter, work-queue 121); F2 owed
docs/sprints/sprint-263-the-operators-chat-makes-its-tool-call-on-openai.md: MERGED | **Status:** MERGED 2026-10-09 — `0.125.01`, fast-forwarded to `9df7dacd`, tag `v0.125.01`, GATE PROVEN `9df7dacd` (CI, CodeQL, Security Findings); no deploy; F1a and F1b passed; 🔴 found by F1b, carried over from S262's adapter: the operator's ledger row carries no stop reason and, on OpenAI, drops a cut-off call's tokens (work-queue 124)
docs/sprints/sprint-264-a-cut-off-reply-is-recorded-and-the-chat-says-so.md: MERGED | **Status:** MERGED 2026-10-10 — `0.125.02`, fast-forwarded to `cc050bba`, tag `v0.125.02`, GATE PROVEN `cc050bba` (CI, CodeQL, Security Findings); no deploy; F1a passed and F1b passed on OpenAI (a real cut-off, $0.0033); F1b on Anthropic is owed after its account is funded (2026-10-11)
docs/sprints/sprint-265-a-failed-chat-request-is-audited-and-says-why.md: MERGED | **Status:** MERGED 2026-10-11 — `0.125.03`, fast-forwarded to `c32398fc`, tag `v0.125.03`, GATE PROVEN `c32398fc` (CI, CodeQL, Security Findings); no deploy; F1a and F1b passed, both at no cost
docs/sprints/sprint-266-a-runs-barrier-history-ends-on-its-as-of.md: MERGED | **Status:** MERGED 2026-10-11 — `0.125.04`, fast-forwarded to `b1580076`, tag `v0.125.04`, GATE PROVEN `b1580076` (CI, CodeQL, Security Findings); not deployed (image-only, with the next retag); F1a and F1b passed, both at no cost
docs/sprints/sprint-267-a-tag-is-proven-from-any-attempt-of-its-build.md: MERGED | **Status:** MERGED 2026-10-11 — `0.125.05`, fast-forwarded to `475dba3c`, tag `v0.125.05`, GATE PROVEN `475dba3c` (CI, CodeQL, Security Findings); no deploy; F1 passed at no cost
docs/sprints/sprint-268-an-intent-that-lacks-what-its-family-needs-is-refused.md: MERGED | **Status:** MERGED 2026-10-11 — `0.125.06`, fast-forwarded to `e9f4f4a8`, tag `v0.125.06`, GATE PROVEN `e9f4f4a8` (CI, CodeQL, Security Findings); no deploy; F1a passed at no cost; F1b passed on OpenAI ($0.04), not run on Anthropic
docs/sprints/sprint-269-a-null-parameter-is-no-value.md: MERGED | **Status:** MERGED 2026-10-11 — `0.125.07`, fast-forwarded to `4b536d7e`, tag `v0.125.07`, GATE PROVEN `4b536d7e` (CI, CodeQL, Security Findings); no deploy; F1 passed at no cost
docs/sprints/sprint-27-p10-curator-datasets.md: MERGED | **Status:** MERGED — `ba85c694` on `main` (feat: curator agent — dataset assembly by provenance traversal (P10 be) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-27-p10-curator-datasets` · **Build phase:** P10 · **Effort: M–L**
docs/sprints/sprint-270-the-deploy-defaults-are-the-live-wake-window.md: MERGED | **Status:** MERGED 2026-10-12 — `0.125.08`, fast-forwarded to `5d242a8e`, tag `v0.125.08`, GATE PROVEN `5d242a8e` (CI, CodeQL, Security Findings); F1 passed at no cost; deploy owed
docs/sprints/sprint-271-a-full-up-creates-the-master-with-its-probes.md: MERGED | **Status:** MERGED 2026-10-13 — no version bump, fast-forwarded to `9eb1325f`, GATE PROVEN `9eb1325f` (CI, CodeQL, Security Findings); F1 passed at no cost; F2 owed at the next full `up`; no deploy
docs/sprints/sprint-272-a-container-ends-cleanly-on-the-stop-signal.md: MERGED | **Status:** MERGED 2026-10-14 — `0.125.09`, fast-forwarded to `497293b8`, tag `v0.125.09`, GATE PROVEN `497293b8` (CI, CodeQL, Security Findings); F1 passed at no cost; deployed as `s272` 2026-10-14; F2 passed at the retag, one read owed after the first nightly window's end
docs/sprints/sprint-273-the-secrets-scan-reads-every-file-as-utf-8.md: MERGED | **Status:** MERGED 2026-10-14 — no version bump, fast-forwarded to `25a0129d`, GATE PROVEN `25a0129d` (CI, CodeQL, Security Findings); the new case's first Linux run read PASS; F1 passed in its first part and failed in its second, which the planner's follow-up (`ccc2bf94`, GATE PROVEN) put right the same day; no deploy
docs/sprints/sprint-274-a-full-up-keeps-the-masters-live-start.md: MERGED | **Status:** MERGED 2026-10-14 — `0.125.10`, fast-forwarded to `17655eea`, tag `v0.125.10`, GATE PROVEN `17655eea` (CI, CodeQL, Security Findings); F1 passed at no cost; no deploy
docs/sprints/sprint-275-the-operator-hears-when-a-container-fails.md: MERGED | **Status:** MERGED 2026-10-14 — `0.126.00`, fast-forwarded to `82909a54`, tag `v0.126.00`, GATE PROVEN `82909a54` (CI, CodeQL, Security Findings); F1 passed at no cost; **deployed as `s275` 2026-10-14** (image-only retag, 16 of 16 apps and the job; then `deploy-agents.ps1 sensor`; rollback `s272`); **F2 passed 2026-10-15** (the first weekday fire on `s275` (2026-10-14 22:00 to 23:50 UTC, 12 fires): every fire's console holds `container-sensor read 0 rows: 0 new events, 0 alarms, told 0` and none an error line; the graph holds 12 `ContainerSensorRead`, all `outcome: read`, the first reading the 24 hours from 2026-10-13 22:00 UTC and each later one overlapping the last by ten minutes; the brief of `sched-2026-10-14` (Telegram message 18, 22:50:21 UTC) carries `Containers: no alarm in 24 hours`; no alarm, so no message; the same query run as the operator also returns 0 rows); work-queue 119 closed
docs/sprints/sprint-276-a-debater-runs-on-the-first-llm-that-works.md: MERGED | **Status:** MERGED 2026-10-15 — `0.127.00`, fast-forwarded to `fe6da5ac`, tag `v0.127.00`, GATE PROVEN `fe6da5ac` (CI, CodeQL, Security Findings; CI on attempt 2, attempt 1 a midnight-straddle flake in a scanner test already on `main`, fixed by its own chore); Windows `make ci` exit 0 (5,031 passed, 8 skipped, 100.00 %, audit clean); built by Codex, its 29 production files the planner's prototype byte for byte; the planner's 32 breaks 32 red against the builder's tests; one planner change at review, an import cycle CodeQL read as seven errors (133 open alerts after, 0 errors); F1a passed at no cost; F1b passed 2026-10-15 (paid, on the operator's *"go ahead"*): one real probe per candidate through the master's own start path (`load_credential_tests`, `select_llm_provider`, `expand_llm_candidates`) on merged `main`: `openai/gpt-5.5/high` (`reasoning_effort: high`, `max_completion_tokens: 256`) and `anthropic/claude-opus-5/max` (`output_config.effort: max`, `max_tokens: 1`) each answered HTTP 200; the cost is bounded by 256 and 1 output tokens; **deployed as `s276` 2026-10-15 12:48 AEDT: first the `llm-candidates` step, corrected by `chore-llm-candidates-carry-the-credential-pack` (`551f65a6`, GATE PROVEN, no bump) because the step as specced left the master's injected `s275` credential pack in place and the S276 master refuses to start on an LLM probe without `candidate_paths`; the step read both `[OK]`, the master's three packs equal `main`'s byte for byte, the `s275` master healthy on them; then the image-only retag from `v0.127.00` (build `38664365870`, 15 of 15), 17 of 17 `Succeeded`, every app identical to its snapshot but for the tag and the master's three keys the step set, `DeployRecord` `s276:fe6da5ac`, rollback `s275`; read at the retag: 15 of 15 types activated, the three deliberators on `openai/gpt-5.5/high` with nothing passed over, the master's fleet check passed with `llm_passed_over` empty, 0 faults, escalations or flags**; F2 owed at the first weekday fire
docs/sprints/sprint-277-a-refused-request-is-answered-by-the-next-llm.md: MERGED | **Status:** MERGED
docs/sprints/sprint-278-a-failure-the-platform-logs-is-an-alarm.md: MERGED | **Status:** MERGED
docs/sprints/sprint-279-a-pass-reads-each-label-once.md: MERGED | **Status:** MERGED
docs/sprints/sprint-28-p10-training-trigger.md: MERGED | **Status:** MERGED — `13944ace` on `main` (feat: curator training trigger — advisory baseline predictor (P10)) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-28-p10-training-trigger` · **Build phase:** P10 · **Effort: M**
docs/sprints/sprint-280-a-partly-filled-order-is-a-fill-of-its-part.md: MERGED | **Status:** MERGED
docs/sprints/sprint-281-a-replay-arm-declares-how-its-positions-exit.md: MERGED | **Status:** MERGED
docs/sprints/sprint-282-each-exit-arm-is-scored-against-stops-only-on-the-same-days.md: MERGED | **Status:** MERGED
docs/sprints/sprint-283-no-broker-read-is-cut-at-a-page.md: MERGED | **Status:** MERGED
docs/sprints/sprint-284-a-headline-counts-only-for-the-company-it-names.md: MERGED | **Status:** MERGED
docs/sprints/sprint-285-the-dispatcher-keeps-the-deadline-it-tells.md: SPEC | **Status:** SPEC
docs/sprints/sprint-29-p10-predictor-registry.md: MERGED | **Status:** MERGED — `175a07b8` on `main` (feat: curator predictor registry — promote_predictor gate + audit (P10) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-29-p10-predictor-registry` · **Build phase:** P10 (exit) · **Effort: M**
docs/sprints/sprint-30-p11-analyst-technical-core.md: MERGED | **Status:** MERGED — `2d59f235` on `main` (feat: analyst technical scoring core — RSI/MACD/Bollinger/SMA/EMA (P11) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-30-p11-analyst-technical-core` · **Build phase:** P11 · **Effort: L**
docs/sprints/sprint-31-p11-analyst-oscillators.md: MERGED | **Status:** MERGED — `524968d9` on `main` (docs: close Sprint 31 — analyst oscillators + volatility shipped (P11)) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-31-p11-analyst-oscillators` · **Build phase:** P11 · **Effort: M**
docs/sprints/sprint-32-p11-analyst-volume-event.md: MERGED | **Status:** MERGED — `036c38d9` on `main` (docs: close Sprint 32 — analyst volume/event signals shipped (P11)) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-32-p11-analyst-volume-event` · **Build phase:** P11 · **Effort: M**
docs/sprints/sprint-33-p11-analyst-patterns.md: MERGED | **Status:** MERGED — `75f77df9` on `main` (docs: close Sprint 33 — analyst patterns/smoothing/calendar shipped (P) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-33-p11-analyst-patterns` · **Build phase:** P11 · **Effort: L**
docs/sprints/sprint-34-provider-fundamentals.md: MERGED | **Status:** MERGED — `15655bdd` on `main` (docs: close Sprint 34 — provider fundamentals feed shipped (P11)) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-34-provider-fundamentals` · **Build phase:** P11 · **Effort: M**
docs/sprints/sprint-35-analyst-fundamental-scoring.md: MERGED | **Status:** MERGED — `ce50da4a` on `main` (docs: close Sprint 35 — analyst fundamental scoring shipped (P11)) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-35-analyst-fundamental-scoring` · **Build phase:** P11 · **Effort: M**
docs/sprints/sprint-36-provider-news-feed.md: MERGED | **Status:** MERGED — shipped · **Branch:** `sprint-36-provider-news-feed` · **Build phase:** P11 · **Effort: M**
docs/sprints/sprint-37-analyst-sentiment-pillar.md: MERGED | **Status:** MERGED — `401280dc` on `main` (feat(analyst): sentiment pillar — Loughran-McDonald lexicon champion () (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-37-analyst-sentiment-pillar` · **Build phase:** P12 · **Effort: M**
docs/sprints/sprint-38-analyst-relative-strength.md: MERGED | **Status:** MERGED — shipped · **Branch:** `sprint-38-analyst-relative-strength` · **Build phase:** P11 · **Effort: S–M**
docs/sprints/sprint-39-analyst-signal-diversity.md: MERGED | **Status:** MERGED — shipped · **Branch:** `sprint-39-analyst-signal-diversity` · **Build phase:** P11 · **Effort: S**
docs/sprints/sprint-40-pm-reward-risk.md: MERGED | **Status:** MERGED — shipped · **Branch:** `sprint-40-pm-reward-risk` · **Build phase:** P11 · **Effort: S**
docs/sprints/sprint-41-reporter-trade-outcomes.md: MERGED | **Status:** MERGED — ✅ shipped (2026-06-18, on `main` — no coding agent this cycle) · **Build phase:** P11 · **Effort: S**
docs/sprints/sprint-42-provider-earnings-feed.md: MERGED | **Status:** MERGED — ✅ shipped (2026-06-18, on `main`) · **Build phase:** P11 · **Effort: M** · executed directly (no coding agent this cycle)
docs/sprints/sprint-43-monitor-realized-pnl.md: MERGED | **Status:** MERGED — ✅ shipped (2026-06-18, branch `sprint-43-monitor-realized-pnl`) · **Build phase:** P11 · **Effort: S–M** · executed directly (no coding agent this cycle)
docs/sprints/sprint-44-provider-tiingo-feed.md: MERGED | **Status:** MERGED — `25dda634` on `main` (feat(provider): Tiingo live OHLCV feed as the full-S&P-500 default (S4) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-44-provider-tiingo-feed` · **Build phase:** provider infra (DRIFT-009 closeout · ADR-0006) · **Effort: M**
docs/sprints/sprint-45-execution-alpaca-broker.md: MERGED | **Status:** MERGED — `dee6a505` on `main` (feat(execution): Alpaca paper broker behind the Broker port (S45, ADR-) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-45-execution-alpaca-broker` · **Build phase:** execution / DEP-BROKER (ADR-0006) · **Effort: M–L**
docs/sprints/sprint-46-analyst-sentiment-reading.md: MERGED | **Status:** MERGED — shipped · **Branch:** `sprint-46-analyst-sentiment-reading` · **Build phase:** P12 (checklist item 2) · **Effort: M**
docs/sprints/sprint-47-provider-sentiment-feed.md: MERGED | **Status:** MERGED — shipped · **Branch:** `sprint-47-provider-sentiment-feed` · **Build phase:** P12 (provider-sentiment challenger) · **Effort: M–L**
docs/sprints/sprint-48-analyst-provider-sentiment-reading.md: MERGED | **Status:** MERGED — shipped (2026-06-17, commit `9c24a57`) · **Branch:** `sprint-48-analyst-provider-sentiment-reading` · **Build phase:** P12 (provider-sentiment challenger — completes it) · **Effort: S–M**
docs/sprints/sprint-49-forecaster-finbert-runtime.md: MERGED | **Status:** MERGED — shipped (2026-06-17, commit `82ecb31`) · **Branch:** `sprint-49-forecaster-finbert-runtime` · **Build phase:** P12 (the FinBERT challenger — the reserved forecaster agent's first runtime) · **Effort: L**
docs/sprints/sprint-50-scanner-beta-cap.md: MERGED | **Status:** MERGED — shipped (2026-06-17, commit `51ee2b6`) · **Branch:** `sprint-50-scanner-beta-cap` · **Build phase:** P11 (decision-logic depth — scanner side) · **Effort: M**
docs/sprints/sprint-51-provider-sector-feed.md: MERGED | **Status:** MERGED — shipped (2026-06-17, commit `3951e42`) · **Branch:** `sprint-51-provider-sector-feed` · **Build phase:** P11 (decision-logic depth — the data substrate for the PM sector-concentration cap) · **Effort: M**
docs/sprints/sprint-52-pm-sector-cap.md: MERGED | **Status:** MERGED — shipped (2026-06-17, commit `6f23ff1`) · **Branch:** `sprint-52-pm-sector-cap` · **Build phase:** P11 (decision-logic depth — the PM's second risk gate, twin of S40) · **Effort: M**
docs/sprints/sprint-54-scanner-earnings-exclusion.md: MERGED | **Status:** MERGED — ✅ shipped (2026-06-18, branch `sprint-54-scanner-earnings-exclusion`) · **Build phase:** P11 · **Effort: S** · executed directly (no coding agent this cycle)
docs/sprints/sprint-55-reporter-realized-pnl-repoint.md: MERGED | **Status:** MERGED — ✅ shipped (2026-06-18, branch `sprint-55-reporter-realized-pnl-repoint`) · **Build phase:** P11 (final slice) · **Effort: S** · executed directly (no coding agent this cycle)
docs/sprints/sprint-56-analyst-lm-master-dictionary.md: MERGED | **Status:** MERGED — shipped (implemented directly — no coding agent this cycle).
docs/sprints/sprint-57-forecaster-sentiment-scorecard.md: MERGED | **Status:** MERGED — shipped (implemented directly — no coding agent this cycle).
docs/sprints/sprint-58-forecaster-lightgbm-shadow.md: MERGED | **Status:** MERGED — `25a8d2cd` on `main` (feat(forecaster): LightGBM price/return shadow signal — qlib Phase Q1) (item 22 review, 2026-09-23); the line read: active (2026-06-19) · **Branch:** `sprint-58-forecaster-lightgbm-shadow` · **Build phase:** qlib Phase Q1 (research [R001](../research/qlib-integration/qlib-integration.md)) · **Effort: M**
docs/sprints/sprint-59-forecaster-lgbm-training-scorecard.md: MERGED | **Status:** MERGED — `ef018079` on `main` (feat(forecaster): LightGBM training pipeline + return IC scorecard — q) (item 22 review, 2026-09-23); the line read: active (2026-06-19) · **Branch:** `sprint-58-forecaster-lightgbm-shadow`
docs/sprints/sprint-60-p14-kernel-pubsub.md: MERGED | **Status:** MERGED — `e59c6a53` on `main` (feat(p14): event-driven pub/sub re-architecture + Azure Service Bus ba) (item 22 review, 2026-09-23); the line read: active
docs/sprints/sprint-61-p14-claim-check.md: MERGED | **Status:** MERGED — `e59c6a53` on `main` (feat(p14): event-driven pub/sub re-architecture + Azure Service Bus ba) (item 22 review, 2026-09-23); the line read: planned
docs/sprints/sprint-62-p14-provider-pubsub.md: MERGED | **Status:** MERGED — `e59c6a53` on `main` (feat(p14): event-driven pub/sub re-architecture + Azure Service Bus ba) (item 22 review, 2026-09-23); the line read: planned
docs/sprints/sprint-63-p14-scanner-analyst-pubsub.md: MERGED | **Status:** MERGED — `e59c6a53` on `main` (feat(p14): event-driven pub/sub re-architecture + Azure Service Bus ba) (item 22 review, 2026-09-23); the line read: planned
docs/sprints/sprint-64-p14-pm-execution-pubsub.md: MERGED | **Status:** MERGED — `e59c6a53` on `main` (feat(p14): event-driven pub/sub re-architecture + Azure Service Bus ba) (item 22 review, 2026-09-23); the line read: planned
docs/sprints/sprint-65-p14-monitor-reporter-pubsub.md: MERGED | **Status:** MERGED — `e59c6a53` on `main` (feat(p14): event-driven pub/sub re-architecture + Azure Service Bus ba) (item 22 review, 2026-09-23); the line read: planned
docs/sprints/sprint-66-p14-dispatcher-trigger-emitter.md: MERGED | **Status:** MERGED — `e59c6a53` on `main` (feat(p14): event-driven pub/sub re-architecture + Azure Service Bus ba) (item 22 review, 2026-09-23); the line read: planned
docs/sprints/sprint-67-p14-azure-servicebus-backend.md: MERGED | **Status:** MERGED — `e59c6a53` on `main` (feat(p14): event-driven pub/sub re-architecture + Azure Service Bus ba) (item 22 review, 2026-09-23); the line read: planned
docs/sprints/sprint-68-analyst-alpha158-pillar.md: MERGED | **Status:** MERGED — `d12efa38` on `main` (feat(analyst): Alpha158 feature pillar — qlib Phase Q2 (S68)) (item 22 review, 2026-09-23); the line read: planned · **Branch:** `sprint-68-analyst-alpha158-pillar`
docs/sprints/sprint-69-provider-law-cycle.md: MERGED | **Status:** MERGED — merged to `main` in `cd7fdd2d` (item 22 review, 2026-09-23)
docs/sprints/sprint-70-per-agent-law-backfill.md: MERGED | **Status:** MERGED — shipped
docs/sprints/sprint-71-per-agent-law-backfill.md: MERGED | **Status:** MERGED — shipped
docs/sprints/sprint-72-system-prompt-tunable.md: MERGED | **Status:** MERGED — shipped
docs/sprints/sprint-73-p15-master-agent.md: MERGED | **Status:** MERGED — shipped
docs/sprints/sprint-74-p15-rsa-entrypoints.md: MERGED | **Status:** MERGED — shipped
docs/sprints/sprint-75-p15-key-vault.md: MERGED | **Status:** MERGED — shipped
docs/sprints/sprint-76-p15-ghcr-deploy.md: MERGED | **Status:** MERGED — its README row records it shipped; no merge commit or tag was found to cite (item 22 review, 2026-09-23); the line read: planned
docs/sprints/sprint-77-credential-naming.md: MERGED | **Status:** MERGED — `79461c59` on `main` (fix(s77): align secret_map output keys to agent settings env_prefix) (item 22 review, 2026-09-23); the line read: planned
docs/sprints/sprint-78-provider-ingestor.md: MERGED | **Status:** MERGED — shipped (0.17.00)
docs/sprints/sprint-79-agent-work-loops.md: MERGED | **Status:** MERGED — shipped as a vertical slice (0.18.00) — provider→scanner only; analyst→reporter → S80
docs/sprints/sprint-80-analyst-graph-pull.md: MERGED | **Status:** MERGED — shipped (0.19.00)
docs/sprints/sprint-81-pm-graph-pull.md: MERGED | **Status:** MERGED — shipped (0.20.00)
docs/sprints/sprint-82-execution-monitor-reporter-graph-pull.md: MERGED | **Status:** MERGED — shipped (0.21.00)
docs/sprints/sprint-83-graph-pull-orchestration.md: MERGED | **Status:** MERGED — shipped (0.22.00)
docs/sprints/sprint-84-platform-pack-grant-policy.md: MERGED | **Status:** MERGED — shipped (0.23.01)
docs/sprints/sprint-85-platform-pack-secret-map.md: MERGED | **Status:** MERGED — shipped (0.23.02)
docs/sprints/sprint-86-deploy-pack-policy-wiring.md: MERGED | **Status:** MERGED — shipped (0.23.03)
docs/sprints/sprint-87-staleness-trading-sessions.md: MERGED | **Status:** MERGED — shipped (0.23.04)
docs/sprints/sprint-88-filter-verdicts-collection.md: MERGED | **Status:** MERGED — shipped (0.24.00)
docs/sprints/sprint-89-filter-quality-scorecard.md: MERGED | **Status:** MERGED — shipped (0.25.00)
docs/sprints/sprint-90-ci1-parameter-catalogue.md: SPEC | **Status:** SPEC — queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: S**
docs/sprints/sprint-91-ci2-run-metrics.md: SPEC | **Status:** SPEC — queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: M**
docs/sprints/sprint-92-ci3-parameter-set.md: SPEC | **Status:** SPEC — queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: M**
docs/sprints/sprint-93-ci4-experiment-compare.md: SPEC | **Status:** SPEC — queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: M**
docs/sprints/sprint-94-ci5-gate-promote.md: SPEC | **Status:** SPEC — queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: M**
docs/sprints/sprint-95-ci6-optimiser.md: SPEC | **Status:** SPEC — queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: M**
docs/sprints/sprint-96-deliberation-understanding-veto.md: MERGED | **Status:** MERGED — tag `v0.40.00` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: Part A SHIPPED (0.40.00) · Part B mechanism SHIPPED (0.41.00, opt-in, off by default) · **Phase:** Deliberation → runtime (DL-31) · **Effort: L (split A/B)**
docs/sprints/sprint-97-serve-loop-primitive.md: MERGED | **Status:** MERGED — merged to `main` in `389e8fe4` (item 22 review, 2026-09-23); the line read: in progress (0.42.00 → 0.43.00)
docs/sprints/sprint-98-control-plane-serve-supervisor-operator.md: MERGED | **Status:** MERGED — tag `v0.44.00` (cited by its README row) is on `main` (item 22 review, 2026-09-23); the line read: in progress (0.43.00 → 0.44.00)
docs/sprints/sprint-99-control-plane-serve-forecaster-curator-researcher.md: MERGED | **Status:** MERGED — shipped (handover refreshed 2026-07-03 for the 0.50.00 codebase; supersedes the pre-S104 draft)
docs_seen=290 SPEC=11 BUILT=0 MERGED=279 UNMAPPED=0 MISSING=0
uv run python scripts/check_tracker_size.py
[OK] docs/STATE.md: 34,596 of 40,000 bytes (86 %)
[OK] docs/work-queue.md: 47,916 of 64,000 bytes (74 %)
[WARN] docs/sprints/README.md: 93,251 of 96,000 bytes (97 %)
[OK] docs/sprints/INDEX.md: 23,863 of 48,000 bytes (49 %)
[WARN] docs/design-log.md: 478,552 of 512,000 bytes (93 %)
[OK] docs/laws/functionality-checks.md: 138,521 of 160,000 bytes (86 %)
[OK] docs/laws/drift-register.md: 134,514 of 160,000 bytes (84 %)
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
============================= test session starts =============================
collected 5251 items

tests\test_accept_cli.py .                                               [  0%]
tests\test_agent_image_commands.py .                                     [  0%]
tests\test_agreement.py .......                                          [  0%]
tests\test_analyst_held_stop.py ....                                     [  0%]
tests\test_audit_broker_graph.py ....                                    [  0%]
tests\test_backtest_proposal.py ...                                      [  0%]
tests\test_barrier_current_run.py ....                                   [  0%]
tests\test_barrier_ledger.py ...                                         [  0%]
tests\test_barrier_testbed.py .............                              [  0%]
tests\test_bootstrap.py ..............                                   [  1%]
tests\test_boundary_map.py ..........................................    [  1%]
tests\test_brief_preview.py ...                                          [  1%]
tests\test_broker_fill_lifecycle.py ....                                 [  1%]
tests\test_broker_lifecycle_invariants.py ..                             [  1%]
tests\test_broker_probe_orders.py ......                                 [  2%]
tests\test_broker_snapshot_vocabulary.py .                               [  2%]
tests\test_broker_stop_liveness.py ......                                [  2%]
tests\test_broker_stop_replaced.py ...                                   [  2%]
tests\test_broker_stops_contract.py .                                    [  2%]
tests\test_bus.py .....                                                  [  2%]
tests\test_bus_azure.py .......                                          [  2%]
tests\test_bus_azure_config.py ..s........                               [  2%]
tests\test_bus_azure_correlated_ready.py ....                            [  2%]
tests\test_bus_azure_receiver.py .......                                 [  2%]
tests\test_bus_azure_receiver_edges.py ..                                [  3%]
tests\test_bus_celery.py ........s                                       [  3%]
tests\test_bus_pubsub.py ........                                        [  3%]
tests\test_candidate_delivery.py .........                               [  3%]
tests\test_check_dependency_audit.py ..........                          [  3%]
tests\test_check_llm_outage_cli.py .....                                 [  3%]
tests\test_check_markdown_links.py .............                         [  4%]
tests\test_check_module_size.py ........                                 [  4%]
tests\test_check_tracker_size.py .............                           [  4%]
tests\test_check_version_scheme.py .............                         [  4%]
tests\test_claim_check.py .........                                      [  4%]
tests\test_compare_order_tolerances.py ..                                [  4%]
tests\test_compare_stop_targets.py ..                                    [  4%]
tests\test_config.py ...........                                         [  5%]
tests\test_container_sensor_deploy.py ..                                 [  5%]
tests\test_container_sensor_script.py .......                            [  5%]
tests\test_contract_required_fields.py ......                            [  5%]
tests\test_contract_required_payload_fields.py ......                    [  5%]
tests\test_contract_values.py .........                                  [  5%]
tests\test_cred_audit_plan.py .............                              [  5%]
tests\test_crypto.py ......                                              [  6%]
tests\test_debate_lanes_command.py ..............                        [  6%]
tests\test_debate_lanes_live_lifecycle.py ....                           [  6%]
tests\test_debate_lanes_peer_bus.py .                                    [  6%]
tests\test_debate_lanes_reporting.py .........                           [  6%]
tests\test_debate_lanes_startup.py ...                                   [  6%]
tests\test_debate_lanes_timed.py ....                                    [  6%]
tests\test_debate_lanes_transport.py .........                           [  6%]
tests\test_deliberate_script.py ........                                 [  7%]
tests\test_deliberation.py .............                                 [  7%]
tests\test_deliberation_eval.py ............                             [  7%]
tests\test_deliberation_fail_open_execution.py .                         [  7%]
tests\test_deliberation_gate.py .........                                [  7%]
tests\test_deliberation_guided.py .........................              [  8%]
tests\test_deliberation_guided_text.py ...........                       [  8%]
tests\test_deliberation_prompt_artifacts.py ...............              [  8%]
tests\test_deliberation_prompt_facts.py .......                          [  8%]
tests\test_deliberation_prompt_pipeline.py ....                          [  8%]
tests\test_deliberation_prompt_truth.py ......                           [  9%]
tests\test_deliberation_replay.py ..                                     [  9%]
tests\test_deliberation_reproducibility.py ......                        [  9%]
tests\test_deliberation_understanding.py ........                        [  9%]
tests\test_deliberator_anthropic.py ......                               [  9%]
tests\test_deliberator_anthropic_cost.py .....                           [  9%]
tests\test_deliberator_cold_peer_timing.py .                             [  9%]
tests\test_deliberator_contract_values.py .                              [  9%]
tests\test_deliberator_correlated_peer.py ....                           [  9%]
tests\test_deliberator_provider_grant.py ......                          [  9%]
tests\test_deliberator_reply_inbox.py .....                              [  9%]
tests\test_deliberator_runtime.py .....                                  [  9%]
tests\test_deliberator_servicebus_peer.py s..                            [ 10%]
tests\test_deploy_llm_pack.py ..                                         [ 10%]
tests\test_deploy_master_revision.py ........                            [ 10%]
tests\test_deploy_script_cmd_quoting.py ..                               [ 10%]
tests\test_deploy_script_invariants.py ..........                        [ 10%]
tests\test_deploy_tunables_pack.py ..................................... [ 11%]
..................................                                       [ 11%]
tests\test_dispatch_brief_script.py ..                                   [ 11%]
tests\test_dispatch_fire_lines.py ....                                   [ 11%]
tests\test_dispatch_scheduled_run.py ......                              [ 12%]
tests\test_dispatcher_credential.py .                                    [ 12%]
tests\test_dspy_boundary.py ..                                           [ 12%]
tests\test_dspy_engine.py ....                                           [ 12%]
tests\test_dspy_images.py ..............                                 [ 12%]
tests\test_dspy_recipe.py ...                                            [ 12%]
tests\test_ehlo_budget.py ...                                            [ 12%]
tests\test_ehlo_retry.py ...................                             [ 12%]
tests\test_entrypoints.py ..                                             [ 12%]
tests\test_errors.py ....                                                [ 13%]
tests\test_evaluate_return_model.py ..........                           [ 13%]
tests\test_exit_verdict_cli.py .........                                 [ 13%]
tests\test_exit_verdict_rule.py ...                                      [ 13%]
tests\test_exit_verdict_score.py .......                                 [ 13%]
tests\test_exit_verdict_stats.py ...                                     [ 13%]
tests\test_exit_verdict_trips.py ..                                      [ 13%]
tests\test_export_tiingo_bars.py .........                               [ 13%]
tests\test_factor_signal_parity.py .                                     [ 13%]
tests\test_fallback_delivery.py ..                                       [ 13%]
tests\test_fault_graph.py .......                                        [ 14%]
tests\test_fault_incidents.py ...                                        [ 14%]
tests\test_fault_query.py ....                                           [ 14%]
tests\test_fidelity_export.py ....                                       [ 14%]
tests\test_fidelity_export_book.py ...                                   [ 14%]
tests\test_fidelity_export_edges.py .....                                [ 14%]
tests\test_gate_selftest_leaves_nothing.py .s...                         [ 14%]
tests\test_gate_selftest_runner.py ..........                            [ 14%]
tests\test_graph.py ..........                                           [ 14%]
tests\test_graph_backend_rigor.py ...                                    [ 14%]
tests\test_graph_env.py ....                                             [ 14%]
tests\test_graph_keys_without_edge.py ....                               [ 15%]
tests\test_graph_partial_completion.py ..                                [ 15%]
tests\test_graph_postgres.py ......s                                     [ 15%]
tests\test_graph_postgres_keys.py ....s                                  [ 15%]
tests\test_graph_postgres_reconnect.py ....                              [ 15%]
tests\test_graph_vocabulary.py .................                         [ 15%]
tests\test_graph_vocabulary_completeness.py ...........                  [ 15%]
tests\test_graph_vocabulary_deliberation.py ...                          [ 15%]
tests\test_graph_vocabulary_env.py .....                                 [ 16%]
tests\test_graph_vocabulary_properties.py ......                         [ 16%]
tests\test_guided_offline_scripts.py .....                               [ 16%]
tests\test_guided_record_compat.py ...                                   [ 16%]
tests\test_kernel.py ......                                              [ 16%]
tests\test_law_coverage_assertions.py ............                       [ 16%]
tests\test_law_coverage_component_books.py ....                          [ 16%]
tests\test_law_coverage_formats.py ......                                [ 16%]
tests\test_law_coverage_status.py ....                                   [ 16%]
tests\test_lazy_package_exports.py ..                                    [ 17%]
tests\test_line_endings.py ...........                                   [ 17%]
tests\test_llm_adapter_ownership.py ...                                  [ 17%]
tests\test_llm_adapter_security.py ..                                    [ 17%]
tests\test_llm_candidates_step_packs.py ..                               [ 17%]
tests\test_llm_ledger_provenance.py .....                                [ 17%]
tests\test_llm_ledger_repeats.py ..                                      [ 17%]
tests\test_llm_ledger_tokens.py ....                                     [ 17%]
tests\test_llm_outage.py ..........                                      [ 17%]
tests\test_llm_repeat_readers.py ...                                     [ 17%]
tests\test_llm_tokens.py .......                                         [ 17%]
tests\test_master_dockerfile_closure.py ..                               [ 17%]
tests\test_master_wake_window.py ...                                     [ 18%]
tests\test_metrics.py ....                                               [ 18%]
tests\test_mine_factors.py ....                                          [ 18%]
tests\test_no_dspy_at_runtime.py .                                       [ 18%]
tests\test_openai_operator.py .                                          [ 18%]
tests\test_openai_operator_edges.py .......                              [ 18%]
tests\test_openai_operator_security.py .                                 [ 18%]
tests\test_operator_llm_factory.py .....                                 [ 18%]
tests\test_operator_provider_guards.py ...................               [ 18%]
tests\test_operator_responses.py ....                                    [ 18%]
tests\test_operator_responses_edges.py .........                         [ 19%]
tests\test_operator_responses_wire.py .                                  [ 19%]
tests\test_optimizer.py ...                                              [ 19%]
tests\test_order_intent_contract.py .                                    [ 19%]
tests\test_order_tolerance_informativeness.py ..........                 [ 19%]
tests\test_pack_files.py ...................                             [ 19%]
tests\test_param_law_sync.py ........                                    [ 19%]
tests\test_param_law_sync_bounds.py .................                    [ 20%]
tests\test_param_law_sync_component_books.py .                           [ 20%]
tests\test_param_law_sync_excused.py ........                            [ 20%]
tests\test_param_law_sync_execution_rows.py .                            [ 20%]
tests\test_param_law_sync_output.py ...                                  [ 20%]
tests\test_param_law_sync_repo.py ..                                     [ 20%]
tests\test_param_law_sync_values.py .................................    [ 21%]
tests\test_pg_provision_roles.py ........                                [ 21%]
tests\test_pg_teardown_orphans.py .....                                  [ 21%]
tests\test_pg_teardown_targets.py ............                           [ 21%]
tests\test_pm_gate_outcome_graph_roundtrip.py ......                     [ 21%]
tests\test_pm_resumed_book.py ..                                         [ 21%]
tests\test_poll_payloads.py .................                            [ 22%]
tests\test_poll_same_work.py ..............                              [ 22%]
tests\test_positions_contract.py .......                                 [ 22%]
tests\test_prompt_recipe.py ........                                     [ 22%]
tests\test_pytest_servicebus_guard.py ...                                [ 22%]
tests\test_quality_gate.py .......                                       [ 22%]
tests\test_rejected_order_contract.py .                                  [ 22%]
tests\test_repair_close_pnl.py ....                                      [ 22%]
tests\test_repair_orphan_fills.py ....                                   [ 22%]
tests\test_replay_arms.py ....                                           [ 23%]
tests\test_replay_batch.py ........                                      [ 23%]
tests\test_replay_batch_caching.py ...                                   [ 23%]
tests\test_replay_broker.py ..                                           [ 23%]
tests\test_replay_chunks.py .........                                    [ 23%]
tests\test_replay_corpus.py ....                                         [ 23%]
tests\test_replay_day.py .                                               [ 23%]
tests\test_replay_day_portfolio_values.py .                              [ 23%]
tests\test_replay_env_names.py ..                                        [ 23%]
tests\test_replay_episode_exits.py ....                                  [ 23%]
tests\test_replay_exit_arms.py .                                         [ 23%]
tests\test_replay_exit_fills.py ......                                   [ 23%]
tests\test_replay_exit_policy.py .......                                 [ 23%]
tests\test_replay_exit_runs.py ......                                    [ 24%]
tests\test_replay_fidelity.py .......                                    [ 24%]
tests\test_replay_fidelity_book.py ....                                  [ 24%]
tests\test_replay_fidelity_edges.py .....                                [ 24%]
tests\test_replay_fidelity_facts.py ....                                 [ 24%]
tests\test_replay_fidelity_git.py ........                               [ 24%]
tests\test_replay_fidelity_layer2.py ....                                [ 24%]
tests\test_replay_fidelity_layer3.py ..                                  [ 24%]
tests\test_replay_fidelity_verdict.py ..........                         [ 24%]
tests\test_replay_history_calendar.py ..                                 [ 24%]
tests\test_replay_history_rule.py ....                                   [ 25%]
tests\test_replay_keys.py ......                                         [ 25%]
tests\test_replay_ledger.py .....                                        [ 25%]
tests\test_replay_no_lookahead.py .                                      [ 25%]
tests\test_replay_outputs.py ..                                          [ 25%]
tests\test_replay_regime.py .                                            [ 25%]
tests\test_replay_rounds.py ...............                              [ 25%]
tests\test_replay_runner.py ..                                           [ 25%]
tests\test_replay_runner_counts.py ..                                    [ 25%]
tests\test_replay_runner_progress.py .                                   [ 25%]
tests\test_replay_series.py .                                            [ 25%]
tests\test_replay_session_helpers.py .                                   [ 25%]
tests\test_replay_settings.py ..                                         [ 25%]
tests\test_replay_universe.py ....                                       [ 25%]
tests\test_replay_verdict_edge.py ...                                    [ 25%]
tests\test_replay_verdict_refusals.py ........                           [ 26%]
tests\test_replay_verdict_rule.py ..........                             [ 26%]
tests\test_replay_verdict_stats.py .....                                 [ 26%]
tests\test_researcher_contract_values.py ..                              [ 26%]
tests\test_retrain_return_model.py ...........                           [ 26%]
tests\test_sb_provision_sas.py ...                                       [ 26%]
tests\test_sb_sas_plan.py ...                                            [ 26%]
tests\test_score_arithmetic.py ...                                       [ 26%]
tests\test_score_arithmetic_analyst.py ...............                   [ 27%]
tests\test_score_arithmetic_compat.py ...                                [ 27%]
tests\test_score_arithmetic_guards.py ...............                    [ 27%]
tests\test_score_arithmetic_pins.py .......                              [ 27%]
tests\test_score_arithmetic_regime.py .....                              [ 27%]
tests\test_seed_key_vault_script.py .....                                [ 27%]
tests\test_serve_loop.py ....                                            [ 27%]
tests\test_serve_stop.py ...                                             [ 27%]
tests\test_serve_transport.py .....                                      [ 27%]
tests\test_served_agent_images.py .....                                  [ 28%]
tests\test_served_agent_roster_plan_stability.py ....                    [ 28%]
tests\test_served_request_faults.py ......                               [ 28%]
tests\test_served_request_settlement.py .......                          [ 28%]
tests\test_servicebus_prepare_routes.py .                                [ 28%]
tests\test_servicebus_request.py .                                       [ 28%]
tests\test_settlement_rider_offline.py .                                 [ 28%]
tests\test_sp500_bars.py ....                                            [ 28%]
tests\test_sp500_context.py .....                                        [ 28%]
tests\test_sp500_coverage.py ..                                          [ 28%]
tests\test_sp500_membership.py ...                                       [ 28%]
tests\test_sp500_replay_guards.py ......                                 [ 28%]
tests\test_sp500_replay_identity.py ....                                 [ 28%]
tests\test_sp500_wiki.py ..                                              [ 28%]
tests\test_sprint_status.py .....................                        [ 29%]
tests\test_startup.py ....                                               [ 29%]
tests\test_stop_closing.py .....                                         [ 29%]
tests\test_stop_entrypoints.py .                                         [ 29%]
tests\test_stop_resources.py ..                                          [ 29%]
tests\test_stop_rule.py ...                                              [ 29%]
tests\test_stop_signal.py .....                                          [ 29%]
tests\test_stop_width.py ........                                        [ 29%]
tests\test_stop_width_reads.py .....                                     [ 29%]
tests\test_stop_width_reads_guard.py ..                                  [ 29%]
tests\test_substrate_handshake_wire.py ....                              [ 30%]
tests\test_substrate_import_closure.py .                                 [ 30%]
tests\test_substrate_import_wall.py ..                                   [ 30%]
tests\test_substrate_no_pack_literals.py .                               [ 30%]
tests\test_switch_llm_apply.py .....                                     [ 30%]
tests\test_switch_llm_boundaries.py .......                              [ 30%]
tests\test_switch_llm_config.py .............                            [ 30%]
tests\test_switch_llm_planner_review.py ..                               [ 30%]
tests\test_switch_llm_proof.py .............                             [ 30%]
tests\test_switch_llm_refusals.py ............                           [ 31%]
tests\test_tunable_envelopes.py ......                                   [ 31%]
tests\test_verdict_metrics.py .......                                    [ 31%]
tests\test_verdict_sources.py .....                                      [ 31%]
tests\test_veto_context.py ......                                        [ 31%]
tests\test_veto_context_value_labels.py .                                [ 31%]
tests\test_veto_context_verdict_attribution.py .....                     [ 31%]
tests\test_vocabulary_step.py ....                                       [ 31%]
tests\test_work_loop.py ........                                         [ 31%]
tests\test_work_loop_quarantine.py ..........                            [ 32%]
tests\test_work_loop_storm.py ..                                         [ 32%]
tests\test_work_stop.py ....                                             [ 32%]
tests\test_work_stop_signal.py ..                                        [ 32%]
agents\analyst\tests\test_analyst_agent.py ..........                    [ 32%]
agents\analyst\tests\test_analyst_alpha_feature_edges.py .               [ 32%]
agents\analyst\tests\test_analyst_alpha_features.py ........             [ 32%]
agents\analyst\tests\test_analyst_alpha_integration.py ......            [ 32%]
agents\analyst\tests\test_analyst_alpha_pillar.py .........              [ 32%]
agents\analyst\tests\test_analyst_boundary.py .                          [ 32%]
agents\analyst\tests\test_analyst_domain.py ..........                   [ 33%]
agents\analyst\tests\test_analyst_entrypoint.py .                        [ 33%]
agents\analyst\tests\test_analyst_poll.py .........                      [ 33%]
agents\analyst\tests\test_analyst_poll_processed.py .                    [ 33%]
agents\analyst\tests\test_analyst_pubsub.py .....                        [ 33%]
agents\analyst\tests\test_analyst_settings.py .....                      [ 33%]
agents\analyst\tests\test_analyst_store.py ...                           [ 33%]
agents\analyst\tests\test_analyze_domain.py ...                          [ 33%]
agents\analyst\tests\test_broker_stop_deferral.py .                      [ 33%]
agents\analyst\tests\test_exit_authority.py ....                         [ 33%]
agents\analyst\tests\test_fundamental_rules.py ......................... [ 34%]
...................                                                      [ 34%]
agents\analyst\tests\test_indicators.py ..................               [ 34%]
agents\analyst\tests\test_indicators_event.py ........                   [ 35%]
agents\analyst\tests\test_indicators_kernel.py ................          [ 35%]
agents\analyst\tests\test_indicators_pattern.py ........................ [ 35%]
....                                                                     [ 35%]
agents\analyst\tests\test_indicators_pattern_edges.py ..........         [ 36%]
agents\analyst\tests\test_indicators_pattern_triangles.py ..             [ 36%]
agents\analyst\tests\test_indicators_range.py ........................   [ 36%]
agents\analyst\tests\test_measured_stop_targets.py ......                [ 36%]
agents\analyst\tests\test_p2_slice.py .                                  [ 36%]
agents\analyst\tests\test_position_sync_poll_branches.py ..              [ 36%]
agents\analyst\tests\test_recommend_domain.py ......                     [ 36%]
agents\analyst\tests\test_relative_strength.py .............             [ 37%]
agents\analyst\tests\test_scaled_stop_targets.py .........               [ 37%]
agents\analyst\tests\test_sentiment_fixture_measurement.py .             [ 37%]
agents\analyst\tests\test_sentiment_reading.py .........                 [ 37%]
agents\analyst\tests\test_sentiment_rules.py ............                [ 37%]
agents\analyst\tests\test_sentiment_subject.py ......................... [ 38%]
...                                                                      [ 38%]
agents\analyst\tests\test_sentiment_weighting.py .....                   [ 38%]
agents\analyst\tests\test_signal_selection.py ........                   [ 38%]
agents\analyst\tests\test_stop_target_backfill.py .......                [ 38%]
agents\analyst\tests\test_stop_target_evidence.py ....                   [ 38%]
agents\analyst\tests\test_stop_target_live_positions.py .                [ 38%]
agents\analyst\tests\test_stop_target_outcome.py ..........              [ 38%]
agents\analyst\tests\test_technical_rules.py ........................... [ 39%]
.                                                                        [ 39%]
agents\analyst\tests\test_technical_rules_event.py .............         [ 39%]
agents\analyst\tests\test_technical_rules_pattern.py .................   [ 40%]
agents\analyst\tests\test_technical_rules_range.py ..................... [ 40%]
...                                                                      [ 40%]
agents\analyst\tests\test_unified_held_analysis.py ..                    [ 40%]
agents\curator\tests\test_assembly.py .....                              [ 40%]
agents\curator\tests\test_build_dataset.py .......                       [ 40%]
agents\curator\tests\test_curator_entrypoint.py .                        [ 40%]
agents\curator\tests\test_filter_quality.py ....                         [ 40%]
agents\curator\tests\test_manifest.py ..                                 [ 40%]
agents\curator\tests\test_p10_boundary.py .                              [ 40%]
agents\curator\tests\test_p10_exit.py ..                                 [ 40%]
agents\curator\tests\test_p10_training_boundary.py .                     [ 40%]
agents\curator\tests\test_promote_predictor.py .......                   [ 41%]
agents\curator\tests\test_registry.py .......                            [ 41%]
agents\curator\tests\test_split.py ...                                   [ 41%]
agents\curator\tests\test_store.py ..                                    [ 41%]
agents\curator\tests\test_train_predictor.py .....                       [ 41%]
agents\curator\tests\test_training.py ......                             [ 41%]
agents\deliberator\tests\test_activated_candidate.py ......              [ 41%]
agents\deliberator\tests\test_answered_models.py ..                      [ 41%]
agents\deliberator\tests\test_concurrent_reviews.py ...                  [ 41%]
agents\deliberator\tests\test_deliberator_agent.py ..                    [ 41%]
agents\deliberator\tests\test_deliberator_imports.py .                   [ 41%]
agents\deliberator\tests\test_deliberator_pending_payloads.py .          [ 41%]
agents\deliberator\tests\test_dspy_concurrency.py .                      [ 41%]
agents\deliberator\tests\test_dspy_runtime.py .                          [ 41%]
agents\deliberator\tests\test_dspy_turn_parity.py ...................... [ 42%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 46%]
............................                                             [ 46%]
agents\deliberator\tests\test_fail_open_reason.py ...                    [ 46%]
agents\deliberator\tests\test_guided_record.py ......                    [ 47%]
agents\deliberator\tests\test_guided_turn.py ..                          [ 47%]
agents\deliberator\tests\test_guided_turn_edges.py ........              [ 47%]
agents\deliberator\tests\test_handed_fallbacks.py .........              [ 47%]
agents\deliberator\tests\test_judge_non_answer_fail_open.py ...          [ 47%]
agents\deliberator\tests\test_ledger_usage_forwarding.py ..              [ 47%]
agents\deliberator\tests\test_llm_openai_adapter.py ....                 [ 47%]
agents\deliberator\tests\test_llm_openai_usage.py .....                  [ 47%]
agents\deliberator\tests\test_llm_output_bounds.py ...                   [ 47%]
agents\deliberator\tests\test_llm_provider.py ..........                 [ 47%]
agents\deliberator\tests\test_manager_preflight.py ....                  [ 48%]
agents\deliberator\tests\test_orphaned_reply_count.py .                  [ 48%]
agents\deliberator\tests\test_output_cap_requests.py ......              [ 48%]
agents\deliberator\tests\test_output_limits.py ..                        [ 48%]
agents\deliberator\tests\test_peer_ledger_repeats.py .                   [ 48%]
agents\deliberator\tests\test_provider_default_model.py ...........      [ 48%]
agents\deliberator\tests\test_refusal_attempts.py ...................... [ 48%]
                                                                         [ 48%]
agents\deliberator\tests\test_refusal_concurrency.py ..                  [ 48%]
agents\deliberator\tests\test_refusal_run.py ...                         [ 48%]
agents\deliberator\tests\test_review_veto_semantics.py ...               [ 49%]
agents\deliberator\tests\test_stop_reason_fail_open.py ..                [ 49%]
agents\execution\tests\test_account_snapshot.py ....                     [ 49%]
agents\execution\tests\test_alpaca_account.py ..                         [ 49%]
agents\execution\tests\test_alpaca_adoption.py .                         [ 49%]
agents\execution\tests\test_alpaca_broker.py ...........                 [ 49%]
agents\execution\tests\test_alpaca_http_errors.py ..                     [ 49%]
agents\execution\tests\test_alpaca_order_reads.py .........              [ 49%]
agents\execution\tests\test_alpaca_stop_orders.py .....                  [ 49%]
agents\execution\tests\test_broker_evidence_ownership.py .               [ 49%]
agents\execution\tests\test_broker_positions.py ........                 [ 49%]
agents\execution\tests\test_broker_stop_branch_edges.py .....            [ 49%]
agents\execution\tests\test_broker_stop_edges.py .......                 [ 50%]
agents\execution\tests\test_broker_stop_pending_position.py ..           [ 50%]
agents\execution\tests\test_broker_stop_realign.py .......               [ 50%]
agents\execution\tests\test_broker_stop_replace_adapters.py ......       [ 50%]
agents\execution\tests\test_broker_stop_replacement.py .....             [ 50%]
agents\execution\tests\test_broker_stop_replacement_e2e.py .             [ 50%]
agents\execution\tests\test_broker_stop_sold_edges.py .                  [ 50%]
agents\execution\tests\test_broker_stop_unprotected.py ...               [ 50%]
agents\execution\tests\test_broker_stops.py ....                         [ 50%]
agents\execution\tests\test_deliberation_posture.py .......              [ 50%]
agents\execution\tests\test_deliberation_posture_degraded.py ...         [ 50%]
agents\execution\tests\test_divergence_flag_ownership.py .               [ 50%]
agents\execution\tests\test_drop_sweep.py ......                         [ 50%]
agents\execution\tests\test_drop_sweep_ack.py .....                      [ 51%]
agents\execution\tests\test_drop_sweep_append_safe.py ......             [ 51%]
agents\execution\tests\test_drop_sweep_edges.py ......                   [ 51%]
agents\execution\tests\test_drop_sweep_identity.py ..                    [ 51%]
agents\execution\tests\test_drop_sweep_liveness.py ..                    [ 51%]
agents\execution\tests\test_drop_sweep_reads.py .....                    [ 51%]
agents\execution\tests\test_execution_agent.py ......                    [ 51%]
agents\execution\tests\test_execution_deliberation_gate.py ............  [ 51%]
agents\execution\tests\test_execution_domain.py ......                   [ 51%]
agents\execution\tests\test_execution_entrypoint.py ..                   [ 51%]
agents\execution\tests\test_execution_pending_payloads.py ..             [ 52%]
agents\execution\tests\test_execution_poll.py .......                    [ 52%]
agents\execution\tests\test_execution_pubsub.py .....                    [ 52%]
agents\execution\tests\test_exit_stop_cancel.py .....                    [ 52%]
agents\execution\tests\test_exit_stops.py ..                             [ 52%]
agents\execution\tests\test_fill_attempts.py ..                          [ 52%]
agents\execution\tests\test_fill_refresh_terminal.py ......              [ 52%]
agents\execution\tests\test_fill_refresh_unresolved_pnl.py ...           [ 52%]
agents\execution\tests\test_filled_entry_stops.py .....                  [ 52%]
agents\execution\tests\test_graph_write_failure_retry.py ...             [ 52%]
agents\execution\tests\test_order_tolerance.py ....                      [ 52%]
agents\execution\tests\test_p3_execution_slice.py .                      [ 52%]
agents\execution\tests\test_partial_fill_completion.py ...               [ 52%]
agents\execution\tests\test_partial_fill_mapping.py .............        [ 53%]
agents\execution\tests\test_partial_fill_pnl.py .                        [ 53%]
agents\execution\tests\test_partial_fill_refresh.py .......              [ 53%]
agents\execution\tests\test_position_sync_drop_sweep.py ..               [ 53%]
agents\execution\tests\test_position_sync_poll.py .....                  [ 53%]
agents\execution\tests\test_position_sync_work_items.py ...              [ 53%]
agents\execution\tests\test_promote_stage.py ......                      [ 53%]
agents\execution\tests\test_realized_pnl_multilot.py ..                  [ 53%]
agents\execution\tests\test_realized_pnl_refresh.py .....                [ 53%]
agents\execution\tests\test_reconciliation.py ...                        [ 53%]
agents\execution\tests\test_reconciliation_active_positions.py .         [ 53%]
agents\execution\tests\test_reconciliation_flag_episodes.py ....         [ 53%]
agents\execution\tests\test_reconciliation_flag_sweep.py ...             [ 53%]
agents\execution\tests\test_reconciliation_flag_upgrade.py .......       [ 54%]
agents\execution\tests\test_reconciliation_flags.py ......               [ 54%]
agents\execution\tests\test_run_start_orders.py .....                    [ 54%]
agents\execution\tests\test_scaled_order_tolerance.py .......            [ 54%]
agents\execution\tests\test_stage_gate.py .....                          [ 54%]
agents\execution\tests\test_stop_derivation_provenance.py ....           [ 54%]
agents\execution\tests\test_stop_expiry_beyond_page.py ...               [ 54%]
agents\execution\tests\test_tolerance_evidence.py ....                   [ 54%]
agents\forecaster\tests\test_barrier_claim.py .....                      [ 54%]
agents\forecaster\tests\test_barrier_garch.py ................           [ 55%]
agents\forecaster\tests\test_barrier_garch_oracle.py .....s              [ 55%]
agents\forecaster\tests\test_barrier_poll.py .....                       [ 55%]
agents\forecaster\tests\test_barrier_refusal_severity.py .........       [ 55%]
agents\forecaster\tests\test_barrier_refusals.py ..............          [ 55%]
agents\forecaster\tests\test_barrier_route.py ..                         [ 55%]
agents\forecaster\tests\test_barrier_scorecard.py ....                   [ 55%]
agents\forecaster\tests\test_barrier_scorecard_oracle.py ..              [ 55%]
agents\forecaster\tests\test_barrier_settlement.py ...............       [ 56%]
agents\forecaster\tests\test_barrier_settlement_faults.py ...            [ 56%]
agents\forecaster\tests\test_barrier_settlement_loop.py ...              [ 56%]
agents\forecaster\tests\test_barrier_settlement_record.py .....          [ 56%]
agents\forecaster\tests\test_factor_signal.py ......                     [ 56%]
agents\forecaster\tests\test_forecaster_agent.py .......                 [ 56%]
agents\forecaster\tests\test_forecaster_boundary.py ...                  [ 56%]
agents\forecaster\tests\test_forecaster_domain.py ......                 [ 56%]
agents\forecaster\tests\test_forecaster_entrypoint.py ..                 [ 56%]
agents\forecaster\tests\test_forecaster_evaluation.py ...........        [ 57%]
agents\forecaster\tests\test_forecaster_factor_agent.py .....            [ 57%]
agents\forecaster\tests\test_forecaster_features.py ......               [ 57%]
agents\forecaster\tests\test_forecaster_finbert.py ..                    [ 57%]
agents\forecaster\tests\test_forecaster_lightgbm.py .                    [ 57%]
agents\forecaster\tests\test_forecaster_model.py ...                     [ 57%]
agents\forecaster\tests\test_forecaster_model_trainer.py .......         [ 57%]
agents\forecaster\tests\test_forecaster_pending_payloads.py ......       [ 57%]
agents\forecaster\tests\test_forecaster_poll.py ...                      [ 57%]
agents\forecaster\tests\test_forecaster_retrain_policy.py ...........    [ 57%]
agents\forecaster\tests\test_forecaster_return_agent.py .....            [ 58%]
agents\forecaster\tests\test_forecaster_return_labels.py ......          [ 58%]
agents\forecaster\tests\test_forecaster_return_model.py ...              [ 58%]
agents\forecaster\tests\test_forecaster_return_scorecard.py .....        [ 58%]
agents\forecaster\tests\test_forecaster_return_scorecard_math.py ....... [ 58%]
....                                                                     [ 58%]
agents\forecaster\tests\test_forecaster_store.py ......                  [ 58%]
agents\forecaster\tests\test_scorecard_math.py .....                     [ 58%]
agents\forecaster\tests\test_sentiment_scorecard.py ...                  [ 58%]
agents\forecaster\tests\test_statistics.py ..............                [ 59%]
agents\master\tests\test_activation_replay.py ....                       [ 59%]
agents\master\tests\test_activation_replay_store.py ....                 [ 59%]
agents\master\tests\test_candidate_activation.py .........               [ 59%]
agents\master\tests\test_candidate_declaration.py ..................     [ 59%]
agents\master\tests\test_candidate_expansion.py ......                   [ 59%]
agents\master\tests\test_candidate_fleet.py ...                          [ 59%]
agents\master\tests\test_candidate_probe.py .........                    [ 60%]
agents\master\tests\test_credential_probe_body.py ..............         [ 60%]
agents\master\tests\test_credential_probe_classification.py ...          [ 60%]
agents\master\tests\test_credential_probe_dsn.py ....                    [ 60%]
agents\master\tests\test_credential_probe_loading.py ......              [ 60%]
agents\master\tests\test_credential_probe_openai.py ...........          [ 60%]
agents\master\tests\test_credential_probes.py ........                   [ 60%]
agents\master\tests\test_credential_test.py .........                    [ 61%]
agents\master\tests\test_ehlo_budgets.py ...                             [ 61%]
agents\master\tests\test_ehlo_server.py ...                              [ 61%]
agents\master\tests\test_ehlo_server_routes.py ..                        [ 61%]
agents\master\tests\test_fallback_declaration.py ....                    [ 61%]
agents\master\tests\test_fallback_handover.py .......                    [ 61%]
agents\master\tests\test_fleet_preflight.py .......                      [ 61%]
agents\master\tests\test_fleet_preflight_faults.py .                     [ 61%]
agents\master\tests\test_fleet_preflight_loop.py ..                      [ 61%]
agents\master\tests\test_fleet_preflight_packs.py ..                     [ 61%]
agents\master\tests\test_grants.py ...                                   [ 61%]
agents\master\tests\test_http_server.py .....                            [ 61%]
agents\master\tests\test_identity.py .                                   [ 61%]
agents\master\tests\test_key_vault.py .........                          [ 62%]
agents\master\tests\test_master_agent.py .............                   [ 62%]
agents\master\tests\test_master_entrypoint.py ........                   [ 62%]
agents\master\tests\test_provider_selection.py .....                     [ 62%]
agents\master\tests\test_provider_selection_refusals.py ......           [ 62%]
agents\master\tests\test_remediation.py ................                 [ 62%]
agents\master\tests\test_remediation_activation.py ...                   [ 62%]
agents\master\tests\test_remediation_auto_activation.py ..               [ 63%]
agents\master\tests\test_remediation_execution.py .......                [ 63%]
agents\master\tests\test_remediation_execution_graph.py ......           [ 63%]
agents\master\tests\test_remediation_gate.py ..........                  [ 63%]
agents\master\tests\test_remediation_posture.py ....                     [ 63%]
agents\master\tests\test_remediation_prompt_artifact.py ......           [ 63%]
agents\master\tests\test_secret_cache.py ....                            [ 63%]
agents\master\tests\test_secret_map.py ...................               [ 64%]
agents\master\tests\test_stop_deadline.py ..                             [ 64%]
agents\master\tests\test_stop_preflight.py ..                            [ 64%]
agents\master\tests\test_stop_process.py .                               [ 64%]
agents\master\tests\test_stop_server.py .....                            [ 64%]
agents\master\tests\test_stop_session.py ......                          [ 64%]
agents\master\tests\test_vault_seed.py ...........                       [ 64%]
agents\monitor\tests\test_adr0015_close_lifecycle.py ..                  [ 64%]
agents\monitor\tests\test_broker_reconcile.py .....                      [ 64%]
agents\monitor\tests\test_broker_reconcile_edges.py .                    [ 64%]
agents\monitor\tests\test_monitor_agent.py ..........                    [ 64%]
agents\monitor\tests\test_monitor_agent_branches.py .                    [ 64%]
agents\monitor\tests\test_monitor_entrypoint.py .                        [ 64%]
agents\monitor\tests\test_monitor_exits.py ....                          [ 65%]
agents\monitor\tests\test_monitor_pending_payloads.py ...                [ 65%]
agents\monitor\tests\test_monitor_poll.py .......                        [ 65%]
agents\monitor\tests\test_monitor_position_sync.py .....                 [ 65%]
agents\monitor\tests\test_monitor_position_sync_work_items.py ....       [ 65%]
agents\monitor\tests\test_monitor_pubsub.py .....                        [ 65%]
agents\monitor\tests\test_monitor_store.py ..                            [ 65%]
agents\monitor\tests\test_p3_monitor_slice.py .                          [ 65%]
agents\monitor\tests\test_position_from_partial_fill.py .                [ 65%]
agents\monitor\tests\test_realized_pnl.py .....                          [ 65%]
agents\operator\tests\test_cutoff_adapter.py .........                   [ 65%]
agents\operator\tests\test_cutoff_agent.py ..........                    [ 66%]
agents\operator\tests\test_cutoff_ledger.py .....                        [ 66%]
agents\operator\tests\test_failed_request_agent.py ...                   [ 66%]
agents\operator\tests\test_failed_request_faults.py .......              [ 66%]
agents\operator\tests\test_failed_request_ledger.py .....                [ 66%]
agents\operator\tests\test_failed_request_result.py .................... [ 66%]
..                                                                       [ 66%]
agents\operator\tests\test_operator_agent.py ......                      [ 66%]
agents\operator\tests\test_operator_approve_routing.py ......            [ 67%]
agents\operator\tests\test_operator_boundary.py ..                       [ 67%]
agents\operator\tests\test_operator_entrypoint.py .                      [ 67%]
agents\operator\tests\test_operator_evidence_flags.py ..                 [ 67%]
agents\operator\tests\test_operator_grammar.py .......                   [ 67%]
agents\operator\tests\test_operator_llm.py ........                      [ 67%]
agents\operator\tests\test_operator_llm_usage.py ....                    [ 67%]
agents\operator\tests\test_operator_settings.py ........                 [ 67%]
agents\operator\tests\test_operator_store.py .                           [ 67%]
agents\operator\tests\test_parameter_values.py ......................... [ 68%]
.                                                                        [ 68%]
agents\operator\tests\test_provider_model.py ..                          [ 68%]
agents\operator\tests\test_required_parameters.py ...................... [ 68%]
.............                                                            [ 68%]
agents\portfolio_manager\tests\test_account_sizing.py .....              [ 68%]
agents\portfolio_manager\tests\test_account_staleness.py ...             [ 69%]
agents\portfolio_manager\tests\test_concentration_deployed_correlation.py . [ 69%]
.                                                                        [ 69%]
agents\portfolio_manager\tests\test_concentration_deployed_sector.py ... [ 69%]
....                                                                     [ 69%]
agents\portfolio_manager\tests\test_concentration_no_shock.py .....      [ 69%]
agents\portfolio_manager\tests\test_correlation_census.py ......         [ 69%]
agents\portfolio_manager\tests\test_correlation_census_gate.py ..        [ 69%]
agents\portfolio_manager\tests\test_correlation_concentration.py ...     [ 69%]
agents\portfolio_manager\tests\test_correlation_edges.py ......          [ 69%]
agents\portfolio_manager\tests\test_correlation_market_context.py .      [ 69%]
agents\portfolio_manager\tests\test_correlation_ramp.py .........        [ 69%]
agents\portfolio_manager\tests\test_gate_reachability.py .               [ 69%]
agents\portfolio_manager\tests\test_graph_portfolio.py ..                [ 69%]
agents\portfolio_manager\tests\test_held_book_marks.py .....             [ 69%]
agents\portfolio_manager\tests\test_issuer_concentration.py .......      [ 70%]
agents\portfolio_manager\tests\test_order_volatility.py ..               [ 70%]
agents\portfolio_manager\tests\test_p3_slice.py .                        [ 70%]
agents\portfolio_manager\tests\test_pm_entrypoint.py .                   [ 70%]
agents\portfolio_manager\tests\test_pm_poll.py ........                  [ 70%]
agents\portfolio_manager\tests\test_pm_pubsub.py .....                   [ 70%]
agents\portfolio_manager\tests\test_pm_run_record.py .                   [ 70%]
agents\portfolio_manager\tests\test_portfolio_manager_agent.py ......    [ 70%]
agents\portfolio_manager\tests\test_portfolio_manager_audit.py .....     [ 70%]
agents\portfolio_manager\tests\test_portfolio_manager_edges.py .......   [ 70%]
agents\portfolio_manager\tests\test_portfolio_manager_failures.py ....   [ 70%]
agents\portfolio_manager\tests\test_rejection_empty_reports.py ...       [ 70%]
agents\portfolio_manager\tests\test_rejection_gate_reports.py ....       [ 71%]
agents\portfolio_manager\tests\test_rejection_precedence.py ...          [ 71%]
agents\portfolio_manager\tests\test_rejection_store.py .                 [ 71%]
agents\portfolio_manager\tests\test_resumed_book.py ......               [ 71%]
agents\portfolio_manager\tests\test_reward_risk.py .......               [ 71%]
agents\portfolio_manager\tests\test_reward_risk_measured_excursion.py .. [ 71%]
....                                                                     [ 71%]
agents\portfolio_manager\tests\test_scaled_stop_rr_gate.py ....          [ 71%]
agents\portfolio_manager\tests\test_sector_book_edges.py .               [ 71%]
agents\portfolio_manager\tests\test_sector_cap.py .....                  [ 71%]
agents\portfolio_manager\tests\test_sector_evidence_labels.py ...        [ 71%]
agents\portfolio_manager\tests\test_sector_name_count.py ......          [ 71%]
agents\portfolio_manager\tests\test_unified_exits.py .......             [ 71%]
agents\provider\tests\test_alpaca_data.py ........                       [ 72%]
agents\provider\tests\test_alpaca_raw_bars.py ..                         [ 72%]
agents\provider\tests\test_alpaca_request.py ....                        [ 72%]
agents\provider\tests\test_alpaca_sip.py .....                           [ 72%]
agents\provider\tests\test_av_sentiment.py .....                         [ 72%]
agents\provider\tests\test_barrier_history.py ....                       [ 72%]
agents\provider\tests\test_barrier_history_failures.py ...               [ 72%]
agents\provider\tests\test_barrier_window_as_of.py ......                [ 72%]
agents\provider\tests\test_composite_vix_notes.py .                      [ 72%]
agents\provider\tests\test_domain.py ......                              [ 72%]
agents\provider\tests\test_earnings_source.py ............               [ 73%]
agents\provider\tests\test_finnhub_provider_resilience.py .              [ 73%]
agents\provider\tests\test_finnhub_resilience.py .....                   [ 73%]
agents\provider\tests\test_fmp.py ....                                   [ 73%]
agents\provider\tests\test_fmp_vix.py ..............                     [ 73%]
agents\provider\tests\test_graph_pull_trigger.py ..                      [ 73%]
agents\provider\tests\test_ingest.py .............                       [ 73%]
agents\provider\tests\test_ingest_chunked.py ........                    [ 73%]
agents\provider\tests\test_market_calendar.py ....                       [ 73%]
agents\provider\tests\test_market_calendar_history.py .................. [ 74%]
....................................................................     [ 75%]
agents\provider\tests\test_newest_session_guard.py .......               [ 75%]
agents\provider\tests\test_news_source.py .............                  [ 76%]
agents\provider\tests\test_provider_agent.py .....                       [ 76%]
agents\provider\tests\test_provider_benchmark_ingest.py ......           [ 76%]
agents\provider\tests\test_provider_earnings_horizon.py ......           [ 76%]
agents\provider\tests\test_provider_entrypoint.py ..                     [ 76%]
agents\provider\tests\test_provider_fundamentals.py ...                  [ 76%]
agents\provider\tests\test_provider_news.py ...                          [ 76%]
agents\provider\tests\test_provider_poll.py .....                        [ 76%]
agents\provider\tests\test_provider_pubsub.py ......                     [ 76%]
agents\provider\tests\test_provider_reconcile.py ..                      [ 76%]
agents\provider\tests\test_provider_regime_vix.py ...                    [ 76%]
agents\provider\tests\test_provider_sentiment.py ...                     [ 76%]
agents\provider\tests\test_run_as_of_refusals.py ...........             [ 77%]
agents\provider\tests\test_run_as_of_window.py ......                    [ 77%]
agents\provider\tests\test_sector_cache.py ...                           [ 77%]
agents\provider\tests\test_sector_source.py ..........                   [ 77%]
agents\provider\tests\test_served_fact_provenance.py ..                  [ 77%]
agents\provider\tests\test_sources.py .........s                         [ 77%]
agents\provider\tests\test_stooq.py ....s                                [ 77%]
agents\provider\tests\test_tiingo.py ....                                [ 77%]
agents\reporter\tests\test_benchmark_lineage.py ..                       [ 77%]
agents\reporter\tests\test_benchmark_lineage_edges.py .......            [ 77%]
agents\reporter\tests\test_book_window.py ......                         [ 78%]
agents\reporter\tests\test_book_window_edges.py .....                    [ 78%]
agents\reporter\tests\test_metrics_narrative.py .....                    [ 78%]
agents\reporter\tests\test_p3_reporter_slice.py .                        [ 78%]
agents\reporter\tests\test_performance.py ...                            [ 78%]
agents\reporter\tests\test_performance_compat.py .                       [ 78%]
agents\reporter\tests\test_performance_day_point.py ...                  [ 78%]
agents\reporter\tests\test_performance_inputs_edges.py ..                [ 78%]
agents\reporter\tests\test_performance_metrics.py .....                  [ 78%]
agents\reporter\tests\test_performance_snapshot.py .....                 [ 78%]
agents\reporter\tests\test_reporter_agent.py ......                      [ 78%]
agents\reporter\tests\test_reporter_boundary.py .                        [ 78%]
agents\reporter\tests\test_reporter_entrypoint.py .                      [ 78%]
agents\reporter\tests\test_reporter_poll.py ....                         [ 78%]
agents\reporter\tests\test_reporter_pubsub.py .....                      [ 78%]
agents\reporter\tests\test_store_lineage.py ....                         [ 79%]
agents\reporter\tests\test_trade_outcomes.py ............                [ 79%]
agents\researcher\tests\test_backtest.py .......                         [ 79%]
agents\researcher\tests\test_evidence.py ...                             [ 79%]
agents\researcher\tests\test_factors.py .......                          [ 79%]
agents\researcher\tests\test_p7_boundary.py .                            [ 79%]
agents\researcher\tests\test_proposal.py .....                           [ 79%]
agents\researcher\tests\test_propose.py .....                            [ 79%]
agents\researcher\tests\test_researcher_entrypoint.py .                  [ 79%]
agents\scanner\tests\test_boundary.py .                                  [ 79%]
agents\scanner\tests\test_scan_verdict_persistence.py ....               [ 79%]
agents\scanner\tests\test_scanner_agent.py .....                         [ 80%]
agents\scanner\tests\test_scanner_agent_beta.py ..                       [ 80%]
agents\scanner\tests\test_scanner_beta.py .....                          [ 80%]
agents\scanner\tests\test_scanner_domain.py .                            [ 80%]
agents\scanner\tests\test_scanner_earnings.py .........                  [ 80%]
agents\scanner\tests\test_scanner_earnings_horizon.py ......             [ 80%]
agents\scanner\tests\test_scanner_entrypoint.py .                        [ 80%]
agents\scanner\tests\test_scanner_explain.py .                           [ 80%]
agents\scanner\tests\test_scanner_poll.py .....                          [ 80%]
agents\scanner\tests\test_scanner_poll_benchmark.py ..                   [ 80%]
agents\scanner\tests\test_scanner_pubsub.py ......                       [ 80%]
agents\scanner\tests\test_scanner_settings.py .                          [ 80%]
agents\scanner\tests\test_scanner_verdicts.py ...                        [ 80%]
agents\scanner\tests\test_store.py .                                     [ 80%]
agents\scanner\tests\test_universe.py ....                               [ 80%]
agents\supervisor\tests\test_p5_exit.py ...                              [ 80%]
agents\supervisor\tests\test_resume_dispatch.py ...                      [ 81%]
agents\supervisor\tests\test_stage_dispatch.py ...                       [ 81%]
agents\supervisor\tests\test_supervisor_agent.py .........               [ 81%]
agents\supervisor\tests\test_supervisor_entrypoint.py .                  [ 81%]
agents\supervisor\tests\test_supervisor_fault_incidents.py ..            [ 81%]
agents\supervisor\tests\test_supervisor_gate.py .....                    [ 81%]
agents\supervisor\tests\test_supervisor_health_flags.py ......           [ 81%]
agents\supervisor\tests\test_supervisor_health_sources.py .              [ 81%]
agents\supervisor\tests\test_supervisor_last_run.py ..                   [ 81%]
orchestration\tests\test_act_by_local_time.py ...                        [ 81%]
orchestration\tests\test_adr0015_graph_pull.py .                         [ 81%]
orchestration\tests\test_barrier_claim_as_of.py ...                      [ 81%]
orchestration\tests\test_batch_trace.py ........                         [ 81%]
orchestration\tests\test_container_alarm_text.py ..                      [ 81%]
orchestration\tests\test_container_alarm_words.py ...............        [ 82%]
orchestration\tests\test_container_brief.py .....                        [ 82%]
orchestration\tests\test_container_env.py ........                       [ 82%]
orchestration\tests\test_container_events.py .........................   [ 82%]
orchestration\tests\test_container_faults.py ......                      [ 83%]
orchestration\tests\test_container_lines.py ......                       [ 83%]
orchestration\tests\test_container_platform.py .......                   [ 83%]
orchestration\tests\test_container_queries.py ...............            [ 83%]
orchestration\tests\test_container_reader.py ...............             [ 83%]
orchestration\tests\test_container_sensor.py ......                      [ 83%]
orchestration\tests\test_container_telling.py .......                    [ 84%]
orchestration\tests\test_container_vocabulary.py ....                    [ 84%]
orchestration\tests\test_daily_brief_boundaries.py .......               [ 84%]
orchestration\tests\test_daily_brief_dispatch.py ....                    [ 84%]
orchestration\tests\test_daily_brief_facts.py ........                   [ 84%]
orchestration\tests\test_daily_brief_facts_edges.py .......              [ 84%]
orchestration\tests\test_daily_brief_filled_quantity.py .                [ 84%]
orchestration\tests\test_daily_brief_text.py .........                   [ 84%]
orchestration\tests\test_deploy_record.py .....                          [ 84%]
orchestration\tests\test_deploy_record_verification.py .......           [ 85%]
orchestration\tests\test_dispatcher_capability.py .                      [ 85%]
orchestration\tests\test_dispatcher_unit.py .......                      [ 85%]
orchestration\tests\test_drop_sweep_cascade.py ..                        [ 85%]
orchestration\tests\test_forecaster_settlement_stage.py .                [ 85%]
orchestration\tests\test_forecaster_stage.py .....                       [ 85%]
orchestration\tests\test_fresh_book_before_decision.py ....              [ 85%]
orchestration\tests\test_graph_pull_e2e.py .....                         [ 85%]
orchestration\tests\test_graph_vocabulary_e2e.py .....                   [ 85%]
orchestration\tests\test_history_window.py ...                           [ 85%]
orchestration\tests\test_llm_brief_candidates.py .....                   [ 85%]
orchestration\tests\test_llm_brief_switches.py .......                   [ 85%]
orchestration\tests\test_master_serve.py .                               [ 85%]
orchestration\tests\test_observatory.py ............                     [ 86%]
orchestration\tests\test_p4_celery_parity.py .                           [ 86%]
orchestration\tests\test_p4_daily_loop.py ..                             [ 86%]
orchestration\tests\test_p4_scheduler.py ...                             [ 86%]
orchestration\tests\test_pm_rejection_display.py ....                    [ 86%]
orchestration\tests\test_pm_rejection_rendering.py ...                   [ 86%]
orchestration\tests\test_position_sync_display_branches.py .             [ 86%]
orchestration\tests\test_realized_pnl_graph_pull.py .                    [ 86%]
orchestration\tests\test_regime_vix_graph_pull.py .                      [ 86%]
orchestration\tests\test_reporter_snapshot_readers.py ..                 [ 86%]
orchestration\tests\test_resume.py ............                          [ 86%]
orchestration\tests\test_resume_postgres_semantics.py .                  [ 86%]
orchestration\tests\test_resume_stage_contracts.py ..                    [ 86%]
orchestration\tests\test_scheduled_dispatch.py ......                    [ 86%]
orchestration\tests\test_scheduled_dispatch_degraded_notices.py ....     [ 87%]
orchestration\tests\test_scheduled_dispatch_degraded_readiness.py ...... [ 87%]
                                                                         [ 87%]
orchestration\tests\test_scheduled_dispatch_human_edges.py ...           [ 87%]
orchestration\tests\test_scheduled_dispatch_notices.py .......           [ 87%]
orchestration\tests\test_scheduled_dispatch_once.py ...............      [ 87%]
orchestration\tests\test_scheduled_dispatch_polling.py .........         [ 87%]
orchestration\tests\test_scheduled_dispatch_readiness.py .........       [ 87%]
orchestration\tests\test_shadow_book_derivation.py ..........            [ 88%]
orchestration\tests\test_shadow_book_disposition.py .....                [ 88%]
orchestration\tests\test_shadow_book_hit_direction.py .                  [ 88%]
orchestration\tests\test_shadow_book_scorecard.py ........               [ 88%]
orchestration\tests\test_start.py .....                                  [ 88%]
orchestration\tests\test_start_as_of.py .                                [ 88%]
orchestration\tests\test_steps.py ...                                    [ 88%]
orchestration\tests\test_telegram_brief.py ...                           [ 88%]
orchestration\tests\test_telegram_client_edges.py ....                   [ 88%]
orchestration\tests\test_telegram_vault_seed.py .                        [ 88%]
orchestration\tests\test_trace_deliberation.py ....                      [ 88%]
orchestration\tests\test_trace_deliberation_counts.py ..                 [ 88%]
orchestration\tests\test_trace_deliberation_edges.py .......             [ 88%]
orchestration\tests\test_trace_format.py .                               [ 89%]
orchestration\tests\test_trace_run_cli.py ...                            [ 89%]
orchestration\tests\test_trading_acceptance.py .........                 [ 89%]
orchestration\tests\test_trading_acceptance_deliberation.py .....        [ 89%]
orchestration\tests\test_trading_acceptance_outcomes.py ......           [ 89%]
orchestration\tests\test_trading_deliberation_not_required.py .......... [ 89%]
                                                                         [ 89%]
orchestration\tests\test_trading_deliberation_posture.py ......          [ 89%]
orchestration\tests\test_trading_deliberation_unvetoed.py ............   [ 89%]
orchestration\tests\test_trading_deliberation_view.py ...                [ 90%]
orchestration\tests\test_trading_fill_outcomes.py .......                [ 90%]
orchestration\tests\test_trading_observatory.py .....                    [ 90%]
orchestration\tests\test_trading_vault_llm_requests.py .........         [ 90%]
orchestration\tests\test_trading_vault_postgres.py .                     [ 90%]
orchestration\tests\test_trading_vault_probe_feed.py .                   [ 90%]
orchestration\tests\test_trading_vault_probes.py .............           [ 90%]
orchestration\tests\test_unified_conservation.py ..                      [ 90%]
orchestration\tests\test_unified_decision_run.py ....                    [ 90%]
orchestration\tests\test_veto_stage.py ........                          [ 90%]
surfaces\tests\test_chat_cutoff.py ......                                [ 91%]
surfaces\tests\test_chat_failed_request.py .....................         [ 91%]
surfaces\tests\test_chat_model_mismatch.py ...                           [ 91%]
surfaces\tests\test_chat_quick_asks.py ....                              [ 91%]
surfaces\tests\test_cli.py .......                                       [ 91%]
surfaces\tests\test_cli_incidents_explain.py ...                         [ 91%]
surfaces\tests\test_cli_narrative_approve.py .....                       [ 91%]
surfaces\tests\test_context.py .....                                     [ 92%]
surfaces\tests\test_dashboard_app.py ...........                         [ 92%]
surfaces\tests\test_dashboard_azure_parsers.py .....                     [ 92%]
surfaces\tests\test_dashboard_azure_rest.py ....                         [ 92%]
surfaces\tests\test_dashboard_azure_retry.py ..                          [ 92%]
surfaces\tests\test_dashboard_azure_template.py ..                       [ 92%]
surfaces\tests\test_dashboard_bundle.py ..                               [ 92%]
surfaces\tests\test_dashboard_bundle_azure.py .....                      [ 92%]
surfaces\tests\test_dashboard_chat.py ......                             [ 92%]
surfaces\tests\test_dashboard_chat_edges.py ....                         [ 92%]
surfaces\tests\test_dashboard_chat_provider.py ...                       [ 92%]
surfaces\tests\test_dashboard_costs.py .......                           [ 92%]
surfaces\tests\test_dashboard_currency.py .....                          [ 93%]
surfaces\tests\test_dashboard_currency_rebuilt.py .....                  [ 93%]
surfaces\tests\test_dashboard_degraded_readiness.py .                    [ 93%]
surfaces\tests\test_dashboard_flag_ack.py ..                             [ 93%]
surfaces\tests\test_dashboard_flags_resolution.py .                      [ 93%]
surfaces\tests\test_dashboard_fleet.py .....                             [ 93%]
surfaces\tests\test_dashboard_hold_answer_route_edges.py ..              [ 93%]
surfaces\tests\test_dashboard_hold_answers.py ...                        [ 93%]
surfaces\tests\test_dashboard_jargon.py ..                               [ 93%]
surfaces\tests\test_dashboard_llm_cache_costs.py ......                  [ 93%]
surfaces\tests\test_dashboard_llm_costs.py .                             [ 93%]
surfaces\tests\test_dashboard_local_time.py ...                          [ 93%]
surfaces\tests\test_dashboard_next_check.py ....                         [ 93%]
surfaces\tests\test_dashboard_projections.py .........                   [ 93%]
surfaces\tests\test_dashboard_read_cache.py .....                        [ 94%]
surfaces\tests\test_dashboard_readiness.py .........                     [ 94%]
surfaces\tests\test_dashboard_reholds.py ...                             [ 94%]
surfaces\tests\test_dashboard_resume.py .                                [ 94%]
surfaces\tests\test_dashboard_run_result.py ...                          [ 94%]
surfaces\tests\test_dashboard_schedule.py .......                        [ 94%]
surfaces\tests\test_dashboard_state.py .....                             [ 94%]
surfaces\tests\test_dashboard_template_currency.py ...                   [ 94%]
surfaces\tests\test_dashboard_tri_state.py .                             [ 94%]
surfaces\tests\test_dashboard_verdict.py ................                [ 94%]
surfaces\tests\test_dashboard_verdict_unproven.py ..                     [ 94%]
surfaces\tests\test_dashboard_vitals.py ....                             [ 95%]
surfaces\tests\test_dashboard_window_days.py ........................... [ 95%]
..                                                                       [ 95%]
surfaces\tests\test_datasets_surface.py ....                             [ 95%]
surfaces\tests\test_entry_imports.py ....                                [ 95%]
surfaces\tests\test_entrypoint.py .                                      [ 95%]
surfaces\tests\test_faults.py ....                                       [ 95%]
surfaces\tests\test_github_build_tag_ancestry.py ...                     [ 95%]
surfaces\tests\test_github_build_tag_attempts.py ...................     [ 96%]
surfaces\tests\test_github_build_tag_guards.py ................          [ 96%]
surfaces\tests\test_github_builds.py ...........                         [ 96%]
surfaces\tests\test_github_builds_env.py ..                              [ 96%]
surfaces\tests\test_github_tree_diff.py .......                          [ 96%]
surfaces\tests\test_graph_pull_runs.py .....                             [ 97%]
surfaces\tests\test_health_incidents.py .                                [ 97%]
surfaces\tests\test_image_paths.py ...................                   [ 97%]
surfaces\tests\test_lifecycle_flags.py ......                            [ 97%]
surfaces\tests\test_mcp_server.py ......                                 [ 97%]
surfaces\tests\test_metrics_server.py ..                                 [ 97%]
surfaces\tests\test_p6_exit.py .                                         [ 97%]
surfaces\tests\test_p7_exit.py ....                                      [ 97%]
surfaces\tests\test_p8_exit.py ....                                      [ 97%]
surfaces\tests\test_p9_exit.py ..                                        [ 97%]
surfaces\tests\test_performance_chat.py ......                           [ 98%]
surfaces\tests\test_performance_scoreboard.py ................           [ 98%]
surfaces\tests\test_performance_text.py ....                             [ 98%]
surfaces\tests\test_predictors_surface.py ....                           [ 98%]
surfaces\tests\test_proposals_surface.py ..                              [ 98%]
surfaces\tests\test_queries.py ...                                       [ 98%]
surfaces\tests\test_registry_surface.py ....                             [ 98%]
surfaces\tests\test_scorecard_attribution.py .....                       [ 98%]
surfaces\tests\test_scorecard_chat.py ......                             [ 98%]
surfaces\tests\test_scorecard_edges.py .......                           [ 98%]
surfaces\tests\test_scorecard_g1_g3.py ..............                    [ 99%]
surfaces\tests\test_scorecard_reason.py ......                           [ 99%]
surfaces\tests\test_scorecard_settling.py ....                           [ 99%]
surfaces\tests\test_scorecard_tile.py ..........                         [ 99%]
surfaces\tests\test_scorecard_verdicts.py .......                        [ 99%]
surfaces\tests\test_stage_promote_cli.py ...                             [ 99%]
surfaces\tests\test_stage_surface.py ..                                  [ 99%]
surfaces\tests\test_status_fleet_check.py .......                        [100%]

============================== warnings summary ===============================
tests/test_barrier_testbed.py: 2170 warnings
  C:\Users\yury_\Downloads\project\ta-s285\tests\test_barrier_testbed.py:22: DeprecationWarning: The 'generic' unit for NumPy timedelta is deprecated, and will raise an error in the future. This includes implicit conversion of bare integers (e.g. `+ 1`). Please use a specific unit instead.
    (str(start + i), close, close * 1.01, close * 0.99, close) for i in range(n)

tests/test_barrier_testbed.py: 300 warnings
  C:\Users\yury_\Downloads\project\ta-s285\tests\test_barrier_testbed.py:112: DeprecationWarning: The 'generic' unit for NumPy timedelta is deprecated, and will raise an error in the future. This includes implicit conversion of bare integers (e.g. `+ 1`). Please use a specific unit instead.
    rows = [(str(start + i), c, c * 1.01, c * 0.999, c) for i, c in enumerate(closes)]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.2-final-0 _______________

Name                                                            Stmts   Miss Branch BrPart    Cover   Missing
-------------------------------------------------------------------------------------------------------------
agents\__init__.py                                                  0      0      0      0  100.00%
agents\analyst\__init__.py                                          6      0      0      0  100.00%
agents\analyst\agent.py                                            46      0      4      0  100.00%
agents\analyst\domain\__init__.py                                   0      0      0      0  100.00%
agents\analyst\domain\alpha_features.py                            54      0      2      0  100.00%
agents\analyst\domain\alpha_pillar.py                              17      0      2      0  100.00%
agents\analyst\domain\analyze.py                                   53      0     20      0  100.00%
agents\analyst\domain\fundamental_rules.py                         32      0     20      0  100.00%
agents\analyst\domain\indicators.py                                66      0     18      0  100.00%
agents\analyst\domain\indicators_event.py                          19      0     10      0  100.00%
agents\analyst\domain\indicators_kernel.py                         32      0     14      0  100.00%
agents\analyst\domain\indicators_pattern.py                        76      0     36      0  100.00%
agents\analyst\domain\indicators_range.py                          48      0     18      0  100.00%
agents\analyst\domain\recommend.py                                 49      0     14      0  100.00%
agents\analyst\domain\recommend_summary.py                         13      0      4      0  100.00%
agents\analyst\domain\recommend_text.py                             9      0      4      0  100.00%
agents\analyst\domain\relative_strength.py                         23      0     10      0  100.00%
agents\analyst\domain\score_arithmetic.py                           5      0      0      0  100.00%
agents\analyst\domain\scoring.py                                   70      0     18      0  100.00%
agents\analyst\domain\sentiment_reading.py                         20      0      2      0  100.00%
agents\analyst\domain\sentiment_rules.py                           38      0      6      0  100.00%
agents\analyst\domain\sentiment_subject.py                         36      0      8      0  100.00%
agents\analyst\domain\sentiment_weights.py                          8      0      4      0  100.00%
agents\analyst\domain\signal_selection.py                          29      0      2      0  100.00%
agents\analyst\domain\stop_target.py                               68      0     20      0  100.00%
agents\analyst\domain\stop_target_outcome.py                       49      0     12      0  100.00%
agents\analyst\domain\target_excursion_metrics.py                  12      0      2      0  100.00%
agents\analyst\domain\technical_rules.py                           96      0     46      0  100.00%
agents\analyst\domain\technical_rules_event.py                     35      0     14      0  100.00%
agents\analyst\domain\technical_rules_pattern.py                   36      0     14      0  100.00%
agents\analyst\domain\technical_rules_range.py                     56      0     28      0  100.00%
agents\analyst\entrypoint.py                                        9      0      0      0  100.00%
agents\analyst\held_universe.py                                    11      0      2      0  100.00%
agents\analyst\history_requirements.py                             25      0      0      0  100.00%
agents\analyst\outcome_backfill.py                                 50      0     20      0  100.00%
agents\analyst\poll.py                                             69      0     18      0  100.00%
agents\analyst\provider_client.py                                  25      0      4      0  100.00%
agents\analyst\recommendation_props.py                             10      0      2      0  100.00%
agents\analyst\result.py                                           29      0     12      0  100.00%
agents\analyst\run.py                                              44      0      8      0  100.00%
agents\analyst\settings.py                                         35      0      8      0  100.00%
agents\analyst\settings_indicators.py                              24      0      0      0  100.00%
agents\analyst\settings_stop_target.py                             12      0      0      0  100.00%
agents\analyst\store.py                                            30      0     10      0  100.00%
agents\curator\__init__.py                                          2      0      0      0  100.00%
agents\curator\agent.py                                            73      0     10      0  100.00%
agents\curator\agent_support.py                                     9      0      0      0  100.00%
agents\curator\dataset_store.py                                     9      0      0      0  100.00%
agents\curator\domain\assembly.py                                  32      0      6      0  100.00%
agents\curator\domain\filter_quality.py                            45      0     12      0  100.00%
agents\curator\domain\manifest.py                                  24      0      0      0  100.00%
agents\curator\domain\registry.py                                  24      0      8      0  100.00%
agents\curator\domain\split.py                                     16      0      2      0  100.00%
agents\curator\domain\training.py                                  46      0     14      0  100.00%
agents\curator\entrypoint.py                                       11      0      0      0  100.00%
agents\curator\predictor.py                                        19      0      4      0  100.00%
agents\curator\promotion.py                                        39      0     10      0  100.00%
agents\curator\settings.py                                         12      0      0      0  100.00%
agents\curator\store.py                                            26      0      8      0  100.00%
agents\deliberator\__init__.py                                      3      0      0      0  100.00%
agents\deliberator\agent.py                                        31      0      2      0  100.00%
agents\deliberator\context.py                                      61      0     16      0  100.00%
agents\deliberator\context_arithmetic.py                           63      0     18      0  100.00%
agents\deliberator\context_market.py                               28      0     12      0  100.00%
agents\deliberator\context_pm.py                                   35      0     10      0  100.00%
agents\deliberator\context_stop.py                                 23      0      8      0  100.00%
agents\deliberator\context_values.py                               22      0      2      0  100.00%
agents\deliberator\entrypoint.py                                   37      0      2      0  100.00%
agents\deliberator\guided_turn.py                                  15      0      0      0  100.00%
agents\deliberator\model_chain.py                                  52      0     14      0  100.00%
agents\deliberator\peer_client.py                                  26      0      2      0  100.00%
agents\deliberator\poll.py                                         54      0     12      0  100.00%
agents\deliberator\prompt_recipe.py                                 7      0      0      0  100.00%
agents\deliberator\review_batch.py                                 49      0     10      0  100.00%
agents\deliberator\review_record.py                                51      0     14      0  100.00%
agents\deliberator\servicebus_peer_client.py                       56      0      6      0  100.00%
agents\deliberator\servicebus_reply_inbox.py                       72      0     16      0  100.00%
agents\deliberator\settings.py                                     42      0      8      0  100.00%
agents\deliberator\store.py                                        24      0      6      0  100.00%
agents\deliberator\turn_ledger.py                                  43      0      4      0  100.00%
agents\execution\__init__.py                                        2      0      0      0  100.00%
agents\execution\agent.py                                          44      0      0      0  100.00%
agents\execution\alpaca.py                                         56      0      4      0  100.00%
agents\execution\alpaca_account.py                                 18      0      4      0  100.00%
agents\execution\alpaca_order_reads.py                             64      0     20      0  100.00%
agents\execution\alpaca_orders.py                                  54      0     12      0  100.00%
agents\execution\alpaca_positions.py                               20      0      4      0  100.00%
agents\execution\alpaca_replace.py                                 30      0      4      0  100.00%
agents\execution\broker.py                                         60      0      2      0  100.00%
agents\execution\broker_factory.py                                  8      0      2      0  100.00%
agents\execution\broker_status_refresh.py                          36      0      8      0  100.00%
agents\execution\broker_stop_actions.py                            41      0      2      0  100.00%
agents\execution\broker_stop_realign.py                            80      0     16      0  100.00%
agents\execution\broker_stop_thresholds.py                         61      0     12      0  100.00%
agents\execution\broker_stop_types.py                              25      0      0      0  100.00%
agents\execution\broker_stop_writes.py                             29      0      8      0  100.00%
agents\execution\broker_stops.py                                   78      0     38      0  100.00%
agents\execution\deliberation_faults.py                            14      0      0      0  100.00%
agents\execution\deliberation_gate.py                              65      0     24      0  100.00%
agents\execution\deliberation_posture.py                           16      0      4      0  100.00%
agents\execution\divergence_episodes.py                            22      0      6      0  100.00%
agents\execution\domain\__init__.py                                 0      0      0      0  100.00%
agents\execution\domain\orders.py                                  34      0      6      0  100.00%
agents\execution\domain\reconcile.py                               20      0      8      0  100.00%
agents\execution\domain\result.py                                   9      0      0      0  100.00%
agents\execution\domain\stage_gate.py                              29      0      8      0  100.00%
agents\execution\domain\stage_metrics.py                           17      0      4      0  100.00%
agents\execution\domain\submit.py                                  18      0      2      0  100.00%
agents\execution\drop_sweep.py                                     84      0     26      0  100.00%
agents\execution\drop_sweep_ack.py                                 18      0      2      0  100.00%
agents\execution\drop_sweep_reads.py                               18      0      0      0  100.00%
agents\execution\drop_sweep_records.py                             52      0     18      0  100.00%
agents\execution\entrypoint.py                                     10      0      0      0  100.00%
agents\execution\exit_stops.py                                     32      0     12      0  100.00%
agents\execution\fill_attempts.py                                  65      0     16      0  100.00%
agents\execution\filled_entry_stops.py                             98      0     40      0  100.00%
agents\execution\live_gate.py                                      10      0      0      0  100.00%
agents\execution\order_status_store.py                             14      0      0      0  100.00%
agents\execution\order_tolerance.py                                69      0      6      0  100.00%
agents\execution\paper_broker.py                                   59      0     16      0  100.00%
agents\execution\paper_broker_math.py                              51      0     16      0  100.00%
agents\execution\paper_broker_orders.py                            28      0      8      0  100.00%
agents\execution\partial_fill.py                                   10      0      2      0  100.00%
agents\execution\pm_execution.py                                   35      0      6      0  100.00%
agents\execution\poll.py                                           42      0      6      0  100.00%
agents\execution\realized_pnl.py                                   47      0     14      0  100.00%
agents\execution\reconciliation.py                                 46      0      6      0  100.00%
agents\execution\reconciliation_flags.py                           73      0     30      0  100.00%
agents\execution\reconciliation_store.py                           70      0     24      0  100.00%
agents\execution\run.py                                            52      0     14      0  100.00%
agents\execution\run_start_orders.py                               18      0      2      0  100.00%
agents\execution\settings.py                                       32      0      2      0  100.00%
agents\execution\snapshot_account.py                                9      0      4      0  100.00%
agents\execution\stage_flow.py                                     33      0      8      0  100.00%
agents\execution\store.py                                          61      0     20      0  100.00%
agents\execution\tolerance_store_props.py                          33      0      8      0  100.00%
agents\forecaster\__init__.py                                       2      0      0      0  100.00%
agents\forecaster\agent.py                                         58      0      0      0  100.00%
agents\forecaster\barrier_fit.py                                   24      0      2      0  100.00%
agents\forecaster\barrier_forecast.py                              43      0      6      0  100.00%
agents\forecaster\barrier_refusal.py                               28      0      8      0  100.00%
agents\forecaster\barrier_scorecard.py                             17      0      0      0  100.00%
agents\forecaster\barrier_store.py                                 32      0      2      0  100.00%
agents\forecaster\comparison.py                                    32      0     10      0  100.00%
agents\forecaster\domain\__init__.py                                0      0      0      0  100.00%
agents\forecaster\domain\barrier_garch.py                          78      0      8      0  100.00%
agents\forecaster\domain\barrier_settlement.py                     54      0     12      0  100.00%
agents\forecaster\domain\barrier_skill.py                          43      0      8      0  100.00%
agents\forecaster\domain\evaluation.py                             41      0     10      0  100.00%
agents\forecaster\domain\factor_signal.py                         117      0     40      0  100.00%
agents\forecaster\domain\features.py                               38      0      2      0  100.00%
agents\forecaster\domain\retrain_policy.py                         42      0     10      0  100.00%
agents\forecaster\domain\return_labels.py                          23      0      6      0  100.00%
agents\forecaster\domain\return_scorecard.py                       35      0     10      0  100.00%
agents\forecaster\domain\scorecard.py                              40      0      6      0  100.00%
agents\forecaster\domain\sentiment.py                              20      0      6      0  100.00%
agents\forecaster\domain\statistics.py                             55      0     16      0  100.00%
agents\forecaster\entrypoint.py                                    25      0      0      0  100.00%
agents\forecaster\factor_prediction.py                             19      0      4      0  100.00%
agents\forecaster\factor_signal.py                                 30      0      2      0  100.00%
agents\forecaster\finbert.py                                       14      0      0      0  100.00%
agents\forecaster\lightgbm_model.py                                11      0      0      0  100.00%
agents\forecaster\model.py                                         11      0      0      0  100.00%
agents\forecaster\model_trainer.py                                 19      0      2      0  100.00%
agents\forecaster\poll.py                                          42      0     12      0  100.00%
agents\forecaster\price_signal.py                                  26      0      4      0  100.00%
agents\forecaster\provider_client.py                               24      0      4      0  100.00%
agents\forecaster\return_model.py                                  10      0      0      0  100.00%
agents\forecaster\scorecards.py                                    27      0      2      0  100.00%
agents\forecaster\settings.py                                      30      0      0      0  100.00%
agents\forecaster\settlement_pass.py                               51      0      8      0  100.00%
agents\forecaster\settlement_store.py                              22      0      0      0  100.00%
agents\forecaster\settling_bars.py                                 19      0      4      0  100.00%
agents\forecaster\store.py                                         21      0      4      0  100.00%
agents\forecaster\work.py                                          15      0      2      0  100.00%
agents\master\__init__.py                                           0      0      0      0  100.00%
agents\master\activation_credentials.py                            12      0      2      0  100.00%
agents\master\activation_remediation.py                            25      0      8      0  100.00%
agents\master\activation_replay.py                                 56      0      8      0  100.00%
agents\master\agent.py                                             65      0      6      0  100.00%
agents\master\credential_check.py                                  33      0      2      0  100.00%
agents\master\credential_outcomes.py                               44      0     12      0  100.00%
agents\master\credential_probe_candidate.py                        34      0     16      0  100.00%
agents\master\credential_probe_support.py                          66      0     26      0  100.00%
agents\master\credential_probe_transports.py                        5      0      0      0  100.00%
agents\master\credential_probes.py                                 89      0     30      0  100.00%
agents\master\credential_report.py                                 36      0      4      0  100.00%
agents\master\credential_result.py                                 19      0      2      0  100.00%
agents\master\credential_selection.py                              18      0     12      0  100.00%
agents\master\credential_test.py                                   25      0      6      0  100.00%
agents\master\draining_server.py                                   29      0      0      0  100.00%
agents\master\entrypoint.py                                        36      0      6      0  100.00%
agents\master\fleet_preflight.py                                   48      0     12      0  100.00%
agents\master\fleet_preflight_loop.py                              20      0      4      0  100.00%
agents\master\grants.py                                            17      0      6      0  100.00%
agents\master\http_server.py                                       84      0     10      0  100.00%
agents\master\identity.py                                           9      0      0      0  100.00%
agents\master\key_vault.py                                         41      0      6      0  100.00%
agents\master\model_candidates.py                                  64      0     18      0  100.00%
agents\master\model_choice.py                                      43      0     18      0  100.00%
agents\master\model_expansion.py                                   29      0     12      0  100.00%
agents\master\pack_loading.py                                      20      0      4      0  100.00%
agents\master\remediation.py                                       91      0     24      0  100.00%
agents\master\remediation_execution.py                             60      0     12      0  100.00%
agents\master\remediation_gate.py                                  76      0     20      0  100.00%
agents\master\remediation_posture.py                                8      0      2      0  100.00%
agents\master\remediation_records.py                                9      0      0      0  100.00%
agents\master\secret_map.py                                        25      0     10      0  100.00%
agents\master\settings.py                                          23      0      0      0  100.00%
agents\master\stopping.py                                          20      0      6      0  100.00%
agents\master\store.py                                             40      0      6      0  100.00%
agents\master\vault_seed.py                                        76      0     20      0  100.00%
agents\monitor\__init__.py                                          2      0      0      0  100.00%
agents\monitor\agent.py                                            38      0      4      0  100.00%
agents\monitor\decide.py                                           19      0      4      0  100.00%
agents\monitor\domain\__init__.py                                   0      0      0      0  100.00%
agents\monitor\domain\exit_rules.py                                15      0      2      0  100.00%
agents\monitor\domain\positions.py                                 33      0      2      0  100.00%
agents\monitor\entrypoint.py                                        9      0      0      0  100.00%
agents\monitor\poll.py                                             55      0      8      0  100.00%
agents\monitor\position_book.py                                     5      0      0      0  100.00%
agents\monitor\position_sync.py                                    44      0     14      0  100.00%
agents\monitor\provider_client.py                                  33      0     12      0  100.00%
agents\monitor\pubsub.py                                           13      0      0      0  100.00%
agents\monitor\reconcile.py                                        71      0     38      0  100.00%
agents\monitor\result.py                                            4      0      0      0  100.00%
agents\monitor\run.py                                              41      0      8      0  100.00%
agents\monitor\settings.py                                          9      0      0      0  100.00%
agents\monitor\store.py                                            43      0     10      0  100.00%
agents\operator\__init__.py                                         2      0      0      0  100.00%
agents\operator\agent.py                                           58      0     10      0  100.00%
agents\operator\domain\__init__.py                                  0      0      0      0  100.00%
agents\operator\domain\evidence.py                                 68      0     26      0  100.00%
agents\operator\domain\grammar.py                                  30      0      6      0  100.00%
agents\operator\domain\prompts.py                                  15      0      0      0  100.00%
agents\operator\domain\result.py                                   63      0     14      0  100.00%
agents\operator\entrypoint.py                                      11      0      0      0  100.00%
agents\operator\ledger.py                                          28      0      0      0  100.00%
agents\operator\prompt_recipe.py                                    5      0      0      0  100.00%
agents\operator\settings.py                                        19      0      0      0  100.00%
agents\operator\store.py                                           21      0      4      0  100.00%
agents\portfolio_manager\__init__.py                                2      0      0      0  100.00%
agents\portfolio_manager\agent.py                                  50      0      6      0  100.00%
agents\portfolio_manager\domain\__init__.py                         0      0      0      0  100.00%
agents\portfolio_manager\domain\concentration.py                    3      0      0      0  100.00%
agents\portfolio_manager\domain\correlation.py                     55      0      8      0  100.00%
agents\portfolio_manager\domain\correlation_census.py              57      0      4      0  100.00%
agents\portfolio_manager\domain\correlation_census_builder.py      26      0     10      0  100.00%
agents\portfolio_manager\domain\correlation_math.py                38      0     14      0  100.00%
agents\portfolio_manager\domain\correlation_ramp.py                15      0      8      0  100.00%
agents\portfolio_manager\domain\deployment_floor.py                24      0      6      0  100.00%
agents\portfolio_manager\domain\exits.py                           12      0      0      0  100.00%
agents\portfolio_manager\domain\gate_report.py                     29      0      6      0  100.00%
agents\portfolio_manager\domain\issuer.py                           5      0      0      0  100.00%
agents\portfolio_manager\domain\order_decision.py                  38      0     10      0  100.00%
agents\portfolio_manager\domain\position_gates.py                  45      0     18      0  100.00%
agents\portfolio_manager\domain\rejection_reasons.py                7      0      0      0  100.00%
agents\portfolio_manager\domain\reward_risk_detail.py              57      0     20      0  100.00%
agents\portfolio_manager\domain\risk.py                            64      0     24      0  100.00%
agents\portfolio_manager\domain\sector_book.py                     93      0     22      0  100.00%
agents\portfolio_manager\domain\sector_gate_outcomes.py            25      0      6      0  100.00%
agents\portfolio_manager\domain\sizing.py                           6      0      2      0  100.00%
agents\portfolio_manager\domain\volatility.py                       8      0      4      0  100.00%
agents\portfolio_manager\entrypoint.py                             10      0      0      0  100.00%
agents\portfolio_manager\graph_portfolio.py                        61      0     22      0  100.00%
agents\portfolio_manager\issuer_map.py                             30      0     10      0  100.00%
agents\portfolio_manager\market_context.py                          8      0      2      0  100.00%
agents\portfolio_manager\poll.py                                   39      0      4      0  100.00%
agents\portfolio_manager\portfolio.py                              33      0      2      0  100.00%
agents\portfolio_manager\provider_client.py                        32      0      8      0  100.00%
agents\portfolio_manager\pubsub.py                                 11      0      0      0  100.00%
agents\portfolio_manager\result.py                                 22      0      6      0  100.00%
agents\portfolio_manager\run.py                                    39      0     14      0  100.00%
agents\portfolio_manager\run_snapshot.py                           29      0     12      0  100.00%
agents\portfolio_manager\settings.py                               20      0      0      0  100.00%
agents\portfolio_manager\store.py                                  34      0     10      0  100.00%
agents\provider\__init__.py                                         7      0      0      0  100.00%
agents\provider\agent.py                                           56      0      4      0  100.00%
agents\provider\alpaca_data.py                                     78      0     24      0  100.00%
agents\provider\alpaca_request.py                                  20      0      4      0  100.00%
agents\provider\av_sentiment.py                                    56      0     14      0  100.00%
agents\provider\barrier_history.py                                 62      0     14      0  100.00%
agents\provider\barrier_window.py                                  21      0      4      0  100.00%
agents\provider\composite.py                                       34      0      2      0  100.00%
agents\provider\domain\__init__.py                                  0      0      0      0  100.00%
agents\provider\domain\integrity.py                                56      0     16      0  100.00%
agents\provider\domain\market_calendar.py                          15      0      4      0  100.00%
agents\provider\domain\regime.py                                   14      0     10      0  100.00%
agents\provider\entrypoint.py                                      13      0      0      0  100.00%
agents\provider\finnhub_http.py                                    11      0      0      0  100.00%
agents\provider\finnhub_resilience.py                              54      0     10      0  100.00%
agents\provider\fmp.py                                             55      0     14      0  100.00%
agents\provider\fmp_vix.py                                         75      0     24      0  100.00%
agents\provider\fundamentals.py                                    71      0     18      0  100.00%
agents\provider\fundamentals_parse.py                              68      0     30      0  100.00%
agents\provider\ingest.py                                          51      0      8      0  100.00%
agents\provider\ingest_chunked.py                                  43      0      8      0  100.00%
agents\provider\market_fields.py                                   53      0     12      0  100.00%
agents\provider\poll.py                                            63      0     12      0  100.00%
agents\provider\regime_arithmetic.py                                5      0      0      0  100.00%
agents\provider\sector_cache.py                                    15      0     10      0  100.00%
agents\provider\settings.py                                        15      0      0      0  100.00%
agents\provider\settings_feeds.py                                  32      0      0      0  100.00%
agents\provider\sources.py                                         73      0     16      0  100.00%
agents\provider\stooq.py                                           36      0      6      0  100.00%
agents\provider\store.py                                           21      0      2      0  100.00%
agents\provider\tiingo.py                                          54      0     14      0  100.00%
agents\reporter\__init__.py                                         8      0      2      0  100.00%
agents\reporter\agent.py                                           42      0      4      0  100.00%
agents\reporter\benchmark_input.py                                 50      0     22      0  100.00%
agents\reporter\book_inputs.py                                     18      0      2      0  100.00%
agents\reporter\domain\__init__.py                                  0      0      0      0  100.00%
agents\reporter\domain\book_window.py                              25      0      2      0  100.00%
agents\reporter\domain\lineage.py                                  73      0      8      0  100.00%
agents\reporter\domain\metrics.py                                  29      0      6      0  100.00%
agents\reporter\domain\narrative.py                                44      0     12      0  100.00%
agents\reporter\domain\performance.py                              59      0     14      0  100.00%
agents\reporter\domain\trade_outcomes.py                           21      0     10      0  100.00%
agents\reporter\entrypoint.py                                       6      0      0      0  100.00%
agents\reporter\narrative_result.py                                14      0      0      0  100.00%
agents\reporter\performance_inputs.py                              73      0     22      0  100.00%
agents\reporter\poll.py                                            15      0      0      0  100.00%
agents\reporter\result.py                                          48      0      6      0  100.00%
agents\reporter\settings.py                                         9      0      0      0  100.00%
agents\reporter\snapshot_result.py                                 16      0      2      0  100.00%
agents\reporter\store.py                                           17      0      4      0  100.00%
agents\researcher\__init__.py                                       2      0      0      0  100.00%
agents\researcher\agent.py                                         58      0     10      0  100.00%
agents\researcher\domain\backtest.py                              103      0     32      0  100.00%
agents\researcher\domain\backtest_types.py                         43      0      2      0  100.00%
agents\researcher\domain\evidence.py                               32      0      8      0  100.00%
agents\researcher\domain\factor_proposal.py                         6      0      0      0  100.00%
agents\researcher\domain\factors.py                                61      0     16      0  100.00%
agents\researcher\domain\factors_impl.py                           47      0     14      0  100.00%
agents\researcher\domain\proposal.py                               29      0     10      0  100.00%
agents\researcher\entrypoint.py                                    11      0      0      0  100.00%
agents\researcher\settings.py                                      16      0      0      0  100.00%
agents\researcher\store.py                                          8      0      2      0  100.00%
agents\scanner\__init__.py                                          7      0      0      0  100.00%
agents\scanner\agent.py                                            60      0      4      0  100.00%
agents\scanner\domain\__init__.py                                   0      0      0      0  100.00%
agents\scanner\domain\beta.py                                      24      0      6      0  100.00%
agents\scanner\domain\filter_attestation.py                        31      0     18      0  100.00%
agents\scanner\domain\filters.py                                   58      0     16      0  100.00%
agents\scanner\domain\ranking.py                                    6      0      0      0  100.00%
agents\scanner\entrypoint.py                                        7      0      0      0  100.00%
agents\scanner\poll.py                                             24      0      0      0  100.00%
agents\scanner\provider_client.py                                  20      0      2      0  100.00%
agents\scanner\results.py                                           7      0      2      0  100.00%
agents\scanner\settings.py                                         15      0      0      0  100.00%
agents\scanner\store.py                                            20      0      6      0  100.00%
agents\scanner\universe.py                                         25      0      2      0  100.00%
agents\supervisor\__init__.py                                       2      0      0      0  100.00%
agents\supervisor\agent.py                                         67      0     12      0  100.00%
agents\supervisor\domain\__init__.py                                0      0      0      0  100.00%
agents\supervisor\domain\gate.py                                   69      0     30      0  100.00%
agents\supervisor\domain\hard_no.py                                11      0      6      0  100.00%
agents\supervisor\domain\health.py                                 34      0      2      0  100.00%
agents\supervisor\domain\matrix.py                                 17      0      2      0  100.00%
agents\supervisor\entrypoint.py                                    11      0      0      0  100.00%
agents\supervisor\fault_resolution.py                              13      0      2      0  100.00%
agents\supervisor\result.py                                        16      0      2      0  100.00%
agents\supervisor\settings.py                                       6      0      0      0  100.00%
agents\supervisor\store.py                                         67      0     22      0  100.00%
contracts\__init__.py                                              11      0      2      0  100.00%
contracts\analyst.py                                               65      0      0      0  100.00%
contracts\barrier_history.py                                       40      0      2      0  100.00%
contracts\broker_lifecycle.py                                      60      0     12      0  100.00%
contracts\broker_stops.py                                          53      0      8      0  100.00%
contracts\common.py                                                31      0      2      0  100.00%
contracts\curator.py                                               48      0      0      0  100.00%
contracts\deliberator.py                                           49      0      4      0  100.00%
contracts\execution.py                                             46      0      0      0  100.00%
contracts\feed_notes.py                                            18      0      4      0  100.00%
contracts\forecaster.py                                            39      0      0      0  100.00%
contracts\monitor.py                                               25      0      0      0  100.00%
contracts\operator.py                                              25      0      0      0  100.00%
contracts\pnl.py                                                    3      0      0      0  100.00%
contracts\portfolio_manager.py                                     58      0      6      0  100.00%
contracts\position_refs.py                                          5      0      0      0  100.00%
contracts\position_sync.py                                         37      0      6      0  100.00%
contracts\positions.py                                             88      0     16      0  100.00%
contracts\provider.py                                              72      0      0      0  100.00%
contracts\reporter.py                                              21      0      0      0  100.00%
contracts\researcher.py                                            41      0      0      0  100.00%
contracts\resume.py                                                16      0      0      0  100.00%
contracts\run_posture.py                                            9      0      2      0  100.00%
contracts\scanner.py                                               33      0      0      0  100.00%
contracts\stop_rule.py                                              6      0      0      0  100.00%
contracts\stop_width.py                                            61      0     20      0  100.00%
contracts\supervisor.py                                            32      0      0      0  100.00%
kernel\__init__.py                                                 31      0      0      0  100.00%
kernel\agent.py                                                    21      0      2      0  100.00%
kernel\bootstrap.py                                                49      0     16      0  100.00%
kernel\bus.py                                                      48      0      8      0  100.00%
kernel\bus_azure.py                                                45      0      8      0  100.00%
kernel\bus_azure_config.py                                         33      0      8      0  100.00%
kernel\bus_azure_ready.py                                          57      0     14      0  100.00%
kernel\bus_azure_receiver.py                                       67      0     12      0  100.00%
kernel\bus_celery.py                                               61      0     12      0  100.00%
kernel\bus_celery_config.py                                        15      0      0      0  100.00%
kernel\claim_check.py                                              24      0      2      0  100.00%
kernel\config.py                                                   51      0     14      0  100.00%
kernel\contract.py                                                 28      0      4      0  100.00%
kernel\crypto.py                                                   21      0      0      0  100.00%
kernel\deliberation.py                                             59      0      8      0  100.00%
kernel\deliberation_eval.py                                        52      0      2      0  100.00%
kernel\deliberation_gate.py                                        28      0      6      0  100.00%
kernel\deliberation_guided.py                                      69      0     12      0  100.00%
kernel\deliberation_guided_render.py                               13      0      4      0  100.00%
kernel\deliberation_program.py                                     27      0      4      0  100.00%
kernel\deliberation_prompt_artifacts.py                            53      0     20      0  100.00%
kernel\deliberation_prompts.py                                      4      0      0      0  100.00%
kernel\deliberation_understanding.py                               29      0      4      0  100.00%
kernel\deliberation_verdicts.py                                    21      0      4      0  100.00%
kernel\dspy_engine.py                                              28      0      4      0  100.00%
kernel\dspy_optimizer.py                                           28      0      8      0  100.00%
kernel\ehlo_retry.py                                               58      0      8      0  100.00%
kernel\ehlo_settings.py                                             8      0      0      0  100.00%
kernel\envelope.py                                                 32      0      8      0  100.00%
kernel\errors.py                                                   43      0      2      0  100.00%
kernel\fault_collapse.py                                           37      0      0      0  100.00%
kernel\fault_graph.py                                              39      0      8      0  100.00%
kernel\fault_incidents.py                                          30      0      4      0  100.00%
kernel\fault_query.py                                              38      0      4      0  100.00%
kernel\graph.py                                                    29      0      0      0  100.00%
kernel\graph_env.py                                                38      0     10      0  100.00%
kernel\graph_guarded.py                                            27      0      2      0  100.00%
kernel\graph_memory.py                                             73      0     22      0  100.00%
kernel\graph_pending.py                                             6      0      0      0  100.00%
kernel\graph_postgres.py                                           70      0     14      0  100.00%
kernel\graph_postgres_config.py                                     5      0      0      0  100.00%
kernel\graph_postgres_keys.py                                       3      0      0      0  100.00%
kernel\graph_postgres_queries.py                                   23      0      6      0  100.00%
kernel\graph_postgres_reads.py                                     37      0      2      0  100.00%
kernel\graph_support.py                                            48      0     14      0  100.00%
kernel\graph_vocabulary.py                                         52      0     22      0  100.00%
kernel\handshake.py                                                30      0      0      0  100.00%
kernel\llm.py                                                      31      0      6      0  100.00%
kernel\llm_anthropic.py                                            56      0      4      0  100.00%
kernel\llm_anthropic_responses.py                                  28      0      8      0  100.00%
kernel\llm_error_text.py                                            8      0      2      0  100.00%
kernel\llm_factory.py                                              50      0     14      0  100.00%
kernel\llm_ledger.py                                               45      0      4      0  100.00%
kernel\llm_openai.py                                               53      0     14      0  100.00%
kernel\llm_openai_operator.py                                      53      0      8      0  100.00%
kernel\llm_outage.py                                               51      0     16      0  100.00%
kernel\llm_tokens.py                                               42      0     10      0  100.00%
kernel\market_pack.py                                              18      0      0      0  100.00%
kernel\metrics.py                                                  28      0      0      0  100.00%
kernel\metrics_prometheus.py                                       28      0      0      0  100.00%
kernel\optimizer.py                                                17      0      0      0  100.00%
kernel\payload.py                                                  14      0      0      0  100.00%
kernel\prompt_recipe.py                                            29      0      8      0  100.00%
kernel\serve_loop.py                                               40      0      8      0  100.00%
kernel\serve_transport.py                                          17      0      2      0  100.00%
kernel\startup.py                                                  22      0      6      0  100.00%
kernel\stop.py                                                     80      0     24      0  100.00%
kernel\tunable_envelope.py                                         13      0     10      0  100.00%
kernel\work_loop.py                                                81      0     30      0  100.00%
kernel\work_loop_policy.py                                         22      0      2      0  100.00%
kernel\work_loop_quarantine.py                                     23      0      2      0  100.00%
kernel\work_loop_state.py                                          82      0     18      0  100.00%
orchestration\__init__.py                                          13      0      4      0  100.00%
orchestration\agreement.py                                         36      0      6      0  100.00%
orchestration\batch_chain.py                                       31      0     12      0  100.00%
orchestration\batch_trace.py                                      129      0     50      0  100.00%
orchestration\bindings.py                                          33      0      0      0  100.00%
orchestration\container_alarm_text.py                              85      0     22      0  100.00%
orchestration\container_brief.py                                   27      0      8      0  100.00%
orchestration\container_events.py                                  84      0     14      0  100.00%
orchestration\container_lines.py                                   36      0      6      0  100.00%
orchestration\container_logs.py                                    58      0     10      0  100.00%
orchestration\container_queries.py                                 36      0      4      0  100.00%
orchestration\container_sensor.py                                  88      0     28      0  100.00%
orchestration\container_sensor_graph.py                            30      0      4      0  100.00%
orchestration\container_sensor_guard.py                            66      0      6      0  100.00%
orchestration\daily_brief.py                                       40      0     10      0  100.00%
orchestration\daily_brief_facts.py                                 87      0     22      0  100.00%
orchestration\daily_brief_fills.py                                 46      0     14      0  100.00%
orchestration\daily_brief_guard.py                                 22      0      2      0  100.00%
orchestration\daily_brief_text.py                                  98      0     14      0  100.00%
orchestration\deliberation_replay.py                               20      0      2      0  100.00%
orchestration\deploy_record.py                                     48      0     12      0  100.00%
orchestration\dispatcher.py                                        38      0      2      0  100.00%
orchestration\fleet_readiness.py                                   50      0     18      0  100.00%
orchestration\history_window.py                                    20      0      8      0  100.00%
orchestration\hold_answers.py                                      18      0      4      0  100.00%
orchestration\lineage.py                                           12      0      8      0  100.00%
orchestration\llm_brief.py                                         23      0      6      0  100.00%
orchestration\local_pipeline.py                                    45      0      2      0  100.00%
orchestration\master_serve.py                                      17      0      0      0  100.00%
orchestration\narratives.py                                         7      0      0      0  100.00%
orchestration\observatory.py                                       75      0     24      0  100.00%
orchestration\packs\__init__.py                                     2      0      0      0  100.00%
orchestration\packs\trading_acceptance.py                          71      0     22      0  100.00%
orchestration\packs\trading_boundaries.py                          41      0     12      0  100.00%
orchestration\packs\trading_deliberation_attribution.py            31      0     16      0  100.00%
orchestration\packs\trading_deliberation_view.py                   79      0     24      0  100.00%
orchestration\packs\trading_fill_outcomes.py                       54      0     14      0  100.00%
orchestration\packs\trading_observatory.py                         22      0      8      0  100.00%
orchestration\packs\trading_observatory_chain.py                   39      0      0      0  100.00%
orchestration\packs\trading_observatory_views.py                   53      0      8      0  100.00%
orchestration\packs\trading_parameter_truths.py                     3      0      0      0  100.00%
orchestration\packs\trading_run_postures.py                        13      0      2      0  100.00%
orchestration\packs\trading_stage_view.py                           5      0      0      0  100.00%
orchestration\packs\trading_vault_llm_requests.py                  15      0      0      0  100.00%
orchestration\packs\trading_vault_postgres.py                      11      0      0      0  100.00%
orchestration\packs\trading_vault_probe_support.py                 25      0      4      0  100.00%
orchestration\packs\trading_vault_probes.py                        64      0      0      0  100.00%
orchestration\packs\us_equities_sp500.py                            9      0      0      0  100.00%
orchestration\pm_rejections.py                                     11      0      2      0  100.00%
orchestration\quality_gate.py                                      31      0      6      0  100.00%
orchestration\replay_batch.py                                      37      0      8      0  100.00%
orchestration\replay_chunks.py                                     22      0      6      0  100.00%
orchestration\replay_corpus.py                                     30      0      6      0  100.00%
orchestration\replay_keys.py                                       26      0      0      0  100.00%
orchestration\replay_rounds.py                                     53      0     14      0  100.00%
orchestration\replay_types.py                                      49      0      0      0  100.00%
orchestration\resume.py                                           100      0     34      0  100.00%
orchestration\resume_plan.py                                       40      0      8      0  100.00%
orchestration\run_outcome.py                                        6      0      2      0  100.00%
orchestration\scheduled_dispatch.py                                67      0     12      0  100.00%
orchestration\scheduled_dispatch_actions.py                        49      0      8      0  100.00%
orchestration\scheduled_dispatch_gate.py                           24      0      6      0  100.00%
orchestration\scheduled_dispatch_human.py                          59      0     30      0  100.00%
orchestration\scheduled_dispatch_polling.py                        37      0      8      0  100.00%
orchestration\scheduler.py                                          9      0      0      0  100.00%
orchestration\settings.py                                          20      0      0      0  100.00%
orchestration\shadow_book.py                                       74      0     22      0  100.00%
orchestration\shadow_book_join.py                                  19      0      6      0  100.00%
orchestration\shadow_book_prices.py                                28      0      6      0  100.00%
orchestration\shadow_book_render.py                                27      0      4      0  100.00%
orchestration\shadow_book_scorecard.py                             44      0      6      0  100.00%
orchestration\shadow_book_settings.py                              12      0      0      0  100.00%
orchestration\start.py                                             31      0      0      0  100.00%
orchestration\steps.py                                             22      0      2      0  100.00%
orchestration\telegram_client.py                                   68      0     10      0  100.00%
orchestration\telegram_http.py                                      7      0      0      0  100.00%
orchestration\telegram_port.py                                      9      0      0      0  100.00%
orchestration\telegram_updates.py                                  25      0      8      0  100.00%
orchestration\trace_deliberation.py                                59      0     24      0  100.00%
orchestration\trace_format.py                                       6      0      2      0  100.00%
orchestration\trigger.py                                           14      0      0      0  100.00%
orchestration\verdict_metrics.py                                   36      0      2      0  100.00%
orchestration\verdict_sources.py                                   24      0      6      0  100.00%
orchestration\veto.py                                              23      0      0      0  100.00%
orchestration\veto_context.py                                       2      0      0      0  100.00%
orchestration\veto_context_pm.py                                    2      0      0      0  100.00%
surfaces\__init__.py                                                2      0      0      0  100.00%
surfaces\cli.py                                                    78      0     32      0  100.00%
surfaces\cli_commands.py                                           52      0      4      0  100.00%
surfaces\cli_commands_extra.py                                     32      0      4      0  100.00%
surfaces\cli_commands_queries.py                                   34      0      2      0  100.00%
surfaces\context.py                                                37      0      0      0  100.00%
surfaces\dashboard\__init__.py                                      2      0      0      0  100.00%
surfaces\dashboard\app.py                                          90      0     34      0  100.00%
surfaces\dashboard\azure_http.py                                   45      0      8      0  100.00%
surfaces\dashboard\azure_parsers.py                                55      0     14      0  100.00%
surfaces\dashboard\azure_port.py                                   13      0      0      0  100.00%
surfaces\dashboard\azure_rest.py                                   89      0     16      0  100.00%
surfaces\dashboard\bundle_azure.py                                 49      0      8      0  100.00%
surfaces\dashboard\chat.py                                         75      0     38      0  100.00%
surfaces\dashboard\chat_binding.py                                 25      0      4      0  100.00%
surfaces\dashboard\github_builds.py                                87      0     14      0  100.00%
surfaces\dashboard\github_tag_builds.py                            53      0     16      0  100.00%
surfaces\dashboard\github_tree_diff.py                             34      0      4      0  100.00%
surfaces\dashboard\hold_answer_panel.py                            13      0      4      0  100.00%
surfaces\dashboard\hold_answer_route.py                            32      0      6      0  100.00%
surfaces\dashboard\image_paths.py                                  12      0      0      0  100.00%
surfaces\dashboard\llm_cost_tokens.py                              36      0      2      0  100.00%
surfaces\dashboard\llm_costs.py                                    56      0     10      0  100.00%
surfaces\dashboard\projections.py                                  42      0      4      0  100.00%
surfaces\dashboard\projections_azure.py                            54      0     10      0  100.00%
surfaces\dashboard\projections_currency.py                         47      0     14      0  100.00%
surfaces\dashboard\projections_fleet.py                            71      0     16      0  100.00%
surfaces\dashboard\projections_health.py                           22      0      6      0  100.00%
surfaces\dashboard\projections_infra.py                            24      0      2      0  100.00%
surfaces\dashboard\projections_performance.py                      17      0      6      0  100.00%
surfaces\dashboard\projections_scorecard.py                        26      0      6      0  100.00%
surfaces\dashboard\projections_state.py                            75      0     18      0  100.00%
surfaces\dashboard\projections_summary.py                          40      0     12      0  100.00%
surfaces\dashboard\projections_verdict.py                          75      0     34      0  100.00%
surfaces\dashboard\projections_vitals.py                           46      0      4      0  100.00%
surfaces\dashboard\read_cache.py                                   67      0      4      0  100.00%
surfaces\dashboard\route_selection.py                              10      0      0      0  100.00%
surfaces\dashboard\settings.py                                     31      0      0      0  100.00%
surfaces\dashboard\static_response.py                              32      0      4      0  100.00%
surfaces\dashboard\time_windows.py                                 79      0     24      0  100.00%
surfaces\entrypoint.py                                              3      0      0      0  100.00%
surfaces\mcp_server.py                                             15      0      0      0  100.00%
surfaces\mcp_tools.py                                              56      0     12      0  100.00%
surfaces\metrics_server.py                                         11      0      0      0  100.00%
surfaces\operator_tools.py                                         50      0     16      0  100.00%
surfaces\performance_tool.py                                       18      0      4      0  100.00%
surfaces\plain_errors.py                                            8      0      2      0  100.00%
surfaces\queries\__init__.py                                       10      0      0      0  100.00%
surfaces\queries\_graph.py                                          4      0      0      0  100.00%
surfaces\queries\datasets.py                                       18      0      0      0  100.00%
surfaces\queries\faults.py                                         19      0      0      0  100.00%
surfaces\queries\flags.py                                          21      0      0      0  100.00%
surfaces\queries\fleet_check.py                                    60      0     22      0  100.00%
surfaces\queries\health.py                                         28      0      6      0  100.00%
surfaces\queries\lifecycle.py                                      67      0     18      0  100.00%
surfaces\queries\packs.py                                          13      0      0      0  100.00%
surfaces\queries\performance.py                                    41      0      8      0  100.00%
surfaces\queries\performance_text.py                               44      0     14      0  100.00%
surfaces\queries\positions.py                                      29      0      4      0  100.00%
surfaces\queries\predictors.py                                     29      0      4      0  100.00%
surfaces\queries\proposals.py                                      21      0      0      0  100.00%
surfaces\queries\runs.py                                           38      0      4      0  100.00%
surfaces\queries\scorecard.py                                      64      0     14      0  100.00%
surfaces\queries\scorecard_actions.py                              52      0      8      0  100.00%
surfaces\queries\scorecard_model.py                                70      0      4      0  100.00%
surfaces\queries\scorecard_text.py                                 50      0     10      0  100.00%
surfaces\queries\scorecard_verdicts.py                             31      0      8      0  100.00%
surfaces\queries\stage.py                                          20      0      2      0  100.00%
surfaces\render.py                                                 70      0     26      0  100.00%
surfaces\render_extras.py                                          30      0     14      0  100.00%
surfaces\render_review.py                                          20      0     10      0  100.00%
surfaces\scorecard_settings.py                                      9      0      0      0  100.00%
surfaces\scorecard_tool.py                                         17      0      2      0  100.00%
-------------------------------------------------------------------------------------------------------------
TOTAL                                                           21578      0   4618      0  100.00%
Coverage HTML written to dir htmlcov
Required test coverage of 100.0% reached. Total coverage: 100.00%
=========================== short test summary info ===========================
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_gate_selftest_leaves_nothing.py:57: a link needs a privilege here
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 5242 passed, 9 skipped, 2470 warnings in 636.05s (0:10:36) ==========
uv run python scripts/check_dependency_audit.py
dependency audit failed: WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\urllib3\connection.py", line 239, in _new_conn
    sock = connection.create_connection(
        (self._dns_host, self.port),
    ...<2 lines>...
        socket_options=self.socket_options,
    )
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\urllib3\util\connection.py", line 85, in create_connection
    raise err
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\urllib3\util\connection.py", line 73, in create_connection
    sock.connect(sa)
    ~~~~~~~~~~~~^^^^
ConnectionRefusedError: [WinError 10061] No connection could be made because the target machine actively refused it

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\urllib3\connectionpool.py", line 779, in urlopen
    self._prepare_proxy(conn)
    ~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\urllib3\connectionpool.py", line 1074, in _prepare_proxy
    conn.connect()
    ~~~~~~~~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\urllib3\connection.py", line 827, in connect
    self.sock = sock = self._new_conn()
                       ~~~~~~~~~~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\urllib3\connection.py", line 254, in _new_conn
    raise NewConnectionError(
        self, f"Failed to establish a new connection: {e}"
    ) from e
urllib3.exceptions.NewConnectionError: HTTPSConnection(host='127.0.0.1', port=9): Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it

The above exception was the direct cause of the following exception:

urllib3.exceptions.ProxyError: ('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=9): Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it"))

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\requests\adapters.py", line 696, in send
    resp = conn.urlopen(
        method=request.method,
    ...<9 lines>...
        chunked=chunked,
    )
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\urllib3\connectionpool.py", line 847, in urlopen
    retries = retries.increment(
        method, url, error=new_e, _pool=self, _stacktrace=sys.exc_info()[2]
    )
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\urllib3\util\retry.py", line 555, in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=9): Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it")))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Scripts\pip-audit.exe\__main__.py", line 10, in <module>
    sys.exit(audit())
             ~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\pip_audit\_cli.py", line 554, in audit
    for spec, vulns in auditor.audit(source):
                       ~~~~~~~~~~~~~^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\pip_audit\_audit.py", line 68, in audit
    for dep, vulns in self._service.query_all(specs):
                      ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\pip_audit\_service\interface.py", line 180, in query_all
    yield self.query(spec)
          ~~~~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\pip_audit\_service\pypi.py", line 64, in query
    response: requests.Response = self.session.get(url=url, timeout=self.timeout)
                                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\requests\sessions.py", line 671, in get
    return self.request("GET", url, params=params, **kwargs)
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\requests\sessions.py", line 651, in request
    resp = self.send(prep, **send_kwargs)
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\requests\sessions.py", line 784, in send
    r = adapter.send(request, **kwargs)
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\cachecontrol\adapter.py", line 76, in send
    resp = super().send(request, stream, timeout, verify, cert, proxies)
  File "C:\Users\yury_\Downloads\project\ta-s285\.venv\Lib\site-packages\requests\adapters.py", line 723, in send
    raise ProxyError(e, request=request)
requests.exceptions.ProxyError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by ProxyError('Unable to connect to proxy', NewConnectionError("HTTPSConnection(host='127.0.0.1', port=9): Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it")))
make: *** [Makefile:60: ci] Error 1
CI_EXIT=2
```

The two independent security commands, under the same offline environment:

```text
$ uv run pre-commit run detect-secrets --all-files
$ uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
DETECT_SECRETS_EXIT=0
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 2 new file(s)
UNTRACKED_SECRETS_EXIT=0
```

Offline bump evidence; `uv.lock` was staged successfully:

```text
$ uv lock --offline
Resolved 180 packages in 324ms
Updated trading-agents v0.128.6 -> v0.128.7
LOCK_EXIT=0
$ git add -- uv.lock
```

**`make gate-ran`:** Not done; planner after the push. No push, merge, deployment, CodeQL or live proof was performed.

**Not met / verified failing:** `make ci` is verified failing (exit 2) only because the dependency audit cannot refresh PyPI data offline; an overall green CI gate and a current vulnerability verdict are not proven. Planner's F1 (`wq131_probe.py` versus `f1_proto.txt`) is not done; F2 on the fleet is not done. Push, `make gate-ran`, CodeQL, merge and deployment are not done. The two unchecked success factors remain unchecked for those reasons.

---

## Return notes

Final documentation checks after filling the handback:

```text
$ uv run --offline --no-sync python scripts/check_sprint_status.py
docs/sprints/sprint-285-the-dispatcher-keeps-the-deadline-it-tells.md: BUILT | **Status:** BUILT
SPRINT_STATUS_EXIT=0
$ uv run --offline --no-sync python scripts/check_tracker_size.py
[OK] docs/STATE.md: 34,596 of 40,000 bytes (86 %)
[OK] docs/work-queue.md: 47,916 of 64,000 bytes (74 %)
[WARN] docs/sprints/README.md: 93,337 of 96,000 bytes (97 %)
[OK] docs/sprints/INDEX.md: 23,863 of 48,000 bytes (49 %)
[WARN] docs/design-log.md: 478,552 of 512,000 bytes (93 %)
[OK] docs/laws/functionality-checks.md: 138,521 of 160,000 bytes (86 %)
[OK] docs/laws/drift-register.md: 134,514 of 160,000 bytes (84 %)
TRACKER_SIZE_EXIT=0
$ uv run --offline --no-sync python scripts/check_markdown_links.py
MARKDOWN_LINKS_EXIT=0
$ uv run --offline --no-sync python scripts/check_version_scheme.py
VERSION_SCHEME_EXIT=0
```

- The production fix, law cycle, deployment row and six existing-test edits are the exact Appendix: all 15 canonical blobs match. No other existing test changed. No state, design-log or work-queue edit; no agent, contract, kernel, brief, sensor, pack, Dockerfile, infrastructure script or `place_scheduled_run` edit.
- A4's two required scenarios are separate parametrized cases. This yields 19 cases and 5,242 full-suite passes, one more than the prototype's combined A4 count of 5,241; no extra test function or behavior was added. A3 still fails only at 23:20:00 and A4 only on the late-answer case on the unchanged tree.
- The first attempted red-log redirection did not launch pytest because `.tools` did not exist. Created the ignored evidence directory, then ran and pasted the actual unchanged-tree output before either Appendix section. Pasted logs trim trailing whitespace only; their raw versions remain in `.tools` and `ci.txt`. Initial formatting made the new once test file 211 lines; shortened it to 198 before running pytest, preserving all planned assertions. Final test files are 198 and 98 lines after Ruff formatting.
- Main was `d7b728aaba92f041bb7f8d9041a08f23ef5b6b19`, version `0.128.06`; the next PATCH is `0.128.07`. `uv lock --offline` resolved 180 packages and changed only the project version to normalized `0.128.7`; `uv.lock` was staged. No bare sync or network/live-service operation was used.
- The dependency audit is the only failing CI step; the planner must rerun it online, then perform the exact-HEAD remote gates, CodeQL/blob review and F1 comparison before merge. The planner owns any deployment and F2. The branch is BUILT, without a green overall CI, remote, merged, deployed or live-proof claim.

---

## Appendix — the prototype (`proto-s285` `d795aad6`: `make ci` 5,241 passed, 9 skipped, 100.00 %, every step green, the dependency audit included; 17 / 17 breaks red against the planner's tests)

Apply with `git apply` from the worktree root. Section 1 is production code, section 2 the law cycle, `docs/deployment.md`'s dispatcher row and the six existing-test edits. Both come from one diff; apply section 1, then section 2. The version bump is yours (step 5), not here.

### Section 1 — production code (4 files)

```diff
diff --git a/orchestration/scheduled_dispatch.py b/orchestration/scheduled_dispatch.py
index 697ddc14..3b2e2866 100644
--- a/orchestration/scheduled_dispatch.py
+++ b/orchestration/scheduled_dispatch.py
@@ -73,7 +73,7 @@ class ScheduledDispatchDecision:
 class ScheduledDispatchResult:
     """Scheduled-run outcome after optional graph placement."""

-    action: Literal["placed", "skipped", "held"]
+    action: Literal["placed", "already-placed", "skipped", "held"]
     run_id: str
     reason: str
     node_key: str | None = None
diff --git a/orchestration/scheduled_dispatch_actions.py b/orchestration/scheduled_dispatch_actions.py
index 93568f76..602bb726 100644
--- a/orchestration/scheduled_dispatch_actions.py
+++ b/orchestration/scheduled_dispatch_actions.py
@@ -12,6 +12,8 @@ from typing import TYPE_CHECKING
 from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

 from agents.scanner.universe import FileUniverse
+from contracts.provider import RUN_REQUEST_LABEL
+from contracts.run_posture import RUN_POSTURE_DEGRADED, RUN_POSTURE_NORMAL
 from orchestration.scheduled_dispatch import (
     ScheduledDispatchResult,
     place_scheduled_run,
@@ -27,7 +29,9 @@ if TYPE_CHECKING:
     from orchestration.scheduled_dispatch import TradingCalendar

 _ACTION_START = time(22, 30)
-_ACT_BY = time(23, 20)
+# DL-309: the last placing fire leaves a run 20 minutes before the 23:30 window end.
+_ACT_BY = time(23, 10)
+_TICK_MINUTES = 10  # The pack's */10 cron; a fire lands seconds after its tick.


 def act_by_text(now: datetime, timezone: str) -> str:
@@ -44,17 +48,44 @@ def act_by_text(now: datetime, timezone: str) -> str:
     return f"{deadline:%H:%M} {timezone.rsplit('/', 1)[-1]} ({utc})"


+def fire_tick(now: datetime) -> time:
+    """Return the cron tick a fire belongs to: its time floored to ten minutes."""
+    return time(now.hour, now.minute - now.minute % _TICK_MINUTES)
+
+
 def is_action_time(now: datetime) -> bool:
     """Return whether a dispatcher fire may place a run in the fleet window."""
-    return _ACTION_START <= now.time().replace(tzinfo=None) <= _ACT_BY
+    return _ACTION_START <= fire_tick(now) <= _ACT_BY


 def outside_window(
-    run_id: str, reason: str, hold: Node | None
+    run_id: str, now: datetime, hold: Node | None
 ) -> ScheduledDispatchResult:
-    """Keep an existing hold, or skip placement outside the bounded window."""
+    """Keep an existing hold, or skip, naming which side of the window the fire is."""
+    side = "before" if fire_tick(now) < _ACTION_START else "after"
+    reason = f"{side} the placing window, {_ACTION_START:%H:%M} to {_ACT_BY:%H:%M} UTC"
+    if hold is None:
+        return ScheduledDispatchResult("skipped", run_id, reason)
+    failures = tuple(str(item) for item in hold.props.get("failures", ()))
+    return ScheduledDispatchResult("held", run_id, reason, hold.key, failures=failures)
+
+
+def already_placed(graph: GraphStore, run_id: str) -> ScheduledDispatchResult | None:
+    """Return the day's run an earlier fire placed, or None while there is none."""
+    node = graph.get_node(RUN_REQUEST_LABEL, f"run-request:{run_id}")
+    if node is None:
+        return None
+    degraded = node.props.get("run_posture") == RUN_POSTURE_DEGRADED
     return ScheduledDispatchResult(
-        "held" if hold is not None else "skipped", run_id, reason
+        "already-placed",
+        run_id,
+        "placed by an earlier fire",
+        node.key,
+        tuple(str(ticker) for ticker in node.props.get("tickers", ())),
+        failures=tuple(str(item) for item in node.props.get("degraded_by", ()))
+        if degraded
+        else (),
+        run_posture=RUN_POSTURE_DEGRADED if degraded else RUN_POSTURE_NORMAL,
     )


diff --git a/orchestration/scheduled_dispatch_human.py b/orchestration/scheduled_dispatch_human.py
index 6198a71e..04626c5a 100644
--- a/orchestration/scheduled_dispatch_human.py
+++ b/orchestration/scheduled_dispatch_human.py
@@ -20,6 +20,7 @@ from orchestration.scheduled_dispatch import (
 )
 from orchestration.scheduled_dispatch_actions import (
     act_by_text,
+    already_placed,
     is_action_time,
     outside_window,
     place_override,
@@ -64,8 +65,14 @@ def dispatch_with_human_answer(
     brief_safely(
         graph, telegram, run_id=decision.run_id, as_of=as_of, now=now, settings=settings
     )
+    placed = already_placed(graph, decision.run_id)
+    if placed is not None:
+        # Once placed, a fire reads no readiness and holds nothing (DSP-NEV-04).
+        if is_action_time(now) and placed.run_posture == RUN_POSTURE_DEGRADED:
+            _notify_degraded_run(graph, telegram, placed, now)
+        return placed
     if not is_action_time(now):
-        return outside_window(decision.run_id, decision.reason, hold)
+        return outside_window(decision.run_id, now, hold)
     if answer == "skip_today":
         return ScheduledDispatchResult("skipped", decision.run_id, "operator")
     if answer == "run_now":
diff --git a/scripts/dispatch_scheduled_run.py b/scripts/dispatch_scheduled_run.py
index ea9b5ee0..95d32959 100644
--- a/scripts/dispatch_scheduled_run.py
+++ b/scripts/dispatch_scheduled_run.py
@@ -122,7 +122,7 @@ def format_dispatch_result(result: ScheduledDispatchResult) -> str:
     """Render an intentional hold as a successful scheduler decision."""
     if result.action == "held":
         return (
-            f"held {result.run_id} reason={result.readiness_state} "
+            f"held {result.run_id} reason={result.readiness_state or result.reason} "
             f"failures={len(result.failures)}"
         )
     return f"{result.action} {result.run_id} reason={result.reason}"
```

### Section 2 — the law cycle, the deployment row and the six existing-test edits (11 files)

```diff
diff --git a/docs/deployment.md b/docs/deployment.md
index f07d60cf..f750790d 100644
--- a/docs/deployment.md
+++ b/docs/deployment.md
@@ -230,7 +230,7 @@ Default schedule:

 | Component | Schedule |
 | --- | --- |
-| `dispatcher-cron` job | `*/10 22-23 * * 1-5` UTC: every ten minutes, weekdays; it places a run only from 22:30 to 23:20 ([DL-183](design-log-archive/INDEX.md)) |
+| `dispatcher-cron` job | `*/10 22-23 * * 1-5` UTC: every ten minutes, weekdays; it places a run only from the 22:30 fire to the 23:10 fire, and only once ([DL-183](design-log-archive/INDEX.md), [DL-309](design-log.md)) |
 | `master` app cron scale window | starts `0 22 * * 1-5` UTC on the live app (operator, 2026-10-12, [DL-294](design-log.md) amendment 1): one readiness check before the 22:30 run; the script's default since [S274](sprints/sprint-274-a-full-up-keeps-the-masters-live-start.md) |
 | 15 agent app cron scale window | starts `30 22 * * 1-5` UTC |
 | all app scale windows | end `30 23 * * 1-5` UTC (operator, 2026-10-11, [DL-294](design-log.md): weekdays only, one hour; it was every day until 00:30) |
diff --git a/docs/laws/INDEX.md b/docs/laws/INDEX.md
index 167a87e5..84b43d19 100644
--- a/docs/laws/INDEX.md
+++ b/docs/laws/INDEX.md
@@ -52,7 +52,7 @@ Each agent's law files live at `agents/<name>/laws/`:
 | curator | ✅ LOCKED v1.1 (S205) | 23 / 47 | S205 rewrites and proves `CUR-TYP-01`; counters are clauses proven / clauses declared |
 | researcher | ✅ LOCKED v1.2 (DL-203) | 20 / 43 | DL-203 reconciles `PARAM` only; S205 rewrites and proves `RES-TYP-01`; counters are clauses proven / clauses declared |
 | master | ✅ LOCKED v1.12 (S277, DL-289) | 33 / 58 | S277 (DL-289 amendment 4) re-proves every-candidate probing, later proven fallback/key handover, refusal and unanswered pass-over, and recorded llm_fallbacks; no clause added. S276 (DL-289 amendment 1) adds and proves MST-OUT-05, MST-NEV-08 and MST-FAIL-08; amended MST-OUT-04, MST-NEV-07 and MST-OBS-04 re-proven for ordered candidate choice, key containment and recorded passed-over outcomes. Before that S272 (DL-297) adds and proves MST-TRG-03, MST-ORD-04 and MST-OBS-05 and proves amended MST-OUT-03; DRIFT-113 corrected, recovery at boot not built; before that S262 (DL-282) amends and re-proves `MST-OUT-04` for selected-vendor readiness and adds and proves `MST-NEV-07` for validated probe/key selection; DRIFT-105 corrected; before that S251 adds and proves `MST-FAIL-07` (the start-up refusal of an unhonourable remediation mode; remediation outside the constitution until DL-36 C/D; DRIFT-059); S244 amends and proves `MST-TRG-01`/`MST-ORD-02`, re-proves `MST-STA-02`/`MST-IDM-01`, and adds and proves `MST-IDM-03` (boot-id replay), `MST-ORD-03` (concurrent EHLO) and `MST-FAIL-06` (loud budget exhaustion), DRIFT-091; S232 adds and proves `MST-DEP-05` (substrate-only imports) and corrects `MST-NEV-01`/`MST-SEC-03`/`MST-DEP-03` to name the pack data actually consulted; DL-203 reconciles `PARAM` only; S217 adds and proves `MST-OUT-04` whole-fleet readiness and `MST-FAIL-05` classification; S205 rewrites and proves `MST-TYP-01`; S188 adds and proves credential-test handover guards; RSA/Key Vault clauses deferred S74; S204 gives every clause a row and makes rowless clauses a hard gate |
-| dispatcher | ✅ LOCKED v1.6 (S278, DL-301 amendment 7) | 43 / 47 | S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. Before that S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. S251 names the daily brief in the purpose line and `DSP-IDN-03` (DRIFT-077); Component book under `orchestration/laws/dispatcher/`; scheduled placement, the human-hold loop and the daily brief (S234, DL-230/DL-231); `orchestration.dispatcher.Dispatcher` named out of scope by DL-221; closes DRIFT-068 and DRIFT-069 |
+| dispatcher | ✅ LOCKED v1.7 (S285, DL-309) | 46 / 49 | S285 (DL-309) adds and proves DSP-NEV-04 (a placed run is never held again) and DSP-OBS-04 (each fire's line says what it did), amends DSP-TRG-01 and DSP-PERF-01 (the last placing fire is the 23:10 tick) and DSP-IDM-02, and proves DSP-TYP-01 with the fourth action, `already-placed`. S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. Before that S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. S251 names the daily brief in the purpose line and `DSP-IDN-03` (DRIFT-077); Component book under `orchestration/laws/dispatcher/`; scheduled placement, the human-hold loop and the daily brief (S234, DL-230/DL-231); `orchestration.dispatcher.Dispatcher` named out of scope by DL-221; closes DRIFT-068 and DRIFT-069 |
 | surfaces | ✅ LOCKED v1.8 (S274, S270, S267, S263, S262, S251, S236, S229, S228) | 31 / 38 | S274 (DL-300) reconciles `PARAM` only: `master_window_start_utc` is 22:00, the master's live wake (DL-294 amendment 1); no clause changes; before that S270 (DL-295) reconciles `PARAM` only: `window_end_utc` is 23:30 and the new `window_days_utc` is 1-5, the operator's wake window (DL-294); no clause changes; before that S267 (DL-288) adds and proves `SRF-DEP-04`: complete-tag evidence from every attempt of a successful image-build run, latest first and earlier attempts newest first, with main-history and unreadable-evidence guards; DRIFT-111 corrected; before that S263 (DL-284) amends and re-proves `SRF-DEP-03` for model-family disconnection and its start-up reason; before that S262 (DL-282) adds and proves `SRF-DEP-03`: dashboard chat binds only through its selected provider and disconnects for absent keys, unknown providers and either vendor configuration error; DRIFT-105 corrected; before that S251 narrows `SRF-OUT-03` (quick asks write no audit fact; DRIFT-078); Component book under `surfaces/laws/`; dashboard, CLI, MCP, chat and operator-intent write boundaries; S236 adds and proves `SRF-OUT-08` (the unattended scorecard) and the `scorecard` tool, and files DRIFT-078; selected-run scoping cites corrected DRIFT-022 |

 See [ledger.md](ledger.md) for the canonical version of this table.
diff --git a/docs/laws/ledger.md b/docs/laws/ledger.md
index e5b3b3b5..e798fa5f 100644
--- a/docs/laws/ledger.md
+++ b/docs/laws/ledger.md
@@ -49,7 +49,7 @@ and torn down to zero. Historical Neo4j rows remain valid evidence for the pre-S
 | operator | ✅ v1.10 (LOCKED) | 20 / 51 | 🟨 partial — **20 of 51 clauses proven** after S269 (DL-292) rewords and re-proves `OPR-FAIL-02`: only text, a number or a boolean is a value; `null`, lists and objects are omitted from required and optional parameters, so missing required values are refused with the existing sentence and audit, while scalar text and blank-text behavior are unchanged; DRIFT-112 corrected; no clause added; before that S268 (DL-290) rewords and re-proves `OPR-FAIL-02`: an intent of no known family, or lacking a parameter its family requires under any accepted name, is refused before its audit, which reads `refused`, and no `Intent` is written; the prompt states each family's parameter names; DRIFT-109 corrected; no clause added; before that S265 (DL-286) rewords and re-proves `OPR-FAIL-01`: failed requests are audited on both capabilities, one operator fault and one plain reason, no grammar or error text in graph; malformed JSON is a fault-free refusal; DRIFT-107/108 corrected; no clause added; before that S264 (DL-285) re-proves `OPR-STA-03` for vendor stop reasons and billed counts on both reply paths and adds/proves `OPR-FAIL-04` for audited, fault-free cut-offs with one sentence and explicit grammar preserved; DRIFT-106 corrected; before that S263 (DL-284) amends and re-proves `OPR-DEP-01` for provider effort resolution and pre-call model-family refusal; PARAM effort and CAP reconciled; before that S262 (DL-282) amends and re-proves `OPR-DEP-01` for the selected vendor, model resolution and no fallback; PARAM reconciled; before that S256 (DL-272) rewrites and proves `OPR-IDM-02`: duplicate commands share audit/intent while every model call has its own row; DRIFT-104 corrected; S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; 31 have a gray row |
 | supervisor | ✅ v1.3 (LOCKED) | 23 / 48 | 🟨 partial — **23 of 48 clauses proven** after S251 (DL-260) declares the divergence-family exception in `SUP-IDN-02` (DRIFT-094) and proves `SUP-OBS-02` on its real sources (live `Fault` incidents, unresolved critical Flags; DRIFT-076); v1.2 (DL-225) was never reflected here and is now; after S205 rewrites and proves `SUP-TYP-01`; S179 proves append-only `FaultResolution` retirement (`SUP-OBS-03`); 26 have a gray row |
 | master | ✅ v1.12 (LOCKED) | 33 / 58 | S277 (DL-289 amendment 4) re-proves every-candidate probing, later proven fallback/key handover, refusal and unanswered pass-over, and recorded llm_fallbacks; no clause added. S276 (DL-289 amendment 1) adds and proves MST-OUT-05, MST-NEV-08 and MST-FAIL-08; amended MST-OUT-04, MST-NEV-07 and MST-OBS-04 re-proven for ordered candidate choice, key containment and recorded passed-over outcomes. 🟨 partial — **33 of 58 clauses proven** after S272 (DL-297) adds and proves MST-TRG-03, MST-ORD-04 and MST-OBS-05 and proves amended MST-OUT-03; DRIFT-113 corrected, recovery at boot not built; before that S262 (DL-282) amends and re-proves `MST-OUT-04` for selected-vendor readiness and adds and proves `MST-NEV-07` for validated probe/key selection; DRIFT-105 corrected; before that S251 (DL-260) adds and proves `MST-FAIL-07`: master refuses to start in a remediation mode it cannot honour; attempting remediation is stated outside the constitution until DL-36 Pieces C/D (DRIFT-059); after S244 amends and proves `MST-TRG-01` (`POST /ehlo`, the agent's bounded resend with one boot id) and `MST-ORD-02` (master may be asleep or busy), re-proves `MST-STA-02`/`MST-IDM-01` on their amended text, and adds and proves `MST-IDM-03` (a repeated boot id replays), `MST-ORD-03` (concurrent EHLO service) and `MST-FAIL-06` (a spent budget exits loud); S232 adds and proves `MST-DEP-05` (substrate-only imports) and corrects `MST-NEV-01`/`MST-SEC-03`/`MST-DEP-03` to name the pack data actually consulted; S217 adds and proves `MST-OUT-04` whole-fleet readiness and `MST-FAIL-05` classification; S205 rewrites and proves `MST-TYP-01`; S188 adds and proves credential-test handover guards; S204 gives every clause a row and promotes missing rows to a hard gate · RSA signing + Key Vault + integration clauses deferred (S73/S74) |
-| dispatcher | ✅ v1.6 (LOCKED) | 43 / 47 | S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. 🟨 partial — **43 of 47 clauses proven**; S251 names the daily brief in the purpose line and `DSP-IDN-03`'s scope (DRIFT-077), count unchanged; after S234 adds and proves the daily brief (`DSP-IDN-04`, `DSP-TRG-03`, `DSP-OUT-06`, `DSP-IDM-03`, `DSP-SEC-02`, `DSP-FAIL-03`) and proves `DSP-SEC-01` across every port operation; `DSP-DEP-01` amended and still gray (partial: `CAP` conformance). S229 covered scheduled run placement, readiness holds, degraded placement, human answers and notices; names `orchestration.dispatcher.Dispatcher` out of scope by DL-221; closes DRIFT-068 and DRIFT-069. |
+| dispatcher | ✅ v1.7 (LOCKED) | 46 / 49 | S285 (DL-309) adds and proves DSP-NEV-04 (a placed run is never held again) and DSP-OBS-04 (each fire's line says what it did), amends DSP-TRG-01 and DSP-PERF-01 (the last placing fire is the 23:10 tick) and DSP-IDM-02, and proves DSP-TYP-01 with the fourth action, `already-placed`. S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. 🟨 partial — **46 of 49 clauses proven**; S251 names the daily brief in the purpose line and `DSP-IDN-03`'s scope (DRIFT-077), count unchanged; after S234 adds and proves the daily brief (`DSP-IDN-04`, `DSP-TRG-03`, `DSP-OUT-06`, `DSP-IDM-03`, `DSP-SEC-02`, `DSP-FAIL-03`) and proves `DSP-SEC-01` across every port operation; `DSP-DEP-01` amended and still gray (partial: `CAP` conformance). S229 covered scheduled run placement, readiness holds, degraded placement, human answers and notices; names `orchestration.dispatcher.Dispatcher` out of scope by DL-221; closes DRIFT-068 and DRIFT-069. |
 | surfaces | ✅ v1.8 (LOCKED) | 31 / 38 | 🟨 partial — **31 of 38 clauses proven**; S274 (DL-300) reconciles `PARAM` only: `master_window_start_utc` is 22:00, the master's live wake (DL-294 amendment 1); no clause changes; before that S270 (DL-295) reconciles `PARAM` only: `window_end_utc` is 23:30 and the new `window_days_utc` is 1-5, the operator's wake window (DL-294); no clause changes; before that S267 (DL-288) adds and proves `SRF-DEP-04`: complete-tag evidence from every attempt of a successful image-build run, latest first and earlier attempts newest first, with main-history and unreadable-evidence guards; DRIFT-111 corrected; before that S263 (DL-284) amends and re-proves `SRF-DEP-03` for model-family disconnection and its start-up reason; before that S262 (DL-282) adds and proves `SRF-DEP-03`: dashboard chat binds only through its selected provider and disconnects for absent keys, unknown providers and either vendor configuration error; DRIFT-105 corrected; before that S251 narrows `SRF-OUT-03` to model-composed answers and names the quick asks as graph reads that write no audit fact (DRIFT-078), count unchanged; after S236 adds and proves `SRF-OUT-08` (the unattended vital and the `scorecard` answer: G1, G3 and two clocks from the acceptance gate's verdict and the records human actions leave) and lists `scorecard` in `SRF-TRG-02`; DRIFT-078 is filed for `SRF-OUT-03`'s silence on the quick asks. S228 added and proved `SRF-OUT-07` (28 of 35); S229 authored the book (27 of 34). Covers dashboard, CLI, MCP, chat and operator-intent write boundaries; selected-run scoping cites DRIFT-022 as already corrected. |

 *2026-09-23 — [DL-203](../design-log.md) (work-queue item 33) amended nine of these laws in
diff --git a/orchestration/laws/dispatcher/laws.md b/orchestration/laws/dispatcher/laws.md
index 8dedaee7..26c88798 100644
--- a/orchestration/laws/dispatcher/laws.md
+++ b/orchestration/laws/dispatcher/laws.md
@@ -1,6 +1,6 @@
 # `Dispatcher` — Laws

-**Prefix:** `DSP` · **status:** LOCKED v1.6 · **Owner:** Yury Gurevich
+**Prefix:** `DSP` · **status:** LOCKED v1.7 · **Owner:** Yury Gurevich

 > Decide whether the scheduled daily graph-pull run is placed, skipped, held, or placed in degraded posture,
 > brief the operator once on each run it placed, and tell the operator when a container of the
@@ -61,9 +61,11 @@ green only when a functional test cites its ID (conventions §3). Tests + status

 ## Triggers (`TRG`)

-- **DSP-TRG-01** — A cron fire may place a run only inside the action window
-  `_ACTION_START=22:30 UTC` through `_ACT_BY=23:20 UTC`. A late `run_now` answer remains evidence but
-  cannot place a run.
+- **DSP-TRG-01** — A cron fire may place a run only inside the action window, read by the fire's
+  ten-minute tick (the job's cron is `*/10`, and a fire lands seconds after its tick): from
+  `_ACTION_START=22:30 UTC` to the last placing fire, `_ACT_BY=23:10 UTC`. The last placing fire leaves
+  a run 20 minutes before the fleet's window ends at 23:30 UTC, which the longest measured run fits
+  (DL-309). A late `run_now` answer remains evidence but cannot place a run.
 - **DSP-TRG-02** — Calendar skip is evaluated before readiness, Telegram polling, notices, or hold
   writes.
 - **DSP-TRG-03** — Every fire whose `as_of` is its own UTC date attempts that day's brief after the
@@ -129,6 +131,10 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   the configured universe membership, and never decides what to buy, sell, size, or veto.
 - **DSP-NEV-03** — The sensor never acts on a container: it starts, stops, scales, restarts and
   reconfigures nothing, and calls no management API. It reads the log workspace and tells.
+- **DSP-NEV-04** — The scheduled dispatcher never holds a run whose day-keyed `RunRequest` exists.
+  Once an earlier fire placed it, on a passing check or on a `run_now` answer, a fire reads no
+  readiness, writes no `RunHold` and sends no hold notice; it reports `already-placed`, and inside
+  the action window it retries a degraded notice that was not sent.

 ## State & effects (`STA`)

@@ -141,8 +147,9 @@ green only when a functional test cites its ID (conventions §3). Tests + status

 - **DSP-IDM-01** — The scheduled run id is deterministic from the session date:
   `sched-YYYY-MM-DD`.
-- **DSP-IDM-02** — Re-firing the same scheduled placement is idempotent: ready runs merge to one
-  `RunRequest`, and failing runs merge to one active `RunHold`.
+- **DSP-IDM-02** — Re-firing the same scheduled placement is idempotent: once the day's `RunRequest`
+  exists a fire writes no `RunRequest` and no `RunHold`, and until it exists failing runs merge to
+  one active `RunHold`.
 - **DSP-IDM-03** — At most one brief per run id. A fire sends only while the run's `RunRequest`
   carries no `brief_sent_at`; a successful send writes `brief_sent_at`, `brief_message_id`, and
   `brief_verdict` (the verdict the brief carried, `NOT_FINISHED` for a RED brief) on that
@@ -181,7 +188,8 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 ## Type alignment (`TYP`)

 - **DSP-TYP-01** — `ScheduledDispatchResult` is the dispatcher output contract and its action space
-  is exactly `placed`, `skipped`, or `held`, with readiness details present only when relevant.
+  is exactly `placed`, `already-placed`, `skipped`, or `held`, with readiness details present only
+  when relevant.

 ## Security & privilege (`SEC`)

@@ -215,10 +223,15 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 - **DSP-OBS-03** — Each sensor run prints one line: the rows read, the new events, the alarms and how
   many were told, or the failure. Every alarm and report the sensor kept, and every read, is
   reconstructable from `ContainerEvent` and `ContainerSensorRead` facts and their `TOLD` edges.
+- **DSP-OBS-04** — Each fire prints one line that names what it did and why: `placed` with the
+  calendar's reason on the fire that wrote the run; `already-placed` on every later fire; `held`
+  with the readiness state and the failure count, or, once the action window has passed, that it
+  has; `skipped` with the calendar's reason, `operator` for a skip answer, or which side of the
+  action window the fire is on, with the window's times.

 ## Performance envelope (`PERF`)

-- **DSP-PERF-01** — Human override placement is bounded to the 22:30-23:20 UTC action window; outside
+- **DSP-PERF-01** — Human override placement is bounded to the 22:30-23:10 UTC action window; outside
   that window the dispatcher does not begin a run.

 ## Capability declaration (`CAP`)
@@ -304,3 +317,7 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   whoever caused it: a revision update the platform failed, its autoscaler failing, and any other
   row it marks `Warning` but the five measured by-products of a deploy or a wake. `DSP-IN-05`
   amended. No clause added.
+- v1.7 — S285 (DL-309, work-queue 131 parts b and d): the last placing fire is the 23:10 tick, read
+  by the fire's tick, and leaves a run 20 minutes before the 23:30 window end; a placed run is
+  never held again; each fire's line says what it did. New `DSP-NEV-04` and `DSP-OBS-04`;
+  `DSP-TRG-01`, `DSP-IDM-02`, `DSP-TYP-01` (now proven) and `DSP-PERF-01` amended.
diff --git a/orchestration/laws/dispatcher/test-plan.md b/orchestration/laws/dispatcher/test-plan.md
index 3ca07956..a30a720d 100644
--- a/orchestration/laws/dispatcher/test-plan.md
+++ b/orchestration/laws/dispatcher/test-plan.md
@@ -1,6 +1,6 @@
 # `Dispatcher` — Law Test-Plan

-**Prefix:** `DSP` · **status:** LOCKED v1.6 · **aligned with:** laws.md LOCKED v1.6
+**Prefix:** `DSP` · **status:** LOCKED v1.7 · **aligned with:** laws.md LOCKED v1.7

 | Clause | Description | Test | Status |
 | --- | --- | --- | --- |
@@ -12,7 +12,7 @@
 | DSP-IN-02 | Normal and override placement require a non-empty configured universe. | `orchestration/tests/test_scheduled_dispatch.py::test_empty_configured_universe_is_an_error`; `orchestration/tests/test_scheduled_dispatch_human_edges.py::test_place_override_rejects_empty_universe` | 🟩 |
 | DSP-IN-03 | Readiness uses the latest fresh parseable `FleetPreflight`; missing, stale, malformed, non-degradable, or undeclared failed evidence holds, and declared degradable failures degrade. | `orchestration/tests/test_scheduled_dispatch_readiness.py::test_absent_preflight_holds_with_unknown_readiness`; `orchestration/tests/test_scheduled_dispatch_readiness.py::test_stale_passing_preflight_holds_as_unknown`; `orchestration/tests/test_scheduled_dispatch_degraded_readiness.py::test_llm_only_failing_check_places_degraded_run_and_releases_hold`; `orchestration/tests/test_scheduled_dispatch_degraded_readiness.py::test_non_degradable_failure_keeps_llm_outage_held`; `orchestration/tests/test_scheduled_dispatch_degraded_readiness.py::test_unparseable_master_stale_and_missing_checks_still_hold`; `orchestration/tests/test_scheduled_dispatch_degraded_readiness.py::test_degradable_set_comes_from_the_pack_declaration` | 🟩 |
 | DSP-IN-04 | Human answers are only `run_now` or `skip_today`, scoped to the matching scheduled run id; free text or stale ids cannot decide today's placement. | `orchestration/tests/test_scheduled_dispatch_polling.py::test_c13_plain_text_updates_are_ignored`; `orchestration/tests/test_scheduled_dispatch_polling.py::test_c14_yesterdays_answer_is_inert_for_todays_run`; `orchestration/tests/test_scheduled_dispatch_notices.py::test_c6_run_now_places_despite_a_failing_preflight`; `orchestration/tests/test_scheduled_dispatch_notices.py::test_c7_skip_today_writes_no_run_and_formats_operator_skip` | 🟩 |
-| DSP-TRG-01 | A cron fire may place only in the 22:30-23:20 UTC action window; a late `run_now` answer remains evidence but cannot place. | `orchestration/tests/test_scheduled_dispatch_polling.py::test_late_run_now_is_recorded_but_never_placed` | 🟩 |
+| DSP-TRG-01 | A cron fire may place only from the 22:30 tick to the last placing fire, the 23:10 tick, read by the fire's ten-minute tick; that fire leaves a run 20 minutes before the 23:30 window end; a late `run_now` answer remains evidence but cannot place. | `orchestration/tests/test_scheduled_dispatch_polling.py::test_late_run_now_is_recorded_but_never_placed`; `orchestration/tests/test_scheduled_dispatch_once.py::test_the_last_placing_fire_is_the_2310_tick`; `orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not`; `tests/test_dispatch_fire_lines.py::test_a_run_placed_at_the_last_fire_ends_before_the_window` | 🟩 |
 | DSP-TRG-02 | Calendar skip is evaluated before readiness, polling, notices, or hold writes. | `orchestration/tests/test_scheduled_dispatch.py::test_weekend_and_holiday_skip_with_stated_reason`; `orchestration/tests/test_scheduled_dispatch_readiness.py::test_calendar_skip_writes_no_hold_when_fleet_is_failing`; `orchestration/tests/test_scheduled_dispatch_polling.py::test_c15_calendar_skip_stays_silent_when_the_fleet_is_failing`; `orchestration/tests/test_daily_brief_boundaries.py::test_a5_no_brief_for_a_skipped_or_a_never_placed_run` | 🟩 |
 | DSP-TRG-03 | Every fire whose `as_of` is its own UTC date attempts that day's brief after the calendar skip and before the action-window return (so fires after `_ACT_BY` too); a past-session fire briefs nothing; it sends once the `Snapshot` exists; on the 23:50 UTC last fire a placed run with no `Snapshot` gets one RED brief; a skipped run or a held run with no `RunRequest` gets none. | `orchestration/tests/test_daily_brief_dispatch.py::test_a3_nothing_before_the_snapshot_then_red_on_the_last_fire`; `orchestration/tests/test_daily_brief_boundaries.py::test_a4_the_brief_survives_the_windows_early_return`; `orchestration/tests/test_daily_brief_boundaries.py::test_a5_no_brief_for_a_skipped_or_a_never_placed_run`; `orchestration/tests/test_daily_brief_boundaries.py::test_a_refire_for_a_past_session_briefs_nothing`; `orchestration/tests/test_daily_brief_facts_edges.py::test_a_red_brief_names_the_stage_and_what_the_run_ordered` | 🟩 |
 | DSP-OUT-01 | Normal placement writes one day-keyed `RunRequest` with tickers and no degraded-posture properties. | `orchestration/tests/test_scheduled_dispatch.py::test_trading_day_places_day_keyed_run_request`; `orchestration/tests/test_scheduled_dispatch_degraded_readiness.py::test_passing_check_places_normal_run_without_posture_property` | 🟩 |
@@ -26,20 +26,20 @@
 | DSP-STA-01 | `RunHold` evidence is append-only: recovery adds `released_at`, and re-hold creates a new key. | `orchestration/tests/test_scheduled_dispatch_readiness.py::test_recovery_releases_hold_and_places_run`; `orchestration/tests/test_scheduled_dispatch_notices.py::test_c5_rehold_after_release_gets_its_own_notice` | 🟩 |
 | DSP-STA-02 | Telegram failures are contained as graph faults and do not crash scheduled dispatch. | `orchestration/tests/test_scheduled_dispatch_polling.py::test_c12_telegram_outage_records_a_fault_without_stopping_dispatch`; `orchestration/tests/test_daily_brief_dispatch.py::test_a6_a_failed_send_changes_nothing_else_and_the_next_fire_retries`; `orchestration/tests/test_telegram_brief.py::test_send_brief_failures_are_values_that_keep_the_transport_error`; `orchestration/tests/test_telegram_brief.py::test_a_refused_brief_leaves_the_ports_error_word_and_never_its_text` | 🟩 |
 | DSP-IDM-01 | Scheduled run id is deterministic from the session date. | `orchestration/tests/test_scheduled_dispatch.py::test_scheduled_run_id_is_stable` | 🟩 |
-| DSP-IDM-02 | Same-day re-fires merge to one `RunRequest` or one active `RunHold`. | `orchestration/tests/test_scheduled_dispatch.py::test_double_fire_merges_to_one_run_request_node`; `orchestration/tests/test_scheduled_dispatch_readiness.py::test_failing_refire_merges_one_hold` | 🟩 |
+| DSP-IDM-02 | Same-day re-fires write nothing once the day's `RunRequest` exists, and merge to one active `RunHold` until it does. | `orchestration/tests/test_scheduled_dispatch.py::test_double_fire_merges_to_one_run_request_node`; `orchestration/tests/test_scheduled_dispatch_readiness.py::test_failing_refire_merges_one_hold`; `orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so`; `orchestration/tests/test_scheduled_dispatch_once.py::test_an_override_placed_run_is_already_placed_at_the_next_fire` | 🟩 |
 | DSP-IDM-03 | At most one brief per run id: a fire sends only while the `RunRequest` carries no `brief_sent_at`; a successful send writes `brief_sent_at`, `brief_message_id` and `brief_verdict` (`NOT_FINISHED` for RED) on it; a failed send writes nothing, so a later fire retries. | `orchestration/tests/test_daily_brief_dispatch.py::test_a1_a_finished_run_gets_its_brief`; `orchestration/tests/test_daily_brief_dispatch.py::test_a2_a_second_fire_sends_nothing`; `orchestration/tests/test_daily_brief_dispatch.py::test_a3_nothing_before_the_snapshot_then_red_on_the_last_fire`; `orchestration/tests/test_daily_brief_dispatch.py::test_a6_a_failed_send_changes_nothing_else_and_the_next_fire_retries`; `tests/test_brief_preview.py::test_a13_the_preview_prints_the_brief_and_sends_and_writes_nothing` | 🟩 |
 | DSP-ORD-01 | Latest valid `FleetPreflight` wins over older, malformed, or non-string facts. | `orchestration/tests/test_scheduled_dispatch_readiness.py::test_latest_preflight_wins_over_an_older_failure`; `orchestration/tests/test_scheduled_dispatch_readiness.py::test_invalid_or_out_of_order_preflight_facts_do_not_displace_latest` | 🟩 |
 | DSP-ORD-02 | First effective answer wins; later answers remain visible and replayed updates do not duplicate evidence. | `orchestration/tests/test_scheduled_dispatch_polling.py::test_c8_same_telegram_update_is_written_once`; `orchestration/tests/test_scheduled_dispatch_polling.py::test_c9_first_answer_wins_when_later_answer_disagrees` | 🟩 |
 | DSP-FAIL-01 | Telegram-port exceptions or protocol errors become faults and fallbacks. | `orchestration/tests/test_scheduled_dispatch_polling.py::test_c12_telegram_outage_records_a_fault_without_stopping_dispatch`; `orchestration/tests/test_scheduled_dispatch_human_edges.py::test_fault_safe_records_port_reported_error`; `orchestration/tests/test_telegram_brief.py::test_send_brief_failures_are_values_that_keep_the_transport_error` | 🟩 |
 | DSP-FAIL-02 | Empty configured universe fails loudly rather than placing an empty `RunRequest`. | `orchestration/tests/test_scheduled_dispatch.py::test_empty_configured_universe_is_an_error`; `orchestration/tests/test_scheduled_dispatch_human_edges.py::test_place_override_rejects_empty_universe` | 🟩 |
 | DSP-FAIL-03 | Composing or sending a brief can fail only into a fault: an exception, a send the port reports failed, or a brief module the image lacks becomes one `Fault` and the fire goes on; a brief never changes the placement outcome and never crashes the fire. | `orchestration/tests/test_daily_brief_dispatch.py::test_a6_a_failed_send_changes_nothing_else_and_the_next_fire_retries`; `orchestration/tests/test_daily_brief_boundaries.py::test_a7_a_malformed_snapshot_is_a_fault_and_nothing_else`; `orchestration/tests/test_daily_brief_boundaries.py::test_a_missing_brief_module_is_a_fault_and_the_fire_places`; `orchestration/tests/test_daily_brief_boundaries.py::test_a_fault_the_graph_refuses_still_never_stops_the_fire`; `orchestration/tests/test_daily_brief_facts_edges.py::test_unreadable_facts_are_named_data_errors_not_guesses` | 🟩 |
-| DSP-TYP-01 | `ScheduledDispatchResult` action space is `placed`, `skipped`, or `held`, with readiness details only when relevant. | _tbd_ | ⬜ |
+| DSP-TYP-01 | `ScheduledDispatchResult` action space is `placed`, `already-placed`, `skipped`, or `held`, with readiness details only when relevant. | `tests/test_dispatch_fire_lines.py::test_the_result_names_one_of_four_actions_and_readiness_only_when_held` | 🟩 |
 | DSP-SEC-01 | Telegram credentials remain inside the injected Telegram port and are never logged or returned by scheduled-dispatch logic. | `tests/test_dispatcher_credential.py::test_the_bot_credential_never_leaves_the_port_on_any_path`; `orchestration/tests/test_container_vocabulary.py::test_a28_send_alarm_posts_only_chat_and_plain_text` | 🟩 |
 | DSP-SEC-02 | P&L amounts leave the dispatcher only in the daily brief, only to the configured operator chat, and only through the injected Telegram port (DL-230); the job's printed output and every fault carry no amount, a brief's fault naming its step and an error type, never a value. | `tests/test_dispatch_brief_script.py::test_a10_no_amount_leaves_through_the_job_log_or_a_fault`; `orchestration/tests/test_daily_brief_dispatch.py::test_a6_a_failed_send_changes_nothing_else_and_the_next_fire_retries`; `orchestration/tests/test_daily_brief_boundaries.py::test_a7_a_malformed_snapshot_is_a_fault_and_nothing_else`; `orchestration/tests/test_telegram_brief.py::test_send_brief_posts_plain_text_to_the_configured_chat_only`; `orchestration/tests/test_telegram_brief.py::test_a_refused_brief_leaves_the_ports_error_word_and_never_its_text`; `tests/test_dispatcher_credential.py::test_the_bot_credential_never_leaves_the_port_on_any_path` | 🟩 |
 | DSP-DEP-01 | The scheduled dispatcher depends on graph, UTC clock, provider calendar, universe source and Telegram for optional notices, answers and brief. Brief reads include its run chain to Snapshot, Fill, Fault and Flag with resolutions, master-owned AgentInstance records of the last 24 hours, and pack acceptance. Sensor depends on managed identity and the log query API. | partial: `orchestration/tests/test_dispatcher_capability.py::test_every_fire_stays_inside_the_declared_capability` holds the graph reads, writes and Telegram operations of real fires against `CAP`; no test proves the UTC clock, provider calendar or universe-source dependencies; partial AgentInstance reads: `orchestration/tests/test_llm_brief_candidates.py::test_a22_llm_line_groups_replicas_and_filters_old_or_undated`; `orchestration/tests/test_llm_brief_candidates.py::test_a24_real_fire_carries_the_candidate_line`; clock/calendar/universe dependencies remain unproven | ⬜ |
 | DSP-OBS-01 | Holds, releases, answers, notices, degraded causes, and Telegram faults are reconstructable from graph facts and returned results. | `orchestration/tests/test_scheduled_dispatch_notices.py::test_c2_new_hold_sends_one_notice_and_marks_the_hold`; `orchestration/tests/test_scheduled_dispatch_notices.py::test_c6_run_now_places_despite_a_failing_preflight`; `orchestration/tests/test_scheduled_dispatch_degraded_notices.py::test_degraded_run_sends_one_informational_notice_and_no_hold`; `orchestration/tests/test_scheduled_dispatch_polling.py::test_c12_telegram_outage_records_a_fault_without_stopping_dispatch` | 🟩 |
 | DSP-OBS-02 | Human notice deadlines name Melbourne time first and include UTC fallback. | `orchestration/tests/test_act_by_local_time.py::test_act_by_reads_melbourne_first_and_follows_daylight_saving`; `orchestration/tests/test_act_by_local_time.py::test_act_by_falls_back_to_utc_without_usable_zone_data`; `orchestration/tests/test_act_by_local_time.py::test_a_new_hold_notice_carries_the_local_deadline` | 🟩 |
-| DSP-PERF-01 | Human override placement is bounded to the 22:30-23:20 UTC action window. | `orchestration/tests/test_scheduled_dispatch_polling.py::test_late_run_now_is_recorded_but_never_placed`; `orchestration/tests/test_daily_brief_boundaries.py::test_a4_the_brief_survives_the_windows_early_return` | 🟩 |
+| DSP-PERF-01 | Human override placement is bounded to the 22:30-23:10 UTC action window. | `orchestration/tests/test_scheduled_dispatch_polling.py::test_late_run_now_is_recorded_but_never_placed`; `orchestration/tests/test_scheduled_dispatch_once.py::test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not`; `orchestration/tests/test_daily_brief_boundaries.py::test_a4_the_brief_survives_the_windows_early_return` | 🟩 |
 | DSP-IDN-05 | The scheduled dispatcher runs the container sensor (`orchestration/container_*.py`, DL-301): on each fire it reads the platform's container events from the log workspace, records the ones it keeps and tells the operator of each alarm once. It reports and never decides: no sensor read changes a placement, a hold, a notice, the brief's other lines, or any container. | `tests/test_container_sensor_script.py::test_every_outcome_keeps_dispatch_order_and_status`; `orchestration/tests/test_container_brief.py::test_a23_real_brief_facts_include_the_sensor_line` | 🟩 |
 | DSP-IN-05 | The sensor's input is the rows of the workspace's `ContainerAppSystemLogs_CL` that reached it inside the read window, read by their ingestion time, and for an alarm's why the stderr lines of `ContainerAppConsoleLogs_CL` of the same replica, or, for a failure of the platform itself, the row's own reason and message. A row is an alarm (a failed start or a failed scale-up, a revision that failed to provision, a scale rule the scaler refused, a memory kill, an exit with code 137, any other exit whose code is not 0 or cannot be read, a revision update the platform failed, the platform's autoscaler failing to read or update a scale unless it found the revision gone, any other row the platform marks `error`, and any other row it marks `Warning` except the five each deploy and each wake leave behind: a replica waiting for its node, a probe refused while a replica starts or stops, a scale object checked or removed with its revision, and a completed container), a report (a preemption, or a node scale-down that moved a replica), or nothing; an exit with code 0 is nothing. The app is the row's app or job name, else its revision's name less the revision suffix, else `unknown`. | `orchestration/tests/test_container_events.py::test_a1_measured_kinds`; `orchestration/tests/test_container_events.py::test_a2_noise_and_clean_exit_are_nothing`; `orchestration/tests/test_container_events.py::test_a3_unknown_error_and_unreadable_exit`; `orchestration/tests/test_container_events.py::test_a4_app_precedence_and_unknown`; `orchestration/tests/test_container_events.py::test_a7_query_matches_classifier_and_ingestion_window`; `orchestration/tests/test_container_lines.py::test_a8_traceback_order_and_shape_precedence`; `orchestration/tests/test_container_lines.py::test_a9_console_window`; `orchestration/tests/test_container_telling.py::test_a20_replica_line_reaches_graph_and_message`; `orchestration/tests/test_container_platform.py::test_a31_platform_failures_alarm`; `orchestration/tests/test_container_platform.py::test_a32_revision_gone_is_nothing`; `orchestration/tests/test_container_platform.py::test_a33_measured_warnings_are_nothing`; `orchestration/tests/test_container_platform.py::test_a34_unknown_warning_alarms_and_unmarked_unknown_does_not`; `orchestration/tests/test_container_platform.py::test_a35_query_asks_for_unknown_warnings_not_measured_ones`; `orchestration/tests/test_container_platform.py::test_a36_platform_why_is_its_own_words` | 🟩 |
 | DSP-TRG-04 | Every fire runs the sensor once, after its dispatch, whatever the dispatch's outcome: placed, skipped, held, or failed. With no `LOG_ANALYTICS_WORKSPACE_ID` in the job's environment the sensor does nothing and the fire's output is unchanged. A read ends at the fire's time and starts `container_sensor_overlap_minutes` before the previous successful read ended; the first read starts `container_sensor_first_read_hours` back, and no read starts further back than `container_sensor_max_lookback_hours`. | `orchestration/tests/test_container_sensor.py::test_a14_first_read_then_overlapping_fire`; `orchestration/tests/test_container_sensor.py::test_a15_long_gap_caps_window_and_message`; `orchestration/tests/test_container_env.py::test_a25_unconfigured_sensor_builds_nothing`; `tests/test_container_sensor_script.py::test_every_outcome_keeps_dispatch_order_and_status` | 🟩 |
@@ -51,3 +51,5 @@
 | DSP-SEC-03 | The sensor reads as the job's system-assigned managed identity, which holds the role Log Analytics Reader on the one log workspace and nothing else; no credential for it is stored anywhere. A console line leaves only with credentials in a URL, named secrets, bearer tokens, runs of 32 or more token characters and amounts masked, and cut to 160 characters. A printed line, a fault and a read record name a failure by its error type and a status word, never a reply body, a query or a token. Only a replica name that matches the platform's naming rule is put into a query. | `orchestration/tests/test_container_lines.py::test_a10_credentials_and_amounts_are_masked`; `orchestration/tests/test_container_reader.py::test_a11_one_identity_get_then_workspace_posts`; `orchestration/tests/test_container_reader.py::test_a12_http_status_never_includes_reason_or_body`; `orchestration/tests/test_container_queries.py::test_a13_hostile_replica_is_never_sent`; `tests/test_container_sensor_deploy.py::test_a30_sensor_identity_role_and_workspace_are_exact` | 🟩 |
 | DSP-OBS-03 | Each sensor run prints one line: the rows read, the new events, the alarms and how many were told, or the failure. Every alarm and report the sensor kept, and every read, is reconstructable from `ContainerEvent` and `ContainerSensorRead` facts and their `TOLD` edges. | `orchestration/tests/test_container_sensor.py::test_a16_records_every_kept_row_and_tells_seven_alarms`; `orchestration/tests/test_container_vocabulary.py::test_a27_pack_accepts_events_reads_edges_and_failures`; `orchestration/tests/test_container_env.py::test_a25_configured_reader_and_a24_close`; `tests/test_container_sensor_script.py::test_a26_weekend_skip_then_sensor_or_safe_failure` | 🟩 |
 | DSP-OUT-09 | A recent activation with another candidate passed over, or the runs DeliberationRun naming switches, adds one LLM line after containers and before needs-you. Sorted agent types are grouped by distinct choice/passed-over list with chosen vendor/model/effort and reasons; then each run switch followed by during the run. Parts join with the middle-dot separator; neither fact means no line. | `orchestration/tests/test_llm_brief_candidates.py::test_a21_quiet_night_has_no_llm_line`; `test_a22_llm_line_groups_replicas_and_filters_old_or_undated`; `test_a23_llm_line_follows_container_before_needs_you`; `test_a24_real_fire_carries_the_candidate_line`; `orchestration/tests/test_llm_brief_switches.py::test_a19_brief_names_each_switch_in_run_order`; `orchestration/tests/test_llm_brief_switches.py::test_a20_activation_parts_precede_run_switches`; `orchestration/tests/test_llm_brief_switches.py::test_a21_no_switch_means_no_line`; `orchestration/tests/test_llm_brief_switches.py::test_a22_real_fire_carries_the_runs_switch` | 🟩 |
+| DSP-NEV-04 | The dispatcher never holds a run whose day-keyed `RunRequest` exists: a later fire reads no readiness, writes no `RunHold` and sends no hold notice; it reports `already-placed` and, inside the action window, retries only an unsent degraded notice. | `orchestration/tests/test_scheduled_dispatch_once.py::test_a_placed_run_is_never_held_when_a_later_check_fails`; `orchestration/tests/test_scheduled_dispatch_once.py::test_an_override_placed_run_is_already_placed_at_the_next_fire`; `orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only`; `orchestration/tests/test_scheduled_dispatch_notices.py::test_c5_rehold_after_release_gets_its_own_notice` | 🟩 |
+| DSP-OBS-04 | Each fire prints one line naming what it did and why: `placed` with the calendar's reason, `already-placed` on every later fire, `held` with the readiness state or that the action window has passed, `skipped` with the calendar's reason, the operator, or which side of the action window the fire is on. | `tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did`; `tests/test_dispatch_fire_lines.py::test_a_skip_answer_still_says_operator`; `orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so` | 🟩 |
diff --git a/orchestration/tests/test_act_by_local_time.py b/orchestration/tests/test_act_by_local_time.py
index d0ca2fd7..6466c266 100644
--- a/orchestration/tests/test_act_by_local_time.py
+++ b/orchestration/tests/test_act_by_local_time.py
@@ -23,16 +23,16 @@ def test_act_by_reads_melbourne_first_and_follows_daylight_saving() -> None:
     standard = datetime(2026, 9, 24, 22, 30, tzinfo=UTC)
     daylight = datetime(2026, 10, 5, 22, 30, tzinfo=UTC)

-    assert act_by_text(standard, "Australia/Melbourne") == "09:20 Melbourne (23:20 UTC)"
-    assert act_by_text(daylight, "Australia/Melbourne") == "10:20 Melbourne (23:20 UTC)"
+    assert act_by_text(standard, "Australia/Melbourne") == "09:10 Melbourne (23:10 UTC)"
+    assert act_by_text(daylight, "Australia/Melbourne") == "10:10 Melbourne (23:10 UTC)"


 def test_act_by_falls_back_to_utc_without_usable_zone_data() -> None:
     """DSP-OBS-02: invalid zone data keeps a correct UTC fallback."""
     now = datetime(2026, 9, 24, 22, 30, tzinfo=UTC)

-    assert act_by_text(now, "Nowhere/Atlantis") == "23:20 UTC"
-    assert act_by_text(now, "../etc") == "23:20 UTC"
+    assert act_by_text(now, "Nowhere/Atlantis") == "23:10 UTC"
+    assert act_by_text(now, "../etc") == "23:10 UTC"


 def test_a_new_hold_notice_carries_the_local_deadline() -> None:
@@ -43,4 +43,4 @@ def test_a_new_hold_notice_carries_the_local_deadline() -> None:

     dispatch(graph, telegram)

-    assert telegram.sent[0]["act_by"] == "09:20 Melbourne (23:20 UTC)"
+    assert telegram.sent[0]["act_by"] == "09:10 Melbourne (23:10 UTC)"
diff --git a/orchestration/tests/test_daily_brief_boundaries.py b/orchestration/tests/test_daily_brief_boundaries.py
index c6936fd4..8faf8d47 100644
--- a/orchestration/tests/test_daily_brief_boundaries.py
+++ b/orchestration/tests/test_daily_brief_boundaries.py
@@ -58,7 +58,7 @@ def test_a4_the_brief_survives_the_windows_early_return() -> None:
     after = {key: dict(node.props) for key, node in graph._nodes.items()}
     assert len(telegram.briefs) == 1
     assert result == fire(no_brief, FakeTelegram(), at(23, 30))
-    assert result.action == "skipped"
+    assert result.action == "already-placed"
     changed = {key for key in after if after[key] != before.get(key)}
     assert changed == {("RunRequest", "run-request:sched-2026-09-25")}
     added = (
@@ -130,7 +130,7 @@ def test_a_missing_brief_module_is_a_fault_and_the_fire_places(

     result = fire(graph, FakeTelegram(), at(22, 50))

-    assert result.action == "placed"
+    assert result.action == "already-placed"
     (fault,) = graph.list_nodes("Fault")
     assert fault.props["message"] == (
         "daily brief not sent for sched-2026-09-25: brief failed (ModuleNotFoundError)"
@@ -163,7 +163,7 @@ def test_a_fault_the_graph_refuses_still_never_stops_the_fire(

     result = fire(graph, FakeTelegram(brief_raises=True), at(22, 50))

-    assert result.action == "placed"
+    assert result.action == "already-placed"
     err = capsys.readouterr().err
     assert err == "error daily brief fault not recorded: OSError\n"
     assert amount_free(err)
diff --git a/orchestration/tests/test_scheduled_dispatch_degraded_notices.py b/orchestration/tests/test_scheduled_dispatch_degraded_notices.py
index 4b0f9c92..46353811 100644
--- a/orchestration/tests/test_scheduled_dispatch_degraded_notices.py
+++ b/orchestration/tests/test_scheduled_dispatch_degraded_notices.py
@@ -34,7 +34,7 @@ def test_degraded_run_sends_one_informational_notice_and_no_hold() -> None:
     first = dispatch(graph, telegram)
     second = dispatch(graph, telegram)

-    assert (first.action, second.action) == ("placed", "placed")
+    assert (first.action, second.action) == ("placed", "already-placed")
     assert telegram.sent == []
     assert len(telegram.degraded_sent) == 1
     assert telegram.degraded_sent[0] == {
diff --git a/orchestration/tests/test_scheduled_dispatch_notices.py b/orchestration/tests/test_scheduled_dispatch_notices.py
index db5cf7e8..ae33b237 100644
--- a/orchestration/tests/test_scheduled_dispatch_notices.py
+++ b/orchestration/tests/test_scheduled_dispatch_notices.py
@@ -10,9 +10,13 @@ from __future__ import annotations
 from datetime import timedelta
 from importlib import import_module

+import pytest
+
+from agents.scanner.universe import FakeUniverse
 from contracts.provider import RUN_REQUEST_LABEL
 from kernel import InMemoryGraphStore
 from orchestration.tests.scheduled_dispatch_human_helpers import (
+    AS_OF,
     NOW,
     FakeAnswer,
     FakeTelegram,
@@ -107,13 +111,25 @@ def test_c4_second_fire_on_one_hold_sends_no_second_notice() -> None:


 def test_c5_rehold_after_release_gets_its_own_notice() -> None:
-    """DSP-STA-01: a released hold is untouched and a new hold is announced."""
+    """DSP-STA-01: a released hold is untouched and a new hold is announced.
+
+    The release places nothing (an empty universe): a placed run is never held
+    again (DSP-NEV-04).
+    """
     graph = InMemoryGraphStore()
     telegram = FakeTelegram()
     preflight(graph, passed=False)
     dispatch(graph, telegram)
     preflight(graph, passed=True, checked_at=NOW - timedelta(minutes=4))
-    dispatch(graph, telegram)
+    controller = import_module("orchestration.scheduled_dispatch_human")
+    with pytest.raises(ValueError, match="no tickers"):
+        controller.dispatch_with_human_answer(
+            graph,
+            as_of=AS_OF,
+            now=NOW,
+            telegram=telegram,
+            universe_source=FakeUniverse({"sp500": ()}),
+        )
     preflight(graph, passed=False, checked_at=NOW - timedelta(minutes=3))

     dispatch(graph, telegram)
diff --git a/tests/test_dispatch_brief_script.py b/tests/test_dispatch_brief_script.py
index 80e2079a..10548da0 100644
--- a/tests/test_dispatch_brief_script.py
+++ b/tests/test_dispatch_brief_script.py
@@ -26,7 +26,7 @@ from orchestration.tests.daily_brief_scenarios import (
 from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram

 # 23:30 is past the action window: the job places nothing, and the brief still goes.
-_PRINTED = "skipped sched-2026-09-25 reason=NYSE trading session\n"
+_PRINTED = "already-placed sched-2026-09-25 reason=placed by an earlier fire\n"


 class _Clock(datetime):
diff --git a/tests/test_master_wake_window.py b/tests/test_master_wake_window.py
index 55e712e4..e47e24b8 100644
--- a/tests/test_master_wake_window.py
+++ b/tests/test_master_wake_window.py
@@ -49,7 +49,7 @@ def test_the_check_made_at_the_wake_is_fresh_at_the_first_placing_tick() -> None


 def test_every_placing_tick_finds_a_fresh_check() -> None:
-    """DSP-IN-03 / DSP-TRG-01: all six placing ticks find readable, fresh checks."""
+    """DSP-IN-03 / DSP-TRG-01: all five placing ticks find readable, fresh checks."""
     limit = OrchestratorSettings(_env_file=None).preflight_max_age_minutes
     interval = MasterSettings(_env_file=None).fleet_preflight_interval_minutes
     wake = _wake()
@@ -62,7 +62,7 @@ def test_every_placing_tick_finds_a_fresh_check() -> None:
         ticks.append(tick)
         tick += timedelta(minutes=10)  # The pack's */10 dispatcher cron.

-    assert len(ticks) == 6
+    assert len(ticks) == 5
     for tick in ticks:
         newest = max(check for check in checks if check <= tick)
         assert tick - newest <= timedelta(minutes=limit)
```
