<!-- Agent: planning | Role: sprint handover -->
# Sprint 262 — the fleet's LLM vendor is one declared value, and one command applies it and proves it

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it`
**Status:** BUILT
**Version:** *next available MINOR at merge*
**Effort:** L
**Decisions:** [DL-282](../design-log.md) (this sprint's ten decisions, made) · [DL-265](../design-log.md) (the hand-made switch it replaces) · DL-100 (the models follow the provider) · [work-queue 109](../work-queue.md)

> **Why this bump kind.** The operator's chat gains a second vendor and the repository gains a
> command that changes the fleet: new capability, so MINOR.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md`, `surfaces/laws/laws.md` | One component's **locked constitution** | **LOCKED.** This sprint amends three of them under a law cycle, named below. Any other clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: master **`OUT`**, **`NEV`**, **`SEC`**, **`PARAM`**; operator **`DEP`**,
**`PARAM`**; surfaces **`DEP`**, **`IN`**.

### The rule

1. **Before writing code**, read every law file in the map below, whole.
2. Read each component's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It is answered for you; confirm it against what you read.
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No file in `contracts/` changes, and none may** (it is a fidelity decision path, see the invariant
below). **Yes, three components gain or change a guarantee**, so three law cycles are owed in this
unit of work:

| Book | From | What the cycle owes |
| --- | --- | --- |
| `agents/master/laws/laws.md` | LOCKED v1.8 | `MST-OUT-04` reworded: the fleet check tests every pack-declared probe **that applies under the declared LLM provider**. One new clause, next free ID in `NEV`: the master never hands an agent the key of an LLM vendor other than the declared one, and refuses to start on an unknown provider, an unknown probe tag, or a granted vendor key with no probe. `PARAM` row `llm_provider`. Changelog line, version up |
| `agents/operator/laws/laws.md` | LOCKED v1.4 | `OPR-DEP-01` names the declared provider instead of one vendor. `PARAM`: new row `llm_provider`; `model` Value becomes `""` with the resolve rule in its Rationale; `effort` Rationale no longer says "Anthropic". Changelog line, version up |
| `surfaces/laws/laws.md` | LOCKED v1.3 | One new clause, next free ID in `DEP`: the dashboard chat is served by the operator's declared provider and by no other, and a missing key for that provider reads as disconnected. Changelog line, version up |

