<!-- Agent: planning | Role: sprint handover — make the orphaned-reply count a recorded fact before anyone diagnoses it -->
# Sprint 194 — a number nobody records is a number nobody has

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-194-a-number-nobody-records-is-a-number-nobody-has` — cut from **`main`**
**Status:** MERGED + GATE PROVEN on `main`
**Version:** `0.94.05` (PATCH from `0.94.04`)
**Effort:** S
**Decisions:** [DL-145](../design-log.md) the second K=4 measurement · work-queue item 3

> **Why this bump kind.** No new capability and no new behaviour — the number is already computed
> every run, in memory, and thrown away. Persisting a fact the agent already holds is a **fix**, so
> PATCH.

> 🎯 **This sprint exists because S172's acceptance criterion cannot currently be falsified.**
> It is deliberately *not* the fix for the lost replies. It is the instrument that makes the fix
> measurable — and it must land first, or a fourth attempt ends where the first three did.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` | The deliberator's **locked constitution** (currently **v1.2**) | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/deliberator/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding section: **`DLIB-OBS`** — what a `DeliberationRun` must record. **`DLIB-NEV-06`** also binds:
it exists to stop evidence about lost replies being quieted, and this sprint is the constructive
side of that clause.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read `test-plan.md` alongside `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row (next free is **DRIFT-056**).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**My reading is that the second half is YES, and that this one does need a law clause.** Nothing in
`contracts/` changes — but the agent starts promising something it never promised: *every
`DeliberationRun` records how many peer replies arrived for a debate it was no longer waiting on.*
That is a new observable guarantee, of exactly the kind `DLIB-OBS` already covers for
`failed_open_count`. **Expect a new `DLIB-OBS` clause, a `test-plan.md` row, a laws version bump to
v1.3, and a ledger/INDEX rollup update.** Confirm that reading rather than inheriting it, and if you
conclude a full cycle is *not* needed, say why from the law text.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/deliberator/store.py` (`write_deliberation_run`) | `agents/deliberator/laws/laws.md` + `test-plan.md` | `DLIB-OBS` — the run's recorded facts |
| `agents/deliberator/poll.py` | same | it is the caller that must supply the number |
| `agents/deliberator/servicebus_peer_client.py` | same; `DLIB-NEV-06` | the counter's home |
| `orchestration/packs/trading_graph_vocabulary.json` | `docs/laws/conventions.md` | property-enforced label — see the deploy trap below |

---

## Goal

Make `orphaned_reply_count` a **recorded fact on the `DeliberationRun`**, beside `failed_open_count`,
so that S172's success factor 4 can be checked by reading the graph instead of by watching a log
that no longer exists.

---

## Why (context) — measured 2026-09-01, [DL-145](../design-log.md)

S172's success factor 4 is `orphaned_reply_count == 0`. That number:

- **lives only in process memory** — `ServiceBusPeerClient._orphaned_reply_count`
  (`agents/deliberator/servicebus_peer_client.py:60-66`), incremented by `_record_orphans` (`:150`);
- **is emitted only as a log warning** (`:170`);
- **is never written to the graph** — `DeliberationRun` props are exactly
  `created_at, debates, failed_open_count, failed_open_reason, failed_open_tickers, max_rounds,
  narrative, real_debate_count, role_models, source_pm_run_id, transcript, verdicts,
  vetoed_tickers`;
- **and the log does not survive.** `ContainerAppConsoleLogs_CL` held **625 rows in three hours**,
  of which `master` 531, `deliberator-proponent` 40, `deliberator-opponent` 54, and
  **`deliberator-manager` zero**. The one process that counts orphans emits nothing that outlives it.

🪤 **That was established with a control query, not assumed.** The filtered query returned nothing
*and* an unfiltered count over the same window returned **0**, which is how "the table is empty for
that app" was told apart from "no orphans occurred". Do the same whenever you read that table.

**Consequence:** DL-140's *"6 orphaned replies"* can never be re-derived, and the 2026-09-01 re-run's
count is **UNKNOWN — not zero**. Two expensive live runs have now failed to settle a criterion that a
single integer would have settled.

🟩 **And it is buildable on `main` today.** `servicebus_peer_client.py` and its counter are on
`main`; only S172's `servicebus_reply_inbox.py` is branch-only. So this does **not** wait for S172 —
it lands in production and starts recording the number on **every nightly run**, including the
current serial path, which also answers a question nobody has asked: *do orphans happen at K=1 too?*

