<!-- Agent: planning | Role: sprint handover -->
# Sprint 294 — the local demonstrator reaches nothing outside its own process

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-294-the-local-demonstrator-reaches-nothing-outside-its-process`
**Status:** MERGED 2026-11-28 — `0.132.01`, fast-forwarded to `054d1141`, tag `v0.132.01`, GATE PROVEN; F1 passed (05:24 UTC); no deploy
**Version:** `0.132.01` (PATCH)
**Effort:** S
**Decisions:** [DL-329](../design-log.md) (this sprint's five decisions, made and measured) · [DL-328](../design-log.md) (the test lane, the run on real data since S293) · [work-queue 144](../work-queue.md)

> **Why this bump kind.** No new capability. A demonstrator flag writes to the live graph and
> another loads the fleet's secrets into the process; both leave, and the run on real data they
> stood for already exists as the test lane. A hazard removed: a PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 4 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | No agent's law binds a script in `scripts/`; none is edited. Read-only |
| `docs/laws/conventions.md` | Module headers, test docstrings, clause citations | Binds the new test file's header and docstrings |
| `docs/laws/drift-register.md` | Where a law found wrong or silent is recorded | The one law-adjacent file you may append to; this sprint expects no row |

Binding: **`docs/laws/conventions.md`** (the `Agent:` / `Role:` / `External I/O:` header; a test cites
what governs it). No clause governs the demonstrator, so the tests cite **DL-329**'s decisions.

### The rule

1. **Before writing code**, read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md), whole.
2. Read [DL-329](../design-log.md) and DL-328's *Decided* list (the lane this sprint points at).
3. **Answer the law-cycle question below** in the Law reading record.
4. **Write the Law reading record** (bottom of this file) **before** your first change.
5. **If a law contradicts this spec, STOP and report.**
6. Every new test cites the DL-329 decision it proves (`D1`, `D2` or `D3`) in its docstring.

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**No.** No file in `contracts/`, `kernel/`, `agents/` or `orchestration/` changes. The change is to
tooling in `scripts/`, one guide and the version lines; the property it adds (the demonstrator
reaches nothing outside its process) is a tooling decision recorded as DL-329, not an agent's
guarantee. No law cycle is owed.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `scripts/run_local.py`, `accept.py`, `observatory.py`, `trace_run.py`, `module_size_baseline.py` | `docs/laws/conventions.md`; DL-329; DL-328 | The module header; D1 to D3 |
| `scripts/universe_sp100.txt`, `scripts/universe_sp500.txt`, `docs/observability.md` | DL-329 D3 | One comment line each; the guide's three bullets |
| `tests/test_run_local_stays_in_process.py` (new) | `docs/laws/conventions.md` | Module header; each test cites its DL-329 decision |

⚠️ **One invariant.** `orchestration/local_pipeline.py::cascade_once` and every test that calls it are
untouched: 27 test files use it, and its `deliberation_llm` parameters stay. If your change would edit
anything outside Appendix B's ten files, the new test file, this spec and `docs/sprints/README.md`,
stop and report.

---

## Goal

At merge, `scripts/run_local.py` accepts `--trace`, `--observe` and `--run-id` and nothing else:
`--real`, `--veto`, `--universe`, `--chunk-size`, `--chunk-delay` and `--ohlcv-only` are refused by
argparse with exit 2 before any graph, settings or model is built. Every remaining flag runs on an
in-memory graph, the fake data source and the in-process paper broker, loads no `.env`, writes no
environment name, builds no model client and opens no connection. The module's docstring, the three
sibling scripts, the two universe files and `docs/observability.md` name the test lane
(`scripts/run_lane.py`) as the run on real data, and no committed file tells a reader to run a removed
flag.

## Why (context)

Work-queue 144, found packaging S293. `--real` calls `load_dotenv()` and then
`build_graph_from_env()`: from the main checkout, the one tree with `.env`, it places a `local-1`
RunRequest on the live graph, where an awake fleet would pick it up. Nothing runs it unprompted, but
`docs/observability.md` gives it as *the* one-command test run, and the hazard is one habit away. Since
S293 the test lane runs the fleet's own work on the test paper account and a graph of its own, and
refuses any start that could reach the fleet (DL-328); the demonstrator's live mode has no job left.
Asking whether `--real` was the only way out found a second: `--veto` loads `.env` by itself.

### Measured, 2026-11-28 — read these before designing

Every probe below refuses `socket.getaddrinfo` and `socket.socket.connect` before a byte leaves
(kit OneDrive `wq144-2026-11-28/`; run from the main checkout, `.env` present, unless stated).

| Claim | Value | How it was measured |
| --- | --- | --- |
| What `--real` reaches | the graph factory, with the env file's own `POSTGRES_DSN` (the live graph's) | *[measured]* `probe_real_stops_at_graph.py`: `kernel.graph_env.build_graph_from_env` replaced by a recorder that raises; the DSN compared with `.env`'s, never printed |
| What `--veto` does without `--real` | `load_dotenv()` once; 52 names added to the process, `POSTGRES_DSN` among them; an OpenAI `gpt-5.5` debate client and an Anthropic `claude-opus-4-8` judge built on the fleet's keys; 0 network attempts; verdicts `{}` | *[measured]* `probe_demo_network.py --veto` |
| Why `--veto` never calls a model in the demo | the analyst rejects both tickers (`target_estimate_unavailable`), so no order reaches the debate | *[measured]* the same run's observatory |
| What the demo does (`--trace --observe`) | 0 `load_dotenv` calls, 0 names added, 0 network attempts; RunRequest 1, Snapshot 1 | *[measured]* `probe_demo_network.py --trace --observe` |
| Whether the demo reads `.env` at all | yes, through the agents' settings: `kernel/config.py::AgentSettings` reads `.env` from the working directory, as every agent's does; nothing built from those values reaches out (0 attempts above) | *[read]* `kernel/config.py:61-74`; *[measured]* above |
| `local-` runs on the live graph | 0 of 122 RunRequests (21 are not `sched-`: `check-`, `confirm-`, `manual-`, `probe-`, `verify-`) | *[measured 2026-11-28 09:40 AEDT]* `live_local_runs.py`, read-only |
| Who reads `scripts/universe_sp500.txt` | no code names it; its own header names `run_local.py --universe`, which reads any path it is given | *[measured]* `git grep -n universe_sp500` over the code trees prints nothing |
| Who reads `scripts/universe_sp100.txt` | `agents/scanner/universe.py` (the `sp500` universe, so the dispatcher and the lane); the orchestration image copies it; a build-images path | *[measured]* `git grep -n universe_sp100`; `orchestration/Dockerfile:118`; `.github/workflows/build-images.yml:16` |
| Tests that run `run_local.py` today | none; `scripts/` is outside the coverage source | *[measured]* `git grep -n run_local -- tests '*/tests'` prints nothing; `pyproject.toml` `[tool.coverage.run]` |
| `run_local.py`'s size | 227 lines, frozen in `scripts/module_size_baseline.py`; 138 on the prototype, so the entry must go | *[measured]* `wc -l`; `tests/test_check_module_size.py::test_every_baselined_path_is_over_the_block_today` fails while the entry stays (break B21) |
| `docs/observability.md`'s test-run bullet | recommends `run_local.py --real --observe` against "live Aura + Tiingo" and says the observatory reads Neo4j; Aura is gone (ADR-0014) | *[read]* `docs/observability.md:52-57` |
| The prototype | 15 of the 19 new test cases red on the unchanged tree, 19 green after; 21 planted breaks red; `make ci` exit 0 | *[measured]* `proto-s294` (never pushed); Appendix B, Appendix C, Closeout of the planner's prototype below |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first.** One new file, `tests/test_run_local_stays_in_process.py`, with the
   six tests of the Test plan under exactly its names. On the unchanged tree they give 15 failed,
   4 passed.
2. **The change.** Apply Appendix B exactly: `scripts/run_local.py`, `accept.py`, `observatory.py`,
   `trace_run.py`, `module_size_baseline.py`, `universe_sp100.txt`, `universe_sp500.txt`,
   `docs/observability.md`, and one line each of `pyproject.toml` and `uv.lock`.
3. **The handback** at the bottom of this file, and this sprint's row of [`README.md`](README.md).

### Out of scope (do NOT build this sprint)

- **`orchestration/local_pipeline.py` and its tests.** `cascade_once` keeps its `deliberation_llm`
  parameters; its tests use them.
- **`scripts/deliberate.py`.** Its own `--real` is a paid debate the operator asks for by name.
- **The `--run-id` defaults** (`local-1`) of `accept.py`, `observatory.py`, `trace_run.py`. Only their
  docstrings change (DL-329, ruled out).
- **`scripts/universe_sp500.txt`'s tickers.** One comment line changes; the file stays.
- **`kernel/config.py`'s `.env` reading.** The kernel's design for every agent; named, not done.
- **Any other file.** No `laws.md` edit, no ADR, no design-log entry (DL-329 is written).

### The road not taken (LAW-06)

- **Point `--real` at the lane's guard.** Rejected: `cascade_once` runs a subset of each agent's work
  (DL-328), so a guarded `--real` would be a second, weaker lane.
- **Refuse `--real` when `POSTGRES_DSN` looks like the fleet's.** Rejected: a DSN's shape does not say
  whose it is; the lane refuses by comparing two named values the demonstrator does not hold.
- **Keep `--veto` on fake models.** Rejected: no order reaches the debate on the demo's data, so it
  would print an empty verdict; the lane runs the deliberator's own roles on fakes.
- **Keep `--universe` for the fake source.** Rejected: the fake has bars for two tickers; any other
  universe fails pre-flight.
- **Delete `scripts/universe_sp500.txt`.** Rejected: the ledger cites it; removing data is its own
  decision.
- **Leave `run_local.py` in the size baseline.** Not allowed: the checker and its test fail on an
  entry under 200 lines.

---

## The design decisions — made, and recorded in DL-329

**Nothing is left for the builder to decide.** Do not add a design-log entry.

1. **D1** — six flags leave (`--real`, `--veto`, `--universe`, `--chunk-size`, `--chunk-delay`,
   `--ohlcv-only`); argparse refuses each with exit 2. `--trace`, `--observe`, `--run-id` stay.
2. **D2** — the demonstrator is in-memory only: no `.env` loaded, no environment name written, no
   model built, no connection opened.
3. **D3** — every pointer moves to the lane: the module docstring, the three sibling scripts, the two
   universe files, `docs/observability.md` (its stale Aura and Neo4j lines go too).
4. **D4** — PATCH; both version lines are in Appendix B; `uv lock` is not run.
5. **D5** — no deploy.

---

## Blast radius — measured 2026-11-28

| What | Detail |
| --- | --- |
| Files changed | `scripts/run_local.py` (227 → 138), `scripts/accept.py`, `observatory.py`, `trace_run.py` (one docstring line each), `scripts/module_size_baseline.py` (one entry out), `scripts/universe_sp100.txt`, `universe_sp500.txt` (one comment line each), `docs/observability.md` (three bullets), `pyproject.toml`, `uv.lock` (one line each); `tests/test_run_local_stays_in_process.py` (new, 147 on the prototype); this spec; `docs/sprints/README.md` |
| Agents affected | none. No agent, kernel, contracts or orchestration file changes |
| Contract change? | no |
| Graph vocabulary change? | no |
| New env keys / tunables | none |
| Deploy implication | none. The merge builds images (`pyproject.toml`, `uv.lock` and `scripts/universe_sp100.txt` are build paths); the orchestration image's universe file differs by one `#` line its loader skips. Not a fidelity decision path |
| Rollback | revert the commit. Nothing live changes: no graph write, no order, no setting |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Plant the failing tests first** (Test plan) and run them on the unchanged tree:
   `uv run --no-sync pytest tests/test_run_local_stays_in_process.py tests/test_check_module_size.py --no-cov -q -p no:cacheprovider`.
   Paste the output: **15 failed, 12 passed** on the planner's prototype (the 12 are A2's four cases
   and the size checker's eight tests).
