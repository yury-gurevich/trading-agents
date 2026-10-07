<!-- Agent: planning | Role: sprint handover -->
# Sprint 254 — Each debater turn is run by DSPy, and the model reads the same prompt as before

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-254-each-debater-turn-is-run-by-dspy`
**Status:** BUILT 2026-10-07 — all 12 handback items met; 4251 tests pass, 100.00% coverage, 33 guards red/restored; 14/15 CI recipes pass, external advisory audit NOT RUN under the no-network restriction; not pushed or merged.
**Version:** *next available MINOR at merge*
**Effort:** M
**Decisions:** [ADR-0032](../decisions/0032-dspy-runs-the-llm-roles-at-run-time.md) (DSPy runs the LLM
roles at run time) · [DL-266](../design-log.md) (the reversal, its measurements, and decisions D1–D7
this sprint builds) · work-queue **110** · retires what [DL-252](../design-log.md) D1 settled · keeps
[DL-184](../design-log.md)'s premise

> **Why this bump kind.** The deliberator gains a runtime it did not have: it executes DSPy programs
> in its own process, where until now it copied DSPy's text. Later sprints build on that capability.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the one amendment this spec names. A clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`DLIB-OUT`**, **`DLIB-NEV`**, **`DLIB-FAIL`**, **`DLIB-OBS`**.

### The rule

1. **Before writing code**, read every law file in the map below, whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row (next free: DRIFT-102).
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's answer: Yes, one new guarantee; no `contracts/` change.** Until now no library stood
between the deliberator and its LLM client. Now one does, so the deliberator owes a prohibition it
never needed. Exactly this is owed, in the same unit of work:

- **`DLIB-NEV-10`** in `agents/deliberator/laws/laws.md`: *"Never lets a library that builds or parses
  a role's prompt reach a model vendor except through the agent's own LLM client."*
- The book's version goes to **v1.13**, with a Changelog line naming S254 and ADR-0032.
- A `test-plan.md` row for the clause, and the clause ID in the docstring of test B2.
- The rollup in **both** `docs/laws/ledger.md` and `docs/laws/INDEX.md`. Let `make ci` tell you the
  number.

Edit no other clause. If your law reading finds that an existing clause already makes this guarantee,
name it in the Law reading record, cite it in B2, and do not add a duplicate.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/deliberator/guided_turn.py` | `agents/deliberator/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `DLIB-OUT-06` (the reasoning is recorded exactly as the model wrote it, or why it could not be read); `DLIB-OUT-03` and `DLIB-OBS-05` (every call is ledgered with the vendor's own token counts); `DLIB-NEV-07` (no empty turn); `DLIB-FAIL-01`, `DLIB-FAIL-04` (a stopped or failed call fails the order open, its reason named) |
| `agents/deliberator/prompt_recipe.py`, `kernel/prompt_recipe.py` | same | `DLIB-OBS-07`: the digest identifies the code that rendered the prompt. DSPy now renders it, so the digest must change when DSPy does |
| `kernel/deliberation_guided*.py` and the two new kernel modules | same, plus [DL-252](../design-log.md) D1–D8 | D2, D3, D5 and D6 stay; D1 (the frozen literals) is what this sprint retires |
| `agents/deliberator/Dockerfile` | [DL-184](../design-log.md), [DL-199](../design-log.md) | `diskcache` reaches no container; the audit re-measures that premise on every run |
| `scripts/dependency_audit_rules.py`, `dependency_audit_baseline.py` | same | The premise is keyed on an extra's name today, and this sprint makes that name appear in a Dockerfile |
| `agents/deliberator/laws/laws.md` | `docs/laws/conventions.md` | The one amendment: `DLIB-NEV-10` |

⚠️ **The model must read the same text, and the graph must record the same fields, as on `main`.**
If a change would alter one byte of a system or user message, or the content of one recorded field,
stop and report. This sprint changes who renders and who calls. It changes nothing else.

---

## Goal

At merge, a defender or challenger turn is executed by a real `dspy.ChainOfThought` program in the
deliberator's process, through an engine that wraps the agent's own LLM client. The vendor receives
the system and user text production sends today, byte for byte. Each turn's record, its `LLMCall`, and
every failure path are what they are on `main`. `diskcache` and LiteLLM are installed in no image.

## Why (context)

The operator, 2026-10-07: *"from the very beginning i intended it to be an active participant. Revert
this decision and let's put dspy back where it belongs."* Recorded as ADR-0032.

Since S246 the runtime has copied DSPy's text: DSPy renders offline into a golden fixture, and three
kernel modules reproduce it. Every further DSPy feature needs the same again. The judge's guided
ruling, `dspy.History` for rounds, `dspy.Refine`, EXP-019's typed answers and a saved optimised
program would each need a hand-written twin and a parity fixture. This sprint removes that cost once.
It is deliberately the smallest step: the same turn, run by the library itself.

### Measured, 2026-10-07 — read these before designing

All with DSPy 3.4.0 (the lock's version), no LLM call and no network. The script in the Appendix
reproduces the first six rows in a worktree with no `.env`.

| Claim | Value | How it was measured |
| --- | --- | --- |
| A turn run by DSPy gives `main`'s record | **132 of 132** cases give the same `DebateTurnRecord` or raise the same exception | *[measured]* Appendix script: both roles × the golden's 3 user cases × (its 17 parse cases, 2 blank completions, a stopped call, a transport error, a timeout), against `main`'s `guided_turn` at `02e4f865` |
| The vendor client receives `main`'s text | 132 of 132: one call, the same system and user strings | *[measured]* Appendix script |
| DSPy needs LiteLLM or `diskcache` for this | no: neither is loaded, and all 132 cases pass with both unimportable | *[measured]* Appendix script, `block` argument |
| DSPy writes to disk with its disk cache off | 0 files in its cache directory | *[measured]* Appendix script |
| DSPy keeps prompts in memory with its history off | 0 calls in its global history | *[measured]* Appendix script, `disable_history=True` |
| How our client's failure crosses DSPy | as `dspy.utils.exceptions.LMUnexpectedError`, with our exception as `__cause__`; an exception raised by the adapter's `parse` arrives unwrapped | *[measured]* Appendix script |
| Four plain threads sharing one program, each entering its own `dspy.context` | 4 of 4 turns correct | *[measured]* planner's probe, not in the Appendix |
| Cost of loading DSPy in the deliberator's process | import + 0.9 to 1.4 s; resident memory 58 → 83 MB at import, about 120 MB after a turn; the first turn in a process + 2.3 s once, later turns + 7 ms | *[measured]* on the planner's Windows machine. *[ASSUMED]* the Linux image is close. The container has 0.5 CPU and 1.0 Gi |
| Packages the `optimizer` extra adds to the deliberator image's set | 41 added to 56 | *[measured]* `uv export --frozen --no-dev --extra runtime --extra azure --extra llm`, with and without `--extra optimizer` |
| 🪤 Packages the lock reaches only through LiteLLM or `diskcache` | 33, and **8 of them are loaded by DSPy all the same** (`attrs`, `jsonschema`, `jsonschema-specifications`, `referencing`, `rpds-py`, `pygments`, `pyyaml`, `rich`) | *[measured]* a walk of `uv.lock` against the modules a turn loads. An exclusion list computed from the lock would break `import dspy` |
| `uv sync --no-install-package` exists in the Dockerfiles' uv | yes, `uv==0.4.29` | *[measured]* `uvx --from 'uv==0.4.29' uv sync --help` |
| A fixed `diskcache` exists | no: 5.6.3, the affected release, is the latest on PyPI | *[measured]* PyPI's JSON |
| CI has DSPy installed | no: `ci.yml` and the `Makefile` run `uv sync` with no extra | *[measured, read]* `.github/workflows/ci.yml`, `Makefile` |
| DSPy versions in the tree | lock 3.4.0; the committed golden says 3.3.1; the planner's main venv has 3.3.1 | *[measured]* |
| 3.4.0 renders the golden like 3.3.1 | identical but for the `dspy_version` string | *[measured 2026-09-30]* [R009](../research/dspy/v3.4.md); not re-run today |
| A broken deliberator image is caught before a retag | *[ASSUMED]* yes, if DSPy is imported when the entrypoint is imported | *[read]* `build-images.yml` runs each image's real entrypoint. Not tried with a broken image |

---

## Scope — and what is deliberately NOT here

1. **The failing test first (A1).** A turn served by the deliberator loads `dspy`, and the vendor
   client receives `main`'s system and user text.
2. **The program runs in the runtime tree** (D1). Two new kernel modules, neither imported by
   `kernel/__init__.py`:
   - `kernel/dspy_engine.py`: the engine that wraps an `LLMClient`, and the one function that runs a
     program through it.
   - `kernel/deliberation_program.py`: the `DebateTurn` signature, the strict adapter, and the
     `ChainOfThought` program over `GuidedReasoning`.

   `agents/deliberator/guided_turn.py` executes the program. `agents/deliberator/agent.py` is not
   changed: the engine is handed the ledger client `guided_turn` is handed today. The Appendix script
   is the measured reference shape for all three.
3. **Strict JSON is kept** (D3). The adapter's `parse` is today's `parse_guided_turn`, so the 17 parse
   cases of the golden give the same `DebateTurnRecord` as on `main`.
4. **Failures are the ones production has today** (D5). The exception that reaches the caller on a
   stopped, failed or blank completion is the type and text it is on `main`. One vendor call per turn
   on every path.
5. **The kernel stops holding DSPy's text.** `kernel/deliberation_guided_format.py` goes, with
   `guided_system` and `guided_user`. `scripts/deliberation_guided_program.py` goes: the program now
   lives in the kernel. `parse_guided_turn`, `render_transcript` and `render_guided_text` stay.
6. **The golden becomes the upgrade tripwire.** Regenerate it with the installed DSPy. CI renders
   every case with the installed DSPy and compares, and the golden's `dspy_version` must equal the
   installed one. Apart from that version string the regenerated golden must equal the committed one:
   if anything else differs, stop and report.
7. **The recipe digest covers the DSPy version** (D6, `DLIB-OBS-07`), and the operator agent's own
   digest does not change.
8. **The image** (D4). `agents/deliberator/Dockerfile` installs the `optimizer` extra and leaves out
   exactly `diskcache` and `litellm`. No other Dockerfile changes.
9. **The audit's premise checks the package.** The accepted advisory stays accepted only while every
   Dockerfile that installs the extra leaves `diskcache` out by name.
10. **No other agent can load DSPy.** The other fourteen images do not have it, so an import that
    reaches it from their entrypoints would pass CI and crash in production.
11. **The law cycle** for `DLIB-NEV-10`.

### Out of scope (do NOT build this sprint)

- **`pyproject.toml` and `uv.lock`.** Do not touch either. The planner moves `dspy` into the `dev`
  group, raises its floor, re-locks and bumps the version at merge.
- **The judge.** Its prompt, message and parse stay byte-identical. Guiding the judge changes a prompt,
  so it needs ADR-0010's gate and a paid replay: the next sprint.
- **Accepting DSPy's JSON repair.** It changes what `DLIB-OUT-06` records. A later decision.
- **`dspy.History`, `dspy.Refine`, typed weights, GEPA.** Each builds on this sprint; none is in it.
- **One `dspy.Module` that composes the three roles** (the loop in
  [R010](../research/debate-pipeline-prototype/INDEX.md)). It is how the debate will be evaluated and
  optimised offline once the judge is a DSPy predictor. It needs the judge first.
- **`kernel/dspy_optimizer.py` and the operator agent's prompts.**
- **`kernel.deliberate`, the replay and eval harnesses** (DL-252 D7's known divergence), and the two
  defects in `scripts/guided_turn_replay.py` that R009 names. Keep that script working through the new
  path; fix nothing else in it.
- **Trimming LiteLLM's unused dependencies from the image.** See the 🪤 row above.
- **No `laws.md` edit** other than `DLIB-NEV-10`, the version and the Changelog line.
- **No ADR reversal.** ADR-0032 is the reversal; this sprint builds its first step.

### The road not taken (LAW-06)

- **Call the vendor through DSPy's own LM layer** (`dspy.LM("anthropic/…")`). Rejected: the call
  leaves the `LLMCall` ledger, the stop-reason handling and the outage handling, and it needs the
  vendor key inside DSPy.
- **Install the extra whole.** Rejected: `diskcache` would reach three containers against DL-184.
- **Leave out every package only LiteLLM brings.** Rejected for now: 8 of those are loaded by DSPy
  (measured above), and "never loaded in one probe" is not proof for the rest.
- **Keep the kernel renderer as a fallback beside DSPy.** Rejected: two renderers of one prompt is the
  state this sprint ends, and a fallback that is never exercised rots.
- **Move the judge in the same sprint.** Rejected: this sprint's proof is that nothing the model reads
  changes. A changed judge prompt would make that proof unreadable.

---

## The design decisions — made, and recorded in DL-266

The planner made these, each measured in the Appendix script. **Build them as written.** Record in
`docs/design-log.md` (next free: **DL-267**) only a decision the spec did not make, or a place where
you had to depart from one of these, with the reason.

| # | Decision | Rejected |
| --- | --- | --- |
| D1 | The engine and the program live in `kernel/`, in modules `kernel/__init__.py` never imports | `agents/deliberator/`: the judge and later roles would need them moved |
| D2 | *(planner, at merge)* `dspy` in the `dev` group so CI has it, and in the `optimizer` extra the one Dockerfile names | a base dependency: fourteen images would carry a library they never run |
| D3 | A `ChatAdapter` subclass with the JSON fallback off whose `parse` is `parse_guided_turn`. An unreadable completion raises an exception carrying the completion and DL-252 D3's reason | DSPy's own parse: it repairs JSON, which changes the record |
| D4 | The image leaves out exactly `diskcache` and `litellm` | a list computed from the lock (breaks the import); the extra whole (breaks DL-184) |
| D5 | The one function that runs a program catches `LMUnexpectedError` and re-raises its `__cause__`, so the caller sees the client's own exception. A blank completion raises `empty_debate_turn` inside the engine, after the ledger has recorded the call | letting DSPy's wrapper reach `fault_boundary`: `failed_open_reason` would name DSPy's class, not the cause |
| D6 | The recipe digest takes the installed DSPy version string as well as the module sources | hashing DSPy's source tree: slow, and it moves with files that render nothing |
| D7 | DSPy is imported, the caches turned off and the two programs built when the agent module is imported. Each turn builds its own `dspy.LM` around its own client with `cache=False, num_retries=0`, and enters `dspy.context(lm=…, adapter=…, disable_history=True)` in the serving thread | importing lazily: a broken image would start, activate and fail its first debate at night |

---

## Blast radius — measured 2026-10-07

| What | Detail |
| --- | --- |
| Files changed | `agents/deliberator/guided_turn.py` **81**, `agents/deliberator/prompt_recipe.py` **71**, `kernel/prompt_recipe.py`, `kernel/deliberation_guided.py` **155**, `kernel/deliberation_guided_render.py` **76**, `scripts/render_guided_turn_golden.py` **118**, `scripts/guided_turn_replay.py`, `scripts/dependency_audit_rules.py`, `scripts/dependency_audit_baseline.py` **50**, `agents/deliberator/Dockerfile`, the golden fixture, the deliberator's `laws.md` and `test-plan.md`, the two rollups. New: `kernel/dspy_engine.py`, `kernel/deliberation_program.py`, one fixture of `main`'s records. Removed: `kernel/deliberation_guided_format.py` **88**, `scripts/deliberation_guided_program.py` **58**, `tests/dspy_free_probe.py` **52**. Tests rewritten: `tests/test_no_dspy_at_runtime.py` **92**, `tests/test_deliberation_guided.py` **111**, `tests/test_guided_offline_scripts.py`, `tests/test_prompt_recipe.py`, `tests/test_check_dependency_audit.py`, `agents/deliberator/tests/test_guided_turn.py` |
| Agents affected | the deliberator only (one image, three apps). It imports no other agent |
| Contract change? | no. The law cycle is owed for the new guarantee, not for a contract |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | image-only retag. The deliberator image's contents change; the other fourteen do not |
| Rollback | retag the fleet to the tag it ran before. Nothing beyond the retag: no graph write, schema, pack, env key or infra setting changes |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Run the Appendix script** in your worktree, both ways, and paste its output into the Closeout.
   It must print 132 of 132 twice. If it does not, stop and report: your environment differs from
   the one this spec was measured in.
3. **Capture `main`'s behaviour before changing it**, as one committed fixture
   (`tests/fixtures/guided_turn_main_records.json`, naming the commit it was taken from): the
   `DebateTurnRecord` or the exception each of the Appendix script's cases gives, and each role's
   `LLMCall.system_prompt_hash` from one turn served through `DeliberatorAgent` on the in-memory store.
4. **Plant the failing test first** (A1) and watch it fail. Paste the red output.
5. **Implement** decisions D1 and D3 to D7.
6. **Law cycle:** clause, version, Changelog, test-plan row, docstring citation, both rollups.
7. **Prove the guards can fail (DL-70):** break each guarded property, watch the guard go red, restore.
8. **`make ci`**, every step of the `ci:` target, **redirected to a file, never piped**. Name any step
   your sandbox cannot run as NOT RUN.
9. **Fill the handback sections** at the bottom of this file and set Status to `BUILT`, here and in
   this sprint's `README.md` row.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A served turn is run by DSPy and sends `main`'s text | A recording client behind `DeliberatorAgent.debate_turn`, each role, each of the golden's 3 user cases | `dspy` is loaded in the serving process; the client received exactly one call whose system and user strings equal what `main` sent (step 3's fixture) (`DLIB-OUT-06`) |
| A2 | Every completion records what `main` records | The golden's 17 completions and 2 blank ones; step 3's fixture | `text`, `reasoning` and `reasoning_error` are equal case by case, and a blank completion still raises `empty_debate_turn` (`DLIB-OUT-06`, `DLIB-NEV-07`) |
| A3 | A failed call fails as it does today | A client that raises `LLMCompletionStoppedError`, one `RuntimeError`, one `TimeoutError` | The same exception type and message reach the caller, and through `DeliberatorAgent` the `LLMCall` carries the same stop reason (`DLIB-FAIL-01`, `DLIB-FAIL-04`) |
| A4 | One vendor call per turn | A counting client on the success, stopped, failed and unreadable paths | The count is 1 on each (`DLIB-OUT-03`) |
| A5 | The prompt hashes do not move | Step 3's two hashes | Each role's `LLMCall.system_prompt_hash` equals `main`'s, and two turns of one role send identical system text (`DLIB-OBS-06`) |
| A6 | The recipe digest follows DSPy and nothing else moves | The installed version string, then a different one | The deliberator's digest differs between the two and covers both new kernel modules; the operator agent's digest equals its value on `main` (`DLIB-OBS-07`) |
| A7 | Concurrent turns do not cross | Four turns served from plain threads sharing the programs, each with its own client and its own packet | Each client received only its own packet, and each turn parsed |
| B1 | 🪤 The turn needs neither package | A separate interpreter in which `diskcache` and `litellm` cannot be imported, DSPy's cache directory pointed at an empty folder | The turn completes, the folder is still empty, and DSPy's global history is empty |
| B2 | 🪤 DSPy reaches no vendor by itself | A turn served with every socket connection refused | It completes through the client alone, and the LM the program ran on carries our engine (`DLIB-NEV-10`) |
| B3 | 🪤 No other image's code loads DSPy | What each of the other fourteen Dockerfiles' `CMD` runs (thirteen `agents.<name>.entrypoint` modules and `scripts/dispatch_scheduled_run.py`), imported in an interpreter where `dspy` cannot be imported | All fourteen import; the deliberator's entrypoint does not |
| B4 | 🪤 The images | Every Dockerfile's `uv sync` line | Only `agents/deliberator/Dockerfile` names the `optimizer` extra, and it names `--no-install-package diskcache` and `--no-install-package litellm` |
| B5 | 🪤 The audit's premise | A Dockerfile text that installs the extra without leaving `diskcache` out; one that leaves it out | The first voids the acceptance and names the Dockerfile; the second keeps it, and the accepted note says how many Dockerfiles install the extra and that each leaves the package out |
| B6 | The golden is the installed DSPy's | The golden writer run on the installed DSPy | Its output equals the committed golden exactly, and the golden's `dspy_version` equals the installed version |
| B7 | The judge is untouched | The existing judge and verdict tests | They pass with no edit to them |

No test may skip when DSPy is missing (`pytest.importorskip` is not allowed here). A skipped proof is
not a proof.

---

## Success factors

- [x] A served defender or challenger turn is executed by `dspy.ChainOfThought`, and the vendor client
      receives the text `main` sends.
- [x] Every captured case records what `main` records, and both roles' system prompt hashes equal
      `main`'s.
- [x] One vendor call per turn on every path; a failed call raises what it raises on `main`.
- [x] The deliberator's Dockerfile installs DSPy and leaves out `diskcache` and `litellm`; no other
      Dockerfile changed.
- [x] No other agent's entrypoint can reach `dspy`.
- [x] `kernel/deliberation_guided_format.py` is gone, and no module holds DSPy's format text.
- [x] `pyproject.toml` and `uv.lock` are untouched.
- [x] Law cycle done for `DLIB-NEV-10`, or an existing clause named in its place.
- [x] Every new guard planted, watched to fail, restored, stated per guard.
- [x] Every touched module < 200 lines.
- [x] `make ci` exit 0, 100.00 % coverage, or each step that could not run named as NOT RUN.

---

## Traps

🪤 **A `dspy.LM` built without our engine calls the vendor itself.** It would work, and every call
would be missing from the ledger. Construct it in one place, always with the engine.
🪤 **DSPy caches answers by default.** A cached answer skips the client, so it skips the ledger. Pass
`cache=False`, and turn the disk and memory caches off.
🪤 **The default `ChatAdapter` falls back to `JSONAdapter` on a parse error.** That is a second vendor
call with a different prompt. The adapter is built with `use_json_adapter_fallback=False`.
🪤 **`dspy.context` does not reach a plain thread**, and `dspy.configure` may only be called from the
thread that first called it. Enter `dspy.context` inside the thread that serves the turn, and never
call `dspy.configure` for the LM or the adapter.
🪤 **The audit's premise is keyed on the extra's name.** Today any Dockerfile naming the extra voids
the acceptance, so the gate goes red the moment the Dockerfile changes. The rule has to change in the
same commit (B5), and it must still fail when the package is not left out.
🪤 **A bare `uv sync` in your worktree removes DSPy.** The worktree's venv was synced with
`--extra optimizer`. If you must sync, use `uv sync --locked --extra optimizer`. `uv run` is safe.
🪤 **`kernel/__init__.py` re-exports widely.** Importing either new module there puts DSPy on every
agent's import path, and fourteen images do not have it (B3).
🪤 **`num_retries` defaults to 3.** The measured failures were not retried, but a default is not a
guarantee: set it to 0.
🪤 **Equal text is not equal bytes on the wire.** Compare the strings the client receives, not the
strings a renderer returns.
🪤 **`recipe_digest` is shared with the operator agent.** Its digest must not move (A6).

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `agents/deliberator/agent.py` **168**, `kernel/deliberation_guided.py` **155**,
  `scripts/compile_deliberation_prompts.py` **170**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `kernel.tunable(..., why=...)` with bounds. This sprint adds no tunable.
- Faults, not silent failure: `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Secrets never through the worktree. A worktree has **no `.env`**, and nothing here needs one.
  **State which tree you ran in.**

