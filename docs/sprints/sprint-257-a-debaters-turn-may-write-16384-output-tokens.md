<!-- Agent: planning | Role: sprint handover -->
# Sprint 257 — A debater's turn may write up to 16,384 output tokens, and the manager may wait long enough for it

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-257-a-debaters-turn-may-write-16384-output-tokens`
**Status:** BUILT
**Version:** `0.123.02`
**Effort:** S
**Decisions:** [DL-274](../design-log.md) (decisions D1 to D4 this sprint builds) · work-queue **111** ·
[DL-264](../design-log.md) amendment 7 (this fix comes before step 3) ·
[sprint-256](sprint-256-a-served-request-is-settled-when-it-is-taken.md) (built first: after it no
message lock is held while a turn runs, so a longer turn is safe)

> **Why this bump kind.** No new capability. A turn the vendor cuts at the cap fails its order open, and
> on `gpt-5.5` one defender turn in five is longer than the cap allows.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the amendments this spec names. A clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: deliberator **`DLIB-PERF`**, **`DLIB-DEP`**, **`DLIB-NEV`**, and the book's
`PARAM` table.

### The rule

1. **Before writing code**, read every law file in the map below, whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides what this sprint owes.
5. **Write the Law reading record** (at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row (take the next free number).
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's answer: No.** No file in `contracts/` changes and no agent promises anything new: two
bounds and one default move inside guarantees the book already makes (`DLIB-PERF-02`: *"Peer wait time is
bounded by `request_timeout_seconds`"*). What is owed is the reconciliation the gate enforces:

- The two `PARAM` rows of `agents/deliberator/laws/laws.md` follow the code: `max_tokens` (default and
  upper bound 16,384) and `request_timeout_seconds` (upper bound 300). `make ci`'s parameter step fails
  until they do.
- A Changelog line naming S257 and DL-274, and the version step the conventions ask of a `PARAM`-only
  change. Do not pin the number here: sprint 256 moves the same book first.

Edit no clause. If your reading finds a clause that states the old numbers, name it in the Law reading
record and stop.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/deliberator/settings.py` | `agents/deliberator/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | the `PARAM` table; `DLIB-PERF-02` (the wait is bounded by the setting); `DLIB-DEP-04` (cited by the test that pins the cap and its law row) |
| `kernel/llm_anthropic.py` | same | `DLIB-NEV-06`: a failed peer call is never hidden. A cap the vendor's client refuses would fail every turn |

⚠️ **Nothing a model reads may change.** No prompt, no packet line, no schema. If a test that compares
prompt bytes or hashes fails, stop and report.

---

## Goal

At merge, a debater's or judge's call may write up to 16,384 output tokens by default, the setting cannot
be raised past what Anthropic's client accepts without streaming, and the manager's wait for a served turn
can be set as high as 300 seconds. Nothing a model is sent changes except that one number in the request.

## Why (context)

On `gpt-5.5` the model's reasoning counts against the output cap, and the fleet runs it at `high` effort.
The one production debate measured there wrote 6,363 and 7,738 tokens in its two defender turns against
a cap of 8,192. A completion cut at the cap raises in the vendor adapter, and that order fails open: it is
submitted as the portfolio manager approved it, unreviewed. The fleet debates on `gpt-5.5` now, and the
typed turn that step 3 brings is longer still. No setting can raise the cap, because the tunable's own
upper bound is 8,192.

### Measured, 2026-10-08 — read these before designing

No LLM call was made for this spec. Rows marked *kept records* come from the call logs of two experiments
run on 2026-10-07; rows marked *live* were read from the fleet's graph or its apps and cannot be re-run in
a worktree.

| Claim | Value | How it was measured |
| --- | --- | --- |
| How the cap is sent | OpenAI: `max_completion_tokens`, which counts reasoning tokens too; Anthropic: `max_tokens`. One setting, `DeliberatorSettings.max_tokens`, feeds both through `build_llm` | *[measured, read]* `kernel/llm_openai.py`, `kernel/llm_anthropic.py`, `agents/deliberator/entrypoint.py` |
| What a cut completion does | `kernel/llm_openai.py` raises `LLMCompletionStoppedError(stop_reason="length")`; the turn fails and the order fails open | *[measured, read]* |
| The one production debate on `gpt-5.5` | output tokens 6,363, 3,860, 7,738 and 3,866 for the four turns, 368 for the judge; 58.1, 32.1, 59.8, 33.1 and 5.4 seconds; 188 seconds of model time for the order | *[measured 2026-10-07]* S254's F1, one order, the vendor's counts |
| The typed first turn on `gpt-5.5` | defender: median 6,726 tokens, largest **11,556**, **5 of 25 over 8,192**; challenger: median 4,985, largest 7,320, 0 of 24 over | *[measured, kept records]* 49 calls of EXP-020 and EXP-021 |
| Speed on `gpt-5.5` at `high` effort | 86 to 117 output tokens a second over the 49 calls, median 109: a turn's time follows its output | *[measured, kept records]* |
| So a turn that used a whole cap would take | 8,192: up to 96 s. 12,288: up to 143 s. **16,384: up to 191 s** (at the slowest measured rate) | *[computed from the row above]* |
| The slowest call on record | 118 seconds for 11,556 tokens, against a 120-second wait | *[measured, kept records]* |
| Opus, guided turns, since 2026-09-30 | challenger largest 4,846 tokens and 56.1 s, defender largest 3,300 and 35.6 s, judge 434 and 7.7 s (9 debated orders, 45 calls) | *[measured, live]* the `LLMCall` rows |
| What Anthropic's client accepts without streaming | up to **21,333**: version 0.120.2 refuses a non-streaming request whose `max_tokens` makes 3,600 s × cap / 128,000 exceed 600 s, for every model; `claude-opus-5` has no lower per-model limit | *[measured, offline]* `Anthropic(api_key="x")._calculate_nonstreaming_timeout(cap, None)`: 21,333 allowed, 21,334 refused |
| Where that library is installed | only in the `llm` extra. CI's environment and a worktree's do not have it, so no CI test can call it | *[measured, read]* `pyproject.toml` |
| What the fleet sets | no app sets `DELIBERATOR_MAX_TOKENS`, so the code's default is the fleet's cap. All three deliberators carry `DELIBERATOR_REQUEST_TIMEOUT_SECONDS=120` from the tunables pack | *[measured, live]* the three apps' environment names; the pack |
| The tunables pack is fidelity decision code | `orchestration/packs/trading_tunables.json` is in `DECISION_PATHS`: an edit to it starts the fidelity count again | *[measured, read]* `scripts/replay_fidelity_git.py` |
| The prototype against the whole suite | the two bounds and the default changed in the settings, the two `PARAM` rows changed to match: the parameter step passes, and **exactly two existing tests fail** (4,301 pass, 8 skipped), both because they pin the old cap; they are named under Traps. No test pins the wait's bound of 120 | *[measured]* a throwaway worktree at `5535eb32` |
| Module sizes | `agents/deliberator/settings.py` **158**, `kernel/llm_anthropic.py` **158** | *[measured]* `wc -l` |
| A larger cap changes what Opus writes | *[ASSUMED not to]* the cap is a ceiling, and Opus's largest turn is 4,846 tokens. Not measured: the Anthropic account is empty until 2026-10-11 | F2 reads it |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first (A1, A3, A4).**
2. **The cap** (D1): `max_tokens` defaults to 16,384 and may not exceed 16,384. Its `why` states the
   measured reason.
3. **The ceiling has a reason in code** (D2): a named constant in `kernel/llm_anthropic.py` holds the
   largest cap Anthropic's client accepts without streaming, with its arithmetic, and a test holds the
   setting's upper bound at or under it.
4. **The wait** (D3): `request_timeout_seconds` may be set up to 300. Its default stays 30.
5. **The `PARAM` rows and the Changelog line.**

### Out of scope (do NOT build this sprint)

- **`pyproject.toml` and `uv.lock`.** Do not touch either. The planner bumps the version at merge.
- **`orchestration/packs/`.** The fleet's wait is raised on the live app at the deploy, by the planner
  (D4). An edit to the tunables pack would start the fidelity count again.
- **The effort.** Running the debaters at `medium` on `gpt-5.5` changes what they write.
- **Streaming.** It would lift the 21,333 limit and is a change to how every call is made.
- **A per-vendor cap.** One setting feeds both vendors; 16,384 is valid for both.
- **Execution's grace and the night's capacity** (work-queue 113), and a time to live on a request.
- **The role prompts, the packet, the guided turn, the DSPy modules, the judge.**
- **The merge and the push.** Commit on the branch and hand back.

### The road not taken (LAW-06)

- **Lower the effort to `medium` on `gpt-5.5`.** Rejected: it changes the debaters' writing to work
  around a number, and needs a paid measurement first.
- **A cap of 12,288.** Rejected: 6 % above the largest turn already measured.
- **A cap of 32,768, or no upper bound.** Rejected: Anthropic's client refuses a non-streaming call above
  21,333, so a setting in that range would fail every Opus turn.
- **Raise the bound and leave the default at 8,192.** Rejected: the fleet reads the default; reaching it
  with a setting means the tunables pack or a hand-made live change.
- **Leave the wait's bound at 120.** Rejected: a turn that uses the new cap can take 191 seconds, so the
  failure would move from the cap to the wait.

---

## The design decisions — made, and recorded in DL-274

**Build them as written.** Record in `docs/design-log.md` (take the next free number) only a decision the
spec did not make, or a place where you had to depart from one of these, with the reason.

| # | Decision | Rejected |
| --- | --- | --- |
| D1 | `DeliberatorSettings.max_tokens`: default `16384`, `le=16384`, `ge=64` unchanged. The `why` keeps the S246 sentence about the readings and adds the measured reason: on `gpt-5.5` reasoning counts against the cap, a defender turn reached 7,738 tokens in production and 11,556 in the typed turn, and the cap is billed only when used | see the road not taken |
| D2 | `kernel/llm_anthropic.py` gains `NONSTREAMING_MAX_TOKENS = 21_333`, with a comment giving the client's rule (3,600 s × cap / 128,000 must not exceed 600 s), the version it was measured on (0.120.2) and the date. A test asserts the setting's upper bound is at or under it, and that the constant equals `600 * 128_000 // 3_600` | calling the vendor's client in a test: it is not installed where CI runs |
| D3 | `DeliberatorSettings.request_timeout_seconds`: `le=300.0`; default `30.0` and `ge=1.0` unchanged. The `why` says a turn at the cap can take about 190 seconds on the slowest rate measured | a default of 240: the fleet's value comes from the pack, not the default |
| D4 | The fleet's wait goes from 120 to 240 seconds on the manager's live app at the deploy, by the planner, on the operator's word, with a before and after snapshot. The tunables pack is not edited | editing the pack: it starts the fidelity count again |

