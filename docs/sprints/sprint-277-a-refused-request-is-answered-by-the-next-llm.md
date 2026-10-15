<!-- Agent: planning | Role: sprint handover -->
# Sprint 277 — a request a vendor refuses is answered by the role's next declared LLM, and the role stays on it

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-277-a-refused-request-is-answered-by-the-next-llm`
**Status:** MERGED
**Version:** `0.128.00` (MINOR)
**Effort:** L
**Decisions:** [DL-289](../design-log.md) (the direction, operator 2026-10-11; P3 is this sprint; amendment 4 holds its ten decisions, made and measured) · [DL-282](../design-log.md) (S262's one-key rule, reversed here for the three declared roles alone) · [work-queue 123](../work-queue.md)

> **Why this bump kind.** A new capability: an LLM role that the vendor refuses during the night
> moves to the next declared LLM instead of failing its orders open. The master gains a fallback
> hand-over and a recorded property, the deliberator a chain of clients and two recorded
> properties, and the brief names the move. MINOR.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md`, `orchestration/laws/dispatcher/laws.md` | One component's **locked constitution** | **LOCKED. Read-only during a build**, except the text the Appendix § 6 gives, applied exactly. A clause you believe is wrong is a `drift-register.md` row plus a STOP |
| `.../laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: master **`OUT`**, **`NEV`**, **`FAIL`**, **`OBS`**, **`SEC`**; deliberator
**`OUT`**, **`STA`**, **`FAIL`**, **`OBS`**, **`DEP`**, **`PARAM`**; dispatcher **`OUT`**.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.**
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No file in `contracts/` changes. Yes, it adds guarantees**, so it owes a law cycle in this unit of
work, and the clause text is fixed by the planner (Appendix § 6):

- **Master v1.11 → v1.12:** `MST-OUT-05` amended (every candidate is probed; each later one that
  passes is handed over as a fallback with its vendor's key, recorded as `llm_fallbacks`);
  `MST-OUT-04`, `MST-NEV-07`, `MST-FAIL-08` and `MST-OBS-04` amended for it. No clause added.
- **Deliberator v1.17 → v1.18:** new `DLIB-FAIL-05` (a request a vendor answers with an error status
  goes to the next candidate, and the process stays there); `DLIB-FAIL-01`, `DLIB-OUT-02`
  (`llm_switches`) and `DLIB-DEP-05` amended; PARAM gains `llm_fallbacks` and rewords
  `llm_provider`.
- **Dispatcher v1.4 → v1.5:** `DSP-OUT-09` amended (the LLM line also names the run's switches).

You write a `test-plan.md` row for `DLIB-FAIL-05` citing **your** tests, widen each amended clause's
row with your tests (and its description where the clause's meaning grew), set each test plan's
header version, and set the three books' rows in **both** `docs/laws/ledger.md` and
`docs/laws/INDEX.md` to the new version and the count the law gate derives. 🪤 **The roll-up is
derived, not declared**: on the prototype the gate derived **master 33 / 58, deliberator 35 / 66,
dispatcher 43 / 47**. Let the gate tell you yours.

*Read and left unchanged, on purpose:* `DLIB-STA-03` (a peer writes only `LLMCall` rows; the switch
is recorded on the row, which is why there is no new node), `DLIB-OBS-08` (every attempt is its own
row, `:repeat-N`), `MST-NEV-06` (only a candidate whose probes passed is handed over), `MST-NEV-08`
(a role without the new `fallbacks` key is already "a field that is not a non-empty string").

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/master/model_choice.py`, `model_candidates.py`, `credential_test.py`, `credential_outcomes.py`, `credential_report.py` | `agents/master/laws/laws.md` + `test-plan.md` | `MST-OUT-04`/`05`, `MST-NEV-06`/`07`/`08`, `MST-FAIL-04`/`08`, `MST-OBS-04`, `MST-SEC-02`/`04` |
| `agents/deliberator/model_chain.py`, `turn_ledger.py` (new); `agent.py`, `entrypoint.py`, `settings.py`, `review_record.py`, `store.py`, `poll.py` | `agents/deliberator/laws/laws.md` + `test-plan.md` | `DLIB-FAIL-01`/`04`/`05`, `DLIB-OUT-02`/`03`/`05`, `DLIB-STA-03`, `DLIB-OBS-05`/`07`/`08`, `DLIB-DEP-05`, `DLIB-NEV-10`/`11`, `DLIB-SEC-02`, PARAM |
| `kernel/llm_ledger.py` | the deliberator book (`DLIB-OUT-03`, `DLIB-OBS-08`); `agents/operator/laws/laws.md` (the operator writes rows through the same ledger) | an optional argument; every row written without it is byte for byte as before |
| `orchestration/llm_brief.py`, `daily_brief_facts.py` | `orchestration/laws/dispatcher/laws.md` + `test-plan.md` | `DSP-OUT-06`/`08`/`09` |
| `orchestration/packs/trading_llm.json`, `trading_graph_vocabulary.json` | master + deliberator books; [ADR-0012](../decisions/) (pack data, never substrate code) | the master reads the declaration as injected data (`MST-NEV-05`, `MST-DEP-05`); the vocabulary's lists stay sorted |
| `infra/deploy-agents.ps1` | master book (`MST-OUT-05`); the S276 spec's `llm-candidates` step | the step sets the vocabulary before the packs, now on every role too |

⚠️ **The invariant: with every vendor answering, every request a debate sends is the one it sends
today, and no file the fidelity count calls a decision path changes**
(`scripts/replay_fidelity_git.py::DECISION_PATHS`: `contracts/`, the scanner, analyst and PM,
`trading_tunables.json` among them). The first candidate is tonight's `openai` / `gpt-5.5` /
`high`; the deliberator moves only on a vendor's error answer. What does change on a quiet night is
named: each role's activation and each fleet check probe the second candidate too (one Anthropic
probe each), each role holds the second vendor's key, and three records gain a property
(`AgentInstance.llm_fallbacks`, `DeliberationRun.llm_switches`, the `LLMCall` row's
`llm_passed_over`, the last only when a candidate refused). **If your change would touch a decision
path, STOP and report.**

---

## Goal

At merge, the master probes every declared candidate at each activation and fleet check and hands
each deliberator role, after its chosen candidate, every later candidate whose probes also passed,
as its fallbacks, with each fallback vendor's key; the `AgentInstance` records them. When a vendor
answers one of the role's requests with an HTTP error status (400 to 599), the role sends that
request to its next candidate and stays on it for the rest of the process; a time-out, a dropped
connection, a truncated completion or an unreadable reply moves nothing, as today. Each attempt is
its own `LLMCall` row under its own model, the row after a refusal names what refused it, the run's
`DeliberationRun` says which role switched to which model and why, and the brief's LLM line says so.
An order fails open only when the role has no candidate left. Every other agent type is unchanged.

## Why (context)

DL-289 is the operator's direction of 2026-10-11, after work-queue 123 asked what a debater should do
when its vendor refuses it: *"Refuse to start when another LLM can do the job and miss a day's run is
not a best Idea. Let's create a list of LLM that can replace currently not working one."* S276 (P1,
P2) built the list and the choice at activation and is deployed as `s276`. It left one hole by
design: a vendor that starts refusing **after** activation — an account that runs dry mid-week, as
Anthropic's did on 2026-10-06 (DL-265), a revoked key, a rate limit the SDK's own retries do not
outlast — still fails every order of the night open, with the second vendor's key never handed over.
P3 closes it: *"A turn whose request the vendor refuses before generation is retried once on the next
candidate, and the process stays on that candidate"* (DL-289).

### Measured, 2026-10-15 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| How the SDKs carry a vendor's refusal | `openai.AuthenticationError` and `anthropic.AuthenticationError`, each with `status_code=401` | *[measured 2026-10-15, no cost]* `s277_switch_measure.py` M1: the real adapters with made-up keys, refused before generation |
| A time-out carries no status | `APITimeoutError`, `status_code` `None` | *[measured]* same script, M2: a 1 ms client time-out |
| What a drained account answers | Anthropic `400 invalid_request_error … credit balance is too low`; both are error statuses, so both move | *[measured 2026-08-20 and on the four blind nights]* DL-001-to-140 and DL-141-to-175 archives |
| What `main` does with one refused turn | `debate_turn` raises; the order fails open (`DLIB-FAIL-01`) | *[measured]* M7 on `main` `e38a99ef` (`s277_measure_main_e38a99ef.txt`) |
| What the prototype does | the request answered on the second candidate, two rows (`gpt-5.5` empty, `claude-opus-5` with `llm_passed_over`), the process on the second for the next request; both refused raises the second's refusal; through the DSPy turn the reasoning is read and the switch line written | *[measured]* M3–M6 (`s277_measure_proto.txt`) |
| Why a time-out does not move | both SDKs time out a read after 600 s and retry twice (`openai` 2.49.0, `anthropic` 0.120.2, adapters built on the defaults); the manager stops waiting for a peer turn after `request_timeout_seconds`, 240 live | *[measured]* `s277_rollback_check.txt` prints both SDKs' `DEFAULT_TIMEOUT`; *[read]* `kernel/llm_openai.py`; the 240 is a live-only setting (STATE, Standing conditions) |
| Extra probes the change costs | 9 to 61 Anthropic probes a UTC day over 2026-10-06 to 10-15 (one per deliberator activation, three per fleet check), each `max_tokens: 1` | *[measured 2026-10-15, read-only]* `s277_probe_counts.py` on the live graph; the high days were deploy days |
| What one such probe costs | *[ASSUMED — not measured]* under a tenth of a cent: one output token and a one-character prompt | F1b of S276 measured that it answers 200, not its price |
| The `s276` images read what S277 ships | `s276`'s parser reads the new pack (both candidates, three roles); `s276`'s settings start with `DELIBERATOR_LLM_FALLBACKS` set and ignore it | *[measured]* `s277_rollback_check.py` on `main` `e38a99ef` |
| What the prototype breaks | 2 of the 5,032 existing tests: S276's A1 and A3, which assert that no later candidate is probed; one more file's import of the moved ledger wrapper is edited (§ 7) | *[measured]* the full suite on the prototype's production change, before its own tests |
| The change touches no decision path | 0 of the 37 changed or new files (`s277_decision_paths.txt`) | *[measured on the prototype]* `DECISION_PATHS` against `git diff origin/main` |
| The prototype's gate | `make ci` exit 0, sixteen steps: 5,075 passed, 9 skipped, 100.00 %; the dependency audit clean | *[measured 2026-10-15]* `s277-proto-make-ci.txt`, Windows, `../ta-s277-proto`, no `.env` |

Evidence outside the repo: OneDrive `trading-agents-data/wq123p3-2026-10-15/`.

---

## Scope — and what is deliberately NOT here

1. **The master hands over fallbacks (Appendix § 1).** Every candidate is probed at each activation
   and fleet check. The first that passes is chosen, as in S276; each later one whose probes pass is
   a fallback; every other candidate is passed over, before the chosen one or after it. The role's
   declaration gains a fourth key, `fallbacks` (`DELIBERATOR_LLM_FALLBACKS`), which ACTIVATE fills
   with the fallbacks' `vendor/model/effort` labels joined by commas (empty when none), and ACTIVATE
   keeps each fallback vendor's key. `AgentInstance.llm_fallbacks` records the labels.
2. **The deliberator moves on a refusal (§ 2, § 3).** A new `ModelChain` holds one client per
   handed-over candidate; the ledger wrapper, moved to `turn_ledger.py`, sends a request a vendor
   answered with an error status to the next candidate, once per candidate, and the process stays
   there. Each attempt is its own `LLMCall` row under its candidate's model; the row of an attempt
   made after a refusal carries `llm_passed_over`.
3. **The run says so (§ 3).** `DeliberationRun.llm_switches` holds one line per role that answered
   on a later candidate, read from the rows the manager already reads for `role_models`.
4. **The brief says so (§ 4).** `DSP-OUT-09`'s line names each switch, after the activation parts.
5. **The deploy (§ 5).** The `llm-candidates` step sets the vocabulary on the master and on each role
   named in the pack before it sends the packs.
6. **The law cycle** of three books (§ 6) and **three named existing-test edits** (§ 7).

### Out of scope (do NOT build this sprint)

- **A switch on a time-out or a dropped connection.** The call's fate is unknown and, at the SDK's
  600-second read time-out, the manager stopped waiting 360 seconds earlier (Measured).
- **Moving back to the first candidate during the night**, or re-probing it. The process stays where
  it moved; the next night's activation starts from the first candidate again.
- **The operator's chat on the list.** The operator keeps one declared vendor (DL-289, *not now*).
- **`contracts/`, `trading_tunables.json`** and every other decision path.
- **The dashboard.** No view beyond the graph and the brief.
- **`switch_llm_config.py` / `switch_llm_proof.py`.** The switch still proves a choosing app by its
  `llm_candidate`, which is unchanged.
- **No ADR reversal.**

### The road not taken (LAW-06)

- **A new `LLMSwitch` node written at the switch.** Rejected: `DLIB-STA-03` says a peer writes only
  its `LLMCall` rows, and the row the switch produced is where the fact belongs.
- **Record the reason in the refused row's `stop_reason`.** Rejected: `kernel/llm_outage.py` counts a
  row with an empty response and stop reason `unknown` as silent; a refusal must stay silent there.
- **Put the chain inside the vendor client, below the ledger.** Rejected: one row per turn would name
  the first candidate's model for an answer the second gave, and the refused attempt would leave no
  row.
- **Hand over a fallback the master has not proven.** Rejected: DL-36 and `MST-NEV-06`.
- **Let the deliberator probe its fallbacks itself.** Rejected: the master is the one process that
  tests a credential before handing it over (`MST-NEV-06`).
- **Make `fallbacks` optional in the pack.** Rejected: a new master reading an old pack would run
  with no fallback and say nothing; required, the step that ships the pack runs before the retag.
- **The vendor's message in the reason.** Rejected: unbounded text on every row; `http_<status>` is
  enough to act on, and a request that finally fails still records the vendor's message in its
  fail-open reason.
- **Fail the request on a refusal of a candidate the process has already left.** Rejected: under the
  manager's three concurrent orders, a refusal that was in flight when another thread moved would
  then fail an order the second candidate could answer.

---

## The design decisions — made, and recorded in DL-289 amendment 4

The planner made them and measured them on the prototype; the builder applies them, never re-decides.

1. **D1 — every candidate is probed.** `choose_llm` no longer stops at the first pass. Chosen: the
   first that passes (S276). Fallbacks: each later one whose probes passed (refused and unanswered
   alike are not). Passed over: every other, with its reason, before or after the chosen.
2. **D2 — the hand-over.** The role's fourth declared key, `fallbacks`, holds the fallbacks' labels
   joined by commas, in order, empty when none; ACTIVATE keeps the key of each vendor the chosen
   candidate or a fallback names and withholds every other. S262's one-key rule (DL-282) is reversed
   for the declared roles alone. `AgentInstance.llm_fallbacks` records the labels; the fleet check
   is unchanged (a passed-over fallback lands in its `llm_passed_over`, failing nothing).
3. **D3 — what moves.** A request a vendor answered with an HTTP error status, read from the SDK
   exception's `status_code` (an `int`, not a `bool`, 400 to 599). Nothing else moves.
4. **D4 — the process stays.** The chain moves past a refused candidate and never back. A refusal by
   a candidate the process already left is sent to the one in use, so concurrent orders move it once
   and a request tries each candidate at most once. With no candidate left the refusal is raised.
5. **D5 — where.** In the ledger wrapper (`LedgerLLM`, moved from `agent.py` to `turn_ledger.py`),
   above the vendor client and below DSPy: DSPy sees one answer or one exception, as today.
6. **D6 — the row.** The kernel ledger takes an optional `passed_over` and writes `llm_passed_over`
   only when it is not empty; the refused attempt's own row is written as today.
7. **D7 — the run.** `review_record.llm_switches` reads the run's answered rows (the keys
   `role_models` already reads) into lines `<agent> switched to <model> (passed over <lines>)`,
   distinct, in row order; `DeliberationRun.llm_switches` is always written, empty when none.
8. **D8 — the brief.** `llm_line` takes the run's `DeliberationRun`; each switch line follows the
   activation parts with ` during the run`.
9. **D9 — the start.** `build_role_models` builds the chosen client, then one per fallback through
   `build_llm` (so a foreign model is refused, `DLIB-NEV-11`); an unreadable fallback label stops
   the role before any request; `main` uses it.
10. **D10 — the deploy.** The `llm-candidates` step sets the vocabulary on the master, then on each
    role in the pack's `roles`, each read back, and sends the packs only when all succeeded; then
    the image-only retag. Never the retag first: the new master writes `llm_fallbacks` on every
    activation and the new manager writes `llm_switches` on every run.