---

## Sequencing after merge

Owed by the planner, in this order:

1. **The dependency layout (D2):** `dspy` in the `dev` group and its floor raised to the lock's
   version, `uv lock`, the MINOR bump. Then Windows `make ci`, all steps, in an environment synced
   with no extra, which is CI's.
2. Push the branch; **`make gate-ran` exits 0**, run from the worktree whose `HEAD` is the commit being
   proven, the printed SHA checked against `git rev-parse HEAD`. The branch's open CodeQL alerts are
   compared with the last merged branch's.
3. Merge to `main` and push.
4. **The image, before any retag.** `docker build -f agents/deliberator/Dockerfile .`, then in the
   built image: `import dspy` and `import agents.deliberator.entrypoint` succeed, `diskcache` and
   `litellm` cannot be found, and one guided turn runs against a canned client. The image size is
   recorded against the current one.
5. **Deploy: image-only retag, and not before the fidelity verdict due 2026-10-08.** It rides the
   retag already owed for S252 and S253. The rollback tag is recorded with the deploy.
6. **F1 (costs money: the balance is asked about first).** One real debate through the merged code
   against the live vendor: both debaters' turns carry readings, and their system prompt hashes equal
   the last debate night's.
7. **F2.** The first scheduled night with a debated buy after the retag: the same two hashes, a new
   `prompt_recipe_hash`, no fail-open from an import or a parse, and the three apps' peak memory.