3. **Apply Appendix B**, exactly, and check the ten blob ids it gives.
4. **Run the same command again: 27 passed.**
5. **Prove the guards can fail (DL-70):** the 21 breaks of Appendix C, one at a time, each red on the
   test named for it, each restored before the next.
6. **`make ci` green**, every step of the `ci:` target (count them from the `Makefile`),
   **redirected to a file, never piped**.
7. **Fill the handback sections** at the bottom of this file.

---

## Test plan

One file, `tests/test_run_local_stays_in_process.py`, under **exactly these names** (the planner's
break script judges by them). Its docstring declares `Agent: tooling`, a `Role:` and
`External I/O: reads committed files; no network, no database, no actual .env.` It imports the script
as `from scripts import run_local` (as `tests/test_run_lane_cli.py` imports `run_lane`) and calls
`run_local.main()` with `sys.argv` monkeypatched to `["run_local.py", *argv]`.

**The fixture `doors_shut`** (used by A1 and A2) depends on `preserve_environment` from
`orchestration.tests.lane_fixtures` (import it as `preserve_environment as preserve_environment`, as
`tests/test_run_lane_cli.py` does), so the whole environment is restored after each case. It
monkeypatches each of `dotenv.load_dotenv`, `dotenv.dotenv_values`,
`kernel.graph_env.build_graph_from_env`, `socket.getaddrinfo` and `socket.socket.connect` to one
function that raises `AssertionError("the demonstrator reached outside its process")`, and sets
`POSTGRES_DSN` to `postgresql://planted@fleet.invalid/live`.

| # | Test | On the unchanged tree | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 `test_a_flag_that_reached_outside_the_process_is_refused`, parametrized over the argv `["--real"]`, `["--veto"]`, `["--universe", "scripts/universe_sp100.txt"]`, `["--chunk-size", "5"]`, `["--chunk-delay", "1"]`, `["--ohlcv-only"]`, ids the first token; uses `doors_shut` | all six fail (`--real` and `--veto` at a shut door, the other four run and do not raise) | `main()` raises `SystemExit` with code 2, and stderr holds `unrecognized arguments: <first token>`. Docstring cites `DL-329 D1` |
| A2 | 🎯 `test_the_demo_reaches_nothing_outside_the_process`, parametrized over `[]`, `["--trace"]`, `["--observe"]`, `["--trace", "--observe", "--run-id", "demo-2"]`; uses `doors_shut` | all four pass: a guard, red only under the breaks | `main()` returns; stdout holds `MODE: demo  (in-memory + fake data)`, `placed RunRequest run-request:<id> (2 tickers)` (`local-1`, or `demo-2` for the last case) and `  RunRequest     1`; `dict(os.environ)` after equals it before the call. Docstring cites `DL-329 D2` |
| A3 | `test_the_help_offers_only_the_in_memory_demo` | fails | `--help` raises `SystemExit` with code 0; the set of `--[a-z][a-z-]*` matches in stdout is exactly `{"--help", "--trace", "--observe", "--run-id"}`; stdout holds neither `POSTGRES` nor `Tiingo`. Docstring cites `DL-329 D1` |
| A4 | `test_the_docstring_sends_a_real_run_to_the_lane` | fails | `run_local.__doc__` holds `scripts/run_lane.py` and `No network, no database, no model call`, and none of the six removed flags, `POSTGRES_DSN` or `Tiingo`. Docstring cites `DL-329 D3` |
| A5 | 🪤 `test_no_committed_file_points_at_a_removed_flag`, parametrized over `scripts/accept.py`, `scripts/observatory.py`, `scripts/trace_run.py`, `scripts/universe_sp100.txt`, `scripts/universe_sp500.txt`, `docs/observability.md` | all six fail | the file's text (UTF-8, from the repository root) holds no `run_local.py <flag>` for any of the six removed flags. Docstring cites `DL-329 D3` |
| A6 | `test_the_observability_guide_sends_a_test_run_to_the_lane` | fails | `docs/observability.md` holds `scripts/run_lane.py --tickers` and `scripts/run_local.py --observe`. Docstring cites `DL-329 D3` |

---

## Success factors

- [x] The ten files of Appendix B carry its blob ids.
- [x] Each removed flag is refused with exit 2 before any graph or model: A1.
- [x] Every remaining flag runs with each outward door shut and writes no environment name: A2.
- [x] The help, the docstring and every pointer name only the demo and the lane: A3 to A6.
- [x] The six tests exist under the names given; 15 cases were seen failing first, then all 19 pass.
- [x] The law-cycle answer and the reading record are filled before the first change.
- [x] Each of the 21 breaks was planted, seen red on its named test, and restored.
- [x] `run_local.py` is under 200 lines and out of the size baseline; every touched module under 200.
- [x] `make ci` exit 0, 100.00 % coverage; a step the sandbox cannot run is named "not done".

---

## Traps

🪤 **Do not run `uv lock` or `uv sync`, in any form.** The lock was written by a newer `uv`; it changes
in **one line**, given in Appendix B (`0.132.0` → `0.132.1`, the lock's normalised form).

🪤 **Restore the whole environment in the tests.** On the unchanged tree `--chunk-size` and
`--ohlcv-only` write `PROVIDER_INGEST_*` names into `os.environ`; without `preserve_environment` they
leak into every later test of the session.

🪤 **Patch `dotenv.load_dotenv` and `dotenv.dotenv_values` as module attributes.** `run_local.py` and
`scripts/deliberate.py` import them inside the function, so the patch reaches them;
`pydantic-settings` imported its own `dotenv_values` when the kernel loaded, so the agents' settings
still build. `kernel.graph_env.build_graph_from_env` is imported inside `main()` too.

🪤 **A2 is green on both trees.** It pins D2; only breaks B7 to B11 show it can fail.

🪤 **The size baseline must lose its entry.** With the entry kept, `check_module_size.py` and
`test_every_baselined_path_is_over_the_block_today` both fail (B21).

🪤 **Apply the diff; do not retype.** `run_local.py`'s docstring keeps its `—` and `→` characters, and
the blob ids catch a single different byte.

🪤 **`ruff format` runs as a pre-commit hook.** Run `uv run --no-sync ruff format` on the test file
before committing. No `# noqa`.

🪤 **Paste step lines and verdicts into the Closeout, not the whole `make ci` log.**

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150), tests included. No `# noqa`.
  📌 Prototype sizes: `scripts/run_local.py` **138**, `tests/test_run_local_stays_in_process.py` **147**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers in code. The planted DSN and the argv values are test data.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe.** Redirect to a file and read the file.
- Version bump of the kind named at the top, `uv.lock` staged with it, both from Appendix B.
- Secrets never through the worktree. The worktree has **no `.env`** and this sprint needs none.
  **State which tree you ran in.**

---

## Sequencing after merge (the planner's)

