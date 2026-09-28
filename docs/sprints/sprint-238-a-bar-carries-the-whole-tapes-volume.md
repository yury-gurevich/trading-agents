<!-- Agent: planning | Role: sprint handover -->
# Sprint 238 — a bar carries the whole tape's volume, and fetching it never trips the plan's 15-minute wall

**Phase:** Etalon-first continuous improvement (DL-19) · live defect, ranked first (work-queue 89)
**Branch:** `sprint-238-a-bar-carries-the-whole-tapes-volume`
**Status:** BUILT — 2026-09-28, claude.ai cloud session, branch `claude/festive-shannon-7fibne` (the session forced this name; not `sprint-238-…`). Owed to the planner: `uv lock`, Windows `make ci`, `make gate-ran`, F1–F3.
**Version:** *next available PATCH at merge*
**Effort:** S
**Decisions:** [DL-233](../design-log.md) (the measurement, and its 2026-09-28 amendment: six planner decisions this spec builds on) · work-queue item **89** · [DL-237](../design-log.md) / DL-238 D7 (the clean-session rule this sprint must not reset) · **DRIFT-080** (the provider law never says which volume a bar carries) · the builder's design decisions go to the **next free DL** (`DL-239` at spec time)

> **Why this bump kind.** No new capability. The provider exists to hand every agent *"clean,
> validated … facts … it never has to … second-guess"* (its purpose statement), and the scanner's
> 500,000-share floor already assumes consolidated volume. The bars carry one venue's 1.55–6.49 % share
> of it. That is a bug, so this is a PATCH.

---

## 🔴 MUST RULE — read the laws for every element you touch, BEFORE you write any code

**This is a gate, not advice. Do not open an editor until step 5 is done.**

| Location | What lives there | How to treat it |
| --- | --- | --- |
| `agents/<name>/laws/laws.md` | One agent's **locked constitution** | **LOCKED. Read-only during a build**, except the provider amendment this spec names (law-cycle answer: Yes) |
| `agents/<name>/laws/test-plan.md` | Proven (🟩) vs unproven (⬜) per clause | Read it to learn whether what you rely on is proven or merely asserted |
| `docs/laws/*.md` | Umbrella laws, ledger, conventions | Same status. `drift-register.md` is the **one law-adjacent file you may append to** |

Binding sections here: **`PROV-IDN`** (purpose), **`PROV-OUT`** (`-01`, `-03`, `-04`), **`PROV-FAIL`**
(`-01`, `-05`), **`PROV-PARAM`** (`alpaca_data_feed`), and the scanner's **`PARAM`** row for
`min_average_volume` (read-only).

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

### The law-cycle question — answered

> **Does this sprint change any file in `contracts/`, or add a guarantee an agent did not previously
> make?**

**Yes — a new guarantee, no contract change.** The provider will promise which volume a bar carries,
and that asking for it respects the feed's entitlement. Today its law is silent on both. The sprint owes,
in the same unit of work:

- **`PROV-OUT-07`** (the next free `OUT` ID; checked free at spec time), in substance: *an OHLCV bar's
  volume is the consolidated tape's volume across every venue, never one venue's share; a request never
  asks a source for data its entitlement refuses, and a refusal fails loud per `PROV-FAIL-01`, never as
  an empty success or a silent switch to a one-venue feed.* You own the final wording.
- The provider book goes **v1.3 → v1.4** with a Changelog line; the `alpaca_data_feed` `PARAM` row reads
  `"sip"`, its rationale naming consolidated volume and DL-233.
- A `test-plan.md` row per clause, the clause ID cited in each test docstring, and the rollup updated in
  **both** `docs/laws/ledger.md` **and** `docs/laws/INDEX.md` (let `make ci` tell you the number).