🪤 **Take no new DL number.** These decisions are DL-289 amendment 4, already in the log on `main`
(the planner's). Do not edit `docs/design-log.md`.

---

## Blast radius — measured 2026-10-15

| What | Detail |
| --- | --- |
| Files changed | 19 production files (2 new, 17 changed), 3 law books, 3 test plans, 2 roll-ups, 2 existing test files; sizes in Guardrails |
| Agents affected | master, deliberator (three roles), the dispatcher job (the brief); `kernel/llm_ledger.py`; tooling (deploy). No agent imports another (`import-linter` green on the prototype) |
| Contract change? | No |
| Graph vocabulary change? | **Yes**: `AgentInstance.llm_fallbacks` (master), `DeliberationRun.llm_switches` and `LLMCall.llm_passed_over` (deliberator) |
| New env keys / tunables | `DELIBERATOR_LLM_FALLBACKS` (handed over by the master at activation, never set by a deploy); deliberator tunable `llm_fallbacks` |
| Deploy implication | **Not image-only.** First `deploy-agents.ps1 -Action llm-candidates` (the vocabulary on the master and the three deliberator apps, then the master's credential and LLM packs, each read back), then the image-only retag of the 16 apps and the job. 🪤 **Never the retag first** (D10) |
| Rollback | Retag to `s276`. The `s276` master reads the new pack and hands over one candidate, as before; the `s276` deliberator ignores `DELIBERATOR_LLM_FALLBACKS` (both measured). The wider vocabulary and the new pack stay and are additive. Rows written meanwhile keep the new properties |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Plant the failing tests first** (Test plan below) and watch them fail: on the unchanged tree
   every new test file fails to import or fails. Paste the red output.
3. **Apply the Appendix § 1 to § 5 exactly.** Change nothing else in production code.
4. **Law cycle:** § 6's text exactly, then your test-plan rows and the roll-ups.
5. **The three existing-test edits** (§ 7), exactly.
6. **Prove the guards can fail (DL-70):** plant the breaks under *Traps*, one at a time, each red on
   one of your tests; restore each.
7. **Bump the version (MINOR)** in `pyproject.toml` and run `uv lock --offline`; stage `uv.lock`.
8. **`make ci` green** — every step, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Name the tests as you like; cite the clause in each docstring. Every row must be a test of yours.
`FIRST` is `openai/gpt-5.5/high`, `SECOND` `anthropic/claude-opus-5/max`. A refusing client is any
stand-in whose `complete` raises an exception with an integer `status_code`.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A refusal moves the request and the process | a chain FIRST (refuses, one case each of 400, 401, 403, 404, 429, 500, 503, 529, 599) then SECOND (answers) | the request returns SECOND's answer; a second request goes to SECOND alone; FIRST was sent one request; rows `r1` (`gpt-5.5`, no `llm_passed_over`), `r1:repeat-1` (`claude-opus-5`, `llm_passed_over` = `FIRST: http_<status>`), `r2` (`claude-opus-5`, none) (`DLIB-FAIL-05`) |
| A2 | 🪤 No status moves nothing | FIRST raises, one case each: `TimeoutError`, `ConnectionError`, `status_code` `None`, `"429"`, `True`, `399`, `600`, `LLMCompletionStoppedError` | the same exception is raised; SECOND was never sent anything; the chain stays on FIRST; one row (`DLIB-FAIL-05`) |
| A3 | The last candidate refused fails the request | FIRST 429, SECOND 400 | SECOND's refusal is raised (status 400); the chain is on SECOND; a next request is sent to SECOND alone and raises; a chain of one candidate has nothing after it (`DLIB-FAIL-05`, `DLIB-FAIL-01`) |
| A4 | 🪤 A refusal of a candidate already left goes to the one in use | three candidates | `after(first)` twice gives the second both times; `after(second)` the third; `after(third)` `None`; then `after(first)` the third, and the chain stays on the third (`DLIB-FAIL-05`) |
| A5 | 🪤 Concurrent refusals skip no candidate | three threads on one chain whose FIRST refuses all three at once (a barrier), a SECOND that answers, a THIRD that must never be called | all three answer SECOND's text; FIRST was sent three, THIRD none; the chain is on SECOND (`DLIB-FAIL-05`) |
| A6 | The reason is the status alone | `refusal()` on status 429, 400, `False`, and a `ValueError` whose text reads like a 429 | `http_429`, `http_400`, `None`, `None` (`DLIB-FAIL-05`) |
| A7 | The role is built on what it was handed | opponent settings: openai, `gpt-5.5`, `high`, `llm_fallbacks` = `" SECOND ,,"`; an injected builder | labels `[FIRST, SECOND]`; the first client is the one given; the builder called once with `anthropic`, the anthropic key from the environment, `claude-opus-5`, the role's `max_tokens`, `max`; no fallbacks gives one candidate (`DLIB-DEP-05`) |
| A8 | 🪤 An unreadable fallback stops the role | `llm_fallbacks` each of `anthropic/claude-opus-5`, `anthropic//max`, `a/b/c/d`, `/claude-opus-5/max` | `ValueError` naming an unreadable fallback (`DLIB-DEP-05`) |
| A9 | 🪤 A fallback the kernel refuses stops the role | `anthropic/gpt-5.5/max`; `opnai/gpt-5.5/high`; an empty chain | `ModelProviderMismatchError`; `UnknownProviderError`; `ValueError` (`DLIB-NEV-11`, `DLIB-DEP-05`) |
| A10 | 🎯 A run records the switch | a real review over the in-process bus, two rounds: the proponent answers, the opponent's chain FIRST (429) then SECOND (answers), the manager rules `uphold` | `failed_open_count` 0, `real_debate_count` 1, `role_models.challenger` `claude-opus-5`, `llm_switches` = `["deliberator-opponent switched to claude-opus-5 (passed over openai/gpt-5.5/high: http_429)"]`, three opponent rows (`DLIB-OUT-02`, `DLIB-FAIL-05`) |
| A11 | No switch, an empty list | rows without, with an empty, and with a non-list `llm_passed_over`; a missing key; no graph; two rows with the same switch | `[]`, `[]`, then one line (`DLIB-OUT-02`) |
| A12 | The entrypoint runs the role on its chain | proponent settings with `llm_fallbacks` `openai/gpt-5.5/xhigh` and an OpenAI key | `build_role_models` gives labels `[FIRST, openai/gpt-5.5/xhigh]` with efforts `high`, `xhigh`; `main`'s source calls `build_role_models(settings, os.environ)` (`DLIB-DEP-05`) |
| A13 | 🎯 A refused fallback is passed over and its key withheld | the real packs; the anthropic probe answers 400 | probes `[FIRST, SECOND]`; `DELIBERATOR_LLM_FALLBACKS` `""`; `OPENAI_API_KEY` present, `ANTHROPIC_API_KEY` absent; `llm_fallbacks` `[]`; `llm_passed_over` `[SECOND: unrecoverable:http_400]`; passed `["openai:gpt-5.5:high"]`; no fault (`MST-OUT-05`, `MST-FAIL-08`, `MST-NEV-07`, `MST-OBS-04`) |
| A14 | 🪤 An unanswered fallback is never handed over | the anthropic probe times out | fallbacks `""`, no anthropic key, passed over `SECOND: TimeoutError`, no transport failure recorded, no fault, the fleet check passes (`MST-FAIL-08`, `MST-NEV-06`) |
| A15 | A refused fallback fails no fleet check | the anthropic probe answers 429 | `passed` true, `failure_count` 0, `llm_passed_over` one `<role>: SECOND: unrecoverable:http_429` line for each of the three roles (`MST-OUT-04`, `MST-FAIL-08`) |
| A16 | No fallback after the last or an unproven choice | first 429 / second 200; first 401 / second 503 | fallbacks `""`, no OpenAI key, `llm_candidate` SECOND, `llm_fallbacks` `[]` (`MST-OUT-05`, `MST-FAIL-08`) |
| A17 | 🪤 Every role names its fallbacks key | the committed `trading_llm.json`; the same with one role's `fallbacks` removed | each role's key is `DELIBERATOR_LLM_FALLBACKS`; the edited pack is refused naming `'fallbacks'` (`MST-NEV-08`, `MST-OUT-05`) |
| A18 | A type that does not choose is unchanged | activate `operator` | no `DELIBERATOR_LLM_FALLBACKS`, no anthropic key, no `llm_fallbacks` (`MST-NEV-07`) |
| A19 | 🎯 The brief names a switch | a `DeliberationRun` with two switch lines | `LLM: <first> during the run · <second> during the run` (`DSP-OUT-09`) |
| A20 | Activations first, then switches | a passed-over activation and one switch | `LLM: <activation part> · <switch> during the run`; without the run, the activation part alone (`DSP-OUT-09`) |
| A21 | 🪤 No switch, no line | `llm_switches` empty list, empty tuple, `None`, a string; no run | `None` each time (`DSP-OUT-09`) |
| A22 | A real fire carries the switch | the brief fixture pair, its `DeliberationRun`s given one switch | the sent brief's second-to-last line is `LLM: <switch> during the run` (`DSP-OUT-09`) |
| A23 | The step sets every role's vocabulary before the packs | the deploy script's text | inside `Enable-LlmCandidates`: `Set-AppVocabulary "master"`, then a loop over `(Load-LlmPack).roles` that sets, checks and folds each role's result into `$vocabOk`, then `if ($vocabOk) {` (`MST-OUT-05`) |
| A24 | The vocabulary declares what the images write | `trading_graph_vocabulary.json`, `trading_llm.json` | the three properties present, each list still sorted; the pack's roles are the three deliberators (`MST-OBS-04`, `DLIB-OUT-02`, `DLIB-FAIL-05`) |

---

## Success factors

- [ ] **F0 (planner, done before handover):** the prototype passes `make ci` (`make ci` exit 0, sixteen steps: 5,075 passed, 9 skipped, 100.00 %; the dependency audit clean) and its
      27 planted breaks each turn the planner's tests red (`s277_breaks_proto.txt`).
- [x] The Appendix applied exactly: the 19 production files equal the prototype's blobs
      (`prototype_blobs.txt`), the three `laws.md` equal § 6.
- [x] A1–A24 pass; each docstring cites its clause.
- [x] Every break under *Traps* planted one at a time turns one of your tests red, then restored.
- [x] No decision-path file changed (`DECISION_PATHS` against `git diff origin/main` prints none).
- [x] Law cycle: three books, three test plans, both roll-ups at the derived counts.
- [x] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage, redirected to a file.
- [ ] **F1a (planner, after merge, no cost):** `s277_switch_measure.py` on merged `main` prints what
      it printed on the prototype (the real SDKs' refusals with made-up keys, the switch, the stay,
      the DSPy turn); the deploy script's `llm-candidates` step on a stand-in `az` sets the
      vocabulary on the master and the three roles before the packs, and a failed role vocabulary
      sends no pack.
- [ ] **F2 (after the deploy, at the first weekday fire):** the three deliberators' `AgentInstance`
      rows hold `llm_candidate` `openai/gpt-5.5/high` and `llm_fallbacks`
      `["anthropic/claude-opus-5/max"]`; the fleet checks pass with `llm_passed_over` empty; the
      night's `DeliberationRun` (if a buy is debated) has `llm_switches` empty and names `gpt-5.5`
      for all three roles; no `LLM:` line in the brief; no `VocabularyError` fault.
- [ ] **Not claimed, named:** a real switch on the fleet. It needs a vendor to refuse during a
      debate; the first night one does, its rows, its run and its brief are the proof.

---

## Traps

🪤 **The in-memory graph returns a list property as a tuple.** `llm_switches` reads
`llm_passed_over` as a list or a tuple; compare graph props with `list(...)` in your asserts.
🪤 **The graph is append-only**: a test that writes a property twice under one key raises
`cannot be overwritten`; use a fresh key per case.
🪤 **`agents/**/llm_*.py` is reserved for vendor adapters** (`tests/test_llm_adapter_ownership.py`).
The new modules are `model_chain.py` and `turn_ledger.py`; do not rename them.
🪤 **The anthropic SDK is not installed in the CI environment**: an `AnthropicLLMClient` cannot be
built there. A12's fallback is an OpenAI candidate for that reason; inject a builder (A7) for an
anthropic fallback.
🪤 **A refusal that never raised still has a row.** The refused attempt's row (empty response, stop
reason `unknown`) is what `kernel/llm_outage.py` counts as silent; do not give it a stop reason.
🪤 **`ModelChain.after` is called with the candidate that refused, not with the index.** A thread
whose request was in flight when another thread moved must land on the one in use (A4, A5).
🪤 **`DeliberationRun.llm_switches` is written even when empty**, and must be: the brief and F2 read
the empty list. `LLMCall.llm_passed_over` is the opposite: written only when not empty, so every
other agent's rows are unchanged.
🪤 **The deploy script is a raw file.** Edit it byte for byte (a `\t` in a Python string becomes a
tab).
🪤 **`ruff format` grows test files, and tests are under the 200-line block too**; measure sizes
after formatting. The planner's own deliberator tests needed three files.
🪤 **Do not touch `trading_tunables.json` or `contracts/`**: both are decision paths.

**The breaks — plant one at a time; each must turn one of your tests red; restore each:**

| # | File | Break |
| --- | --- | --- |
| B1 | `agents/master/model_choice.py` | stop probing at the first candidate that passes (S276's `if outcomes.proven: break`) |
| B2 | same | a fallback is any later candidate not refused (an unanswered one handed over) |
| B3 | same | the kept vendors are the chosen one's alone (the fallback's key withheld) |
| B4 | same | the `fallbacks` key never set |
| B5 | same | fallbacks listed among the passed over |
| B6 | `credential_report.py` | `llm_fallbacks` not written |
| B7 | `model_candidates.py` | a role's missing `fallbacks` read as empty |
| B8 | `agents/deliberator/model_chain.py` | `refusal` answers a reason for an exception with no integer status |
| B9 | same | the error statuses are 400 to 499 |
| B10 | same | `after` moves to the refused candidate's next even when the process is already past it |
| B11 | same | `after` returns the next candidate without moving the process |
| B12 | `turn_ledger.py` | the refusal not added to `passed_over` |
| B13 | same | the row's model not the candidate's |
| B14 | same | every exception re-raised (no move) |
| B15 | `kernel/llm_ledger.py` | `llm_passed_over` written on every row |
| B16 | `review_record.py` | `llm_switches` reads a list only (a tuple ignored) |
| B17 | `store.py` | `llm_switches` not written |
| B18 | `poll.py` | `llm_switches` not passed |
| B19 | `orchestration/llm_brief.py` | the switches not added |
| B20 | same | the switches put before the activation parts |
| B21 | `daily_brief_facts.py` | the run's `DeliberationRun` not passed |
| B22 | `trading_graph_vocabulary.json` | `llm_switches` undeclared |
| B23 | `trading_llm.json` | one role's `fallbacks` removed |
| B24 | `infra/deploy-agents.ps1` | a role's vocabulary result not folded into `$vocabOk` |
| B25 | `agents/deliberator/entrypoint.py` | `main` builds the chosen client alone |
| B26 | `model_chain.py` | a fallback label of two parts accepted |
| B27 | same | the handed-over fallbacks never built |

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Sizes on the prototype (main → prototype): `agents/deliberator/poll.py` **188 → 190**,
  `agents/deliberator/settings.py` **169 → 178**, `agents/deliberator/review_record.py`
  **145 → 169**, `agents/deliberator/entrypoint.py` **149 → 160**, `agents/deliberator/agent.py`
  **168 → 106**, `agents/deliberator/store.py` **87 → 93**, `kernel/llm_ledger.py` **154 → 159**,
  `orchestration/daily_brief_facts.py` **170 → 170**, `orchestration/llm_brief.py` **47 → 52**,
  `agents/master/model_choice.py` **75 → 91**, `model_candidates.py` **104 → 111**,
  `credential_test.py` **91 → 98**, `credential_outcomes.py` **107 → 109**, `credential_report.py`
  **96 → 99**; new: `agents/deliberator/model_chain.py` **122**, `turn_ledger.py` **115**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- Faults, not silent failure. A key never reaches a row, a log or a reply (`DLIB-SEC-02`,
  `MST-SEC-04`).
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.**
- Version bump MINOR, `uv.lock` staged with it.
- A worktree has **no `.env`**; nothing here needs one. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. Review: the CodeQL set-diff against the last merged branch
   (`sprint-276-a-debater-runs-on-the-first-llm-that-works`, 133 open, 0 errors); the 19 blobs
   against `prototype_blobs.txt`; the planner's tests on the built code; the breaks against the
   builder's tests alone.
2. **Not before S276's F2 is recorded** (the first weekday fire on `s276`, 22:00 UTC 2026-10-15).
3. `make gate-ran` from the worktree whose `HEAD` is the merged commit; merge; tag; push.
4. F1a at no cost.
5. **Deploy, the operator's call:** `deploy-agents.ps1 -Action llm-candidates`, then the image-only
   retag (deploy skill), rollback `s276`. Then F2 at the first weekday fire; work-queue 123 closes on
   F2.

---

## Handover — paste this to Codex

```text
You are building Sprint 277 in the worktree ../ta-s277, on the branch
sprint-277-a-refused-request-is-answered-by-the-next-llm. Never work on main. The worktree and its
venv are ready; never run a bare `uv sync` (it needs the network and you have none).

Read docs/sprints/sprint-277-a-refused-request-is-answered-by-the-next-llm.md, whole, before
anything else. It is the spec, and its bottom sections are your handback. The Appendix holds the
production code and the law text, which you apply exactly; your work is the tests, the law rows,
the three named test edits, the bump and the evidence.

In order:
1. Read agents/master/laws/laws.md and test-plan.md, agents/deliberator/laws/laws.md and
   test-plan.md, orchestration/laws/dispatcher/laws.md and test-plan.md, docs/laws/conventions.md
   and docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any code.
2. Write the tests of the Test plan (A1 to A24) in new test files (agents/deliberator/tests/,
   agents/master/tests/, orchestration/tests/, tests/), each docstring citing its clause. Run them
   on the unchanged tree and paste the red output into the Closeout.
3. Apply the Appendix sections 1 to 5 exactly: two new modules (agents/deliberator/model_chain.py,
   agents/deliberator/turn_ledger.py) and the diffs to 17 existing files. Change nothing else in
   production code. Do not rename the new modules: agents/**/llm_*.py is reserved.
4. Apply section 6 to the three laws.md files exactly. Then add a test-plan row for DLIB-FAIL-05
   citing your tests, widen the amended clauses' rows (MST-OUT-04, MST-OUT-05, MST-NEV-07,
   MST-FAIL-08, MST-OBS-04, DLIB-FAIL-01, DLIB-OUT-02, DLIB-DEP-05, DSP-OUT-09) with your tests, set
   each test plan's header version, and set the three books' rows in docs/laws/INDEX.md and
   docs/laws/ledger.md to the new version and the count the law gate derives (master 33 / 58,
   deliberator 35 / 66, dispatcher 43 / 47 on the prototype).
5. Apply section 7 to the two existing test files, exactly. Change no other existing test.
6. Plant the breaks B1 to B27 under Traps one at a time; each must turn at least one of your tests
   red; restore each before the next. Record each in the Closeout.
7. Bump the version (MINOR) in pyproject.toml, run uv lock --offline, stage uv.lock. Run make ci
   redirected to a file and read the file. The dependency audit step needs the network: if it is the
   only step that fails, say so; the planner runs it.
8. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: run infra/deploy-agents.ps1, pwsh or any az command; reach the network or any LLM vendor;
change contracts/, orchestration/packs/trading_tunables.json or any other decision-path file; add
or reword a law clause beyond section 6; change any existing test but the two section 7 names;
reorder the vocabulary's lists; use noqa; let any module, test files included, reach 200 lines;
measure make ci through a pipe.

Traps (the spec's Traps section has them all): the in-memory graph returns lists as tuples, so
compare with list(...); the graph is append-only, so one key per written case; agents/**/llm_*.py
is reserved for vendor adapters; the anthropic SDK is not installed here, so build an anthropic
fallback through an injected builder; the refused attempt's own row stays silent (no stop reason);
ModelChain.after takes the refused candidate, and a refusal in flight lands on the one in use;
DeliberationRun.llm_switches is written even when empty, LLMCall.llm_passed_over only when not; the
deploy script is edited byte for byte; ruff format grows test files, so measure sizes after
formatting.

Two tiers when something does not fit. A wrong command, count, path or line number whose intent is
plain: correct it, record it in Return notes, and carry on. A law that contradicts the spec, an
existing test other than the section 7 ones failing, or a measurement in the spec that does not
reproduce: STOP and report. State anything not done as "not done" or "verified failing". Never
write a Result for work you have not done.
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
| Master choice, probes, report, pack and deploy | `agents/master/laws/laws.md` v1.11 and `test-plan.md`, whole | MST-OUT-04/05, MST-NEV-06/07/08, MST-FAIL-04/08, MST-OBS-04, MST-SEC-02/04, MST-DEP-05 | Yes: only proven later candidates and their keys may be handed over; unanswered fallbacks stay out. MST-SEC-02 remains gray; this sprint proves only the named candidate-key boundary. |
| Deliberator chain, ledger, startup, run records | `agents/deliberator/laws/laws.md` v1.17 and `test-plan.md`, whole | DLIB-FAIL-01/04 (new FAIL-05 supplied by §6), DLIB-OUT-02/03/05, DLIB-STA-03, DLIB-OBS-05/07/08, DLIB-DEP-05, DLIB-NEV-10/11, DLIB-SEC-02, PARAM | Yes: one row per attempt; no new peer-owned node; refusal rows retain unknown stop reason. STA-03 and DEP-03 remain gray; no claim to prove their whole envelopes. |
| Shared kernel ledger and unchanged operator callers | `agents/operator/laws/laws.md` v1.10 and `test-plan.md`, whole; deliberator book above | OPR-STA-03, OPR-IDM-02, OPR-DEP-01; DLIB-OUT-03, DLIB-OBS-08 | Yes: optional metadata is absent on ordinary rows; operator remains on its one selected vendor. |
| Dispatcher brief | `orchestration/laws/dispatcher/laws.md` v1.4 and `test-plan.md`, whole | DSP-OUT-06/08/09, DSP-DEP-01 | Yes: activation parts precede run switches; no qualifying fact means no line. DEP-01 remains gray beyond the bounded graph-read proof. |
| Law cycle and substrate/pack boundary | `docs/laws/conventions.md` and `drift-register.md`, whole; `docs/decisions/0012-platform-domain-separation.md`; S276 `llm-candidates` step | conventions §2/3/4/7/7a/9/10; ADR-0012 | Yes: use §6 verbatim, faithful amended summaries, functional citations and gate-derived rollups; pack policy stays injected data. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No contract change; yes, the declared-role fallback handover, refusal switch and recorded switch guarantees change. Apply exactly §6: master v1.12, deliberator v1.18, dispatcher v1.5, with the test-plan/rollup cycle in this unit.

**Contradictions found between a law and this spec:** None beyond the deliberate amendments expressly supplied by §6.

**Laws found silent where a decision was needed:** The new refusal-switch guarantee is not in v1.17 and is supplied by DLIB-FAIL-05 in §6; no further undecided silence found. No extra clause or decision is introduced.

**Clauses that were ⬜ and are now proven:** New DLIB-FAIL-05 is proven; no previously declared gray envelope is promoted. Existing gray envelopes named above remain gray. The amended green clauses are re-proven by the new tests; the gate derives master 33 / 58, deliberator 35 / 66, dispatcher 43 / 47.

Reading recorded before any code change, 2026-10-15, in `C:\Users\yury_\Downloads\project\ta-s277`, clean branch `sprint-277-a-refused-request-is-answered-by-the-next-llm`, HEAD and `origin/main` `53fcfcc2c21ae8394c6a7eecb62958c65b1b2fb0`. No `.env`; ready `.venv`. Scope is the Appendix, new tests, named existing-test edits, law rows, version and handback only; no tracker, decision-path, network, vendor or deploy action.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_refusal_moves_request_and_process` | `agents/deliberator/tests/test_refusal_attempts.py` | PASS | DLIB-FAIL-05, DLIB-OBS-08 |
| A2 | `test_a2_without_error_status_nothing_moves` | `agents/deliberator/tests/test_refusal_attempts.py` | PASS | DLIB-FAIL-05 |
| A3 | `test_a3_last_refusal_is_raised_and_stays_on_last` | `agents/deliberator/tests/test_refusal_attempts.py` | PASS | DLIB-FAIL-05, DLIB-FAIL-01 |
| A4 | `test_a4_already_left_candidate_lands_on_current` | `agents/deliberator/tests/test_refusal_concurrency.py` | PASS | DLIB-FAIL-05 |
| A5 | `test_a5_concurrent_refusals_skip_no_candidate` | `agents/deliberator/tests/test_refusal_concurrency.py` | PASS | DLIB-FAIL-05 |
| A6 | `test_a6_reason_is_only_integer_status` | `agents/deliberator/tests/test_refusal_attempts.py` | PASS | DLIB-FAIL-05 |
| A7 | `test_a7_handed_candidates_build_with_their_own_vendor_key` | `agents/deliberator/tests/test_handed_fallbacks.py` | PASS | DLIB-DEP-05 |
| A8 | `test_a8_unreadable_fallback_stops_before_build` | `agents/deliberator/tests/test_handed_fallbacks.py` | PASS | DLIB-DEP-05 |
| A9 | `test_a9_kernel_refuses_unrunnable_fallback`; `test_a9_empty_chain_is_refused` | `agents/deliberator/tests/test_handed_fallbacks.py` | PASS | DLIB-NEV-11, DLIB-DEP-05; DLIB-DEP-05 |
| A10 | `test_a10_real_review_records_answered_model_and_switch` | `agents/deliberator/tests/test_refusal_run.py` | PASS | DLIB-OUT-02, DLIB-FAIL-05 |
| A11 | `test_a11_run_always_writes_empty_switches`; `test_a11_switch_reader_skips_bad_rows_and_deduplicates_in_row_order` | `agents/deliberator/tests/test_refusal_run.py` | PASS | DLIB-OUT-02 |
| A12 | `test_a12_entrypoint_builds_and_uses_role_chain` | `agents/deliberator/tests/test_handed_fallbacks.py` | PASS | DLIB-DEP-05 |
| A13 | `test_a13_refused_fallback_is_recorded_and_key_withheld` | `agents/master/tests/test_fallback_handover.py` | PASS | MST-OUT-05, MST-FAIL-08, MST-NEV-07, MST-OBS-04 |
| A14 | `test_a14_unanswered_fallback_is_never_handed_over` | `agents/master/tests/test_fallback_handover.py` | PASS | MST-FAIL-08, MST-NEV-06 |
| A15 | `test_a15_refused_fallback_fails_no_fleet_check` | `agents/master/tests/test_fallback_handover.py` | PASS | MST-OUT-04, MST-FAIL-08 |
| A16 | `test_a16_no_fallback_after_last_or_unproven_choice` | `agents/master/tests/test_fallback_handover.py` | PASS | MST-OUT-05, MST-FAIL-08 |
| A17 | `test_a17_every_role_names_its_fallbacks_key`; `test_a17_missing_fallback_key_refuses_pack` | `agents/master/tests/test_fallback_declaration.py` | PASS | MST-OUT-05, MST-NEV-08; MST-NEV-08 |
| A18 | `test_a18_nonchoosing_type_keeps_its_one_vendor` | `agents/master/tests/test_fallback_handover.py` | PASS | MST-NEV-07 |
| A19 | `test_a19_brief_names_each_switch_in_run_order` | `orchestration/tests/test_llm_brief_switches.py` | PASS | DSP-OUT-09 |
| A20 | `test_a20_activation_parts_precede_run_switches` | `orchestration/tests/test_llm_brief_switches.py` | PASS | DSP-OUT-09 |
| A21 | `test_a21_no_switch_means_no_line` | `orchestration/tests/test_llm_brief_switches.py` | PASS | DSP-OUT-09 |
| A22 | `test_a22_real_fire_carries_the_runs_switch` | `orchestration/tests/test_llm_brief_switches.py` | PASS | DSP-OUT-09 |
| A23 | `test_a23_role_vocabulary_success_gates_pack_delivery` | `tests/test_fallback_delivery.py` | PASS | MST-OUT-05 |
| A24 | `test_a24_vocabulary_declares_every_fallback_property_in_sorted_lists` | `tests/test_fallback_delivery.py` | PASS | MST-OBS-04, DLIB-OUT-02, DLIB-FAIL-05 |

**Tests added beyond the plan:** `agents/master/tests/test_fallback_handover.py::test_proven_fallback_keeps_its_key_and_record` (MST-OUT-05, MST-NEV-07, MST-OBS-04). The plan produces 55 cases and this passing-fallback control adds one: 56 cases total. A9, A11 and A17 each use more than one test function.

---

## Closeout — evidence

**Status:** MERGED 2026-10-15 — `0.128.00`, fast-forwarded with S278 to `9781b4e1` (S277's own commit `6a5742c8`, tag `v0.128.00`), GATE PROVEN `6a5742c8` (CI, CodeQL, Security Findings); merged before S276's F2 on the operator's word (*"can we do it now?"*), so `main` runs ahead of the fleet (`s276`); F1a passed at no cost; not deployed (the `llm-candidates` step, then the retag, is the operator's call). The builder's handback read: BUILT — local tests and guards proven; overall CI verified failing at the offline dependency audit; remote gate and live checks owed.

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s277`, branch `sprint-277-a-refused-request-is-answered-by-the-next-llm`; `.env` absent. Ready worktree `.venv`; no sync or vendor call. Proof artifacts are in `C:\Users\yury_\AppData\Local\Temp\s277-evidence`.

**Result:** Appendix applied exactly: all 24 supplied raw blob hashes match (19 production, 3 law books, 2 existing test files). All A1–A24 cases and the extra passing-fallback control pass (56 new cases); B1–B27 each turn a new test red and restore exact bytes. Full pytest: 5088 passed, 9 skipped, 2470 warnings in 443.47s (0:07:23), 100.00 % coverage. The dependency audit is verified failing offline; a fresh advisory check is not done. No decision path changed; no remote, merge, deploy or live proof claimed.

**Files changed:** 42, exactly the scoped production/law/test/version/handback surfaces:

```text
agents/deliberator/agent.py
agents/deliberator/entrypoint.py
agents/deliberator/laws/laws.md
agents/deliberator/laws/test-plan.md
agents/deliberator/model_chain.py
agents/deliberator/poll.py
agents/deliberator/review_record.py
agents/deliberator/settings.py
agents/deliberator/store.py
agents/deliberator/tests/refusal_testkit.py
agents/deliberator/tests/test_handed_fallbacks.py
agents/deliberator/tests/test_ledger_usage_forwarding.py
agents/deliberator/tests/test_refusal_attempts.py
agents/deliberator/tests/test_refusal_concurrency.py
agents/deliberator/tests/test_refusal_run.py
agents/deliberator/turn_ledger.py
agents/master/credential_outcomes.py
agents/master/credential_report.py
agents/master/credential_test.py
agents/master/laws/laws.md
agents/master/laws/test-plan.md
agents/master/model_candidates.py
agents/master/model_choice.py
agents/master/tests/test_candidate_activation.py
agents/master/tests/test_fallback_declaration.py
agents/master/tests/test_fallback_handover.py
docs/laws/INDEX.md
docs/laws/ledger.md
docs/sprints/README.md
docs/sprints/sprint-277-a-refused-request-is-answered-by-the-next-llm.md
infra/deploy-agents.ps1
kernel/llm_ledger.py
orchestration/daily_brief_facts.py
orchestration/laws/dispatcher/laws.md
orchestration/laws/dispatcher/test-plan.md
orchestration/llm_brief.py
orchestration/packs/trading_graph_vocabulary.json
orchestration/packs/trading_llm.json
orchestration/tests/test_llm_brief_switches.py
pyproject.toml
tests/test_fallback_delivery.py
uv.lock
```

**Design decisions:** DL-289 amendment 4 (the planner's, on `main`); no new DL.

**Proof — the red run first:**

```text
Unchanged production tree; .venv/Scripts/python.exe -m pytest <eight new test files>
--no-cov -q --tb=short --continue-on-collection-errors
RED_EXIT=1
FFFFF.FFFFFFFFFFFFFF                                                     [100%]
=================================== ERRORS ====================================
_____ ERROR collecting agents/deliberator/tests/test_refusal_attempts.py ______
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s277\agents\deliberator\tests\test_refusal_attempts.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\deliberator\tests\test_refusal_attempts.py:10: in <module>
    from agents.deliberator.model_chain import refusal
E   ModuleNotFoundError: No module named 'agents.deliberator.model_chain'
____ ERROR collecting agents/deliberator/tests/test_refusal_concurrency.py ____
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s277\agents\deliberator\tests\test_refusal_concurrency.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\deliberator\tests\test_refusal_concurrency.py:11: in <module>
    from agents.deliberator.tests.refusal_testkit import (
agents\deliberator\tests\refusal_testkit.py:12: in <module>
    from agents.deliberator.model_chain import ModelChain, RoleCandidate
E   ModuleNotFoundError: No module named 'agents.deliberator.model_chain'
_____ ERROR collecting agents/deliberator/tests/test_handed_fallbacks.py ______
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s277\agents\deliberator\tests\test_handed_fallbacks.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\deliberator\tests\test_handed_fallbacks.py:12: in <module>
    from agents.deliberator.entrypoint import build_role_models, main
E   ImportError: cannot import name 'build_role_models' from 'agents.deliberator.entrypoint' (C:\Users\yury_\Downloads\project\ta-s277\agents\deliberator\entrypoint.py)
________ ERROR collecting agents/deliberator/tests/test_refusal_run.py ________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s277\agents\deliberator\tests\test_refusal_run.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\deliberator\tests\test_refusal_run.py:11: in <module>
    from agents.deliberator.review_record import llm_switches
E   ImportError: cannot import name 'llm_switches' from 'agents.deliberator.review_record' (C:\Users\yury_\Downloads\project\ta-s277\agents\deliberator\review_record.py)
================================== FAILURES ===================================
___________ test_a13_refused_fallback_is_recorded_and_key_withheld ____________
agents\master\tests\test_fallback_handover.py:17: in test_a13_refused_fallback_is_recorded_and_key_withheld
    assert fixture.labels() == [FIRST, SECOND]
E   AssertionError: assert ['openai/gpt-5.5/high'] == ['openai/gpt-...e-opus-5/max']
E
E     Right contains one more item: 'anthropic/claude-opus-5/max'
E     Use -v to get more diff
______________ test_a14_unanswered_fallback_is_never_handed_over ______________
agents\master\tests\test_fallback_handover.py:34: in test_a14_unanswered_fallback_is_never_handed_over
    assert fixture.labels() == [FIRST, SECOND]
E   AssertionError: assert ['openai/gpt-5.5/high'] == ['openai/gpt-...e-opus-5/max']
E
E     Right contains one more item: 'anthropic/claude-opus-5/max'
E     Use -v to get more diff
_______________ test_a15_refused_fallback_fails_no_fleet_check ________________
agents\master\tests\test_fallback_handover.py:55: in test_a15_refused_fallback_fails_no_fleet_check
    assert list(check.props["llm_passed_over"]) == [
E   AssertionError: assert [] == ['deliberator...ble:http_429']
E
E     Right contains 3 more items, first extra item: 'deliberator-manager: anthropic/claude-opus-5/max: unrecoverable:http_429'
E     Use -v to get more diff
_________ test_a16_no_fallback_after_last_or_unproven_choice[429-200] _________
agents\master\tests\test_fallback_handover.py:72: in test_a16_no_fallback_after_last_or_unproven_choice
    assert reply.config["DELIBERATOR_LLM_FALLBACKS"] == ""
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   KeyError: 'DELIBERATOR_LLM_FALLBACKS'
_________ test_a16_no_fallback_after_last_or_unproven_choice[401-503] _________
agents\master\tests\test_fallback_handover.py:72: in test_a16_no_fallback_after_last_or_unproven_choice
    assert reply.config["DELIBERATOR_LLM_FALLBACKS"] == ""
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   KeyError: 'DELIBERATOR_LLM_FALLBACKS'
________________ test_proven_fallback_keeps_its_key_and_record ________________
agents\master\tests\test_fallback_handover.py:95: in test_proven_fallback_keeps_its_key_and_record
    assert fixture.labels() == [FIRST, SECOND]
E   AssertionError: assert ['openai/gpt-5.5/high'] == ['openai/gpt-...e-opus-5/max']
E
E     Right contains one more item: 'anthropic/claude-opus-5/max'
E     Use -v to get more diff
_________________ test_a17_every_role_names_its_fallbacks_key _________________
agents\master\tests\test_fallback_declaration.py:21: in test_a17_every_role_names_its_fallbacks_key
    assert role.fallbacks_key == "DELIBERATOR_LLM_FALLBACKS"
           ^^^^^^^^^^^^^^^^^^
E   AttributeError: 'LlmRole' object has no attribute 'fallbacks_key'
_______ test_a17_missing_fallback_key_refuses_pack[deliberator-manager] _______
agents\master\tests\test_fallback_declaration.py:31: in test_a17_missing_fallback_key_refuses_pack
    with pytest.raises(ValueError, match="'fallbacks'.*non-empty string"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
______ test_a17_missing_fallback_key_refuses_pack[deliberator-proponent] ______
agents\master\tests\test_fallback_declaration.py:31: in test_a17_missing_fallback_key_refuses_pack
    with pytest.raises(ValueError, match="'fallbacks'.*non-empty string"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
______ test_a17_missing_fallback_key_refuses_pack[deliberator-opponent] _______
agents\master\tests\test_fallback_declaration.py:31: in test_a17_missing_fallback_key_refuses_pack
    with pytest.raises(ValueError, match="'fallbacks'.*non-empty string"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE ValueError
________________ test_a19_brief_names_each_switch_in_run_order ________________
orchestration\tests\test_llm_brief_switches.py:31: in test_a19_brief_names_each_switch_in_run_order
    assert llm_line(graph, now=NOW, deliberation=run) == (
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: llm_line() got an unexpected keyword argument 'deliberation'
_______________ test_a20_activation_parts_precede_run_switches ________________
orchestration\tests\test_llm_brief_switches.py:52: in test_a20_activation_parts_precede_run_switches
    llm_line(graph, now=NOW, deliberation=run)
E   TypeError: llm_line() got an unexpected keyword argument 'deliberation'
_________________ test_a21_no_switch_means_no_line[switches0] _________________
orchestration\tests\test_llm_brief_switches.py:63: in test_a21_no_switch_means_no_line
    assert llm_line(graph, now=NOW, deliberation=run) is None
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: llm_line() got an unexpected keyword argument 'deliberation'
_________________ test_a21_no_switch_means_no_line[switches1] _________________
orchestration\tests\test_llm_brief_switches.py:63: in test_a21_no_switch_means_no_line
    assert llm_line(graph, now=NOW, deliberation=run) is None
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: llm_line() got an unexpected keyword argument 'deliberation'
___________________ test_a21_no_switch_means_no_line[None] ____________________
orchestration\tests\test_llm_brief_switches.py:63: in test_a21_no_switch_means_no_line
    assert llm_line(graph, now=NOW, deliberation=run) is None
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: llm_line() got an unexpected keyword argument 'deliberation'
________________ test_a21_no_switch_means_no_line[wrong shape] ________________
orchestration\tests\test_llm_brief_switches.py:63: in test_a21_no_switch_means_no_line
    assert llm_line(graph, now=NOW, deliberation=run) is None
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: llm_line() got an unexpected keyword argument 'deliberation'
_________________ test_a22_real_fire_carries_the_runs_switch __________________
orchestration\tests\test_llm_brief_switches.py:75: in test_a22_real_fire_carries_the_runs_switch
    assert telegram.briefs[0].splitlines()[-2] == f"LLM: {SWITCH} during the run"
E   AssertionError: assert 'Filled: none' == 'LLM: deliber...uring the run'
E
E     - LLM: deliberator-opponent switched to claude-opus-5 (passed over openai/gpt-5.5/high: http_429) during the run
E     + Filled: none
____________ test_a23_role_vocabulary_success_gates_pack_delivery _____________
tests\test_fallback_delivery.py:23: in test_a23_role_vocabulary_success_gates_pack_delivery
    assert loop in body
E   assert 'foreach ($role in @((Load-LlmPack).roles.PSObject.Properties.Name)) {' in '\n  # DL-289: run BEFORE the retag that brings the master\'s S276 image. That image writes\n  # llm_passed_over on ev...master") -eq "Succeeded")\n  Check $packOk "credential and LLM packs on master"\n  Bot\n  return $vocabOk -and $packOk'
____ test_a24_vocabulary_declares_every_fallback_property_in_sorted_lists _____
tests\test_fallback_delivery.py:53: in test_a24_vocabulary_declares_every_fallback_property_in_sorted_lists
    assert prop in names
E   AssertionError: assert 'llm_fallbacks' in ['agent_type', 'boot_id', 'credential_tests_cached', 'credential_tests_declared', 'credential_tests_failed_optional', 'credential_tests_passed', ...]
=========================== short test summary info ===========================
ERROR agents/deliberator/tests/test_refusal_attempts.py
ERROR agents/deliberator/tests/test_refusal_concurrency.py
ERROR agents/deliberator/tests/test_handed_fallbacks.py
ERROR agents/deliberator/tests/test_refusal_run.py
FAILED agents/master/tests/test_fallback_handover.py::test_a13_refused_fallback_is_recorded_and_key_withheld
FAILED agents/master/tests/test_fallback_handover.py::test_a14_unanswered_fallback_is_never_handed_over
FAILED agents/master/tests/test_fallback_handover.py::test_a15_refused_fallback_fails_no_fleet_check
FAILED agents/master/tests/test_fallback_handover.py::test_a16_no_fallback_after_last_or_unproven_choice[429-200]
FAILED agents/master/tests/test_fallback_handover.py::test_a16_no_fallback_after_last_or_unproven_choice[401-503]
FAILED agents/master/tests/test_fallback_handover.py::test_proven_fallback_keeps_its_key_and_record
FAILED agents/master/tests/test_fallback_declaration.py::test_a17_every_role_names_its_fallbacks_key
FAILED agents/master/tests/test_fallback_declaration.py::test_a17_missing_fallback_key_refuses_pack[deliberator-manager]
FAILED agents/master/tests/test_fallback_declaration.py::test_a17_missing_fallback_key_refuses_pack[deliberator-proponent]
FAILED agents/master/tests/test_fallback_declaration.py::test_a17_missing_fallback_key_refuses_pack[deliberator-opponent]
FAILED orchestration/tests/test_llm_brief_switches.py::test_a19_brief_names_each_switch_in_run_order
FAILED orchestration/tests/test_llm_brief_switches.py::test_a20_activation_parts_precede_run_switches
FAILED orchestration/tests/test_llm_brief_switches.py::test_a21_no_switch_means_no_line[switches0]
FAILED orchestration/tests/test_llm_brief_switches.py::test_a21_no_switch_means_no_line[switches1]
FAILED orchestration/tests/test_llm_brief_switches.py::test_a21_no_switch_means_no_line[None]
FAILED orchestration/tests/test_llm_brief_switches.py::test_a21_no_switch_means_no_line[wrong shape]
FAILED orchestration/tests/test_llm_brief_switches.py::test_a22_real_fire_carries_the_runs_switch
FAILED tests/test_fallback_delivery.py::test_a23_role_vocabulary_success_gates_pack_delivery
FAILED tests/test_fallback_delivery.py::test_a24_vocabulary_declares_every_fallback_property_in_sorted_lists
19 failed, 1 passed, 4 errors in 12.24s
```

**Proof — the green run:**

```text
........................................................                 [100%]
56 passed in 5.70s
GREEN_EXIT=0

Final full CI pytest:
5088 passed, 9 skipped, 2470 warnings in 443.47s (0:07:23)
TOTAL                                                           21336      0   4562      0  100.00%
```

**Guards planted:** each mutation was applied to one production file, tested only against a new builder test, then restored before the next. Raw bytes rechecked after every restore.

```text
B1: exit=1; RED=agents/master/tests/test_fallback_handover.py::test_proven_fallback_keeps_its_key_and_record; RESTORED=True
B2: exit=1; RED=agents/master/tests/test_fallback_handover.py::test_a14_unanswered_fallback_is_never_handed_over; RESTORED=True
B3: exit=1; RED=agents/master/tests/test_fallback_handover.py::test_proven_fallback_keeps_its_key_and_record; RESTORED=True
B4: exit=1; RED=agents/master/tests/test_fallback_handover.py::test_proven_fallback_keeps_its_key_and_record; RESTORED=True
B5: exit=1; RED=agents/master/tests/test_fallback_handover.py::test_proven_fallback_keeps_its_key_and_record; RESTORED=True
B6: exit=1; RED=agents/master/tests/test_fallback_handover.py::test_proven_fallback_keeps_its_key_and_record; RESTORED=True
B7: exit=1; RED=agents/master/tests/test_fallback_declaration.py::test_a17_missing_fallback_key_refuses_pack[deliberator-manager]; RESTORED=True
B8: exit=1; RED=agents/deliberator/tests/test_refusal_attempts.py::test_a2_without_error_status_nothing_moves[error0]; RESTORED=True
B9: exit=1; RED=agents/deliberator/tests/test_refusal_attempts.py::test_a1_refusal_moves_request_and_process[500]; RESTORED=True
B10: exit=1; RED=agents/deliberator/tests/test_refusal_concurrency.py::test_a4_already_left_candidate_lands_on_current; RESTORED=True
B11: exit=1; RED=agents/deliberator/tests/test_refusal_attempts.py::test_a1_refusal_moves_request_and_process[400]; RESTORED=True
B12: exit=1; RED=agents/deliberator/tests/test_refusal_attempts.py::test_a1_refusal_moves_request_and_process[400]; RESTORED=True
B13: exit=1; RED=agents/deliberator/tests/test_refusal_attempts.py::test_a1_refusal_moves_request_and_process[400]; RESTORED=True
B14: exit=1; RED=agents/deliberator/tests/test_refusal_attempts.py::test_a1_refusal_moves_request_and_process[400]; RESTORED=True
B15: exit=1; RED=agents/deliberator/tests/test_refusal_attempts.py::test_a1_refusal_moves_request_and_process[400]; RESTORED=True
B16: exit=1; RED=agents/deliberator/tests/test_refusal_run.py::test_a11_switch_reader_skips_bad_rows_and_deduplicates_in_row_order; RESTORED=True
B17: exit=1; RED=agents/deliberator/tests/test_refusal_run.py::test_a11_run_always_writes_empty_switches; RESTORED=True
B18: exit=1; RED=agents/deliberator/tests/test_refusal_run.py::test_a10_real_review_records_answered_model_and_switch; RESTORED=True
B19: exit=1; RED=orchestration/tests/test_llm_brief_switches.py::test_a19_brief_names_each_switch_in_run_order; RESTORED=True
B20: exit=1; RED=orchestration/tests/test_llm_brief_switches.py::test_a20_activation_parts_precede_run_switches; RESTORED=True
B21: exit=1; RED=orchestration/tests/test_llm_brief_switches.py::test_a22_real_fire_carries_the_runs_switch; RESTORED=True
B22: exit=1; RED=tests/test_fallback_delivery.py::test_a24_vocabulary_declares_every_fallback_property_in_sorted_lists; RESTORED=True
B23: exit=1; RED=agents/master/tests/test_fallback_declaration.py::test_a17_every_role_names_its_fallbacks_key; RESTORED=True
B24: exit=1; RED=tests/test_fallback_delivery.py::test_a23_role_vocabulary_success_gates_pack_delivery; RESTORED=True
B25: exit=1; RED=agents/deliberator/tests/test_handed_fallbacks.py::test_a12_entrypoint_builds_and_uses_role_chain; RESTORED=True
B26: exit=1; RED=agents/deliberator/tests/test_handed_fallbacks.py::test_a8_unreadable_fallback_stops_before_build[anthropic/claude-opus-5]; RESTORED=True
B27: exit=1; RED=agents/deliberator/tests/test_handed_fallbacks.py::test_a7_handed_candidates_build_with_their_own_vendor_key; RESTORED=True
GUARDS_PROVEN=27/27; all Appendix bytes restored
MUTATIONS_EXIT=0
```

Rechecked after the fixture type corrections:

```text
B16 after fixture type correction: red, restored exact bytes
B25 after fixture type correction: red, restored exact bytes
RECHECK_EXIT=0
```

**Module line counts:** after formatting:

```text
agents/deliberator/agent.py: 106
agents/deliberator/entrypoint.py: 160
agents/deliberator/model_chain.py: 122
agents/deliberator/poll.py: 190
agents/deliberator/review_record.py: 169
agents/deliberator/settings.py: 178
agents/deliberator/store.py: 93
agents/deliberator/tests/refusal_testkit.py: 78
agents/deliberator/tests/test_handed_fallbacks.py: 129
agents/deliberator/tests/test_ledger_usage_forwarding.py: 93
agents/deliberator/tests/test_refusal_attempts.py: 112
agents/deliberator/tests/test_refusal_concurrency.py: 49
agents/deliberator/tests/test_refusal_run.py: 133
agents/deliberator/turn_ledger.py: 115
agents/master/credential_outcomes.py: 109
agents/master/credential_report.py: 99
agents/master/credential_test.py: 98
agents/master/model_candidates.py: 111
agents/master/model_choice.py: 91
agents/master/tests/test_candidate_activation.py: 92
agents/master/tests/test_fallback_declaration.py: 32
agents/master/tests/test_fallback_handover.py: 107
kernel/llm_ledger.py: 159
orchestration/daily_brief_facts.py: 170
orchestration/llm_brief.py: 52
orchestration/tests/test_llm_brief_switches.py: 78
tests/test_fallback_delivery.py: 64
ALL_TOUCHED_PYTHON_MODULES_LT_200=True; new test docstrings cite clauses
```

**`make ci`:** redirected directly to `C:\Users\yury_\AppData\Local\Temp\s277-evidence\make-ci.txt`, exit 2. Steps 1–13 pass; step 14 fails because fresh dependency-advisory evidence requires the network. Steps 15 and 16 pass when run separately after make stops. Overall CI is **verified failing**, not green. The launcher sets `UV_OFFLINE=1`, `UV_NO_SYNC=1`, disables Python downloads and pip indexes, restricts Git transport to local files, and loads an external process-local guard rejecting nonlocal DNS/connects. No production file is modified for this boundary.

```text
uv run ruff check . --output-format=github
uv run ruff format --check .
uv run mypy kernel contracts agents orchestration surfaces
Success: no issues found in 1254 source files
uv run lint-imports
Contracts: 5 kept, 0 broken.
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
5088 passed, 9 skipped, 2470 warnings in 443.47s (0:07:23)
TOTAL                                                           21336      0   4562      0  100.00%
MAKE_CI_EXIT=2
dependency audit failed: WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\urllib3\connection.py", line 239, in _new_conn
    sock = connection.create_connection(
        (self._dns_host, self.port),
    ...<2 lines>...
        socket_options=self.socket_options,
    )
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\urllib3\util\connection.py", line 60, in create_connection
    for res in socket.getaddrinfo(host, port, family, socket.SOCK_STREAM):
               ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\AppData\Local\Temp\s277-evidence\offline\sitecustomize.py", line 13, in _offline_getaddrinfo
    raise socket.gaierror('Sprint 277 offline: external DNS disabled')
socket.gaierror: Sprint 277 offline: external DNS disabled

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\urllib3\connectionpool.py", line 793, in urlopen
    response = self._make_request(
        conn,
    ...<10 lines>...
        **response_kw,
    )
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\urllib3\connectionpool.py", line 494, in _make_request
    raise new_e
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\urllib3\connectionpool.py", line 470, in _make_request
    self._validate_conn(conn)
    ~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\urllib3\connectionpool.py", line 1125, in _validate_conn
    conn.connect()
    ~~~~~~~~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\urllib3\connection.py", line 827, in connect
    self.sock = sock = self._new_conn()
                       ~~~~~~~~~~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\urllib3\connection.py", line 246, in _new_conn
    raise NameResolutionError(self.host, self, e) from e
urllib3.exceptions.NameResolutionError: HTTPSConnection(host='pypi.org', port=443): Failed to resolve 'pypi.org' (Sprint 277 offline: external DNS disabled)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\requests\adapters.py", line 696, in send
    resp = conn.urlopen(
        method=request.method,
    ...<9 lines>...
        chunked=chunked,
    )
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\urllib3\connectionpool.py", line 847, in urlopen
    retries = retries.increment(
        method, url, error=new_e, _pool=self, _stacktrace=sys.exc_info()[2]
    )
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\urllib3\util\retry.py", line 555, in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by NameResolutionError("HTTPSConnection(host='pypi.org', port=443): Failed to resolve 'pypi.org' (Sprint 277 offline: external DNS disabled)"))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Scripts\pip-audit.exe\__main__.py", line 10, in <module>
    sys.exit(audit())
             ~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\pip_audit\_cli.py", line 554, in audit
    for spec, vulns in auditor.audit(source):
                       ~~~~~~~~~~~~~^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\pip_audit\_audit.py", line 68, in audit
    for dep, vulns in self._service.query_all(specs):
                      ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\pip_audit\_service\interface.py", line 180, in query_all
    yield self.query(spec)
          ~~~~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\pip_audit\_service\pypi.py", line 64, in query
    response: requests.Response = self.session.get(url=url, timeout=self.timeout)
                                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\requests\sessions.py", line 671, in get
    return self.request("GET", url, params=params, **kwargs)
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\requests\sessions.py", line 651, in request
    resp = self.send(prep, **send_kwargs)
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\requests\sessions.py", line 784, in send
    r = adapter.send(request, **kwargs)
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\cachecontrol\adapter.py", line 76, in send
    resp = super().send(request, stream, timeout, verify, cert, proxies)
  File "C:\Users\yury_\Downloads\project\ta-s277\.venv\Lib\site-packages\requests\adapters.py", line 729, in send
    raise ConnectionError(e, request=request)
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by NameResolutionError("HTTPSConnection(host='pypi.org', port=443): Failed to resolve 'pypi.org' (Sprint 277 offline: external DNS disabled)"))
make: *** [Makefile:60: ci] Error 1

Detect secrets...........................................................Passed
TRACKED_SECRETS_EXIT=0
Detect secrets...........................................................Passed
detect-secrets (untracked): scanning 11 new file(s)
UNTRACKED_SECRETS_EXIT=0
```

**`make gate-ran`:** (planner) from `../ta-s277`: `GATE PROVEN for 6a5742c8` (CI, including the dependency audit the sandbox could not reach, CodeQL, Security Findings), SHA checked against `git rev-parse HEAD`. **Planner review:** 24 of 24 production, law and existing-test blobs equal the prototype's; the planner's tests beside the builder's on the built tree, 110 passed; 27 of 27 breaks red against the builder's tests alone; CodeQL set-diff against the S276 branch, nothing new, 0 errors. **F1a (merged `main` `9781b4e1`, no cost):** `s277_switch_measure.py` printed what it printed on the prototype, line for line (the real SDKs' refusals with made-up keys, HTTP 401 on both; the time-out with no status; the switch, the stay, both refused, the DSPy turn and the run's `llm_switches`); the deploy script's own `llm-candidates` step on a stand-in `az` set the vocabulary on the master and the three roles before one pack update carrying both packs, each decoding to its file byte for byte, and a failed vocabulary on the master or on `deliberator-opponent` sent no pack (OneDrive `trading-agents-data/wq123p3-2026-10-15/`, `s277_f1a_main_9781b4e1.txt`, `s277_f1a_standin_main_9781b4e1.txt`).

**Not met / verified failing:** dependency audit verified failing; fresh advisory lookups **not done** offline. `make gate-ran`, push, merge, F1a, deploy, F2 and a real fleet refusal switch **not done**; these remain the planner/operator sequence. F0 is the planner-provided prototype evidence, not a builder rerun. All executed existing tests pass; the nine skips and their reasons are in the full CI log. No excluded existing test was edited.

---

## Return notes

- The untracked secret scan initially flagged the literal stand-in in A7. The fixture now supplies the same dummy through a local value; the scan passes with no baseline change or allowlist. The final 56-case run above includes that correction.
- Only the Appendix changes production; the 19 production, 3 laws and 2 existing-test raw blobs equal the supplied OneDrive `prototype_blobs.txt`. Deploy bytes, including backslashes and LF endings, are exact.
- The Appendix extraction command needed no blank separator between diff blocks: `git apply --recount` treats a separator as additional context. The failed `--check` wrote nothing; the corrected application passed all target hash checks. No spec intent changed.
- New fixture construction was corrected to supply the stopped-error constructor's keyword-only provider and stop reason. The first CI attempt then found two new-test type errors; explicit OpenAI client narrowing and a distinct switch-props variable fixed them. The final redirected run above supersedes that attempt; production blobs stayed exact.
- The version is 0.128.00. `uv lock --offline` exited 0, resolved 180 packages and changed only the project version in `uv.lock`; the lock was staged. No bare `uv sync` ran.
- Law rows retain their broader gray envelopes. DLIB-FAIL-05 is the only new green clause; the derived rollups are 33 / 58, 35 / 66 and 43 / 47. The supplied production module measurements reproduce; every touched Python file is below 200 lines after formatting.
- Builder tests use eight new test files and one helper, so the final changed-file count is 42. The new suite has 56 cases; the prototype's 43 additional cases are its own test count.
- No network, vendor, infrastructure or deploy action was used. The dependency audit is left to the planner. The planner also owes the exact-HEAD remote gate and the stated post-merge/live checks; the real fleet switch remains unclaimed.
- `docs/STATE.md`, `docs/design-log.md`, `docs/work-queue.md`, contracts, tunables and every other decision path are unchanged. No new design-log number, drift row, law wording or existing-test edit beyond the authorized Appendix is introduced.

---

## Appendix — the change, measured on the planner's prototype

The prototype is `../ta-s277-proto` at `9b69ce26` (local only). Each section is the diff from
`origin/main` `e38a99ef`, applied with `git apply` or by hand; the result must equal the prototype's
blob ids in `prototype_blobs.txt` (OneDrive `trading-agents-data/wq123p3-2026-10-15/`).

### 1. The master hands over fallbacks

`model_choice.py` probes every candidate and hands over each later pass; the role gains a fourth key; the report and the `AgentInstance` carry `llm_fallbacks`; each role in the pack names `fallbacks`.

`agents/master/model_candidates.py`:

```diff
diff --git a/agents/master/model_candidates.py b/agents/master/model_candidates.py
index 1d17e33e..6036e41f 100644
--- a/agents/master/model_candidates.py
+++ b/agents/master/model_candidates.py
@@ -34,11 +34,17 @@ class LlmCandidate:

 @dataclass(frozen=True)
 class LlmRole:
-    """The configuration keys an agent type reads its chosen candidate from."""
+    """The configuration keys an agent type reads its candidates from.
+
+    The chosen candidate's vendor, model and effort, and the later candidates that
+    also passed, in order, as ``vendor/model/effort`` labels joined by commas
+    (DL-289 P3).
+    """

     vendor_key: str
     model_key: str
     effort_key: str
+    fallbacks_key: str


 @dataclass(frozen=True)
@@ -94,7 +100,8 @@ def _candidate(entry: object) -> LlmCandidate:
 def _role(name: object, keys: object) -> LlmRole:
     if not isinstance(keys, dict):
         raise ValueError(f"LLM role {name!r} must be an object")
-    return LlmRole(*(_text(keys, key) for key in ("vendor", "model", "effort")))
+    fields = ("vendor", "model", "effort", "fallbacks")
+    return LlmRole(*(_text(keys, key) for key in fields))


 def _text(entry: dict[str, object], key: str) -> str:
```

`agents/master/model_choice.py`:

```diff
diff --git a/agents/master/model_choice.py b/agents/master/model_choice.py
index 65a16acc..9f8ccbe4 100644
--- a/agents/master/model_choice.py
+++ b/agents/master/model_choice.py
@@ -1,14 +1,18 @@
-"""Choose the first declared LLM candidate whose probes pass (DL-289 P2).
+"""Choose the first declared LLM candidate whose probes pass (DL-289 P2, P3).

 Agent: master
-Role: try an agent type's candidates in order, hand over the first that works.
+Role: probe an agent type's candidates in order, hand over the first that works and
+      each later one that also works, as its fallbacks.
 External I/O: none directly (delegates to the injected candidate probes).

 A candidate passes when none of its required probes was refused and none went
-unanswered. The ones before it are passed over: recorded, never a failure of the
-activation or of the fleet check. When none passes, the first that was only
-unanswered is handed over unproven (`MST-FAIL-04`); when every one was refused,
-every refusal stands and the activation is refused.
+unanswered. Every candidate is probed. The first that passes is chosen; each later
+one that passes is handed over after it as a fallback, with its vendor's key, so the
+role can move to it during the night (`DLIB-FAIL-05`). Every other candidate is
+passed over: recorded, never a failure of the activation or of the fleet check. When
+none passes, the first that was only unanswered is handed over unproven
+(`MST-FAIL-04`) with no fallback; when every one was refused, every refusal stands
+and the activation is refused.
 """

 from __future__ import annotations
@@ -24,14 +28,16 @@ if TYPE_CHECKING:
     from agents.master.credential_check import CredentialTest, PassCache
     from agents.master.model_candidates import LlmCandidate, LlmRole

+type Choice = tuple[Outcomes, str, tuple[str, ...], tuple[str, ...]]
+

 def choose_llm(
     entries: list[tuple[CredentialTest, LlmCandidate, LlmRole]],
     config: dict[str, object],
     str_config: Mapping[str, str],
     cache: PassCache | None,
-) -> tuple[Outcomes, str, tuple[str, ...]]:
-    """Return the outcomes to report, the chosen label and the passed-over lines."""
+) -> Choice:
+    """Return the outcomes, the chosen label, the passed over and the fallbacks."""
     groups: dict[LlmCandidate, list[CredentialTest]] = {}
     roles: dict[LlmCandidate, LlmRole] = {}
     for test, candidate, role in entries:
@@ -43,8 +49,6 @@ def choose_llm(
         for test in group:
             outcomes.run(test, str_config, cache)
         tried.append((candidate, outcomes))
-        if outcomes.proven:
-            break
     chosen = next((item for item in tried if item[1].proven), None) or next(
         (item for item in tried if not item[1].failed_required), None
     )
@@ -52,24 +56,36 @@ def choose_llm(
         refused = Outcomes()
         for _, outcomes in tried:
             refused.extend(outcomes)
-        return refused, "", ()
+        return refused, "", (), ()
     candidate, outcomes = chosen
-    _hand_over(config, candidate, roles[candidate])
+    later = tried[tried.index(chosen) + 1 :]
+    fallbacks = tuple(item for item, other in later if other.proven)
+    report = Outcomes()
+    report.extend(outcomes)
+    for item, other in later:
+        if item in fallbacks:
+            report.extend(other)
+    _hand_over(config, candidate, fallbacks, roles[candidate])
     passed_over = tuple(
         f"{item.label}: {other.first_reason()}"
         for item, other in tried
-        if item != candidate
+        if item != candidate and item not in fallbacks
     )
-    return outcomes, candidate.label, passed_over
+    return report, candidate.label, passed_over, tuple(f.label for f in fallbacks)


 def _hand_over(
-    config: dict[str, object], candidate: LlmCandidate, role: LlmRole
+    config: dict[str, object],
+    candidate: LlmCandidate,
+    fallbacks: tuple[LlmCandidate, ...],
+    role: LlmRole,
 ) -> None:
-    """Name the candidate in the role's keys; withhold every other vendor's key."""
+    """Name the candidate and its fallbacks; withhold every vendor's key none uses."""
+    vendors = {candidate.vendor, *(item.vendor for item in fallbacks)}
     for vendor, key in KEY_ENV.items():
-        if vendor != candidate.vendor:
+        if vendor not in vendors:
             config.pop(key, None)
     config[role.vendor_key] = candidate.vendor
     config[role.model_key] = candidate.model
     config[role.effort_key] = candidate.effort
+    config[role.fallbacks_key] = ",".join(item.label for item in fallbacks)
```

`agents/master/credential_test.py`:

```diff
diff --git a/agents/master/credential_test.py b/agents/master/credential_test.py
index 2baeee81..28ab55cf 100644
--- a/agents/master/credential_test.py
+++ b/agents/master/credential_test.py
@@ -68,7 +68,7 @@ def resolve_and_test_report(
     """Resolve secrets, run applicable tests, and return activation evidence.

     An agent type with LLM candidates runs its other tests first, then is handed
-    the first candidate that passes (`model_choice`).
+    the first candidate that passes and each later one that passes (`model_choice`).
     """
     config = resolve_config(agent_type, store, secret_map)
     str_config = {k: v for k, v in config.items() if isinstance(v, str)}
@@ -86,6 +86,13 @@ def resolve_and_test_report(
     ]
     if not candidates:
         return outcomes.report(config)
-    chosen, label, passed_over = choose_llm(candidates, config, str_config, cache)
+    chosen, label, passed_over, fallbacks = choose_llm(
+        candidates, config, str_config, cache
+    )
     outcomes.extend(chosen)
-    return outcomes.report(config, llm_candidate=label, llm_passed_over=passed_over)
+    return outcomes.report(
+        config,
+        llm_candidate=label,
+        llm_passed_over=passed_over,
+        llm_fallbacks=fallbacks,
+    )
```

`agents/master/credential_outcomes.py`:

```diff
diff --git a/agents/master/credential_outcomes.py b/agents/master/credential_outcomes.py
index 1390943b..21f2fa45 100644
--- a/agents/master/credential_outcomes.py
+++ b/agents/master/credential_outcomes.py
@@ -90,6 +90,7 @@ class Outcomes:
         *,
         llm_candidate: str = "",
         llm_passed_over: tuple[str, ...] = (),
+        llm_fallbacks: tuple[str, ...] = (),
     ) -> CredentialTestReport:
         """Freeze the outcomes into the activation evidence."""
         return CredentialTestReport(
@@ -104,4 +105,5 @@ class Outcomes:
             tuple(self.credential_failures),
             llm_candidate,
             llm_passed_over,
+            llm_fallbacks,
         )
```

`agents/master/credential_report.py`:

```diff
diff --git a/agents/master/credential_report.py b/agents/master/credential_report.py
index efa3990e..69e69e33 100644
--- a/agents/master/credential_report.py
+++ b/agents/master/credential_report.py
@@ -47,13 +47,15 @@ class CredentialTestReport:
     credential_failures: tuple[CredentialFailure, ...] = ()
     llm_candidate: str = ""
     llm_passed_over: tuple[str, ...] = ()
+    llm_fallbacks: tuple[str, ...] = ()


 def credential_test_props(report: CredentialTestReport) -> dict[str, object]:
     """Return graph-safe activation props for credential-test evidence.

-    An agent type that chose an LLM candidate also records which one, and each
-    candidate passed over before it with the reason (DL-289).
+    An agent type that chose an LLM candidate also records which one, each
+    candidate passed over with the reason, and the fallbacks handed over after
+    it (DL-289).
     """
     props: dict[str, object] = {
         "credential_tests_declared": list(report.applicable),
@@ -68,6 +70,7 @@ def credential_test_props(report: CredentialTestReport) -> dict[str, object]:
     if report.llm_candidate:
         props["llm_candidate"] = report.llm_candidate
         props["llm_passed_over"] = list(report.llm_passed_over)
+        props["llm_fallbacks"] = list(report.llm_fallbacks)
     return props


```

`orchestration/packs/trading_llm.json`:

```diff
diff --git a/orchestration/packs/trading_llm.json b/orchestration/packs/trading_llm.json
index 8c4d2163..a8ca0714 100644
--- a/orchestration/packs/trading_llm.json
+++ b/orchestration/packs/trading_llm.json
@@ -1,5 +1,5 @@
 {
-  "_comment": "The fleet's LLM declaration (DL-282, DL-289). candidates: the ordered ways an LLM role may run, each a vendor, a model and an effort, the preferred first. The master probes an agent type in roles with each candidate in order at every activation and hands it the first that works; the vendor of the first candidate is the declared provider, written by infra/deploy-agents.ps1 and scripts/switch_llm_config.py into each app key under apps (master first), and the master puts that vendor's candidates first. roles: the configuration keys each choosing agent type is handed its candidate in.",
+  "_comment": "The fleet's LLM declaration (DL-282, DL-289). candidates: the ordered ways an LLM role may run, each a vendor, a model and an effort, the preferred first. The master probes an agent type in roles with each candidate in order at every activation and hands it the first that works; the vendor of the first candidate is the declared provider, written by infra/deploy-agents.ps1 and scripts/switch_llm_config.py into each app key under apps (master first), and the master puts that vendor's candidates first. The master probes every candidate and hands over each later one that also works as a fallback, which the role moves to when a vendor refuses a request during the night. roles: the configuration keys each choosing agent type is handed its candidate and its fallbacks in.",
   "candidates": [
     { "vendor": "openai", "model": "gpt-5.5", "effort": "high" },
     { "vendor": "anthropic", "model": "claude-opus-5", "effort": "max" }
@@ -15,17 +15,20 @@
     "deliberator-manager": {
       "vendor": "DELIBERATOR_LLM_PROVIDER",
       "model": "DELIBERATOR_JUDGE_MODEL",
-      "effort": "DELIBERATOR_EFFORT"
+      "effort": "DELIBERATOR_EFFORT",
+      "fallbacks": "DELIBERATOR_LLM_FALLBACKS"
     },
     "deliberator-proponent": {
       "vendor": "DELIBERATOR_LLM_PROVIDER",
       "model": "DELIBERATOR_DEFENDER_MODEL",
-      "effort": "DELIBERATOR_EFFORT"
+      "effort": "DELIBERATOR_EFFORT",
+      "fallbacks": "DELIBERATOR_LLM_FALLBACKS"
     },
     "deliberator-opponent": {
       "vendor": "DELIBERATOR_LLM_PROVIDER",
       "model": "DELIBERATOR_CHALLENGER_MODEL",
-      "effort": "DELIBERATOR_EFFORT"
+      "effort": "DELIBERATOR_EFFORT",
+      "fallbacks": "DELIBERATOR_LLM_FALLBACKS"
     }
   }
 }
```

### 2. The deliberator moves on a refusal

Two new modules, the ledger wrapper moved out of `agent.py`, the kernel ledger's optional `passed_over`, the role built on its chain, the new setting.

`agents/deliberator/model_chain.py` (new, 122 lines):

```python
"""A role's handed-over LLM candidates, in order, and the move to the next (DL-289 P3).

Agent: deliberator
Role: hold one client per candidate the master handed the role; move the process to
      the next candidate when a vendor answers a request with an error status.
External I/O: none directly (the vendor clients it builds make the calls).

The master hands a role its chosen candidate under the role's three keys and each
later candidate that also passed under ``DELIBERATOR_LLM_FALLBACKS``, with its
vendor's key (`MST-OUT-05`). A vendor that answers with an HTTP error status
generated nothing, so the request is sent to the next candidate and the process
stays on it (`DLIB-FAIL-05`). A time-out or a dropped connection has no status: the
call's fate is unknown and its time is spent, so it fails the request as before.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

from kernel.llm_factory import build_llm, key_env_var

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from agents.deliberator.settings import DeliberatorSettings
    from kernel.llm import LLMClient

_ERROR_STATUSES = range(400, 600)


@dataclass(frozen=True)
class RoleCandidate:
    """One handed-over way to run the role: its label, its model and its client."""

    label: str
    model: str
    client: LLMClient


class ModelChain:
    """The role's candidates in hand-over order; the process runs on one at a time.

    Shared by the manager's concurrent orders: a request refused by a candidate the
    process has already left is sent to the one in use, so two refusals of one
    candidate move the process once.
    """

    def __init__(self, candidates: Sequence[RoleCandidate]) -> None:
        """Hold the candidates, the first in use."""
        if not candidates:
            raise ValueError("a role needs at least one LLM candidate")
        self.candidates = tuple(candidates)
        self._index = 0
        self._lock = threading.Lock()

    def current(self) -> RoleCandidate:
        """Return the candidate the process is on."""
        with self._lock:
            return self.candidates[self._index]

    def after(self, refused: RoleCandidate) -> RoleCandidate | None:
        """Move past *refused* and return the candidate to send to; None at the end."""
        with self._lock:
            position = self.candidates.index(refused)
            if position + 1 >= len(self.candidates):
                return None
            self._index = max(self._index, position + 1)
            return self.candidates[self._index]


def refusal(exc: BaseException) -> str | None:
    """Name a vendor's error answer as ``http_<status>``, else None.

    Both SDKs give an API status error the HTTP status as ``status_code``. A
    time-out, a dropped connection, a truncated completion or an unreadable turn
    carries none.
    """
    status = getattr(exc, "status_code", None)
    if isinstance(status, bool) or not isinstance(status, int):
        return None
    return f"http_{status}" if status in _ERROR_STATUSES else None


def handed_fallbacks(settings: DeliberatorSettings) -> tuple[tuple[str, str, str], ...]:
    """Return the fallbacks the master handed over, each vendor, model and effort."""
    found: list[tuple[str, str, str]] = []
    for item in settings.llm_fallbacks.split(","):
        text = item.strip()
        if not text:
            continue
        parts = text.split("/")
        if len(parts) != 3 or not all(parts):  # vendor/model/effort
            raise ValueError(f"unreadable LLM fallback {text!r}")
        found.append((parts[0], parts[1], parts[2]))
    return tuple(found)


def build_role_chain(
    settings: DeliberatorSettings,
    environ: Mapping[str, str],
    first: LLMClient,
    *,
    build: Callable[..., LLMClient] = build_llm,
) -> ModelChain:
    """Put the role's chosen client first, then one client per handed-over fallback."""
    model = settings.model_for_role(settings.peer_role or "judge")
    label = f"{settings.llm_provider}/{model}/{settings.effort}"
    candidates = [RoleCandidate(label, model, first)]
    for vendor, fallback_model, effort in handed_fallbacks(settings):
        client = build(
            vendor,
            api_key=environ.get(key_env_var(vendor)),
            model=fallback_model,
            max_tokens=settings.max_tokens,
            effort=effort,
        )
        candidates.append(
            RoleCandidate(f"{vendor}/{fallback_model}/{effort}", fallback_model, client)
        )
    return ModelChain(candidates)
```

`agents/deliberator/turn_ledger.py` (new, 115 lines):

```python
"""The ledger row around each completion a deliberator role makes.

Agent: deliberator
Role: write one LLMCall per completion attempt, and send a request a vendor refused
      to the role's next handed-over candidate (DLIB-OBS-08, DLIB-FAIL-05).
External I/O: GraphStore writes; the LLM vendor through the injected clients.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.model_chain import ModelChain, RoleCandidate, refusal
from agents.deliberator.prompt_recipe import PROMPT_RECIPE_HASH
from kernel import (
    LLMCompletionStoppedError,
    llm_stop_reason,
    llm_usage,
    record_llm_call,
)

if TYPE_CHECKING:
    from kernel import GraphStore, LLMClient, Node


class LedgerLLM:
    """LLMClient wrapper that writes one shared LLMCall node per completion.

    Given a plain client it runs that client under *model*, as before; given the
    role's `ModelChain` it runs the candidate in use, and a vendor's error answer
    sends the request to the next candidate, each attempt its own row.
    """

    def __init__(
        self,
        graph: GraphStore,
        llm: LLMClient | ModelChain,
        *,
        calling_agent: str,
        model: str,
        correlation_id: str,
    ) -> None:
        """Wrap the role's client or chain for one request."""
        self._graph = graph
        self._chain = (
            llm
            if isinstance(llm, ModelChain)
            else ModelChain((RoleCandidate("", model, llm),))
        )
        self._calling_agent = calling_agent
        self._correlation_id = correlation_id
        self.last_node_key: str | None = None

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Answer on the candidate in use; a vendor's refusal moves to the next."""
        candidate = self._chain.current()
        passed_over: list[str] = []
        while True:
            try:
                return self._attempt(
                    candidate, tuple(passed_over), system, user, tool_schema
                )
            except Exception as exc:
                reason = refusal(exc)
                following = None if reason is None else self._chain.after(candidate)
                if following is None:
                    raise
                passed_over.append(f"{candidate.label}: {reason}")
                candidate = following

    def _attempt(
        self,
        candidate: RoleCandidate,
        passed_over: tuple[str, ...],
        system: str,
        user: str,
        tool_schema: dict[str, object],
    ) -> str:
        """Record one call around one candidate's completion."""
        llm = candidate.client
        raw = ""
        stopped: LLMCompletionStoppedError | None = None
        with record_llm_call(
            self._graph,
            calling_agent=self._calling_agent,
            correlation_id=self._correlation_id,
            model=candidate.model,
            prompt=user,
            system_prompt=system,
            prompt_recipe_hash=PROMPT_RECIPE_HASH,
            passed_over=passed_over,
        ) as call:
            try:
                raw = llm.complete(system=system, user=user, tool_schema=tool_schema)
            except LLMCompletionStoppedError as exc:
                call.set_stop_reason(exc.stop_reason)
                stopped = exc
            else:
                call.set_response(raw)
                call.set_stop_reason(llm_stop_reason(llm))
            # Usage is read on both paths: a truncated or refused completion was
            # still generated and still billed, so dropping its tokens here would
            # under-report exactly the calls that cost the most — `effort=max`
            # spends the whole output budget before raising `max_tokens`, and the
            # estimate fallback sees an empty response, so a success-only capture
            # records those calls as costing *zero* output. Measured: planting
            # that guard turned the truncation test red at `assert 0 == 4096`.
            call.set_usage(llm_usage(llm))
        node: Node | None = call.node
        self.last_node_key = node.key if node is not None else None
        if stopped is not None:
            raise stopped
        return raw
```

`kernel/llm_ledger.py`:

```diff
diff --git a/kernel/llm_ledger.py b/kernel/llm_ledger.py
index fa854c50..9151dd25 100644
--- a/kernel/llm_ledger.py
+++ b/kernel/llm_ledger.py
@@ -58,6 +58,7 @@ def record_llm_call(
     prompt: str,
     system_prompt: str = "",
     prompt_recipe_hash: str = RECIPE_UNKNOWN,
+    passed_over: tuple[str, ...] = (),
 ) -> Iterator[LLMCallCapture]:
     """Persist one LLM call after the wrapped completion finishes.

@@ -66,7 +67,8 @@ def record_llm_call(
     `DLIB-IDM-02` reads as though the recorded hashes bound what the model was
     asked, and until now only the *user* half was hashed, so two calls with
     different system prompts and identical user context were indistinguishable —
-    exactly what a role-prompt experiment changes.
+    exactly what a role-prompt experiment changes. ``passed_over`` names the
+    candidates that refused this same request before this call was made.
     """
     started = time.perf_counter()
     capture = LLMCallCapture(prompt=prompt)
@@ -93,6 +95,7 @@ def record_llm_call(
             token_source=counts.token_source,
             system_prompt_hash=digest_text(system_prompt),
             prompt_recipe_hash=prompt_recipe_hash,
+            passed_over=passed_over,
         )


@@ -113,6 +116,7 @@ def write_llm_call(
     token_source: str = SOURCE_ESTIMATED,
     system_prompt_hash: str = "",
     prompt_recipe_hash: str = RECIPE_UNKNOWN,
+    passed_over: tuple[str, ...] = (),
 ) -> Node:
     """Append this completion under the first free shared LLM call ledger key.

@@ -120,33 +124,34 @@ def write_llm_call(
     it cannot silently present a word count as a vendor measurement, and
     ``prompt_recipe_hash`` defaults to ``unknown`` for the same reason: an
     unrecorded renderer must read as unrecorded, never as *this* renderer.
+    ``llm_passed_over`` is written only when a candidate refused the request
+    before this call, so every other row is unchanged.
     """
     first = f"llmcall:{calling_agent}:{correlation_id}"
     key, repeat = first, 0
     while graph.get_node("LLMCall", key) is not None:
         repeat += 1
         key = f"{first}:repeat-{repeat}"
-    return graph.merge_node(
-        "LLMCall",
-        key,
-        {
-            "calling_agent": calling_agent,
-            "correlation_id": correlation_id,
-            "model": model,
-            "prompt_hash": prompt_hash,
-            "response_hash": response_hash,
-            "tokens_in": tokens_in,
-            "tokens_out": tokens_out,
-            "cache_read_tokens": cache_read_tokens,
-            "cache_write_tokens": cache_write_tokens,
-            "token_source": token_source,
-            "system_prompt_hash": system_prompt_hash,
-            "prompt_recipe_hash": prompt_recipe_hash,
-            "latency_ms": latency_ms,
-            "stop_reason": str(stop_reason or "").strip() or STOP_REASON_UNKNOWN,
-            "created_at": datetime.now(tz=UTC).isoformat(),
-        },
-    )
+    props: dict[str, object] = {
+        "calling_agent": calling_agent,
+        "correlation_id": correlation_id,
+        "model": model,
+        "prompt_hash": prompt_hash,
+        "response_hash": response_hash,
+        "tokens_in": tokens_in,
+        "tokens_out": tokens_out,
+        "cache_read_tokens": cache_read_tokens,
+        "cache_write_tokens": cache_write_tokens,
+        "token_source": token_source,
+        "system_prompt_hash": system_prompt_hash,
+        "prompt_recipe_hash": prompt_recipe_hash,
+        "latency_ms": latency_ms,
+        "stop_reason": str(stop_reason or "").strip() or STOP_REASON_UNKNOWN,
+        "created_at": datetime.now(tz=UTC).isoformat(),
+    }
+    if passed_over:
+        props["llm_passed_over"] = list(passed_over)
+    return graph.merge_node("LLMCall", key, props)


 def digest_text(value: str) -> str:
```

`agents/deliberator/agent.py`:

```diff
diff --git a/agents/deliberator/agent.py b/agents/deliberator/agent.py
index 836e003f..fc973b36 100644
--- a/agents/deliberator/agent.py
+++ b/agents/deliberator/agent.py
@@ -10,8 +10,8 @@ from __future__ import annotations
 from typing import TYPE_CHECKING, cast

 from agents.deliberator.guided_turn import guided_turn
-from agents.deliberator.prompt_recipe import PROMPT_RECIPE_HASH
 from agents.deliberator.settings import DeliberatorSettings
+from agents.deliberator.turn_ledger import LedgerLLM
 from contracts.deliberator import (
     DebateProposition,
     DebateTurnRecord,
@@ -21,20 +21,12 @@ from contracts.deliberator import (
     VerdictRequest,
     contract_for,
 )
-from kernel import (
-    AgentBase,
-    FakeLLMClient,
-    LLMCompletionStoppedError,
-    Proposition,
-    Turn,
-    llm_stop_reason,
-    llm_usage,
-    record_llm_call,
-)
+from kernel import AgentBase, FakeLLMClient, Proposition, Turn
 from kernel import judge_verdict as judge_kernel_verdict

 if TYPE_CHECKING:
-    from kernel import GraphStore, LLMClient, MessageBus, Node
+    from agents.deliberator.model_chain import ModelChain
+    from kernel import GraphStore, LLMClient, MessageBus
     from kernel.agent import AgentHandler


@@ -46,14 +38,19 @@ class DeliberatorAgent(AgentBase):
         bus: MessageBus,
         *,
         graph: GraphStore,
-        llm: LLMClient | None = None,
+        llm: LLMClient | ModelChain | None = None,
         settings: DeliberatorSettings | None = None,
     ) -> None:
-        """Create a deliberator instance with injected bus, graph, and LLM."""
+        """Create a deliberator instance with injected bus, graph, and LLM.
+
+        In the fleet *llm* is the role's `ModelChain`: its handed-over candidates.
+        """
         self.settings = settings if settings is not None else DeliberatorSettings()
         super().__init__(contract_for(self.settings.identity, self.settings.role), bus)
         self._graph = graph
-        self._llm = llm if llm is not None else FakeLLMClient({})
+        self._llm: LLMClient | ModelChain = (
+            llm if llm is not None else FakeLLMClient({})
+        )
         self.handlers = cast(
             "dict[str, AgentHandler]",
             {"debate_turn": self.debate_turn, "verdict": self.verdict},
@@ -65,7 +62,7 @@ class DeliberatorAgent(AgentBase):
         if peer_role is not None and request.role != peer_role:
             raise ValueError(f"{self.settings.identity} cannot serve {request.role}")
         model = self.settings.model_for_role(request.role)
-        ledger = _LedgerLLM(
+        ledger = LedgerLLM(
             self._graph,
             self._llm,
             calling_agent=self.settings.identity,
@@ -81,7 +78,7 @@ class DeliberatorAgent(AgentBase):
     def verdict(self, request: VerdictRequest) -> VerdictReply:
         """Return the manager ruling using the unchanged verdict parser."""
         model = self.settings.model_for_role("judge")
-        ledger = _LedgerLLM(
+        ledger = LedgerLLM(
             self._graph,
             self._llm,
             calling_agent=self.settings.identity,
@@ -101,65 +98,6 @@ class DeliberatorAgent(AgentBase):
         )


-class _LedgerLLM:
-    """LLMClient wrapper that writes one shared LLMCall node per completion."""
-
-    def __init__(
-        self,
-        graph: GraphStore,
-        llm: LLMClient,
-        *,
-        calling_agent: str,
-        model: str,
-        correlation_id: str,
-    ) -> None:
-        self._graph = graph
-        self._llm = llm
-        self._calling_agent = calling_agent
-        self._model = model
-        self._correlation_id = correlation_id
-        self.last_node_key: str | None = None
-
-    def complete(
-        self, *, system: str, user: str, tool_schema: dict[str, object]
-    ) -> str:
-        """Record a call around the injected LLM completion."""
-        raw = ""
-        stopped: LLMCompletionStoppedError | None = None
-        with record_llm_call(
-            self._graph,
-            calling_agent=self._calling_agent,
-            correlation_id=self._correlation_id,
-            model=self._model,
-            prompt=user,
-            system_prompt=system,
-            prompt_recipe_hash=PROMPT_RECIPE_HASH,
-        ) as call:
-            try:
-                raw = self._llm.complete(
-                    system=system, user=user, tool_schema=tool_schema
-                )
-            except LLMCompletionStoppedError as exc:
-                call.set_stop_reason(exc.stop_reason)
-                stopped = exc
-            else:
-                call.set_response(raw)
-                call.set_stop_reason(llm_stop_reason(self._llm))
-            # Usage is read on both paths: a truncated or refused completion was
-            # still generated and still billed, so dropping its tokens here would
-            # under-report exactly the calls that cost the most — `effort=max`
-            # spends the whole output budget before raising `max_tokens`, and the
-            # estimate fallback sees an empty response, so a success-only capture
-            # records those calls as costing *zero* output. Measured: planting
-            # that guard turned the truncation test red at `assert 0 == 4096`.
-            call.set_usage(llm_usage(self._llm))
-        node: Node | None = call.node
-        self.last_node_key = node.key if node is not None else None
-        if stopped is not None:
-            raise stopped
-        return raw
-
-
 def _proposition(proposition: DebateProposition) -> Proposition:
     return Proposition(proposition.decision, proposition.context)

```

`agents/deliberator/entrypoint.py`:

```diff
diff --git a/agents/deliberator/entrypoint.py b/agents/deliberator/entrypoint.py
index b5c5a5ae..0d5534a2 100644
--- a/agents/deliberator/entrypoint.py
+++ b/agents/deliberator/entrypoint.py
@@ -10,6 +10,7 @@ from __future__ import annotations
 from typing import TYPE_CHECKING

 from agents.deliberator.agent import DeliberatorAgent
+from agents.deliberator.model_chain import build_role_chain
 from agents.deliberator.peer_client import BusPeerClient, ServiceBusPeerClient
 from agents.deliberator.settings import DeliberatorSettings
 from kernel import AzureServiceBusSettings, CollectingFaultSink, InProcessBus
@@ -24,6 +25,7 @@ PEER_SERVE_IDLE_SLEEP_SECONDS = 0
 if TYPE_CHECKING:
     from collections.abc import Callable, Mapping

+    from agents.deliberator.model_chain import ModelChain
     from agents.deliberator.peer_client import PeerClient
     from kernel import FaultSink, GraphStore, LLMClient, MessageBus

@@ -41,7 +43,7 @@ def build_served_bus(
 def build_manager(
     graph: GraphStore,
     settings: DeliberatorSettings | None = None,
-    llm: LLMClient | None = None,
+    llm: LLMClient | ModelChain | None = None,
     sink: FaultSink | None = None,
 ) -> tuple[DeliberatorAgent, PeerClient]:
     """Build the manager and its production peer-client port."""
@@ -92,8 +94,17 @@ def build_role_llm(
     )


+def build_role_models(
+    settings: DeliberatorSettings, environ: Mapping[str, str]
+) -> ModelChain:
+    """Build the role's chosen client, then one per handed-over fallback (DL-289)."""
+    return build_role_chain(settings, environ, build_role_llm(settings, environ))
+
+
 def serve_peer(
-    graph: GraphStore, settings: DeliberatorSettings, llm: LLMClient | None
+    graph: GraphStore,
+    settings: DeliberatorSettings,
+    llm: LLMClient | ModelChain | None,
 ) -> None:
     """Serve a peer without sleeping beyond the Service Bus receive wait."""
     bus = InProcessBus()
@@ -122,7 +133,7 @@ def main() -> None:  # pragma: no cover
         master_public_key_from_env(),
     )
     graph = build_graph_from_env()
-    llm = build_role_llm(settings, os.environ)
+    llm = build_role_models(settings, os.environ)
     if settings.role == "manager":
         fault_sink = GraphFaultSink(graph, CollectingFaultSink())
         manager, peer_client = build_manager(graph, settings, llm=llm, sink=fault_sink)
```

`agents/deliberator/settings.py`:

```diff
diff --git a/agents/deliberator/settings.py b/agents/deliberator/settings.py
index a45589a8..64c2014a 100644
--- a/agents/deliberator/settings.py
+++ b/agents/deliberator/settings.py
@@ -58,9 +58,18 @@ class DeliberatorSettings(AgentSettings):
     llm_provider: str = tunable(
         default="anthropic",
         why=(
-            "Which vendor answers deliberation calls. A tunable, not an automatic "
-            "fallback: a silent switch would make 'which model reviewed this order' "
-            "unanswerable afterwards. Switching is an operator act (DL-99)."
+            "Which vendor answers deliberation calls first. The master hands each "
+            "role its chosen candidate's vendor at activation (DL-289); a move to a "
+            "fallback is recorded on the LLMCall row, so 'which model reviewed this "
+            "order' stays answerable."
+        ),
+    )
+    llm_fallbacks: str = tunable(
+        "",
+        why=(
+            "The later candidates the master handed over, vendor/model/effort joined "
+            "by commas. A vendor that answers a request with an error status sends "
+            "it to the next, and the process stays there (DL-289 P3). Empty: none."
         ),
     )
     defender_model: str = tunable(
```

### 3. The run says so

`llm_switches` read from the answered rows, written on every `DeliberationRun`; the vocabulary declares the three new properties.

`agents/deliberator/review_record.py`:

```diff
diff --git a/agents/deliberator/review_record.py b/agents/deliberator/review_record.py
index 52b38afc..15e90050 100644
--- a/agents/deliberator/review_record.py
+++ b/agents/deliberator/review_record.py
@@ -143,3 +143,27 @@ def role_models(
         or settings.model_for_role(role)
         for role, identity in served
     }
+
+
+def llm_switches(
+    graph: GraphStore | None, llm_call_keys: tuple[str, ...] | list[str]
+) -> list[str]:
+    """Return each role that answered on a later candidate, and what refused first.
+
+    Read from the run's own `LLMCall` rows: a row whose request a candidate refused
+    before it names them under `llm_passed_over` (DLIB-FAIL-05). One line per role,
+    model and refusals, in the order the rows were written.
+    """
+    lines: list[str] = []
+    for key in llm_call_keys:
+        node = graph.get_node("LLMCall", key) if graph is not None else None
+        over = node.props.get("llm_passed_over") if node is not None else None
+        if node is None or not isinstance(over, (list, tuple)) or not over:
+            continue
+        line = (
+            f"{node.props.get('calling_agent', '')} switched to "
+            f"{node.props.get('model', '')} (passed over {'; '.join(map(str, over))})"
+        )
+        if line not in lines:
+            lines.append(line)
+    return lines
```

`agents/deliberator/store.py`:

```diff
diff --git a/agents/deliberator/store.py b/agents/deliberator/store.py
index c72eed44..af616059 100644
--- a/agents/deliberator/store.py
+++ b/agents/deliberator/store.py
@@ -50,8 +50,13 @@ def write_deliberation_run(
     failed_open_tickers: list[str],
     failed_open_reason: str,
     llm_call_keys: list[str],
+    llm_switches: list[str] | None = None,
 ) -> Node:
-    """Write one idempotent DeliberationRun and link LLM audit calls."""
+    """Write one idempotent DeliberationRun and link LLM audit calls.
+
+    ``llm_switches`` names each role that answered on a later candidate during
+    the run (DLIB-OUT-02); written empty when none did.
+    """
     key = order_set.run_id
     current = graph.get_node(DELIBERATION_RUN_LABEL, key)
     if current is None:
@@ -72,6 +77,7 @@ def write_deliberation_run(
                 "orphaned_reply_count": orphaned_reply_count,
                 "failed_open_tickers": failed_open_tickers,
                 "failed_open_reason": failed_open_reason,
+                "llm_switches": list(llm_switches or []),
                 "created_at": datetime.now(tz=UTC).isoformat(),
             },
         )
```

`agents/deliberator/poll.py`:

```diff
diff --git a/agents/deliberator/poll.py b/agents/deliberator/poll.py
index d0e4085d..49eb97df 100644
--- a/agents/deliberator/poll.py
+++ b/agents/deliberator/poll.py
@@ -16,6 +16,7 @@ from agents.deliberator.review_record import (
     OrderReview,
     fail_open_review,
     failed_open_reason,
+    llm_switches,
     narrative,
     role_models,
 )
@@ -85,6 +86,7 @@ def review_pm_node(
         failed_open_tickers=batch.failed_open_tickers,
         failed_open_reason=_combined_failed_open_reason(batch.failed_open_reasons),
         llm_call_keys=batch.llm_call_keys,
+        llm_switches=llm_switches(graph, batch.llm_call_keys),
     )


```

`orchestration/packs/trading_graph_vocabulary.json`:

```diff
diff --git a/orchestration/packs/trading_graph_vocabulary.json b/orchestration/packs/trading_graph_vocabulary.json
index 5299c317..dbf60ec8 100644
--- a/orchestration/packs/trading_graph_vocabulary.json
+++ b/orchestration/packs/trading_graph_vocabulary.json
@@ -396,6 +396,7 @@
       "drain_at",
       "drain_reason",
       "llm_candidate",
+      "llm_fallbacks",
       "llm_passed_over",
       "started_at",
       "state"
@@ -406,6 +407,7 @@
       "failed_open_count",
       "failed_open_reason",
       "failed_open_tickers",
+      "llm_switches",
       "max_rounds",
       "narrative",
       "orphaned_reply_count",
@@ -526,6 +528,7 @@
       "correlation_id",
       "created_at",
       "latency_ms",
+      "llm_passed_over",
       "model",
       "prompt_hash",
       "prompt_recipe_hash",
```

### 4. The brief says so

The LLM line takes the run's `DeliberationRun`.

`orchestration/llm_brief.py`:

```diff
diff --git a/orchestration/llm_brief.py b/orchestration/llm_brief.py
index 086d7a0c..52fcd7ab 100644
--- a/orchestration/llm_brief.py
+++ b/orchestration/llm_brief.py
@@ -2,11 +2,13 @@

 Agent: orchestration
 Role: say in one line when an LLM role was activated on anything but its first
-      working candidate in the last day (DL-289 P2).
+      working candidate in the last day, or passed a candidate over, or switched to
+      a later candidate during the run (DL-289 P2, P3).
 External I/O: reads the injected GraphStore.

 No line when every role ran on its first candidate, so a quiet night briefs as
-before. The master records the choice on each `AgentInstance` it activates.
+before. The master records the choice on each `AgentInstance` it activates; the
+deliberator records a switch during the run on the run's `DeliberationRun`.
 """

 from __future__ import annotations
@@ -19,13 +21,15 @@ from orchestration.daily_brief_fills import parse_instant
 if TYPE_CHECKING:
     from datetime import datetime

-    from kernel import GraphStore
+    from kernel import GraphStore, Node

 BRIEF_WINDOW = timedelta(hours=24)
 _SEP = " · "


-def llm_line(graph: GraphStore, *, now: datetime) -> str | None:
+def llm_line(
+    graph: GraphStore, *, now: datetime, deliberation: Node | None = None
+) -> str | None:
     """Return the brief's LLM line, or None when no candidate was passed over."""
     since = now - BRIEF_WINDOW
     groups: dict[tuple[str, tuple[str, ...]], set[str]] = {}
@@ -38,10 +42,11 @@ def llm_line(graph: GraphStore, *, now: datetime) -> str | None:
         chosen = str(node.props.get("llm_candidate", ""))
         key = (chosen, tuple(str(line) for line in over))
         groups.setdefault(key, set()).add(str(node.props.get("agent_type", "")))
-    if not groups:
-        return None
     parts = [
         f"{', '.join(sorted(types))} on {chosen} (passed over {'; '.join(over)})"
         for (chosen, over), types in sorted(groups.items())
     ]
-    return f"LLM: {_SEP.join(parts)}"
+    switches = deliberation.props.get("llm_switches") if deliberation else None
+    if isinstance(switches, (list, tuple)):
+        parts.extend(f"{line} during the run" for line in map(str, switches))
+    return f"LLM: {_SEP.join(parts)}" if parts else None
```

`orchestration/daily_brief_facts.py`:

```diff
diff --git a/orchestration/daily_brief_facts.py b/orchestration/daily_brief_facts.py
index d49d3bb5..30f06e6f 100644
--- a/orchestration/daily_brief_facts.py
+++ b/orchestration/daily_brief_facts.py
@@ -74,7 +74,7 @@ def brief_facts(
         critical_flags=health["pending_human_flags"],
         last_stage=_last_stage(nodes),
         containers=container_line(graph, now=now, timezone=timezone),
-        llm=llm_line(graph, now=now),
+        llm=llm_line(graph, now=now, deliberation=nodes.get("DeliberationRun")),
     )
     snapshot = nodes.get("Snapshot")
     if snapshot is None or pm_run is None:
```

### 5. The deploy

The `llm-candidates` step sets every role's vocabulary before the packs. Edit byte for byte.

`infra/deploy-agents.ps1`:

```diff
diff --git a/infra/deploy-agents.ps1 b/infra/deploy-agents.ps1
index ade3e6c4..1470e3b6 100644
--- a/infra/deploy-agents.ps1
+++ b/infra/deploy-agents.ps1
@@ -770,9 +770,11 @@ function Enable-ContainerSensor {
 }

 function Enable-LlmCandidates {
-  # DL-289: run BEFORE the retag that brings the master's S276 image. That image writes
-  # llm_passed_over on every fleet check and llm_candidate on a chosen activation, which
-  # the earlier vocabulary refuses; so the vocabulary goes first, then the candidate pack.
+  # DL-289: run BEFORE the retag that brings a master or a role image of S276 or later.
+  # Those images write properties the earlier vocabulary refuses: the master
+  # llm_passed_over, llm_candidate and llm_fallbacks; each role (the pack's roles) the
+  # LLMCall row's llm_passed_over and the DeliberationRun's llm_switches (S277). So the
+  # vocabulary goes first, on the master and on every role, then the candidate pack.
   # The credential pack rides with it: the injected one wins over the image's file, and
   # the S276 master refuses to start on an LLM probe without candidate_paths. An older
   # image ignores the candidate pack and the new probe keys. Each step is read back, so a
@@ -780,6 +782,11 @@ function Enable-LlmCandidates {
   Top "LLM CANDIDATES"
   $vocabOk = Set-AppVocabulary "master"
   Check $vocabOk "graph vocabulary on master"
+  foreach ($role in @((Load-LlmPack).roles.PSObject.Properties.Name)) {
+    $roleOk = Set-AppVocabulary $role
+    Check $roleOk "graph vocabulary on $role"
+    $vocabOk = $vocabOk -and $roleOk
+  }
   $state = $null
   if ($vocabOk) {
     $state = Invoke-Az @(
```

### 6. The law books — master v1.12, deliberator v1.18, dispatcher v1.5

Apply exactly. The test plans and the two roll-ups are yours (MUST RULE).

`agents/master/laws/laws.md`:

```diff
diff --git a/agents/master/laws/laws.md b/agents/master/laws/laws.md
index 3a01a99d..08a558c8 100644
--- a/agents/master/laws/laws.md
+++ b/agents/master/laws/laws.md
@@ -1,6 +1,6 @@
 # `Master` — Laws

-**Prefix:** `MST` · **status:** LOCKED v1.11 · **Owner:** Yury Gurevich
+**Prefix:** `MST` · **status:** LOCKED v1.12 · **Owner:** Yury Gurevich

 > Receive EHLO from freshly-started agent containers, verify declared capabilities,
 > distribute minimum-privilege credentials via ACTIVATE, and maintain the
@@ -64,15 +64,17 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   declared LLM provider for every agent type in the grant policy and writes one `FleetPreflight`
   node per check. An empty provider leaves every probe applicable. The check passes only if every
   probe passed or has a fresh costly-pass cache entry. A credential failure or a transport failure
-  fails it. An LLM candidate passed over for a later one fails nothing (`MST-FAIL-08`); the node
-  lists each as `<agent type>: <vendor/model/effort>: <reason>` under `llm_passed_over`.
+  fails it. An LLM candidate passed over fails nothing (`MST-FAIL-08`); the node lists each as
+  `<agent type>: <vendor/model/effort>: <reason>` under `llm_passed_over`.
 - **MST-OUT-05** — An agent type named under `roles` in the pack's LLM declaration is activated on
   the first declared candidate (a vendor, a model and an effort) whose probes pass, the declared
-  provider's candidates tried first, each group in declared order. Each candidate is probed with
-  its own model and effort; the ones after the first that passes are not probed. ACTIVATE's config
-  names the chosen vendor, model and effort under the role's three keys and holds no other vendor's
-  key. The `AgentInstance` records `llm_candidate` (`vendor/model/effort`) and `llm_passed_over`,
-  one `<vendor/model/effort>: <reason>` for each candidate tried before it.
+  provider's candidates tried first, each group in declared order. Every candidate is probed, each
+  with its own model and effort. ACTIVATE's config names the chosen vendor, model and effort under
+  the role's `vendor`, `model` and `effort` keys and, under its `fallbacks` key, each later candidate
+  whose probes also passed, as `vendor/model/effort` joined by commas in that order (empty when
+  none); it holds the key of each vendor those candidates name and no other. The `AgentInstance`
+  records `llm_candidate` (`vendor/model/effort`), `llm_fallbacks` (the labels handed over after
+  it) and `llm_passed_over`, one `<vendor/model/effort>: <reason>` for each other candidate.

 ## Never (`NEV`)

@@ -93,7 +95,8 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   or an agent type granted the declared vendor's key without a probe tagged for that vendor.
   An empty provider preserves the original probes and secret map after validating probe tags.
   An agent type named under the LLM declaration's `roles` keeps every vendor's probes and keys at
-  start; `MST-OUT-05` withholds the vendors not chosen at each activation.
+  start; `MST-OUT-05` withholds at each activation the key of every vendor that neither the chosen
+  candidate nor a fallback names.
 - **MST-NEV-08** — Master refuses to start on an LLM declaration with no candidate, a candidate of an
   unknown vendor, a model of another known vendor's family, a repeated candidate, a field that is not
   a non-empty string, or a role whose agent type has, for some candidate, no probe of that vendor, a
@@ -169,11 +172,12 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   the setting that fixes it (`MASTER_REMEDIATION_MODE=manual`), so the switch is never silently
   inert. `manual` starts unchanged. *(DRIFT-059; the guard is `agents/master/remediation_posture.py`,
   S203.)*
-- **MST-FAIL-08** — An LLM candidate whose probes were refused or went unanswered, when a later
+- **MST-FAIL-08** — An LLM candidate whose probes were refused or went unanswered, when another
   candidate passes, is neither a credential failure of the activation nor a failure of the fleet
-  check. When no candidate passes, the first whose probes were only unanswered is handed over
-  unproven, as `MST-FAIL-04` allows; when every candidate was refused, every refusal stands and the
-  activation is refused (`MST-NEV-06`).
+  check, before the chosen candidate or after it; it is passed over, and never handed over as a
+  fallback. When no candidate passes, the first whose probes were only unanswered is handed over
+  unproven, as `MST-FAIL-04` allows, with no fallback; when every candidate was refused, every
+  refusal stands and the activation is refused (`MST-NEV-06`).

 **Remediation is outside this constitution.** No clause governs *attempting* a remediation: what
 master may attempt, the one-shot bound, or what is recorded when an attempt fails. Those clauses are
@@ -230,8 +234,8 @@ guarantees.
 - **MST-OBS-03** — Fault channel receives all graph/Key Vault errors via `fault_boundary`.
 - **MST-OBS-04** — Successful activation records applicable credential-test evidence on the
   `AgentInstance`: live-tested names, live-passed names, cached-pass names, optional failures, and
-  transport failures; for an agent type that chose an LLM candidate, also the candidate and the ones
-  passed over (`MST-OUT-05`).
+  transport failures; for an agent type that chose an LLM candidate, also the candidate, the
+  fallbacks handed over after it and the ones passed over (`MST-OUT-05`).
 - **MST-OBS-05** — A stop leaves two lines on the container's stderr. When the signal arrives:
   `[<agent>] stop signal <NAME>: taking no new work`, written unbuffered from the handler, so a
   process killed later still shows that it was told to stop. When the process has closed what it
@@ -295,6 +299,12 @@ guarantees.

 ## Changelog

+- v1.12 — S277 / DL-289 P3 (2026-10-15): a role can move to a later candidate during the night.
+  `MST-OUT-05` amended: every candidate is probed, and each later one that passes is handed over as
+  a fallback under the role's `fallbacks` key with its vendor's key, recorded as `llm_fallbacks`;
+  this reverses S262's one-key rule for the declared roles alone (DL-282). `MST-OUT-04`, `MST-NEV-07`,
+  `MST-FAIL-08` and `MST-OBS-04` amended for it. No clause added.
+
 - v1.11 — S276 / DL-289 (2026-10-15): an LLM role runs on the first declared candidate that works.
   New `MST-OUT-05` (the choice at activation and its record), `MST-NEV-08` (the start-time refusals
   of a declaration no role could run on) and `MST-FAIL-08` (a passed-over candidate fails nothing).
```

`agents/deliberator/laws/laws.md`:

```diff
diff --git a/agents/deliberator/laws/laws.md b/agents/deliberator/laws/laws.md
index 068593a2..34940170 100644
--- a/agents/deliberator/laws/laws.md
+++ b/agents/deliberator/laws/laws.md
@@ -1,6 +1,6 @@
 # `Deliberator` -- Laws

-**Prefix:** `DLIB` · **status:** LOCKED v1.17 · **Owner:** Yury Gurevich
+**Prefix:** `DLIB` · **status:** LOCKED v1.18 · **Owner:** Yury Gurevich

 > Adversarially review PM-approved orders with a bounded proponent/opponent debate
 > and a manager verdict before execution, subtracting unsafe orders only when the
@@ -50,7 +50,10 @@ ADR-0020; declaring is not proving, so every clause starts gray.
   containing only `overturn` verdicts, per-ticker debate turns, role models,
   narrative, and creation time. A role's model is the one its `LLMCall` rows in
   the run name for the identity that served it, several joined in sorted order;
-  a role with no row names its resolved setting.
+  a role with no row names its resolved setting. `llm_switches` holds, for each
+  of the run's `LLMCall` rows that names `llm_passed_over` (`DLIB-FAIL-05`), one
+  line `<calling agent> switched to <model> (passed over <its lines joined by
+  "; ">)`, each distinct line once, in row order; it is empty when none does.
 + **DLIB-OUT-03** -- Each LLM call writes a shared `LLMCall` with
   `calling_agent`, model, hashes, token counts, latency, and timestamp.
 + **DLIB-OUT-04** -- `overturn` verdicts may only subtract existing
@@ -126,7 +129,8 @@ ADR-0020; declaring is not proving, so every clause starts gray.

 + **DLIB-FAIL-01** -- Any LLM, peer-call, or unreadable judge-ruling failure
   is fail-open for the affected order and records an uphold verdict with a
-  failure rationale.
+  failure rationale. An LLM request is failed only once `DLIB-FAIL-05` has no
+  candidate left to send it to.
 + **DLIB-FAIL-02** -- A graph-write failure records a fault; no compensating
   delete is attempted.
 + **DLIB-FAIL-03** -- After a crash, the manager retries any `PMRun` that still
@@ -134,6 +138,15 @@ ADR-0020; declaring is not proving, so every clause starts gray.
 + **DLIB-FAIL-04** -- A provider-declared truncated or refused completion, or a
   judge response that cannot be read as one of the declared rulings, is a
   failed LLM call with its stop or parse reason named.
++ **DLIB-FAIL-05** -- A request a vendor answers with an HTTP error status (400
+  to 599) is sent to the role's next handed-over candidate, and the process stays
+  on that candidate for every later request; a request refused by a candidate the
+  process has already left is sent to the one in use, so each candidate is tried
+  at most once a request. A time-out, a dropped connection, a truncated
+  completion or an unreadable reply moves nothing. Each attempt is its own
+  `LLMCall` row, under its candidate's model; the row of an attempt made after a
+  refusal names, under `llm_passed_over`, each `<vendor/model/effort>:
+  http_<status>` that refused the request before it.

 ## Type Alignment (`TYP`)

@@ -168,8 +181,9 @@ ADR-0020; declaring is not proving, so every clause starts gray.
 + **DLIB-DEP-03** -- `DEP-LLM` for external model calls and fail-open behaviour.
 + **DLIB-DEP-04** -- `DEP-CONFIG` for role, round, model, and credential settings.
 + **DLIB-DEP-05** -- Each role runs on the vendor, model and effort its settings
-  hold after activation, so the ones the master handed it (DL-289) and never the
-  values read before. An empty effort sends the vendor none.
+  hold after activation, so the ones the master handed it (DL-289), its
+  fallbacks included, and never the values read before. An empty effort sends
+  the vendor none.

 ## Observability & Audit (`OBS`)

@@ -229,7 +243,8 @@ ADR-0020; declaring is not proving, so every clause starts gray.
 | `role` | `manager` | enum | YES | Selects one of the three image identities |
 | `instance_name` | empty | string | YES | Allows an explicit fleet app identity |
 | `max_rounds` | `2` | int >= 1 <= 5 | YES | More than one live round while bounded |
-| `llm_provider` | `anthropic` | string | YES | Which vendor answers deliberation calls; switching is an operator act, never an automatic fallback, so which model reviewed an order stays answerable (DL-99) |
+| `llm_provider` | `anthropic` | string | YES | The vendor the role's first candidate is on; the master hands it over at activation, and a move to a fallback is recorded on the `LLMCall` row, so which model reviewed an order stays answerable (DL-289) |
+| `llm_fallbacks` | empty | string | YES | The later candidates the master handed over, `vendor/model/effort` joined by commas; a vendor's error answer moves the process to the next (`DLIB-FAIL-05`); empty means none |
 | `defender_model` | empty | string | YES | Proponent role model; empty resolves the provider default |
 | `challenger_model` | empty | string | YES | Opponent role model; empty resolves the provider default |
 | `judge_model` | empty | string | YES | Manager verdict model; empty resolves the provider default |
@@ -346,3 +361,9 @@ ADR-0020; declaring is not proving, so every clause starts gray.
   runs on what the master handed it at activation) and `DLIB-NEV-11` (no model
   of another vendor's family is sent); amends and proves `DLIB-OUT-02` (role
   models are the ones that answered). PARAM: `effort` defaults to empty.
++ v1.18 -- S277 / DL-289 P3 (2026-10-15). Adds `DLIB-FAIL-05` (a request a
+  vendor refuses is sent to the role's next handed-over candidate, and the
+  process stays there); amends `DLIB-FAIL-01` (an LLM request fails only with no
+  candidate left), `DLIB-OUT-02` (`llm_switches`) and `DLIB-DEP-05` (the
+  fallbacks are handed over too). PARAM: `llm_fallbacks` added, `llm_provider`
+  reworded.
```

`orchestration/laws/dispatcher/laws.md`:

```diff
diff --git a/orchestration/laws/dispatcher/laws.md b/orchestration/laws/dispatcher/laws.md
index c7c0d3f6..108ca89c 100644
--- a/orchestration/laws/dispatcher/laws.md
+++ b/orchestration/laws/dispatcher/laws.md
@@ -1,6 +1,6 @@
 # `Dispatcher` — Laws

-**Prefix:** `DSP` · **status:** LOCKED v1.4 · **Owner:** Yury Gurevich
+**Prefix:** `DSP` · **status:** LOCKED v1.5 · **Owner:** Yury Gurevich

 > Decide whether the scheduled daily graph-pull run is placed, skipped, held, or placed in degraded posture,
 > brief the operator once on each run it placed, and tell the operator when a container of the
@@ -114,10 +114,11 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 ## Prohibitions (`NEV`)

 - **DSP-OUT-09** — A brief whose last 24 hours hold an `AgentInstance` activated on an LLM candidate
-  after passing over another carries one line after the container line and before needs-you:
-  `LLM: ` then, for each distinct choice and passed-over list, the agent types sorted, ` on ` the
-  chosen `vendor/model/effort`, and in brackets `passed over ` each passed-over line, the parts
-  joined by ` · `. With no such activation there is no line.
+  with another passed over, or whose run's `DeliberationRun` names an `llm_switches` line, carries
+  one line after the container line and before needs-you: `LLM: ` then, for each distinct choice and
+  passed-over list, the agent types sorted, ` on ` the chosen `vendor/model/effort`, and in brackets
+  `passed over ` each passed-over line; then each `llm_switches` line followed by ` during the run`;
+  the parts joined by ` · `. With neither there is no line.
 - **DSP-NEV-01** — The scheduled dispatcher never writes master-owned `FleetPreflight` evidence.
 - **DSP-NEV-02** — The scheduled dispatcher never talks to the broker, never chooses tickers beyond
   the configured universe membership, and never decides what to buy, sell, size, or veto.
@@ -292,3 +293,5 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   amended for it.
 - v1.4 — S276 (DL-289, work-queue 123): the brief's LLM line. New `DSP-OUT-09`; `DSP-DEP-01` and
   `CAP` amended for the `AgentInstance` read.
+- v1.5 — S277 (DL-289 P3, work-queue 123): the brief's LLM line also names a switch during the run,
+  read from the run's `DeliberationRun`. `DSP-OUT-09` amended. No clause added.
```

### 7. The three existing test edits

S276's A1 and A3 asserted that no later candidate is probed (D1 changes that); the usage test imports the ledger wrapper from its new module. Change no other existing test.

`agents/master/tests/test_candidate_activation.py`:

```diff
diff --git a/agents/master/tests/test_candidate_activation.py b/agents/master/tests/test_candidate_activation.py
index 03a69cd7..5fe9552e 100644
--- a/agents/master/tests/test_candidate_activation.py
+++ b/agents/master/tests/test_candidate_activation.py
@@ -12,20 +12,25 @@ import pytest
 from agents.master.tests.candidate_testkit import FIRST, SECOND, world


-def test_a1_first_passing_candidate_is_handed_over_alone() -> None:
-    """MST-OUT-05 / MST-OBS-04: the first pass and its key alone reach the role."""
+def test_a1_first_passing_candidate_is_handed_over_with_its_fallback() -> None:
+    """MST-OUT-05 / MST-OBS-04: the first pass, then the later pass as a fallback."""
     fixture = world()
     reply = fixture.activate()
-    assert fixture.labels() == [FIRST]
+    assert fixture.labels() == [FIRST, SECOND]
     assert reply.config["DELIBERATOR_LLM_PROVIDER"] == "openai"
     assert reply.config["DELIBERATOR_CHALLENGER_MODEL"] == "gpt-5.5"
     assert reply.config["DELIBERATOR_EFFORT"] == "high"
+    assert reply.config["DELIBERATOR_LLM_FALLBACKS"] == SECOND
     assert "OPENAI_API_KEY" in reply.config
-    assert "ANTHROPIC_API_KEY" not in reply.config
+    assert "ANTHROPIC_API_KEY" in reply.config
     (instance,) = fixture.graph.list_nodes("AgentInstance")
     assert instance.props["llm_candidate"] == FIRST
+    assert list(instance.props["llm_fallbacks"]) == [SECOND]
     assert list(instance.props["llm_passed_over"]) == []
-    assert list(instance.props["credential_tests_passed"]) == ["openai:gpt-5.5:high"]
+    assert list(instance.props["credential_tests_passed"]) == [
+        "openai:gpt-5.5:high",
+        "anthropic:claude-opus-5:max",
+    ]


 @pytest.mark.parametrize(
@@ -66,9 +71,10 @@ def test_a3_declared_providers_candidates_go_first() -> None:
     """MST-OUT-05: the declared Anthropic provider is tried before OpenAI."""
     fixture = world(provider="anthropic")
     reply = fixture.activate()
-    assert fixture.labels() == [SECOND]
+    assert fixture.labels() == [SECOND, FIRST]
     assert reply.config["DELIBERATOR_LLM_PROVIDER"] == "anthropic"
-    assert "OPENAI_API_KEY" not in reply.config
+    assert reply.config["DELIBERATOR_LLM_FALLBACKS"] == FIRST
+    assert "OPENAI_API_KEY" in reply.config


 def test_a7_nonchoosing_type_keeps_its_single_vendor() -> None:
```

`agents/deliberator/tests/test_ledger_usage_forwarding.py`:

```diff
diff --git a/agents/deliberator/tests/test_ledger_usage_forwarding.py b/agents/deliberator/tests/test_ledger_usage_forwarding.py
index 562b3c2b..32d0ecb6 100644
--- a/agents/deliberator/tests/test_ledger_usage_forwarding.py
+++ b/agents/deliberator/tests/test_ledger_usage_forwarding.py
@@ -1,7 +1,7 @@
 """A truncated or refused completion is still billed, so it is still counted.

 Agent: deliberator
-Role: prove `_LedgerLLM` forwards the provider's usage on the stopped path as
+Role: prove `LedgerLLM` forwards the provider's usage on the stopped path as
       well as the clean one.
 External I/O: none.

@@ -16,7 +16,7 @@ from __future__ import annotations

 import pytest

-from agents.deliberator.agent import _LedgerLLM
+from agents.deliberator.turn_ledger import LedgerLLM
 from kernel import InMemoryGraphStore, LLMCompletionStoppedError
 from kernel.llm_tokens import SOURCE_ESTIMATED, SOURCE_VENDOR, LLMUsage

@@ -57,7 +57,7 @@ def _props(graph: InMemoryGraphStore, key: str) -> dict[str, object]:
 def test_a_truncated_completion_still_records_what_it_burned() -> None:
     """DLIB-OBS-05: the tokens were spent whether or not an answer came back."""
     graph = InMemoryGraphStore()
-    ledger = _LedgerLLM(
+    ledger = LedgerLLM(
         graph,
         _StoppingLLM(),
         calling_agent="deliberator-opponent",
@@ -78,7 +78,7 @@ def test_a_truncated_completion_still_records_what_it_burned() -> None:
 def test_a_provider_that_reports_no_usage_falls_back_and_says_so() -> None:
     """DLIB-OBS-05: the fake LLM in CI has no usage, and must not look measured."""
     graph = InMemoryGraphStore()
-    ledger = _LedgerLLM(
+    ledger = LedgerLLM(
         graph,
         _SilentLLM(),
         calling_agent="deliberator-opponent",
```
