<!-- Agent: planning | Role: sprint handover -->
# Sprint 295 — a held run reaches the operator on Telegram and their answer comes back

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-295-a-held-run-reaches-the-operator-and-the-answer-comes-back`
**Status:** MERGED 2026-11-28 — `0.133.00`, fast-forwarded to `9d7e2bf3`, tag `v0.133.00`, GATE PROVEN; F1 2026-11-28: (a) and (c) PASS, (b) VERIFIED FAILING on a fleet defect (work-queue 146, DL-331); no deploy
**Version:** *next available MINOR at merge* (the prototype measured `0.133.00`)
**Effort:** S
**Decisions:** [DL-330](../design-log.md) (this sprint's six decisions, made and measured) · [DL-328](../design-log.md) (the test lane: no fleet secret in a test) · [work-queue 120](../work-queue.md) part (a)

> **Why this bump kind.** A new capability: a drill that runs the dispatcher's hold path for real,
> through a Telegram bot of its own, which nothing in the repository could do before. A MINOR.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `orchestration/laws/dispatcher/laws.md` | The dispatcher's **locked constitution** (`DSP`, v1.8): holds, answers, notices | **Read-only.** The drill calls the dispatcher's fire unchanged; no dispatcher file changes |
| `orchestration/laws/dispatcher/test-plan.md` | Which `DSP` clauses are proven | Read it with `laws.md`; this sprint proves none and cites none |
| `docs/laws/conventions.md` | Module headers, test docstrings, clause citations | Binds every new file's header and every test's docstring |
| `docs/laws/drift-register.md` | Where a law found wrong or silent is recorded | The one law-adjacent file you may append to; this sprint expects no row |

Binding: the dispatcher's **`DSP-IN-04`** (answers are `run_now` or `skip_today` for the matching run),
**`DSP-OUT-03`** and **`DSP-OUT-05`** (one hold, one notice with exactly the two buttons),
**`DSP-ORD-02`** (the first answer decides), **`DSP-STA-02`** and **`DSP-FAIL-01`** (a Telegram failure is
a fault, never a crash), **`DSP-SEC-01`** (the token lives in the injected port). The drill relies on
each and changes none.

### The rule

1. **Before writing code**, read `orchestration/laws/dispatcher/laws.md` and its `test-plan.md`,
   [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md), whole.
2. Read [DL-330](../design-log.md), whole, and DL-328's *Decided* list.
3. **Answer the law-cycle question below** in the Law reading record.
4. **Write the Law reading record** (bottom of this file) **before** your first change.
5. **If a law contradicts this spec, STOP and report.**
6. Every new test cites the DL-330 decision it proves (`D1` to `D5`) in its docstring. **Cite no `DSP`
   clause ID:** those clauses are proven by the dispatcher's own tests, and a citation here would move
   the law-coverage rollup.

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No.** No file in `contracts/`, `kernel/` or `agents/` changes, and no dispatcher file changes. The
sprint adds tooling in `orchestration/` and `scripts/` that runs the dispatcher's own fire on an
in-memory graph; its properties (a test bot only, never inside the fleet's window) are DL-330's
tooling decisions, not a guarantee the dispatcher makes. No law cycle is owed.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/hold_drill.py`, `hold_drill_verdict.py` (new) | `orchestration/laws/dispatcher/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | They call `dispatch_with_human_answer` and read the `RunHold`, `RunHoldAnswer`, `RunRequest` and `Fault` facts it writes (`DSP-OUT-03`, `DSP-OUT-05`, `DSP-ORD-02`, `DSP-STA-02`) |
| `orchestration/hold_drill_guard.py` (new) | the same; DL-328 | `DSP-SEC-01`; DL-328's rule that a test holds no fleet secret |
| `scripts/run_hold_drill.py` (new) | `docs/laws/conventions.md`; DL-330 | The module header; D1 and D5 |
| the four new test files | `docs/laws/conventions.md` | Module headers; each test cites its DL-330 decision |

⚠️ **One invariant.** No existing file changes but `pyproject.toml` and `uv.lock` (one line each). The
drill drives `orchestration/scheduled_dispatch_human.py::dispatch_with_human_answer` and
`orchestration/telegram_client.py::TelegramClient` exactly as the fleet's job does. If your change would
edit any dispatcher, Telegram or existing test file, stop and report.

---

## Goal

At merge, `scripts/run_hold_drill.py`, run from the main checkout, reads `TELEGRAM_TEST_BOT_TOKEN` and
`TELEGRAM_CHAT_ID` from the env file without loading it and refuses to start when either is missing,
when the token is not a bot token, when the test bot is the fleet's, or inside 22:00 to 24:00 UTC. Then,
for each of the two NYSE sessions before today, on an in-memory graph, it plants a failing fleet
preflight and fires the dispatcher's unchanged `dispatch_with_human_answer` at 22:30:05 and then at
22:40:05 UTC on that date: the run is held, one notice with *Run now* and *Skip today* reaches the
operator through the test bot, and the operator's press is recorded from Telegram, acknowledged, past
the cursor, and acted on. The first round asks for *Run now* and must place the run; the second asks for
*Skip today* and must skip it. Exit 0 when both pass, 1 when one does not, 2 when refused.

## Why (context)

Work-queue 120 (a). When a fleet check fails, the dispatcher holds the night's run and sends the
operator a Telegram notice with two buttons; their press, read back at the next ten-minute fire, decides
whether the run starts. It is the one place where the fleet asks a human, and it has never run for real:
the live graph holds 0 `RunHold` and 0 `RunHoldAnswer`, and the proof of S217 to S219 was a healthy fleet
producing silence. Its first real use would be on a night when something is already wrong. The drill
runs that path, end to end on Telegram, at a time the operator chooses, without touching the fleet.

### Measured, 2026-11-28 — read these before designing

Kit OneDrive `trading-agents-data/wq120-2026-11-28/`. Live reads are read-only; no value is printed.

| Claim | Value | How it was measured |
| --- | --- | --- |
| Holds on the live graph | 0 `RunHold`, 0 `RunHoldAnswer`; 8 of 327 `FleetPreflight` failed, none the newest at a placing fire | *[measured]* read-only SQL on the live graph, main checkout |
| What a real failure reads like | `transient:execution:alpaca-broker:TimeoutError`, `transient:provider:finnhub:TimeoutError` (kind, agent, check, reason) | *[measured]* the same read |
| Which agents a failure may name and still let a run go | `operator` only (a degraded run); any other agent reads `failing` | *[read]* `orchestration/packs/trading_run_postures.json`; `orchestration/fleet_readiness.py` |
| The dispatcher's fire, in memory, with a scripted Bot API | fire at 22:30:05: `held`, one `sendMessage` with buttons `run_now:sched-2026-11-27` and `skip_today:sched-2026-11-27`; a second fire: no second notice; after a press: `getUpdates`, `answerCallbackQuery` (`Answer recorded`), `getUpdates` with `offset` = the update id + 1; `placed`, 99 tickers (or `skipped reason=operator`); 0 Faults | *[measured]* `measure_fire.py` → `measure_fire.txt`, the unchanged `dispatch_with_human_answer` and the real `TelegramClient` |
| The run id a hold uses | always `sched-<as_of>` | *[read]* `orchestration/scheduled_dispatch.py::scheduled_run_id` |
| Which presses a fire records | every legal `run_now` / `skip_today` press, whatever run it names | *[read]* `orchestration/scheduled_dispatch_polling.py::poll_answers` |
| How long Telegram keeps an unread update | up to 24 hours; a `getUpdates` with an offset confirms every update below it | *[read]* Bot API docs, `getUpdates` |
| The fleet's bot | no webhook, 0 pending updates; `.env` holds `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` only; the chat id is positive (a private chat) | *[measured]* read-only `getMe` and `getWebhookInfo`, names and shapes only |
| The two sessions before 2026-11-28 | 2026-11-27 and 2026-11-25 (2026-11-26 is Thanksgiving) | *[measured]* `is_trading_session`, in `measure_fire.txt` |
| Whether a brief can fire in a drill | no: within a fire the brief runs before the act, when no RunRequest exists, and the drill fires no more after the act | *[read]* `orchestration/scheduled_dispatch_human.py`, `orchestration/daily_brief.py::attempt_brief` |
| Whether the lane's graph can take a drill | no: `GraphStore` has no delete, and a *Run now* places `run-request:sched-<date>`, after which `run_lane.py` refuses the branch | *[read]* `kernel/graph.py`; DL-328 |
| What a refused notice's Fault says | `telegram_message_id_missing`, not Telegram's refusal: `send_hold_notice` overwrites the transport's `telegram_response_invalid` | *[measured]* the prototype's `test_a_notice_telegram_refuses_fails_the_round_at_once`; work-queue 145 |
| How late Telegram accepts an acknowledgement | not documented; third-party sources say about 10 to 15 seconds | *[ASSUMED, not measured]* the fleet acknowledges at its next ten-minute fire; F1 (b) measures what that does |
| The prototype | the new tests fail to collect on the unchanged tree (3 errors) and 30 pass after; 21 planted breaks red; `make ci` exit 0 | *[measured]* `proto-s295` (never pushed); Appendix B, Appendix C, Closeout of the planner's prototype below |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first.** Four new files under the Test plan's exact names:
   `orchestration/tests/hold_drill_fakes.py` (the fake Bot API), `orchestration/tests/test_hold_drill_guard.py`,
   `orchestration/tests/test_hold_drill.py`, `tests/test_run_hold_drill_cli.py`. On the unchanged tree
   the three test files fail to collect (3 errors).
2. **The change.** Apply Appendix B exactly: four new files (`orchestration/hold_drill.py`,
   `orchestration/hold_drill_guard.py`, `orchestration/hold_drill_verdict.py`,
   `scripts/run_hold_drill.py`) and one line each of `pyproject.toml` and `uv.lock`.
3. **The handback** at the bottom of this file, and this sprint's row of [`README.md`](README.md).

### Out of scope (do NOT build this sprint)

- **Any dispatcher or Telegram file.** `scheduled_dispatch*.py`, `hold_answers.py`, `telegram_*.py` stay
  as they are; the drill proves them as they are.
- **The refused-notice Fault text** (work-queue 145). The drill prints the Fault as the fleet writes it.
- **A test bot, a token, or any live call.** The operator creates the bot after the merge; the build is
  proven on the fake Bot API alone.
- **Work-queue 120 (b)**, commands typed from the phone.
- **Any other file.** No `laws.md` edit, no ADR, no design-log entry (DL-330 is written), no `.env.example`
  line (S293's test names are not in it either).

### The road not taken (LAW-06)

- **The fleet's bot.** Rejected: a press the drill leaves unread stays in the fleet bot's queue up to 24
  hours, and the fleet's next hold records it into the live graph; for the same run id it would act on
  it. And a test holds no fleet secret (DL-328).
- **The lane's Neon graph.** Rejected: a *Run now* leaves a RunRequest the lane then refuses, and the
  graph has no delete.
- **Driving `TelegramClient` directly.** Rejected: it proves the client, not the path from hold to act.
- **The real clock, or future sessions.** Rejected: the placing window is inside the fleet's own, and a
  notice naming tonight's run could pass for a real hold.
- **A drill wording inside the notice.** Rejected: that changes the fleet's notice; the drill sends its
  own plain message before each notice instead.
- **The fleet's ten-minute cadence by default.** Rejected: the operator would wait up to ten minutes a
  round; `--poll-seconds 300` is the faithful form, used by F1 (b).

---

## The design decisions — made, and recorded in DL-330

**Nothing is left for the builder to decide.** Do not add a design-log entry.

1. **D1** — a test bot of the operator's own: `TELEGRAM_TEST_BOT_TOKEN` and `TELEGRAM_CHAT_ID`, read
   from the env file, never loaded; refused when missing, when not `<digits>:<key>`, or when its bot id
   equals the fleet `TELEGRAM_BOT_TOKEN`'s (from the file or the environment). No repr or printed line
   holds the token.
2. **D2** — an in-memory graph; no Postgres, feed, broker or model.
3. **D3** — the dispatcher's own fire, unchanged, on the two NYSE sessions before today: a failing
   `FleetPreflight` at 22:25 UTC (`transient:execution:alpaca-broker:hold-drill`), the first fire at
   22:30:05, every later fire at 22:40:05; a plain drill message before each notice names the button.
4. **D4** — *Run now* on the newer session, then *Skip today*; a round passes on the notice sent, the
   asked answer recorded from Telegram, the act (placed with one RunRequest, or skipped `operator` with
   none) and no unconfirmed answer for the run; faults printed, not judged; a press waiting before the
   notice is confirmed away; no press within the wait fails the round.
5. **D5** — refused inside 22:00 to 24:00 UTC; exit 0, 1 or 2; `--poll-seconds` 1 to 600 (default 5),
   `--wait-minutes` 1 to 30 (default 10); no env-file name enters the process environment.
6. **D6** — MINOR; both version lines are in Appendix B; `uv lock` is not run; no deploy.

---

## Blast radius — measured 2026-11-28

| What | Detail |
| --- | --- |
| Files changed | New: `orchestration/hold_drill.py` (131 lines), `orchestration/hold_drill_guard.py` (78), `orchestration/hold_drill_verdict.py` (77), `scripts/run_hold_drill.py` (103), and the four test files (95, 91, 134, 131 on the prototype). One line each: `pyproject.toml`, `uv.lock`. This spec; `docs/sprints/README.md` |
| Agents affected | none. The drill imports `agents.provider.domain.market_calendar`, as `scheduled_dispatch.py` does; no agent file changes |
| Contract change? | no |
| Graph vocabulary change? | no. The drill writes only in memory, with the labels the dispatcher already writes |
| New env keys / tunables | `TELEGRAM_TEST_BOT_TOKEN`, read by the drill from the main checkout's `.env` only; never a fleet setting. No tunable |
| Deploy implication | none. The merge builds images (`pyproject.toml`, `uv.lock` and `orchestration/` are build paths); the new modules ship unused in the orchestration image |
| Rollback | revert the commit. Nothing live changes: no graph write, no order, no setting, no fleet secret |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Plant the failing tests first** (Test plan) and run them on the unchanged tree:
   `uv run --no-sync pytest orchestration/tests/test_hold_drill_guard.py orchestration/tests/test_hold_drill.py tests/test_run_hold_drill_cli.py --no-cov -q -p no:cacheprovider`.
   Paste the output: **3 errors during collection** on the planner's prototype.
3. **Apply Appendix B**, exactly, and check the six blob ids it gives.
4. **Run the same command again: 30 passed.**
5. **Prove the guards can fail (DL-70):** the 21 breaks of Appendix C, one at a time, each red on the
   test named for it, each restored before the next.
6. **`make ci` green**, every step of the `ci:` target (count them from the `Makefile`),
   **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Four files, under **exactly these names** (the planner's break script judges by them). Each file's
docstring declares `Agent:` (`orchestration` for the three under `orchestration/tests/`, `tooling` for
the CLI test), a `Role:` and `External I/O: none` (the CLI test: temporary env files and a fake Bot
API). Each test's docstring cites its DL-330 decision. No test makes a network call, sleeps, or reads
an actual `.env`.

**`orchestration/tests/hold_drill_fakes.py`** (no tests of its own) provides:

- `TODAY = date(2026, 11, 28)`, `SAFE_NOW = datetime(2026, 11, 28, 6, 0, tzinfo=UTC)`,
  `TEST_BOT_VALUE = "7000000001:test-drill-key"` and `FLEET_BOT_VALUE = "8000000002:fleet-key"`, each
  of the last two followed by `# pragma: allowlist secret`. 🪤 Do not name a constant `*TOKEN*`: ruff's
  S105 reads it as a password.
