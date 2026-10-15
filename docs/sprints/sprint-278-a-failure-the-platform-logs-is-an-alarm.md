<!-- Agent: planning | Role: sprint handover -->
# Sprint 278 — a failure the platform logs is an alarm, whoever caused it

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-278-a-failure-the-platform-logs-is-an-alarm`
**Status:** BUILT
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-301](../design-log.md) amendment 7 (measured and decided, planner, 2026-10-15; amendment 6 is the operator's decision) · [work-queue 133](../work-queue.md) · stacked on [S277](sprint-277-a-refused-request-is-answered-by-the-next-llm.md)'s built commit `6a5742c8`

> **Why this bump kind.** A fix: the dispatcher's purpose already says the operator is told when a
> container of the fleet fails, and the sensor S275 built did not hear the platform's own failures
> (a revision update refused, the autoscaler refused or unable to reach its server). No new capability.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `orchestration/laws/dispatcher/laws.md` | The dispatcher's **locked constitution**, which governs the container sensor (`DSP-IDN-05`) | **LOCKED. Read-only during a build**, except the one amendment the Appendix gives exactly |
| `orchestration/laws/dispatcher/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it; you widen two rows (Steps) |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`DSP-IN-05`**, **`DSP-OUT-07`**, **`DSP-IDM-04`**, **`DSP-FAIL-04`**, **`DSP-NEV-03`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the dispatcher's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **The law-cycle question is answered below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes, one amended clause, no new clause, no `contracts/` change.** `DSP-IN-05` lists what a row is;
it gains the platform's own failures, the five measured by-products that are nothing, and the
platform's words as the why of a platform failure. The amended text is in Appendix section 2, exactly.
The law goes v1.5 → v1.6 (S277 made it v1.5; this branch is stacked on S277). The count stays
**43 / 47**: let the gate derive it.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/container_events.py` | dispatcher `laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `DSP-IN-05` what a row is; `DSP-IDM-04` a row read twice is recorded once (the key) |
| `orchestration/container_queries.py` | same | `DSP-IN-05` the rows read; `DSP-SEC-03` only instants and replica names enter a query |
| `orchestration/container_lines.py`, `container_sensor.py` | same | `DSP-IN-05` the why; `DSP-OUT-07` the why line under each kind |
| `orchestration/container_alarm_text.py` | same | `DSP-OUT-07` one line per kind, in the operator's words; `DSP-OUT-08` the brief's line |
| `orchestration/tests/test_container_platform.py` (new) | conventions §3 | every test cites its clause |

⚠️ **The sensor never changes a fire and never acts on a container (`DSP-FAIL-04`, `DSP-NEV-03`).**
Nothing here touches `container_sensor_guard.py`, the dispatch, or any container. If your change would,
stop and report.

---

## Goal