1. The planner re-measures: the ten blobs against Appendix B; the planner's test file run in place of
   the builder's; the break script against the builder's test file (21 breaks); the planner's own
   `make ci`; the branch pushed; **`make gate-ran` exits 0** from `../ta-s294`, its SHA checked against
   `git rev-parse HEAD`; the open CodeQL alerts set-diffed against the baseline of 138.
2. Merge to `main`, tag. **Post-merge CodeQL** checked on `main`.
3. **F1, at no cost, from the main checkout (the tree with `.env`), every probe refusing sockets:**
   (a) `probe_real_stops_at_graph.py` exits 2 with `unrecognized arguments: --real` and reaches no
   graph factory; (b) `probe_demo_network.py --trace --observe` reads 0 `load_dotenv` calls, 0 names
   added, 0 network attempts; (c) `live_local_runs.py` still reads 0 `local-` RunRequests. On the
   prototype tree (no `.env`) (a) and (b) gave exactly that (Closeout of the planner's prototype).
4. **No deploy.** Work-queue 144 closes at F1; there is no F2.

---

## Handover — paste this to Codex

```text
You are building Sprint 294 in the worktree ../ta-s294, on the branch
sprint-294-the-local-demonstrator-reaches-nothing-outside-its-process. Never work on main.

Read docs/sprints/sprint-294-the-local-demonstrator-reaches-nothing-outside-its-process.md, whole,
before anything else. It is the spec, and its bottom sections are your handback. Every decision is
made: Appendix B is the whole change to ten files, and you write one test file.

In order:
1. Read docs/laws/conventions.md and docs/laws/drift-register.md, and DL-329 in
   docs/design-log.md. Fill the Law reading record in the spec BEFORE any change. The law-cycle
   answer: No (tooling only, no contract, no agent guarantee).
2. Write tests/test_run_local_stays_in_process.py: the fixture doors_shut and the six tests of the
   Test plan under exactly the names given, with a module docstring that declares Agent, Role and
   External I/O. Run
     uv run --no-sync pytest tests/test_run_local_stays_in_process.py tests/test_check_module_size.py --no-cov -q -p no:cacheprovider
   on the unchanged production files and paste the output into the Closeout. Expected: 15 failed,
   12 passed.
3. Apply Appendix B: save its diff block to a file outside the repository's tracked files and run
   git apply on it. Then git hash-object on the ten files must print the ten blob ids Appendix B
   gives. Do NOT run uv lock or uv sync in any form.
4. Run the same pytest command again: 27 passed.
5. Plant the 21 breaks of Appendix C one at a time. Each must go red on the test named for it.
   Restore each with git checkout of that file before the next (commit your work first, or keep a
   copy, so the restore returns your built file).
6. Run uv run --no-sync ruff format on the test file, then make ci redirected to a file, and read
   the file. If a step cannot run in your sandbox (the dependency audit needs a network), say
   "not done" for that step and paste its lines.
7. Fill Test plan results, Closeout and Return notes; set Status to BUILT here and in this sprint's
   row of docs/sprints/README.md (the row's status cell must lead with BUILT). Commit on the branch
   if your sandbox lets you write the repository's git directory; if not, leave the tree
   uncommitted and say so.

DO NOT: run uv lock or uv sync; run scripts/run_local.py, scripts/run_lane.py or any script outside
pytest and make ci; run any az command; change any file Appendix B does not name except the test
file, this spec and docs/sprints/README.md; touch orchestration/local_pipeline.py or any existing
test; add a design-log entry; edit docs/STATE.md, docs/work-queue.md or docs/design-log.md; add
entries to .secrets.baseline; use noqa; paste a whole make ci log into the spec; measure make ci
through a pipe.

Traps: restore the whole environment in the tests (preserve_environment), because the unchanged
tree writes PROVIDER_INGEST_* names; patch dotenv.load_dotenv and dotenv.dotenv_values as module
attributes; A2 passes on both trees and goes red only under breaks B7 to B11; the size baseline
must lose run_local.py's entry; apply the diff, never retype (the docstring keeps its em dash and
arrows); ruff format is a pre-commit hook.

Two tiers of trouble. A wrong path, count or command in this spec whose intent is plain: correct
it, go on, and record it in the Return notes. A blob id that does not match after a clean git
apply, a law that contradicts the spec, an existing test that fails, or a break that stays green:
STOP and report. State anything not done as "not done" or "verified failing". Never write a Result
for work you have not done.

Handback checklist, each answered in the Closeout:
 1. Law reading record filled before the first change; the law-cycle answer with its reason.
 2. Red output of step 2 pasted (15 failed, 12 passed).
 3. The ten blob ids after git apply, as printed.
 4. Green output of step 4 pasted (27 passed).
 5. git diff --stat against the base: exactly Appendix B's ten files, the test file, this spec and
    docs/sprints/README.md.
 6. The 21 breaks, one line each: the test that went red, and restored.
 7. The line counts of scripts/run_local.py and the test file.
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
5. Set **Status:** to `BUILT`.
6. State anything not met plainly as "verified failing" or "not done" (LAW-02). **Never write a
   `Result:` for work you have not done.**

An incomplete handback is returned, not repaired (DL-48).

---

## Law reading record — fill BEFORE writing code

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| Appendix B tooling, guide and version lines; new CLI tests | `docs/laws/conventions.md` (whole); `docs/laws/drift-register.md` (whole); DL-329 (whole); DL-328 Decided D1-D7 | conventions §7 test citations and §9 drift reporting; repository module-header rule; DL-329 D1-D5 | No. Read before this record, the first edit; tooling tests cite DL-329 D1-D3 and preserve the whole environment. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** No: tooling only; no contract change and no new agent guarantee.

**Contradictions found between a law and this spec:** None. No agent law governs the demonstrator; conventions §7 applies to agent functional tests, while these tooling tests cite DL-329.

**Laws found silent where a decision was needed:** None; DL-329 already settles every tooling decision.

**Clauses that were ⬜ and are now proven:** None; no agent clause changes or is claimed green.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_a_flag_that_reached_outside_the_process_is_refused` | `tests/test_run_local_stays_in_process.py` | PASS (6 cases) | DL-329 D1 |
| A2 | `test_the_demo_reaches_nothing_outside_the_process` | `tests/test_run_local_stays_in_process.py` | PASS (4 cases) | DL-329 D2 |
| A3 | `test_the_help_offers_only_the_in_memory_demo` | `tests/test_run_local_stays_in_process.py` | PASS (1 case) | DL-329 D1 |
| A4 | `test_the_docstring_sends_a_real_run_to_the_lane` | `tests/test_run_local_stays_in_process.py` | PASS (1 case) | DL-329 D3 |
| A5 | `test_no_committed_file_points_at_a_removed_flag` | `tests/test_run_local_stays_in_process.py` | PASS (6 cases) | DL-329 D3 |
| A6 | `test_the_observability_guide_sends_a_test_run_to_the_lane` | `tests/test_run_local_stays_in_process.py` | PASS (1 case) | DL-329 D3 |

**Tests added beyond the plan:** None; exactly the six named tests, 19 parametrized cases.

---

## Closeout — evidence

**Status:** BUILT in this spec and at the start of this sprint's README status cell.

**Tree the proofs ran in (and `.env` present?):** `C:\Users\yury_\Downloads\project\ta-s294`, branch `sprint-294-the-local-demonstrator-reaches-nothing-outside-its-process`; `Test-Path .env` printed `False` before tests and after CI.

**Result:** All 19 planned cases and eight existing size-checker tests pass; all 21 Appendix C breaks failed their named test and were restored; all 16 local CI steps passed, exit 0, 100.00% coverage. The law record above was the first edit, before test or production changes. Law-cycle answer: No (tooling only, no contract change, no new agent guarantee).

**Files changed:** Exactly Appendix B's ten files, the new test, this spec and the sprint README: 13 files against base `b592b2de9f9b924a008172fc043e64a1f52b0795`.

git diff --stat against the base:

```text
 docs/observability.md                              |  13 +-
 docs/sprints/README.md                             |   2 +-
 ...nstrator-reaches-nothing-outside-its-process.md | 485 +++++++++++++++++++--
 pyproject.toml                                     |   2 +-
 scripts/accept.py                                  |   2 +-
 scripts/module_size_baseline.py                    |   1 -
 scripts/observatory.py                             |   2 +-
 scripts/run_local.py                               | 113 +----
 scripts/trace_run.py                               |   2 +-
 scripts/universe_sp100.txt                         |   2 +-
 scripts/universe_sp500.txt                         |   2 +-
 tests/test_run_local_stays_in_process.py           | 139 ++++++
 uv.lock                                            |   2 +-
 13 files changed, 622 insertions(+), 145 deletions(-)
```

**Appendix B — git hash-object output after git apply:**

```text
7bf1c92ea660890b0e3ca2f50d23b212b2413355  docs/observability.md
57aa18a088c5ab9ebbea1c6e1ab78cf3122750cd  pyproject.toml
6429ff9e0e414945637f8f6baadef6b64ec5d895  scripts/accept.py
ac0e5263bd086640592a7bd6de97710b450c2714  scripts/module_size_baseline.py
e35efc8d237d93d2f14b5c06040db5e5b482f847  scripts/observatory.py
7727f41755f485bd5788273dbdb82adb50f52899  scripts/run_local.py
5da1269cdd300c79d199371d8ddc7c54dc31a1f4  scripts/trace_run.py
c2e392c9f64b31bd8fa18197dccded642869fd33  scripts/universe_sp100.txt
65b7006e61eec096df95af39365c008deda0f01d  scripts/universe_sp500.txt
eb124802cfaf8a388b49a7536824be2c0b38e21d  uv.lock
```

**Commit evidence:** Built files and the pre-code law record committed on the required branch as `83033236aa8f800b8feb048089b795b000d4f67b`, the restoration point for every break. This completed handback is committed in a follow-up; its SHA is reported in the final reply.

**Design decisions:** recorded as [`DL-329`](../design-log.md) by the planner before the build.

**Proof — the red run first:** unchanged production files at base `b592b2de9f9b924a008172fc043e64a1f52b0795`; exit 1.

```text
FFFFFF....FFFFFFFFF........                                              [100%]
================================== FAILURES ===================================
_______ test_a_flag_that_reached_outside_the_process_is_refused[--real] _______
tests\test_run_local_stays_in_process.py:59: in test_a_flag_that_reached_outside_the_process_is_refused
    run_local.main()
scripts\run_local.py:143: in main
    load_dotenv()
tests\test_run_local_stays_in_process.py:39: in reached_outside
    raise AssertionError("the demonstrator reached outside its process")
E   AssertionError: the demonstrator reached outside its process
_______ test_a_flag_that_reached_outside_the_process_is_refused[--veto] _______
tests\test_run_local_stays_in_process.py:59: in test_a_flag_that_reached_outside_the_process_is_refused
    run_local.main()
scripts\run_local.py:190: in main
    deliberation_llm, deliberation_judge_llm = build_role_llms(True)
                                               ^^^^^^^^^^^^^^^^^^^^^
scripts\deliberate.py:158: in build_role_llms
    _load_dotenv()
scripts\deliberate.py:138: in _load_dotenv
    load_dotenv(_ROOT / ".env")
tests\test_run_local_stays_in_process.py:39: in reached_outside
    raise AssertionError("the demonstrator reached outside its process")
E   AssertionError: the demonstrator reached outside its process
---------------------------- Captured stdout call -----------------------------
MODE: demo  (in-memory + fake data)

PRE-FLIGHT
  [OK ] graph reachable          ok
  [OK ] data source configured   FakeDataSource
  [OK ] universe non-empty       2 tickers

DISPATCHER
  placed RunRequest run-request:local-1 (2 tickers)
_____ test_a_flag_that_reached_outside_the_process_is_refused[--universe] _____
tests\test_run_local_stays_in_process.py:58: in test_a_flag_that_reached_outside_the_process_is_refused
    with pytest.raises(SystemExit) as raised:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE SystemExit
---------------------------- Captured stdout call -----------------------------
MODE: demo  (in-memory + fake data)
UNIVERSE: scripts/universe_sp100.txt  (99 tickers)

PRE-FLIGHT
  [OK ] graph reachable          ok
  [OK ] data source configured   FakeDataSource
  [OK ] universe non-empty       99 tickers

DISPATCHER
  placed RunRequest run-request:local-1 (99 tickers)

CASCADE (one graph-pull pass per agent)
  position_sync      woke: processed 1
  provider           woke: processed 1
  scanner            woke: processed 1
  analyst            woke: processed 1
  provider_barrier_history idle: processed 0
  forecaster         woke: processed 1
  forecaster_settlement woke: processed 1
  portfolio_manager  woke: processed 1
  execution          woke: processed 1
  monitor            woke: processed 1
  reporter           woke: processed 1

GRAPH (provenance chain)
  RunRequest     1
  MarketData     1
  ScanRun        1
  AnalystRun     1
  PMRun          1
  ExecutionRun   1
  MonitorRun     2
  Snapshot       1
____ test_a_flag_that_reached_outside_the_process_is_refused[--chunk-size] ____
tests\test_run_local_stays_in_process.py:58: in test_a_flag_that_reached_outside_the_process_is_refused
    with pytest.raises(SystemExit) as raised:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE SystemExit
---------------------------- Captured stdout call -----------------------------
MODE: demo  (in-memory + fake data)
INGEST: chunked  size=5  delay=60.0s

PRE-FLIGHT
  [OK ] graph reachable          ok
  [OK ] data source configured   FakeDataSource
  [OK ] universe non-empty       2 tickers

DISPATCHER
  placed RunRequest run-request:local-1 (2 tickers)

CASCADE (one graph-pull pass per agent)
  position_sync      woke: processed 1
  provider           woke: processed 1
  scanner            woke: processed 1
  analyst            woke: processed 1
  provider_barrier_history idle: processed 0
  forecaster         woke: processed 1
  forecaster_settlement woke: processed 1
  portfolio_manager  woke: processed 1
  execution          woke: processed 1
  monitor            woke: processed 1
  reporter           woke: processed 1

GRAPH (provenance chain)
  RunRequest     1
  MarketData     1
  ScanRun        1
  AnalystRun     1
  PMRun          1
  ExecutionRun   1
  MonitorRun     2
  Snapshot       1
___ test_a_flag_that_reached_outside_the_process_is_refused[--chunk-delay] ____
tests\test_run_local_stays_in_process.py:58: in test_a_flag_that_reached_outside_the_process_is_refused
    with pytest.raises(SystemExit) as raised:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE SystemExit
---------------------------- Captured stdout call -----------------------------
MODE: demo  (in-memory + fake data)

PRE-FLIGHT
  [OK ] graph reachable          ok
  [OK ] data source configured   FakeDataSource
  [OK ] universe non-empty       2 tickers

DISPATCHER
  placed RunRequest run-request:local-1 (2 tickers)

CASCADE (one graph-pull pass per agent)
  position_sync      woke: processed 1
  provider           woke: processed 1
  scanner            woke: processed 1
  analyst            woke: processed 1
  provider_barrier_history idle: processed 0
  forecaster         woke: processed 1
  forecaster_settlement woke: processed 1
  portfolio_manager  woke: processed 1
  execution          woke: processed 1
  monitor            woke: processed 1
  reporter           woke: processed 1

GRAPH (provenance chain)
  RunRequest     1
  MarketData     1
  ScanRun        1
  AnalystRun     1
  PMRun          1
  ExecutionRun   1
  MonitorRun     2
  Snapshot       1
____ test_a_flag_that_reached_outside_the_process_is_refused[--ohlcv-only] ____
tests\test_run_local_stays_in_process.py:58: in test_a_flag_that_reached_outside_the_process_is_refused
    with pytest.raises(SystemExit) as raised:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
E   Failed: DID NOT RAISE SystemExit
---------------------------- Captured stdout call -----------------------------
MODE: demo  (in-memory + fake data)
INGEST: OHLCV-only fast mode (enrichment skipped, DL-29)

PRE-FLIGHT
  [OK ] graph reachable          ok
  [OK ] data source configured   FakeDataSource
  [OK ] universe non-empty       2 tickers

DISPATCHER
  placed RunRequest run-request:local-1 (2 tickers)

CASCADE (one graph-pull pass per agent)
  position_sync      woke: processed 1
  provider           woke: processed 1
  scanner            woke: processed 1
  analyst            woke: processed 1
  provider_barrier_history idle: processed 0
  forecaster         woke: processed 1
  forecaster_settlement woke: processed 1
  portfolio_manager  woke: processed 1
  execution          woke: processed 1
  monitor            woke: processed 1
  reporter           woke: processed 1

GRAPH (provenance chain)
  RunRequest     1
  MarketData     1
  ScanRun        1
  AnalystRun     1
  PMRun          1
  ExecutionRun   1
  MonitorRun     2
  Snapshot       1
________________ test_the_help_offers_only_the_in_memory_demo _________________
tests\test_run_local_stays_in_process.py:95: in test_the_help_offers_only_the_in_memory_demo
    assert set(re.findall(r"--[a-z][a-z-]*", output)) == {
E   AssertionError: assert {'--chunk-del...'--real', ...} == {'--help', '-...d', '--trace'}
E
E     Extra items in the left set:
E     '--real'
E     '--chunk-delay'
E     '--veto'
E     '--chunk-size'
E     '--universe'
E     '--ohlcv-only'
E     Use -v to get more diff
_______________ test_the_docstring_sends_a_real_run_to_the_lane _______________
tests\test_run_local_stays_in_process.py:109: in test_the_docstring_sends_a_real_run_to_the_lane
    assert "scripts/run_lane.py" in doc
E   AssertionError: assert 'scripts/run_lane.py' in 'Local end-to-end demonstrator for the graph-pull pipeline.\n\nAgent: tooling\nRole: start the system in one process —...Postgres + real market data\n  PYTHONPATH=. python scripts/run_local.py --real --universe scripts/universe_sp100.txt\n'
_____ test_no_committed_file_points_at_a_removed_flag[scripts/accept.py] ______
tests\test_run_local_stays_in_process.py:132: in test_no_committed_file_points_at_a_removed_flag
    assert f"run_local.py {argv[0]}" not in text
E   assert 'run_local.py --real' not in '"""Layer-3 ...    main()\n'
E
E     'run_local.py --real' is contained here:
E        after a `run_local.py --real` run.
E       External I/O: PostgreSQL (POSTGRES_DSN from .env); stdout; exit code.
E
E       Run it:
E         PYTHONPATH=. python scripts/accept.py --run-id <id>...
E
E     ...Full output truncated (31 lines hidden), use '-vv' to show
___ test_no_committed_file_points_at_a_removed_flag[scripts/observatory.py] ___
tests\test_run_local_stays_in_process.py:132: in test_no_committed_file_points_at_a_removed_flag
    assert f"run_local.py {argv[0]}" not in text
E   assert 'run_local.py --real' not in '"""Pipeline...    main()\n'
E
E     'run_local.py --real' is contained here:
E       se after `run_local.py --real` has written the provenance chain.
E     ?           +++++++++++++++++++
E       External I/O: PostgreSQL (POSTGRES_DSN from .env); stdout.
E
E       Run it:...
E
E     ...Full output truncated (33 lines hidden), use '-vv' to show
____ test_no_committed_file_points_at_a_removed_flag[scripts/trace_run.py] ____
tests\test_run_local_stays_in_process.py:132: in test_no_committed_file_points_at_a_removed_flag
    assert f"run_local.py {argv[0]}" not in text
E   assert 'run_local.py --real' not in '"""Post-run...    main()\n'
E
E     'run_local.py --real' is contained here:
E       se after `run_local.py --real` has written the provenance chain.
E     ?           +++++++++++++++++++
E       External I/O: PostgreSQL (POSTGRES_DSN from .env).
E
E       Run it:...
E
E     ...Full output truncated (29 lines hidden), use '-vv' to show
_ test_no_committed_file_points_at_a_removed_flag[scripts/universe_sp100.txt] _
tests\test_run_local_stays_in_process.py:132: in test_no_committed_file_points_at_a_removed_flag
    assert f"run_local.py {argv[0]}" not in text
E   AssertionError: assert 'run_local.py --real' not in '# S&P 100 l...\nWMT\nXOM\n'
E
E     'run_local.py --real' is contained here:
E       : scripts/run_local.py --real --universe scripts/universe_sp100.txt
E     ?           +++++++++++++++++++
E       # Note (DL-17): BK dropped — Alpaca's free `iex` feed had no recent BK bars
E       #       (latest 2026-05-20, ~5 weeks stale), which tainted the whole batch;
E       #       the `sip` feed (fuller coverage) is 403 on the free plan. 99 tickers....
E
E     ...Full output truncated (99 lines hidden), use '-vv' to show
_ test_no_committed_file_points_at_a_removed_flag[scripts/universe_sp500.txt] _
tests\test_run_local_stays_in_process.py:132: in test_no_committed_file_points_at_a_removed_flag
    assert f"run_local.py {argv[0]}" not in text
E   AssertionError: assert 'run_local.py --universe' not in '# S&P-500 u...nZBRA\nZTS\n'
E
E     'run_local.py --universe' is contained here:
E       . Read by run_local.py --universe.
E       A
E       AAPL
E       ABBV
E       ABNB...
E
E     ...Full output truncated (499 lines hidden), use '-vv' to show
___ test_no_committed_file_points_at_a_removed_flag[docs/observability.md] ____
tests\test_run_local_stays_in_process.py:132: in test_no_committed_file_points_at_a_removed_flag
    assert f"run_local.py {argv[0]}" not in text
E   AssertionError: assert 'run_local.py --real' not in '# Observabi...breakdown)\n'
E
E     'run_local.py --real' is contained here:
E       n scripts/run_local.py --real --observe`
E         (live Aura + Tiingo; `--observe` alone is the in-memory demo, no creds). *Validated live against the free
E         Aura (`c3ce91d0`) on 2026-06-25:* a 3-ticker run pulled 41 real Tiingo bars/name, opened 1 position
E         (`AAPL qty=34 est=$293.32`), and reported `OBSERVATORY OK - all invariants hold`.
E       - **Monitor a persisted run after the fact:** `PYTHONPATH=. python scripts/observatory.py --run-id <id>`...
E
E     ...Full output truncated (67 lines hidden), use '-vv' to show
__________ test_the_observability_guide_sends_a_test_run_to_the_lane __________
tests\test_run_local_stays_in_process.py:138: in test_the_observability_guide_sends_a_test_run_to_the_lane
    assert "scripts/run_lane.py --tickers" in text
E   AssertionError: assert 'scripts/run_lane.py --tickers' in '# Observability & Historical Data\n\n**Principle:** the system is loud *inward* and quiet *outward*. Internally it\nc...lts by agent — same metric broken out by `agent` label\n7–10. (additional panels for throughput and agent breakdown)\n'
=========================== short test summary info ===========================
FAILED tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused[--real]
FAILED tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused[--veto]
FAILED tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused[--universe]
FAILED tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused[--chunk-size]
FAILED tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused[--chunk-delay]
FAILED tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused[--ohlcv-only]
FAILED tests/test_run_local_stays_in_process.py::test_the_help_offers_only_the_in_memory_demo
FAILED tests/test_run_local_stays_in_process.py::test_the_docstring_sends_a_real_run_to_the_lane
FAILED tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag[scripts/accept.py]
FAILED tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag[scripts/observatory.py]
FAILED tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag[scripts/trace_run.py]
FAILED tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag[scripts/universe_sp100.txt]
FAILED tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag[scripts/universe_sp500.txt]
FAILED tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag[docs/observability.md]
FAILED tests/test_run_local_stays_in_process.py::test_the_observability_guide_sends_a_test_run_to_the_lane
15 failed, 12 passed in 6.69s
```

**Proof — the green run:** same command as step 2; exit 0.

```text
...........................                                              [100%]
27 passed in 3.56s
```

**Guards planted:** 21 of 21 red on the named test; every restoration verified against the committed blob.

```text
B1: tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused — exit 1; 1 failed, 5 passed in 5.44s; restored with git checkout (blob verified)
B2: tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused — exit 1; 1 failed, 5 passed in 5.54s; restored with git checkout (blob verified)
B3: tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused — exit 1; 1 failed, 5 passed in 5.43s; restored with git checkout (blob verified)
B4: tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused — exit 1; 1 failed, 5 passed in 5.35s; restored with git checkout (blob verified)
B5: tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused — exit 1; 1 failed, 5 passed in 5.26s; restored with git checkout (blob verified)
B6: tests/test_run_local_stays_in_process.py::test_a_flag_that_reached_outside_the_process_is_refused — exit 1; 1 failed, 5 passed in 5.30s; restored with git checkout (blob verified)
B7: tests/test_run_local_stays_in_process.py::test_the_demo_reaches_nothing_outside_the_process — exit 1; 4 failed in 5.68s; restored with git checkout (blob verified)
B8: tests/test_run_local_stays_in_process.py::test_the_demo_reaches_nothing_outside_the_process — exit 1; 4 failed in 5.43s; restored with git checkout (blob verified)
B9: tests/test_run_local_stays_in_process.py::test_the_demo_reaches_nothing_outside_the_process — exit 1; 4 failed in 6.07s; restored with git checkout (blob verified)
B10: tests/test_run_local_stays_in_process.py::test_the_demo_reaches_nothing_outside_the_process — exit 1; 4 failed in 5.75s; restored with git checkout (blob verified)
B11: tests/test_run_local_stays_in_process.py::test_the_demo_reaches_nothing_outside_the_process — exit 1; 4 failed in 7.76s; restored with git checkout (blob verified)
B12: tests/test_run_local_stays_in_process.py::test_the_docstring_sends_a_real_run_to_the_lane — exit 1; 1 failed in 5.52s; restored with git checkout (blob verified)
B13: tests/test_run_local_stays_in_process.py::test_the_docstring_sends_a_real_run_to_the_lane — exit 1; 1 failed in 15.49s; restored with git checkout (blob verified)
B14: tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag — exit 1; 1 failed, 5 passed in 8.80s; restored with git checkout (blob verified)
B15: tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag — exit 1; 1 failed, 5 passed in 5.28s; restored with git checkout (blob verified)
B16: tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag — exit 1; 1 failed, 5 passed in 6.92s; restored with git checkout (blob verified)
B17: tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag — exit 1; 1 failed, 5 passed in 5.70s; restored with git checkout (blob verified)
B18: tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag — exit 1; 1 failed, 5 passed in 5.57s; restored with git checkout (blob verified)
B19: tests/test_run_local_stays_in_process.py::test_no_committed_file_points_at_a_removed_flag — exit 1; 1 failed, 5 passed in 5.58s; restored with git checkout (blob verified)
B20: tests/test_run_local_stays_in_process.py::test_the_observability_guide_sends_a_test_run_to_the_lane — exit 1; 1 failed in 5.30s; restored with git checkout (blob verified)
B21: tests/test_check_module_size.py::test_every_baselined_path_is_over_the_block_today — exit 1; 1 failed in 1.59s; restored with git checkout (blob verified)
```

**Module line counts:** `scripts/run_local.py` 138; `tests/test_run_local_stays_in_process.py` 139 (`Get-Content` line counts). All touched Python modules passed the size gate.

**`make ci`:** `make ci > "$env:TEMP\s294-make-ci.txt" 2>&1`; `UV_NO_SYNC=1`, `PYTHONUTF8=1`. Log: `C:\Users\yury_\AppData\Local\Temp\s294-make-ci.txt`; exit code **0**, captured immediately from `$LASTEXITCODE` in `s294-make-ci-exit.txt`. The file was read after completion. Counted 16 recipes from the Makefile; every recipe completed successfully (the gate stops at a failing recipe). No local CI step is not done. Verdict lines derived from completion:

```text
PASS step 1: uv run ruff check . --output-format=github (exit 0)
PASS step 2: uv run ruff format --check . (exit 0)
PASS step 3: uv run mypy kernel contracts agents orchestration surfaces (exit 0)
PASS step 4: uv run lint-imports (exit 0)
PASS step 5: uv run python scripts/check_module_size.py kernel contracts agents orchestration surfaces tests scripts (exit 0)
PASS step 6: uv run python scripts/check_module_header.py kernel contracts agents orchestration surfaces scripts (exit 0)
PASS step 7: uv run python scripts/check_law_coverage.py (exit 0)
PASS step 8: uv run python scripts/check_param_law_sync.py (exit 0)
PASS step 9: uv run python scripts/check_sprint_status.py (exit 0)
PASS step 10: uv run python scripts/check_tracker_size.py (exit 0)
PASS step 11: uv run python scripts/check_markdown_links.py (exit 0)
PASS step 12: uv run python scripts/check_version_scheme.py (exit 0)
PASS step 13: uv run pytest (exit 0)
PASS step 14: uv run python scripts/check_dependency_audit.py (exit 0)
PASS step 15: uv run pre-commit run detect-secrets --all-files (exit 0)
PASS step 16: uv run python scripts/check_untracked_secrets.py (exit 0)
```

Copied verdict, totals, warning and skip lines from the log (the complete log remains outside the repository):

```text
1862 files already formatted
Success: no issues found in 1311 source files
Contracts: 5 kept, 0 broken.
[WARN] portfolio_manager.max_position_pct declared_default=0.10 envelope=(0.01, 0.05) source=FCA COLL 5.2 — UCITS investment powers and limits
[WARN] portfolio_manager.max_positions declared_default=10 envelope=(30.0, 60.0) source=Evans and Archer, forty years later
docs_seen=300 SPEC=11 BUILT=0 MERGED=289 UNMAPPED=0 MISSING=0
TOTAL                                                           22224      0   4760      0  100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
SKIPPED [1] tests\test_bus_azure_config.py:21: Service Bus dotenv isolation proof requires local .env
SKIPPED [1] tests\test_bus_celery.py:181: CELERY_BROKER_URL is not set
SKIPPED [1] tests\test_deliberator_servicebus_peer.py:36: A1 proof requires .env present; CI has no local secrets file
SKIPPED [1] tests\test_gate_selftest_leaves_nothing.py:57: a link needs a privilege here
SKIPPED [1] tests\test_graph_postgres.py:137: POSTGRES_TEST_DSN is not set
SKIPPED [1] tests\test_graph_postgres_keys.py:90: POSTGRES_TEST_DSN is not set
SKIPPED [1] agents\forecaster\tests\test_barrier_garch_oracle.py:179: could not import 'scipy.signal': No module named 'scipy'
SKIPPED [1] agents\provider\tests\test_sources.py:159: FINNHUB_TEST_NETWORK=1 is not set
SKIPPED [1] agents\provider\tests\test_stooq.py:66: STOOQ_TEST_NETWORK=1 is not set
========= 5441 passed, 9 skipped, 2470 warnings in 575.91s (0:09:35) ==========
No unaccepted vulnerabilities; 1 accepted advisory re-checked
Detect secrets...........................................................Passed
detect-secrets (untracked): no untracked files to scan
```

**`make gate-ran`:** not done; the planner's, after the push (Sequencing step 1).

**Not met / verified failing:** No required local CI step is not done or verified failing. Nine full-suite cases were skipped for their printed reasons in the CI excerpt above. Planner-owned push, remote gates, independent re-measurement, merge/tag, CodeQL comparison and F1 are not done. No deploy is owed.

---

## Planner review and F1 — 2026-11-28

**Review of the handback (`054d1141`, built by Codex).** The ten production blobs equal Appendix B's;
the diff touches exactly those ten paths, the new test, this spec and the sprint README; no
`.secrets.baseline` entry. The planner's test in place of the builder's, with the size checker's
tests: 27 passed. The 21 breaks of Appendix C against the builder's test: 21 of 21 red, the tree
clean after (kit `wq144-2026-11-28/breaks_builder_054d1141.txt`). The builder's own `make ci` log,
read: exit 0, the dependency audit `No unaccepted vulnerabilities; 1 accepted advisory re-checked`
(its sandbox reached the network this time), 5,441 passed, 9 skipped, 100.00 %. The remote gate:
**GATE PROVEN `054d1141`** (CI, CodeQL, Security Findings, attempt 1), run from `../ta-s294` with
that `HEAD`. CodeQL on the branch: 138 open alerts, the same rule-and-path set as the S293 baseline,
0 errors (kit `codeql_open_sprint294.txt`, the new baseline). `main` fast-forwarded to `054d1141`,
tag `v0.132.01`.

**F1 (the planner's, main checkout with `.env`, each probe refusing every socket lookup and connect,
05:24 UTC; kit `wq144-2026-11-28/f1*_main_054d1141.txt`).**

1. `probe_real_stops_at_graph.py`: `run_local.py: error: unrecognized arguments: --real`, exit 2;
   the graph factory is never reached (before the merge it was reached once, with `.env`'s
   `POSTGRES_DSN`, kit `probe_real.txt`).
2. `probe_demo_network.py --trace --observe`: 0 `load_dotenv` calls, 0 names added
   (`POSTGRES_DSN` not in the environment), 0 network attempts; RunRequest 1, Snapshot 1; exit 0.
3. `live_local_runs.py .env`: the live graph's 122 RunRequests, 0 with a `local-` key, byte-identical
   to the reading taken before the build (kit `live_local_runs.txt`).

Nothing to tear down. Work-queue 144 closed. No deploy (DL-329 D5).

---

## Return notes

- No path, count or command correction was needed. The independently written test file is 139 lines (the prototype's 147 was descriptive).
- All ten Appendix B blobs matched after clean `git apply`; all 21 breaks went red on their named tests and were restored by `git checkout` with blob verification.
- `UV_NO_SYNC=1` was inherited by Makefile and hook commands. No `uv lock` or `uv sync` was run; the lock changed only through Appendix B.
- The first build commit attempt was stopped by the trailing-whitespace hook trimming pasted pytest diagnostic whitespace in this spec. The retry passed all applicable hooks; the raw red log remains outside the repository.
- The law record was the first edit; no design log, law book, baseline for secrets, state tracker, existing test or orchestration module was edited.
- Planner-owned work is not done: push, remote `make gate-ran`, independent re-measurement, merge/tag, CodeQL comparison and F1. No deploy is owed (D5).

---

## Closeout of the planner's prototype — measured 2026-11-28

Tree: `../ta-s294-proto`, branch `proto-s294` (never pushed), no `.env`. Commits: `60d5fe34` (the
planner's test file alone, on `main` `5ad74085`), `9ac674a2` (Appendix B). Kit OneDrive
`wq144-2026-11-28/`.

```text
red, on 60d5fe34 (the production files unchanged):
  uv run --no-sync pytest tests/test_run_local_stays_in_process.py tests/test_check_module_size.py --no-cov -q -p no:cacheprovider
  15 failed, 12 passed (A1 x6, A3, A4, A5 x6, A6 failed; A2 x4 and the size checker's 8 tests passed)
green, on 9ac674a2 (Appendix B applied): the same command, 27 passed
make ci, on 9ac674a2, redirected to proto_make_ci.txt: make ci exit 0
  5441 passed, 9 skipped; Required test coverage of 100.0% reached. Total coverage: 100.00%
  dependency audit: No unaccepted vulnerabilities; 1 accepted advisory re-checked
  detect-secrets: Passed; untracked: no untracked files to scan
breaks, s294_breaks.py against the planner's test file: breaks red: 21 of 21; tree after: clean
B21 on the gate's own size step (check_module_size.py with the Makefile's scope): exit 1
  [FAIL] scripts/run_local.py: 138 lines is under the block - delete its entry from scripts/module_size_baseline.py so it cannot grow back.
F1 (a) on the prototype tree: probe_real_stops_at_graph.py
  run_local.py: error: unrecognized arguments: --real ; exit 2
F1 (b) on the prototype tree: probe_demo_network.py --trace --observe
  load_dotenv calls: 0 ; env names added: 0 ; network attempts: 0 ; exit 0
line counts: scripts/run_local.py 138, tests/test_run_local_stays_in_process.py 147
```

## Appendix B — the change, measured on the planner's prototype

Save the block below to a file and run `git apply <file>` from the worktree's root. It changes
`scripts/run_local.py`, the three sibling scripts' docstrings, the size baseline, the two universe
files' comment lines, `docs/observability.md`, and one line each of `pyproject.toml` and `uv.lock`.
The test file is yours to write (Test plan).

After it, `git hash-object` on each file prints:

```text
7bf1c92ea660890b0e3ca2f50d23b212b2413355  docs/observability.md
57aa18a088c5ab9ebbea1c6e1ab78cf3122750cd  pyproject.toml
6429ff9e0e414945637f8f6baadef6b64ec5d895  scripts/accept.py
ac0e5263bd086640592a7bd6de97710b450c2714  scripts/module_size_baseline.py
e35efc8d237d93d2f14b5c06040db5e5b482f847  scripts/observatory.py
7727f41755f485bd5788273dbdb82adb50f52899  scripts/run_local.py
5da1269cdd300c79d199371d8ddc7c54dc31a1f4  scripts/trace_run.py
c2e392c9f64b31bd8fa18197dccded642869fd33  scripts/universe_sp100.txt
65b7006e61eec096df95af39365c008deda0f01d  scripts/universe_sp500.txt
eb124802cfaf8a388b49a7536824be2c0b38e21d  uv.lock
```

```diff
diff --git a/docs/observability.md b/docs/observability.md
index 57bd6790..7bf1c92e 100644
--- a/docs/observability.md
+++ b/docs/observability.md
@@ -49,12 +49,13 @@ floor/ceiling/required invariants flagged — use the **pipeline observatory** (
 substrate + `orchestration/packs/trading_observatory.py` trading pack; DL-27). It applies the deliberation
 firewall pattern (baseline + floor/ceiling) to the data pipeline.

-- **Run a test + monitor it in one command:** `PYTHONPATH=. python scripts/run_local.py --real --observe`
-  (live Aura + Tiingo; `--observe` alone is the in-memory demo, no creds). *Validated live against the free
-  Aura (`c3ce91d0`) on 2026-06-25:* a 3-ticker run pulled 41 real Tiingo bars/name, opened 1 position
-  (`AAPL qty=34 est=$293.32`), and reported `OBSERVATORY OK - all invariants hold`.
-- **Monitor a persisted run after the fact:** `PYTHONPATH=. python scripts/observatory.py --run-id <id>`
-  (reads the run back from Neo4j).
+- **Run a test on real data:** `python scripts/run_lane.py --tickers AAPL,MSFT` with the main checkout's
+  venv, from the main checkout: the test lane (DL-328), on the test paper account and a graph of its own.
+  It prints each round and the fleet's acceptance verdict, and refuses a start from 22:00 to 24:00 UTC.
+- **See the observatory with no credentials:** `PYTHONPATH=. python scripts/run_local.py --observe` runs
+  the in-memory demo on fake data, with no network, and prints it (DL-329).
+- **Monitor a persisted fleet run after the fact:** `PYTHONPATH=. python scripts/observatory.py --run-id <id>`
+  (reads the run back from the graph `POSTGRES_DSN` names: the live one, from the main checkout).

 It prints the full `provider → reporter` spine, each stage as `[stage]  <- (trigger)` with its output
 artifacts, and flags:
diff --git a/pyproject.toml b/pyproject.toml
index 2135baf4..57aa18a0 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -1,6 +1,6 @@
 [project]
 name = "trading-agents"
-version = "0.132.00"
+version = "0.132.01"
 description = "An operator-controlled, single-user, agent-based trading system. Domain logic lives only in agents; the kernel is plumbing; contracts are the shared boundary."
 requires-python = ">=3.13"
 dependencies = [
diff --git a/scripts/accept.py b/scripts/accept.py
index e9e53ef2..6429ff9e 100644
--- a/scripts/accept.py
+++ b/scripts/accept.py
@@ -4,7 +4,7 @@ Agent: tooling
 Role: load the graph store from .env and run the acceptance gate for a given
       run_id — every per-stage invariant + the cross-stage conservation
       boundaries. Exits non-zero on FAIL, so it can gate a deploy.
-      Use after a `run_local.py --real` run.
+      Use on a fleet run (`--run-id sched-YYYY-MM-DD`); the test lane prints its own.
 External I/O: PostgreSQL (POSTGRES_DSN from .env); stdout; exit code.

 Run it:
diff --git a/scripts/module_size_baseline.py b/scripts/module_size_baseline.py
index 548137e4..ac0e5263 100644
--- a/scripts/module_size_baseline.py
+++ b/scripts/module_size_baseline.py
@@ -28,7 +28,6 @@ LEGACY_MAX_LINES: dict[str, int] = {
     "scripts/deliberation_replay_batch.py": 240,
     "scripts/evaluate_return_model.py": 288,
     "scripts/gate_selftest_cases.py": 346,
-    "scripts/run_local.py": 227,
     "scripts/sb_sas_plan.py": 212,
     "scripts/servicebus_request.py": 216,
     "scripts/vocabulary_resolution.py": 268,
diff --git a/scripts/observatory.py b/scripts/observatory.py
index 4eabe1a5..e35efc8d 100644
--- a/scripts/observatory.py
+++ b/scripts/observatory.py
@@ -3,7 +3,7 @@
 Agent: tooling
 Role: load the graph store from .env and print the observatory for a given run_id —
       per-stage I/O plus floor/ceiling/required WARNs against the locked trading
-      baseline. Use after `run_local.py --real` has written the provenance chain.
+      baseline. Use on a fleet run (`--run-id sched-YYYY-MM-DD`).
 External I/O: PostgreSQL (POSTGRES_DSN from .env); stdout.

 Run it:
diff --git a/scripts/run_local.py b/scripts/run_local.py
index 401a983e..7727f417 100644
--- a/scripts/run_local.py
+++ b/scripts/run_local.py
@@ -5,35 +5,31 @@ Role: start the system in one process — pre-flight checks, the dispatcher plac
       RunRequest, then run each agent's graph-pull poll once and print how every
       downstream agent wakes off its prerequisite gate
       (provider → scanner → analyst → PM → execution → monitor → reporter).
-      --real: loads .env, uses PostgreSQL (POSTGRES_DSN) + real Tiingo OHLCV data.
-      --universe FILE: newline-delimited tickers; overrides the built-in list.
-      Default: in-memory graph + FakeDataSource (no credentials needed).
-External I/O: stdout; network (Tiingo, Finnhub, PostgreSQL) when --real.
+      In-memory graph + FakeDataSource only; no flag reaches further (DL-329).
+      A run on real data is the test lane's: `scripts/run_lane.py` (DL-328).
+External I/O: stdout. No network, no database, no model call; the agents' settings
+      read a `.env` in the working directory, as every agent's do.

 Run it:
-  PYTHONPATH=. python scripts/run_local.py           # in-memory demo
-  PYTHONPATH=. python scripts/run_local.py --real    # live Postgres + real market data
-  PYTHONPATH=. python scripts/run_local.py --real --universe scripts/universe_sp100.txt
+  PYTHONPATH=. python scripts/run_local.py                     # the cascade
+  PYTHONPATH=. python scripts/run_local.py --trace --observe   # + trace, observatory
 """

 from __future__ import annotations

 import argparse
-import os
 from datetime import UTC, datetime, timedelta

 from agents.execution.paper_broker import PaperBroker
 from agents.provider import ProviderAgent
 from agents.provider.settings import ProviderSettings
 from agents.provider.sources import FakeDataSource
-from agents.scanner.universe import load_universe_file
 from contracts.provider import OHLCVBar
 from kernel import InMemoryGraphStore, InProcessBus
 from orchestration.local_pipeline import cascade_once
 from orchestration.start import all_passed, place_run_request, preflight

 _TICKERS_DEMO: tuple[str, ...] = ("AAPL", "MSFT")
-_TICKERS_REAL: tuple[str, ...] = ("AAPL", "MSFT", "GOOGL")
 _CHAIN = (
     "RunRequest",
     "MarketData",
@@ -73,11 +69,6 @@ def _fake_source() -> FakeDataSource:
 def main() -> None:
     """Start the system once and print the graph-pull cascade."""
     parser = argparse.ArgumentParser(description="graph-pull pipeline demonstrator")
-    parser.add_argument(
-        "--real",
-        action="store_true",
-        help="use live PostgreSQL (POSTGRES_DSN from .env) + real Tiingo market data",
-    )
     parser.add_argument(
         "--trace",
         action="store_true",
@@ -88,79 +79,19 @@ def main() -> None:
         action="store_true",
         help="print the pipeline observatory (stage outputs + floor/ceiling WARNs)",
     )
-    parser.add_argument(
-        "--universe",
-        metavar="FILE",
-        help="newline-delimited ticker file; overrides the built-in universe",
-    )
     parser.add_argument(
         "--run-id",
         default="local-1",
         metavar="ID",
         help="RunRequest id (use a fresh id per run; the graph is append-only)",
     )
-    parser.add_argument(
-        "--chunk-size",
-        type=int,
-        default=0,
-        metavar="N",
-        help="paced ingest sub-batch size (0 = single-shot); respects API rate limits",
-    )
-    parser.add_argument(
-        "--chunk-delay",
-        type=float,
-        default=60.0,
-        metavar="SECONDS",
-        help="pause between ingest chunks (with --chunk-size)",
-    )
-    parser.add_argument(
-        "--ohlcv-only",
-        action="store_true",
-        help="fast mode (DL-29): request only OHLCV; skip per-ticker Finnhub "
-        "enrichment the acceptance gate doesn't need (~33 min -> seconds at S&P-500)",
-    )
-    parser.add_argument(
-        "--veto",
-        action="store_true",
-        help="DL-31 Part B: run the LLM challenger-veto between PM and execution "
-        "(real model per .env); persists a DeliberationRun with the debate transcript",
-    )
     args = parser.parse_args()

-    if args.chunk_size:
-        os.environ["PROVIDER_INGEST_CHUNK_SIZE"] = str(args.chunk_size)
-        os.environ["PROVIDER_INGEST_CHUNK_DELAY_SECONDS"] = str(args.chunk_delay)
-
-    if args.ohlcv_only:
-        os.environ["PROVIDER_INGEST_OHLCV_ONLY"] = "true"
-
-    if args.real:
-        from dotenv import load_dotenv
-
-        from agents.provider.composite import market_source_from_settings
-        from kernel.graph_env import build_graph_from_env
-
-        load_dotenv()
-        graph = build_graph_from_env()
-        settings = ProviderSettings()
-        source = market_source_from_settings(settings)
-        tickers = _TICKERS_REAL
-        print("MODE: real  (Postgres + Tiingo/Finnhub)")
-    else:
-        graph = InMemoryGraphStore()
-        settings = ProviderSettings(max_staleness_days=7)
-        source = _fake_source()
-        tickers = _TICKERS_DEMO
-        print("MODE: demo  (in-memory + fake data)")
-
-    if args.universe:
-        tickers = load_universe_file(args.universe)
-        print(f"UNIVERSE: {args.universe}  ({len(tickers)} tickers)")
-
-    if args.chunk_size:
-        print(f"INGEST: chunked  size={args.chunk_size}  delay={args.chunk_delay}s")
-    if args.ohlcv_only:
-        print("INGEST: OHLCV-only fast mode (enrichment skipped, DL-29)")
+    graph = InMemoryGraphStore()
+    settings = ProviderSettings(max_staleness_days=7)
+    source = _fake_source()
+    tickers = _TICKERS_DEMO
+    print("MODE: demo  (in-memory + fake data)")

     agent = ProviderAgent(
         InProcessBus(),
@@ -182,22 +113,8 @@ def main() -> None:
     place_run_request(graph, run_id=args.run_id, tickers=tickers)
     print(f"  placed RunRequest run-request:{args.run_id} ({len(tickers)} tickers)")

-    deliberation_llm = None
-    deliberation_judge_llm = None
-    if args.veto:
-        from scripts.deliberate import build_role_llms
-
-        deliberation_llm, deliberation_judge_llm = build_role_llms(True)
-        print("VETO: LLM challenger-veto active between PM and execution (DL-31)")
-
     print("\nCASCADE (one graph-pull pass per agent)")
-    for result in cascade_once(
-        graph,
-        provider_agent=agent,
-        broker=PaperBroker(),
-        deliberation_llm=deliberation_llm,
-        deliberation_judge_llm=deliberation_judge_llm,
-    ):
+    for result in cascade_once(graph, provider_agent=agent, broker=PaperBroker()):
         woke = "woke" if result.processed else "idle"
         print(f"  {result.name:<18} {woke}: processed {result.processed}")

@@ -205,12 +122,6 @@ def main() -> None:
     for label in _CHAIN:
         print(f"  {label:<14} {len(graph.list_nodes(label))}")

-    if args.veto:
-        for delib in graph.list_nodes("DeliberationRun"):
-            print("\nDELIBERATION (persisted on the graph)")
-            print(f"  verdicts: {dict(delib.props['verdicts'])}")
-            print(f"  vetoed:   {list(delib.props['vetoed_tickers'])}")
-
     if args.trace:
         from orchestration.batch_trace import print_trace

diff --git a/scripts/trace_run.py b/scripts/trace_run.py
index fa5961bb..5da1269c 100644
--- a/scripts/trace_run.py
+++ b/scripts/trace_run.py
@@ -2,7 +2,7 @@

 Agent: tooling
 Role: load the graph store from .env and print the batch trace for a given run_id.
-      Intended for use after `run_local.py --real` has written the provenance chain.
+      Use on a fleet run (`--run-id sched-YYYY-MM-DD`).
 External I/O: PostgreSQL (POSTGRES_DSN from .env).

 Run it:
diff --git a/scripts/universe_sp100.txt b/scripts/universe_sp100.txt
index 9868b85f..c2e392c9 100644
--- a/scripts/universe_sp100.txt
+++ b/scripts/universe_sp100.txt
@@ -1,6 +1,6 @@
 # S&P 100 large-cap universe — liquid US tickers for populate/load runs.
 # Format: one ticker per line; blank lines and #-comments ignored.
-# Used by: scripts/run_local.py --real --universe scripts/universe_sp100.txt
+# Used by: the `sp500` universe (agents/scanner/universe.py): the dispatcher, scripts/run_lane.py.
 # Note (DL-17): BK dropped — Alpaca's free `iex` feed had no recent BK bars
 #       (latest 2026-05-20, ~5 weeks stale), which tainted the whole batch;
 #       the `sip` feed (fuller coverage) is 403 on the free plan. 99 tickers.
diff --git a/scripts/universe_sp500.txt b/scripts/universe_sp500.txt
index 266ec3b9..65b7006e 100644
--- a/scripts/universe_sp500.txt
+++ b/scripts/universe_sp500.txt
@@ -1,6 +1,6 @@
 # S&P-500 universe (503 tickers, incl. dual share classes).
 # Source: datasets/s-and-p-500-companies (GitHub), fetched 2026-06-25.
-# Refresh: re-fetch the same CSV. Read by run_local.py --universe.
+# Refresh: re-fetch the same CSV. No code reads it since DL-329 removed its one reader.
 A
 AAPL
 ABBV
diff --git a/uv.lock b/uv.lock
index 3f8acc11..eb124802 100644
--- a/uv.lock
+++ b/uv.lock
@@ -3669,7 +3669,7 @@ wheels = [

 [[package]]
 name = "trading-agents"
-version = "0.132.0"
+version = "0.132.1"
 source = { virtual = "." }
 dependencies = [
     { name = "cryptography" },
```

## Appendix C — the 21 breaks, as exact replacements

Each break replaces the one occurrence of **Old** with **New** in the file named, on the built tree.
`TRACE` is the two lines `    parser.add_argument(` and `        "--trace",` (the first option the
parser adds); a row that says *above* inserts its line before **Old** at the same indent and keeps
**Old**. Run them against `tests/test_run_local_stays_in_process.py` and
`tests/test_check_module_size.py`.

| # | File | Old | New | Must go red |
| --- | --- | --- | --- | --- |
| B1 | `scripts/run_local.py` | `TRACE` | above: `parser.add_argument("--real", action="store_true")` | A1 |
| B2 | the same | `TRACE` | above: `parser.add_argument("--veto", action="store_true")` | A1 |
| B3 | the same | `TRACE` | above: `parser.add_argument("--universe", metavar="FILE")` | A1 |
| B4 | the same | `TRACE` | above: `parser.add_argument("--chunk-size", type=int, default=0)` | A1 |
| B5 | the same | `TRACE` | above: `parser.add_argument("--chunk-delay", type=float, default=60.0)` | A1 |
| B6 | the same | `TRACE` | above: `parser.add_argument("--ohlcv-only", action="store_true")` | A1 |
| B7 | the same | the line `graph = InMemoryGraphStore()` | `from kernel.graph_env import build_graph_from_env`, a blank line, `graph = build_graph_from_env()` | A2 |
| B8 | the same | the line `args = parser.parse_args()` | that line, then `from dotenv import load_dotenv`, a blank line, `load_dotenv()` | A2 |
| B9 | the same | the line `graph = InMemoryGraphStore()` | above: `__import__("os").environ["PROVIDER_INGEST_OHLCV_ONLY"] = "true"` | A2 |
| B10 | the same | the line `for result in cascade_once(graph, provider_agent=agent, broker=PaperBroker()):` | above: `from scripts.deliberate import build_role_llms`, a blank line, `build_role_llms(True)` | A2 |
| B11 | the same | the line `print("MODE: demo  (in-memory + fake data)")` | above: `__import__("socket").getaddrinfo("api.tiingo.com", 443)` | A2 |
| B12 | the same | `` `scripts/run_lane.py` (DL-328) `` | `` `scripts/run_local.py --real` (DL-328) `` | A4 |
| B13 | the same | `No network, no database, no model call` | `PostgreSQL when asked` | A4 |
| B14 | `scripts/accept.py` | the line ``Use on a fleet run (`--run-id sched-YYYY-MM-DD`); the test lane prints its own.`` | ``Use after a `run_local.py --real` run.`` | A5 |
| B15 | `scripts/observatory.py` | the line ``baseline. Use on a fleet run (`--run-id sched-YYYY-MM-DD`).`` | ``baseline. Use after `run_local.py --real` has written the provenance chain.`` | A5 |
| B16 | `scripts/trace_run.py` | the line ``Use on a fleet run (`--run-id sched-YYYY-MM-DD`).`` | ``Intended for use after `run_local.py --real` has written the provenance chain.`` | A5 |
| B17 | `scripts/universe_sp100.txt` | the line ``# Used by: the `sp500` universe (agents/scanner/universe.py): the dispatcher, scripts/run_lane.py.`` | `# Used by: scripts/run_local.py --real --universe scripts/universe_sp100.txt` | A5 |
| B18 | `scripts/universe_sp500.txt` | the line `# Refresh: re-fetch the same CSV. No code reads it since DL-329 removed its one reader.` | `# Refresh: re-fetch the same CSV. Read by run_local.py --universe.` | A5 |
| B19 | `docs/observability.md` | `` `python scripts/run_lane.py --tickers AAPL,MSFT` `` | `` `PYTHONPATH=. python scripts/run_local.py --real --observe` `` | A5 |
| B20 | the same | `` `PYTHONPATH=. python scripts/run_local.py --observe` `` | `` `PYTHONPATH=. python scripts/observatory.py` `` | A6 |
| B21 | `scripts/module_size_baseline.py` | the line `"scripts/gate_selftest_cases.py": 346,` | that line, then `"scripts/run_local.py": 227,` | the existing `test_every_baselined_path_is_over_the_block_today` in `tests/test_check_module_size.py` |

On the prototype: 21 planted, 21 red, each on the test named, the tree clean after (`s294_breaks.py`, kit OneDrive `wq144-2026-11-28/`). B1 to B6 also turn A3 red, and B19 turns A6 red, which is expected. With B21 planted the gate's own size step fails as well (exit 1, `[FAIL] scripts/run_local.py: 138 lines is under the block - delete its entry from scripts/module_size_baseline.py so it cannot grow back.`).