- `FakeBot(*, send_ok=True, ack_ok=True, confirm_ok=True)`, a callable `(method, payload, timeout)`
  used as `TelegramClient(..., sender=bot)`, behaving as the Bot API does: `sendMessage` records
  `(text, [callback_data of each button])` in `bot.sent` and returns `{"ok": True, "result":
  {"message_id": 100 + len(bot.sent)}}` (or `{"ok": False, ...}` when `send_ok` is false);
  `getUpdates` with an `offset` drops every update whose id is below it (returns `{"ok": False, ...}`
  instead when `confirm_ok` is false), and with or without one returns `{"ok": True, "result": <the
  updates left>}`; `answerCallbackQuery` records the callback id in `bot.acks` and returns ok (not ok
  when `ack_ok` is false). `bot.press(answer, run_id)` queues `{"update_id": <rising from 501>,
  "callback_query": {"id": "cb<update id>", "data": "<answer>:<run_id>"}}`. `bot.notices()` returns
  the sent messages that carry buttons.
- `drill_on(bot, presses, lines, *, wait=30)` returns `(drill, slept)`: a `Drill` on the real
  `TelegramClient(api_token=TEST_BOT_VALUE, chat_id="42", sender=bot)`,
  `OrchestratorSettings(_env_file=None)`, `poll_seconds=5`, `wait_seconds=wait`, `report=lines.append`,
  and a `sleep` that appends its argument to `slept` and then makes the next press of `presses`, if any.

In the tables, `R1` is `sched-2026-11-27` (session `D1`, 2026-11-27) and `R2` is `sched-2026-11-25`
(`D2`, 2026-11-25).

**`orchestration/tests/test_hold_drill_guard.py`** (12 cases). `GOOD` is
`{"TELEGRAM_TEST_BOT_TOKEN": f" {TEST_BOT_VALUE} ", "TELEGRAM_CHAT_ID": " 42 "}`.

