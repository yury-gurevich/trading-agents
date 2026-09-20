<!-- Agent: planning | Role: sprint handover -->
# Sprint 219 — the human is told a run is held, and can answer from the phone or the dashboard

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-219-the-human-is-told-and-can-answer`
**Status:** SPEC
**Version:** *next available MINOR at merge* — the fleet gains a channel it did not have. Under the
widened scheme (`MAJOR.MMM.PP`, operator 2026-09-20) that is `0.101.00` if `main` is still `0.100.00`.
**Effort:** L — the largest of the three. Read "If you are running long" before you start.
**Decisions:** [DL-179](../design-log.md) §8–§9 (two answers only; three sprints, one deploy) ·
[DL-182](../design-log.md) (the answer is a graph fact; polling, not a webhook) · third of three
sprints for work-queue item **58** · builds on S217 (`FleetPreflight`) and S218 (`RunHold`)

**Builder:** GitHub Copilot. Every behaviour is pinned by a row in the test plan.
**If a number you measure differs from one written here, stop and report. Do not adjust and continue.**

🚨 **This is the sprint that unblocks the deploy.** S217 and S218 are merged and *not* deployed
because together they hold a run with nobody told, which is worse than today. Nothing deploys until
this merges.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/master/laws/laws.md` (v1.4) | The master's locked constitution | **LOCKED.** Read-only, and this sprint must not make the master do anything |
| `docs/laws/flow.md` | The umbrella law for the run's flow | Read-only |
| `docs/laws/conventions.md` | Clause-citation rules for tests | Read-only |
| `docs/laws/drift-register.md` | The one law-adjacent file you may append to | You add **one** row (scope item 8) |

### The rule

1. **Before writing code**, read `docs/laws/flow.md`, [`docs/laws/conventions.md`](../laws/conventions.md)
   and [`docs/laws/drift-register.md`](../laws/drift-register.md), plus `DRIFT-068` specifically.
2. **Answer the law-cycle question below.**
3. **Write the Law reading record** (at the bottom) **before** your first code change.
4. **If a law contradicts this spec, STOP and report.**
5. Tests for behaviour a clause governs cite the clause ID in their docstring (conventions §3).

### 🩹 The law-cycle question — answered **NO, with one drift row**

No `contracts/` file changes and no *agent* makes a new guarantee: everything here lives in
`orchestration/` and `surfaces/`, neither of which has a law book. That silence is already recorded
as **DRIFT-068** for the placement gate; this sprint adds a second guarantee of the same shape (the
operator is told, and an answer decides) and so adds **DRIFT-069**. Do **not** create a law book.