---

## Planner's correction, 2026-10-07 14:31 AEDT — and how the build resumes

**The defect was the spec's.** Checklist item 8 asked for a whole-repository `git grep` to print
nothing. The spec contains the pattern, and so do DL-252 and S246's spec, so no build could satisfy it.
The planner wrote the command without running it. Codex stopped on it as the handover told it to, before
implementing ([DL-267](../design-log.md)).

**What stands from the first pass, and is not redone:** the Law reading record; the Appendix script's
two outputs (132 of 132); `tests/fixtures/guided_turn_main_records.json`; test A1 and its probe,
verified failing; DL-267.

**What the planner changed on this branch:**

- Checklist item 8 is scoped to the code trees: `kernel contracts agents orchestration surfaces scripts tests`.
- Checklist item 9 names the one value that may change. Test B3 names the fourteen things it imports.
- The stop rule: a wrong command, count or path with a plain intent is corrected and recorded, not
  stopped on.
- `main`'s documentation commits are merged in, and `docs/STATE.md` is `main`'s. The builder adds
  nothing to `STATE.md` from here: intent and results go in the Closeout below.

### Resume — paste this to Codex

```text
Sprint 254, resumed. Same worktree and branch: ../ta-s254, sprint-254-each-debater-turn-is-run-by-dspy.
The planner has committed on top of your 03ca1c72: pull nothing, just read `git log -3` and the spec's
section "Planner's correction". Your stop was right; the defect was the spec's (checklist 8), and it
is corrected: the removal grep is scoped to
  kernel contracts agents orchestration surfaces scripts tests
Everything from your first pass stands and is not redone: the Law reading record, the two Appendix
outputs, tests/fixtures/guided_turn_main_records.json, A1 and its probe, DL-267.

Continue from Step 5 of the spec (implement D1 and D3-D7), then Steps 6 to 9. The handover block in
the spec is unchanged except for checklist items 8 and 9, test B3's wording, and the stop rule, which
now reads: a wrong command, count or path whose intent is plain from Scope and Success factors is NOT
a reason to stop; follow the intent, record the correction in Return notes, continue. Stop only when
a behaviour, a law or the spec's invariant is in question, or a measurement the spec relies on does
not reproduce.

Unchanged rules: no network, no .env, never a bare `uv sync`, do not touch pyproject.toml or uv.lock,
do not push, no LLM call in any test, the judge is not touched, no prompt text and no recorded field
changes. New: do not edit docs/STATE.md; put intent and results in the spec's Closeout. Replace the
"not done" rows of the Test plan results as you prove each one, and set Status to BUILT (spec and
README row) only when the 12-item checklist is met.
```

---

## Handover — paste this to Codex