Each new or reworded clause gets a `test-plan.md` row, its ID cited in the test docstring, and the
rollup updated in **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md`.
🪤 **The rollup is derived, not declared.** `make ci` recomputes it. Let the gate tell you the number.
🪤 **The parameter step compares every `PARAM` row's Value and bounds with the code** (S258). A new
settings field with no row, or a row whose Value differs from the default, fails the gate. That is
measured for this sprint, see the table below.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/master/entrypoint.py`, `settings.py`, `credential_test.py`, `credential_probes.py`, the new selection module | `agents/master/laws/laws.md` + `test-plan.md` | `MST-OUT-04` (what the fleet check tests), `MST-NEV-06` (no credential handed over before its applicable tests pass), `MST-SEC-*`, the `PARAM` table |
| `agents/operator/settings.py`, `agents/operator/agent.py` | `agents/operator/laws/laws.md` + `test-plan.md` | `OPR-DEP-01`, the `PARAM` table |
| `surfaces/dashboard/chat_binding.py` | `surfaces/laws/laws.md` + `test-plan.md` | `SRF-DEP-01`, `SRF-DEP-02`, `SRF-IN-03` (unbound chat reports disconnection) |
| `kernel/llm_factory.py`, the new OpenAI operator adapter | `docs/laws/conventions.md`; `tests/test_llm_adapter_ownership.py` and `tests/test_llm_adapter_security.py` (read both whole: they are the kernel's rules for adapters) | S222: vendor adapters live only in `kernel/`; a selected vendor's failure never builds another vendor |
| `orchestration/packs/trading_credential_tests.json`, `trading_secrets.json`, the new `trading_llm.json` | `agents/master/laws/laws.md`; `orchestration/laws/laws.md` (read only) | `MST-NEV-06`; the packs are trading-pack data the master receives at deploy (ADR-0012) |
| `agents/deliberator/settings.py` (**read only, do not edit**) | `agents/deliberator/laws/laws.md`, `PARAM` row `llm_provider` | DL-99 / DL-100: the vendor is an operator act, never a fallback; the models follow the provider |
| `infra/deploy-agents.ps1` | `tests/test_deploy_script_invariants.py`, `tests/test_deploy_tunables_pack.py` (read both whole) | `make ci` cannot read PowerShell; these tests are the only gate the script has |

⚠️ **The one invariant this sprint must not break: no file under a fidelity decision path changes.**
The paths are `agents/scanner/`, `agents/analyst/`, `agents/portfolio_manager/`,
`agents/provider/domain/`, `agents/execution/order_tolerance.py`, `contracts/`,
`orchestration/packs/trading_tunables.json`, `orchestration/packs/trading_issuer_map.json` and
`orchestration/history_window.py` (`scripts/replay_fidelity_git.py:21-31`). A deploy that carries a
change to any of them resets a count the project has been waiting on since 2026-10-02. **If your build
needs one of them changed, even a comment or a test under those folders, stop and report.** The
tunables pack keeps its three `DELIBERATOR_LLM_PROVIDER` lines; this sprint overrides them and does
not delete them.

---

## Goal

At merge, one file states which LLM vendor the fleet uses. The three deliberators, the operator
agent, the operator's dashboard chat and the master's credential probes all follow that one value:
only the declared vendor's probes are run and counted, and only its key is handed to an agent. A full
`up` deploys that value and no longer reverts it. One command reads the file, sets the value on the
five live apps, checks that nothing else on them moved, and reads the graph for the proof (a fleet
check that passed and the activations of the apps it changed). Switching back is the same file and
the same command.

## Why (context)

On 2026-10-06 the Anthropic account ran empty and the operator said: *"re-wire for Chat GPT and get
the pipeline going"*, and, watching it done by hand, *"that SHOULD be a configurational change and a
trigger"* ([DL-265](../design-log.md)). The hand switch took five live changes on four apps and a
hand-edited copy of the master's credential-test pack. Three things stood in the way:

- Every deliberator must pass **both** vendors' probes, and the fleet check counts every failing
  probe. One empty vendor account refuses three agents, the run goes degraded, and a degraded run
  holds every buy.
- The operator agent has no provider setting and its only probe is Anthropic.
- The provider lives in the tunables pack, a fidelity decision path, so it could not be changed there.

On 2026-10-07 the operator kept the debate on OpenAI while the debate workflow is rebuilt (*"Keep it
on OpenAi whilst we are plumbing"*). So the hand-made state has to last for weeks, and **any full
`up` reverts it** to a vendor whose account is empty.

### Measured, 2026-10-09 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Live provider settings | `master`: no `*LLM_PROVIDER` variable. `operator`: none. `deliberator-manager`: `DELIBERATOR_LLM_PROVIDER=openai` | *[measured 2026-10-09 06:14 UTC]* `az containerapp show`, env names containing `LLM_PROVIDER` |
| The credential-test pack | 12 probes over 6 agent types; 4 named `anthropic` (operator and the three deliberators), 3 named `openai` (the three deliberators), 5 others; all `required` | *[measured]* the JSON parsed |
| The master's live pack | A hand-edited copy with the four `anthropic` probes removed, 8 of 12 | *[carried from DL-265, 2026-10-06; not re-read]* |
| The operator **container** calls no vendor | It binds `FakeLLMClient({})`: `agents/operator/entrypoint.py:34` passes no client and `agents/operator/agent.py:72` falls back to the fake | *[measured, both files read whole]* |
| The operator's real LLM use | The dashboard chat only: `surfaces/dashboard/chat_binding.py:34` builds `OperatorAnthropicLLMClient` from `ANTHROPIC_API_KEY` | *[measured, read whole]* |
| Readers of `OperatorSettings.model` | Three: `agents/operator/agent.py:103` and `:131` (the ledger row's model) and `surfaces/dashboard/chat_binding.py:36` | *[measured]* `grep` over `agents/operator` and `surfaces`, tests excluded |
| What the master records at an activation | `AgentInstance` gains `credential_tests_declared`, `credential_tests_tested`, `credential_tests_passed` (`agents/master/credential_report.py:53-55`, merged at `agents/master/agent.py:144`), beside `agent_type`, `state`, `started_at` (`agents/master/store.py:60-65`) | *[measured, read]* |
| What the fleet check records | One `FleetPreflight` node: `checked_at`, `passed`, `failure_count`, `failures`, `agent_types_checked` (`agents/master/fleet_preflight.py:78-88`); the first check runs when the master starts (`fleet_preflight_loop.py:33-44`) | *[measured, read]* |
| A prototype of parts A to C | 11 files changed, 2 added; **no fidelity decision path touched** | *[measured]* `git status --porcelain -- <the nine paths>` printed nothing |
| Existing tests the prototype breaks | **Exactly four**: `agents/master/tests/test_credential_probe_loading.py::test_trading_credential_tests_load_to_nonzero_count` and `agents/master/tests/test_fleet_preflight_packs.py::test_every_trading_credential_probe_is_required` (both pin 12 probes; 13 now), `surfaces/tests/test_dashboard_chat.py::test_chat_binding_requires_live_graph_and_key` and `surfaces/tests/test_dashboard_chat_edges.py::test_chat_binding_configuration_failure_is_disconnected` (both patch `chat_binding.OperatorAnthropicLLMClient`, a name the binding no longer imports) | *[measured]* whole suite on the prototype: 4,430 passed, 7 failed, 7 skipped. The 7 are these four, the file-name one of the next row, and two import-wall tests that fail the same way on `main` when pytest is started without `uv run` (they pass under it) |
| A fifth test, broken only by a file name | `tests/test_llm_adapter_ownership.py::test_vendor_adapter_implementations_live_only_in_kernel` fails on **any** file under `agents/` whose name starts `llm_`. The prototype's `agents/master/llm_selection.py` tripped it | *[measured]* |
| The parameter step on the prototype | Exit 1 with two lines (`operator.llm_provider settings field has no PARAM row`; `operator.model law Value ... differs from code default ''`) before the law rows; exit 0 after them | *[measured]* `scripts/check_param_law_sync.py`, both runs |
| `agents/master/entrypoint.py` | 195 lines on `main`; **199** with the prototype's four-line wiring | *[measured]* `wc -l` |
| The OpenAI SDK's forced function call | `openai` 2.49.0: `tools=[{"type":"function","function":{name, parameters}}]`, `tool_choice={"type":"function","function":{"name":...}}`; the reply's `choices[0].message.tool_calls[0].function.arguments` is a JSON **string**; the SDK's `ReasoningEffort` type lists `none, minimal, low, medium, high, xhigh, max` | *[measured offline, no call made]* the installed package's types, and a wire-form reply parsed through `ChatCompletion.model_validate` |
| `gpt-5.5` accepts the operator's default effort `max` with a forced function, and an interpret turn fits 4,096 completion tokens | not known | *[ASSUMED — not measured]* it needs a paid call. Settled by F1b after merge (the planner's, on the operator's word). If it fails, the remedy is the `OPERATOR_EFFORT` setting, not this sprint's code |
| With a forced named function, `finish_reason` is `stop`, not `tool_calls` | not known | *[ASSUMED — from the vendor's documentation as remembered, not measured]* so the adapter must read the tool call and never branch on `finish_reason`, except for `length` |
| An env-only `az containerapp update` on an app at 0 replicas starts one replica of the new revision | not known for an env-only change | *[ASSUMED]* seen at four **image** retags on 2026-10-08 (15 of 15 agent types activated within minutes of each). Settled by F1a. The command must fail loudly when the proof does not arrive, never pass |
| `properties.runningStatus` of an app at 0 replicas | `Running` on `master`, `operator` and `deliberator-manager`, each with 0 replicas | *[measured 2026-10-09 06:14 UTC]* `az containerapp replica list --query "length(@)"` beside `az containerapp show --query properties.runningStatus` |
| Key Vault holds `openai-api-key` | named in `orchestration/packs/trading_vault_seed.json`; the three deliberators have received it nightly since 2026-10-06 | *[read; and carried from DL-265]* |
| The rider's test | `tests/test_served_request_settlement.py::test_receive_batch_tunable_can_still_be_raised` passes with a clean environment, **fails** with `AZURE_SERVICEBUS_CONNECTION_STRING=placeholder-not-a-credential` set (the send guard of S159 fires), and passes in that environment once the settings are built with `connection_string=None, connection_strings_json=None` | *[measured]* three runs, the third on a patched copy |

---

## Scope — and what is deliberately NOT here

1. **One declared provider (D1).** New `orchestration/packs/trading_llm.json`: the provider and, for
   each of the five apps that follow it, the name of the environment variable that app reads.
2. **The master applies it (D2, D3).** A probe may carry the vendor it belongs to. Where the master
   loads its packs, it keeps the declared vendor's probes and key and drops the other vendor's. An
   empty setting changes nothing. Three refusals at start-up: an unknown provider, an unknown probe
   tag, a granted vendor key with no probe.
3. **The packs say it (D3).** Every `anthropic` and `openai` probe is tagged; the operator gains the
   `openai` probe and the `openai-api-key` grant. 13 probes.
4. **The operator follows (D4).** `OperatorSettings.llm_provider`; `model` empty resolves the
   provider's default at all three readers.
5. **The operator's chat follows (D5, D6).** A kernel OpenAI adapter with a forced function call, a
   kernel factory for the operator's client, and the dashboard binding built through it.
6. **A full `up` keeps it (D7).** `infra/deploy-agents.ps1` reads the pack: the value wins over the
   tunables pack's line for the same key, and the master receives it.
7. **The command (D8).** `scripts/switch_llm_provider.py`: report, apply, prove.
8. **The three law cycles (D9)** and a section *Switching the LLM vendor* in
   [`docs/deployment.md`](../deployment.md) under *Container Apps Fleet Deploy*: the file, the
   command, its exit codes, what it does not do.
9. **Rider (D10).** The one settlement test above is made offline by construction.

### Out of scope (do NOT build this sprint)

- **The tunables pack.** Its three `DELIBERATOR_LLM_PROVIDER` lines stay, byte for byte. They are
  removed later by the planner, when the fidelity count allows.
- **Any other fidelity decision path**, and anything in `contracts/`.
- **`agents/deliberator/`.** It already reads `DELIBERATOR_LLM_PROVIDER`; nothing there changes.
- **A real LLM client in the operator container.** It keeps the fake client. Only its setting, its
  probe and its key follow the provider.
- **A vendor per role** (the judge on one vendor, the debaters on another). One provider for all.
- **The two other live-only settings** (the manager's wait of 240 seconds, three debates at once).
  They live in the tunables pack and stay live-only.
- **The graph vocabulary.** No new label and no new property: `FleetPreflight` and `AgentInstance`
  keep their shape.
- **The probes' request bodies.** Tag them, do not rewrite them.
- **Running the command, any `az` call, any live LLM call.** You have no network. The live proof is
  the planner's.
- **`pyproject.toml` and `uv.lock`.** The planner bumps the version at merge.
- **No ADR reversal.** An ADR is reversed by a new ADR, never by a sprint.

### The road not taken (LAW-06)

- **Filter the credential-test pack in the deploy tooling** (what was done by hand on 2026-10-06).
  Rejected: the filter would live in PowerShell, which the gate cannot read, and the master would
  run a pack the repository does not hold.
- **Keep the provider in the tunables pack.** Rejected: it is a fidelity decision path, and the
  operator asked for the setting to sit apart from the decision parameters.
- **The command takes the vendor as an argument.** Rejected: that makes a live-only state, which a
  full `up` reverts. The command applies what the pack declares and nothing else.
- **Hand both vendors' keys to an agent and test only one.** Rejected: DL-36 is the operator's
  policy that the master tests every credential before giving it to an agent.
- **Select inside `resolve_and_test_report`, on every call.** Prototyped first. Rejected: it threads
  a new argument through `agents/master/agent.py` (182 lines) and `fleet_preflight.py`, and leaves
  the key withheld nowhere. Selecting once, where the packs are loaded, touches one place.
- **Record the provider on `FleetPreflight`.** Rejected: a new property on a property-enforced
  label moves the vocabulary pack, which turns an image-only retag into a full `up` of 17 targets.
- **The command wakes the apps it did not change, to re-prove their activation.** Rejected for this
  sprint: it needs temporary scale rules on live apps. The fleet check already tests every agent
  type's credentials under the new selection; the command says which activations it did not re-prove.
- **A new action in `infra/deploy-agents.ps1` instead of a Python command.** Rejected: unread by
  `make ci`. The command is Python with the `az` runner injected, so its logic is under test.
- **Translate the effort setting for OpenAI.** Rejected: the SDK's own type lists the same ladder;
  the value is passed as set and F1b measures it.

---

## The design decisions — made, and recorded in DL-282

They are recorded in [DL-282](../design-log.md) with these rejected alternatives. Build them as
written. A decision you find you cannot build is a STOP, not an improvisation.

**D1 — the file.** `orchestration/packs/trading_llm.json`:

```json
{
  "_comment": "<one paragraph: what this file is, that the deploy script and scripts/switch_llm_provider.py read it, and that it wins over the tunables pack for the keys it names>",
  "provider": "openai",
  "apps": {
    "master": "MASTER_LLM_PROVIDER",
    "operator": "OPERATOR_LLM_PROVIDER",
    "deliberator-manager": "DELIBERATOR_LLM_PROVIDER",
    "deliberator-proponent": "DELIBERATOR_LLM_PROVIDER",
    "deliberator-opponent": "DELIBERATOR_LLM_PROVIDER"
  }
}
```

The value at merge is `openai`: it is what the fleet runs, on the operator's word of 2026-10-07. The
order of `apps` is the order the command applies them in, the master first.

**D2 — the master selects once, at load.** A new module in `agents/master/` (🪤 its file name must
**not** start `llm_`) holds one pure function. `agents/master/entrypoint.py::build_app` calls it right
after the three packs are loaded and before the existing "a secret map needs credential tests" check.

- `MasterSettings.llm_provider`: `str`, default `""`, env `MASTER_LLM_PROVIDER`.
- `CredentialTest.llm_provider: str = ""`, filled by the parser from an entry's optional
  `"llm_provider"` field.
- With an empty setting the function returns both inputs **unchanged**, after validating the tags.
- With a declared provider it returns the tests whose tag is empty or equal to it, and the secret map
  without any pair whose environment variable is another vendor's key (`kernel.llm_factory.KEY_ENV`
  is the list of vendors and their key variables; the master may import the kernel).
- **Refusals, each a raised error naming what is wrong, so the master does not start:** (a) the
  setting is not empty and not a key of `KEY_ENV`; (b) any probe's tag is not empty and not a key of
  `KEY_ENV`; (c) after selection, an agent type is granted the declared vendor's key and has no probe
  tagged with that vendor. (a) matters most: a mistyped value would otherwise drop **both** vendors'
  probes and hand keys over untested.
- 🪤 `entrypoint.py` is at 195 lines and the wiring took it to 199 in the prototype. Do not trim to
  fit: move the pack loading (`_resolve_pack` and its three calls) to a module of its own if the
  file would pass 190.

**D3 — the packs.** In `trading_credential_tests.json` every entry named `anthropic` gains
`"llm_provider": "anthropic"` and every entry named `openai` gains `"llm_provider": "openai"`; the
`operator` list gains an `openai` entry identical to the deliberators'. In `trading_secrets.json` the
`operator` list gains `["openai-api-key", "OPENAI_API_KEY"]`. Keep both files' existing formatting, so
the diff shows the added lines and nothing else.

**D4 — the operator's settings.** `llm_provider: str`, default `"anthropic"`. `model` default becomes
`""`, and one method or property returns `model or default_model_for(llm_provider)`, as
`agents/deliberator/settings.py:153-164` does. All three readers of `settings.model` use the resolved
value, so an `LLMCall` row never records an empty model.

**D5 — the kernel.** A new module `kernel/llm_openai_operator.py` holds `OperatorOpenAILLMClient`,
the OpenAI counterpart of `OperatorAnthropicLLMClient` (`kernel/llm_anthropic.py:113-162`), with the
same return contract: for a non-empty `tool_schema` the function's arguments as a JSON string, for an
empty one the `answer` string. It uses Chat Completions, as `kernel/llm_openai.py` does, with one
forced function, `max_completion_tokens` and `reasoning_effort` passed as set. It exposes
`last_usage` and `last_stop_reason` like the existing OpenAI adapter. A reply with no tool call, or
with arguments that do not parse to an object, returns the same fallback the Anthropic adapter
returns (`{"outcome": "refused", "reason": "model returned no tool result"}`). A `length` finish
raises `LLMCompletionStoppedError(provider="openai", stop_reason="length")`, as `_text` does today.
`kernel/llm_factory.py` gains `build_operator_llm(provider, *, api_key, model, max_tokens, effort)`:
it builds exactly the selected vendor's operator client and raises `UnknownProviderError` otherwise.
The Appendix holds the prototype of the adapter.

**D6 — the chat binding.** `bind_dashboard_chat` reads `OperatorSettings().llm_provider`, takes the
key from `key_env_var(provider)` and builds through `build_operator_llm`. No key for the declared
provider, an unknown provider, or either adapter's `ConfigurationError` gives `None` (disconnected).
🪤 `kernel.llm_anthropic.ConfigurationError` and `kernel.llm_openai.ConfigurationError` are two
different classes: catch both.

**D7 — the deploy script.** `infra/deploy-agents.ps1` loads `trading_llm.json` (missing file: throw,
as `Load-Tunables` does). `Get-AgentEnv` removes from the tunables list any key the LLM pack names for
that app and appends the pack's `NAME=provider`, so no key is passed twice. The master's `$envv`
gains `MASTER_LLM_PROVIDER=<provider>`. No vendor name is written as a literal in the script.
Parse-check the script with the PowerShell parser and paste the result; if your sandbox has no
PowerShell, say NOT RUN.

**D8 — the command.** `scripts/switch_llm_provider.py`, with modules beside it as needed (each under
200 lines, each with the `Agent:` / `Role:` / `External I/O:` header). Every `az` call goes through
one injected runner (`shutil.which("az")`, no shell, `-o json`, **stdout only** parsed), the clock and
the sleep are injected, and the graph is injected, so every branch is a unit test.

| Invocation | What it does | Exit |
| --- | --- | --- |
| no flag | Prints the declared provider and, for each app, the live value and whether it differs. Changes nothing | 0 all equal · 3 a difference is pending |
| `--apply --evidence-dir DIR` | Snapshot of each of the five apps to `DIR` → for each app that differs, in the pack's order, one `az containerapp update --set-env-vars NAME=value` → snapshot again → nothing else moved → the proof below | 0 applied and proven · 1 a check failed |
| `--prove-since <UTC ISO>` | The proof read alone, for an apply whose proof timed out | 0 · 1 |
| any | Unknown provider in the pack; `--apply` with `DIR` inside the repository tree; `POSTGRES_DSN` absent when a proof is to be read | 2 |

- **Before the first update** it refuses (exit 1) when any target app has a replica, read from
  `az containerapp replica list`, unless `--even-if-running` is given. 🪤 Not from
  `properties.runningStatus`: it reads `Running` at 0 replicas (measured).
- **Nothing else moved:** between the two snapshots of an app, `properties.template.containers` with
  the one variable removed, `properties.template.scale`, the names in
  `properties.configuration.secrets`, `properties.configuration.ingress`,
  `properties.configuration.registries` and `identity` are equal. A difference is exit 1 naming the
  app and the field.
- **A failed update stops the run** (exit 1): no further app is updated, and the output says which
  apps were changed before it.
- **The proof,** polled every `--poll-seconds` (default 30) for at most `--wait-seconds` (default
  900), counting from the instant taken before the first update: (1) a `FleetPreflight` node with
  `checked_at` at or after it and `passed` true; (2) for each **changed** app other than the master,
  an `AgentInstance` with that `agent_type`, `started_at` at or after it, `state` `active`, whose
  `credential_tests_passed` holds every probe name the pack tags with the declared vendor for that
  agent type, and whose `credential_tests_declared` holds no probe name tagged with another vendor.
  A term still missing at the timeout is exit 1 and is named.
- **An app the apply did not change** is listed as `unchanged, activation not re-proven`. It is not
  a failure.
- The resource group defaults to `trading-agents` (`--resource-group`), as `scripts/cred_audit.py:34`
  does; the subscription is the `az` default unless `--subscription` is given.
- Every line it prints is ASCII. 🪤 A redirected stdout on Windows is cp1252, and S258 lost a run to
  one `≥`.

**D9 — the law cycles** are the table under the law-cycle question.

**D10 — the rider.** In `tests/test_served_request_settlement.py::test_receive_batch_tunable_can_still_be_raised`
the settings are built with `connection_string=None, connection_strings_json=None` beside the two
arguments already there. Nothing else in that file changes.

🪤 **Take no DL number for these.** DL-282 is written. If the build forces a decision the spec did not
make, add it as an amendment under DL-282 and say so in Return notes.

---

## Blast radius — measured 2026-10-09

| What | Detail |
| --- | --- |
| Files changed | `agents/master/entrypoint.py` **195**, `settings.py` **139**, `credential_test.py` **157**, `credential_probes.py` **168**; `agents/operator/settings.py` **64**, `agent.py` **164**; `kernel/llm_factory.py` **70**; `surfaces/dashboard/chat_binding.py` **42**; `infra/deploy-agents.ps1` **928** (not under the size gate); three law books and their test plans; two packs; `docs/deployment.md`; `tests/test_served_request_settlement.py`. New: the master's selection module, `kernel/llm_openai_operator.py`, `orchestration/packs/trading_llm.json`, `scripts/switch_llm_provider.py` and its modules, the tests |
| Agents affected | master, operator; surfaces; kernel. No agent imports another |
| Contract change? | No, and none is allowed |
| Graph vocabulary change? | No |
| New env keys / tunables | `MASTER_LLM_PROVIDER`, `OPERATOR_LLM_PROVIDER`. Neither is in the tunables pack; both come from the new pack |
| Deploy implication | Image-only retag, then three narrow updates on `master` (the provider, the secret map, the credential-test pack) and the new command. No full `up` |
| Rollback | Retag to `s259a`. **A retag does not undo the master's packs:** the older image ignores `MASTER_LLM_PROVIDER` and would run every probe of the new pack, Anthropic's included, so the hand-made 8-probe pack of 2026-10-06 must be put back on `master` in the same step (the planner holds it outside the repository). The two new variables are ignored by older images |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Read DL-282 and DL-265** in `docs/design-log.md`.
3. **Plant the failing tests first** (A1, A2, B2, B5, C1, D2 of the Test plan) and watch them fail.
   Paste the red output.
4. **Implement**, in the order of Scope 1 to 7.
5. **Law cycles**: clauses, test-plan rows, docstring citations, rollups.
6. **Prove the guards can fail (DL-70)**: break the implementation, watch each guard go red, restore.
7. **`make ci` green**, every step of the `ci:` target, **redirected to a file, never piped**.
8. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 the master keeps the declared vendor's probes | the real pack, provider `openai`, then `anthropic`, then empty | 9 tests, 9 tests, 13 tests; no kept test carries the other vendor's tag |
| A2 | 🎯 the other vendor's key is not handed over | the real secret map, provider `openai` | `resolve_config` for each deliberator and for the operator holds `OPENAI_API_KEY` and not `ANTHROPIC_API_KEY`; with an empty provider it holds both |
| A3 | 🎯 the fleet check follows the selection | the real packs, loaded with a transport that answers 401 to Anthropic and 200 to everything else, the selection applied, then `run_fleet_preflight` | provider `openai` → the check passes; provider empty → it fails naming the four Anthropic probes (DL-265's night, reproduced) |
| A4 | 🪤 an unknown provider does not start the master | `llm_provider="opnai"`; then a pack entry tagged `"opnai"` | each raises, naming the value |
| A5 | 🪤 a granted key with no probe does not start the master | the real packs with the operator's `openai` probe removed, provider `openai` | raises, naming `operator` |
| A6 | an empty provider changes nothing | any tests and map | the same objects come back |
| A7 | the real packs are consistent | the three pack files | every probe named after a vendor carries that vendor's tag; every agent type granted a vendor key has that vendor's probe; 13 probes, all required |
| B1 | 🎯 the operator's model follows the provider | default settings; `OPERATOR_LLM_PROVIDER=openai`; an explicit model | `claude-opus-5`; `gpt-5.5`; the explicit one. An `LLMCall` written by `interpret` records the resolved model, never `""` |
| B2 | 🎯 the OpenAI operator adapter forces one function | a fake SDK client | the request carries `tools` with one function, `tool_choice` naming it, `max_completion_tokens`, `reasoning_effort`; interpret returns the arguments as JSON; explain returns the `answer` string; usage and stop reason are recorded |
| B3 | 🪤 a reply the adapter cannot use | no tool call; arguments that are not JSON; arguments that are a JSON list; `finish_reason` `length` | the refusal fallback three times; `LLMCompletionStoppedError` for `length` |
| B4 | the operator factory never changes vendor | each provider; an unknown one; the selected vendor's constructor raising | its own class each time; `UnknownProviderError`; the other vendor is never built |
| B5 | 🎯 the chat binding follows the provider | `OPERATOR_LLM_PROVIDER=openai` with only `OPENAI_API_KEY`; the same with only `ANTHROPIC_API_KEY`; an unknown provider | bound through the OpenAI client; `None`; `None` |
| B6 | the adapter rules still hold | the new class | `VENDOR_ADAPTER_CLASSES` in `tests/test_llm_adapter_ownership.py` names it; it imports `openai` only through `importlib` and its key reaches nothing else, as `tests/test_llm_adapter_security.py` proves for the Anthropic one |
| C1 | the LLM pack names real things | `trading_llm.json`, the deploy script, the settings classes | the provider is a key of `KEY_ENV`; every app is `master` or a key of the script's `$AGENTS`; every variable is that app's settings prefix plus `LLM_PROVIDER`, and the class has the field |
| C2 | the deploy script reads the pack | the script's text | it loads `trading_llm.json`; `Get-AgentEnv` filters the tunables by the pack's keys before appending; the master's env carries the variable; no vendor name is a literal |
| D1 | the report changes nothing | five apps, one differing | exit 3 naming it; no `update` call was made. All equal → exit 0 |
| D2 | 🎯 apply changes only what differs, the master first | three apps differ | three `update` calls in the pack's order, each with one `NAME=value`; ten snapshot files in the evidence directory |
| D3 | 🪤 the refusals | evidence directory inside the repository; no `POSTGRES_DSN`; an app with one replica; an unknown provider | exit 2, 2, 1, 2; in each, no `update` call |
| D4 | 🪤 something else moved | the second snapshot differs in image; in a scale rule; in another variable; in a secret name | exit 1 naming the app and the field, four times |
| D5 | 🎯 the proof needs every term | a graph holding all terms; then each term removed in turn (no fleet check since the start; a fleet check with `passed` false; no activation of one changed app; an activation whose passed list lacks the vendor's probe; one that declares the other vendor's probe) | exit 0; then exit 1 naming the missing term, five times; the wait ends by the injected clock |
| D6 | an unchanged app is reported, not failed | two of five apps already on the value | both read `unchanged, activation not re-proven`; exit 0 |
| D7 | 🪤 a failed update stops the run | the second `update` returns non-zero | exit 1; no third call; the output names the app already changed |
| D8 | every printed line is ASCII | each mode's output | `.encode("ascii")` succeeds |
| E1 | the rider | `AZURE_SERVICEBUS_CONNECTION_STRING=placeholder-not-a-credential` set through `monkeypatch` | the test still passes |

---

## Success factors

- [x] With provider `openai`, the fleet check passes while every Anthropic probe would fail (A3).
- [x] The unselected vendor's key is not in any agent's resolved config (A2).
- [x] A mistyped provider, a mistyped tag and a granted key with no probe each stop the master (A4, A5).
- [x] With an empty `MASTER_LLM_PROVIDER` the master behaves as today (A6).
- [x] The dashboard chat binds on OpenAI with only OpenAI's key, and is disconnected without it (B5).
- [x] The command's report mode changes nothing; apply changes only differing apps; the proof fails
      on each missing term (D1, D2, D5).
- [x] **No fidelity decision path changed**: the scope command of the checklist prints nothing.
- [x] Exactly five existing tests edited: the four of the Measured table and the rider. One existing
      constant extended (`VENDOR_ADAPTER_CLASSES`).
- [x] The three law cycles done; the parameter step exits 0.
- [x] Every new guard planted, watched to fail, restored, stated per guard.
- [x] Every touched Python module under 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **A green fleet check with nothing selected.** A mistyped provider deselects both vendors and the
check goes green over probes that never ran. Refusal (a) of D2 is what prevents it: plant the typo
and watch the master refuse.
🪤 **A file under `agents/` named `llm_*.py`** fails the adapter-ownership test (measured).
🪤 **`chat_binding` tests patch a name on the module.** After D6 the binding imports the factory, so
the two tests that patch `OperatorAnthropicLLMClient` must patch what the binding now calls.
🪤 **`finish_reason` after a forced function** is assumed to be `stop`. Read the tool call; do not
wait for `tool_calls`.
🪤 **A script run without the `.env` file reads an in-memory graph and proves nothing.** The command
refuses a proof read without `POSTGRES_DSN` rather than report an empty graph.
🪤 **`-o tsv 2>&1` captures the Azure CLI's progress spinner.** Parse stdout only, as JSON.
🪤 **Your working files come back CRLF on Windows.** The repository is LF (`.gitattributes`); check
`git diff --stat` shows no whole-file rewrites before you commit.
🪤 **`--no-cov` hides a coverage hole.** The floor is 100.00 % and it is measured by `make ci`, not
by a single test file's run.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `agents/master/entrypoint.py` **195**, `agents/master/agent.py` **182** (do not
  touch it), `agents/master/credential_probes.py` **168**, `agents/master/credential_test.py` **157**,
  `agents/operator/agent.py` **164**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: `kernel.tunable(..., why=...)` with bounds where a bound exists.
- Faults, not silent failure.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- No version bump and no `uv.lock` change by the builder; the planner does both at merge.
- Secrets never through the worktree. A worktree has **no `.env`**. **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. Review the diff against the checklist; re-measure (the scope command, the five edited tests, the
   planted guards); merge `main` in; MINOR bump, `uv lock`; Windows `make ci`; push;
   **`make gate-ran` from `../ta-s262`**, the printed SHA checked against `git rev-parse HEAD`;
   CodeQL set-diff against `main`'s open alerts; fast-forward `main`; tag.
2. Parse-check `infra/deploy-agents.ps1` and read the env list `Get-AgentEnv` builds for the three
   deliberators, the operator and one other app.
3. **F1a, on the operator's word for the retag:** image-only retag from the release tag (read the
   decision-path diff from the deployed SHA first: expected empty, so the fidelity count stands).
   Then on `master`, each with a snapshot before and after: `MASTER_LLM_PROVIDER=openai`, the new
   secret map, the new credential-test pack. Then
   `uv run --env-file .env python scripts/switch_llm_provider.py --apply --evidence-dir <outside the repo>`.
   Expected: the master and the operator change, the three deliberators read
   `unchanged, activation not re-proven`, a `FleetPreflight` passes with 15 agent types, exit 0.
   It also settles the assumption that an env-only update starts a replica.
4. **F1b, paid, asked first:** one `interpret` and one `explain` through the dashboard binding on
   `gpt-5.5`. Neither stops on `length`; tokens read against 4,096.
5. **F2:** the first scheduled run after the deploy reads 8 / 8, each deliberator and the operator
   activated with the declared vendor's probe passed and the other vendor's not declared, no
   `Escalation`.
6. **Not proven by any of these:** the return to Anthropic (its account is empty until 2026-10-11).
7. Work-queue 109 stays open until the three provider lines leave the tunables pack.

---

## Handover — paste this to Codex

```text
Sprint 262 — the fleet's LLM vendor is one declared value, and one command applies it and proves it.
Spec: docs/sprints/sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it.md
(read ALL of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents, local checkout.

Your worktree already exists: ../ta-s262, on branch
sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it, cut from main, with its
venv synced to the lock. Work only there, never in the main checkout and never on main. You have no
.env and no network: every proof is a unit test. `uv run` is safe; never run a bare `uv sync`. Do not
touch pyproject.toml or uv.lock, and say so: the planner bumps the version at merge. Do not push and
do not merge: commit on the branch and hand back. Do not edit docs/STATE.md, docs/work-queue.md or
docs/design-log.md (one exception: an amendment under DL-282 if the build forces a decision). If a
make ci step cannot run in your sandbox (the dependency audit needs the network), do not bypass it
silently: name the step as NOT RUN in the handback.

This handover is complete: nobody will send you follow-up messages. Two tiers:
- A wrong line number, count, path, test name or clause number whose intent is plain from the spec's
  Scope and Success factors is NOT a reason to stop: follow the intent, record the correction in
  Return notes, continue.
- STOP and report, without improvising, when: the build needs a change to any file under
  agents/scanner/, agents/analyst/, agents/portfolio_manager/, agents/provider/domain/, contracts/,
  agents/execution/order_tolerance.py, orchestration/history_window.py,
  orchestration/packs/trading_tunables.json or orchestration/packs/trading_issuer_map.json; it needs
  a change to agents/deliberator/ or to orchestration/packs/trading_graph_vocabulary.json; an
  existing test other than the five named in the spec has to be edited; a law you read contradicts
  the spec; or a decision D1-D10 cannot be built as written.

What and why: on 2026-10-06 the Anthropic account ran empty and switching the debate to OpenAI took
five live changes on four apps and a hand-edited copy of the master's credential-test pack, because
every deliberator must pass both vendors' probes, the operator agent knows one vendor, and the
provider sits in a file that must not change. The operator asked for one setting and one trigger.
This sprint builds that: one pack file, the master's probes and keys following it, the operator and
its dashboard chat following it, the deploy script keeping it, and one Python command that applies
it to the live apps and reads the proof from the graph. You build and unit-test all of it. You run
none of it against Azure, the graph or a model.

MUST RULE before any code: read, whole, agents/master/laws/laws.md, agents/operator/laws/laws.md,
surfaces/laws/laws.md (each with its test-plan.md), agents/deliberator/laws/laws.md (read only),
orchestration/laws/laws.md (read only), docs/laws/conventions.md, docs/laws/drift-register.md,
tests/test_llm_adapter_ownership.py, tests/test_llm_adapter_security.py,
tests/test_deploy_script_invariants.py, tests/test_deploy_tunables_pack.py, and DL-282 and DL-265 in
docs/design-log.md. Fill the Law reading record first. Law-cycle answer: YES for master, operator
and surfaces, as the spec's table says; NO contracts/ file changes.

Order (the spec's Steps): laws -> plant A1, A2, B2, B5, C1 and D2, watch them fail, paste the red ->
implement Scope 1 to 7 -> the three law cycles -> the deployment.md section -> the rider -> break
and restore every guard -> make ci to a file.

Build (decisions D1-D10 are made; build them as written):
1. orchestration/packs/trading_llm.json (D1).
2. The master: the optional probe tag, MasterSettings.llm_provider, one selection function in a new
   module whose name does not start llm_, called once in build_app; three refusals (D2).
3. The two packs: tags on every vendor probe, the operator's openai probe and key grant (D3).
4. OperatorSettings.llm_provider, model default "" resolved at all three readers (D4).
5. kernel/llm_openai_operator.py and build_operator_llm (D5); the Appendix holds a prototype.
6. surfaces/dashboard/chat_binding.py through the factory (D6).
7. infra/deploy-agents.ps1 reads the pack (D7); parse-check it.
8. scripts/switch_llm_provider.py and its modules (D8).
9. The law cycles (D9), docs/deployment.md, the rider (D10).

DO NOT: change the tunables pack or any other fidelity decision path; change agents/deliberator/;
add a graph label or property; rewrite a probe's request body; give the operator container a real
LLM client; let the command take the vendor as an argument; translate the effort value; name a
module under agents/ llm_*.py; trim agents/master/entrypoint.py to fit instead of splitting it; call
az, the graph or a model; pin a version number.

Handback checklist (the handback is returned against these, one by one):
 1. Law reading record filled before the first code change.
 2. The red output of A1, A2, B2, B5, C1 and D2 pasted, from before the implementation.
 3. Test plan results: one row for each of A1-A7, B1-B6, C1-C2, D1-D8 and E1, with file and status.
 4. Every guard's break-and-restore stated, one line per guard. At least: each of the three refusals
    of D2; the key withheld (A2); the selection ignored (A3); the resolved model (B1); the forced
    tool_choice (B2); the length stop (B3); each term of the proof (D5); the nothing-else-moved
    check (D4); the replica refusal (D3); the stop on a failed update (D7).
 5. This prints nothing, and you say so (run it against the commit the branch was cut from if main
    has moved; name which you used):
    git diff main --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration/history_window.py orchestration/packs/trading_tunables.json orchestration/packs/trading_issuer_map.json orchestration/packs/trading_graph_vocabulary.json agents/deliberator pyproject.toml uv.lock docs/STATE.md docs/work-queue.md
 6. Every EXISTING test you edited, named, with the reason. The expected answer is five: the four
    of the spec's Measured table and the rider; plus the one constant VENDOR_ADAPTER_CLASSES.
 7. `git diff main -- orchestration/packs/trading_credential_tests.json orchestration/packs/trading_secrets.json`
    pasted whole: added lines only.
 8. The PowerShell parse-check of infra/deploy-agents.ps1: the command and its output, or NOT RUN
    with the reason.
 9. The three law books' old and new versions, the new and reworded clause IDs, and the rollup lines
    make ci printed.
10. The parameter step's output (scripts/check_param_law_sync.py), exit code stated.
11. make ci output file named, exit code stated, every NOT RUN step named with its reason.
12. Module line counts for every touched or new Python module; Status BUILT here and in the README
    row (the status cell leads with BUILT).
13. One line saying the command, the deploy script and the OpenAI adapter were NOT RUN against any
    live system, and anything in them you are unsure of.
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
| Master pack loading, probes and key selection | `agents/master/laws/laws.md` LOCKED v1.8 and its whole `test-plan.md` | `MST-OUT-04`, `MST-NEV-06`, `MST-SEC-02/03/04`, `MST-DEP-04/05`, PARAM | Yes: select once before the credential-bearing-pack check; preserve empty-provider identity and minimum privilege. `MST-SEC-02/03` remain grey; this sprint proves the narrower new vendor-key guarantee. |
| Operator settings and recorded model | `agents/operator/laws/laws.md` LOCKED v1.4 and its whole `test-plan.md` | `OPR-DEP-01`, `OPR-SEC-01`, `OPR-STA-03`, PARAM | Yes: resolve the model at all three readers; retain the fake container client. |
| Dashboard chat binding | `surfaces/laws/laws.md` LOCKED v1.3 and its whole `test-plan.md` | `SRF-IN-03`, `SRF-DEP-01/02`, new `SRF-DEP-03` | Yes: missing selected key and either configuration error disconnect. `SRF-DEP-01` remains grey; the new narrower clause gets functional proof. |
| Kernel adapter and factory | Whole `docs/laws/conventions.md`, `tests/test_llm_adapter_ownership.py`, `tests/test_llm_adapter_security.py` | conventions sections 3, 4, 7, 7a; `OPR-SEC-01`, `OPR-DEP-01` | No: vendor implementations stay in kernel, imports lazy, selected-vendor failure never constructs another vendor. |
| Pack, deploy script and command | Whole `orchestration/laws/dispatcher/laws.md` LOCKED v1.2, `tests/test_deploy_script_invariants.py`, `tests/test_deploy_tunables_pack.py` | `MST-NEV-06`, `MST-OUT-04`, `DSP-IN-03`, `DSP-ORD-01` | No: use existing graph evidence only; count replicas, compare snapshots, inject every external boundary. |
| Deliberator selection (read only) | Whole `agents/deliberator/laws/laws.md` LOCKED v1.16 | `DLIB-DEP-03/04`, PARAM `llm_provider` and provider-resolved models | No: no deliberator, contract, fidelity path or graph-vocabulary edit. |
| Governing context | Whole `CLAUDE.md`, `docs/laws/drift-register.md`; DL-282 and DL-265 in `docs/design-log.md` | LAW-02, LAW-06, conventions section 9 | No: D1-D10 are decided. Correct the nonexistent orchestration law path through the laws index and record it in Return notes. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** YES for master, operator and surfaces, exactly the three D9 cycles; NO contract changes. Owed: `MST-OUT-04` amendment, new `MST-NEV-07`, `OPR-DEP-01` amendment, new `SRF-DEP-03`, PARAM rows and both rollups. Pre-code record: these cycles were not done at the time of reading. All three are now completed and proven locally below.

**Contradictions found between a law and this spec:** none beyond the three amendments explicitly authorized by D9.

**Laws found silent where a decision was needed:** master vendor-key containment and dashboard selected-provider binding are absent; D9 already decides their new guarantees. Recorded as DRIFT-105, to be closed by this cycle; no additional decision needed.

**Clauses that were ⬜ and are now proven:** new `MST-NEV-07` and `SRF-DEP-03`. Amended `MST-OUT-04` and `OPR-DEP-01` re-proven. Existing grey clauses remain grey; no promotion from partial proof.

**Pre-code baseline:** clean `C:\Users\yury_\Downloads\project\ta-s262`, branch `sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it`; HEAD, main and origin/main all `ceec5bb605271295b06e1ca1f04df2a42ffc1d4d`. No push, merge, live call, version/lock or tracker edit is authorized. `docs/STATE.md` is the active tracker under CLAUDE.md and is explicitly excluded by this handover.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a1_only_declared_vendor_probes_remain` | `agents/master/tests/test_provider_selection.py` | PASS | `MST-NEV-07, MST-OUT-04` |
| A2 | `test_a2_unselected_vendor_key_is_withheld` | `agents/master/tests/test_provider_selection.py` | PASS | `MST-NEV-07, MST-SEC-02` |
| A3 | `test_a3_fleet_check_follows_selection` | `agents/master/tests/test_provider_selection.py` | PASS | `MST-OUT-04` |
| A4 | `test_a4_unknown_provider_refuses_start; test_a4_unknown_probe_tag_is_refused` | `agents/master/tests/test_provider_selection_refusals.py` | PASS | `MST-NEV-07` |
| A5 | `test_a5_granted_key_without_probe_is_refused` | `agents/master/tests/test_provider_selection_refusals.py` | PASS | `MST-NEV-07` |
| A6 | `test_a6_empty_selection_preserves_input_objects` | `agents/master/tests/test_provider_selection.py` | PASS | `MST-NEV-07` |
| A7 | `test_a7_real_packs_are_consistent` | `agents/master/tests/test_provider_selection.py` | PASS | `MST-NEV-06, MST-NEV-07` |
| B1 | `test_b1_model_follows_provider_and_override` | `agents/operator/tests/test_provider_model.py` | PASS | `OPR-DEP-01, OPR-STA-03` |
| B2 | `test_b2_operator_forces_one_named_function` | `tests/test_openai_operator.py` | PASS | `OPR-DEP-01, OPR-NEV-05` |
| B3 | `test_b3_unusable_tool_reply_is_refused; test_b3_length_raises_after_recording_usage` | `tests/test_openai_operator_edges.py` | PASS | `OPR-FAIL-01, OPR-FAIL-02, OPR-NEV-05, OPR-STA-03` |
| B4 | `test_b4_factory_builds_exactly_selected_vendor; test_b4_selected_failure_never_builds_other_vendor; test_b4_unknown_provider_refuses` | `tests/test_operator_llm_factory.py` | PASS | `OPR-DEP-01` |
| B5 | `test_b5_chat_binds_only_with_selected_key; test_each_vendor_configuration_error_disconnects` | `surfaces/tests/test_dashboard_chat_provider.py` | PASS | `SRF-DEP-03, SRF-IN-03` |
| B6 | `test_b6_openai_key_never_escapes_operator` | `tests/test_openai_operator_security.py` | PASS | `OPR-DEP-01, OPR-SEC-01` |
| C1 | `test_c1_llm_pack_names_real_apps_and_settings` | `tests/test_deploy_llm_pack.py` | PASS | `MST-NEV-07, OPR-DEP-01` |
| C2 | `test_c2_deploy_filters_tunables_before_appending_llm_pack` | `tests/test_deploy_llm_pack.py` | PASS | `MST-NEV-07` |
| D1 | `test_d1_report_is_read_only` | `tests/test_switch_llm_apply.py` | PASS | `MST-OUT-04` |
| D2 | `test_d2_apply_changes_only_differences_master_first` | `tests/test_switch_llm_apply.py` | PASS | `MST-NEV-07, MST-OUT-04` |
| D3 | `test_d3_evidence_inside_repo_is_refused; test_d3_proof_without_dsn_is_refused; test_d3_replicas_refuse_before_first_update; test_d3_unknown_provider_refuses_before_azure` | `tests/test_switch_llm_refusals.py` | PASS | `MST-NEV-07, MST-OUT-04` |
| D4 | `test_d4_nothing_else_may_move (seven fields)` | `tests/test_switch_llm_refusals.py` | PASS | `MST-OUT-04` |
| D5 | `test_d5_each_missing_proof_term_fails; test_d5_deadline_is_bounded_by_injected_clock` | `tests/test_switch_llm_proof.py` | PASS | `MST-NEV-07, MST-OUT-04` |
| D6 | `test_d6_unchanged_apps_are_not_reproven` | `tests/test_switch_llm_apply.py` | PASS | `MST-OUT-04` |
| D7 | `test_d7_failed_second_update_stops_run` | `tests/test_switch_llm_apply.py` | PASS | `MST-OUT-04` |
| D8 | `test_d8_report_apply_and_prove_output_are_ascii` | `tests/test_switch_llm_apply.py` | PASS | `MST-OUT-04` |
| E1 | `test_e1_rider_ignores_ambient_bus_credentials` | `tests/test_settlement_rider_offline.py` | PASS | `DEP-BUS-05, DLIB-IDM-04` |

**Tests added beyond the plan:** one-call master composition, vendor-wide probe applicability, fake container ownership, lazy SDK failure and cleared accounting, all seven protected fields, stale/inactive/malformed graph facts, evidence-based proof retry, proof arrival during polling, pack/clock/bounds validation, Azure stdout and error containment, resolved CLI execution, and explicit Postgres backend selection. These close independent failure paths without live calls.

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s262`, branch `sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it`; `.env` absent, verified with `Test-Path .env` → `False`. No live calls, push or merge. `pyproject.toml` and `uv.lock` untouched; the planner bumps and locks at merge.

**Result:** the pack declaration selects the master's vendor probes and distributed key, resolves the operator's model and dashboard vendor, and supplies exactly one deployment provider variable per target. The injected command reports differences without updates, applies only differing apps in master-first order, snapshots and compares protected configuration, stops on replicas or update failure, and requires every fresh graph proof term. Local focused tests and 45 independently broken/restored guards prove these behaviors.

**Files changed:**

- `agents/master/credential_probes.py`
- `agents/master/credential_selection.py`
- `agents/master/credential_test.py`
- `agents/master/entrypoint.py`
- `agents/master/laws/laws.md`
- `agents/master/laws/test-plan.md`
- `agents/master/pack_loading.py`
- `agents/master/settings.py`
- `agents/master/tests/test_credential_probe_loading.py`
- `agents/master/tests/test_fleet_preflight_packs.py`
- `agents/master/tests/test_provider_selection.py`
- `agents/master/tests/test_provider_selection_refusals.py`
- `agents/operator/agent.py`
- `agents/operator/laws/laws.md`
- `agents/operator/laws/test-plan.md`
- `agents/operator/settings.py`
- `agents/operator/tests/test_provider_model.py`
- `docs/deployment.md`
- `docs/design-log.md`
- `docs/laws/INDEX.md`
- `docs/laws/drift-register.md`
- `docs/laws/ledger.md`
- `docs/sprints/README.md`
- `docs/sprints/sprint-262-the-llm-vendor-is-one-declared-value-and-one-command-applies-it.md`
- `infra/deploy-agents.ps1`
- `kernel/llm_factory.py`
- `kernel/llm_openai.py`
- `kernel/llm_openai_operator.py`
- `orchestration/packs/trading_credential_tests.json`
- `orchestration/packs/trading_llm.json`
- `orchestration/packs/trading_secrets.json`
- `scripts/switch_llm_apply.py`
- `scripts/switch_llm_azure.py`
- `scripts/switch_llm_config.py`
- `scripts/switch_llm_proof.py`
- `scripts/switch_llm_provider.py`
- `surfaces/dashboard/chat_binding.py`
- `surfaces/laws/laws.md`
- `surfaces/laws/test-plan.md`
- `surfaces/tests/test_dashboard_chat.py`
- `surfaces/tests/test_dashboard_chat_edges.py`
- `surfaces/tests/test_dashboard_chat_provider.py`
- `tests/switch_llm_testkit.py`
- `tests/test_deploy_llm_pack.py`
- `tests/test_llm_adapter_ownership.py`
- `tests/test_openai_operator.py`
- `tests/test_openai_operator_edges.py`
- `tests/test_openai_operator_security.py`
- `tests/test_operator_llm_factory.py`
- `tests/test_served_request_settlement.py`
- `tests/test_settlement_rider_offline.py`
- `tests/test_switch_llm_apply.py`
- `tests/test_switch_llm_boundaries.py`
- `tests/test_switch_llm_config.py`
- `tests/test_switch_llm_proof.py`
- `tests/test_switch_llm_refusals.py`

**Design decisions:** recorded as [`DL-282`](../design-log.md). Amendment: proof retry can read original before snapshots to recover changed-app scope; without evidence it conservatively requires every non-master target activation. No D1-D10 reversal. Rejected inference from missing activations is circular; no new graph property was added.

**Proof — the red run first:**

```text
Command: uv run pytest --no-cov --tb=short -q agents/master/tests/test_provider_selection.py tests/test_openai_operator.py surfaces/tests/test_dashboard_chat_provider.py tests/test_deploy_llm_pack.py tests/test_switch_llm_apply.py
Exit code: 1
FFFFFF                                                                   [100%]
================================== FAILURES ===================================
_________________ test_a1_only_declared_vendor_probes_remain __________________
agents\master\tests\test_provider_selection.py:23: in test_a1_only_declared_vendor_probes_remain
    from agents.master.credential_selection import select_llm_provider
E   ModuleNotFoundError: No module named 'agents.master.credential_selection'
__________________ test_a2_unselected_vendor_key_is_withheld __________________
agents\master\tests\test_provider_selection.py:37: in test_a2_unselected_vendor_key_is_withheld
    from agents.master.credential_selection import select_llm_provider
E   ModuleNotFoundError: No module named 'agents.master.credential_selection'
_________________ test_b2_operator_forces_one_named_function __________________
tests\test_openai_operator.py:16: in test_b2_operator_forces_one_named_function
    import kernel.llm_openai_operator as adapter
E   ModuleNotFoundError: No module named 'kernel.llm_openai_operator'
__________________ test_b5_chat_binds_only_with_selected_key __________________
surfaces\tests\test_dashboard_chat_provider.py:20: in test_b5_chat_binds_only_with_selected_key
    import kernel.llm_openai_operator as adapter
E   ModuleNotFoundError: No module named 'kernel.llm_openai_operator'
________________ test_c1_llm_pack_names_real_apps_and_settings ________________
tests\test_deploy_llm_pack.py:20: in test_c1_llm_pack_names_real_apps_and_settings
    pack = json.loads((ROOT / "orchestration/packs/trading_llm.json").read_text("utf-8"))
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\pathlib\_local.py:546: in read_text
    return PathBase.read_text(self, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\pathlib\_abc.py:632: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors, newline=newline) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\miniconda3\Lib\pathlib\_local.py:537: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\yury_\\Downloads\\project\\ta-s262\\orchestration\\packs\\trading_llm.json'
_____________ test_d2_apply_changes_only_differences_master_first _____________
tests\test_switch_llm_apply.py:15: in test_d2_apply_changes_only_differences_master_first
    from scripts.switch_llm_provider import main
E   ModuleNotFoundError: No module named 'scripts.switch_llm_provider'
=========================== short test summary info ===========================
FAILED agents/master/tests/test_provider_selection.py::test_a1_only_declared_vendor_probes_remain
FAILED agents/master/tests/test_provider_selection.py::test_a2_unselected_vendor_key_is_withheld
FAILED tests/test_openai_operator.py::test_b2_operator_forces_one_named_function
FAILED surfaces/tests/test_dashboard_chat_provider.py::test_b5_chat_binds_only_with_selected_key
FAILED tests/test_deploy_llm_pack.py::test_c1_llm_pack_names_real_apps_and_settings
FAILED tests/test_switch_llm_apply.py::test_d2_apply_changes_only_differences_master_first
6 failed in 4.40s
```

**Proof — the green run:**

```text
Command: uv run pytest --no-cov --tb=short -q agents/master/tests/test_provider_selection.py agents/master/tests/test_provider_selection_refusals.py agents/operator/tests/test_provider_model.py tests/test_openai_operator.py tests/test_openai_operator_edges.py tests/test_operator_llm_factory.py tests/test_openai_operator_security.py surfaces/tests/test_dashboard_chat_provider.py tests/test_deploy_llm_pack.py tests/test_switch_llm_apply.py tests/test_switch_llm_refusals.py tests/test_switch_llm_proof.py tests/test_settlement_rider_offline.py tests/test_switch_llm_config.py tests/test_switch_llm_boundaries.py
Exit code: 0
........................................................................ [ 86%]
...........                                                              [100%]
83 passed in 4.98s
```

**Guards planted:** each row was changed on disk, tested, restored from original bytes, and tested again; all red exits were 1 and all restored exits were 0. Exact commands and complete red/restored stdout are outside the repository in `C:\Users\yury_\AppData\Local\Temp\s262-guard-evidence`, `C:\Users\yury_\AppData\Local\Temp\s262-guard-extra-evidence`, `C:\Users\yury_\AppData\Local\Temp\s262-guard-final-evidence` `C:\Users\yury_\AppData\Local\Temp\s262-guard-backend-evidence`, `C:\Users\yury_\AppData\Local\Temp\s262-guard-config-evidence` and `C:\Users\yury_\AppData\Local\Temp\s262-guard-config-final-evidence`. The initial two redundant-boundary attempts are preserved in the first logs; the successful independent retries are the rows below.

| Guard | Planted break | Actual red / restored output |
| --- | --- | --- |
| 1. A4 unknown provider | coerce an unknown provider to openai | `planted exit=1; restored exit=0; PROVEN` |
| 2. A4 unknown tag including empty selection | skip unknown-tag validation, including empty selection | `planted exit=1; restored exit=0; PROVEN` |
| 3. A5 granted key without vendor probe | skip grant-without-probe refusal | `planted exit=1; restored exit=0; PROVEN` |
| 4. A2 unselected key withheld | retain unselected vendor key | `planted exit=1; restored exit=0; PROVEN` |
| 5. A3 vendor probe selection ignored | run every vendor probe | `planted exit=1; restored exit=0; PROVEN` |
| 6. A6 empty selection preserves original objects | copy the empty-selection secret map | `planted exit=1; restored exit=0; PROVEN` |
| 7. master composes selection exactly once | pass an empty provider at master composition | `planted exit=1; restored exit=0; PROVEN` |
| 8. B1 model resolution | record the unresolved model | `planted exit=1; restored exit=0; PROVEN` |
| 9. B2 forced named tool | use automatic tool choice | `planted exit=1; restored exit=0; PROVEN` |
| 10. B3 length stop | ignore a length stop | `planted exit=1; restored exit=0; PROVEN` |
| 11. B3 unusable arguments refusal | return intent for unusable arguments | `planted exit=1; restored exit=0; PROVEN` |
| 12. D5 no fresh FleetPreflight | ignore absence of a fresh fleet check | `planted exit=1; restored exit=0; PROVEN` |
| 13. D5 FleetPreflight passed false | accept a failed fleet check | `planted exit=1; restored exit=0; PROVEN` |
| 14. D5 missing changed-app activation | ignore a missing changed-app activation | `planted exit=1; restored exit=0; PROVEN` |
| 15. D5 selected probe not passed | ignore missing passed vendor probes | `planted exit=1; restored exit=0; PROVEN` |
| 16. D5 other vendor probe declared | allow the other vendor probe to be declared | `planted exit=1; restored exit=0; PROVEN` |
| 17. D5 stale fleet check | accept an old fleet timestamp | `planted exit=1; restored exit=0; PROVEN` |
| 18. D5 inactive AgentInstance | accept a non-active instance | `planted exit=1; restored exit=0; PROVEN` |
| 19. D5 stale activation | accept an old activation timestamp | `planted exit=1; restored exit=0; PROVEN` |
| 20. D5 missing probe lists | accept missing probe lists | `planted exit=1; restored exit=0; PROVEN` |
| 21. D3 replica refusal | skip replica counting | `planted exit=1; restored exit=0; PROVEN` |
| 22. D4 nothing else moved all seven fields | skip all protected-field comparisons (seven planted fields) | `planted exit=1; restored exit=0; PROVEN` |
| 23. D7 stop after failed update | return success after a failed update | `planted exit=1; restored exit=0; PROVEN` |
| 24. D3 external evidence directory | allow evidence in the repository | `planted exit=1; restored exit=0; PROVEN` |
| 25. D3 no graph proof without DSN | allow proof without DSN | `planted exit=1; restored exit=0; PROVEN` |
| 26. D3 UTC proof timestamp | allow non-UTC timestamp | `planted exit=1; restored exit=0; PROVEN` |
| 27. D3 poll bound | allow zero polling interval | `planted exit=1; restored exit=0; PROVEN` |
| 28. D3 wait bound | allow a negative wait | `planted exit=1; restored exit=0; PROVEN` |
| 29. B5 selected vendor key | read the other vendor key | `planted exit=1; restored exit=0; PROVEN` |
| 30. C2 duplicate provider filtering | keep duplicate tunable provider keys | `planted exit=1; restored exit=0; PROVEN` |
| 31. D7 nonzero Azure update stops following calls | ignore nonzero Azure status with valid JSON stdout | `planted exit=1; restored exit=0; PROVEN` |
| 32. D5 bounded deadline | extend the proof deadline | `planted exit=1; restored exit=0; PROVEN` |
| 33. B3 absent selected key | construct with no selected key | `planted exit=1; restored exit=0; PROVEN` |
| 34. B3 absent optional SDK | raise the wrong missing-SDK error | `planted exit=1; restored exit=0; PROVEN` |
| 35. B4 selected construction never switches vendor | construct the other vendor after selection | `planted exit=1; restored exit=0; PROVEN` |
| 36. B5 absent selected key disconnects | construct without a selected dashboard key | `planted exit=1; restored exit=0; PROVEN` |
| 37. B5 OpenAI configuration error disconnects | propagate OpenAI configuration refusal | `planted exit=1; restored exit=0; PROVEN` |
| 38. B5 Anthropic configuration error disconnects | propagate Anthropic configuration refusal | `planted exit=1; restored exit=0; PROVEN` |
| 39. C2 missing provider pack refuses | allow a missing deployment provider pack | `planted exit=1; restored exit=0; PROVEN` |
| 40. D8 validated DSN selects Postgres | discard the validated DSN when building Postgres | `planted exit=1; restored exit=0; PROVEN` |
| 41. D3 unknown pack provider | allow an unknown provider with otherwise valid pack inputs | `planted exit=1; restored exit=0; PROVEN` |
| 42. D3 ordered master-first target map | skip ordered master-first map validation | `planted exit=1; restored exit=0; PROVEN` |
| 43. D3 provider environment key validation | allow an invalid provider environment key | `planted exit=1; restored exit=0; PROVEN` |
| 44. D3 target selected-vendor probe declaration | allow a target with no selected vendor probe | `planted exit=1; restored exit=0; PROVEN` |
| 45. D5 malformed fleet timestamp | accept a malformed fleet timestamp | `planted exit=1; restored exit=0; PROVEN` |

**Module line counts:** all 39 touched/new Python modules are below 200 lines.

| Python module | Lines |
| --- | ---: |
| `agents/master/credential_probes.py` | 173 |
| `agents/master/credential_selection.py` | 49 |
| `agents/master/credential_test.py` | 158 |
| `agents/master/entrypoint.py` | 156 |
| `agents/master/pack_loading.py` | 62 |
| `agents/master/settings.py` | 144 |
| `agents/master/tests/test_credential_probe_loading.py` | 143 |
| `agents/master/tests/test_fleet_preflight_packs.py` | 42 |
| `agents/master/tests/test_provider_selection.py` | 121 |
| `agents/master/tests/test_provider_selection_refusals.py` | 100 |
| `agents/operator/agent.py` | 164 |
| `agents/operator/settings.py` | 69 |
| `agents/operator/tests/test_provider_model.py` | 48 |
| `kernel/llm_factory.py` | 97 |
| `kernel/llm_openai.py` | 107 |
| `kernel/llm_openai_operator.py` | 104 |
| `scripts/switch_llm_apply.py` | 109 |
| `scripts/switch_llm_azure.py` | 135 |
| `scripts/switch_llm_config.py` | 87 |
| `scripts/switch_llm_proof.py` | 104 |
| `scripts/switch_llm_provider.py` | 151 |
| `surfaces/dashboard/chat_binding.py` | 51 |
| `surfaces/tests/test_dashboard_chat.py` | 198 |
| `surfaces/tests/test_dashboard_chat_edges.py` | 110 |
| `surfaces/tests/test_dashboard_chat_provider.py` | 81 |
| `tests/switch_llm_testkit.py` | 160 |
| `tests/test_deploy_llm_pack.py` | 57 |
| `tests/test_llm_adapter_ownership.py` | 90 |
| `tests/test_openai_operator.py` | 84 |
| `tests/test_openai_operator_edges.py` | 108 |
| `tests/test_openai_operator_security.py` | 84 |
| `tests/test_operator_llm_factory.py` | 83 |
| `tests/test_served_request_settlement.py` | 91 |
| `tests/test_settlement_rider_offline.py` | 21 |
| `tests/test_switch_llm_apply.py` | 99 |
| `tests/test_switch_llm_boundaries.py` | 124 |
| `tests/test_switch_llm_config.py` | 107 |
| `tests/test_switch_llm_proof.py` | 146 |
| `tests/test_switch_llm_refusals.py` | 110 |

**Excluded-scope proof:** run against the exact branch-cut baseline, which is also still main at the pre-code measurement:

```text
git diff ceec5bb605271295b06e1ca1f04df2a42ffc1d4d --stat -- agents/scanner agents/analyst agents/portfolio_manager agents/provider/domain agents/execution/order_tolerance.py contracts orchestration/history_window.py orchestration/packs/trading_tunables.json orchestration/packs/trading_issuer_map.json orchestration/packs/trading_graph_vocabulary.json agents/deliberator pyproject.toml uv.lock docs/STATE.md docs/work-queue.md
Exit code: 0
(stdout empty)
```

**Every existing test edit — exactly five tests and one constant:**

- `agents/master/tests/test_credential_probe_loading.py::test_trading_credential_tests_load_to_nonzero_count`: 12 → 13 for the operator's added probe.
- `agents/master/tests/test_fleet_preflight_packs.py::test_every_trading_credential_probe_is_required`: 12 → 13; all probes remain required.
- `surfaces/tests/test_dashboard_chat.py::test_chat_binding_requires_live_graph_and_key`: patch the selected-provider factory now called by the binding.
- `surfaces/tests/test_dashboard_chat_edges.py::test_chat_binding_configuration_failure_is_disconnected`: patch the factory with its provider argument; the refusal expectation is unchanged.
- `tests/test_served_request_settlement.py::test_receive_batch_tunable_can_still_be_raised`: explicit `connection_string=None`, `connection_strings_json=None` keep the rider offline even with ambient bus config.
- Only `VENDOR_ADAPTER_CLASSES` in `tests/test_llm_adapter_ownership.py` extended for `OperatorOpenAILLMClient`; no existing test function there changed.

**Pack diff — whole, added lines only:**

```diff
diff --git a/orchestration/packs/trading_credential_tests.json b/orchestration/packs/trading_credential_tests.json
index cfbd2846..54be33d8 100644
--- a/orchestration/packs/trading_credential_tests.json
+++ b/orchestration/packs/trading_credential_tests.json
@@ -67,8 +67,26 @@
     }
   ],
   "operator": [
+    {
+      "name": "openai",
+      "llm_provider": "openai",
+      "kind": "http_status",
+      "method": "POST",
+      "url": "https://api.openai.com/v1/chat/completions",
+      "headers": { "Authorization": "Bearer {OPENAI_API_KEY}" },
+      "json_body": {
+        "model": "gpt-5.5",
+        "max_completion_tokens": 256,
+        "messages": [{ "role": "user", "content": "." }]
+      },
+      "expected_statuses": [200],
+      "credential_failure_statuses": [400, 401, 403, 429],
+      "required": true,
+      "cost": "cheap"
+    },
     {
       "name": "anthropic",
+      "llm_provider": "anthropic",
       "kind": "http_status",
       "method": "POST",
       "url": "https://api.anthropic.com/v1/messages",
@@ -90,6 +108,7 @@
   "deliberator-manager": [
     {
       "name": "anthropic",
+      "llm_provider": "anthropic",
       "kind": "http_status",
       "method": "POST",
       "url": "https://api.anthropic.com/v1/messages",
@@ -109,6 +128,7 @@
     },
     {
       "name": "openai",
+      "llm_provider": "openai",
       "kind": "http_status",
       "method": "POST",
       "url": "https://api.openai.com/v1/chat/completions",
@@ -127,6 +147,7 @@
   "deliberator-proponent": [
     {
       "name": "anthropic",
+      "llm_provider": "anthropic",
       "kind": "http_status",
       "method": "POST",
       "url": "https://api.anthropic.com/v1/messages",
@@ -146,6 +167,7 @@
     },
     {
       "name": "openai",
+      "llm_provider": "openai",
       "kind": "http_status",
       "method": "POST",
       "url": "https://api.openai.com/v1/chat/completions",
@@ -164,6 +186,7 @@
   "deliberator-opponent": [
     {
       "name": "anthropic",
+      "llm_provider": "anthropic",
       "kind": "http_status",
       "method": "POST",
       "url": "https://api.anthropic.com/v1/messages",
@@ -183,6 +206,7 @@
     },
     {
       "name": "openai",
+      "llm_provider": "openai",
       "kind": "http_status",
       "method": "POST",
       "url": "https://api.openai.com/v1/chat/completions",
diff --git a/orchestration/packs/trading_secrets.json b/orchestration/packs/trading_secrets.json
index f6168ee5..ccd9bb9e 100644
--- a/orchestration/packs/trading_secrets.json
+++ b/orchestration/packs/trading_secrets.json
@@ -11,6 +11,7 @@
     ["alpaca-secret-key", "EXECUTION_ALPACA_SECRET_KEY"]
   ],
   "operator": [
+    ["openai-api-key", "OPENAI_API_KEY"],
     ["anthropic-api-key", "ANTHROPIC_API_KEY"]
   ],
   "deliberator-manager": [
```

**PowerShell parse check — no execution of the deployment script:**

```powershell
$s262Tokens=$null; $s262Errors=$null
[System.Management.Automation.Language.Parser]::ParseFile((Join-Path (Get-Location) 'infra/deploy-agents.ps1'), [ref]$s262Tokens, [ref]$s262Errors) | Out-Null
$s262Errors
"PowerShell parser errors=$($s262Errors.Count)"
```

```text
PowerShell parser errors=0
Exit code: 0
```

**Offline deployment env composition:** evaluated only AST-extracted `Get-AgentEnv`, `Get-AppTunables`, `Get-AppLlmEnv`, with graph/bus functions stubbed and the two committed packs read directly; no `az` call or deployment script invocation.

```text
deliberator-manager provider assignments=1: DELIBERATOR_LLM_PROVIDER=openai; env total=8
deliberator-proponent provider assignments=1: DELIBERATOR_LLM_PROVIDER=openai; env total=7
deliberator-opponent provider assignments=1: DELIBERATOR_LLM_PROVIDER=openai; env total=7
operator provider assignments=1: OPERATOR_LLM_PROVIDER=openai; env total=3
reporter provider assignments=0: ; env total=2
master: MASTER_LLM_PROVIDER=openai
offline env composition exit=0
```

**Law cycles and rollups:** master LOCKED v1.8 → v1.9 (`MST-OUT-04` amended; `MST-NEV-07` added; provider PARAM); operator v1.4 → v1.5 (`OPR-DEP-01` amended; provider/model/effort PARAM); surfaces v1.3 → v1.4 (`SRF-DEP-03` added). Both ledger and INDEX agree; DRIFT-105 CORRECTED. Existing gray `MST-SEC-02/03` and `SRF-DEP-01` remain gray. The coverage checker prints nothing on success; this explicit readback uses its own derived counters:

```text
uv run python scripts/check_law_coverage.py
(stdout empty)
Exit code: 0
master: derived 26 / 52
operator: derived 19 / 50
surfaces: derived 30 / 37
```

**PARAM/settings step:**

```text
uv run python scripts/check_param_law_sync.py
[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 — UCITS investment powers and limits
[WARN] portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later
Exit code: 0
```

The two portfolio-manager warnings are unchanged and outside this sprint's scope.

**`make ci`:** redirected to `C:\Users\yury_\AppData\Local\Temp\s262-make-ci.txt`, exit **2**. All first twelve steps passed. The dependency-audit attempt exits 1 before obtaining an advisory report; **dependency audit NOT RUN** because the offline boundary blocks external DNS/connect calls. The two subsequent Make recipe steps passed separately. Overall CI is not green.

```powershell
$env:UV_OFFLINE='1'
$env:PYTHONUTF8='1'
$env:PYTHONPATH=(Join-Path $env:TEMP 's262-offline-guard')
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='http.proxy'
$env:GIT_CONFIG_VALUE_0='http://127.0.0.1:9'
make ci > "$env:TEMP\s262-make-ci.txt" 2>&1
$s262Exit=$LASTEXITCODE
```

Actual coverage/test output and the audit's terminating output:

```text
TOTAL                                                           20156      0   4266      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
========= 4520 passed, 8 skipped, 2470 warnings in 647.93s (0:10:47) ==========
uv run python scripts/check_dependency_audit.py
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /pypi/aiohappyeyeballs/2.7.1/json (Caused by NewConnectionError("HTTPSConnection(host='pypi.org', port=443): Failed to establish a new connection: S262 offline proof: external network NOT RUN"))
make: *** [Makefile:59: ci] Error 1
make ci exit=2
```

| Step | Outcome |
| --- | --- |
| 1. Ruff | PASS, exit 0 |
| 2. Format | PASS, exit 0 |
| 3. Mypy | PASS, exit 0; 1,172 source files |
| 4. Import-linter | PASS, exit 0; 4 kept, 0 broken |
| 5. Module size | PASS, exit 0; all touched/new Python files below 200 |
| 6. Module header | PASS, exit 0 |
| 7. Law coverage | PASS, exit 0; derived rollups above |
| 8. PARAM/settings sync | PASS, exit 0; exact output above |
| 9. Sprint status | PASS, exit 0; README/spec both BUILT |
| 10. Markdown links | PASS, exit 0 |
| 11. Version scheme | PASS, exit 0; version and lock untouched |
| 12. Pytest | PASS, exit 0; 4,520 passed, 8 skipped, 100.00% |
| 13. Dependency audit | NOT RUN offline; attempted boundary refusal, exit 1 |
| 14. Detect secrets | PASS separately, exit 0; no baseline change |
| 15. Untracked secrets | PASS separately, exit 0 |

```text
uv run pre-commit run detect-secrets --all-files
Detect secrets...........................................................Passed
Exit code: 0
uv run python scripts/check_untracked_secrets.py
detect-secrets (untracked): no untracked files to scan
Exit code: 0
```

Markdown lint also passed. The command modules passed `uv run mypy --explicit-package-bases scripts/switch_llm_provider.py scripts/switch_llm_config.py scripts/switch_llm_azure.py scripts/switch_llm_apply.py scripts/switch_llm_proof.py`: `Success: no issues found in 5 source files`, exit 0. The Make recipe does not include scripts in mypy, so this is separate proof. Test-only fixture refinements after the full run were independently broken/restored; production source did not change. A prior secret-hook run reported file changes because the handback was edited concurrently; the steady-tree retry above passed with no baseline update.

**`make gate-ran`:** NOT RUN — no push is authorized, so no remote gate is claimed.

**Not met / verified failing:** overall `make ci` is not green (exit 2 at the offline dependency audit). Dependency audit and live checks are NOT RUN offline. No MERGED, remote-gated, deployed or live-proven claim.

---

## Return notes

- `main` advanced during the build to `80322272e655432c3e0377d956c7b3dc959b3eeb`; all comparisons use the recorded branch-cut SHA `ceec5bb605271295b06e1ca1f04df2a42ffc1d4d`. No merge from main was performed.
- Four new tests now use named dummy credential constants after detect-secrets flagged literal keyword assignments; the values and behavior are unchanged, and all 16 affected cases passed again. No baseline update or detector suppression.
- Scope held; excluded fidelity paths, deliberator, contracts, version/lock and tracker files are untouched. All evidence is local/unit; the operator container still uses its fake client.
- Correction: `orchestration/laws/laws.md` does not exist; the laws INDEX points to `orchestration/laws/dispatcher/laws.md`, read whole before code. The CI recipe has 15 steps, including sprint status; AGENTS.md's short form says 14.
- Law reading found no conflict beyond D9's authorized amendments. The law checker does not print successful rollup lines; actual derived counts were pasted explicitly instead.
- The initial failed-update mutation was masked by empty stdout failing JSON parsing. The failure fixture now returns valid JSON with a nonzero status, and removing the exit-status guard independently fails D7. The dashboard key refusal had a second adapter guard; its test now asserts missing selected credentials stop before factory construction.
- Empty `MASTER_LLM_PROVIDER` preserves the exact input objects after tag validation. Public usage/stop-reason aliases preserve older `_usage` imports; no deliberator test was edited. `build_app` stays small by moving pack loading, not trimming its behavior.
- Proof retry scope is DL-282's recorded amendment: use original snapshots when available; otherwise all non-master targets are required. The command constructs Postgres directly from the validated DSN when the graph is not injected, avoiding a development-memory fallback.
- **Live execution NOT RUN:** the command, deployment script and OpenAI adapter were not run against Azure, a live graph or a model. Env-only replica startup is unproven; paid `gpt-5.5` effort acceptance and the 4,096-token cap for real interpret/explain calls are unproven; return to Anthropic is unproven. F1a/F1b/F2 and remote gates belong to the planner's authorized post-merge sequence.

---

## Planner's review at the merge — 2026-10-09

Re-measured by the planner in `../ta-s262`, not taken from the handback.

- **Scope.** The checklist's scope command against the branch-cut commit `ceec5bb6` prints nothing:
  no fidelity decision path, no `agents/deliberator/` file, no graph vocabulary, no tracker. No
  security baseline, workflow or `Makefile` change. Every changed file is LF in the index.
- **Existing tests.** Six existing test files are edited, as specified: the two probe counts
  (12 to 13), the two chat-binding patches (they now patch `build_operator_llm`), the rider, and the
  one constant `VENDOR_ADAPTER_CLASSES`.
- **The packs.** The diff of `trading_credential_tests.json` and `trading_secrets.json` is added
  lines only. The operator's OpenAI probe and key pair sit before its Anthropic ones; the order
  carries no meaning.
- **The deploy script.** It parses with no error. Its real `Get-AgentEnv`, run with the cluster
  calls stubbed, gives each deliberator `DELIBERATOR_LLM_PROVIDER=openai` once (no key passed
  twice), the operator `OPERATOR_LLM_PROVIDER=openai`, the master `MASTER_LLM_PROVIDER=openai`, and
  leaves the scanner's and execution's lists as they were. The same functions on `main` give the
  deliberators `anthropic`: the revert this sprint removes.
- **Guards.** 32 things broken one at a time against the sprint's fourteen test files, each restored:
  30 went red. One of the other two was the planner's own mistake (a key under a variable name the
  rule does not cover); its corrected form, the operator's OpenAI probe taken out of the real pack,
  is red. The last was a real gap: removing the check that the value was applied after an update left
  every test green.
- **Two changes made by the planner on the branch** (`e487cec3`):
  1. *An apply with nothing to change waited fifteen minutes and exited 1.* Every app already on the
     declared value means no update, so no container restarts and no fleet check can follow; the
     command now says so and exits 0 at once, writing no evidence. Measured before the change with
     the sprint's own fake Azure: exit 1, `proof failed: no FleetPreflight since the start`. The spec
     had not said what this case should do: the omission was the spec's.
  2. *A test for an update that did not take:* the update call succeeds, the value on the app is
     unchanged, the command exits 1 naming the app. With it, the surviving break above is red.
  Both are in `tests/test_switch_llm_planner_review.py`; removing either guard turns it red.
- **Seen and accepted.** `FleetPreflight.checked_at` is written to the second and the command's start
  instant is not, so a fleet check inside the same second as the start would not count; the master
  starts tens of seconds after an update. The proof read lists every `AgentInstance` at each poll,
  which is acceptable for a command run by hand a few times a year.
- **Version.** MINOR, `0.124.00` to `0.125.00`; `uv lock` changed the version line alone (180
  packages).

**Still owed after the merge, none of it proven here:** F1a (the command against the fleet, with the
retag and the master's three narrow updates), F1b (one paid exchange through the dashboard chat on
`gpt-5.5`), F2 (the first scheduled run), and the return to Anthropic.

---

## Appendix — the planner's prototype of the OpenAI operator adapter

Built on a throwaway worktree on 2026-10-09 and type-checked there. It was never run against the
vendor. Port it; it is not finished. **What it lacks:** the `length` stop of D5 (it returns the
fallback instead of raising); a `description` on the function; and it imports two private helpers
from `kernel/llm_openai.py`, which you may make public or move rather than import with an underscore.

```python
"""OpenAI tool-use adapter for operator commands and explanations.

Agent: kernel
Role: return one forced function call's arguments from OpenAI Chat Completions.
External I/O: OpenAI API over HTTPS.
"""

from __future__ import annotations

import importlib
import json

from kernel.llm import STOP_REASON_UNKNOWN
from kernel.llm_openai import ConfigurationError, _stop_reason, _usage
from kernel.llm_tokens import LLMUsage

_ANSWER_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
}


class OperatorOpenAILLMClient:
    """OpenAI function-calling implementation of the operator LLM port."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "gpt-5.5",
        max_tokens: int = 4096,
        effort: str = "max",
    ) -> None:
        """Create the OpenAI client, failing early without credentials."""
        if not api_key:
            raise ConfigurationError("OPENAI_API_KEY is required")
        try:
            openai = importlib.import_module("openai")
        except ModuleNotFoundError as exc:
            raise ConfigurationError("openai package is not installed") from exc
        self._client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.effort = effort
        self.last_stop_reason = STOP_REASON_UNKNOWN
        self.last_usage: LLMUsage | None = None

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Call OpenAI with one forced function and return its arguments."""
        name = "parse_intent" if tool_schema else "answer_question"
        self.last_usage = None
        response = self._client.chat.completions.create(
            model=self.model,
            max_completion_tokens=self.max_tokens,
            reasoning_effort=self.effort,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "parameters": tool_schema or _ANSWER_SCHEMA,
                    },
                }
            ],
            tool_choice={"type": "function", "function": {"name": name}},
        )
        self.last_stop_reason = _stop_reason(response)
        self.last_usage = _usage(response)
        data = _arguments(response)
        return json.dumps(data) if tool_schema else str(data.get("answer", ""))


def _arguments(response: object) -> dict[str, object]:
    for choice in getattr(response, "choices", ()):
        message = getattr(choice, "message", None)
        for call in getattr(message, "tool_calls", None) or ():
            raw = getattr(getattr(call, "function", None), "arguments", "")
            try:
                data = json.loads(raw)
            except (TypeError, ValueError):
                break
            return dict(data) if isinstance(data, dict) else {}
    return {"outcome": "refused", "reason": "model returned no tool result"}
```

The wire form of a reply, as the installed SDK parses it (`openai` 2.49.0, offline):

```json
{"id": "x", "object": "chat.completion", "created": 0, "model": "gpt-5.5",
 "choices": [{"index": 0, "finish_reason": "stop",
   "message": {"role": "assistant", "content": null,
     "tool_calls": [{"id": "c1", "type": "function",
       "function": {"name": "parse_intent", "arguments": "{\"outcome\": \"intent\"}"}}]}}]}
```
