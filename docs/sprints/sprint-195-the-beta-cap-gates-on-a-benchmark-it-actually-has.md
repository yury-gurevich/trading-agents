<!-- Agent: planning | Role: sprint record — make the scanner's beta cap evaluable in the fleet -->
# Sprint 195 — the beta cap gates on a benchmark it actually has

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-195-the-beta-cap-has-never-fired`
**Status:** MERGED
**Version:** next available PATCH at merge — `0.94.08`, plus `0.94.09` for the image fix below
**Effort:** S
**Decisions:** [`DL-151`](../design-log.md) — where the benchmark ticker is owned, and the two
routes rejected to get it to the provider.

---

## Goal

The scanner's `max_beta` gate evaluates on every deployed run, or says plainly that it did not.

## Why (context)

### Measured, 2026-09-04 — read these before designing

- **The beta cap has never fired in the fleet.** Across **59 stored `ScanRun` nodes**, `max_beta`
  was evaluated **0 times** and recorded in `skipped_filters` **112 times**. Not a regression — it
  has never once gated. (Denominator: runs whose `candidate_set` carries the per-candidate
  `skipped_filters` field, which arrived with S183.)
- **The cause is an empty benchmark series, not missing code.** `compute_beta`
  (`agents/scanner/domain/beta.py:20`) is implemented and wired
  (`agents/scanner/domain/filters.py:111`). The persisted snapshot for `sched-2026-09-03` carries
  `benchmark = ()`, because `MARKET_FIELDS` (`agents/provider/ingest.py:30`) never requested the
  field, so `market_fields.py:93` left it as `empty_bars`.
- **The fleet scanner has no second route to it.** `agents/scanner/poll.py:44-50` validates the
  stored snapshot and passes `market.benchmark` straight into `apply_filters`. Empty in, no beta
  out. The in-process path (`agents/scanner/agent.py:95` → `request_benchmark_bars`) fetches the
  series itself, which is why every unit test and every local run is green while production never
  gates.
- **The data was always available.** Probed live through the real `CompositeDataSource` on
  2026-09-04: `SPY: 143 bars`, the same window as the candidates. Nobody asked for it.
- **It cost three nights of trading.** `sched-2026-09-01`, `-02` and `-03` each approved 2 orders
  and submitted 0. The deliberator vetoed both names all three nights with byte-identical verdicts
  `{'AMD': 'revise', 'USB': 'revise'}`, reasoning — correctly — that `max_beta` was *skipped, not
  passed*, so gap and beta risk were uncertified. AMD's real beta over that window is **3.2877**
  against a `max_beta` of **2.5**: with a benchmark it would have been dropped at the scanner and
  never reached the PM at all.

## Scope — and what is deliberately NOT here

In scope: the benchmark series reaches the persisted snapshot the graph-pull scanner reads.

### Out of scope (do NOT build this sprint)

- The `earnings_window` half of the same veto. It is **not** a data defect: the provider's
  `earnings_lookahead_days = 30` against the scanner's `earnings_exclusion_days = 5` means absence
  from the earnings map *proves* no earnings inside the exclusion window. The filter records SKIP
  where it could record PASS with certainty. Filed separately — a labelling change to
  `evaluate_filters`, not a fetch change, and it must not ride along with a contract change.
- Re-tuning `max_beta` itself. The cap has never run; tuning a gate before observing it once is
  guesswork. That is a `tuner` job after the first deployed run that evaluates it.
- Backfilling beta onto the 59 historical `ScanRun` nodes. They are append-only facts and were
  honestly recorded as skipped.

### The road not taken (LAW-06)

- **Let the scanner fetch its own benchmark in the poll path** (mirror `agent.py:95`). Rejected: the
  poll path exists precisely so "the provider container need not be alive" (DL-08, stated in
  `agents/scanner/poll.py`'s own header). Giving the scanner a live provider RPC — or its own data
  credential — would trade a measurable gate for a structural regression.
- **Give the provider its own `benchmark_ticker` setting.** Rejected: two agents would then declare
  the same value independently, which is exactly the PARAM divergence class work-queue item 33
  already tracks. The scanner owns the cap, so it owns the cap's denominator.

## The design decisions this sprint has to make

1. **Who owns the benchmark ticker?** The scanner — it is the denominator of *its* gate.
2. **How does the provider learn it without importing another agent?** Agents are islands
   (import-linter), so it cannot read `ScannerSettings`. It arrives as run state: orchestration
   already stamps analyst-owned knobs (`required_history_bars`, `lookback_days`) onto the
   `RunRequest` for the provider to honour, and `DataRequest.benchmark_ticker` already exists in the
   contract (`contracts/provider.py:31`). This sprint follows that precedent exactly.
3. **What happens when a run names no benchmark?** Nothing changes: the field is unrequested, the
   cap records `skipped`, and no other gate is affected. Failing closed here would stall ingest.

## Blast radius — measured 2026-09-04 (line counts re-measured after merge)

| File | Lines after | Change |
| --- | --- | --- |
| `contracts/provider.py` | 159 | One new RunRequest prop name |
| `orchestration/start.py` | 100 | Stamps the scanner's benchmark on the RunRequest |
| `agents/provider/poll.py` | 101 | Reads the prop, normalises it, passes it on |
| `agents/provider/ingest.py` | 179 | `with_benchmark_field` keeps field and ticker inseparable |
| `agents/provider/ingest_chunked.py` | 146 | Asks for the series on the first chunk only |

Nothing in the trading path changes shape: the snapshot gains a field that was already declared and
already merged by `_merge_parts` (`ingest_chunked.py:88`) — it had simply never been populated.

## Test plan

| # | Test | Proves |
| --- | --- | --- |
| 1 | `test_declared_benchmark_reaches_the_persisted_snapshot` | the fix, end to end through `ingest_run_node` |
| 2 | `test_no_declared_benchmark_leaves_the_series_empty` | the opt-out stays honest |
| 3 | `test_blank_benchmark_prop_is_treated_as_unnamed` | blank is not a ticker |
| 4 | `test_non_string_benchmark_prop_is_treated_as_unnamed` | a malformed prop cannot crash ingest |
| 5 | `test_benchmark_prop_is_normalised_to_upper_case` | ` spy ` resolves to `SPY` |
| 6 | `test_chunked_ingest_asks_for_the_benchmark_once` | 99 tickers cost one extra call, not one per chunk |
| 7 | `test_beta_cap_gates_when_the_snapshot_carries_a_benchmark` | **the tripwire** — a 3x name is dropped by `max_beta` |
| 8 | `test_beta_cap_is_skipped_not_passed_without_a_benchmark` | the defect's own shape, pinned so it cannot return silently |
| 9 | `test_place_run_request_declares_the_scanner_benchmark` | the run carries the scanner's own value, not a copy |

## Success factors

- `max_beta` appears in `survived_filters` (or fires as a drop) on the next deployed run.
- A run that names no benchmark still ingests and scans.
- One extra provider call per run, regardless of chunking.
- `make ci` exit 0 with the 100 % floor intact.

## Traps

- 🪤 **Naming a benchmark without requesting the field fetches nothing.** That asymmetry is the
  original defect in miniature: `collect_optional_fields` needs *both*. `with_benchmark_field` now
  binds them so no caller can supply one without the other.
- 🪤 **The chunked path is the deployed path.** A fix that only touched `ingest_once` would look
  right in tests and change nothing in the fleet, where 99 tickers exceed `ingest_chunk_size`.
- 🪤 **Green unit tests were never evidence here.** The in-process path fetches its own benchmark;
  only the graph-pull path was broken. Test 8 pins the broken shape so it stays visible.

## Law reading record

`agents/scanner/laws/laws.md` (LOCKED v1, S70) and `agents/provider/laws/laws.md` (LOCKED v1, S69)
read before coding. No clause changes: the scanner's duty to attribute drops is unchanged, and the
provider's duty to serve requested fields honestly is unchanged — this sprint makes an
already-declared field actually requested. No law-cycle needed; no clause text touched.

---

## Closeout — evidence

**Status:** MERGED

**Tree the proofs ran in (and `.env` present?):** `C:/Users/yury_/AppData/Local/Temp/wt-s195`,
branch `sprint-195-the-beta-cap-has-never-fired`, `.env` **no** (the worktree has none — the unit
gate needs none).

**Result:** the `RunRequest` now declares the scanner's benchmark ticker; the provider ingests that
series into the snapshot the graph-pull scanner reads; `max_beta` evaluates. On the fixture that
mirrors the live case, a 3x-beta name is dropped by the cap instead of surviving unjudged.

**Files changed:** `contracts/provider.py`, `orchestration/start.py`, `agents/provider/poll.py`,
`agents/provider/ingest.py`, `agents/provider/ingest_chunked.py`,
`agents/provider/tests/test_ingest.py`, `agents/provider/tests/test_provider_benchmark_ingest.py`
(new), `agents/scanner/tests/test_scanner_poll_benchmark.py` (new),
`orchestration/tests/test_start.py`, `pyproject.toml`, `uv.lock`.

**Design decisions:** recorded as [`DL-151`](../design-log.md) — benchmark ownership stays with the
scanner and travels as run state; the two rejected routes are recorded there and under *The road not
taken* above.

**Proof — the red run first** (implementation stashed, tests and contract left in place):

```text
    assert {bar.ticker for bar in benchmark} == {"SPY"}