At merge, a row of the workspace's `ContainerAppSystemLogs_CL` that the platform marks `Warning` or
`error` is an alarm, except five measured by-products of a deploy or a wake, which are nothing.
`RevisionFailure` is `revision-failed` (*revision update failed*); `FailedGetScale` and
`FailedUpdateStatus` are `autoscaler-failed` (*the platform's autoscaler failed*), unless the message
ends ` not found`; any other `Warning` is `platform-warning` (*platform warning*). With no console
line, a platform failure's why is the platform's own reason and message, masked and cut like a
console line. Replayed over the workspace's 30 days, the result is the same as today's for the first
four weeks. The last week gains 41 events, each with its why.

## Why (context)

On 2026-10-14 between 09:05 and 11:02 UTC, the workspace logged 25 `RevisionFailure` rows on 14 apps,
plus the autoscaler's `FailedGetScale` and `FailedUpdateStatus`. The sensor heard none of them, so the
night's brief said *no alarm* ([DL-301](../design-log.md) amendment 5). The operator, 2026-10-15: *"the
failure is a failure regardless"* (amendment 6). Measuring for this spec found a second burst the
same day, 2026-10-15 05:04 UTC (4 rows on 2 apps), also unheard. S275's sensor reads an allow list
of reasons. A failure reason the platform has not used before is silent by construction.

### Measured, 2026-10-15 — read these before designing

All read as the planner from the live workspace, at no cost. Queries and outputs are in OneDrive
`trading-agents-data/wq133-2026-10-15/` (`warn_inventory`, `near_deploy`, `transient`,
`unhealthy_phase`, `autoscaler_rows`, each `.kql` and `.json`).

| Claim | Value | How it was measured |
| --- | --- | --- |
| Reasons marked `Warning` or `error` in 30 days | 14; every failure row is marked `Warning` (its `Type_s`), its `Level` is `info` | *[measured 2026-10-15]* `warn_inventory.kql` |
| `ScaledObjectCheckFailed` / `ScaledObjectDeleted` near a revision change on the same app (−30 to +5 min) | 1,961 of 1,961 / 988 of 988 | *[measured]* `near_deploy.kql` |
| `AssigningReplicaFailed` replicas later assigned | 217 of 217, longest wait 164 s (835 rows) | *[measured]* `transient.kql` |
| `ReplicaUnhealthy` | the master only, 897 rows: 855 within 157 s of the replica's start, 41 within 3 min of its stop, 1 mid-life (2026-09-16, 328 s after start) | *[measured]* `unhealthy_phase.kql` |
| `Completed` marked `Warning` | 2 rows, `exit code '0'` | *[measured]* `warn_inventory.kql` |
| `RevisionFailure` | 25 rows, 14 apps, 2026-10-14 09:11 UTC, *failed calling webhook "mapp.kb.io" … no endpoints available* | *[measured]* `warn_inventory.kql` |
| `FailedGetScale` / `FailedUpdateStatus` | 15 / 5 rows: 4 `… not found` (one each on 2026-09-18, 09-28, 10-01, 10-11, a revision a deploy had replaced); the rest *forbidden* or *the server is currently unable to handle the request*, in bursts at 2026-10-14 09:05–09:11 and 2026-10-15 05:04 UTC | *[measured]* `autoscaler_rows.kql` |
| Failure rows naming a replica | 0 of 41, so none has a console line | *[measured]* `autoscaler_rows.json`, the replay |
| The replay, before and after | weeks to 09-22, 09-29, 10-06, 10-13: identical kinds and counts; week to 10-15 07:00 UTC: + 25 `revision-failed`, + 16 `autoscaler-failed`, 41 of 41 with a why, one message of 819 characters | *[measured]* `f0_live_replay.py` on `../ta-s277` and on the prototype, `f0_ta-s277.txt`, `f0_ta-s278-proto.txt` |
| Unknown `Warning` reasons in 30 days | 0, so the catch-all adds no alarm to the past | *[measured]* the replay: no `platform-warning` |
| Graph vocabulary | kinds are values, not declared; `Type_s` is not stored; no new property | *[measured]* `orchestration/packs/trading_graph_vocabulary.json` read; A27 passes on the prototype |
| A first read after the deploy re-tells the two past bursts | No. Reads continue from the last read with a 10-minute overlap | *[read]* `container_sensor_graph.read_window` |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (A31 to A37 below) in `orchestration/tests/test_container_platform.py`.
2. **Classification** (`container_events.py`): three new kinds, all alarms; `RevisionFailure`,
   `FailedGetScale`, `FailedUpdateStatus` named; an autoscaler row ending ` not found` is nothing; any
   other `Warning` is `platform-warning` unless its reason is one of `BENIGN_WARNINGS`; `Type_s` read,
   not keyed.
3. **The query** (`container_queries.py`): also asks for `Warning` rows whose reason is not benign,
   and projects `Type_s`.
4. **The why** (`container_lines.py`, `container_sensor.py`): `platform_why`, used when no console line
   explains a platform kind.
5. **The words** (`container_alarm_text.py`): one phrase per new kind.
6. **The law**: `DSP-IN-05` as given, v1.6; the test-plan rows; the rollups.

### Out of scope (do NOT build this sprint)

- **No change to the message's shape, grouping, limits or the brief's line.** A burst is already one
  line per kind (DL-301 amendment 7, decision 5).
- **No alarm for a master that turns unready in mid-life.** It happened once in 30 days, and the
  fleet check sees a master that does not answer (named, not decided).
- **No tunable, env key, vocabulary or pack change.** The benign list is measured fact, not a setting.
- **No change to `container_sensor_guard.py`, `container_sensor_graph.py`, `container_logs.py`,
  `container_brief.py`, the Dockerfile or `infra/`.**
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Add the three reasons to the allow list and stop.** Rejected: the next failure reason the platform
  has not used before is silent again, against the operator's *regardless*.
- **Every `Warning` an alarm.** Rejected: the five by-products alone are 4,683 rows in 30 days, nearly
  all from deploys and the nightly wake. A channel that cries at every deploy is learned to be ignored.
- **Excuse rows that fall near a deploy.** Rejected: the sensor reads rows, not deploys. A row-local
  rule (the reason, the message's ending) needs no second query.
- **A longer why for platform text.** Rejected: the graph keeps the whole 300 characters on the
  `ContainerEvent`. The message keeps one line limit.
- **Fold the autoscaler into `scaler-failed`.** Rejected: that kind is a scale rule of ours the scaler
  refused. The autoscaler's failures are the platform's, and the operator should see whose failure it is.

---

## The design decisions — made, and recorded in DL-301 amendment 7

1. `RevisionFailure` → `revision-failed`; `FailedGetScale`, `FailedUpdateStatus` → `autoscaler-failed`.
2. Any other `Warning` → `platform-warning`, except the five in `BENIGN_WARNINGS`.
3. An autoscaler row whose message ends ` not found` → nothing.
4. A platform kind's why, with no console line, is `safe_line(f"{reason}: {message}")`.
5. No new grouping: the burst is one line of its kind.
6. `Type_s` is projected and read, never part of `event_key`, so no row is recorded twice across the
   deploy's overlap (`DSP-IDM-04`).
7. PATCH.
8. Stacked on S277 (`6a5742c8`); merged after S277.

---

## Blast radius — measured 2026-10-15

| What | Detail |
| --- | --- |
| Files changed | `orchestration/container_events.py` 155 → **181**, `container_queries.py` 91 → **93**, `container_lines.py` 64 → **77**, `container_sensor.py` 179 → **179**, `container_alarm_text.py` 177 → **183**; new `orchestration/tests/test_container_platform.py` (**172** on the prototype); `orchestration/laws/dispatcher/laws.md`, `test-plan.md`; `docs/laws/ledger.md`, `docs/laws/INDEX.md`; `pyproject.toml`, `uv.lock`; this spec and its README row |
| Agents affected | none. Only `orchestration/`, which the dispatcher job runs |
| Contract change? | no |
| Graph vocabulary change? | no. Kinds are values; `Type_s` is not stored |
| New env keys / tunables | none |
| Deploy implication | image-only retag. The job's image copies the nine `container_*` modules by name, and no module is added |
| Rollback | retag back to the tag before (the S277 deploy's, else `s276`). A retag does not undo the `ContainerEvent` nodes written or a message sent |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. The design decisions are recorded (DL-301 amendment 7). Do not edit `docs/design-log.md`.
3. **Write the tests A31 to A37** under the names below and run them on the unchanged tree. Paste the
   red output.
4. **Apply Appendix section 1** (production) exactly.
5. **Apply Appendix section 2** (`laws.md`) exactly. Then in `test-plan.md` set the header to v1.6,
   put section 2's `DSP-IN-05` text in its row's description, add A31 to A36 to the `DSP-IN-05` row's tests, and
   add A36 and A37 to the `DSP-OUT-07` row's. Set the dispatcher rows of `docs/laws/ledger.md` and
   `docs/laws/INDEX.md` to v1.6 with a note naming S278 and DL-301 amendment 7, and the count the gate derives
   (43 / 47 on the prototype).
6. **Plant the breaks B01 to B22** (Traps) one at a time; each must turn at least one of your tests
   red; restore each before the next.
7. **Bump** PATCH: `0.128.00` → `0.128.01`; `uv lock --offline`; stage `uv.lock`.
8. **`make ci`**, redirected to a file. Read the file.
9. **Fill the handback sections**; set Status to `BUILT` here and in this sprint's
   `docs/sprints/README.md` row.

---

## Test plan

All in the new file `orchestration/tests/test_container_platform.py`, under exactly these names (the
planner judges the breaks by them). Build platform rows with `container_sensor_helpers.row(...)` plus
`Type_s="Warning"` and `Level="info"`, as the measured rows are.

| # | Test (exact name) | Plants | Must prove |
| --- | --- | --- | --- |
| A31 | 🎯 `test_a31_platform_failures_alarm` | `RevisionFailure` (the webhook message), `FailedGetScale` *forbidden*, `FailedUpdateStatus` *unable to handle the request*, and a `FailedGetScale` row with no `Type_s` | kinds `revision-failed`, `autoscaler-failed` ×3, each an alarm (`DSP-IN-05`) |
| A32 | `test_a32_revision_gone_is_nothing` | `FailedGetScale` and `FailedUpdateStatus` ending ` not found`; the same with text after it; a `RevisionFailure` ending ` not found` | the first nothing; the second and third alarms (`DSP-IN-05`) |
| A33 | 🪤 `test_a33_measured_warnings_are_nothing` | each of the **five measured reasons written out literally** (`AssigningReplicaFailed`, `Completed`, `ReplicaUnhealthy`, `ScaledObjectCheckFailed`, `ScaledObjectDeleted`), marked `Warning` | nothing (`DSP-IN-05`) |
| A34 | `test_a34_unknown_warning_alarms_and_unmarked_unknown_does_not` | `FailedMount` marked `Warning`; the same marked `Normal`; unmarked; `ScaleDown` marked `Warning`; `Error` with exit 0 marked `Warning` | `platform-warning` alarm with its reason; nothing; nothing; still `preempted`; nothing (`DSP-IN-05`) |
| A35 | `test_a35_query_asks_for_unknown_warnings_not_measured_ones` | `events_query` | holds `or (Type_s == 'Warning' and Reason_s !in (<the five, literal, in that order>))` and projects `Reason_s, Type_s, Level,`; `event_key` of a row is the same with and without `Type_s` (`DSP-IN-05` / `DSP-IDM-04`) |
| A36 | 🎯 `test_a36_platform_why_is_its_own_words` | `sense_containers` on an in-memory graph: two `RevisionFailure` rows (two apps, different times), one `FailedGetScale` whose message holds `token=abc123`, one ordinary exit with no replica | each platform event's `error_line` is `<Reason>: <message>` masked (`token=***`) and cut to `LINE_LIMIT`; the exit's is empty; the message holds `revision update failed ×2: <apps> · `, `  why (<latest app>): RevisionFailure: …`, `the platform's autoscaler failed: <app> · ` (`DSP-IN-05` / `DSP-OUT-07`) |
| A37 | `test_a37_platform_kinds_in_the_operators_words` | `group_events` of one fact per new kind | `kind_words` gives `revision update failed`, `the platform's autoscaler failed`, `platform warning` (`DSP-OUT-07`) |

---

## Success factors

- [x] A31 to A37 exist under the names above, each citing its clause, red suite before section 1 (six failed; A33 already passed) and all green after.
- [x] Appendix sections 1 and 2 applied exactly: the five production files and `laws.md` equal the
      prototype's blobs (`prototype_blobs.txt`, OneDrive `trading-agents-data/wq133-2026-10-15/`).
- [x] No existing test changed; every existing container test passes.
- [x] B01 to B22 each red against your tests, each restored.
- [x] Every touched module, the new test file included, under 200 lines after `ruff format`.
- [x] Version `0.128.01`, `uv.lock` one line changed.
- [ ] `make ci` exit 0, 100.00 % coverage (the dependency audit may be the only step that cannot reach
      its network; say so if it is).
- [ ] **F1 (the planner's, at review, no cost):** the replay on the built tree equals
      `f0_ta-s278-proto.txt` week for week.
- [ ] **F2 (the planner's, after deploy):** the first weekday fires on the new tag each read
      `outcome: read` with no error line. The first platform failure after that is told by one message
      naming its kind and the platform's why. It is owed until one happens; the replay is the evidence until then.

---

## Traps

🪤 **The helper's `row()` carries no `Type_s`.** Every existing test row is unmarked and so cannot reach
the catch-all. Build platform rows with `Type_s="Warning"` and `Level="info"`. The platform's failure rows
are `info`, not `error`.
🪤 **Do not parametrize over `BENIGN_WARNINGS` or build A35's expected text from it.** A test that reads
the constant cannot see the constant lose a reason (B11). Write the five out.
🪤 **`event_key` must not read `Type_s`** (B13). An event read before the deploy and again in the
next read's ten-minute overlap would be recorded and told twice.
🪤 **The why is cut at 160 characters with `…`.** Compare its start, its length, or an exact masked
short message. Never compare the whole long webhook text.
🪤 **Two rows at one instant leave the "latest why" to graph order.** Give the rows different `time_t`.
🪤 **`ruff` flags a literal `×` (RUF001).** Use `TIMES` from `container_alarm_text`.
🪤 **The base is S277's commit, not `main`.** The dispatcher law is at v1.5 here and the version is
`0.128.00`; S277's files are not yours to touch.
🪤 **`ruff format` grows test files.** Measure sizes after formatting.

**Breaks — plant one at a time against your tests, restore each:**

| # | File | Plant |
| --- | --- | --- |
| B01 | `container_events.py` | delete the `"RevisionFailure": REVISION_FAILED,` line |
| B02 | `container_events.py` | delete the `"FailedUpdateStatus": AUTOSCALER_FAILED,` line |
| B03 | `container_events.py` | `"FailedGetScale": AUTOSCALER_FAILED` → `SCALER_FAILED` |
| B04 | `container_events.py` | delete `REVISION_FAILED,` from `ALARM_KINDS` |
| B05 | `container_events.py` | delete `PLATFORM_WARNING,` from `ALARM_KINDS` |
| B06 | `container_events.py` | delete the two-line ` not found` rule |
| B07 | `container_events.py` | `message.endswith(_GONE)` → `_GONE in message` |
| B08 | `container_events.py` | the ` not found` rule for every reason (drop `_BY_REASON.get(reason) == AUTOSCALER_FAILED and`) |
| B09 | `container_events.py` | the catch-all's condition → `False` |
| B10 | `container_events.py` | the catch-all without `marked == WARNING and` |
| B11 | `container_events.py` | delete `"ReplicaUnhealthy",` from `BENIGN_WARNINGS` |
| B12 | `container_events.py` | add `"FailedMount",` to `BENIGN_WARNINGS` |
| B13 | `container_events.py` | add `"Type_s",` to `_KEY_FIELDS` after `"Reason_s",` |
| B14 | `container_queries.py` | `Reason_s !in ({benign})` → `Reason_s in ({benign})` |
| B15 | `container_queries.py` | drop `Type_s, ` from the projection |
| B16 | `container_sensor.py` | drop ` or platform_why(event)` |
| B17 | `container_lines.py` | drop the `PLATFORM_KINDS` check in `platform_why` |
| B18 | `container_lines.py` | return the text without `safe_line` |
| B19 | `container_lines.py` | `safe_line(event.message)` (the reason lost) |
| B20 | `container_alarm_text.py` | `"revision update failed"` → `"revision failed"` |
| B21 | `container_alarm_text.py` | `"the platform's autoscaler failed"` → `"autoscaler failed"` |
| B22 | `container_alarm_text.py` | delete the `PLATFORM_WARNING` words line |

On the prototype, all 22 went red against the planner's own tests (`s278_breaks_on_prototype.txt`).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Sizes after the change: `container_events.py` **181**, `container_alarm_text.py` **183**,
  `container_sensor.py` **179**. Section 1 already places them; add nothing to them.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — the five benign reasons are measured facts named in a constant with its date.
- Faults, not silent failure. Nothing here changes the sensor's fault boundary.
- `make ci` **every step** green, **100.00 % coverage floor**, redirected to a file, never piped.
- Version bump PATCH, `uv.lock` staged with it.
- A worktree has **no `.env`**. State which tree you ran in.

---

## Sequencing after merge (the planner's)

1. S277 merges first (after S276's F2). If S277 changes at its merge, rebase this branch on it and re-gate.
2. Review: blobs against `prototype_blobs.txt`; the planner's tests (`planner_test_container_platform.py`)
   beside the builder's; `s278_breaks.py` against the builder's tests alone; CodeQL set-diff against
   the S277 branch; F1.
3. `make gate-ran` from `../ta-s278`, the SHA checked against `git rev-parse HEAD`; merge, fast-forward.
4. Deploy with the next retag (image-only); record the rollback tag; F2.

---

## Handover — paste this to Codex

```text
You are building Sprint 278 in the worktree ../ta-s278, on the branch
sprint-278-a-failure-the-platform-logs-is-an-alarm. Never work on main. The branch is stacked on
Sprint 277's built commit (6a5742c8): do not touch S277's files. The worktree and its venv are ready;
never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-278-a-failure-the-platform-logs-is-an-alarm.md, whole, before anything
else. It is the spec, and its bottom sections are your handback. The Appendix holds the production
code and the law text, which you apply exactly. Your work is the tests, the law rows, the bump and
the evidence.

In order:
1. Read orchestration/laws/dispatcher/laws.md and test-plan.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any code.
2. Write the tests A31 to A37 in the new file orchestration/tests/test_container_platform.py, under
   the exact names in the Test plan, each docstring citing its clause. Run them on the unchanged tree
   and paste the red output into the Closeout.
3. Apply Appendix section 1 exactly (five files under orchestration/). Change nothing else in
   production code.
4. Apply Appendix section 2 to orchestration/laws/dispatcher/laws.md exactly. Then in test-plan.md:
   header v1.6, the DSP-IN-05 row's description to the new clause text, A31 to A36 added to the
   DSP-IN-05 row, A36 and A37 added to the DSP-OUT-07 row. Set the dispatcher rows of
   docs/laws/ledger.md and docs/laws/INDEX.md to v1.6, naming S278 and DL-301 amendment 7, with the
   count the law gate derives (43 / 47 on the prototype).
5. Plant the breaks B01 to B22 (Traps) one at a time; each must turn at least one of your tests red;
   restore each before the next. Record each in the Closeout.
6. Bump the version PATCH (0.128.00 -> 0.128.01) in pyproject.toml, run uv lock --offline, stage
   uv.lock. Run make ci redirected to a file and read the file. If the dependency audit is the only
   step that fails for want of network, say so; the planner runs it.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: run infra/ scripts, pwsh or any az command; reach the network; change contracts/, any pack
file, container_sensor_guard.py, container_sensor_graph.py, container_logs.py, container_brief.py or
the Dockerfile; add or reword a law clause beyond section 2; change any existing test; use noqa; let
any module, test files included, reach 200 lines; measure make ci through a pipe.

Traps (the spec's Traps section has them all): the helper's row() has no Type_s, so mark platform
rows Type_s="Warning", Level="info"; never parametrize over BENIGN_WARNINGS or build A35's expected
text from it, write the five out; event_key must not read Type_s; the why is cut at 160 characters;
give rows that compete for the latest why different time_t; use TIMES, not a literal x-sign; ruff
format grows test files, measure after formatting.

Two tiers when something does not fit. A wrong command, count, path or line number whose intent is
plain: correct it, record it in Return notes, and carry on. A law that contradicts the spec, an
existing test failing, or a measurement in the spec that does not reproduce: STOP and report. State
anything not done as "not done" or "verified failing". Never write a Result for work you have not done.
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
| Classification and row identity (`container_events.py`) | `orchestration/laws/dispatcher/laws.md` and `test-plan.md` (whole); `docs/laws/conventions.md` and `drift-register.md` (whole), read 2026-10-15 before code | `DSP-IDN-05`, `DSP-IN-05`, `DSP-IDM-04` | Yes: platform fixtures must carry `Type_s="Warning"`, `Level="info"`; identity must ignore `Type_s`. Apply only the authorized Appendix amendment. |
| Query (`container_queries.py`) | Same four files, whole | `DSP-IN-05`, `DSP-SEC-03` | Keep expectations literal for the five measured exclusions and the projected marker. |
| Why and operator words (`container_lines.py`, `container_sensor.py`, `container_alarm_text.py`) | Same four files, whole | `DSP-IN-05`, `DSP-OUT-07`, `DSP-OUT-08`, `DSP-SEC-03`, `DSP-FAIL-04`, `DSP-NEV-03` | Prove stored masked/cut why and cross-app wording with different event times; preserve the exact Appendix and sensor boundaries. |
| New tests and law rollups | Same four files, whole; repository `CLAUDE.md` and documentation indexes | conventions §§3, 4, 7, 7a; `DSP-IN-05`, `DSP-IDM-04`, `DSP-OUT-07` | Cite each governing clause; derive the count from the gate. No existing test changes. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** Yes: one existing guarantee is widened by the exact `DSP-IN-05` amendment in Appendix section 2, v1.5 → v1.6; no new clause and no `contracts/` change. Decisions are already recorded in DL-301 amendment 7. Worktree `C:\Users\yury_\Downloads\project\ta-s278`, branch `sprint-278-a-failure-the-platform-logs-is-an-alarm`, clean starting HEAD `13ecb63674e3843597de14241656dcde431e57a9`, with S277 built commit `6a5742c8` an ancestor. This record precedes code changes.

**Contradictions found between a law and this spec:** None. The old input clause is intentionally widened only as authorized by Appendix section 2. DRIFT-114 and DRIFT-115 are already corrected; their boundaries remain unchanged.

**Laws found silent where a decision was needed:** None beyond the amendment already decided in DL-301 amendment 7; no new drift row needed.

**Clauses that were ⬜ and are now proven:** None at this pre-code reading. Binding rows are already 🟩. `DSP-IDN-03`, `DSP-NEV-02`, `DSP-TYP-01`, and `DSP-DEP-01` remain ⬜; their unproven scope is not claimed by this sprint.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A31 | `test_a31_platform_failures_alarm` | `orchestration/tests/test_container_platform.py` | PASS | `DSP-IN-05` |
| A32 | `test_a32_revision_gone_is_nothing` | `orchestration/tests/test_container_platform.py` | PASS | `DSP-IN-05` |
| A33 | `test_a33_measured_warnings_are_nothing` | `orchestration/tests/test_container_platform.py` | PASS | `DSP-IN-05` |
| A34 | `test_a34_unknown_warning_alarms_and_unmarked_unknown_does_not` | `orchestration/tests/test_container_platform.py` | PASS | `DSP-IN-05` |
| A35 | `test_a35_query_asks_for_unknown_warnings_not_measured_ones` | `orchestration/tests/test_container_platform.py` | PASS | `DSP-IN-05 / DSP-IDM-04` |
| A36 | `test_a36_platform_why_is_its_own_words` | `orchestration/tests/test_container_platform.py` | PASS | `DSP-IN-05 / DSP-OUT-07` |
| A37 | `test_a37_platform_kinds_in_the_operators_words` | `orchestration/tests/test_container_platform.py` | PASS | `DSP-OUT-07` |

**Tests added beyond the plan:** None; seven exact planned test functions, with literal cases inside them.

---

## Closeout — evidence

**Status:** BUILT — local implementation and guards proven; overall CI verified failing only at the offline dependency audit. Planner review, remote gates, F1 and F2 not done.

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s278`, branch `sprint-278-a-failure-the-platform-logs-is-an-alarm`; `.env` absent. Prepared worktree venv; `UV_OFFLINE=1`, `UV_NO_SYNC=1`, `PYTHONUTF8=1`. External Python DNS/connect calls blocked by a temporary `sitecustomize.py` outside the worktree; loopback fixtures remain available. No bare `uv sync`.

**Result:** Exact Appendix production and law blobs matched against local prototype commit `f182d2ee`; A31-A37 pass, all 130 container tests pass, and B01-B22 each make a builder test red before restoration. PATCH `0.128.01`; offline lock update changes one package-version line. Full pytest: 5095 passed, 9 skipped, 2470 warnings in 452.26s (0:07:32); coverage 100.00%. Overall `make ci` exit 2: only dependency audit could not obtain fresh external advisory data; its success is not claimed.

**Files changed:**

- `orchestration/container_events.py`
- `orchestration/container_queries.py`
- `orchestration/container_lines.py`
- `orchestration/container_sensor.py`
- `orchestration/container_alarm_text.py`
- `orchestration/tests/test_container_platform.py`
- `orchestration/laws/dispatcher/laws.md`
- `orchestration/laws/dispatcher/test-plan.md`
- `docs/laws/ledger.md`
- `docs/laws/INDEX.md`
- `pyproject.toml`
- `uv.lock`
- `docs/sprints/sprint-278-a-failure-the-platform-logs-is-an-alarm.md`
- `docs/sprints/README.md`

**Design decisions:** recorded as [`DL-301`](../design-log.md) amendment 7 (planner).

**Proof — the red run first:** On unchanged production and law blobs, `uv run --offline --no-sync pytest orchestration/tests/test_container_platform.py --no-cov -q`, exit 1. A33 already passes on the old classifier; the six changed-behavior tests fail.

```text
RED_EXIT=1
FF.FFFF                                                                  [100%]
================================== FAILURES ===================================
______________________ test_a31_platform_failures_alarm _______________________
orchestration\tests\test_container_platform.py:50: in test_a31_platform_failures_alarm
    assert event is not None
E   assert None is not None
______________________ test_a32_revision_gone_is_nothing ______________________
orchestration\tests\test_container_platform.py:59: in test_a32_revision_gone_is_nothing
    assert event is not None
E   assert None is not None
________ test_a34_unknown_warning_alarms_and_unmarked_unknown_does_not ________
orchestration\tests\test_container_platform.py:81: in test_a34_unknown_warning_alarms_and_unmarked_unknown_does_not
    assert event is not None
E   assert None is not None
_________ test_a35_query_asks_for_unknown_warnings_not_measured_ones __________
orchestration\tests\test_container_platform.py:98: in test_a35_query_asks_for_unknown_warnings_not_measured_ones
    assert (
E   assert "or (Type_s == 'Warning' and Reason_s !in ('AssigningReplicaFailed', 'Completed', 'ReplicaUnhealthy', 'ScaledObjectCheckFailed', 'ScaledObjectDeleted'))" in 'ContainerAppSystemLogs_CL\n| where ingestion_time() > datetime(2026-10-14T21:30:00.000000Z) and ingestion_time() <= d..., JobName_s, RevisionName_s, ReplicaName_s, Reason_s, Level, Log_s, Count_d\n| order by TimeGenerated asc\n| take 5000'
___________________ test_a36_platform_why_is_its_own_words ____________________
orchestration\tests\test_container_platform.py:129: in test_a36_platform_why_is_its_own_words
    assert (result.recorded, result.alarms, result.told) == (4, 4, 4)
E   assert (1, 1, 1) == (4, 4, 4)
E
E     At index 0 diff: 1 != 4
E     Use -v to get more diff
_______________ test_a37_platform_kinds_in_the_operators_words ________________
orchestration\tests\test_container_platform.py:158: in test_a37_platform_kinds_in_the_operators_words
    assert kind_words(group) == words
E   AssertionError: assert 'revision-failed' == 'revision update failed'
E
E     - revision update failed
E     ?         ^^^^^^^^
E     + revision-failed
E     ?         ^
=========================== short test summary info ===========================
FAILED orchestration/tests/test_container_platform.py::test_a31_platform_failures_alarm
FAILED orchestration/tests/test_container_platform.py::test_a32_revision_gone_is_nothing
FAILED orchestration/tests/test_container_platform.py::test_a34_unknown_warning_alarms_and_unmarked_unknown_does_not
FAILED orchestration/tests/test_container_platform.py::test_a35_query_asks_for_unknown_warnings_not_measured_ones
FAILED orchestration/tests/test_container_platform.py::test_a36_platform_why_is_its_own_words
FAILED orchestration/tests/test_container_platform.py::test_a37_platform_kinds_in_the_operators_words
6 failed, 1 passed in 3.35s
```

**Proof — the green run:** New suite after the Appendix, followed by all `test_container*.py` under `orchestration/tests/` and `tests/`, each with `uv run --offline --no-sync pytest --no-cov -q` (exit 0). No existing test edited.

```text
.......                                                                  [100%]
7 passed in 1.07s
```

```text
........................................................................ [ 55%]
..........................................................               [100%]
130 passed in 3.77s
```

The two Appendix sections, unchanged after formatting:

```text
APPENDIX_SECTION_1=APPLIED_EXACTLY
orchestration/container_alarm_text.py: 832df2da8a18a0ed9515925b545c8a00f6e0794b MATCH prototype f182d2ee
orchestration/container_events.py: 94bf741ea815deaa0daba4b36a6caabdaec69d9a MATCH prototype f182d2ee
orchestration/container_lines.py: a0d828c6b45c21f00b0639ba00ea1c6ba124b49b MATCH prototype f182d2ee
orchestration/container_queries.py: 6047f95ffa54bac3c73217f9ccde8163c686312d MATCH prototype f182d2ee
orchestration/container_sensor.py: 1e717a54bb2faaef68e1001deb7f1d93a18d9601 MATCH prototype f182d2ee
APPENDIX_SECTION_2=APPLIED_EXACTLY
orchestration/laws/dispatcher/laws.md: 8dedaee706a7a51cd3327067c1cd090a1e6a43ba MATCH prototype f182d2ee
```

Law counter derived by the gate implementation (`_derived_counter`) and full law gate:

```text
DISPATCHER_DERIVED=43/47
LAW_COVERAGE_EXIT=0
```

**Guards planted:** Each exact B01-B22 mutation ran alone against the seven builder tests only (`.venv/Scripts/python.exe -m pytest orchestration/tests/test_container_platform.py --no-cov -q`). Each exit was 1 with an actual test failure, not a collection error. All five production byte sequences checked restored before the next mutation; final restored suite exit 0.

```text
B01: exit 1; RED test_a31_platform_failures_alarm, test_a32_revision_gone_is_nothing, test_a36_platform_why_is_its_own_words; RESTORED
B02: exit 1; RED test_a31_platform_failures_alarm, test_a32_revision_gone_is_nothing; RESTORED
B03: exit 1; RED test_a31_platform_failures_alarm, test_a32_revision_gone_is_nothing, test_a36_platform_why_is_its_own_words; RESTORED
B04: exit 1; RED test_a31_platform_failures_alarm, test_a32_revision_gone_is_nothing, test_a36_platform_why_is_its_own_words; RESTORED
B05: exit 1; RED test_a34_unknown_warning_alarms_and_unmarked_unknown_does_not; RESTORED
B06: exit 1; RED test_a32_revision_gone_is_nothing; RESTORED
B07: exit 1; RED test_a32_revision_gone_is_nothing; RESTORED
B08: exit 1; RED test_a32_revision_gone_is_nothing; RESTORED
B09: exit 1; RED test_a34_unknown_warning_alarms_and_unmarked_unknown_does_not; RESTORED
B10: exit 1; RED test_a34_unknown_warning_alarms_and_unmarked_unknown_does_not; RESTORED
B11: exit 1; RED test_a33_measured_warnings_are_nothing, test_a35_query_asks_for_unknown_warnings_not_measured_ones; RESTORED
B12: exit 1; RED test_a34_unknown_warning_alarms_and_unmarked_unknown_does_not, test_a35_query_asks_for_unknown_warnings_not_measured_ones; RESTORED
B13: exit 1; RED test_a35_query_asks_for_unknown_warnings_not_measured_ones; RESTORED
B14: exit 1; RED test_a35_query_asks_for_unknown_warnings_not_measured_ones; RESTORED
B15: exit 1; RED test_a35_query_asks_for_unknown_warnings_not_measured_ones; RESTORED
B16: exit 1; RED test_a36_platform_why_is_its_own_words; RESTORED
B17: exit 1; RED test_a36_platform_why_is_its_own_words; RESTORED
B18: exit 1; RED test_a36_platform_why_is_its_own_words; RESTORED
B19: exit 1; RED test_a36_platform_why_is_its_own_words; RESTORED
B20: exit 1; RED test_a36_platform_why_is_its_own_words, test_a37_platform_kinds_in_the_operators_words; RESTORED
B21: exit 1; RED test_a36_platform_why_is_its_own_words, test_a37_platform_kinds_in_the_operators_words; RESTORED
B22: exit 1; RED test_a37_platform_kinds_in_the_operators_words; RESTORED
GUARDS_PROVEN=22/22
RESTORED_EXIT=0
.......                                                                  [100%]
7 passed in 0.99s
```

**Module line counts:** After `ruff format` (six files unchanged); all under 200.

```text
orchestration/container_events.py: 181 lines
orchestration/container_queries.py: 93 lines
orchestration/container_lines.py: 77 lines
orchestration/container_sensor.py: 179 lines
orchestration/container_alarm_text.py: 183 lines
orchestration/tests/test_container_platform.py: 158 lines
POST_FORMAT_APPENDIX_BLOBS=MATCH
```

Offline version/lock update (`uv lock --offline`, exit 0; `uv.lock` staged):

```text
Resolved 180 packages in 341ms
Updated trading-agents v0.128.0 -> v0.128.1
```

```text
1	1	uv.lock
```

**`make ci`:** Ran from this worktree as `make ci > $env:TEMP/ta-s278-evidence/ci.txt 2>&1`, captured `$LASTEXITCODE=2`, and read the log. Steps 1-13 passed; step 14 (dependency audit) is verified failing because fresh PyPI advisory data cannot be fetched offline. The network-dependent advisory refresh is **NOT RUN**; the planner owes it. Make stopped before steps 15-16, so both security steps were run separately and passed. Full raw logs remain outside the repository at `%TEMP%/ta-s278-evidence/`. Command lines, coverage/result, skips and audit failure below are pasted log excerpts; module warnings, per-file test progress and coverage rows omitted.

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
uv run lint-imports
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
uv run python scripts/check_tracker_size.py
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
uv run python scripts/check_dependency_audit.py
TOTAL                                                           21353      0   4568      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_gate_selftest_leaves_nothing.py:57: a link needs a privilege here
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 5095 passed, 9 skipped, 2470 warnings in 452.26s (0:07:32) ==========
dependency audit failed: WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\urllib3\connection.py", line 239, in _new_conn
    sock = connection.create_connection(
        (self._dns_host, self.port),
    ...<2 lines>...
        socket_options=self.socket_options,
    )
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\urllib3\util\connection.py", line 60, in create_connection
    for res in socket.getaddrinfo(host, port, family, socket.SOCK_STREAM):
               ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\AppData\Local\Temp\ta-s278-evidence\sitecustomize.py", line 20, in _resolve
    raise OSError('Sprint 278 offline guard: external DNS blocked')
OSError: Sprint 278 offline guard: external DNS blocked

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\urllib3\connectionpool.py", line 793, in urlopen
    response = self._make_request(
        conn,
    ...<10 lines>...
        **response_kw,
    )
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\urllib3\connectionpool.py", line 494, in _make_request
    raise new_e
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\urllib3\connectionpool.py", line 470, in _make_request
    self._validate_conn(conn)
    ~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\urllib3\connectionpool.py", line 1125, in _validate_conn
    conn.connect()
    ~~~~~~~~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\urllib3\connection.py", line 827, in connect
    self.sock = sock = self._new_conn()
                       ~~~~~~~~~~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\urllib3\connection.py", line 254, in _new_conn
    raise NewConnectionError(
        self, f"Failed to establish a new connection: {e}"
    ) from e
urllib3.exceptions.NewConnectionError: HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: Sprint 278 offline guard: external DNS blocked

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\requests\adapters.py", line 696, in send
    resp = conn.urlopen(
        method=request.method,
    ...<9 lines>...
        chunked=chunked,
    )
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\urllib3\connectionpool.py", line 847, in urlopen
    retries = retries.increment(
        method, url, error=new_e, _pool=self, _stacktrace=sys.exc_info()[2]
    )
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\urllib3\util\retry.py", line 555, in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: Sprint 278 offline guard: external DNS blocked"))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Scripts\pip-audit.exe\__main__.py", line 10, in <module>
    sys.exit(audit())
             ~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\pip_audit\_cli.py", line 554, in audit
    for spec, vulns in auditor.audit(source):
                       ~~~~~~~~~~~~~^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\pip_audit\_audit.py", line 68, in audit
    for dep, vulns in self._service.query_all(specs):
                      ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\pip_audit\_service\interface.py", line 180, in query_all
    yield self.query(spec)
          ~~~~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\pip_audit\_service\pypi.py", line 64, in query
    response: requests.Response = self.session.get(url=url, timeout=self.timeout)
                                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\requests\sessions.py", line 671, in get
    return self.request("GET", url, params=params, **kwargs)
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\requests\sessions.py", line 651, in request
    resp = self.send(prep, **send_kwargs)
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\requests\sessions.py", line 784, in send
    r = adapter.send(request, **kwargs)
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\cachecontrol\adapter.py", line 76, in send
    resp = super().send(request, stream, timeout, verify, cert, proxies)
  File "C:\Users\yury_\Downloads\project\ta-s278\.venv\Lib\site-packages\requests\adapters.py", line 729, in send
    raise ConnectionError(e, request=request)
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: Sprint 278 offline guard: external DNS blocked"))
make: *** [Makefile:60: ci] Error 1
MAKE_CI_EXIT=2
```

Separate final two steps:

```text
Detect secrets...........................................................Passed
DETECT_SECRETS_EXIT=0
detect-secrets (untracked): no untracked files to scan
UNTRACKED_SECRETS_EXIT=0
```

**`make gate-ran`:** *(planner, at review)*

**Not met / verified failing:** Overall `make ci` is verified failing (exit 2); the fresh dependency-advisory refresh is NOT RUN (offline). The nine pytest cases listed above were skipped, so their runtime proof is not done. Planner blob-file comparison with `prototype_blobs.txt`, planner tests/break runner, CodeQL set-diff, F1 replay, `make gate-ran`, push, merge, deploy and F2 are not done. Local full-object comparison to `f182d2ee` proves the six Appendix blobs; it does not substitute for F1/F2.

---

## Return notes

- No scope or implementation pivot: production and law match the authorized prototype exactly. Existing tests, S277 implementation, protected sensor modules, contracts, packs, Dockerfile, infra, `docs/STATE.md`, `docs/design-log.md` and `docs/work-queue.md` are unchanged relative to the starting HEAD.
- Command correction: Windows subprocess text-mode stdin made `git apply --check` reject the diff as corrupt at line 7; `--recount` did not help. Sending the original UTF-8 diff as bytes fixed the transport, without editing hunks or Appendix text. Both sections then applied and all full blob IDs matched.
- A33 already passes on the unchanged classifier, which ignored those reasons. The initial suite is red (six failed, one passed); B11 proves A33 detects a removed benign reason. Seven builder test functions hold their literal cases in 158 lines. The prototype's 172-line file and its test count describe a different test implementation; this run's actual count and nine skips are recorded above.
- Derived dispatcher count reproduces 43 / 47; the amended description is the complete normalized `DSP-IN-05` clause. No gray clause promoted and no new drift discovered.
- Offline `uv lock --offline` succeeded, resolving 180 packages; the lock normalizes the project version to `0.128.1`. Its only changed line is staged with `pyproject.toml`'s `0.128.01` bump.
- Commit-hook correction: the first attempt exited 1 on markdownlint MD012, one extra blank line in the added handback. Removed it; a separate full Markdown lint then passed (exit 0). All other hooks in that attempt passed.
- Build evidence is local. Planner owes the fresh dependency audit, review gates, replay F1 and post-deploy F2. S277 must merge first; any rebase or changed base needs re-gating.

Final documentation and scope checks after setting BUILT (all exit 0):

```text
FINAL_SCOPE=14/14 approved paths; no protected or existing-test edits
SIX_APPENDIX_BLOBS=MATCH
TESTS=7 exact planned functions; clause docstrings; 158 lines
VERSION=0.128.01; uv.lock=one line; SPEC_APPENDIX=UNCHANGED
check_law_coverage.py: exit 0
check_sprint_status.py: exit 0
docs/sprints/sprint-278-a-failure-the-platform-logs-is-an-alarm.md: BUILT | **Status:** BUILT
docs_seen=283 SPEC=10 BUILT=2 MERGED=271 UNMAPPED=0 MISSING=0
check_tracker_size.py: exit 0
check_markdown_links.py: exit 0
check_version_scheme.py: exit 0
MARKDOWN_EXIT=0
markdownlint-cli2........................................................Passed
```

---

## Appendix — the change, measured on the planner's prototype

The prototype is `../ta-s278-proto` at `f182d2ee` (local branch `proto-s278`, not pushed): `make ci`
exit 0, 5,105 passed, 100.00 %; 22 breaks, 22 red. Each section is the diff from `6a5742c8`, applied
with `git apply` or by hand. The result must equal the prototype's blob ids in `prototype_blobs.txt`.

### 1. Production — five files under `orchestration/`

```diff
diff --git a/orchestration/container_alarm_text.py b/orchestration/container_alarm_text.py
index a45c6d7e..832df2da 100644
--- a/orchestration/container_alarm_text.py
+++ b/orchestration/container_alarm_text.py
@@ -16,12 +16,15 @@ from datetime import UTC, datetime
 from typing import TYPE_CHECKING

 from orchestration.container_events import (
+    AUTOSCALER_FAILED,
     EXIT_ERROR,
     KILLED,
     MEMORY_KILL,
     PLATFORM_ERROR,
+    PLATFORM_WARNING,
     PREEMPTED,
     PROVISION_FAILED,
+    REVISION_FAILED,
     SCALER_FAILED,
     START_FAILED,
 )
@@ -39,6 +42,9 @@ _WORDS = {
     KILLED: "killed (exit code 137)",
     PLATFORM_ERROR: "platform error",
     PREEMPTED: "moved off its node by the platform",
+    REVISION_FAILED: "revision update failed",
+    AUTOSCALER_FAILED: "the platform's autoscaler failed",
+    PLATFORM_WARNING: "platform warning",
 }
 _EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
 TIMES = chr(0x00D7)  # the multiplication sign of a repeat count
diff --git a/orchestration/container_events.py b/orchestration/container_events.py
index 16356046..94bf741e 100644
--- a/orchestration/container_events.py
+++ b/orchestration/container_events.py
@@ -4,9 +4,10 @@ Agent: orchestration
 Role: classify Azure Container Apps system-log rows for the container sensor (DL-301).
 External I/O: none.

-A row is one record of the workspace's `ContainerAppSystemLogs_CL`. The kinds are an
-allow list measured on its 30 days (2026-10-14): a reason not named here is ignored,
-except that a row the platform itself marks `error` is always an alarm.
+A row is one record of the workspace's `ContainerAppSystemLogs_CL`. A row the platform
+marks `error` or `Warning` is an alarm unless it is one of the warnings measured as
+a deploy's or a wake's by-product on the workspace's 30 days (2026-10-15, DL-301
+amendment 7); a reason not named here and not so marked is ignored.
 """

 from __future__ import annotations
@@ -27,6 +28,9 @@ KILLED = "killed"
 EXIT_ERROR = "exit-error"
 PLATFORM_ERROR = "platform-error"
 PREEMPTED = "preempted"
+REVISION_FAILED = "revision-failed"
+AUTOSCALER_FAILED = "autoscaler-failed"
+PLATFORM_WARNING = "platform-warning"

 ALARM_KINDS = frozenset(
     {
@@ -37,8 +41,12 @@ ALARM_KINDS = frozenset(
         KILLED,
         EXIT_ERROR,
         PLATFORM_ERROR,
+        REVISION_FAILED,
+        AUTOSCALER_FAILED,
+        PLATFORM_WARNING,
     }
 )
+PLATFORM_KINDS = frozenset({REVISION_FAILED, AUTOSCALER_FAILED, PLATFORM_WARNING})

 EXIT_REASON = "Error"  # the platform's reason for every exit; the code says which
 _BY_REASON = {
@@ -48,8 +56,19 @@ _BY_REASON = {
     "OOMKilled": MEMORY_KILL,
     "Preempted": PREEMPTED,
     "ScaleDown": PREEMPTED,
+    "RevisionFailure": REVISION_FAILED,
+    "FailedGetScale": AUTOSCALER_FAILED,
+    "FailedUpdateStatus": AUTOSCALER_FAILED,
 }
 SENSED_REASONS = (*_BY_REASON, EXIT_REASON)  # the query's filter is built from this
+WARNING = "Warning"
+BENIGN_WARNINGS = (  # each one ends by itself: measured 2026-10-15 (DL-301 amendment 7)
+    "AssigningReplicaFailed",
+    "Completed",
+    "ReplicaUnhealthy",
+    "ScaledObjectCheckFailed",
+    "ScaledObjectDeleted",
+)
 _KEY_FIELDS = (
     "TimeGenerated",
     "time_t",
@@ -65,6 +84,7 @@ _KEY_FIELDS = (
 _EXIT_CODE = re.compile(r"exit code '(-?\d+)'")
 _REVISION_SUFFIX = re.compile(r"--[a-z0-9]+$")
 _PROVISIONING = "Error provisioning revision"
+_GONE = " not found"  # the autoscaler asked for a revision a deploy had just removed
 _KILL_CODE = 137
 MESSAGE_LIMIT = 300

@@ -95,7 +115,7 @@ def classify(row: Mapping[str, object]) -> ContainerEvent | None:
     reason = _text(row, "Reason_s")
     message = _text(row, "Log_s")
     code = _exit_code(message)
-    kind = _kind(reason, _text(row, "Level"), message, code)
+    kind = _kind(reason, _text(row, "Level"), _text(row, "Type_s"), message, code)
     if kind is None:
         return None
     revision = _text(row, "RevisionName_s")
@@ -124,15 +144,21 @@ def event_key(row: Mapping[str, object]) -> str:
     return f"container-event:{hashlib.sha256(joined.encode()).hexdigest()[:32]}"


-def _kind(reason: str, level: str, message: str, code: int | None) -> str | None:
+def _kind(
+    reason: str, level: str, marked: str, message: str, code: int | None
+) -> str | None:
     if reason == EXIT_REASON:
         if code == 0:
             return None
         return KILLED if code == _KILL_CODE else EXIT_ERROR
+    if _BY_REASON.get(reason) == AUTOSCALER_FAILED and message.endswith(_GONE):
+        return None
     if reason in _BY_REASON:
         return _BY_REASON[reason]
     if level.lower() == "error":
         return PROVISION_FAILED if message.startswith(_PROVISIONING) else PLATFORM_ERROR
+    if marked == WARNING and reason not in BENIGN_WARNINGS:
+        return PLATFORM_WARNING
     return None


diff --git a/orchestration/container_lines.py b/orchestration/container_lines.py
index 3ebd2fde..a0d828c6 100644
--- a/orchestration/container_lines.py
+++ b/orchestration/container_lines.py
@@ -7,6 +7,8 @@ External I/O: none.
 Lines of one traceback share a timestamp, so "the last line" is not the error: the
 line is chosen by its shape. A container's closing line naming a failed close comes
 first, then an exception line, then the line saying it was told to stop (DL-297).
+A failure of the platform itself has no replica and so no console: its why is the
+platform's own reason and message (DL-301 amendment 7).
 """

 from __future__ import annotations
@@ -15,10 +17,14 @@ import re
 from datetime import timedelta
 from typing import TYPE_CHECKING

+from orchestration.container_events import PLATFORM_KINDS
+
 if TYPE_CHECKING:
     from collections.abc import Sequence
     from datetime import datetime

+    from orchestration.container_events import ContainerEvent
+
 LINE_WINDOW = timedelta(minutes=15)  # how far before an alarm its line may be
 _LINE_AFTER = timedelta(minutes=1)  # the platform stamps an exit after its last line
 LINE_LIMIT = 160
@@ -53,6 +59,13 @@ def choose_line(lines: Sequence[tuple[datetime, str]], occurred: datetime) -> st
     return ""


+def platform_why(event: ContainerEvent) -> str:
+    """Return the platform's own words for a platform failure, made safe; else ''."""
+    if event.kind not in PLATFORM_KINDS:
+        return ""
+    return safe_line(f"{event.reason}: {event.message}")
+
+
 def safe_line(text: str) -> str:
     """Return one line with credentials, long tokens and amounts masked, and cut."""
     line = " ".join(text.split())
diff --git a/orchestration/container_queries.py b/orchestration/container_queries.py
index f234436d..6047f95f 100644
--- a/orchestration/container_queries.py
+++ b/orchestration/container_queries.py
@@ -15,7 +15,7 @@ import re
 from datetime import UTC
 from typing import TYPE_CHECKING

-from orchestration.container_events import SENSED_REASONS
+from orchestration.container_events import BENIGN_WARNINGS, SENSED_REASONS, WARNING

 if TYPE_CHECKING:
     from collections.abc import Mapping, Sequence
@@ -44,13 +44,15 @@ class ContainerLogReadError(RuntimeError):
 def events_query(start: datetime, until: datetime) -> str:
     """Return the query for the sensed rows ingested after ``start`` up to ``until``."""
     reasons = ", ".join(f"'{reason}'" for reason in SENSED_REASONS)
+    benign = ", ".join(f"'{reason}'" for reason in BENIGN_WARNINGS)
     return (
         "ContainerAppSystemLogs_CL\n"
         f"| where ingestion_time() > {kql_time(start)}"
         f" and ingestion_time() <= {kql_time(until)}\n"
-        f"| where Reason_s in ({reasons}) or Level =~ 'error'\n"
+        f"| where Reason_s in ({reasons}) or Level =~ 'error'"
+        f" or (Type_s == '{WARNING}' and Reason_s !in ({benign}))\n"
         "| project TimeGenerated, time_t, ContainerAppName_s, JobName_s, "
-        "RevisionName_s, ReplicaName_s, Reason_s, Level, Log_s, Count_d\n"
+        "RevisionName_s, ReplicaName_s, Reason_s, Type_s, Level, Log_s, Count_d\n"
         "| order by TimeGenerated asc\n"
         f"| take {EVENT_ROWS_MAX}"
     )
diff --git a/orchestration/container_sensor.py b/orchestration/container_sensor.py
index 4bd28df6..1e717a54 100644
--- a/orchestration/container_sensor.py
+++ b/orchestration/container_sensor.py
@@ -17,7 +17,7 @@ from typing import TYPE_CHECKING, Protocol

 from orchestration.container_alarm_text import alarm_message, group_events
 from orchestration.container_events import ContainerEvent, classify
-from orchestration.container_lines import LINE_WINDOW, choose_line
+from orchestration.container_lines import LINE_WINDOW, choose_line, platform_why
 from orchestration.container_queries import EVENT_ROWS_MAX
 from orchestration.container_sensor_graph import (
     CONTAINER_EVENT,
@@ -151,7 +151,7 @@ def _why(event: ContainerEvent, lines: _Lines) -> str:
     occurred = parse_instant(event.occurred_at)
     if not event.alarm or occurred is None:
         return ""
-    return choose_line(lines.get(event.replica, []), occurred)
+    return choose_line(lines.get(event.replica, []), occurred) or platform_why(event)


 def _tell(
```

### 2. The law — `orchestration/laws/dispatcher/laws.md`, v1.6

```diff
diff --git a/orchestration/laws/dispatcher/laws.md b/orchestration/laws/dispatcher/laws.md
index 108ca89c..8dedaee7 100644
--- a/orchestration/laws/dispatcher/laws.md
+++ b/orchestration/laws/dispatcher/laws.md
@@ -1,6 +1,6 @@
 # `Dispatcher` — Laws

-**Prefix:** `DSP` · **status:** LOCKED v1.5 · **Owner:** Yury Gurevich
+**Prefix:** `DSP` · **status:** LOCKED v1.6 · **Owner:** Yury Gurevich

 > Decide whether the scheduled daily graph-pull run is placed, skipped, held, or placed in degraded posture,
 > brief the operator once on each run it placed, and tell the operator when a container of the
@@ -47,10 +47,15 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   `run_id`. Free text, stale run ids, and malformed answer payloads cannot decide today's placement.
 - **DSP-IN-05** — The sensor's input is the rows of the workspace's `ContainerAppSystemLogs_CL` that
   reached it inside the read window, read by their ingestion time, and for an alarm's why the stderr
-  lines of `ContainerAppConsoleLogs_CL` of the same replica. A row is an alarm (a failed start or a
-  failed scale-up, a revision that failed to provision, a scale rule the scaler refused, a memory kill,
-  an exit with code 137, any other exit whose code is not 0 or cannot be read, any other row the
-  platform marks `error`), a report (a preemption, or a node scale-down that moved a replica), or
+  lines of `ContainerAppConsoleLogs_CL` of the same replica, or, for a failure of the platform itself,
+  the row's own reason and message. A row is an alarm (a failed start or a failed scale-up, a revision
+  that failed to provision, a scale rule the scaler refused, a memory kill, an exit with code 137, any
+  other exit whose code is not 0 or cannot be read, a revision update the platform failed, the
+  platform's autoscaler failing to read or update a scale unless it found the revision gone, any
+  other row the platform marks `error`, and any other row it marks `Warning` except the five each
+  deploy and each wake leave behind: a replica waiting for its node, a probe refused while a replica
+  starts or stops, a scale object checked or removed with its revision, and a completed container),
+  a report (a preemption, or a node scale-down that moved a replica), or
   nothing; an exit with code 0 is nothing. The app is the row's app or job name, else its revision's
   name less the revision suffix, else `unknown`.

@@ -295,3 +300,7 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   `CAP` amended for the `AgentInstance` read.
 - v1.5 — S277 (DL-289 P3, work-queue 123): the brief's LLM line also names a switch during the run,
   read from the run's `DeliberationRun`. `DSP-OUT-09` amended. No clause added.
+- v1.6 — S278 (DL-301 amendment 7, work-queue 133): a failure the platform logs is an alarm
+  whoever caused it: a revision update the platform failed, its autoscaler failing, and any other
+  row it marks `Warning` but the five measured by-products of a deploy or a wake. `DSP-IN-05`
+  amended. No clause added.
```
