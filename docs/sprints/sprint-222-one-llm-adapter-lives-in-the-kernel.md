<!-- Agent: planning | Role: sprint handover — the vendor LLM adapters move into the kernel -->
# Sprint 222 — one LLM adapter lives in the kernel

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-222-one-llm-adapter-lives-in-the-kernel`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** work-queue item **7** · `DL-191` (next free at spec time — re-check it at merge) · [DL-101](../design-log.md) filed the split · DL-100 fixed the per-provider model default

> **Why this bump kind.** PATCH. Nothing gains a capability: the same two agents call the same two
> vendors with the same guarantees. Code moves, duplication goes, and one import stops crossing a
> boundary it should not. That is a refactor.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/deliberator/laws/laws.md` + `test-plan.md` | The deliberator's locked constitution | Read-only. `DLIB-OUT-05`, `DLIB-FAIL-04`, `DLIB-SEC-02` and `DLIB-OBS-05` all describe behaviour that lives in the code you are moving |
| `agents/operator/laws/laws.md` + `test-plan.md` | The operator's locked constitution | Read-only. `OPR-SEC-01` and `OPR-DEP-01` bind here |
| `docs/laws/conventions.md`, `docs/laws/drift-register.md` | Conventions and drift rows | `drift-register.md` is the one law-adjacent file you may append to |

Binding clauses: **`DLIB-OUT-05`**, **`DLIB-FAIL-04`**, **`DLIB-SEC-02`**, **`DLIB-OBS-05`**,
**`OPR-SEC-01`**, **`OPR-DEP-01`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each agent's `test-plan.md` beside its `laws.md`. The clauses above are **green today**; a
   regression here **un-proves a green clause**, which is worse than a new bug.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below** before step 5.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring**.

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No, and holding that "No" is a scope rule, not an observation.** `contracts/` is untouched. Both
agents keep exactly the guarantees they have: the deliberator still selects its provider by tunable,
the operator still calls Anthropic, and no agent holds an API key. **Where the code lives is not a
guarantee.**