```text
Sprint 254 — each debater turn is run by DSPy, and the model reads the same prompt as before. Spec:
docs/sprints/sprint-254-each-debater-turn-is-run-by-dspy-and-the-prompt-does-not-change.md on main
(read ALL of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s254, on branch sprint-254-each-debater-turn-is-run-by-dspy, cut
from main, with its venv synced to the lock plus the optimizer extra (DSPy 3.4.0). Work only there,
never in the main checkout and never on main. You have no .env and no network: every proof is a unit
test, and no test calls an LLM. NEVER run a bare `uv sync` there (it removes DSPy); `uv run` is safe.
Do not touch pyproject.toml or uv.lock, and say so: the planner changes both at merge. Do not push;
commit on the branch and hand back. If a make ci step cannot run in your sandbox (the dependency
audit needs the network; a pre-commit hook may fail to spawn sh), do not bypass it silently: name the
step as NOT RUN in the handback.

This handover is complete: nobody will send you follow-up messages. If something in the spec is wrong
or blocked, record it in the handback (Return notes, "not done") and stop; do not improvise.
A wrong command, count or path whose intent is plain from the spec's Scope and Success factors is NOT
a reason to stop: follow the intent, record the correction in Return notes, and continue. Stop only
when a behaviour, a law or the invariant marked with the warning sign is in question, or when a
measurement the spec relies on does not reproduce.

What and why: since S246 the deliberator copies DSPy's prompt text. DSPy renders offline into
tests/fixtures/deliberation_guided_golden.json and three kernel modules reproduce it byte for byte.
The operator reversed that (ADR-0032): DSPy is to run in the agent's process. This sprint makes the
defender's and the challenger's turn a real dspy.ChainOfThought call, through a DSPy engine that
wraps the agent's own LLM client, and changes NOTHING the model reads or the graph records. The
planner measured it first: the Appendix script runs the new shape against main's guided_turn over 132
cases and all 132 match.

MUST RULE before any code: read, whole, agents/deliberator/laws/laws.md and test-plan.md,
docs/laws/conventions.md, docs/laws/drift-register.md, and DL-252, DL-184 and DL-266 in
docs/design-log.md. Fill the Law reading record first. Law-cycle answer: YES, and exactly this is
owed: add DLIB-NEV-10 ("Never lets a library that builds or parses a role's prompt reach a model
vendor except through the agent's own LLM client."), deliberator laws v1.13, a Changelog line naming
S254 and ADR-0032, a test-plan row, the clause ID in test B2's docstring, both rollups
(docs/laws/ledger.md and docs/laws/INDEX.md). Edit no other clause.

Order (the spec's Steps): laws -> run the Appendix script both ways (must print 132 of 132 twice) ->
capture main's records and the two system prompt hashes into
tests/fixtures/guided_turn_main_records.json -> plant A1, watch it fail, paste the red -> implement
-> law cycle -> break and restore every guard -> make ci to a file.

Build (decisions D1, D3-D7 are made; build them as written, the Appendix script is the reference):
1. kernel/dspy_engine.py: the engine that wraps an LLMClient (one request -> one client.complete with
   request.system and the single user message; a blank completion raises LLMCompletionStoppedError
   with the stop reason the caller names), and the one function that runs a program: its own dspy.LM
   with the engine, cache=False, num_retries=0; dspy.context(lm, adapter, disable_history=True);
   LMUnexpectedError is caught and its __cause__ re-raised. Disk and memory caches turned off at
   import.
2. kernel/deliberation_program.py: the DebateTurn signature (move it from
   scripts/deliberation_guided_program.py, field descriptions unchanged), the strict adapter
   (ChatAdapter, JSON fallback off, parse = parse_guided_turn plus the blank-argument rule, raising an
   exception that carries the completion and the reason), and the ChainOfThought program over
   GuidedReasoning. Neither new module may be imported by kernel/__init__.py.
3. agents/deliberator/guided_turn.py: run the role's program; an unreadable completion becomes the
   record main writes (raw text, reasoning_error). agents/deliberator/agent.py is not changed.
4. Remove kernel/deliberation_guided_format.py, guided_system and guided_user,
   scripts/deliberation_guided_program.py and tests/dspy_free_probe.py. Keep parse_guided_turn,
   render_transcript, render_guided_text. Keep scripts/guided_turn_replay.py working; fix nothing
   else in it.
5. The golden: regenerate with the installed DSPy. Only its dspy_version may change. Tests render
   every case with the installed DSPy and compare with it.
6. The recipe digest covers the installed DSPy version and the two new modules; the operator agent's
   digest must equal its value on main.
7. agents/deliberator/Dockerfile: add --extra optimizer --no-install-package diskcache
   --no-install-package litellm to its uv sync line. No other Dockerfile changes.
8. scripts/dependency_audit_rules.py and its baseline: the diskcache acceptance holds only while every
   Dockerfile that installs the extra leaves the package out by name; the accepted note says so.
9. Tests A1-A7 and B1-B7 from the spec's Test plan, each citing its clause.

DO NOT: change any prompt text or any recorded field; accept DSPy's JSON repair; build a dspy.LM
without the engine; call dspy.configure for the LM or adapter; let DSPy cache or keep history; skip a
test when DSPy is missing; touch the judge, kernel/dspy_optimizer.py, kernel.deliberate, the replay
harness's logic or the operator agent; widen the image's exclusion list; pin a version number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The Appendix script's two outputs pasted (132 of 132, twice), with the tree it ran in.
 3. tests/fixtures/guided_turn_main_records.json committed, naming the commit it was taken from.
 4. A1's red output pasted, from before the implementation.
 5. Test plan results: one row for each of A1-A7 and B1-B7, with file, status and clause.
 6. Every guard's break-and-restore stated, one line per guard.
 7. DLIB-NEV-10, v1.13, Changelog, test-plan row, both rollups; no other clause edited.
 8. kernel/deliberation_guided_format.py, scripts/deliberation_guided_program.py and
    tests/dspy_free_probe.py are gone, and this command prints nothing (code trees only; the docs
    keep the names as history):
    git grep -n "guided_system\|GUIDED_TURN_PREFIX" -- kernel contracts agents orchestration surfaces scripts tests
 9. The regenerated golden's diff pasted: its dspy_version value is the only change.
10. `git diff main -- pyproject.toml uv.lock` is empty, and you say so.
11. make ci output file named, exit code stated, every NOT RUN step named with its reason.
12. Module line counts for every touched module; Status BUILT here and in the README row.
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
| Guided turn, engine and strict program | `agents/deliberator/laws/laws.md` and `test-plan.md` (whole); `docs/laws/conventions.md` and `drift-register.md` (whole) | DLIB-OUT-03/05/06, DLIB-NEV-07, DLIB-FAIL-01/04, DLIB-OBS-05/06 | Keep the client ledger, exact raw unreadable completion and named error, blank-turn exception, and provider failure unchanged. |
| Prompt recipe | same law book and plan | DLIB-OBS-07 | Include the installed DSPy version and both new modules without moving the operator digest. |
| Dockerfile and dependency acceptance | DL-184 and DL-199; DL-252 D1-D8; DL-266 D1-D7; ADR-0032 | DLIB-NEV-10 (owed); DLIB-OUT-03 | Keep diskcache outside every image; runtime DSPy uses only the agent client, with no repair, cache, history or retries. |
| One law amendment and rollups | same law book, plan and conventions | DLIB-NEV-10 (new) | No existing clause makes the library-to-vendor prohibition; add exactly the specified clause, v1.13, Changelog, row and both rollups. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** YES: DLIB-NEV-10 is a new guarantee; no contracts change. The existing DLIB-NEV clauses do not state this prohibition. This reading record was written before any code change, on clean branch `sprint-254-each-debater-turn-is-run-by-dspy`, HEAD `ab88b9162b61c43b8405567b231e52c7e88af1bc`; local main/origin/main `dd2f08f6a7aec39458a11f536b89599ff60204e0` differs only in five documentation paths. No push, network, .env, dependency-file edit or merge is authorised.

**Contradictions found between a law and this spec:** None. v1.11's historical Changelog describes the retired renderer; the operative clauses govern the unchanged reasoning and failure semantics.

**Laws found silent where a decision was needed:** The specified library-to-vendor guarantee is absent and is resolved by this sprint's explicitly owed DLIB-NEV-10. No additional undecided silence found. DLIB-DEP-03 and DLIB-OBS-02 are gray; this sprint does not claim to prove the whole dependency or spend-attribution clause.

**Clauses that were ⬜ and are now proven:** None. No law amendment or runtime implementation was made.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a_served_turn_runs_dspy_and_sends_mains_text` | `agents/deliberator/tests/test_dspy_runtime.py` | PASS: 1; original red retained | DLIB-OUT-06 |
| A2 | `test_served_records_equal_main` | `agents/deliberator/tests/test_dspy_turn_parity.py` | PASS: 114 outcomes | DLIB-OUT-06, DLIB-NEV-07 |
| A3 | `test_served_failures_equal_main_and_keep_ledger_stop_reason` | `agents/deliberator/tests/test_dspy_turn_parity.py` | PASS: 18 failures and ledger stop reasons | DLIB-FAIL-01, DLIB-FAIL-04 |
| A4 | `test_every_turn_has_one_client_call_and_one_ledger_row` | `agents/deliberator/tests/test_dspy_turn_parity.py` | PASS: 132 one-call / one-row cases | DLIB-OUT-03 |
| A5 | `test_role_system_text_is_reused_and_has_mains_hash` | `agents/deliberator/tests/test_dspy_turn_parity.py` | PASS: 2 roles; actual calls and ledger hashes | DLIB-OBS-06 |
| A6 | `test_dspy_version_changes_only_the_deliberator_recipe; test_each_new_modules_source_changes_the_recipe` | `tests/test_dspy_recipe.py` | PASS: version and both modules; operator unchanged | DLIB-OBS-07 |
| A7 | `test_concurrent_turns_keep_their_own_client_and_packet` | `agents/deliberator/tests/test_dspy_concurrency.py` | PASS: 4 overlapping plain threads | DLIB-ORD-01, DLIB-OUT-06 |
| B1 | `test_served_turn_needs_no_excluded_package_cache_or_history` | `tests/test_dspy_boundary.py` | PASS: hard import blocks, empty cache/history, repeated calls | DLIB-OUT-03, DLIB-OBS-07 |
| B2 | `test_dspy_uses_only_the_agents_engine_with_sockets_refused` | `tests/test_dspy_boundary.py` | PASS: actual LM engine; sockets refused | DLIB-NEV-10 |
| B3 | `test_other_image_entrypoints_import_without_dspy` | `tests/test_no_dspy_at_runtime.py` | PASS: 13 modules and 1 script; deliberator requires DSPy | DLIB-NEV-05 |
| B4 | `test_only_deliberator_installs_optimizer_with_exact_exclusions` | `tests/test_dspy_images.py` | PASS: all 15 tracked Dockerfiles; exact 2 exclusions | DLIB-DEP-03 (bounded image premise only), ADR-0032 |
| B5 | `test_optimizer_installation_with_diskcache_excluded_preserves_acceptance; test_any_optimizer_command_without_diskcache_exclusion_voids_acceptance; test_each_installer_must_exclude_the_package_and_comments_install_nothing` | `tests/test_dspy_images.py` | PASS: 9 synthetic premise cases; existing alias/fix/stale/package guards pass | DLIB-DEP-03 (bounded audit premise only), DL-184, DL-199 |
| B6 | `test_the_golden_writer_produces_the_goldens_shape; test_the_golden_was_written_by_dspy_and_covers_the_spec_table` | `tests/test_guided_offline_scripts.py; tests/test_deliberation_guided.py` | PASS: real installed DSPy, exact output bytes and version | DLIB-OUT-06 |
| B7 | `existing judge, verdict and fail-open tests (unchanged)` | `tests/test_deliberation.py; agents/deliberator/tests/test_judge_non_answer_fail_open.py; agents/deliberator/tests/test_review_veto_semantics.py` | PASS: 19 existing tests, no edits | DLIB-FAIL-04 |