- **`DRIFT-080`**: intent (the purpose statement) says consumers never second-guess a fact; reality
  served one venue's volume from 2026-08-08 at the latest; kind `law gap`; status `CORRECTED (S238,
  provider laws v1.4)`.

### Element → law map

| Element you will touch | Law file(s) to read first | Why it binds |
| --- | --- | --- |
| `agents/provider/alpaca_data.py` | `agents/provider/laws/laws.md` + `test-plan.md`; `docs/laws/conventions.md` | `PROV-OUT-01` (validated facts, honest quality record), `PROV-FAIL-01` (a refused request is contained, never bad data as good), new `PROV-OUT-07` |
| `agents/provider/settings_feeds.py` | provider `laws.md` § `PARAM` | `alpaca_data_feed` is `NO (mode selector)`; its default moves `"iex"` → `"sip"` |
| `orchestration/packs/trading_vault_probes.py` | provider `PROV-SEC-*`; [DL-36](../design-log.md) (credentials are tested before handover) | the seeder's `alpaca-data` probe must test the feed the fleet actually reads |
| `agents/scanner/settings.py` (**read only**) | `agents/scanner/laws/laws.md` § `PARAM` | `min_average_volume` (500,000 shares) assumes consolidated volume; the value does not change |

⚠️ **No file on DL-238 D7's decision-path list changes.** The list is `DECISION_PATHS` in
`scripts/replay_fidelity_git.py:21-31`: `agents/scanner/`, `agents/analyst/`,
`agents/portfolio_manager/`, `agents/provider/domain/`, `agents/execution/order_tolerance.py`,
`contracts/`, `orchestration/packs/trading_tunables.json`, `orchestration/packs/trading_issuer_map.json`,
`orchestration/history_window.py`. Any change there marks every `s232` session non-clean, and DL-237's
first fidelity verdict slips by four sessions or more. **If your change needs one of those files, stop
and report.** That includes the scanner's own `laws.md`, which sits under `agents/scanner/`.

---

## Goal

At merge, the provider's default OHLCV fetch asks Alpaca for **SIP** (consolidated) daily bars, and a
SIP request never sets an `end` inside the plan's 15-minute window. So a window ending today returns 200
with whole-tape volume, whether it comes from the scheduled run, an intraday manual run or the Key Vault
seeder's probe. An `iex` request is byte-identical to today's. The provider law states the guarantee as
`PROV-OUT-07`, cited by the tests that prove it.

## Why (context)

Since 2026-08-08 at the latest, every scheduled run has filtered its universe on **IEX** volume, 1.55–6.49 % of the tape
by name, against a floor written for consolidated volume. The floor drops 60–64 of every run's 99–100
names, so every candidate comes from the ~35 names that happen to trade heavily on IEX, and the candidate
cap of 25 has never bound. Every P16 scoreboard figure measures that accident. On the fleet's own inputs,
S237's Layer 2 measured what SIP volume changes: approvals rise from a median **2** to **13** a session.
The book sits ~24 % invested and would fill within days, bounded by the PM's position, sector and
cluster caps.

The obvious fix, one setting from `iex` to `sip`, **fails every run**: Alpaca reads the fleet's bare-date
`end` as the end of that day, which is always inside the free plan's 15-minute window for SIP (measured
below). That is why this is a sprint and not an env edit.

### Measured, 2026-09-28 — read these before designing

| Claim | Value | How it was measured |
| --- | --- | --- |
| Volume-floor drops on the live scanner | **3,128 of 4,951** evaluations (63.2 %), 60–64 names every run | *[measured 2026-09-27, DL-233]* all 50 stored `FilterTrace`s, 2026-08-08 → 2026-09-25 |
| Universe names below 500,000 | **65 / 99** on IEX, **0 / 99** on SIP (thinnest BLK 735,313, GD 1,277,979) | *[measured 2026-09-28]* `scripts/universe_sp100.txt`, 203-session average to 2026-09-25, both feeds |
| IEX share of SIP volume | 1.55 % – 6.49 %, median 4.21 % | *[measured 2026-09-28]* same request, 99 names |
| `feed=sip`, `end` = today's bare date | **403** `subscription does not permit querying recent SIP data` | *[measured 2026-09-28 06:58 AEST]* the provider's own request shape, provider key; Sunday, market closed |
| `feed=sip`, `end` = now / tomorrow's date | 403 / 403 | *[measured]* same run |
| `feed=sip`, `end` = now − 16 min (RFC 3339) / `end` omitted | 200 / 200, LLY average 3,019,571 against IEX 115,867 | *[measured]* same run |
| `trades/latest?feed=sip` (the credential test's endpoint) | 403 | *[measured]* same run |
| The live `provider` app overrides the feed | **No**: no `PROVIDER_ALPACA_*` variable on `provider` (`s232`) | *[measured 2026-09-28]* `az containerapp show … env[].name` |
| Approvals with SIP volume | median 13 a session against 2 (381 against 85 over 31 sessions) | *[measured 2026-09-27]* S237 Layer 2, live inputs from 2026-08-13 |
| A clamped SIP request made at 22:30 UTC includes that session's bar | bar timestamps are 04:00Z (EDT) / 05:00Z (EST), well before 22:15Z | *[ASSUMED for the day-of case]* the Sunday run returned Friday's bar with `end` omitted; the first post-deploy run settles it (F4 below) |
| During market hours, a clamped SIP request returns today's partial bar up to now − 15 min | — | *[ASSUMED — not measured]* the measurement ran on a Sunday. Only intraday manual runs see it; they already read a partial IEX bar today. Settle with the same request during a session (13:30–20:00 UTC) if an intraday run matters before then |

---

## Scope — and what is deliberately NOT here

1. **The failing tests first** (A1–A6 below), asserted on the request the provider sends and the source
   it builds, not on a proxy.
2. **The request end rule, and the whole query with it.** One pure, fully covered function builds the
   complete query a page request sends (`symbols`, `timeframe`, `start`, `end`, `feed`, `limit`,
   `page_token`) from `(tickers, window, feed, page_token, now)`. Its `end`: for `sip`,
   `min(midnight UTC after window.end, now − 15 min)` as RFC 3339 with `Z`; for any other feed,
   `window.end.isoformat()` exactly as today. `AlpacaDataSource` takes an injectable clock (default:
   the real UTC time). `_download_page` only encodes and sends what that function returns: it stays
   the only `pragma: no cover` code, and no rule hides inside it.
3. **The default flips.** `ProviderFeedSettings.alpaca_data_feed` defaults to `"sip"`.
   `PROVIDER_ALPACA_DATA_FEED` still overrides it.
4. **One source for the default.** The seeder's probe (`trading_vault_probes._alpaca_data_source`) falls
   back to the provider's own default, not a second `"iex"` literal. `orchestration` may import
   `agents.provider`; it already does.
5. **The law cycle** named above: `PROV-OUT-07`, v1.4, the `PARAM` row, test-plan rows, both rollups,
   `DRIFT-080`.
6. **The builder's design decisions** in `docs/design-log.md` under the next free DL.

### Out of scope (do NOT build this sprint)

- **Any file on the decision-path list** (the ⚠️ above). The floor stays 500,000; the scanner, analyst,
  PM, contracts and pack tunables are untouched.
- **`orchestration/packs/trading_credential_tests.json`.** The `alpaca-data` credential check stays on
  `feed=iex`: it proves the key, and SIP's latest trade is refused on this plan (measured). Changing it
  makes every fleet check fail.
- **The replay harness.** `scripts/replay_dataset_sources.py` already reads SIP, with historical `end`s.
- **Item 91** (the PM's adoption-day marks). It is the next sprint, not this one.
- **The deploy.** It is the operator's call, and never before `sched-2026-09-28` has delivered its three
  owed proofs.

### The road not taken (LAW-06)

- **`PROVIDER_ALPACA_DATA_FEED=sip` in `trading_tunables.json`.** Rejected: that file is a decision path,
  so it resets DL-237's clean set (DL-233 amendment, decision 1).
- **Omit `end` for SIP.** Rejected: measured to work, but a window ending yesterday requested in the first
  15 minutes after UTC midnight still 403s.
- **Retry on 403 with a clamped `end`.** Rejected: two requests per page, and a vendor message string as
  control flow. The clamp is deterministic.
- **Fall back to IEX when SIP is refused.** Rejected: it silently reintroduces the defect this sprint
  removes. A refusal fails loud (`PROV-FAIL-01`).
- **A settings field for the 15 minutes.** Rejected: it is Alpaca's entitlement, not our policy, and a new
  env key turns the deploy into a full `up` (DL-233 amendment, decision 3).
- **Scale the floor to IEX, use IEX dollar volume, or drop the floor.** Rejected in DL-233 (b)–(d): IEX's
  share varies 4× by name, and the floor is the guard a wider universe needs.

---

## The design decisions this sprint has to make

**Record these in `docs/design-log.md` with their rejected alternatives BEFORE implementing (LAW-06).**

1. **Where the end rule lives and what it is called.** `alpaca_data.py` is **181** lines; the rule, the
   clock and their docstrings will likely push it past 200. A small sibling module (for example
   `agents/provider/alpaca_request.py`) is the expected shape; say what you chose and why.
2. **How the probe reads the provider's default.** Pick one source and name it.
3. **The final `PROV-OUT-07` wording**, and whether the refusal half belongs in it or is left to
   `PROV-FAIL-01` with a cross-reference.

🪤 **Take the next free DL number, then re-check it at merge.** `DL-239` is free at spec time; the planner
may land another DL on `main` before you merge.

---

## Blast radius — measured 2026-09-28

| What | Detail |
| --- | --- |
| Files changed | `agents/provider/alpaca_data.py` (**181**) + likely a new sibling for the end rule; `agents/provider/settings_feeds.py` (130); `orchestration/packs/trading_vault_probes.py` (**181**); tests `agents/provider/tests/test_alpaca_data.py` (102), `orchestration/tests/test_trading_vault_probes.py`; `agents/provider/laws/laws.md` (373), `test-plan.md` (134); `docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md`, `docs/design-log.md`; `pyproject.toml` + `uv.lock` |
| Agents affected | provider only, plus the orchestration pack probe that `scripts/seed_key_vault*.py` run. No agent imports another. |
| Contract change? | No |
| Graph vocabulary change? | No |
| New env keys / tunables | None. A default changes inside the image; the existing `PROVIDER_ALPACA_DATA_FEED` still overrides it. |
| Deploy implication | **Image rebuild and retag**, not a full `up`. It changes what the fleet trades, so it is the **operator's call**, after `sched-2026-09-28`. |

---

## Steps, in order

1. **Read the laws** (MUST RULE above) and write the Law reading record.
2. **Record the design decisions** in `docs/design-log.md`.
3. **Plant the failing tests first** (A1–A6) and watch them fail. Paste the red output.
4. **Implement.**
5. **Law cycle**: `PROV-OUT-07`, v1.4 + Changelog, the `PARAM` row, test-plan rows, docstring
   citations, both rollups, `DRIFT-080`.
6. **Prove the guards can fail (DL-70)**, planting each of these in turn, watching it go red, and
   restoring it: the clamp removed (A1 red); the clamp applied to `iex` (A3 red); the default reverted
   to `"iex"` (A4 red); the probe's fallback hard-coded to `"iex"` (A5 red); a 403 swallowed into an
   empty result (A6 red).
7. **Confirm the decision paths are untouched:**
   `git fetch origin main && git diff --name-only origin/main...HEAD | grep -E '^(agents/(scanner|analyst|portfolio_manager|provider/domain)/|contracts/|agents/execution/order_tolerance\.py|orchestration/packs/trading_(tunables|issuer_map)\.json|orchestration/history_window\.py)'`
   must print nothing. Paste the command and its (empty) output.
8. **`make ci` green**: every step of the `ci:` target, **redirected to a file, never piped**.
9. **Fill the handback sections** at the bottom of this file.

---

## Test plan

| # | Test | Plants | Must prove |
| --- | --- | --- | --- |
| A1 | 🎯 A SIP request for a window ending today never ends inside the last 15 minutes (`PROV-OUT-07`) | clock `2026-09-28T22:30:00Z`; window ending `2026-09-28` | the request's `end` is `2026-09-28T22:15:00Z`, and that session's 04:00Z bar would be inside it |
| A2 | A SIP request for a past window ends at the midnight after it | clock `2026-10-02T12:00:00Z`, window ending `2026-09-28`; and clock `2026-09-29T00:05:00Z`, same window | `2026-09-29T00:00:00Z`; then `2026-09-28T23:50:00Z` (the clamp wins in the first 15 minutes after midnight) |
| A3 | An IEX request is byte-identical to today's | two clocks a day apart; `feed="iex"`; with and without a `page_token` | the whole query equals the dict `main`'s `_download_page` builds today, parameter for parameter, and does not depend on the clock |
| A4 | The provider's default feed is SIP (`PROV-OUT-07`) | `ProviderFeedSettings()` with no env; `market_source_from_settings` | the setting reads `"sip"` and the composed `AlpacaDataSource` is built with `feed="sip"` |
| A5 | The seeder probe tests the fleet's feed | env without `PROVIDER_ALPACA_DATA_FEED`; then with it set to `iex` | the probe's source reads `"sip"`, then `"iex"`: the default comes from the provider, and the override still works |
| A6 | 🪤 A refused request fails loud (`PROV-OUT-07` / `PROV-FAIL-01`) | the page download raises `HTTPError` 403 | `fetch_ohlcv` raises: no `()` success, and no second request on another feed |

---

## Success factors

- [ ] With no env override, the provider requests `feed=sip`, and a SIP request's `end` is never later
      than `now − 15 min` for the injected clock (A1, A2, A4).
- [ ] An `iex` request is byte-identical to `main`'s (A3).
- [ ] The seeder's `alpaca-data` probe falls back to the provider's default (A5).
- [ ] A refused request raises; nothing falls back to IEX (A6).
- [ ] Step 7's decision-path check prints nothing.
- [ ] Law cycle done: `PROV-OUT-07` 🟩, provider book v1.4, `PARAM` row `"sip"`, both rollups, `DRIFT-080`.
- [ ] Design decisions recorded with rejected alternatives under a free DL number.
- [ ] Every DL-70 plant in step 6 planted, watched to fail and restored, stated per plant.
- [ ] Every touched module < 200 lines.
- [ ] `make ci` exit 0, 100.00 % coverage.
- [ ] **Planner, before merge (live, main's `.env`)**, from the branch's worktree with
      `uv run --env-file <main>/.env`:
  - **F1**: `market_source_from_settings(ProviderSettings())` with no feed override fetches the
    99 names over a 300-day window ending today. Result: 200, 99 names, LLY's 203-session average in the
    millions (3,019,571 to 2026-09-25).
  - **F2**: `probe_alpaca_data(env)` without the feed variable reads `passed`.
  - **F3**: the scanner's own filters over F1's bars, with the live scanner settings, show
    `min_average_volume` dropping 0 names and the candidate count at the cap (25), or the reason it is not.
- [ ] **Owed after the operator's deploy (F4)**: the first scheduled run's `ScanRun` shows LLY's
      `average_volume` in the millions, its `FilterTrace` drops 0 names on volume, candidates = 25, and the
      provider records no fault.

---

## Traps

🪤 **The one-line flip looks right and 403s every run.** A unit test with a stubbed HTTP layer cannot
see it; only F1 can. This is why the planner runs F1 before merging.
🪤 **Midnight after `window.end`, not `window.end` at 00:00.** Daily bars are stamped 04:00Z or 05:00Z. An
`end` of `T00:00Z` on the window's last day drops that day's bar, silently, on every run.
🪤 **Touching a decision path resets the fidelity clock.** The scanner's `laws.md` is under
`agents/scanner/`. Leave it alone; the floor's meaning is carried by `PROV-OUT-07` and DRIFT-080.
🪤 **Do not "fix" the credential test to SIP.** `trades/latest?feed=sip` is refused on this plan
(measured): every fleet check would fail and the dispatcher would hold the run.
🪤 **Do not hide the rule in `_download_page`.** That function is `pragma: no cover`; logic there is
untested logic that reads as covered.
🪤 **`alpaca_data.py` and `trading_vault_probes.py` are both at 181.** Split; do not grow either past 200.

---

## Guardrails (every sprint)

- No agent imports another agent; kernel imports nothing above it (`import-linter`).
- Every module < 200 lines (warn at 150). Split, don't grow. No `# noqa` to bypass a rule.
  📌 Current sizes: `alpaca_data.py` **181**, `trading_vault_probes.py` **181**, `settings_feeds.py`
  **130**, `test_alpaca_data.py` **102**.