---

## Blast radius — measured 2026-10-08

| What | Detail |
| --- | --- |
| Files changed | `agents/deliberator/settings.py` **158**, `kernel/llm_anthropic.py` **158**, the deliberator's `laws.md` (two `PARAM` rows, one Changelog line); the tests |
| Agents affected | the three deliberator roles. No agent imports another |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none. One default and two upper bounds change |
| Deploy implication | image-only retag, then one live setting on `deliberator-manager` (D4) |
| Rollback | retag the fleet to the tag it ran before, and set `DELIBERATOR_REQUEST_TIMEOUT_SECONDS` back to `120` on `deliberator-manager` if it was raised: a retag does not undo a live setting, and older code refuses a value above 120 at start-up |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Plant the failing tests first** (A1, A3, A4) and watch them fail. Paste the red output.
3. **Implement** D1 to D3.
4. **The `PARAM` rows and the Changelog line.**
5. **Prove the guards can fail (DL-70):** break each guarded property, watch the guard go red, restore.
6. **`make ci`**, every step of the `ci:` target, **redirected to a file, never piped**. Name any step
   your sandbox cannot run as NOT RUN.
7. **Fill the handback sections** at the bottom of this file and set Status to `BUILT`, here and in
   this sprint's `README.md` row.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 The default cap is 16,384 and its law row agrees | The settings and the book's `PARAM` row | The default is 16,384; 16,384 is accepted and 16,385 refused; the row reads `` `max_tokens` `` · `` `16384` `` · `int >= 64 <= 16384`; the `why` names the measured reason (`DLIB-DEP-04`) |