**Tests added beyond the plan:** Four engine/adapter edge tests in `tests/test_dspy_engine.py`: streaming uses a single completion, the caller chooses the blank stop reason, an uncaused DSPy error remains loud, and a future parser non-answer still retains its text and reason. B5 additionally proves comments, separate commands and multiple installers cannot satisfy an exclusion. A6 checks each new module's actual source sensitivity. Probes use canned clients only.

**Resume test output** (`.venv/s254-proof/plan-green.txt`, exit 0; full command recorded in Closeout):

```text
368 passed in 30.34s
```

---

## Closeout — evidence

**Resume INTENT (Step 5, 2026-10-07):** Execute D1 and D3-D7 against the measured Appendix shape, retaining the law reading, two Appendix runs, main fixture, A1 red and DL-267. Prove A1-A7/B1-B7, complete only DLIB-NEV-10/v1.13 and its rollups, break/restore every new guard, redirect CI, and report unavailable steps. No network, .env, push, judge edit, dependency-file edit or STATE edit.

**Result:** Implemented the measured engine/program shape. Actual served calls preserve all six captured wire requests and both role hashes; all 132 records or exceptions match main. Every case makes one client call and one ledger row. Four overlapping threads retain their own clients and packets. The strict parser and blank rules, client failure types, judge and recorded payload fields are preserved. Real installed DSPy reproduces the golden byte for byte; only its version value changes. Both new modules and that version enter the deliberator recipe; the operator recipe remains the captured main value.

**Law cycle:** DLIB-NEV-10 added exactly as authorised; laws v1.13 and Changelog name S254/ADR-0032; B2 docstring and test-plan row cite it; both rollups read 28 / 60. All 59 pre-existing clauses are byte-identical. The OUT-06 test-plan citation follows the retired runtime-free probe to A1/A2. No other clause is edited, and DEP-03/OBS-02 remain gray.

**Design decisions:** D1 and D3-D7 implemented as written. D2 (dev dependency and version bump) remains the planner's merge work. DL-267 and the Planner's correction stand; no new behavioural decision was needed.

**Files changed:** The guided turn and recipe declarations; the two new kernel modules; shared recipe hashing; removal of the copied message formatter and old program/probe; real golden writer and tests; deliberator Dockerfile only; audit premise and baseline; the authorised law amendment/rollups; sprint handback and indexes. Existing agent/judge/operator/replay logic, prompt text, contracts, baseline fixture and dependency files were not edited on resume.

**The Appendix script's two outputs:**

`C:/Users/yury_/Downloads/project/ta-s254`, `appendix-normal.txt`, exit 0:

```text
dspy 3.4.0; cases 132: same record or same exception 132, same single vendor call with the same text 132
per role and user case: 17 parse cases, 2 blank completions, 3 failures; roles 2; user cases 3
blocked: nothing | litellm loaded: False | diskcache loaded: False
files in DSPy's cache directory: 0 | calls DSPy kept in its global history: 0
```

`C:/Users/yury_/Downloads/project/ta-s254`, `appendix-block.txt`, exit 0:

```text
dspy 3.4.0; cases 132: same record or same exception 132, same single vendor call with the same text 132
per role and user case: 17 parse cases, 2 blank completions, 3 failures; roles 2; user cases 3
blocked: ['diskcache', 'litellm'] | litellm loaded: False | diskcache loaded: False
files in DSPy's cache directory: 0 | calls DSPy kept in its global history: 0
```

**Proof — the red run first:**

`uv run --no-sync pytest agents/deliberator/tests/test_dspy_runtime.py --no-cov -q`, exit 1, before any runtime edit:

```text
F                                                                        [100%]
================================== FAILURES ===================================
______________ test_a_served_turn_runs_dspy_and_sends_mains_text ______________
agents\deliberator\tests\test_dspy_runtime.py:28: in test_a_served_turn_runs_dspy_and_sends_mains_text
    assert result.returncode == 0, result.stdout + result.stderr
E   AssertionError: Traceback (most recent call last):
E       File "<frozen runpy>", line 198, in _run_module_as_main
E       File "<frozen runpy>", line 88, in _run_code
E       File "C:\Users\yury_\Downloads\project\ta-s254\agents\deliberator\tests\dspy_served_probe.py", line 70, in <module>
E         main()
E         ~~~~^^
E       File "C:\Users\yury_\Downloads\project\ta-s254\agents\deliberator\tests\dspy_served_probe.py", line 38, in main
E         assert "dspy" in sys.modules, "a served deliberator must load DSPy"
E                ^^^^^^^^^^^^^^^^^^^^^
E     AssertionError: a served deliberator must load DSPy
E
E   assert 1 == 0
E    +  where 1 = CompletedProcess(args=['C:\\Users\\yury_\\Downloads\\project\\ta-s254\\.venv\\Scripts\\python.exe', '-m', 'agents.deli... deliberator must load DSPy"\n           ^^^^^^^^^^^^^^^^^^^^^\nAssertionError: a served deliberator must load DSPy\n').returncode
=========================== short test summary info ===========================
FAILED agents/deliberator/tests/test_dspy_runtime.py::test_a_served_turn_runs_dspy_and_sends_mains_text
1 failed in 2.45s
```

**Proof — green runtime and planned regressions:**

```text
uv run --no-sync pytest agents/deliberator/tests/test_dspy_runtime.py --no-cov -q
1 passed in 7.77s

uv run --no-sync pytest agents/deliberator/tests/test_dspy_runtime.py agents/deliberator/tests/test_dspy_turn_parity.py agents/deliberator/tests/test_dspy_concurrency.py tests/test_dspy_recipe.py tests/test_dspy_boundary.py tests/test_no_dspy_at_runtime.py tests/test_dspy_images.py tests/test_dspy_engine.py tests/test_guided_offline_scripts.py tests/test_deliberation_guided.py tests/test_deliberation_guided_text.py tests/test_prompt_recipe.py tests/test_check_dependency_audit.py agents/deliberator/tests/test_guided_turn.py tests/test_deliberation.py agents/deliberator/tests/test_judge_non_answer_fail_open.py agents/deliberator/tests/test_review_veto_semantics.py --no-cov -q
368 passed in 30.34s
```

Both commands returned exit 0. Logs: `.venv/s254-proof/a1-green.txt` and `plan-green.txt`. B1/B2 fresh interpreters refuse connections, block both excluded imports, and observe actual engines, two client calls/two ledger rows, empty cache files and empty global/per-LM history. B3 imports what all fourteen other Dockerfile CMDs run with DSPy blocked.

**Guard break-and-restore proofs (DL-70):** Each mutation ran in a fresh pytest process, returned exit 1, was restored byte for byte in `finally`, then returned exit 0. Logs: `.venv/s254-proof/<guard>-red.txt` and `<guard>-restored.txt`; manifests: `guards-0-10.json`, `guards-10-21.json`, `guards-21-33.json`. No judge file was mutated.

