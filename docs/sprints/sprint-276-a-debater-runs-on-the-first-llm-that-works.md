<!-- Agent: planning | Role: sprint handover -->
# Sprint 276 — a debater runs on the first declared LLM that works, and the brief says when it was not the first

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-276-a-debater-runs-on-the-first-llm-that-works`
**Status:** BUILT
**Version:** `0.127.00` (MINOR; lock package `0.127.0`)
**Effort:** L
**Decisions:** [DL-289](../design-log.md) (the direction, operator 2026-10-11; amendment 1 holds this sprint's ten decisions, made and measured) · [DL-282](../design-log.md) (one declared vendor, S262) · [DL-284](../design-log.md) (the two holes, found 2026-10-09) · [work-queue 123](../work-queue.md)

> **Why this bump kind.** A new capability: an LLM role gains a fallback it did not have (an ordered
> list of vendor, model and effort, chosen at activation), the master gains a declaration, two
> recorded properties and a deploy step, and the brief gains a line. MINOR.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md`, `orchestration/laws/dispatcher/laws.md` | One component's **locked constitution** | **LOCKED. Read-only during a build**, except the text the Appendix § 10 gives, applied exactly. A clause you believe is wrong is a `drift-register.md` row plus a STOP |
| `.../laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: master **`OUT`**, **`NEV`**, **`FAIL`**, **`OBS`**, **`SEC`**, **`PARAM`**;
deliberator **`OUT`**, **`NEV`**, **`DEP`**, **`PARAM`**; dispatcher **`OUT`**, **`DEP`**, **`CAP`**.

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
work, and the clause text is fixed by the planner (Appendix § 10):

- **Master v1.10 → v1.11:** new `MST-OUT-05` (an LLM role is activated on the first declared
  candidate that passes, and the record of it), `MST-NEV-08` (the start-time refusals of a
  declaration no role could run on), `MST-FAIL-08` (a candidate passed over fails nothing; none
  passing); `MST-OUT-04`, `MST-NEV-07` and `MST-OBS-04` amended; PARAM gains `llm_pack_path` and
  `llm_pack_b64`.
- **Deliberator v1.16 → v1.17:** new `DLIB-DEP-05` (a role runs on what the master handed it) and
  `DLIB-NEV-11` (no model of another vendor's family is sent); `DLIB-OUT-02` amended (role models
  are the ones that answered); PARAM `effort` defaults to empty.
- **Dispatcher v1.3 → v1.4:** new `DSP-OUT-09` (the brief's LLM line); `DSP-DEP-01` and `CAP`
  amended for the `AgentInstance` read.

You write a `test-plan.md` row per new clause citing **your** tests, widen the three amended rows'
descriptions and test lists, set each test plan's header version, and set the three books' rows in
**both** `docs/laws/ledger.md` and `docs/laws/INDEX.md` to the new version and the count the law
gate derives. 🪤 **The roll-up is derived, not declared**: on the prototype the gate derived
**master 33 / 58, deliberator 34 / 65, dispatcher 43 / 47**. Let the gate tell you yours.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/master/model_candidates.py`, `model_expansion.py`, `model_choice.py`, `credential_outcomes.py`, `credential_probe_candidate.py` (new); `credential_test.py`, `credential_probes.py`, `credential_report.py`, `credential_selection.py`, `entrypoint.py`, `pack_loading.py`, `settings.py`, `fleet_preflight.py` | `agents/master/laws/laws.md` + `test-plan.md` | `MST-OUT-04`/`05`, `MST-NEV-06`/`07`/`08`, `MST-FAIL-04`/`05`/`08`, `MST-OBS-04`, `MST-SEC-02`/`04`, `MST-DEP-04`/`05`, PARAM |
| `kernel/llm_factory.py` | `agents/deliberator/laws/laws.md` (`DLIB-NEV-11`, `DLIB-SEC-02`); `agents/operator/laws/laws.md` for `build_operator_llm` | the refusal moves into a helper both builders call; the operator's behaviour must not change |
| `agents/deliberator/entrypoint.py`, `settings.py`, `review_record.py`, `poll.py` | `agents/deliberator/laws/laws.md` + `test-plan.md` | `DLIB-OUT-02`, `DLIB-DEP-04`/`05`, `DLIB-NEV-11`, PARAM `effort` |
| `orchestration/llm_brief.py` (new), `daily_brief_text.py`, `daily_brief_facts.py`, `orchestration/Dockerfile` | `orchestration/laws/dispatcher/laws.md` + `test-plan.md` | `DSP-OUT-06`/`08`/`09`, `DSP-DEP-01`, `CAP` (`labels_read`) |
| `orchestration/packs/trading_llm.json`, `trading_credential_tests.json`, `trading_graph_vocabulary.json` | master + deliberator books; [ADR-0012](../decisions/) (pack data, never substrate code) | the master reads them as injected data only (`MST-NEV-05`, `MST-DEP-05`) |
| `infra/deploy-agents.ps1`, `scripts/switch_llm_config.py`, `scripts/switch_llm_proof.py`, `scripts/guided_turn_replay.py` | master book (`MST-OUT-04`/`05`); [DL-282](../design-log.md) | the deploy and the switch write the declared provider; the proof reads the chosen candidate |

⚠️ **The invariant: with every vendor answering, nothing the fleet does tonight changes.** The first
declared candidate is the debate's live vendor, model and effort (`openai` / `gpt-5.5` / `high`), so
every debate turn sends what it sends today, and no file the fidelity count calls a decision path
changes (`scripts/replay_fidelity_git.py::DECISION_PATHS`: `contracts/`, the scanner, analyst and PM,
`trading_tunables.json` among them). **If your change would touch any of those paths, STOP and
report.**

---

## Goal

At merge, the pack declares the LLM roles' candidates in order — `openai` / `gpt-5.5` / `high`, then
`anthropic` / `claude-opus-5` / `max` — and the master hands each deliberator, at every activation,
the first candidate whose probes pass, each probe sending that candidate's own model and effort. A
refused effort, a missing model, an empty account or an unanswered vendor moves the role to the next
candidate; the passed-over candidate is recorded on the `AgentInstance` and the `FleetPreflight`,
fails neither the activation nor the fleet check, and the next brief names it in one line. The role
reads what it was handed (its settings are read after activation), never sends an effort it was not
handed (the default effort is empty), never sends another vendor's model, and its record names the
models that actually answered. Every other agent type keeps today's single declared vendor.
Work-queue 123's two holes are closed inside this.

## Why (context)

Work-queue 123 found on 2026-10-09 that the debaters had the two holes the operator's chat had: their
default effort `max` is refused by `gpt-5.5`, and an explicit role model of another vendor would be
sent as is. Neither bites tonight only because the tunables pack sets `DELIBERATOR_EFFORT=high` and
leaves the role models empty. The decision the row waited for — a debater that cannot run either
refuses to start (no debate record, so under the binding posture every buy of the night is dropped)
or fails each order open (the buys go undebated) — the operator answered with neither, on
2026-10-11: *"Refuse to start when another LLM can do the job and miss a day's run is not a best
Idea. Let's create a list of LLM that can replace currently not working one"* ([DL-289](../design-log.md)).
The fleet has met the failure this covers: on 2026-10-06 the Anthropic account ran empty mid-week
(DL-265) and every debate that night failed open.

DL-289 split the feature in two: **the list and the choice at activation (P1, P2) — this sprint**;
the switch during the night (P3) — the next.

### Measured, 2026-10-11 and 2026-10-15 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| How `gpt-5.5` refuses an effort and a model | HTTP 400, `code: unsupported_value`, `param: reasoning_effort` (Chat Completions); HTTP 404, `code: model_not_found` | *[measured 2026-10-11, DL-289, no cost]* three requests refused before generation |
| How Anthropic refuses an effort and a model | HTTP 400 `invalid_request_error` *"output_config.effort: Input should be 'low', 'medium', 'high', 'xhigh' or 'max'"*; HTTP 404 `not_found_error` *"model: gpt-5.5"* | *[measured 2026-10-15 by the planner, no cost]* `anthropic_refusals.py` in the evidence folder, refused before generation |
| Both vendors' refusals are probe statuses | 400 and 404 are both credential failures of the probe (404 added to the deliberators' `credential_failure_statuses`, so it reads `unrecoverable`, not `unexpected`) | *[measured on the prototype]* `test_a_refused_or_unanswered_candidate_is_passed_over` |
| What runs the debate tonight | `DELIBERATOR_LLM_PROVIDER=openai` (the LLM pack, written by every full `up` since S262), `DELIBERATOR_EFFORT=high` (the tunables pack), role models empty (so `gpt-5.5`) | *[read 2026-10-15]* `orchestration/packs/trading_llm.json`, `trading_tunables.json`; the deploy script's own `Up` on a stand-in prints `DELIBERATOR_EFFORT=high DELIBERATOR_LLM_PROVIDER=openai` for all three |
| The master's probes today | A vendor probe sends a fixed model and **no effort**, so a refused effort passes activation and is met on the first debate turn | *[read]* `trading_credential_tests.json` |
| Settings are read before activation | `DeliberatorSettings()` is built before `activate_agent`, so a value ACTIVATE hands over would not reach the role | *[read]* `agents/deliberator/entrypoint.py::main` on `main` |
| An undeclared graph property is refused | `kernel/graph_vocabulary.py` raises `VocabularyError` for it; the master's write guard holds the vocabulary it was given at its last full `up` or vocabulary step | *[read]* — why the deploy sets the master's vocabulary before the retag (Blast radius) |
| The change touches no decision path | 0 of the 50 changed files | *[measured on the prototype]* `DECISION_PATHS` against `git diff origin/main` |
| The master's create call still fits | 20,069 of 32,767 characters | *[measured on the prototype]* the script's own `Up`, every call a stand-in (`llm_step_standin.ps1`) |
| The prototype's gate | `make ci` exit 0, sixteen steps: 5,031 passed, 8 skipped, 100.00 %; the dependency audit clean | *[measured 2026-10-15]* `proto-make-ci.txt`, Windows, `../ta-s276-proto` at `b3f85ee6`, no `.env` |
| Anthropic answers HTTP 200 to `max_tokens: 1` with `output_config.effort: max` on `claude-opus-5` | *[ASSUMED — not measured]* | a paid call (about $0.0002); F1b, on the operator's word. If refused, the fallback candidate could never pass, and its probe needs a larger `max_tokens` |
| OpenAI answers HTTP 200 to `reasoning_effort: high` with `max_completion_tokens: 256` | *[ASSUMED — not measured]* (a reply cut at the cap is still 200) | a paid call (under $0.01); F1b, on the operator's word |

---

## Scope — and what is deliberately NOT here

1. **The declaration (P1).** `trading_llm.json` replaces its single `provider` with an ordered
   `candidates` list (vendor, model, effort) and gains `roles`: the three deliberators and the three
   configuration keys each is handed its candidate in. The first candidate's vendor is the declared
   provider wherever one is written (the deploy's `Get-AppLlmEnv`, the switch command).
2. **The master's choice (P2).** The master loads the declaration (`MASTER_LLM_PACK_B64`), refuses to
   start on one no role could run on, keeps every vendor's probes and keys for the role types, and
   replaces each role type's vendor probes with one probe per candidate, the declared provider's
   first. At each activation and each fleet check it tries the candidates in order, hands over the
   first that passes — its vendor, model and effort under the role's keys, and that vendor's key
   alone — and records the choice and every candidate passed over.
3. **Probes that are the request.** A vendor probe declares `candidate_paths`: where in its body the
   candidate's model and effort go, so the probe sends exactly what the role will send.
4. **The deliberator reads what it was handed.** Settings are read after activation; `effort`
   defaults to empty (none sent); `build_llm` refuses another vendor's model (work-queue 123's two
   fixes); `role_models` names the models that answered, read from the run's `LLMCall` rows.
5. **The brief says so.** One `LLM:` line when an activation of the last 24 hours passed a candidate
   over; none otherwise.
6. **The deploy.** A full `up` ships the declaration on the master's create; a new narrow action,
   `deploy-agents.ps1 llm-candidates`, sets the master's vocabulary and then its declaration, for a
   fleet that is retagged rather than rebuilt. The switch command proves a choosing app by its
   candidate.
7. **The law cycle** of three books (Appendix § 10), and five named existing-test edits (§ 11).

### Out of scope (do NOT build this sprint)

- **The switch during the night (DL-289 P3).** A turn refused mid-debate still fails its order open,
  as today. That sprint will reverse S262's one-key rule (an agent holding every passing vendor's
  key); this one keeps it: an agent holds the chosen vendor's key alone.
- **The operator's chat on the list.** The operator agent type keeps today's single declared vendor
  (DL-289's open question, answered *not now*: the fleet's operator binds the fake client, and the
  dashboard chat reads the operator's local `.env`).
- **The master's own LLM.** No master role is declared; `MASTER_LLM_PROVIDER` still selects the
  single vendor for every agent type not under `roles`, and orders the role types' candidates.
- **The switch command's apply.** It still writes one provider value per app; changing a candidate's
  model or effort is the `llm-candidates` step (or a full `up`), not the switch.
- **`trading_tunables.json` and `contracts/`.** Both are decision paths. `DELIBERATOR_EFFORT=high`
  and `DELIBERATOR_LLM_PROVIDER=anthropic` stay in the tunables pack and keep being written to the
  apps' environment; ACTIVATE's config overwrites them in the process (`kernel.bootstrap._apply_config`).
- **The dashboard and the operator's surfaces.** No view of the choice beyond the graph and the brief.
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Template the probe body as text (`"{LLM_MODEL}"`).** Rejected: `json_body` is serialised once at
  parse on purpose (`credential_probe_support.json_body` says why: `format_map` on JSON text would
  have to escape every brace); paths into the parsed body need no escaping and cannot reach a header.
- **Let each deliberator probe the candidates itself.** Rejected: the master is the one process that
  tests a credential before handing it over (DL-36, `MST-NEV-06`); an agent would need every vendor's
  key first.
- **A second env value on the master for the order, written by the switch.** Rejected: the master
  already reads `MASTER_LLM_PROVIDER`, which the switch already writes; putting that vendor's
  candidates first keeps a reorder one command.
- **Hand over every passing vendor's key now.** Rejected for this sprint: nothing switches during
  the night yet (P3), so a second key would only widen what an agent holds.
- **A full `up` for the deploy.** Rejected: it reverts three live-only settings (the manager's
  240-second wait, three debates at once, the five-minute message lock); the narrow step sets only
  what the new master needs.
- **Always print the LLM line.** Rejected: the brief stays as it is on a quiet night (`DSP-OUT-08`'s
  container line is the exception because a silent sensor is itself news).

---

## The design decisions — made, and recorded in DL-289 amendment 1

The planner made them and measured them on the prototype; the builder applies them, never re-decides.

1. **D1 — the declaration's shape.** `candidates` (ordered; each `vendor`, `model`, `effort`, all
   non-empty, no repeat, the model not of another known vendor's family), `apps` (unchanged: the key
   each app is given the declared provider in), `roles` (agent type → the `vendor`, `model` and
   `effort` keys). `provider` is removed: the first candidate's vendor is it.
2. **D2 — the master holds the list; its declared provider orders it.** `MASTER_LLM_PACK_B64` (or
   `MASTER_LLM_PACK_PATH`); `LlmPlan.ordered(provider)` puts that vendor's candidates first, each
   group in declared order.
3. **D3 — the choice lives where both callers already are.** `resolve_and_test_report` runs the
   other probes, then the candidates in order (`model_choice.choose_llm`), so activation, the fleet
   check and a remediation re-test all choose the same way.
4. **D4 — what passing means.** A candidate passes when none of its required probes was refused and
   none went unanswered; the first that passes is chosen and no later one is probed. A candidate
   before it is *passed over*: one line `vendor/model/effort: reason`, neither a credential failure
   nor a fleet-check failure. With none passing, the first only unanswered is handed over unproven
   (`MST-FAIL-04` as today); with every one refused, every refusal stands and activation is refused.