| A2 | 🎯 The cap reaches each vendor's request | `build_llm` for each provider from default settings, with the vendor's client replaced as the existing adapter tests replace it | OpenAI's request carries `max_completion_tokens` 16,384; Anthropic's carries `max_tokens` 16,384 |
| A3 | 🪤 No setting can ask Anthropic for a call its client refuses | The setting's upper bound and `NONSTREAMING_MAX_TOKENS` | The bound is at or under the constant; the constant equals `600 * 128_000 // 3_600`. Planting a bound of 32,768 turns it red |
| A4 | 🎯 The manager may wait up to 300 seconds | The settings and the `PARAM` row | 300 is accepted and 300.1 refused; the default is still 30; the row reads `float >= 1 <= 300`; `build_manager` hands the peer client the configured value (`DLIB-PERF-02`) |
| A5 | 🪤 A cut completion still fails its order open, loudly | The existing stop-reason tests | They pass with no edit (`DLIB-NEV-06`, `DLIB-OBS-03`) |
| B1 | 🪤 Nothing a model reads changes | The role prompts, the packet builder, the guided turn, the DSPy engine and program | `git diff main` is empty for them; the parity and hash tests of sprint 254 pass with no edit |
| B2 | 🪤 The parameter step agrees | `scripts/check_param_law_sync.py` | Exit 0 |

No test may skip when a dependency is missing. A skipped proof is not a proof. No test calls an LLM.

---

## Success factors

- [x] The default cap is 16,384, and a setting above 16,384 is refused (A1).
- [x] Both vendors' requests carry the cap from the settings (A2).
- [x] The cap's upper bound cannot pass what Anthropic's client accepts without streaming (A3).
- [x] The wait can be set to 300 seconds and no higher; its default is unchanged (A4).
- [x] A completion cut at the cap still fails its order open and says so (A5).
- [x] No prompt, packet line or schema changes (B1).
- [x] The two `PARAM` rows follow the code; no clause is edited.
- [x] `pyproject.toml`, `uv.lock` and `orchestration/packs/` are untouched.
- [x] Every new guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module < 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage, or each step that could not run named as NOT RUN.

---

## Traps

🪤 **Existing tests pin the old numbers.** Measured on the prototype; each needs a deliberate edit, named
in the handback with its reason. Any other is a finding: name it.

- `agents/deliberator/tests/test_guided_turn_edges.py::test_the_output_cap_is_8192_and_its_law_row_agrees`:
  pins the default of 8,192 and the old `PARAM` row. It becomes A1; rename it.
- `agents/deliberator/tests/test_llm_provider.py::test_max_tokens_default_is_its_own_ceiling`: pins a
  default and a maximum of 8,192. The default is still its own ceiling, at 16,384.

🪤 **The `why` text is asserted.** One of those tests looks for `3,026` in the setting's description. Keep
the S246 sentence; add to it.
🪤 **The `PARAM` row is asserted as a whole string**, and `make ci` compares the table with the code. Change
the row and the code in the same commit.
🪤 **`anthropic` and `openai` are not installed in CI's environment or in your worktree.** Do not import
either at module level, and do not write a test that needs one.
🪤 **`kernel` may not import an agent.** The constant lives in the kernel; the deliberator's settings and
the test import it from there.
🪤 **Sprint 256 changes the same law book and its rollups.** It is merged before your worktree is cut.
Do not carry a version number over from this spec: read the book.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `kernel.tunable(..., why=...)` with bounds. This sprint adds no tunable; the one
  new constant carries its derivation.
- Faults, not silent failure: `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Secrets never through the worktree. A worktree has **no `.env`**, and nothing here needs one.
  **State which tree you ran in.**

---

## Sequencing after merge

Owed by the planner, in this order:

1. **Before the handover:** sprint 256 merged, then the worktree `../ta-s257` cut from `main` and its
   venv synced.
2. Review against the checklist; the PATCH bump and `uv lock`; Windows `make ci`, all steps; push the
   branch; **`make gate-ran` exits 0** from the worktree whose `HEAD` is the commit being proven; the
   branch's open CodeQL alerts compared with sprint 256's branch.
3. Merge, the tag.
4. **F1a, no cost.** With the real vendor library, from the main checkout: the merged default cap is
   accepted by `Anthropic._calculate_nonstreaming_timeout`, and 21,334 is refused.
5. **F1b, paid, on the operator's word (about $0.80 on the OpenAI account).** One real debate through the
   merged code on `gpt-5.5` with the fleet's settings, on a recorded packet, writes kept in memory: every
   turn ends normally, and each turn's output tokens and seconds are read against 16,384 and 240.
6. **Deploy:** image-only retag, on the operator's word. Then D4: `DELIBERATOR_REQUEST_TIMEOUT_SECONDS`
   to `240` on `deliberator-manager`, read before and after, every other field unchanged. The decision
   paths are read first; none is touched, so the fidelity count stays where it is. The rollback tag and
   the setting's old value are recorded.
7. **F2, the first scheduled night with a debated buy after the retag.** No completion stops on `length`;
   no order fails open on the cap or on the wait; each turn's output tokens against 16,384 and its
   seconds against 240; the debate's whole time against execution's grace (work-queue 113).

---

## Handover — paste this to Codex

```text
Sprint 257 — a debater's turn may write up to 16,384 output tokens, and the manager may wait long
enough for it. Spec: docs/sprints/sprint-257-a-debaters-turn-may-write-16384-output-tokens.md (read ALL
of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s257, on branch
sprint-257-a-debaters-turn-may-write-16384-output-tokens, cut from main after sprint 256 was merged,
with its venv synced to the lock. Work only there, never in the main checkout and never on main. You
have no .env and no network: every proof is a unit test, and no test calls an LLM. `uv run` is safe.
Do not touch pyproject.toml or uv.lock, and say so: the planner bumps the version at merge. Do not push
and do not merge: commit on the branch and hand back. Do not edit docs/STATE.md: put intent and results
in the spec's Closeout. If a make ci step cannot run in your sandbox (the dependency audit needs the
network), do not bypass it silently: name the step as NOT RUN in the handback.