| Guard | Guarded property | Planted result (exit 1) | Restored result (exit 0) |
| --- | --- | --- | --- |
| 01-cot | A1 actual ChainOfThought execution (`agents/deliberator/tests/test_dspy_runtime.py`) | 1 failed in 8.71s | 1 passed in 6.57s |
| 02-system | A1 unchanged signature/system text (`agents/deliberator/tests/test_dspy_runtime.py`) | 1 failed in 8.50s | 1 passed in 6.61s |
| 03-user | A1 unchanged user packet (`agents/deliberator/tests/test_dspy_runtime.py`) | 1 failed in 8.82s | 1 passed in 6.71s |
| 04-repair | A2 strict JSON without repair (`agents/deliberator/tests/test_dspy_turn_parity.py::test_served_records_equal_main[defender-first_turn-malformed_json_trailing_comma]`) | 1 failed in 4.19s | 1 passed in 4.18s |
| 05-argument | A2 blank argument stays unreadable (`agents/deliberator/tests/test_dspy_turn_parity.py::test_served_records_equal_main[defender-first_turn-empty_argument]`) | 1 failed in 4.28s | 1 passed in 4.54s |
| 06-blank | A2 blank completion keeps empty_debate_turn (`agents/deliberator/tests/test_dspy_turn_parity.py::test_served_records_equal_main[defender-first_turn-blank]`) | 1 failed in 4.29s | 1 passed in 4.21s |
| 07-cause | A3 original client failure type/message (`agents/deliberator/tests/test_dspy_turn_parity.py::test_served_failures_equal_main_and_keep_ledger_stop_reason`) | 18 failed in 4.84s | 18 passed in 5.00s |
| 08-once | A4 one client call (`agents/deliberator/tests/test_dspy_turn_parity.py::test_every_turn_has_one_client_call_and_one_ledger_row[defender-first_turn-valid]`) | 1 failed in 4.24s | 1 passed in 4.21s |
| 09-hashes | A5 actual system text and ledger hashes (`agents/deliberator/tests/test_dspy_turn_parity.py::test_role_system_text_is_reused_and_has_mains_hash`) | 2 failed in 4.34s | 2 passed in 4.27s |
| 10-version | A6 installed version is actually hashed (`tests/test_dspy_recipe.py`) | 1 failed, 2 passed in 3.95s | 3 passed in 1.97s |
| 11-engine-recipe | A6 engine source is actually declared (`tests/test_dspy_recipe.py`) | 2 failed, 1 passed in 4.03s | 3 passed in 2.03s |
| 12-program-recipe | A6 program source is actually declared (`tests/test_dspy_recipe.py`) | 2 failed, 1 passed in 3.94s | 3 passed in 1.95s |
| 13-thread | A7 no global LM/adapter configuration (`agents/deliberator/tests/test_dspy_concurrency.py`) | 1 failed in 3.89s | 1 passed in 3.80s |
| 14-disk | B1 disk cache disabled at import (`tests/test_dspy_boundary.py::test_served_turn_needs_no_excluded_package_cache_or_history`) | 1 failed in 3.39s | 1 passed in 5.68s |
| 15-memory | B1 memory cache disabled at import (`tests/test_dspy_boundary.py::test_served_turn_needs_no_excluded_package_cache_or_history`) | 1 failed in 3.47s | 1 passed in 5.70s |
| 16-lm-cache | B1 per-LM cache disabled (`tests/test_dspy_boundary.py::test_served_turn_needs_no_excluded_package_cache_or_history`) | 1 failed in 3.83s | 1 passed in 5.70s |
| 17-history | B1 history disabled (`tests/test_dspy_boundary.py::test_served_turn_needs_no_excluded_package_cache_or_history`) | 1 failed in 5.87s | 1 passed in 5.98s |
| 18-retries | B2 retries disabled (`tests/test_dspy_boundary.py::test_dspy_uses_only_the_agents_engine_with_sockets_refused`) | 1 failed in 5.86s | 1 passed in 5.71s |
| 19-fallback | B2 JSON adapter fallback disabled (`tests/test_dspy_boundary.py::test_dspy_uses_only_the_agents_engine_with_sockets_refused`) | 1 failed in 6.08s | 1 passed in 5.69s |
| 20-vendor | B2 own engine is mandatory; sockets refused (`tests/test_dspy_boundary.py::test_dspy_uses_only_the_agents_engine_with_sockets_refused`) | 1 failed in 3.42s | 1 passed in 5.89s |
| 21-import-wall | B3 kernel initializer does not expose DSPy (`tests/test_no_dspy_at_runtime.py`) | 1 failed in 5.27s | 1 passed in 2.99s |
| 22-other-image | B4 no other image installs optimizer (`tests/test_dspy_images.py::test_only_deliberator_installs_optimizer_with_exact_exclusions`) | 1 failed in 1.29s | 1 passed in 1.04s |
| 23-disk-exclusion | B4 diskcache excluded by name (`tests/test_dspy_images.py::test_only_deliberator_installs_optimizer_with_exact_exclusions`) | 1 failed in 1.25s | 1 passed in 1.05s |
| 24-litellm-exclusion | B4 litellm excluded by name (`tests/test_dspy_images.py::test_only_deliberator_installs_optimizer_with_exact_exclusions`) | 1 failed in 1.29s | 1 passed in 1.08s |
| 25-exact-exclusions | B4 no wider exclusion list (`tests/test_dspy_images.py::test_only_deliberator_installs_optimizer_with_exact_exclusions`) | 1 failed in 1.26s | 1 passed in 1.03s |
| 26-audit-premise | B5 unsafe installation voids acceptance (`tests/test_dspy_images.py`) | 7 failed, 3 passed in 1.32s | 10 passed in 1.07s |
| 27-audit-count | B5 accepted note counts actual installers (`tests/test_dspy_images.py`) | 2 failed, 8 passed in 1.28s | 10 passed in 1.05s |
| 28-audit-note | B5 accepted note names package exclusion (`tests/test_dspy_images.py`) | 2 failed, 8 passed in 1.42s | 10 passed in 1.06s |
| 29-golden | B6 installed DSPy reproduces the exact golden (`tests/test_guided_offline_scripts.py::test_the_golden_writer_produces_the_goldens_shape`) | 1 failed in 4.18s | 1 passed in 2.04s |
| 30-stream | extra engine stream makes one completion (`tests/test_dspy_engine.py::test_stream_preserves_the_single_completion_and_does_not_own_the_client`) | 1 failed in 4.04s | 1 passed in 1.92s |
| 31-caller-stop | extra engine uses caller's blank reason (`tests/test_dspy_engine.py::test_blank_engine_response_uses_the_callers_stop_reason`) | 1 failed in 3.99s | 1 passed in 1.94s |
| 32-uncaused | extra uncaused library error remains loud (`tests/test_dspy_engine.py::test_unexpected_error_without_a_cause_is_preserved`) | 1 failed in 4.43s | 1 passed in 1.95s |
| 33-reason | extra parser non-answer stays named (`tests/test_dspy_engine.py::test_unreadability_without_a_parser_reason_is_still_named`) | 1 failed in 4.14s | 1 passed in 1.92s |

**Audit premise against the actual tracked images (synthetic advisory input, not an external audit):**

```text
SYNTHETIC audit input; actual 15 tracked Dockerfiles:
accepted: PYSEC-2026-2447 (diskcache 5.6.3) - reachable only via the 'optimizer' extra, installed by 1 of 15 Dockerfiles; each installing command excludes diskcache by name; no fix release exists; every deployed optimizer installation excludes diskcache by name (S254, DL-266, ADR-0032) [DL-184] - retire when diskcache publishes a fixed release, or the optimizer extra is dropped
```

**Regenerated golden — actual diff:**

```diff
diff --git a/tests/fixtures/deliberation_guided_golden.json b/tests/fixtures/deliberation_guided_golden.json
index 66e32027..8e613b2f 100644
--- a/tests/fixtures/deliberation_guided_golden.json
+++ b/tests/fixtures/deliberation_guided_golden.json
@@ -4 +4 @@
-  "dspy_version": "3.3.1",
+  "dspy_version": "3.4.0",
```

**Scope/removal proof (exit values pasted):**

```text
git grep -n "guided_system\|GUIDED_TURN_PREFIX" -- kernel contracts agents orchestration surfaces scripts tests
scoped removal grep exit=1 (1 means no matches)
git diff main -- pyproject.toml uv.lock
dependency-file diff exit=0
git diff -- agents/deliberator/agent.py kernel/__init__.py kernel/deliberation.py kernel/deliberation_prompts.py kernel/deliberation_verdicts.py kernel/dspy_optimizer.py agents/operator scripts/guided_turn_replay.py docs/STATE.md tests/fixtures/guided_turn_main_records.json tests/test_deliberation.py agents/deliberator/tests/test_judge_non_answer_fail_open.py agents/deliberator/tests/test_review_veto_semantics.py
protected-path diff exit=0
```

Each diff above prints nothing. The three retired modules are removed. `pyproject.toml` and `uv.lock` are untouched; STATE is not edited on resume. All other Dockerfiles are byte-identical to the resumed HEAD.

**Module line counts — actual output, all surviving touched modules < 200:**