---

## Scope

1. Thread the per-run orphan count from the peer client to `write_deliberation_run`.
2. Declare `orphaned_reply_count` on `DeliberationRun` in the vocabulary pack.
3. Record it on every run, including **zero** — a missing key and a real zero must not look alike.
4. Tests, including the per-run-isolation trap below.

### Out of scope (do NOT build this sprint)

- **Do not fix the lost replies.** That is S192, and it cannot be judged until this exists.
- **Do not touch `debate_concurrency`, `max_rounds`, or `request_timeout_seconds`.**
- **Do not remove the log warning.** `DLIB-NEV-06` wants the evidence louder, not relocated.
- **Do not add orphan *identity* (which correlation keys)** — tempting, and it is the natural next
  ask, but it is a bigger surface and a count is what the success factor needs. Note it in the
  handback if you think it belongs.

### The road not taken (LAW-06)

**Parsing the count back out of logs** was considered and rejected: the manager emits nothing to Log
Analytics at all, so there is nothing to parse — and a fix that depends on log retention would fail
silently the same way this did.

---

## 🚨 Two traps that will produce a wrong number quietly

🪤 **1 · The counter is cumulative per client instance, not per run.** `_orphaned_reply_count` is
initialised once in `__init__` and only ever incremented. The poll loop can serve **several PM runs
from one client**, so reading the raw attribute would stamp run #2 with run #1's orphans plus its
own. **The recorded value must be the delta for that run** — snapshot before, subtract after, or
have the client expose a per-run scope. Whichever you choose, prove it with a test that runs **two
debates through one client** and asserts the second run's count excludes the first's. Without that
test this sprint ships a number that is wrong in exactly the direction that hides the defect.

🪤 **2 · The vocabulary pack moves, so the deploy is a full `up`, never a retag.** `DeliberationRun`
is **property-enforced** — it is listed under `properties` in
`orchestration/packs/trading_graph_vocabulary.json` with an explicit key list. Adding a key changes
the pack hash, and the write guard is **fail-closed**: an image deployed against a stale pack raises
`VocabularyError` and stalls the run mid-cascade (the S148 stall, [DL-85](../design-log.md)). **Say
so in the handback** so nobody retags. Verify with
`git show <deployed>:orchestration/packs/trading_graph_vocabulary.json | sha256sum` against `HEAD`.

---

## Steps, in order

1. MUST RULE reading; write the Law reading record; answer the law-cycle question.
2. Decide and implement per-run scoping of the count (trap 1). **Write that test first.**
3. Thread it to `write_deliberation_run` and record it, zero included.
4. Declare the property in the vocabulary pack.
5. Complete the law cycle if your answer to the law-cycle question was yes.
6. `make ci` redirected **to a file**, then read the file.
7. PATCH bump; fill the sprint doc, `docs/design-log.md`, and work-queue item 3.

---

## Test plan

| # | Test | Passes only if |
| --- | --- | --- |
| 1 | A run with no orphans records `orphaned_reply_count == 0` | Zero is recorded, not omitted |
| 2 | A run with N orphaned replies records exactly N | The number is real, not a flag |
| 3 | **Two runs through one client instance** | The second run's count **excludes** the first's — trap 1 |
| 4 | The property is declared in the vocabulary pack | The fail-closed guard will accept the write |
| 5 | A `DeliberationRun` written without the count still reads back safely | Old rows do not break readers |
| 6 | The log warning still fires | `DLIB-NEV-06` — evidence added, not moved |

---

## Success factors

1. 🟩 Test 3 exists and fails against a naive cumulative read — paste both outputs.
2. 🟩 `make ci` exit 0, 100 % coverage, from a file.
3. 🟩 `make gate-ran` exits 0 for the merged SHA, run from the worktree at that commit.
4. 🟩 The vocabulary hash is shown to have **changed**, with the handback stating **full `up`**.
5. 🟩 Law cycle completed, or its absence justified from the law text.

**Not a success factor:** any orphan number from a live run. This sprint ships the instrument; the
first nightly run after deploy reads it.

---

## Guardrails (every sprint)

- Branch from `main`; never commit to `main`.
- `make ci` locally **before** pushing; then push and require `make gate-ran` for the exact SHA.
- Module size: hard block 200, warn 150. No `# noqa` to bypass.
- 🪤 **Check `git branch --show-current` immediately before every commit** — this tree is shared.
- 🪤 **Never measure the gate through a pipe** — redirect to a file and read the file.