- Module docstring declares `Agent:` / `Role:` / `External I/O:`.
- No magic numbers: the 15 minutes is a **named constant** citing Alpaca's refusal (DL-233 amendment,
  decision 3), not a `tunable()`. `alpaca_data_feed` is a **mode selector**, not a tunable; its `PARAM`
  row already says so.
- Faults, not silent failure: `kernel.fault_boundary`.
- `make ci` **every step** green, **100.00 % coverage floor**. **Never measure the gate through a
  pipe**: `make ci | tail` reports *`tail`'s* exit code. Redirect to a file and read the file.
- Version bump: PATCH in `pyproject.toml`. 🪤 A cloud session cannot re-resolve `uv lock`
  (`download.pytorch.org` is blocked, DL-228): if it fails, leave `uv.lock` untouched and say exactly
  that; the planner re-locks before merging.
- Secrets never through the tree. The cloud session has **no `.env`, no `gh` and no Azure**, so no live
  proof is possible there: **state which environment you ran in**, and leave F1–F3 to the planner.

---

## Sequencing after merge

1. The cloud session: `make ci` green in its environment, the branch pushed, then it stops.
2. The planner, locally: re-lock if owed, `make ci` on Windows, **`make gate-ran` exits 0** from a
   worktree whose `HEAD` is the pushed commit (🪤 check the printed SHA against `git rev-parse HEAD`),
   then F1–F3 on that worktree with `main`'s `.env`. Check the branch ref's open CodeQL alerts too: the
   Security Findings gate reads `main`'s.