🚨 **The moment you give the operator a provider choice, the answer becomes Yes** — `OPR-DEP-01`
names *"Anthropic Claude (or injected `FakeLLMClient`)"* as its sole external call, so a second vendor
is a new dependency, a new tunable, a PARAM row and an operator law cycle. **That is explicitly out of
scope** (see Out of scope). If you believe the move cannot be done without it, stop and report.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/deliberator/llm_anthropic.py` (**129** lines) | deliberator `laws.md` + `test-plan.md` | `DLIB-OUT-05` records the provider stop reason; `DLIB-FAIL-04` turns a truncated or refused completion into an error, not an empty answer (S189) |
| `agents/deliberator/llm_openai.py` (**126**) | same | Same two clauses, other vendor |
| `agents/deliberator/llm_factory.py` (**89**) | same | Provider selection and the per-provider default model (DL-100) |
| `agents/operator/llm_anthropic.py` (**103**) | operator `laws.md` + `test-plan.md` | `OPR-SEC-01` — the client is injected and the operator holds no keys; `OPR-DEP-01` — Anthropic is its sole external call |
| `surfaces/dashboard/chat_binding.py:13` | operator `laws.md`; `docs/laws/conventions.md` | It imports `AnthropicLLMClient, ConfigurationError` **out of an agent's internals** — the import this sprint removes |
| `kernel/llm.py` (**80**), `kernel/llm_ledger.py` (**153**), `kernel/llm_tokens.py` | conventions | The port, the `LLMCall` ledger and token accounting are already kernel; the adapters are joining them, not replacing them |

⚠️ **The one invariant this sprint must not break: the API key never appears anywhere but the
request.** `DLIB-SEC-02` and `OPR-SEC-01` say it is never logged, never a graph prop, never in an
exception. Moving code between modules is exactly how a key ends up in a new log line or a reraised
message. S189 already ships a sentinel-based test for this shape — reuse that pattern, do not invent one.

---

## Goal

At merge there is **one** Anthropic adapter and **one** OpenAI adapter in the repository, both in
`kernel/`, reached through one factory in `kernel/`. `agents/deliberator/llm_anthropic.py`,
`agents/deliberator/llm_openai.py`, `agents/deliberator/llm_factory.py` and
`agents/operator/llm_anthropic.py` no longer exist. `surfaces/dashboard/chat_binding.py` imports from
`kernel`, not from an agent. Every clause listed above is still green, and no agent gained or lost a
capability.

## Why (context)

The port (`kernel/llm.py`) and the `LLMCall` ledger (`kernel/llm_ledger.py`) are kernel. The **vendor
adapters and the factory are not** — they live inside two agents, in two copies, and the copies have
already drifted apart. The measured consequence the row was filed for: S168's OpenAI provider option
reached only the deliberator, because the operator's copy has no factory at all.

🪤 **Do not re-justify this sprint on the 2026-08-19 or 2026-08-20 outages.** A provider switch only
helps if some provider has credit, and both vendors ran dry inside three days ([DL-125](../design-log.md)).
The case for this work is duplication and a boundary violation, not availability.

### Measured, 2026-09-21 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Adapter copies | `agents/deliberator/llm_anthropic.py` **129** lines, `agents/operator/llm_anthropic.py` **103** | `wc -l` |
| 🚨 Are the two copies identical? | **No** | `diff` — see the trap below |
| Deliberator-only files | `llm_openai.py` **126**, `llm_factory.py` **89** | `wc -l` |
| Operator has a factory | **No** — it constructs `AnthropicLLMClient` directly | `grep` over call sites |
| Surface reaching into an agent | `surfaces/dashboard/chat_binding.py:13` imports `AnthropicLLMClient, ConfigurationError` from `agents.operator.llm_anthropic`, used at `:34` | `grep` |
| Other call sites to repoint | `agents/deliberator/entrypoint.py:80,90`; `scripts/deliberate.py:177` | `grep` over `agents surfaces orchestration scripts`, tests excluded |
| Kernel already owns | `kernel/llm.py` **80** (`LLMClient` Protocol, `LLMCompletionStoppedError`, `llm_stop_reason`, `FakeLLMClient`), `llm_ledger.py` **153**, `llm_tokens.py` | `ls`, `grep` |

🚨 **The single most important measurement: the two "duplicate" adapters are not duplicates.**
The deliberator's adapts **free-text completions** and carries the S189 stop-reason handling
(`STOP_REASON_UNKNOWN`, `LLMCompletionStoppedError`). The operator's adapts **tool-use responses** and
imports `json` to parse them. They share transport, configuration, key handling and error mapping;
they differ in how they read the response. A refactor that deletes one and points both at the other
**breaks the operator's tool calling**, and the unit tests most likely to catch it are the operator's.

---

## Scope — and what is deliberately NOT here

1. **Plant the failing test first.** A test asserting that **no module under `agents/` or `surfaces/`
   defines or imports a vendor adapter** — it fails today, on four files. Watch it fail, paste the red
   output. This test is also the guard that stops the split reappearing.
2. **`kernel/llm_anthropic.py`** — one Anthropic client carrying what both copies share: configuration
   and key handling, the HTTP call, error mapping, stop-reason capture, and the `ConfigurationError`
   that `chat_binding.py` imports today. The **response shapes stay distinguishable**: expose the
   free-text path and the tool-use path as two named entry points on one client, or as two thin
   classes over one transport. Name your choice and your rejected alternative in the design log.
3. **`kernel/llm_openai.py`** — the moved OpenAI client, unchanged in behaviour.
4. **`kernel/llm_factory.py`** — the moved factory, with `KEY_ENV`, `DEFAULT_MODEL`,
   `UnknownProviderError`, `build_llm` and `key_env_var`.
   🚨 **Preserve its docstring's rule verbatim in substance:** *the provider is a tunable, not a
   fallback chain.* An automatic silent switch makes "which model reviewed this order" unanswerable,
   and DL-100 records the worse failure — a switch that carries the other vendor's model name stamps a
   false model on the `DeliberationRun`. The per-provider `DEFAULT_MODEL` exists for exactly that.
5. **Delete the four agent-side files** and repoint every call site: `agents/deliberator/entrypoint.py`
   (`:80`, `:90`), `scripts/deliberate.py` (`:177`), `surfaces/dashboard/chat_binding.py` (`:13`, `:34`),
   and the operator's own construction path.
6. **Move the tests with the code.** The existing adapter tests are the proof these clauses are green;
   they move to `tests/` against the kernel modules and keep citing their clause IDs.
7. **Coverage.** `kernel/` is in the coverage source list, so the moved code must stay at **100 %**.

### Out of scope (do NOT build this sprint)

- 🚨 **Giving the operator a provider choice.** That is a new dependency under `OPR-DEP-01`, a new tunable, a PARAM row and an operator law cycle. It becomes trivial *after* this sprint, and it gets its own.
- **Any change to what either agent sends or how it reads a verdict.** Prompts, roles, models, effort, token budgets and retry behaviour are all untouched.
- **Any change to `kernel/llm_ledger.py` or `kernel/llm_tokens.py`.** They already work; this sprint moves callers, not the ledger.
- **`FakeLLMClient`.** It stays exactly where it is and keeps its behaviour — tests and `run_local.py` depend on it.
- **No `contracts/` change. No law amendment.** If you think one is owed, stop and report.

### The road not taken (LAW-06)

- **Delete one adapter and point both agents at the survivor.** Rejected on measurement: they are not duplicates — free-text versus tool-use — so this silently breaks the operator.
- **Leave the adapters in the agents and only fix the `chat_binding` import.** Rejected: it treats the symptom. The duplication is why a provider option reached one agent and not the other.
- **Introduce a vendor fallback chain while the code is open.** Rejected, and this is the one that would look like an improvement: attribution is the point of the veto, and a silent switch destroys it (DL-100).
- **Put the adapters in `contracts/`.** Rejected: `contracts/` is typed DTOs, and `kernel` is where the port and ledger already live.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **How free-text and tool-use stay distinguishable** over one transport — two entry points, or two thin classes. Name what you rejected and why.
2. **Where `ConfigurationError` lives** now that a surface imports it — and what that means for anything else currently importing it from an agent.
3. **What the new guard test asserts** — "no vendor adapter outside `kernel/`" needs a precise, non-brittle definition. Say what would make it fire falsely.

🪤 **Take the next free DL number, then re-check it at merge.** The log has historic duplicates and
entries are prepended *and* appended. `DL-190` is taken (S221).

---

## Blast radius — measured 2026-09-21

| What | Detail |
| --- | --- |
| Files changed | 4 agent files **deleted**; `kernel/llm_anthropic.py`, `kernel/llm_openai.py`, `kernel/llm_factory.py` **new**; `agents/deliberator/entrypoint.py`, `agents/operator/*` construction path, `surfaces/dashboard/chat_binding.py`, `scripts/deliberate.py` repointed; adapter tests moved |
| Agents affected | `deliberator`, `operator` — 🪤 confirm neither imports the other (`import-linter`) |
| Contract change? | **No** |
| Graph vocabulary change? | **No** |
| New env keys / tunables | **None.** `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` keep their names and meanings |
| Deploy implication | 🟠 **Image-only retag.** Agent code changes, so images rebuild — but no injected pack, no env key and nothing under `infra/` moves, so this is **not** a full `up`. |

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 No vendor adapter outside `kernel/` | the repo tree | fails today on 4 files; passes at merge — and is specific enough not to fire on a comment |
| A2 | 🪤 The operator's tool-use parsing still works | a recorded tool-use response | the operator reads the tool call exactly as before |
| A3 | 🪤 The deliberator's stop-reason path still works | `finish_reason=length`, and a refusal | `LLMCompletionStoppedError` raised, `stop_reason` recorded — `DLIB-FAIL-04`, `DLIB-OUT-05` |
| A4 | 🪤 No automatic provider switch | provider `anthropic`, the call fails | nothing calls OpenAI; the failure surfaces — a fallback chain must be impossible, not merely absent |
| A5 | 🪤 The key never escapes | a sentinel key value | it appears in no log, exception, `LLMCall`, graph prop or fault — `DLIB-SEC-02`, `OPR-SEC-01`; reuse S189's sentinel pattern |
| A6 | 🎯 The surface no longer reaches into an agent | `surfaces/dashboard/chat_binding.py` | it imports the client and `ConfigurationError` from `kernel`; a test asserts no `surfaces/` module imports `agents.*.llm_*` |
| A7 | Per-provider default model is preserved | provider with no model named | anthropic → `claude-opus-5`, openai → `gpt-5.5`; never the other vendor's name (DL-100) |
| A8 | `FakeLLMClient` is unchanged | existing users | `run_local.py` and the existing suites still pass against it |
| A9 | Layering holds | `import-linter` | `kernel` imports nothing from `contracts`, `agents`, `orchestration` or `surfaces` |

---

## Success factors

- [ ] `agents/deliberator/llm_anthropic.py`, `llm_openai.py`, `llm_factory.py` and `agents/operator/llm_anthropic.py` are **deleted**, and A1 would fail if any came back.
- [ ] Both agents reach their vendor through one kernel factory; the operator still calls Anthropic only.
- [ ] `surfaces/dashboard/chat_binding.py` imports nothing from `agents.*`'s adapter internals.
- [ ] Every clause in the law map is still green, with its test citing the clause ID.
- [ ] No new tunable, no PARAM row, no law amendment — or the sprint stopped and reported.
- [ ] Design decisions recorded with rejected alternatives.
- [ ] Every new guard planted, watched to fail, restored — stated per guard.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage, redirected to a file. 🪰 Your bump must satisfy `check_version_scheme.py` — a PATCH here is `0.103.02`, not `0.103.2`.

---

## Traps

🪤 **They are not duplicates.** Free-text versus tool-use. The deliberator's copy carries S189's
stop-reason handling; the operator's imports `json` to read tool calls. Collapsing them by deleting
one is the obvious move and it is wrong.

🪤 **The provider is a selection, not a fallback.** Having all the vendors in one module makes a
fallback chain a two-line temptation. A4 exists to make it impossible rather than merely absent —
attribution is the point of the veto (DL-100).

🪤 **A key leaks during a move, not during a design.** A reraise that adds context, a debug log added
while porting, a `repr()` of a config object — all of them put the key somewhere new.
`DLIB-SEC-02`/`OPR-SEC-01` are green today; keep them green with A5.

🪤 **The tests are the proof those clauses are green.** Moving code and leaving its tests behind
un-proves a clause while `make ci` stays green, because coverage does not know which clause a test
was standing for. Move them, and keep the clause IDs in their docstrings.

🪤 **`kernel` imports nothing above it.** If the moved adapter wants an agent's settings type, that is
the boundary telling you the signature is wrong — pass plain values, not the agent's object.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` for size.
- Module docstring declares `Agent:` / `Role:` / `External I/O:` — the moved kernel modules need theirs rewritten, since they are no longer an agent's.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **all steps** green, **100.00 % coverage floor**. **Never measure the gate through a pipe** — redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree — a worktree has **no `.env`**, so no live vendor call is possible there. **State which tree you ran in**, and do not claim a live call you did not make.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0**.
   🪤 **Run it from the worktree whose `HEAD` is the commit you are proving** — it resolves the SHA from the working directory and ignores a `SHA=` argument. **Check the printed SHA against `git rev-parse HEAD`.**
2. Merge to `main` locally and push.
3. **Post-merge CodeQL** — `codeql.yml` runs only on `main`.
4. **Deploy: image-only retag.** No injected pack moves. The live proof is the first scheduled run whose debate completes with its `LLMCall` rows intact — a refactor that broke the ledger would show there and nowhere earlier.

---

## Handover — paste this to the builder

```text
Sprint 222 - one LLM adapter lives in the kernel.
Repo: trading-agents. Branch: sprint-222-one-llm-adapter-lives-in-the-kernel (create it BEFORE any
code; never work on main; branch from current main). Full spec:
docs/sprints/sprint-222-one-llm-adapter-lives-in-the-kernel.md - read it whole first.

WHAT IS WRONG TODAY
The LLM port (kernel/llm.py) and the LLMCall ledger (kernel/llm_ledger.py) are kernel, but the
VENDOR ADAPTERS and the factory are not: they live inside two agents, in two copies that have
drifted. Measured consequence: the OpenAI provider option reached only the deliberator, because the
operator has no factory at all. And surfaces/dashboard/chat_binding.py:13 imports
`AnthropicLLMClient, ConfigurationError` straight out of an agent's internals.

THE SINGLE MOST IMPORTANT FACT, MEASURED
The two "duplicate" adapters are NOT duplicates. The deliberator's (129 lines) adapts FREE-TEXT
completions and carries S189's stop-reason handling. The operator's (103 lines) adapts TOOL-USE
responses and imports json to parse them. They share transport, config, key handling and error
mapping; they differ in how they read the response. Deleting one and pointing both at the other
BREAKS THE OPERATOR'S TOOL CALLING. Keep the two response shapes distinguishable over one transport.

MUST RULE - BEFORE YOU OPEN AN EDITOR
Read agents/deliberator/laws/laws.md + test-plan.md and agents/operator/laws/laws.md + test-plan.md,
plus docs/laws/conventions.md and docs/laws/drift-register.md. Fill the "Law reading record" at the
bottom of the spec. Binding clauses: DLIB-OUT-05, DLIB-FAIL-04, DLIB-SEC-02, DLIB-OBS-05,
OPR-SEC-01, OPR-DEP-01. ALL ARE GREEN TODAY - a regression un-proves a green clause, which is worse
than a new bug. If a law contradicts the spec, STOP AND REPORT.

LAW-CYCLE ANSWER IS "No", AND HOLDING IT IS A SCOPE RULE
contracts/ is untouched and no agent gains a guarantee. Where code LIVES is not a guarantee. BUT:
the moment you give the OPERATOR a provider choice, the answer becomes Yes - OPR-DEP-01 names
Anthropic as its sole external call, so a second vendor is a new dependency, a new tunable, a PARAM
row and an operator law cycle. That is OUT OF SCOPE. If you think the move needs it, stop and report.

WHAT TO BUILD
1. PLANT THE FAILING TEST FIRST: a test that no module under agents/ or surfaces/ defines or imports
   a vendor adapter. It fails today on 4 files. Watch it fail, paste the red output.
2. kernel/llm_anthropic.py - one Anthropic client: config + key handling, the HTTP call, error
   mapping, stop-reason capture, and the ConfigurationError that chat_binding.py imports today.
   Free-text and tool-use stay distinguishable: two named entry points on one client, or two thin
   classes over one transport. Record your choice and what you rejected.
3. kernel/llm_openai.py - the moved OpenAI client, behaviour unchanged.
4. kernel/llm_factory.py - the moved factory with KEY_ENV, DEFAULT_MODEL, UnknownProviderError,
   build_llm, key_env_var.
5. DELETE agents/deliberator/llm_anthropic.py, llm_openai.py, llm_factory.py and
   agents/operator/llm_anthropic.py. Repoint every call site: agents/deliberator/entrypoint.py:80
   and :90, scripts/deliberate.py:177, surfaces/dashboard/chat_binding.py:13 and :34, and the
   operator's own construction path.
6. MOVE THE TESTS WITH THE CODE, keeping their clause IDs in the docstrings. Those tests are what
   makes those clauses green; leaving them behind un-proves a clause while make ci stays green.
7. kernel/ is in the coverage source list - the moved code must stay at 100%.

ORDER OF WORK
Read laws -> write the Law reading record -> record design decisions in docs/design-log.md (next
free DL number; DL-190 is taken; re-check at merge) -> plant the failing test and watch it fail ->
implement -> break each new guard, watch it go red, restore it, say so per guard -> make ci, ALL
steps, redirected to a FILE (make ci > /tmp/ci.txt 2>&1 ; echo $?) then read the file; NEVER pipe it
-> fill the handback sections, set Status: BUILT.

DO NOT
- Do not give the operator a provider choice, a new tunable, or a PARAM row.
- Do not introduce a vendor FALLBACK CHAIN. The provider is a SELECTION. An automatic silent switch
  makes "which model reviewed this order" unanswerable, and DL-100 records the worse failure: a
  switch carrying the other vendor's model name stamps a FALSE model on the DeliberationRun. Test A4
  must make a fallback impossible, not merely absent. Keep DEFAULT_MODEL per provider.
- Do not change prompts, roles, models, effort, token budgets or retry behaviour.
- Do not touch kernel/llm_ledger.py or kernel/llm_tokens.py.
- Do not move or change FakeLLMClient - run_local.py and the suites depend on it.
- Do not let kernel import anything from contracts/, agents/, orchestration/ or surfaces/. If the
  moved adapter wants an agent's settings object, the signature is wrong: pass plain values.
- Do not justify anything by the August LLM outages. Both vendors ran dry inside three days; a
  provider switch would not have helped. This is about duplication and a boundary.

TRAPS THAT HAVE ALREADY COST THIS PROJECT
- A key leaks during a MOVE, not during a design: a reraise that adds context, a debug log added
  while porting, a repr() of a config object. DLIB-SEC-02 and OPR-SEC-01 are green - keep them green.
  S189 already ships a sentinel-based test for exactly this; reuse that pattern.
- The moved kernel modules need their module docstrings rewritten: `Agent:` is no longer an agent.
- Your own bump must satisfy the version check that landed in S221: a PATCH here is 0.103.02, NOT
  0.103.2.

WHAT YOU CANNOT PROVE, AND MUST NOT CLAIM
The worktree has no .env, so no live vendor call is possible there. Do not claim one. State plainly
which tree you ran in and whether it had .env.

HANDBACK CONTRACT
Fill the Law reading record BEFORE your first code change. Fill the Test plan results table - a test
you chose not to write needs a reason, not a blank. Fill Closeout - evidence with real pasted output
(the RED run first, then the green). Fill Return notes. Set Status: BUILT. Anything not met is
stated plainly as "verified failing" or "not done". An incomplete handback is returned, not repaired.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first code change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02).

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| *(fill)* | *(fill)* | *(fill)* | *(fill)* |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(fill — the spec says No; confirm with the reason, and say explicitly that the operator gained no provider choice)*

**Contradictions found between a law and this spec:** *(fill)*

**Laws found silent where a decision was needed:** *(fill)*

**Clauses that were green and are still green:** *(fill — name the test that proves each, post-move)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | *(fill)* | *(fill)* | *(fill)* | *(fill)* |

**Tests added beyond the plan:** *(fill)*

---

## Closeout — evidence

**Status:** *(fill: BUILT | MERGED)*

**Tree the proofs ran in (and `.env` present?):** *(fill)*

**Result:** *(fill — what is now true, in the artefact's own words)*

**Files changed:** *(fill — including the four deletions)*

**Design decisions:** recorded as `DL-NNN` — *(fill)*

**Proof — the red run first:**

```text
(fill)
```

**Proof — the green run:**

```text
(fill)
```

**Guards planted:** *(fill, per guard)*

**Module line counts:** *(fill)*

**`make ci`:** *(fill — redirected to which path, exit code, counts, coverage, pip-audit, detect-secrets)*

**`make gate-ran`:** *(fill — run from which worktree, at which full 40-char SHA)*

```text
(fill)
```

**Not met / verified failing:** *(fill, or "none")*

---

## Return notes

- *(Scope held / where it moved and why.)*
- *(How you kept free-text and tool-use distinguishable, and what you rejected.)*
- *(What the next sprint should know — in particular, what giving the operator a provider choice would now cost.)*