E   AssertionError: assert set() == {'SPY'}
E   TypeError: ingest_chunked() got an unexpected keyword argument 'benchmark_ticker'
E   KeyError: 'benchmark_ticker'
FAILED test_declared_benchmark_reaches_the_persisted_snapshot
FAILED test_benchmark_prop_is_normalised_to_upper_case
FAILED test_chunked_ingest_asks_for_the_benchmark_once
FAILED test_place_run_request_declares_the_scanner_benchmark
4 failed, 9 passed
```

**Proof — the green run:**

```text
2474 passed, 6 skipped in 97.51s
TOTAL   15660   0   3364   0   100.00%
Required test coverage of 100.0% reached. Total coverage: 100.00%
```

**The first merge broke the dispatcher image, and the smoke test caught it.** `0.94.08` merged green on CI, CodeQL and Security Findings, then `build-images.yml` failed: `place_run_request` now imports `ScannerSettings`, and the slim dispatcher image copies `agents/scanner/__init__.py` and `universe.py` but not `settings.py`. The calendar-skip smoke (`DISPATCHER_AS_OF=2026-07-04`, expecting `skipped sched-2026-07-04`) exited 1. Fixed in `0.94.09` by the missing `COPY`, and the guard that could not have caught it was replaced: `test_dispatcher_image_copies_everything_its_entrypoint_imports` now reads the entrypoints' imports transitively instead of checking a hardcoded list.

**Guards planted:** test 8 pins the *broken* shape (`max_beta` in `skipped_filters`, never in
`survived_filters`, when the snapshot carries no benchmark), so a future regression to an empty
series fails a test instead of passing silently for 59 runs. The Dockerfile guard was verified by removing the new `COPY` line — `AssertionError: dispatcher image omits imported modules: ['agents/scanner/settings.py']` — then restoring it and re-running green.

**Module line counts, re-measured 2026-09-04 after merge** (the first set of numbers in this doc was
asserted, not measured, and three of five were wrong): `contracts/provider.py` **159**,
`orchestration/start.py` **100**, `agents/provider/poll.py` **101**, `agents/provider/ingest.py`
**179**, `agents/provider/ingest_chunked.py` **146** — all under the 200 hard block.

**`make ci`:** redirected to a file, exit code **0**. 2474 passed, 6 skipped, coverage 100.00 %.
pip-audit: no known vulnerabilities. detect-secrets: passed, untracked scan passed.

**`make gate-ran`:** run from `C:/Users/yury_/AppData/Local/Temp/wt-main`, whose `HEAD` matched the
printed SHA:

```text
GATE PROVEN for 92597aa305180c2a047ccc54010cdb29c0a2f7c0:
  Security Findings: success
  CI: success
  CodeQL: success
  Build and push agent images: success
```

The first merge (`6b82092`, `0.94.08`) is green on CI, CodeQL and Security Findings but **failed**
`build-images.yml`; `92597aa` (`0.94.09`) is the commit where all four are green.

**Not met / verified failing:** the fix is **not yet observed in the fleet**. The running images are
`:s194`; until a deploy retags them, production still scans without a benchmark. The first deployed
run that records `max_beta` in `survived_filters` is the live proof, and it is still owed.

---

## Return notes

- No handover happened: Codex was out of weekly quota (resets 2026-09-07), so this was specified and
  built in one session. The spec is written as a record rather than a handover — the *Handover* and
  *Handback contract* sections of `_TEMPLATE.md` are deliberately absent, not forgotten.
- The `earnings_window` half of the same veto is untouched and separately filed. Expect the
  deliberator to keep objecting to it after this ships; one gate certified is not two.
- What the next sprint should know: the in-process and graph-pull paths fetch market data
  differently, and only the graph-pull path runs in production. Any future "the fleet does not see
  X" question should start by diffing those two paths.
