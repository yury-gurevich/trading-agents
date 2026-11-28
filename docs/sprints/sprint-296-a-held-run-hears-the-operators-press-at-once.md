<!-- Agent: planning | Role: sprint handover -->
# Sprint 296 — a held run hears the operator's press at once

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-296-a-held-run-hears-the-operators-press-at-once`
**Status:** SPEC
**Version:** *next available PATCH at merge* (the prototype measured `0.133.01`)
**Effort:** M
**Decisions:** [DL-332](../design-log.md) (this sprint's nine decisions, made and measured) · [DL-331](../design-log.md) (the constraint it fixes, measured live) · [work-queue 146](../work-queue.md)

> **Why this bump kind.** A fix: the one place the fleet asks the operator loses most of their
> answers at the fleet's own cadence (DL-331). No new capability; a PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `orchestration/laws/dispatcher/laws.md` | The dispatcher's **locked constitution** (`DSP`, v1.8): holds, answers, notices | **This sprint is its law cycle to v1.9**, written in full in Appendix B: two new clauses, three amended. Apply it; do not write your own |
| `orchestration/laws/dispatcher/test-plan.md` | Which `DSP` clauses are proven, by which tests | Appendix B adds two rows and amends one; they name **your** tests, so the names in the Test plan are binding |
| `docs/laws/ledger.md`, `docs/laws/INDEX.md` | The rollups (`47 / 50`) | Appendix B moves both to `49 / 52` |
| `docs/laws/conventions.md` | Module headers, test docstrings, clause citations | Binds every new file and every test docstring |
| `docs/laws/drift-register.md` | Where a law found wrong or silent is recorded | The one law-adjacent file you may append to; this sprint expects no row |

Binding, unchanged: **`DSP-IN-04`** (only `run_now` or `skip_today` for the matching run decides),
**`DSP-TRG-01`** (a run is placed only from the 22:30 tick to the 23:10 tick), **`DSP-ORD-02`** (the
first answer decides), **`DSP-STA-02`** and **`DSP-FAIL-01`** (a Telegram failure is a fault, never a
crash), **`DSP-SEC-01`** (the token lives in the port), **`DSP-TRG-04`** (the sensor runs once after
the dispatch). New: **`DSP-TRG-05`** (the listening) and **`DSP-PERF-02`** (a press acknowledged within
seconds). Amended: **`DSP-STA-02`** (wait failures), **`DSP-OBS-04`** (the second line) and `CAP`
(`wait_answer`).

### The rule

1. **Before writing code**, read `orchestration/laws/dispatcher/laws.md` and its `test-plan.md`,
   [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md), whole.
2. Read [DL-331](../design-log.md) and [DL-332](../design-log.md), whole.
3. **Answer the law-cycle question below** in the Law reading record.
4. **Write the Law reading record** (bottom of this file) **before** your first change.
5. **If a law contradicts this spec, STOP and report.**
6. Every new or rewritten test's docstring cites what it proves: the `DSP` clause IDs the Test plan
   gives, or the DL-330 / DL-332 decision where it gives no clause. A test the test-plan rows name
   **must** cite that row's clause (the law-coverage step checks it).

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**Yes, a guarantee.** No file in `contracts/`, `kernel/` or `agents/` changes. The dispatcher gains a
promise it did not make: a fire that leaves its run held stays on the operator's bot and answers a
press within seconds (`DSP-TRG-05`, `DSP-PERF-02`). The full cycle (law text, changelog, test-plan
rows, both rollups) is written in Appendix B; your tests are the proof the new rows cite.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/hold_listener.py` (new) | `orchestration/laws/dispatcher/laws.md` + `test-plan.md` | `DSP-TRG-05`, `DSP-PERF-02`; it calls `poll_answers` and `dispatch_with_human_answer` unchanged (`DSP-IN-04`, `DSP-TRG-01`, `DSP-ORD-02`, `DSP-STA-02`) |
| `orchestration/telegram_client.py`, `telegram_port.py`, `telegram_updates.py` | the same | `DSP-SEC-01` (the token stays in the port); `CAP` (`wait_answer`) |
| `orchestration/scheduled_dispatch_actions.py` | the same | `DSP-TRG-01`: two helpers, `next_tick` and `may_act`, beside `fire_tick` and `is_action_time` |
| `scripts/dispatch_scheduled_run.py`, `orchestration/Dockerfile` | the same | `DSP-OBS-04` (the second line), `DSP-TRG-04` (the sensor still runs once, after) |
| `orchestration/hold_drill.py`, `hold_drill_verdict.py`, `scripts/run_hold_drill.py` | DL-330; DL-332 D7 | The drill listens as the fleet does |
| the laws, test plan and rollups | `docs/laws/conventions.md` | Appendix B's text, applied as given |
| seven test files | `docs/laws/conventions.md`; the Test plan | Names, docstrings, clause citations |

⚠️ **One invariant.** `orchestration/scheduled_dispatch_human.py`, `scheduled_dispatch_polling.py`,
`hold_answers.py` and `scheduled_dispatch.py` do not change: the listener calls them as they are. If
your change would edit any of them, stop and report.

---

## Goal

A fire that leaves today's run held stays on the operator's Telegram bot until 30 seconds before the
next fire. When the operator presses *Run now* or *Skip today*, the press is recorded, acknowledged
(*Answer recorded* appears on the phone) and acted on within seconds, and a *Run now* by 23:10 UTC
starts the run in that fire. The hold drill listens the same way, so its live run proves it.

---

## Why (context)

The fleet asks the operator one thing: a held run's notice with *Run now* and *Skip today*. S295's
drill ran it for real on 2026-11-28 and found it broken at the fleet's cadence (DL-331, work-queue
146): Telegram drops a press nobody reads in about 2.5 to 4 minutes and refuses an acknowledgement
about 15 seconds after the press, and the dispatcher reads answers once per ten-minute fire. So most
presses on a real hold never reach the fleet, and each one that does writes a `telegram` Fault while
the operator sees nothing.

### Measured, 2026-11-28 — read these before designing

Kit: OneDrive `trading-agents-data/wq120-2026-11-28/`. *[measured]* = run or read whole, this day.

- *[measured, live, the test bot]* **A press expires unread.** Update 806096848 was in the queue at
  09:59:08 UTC and gone at the drill's 10:02:52 poll with no call between; ids 837, 838, 841, 842 and
  847 were assigned and never delivered, each to a press that waited about three minutes or more.
  Presses fetched 20, 60 and 150 s after their message were kept (3 of 3). Every
  `answerCallbackQuery` 13 s or more after its press returned HTTP 400 `query is too old`
  (`f1b_traced.txt`, `f1b_rerun_traced.txt`, `probe_press_lifetime.txt`).
- *[measured, the test bot, nothing sent]* **A long poll waits; an overlapping poll ends the older
  one.** `getUpdates` with `timeout` 8 on an empty queue returned empty after 8.9 s; a second poll
  started 3 s into a long one made the long one return HTTP 409 (`Conflict: terminated by other
  getUpdates request`) and itself proceeded (`probe_long_poll.txt`).
- *[measured, read-only `az`]* **The job.** Cron `*/10 22-23 * * 1-5`, replica timeout 1800 s,
  parallelism 1, retry 0; its last 100 executions all `Succeeded`, each starting at its tick, 35 to
  61 s long (median 37 s).
- *[measured, read whole]* **The fire.** `dispatch_with_human_answer` polls answers once, only while a
  hold is active; `poll_answers` records, acknowledges and confirms in one pass; `is_action_time`
  floors the clock to the ten-minute tick, so a fire at 23:19 counts as the 23:10 tick.
- *[measured, read]* **The graph connection** (`kernel/graph_postgres.py`) reconnects once per
  statement on a dropped connection, so a fire that keeps it for minutes recovers on its next query.
- *[measured, the prototype]* **The image guard** `test_dispatcher_image_copies_everything_its_entrypoint_imports`
  went red until `orchestration/Dockerfile` copied the new module; **the capability guard**
  `test_every_fire_stays_inside_the_declared_capability` went red until a listening fire used the new
  `wait_answer` operation. Both are real guards; both are part of this sprint.
- *[assumed]* That a real press reaches a long poll at once. Telegram documents it; the prototype's
  tests use a fake; F1 measures it on the test bot.

---

## Scope — and what is deliberately NOT here

In: the listener (`orchestration/hold_listener.py`); a long-poll read on the Telegram client and a
port that declares it; two time helpers; the job script listening after a held fire; the dispatcher
image copying the module; the drill listening the same way (its two flags leave); the law cycle to
v1.9; PATCH `0.133.01`.

### Out of scope (do NOT build this sprint)

- **Work-queue 145** (a refused notice's Fault names the wrong cause): a separate fix.
- **Any change to the cron, the action window or the act-by time.**
- **A webhook or an every-minute cron** (ruled out, DL-332 D1).
- **The deploy.** The fleet runs this only after a dispatcher retag, the operator's word after F1.

### The road not taken (LAW-06)

- **Fire every minute while a hold is open.** Ruled out: an acknowledgement up to a minute late is
  still refused (a Fault per press stays), and it is ten times the fires and sensor reads a night.
- **A webhook on a fleet app's ingress.** Ruled out: a public endpoint and a secret, and the master
  would write answers the dispatcher owns.
- **Keep the drill's `--poll-seconds`.** Ruled out: it imitated the late polling this sprint removes.

---

## The design decisions — made, and recorded in DL-332

D1 a listener the job calls after a held fire · D2 until 30 s before the next tick, long polls of at
most 25 s, at most four waits for each one the time allows · D3 on a press: the unchanged
`poll_answers`, then the unchanged `dispatch_with_human_answer` while the time is at or before
23:10:00 UTC; after it, recorded only · D4 an update that is not an answer is confirmed after the wait
that returned it · D5 a failed wait is one Fault and ends the listening · D6 a second printed line ·
D7 the drill listens the same way; its poll flags leave · D8 the law cycle to v1.9, PATCH · D9 the
deploy is the operator's, after F1. Read DL-332 for each one's reason and what it ruled out.

---

## Blast radius — measured 2026-11-28

| What | Detail |
| --- | --- |
| Files changed | New: `orchestration/hold_listener.py` (120 lines on the prototype). Changed: `orchestration/telegram_client.py` (155), `telegram_port.py` (53), `telegram_updates.py` (65), `scheduled_dispatch_actions.py` (144), `hold_drill.py` (140), `hold_drill_verdict.py` (79), `orchestration/Dockerfile` (one line), `scripts/dispatch_scheduled_run.py` (154), `scripts/run_hold_drill.py` (81); the dispatcher's `laws.md` and `test-plan.md`; `docs/laws/ledger.md`, `docs/laws/INDEX.md`; one line each in `pyproject.toml` and `uv.lock`. Tests: three new or rewritten for the drill, two new, two amended (Test plan). This spec; `docs/sprints/README.md` |
| Agents affected | none. The dispatcher job (`orchestration`) only |
| Contract change? | no. A new `Protocol` in `orchestration/telegram_port.py` extends the existing port; every existing fake still satisfies `TelegramPort` |
| Graph vocabulary change? | no. The listener writes `RunHoldAnswer`, `RunRequest` and `Fault` through the existing functions |
| New env keys / tunables | none |
| Deploy implication | **the dispatcher image changes** (a new module, copied by its Dockerfile). The merge builds images; the fleet runs the fix only after a dispatcher retag, the operator's word after F1. Until then nothing changes live |
| Rollback | revert the commit; after a deploy, retag the dispatcher job to `s291` |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Write the seven test files of the Test plan first** and run, on the unchanged production files:
   `uv run --no-sync pytest orchestration/tests/test_hold_listener.py tests/test_hold_listener_job.py orchestration/tests/test_hold_drill.py tests/test_run_hold_drill_cli.py orchestration/tests/test_dispatcher_capability.py --no-cov -q -p no:cacheprovider`.
   Paste the output. On the planner's dry run: ****3 errors during collection****.
3. **Apply Appendix B**, exactly, and check the sixteen blob ids it gives.
4. **Run the same command again: 31 passed.**
5. **Prove the guards can fail (DL-70):** the 19 breaks of Appendix C, one at a time, each red on the
   test named for it, each restored before the next.
6. **`make ci` green**, every step of the `ci:` target (count them from the `Makefile`),
   **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Seven files, under **exactly these names**: the planner's break script and the dispatcher's
test-plan rows (Appendix B) judge by them. Each file's docstring declares `Agent:` (`orchestration`
under `orchestration/tests/`, `tooling` under `tests/`), a `Role:` and `External I/O: none` (or what
it replaces in-process). No test makes a network call, sleeps, or reads an actual `.env`. In the
tables `R1` is `sched-2026-11-27` (session `D1`, 2026-11-27), `R2` is `sched-2026-11-25` (`D2`).