```text
agents/deliberator/guided_turn.py: 54
agents/deliberator/prompt_recipe.py: 75
agents/deliberator/tests/dspy_fixtures.py: 80
agents/deliberator/tests/dspy_served_probe.py: 71
agents/deliberator/tests/test_dspy_concurrency.py: 72
agents/deliberator/tests/test_dspy_runtime.py: 29
agents/deliberator/tests/test_dspy_turn_parity.py: 87
agents/deliberator/tests/test_guided_turn.py: 96
kernel/deliberation_guided.py: 152
kernel/deliberation_guided_format.py: 0 (removed)
kernel/deliberation_guided_render.py: 46
kernel/deliberation_program.py: 70
kernel/dspy_engine.py: 88
kernel/prompt_recipe.py: 91
scripts/deliberation_guided_program.py: 0 (removed)
scripts/dependency_audit_baseline.py: 50
scripts/dependency_audit_rules.py: 172
scripts/render_guided_turn_golden.py: 112
tests/dspy_boundary_probe.py: 74
tests/dspy_free_probe.py: 0 (removed)
tests/dspy_image_probe.py: 59
tests/test_deliberation_guided.py: 120
tests/test_deliberation_guided_text.py: 160
tests/test_dspy_boundary.py: 42
tests/test_dspy_engine.py: 71
tests/test_dspy_images.py: 97
tests/test_dspy_recipe.py: 51
tests/test_guided_offline_scripts.py: 137
tests/test_no_dspy_at_runtime.py: 32
tests/test_prompt_recipe.py: 185
```

**`make ci` — actual output and unavailable step:**

Command: `make ci > .venv/s254-proof/make-ci-loopback.txt 2>&1`, run from `C:/Users/yury_/Downloads/project/ta-s254`. **Exit 2**, because the external dependency-advisory lookup is blocked. `UV_OFFLINE=1`, `UV_NO_SYNC=1`, `PYTHON_DOTENV_DISABLED=1`, `PYTHONUTF8=1`; the temporary `sitecustomize` guard permits local loopback IPC only and refuses external sockets and DNS. No sync command, dependency-file change or external access was used.

Real output from the full run:

```text
Success: no issues found in 1159 source files
TOTAL                                                           19979      0   4226      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 4251 passed, 8 skipped, 2470 warnings in 312.20s (0:05:12) ==========
uv run python scripts/check_dependency_audit.py
RuntimeError: S254 no-network restriction: external sockets and DNS refused
make: *** [Makefile:59: ci] Error 1
MAKE_CI_LOOPBACK_EXIT=2
```

The remaining recipes were then run directly, with the same offline restrictions:

```text
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
DETECT_SECRETS_EXIT=0
uv run python scripts/check_untracked_secrets.py
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 11 new file(s)
UNTRACKED_SECRETS_EXIT=0
```

Logs: `.venv/s254-proof/ci-detect-secrets.txt` and `ci-untracked-secrets.txt`. This is **14 of 15 recipes passed, not a full CI pass**:

| CI recipe | Result / reason |
| --- | --- |
| 1. ruff | PASS |
| 2. format check | PASS |
| 3. mypy | PASS, 1159 source files |
| 4. import-linter | PASS |
| 5. module size | PASS; all touched modules < 200 |
| 6. module headers | PASS |
| 7. law coverage | PASS |
| 8. PARAM/settings sync | PASS |
| 9. sprint status | PASS; rerun on the final BUILT markers |
| 10. markdown links | PASS; rerun on the final handback |
| 11. version scheme | PASS; dependency files unchanged |
| 12. pytest / coverage | PASS: 4251 passed, 8 skipped; 100.00% |
| 13. dependency audit | **NOT RUN to completion:** attempted and blocked at external advisory lookup by the no-network restriction; acceptance premises are separately proven with synthetic input |
| 14. detect-secrets | PASS, run directly after the blocked recipe |
| 15. untracked secrets | PASS, run directly after the blocked recipe |

**Final handback static checks (real output, exit 0):**

```text
uv run python scripts/check_sprint_status.py
docs_seen=259 SPEC=11 BUILT=1 MERGED=247 UNMAPPED=0 MISSING=0
FINAL_SPRINT_STATUS_EXIT=0
uv run python scripts/check_markdown_links.py
FINAL_MARKDOWN_LINKS_EXIT=0
git diff --check
DIFF_CHECK_EXIT=0
```

Logs: `.venv/s254-proof/final-sprint-status.txt` and `final-markdown-links.txt`. Final staged-file detect-secrets also passes; the commit hooks recheck the staged handback.

The eight existing skips are .env isolation proofs (2), unset Celery/Postgres test configuration (3), missing optional SciPy (1), and disabled live feed tests (2). No S254/DSPy proof skips. No coverage floor was changed.

**12-item handback checklist — met:**

1. Original pre-code Law reading record retained.
2. Both original Appendix outputs retained, 132/132 twice, with their worktree.
3. Immutable main fixture already committed, with source and executed HEAD named.
4. Original A1 red output retained.
5. All A1-A7/B1-B7 rows name files, passing status and clauses.
6. All 33 guarded-property mutations have red and restored-green output, one row each.
7. Exactly DLIB-NEV-10, v1.13, S254/ADR-0032 Changelog, B2 citation, test-plan row and both rollups; existing 59 clauses unchanged.
8. All three retired modules removed; corrected source-scoped grep prints nothing.
9. Real writer regenerated the golden; pasted diff changes only its DSPy version value.
10. `git diff main -- pyproject.toml uv.lock` prints nothing; neither file edited.
11. Actual full CI log/exit recorded, every recipe accounted for and blocked advisory lookup named NOT RUN.
12. Actual touched-module counts pasted, each < 200; Status BUILT in this spec and its README row.

---

## Return notes

The planner's corrected command was followed on the same worktree/branch, with no pull. The original law-reading record, Appendix outputs, main fixture, A1 red/probe and DL-267 stand; none was recaptured or redone. The corrected source-scoped removal grep is empty, and B3 proves the actual 13 module CMDs plus the dispatcher script. The actual `ci:` target has 15 recipes, including sprint status; the older 14-step count was treated as a count correction, with every recipe accounted for.

**Execution-profile correction:** The first `make ci` (`.venv/s254-proof/make-ci.txt`, exit 2) used an overly broad temporary socket/DNS block. It caused two existing loopback HTTP tests and Windows asyncio's local socket pair to fail, plus its destructor warning in a later test: 4 failed, 4247 passed, 8 skipped; 99.88% coverage. No repository code or tests were changed to compensate. The scratch guard now permits loopback addresses only and resolves them numerically; external TCP, UDP and DNS remain refused before access. The affected 18 tests then passed in 5.10s (`local-ipc-restored.txt`, exit 0). The full CI target was rerun with that corrected profile. This is a local test setup correction under the updated stop rule, not a change to a role's behavior or a law.

The immutable fixture still names source `9f4051ad2f52300fc2c4a87637b72e7464fc5f16` and executed worktree HEAD `ab88b9162b61c43b8405567b231e52c7e88af1bc`; their source equivalence was recorded before implementation. The existing five scoped false positives are public commit/prompt digests, not credentials. No `.env` was opened, no dependency file was edited, and STATE was not edited on resume.

**Carry-forward / not done:** The full external dependency audit, remote CI/exact-SHA gate, push, merge, Docker build, deployment and live replay are not done under this handover's restrictions. The planner still owes D2 (DSPy in the dev group and the feature version/lock bump) at merge. Local main was not changed by this work. The runtime build, recorded-parity tests, law cycle and all guard proofs are complete; BUILT describes that state and does not claim remote/deployed/live proof.

---

## Planner's review and merge-time work — 2026-10-07 15:51 AEDT

**The handback is accepted.** Re-measured by the planner, not read from the builder's logs:

| Claim | Value | How it was measured |
| --- | --- | --- |
| A turn on the branch equals a turn on `main` | **168 of 168** rows byte-identical: the record or the exception, and the one call's system text, user text and tool schema | *[measured]* one script run in each tree (`main` at `967bebb0`, the branch at `a4d3c563`), the two dumps compared with `cmp`. The spec's 132 cases plus 36 the golden does not hold: fenced JSON, plain prose, non-ASCII text, CRLF line ends, a field written twice, a missing closing marker |
| The system prompt hashes | the defender's and the challenger's SHA-256 are equal in both trees and equal the fixture's two values | *[measured]* same run |
| Packages loaded by a served turn | `dspy` loaded on the branch; `litellm` and `diskcache` not loaded | *[measured]* same run |
| The builder's planned tests | 368 passed | *[measured]* re-run by the planner |
| The guards can fail | 4 of the builder's 33 re-broken by the planner, each red and then green: the Dockerfile without the `diskcache` exclusion, `num_retries=3`, `kernel/__init__.py` importing the engine, the JSON fallback left on | *[measured]* |

**Decision D2, done by the planner on this branch.** `dspy>=3.4.0` in the `dev` group and in the
`optimizer` extra; version `0.122.00`; `uv lock` added 4 lines and removed 2, and no package's version
moved. The move opened a second route to `diskcache`, closed in the same commit
([DL-268](../design-log.md)).

**A CodeQL error on the pushed branch, fixed before the merge.** The remote gate was proven for
`da04677d` (CI, CodeQL, Security Findings). That gate reads `main`'s alerts, so it cannot see a
branch's. The branch's open alerts were therefore compared with the last merged branch's 131, and two
were new:

