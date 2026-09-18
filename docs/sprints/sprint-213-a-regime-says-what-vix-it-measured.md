<!-- Agent: planning | Role: sprint handover -->
# Sprint 213 — a regime says what VIX it measured, and says so when it measured none

**Phase:** Etalon-first continuous improvement (DL-19)
**Branch:** `sprint-213-regime-measures-vix`
**Status:** SPEC
**Version:** *next available PATCH at merge*
**Effort:** M
**Decisions:** implements [ADR-0028](../decisions/0028-the-regime-reads-vix-from-fmp-and-says-when-it-cannot.md) (read its **Correction** section) · closes work-queue item **70** · evidence [EXP-009](../research/experiments/EXP-009-volatility-sizing-replay.md) · DL and DRIFT numbers: next free **at branch time** (see *Sequencing*)

> **Why this bump kind.** PATCH. No new capability: `PROV-OUT-02` already promises *"the classification, the
> inputs behind it"* and `PROV-OUT-03` / `PROV-NEV-01` already forbid a silently degraded response. The code has
> never delivered either. The contract gains two fields to state what the law already requires.

---

## ⛔ SEQUENCING — do not branch until S211 **and** S212 are merged to `main`

This sprint shares files with both:

| Shared file | S211 | S212 | S213 |
| --- | --- | --- | --- |
| `docs/laws/ledger.md`, `docs/laws/INDEX.md` (rollups) | analyst + PM rows | — | provider row |
| `docs/laws/drift-register.md` | DRIFT-066 | — | next free |
| `docs/design-log.md` | DL-172 | next free | next free |
| `pyproject.toml` + `uv.lock` | PATCH | PATCH | PATCH |
| `docs/work-queue.md` | row 60 | rows 66, 67 | row 70 |

Branch from `origin/main` **after both have merged**, then take the next free DL, DRIFT and PATCH numbers
**at that moment**, and re-check all three again at merge. The rollup numbers are derived by `make ci`, so let
the gate tell you.

### Compatibility with S211 and S212 — checked 2026-09-17, no contradiction

- **S211** (reward_risk measured quantities) changes `contracts/analyst.py`, the analyst stop/target
  derivation, the PM reward-risk gate and the graph vocabulary. It **does not read the regime label or VIX**.
  Its target derives from per-name favourable excursion, *"rather than from a regime constant"*. S213 changes no
  base policy default (`base_stop_loss_pct`, `base_take_profit_pct`, `base_min_confidence`,
  `base_max_holding_days`), so nothing S211 depends on moves. S213 touches `contracts/provider.py`, a different
  file.
- **S212** (trace says why nothing was submitted) changes `orchestration/batch_trace.py`, adds a trace module,
  and changes `scripts/trace_run.py`. **S213 must not edit any of them.** The trace already prints the regime line
  (`batch_trace.py:80`, label plus `vix`), and with VIX populated it shows the value unchanged. Showing the new
  VIX status in the trace is a follow-up after both merge (see *Out of scope*).
- **ADR-0028 as first written would have contradicted the analyst and PM laws' exit guarantees.** That is
  already corrected in the ADR (*Correction* section). This spec follows the corrected version.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/provider/laws/laws.md` | The provider's **locked constitution** (LOCKED **v1.1**) | **Read-only during a build** — except the amendment this sprint explicitly owes, below |
| `agents/provider/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | `PROV-OUT-02` is 🟩 on tests that hand the classifier a VIX production never supplies |
| `agents/analyst/laws/laws.md`, `agents/portfolio_manager/laws/laws.md` | Consumers' constitutions | **Read-only, and not amended by this sprint.** You must prove their behaviour is *unchanged* |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections: **`PROV-OUT`** (02, 03), **`PROV-NEV`** (01, 03, 04, 07, 08), **`PROV-FAIL`**, **`PROV-TYP`**,
the provider **`CAP`** declaration, and on the consumer side **`ANLZ-FAIL-01`** and the PM's
`provider_degraded` attribution.

### The rule

1. **Before writing code**, read every law file in the map below — whole file, first time.
2. Read each agent's `test-plan.md` alongside its `laws.md`. If a clause you rely on is ⬜, say so.
3. Read [`docs/laws/conventions.md`](../laws/conventions.md) and
   [`docs/laws/drift-register.md`](../laws/drift-register.md).