3. Merge to `main` locally and push. 🪤 Check you are not on the branch already.
4. **Post-merge CodeQL** on `main`.
5. **Deploy**: image rebuild and retag (`/deploy-fleet`). **The operator's call**, not before
   `sched-2026-09-28`'s three proofs (S234's brief, S232's acceptance, item 87). Then F4 on the next
   scheduled run. After it, S237's Layer 2 "SIP volume" swap is a no-op for post-deploy sessions: that
   is the fix working, not a harness fault.

---

## Handover — paste this to the Claude cloud session

```text
Sprint 238 — a bar carries the whole tape's volume, and fetching it never trips the plan's
15-minute wall. Spec: docs/sprints/sprint-238-a-bar-carries-the-whole-tapes-volume.md on main
(read ALL of it, then CLAUDE.md). Repo: yury-gurevich/trading-agents.

Branch: sprint-238-a-bar-carries-the-whole-tapes-volume, cut from main. Never main. If your session
forces another branch name, use it and name it in the handback.
You have NO .env, NO gh, NO Azure and no route to download.pytorch.org. Every proof is a unit test.
You cannot run `make gate-ran`: it is owed to the planner. If `uv lock` cannot re-resolve after the
version bump, leave uv.lock untouched and say exactly that. A run result read through the GitHub
connector is an observation, never GATE PROVEN. Take DL-239 (re-check it is still free on main).

The defect (measured, DL-233 and its 2026-09-28 amendment): the provider fetches Alpaca daily bars
with feed=iex (ProviderFeedSettings.alpaca_data_feed default), so volume is IEX's 1.55-6.49 % share
of the tape. The scanner's 500,000 floor drops 65 of 99 names on IEX and 0 on SIP. Flipping the
default alone FAILS: _download_page sends end=window.end.isoformat(), Alpaca reads a bare date as
the end of that day, and on this plan a SIP request whose end is within the last 15 minutes is
refused (measured 403 "subscription does not permit querying recent SIP data"), at any hour, even on
a Sunday. end = now - 16 min: 200.

MUST RULE before any code: read agents/provider/laws/laws.md and test-plan.md whole (PROV-IDN,
PROV-OUT-01/03/04, PROV-FAIL-01/05, PARAM alpaca_data_feed), the scanner book's PARAM row for
min_average_volume, docs/laws/conventions.md, docs/laws/drift-register.md. Fill the Law reading
record in the spec first, before any code.

Law-cycle answer: YES (a new guarantee; no contracts/ change). PROV-OUT-07: a bar's volume is the
consolidated tape's; a request never asks for what the entitlement refuses; a refusal fails loud.
Provider book v1.3 -> v1.4 + Changelog, PARAM row "sip", test-plan rows, clause ID in each test
docstring, rollups in docs/laws/ledger.md AND docs/laws/INDEX.md (make ci recomputes them),
DRIFT-080 (law gap, CORRECTED S238).

Build:
1. One pure, covered function builds the WHOLE page query (symbols, timeframe, start, end, feed,
   limit, page_token) from (tickers, window, feed, page_token, now). end for sip: min(midnight UTC
   after window.end, now - 15 min), RFC 3339 with Z. Any other feed: window.end.isoformat(),
   exactly today's query. 15 minutes is a named constant, not a tunable or settings field.
   AlpacaDataSource takes an injectable clock (default real UTC now). _download_page only encodes
   and sends that dict. alpaca_data.py is 181 lines: put the builder in a sibling module.
2. ProviderFeedSettings.alpaca_data_feed default "sip". PROVIDER_ALPACA_DATA_FEED still overrides.
3. orchestration/packs/trading_vault_probes.py _alpaca_data_source: fall back to the provider's own
   default, not a second "iex" literal. That file is 181 lines too.

Order: DL-239 -> red tests A1-A6 (paste the red output) -> implement -> law cycle -> DL-70 plants
(no clamp; clamp on iex; default back to iex; probe hard-coded iex; 403 swallowed to (): each must
go red, paste each, restore) -> the step 7 decision-path grep prints nothing -> make ci redirected to
a file, exit 0, 100.00 %.

DO NOT:
- touch any file on scripts/replay_fidelity_git.py DECISION_PATHS: agents/scanner/,
  agents/analyst/, agents/portfolio_manager/, agents/provider/domain/, contracts/,
  agents/execution/order_tolerance.py, orchestration/packs/trading_tunables.json,
  orchestration/packs/trading_issuer_map.json, orchestration/history_window.py. That includes the
  scanner's laws.md. It resets the DL-237 fidelity clock. If you need one, stop and report.
- set the feed through trading_tunables.json or any env value.
- change orchestration/packs/trading_credential_tests.json (stays feed=iex; SIP latest is refused).
- fall back to IEX when SIP is refused, or retry on 403.
- send end as window.end at T00:00Z: it drops the day's bar (stamped 04:00Z/05:00Z).
- put logic inside _download_page (pragma: no cover).
- change min_average_volume or any other tunable.
- let any test reach the network (the session's egress refuses hosts; stub every HTTP call).
- claim a live Alpaca proof or GATE PROVEN: F1-F3 and the gate are the planner's after you push.
- pin a version: PATCH, next available at merge; uv.lock as above.

Handback — the planner returns it if ANY of these is missing:
[ ] Law reading record filled, including the law-cycle answer and contradictions/silences found.
[ ] Test plan results: A1-A6, each with its final test name, file, PASS, and clause IDs cited.
[ ] Closeout: the red run pasted before the fix; the green run pasted after.
[ ] Each of the five DL-70 plants: what was planted, its red output, restored.
[ ] The step 7 decision-path grep: the command and its empty output.
[ ] Module line counts for every file touched (all < 200).
[ ] make ci: the file it went to, exit code, passed/skipped, coverage 100.00 %, dependency audit,
    detect-secrets.
[ ] Exactly how uv.lock was touched (re-resolved, or untouched and owed).
[ ] Return notes: scope held or moved; what you disagreed with after reading the laws; what the
    next sprint should know.
[ ] Status: BUILT on the spec, and this sprint's README.md row leads with BUILT, in the same commit.
[ ] Owed items named: make gate-ran, Windows make ci, uv lock if not re-resolved, F1-F3.
Commit on the branch and PUSH it, then stop: no merge. Anything not met: "not done", never a
Result: for work not done.
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

*Filled 2026-09-28, before the first code change, in a claude.ai cloud session (no `.env`).*

| Element | Law file(s) read | Clauses that bind it | Did reading change your approach? |
| --- | --- | --- | --- |
| `agents/provider/alpaca_data.py` + the new sibling `alpaca_request.py` | `agents/provider/laws/laws.md` (v1.3, whole), `test-plan.md` (whole), `docs/laws/conventions.md`, `docs/laws/drift-register.md` | `PROV-IDN-01` (purpose: facts consumers never second-guess), `PROV-OUT-01` 🟩 (validated facts, honest quality record), `PROV-OUT-03` 🟩 split rows (SUCCESS/DEGRADED/FAULT), `PROV-OUT-04` ⬜ (provenance names the source — DRIFT-040), `PROV-FAIL-01` 🟩 (a failure is contained at the boundary as a typed fault, never bad-as-good), `PROV-FAIL-05` ⬜, `PROV-NEV-01` 🟩, `PROV-DEP-04` 🧱 (clock) | **Yes, twice.** (1) `PROV-FAIL-01` says a failure is *contained at the boundary*; A6 says `fetch_ohlcv` *raises*. Read together they agree only because the containment lives one layer up: `ProviderAgent._get_market_data` wraps the source call in `fault_boundary(reraise=False)` and records `source_unavailable` (the green `PROV-OUT-03c`/`PROV-FAIL-01` test). So the source must raise, and A6 cites `PROV-FAIL-01` for the source half only. (2) `PROV-DEP-04` names the clock as a dependency: the injected clock is that dependency made explicit, so the builder takes `now` as an argument and never reads the time itself. |
| `agents/provider/settings_feeds.py` | provider `laws.md` § `PARAM` | `alpaca_data_feed` `NO (mode selector)` | No: the row changes value and rationale, stays a mode selector, not a `tunable()`. |
| `orchestration/packs/trading_vault_probes.py` | provider `PROV-SEC-01/02` (sole key holder, never logged), DL-36 | the probe builds the provider's own `AlpacaDataSource` with the provider's key names | Yes: the probe reads the provider's *settings field* default (`ProviderFeedSettings.model_fields`), so the probe tests exactly what `ProviderFeedSettings()` would read, and the one literal lives in the one place `PARAM` declares. |
| `agents/scanner/settings.py` (read only) | `agents/scanner/laws/laws.md` § `PARAM` row `min_average_volume` | `500000.0`, `float ≥ 0 (shares/day)`, *"Require enough daily liquidity for later sizing and execution"* | No. The row says *shares/day*, not *IEX shares/day*: it presupposes the whole tape, which is what `PROV-OUT-07` now guarantees. Nothing under `agents/scanner/` is touched. |

**Law-cycle question — does this sprint change `contracts/` or add a new guarantee?** **Yes — a new
guarantee, no contract change.** Before this sprint the provider book never says *which* volume an
OHLCV bar carries, nor that a request must stay inside the source's entitlement. `PROV-OUT-07` is the
next free `OUT` ID (v1.3 declares `OUT-01..06`; checked). Owed and done in this unit of work: v1.3 → v1.4
+ Changelog, `PARAM` row `"sip"`, a `test-plan.md` row, clause IDs in test docstrings, both rollups,
`DRIFT-080`.

**Contradictions found between a law and this spec:** None that stops the sprint. One tension resolved
by reading, not by amendment: A6's "`fetch_ohlcv` raises" against `PROV-FAIL-01`'s "contained … never a
crash" — consistent because the provider's boundary is the agent's `fault_boundary`, not the adapter
(see row 1). `PROV-OUT-07` therefore cross-references `PROV-FAIL-01` for *how* a refusal is contained and
states only what is new: no silent empty success and no silent switch to a one-venue feed.

**Laws found silent where a decision was needed:**

- **Which volume a bar carries** — silent in v1.3. This is the sprint's `DRIFT-080` (law gap), closed by
  `PROV-OUT-07`.
- **Which feed served a stored bar** — `PROV-OUT-04` (⬜) already requires provenance to name the
  *source*, and `DRIFT-040` (OPEN) records that `MarketSnapshot` does not. The feed is a finer grain of
  the same gap: after this sprint, a `MarketSnapshot` written on IEX volume and one written on SIP volume
  are indistinguishable in the graph. Not silent (the law asks for it), so no new row; noted against
  `DRIFT-040` in the return notes. Fixing it touches `agents/provider/domain/` or `contracts/`, both
  decision paths — out of scope here.
- **`PROV-FAIL-05`** (⬜, `_tbd_`) speaks of `DEP-FEED` *red*. An entitlement refusal (403) is not a feed
  outage, so A6 does not cite `FAIL-05`; it stays ⬜.

**Clauses that were ⬜ and are now proven:** None were ⬜ before — `PROV-OUT-07` is new and lands 🟩
(A1, A2, A4, A5, A6 cite it). Provider rollup 17 / 62 → 18 / 63.

---

## Test plan results — fill at handback

| Plan # | Final test name | File | Status | Clause(s) cited |
| --- | --- | --- | --- | --- |
| A1 | `test_sip_request_for_a_window_ending_today_ends_fifteen_minutes_ago` | `agents/provider/tests/test_alpaca_sip.py` | PASS | `PROV-OUT-07` |
| A2 | `test_sip_past_window_ends_at_the_midnight_after_it` (3 cases: `2026-10-02T12:00Z` → `2026-09-29T00:00:00Z`; `2026-09-29T00:05Z` → `2026-09-28T23:50:00Z`; `2026-09-29T00:15Z` → `2026-09-29T00:00:00Z`, the boundary) | `agents/provider/tests/test_alpaca_request.py` | PASS | `PROV-OUT-07` |
| A3 | `test_iex_request_is_the_query_the_source_always_sent` (2 clocks a day apart; page 1 without and page 2 with `page_token`, through the real page loop; key order and the urlencoded bytes) | `agents/provider/tests/test_alpaca_sip.py` | PASS | `PROV-OUT-07` |
| A4 | `test_provider_default_feed_is_the_consolidated_tape` (`ProviderFeedSettings(_env_file=None)` reads `"sip"`; `market_source_from_settings` builds `AlpacaDataSource` with `_feed == "sip"`; `PROVIDER_ALPACA_DATA_FEED=iex` still overrides) | `agents/provider/tests/test_alpaca_data.py` | PASS | `PROV-OUT-07` |
| A5 | `test_alpaca_data_probe_tests_the_fleets_feed` (no env var → `"sip"`; env `iex` → `"iex"`; the settings field's default monkeypatched → the probe follows it, so a second literal of *any* value fails) | `orchestration/tests/test_trading_vault_probe_feed.py` | PASS | `PROV-OUT-07` |
| A6 | `test_refused_sip_request_raises_and_never_asks_another_feed` (stubbed page download raises `HTTPError` 403; `fetch_ohlcv` raises; exactly one request, on `sip`) | `agents/provider/tests/test_alpaca_sip.py` | PASS | `PROV-OUT-07`, `PROV-FAIL-01` |

**Tests added beyond the plan:**

- `test_alpaca_request.py::test_sip_end_is_whole_seconds_and_never_later_than_the_wall` (`PROV-OUT-07`):
  `now` with 999,999 µs still sends `22:15:00Z`, never rounded up past the wall; pins the constant at 15 min.
- `test_alpaca_sip.py::test_default_clock_is_aware_utc` (`PROV-OUT-07`): the default clock is aware UTC
  (covers the default; a naive clock would break the `min` against an aware midnight).

## Closeout — evidence

**Status:** BUILT

**Tree the proofs ran in (and `.env` present?):** a claude.ai cloud container, Linux, clone of
`yury-gurevich/trading-agents` on branch `claude/festive-shannon-7fibne` cut from `main` `2fa1325`.
**No `.env`**, no `gh`, no Azure, no route to `download.pytorch.org`. No test reached the network: every
Alpaca call is stubbed at `_download_page`. Every `uv run` ran with `UV_FROZEN=1` / `--frozen` because the
bumped `pyproject.toml` cannot be re-locked here.

**Result:** With no override the provider's `AlpacaDataSource` is built on `feed="sip"`; a SIP page query's
`end` is `min(midnight UTC after window.end, now − 15 min)` as RFC 3339 `Z`, and an IEX query is key-for-key and
byte-for-byte `main`'s (A1–A4, unit tests). The seeder's probe falls back to the provider's settings default
(A5). A refused request raises from the adapter, one request, no second feed (A6). **Not proven here:** that
Alpaca answers the clamped SIP request with 200 and whole-tape volume: that is F1, the planner's.

**Files changed:** `agents/provider/alpaca_request.py` (new), `agents/provider/alpaca_data.py`,
`agents/provider/settings_feeds.py`, `orchestration/packs/trading_vault_probes.py`; tests
`agents/provider/tests/test_alpaca_sip.py` (new), `agents/provider/tests/test_alpaca_request.py` (new),
`agents/provider/tests/test_alpaca_data.py`, `orchestration/tests/test_trading_vault_probe_feed.py` (new; the
existing probe test file is 180 lines); laws `agents/provider/laws/laws.md` (v1.4), `test-plan.md`,
`docs/laws/ledger.md`, `docs/laws/INDEX.md`, `docs/laws/drift-register.md` (DRIFT-080); `docs/design-log.md`
(DL-239); this spec, `docs/sprints/README.md`, `docs/sprints/INDEX.md`; `pyproject.toml` 0.117.02 → 0.117.03.

**Design decisions:** [DL-239](../design-log.md) (free on `main` at `2fa1325`; re-check at merge): the whole
query is one pure builder in a sibling module, clock injected and read once per fetch; the probe reads
`ProviderFeedSettings.model_fields["alpaca_data_feed"].default`; `PROV-OUT-07` keeps the refusal half and
cross-references `PROV-FAIL-01`. Rejected alternatives are listed under each decision there.

**Proof — the red run first:** the new tests against `main`'s code (`pytest … --continue-on-collection-errors`):

```text
E   ModuleNotFoundError: No module named 'agents.provider.alpaca_request'
E   TypeError: AlpacaDataSource.__init__() got an unexpected keyword argument 'clock'   (x4)
E   AttributeError: 'AlpacaDataSource' object has no attribute '_clock'
E   AssertionError: assert 'iex' == 'sip'   (x2)
FAILED agents/provider/tests/test_alpaca_sip.py::test_sip_request_for_a_window_ending_today_ends_fifteen_minutes_ago
FAILED agents/provider/tests/test_alpaca_sip.py::test_iex_request_is_the_query_the_source_always_sent[now0]
FAILED agents/provider/tests/test_alpaca_sip.py::test_iex_request_is_the_query_the_source_always_sent[now1]
FAILED agents/provider/tests/test_alpaca_sip.py::test_refused_sip_request_raises_and_never_asks_another_feed
FAILED agents/provider/tests/test_alpaca_sip.py::test_default_clock_is_aware_utc
FAILED agents/provider/tests/test_alpaca_data.py::test_provider_default_feed_is_the_consolidated_tape
FAILED orchestration/tests/test_trading_vault_probe_feed.py::test_alpaca_data_probe_tests_the_fleets_feed
ERROR agents/provider/tests/test_alpaca_request.py
7 failed, 7 passed, 1 error in 0.30s
```

🪤 Honest reading of the red: A1, A3 and A6 go red on `main` because the source has no `clock` and
`_download_page` has the old signature, not because of their assertions. A6's *assertion* (a 403 raises) was
already true on `main`; its guard value is proven by plant 5 below, and A3's by plant 2.

**Proof — the green run:**

```text
agents/provider/tests/test_alpaca_sip.py::test_sip_request_for_a_window_ending_today_ends_fifteen_minutes_ago PASSED
agents/provider/tests/test_alpaca_sip.py::test_iex_request_is_the_query_the_source_always_sent[now0] PASSED
agents/provider/tests/test_alpaca_sip.py::test_iex_request_is_the_query_the_source_always_sent[now1] PASSED
agents/provider/tests/test_alpaca_sip.py::test_refused_sip_request_raises_and_never_asks_another_feed PASSED
agents/provider/tests/test_alpaca_sip.py::test_default_clock_is_aware_utc PASSED
agents/provider/tests/test_alpaca_request.py::test_sip_past_window_ends_at_the_midnight_after_it[now0-2026-09-29T00:00:00Z] PASSED
agents/provider/tests/test_alpaca_request.py::test_sip_past_window_ends_at_the_midnight_after_it[now1-2026-09-28T23:50:00Z] PASSED
agents/provider/tests/test_alpaca_request.py::test_sip_past_window_ends_at_the_midnight_after_it[now2-2026-09-29T00:00:00Z] PASSED
agents/provider/tests/test_alpaca_request.py::test_sip_end_is_whole_seconds_and_never_later_than_the_wall PASSED
agents/provider/tests/test_alpaca_data.py::test_provider_default_feed_is_the_consolidated_tape PASSED
orchestration/tests/test_trading_vault_probe_feed.py::test_alpaca_data_probe_tests_the_fleets_feed PASSED
(+ the 7 pre-existing test_alpaca_data.py tests and all 13 test_trading_vault_probes.py tests PASSED)
============================== 31 passed in 0.38s ==============================
```

**Guards planted:** each planted alone, run over the four S238 test files, restored, and the restore checked
with `cmp` against a backup (identical). Plants 3 and 4 were re-run with `PYTHONDONTWRITEBYTECODE=1` and
`__pycache__` removed: the first pass of plant 4 was contaminated by a stale `.pyc` from plant 3 (`"sip"` and
`"iex"` are the same length, so the source's size and whole-second mtime can match); the clean outputs are below.

1. **No clamp** — `alpaca_request._end` returns `window.end.isoformat()` for every feed. Red:
   `FAILED test_alpaca_sip.py::test_sip_request_for_a_window_ending_today_ends_fifteen_minutes_ago`, all three
   `test_sip_past_window_ends_at_the_midnight_after_it` cases, `test_sip_end_is_whole_seconds_and_never_later_than_the_wall`
   — `5 failed, 13 passed`. Restored.
2. **Clamp applied to `iex`** — the `if feed != SIP_FEED` early return removed. Red:
   `FAILED test_iex_request_is_the_query_the_source_always_sent[now0]`, `[now1]` — `2 failed, 16 passed`. Restored.
3. **Default reverted to `"iex"`** in `settings_feeds.py`. Red: `AssertionError: assert 'iex' == 'sip'` ×2;
   `FAILED test_alpaca_data.py::test_provider_default_feed_is_the_consolidated_tape`,
   `FAILED test_trading_vault_probe_feed.py::test_alpaca_data_probe_tests_the_fleets_feed` — `2 failed, 16 passed`. Restored.
4. **Probe fallback hard-coded to `"iex"`** (`env.get("PROVIDER_ALPACA_DATA_FEED", "iex")`). Red:
   `AssertionError: assert 'iex' == 'sip'`; `FAILED test_trading_vault_probe_feed.py::test_alpaca_data_probe_tests_the_fleets_feed`
   — `1 failed, 17 passed`. Restored.
5. **403 swallowed into `()`** — `fetch_ohlcv` wrapped in `try … except urllib.error.HTTPError: return ()`. Red:
   `FAILED test_alpaca_sip.py::test_refused_sip_request_raises_and_never_asks_another_feed` — `1 failed, 17 passed`. Restored.

After restoring: `18 passed`.

**Decision-path check (step 7):** run on `HEAD` `a2a60cf` (the build commit), after `git fetch origin main`:

```text
$ git diff --name-only origin/main...HEAD | grep -E '^(agents/(scanner|analyst|portfolio_manager|provider/domain)/|contracts/|agents/execution/order_tolerance\.py|orchestration/packs/trading_(tunables|issuer_map)\.json|orchestration/history_window\.py)'
$ echo $?
1
```

Empty output (grep exit 1: no match). The handback commit adds only `docs/sprints/` files.

**Module line counts:** `agents/provider/alpaca_data.py` **178** (was 181), `agents/provider/alpaca_request.py`
**64** (new), `agents/provider/settings_feeds.py` **131**, `orchestration/packs/trading_vault_probes.py` **187**
(was 181; ⚠️ above the 150 warning, as it already was), `agents/provider/tests/test_alpaca_data.py` **120**,
`agents/provider/tests/test_alpaca_sip.py` **140** (new), `agents/provider/tests/test_alpaca_request.py` **48**
(new), `orchestration/tests/test_trading_vault_probe_feed.py` **32** (new). All < 200.

**`make ci`:** `UV_FROZEN=1 make ci > <session scratchpad>/ci-final.txt 2>&1; echo $?` → **exit 0**, run on this
tree with the handback filled (only this `make ci` figure paragraph was written after it; `check_sprint_status`
and `check_markdown_links` were re-run on it). All 15 steps ran in order: ruff check (clean), ruff format
(clean), mypy `Success: no issues found in 1059 source files`, import-linter `Contracts: 5 kept, 0 broken`,
module size (warnings only, none of this sprint's files over 200), module header, law coverage (provider
18 / 63 agrees in ledger and INDEX), PARAM/settings sync (two pre-existing `portfolio_manager` envelope
`[WARN]`s only), sprint status (this spec reads `BUILT`), markdown links, version scheme (`0.117.03`),
pytest **3469 passed, 6 skipped**, coverage **100.00 %** (`TOTAL 18873 0 4096 0 100.00%`), dependency audit
`No unaccepted vulnerabilities; 1 accepted advisory re-checked` (PYSEC-2026-2447, DL-184), detect-secrets
`Passed`, untracked secrets `no untracked files to scan`. `UV_FROZEN=1` because the lock cannot re-resolve
here (DL-228); remote CI runs `uv sync --frozen` too.

**`make gate-ran`:** *(planner: local worktree, full SHA, output)* — **not done: owed.** This session has no `gh`.

**`uv.lock`:** **untouched and owed.** `uv lock` after the bump failed:
`error: Failed to fetch: https://download.pytorch.org/whl/cpu/torch/ … tunnel error: unsuccessful` (exit 2);
`git diff --stat uv.lock` is empty. `uv.lock` still records `trading-agents` `0.117.2`; the planner re-locks
before merging.