---

## Sequencing after merge

**Deploy is a full `pwsh infra/deploy-agents.ps1 up -Tag <tag>`** (trap 2). After that, the value
arrives on its own from the next nightly run — no experiment needed. **Then** S192 becomes
answerable: with the count recorded per run, the intermittency [DL-145](../design-log.md) found can
be counted across nights instead of chased with expensive one-off K=4 runs.

---

## Handover — paste this to Codex

> Build **Sprint 194** from `docs/sprints/sprint-194-a-number-nobody-records-is-a-number-nobody-has.md`,
> branched from `main`.
>
> S172's acceptance criterion is `orphaned_reply_count == 0`. That number is computed every run and
> then thrown away: it lives only in `ServiceBusPeerClient` memory, is emitted only as a log warning,
> is never written to the graph, and the manager emits nothing to Log Analytics at all. Two expensive
> live runs have failed to settle a criterion one integer would settle. **Record it on the
> `DeliberationRun`, beside `failed_open_count`.**
>
> **Two traps decide whether this works.** The counter is **cumulative per client instance**, and the
> poll loop can serve several runs from one client — so record the **per-run delta**, and prove it
> with a test that pushes two runs through one client. And `DeliberationRun` is **property-enforced**
> in the vocabulary pack, so this changes the pack hash and the deploy is a **full `up`, never a
> retag** — the write guard is fail-closed and a stale pack stalls the run mid-cascade.
>
> Answer the law-cycle question yourself: my reading is that this **does** add a new observable
> guarantee and so wants a `DLIB-OBS` clause and a laws bump to v1.3.
>
> Do not fix the lost replies — that is S192 and it cannot be judged until this exists.

---

## Handback contract — MANDATORY

Report, in this order: what you changed and why · the two-runs-one-client test failing then passing ·
`make ci` from the file with its tally · merged SHA and `make gate-ran` · **the vocabulary hash
before and after, with the words "full `up` required"** · the law-cycle answer and what you did about
it · anything you could not do.

🚨 **Do not hand back with the Closeout block unfilled.**

---

## Law reading record — fill BEFORE writing code

| Law file | Read in full? | Clauses relied on | Status (🟩/⬜) | Notes |
| --- | --- | --- | --- | --- |
| `agents/deliberator/laws/laws.md` | Yes | `DLIB-OUT-02`, `DLIB-NEV-06`, `DLIB-OBS-01`, `DLIB-OBS-03` | `DLIB-OUT-02` 🟩; `DLIB-NEV-06` 🟩; `DLIB-OBS-01` ⬜; `DLIB-OBS-03` 🟩 | Current law records verdict/debate/fail-open evidence, but is silent on orphaned peer replies. |
| `agents/deliberator/laws/test-plan.md` | Yes | same | mixed | The relied-on failed-call visibility clauses are green; reconstructable-run evidence is still gray, and the new orphan count needs its own cited row. |
| `docs/laws/conventions.md` | Yes | §2, §3, §4, §7, §9 | applies | New IDs are append-only; a clause is green only with a passing functional test citation; locked laws need an explicit amendment and changelog. |
| `docs/laws/drift-register.md` | Yes | central drift register shape | applies | No existing deliberator drift row or `DRIFT-056` row covers this; the sprint can amend the deliberator law directly because the guarantee is decided here. |

**Law-cycle answer:** YES. The sprint adds a guarantee the deliberator did not previously make:
each `DeliberationRun` must record the count of peer replies that arrived after the manager stopped
waiting for them. `DLIB-OUT-02` records the existing run payload shape, `DLIB-NEV-06` forbids hiding
failed peer/debate evidence, and `DLIB-OBS` currently names reconstructability and fail-open
rationale but not late/orphaned replies. Per conventions §4 and §7, the locked law should be amended
first with a new append-only `DLIB-OBS-04`, then proven by functional tests that cite it. No
`contracts/` file is planned.

---

## Test plan results — fill at handback