4. **Answer the law-cycle question below.** It is already answered **Yes** — see why.
5. **Write the Law reading record** (bottom of this file) **before** your first code change.
6. **If a law contradicts this spec, STOP and report.**
7. **If a law is silent** where you needed a decision, record it and add a `drift-register.md` row.
8. Every test for behaviour a clause governs **cites the clause ID in its docstring** (conventions §3).

### 🩹 The law-cycle question — answered **YES**

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously make?**

**Yes, both.** `contracts/provider.py` `RegimeContext` gains the VIX status and bar date, and the provider
now guarantees *which* VIX it measured and *that* it says so when it measured none. **This sprint owes, in the
same unit of work:**

- a `PROV-OUT-02` amendment naming the regime's VIX value, VIX bar date and VIX status as part of *"the inputs
  behind it"*
- a proof row showing `PROV-OUT-03` / `PROV-NEV-01` hold **on a source that returns nothing** (not one that
  raises)
- `laws.md` version **v1.1 → v1.2** with a Changelog line
- `test-plan.md` rows, with clause IDs cited in the test docstrings
- the provider rollup in **both** `docs/laws/ledger.md` and `docs/laws/INDEX.md`, derived by the gate
- a `drift-register.md` row recording that `PROV-OUT-02` was 🟩 on `FakeDataSource` only, and that
  `PROV-OUT-03`/`NEV-01` were violated in production for every scheduled run
- `contracts.provider.CONTRACT.version` **0.5.0 → 0.6.0**. Nothing enforces this (DRIFT-060 is open), so do it
  deliberately and say so.

🪤 **`PROV-NEV-08` ("never … classify") vs `PROV-OUT-02` ("the classification").** This tension predates the
sprint. NEV-08's text scopes itself to *"sentiment scoring, … fundamental judgement"* per ADR-0002, and DRIFT-004
explicitly adopted the regime classification into OUT-02. **This sprint does not change who classifies.** If,
having read both, you judge them genuinely contradictory, file a drift row and report. Do **not** resolve it in
code.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| new `agents/provider/fmp_vix.py` (the VIX source) | provider `laws.md` + `test-plan.md` | `PROV-NEV-03` / `SEC-06` (declared endpoints: FMP is declared as validation/failover in `CAP`), `NEV-04` (never log the key), `NEV-07` (never fabricate), `FAIL-01` (contain source failure at the boundary) |
| `agents/provider/composite.py` (**112**) | same | Regime inputs stop delegating to the price source |
| `agents/provider/sources.py` (**182** 🚨) | same | `RegimeInputs` shape — **18 lines from the block** |
| `agents/provider/agent.py` (**163** ⚠) | same, plus `ANLZ-FAIL-01` and the PM's `provider_degraded` | `_get_regime` must record a VIX shortfall **without** adding `provenance.incident_refs` |
| `agents/provider/domain/regime.py` (**30**) | provider `laws.md` | Classification unchanged; input status is new |
| `contracts/provider.py` (**165**) | provider `laws.md` `PROV-TYP-*`; `tests/test_contract_required_fields.py` / `..._payload_fields.py` (S205) | Contract change → law cycle; check whether a `PROV-TYP` clause enumerates `RegimeContext` fields |
| `agents/provider/domain/market_calendar.py` (**93**, read-only) | provider `laws.md` | `trading_sessions_between(after, through)` is the freshness rule |

⚠️ **The invariant this sprint must not break: a missing VIX halts nothing.** The analyst returns an empty
result — no buys **and no exits** — whenever `regime.provenance.incident_refs` is non-empty
(`agents/analyst/run.py:56`), and the PM rejects every order on the same condition
(`agents/portfolio_manager/run.py:123`). **If your design puts any VIX-shortfall marker into
`provenance.incident_refs`, or lets a VIX vendor failure raise into `_get_regime`'s `fault_boundary` (which
produces `regime_source_degraded`, an incident ref), stop.** That is the S147 book-freeze failure, reintroduced
through an auxiliary input.

---

## Goal

