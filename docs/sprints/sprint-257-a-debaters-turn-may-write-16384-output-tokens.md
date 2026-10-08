<!-- Agent: planning | Role: sprint handover -->
# Sprint 257 — A debater's turn may write up to 16,384 output tokens, and the manager may wait long enough for it

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-257-a-debaters-turn-may-write-16384-output-tokens`
**Status:** SPEC
**Version:** *next available PATCH at merge*
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

- [ ] The default cap is 16,384, and a setting above 16,384 is refused (A1).
- [ ] Both vendors' requests carry the cap from the settings (A2).
- [ ] The cap's upper bound cannot pass what Anthropic's client accepts without streaming (A3).
- [ ] The wait can be set to 300 seconds and no higher; its default is unchanged (A4).
- [ ] A completion cut at the cap still fails its order open and says so (A5).
- [ ] No prompt, packet line or schema changes (B1).
- [ ] The two `PARAM` rows follow the code; no clause is edited.
- [ ] `pyproject.toml`, `uv.lock` and `orchestration/packs/` are untouched.
- [ ] Every new guard planted, watched to fail, restored, stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage, or each step that could not run named as NOT RUN.

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
| _to be filled by the builder_ | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** _to be filled_

**Contradictions found between a law and this spec:** _to be filled_

**Laws found silent where a decision was needed:** _to be filled_

**Clauses that were ⬜ and are now proven:** _to be filled_

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | _to be filled_ | | | |

**Tests added beyond the plan:** _to be filled_

---

## Closeout — evidence

**Status:** _to be filled: BUILT_

**Tree the proofs ran in (and `.env` present?):** _to be filled_

**Result:** _to be filled_

**Files changed:** _to be filled_

**Design decisions:** recorded as [`DL-274`](../design-log.md); _anything the builder added, to be filled_

**Proof — the red run first:**

```text
to be filled
```

**Proof — the green run:**

```text
to be filled
```

**Guards planted:** _to be filled, one line per guard_

**Existing tests edited:** _to be filled, one line per test with the reason_

**The `PARAM` rows, the Changelog line and the book's version:** _to be filled_

**Module line counts:** _to be filled_

**`make ci`:** _to be filled: the output file, the exit code, passed and skipped, coverage, each NOT RUN step_

**`make gate-ran`:** owed by the planner at merge.

**Not met / verified failing:** _to be filled_

---

## Return notes

- _to be filled by the builder_