| # | Test | Result | Evidence |
| --- | --- | --- | --- |
| 1 | zero recorded, not omitted | 🟩 Passed | `test_manager_reviews_pending_pmrun_with_two_peer_rounds_and_llm_costs` asserts `orphaned_reply_count == 0` on the normal local peer path. |
| 2 | N orphans recorded as N | 🟩 Passed | `test_orphaned_reply_count.py::test_manager_records_orphaned_reply_count_per_run_delta` records `2` for the first PM run. |
| 3 | two runs, one client — no bleed | 🟩 Passed after red proof | Naive raw cumulative write failed with `assert 3 == 1` for run #2; the delta implementation records `1` while the peer client's lifetime total remains `3`. |
| 4 | property declared in the pack | 🟩 Passed | `test_graph_vocabulary_deliberation.py` accepts `orphaned_reply_count`; the property scanner recovers it from the write site. |
| 5 | old rows read back safely | 🟩 Passed | `test_deliberation_view_handles_missing_narrative` omits the new field and renders `orphaned_replies=n/a` with no new breach. |
| 6 | log warning still fires | 🟩 Passed | `test_debate_turn_skips_stale_ahead_of_genuine_reply_and_faults` still asserts an `OrphanedPeerReply` fault and sink context with `orphan_count == 1`. |

---

## Closeout — evidence

- **Merged SHA:** `e0a144fc08b1d5fd8bc219f4ed48fef74fa8d120`
- **Version:** `0.94.05`
- **Red proof, missing field:** focused tests failed before implementation:
  `KeyError: 'orphaned_reply_count'` in the manager persistence test,
  `VocabularyError: undeclared properties for label 'DeliberationRun': ['orphaned_reply_count']`,
  and a missing view observation key.
- **Red proof, cumulative trap:** deliberately naive raw-count write failed
  `test_manager_records_orphaned_reply_count_per_run_delta` with `assert 3 == 1`, proving run #2
  would inherit run #1's orphan count.
- **Focused green:** 61 passed in 8.88 s across deliberator, Service Bus peer, vocabulary, property
  scanner, and deliberation-view tests.
- **`make ci`:** `cmd /c "make ci > %TEMP%\s194-make-ci.txt 2>&1"` exited 0. File evidence:
  ruff/format/mypy/import-linter passed; module-size warnings only; law coverage and PARAM sync
  completed; pytest `2452 passed, 4 skipped` with `100.00%`; pip-audit found no known
  vulnerabilities; detect-secrets and untracked secret scan passed.
- **Branch `make gate-ran`:** `GATE PROVEN for e0a144fc08b1d5fd8bc219f4ed48fef74fa8d120`
  after branch CI `33602950063` and Security Findings completed success.
- **Main `make gate-ran`:** run from `main` with `git rev-parse HEAD` =
  `e0a144fc08b1d5fd8bc219f4ed48fef74fa8d120`; output:
  `GATE PROVEN for e0a144fc08b1d5fd8bc219f4ed48fef74fa8d120` with CI,
  Security Findings, CodeQL, Build and push agent images, Configured Graph Update, and
  `uv in / for openai - Update` all success.
- **Vocabulary hash before → after:** `9b57a99786fee046042e2dd36a9d399e25d0d64850633a1b1db267ad1693a64e`
  → `d47e88b19111ed2c5d355fee63d1e55426239da5a097ca748aa1f0833bf563c2`.
- **Deploy shape:** full `up` required — the vocabulary pack changed and `DeliberationRun` is
  property-enforced, so an image-only retag would be unsafe.
- **Law cycle:** Completed locally. Deliberator laws `v1.1` → `v1.2`; new `DLIB-OBS-04` added and
  cited by passing functional tests; ledger and laws index now read `10 / 52`.

---

## Return notes

- The spec expected a deliberator laws `v1.3` bump, but the actual law file was `LOCKED v1.1`; the
  correct amendment is `v1.2`.
- First full `make ci` failed on module size after the new test pushed
  `agents/deliberator/poll.py` to 202 lines and `test_deliberator_agent.py` to 224. The helper moved
  to `peer_client.py` and the new two-run proof was split into `test_orphaned_reply_count.py`; final
  full CI passed.
- Historical rows do not gain a fake zero. The view renders missing `orphaned_reply_count` as `n/a`.
- Branch push, remote gate, fast-forward merge to `main`, main push, configured graph update, image
  build, CodeQL, and post-merge `make gate-ran` are complete for
  `e0a144fc08b1d5fd8bc219f4ed48fef74fa8d120`.
- No live orphan count is claimed from this sprint. The instrument is shipped; the next live
  deliberation run is the first chance to record the number this sprint added.
