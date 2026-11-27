<!-- Agent: planning | Role: sprint handover -->
# Sprint 293 — a test run reaches only the test paper account and a graph of its own

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-293-a-test-run-reaches-only-the-test-account-and-its-own-graph`
**Status:** SPEC
**Version:** *next available MINOR at merge* (the prototype measured `0.132.00`)
**Effort:** M
**Decisions:** [DL-328](../design-log.md) (this sprint's seven decisions, made and measured) · [DL-307](../design-log.md) (the test lane's options; this is option A) · [work-queue 136](../work-queue.md)

> **Why this bump kind.** A new capability: a run of the pipeline beside the fleet, on the second
> paper account and a graph of its own, that refuses any start which could reach the fleet's
> account, graph or bus. No agent's behaviour changes. A MINOR.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build.** A clause you believe is wrong is a `drift-register.md` row plus a report — never a quiet edit |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: execution **`EXEC-IDN-01`** (the sole broker interface) and **`EXEC-OUT-03`**
(only the `paper` and `broker_shadow` stages submit), and the execution `PARAM` row
`alpaca_base_url`; deliberator **`DLIB-OUT-01`** and **`DLIB-OUT-02`** (what a debate records).

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read the agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It decides whether this sprint owes a clause.
5. **Write the Law reading record** (template at the bottom) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, that silence is a finding: record it and add a
   `drift-register.md` row.
8. Every test cites what it proves in its docstring: a clause ID where a clause governs it, else the
   decision of DL-328 it proves (`DL-328 D2`).

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**No.** No file in `contracts/`, `kernel/` or `agents/` changes. The lane is orchestration tooling:
it calls each agent's own work functions, unchanged, and no agent gains or loses a guarantee. Its own
guarantees (what it refuses, what its process may hold) are DL-328's decisions; no law book covers
orchestration tooling (the one orchestration book is the dispatcher's, and the dispatcher is not
touched). The tests cite `DL-328 D<n>`.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `orchestration/lane_stages.py` (execution stage), `orchestration/lane_env.py` (the broker's keys and base URL) | `agents/execution/laws/laws.md` + `test-plan.md` | `EXEC-IDN-01`: the lane reaches the broker only through execution's own `process_work_item`; `EXEC-OUT-03` and the `alpaca_base_url` PARAM row: the lane sets the paper base and leaves the stage alone |
| `orchestration/lane_debate.py` | `agents/deliberator/laws/laws.md` + `test-plan.md` | `DLIB-OUT-01`, `DLIB-OUT-02`: the debate is the manager's own `review_pm_node`; the lane changes only how the manager reaches its peers (in process) and which model answers (a fake) |
| `orchestration/lane_run.py` | `orchestration/laws/dispatcher/laws.md` (read, not touched) | The lane places a `RunRequest` with the dispatcher's own `place_run_request`, under a `lane-` id on its own graph; no dispatcher clause changes |
| every file | `docs/laws/conventions.md`, `docs/laws/drift-register.md` | docstring citations; where a silent law is reported |

⚠️ **The one invariant: nothing a lane run builds may reach the fleet's broker account, graph or
bus.** If any step of yours would build a broker, graph or bus client before `isolate_lane` has
returned, or from anything but the process environment it leaves, stop and report.

---

## Goal

`uv run python scripts/run_lane.py` in the main checkout runs one pipeline run through the nine
run-path agents' own work functions, in one process, against the second Alpaca paper account and a
Neon branch of its own, with fake models in the debate. Before it builds anything it refuses: a
missing lane value, a test key equal to a fleet key, a non-paper endpoint, a lane graph on the
fleet's database endpoint, and a start inside the fleet's nightly window; and it rewrites its own
environment so that no fleet secret's value remains. It refuses a graph that holds any run but a
lane run. It ends with the fleet's acceptance verdict.

## Why (context)

A test run today is a run of the live fleet: the planner widens the KEDA window and fires a run
(the work queue's standing notes). Two were declined in October (2026-10-16 and -17) because the
run's first step cancels the orders an earlier run left pending (JNJ, then CAT and MDLZ). DL-307
measured why a test database alone is not enough (the broker account and the bus are shared too)
and named three options; option A, one process on the planner's machine, is the cheapest. Its one
blocker, a second paper account, was lifted on 2026-11-26.

### Measured, 2026-11-27 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| The test account | HTTP 200, `ACTIVE`, equity $100,000, 0 positions, 0 open orders | *[measured 2026-11-27, read-only GETs]* kit `probe_readonly.py` |
| Its keys read the fleet's market data | SIP daily bars: 15 AAPL bars, 2026-11-02 to 11-20 (IEX the same) | *[measured 2026-11-27]* the same script |
| The fleet's Alpaca key in `.env` | one value under three names (the unprefixed, the `PAPER` and the `PROVIDER_` one); the test key differs and reaches a different account id | *[measured 2026-11-27]* the same script (it prints whether the ids are equal, never an id) |
| `ALPACA_TEST_ENDPOINT` | `https://paper-api.alpaca.markets/v2`; `AlpacaBroker` joins its base and `/v2/orders` (`agents/execution/alpaca.py:34`, `:183`), so it cannot be the base | *[measured 2026-11-27]* |
| Where a fleet endpoint enters a run | `POSTGRES_DSN` (`kernel/graph_env.py:74`); `AZURE_SERVICEBUS_CONNECTION_STRING` or `SERVICEBUS_CONNECTION_STRING` (`kernel/bus_azure_config.py:40-47`), and `agents/deliberator/entrypoint.py::build_manager` returns a Service Bus peer client when one is set; execution's key from `EXECUTION_ALPACA_API_KEY`, `ALPACA_PAPER_API_KEY` or `ALPACA_API_KEY` (`agents/execution/settings.py:96-110`); the provider's from `PROVIDER_ALPACA_API_KEY` | *[measured 2026-11-27]* `grep` of every `os.environ` read and every `AliasChoices` outside the entrypoints |
| `.env` holds them | `POSTGRES_DSN`, `SERVICEBUS_CONNECTION_STRING`, the fleet key | *[measured 2026-11-27]* the names only |
| The local runner is not the lane | `cascade_once` runs `execution_poll.find_pending` / `execute_pm_node`, the old `orchestration.veto` debate and the forecaster's four local legs; the entrypoints run `find_pending_work` / `process_work_item`, the deliberator agent and the barrier leg only | *[read 2026-11-27]* `orchestration/local_pipeline.py`, each `agents/*/entrypoint.py` |
| `scripts/run_local.py --real` | builds its graph from `POSTGRES_DSN` after `load_dotenv()`: in the main checkout it writes a `local-1` RunRequest to the live graph | *[read from the code 2026-11-27, not run]* `scripts/run_local.py:138-144` |
| Neon | one project, one branch (`production`, 210 MB), one read-write endpoint; the live DSN is the direct host, not `-pooler` | *[measured 2026-11-27]* Neon API, read-only |
| A schema-only branch | offered on the Launch plan, beta, 5 root branches a project, 3 GB each | *[Neon's documentation, read 2026-11-27]* |
| The fleet's universe | `sp500` holds 99 tickers | *[measured 2026-11-27]* `FileUniverse().members("sp500")` |
| The prototype, in memory | 4 rounds; ACCEPTANCE PASS; 2 debates (AAPL, MSFT) both `uphold`, 0 failed open; 1 ExecutionRun, 1 Snapshot; 2 faults, the forecaster's designed refusal (11 bars against 700) | *[measured 2026-11-27]* `proto-s293`, `orchestration/tests/test_lane_stages.py` |

---

## Scope — and what is deliberately NOT here

1. **`orchestration/lane_guard.py`**: the refusals of DL-328 D2 (`lane_values`, `fleet_values`,
   `refuse_unsafe_start`, `neon_endpoint_id`, `LaneRefusedError`).
2. **`orchestration/lane_env.py`**: the environment of DL-328 D3 (`isolate_lane`,
   `lane_environment`, `refuse_leaks`, `pack_tunables`, `load_tunables_pack`).
3. **`orchestration/lane_debate.py`** and **`orchestration/lane_stages.py`**: the nine stages of
   DL-328 D1 and the fake debate of D6.
4. **`orchestration/lane_run.py`**: the run of D4 and D5 (`lane_run_id`, `last_closed_session`,
   `refuse_foreign_runs`, `run_rounds`, `run_lane`).
5. **`scripts/run_lane.py`**: the command.
6. **The version** `0.132.00` in `pyproject.toml` and the one `version` line of `uv.lock`, by hand.
7. **Five test files** (Test plan).

All of it is given in Appendix B, measured. You write the tests.

### Out of scope (do NOT build this sprint)

- **No change to any agent, `kernel/` or `contracts/` file**, to `orchestration/local_pipeline.py` or
  to `scripts/run_local.py`. The `--real` hazard of `run_local.py` is a work-queue row of its own.
- **No Neon branch, no `.env` edit, no Key Vault entry.** The planner creates the branch and adds
  `LANE_POSTGRES_DSN` to the main checkout's `.env` at F1 (Sequencing after merge).
- **No real model.** Every role answers with a fake (DL-328 D6).
- **No deploy.** Nothing runs in Azure.
- **No `laws.md` edit**, no ADR, no design-log entry (DL-328 is written).

### The road not taken (LAW-06)

- **Extend `cascade_once`.** Rejected: it runs a subset of each agent's work (above) and 27 test files
  call it.
- **A builder in every entrypoint, called by `main()` and the lane.** Rejected: nine agents changed
  for no behaviour; `test_each_stage_drives_the_function_its_entrypoint_hands_work_loop` ties the
  lane to each entrypoint instead.
- **Build each client explicitly and leave the environment as it is.** Rejected: `build_manager` and
  every settings class read the environment; one missed read reaches the fleet.
- **Load `.env`, then delete the fleet's names.** Rejected: a name added to `.env` later would pass
  through. The lane carries an allow-list.
- **Compare the two accounts' ids in code.** Rejected: `BrokerAccount` carries no id and the ids may
  not enter a public repository. F1 compares them once, read-only.
- **A flag to start inside the window.** Rejected: a flag is how the window gets crossed by habit.
- **A copy-on-write branch of the live graph.** Rejected: it holds 40 positions and their stops that
  the empty test account does not; reconciliation and the stop pass would act on them.
- **A second database on the live endpoint.** Rejected: it shares the fleet's compute and differs
  from the live DSN by its path alone.
- **A real model as an option now.** Rejected: a paid call is the operator's word each time.

---

## The design decisions — made, and recorded in DL-328

1. **D1** One process drives each run-path agent's own `find` / `process` pair, with its settings and
   fault sink; the deliberator's three roles on one in-process bus.
2. **D2** Five refusals before any endpoint is built.
3. **D3** The env file is read, never loaded; the environment is rewritten and then proved to hold no
   fleet secret's value.
4. **D4** The lane's graph is a Neon schema-only branch; a graph holding any run but a `lane-` run is
   refused; run id `lane-YYYYMMDD-HHMMSS`; the session is the last one settled by 17:00 New York.
5. **D5** Rounds until one advances nothing, at most 12 by default; the fleet's acceptance verdict;
   exit 0, 1 or 2.
6. **D6** Fake models in all three roles; the judge rules `uphold`.
7. **D7** Not deployed; MINOR.

---

## Blast radius — measured 2026-11-27

| What | Detail |
| --- | --- |
| Files changed | new: `orchestration/lane_guard.py` (146), `lane_env.py` (141), `lane_debate.py` (76), `lane_stages.py` (149), `lane_run.py` (127), `scripts/run_lane.py` (120); the five test files; `pyproject.toml` and `uv.lock`, one line each |
| Agents affected | none changed; the lane imports nine agents' work functions from `orchestration`, which `import-linter` allows |
| Contract change? | no |
| Graph vocabulary change? | no: the lane writes only what the agents write (the in-memory run is guarded by the pack's vocabulary) |
| New env keys / tunables | none in any app; the lane reads `ALPACA_TEST_API_KEY`, `ALPACA_TEST_API_SECRET`, `ALPACA_TEST_ENDPOINT` and `LANE_POSTGRES_DSN` from the main checkout's `.env` |
| Deploy implication | none: nothing runs in Azure; the merge's image build carries files no image runs |
| Rollback | revert the merge. What a revert does not undo: a lane run's orders on the test paper account and its rows on the lane's branch; neither touches the fleet |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Write the five test files** of the Test plan, under exactly the names it gives, and run them on
   the unchanged tree:
   `uv run --no-sync pytest orchestration/tests/test_lane_guard.py orchestration/tests/test_lane_env.py orchestration/tests/test_lane_run.py orchestration/tests/test_lane_stages.py tests/test_run_lane_cli.py --no-cov -q -p no:cacheprovider`.
   Every file errors on collection: the modules it imports do not exist yet. Paste the summary line
   (on the planner's dry run: `5 errors`).
3. **Apply Appendix B**, exactly, and check the eight blob ids it gives.
4. **Run the same command again: 75 passed.** Then the neighbours:
   `uv run --no-sync pytest orchestration/tests tests/test_accept_cli.py --no-cov -q -p no:cacheprovider`: no failure.
5. **Prove the guards can fail (DL-70):** the 25 breaks of Appendix C, one at a time, each red
   on the test named for it, each restored before the next.
6. **`make ci` green**, every step of the `ci:` target (count them from the `Makefile`),
   **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

Under **exactly these names** (the planner's break script judges by them). Each docstring cites the
decision it proves, `DL-328 D<n>`. The literal name lists of A2 and A8 are written out in a helper,
`orchestration/tests/lane_fixtures.py` (module docstring with `Agent:`, `Role:`, `External I/O:`), and
never taken from the production constants: a name dropped from a constant must fail a test, not
remove a case.

`lane_fixtures.py` holds: `MEASURED_FLEET_NAMES`, the fourteen names of
`orchestration/lane_guard.py::FLEET_SECRET_NAMES` in Appendix B, written out; `MEASURED_ENDPOINT_NAMES`,
the seven further names of `lane_env.py::DROPPED_NAMES`; `MEASURED_FEED_NAMES`, the five of
`lane_env.py::FEED_NAMES`; and `LANE`, the four lane values keyed by their env-file names: key `PKLANE`, secret
`lane-secret`, endpoint `https://paper-api.alpaca.markets/v2`, DSN
`postgresql://u:p@ep-lane-1.ap-southeast-2.aws.neon.tech/db` (mark the two lines that quote the key
and the secret with the next-line pragma, Traps).

**`orchestration/tests/test_lane_guard.py`** (`SAFE_NOW` = 2026-11-27 03:00 UTC; a fleet DSN on
endpoint `ep-fleet-1234`, the lane's on `ep-lane-5678`)

| # | Test | Must prove |
| --- | --- | --- |
| A1 | `test_each_missing_lane_value_is_named` | `lane_values` on `{ALPACA_TEST_API_KEY: "k", ALPACA_TEST_API_SECRET: "  "}` raises `LaneRefusedError` whose message is exactly `missing lane values: ALPACA_TEST_API_SECRET, ALPACA_TEST_ENDPOINT, LANE_POSTGRES_DSN`; four present values come back stripped as a `LaneValues` |
| A2 | 🎯 `test_every_fleet_name_is_read_from_the_env_file_then_the_environment`, parametrized over `MEASURED_FLEET_NAMES` | `fleet_values({}, {name: "f"})` is `{name: "f"}`; `fleet_values({name: "s"}, {})` is `{name: "s"}`; with both, the env file's value wins; `fleet_values({"HF_TOKEN": "x"}, {"PATH": "y"})` is `{}` |
| A3 | 🎯 `test_a_test_value_equal_to_a_fleet_value_is_refused`, parametrized over `MEASURED_FLEET_NAMES` × `key`, `secret` | the fleet mapping built by `fleet_values({}, {name: <the lane's key or secret>})`; `refuse_unsafe_start` raises, the message naming `fleet's <name>` |
| A4 | `test_an_endpoint_other_than_the_paper_host_is_refused`, parametrized | `https://api.alpaca.markets`, `https://paper-api.alpaca.markets.example.com/v2` and `paper-api.alpaca.markets` each raise, matching `paper host` |
| A5 | 🎯 `test_the_fleets_database_endpoint_is_refused_direct_or_pooled`, parametrized | against the fleet DSN: the same DSN, a `-pooler` host of the same endpoint with another user and database, and the same endpoint in upper case each raise, matching `live graph` |
| A6 | `test_a_lane_graph_on_its_own_endpoint_starts` | the lane's DSN starts with and without a fleet DSN; `neon_endpoint_id(<fleet DSN>)` is `ep-fleet-1234`; a DSN `not a dsn` raises, matching `names no host` |
| A7 | 🎯 `test_the_fleets_nightly_window_is_refused`, parametrized | 21:59:59 UTC starts; 22:00:00 and 23:59:59 UTC raise, matching `nightly window`; 00:00:00 starts; 2026-11-28 09:30 at UTC+11 (22:30 UTC) raises |

**`orchestration/tests/test_lane_env.py`** (a fixture that restores the whole of `os.environ` after
the test; a planted shell holding `shell-<name>` for every `MEASURED_FLEET_NAMES` and
`MEASURED_ENDPOINT_NAMES` name plus `PATH`; a planted env file holding `file-<name>` for every
`MEASURED_FLEET_NAMES` name, `feed-<name>` for every `MEASURED_FEED_NAMES` name, `TIINGO_API_KEY`,
`HF_TOKEN`, a name whose value is `None`, and `LANE`)

| # | Test | Must prove |
| --- | --- | --- |
| A8 | 🎯 `test_the_lane_environment_holds_no_fleet_value` | after `isolate_lane(shell, env file, now=2026-11-27 03:00 UTC, pack=load_tunables_pack())`: no planted value but the feed values and the lane's own is left in the shell; each feed name holds `feed-<name>`; `POSTGRES_DSN` is the lane's DSN; `EXECUTION_ALPACA_API_KEY` and `PROVIDER_ALPACA_API_KEY` the lane's key; `EXECUTION_ALPACA_SECRET_KEY` and `PROVIDER_ALPACA_API_SECRET` its secret; `EXECUTION_ALPACA_BASE_URL` `https://paper-api.alpaca.markets`; `GRAPH_VOCABULARY_PATH` and `PORTFOLIO_MANAGER_ISSUER_MAP_PATH` the two pack files, which exist; `PATH` unchanged; `TIINGO_API_KEY`, `HF_TOKEN`, the four lane names gone |
| A9 | 🎯 `test_settings_built_after_isolation_reach_only_the_lane` | the planted shell in `os.environ`, then `isolate_lane(os.environ, ...)`: `ExecutionSettings()` holds the lane's key and secret, base `https://paper-api.alpaca.markets`, `deliberation_grace_seconds` 1800; `ProviderSettings()` the lane's key and secret; `AzureServiceBusSettings()` no connection string and no connection-strings JSON; `PortfolioManagerSettings()` `max_position_pct` `Decimal("0.01")` and `max_positions` 60; `DeliberatorSettings(role="manager")` `request_timeout_seconds` 240 |
| A10 | `test_a_surviving_fleet_value_is_refused_by_name` | an environment holding the values `sk` and `live`, against a fleet mapping that gives `live` to the fleet's DSN name and `sk` to its OpenAI key name: `refuse_leaks` raises, its message naming both names in sorted order, comma-separated; an environment holding neither value passes |
| A11 | `test_the_pack_leaves_out_the_peers_and_refuses_a_conflict` | on the committed pack `DELIBERATOR_REQUEST_TIMEOUT_SECONDS` is `"240"` and `SCANNER_CANDIDATE_CAP` `"25"`; `{"apps": {"a": {"X": "1"}, "b": {"X": 1}, "c": "not an object"}}` gives `{"X": "1"}`; `"1"` against `"2"` raises `ValueError` matching `sets X twice`; no `apps` raises matching `no apps object`; a pack file holding a JSON list raises matching `JSON object` |

**`orchestration/tests/test_lane_run.py`**

| # | Test | Must prove |
| --- | --- | --- |
| A12 | `test_a_lane_run_id_is_its_start_in_utc_to_the_second` | 2026-11-27 14:05:09 UTC gives `lane-20261127-140509` |
| A13 | 🎯 `test_the_session_is_the_last_one_settled_in_new_york`, parametrized | 2026-11-25 21:59 UTC → 2026-11-24; 2026-11-25 22:00 UTC → 2026-11-25; 2026-11-27 03:00 UTC → 2026-11-25 (Thanksgiving); 2026-11-29 03:00 UTC → 2026-11-27; 2026-12-01 03:00 UTC → 2026-11-30 |
| A14 | `test_no_session_in_ten_days_is_refused` | with `is_session=lambda _: False` it raises, matching `no NYSE session` |
| A15 | 🎯 `test_a_graph_holding_a_fleet_run_is_refused` | an in-memory graph with one `lane-1` RunRequest passes; add one keyed `run-request:x` with no `run_id` and one `sched-2026-11-25`: it raises, matching `2 run\(s\).*first 'run-request:x'` |
| A16 | `test_a_run_id_without_the_lane_prefix_is_refused` | `run_lane(InMemoryGraphStore(), (), tickers=("AAPL",), run_id="sched-2026-11-25", as_of=2026-11-25, max_rounds=1)` raises, matching `starts with 'lane-'` |
| A17 | 🎯 `test_rounds_run_until_one_advances_nothing` | three counting stages (3 items, 1 item, 1 item whose `process` raises): 4 rounds; advanced per round `{3-stage 1, 1-stage 1, raising 0}`, then `{1, 0, 0}` twice, then all 0; round 1's failed has the raising stage 1; each stage flushed 4 times |
| A18 | `test_rounds_stop_at_the_round_limit` | a stage with 1,000 items and `max_rounds=2`: two rounds, each advancing 1 |

**`orchestration/tests/test_lane_stages.py`** (a vocabulary-guarded in-memory graph from
`orchestration/packs/trading_graph_vocabulary.json`; `ProviderAgent` on `orchestration.tests.helpers.source()`
with `ProviderSettings(max_staleness_days=7)`; `PaperBroker()`)

| # | Test | Must prove |
| --- | --- | --- |
| A19 | 🎯 `test_each_stage_drives_the_function_its_entrypoint_hands_work_loop` | the stage names are `STAGE_NAMES`; each stage's `find` and `process` (a `functools.partial`'s `.func`) is the object of the same name in the agent's entrypoint module, read with `vars(module)[name]`: scanner (`find_pending`, `scan_market_node`), analyst (`find_pending`, `analyze_scan_node`), portfolio manager (`find_pending`, `evaluate_analyst_node`), execution and monitor (`find_pending_work`, `process_work_item`), reporter (`find_pending`, `report_monitor_node`); the provider's and the deliberator's against `agents/provider/poll.py` (`find_current_work`, `process_work_item`) and `agents/deliberator/poll.py` (`find_pending`, `review_pm_node`), which their entrypoints import inside `main()`; the forecaster's `process` is the entrypoint's `process_work_item` with `capabilities` equal to its `DEPLOYED_CAPABILITIES` |
| A20 | 🎯 `test_a_lane_run_passes_acceptance_with_real_debates` | with three counting fakes (`FakeLLMClient` subclasses; the debaters answer `test lane: defend` and `test lane: challenge`, the judge `FAKE_JUDGE_RULING`): `run_lane(..., tickers=("AAPL", "MSFT"), run_id="lane-test", as_of=<today, UTC>, max_rounds=12)` gives verdict `PASS`, a last round that advances nothing, fewer than 12 rounds, one `DeliberationRun` with verdicts `{"AAPL": "uphold", "MSFT": "uphold"}`, `real_debate_count` 2, `failed_open_count` 0, one `ExecutionRun`, one `Snapshot`, and each of the three fakes called at least once |

**`tests/test_run_lane_cli.py`** (module docstring `Agent: tooling`; the same `os.environ` fixture;
`scripts.run_lane._now` monkeypatched to 2026-11-27 03:00 UTC)

| # | Test | Must prove |
| --- | --- | --- |
| A21 | 🎯 `test_an_unsafe_start_is_refused_before_any_endpoint` | an env file holding only `ALPACA_TEST_API_KEY`: `main(["--env-file", <it>])` returns 2, prints a line starting `REFUSED: missing lane values`, and leaves `os.environ` equal to before; the four lane values plus a `POSTGRES_DSN` on the lane's own endpoint: returns 2, printing `live graph` |
| A22 | 🎯 `test_an_isolated_start_runs_one_lane_run_and_prints_its_verdict` | the four lane values and a fleet `POSTGRES_DSN` on another endpoint; `kernel.graph_env.build_graph_from_env`, `agents.provider.entrypoint.build_agent`, `agents.execution.broker_factory.broker_from_settings` and `orchestration.lane_run.last_closed_session` monkeypatched (a guarded in-memory graph that records `os.environ["POSTGRES_DSN"]` when built; a provider agent on the fixture source that records the `ProviderSettings().alpaca_api_key` it was given; `PaperBroker()`; today, UTC): `main(["--env-file", <it>, "--tickers", "aapl, msft"])` returns 0; the recorded DSN is the lane's and the recorded key `PKLANE`; the output starts `LANE RUN  2 tickers, at most 12 rounds` and holds `  run id   lane-20261127-030000` and `PASS` |
| A23 | `test_the_default_universe_is_the_fleets` | `scripts.run_lane._tickers("")` equals `FileUniverse().members(OrchestratorSettings().universe)` and is not empty |

---

## Success factors

- [ ] The eight files of Appendix B hold the blob ids it gives.
- [ ] The five test files: every file errors on the unchanged tree; 75 tests pass after Appendix B.
- [ ] The neighbours pass: `orchestration/tests` and `tests/test_accept_cli.py`.
- [ ] 25 of 25 breaks of Appendix C red, each on the test named for it, each restored.
- [ ] Every new module under 150 lines; no `# noqa` added beyond Appendix B's one; every module docstring
      declares `Agent:`, `Role:`, `External I/O:`.
- [ ] No change to any file outside Appendix B, the five test files, this spec and
      `docs/sprints/README.md`.
- [ ] `make ci` exit 0, 100.00 % coverage.

---

## Traps

🪤 **The tests leak the environment if they do not restore it.** `isolate_lane` writes into the
mapping it is given; on `os.environ` it adds the pack's values, the lane's DSN and keys, and removes
names. `monkeypatch.setenv` restores only what it set. Save the whole of `os.environ` before and
restore it after (a fixture), or later tests in the same process run with a lane environment.

🪤 **A name list taken from the production constant tests nothing about that list.** A2, A3 and A8
read `lane_fixtures.py`, never `FLEET_SECRET_NAMES`, `DROPPED_NAMES` or `FEED_NAMES`.

🪤 **detect-secrets flags a quoted value under a name with `KEY`, `SECRET` or `TOKEN` in it**, test
fakes included. Mark each such line with `# pragma: allowlist nextline secret` on the line above it, as
`agents/forecaster/tests/test_forecaster_finbert.py:75` does; never add `.secrets.baseline` entries,
and never put the pragma at the end of a line that would then pass 88 characters.

🪤 **A20 needs today's date as the session.** The fixture's bars are dated back from today, UTC;
`last_closed_session` would pick an earlier session and the analyst would score nothing (the
acceptance verdict then reads FAIL). `run_lane` takes `as_of` from its caller for this reason.

🪤 **The window check reads UTC.** A20 and A22 never call it with the real clock: `run_lane` does not
check the window (`isolate_lane` does), and A22 fixes `_now`.

🪤 **`AzureServiceBusSettings` is exported by `kernel`**; `DeliberatorSettings(role="manager")` needs
no `type: ignore` in a test (the literal matches), but `lane_debate._role` does, for a `str`.

🪤 **No existing test changes and none fails with or without Appendix B**: a green suite alone proves
nothing here. The proof is A1 to A23 and the breaks.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow.
  📌 Sizes after Appendix B: `lane_guard.py` **146**, `lane_env.py` **141**, `lane_debate.py` **76**,
  `lane_stages.py` **149**, `lane_run.py` **127**, `scripts/run_lane.py` **120**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version: Appendix B's two lines. **Do not run `uv lock` or `uv sync` in any form.**
- Secrets never through the worktree; the worktree has **no `.env`**, and nothing in this sprint needs
  one.

---

## Sequencing after merge (the planner's)

1. Re-measure the handback: the eight blob ids; the planner's tests in place of the builder's (kit
   `planner_tests/`); the breaks against the builder's tests (kit `s293_breaks.py`); the planner's own
   `make ci`; push; the branch's CodeQL alerts set-diffed against the last baseline (138); `make
   gate-ran` from the sprint worktree, the printed SHA checked against `git rev-parse HEAD`.
2. Fast-forward `main`, tag `v0.132.00`, check `main`'s runs on the merged SHA.
3. **F1, the planner's, outside 22:00 to 24:00 UTC:**
   1. Create the lane's branch: `POST /projects/<id>/branches` with
      `{"branch": {"parent_id": <production>, "name": "lane", "init_source": "schema-only"},
      "endpoints": [{"type": "read_write"}]}`; read its connection URI; put it in the main checkout's
      `.env` as `LANE_POSTGRES_DSN`. If the beta refuses, an ordinary branch, a new database on it and
      `alembic upgrade head` with that database's DSN as `POSTGRES_DSN` for that one command.
   2. Read before: the fleet account's positions and open orders (counts), and the live graph's
      RunRequests whose run id starts `lane-` (0).
   3. From the main checkout: `uv run python scripts/run_lane.py --tickers AAPL,MSFT,KO,JNJ,XOM`.
      Expect: no `REFUSED`; rounds that end with one advancing nothing; an acceptance verdict.
   4. Read after: the fleet account's counts equal before; the live graph still holds 0 `lane-`
      RunRequests; the lane's graph holds the run; the test account's orders equal the run's
      ExecutionRun (or none, if the PM approved none).
   5. Plant two refusals for real: the run again with `LANE_POSTGRES_DSN` set to the live DSN in a
      copy of the env file (`--env-file`), and once between 22:00 and 24:00 UTC with `--tickers AAPL`:
      both print `REFUSED` and exit 2.
   6. Teardown: cancel the F1 run's open orders on the test account; keep the branch, its rows and
      `LANE_POSTGRES_DSN` (they are the lane). Record the row in `docs/laws/functionality-checks.md`.
4. Close work-queue 136 at F1, or record what failed.

---

## Handover — paste this to Codex

```text
You are building Sprint 293 in the worktree ../ta-s293, on the branch
sprint-293-a-test-run-reaches-only-the-test-account-and-its-own-graph. Never work on main.

Read docs/sprints/sprint-293-a-test-run-reaches-only-the-test-account-and-its-own-graph.md,
whole, before anything else. It is the spec, and its bottom sections are your handback. Every
decision is made (DL-328): Appendix B is the whole production change, eight files, and you write
six test files (one helper and five test modules).

In order:
1. Read agents/execution/laws/laws.md and test-plan.md, agents/deliberator/laws/laws.md and
   test-plan.md, orchestration/laws/dispatcher/laws.md, docs/laws/conventions.md and
   docs/laws/drift-register.md. Fill the Law reading record in the spec BEFORE any change. The
   law-cycle answer is No (no contracts, kernel or agent file changes); say why in your words.
2. Write orchestration/tests/lane_fixtures.py and the five test files of the Test plan under
   exactly the names given. Every module docstring declares Agent, Role and External I/O. Run
     uv run --no-sync pytest orchestration/tests/test_lane_guard.py orchestration/tests/test_lane_env.py orchestration/tests/test_lane_run.py orchestration/tests/test_lane_stages.py tests/test_run_lane_cli.py --no-cov -q -p no:cacheprovider
   on the unchanged tree and paste the summary line into the Closeout. Expected: 5 errors (the
   modules they import do not exist yet).
3. Apply Appendix B: save its diff block to a file outside the repository's tracked files and run
   git apply on it. Then git hash-object on the eight files must print the eight blob ids
   Appendix B gives. Do NOT run uv lock or uv sync in any form.
4. Run the same pytest command again: 75 passed. Then
     uv run --no-sync pytest orchestration/tests tests/test_accept_cli.py --no-cov -q -p no:cacheprovider
   No test may fail.
5. Plant the 25 breaks of Appendix C one at a time. Each must go red on the test named for
   it. Restore each with git checkout of that file before the next (commit your work first, or
   keep a copy, so the restore returns your built file).
6. Run uv run --no-sync ruff format on your six test files, then make ci redirected to a file,
   and read the file. If a step cannot run in your sandbox (the dependency audit needs a
   network), say "not done" for that step and paste its lines.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in this
   sprint's row of docs/sprints/README.md (the row's status cell must lead with BUILT). Commit on
   the branch if your sandbox lets you write the repository's git directory; if not, leave the
   tree uncommitted and say so.

DO NOT: run uv lock or uv sync; run scripts/run_lane.py, scripts/run_local.py, any az command or
anything that reaches a network; create or read any .env; change any file Appendix B does not
name except your six test files, this spec and docs/sprints/README.md; change any existing test;
take a name list in A2, A3 or A8 from a production constant; add a design-log entry; edit
docs/STATE.md, docs/work-queue.md or docs/design-log.md; add entries to .secrets.baseline; use
noqa beyond Appendix B's; paste a whole make ci log into the spec; measure make ci through a pipe.

Traps: isolate_lane rewrites the mapping it is given, so a test that passes os.environ must
restore the whole environment afterwards (a fixture), or later tests run in a lane environment;
detect-secrets flags quoted test values under names holding KEY, SECRET or TOKEN: put
"# pragma: allowlist nextline secret" on the line above, never a baseline entry; A20 and A22
need today's date as the session, because the fixture's bars are dated back from today; no
existing test fails with the old code or the new, so a green suite alone proves nothing; ruff
format is a pre-commit hook.

Two tiers of trouble. A wrong path, count or command in this spec whose intent is plain: correct
it, go on, and record it in the Return notes. A blob id that does not match after a clean git
apply, a law that contradicts the spec, an existing test that fails, or a break that stays
green: STOP and report. State anything not done as "not done" or "verified failing". Never write
a Result for work you have not done.

Handback checklist, each answered in the Closeout:
 1. Law reading record filled before the first change; the law-cycle answer with its reason.
 2. Red output of step 2 pasted (5 errors).
 3. The eight blob ids after git apply, as printed.
 4. Green output of step 4 pasted (75 passed; the neighbours pass).
 5. git diff --stat against the base: exactly Appendix B's eight files, your six test files,
    this spec and docs/sprints/README.md.
 6. The 25 breaks, one line each: the test that went red, and restored.
 7. The line counts of your six test files.
 8. make ci: the file's path, the exit code, each step's verdict line, the pytest totals and
    coverage; every step not run named "not done".
 9. The tree the proofs ran in, and that it holds no .env.
10. Status BUILT in the spec and in the README row; committed or not, and the SHA if committed.
```

---

## Handback contract — MANDATORY

1. Fill the **Law reading record** *before* your first change.
2. Fill the **Test plan results** table. A test you chose not to write needs a reason, not a blank.
3. Fill **Closeout — evidence** with real pasted output.
4. Fill **Return notes**.
5. Set **Status:** to `BUILT`, here and in the README row.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| *(builder)* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *(builder)*

**Contradictions found between a law and this spec:** *(builder)*

**Laws found silent where a decision was needed:** *(builder)*

**Clauses that were ⬜ and are now proven:** *(builder)*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Decision or clause cited |
| --- | --- | --- | --- | --- |
| A1–A23 | *(builder)* | | | |

**Tests added beyond the plan:** *(builder)*

---

## Closeout — evidence

**Status:** *(builder: BUILT)*

**Tree the proofs ran in (and `.env` present?):** *(builder)*

**Result:** *(builder)*

**Files changed:** *(builder)*

**Proof — the red run first:** *(builder)*

**The eight blob ids:** *(builder)*

**Proof — the green run:** *(builder)*

**Guards planted:** *(builder: one line per break)*

**Module line counts:** *(builder)*

**`make ci`:** *(builder)*

**Not met / verified failing:** *(builder)*

---

## Return notes

- *(builder)*

---

## Appendix A — measured on the planner's prototype, 2026-11-27

`proto-s293` at `a9a081cc` (local, never pushed), branched from `main` `306ed69d`:

- The five test files against the prototype: 75 passed. On `main`'s tree (the test files
  alone): 5 errors, one per test module: four `ModuleNotFoundError` (`orchestration.lane_guard` twice,
  `lane_env`, `lane_debate`) and one `ImportError` (`cannot import name 'run_lane' from 'scripts'`).
  The dry run from this committed spec, in `../ta-s293` at its base: 5 errors; 8 of 8 blob ids after
  `git apply`; 75 passed; the tree restored clean (kit `dry_run.py`, `dry_run.txt`).
- The break script (kit OneDrive `wq136-2026-11-27/s293_breaks.py`), all 25 breaks against
  the planner's tests: 25 red, each on the test named for it; the tree clean after.
  Its first run read 23 of 25: the planted env file held every fleet name, so a name the shell
  alone set (B2) and an env-file name a shell had also loaded (B8) were never exercised. A8's plant
  was split in two (seven fleet names in each source, two plain names in both) and both went red.
- `make ci` on the prototype, every step: exit 0, every step: `mypy` no issues in 1,311 source files, import contracts 5 kept, `pytest` 5,423 passed and 8 skipped at 100.00 % coverage, the dependency audit "No unaccepted vulnerabilities; 1 accepted advisory re-checked", detect-secrets passed, no untracked file to scan (Windows).
- The in-memory run (A20's fixture): rounds `{provider, scanner, execution, monitor}`, then
  `{analyst, forecaster, portfolio_manager, deliberator, execution, monitor, reporter}`, then
  `{provider, forecaster}`, then none; ACCEPTANCE PASS; the two faults are the forecaster's designed
  refusal (11 bars against `barrier_min_history_sessions` 700).

---

## Appendix B — the change, measured on the planner's prototype

`git diff 306ed69d a9a081cc` over the eight production files. After `git apply`, `git hash-object`
on each must print:

```text
98095e73e4b3dfdd0bb02ac0b649ead1ef241e26  orchestration/lane_guard.py
a5d291795c65042680d0e36d17f6b0bbe18e66f6  orchestration/lane_env.py
96d5b58692f675d48d00cdaa0063acbe5a6414a0  orchestration/lane_debate.py
449a701f405746c73fe4eaf429d1dada1c8c2635  orchestration/lane_stages.py
63886f813205b0f84230b7cf4d712c901b78d553  orchestration/lane_run.py
999b7c568bfa9faa3ab7d065bdff55ac188a9810  scripts/run_lane.py
2135baf4bfec7df1a7eba6c29682c3ced11dab6a  pyproject.toml
3f8acc110e622f7e350a26f06b1e031e16f9cd74  uv.lock
```

```diff
diff --git a/orchestration/lane_debate.py b/orchestration/lane_debate.py
new file mode 100644
index 00000000..96d5b586
--- /dev/null
+++ b/orchestration/lane_debate.py
@@ -0,0 +1,76 @@
+"""Test-lane debate — the three deliberator roles on one in-process bus.
+
+Agent: orchestration
+Role: wire the deliberator's manager and its two peers for a test-lane run (DL-328):
+      the peers are bound on one ``InProcessBus`` and the manager reaches them through
+      ``BusPeerClient``, where the fleet uses Service Bus; every role answers with a
+      fake model, so a lane run makes no paid call.
+External I/O: none.
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from functools import partial
+from typing import TYPE_CHECKING, Any
+
+from agents.deliberator.agent import DeliberatorAgent
+from agents.deliberator.peer_client import BusPeerClient
+from agents.deliberator.poll import find_pending, review_pm_node
+from agents.deliberator.settings import DeliberatorSettings
+from kernel import FakeLLMClient, InProcessBus
+
+if TYPE_CHECKING:
+    from collections.abc import Callable
+
+    from kernel import FaultSink, GraphStore, LLMClient
+
+FAKE_JUDGE_RULING = (
+    '{"ruling": "uphold", "rationale": "test lane: the fake judge upholds every order"}'
+)
+"""Every judge ruling in a lane run is this fake ``uphold``."""
+
+
+@dataclass(frozen=True)
+class DebateModels:
+    """The model each deliberator role answers with."""
+
+    proponent: LLMClient
+    opponent: LLMClient
+    judge: LLMClient
+
+
+def fake_debate_models() -> DebateModels:
+    """Return a fake model for each of the three roles."""
+    return DebateModels(
+        proponent=FakeLLMClient({"DECISION UNDER TEST": "test lane: defend"}),
+        opponent=FakeLLMClient({"DECISION UNDER TEST": "test lane: challenge"}),
+        judge=FakeLLMClient({"DECISION UNDER TEST": FAKE_JUDGE_RULING}),
+    )
+
+
+def debate_pair(
+    graph: GraphStore, models: DebateModels, sink: FaultSink
+) -> tuple[Callable[[], list[Any]], Callable[[Any], None]]:
+    """Return the manager's work pair, its two peers bound beside it."""
+    bus = InProcessBus()
+    for role, llm in (("proponent", models.proponent), ("opponent", models.opponent)):
+        DeliberatorAgent(bus, graph=graph, llm=llm, settings=_role(role)).bind()
+    settings = _role("manager")
+    manager = DeliberatorAgent(bus, graph=graph, llm=models.judge, settings=settings)
+    process = partial(
+        review_pm_node,
+        graph=graph,
+        manager=manager,
+        peer_client=BusPeerClient(bus, sender=settings.identity),
+        settings=settings,
+        sink=sink,
+    )
+    return partial(find_pending, graph), process
+
+
+def _role(role: str) -> DeliberatorSettings:
+    return DeliberatorSettings(
+        role=role,  # type: ignore[arg-type]
+        instance_name=f"deliberator-{role}",
+    )
diff --git a/orchestration/lane_env.py b/orchestration/lane_env.py
new file mode 100644
index 00000000..a5d29179
--- /dev/null
+++ b/orchestration/lane_env.py
@@ -0,0 +1,141 @@
+"""Test-lane environment — the lane's process holds only the lane's endpoints.
+
+Agent: orchestration
+Role: rewrite the process environment for a test-lane run (DL-328): drop every name
+      the env file declares and every fleet endpoint name, carry only the data-feed
+      keys, point the graph at the lane DSN and the broker and market data at the
+      test paper account, apply the tunables pack as a full ``up`` does, then refuse
+      when any fleet secret's value is still present.
+External I/O: reads the tunables pack, the vocabulary and issuer-map paths it names.
+"""
+
+from __future__ import annotations
+
+import json
+from pathlib import Path
+from typing import TYPE_CHECKING
+
+from agents.portfolio_manager.issuer_map import ISSUER_MAP_PATH_ENV
+from kernel.graph_env import GRAPH_VOCABULARY_PATH_ENV
+from orchestration.lane_guard import (
+    FLEET_SECRET_NAMES,
+    PAPER_BASE_URL,
+    LaneRefusedError,
+    fleet_values,
+    lane_values,
+    refuse_unsafe_start,
+)
+
+if TYPE_CHECKING:
+    from collections.abc import Mapping, MutableMapping
+    from datetime import datetime
+
+    from orchestration.lane_guard import LaneValues
+
+PACKS = Path(__file__).resolve().parent / "packs"
+TUNABLES_PATH = PACKS / "trading_tunables.json"
+VOCABULARY_PATH = PACKS / "trading_graph_vocabulary.json"
+ISSUER_MAP_PATH = PACKS / "trading_issuer_map.json"
+
+FEED_NAMES = (
+    "PROVIDER_FINNHUB_API_KEY",
+    "PROVIDER_FMP_API_KEY",
+    "PROVIDER_ALPHAVANTAGE_API_KEY",
+    "PROVIDER_TIINGO_API_KEY",
+    "PROVIDER_FRED_API_KEY",
+)
+"""The only env-file values a lane run carries: read-only data feeds."""
+
+DROPPED_NAMES = (
+    *FLEET_SECRET_NAMES,
+    "ALPACA_BASE_URL",
+    "EXECUTION_ALPACA_BASE_URL",
+    "AZURE_SERVICEBUS_CONNECTION_STRINGS_JSON",
+    "AZURE_SERVICEBUS_NAMESPACE_ENDPOINT",
+    "MASTER_URL",
+    "GRAPH_VOCABULARY_B64",
+    "PORTFOLIO_MANAGER_ISSUER_MAP_B64",
+)
+"""Fleet endpoint names dropped even when the shell, not the env file, set them."""
+
+PEER_APPS = ("deliberator-proponent", "deliberator-opponent")
+"""Not applied: the peers differ from the manager only in a Service Bus wait."""
+
+
+def load_tunables_pack(path: Path = TUNABLES_PATH) -> Mapping[str, object]:
+    """Read the tunables pack a full ``up`` injects."""
+    data: object = json.loads(path.read_text(encoding="utf-8"))
+    if not isinstance(data, dict):
+        raise ValueError("tunables pack must be a JSON object")
+    return data
+
+
+def pack_tunables(pack: Mapping[str, object]) -> dict[str, str]:
+    """Return the pack's per-app values as one environment, the peers left out."""
+    apps = pack.get("apps")
+    if not isinstance(apps, dict):
+        raise ValueError("tunables pack has no apps object")
+    merged: dict[str, str] = {}
+    for app, values in apps.items():
+        if app in PEER_APPS or not isinstance(values, dict):
+            continue
+        for name, value in values.items():
+            if merged.get(name, str(value)) != str(value):
+                raise ValueError(f"tunables pack sets {name} twice, differently")
+            merged[name] = str(value)
+    return merged
+
+
+def lane_environment(
+    environ: MutableMapping[str, str],
+    dotenv: Mapping[str, str | None],
+    lane: LaneValues,
+    *,
+    pack: Mapping[str, object],
+) -> None:
+    """Rewrite *environ* so a run built from it reaches only the lane."""
+    for name in {*dotenv, *DROPPED_NAMES}:
+        environ.pop(name, None)
+    for name in FEED_NAMES:
+        value = (dotenv.get(name) or "").strip()
+        if value:
+            environ[name] = value
+    environ.update(pack_tunables(pack))
+    environ.update(
+        {
+            "POSTGRES_DSN": lane.dsn,
+            "EXECUTION_ALPACA_API_KEY": lane.key,
+            "EXECUTION_ALPACA_SECRET_KEY": lane.secret,
+            "EXECUTION_ALPACA_BASE_URL": PAPER_BASE_URL,
+            "PROVIDER_ALPACA_API_KEY": lane.key,
+            "PROVIDER_ALPACA_API_SECRET": lane.secret,
+            GRAPH_VOCABULARY_PATH_ENV: str(VOCABULARY_PATH),
+            ISSUER_MAP_PATH_ENV: str(ISSUER_MAP_PATH),
+        }
+    )
+
+
+def isolate_lane(
+    environ: MutableMapping[str, str],
+    dotenv: Mapping[str, str | None],
+    *,
+    now: datetime,
+    pack: Mapping[str, object],
+) -> LaneValues:
+    """Refuse an unsafe start, else rewrite *environ* for the lane and prove it."""
+    lane = lane_values(dotenv)
+    fleet = fleet_values(environ, dotenv)
+    refuse_unsafe_start(lane, fleet, now=now)
+    lane_environment(environ, dotenv, lane, pack=pack)
+    refuse_leaks(environ, fleet)
+    return lane
+
+
+def refuse_leaks(environ: Mapping[str, str], fleet: Mapping[str, str]) -> None:
+    """Raise LaneRefusedError when any fleet secret's value is still present."""
+    present = set(environ.values())
+    leaked = sorted(name for name, value in fleet.items() if value in present)
+    if leaked:
+        raise LaneRefusedError(
+            f"fleet values still in the lane's environment: {', '.join(leaked)}"
+        )
diff --git a/orchestration/lane_guard.py b/orchestration/lane_guard.py
new file mode 100644
index 00000000..98095e73
--- /dev/null
+++ b/orchestration/lane_guard.py
@@ -0,0 +1,146 @@
+"""Test-lane refusals — what must hold before a run may start on the test account.
+
+Agent: orchestration
+Role: refuse a test-lane start that could reach the fleet's broker account, graph or
+      data budget (work-queue 136 option A, DL-307, DL-328): a missing lane value, a
+      test key equal to a fleet key, an endpoint other than Alpaca's paper host, a lane
+      graph on the live Neon endpoint, or a start inside the fleet's nightly window.
+External I/O: none (reads the mappings and the clock it is handed).
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from datetime import UTC, time
+from typing import TYPE_CHECKING
+from urllib.parse import urlsplit
+
+if TYPE_CHECKING:
+    from collections.abc import Mapping
+    from datetime import datetime
+
+LANE_KEY = "ALPACA_TEST_API_KEY"
+LANE_SECRET = "ALPACA_TEST_API_SECRET"  # noqa: S105  # pragma: allowlist secret
+LANE_ENDPOINT = "ALPACA_TEST_ENDPOINT"
+LANE_DSN = "LANE_POSTGRES_DSN"
+PAPER_HOST = "paper-api.alpaca.markets"
+PAPER_BASE_URL = f"https://{PAPER_HOST}"
+
+FLEET_KEY_NAMES = (
+    "ALPACA_API_KEY",
+    "ALPACA_PAPER_API_KEY",
+    "EXECUTION_ALPACA_API_KEY",
+    "PROVIDER_ALPACA_API_KEY",
+)
+"""Every name a fleet Alpaca key id is read from: execution's and provider's."""
+
+FLEET_SECRET_NAMES = (
+    *FLEET_KEY_NAMES,
+    "ALPACA_API_SECRET",
+    "ALPACA_PAPER_API_SECRET",
+    "EXECUTION_ALPACA_SECRET_KEY",
+    "PROVIDER_ALPACA_API_SECRET",
+    "POSTGRES_DSN",
+    "SERVICEBUS_CONNECTION_STRING",
+    "AZURE_SERVICEBUS_CONNECTION_STRING",
+    "TELEGRAM_BOT_TOKEN",
+    "ANTHROPIC_API_KEY",
+    "OPENAI_API_KEY",
+)
+"""Names whose values reach the fleet's account, graph, bus, phone or LLM balance."""
+
+FLEET_WINDOW_UTC = (time(22, 0), time(23, 59, 59))
+"""The fleet's nightly window, the master's wake (22:00) to midnight (DL-294).
+
+The lane shares the data vendors' per-key budgets (Finnhub, FMP, Alpha Vantage)
+with the fleet, so a lane run inside the window could degrade the fleet's run.
+"""
+
+
+class LaneRefusedError(RuntimeError):
+    """A test-lane start was refused; the message names the condition."""
+
+
+@dataclass(frozen=True)
+class LaneValues:
+    """The four values a lane run is built from, read from the env file."""
+
+    key: str
+    secret: str
+    endpoint: str
+    dsn: str
+
+
+def lane_values(dotenv: Mapping[str, str | None]) -> LaneValues:
+    """Return the lane's four values; refuse when any is missing or blank."""
+    names = (LANE_KEY, LANE_SECRET, LANE_ENDPOINT, LANE_DSN)
+    missing = [name for name in names if not (dotenv.get(name) or "").strip()]
+    if missing:
+        raise LaneRefusedError(f"missing lane values: {', '.join(missing)}")
+    key, secret, endpoint, dsn = (str(dotenv[name]).strip() for name in names)
+    return LaneValues(key=key, secret=secret, endpoint=endpoint, dsn=dsn)
+
+
+def fleet_values(
+    environ: Mapping[str, str], dotenv: Mapping[str, str | None]
+) -> dict[str, str]:
+    """Return each fleet secret's value from the env file, else the environment."""
+    values: dict[str, str] = {}
+    for name in FLEET_SECRET_NAMES:
+        value = (dotenv.get(name) or environ.get(name) or "").strip()
+        if value:
+            values[name] = value
+    return values
+
+
+def refuse_unsafe_start(
+    lane: LaneValues, fleet: Mapping[str, str], *, now: datetime
+) -> None:
+    """Raise LaneRefusedError unless every start condition holds."""
+    _refuse_window(now)
+    _refuse_fleet_keys(lane, fleet)
+    if urlsplit(lane.endpoint).hostname != PAPER_HOST:
+        raise LaneRefusedError(
+            f"{LANE_ENDPOINT} must be Alpaca's paper host {PAPER_HOST}"
+        )
+    _refuse_fleet_graph(lane.dsn, fleet.get("POSTGRES_DSN", ""))
+
+
+def neon_endpoint_id(dsn: str) -> str:
+    """Return the DSN's endpoint id: the host's first label without ``-pooler``.
+
+    Neon serves one compute endpoint under two host names, direct and pooled
+    (``ep-x`` and ``ep-x-pooler``); both reach the same database.
+    """
+    host = (urlsplit(dsn).hostname or "").lower()
+    first = host.split(".", 1)[0]
+    return first.removesuffix("-pooler")
+
+
+def _refuse_window(now: datetime) -> None:
+    start, end = FLEET_WINDOW_UTC
+    clock = now.astimezone(UTC).time()
+    if start <= clock <= end:
+        raise LaneRefusedError(
+            "inside the fleet's nightly window (22:00 to 24:00 UTC): the lane "
+            "shares the data vendors' budgets with the fleet's run"
+        )
+
+
+def _refuse_fleet_keys(lane: LaneValues, fleet: Mapping[str, str]) -> None:
+    for name, value in fleet.items():
+        if value in (lane.key, lane.secret):
+            raise LaneRefusedError(
+                f"a test Alpaca value equals the fleet's {name}: the lane would "
+                "trade on the fleet's account"
+            )
+
+
+def _refuse_fleet_graph(lane_dsn: str, fleet_dsn: str) -> None:
+    if not neon_endpoint_id(lane_dsn):
+        raise LaneRefusedError(f"{LANE_DSN} names no host")
+    if fleet_dsn and neon_endpoint_id(lane_dsn) == neon_endpoint_id(fleet_dsn):
+        raise LaneRefusedError(
+            f"{LANE_DSN} is on the fleet's database endpoint: the lane would "
+            "write to the live graph"
+        )
diff --git a/orchestration/lane_run.py b/orchestration/lane_run.py
new file mode 100644
index 00000000..63886f81
--- /dev/null
+++ b/orchestration/lane_run.py
@@ -0,0 +1,127 @@
+"""Test-lane run — place one lane run and drive its stages until nothing moves.
+
+Agent: orchestration
+Role: start a test-lane run (DL-328): refuse a graph that holds any run but a lane
+      run, place a ``lane-`` RunRequest for the last closed NYSE session, run every
+      stage once per round until a round advances nothing, and read the run's
+      acceptance verdict the way the fleet's runs are read.
+External I/O: none (the injected graph and stages do the I/O).
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from datetime import UTC, datetime, time, timedelta
+from typing import TYPE_CHECKING
+from zoneinfo import ZoneInfo
+
+from agents.provider.domain.market_calendar import is_trading_session
+from contracts.provider import RUN_REQUEST_LABEL
+from kernel.work_loop import run_once
+from kernel.work_loop_state import WorkLoopState
+from orchestration.lane_guard import LaneRefusedError
+from orchestration.packs.trading_acceptance import accept_run
+from orchestration.start import place_run_request
+
+if TYPE_CHECKING:
+    from collections.abc import Callable
+    from datetime import date
+
+    from kernel import GraphStore
+    from orchestration.lane_stages import LaneStage
+    from orchestration.packs.trading_acceptance import TradingAcceptanceResult
+
+LANE_RUN_PREFIX = "lane-"
+NEW_YORK = ZoneInfo("America/New_York")
+SESSION_SETTLED = time(17, 0)
+"""A session counts as closed one hour after the 16:00 bell, once its bars settle."""
+
+
+@dataclass(frozen=True)
+class RoundReport:
+    """What each stage advanced and failed in one round."""
+
+    number: int
+    advanced: dict[str, int]
+    failed: dict[str, int]
+
+
+@dataclass(frozen=True)
+class LaneRunResult:
+    """A lane run's id, its rounds and its acceptance verdict."""
+
+    run_id: str
+    rounds: tuple[RoundReport, ...]
+    acceptance: TradingAcceptanceResult
+
+
+def lane_run_id(now: datetime) -> str:
+    """Return the run id for a lane run started at *now* (UTC, to the second)."""
+    return f"{LANE_RUN_PREFIX}{now.astimezone(UTC):%Y%m%d-%H%M%S}"
+
+
+def last_closed_session(
+    now: datetime, *, is_session: Callable[[date], bool] = is_trading_session
+) -> date:
+    """Return the latest NYSE session whose bars have settled by *now*."""
+    local = now.astimezone(NEW_YORK)
+    day = local.date()
+    if local.time() < SESSION_SETTLED:
+        day -= timedelta(days=1)
+    for _ in range(10):
+        if is_session(day):
+            return day
+        day -= timedelta(days=1)
+    raise LaneRefusedError(f"no NYSE session in the ten days before {local.date()}")
+
+
+def refuse_foreign_runs(graph: GraphStore) -> None:
+    """Refuse a graph holding any run that is not a lane run (a copy of the fleet's)."""
+    foreign = sorted(
+        str(node.props.get("run_id", node.key))
+        for node in graph.list_nodes(RUN_REQUEST_LABEL)
+        if not str(node.props.get("run_id", "")).startswith(LANE_RUN_PREFIX)
+    )
+    if foreign:
+        raise LaneRefusedError(
+            f"the lane graph holds {len(foreign)} run(s) that are not lane runs, "
+            f"first {foreign[0]!r}: it is not the lane's own graph"
+        )
+
+
+def run_rounds(
+    stages: tuple[LaneStage, ...], *, max_rounds: int
+) -> tuple[RoundReport, ...]:
+    """Run every stage once per round until a round advances nothing."""
+    states = {stage.name: WorkLoopState() for stage in stages}
+    reports: list[RoundReport] = []
+    for number in range(1, max_rounds + 1):
+        advanced: dict[str, int] = {}
+        failed: dict[str, int] = {}
+        for stage in stages:
+            result = run_once(stage.find, stage.process, state=states[stage.name])
+            stage.flush()
+            advanced[stage.name] = result.advanced
+            failed[stage.name] = result.failed
+        reports.append(RoundReport(number, advanced, failed))
+        if not any(advanced.values()):
+            break
+    return tuple(reports)
+
+
+def run_lane(
+    graph: GraphStore,
+    stages: tuple[LaneStage, ...],
+    *,
+    tickers: tuple[str, ...],
+    run_id: str,
+    as_of: date,
+    max_rounds: int,
+) -> LaneRunResult:
+    """Place one lane run on the lane graph, drive it, and read its verdict."""
+    if not run_id.startswith(LANE_RUN_PREFIX):
+        raise LaneRefusedError(f"a lane run id starts with {LANE_RUN_PREFIX!r}")
+    refuse_foreign_runs(graph)
+    place_run_request(graph, run_id=run_id, tickers=tickers, as_of=as_of)
+    rounds = run_rounds(stages, max_rounds=max_rounds)
+    return LaneRunResult(run_id, rounds, accept_run(graph, run_id))
diff --git a/orchestration/lane_stages.py b/orchestration/lane_stages.py
new file mode 100644
index 00000000..449a701f
--- /dev/null
+++ b/orchestration/lane_stages.py
@@ -0,0 +1,149 @@
+"""Test-lane stages — each agent's own work pair, wired as its entrypoint wires it.
+
+Agent: orchestration
+Role: build the nine run-path stages a test-lane run drives in one process (DL-328):
+      the ``find``/``process`` pair, settings and fault sink each entrypoint gives
+      its ``work_loop``; ``lane_debate`` wires the debate.
+External I/O: none (delegates to the injected graph, broker and provider agent).
+"""
+
+from __future__ import annotations
+
+from dataclasses import dataclass
+from datetime import UTC, datetime
+from functools import partial
+from typing import TYPE_CHECKING, Any
+
+from agents.analyst.poll import analyze_scan_node
+from agents.analyst.poll import find_pending as analyst_pending
+from agents.analyst.settings import AnalystSettings
+from agents.execution import poll as execution_poll
+from agents.execution.settings import ExecutionSettings
+from agents.forecaster import work as forecaster_work
+from agents.forecaster.entrypoint import build_served_bus as forecaster_bus
+from agents.forecaster.poll import DEPLOYED_CAPABILITIES
+from agents.monitor import poll as monitor_poll
+from agents.monitor.settings import MonitorSettings
+from agents.portfolio_manager.issuer_map import load_issuer_map_from_env
+from agents.portfolio_manager.poll import evaluate_analyst_node
+from agents.portfolio_manager.poll import find_pending as pm_pending
+from agents.portfolio_manager.settings import PortfolioManagerSettings
+from agents.provider import poll as provider_poll
+from agents.reporter.poll import find_pending as reporter_pending
+from agents.reporter.poll import report_monitor_node
+from agents.scanner.poll import find_pending as scanner_pending
+from agents.scanner.poll import scan_market_node
+from agents.scanner.settings import ScannerSettings
+from kernel import CollectingFaultSink
+from kernel.fault_graph import GraphFaultSink
+from orchestration.lane_debate import debate_pair
+
+if TYPE_CHECKING:
+    from collections.abc import Callable
+
+    from agents.execution.broker import Broker
+    from agents.provider.agent import ProviderAgent
+    from kernel import GraphStore
+    from orchestration.lane_debate import DebateModels
+
+STAGE_NAMES = (
+    "provider",
+    "scanner",
+    "analyst",
+    "forecaster",
+    "portfolio_manager",
+    "deliberator",
+    "execution",
+    "monitor",
+    "reporter",
+)
+"""The run-path agents in the order a run's work flows; each has a fault sink."""
+
+
+@dataclass(frozen=True)
+class LaneStage:
+    """One agent's work pair and its fault-sink flush (empty for unsinked loops)."""
+
+    name: str
+    find: Callable[[], list[Any]]
+    process: Callable[[Any], None]
+    flush: Callable[[], None]
+
+
+def build_stages(
+    graph: GraphStore,
+    *,
+    provider_agent: ProviderAgent,
+    broker: Broker,
+    models: DebateModels,
+) -> tuple[LaneStage, ...]:
+    """Return the run-path stages in ``STAGE_NAMES`` order."""
+    sink = {name: GraphFaultSink(graph, CollectingFaultSink()) for name in STAGE_NAMES}
+    find_debate, debate = debate_pair(graph, models, sink["deliberator"])
+    forecast = partial(
+        forecaster_work.process_work_item,
+        graph=graph,
+        bus=forecaster_bus(graph, sink["forecaster"]),
+        capabilities=DEPLOYED_CAPABILITIES,
+        sink=sink["forecaster"],
+    )
+    pairs: dict[str, tuple[Callable[[], list[Any]], Callable[[Any], None]]] = {
+        "provider": (
+            partial(provider_poll.find_current_work, graph),
+            partial(provider_poll.process_work_item, agent=provider_agent),
+        ),
+        "scanner": (
+            partial(scanner_pending, graph),
+            partial(scan_market_node, graph=graph, settings=ScannerSettings()),
+        ),
+        "analyst": (
+            partial(analyst_pending, graph),
+            partial(
+                analyze_scan_node,
+                graph=graph,
+                settings=AnalystSettings(),
+                sink=sink["analyst"],
+            ),
+        ),
+        "forecaster": (
+            lambda: forecaster_work.find_pending_work(graph, now=datetime.now(tz=UTC)),
+            forecast,
+        ),
+        "portfolio_manager": (
+            partial(pm_pending, graph),
+            partial(
+                evaluate_analyst_node,
+                graph=graph,
+                settings=PortfolioManagerSettings(),
+                issuer_map=load_issuer_map_from_env(),
+                sink=sink["portfolio_manager"],
+            ),
+        ),
+        "deliberator": (find_debate, debate),
+        "execution": (
+            partial(execution_poll.find_pending_work, graph),
+            partial(
+                execution_poll.process_work_item,
+                graph=graph,
+                broker=broker,
+                settings=ExecutionSettings(),
+                sink=sink["execution"],
+            ),
+        ),
+        "monitor": (
+            partial(monitor_poll.find_pending_work, graph),
+            partial(
+                monitor_poll.process_work_item,
+                graph=graph,
+                settings=MonitorSettings(),
+                sink=sink["monitor"],
+            ),
+        ),
+        "reporter": (
+            partial(reporter_pending, graph),
+            partial(report_monitor_node, graph=graph),
+        ),
+    }
+    return tuple(
+        LaneStage(name, *pairs[name], sink[name].flush) for name in STAGE_NAMES
+    )
diff --git a/pyproject.toml b/pyproject.toml
index e37819f3..2135baf4 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -1,6 +1,6 @@
 [project]
 name = "trading-agents"
-version = "0.131.09"
+version = "0.132.00"
 description = "An operator-controlled, single-user, agent-based trading system. Domain logic lives only in agents; the kernel is plumbing; contracts are the shared boundary."
 requires-python = ">=3.13"
 dependencies = [
diff --git a/scripts/run_lane.py b/scripts/run_lane.py
new file mode 100644
index 00000000..999b7c56
--- /dev/null
+++ b/scripts/run_lane.py
@@ -0,0 +1,116 @@
+"""Run one pipeline pass on the test lane: the test paper account and the lane's graph.
+
+Agent: tooling
+Role: the test run beside the fleet (work-queue 136 option A, DL-328): read the env
+      file without loading it, refuse an unsafe start, rewrite this process's
+      environment so only the lane's endpoints remain, then drive one lane run
+      through the nine run-path stages and print each round and the acceptance verdict.
+External I/O: reads the env file; the lane's PostgreSQL (LANE_POSTGRES_DSN); the test
+      Alpaca paper account (orders, positions, account); market-data feeds; stdout.
+
+Run it from the main checkout, which holds the only .env:
+  uv run python scripts/run_lane.py                       # the fleet's universe
+  uv run python scripts/run_lane.py --tickers AAPL,MSFT,KO
+Exit code: 0 when the acceptance verdict passes, 1 when it does not, 2 when refused.
+"""
+
+from __future__ import annotations
+
+import argparse
+import os
+import sys
+from datetime import UTC, datetime
+from pathlib import Path
+
+_ROOT = Path(__file__).resolve().parents[1]
+if str(_ROOT) not in sys.path:
+    sys.path.insert(0, str(_ROOT))
+
+from orchestration.lane_guard import LaneRefusedError  # noqa: E402
+
+
+def main(argv: list[str] | None = None) -> int:
+    """Refuse or isolate, then run one lane run and print what it did."""
+    args = _parser().parse_args(argv)
+    from dotenv import dotenv_values
+
+    from orchestration.lane_env import isolate_lane, load_tunables_pack
+
+    now = _now()
+    try:
+        isolate_lane(
+            os.environ,
+            dotenv_values(args.env_file),
+            now=now,
+            pack=load_tunables_pack(),
+        )
+        return _run(args, now)
+    except LaneRefusedError as refused:
+        print(f"REFUSED: {refused}")
+        return 2
+
+
+def _run(args: argparse.Namespace, now: datetime) -> int:
+    from agents.execution.broker_factory import broker_from_settings
+    from agents.execution.settings import ExecutionSettings
+    from agents.provider.entrypoint import build_agent
+    from agents.provider.settings import ProviderSettings
+    from kernel.graph_env import build_graph_from_env
+    from orchestration.lane_debate import fake_debate_models
+    from orchestration.lane_run import lane_run_id, last_closed_session, run_lane
+    from orchestration.lane_stages import build_stages
+    from orchestration.packs.trading_acceptance import render_acceptance
+
+    graph = build_graph_from_env()
+    stages = build_stages(
+        graph,
+        provider_agent=build_agent(ProviderSettings(), graph),
+        broker=broker_from_settings(ExecutionSettings()),
+        models=fake_debate_models(),
+    )
+    tickers = _tickers(args.tickers)
+    print(f"LANE RUN  {len(tickers)} tickers, at most {args.max_rounds} rounds")
+    as_of = last_closed_session(now)
+    result = run_lane(
+        graph,
+        stages,
+        tickers=tickers,
+        run_id=lane_run_id(now),
+        as_of=as_of,
+        max_rounds=args.max_rounds,
+    )
+    print(f"  run id   {result.run_id}  (session {as_of.isoformat()})")
+    for report in result.rounds:
+        moved = ", ".join(f"{k} {v}" for k, v in report.advanced.items() if v)
+        broke = ", ".join(f"{k} {v}" for k, v in report.failed.items() if v)
+        print(f"  round {report.number:>2}  advanced: {moved or '-'}")
+        print(f"            failed:   {broke or '-'}")
+    print(render_acceptance(result.acceptance))
+    return 0 if result.acceptance.passed else 1
+
+
+def _now() -> datetime:
+    return datetime.now(tz=UTC)
+
+
+def _tickers(raw: str) -> tuple[str, ...]:
+    if raw:
+        return tuple(t.strip().upper() for t in raw.split(",") if t.strip())
+    from agents.scanner.universe import FileUniverse
+    from orchestration.settings import OrchestratorSettings
+
+    return FileUniverse().members(OrchestratorSettings().universe)
+
+
+def _parser() -> argparse.ArgumentParser:
+    parser = argparse.ArgumentParser(description="one run on the test lane")
+    parser.add_argument("--env-file", default=".env", help="the env file to read")
+    parser.add_argument(
+        "--tickers", default="", help="comma-separated tickers; default the fleet's"
+    )
+    parser.add_argument("--max-rounds", type=int, default=12, help="round limit")
+    return parser
+
+
+if __name__ == "__main__":
+    sys.exit(main())
diff --git a/uv.lock b/uv.lock
index 98db7b5e..3f8acc11 100644
--- a/uv.lock
+++ b/uv.lock
@@ -3669,7 +3669,7 @@ wheels = [

 [[package]]
 name = "trading-agents"
-version = "0.131.9"
+version = "0.132.0"
 source = { virtual = "." }
 dependencies = [
     { name = "cryptography" },
```

---

## Appendix C — the 25 breaks, as exact replacements

Each replaces one exact text, found once in its file, and must turn the named test red. Restore
the file before the next.

| # | File | Replace | With | Must fail |
| --- | --- | --- | --- | --- |
| B1 | `orchestration/lane_guard.py` | `    "PROVIDER_ALPACA_API_KEY",\n)` | `\n)` | `test_every_fleet_name_is_read_from_the_env_file_then_the_environment` |
| B2 | `orchestration/lane_guard.py` | `    "SERVICEBUS_CONNECTION_STRING",\n` | *(nothing)* | `test_the_lane_environment_holds_no_fleet_value` |
| B3 | `orchestration/lane_guard.py` | `first.removesuffix("-pooler")` | `first` | `test_the_fleets_database_endpoint_is_refused_direct_or_pooled` |
| B4 | `orchestration/lane_guard.py` | `if start <= clock <= end:` | `if start < clock <= end:` | `test_the_fleets_nightly_window_is_refused` |
| B5 | `orchestration/lane_guard.py` | `clock = now.astimezone(UTC).time()` | `clock = now.time()` | `test_the_fleets_nightly_window_is_refused` |
| B6 | `orchestration/lane_guard.py` | `if value in (lane.key, lane.secret):` | `if value == lane.key:` | `test_a_test_value_equal_to_a_fleet_value_is_refused` |
| B7 | `orchestration/lane_guard.py` | `!= PAPER_HOST:` | `not in (PAPER_HOST, "api.alpaca.markets"):` | `test_an_endpoint_other_than_the_paper_host_is_refused` |
| B8 | `orchestration/lane_env.py` | `for name in {*dotenv, *DROPPED_NAMES}:` | `for name in DROPPED_NAMES:` | `test_the_lane_environment_holds_no_fleet_value` |
| B9 | `orchestration/lane_env.py` | `    "MASTER_URL",\n` | *(nothing)* | `test_the_lane_environment_holds_no_fleet_value` |
| B10 | `orchestration/lane_env.py` | `PEER_APPS = ("deliberator-proponent", "deliberator-opponent")` | `PEER_APPS = ("deliberator-proponent",)` | `test_the_pack_leaves_out_the_peers_and_refuses_a_conflict` |
| B11 | `orchestration/lane_env.py` | `            "EXECUTION_ALPACA_BASE_URL": PAPER_BASE_URL,\n` | *(nothing)* | `test_the_lane_environment_holds_no_fleet_value` |
| B12 | `orchestration/lane_env.py` | `    if leaked:` | `    if leaked and not leaked:` | `test_a_surviving_fleet_value_is_refused_by_name` |
| B13 | `orchestration/lane_env.py` | `    environ.update(pack_tunables(pack))` | `    pack_tunables(pack)` | `test_settings_built_after_isolation_reach_only_the_lane` |
| B14 | `orchestration/lane_env.py` | `            ISSUER_MAP_PATH_ENV: str(ISSUER_MAP_PATH),\n` | *(nothing)* | `test_the_lane_environment_holds_no_fleet_value` |
| B15 | `orchestration/lane_run.py` | `SESSION_SETTLED = time(17, 0)` | `SESSION_SETTLED = time(16, 0)` | `test_the_session_is_the_last_one_settled_in_new_york` |
| B16 | `orchestration/lane_run.py` | `.startswith(LANE_RUN_PREFIX)\n    )` | `.startswith(("lane-", "sched-"))\n    )` | `test_a_graph_holding_a_fleet_run_is_refused` |
| B17 | `orchestration/lane_run.py` | `        if not any(advanced.values()):` | `        if True:` | `test_rounds_run_until_one_advances_nothing` |
| B18 | `orchestration/lane_run.py` | `    if not run_id.startswith(LANE_RUN_PREFIX):` | `    if not run_id:` | `test_a_run_id_without_the_lane_prefix_is_refused` |
| B19 | `orchestration/lane_stages.py` | `from agents.forecaster.poll import DEPLOYED_CAPABILITIES` | `from agents.forecaster.poll import LOCAL_CAPABILITIES as DEPLOYED_CAPABILITIES` | `test_each_stage_drives_the_function_its_entrypoint_hands_work_loop` |
| B20 | `orchestration/lane_stages.py` | `partial(execution_poll.find_pending_work, graph)` | `partial(execution_poll.find_pending, graph)` | `test_each_stage_drives_the_function_its_entrypoint_hands_work_loop` |
| B21 | `orchestration/lane_stages.py` | `partial(provider_poll.find_current_work, graph)` | `partial(provider_poll.find_pending_work, graph)` | `test_each_stage_drives_the_function_its_entrypoint_hands_work_loop` |
| B22 | `orchestration/lane_debate.py` | `llm=models.judge, settings=settings` | `llm=models.proponent, settings=settings` | `test_a_lane_run_passes_acceptance_with_real_debates` |
| B23 | `orchestration/lane_debate.py` | `{"ruling": "uphold", ` | `{"ruling": "overturn", ` | `test_a_lane_run_passes_acceptance_with_real_debates` |
| B24 | `scripts/run_lane.py` | `        return 2\n` | `        return 0\n` | `test_an_unsafe_start_is_refused_before_any_endpoint` |
| B25 | `scripts/run_lane.py` | `t.strip().upper()` | `t.strip()` | `test_an_isolated_start_runs_one_lane_run_and_prints_its_verdict` |
