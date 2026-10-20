<!-- Agent: planning | Role: sprint handover -->
# Sprint 285 — The dispatcher keeps the deadline it tells, and places the day's run once

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-285-the-dispatcher-keeps-the-deadline-it-tells`
**Status:** MERGED
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

- [x] On the built tree, `wq131_probe.py` (planner's F1) prints exactly the prototype's output (`f1_proto.txt`): one `placed`, then `already-placed`, and no hold on the night a later check fails. *(Planner, 2026-10-21: byte for byte, sha256 `de2c8bbaf88bcf29`.)*
- [x] `place_scheduled_run`, the brief, the sensor, `contracts/` and every agent unchanged; no existing test changed beyond Appendix section 2's six files.
- [x] Design decisions recorded with rejected alternatives: DL-309, already on `main`.
- [x] Law cycle done as Appendix section 2: `DSP-NEV-04`, `DSP-OBS-04` and `DSP-TYP-01` 🟩, rollup 46 / 49 in both rollups.
- [x] B1 to B17 each planted, watched to fail against your tests alone, restored — stated per break.
- [x] Every touched module < 200 lines, test files included.
- [x] `make ci` exit 0, 100.00 % coverage. *(Planner, 2026-10-21: the builder's offline run was red only at the dependency audit; the remote CI on `f01edfc6` ran all 16 steps green, GATE PROVEN.)*

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
[planner, 2026-10-21: 2373 of the builder's 2396 pasted lines removed here, the step lines and verdicts kept; the whole output is in the kit, `s285_builder_make_ci.txt`]
uv run ruff check . --output-format=github
uv run ruff format --check .
1798 files already formatted
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 1274 source files
uv run lint-imports
Contracts: 5 kept, 0 broken.
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
uv run python scripts/check_tracker_size.py
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
TOTAL                                                           21578      0   4618      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 5242 passed, 9 skipped, 2470 warnings in 636.05s (0:10:36) ==========
uv run python scripts/check_dependency_audit.py
dependency audit failed: WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
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

### The planner's review and merge (2026-10-21)

Kit and outputs in OneDrive `trading-agents-data/wq131bd-2026-10-20/`.

- **Scope:** the 21 changed files are the spec's: the four production files, the five law and
  deployment documents, Appendix section 2's six existing tests, the two new test files,
  `pyproject.toml`, `uv.lock` (the root package's version line only), this spec and its README row;
  `place_scheduled_run` byte for byte the same; nothing under `contracts/`, `agents/`, `kernel/` or
  `infra/`.
- **Blobs:** 15 of 15 equal `prototype_blobs.txt`.
- **Breaks:** 17 of 17 red against the builder's two test files alone, tree clean after, each count
  the builder's (`s285_breaks_on_built_codex_tests_f01edfc6.txt`).
- **The planner's tests on the built tree** (swapped in at the same paths, then restored): 18 passed
  (`s285_planner_tests_on_built_f01edfc6.txt`). The builder's read 19 cases because A4's two
  scenarios are separate cases (return notes); accepted.
- **CodeQL** set-diff against the S284 branch by rule and path: 0 errors either side, 134 → 135 open.
  The one new alert is a warning, `py/implicit-string-concatenation-in-list` at
  `tests/test_dispatch_fire_lines.py:46-47` (alert 308): one expected line split for length, as meant.
  The same pattern is already open on `main` (alert 241, `surfaces/tests/test_dashboard_readiness.py`).
  Accepted; parenthesizing both strings closes both (`codeql_sprint-284-….tsv`, `codeql_sprint-285-….tsv`).
- **F1 passed** (`wq131_probe.py` from the built tree, in memory, no cost): the output equals
  `f1_proto.txt` byte for byte (sha256 `de2c8bbaf88bcf29`). Against `main`'s (`1eb449f88f995e44`): the
  three fires before 22:30 say `before the placing window`; the night places once and the eight later
  fires say `already-placed`; on the night whose 23:01 check fails the run stays placed, with no
  `RunHold` and no hold notice, where `main` held it and sent a notice naming 23:20
  (`f1_main_e82f9d88.txt`, `f1_built_f01edfc6.txt`).
- **`make gate-ran`** from `../ta-s285`: GATE PROVEN for `f01edfc6` (CI, which ran the dependency
  audit the builder could not reach, CodeQL, Security Findings; `s285-gate-ran-branch-f01edfc6.txt`).
- **Deploy check:** `git diff v0.128.06..v0.128.07` touches no `DECISION_PATHS` entry and nothing
  under `kernel/`, `agents/`, `contracts/`, `infra/` or a Dockerfile: an image-only retag, and the
  fidelity count holds.
- **The builder's pasted `make ci` output** (2396 lines) is trimmed above to its step lines
  and verdicts; the whole of it is in the kit (`s285_builder_make_ci.txt`, the break logs in
  `s285_builder_tools/`).
- **Merged:** `main` fast-forwarded `d7b728aa` → `f01edfc6`; tag `v0.128.07`. **Deployed as `s285`**
  2026-10-21 on the operator's word (*"deploy if you need to"*), an image-only retag, rollback `s284`
  (OneDrive `trading-agents-data/deploy-s285-2026-10-21/`): every injected pack on the 17 targets (vocabulary `aed6e10c…`, the master's credential and LLM packs, the PM's issuer map) equal to the repo at `f01edfc6` before and after; build `39430313878` from `v0.128.07`, 15 of 15 images; retag 00:27 to 00:33 AEDT, 17 of 17 `Succeeded`; `compare_snapshots.py`: only the image changed on every app and the job (KEDA rules, replicas, env intact); `DeployRecord s285:f01edfc6`; read at the retag: 15 of 15 agent types activated, 3 fleet checks passed, 0 faults, escalations or flags, no LLM call; the CVS 10 buy
  filled at the 10-20 open during the retag (93.685), no buy order open. **F2 owed on
  `sched-2026-10-20`:** the job's twelve lines read 3 `skipped … before the placing window`, 1 `placed`, 8 `already-placed`;
  8 / 8; no fault. Then close parts (b) and (d) of work-queue 131.

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