Every scheduled regime carries a real VIX close from FMP when one is available, the date of the bar it came
from, and a status: **measured** (as-of session), **prior_session** (one session old, warning), or **missing**
(anything else, warning). Its label is computed from that VIX with the existing thresholds. When VIX is missing,
the regime says so in its own fields, the label is `neutral`, a warning fault is recorded, and **the analyst and
PM behave exactly as they do today**, with recommendations, exits and orders all unaffected.

## Why (context)

[EXP-009](../research/experiments/EXP-009-volatility-sizing-replay.md) found **50 / 50** scheduled regimes
`neutral`, with `vix` absent on all 50. Every production source hard-codes `vix=None`, `classify_regime` maps
`None` to `neutral`, and nothing marks the shortfall. [ADR-0028](../decisions/0028-the-regime-reads-vix-from-fmp-and-says-when-it-cannot.md)
chose FMP after probing six sources live. Until this ships, work-queue item 64's question (*should the regime
move risk?*) has nothing to act on, and the deliberator is told `vix_index=None` every night.

### Measured, 2026-09-17 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Regimes with a VIX value | **0 / 70** snapshots, all `neutral`, 0 label changes | *[re-measured 2026-09-18]* every `RegimeContext` on the live spine — the defect has grown from EXP-009's 50 / 50, not narrowed |
| Production sources returning VIX | **none** — `alpaca_data.py:54`, `tiingo.py:46`, `fmp.py:46`, `stooq.py:42`, `fundamentals.py:73` all `vix=None` | *[measured]* code read; only `FakeDataSource` (`sources.py:122`) returns one |
| Where regime inputs come from today | `CompositeDataSource.fetch_regime_inputs` → price source (Alpaca) | *[measured]* `composite.py:44-46`, `market_source_from_settings` at `composite.py:83` |
| FMP is **not** in the live composite | `market_source_from_settings` builds Alpaca + Finnhub + Alpha Vantage only | *[measured]* `composite.py:83-112` |
| FMP credential reaches the provider | `fmp-api-key → PROVIDER_FMP_API_KEY` entitlement; `settings.fmp_api_key` via `env_prefix="PROVIDER_"` | *[measured]* `orchestration/packs/trading_secrets.json`; `agents/provider/settings_feeds.py:19,71` |
| FMP credential probe blocks activation? | **No** — `"required": false` | *[measured]* `trading_credential_tests.json`, probe `fmp` |
| FMP serves `^VIX` on our plan | `stable/historical-price-eod/light?symbol=^VIX` → 200, `[{symbol, date, price, volume}]`, newest first | *[measured 2026-09-17 03:58 UTC]* live GET |
| FMP agrees with FRED and Cboe | 74 common days, max abs difference **0.000** | *[measured]* live pulls 2026-06-01 → 2026-09-16 |
| Labels with real VIX | neutral 38, **risk_on 10, risk_off 1**, 12 changes over 49 run dates; VIX 14.25–20.66 | *[measured]* FMP closes × live thresholds 15/20/25/35 |
| FMP bar for as-of session exists by 22:30 UTC | **unknown** | *[ASSUMED — not measured]* present by 03:58 UTC next day; the freshness rule tolerates one session either way; the post-deploy check records which case occurred |
| Who halts on a regime incident ref | analyst (empty result, no exits) and PM (`provider_degraded`) | *[measured]* `agents/analyst/run.py:56`, `agents/portfolio_manager/run.py:123` |
| Old snapshots stay readable | contract models use `ConfigDict(frozen=True)`, pydantic default `extra="ignore"` | *[measured]* `contracts/common.py:27-28`; new fields need **defaults** so the 50 historical snapshots still validate |
| 🆕 The referee is shown the null | `context_pm.py:63` renders `label=neutral; vix_index=None` into **every** debate prompt | *[measured 2026-09-18]* the deliberator has reasoned about regime with an empty VIX on all 70 runs, including the S214 baseline now being measured |
| Consumers of the label | analyst summary text, deliberator prompt (`context_pm.py:63`), trace (`batch_trace.py:80` — **was `:78`; S212's merge shifted it by two**) — **no risk number** | *[measured]* repo search of non-test modules |

---

## Scope — and what is deliberately NOT here

1. **A VIX source that never raises for vendor failure.** A new module (suggested `agents/provider/fmp_vix.py`)
   fetches `stable/historical-price-eod/light?symbol=^VIX` from `settings.fmp_base_url` with
   `settings.fmp_api_key` and `settings.fmp_timeout`. It handles timeout, HTTP error, non-JSON body, empty list
   and non-numeric price **itself**, returning "missing" with a reason. It never puts the key in a message or
   exception.
2. **Freshness from the trading calendar.** With `n = trading_sessions_between(after=bar_date, through=as_of)`:
   `n == 0` → `measured`; `n == 1` → `prior_session`; otherwise → `missing`. Pick the **newest bar dated on or
   before `as_of`**; never use a bar dated after it. 🪤 The calendar never raises. Past `calendar_window_end()` it
   silently stops knowing holidays, but the dispatcher already refuses to schedule such runs
   (`CalendarWindowExceededError`), so no extra handling is owed. Don't add a raise.
3. **Regime inputs come from the VIX source**, not the price source: `CompositeDataSource` gains a regime source
   and `market_source_from_settings` constructs it. `FakeDataSource` keeps working for tests and `run_local.py`.
4. **Contract:** `RegimeContext` gains `vix_status: Literal["measured", "prior_session", "missing"]` defaulting to
   `"missing"`, and `vix_as_of: date | None = None`. The defaults are deliberate: all 50 historical snapshots
   validate and read, truthfully, as `missing`. Name the fields otherwise if the law reading gives a better
   reason, but keep the defaults' meaning.
5. **`_get_regime` records the shortfall honestly without halting anyone.** `prior_session` and `missing` each
   record a **warning** fault naming the status and reason. **`provenance.incident_refs` stays `()`** for both.
   `regime_source_degraded` keeps its meaning for a genuine boundary failure (unchanged).
6. **The law cycle** listed above.

### Out of scope (do NOT build this sprint)

- **Any change to what the label moves.** No threshold, no base policy default, no stop, floor or sizing
  change. That is work-queue item 64 / ADR-0025 Decision B.
- **Any change to how the analyst or PM react to a degraded regime.** Their halt-on-incident-ref behaviour is
  their laws' business. This sprint only guarantees it is **not triggered** by VIX.
- **The deliberator rendering `vix_status` / `vix_as_of`.** `context_pm.py:63` keeps rendering `vix_index`. Adding
  status is a deliberator change under `DLIB-NEV-08` (its own law cycle) — follow-up.
- **The trace showing VIX status** — `batch_trace.py` belongs to S212. Follow-up after both merge.
- **A FRED fallback.** ADR-0028 names it; it is not built now.
- **Adding properties to the `Regime` graph node** (`agents/provider/store.py:58-62`). The `RegimeContext`
  snapshot already carries the full contract. A new `Regime` property would move the vocabulary pack, which S211
  also moves, and force a full `up`. If you find a law requires it, stop and report.
- **No ADR reversal.**

### The road not taken (LAW-06)

- **Mark a missing VIX with an incident ref** (ADR-0028 as first written). Rejected: the analyst and PM halt on
  any regime incident ref, so every FMP miss would freeze the book, exits included (see the ADR's *Correction*).
- **Let the FMP call raise and rely on the existing `fault_boundary`.** Rejected for the same reason: that path
  emits `regime_source_degraded`.
- **Extend `FMPDataSource` (`fmp.py`, 140 lines) with a VIX method.** Rejected as the default: it is the OHLCV
  validation source and not composed in production. A VIX method there drags an unused OHLCV client into the
  composite, and the file would approach the 150-line warning. Record it if you choose otherwise.
- **Use the FMP `quote` endpoint.** Rejected: it has no bar date, so freshness can't be proven.
- **Use FRED, Cboe or a VIXY / realised-volatility proxy.** Rejected in ADR-0028 (lag, undocumented, wrong
  units).

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where status travels between source and agent:** on `RegimeInputs` (`sources.py`, 182 lines — may force a
   split) or as a separate result type from the VIX source. What hangs on it: `FakeDataSource` and every test that
   constructs `RegimeInputs`.
2. **The fault shape for `prior_session` vs `missing`:** severity (warning for both is the spec's position),
   `error_type` names, and the context keys, so a nightly query can count them without parsing messages
   (DL-152's lesson).
3. **Whether `vix` is kept or cleared when `missing` because the bar is stale** — the spec's position is
   **cleared** (`PROV-NEV-07`: never present a stale value as current). Record it.

---

## Blast radius — measured 2026-09-17

| What | Detail |
| --- | --- |
| Files changed | new `agents/provider/fmp_vix.py`; `agents/provider/composite.py` (112); `agents/provider/sources.py` (182 🚨); `agents/provider/agent.py` (163 ⚠); `contracts/provider.py` (165); provider `laws.md` + `test-plan.md`; `docs/laws/{ledger,INDEX,drift-register}.md`; `docs/design-log.md`; `docs/work-queue.md`; `pyproject.toml` + `uv.lock`; tests |
| Agents affected | **provider** (code). Analyst, PM, deliberator **read** `RegimeContext` and must be proven unchanged. No agent imports another |
| Contract change? | **Yes** — `RegimeContext` +2 defaulted fields; law cycle mandatory |
| Graph vocabulary change? | **Should be no** — the new fields ride inside the existing `RegimeContext.snapshot`. Diff `orchestration/packs/trading_graph_vocabulary.json` at handback and state the result |
| New env keys / tunables | **None expected.** `fmp_base_url`, `fmp_api_key`, `fmp_timeout` already exist. If you add a tunable, the deploy becomes a full `up`; say so <!-- pragma: allowlist secret --> |
| Deploy implication | **Image rebuild and fleet retag**, if the vocabulary pack and tunables are unchanged (verify, don't assume). Every image carries `contracts/`; old images ignore the new fields, so a mixed fleet can't break |

---

## Steps, in order

1. Confirm S211 and S212 are merged; branch from current `origin/main`; take the next free DL, DRIFT and PATCH.
2. **Read the laws** (MUST RULE above) and write the Law reading record.
3. **Record the design decisions** in `docs/design-log.md`.
4. **Plant the failing tests first** and watch them fail. Paste the red output.
5. **Implement.**
6. **Law cycle:** amendment, version, Changelog, test-plan rows, docstring citations, rollups, drift row,
   `CONTRACT.version`.
7. **Prove the guards can fail (DL-70):** break the implementation, watch each guard go red, restore.
8. **`make ci` green** — all 12 steps, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

All tests are in-memory with the FMP transport **stubbed** (inject the opener or monkeypatch the HTTP call).
**No `.env`, no network.**

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 As-of bar → measured | Stub returns `[{date: as_of, price: 14.3}, …]` | `vix=14.3`, `vix_as_of=as_of`, `vix_status="measured"`, `label="risk_on"`, **no** fault, `incident_refs=()` |
| A2 | Prior session → warning, label still computed | as_of = a Monday; newest bar = the previous Friday, price 21.0 | `vix_status="prior_session"`, `vix_as_of`=Friday, `label="risk_off"`, one **warning** fault, `incident_refs=()` |
| A3 | Stale beyond one session → missing | newest bar 3 sessions old | `vix_status="missing"`, `vix=None`, `label="neutral"`, warning fault naming staleness, `incident_refs=()` |
| A4 | 🪤 Vendor failure never raises | Stub raises timeout / returns HTTP 500 / non-JSON / `[]` / `price: "n/a"` — one case each | For every case: no exception escapes `_get_regime`; `vix_status="missing"`; `incident_refs=()`; **no** `regime_source_degraded` |
| A5 | 🪤 Never uses a future bar | newest bar dated after `as_of` | That bar is ignored; the choice follows A1–A3 on the remaining bars |
| A6 | 🎯 **A missing VIX halts nothing** | Graph-pull run (extend the pattern in `orchestration/tests/test_graph_pull_e2e.py`) with the VIX stub returning `[]` | The analyst emits its normal recommendations (buys **and** exits); the PM does **not** return `provider_degraded`; identical to the same run with VIX measured apart from `label` / `vix*` |
| A7 | Old snapshots still read | Validate a `RegimeContext` dict **without** the new fields | Validates; `vix_status == "missing"`, `vix_as_of is None` |
| A8 | 🎯 `PROV-OUT-02` proven on the **production** composition | `market_source_from_settings` with stubbed transports | `fetch_regime_inputs` reaches the VIX source, **not** the price source. This is the test that could have failed for the last 50 nights |
| A9 | 🪤 A holiday is not a missed session | as_of = Tue 2026-09-08 (after Labor Day, Mon 09-07); newest bar = Fri 09-04 | `trading_sessions_between` = 1 → `vix_status="prior_session"`, **not** `missing` |
| A10 | Credential never leaks (`PROV-NEV-04`) | Stub failure echoing the request URL | No fault message, context value or exception text contains the API key |

---

## Success factors

- [ ] A1–A10 pass, each cited to its clause; every guard planted, watched red, restored (stated per guard).
- [ ] **A6 holds:** a missing VIX changes no analyst or PM output other than the regime's own fields.
- [ ] `provenance.incident_refs` is `()` in every VIX shortfall case (A2–A5).
- [ ] `git diff --stat -- agents/analyst agents/portfolio_manager agents/deliberator orchestration/batch_trace.py scripts/trace_run.py` is **empty**.
- [ ] Law cycle complete: `PROV-OUT-02` amended, `laws.md` v1.2 + Changelog, test-plan rows, rollups derived in
      both files, drift row, `CONTRACT.version` 0.6.0.
- [ ] Vocabulary pack diff stated (expected: unchanged), plus the deploy implication derived from it.
- [ ] Every touched module < 200 lines (`sources.py` is at 182).
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] 🟢 **Post-deploy, planning agent:** the first scheduled run after deploy has a `RegimeContext` with a
      numeric `vix`, a `vix_as_of`, and a `vix_status`, and the run went 8/8 with no `provider_degraded`. Record
      **which freshness case occurred at 22:30 UTC** in `docs/laws/functionality-checks.md`. That answers
      ADR-0028's one open assumption.

---

## Traps

🪤 **The incident-ref trap is the whole risk of this sprint.** A test asserting `vix_status == "missing"` passes
just as well when you *also* add an incident ref. A6 is the only test that catches it, so don't skip or weaken A6.
🪤 **`FakeDataSource` makes everything green.** It returns a VIX, so any test built on it can't see the
production path. A8 must use `market_source_from_settings`.
🪤 **Weekends and holidays.** A Monday run's prior session is Friday, not Sunday. Calendar days would mislabel
every Monday as `missing`. Use `trading_sessions_between`.
🪤 **FMP returns newest first and may include today's partial row.** Select by date, never by list position.
🪤 **`sources.py` is 182 lines.** Growing `RegimeInputs` there may hit the block. Split rather than compress.
🪤 **`CONTRACT.version` has no gate (DRIFT-060).** Moving it is on you; nothing will fail if you forget.
🪤 **S205's required-field guards.** Measured 2026-09-17: `tests/test_contract_required_fields.py` and
`test_contract_required_payload_fields.py` do **not** reference `RegimeContext` today. If the `PROV-TYP`
reading shows a clause that should now require the new fields, extend the guard in the same law cycle.
🪤 **A worktree has no `.env`.** All tests are stubbed. The live proof is the planning agent's, post-deploy.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa`.
  📌 Current sizes: `sources.py` **182**, `contracts/provider.py` **165**, `agent.py` **163**, `fmp.py` **140**,
  `composite.py` **112**, `market_calendar.py` **93**, `domain/regime.py` **30**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers. The one-session tolerance is ADR-0028's rule, not a tunable. If you believe it should be
  tunable, record why in the design log and say so; a new tunable changes the deploy.
- Faults, not silent failure — `kernel.fault_boundary` — but **not** for the VIX vendor call (see Scope 1).
- `make ci` **all 12 steps** green, **100.00 % coverage floor**. **Never measure the gate through a pipe.**
- PATCH version bump, `uv.lock` staged with it.
- **Line endings are LF.** The repo has no `.gitattributes` (work-queue item 69). Check `git ls-files --eol` on
  every file you touch before committing.

---

## Sequencing after merge

1. `make ci` green locally, branch pushed, **`make gate-ran` exits 0** from the worktree whose `HEAD` is the
   commit being proved; check the printed SHA against `git rev-parse HEAD`.
2. Merge to `main` locally and push (not from the branch's own worktree).
3. **Post-merge CodeQL** on the merged SHA.
4. **Deploy** per the Blast radius row. Image retag if the vocabulary pack and tunables are unchanged, otherwise
   a full `up`.
5. Planning agent runs the post-deploy check above and records it.

---

## Handover — paste this to Codex

```text
Sprint 213 - a regime says what VIX it measured, and says so when it measured none.
Spec: docs/sprints/sprint-213-a-regime-says-what-vix-it-measured.md (read it whole).
Decision: docs/decisions/0028-the-regime-reads-vix-from-fmp-and-says-when-it-cannot.md, INCLUDING its
"Correction" section.

DO NOT START until S211 and S212 are both merged to main. Then branch
sprint-213-regime-measures-vix in its own worktree from current origin/main, and take the next free DL,
DRIFT and PATCH numbers at that moment (re-check at merge). Never commit to main.

MUST RULE: before code, read agents/provider/laws/laws.md + test-plan.md, agents/analyst/laws/laws.md and
agents/portfolio_manager/laws/laws.md (read-only, not amended), docs/laws/conventions.md,
docs/laws/drift-register.md. Fill the Law reading record first.
LAW-CYCLE ANSWER: YES. contracts/provider.py RegimeContext gains vix_status (default "missing") and
vix_as_of (default None). Amend PROV-OUT-02, provider laws v1.1 -> v1.2 + Changelog, test-plan rows with
clause IDs in docstrings, rollups in docs/laws/ledger.md AND docs/laws/INDEX.md (let make ci derive the
numbers), a drift row, contracts.provider CONTRACT.version 0.5.0 -> 0.6.0.

WHAT: every production source hard-codes vix=None, so all 50 scheduled regimes were a silent "neutral".
Add an FMP VIX source (stable/historical-price-eod/light?symbol=^VIX, existing settings.fmp_* fields,
existing credential) composed in market_source_from_settings as the regime-input source. Freshness via
agents/provider/domain/market_calendar.py trading_sessions_between(after=bar_date, through=as_of):
0 -> measured, 1 -> prior_session (warning fault), else -> missing (warning fault, vix cleared,
label neutral). Newest bar dated <= as_of only.

THE INVARIANT - a missing VIX halts nothing:
- The analyst returns an EMPTY result (no exits) and the PM rejects all orders whenever
  regime.provenance.incident_refs is non-empty (agents/analyst/run.py:56, agents/portfolio_manager/run.py:123).
- So NEVER put a VIX shortfall into provenance.incident_refs.
- NEVER let the FMP call raise into _get_regime's fault_boundary (that produces regime_source_degraded).
  The VIX source handles timeout/HTTP/parse/empty itself and returns missing.
- Test A6 (graph-pull run with VIX missing: analyst and PM output unchanged) is mandatory.

DO NOT EDIT: agents/analyst, agents/portfolio_manager, agents/deliberator, orchestration/batch_trace.py,
scripts/trace_run.py (S212 owns the trace), the Regime graph node properties / vocabulary pack (expected
unchanged - diff it and state the result), any threshold or base policy default.

ORDER: design decisions in docs/design-log.md -> tests A1-A10 red (paste output) -> implement -> law cycle
-> break each guard, watch red, restore -> make ci redirected to a file (never piped) -> fill Closeout +
Return notes, Status: BUILT.

TRAPS: FakeDataSource returns a VIX, so tests on it cannot fail - A8 must use market_source_from_settings.
Monday's prior session is Friday (use the calendar, not calendar days). FMP lists newest first; select by
date. sources.py is 182 lines: split, don't compress. Never put the API key in any message. Worktree has
no .env: stub the transport. Keep line endings LF (no .gitattributes); check git ls-files --eol.
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
| *to fill* | | | |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** *to fill*

**Contradictions found between a law and this spec:** *to fill*

**Laws found silent where a decision was needed:** *to fill*

**Clauses that were ⬜ and are now proven:** *to fill*

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | *to fill* | | | |

**Tests added beyond the plan:** *to fill*

---

## Closeout — evidence

**Status:** *to fill*

**Tree the proofs ran in (and `.env` present?):** *to fill*

**Result:** *to fill*

**Files changed:** *to fill*

**Design decisions:** *to fill*

**Proof — the red run first:**

```text
_to fill_
```

**Proof — the green run:**

```text
_to fill_
```

**Guards planted:** *to fill*

**Module line counts:** *to fill*

**Vocabulary pack diff and deploy implication:** *to fill*

**`make ci`:** *to fill*

**`make gate-ran`:** *to fill*

**Not met / verified failing:** *to fill*

---

## Return notes

- *to fill*