This handover is complete: nobody will send you follow-up messages. Two tiers:
- A wrong command, count, path, test name or clause number whose intent is plain from the spec's Scope
  and Success factors is NOT a reason to stop: follow the intent, record the correction in Return
  notes, continue. An existing test beyond those the spec names that pins 8,192 or 120 is the same
  tier: edit it, and name it with the reason.
- STOP and report, without improvising, when: a test that compares prompt bytes or hashes fails; a law
  clause states the old numbers; making the suite pass would need a change under orchestration/packs/,
  to a prompt, or to how a call is made (streaming, effort, a per-vendor cap).

What and why: on gpt-5.5 the model's reasoning counts against the output cap. The one production debate
measured there wrote 7,738 tokens in a defender turn against a cap of 8,192, and in two experiments 5
of 25 defender turns wrote more than 8,192 (the largest 11,556). A completion cut at the cap fails its
order open: it is submitted unreviewed. No setting can raise the cap because the tunable's own upper
bound is 8,192. The planner measured the numbers this spec uses: 86 to 117 output tokens a second, so a
turn at 16,384 tokens can take about 190 seconds, and Anthropic's client refuses a non-streaming call
above 21,333 tokens.

MUST RULE before any code: read, whole, the deliberator's laws.md and test-plan.md,
docs/laws/conventions.md, docs/laws/drift-register.md, and DL-274 in docs/design-log.md. Fill the Law
reading record first. Law-cycle answer: NO. No contracts/ file and no new guarantee. Owed: the two
PARAM rows follow the code (max_tokens and request_timeout_seconds), one Changelog line naming S257 and
DL-274, and the version step the conventions ask of a PARAM-only change. Edit no clause.