| # | Test | Must prove |
| --- | --- | --- |
| G1 | `test_each_missing_drill_value_is_named` | a blank test token and no chat id: `DrillRefusedError` matching `TELEGRAM_TEST_BOT_TOKEN, TELEGRAM_CHAT_ID`; `GOOD` with the chat id `None`: matching `missing drill values: TELEGRAM_CHAT_ID$`. D1 |
| G2 | `test_a_value_that_is_not_a_bot_token_is_refused`, parametrized over `no-colon`, `:key`, `abc:key`, `12 3:key` | `bot_id(token) == ""`, and `drill_values` raises matching `is not a bot token`. D1 |
| G3 | `test_the_fleets_bot_is_refused_under_any_key`, two cases: the file holds `TELEGRAM_BOT_TOKEN = "7000000001:a-regenerated-key"` (same bot id, another key); the environment holds `TELEGRAM_BOT_TOKEN = TEST_BOT_VALUE` and the file none | each raises matching `is the fleet's bot`. D1 |
| G4 | `test_a_start_inside_the_fleets_window_is_refused`, over 21:59:59, 22:00:00, 23:59:59 and 00:00:00 UTC on 2026-11-27, the environment holding the fleet's `FLEET_BOT_VALUE` | the two inside raise matching `fleet's nightly window`; the two outside return `DrillValues(TEST_BOT_VALUE, "42")` (stripped). D5 |
| G5 | `test_the_values_never_print_the_token` | the values hold `(TEST_BOT_VALUE, "42")`; `repr(values) == "DrillValues()"`; `bot_id(values.bot_token) == "7000000001"`. D1 |

**`orchestration/tests/test_hold_drill.py`** (10 cases), each on a fresh `FakeBot` and `drill_on`.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| D1 | `test_the_two_sessions_are_the_last_before_today` | — | `prior_sessions(TODAY, 2) == (D1, D2)` and `prior_sessions(D1, 1) == (D2,)`. D3 |
| D2 | 🎯 `test_run_now_is_recorded_from_telegram_and_places_the_run` | a *Run now* press for `R1` at the first sleep | `run_round(drill, as_of=D1, wanted="run_now")` is true; the first message sent ends `Next message: press Run now.`; exactly one notice, its text starting `Run sched-2026-11-27 is held. Checks: ` and holding `transient:execution:alpaca-broker:hold-drill`, its buttons `[run_now:R1, skip_today:R1]`; the report lines are exactly `R1  held, notice 102: Run now`, `R1  PASS`, `  answer    run_now from telegram`, `  act       placed reason=NYSE trading session, RunRequest 1`, `  cursor    confirmed`, `  faults    0`; `bot.acks == ["cb501"]`; no update left; `slept == [5]`. D3, D4 |
| D3 | 🎯 `test_skip_today_is_recorded_from_telegram_and_skips_the_run` | a *Skip today* press for `R2` | true; lines 2 to 4 are `R2  PASS`, `  answer    skip_today from telegram`, `  act       skipped reason=operator, RunRequest 0`. D4 |
| D4 | `test_the_other_button_fails_the_round_and_is_still_acted_on` | a *Run now* press for `R2`, asked `skip_today` | false; lines 2 to 4 are `R2  FAIL`, `  answer    run_now from telegram, asked skip_today`, `  act       placed reason=NYSE trading session, RunRequest 1`. D4 |
| D5 | `test_no_press_fails_the_round_after_the_wait` | no press, `wait=12` | false; `slept == [5, 5, 5]`; the last two lines `R1  FAIL`, `  no answer in 15 s`; exactly one notice. D4 |
| D6 | `test_a_notice_telegram_refuses_fails_the_round_at_once` | `FakeBot(send_ok=False)` | false; `slept == []`; the lines are exactly `R1  FAIL`, `  notice not sent (held) (telegram: telegram_message_id_missing)`. D4 |
| D7 | 🪤 `test_a_press_waiting_before_the_notice_does_not_count` | a *Run now* press for `R1` queued before `drill_on`; no press after; `wait=5` | false; the last line `  no answer in 5 s`; no update left; no acknowledgement. D4 |
| D8 | `test_a_late_acknowledgement_is_a_fault_not_a_failure` | `FakeBot(ack_ok=False)`, a *Run now* press | true; the last line `  faults    1 (telegram: telegram_response_invalid)`. D4 |
| D9 | `test_a_cursor_left_behind_fails_the_round` | `FakeBot(confirm_ok=False)`, a *Run now* press | false; the lines hold `  cursor    1 answer(s) still pending`. D4 |
| D10 | `test_the_drill_asks_run_now_then_skip_today_and_says_when_done` | presses *Run now* for `R1`, then *Skip today* for `R2` | `run_drill(drill, today=TODAY) == (True, True)`; the notices' first buttons are `run_now:R1`, `run_now:R2`, in that order; the last message sent is `("Hold drill done: 2 of 2 rounds passed.", [])`; the verdict lines are `R1  PASS`, `R2  PASS`. D4 |

**`tests/test_run_hold_drill_cli.py`** (8 cases). It imports the script as
`from scripts import run_hold_drill as cli` (as `tests/test_run_lane_cli.py` imports `run_lane`). A
fixture `bot` monkeypatches `orchestration.telegram_client.send_request` with a function that records
the token of every call and passes the rest to one `FakeBot`, and sets `cli._now` to return `SAFE_NOW`;
presses are made by monkeypatching `cli._sleep`. Env files are written under `tmp_path`.

| # | Test | Must prove |
| --- | --- | --- |
| C1 | `test_a_refused_start_exits_2_and_calls_no_bot` | an env file with only `TELEGRAM_CHAT_ID`: `cli.main(["--env-file", env]) == 2`, stdout exactly `REFUSED: missing drill values: TELEGRAM_TEST_BOT_TOKEN\n`, no Bot API call. D1, D5 |
| C2 | 🎯 `test_both_rounds_passing_exit_0` | both presses, `--wait-minutes 1`: exit 0; the first line `HOLD DRILL  test bot 7000000001, a poll every 5 s, at most 1 min a round`, the last `HOLD DRILL  2 of 2 rounds passed`. D5 |
| C3 | `test_a_failed_round_exits_1` | only the *Run now* press, `--poll-seconds 30 --wait-minutes 1`: exit 1; the last line `HOLD DRILL  1 of 2 rounds passed`. D5 |
| C4 | 🪤 `test_the_env_file_is_read_not_loaded` | an env file that also holds `TELEGRAM_BOT_TOKEN=FLEET_BOT_VALUE` and `POSTGRES_DSN=postgresql://planted@fleet.invalid/live`, both presses: exit 0; `dict(os.environ)` after equals it before; every Bot API call carried `TEST_BOT_VALUE`. D1, D5 |
| C5 | `test_a_poll_outside_its_bounds_is_refused`, over `--poll-seconds 0`, `--poll-seconds 601`, `--wait-minutes 0`, `--wait-minutes 31` | `SystemExit` with code 2, and stderr holds `must be 1 to`. D5 |

---

## Success factors

- [x] The six files of Appendix B carry its blob ids.
- [x] A start is refused for a missing value, a non-token, the fleet's bot, or inside the fleet's window: G1 to G5, C1.
- [x] Each round holds a past session, sends one notice with both buttons, records the press from Telegram, and places or skips as asked: D1 to D3, D10.
- [x] A round fails on the other button, on no press, on a refused notice, and on a cursor left behind; a waiting press does not count; a refused acknowledgement is a printed fault: D4 to D9.
- [x] The CLI exits 0, 1 or 2 as stated, reads its env file without loading it, and bounds its two numbers: C1 to C5.
- [x] The four test files exist under the names given; the three test files were seen failing first, then all 30 cases pass.
- [x] The law-cycle answer and the reading record are filled before the first change.
- [x] Each of the 21 breaks was planted, seen red on its named test, and restored.
- [x] Every new module under 200 lines (under 150 on the prototype).
- [ ] `make ci` exit 0, 100.00 % coverage; a step the sandbox cannot run is named "not done".

---

## Traps