**`orchestration/tests/hold_drill_fakes.py`** (rewritten; no tests of its own) keeps `TODAY`,
`SAFE_NOW`, `TEST_BOT_VALUE` and `FLEET_BOT_VALUE` as they are, adds `PRESS_LIFETIME = 180.0` and
`ACK_LIMIT = 15.0`, and provides:

- `FakeBot(*, send_ok=True, ack_ok=True, confirm_ok=True, wait_ok=True, operator=None)`, a callable
  `(method, payload, timeout)` used as `TelegramClient(..., sender=bot)`, on a fake clock `bot.now`
  (seconds, from 0) that **moves only while a long poll waits**:
  - `sendMessage` records `(text, [callback_data of each button])` in `bot.sent` and returns
    `{"ok": send_ok, "result": {"message_id": 100 + len(bot.sent)}}`; when the message carries
    buttons and `operator` maps its run id (the part after the first `:` of the first button's data)
    to `(answer, seconds)`, the operator presses that answer that many seconds later.
  - `getUpdates` first lets every press that is due arrive (as
    `{"update_id": <rising from 501>, "callback_query": {"id": "cb<update id>", "data": "<answer>:<run id>"}}`)
    and drops every press made `PRESS_LIFETIME` seconds ago or more. With an `offset`: drop the
    updates below it and return the rest (`{"ok": False, ...}` when `confirm_ok` is false). With a
    `timeout`: count it in `bot.waits` (`{"ok": False, ...}` when `wait_ok` is false); if no update
    is queued, move the clock to the next due press inside the wait, or by the whole wait, and let
    due presses arrive. Every successful call returns `{"ok": True, "result": <the queued updates>}`.
  - `answerCallbackQuery` appends the press's age (`bot.now` minus the time it was made) to
    `bot.acks`, and returns ok only when `ack_ok` and the age is at most `ACK_LIMIT`.
  - `bot.press(answer, run_id, *, after=0.0)`, `bot.text(words)` (a `{"message": {"text": words}}`
    update), `bot.elapsed()` (the clock), `bot.notices()` (the sent messages with buttons).
- `drill_on(bot, lines)` returns a `Drill` on `TelegramClient(api_token=TEST_BOT_VALUE, chat_id="42",
  sender=bot)`, `OrchestratorSettings(_env_file=None)`, `elapsed=bot.elapsed`, `report=lines.append`.

**`orchestration/tests/test_hold_listener.py`** (new, 8 cases), on the real dispatcher, the real
`TelegramClient` and a `FakeBot`. A helper plants a failing `FleetPreflight` for `D1` at 22:25 UTC
(failures `["transient:execution:alpaca-broker:TimeoutError"]`), fires `dispatch_with_human_answer`
once at a given time (asserting `held`), and returns the graph, the client and a clock that is that
time plus the bot's elapsed seconds. `SETTINGS = OrchestratorSettings(_env_file=None)`.

| # | Test | Cites | Must prove |
| --- | --- | --- | --- |
| L1 | `test_a_held_fire_listens_until_30_s_before_the_next_tick` | DSP-TRG-05 | held at 22:40:20, no press: the line is `listened 550 s: no answer`, the clock reads 22:49:30, `bot.waits == 22` |
| L2 | 🎯 `test_a_press_is_recorded_acknowledged_and_acted_on_at_once` | DSP-TRG-05, DSP-PERF-02 | held at 22:30:20, *Run now* 200 s on: `listened 200 s: answered, placed NYSE trading session`; `bot.acks == [0.0]`; one `RunHoldAnswer` answered `2026-11-27T22:33:40+00:00`; the day's `RunRequest` exists; no `Fault`; no update left |
| L3 | `test_an_answer_acts_only_by_the_act_by_time`, two cases | DSP-TRG-05, DSP-TRG-01 | held at 23:00:20, *Run now* 500 s on: `listened 500 s: answered, placed NYSE trading session`, a `RunRequest`; held at 23:10:20, 60 s on: `listened 60 s: answered after the act-by time, recorded only`, no `RunRequest`; each one `RunHoldAnswer` and `acks == [0.0]` |
| L4 | `test_a_failed_wait_is_one_fault_and_ends_the_listening` | DSP-TRG-05, DSP-STA-02 | `wait_ok=False`: `listened 0 s: stopped, the wait failed (a telegram Fault)`; `bot.waits == 1`; one `Fault` with `capability` `telegram` |
| L5 | 🪤 `test_an_update_that_is_not_an_answer_is_confirmed_and_the_wait_goes_on` | DSP-TRG-05, DSP-IN-04 | typed text and a *Run now* for `sched-2026-11-25` queued, *Skip today* 100 s on: `listened 100 s: answered, skipped operator`; `bot.waits == 5`; no update left; `RunHoldAnswer` run ids `[sched-2026-11-25, R1]` (sorted); no `RunRequest` at all |
| L6 | `test_a_stopped_clock_cannot_hold_the_fire` | DSP-TRG-05 | the listener's clock frozen at 22:30:20: `listened 0 s: no answer`; `bot.waits == 88` |
| L7 | `test_a_fire_that_is_not_held_or_is_answered_does_not_listen` | DSP-TRG-05 | a held graph answered (*Run now* at once, then one more fire), and an empty graph: each `listened 0 s: not held or answered`; `bot.waits == 0` |

**`tests/test_hold_listener_job.py`** (new, 5 cases). It imports `scripts.dispatch_scheduled_run as
entrypoint`.

| # | Test | Cites | Must prove |
| --- | --- | --- | --- |
| J1 | `test_the_client_waits_on_one_long_poll_and_confirms_nothing` | DSP-TRG-05 | a sender returning a text update (id 7), a *Run now* for `R1` (id 6, `cb6`) and a string: `wait_for_updates(timeout_seconds=25) == WaitedUpdates(7, (TelegramAnswer(6, "run_now", R1, "cb6"),))`; the one call was `("getUpdates", {"timeout": 25}, 35.0)` |
| J2 | `test_a_wait_that_fails_returns_none_and_says_why`, two cases | DSP-TRG-05, DSP-FAIL-01 | a sender raising `RuntimeError`: `None`, `last_error == "RuntimeError"`; a reply whose result is not a list: `None`, `"telegram_response_invalid"` |
| J3 | 🎯 `test_a_held_fire_prints_what_it_heard_and_a_placed_one_never_waits`, two cases | DSP-OBS-04, DSP-TRG-05 | `entrypoint.main(["--as-of", "2026-11-27", "--env-file", "none"]) == 0` with `_live_graph`, `_telegram` (a client on a `FakeBot` whose operator presses *Run now* 40 s on), `_now` (22:30:20 plus the bot's seconds) and `sense_from_env` (returns `""`) patched, `POSTGRES_DSN` set: a failing preflight prints exactly `held sched-2026-11-27 reason=failing failures=1` and `listened 40 s: answered, placed NYSE trading session`, `bot.waits == 2`; a passing one prints only `placed sched-2026-11-27 reason=NYSE trading session`, `bot.waits == 0` |

**`orchestration/tests/test_hold_drill.py`** (rewritten, 11 cases), each on a fresh `FakeBot` and
`drill_on`; each cites its DL-330 or DL-332 decision.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| D1 | `test_the_two_sessions_are_the_last_before_today` | — | as before |
| D2 | 🎯 `test_run_now_is_recorded_from_telegram_and_places_the_run` | operator *Run now* on `R1` 40 s on | true; the first message ends `Next message: press Run now.`; one notice, as before; the lines are exactly `R1  held, notice 102: Run now`, `R1  PASS`, `  listen    listened 40 s: answered, placed NYSE trading session`, `  answer    run_now from telegram`, `  act       placed reason=NYSE trading session, RunRequest 1`, `  cursor    confirmed`, `  faults    0`; `bot.acks == [0.0]`; no update left |
| D3 | `test_skip_today_is_recorded_from_telegram_and_skips_the_run` | *Skip today* on `R2` 30 s on | true; lines 2 to 5 `R2  PASS`, `  listen    listened 30 s: answered, skipped operator`, `  answer    skip_today from telegram`, `  act       skipped reason=operator, RunRequest 0` |
| D4 | `test_a_press_minutes_after_the_notice_is_heard_at_once` | *Run now* on `R1` 240 s on | true; line 3 `  listen    listened 240 s: answered, placed NYSE trading session`; `bot.acks == [0.0]` |
| D5 | `test_the_other_button_fails_the_round_and_is_still_acted_on` | *Run now* on `R2`, asked `skip_today` | false; lines 2 to 5 `R2  FAIL`, the listen line, `  answer    run_now from telegram, asked skip_today`, the placed act line |
| D6 | `test_no_press_fails_the_round_when_the_listening_ends` | no press | false; the last two lines `R1  FAIL`, `  listened 565 s: no answer`; `bot.waits == 23`; one notice |
| D7 | `test_a_notice_telegram_refuses_fails_the_round_at_once` | `send_ok=False` | false; `bot.waits == 0`; the lines exactly as before |
| D8 | 🪤 `test_a_press_waiting_before_the_notice_does_not_count` | a *Run now* on `R1` pressed before the round | false; the last line `  listened 565 s: no answer`; no update left; no acknowledgement |
| D9 | `test_a_refused_acknowledgement_is_a_fault_not_a_failure` | `ack_ok=False`, *Run now* 40 s on | true; the last line `  faults    1 (telegram: telegram_response_invalid)` |
| D10 | `test_a_cursor_left_behind_fails_the_round` | `confirm_ok=False`, *Run now* 40 s on | false; the lines hold `  cursor    1 answer(s) still pending` |
| D11 | `test_the_drill_asks_run_now_then_skip_today_and_says_when_done` | *Run now* on `R1` 40 s on, *Skip today* on `R2` 50 s on | as before, `(True, True)` |

**`tests/test_run_hold_drill_cli.py`** (rewritten, 6 cases). The `bot` fixture's `FakeBot` presses
*Run now* on `R1` 40 s and *Skip today* on `R2` 50 s after each notice; it patches
`orchestration.telegram_client.send_request` (recording each call's token), `cli._now` (`SAFE_NOW`)
and `cli._elapsed` (the bot's clock).

| # | Test | Must prove |
| --- | --- | --- |
| C1 | `test_a_refused_start_exits_2_and_calls_no_bot` | as before |
| C2 | 🎯 `test_both_rounds_passing_exit_0` | exit 0; the first line `HOLD DRILL  test bot 7000000001, listening as the fleet does: until 30 s before the next tick`, the last `HOLD DRILL  2 of 2 rounds passed`; `bot.acks == [0.0, 0.0]` |
| C3 | `test_a_failed_round_exits_1` | the `R2` press removed: exit 1; the lines hold `  listened 565 s: no answer`; the last `HOLD DRILL  1 of 2 rounds passed` |
| C4 | 🪤 `test_the_env_file_is_read_not_loaded` | as before |
| C5 | `test_the_poll_flags_are_gone`, over `--poll-seconds` and `--wait-minutes` | `cli.main([flag, "5"])` exits 2 and stderr holds `unrecognized arguments: <flag> 5` |

**Two existing test files change** (both cited by existing rows):

- `orchestration/tests/scheduled_dispatch_human_helpers.py`: `FakeTelegram` gains `waits: int = 0` and
  `wait_for_updates(self, *, timeout_seconds)`, which raises like its other methods when `fails`,
  counts the call, and returns `WaitedUpdates(<the highest answer's update id, else 0>, self.answers)`.
- `orchestration/tests/test_dispatcher_capability.py::test_every_fire_stays_inside_the_declared_capability`:
  its docstring adds *a held run whose fire hears the answer while it listens (DSP-TRG-05)*;
  `_operations` adds `"wait_answer": bool(telegram.waits)`; after the fires, a new recording graph
  with a failing preflight at 22:25 is fired at 22:30 and then listened on with
  `listen_while_held(graph, as_of=DAY, telegram=FakeTelegram(answers=(answer,)), clock=lambda: at(22, 31))`;
  that port's operations join the set and the graph joins `graphs`.

---

## Success factors

- [ ] The sixteen files of Appendix B carry its blob ids.
- [ ] A held fire stays on the bot until 30 s before the next tick, and no longer: L1, L6, J3.
- [ ] A press is recorded, acknowledged at once and acted on in the same fire; after 23:10 it is recorded only: L2, L3, D2, D4, J3.
- [ ] A failed wait is one Fault and ends the listening; typed text cannot spin it; a placed, skipped or answered fire does not listen: L4, L5, L7, J2, J3.
- [ ] The client's wait is one long poll that confirms nothing: J1.
- [ ] The drill listens as the fleet does; its poll flags are gone: D1 to D11, C1 to C5.
- [ ] The dispatcher image copies the module; the capability guard covers `wait_answer`.
- [ ] Laws v1.9, the test plan and both rollups (`49 / 52`) as Appendix B gives; `check_law_coverage` passes.
- [ ] The seven test files exist under the names given; the red run was seen first, then the green run.
- [ ] The law-cycle answer and the reading record are filled before the first change.
- [ ] Each of the 19 breaks was planted, seen red on its named test, and restored.
- [ ] Every module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage; a step the sandbox cannot run is named "not done".

---

## Traps

🪤 **Do not run `uv lock` or `uv sync`, in any form.** The lock changes in **one line**, given in
Appendix B (`0.133.0` → `0.133.1`, the lock's normalised form).

🪤 **The fake's clock moves only inside a long poll.** A test that expects time to pass must let a
wait happen; nothing in a test sleeps.

🪤 **The four counts are the design, not trivia.** 550 s / 22 waits (L1), 565 s / 23 (D6), 88 (L6),
5 (L5): a count that differs means the listener's window, its wait or its cap differs. Do not adjust a
count to make a test pass; report it.

🪤 **`may_act` reads the clock, not the tick.** `is_action_time` floors to the ten-minute tick, so a
listener at 23:11 would still count as the 23:10 tick and place a run the notice said it would not
(break B10).

🪤 **Patch `orchestration.telegram_client.send_request`, not `orchestration.telegram_http.send_request`.**

🪤 **The test-plan rows name your tests.** A test the rows name that is renamed, or whose docstring
does not cite the row's clause, fails the law-coverage step.

🪤 **Apply the diff; do not retype.** The blob ids catch a single different byte.

🪤 **`ruff format` runs as a pre-commit hook.** Run `uv run --no-sync ruff format` on the test files
before committing. No `# noqa`.

🪤 **Paste step lines and verdicts into the Closeout, not the whole `make ci` log.**

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150), tests included. No `# noqa`.
  📌 Prototype sizes: `orchestration/hold_listener.py` **120**, `telegram_client.py` **155**,
  `scheduled_dispatch_actions.py` **144**, `hold_drill.py` **140**, `scripts/dispatch_scheduled_run.py`
  **154**, `orchestration/tests/test_dispatcher_capability.py` **159**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers in code: the margin, the wait and the cap are named in Appendix B.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it, both from Appendix B.
- Secrets never through the worktree. The worktree has **no `.env`** and this sprint needs none; the
  tokens in the tests are invented. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. The planner re-measures: the sixteen blobs against Appendix B; the planner's seven test files run in
   place of the builder's; the break script against the builder's test files (19 breaks); the branch
   pushed; **`make gate-ran` exits 0** from `../ta-s296`, its SHA checked against `git rev-parse HEAD`;
   the open CodeQL alerts set-diffed against the baseline of 138, **after the branch's CI has finished**.
2. Merge to `main`, tag. **Post-merge CodeQL** and the image build checked on `main`.
3. **F1, from the main checkout, outside 22:00 to 24:00 UTC, with the operator at their phone**
   (`.venv/Scripts/python.exe scripts/run_hold_drill.py`, the test bot already in `.env`): on the first
   notice the operator waits **about four minutes**, then presses *Run now* once; on the second, presses
   *Skip today* at once. Both rounds `PASS`, `faults 0` on both, exit 0; the first round's listen line
   reads about 240 s; the operator sees *Answer recorded* within seconds of each press. Then the test
   bot's `getWebhookInfo` reads 0 pending. **Nobody reads the bot while the drill runs.**
4. **The deploy, on the operator's word:** retag the dispatcher job to an image built from this merge
   (the fleet's apps need not move). F2: the first weekday night after it, the job's fires take their
   usual ~40 s (nothing held, nothing to listen for) and the run reads `ACCEPTANCE PASS`.
5. Work-queue 146 closes at F2; 120 (a) closes at F1.

---

## Handover — paste this to Codex

```text
You are building Sprint 296 in the worktree ../ta-s296, on the branch
sprint-296-a-held-run-hears-the-operators-press-at-once. Never work on main.

Read docs/sprints/sprint-296-a-held-run-hears-the-operators-press-at-once.md, whole, before
anything else. It is the spec, and its bottom sections are your handback. Every decision is made:
Appendix B is the whole production change (sixteen files, the law cycle included), and you write or
amend seven test files.

In order:
1. Read orchestration/laws/dispatcher/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md, and DL-331 and DL-332 in docs/design-log.md. Fill the Law reading
   record in the spec BEFORE any change. The law-cycle answer: Yes, a guarantee (DSP-TRG-05 and
   DSP-PERF-02), written in full in Appendix B.
2. Write the test files of the Test plan: rewrite orchestration/tests/hold_drill_fakes.py,
   orchestration/tests/test_hold_drill.py and tests/test_run_hold_drill_cli.py; create
   orchestration/tests/test_hold_listener.py and tests/test_hold_listener_job.py; amend
   orchestration/tests/scheduled_dispatch_human_helpers.py and
   orchestration/tests/test_dispatcher_capability.py as described. Exactly the test names given;
   docstrings cite the clauses the tables give. Run
     uv run --no-sync pytest orchestration/tests/test_hold_listener.py tests/test_hold_listener_job.py orchestration/tests/test_hold_drill.py tests/test_run_hold_drill_cli.py orchestration/tests/test_dispatcher_capability.py --no-cov -q -p no:cacheprovider
   on the unchanged production files and paste the output into the Closeout. Expected: **3 errors during collection**.
3. Apply Appendix B: save its diff block to a file outside the repository's tracked files and run
   git apply on it. Then git hash-object on the sixteen files must print the sixteen blob ids
   Appendix B gives. Do NOT run uv lock or uv sync in any form.
4. Run the same pytest command again: 31 passed.
5. Plant the 19 breaks of Appendix C one at a time. Each must go red on the test named for it.
   Restore each with git checkout of that file before the next (commit your work first, or keep a
   copy, so the restore returns your built file).
6. Run uv run --no-sync ruff format on the test files, then make ci redirected to a file, and read
   the file. If a step cannot run in your sandbox (the dependency audit needs a network), say
   "not done" for that step and paste its lines.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in this sprint's
   row of docs/sprints/README.md (the row's status cell must lead with BUILT). Commit on the branch
   if your sandbox lets you write the repository's git directory; if not, leave the tree
   uncommitted and say so.

DO NOT: run uv lock or uv sync; run scripts/run_hold_drill.py, scripts/dispatch_scheduled_run.py or
any script outside pytest and make ci; make any network call, including to Telegram; run any az
command; change any file Appendix B does not name except the seven test files, this spec and
docs/sprints/README.md; edit scheduled_dispatch_human.py, scheduled_dispatch_polling.py,
hold_answers.py or scheduled_dispatch.py; add a design-log entry; edit docs/STATE.md,
docs/work-queue.md or docs/design-log.md; add entries to .secrets.baseline; use noqa; name a test
constant *TOKEN* (ruff S105); paste a whole make ci log into the spec; measure make ci through a
pipe.

Traps: the fake's clock moves only inside a long poll, and nothing in a test sleeps; the counts in
the tables (550 s and 22 waits, 565 s and 23, 88, 5) are the design: report a different count, do
not adjust it; may_act reads the clock, not the tick; patch orchestration.telegram_client.send_request;
the test-plan rows name your tests, so keep the names and cite the clauses; apply the diff, never
retype; ruff format is a pre-commit hook.

Two tiers of trouble. A wrong path, count or command in this spec whose intent is plain: correct
it, go on, and record it in the Return notes. A blob id that does not match after a clean git
apply, a law that contradicts the spec, an existing test that fails, or a break that stays green:
STOP and report. State anything not done as "not done" or "verified failing". Never write a Result
for work you have not done.

Handback checklist, each answered in the Closeout:
 1. Law reading record filled before the first change; the law-cycle answer with its reason.
 2. Red output of step 2 pasted.
 3. The sixteen blob ids after git apply, as printed.
 4. Green output of step 4 pasted.
 5. git diff --stat against the base: exactly Appendix B's sixteen files, the seven test files, this
    spec and docs/sprints/README.md.
 6. The 19 breaks, one line each: the test that went red, and restored.
 7. The line counts of the changed modules and the seven test files.
 8. make ci: the file's path, the exit code, each step's verdict line, the pytest totals and
    coverage; every step not run named "not done".
 9. The tree the proofs ran in, and that it holds no .env.
10. Status BUILT in the spec and in the README row; committed or not, and the SHA if committed.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first change.
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
| | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(answer + reason)*

**Contradictions found between a law and this spec:** *(or "none found")*

**Laws found silent where a decision was needed:** *(or "none")*

**Clauses that were ⬜ and are now proven:** *(clause IDs)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| | | | | |

**Tests added beyond the plan:** *(name + why, or "none")*

---

## Closeout — evidence

**Status:** *(BUILT, or what is not)*

**Tree the proofs ran in (and `.env` present?):**

**Result:** *(only for work done)*

**Files changed:** *(`git diff --stat` against the base)*

**Commit:**

**Proof — the red run first:**

**Proof — the green run:**

**Sixteen blobs after git apply:**

**Guards planted:** *(B1 to B19, one line each)*

**Module line counts:**

**`make ci`:** *(path, exit code, each step's verdict line, pytest totals and coverage)*

**`make gate-ran`:** not done; the planner's, after the push.

**Not met / verified failing:**

---

## Return notes

*(spec corrections made under the first tier, anything the next planner should know)*

---

## Closeout of the planner's prototype — measured 2026-11-28

Prototype `../ta-s296-proto`, local branch `proto-s296` (never pushed), from `main` `702d4248`;
final commit `feb6534b`. Kit OneDrive `wq120-2026-11-28/`.

- **Red**, the seven test files on the unchanged production files: **3 errors during collection**
  (`orchestration/tests/test_hold_listener.py`, `tests/test_hold_listener_job.py`,
  `orchestration/tests/test_dispatcher_capability.py`; kit `red_on_unchanged_296.txt`, measured in
  `../ta-s296`).
- **Green**, the same command after the change: **31 passed**.
- **`make ci`** on `fd8889eb` (`UV_NO_SYNC=1`, redirected to kit `proto296_make_ci.txt`): exit 0;
  5,484 passed, 8 skipped, 100.00 %; dependency audit `No unaccepted vulnerabilities; 1 accepted
  advisory re-checked`. `feb6534b` then reordered two lines of L5 (below); on it the five test files
  read 31 passed and `orchestration/hold_listener.py` 100.00 % branch coverage.
- **Breaks: 19 of 19 red** on `feb6534b`, the tree clean after (kit `s296_breaks_on_prototype.txt`).
  🪤 On the run before, B7 survived: L5 queued the other run's press *after* the text, so
  `poll_answers`' own confirm cleared the text and the listener's confirm of a non-answer was never
  needed. L5 now queues the press first; the order is the test's point.
- **Two existing guards went red on the way, and their fixes are part of the change:** the dispatcher
  image's module list (`orchestration/Dockerfile`) and the capability guard (a listening fire uses
  `wait_answer`).
- **Dry run** from the committed spec in `../ta-s296`: DRY_RUN_PENDING.

---

## Appendix B — the change, measured on the planner's prototype

Sixteen files. Apply the block below with `git apply`; then `git hash-object` on each file must print:

```text
6d90d98970ab7eddbc6f556a0b025e35b57e35a6  docs/laws/INDEX.md
2d1fc49139e91907c15d50e2f6134fd09903dddc  docs/laws/ledger.md
2a196e7e39f522dc4f5fb027f145e91722694fc4  orchestration/Dockerfile
66264f3a618308896de88144e08187bc36fa461d  orchestration/hold_drill.py
23da61d2bf2a9102fbb8508c2624997a60ce41e8  orchestration/hold_drill_verdict.py
56849a5e60d0dde947db83cd3e0b89fa58a924b1  orchestration/hold_listener.py
f621aac1d0b00601da709a931031831629440d32  orchestration/laws/dispatcher/laws.md
238b898da7c9cd5e4617ce45d0be57a56bacc257  orchestration/laws/dispatcher/test-plan.md
3be3b85c7ddb7bbf65164c95633939a1f2e2658b  orchestration/scheduled_dispatch_actions.py
800dc2c58ea87ac951465a74d2357922b9b661d7  orchestration/telegram_client.py
bd9f747070948ca766895b2b627af68b4d0ae7c3  orchestration/telegram_port.py
88ce2e6b02e5778a93eff05aa24aa65189f9b817  orchestration/telegram_updates.py
eef8f20568d3ff01cbacc8f5ea72120fdf5c46bd  pyproject.toml
3cfe44f3a3c2798fafa50cab46d945f6ed2b3c4d  scripts/dispatch_scheduled_run.py
7f1958e7f1554772e6d722e0dbe524558b6ad5c8  scripts/run_hold_drill.py
b76e3f9efd934fb0b8d874dca56cd7e57f777873  uv.lock
```

```diff
diff --git a/docs/laws/INDEX.md b/docs/laws/INDEX.md
index 1bcf5452..6d90d989 100644
--- a/docs/laws/INDEX.md
+++ b/docs/laws/INDEX.md
@@ -52,7 +52,7 @@ Each agent's law files live at `agents/<name>/laws/`:
 | curator | ✅ LOCKED v1.1 (S205) | 23 / 47 | S205 rewrites and proves `CUR-TYP-01`; counters are clauses proven / clauses declared |
 | researcher | ✅ LOCKED v1.2 (DL-203) | 20 / 43 | DL-203 reconciles `PARAM` only; S205 rewrites and proves `RES-TYP-01`; counters are clauses proven / clauses declared |
 | master | ✅ LOCKED v1.12 (S277, DL-289) | 33 / 58 | S277 (DL-289 amendment 4) re-proves every-candidate probing, later proven fallback/key handover, refusal and unanswered pass-over, and recorded llm_fallbacks; no clause added. S276 (DL-289 amendment 1) adds and proves MST-OUT-05, MST-NEV-08 and MST-FAIL-08; amended MST-OUT-04, MST-NEV-07 and MST-OBS-04 re-proven for ordered candidate choice, key containment and recorded passed-over outcomes. Before that S272 (DL-297) adds and proves MST-TRG-03, MST-ORD-04 and MST-OBS-05 and proves amended MST-OUT-03; DRIFT-113 corrected, recovery at boot not built; before that S262 (DL-282) amends and re-proves `MST-OUT-04` for selected-vendor readiness and adds and proves `MST-NEV-07` for validated probe/key selection; DRIFT-105 corrected; before that S251 adds and proves `MST-FAIL-07` (the start-up refusal of an unhonourable remediation mode; remediation outside the constitution until DL-36 C/D; DRIFT-059); S244 amends and proves `MST-TRG-01`/`MST-ORD-02`, re-proves `MST-STA-02`/`MST-IDM-01`, and adds and proves `MST-IDM-03` (boot-id replay), `MST-ORD-03` (concurrent EHLO) and `MST-FAIL-06` (loud budget exhaustion), DRIFT-091; S232 adds and proves `MST-DEP-05` (substrate-only imports) and corrects `MST-NEV-01`/`MST-SEC-03`/`MST-DEP-03` to name the pack data actually consulted; DL-203 reconciles `PARAM` only; S217 adds and proves `MST-OUT-04` whole-fleet readiness and `MST-FAIL-05` classification; S205 rewrites and proves `MST-TYP-01`; S188 adds and proves credential-test handover guards; RSA/Key Vault clauses deferred S74; S204 gives every clause a row and makes rowless clauses a hard gate |
-| dispatcher | ✅ LOCKED v1.8 (S287, DL-311) | 47 / 50 | S287 (DL-311) adds and proves DSP-OUT-10 (the brief's book lines: the held names past their declared target and the forecast's odds, from the active Positions and the session's held claims read by key), amends DSP-DEP-01 and CAP for the Position and BarrierForecast reads, and moves DSP-OUT-09 back under Outputs. S285 (DL-309) adds and proves DSP-NEV-04 (a placed run is never held again) and DSP-OBS-04 (each fire's line says what it did), amends DSP-TRG-01 and DSP-PERF-01 (the last placing fire is the 23:10 tick) and DSP-IDM-02, and proves DSP-TYP-01 with the fourth action, `already-placed`. S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. Before that S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. S251 names the daily brief in the purpose line and `DSP-IDN-03` (DRIFT-077); Component book under `orchestration/laws/dispatcher/`; scheduled placement, the human-hold loop and the daily brief (S234, DL-230/DL-231); `orchestration.dispatcher.Dispatcher` named out of scope by DL-221; closes DRIFT-068 and DRIFT-069 |
+| dispatcher | ✅ LOCKED v1.9 (S296, DL-332) | 49 / 52 | S296 (DL-332) adds and proves DSP-TRG-05 (a held fire stays on the operator's bot until 30 s before the next tick and acts on a press at once) and DSP-PERF-02 (a press acknowledged within seconds), and amends DSP-STA-02, DSP-OBS-04 and CAP (`wait_answer`). S287 (DL-311) adds and proves DSP-OUT-10 (the brief's book lines: the held names past their declared target and the forecast's odds, from the active Positions and the session's held claims read by key), amends DSP-DEP-01 and CAP for the Position and BarrierForecast reads, and moves DSP-OUT-09 back under Outputs. S285 (DL-309) adds and proves DSP-NEV-04 (a placed run is never held again) and DSP-OBS-04 (each fire's line says what it did), amends DSP-TRG-01 and DSP-PERF-01 (the last placing fire is the 23:10 tick) and DSP-IDM-02, and proves DSP-TYP-01 with the fourth action, `already-placed`. S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. Before that S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. S251 names the daily brief in the purpose line and `DSP-IDN-03` (DRIFT-077); Component book under `orchestration/laws/dispatcher/`; scheduled placement, the human-hold loop and the daily brief (S234, DL-230/DL-231); `orchestration.dispatcher.Dispatcher` named out of scope by DL-221; closes DRIFT-068 and DRIFT-069 |
 | surfaces | ✅ LOCKED v1.9 (S287, S274, S270, S267, S263, S262, S251, S236, S229, S228) | 32 / 39 | S287 (DL-311) adds and proves `SRF-OUT-09` (the selected run's book panel: the brief's book lines and a row per held name, the likeliest to reach its stop first leading) and aligns the test-plan's status line; before that S274 (DL-300) reconciles `PARAM` only: `master_window_start_utc` is 22:00, the master's live wake (DL-294 amendment 1); no clause changes; before that S270 (DL-295) reconciles `PARAM` only: `window_end_utc` is 23:30 and the new `window_days_utc` is 1-5, the operator's wake window (DL-294); no clause changes; before that S267 (DL-288) adds and proves `SRF-DEP-04`: complete-tag evidence from every attempt of a successful image-build run, latest first and earlier attempts newest first, with main-history and unreadable-evidence guards; DRIFT-111 corrected; before that S263 (DL-284) amends and re-proves `SRF-DEP-03` for model-family disconnection and its start-up reason; before that S262 (DL-282) adds and proves `SRF-DEP-03`: dashboard chat binds only through its selected provider and disconnects for absent keys, unknown providers and either vendor configuration error; DRIFT-105 corrected; before that S251 narrows `SRF-OUT-03` (quick asks write no audit fact; DRIFT-078); Component book under `surfaces/laws/`; dashboard, CLI, MCP, chat and operator-intent write boundaries; S236 adds and proves `SRF-OUT-08` (the unattended scorecard) and the `scorecard` tool, and files DRIFT-078; selected-run scoping cites corrected DRIFT-022 |

 See [ledger.md](ledger.md) for the canonical version of this table.
diff --git a/docs/laws/ledger.md b/docs/laws/ledger.md
index 8e1273bb..2d1fc491 100644
--- a/docs/laws/ledger.md
+++ b/docs/laws/ledger.md
@@ -49,7 +49,7 @@ and torn down to zero. Historical Neo4j rows remain valid evidence for the pre-S
 | operator | ✅ v1.10 (LOCKED) | 20 / 51 | 🟨 partial — **20 of 51 clauses proven** after S269 (DL-292) rewords and re-proves `OPR-FAIL-02`: only text, a number or a boolean is a value; `null`, lists and objects are omitted from required and optional parameters, so missing required values are refused with the existing sentence and audit, while scalar text and blank-text behavior are unchanged; DRIFT-112 corrected; no clause added; before that S268 (DL-290) rewords and re-proves `OPR-FAIL-02`: an intent of no known family, or lacking a parameter its family requires under any accepted name, is refused before its audit, which reads `refused`, and no `Intent` is written; the prompt states each family's parameter names; DRIFT-109 corrected; no clause added; before that S265 (DL-286) rewords and re-proves `OPR-FAIL-01`: failed requests are audited on both capabilities, one operator fault and one plain reason, no grammar or error text in graph; malformed JSON is a fault-free refusal; DRIFT-107/108 corrected; no clause added; before that S264 (DL-285) re-proves `OPR-STA-03` for vendor stop reasons and billed counts on both reply paths and adds/proves `OPR-FAIL-04` for audited, fault-free cut-offs with one sentence and explicit grammar preserved; DRIFT-106 corrected; before that S263 (DL-284) amends and re-proves `OPR-DEP-01` for provider effort resolution and pre-call model-family refusal; PARAM effort and CAP reconciled; before that S262 (DL-282) amends and re-proves `OPR-DEP-01` for the selected vendor, model resolution and no fallback; PARAM reconciled; before that S256 (DL-272) rewrites and proves `OPR-IDM-02`: duplicate commands share audit/intent while every model call has its own row; DRIFT-104 corrected; S222 proves `OPR-SEC-01` key containment and `OPR-DEP-01` Anthropic-only dependency; S205 rewrites and proves `OPR-TYP-01`; 31 have a gray row |
 | supervisor | ✅ v1.3 (LOCKED) | 23 / 48 | 🟨 partial — **23 of 48 clauses proven** after S251 (DL-260) declares the divergence-family exception in `SUP-IDN-02` (DRIFT-094) and proves `SUP-OBS-02` on its real sources (live `Fault` incidents, unresolved critical Flags; DRIFT-076); v1.2 (DL-225) was never reflected here and is now; after S205 rewrites and proves `SUP-TYP-01`; S179 proves append-only `FaultResolution` retirement (`SUP-OBS-03`); 26 have a gray row |
 | master | ✅ v1.12 (LOCKED) | 33 / 58 | S277 (DL-289 amendment 4) re-proves every-candidate probing, later proven fallback/key handover, refusal and unanswered pass-over, and recorded llm_fallbacks; no clause added. S276 (DL-289 amendment 1) adds and proves MST-OUT-05, MST-NEV-08 and MST-FAIL-08; amended MST-OUT-04, MST-NEV-07 and MST-OBS-04 re-proven for ordered candidate choice, key containment and recorded passed-over outcomes. 🟨 partial — **33 of 58 clauses proven** after S272 (DL-297) adds and proves MST-TRG-03, MST-ORD-04 and MST-OBS-05 and proves amended MST-OUT-03; DRIFT-113 corrected, recovery at boot not built; before that S262 (DL-282) amends and re-proves `MST-OUT-04` for selected-vendor readiness and adds and proves `MST-NEV-07` for validated probe/key selection; DRIFT-105 corrected; before that S251 (DL-260) adds and proves `MST-FAIL-07`: master refuses to start in a remediation mode it cannot honour; attempting remediation is stated outside the constitution until DL-36 Pieces C/D (DRIFT-059); after S244 amends and proves `MST-TRG-01` (`POST /ehlo`, the agent's bounded resend with one boot id) and `MST-ORD-02` (master may be asleep or busy), re-proves `MST-STA-02`/`MST-IDM-01` on their amended text, and adds and proves `MST-IDM-03` (a repeated boot id replays), `MST-ORD-03` (concurrent EHLO service) and `MST-FAIL-06` (a spent budget exits loud); S232 adds and proves `MST-DEP-05` (substrate-only imports) and corrects `MST-NEV-01`/`MST-SEC-03`/`MST-DEP-03` to name the pack data actually consulted; S217 adds and proves `MST-OUT-04` whole-fleet readiness and `MST-FAIL-05` classification; S205 rewrites and proves `MST-TYP-01`; S188 adds and proves credential-test handover guards; S204 gives every clause a row and promotes missing rows to a hard gate · RSA signing + Key Vault + integration clauses deferred (S73/S74) |
-| dispatcher | ✅ v1.8 (LOCKED) | 47 / 50 | S287 (DL-311) adds and proves DSP-OUT-10 (the brief's book lines: the held names past their declared target and the forecast's odds, from the active Positions and the session's held claims read by key), amends DSP-DEP-01 and CAP for the Position and BarrierForecast reads, and moves DSP-OUT-09 back under Outputs. S285 (DL-309) adds and proves DSP-NEV-04 (a placed run is never held again) and DSP-OBS-04 (each fire's line says what it did), amends DSP-TRG-01 and DSP-PERF-01 (the last placing fire is the 23:10 tick) and DSP-IDM-02, and proves DSP-TYP-01 with the fourth action, `already-placed`. S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. 🟨 partial — **47 of 50 clauses proven**; S251 names the daily brief in the purpose line and `DSP-IDN-03`'s scope (DRIFT-077), count unchanged; after S234 adds and proves the daily brief (`DSP-IDN-04`, `DSP-TRG-03`, `DSP-OUT-06`, `DSP-IDM-03`, `DSP-SEC-02`, `DSP-FAIL-03`) and proves `DSP-SEC-01` across every port operation; `DSP-DEP-01` amended and still gray (partial: `CAP` conformance). S229 covered scheduled run placement, readiness holds, degraded placement, human answers and notices; names `orchestration.dispatcher.Dispatcher` out of scope by DL-221; closes DRIFT-068 and DRIFT-069. |
+| dispatcher | ✅ v1.9 (LOCKED) | 49 / 52 | S296 (DL-332) adds and proves DSP-TRG-05 (a held fire stays on the operator's bot until 30 s before the next tick and acts on a press at once) and DSP-PERF-02 (a press acknowledged within seconds), and amends DSP-STA-02, DSP-OBS-04 and CAP (`wait_answer`). S287 (DL-311) adds and proves DSP-OUT-10 (the brief's book lines: the held names past their declared target and the forecast's odds, from the active Positions and the session's held claims read by key), amends DSP-DEP-01 and CAP for the Position and BarrierForecast reads, and moves DSP-OUT-09 back under Outputs. S285 (DL-309) adds and proves DSP-NEV-04 (a placed run is never held again) and DSP-OBS-04 (each fire's line says what it did), amends DSP-TRG-01 and DSP-PERF-01 (the last placing fire is the 23:10 tick) and DSP-IDM-02, and proves DSP-TYP-01 with the fourth action, `already-placed`. S278 (DL-301 amendment 7) amends and re-proves DSP-IN-05 for named platform failures, unknown warnings except the five measured deploy/wake by-products, and the platform's own safe why; A31-A37 also re-prove DSP-IDM-04 and DSP-OUT-07. No clause added; count unchanged. S277 (DL-289 amendment 4) re-proves DSP-OUT-09 with activation parts before the runs switch lines; no clause added. S276 (DL-289 amendment 1) adds and proves DSP-OUT-09 for the brief LLM line; DSP-DEP-01 and CAP include recent AgentInstance reads, dependency envelope still gray. S275 (DL-301 amendments 1 and 2) adds and proves the ten sensor clauses; A1–A30 pass and all 35 specified breaks turn a builder test red, then restore. 🟨 partial — **49 of 52 clauses proven**; S251 names the daily brief in the purpose line and `DSP-IDN-03`'s scope (DRIFT-077), count unchanged; after S234 adds and proves the daily brief (`DSP-IDN-04`, `DSP-TRG-03`, `DSP-OUT-06`, `DSP-IDM-03`, `DSP-SEC-02`, `DSP-FAIL-03`) and proves `DSP-SEC-01` across every port operation; `DSP-DEP-01` amended and still gray (partial: `CAP` conformance). S229 covered scheduled run placement, readiness holds, degraded placement, human answers and notices; names `orchestration.dispatcher.Dispatcher` out of scope by DL-221; closes DRIFT-068 and DRIFT-069. |
 | surfaces | ✅ v1.9 (LOCKED) | 32 / 39 | 🟨 partial — **32 of 39 clauses proven**; S287 (DL-311) adds and proves `SRF-OUT-09` (the selected run's book panel: the brief's book lines and a row per held name, the likeliest to reach its stop first leading) and aligns the test-plan's status line; before that S274 (DL-300) reconciles `PARAM` only: `master_window_start_utc` is 22:00, the master's live wake (DL-294 amendment 1); no clause changes; before that S270 (DL-295) reconciles `PARAM` only: `window_end_utc` is 23:30 and the new `window_days_utc` is 1-5, the operator's wake window (DL-294); no clause changes; before that S267 (DL-288) adds and proves `SRF-DEP-04`: complete-tag evidence from every attempt of a successful image-build run, latest first and earlier attempts newest first, with main-history and unreadable-evidence guards; DRIFT-111 corrected; before that S263 (DL-284) amends and re-proves `SRF-DEP-03` for model-family disconnection and its start-up reason; before that S262 (DL-282) adds and proves `SRF-DEP-03`: dashboard chat binds only through its selected provider and disconnects for absent keys, unknown providers and either vendor configuration error; DRIFT-105 corrected; before that S251 narrows `SRF-OUT-03` to model-composed answers and names the quick asks as graph reads that write no audit fact (DRIFT-078), count unchanged; after S236 adds and proves `SRF-OUT-08` (the unattended vital and the `scorecard` answer: G1, G3 and two clocks from the acceptance gate's verdict and the records human actions leave) and lists `scorecard` in `SRF-TRG-02`; DRIFT-078 is filed for `SRF-OUT-03`'s silence on the quick asks. S228 added and proved `SRF-OUT-07` (28 of 35); S229 authored the book (27 of 34). Covers dashboard, CLI, MCP, chat and operator-intent write boundaries; selected-run scoping cites DRIFT-022 as already corrected. |

 *2026-09-23 — [DL-203](../design-log.md) (work-queue item 33) amended nine of these laws in
diff --git a/orchestration/Dockerfile b/orchestration/Dockerfile
index ff4375e7..2a196e7e 100644
--- a/orchestration/Dockerfile
+++ b/orchestration/Dockerfile
@@ -86,6 +86,7 @@ COPY orchestration/daily_brief_text.py orchestration/daily_brief_text.py
 COPY orchestration/fleet_readiness.py orchestration/fleet_readiness.py
 COPY orchestration/history_window.py orchestration/history_window.py
 COPY orchestration/hold_answers.py orchestration/hold_answers.py
+COPY orchestration/hold_listener.py orchestration/hold_listener.py
 COPY orchestration/observatory.py orchestration/observatory.py
 COPY orchestration/packs/__init__.py orchestration/packs/__init__.py
 COPY orchestration/packs/trading_acceptance.py orchestration/packs/trading_acceptance.py
diff --git a/orchestration/hold_drill.py b/orchestration/hold_drill.py
index a0326852..66264f3a 100644
--- a/orchestration/hold_drill.py
+++ b/orchestration/hold_drill.py
@@ -3,9 +3,10 @@
 Agent: orchestration
 Role: stage work-queue 120 (a) (DL-330): on an in-memory graph, plant a failing
       fleet preflight for a past NYSE session, fire the unchanged
-      dispatch_with_human_answer at a planted clock inside the placing window, and
-      wait for the operator's press on the test bot; the verdict module judges it.
-External I/O: the injected Telegram port (the test bot); the sleep it is handed.
+      dispatch_with_human_answer at a planted clock inside the placing window, then
+      listen for the operator's press on the test bot as the fleet does (DL-332); the
+      verdict module judges it.
+External I/O: the injected Telegram port (the test bot); the elapsed clock it is handed.
 """

 from __future__ import annotations
@@ -17,6 +18,7 @@ from typing import TYPE_CHECKING
 from agents.provider.domain.market_calendar import is_trading_session
 from kernel import InMemoryGraphStore
 from orchestration.hold_drill_verdict import faults, judge, verdict
+from orchestration.hold_listener import listen_while_held
 from orchestration.scheduled_dispatch import scheduled_run_id
 from orchestration.scheduled_dispatch_human import dispatch_with_human_answer

@@ -28,25 +30,22 @@ if TYPE_CHECKING:
     from orchestration.hold_answers import Answer
     from orchestration.scheduled_dispatch import ScheduledDispatchResult
     from orchestration.settings import OrchestratorSettings
-    from orchestration.telegram_port import TelegramPort
+    from orchestration.telegram_port import ListeningTelegramPort, TelegramPort

 ROUNDS: tuple[Answer, ...] = ("run_now", "skip_today")
 BUTTON = {"run_now": "Run now", "skip_today": "Skip today"}
 DRILL_FAILURE = "transient:execution:alpaca-broker:hold-drill"
-PREFLIGHT_AT = time(22, 25)  # fresh at both fires: 70 minutes is the age limit
+PREFLIGHT_AT = time(22, 25)  # fresh for the whole round: 70 minutes is the age limit
 FIRST_FIRE = time(22, 30, 5)  # the first tick of the placing window, 22:30 to 23:10
-ANSWER_FIRE = time(22, 40, 5)


 @dataclass(frozen=True)
 class Drill:
-    """What every round shares: the bot, the settings, the waiting and the printer."""
+    """What every round shares: the bot, the settings, the clock and the printer."""

-    telegram: TelegramPort
+    telegram: ListeningTelegramPort
     settings: OrchestratorSettings
-    poll_seconds: int
-    wait_seconds: int
-    sleep: Callable[[float], None]
+    elapsed: Callable[[], float]  # seconds from any origin: real time passing
     report: Callable[[str], None]


@@ -92,29 +91,40 @@ def run_round(drill: Drill, *, as_of: date, wanted: Answer) -> bool:
     drill.telegram.send_brief(
         text=f"Hold drill: nothing in the fleet is held. Next message: press {button}."
     )
-    result = _fire(drill, graph, as_of, FIRST_FIRE)
+    clock = _planted_clock(drill, as_of)
+    result = _fire(drill, graph, as_of, clock())
     hold = graph.get_node("RunHold", result.node_key or "")
     if hold is None or "notified_at" not in hold.props:
         line = f"notice not sent ({result.action}){faults(graph)}"
         return verdict(drill.report, run_id, passed=False, lines=[line])
     drill.report(f"{run_id}  held, notice {hold.props['notice_message_id']}: {button}")
-    waited = 0
-    while (result := _fire(drill, graph, as_of, ANSWER_FIRE)).action == "held":
-        if waited >= drill.wait_seconds:
-            line = f"no answer in {waited} s"
-            return verdict(drill.report, run_id, passed=False, lines=[line])
-        drill.sleep(drill.poll_seconds)
-        waited += drill.poll_seconds
+    heard = listen_while_held(
+        graph,
+        as_of=as_of,
+        telegram=drill.telegram,
+        clock=clock,
+        settings=drill.settings,
+    )
+    if heard.result is None:
+        return verdict(drill.report, run_id, passed=False, lines=[heard.line()])
     return judge(
         graph,
         drill.telegram,
         run_id=run_id,
         wanted=wanted,
-        result=result,
+        result=heard.result,
         report=drill.report,
+        heard=heard.line(),
     )


+def _planted_clock(drill: Drill, as_of: date) -> Callable[[], datetime]:
+    """*as_of*'s first placing fire, moving at the real time since the round began."""
+    origin = drill.elapsed()
+    start = datetime.combine(as_of, FIRST_FIRE, UTC)
+    return lambda: start + timedelta(seconds=drill.elapsed() - origin)
+
+
 def _drain(telegram: TelegramPort) -> None:
     """Confirm any press already waiting: only a press after the notice counts."""
     stale = telegram.poll_answers()
@@ -123,9 +133,8 @@ def _drain(telegram: TelegramPort) -> None:


 def _fire(
-    drill: Drill, graph: GraphStore, as_of: date, clock: time
+    drill: Drill, graph: GraphStore, as_of: date, now: datetime
 ) -> ScheduledDispatchResult:
-    now = datetime.combine(as_of, clock, UTC)
     return dispatch_with_human_answer(
         graph, as_of=as_of, now=now, telegram=drill.telegram, settings=drill.settings
     )
diff --git a/orchestration/hold_drill_verdict.py b/orchestration/hold_drill_verdict.py
index b052eef0..23da61d2 100644
--- a/orchestration/hold_drill_verdict.py
+++ b/orchestration/hold_drill_verdict.py
@@ -32,6 +32,7 @@ def judge(
     wanted: Answer,
     result: ScheduledDispatchResult,
     report: Callable[[str], None],
+    heard: str,
 ) -> bool:
     """Report one answered round's lines and return whether it did what was asked."""
     answers = [
@@ -44,6 +45,7 @@ def judge(
     asked = f", asked {wanted}" if pressed != wanted else ""
     cursor = f"{len(pending)} answer(s) still pending" if pending else "confirmed"
     lines = [
+        f"listen    {heard}",
         f"answer    {pressed} from {source}{asked}",
         f"act       {result.action} reason={result.reason}, RunRequest {int(placed)}",
         f"cursor    {cursor}",
diff --git a/orchestration/hold_listener.py b/orchestration/hold_listener.py
new file mode 100644
index 00000000..56849a5e
--- /dev/null
+++ b/orchestration/hold_listener.py
@@ -0,0 +1,120 @@
+"""Hold listener: while today's run is held and unanswered, the fire stays on the bot.
+
+Agent: orchestration
+Role: DSP-TRG-05 / DSP-PERF-02 (DL-332): after a fire that leaves the run held,
+      long-poll the operator's bot until 30 s before the next ten-minute tick; on a
+      press, record, acknowledge and confirm it at once and, at or before the act-by
+      time, act on it in the same fire. Telegram drops a press nobody reads in minutes
+      and refuses an acknowledgement about 15 s after the press (DL-331), so a fire
+      that only polled once lost most presses.
+External I/O: the injected Telegram port and GraphStore; the clock it is handed.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from datetime import timedelta
+from functools import partial
+from math import ceil
+from typing import TYPE_CHECKING
+
+from orchestration.fleet_readiness import is_active_run_hold
+from orchestration.hold_answers import effective_answer
+from orchestration.scheduled_dispatch import scheduled_run_id
+from orchestration.scheduled_dispatch_actions import may_act, next_tick
+from orchestration.scheduled_dispatch_human import dispatch_with_human_answer
+from orchestration.scheduled_dispatch_polling import fault_safe, poll_answers
+
+if TYPE_CHECKING:
+    from collections.abc import Callable
+    from datetime import date, datetime
+
+    from kernel import GraphStore
+    from orchestration.scheduled_dispatch import ScheduledDispatchResult
+    from orchestration.settings import OrchestratorSettings
+    from orchestration.telegram_port import ListeningTelegramPort
+
+LISTEN_MARGIN = timedelta(seconds=30)  # off the bot before the next fire polls (409)
+WAIT_SECONDS = 25  # one long poll
+WAITS_PER_POLL = 4  # waits that return at once (updates, a stopped clock) stay bounded
+
+
+@dataclass(frozen=True)
+class Listened:
+    """What one listening fire heard: for how long, and what an answer led to."""
+
+    seconds: int
+    outcome: str
+    result: ScheduledDispatchResult | None = None
+
+    def line(self) -> str:
+        """The fire's second printed line (DSP-OBS-04)."""
+        return f"listened {self.seconds} s: {self.outcome}"
+
+
+def listen_while_held(
+    graph: GraphStore,
+    *,
+    as_of: date,
+    telegram: ListeningTelegramPort,
+    clock: Callable[[], datetime],
+    settings: OrchestratorSettings | None = None,
+) -> Listened:
+    """Stay on the bot while *as_of*'s run is held and unanswered; act on a press."""
+    start = clock()
+    until = next_tick(start) - LISTEN_MARGIN
+    run_id = scheduled_run_id(as_of)
+    waits = WAITS_PER_POLL * ceil((until - start).total_seconds() / WAIT_SECONDS)
+    while _unanswered(graph, run_id) and waits > 0:
+        left = int((until - clock()).total_seconds())
+        if left <= 0:
+            break
+        waits -= 1
+        timeout = min(WAIT_SECONDS, left)
+        wait = partial(telegram.wait_for_updates, timeout_seconds=timeout)
+        waited = fault_safe(graph, telegram, wait, None)
+        if waited is None:
+            return _heard(start, clock(), "stopped, the wait failed (a telegram Fault)")
+        if waited.answers:
+            now = clock()
+            poll_answers(graph, telegram, as_of=as_of, now=now)
+            if effective_answer(graph, run_id=run_id) is not None:
+                return _act(graph, as_of, telegram, start, now, settings)
+        if waited.last_update_id:
+            confirm = partial(telegram.confirm, up_to_update_id=waited.last_update_id)
+            fault_safe(graph, telegram, confirm, False)
+    held = _unanswered(graph, run_id)
+    return _heard(start, clock(), "no answer" if held else "not held or answered")
+
+
+def _act(
+    graph: GraphStore,
+    as_of: date,
+    telegram: ListeningTelegramPort,
+    start: datetime,
+    now: datetime,
+    settings: OrchestratorSettings | None,
+) -> Listened:
+    if not may_act(now):
+        return _heard(start, now, "answered after the act-by time, recorded only")
+    result = dispatch_with_human_answer(
+        graph, as_of=as_of, now=now, telegram=telegram, settings=settings
+    )
+    return _heard(start, now, f"answered, {result.action} {result.reason}", result)
+
+
+def _unanswered(graph: GraphStore, run_id: str) -> bool:
+    held = any(
+        node.props.get("run_id") == run_id and is_active_run_hold(node)
+        for node in graph.list_nodes("RunHold")
+    )
+    return held and effective_answer(graph, run_id=run_id) is None
+
+
+def _heard(
+    start: datetime,
+    end: datetime,
+    outcome: str,
+    result: ScheduledDispatchResult | None = None,
+) -> Listened:
+    return Listened(int((end - start).total_seconds()), outcome, result)
diff --git a/orchestration/laws/dispatcher/laws.md b/orchestration/laws/dispatcher/laws.md
index a58f0f4a..f621aac1 100644
--- a/orchestration/laws/dispatcher/laws.md
+++ b/orchestration/laws/dispatcher/laws.md
@@ -1,6 +1,6 @@
 # `Dispatcher` — Laws

-**Prefix:** `DSP` · **status:** LOCKED v1.8 · **Owner:** Yury Gurevich
+**Prefix:** `DSP` · **status:** LOCKED v1.9 · **Owner:** Yury Gurevich

 > Decide whether the scheduled daily graph-pull run is placed, skipped, held, or placed in degraded posture,
 > brief the operator once on each run it placed, and tell the operator when a container of the
@@ -79,6 +79,16 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   time and starts `container_sensor_overlap_minutes` before the previous successful read ended; the
   first read starts `container_sensor_first_read_hours` back, and no read starts further back than
   `container_sensor_max_lookback_hours`.
+- **DSP-TRG-05** — A fire that leaves its run held with no answer recorded stays on the operator's
+  bot until 30 seconds before the next ten-minute tick (DL-332), in long polls of at most 25 seconds
+  that confirm nothing, and at most four polls for each one the time allows. On a press it records,
+  acknowledges and confirms the answer at once and, while the time is at or before `_ACT_BY`, acts on
+  it in the same fire (`DSP-TRG-01`); after `_ACT_BY` it records only. It stops at the run's first
+  effective answer, at that deadline, or at a wait that fails, which becomes a `telegram` `Fault`
+  (`DSP-STA-02`). An update that is not an answer is confirmed after the wait that returned it. A
+  fire that placed or skipped the run, or found it answered, does not listen. Telegram drops a press
+  nobody reads in about 2.5 to 4 minutes and refuses an acknowledgement about 15 seconds after the
+  press (DL-331), so a fire that polled once heard most presses too late or not at all.

 ## Outputs (`OUT`)

@@ -157,7 +167,7 @@ green only when a functional test cites its ID (conventions §3). Tests + status

 - **DSP-STA-01** — `RunHold` facts are append-only: recovery adds `released_at`, and a later re-hold
   creates a new key rather than mutating a released hold into active evidence.
-- **DSP-STA-02** — Telegram send, poll, ack, and confirm failures are contained as graph faults and
+- **DSP-STA-02** — Telegram send, poll, wait, ack, and confirm failures are contained as graph faults and
   do not crash scheduled dispatch.

 ## Determinism & idempotency (`IDM`)
@@ -246,12 +256,16 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   calendar's reason on the fire that wrote the run; `already-placed` on every later fire; `held`
   with the readiness state and the failure count, or, once the action window has passed, that it
   has; `skipped` with the calendar's reason, `operator` for a skip answer, or which side of the
-  action window the fire is on, with the window's times.
+  action window the fire is on, with the window's times. A fire that listens (`DSP-TRG-05`)
+  prints a second line: how long it listened and what came of it.

 ## Performance envelope (`PERF`)

 - **DSP-PERF-01** — Human override placement is bounded to the 22:30-23:10 UTC action window; outside
   that window the dispatcher does not begin a run.
+- **DSP-PERF-02** — While a fire listens, a press is acknowledged within seconds of reaching the
+  bot, inside Telegram's limit of about 15 seconds, and a `run_now` pressed at or before `_ACT_BY`
+  starts the run in that fire, not at the next tick.

 ## Capability declaration (`CAP`)

@@ -282,7 +296,8 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   },
   "telegram": {
     "operations": [
-      "send_notice", "poll_answer", "ack_answer", "confirm_offset", "send_brief", "send_alarm"
+      "send_notice", "poll_answer", "wait_answer", "ack_answer", "confirm_offset", "send_brief",
+      "send_alarm"
     ],
     "access": "injected port"
   }
@@ -346,3 +361,9 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   session's held claims by key. New `DSP-OUT-10`; `DSP-DEP-01` and `CAP` amended for the
   `Position` and `BarrierForecast` reads. `DSP-OUT-09` moves back under Outputs: since v1.4 it
   sat under the Prohibitions heading. 46 / 49 → 47 / 50.
+- v1.9 — S296 (DL-332, work-queue 146): a held fire stays on the operator's bot until shortly
+  before the next fire, so a press is heard, acknowledged and acted on at once. Measured
+  2026-11-28: Telegram drops a press nobody reads within minutes and refuses an acknowledgement
+  about 15 seconds after the press, so a fire that polled once lost most presses (DL-331). New
+  `DSP-TRG-05` and `DSP-PERF-02`; `DSP-STA-02`, `DSP-OBS-04` and `CAP` (`wait_answer`) amended.
+  47 / 50 → 49 / 52.
diff --git a/orchestration/laws/dispatcher/test-plan.md b/orchestration/laws/dispatcher/test-plan.md
index 9b668bce..238b898d 100644
--- a/orchestration/laws/dispatcher/test-plan.md
+++ b/orchestration/laws/dispatcher/test-plan.md
@@ -1,6 +1,6 @@
 # `Dispatcher` — Law Test-Plan

-**Prefix:** `DSP` · **status:** LOCKED v1.8 · **aligned with:** laws.md LOCKED v1.8
+**Prefix:** `DSP` · **status:** LOCKED v1.9 · **aligned with:** laws.md LOCKED v1.9

 | Clause | Description | Test | Status |
 | --- | --- | --- | --- |
@@ -52,5 +52,7 @@
 | DSP-OBS-03 | Each sensor run prints one line: the rows read, the new events, the alarms and how many were told, or the failure. Every alarm and report the sensor kept, and every read, is reconstructable from `ContainerEvent` and `ContainerSensorRead` facts and their `TOLD` edges. | `orchestration/tests/test_container_sensor.py::test_a16_records_every_kept_row_and_tells_seven_alarms`; `orchestration/tests/test_container_vocabulary.py::test_a27_pack_accepts_events_reads_edges_and_failures`; `orchestration/tests/test_container_env.py::test_a25_configured_reader_and_a24_close`; `tests/test_container_sensor_script.py::test_a26_weekend_skip_then_sensor_or_safe_failure` | 🟩 |
 | DSP-OUT-09 | A recent activation with another candidate passed over, or the runs DeliberationRun naming switches, adds one LLM line after containers and before needs-you. Sorted agent types are grouped by distinct choice/passed-over list with chosen vendor/model/effort and reasons; then each run switch followed by during the run. Parts join with the middle-dot separator; neither fact means no line. | `orchestration/tests/test_llm_brief_candidates.py::test_a21_quiet_night_has_no_llm_line`; `test_a22_llm_line_groups_replicas_and_filters_old_or_undated`; `test_a23_llm_line_follows_container_before_needs_you`; `test_a24_real_fire_carries_the_candidate_line`; `orchestration/tests/test_llm_brief_switches.py::test_a19_brief_names_each_switch_in_run_order`; `orchestration/tests/test_llm_brief_switches.py::test_a20_activation_parts_precede_run_switches`; `orchestration/tests/test_llm_brief_switches.py::test_a21_no_switch_means_no_line`; `orchestration/tests/test_llm_brief_switches.py::test_a22_real_fire_carries_the_runs_switch` | 🟩 |
 | DSP-NEV-04 | The dispatcher never holds a run whose day-keyed `RunRequest` exists: a later fire reads no readiness, writes no `RunHold` and sends no hold notice; it reports `already-placed` and, inside the action window, retries only an unsent degraded notice. | `orchestration/tests/test_scheduled_dispatch_once.py::test_a_placed_run_is_never_held_when_a_later_check_fails`; `orchestration/tests/test_scheduled_dispatch_once.py::test_an_override_placed_run_is_already_placed_at_the_next_fire`; `orchestration/tests/test_scheduled_dispatch_once.py::test_an_unsent_degraded_notice_is_retried_inside_the_window_only`; `orchestration/tests/test_scheduled_dispatch_notices.py::test_c5_rehold_after_release_gets_its_own_notice` | 🟩 |
-| DSP-OBS-04 | Each fire prints one line naming what it did and why: `placed` with the calendar's reason, `already-placed` on every later fire, `held` with the readiness state or that the action window has passed, `skipped` with the calendar's reason, the operator, or which side of the action window the fire is on. | `tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did`; `tests/test_dispatch_fire_lines.py::test_a_skip_answer_still_says_operator`; `orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so` | 🟩 |
+| DSP-OBS-04 | Each fire prints one line naming what it did and why: `placed` with the calendar's reason, `already-placed` on every later fire, `held` with the readiness state or that the action window has passed, `skipped` with the calendar's reason, the operator, or which side of the action window the fire is on; a fire that listens prints a second line, how long and what came of it. | `tests/test_hold_listener_job.py::test_a_held_fire_prints_what_it_heard_and_a_placed_one_never_waits`; `tests/test_dispatch_fire_lines.py::test_each_fire_prints_what_it_did`; `tests/test_dispatch_fire_lines.py::test_a_skip_answer_still_says_operator`; `orchestration/tests/test_scheduled_dispatch_once.py::test_a_night_places_the_run_once_and_every_later_fire_says_so` | 🟩 |
 | DSP-OUT-10 | A finished brief whose book holds a name carries the book's lines after the fills: the active Positions by ticker joined to the session's held claims, read by key; one line with no claim, else the names past their declared target (gain now, above target, at their stops) and the odds line (expected target first, stop first, neither; three likelier to stop; four with no forecast). A RED brief has none. | `orchestration/tests/test_book_odds.py::test_the_book_joins_each_held_name_to_its_sessions_claim`; `orchestration/tests/test_book_odds.py::test_a_name_without_a_readable_claim_is_unforecast`; `orchestration/tests/test_book_odds.py::test_nothing_held_is_no_book`; `orchestration/tests/test_book_odds.py::test_the_book_reads_positions_once_and_each_claim_by_key`; `orchestration/tests/test_book_odds.py::test_the_label_and_prefix_are_the_forecasters`; `orchestration/tests/test_book_brief.py::test_the_book_line_totals_the_names_past_their_target`; `orchestration/tests/test_book_brief.py::test_the_odds_line_sums_the_claims_and_names_the_likelier_to_stop`; `orchestration/tests/test_book_brief.py::test_a_book_with_no_claim_says_so_in_one_line`; `orchestration/tests/test_book_brief.py::test_no_name_past_its_target_reads_none`; `orchestration/tests/test_daily_brief_book.py::test_a_finished_brief_carries_the_book_after_its_fills`; `orchestration/tests/test_daily_brief_book.py::test_a_red_brief_carries_no_book`; `orchestration/tests/test_daily_brief_book.py::test_a_malformed_session_names_its_field` | 🟩 |
+| DSP-TRG-05 | A fire that leaves its run held and unanswered stays on the bot until 30 s before the next tick, in long polls of at most 25 s that confirm nothing, at most four per poll the time allows; on a press it records, acknowledges and confirms at once and acts by `_ACT_BY`, after it records only; it stops at the first effective answer, the deadline or a failed wait (a `telegram` Fault); a non-answer update is confirmed; a placed, skipped or answered fire does not listen. | `orchestration/tests/test_hold_listener.py::test_a_held_fire_listens_until_30_s_before_the_next_tick`; `orchestration/tests/test_hold_listener.py::test_an_answer_acts_only_by_the_act_by_time`; `orchestration/tests/test_hold_listener.py::test_a_failed_wait_is_one_fault_and_ends_the_listening`; `orchestration/tests/test_hold_listener.py::test_an_update_that_is_not_an_answer_is_confirmed_and_the_wait_goes_on`; `orchestration/tests/test_hold_listener.py::test_a_stopped_clock_cannot_hold_the_fire`; `orchestration/tests/test_hold_listener.py::test_a_fire_that_is_not_held_or_is_answered_does_not_listen`; `tests/test_hold_listener_job.py::test_the_client_waits_on_one_long_poll_and_confirms_nothing` | 🟩 |
+| DSP-PERF-02 | While a fire listens, a press is acknowledged within seconds of reaching the bot, inside Telegram's limit of about 15 s, and a `run_now` pressed by `_ACT_BY` starts the run in that fire. | `orchestration/tests/test_hold_listener.py::test_a_press_is_recorded_acknowledged_and_acted_on_at_once` | 🟩 |
diff --git a/orchestration/scheduled_dispatch_actions.py b/orchestration/scheduled_dispatch_actions.py
index 602bb726..3be3b85c 100644
--- a/orchestration/scheduled_dispatch_actions.py
+++ b/orchestration/scheduled_dispatch_actions.py
@@ -7,7 +7,7 @@ External I/O: reads and writes the injected GraphStore.

 from __future__ import annotations

-from datetime import UTC, datetime, time
+from datetime import UTC, datetime, time, timedelta
 from typing import TYPE_CHECKING
 from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

@@ -53,6 +53,19 @@ def fire_tick(now: datetime) -> time:
     return time(now.hour, now.minute - now.minute % _TICK_MINUTES)


+def next_tick(now: datetime) -> datetime:
+    """Return the cron tick after the one *now* belongs to: the next fire's tick."""
+    tick = fire_tick(now)
+    return now.replace(hour=tick.hour, minute=tick.minute, second=0, microsecond=0) + (
+        timedelta(minutes=_TICK_MINUTES)
+    )
+
+
+def may_act(now: datetime) -> bool:
+    """Return whether an answer read at *now* may act: by the notice's act-by time."""
+    return _ACTION_START <= now.time() <= _ACT_BY
+
+
 def is_action_time(now: datetime) -> bool:
     """Return whether a dispatcher fire may place a run in the fleet window."""
     return _ACTION_START <= fire_tick(now) <= _ACT_BY
diff --git a/orchestration/telegram_client.py b/orchestration/telegram_client.py
index 556a9e71..800dc2c5 100644
--- a/orchestration/telegram_client.py
+++ b/orchestration/telegram_client.py
@@ -11,7 +11,12 @@ from collections.abc import Callable, Mapping
 from functools import partial

 from orchestration.telegram_http import send_request
-from orchestration.telegram_updates import TelegramAnswer, parse_answer
+from orchestration.telegram_updates import (
+    TelegramAnswer,
+    WaitedUpdates,
+    parse_answer,
+    waited_updates,
+)

 Sender = Callable[[str, dict[str, object], float], object]

@@ -111,6 +116,16 @@ class TelegramClient:
         answers = (parse_answer(update) for update in updates)
         return tuple(answer for answer in answers if answer is not None)

+    def wait_for_updates(self, *, timeout_seconds: int) -> WaitedUpdates | None:
+        """Long-poll for up to *timeout_seconds*; confirm nothing (DSP-TRG-05)."""
+        payload: dict[str, object] = {"timeout": timeout_seconds}
+        response = self._request("getUpdates", payload, waiting=timeout_seconds)
+        updates = response.get("result") if response else None
+        if not isinstance(updates, list):
+            self.last_error = self.last_error or "telegram_response_invalid"
+            return None
+        return waited_updates(updates)
+
     def confirm(self, *, up_to_update_id: int) -> bool:
         """Advance Telegram's cursor without creating local mutable state."""
         return self._request("getUpdates", {"offset": up_to_update_id + 1}) is not None
@@ -126,11 +141,11 @@ class TelegramClient:
         )

     def _request(
-        self, method: str, payload: dict[str, object]
+        self, method: str, payload: dict[str, object], *, waiting: float = 0.0
     ) -> Mapping[str, object] | None:
         self.last_error = ""
         try:
-            response = self._sender(method, payload, self._timeout_seconds)
+            response = self._sender(method, payload, self._timeout_seconds + waiting)
         except Exception as exc:
             self.last_error = type(exc).__name__
             return None
diff --git a/orchestration/telegram_port.py b/orchestration/telegram_port.py
index 9b5ad14c..bd9f7470 100644
--- a/orchestration/telegram_port.py
+++ b/orchestration/telegram_port.py
@@ -10,7 +10,7 @@ from __future__ import annotations
 from typing import TYPE_CHECKING, Protocol

 if TYPE_CHECKING:
-    from orchestration.telegram_updates import TelegramAnswer
+    from orchestration.telegram_updates import TelegramAnswer, WaitedUpdates


 class TelegramPort(Protocol):
@@ -43,3 +43,11 @@ class TelegramPort(Protocol):
     def confirm(self, *, up_to_update_id: int) -> bool:
         """Advance the remote update cursor through one handled update."""
         ...  # pragma: no cover - protocol declaration only.
+
+
+class ListeningTelegramPort(TelegramPort, Protocol):
+    """The dispatcher's port plus the long poll a listening fire waits on."""
+
+    def wait_for_updates(self, *, timeout_seconds: int) -> WaitedUpdates | None:
+        """Wait up to *timeout_seconds* for updates; confirm none (DSP-TRG-05)."""
+        ...  # pragma: no cover - protocol declaration only.
diff --git a/orchestration/telegram_updates.py b/orchestration/telegram_updates.py
index 9caf0d4f..88ce2e6b 100644
--- a/orchestration/telegram_updates.py
+++ b/orchestration/telegram_updates.py
@@ -1,7 +1,8 @@
 """Telegram callback parsing for held-run decisions.

 Agent: orchestration
-Role: convert Telegram update payloads into legal dispatcher answers.
+Role: convert Telegram update payloads into legal dispatcher answers, and say what one
+      long poll returned (DSP-TRG-05).
 External I/O: none.
 """

@@ -41,3 +42,24 @@ def parse_answer(update: object) -> TelegramAnswer | None:
     return TelegramAnswer(
         update["update_id"], cast("Answer", answer), run_id, callback["id"]
     )
+
+
+@dataclass(frozen=True)
+class WaitedUpdates:
+    """What one long poll returned: the newest update id seen, and the legal answers."""
+
+    last_update_id: int
+    answers: tuple[TelegramAnswer, ...]
+
+
+def waited_updates(updates: list[object]) -> WaitedUpdates:
+    """Return the newest update id among *updates*, of any shape, and their answers."""
+    ids = [
+        update["update_id"]
+        for update in updates
+        if isinstance(update, Mapping) and isinstance(update.get("update_id"), int)
+    ]
+    answers = (parse_answer(update) for update in updates)
+    return WaitedUpdates(
+        max(ids, default=0), tuple(answer for answer in answers if answer is not None)
+    )
diff --git a/pyproject.toml b/pyproject.toml
index 1b8bb883..eef8f205 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -1,6 +1,6 @@
 [project]
 name = "trading-agents"
-version = "0.133.00"
+version = "0.133.01"
 description = "An operator-controlled, single-user, agent-based trading system. Domain logic lives only in agents; the kernel is plumbing; contracts are the shared boundary."
 requires-python = ">=3.13"
 dependencies = [
diff --git a/scripts/dispatch_scheduled_run.py b/scripts/dispatch_scheduled_run.py
index 95d32959..3cfe44f3 100644
--- a/scripts/dispatch_scheduled_run.py
+++ b/scripts/dispatch_scheduled_run.py
@@ -1,7 +1,9 @@
 """Scheduled dispatcher entrypoint for Container Apps Jobs.

 Agent: tooling
-Role: load environment, require PostgreSQL, and place or skip today's RunRequest.
+Role: load environment, require PostgreSQL, and place or skip today's RunRequest; while
+      the run is held, stay on the operator's bot until shortly before the next fire
+      (DSP-TRG-05).
 External I/O: environment, PostgreSQL graph, stdout/stderr.

 Run it:
@@ -24,6 +26,7 @@ if str(_ROOT) not in sys.path:
 from dotenv import load_dotenv  # noqa: E402

 from orchestration.container_sensor_guard import sense_from_env  # noqa: E402
+from orchestration.hold_listener import listen_while_held  # noqa: E402
 from orchestration.scheduled_dispatch import (  # noqa: E402
     CalendarWindowExceededError,
     ScheduledDispatchResult,
@@ -82,13 +85,17 @@ def _dispatch(argv: list[str] | None) -> int:

     try:
         graph = _live_graph()
+        telegram = _telegram()
         try:
             result = dispatch_with_human_answer(
-                graph,
-                as_of=as_of,
-                now=datetime.now(tz=UTC),
-                telegram=_telegram(),
+                graph, as_of=as_of, now=_now(), telegram=telegram
             )
+            print(format_dispatch_result(result))
+            if result.action == "held":
+                heard = listen_while_held(
+                    graph, as_of=as_of, telegram=telegram, clock=_now
+                )
+                print(heard.line())
         finally:
             close = getattr(graph, "close", None)
             if callable(close):
@@ -102,11 +109,13 @@ def _dispatch(argv: list[str] | None) -> int:
             file=sys.stderr,
         )
         return 1
-
-    print(format_dispatch_result(result))
     return 0


+def _now() -> datetime:
+    return datetime.now(tz=UTC)
+
+
 def _as_of_date(raw: str) -> date:
     if raw:
         return date.fromisoformat(raw)
diff --git a/scripts/run_hold_drill.py b/scripts/run_hold_drill.py
index ac99f503..7f1958e7 100644
--- a/scripts/run_hold_drill.py
+++ b/scripts/run_hold_drill.py
@@ -3,13 +3,13 @@
 Agent: tooling
 Role: work-queue 120 (a) (DL-330): read the env file without loading it, refuse an
       unsafe start, then run two rounds of the dispatcher's own fire on an in-memory
-      graph (Run now, then Skip today) and print what each round sent, recorded and did.
+      graph (Run now, then Skip today), each listening for the press as the fleet does
+      (DL-332), and print what each round sent, heard, recorded and did.
 External I/O: reads the env file; Telegram's Bot API as the test bot; stdout.

 Run it from the main checkout, which holds the only .env:
   .venv/Scripts/python.exe scripts/run_hold_drill.py
-  .venv/Scripts/python.exe scripts/run_hold_drill.py --poll-seconds 300
-The second form answers a press as late as the fleet's ten-minute fires can.
+A round listens until 30 s before its next tick, about nine and a half minutes.
 Exit code: 0 when both rounds pass, 1 when one does not, 2 when refused.
 """

@@ -21,10 +21,6 @@ import sys
 import time
 from datetime import UTC, datetime
 from pathlib import Path
-from typing import TYPE_CHECKING
-
-if TYPE_CHECKING:
-    from collections.abc import Callable

 _ROOT = Path(__file__).resolve().parents[1]
 if str(_ROOT) not in sys.path:
@@ -53,15 +49,13 @@ def main(argv: list[str] | None = None) -> int:
     from orchestration.telegram_client import TelegramClient

     print(
-        f"HOLD DRILL  test bot {bot_id(values.bot_token)}, a poll every "
-        f"{args.poll_seconds} s, at most {args.wait_minutes} min a round"
+        f"HOLD DRILL  test bot {bot_id(values.bot_token)}, listening as the fleet "
+        "does: until 30 s before the next tick"
     )
     drill = Drill(
         telegram=TelegramClient(api_token=values.bot_token, chat_id=values.chat_id),
         settings=OrchestratorSettings(_env_file=None),
-        poll_seconds=args.poll_seconds,
-        wait_seconds=args.wait_minutes * 60,
-        sleep=_sleep,
+        elapsed=_elapsed,
         report=print,
     )
     passed = run_drill(drill, today=now.date())
@@ -73,29 +67,13 @@ def _now() -> datetime:
     return datetime.now(tz=UTC)


-def _sleep(seconds: float) -> None:
-    time.sleep(seconds)
-
-
-def _bounded(low: int, high: int) -> Callable[[str], int]:
-    def parse(raw: str) -> int:
-        value = int(raw)
-        if not low <= value <= high:
-            raise argparse.ArgumentTypeError(f"must be {low} to {high}")
-        return value
-
-    return parse
+def _elapsed() -> float:
+    return time.monotonic()


 def _parser() -> argparse.ArgumentParser:
     parser = argparse.ArgumentParser(description="the hold drill on a test bot")
     parser.add_argument("--env-file", default=".env", help="the env file to read")
-    parser.add_argument(
-        "--poll-seconds", type=_bounded(1, 600), default=5, help="seconds between polls"
-    )
-    parser.add_argument(
-        "--wait-minutes", type=_bounded(1, 30), default=10, help="wait for each press"
-    )
     return parser


diff --git a/uv.lock b/uv.lock
index a2d99c22..b76e3f9e 100644
--- a/uv.lock
+++ b/uv.lock
@@ -3669,7 +3669,7 @@ wheels = [

 [[package]]
 name = "trading-agents"
-version = "0.133.0"
+version = "0.133.1"
 source = { virtual = "." }
 dependencies = [
     { name = "cryptography" },
```

---

## Appendix C — the 19 breaks, as exact replacements

Each break replaces the first text with the second in the file named, once; the named test must then
fail. Restore with `git checkout -- <file>` before the next. The planner's script
(`s296_breaks.py`, kit) applies exactly these.

**L** = `orchestration/tests/test_hold_listener.py`, **J** = `tests/test_hold_listener_job.py`,
**D** = `orchestration/tests/test_hold_drill.py`, **C** = `tests/test_run_hold_drill_cli.py`;
B16's test is the existing `tests/test_dispatch_scheduled_run.py::test_dispatcher_image_copies_everything_its_entrypoint_imports`.

| # | File | Replace | With | Must fail |
| --- | --- | --- | --- | --- |
| B1 | `orchestration/hold_listener.py` | `LISTEN_MARGIN = timedelta(seconds=30)` | `LISTEN_MARGIN = timedelta(seconds=0)` | L1 |
| B2 | the same | `WAIT_SECONDS = 25` | `WAIT_SECONDS = 50` | L1 |
| B3 | the same | `WAITS_PER_POLL = 4` | `WAITS_PER_POLL = 40` | L6 |
| B4 | the same | the failed wait's `return _heard(start, clock(), "stopped, the wait failed (a telegram Fault)")` | `continue` | L4 |
| B5 | the same | `if waited.answers:` | `if False:` | L2 |
| B6 | the same | in `_act`, `if not may_act(now):` | `if False:` | L3 |
| B7 | the same | `if waited.last_update_id:` | `if False:` | L5 |
| B8 | the same | in `_unanswered`, `return held and effective_answer(graph, run_id=run_id) is None` | `return held` | L7 |
| B9 | `orchestration/scheduled_dispatch_actions.py` | in `next_tick`, `timedelta(minutes=_TICK_MINUTES)` | `timedelta(minutes=2 * _TICK_MINUTES)` | L1 |
| B10 | the same | in `may_act`, `return _ACTION_START <= now.time() <= _ACT_BY` | `return is_action_time(now)` (the tick, not the clock) | L3 |
| B11 | `orchestration/telegram_client.py` | `payload: dict[str, object] = {"timeout": timeout_seconds}` | `payload: dict[str, object] = {}` | J1 |
| B12 | the same | `self._request("getUpdates", payload, waiting=timeout_seconds)` | `self._request("getUpdates", payload)` | J1 |
| B13 | `orchestration/telegram_updates.py` | in `waited_updates`, `max(ids, default=0), tuple(` | `0, tuple(` | J1 |
| B14 | `scripts/dispatch_scheduled_run.py` | `if result.action == "held":` | `if False:` | J3 |
| B15 | the same | `if result.action == "held":` | `if True:` | J3 |
| B16 | `orchestration/Dockerfile` | the line `COPY orchestration/hold_listener.py orchestration/hold_listener.py` | deleted | the image test |
| B17 | `orchestration/hold_drill.py` | in `_planted_clock`, `return lambda: start + timedelta(seconds=drill.elapsed() - origin)` | `return lambda: start` | D2 |
| B18 | `orchestration/hold_drill_verdict.py` | the line `f"listen    {heard}",` | deleted | D2 |
| B19 | `scripts/run_hold_drill.py` | the `--env-file` argument line in `_parser` | the same, followed by `parser.add_argument("--poll-seconds", type=int, default=5)` and `parser.add_argument("--wait-minutes", type=int, default=10)` | C5 |

The byte-exact replacements are the planner's `s296_breaks.py` (kit `wq120-2026-11-28/`), which plants
each, runs the five test files, and prints every test that failed.