Order (the spec's Steps): laws -> plant A1, A3 and A4, watch them fail, paste the red -> implement ->
PARAM rows and Changelog -> break and restore every guard -> make ci to a file.

Build (decisions D1-D3 are made; build them as written):
1. agents/deliberator/settings.py: max_tokens default 16384 and le=16384; request_timeout_seconds
   le=300.0 with its default unchanged. Each why keeps what it says and adds the measured reason from
   the spec's decision table.
2. kernel/llm_anthropic.py: NONSTREAMING_MAX_TOKENS = 21_333 with the comment the spec describes.
3. Tests A1-A5, B1 and B2 from the spec's Test plan, each citing its clause where one binds.
D4 is the planner's, at the deploy: do nothing for it.

DO NOT: edit anything under orchestration/packs/; change the effort, add streaming or a per-vendor cap;
import anthropic or openai at module level or in a test; change a prompt, a packet line, a schema, the
guided turn, the DSPy modules or the judge; touch execution's grace; import one agent from another; pin
a version number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The red output of A1, A3 and A4 pasted, from before the implementation.
 3. Test plan results: one row for each of A1-A5, B1 and B2, with file, status and clause.
 4. Every guard's break-and-restore stated, one line per guard, including a bound of 32768 for A3.
 5. The two PARAM rows as they now read, the Changelog line, and the book's version; no clause edited.
 6. This prints nothing, and you say so:
    git diff main -- pyproject.toml uv.lock orchestration/packs kernel/deliberation_prompts.py kernel/deliberation_program.py kernel/dspy_engine.py agents/deliberator/guided_turn.py agents/deliberator/context.py
 7. Every EXISTING test you edited, named, with the reason for each edit.
 8. make ci output file named, exit code stated, every NOT RUN step named with its reason.
 9. Module line counts for every touched module; Status BUILT here and in the README row.
State anything not met as "not done" or "verified failing". Never write a Result for work not done.
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
| `agents/deliberator/settings.py` and its tests | Whole `agents/deliberator/laws/laws.md` (LOCKED v1.15), whole `agents/deliberator/laws/test-plan.md`, whole `docs/laws/conventions.md`, whole `docs/laws/drift-register.md`; DL-274 read in full | `DLIB-DEP-04`, `DLIB-PERF-02`; the two `PARAM` rows | No: follow D1 and D3, keep the existing descriptions and lower bounds, and reconcile PARAM only. Recorded before the first test or source edit. |
| `kernel/llm_anthropic.py` and vendor request tests | Same whole law files and DL-274 | `DLIB-NEV-06`, `DLIB-FAIL-04`, `DLIB-DEP-03`; existing `DLIB-NEV-10` boundary | No: D2 records the measured client ceiling without importing a vendor SDK in tests or changing how calls are made. |
| Existing stop-reason, parity and hash proofs | Same whole law files and test plan | `DLIB-NEV-06`, `DLIB-OBS-03`, `DLIB-FAIL-04`, `DLIB-OUT-06`, `DLIB-IDM-02`, `DLIB-NEV-10` | No: run these unchanged; any prompt-byte or hash regression stops the sprint. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** NO. D1-D3 change an existing default and two bounds inside existing guarantees. No contract or clause edit is authorized. Owed: two PARAM rows, an S257 / DL-274 Changelog entry and the next book amendment version under conventions §4.

**Contradictions found between a law and this spec:** None. No clause fixes the cap at 8,192 or the wait at 120; those numbers occur in PARAM and historical Changelog text only.

**Laws found silent where a decision was needed:** None for D1-D3. DL-274 already decides the bounds and the client ceiling; D4 and execution's grace remain outside the build.

**Clauses that were ⬜ and are now proven:** None claimed. `DLIB-DEP-03` and `DLIB-PERF-01` are gray in the read test plan; request-argument wiring alone does not prove all of DEP-LLM, and rounds are unchanged. `DLIB-DEP-04`, `DLIB-PERF-02`, `DLIB-NEV-06` and `DLIB-OBS-03` are already green.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_the_output_cap_is_16384_and_its_law_row_agrees` | `agents/deliberator/tests/test_guided_turn_edges.py` | PASS | `DLIB-DEP-04` |
| A2 | `test_each_roles_default_cap_reaches_the_vendor_request` (both vendors × defender, challenger, judge; 6 cases) | `agents/deliberator/tests/test_output_cap_requests.py` | PASS, synthetic SDKs | `DLIB-DEP-04`, `DLIB-DEP-03` (request wiring only; full clause stays gray) |
| A3 | `test_the_cap_cannot_exceed_anthropics_nonstreaming_limit` | `agents/deliberator/tests/test_output_limits.py` | PASS | `DLIB-DEP-04`, `DLIB-NEV-06` |
| A4 | `test_the_manager_may_wait_up_to_300_seconds` | `agents/deliberator/tests/test_output_limits.py` | PASS | `DLIB-PERF-02`, `DLIB-DEP-04` |
| A5 | `test_one_stopped_turn_fails_only_that_order_and_records_reason`; `test_manager_fail_open_records_visible_rationale`; vendor stop-reason tests | `agents/deliberator/tests/test_stop_reason_fail_open.py`, `test_fail_open_reason.py`, `test_llm_openai_adapter.py`; `tests/test_deliberator_anthropic.py` | PASS, existing tests unchanged | `DLIB-NEV-06`, `DLIB-OBS-03`, `DLIB-FAIL-01`, `DLIB-FAIL-04`, `DLIB-NEV-07` |
| B1 | `test_a_served_turn_runs_dspy_and_sends_mains_text`; `test_served_records_equal_main`; `test_role_system_text_is_reused_and_has_mains_hash`; ledger hash and output-bound tests | `agents/deliberator/tests/test_dspy_runtime.py`, `test_dspy_turn_parity.py`, `test_llm_output_bounds.py`; `tests/test_llm_ledger_provenance.py`, `test_deliberation_guided.py`, `test_deliberation_guided_text.py` | PASS, existing tests unchanged | `DLIB-OUT-06`, `DLIB-OBS-06`, `DLIB-IDM-02`, `DLIB-OBS-07` |
| B2 | `uv run python scripts/check_param_law_sync.py` | `scripts/check_param_law_sync.py` (unchanged) | PASS, exit 0; numeric limits independently pinned by A1/A4 (DL-275) | PARAM gate; no functional-test docstring |

**Tests added beyond the plan:** None. The six A2 cases cover each existing role on each vendor. The existing default/ceiling test also retains the 64-token minimum pin.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s257`, on the named sprint branch; `.env` absent. Unit proofs only, Python 3.13.2; UV offline. For mutations and final CI, `.tools/s257/offline/sitecustomize.py` blocks external DNS/TCP/UDP while allowing loopback IPC. No live LLM call.

**INTENT (recorded before code):** Work only in `C:\Users\yury_\Downloads\project\ta-s257`, branch `sprint-257-a-debaters-turn-may-write-16384-output-tokens`; clean starting HEAD and `origin/main` both `7309b858d0d19cab77f58c5edba859c557da1da0`, `.env` absent. Plant and record A1/A3/A4 red, implement D1-D3, reconcile PARAM without clause edits, break and restore every guard, run offline unit proofs and redirected CI, then commit locally. Success factors are the checklist above. `docs/STATE.md`, package version files, packs, prompts, schemas and call mechanics are excluded; no push, merge, deploy or live proof.

**Result:** BUILT D1-D3 as written: default and maximum output cap 16,384; Anthropic client ceiling recorded as 21,333 with its measured derivation; manager wait maximum 300 seconds with the default still 30. A1/A3/A4 were red before implementation; A1-A5/B1/B2 pass; 17 guard plants failed and restored. Final full pytest: **4,330 passed, 8 existing skips, 100.00 % coverage**. Fourteen available CI checks passed; the full `make ci` gate is **verified failing, exit 2** solely at the unavailable online dependency audit, named NOT RUN to completion. Both following security checks passed separately. No clause, contract, prompt or call-mechanics change; package version and lock untouched.

**Files changed:**

- `agents/deliberator/laws/laws.md`
- `agents/deliberator/laws/test-plan.md`
- `agents/deliberator/settings.py`
- `agents/deliberator/tests/test_guided_turn_edges.py`
- `agents/deliberator/tests/test_llm_provider.py`
- `agents/deliberator/tests/test_output_cap_requests.py`
- `agents/deliberator/tests/test_output_limits.py`
- `docs/design-log.md`
- `docs/sprints/INDEX.md`
- `docs/sprints/README.md`
- `docs/sprints/sprint-257-a-debaters-turn-may-write-16384-output-tokens.md`
- `kernel/llm_anthropic.py`

**Design decisions:** D1-D3 built as [`DL-274`](../design-log.md); D4 remains the planner's. [`DL-275`](../design-log.md) records the observed PARAM-gate limitation and the scoped numeric proof, including the rejected global-checker change.

**Proof — the red run first:**

```text
uv run pytest --no-cov -q agents/deliberator/tests/test_guided_turn_edges.py::test_the_output_cap_is_16384_and_its_law_row_agrees agents/deliberator/tests/test_output_limits.py
FFF                                                                      [100%]
================================== FAILURES ===================================
_____________ test_the_output_cap_is_16384_and_its_law_row_agrees _____________
agents\deliberator\tests\test_guided_turn_edges.py:124: in test_the_output_cap_is_16384_and_its_law_row_agrees
    assert DeliberatorSettings().max_tokens == 16384
E   AssertionError: assert 8192 == 16384
E    +  where 8192 = DeliberatorSettings(role='manager', instance_name='', max_rounds=2, debate_concurrency=4, llm_provider='anthropic', de...s=30.0, poll_interval_seconds=60, proponent_identity='deliberator-proponent', opponent_identity='deliberator-opponent').max_tokens
E    +    where DeliberatorSettings(role='manager', instance_name='', max_rounds=2, debate_concurrency=4, llm_provider='anthropic', de...s=30.0, poll_interval_seconds=60, proponent_identity='deliberator-proponent', opponent_identity='deliberator-opponent') = DeliberatorSettings()
__________ test_the_cap_cannot_exceed_anthropics_nonstreaming_limit ___________
agents\deliberator\tests\test_output_limits.py:24: in test_the_cap_cannot_exceed_anthropics_nonstreaming_limit
    assert ceiling == 600 * 128_000 // 3_600
E   assert None == ((600 * 128000) // 3600)
_________________ test_the_manager_may_wait_up_to_300_seconds _________________
agents\deliberator\tests\test_output_limits.py:32: in test_the_manager_may_wait_up_to_300_seconds
    settings = DeliberatorSettings(request_timeout_seconds=300.0)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\pydantic_settings\main.py:262: in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
E   pydantic_core._pydantic_core.ValidationError: 1 validation error for DeliberatorSettings
E   request_timeout_seconds
E     Input should be less than or equal to 120 [type=less_than_equal, input_value=300.0, input_type=float]
E       For further information visit https://errors.pydantic.dev/2.13/v/less_than_equal
=========================== short test summary info ===========================
FAILED agents/deliberator/tests/test_guided_turn_edges.py::test_the_output_cap_is_16384_and_its_law_row_agrees
FAILED agents/deliberator/tests/test_output_limits.py::test_the_cap_cannot_exceed_anthropics_nonstreaming_limit
FAILED agents/deliberator/tests/test_output_limits.py::test_the_manager_may_wait_up_to_300_seconds
3 failed in 11.05s
EXIT_CODE=1
```

A1, A3 and A4 failed before any settings, adapter or PARAM edit. Captured in `.tools/s257/red.txt` and pasted here before implementation.

**Proof — the green run:**

Focused A1-A5/B1 run, `.tools/s257/green.txt`:

```text
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 61%]
........................................................................ [ 81%]
................................................................         [100%]
352 passed in 20.33s
EXIT_CODE=0
```

B2, `.tools/s257/param-sync.txt`:

```text
uv run python scripts/check_param_law_sync.py
[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 — UCITS investment powers and limits
[WARN] portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later
PARAM_SYNC_EXIT_CODE=0
```

**Guards planted:** 17 plants, each red (exit 1) then restored green (exit 0), with original bytes restored in a `finally` block. Complete local traces: `.tools/s257/guards-complete.txt`; initial numeric-gate survivor retained separately in `.tools/s257/guards-initial.txt`. One line per guard:

- G01 A1: cap default reverted to 8,192 → red → restored.
- G02 A1: ceiling lowered to 16,383, refusing the legal endpoint → red → restored.
- G03 A1/A3: ceiling raised to **32,768** → both red → restored.
- G04 A3: upper bound removed → red → restored.
- G05 existing ceiling test: cap minimum changed from 64 to 63 → red → restored.
- G06 A1: `gpt-5.5` removed from the measured reason → red → restored.
- G07 A1: numeric PARAM default and ceiling reverted to 8,192 → red → restored. B2's numeric blind spot was separately observed (DL-275), not counted as red.
- G08 A2: OpenAI request cap fixed at 8,192 → 3 red / 3 passing vendor cases → restored all 6 green.
- G09 A2: Anthropic request cap fixed at 8,192 → 3 red / 3 passing vendor cases → restored all 6 green.
- G10 A3: client constant raised from 21,333 to 21,334 → red → restored.
- G11 A4: wait default changed from 30 to 31 → red → restored.
- G12 A4: ceiling lowered to 299, refusing 300 → red → restored.
- G13 A4: ceiling raised to 301, accepting 300.1 → red → restored.
- G14 A4: measured `190`-second reason changed to `180` → red → restored.
- G15 A4: numeric wait PARAM bound reverted to 120 → red → restored.
- G16 A4: manager forwarding replaced with a fixed 120-second wait → red → restored.
- G17 B2: the cap's Tunable cell changed from YES to NO → checker exit 1 → restored exit 0.

A5 and B1 are existing proofs run without mutation; no prompt-byte or hash test failed. Raw completion lines from the guard runs:

```text
RED_THEN_RESTORED G01 A1 default 8192
RED_THEN_RESTORED G02 A1 legal endpoint refused
RED_THEN_RESTORED G03 A1/A3 bound 32768
RED_THEN_RESTORED G04 A3 no upper bound
RED_THEN_RESTORED G05 existing cap minimum changed
RED_THEN_RESTORED G06 A1 measured reason removed
RED_THEN_RESTORED G07 A1/B2 cap PARAM old
RED_THEN_RESTORED G08 A2 OpenAI cap 8192
RED_THEN_RESTORED G09 A2 Anthropic cap 8192
RED_THEN_RESTORED G10 A3 client constant 21334
RED_THEN_RESTORED G11 A4 default wait 31
RED_THEN_RESTORED G12 A4 legal wait refused
RED_THEN_RESTORED G13 A4 excess wait accepted
RED_THEN_RESTORED G14 A4 measured rate reason changed
RED_THEN_RESTORED G15 A4/B2 wait PARAM old
RED_THEN_RESTORED G16 A4 configured wait not forwarded
RED_THEN_RESTORED G17 B2 tunable declaration mismatch
TOTAL_RED_THEN_RESTORED=17
```

**Existing tests edited:**

- `agents/deliberator/tests/test_guided_turn_edges.py::test_the_output_cap_is_8192_and_its_law_row_agrees` → `test_the_output_cap_is_16384_and_its_law_row_agrees` (A1): replace the old default and PARAM pin; add acceptance/refusal and measured-reason pins; retain the S246 `3,026` assertion.
- `agents/deliberator/tests/test_llm_provider.py::test_max_tokens_default_is_its_own_ceiling`: the old assertions pinned 8,192; pin the new default and maximum at 16,384 while retaining the 64-token minimum, and cite `DLIB-DEP-04` in the updated explanation.

No other existing test function was edited. A5 and B1 ran unchanged. The test-plan rows add references without moving any clause's status.

**The `PARAM` rows, the Changelog line and the book's version:** LOCKED v1.16 (read v1.15 after S256; one PARAM-only amendment).

```text
| `max_tokens` | `16384` | int >= 64 <= 16384 | YES | Per-call response cap; S246 raised it for the guided readings written before each debater's argument (challenger max 3,026 output tokens before them, DL-252 D8); on gpt-5.5 reasoning counts against the cap, a defender reached 7,738 tokens in production and 11,556 in the typed turn, and the unused cap costs nothing (DL-274 D1) |
| `request_timeout_seconds` | `30.0` | float >= 1 <= 300 | YES | Bounds peer RPC wait; a turn at the cap can take about 190 seconds at the slowest measured output rate on gpt-5.5 (DL-274 D3) |
+ v1.16 -- S257 / DL-274 (2026-10-08). PARAM-only: `max_tokens` defaults to
  16,384 with the same ceiling, below Anthropic's 21,333 non-streaming limit;
  `request_timeout_seconds` may reach 300, still defaulting to 30. Measured
  gpt-5.5 reasoning needs the cap and can take about 190 seconds at it. No clause changes.
```

Clauses and the capability declaration are unchanged, compared byte for byte with `main`; both original `why` texts remain exact prefixes of their new descriptions. No contract file changed.

**Module line counts:** every touched module is below the 200-line block.

```text
agents/deliberator/settings.py: 164 lines
kernel/llm_anthropic.py: 162 lines
agents/deliberator/tests/test_guided_turn_edges.py: 130 lines
agents/deliberator/tests/test_llm_provider.py: 156 lines
agents/deliberator/tests/test_output_limits.py: 62 lines
agents/deliberator/tests/test_output_cap_requests.py: 70 lines
```

**`make ci`:** ran twice, redirected to a file, never piped. Final output: `C:\Users\yury_\Downloads\project\ta-s257\ci.txt`; **exit 2**, 4,330 passed / 8 existing skips / 100.00 % coverage. Initial full output is preserved in `.tools/s257/ci-initial.txt`; the final rerun follows the synthetic-key scanner correction and is the handback proof. External networking was blocked; no LLM was called.

| Step | Check | Actual result |
| --- | --- | --- |
| 1 | ruff | PASS |
| 2 | format | PASS |
| 3 | mypy | PASS |
| 4 | import-linter | PASS |
| 5 | module size | PASS |
| 6 | module header | PASS |
| 7 | law coverage | PASS |
| 8 | PARAM/settings sync | PASS; numeric proof is A1/A4, DL-275 |
| 9 | sprint status | PASS |
| 10 | markdown links | PASS |
| 11 | version scheme | PASS |
| 12 | pytest / 100.00 % floor | PASS; 4,330 passed, 8 existing skips |
| 13 | dependency audit (`scripts/check_dependency_audit.py`, pip-audit) | NOT RUN to completion: online advisory lookup blocked by the no-network proof guard; attempted and failed |
| 14 | detect-secrets | PASS, exit 0; run separately after the target stopped at step 13 |
| 15 | untracked secrets | PASS, exit 0; run separately after the target stopped at step 13 |

Actual output excerpts from the final `ci.txt` (full output remains in the named file):

```text
make ci > ci.txt 2>&1
uv run ruff check . --output-format=github
uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
uv run lint-imports
uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts
uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts
uv run python scripts/check_law_coverage.py
uv run python scripts/check_param_law_sync.py
uv run python scripts/check_sprint_status.py
uv run python scripts/check_markdown_links.py
uv run python scripts/check_version_scheme.py
uv run pytest
uv run python scripts/check_dependency_audit.py
Success: no issues found in 1165 source files
Contracts: 5 kept, 0 broken.
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: S257 offline proof: external DNS is disabled"))
make: *** [Makefile:59: ci] Error 1
TOTAL                                                           20066      0   4240      0  100.00%
========= 4330 passed, 8 skipped, 2470 warnings in 399.46s (0:06:39) ==========
FINAL_MAKE_CI_EXIT_CODE=2
```

The target stopped before its final two checks; these were run explicitly, with new tests already staged, and no tracked edits while pre-commit scanned:

```text
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
FINAL_DETECT_SECRETS_EXIT_CODE=0
uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
FINAL_UNTRACKED_SECRETS_EXIT_CODE=0
```

Security logs: `.tools/s257/detect-secrets.txt`, `.tools/s257/untracked-secrets.txt`. `.secrets.baseline` is unchanged. A1-A5/B1/B2 have no skipped case; the eight full-suite skips and their reasons are pasted above.

**Scope proof:** the exact required command printed nothing; the measured stdout was empty. `pyproject.toml` and `uv.lock` were not touched. Packs, prompts, packet builder, guided turn, DSPy modules, contracts and `docs/STATE.md` were not touched. Mutation-only changes to `kernel/llm_openai.py` and the entrypoint were restored.

```text
git diff main -- pyproject.toml uv.lock orchestration/packs kernel/deliberation_prompts.py kernel/deliberation_program.py kernel/dspy_engine.py agents/deliberator/guided_turn.py agents/deliberator/context.py
STDOUT_BYTES=0
EXIT_CODE=0
Extra exclusions and mutation-only files: STDOUT_BYTES=0 EXIT_CODE=0
CLAUSES_AND_CAPABILITY_UNCHANGED=YES
BOTH_EXISTING_WHY_TEXTS_PRESERVED=YES
NEW_TESTS_IMPORT_NO_VENDOR_SDK=YES
```

**`make gate-ran`:** owed by the planner at merge; not run here (no push / no network).

**Not met / verified failing:**

- **Verified failing:** overall `make ci` exit 2; dependency audit **NOT RUN to completion** because its online PyPI/advisory lookup requires the network. No clean vulnerability result is claimed. The other 14 checks passed, including the separately invoked security tail.
- **Verified failing spec assumption:** B2 does not compare numeric Value/Type cells. A1 and A4 catch both old rows; G17 proves the check B2 really enforces. The shared checker was not changed (DL-275).
- **Not done, planner-owned:** PATCH bump / lock, push, exact-SHA remote gate, CodeQL comparison, merge/tag, image build, retag/D4 and F1a/F1b/F2. No deployment or live model proof is claimed.
- **Not done under the read-only umbrella scope:** central law-rollup version labels still v1.15; the amended book is v1.16 with the same 32 / 63 clause count. The two labels can be reconciled at merge; no law clause or rollup count changed.

---

## Return notes

- Corrected the spec's PARAM-gate claim, without widening the checker: with the old numeric cap row planted, A1 failed but B2 exited 0. `ParamRow` parses only name and Tunable; A1/A4 now provide the exact numeric-row proof required by the scope. DL-275 records the finding, the chosen scoped proof and the rejected global-checker change. B2's own declaration-mismatch plant did fail and restore.
- Re-counted the actual `ci:` target: **15** steps, including sprint status. AGENTS.md's short form says 14; CLAUDE.md and the Makefile are the current reference. No rule file was edited.
- The two existing 8,192 pins named under Traps were the only existing tests edited. No additional existing test pinned the old wait bound. A5 and B1 were not edited; no prompt-byte or hash failure occurred.
- Detect-secrets initially rejected the A2 test's literal synthetic credential as a Secret Keyword false positive (`.tools/s257/detect-secrets-initial.txt`). Changed it to the existing single-character fixture convention, `api_key="k"`; no real credential, baseline change or allowlist. The final six request cases passed (`.tools/s257/final-request-tests.txt`); full CI and secrets checks were rerun on that final test file.
- One scanner rerun reported `files were modified` because the builder edited this handover while the scan was running (`.tools/s257/detect-secrets-concurrent-doc-edit.txt`). No hook mutation remained in the diff. Holding the tracked tree steady for the final scan yielded exit 0; the baseline is unchanged.
- The locked book advanced from S256's **v1.15 to v1.16**, PARAM-only. Central law version labels in `docs/laws/INDEX.md` and `docs/laws/ledger.md` still say v1.15; those umbrella files were left read-only under MUST RULE. The planner can reconcile their version labels at merge; the clause count stays **32 / 63**, and no clause status moves.
- `pyproject.toml` and `uv.lock` were not touched; the planner owes the PATCH bump and lock reconciliation at merge. `docs/STATE.md` was not edited, by the handover; intent and results live here. No package version was pinned.
- No push, remote gate, merge, image build, deployment or live/vendor-library proof was performed. The planner owes `make gate-ran` on the final bumped SHA, the S256 CodeQL comparison, F1a/F1b, retag/D4 with the before/after snapshot, and F2. No paid call or live app setting was changed. The fleet's pack wait remains 120; the code default remains 30 and the allowed maximum is now 300.

---

## Planner's review and merge-time work — 2026-10-08 16:20 AEDT

**The handback against the checklist.** All nine items are met. Item 8 names one step as NOT RUN, the
dependency audit, which needs the network; the planner runs the whole gate below.

**Re-measured by the planner, not read from the builder's logs.**

- The scope command of item 6 prints nothing. Neither does the same diff over `contracts/`,
  `orchestration/`, `surfaces/`, `scripts/`, `infra/`, `.github/`, the `Makefile`, `.secrets.baseline` and
  `docs/STATE.md`. Twelve files changed: two modules, two edited tests, two new tests, the law book and its
  test plan, and four documents.
- Eight plants of the planner's own, one at a time, each red, each restored: the default back at 8,192
  (7 tests fail), a bound of 32,768 (2), the client constant at 21,334 (1), a wait bound of 301 (1), the
  manager forwarding a fixed 120 seconds (1), OpenAI's request cap fixed at 8,192 (3 of the 6 request
  cases), the cap's law row back at 8,192 (1), the wait's law row back at 120 (1). The nine tests of the
  sprint are green before and after, and the tree is clean.
