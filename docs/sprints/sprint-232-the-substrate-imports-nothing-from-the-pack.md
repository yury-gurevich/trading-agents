<!-- Agent: planning | Role: sprint handover -->
# Sprint 232 — the substrate imports nothing from the pack and names none of its agents

**Phase:** Etalon-first continuous improvement (DL-19) · next leg P20, item **E20.2**
**Branch:** `sprint-232-the-substrate-imports-nothing-from-the-pack`
**Status:** MERGED `f685260e` · tag `v0.114.01` · 2026-09-26 · not deployed (operator approval owed)
**Version:** `0.114.01` at merge (built as `0.113.01`; S233 took it, and S234's MINOR moved `main` to `0.114.00`)
**Effort:** M. The plan sized E20.2 at **L (2.5)** because it expected the grant table to move and every
agent's imports to change. Both expectations are measured false below
**Decisions:** [ADR-0012](../decisions/0012-platform-domain-separation.md) (the wall, declared) ·
[DL-12](../design-log.md) (the grant leak, closed in S84–S86) · work-queue **84** · this sprint files
**DRIFT-075** · the builder records its decisions as the next free DL number (**DL-228**: DL-227 is S231's)

> **Why this bump kind.** No new capability. ADR-0012 already forbids the substrate to import or name
> the pack, and `MST-NEV-05`/`MST-DEP-03` already promise it for the master. This sprint moves a small
> amount of vocabulary, turns one roster into pack data, and adds the enforcement that makes the promise
> checkable. A refactor that makes an existing promise true is a PATCH.

> 🩹 **Planner review, 2026-09-26 (local planner session): cleared to build.**
> **Design decision 1 is confirmed: the kernel.** Technical calls are delegated to the planner, so the
> operator is told rather than asked. The rejected homes are argued below, and the kernel already hosts
> `AgentContract`, `Capability`, `AgentFault` and `Envelope`.
> **Re-measured on `main` @ `89dcbb08`, which changes 0 code files since `c51bf9e`:** row 1 (0
> `DEFAULT_GRANTS` in any `.py`), row 8 (10 lines: 3 production, 7 tests), row 10 (68 first-party modules,
> exactly `contracts`, `contracts.common`, `contracts.master` from the pack), row 11 (the islands
> contract lists 12, with neither master nor deliberator), row 17 (both hashes equal), the guardrail sizes
> and `agents/master/Dockerfile:9` all reproduce.
> 🩹 **One correction: DL-227 is taken by S231**, which merges first. Record this sprint's decisions as
> **DL-228** and re-check at merge. S231 touches no file in this blast radius (`scripts/sp500_*`,
> `replay_universe*`, `replay_dataset_sources.py`, and their tests). It bumps to `0.113.00`, so this PATCH
> lands at the next free PATCH above that.

**Builder:** this cloud session (Claude Code); the planner's review above clears it to start. If the work goes
to Codex instead, the handover block below is self-contained.
**The build environment has no `.env`, no Azure access and no live graph. Every proof in this sprint is
on fixtures, and no handback may claim live evidence.**
**If a number you measure differs from one written here, stop and report. Do not adjust and continue.**

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the master amendments this spec names (the law-cycle answer is Yes). Any other clause you believe is wrong is a `drift-register.md` row plus a report, never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: master **`MST-TYP`**, **`MST-NEV`**, **`MST-SEC`**, **`MST-DEP`**; deliberator
**`DLIB-NEV-05`**. **No law book binds `kernel/` or `scripts/`**; for those, ADR-0012 §Decision 2 and
`CLAUDE.md` bind.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.** The law is more likely right than the spec.
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answer before step 5

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**The planner's answer is Yes, on both counts.** `contracts/master.py` leaves `contracts/`, and
`contracts/common.py` changes. The master also gains a guarantee it has never made: it will import **no**
pack module. Today it imports `contracts.master`, and `MST-NEV-05` covers only trading **agents**. The
law cycle owed, in this unit of work:

1. **Master laws LOCKED v1.5 → v1.6.** Bump the version and add a Changelog line naming DL-12, ADR-0012
   and this sprint:
   - **`MST-NEV-01`** names `DEFAULT_GRANTS`, which S84 deleted on 2026-06-22. The guarantee is
     unchanged; its subject becomes the grant policy the pack supplies.
   - **`MST-SEC-03`** names `DEFAULT_GRANTS` in `grants.py` and says the table *"cannot be changed by
     runtime config"*. The same book's `PARAM` table (v1.5) marks `grant_policy_b64` and
     `grant_policy_path` `Tunable YES`, and the policy arrives as a deploy-time environment variable.
     Rewrite the clause to what the code guarantees, and no more (design decision 6): the pack's grant
     policy is the only privilege table, the master image ships none, and master reads it once, when it
     starts. 🪤 It must **not** claim the variable cannot be changed, because nothing enforces that. That
     is DRIFT-058's lesson: a clause whose check cannot fail.
   - **`MST-DEP-03`** names `DEFAULT_GRANTS`. Its subject becomes the pack data injected at start-up
     (grant policy, secret map, credential tests) plus the `AgentDefinition` nodes.
   - **`MST-TYP-01`** names the path `contracts/master.py`, and that file moves (scope item 2).
   - **A new clause, `MST-DEP-05`** (the next free `DEP` number): master imports only the substrate
     (`kernel` and its own package) and never a pack module. That rules out the pack vocabulary
     (`contracts`), every other agent, `orchestration` and `surfaces`.
2. **Master `test-plan.md`.** Move the header to v1.6; it reads **v1.4** today, although `laws.md` is at
   v1.5. The `MST-NEV-05` and `MST-DEP-03` rows must cite a contract that actually lists `agents.master`,
   and they go 🟩 only where a functional test proves every conjunct (conventions §7a). Add an
   `MST-DEP-05` row. Two existing tests in `agents/master/tests/test_master_agent.py`,
   `test_activate_uses_injected_grant_policy` and `test_substrate_default_knows_no_agent_types`, cite no
   clause today. They may cite `MST-SEC-03`/`MST-DEP-03` if, and only if, they prove the amended text
   whole.
3. **Deliberator `test-plan.md`, one row.** `DLIB-NEV-05` (*"Never imports another agent or
   `orchestration`"*) is ⬜ `_tbd_`. Once `agents.deliberator` is in the islands contract, the row can
   read 🧱 and name both contracts. The clause text does not change, so the DLIB version does not move.
4. **Rollups** in both `docs/laws/ledger.md` and `docs/laws/INDEX.md`. `make ci` derives them; never
   declare them.
5. **`drift-register.md`, Master section: DRIFT-075** (the next free ID). It records rows 2, 3 and 12 of
   *Measured* below, with status `CORRECTED (S232)`.

🪤 **The rollup is derived, not declared.** Let the gate tell you the number.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `contracts/master.py` → `kernel/handshake.py` | `agents/master/laws/laws.md` + `test-plan.md`; conventions §2, §4, §7a | `MST-TYP-01` (the fields; the messages are `_Frozen`; `AgentState` is a `StrEnum`; the clause names the path), `MST-IN-01`/`IN-02`, `MST-OUT-01`/`OUT-02` |
| `agents/master/agent.py`, `http_server.py`, `store.py`, and 7 test modules | same | `MST-NEV-05`, `MST-DEP-03`, new `MST-DEP-05` |
| `agents/master/laws/laws.md`, `test-plan.md` | same; conventions §4 (amendment), §7a (the summary mirrors the law) | `MST-NEV-01`, `MST-SEC-03`, `MST-DEP-03`, `MST-TYP-01`, `MST-DEP-05` |
| `contracts/common.py` (re-export) | the `TYP` clauses of every agent whose payloads carry these types; `tests/test_contract_required_fields.py` | no field, class or base may change identity |
| `.importlinter` | master `test-plan.md` (`MST-NEV-05`/`MST-DEP-03`, both 🧱); `agents/deliberator/laws/laws.md` + `test-plan.md` (`DLIB-NEV-05`) | these rows cite a contract that does not list their agent |
| `kernel/serve_transport.py`, `scripts/sb_sas_plan.py`, `scripts/servicebus_prepare_routes.py`, `tests/test_served_agent_images.py`, the new pack roster | no law book. ADR-0012 §Decision 2: *"the agent roster … is pack-provided input to the substrate, never hardcoded in it"*. `CLAUDE.md` (module-size baseline) | `sb_sas_plan.py` is baselined at **212** lines and may not grow |
| `agents/master/Dockerfile` | `CLAUDE.md` (the full cycle for anything that changes production); DL-12, S86: *"the same image runs any pack"* | a production image |
| `docs/decisions/0012-platform-domain-separation.md` | this template: *"No ADR reversal"* | a dated **Correction** section only, on the ADR-0025/0031 precedent |

⚠️ **The one invariant: no payload changes shape, name or identity.** Every moved class keeps its name,
fields, config and base. `contracts.common._Frozen`, `contracts.common.Provenance` and
`contracts.common.Explanation` stay importable and are **the same objects** as the kernel's. Every
message serialises to the same JSON bytes, and the deliberator's and operator's prompt-recipe hashes do
not move. If any of these would change, stop and report.

---

## Goal

After this sprint the substrate, meaning `kernel` and `agents/master`, imports nothing from the trading
pack and names none of its agents, and a gate says so. The master's handshake messages and the evidence
vocabulary every payload carries (`Provenance`, `Explanation` and the frozen base) live in the kernel.
`contracts/` holds only trading vocabulary, and the master image stops copying it. The served-agent
roster is pack data instead of a kernel constant. `lint-imports` enforces the wall with a contract whose
source is the substrate, and the islands contract lists all 14 agents. The master law book names only
things that exist.

## Why (context)

P20's exit is a second pack running on the same substrate with **zero substrate edits after E20.2**. That
makes this the last cheap moment to find the leaks. ADR-0012 declared the wall *de jure* in June and named
two leaks. Measured today, one of them is already closed, one is real and small, and there is a third
that the ADR did not name. The master law book still cites a symbol that was deleted three months ago,
and its two import clauses rest on a contract that has never listed the master.

### Measured, 2026-09-25 — read these before designing

Every figure comes from the code at `c51bf9e` (= `main`), in a cloud checkout with no `.env`: AST
scans, `lint-imports` and a planted fixture. Nothing here is live.

| # | Claim | Value | How it was measured |
| --- | --- | --- | --- |
| 1 | 🩹 **The first named leak is already closed** | `DEFAULT_GRANTS` appears in **0** `.py` files. The grant policy is `orchestration/packs/trading_grants.json`, parsed by `agents/master/grants.py` (`parse_grant_policy`, `load_grant_policy`; 37 lines) and delivered as `MASTER_GRANT_POLICY_B64` | *[measured]* grep over every `.py`. [DL-12](../design-log.md): S84 (0.23.01) moved the table, S85 did the same for the secret map, S86 wired the deploy. The plan's E20.2 row repeats ADR-0012's June list without re-measuring it |
| 2 | Where `DEFAULT_GRANTS` is still named | master `laws.md` **`MST-NEV-01`**, **`MST-SEC-03`**, **`MST-DEP-03`**; the `MST-SEC-03` and `MST-DEP-03` rows of `test-plan.md`; ADR-0012's *Known leaks*; historical docs (the build plan, sprint docs, the state archive) | *[measured]* grep over `*.md` |
| 3 | `MST-SEC-03` contradicts its own book | the clause says *"cannot be changed by runtime config"*; the `PARAM` table (v1.5) marks `grant_policy_b64` and `grant_policy_path` `Tunable YES`, and the policy arrives as a deploy-time environment variable | *[measured]* `agents/master/laws/laws.md` |
| 4 | Which parts of `contracts/` are substrate | **`master.py`** (107 lines: `AgentState`, `EHLOMessage`, `ACTIVATEMessage`, `DRAINMessage` and the master `CONTRACT`) and **3 names** in `common.py`: `_Frozen`, `Provenance`, `Explanation`. The rest is trading: `Ticker`, `Action`, `RegimeLabel`, `Money`, `ScanRequest` and `Window` in `common.py`, and all **24** other modules | *[measured]* every module read. This matches ADR-0012's own first-cut table (*"`common/` base classes … master msgs"*). The law template, which the ADR counts as substrate, requires every agent to record provenance and explain rejections, so `Provenance` and `Explanation` are substrate by the same table |
| 5 | Every import of a `contracts` module | **934** statements in **491** files (kernel, contracts, agents, orchestration, surfaces, scripts, tests, probes) | *[measured]* AST, module-level and nested imports |
| 6 | Of those, the ones naming a trading module | **829** statements in **467** files, 40 of which import substrate and trading names in one statement | *[measured]* AST |
| 7 | Of those, the ones naming only a substrate candidate | **105** statements in **103** files: **11** import `contracts.master`; **94** import only `_Frozen`/`Provenance`/`Explanation` from `contracts.common` | *[measured]* AST |
| 8 | 🎯 **Imports that cross the wall today (substrate → pack)** | **10** import lines in **10** modules, all `agents.master* → contracts.master`: **3** production (`agent.py:32`, `http_server.py:14`, `store.py:13`) and **7** tests (`credential_probe_testkit`, `test_credential_test`, `test_master_agent`, `test_master_entrypoint`, `test_remediation_activation`, `test_remediation_auto_activation`, `test_secret_map`). `kernel → pack`: **0** | *[measured]* `lint-imports` run with the candidate contract from scope item 4: *"1 kept, 1 broken"*, and exactly these 10 lines. The 11th importer of `contracts.master`, `tests/test_contract_required_fields.py:12`, is outside the substrate |
| 9 | Pack → substrate imports (legal, and unchanged here) | for example, `orchestration/master_serve.py` (the trading master's composition root) imports 6 `agents.master` modules, and `orchestration/packs/trading_vault_probes.py` imports `agents.master.vault_seed` | *[measured]* grep |
| 10 | Master's runtime import closure | a fresh interpreter importing `agents.master.entrypoint` loads **68** first-party modules: 40 from `kernel`, 24 from `agents.master`, the `agents` package itself, and **3 from the pack**: `contracts`, `contracts.common` and `contracts.master` | *[measured]* `sys.modules` after the import |
| 11 | 🪤 **The islands contract has never listed the master or the deliberator** | `agents-are-islands` lists **12** of the **14** agent packages. On a planted fixture where `agents.master` imports `agents.scanner` and `agents.deliberator` imports `agents.execution`, the repo's own `.importlinter` reads *"4 kept, 0 broken"* and exits 0. The candidate contracts on the same fixture read *"0 kept, 2 broken"*, exit 1 and name both plants; on the clean fixture they read *"2 kept"* and exit 0 | *[measured]* a fixture of empty packages mirroring the five roots and the 14 agents |
| 12 | So two 🧱 rows prove nothing | `MST-NEV-05` and `MST-DEP-03` are 🧱 on *"import-linter: Agents may not import one another"*, and `DLIB-NEV-05` is ⬜ `_tbd_`. The law gate accepts any 🧱 row that contains the word `import-linter`, whatever the contract covers | *[measured]* `scripts/law_coverage_status.py:16-22` |
| 13 | Widening the islands contract on today's tree | **0** violations: the contract still holds with `agents.master` and `agents.deliberator` added | *[measured]* `lint-imports` with the candidate config |
| 14 | 🩹 **A leak the ADR did not name, of the same kind: the served roster** | pack agent-type string literals in substrate code (`kernel/` and `agents/master/`, docstrings excluded): **9**, all in `kernel/serve_transport.py` lines 22–51 (`SERVED_AGENT_TYPES`, `DELIBERATOR_PEER_AGENT_TYPES`, `DELIBERATOR_MANAGER_TYPE`, and `"deliberator"` in `image_dir_for_served_agent`). `agents/master/`: **0** | *[measured]* AST string constants compared with the 15 keys of `trading_grants.json`, plus `"deliberator"` |
| 15 | Who reads the roster | **3** files: `scripts/sb_sas_plan.py` (212 lines, baselined), `scripts/servicebus_prepare_routes.py` (119 lines; `deploy-agents.ps1` runs it in `Prepare-ServiceBusRoutes`, line 369, during `up` only) and `tests/test_served_agent_images.py`. The agents use only `consumer_from_env` and `request_topic` (8 files), and both stay | *[measured]* grep |
| 16 | Other trading content in the kernel (not agent types) | `kernel/deliberation_prompts.py` (199 lines) holds the champion prompts, with worked trading examples (AAPL, NVDA, a −3 % stop, `max_sector_pct`), and is one of the 7 modules hashed into the deliberator's recipe digest. `kernel/market_pack.py` declares a market-shaped protocol (`exchange`, *"one tradeable universe"*) that only `surfaces/context.py` uses. `kernel/__init__.py` imports both, the first through `kernel.deliberation`, so the master's closure (row 10) loads them | *[measured]* read; `sys.modules` |
| 17 | Prompt-recipe hashes at the base | deliberator `31fe77975825cb3dadcc7989ed8c7d37ee571dc719dc612a795c671c189b1480`; operator `3fcfed8fe7d67a881da04268d7119c5aab55402a8458927c4bb600262c94c259` | *[measured]* `PROMPT_RECIPE_HASH` imported at `c51bf9e` |
| 18 | Nothing keys on a class's module path | the only digest over module names is `kernel/prompt_recipe.py`, which covers the declared prompt modules. No bus, graph or envelope code reads `__module__` or `__qualname__` | *[measured]* grep over kernel, agents, orchestration, surfaces and contracts |
| 19 | `MST-TYP-01`'s test pins the base class | `tests/test_contract_required_fields.py:38-40` asserts `issubclass(message, contracts.common._Frozen)` for the three master messages | *[measured]* read |
| 20 | Master tests read trading pack files | **12** files read 6 pack files through `agents/master/tests/helpers.py`. This is data read by path, not an import | *[measured]* grep |
| 21 | Nothing reads the master's `CONTRACT` | **0** importers of `contracts.master.CONTRACT` | *[measured]* grep |
| 22 | `contracts.common.RunTrigger` is dead | **0** importers. `orchestration.trigger.RunTrigger` is a different, live class | *[measured]* AST |
| 23 | The master image ships the trading vocabulary | `agents/master/Dockerfile:9` is `COPY contracts/ contracts/`, which copies all 26 modules | *[measured]* read |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (A1–A3 below). Watch them fail on the base.
2. **The substrate vocabulary moves into the kernel.**
   - `kernel/payload.py` (new) holds the **one** frozen base, `Provenance` and `Explanation`, moved from
     `contracts/common.py` verbatim, docstrings included.
   - `kernel/handshake.py` (new, via `git mv contracts/master.py`) holds `AgentState`, `EHLOMessage`,
     `ACTIVATEMessage`, `DRAINMessage` and the master `CONTRACT`. Only three things change: the base
     import, the module header (`Agent: kernel`), and the `CONTRACT` text. Its `mission` and the `never`
     entry *"perform trading logic or place orders"* become pack-neutral, because the kernel names no
     trading concept (design decision 7).
   - `contracts/common.py` **re-exports** the three names explicitly, because mypy strict turns implicit
     re-export off. It aliases the kernel base as `_Frozen` and keeps every trading name. **No other
     import site changes**: the 134 statements in 133 files that import these names (rows 6 and 7) stay
     as they are.
3. **The master imports only the kernel.** Repoint the 10 lines in row 8, and
   `tests/test_contract_required_fields.py`. Drop `COPY contracts/ contracts/` from
   `agents/master/Dockerfile`.
4. **The wall goes into `.importlinter`.** This adds no CI step, because `lint-imports` already runs.
   - `agents-are-islands` gains `agents.deliberator` and `agents.master`, for 14 modules in all.
   - A new forbidden contract, `substrate-imports-no-pack`, has `source_modules` = `kernel` and
     `agents.master`, and `forbidden_modules` = `contracts`, the 13 other `agents.*` packages,
     `orchestration` and `surfaces`. The existing kernel contract stays.
5. **The served roster becomes pack data.** A new file, `orchestration/packs/trading_served_agents.json`,
   holds the served types, the deliberator's peer, manager and reply types, and the image directory for
   each served type. `kernel/serve_transport.py` keeps `request_topic`, `reply_topic` and
   `consumer_from_env`, and loses the roster and `image_dir_for_served_agent`. A small new loader in
   `scripts/` reads the JSON by path, without importing `orchestration`, and serves `sb_sas_plan.py`,
   `servicebus_prepare_routes.py` and the test. The planned routes and SAS grants stay identical (A6).
6. **A test for the wall at the level of names.** No production module in `kernel/` or `agents/master/`
   may hold a string literal (outside docstrings) equal to a pack agent type: a key of
   `trading_grants.json`, or a role or image name from the roster. It is red today, with 9 literals (row
   14).
7. **The law cycle** described in the law-cycle answer above.
8. **ADR-0012 gets a dated Correction section.** It records that leak 1 closed in S84–S86 (DL-12), that
   leak 2 and the served roster closed in S232, and which residue is deferred (see Out of scope). The *de
   jure → de facto* re-opening stays E20.5's to record.
9. **The design decisions** go into `docs/design-log.md` (the next free DL number) before implementation.

### Out of scope (do NOT build this sprint)

- **`kernel/deliberation_prompts.py`.** Trading prompts in the kernel are a leak (row 16), but moving the
  module changes a module name that is hashed into every future `LLMCall`'s recipe digest
  (`kernel/prompt_recipe.py` hashes `__name__`; S200). After the move, no recorded debate would be
  comparable with the new renderer. The move would also touch the LOCKED deliberator book (`DLIB-IDM-02`,
  `DLIB-OBS-07`), and the second pack does not deliberate. The DL records it; the module stays.
- **`kernel/market_pack.py`** and the imports `kernel/__init__.py` makes eagerly. Only the trading
  dashboard reads them, and a pack that is not a market registers nothing there. The DL records them;
  they stay.
- **The master tests reading trading pack files** (row 20). That is a data dependency, not an import, and
  moving 12 files buys the wall nothing.
- **Trading wording in master clauses that are true** (`MST-IDN-01`'s *"trading-system"*, `MST-NEV-02`'s
  examples, `MST-NEV-03`, `MST-ORD-02`). They hold for the only pack, and conventions §4 forbids
  amending a law for its wording. E20.5 rewords them once a second pack exists to test the wording
  against.
- **The supervisor and the operator.** Both carry trading rosters (`contracts/supervisor.py`'s
  `depends_on` names 11 agents), and both stay pack, per ADR-0012's first cut. Whether a second pack
  needs a substrate supervisor is E20.3's question. **Orchestration and the surfaces** are not in
  ADR-0012's table, and they stay on the pack side.
- **`contracts.common.RunTrigger`** (dead; row 22): neither moved nor deleted.
- **The agent side of the handshake.** `kernel/bootstrap.py` builds the EHLO as a dict because it could
  not import `contracts.master`. Once the messages live in the kernel it could use the type, but that
  would change every agent's boot path. Not in this sprint.
- **No new CI step, tracking surface or status doc** (next-leg-plan §5, the process freeze).
- **No `laws.md` edit** beyond the master amendments and the one DLIB test-plan row named above. **No
  ADR reversal.**

### The road not taken (LAW-06)

- **Move the trading modules out and keep `contracts/` as the substrate.** Rejected: that rewrites **829**
  statements in **467** files and touches all 15 Dockerfiles, only to relocate the side that is not
  moving.
- **A `contracts/platform/` subpackage.** Rejected: the substrate would live inside the pack's package,
  and the master image would still copy `contracts/` or need a partial `COPY`.
- **A new top-level `substrate/` package.** Rejected: a sixth root package, a `COPY` line in 15
  Dockerfiles and a new architecture layer. The kernel already hosts substrate vocabulary (`AgentContract`,
  `Capability`, `AgentFault`, `Envelope`) behind its own contract.
- **Put the vocabulary in the kernel, but rewrite every import site instead of re-exporting.** Rejected:
  134 statements in 133 files would change and 40 of them would split in two. The deliberator's context
  modules would change as well, which moves `PROMPT_RECIPE_HASH`.
- **Move `Window` too.** Rejected: it is a date range for data requests, and the substrate does not use it
  (ADR-0012 §3: no speculative generality).
- **Declare the wall with module lists alone and move nothing.** Rejected: `common.py` mixes both sides
  name by name, and import-linter works on whole modules.
- **A gate step that checks each 🧱 row names a contract that lists its agent.** Rejected under the
  process freeze. The rows get corrected, and A2 proves the contract covers the master.
- **The served roster as a Python module in `orchestration/packs/`.** Rejected: the deploy script would
  import pack Python under `uv run --extra azure`, and `orchestration/packs/__init__.py` imports
  `us_equities_sp500`, the failure shape of DL-218. Instead it is JSON read by path, like the grant policy
  and the secret map (DL-12, option a).
- **Leave the served roster for E20.3 to find.** Rejected: ADR-0012 names this kind of leak (*"the agent
  roster"*), and leaving a known one in place would make E20.3's count of substrate edits dishonest.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where the substrate vocabulary lives.** This spec recommends the kernel. 🚩 **The operator decides at
   review.** The builder does not start until the choice is confirmed. ✅ **Decided: the kernel**
   (operator, 2026-09-26; [DL-228](../design-log.md) Decision 1).
2. **The module names:** `kernel/payload.py` and `kernel/handshake.py`, unless the reviewer renames
   them.
3. **How the re-export works:** one base class, aliased as `_Frozen`, with explicit re-exports that mypy
   strict accepts.
4. **The exact text of the wall's contract:** the source and forbidden lists above, and whether the
   kernel's existing contract stays alongside it. Recommended: keep it; it costs nothing.
5. **The roster file and its loader:** the JSON shape (including the map of image directories), which
   module the loader lives in, and one sentence on how two packs' rosters would combine (not built).
6. **The amended master wording** of `MST-NEV-01`, `MST-SEC-03`, `MST-DEP-03` and `MST-TYP-01`, and the
   new `MST-DEP-05`. Each clause asserts only what a test or the gate can falsify.
7. **The pack-neutral text of the master `CONTRACT`** once it lives in the kernel.
8. **Whether the served roster belongs in this sprint or in E20.3.** Raised at review. The operator
   delegated it (2026-09-26: *"make a rational and document it"*). ✅ **Decided: this sprint.** The
   reasons for and against, why the case for it wins, and what would reverse it are in
   [DL-228](../design-log.md) Decision 8.

🪤 **Take the next free DL number, then re-check it at merge.** The newest entry was **DL-226** when this
was specced; S231 has since taken **DL-227**, so this sprint's is **DL-228**. The drift register's newest
ID is **DRIFT-074**.

---

## Blast radius — measured 2026-09-25

| What | Detail |
| --- | --- |
| Files changed | **moved:** `contracts/master.py` (107) → `kernel/handshake.py`. **new:** `kernel/payload.py`, `orchestration/packs/trading_served_agents.json`, a roster loader in `scripts/`, the wall tests. **edited:** `contracts/common.py` (90), `kernel/serve_transport.py` (72), `agents/master/agent.py` (182), `http_server.py` (90), `store.py` (**194**), the 7 master test modules in row 8 (87–197 lines), `agents/master/Dockerfile` (18), `.importlinter` (58), `scripts/sb_sas_plan.py` (**212**, baselined), `scripts/servicebus_prepare_routes.py` (119), `tests/test_served_agent_images.py` (93), `tests/test_contract_required_fields.py` (114). **laws and docs:** master `laws.md` (224) and `test-plan.md` (54), one row of the deliberator `test-plan.md`, `docs/laws/drift-register.md`, `ledger.md`, `INDEX.md`, ADR-0012 (88), `docs/design-log.md` |
| Imports crossing the wall | **10** lines today (row 8), **0** after. Pack → substrate imports are unchanged. Import sites repointed: **11** (`contracts.master`) plus the **3** roster readers |
| Agents affected | **master** (imports, image, laws) and **deliberator** (named in the islands contract only; no code). No agent imports another, and the widened islands contract proves it |
| Contract change? | **yes**: `contracts/master.py` leaves and `contracts/common.py` re-exports, so the law cycle above is owed |
| Graph vocabulary change? | **no**: no label or property |
| New env keys / tunables | **none**. The grant policy and secret map already travel as pack data (S86) |
| Deploy implication | **Image-only retag.** Every image copies `kernel/`, so all 15 rebuild, and the master image loses `COPY contracts/`. The plan expected a full `up` because it assumed the grant table still had to move; that happened in S84–S86. `servicebus_prepare_routes.py` runs only during `up`, so A6 proves its plan identical on fixtures, and the next `up` exercises it live |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`, once the operator has confirmed decision 1.
3. **Plant the failing tests first** (A1–A3) and watch them fail on the base. Paste the red output.
4. **Implement** scope items 2–6.
5. **Law cycle** (item 7): the amendments, the new clause, the test-plan rows, the docstring citations and
   DRIFT-075. Then the ADR correction (item 8).
6. **Prove the guards can fail (DL-70).** For A1, A2, A3 and A6, break the implementation, watch each
   test go red, and restore it.
7. **Measure the invariant.** Print both `PROMPT_RECIPE_HASH` values and compare them with row 17. Print
   the summary from `lint-imports`.
8. **`make ci` green** — every step of the `ci:` target, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 the master's import closure holds no pack module | a fresh interpreter (a subprocess) imports `agents.master.entrypoint` | `sys.modules` holds no `contracts*`, no other `agents.*`, no `orchestration*` and no `surfaces*`. **Red on the base:** `contracts`, `contracts.common`, `contracts.master`. Cites `MST-DEP-05`, and `MST-NEV-05`/`MST-DEP-03` only if it proves them whole |
| A2 | 🎯 the repo's own `.importlinter` catches a leak into or out of the substrate | a temporary package tree mirroring the 5 roots and the 14 agents, with plants `agents.master → agents.scanner`, `agents.master → contracts` and `agents.deliberator → agents.execution`; `lint-imports --config <the repo's .importlinter>` runs in a subprocess | exit 1, with each plant named in the output; the clean tree exits 0. **Red on the base:** exit 0, *"4 kept, 0 broken"* (row 11). Cites `MST-NEV-05`, `MST-DEP-03`, `MST-DEP-05` and `DLIB-NEV-05` |
| A3 | 🎯 no substrate module names a pack agent | the AST of every production module in `kernel/` and `agents/master/`, docstrings excluded, compared with the pack's agent types | **0** literals. **Red on the base:** 9, all in `kernel/serve_transport.py` |
| A4 | the moved types are the same types | import both paths | `contracts.common._Frozen is` the kernel base, `contracts.common.Provenance is kernel.payload.Provenance`, and the same for `Explanation`. `MST-TYP-01`'s required fields, the `_Frozen` bases and `AgentState`'s `StrEnum` all hold at the new path (the existing test, repointed). Cites `MST-TYP-01` |
| A5 | the wire does not move | fixtures: an EHLO dict shaped the way `kernel/bootstrap.py` sends it, an `ACTIVATEMessage`, and a pack payload that carries `Provenance` and `Explanation` | the dict parses, and each `model_dump_json()` equals a literal captured on the base |
| A6 | 🪤 the Service Bus plan does not move | today's constants copied into the test as literals | the route list and the SAS-grant plan built from the pack roster equal the plans built from the literals. Every served type maps to the same image directory, and that directory holds a `Dockerfile` |
| A7 | the master image carries its whole closure, and no `contracts/` | `agents/master/Dockerfile`; A1's closure | no `COPY contracts/`, and every module in the closure lies under a copied path |
| A8 | 🪤 the prompt digests do not move | none | `test_the_deliberator_declares_every_module_that_builds_its_prompt` passes **without** `kernel.payload` in `PROMPT_MODULES`, and both hashes equal row 17. This is a handback measurement, not a committed test: a pinned hash would break on every later, legitimate prompt change |
| A9 | an unknown type is still refused, and no policy still means no types | the existing `test_activate_unknown_agent_type_raises`, `test_activate_uses_injected_grant_policy` and `test_substrate_default_knows_no_agent_types` | they pass unchanged. The last two cite the amended `MST-SEC-03`/`MST-DEP-03` if they prove them whole |

---

## Success factors

- [ ] `lint-imports` keeps every contract on the tree, including `substrate-imports-no-pack` and a
      14-agent islands contract (was 12).
- [ ] A fresh interpreter importing `agents.master.entrypoint` loads **0** pack modules (was 3) — A1.
- [ ] The repo's `.importlinter` fails on each planted leak (A2); on the base it let all three through.
- [ ] Substrate code holds **0** pack agent-type literals (was 9) — A3.
- [ ] `agents/master/Dockerfile` does not copy `contracts/` (A7).
- [ ] Every moved type is the same object under both paths, and the JSON is byte-identical (A4, A5).
      Both prompt-recipe hashes equal row 17 (A8).
- [ ] The planned Service Bus routes and SAS grants are unchanged (A6).
- [ ] Master laws at v1.6: `MST-NEV-01`, `MST-SEC-03`, `MST-DEP-03` and `MST-TYP-01` amended and
      `MST-DEP-05` added. Test plan at v1.6, the `DLIB-NEV-05` row, DRIFT-075, and rollups in
      `ledger.md` and `docs/laws/INDEX.md` as `make ci` derives them.
- [ ] ADR-0012 carries the dated correction.
- [ ] Design decisions recorded, with the rejected alternatives.
- [ ] Guards A1, A2, A3 and A6 planted, watched to fail and restored, stated for each guard.
- [ ] Every touched module under 200 lines; `sb_sas_plan.py` at 212 or fewer.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **Two frozen bases.** If the kernel defines a base and `contracts/common.py` keeps its own `_Frozen`,
the master messages and the trading DTOs stop sharing a base. `issubclass(..., _Frozen)` (row 19) then
passes or fails depending on which class a test imports. Keep one class and alias it.
🪤 **`contracts/**` is exempt from `D101`/`D106`, and the kernel is not.** A public class that moves into
the kernel needs a docstring. Either keep the base private or document it.
🪤 **mypy strict turns implicit re-export off.** In `contracts/common.py`, `from kernel.payload import
Provenance` stays private to mypy unless it is re-exported explicitly (`import X as X`, or `__all__`).
🪤 **The prompt-recipe closure follows `__module__`.** `tests/test_prompt_recipe.py` walks the names bound
at runtime in `agents.deliberator.context*` and `kernel.deliberation`, and follows every one whose
`__module__` starts with `kernel.`. A moved class bound at runtime there would pull `kernel.payload` into
the closure and fail the test. Measured: `context_values.py` imports `Explanation` only under
`TYPE_CHECKING`, so the expected result is no change; verify it. If the test does fail, **do not** add
`kernel.payload` to `PROMPT_MODULES`, because that moves every future recipe digest. Exempt it the way
`contracts/` is exempt (payload shapes, not prompt text), in one reviewable line, and report it.
🪤 **A 🧱 row passes the law gate on the word `import-linter` alone** (row 12). Correcting the row is not
the proof; A2 is.
🪤 **Import-linter reads imports, not names.** A green wall does not mean the substrate names nothing
from trading. The deliberation prompts and the market-pack protocol stay (see Out of scope), and the
master's process still loads them through `kernel/__init__.py`. Never write *"the substrate knows
nothing of trading"* in a handback, a clause or a changelog.
🪤 **`sb_sas_plan.py` sits at its frozen 212 lines.** Its import lines may be swapped one for one, but the
loader cannot live there.
🪤 **`deploy-agents.ps1 up` runs `servicebus_prepare_routes.py`** under `uv run --extra azure`. Read the
roster as JSON by path; importing `orchestration.packs` pulls in `us_equities_sp500` (DL-218's failure
shape).
🪤 **`store.py` is at 194 lines and `test_master_agent.py` at 197.** Swap import lines, and keep each
docstring citation on one line.
🪤 **`MST-TYP-01` names `contracts/master.py`.** Amend it in the same commit as the move, or the clause
names a file that no longer exists.
🪤 **Historical docs name the old paths** (`docs/build-plan.md`, ADR-0016, sprint docs, the state
archive). They are records; do not rewrite them.
🪤 **The module header check** reads `Agent:`/`Role:`/`External I/O:`. The moved file's `Agent: master`
becomes `Agent: kernel`.
🪤 **This environment has no `.env`, no Azure and no graph.** Every proof is a fixture. Say which tree
you ran in.

---

## Guardrails (every sprint)

- No agent imports another agent, and the kernel imports nothing above it (`import-linter`). After this
  sprint, the same holds for the master.
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to dodge a rule.
  📌 Current sizes: `agents/master/store.py` **194**, `agents/master/agent.py` **182**,
  `agents/master/tests/test_master_agent.py` **197**, `scripts/sb_sas_plan.py` **212** (baselined),
  `contracts/master.py` **107**, `contracts/common.py` **90**, `kernel/serve_transport.py` **72**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers — `kernel.tunable(..., why=...)` with bounds. This sprint adds no tunable.
- Faults, not silent failure — `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe** — `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it.
- Secrets never through the worktree. **State which tree you ran in.**

---

## Sequencing after merge

1. `make ci` green locally, the branch pushed, and **`make gate-ran` exits 0**, run from the worktree
   whose `HEAD` is the commit being proven. Check the printed SHA against `git rev-parse HEAD`. 🪤 If the
   build environment cannot run `make gate-ran`, the handback says so and the planner runs it.
2. The planner merges to `main` locally and pushes. Then post-merge CodeQL.
3. **Deploy: an image-only retag**, with operator approval. All 15 images rebuild. Confirm that the
   master image was built without `contracts/`: the build's entrypoint smoke for that image is the first
   real proof that its closure is complete.
4. **Functionality check (live, by the planner, ⏳ 1 run).** On the retagged fleet, the master activates
   every agent type in the pack's grant policy with no `contracts/` in its image: the next
   `FleetPreflight` reads `passed=True`, every agent type writes an `AgentInstance`, and the scheduled run
   ends with `ACCEPTANCE PASS`. At the next full `up`, `Prepare-ServiceBusRoutes` reports *"served request
   topics + subscriptions"* OK, with the same topics. Record a row in `docs/laws/functionality-checks.md`.

---

## Handover — paste this to the builder

```text
Sprint 232 — the substrate imports nothing from the pack and names none of its agents (P20, E20.2).
Spec: docs/sprints/sprint-232-the-substrate-imports-nothing-from-the-pack.md (read all of it).

Branch: sprint-232-the-substrate-imports-nothing-from-the-pack. Never main.
You have NO .env, NO Azure access and NO live graph. Prove everything on fixtures; claim nothing live.
Design decision 1 is confirmed (planner review, 2026-09-26): the substrate vocabulary goes into the
kernel. Record the design decisions as DL-228 (DL-227 is S231's).

MUST RULE before any code: read agents/master/laws/laws.md + test-plan.md,
agents/deliberator/laws/laws.md + test-plan.md, docs/laws/conventions.md,
docs/laws/drift-register.md, ADR-0012 and DL-12. Fill the Law reading record BEFORE the first code
change. Law-cycle answer: YES (contracts/ changes; the master gains MST-DEP-05).

Build:
1. Tests A1-A3 first; paste the red run.
   A1: a subprocess imports agents.master.entrypoint; sys.modules must hold no contracts*, no other
       agents.*, no orchestration*, no surfaces*. Red today: contracts, contracts.common,
       contracts.master.
   A2: a temporary package tree (5 roots, 14 agents) with plants master->scanner, master->contracts,
       deliberator->execution; lint-imports --config <the repo's .importlinter> in a subprocess must
       exit 1 and name each plant; the clean tree exits 0. Red today: "4 kept, 0 broken".
   A3: an AST scan of the production modules in kernel/ and agents/master/ (docstrings excluded)
       finds no string literal equal to a pack agent type (the trading_grants.json keys plus the
       roster's role/image names). Red today: 9, all in kernel/serve_transport.py.
2. kernel/payload.py (new): the ONE frozen base, Provenance and Explanation, moved verbatim from
   contracts/common.py. contracts/common.py re-exports them explicitly (mypy strict), aliases the
   base as _Frozen, and keeps every trading name. No other import site changes.
3. git mv contracts/master.py kernel/handshake.py. Change only the base import, the header
   (Agent: kernel) and the CONTRACT's mission/never text (pack-neutral: no trading words in kernel).
4. Repoint agents/master/agent.py:32, http_server.py:14, store.py:13, the 7 master test modules
   and tests/test_contract_required_fields.py. Drop "COPY contracts/ contracts/" from
   agents/master/Dockerfile.
5. .importlinter: add agents.deliberator and agents.master to agents-are-islands; add the forbidden
   contract substrate-imports-no-pack (source: kernel, agents.master; forbidden: contracts, the 13
   other agents.* packages, orchestration, surfaces). Keep the existing kernel contract.
6. The served roster: orchestration/packs/trading_served_agents.json (served types, the deliberator's
   peer/manager/reply types, image directories). kernel/serve_transport.py keeps request_topic,
   reply_topic and consumer_from_env only. A small loader in scripts/ reads the JSON BY PATH (never
   import orchestration.packs) for sb_sas_plan.py, servicebus_prepare_routes.py and
   tests/test_served_agent_images.py. A6: the route and SAS plans equal those built from today's
   constants, copied into the test as literals.
7. The law cycle: master laws v1.5 -> v1.6 (amend MST-NEV-01, MST-SEC-03, MST-DEP-03, MST-TYP-01; add
   MST-DEP-05; Changelog line); test-plan v1.6 (re-cite MST-NEV-05/MST-DEP-03 on a contract that
   lists agents.master; mark 🟩 only where a test proves every conjunct); DLIB-NEV-05 row ⬜ -> 🧱;
   DRIFT-075 in the Master section; rollups in ledger.md and docs/laws/INDEX.md as make ci derives.
8. ADR-0012: add a dated Correction section (leak 1 closed S84-S86; leak 2 and the roster closed
   S232; the deferred residue listed). No reversal.

Order: design decisions in the DL (next free number; re-check at merge) -> red A1-A3 -> implement ->
A4-A9 -> break A1, A2, A3 and A6 on purpose, watch each fail, restore -> print both
PROMPT_RECIPE_HASH values (they must equal the spec's row 17) -> make ci > file (never piped),
exit 0.

DO NOT:
- create a second frozen base; contracts.common._Frozen IS the kernel base.
- add kernel.payload to PROMPT_MODULES (that moves every recipe digest); if the closure test catches
  it, exempt it like contracts/ and report.
- move kernel/deliberation_prompts.py or kernel/market_pack.py, or reword true trading clauses.
- grow scripts/sb_sas_plan.py (212, baselined) or push store.py (194) or test_master_agent.py (197)
  past 200 lines.
- rewrite historical docs that name the old paths.
- add a CI step, a status doc or a tunable.
- write "the substrate knows nothing of trading": import-linter reads imports, not names.
- pin a version number: PATCH, next available at merge, uv.lock staged with it.
- claim any live check. The planner retags and verifies after merge.

Handback: fill the Law reading record, the Test plan results, the Closeout evidence (red and green
output, guards, line counts, the make ci file and its exit code, make gate-ran from the worktree at
the full SHA or a plain statement that it could not run), and Return notes. Set Status: BUILT and
change this sprint's README.md row to lead with BUILT in the same commit. Anything not met: say
"not done" or "verified failing". Never write a Result for work not done.
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
| `contracts/master.py` → `kernel/handshake.py` | `agents/master/laws/laws.md` (whole, LOCKED v1.5) + `test-plan.md` (whole, v1.4) | `MST-TYP-01` (fields; `_Frozen`; `AgentState` `StrEnum`; names the path), `MST-IN-01`/`IN-02`, `MST-OUT-01`/`OUT-02` | No — confirmed the message shapes are exactly the three named plus `AgentState`, matching the spec's row 4 |
| `agents/master/agent.py`, `http_server.py`, `store.py`, 7 test modules | same | `MST-NEV-05`, `MST-DEP-03`, new `MST-DEP-05` | Yes — `MST-NEV-05`/`MST-DEP-03` are 🧱 on an islands contract that (pre-fix) never listed `agents.master` (test-plan.md row 51-52), so today's 🧱 is honest about the gate existing but not about it covering master. Widening the contract (scope item 4) is required before the row can be trusted, matching the spec's own finding (row 12) |
| `agents/master/laws/laws.md`, `test-plan.md` | same; `docs/laws/conventions.md` §4 (amendment), §7a (summary mirrors the law) | `MST-NEV-01`, `MST-SEC-03`, `MST-DEP-03`, `MST-TYP-01`, `MST-DEP-05` | Yes — `MST-SEC-03` today asserts `"cannot be changed by runtime config"` while the same book's own `PARAM` table (v1.5) marks `grant_policy_b64`/`grant_policy_path` `Tunable YES`; conventions §4 says a clause is amended only when functionality is genuinely lacking, and DRIFT-058's lesson (a clause whose check cannot fail) means the amendment must state only what the code guarantees, not the aspiration |
| `contracts/common.py` (re-export) | `TYP` clauses of every agent whose payloads carry `_Frozen`/`Provenance`/`Explanation`; `tests/test_contract_required_fields.py` | no field, class or base may change identity | No — confirmed via conventions' independence rule (§5) that re-exporting under the same name/identity is the only way to avoid touching 133 other files' import sites |
| `.importlinter` | master `test-plan.md` (`MST-NEV-05`/`MST-DEP-03`, both 🧱); `agents/deliberator/laws/laws.md` + `test-plan.md` (`DLIB-NEV-05`, ⬜ `_tbd_`) | these rows cite a contract that does not list their agent | Yes — read `DLIB-NEV-05`'s exact text (*"Never imports another agent or `orchestration`"*) in `agents/deliberator/laws/laws.md:64` and its `test-plan.md:26` row; confirmed it needs no wording change, only the contract widening plus a re-cited row |
| `kernel/serve_transport.py`, `scripts/sb_sas_plan.py`, `scripts/servicebus_prepare_routes.py`, `tests/test_served_agent_images.py`, new pack roster | no law book binds `kernel/`/`scripts/`; ADR-0012 §Decision 2; `CLAUDE.md` module-size baseline | `sb_sas_plan.py` baselined at 212, may not grow | No — confirmed `sb_sas_plan.py` is at exactly 212 lines today (measured), so the roster import must be a 1-for-1 swap, never a net addition |
| `agents/master/Dockerfile` | `CLAUDE.md` full cycle for anything touching production; DL-12 (S86: *"the same image runs any pack"*) | a production image | No — DL-12 already established the image is pack-agnostic; dropping `COPY contracts/` completes that, it does not reverse it |
| `docs/decisions/0012-platform-domain-separation.md` | this template's *"No ADR reversal"* rule; precedent in ADR-0025/ADR-0031's dated Correction sections | a dated Correction section only | No — read ADR-0012 whole; its *Known leaks* section already named leak 1 (closed S84–S86) and leak 2 (`contracts/` mixing), so the Correction records closure, not a reversal |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **Yes, on both counts.** `contracts/master.py` leaves `contracts/` (moves to `kernel/handshake.py`) and `contracts/common.py` changes (re-exports replace three locally-defined names). The master also gains a guarantee it has never made in its law book: `MST-DEP-05` — it imports no pack module at all, not even `contracts.master`, which it imports today. This triggers the full law cycle: master laws LOCKED v1.5 → v1.6 (amend `MST-NEV-01`, `MST-SEC-03`, `MST-DEP-03`, `MST-TYP-01`; add `MST-DEP-05`), `test-plan.md` to v1.6, one `DLIB-NEV-05` row from ⬜ to 🧱, `DRIFT-075` in the drift register, and rollups in `ledger.md`/`docs/laws/INDEX.md` derived by `make ci`.

**Contradictions found between a law and this spec:** None. The spec's law-cycle answer, the amendments it prescribes, and the measured text of `laws.md`/`test-plan.md` all agree — the amendments correct clauses that were already inaccurate (`MST-SEC-03`'s "cannot be changed" claim, the 🧱 rows citing a contract that never listed `agents.master`) rather than reversing anything the law asserted correctly.

**Laws found silent where a decision was needed:** The master `test-plan.md` (v1.4 header, though `laws.md` is v1.5 — a pre-existing version-header drift, not introduced here) was silent on whether `MST-NEV-05`/`MST-DEP-03`'s 🧱 rows require the cited contract to actually name the agent; conventions §3 defines 🧱 as needing the row to "name both the gate and the specific rule... it stands on," which implicitly requires the rule to cover the clause's subject, but no gate check enforces that (row 12: "the law gate accepts any 🧱 row that contains the word `import-linter`"). This sprint does not add such a gate check (out of scope, process freeze) — it only corrects the two rows so the silence does not currently hide a false claim.

**Clauses that were ⬜ and are now proven:** `MST-DEP-05` (new, proven 🟩 by A1). `DLIB-NEV-05` moves from ⬜ `_tbd_` to 🧱 (structural, once `agents.deliberator` is in the islands contract, proven non-vacuous by A2's planted `agents.deliberator → agents.execution` leak). `MST-NEV-05` and `MST-DEP-03` are re-cited (still 🧱) on a contract that now actually lists `agents.master` — not newly green, but no longer resting on a contract blind to their subject.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_master_import_closure_holds_no_pack_module` | `tests/test_substrate_import_closure.py` | 🟩 PASS | `MST-DEP-05` |
| A2 | `test_planted_leaks_are_caught_by_the_repos_own_config`; `test_clean_fixture_tree_passes_the_repos_own_config` | `tests/test_substrate_import_wall.py` | 🟩 PASS | `MST-NEV-05`, `MST-DEP-03`, `MST-DEP-05`, `DLIB-NEV-05` |
| A3 | `test_no_substrate_module_names_a_pack_agent` | `tests/test_substrate_no_pack_literals.py` | 🟩 PASS | `MST-DEP-05` |
| A4 | `test_the_frozen_base_and_evidence_types_are_the_same_objects`; existing `test_master_payload_fields_required_by_law` (repointed) | `tests/test_substrate_handshake_wire.py`; `tests/test_contract_required_fields.py` | 🟩 PASS | `MST-TYP-01` |
| A5 | `test_the_ehlo_dict_kernel_bootstrap_sends_still_parses`; `test_the_activate_message_wire_shape_is_unchanged`; `test_a_pack_payload_carrying_provenance_and_explanation_is_unchanged` | `tests/test_substrate_handshake_wire.py` | 🟩 PASS | `MST-TYP-01` |
| A6 | `test_the_roster_equals_todays_constants`; `test_the_request_and_reply_route_list_is_unchanged`; `test_every_served_type_maps_to_an_image_directory_with_a_dockerfile`; `test_the_sas_plan_built_from_the_roster_equals_the_plan_from_literals` | `tests/test_served_agent_roster_plan_stability.py` | 🟩 PASS | — (no law book binds `kernel/serve_transport.py`/`scripts/`; ADR-0012 §Decision 2) |
| A7 | `test_master_dockerfile_copies_no_contracts_directory`; `test_every_closure_module_lies_under_a_copied_path` | `tests/test_master_dockerfile_closure.py` | 🟩 PASS | — (production image; no law book) |
| A8 | Handback measurement (not a committed test, per spec): both `PROMPT_RECIPE_HASH` values printed and compared with row 17 — equal, unchanged. Existing `test_the_deliberator_declares_every_module_that_builds_its_prompt` (`tests/test_prompt_recipe.py`) passes unchanged, confirming `kernel.payload` never enters the deliberator's declared-module closure (`context_values.py` imports `Explanation` only under `TYPE_CHECKING`) | `tests/test_prompt_recipe.py` (existing, unmodified) | 🟩 PASS (measurement below) | — |
| A9 | Existing `test_activate_unknown_agent_type_raises`, `test_activate_uses_injected_grant_policy`, `test_substrate_default_knows_no_agent_types` pass unchanged (repointed import only) | `agents/master/tests/test_master_agent.py` (existing, unmodified bodies) | 🟩 PASS | `MST-NEV-01` (first test); the latter two remain uncited — they prove parts of the amended `MST-SEC-03`/`MST-DEP-03` but not each clause whole (see Law reading record) |

**Tests added beyond the plan:** none. Every new test file maps to a lettered plan item (A1–A7); A8 and A9 are measurements/regressions against existing tests, per the spec's own instruction that A8 is "a handback measurement, not a committed test."

---

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** `/home/user/trading-agents` (this cloud builder
session's checkout of `sprint-232-the-substrate-imports-nothing-from-the-pack`, merged with
`origin/main`). No `.env` file present (confirmed: `ls .env` → "No such file or directory"), no Azure
access, no live graph. Every proof below is on fixtures or the repo's own static/AST tooling.

**Result:** Built as specced. The substrate vocabulary (`_Frozen`, `Provenance`, `Explanation`,
`AgentState`, `EHLOMessage`, `ACTIVATEMessage`, `DRAINMessage`, the master `CONTRACT`) moved into
`kernel/payload.py` (new) and `kernel/handshake.py` (via `git mv contracts/master.py`).
`contracts/common.py` re-exports the three shared names explicitly. The master's 10 import lines onto
`contracts.master` and 1 onto `contracts.common` (via `_Frozen`) are repointed; `agents/master/Dockerfile`
drops `COPY contracts/`. `.importlinter` widens `agents-are-islands` to 14 modules (adds
`agents.master`, `agents.deliberator`) and adds `substrate-imports-no-pack`. The served-agent roster
moves to `orchestration/packs/trading_served_agents.json`, read by path from the new
`scripts/served_agent_roster.py` loader; `kernel/serve_transport.py` keeps only `request_topic`,
`reply_topic`, `consumer_from_env`. Master laws bump to LOCKED v1.6 (`MST-NEV-01`, `MST-SEC-03`,
`MST-DEP-03`, `MST-TYP-01` amended; `MST-DEP-05` added); `test-plan.md` to v1.6; `DLIB-NEV-05` moves
⬜ → 🧱; `DRIFT-075` recorded; ADR-0012 carries a dated Correction. One deviation from the letter of the
handover, forced by this environment, is recorded under "Not met" below: `uv.lock`'s `trading-agents`
version line was hand-edited rather than produced by a successful `uv lock` run, because `uv lock`
cannot complete in this sandbox (see below).

**Files changed:** `kernel/payload.py` (new, 44), `kernel/handshake.py` (moved from
`contracts/master.py`, 107), `contracts/common.py` (67, was 90), `kernel/serve_transport.py` (51, was
72), `agents/master/agent.py` (182), `agents/master/http_server.py` (90), `agents/master/store.py`
(194), `agents/master/Dockerfile` (17), `.importlinter` (84, was 58), `agents/master/tests/` (7 files:
`credential_probe_testkit.py`, `test_credential_test.py`, `test_master_agent.py` (197),
`test_master_entrypoint.py`, `test_remediation_activation.py`, `test_remediation_auto_activation.py`,
`test_secret_map.py`), `tests/test_contract_required_fields.py` (114), `tests/test_served_agent_images.py`
(94), `scripts/sb_sas_plan.py` (211, was 212), `scripts/servicebus_prepare_routes.py` (118),
`scripts/served_agent_roster.py` (new, 62), `orchestration/packs/trading_served_agents.json` (new).
New tests: `tests/test_substrate_import_closure.py` (45), `tests/test_substrate_import_wall.py` (86),
`tests/test_substrate_no_pack_literals.py` (81), `tests/test_substrate_handshake_wire.py` (75),
`tests/test_served_agent_roster_plan_stability.py` (103), `tests/test_master_dockerfile_closure.py`
(61). Law/docs: `agents/master/laws/laws.md` (235), `agents/master/laws/test-plan.md` (55),
`agents/deliberator/laws/test-plan.md` (one row), `docs/laws/drift-register.md` (`DRIFT-075`),
`docs/laws/ledger.md`, `docs/laws/INDEX.md` (rollups, `make ci`-derived), `docs/decisions/0012-platform-domain-separation.md`
(Correction section), `docs/design-log.md` (`DL-228`), `docs/sprints/sprint-176-a-partial-fill-must-be-able-to-finish.md`
(one dead-link fix, target only, wording untouched), `pyproject.toml` (version, `flake8-type-checking`
config), `uv.lock` (version line, hand-edited — see "Not met").

**Design decisions:** recorded as DL-228 in [`design-log.md`](../design-log.md) — the kernel as the
substrate vocabulary's home (confirmed by the planner), `kernel/payload.py`/`kernel/handshake.py` as
module names, the explicit re-export shape, the `.importlinter` contract text, the roster JSON shape
and its path-based loader (with the two-pack combination question answered but not built), the amended
master wording, and the pack-neutral `CONTRACT` text — each with its rejected alternatives.

**Proof — the red run first** (A1 and A3; A2 produced the same "4 kept, 0 broken" red the spec
predicted and is shown in the Guards section below to avoid duplication):

```text
$ uv run pytest tests/test_substrate_import_closure.py tests/test_substrate_no_pack_literals.py -vv --no-cov
FAILED tests/test_substrate_import_closure.py::test_master_import_closure_holds_no_pack_module - AssertionError: assert ['contracts', 'contracts.common', 'contracts.master'] == []

  Left contains 3 more items, first extra item: 'contracts'

  Full diff:
  - []
  + [
  +     'contracts',
  +     'contracts.common',
  +     'contracts.master',
  + ]
FAILED tests/test_substrate_no_pack_literals.py::test_no_substrate_module_names_a_pack_agent - assert ["kernel/serve_transport.py:22: 'deliberator-manager'", "kernel/serve_transport.py:24: 'deliberator-proponent'", "kernel/serve_transport.py:25: 'deliberator-opponent'", "kernel/serve_transport.py:29: 'curator'", "kernel/serve_transport.py:31: 'forecaster'", "kernel/serve_transport.py:32: 'operator'", "kernel/serve_transport.py:33: 'researcher'", "kernel/serve_transport.py:34: 'supervisor'", "kernel/serve_transport.py:51: 'deliberator'"] == []

  Left contains 9 more items, first extra item: "kernel/serve_transport.py:22: 'deliberator-manager'"
  ...
2 failed in <1s
```

This matches the spec's predicted red exactly: row 10 (`contracts`, `contracts.common`, `contracts.master`
in the closure) and row 14 (9 literals, all in `kernel/serve_transport.py`, same line numbers: 22, 24,
25, 29, 31, 32, 33, 34, 51).

**Proof — the green run:**

```text
$ uv run pytest tests/test_substrate_import_closure.py tests/test_substrate_import_wall.py \
    tests/test_substrate_no_pack_literals.py tests/test_substrate_handshake_wire.py \
    tests/test_served_agent_roster_plan_stability.py tests/test_master_dockerfile_closure.py \
    tests/test_served_agent_images.py tests/test_prompt_recipe.py tests/test_contract_required_fields.py \
    -v --no-cov
============================= test session starts ==============================
collecting ... collected 33 items
[... 33 passed ...]
============================== 33 passed in 2.41s ==============================

$ uv run lint-imports
Analyzed 588 files, 1972 dependencies.
Agents may not import one another (talk only via messages) KEPT
Substrate imports no pack module KEPT
Agents may not reach into surfaces or orchestration KEPT
Kernel is pure plumbing — no domain, no contracts, no agents KEPT
Contracts declare schemas only — never import agents or runtime layers KEPT
Contracts: 5 kept, 0 broken.
```

**Guards planted (DL-70) — each broken, watched red, then restored, per guard:**

- **A1** — planted `import contracts` (plus an `assert contracts` to survive unused-import removal)
  into `agents/master/agent.py`. `test_master_import_closure_holds_no_pack_module` went red:
  `assert ['contracts'] == []`. Reverted to the committed file; test green again.
- **A2** — removed `agents.deliberator`/`agents.master` from `agents-are-islands` and dropped the
  `substrate-imports-no-pack` contract from `.importlinter` (restoring it to the pre-sprint text).
  `test_planted_leaks_are_caught_by_the_repos_own_config` went red: `lint-imports` returned exit 0,
  "4 kept, 0 broken" — the exact base-red the spec measured (row 11). Restored `.importlinter`; both
  tests green again, `lint-imports` back to "5 kept, 0 broken".
- **A3** — planted `_DL_70_GUARD_PLANT = "curator"` into `kernel/serve_transport.py`.
  `test_no_substrate_module_names_a_pack_agent` went red: `["kernel/serve_transport.py:22: 'curator'"]
  == []`. Reverted; test green again.
- **A6** — changed `orchestration/packs/trading_served_agents.json`'s `forecaster` image directory to
  `"wrong-dl-70-guard-plant"`. `test_every_served_type_maps_to_an_image_directory_with_a_dockerfile`
  went red: `assert 'wrong-dl-70-guard-plant' == 'forecaster'`. Reverted the JSON; all four tests in
  `tests/test_served_agent_roster_plan_stability.py` green again.

**Prompt-recipe hashes after the change:** deliberator
`31fe77975825cb3dadcc7989ed8c7d37ee571dc719dc612a795c671c189b1480`; operator
`3fcfed8fe7d67a881da04268d7119c5aab55402a8458927c4bb600262c94c259`. **Both equal row 17 exactly — no
movement.** `tests/test_prompt_recipe.py::test_the_deliberator_declares_every_module_that_builds_its_prompt`
passes unchanged: `kernel.payload` never enters the declared closure, because
`agents/deliberator/context_values.py` imports `Explanation` only under `TYPE_CHECKING`
(verified by reading the file, per the spec's trap).

**Module line counts** (touched or baselined; all under 200 except the frozen baseline):
`kernel/payload.py` 44, `kernel/handshake.py` 107, `contracts/common.py` 67 (was 90),
`kernel/serve_transport.py` 51 (was 72), `agents/master/agent.py` 182, `agents/master/http_server.py`
90, `agents/master/store.py` 194, `agents/master/tests/test_master_agent.py` 197, `scripts/sb_sas_plan.py`
**211** (baselined at 212, did not grow), `scripts/servicebus_prepare_routes.py` 118,
`scripts/served_agent_roster.py` 62, `tests/test_served_agent_images.py` 94,
`tests/test_contract_required_fields.py` 114, `.importlinter` 84, `agents/master/Dockerfile` 17.
`scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts` exits 0.

**`make ci`:** `make ci > /tmp/ci.txt 2>&1; echo $?` → **exit 0**. `3254 passed, 6 skipped` (the 6
skips are pre-existing, `.env`/live-network gated, unrelated to this sprint). `Required test coverage
of 100.0% reached. Total coverage: 100.00%`. Dependency audit: `No unaccepted vulnerabilities; 1
accepted advisory re-checked` (the pre-existing `diskcache` acceptance, unrelated). `detect-secrets`:
`Passed` on tracked files, and `detect-secrets (untracked): scanning 9 new file(s)` → `Passed`.
`lint-imports`: `5 kept, 0 broken`. Every one of the 15 steps ran and none failed.

**`make gate-ran`:** Attempted; could not run. `scripts/assert_gate_ran.py` calls the `gh` CLI directly
(`subprocess.run(["gh", "api", endpoint], ...)`), which is not installed in this build environment:

```text
$ make gate-ran
...
FileNotFoundError: [Errno 2] No such file or directory: 'gh'
make: *** [Makefile:71: gate-ran] Error 1
```

Per the spec's own fallback, the handback says so; the planner runs `make gate-ran` after the branch
below is pushed and the remote gate has had time to complete.

**Not met / verified failing:**

- **`uv lock` could not run in this sandbox.** `uv lock` resolves the full dependency graph for every
  declared extra, including `forecaster`'s `torch` pin from the custom `pytorch-cpu` index
  (`https://download.pytorch.org/whl/cpu`). That host is blocked by this session's egress policy —
  `curl $HTTPS_PROXY/__agentproxy/status` shows repeated `connect_rejected` / "gateway answered 403 to
  CONNECT (policy denial)" entries for `download.pytorch.org:443`, and the proxy's own guidance is
  explicit: *"Do not retry or route around it — report the blocked host."* `uv lock --offline` also
  fails (`torch was not found in the cache`, since the `forecaster` extra was never installed in this
  session). Consequence discovered while diagnosing: with `pyproject.toml`'s version bumped and
  `uv.lock` left at the old version, **every** `uv run` invocation started failing outright (uv
  detected the lockfile was stale and tried to re-lock, hitting the same blocked host) — this would
  have made `make ci` itself unrunnable here. I hand-edited the single self-referential version field
  in `uv.lock` (`trading-agents`'s own `version`, `"0.113.0"` → `"0.113.1"`, matching `uv`'s own PEP 440
  normalization of `pyproject.toml`'s `"0.113.01"` — confirmed by
  `tests/test_check_version_scheme.py::test_real_pyproject_passes_despite_normalized_lockfile`, which
  asserts the two strings legitimately differ). No dependency, version pin, or hash anywhere else in
  `uv.lock` was touched, and none needed to be — this sprint adds no dependency. `uv sync --frozen`
  (what remote CI actually runs) succeeds cleanly against the hand-edited lockfile. **This is not the
  `uv lock` run the spec asked for; it is the narrowest fix that keeps the tool usable under a policy
  block I am directed not to route around.** Flagging plainly per LAW-02 rather than claiming a
  `uv lock` success that did not happen. The planner (or the operator, with network access) should run
  a real `uv lock` at the first opportunity to confirm this by-hand edit is the only drift.

---

## Return notes

- **Every Measured row re-checked and held.** Rows 1, 4, 5, 6, 7, 8, 10, 11, 13, 14, 17 were
  re-derived independently during this build (import counts, the closure, the literal scan, the
  fixture's "4 kept, 0 broken", the prompt-recipe hashes) and matched the spec exactly — no number
  differed, so the STOP rule never triggered.
- **The one genuine surprise was environmental, not a spec number.** Bumping `pyproject.toml`'s
  version without a matching `uv.lock` update made every `uv run` invocation fail outright (uv tries
  to re-lock on a detected mismatch), and a real `uv lock` cannot complete here because
  `download.pytorch.org` (the `forecaster` extra's pinned index) is blocked by this session's egress
  policy. Fixed the narrowest way possible — the one self-referential version field in `uv.lock`,
  matching `uv`'s own PEP 440 normalization — and flagged it plainly in Closeout rather than silently
  running `uv lock` from memory or masking the gap. Recommend the planner (or the operator, off
  network) runs a real `uv lock` at the next opportunity to confirm nothing else drifted.
- **DL-228 vs DL-227:** confirmed at merge-time (post-merge with `origin/main`) that DL-227 belongs to
  S231 and DL-228 was still free; DRIFT-074 was the newest drift entry, so DRIFT-075 was correctly
  free too.
- **`agents-are-islands` and `substrate-imports-no-pack` overlap on `agents.master`'s forbidden set**
  by design (recommended in the spec: keep both, "it costs nothing"). Confirmed on the live tree:
  widening both together produces `5 kept, 0 broken`, no new violation from the overlap.
- **One historical dead link, not a content rewrite.** `docs/sprints/sprint-176-…md` held a literal
  markdown link (`[...](../../contracts/master.py)`) that `check_markdown_links.py` correctly flagged
  once the file moved. Repointed only the href to `../../kernel/handshake.py`; the visible link text
  and all surrounding prose (a historical record of DRIFT-033) are untouched — this is a mechanical
  link fix, not the "rewriting historical docs" the spec's trap warns against, and the trap's own
  wording ("They are records; do not rewrite them") is about content, not a dangling href a live gate
  step checks on every run.
- **Sequencing after merge (spec's own next steps, not done here):** `make gate-ran` from the branch
  worktree once pushed; the planner's merge to `main`; an image-only retag with operator approval; and
  the live functionality check (master activates every agent type with no `contracts/` in its image,
  `FleetPreflight passed=True`, `ACCEPTANCE PASS`, `Prepare-ServiceBusRoutes` unchanged at the next
  `up`). None of this is claimable from a sandbox with no `.env`, no Azure and no live graph.

---

## Planner review and merge — 2026-09-26

**Reviewed.** Scope matches the spec's map: 46 files, no security-baseline edit. `CLAUDE.md` gains an
accurate note (S234's cloud session hit the same `gh` and `uv lock` limits). `pyproject.toml`'s lint
change adds the moved base class to ruff's runtime-evaluated list, so it tightens, not loosens. The master
runs `agents.master.entrypoint` from `kernel/` and `agents/master/` only; its indented imports are all
`TYPE_CHECKING` blocks naming the substrate, and its only dynamic imports are vendor SDKs. The dispatcher
image copies `kernel/` and `contracts/` whole, so S234's file-by-file list is unaffected.

**Merged.** `main` (S233, S234) merged in as `d470cd78`: the version re-bumped to **`0.114.01`**
(`uv lock --check` exit 0, so the hand-edited lock is what `uv lock` writes, and the owed re-lock is
settled); law rollups master v1.6 from here, dispatcher v1.1 from S234; DL-229 above DL-228; DRIFT-075 to
077 unique. 🐛 **`make ci` then failed one test on Windows:** `test_every_closure_module_lies_under_a_copied_path`
compared `str(Path(...))`, which is `agents\master` on Windows, with the Dockerfile's `agents/master/`.
It passed on Linux (the cloud session, remote CI). Fixed in `f685260e` with `as_posix()`; with the
master's own `COPY` removed it still fails, naming `agents.master`. `make ci` exit 0 (**3,309 passed,
6 skipped, 100.00 %**, 5 contracts kept). **`GATE PROVEN` for `f685260e…`** (CI, CodeQL, Security
Findings, attempt 1); `main` fast-forwarded to it and tagged `v0.114.01`.

**Re-measured, not taken from the handback:** the master's closure in a fresh interpreter loads 67
first-party modules and **0** from the pack; both prompt-recipe hashes equal row 17; `lint-imports` reads 5
kept, and a real `import contracts.common` planted in `agents/master/store.py` breaks *Substrate imports no
pack module*, naming the line.

**Owed:** the deploy (operator approval; image-only retag, all 15 images rebuild and the master's loses
`contracts/`), then the functionality check in *Sequencing after merge* step 4.