**Planner live check (F1–F3):** *(planner, before merge)* — **not done: owed.** No `.env` and no route to
Alpaca from this session.

**Not met / verified failing:**

- **Not done (owed to the planner):** `uv lock`, Windows `make ci`, `make gate-ran` for the pushed SHA, F1–F3;
  F4 after the operator's deploy.
- **Not done (by instruction):** the branch is `claude/festive-shannon-7fibne`, not
  `sprint-238-a-bar-carries-the-whole-tapes-volume`: the session is bound to that name.
- Nothing in scope is verified failing.

---

## Return notes

- **Scope held.** No decision-path file, no tunable, no env value, no `trading_credential_tests.json` change,
  no fallback, no retry. Two small moves inside scope: (1) `_download`'s page loop lost its
  `pragma: no cover` and is now covered through a stubbed `_download_page`, so `_download_page` really is the
  adapter's only uncovered code, as the spec states; (2) the clock is read **once per fetch**, not per page, so
  every page of one paginated fetch asks the same `end` (a page token is issued against one query).
- **What I disagreed with after reading the laws.** Nothing that stops the sprint. (a) A6's "`fetch_ohlcv`
  raises" reads against `PROV-FAIL-01`'s "contained … never a crash"; it holds because containment is the
  agent's `fault_boundary`, one layer up, so `PROV-OUT-07` cross-references `FAIL-01` rather than restating it.
  (b) The spec's `min(…, now − 15 min)` sits exactly on the wall. `end` is truncated to whole seconds and the
  request reaches Alpaca some milliseconds later, so it is never inside the wall **if the container clock is
  not ahead of Alpaca's**. A clock running ahead by more than the request latency would 403 intermittently.
  F1 measures the happy path only; if a live 403 ever appears with a clamped `end`, the fix is a larger
  constant margin, not a retry. I kept 15 minutes as specified.
- **What the next sprint should know.**
  - `MarketSnapshot` still does not record **which feed** served its bars (`PROV-OUT-04` ⬜, DRIFT-040). After
    the deploy, stored IEX-volume snapshots and SIP-volume snapshots are indistinguishable in the graph; the
    replay harness and any before/after comparison must split on the deploy time, not on the record.
  - A window whose `start` is today, requested in the first 15 minutes after UTC midnight, gets an `end`
    before its `start`; Alpaca will refuse it and the provider records a fault. No live caller asks for such a
    window (the dispatcher's history window is ~300 days); noted, not built.
  - `trading_vault_probes._alpaca_data_source` still carries its own literals for the base URL and timeout;
    only the feed now reads the provider's settings default. Same pattern if they ever diverge.
  - `docs/STATE.md` and `docs/laws/functionality-checks.md` are not touched: no live check ran here, and
    STATE is the planner's live tracker.