5. **D5 — what is handed over.** The role's three keys name the candidate; every other vendor's key
   is withheld (S262's one-key rule kept until P3).
6. **D6 — the probe is the request.** `candidate_paths` places the candidate's model and effort in a
   copy of the declared body; the values reach the probe in two reserved configuration keys
   (`llm:model`, `llm:effort`) no environment name can spell. A role probe without them is refused at
   start (`MST-NEV-08`).
7. **D7 — the deliberator.** Settings re-read after activation (`activated_settings`); the client
   built from them (`build_role_llm`) with an empty effort sent as none; `build_llm` refuses another
   vendor's model through the same helper `build_operator_llm` uses.
8. **D8 — the record.** `role_models` reads each role's models from the run's `LLMCall` rows by the
   identity that served it, sorted and joined when replicas differ, else the resolved setting.
9. **D9 — the brief.** `DSP-OUT-09`: one line after the container line, only when an activation of
   the last 24 hours passed a candidate over.
10. **D10 — the deploy.** The full `up` ships the declaration on the master's create; the narrow
    `llm-candidates` step sets the master's vocabulary first, then the declaration, each read back;
    the retag follows it. An older image ignores both, so the order is safe both ways.

🪤 **Take no new DL number.** These decisions are DL-289 amendment 1, already in the log on `main`
(the planner's). Do not edit `docs/design-log.md`.

---

## Blast radius — measured 2026-10-15

| What | Detail |
| --- | --- |
| Files changed | 29 production files (6 new, 23 changed), 3 law books, 3 test plans, 2 roll-ups, 5 existing tests; sizes in Guardrails |
| Agents affected | master, deliberator (three roles), the dispatcher job (the brief); kernel's `llm_factory`; tooling (deploy, switch). No agent imports another (`import-linter` green on the prototype) |
| Contract change? | No |
| Graph vocabulary change? | **Yes**: `AgentInstance.llm_candidate`, `AgentInstance.llm_passed_over`, `FleetPreflight.llm_passed_over` (all master-written) |
| New env keys / tunables | `MASTER_LLM_PACK_B64` (master); master tunables `llm_pack_path`, `llm_pack_b64`; deliberator `effort` default `max` → empty |
| Deploy implication | **Not image-only.** First `deploy-agents.ps1 -Action llm-candidates` (the master's vocabulary, then `MASTER_LLM_PACK_B64`, each read back), then the image-only retag of the 16 apps and the job. 🪤 **Never the retag first:** the new master writes `FleetPreflight.llm_passed_over` on every fleet check, which the master's current vocabulary refuses |
| Rollback | Retag to `s275`. A retag does not undo the master's `MASTER_LLM_PACK_B64` or its wider vocabulary; both are ignored by the older image (an unknown setting, additive properties), so nothing else is needed. `AgentInstance` and `FleetPreflight` rows written meanwhile keep the new properties |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Plant the failing tests first** (Test plan below) and watch them fail: on the unchanged tree
   every new test file fails to import or fails. Paste the red output.
3. **Apply the Appendix § 1 to § 9 exactly.** Change nothing else in production code.
4. **Law cycle:** § 10's text exactly, then your test-plan rows and the roll-ups.
5. **The five existing-test edits** (§ 11), exactly.
6. **Prove the guards can fail (DL-70):** plant the breaks under *Traps*, one at a time, each red on
   one of your tests; restore each.
7. **Bump the version (MINOR)** in `pyproject.toml` and run `uv lock --offline`; stage `uv.lock`.
8. **`make ci` green** — every step, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Name the tests as you like; cite the clause in each docstring. Every row must be a test of yours.

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 The first candidate that passes is handed over alone | the real packs; every probe 200 | activating `deliberator-opponent` probes `openai/gpt-5.5/high` only; config `DELIBERATOR_LLM_PROVIDER=openai`, `DELIBERATOR_CHALLENGER_MODEL=gpt-5.5`, `DELIBERATOR_EFFORT=high`, `OPENAI_API_KEY` present, `ANTHROPIC_API_KEY` absent; `AgentInstance.llm_candidate` = `openai/gpt-5.5/high`, `llm_passed_over` empty (`MST-OUT-05`) |
| A2 | 🎯 A refused or unanswered first candidate is passed over | the first candidate answers 429, 400, 404, 418, 503, and a timeout (one case each) | the anthropic candidate is handed over (model `claude-opus-5`, effort `max`, its key alone); `llm_passed_over` = `openai/gpt-5.5/high: <reason>` with `unrecoverable:http_429` / `_400` / `_404`, `unexpected:http_418`, `http_503`, `TimeoutError`; no transport failure recorded, no `Escalation` (`MST-OUT-05`, `MST-FAIL-08`) |
| A3 | The declared provider's candidate goes first | `llm_provider=anthropic` | only `anthropic/claude-opus-5/max` is probed (`MST-OUT-05`) |
| A4 | None passing: the first only unanswered is handed over unproven | first 401, second 503 | anthropic handed over, its probe in `credential_tests_transport_failed`; the fleet check fails (`MST-FAIL-08`, `MST-FAIL-04`) |
| A5 | 🪤 Every candidate refused refuses the activation | first 429, second 400 | `ActivationRefused` naming both candidate probes; no `AgentInstance`; the fleet check fails with both in `failures` and `llm_passed_over` empty (`MST-FAIL-08`, `MST-NEV-06`) |
| A6 | A passed-over candidate does not fail the fleet check | first 429 | `FleetPreflight.passed` true, `failure_count` 0, `llm_passed_over` one line per role type: `<type>: openai/gpt-5.5/high: unrecoverable:http_429` (`MST-OUT-04`, `MST-FAIL-08`) |
| A7 | 🪤 A type that does not choose keeps its single vendor | activate `operator` | no candidate probe is sent, `OPENAI_API_KEY` alone, no `DELIBERATOR_*` key, no `llm_candidate` (`MST-NEV-07`) |
| A8 | The real declaration parses and orders | `trading_llm.json` | candidates `openai/gpt-5.5/high`, `anthropic/claude-opus-5/max`; the three roles and their keys; `ordered("anthropic")` puts anthropic first, each group in order; `ordered("")` is the declared order (`MST-OUT-05`) |
| A9 | 🪤 A declaration no role could run on is refused | each of: not an object; no or empty candidates; a candidate not an object; vendor `opnai`; an anthropic model under openai and the reverse; an empty or missing effort; a repeated candidate; roles not an object; a role not an object; a role key empty | `ValueError` naming the cause (`MST-NEV-08`); a model of no known family is accepted |
| A10 | 🪤 Expansion refusals | the real packs less: the manager's anthropic probe; every probe's `takes_candidate`; the anthropic key in the secret map; no secret map | start refused naming the agent type and candidate, `has no anthropic probe`, `without candidate_paths`, `not granted ANTHROPIC_API_KEY` / `OPENAI_API_KEY` (`MST-NEV-08`) |
| A11 | Expansion order and selection | the real packs, provider openai | each role type: `openai:gpt-5.5:high` then `anthropic:claude-opus-5:max`; six candidate probes, each with a role; the operator's single `openai` probe kept; each role type keeps both keys, the operator one (`MST-OUT-05`, `MST-NEV-07`); no pack means no change |
| A12 | A candidate's probe carries its model and effort | an anthropic probe with `candidate_paths`, a candidate's config | the body is `{"max_tokens":1,"model":"claude-opus-5","output_config":{"effort":"max"}}` with a JSON content type; without a candidate the declared bytes; the declared body is not changed by a candidate (`MST-OUT-05`) |
| A13 | 🪤 Malformed `candidate_paths` are refused | not an object; one field; an extra field; a path not a list, empty, or holding an empty key; no `json_body`; a path through a scalar; a non-object body | `ValueError` (`MST-NEV-08`) |
| A14 | The committed packs start a master as the deploy delivers them | every pack as a base64 setting | `build_app` succeeds with the two candidate probe names (`MST-NEV-08`) |
| A15 | Settings are read after the master's hand-over | env anthropic/max; a stand-in `activate` that sets openai, `gpt-5.5`, `high` | the returned settings are openai, `high`, challenger model `gpt-5.5`; the stand-in was called with the role's identity and key (`DLIB-DEP-05`) |
| A16 | The role's client is built on what it was handed | proponent, anthropic, `claude-opus-5`, `xhigh` | an `AnthropicLLMClient` with that model and effort (`DLIB-DEP-05`) |
| A17 | 🪤 An empty effort sends none | the default settings, each vendor | `effort == ""`; OpenAI's client gets `None`, Anthropic's `max` (`DLIB-DEP-05`) |
| A18 | 🪤 Another vendor's model is never sent | `build_llm` openai + `claude-opus-5`, anthropic + `gpt-5.5` | `ModelProviderMismatchError` (`DLIB-NEV-11`) |
| A19 | The record names the models that answered | proponent on anthropic, opponent and manager on openai, a real review | `role_models` = defender `claude-opus-5`, challenger `gpt-5.5`, judge `gpt-5.5` (`DLIB-OUT-02`) |
| A20 | Two models on one role are both named | three `LLMCall` rows of the proponent (two models), one unknown key | defender `claude-opus-5, gpt-5.5`; the others fall back to the setting; no graph equals no rows (`DLIB-OUT-02`) |
| A21 | 🪤 No LLM line on a quiet night | activations with no passed-over list, an empty one, a non-LLM type | `llm_line` is `None` (`DSP-OUT-09`) |
| A22 | The LLM line's words | two replicas and the manager on one fallback; a second choice; one activation 25 hours old; one with no `started_at` | exactly `LLM: deliberator-manager, deliberator-opponent on anthropic/claude-opus-5/max (passed over openai/gpt-5.5/high: unrecoverable:http_429)`; two parts joined by ` · `; the old and the undated left out (`DSP-OUT-09`) |
| A23 | The line's place | full and RED briefs with both lines | container line, then LLM line, then needs-you (`DSP-OUT-09`) |
| A24 | A real fire carries the line | the brief fixture pair plus a passed-over activation | the sent brief's second-to-last line starts `LLM: deliberator-manager on anthropic/claude-opus-5/max` (`DSP-OUT-09`) |
| A25 | The deploy ships the declaration | the deploy script's text | the master's create list holds `(Get-MasterLlmPackEnv)`, whose getter reads `trading_llm.json` into `MASTER_LLM_PACK_B64=`, named once; the four create packs plus the 5,000 reserve fit 32,767 (`MST-OUT-05`) |
| A26 | The narrow step's order | the deploy script's text | `Set-AppVocabulary "master"` before `Get-MasterLlmPackEnv`; the pack only `if ($vocabOk)`; it returns both; `llm-candidates` is in `ValidateSet` and throws when the step fails (`MST-OUT-05`) |
| A27 | The declared provider is the first candidate's vendor | the committed pack; the deploy script | the switch reads `openai`; the script writes `@($pack.candidates)[0].vendor` and never `$pack.provider` (`MST-OUT-05`) |
| A28 | The switch proves a choosing app by its candidate | a passing fleet check and one manager activation, chosen openai, then anthropic | no missing term, then `deliberator-manager: vendor probe not passed or other vendor probe declared` (`MST-OUT-05`) |

---

## Success factors

- [ ] **F0 (planner, done before handover):** the prototype passes `make ci` (exit 0, 5,031 passed,
      100.00 %) and its 32 planted breaks each turn the planner's tests red (`breaks_on_prototype.txt`).
- [x] The Appendix applied exactly: the 29 production files equal the prototype's blobs
      (`prototype_blobs.txt`), the three `laws.md` equal § 10.
- [x] A1–A28 pass; each docstring cites its clause.
- [x] Every break under *Traps* planted one at a time turns one of your tests red, then restored.
- [x] No decision-path file changed (`DECISION_PATHS` against `git diff origin/main` prints none).
- [x] Law cycle: three books, three test plans, both roll-ups at the derived counts.
- [x] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage, redirected to a file.
- [ ] **F1a (planner, after merge, no cost):** the deploy script's own `llm-candidates` step and `Up`
      on a stand-in `az` (`llm_step_standin.ps1`): vocabulary then pack, the pack decoding to
      `trading_llm.json` byte for byte, a failed vocabulary sending no pack; the master's create
      carrying `MASTER_LLM_PACK_B64` and `MASTER_LLM_PROVIDER=openai` within 32,767 characters.
- [ ] **F1b (planner, after merge, paid, about $0.01 in all, on the operator's word):** one real
      probe per candidate through the master's own probe runner on merged `main`: each answers 200.
- [ ] **F2 (after the deploy, at the first weekday fire):** the three deliberators' new
      `AgentInstance` rows hold `llm_candidate` `openai/gpt-5.5/high` and an empty `llm_passed_over`;
      the fleet checks pass with `llm_passed_over` empty; the night's `DeliberationRun` (if a buy is
      debated) names `gpt-5.5` for all three roles; the brief has no `LLM:` line; no
      `VocabularyError` fault.

---

## Traps

🪤 **The in-memory graph returns a list property as a tuple.** A reader that checks
`isinstance(x, list)` reads nothing in tests and everything on Postgres; the prototype's brief line
did exactly that until its own test caught it (`llm_brief.py` accepts both). Compare graph props with
`list(...)` in your asserts.
🪤 **`agents/**/llm_*.py` is reserved for vendor adapters** (`tests/test_llm_adapter_ownership.py`).
The master's new modules are `model_*.py` for that reason; do not rename them.
🪤 **The deploy script is a raw file.** Edit it with a tool that writes bytes; a Python string with
`\t` in a Windows path writes a tab (the planner's prototype did, once).
🪤 **The new master's first fleet check writes `llm_passed_over`.** The vocabulary must reach the
master before the image; that is a deploy concern (Blast radius), not yours, but do not "fix" it by
writing the property only when non-empty: the brief and the switch read the empty list.
🪤 **Settings read before activation are stale.** `activated_settings` re-reads them; `main` must
use what it returns for everything after the EHLO.
🪤 **An empty effort sent to OpenAI is refused.** `build_role_llm` passes `settings.effort or None`.
🪤 **Do not touch `trading_tunables.json`** to remove `DELIBERATOR_EFFORT`: it is a decision path,
and ACTIVATE's config overwrites the value in the process anyway.
🪤 **The operator's two probes keep no `candidate_paths`**: the operator does not choose. Only the six
deliberator probes carry them, and `404` joined only their `credential_failure_statuses`.
🪤 **`ruff format` grows test files**; measure sizes after formatting.

**The breaks — plant one at a time; each must turn one of your tests red; restore each:**

| # | File | Break |
| --- | --- | --- |
| B1 | `agents/master/model_choice.py` | remove `if outcomes.proven: break` (every candidate probed) |
| B2 | same | drop the fallback to the first only-unanswered candidate |
| B3 | same | `config.pop(key, None)` → `pass` (the other vendor's key handed over) |
| B4 | same | the effort key set to the candidate's model |
| B5 | same | the chosen candidate listed among the passed over |
| B6 | `credential_outcomes.py` | `proven` ignores transport failures |
| B7 | `credential_test.py` | the report gets `llm_passed_over=()` |
| B8 | `credential_report.py` | `llm_candidate` not written |
| B9 | `fleet_preflight.py` | passed-over lines not collected |
| B10 | `model_candidates.py` | `ordered` returns the declared order |
| B11 | same | the foreign-model refusal disabled |
| B12 | same | the repeat refusal disabled |
| B13 | `model_expansion.py` | the granted-key refusal disabled |
| B14 | same | the `candidate_paths` refusal disabled |
| B15 | `credential_probes.py` | the candidate body never built |
| B16 | `credential_probe_candidate.py` | no `deepcopy` of the declared body |
| B17 | `credential_selection.py` | role types lose the other vendor's key at start |
| B18 | `kernel/llm_factory.py` | `build_llm` no longer refuses a foreign model |
| B19 | `agents/deliberator/entrypoint.py` | `activated_settings` returns the settings it was given |
| B20 | same | `effort=settings.effort` (an empty effort sent) |
| B21 | `review_record.py` | `LLMCall` rows ignored |
| B22 | `orchestration/llm_brief.py` | a tuple list not read |
| B23 | same | no 24-hour window |
| B24 | `daily_brief_text.py` | the LLM line not composed |
| B25 | `orchestration/packs/trading_llm.json` | the two candidates swapped |
| B26 | `trading_credential_tests.json` | the three anthropic probes' `candidate_paths` removed |
| B27 | `infra/deploy-agents.ps1` | `(Get-MasterLlmPackEnv)` dropped from the create |
| B28 | same | the vocabulary step removed from `Enable-LlmCandidates` |
| B29 | `scripts/switch_llm_proof.py` | the `llm_candidate` branch disabled |
| B30 | `scripts/switch_llm_config.py` | the last candidate's vendor declared |
| B31 | `orchestration/Dockerfile` | `llm_brief.py` not copied (an existing test goes red) |
| B32 | `trading_graph_vocabulary.json` | `llm_candidate` undeclared (an existing test goes red) |

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Sizes on the prototype (main → prototype): `agents/master/credential_probes.py` **173 → 187**,
  `agents/master/entrypoint.py` **173 → 179**, `agents/master/settings.py` **157 → 171**,
  `agents/master/credential_test.py` **158 → 141**, `agents/master/fleet_preflight.py` **141 → 147**,
  `agents/deliberator/poll.py` **188 → 188**, `agents/deliberator/settings.py` **164 → 169**,
  `agents/deliberator/entrypoint.py` **123 → 149**, `agents/deliberator/review_record.py`
  **127 → 145**, `orchestration/daily_brief_text.py` **182 → 183**,
  `orchestration/daily_brief_facts.py` **168 → 170**, `kernel/llm_factory.py` **130 → 138**,
  `scripts/guided_turn_replay.py` **174 → 174**; new: `credential_outcomes.py` **107**,
  `model_candidates.py` **104**, `model_expansion.py` **89**, `model_choice.py` **75**,
  `credential_probe_candidate.py` **69**, `orchestration/llm_brief.py` **47**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- Faults, not silent failure. Credential evidence never holds a secret value (`MST-SEC-04`).
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.**
- Version bump MINOR, `uv.lock` staged with it.
- A worktree has **no `.env`**; nothing here needs one. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. Review: the CodeQL set-diff against the last merged branch
   (`sprint-275-the-operator-hears-when-a-container-fails`, 133 open, 0 errors); the 29 blobs against
   `prototype_blobs.txt`; the planner's tests (`planner_tests/`) on the built code; the 32 breaks
   against the builder's tests alone.
2. `make gate-ran` from the worktree whose `HEAD` is the merged commit; merge; tag; push.
3. F1a at no cost; F1b on the operator's word.
4. **Deploy, the operator's call:** `deploy-agents.ps1 -Action llm-candidates`, then the image-only
   retag (deploy skill), rollback `s275`. Then F2 at the first weekday fire; work-queue 123 closes on
   F2. The deploy skill gains the `llm-candidates` step in the docs commit after the deploy.

---

## Handover — paste this to Codex

```text
You are building Sprint 276 in the worktree ../ta-s276, on the branch
sprint-276-a-debater-runs-on-the-first-llm-that-works. Never work on main.

Read docs/sprints/sprint-276-a-debater-runs-on-the-first-llm-that-works.md, whole, before anything
else. It is the spec, and its bottom sections are your handback. The Appendix holds the production
code and the law text, which you apply exactly; your work is the tests, the law rows, the five named
test edits, the bump and the evidence.

In order:
1. Read agents/master/laws/laws.md and test-plan.md, agents/deliberator/laws/laws.md and
   test-plan.md, orchestration/laws/dispatcher/laws.md and test-plan.md, docs/laws/conventions.md
   and docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any code.
2. Write the tests of the Test plan (A1 to A28) in new test files (agents/master/tests/,
   agents/deliberator/tests/, orchestration/tests/, tests/), each docstring citing its clause. Run
   them on the unchanged tree and paste the red output into the Closeout.
3. Apply the Appendix sections 1 to 9 exactly: six new modules (agents/master/model_candidates.py,
   model_choice.py, model_expansion.py, credential_outcomes.py, credential_probe_candidate.py,
   orchestration/llm_brief.py) and the diffs to 23 existing files. Change nothing else in
   production code. Do not rename the model_*.py modules: agents/**/llm_*.py is reserved.
4. Apply section 10 to the three laws.md files exactly. Then add a test-plan row per new clause
   citing your tests, widen the amended clauses' rows (MST-OUT-04, MST-NEV-07, MST-OBS-04,
   DLIB-OUT-02, DSP-DEP-01 where it has a row) with your tests, set each test plan's header version,
   and set the three books' rows in docs/laws/INDEX.md and docs/laws/ledger.md to the new version and
   the count the law gate derives (master 33 / 58, deliberator 34 / 65, dispatcher 43 / 47 on the
   prototype).
5. Apply section 11 to the five existing test files, exactly. Change no other existing test.
6. Plant the breaks B1 to B32 under Traps one at a time; each must turn at least one of your tests
   red; restore each before the next. Record each in the Closeout.
7. Bump the version (MINOR) in pyproject.toml, run uv lock --offline, stage uv.lock. Run make ci
   redirected to a file and read the file.
8. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in the sprint's
   row of docs/sprints/README.md. Commit on the branch if your sandbox lets you write the
   repository's git directory; if not, leave the tree uncommitted and say so. Do not edit
   docs/STATE.md, docs/design-log.md or docs/work-queue.md.

DO NOT: run infra/deploy-agents.ps1, pwsh or any az command; reach the network or any LLM vendor;
change contracts/, orchestration/packs/trading_tunables.json or any other decision-path file;
add or reword a law clause beyond section 10; change any existing test but the five section 11
names; reorder the vocabulary's lists; use noqa; let any module reach 200 lines; measure make ci
through a pipe.

Traps (the spec's Traps section has them all): the in-memory graph returns lists as tuples, so
compare with list(...); agents/**/llm_*.py is reserved for vendor adapters; the deploy script is
edited byte for byte (a "\t" in a Python string becomes a tab); FleetPreflight writes
llm_passed_over even when it is empty, and must; settings read before activation are stale; an
empty effort is sent as None; the operator's probes carry no candidate_paths; ruff format grows test
files, so measure sizes after formatting.

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
| Master declaration, expansion, probes, choice, activation and fleet check | `agents/master/laws/laws.md` LOCKED v1.10 and its whole `test-plan.md` | `MST-OUT-04`, planned `MST-OUT-05`; `MST-NEV-06`/`07`, planned `MST-NEV-08`; `MST-FAIL-04`/`05`, planned `MST-FAIL-08`; `MST-OBS-04`; `MST-SEC-02`/`04`; `MST-DEP-04`/`05`; PARAM | Yes: exercise real pack data with injected transports and secret-store stand-ins; prove the chosen key alone and distinguish activation's unanswered allowance from fleet readiness. `MST-SEC-02` remains gray as a whole, as do `MST-SEC-03`, `MST-DEP-02` and `MST-OBS-03`; no live dependency proof is claimed. |
| Deliberator activation, clients and model records | `agents/deliberator/laws/laws.md` LOCKED v1.16 and its whole `test-plan.md` | `DLIB-OUT-02`; planned `DLIB-DEP-05`/`DLIB-NEV-11`; `DLIB-DEP-04`; `DLIB-SEC-02`; PARAM | Yes: test settings after ACTIVATE, empty effort, foreign-family refusal, and run-owned `LLMCall` identities through a real review. `DLIB-DEP-03` and `DLIB-SEC-01` remain gray; local stand-ins prove no vendor availability. |
| Shared factory's operator compatibility | `agents/operator/laws/laws.md` LOCKED v1.10 and its whole `test-plan.md` | `OPR-DEP-01`, `OPR-SEC-01` | Keep the operator's selected-provider and foreign-family refusal behavior unchanged; its probes carry no candidate paths. |
| Brief line, facts, composition and image | `orchestration/laws/dispatcher/laws.md` LOCKED v1.3 and its whole `test-plan.md` | `DSP-OUT-06`/`08`, planned `DSP-OUT-09`; `DSP-DEP-01`; CAP | Yes: assert tuple-backed graph lists, the 24-hour window, deduplication, exact wording and placement, and a real fire with an injected Telegram port. `DSP-DEP-01` remains gray: these reads do not prove its clock/calendar/universe dependency envelope. |
| Packs, deploy and switch tooling | Master and deliberator books above; `docs/decisions/0012-platform-domain-separation.md` | `MST-OUT-04`, planned `MST-OUT-05`; `MST-NEV-05`/`07`; `MST-DEP-05`; `DLIB-DEP-04`; PARAM | Preserve injected pack data, vocabulary list order, and exact Appendix bytes. Deploy tests inspect text only; no deploy, PowerShell Core, Azure, network or vendor invocation. |
| Law amendment and evidence discipline | Whole `docs/laws/conventions.md` and whole `docs/laws/drift-register.md`; `docs/laws/INDEX.md` | Conventions §§2–4, 7, 7a, 9–10; DRIFT-058/059/075/091/105/113/114/115 | Apply only §10's authorized law text; faithful amended summaries, cited tests and gate-derived counts. Keep supporting gray rows gray. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No contract changes; yes, the six new guarantees require the three §10 amendments, new test-plan rows and synchronized derived roll-ups in this unit of work. D1–D10 and the rejected alternatives are already fixed by DL-289 amendment 1; no new design decision or DL number is needed.

**Contradictions found between a law and this spec:** None found outside the explicit §10 amendment. The current single-provider selection is deliberately widened for declared roles only; the operator and in-flight debate behavior retain their existing selection. Read completed on 2026-10-15 before any code change, in `C:/Users/yury_/Downloads/project/ta-s276`, clean branch `sprint-276-a-debater-runs-on-the-first-llm-that-works`, initial HEAD `f1598b45fe924c0baaa9a9f6eff64a6733ff4bd2`; local `origin/main` `38a1c0b79af6505160c15c4587f10c39e577afa4`, not fetched. No `.env` present. Sprint evidence stays here; the three prohibited trackers are untouched.

**Laws found silent where a decision was needed:** The pre-amendment books do not declare the candidate choice, unrunnable-declaration refusals, passed-over outcomes, post-activation settings, foreign-family guard or brief line. §10 supplies their decided text; no additional unresolved silence was found.

**Clauses that were ⬜ and are now proven:** At the pre-code checkpoint proof was not done. Now the six newly declared clauses are proven: `MST-OUT-05`, `MST-NEV-08`, `MST-FAIL-08`, `DLIB-DEP-05`, `DLIB-NEV-11`, `DSP-OUT-09`. The five amended rows are widened and re-proven where previously green; `DSP-DEP-01` and all other supporting gray rows remain gray. Derived counts: master 33 / 58, deliberator 34 / 65, dispatcher 43 / 47.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_first_passing_candidate_is_handed_over_alone` | `agents/master/tests/test_candidate_activation.py` | PASS | `MST-OBS-04`, `MST-OUT-05` |
| A2 | `test_a2_refused_or_unanswered_candidate_is_passed_over` | `agents/master/tests/test_candidate_activation.py` | PASS | `MST-FAIL-08`, `MST-OBS-04`, `MST-OUT-05` |
| A3 | `test_a3_declared_providers_candidates_go_first` | `agents/master/tests/test_candidate_activation.py` | PASS | `MST-OUT-05` |
| A4 | `test_a4_first_only_unanswered_candidate_is_handed_over_unproven` | `agents/master/tests/test_candidate_fleet.py` | PASS | `MST-FAIL-04`, `MST-FAIL-08` |
| A5 | `test_a5_every_candidate_refused_refuses_activation` | `agents/master/tests/test_candidate_fleet.py` | PASS | `MST-FAIL-08`, `MST-NEV-06` |
| A6 | `test_a6_passed_over_candidate_does_not_fail_fleet` | `agents/master/tests/test_candidate_fleet.py` | PASS | `MST-FAIL-08`, `MST-OUT-04` |
| A7 | `test_a7_nonchoosing_type_keeps_its_single_vendor` | `agents/master/tests/test_candidate_activation.py` | PASS | `MST-NEV-07` |
| A8 | `test_a8_real_declaration_parses_and_orders` | `agents/master/tests/test_candidate_declaration.py` | PASS | `MST-OUT-05` |
| A9 | `test_a9_unrunnable_declaration_is_refused`; `test_a9_unknown_model_family_is_the_vendors_to_judge` | `agents/master/tests/test_candidate_declaration.py` | PASS | `MST-NEV-08` |
| A10 | `test_a10_expansion_refuses_unrunnable_roles` | `agents/master/tests/test_candidate_expansion.py` | PASS | `MST-NEV-08` |
| A11 | `test_a11_expansion_preserves_roles_keys_and_nonchoosing_probe` | `agents/master/tests/test_candidate_expansion.py` | PASS | `MST-NEV-07`, `MST-OUT-05` |
| A12 | `test_a12_candidate_probe_carries_own_model_and_effort` | `agents/master/tests/test_candidate_probe.py` | PASS | `MST-OUT-05` |
| A13 | `test_a13_malformed_candidate_paths_are_refused`; `test_a13_missing_body_and_scalar_paths_are_refused` | `agents/master/tests/test_candidate_probe.py` | PASS | `MST-NEV-08` |
| A14 | `test_a14_base64_packs_start_master_as_deploy_delivers_them` | `agents/master/tests/test_candidate_expansion.py` | PASS | `MST-NEV-08` |
| A15 | `test_a15_settings_are_read_after_activation` | `agents/deliberator/tests/test_activated_candidate.py` | PASS | `DLIB-DEP-05` |
| A16 | `test_a16_role_client_uses_handed_over_candidate` | `agents/deliberator/tests/test_activated_candidate.py` | PASS | `DLIB-DEP-05` |
| A17 | `test_a17_empty_effort_sends_none` | `agents/deliberator/tests/test_activated_candidate.py` | PASS | `DLIB-DEP-05` |
| A18 | `test_a18_foreign_vendor_model_is_refused` | `agents/deliberator/tests/test_activated_candidate.py` | PASS | `DLIB-NEV-11` |
| A19 | `test_a19_review_names_the_models_that_answered` | `agents/deliberator/tests/test_answered_models.py` | PASS | `DLIB-OUT-02` |
| A20 | `test_a20_multiple_models_on_one_role_are_sorted_and_deduplicated` | `agents/deliberator/tests/test_answered_models.py` | PASS | `DLIB-OUT-02` |
| A21 | `test_a21_quiet_night_has_no_llm_line` | `orchestration/tests/test_llm_brief_candidates.py` | PASS | `DSP-OUT-09` |
| A22 | `test_a22_llm_line_groups_replicas_and_filters_old_or_undated` | `orchestration/tests/test_llm_brief_candidates.py` | PASS | `DSP-DEP-01`, `DSP-OUT-09` |
| A23 | `test_a23_llm_line_follows_container_before_needs_you` | `orchestration/tests/test_llm_brief_candidates.py` | PASS | `DSP-OUT-09` |
| A24 | `test_a24_real_fire_carries_the_candidate_line` | `orchestration/tests/test_llm_brief_candidates.py` | PASS | `DSP-DEP-01`, `DSP-OUT-09` |
| A25 | `test_a25_master_create_ships_candidate_declaration`; `test_a25_image_and_vocabulary_deliver_the_choice` | `tests/test_candidate_delivery.py` | PASS | `DSP-OUT-09`, `MST-OUT-05` |
| A26 | `test_a26_narrow_step_sets_vocabulary_before_pack` | `tests/test_candidate_delivery.py` | PASS | `MST-OUT-05` |
| A27 | `test_a27_declared_provider_is_first_candidates_vendor`; `test_a27_switch_refuses_a_missing_or_malformed_first_candidate` | `tests/test_candidate_delivery.py` | PASS | `MST-OUT-05` |
| A28 | `test_a28_switch_proves_a_choosing_app_by_its_candidate` | `tests/test_candidate_delivery.py` | PASS | `MST-OUT-05` |

**Tests added beyond the plan:** A25's image/vocabulary packaging guard also supplies builder-owned red proof for B31/B32; A27's three malformed-first-candidate cases guard the switch loader's refusals. The nine new test modules contain 67 passing cases, plus one shared fixture module. No other existing test was edited.

---

## Closeout — evidence

**Status:** BUILT — local build proof only; see the CI and not-met records below.

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/Downloads/project/ta-s276`, branch `sprint-276-a-debater-runs-on-the-first-llm-that-works`; no `.env`. CI used a stripped child environment, `UV_OFFLINE=1`, `PIP_NO_INDEX=1` and an external socket guard refusing non-local connections. No vendor, Azure, deploy or external network call was made.

**Result:** All 29 production blobs match both the Appendix and local prototype `b3f85ee6`; all three law blobs and five existing-test blobs match the supplied diff IDs. A1–A28 pass (67 cases); all B1–B32 turn a builder test red and are restored byte for byte; the post-guard run passes 69 cases including the two existing packaging guards. The three law test plans and both roll-ups pass the law gate at its derived counts. MINOR `0.126.00` → `0.127.00`; `uv lock --offline` succeeds and its staged diff changes only the package version. Full-suite and CI results are recorded below, with no remote or live claim.

**Files changed:** 56 scoped files: 29 production files (six new), three exact law amendments, three law test plans, two roll-ups, five exact existing-test edits, nine new test modules and their helper, `pyproject.toml`, `uv.lock`, this handback and the sprint README row. No decision-path file, prohibited tracker, other existing test, secret baseline or `trading_tunables.json` changed.

**Design decisions:** recorded as [DL-289](../design-log.md) amendment 1 by the planner; nothing new.

**Proof — the red run first:** Production files unchanged (`git diff --name-only` named only this spec); nine new test files. Command: `uv run --offline pytest --no-cov --continue-on-collection-errors <the nine new test files>`; exit 1. Full output:

```text
============================= test session starts =============================
collected 2 items / 8 errors

agents\deliberator\tests\test_answered_models.py FF                      [100%]

=================================== ERRORS ====================================
____ ERROR collecting agents/deliberator/tests/test_activated_candidate.py ____
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s276\agents\deliberator\tests\test_activated_candidate.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\deliberator\tests\test_activated_candidate.py:14: in <module>
    from agents.deliberator.entrypoint import activated_settings, build_role_llm
E   ImportError: cannot import name 'activated_settings' from 'agents.deliberator.entrypoint' (C:\Users\yury_\Downloads\project\ta-s276\agents\deliberator\entrypoint.py)
______ ERROR collecting agents/master/tests/test_candidate_activation.py ______
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s276\agents\master\tests\test_candidate_activation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\master\tests\test_candidate_activation.py:10: in <module>
    from agents.master.tests.candidate_testkit import FIRST, SECOND, world
agents\master\tests\candidate_testkit.py:20: in <module>
    from agents.master.model_candidates import load_llm_plan
E   ModuleNotFoundError: No module named 'agents.master.model_candidates'
_____ ERROR collecting agents/master/tests/test_candidate_declaration.py ______
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s276\agents\master\tests\test_candidate_declaration.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\master\tests\test_candidate_declaration.py:12: in <module>
    from agents.master.model_candidates import load_llm_plan, parse_llm_plan
E   ModuleNotFoundError: No module named 'agents.master.model_candidates'
______ ERROR collecting agents/master/tests/test_candidate_expansion.py _______
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s276\agents\master\tests\test_candidate_expansion.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\master\tests\test_candidate_expansion.py:15: in <module>
    from agents.master.model_candidates import load_llm_plan
E   ModuleNotFoundError: No module named 'agents.master.model_candidates'
________ ERROR collecting agents/master/tests/test_candidate_fleet.py _________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s276\agents\master\tests\test_candidate_fleet.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\master\tests\test_candidate_fleet.py:11: in <module>
    from agents.master.tests.candidate_testkit import FIRST, SECOND, world
agents\master\tests\candidate_testkit.py:20: in <module>
    from agents.master.model_candidates import load_llm_plan
E   ModuleNotFoundError: No module named 'agents.master.model_candidates'
________ ERROR collecting agents/master/tests/test_candidate_probe.py _________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s276\agents\master\tests\test_candidate_probe.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
agents\master\tests\test_candidate_probe.py:12: in <module>
    from agents.master.credential_probe_candidate import (
E   ModuleNotFoundError: No module named 'agents.master.credential_probe_candidate'
______ ERROR collecting orchestration/tests/test_llm_brief_candidates.py ______
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s276\orchestration\tests\test_llm_brief_candidates.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
orchestration\tests\test_llm_brief_candidates.py:14: in <module>
    from orchestration.llm_brief import llm_line
E   ModuleNotFoundError: No module named 'orchestration.llm_brief'
______________ ERROR collecting tests/test_candidate_delivery.py ______________
ImportError while importing test module 'C:\Users\yury_\Downloads\project\ta-s276\tests\test_candidate_delivery.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\miniconda3\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_candidate_delivery.py:14: in <module>
    from scripts.switch_llm_config import declared_provider, load_pack
E   ImportError: cannot import name 'declared_provider' from 'scripts.switch_llm_config' (C:\Users\yury_\Downloads\project\ta-s276\scripts\switch_llm_config.py)
================================== FAILURES ===================================
_______________ test_a19_review_names_the_models_that_answered ________________
agents\deliberator\tests\test_answered_models.py:51: in test_a19_review_names_the_models_that_answered
    assert run.props["role_models"] == {
E   AssertionError: assert mappingproxy(...': 'gpt-5.5'}) == {'defender': ...e': 'gpt-5.5'}
E
E     Omitting 2 identical items, use -vv to show
E     Differing items:
E     {'defender': 'gpt-5.5'} != {'defender': 'claude-opus-5'}
E     Use -v to get more diff
______ test_a20_multiple_models_on_one_role_are_sorted_and_deduplicated _______
agents\deliberator\tests\test_answered_models.py:82: in test_a20_multiple_models_on_one_role_are_sorted_and_deduplicated
    assert role_models(settings, graph, keys) == expected
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: role_models() takes 1 positional argument but 3 were given
=========================== short test summary info ===========================
ERROR agents/deliberator/tests/test_activated_candidate.py
ERROR agents/master/tests/test_candidate_activation.py
ERROR agents/master/tests/test_candidate_declaration.py
ERROR agents/master/tests/test_candidate_expansion.py
ERROR agents/master/tests/test_candidate_fleet.py
ERROR agents/master/tests/test_candidate_probe.py
ERROR orchestration/tests/test_llm_brief_candidates.py
ERROR tests/test_candidate_delivery.py
FAILED agents/deliberator/tests/test_answered_models.py::test_a19_review_names_the_models_that_answered
FAILED agents/deliberator/tests/test_answered_models.py::test_a20_multiple_models_on_one_role_are_sorted_and_deduplicated
======================== 2 failed, 8 errors in 12.71s =========================
```

**Proof — the green run:** `uv run --offline pytest --no-cov <nine new files> <two existing packaging guards>`, exit 0:

```text
============================= test session starts =============================
collected 69 items

agents\deliberator\tests\test_activated_candidate.py ......              [  8%]
agents\deliberator\tests\test_answered_models.py ..                      [ 11%]
agents\master\tests\test_candidate_activation.py .........               [ 24%]
agents\master\tests\test_candidate_declaration.py ..................     [ 50%]
agents\master\tests\test_candidate_expansion.py ......                   [ 59%]
agents\master\tests\test_candidate_fleet.py ...                          [ 63%]
agents\master\tests\test_candidate_probe.py .........                    [ 76%]
orchestration\tests\test_llm_brief_candidates.py .....                   [ 84%]
tests\test_candidate_delivery.py .........                               [ 97%]
tests\test_dispatch_scheduled_run.py .                                   [ 98%]
tests\test_graph_vocabulary_properties.py .                              [100%]

============================= 69 passed in 8.44s ==============================
```

Full-suite proof from the redirected CI log:

```text
TOTAL                                                           21231      0   4536      0  100.00%
========= 5031 passed, 8 skipped, 2470 warnings in 432.53s (0:07:12) ==========
```

**Guards planted:** Each specified break was planted alone, the named test run exited 1, and the original file's SHA256 was restored before the next plant. B31/B32 also turn their existing guards red; those guards pass on the restored tree. Actual runner output:

```text
B01: exit 1; RED; restored SHA256 d16c4f05396c95ba16a846cd883eff348ccd7b8f99d45e2295ae63bdcd4f4ae2; FAILED agents/master/tests/test_candidate_activation.py::test_a1_first_passing_candidate_is_handed_over_alone
B02: exit 1; RED; restored SHA256 d16c4f05396c95ba16a846cd883eff348ccd7b8f99d45e2295ae63bdcd4f4ae2; FAILED agents/master/tests/test_candidate_fleet.py::test_a4_first_only_unanswered_candidate_is_handed_over_unproven
B03: exit 1; RED; restored SHA256 d16c4f05396c95ba16a846cd883eff348ccd7b8f99d45e2295ae63bdcd4f4ae2; FAILED agents/master/tests/test_candidate_activation.py::test_a1_first_passing_candidate_is_handed_over_alone
B04: exit 1; RED; restored SHA256 d16c4f05396c95ba16a846cd883eff348ccd7b8f99d45e2295ae63bdcd4f4ae2; FAILED agents/master/tests/test_candidate_activation.py::test_a1_first_passing_candidate_is_handed_over_alone
B05: exit 1; RED; restored SHA256 d16c4f05396c95ba16a846cd883eff348ccd7b8f99d45e2295ae63bdcd4f4ae2; FAILED agents/master/tests/test_candidate_activation.py::test_a1_first_passing_candidate_is_handed_over_alone
B06: exit 1; RED; restored SHA256 b9cc7de3d1917aaecfcab9afef3fbc3eac50b4cfc6105c62b97bd1d784e8f9fb; FAILED agents/master/tests/test_candidate_activation.py::test_a2_refused_or_unanswered_candidate_is_passed_over[503-http_503]; FAILED agents/master/tests/test_candidate_activation.py::test_a2_refused_or_unanswered_candidate_is_passed_over[answer5-TimeoutError]
B07: exit 1; RED; restored SHA256 3a83cb4a1bc2383d3aec9ca58bf9d6f62e96435962561ca7461bb4013b98cf63; FAILED agents/master/tests/test_candidate_activation.py::test_a2_refused_or_unanswered_candidate_is_passed_over[429-unrecoverable:http_429]; FAILED agents/master/tests/test_candidate_activation.py::test_a2_refused_or_unanswered_candidate_is_passed_over[400-unrecoverable:http_400]; FAILED agents/master/tests/test_candidate_activation.py::test_a2_refused_or_unanswered_candidate_is_passed_over[404-unrecoverable:http_404]; FAILED agents/master/tests/test_candidate_activation.py::test_a2_refused_or_unanswered_candidate_is_passed_over[418-unexpected:http_418]; FAILED agents/master/tests/test_candidate_activation.py::test_a2_refused_or_unanswered_candidate_is_passed_over[503-http_503]; FAILED agents/master/tests/test_candidate_activation.py::test_a2_refused_or_unanswered_candidate_is_passed_over[answer5-TimeoutError]
B08: exit 1; RED; restored SHA256 ee6eb424cd536c86634bff8426fff24abc260a73f62df79693c9c7de746cc425; FAILED agents/master/tests/test_candidate_activation.py::test_a1_first_passing_candidate_is_handed_over_alone
B09: exit 1; RED; restored SHA256 f0b9977175005b9815d45dfbbb3e2de3314235e9f7edff436f09a01fd3872042; FAILED agents/master/tests/test_candidate_fleet.py::test_a6_passed_over_candidate_does_not_fail_fleet
B10: exit 1; RED; restored SHA256 cba332246b83b74a77c9fe902f36866786dad56f927ddcb7260f41caa60c96ac; FAILED agents/master/tests/test_candidate_activation.py::test_a3_declared_providers_candidates_go_first
B11: exit 1; RED; restored SHA256 cba332246b83b74a77c9fe902f36866786dad56f927ddcb7260f41caa60c96ac; FAILED agents/master/tests/test_candidate_declaration.py::test_a9_unrunnable_declaration_is_refused[raw6-belongs to anthropic]; FAILED agents/master/tests/test_candidate_declaration.py::test_a9_unrunnable_declaration_is_refused[raw7-belongs to openai]
B12: exit 1; RED; restored SHA256 cba332246b83b74a77c9fe902f36866786dad56f927ddcb7260f41caa60c96ac; FAILED agents/master/tests/test_candidate_declaration.py::test_a9_unrunnable_declaration_is_refused[raw12-must not repeat]
B13: exit 1; RED; restored SHA256 4da50cd5a3c64d1b84aabb467eac14bcea5ae16d65741bed0472722ef0a97b0c; FAILED agents/master/tests/test_candidate_expansion.py::test_a10_expansion_refuses_unrunnable_roles[key]; FAILED agents/master/tests/test_candidate_expansion.py::test_a10_expansion_refuses_unrunnable_roles[map]
B14: exit 1; RED; restored SHA256 4da50cd5a3c64d1b84aabb467eac14bcea5ae16d65741bed0472722ef0a97b0c; FAILED agents/master/tests/test_candidate_expansion.py::test_a10_expansion_refuses_unrunnable_roles[paths]
B15: exit 1; RED; restored SHA256 afce24d7dc7753ee8c29cbf83f41b58cd7a1c4daabc85ba55a259cebff1c70bf; FAILED agents/master/tests/test_candidate_probe.py::test_a12_candidate_probe_carries_own_model_and_effort
B16: exit 1; RED; restored SHA256 c38f565f8e76b8dfb5c01e6ae02b59347c500aa58e50a2ec10edd631b7059975; FAILED agents/master/tests/test_candidate_probe.py::test_a12_candidate_probe_carries_own_model_and_effort
B17: exit 1; RED; restored SHA256 521c1a8aef13b586e0a2051b4b09cf2c476dd083f56df6a2345cdf22a31c4b45; FAILED agents/master/tests/test_candidate_expansion.py::test_a11_expansion_preserves_roles_keys_and_nonchoosing_probe
B18: exit 1; RED; restored SHA256 22299ae7adfbac1cea6b0b14a01363983d65c52088d8c9a667c16f52ca44584d; FAILED agents/deliberator/tests/test_activated_candidate.py::test_a18_foreign_vendor_model_is_refused[openai-claude-opus-5]; FAILED agents/deliberator/tests/test_activated_candidate.py::test_a18_foreign_vendor_model_is_refused[anthropic-gpt-5.5]
B19: exit 1; RED; restored SHA256 d0ec55aff1763a2c444a8d8c7d14e6800b2698f997862ff548e82ce0bec705af; FAILED agents/deliberator/tests/test_activated_candidate.py::test_a15_settings_are_read_after_activation
B20: exit 1; RED; restored SHA256 d0ec55aff1763a2c444a8d8c7d14e6800b2698f997862ff548e82ce0bec705af; FAILED agents/deliberator/tests/test_activated_candidate.py::test_a17_empty_effort_sends_none[openai]
B21: exit 1; RED; restored SHA256 f9f40f4be179e8a8abdecae7b380acaf16aa0f2f77bc780d9ccb0d324747eead; FAILED agents/deliberator/tests/test_answered_models.py::test_a19_review_names_the_models_that_answered
B22: exit 1; RED; restored SHA256 497e20187fd668e9074de09eeefc2647f0617ab002311ed0df72f67dc2106633; FAILED orchestration/tests/test_llm_brief_candidates.py::test_a22_llm_line_groups_replicas_and_filters_old_or_undated
B23: exit 1; RED; restored SHA256 497e20187fd668e9074de09eeefc2647f0617ab002311ed0df72f67dc2106633; FAILED orchestration/tests/test_llm_brief_candidates.py::test_a22_llm_line_groups_replicas_and_filters_old_or_undated
B24: exit 1; RED; restored SHA256 259aceba3b4dea80fbc4971bdbff88a7037996d2c03113d33b5f435167dca067; FAILED orchestration/tests/test_llm_brief_candidates.py::test_a23_llm_line_follows_container_before_needs_you[PASS]; FAILED orchestration/tests/test_llm_brief_candidates.py::test_a23_llm_line_follows_container_before_needs_you[NOT_FINISHED]
B25: exit 1; RED; restored SHA256 74f09e003b2ea2f190c498435bfd12876a13c037b5a501fb6eed8b8158c6901d; FAILED agents/master/tests/test_candidate_declaration.py::test_a8_real_declaration_parses_and_orders
B26: exit 1; RED; restored SHA256 219793161b6f7863d3e0e1d79ae18a60ed5d25408ba2f9da06afd577ee09e3dc; FAILED agents/master/tests/test_candidate_expansion.py::test_a14_base64_packs_start_master_as_deploy_delivers_them
B27: exit 1; RED; restored SHA256 a4095f9eb3e78ab83b15d00b47ed898dcccbbf27ea698b3fb2aafd1de2e4eca7; FAILED tests/test_candidate_delivery.py::test_a25_master_create_ships_candidate_declaration
B28: exit 1; RED; restored SHA256 a4095f9eb3e78ab83b15d00b47ed898dcccbbf27ea698b3fb2aafd1de2e4eca7; FAILED tests/test_candidate_delivery.py::test_a26_narrow_step_sets_vocabulary_before_pack
B29: exit 1; RED; restored SHA256 3722f4b28607757caacb5ab0e89870be6b90e35b1668c04977b195db414b0d91; FAILED tests/test_candidate_delivery.py::test_a28_switch_proves_a_choosing_app_by_its_candidate[openai/gpt-5.5/high]
B30: exit 1; RED; restored SHA256 4e9f034b3abd3cc28486d701309600ce3a739e9c0e8e6d0e362c49f5e15e20bb; FAILED tests/test_candidate_delivery.py::test_a27_declared_provider_is_first_candidates_vendor
B31: exit 1; RED; restored SHA256 83a0fed1f750150304daa684363384b1f3ba7ea1fe5099832b61fd31f802ed27; FAILED tests/test_candidate_delivery.py::test_a25_image_and_vocabulary_deliver_the_choice; FAILED tests/test_dispatch_scheduled_run.py::test_dispatcher_image_copies_everything_its_entrypoint_imports
B32: exit 1; RED; restored SHA256 92d839ce46674cf55427dc91375143dc70faa6e26c92b3329c408bdadd16a39d; FAILED tests/test_candidate_delivery.py::test_a25_image_and_vocabulary_deliver_the_choice; FAILED tests/test_graph_vocabulary_properties.py::test_every_property_the_code_can_write_is_declared
GUARDS_PROVEN=32/32; ALL_MUTATED_FILES_RESTORED
```

**Module line counts:** Measured after ruff formatting; every touched Python module is under 200 lines (maximum 188).

```text
APPENDIX_PRODUCTION_BLOBS_MATCH=29/29
APPENDIX_LAWS_BLOBS_MATCH=3/3
APPENDIX_EXISTING-TESTS_BLOBS_MATCH=5/5
LOCAL_PROTOTYPE_b3f85ee6_PRODUCTION_BLOBS_MATCH=29/29
DECISION_PATH_CHANGES_AGAINST_ORIGIN_MAIN=0
PROHIBITED_TRACKER_CHANGES=0; NO_UNAPPROVED_EXISTING_TEST_CHANGED
CHANGED_FILES=56
149 agents/deliberator/entrypoint.py
188 agents/deliberator/poll.py
145 agents/deliberator/review_record.py
169 agents/deliberator/settings.py
 99 agents/deliberator/tests/test_activated_candidate.py
 93 agents/deliberator/tests/test_answered_models.py
107 agents/master/credential_outcomes.py
 69 agents/master/credential_probe_candidate.py
187 agents/master/credential_probes.py
 96 agents/master/credential_report.py
 69 agents/master/credential_selection.py
141 agents/master/credential_test.py
179 agents/master/entrypoint.py
147 agents/master/fleet_preflight.py
104 agents/master/model_candidates.py
 75 agents/master/model_choice.py
 89 agents/master/model_expansion.py
 71 agents/master/pack_loading.py
171 agents/master/settings.py
127 agents/master/tests/candidate_testkit.py
 84 agents/master/tests/test_candidate_activation.py
 91 agents/master/tests/test_candidate_declaration.py
107 agents/master/tests/test_candidate_expansion.py
 77 agents/master/tests/test_candidate_fleet.py
114 agents/master/tests/test_candidate_probe.py
 43 agents/master/tests/test_fleet_preflight_packs.py
111 agents/master/tests/test_provider_selection_refusals.py
138 kernel/llm_factory.py
170 orchestration/daily_brief_facts.py
183 orchestration/daily_brief_text.py
 47 orchestration/llm_brief.py
111 orchestration/tests/test_llm_brief_candidates.py
174 scripts/guided_turn_replay.py
 98 scripts/switch_llm_config.py
108 scripts/switch_llm_proof.py
136 tests/test_candidate_delivery.py
 57 tests/test_deploy_llm_pack.py
123 tests/test_switch_llm_config.py
117 tests/test_switch_llm_refusals.py
GUARDS_PROVEN=32/32; ALL_MUTATED_FILES_RESTORED
```

**`make ci`:** Actual unmodified target, redirected by `python ../ta-s276-evidence/run_offline_ci.py` to `../ta-s276-evidence/make-ci.txt` (stdout and stderr to one file, no pipe); exit 2. The file was read. First thirteen steps pass, including the full test suite at 100.00% coverage. Overall gate **verified failing** at dependency audit; online audit **NOT RUN** under the user's network prohibition. The last two security steps were run separately offline; they do not turn the overall CI gate green.

```text
MAKE_CI_EXIT=2
TOTAL                                                           21231      0   4536      0  100.00%
========= 5031 passed, 8 skipped, 2470 warnings in 432.53s (0:07:12) ==========
uv run python scripts/check_dependency_audit.py
dependency audit failed: WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\urllib3\connection.py", line 239, in _new_conn
    sock = connection.create_connection(
        (self._dns_host, self.port),
    ...<2 lines>...
        socket_options=self.socket_options,
    )
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\urllib3\util\connection.py", line 60, in create_connection
    for res in socket.getaddrinfo(host, port, family, socket.SOCK_STREAM):
               ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s276-evidence\offline\sitecustomize.py", line 27, in _offline_getaddrinfo
    _permit(host)
    ~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s276-evidence\offline\sitecustomize.py", line 23, in _permit
    raise OSError("Sprint 276: external network access disabled by user instruction")
OSError: Sprint 276: external network access disabled by user instruction

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\urllib3\connectionpool.py", line 793, in urlopen
    response = self._make_request(
        conn,
    ...<10 lines>...
        **response_kw,
    )
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\urllib3\connectionpool.py", line 494, in _make_request
    raise new_e
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\urllib3\connectionpool.py", line 470, in _make_request
    self._validate_conn(conn)
    ~~~~~~~~~~~~~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\urllib3\connectionpool.py", line 1125, in _validate_conn
    conn.connect()
    ~~~~~~~~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\urllib3\connection.py", line 827, in connect
    self.sock = sock = self._new_conn()
                       ~~~~~~~~~~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\urllib3\connection.py", line 254, in _new_conn
    raise NewConnectionError(
        self, f"Failed to establish a new connection: {e}"
    ) from e
urllib3.exceptions.NewConnectionError: HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: Sprint 276: external network access disabled by user instruction

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\requests\adapters.py", line 696, in send
    resp = conn.urlopen(
        method=request.method,
    ...<9 lines>...
        chunked=chunked,
    )
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\urllib3\connectionpool.py", line 847, in urlopen
    retries = retries.increment(
        method, url, error=new_e, _pool=self, _stacktrace=sys.exc_info()[2]
    )
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\urllib3\util\retry.py", line 555, in increment
    raise MaxRetryError(_pool, url, reason) from reason  # type: ignore[arg-type]
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: Sprint 276: external network access disabled by user instruction"))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Scripts\pip-audit.exe\__main__.py", line 10, in <module>
    sys.exit(audit())
             ~~~~~^^
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\pip_audit\_cli.py", line 554, in audit
    for spec, vulns in auditor.audit(source):
                       ~~~~~~~~~~~~~^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\pip_audit\_audit.py", line 68, in audit
    for dep, vulns in self._service.query_all(specs):
                      ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\pip_audit\_service\interface.py", line 180, in query_all
    yield self.query(spec)
          ~~~~~~~~~~^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\pip_audit\_service\pypi.py", line 64, in query
    response: requests.Response = self.session.get(url=url, timeout=self.timeout)
                                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\requests\sessions.py", line 671, in get
    return self.request("GET", url, params=params, **kwargs)
           ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\requests\sessions.py", line 651, in request
    resp = self.send(prep, **send_kwargs)
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\requests\sessions.py", line 784, in send
    r = adapter.send(request, **kwargs)
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\cachecontrol\adapter.py", line 76, in send
    resp = super().send(request, stream, timeout, verify, cert, proxies)
  File "C:\Users\yury_\Downloads\project\ta-s276\.venv\Lib\site-packages\requests\adapters.py", line 729, in send
    raise ConnectionError(e, request=request)
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: Sprint 276: external network access disabled by user instruction"))
make: *** [Makefile:60: ci] Error 1
Detect secrets...........................................................Passed
DETECT_SECRETS_EXIT=0
detect-secrets (untracked): no untracked files to scan
UNTRACKED_SECRETS_EXIT=0
```

**`make gate-ran`:** not done; the planner runs it at review from the exact commit's worktree. Push, remote gates and merge are not done.

**Not met / verified failing:** Full CI is verified failing (exit 2); dependency advisory lookup is NOT RUN offline. F0's planner CI/guard evidence was not re-run; only its 29 production blob identities were independently compared. Push, `make gate-ran`, review, merge, F1a (PowerShell stand-in), F1b (paid real probes), deployment and F2 are not done. Vendor request-cap assumptions remain unmeasured here.

**Planner review (2026-10-15, `87aa3ee0`):** the 29 production files are the prototype `b3f85ee6` byte for byte (`git diff proto-s276 HEAD` names only the three law test plans); `uv.lock` changes the package version alone. Windows `make ci` with network, redirected to a file: **exit 0**, 5,031 passed, 8 skipped, 100.00 %, dependency audit clean (no unaccepted vulnerabilities, 1 accepted advisory re-checked); this discharges the offline exit 2 above. The planner's 67 tests pass on the built code. The planner's 32 breaks, run against the builder's 14 new and edited test files only, **32 of 32 red**, tree restored clean. Evidence: OneDrive `trading-agents-data/wq123-2026-10-15/` (`s276-make-ci.txt`, `planner_tests_on_built.txt`, `breaks_on_builder_tests.txt`). Push, CodeQL set-diff and `make gate-ran` follow on this commit.

**One planner change at review, the planner's own miss:** the CodeQL set-diff against sprint 275's branch (133 open, 0 errors) found **7 new errors**, `py/unsafe-cyclic-import`, in `credential_outcomes.py`, `credential_test.py` and `model_choice.py`: the prototype's two new modules read `CredentialTest` and `PassCache` from `credential_test` (under `TYPE_CHECKING`), which imports both of them at run time. The two types and `Cost` now live in a new leaf module, `agents/master/credential_check.py` (77 lines), that `credential_test` re-exports through `__all__`, so none of the other 30 importers changed and the cycle is gone, not hidden. The same diff found one warning in a builder test (`py/incomplete-url-substring-sanitization`, A7's host check), now a `urlsplit(...).hostname` comparison. Windows `make ci` on the fix: exit 0 (5,031 passed, 8 skipped, 100.00 %, audit clean; `s276-make-ci-cycle-fix.txt`).

---

## Return notes

- All work and proof stayed in `../ta-s276` on the named sprint branch. The 29 production files, three law files and five existing-test edits retain their exact Appendix/prototype identities after every plant. Scope proof finds zero `DECISION_PATHS` against local `origin/main`; no network fetch was used.
- The deploy still needs the master's vocabulary before the new image because even a quiet fleet check writes `llm_passed_over`. F1a, F1b, the operator's deploy and F2 remain the planner/operator sequence; no command in that sequence was invoked here.
- The declaration is activation-time fallback only. Mid-debate refusal still fails open as before; P3 is not done. The Anthropic `max_tokens: 1` and OpenAI `max_completion_tokens: 256` success assumptions still require F1b.
- Evidence logs and the byte-restoring guard runner are outside the repository in `../ta-s276-evidence`; required output is pasted above. Final local bookkeeping checks after filling this handback:

```text
FINAL_LAW_COVERAGE_EXIT=0
docs_seen=281 SPEC=10 BUILT=1 MERGED=270 UNMAPPED=0 MISSING=0
FINAL_SPRINT_STATUS_EXIT=0
FINAL_MARKDOWN_LINKS_EXIT=0
FINAL_SCOPE_EXIT=0
LOCAL_PROTOTYPE_LAWS_BLOBS_MATCH=3/3
LOCAL_PROTOTYPE_EXISTING-TESTS_BLOBS_MATCH=5/5
```

---

## Appendix — the change, measured on the planner's prototype

The prototype is `b3f85ee6` on the planner's local branch `proto-s276`, cut from `main` at
`2ebb1158`. Each new file is given whole; each changed file as a diff against `main`. The blob of
every production file is in `prototype_blobs.txt` in the evidence folder
(`OneDrive/trading-agents-data/wq123-2026-10-15/`).

### 1. The declaration — `agents/master/model_candidates.py` (new)

`agents/master/model_candidates.py` — new, 104 lines:

```python
"""The pack's ordered LLM candidates and the agent types that choose among them.

Agent: master
Role: parse and validate the declared vendor, model and effort list (DL-289 P1).
External I/O: reads the declaration file when load_llm_plan is called.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from kernel.llm_factory import KEY_ENV, model_provider

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class LlmCandidate:
    """One declared way to run an LLM role: a vendor, a model and an effort."""

    vendor: str
    model: str
    effort: str

    @property
    def label(self) -> str:
        """Name the candidate in records and lines: ``vendor/model/effort``."""
        return f"{self.vendor}/{self.model}/{self.effort}"


@dataclass(frozen=True)
class LlmRole:
    """The configuration keys an agent type reads its chosen candidate from."""

    vendor_key: str
    model_key: str
    effort_key: str


@dataclass(frozen=True)
class LlmPlan:
    """The ordered candidates and the agent types that run on the first working one."""

    candidates: tuple[LlmCandidate, ...]
    roles: Mapping[str, LlmRole]

    def ordered(self, provider: str) -> tuple[LlmCandidate, ...]:
        """The declared provider's candidates first, each group in declared order."""
        first = tuple(item for item in self.candidates if item.vendor == provider)
        rest = tuple(item for item in self.candidates if item.vendor != provider)
        return first + rest


def parse_llm_plan(text: str) -> LlmPlan:
    """Parse the LLM pack; refuse anything a role could not run on."""
    raw = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError("LLM declaration must be an object")
    entries = raw.get("candidates")
    if not isinstance(entries, list) or not entries:
        raise ValueError("LLM declaration needs a non-empty candidates list")
    candidates = tuple(_candidate(entry) for entry in entries)
    if len({item.label for item in candidates}) != len(candidates):
        raise ValueError("LLM candidates must not repeat")
    roles = raw.get("roles", {})
    if not isinstance(roles, dict):
        raise ValueError("LLM roles must map agent types to keys")
    return LlmPlan(
        candidates, {str(name): _role(name, keys) for name, keys in roles.items()}
    )


def load_llm_plan(path: str) -> LlmPlan:
    """Load the LLM pack from a JSON file at *path*."""
    return parse_llm_plan(Path(path).read_text(encoding="utf-8"))


def _candidate(entry: object) -> LlmCandidate:
    if not isinstance(entry, dict):
        raise ValueError("an LLM candidate must be an object")
    vendor, model, effort = (_text(entry, key) for key in ("vendor", "model", "effort"))
    if vendor not in KEY_ENV:
        raise ValueError(f"unknown LLM candidate vendor {vendor!r}")
    owner = model_provider(model)
    if owner not in (None, vendor):
        raise ValueError(f"model {model!r} belongs to {owner}, not {vendor}")
    return LlmCandidate(vendor, model, effort)


def _role(name: object, keys: object) -> LlmRole:
    if not isinstance(keys, dict):
        raise ValueError(f"LLM role {name!r} must be an object")
    return LlmRole(*(_text(keys, key) for key in ("vendor", "model", "effort")))


def _text(entry: dict[str, object], key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"LLM declaration field {key!r} must be a non-empty string")
    return value
```

### 2. The probe carries the candidate — `credential_probe_candidate.py` (new), `credential_probes.py`

`agents/master/credential_probe_candidate.py` — new, 69 lines:

```python
"""Place an LLM candidate's model and effort into a declared probe body.

Agent: master
Role: let one vendor probe test each declared candidate exactly as it will run.
External I/O: none.

A probe declares ``candidate_paths``: where in its JSON body the model and the effort
go. The values travel to the probe in two reserved configuration keys, which no
environment name can spell, so a probe of a candidate sends that candidate's model
and effort and nothing else changes.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

MODEL_KEY = "llm:model"
EFFORT_KEY = "llm:effort"
_FIELDS = {"model": MODEL_KEY, "effort": EFFORT_KEY}

type CandidatePaths = dict[str, tuple[str, ...]]


def candidate_paths(value: object) -> CandidatePaths | None:
    """Validate a probe's ``candidate_paths``; None when it declares none."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != set(_FIELDS):
        raise ValueError("candidate_paths must name exactly 'model' and 'effort'")
    paths: CandidatePaths = {}
    for field, path in value.items():
        if (
            not isinstance(path, list)
            or not path
            or not all(isinstance(part, str) and part for part in path)
        ):
            raise ValueError(f"candidate_paths {field!r} must be a list of keys")
        paths[field] = tuple(path)
    return paths


def candidate_body(
    declared: object, paths: CandidatePaths, config: Mapping[str, str]
) -> bytes:
    """Serialise the declared body with the candidate's model and effort placed."""
    body = deepcopy(declared)
    if not isinstance(body, dict):
        raise ValueError("candidate_paths need a json_body object")
    for field, path in paths.items():
        node: dict[str, object] = body
        for part in path[:-1]:
            child = node.setdefault(part, {})
            if not isinstance(child, dict):
                raise ValueError(f"candidate path {'.'.join(path)} crosses a value")
            node = child
        node[path[-1]] = config[_FIELDS[field]]
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def with_candidate(
    config: Mapping[str, str], model: str, effort: str
) -> dict[str, str]:
    """Return the configuration a candidate's probe runs against."""
    return {**config, MODEL_KEY: model, EFFORT_KEY: effort}
```

`agents/master/credential_probes.py` — diff against `main`:

```diff
diff --git a/agents/master/credential_probes.py b/agents/master/credential_probes.py
index 3de23bcd..29339f08 100644
--- a/agents/master/credential_probes.py
+++ b/agents/master/credential_probes.py
@@ -12,6 +12,11 @@ import json
 from pathlib import Path
 from typing import TYPE_CHECKING, Literal

+from agents.master.credential_probe_candidate import (
+    MODEL_KEY,
+    candidate_body,
+    candidate_paths,
+)
 from agents.master.credential_probe_support import (
     HttpProbeRequest,
     bool_field,
@@ -108,6 +113,7 @@ def _test_from_entry(
         cost=test_cost,
         agent_types=(agent_type,),
         llm_provider=str(entry.get("llm_provider", "")),
+        takes_candidate=entry.get("candidate_paths") is not None,
     )


@@ -119,6 +125,9 @@ def _http_runner(
     headers = str_dict(entry.get("headers", {}), "headers")
     query = str_dict(entry.get("query", {}), "query")
     body = json_body(entry.get("json_body"))
+    paths = candidate_paths(entry.get("candidate_paths"))
+    if paths is not None and body is None:
+        raise ValueError("candidate_paths need a json_body")
     expected = status_set(entry.get("expected_statuses", [200]))
     credential_failure_statuses = status_set(
         entry.get("credential_failure_statuses", [401, 403])
@@ -133,11 +142,16 @@ def _http_runner(
             }
         except KeyError as exc:
             return credential_failed(f"missing_config:{exc.args[0]}")
-        if body is not None:
+        payload = body
+        if paths is not None and MODEL_KEY in config:
+            payload = candidate_body(entry["json_body"], paths, config)
+        if payload is not None:
             rendered_headers = with_json_content_type(rendered_headers)
         try:
             status = transport(
-                HttpProbeRequest(method, url, rendered_headers, timeout_seconds, body)
+                HttpProbeRequest(
+                    method, url, rendered_headers, timeout_seconds, payload
+                )
             )
         except (TimeoutError, OSError) as exc:
             return credential_transport_failed(type(exc).__name__)
```

### 3. The outcomes and the choice — `credential_outcomes.py`, `model_choice.py` (new); `credential_test.py`, `credential_report.py`

`agents/master/credential_outcomes.py` — new, 107 lines:

```python
"""Collect what each credential test did during one activation or fleet check.

Agent: master
Role: run one test against resolved config and file its outcome under its name.
External I/O: none directly (delegates to the injected test callable).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from agents.master.credential_report import (
    CredentialFailure,
    CredentialTestReport,
    CredentialTransportFailure,
)
from agents.master.credential_result import coerce_result

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.master.credential_test import CredentialTest, PassCache


@dataclass
class Outcomes:
    """Every name a run of tests declared, tested, passed, cached or failed."""

    applicable: list[str] = field(default_factory=list)
    tested: list[str] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)
    cached: list[str] = field(default_factory=list)
    failed_required: list[str] = field(default_factory=list)
    failed_optional: list[str] = field(default_factory=list)
    transport_failures: list[CredentialTransportFailure] = field(default_factory=list)
    credential_failures: list[CredentialFailure] = field(default_factory=list)

    def run(
        self,
        test: CredentialTest,
        config: Mapping[str, str],
        cache: PassCache | None,
    ) -> None:
        """Run one applicable test, or reuse its fresh costly pass."""
        self.applicable.append(test.name)
        if test.cost == "costly" and cache is not None and cache.fresh(test.name):
            self.cached.append(test.name)
            return
        self.tested.append(test.name)
        result = coerce_result(test.run(config))
        if result.status == "passed":
            self.passed.append(test.name)
            if test.cost == "costly" and cache is not None:
                cache.record(test.name)
        elif result.status == "transport_failure":
            self.transport_failures.append(
                CredentialTransportFailure(test.name, result.reason)
            )
        else:
            self.credential_failures.append(CredentialFailure(test.name, result.reason))
            if test.required:
                self.failed_required.append(test.name)
            else:
                self.failed_optional.append(test.name)

    @property
    def proven(self) -> bool:
        """No required test was refused and none went unanswered."""
        return not self.failed_required and not self.transport_failures

    def first_reason(self) -> str:
        """The first refusal's reason, else the first unanswered test's."""
        refused = [
            failure.reason
            for failure in self.credential_failures
            if failure.name in self.failed_required
        ]
        unanswered = [failure.reason for failure in self.transport_failures]
        return (refused or unanswered or [""])[0]

    def extend(self, other: Outcomes) -> None:
        """Add another run's outcomes after this one's, in order."""
        for name in self.__dataclass_fields__:
            getattr(self, name).extend(getattr(other, name))

    def report(
        self,
        config: dict[str, object],
        *,
        llm_candidate: str = "",
        llm_passed_over: tuple[str, ...] = (),
    ) -> CredentialTestReport:
        """Freeze the outcomes into the activation evidence."""
        return CredentialTestReport(
            config,
            tuple(self.applicable),
            tuple(self.tested),
            tuple(self.passed),
            tuple(self.cached),
            tuple(self.failed_required),
            tuple(self.failed_optional),
            tuple(self.transport_failures),
            tuple(self.credential_failures),
            llm_candidate,
            llm_passed_over,
        )
```

`agents/master/model_choice.py` — new, 75 lines:

```python
"""Choose the first declared LLM candidate whose probes pass (DL-289 P2).

Agent: master
Role: try an agent type's candidates in order, hand over the first that works.
External I/O: none directly (delegates to the injected candidate probes).

A candidate passes when none of its required probes was refused and none went
unanswered. The ones before it are passed over: recorded, never a failure of the
activation or of the fleet check. When none passes, the first that was only
unanswered is handed over unproven (`MST-FAIL-04`); when every one was refused,
every refusal stands and the activation is refused.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.master.credential_outcomes import Outcomes
from kernel.llm_factory import KEY_ENV

if TYPE_CHECKING:
    from collections.abc import Mapping

    from agents.master.credential_test import CredentialTest, PassCache
    from agents.master.model_candidates import LlmCandidate, LlmRole


def choose_llm(
    entries: list[tuple[CredentialTest, LlmCandidate, LlmRole]],
    config: dict[str, object],
    str_config: Mapping[str, str],
    cache: PassCache | None,
) -> tuple[Outcomes, str, tuple[str, ...]]:
    """Return the outcomes to report, the chosen label and the passed-over lines."""
    groups: dict[LlmCandidate, list[CredentialTest]] = {}
    roles: dict[LlmCandidate, LlmRole] = {}
    for test, candidate, role in entries:
        groups.setdefault(candidate, []).append(test)
        roles[candidate] = role
    tried: list[tuple[LlmCandidate, Outcomes]] = []
    for candidate, group in groups.items():
        outcomes = Outcomes()
        for test in group:
            outcomes.run(test, str_config, cache)
        tried.append((candidate, outcomes))
        if outcomes.proven:
            break
    chosen = next((item for item in tried if item[1].proven), None) or next(
        (item for item in tried if not item[1].failed_required), None
    )
    if chosen is None:
        refused = Outcomes()
        for _, outcomes in tried:
            refused.extend(outcomes)
        return refused, "", ()
    candidate, outcomes = chosen
    _hand_over(config, candidate, roles[candidate])
    passed_over = tuple(
        f"{item.label}: {other.first_reason()}"
        for item, other in tried
        if item != candidate
    )
    return outcomes, candidate.label, passed_over


def _hand_over(
    config: dict[str, object], candidate: LlmCandidate, role: LlmRole
) -> None:
    """Name the candidate in the role's keys; withhold every other vendor's key."""
    for vendor, key in KEY_ENV.items():
        if vendor != candidate.vendor:
            config.pop(key, None)
    config[role.vendor_key] = candidate.vendor
    config[role.model_key] = candidate.model
    config[role.effort_key] = candidate.effort
```

`agents/master/credential_test.py` — diff against `main`:

```diff
diff --git a/agents/master/credential_test.py b/agents/master/credential_test.py
index 6787d47d..add5b156 100644
--- a/agents/master/credential_test.py
+++ b/agents/master/credential_test.py
@@ -17,18 +17,17 @@ from datetime import UTC, datetime, timedelta
 from threading import Lock
 from typing import TYPE_CHECKING, Literal

-from agents.master.credential_report import (
-    CredentialFailure,
-    CredentialTestReport,
-    CredentialTransportFailure,
-)
-from agents.master.credential_result import CheckResult, coerce_result
+from agents.master.credential_outcomes import Outcomes
+from agents.master.model_choice import choose_llm
 from agents.master.secret_map import resolve_config

 if TYPE_CHECKING:
     from collections.abc import Callable, Mapping

+    from agents.master.credential_report import CredentialTestReport
+    from agents.master.credential_result import CheckResult
     from agents.master.key_vault import SecretStore
+    from agents.master.model_candidates import LlmCandidate, LlmRole
     from agents.master.secret_map import SecretMap

 Cost = Literal["cheap", "costly"]
@@ -48,7 +47,9 @@ class CredentialTest:

     ``run(config)`` returns True or ``CredentialCheckResult(status="passed")`` when
     the credential works. A ``required`` credential failure blocks activation; a
-    transport failure is faulted by the caller but does not block.
+    transport failure is faulted by the caller but does not block. A test with a
+    ``candidate`` probes that LLM candidate for an agent type that chooses one
+    (DL-289); ``takes_candidate`` marks a declared probe able to carry one.
     """

     name: str
@@ -57,6 +58,9 @@ class CredentialTest:
     cost: Cost = "cheap"
     agent_types: tuple[str, ...] = ()
     llm_provider: str = ""
+    takes_candidate: bool = False
+    candidate: LlmCandidate | None = None
+    role: LlmRole | None = None


 class PassCache:
@@ -111,48 +115,27 @@ def resolve_and_test_report(
     *,
     cache: PassCache | None = None,
 ) -> CredentialTestReport:
-    """Resolve secrets, run applicable tests, and return activation evidence."""
+    """Resolve secrets, run applicable tests, and return activation evidence.
+
+    An agent type with LLM candidates runs its other tests first, then is handed
+    the first candidate that passes (`model_choice`).
+    """
     config = resolve_config(agent_type, store, secret_map)
     str_config = {k: v for k, v in config.items() if isinstance(v, str)}
-    applicable: list[str] = []
-    tested: list[str] = []
-    passed: list[str] = []
-    cached: list[str] = []
-    failed_required: list[str] = []
-    failed_optional: list[str] = []
-    transport_failures: list[CredentialTransportFailure] = []
-    credential_failures: list[CredentialFailure] = []
-    for test in tests:
-        if test.agent_types and agent_type not in test.agent_types:
-            continue
-        applicable.append(test.name)
-        if test.cost == "costly" and cache is not None and cache.fresh(test.name):
-            cached.append(test.name)
-            continue
-        tested.append(test.name)
-        result = coerce_result(test.run(str_config))
-        if result.status == "passed":
-            passed.append(test.name)
-            if test.cost == "costly" and cache is not None:
-                cache.record(test.name)
-        elif result.status == "transport_failure":
-            transport_failures.append(
-                CredentialTransportFailure(test.name, result.reason)
-            )
-        else:
-            credential_failures.append(CredentialFailure(test.name, result.reason))
-            if test.required:
-                failed_required.append(test.name)
-            else:
-                failed_optional.append(test.name)
-    return CredentialTestReport(
-        config,
-        tuple(applicable),
-        tuple(tested),
-        tuple(passed),
-        tuple(cached),
-        tuple(failed_required),
-        tuple(failed_optional),
-        tuple(transport_failures),
-        tuple(credential_failures),
-    )
+    applicable = [
+        test for test in tests if not test.agent_types or agent_type in test.agent_types
+    ]
+    outcomes = Outcomes()
+    for test in applicable:
+        if test.candidate is None:
+            outcomes.run(test, str_config, cache)
+    candidates = [
+        (test, test.candidate, test.role)
+        for test in applicable
+        if test.candidate is not None and test.role is not None
+    ]
+    if not candidates:
+        return outcomes.report(config)
+    chosen, label, passed_over = choose_llm(candidates, config, str_config, cache)
+    outcomes.extend(chosen)
+    return outcomes.report(config, llm_candidate=label, llm_passed_over=passed_over)
```

`agents/master/credential_report.py` — diff against `main`:

```diff
diff --git a/agents/master/credential_report.py b/agents/master/credential_report.py
index 7f903175..efa3990e 100644
--- a/agents/master/credential_report.py
+++ b/agents/master/credential_report.py
@@ -45,11 +45,17 @@ class CredentialTestReport:
     failed_optional: tuple[str, ...]
     transport_failures: tuple[CredentialTransportFailure, ...]
     credential_failures: tuple[CredentialFailure, ...] = ()
+    llm_candidate: str = ""
+    llm_passed_over: tuple[str, ...] = ()


 def credential_test_props(report: CredentialTestReport) -> dict[str, object]:
-    """Return graph-safe activation props for credential-test evidence."""
-    return {
+    """Return graph-safe activation props for credential-test evidence.
+
+    An agent type that chose an LLM candidate also records which one, and each
+    candidate passed over before it with the reason (DL-289).
+    """
+    props: dict[str, object] = {
         "credential_tests_declared": list(report.applicable),
         "credential_tests_tested": list(report.tested),
         "credential_tests_passed": list(report.passed),
@@ -59,6 +65,10 @@ def credential_test_props(report: CredentialTestReport) -> dict[str, object]:
             failure.name for failure in report.transport_failures
         ],
     }
+    if report.llm_candidate:
+        props["llm_candidate"] = report.llm_candidate
+        props["llm_passed_over"] = list(report.llm_passed_over)
+    return props


 def submit_transport_faults(
```

### 4. The start — `model_expansion.py` (new); `credential_selection.py`, `settings.py`, `pack_loading.py`, `entrypoint.py`

`agents/master/model_expansion.py` — new, 89 lines:

```python
"""Turn each LLM role's vendor probes into one probe per declared candidate.

Agent: master
Role: build, once at start, the ordered candidate probes an activation tries.
External I/O: none; pure transformation of injected pack data.

The master refuses to start when a role could not run on a candidate it declares:
no probe of that vendor for the agent type, a probe that cannot carry a model and
an effort, or no key of that vendor in the agent type's secret map.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from agents.master.credential_probe_candidate import with_candidate
from kernel.llm_factory import KEY_ENV

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from agents.master.credential_result import CheckResult
    from agents.master.credential_test import CredentialTest
    from agents.master.model_candidates import LlmCandidate, LlmPlan
    from agents.master.secret_map import SecretMap


def expand_llm_candidates(
    plan: LlmPlan | None,
    provider: str,
    tests: tuple[CredentialTest, ...],
    secret_map: SecretMap | None,
) -> tuple[CredentialTest, ...]:
    """Replace each role type's LLM probes with its candidates' probes, in order."""
    if plan is None:
        return tests
    kept = tuple(
        test
        for test in tests
        if not test.llm_provider or not set(test.agent_types) & set(plan.roles)
    )
    expanded: list[CredentialTest] = []
    for agent_type, role in plan.roles.items():
        granted = {env for _, env in (secret_map or {}).get(agent_type, [])}
        for candidate in plan.ordered(provider):
            probes = [
                test
                for test in tests
                if test.llm_provider == candidate.vendor
                and agent_type in test.agent_types
            ]
            _refuse_unrunnable(agent_type, candidate, probes, granted)
            expanded.extend(
                replace(
                    test,
                    name=f"{test.name}:{candidate.model}:{candidate.effort}",
                    run=_bound(test, candidate),
                    agent_types=(agent_type,),
                    candidate=candidate,
                    role=role,
                )
                for test in probes
            )
    return kept + tuple(expanded)


def _refuse_unrunnable(
    agent_type: str,
    candidate: LlmCandidate,
    probes: list[CredentialTest],
    granted: set[str],
) -> None:
    where = f"{agent_type} candidate {candidate.label}"
    if not probes:
        raise ValueError(f"{where} has no {candidate.vendor} probe")
    if not all(test.takes_candidate for test in probes):
        raise ValueError(f"{where} has a probe without candidate_paths")
    if KEY_ENV[candidate.vendor] not in granted:
        raise ValueError(f"{where} is not granted {KEY_ENV[candidate.vendor]}")


def _bound(
    test: CredentialTest, candidate: LlmCandidate
) -> Callable[[Mapping[str, str]], CheckResult]:
    def run(config: Mapping[str, str]) -> CheckResult:
        return test.run(with_candidate(config, candidate.model, candidate.effort))

    return run
```

`agents/master/credential_selection.py` — diff against `main`:

```diff
diff --git a/agents/master/credential_selection.py b/agents/master/credential_selection.py
index 14ac9718..50274cf0 100644
--- a/agents/master/credential_selection.py
+++ b/agents/master/credential_selection.py
@@ -12,6 +12,8 @@ from typing import TYPE_CHECKING
 from kernel.llm_factory import KEY_ENV

 if TYPE_CHECKING:
+    from collections.abc import Collection
+
     from agents.master.credential_test import CredentialTest
     from agents.master.secret_map import SecretMap

@@ -20,8 +22,13 @@ def select_llm_provider(
     provider: str,
     tests: tuple[CredentialTest, ...],
     secret_map: SecretMap | None,
+    roles: Collection[str] = (),
 ) -> tuple[tuple[CredentialTest, ...], SecretMap | None]:
-    """Validate tags, then keep only the selected vendor's probes and key."""
+    """Validate tags, then keep only the selected vendor's probes and key.
+
+    An agent type in ``roles`` keeps every vendor's probes and keys: it chooses
+    among the declared LLM candidates at each activation (`model_choice`).
+    """
     if provider and provider not in KEY_ENV:
         raise ValueError(f"unknown MASTER_LLM_PROVIDER {provider!r}")
     for test in tests:
@@ -29,21 +36,34 @@ def select_llm_provider(
             raise ValueError(f"unknown probe llm_provider {test.llm_provider!r}")
     if not provider:
         return tests, secret_map
-    selected = tuple(test for test in tests if test.llm_provider in ("", provider))
+    selected = tuple(
+        test
+        for test in tests
+        if test.llm_provider in ("", provider)
+        or (test.agent_types and set(test.agent_types) <= set(roles))
+    )
     other_keys = {env for vendor, env in KEY_ENV.items() if vendor != provider}
     secrets = (
         {
-            agent_type: [(kv, env) for kv, env in pairs if env not in other_keys]
+            agent_type: [
+                (kv, env)
+                for kv, env in pairs
+                if env not in other_keys or agent_type in roles
+            ]
             for agent_type, pairs in secret_map.items()
         }
         if secret_map is not None
         else None
     )
     for agent_type, pairs in (secrets or {}).items():
-        if any(env == KEY_ENV[provider] for _, env in pairs) and not any(
-            test.llm_provider == provider
-            and (not test.agent_types or agent_type in test.agent_types)
-            for test in selected
+        if (
+            agent_type not in roles
+            and any(env == KEY_ENV[provider] for _, env in pairs)
+            and not any(
+                test.llm_provider == provider
+                and (not test.agent_types or agent_type in test.agent_types)
+                for test in selected
+            )
         ):
             raise ValueError(f"{agent_type} granted {provider} key without its probe")
     return selected, secrets
```

`agents/master/settings.py` — diff against `main`:

```diff
diff --git a/agents/master/settings.py b/agents/master/settings.py
index 79a6d319..1d8be15c 100644
--- a/agents/master/settings.py
+++ b/agents/master/settings.py
@@ -82,6 +82,20 @@ class MasterSettings(AgentSettings):
             "takes precedence over credential_tests_path."
         ),
     )
+    llm_pack_path: str = tunable(
+        "",
+        why=(
+            "Filesystem path to the pack's ordered LLM candidates; empty = no "
+            "agent type chooses a candidate unless base64 pack data is supplied."
+        ),
+    )
+    llm_pack_b64: str = tunable(
+        "",
+        why=(
+            "Base64-encoded LLM candidate JSON injected at deploy time (cloud); "
+            "takes precedence over llm_pack_path."
+        ),
+    )
     credential_pass_cache_ttl_minutes: int = tunable(
         5,
         why=(
```

`agents/master/pack_loading.py` — diff against `main`:

```diff
diff --git a/agents/master/pack_loading.py b/agents/master/pack_loading.py
index 55e11af8..6c6e5757 100644
--- a/agents/master/pack_loading.py
+++ b/agents/master/pack_loading.py
@@ -1,7 +1,7 @@
 """Load master's injected declarations without importing a trading pack.

 Agent: master
-Role: resolve base64 or file declarations for grants, secrets and probes.
+Role: resolve base64 or file declarations for grants, secrets, probes and LLMs.
 External I/O: configured declaration files only.
 """

@@ -15,6 +15,7 @@ from agents.master.credential_probes import (
     parse_credential_tests,
 )
 from agents.master.grants import load_grant_policy, parse_grant_policy
+from agents.master.model_candidates import load_llm_plan, parse_llm_plan
 from agents.master.secret_map import load_secret_map, parse_secret_map

 if TYPE_CHECKING:
@@ -22,6 +23,7 @@ if TYPE_CHECKING:

     from agents.master.credential_test import CredentialTest
     from agents.master.grants import GrantPolicy
+    from agents.master.model_candidates import LlmPlan
     from agents.master.secret_map import SecretMap
     from agents.master.settings import MasterSettings

@@ -60,3 +62,10 @@ def load_master_packs(
         load_credential_tests,
     )
     return grants, secrets, tests or ()
+
+
+def load_llm_pack(settings: MasterSettings) -> LlmPlan | None:
+    """Read the ordered LLM candidates; absent means no agent type chooses one."""
+    return _resolve_pack(
+        settings.llm_pack_b64, settings.llm_pack_path, parse_llm_plan, load_llm_plan
+    )
```

`agents/master/entrypoint.py` — diff against `main`:

```diff
diff --git a/agents/master/entrypoint.py b/agents/master/entrypoint.py
index 5bc320aa..ab7f3063 100644
--- a/agents/master/entrypoint.py
+++ b/agents/master/entrypoint.py
@@ -20,7 +20,8 @@ from agents.master.fleet_preflight import (
 )
 from agents.master.fleet_preflight_loop import start_fleet_preflight_daemon
 from agents.master.http_server import serve
-from agents.master.pack_loading import load_master_packs
+from agents.master.model_expansion import expand_llm_candidates
+from agents.master.pack_loading import load_llm_pack, load_master_packs
 from agents.master.remediation_posture import refuse_unwired_automatic_remediation
 from agents.master.settings import MasterSettings
 from agents.master.stopping import shut_down
@@ -64,10 +65,15 @@ def build_app(
     """
     settings = settings or MasterSettings()
     grant_policy, secret_map, credential_tests = load_master_packs(settings)
+    plan = load_llm_pack(settings)
     credential_tests, secret_map = select_llm_provider(
         settings.llm_provider,
         credential_tests,
         secret_map,
+        roles=plan.roles if plan else (),
+    )
+    credential_tests = expand_llm_candidates(
+        plan, settings.llm_provider, credential_tests, secret_map
     )
     if secret_map and not credential_tests:
         raise ValueError(
```

### 5. The fleet check — `agents/master/fleet_preflight.py`

`agents/master/fleet_preflight.py` — diff against `main`:

```diff
diff --git a/agents/master/fleet_preflight.py b/agents/master/fleet_preflight.py
index 3d4b6871..e86a87d8 100644
--- a/agents/master/fleet_preflight.py
+++ b/agents/master/fleet_preflight.py
@@ -52,8 +52,12 @@ def run_fleet_preflight(
     pass_cache: PassCache | None,
     now: datetime,
 ) -> FleetPreflightResult:
-    """Test every grant-policy agent type and record fleet readiness."""
+    """Test every grant-policy agent type and record fleet readiness.
+
+    An LLM candidate passed over for a later one is recorded, not a failure.
+    """
     failures: list[PreflightFailure] = []
+    passed_over: list[str] = []
     agent_types_checked = tuple(sorted(grant_policy))
     for agent_type in agent_types_checked:
         try:
@@ -70,6 +74,7 @@ def run_fleet_preflight(
             )
             continue
         failures.extend(_report_failures(agent_type, report))
+        passed_over.extend(f"{agent_type}: {line}" for line in report.llm_passed_over)
     checked_at = now.astimezone(UTC).isoformat(timespec="seconds")
     failure_values = [
         f"{failure.klass}:{failure.agent_type}:{failure.probe}:{failure.reason}"
@@ -84,6 +89,7 @@ def run_fleet_preflight(
             "failure_count": len(failures),
             "failures": failure_values,
             "agent_types_checked": list(agent_types_checked),
+            "llm_passed_over": passed_over,
         },
     )
     if failures:
```

### 6. The kernel and the deliberator — `kernel/llm_factory.py`, the deliberator's `settings.py`, `entrypoint.py`, `review_record.py`, `poll.py`; `scripts/guided_turn_replay.py`

`kernel/llm_factory.py` — diff against `main`:

```diff
diff --git a/kernel/llm_factory.py b/kernel/llm_factory.py
index e6385316..1d26260c 100644
--- a/kernel/llm_factory.py
+++ b/kernel/llm_factory.py
@@ -52,7 +52,11 @@ def build_llm(
     max_tokens: int,
     effort: str | None,
 ) -> LLMClient:
-    """Build exactly the selected provider; never silently switch vendors."""
+    """Build exactly the selected provider; never silently switch vendors.
+
+    A model of another known vendor's family is refused, never sent (DL-289).
+    """
+    _refuse_foreign_model(provider, model)
     if provider == "anthropic":
         return AnthropicLLMClient(
             api_key=api_key, model=model, max_tokens=max_tokens, effort=effort or "max"
@@ -99,12 +103,7 @@ def build_operator_llm(
     effort: str,
 ) -> LLMClient:
     """Construct exactly the selected vendor's operator adapter."""
-    owner = model_provider(model)
-    if provider in KEY_ENV and owner not in (None, provider):
-        raise ModelProviderMismatchError(
-            f"model {model!r} belongs to {owner}; the declared llm_provider is "
-            f"{provider}. Unset the model to use the provider's default."
-        )
+    _refuse_foreign_model(provider, model)
     if provider == "anthropic":
         return OperatorAnthropicLLMClient(
             api_key=api_key,
@@ -122,6 +121,15 @@ def build_operator_llm(
     raise UnknownProviderError(f"unknown llm_provider {provider!r}")


+def _refuse_foreign_model(provider: str, model: str) -> None:
+    owner = model_provider(model)
+    if provider in KEY_ENV and owner not in (None, provider):
+        raise ModelProviderMismatchError(
+            f"model {model!r} belongs to {owner}; the declared llm_provider is "
+            f"{provider}. Unset the model to use the provider's default."
+        )
+
+
 def key_env_var(provider: str) -> str:
     """Return the env var holding this provider's key."""
     try:
```

`agents/deliberator/settings.py` — diff against `main`:

```diff
diff --git a/agents/deliberator/settings.py b/agents/deliberator/settings.py
index 9f1176ed..a45589a8 100644
--- a/agents/deliberator/settings.py
+++ b/agents/deliberator/settings.py
@@ -84,9 +84,14 @@ class DeliberatorSettings(AgentSettings):
             "provider's own default, so switching provider is one switch."
         ),
     )
-    effort: Effort = tunable(
-        "max",
-        why="Anthropic output_config effort for deliberation calls.",
+    effort: Effort | Literal[""] = tunable(
+        "",
+        why=(
+            "Reasoning effort for deliberation calls. Empty sends none: Anthropic's "
+            "client uses max, OpenAI's the vendor default. A fixed default would be "
+            "refused by some vendor (gpt-5.5 answers HTTP 400 to max); the master "
+            "hands each role its chosen candidate's effort at activation (DL-289)."
+        ),
     )
     max_tokens: int = tunable(
         16384,
```

`agents/deliberator/entrypoint.py` — diff against `main`:

```diff
diff --git a/agents/deliberator/entrypoint.py b/agents/deliberator/entrypoint.py
index 05d24d9f..b5c5a5ae 100644
--- a/agents/deliberator/entrypoint.py
+++ b/agents/deliberator/entrypoint.py
@@ -2,7 +2,7 @@

 Agent: deliberator
 Role: activate one deliberator role, then graph-pull as manager or serve as peer.
-External I/O: master HTTP endpoint, graph store, Service Bus, Anthropic API.
+External I/O: master HTTP endpoint, graph store, Service Bus, the chosen LLM API.
 """

 from __future__ import annotations
@@ -15,12 +15,15 @@ from agents.deliberator.settings import DeliberatorSettings
 from kernel import AzureServiceBusSettings, CollectingFaultSink, InProcessBus
 from kernel.bootstrap import activate_agent, master_public_key_from_env
 from kernel.fault_graph import GraphFaultSink
+from kernel.llm_factory import build_llm, key_env_var
 from kernel.serve_loop import serve_loop
 from kernel.serve_transport import consumer_from_env

 PEER_SERVE_IDLE_SLEEP_SECONDS = 0

 if TYPE_CHECKING:
+    from collections.abc import Callable, Mapping
+
     from agents.deliberator.peer_client import PeerClient
     from kernel import FaultSink, GraphStore, LLMClient, MessageBus

@@ -60,6 +63,35 @@ def build_manager(
     )


+def activated_settings(
+    settings: DeliberatorSettings,
+    master_url: str,
+    public_key_pem: str | None,
+    activate: Callable[..., object] = activate_agent,
+) -> DeliberatorSettings:
+    """EHLO as this role, then re-read settings so the master's hand-over applies.
+
+    The master names the role's vendor, model and effort in ACTIVATE's config,
+    which lands in the process environment (DL-289); settings read before it
+    would run the role on the image's defaults.
+    """
+    activate(master_url, settings.identity, public_key_pem=public_key_pem)
+    return DeliberatorSettings()
+
+
+def build_role_llm(
+    settings: DeliberatorSettings, environ: Mapping[str, str]
+) -> LLMClient:
+    """Build the role's client on the vendor, model and effort it was handed."""
+    return build_llm(
+        settings.llm_provider,
+        api_key=environ.get(key_env_var(settings.llm_provider)),
+        model=settings.model_for_role(settings.peer_role or "judge"),
+        max_tokens=settings.max_tokens,
+        effort=settings.effort or None,
+    )
+
+
 def serve_peer(
     graph: GraphStore, settings: DeliberatorSettings, llm: LLMClient | None
 ) -> None:
@@ -82,21 +114,15 @@ def main() -> None:  # pragma: no cover

     from agents.deliberator.poll import find_pending, review_pm_node
     from kernel.graph_env import build_graph_from_env
-    from kernel.llm_factory import build_llm, key_env_var
     from kernel.work_loop import work_loop

-    settings = DeliberatorSettings()
-    master_url = os.environ.get("MASTER_URL", "http://master:8000")
-    pubkey = master_public_key_from_env()
-    activate_agent(master_url, settings.identity, public_key_pem=pubkey)
-    graph = build_graph_from_env()
-    llm = build_llm(
-        settings.llm_provider,
-        api_key=os.environ.get(key_env_var(settings.llm_provider)),
-        model=settings.model_for_role(settings.peer_role or "judge"),
-        max_tokens=settings.max_tokens,
-        effort=settings.effort,
+    settings = activated_settings(
+        DeliberatorSettings(),
+        os.environ.get("MASTER_URL", "http://master:8000"),
+        master_public_key_from_env(),
     )
+    graph = build_graph_from_env()
+    llm = build_role_llm(settings, os.environ)
     if settings.role == "manager":
         fault_sink = GraphFaultSink(graph, CollectingFaultSink())
         manager, peer_client = build_manager(graph, settings, llm=llm, sink=fault_sink)
```

`agents/deliberator/review_record.py` — diff against `main`:

```diff
diff --git a/agents/deliberator/review_record.py b/agents/deliberator/review_record.py
index 89764d1b..52b38afc 100644
--- a/agents/deliberator/review_record.py
+++ b/agents/deliberator/review_record.py
@@ -8,11 +8,12 @@ External I/O: none.
 from __future__ import annotations

 from dataclasses import dataclass
-from typing import TYPE_CHECKING
+from typing import TYPE_CHECKING, Literal

 if TYPE_CHECKING:
     from agents.deliberator.settings import DeliberatorSettings
     from contracts.deliberator import DebateProposition, DebateTurnRecord
+    from kernel import GraphStore

 _FAILED_OPEN_REASON_LIMIT = 500
 _UNKNOWN_FAIL_OPEN_REASON = "UnknownError: reason unavailable"
@@ -113,15 +114,32 @@ def narrative(debates: dict[str, object]) -> str:
     )


-def role_models(settings: DeliberatorSettings) -> dict[str, str]:
-    """Return the three *resolved* models stamped on a DeliberationRun.
+def role_models(
+    settings: DeliberatorSettings,
+    graph: GraphStore | None = None,
+    llm_call_keys: tuple[str, ...] | list[str] = (),
+) -> dict[str, str]:
+    """Return the three models stamped on a DeliberationRun: the ones that answered.

-    Reads through `model_for_role` rather than the tunables, so the audit record
-    names the model that actually answered — never the empty sentinel, and never
-    the other vendor's name after a provider switch (DL-100).
+    Each role's entry is read from the run's own `LLMCall` rows by the identity
+    that served it, because every replica chooses its LLM at activation (DL-289)
+    and two replicas of one role may run on different models; several models
+    are joined, sorted. A role with no row falls back to `model_for_role`: never
+    the empty sentinel, never the other vendor's name (DL-100).
     """
+    answered: dict[str, set[str]] = {}
+    for key in llm_call_keys:
+        node = graph.get_node("LLMCall", key) if graph is not None else None
+        if node is not None and isinstance(node.props.get("model"), str):
+            agent = str(node.props.get("calling_agent", ""))
+            answered.setdefault(agent, set()).add(str(node.props["model"]))
+    served: tuple[tuple[Literal["defender", "challenger", "judge"], str], ...] = (
+        ("defender", settings.proponent_identity),
+        ("challenger", settings.opponent_identity),
+        ("judge", settings.identity),
+    )
     return {
-        "defender": settings.model_for_role("defender"),
-        "challenger": settings.model_for_role("challenger"),
-        "judge": settings.model_for_role("judge"),
+        role: ", ".join(sorted(answered.get(identity, ())))
+        or settings.model_for_role(role)
+        for role, identity in served
     }
```

`agents/deliberator/poll.py` — diff against `main`:

```diff
diff --git a/agents/deliberator/poll.py b/agents/deliberator/poll.py
index f54135d4..d0e4085d 100644
--- a/agents/deliberator/poll.py
+++ b/agents/deliberator/poll.py
@@ -76,7 +76,7 @@ def review_pm_node(
         debates=batch.debates,
         narrative=narrative(batch.debates),
         transcript=batch.transcript,
-        role_models=role_models(settings),
+        role_models=role_models(settings, graph, batch.llm_call_keys),
         max_rounds=settings.max_rounds,
         real_debate_count=batch.real_debate_count,
         failed_open_count=len(batch.failed_open_tickers),
```

`scripts/guided_turn_replay.py` — diff against `main`:

```diff
diff --git a/scripts/guided_turn_replay.py b/scripts/guided_turn_replay.py
index 9eb99207..88fd74c1 100644
--- a/scripts/guided_turn_replay.py
+++ b/scripts/guided_turn_replay.py
@@ -159,7 +159,7 @@ def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI wiring
             api_key=os.environ.get(key_env_var(settings.llm_provider)),
             model=settings.model_for_role(role),
             max_tokens=settings.max_tokens,
-            effort=settings.effort,
+            effort=settings.effort or None,
         )
         for role in roles
     }
```

### 7. The brief's line — `orchestration/llm_brief.py` (new); `daily_brief_text.py`, `daily_brief_facts.py`, `orchestration/Dockerfile`

`orchestration/llm_brief.py` — new, 47 lines:

```python
"""The daily brief's LLM line: which roles ran on a later candidate, and why.

Agent: orchestration
Role: say in one line when an LLM role was activated on anything but its first
      working candidate in the last day (DL-289 P2).
External I/O: reads the injected GraphStore.

No line when every role ran on its first candidate, so a quiet night briefs as
before. The master records the choice on each `AgentInstance` it activates.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from orchestration.daily_brief_fills import parse_instant

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore

BRIEF_WINDOW = timedelta(hours=24)
_SEP = " · "


def llm_line(graph: GraphStore, *, now: datetime) -> str | None:
    """Return the brief's LLM line, or None when no candidate was passed over."""
    since = now - BRIEF_WINDOW
    groups: dict[tuple[str, tuple[str, ...]], set[str]] = {}
    for node in graph.list_nodes("AgentInstance"):
        started = parse_instant(node.props.get("started_at"))
        over = node.props.get("llm_passed_over")
        stale = started is None or started < since
        if stale or not isinstance(over, (list, tuple)) or not over:
            continue
        chosen = str(node.props.get("llm_candidate", ""))
        key = (chosen, tuple(str(line) for line in over))
        groups.setdefault(key, set()).add(str(node.props.get("agent_type", "")))
    if not groups:
        return None
    parts = [
        f"{', '.join(sorted(types))} on {chosen} (passed over {'; '.join(over)})"
        for (chosen, over), types in sorted(groups.items())
    ]
    return f"LLM: {_SEP.join(parts)}"
```

`orchestration/daily_brief_text.py` — diff against `main`:

```diff
diff --git a/orchestration/daily_brief_text.py b/orchestration/daily_brief_text.py
index 22fc186d..e02721ff 100644
--- a/orchestration/daily_brief_text.py
+++ b/orchestration/daily_brief_text.py
@@ -70,11 +70,12 @@ class BriefFacts:
     critical_flags: int = 0
     last_stage: str | None = None
     containers: str | None = None
+    llm: str | None = None


 def compose_brief(facts: BriefFacts) -> str:
     """Return the plain-text message; a run with no report gets the RED brief."""
-    sensed = (facts.containers,) if facts.containers else ()
+    sensed = tuple(line for line in (facts.containers, facts.llm) if line)
     if facts.verdict == NOT_FINISHED:
         stage = (
             f"Last stage finished: {facts.last_stage}"
```

`orchestration/daily_brief_facts.py` — diff against `main`:

```diff
diff --git a/orchestration/daily_brief_facts.py b/orchestration/daily_brief_facts.py
index 9fcb69fd..d49d3bb5 100644
--- a/orchestration/daily_brief_facts.py
+++ b/orchestration/daily_brief_facts.py
@@ -28,6 +28,7 @@ from orchestration.daily_brief_text import (
     BriefFacts,
     local_stamp,
 )
+from orchestration.llm_brief import llm_line
 from orchestration.packs.trading_acceptance import accept_run
 from orchestration.packs.trading_observatory_views import SPEC

@@ -73,6 +74,7 @@ def brief_facts(
         critical_flags=health["pending_human_flags"],
         last_stage=_last_stage(nodes),
         containers=container_line(graph, now=now, timezone=timezone),
+        llm=llm_line(graph, now=now),
     )
     snapshot = nodes.get("Snapshot")
     if snapshot is None or pm_run is None:
```

`orchestration/Dockerfile` — diff against `main`:

```diff
diff --git a/orchestration/Dockerfile b/orchestration/Dockerfile
index 5263c245..d18fde05 100644
--- a/orchestration/Dockerfile
+++ b/orchestration/Dockerfile
@@ -68,6 +68,7 @@ COPY orchestration/batch_chain.py orchestration/batch_chain.py
 COPY orchestration/batch_trace.py orchestration/batch_trace.py
 COPY orchestration/container_alarm_text.py orchestration/container_alarm_text.py
 COPY orchestration/container_brief.py orchestration/container_brief.py
+COPY orchestration/llm_brief.py orchestration/llm_brief.py
 COPY orchestration/container_events.py orchestration/container_events.py
 COPY orchestration/container_lines.py orchestration/container_lines.py
 COPY orchestration/container_logs.py orchestration/container_logs.py
```

### 8. The packs — `trading_llm.json`, `trading_credential_tests.json`, `trading_graph_vocabulary.json`

`orchestration/packs/trading_llm.json` — diff against `main`:

```diff
diff --git a/orchestration/packs/trading_llm.json b/orchestration/packs/trading_llm.json
index 363014eb..8c4d2163 100644
--- a/orchestration/packs/trading_llm.json
+++ b/orchestration/packs/trading_llm.json
@@ -1,11 +1,31 @@
 {
-  "_comment": "One declared LLM provider for the fleet. infra/deploy-agents.ps1 and scripts/switch_llm_provider.py read this file; its provider wins over trading_tunables.json for every app environment key named here. App order is apply order, with the master first.",
-  "provider": "openai",
+  "_comment": "The fleet's LLM declaration (DL-282, DL-289). candidates: the ordered ways an LLM role may run, each a vendor, a model and an effort, the preferred first. The master probes an agent type in roles with each candidate in order at every activation and hands it the first that works; the vendor of the first candidate is the declared provider, written by infra/deploy-agents.ps1 and scripts/switch_llm_config.py into each app key under apps (master first), and the master puts that vendor's candidates first. roles: the configuration keys each choosing agent type is handed its candidate in.",
+  "candidates": [
+    { "vendor": "openai", "model": "gpt-5.5", "effort": "high" },
+    { "vendor": "anthropic", "model": "claude-opus-5", "effort": "max" }
+  ],
   "apps": {
     "master": "MASTER_LLM_PROVIDER",
     "operator": "OPERATOR_LLM_PROVIDER",
     "deliberator-manager": "DELIBERATOR_LLM_PROVIDER",
     "deliberator-proponent": "DELIBERATOR_LLM_PROVIDER",
     "deliberator-opponent": "DELIBERATOR_LLM_PROVIDER"
+  },
+  "roles": {
+    "deliberator-manager": {
+      "vendor": "DELIBERATOR_LLM_PROVIDER",
+      "model": "DELIBERATOR_JUDGE_MODEL",
+      "effort": "DELIBERATOR_EFFORT"
+    },
+    "deliberator-proponent": {
+      "vendor": "DELIBERATOR_LLM_PROVIDER",
+      "model": "DELIBERATOR_DEFENDER_MODEL",
+      "effort": "DELIBERATOR_EFFORT"
+    },
+    "deliberator-opponent": {
+      "vendor": "DELIBERATOR_LLM_PROVIDER",
+      "model": "DELIBERATOR_CHALLENGER_MODEL",
+      "effort": "DELIBERATOR_EFFORT"
+    }
   }
 }
```

`orchestration/packs/trading_credential_tests.json` — diff against `main`:

```diff
diff --git a/orchestration/packs/trading_credential_tests.json b/orchestration/packs/trading_credential_tests.json
index 54be33d8..312d5db4 100644
--- a/orchestration/packs/trading_credential_tests.json
+++ b/orchestration/packs/trading_credential_tests.json
@@ -121,8 +121,9 @@
         "max_tokens": 1,
         "messages": [{ "role": "user", "content": "." }]
       },
+      "candidate_paths": { "model": ["model"], "effort": ["output_config", "effort"] },
       "expected_statuses": [200],
-      "credential_failure_statuses": [400, 401, 403, 429],
+      "credential_failure_statuses": [400, 401, 403, 404, 429],
       "required": true,
       "cost": "cheap"
     },
@@ -138,8 +139,9 @@
         "max_completion_tokens": 256,
         "messages": [{ "role": "user", "content": "." }]
       },
+      "candidate_paths": { "model": ["model"], "effort": ["reasoning_effort"] },
       "expected_statuses": [200],
-      "credential_failure_statuses": [400, 401, 403, 429],
+      "credential_failure_statuses": [400, 401, 403, 404, 429],
       "required": true,
       "cost": "cheap"
     }
@@ -160,8 +162,9 @@
         "max_tokens": 1,
         "messages": [{ "role": "user", "content": "." }]
       },
+      "candidate_paths": { "model": ["model"], "effort": ["output_config", "effort"] },
       "expected_statuses": [200],
-      "credential_failure_statuses": [400, 401, 403, 429],
+      "credential_failure_statuses": [400, 401, 403, 404, 429],
       "required": true,
       "cost": "cheap"
     },
@@ -177,8 +180,9 @@
         "max_completion_tokens": 256,
         "messages": [{ "role": "user", "content": "." }]
       },
+      "candidate_paths": { "model": ["model"], "effort": ["reasoning_effort"] },
       "expected_statuses": [200],
-      "credential_failure_statuses": [400, 401, 403, 429],
+      "credential_failure_statuses": [400, 401, 403, 404, 429],
       "required": true,
       "cost": "cheap"
     }
@@ -199,8 +203,9 @@
         "max_tokens": 1,
         "messages": [{ "role": "user", "content": "." }]
       },
+      "candidate_paths": { "model": ["model"], "effort": ["output_config", "effort"] },
       "expected_statuses": [200],
-      "credential_failure_statuses": [400, 401, 403, 429],
+      "credential_failure_statuses": [400, 401, 403, 404, 429],
       "required": true,
       "cost": "cheap"
     },
@@ -216,8 +221,9 @@
         "max_completion_tokens": 256,
         "messages": [{ "role": "user", "content": "." }]
       },
+      "candidate_paths": { "model": ["model"], "effort": ["reasoning_effort"] },
       "expected_statuses": [200],
-      "credential_failure_statuses": [400, 401, 403, 429],
+      "credential_failure_statuses": [400, 401, 403, 404, 429],
       "required": true,
       "cost": "cheap"
     }
```

`orchestration/packs/trading_graph_vocabulary.json` — diff against `main`:

```diff
diff --git a/orchestration/packs/trading_graph_vocabulary.json b/orchestration/packs/trading_graph_vocabulary.json
index d0f0989e..5299c317 100644
--- a/orchestration/packs/trading_graph_vocabulary.json
+++ b/orchestration/packs/trading_graph_vocabulary.json
@@ -395,6 +395,8 @@
       "credential_tests_transport_failed",
       "drain_at",
       "drain_reason",
+      "llm_candidate",
+      "llm_passed_over",
       "started_at",
       "state"
     ],
@@ -493,6 +495,7 @@
       "checked_at",
       "failure_count",
       "failures",
+      "llm_passed_over",
       "passed"
     ],
     "RunHold": [
```

### 9. The deploy and the switch — `infra/deploy-agents.ps1`, `scripts/switch_llm_config.py`, `scripts/switch_llm_proof.py`

`infra/deploy-agents.ps1` — diff against `main`:

```diff
diff --git a/infra/deploy-agents.ps1 b/infra/deploy-agents.ps1
index 6b01081d..0c0fb579 100644
--- a/infra/deploy-agents.ps1
+++ b/infra/deploy-agents.ps1
@@ -15,7 +15,7 @@
 # POSTGRES_DSN is the schema/admin DSN; fleet roles use per-target DSNs.

 param(
-  [ValidateSet('preflight', 'up', 'postgres-flip', 'servicebus-flip', 'sensor', 'down')]
+  [ValidateSet('preflight', 'up', 'postgres-flip', 'servicebus-flip', 'sensor', 'llm-candidates', 'down')]
   [string]$Action = 'preflight',
   [string]$Tag = 'latest',
   # DL-294 amendment 1: one readiness check, at the wake, before the 22:30 UTC dispatch.
@@ -450,7 +450,8 @@ function Load-LlmPack {
 function Get-AppLlmEnv($name) {
   $pack = Load-LlmPack
   if (@($pack.apps.PSObject.Properties.Name) -notcontains $name) { return @() }
-  return @("$($pack.apps.$name)=$($pack.provider)")
+  # The first candidate's vendor is the declared provider (DL-289).
+  return @("$($pack.apps.$name)=$(@($pack.candidates)[0].vendor)")
 }

 function Resolve-DispatcherCron {
@@ -690,6 +691,13 @@ function Get-MasterCredentialTestsEnv {
   return "MASTER_CREDENTIAL_TESTS_B64=" + [Convert]::ToBase64String([IO.File]::ReadAllBytes($file))
 }

+function Get-MasterLlmPackEnv {
+  # The ordered LLM candidates ride the master's create call too (DL-289): the
+  # master expands them into the probes an LLM role is activated through.
+  $file = Join-Path $PSScriptRoot "..\orchestration\packs\trading_llm.json"
+  return "MASTER_LLM_PACK_B64=" + [Convert]::ToBase64String([IO.File]::ReadAllBytes($file))
+}
+
 function Get-IssuerMapEnv {
   # The issuer map is trading-pack data (ADR-0012), not a PM tunable. Inject it
   # as base64 so the portfolio-manager image stays pack-agnostic like master.
@@ -761,6 +769,28 @@ function Enable-ContainerSensor {
   return ($held -eq "1") -and $vocabOk
 }

+function Enable-LlmCandidates {
+  # DL-289: run BEFORE the retag that brings the master's S276 image. That image writes
+  # llm_passed_over on every fleet check and llm_candidate on a chosen activation, which
+  # the earlier vocabulary refuses; so the vocabulary goes first, then the candidate pack.
+  # An older image ignores both. Each step is read back, so a re-run is safe.
+  Top "LLM CANDIDATES"
+  $vocabOk = Set-AppVocabulary "master"
+  Check $vocabOk "graph vocabulary on master"
+  $state = $null
+  if ($vocabOk) {
+    $state = Invoke-Az @(
+      "containerapp", "update", "--name", "master", "--resource-group", $RG,
+      "--subscription", $SUB, "--set-env-vars", (Get-MasterLlmPackEnv),
+      "--query", "properties.provisioningState", "-o", "tsv"
+    )
+  }
+  $packOk = ($null -ne $state) -and ((Get-AppState "master") -eq "Succeeded")
+  Check $packOk "MASTER_LLM_PACK_B64 on master"
+  Bot
+  return $vocabOk -and $packOk
+}
+
 function Up {
   if (-not (Preflight)) { Write-Host "`nPreflight failed — fix the [XX] items above." -ForegroundColor Red; return }
   # Refuse before the first create, not after the ninth: a deploy that discards
@@ -789,7 +819,7 @@ function Up {
     "MASTER_GRAPH=auto",
     "MASTER_PRIVATE_KEY_PEM_B64=secretref:master-key-b64",
     "MASTER_GRANT_POLICY_B64=$grantB64", "MASTER_SECRET_MAP_B64=$secretB64",
-    (Get-MasterCredentialTestsEnv)
+    (Get-MasterCredentialTestsEnv), (Get-MasterLlmPackEnv)
   ) + (Get-AppLlmEnv "master")
   $masterGraph = Get-GraphConfig "master"
   $envv += @($masterGraph.envVars)
@@ -977,5 +1007,6 @@ switch ($Action) {
   'postgres-flip' { Flip-PostgresRoles }
   'servicebus-flip' { Flip-ServiceBusSas }
   'sensor' { if (-not (Enable-ContainerSensor)) { throw "container sensor not enabled" } }
+  'llm-candidates' { if (-not (Enable-LlmCandidates)) { throw "LLM candidates not enabled" } }
   'down' { Down }
 }
```

`scripts/switch_llm_config.py` — diff against `main`:

```diff
diff --git a/scripts/switch_llm_config.py b/scripts/switch_llm_config.py
index d27389c8..3f44aa52 100644
--- a/scripts/switch_llm_config.py
+++ b/scripts/switch_llm_config.py
@@ -40,7 +40,7 @@ def load_pack(root: Path) -> LlmPack:
     """Validate provider and target keys, reading vendor probe names as data."""
     packs = root / "orchestration/packs"
     raw = json.loads((packs / "trading_llm.json").read_text(encoding="utf-8"))
-    provider = raw["provider"]
+    provider = declared_provider(raw)
     apps = raw["apps"]
     if provider not in KEY_ENV:
         raise ValueError(f"unknown declared provider {provider!r}")
@@ -69,6 +69,17 @@ def load_pack(root: Path) -> LlmPack:
     return LlmPack(provider, apps, probes)


+def declared_provider(raw: dict[str, object]) -> str:
+    """The first candidate's vendor is the declared provider (DL-289)."""
+    candidates = raw["candidates"]
+    if not isinstance(candidates, list) or not candidates:
+        raise ValueError("the LLM pack declares no candidates")
+    first = candidates[0]
+    if not isinstance(first, dict):
+        raise ValueError("an LLM candidate must be an object")
+    return str(first["vendor"])
+
+
 def evidence_directory(value: str, root: Path) -> Path:
     """Refuse evidence files inside the repository, including resolved symlinks."""
     if not value:
```

`scripts/switch_llm_proof.py` — diff against `main`:

```diff
diff --git a/scripts/switch_llm_proof.py b/scripts/switch_llm_proof.py
index 131dd161..012ee03c 100644
--- a/scripts/switch_llm_proof.py
+++ b/scripts/switch_llm_proof.py
@@ -63,6 +63,10 @@ def missing_terms(


 def _valid_activation(props: Mapping[str, object], pack: LlmPack, app: str) -> bool:
+    chosen = props.get("llm_candidate")
+    if isinstance(chosen, str):
+        # An app that chooses among candidates proves the switch by its choice.
+        return chosen.startswith(f"{pack.provider}/")
     passed = props.get("credential_tests_passed")
     declared = props.get("credential_tests_declared")
     if not isinstance(passed, (tuple, list)) or not isinstance(declared, (tuple, list)):
```

### 10. The law books — master v1.11, deliberator v1.17, dispatcher v1.4

`agents/master/laws/laws.md` — diff against `main`:

```diff
diff --git a/agents/master/laws/laws.md b/agents/master/laws/laws.md
index 99afca33..3a01a99d 100644
--- a/agents/master/laws/laws.md
+++ b/agents/master/laws/laws.md
@@ -1,6 +1,6 @@
 # `Master` — Laws

-**Prefix:** `MST` · **status:** LOCKED v1.10 · **Owner:** Yury Gurevich
+**Prefix:** `MST` · **status:** LOCKED v1.11 · **Owner:** Yury Gurevich

 > Receive EHLO from freshly-started agent containers, verify declared capabilities,
 > distribute minimum-privilege credentials via ACTIVATE, and maintain the
@@ -64,7 +64,15 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   declared LLM provider for every agent type in the grant policy and writes one `FleetPreflight`
   node per check. An empty provider leaves every probe applicable. The check passes only if every
   probe passed or has a fresh costly-pass cache entry. A credential failure or a transport failure
-  fails it.
+  fails it. An LLM candidate passed over for a later one fails nothing (`MST-FAIL-08`); the node
+  lists each as `<agent type>: <vendor/model/effort>: <reason>` under `llm_passed_over`.
+- **MST-OUT-05** — An agent type named under `roles` in the pack's LLM declaration is activated on
+  the first declared candidate (a vendor, a model and an effort) whose probes pass, the declared
+  provider's candidates tried first, each group in declared order. Each candidate is probed with
+  its own model and effort; the ones after the first that passes are not probed. ACTIVATE's config
+  names the chosen vendor, model and effort under the role's three keys and holds no other vendor's
+  key. The `AgentInstance` records `llm_candidate` (`vendor/model/effort`) and `llm_passed_over`,
+  one `<vendor/model/effort>: <reason>` for each candidate tried before it.

 ## Never (`NEV`)

@@ -84,6 +92,12 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   key. Master refuses to start on an unknown non-empty provider, an unknown non-empty probe tag,
   or an agent type granted the declared vendor's key without a probe tagged for that vendor.
   An empty provider preserves the original probes and secret map after validating probe tags.
+  An agent type named under the LLM declaration's `roles` keeps every vendor's probes and keys at
+  start; `MST-OUT-05` withholds the vendors not chosen at each activation.
+- **MST-NEV-08** — Master refuses to start on an LLM declaration with no candidate, a candidate of an
+  unknown vendor, a model of another known vendor's family, a repeated candidate, a field that is not
+  a non-empty string, or a role whose agent type has, for some candidate, no probe of that vendor, a
+  probe that declares no `candidate_paths`, or no key of that vendor in the secret map.

 ## State & storage (`STA`)

@@ -155,6 +169,11 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   the setting that fixes it (`MASTER_REMEDIATION_MODE=manual`), so the switch is never silently
   inert. `manual` starts unchanged. *(DRIFT-059; the guard is `agents/master/remediation_posture.py`,
   S203.)*
+- **MST-FAIL-08** — An LLM candidate whose probes were refused or went unanswered, when a later
+  candidate passes, is neither a credential failure of the activation nor a failure of the fleet
+  check. When no candidate passes, the first whose probes were only unanswered is handed over
+  unproven, as `MST-FAIL-04` allows; when every candidate was refused, every refusal stands and the
+  activation is refused (`MST-NEV-06`).

 **Remediation is outside this constitution.** No clause governs *attempting* a remediation: what
 master may attempt, the one-shot bound, or what is recorded when an attempt fails. Those clauses are
@@ -211,7 +230,8 @@ guarantees.
 - **MST-OBS-03** — Fault channel receives all graph/Key Vault errors via `fault_boundary`.
 - **MST-OBS-04** — Successful activation records applicable credential-test evidence on the
   `AgentInstance`: live-tested names, live-passed names, cached-pass names, optional failures, and
-  transport failures.
+  transport failures; for an agent type that chose an LLM candidate, also the candidate and the ones
+  passed over (`MST-OUT-05`).
 - **MST-OBS-05** — A stop leaves two lines on the container's stderr. When the signal arrives:
   `[<agent>] stop signal <NAME>: taking no new work`, written unbuffered from the handler, so a
   process killed later still shows that it was told to stop. When the process has closed what it
@@ -247,7 +267,9 @@ guarantees.

 | Name | Value | Type | Tunable | Rationale |
 | --- | --- | --- | --- | --- |
-| `llm_provider` | `""` | `str` | YES | Declared vendor selects applicable probes and keys once at pack loading; empty preserves every declaration after validating tags (`MST-NEV-07`) |
+| `llm_provider` | `""` | `str` | YES | Declared vendor selects applicable probes and keys once at pack loading; empty preserves every declaration after validating tags (`MST-NEV-07`); an LLM role's candidates of this vendor are tried first (`MST-OUT-05`) |
+| `llm_pack_path` | `""` | `str` | YES | Filesystem path fallback for the pack's ordered LLM candidates and the agent types that choose among them (`MST-OUT-05`) |
+| `llm_pack_b64` | `""` | `str` | YES | Base64 environment delivery for the LLM candidate pack; wins over `llm_pack_path` |
 | `handshake_timeout_2_seconds` | `300.0` | `float ≥ 30.0 ≤ 600.0` | YES | Master's replay window (`MST-IDM-03`): seconds a resent EHLO with the same boot id and type gets the first ACTIVATE back; must be ≥ the kernel's EHLO budget (`ehlo_budget_seconds`, 300) so every resend is replayed |
 | `ehlo_listen_backlog` | `64` | `int ≥ 16 ≤ 1024` | YES | Listen backlog of master's EHLO server (`MST-ORD-03`); one wave is the 15 agent types waking together, and 64 holds four waves of resends |
 | `credential_tests_path` | `""` | `str` | YES | Filesystem path fallback for the master credential-test declaration pack |
@@ -273,6 +295,12 @@ guarantees.

 ## Changelog

+- v1.11 — S276 / DL-289 (2026-10-15): an LLM role runs on the first declared candidate that works.
+  New `MST-OUT-05` (the choice at activation and its record), `MST-NEV-08` (the start-time refusals
+  of a declaration no role could run on) and `MST-FAIL-08` (a passed-over candidate fails nothing).
+  `MST-OUT-04`, `MST-NEV-07` and `MST-OBS-04` amended for it. PARAM gains `llm_pack_path` and
+  `llm_pack_b64`. The single-vendor selection of every other agent type is unchanged.
+
 - v1.10 — S272 / DL-297 (2026-10-13): every container ends on the stop signal. New `MST-TRG-03`
   (the kernel's graph-pull and serve loops and master's server end on `SIGTERM`, close what they
   hold, exit `0` only when all of it closed), `MST-ORD-04` (master's order: listening socket,
```

`agents/deliberator/laws/laws.md` — diff against `main`:

```diff
diff --git a/agents/deliberator/laws/laws.md b/agents/deliberator/laws/laws.md
index a0152ed8..068593a2 100644
--- a/agents/deliberator/laws/laws.md
+++ b/agents/deliberator/laws/laws.md
@@ -1,6 +1,6 @@
 # `Deliberator` -- Laws

-**Prefix:** `DLIB` · **status:** LOCKED v1.16 · **Owner:** Yury Gurevich
+**Prefix:** `DLIB` · **status:** LOCKED v1.17 · **Owner:** Yury Gurevich

 > Adversarially review PM-approved orders with a bounded proponent/opponent debate
 > and a manager verdict before execution, subtracting unsafe orders only when the
@@ -48,7 +48,9 @@ ADR-0020; declaring is not proving, so every clause starts gray.
   `DeliberationRun` linked by `PMRun -DELIBERATED_BY-> DeliberationRun`.
 + **DLIB-OUT-02** -- Each `DeliberationRun` records verdicts, vetoed tickers
   containing only `overturn` verdicts, per-ticker debate turns, role models,
-  narrative, and creation time.
+  narrative, and creation time. A role's model is the one its `LLMCall` rows in
+  the run name for the identity that served it, several joined in sorted order;
+  a role with no row names its resolved setting.
 + **DLIB-OUT-03** -- Each LLM call writes a shared `LLMCall` with
   `calling_agent`, model, hashes, token counts, latency, and timestamp.
 + **DLIB-OUT-04** -- `overturn` verdicts may only subtract existing
@@ -88,6 +90,8 @@ ADR-0020; declaring is not proving, so every clause starts gray.

 + **DLIB-NEV-10** -- Never lets a library that builds or parses a role's prompt
   reach a model vendor except through the agent's own LLM client.
++ **DLIB-NEV-11** -- Never sends a vendor a model of another known vendor's
+  family: building the role's client refuses it.

 ## State & Effects (`STA`)

@@ -163,6 +167,9 @@ ADR-0020; declaring is not proving, so every clause starts gray.
 + **DLIB-DEP-02** -- `DEP-BUS` for manager-to-peer request/reply.
 + **DLIB-DEP-03** -- `DEP-LLM` for external model calls and fail-open behaviour.
 + **DLIB-DEP-04** -- `DEP-CONFIG` for role, round, model, and credential settings.
++ **DLIB-DEP-05** -- Each role runs on the vendor, model and effort its settings
+  hold after activation, so the ones the master handed it (DL-289) and never the
+  values read before. An empty effort sends the vendor none.

 ## Observability & Audit (`OBS`)

@@ -226,7 +233,7 @@ ADR-0020; declaring is not proving, so every clause starts gray.
 | `defender_model` | empty | string | YES | Proponent role model; empty resolves the provider default |
 | `challenger_model` | empty | string | YES | Opponent role model; empty resolves the provider default |
 | `judge_model` | empty | string | YES | Manager verdict model; empty resolves the provider default |
-| `effort` | `max` | enum | YES | Anthropic reasoning effort |
+| `effort` | `""` | enum or empty | YES | Reasoning effort for deliberation calls; empty sends none (Anthropic's client uses max, OpenAI the vendor default), because a fixed default is refused by some vendor (gpt-5.5 answers HTTP 400 to max); the master hands each role its candidate's effort at activation (DL-289) |
 | `max_tokens` | `16384` | int >= 64 <= 16384 | YES | Per-call response cap; S246 raised it for the guided readings written before each debater's argument (challenger max 3,026 output tokens before them, DL-252 D8); on gpt-5.5 reasoning counts against the cap, a defender reached 7,738 tokens in production and 11,556 in the typed turn, and the unused cap costs nothing (DL-274 D1) |
 | `request_timeout_seconds` | `30.0` | float >= 1 <= 300 | YES | Bounds peer RPC wait; a turn at the cap can take about 190 seconds at the slowest measured output rate on gpt-5.5 (DL-274 D3) |
 | `debate_concurrency` | `4` | int >= 1 <= 25 | YES | Manager fan-out over independent PM-approved orders, bounded by the vendor rate limit because each concurrent order holds one in-flight completion per peer role |
@@ -335,3 +342,7 @@ ADR-0020; declaring is not proving, so every clause starts gray.
   16,384 with the same ceiling, below Anthropic's 21,333 non-streaming limit;
   `request_timeout_seconds` may reach 300, still defaulting to 30. Measured
   gpt-5.5 reasoning needs the cap and can take about 190 seconds at it. No clause changes.
++ v1.17 -- S276 / DL-289 (2026-10-15). Adds and proves `DLIB-DEP-05` (a role
+  runs on what the master handed it at activation) and `DLIB-NEV-11` (no model
+  of another vendor's family is sent); amends and proves `DLIB-OUT-02` (role
+  models are the ones that answered). PARAM: `effort` defaults to empty.
```

`orchestration/laws/dispatcher/laws.md` — diff against `main`:

```diff
diff --git a/orchestration/laws/dispatcher/laws.md b/orchestration/laws/dispatcher/laws.md
index 81e697e4..c7c0d3f6 100644
--- a/orchestration/laws/dispatcher/laws.md
+++ b/orchestration/laws/dispatcher/laws.md
@@ -1,6 +1,6 @@
 # `Dispatcher` — Laws

-**Prefix:** `DSP` · **status:** LOCKED v1.3 · **Owner:** Yury Gurevich
+**Prefix:** `DSP` · **status:** LOCKED v1.4 · **Owner:** Yury Gurevich

 > Decide whether the scheduled daily graph-pull run is placed, skipped, held, or placed in degraded posture,
 > brief the operator once on each run it placed, and tell the operator when a container of the
@@ -113,6 +113,11 @@ green only when a functional test cites its ID (conventions §3). Tests + status

 ## Prohibitions (`NEV`)

+- **DSP-OUT-09** — A brief whose last 24 hours hold an `AgentInstance` activated on an LLM candidate
+  after passing over another carries one line after the container line and before needs-you:
+  `LLM: ` then, for each distinct choice and passed-over list, the agent types sorted, ` on ` the
+  chosen `vendor/model/effort`, and in brackets `passed over ` each passed-over line, the parts
+  joined by ` · `. With no such activation there is no line.
 - **DSP-NEV-01** — The scheduled dispatcher never writes master-owned `FleetPreflight` evidence.
 - **DSP-NEV-02** — The scheduled dispatcher never talks to the broker, never chooses tickers beyond
   the configured universe membership, and never decides what to buy, sell, size, or veto.
@@ -191,8 +196,8 @@ green only when a functional test cites its ID (conventions §3). Tests + status
 - **DSP-DEP-01** — The scheduled dispatcher depends on the graph store (`DEP-POSTGRES`), UTC clock
   (`DEP-CLOCK`), provider-owned market calendar, configured universe source, and Telegram port for
   optional operator notices, answers, and the daily brief. For the brief its graph reads include the
-  run's chain to its `Snapshot`, `Fill`, `Fault` and `Flag` facts with their resolutions, and the
-  pack's acceptance verdict. The sensor depends on the job's managed-identity endpoint and the log
+  run's chain to its `Snapshot`, `Fill`, `Fault` and `Flag` facts with their resolutions, the
+  master's `AgentInstance` records of the last 24 hours, and the pack's acceptance verdict. The sensor depends on the job's managed-identity endpoint and the log
   workspace's query API.

 ## Observability & audit (`OBS`)
@@ -224,7 +229,7 @@ green only when a functional test cites its ID (conventions §3). Tests + status
       "FleetPreflight", "RunRequest", "RunHold", "RunHoldAnswer", "MarketData", "ScanRun",
       "AnalystRun", "PMRun", "DeliberationRun", "OrderIntent", "ExecutionRun", "MonitorRun",
       "Snapshot", "Fill", "Fault", "FaultResolution", "Flag", "FlagResolution",
-      "BrokerPositionSnapshot", "ContainerEvent", "ContainerSensorRead"
+      "BrokerPositionSnapshot", "ContainerEvent", "ContainerSensorRead", "AgentInstance"
     ],
     "access": "bounded dispatcher placement; the brief marks only its own RunRequest"
   },
@@ -285,3 +290,5 @@ green only when a functional test cites its ID (conventions §3). Tests + status
   `DSP-TRG-04`, `DSP-OUT-07`, `DSP-OUT-08`, `DSP-NEV-03`, `DSP-IDM-04`, `DSP-FAIL-04`, `DSP-SEC-03` and
   `DSP-OBS-03`; the purpose line, `DSP-IDN-03`'s scope sentence, `DSP-DEP-01`, `CAP` and `PARAM`
   amended for it.
+- v1.4 — S276 (DL-289, work-queue 123): the brief's LLM line. New `DSP-OUT-09`; `DSP-DEP-01` and
+  `CAP` amended for the `AgentInstance` read.
```

### 11. The five existing test edits

`agents/master/tests/test_provider_selection_refusals.py` — diff against `main`:

```diff
diff --git a/agents/master/tests/test_provider_selection_refusals.py b/agents/master/tests/test_provider_selection_refusals.py
index fb661330..4392484a 100644
--- a/agents/master/tests/test_provider_selection_refusals.py
+++ b/agents/master/tests/test_provider_selection_refusals.py
@@ -76,10 +76,13 @@ def test_selection_runs_once_when_building_master(
     real_selection = select_llm_provider

     def selection(
-        provider: str, tests: tuple[CredentialTest, ...], secrets: SecretMap | None
+        provider: str,
+        tests: tuple[CredentialTest, ...],
+        secrets: SecretMap | None,
+        roles: tuple[str, ...] = (),
     ) -> tuple[tuple[CredentialTest, ...], SecretMap | None]:
         calls.append(provider)
-        return real_selection(provider, tests, secrets)
+        return real_selection(provider, tests, secrets, roles)

     monkeypatch.setattr(entrypoint, "select_llm_provider", selection)
     monkeypatch.setattr(
```

`agents/master/tests/test_fleet_preflight_packs.py` — diff against `main`:

```diff
diff --git a/agents/master/tests/test_fleet_preflight_packs.py b/agents/master/tests/test_fleet_preflight_packs.py
index af283b84..29b5c175 100644
--- a/agents/master/tests/test_fleet_preflight_packs.py
+++ b/agents/master/tests/test_fleet_preflight_packs.py
@@ -39,4 +39,5 @@ def test_vocabulary_declares_fleet_preflight_and_its_properties() -> None:
         "failure_count",
         "failures",
         "agent_types_checked",
+        "llm_passed_over",
     }
```

`tests/test_deploy_llm_pack.py` — diff against `main`:

```diff
diff --git a/tests/test_deploy_llm_pack.py b/tests/test_deploy_llm_pack.py
index baf34cf3..0a1e5ec0 100644
--- a/tests/test_deploy_llm_pack.py
+++ b/tests/test_deploy_llm_pack.py
@@ -20,7 +20,7 @@ def test_c1_llm_pack_names_real_apps_and_settings() -> None:
     pack = json.loads(
         (ROOT / "orchestration/packs/trading_llm.json").read_text("utf-8")
     )
-    assert pack["provider"] in KEY_ENV
+    assert pack["candidates"][0]["vendor"] in KEY_ENV
     script = (ROOT / "infra/deploy-agents.ps1").read_text("utf-8")
     block = script.split("$AGENTS = [ordered]@{", 1)[1].split("}", 1)[0]
     names = set(re.findall(r'["\']?([a-z][a-z-]+)["\']?\s*=\s*"', block)) | {"master"}
```

`tests/test_switch_llm_config.py` — diff against `main`:

```diff
diff --git a/tests/test_switch_llm_config.py b/tests/test_switch_llm_config.py
index 78360e95..af06bf55 100644
--- a/tests/test_switch_llm_config.py
+++ b/tests/test_switch_llm_config.py
@@ -21,7 +21,15 @@ def test_invalid_target_map_refuses_before_azure(tmp_path: Path, apps: object) -
     packs = tmp_path / "root/orchestration/packs"
     packs.mkdir(parents=True)
     (packs / "trading_llm.json").write_text(
-        json.dumps({"provider": "openai", "apps": apps}), encoding="utf-8"
+        json.dumps(
+            {
+                "candidates": [
+                    {"vendor": "openai", "model": "gpt-5.5", "effort": "high"}
+                ],
+                "apps": apps,
+            }
+        ),
+        encoding="utf-8",
     )
     (packs / "trading_credential_tests.json").write_text(
         (ROOT / "orchestration/packs/trading_credential_tests.json").read_text(
@@ -41,7 +49,15 @@ def test_missing_selected_probe_refuses_before_azure(tmp_path: Path) -> None:
     packs = tmp_path / "root/orchestration/packs"
     packs.mkdir(parents=True)
     (packs / "trading_llm.json").write_text(
-        json.dumps({"provider": "openai", "apps": APPS}), encoding="utf-8"
+        json.dumps(
+            {
+                "candidates": [
+                    {"vendor": "openai", "model": "gpt-5.5", "effort": "high"}
+                ],
+                "apps": APPS,
+            }
+        ),
+        encoding="utf-8",
     )
     (packs / "trading_credential_tests.json").write_text("{}", encoding="utf-8")
     azure = FakeAzure()
```

`tests/test_switch_llm_refusals.py` — diff against `main`:

```diff
diff --git a/tests/test_switch_llm_refusals.py b/tests/test_switch_llm_refusals.py
index 1650a534..43f727f2 100644
--- a/tests/test_switch_llm_refusals.py
+++ b/tests/test_switch_llm_refusals.py
@@ -69,7 +69,14 @@ def test_d3_unknown_provider_refuses_before_azure(tmp_path: Path) -> None:
     packs = tmp_path / "root/orchestration/packs"
     packs.mkdir(parents=True)
     (packs / "trading_llm.json").write_text(
-        json.dumps({"provider": "opnai", "apps": {"master": "MASTER_LLM_PROVIDER"}})
+        json.dumps(
+            {
+                "candidates": [
+                    {"vendor": "opnai", "model": "gpt-5.5", "effort": "high"}
+                ],
+                "apps": {"master": "MASTER_LLM_PROVIDER"},
+            }
+        )
     )
     (packs / "trading_credential_tests.json").write_text("{}", encoding="utf-8")
     azure = FakeAzure()
```
