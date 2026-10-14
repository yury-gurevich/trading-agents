<!-- Agent: planning | Role: sprint handover -->
# Sprint 275 — the operator hears, at once and in the brief, when a container fails to start, crashes or is killed, and why

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-275-the-operator-hears-when-a-container-fails`
**Status:** MERGED 2026-10-14 — `0.126.00`, fast-forwarded to `82909a54`, tag `v0.126.00`, GATE PROVEN `82909a54` (CI, CodeQL, Security Findings); F1 passed at no cost; not deployed (the operator's call); F2 owed
**Version:** `0.126.00`
**Effort:** L
**Decisions:** [DL-301](../design-log.md) (this sprint's ten decisions, made and measured) · [DL-283](../design-log.md) (the sensor's direction, 2026-10-09) · [DL-297](../design-log.md) amendments 2 and 3 (a clean stop logs nothing; the readiness probe fails after a stop) · [work-queue 119](../work-queue.md)

> **Why this bump kind.** A new capability: the dispatcher job gains a sensor it did not have, two
> graph labels, an operator message and a brief line. MINOR.

> 🔁 **Corrected after the first build's stop, 2026-10-14 18:00 AEDT (planner; DRIFT-114, DL-301 amendment 1).** The builder stopped before any code: § 9's `DSP-OUT-07` asked for one message line per app, kind and exit code, an alarm-event total and an overflow counted with apps, where § 7 and DL-301 D5 group by kind and exit code across apps. **The clause was wrong, not the code.** § 9 now says what § 1 to § 8 do in five clauses: `DSP-OUT-07` (D5's grouping, header and overflow, and the read record's message id, send error and row-limit cut), `DSP-OUT-08` (the brief counts repeats and names kinds with their apps), `DSP-FAIL-04` (a failure before the graph is open prints one line and records nothing), `DSP-IN-05` (an exit whose code cannot be read alarms; a row with no names is `unknown`) and `DSP-IDM-04` (an untold alarm's age is from its recording). § 8's `settings.py` diff words the alarm-groups tunable's `why` as kinds of failure. No other line of the Appendix changed: 18 of the 20 blobs are as before. The stopped handback is commit `1dc6b7ee` on the branch.

> 🔁 **Corrected after the second stop, 2026-10-14 19:27 AEDT (planner; DRIFT-115, DL-301 amendment 2).** The resumed build stopped with all 20 files equal to the Appendix: its A24 found that a `ValueError`'s text reached the `Fault`'s stored traceback, because § 6's `sense_safely` called `_record` inside its `except` block and Python chained the handled error. **The code was wrong, not the clause** (`DSP-SEC-03` stands). § 6's `container_sensor_guard.py` now records once the handler has ended, as `daily_brief_guard.py` on `main` does; it is the only file that changed (re-apply it; 19 of the 20 blobs are as before). The builder's stopped handback is kept in the evidence folder (`codex_stop_drift115/`) and in the sections below until the build fills them again.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `orchestration/laws/dispatcher/laws.md` | The dispatcher's **locked constitution**: scheduled placement, holds, the daily brief, and from this sprint the container sensor | **LOCKED.** This sprint amends it, exactly as the Appendix gives it (§ 9): no other clause changes |
| `orchestration/laws/dispatcher/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | You add ten rows, each citing **your** tests |
| `docs/laws/conventions.md`, `docs/laws/drift-register.md` | Umbrella conventions; the one law-adjacent file you may append to | Read both |

Binding sections here: **`IDN`**, **`IN`**, **`TRG`**, **`OUT`**, **`NEV`**, **`IDM`**, **`FAIL`**,
**`SEC`**, **`OBS`**, **`CAP`**, **`PARAM`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the dispatcher's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes — a new guarantee, and the cycle is owed in full.** No file in `contracts/` changes. The
dispatcher's book goes from v1.2 to **v1.3** with ten new clauses (`DSP-IDN-05`, `DSP-IN-05`,
`DSP-TRG-04`, `DSP-OUT-07`, `DSP-OUT-08`, `DSP-NEV-03`, `DSP-IDM-04`, `DSP-FAIL-04`, `DSP-SEC-03`,
`DSP-OBS-03`), five `PARAM` rows, `CAP` amended, the purpose line, `DSP-IDN-03`'s scope sentence and
`DSP-DEP-01` amended, and a Changelog line — the whole text is the Appendix (§ 9), apply it exactly.
You write: a `test-plan.md` row per new clause citing your tests, the header to v1.3, `DSP-IDN-03`'s
and `DSP-DEP-01`'s descriptions widened as § 9 widens them, and your send-alarm test added to
`DSP-SEC-01`'s row; the dispatcher's row in **both** `docs/laws/ledger.md` and `docs/laws/INDEX.md`
to v1.3 and **42 / 46** (the gate derives it; let it tell you).