- `py/unsafe-cyclic-import`, **error** level, on `kernel/deliberation_guided_render.py`. The renderer
  imports `GuidedReasoning` for type checking only, and `kernel/deliberation_guided.py` imported the
  renderer back for two re-exports. Nothing fails at run time, but `main` holds 0 open error-level
  alerts and its security gate fails on a new one.
- `py/implicit-string-concatenation-in-list`, a warning, on one B5 case.

Fix: `kernel/deliberation_guided.py` no longer imports the renderer, and the two callers import
`render_guided_text` and `render_transcript` from `kernel.deliberation_guided_render`. The B5 case
joins its two lines with `+`. The 168-row comparison with `main` was re-run after the fix: identical.

**`make ci`, Windows, the environment synced with no extra (CI's):** exit 0, all 15 steps. 4,255 passed, 8 skipped, 100.00 % coverage. The dependency audit ran against the network, which the builder's sandbox could not do: no unaccepted vulnerability, 1 accepted advisory re-checked.

**Still owed, in the order of "Sequencing after merge":** the remote gate for the pushed commit, the
merge, the image check in the built container, the retag (not before the fidelity verdict), F1 and F2.

---

## Appendix — the reference shape, and the script behind the Measured table

The classes `StrictGuidedAdapter` and `ClientEngine` and the functions `run_program` and
`dspy_guided_turn` below are the measured shape of decisions D1 and D3 to D7. The rest of the script
compares that shape with `main`'s `guided_turn`. Expected output, both ways: `cases 132: same record
or same exception 132, same single vendor call with the same text 132`, neither package loaded, 0
files in the cache directory, 0 calls in the global history.

```python
"""S254 reference shape and its proof: a guided turn run by DSPy, against main's turn.

Run from a checkout of `main` at `02e4f865` whose environment has the lock's DSPy (3.4.0). It makes
no LLM call and no network call, and needs no `.env`:
  PYTHONPATH=. uv run --no-sync python <this file>          # the comparison
  PYTHONPATH=. uv run --no-sync python <this file> block    # with litellm and diskcache unimportable
It imports main's own `guided_turn`, so it stops running once the sprint replaces that function.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

BLOCKED = {"litellm", "diskcache"} if sys.argv[1:] == ["block"] else set()


class _Blocker:
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in BLOCKED:
            raise ImportError(f"blocked by the probe: {name}")
        return None


sys.meta_path.insert(0, _Blocker())
CACHE = tempfile.mkdtemp(prefix="s254-dspy-cache-")
os.environ["DSPY_CACHEDIR"] = CACHE

import dspy  # noqa: E402
from dspy.clients.base_lm import GLOBAL_HISTORY  # noqa: E402
from dspy.lm15 import Message, Response, TextPart, Usage, response_to_events  # noqa: E402
from dspy.utils.exceptions import LMUnexpectedError  # noqa: E402

from agents.deliberator.guided_turn import GUIDED_SYSTEMS  # noqa: E402
from agents.deliberator.guided_turn import guided_turn as main_guided_turn  # noqa: E402
from contracts.deliberator import DebateProposition, DebateTurnRecord, DebateTurnRequest  # noqa: E402
from kernel.deliberation import CHALLENGER_SYSTEM, DEFENDER_SYSTEM, Turn  # noqa: E402
from kernel.deliberation_guided import (  # noqa: E402
    GuidedReasoning,
    guided_user,
    parse_guided_turn,
    render_guided_text,
    render_transcript,
    unreadable,
)
from kernel.llm import LLMCompletionStoppedError  # noqa: E402

dspy.configure_cache(enable_disk_cache=False, enable_memory_cache=False)


class DebateTurn(dspy.Signature):
    decision: str = dspy.InputField(desc="the decision under test")
    context: str = dspy.InputField(
        desc="the evidence packet for this decision; every value you read comes from here"
    )
    transcript: str = dspy.InputField(desc="the debate so far")
    argument: str = dspy.OutputField(
        desc="step 3: your turn, at most ~5 sentences, built only from your readings and gaps"
    )


class UnreadableTurnError(Exception):
    """The completion could not be read as a guided turn; it and the reason are kept."""

    def __init__(self, reason: str, completion: str) -> None:
        super().__init__(reason)
        self.reason, self.completion = reason, completion


class StrictGuidedAdapter(dspy.ChatAdapter):
    """DSPy's chat format, parsed with strict JSON (DL-252 D6)."""

    def __init__(self) -> None:
        super().__init__(use_json_adapter_fallback=False)

    def parse(self, signature, completion):
        turn = parse_guided_turn(completion)
        if turn.error is None and not turn.argument:
            turn = unreadable("empty field: argument")
        if turn.reasoning is None:
            raise UnreadableTurnError(turn.error or "unreadable", completion)
        return {"reasoning": turn.reasoning, "argument": turn.argument}


class ClientEngine:
    """A DSPy engine: every request goes through the agent's own LLM client."""

    def __init__(self, llm) -> None:
        self._llm = llm

    def complete(self, request):
        text = self._llm.complete(system=request.system, user=request.messages[0].text, tool_schema={})
        if not text.strip():
            raise LLMCompletionStoppedError(provider="kernel", stop_reason="empty_debate_turn")
        return Response(id=None, model=request.model, message=Message.assistant([TextPart(text)]),
                        finish_reason="stop", usage=Usage(input_tokens=0, output_tokens=0, total_tokens=0))

    def stream(self, request):
        return response_to_events(self.complete(request))

    def close(self) -> None:
        pass


ADAPTER = StrictGuidedAdapter()
PROGRAMS = {
    role: dspy.ChainOfThought(DebateTurn.with_instructions(prompt), rationale_field_type=GuidedReasoning)
    for role, prompt in (("defender", DEFENDER_SYSTEM), ("challenger", CHALLENGER_SYSTEM))
}


def run_program(program, llm, **inputs):
    lm = dspy.LM("custom/deliberator", engine=ClientEngine(llm), cache=False, num_retries=0)
    try:
        with dspy.context(lm=lm, adapter=ADAPTER, disable_history=True):
            return program(**inputs)
    except LMUnexpectedError as exc:
        if exc.__cause__ is not None:
            raise exc.__cause__ from None
        raise


def dspy_guided_turn(llm, request: DebateTurnRequest) -> DebateTurnRecord:
    transcript = tuple(Turn(t.role, t.round, t.text) for t in request.transcript)
    try:
        pred = run_program(
            PROGRAMS[request.role],
            llm,
            decision=request.proposition.decision,
            context=request.proposition.context,
            transcript=render_transcript(transcript),
        )
    except UnreadableTurnError as exc:
        return DebateTurnRecord(role=request.role, round=request.round_number,
                                text=exc.completion.strip(), reasoning_error=exc.reason)
    return DebateTurnRecord(role=request.role, round=request.round_number,
                            text=render_guided_text(pred.reasoning, pred.argument), reasoning=pred.reasoning)


class Client:
    def __init__(self, answer):
        self.answer, self.calls = answer, []

    def complete(self, *, system, user, tool_schema):
        self.calls.append((system, user))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def outcome(fn, answer, request):
    client = Client(answer)
    try:
        result = fn(client, request).model_dump(mode="json")
    except Exception as exc:
        result = {"raised": type(exc).__name__, "text": str(exc)}
    return result, client.calls


golden = json.loads(Path("tests/fixtures/deliberation_guided_golden.json").read_text(encoding="utf-8"))
earlier = (DebateTurnRecord(role="defender", round=1, text="Readings: none\nGaps: none\nArgument: A."),)
same_record = same_text = cases = 0
for role in ("defender", "challenger"):
    for user_case in golden["user"]:
        inputs = user_case["inputs"]
        request = DebateTurnRequest(
            request_id="r",
            proposition=DebateProposition(decision=inputs["decision"], context=inputs["context"]),
            role=role, round_number=1, transcript=earlier if role == "challenger" else (),
        )
        for answer in [c["completion"] for c in golden["parse"]] + [
            "", "   \n", LLMCompletionStoppedError(provider="anthropic", stop_reason="max_tokens"),
            RuntimeError("provider down"), TimeoutError("timed out"),
        ]:
            old, old_calls = outcome(main_guided_turn, answer, request)
            new, new_calls = outcome(dspy_guided_turn, answer, request)
            cases += 1
            same_record += old == new
            same_text += old_calls == new_calls and len(new_calls) == 1
            if old != new or old_calls != new_calls:
                print("DIFF", role, user_case["name"], repr(answer)[:60], "\n  main:", str(old)[:200], "\n  dspy:", str(new)[:200])
            assert new_calls[0][0] == GUIDED_SYSTEMS[role]
print(f"dspy {dspy.__version__}; cases {cases}: same record or same exception {same_record}, "
      f"same single vendor call with the same text {same_text}")
print("per role and user case:", len(golden["parse"]), "parse cases, 2 blank completions, 3 failures;",
      "roles 2; user cases", len(golden["user"]))
print("blocked:", sorted(BLOCKED) or "nothing", "| litellm loaded:", "litellm" in sys.modules,
      "| diskcache loaded:", "diskcache" in sys.modules)
print("files in DSPy's cache directory:", len(os.listdir(CACHE)),
      "| calls DSPy kept in its global history:", len(GLOBAL_HISTORY))
```