🪤 **The master must stay untouched.** It is tempting to let the master own the channel — it is awake
20:25–00:30 and already owns secrets. [DL-182](../design-log.md) rejected that: its law book is
**LOCKED v1.4** and a new capability costs a full cycle. If you find yourself editing anything under
`agents/master/`, stop and report.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/telegram_*.py` (new) | `docs/laws/flow.md` | a new external I/O boundary on the run's entry path |
| `orchestration/scheduled_dispatch*.py` | `docs/laws/flow.md`, `DRIFT-068` | the run's entry point |
| `surfaces/dashboard/*` | `docs/laws/flow.md` | a read-mostly surface gaining its first write |
| `orchestration/packs/trading_graph_vocabulary.json` | — | property-enforced labels fail closed |

⚠️ **The one invariant: a ready fleet runs exactly as today.** When the latest `FleetPreflight`
passed and is fresh, the dispatcher places the same `RunRequest` with the same id, sends **no**
Telegram message, and writes **no** new node. If your change alters any existing S218 behaviour for
that case, stop and report.

---

## Goal

After this sprint, a held run reaches the operator's phone within one dispatcher fire, and the
operator's answer — given from Telegram **or** the dashboard — decides whether the run happens.
`run_now` places the run despite the failed check. `skip_today` records the decision and places
nothing. Silence still means no run ([DL-179](../design-log.md)).

## Why (context)

Operator, 2026-09-19 ([DL-179](../design-log.md)): *"If anything is not funded or is not accessible
then the start should be delayed first for one hour then for another hour, Human needs to decide."*
S217 built the check and S218 built the hold. **Nobody is told.** A hold today is visible only to
someone who opens the dashboard, which runs on the operator's own machine.

### Measured, 2026-09-20 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Telegram credential | **proven end to end** — `@yury_trading_alerts_bot`, `getMe` ok, `sendMessage` delivered | *[measured 2026-09-20, DL-179]* `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` in `.env` |
| Bot privacy mode | `can_read_all_group_messages: false` | *[measured]* `getMe` |
| Fleet ingress | **every app `--ingress internal`** | *[measured]* `infra/deploy-agents.ps1:723` |
| Dashboard deployment | **not deployed** — no Dockerfile under `surfaces/`, absent from `$AGENTS` | *[measured]* `infra/deploy-agents.ps1:46-53` |
| Dispatcher job secrets | `POSTGRES_DSN` + Service Bus vars, set by the deploy script | *[measured]* `infra/deploy-agents.ps1:472-473` |
| Dispatcher job timeout | `--replica-timeout 1800` (30 min) | *[measured]* `infra/deploy-agents.ps1:507` |
| Dispatcher cron | `30 22 * * 1-5` | *[measured]* `orchestration/packs/trading_tunables.json` → `dispatcher.cron` |
| Agents' scale window | `start 30 22`, `end 30 00` UTC | *[measured 2026-09-19, S218]* scanner KEDA rule |
| Dashboard HTTP shape | raw WSGI; **`/api/chat` is the only non-GET route** — everything else 405s | *[measured]* `surfaces/dashboard/app.py:62-67` |
| Module sizes — **TOTAL lines, which is what the gate counts** | `orchestration/scheduled_dispatch.py` **147**, `surfaces/dashboard/app.py` **184**, `surfaces/dashboard/projections_verdict.py` **167**, `surfaces/dashboard/settings.py` **160**, `scripts/dispatch_scheduled_run.py` **118**, `orchestration/scheduled_dispatch_gate.py` **71**, `orchestration/fleet_readiness.py` **64** | *[measured 2026-09-20 on `f5c51de`]* `wc -l`, which agrees with `grep -c ''` and with `scripts/check_module_size.py:39` (`len(read_text().splitlines())`) |
| `RunHold` today | key `hold:<run_id>`, then `hold:<run_id>:<n>`; props `run_id, as_of, held_at, state, readiness_state, preflight_key, failures, released_at` | *[measured]* S218, `orchestration/scheduled_dispatch_gate.py` |
| Append-only rule | adding a **new** key to a node merges; changing an **existing** key's value is refused | *[measured]* `kernel/graph_postgres_queries.py:18-42` |

🪤 **Two of those are traps.** `orchestration/scheduled_dispatch.py` at **147** is three lines from the 150-line
warning, and `surfaces/dashboard/app.py` at **184** is sixteen from the 200-line hard block. **New logic goes in new
modules**, not into either of those.

🚨 **Count TOTAL lines, including blank ones.** The gate does (`scripts/check_module_size.py:39`). Counting **non-blank** lines gives **115** and **161** for those two files — both correct, both the wrong metric, and both comfortably under a limit the file is actually close to. A builder stopped on exactly this discrepancy on 2026-09-20, which is the stop rule working as intended; the spec was at fault for not saying which count it meant.

---

## Scope — and what is deliberately NOT here

1. **`orchestration/telegram_client.py` (new, under 120 lines).** A thin, typed Telegram port.
   - `send_hold_notice(...) -> int` posts `sendMessage` with an inline keyboard of exactly **two**
     buttons, `callback_data` `run_now:<run_id>` and `skip_today:<run_id>`. Returns the `message_id`.
   - `poll_answers(...) -> tuple[TelegramAnswer, ...]` calls `getUpdates` and returns one record per
     `callback_query` it understands (`update_id`, `answer` in {`run_now`, `skip_today`}, `run_id`,
     `callback_query_id`). Anything else is **ignored without raising**.
   - `confirm(*, up_to_update_id)` calls `getUpdates` with `offset=<id>+1` so Telegram drops the
     confirmed updates. 🪤 **This is the offset story, and it must not become local state:** the
     graph is append-only, so a mutable "last offset" node is impossible. Telegram's own
     confirmation is the cursor.
   - `ack_button(*, callback_query_id, text)` calls `answerCallbackQuery` so the button stops
     spinning in the operator's client. **Not optional** — without it the phone shows a hung button.
   - Every call is bounded by a timeout and **never raises to the caller**. A Telegram outage must
     not stop the dispatcher: failures return a falsy result and are recorded as a fault.
2. **Notice on hold, exactly once per hold.** When `hold_unready_run` writes a **new** active hold,
   send the notice and merge `notified_at` and `notice_message_id` onto **that hold node** (adding
   new keys is allowed — see the measured table). A fire that finds an already-notified active hold
   sends **nothing**. A released hold is never re-notified.
   - The message names the run, what failed (the recorded strings, as S218 shows them), and **when
     the answer will be acted on** (`act_by`), because the answer is not instant.
     🚨 **DL-182 calls this out:** without it the operator presses a button, nothing happens for
     minutes, and a working channel reads as broken.
3. **`RunHoldAnswer`, one append-only fact, written by both surfaces.** Key
   `answer:<run_id>:<source>:<ordinal>`; props `run_id`, `as_of`, `answer` (`run_now` | `skip_today`),
   `source` (`telegram` | `dashboard`), `answered_at`, `update_id` (Telegram only; `0` for dashboard).
   - **Dedupe on `update_id`:** an update already recorded is never written twice.
   - **First answer wins.** If more than one exists for a run, the earliest `answered_at` decides and
     the rest are recorded but inert. Do not try to "cancel" a written fact.
4. **Act on the answer, at the next fire.** In the placement path, after readiness is read and before
   a hold is written:
   - An effective `run_now` for this run id → **place the run** exactly as a ready fleet would, and
     merge `answered_with="run_now"` onto the active hold. The operator overrides the check; that is
     the whole point of asking.
   - An effective `skip_today` → place nothing, merge `answered_with="skip_today"`, print
     `skipped <run_id> reason=operator`, exit **0**.
   - No answer → behave exactly as S218 does today.
5. **Poll inside the dispatcher.** On each fire, before deciding: `poll_answers`, write any new
   `RunHoldAnswer` facts, `ack_button` each, then `confirm` up to the highest update id handled.
   Wrapped so a Telegram failure degrades to "no answer", never to a crash.
6. **Dashboard answer button.** A `POST /api/hold/answer` route taking `{run_id, answer}` writes the
   same `RunHoldAnswer` with `source="dashboard"`. The readiness panel shows **Run now** and
   **Skip today** buttons **only while an active hold exists**, and they disappear once answered.
   🪤 **DL-47: never show an unwired control.** Put the logic in a new module — `app.py` is 16 lines
   from the hard block and currently 405s every non-GET but `/api/chat`.
7. **Cron and secrets.**
   - `dispatcher.cron` gains fires at roughly `30,40,50 22` and `0,10,20 23` on weekdays, however
     `trading_tunables.json` best expresses it. Worst-case answer latency becomes **about 10 minutes**.
     State the value you chose in the Closeout.
   - Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` to the dispatcher job's env in
     `infra/deploy-agents.ps1`, the same way `POSTGRES_DSN` is planned (`:472-473`), and extend the
     `Assert-EnvPreserved` planned list so a later deploy cannot silently drop them.
8. **Vocabulary and drift row.** Add `RunHoldAnswer` with its props, and `notified_at`,
   `notice_message_id`, `answered_with` to `RunHold`, in `trading_graph_vocabulary.json`. Append
   **DRIFT-069**: the dispatcher now guarantees "a held run is announced once, and an operator answer
   decides it", and no law book declares it.

### Out of scope (do NOT build this sprint)

- **A webhook, external ingress, or any deployed HTTP surface.** [DL-182](../design-log.md); operator
  2026-09-20: *"poll then. if we have problems with latency we will change it later."*
- **"Run at a later time."** DL-179 §8 — it needs wake-on-demand, which does not exist.
- **Anything under `agents/master/`.** DL-182.
- **A law book for the dispatcher.** The drift row only.
- **Free-text Telegram commands.** Buttons only; a text message to the bot is ignored.
- **Deploying.** The full `up` is a separate, operator-approved step after this merges.

### The road not taken (LAW-06)

- **Webhook.** Rejected in [DL-182](../design-log.md) on measured blast radius: a 17th app, the
  fleet's first external ingress, and a third scale-rule shape in loops that have already mishandled
  the second (the S210 `daily-master-window` flattening).
- **A long-lived polling replica.** Rejected: a hung replica risks the schedule itself, for latency
  DL-179 §8 says cannot be spent.
- **A mutable "last Telegram offset" node.** Impossible under the append-only store, and unnecessary:
  Telegram's own `offset` confirmation is the cursor.

---

## The design decisions this sprint has to make

1. **What `act_by` says in the notice.** It must be true given the cron you choose in scope item 7.
   Record the wording in the Closeout.
2. **How the cron expresses two ranges** in `trading_tunables.json` — one field the deploy script
   already understands, or a documented second field. Say which, and why.
3. **What happens to an answer that arrives after the window.** Recommended: it is still recorded and
   still prevents a run; it simply cannot cause one. Say what you chose.

---

## Blast radius — measured 2026-09-20

**Changed:** `orchestration/` (two new modules, the gate, settings), `surfaces/dashboard/` (one new
module, one route, the readiness panel), the vocabulary pack, `trading_tunables.json`,
`infra/deploy-agents.ps1` (job env only), the drift register.

**Not changed:** every agent, `contracts/`, `kernel/`, the master, all KEDA scale rules, every
existing route, the 16-app shape.

🚨 **The deploy is a full `up`, not an image-only retag** — the vocabulary pack moves again and the
dispatcher job's env changes. It goes out together with S217 and S218.

---

## Steps, in order

| # | Do | Expected |
| --- | --- | --- |
| 1 | `git worktree add ../trading-agents-sprint-219-the-human-is-told -b sprint-219-the-human-is-told-and-can-answer origin/main`, open **that folder** | a worktree with **no** `.env` |
| 2 | Read the laws; fill the Law reading record | — |
| 3 | Record the three design decisions in `docs/design-log.md` (next free DL; DL-182 is the latest) | — |
| 4 | Write tests C1–C18. Run the focused suite | **red**, and paste it |
| 5 | Implement scope items 1–8 | — |
| 6 | Same command | **green** |
| 7 | **DL-70.** Plant each guard below, watch its test go red, restore it. Paste each red line | see "Guards to plant" |
| 8 | `make ci > ci.txt 2>&1; echo $?`, **never piped** | exit **0**, 100.00 % coverage |
| 9 | Push; `make gate-ran` from the worktree | `GATE PROVEN`, printed SHA equals `git rev-parse HEAD` |
| 10 | Fill the handback, set **Status:** `BUILT`, commit, push, `make gate-ran` again | `GATE PROVEN` for the final SHA |

**Guards to plant (step 7):** (a) notify on every fire instead of once per hold, so C4 goes red;
(b) drop the `update_id` dedupe, so C8 goes red; (c) let the last answer win, so C9 goes red;
(d) remove the `act_by` line from the notice, so C3 goes red; (e) let a Telegram timeout propagate,
so C12 goes red; (f) show the buttons with no active hold, so C16 goes red.

🚨 **Every Telegram call in tests is a fake.** No test may touch the network or read `.env`. Inject
the port and assert on what was sent.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| C1 | 🎯 a ready fleet is silent | fresh passing check | run placed; **zero** Telegram calls; no `RunHoldAnswer`; no new props on any hold |
| C2 | 🎯 a new hold sends one notice | failing check, no prior hold | exactly one `sendMessage`; hold carries `notified_at` and `notice_message_id` |
| C3 | 🪤 the notice says when it will be acted on | as C2 | text contains the `act_by` time and both button labels; `callback_data` is `run_now:<run_id>` / `skip_today:<run_id>` |
| C4 | 🎯 a second fire on the same hold is silent | fire twice while failing | still exactly **one** `sendMessage` in total |
| C5 | a re-hold after release notifies again | S218's B16 sequence | the **new** hold node gets its own notice; the released one is untouched |
| C6 | 🎯 `run_now` places the run despite a failing check | a `run_now` answer for today | `RunRequest` placed with the id a ready fleet would use; hold carries `answered_with="run_now"` |
| C7 | 🎯 `skip_today` places nothing | a `skip_today` answer | no `RunRequest`; `answered_with="skip_today"`; stdout `skipped <run_id> reason=operator`; exit **0** |
| C8 | 🪤 the same Telegram update is never recorded twice | `poll_answers` returns the same `update_id` on two fires | exactly one `RunHoldAnswer` |
| C9 | 🪤 first answer wins | `skip_today` at T, `run_now` at T+1m | the run is **not** placed; both facts exist |
| C10 | the button is acknowledged | any answer | `answerCallbackQuery` called with that `callback_query_id` |
| C11 | updates are confirmed | two updates handled | `getUpdates` called with `offset = max(update_id) + 1` |
| C12 | 🪤 a Telegram outage does not stop the dispatcher | the port raises on every call | the hold is still written; exit **0**; a fault is recorded; no traceback |
| C13 | a text message to the bot is ignored | `getUpdates` returns a plain message | no `RunHoldAnswer`, no crash |
| C14 | an answer for another day is inert | an answer carrying yesterday's run id | today's decision is unaffected |
| C15 | the calendar still wins | non-session day plus a failing check | `skipped`, no hold, **no** Telegram call |
| C16 | 🎯 dashboard buttons appear only with an active hold | active hold / no hold / released hold | present in the first case only |
| C17 | 🎯 the dashboard writes the same fact | `POST /api/hold/answer` | a `RunHoldAnswer` with `source="dashboard"`, `update_id=0`; the dispatcher then honours it exactly as C6/C7 |
| C18 | 🪤 UI and message wording carry no internal ids | C3's text and C16's labels | no match for `S\d{3}`, `DL-\d+`, `DRIFT-` or `MST-` |

---

## Success factors

- [ ] A ready fleet is byte-for-byte unchanged, and silent (C1, C15).
- [ ] A held run is announced **once**, and says when the answer lands (C2–C5).
- [ ] Either surface can answer, and both write the same fact (C6, C7, C17).
- [ ] Replays, double presses and late answers cannot change a decision (C8, C9, C14).
- [ ] Telegram being down degrades to "no answer", never to a failed dispatch (C12, C13).
- [ ] No unwired control is ever shown (C16); no internal ids reach a human (C18).
- [ ] Drift row filed; the three design decisions recorded with rejected alternatives.
- [ ] Every guard planted, watched red, restored (step 7), stated per guard.
- [ ] `agents/master/` untouched; `contracts/` and `kernel/` untouched.
- [ ] Every touched module under 200 lines; new modules under 150; `scheduled_dispatch.py` and
      `app.py` do not grow past their warnings.
- [ ] `make ci` exit 0, 100.00 % coverage; `GATE PROVEN` for the final SHA.

---

## Traps

- 🪤 **`scheduled_dispatch.py` is 147 lines and `app.py` is 184.** New modules, not new lines there.
- 🪤 **The append-only store refuses a changed value.** `notified_at`, `answered_with` and friends are
  *new* keys on an existing node, which merges. Never try to change `state`. S218's DL-181 is the
  precedent, and S218's amendment R1 is what happens when a released fact is treated as live.
- 🪤 **`getUpdates` and a webhook are mutually exclusive**, and unconfirmed updates expire after 24 h.
  If a webhook was ever set on this bot, polling returns nothing — `getWebhookInfo` says so.
- 🪤 **Two pollers conflict.** Telegram returns `409` if two consumers call `getUpdates` at once. The
  dispatcher is the only poller; the dashboard must never poll.
- 🪤 **A test that reads `.env` passes locally and fails in CI**, which has no `.env`. Inject.

## Guardrails (every sprint)

- Do not deploy. Do not merge. Do not add a tunable that is not in scope item 7.
- Every file ends with a newline. LF only (`.gitattributes` enforces it).
- Do not edit `pyproject.toml` beyond the single version bump.
- If a measured number here differs from what you observe: **stop and report**.

## If you are running long

This is an **L**. If you reach step 6 with scope items 1–4 and 6–8 green but the **poller** (item 5)
incomplete, **stop and hand back what is green**, with the poller explicitly marked not done. A
dashboard-answerable hold with a working notice is already shippable behaviour; a half-written poller
that silently drops answers is not. Do **not** trade test coverage for scope.

---

## Handover — paste this to Copilot

```text
Build sprint S219 exactly as written in docs/sprints/sprint-219-the-human-is-told-and-can-answer.md.

Branch: sprint-219-the-human-is-told-and-can-answer, in its own worktree (step 1). Open THAT
folder as your workspace before doing anything else.

Read DL-179 and DL-182 in docs/design-log.md first. DL-182 decided polling over a webhook and
says why; do not revisit it.

Order is binding:
1. Read docs/laws/flow.md, conventions.md, drift-register.md (DRIFT-068 especially).
   Fill the Law reading record BEFORE any code. The law-cycle answer is NO, plus one drift row.
2. Record the three design decisions in docs/design-log.md (next free DL; DL-182 is latest).
3. Write tests C1-C18 FIRST and paste the red run.
4. Implement scope items 1-8. Paste the green run.
5. Plant guards (a)-(f), paste each red line, restore.
6. make ci > ci.txt 2>&1; echo $?   - never through a pipe. Exit 0, 100.00% coverage.
7. Push, then make gate-ran from the worktree. Printed SHA must equal git rev-parse HEAD.
8. Fill the handback, Status: BUILT, commit, push, make gate-ran again on the final SHA.
   In the Closeout state: the act_by wording, how you expressed the cron, and what you decided
   about a late answer.

DO NOT:
- touch anything under agents/master/. DL-182 rejected master owning the channel.
- build a webhook, external ingress, or any deployed HTTP surface.
- add a "run at a later time" answer. DL-179 section 8.
- let any test touch the network or read .env. Inject the Telegram port and assert what was sent.
- add lines to orchestration/scheduled_dispatch.py (147) or surfaces/dashboard/app.py (184).
  New logic goes in new modules.
- show a dashboard button when there is no active hold.
- put sprint numbers, DL ids, DRIFT ids or MST- ids in any operator-facing text.
- deploy or merge.
Every file you write ends with a newline.
If any measured number differs from the spec, or a law contradicts it: STOP and report.
If you run long, see "If you are running long" - hand back what is green, poller marked not done.
```

---

## Handback contract — MANDATORY

Fill every section below before handing back. A placeholder left unfilled is a returned handback.

## Law reading record — fill BEFORE writing code

| Law file | Version read | What it constrained here |
| --- | --- | --- |
| | | |

## Test plan results — fill at handback

| # | Test name | File | PASS/FAIL | Clause cited |
| --- | --- | --- | --- | --- |
| | | | | |

---

## Closeout — evidence

**Status:**

**Files changed:**

**Design decisions (`act_by` wording / cron expression / late answer):**

**Proof — red run:**

**Guards planted:**

**Proof — `make ci`:**

**Proof — `make gate-ran`:**

**Not met / verified failing:**

---

## Return notes