🪤 **The rollup is derived, not declared.** On the prototype the gate read 42 / 46: ten new clauses,
all proven, on top of the 32 / 36 before.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/container_*.py` (nine new modules) | the dispatcher's `laws.md` + `test-plan.md`; `docs/laws/conventions.md` | The ten new clauses; `DSP-SEC-01` (the port holds the credential), `DSP-SEC-02` (amounts leave only in the brief) |
| `scripts/dispatch_scheduled_run.py` | same | `DSP-TRG-04` (every fire, after the dispatch), `DSP-FAIL-04` (the fire's exit code is the dispatch's), `DSP-TRG-02` and `DSP-OUT-02` unchanged |
| `orchestration/daily_brief_text.py`, `daily_brief_facts.py` | same, plus `DSP-OUT-06` | `DSP-OUT-08` (one line, before needs-you, only after the first read); `DSP-OUT-06`'s other lines unchanged |
| `orchestration/telegram_client.py` | same | `DSP-SEC-01`; `CAP.telegram` gains `send_alarm` |
| `orchestration/settings.py` | same, `PARAM` | five tunables, each a `PARAM` row (the PARAM/settings gate) |
| `orchestration/packs/trading_graph_vocabulary.json` | `kernel/graph_vocabulary.py`'s docstring; ADR-0012 | two labels, one edge type, one signature, two property lists; the guarded store refuses anything undeclared |
| `orchestration/Dockerfile` | — | the image copies files by name; an existing test reads the entrypoint's imports |
| `infra/deploy-agents.ps1` | `CLAUDE.md` (full cycle: production state) | `DSP-SEC-03` (one role, one workspace, no secret) |
| `orchestration/tests/test_dispatcher_capability.py` and `scheduled_dispatch_human_helpers.py` | `CAP` | the two existing test files this sprint edits, exactly as § 10 gives |

⚠️ **The sensor never changes the fire.** A dispatch's printed line, its exit code, its placement,
hold, notice and brief (but for the new line) are byte-for-byte what they were, whether the sensor
reads, fails or is not configured. If your change would make any existing test of the dispatcher,
the brief or the entrypoint fail, stop and report.

---

## Goal

From the first fire after the deploy, every dispatcher fire reads the platform's container events
from the log workspace as the job's own managed identity, records each one it keeps in the graph,
and sends the operator one Telegram message naming every alarm not yet told — which apps, what
happened, when, and the line of the container's own console that says why. From the sensor's first
read on, the daily brief carries one line on what the sensor saw in the last day. No failure of the
sensor changes anything the fire did.

## Why (context)

The operator, 2026-10-09: *"I want to know when and wht containers do not start cleanly"*
([DL-283](../design-log.md)). In the 30 days the workspace keeps there were 456 crash, kill and
failed-start events on 21 days, and none reached the operator except through a session reading the
log by hand. The shutdown path is now deployed and proven ([S272](sprint-272-a-container-ends-cleanly-on-the-stop-signal.md),
[DL-297](../design-log.md) amendment 3): every container ends by itself on the stop signal, so a kill
is no longer the known case — it is a fault, and nothing tells anyone when one happens. A weekly
reminder has carried this since 2026-10-09.

### Measured, 2026-10-14 — read these before designing

Raw replies and scripts: OneDrive `trading-agents-data/wq119-2026-10-14/`. Every read below was
read-only, as the planner's own Azure login.

| Claim | Value | How it was measured |
| --- | --- | --- |
| The platform words each kind the same way every time | an exit is reason `Error` with the code in the text, `Container 'x' was terminated with exit code '137'`; 102 rows with code 1, 55 with 137, **none with 0** | *[measured]* `alarms.json`: `ContainerAppSystemLogs_CL`, 30 days, grouped by reason, level and the code `extract`ed from `Log_s` |
| The other kinds | `OOMKilled` 38, `ContainerBackOff` 233 (*Persistent Failure to start container*), `KEDAScalerFailed` 195 on one day (*no desiredReplicas specified*), `KEDAScaleTargetActivationFailed` 1, `Preempted` 5, `ScaleDown` 38 (*deleting pod for node scale down*) | *[measured]* `reasons.json`, `alarms.json` |
| Rows with no reason and no app name | **171**, level `error`, *Error provisioning revision scanner--0000174*: the app is in the revision's name | *[measured]* `errlevel.json` |
| Noise | `ReplicaUnhealthy` 875 (the master's readiness probe), `AssigningReplicaFailed` 809 (*Waiting for infrastructure*), `ScaledObjectCheckFailed` 1,993, `ScaledObjectDeleted` 987, `FailedGetScale` 4 | *[measured]* `reasons.json` |
| A repeat is a new row with a rising count | two rows of one master kill share `TimeGenerated` and carry `Count_d` 1 then 2 | *[measured]* sample of three `Error` rows |
| The dispatcher job's own rows | name the job in `JobName_s`, the app column empty; in 30 days every execution completed (no failure row seen) | *[measured]* job rows grouped by reason |
| Ingestion lag | `ingestion_time()` answers on this table; over 48 hours a row arrived up to **2 min 36 s** after its event, median 3.7 s | *[measured]* `max(ingestion_time() - TimeGenerated)`, 1,347 rows |
| The last console line is not the why | the lines of one Python traceback share a timestamp (their order in a reply is arbitrary); the master's last lines before each kill are the Key Vault SDK's `Request URL:` log | *[measured]* `lastlines.json`, `exit1.json`: each kill or exit joined to its replica's console (`ContainerGroupName_s`) |
| Chosen by shape, the exception line is the why | 2026-09-25: `urllib.error.HTTPError: HTTP Error 404: Not Found` on 13 apps; 2026-09-28: `ValueError: credential test declaration is required when a secret map is configured` (the fault [DL-296](../design-log.md) fixed) | *[measured]* the prototype's replay, below |
| The job has no identity | `identity: None`; env `POSTGRES_DSN`, two Service Bus keys, `GRAPH_VOCABULARY_B64`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`; cron `*/10 22-23 * * 1-5`; image `s272` | *[measured]* `az containerapp job show` |
| The operator can grant the role | the operator's account is Owner of the subscription; Log Analytics Reader carries `*/read` and the two query actions; `az containerapp job identity assign --system-assigned` exists in the installed CLI | *[measured]* `az role assignment list`, `az role definition list`, `--help` |
| The workspace | `trading-agents-logs`, customer id `a281f88c-…`, retention 30 days | *[measured]* `az monitor log-analytics workspace show` |
| The prototype against the live workspace | four reads of a day or a week: **1.3 to 3.6 s**. At 2026-09-25 01:00 UTC: 491 rows, 488 alarms and 3 reports kept, a why for 193, one message of four lines (701 characters). At 2026-09-29 00:00: four lines, the first naming the master's refusal. At 2026-10-11 14:00: the master's two kills of the retag day | *[measured]* `f0_live_replay.py` (the prototype with the planner's CLI token in place of the job's identity, an in-memory graph, a port that prints) → `f0_replay_*.txt` |
| The prototype passes the gate | `make ci` exit 0 in one run, all 16 steps: 4,930 passed, 9 skipped, 100.00 %, on `main` at `be0aec51` merged into the prototype, at `0.126.00` | *[measured]* `ci_prototype_merged.txt` |
| The corrected prototype passes the gate (DRIFT-114) | `make ci` exit 0 in one run, all 16 steps: 4,930 passed, 9 skipped, 100.00 %, on `proto-s275` at `3fb32ada`, at `0.126.00` | *[measured]* `ci_prototype_drift114.txt` |
| The guard records after its handler (DRIFT-115) | on `proto-s275` at `0ac22917`: the planner's tightened test red on the old guard (the plant in the stored traceback) and green on the new; `make ci` exit 0 in one run, all 16 steps: 4,930 passed, 9 skipped, 100.00 %; 38 planted breaks, 38 red in one saved run, judged by the planner's tests and `tests/test_dispatch_scheduled_run.py` (the file of the row *The planner's tests catch the breaks* holds the run before B28 was re-aimed, 36 of 37) | *[measured]* `ci_prototype_drift115.txt`, `breaks_on_prototype_drift115.txt` |
| The planner's tests catch the breaks | 37 planted breaks, 37 red (one re-aimed: its first form changed nothing observable) | *[measured]* `break_s275.py` → `breaks_on_prototype.txt` |
| The job's identity endpoint answers as documented | `IDENTITY_ENDPOINT` and `IDENTITY_HEADER` in the job's env; `GET {endpoint}?resource=https://api.loganalytics.io&api-version=2019-08-01` with header `X-IDENTITY-HEADER` returns `access_token` | *[ASSUMED — read in Microsoft's Container Apps managed-identity documentation, not measured]* the job has no identity to measure with; settled by F2 after the deploy |
| How fast the role takes effect for a new identity | — | *[ASSUMED — not measured]* F2 reads the first fire after it |

---

## Scope — and what is deliberately NOT here

1. **The classification** (`orchestration/container_events.py`, § 1): a platform row becomes an alarm,
   a report or nothing, per DL-301 D3; the app from the row, the job, or the revision's name.
2. **The why** (`container_lines.py`, § 2): the replica's line chosen by shape inside a window, masked
   and cut.
3. **The two queries and the reader** (`container_queries.py`, `container_logs.py`, § 3, § 4): by
   ingestion time; as the job's managed identity through one GET and one POST; no SDK.
4. **The read, the record and the tell** (`container_sensor_graph.py`, `container_sensor.py`, § 5,
   § 6): the window, the dedupe by the row, one message for the untold alarms, `TOLD` edges.
5. **The words** (`container_alarm_text.py`, § 7) and **the brief's line** (`container_brief.py`,
   § 8, plus the brief's two existing modules).
6. **The fault boundary and its wiring** (`container_sensor_guard.py`, § 6, and the entrypoint).
7. **Five tunables, `send_alarm`, the vocabulary, the image's file list, the deploy step** (§ 8).
8. **The law cycle** (§ 9) and **the two existing test edits** (§ 10).

### Out of scope (do NOT build this sprint)

- **A dashboard tile or a health-signal count for container events.** The records make them possible;
  each is its own sprint.
- **Acting on a container** — restart, scale, anything through the management API (`DSP-NEV-03`).
- **Reading outside the dispatcher's window**, and a watchdog for the dispatcher itself not starting
  (DL-283's Azure Monitor alert, named in DL-301).
- **Running `infra/deploy-agents.ps1` or any `az` command.** The deploy is the planner's, after merge.
- **Any other law clause**, any file in `contracts/`, `kernel/`, `agents/`, `surfaces/`.
- **No ADR.** DL-301 records the decisions.

### The road not taken (LAW-06)

Each is recorded with its reason in [DL-301](../design-log.md) *Ruled out*: an Azure Monitor alert
rule (a second channel, a charge, nothing in the graph); the Azure SDK (two packages in the image for
one GET and one POST, and a lock a builder without network cannot re-resolve); a service principal
with a secret (a credential to store and rotate); the role on the group or the subscription (wider
than one workspace); a read by event time with a margin (a row 2 min 36 s late is lost); a cursor node
updated each fire (the graph is append-only); one message line per app (57 lines on 2026-09-25); the
last console line as the why (measured: SDK chatter or a traceback frame); one message per event (488
on 2026-09-25).

---

## The design decisions — made, and recorded in DL-301

**Do not add a design-log entry; DL-301 holds them.** In short:

1. **D1** — the sensor runs in the dispatcher job, after the dispatch, on every fire; it never changes
   the dispatch's line or exit code; with no `LOG_ANALYTICS_WORKSPACE_ID` it does nothing and prints
   nothing.
2. **D2** — read by ingestion time; start 10 minutes before the previous successful read ended; the
   first read 24 hours; never more than a week back (and the message says so); key a digest of the
   row's fields; a failed read does not move the start.
3. **D3** — an allow list of kinds; a row the platform marks `error` always alarms; an exit with 0 is
   nothing; a preemption or a node scale-down is a report.
4. **D4** — the why is the replica's line by shape: a failed close's closing line, then an exception
   line, then the stop line; 15 minutes before to one after; masked; 160 characters.
5. **D5** — one message per fire for all untold alarms, one line per kind and exit code across apps;
   `TOLD` edges only when the message was sent; a report alone sends nothing.
6. **D6** — `ContainerEvent`, `ContainerSensorRead`, `TOLD`, declared with property lists.
7. **D7** — the brief's line from the first read on; none before.
8. **D8** — the job's system-assigned identity, Log Analytics Reader on the one workspace; no SDK; a
   deploy action `sensor`, repeated by a full `up`.
9. **D9** — every failure a `Fault` (and a failed read record); a type and a status word, never a
   body, a query or a token.
10. **D10** — the dispatcher's book v1.3; MINOR.

---

## Blast radius — measured 2026-10-14

| What | Detail |
| --- | --- |
| Files changed | **New:** nine modules `orchestration/container_*.py` (§ 1 to § 8). **Changed:** `orchestration/settings.py`, `telegram_client.py`, `daily_brief_text.py`, `daily_brief_facts.py`, `orchestration/Dockerfile`, `orchestration/packs/trading_graph_vocabulary.json`, `scripts/dispatch_scheduled_run.py`, `infra/deploy-agents.ps1`, the dispatcher's `laws.md` and `test-plan.md`, `docs/laws/INDEX.md`, `docs/laws/ledger.md`, two existing test files (§ 10), `pyproject.toml`, `uv.lock`. Sizes in *Guardrails* |
| Agents affected | none: the dispatcher job only (`orchestration/`, `scripts/`). No agent imports another; the new modules import `kernel` and `orchestration` only |
| Decision paths | none. `scripts/replay_fidelity_git.py`'s `DECISION_PATHS` names no file this sprint touches (it names `orchestration/history_window.py` and two packs, not the vocabulary) |
| Contract change? | no |
| Graph vocabulary change? | yes: `ContainerEvent`, `ContainerSensorRead`, `TOLD`. Only the dispatcher job writes them, so only the job needs the new vocabulary; the deploy step sets it |
| New env keys / tunables | `LOG_ANALYTICS_WORKSPACE_ID` on the job (a coordinate, not a secret); five `ORCHESTRATOR_CONTAINER_SENSOR_*` tunables, all defaulted, none set live |
| Deploy implication | the image retag of the 16 apps and the job (the usual `/deploy-fleet`), then `pwsh infra/deploy-agents.ps1 sensor` (identity, role, env key, the job's vocabulary). **Either order is safe:** the old image ignores the env key; the new image without it is silent |
| Rollback | retag the job back to the previous tag. A retag does not undo: the job's identity and role (harmless without the new image; `az containerapp job identity remove` and `az role assignment delete` remove them), the env key (ignored by the old image), and the graph's `ContainerEvent` and `ContainerSensorRead` records (append-only, read by nothing else) |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Plant the failing tests first** (Test plan below) and watch them fail: on the unchanged tree every
   new test file fails to import, and the edited capability test fails. Paste the red output.
3. **Apply the Appendix** (§ 1 to § 8) exactly. Change nothing else in production code.
4. **Law cycle** (§ 9): the laws.md text exactly, then your test-plan rows and the two roll-ups.
5. **The two existing test edits** (§ 10), exactly.
6. **Prove the guards can fail (DL-70):** plant the breaks under *Traps*, one at a time, each red;
   restore each.
7. **Bump the version (MINOR)** in `pyproject.toml` and run `uv lock --offline`; stage `uv.lock`.
8. **`make ci` green** — every step, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Name your tests as you like; each docstring cites its clause. The planner's own tests sit in the
evidence folder and are run beside yours at review; its break script judges by exit code alone.
Shape the platform rows as § 1's docstring and the *Measured* table give them.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 each kind | one row per measured kind (exit 1, exit 137, `OOMKilled`, `ContainerBackOff`, `KEDAScaleTargetActivationFailed`, `KEDAScalerFailed`, the provisioning `error` row, `Preempted`) | kind, app and exit code per DL-301 D3; `alarm` false only for the report (`DSP-IN-05`) |
| A2 | 🪤 nothing | an exit with code 0, `ReplicaUnhealthy`, `AssigningReplicaFailed`, `StoppingContainer` | `classify` returns `None` (`DSP-IN-05`) |
| A3 | an unknown error row alarms; an exit with no readable code | `Level` `Error` of a new text; reason `Error` with no code | `platform-error`, alarm; `exit-error` with no code (`DSP-IN-05`) |
| A4 | the app | a job row; a row with no names | the job's name; `unknown` (`DSP-IN-05`) |
| A5 | the count | `Count_d` 12.0, "3", None, 0.0, "x", infinity | 12, 3, 1, 1, 1, 1 (`DSP-OUT-07`) |
| A6 | the key | one row twice; the row with another count | same key; another key; message cut to 300 (`DSP-IDM-04`) |
| A7 | the query reads what the classifier reads | `events_query` | every `SENSED_REASONS` entry quoted in it, `Level =~ 'error'`, `ingestion_time()` (`DSP-IN-05`) |
| A8 | 🎯 the why by shape | a traceback's four lines at one stamp; a failed close, an exception and a stop line | the exception line; then the closing, the exception, the stop line in that order; a clean closing line and SDK chatter give `""` (`DSP-IN-05`) |
| A9 | the window | the same line 15 min before, 1 min after, and one second outside each | inside read, outside not (`DSP-IN-05`) |
| A10 | 🪤 masking | a URL with a password (built at run time), a bearer token, `password=`, `SharedAccessKey=`, `token:`, a 40-character run, `$101,976.32`, `25000.00` | each masked; a long line folded and cut to 160 with `…` (`DSP-SEC-03`, `DSP-SEC-02`) |
| A11 | 🎯 the reader | a stand-in opener | one GET to `IDENTITY_ENDPOINT` with `resource` and the header, then POSTs to the workspace with the bearer; the token fetched once for two queries; `timespan` starts an hour before the window (`DSP-SEC-03`) |
| A12 | 🪤 no identity, failed calls | no identity env; HTTP 403 with a body, a URL error, a time-out, a non-object reply, an empty token | `ContainerLogReadError` with status `no managed identity` (nothing sent), `403`, `transport`, `transport`, `shape`, `no token`; never the body (`DSP-SEC-03`, `DSP-FAIL-04`) |
| A13 | reply shapes; hostile names | five malformed tables; replica names with a quote, capitals, empty | `shape` each; no lines query sent; the name never in a query (`DSP-SEC-03`) |
| A14 | 🎯 the window over fires | two reads ten minutes apart | first 24 h back; second 10 min before the first's end (`DSP-TRG-04`) |
| A15 | the cap | a read nine days after the last | starts 168 h back; the message ends with the cap note; the read record `capped` (`DSP-TRG-04`, `DSP-OUT-07`) |
| A16 | 🎯 record and tell | the eight measured rows plus four ignored | 8 events, one message, 7 `TOLD` edges, the read's counts (12 rows, 8 recorded, 7 alarms, 1 report) and message id (`DSP-OUT-07`, `DSP-OBS-03`) |
| A17 | 🪤 read twice | the same row in two overlapping reads | recorded once, told once (`DSP-IDM-04`) |
| A18 | 🎯 unsent then told | a port that returns `None`, then one that raises, then one that sends | the first two tell nothing and keep the port's error word or the type; the third tells it; nothing untold left (`DSP-IDM-04`, `DSP-FAIL-04`) |
| A19 | a report alone; the row limit | one preemption; 5,000 rows | no message; `truncated` true (`DSP-OUT-07`) |
| A20 | the why reaches the message | an exit-1 alarm with lines, a scaler alarm | one lines query for the one replica, window from 15 min before the alarm; the line stored; `why (provider):` in the message; a replica-less alarm asks for no lines (`DSP-IN-05`, `DSP-OUT-07`) |
| A21 | 🎯 the words | four recorded facts of two kinds | the message exactly as the Appendix's § 7 composes it (header, newest first, Melbourne with UTC, `×`, the why's app); the limit counts the rest; five apps name four; a zone that does not exist gives UTC alone; every kind's words (`DSP-OUT-07`) |
| A22 | 🎯 the brief's line | no read; a failed latest read; a read 25 h old; a quiet day; two alarms; one alarm | `None`; the failure and its error; *has not read since*; *no alarm in 24 hours*; the count and kinds (`DSP-OUT-08`) |
| A23 | the line's place | full and RED brief with the line; one without | the line just above needs-you in both; absent without (`DSP-OUT-08`) |
| A24 | 🎯 the boundary | a reader that raises a `ContainerLogReadError("403")`, a `ValueError("token=abc")`, a missing sensor module, a refusing port, a graph that refuses every write, a close that fails | one `Fault` and one failed read each (the error type and status word only); the start unmoved; stderr lines when even the graph refuses; never a raise (`DSP-FAIL-04`, `DSP-SEC-03`) |
| A25 | the wiring | no workspace; workspace but no DSN; a graph factory that raises; a configured fire | `None` and nothing built; the DSN line; the type name; one read, the identity env passed, timeout 20, the line printed, the graph closed (`DSP-TRG-04`, `DSP-OBS-03`) |
| A26 | 🎯 the entrypoint | a weekend `--as-of` with the sensor configured; then a sensor that fails | the skip line then the sensor's line, exit 0; with a failing sensor the skip line alone on stdout, the error line on stderr, exit 0 (`DSP-TRG-04`, `DSP-IDN-05`, `DSP-FAIL-04`) |
| A27 | the vocabulary | a read and a failed read on a store guarded by the pack's vocabulary | no `VocabularyError` (`DSP-OUT-07`, `DSP-OBS-03`) |
| A28 | `send_alarm` | a stand-in sender | `sendMessage` with the chat id and the text only (`DSP-SEC-01`) |
| A29 | 🪤 no management API | the nine modules' source | no `management.azure.com`, no `PUT`/`PATCH`/`DELETE` request, one `POST` and one `GET` (`DSP-NEV-03`) |
| A30 | the deploy step | `infra/deploy-agents.ps1`'s text | the role exactly Log Analytics Reader scoped only to `$ws.id`; system-assigned, no secret, password or client id; the env key and the vocabulary; `up` calls the step after the job's deploy; the planned env list holds the key; the `sensor` action throws on failure (`DSP-SEC-03`, `DSP-TRG-04`) |

---

## Success factors

- [x] A fire with the sensor configured reads, records each kept row once, and tells each alarm in
      one message with its why; a report alone sends nothing (A16 to A21).
- [x] With no workspace id, every existing test of the entrypoint, the brief and the dispatcher passes
      unchanged, and the entrypoint prints exactly what it printed (A25, A26; the existing suite).
- [x] No failure of the sensor changes the fire's line or exit code (A24, A26).
- [x] The job reads as its system-assigned identity with one role on one workspace, and no secret
      exists for it (A11, A30).
- [x] The nine production modules and every other production change equal the Appendix byte for
      byte (the planner checks blobs).
- [x] Law cycle: v1.3, ten rows citing your tests, the two roll-ups at 42 / 46.
- [x] Every break under *Traps* planted, red, restored — stated per break.
- [x] Every touched module < 200 lines.
- [ ] `make ci` exit 0: verified failing at the offline audit; pytest reached 100.00 % at the bumped version.

---

## Traps

🪤 **An unconfigured sensor must print nothing.** `tests/test_dispatch_brief_script.py` pins the
entrypoint's stdout exactly and counts `Fault`s; it runs without `LOG_ANALYTICS_WORKSPACE_ID`.
🪤 **The capability test asserts equality, not a subset**: the Telegram operations real fires use must
equal `CAP.telegram`. Adding `send_alarm` to `CAP` with no fire that uses it turns it red; § 10 adds a
sensor read to its fires. Do not weaken the assertion.
🪤 **The vocabulary file round-trips as `json.dumps(indent=2)` and its lists are not all sorted.**
Append; do not sort (a sorted rewrite is a 233-line diff). Only `edge_types` is sorted: `TOLD` goes in
its sorted place.
🪤 **`merge_node` raises when an existing node is given a different value for a property.** The sensor
skips a key it already holds and never re-merges an event.
🪤 **`keys_without_edge` compares `created_at` as text.** Stamp it with `.isoformat()` of an aware UTC
instant, as the fleet does.
🪤 **A password-shaped URL written as a literal trips the commit hook's secrets scan.** Build the
plant at run time (an f-string placeholder); same for a bot-token literal (ruff S106).
🪤 **`×` is ruff's RUF001.** The text module exports `TIMES = chr(0x00D7)`; use it in tests.
🪤 **A `Fault` raised inside an `except` block carries the handled error in its stored traceback** (`traceback.format_exception` prints the chain). Record after the handler has ended, and test a fault's whole stored properties, not its message alone (DRIFT-115).
🪤 **`sys.modules[name] = None` raises `ModuleNotFoundError`**, a subclass of `ImportError`: the line
names the subclass.
🪤 **Weekdays:** 2026-10-14 is a Wednesday, so 22:30 UTC that day is Thursday 15 Oct 09:30 in
Melbourne. The planner got two names wrong before running.
🪤 **`ruff format` grows test files.** Two of the planner's crossed 200 after formatting; measure after.
🪤 **The skip reason** for 2026-07-04 reads `2026-07-04 is not a NYSE trading session`.
🪤 **The bump needs `uv lock --offline`** (no network in the sandbox); the version test compares the
two versions as integer groups since S274.
🪤 **LF line endings** in every file you write.

**Breaks to plant, one at a time; each must turn at least one of your tests red** (the planner's
script `break_s275.py` plants 38 like these at review):

1. drop `"OOMKilled"` from `_BY_REASON`; 2. let an exit with code 0 alarm; 3. `_KILL_CODE = 138`;
4. ignore `error` rows; 5. map `Preempted` to `START_FAILED`; 6. drop `Count_d` from `_KEY_FIELDS`;
7. reverse `_SHAPES`; 8. the window to 30 minutes; 9. stop masking URL credentials; 10. stop masking
amounts; 11. `LINE_LIMIT = 4000`; 12. accept any replica name; 13. read by `TimeGenerated`;
14. put the HTTP reason in the error; 15. fetch a token per query; 16. no overlap; 17. no cap;
18. let a failed read move the start; 19. add `TOLD` edges when the send failed; 20. let the sensor
run unconfigured; 21. re-raise in `sense_safely`; 22. keep the exception's text in the failure;
23. no `Fault` for an unsent alarm; 24. let the sensor set the exit code; 25. run the sensor before
the dispatch; 26. a quiet day returns `None`; 27. the brief's window to 48 hours; 28. oldest group
first; 29. ignore the group limit; 30. scope the role to `$RG`; 31. drop the step from `Up`; 32. drop
`error_line` from the vocabulary; 33. the brief's line after needs-you; 34. drop a module's `COPY` from
the Dockerfile; 35. record the failure inside `sense_safely`'s `except` block (the shape before DRIFT-115).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` but the two the Appendix
  carries on `Request(...)` (the repo's pattern, as in `surfaces/dashboard/azure_http.py`).
  📌 Sizes on `main` at `be0aec51` → on the prototype: `orchestration/settings.py` **84 → 134**; `orchestration/telegram_client.py` **133 → 140**; `orchestration/daily_brief_text.py` **179 → 182**; `orchestration/daily_brief_facts.py` **166 → 168**; `scripts/dispatch_scheduled_run.py` **129 → 145**; `orchestration/tests/test_dispatcher_capability.py` **142 → 150**; `orchestration/tests/scheduled_dispatch_human_helpers.py` **134 → 140**; `orchestration/container_events.py` **new, 155**; `orchestration/container_lines.py` **new, 64**; `orchestration/container_queries.py` **new, 91**; `orchestration/container_logs.py` **new, 129**; `orchestration/container_sensor_graph.py` **new, 91**; `orchestration/container_sensor.py` **new, 179**; `orchestration/container_sensor_guard.py` **new, 160**; `orchestration/container_alarm_text.py` **new, 177**; `orchestration/container_brief.py` **new, 58**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — the five tunables carry their `why`.
- Faults, not silent failure — `kernel.fault_boundary`, as `daily_brief_guard.py` does.
- `make ci` **every step** green, **100.00 % coverage floor**, redirected to a file.
- Version bump MINOR, `uv.lock` staged with it.
- Secrets never through the worktree; the worktree has **no `.env`**, and nothing here needs one.

---

## Sequencing after merge (the planner's)

1. Merge `main` in first; `git hash-object` of the production files against the prototype's blobs
   (`prototype_blobs.txt`); copy the planner's tests (`planner_tests/`) beside the builder's and run
   them; `uv run --no-sync python <evidence>/break_s275.py <the builder's test files>
   tests/test_dispatch_scheduled_run.py` from the worktree root (38 breaks, judged by exit code; a `NOT FOUND` means the build differs there);
   CodeQL set-diff against the last merged branch; `make gate-ran` from the worktree.
2. Merge to `main` and push; check `main`'s runs and its open alerts.
3. **F1 at no cost**, from a worktree of merged `main` (no `.env`): `f0_live_replay.py` at
   2026-09-25 01:00 and 2026-09-29 00:00 UTC must print the messages recorded in DL-301.
4. **Deploy, the operator's call:** `/deploy-fleet` (the image retag), then
   `pwsh infra/deploy-agents.ps1 sensor` (identity, role, env key, the job's vocabulary), each read
   back. Record the rollback tag.
5. **F2 on the fleet**, at the first weekday fire after it (22:00 UTC): the job's console holds
   `container-sensor read N rows: …` and no `error container-sensor` line; the graph holds a
   `ContainerSensorRead` with outcome `read`; that night's brief carries a `Containers:` line. If the
   day held an alarm, the operator's Telegram holds one message. *Optional, the operator's call:* a
   throwaway job that exits 1, to watch the alarm path end to end and learn what the platform logs
   for a failed job execution (DL-301, *Named*).
6. Close work-queue 119; update the weekly reminder.

---

## Handover — paste this to Codex

```text
You are building Sprint 275 in the worktree ../ta-s275, on the branch
sprint-275-the-operator-hears-when-a-container-fails. Never work on main.

Read docs/sprints/sprint-275-the-operator-hears-when-a-container-fails.md, whole, before anything
else. It is the spec, and its bottom sections are your handback. It is long: the Appendix holds the
production code, which you apply exactly; your work is the tests, the law rows, the two named test
edits, the bump and the evidence.

In order:
1. Read orchestration/laws/dispatcher/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any code.
2. Write the tests of the Test plan (A1 to A30) in new test files under orchestration/tests/ and
   tests/, each docstring citing its clause. Run them on the unchanged tree and paste the red
   output into the Closeout (every new file fails to import).
3. Apply the Appendix sections 1 to 8 exactly: nine new modules under orchestration/, and the
   changes to orchestration/settings.py, telegram_client.py, daily_brief_text.py,
   daily_brief_facts.py, orchestration/Dockerfile, orchestration/packs/trading_graph_vocabulary.json,
   scripts/dispatch_scheduled_run.py and infra/deploy-agents.ps1. Change nothing else in
   production code.
4. Apply section 9 to orchestration/laws/dispatcher/laws.md exactly. Then add a test-plan row per
   new clause citing your tests, set the test plan's header to v1.3, widen DSP-IDN-03's and
   DSP-DEP-01's descriptions as section 9 widens the clauses, add your send_alarm test to
   DSP-SEC-01's row, and set the dispatcher's row in docs/laws/INDEX.md and docs/laws/ledger.md to
   v1.3 and the count the law gate derives (42 / 46 on the prototype).
5. Apply section 10 to the two existing test files, exactly. Change no other existing test.
6. Plant the breaks listed under Traps one at a time; each must turn at least one of your tests
   red; restore each before the next.
7. Bump the version (MINOR) in pyproject.toml, run uv lock --offline, stage uv.lock. Run make ci
   redirected to a file and read the file.
8. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md or docs/design-log.md.

DO NOT: run infra/deploy-agents.ps1 or any az command; reach the network; change contracts/,
kernel/, agents/, surfaces/ or any decision-path file; add or reword a law clause beyond section 9;
change any existing test but the two section 10 names; sort the vocabulary's lists; use noqa beyond
the two the Appendix carries; let any module reach 200 lines; measure make ci through a pipe.

Traps (the spec's Traps section has them all): an unconfigured sensor prints nothing, because an
existing test pins the entrypoint's stdout; the capability test asserts equality of Telegram
operations, and section 10 is how it stays green; never re-merge an existing event; build any
password-shaped URL or token plant at run time; use TIMES, not a literal multiplication sign;
2026-10-15 is a Thursday; ruff format grows test files, so measure sizes after formatting.

If a law contradicts the spec, or any other existing test fails, STOP and report. State anything
not done as "not done" or "verified failing". Never write a Result for work you have not done.
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
| Nine `container_*.py` modules | Dispatcher `laws.md` and `test-plan.md` whole (v1.2), conventions and drift register read on the first pass; corrected v1.3 Appendix § 9 re-read against § 1–8 on resuming at `a6864f86` | Proposed `DSP-IDN-05`, `DSP-IN-05`, `DSP-TRG-04`, `DSP-OUT-07/08`, `DSP-NEV-03`, `DSP-IDM-04`, `DSP-FAIL-04`, `DSP-SEC-03`, `DSP-OBS-03`; existing `DSP-SEC-01/02` | Yes: the planner corrected DRIFT-114. Read-back confirms the five corrected clauses agree with the code; resume tests first, with no production edits yet. |
| Scheduled entrypoint | Same dispatcher book and test plan; conventions; `CLAUDE.md` whole | `DSP-TRG-02`, `DSP-OUT-02`; proposed `DSP-TRG-04`, `DSP-IDN-05`, `DSP-FAIL-04` | Tests will pin dispatch-before-sensor ordering and the dispatch's own status and stdout, including an unconfigured fire. |
| Daily brief text and facts | Same dispatcher book and test plan; conventions | `DSP-IDN-04`, `DSP-TRG-03`, `DSP-OUT-06`, `DSP-SEC-02`; proposed `DSP-OUT-08` | Pin the 24-hour recording window, repeats counted by incident peaks, and the new line before needs-you in full and RED briefs. |
| Telegram port and the two existing test edits | Same dispatcher book and test plan, including `CAP`; conventions | `DSP-SEC-01/02`; proposed `DSP-IDM-04`, `DSP-FAIL-04`, `CAP.telegram.send_alarm` | Keep capability equality intact through the exact § 10 edits; use an injected sender and prove unsent alarms remain pending. |
| Settings | Same dispatcher book and test plan, including `PARAM`; corrected § 8 diff | Five proposed `container_sensor_*` PARAM rows | The corrected alarm-groups rationale says kinds of failure. Apply the exact defaults, bounds and rationales. |
| Graph vocabulary | `kernel/graph_vocabulary.py` module docstring; ADR-0012 whole; dispatcher book and test plan | ADR-0012 substrate/pack wall; proposed `DSP-OUT-07`, `DSP-OBS-03` | Test successful and failed reads through the guarded store; append lists exactly as the Appendix directs. |
| Dockerfile | Sprint Appendix § 8; dispatcher book and test plan | Proposed `DSP-FAIL-04` | Pin all nine module copies in a new test; apply the exact file list. |
| Deploy script | `CLAUDE.md` whole; dispatcher book and test plan; conventions | Proposed `DSP-SEC-03`, `DSP-TRG-04` | Prove the identity, workspace-only role, planned env, vocabulary and Up ordering from source only. No deploy or Azure command is authorized. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes: a new dispatcher sensor guarantee, with no contracts change. The full cycle is owed: apply § 9 exactly, cite the new tests in ten rows, synchronize PARAM and CAP and derive both rollups from the law gate.

**Contradictions found between a law and this spec:** None remaining. DRIFT-114 and DRIFT-115 are corrected by the planner (DL-301 amendments 1 and 2). The corrected guard has blob 448b940223f8fb1d8a07c2ad74ffdecf23662221. A24 passes with an intact traceback and no original planted text; trap 35 restores the old handler shape and makes that assertion fail again. The clause remains unchanged.

**Laws found silent where a decision was needed:** The current v1.2 book does not declare the sensor; the corrected § 9 supplies that guarantee. No additional undecided silence found on resuming.

**Clauses that were ⬜ and are now proven:** The ten new v1.3 clauses are proven by the passing 123-case A1–A30 suite; their cited rows are 🟩 and the law gate derives 42 / 46. DSP-IDN-03, DSP-NEV-02, DSP-TYP-01 and DSP-DEP-01 remain ⬜. Both earlier drifts are corrected by the planner; A24 passes after amendment 2.

**Planner, after the stop (2026-10-14 18:00 AEDT):** DRIFT-114 is corrected in § 9 and § 8 (the note under the title; DL-301 amendment 1). The record above is the first build's, kept as written. On resuming, re-read § 9's five corrected clauses (`DSP-IN-05`, `DSP-OUT-07`, `DSP-OUT-08`, `DSP-IDM-04`, `DSP-FAIL-04`) against § 1 to § 8, then restate each paragraph above for the build you hand back.

**Planner, after the second stop (2026-10-14 19:27 AEDT):** DRIFT-115 is corrected in § 6 (the second note under the title; DL-301 amendment 2). No clause changed. Re-apply § 6's `orchestration/container_sensor_guard.py` exactly and check its blob against the Appendix, run A24 again, then go on from where the build stopped and fill every handback section for the build you hand back.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_measured_kinds` | `orchestration/tests/test_container_events.py` | PASS (full suite) | DSP-IN-05 |
| A2 | `test_a2_noise_and_clean_exit_are_nothing` | `orchestration/tests/test_container_events.py` | PASS (full suite) | DSP-IN-05 |
| A3 | `test_a3_unknown_error_and_unreadable_exit` | `orchestration/tests/test_container_events.py` | PASS (full suite) | DSP-IN-05 |
| A4 | `test_a4_app_precedence_and_unknown` | `orchestration/tests/test_container_events.py` | PASS (full suite) | DSP-IN-05 |
| A5 | `test_a5_repeat_count` | `orchestration/tests/test_container_events.py` | PASS (full suite) | DSP-OUT-07 |
| A6 | `test_a6_key_is_the_row_and_message_is_bounded` | `orchestration/tests/test_container_events.py` | PASS (full suite) | DSP-IDM-04 |
| A7 | `test_a7_query_matches_classifier_and_ingestion_window` | `orchestration/tests/test_container_events.py` | PASS (full suite) | DSP-IN-05 |
| A8 | `test_a8_traceback_order_and_shape_precedence` | `orchestration/tests/test_container_lines.py` | PASS (full suite) | DSP-IN-05 |
| A9 | `test_a9_console_window` | `orchestration/tests/test_container_lines.py` | PASS (full suite) | DSP-IN-05 |
| A10 | `test_a10_credentials_and_amounts_are_masked` | `orchestration/tests/test_container_lines.py` | PASS (full suite) | DSP-SEC-03, DSP-SEC-02 |
| A11 | `test_a11_one_identity_get_then_workspace_posts` | `orchestration/tests/test_container_reader.py` | PASS (full suite) | DSP-SEC-03 |
| A12 | `test_a12_missing_identity_sends_nothing`; `test_a12_transport_and_identity_reply_failures`; `test_a12_http_status_never_includes_reason_or_body`; `test_a12_invalid_json_is_transport` | `orchestration/tests/test_container_reader.py` | PASS (full suite) | DSP-SEC-03, DSP-FAIL-04 |
| A13 | `test_a13_bad_table_is_a_shape_failure`; `test_a13_hostile_replica_is_never_sent`; `test_a13_first_table_is_read_by_column_name` | `orchestration/tests/test_container_queries.py` | PASS (full suite) | DSP-SEC-03 |
| A14 | `test_a14_first_read_then_overlapping_fire` | `orchestration/tests/test_container_sensor.py` | PASS (full suite) | DSP-TRG-04 |
| A15 | `test_a15_long_gap_caps_window_and_message` | `orchestration/tests/test_container_sensor.py` | PASS (full suite) | DSP-TRG-04, DSP-OUT-07 |
| A16 | `test_a16_records_every_kept_row_and_tells_seven_alarms` | `orchestration/tests/test_container_sensor.py` | PASS (full suite) | DSP-OUT-07, DSP-OBS-03 |
| A17 | `test_a17_same_row_in_two_reads_is_never_remerged` | `orchestration/tests/test_container_sensor.py` | PASS (full suite) | DSP-IDM-04 |
| A18 | `test_a18_unsent_then_raised_then_sent` | `orchestration/tests/test_container_telling.py` | PASS (full suite) | DSP-IDM-04, DSP-FAIL-04 |
| A19 | `test_a19_report_only_and_row_limit` | `orchestration/tests/test_container_sensor.py` | PASS (full suite) | DSP-OUT-07 |
| A20 | `test_a20_replica_line_reaches_graph_and_message` | `orchestration/tests/test_container_telling.py` | PASS (full suite) | DSP-IN-05, DSP-OUT-07 |
| A21 | `test_a21_message_exactly_groups_kinds_across_apps`; `test_a21_five_apps_name_four_and_count_the_rest`; `test_a21_every_kind_has_its_words` | `orchestration/tests/test_container_alarm_text.py`; `orchestration/tests/test_container_alarm_words.py` | PASS (full suite) | DSP-OUT-07 |
| A22 | `test_a22_first_failed_stale_and_quiet_read`; `test_a22_recording_window_counts_repeat_peaks` | `orchestration/tests/test_container_brief.py` | PASS (full suite) | DSP-OUT-08 |
| A23 | `test_a23_container_line_is_just_before_needs_you`; `test_a23_real_brief_facts_include_the_sensor_line` | `orchestration/tests/test_container_brief.py` | PASS (full suite) | DSP-OUT-08 |
| A24 | `test_a24_read_failure_is_one_fault_and_failed_read`; `test_a24_missing_sensor_module_is_contained`; `test_a24_refusing_port_records_one_fault_and_no_told_edge`; `test_a24_graph_refusing_all_writes_still_never_raises`; `test_a24_failure_status_is_used_only_when_text` | `orchestration/tests/test_container_faults.py` | PASS (full suite) | DSP-FAIL-04, DSP-SEC-03 |
| A25 | `test_a25_unconfigured_sensor_builds_nothing`; `test_a25_configured_without_dsn_is_a_safe_line`; `test_a25_graph_factory_failure_exposes_only_type`; `test_a25_configured_reader_and_a24_close` | `orchestration/tests/test_container_env.py` | PASS (full suite) | DSP-TRG-04, DSP-OBS-03 |
| A26 | `test_a26_weekend_skip_then_sensor_or_safe_failure` | `tests/test_container_sensor_script.py` | PASS (full suite) | DSP-TRG-04, DSP-IDN-05, DSP-FAIL-04 |
| A27 | `test_a27_pack_accepts_events_reads_edges_and_failures` | `orchestration/tests/test_container_vocabulary.py` | PASS (full suite) | DSP-OUT-07, DSP-OBS-03 |
| A28 | `test_a28_send_alarm_posts_only_chat_and_plain_text` | `orchestration/tests/test_container_vocabulary.py` | PASS (full suite) | DSP-SEC-01 |
| A29 | `test_a29_sensor_has_only_log_reads_and_identity_get` | `orchestration/tests/test_container_vocabulary.py` | PASS (full suite) | DSP-NEV-03 |
| A30 | `test_a30_sensor_identity_role_and_workspace_are_exact`; `test_a30_up_env_preservation_and_sensor_action` | `tests/test_container_sensor_deploy.py` | PASS (full suite) | DSP-SEC-03, DSP-TRG-04 |

**Tests added beyond the plan:** 10 additional edge/source tests, all run in the focused suite: `orchestration/tests/test_container_alarm_words.py::test_text_reads_malformed_facts_conservatively`; `orchestration/tests/test_container_alarm_words.py::test_brief_names_three_kinds_and_counts_the_rest`; `orchestration/tests/test_container_env.py::test_pre_graph_construction_failures_are_safe`; `orchestration/tests/test_container_env.py::test_graph_without_close_is_supported`; `orchestration/tests/test_container_sensor.py::test_recording_age_controls_pending_alarms`; `orchestration/tests/test_container_telling.py::test_refused_port_error_is_a_safe_word`; `orchestration/tests/test_container_telling.py::test_unexplained_alarm_queries_no_lines`; `orchestration/tests/test_container_vocabulary.py::test_image_copies_all_sensor_modules`; `tests/test_container_sensor_script.py::test_every_outcome_keeps_dispatch_order_and_status`; `tests/test_container_sensor_script.py::test_unconfigured_weekend_stdout_is_unchanged`. These cover conservative facts, extra failure shapes, recording age, image copies and all dispatch outcomes. No existing test outside § 10 was changed.

---

## Closeout — evidence

**Status:** MERGED — the build proof is the builder's, below; the full `make ci`, the remote gate, the breaks and F1 are in the planner's review at the merge. *The builder's line read:* BUILT — unit, regression, guard and coverage proofs pass; full CI is verified failing at the offline dependency audit.

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s275`, branch `sprint-275-the-operator-hears-when-a-container-fails`, starting HEAD `a6864f86c6055c38f826fa2c486a86132f4d8128`; no `.env`. The planner's uncommitted corrections were preserved. Tests used synthetic readers, ports and graph factories; the full CI process denied external DNS/connect attempts with a temporary hook outside the worktree.

**Result:** Built as the corrected Appendix: all 20 file blobs match, including guard `448b940223f8fb1d8a07c2ad74ffdecf23662221`. A1–A30 pass (123 cases), regression 567 passed, all 35 breaks red/restored, and the full pytest run passed 4,961 with 9 skipped at 100.00% statement/branch coverage. MINOR `0.126.00`, `uv lock --offline` and staged `uv.lock` are done. `make ci` exited 2 at step 14; the dependency audit is NOT RUN offline. Steps 15/16 passed separately. No full green CI claim.

**Files changed:** The 20 exact Appendix files; 14 new test files and two helpers; dispatcher test plan; both law rollups; this sprint spec and README; pyproject.toml and uv.lock; plus the planner's preserved design-log and drift-register corrections. No other existing test, contracts, kernel, agents, surfaces, decision-path or STATE file changed.

**Design decisions:** recorded as [DL-301](../design-log.md), amendments 1 and 2, by the planner; the builder made no design-log edit.

**Proof — the red run first:**

Command: `uv run --offline --no-sync pytest --no-cov` with the 14 new test files.
Existing production and existing tests were unchanged; only the law-reading record preceded this run.

```text
============================= test session starts =============================
collected 0 items / 14 errors

=================================== ERRORS ====================================
______ ERROR collecting orchestration/tests/test_container_alarm_text.py ______
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_alarm_text.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_alarm_text.py:12: in <module>
    from orchestration.container_alarm_text import TIMES, alarm_message, group_events
E   ModuleNotFoundError: No module named 'orchestration.container_alarm_text'
_____ ERROR collecting orchestration/tests/test_container_alarm_words.py ______
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_alarm_words.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_alarm_words.py:14: in <module>
    from orchestration.container_alarm_text import (
E   ModuleNotFoundError: No module named 'orchestration.container_alarm_text'
________ ERROR collecting orchestration/tests/test_container_brief.py _________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_brief.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_brief.py:15: in <module>
    from orchestration.container_brief import container_line
E   ModuleNotFoundError: No module named 'orchestration.container_brief'
_________ ERROR collecting orchestration/tests/test_container_env.py __________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_env.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_env.py:13: in <module>
    from orchestration import container_logs, container_sensor_guard
E   ImportError: cannot import name 'container_logs' from 'orchestration' (C:\Users\yury_\Downloads\project\ta-s275\orchestration\__init__.py)
________ ERROR collecting orchestration/tests/test_container_events.py ________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_events.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_events.py:14: in <module>
    from orchestration.container_events import SENSED_REASONS, classify, event_key
E   ModuleNotFoundError: No module named 'orchestration.container_events'
________ ERROR collecting orchestration/tests/test_container_faults.py ________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_faults.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_faults.py:16: in <module>
    from orchestration.container_queries import ContainerLogReadError
E   ModuleNotFoundError: No module named 'orchestration.container_queries'
________ ERROR collecting orchestration/tests/test_container_lines.py _________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_lines.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_lines.py:14: in <module>
    from orchestration.container_lines import choose_line, safe_line
E   ModuleNotFoundError: No module named 'orchestration.container_lines'
_______ ERROR collecting orchestration/tests/test_container_queries.py ________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_queries.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_queries.py:14: in <module>
    from orchestration.container_queries import (
E   ModuleNotFoundError: No module named 'orchestration.container_queries'
________ ERROR collecting orchestration/tests/test_container_reader.py ________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_reader.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_reader.py:19: in <module>
    from orchestration.container_queries import ContainerLogReadError
E   ModuleNotFoundError: No module named 'orchestration.container_queries'
________ ERROR collecting orchestration/tests/test_container_sensor.py ________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_sensor.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_sensor.py:13: in <module>
    from orchestration.container_events import classify
E   ModuleNotFoundError: No module named 'orchestration.container_events'
_______ ERROR collecting orchestration/tests/test_container_telling.py ________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_telling.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_telling.py:15: in <module>
    from orchestration.container_sensor import sense_containers
E   ModuleNotFoundError: No module named 'orchestration.container_sensor'
______ ERROR collecting orchestration/tests/test_container_vocabulary.py ______
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\orchestration\tests\test_container_vocabulary.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_container_vocabulary.py:17: in <module>
    from orchestration.container_queries import ContainerLogReadError
E   ModuleNotFoundError: No module named 'orchestration.container_queries'
___________ ERROR collecting tests/test_container_sensor_deploy.py ____________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\tests\test_container_sensor_deploy.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_container_sensor_deploy.py:13: in <module>
    from orchestration.container_sensor_guard import WORKSPACE_ENV
E   ModuleNotFoundError: No module named 'orchestration.container_sensor_guard'
___________ ERROR collecting tests/test_container_sensor_script.py ____________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s275\tests\test_container_sensor_script.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_container_sensor_script.py:16: in <module>
    from orchestration import container_logs
E   ImportError: cannot import name 'container_logs' from 'orchestration' (C:\Users\yury_\Downloads\project\ta-s275\orchestration\__init__.py)
=========================== short test summary info ===========================
ERROR orchestration/tests/test_container_alarm_text.py
ERROR orchestration/tests/test_container_alarm_words.py
ERROR orchestration/tests/test_container_brief.py
ERROR orchestration/tests/test_container_env.py
ERROR orchestration/tests/test_container_events.py
ERROR orchestration/tests/test_container_faults.py
ERROR orchestration/tests/test_container_lines.py
ERROR orchestration/tests/test_container_queries.py
ERROR orchestration/tests/test_container_reader.py
ERROR orchestration/tests/test_container_sensor.py
ERROR orchestration/tests/test_container_telling.py
ERROR orchestration/tests/test_container_vocabulary.py
ERROR tests/test_container_sensor_deploy.py
ERROR tests/test_container_sensor_script.py
!!!!!!!!!!!!!!!!!! Interrupted: 14 errors during collection !!!!!!!!!!!!!!!!!!!
============================= 14 errors in 2.64s ==============================
RED_EXIT=2
NEW_TEST_FILES=14
```

**Proof — the green run:**

```text
============================= test session starts =============================
collected 123 items

orchestration\tests\test_container_alarm_text.py ..                      [  1%]
orchestration\tests\test_container_alarm_words.py ...............        [ 13%]
orchestration\tests\test_container_brief.py .....                        [ 17%]
orchestration\tests\test_container_env.py ........                       [ 24%]
orchestration\tests\test_container_events.py .........................   [ 44%]
orchestration\tests\test_container_faults.py ......                      [ 49%]
orchestration\tests\test_container_lines.py ......                       [ 54%]
orchestration\tests\test_container_queries.py ...............            [ 66%]
orchestration\tests\test_container_reader.py ...............             [ 78%]
orchestration\tests\test_container_sensor.py ......                      [ 83%]
orchestration\tests\test_container_telling.py .......                    [ 89%]
orchestration\tests\test_container_vocabulary.py ....                    [ 92%]
tests\test_container_sensor_deploy.py ..                                 [ 94%]
tests\test_container_sensor_script.py .......                            [100%]

============================= 123 passed in 2.76s =============================
FOCUSED_EXIT=0
============================= test session starts =============================
collected 2 items

orchestration\tests\test_container_faults.py ..                          [100%]

============================== 2 passed in 1.17s ==============================
A24_EXIT=0
============================ 567 passed in 15.49s =============================
REGRESSION_EXIT=0
========= 4961 passed, 9 skipped, 2470 warnings in 398.19s (0:06:38) ==========
TOTAL                                                           20978      0   4454      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
```

**Guards planted:** All 35, one at a time, each failing a builder test and restored before the next. Repeated after the final test typing corrections; 35 / 35 again.

```text
BREAK 01: RED exit=1; orchestration/tests/test_container_events.py::test_a1_measured_kinds[memory-kill-memory-kill-analyst-None-True]; restored
BREAK 02: RED exit=1; orchestration/tests/test_container_events.py::test_a2_noise_and_clean_exit_are_nothing[platform_row3]; restored
BREAK 03: RED exit=1; orchestration/tests/test_container_events.py::test_a1_measured_kinds[killed-killed-master-137-True]; restored
BREAK 04: RED exit=1; orchestration/tests/test_container_events.py::test_a3_unknown_error_and_unreadable_exit[platform_row0-platform-error]; restored
BREAK 05: RED exit=1; orchestration/tests/test_container_events.py::test_a1_measured_kinds[preempted-preempted-reporter-None-False]; restored
BREAK 06: RED exit=1; orchestration/tests/test_container_events.py::test_a6_key_is_the_row_and_message_is_bounded; restored
BREAK 07: RED exit=1; orchestration/tests/test_container_lines.py::test_a8_traceback_order_and_shape_precedence; restored
BREAK 08: RED exit=1; orchestration/tests/test_container_lines.py::test_a9_console_window[-901-False]; restored
BREAK 09: RED exit=1; orchestration/tests/test_container_lines.py::test_a10_credentials_and_amounts_are_masked; restored
BREAK 10: RED exit=1; orchestration/tests/test_container_lines.py::test_a10_credentials_and_amounts_are_masked; restored
BREAK 11: RED exit=1; orchestration/tests/test_container_lines.py::test_a10_credentials_and_amounts_are_masked; restored
BREAK 12: RED exit=1; orchestration/tests/test_container_queries.py::test_a13_hostile_replica_is_never_sent[replica' | take 1]; restored
BREAK 13: RED exit=1; orchestration/tests/test_container_events.py::test_a7_query_matches_classifier_and_ingestion_window; restored
BREAK 14: RED exit=1; orchestration/tests/test_container_reader.py::test_a12_http_status_never_includes_reason_or_body[True]; restored
BREAK 15: RED exit=1; orchestration/tests/test_container_reader.py::test_a11_one_identity_get_then_workspace_posts; restored
BREAK 16: RED exit=1; orchestration/tests/test_container_sensor.py::test_a14_first_read_then_overlapping_fire; restored
BREAK 17: RED exit=1; orchestration/tests/test_container_sensor.py::test_a15_long_gap_caps_window_and_message; restored
BREAK 18: RED exit=1; orchestration/tests/test_container_faults.py::test_a24_read_failure_is_one_fault_and_failed_read[failure0-ContainerLogReadError (403)]; restored
BREAK 19: RED exit=1; orchestration/tests/test_container_telling.py::test_a18_unsent_then_raised_then_sent; restored
BREAK 20: RED exit=1; orchestration/tests/test_container_env.py::test_a25_unconfigured_sensor_builds_nothing; restored
BREAK 21: RED exit=1; orchestration/tests/test_container_faults.py::test_a24_read_failure_is_one_fault_and_failed_read[failure0-ContainerLogReadError (403)]; restored
BREAK 22: RED exit=1; orchestration/tests/test_container_faults.py::test_a24_read_failure_is_one_fault_and_failed_read[failure0-ContainerLogReadError (403)]; restored
BREAK 23: RED exit=1; orchestration/tests/test_container_faults.py::test_a24_refusing_port_records_one_fault_and_no_told_edge; restored
BREAK 24: RED exit=1; tests/test_container_sensor_script.py::test_every_outcome_keeps_dispatch_order_and_status[placed-0]; restored
BREAK 25: RED exit=1; tests/test_container_sensor_script.py::test_every_outcome_keeps_dispatch_order_and_status[placed-0]; restored
BREAK 26: RED exit=1; orchestration/tests/test_container_brief.py::test_a22_first_failed_stale_and_quiet_read; restored
BREAK 27: RED exit=1; orchestration/tests/test_container_brief.py::test_a22_recording_window_counts_repeat_peaks; restored
BREAK 28: RED exit=1; orchestration/tests/test_container_alarm_text.py::test_a21_message_exactly_groups_kinds_across_apps; restored
BREAK 29: RED exit=1; orchestration/tests/test_container_alarm_text.py::test_a21_message_exactly_groups_kinds_across_apps; restored
BREAK 30: RED exit=1; tests/test_container_sensor_deploy.py::test_a30_sensor_identity_role_and_workspace_are_exact; restored
BREAK 31: RED exit=1; tests/test_container_sensor_deploy.py::test_a30_up_env_preservation_and_sensor_action; restored
BREAK 32: RED exit=1; orchestration/tests/test_container_vocabulary.py::test_a27_pack_accepts_events_reads_edges_and_failures; restored
BREAK 33: RED exit=1; orchestration/tests/test_container_brief.py::test_a23_container_line_is_just_before_needs_you[PASS]; restored
BREAK 34: RED exit=1; orchestration/tests/test_container_vocabulary.py::test_image_copies_all_sensor_modules; restored
BREAK 35: RED exit=1; orchestration/tests/test_container_faults.py::test_a24_read_failure_is_one_fault_and_failed_read[failure1-ValueError]; restored
GUARDS_PROVEN=35/35
ALL_MUTATED_FILES_RESTORED=True
FINAL_GUARDS_EXIT=0
```

**Module line counts:** After final formatting, all 32 touched Python modules are below 200; maximum 198.

```text
177 orchestration/container_alarm_text.py
 58 orchestration/container_brief.py
155 orchestration/container_events.py
 64 orchestration/container_lines.py
129 orchestration/container_logs.py
 91 orchestration/container_queries.py
179 orchestration/container_sensor.py
 91 orchestration/container_sensor_graph.py
160 orchestration/container_sensor_guard.py
168 orchestration/daily_brief_facts.py
182 orchestration/daily_brief_text.py
134 orchestration/settings.py
140 orchestration/telegram_client.py
 53 orchestration/tests/container_reader_helpers.py
128 orchestration/tests/container_sensor_helpers.py
140 orchestration/tests/scheduled_dispatch_human_helpers.py
 78 orchestration/tests/test_container_alarm_text.py
 76 orchestration/tests/test_container_alarm_words.py
124 orchestration/tests/test_container_brief.py
172 orchestration/tests/test_container_env.py
121 orchestration/tests/test_container_events.py
158 orchestration/tests/test_container_faults.py
 83 orchestration/tests/test_container_lines.py
 71 orchestration/tests/test_container_queries.py
157 orchestration/tests/test_container_reader.py
198 orchestration/tests/test_container_sensor.py
119 orchestration/tests/test_container_telling.py
117 orchestration/tests/test_container_vocabulary.py
150 orchestration/tests/test_dispatcher_capability.py
145 scripts/dispatch_scheduled_run.py
 70 tests/test_container_sensor_deploy.py
100 tests/test_container_sensor_script.py
ALL_TOUCHED_PYTHON_MODULES_UNDER_200=True
```

**`make ci`:** `C:/Users/yury_/AppData/Local/Temp/s275-build-20261014/make-ci-final.txt`, redirected directly to the file with `make ci > <file> 2>&1`; real exit 2. Read the whole file. Steps 1–13 passed: ruff, format, mypy, import-linter, size/header, law coverage, PARAM, sprint/tracker/docs/version, and pytest. Step 14's fresh dependency audit is NOT RUN offline: 175 of 179 cache entries existed but none was fresh, and the required refresh was blocked before external DNS. The checker was unchanged. The overall gate is verified failing. Steps 15/16 were run separately under the same network block and passed; the secrets baseline is unchanged.

```text
Success: no issues found in 1228 source files
========= 4961 passed, 9 skipped, 2470 warnings in 398.19s (0:06:38) ==========
TOTAL                                                           20978      0   4454      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
uv run python scripts/check_dependency_audit.py
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: Sprint 275 forbids external network access"))
make: *** [Makefile:60: ci] Error 1
MAKE_CI_EXIT=2
DEPENDENCY_AUDIT=NOT RUN offline
Detect secrets...........................................................Passed
TRACKED_SECRETS_EXIT=0
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 25 new file(s)
UNTRACKED_SECRETS_EXIT=0
```

**`make gate-ran`:** not done — no network/push authorized; owed to the planner for the final branch HEAD before merge.

**Not met / verified failing:** Full `make ci` green: verified failing (exit 2) because the dependency audit is NOT RUN offline. The source/test/coverage proofs above are done. Push, remote gates, merge, deployment, rollback readback and F1/F2: not done, outside this offline build. Managed identity behavior and role propagation on the live job remain unproven until F2.

---

## Return notes

- Both earlier stops were resolved by the planner. A24 checks every stored Fault property and retains an intact traceback; trap 35 restores the leaking handler shape and fails it. DSP-SEC-03 stands unchanged.
- A21/A22 use the existing time renderer exactly. New test helper annotations were corrected after the first CI attempt's mypy errors; no extra production or existing-test change was made.
- All 20 Appendix files match, guard blob `448b940223f8fb1d8a07c2ad74ffdecf23662221`. All 35 specified breaks fail a builder test and restore exactly. Every touched Python module stays below 200 lines after formatting (maximum 198).
- Dispatcher law book/test-plan header v1.3; ten new cited clauses proven; both law gate-derived rollups 42 / 46. DSP-IDN-03, DSP-NEV-02, DSP-TYP-01 and DSP-DEP-01 remain gray.
- Version `0.126.00`, normalized lock version `0.126.0`; `uv lock --offline` passed and uv.lock is staged. The planner's design-log/drift-register bytes were preserved.
- Full CI is verified failing at the network-dependent audit: NOT RUN offline, with no fresh cache entry. All tests and coverage passed and both secrets steps passed separately. The planner owes the audit and full remote gate for the final commit; do not merge on this local handback alone.
- No live graph, broker, Azure, deploy, push or merge operation was performed. The job identity endpoint, role propagation and first fleet read/message are F2; F1/F2 and rollback verification are not done.

---

## Appendix — the change, measured on the planner's prototype

Each section below is the prototype's file or its diff against `main` at `be0aec51`, generated from
the prototype's tree, not retyped. A new module is given whole; a changed file as a unified diff.
Apply them exactly.

### 1. The classification — `orchestration/container_events.py` (new)

`orchestration/container_events.py` — new, 155 lines:

```python
"""The platform's container events, read as alarms, reports, or nothing.

Agent: orchestration
Role: classify Azure Container Apps system-log rows for the container sensor (DL-301).
External I/O: none.

A row is one record of the workspace's `ContainerAppSystemLogs_CL`. The kinds are an
allow list measured on its 30 days (2026-10-14): a reason not named here is ignored,
except that a row the platform itself marks `error` is always an alarm.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

START_FAILED = "start-failed"
PROVISION_FAILED = "provision-failed"
SCALER_FAILED = "scaler-failed"
MEMORY_KILL = "memory-kill"
KILLED = "killed"
EXIT_ERROR = "exit-error"
PLATFORM_ERROR = "platform-error"
PREEMPTED = "preempted"

ALARM_KINDS = frozenset(
    {
        START_FAILED,
        PROVISION_FAILED,
        SCALER_FAILED,
        MEMORY_KILL,
        KILLED,
        EXIT_ERROR,
        PLATFORM_ERROR,
    }
)

EXIT_REASON = "Error"  # the platform's reason for every exit; the code says which
_BY_REASON = {
    "ContainerBackOff": START_FAILED,
    "KEDAScaleTargetActivationFailed": START_FAILED,
    "KEDAScalerFailed": SCALER_FAILED,
    "OOMKilled": MEMORY_KILL,
    "Preempted": PREEMPTED,
    "ScaleDown": PREEMPTED,
}
SENSED_REASONS = (*_BY_REASON, EXIT_REASON)  # the query's filter is built from this
_KEY_FIELDS = (
    "TimeGenerated",
    "time_t",
    "ContainerAppName_s",
    "JobName_s",
    "RevisionName_s",
    "ReplicaName_s",
    "Reason_s",
    "Level",
    "Log_s",
    "Count_d",
)
_EXIT_CODE = re.compile(r"exit code '(-?\d+)'")
_REVISION_SUFFIX = re.compile(r"--[a-z0-9]+$")
_PROVISIONING = "Error provisioning revision"
_KILL_CODE = 137
MESSAGE_LIMIT = 300


@dataclass(frozen=True)
class ContainerEvent:
    """One platform row the sensor keeps: which app, what happened, and when."""

    key: str
    app: str
    revision: str
    replica: str
    kind: str
    reason: str
    exit_code: int | None
    message: str
    times: int
    occurred_at: str

    @property
    def alarm(self) -> bool:
        """Whether the operator is told of this event."""
        return self.kind in ALARM_KINDS


def classify(row: Mapping[str, object]) -> ContainerEvent | None:
    """Return the row as an event the sensor keeps, or None for one it ignores."""
    reason = _text(row, "Reason_s")
    message = _text(row, "Log_s")
    code = _exit_code(message)
    kind = _kind(reason, _text(row, "Level"), message, code)
    if kind is None:
        return None
    revision = _text(row, "RevisionName_s")
    app = (
        _text(row, "ContainerAppName_s")
        or _text(row, "JobName_s")
        or _REVISION_SUFFIX.sub("", revision)
    )
    return ContainerEvent(
        key=event_key(row),
        app=app or "unknown",
        revision=revision,
        replica=_text(row, "ReplicaName_s"),
        kind=kind,
        reason=reason,
        exit_code=code,
        message=message[:MESSAGE_LIMIT],
        times=_times(row.get("Count_d")),
        occurred_at=_text(row, "time_t") or _text(row, "TimeGenerated"),
    )


def event_key(row: Mapping[str, object]) -> str:
    """Name one platform row, so a row read twice is recorded once."""
    joined = "\x1f".join(_text(row, name) for name in _KEY_FIELDS)
    return f"container-event:{hashlib.sha256(joined.encode()).hexdigest()[:32]}"


def _kind(reason: str, level: str, message: str, code: int | None) -> str | None:
    if reason == EXIT_REASON:
        if code == 0:
            return None
        return KILLED if code == _KILL_CODE else EXIT_ERROR
    if reason in _BY_REASON:
        return _BY_REASON[reason]
    if level.lower() == "error":
        return PROVISION_FAILED if message.startswith(_PROVISIONING) else PLATFORM_ERROR
    return None


def _exit_code(message: str) -> int | None:
    found = _EXIT_CODE.search(message)
    return int(found.group(1)) if found else None


def _times(value: object) -> int:
    # The platform folds repeats of one event into a count; it is absent on some rows.
    try:
        count = int(float(str(value)))
    except (ValueError, OverflowError):
        return 1
    return max(count, 1)


def _text(row: Mapping[str, object], name: str) -> str:
    value = row.get(name)
    return "" if value is None else str(value)
```

### 2. The why — `orchestration/container_lines.py` (new)

`orchestration/container_lines.py` — new, 64 lines:

```python
"""The why of a container alarm: one line of the replica's own console, made safe.

Agent: orchestration
Role: choose the console line that explains an alarm, and strip what must not leave.
External I/O: none.

Lines of one traceback share a timestamp, so "the last line" is not the error: the
line is chosen by its shape. A container's closing line naming a failed close comes
first, then an exception line, then the line saying it was told to stop (DL-297).
"""

from __future__ import annotations

import re
from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

LINE_WINDOW = timedelta(minutes=15)  # how far before an alarm its line may be
_LINE_AFTER = timedelta(minutes=1)  # the platform stamps an exit after its last line
LINE_LIMIT = 160
_CLOSING = re.compile(r"\] stopped on \S+ after .*; exit [1-9]")
_EXCEPTION = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)\b")
_SIGNAL = re.compile(r"\] stop signal \S+:")
_SHAPES = (_CLOSING, _EXCEPTION, _SIGNAL)
_URL_CREDENTIAL = re.compile(r"(\w+://)[^/\s:@]+:[^@\s]+@")
_BEARER = re.compile(r"(?i)\bbearer\s+\S+")
_NAMED_SECRET = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|apikey|api_key|key|sig|signature"
    r"|sharedaccesskey|accountkey|access_token|client_secret)(\s*[=:]\s*)"
    r"[^\s;&'\",]+"
)
_LONG_RUN = re.compile(r"[A-Za-z0-9+/=_\-]{32,}")
_AMOUNT = re.compile(
    r"\$\s?\d[\d,]*(?:\.\d+)?|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d+\.\d{2}\b"
)


def choose_line(lines: Sequence[tuple[datetime, str]], occurred: datetime) -> str:
    """Return the safe line that explains an alarm at ``occurred``, or ``""``."""
    inside = [
        (at, text)
        for at, text in lines
        if occurred - LINE_WINDOW <= at <= occurred + _LINE_AFTER
    ]
    for shape in _SHAPES:
        matching = [(at, text) for at, text in inside if shape.search(text)]
        if matching:
            return safe_line(max(matching, key=lambda item: item[0])[1])
    return ""


def safe_line(text: str) -> str:
    """Return one line with credentials, long tokens and amounts masked, and cut."""
    line = " ".join(text.split())
    line = _URL_CREDENTIAL.sub(r"\1***@", line)
    line = _BEARER.sub("Bearer ***", line)
    line = _NAMED_SECRET.sub(r"\1\2***", line)
    line = _LONG_RUN.sub("***", line)
    line = _AMOUNT.sub("#", line)
    return line if len(line) <= LINE_LIMIT else line[: LINE_LIMIT - 1] + "…"
```

### 3. The two queries — `orchestration/container_queries.py` (new)

`orchestration/container_queries.py` — new, 91 lines:

```python
"""The container sensor's two workspace queries, and how a reply is read.

Agent: orchestration
Role: word the Log Analytics queries the sensor sends and parse their result table.
External I/O: none.

Only instants and replica names are put into a query. A replica name is checked
against the platform's naming rule before it is, so no text a row carries can change
what a query asks (DL-301).
"""

from __future__ import annotations

import re
from datetime import UTC
from typing import TYPE_CHECKING

from orchestration.container_events import SENSED_REASONS

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from datetime import datetime

EVENT_ROWS_MAX = 5000
LINE_ROWS_MAX = 500
REPLICA_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}$")
_LINE_FILTER = (
    "| where Log_s contains '] stop' or Log_s matches regex "
    r"@'^\s*[A-Za-z_][A-Za-z0-9_.]*(Error|Exception)\b'"
)

Row = dict[str, object]


class ContainerLogReadError(RuntimeError):
    """A workspace read failed; ``status`` is a word safe to print and record."""

    def __init__(self, status: str) -> None:
        """Keep the status word; the message repeats it and nothing else."""
        super().__init__(f"read failed ({status})")
        self.status = status


def events_query(start: datetime, until: datetime) -> str:
    """Return the query for the sensed rows ingested after ``start`` up to ``until``."""
    reasons = ", ".join(f"'{reason}'" for reason in SENSED_REASONS)
    return (
        "ContainerAppSystemLogs_CL\n"
        f"| where ingestion_time() > {kql_time(start)}"
        f" and ingestion_time() <= {kql_time(until)}\n"
        f"| where Reason_s in ({reasons}) or Level =~ 'error'\n"
        "| project TimeGenerated, time_t, ContainerAppName_s, JobName_s, "
        "RevisionName_s, ReplicaName_s, Reason_s, Level, Log_s, Count_d\n"
        "| order by TimeGenerated asc\n"
        f"| take {EVENT_ROWS_MAX}"
    )


def lines_query(replicas: Sequence[str], start: datetime, until: datetime) -> str:
    """Return the query for the stderr lines that can explain an alarm."""
    names = ", ".join(f"'{name}'" for name in replicas if REPLICA_NAME.match(name))
    return (
        "ContainerAppConsoleLogs_CL\n"
        f"| where TimeGenerated between ({kql_time(start)} .. {kql_time(until)})\n"
        f"| where ContainerGroupName_s in ({names}) and Stream_s == 'stderr'\n"
        f"{_LINE_FILTER}\n"
        "| project TimeGenerated, ContainerGroupName_s, Log_s\n"
        "| order by TimeGenerated desc\n"
        f"| take {LINE_ROWS_MAX}"
    )


def kql_time(moment: datetime) -> str:
    """Render an aware instant as a query-language UTC literal."""
    return f"datetime({moment.astimezone(UTC):%Y-%m-%dT%H:%M:%S.%fZ})"


def table_rows(payload: Mapping[str, object]) -> list[Row]:
    """Return the first result table as one dict per row."""
    tables = payload.get("tables")
    if not isinstance(tables, list) or not tables or not isinstance(tables[0], dict):
        raise ContainerLogReadError("shape")
    columns = tables[0].get("columns")
    rows = tables[0].get("rows")
    if not isinstance(columns, list) or not isinstance(rows, list):
        raise ContainerLogReadError("shape")
    try:
        names = [str(column["name"]) for column in columns]
        return [dict(zip(names, row, strict=True)) for row in rows]
    except (KeyError, TypeError, ValueError):
        raise ContainerLogReadError("shape") from None
```

### 4. The reader — `orchestration/container_logs.py` (new)

`orchestration/container_logs.py` — new, 129 lines:

```python
"""Read the platform's container events and console lines from the log workspace.

Agent: orchestration
Role: query Log Analytics as the dispatcher job's managed identity (DL-301).
External I/O: HTTP GET to the job's managed-identity endpoint, HTTPS POST to the
    Log Analytics query API, both through an injectable opener.

No SDK: the image stays as it is, and the token is one documented GET. An error
carries a status word only, never a response body, a query or a token.
"""

from __future__ import annotations

import json
from datetime import UTC, timedelta
from typing import TYPE_CHECKING, Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from orchestration.container_queries import (
    REPLICA_NAME,
    ContainerLogReadError,
    events_query,
    lines_query,
    table_rows,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from datetime import datetime

    from orchestration.container_queries import Row

LOGS_API = "https://api.loganalytics.io/v1/workspaces"
_RESOURCE = "https://api.loganalytics.io"
_IDENTITY_API = "2019-08-01"
_TIMESPAN_LEAD = timedelta(hours=1)  # an event is stamped before it is ingested


class LogReader(Protocol):
    """The two reads the sensor makes of the workspace."""

    def events(self, start: datetime, until: datetime) -> list[Row]:
        """Return the sensed rows that reached the workspace in ``(start, until]``."""
        ...  # pragma: no cover - protocol declaration only.

    def error_lines(
        self, replicas: Sequence[str], start: datetime, until: datetime
    ) -> list[Row]:
        """Return candidate stderr lines of ``replicas`` stamped in the window."""
        ...  # pragma: no cover - protocol declaration only.


class LogAnalyticsReader:
    """The workspace, read as the managed identity the platform gives the job."""

    def __init__(
        self,
        workspace_id: str,
        *,
        environ: Mapping[str, str],
        timeout: float,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        """Bind the workspace, the identity endpoint's env and the opener."""
        self._workspace = workspace_id
        self._environ = environ
        self._timeout = timeout
        self._opener = opener
        self._token = ""

    def events(self, start: datetime, until: datetime) -> list[Row]:
        """Return the sensed rows that reached the workspace in ``(start, until]``."""
        return self._query(events_query(start, until), start - _TIMESPAN_LEAD, until)

    def error_lines(
        self, replicas: Sequence[str], start: datetime, until: datetime
    ) -> list[Row]:
        """Return candidate stderr lines of ``replicas``; an odd name is never sent."""
        names = sorted({name for name in replicas if REPLICA_NAME.match(name)})
        if not names:
            return []
        return self._query(lines_query(names, start, until), start, until)

    def _query(self, query: str, start: datetime, until: datetime) -> list[Row]:
        span = (
            f"{start.astimezone(UTC).isoformat()}/{until.astimezone(UTC).isoformat()}"
        )
        request = Request(  # noqa: S310 - a fixed HTTPS origin.
            f"{LOGS_API}/{quote(self._workspace, safe='')}/query",
            data=json.dumps({"query": query, "timespan": span}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._bearer()}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        return table_rows(self._send(request))

    def _bearer(self) -> str:
        if self._token:
            return self._token
        endpoint = self._environ.get("IDENTITY_ENDPOINT", "")
        header = self._environ.get("IDENTITY_HEADER", "")
        if not endpoint or not header:
            raise ContainerLogReadError("no managed identity")
        query = urlencode({"resource": _RESOURCE, "api-version": _IDENTITY_API})
        request = Request(  # noqa: S310 - the platform's own identity endpoint.
            f"{endpoint}?{query}", headers={"X-IDENTITY-HEADER": header}, method="GET"
        )
        token = self._send(request).get("access_token")
        if not isinstance(token, str) or not token:
            raise ContainerLogReadError("no token")
        self._token = token
        return token

    def _send(self, request: Request) -> dict[str, object]:
        try:
            with self._opener(request, timeout=self._timeout) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise ContainerLogReadError(str(exc.code)) from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise ContainerLogReadError("transport") from None
        if not isinstance(payload, dict):
            raise ContainerLogReadError("shape")
        return payload
```

### 5. The sensor's graph facts — `orchestration/container_sensor_graph.py` (new)

`orchestration/container_sensor_graph.py` — new, 91 lines:

```python
"""The container sensor's graph facts: its reads, its events and what was told.

Agent: orchestration
Role: name the sensor's labels and keys, find where the last read ended, and find the
    alarms no read has told yet (DL-301).
External I/O: reads the injected GraphStore.
"""

from __future__ import annotations

from datetime import UTC, timedelta
from typing import TYPE_CHECKING

from orchestration.daily_brief_fills import parse_instant

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore, Node
    from orchestration.container_events import ContainerEvent
    from orchestration.settings import OrchestratorSettings

CONTAINER_EVENT = "ContainerEvent"
SENSOR_READ = "ContainerSensorRead"
TOLD = "TOLD"  # ContainerSensorRead -> ContainerEvent: the read whose message told it
READ_OK = "read"
READ_FAILED = "failed"


def read_key(until: datetime) -> str:
    """Name the read that ends at ``until``."""
    return f"container-sensor-read:{until.astimezone(UTC).isoformat()}"


def read_window(
    previous: datetime | None, until: datetime, settings: OrchestratorSettings
) -> tuple[datetime, bool]:
    """Return where this read starts, and whether the look-back cap cut it."""
    if previous is None:
        start = until - timedelta(hours=settings.container_sensor_first_read_hours)
    else:
        start = previous - timedelta(minutes=settings.container_sensor_overlap_minutes)
    floor = until - timedelta(hours=settings.container_sensor_max_lookback_hours)
    return (floor, True) if start < floor else (start, False)


def last_read_until(graph: GraphStore) -> datetime | None:
    """Return where the latest successful read ended, or None before the first."""
    ends = [
        parse_instant(node.props.get("read_until"))
        for node in graph.list_nodes(SENSOR_READ)
        if node.props.get("outcome") == READ_OK
    ]
    return max((end for end in ends if end is not None), default=None)


def untold_alarms(graph: GraphStore, since: datetime) -> list[Node]:
    """Return the alarm events recorded since ``since`` that no read has told."""
    keys = graph.keys_without_edge(
        CONTAINER_EVENT, TOLD, downstream=False, created_at_from=since
    )
    nodes = (graph.get_node(CONTAINER_EVENT, key) for key in keys)
    alarms = [
        node for node in nodes if node is not None and node.props.get("alarm") is True
    ]
    return sorted(
        alarms, key=lambda node: (str(node.props.get("occurred_at", "")), node.key)
    )


def event_props(
    event: ContainerEvent, why: str, key: str, until: datetime
) -> dict[str, object]:
    """Return the properties one recorded event holds."""
    props: dict[str, object] = {
        "app": event.app,
        "revision": event.revision,
        "replica": event.replica,
        "kind": event.kind,
        "alarm": event.alarm,
        "reason": event.reason,
        "message": event.message,
        "times": event.times,
        "occurred_at": event.occurred_at,
        "error_line": why,
        "read_key": key,
        "created_at": until.isoformat(),
    }
    if event.exit_code is not None:
        props["exit_code"] = event.exit_code
    return props
```

### 6. The read and its fault boundary — `container_sensor.py`, `container_sensor_guard.py` (new)

`orchestration/container_sensor.py` — new, 179 lines:

```python
"""The container sensor: each dispatcher fire reads the platform's container events.

Agent: orchestration
Role: record new container events and tell the operator once of every alarm (DL-301).
External I/O: reads/writes the injected GraphStore; calls the injected log reader and
    the injected alarm port.

Imported only inside `container_sensor_guard`'s fault boundary, so neither this
module nor anything it imports can stop a dispatcher fire (`DSP-FAIL-04`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, timedelta
from typing import TYPE_CHECKING, Protocol

from orchestration.container_alarm_text import alarm_message, group_events
from orchestration.container_events import ContainerEvent, classify
from orchestration.container_lines import LINE_WINDOW, choose_line
from orchestration.container_queries import EVENT_ROWS_MAX
from orchestration.container_sensor_graph import (
    CONTAINER_EVENT,
    READ_OK,
    SENSOR_READ,
    TOLD,
    event_props,
    last_read_until,
    read_key,
    read_window,
    untold_alarms,
)
from orchestration.daily_brief_fills import parse_instant

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from kernel import GraphStore, Node
    from orchestration.container_logs import LogReader
    from orchestration.container_queries import Row
    from orchestration.settings import OrchestratorSettings

_Lines = dict[str, list[tuple["datetime", str]]]


class AlarmPort(Protocol):
    """The one operation the sensor needs of the operator's channel."""

    last_error: str

    def send_alarm(self, *, text: str) -> int | None:
        """Send one plain-text alarm; return its message id, or None on failure."""
        ...  # pragma: no cover - protocol declaration only.


@dataclass(frozen=True)
class SensorOutcome:
    """What one read found, recorded and told."""

    read_key: str
    rows: int
    recorded: int
    alarms: int
    told: int
    send_error: str


def sense_containers(
    graph: GraphStore,
    reader: LogReader,
    port: AlarmPort,
    *,
    now: datetime,
    settings: OrchestratorSettings,
) -> SensorOutcome:
    """Read the events since the last read, record the new ones, tell the untold."""
    until = now.astimezone(UTC)
    start, capped = read_window(last_read_until(graph), until, settings)
    rows = reader.events(start, until)
    events = _new_events(graph, rows)
    lines = _error_lines(reader, events, until)
    key = read_key(until)
    for event in events:
        why = _why(event, lines)
        graph.merge_node(
            CONTAINER_EVENT, event.key, event_props(event, why, key, until)
        )
    lookback = until - timedelta(hours=settings.container_sensor_max_lookback_hours)
    untold = untold_alarms(graph, lookback)
    cap = settings.container_sensor_max_lookback_hours if capped else None
    message_id, send_error = _tell(port, untold, settings=settings, capped_hours=cap)
    alarms = sum(1 for event in events if event.alarm)
    told = len(untold) if message_id is not None else 0
    props: dict[str, object] = {
        "read_from": start.isoformat(),
        "read_until": until.isoformat(),
        "outcome": READ_OK,
        "rows": len(rows),
        "recorded": len(events),
        "alarms": alarms,
        "reports": len(events) - alarms,
        "told": told,
        "capped": capped,
        "truncated": len(rows) >= EVENT_ROWS_MAX,
        "created_at": until.isoformat(),
    }
    if message_id is not None:
        props["message_id"] = message_id
    if send_error:
        props["send_error"] = send_error
    read = graph.merge_node(SENSOR_READ, key, props)
    if message_id is not None:
        for node in untold:
            graph.add_edge(read, node, TOLD)
    return SensorOutcome(key, len(rows), len(events), alarms, told, send_error)


def _new_events(graph: GraphStore, rows: Sequence[Row]) -> list[ContainerEvent]:
    found: dict[str, ContainerEvent] = {}
    for row in rows:
        event = classify(row)
        if event is None or event.key in found:
            continue
        if graph.get_node(CONTAINER_EVENT, event.key) is None:
            found[event.key] = event
    return list(found.values())


def _error_lines(
    reader: LogReader, events: Sequence[ContainerEvent], until: datetime
) -> _Lines:
    alarms = [event for event in events if event.alarm and event.replica]
    moments = [parse_instant(event.occurred_at) for event in alarms]
    known = [moment for moment in moments if moment is not None]
    if not known:
        return {}
    rows = reader.error_lines(
        [event.replica for event in alarms], min(known) - LINE_WINDOW, until
    )
    lines: _Lines = {}
    for row in rows:
        at = parse_instant(row.get("TimeGenerated"))
        if at is not None:
            replica = str(row.get("ContainerGroupName_s", ""))
            lines.setdefault(replica, []).append((at, str(row.get("Log_s", ""))))
    return lines


def _why(event: ContainerEvent, lines: _Lines) -> str:
    occurred = parse_instant(event.occurred_at)
    if not event.alarm or occurred is None:
        return ""
    return choose_line(lines.get(event.replica, []), occurred)


def _tell(
    port: AlarmPort,
    untold: Sequence[Node],
    *,
    settings: OrchestratorSettings,
    capped_hours: int | None,
) -> tuple[int | None, str]:
    if not untold:
        return None, ""
    text = alarm_message(
        group_events(node.props for node in untold),
        timezone=settings.operator_timezone,
        limit=settings.container_sensor_alarm_groups_max,
        capped_hours=capped_hours,
    )
    try:
        message_id = port.send_alarm(text=text)
    except Exception as exc:  # the port's text may quote the alarm: keep the type only
        return None, type(exc).__name__
    if message_id is None:
        error = str(getattr(port, "last_error", "") or "")
        return None, error if error.isidentifier() else "no message id"
    return message_id, ""
```

`orchestration/container_sensor_guard.py` — new, 160 lines:

```python
"""The fault boundary around the container sensor, and its wiring from the job's env.

Agent: orchestration
Role: run the sensor on every dispatcher fire so that no failure of it reaches the fire.
External I/O: process environment; builds the graph and the Telegram port through
    injected factories; writes Fault and ContainerSensorRead nodes; returns one line.

The script imports this module and nothing else of the sensor. The sensor itself is
imported inside the `try` below, so a module the image lacks is a fault and the fire
is unchanged (`DSP-FAIL-04`). A line or a fault names a step, an error type and a
status word, never a value (`DSP-SEC-03`).
"""

from __future__ import annotations

import os
import sys
from datetime import UTC
from typing import TYPE_CHECKING, cast

from kernel import CollectingFaultSink, GraphFaultSink
from kernel.errors import fault_boundary
from orchestration.settings import OrchestratorSettings

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from datetime import datetime

    from kernel import GraphStore
    from orchestration.container_logs import LogReader
    from orchestration.container_sensor import AlarmPort, SensorOutcome

WORKSPACE_ENV = "LOG_ANALYTICS_WORKSPACE_ID"


class ContainerSensorFailedError(RuntimeError):
    """The sensor did not read or did not tell; names the step and error type only."""


def sense_from_env(
    *,
    now: datetime,
    graph_factory: Callable[[], object],
    port_factory: Callable[[], object],
    environ: Mapping[str, str] | None = None,
) -> str | None:
    """Run the sensor when the job is configured for it; return the line to print."""
    env = os.environ if environ is None else environ
    workspace = env.get(WORKSPACE_ENV, "").strip()
    if not workspace:
        return None  # not configured: the fire's own output stays as it was
    if not env.get("POSTGRES_DSN"):
        return "error container-sensor not run: POSTGRES_DSN is required"
    try:
        from orchestration.container_logs import LogAnalyticsReader

        settings = OrchestratorSettings()
        reader = LogAnalyticsReader(
            workspace,
            environ=dict(env),
            timeout=settings.container_sensor_timeout_seconds,
        )
        graph = cast("GraphStore", graph_factory())
    except Exception as exc:  # the boundary itself: a type name, never a message
        return f"error container-sensor not run: {type(exc).__name__}"
    try:
        port = cast("AlarmPort", port_factory())
        return sense_safely(graph, reader, port, now=now, settings=settings)
    finally:
        close = getattr(graph, "close", None)
        if callable(close):
            try:
                close()
            except Exception as exc:  # a close that fails must not end the fire
                sys.stderr.write(
                    f"error container-sensor close: {type(exc).__name__}\n"
                )


def sense_safely(
    graph: GraphStore,
    reader: LogReader,
    port: AlarmPort,
    *,
    now: datetime,
    settings: OrchestratorSettings,
) -> str:
    """Run one read; any failure becomes one Fault and a failed read, never a raise."""
    try:
        from orchestration.container_sensor import sense_containers

        outcome = sense_containers(graph, reader, port, now=now, settings=settings)
    except Exception as exc:  # the boundary itself: a type and a status word
        failure = _failure(exc)
    else:
        return _told(graph, outcome)
    # Recorded once the handler has ended, so the Fault's traceback chains no earlier
    # error and the exception's own text never reaches the graph (DSP-SEC-03).
    _record_failed_read(graph, now, failure)
    _record(graph, f"container sensor did not read: {failure}")
    return f"error container-sensor failed: {failure}"


def _told(graph: GraphStore, outcome: SensorOutcome) -> str:
    line = (
        f"container-sensor read {outcome.rows} rows: {outcome.recorded} new events, "
        f"{outcome.alarms} alarms, told {outcome.told}"
    )
    if outcome.send_error:
        _record(graph, f"container alarm not sent: {outcome.send_error}")
        line += f", send failed ({outcome.send_error})"
    return line


def _failure(exc: Exception) -> str:
    status = getattr(exc, "status", "")
    name = type(exc).__name__
    return f"{name} ({status})" if isinstance(status, str) and status else name


def _record_failed_read(graph: GraphStore, now: datetime, failure: str) -> None:
    try:
        from orchestration.container_sensor_graph import (
            READ_FAILED,
            SENSOR_READ,
            read_key,
        )

        until = now.astimezone(UTC).isoformat()
        graph.merge_node(
            SENSOR_READ,
            read_key(now),
            {
                "read_until": until,
                "outcome": READ_FAILED,
                "error": failure,
                "created_at": until,
            },
        )
    except Exception as exc:  # the graph refused it: the Fault below still tries
        sys.stderr.write(
            f"error container-sensor read not recorded: {type(exc).__name__}\n"
        )


def _record(graph: GraphStore, message: str) -> None:
    # Raised outside any `except`, so the Fault's traceback chains no earlier error.
    try:
        with fault_boundary(
            GraphFaultSink(graph, CollectingFaultSink()),
            agent="orchestration",
            module="orchestration.container_sensor",
            capability="container_sensor",
            reraise=False,
        ):
            raise ContainerSensorFailedError(message)
    except Exception as exc:  # the graph refused the fault itself
        sys.stderr.write(
            f"error container-sensor fault not recorded: {type(exc).__name__}\n"
        )
```

### 7. The words — `orchestration/container_alarm_text.py` (new)

`orchestration/container_alarm_text.py` — new, 177 lines:

```python
"""The words of a container alarm: one message for the alarms not yet told.

Agent: orchestration
Role: group recorded container events and word the alarm message and the brief's line.
External I/O: none (zone data is read through zoneinfo).

A failure that hits the fleet hits many apps at once (2026-09-25: one cause, 13
apps, 102 exits), so a line is one kind of failure and names its apps. Takes event
properties as the graph holds them and reads no clock. Melbourne time first (DL-216).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from orchestration.container_events import (
    EXIT_ERROR,
    KILLED,
    MEMORY_KILL,
    PLATFORM_ERROR,
    PREEMPTED,
    PROVISION_FAILED,
    SCALER_FAILED,
    START_FAILED,
)
from orchestration.daily_brief_fills import parse_instant
from orchestration.daily_brief_text import local_stamp

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

_WORDS = {
    START_FAILED: "failed to start",
    PROVISION_FAILED: "revision failed to provision",
    SCALER_FAILED: "scale rule refused",
    MEMORY_KILL: "killed for memory",
    KILLED: "killed (exit code 137)",
    PLATFORM_ERROR: "platform error",
    PREEMPTED: "moved off its node by the platform",
}
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
TIMES = chr(0x00D7)  # the multiplication sign of a repeat count
APPS_NAMED = 4
BRIEF_GROUPS = 3


@dataclass(frozen=True)
class AlarmGroup:
    """Events of one kind and exit code: their apps, count, latest time and why."""

    kind: str
    exit_code: int | None
    apps: tuple[str, ...]
    times: int
    last: datetime
    why: str
    why_app: str = ""


def group_events(facts: Iterable[Mapping[str, object]]) -> list[AlarmGroup]:
    """Group event properties by kind and exit code; the newest group first."""
    buckets: dict[tuple[str, int | None], list[Mapping[str, object]]] = {}
    for fact in facts:
        buckets.setdefault((str(fact.get("kind", "")), _code(fact)), []).append(fact)
    groups = [_group(key, items) for key, items in buckets.items()]
    return sorted(groups, key=lambda item: (-item.last.timestamp(), item.kind))


def kind_words(group: AlarmGroup) -> str:
    """Say what happened, in the operator's words."""
    if group.kind == EXIT_ERROR:
        if group.exit_code is None:
            return "exited with an error"
        return f"exited with code {group.exit_code}"
    return _WORDS.get(group.kind, group.kind)


def alarm_message(
    groups: Sequence[AlarmGroup],
    *,
    timezone: str,
    limit: int,
    capped_hours: int | None = None,
) -> str:
    """Return the plain-text alarm: a header, one line per kind, the rest counted."""
    apps = {app for group in groups for app in group.apps}
    kinds = _count(len(groups), "kind")
    lines = [f"Container alarm: {_count(len(apps), 'app')}, {kinds} of failure"]
    for group in groups[:limit]:
        what = f"{kind_words(group)}{_times(group)}"
        lines.append(f"{what}: {_apps(group)} · {_when(group, timezone)}")
        if group.why:
            lines.append(f"  why ({group.why_app}): {group.why}")
    rest = groups[limit:]
    if rest:
        lines.append(f"and {_count(len(rest), 'more kind')} of failure")
    if capped_hours is not None:
        lines.append(
            f"Read only the last {capped_hours} hours; anything earlier is not read."
        )
    return "\n".join(lines)


def brief_summary(groups: Sequence[AlarmGroup]) -> str:
    """Return the brief's short account of the groups, at most three named."""
    named = [
        f"{kind_words(group)}{_times(group)} ({_apps(group)})"
        for group in groups[:BRIEF_GROUPS]
    ]
    rest = len(groups) - BRIEF_GROUPS
    if rest > 0:
        named.append(f"and {rest} more")
    return "; ".join(named)


def _group(
    key: tuple[str, int | None], items: list[Mapping[str, object]]
) -> AlarmGroup:
    # One replica's repeats arrive as rows with a rising count: take its highest.
    peaks: dict[tuple[str, str, str], int] = {}
    for item in items:
        incident = (
            str(item.get("app", "")),
            str(item.get("replica", "")),
            str(item.get("message", "")),
        )
        peaks[incident] = max(peaks.get(incident, 0), _whole(item.get("times")))
    ordered = sorted(items, key=_moment)
    explained = [item for item in ordered if item.get("error_line")]
    latest = explained[-1] if explained else {}
    return AlarmGroup(
        kind=key[0],
        exit_code=key[1],
        apps=tuple(sorted({str(item.get("app", "")) for item in items})),
        times=sum(peaks.values()),
        last=_moment(ordered[-1]),
        why=str(latest.get("error_line", "")),
        why_app=str(latest.get("app", "")),
    )


def _apps(group: AlarmGroup) -> str:
    named = ", ".join(group.apps[:APPS_NAMED])
    rest = len(group.apps) - APPS_NAMED
    return f"{named} and {rest} more" if rest > 0 else named


def _when(group: AlarmGroup, timezone: str) -> str:
    stamp = local_stamp(group.last, timezone)
    if stamp.endswith(" UTC"):
        return stamp
    return f"{stamp} ({group.last.astimezone(UTC):%H:%M} UTC)"


def _times(group: AlarmGroup) -> str:
    return f" {TIMES}{group.times}" if group.times > 1 else ""


def _moment(fact: Mapping[str, object]) -> datetime:
    return parse_instant(fact.get("occurred_at")) or _EPOCH


def _code(fact: Mapping[str, object]) -> int | None:
    value = fact.get("exit_code")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _whole(value: object) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return 1


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}{'' if number == 1 else 's'}"
```

### 8. The brief's line (new), and the changes to eight existing files

`orchestration/container_brief.py` — new, 58 lines:

```python
"""The daily brief's container line: what the sensor recorded in the last day.

Agent: orchestration
Role: say in one line whether the sensor read, and which alarms it recorded (DL-301).
External I/O: reads the injected GraphStore.

No line before the sensor's first read, so a fleet that has never run it briefs as
before. After that the line is always there: a sensor that stopped reading says so.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from orchestration.container_alarm_text import brief_summary, group_events
from orchestration.container_sensor_graph import CONTAINER_EVENT, READ_OK, SENSOR_READ
from orchestration.daily_brief_fills import parse_instant
from orchestration.daily_brief_text import local_stamp

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore

BRIEF_WINDOW = timedelta(hours=24)


def container_line(graph: GraphStore, *, now: datetime, timezone: str) -> str | None:
    """Return the brief's container line, or None before the sensor's first read."""
    reads = [
        (moment, node)
        for node in graph.list_nodes(SENSOR_READ)
        if (moment := parse_instant(node.props.get("read_until"))) is not None
    ]
    if not reads:
        return None
    latest_at, latest = max(reads, key=lambda item: (item[0], item[1].key))
    stamp = local_stamp(latest_at, timezone)
    if latest.props.get("outcome") != READ_OK:
        error = latest.props.get("error", "")
        return f"Containers: the sensor's last read failed ({error}) at {stamp}"
    since = now - BRIEF_WINDOW
    if latest_at < since:
        return f"Containers: the sensor has not read since {stamp}"
    recorded = [
        node.props
        for node in graph.list_nodes(CONTAINER_EVENT)
        if node.props.get("alarm") is True
        and (created := parse_instant(node.props.get("created_at"))) is not None
        and created >= since
    ]
    if not recorded:
        return "Containers: no alarm in 24 hours"
    groups = group_events(recorded)
    total = sum(group.times for group in groups)
    noun = "alarm" if total == 1 else "alarms"
    return f"Containers: {total} {noun} in 24 hours: {brief_summary(groups)}"
```

`orchestration/settings.py` — diff against `main`:

```diff
diff --git a/orchestration/settings.py b/orchestration/settings.py
index d31c354e..2c85da0e 100644
--- a/orchestration/settings.py
+++ b/orchestration/settings.py
@@ -52,6 +52,56 @@ class OrchestratorSettings(AgentSettings):
         le=240,
         unit="minutes",
     )
+    container_sensor_first_read_hours: int = tunable(
+        24,
+        why=(
+            "The sensor's first read covers one day, so the day's deploys before it "
+            "are seen and a month of old events does not arrive as one alarm (DL-301)."
+        ),
+        ge=1,
+        le=168,
+        unit="hours",
+    )
+    container_sensor_max_lookback_hours: int = tunable(
+        168,
+        why=(
+            "A read after a long gap covers at most a week; the workspace keeps 30 "
+            "days, and anything older than a week is history, not an alarm (DL-301)."
+        ),
+        ge=24,
+        le=720,
+        unit="hours",
+    )
+    container_sensor_overlap_minutes: int = tunable(
+        10,
+        why=(
+            "An event reached the workspace up to 2 min 36 s after it happened "
+            "(measured 2026-10-14, 48 hours); each read starts this long before the "
+            "last one ended, and a row read twice is recorded once (DL-301)."
+        ),
+        ge=3,
+        le=60,
+        unit="minutes",
+    )
+    container_sensor_alarm_groups_max: int = tunable(
+        8,
+        why=(
+            "One alarm message names at most this many kinds of failure and "
+            "counts the rest, so it stays readable and inside Telegram's limit."
+        ),
+        ge=1,
+        le=20,
+    )
+    container_sensor_timeout_seconds: float = tunable(
+        20.0,
+        why=(
+            "Each workspace call is bounded so a slow read cannot hold the fire; a "
+            "read of one day to one week took 1.3 to 3.6 s (measured 2026-10-14)."
+        ),
+        ge=1.0,
+        le=120.0,
+        unit="seconds",
+    )


 class DeliberationQualitySettings(AgentSettings):
```

`orchestration/telegram_client.py` — diff against `main`:

```diff
diff --git a/orchestration/telegram_client.py b/orchestration/telegram_client.py
index 101b988b..556a9e71 100644
--- a/orchestration/telegram_client.py
+++ b/orchestration/telegram_client.py
@@ -84,6 +84,13 @@ class TelegramClient:

     def send_brief(self, *, text: str) -> int | None:
         """Send the daily brief as plain text to the configured chat, no buttons."""
+        return self._send_text(text)
+
+    def send_alarm(self, *, text: str) -> int | None:
+        """Send a container alarm as plain text to the configured chat, no buttons."""
+        return self._send_text(text)
+
+    def _send_text(self, text: str) -> int | None:
         response = self._request(
             "sendMessage", {"chat_id": self._chat_id, "text": text}
         )
```

`orchestration/daily_brief_text.py` — diff against `main`:

```diff
diff --git a/orchestration/daily_brief_text.py b/orchestration/daily_brief_text.py
index b9e812f3..22fc186d 100644
--- a/orchestration/daily_brief_text.py
+++ b/orchestration/daily_brief_text.py
@@ -69,10 +69,12 @@ class BriefFacts:
     open_incidents: int = 0
     critical_flags: int = 0
     last_stage: str | None = None
+    containers: str | None = None


 def compose_brief(facts: BriefFacts) -> str:
     """Return the plain-text message; a run with no report gets the RED brief."""
+    sensed = (facts.containers,) if facts.containers else ()
     if facts.verdict == NOT_FINISHED:
         stage = (
             f"Last stage finished: {facts.last_stage}"
@@ -80,7 +82,7 @@ def compose_brief(facts: BriefFacts) -> str:
             else "No stage finished"
         )
         return "\n".join(
-            (_header(facts), stage, _orders(facts.orders), _needs_you(facts))
+            (_header(facts), stage, _orders(facts.orders), *sensed, _needs_you(facts))
         )
     return "\n".join(
         (
@@ -89,6 +91,7 @@ def compose_brief(facts: BriefFacts) -> str:
             facts.scoreboard or "Scoreboard: not in this run's report",
             _orders(facts.orders),
             _fills(facts.fills),
+            *sensed,
             _needs_you(facts),
         )
     )
```

`orchestration/daily_brief_facts.py` — diff against `main`:

```diff
diff --git a/orchestration/daily_brief_facts.py b/orchestration/daily_brief_facts.py
index f51dc755..9fcb69fd 100644
--- a/orchestration/daily_brief_facts.py
+++ b/orchestration/daily_brief_facts.py
@@ -20,6 +20,7 @@ from typing import TYPE_CHECKING
 from agents.supervisor.domain.health import compute_health
 from contracts.run_posture import RUN_POSTURE_DEGRADED, run_posture
 from orchestration.batch_chain import CHAIN, POSITION_SYNC_KEY
+from orchestration.container_brief import container_line
 from orchestration.daily_brief_fills import fills_between, parse_instant, run_orders
 from orchestration.daily_brief_text import (
     NOT_FINISHED,
@@ -71,6 +72,7 @@ def brief_facts(
         open_incidents=health["open_incidents"],
         critical_flags=health["pending_human_flags"],
         last_stage=_last_stage(nodes),
+        containers=container_line(graph, now=now, timezone=timezone),
     )
     snapshot = nodes.get("Snapshot")
     if snapshot is None or pm_run is None:
```

`scripts/dispatch_scheduled_run.py` — diff against `main`:

```diff
diff --git a/scripts/dispatch_scheduled_run.py b/scripts/dispatch_scheduled_run.py
index c1498df8..ea9b5ee0 100644
--- a/scripts/dispatch_scheduled_run.py
+++ b/scripts/dispatch_scheduled_run.py
@@ -23,6 +23,7 @@ if str(_ROOT) not in sys.path:

 from dotenv import load_dotenv  # noqa: E402

+from orchestration.container_sensor_guard import sense_from_env  # noqa: E402
 from orchestration.scheduled_dispatch import (  # noqa: E402
     CalendarWindowExceededError,
     ScheduledDispatchResult,
@@ -35,6 +36,17 @@ from orchestration.telegram_client import TelegramClient  # noqa: E402


 def main(argv: list[str] | None = None) -> int:
+    """Run one scheduled dispatch attempt, then the container sensor (DSP-TRG-04)."""
+    status = _dispatch(argv)
+    line = sense_from_env(
+        now=datetime.now(tz=UTC), graph_factory=_live_graph, port_factory=_telegram
+    )
+    if line:
+        print(line, file=sys.stderr if line.startswith("error") else sys.stdout)
+    return status
+
+
+def _dispatch(argv: list[str] | None) -> int:
     """Run one scheduled dispatch attempt and return a process status."""
     parser = argparse.ArgumentParser(description="scheduled graph-pull dispatcher")
     parser.add_argument(
@@ -75,10 +87,7 @@ def main(argv: list[str] | None = None) -> int:
                 graph,
                 as_of=as_of,
                 now=datetime.now(tz=UTC),
-                telegram=TelegramClient(
-                    api_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
-                    chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
-                ),
+                telegram=_telegram(),
             )
         finally:
             close = getattr(graph, "close", None)
@@ -119,6 +128,13 @@ def format_dispatch_result(result: ScheduledDispatchResult) -> str:
     return f"{result.action} {result.run_id} reason={result.reason}"


+def _telegram() -> TelegramClient:
+    return TelegramClient(
+        api_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
+        chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
+    )
+
+
 def _live_graph() -> object:
     from kernel.graph_env import build_graph_from_env

```

`orchestration/Dockerfile` — diff against `main`:

```diff
diff --git a/orchestration/Dockerfile b/orchestration/Dockerfile
index 9058bbcd..5263c245 100644
--- a/orchestration/Dockerfile
+++ b/orchestration/Dockerfile
@@ -66,6 +66,15 @@ COPY agents/supervisor/store.py agents/supervisor/store.py
 COPY orchestration/__init__.py orchestration/__init__.py
 COPY orchestration/batch_chain.py orchestration/batch_chain.py
 COPY orchestration/batch_trace.py orchestration/batch_trace.py
+COPY orchestration/container_alarm_text.py orchestration/container_alarm_text.py
+COPY orchestration/container_brief.py orchestration/container_brief.py
+COPY orchestration/container_events.py orchestration/container_events.py
+COPY orchestration/container_lines.py orchestration/container_lines.py
+COPY orchestration/container_logs.py orchestration/container_logs.py
+COPY orchestration/container_queries.py orchestration/container_queries.py
+COPY orchestration/container_sensor.py orchestration/container_sensor.py
+COPY orchestration/container_sensor_graph.py orchestration/container_sensor_graph.py
+COPY orchestration/container_sensor_guard.py orchestration/container_sensor_guard.py
 COPY orchestration/daily_brief.py orchestration/daily_brief.py
 COPY orchestration/daily_brief_facts.py orchestration/daily_brief_facts.py
 COPY orchestration/daily_brief_fills.py orchestration/daily_brief_fills.py
```

`orchestration/packs/trading_graph_vocabulary.json` — diff against `main`:

```diff
diff --git a/orchestration/packs/trading_graph_vocabulary.json b/orchestration/packs/trading_graph_vocabulary.json
index 5ec70019..d0f0989e 100644
--- a/orchestration/packs/trading_graph_vocabulary.json
+++ b/orchestration/packs/trading_graph_vocabulary.json
@@ -82,7 +82,9 @@
     "TradeNarrative",
     "TrainingExample",
     "WorkItemQuarantine",
-    "_Reachability"
+    "_Reachability",
+    "ContainerEvent",
+    "ContainerSensorRead"
   ],
   "edge_types": [
     "ADVISES",
@@ -130,6 +132,7 @@
     "STOPS_WITH",
     "SUMMARISES",
     "SURVIVED",
+    "TOLD",
     "TRAINED_ON"
   ],
   "edge_signatures": [
@@ -372,6 +375,11 @@
       "Snapshot",
       "SUMMARISES",
       "PMRun"
+    ],
+    [
+      "ContainerSensorRead",
+      "TOLD",
+      "ContainerEvent"
     ]
   ],
   "owners": {},
@@ -613,6 +621,37 @@
       "settled",
       "settling_ref",
       "voided"
+    ],
+    "ContainerEvent": [
+      "alarm",
+      "app",
+      "created_at",
+      "error_line",
+      "exit_code",
+      "kind",
+      "message",
+      "occurred_at",
+      "read_key",
+      "reason",
+      "replica",
+      "revision",
+      "times"
+    ],
+    "ContainerSensorRead": [
+      "alarms",
+      "capped",
+      "created_at",
+      "error",
+      "message_id",
+      "outcome",
+      "read_from",
+      "read_until",
+      "recorded",
+      "reports",
+      "rows",
+      "send_error",
+      "told",
+      "truncated"
     ]
   },
   "_owners_note": "Empty deliberately. The 8 agents that declare labels_owned mix write-sets with read-sets (reporter) and a wildcard (supervisor 'all'), so the declarations are not yet accurate enough to enforce. Reconciling them is the named next step - the mechanism (Vocabulary.check_node writer=) is built and tested."
```

`infra/deploy-agents.ps1` — diff against `main`:

```diff
diff --git a/infra/deploy-agents.ps1 b/infra/deploy-agents.ps1
index c6ce8528..9c9e3abd 100644
--- a/infra/deploy-agents.ps1
+++ b/infra/deploy-agents.ps1
@@ -3,6 +3,7 @@
 #   pwsh infra/deploy-agents.ps1 preflight   # just the readiness checks
 #   pwsh infra/deploy-agents.ps1 up -Tag s103 # preflight → schema → master → 15 agents + cron job
 #   pwsh infra/deploy-agents.ps1 down         # delete apps + dispatcher job
+#   pwsh infra/deploy-agents.ps1 sensor       # the job's identity + workspace read (DL-301)
 #
 # Operator tunables and the dispatcher cron come from the pack
 # (orchestration/packs/trading_tunables.json), never from live cluster state: a
@@ -14,7 +15,7 @@
 # POSTGRES_DSN is the schema/admin DSN; fleet roles use per-target DSNs.

 param(
-  [ValidateSet('preflight', 'up', 'postgres-flip', 'servicebus-flip', 'down')]
+  [ValidateSet('preflight', 'up', 'postgres-flip', 'servicebus-flip', 'sensor', 'down')]
   [string]$Action = 'preflight',
   [string]$Tag = 'latest',
   # DL-294 amendment 1: one readiness check, at the wake, before the 22:30 UTC dispatch.
@@ -43,6 +44,10 @@ $DISPATCHER_JOB = "dispatcher-cron"
 $POSTGRES_APP_SECRET = "postgres-dsn" # pragma: allowlist secret
 $SERVICEBUS_APP_SECRET = "servicebus-connection-string" # pragma: allowlist secret
 $SERVICEBUS_BUNDLE_SECRET = "servicebus-connection-strings" # pragma: allowlist secret
+# DL-301: the container sensor reads this one workspace, with this one role.
+$LOG_WORKSPACE = "trading-agents-logs"
+$SENSOR_ROLE = "Log Analytics Reader"
+$SENSOR_ENV = "LOG_ANALYTICS_WORKSPACE_ID"
 # Container App name → GHCR image suffix (app names can't contain underscores).
 $AGENTS = [ordered]@{
   scanner = "scanner"; analyst = "analyst"; "portfolio-manager" = "portfolio_manager"
@@ -514,7 +519,7 @@ function Assert-FleetEnvPreserved {
     $planned = @(Get-AgentEnv $name "url" "pub" | ForEach-Object { ($_ -split "=", 2)[0] })
     $ok = (Assert-EnvPreserved $name (Get-LiveEnvNames $name) $planned) -and $ok
   }
-  $dispatcherPlanned = @("POSTGRES_DSN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID") +
+  $dispatcherPlanned = @("POSTGRES_DSN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", $SENSOR_ENV) +
   @((Get-ServiceBusConfig "dispatcher").envVars | ForEach-Object { ($_ -split "=", 2)[0] })
   $ok = (Assert-EnvPreserved $DISPATCHER_JOB (Get-LiveJobEnvNames $DISPATCHER_JOB) $dispatcherPlanned) -and $ok
   Bot
@@ -721,6 +726,39 @@ function Set-JobVocabulary {
   return (Get-JobState $DISPATCHER_JOB) -eq "Succeeded"
 }

+function Enable-ContainerSensor {
+  # DL-301: the dispatcher job reads the platform's container events as its own
+  # system-assigned identity, which holds one role on the one workspace. Nothing
+  # is stored for it. Every step is idempotent and read back, so a re-run is safe.
+  Top "CONTAINER SENSOR"
+  $ws = az monitor log-analytics workspace show --resource-group $RG --subscription $SUB `
+    --workspace-name $LOG_WORKSPACE --query "{id:id, customerId:customerId}" -o json 2>$null |
+  ConvertFrom-Json
+  Check ([bool]$ws) "log workspace $LOG_WORKSPACE"
+  if (-not $ws) { Bot; return $false }
+  $principal = az containerapp job identity assign --name $DISPATCHER_JOB --resource-group $RG `
+    --subscription $SUB --system-assigned --query principalId -o tsv 2>$null
+  Check ([bool]$principal) "$DISPATCHER_JOB system-assigned identity"
+  if (-not $principal) { Bot; return $false }
+  $held = az role assignment list --assignee $principal --role $SENSOR_ROLE --scope $ws.id `
+    --subscription $SUB --query "length(@)" -o tsv 2>$null
+  if ($held -ne "1") {
+    az role assignment create --assignee-object-id $principal --assignee-principal-type ServicePrincipal `
+      --role $SENSOR_ROLE --scope $ws.id --subscription $SUB -o none 2>$null | Out-Null
+    $held = az role assignment list --assignee $principal --role $SENSOR_ROLE --scope $ws.id `
+      --subscription $SUB --query "length(@)" -o tsv 2>$null
+  }
+  Check ($held -eq "1") "$SENSOR_ROLE on $LOG_WORKSPACE only"
+  $state = az containerapp job update --name $DISPATCHER_JOB --resource-group $RG `
+    --subscription $SUB --set-env-vars "$SENSOR_ENV=$($ws.customerId)" `
+    --query properties.provisioningState -o tsv 2>$null
+  Check ($state -eq "Succeeded") "$SENSOR_ENV set on $DISPATCHER_JOB"
+  $vocabOk = ($state -eq "Succeeded") -and (Set-JobVocabulary)
+  Check $vocabOk "graph vocabulary on $DISPATCHER_JOB"
+  Bot
+  return ($held -eq "1") -and $vocabOk
+}
+
 function Up {
   if (-not (Preflight)) { Write-Host "`nPreflight failed — fix the [XX] items above." -ForegroundColor Red; return }
   # Refuse before the first create, not after the ninth: a deploy that discards
@@ -809,6 +847,8 @@ function Up {
   }
   Bot
   Deploy-DispatcherJob $ghcr (Get-GraphConfig "dispatcher") (Get-ServiceBusConfig "dispatcher")
+  # A full `up` keeps the sensor's identity, role and workspace id (DL-301).
+  Enable-ContainerSensor | Out-Null

   if ($script:Failures.Count -gt 0) {
     Write-Host "`nDeploy FAILED for $($script:Failures.Count) target(s):" -ForegroundColor Red
@@ -934,5 +974,6 @@ switch ($Action) {
   'up' { Up }
   'postgres-flip' { Flip-PostgresRoles }
   'servicebus-flip' { Flip-ServiceBusSas }
+  'sensor' { if (-not (Enable-ContainerSensor)) { throw "container sensor not enabled" } }
   'down' { Down }
 }
```

### 9. The law book — `orchestration/laws/dispatcher/laws.md`, v1.2 to v1.3

`orchestration/laws/dispatcher/laws.md` — diff against `main`:

```diff
diff --git a/orchestration/laws/dispatcher/laws.md b/orchestration/laws/dispatcher/laws.md
index f13b552e..81e697e4 100644
--- a/orchestration/laws/dispatcher/laws.md
+++ b/orchestration/laws/dispatcher/laws.md
@@ -1,9 +1,10 @@
 # `Dispatcher` — Laws

-**Prefix:** `DSP` · **status:** LOCKED v1.2 · **Owner:** Yury Gurevich
+**Prefix:** `DSP` · **status:** LOCKED v1.3 · **Owner:** Yury Gurevich

 > Decide whether the scheduled daily graph-pull run is placed, skipped, held, or placed in degraded posture,
-> and brief the operator once on each run it placed.
+> brief the operator once on each run it placed, and tell the operator when a container of the
+> fleet fails to start, crashes or is killed, and why.

 Each clause below has a stable ID (`DSP-CAT-NN`). IDs are append-only (conventions §2). A clause is
 green only when a functional test cites its ID (conventions §3). Tests + status live in
@@ -20,12 +21,17 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   owns or rewrites them.
 - **DSP-IDN-03** — `orchestration.dispatcher.Dispatcher` is outside this book: it is the older
   event-driven wrapper that publishes `run.trigger` once invoked and records the final snapshot. This
-  book governs `scheduled_dispatch*.py`, readiness gating, hold answers, notices, and the daily brief
-  (`orchestration/daily_brief*.py`, `DSP-IDN-04`). *(DRIFT-077.)*
+  book governs `scheduled_dispatch*.py`, readiness gating, hold answers, notices, the daily brief
+  (`orchestration/daily_brief*.py`, `DSP-IDN-04`) and the container sensor
+  (`orchestration/container_*.py`, `DSP-IDN-05`). *(DRIFT-077.)*
 - **DSP-IDN-04** — The scheduled dispatcher sends one daily brief per scheduled run it placed
   (`orchestration/daily_brief*.py`): a plain-text report to the operator of what the run did. It
   reports and never decides: no brief changes a placement, a hold, a notice, or any fact another
   component owns.
+- **DSP-IDN-05** — The scheduled dispatcher runs the container sensor (`orchestration/container_*.py`,
+  DL-301): on each fire it reads the platform's container events from the log workspace, records the
+  ones it keeps and tells the operator of each alarm once. It reports and never decides: no sensor read
+  changes a placement, a hold, a notice, the brief's other lines, or any container.

 ## Inputs (`IN`)

@@ -39,6 +45,14 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   run. A failed check degrades only when every failure belongs to a pack-declared degradable agent.
 - **DSP-IN-04** — Human answers are only `run_now` or `skip_today`, scoped to the matching scheduled
   `run_id`. Free text, stale run ids, and malformed answer payloads cannot decide today's placement.
+- **DSP-IN-05** — The sensor's input is the rows of the workspace's `ContainerAppSystemLogs_CL` that
+  reached it inside the read window, read by their ingestion time, and for an alarm's why the stderr
+  lines of `ContainerAppConsoleLogs_CL` of the same replica. A row is an alarm (a failed start or a
+  failed scale-up, a revision that failed to provision, a scale rule the scaler refused, a memory kill,
+  an exit with code 137, any other exit whose code is not 0 or cannot be read, any other row the
+  platform marks `error`), a report (a preemption, or a node scale-down that moved a replica), or
+  nothing; an exit with code 0 is nothing. The app is the row's app or job name, else its revision's
+  name less the revision suffix, else `unknown`.

 ## Triggers (`TRG`)

@@ -52,6 +66,12 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   for a past session briefs nothing. It sends once the run's `Snapshot` exists. On the day's last fire
   (`LAST_FIRE=23:50 UTC`, the cron's last tick) a placed run with no `Snapshot` gets one RED brief
   instead. A skipped run, or a held run with no `RunRequest`, gets no brief.
+- **DSP-TRG-04** — Every fire runs the sensor once, after its dispatch, whatever the dispatch's
+  outcome: placed, skipped, held, or failed. With no `LOG_ANALYTICS_WORKSPACE_ID` in the job's
+  environment the sensor does nothing and the fire's output is unchanged. A read ends at the fire's
+  time and starts `container_sensor_overlap_minutes` before the previous successful read ended; the
+  first read starts `container_sensor_first_read_hours` back, and no read starts further back than
+  `container_sensor_max_lookback_hours`.

 ## Outputs (`OUT`)

@@ -73,12 +93,31 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   out; and the open incidents and critical flags the supervisor's health derives. Every figure is read
   as stored, never recomputed. A RED brief says the run did not finish, names the last stage that
   finished, and carries the run's orders and the same needs-you counts.
+- **DSP-OUT-07** — A sensor read writes one `ContainerEvent` for each new row it keeps (app, revision,
+  replica, kind, whether it is an alarm, the platform's reason and message, the exit code when there is
+  one, the repeat count, when it happened, the why line for an alarm, the read that found it) and one
+  `ContainerSensorRead` (its window; the rows it read; what it recorded, its alarms and reports; how
+  many it told, and its message id or why the message was not sent; whether the look-back cap or the
+  row limit cut it). When alarms are untold it sends one plain-text message for all of them, one line
+  per kind of failure (a kind and an exit code) across apps (DL-301 D5): first how many apps and how
+  many kinds; then each kind, newest first, with its apps (four named, the rest counted), its repeat
+  count when above one (each replica's highest count, summed), its latest time in the operator's zone
+  with UTC beside it (UTC alone when the zone cannot be read), and under it the why line of its latest
+  alarm that has one, naming that alarm's app; at most `container_sensor_alarm_groups_max` kinds, the
+  remaining kinds counted; and a note when the cap cut the read.
+- **DSP-OUT-08** — From the sensor's first read on, every brief carries one container line before
+  needs-you: that the sensor's latest read failed and why; or that it has not read in 24 hours; or that
+  it recorded no alarm in 24 hours; or how many alarms it recorded in 24 hours, repeats counted as in
+  `DSP-OUT-07`, naming at most three kinds of failure with their apps and counting the rest. Before the
+  first read the brief carries no such line.

 ## Prohibitions (`NEV`)

 - **DSP-NEV-01** — The scheduled dispatcher never writes master-owned `FleetPreflight` evidence.
 - **DSP-NEV-02** — The scheduled dispatcher never talks to the broker, never chooses tickers beyond
   the configured universe membership, and never decides what to buy, sell, size, or veto.
+- **DSP-NEV-03** — The sensor never acts on a container: it starts, stops, scales, restarts and
+  reconfigures nothing, and calls no management API. It reads the log workspace and tells.

 ## State & effects (`STA`)

@@ -97,6 +136,11 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   carries no `brief_sent_at`; a successful send writes `brief_sent_at`, `brief_message_id`, and
   `brief_verdict` (the verdict the brief carried, `NOT_FINISHED` for a RED brief) on that
   `RunRequest`. A failed send writes nothing, so a later fire retries.
+- **DSP-IDM-04** — A row read twice is recorded once: a `ContainerEvent`'s key is a digest of the row's
+  own fields. Each alarm is told by one message: a sent message adds a `TOLD` edge from its
+  `ContainerSensorRead` to every alarm it told. An alarm whose message was not sent stays untold and
+  is told by a later fire's message, while it was recorded less than
+  `container_sensor_max_lookback_hours` before that fire.

 ## Ordering & concurrency (`ORD`)

@@ -114,6 +158,14 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 - **DSP-FAIL-03** — Composing or sending a brief can fail only into a fault: an exception, a send the
   port reports failed, or a brief module the image lacks becomes one `Fault`, and the fire goes on. A
   brief never changes the placement outcome and never crashes the fire.
+- **DSP-FAIL-04** — The sensor can fail only into its own records and its own line. Once the graph is
+  open, a workspace read that fails, a missing managed identity, a sensor module the image lacks (the
+  script imports only `container_sensor_guard`), or a graph write that fails becomes one `Fault` and a
+  failed `ContainerSensorRead`; a graph that refuses even those gets an error line on stderr. A
+  message the port reports unsent is a `Fault` too. Before the graph is open (no `POSTGRES_DSN`, or
+  settings, a reader or a graph that cannot be built) the sensor prints one error line and records
+  nothing. The fire's placement and its exit code are never changed by the sensor, and a failed read
+  does not move the next read's start.

 ## Type alignment (`TYP`)

@@ -127,6 +179,12 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 - **DSP-SEC-02** — P&L amounts leave the dispatcher only in the daily brief, only to the configured
   operator chat, and only through the injected Telegram port (DL-230). The job's printed output and
   every fault carry no amount: a brief's fault names its step and an error type, never a value.
+- **DSP-SEC-03** — The sensor reads as the job's system-assigned managed identity, which holds the role
+  Log Analytics Reader on the one log workspace and nothing else; no credential for it is stored
+  anywhere. A console line leaves only with credentials in a URL, named secrets, bearer tokens, runs of
+  32 or more token characters and amounts masked, and cut to 160 characters. A printed line, a fault
+  and a read record name a failure by its error type and a status word, never a reply body, a query or
+  a token. Only a replica name that matches the platform's naming rule is put into a query.

 ## Dependencies (`DEP`)

@@ -134,7 +192,8 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   (`DEP-CLOCK`), provider-owned market calendar, configured universe source, and Telegram port for
   optional operator notices, answers, and the daily brief. For the brief its graph reads include the
   run's chain to its `Snapshot`, `Fill`, `Fault` and `Flag` facts with their resolutions, and the
-  pack's acceptance verdict.
+  pack's acceptance verdict. The sensor depends on the job's managed-identity endpoint and the log
+  workspace's query API.

 ## Observability & audit (`OBS`)

@@ -142,6 +201,9 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   reconstructable from graph facts and returned dispatcher results.
 - **DSP-OBS-02** — Human notice deadlines name the operator's Melbourne time first and include the
   UTC deadline as a fallback.
+- **DSP-OBS-03** — Each sensor run prints one line: the rows read, the new events, the alarms and how
+  many were told, or the failure. Every alarm and report the sensor kept, and every read, is
+  reconstructable from `ContainerEvent` and `ContainerSensorRead` facts and their `TOLD` edges.

 ## Performance envelope (`PERF`)

@@ -154,22 +216,30 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 {
   "graph": {
     "operations": ["read", "append_write"],
-    "labels_owned": ["RunHold"],
-    "labels_written": ["RunRequest", "RunHold", "RunHoldAnswer", "Fault"],
+    "labels_owned": ["RunHold", "ContainerEvent", "ContainerSensorRead"],
+    "labels_written": [
+      "RunRequest", "RunHold", "RunHoldAnswer", "Fault", "ContainerEvent", "ContainerSensorRead"
+    ],
     "labels_read": [
       "FleetPreflight", "RunRequest", "RunHold", "RunHoldAnswer", "MarketData", "ScanRun",
       "AnalystRun", "PMRun", "DeliberationRun", "OrderIntent", "ExecutionRun", "MonitorRun",
       "Snapshot", "Fill", "Fault", "FaultResolution", "Flag", "FlagResolution",
-      "BrokerPositionSnapshot"
+      "BrokerPositionSnapshot", "ContainerEvent", "ContainerSensorRead"
     ],
     "access": "bounded dispatcher placement; the brief marks only its own RunRequest"
   },
+  "log_workspace": {
+    "operations": ["query"],
+    "access": "managed identity; Log Analytics Reader on one workspace"
+  },
   "calendar": {
     "operations": ["read_session_status"],
     "source": "provider-owned NYSE calendar"
   },
   "telegram": {
-    "operations": ["send_notice", "poll_answer", "ack_answer", "confirm_offset", "send_brief"],
+    "operations": [
+      "send_notice", "poll_answer", "ack_answer", "confirm_offset", "send_brief", "send_alarm"
+    ],
     "access": "injected port"
   }
 }
@@ -184,6 +254,11 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 | `provider_max_staleness_days` | `7` | `int >= 0 <= 30` | YES | Daily dispatcher accepts a one-week fixture window across weekends. |
 | `pm_starting_cash` | `Decimal("100000.00")` | `Decimal >= 0 <= 1000000000` | YES | Seed paper PM sizing with a deterministic portfolio value. |
 | `preflight_max_age_minutes` | `70` | `int >= 10 <= 240` | YES | Require the latest hourly fleet preflight with ten minutes of scheduling slack before placing a trading run. |
+| `container_sensor_first_read_hours` | `24` | `int >= 1 <= 168` | YES | The first read covers one day: the day's deploys are seen, and a month of old events does not arrive as one alarm. |
+| `container_sensor_max_lookback_hours` | `168` | `int >= 24 <= 720` | YES | A read after a long gap covers at most a week of the workspace's 30 days. |
+| `container_sensor_overlap_minutes` | `10` | `int >= 3 <= 60` | YES | An event reached the workspace up to 2 min 36 s late (measured 2026-10-14); a row read twice is recorded once. |
+| `container_sensor_alarm_groups_max` | `8` | `int >= 1 <= 20` | YES | One alarm message stays readable and inside Telegram's limit; the rest are counted. |
+| `container_sensor_timeout_seconds` | `20.0` | `float >= 1.0 <= 120.0` | YES | A slow workspace read cannot hold the fire. |

 ## Divergence register

@@ -206,3 +281,7 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 - v1.2 — S251 (DL-259, DL-260; DRIFT-077): the purpose line and `DSP-IDN-03`'s scope sentence name the
   daily brief, which `DSP-IDN-04` added in v1.1 without touching either. `DSP-IDN-03` stays ⬜. No
   behaviour change; 32 / 36 unchanged.
+- v1.3 — S275 (DL-301, work-queue 119): the container sensor. New `DSP-IDN-05`, `DSP-IN-05`,
+  `DSP-TRG-04`, `DSP-OUT-07`, `DSP-OUT-08`, `DSP-NEV-03`, `DSP-IDM-04`, `DSP-FAIL-04`, `DSP-SEC-03` and
+  `DSP-OBS-03`; the purpose line, `DSP-IDN-03`'s scope sentence, `DSP-DEP-01`, `CAP` and `PARAM`
+  amended for it.
```

### 10. The two existing test edits

`orchestration/tests/test_dispatcher_capability.py` — diff against `main`:

```diff
diff --git a/orchestration/tests/test_dispatcher_capability.py b/orchestration/tests/test_dispatcher_capability.py
index 5f7acefc..ad1bb75a 100644
--- a/orchestration/tests/test_dispatcher_capability.py
+++ b/orchestration/tests/test_dispatcher_capability.py
@@ -16,6 +16,8 @@ from pathlib import Path
 from typing import TYPE_CHECKING

 from kernel import InMemoryGraphStore
+from orchestration.container_sensor_guard import sense_safely
+from orchestration.tests.container_sensor_helpers import MEASURED, SETTINGS, FakeReader
 from orchestration.tests.daily_brief_fixtures import at, fire, seed_run
 from orchestration.tests.daily_brief_scenarios import seed_pair
 from orchestration.tests.scheduled_dispatch_human_helpers import (
@@ -100,6 +102,7 @@ def _operations(telegram: FakeTelegram) -> set[str]:
         "ack_answer": bool(telegram.acknowledgements),
         "confirm_offset": bool(telegram.confirmations),
         "send_brief": bool(telegram.briefs),
+        "send_alarm": bool(telegram.alarms),
     }
     return {name for name, seen in used.items() if seen}

@@ -132,7 +135,12 @@ def test_every_fire_stays_inside_the_declared_capability() -> None:
         graph.recording = True
         fire(graph, port, now)
         operations |= _operations(port)
-    graphs = (finished, red, held, degraded, failed)
+    sensed = _Recording()  # S275: the container sensor runs on every fire
+    sensed.recording = True
+    reader = FakeReader([MEASURED["killed"]])
+    sense_safely(sensed, reader, telegram, now=at(22, 50), settings=SETTINGS)
+    operations |= _operations(telegram)
+    graphs = (finished, red, held, degraded, failed, sensed)
     cap = _declared()

     written = {label for graph in graphs for label in graph.written}
```

`orchestration/tests/scheduled_dispatch_human_helpers.py` — diff against `main`:

```diff
diff --git a/orchestration/tests/scheduled_dispatch_human_helpers.py b/orchestration/tests/scheduled_dispatch_human_helpers.py
index 850beb29..a799ce29 100644
--- a/orchestration/tests/scheduled_dispatch_human_helpers.py
+++ b/orchestration/tests/scheduled_dispatch_human_helpers.py
@@ -41,6 +41,8 @@ class FakeTelegram:
     acknowledgements: list[tuple[str, str]] = field(default_factory=list)
     confirmations: list[int] = field(default_factory=list)
     polls: int = 0
+    alarms: list[str] = field(default_factory=list)
+    last_error: str = ""

     def send_hold_notice(
         self, *, run_id: str, failures: tuple[str, ...], act_by: str
@@ -68,6 +70,10 @@ class FakeTelegram:
             return None
         return 100 + len(self.briefs)

+    def send_alarm(self, *, text: str) -> int | None:
+        self.alarms.append(text)
+        return 200 + len(self.alarms)
+
     def poll_answers(self) -> tuple[TelegramAnswer, ...]:
         self._raise_if_needed()
         self.polls += 1
```

---

## Planner's review at the merge — 2026-10-14

Re-measured by the planner on the builder's commit `2ded9672` and on the merged commit `82909a54`.
Nothing here is taken from the handback.

- **Two stops during the build, both the planner's misses, both corrected before the code was
  written or changed** ([DL-301](../design-log.md) amendments 1 and 2). DRIFT-114: § 9's
  `DSP-OUT-07` asked for one message line per app where § 7 and D5 group by kind across apps; the
  clause moved to the code, and a read-back of every new clause against § 1 to § 8 mended four
  more. DRIFT-115: § 6's guard recorded its `Fault` inside an `except` block, so the handled
  error's text reached the stored traceback; the guard now records after the handler, and the
  planner's test reads every stored property.
- **The 20 production files are the corrected prototype byte for byte** (`prototype_blobs.txt`,
  guard `448b9402`). Against the spec's commit the branch changes the files the spec names, the
  version pair, the builder's 14 test files and two helpers, and no other existing test than
  the two § 10 names.
- **The planner's own tests** (98, with `tests/test_dispatch_scheduled_run.py`) pass on the built
  code, run in a separate tree because one helper shares a name with the builder's. They are not
  committed.
- **Guards.** The planner's 38 breaks, one at a time, judged by the builder's 14 test files and
  `tests/test_dispatch_scheduled_run.py`: **38 red**, the tree clean afterwards. B38 (the record
  back inside the handler) went red on the builder's A24.
- **One planner change on the branch, `82909a54`.** CodeQL read two of the builder's asserts in
  `orchestration/tests/test_container_env.py` as `py/side-effect-in-assert` at **error** level
  (each held a factory that appends); the sensor is now called before the assert. After it: 133
  open alerts on the branch, **0 errors**; against the S274 branch (130, 0 errors) the only new
  ones are three notes, the `...` bodies of two Protocols, a pattern 16 existing notes share.
- **`make ci` on Windows, the planner's, on `82909a54`:** exit 0 in one run, all 16 steps, 4,961
  passed, 9 skipped, 100.00 %, the dependency audit clean (the builder's sandbox could not reach
  the index for it). **Gate:** `GATE PROVEN` for `82909a54`, run from `../ta-s275`, whose `HEAD`
  it is; `main` was fast-forwarded to that commit, so the proven commit is the merged one.
- **Law rows.** Dispatcher v1.3, 42 / 46, in `docs/laws/INDEX.md` and `docs/laws/ledger.md`;
  every limb of the five corrected clauses has a cited test (the failure before the graph opens
  and an untold alarm's age among them).
- **F1, at no cost, on the merged commit: passed.** From `../ta-s275` (no `.env`), the merged
  sensor read the live workspace as the planner's own login into an in-memory graph, its port a
  printer. At 2026-09-25 01:00 UTC: 491 rows, 488 alarms and 3 reports, a why for 193, one
  message of four kind lines naming 16 apps (723 characters: the 701 of DL-301's replay plus
  `(provider)` in its two why lines). At 2026-09-29 00:00 UTC: the four lines DL-301 recorded,
  byte for byte, the master's refusal as the why.
- **Not deployed.** The sensor ships in the dispatcher job's image and needs the job's identity
  and role: the retag (`/deploy-fleet`) and then `pwsh infra/deploy-agents.ps1 sensor` are the
  operator's call. Either order is safe. F2 is owed at the first weekday fire after both.

Evidence outside the repo: OneDrive `trading-agents-data/wq119-2026-10-14/`
(`breaks_on_built_2ded9672.txt`, `planner_tests_on_built_2ded9672.txt`, `codeql_s275_branch.tsv`,
`s275-make-ci.txt`, `s275-gate-ran.txt`, `f1_replay_2026-09-25T01_82909a54.txt`,
`f1_replay_2026-09-29T00_82909a54.txt`, `s275_review_assert_fix.py`, `s275_merge_docs.py`; the two
stops: `codex_stop_drift115/`, `s275_drift114_*.py`, `s275_drift115_*.py`).