- A ninth plant is DL-275's own: with the cap's law row back at 8,192, `scripts/check_param_law_sync.py`
  exits 0. The builder's finding is right.
- The two existing tests the builder edited are the two the spec named. Each edit was read: both assert
  the new numbers in place of the old, the 64-token minimum and the `3,026` sentence are still pinned, and
  neither is weakened.
- The code is the decided design, D1 to D3, nothing more: one default, two bounds, two `why` texts that
  keep their old sentence, one constant with its derivation.

**The planner's error, found by the builder.** This spec says the parameter step of `make ci` fails until
the two `PARAM` rows follow the code, and offers the prototype's pass as the measurement. The step was run
only with the rows already changed; the failing direction was never run. The step compares a row's name
and its Tunable cell, not its Value or its Type (DL-275). A1 and A4 hold the numbers instead. The gap in
the shared check is filed as work-queue 114.

**Changed by the planner at merge.**

- The version is `0.123.02`. `uv lock` changed the version line only; 180 packages before and after.
- The deliberator's row in `docs/laws/INDEX.md` and in `docs/laws/ledger.md` reads v1.16 (S257, DL-274),
  `PARAM` only, 32 / 63 unchanged. The builder left both files alone, as the MUST RULE told it to.
- `main` had not moved since the worktree was cut, so nothing was merged in.

**Accepted as built.**

- `NONSTREAMING_MAX_TOKENS` is read by a test and by no production code: the setting's bound is the
  literal 16,384, and the test holds it at or under the constant. That is D2 as decided.
- A3 reads the constant with `getattr(..., None)`, which let it fail on an assertion before the constant
  existed. With the constant in place it is an ordinary read.
- The builder took DL-275. The next free entry is DL-276.

**Owed, in the order of "Sequencing after merge":** the gate on Windows and on the remote for the merged
SHA, the merge, F1a with the real vendor library, F1b on the operator's word, the deploy and D4 on the
operator's word, F2. Their results are recorded in `docs/STATE.md` and in this file's Status line.