🪤 **Do not run `uv lock` or `uv sync`, in any form.** The lock was written by a newer `uv`; it changes
in **one line**, given in Appendix B (`0.132.1` → `0.133.0`, the lock's normalised form).

🪤 **The notice's Fault text is the fleet's, not what you would expect.** A refused `sendMessage` leaves
`telegram_message_id_missing` (`send_hold_notice` overwrites the transport's error). D6 pins that text;
do not "fix" `telegram_client.py` (work-queue 145).

🪤 **D7 is the only guard against a stale press.** Without the drain, a press left from an earlier drill
would pass a round no one answered (break B8).

🪤 **The planted failure must name a non-degradable agent.** A failure on `operator` makes the run
degraded and placed, with no hold (break B14).

🪤 **Tests never sleep.** The drill's `sleep` is injected; the CLI's is `cli._sleep`. A real sleep in a
test is a defect even if it passes.

🪤 **Patch `orchestration.telegram_client.send_request`, not `orchestration.telegram_http.send_request`.**
`TelegramClient` binds the name from its own module when it is built.

🪤 **Apply the diff; do not retype.** The blob ids catch a single different byte.

🪤 **`ruff format` runs as a pre-commit hook.** Run `uv run --no-sync ruff format` on the test files
before committing. No `# noqa`.

🪤 **Paste step lines and verdicts into the Closeout, not the whole `make ci` log.**

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150), tests included. No `# noqa`.
  📌 Prototype sizes: `orchestration/hold_drill.py` **131**, `hold_drill_guard.py` **78**,
  `hold_drill_verdict.py` **77**, `scripts/run_hold_drill.py` **103**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers in code: the clocks, the failure text and the CLI's bounds are named in Appendix B;
  the tokens and run ids in the tests are test data.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it, both from Appendix B.
- Secrets never through the worktree. The worktree has **no `.env`** and this sprint needs none; the
  tokens in the tests are invented. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. The planner re-measures: the six blobs against Appendix B; the planner's four test files run in place
   of the builder's; the break script against the builder's test files (21 breaks); the branch pushed;
   **`make gate-ran` exits 0** from `../ta-s295`, its SHA checked against `git rev-parse HEAD`; the open
   CodeQL alerts set-diffed against the baseline of 138.
2. Merge to `main`, tag. **Post-merge CodeQL** checked on `main`.
3. **The operator, once (two minutes):** create a bot with Telegram's `@BotFather`, press Start in it,
   and give its token (by chat, or straight into the main checkout's `.env` as
   `TELEGRAM_TEST_BOT_TOKEN`). The planner checks it read-only (`getMe`: a bot id other than the
   fleet's).
4. **F1, from the main checkout, outside 22:00 to 24:00 UTC, with the operator at their phone:**
   (a) `.venv/Scripts/python.exe scripts/run_hold_drill.py`: the operator presses *Run now* on the first
   notice and *Skip today* on the second; exit 0, both rounds `PASS`, `faults 0`. (b) The same with
   `--poll-seconds 300`: both rounds `PASS`; the `faults` lines measure what an acknowledgement minutes
   after the press does, as the fleet's would be. (c) A copy of the env file outside the repository with
   `TELEGRAM_TEST_BOT_TOKEN` set to the fleet's token: `REFUSED: ... is the fleet's bot`, exit 2, nothing
   sent; the copy deleted. After each: the test bot's `getWebhookInfo` reads 0 pending updates.
5. **No deploy.** Work-queue 120 (a) closes at F1; (b) stays open. If F1 (b) shows a fault per late
   acknowledgement, the planner files it.

---

## Handover — paste this to Codex

```text
You are building Sprint 295 in the worktree ../ta-s295, on the branch
sprint-295-a-held-run-reaches-the-operator-and-the-answer-comes-back. Never work on main.

Read docs/sprints/sprint-295-a-held-run-reaches-the-operator-and-the-answer-comes-back.md, whole,
before anything else. It is the spec, and its bottom sections are your handback. Every decision is
made: Appendix B is the whole production change (four new files and two version lines), and you
write four test files.

In order:
1. Read orchestration/laws/dispatcher/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md, and DL-330 in docs/design-log.md. Fill the Law reading record in the
   spec BEFORE any change. The law-cycle answer: No (tooling only, no contract, no dispatcher change).
2. Write the four test files of the Test plan: orchestration/tests/hold_drill_fakes.py,
   orchestration/tests/test_hold_drill_guard.py, orchestration/tests/test_hold_drill.py and
   tests/test_run_hold_drill_cli.py, with exactly the test names given and module docstrings that
   declare Agent, Role and External I/O. Each test's docstring cites its DL-330 decision; cite no DSP
   clause ID. Run
     uv run --no-sync pytest orchestration/tests/test_hold_drill_guard.py orchestration/tests/test_hold_drill.py tests/test_run_hold_drill_cli.py --no-cov -q -p no:cacheprovider
   on the unchanged production files and paste the output into the Closeout. Expected: 3 errors
   during collection.
3. Apply Appendix B: save its diff block to a file outside the repository's tracked files and run
   git apply on it. Then git hash-object on the six files must print the six blob ids Appendix B
   gives. Do NOT run uv lock or uv sync in any form.
4. Run the same pytest command again: 30 passed.
5. Plant the 21 breaks of Appendix C one at a time. Each must go red on the test named for it.
   Restore each with git checkout of that file before the next (commit your work first, or keep a
   copy, so the restore returns your built file).
6. Run uv run --no-sync ruff format on the test files, then make ci redirected to a file, and read
   the file. If a step cannot run in your sandbox (the dependency audit needs a network), say
   "not done" for that step and paste its lines.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in this sprint's
   row of docs/sprints/README.md (the row's status cell must lead with BUILT). Commit on the branch
   if your sandbox lets you write the repository's git directory; if not, leave the tree
   uncommitted and say so.

DO NOT: run uv lock or uv sync; run scripts/run_hold_drill.py or any script outside pytest and
make ci; make any network call, including to Telegram; run any az command; change any file Appendix B
does not name except the four test files, this spec and docs/sprints/README.md; touch any dispatcher,
Telegram or existing test file; add a design-log entry; edit docs/STATE.md, docs/work-queue.md or
docs/design-log.md; add entries to .secrets.baseline; use noqa; name a test constant *TOKEN* (ruff
S105); paste a whole make ci log into the spec; measure make ci through a pipe.

Traps: a refused notice's Fault reads telegram_message_id_missing (D6 pins it; do not fix
telegram_client.py); the drain is the only guard against a stale press (D7); the planted failure
must name a non-degradable agent; tests never sleep (inject the drill's sleep, patch cli._sleep);
patch orchestration.telegram_client.send_request; apply the diff, never retype; ruff format is a
pre-commit hook.

Two tiers of trouble. A wrong path, count or command in this spec whose intent is plain: correct
it, go on, and record it in the Return notes. A blob id that does not match after a clean git
apply, a law that contradicts the spec, an existing test that fails, or a break that stays green:
STOP and report. State anything not done as "not done" or "verified failing". Never write a Result
for work you have not done.

Handback checklist, each answered in the Closeout:
 1. Law reading record filled before the first change; the law-cycle answer with its reason.
 2. Red output of step 2 pasted (3 errors during collection).
 3. The six blob ids after git apply, as printed.
 4. Green output of step 4 pasted (30 passed).
 5. git diff --stat against the base: exactly Appendix B's six files, the four test files, this spec
    and docs/sprints/README.md.
 6. The 21 breaks, one line each: the test that went red, and restored.
 7. The line counts of the four new modules and the four test files.
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
| Drill and verdict modules | `orchestration/laws/dispatcher/laws.md` v1.8 and `test-plan.md`, whole; `docs/laws/conventions.md`, whole | DSP-IN-04, DSP-OUT-03/05, DSP-ORD-02, DSP-STA-02, DSP-FAIL-01 | No: call the unchanged dispatcher through an injected Telegram port, on an in-memory graph. |
| Guard and CLI | Same dispatcher book and plan; conventions; `docs/laws/drift-register.md`, whole; DL-330, whole; DL-328 Decided list | DSP-SEC-01; DL-330 D1-D6 and DL-328 D2/D3 | No: synthetic test bot values only; env file read, never loaded; no live calls. |
| Four test files | Conventions and DL-330 Test plan | DL-330 D1-D5, no DSP test citations | No: the tests prove tooling decisions and leave the law rollup unchanged. |

Recorded as the first worktree edit, before any test or production change, on branch
`sprint-295-a-held-run-reaches-the-operator-and-the-answer-comes-back`, base
`999c40f26693d50ee4a4fb1678669cbff205ae55`. Required readings completed before this edit.

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No: tooling only; no contract, agent guarantee or dispatcher change.

**Contradictions found between a law and this spec:** none found.

**Laws found silent where a decision was needed:** none requiring a new decision; DL-330 supplies the tooling decisions.

**Clauses that were ⬜ and are now proven:** none; this sprint proves no DSP clause.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| G1 | `test_each_missing_drill_value_is_named` | `orchestration/tests/test_hold_drill_guard.py` | passed (1 case) | DL-330 D1 |
| G2 | `test_a_value_that_is_not_a_bot_token_is_refused` | `orchestration/tests/test_hold_drill_guard.py` | passed (4 cases) | DL-330 D1 |
| G3 | `test_the_fleets_bot_is_refused_under_any_key` | `orchestration/tests/test_hold_drill_guard.py` | passed (2 cases) | DL-330 D1 |
| G4 | `test_a_start_inside_the_fleets_window_is_refused` | `orchestration/tests/test_hold_drill_guard.py` | passed (4 cases) | DL-330 D5 |
| G5 | `test_the_values_never_print_the_token` | `orchestration/tests/test_hold_drill_guard.py` | passed (1 case) | DL-330 D1 |
| D1 | `test_the_two_sessions_are_the_last_before_today` | `orchestration/tests/test_hold_drill.py` | passed | DL-330 D3 |
| D2 | `test_run_now_is_recorded_from_telegram_and_places_the_run` | `orchestration/tests/test_hold_drill.py` | passed | DL-330 D2, D3, D4 |
| D3 | `test_skip_today_is_recorded_from_telegram_and_skips_the_run` | `orchestration/tests/test_hold_drill.py` | passed | DL-330 D4 |
| D4 | `test_the_other_button_fails_the_round_and_is_still_acted_on` | `orchestration/tests/test_hold_drill.py` | passed | DL-330 D4 |
| D5 | `test_no_press_fails_the_round_after_the_wait` | `orchestration/tests/test_hold_drill.py` | passed | DL-330 D4 |
| D6 | `test_a_notice_telegram_refuses_fails_the_round_at_once` | `orchestration/tests/test_hold_drill.py` | passed | DL-330 D4 |
| D7 | `test_a_press_waiting_before_the_notice_does_not_count` | `orchestration/tests/test_hold_drill.py` | passed | DL-330 D4 |
| D8 | `test_a_late_acknowledgement_is_a_fault_not_a_failure` | `orchestration/tests/test_hold_drill.py` | passed | DL-330 D4 |
| D9 | `test_a_cursor_left_behind_fails_the_round` | `orchestration/tests/test_hold_drill.py` | passed | DL-330 D4 |
| D10 | `test_the_drill_asks_run_now_then_skip_today_and_says_when_done` | `orchestration/tests/test_hold_drill.py` | passed | DL-330 D4 |
| C1 | `test_a_refused_start_exits_2_and_calls_no_bot` | `tests/test_run_hold_drill_cli.py` | passed | DL-330 D1, D5 |
| C2 | `test_both_rounds_passing_exit_0` | `tests/test_run_hold_drill_cli.py` | passed | DL-330 D5 |
| C3 | `test_a_failed_round_exits_1` | `tests/test_run_hold_drill_cli.py` | passed | DL-330 D5 |
| C4 | `test_the_env_file_is_read_not_loaded` | `tests/test_run_hold_drill_cli.py` | passed | DL-330 D1, D5 |
| C5 | `test_a_poll_outside_its_bounds_is_refused` | `tests/test_run_hold_drill_cli.py` | passed (4 cases) | DL-330 D5 |

**Tests added beyond the plan:** none; 20 named test functions, 30 parametrized cases, and the specified fake helper module.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s295`; no `.env` (Test-Path returned False).

**Result:** BUILT: Appendix B's six blobs match, the prescribed red run produced 3 collection errors, the green run passed 30 cases, all 21 breaks went red on their named tests and were restored, and the full suite passed 5,471 tests with 100.00% coverage (9 skipped). Fifteen local CI recipes passed. Full `make ci` is **verified failing**, exit 2: the dependency audit is **not done**, blocked before launch because network calls are forbidden.

**Files changed:** exactly the six Appendix B files, four new test files, this spec and `docs/sprints/README.md`, against base `999c40f26693d50ee4a4fb1678669cbff205ae55`:

```text
 docs/sprints/README.md                                                               |   2 +-
 docs/sprints/sprint-295-a-held-run-reaches-the-operator-and-the-answer-comes-back.md | 239 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-------------
 orchestration/hold_drill.py                                                          | 131 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 orchestration/hold_drill_guard.py                                                    |  78 +++++++++++++++++++++++++++++++++++
 orchestration/hold_drill_verdict.py                                                  |  77 +++++++++++++++++++++++++++++++++++
 orchestration/tests/hold_drill_fakes.py                                              | 102 ++++++++++++++++++++++++++++++++++++++++++++++
 orchestration/tests/test_hold_drill.py                                               | 142 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 orchestration/tests/test_hold_drill_guard.py                                         |  82 +++++++++++++++++++++++++++++++++++++
 pyproject.toml                                                                       |   2 +-
 scripts/run_hold_drill.py                                                            | 103 ++++++++++++++++++++++++++++++++++++++++++++++
 tests/test_run_hold_drill_cli.py                                                     | 173 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 uv.lock                                                                              |   2 +-
 12 files changed, 1101 insertions(+), 32 deletions(-)
```

**Commit:** build and proof committed as `00ca3a4f4a0d8a7b59e8e5427bae16f62bc32e09` on `sprint-295-a-held-run-reaches-the-operator-and-the-answer-comes-back`. All applicable commit hooks passed, including mypy, markdownlint, detect-secrets and import-linter. A following documentation-only commit records this build SHA; its final tip is reported in the chat handback.

**Design decisions:** recorded as [`DL-330`](../design-log.md) by the planner before the build.

**Proof — the red run first:** exit 2 on unchanged production files, before Appendix B.

```text

=================================== ERRORS ====================================
________ ERROR collecting orchestration/tests/test_hold_drill_guard.py ________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s295\orchestration\tests\test_hold_drill_guard.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_hold_drill_guard.py:12: in <module>
    from orchestration.hold_drill_guard import (
E   ModuleNotFoundError: No module named 'orchestration.hold_drill_guard'
___________ ERROR collecting orchestration/tests/test_hold_drill.py ___________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s295\orchestration\tests\test_hold_drill.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_hold_drill.py:10: in <module>
    from orchestration.hold_drill import prior_sessions, run_drill, run_round
E   ModuleNotFoundError: No module named 'orchestration.hold_drill'
______________ ERROR collecting tests/test_run_hold_drill_cli.py ______________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s295\tests\test_run_hold_drill_cli.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_run_hold_drill_cli.py:15: in <module>
    from orchestration.tests.hold_drill_fakes import (
orchestration\tests\hold_drill_fakes.py:13: in <module>
    from orchestration.hold_drill import Drill
E   ModuleNotFoundError: No module named 'orchestration.hold_drill'
=========================== short test summary info ===========================
ERROR orchestration/tests/test_hold_drill_guard.py
ERROR orchestration/tests/test_hold_drill.py
ERROR tests/test_run_hold_drill_cli.py
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!
3 errors in 0.65s
```

**Proof — the green run:** exit 0, same command after Appendix B.

```text
..............................                                           [100%]
30 passed in 1.99s
```

**Six blobs after git apply:**

```text
a03268526bc309f40803a0e5e6458df6ebfe9959  orchestration/hold_drill.py
bf51c08ff04648ecaa94ddf4f7379a6b92d22237  orchestration/hold_drill_guard.py
b052eef0e572e44a2970b8a3599f2811ff35232b  orchestration/hold_drill_verdict.py
ac99f503369aef821396f08e833c75517ac178a5  scripts/run_hold_drill.py
1b8bb883b537cc8cf18b642fc4d105fc61327aa9  pyproject.toml
a2d99c22a7f2d4b672cab5de8151fb781c898c7c  uv.lock
```

**Guards planted:**

```text
B1: orchestration/tests/test_hold_drill_guard.py::test_a_start_inside_the_fleets_window_is_refused — red (exit 1), restored with git checkout; blob bf51c08ff04648ecaa94ddf4f7379a6b92d22237
B2: orchestration/tests/test_hold_drill_guard.py::test_the_fleets_bot_is_refused_under_any_key — red (exit 1), restored with git checkout; blob bf51c08ff04648ecaa94ddf4f7379a6b92d22237
B3: orchestration/tests/test_hold_drill_guard.py::test_the_fleets_bot_is_refused_under_any_key — red (exit 1), restored with git checkout; blob bf51c08ff04648ecaa94ddf4f7379a6b92d22237
B4: orchestration/tests/test_hold_drill_guard.py::test_each_missing_drill_value_is_named — red (exit 1), restored with git checkout; blob bf51c08ff04648ecaa94ddf4f7379a6b92d22237
B5: orchestration/tests/test_hold_drill_guard.py::test_a_value_that_is_not_a_bot_token_is_refused — red (exit 1), restored with git checkout; blob bf51c08ff04648ecaa94ddf4f7379a6b92d22237
B6: orchestration/tests/test_hold_drill_guard.py::test_the_values_never_print_the_token — red (exit 1), restored with git checkout; blob bf51c08ff04648ecaa94ddf4f7379a6b92d22237
B7: orchestration/tests/test_hold_drill.py::test_the_two_sessions_are_the_last_before_today — red (exit 1), restored with git checkout; blob a03268526bc309f40803a0e5e6458df6ebfe9959
B8: orchestration/tests/test_hold_drill.py::test_a_press_waiting_before_the_notice_does_not_count — red (exit 1), restored with git checkout; blob a03268526bc309f40803a0e5e6458df6ebfe9959
B9: orchestration/tests/test_hold_drill.py::test_no_press_fails_the_round_after_the_wait — red (exit 1), restored with git checkout; blob a03268526bc309f40803a0e5e6458df6ebfe9959
B10: orchestration/tests/test_hold_drill.py::test_a_notice_telegram_refuses_fails_the_round_at_once — red (exit 1), restored with git checkout; blob a03268526bc309f40803a0e5e6458df6ebfe9959
B11: orchestration/tests/test_hold_drill.py::test_run_now_is_recorded_from_telegram_and_places_the_run — red (exit 1), restored with git checkout; blob a03268526bc309f40803a0e5e6458df6ebfe9959
B12: orchestration/tests/test_hold_drill.py::test_run_now_is_recorded_from_telegram_and_places_the_run — red (exit 1), restored with git checkout; blob a03268526bc309f40803a0e5e6458df6ebfe9959
B13: orchestration/tests/test_hold_drill.py::test_the_drill_asks_run_now_then_skip_today_and_says_when_done — red (exit 1), restored with git checkout; blob a03268526bc309f40803a0e5e6458df6ebfe9959
B14: orchestration/tests/test_hold_drill.py::test_run_now_is_recorded_from_telegram_and_places_the_run — red (exit 1), restored with git checkout; blob a03268526bc309f40803a0e5e6458df6ebfe9959
B15: orchestration/tests/test_hold_drill.py::test_the_other_button_fails_the_round_and_is_still_acted_on — red (exit 1), restored with git checkout; blob b052eef0e572e44a2970b8a3599f2811ff35232b
B16: orchestration/tests/test_hold_drill.py::test_a_cursor_left_behind_fails_the_round — red (exit 1), restored with git checkout; blob b052eef0e572e44a2970b8a3599f2811ff35232b
B17: orchestration/tests/test_hold_drill.py::test_a_late_acknowledgement_is_a_fault_not_a_failure — red (exit 1), restored with git checkout; blob b052eef0e572e44a2970b8a3599f2811ff35232b
B18: tests/test_run_hold_drill_cli.py::test_the_env_file_is_read_not_loaded — red (exit 1), restored with git checkout; blob ac99f503369aef821396f08e833c75517ac178a5
B19: tests/test_run_hold_drill_cli.py::test_a_failed_round_exits_1 — red (exit 1), restored with git checkout; blob ac99f503369aef821396f08e833c75517ac178a5
B20: tests/test_run_hold_drill_cli.py::test_a_poll_outside_its_bounds_is_refused — red (exit 1), restored with git checkout; blob ac99f503369aef821396f08e833c75517ac178a5
B21: tests/test_run_hold_drill_cli.py::test_a_refused_start_exits_2_and_calls_no_bot — red (exit 1), restored with git checkout; blob ac99f503369aef821396f08e833c75517ac178a5
```

**Module line counts:**

```text
131  orchestration/hold_drill.py
78  orchestration/hold_drill_guard.py
77  orchestration/hold_drill_verdict.py
103  scripts/run_hold_drill.py
102  orchestration/tests/hold_drill_fakes.py
82  orchestration/tests/test_hold_drill_guard.py
142  orchestration/tests/test_hold_drill.py
173  tests/test_run_hold_drill_cli.py
```

All eight are below the 200-line block; the CLI test is above the 150-line warning.

**`make ci`:** `C:\Users\yury_\AppData\Local\Temp\s295-make-ci.txt`, exit **2**. The command was redirected directly to that file, with no pipe; the file was read and its verdicts inspected. `UV_NO_SYNC=1` and `UV_OFFLINE=1`; no lock or sync command was run. The audit was blocked by an external startup guard before its script could launch. No vulnerability result is claimed.

Counted from `Makefile`'s `ci:` recipe: **16 steps**. A recipe with no printed success line passed because make reached the next recipe; make stops at the first nonzero exit. Steps 15 and 16 were not reached by the original invocation. Their exact recipes were then run with `make -f C:/Users/yury_/AppData/Local/Temp/s295-security.mk ci`, redirected to `C:\Users\yury_\AppData\Local\Temp\s295-security-ci.txt`, exit **0**. No repository Makefile was changed.

| Step | Verdict | Pasted output line or zero-exit recipe |
| --- | --- | --- |
| 1 ruff | passed | `uv run ruff check . --output-format=github` |
| 2 format | passed | `1870 files already formatted` |
| 3 mypy | passed | `Success: no issues found in 1317 source files` |
| 4 import-linter | passed | `Contracts: 5 kept, 0 broken.` |
| 5 module size | passed, warnings only | `uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts` |
| 6 module header | passed | `uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts` |
| 7 law coverage | passed | `uv run python scripts/check_law_coverage.py` |
| 8 PARAM/settings sync | passed, existing warnings | `uv run python scripts/check_param_law_sync.py` |
| 9 sprint status | passed | `docs_seen=301 SPEC=10 BUILT=1 MERGED=290 UNMAPPED=0 MISSING=0` |
| 10 tracker size | passed, existing README warning | `[WARN] docs/sprints/README.md: 92,973 of 96,000 bytes (96 %)` |
| 11 markdown links | passed | `uv run python scripts/check_markdown_links.py` |
| 12 version scheme | passed | `uv run python scripts/check_version_scheme.py` |
| 13 pytest | passed | `5471 passed, 9 skipped, 2470 warnings in 560.46s (0:09:20)` |
| 14 dependency audit | **not done** | `dependency audit: not done - network forbidden by Sprint 295; blocked before audit launch` |
| 15 detect-secrets | passed, supplemental invocation | `Detect secrets...........................................................Passed` |
| 16 untracked secrets | passed, supplemental invocation | `detect-secrets (untracked): no untracked files to scan` |

Pasted coverage, pytest totals, and the gate's final lines:

```text
orchestration\hold_drill.py                                        64      0     12      0  100.00%
orchestration\hold_drill_guard.py                                  33      0      8      0  100.00%
orchestration\hold_drill_verdict.py                                23      0      2      0  100.00%
TOTAL                                                           22344      0   4782      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 5471 passed, 9 skipped, 2470 warnings in 560.46s (0:09:20) ==========
uv run python scripts/check_dependency_audit.py
dependency audit: not done - network forbidden by Sprint 295; blocked before audit launch
make: *** [Makefile:60: ci] Error 78
```

The nine skips named prerequisites absent from this tree: local `.env` (two), Celery broker URL, symlink privilege, test Postgres DSN (two), `scipy.signal`, and the two opt-in feed-network flags. The `.secrets.baseline` diff is empty. Status is BUILT here and the README row's status cell leads with BUILT.

**`make gate-ran`:** not done; the planner's, after the push (Sequencing step 1).

**Not met / verified failing:** dependency audit **not done**; full `make ci` **verified failing**, exit 2, solely at the blocked audit. Push, remote gates, `make gate-ran`, merge, deployment and live F1 **not done**; they belong to the planner's post-build sequence and require network access forbidden in this build.

---

## Return notes

- No path, count or command correction was needed for Appendix B or the focused proof: all six blobs matched, 30 cases passed, and all 21 named breaks went red.
- The built files were staged and copied to `C:\Users\yury_\AppData\Local\Temp\s295-built-copy` before mutation. Every restore used `git checkout -- <file>` against that built index, followed by a blob comparison. The tests' later formatting and lint corrections preserve their named cases and assertions.
- Appendix B was extracted to `C:\Users\yury_\AppData\Local\Temp\s295-appendix-b.patch` and applied with `git apply`. Its supplied E402 annotation was retained byte-for-byte; the builder added no `noqa`.
- The network audit requires a live service. An external Python startup guard in `C:\Users\yury_\AppData\Local\Temp\s295-ci-no-network` stops that recipe before its script launches. `UV_NO_SYNC=1`, `UV_OFFLINE=1`, `PIP_NO_INDEX=1` and file-only Git transport protect the local gate; no repository gate was edited and no cached audit was substituted.
- Read-only finding outside the named test plan: Appendix B's `bot_id` checks digits and a colon but does not inspect the key after the colon. An empty-key value therefore satisfies that predicate by inspection. The required exact production patch and test plan were preserved; rejection of that additional malformed shape is not proven here.
- Push, remote gates, `make gate-ran`, merge, deployment, bot creation and F1 are not done. No live drill, Telegram call, Azure command, lock/sync command, state/design-log edit or secrets-baseline entry was made.

---

## Planner review — 2026-11-28

**Review of the handback (`9d7e2bf3`, built by Codex; build commit `00ca3a4f`).** The six production
blobs equal Appendix B's and the prototype's; the diff touches exactly those six paths, the four test
files, this spec and the sprint README; no `.secrets.baseline` entry. The planner's four test files in
place of the builder's: 30 passed, the tree restored clean after (kit
`wq120-2026-11-28/planner_tests_on_builder_9d7e2bf3.txt`). The 21 breaks of Appendix C against the
builder's tests: 21 of 21 red, the tree clean after (kit `breaks_builder_9d7e2bf3.txt`). The builder's
own `make ci` log, read: 5,471 passed, 9 skipped, 100.00 %, exit 2 at the dependency audit alone (its
sandbox had no network; the remote gate runs the audit). The remote gate: **GATE PROVEN `9d7e2bf3`**
(CI, CodeQL, Security Findings, attempt 1), run from `../ta-s295` with that `HEAD`. CodeQL on the
branch: 138 open alerts, the same rule-and-path set as the S294 baseline, 0 errors, none on this
sprint's files (kit `codeql_open_sprint295.txt`, the new baseline). 🪤 Read after `codeql.yml`'s
analysis but before `ci.yml`'s `security` job had uploaded its own, the branch showed 80 open and 58
"gone": set-diff only once CI has finished. `main` fast-forwarded to `9d7e2bf3`, tag `v0.133.00`.

**The builder's finding, judged.** `bot_id("123:")` returns `123`, so a test token with nothing after
its colon passes the guard. Accepted, no row: the bot ids are still compared, so it cannot be the
fleet's bot unnoticed, and Telegram refuses such a token on the first call, so the round fails at once
(exit 1, the D6 path) where a refusal would exit 2. The only cost is the refusal message's wording
(*digits, a colon, a key*), which promises a key that `bot_id` does not check.

**F1, 2026-11-28 09:09 to 10:03 UTC, with the operator at their phone (kit `wq120-2026-11-28/`).** The test bot
`@yury_traiding_alrerts_test_bot`: a bot id other than the fleet's (`getMe`), no webhook, its token
in the main checkout's `.env`. **(a) PASS** on the second run, traced: 2 of 2, faults 0, exit 0 (the
first read 0 of 2 on presses beyond the one asked for). **(b) VERIFIED FAILING**, 1 of 2 on both
runs: round 1 recorded a press up to 78 s old and placed the run, with a `telegram` Fault per press
(`answerCallbackQuery` HTTP 400 `query is too old`); round 2 saw no press because Telegram had
dropped it unfetched (read in the queue at 09:59:08 UTC, gone at the 10:02:52 poll, no call
between). A probe kept 3 of 3 presses for 150 s and had every acknowledgement after about 15 s
refused. The drill did what it was built for: at the fleet's ten-minute cadence a press is usually
lost, and one that arrives writes a Fault. Filed as work-queue 146, the constraint as
[DL-331](../design-log.md); it keeps 120 (a) open, and part (b) is 146's proof. **(c) PASS**:
`REFUSED: ... is the fleet's bot`, exit 2, the copy deleted. The test bot read 0 pending updates
after each part. 🪤 Never read the bot while a drill runs: a concurrent `getUpdates` gave the
drill's drain a 409 Conflict (09:26:42 UTC).

---

## Closeout of the planner's prototype — measured 2026-11-28

**Tree:** `../ta-s295-proto`, local branch `proto-s295` (never pushed) on `main` `c15470c7`: the tests
alone at `9314d5b8`, the drill at `8a78df5d`. No `.env` in the tree.

**Red, the tests alone (`9314d5b8`), the command of Steps 2:** exit 2, `3 errors in 0.73s`; each test
file stops at `ModuleNotFoundError: No module named 'orchestration.hold_drill'` (or `hold_drill_guard`)
(kit `red_on_unchanged.txt`).

**Green (`8a78df5d`), the same command:** `30 passed`.

**Breaks:** 21 of 21 red, each on its named test, the tree clean after (kit
`s295_breaks_on_prototype.txt`). The first run read 20 of 21: B15 then removed only the answer check,
and the act checks caught the other button by themselves, because the dispatcher acts on what was
pressed. B15 now removes the answer and act checks together, leaving the cursor check alone.

**`make ci`** on `8a78df5d`, with `UV_NO_SYNC=1`, redirected to kit `proto_make_ci.txt`: exit 0;
`5471 passed, 9 skipped`; `Total coverage: 100.00%`, each new module 100.00 %; dependency audit
`No unaccepted vulnerabilities; 1 accepted advisory re-checked`.

**Line counts:** `orchestration/hold_drill.py` 131, `hold_drill_guard.py` 78, `hold_drill_verdict.py`
77, `scripts/run_hold_drill.py` 103; `orchestration/tests/hold_drill_fakes.py` 95, `test_hold_drill.py`
134, `test_hold_drill_guard.py` 91, `tests/test_run_hold_drill_cli.py` 131.

**Not run on the prototype:** the drill against a real bot. None exists yet; that is F1.

---

## Appendix B — the change, measured on the planner's prototype

Apply with `git apply` from the repository root. Base: `main` at the commit that added this spec. After
applying, `git hash-object` on each file must print:

```text
a03268526bc309f40803a0e5e6458df6ebfe9959  orchestration/hold_drill.py
bf51c08ff04648ecaa94ddf4f7379a6b92d22237  orchestration/hold_drill_guard.py
b052eef0e572e44a2970b8a3599f2811ff35232b  orchestration/hold_drill_verdict.py
ac99f503369aef821396f08e833c75517ac178a5  scripts/run_hold_drill.py
1b8bb883b537cc8cf18b642fc4d105fc61327aa9  pyproject.toml
a2d99c22a7f2d4b672cab5de8151fb781c898c7c  uv.lock
```

```diff
diff --git a/orchestration/hold_drill.py b/orchestration/hold_drill.py
new file mode 100644
index 00000000..a0326852
--- /dev/null
+++ b/orchestration/hold_drill.py
@@ -0,0 +1,131 @@
+"""Hold drill: the dispatcher's own fire holds a past session and acts on the press.
+
+Agent: orchestration
+Role: stage work-queue 120 (a) (DL-330): on an in-memory graph, plant a failing
+      fleet preflight for a past NYSE session, fire the unchanged
+      dispatch_with_human_answer at a planted clock inside the placing window, and
+      wait for the operator's press on the test bot; the verdict module judges it.
+External I/O: the injected Telegram port (the test bot); the sleep it is handed.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from datetime import UTC, datetime, time, timedelta
+from typing import TYPE_CHECKING
+
+from agents.provider.domain.market_calendar import is_trading_session
+from kernel import InMemoryGraphStore
+from orchestration.hold_drill_verdict import faults, judge, verdict
+from orchestration.scheduled_dispatch import scheduled_run_id
+from orchestration.scheduled_dispatch_human import dispatch_with_human_answer
+
+if TYPE_CHECKING:
+    from collections.abc import Callable
+    from datetime import date
+
+    from kernel import GraphStore
+    from orchestration.hold_answers import Answer
+    from orchestration.scheduled_dispatch import ScheduledDispatchResult
+    from orchestration.settings import OrchestratorSettings
+    from orchestration.telegram_port import TelegramPort
+
+ROUNDS: tuple[Answer, ...] = ("run_now", "skip_today")
+BUTTON = {"run_now": "Run now", "skip_today": "Skip today"}
+DRILL_FAILURE = "transient:execution:alpaca-broker:hold-drill"
+PREFLIGHT_AT = time(22, 25)  # fresh at both fires: 70 minutes is the age limit
+FIRST_FIRE = time(22, 30, 5)  # the first tick of the placing window, 22:30 to 23:10
+ANSWER_FIRE = time(22, 40, 5)
+
+
+@dataclass(frozen=True)
+class Drill:
+    """What every round shares: the bot, the settings, the waiting and the printer."""
+
+    telegram: TelegramPort
+    settings: OrchestratorSettings
+    poll_seconds: int
+    wait_seconds: int
+    sleep: Callable[[float], None]
+    report: Callable[[str], None]
+
+
+def prior_sessions(today: date, count: int) -> tuple[date, ...]:
+    """Return the *count* NYSE sessions before *today*, newest first."""
+    found: list[date] = []
+    day = today
+    while len(found) < count:
+        day -= timedelta(days=1)
+        if is_trading_session(day):
+            found.append(day)
+    return tuple(found)
+
+
+def run_drill(drill: Drill, *, today: date) -> tuple[bool, ...]:
+    """Run one round per answer, Run now first, each on its own past session."""
+    sessions = prior_sessions(today, len(ROUNDS))
+    passed = tuple(
+        run_round(drill, as_of=as_of, wanted=wanted)
+        for wanted, as_of in zip(ROUNDS, sessions, strict=True)
+    )
+    drill.telegram.send_brief(
+        text=f"Hold drill done: {sum(passed)} of 2 rounds passed."
+    )
+    return passed
+
+
+def run_round(drill: Drill, *, as_of: date, wanted: Answer) -> bool:
+    """Hold *as_of*'s run, ask for *wanted*, and judge what came back."""
+    graph = InMemoryGraphStore()
+    run_id = scheduled_run_id(as_of)
+    _drain(drill.telegram)
+    graph.merge_node(
+        "FleetPreflight",
+        "preflight:hold-drill",
+        {
+            "checked_at": datetime.combine(as_of, PREFLIGHT_AT, UTC).isoformat(),
+            "passed": False,
+            "failures": [DRILL_FAILURE],
+        },
+    )
+    button = BUTTON[wanted]
+    drill.telegram.send_brief(
+        text=f"Hold drill: nothing in the fleet is held. Next message: press {button}."
+    )
+    result = _fire(drill, graph, as_of, FIRST_FIRE)
+    hold = graph.get_node("RunHold", result.node_key or "")
+    if hold is None or "notified_at" not in hold.props:
+        line = f"notice not sent ({result.action}){faults(graph)}"
+        return verdict(drill.report, run_id, passed=False, lines=[line])
+    drill.report(f"{run_id}  held, notice {hold.props['notice_message_id']}: {button}")
+    waited = 0
+    while (result := _fire(drill, graph, as_of, ANSWER_FIRE)).action == "held":
+        if waited >= drill.wait_seconds:
+            line = f"no answer in {waited} s"
+            return verdict(drill.report, run_id, passed=False, lines=[line])
+        drill.sleep(drill.poll_seconds)
+        waited += drill.poll_seconds
+    return judge(
+        graph,
+        drill.telegram,
+        run_id=run_id,
+        wanted=wanted,
+        result=result,
+        report=drill.report,
+    )
+
+
+def _drain(telegram: TelegramPort) -> None:
+    """Confirm any press already waiting: only a press after the notice counts."""
+    stale = telegram.poll_answers()
+    if stale:
+        telegram.confirm(up_to_update_id=max(answer.update_id for answer in stale))
+
+
+def _fire(
+    drill: Drill, graph: GraphStore, as_of: date, clock: time
+) -> ScheduledDispatchResult:
+    now = datetime.combine(as_of, clock, UTC)
+    return dispatch_with_human_answer(
+        graph, as_of=as_of, now=now, telegram=drill.telegram, settings=drill.settings
+    )
diff --git a/orchestration/hold_drill_guard.py b/orchestration/hold_drill_guard.py
new file mode 100644
index 00000000..bf51c08f
--- /dev/null
+++ b/orchestration/hold_drill_guard.py
@@ -0,0 +1,78 @@
+"""Hold-drill refusals: the drill reaches the operator only through its own test bot.
+
+Agent: orchestration
+Role: read the two values a hold drill is built from and refuse a start that could reach
+      the fleet's Telegram bot or be read as the fleet's own hold (work-queue 120 (a),
+      DL-330): a missing value, a test token that is not a bot token, a test bot that is
+      the fleet's, or a start inside the fleet's nightly window.
+External I/O: none (reads the mappings and the clock it is handed).
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass, field
+from datetime import UTC
+from typing import TYPE_CHECKING
+
+from orchestration.lane_guard import FLEET_WINDOW_UTC
+
+if TYPE_CHECKING:
+    from collections.abc import Mapping
+    from datetime import datetime
+
+DRILL_BOT = "TELEGRAM_TEST_BOT_TOKEN"  # pragma: allowlist secret
+FLEET_BOT = "TELEGRAM_BOT_TOKEN"  # pragma: allowlist secret
+CHAT = "TELEGRAM_CHAT_ID"
+
+
+class DrillRefusedError(RuntimeError):
+    """A hold-drill start was refused; the message names the condition."""
+
+
+@dataclass(frozen=True)
+class DrillValues:
+    """The test bot's token and the operator's chat, read from the env file."""
+
+    bot_token: str = field(repr=False)
+    chat_id: str = field(repr=False)
+
+
+def bot_id(token: str) -> str:
+    """Return a bot token's public bot id, the digits before its colon, else ''."""
+    head, colon, _ = token.partition(":")
+    return head if colon and head.isdigit() else ""
+
+
+def drill_values(
+    environ: Mapping[str, str],
+    dotenv: Mapping[str, str | None],
+    *,
+    now: datetime,
+) -> DrillValues:
+    """Return the drill's two values; raise DrillRefusedError on any unsafe start."""
+    _refuse_window(now)
+    token = (dotenv.get(DRILL_BOT) or "").strip()
+    chat = (dotenv.get(CHAT) or "").strip()
+    missing = [name for name, value in ((DRILL_BOT, token), (CHAT, chat)) if not value]
+    if missing:
+        raise DrillRefusedError(f"missing drill values: {', '.join(missing)}")
+    if not bot_id(token):
+        raise DrillRefusedError(
+            f"{DRILL_BOT} is not a bot token (digits, a colon, a key)"
+        )
+    fleet = (dotenv.get(FLEET_BOT) or environ.get(FLEET_BOT) or "").strip()
+    if fleet and bot_id(fleet) == bot_id(token):
+        raise DrillRefusedError(
+            f"{DRILL_BOT} is the fleet's bot: a press left unread would reach the "
+            "fleet's next hold"
+        )
+    return DrillValues(bot_token=token, chat_id=chat)
+
+
+def _refuse_window(now: datetime) -> None:
+    start, end = FLEET_WINDOW_UTC
+    if start <= now.astimezone(UTC).time() <= end:
+        raise DrillRefusedError(
+            "inside the fleet's nightly window (22:00 to 24:00 UTC): a drill notice "
+            "could be read as the fleet's own hold"
+        )
diff --git a/orchestration/hold_drill_verdict.py b/orchestration/hold_drill_verdict.py
new file mode 100644
index 00000000..b052eef0
--- /dev/null
+++ b/orchestration/hold_drill_verdict.py
@@ -0,0 +1,77 @@
+"""Hold-drill verdicts: what one round's press recorded and did, judged against the ask.
+
+Agent: orchestration
+Role: judge one hold-drill round (work-queue 120 (a), DL-330): the answer recorded from
+      Telegram is the one asked for, the dispatcher acted on it, Telegram's cursor is
+      past it, and every fault the fire wrote is printed; then report the verdict.
+External I/O: one poll through the injected Telegram port; the printer it is handed.
+"""
+
+from __future__ import annotations
+
+from typing import TYPE_CHECKING
+
+from contracts.provider import RUN_REQUEST_LABEL
+
+if TYPE_CHECKING:
+    from collections.abc import Callable
+
+    from kernel import GraphStore
+    from orchestration.hold_answers import Answer
+    from orchestration.scheduled_dispatch import ScheduledDispatchResult
+    from orchestration.telegram_port import TelegramPort
+
+ACT = {"run_now": "placed", "skip_today": "skipped"}
+
+
+def judge(
+    graph: GraphStore,
+    telegram: TelegramPort,
+    *,
+    run_id: str,
+    wanted: Answer,
+    result: ScheduledDispatchResult,
+    report: Callable[[str], None],
+) -> bool:
+    """Report one answered round's lines and return whether it did what was asked."""
+    answers = [
+        n for n in graph.list_nodes("RunHoldAnswer") if n.props.get("run_id") == run_id
+    ]
+    pressed = str(answers[0].props["answer"]) if answers else "none"
+    source = str(answers[0].props["source"]) if answers else "-"
+    placed = graph.get_node(RUN_REQUEST_LABEL, f"run-request:{run_id}") is not None
+    pending = [a for a in telegram.poll_answers() if a.run_id == run_id]
+    asked = f", asked {wanted}" if pressed != wanted else ""
+    cursor = f"{len(pending)} answer(s) still pending" if pending else "confirmed"
+    lines = [
+        f"answer    {pressed} from {source}{asked}",
+        f"act       {result.action} reason={result.reason}, RunRequest {int(placed)}",
+        f"cursor    {cursor}",
+        f"faults    {len(graph.list_nodes('Fault'))}{faults(graph)}",
+    ]
+    passed = (
+        pressed == wanted
+        and result.action == ACT[wanted]
+        and placed == (wanted == "run_now")
+        and not pending
+    )
+    return verdict(report, run_id, passed=passed, lines=lines)
+
+
+def faults(graph: GraphStore) -> str:
+    """Return every Fault's capability and message, in brackets, or ''."""
+    found = [
+        f"{n.props.get('capability')}: {n.props.get('message')}"
+        for n in graph.list_nodes("Fault")
+    ]
+    return f" ({'; '.join(found)})" if found else ""
+
+
+def verdict(
+    report: Callable[[str], None], run_id: str, *, passed: bool, lines: list[str]
+) -> bool:
+    """Print the round's verdict line, then its evidence lines; return *passed*."""
+    report(f"{run_id}  {'PASS' if passed else 'FAIL'}")
+    for line in lines:
+        report(f"  {line}")
+    return passed
diff --git a/pyproject.toml b/pyproject.toml
index 57aa18a0..1b8bb883 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -1,6 +1,6 @@
 [project]
 name = "trading-agents"
-version = "0.132.01"
+version = "0.133.00"
 description = "An operator-controlled, single-user, agent-based trading system. Domain logic lives only in agents; the kernel is plumbing; contracts are the shared boundary."
 requires-python = ">=3.13"
 dependencies = [
diff --git a/scripts/run_hold_drill.py b/scripts/run_hold_drill.py
new file mode 100644
index 00000000..ac99f503
--- /dev/null
+++ b/scripts/run_hold_drill.py
@@ -0,0 +1,103 @@
+"""Run the hold drill: a held run asks the operator on a test bot and acts on the press.
+
+Agent: tooling
+Role: work-queue 120 (a) (DL-330): read the env file without loading it, refuse an
+      unsafe start, then run two rounds of the dispatcher's own fire on an in-memory
+      graph (Run now, then Skip today) and print what each round sent, recorded and did.
+External I/O: reads the env file; Telegram's Bot API as the test bot; stdout.
+
+Run it from the main checkout, which holds the only .env:
+  .venv/Scripts/python.exe scripts/run_hold_drill.py
+  .venv/Scripts/python.exe scripts/run_hold_drill.py --poll-seconds 300
+The second form answers a press as late as the fleet's ten-minute fires can.
+Exit code: 0 when both rounds pass, 1 when one does not, 2 when refused.
+"""
+
+from __future__ import annotations
+
+import argparse
+import os
+import sys
+import time
+from datetime import UTC, datetime
+from pathlib import Path
+from typing import TYPE_CHECKING
+
+if TYPE_CHECKING:
+    from collections.abc import Callable
+
+_ROOT = Path(__file__).resolve().parents[1]
+if str(_ROOT) not in sys.path:
+    sys.path.insert(0, str(_ROOT))
+
+from orchestration.hold_drill_guard import (  # noqa: E402
+    DrillRefusedError,
+    bot_id,
+    drill_values,
+)
+
+
+def main(argv: list[str] | None = None) -> int:
+    """Refuse, or run both rounds and print each one's verdict."""
+    args = _parser().parse_args(argv)
+    from dotenv import dotenv_values
+
+    now = _now()
+    try:
+        values = drill_values(os.environ, dotenv_values(args.env_file), now=now)
+    except DrillRefusedError as refused:
+        print(f"REFUSED: {refused}")
+        return 2
+    from orchestration.hold_drill import Drill, run_drill
+    from orchestration.settings import OrchestratorSettings
+    from orchestration.telegram_client import TelegramClient
+
+    print(
+        f"HOLD DRILL  test bot {bot_id(values.bot_token)}, a poll every "
+        f"{args.poll_seconds} s, at most {args.wait_minutes} min a round"
+    )
+    drill = Drill(
+        telegram=TelegramClient(api_token=values.bot_token, chat_id=values.chat_id),
+        settings=OrchestratorSettings(_env_file=None),
+        poll_seconds=args.poll_seconds,
+        wait_seconds=args.wait_minutes * 60,
+        sleep=_sleep,
+        report=print,
+    )
+    passed = run_drill(drill, today=now.date())
+    print(f"HOLD DRILL  {sum(passed)} of {len(passed)} rounds passed")
+    return 0 if all(passed) else 1
+
+
+def _now() -> datetime:
+    return datetime.now(tz=UTC)
+
+
+def _sleep(seconds: float) -> None:
+    time.sleep(seconds)
+
+
+def _bounded(low: int, high: int) -> Callable[[str], int]:
+    def parse(raw: str) -> int:
+        value = int(raw)
+        if not low <= value <= high:
+            raise argparse.ArgumentTypeError(f"must be {low} to {high}")
+        return value
+
+    return parse
+
+
+def _parser() -> argparse.ArgumentParser:
+    parser = argparse.ArgumentParser(description="the hold drill on a test bot")
+    parser.add_argument("--env-file", default=".env", help="the env file to read")
+    parser.add_argument(
+        "--poll-seconds", type=_bounded(1, 600), default=5, help="seconds between polls"
+    )
+    parser.add_argument(
+        "--wait-minutes", type=_bounded(1, 30), default=10, help="wait for each press"
+    )
+    return parser
+
+
+if __name__ == "__main__":
+    sys.exit(main())
diff --git a/uv.lock b/uv.lock
index eb124802..a2d99c22 100644
--- a/uv.lock
+++ b/uv.lock
@@ -3669,7 +3669,7 @@ wheels = [

 [[package]]
 name = "trading-agents"
-version = "0.132.1"
+version = "0.133.0"
 source = { virtual = "." }
 dependencies = [
     { name = "cryptography" },
```

---

## Appendix C — the 21 breaks, as exact replacements

Each break replaces one text, exactly once, in one built file; the named test must fail; then `git
checkout -- <file>` restores it. **G** = `orchestration/tests/test_hold_drill_guard.py`, **D** =
`orchestration/tests/test_hold_drill.py`, **C** = `tests/test_run_hold_drill_cli.py`.

| # | File | Replace | With | Must fail |
| --- | --- | --- | --- | --- |
| B1 | `orchestration/hold_drill_guard.py` | the line `_refuse_window(now)` in `drill_values` | deleted | G4 |
| B2 | the same | `if fleet and bot_id(fleet) == bot_id(token):` | `if fleet and fleet == token:` | G3 |
| B3 | the same | `fleet = (dotenv.get(FLEET_BOT) or environ.get(FLEET_BOT) or "").strip()` | `fleet = (dotenv.get(FLEET_BOT) or "").strip()` | G3 |
| B4 | the same | `((DRILL_BOT, token), (CHAT, chat))` | `((DRILL_BOT, token),)` | G1 |
| B5 | the same | `return head if colon and head.isdigit() else ""` | `return head if colon else ""` | G2 |
| B6 | the same | `bot_token: str = field(repr=False)` | `bot_token: str` | G5 |
| B7 | `orchestration/hold_drill.py` | in `prior_sessions`, the step back `day -= timedelta(days=1)` before the session check | the same line moved after the `found.append(day)` block, so today is checked first | D1 |
| B8 | the same | the line `_drain(drill.telegram)` | deleted | D7 |
| B9 | the same | `if waited >= drill.wait_seconds:` | `if waited >= drill.wait_seconds * 2:` | D5 |
| B10 | the same | `if hold is None or "notified_at" not in hold.props:` | `if hold is None:` | D6 |
| B11 | the same | `FIRST_FIRE = time(22, 30, 5)` | `FIRST_FIRE = time(22, 20, 5)` (before the placing window) | D2 |
| B12 | the same | `Next message: press {button}.` | `Next message: press a button.` | D2 |
| B13 | the same | `ROUNDS: tuple[Answer, ...] = ("run_now", "skip_today")` | `ROUNDS: tuple[Answer, ...] = ("skip_today", "run_now")` | D10 |
| B14 | the same | `DRILL_FAILURE = "transient:execution:alpaca-broker:hold-drill"` | `DRILL_FAILURE = "transient:operator:anthropic:hold-drill"` (a degradable agent) | D2 |
| B15 | `orchestration/hold_drill_verdict.py` | the four conditions of `passed` (the answer, the act, the RunRequest, the cursor) | `not pending` alone: the answer and act checks go together, because on the other button the dispatcher also does the other act | D4 |
| B16 | the same | the line `and not pending` | deleted | D9 |
| B17 | the same | `f"faults    {len(graph.list_nodes('Fault'))}{faults(graph)}"` | the same without `{faults(graph)}` | D8 |
| B18 | `scripts/run_hold_drill.py` | the line `now = _now()` in `main` | above it: `__import__("dotenv").load_dotenv(args.env_file)` | C4 |
| B19 | the same | `return 0 if all(passed) else 1` | `return 0` | C3 |
| B20 | the same | `type=_bounded(1, 600)` | `type=int` | C5 |
| B21 | the same | the refusal's `return 2` | `return 1` | C1 |

The byte-exact replacements are the planner's `s295_breaks.py` (kit `wq120-2026-11-28/`), which plants
each, runs the three test files, and prints every test that failed.
