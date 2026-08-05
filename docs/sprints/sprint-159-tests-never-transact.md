<!-- Agent: planning | Role: sprint handover -->
# Sprint 159 — A unit test must never transact with production

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-159-tests-never-transact`
**Status:** SPEC — closes hardening **row T**, whose open question is now answered
**Version:** fix → **0.86.03** (PATCH: last two digits)
**Effort:** S–M
**Decisions:** [row T](../hardening-backlog.md) · [DL-70](../design-log.md) plant the violation ·
[DL-57](../design-log.md)/[DL-59](../design-log.md) intent ≠ outcome · [LAW-02](../../ops/laws/LAW-02-proof.md)
success is proven · [S133](sprint-133-servicebus-sas.md) entity-level SAS ·
[S158](sprint-158-fail-open-must-be-loud.md) the bundle-miss fix on this same settings object

> **Why the version is a PATCH and not a MINOR.** No new capability: this removes an unintended
> production side effect from the test suite and makes a clean checkout gateable. `0.86.02` →
> **`0.86.03`**. If `main` has moved past `0.86.02` when you start, bump the patch group from
> whatever is on `main` and say so in the return notes.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** — clauses `<AGENT>-<SECTION>-<NN>` | **LOCKED v1. Read-only. Never edit.** A clause you believe is wrong is a `drift-register.md` row plus a report, never an edit |
| `agents/<name>/laws/test-plan.md` | The clause-by-clause map: proven (🟩) vs unproven (⬜) | Read it to learn whether what you are changing is *proven* or merely *asserted* |
| `docs/laws/*.md` | Umbrella laws crossing every agent | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

For **this** sprint the binding sections are `SEC` (security), `DEP` (dependencies), `NEV`
(prohibitions) and `OBS` (observability). This sprint changes *what the test suite is allowed to
touch*, so the security and dependency clauses decide the design.

### The rule

1. **Before writing code**, for every element in the map below, open and read its law file(s) —
   whole file, first time, not a keyword grep.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Also read [`docs/laws/conventions.md`](../laws/conventions.md) (clause-ID scheme, ⬜ → 🟩),
   [`docs/laws/dependencies.md`](../laws/dependencies.md) (external-boundary clauses), and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Write the Law reading record** (template at the bottom) **before** your first code change. It is
   the first thing reviewed at handback.
5. **If a law contradicts this spec, STOP and report.** A contradiction you surface is a success.
6. **If a law is silent** where you must decide, that silence is a finding: record it and add a
   `drift-register.md` row.
7. Every test for behaviour a clause governs **cites the clause ID in its docstring**.

### Element → law map (read all of these)

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/deliberator/peer_client.py` (read-only here) + its tests | `agents/deliberator/laws/laws.md` + `test-plan.md` | The peer client is the thing that sent. `DLIB-*` `SEC`/`DEP`/`NEV` clauses govern what the deliberator may address and with whose credentials |
| `kernel/bus_azure_config.py`, `kernel/bus_azure.py` | `docs/laws/dependencies.md` + `docs/laws/conventions.md` | `kernel` has no agent law; the umbrella dependency clauses govern the Service Bus boundary. S133 put entity-level SAS on this object and S158 fixed its silent fallback — **read both sprints before changing it** |
| `conftest.py` (root) | `docs/laws/conventions.md` | Test-harness policy; conventions §3 governs what a green claim is allowed to mean |

---

## Why this sprint

Hardening row T was filed on 2026-08-04 with one question deliberately left open, because it decided
severity:

> *"Stated honestly: I verified the live endpoint resolves and that the real-send code path is taken;
> I did NOT establish that a message reaches the namespace — the test passes in 3.74 s without
> raising and that is unexplained in either direction."*

**It reaches the namespace.** Measured 2026-08-05 against `trading-agents-bus`:

```text
az servicebus topic subscription list -g trading-agents \
  --namespace-name trading-agents-bus --topic-name deliberator-proponent.requests

Sub    Active    Dead    Total
-----  --------  ------  -------
agent  0         40      40
```

Peeked (non-destructively) from the dead-letter queue:

```text
enqueued : 2026-08-02 10:47:08.987000+00:00
dlq      : S100ReceiverFailure
body     : {"topic": "deliberator-proponent.requests", "label": "AgentMessage",
            "ref": "6b03892d-ec94-4985-b833-a2d243b3d96c", "run_id": "turn-1"}
```

`run_id: "turn-1"` is the literal fixture value from `_turn_request()` in
[`tests/test_deliberator_servicebus_peer.py`](../../tests/test_deliberator_servicebus_peer.py).
The 40 messages arrive in **pairs about one second apart** — two tests per pytest run — across 20
runs between **2026-08-02 10:47 UTC and 2026-08-04 02:12 UTC**.

So the chain is not hypothetical, and it is worse than "a test sent a message":

1. The unit test published to the **production** namespace.
2. A **real production consumer** received it — `S100ReceiverFailure` is written by
   [`kernel/bus_azure_receiver.py:164`](../../kernel/bus_azure_receiver.py#L164), so the live
   deliberator-proponent receive path picked these up.
3. It failed to process them and retried to `max_delivery_count` (5), then dead-lettered them.

**Every local `pytest` run has been injecting traffic into the production bus and exercising a
production consumer's failure path.** No test asserted any of this; nothing in the suite reports it;
`make ci` was green throughout.

---

## The defect, precisely

Four independent facts compose into it. Each is correct on its own, which is why nothing caught it.

| # | Fact | Evidence |
| --- | --- | --- |
| 1 | The root conftest loads `.env` into `os.environ` for **every** test | [`conftest.py`](../../conftest.py) — `load_dotenv(override=False)` |
| 2 | `AzureServiceBusSettings` **also** declares `env_file=".env"`, which pydantic-settings reads directly, regardless of `os.environ` | [`kernel/bus_azure_config.py:33`](../../kernel/bus_azure_config.py#L33) |
| 3 | `publish()` takes the real Azure branch whenever a connection string resolves for the topic | [`kernel/bus_azure.py:109-115`](../../kernel/bus_azure.py#L109-L115) |
| 4 | The tests monkeypatch only the **receive** half (`_read_ready_event`); the **send** is real | [`tests/test_deliberator_servicebus_peer.py:52`](../../tests/test_deliberator_servicebus_peer.py#L52) — while `debate_turn` publishes via `claim_check_write` at [`peer_client.py:112`](../../agents/deliberator/peer_client.py#L112) |

Measured from the repo root, with the repo's own `.env` present:

```text
request_topic          = deliberator-proponent.requests
resolved for topic     = Endpoint=sb://trading-agents-bus.servicebus.windows.net/ ;<redacted>
azure.servicebus       = IMPORTABLE
```

### 🪤 The trap that makes the shallow fix wrong

The obvious fix is *"remove `env_file=\".env\"` from the settings class."* **That is not sufficient
and you must not stop there.** Fact 1 already put the same credentials in `os.environ`, so
pydantic-settings resolves them anyway. A fix that only removes `env_file` will look correct, pass,
and still send.

The same trap in reverse: **a git worktree has no `.env`** (it is gitignored and untracked). Tests
run there take the in-memory path and pass **whether or not you fixed anything**. This is exactly
how CI has been passing all along — there is no `.env` on the runner, so the runner never sees the
defect. **See the Proof environment section — it is the single most important instruction here.**

### The second half: a clean checkout cannot pass `make ci`

`make install` is a bare `uv sync` ([`Makefile:20-21`](../../Makefile#L20)), and `azure-servicebus`
lives in `[project.optional-dependencies] azure` in [`pyproject.toml`](../../pyproject.toml), which
`uv sync` does not install. A fresh clone following the repo's own install step therefore hits
`ModuleNotFoundError: No module named 'azure'` on these two tests. The only reason the gate has ever
been green locally is that the developer venv carried the extra from earlier work — **a green that
depends on the machine's history.**

Both halves share one cause, so item 1 closes both: once the tests take the in-memory path, nothing
imports `azure` and the extra stops being a hidden test dependency.

---

## Proof environment — read before you run anything

**Do this sprint in a branch inside the main working tree, not a worktree** — or, if you use a
worktree, copy `.env` into it *for the duration* and delete it before any `git add`
(CLAUDE.md: credentials never through the worktree; a `git add -A` during a merge stages them).

The reason is not convenience. **Without `.env` present, every test in this sprint passes
vacuously** — including the regression tests you are about to write. A green run in a `.env`-less
tree proves nothing at all, and reporting it as proof would be the exact DL-57 shape this repo keeps
finding: *didn't look* rendering identically to *looked and found nothing*.

Every proof in the closeout must state which tree it ran in and confirm `.env` was present.

---

## What ships (spec)

> Fill in the `**Result:**` line under each item as you complete it. Results go in this file,
> not in chat.

### 1 · The deliberator peer tests take the in-memory path by construction

Both tests in [`tests/test_deliberator_servicebus_peer.py`](../../tests/test_deliberator_servicebus_peer.py)
must inject settings that cannot resolve a connection string, so the offline path is chosen
**explicitly rather than by accident of environment**:

```python
AzureServiceBusSettings(connection_string=None, connection_strings_json=None)
```

Verified already: init kwargs outrank both `.env` and `os.environ`, and
`connection_string_for_topic()` then returns `None`, so `publish()` takes the subscriber loop.
Defaults (`receive_timeout_seconds`, `reply_topic_suffix`, `subscription_name`) are unaffected.

If you find a cleaner construction that is equally explicit, take it and record why.

**Result:**

### 2 · A live send during a test is a loud failure, not a transaction

Item 1 fixes two tests. It does not stop the **next** test from doing the same thing — the settings
object is one no-argument constructor call away from production in any test anyone writes.

Add an **autouse** guard in the root [`conftest.py`](../../conftest.py) that replaces
`AzureServiceBusBus._azure_send` for the duration of every test with something that raises a named
error carrying the topic and the remedy. Any test that reaches the live send path fails with a
message that tells the author what to inject.

- The guard must be **autouse and unconditional**. Do not add an opt-out marker "for future
  integration tests" — there are none in this suite today, and an opt-out is how this comes back.
- Keep [`conftest.py`](../../conftest.py) under the module-size limits and keep its existing
  `load_dotenv(override=False)` behaviour intact (item 4 explains why it stays).
- Guard the **send boundary**, not the settings object. The boundary is the last point where the
  defect is still observable and the first where it is unambiguous.

**Result:**

### 3 · Prove the guard can fail (DL-70)

A guard that has never been observed rejecting anything is not evidence.

Plant the violation: a test that constructs the bus with a **fake but non-`None`** connection string
and publishes, and requires the guard's error. Never a real credential, never a real endpoint —
a string that resolves is enough to select the branch.

**Result:**

### 4 · Answer the `env_file` question explicitly — do not leave it implicit

`AzureServiceBusSettings` is the only settings class in the repo that declares `env_file=".env"`
(verify that claim yourself; if others do, name them). Decide and record:

- **Recommended: remove `env_file=".env"` from `model_config`.** Production containers receive
  secrets as **environment variables** via Container Apps `secretRef`, never as a `.env` file, so
  removing it changes nothing in production. Locally, the root conftest and the operator's shell
  already put `.env` into `os.environ`, so scripts keep working. What it removes is the genuinely
  surprising part — that the file is read *even when a test has cleared `os.environ`*, which makes
  the object un-isolatable by ordinary means.
- **Whichever way you decide, it is not a substitute for items 1–3** (see the trap above).
- If you remove it, prove the production resolution path still works: `os.environ`-only construction
  must still resolve a connection string. If you keep it, say why in the return notes.

**Result:**

### 5 · A clean checkout must be able to pass the gate

Prove the second half of row T is closed: in an environment **without** the `azure` extra, the full
suite passes. Suggested proof — a throwaway venv (outside the repo tree) built with a bare
`uv sync`, then `uv run pytest`, with `.env` present so the proof is not vacuous.

If something *other* than these two tests still needs `azure` at import time, that is a finding:
name it, and either fix it here if it is one line, or record it rather than widening the sprint.

**Result:**

### 6 · Record the finding (LAW-06) and close the row

- Add **DL-89** to [`docs/design-log.md`](../design-log.md): the answered question, the 40-message
  evidence, the `os.environ`-vs-`env_file` trap, and the road not taken below. Status DECIDED.
- Move **row T** to **Done** in [`docs/hardening-backlog.md`](../hardening-backlog.md) with the
  evidence — and state plainly that the open question resolved to the **worse** answer
  (it transacted), not the cleanup answer.
- If reading the deliberator's laws shows the peer/credential boundary is undeclared, add a
  **DRIFT-032** row. Do not edit any `laws.md`.

**Result:**

---

## Test plan — every test I want, and why

**Ground rules.** Cite clause IDs where a clause governs the behaviour. Plant the violation and
require the failure (DL-70). If you conclude one of these is wrong or untestable, say so with a
reason — do not silently drop it.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | injected settings resolve no connection string | offline settings built as in item 1 | `connection_string_for_topic(...)` is `None` for a peer request topic **while `.env` is present** — assert the file exists in the test so a `.env`-less tree cannot pass it vacuously |
| A2 | the peer client takes the in-memory path | the two existing tests, unchanged in intent | they still pass, and `_azure_send` is never reached (the item-2 guard proves this by not firing) |
| A3 | 🎯 **the guard rejects a live send** | a bus built with a fake non-`None` connection string, then `publish()` | the named guard error is raised, naming the topic. **This is the regression test** — if one test from this sprint survives a refactor, it is this one |
| A4 | the guard is active for every test, not opted into | — | assert the autouse fixture is registered / that the patched attribute is in place inside an unrelated test |
| A5 | production resolution still works (only if item 4 removes `env_file`) | `os.environ` carrying a connection string, no file read | settings still resolve it — proves the removal did not break the container path |

**Do not** write a test that sends to a real namespace to "confirm the fix". The whole sprint is
that tests do not do that.

---

## Explicit non-goals

- **No change to `agents/deliberator/peer_client.py`'s behaviour.** It is doing what it is written to
  do; the defect is that a test invoked it with production credentials.
- **No change to the S133 entity-level SAS design** or to S158's bundle-miss fix. Read them; do not
  revise them.
- **No purge of the dead-letter queue — it is already at zero, and that zero is your instrument.**
  The 40 messages were purged 2026-08-05 with operator approval (see Sequencing 3). All 40 carried
  `run_id: "turn-1"`, so nothing real was discarded, and `az` independently confirms
  `active 0 / dead 0 / transferDead 0`. **Do not purge again during implementation** — if the count
  is non-zero when you check it, that is a finding to report, not a queue to tidy.
- **No credential rotation.** Nothing was leaked; the credential was used by the machine that owns
  it. If you disagree, say so rather than acting.
- **No widening into other settings classes** unless item 4 finds one with the same `env_file`
  declaration, in which case name it and fix only that.
- **No `laws.md` edits.** LOCKED v1.

### The road not taken (LAW-06)

Options weighed and **ruled out** — add any you rule out during implementation:

- **Stop loading `.env` in the root conftest.** The clean root-cause fix, and rejected as too blunt
  for this sprint: many tests legitimately read local config through `os.getenv`, and removing it
  would turn one narrow production-safety defect into a broad, poorly-understood test refactor. The
  send-boundary guard closes the dangerous half without that blast radius. **If someone later wants
  the conftest change, this is the entry that says it was considered.**
- **Mark the two tests as integration and skip them by default.** Rejected: it deletes the coverage
  instead of fixing it, and leaves the loaded gun (a bare `AzureServiceBusSettings()`) pointed at
  the next test author.
- **Add `azure` to `make install` so a clean checkout has the extra.** Rejected — it makes the
  *symptom* go away by guaranteeing the SDK is present, i.e. it makes production sends *more*
  reliable from a test run. Exactly backwards.
- **Guard by patching `ServiceBusClient` at the SDK boundary.** Rejected: it only works when the SDK
  is installed, so the clean-checkout case would be unguarded, and it couples the guard to a vendor
  import path.
- **Fail the run if `.env` is present during pytest.** Rejected: it would make the local gate refuse
  to run on every developer machine, and local `.env` is load-bearing for other tests.

---

## Sequencing after merge

1. `make ci` green locally **in a tree with `.env` present**, branch pushed, all four remote gates
   green **before** merging locally (DL-56 — pushing is the gate; no PR required).
2. **No fleet retag is required.** This sprint changes test-harness behaviour, not agent behaviour.
   Say so explicitly rather than leaving the fleet question open.
3. **The dead-letter queue is the closeout's verification instrument.** The 40 messages were purged
   **2026-08-05 with operator approval**, after confirming all 40 carried `run_id: "turn-1"` (a
   `run_id` histogram of `{'turn-1': 40}` — no real production message was discarded). Verified
   independently afterwards: `active 0 / dead 0 / transferDead 0`, and the sibling
   `deliberator-opponent.requests` also 0/0. **Purging destroyed no evidence** — the record is this
   document plus DL-89, not the messages.

   The baseline of **zero** is what makes the closeout provable, and it is why the purge happened
   before the fix rather than after: at zero, *any* message appearing after a `pytest` run is
   unambiguous proof the fix failed. At 40 you would be comparing 40 against 42 and trusting your
   own earlier reading.

   ⚠️ **The baseline decays.** Every `pytest` run against an unfixed tree with `.env` present adds
   two more — including your own runs while implementing. So:

   - **Before** your first proof run, re-check the count and **state it in the closeout**. Non-zero
     is expected if you have already run the suite; report the number, do not purge it.
   - **At closeout**, purge once more (operator-approved for this sprint), then run the full suite
     one final time in a tree **with `.env` present**, and paste the post-run count. **`dead: 0`
     after a full suite run is the single strongest piece of evidence this sprint can produce** —
     stronger than any unit test, because it observes the production side directly.
4. No functionality-check row is owed — there is no production behaviour change to check. If you
   believe one is owed, say why.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). No `# noqa` to bypass.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all 11 steps** green, **100.00 % coverage floor**, before handback. Never lower it.
  **Never measure the gate through a pipe** — `make ci | tail` reports `tail`'s exit code
  (hardening row S). Redirect to a file and read the file.
- Version bump in `pyproject.toml` to **0.86.03** (fix → PATCH), `uv.lock` staged with it.
- Any law clause your tests cover cites the clause ID in the test docstring.
- If `main` has moved when you finish: merge `main` into the branch, resolve, re-run `make ci`, and
  **say so in the return notes** (DL-48).
- Secrets never through the worktree — chat or gitignored `.env` only.

---

## Handback contract — MANDATORY

**Append your results INSIDE this file, at the bottom, in the placeholder sections below.**
Not a separate report file. Not chat-only.

1. Fill the **Law reading record** *before* your first code change.
2. Fill the `**Result:**` line under **each** of the six spec items, in place.
3. Fill the **Test plan results** table — one row per test, with its final name and status. A test
   you chose not to write needs a reason, not a blank.
4. Fill the **Closeout — evidence** block with real command output pasted in, and **state which tree
   you ran in and that `.env` was present**.
5. Fill the **Return notes** block.
6. State any success factor you did **not** meet plainly, as "verified failing" or "not done"
   (LAW-02 — a proven failure is a valid handback, a silent gap is not).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? (yes + what / no) |
| --- | --- | --- | --- |
| `agents/deliberator/peer_client.py` + tests | | | |
| `kernel/bus_azure_config.py` / `bus_azure.py` | | | |
| `conftest.py` (root) | | | |

**Contradictions found between a law and this spec** (a contradiction is a success — name it):

**Laws found silent where a decision was needed** (each needs a `drift-register.md` row):

**Clauses that were ⬜ unproven in `test-plan.md` and are now proven by this sprint's tests:**

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | | | | |
| A2 | | | | |
| A3 | | | | |
| A4 | | | | |
| A5 | | | | |

**Tests added beyond the plan:**

---

## Closeout — evidence

**Tree the proofs ran in (and `.env` present?):**

**Files changed:**

**Proven (LAW-02):**

**Not met / verified failing:**

---

## Return notes
